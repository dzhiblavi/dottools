import abc
import enum
import sys
from typing import List, Any, Optional

from functools import partial
from dots.util import colors


class Tags(enum.Enum):
    ALL = "white"
    OUTPUT = "light_green"
    MERGE = "cyan"
    ACTION = "magenta"
    DIFF = "light_cyan"
    INFO = "green"
    WARN = "yellow"
    ERROR = "red"


TAGS_DEPENDENCIES = {
    Tags.ALL: list(Tags),
    Tags.INFO: [Tags.WARN],
    Tags.WARN: [Tags.ERROR],
}


_LABELS_COLORS = [
    "red",
    "green",
    "yellow",
    "blue",
    "magenta",
    "cyan",
    "light_gray",
    "gray",
    "light_red",
    "light_green",
    "light_yellow",
    "light_blue",
    "light_magenta",
    "light_cyan",
    "white",
]


class _Indent:
    def __init__(self, logger_impl, num, label):
        self._num = num
        self._logger = logger_impl
        self._label = label

    def __enter__(self):
        self._logger._indent += self._num

        if self._label is not None:
            self._logger._labels.append(self._label)

    def __exit__(self, *_):
        self._logger._indent -= self._num

        if self._label is not None:
            self._logger._labels.pop()


class _Silence:
    def __init__(self, logger_impl):
        self._logger = logger_impl
        self._enabled_tags = []

    def __enter__(self):
        self._enabled_tags = self._logger._enabled_tags
        self._logger._enabled_tags = []

    def __exit__(self, *_):
        self._logger._enabled_tags = self._enabled_tags


class Logger(abc.ABC):
    def __init__(self, enabled_tags=None, use_colors=True) -> None:
        self._indent: int = 0
        self._labels: List[str] = []
        self._use_colors: bool = use_colors
        self._enabled_tags = enabled_tags or []

    @abc.abstractmethod
    def _log_impl(self, head: str, fmt: str, *args) -> None:
        pass

    def _clr(self, text: str, *args, **kwargs) -> str:
        if not self._use_colors:
            return text

        return colors.fmt(text, *args, **kwargs)

    def _preamble(self) -> str:
        indent = "-" * self._indent
        labels = self._clr("/", "white").join(
            self._clr(label, _LABELS_COLORS[index % len(_LABELS_COLORS)])
            for index, label in enumerate(self._labels)
        )
        return f"{indent}[{labels}] "

    def _newline(self, preamble: str) -> str:
        return "\n     " + preamble

    def _fmt(self, preamble: str, fmt) -> str:
        if isinstance(fmt, str):
            return fmt

        return self._newline(preamble).join(
            map(
                partial(self._fmt, preamble),
                fmt,
            )
        )

    def _build_log_args(self, preamble: str, fmt, *args) -> List[Any]:
        return [preamble + self._fmt("| " + " " * self._indent, fmt), *args]

    def log(self, tag: Tags, fmt, *args):
        if tag not in self._enabled_tags:
            return

        self._log_impl(
            self._clr(tag.name, tag.value) + ": ",
            *self._build_log_args(self._preamble(), fmt, *args),
        )

    def info(self, fmt, *args):
        self.log(Tags.INFO, fmt, *args)

    def warning(self, fmt, *args):
        self.log(Tags.WARN, fmt, *args)

    def error(self, fmt, *args):
        self.log(Tags.ERROR, fmt, *args)

    def indent(self, label: Optional[str] = None, offset: int = 4):
        return _Indent(self, offset, label)

    def silent(self):
        return _Silence(self)


class StdErrLogger(Logger):
    def _log_impl(self, head: str, fmt: str, *args) -> None:
        if head:
            sys.stderr.write(head)

        sys.stderr.write(fmt % args)
        sys.stderr.write("\n")


_GLOBAL_LOGGER = None


def override_logger(logger_instance: Logger) -> None:
    global _GLOBAL_LOGGER  # pylint: disable=global-variable-not-assigned,global-statement
    _GLOBAL_LOGGER = logger_instance


def init_logger(logger_instance: Logger) -> None:
    assert _GLOBAL_LOGGER is None, "Logger is already initialized"

    override_logger(logger_instance)


def logger() -> Logger:
    global _GLOBAL_LOGGER  # pylint: disable=global-variable-not-assigned,global-statement
    assert _GLOBAL_LOGGER is not None, "Logger has not been initialized yet"
    return _GLOBAL_LOGGER
