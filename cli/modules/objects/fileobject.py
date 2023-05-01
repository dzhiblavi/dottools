import os

from modules import common
from modules.objects import object
from modules.util import logger, diff


class FileObject(object.Object):
    def __init__(self, destination, lines_lazy_source):
        super().__init__()

        self._destination = destination
        self._lines_lazy_source = lines_lazy_source

        self._lines = None
        self._current_lines = None

    def build(self):
        self._lines = self._lines_lazy_source()
        self._current_lines = common.read_lines_or_empty(self._destination)

    def difference(self):
        return [
            (self._destination, diff.get_diff_lines(self._current_lines, self._lines)),
        ]

    def backup(self):
        with logger.logger().indent('backup'):
            backup_path = self._destination + '.backup'

            if os.path.isfile(self._destination):
                common.copy_file(self._destination, backup_path)
            else:
                logger.logger().warning(
                    [
                        'Not backing up since it does not exist',
                        'loc\t= %s',
                    ],
                    self._destination,
                )

    def apply(self):
        with logger.logger().indent('action'):
            return common.write_lines(self._lines, self._destination)
