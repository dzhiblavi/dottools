import os

from modules.config import Config
from modules import common, context
from modules.plugins import plugin


class Generate(plugin.Plugin):
    def __init__(self, config: Config):
        super().__init__(config)

        self._template = os.path.expanduser(self.config.get('template').astype(str))
        assert os.path.isfile(self._template), f'Path {self._template} is not a file'

    def _eval_line(self, line: str) -> str:
        try:
            result = eval(  # pylint: disable=eval-used
                line.replace('"', '\"').replace('\\', '\\\\'),
                {},
                {
                    'ctx': context.context(),
                    'cfg': self.config,
                },
            )
        except Exception:  # pylint: disable=broad-except
            return line

        if result[-1] == os.linesep:
            return result

        return result + os.linesep

    def build(self):
        return list(
            map(
                self._eval_line,
                common.read_lines_or_empty(self._template)
            )
        )


plugin.registry().register(Generate)
