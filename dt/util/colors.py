from typing import Optional

_COLORMAP = {
    "black": 30,
    "red": 31,
    "green": 32,
    "yellow": 33,
    "blue": 34,
    "magenta": 35,
    "cyan": 36,
    "light_gray": 37,
    "gray": 90,
    "light_red": 91,
    "light_green": 92,
    "light_yellow": 93,
    "light_blue": 94,
    "light_magenta": 95,
    "light_cyan": 96,
    "white": 97,
}


_FONTMAP = {
    "bold": 1,
    "fai": 2,
    "ita": 3,
    "und": 4,
}


def _color_fg(name: str) -> int:
    return _COLORMAP.get(name, -1)


def _color_bg(name: str) -> int:
    return _COLORMAP.get(name, -1) + 10


def _get_font(name: str) -> int:
    return _FONTMAP.get(name, -1)


def fmt_line(line: str, fg=None, bg=None, font=None):
    if line[-1] != "\n":
        return fmt(line, fg, bg, font)

    return fmt(line[:-1], fg, bg, font) + "\n"


def fmt(
    text: str,
    fg: Optional[str] = None,
    bg: Optional[str] = None,
    font: Optional[str] = None,
):
    result = "{esc}[0;{fg}m"

    if fg is not None:
        result += "{esc}[{fg}m"

    if bg is not None:
        result += "{esc}[{bg}m"

    if font is not None:
        result += "{esc}[{font}m"

    result += "{text}{esc}[0m"

    return result.format(
        esc="\033",
        text=text,
        fg=_color_fg(fg or ""),
        bg=_color_bg(bg or ""),
        font=_get_font(font or ""),
    )
