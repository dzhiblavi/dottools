import re
import os
import pytest
import cerberus

from modules import context
from modules.util import logger


class _NoopContext:
    def __enter__(self):
        pass

    def __exit__(*args):
        pass


class _SilentLogger:
    def info(self, fmt, *args):
        pass

    def warning(self, fmt, *args):
        pass

    def error(self, fmt, *args):
        pass

    def diff(self, fmt, *args):
        pass

    def action(self, fmt, *args):
        pass

    def indent(self, label=None, offset=4):
        return _NoopContext()

    def silence(self):
        return _NoopContext()


def get_dot_root():
    depth = 3

    path = os.path.abspath(__file__)
    for _ in range(depth):
        path = os.path.dirname(path)

    return path


@pytest.fixture
def dot_root():
    return get_dot_root()


def init_logger():
    logger.override_logger(_SilentLogger())


def init_context(config_path):
    root = get_dot_root()

    context.override_context(
        context.Context(
            config_path=os.path.join(root, config_path),
            dot_root=root,
            dry_run=True,
        )
    )


def assert_same_regex(actual, expected):
    """
    Check whether actual is equal to expected.
    Respects regular expressions in expected
    Uses assert for test purposes
    """

    assert type(actual) == type(expected), \
           f'Type mismatch: {type(actual)} != {type(expected)}'

    if actual is None:
        return

    if type(actual) == list:
        assert len(actual) == len(expected), \
               f'Length mismatch: {len(actual)} != {len(expected)}'

        for act, exp in zip(actual, expected):
            assert_same_regex(act, exp)

        return

    if type(actual) == dict:
        assert actual.keys() == expected.keys(), \
               f'Dict keys mismatch: {expected.keys()} != {actual.keys()}'

        for key in actual:
            assert_same_regex(actual[key], expected[key])

        return

    assert type(actual) == str, \
           f'Unexpected type: not dict, list or str: {type(actual)}'

    assert re.match(expected, actual), \
           f'str mismatch: {expected} !=~ {actual}'
