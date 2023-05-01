import os
import pytest

from modules import config, context
from modules.util import tools, merge
from tests import tests_common
from tests.tests_common import dot_root, assert_same_regex, init_context


def _verify_config(dir):
    config_path = os.path.join(dir, 'config.yaml')
    compiled_path = os.path.join(dir, 'compiled.yaml')
    tests_common.init_context(config_path)

    def compile():
        raw_cfg = tools.load_yaml_by_path(config_path)
        return config.create(context.context().evaluate(raw_cfg)).to_dict()

    if os.path.exists(compiled_path):

        actual_compiled = compile()
        expected_compiled = tools.load_yaml_by_path(compiled_path)
        assert_same_regex(actual_compiled, expected_compiled)
    else:
        with pytest.raises(merge.UnmergeableValues):
            compile()


def test_all(dot_root):
    tests_common.init_logger()
    manuals_path = os.path.join(dot_root, 'cli/tests/manual')

    for subdir in os.listdir(manuals_path):
        path = os.path.join(manuals_path, subdir)

        if not subdir.startswith('test_') or not os.path.isdir(path):
            continue

        print(path)
        _verify_config(path)
