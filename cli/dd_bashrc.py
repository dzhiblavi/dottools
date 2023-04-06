import os
import sys
import yaml
import shutil
import logging

import dd_diff
import dd_context
import dd_overlay
import dd_common
import dd_env


def create_prompt(context, prompt_style, local=None):
    prompt = ''
    for part in prompt_style:
        prompt += context.apply(part, local)
    return prompt


def get_prompt(context, config):
    host_name = config.get('host-name', '<unknown>')

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
    default_prompt = create_prompt(context, default_prompt_style)

    return create_prompt(
        context=context,
        prompt_style=config.get('prompt_style', default_prompt_style),
        local={
            'default': default_prompt,
            'default_style': default_prompt_style,
        },
    )


def create_bashrc(context, bashrc_config):
    def write_info_config(out):
        out.append(": <<END_COMMENT\n")
        out.append("This .bashrc is generated from the following configuration:\n")
        js = yaml.dump(bashrc_config, indent=2).splitlines(True)
        js[-1] += '\n'
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
            dd_env.PROMPT_ENV_VAR: f"'{get_prompt(context, bashrc_config)}'",
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


def process(context, bashrc_config):
    bashrc_location = os.path.expanduser(bashrc_config.get('dst', '~/.bashrc'))
    generated_path = context.dot_generated + '/bashrc'
    method = bashrc_config.get('method', 'copy')

    with context.logger.indent('generate'):
        with context.disable_dry_run():
            dd_common.write_lines(
                context=context,
                lines=create_bashrc(context, bashrc_config),
                path=generated_path,
            )

    with context.logger.indent('diff'):
        any_difference = dd_overlay.has_any_difference(
            context=context,
            src=generated_path,
            dst=bashrc_location,
        )

        if not dd_overlay.created_by_method(context, generated_path, bashrc_location, method):
            context.logger.info('existsing path %s was not created via %s', bashrc_location, method)
            any_difference = True

    with context.logger.indent('action'):
        if not any_difference:
            context.logger.info(
                'The bashrc located in %s is up to date, no actions performed', bashrc_location,
            )
        else:
            dd_overlay.backup(
                context=context,
                src=generated_path,
                dst=bashrc_location,
            )
            dd_overlay.overlay(
                context=context,
                src=generated_path,
                dst=bashrc_location,
                method=method,
            )
