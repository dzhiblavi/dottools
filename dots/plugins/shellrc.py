from typing import Any, Optional, List, Dict

import yaml

from dots.config.config import Config
from dots.util import env
from dots.context import context
from dots.plugins import plugin, file


def _write_scripts(config: Config, kind: str, out: List[str]) -> None:
    for script_path in config.get(kind, []).astype(list):
        with open(script_path.astype(str), "r", encoding="utf-8") as script_f:
            out.extend(script_f.readlines())


def _write_base_env(config: Config, out: List[str]) -> None:
    base_env = {
        env.CONFIG_FILE_PATH_ENV_VAR: context().cfg_path,
        env.HOST_NAME_ENV: config.get("host-name", "unknown").astype(str),
        env.ROOT_PATH_ENV_VAR: context().dottools_root,
    }
    for k, value in base_env.items():
        out.append(f'export {k}="{value}"\n')
    out.append("\n")


def _write_assignment(
    config: Config, prefix: str, field: str, out: List[str], wrap=None
):
    if wrap is None:
        wrap = ""

    for key, value in config.get(field, {}).astype(dict).items():
        out.append(f"{prefix} {key}={wrap}{str(value)}{wrap}\n")
    out.append("\n")


def _write_path(config: Config, out: List[str]) -> None:
    paths = config.get("path", []).astype(list)

    if not paths:
        return

    path_env = ""
    for entry in paths:
        path_env += ":" + entry.astype(str)

    out.append(f"export PATH={path_env}:${{PATH}}\n")


def _create_shellrc(config: Config) -> List[str]:
    minimal = config.getp("minimal", False).astype(bool)

    out: List[str] = []
    _write_scripts(config, "pre", out)
    if not minimal:
        _write_base_env(config, out)
    _write_path(config, out)
    _write_scripts(config, "mid", out)
    _write_assignment(config, "export", "env", out, wrap='"')
    _write_assignment(config, "alias", "aliases", out, wrap='"')
    _write_scripts(config, "post", out)
    return out


class Shellrc(file.File):
    def __init__(self, config: Config) -> None:
        super().__init__(
            config=config, custom_line_source=lambda: _create_shellrc(self.config)
        )


plugin.registry().register(Shellrc)
