import os
import shutil

from modules.context import context
from modules.util import diff
from modules.util.logger import logger


def _create_parent_dir_if_not_exists(file_path):
    dir_name = os.path.dirname(file_path)

    if os.path.isdir(dir_name):
        return

    logger().action(
        [
            'creating parent directory',
            'path\t= %s',
            'dir\t= %s',
        ],
        file_path, dir_name,
    )

    if not context().dry_run:
        os.makedirs(dir_name, exist_ok=True)


def try_remove(file):
    logger().action(
        [
            'trying to remove path',
            'path\t= %s',
        ],
        file,
    )

    if not context().dry_run:
        if os.path.isfile(file) or os.path.islink(file):
            os.remove(file)
        elif os.path.isdir(file):
            shutil.rmtree(file)
        elif os.path.islink(file):
            os.unlink(file)


def read_lines_or_empty(file):
    file = os.path.expanduser(file)

    if not os.path.exists(file):
        logger().warning(
            [
                'path does not exist, no lines read',
                'path\t= %s',
            ],
            file,
        )
        return []

    with open(file, 'r', encoding='utf-8') as file_obj:
        return list(file_obj.readlines())


def write_lines(lines, path):
    _create_parent_dir_if_not_exists(path)

    logger().action(
        [
            'writing content to file',
            'path\t= %s',
        ],
        path,
    )

    if not context().dry_run:
        with open(path, 'w', encoding='utf-8') as file:
            file.writelines(lines)


def copy_file(src, dst):
    _create_parent_dir_if_not_exists(dst)

    logger().action(
        [
            'copying file',
            'src\t= %s',
            'dst\t= %s',
        ],
        src, dst,
    )

    if not context().dry_run:
        shutil.copy(src, dst)

    return True


def files_difference(src, dst):
    return diff.get_diff_lines(
        read_lines_or_empty(dst),
        read_lines_or_empty(src),
    )


def recurse_directories(
    src, dst,
    function,
    ignore_regex,
):
    src = os.path.abspath(src)
    dst = os.path.abspath(dst)

    if any(map(lambda pattern: pattern.search(src), ignore_regex)):
        logger().info(
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
                src=path.path,
                dst=os.path.join(dst, path.name),
                function=function,
                ignore_regex=ignore_regex,
            )
        else:
            recurse_directories(
                src=os.path.join(src, path.name),
                dst=os.path.join(dst, path.name),
                function=function,
                ignore_regex=ignore_regex,
            )
