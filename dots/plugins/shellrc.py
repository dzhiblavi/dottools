from typing import Any, Optional, List, Dict

import yaml

from dots.config.config import Config
from dots.util import env
from dots.context import context
from dots.plugins import plugin, file


def _create_prompt(
    prompt_style: List[str], local: Optional[Dict[str, Any]] = None
) -> str:
    prompt = ""

    for part in prompt_style:
        prompt += context().apply(str(part), local)

    return prompt


def _get_prompt(config: Config) -> str:
    return _create_prompt(
        prompt_style=config.get("prompt-style", []).astype(list),
    )


def _write_info_config(config: Config, out: List[str]) -> None:
    out.append(": <<END_COMMENT\n")
    out.append("This .shellrc is generated from the following configuration:\n")
    js_strs = yaml.dump(config.to_dict(), indent=2).splitlines(True)
    out.extend(js_strs)
    out.append("END_COMMENT\n")


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
        out.append(f"export {k}={value}\n")
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
    path_env = ""
    for entry in config.get("path", []).astype(list):
        path_env += ":" + entry.astype(str)
    out.append(f"export PATH={path_env}:${{PATH}}\n")


def _write_prompt(config: Config, out: List[str]) -> None:
    if config.get("disable_prompt_env", False).astype(bool):
        return

    env_dict = {
        env.PROMPT_ENV_VAR: f"'{_get_prompt(config)}'",
    }

    for k, value in env_dict.items():
        out.append(f"export {k}={value}\n")
    out.append("\n")


def _create_shellrc(config: Config) -> List[str]:
    out: List[str] = []
    _write_scripts(config, "pre", out)
    _write_info_config(config, out)
    _write_base_env(config, out)
    _write_path(config, out)
    _write_prompt(config, out)
    _write_scripts(config, "mid", out)
    _write_assignment(config, "export", "env", out, wrap="")
    _write_assignment(config, "alias", "aliases", out, wrap='"')
    _write_scripts(config, "post", out)
    return out


class Shellrc(file.File):
    def __init__(self, config: Config) -> None:
        super().__init__(
            config=config, custom_line_source=lambda: _create_shellrc(self.config)
        )


plugin.registry().register(Shellrc)
