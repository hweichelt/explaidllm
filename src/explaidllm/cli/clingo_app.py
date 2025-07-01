"""
App Module: clingexplaid CLI clingo app
"""
import logging
from importlib.metadata import version
from typing import Sequence

import clingo
from clingo.application import Application

logger = logging.getLogger(__name__)


class ExplaidLlmApp(Application):
    """
    Application class for executing the explaidllm functionality on the command line
    """

    def __init__(self, name: str) -> None:
        pass

    # def register_options(self, options: clingo.ApplicationOptions) -> None:
    #     group = "ExplaidLLM Methods"

    @staticmethod
    def is_satisfiable(program: str) -> bool:
        control = clingo.Control()
        control.add("base", [], program)
        control.ground([("base", [])])
        return control.solve().satisfiable

    @staticmethod
    def compile_program_from_files(files: Sequence[str], verbose: int = 1):
        if not files:
            logger.info("Reading from -")
        else:
            logger.info(f"Reading from {files[0]} {'...' if len(files) > 1 else ''}")


    def main(self, control: clingo.Control, files: Sequence[str]) -> None:
        logger.info(f"Using ExplaidLLM version {version('explaidllm')}")

        ExplaidLlmApp.compile_program_from_files(files)

        logger.warning("IMPLEMENT EXPLANATION HERE")
