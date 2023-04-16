import os
import yaml
import dd_obj
import util.dd_env as dd_env


def _create_prompt(context, prompt_style, local=None):
    prompt = ''
    for part in prompt_style:
        prompt += context.apply(part, local)
    return prompt


def _get_prompt(context, config):
    host_name = config.get('host-name', '<unknown>')

    with context.logger.silence():
        default_prompt_style = [
            "'<'",
            "fmt('NV', fg='light_green') if ctx.has_gpu else fmt('NONV', fg='light_red')",
            "'> '",
            "'<'",
            "fmt('h', fg='light_green')",
            "'${TMUX:+:\033[0;33mtx/${TMUX_PANE#%}\033[0m}'",
            "':'",
            f"fmt('{host_name}', fg='light_cyan')",
            "'>'",
        ]
        default_prompt = _create_prompt(context, default_prompt_style)

    return _create_prompt(
        context=context,
        prompt_style=config.get('prompt_style', default_prompt_style),
        local={
            'default': default_prompt,
            'default_style': default_prompt_style,
        },
    )


def _create_bashrc(context, bashrc_config):
    def write_info_config(out):
        out.append(": <<END_COMMENT\n")
        out.append("This .bashrc is generated from the following configuration:\n")
        js = yaml.dump(bashrc_config, indent=2).splitlines(True)
        out.extend(js)
        out.append("END_COMMENT\n")

    def write_scripts(out, kind):
        for script_spec in bashrc_config.get(kind, []):
            script_path = context.apply(script_spec)
            with open(script_path, 'r') as script_f:
                out.extend(script_f.readlines())

    def write_base_env(out):
        base_env = {
            dd_env.CONFIG_FILE_PATH_ENV_VAR: context.cfg_path,
            dd_env.HOST_NAME_ENV: context.apply(bashrc_config.get('host-name', 'unknown')),
            dd_env.ROOT_PATH_ENV_VAR: context.dot_root,
            dd_env.BIN_PATH_ENV: context.dot_bin,
            dd_env.LIB_PATH_ENV: context.dot_lib,
            dd_env.DOCKER_PATH_ENV: context.dot_docker,
            dd_env.DOCKER_BIN_PATH_ENV: context.dot_docker_bin,
        }
        for k, v in base_env.items():
            out.append('export {k}={v}\n'.format(k=k, v=v))
        out.append('\n')

    def write_env(out):
        for k, v in bashrc_config.get('env', dict()).items():
            out.append('export {k}={v}\n'.format(k=k, v=v))
        out.append('\n')

    def write_path(out):
        path_env = ''
        for entry in bashrc_config.get('path', []):
            path_env += ':' + context.apply(entry)
        out.append('export PATH={path}:${{PATH}}\n'.format(path=path_env))

    def write_prompt(out):
        if bashrc_config.get('disable_prompt_env', False):
            return
        env = {
            dd_env.PROMPT_ENV_VAR: f"'{_get_prompt(context, bashrc_config)}'",
        }
        for k, v in env.items():
            out.append('export {k}={v}\n'.format(k=k, v=v))
        out.append('\n')

    out = []
    write_scripts(out, 'pre')
    write_info_config(out)
    write_base_env(out)
    write_env(out)
    write_prompt(out)
    write_path(out)
    write_scripts(out, 'post')
    return out


class Bashrc(dd_obj.FileObject):
    def __init__(self, context, bashrc_config):
        dd_obj.FileObject.__init__(
            self, context,
            dst=os.path.expanduser(bashrc_config.get('dst', '~/.bashrc')),
        )

        if not bashrc_config:
            raise AssertionError('None bashrc config has been provided')

        self._config = bashrc_config

    def _generate(self):
        return _create_bashrc(self._context, self._config)


def process(context, bashrc_config):
    bashrc = Bashrc(context, bashrc_config)

    if not bashrc.diff():
        context.logger.info('No difference in .bashrc')
    else:
        bashrc.backup()
        bashrc.apply()
