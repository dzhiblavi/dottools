import os

from modules.plugins import plugin
from modules.objects import copy_fileobject, copy_dirobject


class Copy(plugin.Plugin):
    def __init__(self, config):
        super().__init__(config)

        self._config = config
        self._disabled = self._config.get('disabled', False).astype(bool)

        source_path = os.path.expanduser(self._config.get('src').astype(str))
        destination_path = os.path.expanduser(self._config.get('dst').astype(str))

        if os.path.isdir(source_path):
            self._object = copy_dirobject.CopyDirObject(
                source=source_path,
                destination=destination_path,
                ignore_regex=config.ignored_paths(),
            )
        else:
            self._object = copy_fileobject.CopyFileObject(
                source=source_path,
                destination=destination_path,
            )

    def build(self):
        self._object.build()

    def difference(self):
        return [(Copy.__name__, self._object.difference())]

    def backup(self):
        return [(Copy.__name__, self._object.backup())]

    def apply(self):
        return [(Copy.__name__, self._object.apply())]


plugin.registry().register(Copy)
