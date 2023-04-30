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


def _dump_yaml_lines(obj):
    return yaml.dump(obj, indent=2).replace('%', '%%').splitlines()


def _log_merge_start(logger, opts, base, extend):
    logger.info(
        [
            'Merging:',
            '> options:'
        ] + _dump_yaml_lines(opts) + [
            '> base:',
        ] + _dump_yaml_lines(base) + [
            '> extend with:',
        ] + _dump_yaml_lines(extend),
    )


def _log_merge_result(logger, result):
    logger.info(
        [
            '> result:',
        ] + _dump_yaml_lines(result),
    )


def _merge_impl_list(ctx, base, extend, opts):
    _log_merge_start(ctx.logger, opts, base, extend)

    if not isinstance(base, list) or not isinstance(extend, list):
        raise NonMatchingTypes('non-list values passed to list merge function')

    list_opt = _get_list_merge_options(opts)

    if list_opt == ListMergeOption.ILLEGAL:
        raise UnmergeableValues('list merging is restricted via config')

    if list_opt == ListMergeOption.APPEND:
        result = base + extend

    if list_opt == ListMergeOption.PREPEND:
        result = extend + base

    if list_opt == ListMergeOption.PRESERVE:
        result = base

    if list_opt == ListMergeOption.OVERWRITE:
        result = extend

    _log_merge_result(ctx.logger, result)
    return result


def _dict_union_recursive(ctx, base, extend, opts):
    copy = dict(base)
    opts = _merged_merge_opts(ctx, base, extend, opts)

    for key, base_value in copy.items():
        if key not in extend:
            continue

        with ctx.logger.indent(f'#{key}'):
            copy[key] = merge(ctx, base_value, extend[key], opts)

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
    _log_merge_start(ctx.logger, opts, base, extend)

    if not isinstance(base, dict) or not isinstance(extend, dict):
        raise NonMatchingTypes('non-dict passed in dict merge function')

    opts = _merged_merge_opts(ctx, base, extend, opts)
    dict_opt = _get_dict_merge_options(opts)

    if dict_opt == DictMergeOption.ILLEGAL:
        raise UnmergeableValues('dicts merge is restricted via config')

    if dict_opt == DictMergeOption.UNION_RECURSIVE:
        result = _dict_union_recursive(ctx, base, extend, opts)

    if dict_opt == DictMergeOption.UNION_ADD_ONLY:
        result = _dict_union_add_only(base, extend)

    if dict_opt == DictMergeOption.PRESERVE:
        result = base

    if dict_opt == DictMergeOption.OVERWRITE:
        result = extend

    _log_merge_result(ctx.logger, result)
    return result


def _merge_impl_value(ctx, base, extend, opts):
    _log_merge_start(ctx.logger, opts, base, extend)

    if not isinstance(extend, type(base)):
        raise UnmergeableValues('values of different types cannot be merged')

    value_opt = _get_value_merge_options(opts)

    if value_opt == ValueMergeOption.ILLEGAL:
        raise UnmergeableValues('values merge is restricted via config')

    if value_opt == ValueMergeOption.PRESERVE:
        result = base

    if value_opt == ValueMergeOption.OVERWRITE:
        result = extend

    _log_merge_result(ctx.logger, result)
    return result


def _merge_impl(ctx, base, extend, opts):
    if isinstance(base, list):
        with ctx.logger.indent(label='list'):
            return _merge_impl_list(ctx, base, extend, opts)

    if isinstance(base, dict):
        with ctx.logger.indent(label='dict'):
            return _merge_impl_dict(ctx, base, extend, opts)

    with ctx.logger.indent(label='value'):
        return _merge_impl_value(ctx, base, extend, opts)


def _merged_merge_opts(ctx, base, extend, opts):
    return merge_opts(
        ctx,
        get_merge_opts(ctx, base, opts),
        get_merge_opts(ctx, extend),
    )


def merge(ctx, base, extend, opts):
    """
    Merges extend into base using configuration provided in opts
    """
    with ctx.logger.indent(label='merge'):
        return _merge_impl(ctx, base, extend, opts)


def merge_opts(ctx, opts_a, opts_b):
    """
    Merges two merge options dictionaries
    using strategy supposedly well suited for such application (see below)
    """
    opts_merging_opts = {
        'value': 'overwrite',
        'list': 'append',
        'dict': 'union_recursive',
    }

    if not opts_a:
        return opts_b

    if not opts_b:
        return opts_a

    with ctx.logger.indent(label='merge-opts'):
        return merge(ctx, opts_a, opts_b, opts_merging_opts)


def get_merge_opts(ctx, obj, base_opts=None):
    """
    Extracts merging options from base and merges base_opts with it
    """
    if base_opts is None:
        base_opts = {}

    if 'merge-opts' not in obj:
        return base_opts

    return merge_opts(ctx, base_opts, obj['merge-opts'])
