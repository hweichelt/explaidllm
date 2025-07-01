import logging
import sys

from clingo.application import clingo_main

from .cli import ExplaidLlmApp

logger = logging.getLogger(__name__)


def main():
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting ExplaidLLM")
    clingo_main(ExplaidLlmApp(sys.argv[0]), sys.argv[1:] + ["-V0"])


if __name__ == "__main__":
    main()
