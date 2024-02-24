import os
import re

from typing import Any, Dict, List, Optional
from functools import reduce, partial

from dt.context import context
from dt.util import merge, colors
from dt.util.logger import logger
from dt.config.config import Config

from dt.util.logger import StdErrLogger, Tags, TAGS_DEPENDENCIES, init_logger
from dt.util import tools

FROM_DICT_KEY = "_from"
LIST_META_KEY = "_list"


def _apply_meta_kv(key, value):
    # if kv-pair is <from, value> && if value is not a list, make it a list
    if key == FROM_DICT_KEY and not isinstance(value, list):
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


def _get_objects_to_merge_to_and_remove_from_key(
    obj: Any, opts: Dict[str, str]
) -> List[Any]:
    from_objs = obj[FROM_DICT_KEY]
    del obj[FROM_DICT_KEY]

    if isinstance(from_objs, dict) and LIST_META_KEY in from_objs:
        from_objs = from_objs[LIST_META_KEY]

    assert isinstance(from_objs, list)
    return list(map(lambda from_obj: _apply_merging(from_obj, opts), from_objs))


def _apply_merging_impl(obj: Any, opts: Dict[str, str]) -> Any:
    if FROM_DICT_KEY not in obj:
        return obj

    # Merge all objects in 'from' list sequentially
    merged_from_objects = reduce(
        lambda val, from_obj: merge.merge(val, from_obj, opts),
        _get_objects_to_merge_to_and_remove_from_key(obj, opts),
    )

    # Finally, merge obj (without 'from' key) into merged base objects
    return merge.merge(merged_from_objects, obj, opts)


def _apply_merging(obj: Any, opts: Dict[str, str]) -> Any:
    if isinstance(obj, dict):
        # Get merge options from obj and merge them into
        # parent's merge options opts
        opts = merge.get_merge_opts(obj, opts)

        # first, apply merging to all subobjects
        for key, value in obj.items():
            obj[key] = _apply_merging(value, opts)

        # now we can merge the obj
        obj = _apply_merging_impl(obj, opts)

        # remove utility key from the object
        if merge.MERGE_OPTS_CONFIG_KEY in obj:
            del obj[merge.MERGE_OPTS_CONFIG_KEY]

    if isinstance(obj, list):
        # just apply merging to all elements in the list
        return list(map(lambda from_obj: _apply_merging(from_obj, opts), obj))

    return obj


def _create_config(obj: Any, parent: Optional[Config] = None) -> Config:
    if isinstance(obj, dict):
        config = Config(parent=parent)
        config.set_object(
            {key: _create_config(value, parent=config) for key, value in obj.items()}
        )
        return config

    if isinstance(obj, list):
        config = Config(parent=parent)
        config.set_object([_create_config(item, parent) for item in obj])
        return config

    return Config(obj, parent)


def create(obj: Any) -> Config:
    default_merge_opts = {
        "value": "overwrite",
        "list": "append",
        "dict": "union_recursive",
    }

    local = {
        "ctx": context(),
        "fmt": colors.fmt,
        "env": os.environ,
    }

    obj = _apply_meta_to_raw_objects(obj)
    obj = _apply_merging(obj, default_merge_opts)
    return _create_config(obj)
