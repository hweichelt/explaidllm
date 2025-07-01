import sys

from clingo.application import clingo_main

from .cli import ExplaidLlmApp


def main():
    clingo_main(ExplaidLlmApp(sys.argv[0]), sys.argv[1:] + ["-V0"])


if __name__ == "__main__":
    main()
