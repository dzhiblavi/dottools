import os
import yaml

from modules import obj
from modules.util import env


def _create_prompt(context, prompt_style, local=None):
    prompt = ''

    for part in prompt_style:
        try:
            prompt += context.apply(str(part), local)
        except Exception:
            prompt += str(part)

    return prompt


def _get_prompt(context, config):
    return _create_prompt(
        context=context,
        prompt_style=config.get('prompt-style').astype(list),
    )


def _create_shellrc(context, shellrc_config):
    def write_info_config(out):
        out.append(": <<END_COMMENT\n")
        out.append("This .shellrc is generated from the following configuration:\n")
        js_strs = yaml.dump(shellrc_config.to_dict(), indent=2).splitlines(True)
        out.extend(js_strs)
        out.append("END_COMMENT\n")

    def write_scripts(out, kind):
        for script_path in shellrc_config.get(kind, []).astype(list):
            with open(script_path.astype(str), 'r', encoding='utf-8') as script_f:
                out.extend(script_f.readlines())

    def write_base_env(out):
        base_env = {
            env.CONFIG_FILE_PATH_ENV_VAR: context.cfg_path,
            env.HOST_NAME_ENV: shellrc_config.get('host-name', 'unknown').astype(str),
            env.ROOT_PATH_ENV_VAR: context.dot_root,
            env.BIN_PATH_ENV: context.dot_bin,
            env.LIB_PATH_ENV: context.dot_lib,
            env.DOCKER_PATH_ENV: context.dot_docker,
            env.DOCKER_BIN_PATH_ENV: context.dot_docker_bin,
        }
        for k, value in base_env.items():
            out.append(f'export {k}={value}\n')
        out.append('\n')

    def write_env(out):
        for k, value in shellrc_config.get('env', {}).astype(dict).items():
            if shellrc_config.is_config_key(k):
                continue
            out.append(f'export {k}={str(value)}\n')
        out.append('\n')

    def write_path(out):
        path_env = ''
        for entry in shellrc_config.get('path', []).astype(list):
            path_env += ':' + entry.astype(str)
        out.append(f'export PATH={path_env}:${{PATH}}\n')

    def write_prompt(out):
        if shellrc_config.get('disable_prompt_env', False).astype(bool):
            return

        env_dict = {
            env.PROMPT_ENV_VAR: f"'{_get_prompt(context, shellrc_config)}'",
        }

        for k, value in env_dict.items():
            out.append(f'export {k}={value}\n')
        out.append('\n')

    out = []
    write_scripts(out, 'pre')
    write_info_config(out)
    write_base_env(out)
    write_env(out)
    write_prompt(out)
    write_path(out)
    write_scripts(out, 'mid')
    write_scripts(out, 'post')
    return out


class Shellrc(obj.FileObject):
    def __init__(self, context, shellrc_config):
        obj.FileObject.__init__(
            self, context,
            dst=os.path.expanduser(shellrc_config.get('dst').astype(str)),
        )

        if not shellrc_config:
            raise AssertionError('No shellrc config has been provided')

        self._config = shellrc_config

    def _generate(self):
        return _create_shellrc(self._context, self._config)


def process(context, shellrc_config):
    shellrc = Shellrc(context, shellrc_config)

    if not shellrc.diff():
        context.logger.info('No difference in .shellrc')
    else:
        shellrc.backup()
        shellrc.apply()
