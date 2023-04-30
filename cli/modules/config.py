import re
import yaml

from functools import reduce
from modules.util import merge


FROM_DICT_KEY = 'from'


def _apply_meta_to_raw_objects(obj, list_key=False):
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


def _get_objects_to_merge_to_and_remove_from_key(ctx, obj, opts):
    from_objs = obj[FROM_DICT_KEY]
    del obj[FROM_DICT_KEY]

    if isinstance(from_objs, dict) and 'list' in from_objs:
        from_objs = from_objs['list']

    if not isinstance(from_objs, list):
        from_objs = [from_objs]

    return list(
        map(
            lambda from_obj: _apply_merging(ctx, from_obj, opts),
            from_objs
        )
    )


def _apply_merging_impl(ctx, obj, opts):
    if FROM_DICT_KEY not in obj:
        return obj

    # Merge all objects in 'from' list sequentially
    merged_from_objects = reduce(
        lambda val, from_obj: merge.merge(ctx, val, from_obj, opts),
        _get_objects_to_merge_to_and_remove_from_key(ctx, obj, opts),
    )

    # Finally, merge obj (without 'from' key) into merged base objects
    return merge.merge(ctx, merged_from_objects, obj, opts)


def _apply_merging(ctx, obj, opts):
    if isinstance(obj, dict):
        # Get merge options from obj and merge them into
        # parent's merge options opts
        opts = merge.get_merge_opts(ctx, obj, opts)

        # first, apply merging to all subobjects
        for key, value in obj.items():
            obj[key] = _apply_merging(ctx, value, opts)

        # now we can merge the obj
        return _apply_merging_impl(ctx, obj, opts)

    if isinstance(obj, list):
        # just apply merging to all elements in the list
        return list(
            map(
                lambda from_obj: _apply_merging(ctx, from_obj, opts),
                obj
            )
        )

    return obj


def _create_config(obj, parent=None):
    if isinstance(obj, dict):
        config = _Config(parent=parent)
        config.set_obj(
            {
                key: _create_config(value, parent=config)
                for key, value in obj.items()
            }
        )
        return config

    if isinstance(obj, list):
        config = _Config(parent=parent)
        config.set_obj([_create_config(item, parent) for item in obj])
        return config

    return _Config(obj, parent)


def create(ctx, obj):
    default_merge_opts = {
        'value': 'overwrite',
        'list': 'append',
        'dict': 'union_recursive',
    }

    obj = _apply_meta_to_raw_objects(obj)
    obj = _apply_merging(ctx, obj, default_merge_opts)

    return _create_config(obj)


class _Config:
    MERGE_OPTS_KEY = 'merge-opts'
    IGNORED_PATHS_KEY = 'ignored-paths'
    IGNORED_PATHS_RE_KEY = '__config_ignored-paths-re-cache'

    def __init__(self, obj=None, parent=None):
        self._obj = obj
        self._parent = parent

    def set_obj(self, obj):
        self._obj = obj

    def set_parent(self, parent):
        self._parent = parent

    def __contains__(self, key):
        assert isinstance(self._obj, dict)
        return key in self._obj

    def __getstate__(self):
        if not isinstance(self._obj, dict):
            return self._obj

        state = dict(self._obj)
        state[self.IGNORED_PATHS_RE_KEY] = self.ignored_paths()
        return state

    def __str__(self):
        return str(self._obj)

    def astype(self, clazz):
        obj = self._obj

        if isinstance(obj, clazz):
            return obj

        if clazz == list and isinstance(obj, dict):
            if 'list' not in obj:
                return []

            return obj['list'].astype(list)

        assert False, \
               f'Type mismatch: expected {clazz}, found {type(obj)}'

    def get(self, key, default_value=None):
        return self._get_impl(key, default=_Config(obj=default_value, parent=self._parent))

    def ignored_paths(self):
        if isinstance(self._obj, dict):
            if self.IGNORED_PATHS_RE_KEY not in self._obj:
                self._obj[self.IGNORED_PATHS_RE_KEY] = self._build_ignored_path()

            return self._obj[self.IGNORED_PATHS_RE_KEY]

        return self._find_ignored_paths_in_parents()

    def to_dict(self):
        if isinstance(self._obj, dict):
            return {
                key: value.to_dict()
                for key, value in self._obj.items()
            }

        if isinstance(self._obj, list):
            return [item.to_dict() for item in self._obj]

        return self._obj

    def is_config_key(self, key):
        return key in {
            FROM_DICT_KEY,
            self.MERGE_OPTS_KEY,
            self.IGNORED_PATHS_KEY,
            self.IGNORED_PATHS_RE_KEY,
        }

    def _get_impl(self, key, default=None):
        assert isinstance(self._obj, dict), \
               f'Cannot get({key}) from non-dict value {self._obj}'

        if key not in self._obj:
            return default

        obj = self._obj[key]

        assert isinstance(obj, _Config), \
               'Internal error: obj is not an instance of _Config'

        return obj

    def _find_ignored_paths_in_parents(self):
        if not self._parent:
            return []

        return self._parent.ignored_paths()

    def _build_ignored_path(self):
        ignored_paths = self._find_ignored_paths_in_parents()

        if isinstance(self._obj, dict) and self.IGNORED_PATHS_KEY in self._obj:
            ignored_paths.extend(
                map(
                    lambda obj: re.compile(obj.astype(str)),
                    self._obj[self.IGNORED_PATHS_KEY].astype(list),
                )
            )

        return ignored_paths
