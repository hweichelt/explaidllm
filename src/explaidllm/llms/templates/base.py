"""Base Prompt Template"""

from abc import ABC, abstractmethod


class Template(ABC):
    """Base Prompt Template"""

    @abstractmethod
    def compose_instructions(self) -> str:
        """Composes the instruction template string"""

    @abstractmethod
    def compose_input(self) -> str:
        """Composes the input template string"""
