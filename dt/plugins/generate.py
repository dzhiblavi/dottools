import os
import jinja2

from dt import common
from dt import context
from dt.config.config import Config
from dt.plugins import plugin


class Generate(plugin.Plugin):
    def __init__(self, config: Config):
        super().__init__(config)
        self._environment = jinja2.Environment()
        self._template = os.path.expanduser(self.config.get("template").astype(str))
        assert os.path.isfile(self._template), f"Path {self._template} is not a file"

    def build(self):
        template = self._environment.from_string(
            "".join(common.read_lines_or_empty(self._template))
        )

        def map_line(line):
            if not line or len(line) == 0:
                return os.linesep

            if line[-1] == os.linesep:
                return line

            return line + os.linesep

        return [
            map_line(line)
            for line in template.render(
                {
                    "ctx": context.context(),
                    "cfg": self.config,
                    "env": os.environ,
                }
            ).split(os.linesep)
        ]


plugin.registry().register(Generate)
