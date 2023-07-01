import pytest

from modules.util import merge
from tests import tests_common


@pytest.fixture
def ctx():
    tests_common.init_logger()
    tests_common.init_context('cli/tests/yaml/empty.yaml')


def test_illegal(ctx):
    opts = {
        'list': 'illegal',
        'set': 'illegal',
        'dict': 'illegal',
        'value': 'illegal',
    }

    with pytest.raises(merge.UnmergeableValues):
        merge.merge([], [], opts)

    with pytest.raises(merge.UnmergeableValues):
        merge.merge(set(), set(), opts)

    with pytest.raises(merge.UnmergeableValues):
        merge.merge({}, {}, opts)

    with pytest.raises(merge.UnmergeableValues):
        merge.merge('', '', opts)


def test_lists(ctx):
    assert merge.merge([1, 2, 3], [4, 5, 6], {'list': 'append'}) == [1, 2, 3, 4, 5, 6]
    assert merge.merge([1, 2, 3], [4, 5, 6], {'list': 'prepend'}) == [4, 5, 6, 1, 2, 3]
    assert merge.merge([1, 2, 3], [4, 5, 6], {'list': 'preserve'}) == [1, 2, 3]
    assert merge.merge([1, 2, 3], [4, 5, 6], {'list': 'overwrite'}) == [4, 5, 6]


def test_dicts_plain(ctx):
    base = {
        1: 'a',
        2: 'b',
        3: 'c',
    }
    extend = {
        2: 'b',
        3: 'd',
        4: 'e',
    }
    extend_uniq = {
        4: 'e',
        5: 'f',
    }

    assert merge.merge(
        base, extend,
        opts={
            'dict': 'union_recursive',
            'value': 'overwrite',
        },
    ) == {
        1: 'a',
        2: 'b',
        3: 'd',
        4: 'e',
    }

    assert merge.merge(
        base, extend_uniq,
        opts={
            'dict': 'union_add_only'
        },
    ) == {
        1: 'a',
        2: 'b',
        3: 'c',
        4: 'e',
        5: 'f',
    }

    with pytest.raises(merge.UnmergeableValues):
        merge.merge(base, extend, opts={'dict': 'union_add_only'})

    assert merge.merge(base, extend, opts={'dict': 'preserve'}) == base
    assert merge.merge(base, extend, opts={'dict': 'overwrite'}) == extend


def test_values(ctx):
    assert merge.merge('abc', 'def', {'value': 'preserve'}) == 'abc'
    assert merge.merge('abc', 'def', {'value': 'overwrite'}) == 'def'

    with pytest.raises(merge.UnmergeableValues):
        merge.merge('abc', 123, {'value': 'overwrite'})


def test_dict_recursive_a(ctx):
    base = {
        'list': [
            1, 2, 3, 4
        ],
        'dict': {
            'inner': {
                1: 'a',
                2: 'b',
            },
            'list': [
                {
                    'key': 'value',
                    1: 239,
                }
            ],
            'value': 5,
        },
        'value': 1,
    }
    extend = {
        'list': [5, 6, 7],
        'dict': {
            'inner': {
                1: 'a',
                2: 'c',
                3: 'd',
            },
            'list': [
                {
                    'key': 'other_value',
                    1: 3030,
                }
            ],
            'value': 55,
        },
        'value': 11,
    }

    assert merge.merge(
        base, extend,
        opts={
            'list': 'append',
            'set': 'union',
            'dict': 'union_recursive',
            'value': 'overwrite',
        }
    ) == {
        'list': [1, 2, 3, 4, 5, 6, 7],
        'dict': {
            'inner': {
                1: 'a',
                2: 'c',
                3: 'd',
            },
            'list': [
                {
                    'key': 'value',
                    1: 239,
                },
                {
                    'key': 'other_value',
                    1: 3030,
                },
            ],
            'value': 55,
        },
        'value': 11,
    }

    assert merge.merge(
        base, extend,
        opts={
            'list': 'prepend',
            'set': 'preserve',
            'dict': 'union_recursive',
            'value': 'preserve',
        }
    ) == {
        'list': [5, 6, 7, 1, 2, 3, 4],
        'dict': {
            'inner': {
                1: 'a',
                2: 'b',
                3: 'd',
            },
            'list': [
                {
                    'key': 'other_value',
                    1: 3030,
                },
                {
                    'key': 'value',
                    1: 239,
                },
            ],
            'value': 5,
        },
        'value': 1,
    }
