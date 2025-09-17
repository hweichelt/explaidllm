"""App Module: clingexplaid CLI clingo app"""

import asyncio
import logging
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
from clingexplaid.preprocessors import AssumptionPreprocessor
from clingexplaid.unsat_constraints import UnsatConstraintComputer
from clingo import Symbol
from clingo.application import Application
from dotenv import load_dotenv

from ..llms.models import AbstractModel, ModelTag, OpenAIModel
from ..llms.templates import ExplainTemplate
from ..utils.logging import DEFAULT_LOGGER_NAME
from .rendering import progress_box, render_code_line

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
        pass

    # def register_options(self, options: clingo.ApplicationOptions) -> None:
    #     group = "ExplaidLLM Methods"

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

        loop = asyncio.get_event_loop()

        # STEP 1 --- Preprocessing
        processed_files, ap = loop.run_until_complete(
            self.execute_with_progress(
                self.step_pre,
                progress_label="Preprocessing files",
                progress_emoji="⚙️",
                files=files,
            )
        )
        # Skip explanation if the program is SAT
        if ExplaidLlmApp.is_satisfiable(files):
            logger.info("Program is satisfiable, no explanation needed :)")
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
        ucs = loop.run_until_complete(
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
        llm = OpenAIModel(ModelTag.GPT_4O_MINI)
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

        sys.stdout.write(render_code_line(12, list(ucs.values())[0]))

        sys.stdout.write("\n\n")

        print("Answer:", result)

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
    async def step_pre(files: Sequence[str]) -> Tuple[str, AssumptionPreprocessor]:
        await asyncio.sleep(0.1)  # minimal sleep to make sure progress is drawn
        ap = AssumptionPreprocessor()
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
            else:
                logger.debug("Computing MUS of UNSAT Program")
                return cc.shrink(solve_handle.core())

    @staticmethod
    async def step_ucs(
        files: Sequence[str], mus: UnsatisfiableSubset
    ) -> Dict[int, str]:
        await asyncio.sleep(0.1)  # minimal sleep to make sure progress is drawn
        mus_string = " ".join(
            [f"{'' if a.sign else '-'}{a.symbol}" for a in mus.assumptions]
        )
        ucc = UnsatConstraintComputer()
        ucc.parse_files(files)
        unsatisfiable_constraints = ucc.get_unsat_constraints(
            assumption_string=mus_string
        )
        return unsatisfiable_constraints

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
