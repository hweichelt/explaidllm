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


class ColoringType(Enum):
    FOREGROUND = "38"
    BACKGROUND = "48"


def e(
    element: Union[EscapeCode, Color],
    coloring_type: ColoringType = ColoringType.FOREGROUND,
) -> Optional[str]:
    if isinstance(element, EscapeCode):
        return f"\033[{element.value}m"
    elif isinstance(element, Color):
        return f"\033[{coloring_type.value};2;{element.red};{element.green};{element.blue}m"
    return None


def colored(string: str, fg: Optional[Color] = None, bg: Optional[Color] = None) -> str:
    fg_string = "" if fg is None else e(fg, coloring_type=ColoringType.FOREGROUND)
    bg_string = "" if bg is None else e(bg, coloring_type=ColoringType.BACKGROUND)
    c_string = f"{bg_string}{fg_string}{string}{e(EscapeCode.RESET)}"
    return c_string


COLOR_WHITE = Color(red=255, green=255, blue=255)
COLOR_CYAN = Color(red=1, green=87, blue=155)
COLOR_GRAY = Color(red=100, green=100, blue=100)
COLOR_GREEN = Color(red=104, green=159, blue=56)

COLOR_SPINNER = COLOR_CYAN
COLOR_BORDER = COLOR_GRAY

FINISHED_STRING = colored("✅ Finished", fg=COLOR_GREEN)

LENGTH_EMOJI = 2


def shade(color: Color, shade_factor: float) -> Color:
    factor = max(0.0, min(shade_factor, 1.0))  # clamp to [0, 1]
    return Color(
        red=int(color.red * factor),
        green=int(color.green * factor),
        blue=int(color.blue * factor),
    )


def render_progress_box(label: str, emoji: str, progress_frame: str):
    c_divider = colored("│", fg=COLOR_BORDER)
    label_length = LENGTH_EMOJI + 1 + len(label)
    upper_box = (
        colored("┌─" + "─" * label_length + "─┬─────────────┐", fg=COLOR_BORDER) + "\n"
    )
    progress = (
        c_divider
        + f" {emoji}"
        + f" {label} "
        + c_divider
        + f" {colored(progress_frame, fg=COLOR_SPINNER)} "
        + c_divider
        + "\n"
    )
    lower_box = colored("└─" + "─" * label_length + "─┴─────────────┘", fg=COLOR_BORDER)
    return upper_box + progress + lower_box


def render_code_line(
    line_number: int, content: str, width: Optional[int] = None
) -> str:
    string_line_number = colored(
        f"   {line_number} ", fg=shade(COLOR_WHITE, 0.4), bg=shade(COLOR_GRAY, 0.2)
    )
    content_width = (
        width - len(string_line_number) if width is not None else len(content) + 2
    )
    content_padded = content.ljust(content_width)
    string_content = colored(
        f" {content_padded} ", fg=shade(COLOR_WHITE, 0.6), bg=shade(COLOR_GRAY, 0.3)
    )
    return string_line_number + string_content


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
