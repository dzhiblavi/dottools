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

FROM_DICT_KEY = 'from'


def _apply_meta_to_raw_objects(obj: Any, list_key: bool = False) -> Any:
    """
    This function converts all plain lists to object {'list': the-list}
    So that both list representations will be allowed and treated similarly.

    Thus in yaml, list can be represented in two ways:
    some_list:
        - a
        - b

    or

    some_list:
        list:
            - a
            - b

    And it is useful when you want to add metadata to your list:

    some_list:
        merge-opts:  # will be applied ONLY to this some_list object
            list: illegal

        list:
            - a
            - b
    """

    if isinstance(obj, list):
        if not list_key:
            return {'list': [_apply_meta_to_raw_objects(item) for item in obj]}
        return [_apply_meta_to_raw_objects(item) for item in obj]

    if isinstance(obj, dict):
        return {
            key: _apply_meta_to_raw_objects(value, list_key=key == 'list')
            for key, value in obj.items()
        }

    return obj


def _get_objects_to_merge_to_and_remove_from_key(obj: Any, opts: Dict[str, str]) -> List[Any]:
    from_objs = obj[FROM_DICT_KEY]
    del obj[FROM_DICT_KEY]

    if isinstance(from_objs, dict) and 'list' in from_objs:
        from_objs = from_objs['list']

    if not isinstance(from_objs, list):
        from_objs = [from_objs]

    return list(
        map(
            lambda from_obj: _apply_merging(from_obj, opts),
            from_objs
        )
    )


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
        return list(
            map(
                lambda from_obj: _apply_merging(from_obj, opts),
                obj
            )
        )

    return obj


def _eval(value, local=None):
    if local is None:
        local = {}

    try:
        return eval(value, {}, local)  # pylint: disable=eval-used
    except Exception as error:
        logger().error(
            [
                'Failed to evaluate (( ... ))',
                'value\t= %s',
                'error\t= %s',
                'local\t= %s'
            ],
            value, error, str(local),
        )
        raise


def _match_and_replace_string(value: str, local: Optional[Dict[str, Any]] = None) -> str:
    def _match_evaluater(match, local=None):
        return str(_eval(match.group(1), local))

    return re.sub(
        re.compile('{{(.*)}}'),
        partial(_match_evaluater, local=local),
        value,
    )


def _expand_eval_statement(value: str, local=None):
    """
    Eval statement is string of form (( abc )),
    where abs is to be evaluated as plain python code.
    """

    if not value.startswith('(( ') or not value.endswith(' ))'):
        return value

    return _eval(value[3:-3], local)


def _expand_eval_statement_recursively(obj: Any, local=None):
    """
    Recursively expands strings of form (( abc )) in obj
    exactly as explained in _expand_eval_statement
    """

    if isinstance(obj, str):
        value = _expand_eval_statement(obj, local)

        if value == obj:
            return value

        return _expand_eval_statement_recursively(value, local)

    if isinstance(obj, list):
        return [
            _expand_eval_statement_recursively(item, local)
            for item in obj
        ]

    if isinstance(obj, dict):
        return {
            key: _expand_eval_statement_recursively(value, local)
            for key, value in obj.items()
        }

    return obj


def _create_config(obj: Any, parent: Optional[Config] = None) -> Config:
    if isinstance(obj, dict):
        config = Config(parent=parent)
        config.set_object(
            {
                key: _create_config(value, parent=config)
                for key, value in obj.items()
            }
        )
        return config

    if isinstance(obj, list):
        config = Config(parent=parent)
        config.set_object([_create_config(item, parent) for item in obj])
        return config

    return Config(obj, parent)


def _match_and_replace_strings_recursively(config: Config, local=None) -> Config:
    if config.istype(str):
        config.set_object(_match_and_replace_string(config.astype(str), local))

    if config.istype(list):
        for item in config.astype(list):
            item = _match_and_replace_strings_recursively(item, local)

    if config.istype(dict):
        values = config.astype(dict)
        for key, value in values.items():
            values[key] = _match_and_replace_strings_recursively(value, local)

    return config


def create(obj: Any) -> Config:
    default_merge_opts = {
        'value': 'overwrite',
        'list': 'append',
        'dict': 'union_recursive',
    }

    local = {
        'ctx': context(),
        'fmt': colors.fmt,
        'env': os.environ,
    }

    obj = _expand_eval_statement_recursively(obj, local)

    logger().log(Tags.OUTPUT, [''] + tools.safe_dump_yaml_lines(obj))

    obj = _apply_meta_to_raw_objects(obj)

    logger().log(Tags.OUTPUT, [''] + tools.safe_dump_yaml_lines(obj))

    obj = _apply_merging(obj, default_merge_opts)

    config = _create_config(obj)
    config = _match_and_replace_strings_recursively(config, {**local, 'cfg': config})

    return config
