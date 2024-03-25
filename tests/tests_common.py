import re
import os
import pytest

from dots import context
from dots.util import logger


def get_dot_root():
    depth = 3

    path = os.path.abspath(__file__)
    for _ in range(depth):
        path = os.path.dirname(path)

    return path


@pytest.fixture
def dot_root():
    return get_dot_root()


@pytest.fixture(scope="session")
def disable_log():
    logger.init_logger(logger.StdErrLogger())
    with logger.logger().silent():
        yield


def init_context(config_path):
    root = get_dot_root()

    context.override_context(
        context.Context(
            config_path=os.path.join(root, config_path),
            dottools_root=root,
            dry_run=True,
        )
    )


def assert_same_regex(actual, expected):
    """
    Check whether actual is equal to expected.
    Respects regular expressions in expected
    Uses assert for test purposes
    """

    assert isinstance(
        actual, type(expected)
    ), f"Type mismatch: {type(actual)} != {type(expected)}"

    if actual is None:
        return

    if isinstance(actual, list):
        assert len(actual) == len(
            expected
        ), f"Length mismatch: {len(actual)} != {len(expected)}"

        for act, exp in zip(actual, expected):
            assert_same_regex(act, exp)

        return

    if isinstance(actual, dict):
        assert (
            actual.keys() == expected.keys()
        ), f"Dict keys mismatch: {expected.keys()} != {actual.keys()}"

        for key in actual:
            assert_same_regex(actual[key], expected[key])

        return

    assert isinstance(
        actual, str
    ), f"Unexpected type: not dict, list or str: {type(actual)}"

    assert re.match(expected, actual), f"str mismatch: {expected} !=~ {actual}"
