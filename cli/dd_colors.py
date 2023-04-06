_color_map = {
    'black': 30,
    'red': 31,
    'green': 32,
    'yellow': 33,
    'blue': 34,
    'magenta': 35,
    'cyan': 36,
    'light_gray': 37,
    'gray': 90,
    'light_red': 91,
    'light_green': 92,
    'light_yellow': 93,
    'light_blue': 94,
    'light_magenta': 95,
    'light_cyan': 96,
    'white': 97,
}


_font_map = {
    'bold': 1,
    'fai': 2,
    'ita': 3,
    'und': 4,
}


def _color_fg(name):
    return _color_map.get(name, -1)


def _color_bg(name):
    return _color_map.get(name, -1) + 10


def _get_font(name):
    return _font_map.get(name, -1)


def fmt_line(line, fg=None, bg=None, font=None):
    if line[-1] != '\n':
        return fmt(line, fg, bg, font)
    return fmt(line[:-1], fg, bg, font) + '\n'


def fmt(text, fg=None, bg=None, font=None):
    color_nc = '{esc}[0m'
    result = '{esc}[0;{fg}m'
    if fg is not None:
        result += '{esc}[{fg}m'
    if bg is not None:
        result += '{esc}[{bg}m'
    if font is not None:
        result += '{esc}[{font}m'
    result += '{text}{esc}[0m'

    return result.format(
        esc='\033',
        text=text,
        fg=_color_fg(fg),
        bg=_color_bg(bg),
        font=_get_font(font),
    )

