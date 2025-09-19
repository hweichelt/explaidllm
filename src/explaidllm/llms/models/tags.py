"""Module for handling LLM model tags"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


@dataclass
class Tag:
    """Representation of a LLM model tag for different libraries"""

    openai: Optional[str] = None


class ModelTag(Enum):
    """Language model specifier"""

    GPT_5 = Tag(openai="gpt-5")
    GPT_5_MINI = Tag(openai="gpt-5-mini")
    GPT_5_NANO = Tag(openai="gpt-5-nano")
    GPT_4O = Tag(openai="gpt-4o")
    GPT_4O_MINI = Tag(openai="gpt-4o-mini")
