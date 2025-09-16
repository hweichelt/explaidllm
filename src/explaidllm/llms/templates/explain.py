"""Basic Explanation Prompt Template"""

from pathlib import Path

from clingexplaid.mus.core_computer import UnsatisfiableSubset

from .base import Template

PROMPT_FILE_INSTRUCTIONS = "prompt_templates/explain_instructions.txt"
PROMPT_FILE_INPUT = "prompt_templates/explain_input.txt"


class ExplainTemplate(Template):
    """Basic Explanation Prompt Template"""

    def __init__(self, program: str, mus: UnsatisfiableSubset):
        self._program: str = program
        self._mus: UnsatisfiableSubset = mus

    def compose_instructions(self) -> str:
        with open(Path(__file__).parent / PROMPT_FILE_INSTRUCTIONS, "r", encoding="utf-8") as prompt_file:
            prompt_template = prompt_file.read()
        prompt = prompt_template.format()
        return prompt

    def compose_input(self) -> str:
        with open(Path(__file__).parent / PROMPT_FILE_INPUT, "r", encoding="utf-8") as prompt_file:
            prompt_template = prompt_file.read()
        prompt = prompt_template.format(program=self._program, mus=self._mus)
        return prompt
