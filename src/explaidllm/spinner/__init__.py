from typing import Generator

SPINNER_INTRO = [
    "█          ",
    "▓█         ",
    "▒▓█        ",
    "░▒▓█       ",
    "░░▒▓█      ",
    " ░░▒▓█     ",
    "  ░░▒▓█    ",
    "   ░░▒▓█   ",
    "    ░░▒▓█  ",
    "     ░░▒▓█ ",
    "      ░░▒▓█",
    "       ░░█▓",
    "        █▓▒",
    "       █▓▒░",
    "      █▓▒░░",
    "     █▓▒░░ ",
    "    █▓▒░░  ",
    "   █▓▒░░   ",
    "  █▓▒░░    ",
    " █▓▒░░     ",
]
SPINNER = [
    "█▓▒░░      ",
    "▓█░░       ",
    "▒▓█        ",
    "░▒▓█       ",
    "░░▒▓█      ",
    " ░░▒▓█     ",
    "  ░░▒▓█    ",
    "   ░░▒▓█   ",
    "    ░░▒▓█  ",
    "     ░░▒▓█ ",
    "      ░░▒▓█",
    "       ░░█▓",
    "        █▓▒",
    "       █▓▒░",
    "      █▓▒░░",
    "     █▓▒░░ ",
    "    █▓▒░░  ",
    "   █▓▒░░   ",
    "  █▓▒░░    ",
    " █▓▒░░     ",
]


def get_spinner() -> Generator[str, None, None]:
    for frame in SPINNER_INTRO:
        yield frame
    index = 0
    while True:
        yield SPINNER[index]
        index = index + 1 if index < len(SPINNER) - 1 else 0
