import os

from dots import common
from dots.util.logger import logger
from dots.plugins import plugin


class Dir(plugin.Plugin):
    def __init__(self, config):
        super().__init__(config)

        self._ignore_regex = config.get_ignored_paths().regex_list
        self._destination = os.path.expanduser(self.config.get("dst").astype(str))
        self._source = os.path.expanduser(self.config.get("src").astype(str))
        self._diff_abspaths = []
        self._paths_to_remove = []

    def difference(self):
        _difference = []
        _paths_to_remove = []

        def diff_file(source_path, destination_path):
            diff = common.files_difference(source_path, destination_path)
            _difference.append((destination_path, diff))

            if diff:
                self._diff_abspaths.append((source_path, destination_path))

        common.recurse_directories(
            self._source, self._destination, diff_file, self._ignore_regex
        )

        def to_remove(destination_path, source_path):
            if not os.path.exists(source_path):
                _paths_to_remove.append((destination_path, "<to be removed>"))
                self._paths_to_remove.append(destination_path)

        if os.path.exists(self._destination):
            common.recurse_directories(
                self._destination,
                self._source,
                to_remove,
                self._ignore_regex,
            )

        return [(Dir.__name__, _difference + _paths_to_remove)]

    def apply(self):
        with logger().indent("perform_apply"):
            for source, destination in self._diff_abspaths:
                common.copy_file(source, destination)

            for destination in self._paths_to_remove:
                common.try_remove(destination)


plugin.registry().register(Dir)
