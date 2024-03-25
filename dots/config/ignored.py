import re
import copy

from collections import namedtuple


IgnoredPaths = namedtuple(
    "IgnoredPaths",
    [
        "regex_list",
        "str_list",
    ],
)


class IgnoredPathsManager:
    IGNORED_PATHS_META_KEY = "_ignored-paths"

    def __init__(self, obj):
        self._obj = obj
        self._ignored_paths = None

    def get_ignored_paths(self) -> IgnoredPaths:
        if self._ignored_paths is None:
            self._ignored_paths = self._build_ignored_path()

        return self._ignored_paths

    def _build_ignored_path(self) -> IgnoredPaths:
        ignored_paths = copy.deepcopy(self._find_ignored_paths_in_parents())

        if (
            not self._obj.is_native_type(dict)
            or self.IGNORED_PATHS_META_KEY not in self._obj
        ):
            return ignored_paths

        for pattern in self._obj.get(self.IGNORED_PATHS_META_KEY).astype(list):
            pattern_str = pattern.astype(str)
            ignored_paths.str_list.append(pattern_str)
            ignored_paths.regex_list.append(re.compile(pattern_str))

        return ignored_paths

    def _find_ignored_paths_in_parents(self) -> IgnoredPaths:
        parent_obj = self._obj.get_parent()

        if not parent_obj:
            return IgnoredPaths([], [])

        return parent_obj.get_ignored_paths()
