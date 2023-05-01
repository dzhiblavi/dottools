from modules import common
from modules.objects import fileobject


class CopyFileObject(fileobject.FileObject):
    def __init__(self, source, destination):
        self._source = source

        super().__init__(
            destination=destination,
            lines_lazy_source=lambda: common.read_lines_or_empty(self._source),
        )
