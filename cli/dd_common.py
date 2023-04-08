import os
import sys
import logging
import shutil

import dd_diff
import dd_colors
import dd_context


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
    try:
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

    except Exception as e:
        context.logger.warning(
            [
                'failed to remove path',
                'path\t= %s',
                'what\t= %s',
            ],
            file,
            str(e),
        )


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

    with open(file, 'r', encoding='utf-8') as f:
        return list(f.readlines())


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
        with open(path, 'w') as f:
            f.writelines(lines)


def check_same_file(context, src, dst):
    src_expand = os.path.realpath(src)
    dst_expand = os.path.realpath(dst)

    if src_expand == dst_expand:
        context.logger.info(
            [
                'paths point to same location',
                'src\t= %s',
                'dst\t= %s',
            ],
            src, dst,
        )
        return True
    else:
        return False


def create_direct_symlink(context, src, dst):
    if os.path.exists(dst) or os.path.islink(dst):
        context.logger.info(
            [
                'path already exists',
                'path\t= %s',
            ],
            dst,
        )
        try_remove(context, dst)

    _create_parent_dir_if_not_exists(context, dst)

    context.logger.action(
        [
            'creating symlink',
            'src\t= %s',
            'dst\t= %s',
        ],
        dst, src,
    )
    if not context.dry_run:
        os.symlink(src, dst)

    return True


def copy_file(context, src, dst):
    if check_same_file(context, src, dst):
        context.logger.info(
            [
                'cannot copy file since destination exists',
                'src\t= %s',
                'dst\t= %s',
            ],
            src, dst,
        )
        try_remove(context, dst)

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


def files_difference(context, src, dst):
    if check_same_file(context, src, dst):
        context.logger.info(
            [
                'path is already up to date',
                'path=\t= %s',
            ],
            dst,
        )
        return False

    src_lines = read_lines_or_empty(context, src)
    dst_lines = read_lines_or_empty(context, dst)

    diff = dd_diff.get_diff_lines(dst_lines, src_lines)
    if diff:
        context.logger.info(
            [
                'difference between path',
                'src\t= %s',
                'dst\t= %s',
            ],
            src, dst,
        )
        context.logger.write_plain(diff)
        return True
    else:
        context.logger.info(
            [
                'no difference between files',
                'src\t= %s',
                'dst\t= %s',
            ],
            src, dst,
        )
        return False


def is_a_symlink(context, to, path):
    if not os.path.islink(path):
        context.logger.info('%s is not a symlink', path)
        return False
    if os.path.realpath(to) != os.path.realpath(path):
        context.logger.info('%s does not point to %s', path, to)
        return False
    return True
