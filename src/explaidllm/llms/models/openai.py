"""Wrapper for the OpenAI ChatGPT model"""

import os

from openai import OpenAI

from ..templates import Template
from .base import AbstractModel
from .tags import ModelTag


class OpenAIModel(AbstractModel):
    """Wrapper class for the OpenAI model"""

    model_tag_key = "openai"

    def __init__(self, model_tag: ModelTag):
        super().__init__(model_tag)
        self._client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def prompt(self, instructions_string: str, input_string: str) -> str:
        response = self._client.responses.create(
            model=self.model_tag,
            instructions=instructions_string,
            input=input_string,
        )
        return OpenAIModel.transform_output(response.output_text)

    def prompt_template(self, template: Template) -> str:
        return self.prompt(
            instructions_string=template.compose_instructions(),
            input_string=template.compose_input(),
        )

    @staticmethod
    def transform_output(unfiltered_output: str) -> str:
        return unfiltered_output
