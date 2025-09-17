from dataclasses import dataclass
from enum import Enum
from typing import Optional, Union


class EscapeCode(Enum):
    RESET = "0"


@dataclass
class Color:
    red: int
    green: int
    blue: int


COLOR_BLUE = Color(red=30, green=136, blue=229)
COLOR_GRAY = Color(red=100, green=100, blue=100)

COLOR_SPINNER = COLOR_BLUE
COLOR_BORDER = COLOR_GRAY


def e(element: Union[EscapeCode, Color]) -> Optional[str]:
    if isinstance(element, EscapeCode):
        return f"\033[{element.value}m"
    elif isinstance(element, Color):
        return f"\033[38;2;{element.red};{element.green};{element.blue}m"
    return None


def colored(string: str, color: Color) -> str:
    c_string = f"{e(color)}{string}{e(EscapeCode.RESET)}"
    return c_string


def render_progress_box(label: str, progress_frame: str):
    c_divider = colored("│", COLOR_BORDER)
    upper_box = (
        colored("┌─" + "─" * len(label) + "─┬─────────────┐", COLOR_BORDER) + "\n"
    )
    progress = (
        c_divider
        + f" {label} "
        + c_divider
        + f" {colored(progress_frame, COLOR_SPINNER)} "
        + c_divider
        + "\n"
    )
    lower_box = colored("└─" + "─" * len(label) + "─┴─────────────┘", COLOR_BORDER)
    return upper_box + progress + lower_box
