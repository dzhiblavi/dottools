import os
import re
import sys
import subprocess
import collections
import yaml
import logging
import dd_colors
from functools import partial


def _has_gpu():
    try:
        subprocess.check_call(
            args=['nvidia-smi'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=True,
        )
        return True
    except:
        return False


class _Logger:
    LEVEL_NONE = 0
    LEVEL_ACTION = 1
    LEVEL_ERROR = 2
    LEVEL_WARNING = 3
    LEVEL_INFO = 4

    class _Silence:
        def __init__(self, logger):
            self._logger = logger

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

    class StdErrImpl:
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


    def __init__(self, level):
        logging.basicConfig()

        # self._impl = logging.getLogger('dottools')
        # self._impl.setLevel(logging.INFO)
        self._impl = self.StdErrImpl()

        self._action_fg_clr = 'green'
        self._indent = 0
        self._labels = []
        self._level = level

    def _preamble(self):
        indent = '-' * self._indent
        labels = '/'.join(self._labels if self._labels else ['root'])
        return f'{indent}[{labels}] '

    def _newline(self, preamble):
        return '\n     ' + preamble

    def _fmt(self, preamble, fmt):
        if isinstance(fmt, str):
            return fmt
        else:
            return self._newline(preamble).join(
                map(
                    partial(self._fmt, preamble),
                    fmt,
                )
            )

    def _build_log_args(self, preamble, fmt, *args):
        return [preamble + self._fmt('| ', fmt), *args]

    def write_plain(self, text):
        if self._level < self.LEVEL_INFO:
            return
        sys.stderr.writelines(text)

    def info(self, fmt, *args):
        if self._level < self.LEVEL_INFO:
            return
        self._impl.info(*self._build_log_args(self._preamble(), fmt, *args))

    def warning(self, fmt, *args):
        if self._level < self.LEVEL_WARNING:
            return
        self._impl.warning(*self._build_log_args(self._preamble(), fmt, *args))

    def error(self, fmt, *args):
        if self._level < self.LEVEL_ERROR:
            return
        self._impl.error(*self._build_log_args(self._preamble(), fmt, *args))

    def action(self, fmt, *args):
        if self._level < self.LEVEL_ACTION:
            return

        self._impl.info(
            *self._build_log_args(
                f'{self._preamble()}{dd_colors.fmt("ACTION", fg=self._action_fg_clr)} ',
                fmt, *args,
            )
        )

    def indent(self, label=None, offset=4):
        return self._Indent(self, offset, label)

    def silence(self):
        return self._Silence(self)


class Context:
    def __init__(self, config_path, dot_root, dry_run, log_level):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        self.logger = _Logger(log_level)
        self.dry_run = dry_run
        self.cfg = config
        self.cfg_path = config_path
        self.cfg_dir = os.path.dirname(config_path)
        self.home = os.path.expanduser('~')
        self.has_gpu = _has_gpu()
        self.dot_root = dot_root
        self.dot_cli = os.path.join(dot_root, 'cli')
        self.dot_bin = os.path.join(dot_root, 'bin')
        self.dot_lib = os.path.join(dot_root, 'lib')
        self.dot_common = os.path.join(dot_root, 'common')
        self.dot_docker = os.path.join(dot_root, 'docker')
        self.dot_docker_bin = os.path.join(dot_root, 'docker', 'bin')
        self.dot_dots = os.path.join(dot_root, 'dots')

        if not dry_run:
            self.dot_generated = os.path.join(dot_root, 'dots', 'generated')
        else:
            self.dot_generated = os.path.join(dot_root, 'dots', 'generated_dry-run')

        self.ignored_paths = [
            re.compile(self.apply(ignored_spec))
            for ignored_spec in self.cfg.get('ignored-paths', [])
        ]

    def _join(self, head, path):
        result = os.path.join(head, path) 
        assert os.path.exists(result), f'Path {result} does not exist'
        return os.path.abspath(result)

    def get_ignored_paths(self, ignored_specs=None):
        if ignored_specs is None:
            ignored_specs = []

        return self.ignored_paths + [
            re.compile(self.apply(ignored_spec))
            for ignored_spec in ignored_specs
        ]

    def rel(self, path):
        return self._join(self.cfg_dir, path)

    def lib(self, path):
        return self._join(self.dot_lib, path)

    def common(self, path):
        return self._join(self.dot_common, path)

    def bin(self, path):
        return self._join(self.dot_bin, path)

    def apply(self, s, local=None):
        if not local:
            local = dict()
        try:
            result = eval(
                s, {},
                {
                    'ctx': self,
                    'fmt': dd_colors.fmt,
                    'env': os.environ,
                    **local,
                },
            )
        except:
            result = s

        self.logger.info(
            [
                'Applied context',
                'src\t= %s',
                'res\t= %s',
            ],
            s, result,
        )
        return result

    def disable_dry_run(self):
        class _Disable:
            def __init__(self, ctx):
                self._ctx = ctx

            def __enter__(self):
                self._old = self._ctx.dry_run
                self._ctx.dry_run = False

            def __exit__(self, exc_type, exc_val, exc_tb):
                self._ctx.dry_run = self._old

        return _Disable(self)

