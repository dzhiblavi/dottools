import os
import dd_obj


def process(context, dots_config):
    def process_action(dot_config):
        with context.logger.indent(alias):
            if dot_config.get('disabled', False):
                context.logger.info('Dot is disabled', alias)
                return

            src = os.path.expanduser(context.apply(dot_config['src']))
            dst = os.path.expanduser(context.apply(dot_config['dst']))

            if os.path.isdir(src):
                ignore_regex = context.get_ignored_paths(dot_config.get('ignored-paths'))
                obj = dd_obj.CopyDirObject(context, src, dst, ignore_regex)
            elif os.path.isfile(src):
                obj = dd_obj.CopyFileObject(context, src, dst)
            else:
                raise AssertionError(f'unknown entity (source): {src}')

            if not obj.diff():
                context.logger.info('dotfile is up to date')
            else:
                obj.backup()
                obj.apply()

    for dot_config in dots_config:
        alias = dot_config.get("alias", "<no-alias>")

        if 'actions' in dot_config:
            for action in dot_config['actions']:
                process_action(action)
