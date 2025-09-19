"""App Module: clingexplaid CLI clingo app"""

import asyncio
import json
import logging
import re
import sys
from importlib.metadata import version
from typing import (
    Awaitable,
    Callable,
    Dict,
    Iterable,
    Optional,
    ParamSpec,
    Sequence,
    Set,
    Tuple,
    TypeVar,
)

import clingo
from clingexplaid.mus import CoreComputer
from clingexplaid.mus.core_computer import UnsatisfiableSubset
from clingexplaid.preprocessors import AssumptionPreprocessor, FilterSignature
from clingexplaid.unsat_constraints import UnsatConstraintComputer
from clingo import Symbol
from clingo.application import Application
from clingo.ast import Location
from dotenv import load_dotenv

from ..llms.models import AbstractModel, ModelTag, OpenAIModel
from ..llms.templates import ExplainTemplate
from ..utils.logging import DEFAULT_LOGGER_NAME
from .rendering import progress_box, render_code_line, render_llm_message

logger = logging.getLogger(DEFAULT_LOGGER_NAME)

T = TypeVar("T")
P = ParamSpec("P")


def render_assumptions(assumptions: Iterable[Tuple[Symbol, bool]]) -> str:
    output = []
    for assumption in assumptions:
        assumption_sign = "[+]" if assumption[1] else "[-]"
        assumption_string = f"{assumption[0]}{assumption_sign}"
        output.append(assumption_string)
    return "{" + ", ".join(output) + "}"


class ExplaidLlmApp(Application):
    """
    Application class for executing the explaidllm functionality on the command line
    """

    def __init__(self, name: str) -> None:
        self._assumption_signatures: Set[Tuple[str, int]] = set()
        self._llm_api_key: Optional[str] = None

    def register_options(self, options: clingo.ApplicationOptions) -> None:
        group = "ExplaidLLM Options"

        options.add(
            group,
            "assumption-signature,a",
            "Facts matching with this signature will be converted to assumptions for finding a MUS "
            "(format: <name>/<arity>, default: all facts)",
            self._parse_assumption_signature,
            multi=True,
        )

        options.add(
            group,
            "llm-api-key,k",
            "API Key for prompting the LLM",
            self._parse_llm_api_key,
        )

    @staticmethod
    def _parse_signature(signature_string: str) -> Tuple[str, int]:
        match_result = re.match(r"^([a-zA-Z]+)/([0-9]+)$", signature_string)
        if match_result is None:
            raise ValueError("Wrong signature Format")
        return match_result.group(1), int(match_result.group(2))

    def _parse_assumption_signature(self, assumption_signature: str) -> bool:
        assumption_signature_string = assumption_signature.replace("=", "").strip()
        try:
            signature, arity = self._parse_signature(assumption_signature_string)
        except ValueError:
            print(
                "PARSE ERROR: Wrong signature format. The assumption signatures have to follow the format "
                "<assumption-name>/<arity>"
            )
            return False
        self._assumption_signatures.add((signature, arity))
        return True

    def _parse_llm_api_key(self, llm_api_key: str) -> bool:
        self._llm_api_key = llm_api_key.replace("=", "").strip()
        return True

    @staticmethod
    def is_satisfiable(files: Iterable[str]) -> bool:
        control = clingo.Control()
        for file in files:
            logger.debug(f"Loading file: {file}")
            control.load(file)
        control.ground([("base", [])])
        return control.solve().satisfiable

    def main(self, control: clingo.Control, files: Sequence[str]) -> None:
        load_dotenv()
        logger.debug(f"Using ExplaidLLM version {version('explaidllm')}")

        sys.stdout.write("\n")

        loop = asyncio.get_event_loop()

        # STEP 1 --- Preprocessing
        processed_files, ap = loop.run_until_complete(
            self.execute_with_progress(
                self.step_pre,
                progress_label="Preprocessing files",
                progress_emoji="⚙️",
                assumption_signatures=self._assumption_signatures,
                files=files,
            )
        )
        # Skip explanation if the program is SAT
        if ExplaidLlmApp.is_satisfiable(files):
            logger.info("Program is satisfiable, no explanation needed :)")
            return
        if len(ap.assumptions) == 0:
            logger.info(
                "No assumptions for MUS computation found, either your program has no convertable facts or your "
                "assumption signature filters are too restrictive."
            )
            return

        # STEP 2 --- MUS Computation
        mus = loop.run_until_complete(
            self.execute_with_progress(
                self.step_mus,
                progress_label="Computing Minimal Unsatisfiable Subset",
                progress_emoji="🔘",
                program=processed_files,
                ap=ap,
            )
        )
        logger.debug(f"Found MUS: {mus}")

        # STEP 3 --- UCS Computations
        ucs, locations = loop.run_until_complete(
            self.execute_with_progress(
                self.step_ucs,
                progress_label="Computing Unsatisfiable Constraints",
                progress_emoji="⬅️",
                files=files,
                mus=mus,
            )
        )
        logger.debug(f"Found Unsatisfiable Constraints:\n{ucs}")

        # STEP 4 --- LLM Prompting
        llm = OpenAIModel(ModelTag.GPT_4O_MINI, api_key=self._llm_api_key)
        result = loop.run_until_complete(
            self.execute_with_progress(
                self.step_llm,
                progress_label="Prompting LLM",
                progress_emoji="🤖",
                llm=llm,
                assumptions=ap.assumptions,
                mus=mus,
                ucs=ucs.values(),
            )
        )

        loop.close()

        result_json = json.loads(result, strict=False)
        explanation = " ".join(result_json["explanation"].replace("\n", "").split())

        c_id, uc = list(ucs.items())[0]
        constraint = uc
        position = locations.get(c_id).begin

        sys.stdout.write(
            render_code_line(
                line_number=position.line,
                content=constraint,
                filename=position.filename,
                width=100,
            )
        )
        sys.stdout.write("\n")
        sys.stdout.write(render_llm_message(explanation, width=100))

        sys.stdout.write("\n\n")

    @staticmethod
    async def execute_with_progress(
        function: Callable[P, Awaitable[T]],
        progress_label: str,
        progress_emoji: str,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> T:
        spinner = asyncio.ensure_future(progress_box(progress_label, progress_emoji))
        result = await function(*args, **kwargs)
        spinner.cancel()
        return result

    @staticmethod
    async def step_pre(
        files: Sequence[str],
        assumption_signatures: Optional[Set[Tuple[str, int]]] = None,
    ) -> Tuple[str, AssumptionPreprocessor]:
        await asyncio.sleep(0.1)  # minimal sleep to make sure progress is drawn
        assumption_filters = [
            FilterSignature(name=name, arity=arity)
            for (name, arity) in assumption_signatures
        ]
        assumption_filters = (
            None if len(assumption_filters) == 0 else assumption_filters
        )
        ap = AssumptionPreprocessor(filters=assumption_filters)
        result = None
        if not files:
            pass
            logger.debug("Reading from -")
            logger.warning("IMPLEMENT READING FROM STDIN HERE")
        else:
            logger.debug(f"Reading from {files[0]} {'...' if len(files) > 1 else ''}")
            result = ap.process_files(list(files))
            logger.debug(f"Processed Files:\n{result}")
        return result, ap

    @staticmethod
    async def step_mus(
        program: str, ap: AssumptionPreprocessor
    ) -> Optional[UnsatisfiableSubset]:
        await asyncio.sleep(0.1)  # minimal sleep to make sure progress is drawn
        control = clingo.Control()
        control.configuration.solve.models = 0
        control.add("base", [], program)
        control.ground([("base", [])])
        cc = CoreComputer(control=control, assumption_set=ap.assumptions)
        logger.debug(f"Solving program with assumptions: {ap.assumptions}")
        with control.solve(
            assumptions=list(ap.assumptions), yield_=True
        ) as solve_handle:
            result = solve_handle.get()
            if result.satisfiable:
                return None
            elif len(solve_handle.core()) == 0:
                logger.debug(
                    f"No unsatisfiable core found, probably because of too restrictive assumption filters"
                )
                return UnsatisfiableSubset(set(), minimal=False)
            else:
                logger.debug("Computing MUS of UNSAT Program")
                return cc.shrink(solve_handle.core())

    @staticmethod
    async def step_ucs(
        files: Sequence[str], mus: UnsatisfiableSubset
    ) -> Tuple[Dict[int, str], Dict[int, Location]]:
        await asyncio.sleep(0.1)  # minimal sleep to make sure progress is drawn
        mus_string = " ".join(
            [f"{'' if a.sign else '-'}{a.symbol}" for a in mus.assumptions]
        )
        ucc = UnsatConstraintComputer()
        ucc.parse_files(files)
        unsatisfiable_constraints = ucc.get_unsat_constraints(
            assumption_string=mus_string
        )
        locations = {
            c_id: ucc.get_constraint_location(c_id)
            for c_id in unsatisfiable_constraints.keys()
        }
        return unsatisfiable_constraints, locations

    @staticmethod
    async def step_llm(
        llm: AbstractModel,
        assumptions: Set[Tuple[Symbol, bool]],
        mus: UnsatisfiableSubset,
        ucs: Iterable[str],
    ) -> str:
        return await llm.prompt_template(
            template=ExplainTemplate(
                program="",
                assumptions=assumptions,
                mus=mus,
                unsatisfiable_constraints=ucs,
            )
        )
