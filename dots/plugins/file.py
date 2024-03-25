import os

from dots import common
from dots.util import diff
from dots.util.logger import logger
from dots.plugins import plugin


class File(plugin.Plugin):
    def __init__(self, config, custom_line_source=None):
        super().__init__(config)
        self._destination = os.path.expanduser(self.config.get("dst").astype(str))
        self._current_lines = None
        self._lines = None
        self._plugin = None

        source = self.config.get("src")

        if custom_line_source is not None:
            self._lines_source = custom_line_source

        elif source.istype(str):
            source_path = source.astype(str)
            assert os.path.isfile(source_path), f"Path {source_path} is not a file"
            self._lines_source = lambda: common.read_lines_or_empty(source_path)

        elif source.istype(dict):
            self._plugin = plugin.registry().create_plugin(source)
            self._lines_source = self._plugin.build

        else:
            assert False, f"Failed to create File plugin from {config}"

    def _to_dict_extra(self):
        if not self._plugin:
            return {}

        return self._plugin._to_dict_extra()

    def build(self):
        self._current_lines = common.read_lines_or_empty(self._destination)
        self._lines = self._lines_source()

    def difference(self):
        return [
            (self._destination, diff.get_diff_lines(self._current_lines, self._lines)),
        ]

    def backup(self):
        with logger().indent("perform_backup"):
            backup_path = self._destination + ".backup"

            if os.path.isfile(self._destination):
                common.copy_file(self._destination, backup_path)
            else:
                logger().warning(
                    [
                        "Not backing up since it does not exist",
                        "loc\t= %s",
                    ],
                    self._destination,
                )

    def apply(self):
        with logger().indent("perform_apply"):
            return common.write_lines(self._lines, self._destination)


plugin.registry().register(File)
