import logging
import sys

from clingo.application import clingo_main

from .cli import ExplaidLlmApp
from .utils.logging import setup_logger


def main():
    logger = setup_logger(level=logging.INFO)
    logger.debug("Starting ExplaidLLM")
    clingo_main(ExplaidLlmApp(sys.argv[0]), sys.argv[1:] + ["-V0"])


if __name__ == "__main__":
    main()
