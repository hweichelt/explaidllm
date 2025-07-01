"""
App Module: clingexplaid CLI clingo app
"""

from importlib.metadata import version
from typing import Sequence

import clingo
from clingo.application import Application


class ExplaidLlmApp(Application):
    """
    Application class for executing the explaidllm functionality on the command line
    """

    def __init__(self, name: str) -> None:
        pass

    # def register_options(self, options: clingo.ApplicationOptions) -> None:
    #     group = "ExplaidLLM Methods"

    def main(self, control: clingo.Control, files: Sequence[str]) -> None:
        print("explaidllm", "version", version("explaidllm"))

        # printing the input files
        if not files:
            print("Reading from -")
        else:
            print(f"Reading from {files[0]} {'...' if len(files) > 1 else ''}")

        print("DO EXPLANATION HERE")
