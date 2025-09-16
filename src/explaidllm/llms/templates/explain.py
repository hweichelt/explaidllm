"""Basic Explanation Prompt Template"""
from pathlib import Path
from typing import Iterable, Set, Tuple

from clingexplaid.mus.core_computer import UnsatisfiableSubset
from clingo import Symbol

from .base import Template

PROMPT_FILE_INSTRUCTIONS = "prompt_templates/explain_instructions.txt"
PROMPT_FILE_INPUT = "prompt_templates/explain_input.txt"


class ExplainTemplate(Template):
    """Basic Explanation Prompt Template"""

    def __init__(self, program: str, assumptions: Set[Tuple[Symbol, bool]], mus: UnsatisfiableSubset, unsatisfiable_constraints: Iterable[str]):
        self._program: str = program
        self._assumptions: Set[Tuple[Symbol, bool]] = assumptions
        self._mus: UnsatisfiableSubset = mus
        self._unsatisfiable_constraints = unsatisfiable_constraints

    def compose_instructions(self) -> str:
        with open(Path(__file__).parent / PROMPT_FILE_INSTRUCTIONS, "r", encoding="utf-8") as prompt_file:
            prompt_template = prompt_file.read()
        prompt = prompt_template
        return prompt

    def compose_input(self) -> str:
        with open(Path(__file__).parent / PROMPT_FILE_INPUT, "r", encoding="utf-8") as prompt_file:
            prompt_template = prompt_file.read()
        p_assumptions = ", ".join([f"({str(a[0])},{a[1]})" for a in self._assumptions])
        p_mus = ", ".join([f"({str(a.symbol)},{a.sign})" for a in self._mus.assumptions])
        p_ucs = ", ".join([f"'{uc}'" for uc in self._unsatisfiable_constraints])
        prompt = prompt_template.format(program=self._program, assumptions=p_assumptions, mus=p_mus, ucs=p_ucs)
        return prompt
