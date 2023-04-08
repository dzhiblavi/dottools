import os
import sys
import shutil
import logging

import dd_diff
import dd_common

from functools import partial

def _recursive_files_or(
    context,
    src, dst,
    function,
    ignore_regex=None,
):
    if ignore_regex is None:
        ignore_regex = []

    if any(map(lambda pattern: pattern.search(src), ignore_regex)):
        return False

    if os.path.isfile(src):
        return function(src, dst)

    if not os.path.exists(src):
        context.logger.warning(
            [
                'Path does not exist, skipping',
                'path\t= %s',
            ],
            src,
        )
        return False

    result = False
    for path in os.scandir(src):
        if path.is_file():
            value = _recursive_files_or(
                context=context,
                src=path.path,
                dst=os.path.join(dst, path.name),
                function=function,
                ignore_regex=ignore_regex,
            ) 
        else:
            value = _recursive_files_or(
                context=context,
                src=src + '/' + path.name,
                dst=dst + '/' + path.name,
                function=function,
                ignore_regex=ignore_regex,
            )
        result = result or value
    return result


def overlay(
    context,
    src, dst,
    method,
    ignore_regex=None,
):
    if method == 'copy':
        return _recursive_files_or(
            context,
            src, dst,
            partial(dd_common.copy_file, context),
            ignore_regex,
        )

    assert False, f'Invalid overlay method: {method}'


def has_any_difference(context, src, dst, ignore_regex=None):
    return _recursive_files_or(
        context,
        src, dst,
        partial(dd_common.files_difference, context),
        ignore_regex,
    )


def _backup_file(context, src, dst):
    if not os.path.exists(dst):
        context.logger.info(
            [
                'not backing up file since it does not exist',
                'path\t= %s',
            ],
            dst,
        )
        dd_common.try_remove(context, dst)
        return

    dst = os.path.abspath(dst)
    backup_path = '.' + dst + ('.backup' if not context.dry_run else '.backup.dry_run')

    context.logger.info(
        [
            'backing up file',
            'from\t= %s',
            'to\t= %s',
        ],
        dst, backup_path,
    )

    dd_common.copy_file(context, dst, backup_path)

    return True


def backup(context, src, dst, ignore_regex=None):
    if ignore_regex is None:
        ignore_regex = []

    if any(map(lambda pattern: bool(pattern.match(src)), ignore_regex)):
        context.logger.info(
            [
                'not backing up path since it is ignored',
                'path\t= %s',
            ],
            src,
        )
        return

    if os.path.isfile(src):
        return _backup_file(context, src, dst)

    dst = os.path.abspath(dst)
    backup_path = dst + ('.backup' if not context.dry_run else '.backup.dry_run')

    if not os.path.exists(dst):
        context.logger.info(
            [
                'not backing up path since it does not exist',
                'path\t= %s',
            ],
            dst,
        )

        dd_common.try_remove(context, dst)
        return

    context.logger.info(
        [
            'performing backup of directory',
            'path\t= %s',
            'bckp\t= %s',
        ],
        dst, backup_path,
    )

    def copy_if_in_src(src_file, dst_file):
        src_relpath = os.path.relpath(src_file, dst)

        if not os.path.exists(os.path.join(src, src_relpath)):
            return False

        context.logger.info(
            [
                'Backing up file',
                'path\t= %s',
                'bckp\t= %s',
            ],
            src_file, dst_file,
        )
        dd_common.copy_file(context, src_file, dst_file)

        return True

    return _recursive_files_or(context, dst, backup_path, copy_if_in_src, ignore_regex)


def created_by_method(context, src, dst, method, ignore_regex=None):
    if method == 'copy':
        if os.path.islink(dst):
            context.logger.info(
                [
                    'path is a symlink: could not be created by copy method',
                    'path\t= %s',
                ],
                dst,
            )
            return False
        return True

    assert False, f'Invalid overlay method: {method}'
