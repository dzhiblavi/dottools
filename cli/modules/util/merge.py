"""
TODO
"""

import enum
import yaml


class UnmergeableValues(Exception):
    """
    Raised when values cannot be merged
    """


class IllegalOption(Exception):
    """
    Raised when passed an illegal option
    """


class NonMatchingTypes(Exception):
    """
    Raised when non-matching types are passed to merge
    """


ListMergeOption = enum.Enum(
    'ListMergeOption',
    [
        'ILLEGAL',
        'APPEND',
        'PREPEND',
        'PRESERVE',
        'OVERWRITE',
    ],
)

DictMergeOption = enum.Enum(
    'DictMergeOption',
    [
        'ILLEGAL',
        'UNION_RECURSIVE',
        'UNION_ADD_ONLY',
        'PRESERVE',
        'OVERWRITE',
    ],
)

ValueMergeOption = enum.Enum(
    'ValueMergeOption',
    [
        'ILLEGAL',
        'PRESERVE',
        'OVERWRITE',
    ],
)


def _get_opts(opts, key, clazz):
    if not opts or key not in opts:
        return clazz.ILLEGAL

    try:
        return clazz[opts[key].upper()]
    except ValueError as exc:
        raise IllegalOption(f'Illegal option: {opts}') from exc


def _get_list_merge_options(opts):
    return _get_opts(opts, 'list', ListMergeOption)


def _get_dict_merge_options(opts):
    return _get_opts(opts, 'dict', DictMergeOption)


def _get_value_merge_options(opts):
    return _get_opts(opts, 'value', ValueMergeOption)


def _merge_impl_list(ctx, base, extend, opts):
    ctx.logger.info(
        [
            'Merging lists',
            '> options:'
        ] + yaml.dump(opts, indent=2).splitlines() + [
            '> base:',
        ] + yaml.dump(base, indent=2).splitlines() + [
            '> extend with:',
        ] + yaml.dump(extend, indent=2).splitlines(),
    )

    if not isinstance(base, list) or not isinstance(extend, list):
        raise NonMatchingTypes('non-list values passed to list merge function')

    list_opt = _get_list_merge_options(opts)

    if list_opt == ListMergeOption.ILLEGAL:
        raise UnmergeableValues('list merging is restricted via config')

    if list_opt == ListMergeOption.APPEND:
        return base + extend

    if list_opt == ListMergeOption.PREPEND:
        return extend + base

    if list_opt == ListMergeOption.PRESERVE:
        return base

    if list_opt == ListMergeOption.OVERWRITE:
        return extend

    raise NotImplementedError(f'List option is not implemented: {list_opt}')


def _dict_union_recursive(ctx, base, extend, opts):
    copy = dict(base)
    curr_opts = get_merge_opts(ctx, base, opts)

    for key, base_value in copy.items():
        if key not in extend:
            continue

        with ctx.logger.indent(f'#{key}'):
            copy[key] = merge(ctx, base_value, extend[key], curr_opts)

    for key, extend_value in extend.items():
        if key in copy:
            continue
        copy[key] = extend_value

    return copy


def _dict_union_add_only(base, extend):
    intersection = set(base.keys()) & set(extend.keys())

    if intersection:
        raise UnmergeableValues(f'non-empty keys intersection: {intersection}')

    copy = dict(base)
    copy.update(extend)
    return copy


def _merge_impl_dict(ctx, base, extend, opts):
    ctx.logger.info(
        [
            'Merging dicts',
            '> options:'
        ] + yaml.dump(opts, indent=2).splitlines() + [
            '> base:',
        ] + yaml.dump(base, indent=2).splitlines() + [
            '> extend with:',
        ] + yaml.dump(extend, indent=2).splitlines(),
    )

    if not isinstance(base, dict) or not isinstance(extend, dict):
        raise NonMatchingTypes('non-dict passed in dict merge function')

    dict_opt = _get_dict_merge_options(opts)

    if dict_opt == DictMergeOption.ILLEGAL:
        raise UnmergeableValues('dicts merge is restricted via config')

    if dict_opt == DictMergeOption.UNION_RECURSIVE:
        return _dict_union_recursive(ctx, base, extend, opts)

    if dict_opt == DictMergeOption.UNION_ADD_ONLY:
        return _dict_union_add_only(base, extend)

    if dict_opt == DictMergeOption.PRESERVE:
        return base

    if dict_opt == DictMergeOption.OVERWRITE:
        return extend

    raise NotImplementedError(f'Dict option is not implemented: {dict_opt}')


def _merge_impl_value(ctx, base, extend, opts):
    ctx.logger.info(
        [
            'Merging values',
            '> options:'
        ] + yaml.dump(opts, indent=2).splitlines() + [
            '> base:',
        ] + yaml.dump(base, indent=2).splitlines() + [
            '> extend with:',
        ] + yaml.dump(extend, indent=2).splitlines(),
    )

    if not isinstance(extend, type(base)):
        raise UnmergeableValues('values of different types cannot be merged')

    value_opt = _get_value_merge_options(opts)

    if value_opt == ValueMergeOption.ILLEGAL:
        raise UnmergeableValues('values merge is restricted via config')

    if value_opt == ValueMergeOption.PRESERVE:
        return base

    if value_opt == ValueMergeOption.OVERWRITE:
        return extend

    raise NotImplementedError(f'Value option is not implemented: {value_opt}')


def _merge_impl(ctx, base, extend, opts):
    if isinstance(base, list):
        with ctx.logger.indent(label='list'):
            return _merge_impl_list(ctx, base, extend, opts)

    if isinstance(base, dict):
        with ctx.logger.indent(label='dict'):
            return _merge_impl_dict(ctx, base, extend, opts)

    with ctx.logger.indent(label='value'):
        return _merge_impl_value(ctx, base, extend, opts)


def merge(ctx, base, extend, opts):
    """
    Merges extend into base using configuration provided in opts
    """
    with ctx.logger.indent(label='merge'):
        return _merge_impl(ctx, base, extend, opts)


def get_merge_opts(ctx, obj, base_opts=None):
    """
    Extracts merging options from base and merges base_opts with it
    using strategy supposedly well suited for such application (see below)
    """
    opts_merging_opts = {
        'value': 'overwrite',
        'list': 'append',
        'dict': 'union_recursive',
    }

    if base_opts is None:
        base_opts = {}

    if 'merge-opts' not in obj:
        return base_opts

    with ctx.logger.indent(label='get-merge-opts'):
        return merge(ctx, base_opts, obj['merge-opts'], opts_merging_opts)
