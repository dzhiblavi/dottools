import os
import re
import yaml

from functools import partial
from modules.util import merge


FROM_DICT_KEY = 'from'


def _apply_merging_impl(ctx, obj, opts):
    if FROM_DICT_KEY not in obj:
        return obj

    opts = merge.get_merge_opts(ctx, obj, opts)

    from_objs = obj[FROM_DICT_KEY]
    del obj[FROM_DICT_KEY]

    if not isinstance(from_objs, list):
        from_objs = [from_objs]

    from_objs = list(
        map(
            lambda from_obj: _apply_merging(ctx, from_obj, opts),
            from_objs
        )
    )

    result = dict(from_objs[0])
    for from_obj in from_objs[1:]:
        result = merge.merge(ctx, result, from_obj, opts)

    result = merge.merge(ctx, result, obj, opts)
    return result


def _apply_merging(ctx, obj, opts):
    if isinstance(obj, dict):
        obj = _apply_merging_impl(ctx, obj, opts)

        for key, value in obj.items():
            obj[key] = _apply_merging(ctx, value, opts)

        return obj

    if isinstance(obj, list):
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

    obj = _apply_merging(ctx, obj, default_merge_opts)
    return _create_config(obj)


class _Config:
    IGNORED_PATHS_KEY = 'ignored-paths'
    IGNORED_PATHS_RE_KEY = '__config_ignored-paths-re'

    def __init__(self, obj=None, parent=None):
        self._obj = obj
        self._parent = parent

    def set_obj(self, obj):
        self._obj = obj

    def set_parent(self, parent):
        self._parent = parent

    def __getitem__(self, key):
        assert key != self.IGNORED_PATHS_KEY, \
               'do not try to manually get ignored-paths, use method instead'

        value = self._obj[key]

        if isinstance(value._obj, (dict, list)):
            return value

        return value._obj

    def __contains__(self, key):
        assert isinstance(self._obj, dict)
        return key in self._obj

    def __getstate__(self):
        return self._obj.copy()

    def __str__(self):
        return str(self._obj)

    def to_dict(self):
        if isinstance(self._obj, dict):
            return {
                key: value.to_dict()
                for key, value in self._obj.items()
            }

        if isinstance(self._obj, list):
            return [item.to_dict() for item in self._obj]

        return self._obj

    def get(self, key, default=None):
        assert isinstance(self._obj, dict)

        if key not in self._obj:
            return default

        return self[key]

    def items(self):
        assert isinstance(self._obj, dict)
        return self._obj.items()

    def ignored_paths(self):
        if isinstance(self._obj, dict):
            if self.IGNORED_PATHS_RE_KEY not in self._obj:
                self._obj[self.IGNORED_PATHS_RE_KEY] = self._build_ignored_path()

            return self._obj[self.IGNORED_PATHS_RE_KEY]

        return self._find_ignored_paths_in_parents()

    def _find_ignored_paths_in_parents(self):
        if not self._parent:
            return []

        return self._parent.ignored_paths()

    def _build_ignored_path(self):
        ignored_paths = self._find_ignored_paths_in_parents()

        if isinstance(self._obj, dict) and self.IGNORED_PATHS_KEY in self._obj:
            ignored_paths.extend(
                map(
                    re.compile,
                    self._obj[self.IGNORED_PATHS_KEY],
                )
            )

        return ignored_paths
