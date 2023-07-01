import re
from typing import List, Any


class IgnoredPathsManager:
    # A reserved key for storing a list of paths that should
    # be completely ignored by the tool. The paths are collected
    # on the whole path from an obj (see constructor) to the root.
    IGNORED_PATHS_KEY = 'ignored-paths'

    def __init__(self, obj):
        self._obj = obj
        self._ignored_paths = None
        self._ignored_paths_str = None

    def _find_ignored_paths_in_parents(self) -> List[Any]:
        parent_obj = self._obj.get_parent()

        if not parent_obj:
            return [], []

        return parent_obj.get_ignored_paths().copy(), parent_obj.get_ignored_paths_str().copy()

    def _build_ignored_path(self) -> List[Any]:
        ignored_paths, ignored_paths_str = self._find_ignored_paths_in_parents()

        if not self._obj.is_native_type(dict) or self.IGNORED_PATHS_KEY not in self._obj:
            return ignored_paths, ignored_paths_str

        for pattern in self._obj.get(self.IGNORED_PATHS_KEY).astype(list):
            pattern_str = pattern.astype(str)
            ignored_paths_str.append(pattern_str)
            ignored_paths.append(re.compile(pattern_str))

        return ignored_paths, ignored_paths_str

    def _get_ignored_paths_all(self):
        if not self._obj.is_native_type(dict):
            return self._find_ignored_paths_in_parents()

        if self._ignored_paths is None:
            self._ignored_paths, self._ignored_paths_str = self._build_ignored_path()

        return self._ignored_paths, self._ignored_paths_str

    def get_ignored_paths(self) -> List[Any]:
        return self._get_ignored_paths_all()[0]

    def get_ignored_paths_str(self) -> List[str]:
        return self._get_ignored_paths_all()[1]
