"""Abstract base language model wrapper"""

from abc import ABC, abstractmethod

from ..templates import Template
from .tags import ModelTag


class AbstractModel(ABC):
    """Abstract base class for all language model wrappers"""

    @property
    @abstractmethod
    def model_tag_key(self) -> str:
        """Key to access the model tag from a ModelTag object"""

    def __init__(self, model_tag: ModelTag) -> None:
        """Abstract constructor"""
        self.model_tag: str = getattr(model_tag.value, self.model_tag_key)

    @abstractmethod
    async def prompt(self, instructions_string: str, input_string: str) -> str:
        """Prompts the language model with the given input string"""

    @abstractmethod
    async def prompt_template(self, template: Template) -> str:
        """Explains an explanation graph"""

    @staticmethod
    @abstractmethod
    def transform_output(unfiltered_output: str) -> str:
        """Transforms the direct model output string"""
