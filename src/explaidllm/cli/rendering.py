import asyncio
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Union

import cursor

from ..spinner import get_spinner


class EscapeCode(Enum):
    RESET = "0"


@dataclass
class Color:
    red: int
    green: int
    blue: int


def e(element: Union[EscapeCode, Color]) -> Optional[str]:
    if isinstance(element, EscapeCode):
        return f"\033[{element.value}m"
    elif isinstance(element, Color):
        return f"\033[38;2;{element.red};{element.green};{element.blue}m"
    return None


def colored(string: str, color: Color) -> str:
    c_string = f"{e(color)}{string}{e(EscapeCode.RESET)}"
    return c_string


COLOR_CYAN = Color(red=1, green=87, blue=155)
COLOR_GRAY = Color(red=100, green=100, blue=100)
COLOR_GREEN = Color(red=104, green=159, blue=56)

COLOR_SPINNER = COLOR_CYAN
COLOR_BORDER = COLOR_GRAY

FINISHED_STRING = colored("✅ Finished", COLOR_GREEN)

LENGTH_EMOJI = 2


def render_progress_box(label: str, emoji: str, progress_frame: str):
    c_divider = colored("│", COLOR_BORDER)
    label_length = LENGTH_EMOJI + 1 + len(label)
    upper_box = (
        colored("┌─" + "─" * label_length + "─┬─────────────┐", COLOR_BORDER) + "\n"
    )
    progress = (
        c_divider
        + f" {emoji}"
        + f" {label} "
        + c_divider
        + f" {colored(progress_frame, COLOR_SPINNER)} "
        + c_divider
        + "\n"
    )
    lower_box = colored("└─" + "─" * label_length + "─┴─────────────┘", COLOR_BORDER)
    return upper_box + progress + lower_box


def render_code_line(line_number: int, content: str) -> str:
    return f" {line_number} ▏{content}"


async def progress_box(label: str, emoji: str):
    spinner_generator = get_spinner()
    cursor_up = "\x1b[2A"
    with cursor.HiddenCursor():
        sys.stdout.write("\n\n")
        while True:
            spinner_frame = next(spinner_generator)
            sys.stdout.write(
                f"\r{cursor_up}{render_progress_box(label, emoji, spinner_frame)}"
            )
            sys.stdout.flush()
            try:
                await asyncio.sleep(0.07)
            except asyncio.CancelledError:
                break
    sys.stdout.write(
        f"\r{cursor_up}{render_progress_box(label, emoji, FINISHED_STRING)}"
    )
    sys.stdout.write("\n")
