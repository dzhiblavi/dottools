from typing import Any
from functools import reduce, partial

from dots.yaml import merge

LIST_META_KEY = "_list"
FROM_META_KEY = "_from"
MERGE_OPTS_META_KEY = "_merge-opts"


def _apply_meta_kv(key, value):
    if key == FROM_META_KEY and not isinstance(value, list):
        value = [value]

    return _apply_meta_to_raw_objects(value, list_key=key == LIST_META_KEY)


def _apply_meta_to_raw_objects(obj: Any, list_key: bool = False) -> Any:
    if isinstance(obj, list):
        if not list_key:
            return {LIST_META_KEY: [_apply_meta_to_raw_objects(item) for item in obj]}
        return [_apply_meta_to_raw_objects(item) for item in obj]

    if isinstance(obj, dict):
        return {key: _apply_meta_kv(key, value) for key, value in obj.items()}

    return obj


def _get_objects_to_merge_to_and_remove_from_key(obj: Any, opts):
    from_objs = obj[FROM_META_KEY]
    del obj[FROM_META_KEY]

    if isinstance(from_objs, dict) and LIST_META_KEY in from_objs:
        from_objs = from_objs[LIST_META_KEY]

    assert isinstance(from_objs, list)
    return [_apply_merging(item, opts) for item in from_objs]


def _apply_merging_impl(obj: Any, opts) -> Any:
    if FROM_META_KEY not in obj:
        return obj

    merged_from_objects = reduce(
        partial(merge.merge, opts=opts),
        _get_objects_to_merge_to_and_remove_from_key(obj, opts),
    )

    return merge.merge(merged_from_objects, obj, opts)


def _apply_merging(obj: Any, opts) -> Any:
    if isinstance(obj, dict):
        opts = merge.get_merge_opts(obj, opts)

        for key, value in obj.items():
            obj[key] = _apply_merging(value, opts)

        obj = _apply_merging_impl(obj, opts)

        if MERGE_OPTS_META_KEY in obj:
            del obj[MERGE_OPTS_META_KEY]

    if isinstance(obj, list):
        return [_apply_merging(item, opts) for item in obj]

    return obj


def enrich_obj(obj: Any) -> Any:
    default_merge_opts = {
        "value": "overwrite",
        "list": "append",
        "dict": "union_recursive",
    }

    obj = _apply_meta_to_raw_objects(obj)
    obj = _apply_merging(obj, default_merge_opts)

    return obj
