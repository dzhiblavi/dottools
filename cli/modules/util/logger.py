import abc
import sys
from typing import List, Any, Optional

from functools import partial
from modules.util import colors


LEVEL_NONE = 0
LEVEL_ERROR = 2
LEVEL_WARNING = 3
LEVEL_INFO = 4
LEVEL_ALL = 5


class _Indent:
    def __init__(self, logger_impl, num, label):
        self._num = num
        self._logger = logger_impl
        self._label = label

    def __enter__(self):
        self._logger._indent += self._num

        if self._label is not None:
            self._logger._labels.append(self._label)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._logger._indent -= self._num

        if self._label is not None:
            self._logger._labels.pop()


class Logger(abc.ABC):
    _LABEL_COLORS = [
        'red',
        'green',
        'yellow',
        'blue',
        'magenta',
        'cyan',
        'light_gray',
        'gray',
        'light_red',
        'light_green',
        'light_yellow',
        'light_blue',
        'light_magenta',
        'light_cyan',
        'white',
    ]

    _COLOR_MAP = {
        'ACTION': 'magenta',
        'DIFF': 'cyan',
        'INFO': 'green',
        'WARN': 'yellow',
        'ERROR': 'red',
        'OUT': 'light_green',
    }

    def __init__(self, level: int, use_colors: bool) -> None:
        self._indent: int = 0
        self._labels: List[str] = []
        self._level: int = level
        self._use_colors: bool = use_colors

    def _clr(self, text: str, *args, **kwargs) -> str:
        if not self._use_colors:
            return text

        return colors.fmt(text, *args, **kwargs)

    @abc.abstractmethod
    def _log_impl(self, head: str, fmt: str, *args: List[Any]) -> None:
        pass

    def _preamble(self) -> str:
        indent = '-' * self._indent
        labels = self._clr('/', 'white').join(
            self._clr(label, self._LABEL_COLORS[index])
            for index, label in enumerate(self._labels)
        )
        return f'{indent}[{labels}] '

    def _newline(self, preamble: str) -> str:
        return '\n     ' + preamble

    def _fmt(self, preamble: str, fmt) -> str:
        if isinstance(fmt, str):
            return fmt

        return self._newline(preamble).join(
            map(
                partial(self._fmt, preamble),
                fmt,
            )
        )

    def _build_log_args(self, preamble: str, fmt, *args: List[Any]) -> List[Any]:
        return [preamble + self._fmt('| ' + ' ' * self._indent, fmt), *args]

    def _log_with_tag(self, tag: str, fmt, *args: List[Any]) -> None:
        self._log_impl(
            self._clr(tag, self._COLOR_MAP[tag]) + ': ',
            *self._build_log_args(self._preamble(), fmt, *args),
        )

    def output(self, fmt, *args: List[Any]) -> None:
        self._log_with_tag('OUT', fmt, *args)

    def info(self, fmt, *args: List[Any]):
        if self._level < LEVEL_INFO:
            return

        self._log_with_tag('INFO',  fmt, *args)

    def warning(self, fmt, *args: List[Any]):
        if self._level < LEVEL_WARNING:
            return

        self._log_with_tag('WARN', fmt, *args)

    def error(self, fmt, *args: List[Any]):
        if self._level < LEVEL_ERROR:
            return

        self._log_with_tag('ERROR', fmt, *args)

    def diff(self, fmt, *args: List[Any]):
        self._log_with_tag('DIFF', fmt, *args)

    def action(self, fmt, *args: List[Any]):
        self._log_with_tag('ACTION', fmt, *args)

    def indent(self, label: Optional[str] = None, offset: int = 4):
        return _Indent(self, offset, label)


class StdErrLogger(Logger):
    def _log_impl(self, head: str, fmt: str, *args: List[Any]) -> None:
        if head:
            sys.stderr.write(head)
        sys.stderr.write(fmt % args)
        sys.stderr.write('\n')


_GLOBAL_LOGGER = None


def override_logger(logger_instance: Logger) -> None:
    global _GLOBAL_LOGGER  # pylint: disable=global-variable-not-assigned,global-statement
    _GLOBAL_LOGGER = logger_instance


def init_logger(logger_instance: Logger) -> None:
    assert _GLOBAL_LOGGER is None, \
           'Logger is already initialized'

    override_logger(logger_instance)


def logger() -> Logger:
    global _GLOBAL_LOGGER  # pylint: disable=global-variable-not-assigned,global-statement
    assert _GLOBAL_LOGGER is not None, \
           'Logger has not been initialized yet'
    return _GLOBAL_LOGGER
