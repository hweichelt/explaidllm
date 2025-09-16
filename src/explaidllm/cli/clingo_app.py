"""
App Module: clingexplaid CLI clingo app
"""
import logging
from importlib.metadata import version
from typing import Iterable, Optional, Sequence, Tuple

import clingo
from clingexplaid.mus import CoreComputer
from clingexplaid.mus.core_computer import UnsatisfiableSubset
from clingexplaid.preprocessors import AssumptionPreprocessor
from clingo import Symbol
from clingo.application import Application

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
    def preprocessing_from_files(files: Sequence[str]) -> Tuple[str, AssumptionPreprocessor]:
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
    def compute_mus(program: str, ap: AssumptionPreprocessor) -> Optional[UnsatisfiableSubset]:
        control = clingo.Control()
        control.configuration.solve.models = 0
        control.add("base", [], program)
        control.ground([("base", [])])
        cc = CoreComputer(control=control, assumption_set=ap.assumptions)
        logger.debug(f"Solving program with assumptions:\n{render_assumptions(ap.assumptions)}")
        with control.solve(assumptions=list(ap.assumptions), yield_=True) as solve_handle:
            result = solve_handle.get()
            if result.satisfiable:
                return None
            else:
                logger.debug("Computing MUS of UNSAT Program")
                return cc.shrink(solve_handle.core())

    def main(self, control: clingo.Control, files: Sequence[str]) -> None:
        logger.info(f"Using ExplaidLLM version {version('explaidllm')}")

        processed_files, ap = ExplaidLlmApp.preprocessing_from_files(files)
        # Skip explanation if the Program is SAT
        if ExplaidLlmApp.is_satisfiable(files):
            logger.info("Program is satisfiable, no explanation needed :)")
            return

        # Compute MUS if the program is UNSAT
        mus = self.compute_mus(processed_files, ap)
        logger.info(f"Found MUS: {mus}")


        logger.warning("IMPLEMENT EXPLANATION HERE")
