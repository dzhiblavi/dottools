import os
import re

from typing import Any, Dict, List, Optional
from functools import reduce, partial

from modules.context import context
from modules.util import merge, colors
from modules.util.logger import logger


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

    if isinstance(obj, list) and not list_key:
        return {
            'list': [_apply_meta_to_raw_objects(item) for item in obj],
        }

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
        return _apply_merging_impl(obj, opts)

    if isinstance(obj, list):
        # just apply merging to all elements in the list
        return list(
            map(
                lambda from_obj: _apply_merging(from_obj, opts),
                obj
            )
        )

    return obj


class Config:
    MERGE_OPTS_KEY = 'merge-opts'
    IGNORED_PATHS_KEY = 'ignored-paths'
    IGNORED_PATHS_RE_KEY = '__config_ignored-paths-re-cache'

    def __init__(self, obj: Any = None, parent=None) -> None:
        self._obj = obj
        self._parent = parent

    def set_obj(self, obj: Any) -> None:
        self._obj = obj

    def set_parent(self, parent) -> None:
        self._parent = parent

    def __contains__(self, key: str) -> bool:
        assert isinstance(self._obj, dict)
        return key in self._obj

    def __getstate__(self) -> Any:
        if not isinstance(self._obj, dict):
            return self._obj

        state = dict(self._obj)
        state[self.IGNORED_PATHS_RE_KEY] = self.ignored_paths()
        return state

    def __str__(self) -> str:
        return str(self._obj)

    def istype(self, clazz: type) -> bool:
        if clazz == list:
            if isinstance(self._obj, list):
                return True

            if isinstance(self._obj, dict) and 'list' in self._obj:
                return True

        if clazz == dict:
            return isinstance(self._obj, dict) and 'list' not in self._obj

        return isinstance(self._obj, clazz)

    def astype(self, clazz: type):
        obj = self._obj

        if clazz == dict and isinstance(obj, dict):
            # remove all config keys
            return {
                key: value
                for key, value in obj.items()
                if not self.is_config_key(key)
            }

        if clazz == list and isinstance(obj, dict):
            if 'list' not in obj:
                return []
            return obj['list'].astype(list)

        if isinstance(obj, clazz):
            return obj

        assert False, \
               f'Type mismatch: expected {clazz}, found {type(obj)}'

    def _as_default(self, default: Any):
        if default is not None:
            return Config(obj=default, parent=self)

        return default

    def getp(self, key: str, default: Any = None) -> Any:
        """
        Gets the key using the dotted notation
        Searches key in this object plus all of its parents
        """

        obj: Optional[Config] = self

        while obj is not None:
            value = obj.get(key)

            if value is not None:
                return value

            obj = obj._parent

        return self._as_default(default)

    def get(self, key: str, default: Any = None):
        """
        Gets the value by key from this config or the default one
        uses the dot notation, i.e. a.b.c
        """

        parts = key.split('.')
        obj = self

        for part in parts:
            if not isinstance(obj._obj, dict) or part not in obj._obj:
                return self._as_default(default)

            obj = obj._obj[part]

        return obj

    def to_dict(self):
        if isinstance(self._obj, dict):
            return {
                key: value.to_dict()
                for key, value in self._obj.items()
                if not self._is_internal_key(key)
            }

        if isinstance(self._obj, list):
            return [item.to_dict() for item in self._obj]

        return self._obj

    def is_config_key(self, key: str) -> bool:
        return self._is_internal_key(key) or key in {
            FROM_DICT_KEY,
            self.MERGE_OPTS_KEY,
            self.IGNORED_PATHS_KEY,
        }

    def _is_internal_key(self, key: str) -> bool:
        return key in {
            self.IGNORED_PATHS_RE_KEY,
        }

    def ignored_paths(self) -> List[Any]:
        if isinstance(self._obj, dict):
            if self.IGNORED_PATHS_RE_KEY not in self._obj:
                self._obj[self.IGNORED_PATHS_RE_KEY] = self._build_ignored_path()

            return self._obj[self.IGNORED_PATHS_RE_KEY]

        return self._find_ignored_paths_in_parents()

    def _find_ignored_paths_in_parents(self) -> List[Any]:
        if not self._parent:
            return []

        return self._parent.ignored_paths()

    def _build_ignored_path(self) -> List[Any]:
        ignored_paths = self._find_ignored_paths_in_parents()

        if isinstance(self._obj, dict) and self.IGNORED_PATHS_KEY in self._obj:
            ignored_paths.extend(
                map(
                    lambda obj: re.compile(obj.astype(str)),
                    self._obj[self.IGNORED_PATHS_KEY].astype(list),
                )
            )

        return ignored_paths


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
        config.set_obj(
            {
                key: _create_config(value, parent=config)
                for key, value in obj.items()
            }
        )
        return config

    if isinstance(obj, list):
        config = Config(parent=parent)
        config.set_obj([_create_config(item, parent) for item in obj])
        return config

    return Config(obj, parent)


def _match_and_replace_strings_recursively(config: Config, local=None) -> Config:
    if config.istype(str):
        config.set_obj(_match_and_replace_string(config.astype(str), local))

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
    obj = _apply_meta_to_raw_objects(obj)
    obj = _apply_merging(obj, default_merge_opts)

    config = _create_config(obj)
    config = _match_and_replace_strings_recursively(config, {**local, 'cfg': config})

    return config
