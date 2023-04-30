import os
from modules import obj


def process(context, dots_config):
    def process_action(dot_config):
        with context.logger.indent(alias):
            if dot_config.get('disabled', False).astype(bool):
                context.logger.info('Dot is disabled', alias)
                return

            src = os.path.expanduser(dot_config.get('src').astype(str))
            dst = os.path.expanduser(dot_config.get('dst').astype(str))

            if os.path.isdir(src):
                objt = obj.CopyDirObject(context, src, dst, dot_config.ignored_paths())
            elif os.path.isfile(src):
                objt = obj.CopyFileObject(context, src, dst)
            else:
                raise AssertionError(f'unknown entity (source): {src}')

            if not objt.diff():
                context.logger.info('dotfile is up to date')
            else:
                objt.backup()
                objt.apply()

    for dot_config in dots_config.astype(list):
        alias = dot_config.get("alias", "<no-alias>").astype(str)

        if 'actions' in dot_config:
            for action in dot_config.get('actions').astype(list):
                process_action(action)
