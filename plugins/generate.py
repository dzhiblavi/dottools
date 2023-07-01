import os
import re

import common
import context
from config import Config
from plugins import plugin
from util.logger import logger


class Generate(plugin.Plugin):
    def __init__(self, config: Config):
        super().__init__(config)

        self._regex = re.compile('{{(.*)}}')
        self._template = os.path.expanduser(self.config.get('template').astype(str))
        assert os.path.isfile(self._template), f'Path {self._template} is not a file'

    def _get_all_evaluations(self, line):
        result = []

        for match in re.finditer(self._regex, line):
            result.append({
                'expression': match.group(0),
                'value': self._eval_match(match),
            })

        return result

    def _to_dict_extra(self):
        params = []

        for line in common.read_lines_or_empty(self._template):
            params.extend(self._get_all_evaluations(line))

        return {'params': params}

    def _eval_match(self, match):
        try:
            return str(eval(  # pylint: disable=eval-used
                match.group(1), {},
                {
                    'ctx': context.context(),
                    'cfg': self.config,
                },
            ))
        except Exception as error:
            logger().error(
                [
                    'Failed to evaluate (( ... ))',
                    'value\t= %s',
                    'error\t= %s',
                ],
                match.group(1), error,
            )
            raise

    def _eval_line(self, line: str) -> str:
        result = re.sub(self._regex, self._eval_match, line)

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
