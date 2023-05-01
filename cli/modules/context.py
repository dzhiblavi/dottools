import os

from modules.util import colors
from modules.util import logger
from modules.util import tools


_global_context = None


def override_context(context_instance):
    global _global_context
    _global_context = context_instance


def init_context(context_instance):
    global _global_context
    assert _global_context is None, \
           'Context has already been initialized'

    override_context(context_instance)


def context():
    global _global_context
    assert _global_context is not None, \
           'Context has not been initialized'

    return _global_context


class Context:
    def __init__(self, config_path, dot_root, dry_run):
        self.dry_run = dry_run
        self.cfg_path = config_path
        self.cfg_dir = os.path.dirname(os.path.dirname(config_path))
        self.home = os.path.expanduser('~')
        self.has_gpu = tools.has_gpu()
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

    def _join(self, head, path):
        result = os.path.join(head, path)
        assert os.path.exists(result), f'Path {result} does not exist'
        return os.path.abspath(result)

    def rel(self, path):
        return self._join(self.cfg_dir, path)

    def lib(self, path):
        return self._join(self.dot_lib, path)

    def common(self, path):
        return self._join(self.dot_common, path)

    def bin(self, path):
        return self._join(self.dot_bin, path)

    def load(self, path):
        return tools.load_yaml_by_path(self.rel(path))

    def apply(self, s, local=None):
        if not local:
            local = {}

        try:
            return eval(
                s, {},
                {
                    'ctx': self,
                    'fmt': colors.fmt,
                    'env': os.environ,
                    **local,
                },
            )
        except SyntaxError as err:
            logger.logger().warning(
                [
                    'Failed to apply context:',
                    'src\t= %s',
                    'err\t= %s',
                ],
                s, str(err),
            )
            raise

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

    def evaluate(self, obj):
        if isinstance(obj, str):
            try:
                return self.evaluate(self.apply(obj))
            except Exception:
                return obj

        if isinstance(obj, list):
            return list(map(self.evaluate, obj))

        if isinstance(obj, dict):
            return {
                key: self.evaluate(value)
                for key, value in obj.items()
            }

        return obj
