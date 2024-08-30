import os

from dots.util import fs
from dots.util.logger import logger
from dots.plugins import plugin


class Dir(plugin.Plugin):
    def __init__(self, config):
        super().__init__(config)

        self._ignore_regex = config.get_ignored_paths().regex_list
        self._destination = os.path.expanduser(self.config.get("dst").astype(str))
        self._source = os.path.expanduser(self.config.get("src").astype(str))
        self._softlink = self.config.get("softlink", False).astype(bool)
        self._diff_abspaths = []
        self._paths_to_remove = []

    def difference(self):
        if self._softlink:
            return self._softlink_diff()

        return self._raw_diff()

    def _softlink_diff(self):
        if not os.path.islink(self._destination):
            logger().info(f"Destination {self._destination} is not a link")
            return [f"link {self._destination} -> {self._source}"]

        if os.path.realpath(os.readlink(self._destination)) != os.path.realpath(
            self._source
        ):
            logger().info(
                f"Destination {self._destination} does not point to {self._source}"
            )
            return [f"link {self._destination} -> {self._source}"]

        return []

    def _raw_diff(self):
        _difference = []
        _paths_to_remove = []

        def diff_file(source_path, destination_path):
            diff = fs.files_difference(source_path, destination_path)

            if diff:
                _difference.append(
                    f"diff for file: {destination_path}\n{''.join(diff)}"
                )
                self._diff_abspaths.append((source_path, destination_path))

        fs.recurse_directories(
            self._source, self._destination, diff_file, self._ignore_regex
        )

        def to_remove(destination_path, source_path):
            if not os.path.exists(source_path):
                _paths_to_remove.append(f"remove file {destination_path}")
                self._paths_to_remove.append(destination_path)

        if os.path.exists(self._destination):
            fs.recurse_directories(
                self._destination,
                self._source,
                to_remove,
                self._ignore_regex,
            )

        _difference += _paths_to_remove

        if not _difference:
            return []

        return (
            [f"Directories {self._destination} and {self._source} differ:"]
            + _difference
            + _paths_to_remove
        )

    def apply(self):
        if self._softlink:
            self._softlink_apply()
        else:
            self._raw_apply()

    def _raw_apply(self):
        with logger().indent("perform_apply"):
            for source, destination in self._diff_abspaths:
                fs.copy_file(source, destination)

            for destination in self._paths_to_remove:
                fs.try_remove(destination)

    def _softlink_apply(self):
        with logger().indent("perform_apply"):
            fs.link_directory(self._source, self._destination)


plugin.registry().register(Dir)
