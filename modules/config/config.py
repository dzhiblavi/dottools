import re

from typing import Any, List, Optional


class Config:
    FROM_DICT_KEY = 'from'
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
            self.FROM_DICT_KEY,
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
