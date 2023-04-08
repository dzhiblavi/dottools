import os
import sys
import re
import shutil

import dd_diff
import dd_common
import dd_context
import dd_overlay


def process_dot(context, dot_config):
    alias = dot_config.get('alias', '<no-alias>')
    method = dot_config.get('method', 'copy')

    dot_src_path = os.path.expanduser(context.apply(dot_config['src']))
    dot_dst_path = os.path.expanduser(context.apply(dot_config['dst']))
    src_ignore_regex = context.get_ignored_paths(dot_config.get('ignored-paths'))

    with context.logger.indent('diff'):
        any_difference = dd_overlay.has_any_difference(
            context=context,
            src=dot_src_path,
            dst=dot_dst_path,
            ignore_regex=src_ignore_regex,
        )

        if not dd_overlay.created_by_method(
            context,
            dot_src_path,
            dot_dst_path,
            method,
            src_ignore_regex,
        ):
            context.logger.info(
                [
                    'Existsing dot was not created by the specified method',
                    'alias\t= %s',
                    'dst\t= %s',
                    'meth\t= %s',
                ],
                alias, dot_dst_path, method,
            )
            any_difference = True

    with context.logger.indent('action'):
        if not any_difference:
            context.logger.info(
                [
                    'The dot in is up to date, no actions performed',
                    'alias\t= %s',
                    'dst\t= %s',
                    'meth\t= %s',
                ],
                alias, dot_dst_path, method
            )
        else:
            dd_overlay.backup(
                context=context,
                src=dot_src_path,
                dst=dot_dst_path,
                ignore_regex=src_ignore_regex,
            )
            dd_overlay.overlay(
                context=context,
                src=dot_src_path,
                dst=dot_dst_path,
                method=method,
                ignore_regex=src_ignore_regex,
            )


def process(context, dots_config):
    for dot_config in dots_config:
        alias = dot_config.get("alias", "<no-alias>")
        with context.logger.indent(alias):
            if dot_config.get('disabled', False):
                context.logger.info('Dot with alias "%s" is disabled', alias)
                continue

            process_dot(context, dot_config)
