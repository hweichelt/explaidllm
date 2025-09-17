"""App Module: clingexplaid CLI clingo app"""

import asyncio
import logging
import sys
from importlib.metadata import version
from typing import Dict, Iterable, Optional, Sequence, Set, Tuple

import clingo
import cursor
from clingexplaid.mus import CoreComputer
from clingexplaid.mus.core_computer import UnsatisfiableSubset
from clingexplaid.preprocessors import AssumptionPreprocessor
from clingexplaid.unsat_constraints import UnsatConstraintComputer
from clingo import Symbol
from clingo.application import Application
from dotenv import load_dotenv

from ..llms.models import AbstractModel, ModelTag, OpenAIModel
from ..llms.templates import ExplainTemplate
from ..spinner import get_spinner
from ..utils.logging import DEFAULT_LOGGER_NAME

logger = logging.getLogger(DEFAULT_LOGGER_NAME)


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

    @staticmethod
    def preprocessing_from_files(
        files: Sequence[str],
    ) -> Tuple[str, AssumptionPreprocessor]:
        ap = AssumptionPreprocessor()
        result = None
        if not files:
            logger.info("Reading from -")
            logger.warning("IMPLEMENT READING FROM STDIN HERE")
        else:
            logger.info(f"Reading from {files[0]} {'...' if len(files) > 1 else ''}")
            result = ap.process_files(list(files))
            logger.debug(f"Processed Files:\n{result}")
        return result, ap

    @staticmethod
    def compute_mus(
        program: str, ap: AssumptionPreprocessor
    ) -> Optional[UnsatisfiableSubset]:
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
    def compute_unsatisfiable_constraints(
        files: Sequence[str], mus: UnsatisfiableSubset
    ) -> Dict[int, str]:
        mus_string = " ".join(
            [f"{'' if a.sign else '-'}{a.symbol}" for a in mus.assumptions]
        )
        ucc = UnsatConstraintComputer()
        ucc.parse_files(files)
        unsatisfiable_constraints = ucc.get_unsat_constraints(
            assumption_string=mus_string
        )
        return unsatisfiable_constraints

    def main(self, control: clingo.Control, files: Sequence[str]) -> None:
        load_dotenv()
        logger.info(f"Using ExplaidLLM version {version('explaidllm')}")

        processed_files, ap = ExplaidLlmApp.preprocessing_from_files(files)
        # Skip explanation if the Program is SAT
        if ExplaidLlmApp.is_satisfiable(files):
            logger.info("Program is satisfiable, no explanation needed :)")
            return

        # Compute MUS if the program is UNSAT
        mus = self.compute_mus(processed_files, ap)
        logger.info(f"Found MUS: {mus}")

        # Compute Unsatisfiable Constraints
        ucs = self.compute_unsatisfiable_constraints(files, mus)
        logger.info(f"Found Unsatisfiable Constraints:\n{ucs}")

        llm = OpenAIModel(ModelTag.GPT_4O_MINI)
        logger.info("Prompting Model")

        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            self.supervisor(llm, ap.assumptions, mus, ucs.values())
        )
        loop.close()
        print("Answer:", result)

    @staticmethod
    async def progress_spinner() -> None:
        spinner_generator = get_spinner()
        cursor_up = "\x1b[2A"
        with cursor.HiddenCursor():
            print("\n")
            while True:
                spinner_frame = next(spinner_generator)
                sys.stdout.write(
                    f"\r{cursor_up}"
                    + f"┌───────────────┬─────────────┐\n│ Prompting LLM │ \033[38;2;30;136;229m{spinner_frame}\033[0m │\n└───────────────┴─────────────┘"
                )
                sys.stdout.flush()
                try:
                    await asyncio.sleep(0.07)
                except asyncio.CancelledError:
                    break
        sys.stdout.write(
            f"\r{cursor_up}"
            + f"┌───────────────┬─────────────┐\n│ Prompting LLM │ ✅ Finished │\n└───────────────┴─────────────┘"
        )
        print("\n")

    @staticmethod
    async def prompt_llm(
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

    async def supervisor(
        self,
        llm: AbstractModel,
        assumptions: Set[Tuple[Symbol, bool]],
        mus: UnsatisfiableSubset,
        ucs: Iterable[str],
    ) -> str:
        spinner = asyncio.ensure_future(self.progress_spinner())
        result = await self.prompt_llm(
            llm=llm, assumptions=assumptions, mus=mus, ucs=ucs
        )
        spinner.cancel()
        return result
