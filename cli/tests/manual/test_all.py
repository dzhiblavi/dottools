import os
import pytest

from modules.util import tools, merge
from tests import tests_common
from tests.tests_common import dot_root, assert_same_regex


def _verify_config(dir):
    config_path = os.path.join(dir, 'config.yaml')
    compiled_path = os.path.join(dir, 'compiled.yaml')

    if os.path.exists(compiled_path):
        ctx = tests_common.ctx(config_path)

        actual_compiled = ctx.cfg.to_dict()
        expected_compiled = tools.load_yaml_by_path(compiled_path)
        assert_same_regex(actual_compiled, expected_compiled)
    else:
        with pytest.raises(merge.UnmergeableValues):
            ctx = tests_common.ctx(config_path)


def test_all(dot_root):
    manuals_path = os.path.join(dot_root, 'cli/tests/manual')

    for subdir in os.listdir(manuals_path):
        path = os.path.join(manuals_path, subdir)

        if not subdir.startswith('test_') or not os.path.isdir(path):
            continue

        print(path)
        _verify_config(path)
