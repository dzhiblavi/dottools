import os
from typing import Any

from dt.util import tools


class Context:  # pylint: disable=too-many-instance-attributes
    def __init__(self, config_path: str, dottools_root: str, dry_run: bool) -> None:
        self.dry_run = dry_run
        self.cfg_path = config_path
        self.cfg_dir = os.path.dirname(os.path.dirname(config_path))
        self.home = os.path.expanduser('~')
        self.has_gpu = tools.has_gpu()
        self.dottools_root = dottools_root

    def _join(self, head: str, path: str) -> str:
        result = os.path.join(head, path)
        assert os.path.exists(result), f'Path {result} does not exist'
        return os.path.abspath(result)

    def load(self, path: str) -> Any:
        return tools.load_yaml_by_path(self.rel(path))

    def rel(self, path: str) -> str:
        return self._join(self.cfg_dir, path)


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
