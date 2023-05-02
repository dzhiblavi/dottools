import abc
import sys

from functools import partial
from modules.util import colors


_global_logger = None


def override_logger(logger_instance):
    global _global_logger
    _global_logger = logger_instance


def init_logger(logger_instance):
    assert _global_logger is None, \
           'Logger is already initialized'

    override_logger(logger_instance)


def logger():
    global _global_logger

    assert _global_logger is not None, \
           'Logger has not been initialized yet'

    return _global_logger


LEVEL_NONE = 0
LEVEL_ERROR = 2
LEVEL_WARNING = 3
LEVEL_INFO = 4
LEVEL_ALL = 5


class _Silence:
    def __init__(self, logger):
        self._logger = logger
        self._old_level = None

    def __enter__(self):
        self._old_level = self._logger._level
        self._logger._level = 0

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._logger._level = self._old_level


class _Indent:
    def __init__(self, logger, num, label):
        self._num = num
        self._logger = logger
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
    }

    def __init__(self, level, use_colors):
        self._indent = 0
        self._labels = []
        self._level = level
        self._use_colors = use_colors

    def _clr(self, text, *args, **kwargs):
        if not self._use_colors:
            return text

        return colors.fmt(text, *args, **kwargs)

    @abc.abstractmethod
    def _log_impl(self, head, fmt, *args):
        pass

    def _preamble(self):
        indent = '-' * self._indent
        labels = self._clr('/', 'white').join(
            self._clr(label, self._LABEL_COLORS[index])
            for index, label in enumerate(self._labels)
        )
        return f'{indent}[{labels}] '

    def _newline(self, preamble):
        return '\n     ' + preamble

    def _fmt(self, preamble, fmt):
        if isinstance(fmt, str):
            return fmt

        return self._newline(preamble).join(
            map(
                partial(self._fmt, preamble),
                fmt,
            )
        )

    def _build_log_args(self, preamble, fmt, *args):
        return [preamble + self._fmt('| ' + ' ' * self._indent, fmt), *args]

    def output(self, fmt, *args):
        self._log_impl('', *self._build_log_args(self._preamble(), fmt, *args))

    def _log_with_tag(self, tag, fmt, *args):
        self._log_impl(
            self._clr(tag, self._COLOR_MAP[tag]) + ': ',
            *self._build_log_args(self._preamble(), fmt, *args),
        )

    def info(self, fmt, *args):
        if self._level < LEVEL_INFO:
            return

        self._log_with_tag('INFO',  fmt, *args)

    def warning(self, fmt, *args):
        if self._level < LEVEL_WARNING:
            return

        self._log_with_tag('WARN', fmt, *args)

    def error(self, fmt, *args):
        if self._level < LEVEL_ERROR:
            return

        self._log_with_tag('ERROR', fmt, *args)

    def diff(self, fmt, *args):
        self._log_with_tag('DIFF', fmt, *args)

    def action(self, fmt, *args):
        self._log_with_tag('ACTION', fmt, *args)

    def indent(self, label=None, offset=4):
        return _Indent(self, offset, label)

    def silence(self):
        return _Silence(self)


class StdErrLogger(Logger):
    def __init__(self, log_level, use_colors):
        super().__init__(log_level, use_colors)

    def _log_impl(self, head, fmt, *args):
        sys.stderr.write(head)
        sys.stderr.write(fmt % args)
        sys.stderr.write('\n')
