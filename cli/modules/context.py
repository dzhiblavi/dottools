import os
from typing import Any

from modules.util import tools


class Context:  # pylint: disable=too-many-instance-attributes
    def __init__(self, config_path: str, dot_root: str, dry_run: bool) -> None:
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

    def _join(self, head: str, path: str) -> str:
        result = os.path.join(head, path)
        assert os.path.exists(result), f'Path {result} does not exist'
        return os.path.abspath(result)

    def rel(self, path: str) -> str:
        return self._join(self.cfg_dir, path)

    def lib(self, path: str) -> str:
        return self._join(self.dot_lib, path)

    def common(self, path: str) -> str:
        return self._join(self.dot_common, path)

    def bin(self, path: str) -> str:
        return self._join(self.dot_bin, path)

    def load(self, path: str) -> Any:
        return tools.load_yaml_by_path(self.rel(path))


_GLOBAL_CONTEXT = None


def override_context(context_instance: Context) -> None:
    global _GLOBAL_CONTEXT  # pylint: disable=global-variable-not-assigned,global-statement
    _GLOBAL_CONTEXT = context_instance


def init_context(context_instance: Context) -> None:
    global _GLOBAL_CONTEXT  # pylint: disable=global-variable-not-assigned,global-statement
    assert _GLOBAL_CONTEXT is None, \
           'Context has already been initialized'

    override_context(context_instance)


def context() -> Context:
    global _GLOBAL_CONTEXT  # pylint: disable=global-variable-not-assigned,global-statement
    assert _GLOBAL_CONTEXT is not None, \
           'Context has not been initialized'

    return _GLOBAL_CONTEXT
