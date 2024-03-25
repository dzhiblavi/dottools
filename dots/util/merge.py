import enum

from dots.util import tools
from dots.util.logger import logger, Tags


MERGE_OPTS_CONFIG_KEY = "_merge-opts"


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
    "ListMergeOption",
    [
        "ILLEGAL",
        "APPEND",
        "PREPEND",
        "PRESERVE",
        "OVERWRITE",
    ],
)

DictMergeOption = enum.Enum(
    "DictMergeOption",
    [
        "ILLEGAL",
        "UNION_RECURSIVE",
        "UNION_ADD_ONLY",
        "PRESERVE",
        "OVERWRITE",
    ],
)

ValueMergeOption = enum.Enum(
    "ValueMergeOption",
    [
        "ILLEGAL",
        "PRESERVE",
        "OVERWRITE",
    ],
)


def _get_opts(opts, key, clazz):
    if not opts or key not in opts:
        return clazz.ILLEGAL

    try:
        return clazz[opts[key].upper()]
    except ValueError as exc:
        raise IllegalOption(f"Illegal option: {opts}") from exc


def _get_list_merge_options(opts):
    return _get_opts(opts, "list", ListMergeOption)


def _get_dict_merge_options(opts):
    return _get_opts(opts, "dict", DictMergeOption)


def _get_value_merge_options(opts):
    return _get_opts(opts, "value", ValueMergeOption)


def _log_merge_start(opts, base, extend):
    logger().log(
        Tags.MERGE,
        ["Merging:", "> options:"]
        + tools.safe_dump_yaml_lines(opts)
        + [
            "> base:",
        ]
        + tools.safe_dump_yaml_lines(base)
        + [
            "> extend with:",
        ]
        + tools.safe_dump_yaml_lines(extend),
    )


def _log_merge_result(result):
    logger().log(
        Tags.MERGE,
        [
            "> result:",
        ]
        + tools.safe_dump_yaml_lines(result),
    )


def _merge_impl_list(base, extend, opts):
    _log_merge_start(opts, base, extend)

    if not isinstance(base, list) or not isinstance(extend, list):
        raise NonMatchingTypes("non-list values passed to list merge function")

    list_opt = _get_list_merge_options(opts)

    if list_opt == ListMergeOption.ILLEGAL:
        raise UnmergeableValues("list merging is restricted via config")

    if list_opt == ListMergeOption.APPEND:
        result = base + extend

    if list_opt == ListMergeOption.PREPEND:
        result = extend + base

    if list_opt == ListMergeOption.PRESERVE:
        result = base

    if list_opt == ListMergeOption.OVERWRITE:
        result = extend

    _log_merge_result(result)
    return result


def _dict_union_recursive(base, extend, opts):
    copy = dict(base)
    opts = _merged_merge_opts(base, extend, opts)

    for key, base_value in copy.items():
        if key not in extend:
            continue

        with logger().indent(f"#{key}"):
            copy[key] = merge(base_value, extend[key], opts)

    for key, extend_value in extend.items():
        if key in copy:
            continue

        copy[key] = extend_value

    return copy


def _dict_union_add_only(base, extend):
    intersection = set(base.keys()) & set(extend.keys())

    if intersection:
        raise UnmergeableValues(f"non-empty keys intersection: {intersection}")

    copy = dict(base)
    copy.update(extend)
    return copy


def _merge_impl_dict(base, extend, opts):
    _log_merge_start(opts, base, extend)

    if not isinstance(base, dict) or not isinstance(extend, dict):
        raise NonMatchingTypes("non-dict passed in dict merge function")

    opts = _merged_merge_opts(base, extend, opts)
    dict_opt = _get_dict_merge_options(opts)

    if dict_opt == DictMergeOption.ILLEGAL:
        raise UnmergeableValues("dicts merge is restricted via config")

    if dict_opt == DictMergeOption.UNION_RECURSIVE:
        result = _dict_union_recursive(base, extend, opts)

    if dict_opt == DictMergeOption.UNION_ADD_ONLY:
        result = _dict_union_add_only(base, extend)

    if dict_opt == DictMergeOption.PRESERVE:
        result = base

    if dict_opt == DictMergeOption.OVERWRITE:
        result = extend

    _log_merge_result(result)
    return result


def _merge_impl_value(base, extend, opts):
    _log_merge_start(opts, base, extend)

    if not isinstance(extend, type(base)):
        raise UnmergeableValues("values of different types cannot be merged")

    value_opt = _get_value_merge_options(opts)

    if value_opt == ValueMergeOption.ILLEGAL:
        raise UnmergeableValues("values merge is restricted via config")

    if value_opt == ValueMergeOption.PRESERVE:
        result = base

    if value_opt == ValueMergeOption.OVERWRITE:
        result = extend

    _log_merge_result(result)
    return result


def _merge_impl(base, extend, opts):
    if isinstance(base, list):
        with logger().indent(label="list"):
            return _merge_impl_list(base, extend, opts)

    if isinstance(base, dict):
        with logger().indent(label="dict"):
            return _merge_impl_dict(base, extend, opts)

    with logger().indent(label="value"):
        return _merge_impl_value(base, extend, opts)


def _merged_merge_opts(base, extend, opts):
    return merge_opts(
        get_merge_opts(base, opts),
        get_merge_opts(extend),
    )


def merge(base, extend, opts):
    """
    Merges extend into base using configuration provided in opts
    """
    with logger().indent(label="merge"):
        return _merge_impl(base, extend, opts)


def merge_opts(opts_a, opts_b):
    """
    Merges two merge options dictionaries
    using strategy supposedly well suited for such application (see below)
    """
    opts_merging_opts = {
        "value": "overwrite",
        "list": "append",
        "dict": "union_recursive",
    }

    if not opts_a:
        return opts_b

    if not opts_b:
        return opts_a

    with logger().silent():
        return merge(opts_a, opts_b, opts_merging_opts)


def get_merge_opts(obj, base_opts=None):
    """
    Extracts merging options from base and merges base_opts with it
    """
    if base_opts is None:
        base_opts = {}

    if MERGE_OPTS_CONFIG_KEY not in obj:
        return base_opts

    return merge_opts(base_opts, obj[MERGE_OPTS_CONFIG_KEY])
