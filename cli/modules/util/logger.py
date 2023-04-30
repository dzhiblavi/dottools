import sys

from functools import partial
from modules.util import colors


LEVEL_NONE = 0
LEVEL_ACTION = 1
LEVEL_ERROR = 2
LEVEL_WARNING = 3
LEVEL_INFO = 4


class Logger:
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

    class _StdErrImpl:
        def __init__(self):
            pass

        def _log(self, head, fmt, *args):
            sys.stderr.write(head)
            sys.stderr.write(fmt % args)
            sys.stderr.write('\n')

        def info(self, fmt, *args):
            self._log('INFO: ', fmt, *args)

        def warning(self, fmt, *args):
            self._log('WARN: ', fmt, *args)

        def error(self, fmt, *args):
            self._log('ERROR: ', fmt, *args)

    def __init__(self, level, diff):
        self._impl = self._StdErrImpl()
        self._action_fg_clr = 'green'
        self._indent = 0
        self._labels = []
        self._level = level
        self._diff = diff

    def _preamble(self):
        indent = '-' * self._indent
        labels = '/'.join(self._labels if self._labels else ['root'])
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

    def info(self, fmt, *args):
        if self._level < LEVEL_INFO:
            return

        self._impl.info(*self._build_log_args(self._preamble(), fmt, *args))

    def warning(self, fmt, *args):
        if self._level < LEVEL_WARNING:
            return

        self._impl.warning(*self._build_log_args(self._preamble(), fmt, *args))

    def error(self, fmt, *args):
        if self._level < LEVEL_ERROR:
            return

        self._impl.error(*self._build_log_args(self._preamble(), fmt, *args))

    def log_diff(self, fmt, *args):
        if not self._diff:
            return

        self._impl.info(
            *self._build_log_args(
                f'{self._preamble()}{colors.fmt("DIFF", fg=self._action_fg_clr)} ',
                fmt, *args,
            )
        )

    def action(self, fmt, *args):
        if self._level < LEVEL_ACTION:
            return

        self._impl.info(
            *self._build_log_args(
                f'{self._preamble()}{colors.fmt("ACTION", fg=self._action_fg_clr)} ',
                fmt, *args,
            )
        )

    def indent(self, label=None, offset=4):
        return self._Indent(self, offset, label)

    def silence(self):
        return self._Silence(self)
