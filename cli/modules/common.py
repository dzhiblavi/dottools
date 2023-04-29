import os
import shutil

from modules.util import diff


def _create_parent_dir_if_not_exists(context, file_path):
    dir_name = os.path.dirname(file_path)

    if os.path.isdir(dir_name):
        return

    context.logger.action(
        [
            'creating parent directory',
            'path\t= %s',
            'dir\t= %s',
        ],
        file_path, dir_name,
    )

    if not context.dry_run:
        os.makedirs(dir_name, exist_ok=True)


def try_remove(context, file):
    context.logger.action(
        [
            'trying to remove path',
            'path\t= %s',
        ],
        file,
    )

    if not context.dry_run:
        if os.path.isfile(file) or os.path.islink(file):
            os.remove(file)
        elif os.path.isdir(file):
            shutil.rmtree(file)
        elif os.path.islink(file):
            os.unlink(file)


def read_lines_or_empty(context, file):
    file = os.path.expanduser(file)

    if not os.path.exists(file):
        context.logger.warning(
            [
                'path does not exist, no lines read',
                'path\t= %s',
            ],
            file,
        )
        return []

    with open(file, 'r', encoding='utf-8') as file_obj:
        return list(file_obj.readlines())


def write_lines(context, lines, path):
    _create_parent_dir_if_not_exists(context, path)

    context.logger.action(
        [
            'writing content to file',
            'path\t= %s',
        ],
        path,
    )

    if not context.dry_run:
        with open(path, 'w', encoding='utf-8') as file:
            file.writelines(lines)


def copy_file(context, src, dst):
    _create_parent_dir_if_not_exists(context, dst)

    context.logger.action(
        [
            'copying file',
            'src\t= %s',
            'dst\t= %s',
        ],
        src, dst,
    )

    if not context.dry_run:
        shutil.copy(src, dst)

    return True


def print_difference(context, lines_a, lines_b, obj):
    difference = diff.get_diff_lines(lines_a, lines_b)
    if difference:
        context.logger.log_diff(
            [
                'Diff for object',
                'obj\t= %s',
                '%s',
            ],
            obj, ''.join(difference),
        )
        return True

    return False


def files_difference(context, src, dst):
    src_lines = read_lines_or_empty(context, src)
    dst_lines = read_lines_or_empty(context, dst)

    difference = diff.get_diff_lines(dst_lines, src_lines)

    if difference:
        context.logger.log_diff(
            [
                'Diff for files',
                'src\t= %s',
                'dst\t= %s',
                '%s',
            ],
            src, dst, ''.join(difference),
        )
        return True

    return False


def recurse_directories(
    context,
    src, dst,
    function,
    ignore_regex,
):
    src = os.path.abspath(src)
    dst = os.path.abspath(dst)

    if any(map(lambda pattern: pattern.search(src), ignore_regex)):
        context.logger.info(
            [
                'Ignoring path',
                'path\t= %s',
            ],
            src
        )
        return

    if os.path.isfile(src):
        function(src, dst)
        return

    for path in os.scandir(src):
        if path.is_file():
            recurse_directories(
                context=context,
                src=path.path,
                dst=os.path.join(dst, path.name),
                function=function,
                ignore_regex=ignore_regex,
            )
        else:
            recurse_directories(
                context=context,
                src=os.path.join(src, path.name),
                dst=os.path.join(dst, path.name),
                function=function,
                ignore_regex=ignore_regex,
            )
