import yaml

from modules.util import env
from modules.context import context
from modules.plugins import plugin, file


def _create_prompt(prompt_style, local=None):
    prompt = ''

    for part in prompt_style:
        prompt += context().apply(str(part), local)

    return prompt


def _get_prompt(config):
    return _create_prompt(
        prompt_style=config.get('prompt-style', []).astype(list),
    )


def _write_info_config(config, out):
    out.append(": <<END_COMMENT\n")
    out.append("This .shellrc is generated from the following configuration:\n")
    js_strs = yaml.dump(config.to_dict(), indent=2).splitlines(True)
    out.extend(js_strs)
    out.append("END_COMMENT\n")


def _write_scripts(config, out, kind):
    for script_path in config.get(kind, []).astype(list):
        with open(script_path.astype(str), 'r', encoding='utf-8') as script_f:
            out.extend(script_f.readlines())


def _write_base_env(config, out):
    base_env = {
        env.CONFIG_FILE_PATH_ENV_VAR: context().cfg_path,
        env.HOST_NAME_ENV: config.get('host-name', 'unknown').astype(str),
        env.ROOT_PATH_ENV_VAR: context().dot_root,
        env.BIN_PATH_ENV: context().dot_bin,
        env.LIB_PATH_ENV: context().dot_lib,
        env.DOCKER_PATH_ENV: context().dot_docker,
        env.DOCKER_BIN_PATH_ENV: context().dot_docker_bin,
    }
    for k, value in base_env.items():
        out.append(f'export {k}={value}\n')
    out.append('\n')


def _write_env(config, out):
    for k, value in config.get('env', {}).astype(dict).items():
        if config.is_config_key(k):
            continue
        out.append(f'export {k}={str(value)}\n')
    out.append('\n')


def _write_path(config, out):
    path_env = ''
    for entry in config.get('path', []).astype(list):
        path_env += ':' + entry.astype(str)
    out.append(f'export PATH={path_env}:${{PATH}}\n')


def _write_prompt(config, out):
    if config.get('disable_prompt_env', False).astype(bool):
        return

    env_dict = {
        env.PROMPT_ENV_VAR: f"'{_get_prompt(config)}'",
    }

    for k, value in env_dict.items():
        out.append(f'export {k}={value}\n')
    out.append('\n')


def _create_shellrc(config):
    out = []
    _write_scripts(config, out, 'pre')
    _write_info_config(config, out)
    _write_base_env(config, out)
    _write_env(config, out)
    _write_prompt(config, out)
    _write_path(config, out)
    _write_scripts(config, out, 'mid')
    _write_scripts(config, out, 'post')
    return out


class Shellrc(file.File):
    def __init__(self, config):
        super().__init__(
            config=config,
            custom_line_source=lambda: _create_shellrc(self.config)
        )


plugin.registry().register(Shellrc)
