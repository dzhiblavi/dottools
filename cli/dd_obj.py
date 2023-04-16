import os
import dd_common
from functools import partial


class Object:
    def __init__(self, context):
        self._context = context

    def diff(self):
        raise NotImplementedError('diff is not implemented')

    def backup(self):
        raise NotImplementedError('backup is not implemented')

    def apply(self):
        raise NotImplementedError('apply is not implemented')


class FileObject(Object):
    def __init__(self, context, dst):
        Object.__init__(self, context)

        self._dst = dst
        self._current_lines = dd_common.read_lines_or_empty(self._context, self._dst)
        self._generated_lines = None

    def _generate(self):
        raise NotImplementedError('generate is not implemented for FileObject')

    def _generated(self):
        if not self._generated_lines:
            self._generated_lines = self._generate()

        return self._generated_lines

    def diff(self):
        with self._context.logger.indent('diff'):
            return dd_common.print_difference(
                context=self._context,
                lines_a=self._current_lines,
                lines_b=self._generated(),
                obj=self._dst,
            )

    def backup(self):
        with self._context.logger.indent('backup'):
            backup_path = self._dst + '.backup'

            if os.path.isfile(self._dst):
                dd_common.copy_file(self._context, self._dst, backup_path)
            else:
                self._context.logger.warning(
                    [
                        'Not backing up since it does not exist',
                        'loc\t= %s',
                    ],
                    self._dst,
                )

    def apply(self):
        with self._context.logger.indent('action'):
            return dd_common.write_lines(self._context, self._generated(), self._dst)


class CopyFileObject(FileObject):
    def __init__(self, context, src, dst):
        FileObject.__init__(self, context, dst)
        self._src = src

    def _generate(self):
        return dd_common.read_lines_or_empty(self._context, self._src)


class CopyDirObject(Object):
    def __init__(self, context, src, dst, ignore_regex):
        Object.__init__(self, context)
        self._ignore_regex = ignore_regex
        self._src = src
        self._dst = dst

    def diff(self):
        self._diff_abspaths = []
        self._paths_to_remove = []

        def diff_fn(dst_list, src_path, dst_path):
            if dd_common.files_difference(
                context=self._context,
                src=src_path,
                dst=dst_path,
            ):
                dst_list.append((src_path, dst_path))

        with self._context.logger.indent('diff(+/~)'):
            dd_common.recurse_directories(
                self._context, self._src, self._dst,
                partial(diff_fn, self._diff_abspaths),
                self._ignore_regex,
            )

        def rm_fn(dst_path, src_path):
            if not os.path.exists(src_path):
                self._context.logger.info(
                    [
                        'Path does not exist in source tree (needs to be removed)',
                        'path\t= %s',
                    ],
                    src_path,
                )
                self._paths_to_remove.append(dst_path)

        with self._context.logger.indent('diff(-)'):
            if os.path.exists(self._dst):
                dd_common.recurse_directories(
                    self._context, self._dst, self._src, rm_fn, self._ignore_regex,
                )

        return bool(self._diff_abspaths) or bool(self._paths_to_remove)

    def backup(self):
        backup_dir = self._dst + '.backup'
        dst_to_backup = self._paths_to_remove + [dst for _, dst in self._diff_abspaths]

        with self._context.logger.indent('backup'):
            for dst in dst_to_backup:
                if not os.path.exists(dst):
                    continue

                backup_dst = os.path.join(backup_dir, os.path.relpath(dst, self._dst))
                dd_common.copy_file(self._context, dst, backup_dst)

    def apply(self):
        with self._context.logger.indent('apply'):
            for src, dst in self._diff_abspaths:
                dd_common.copy_file(self._context, src, dst)

            for dst in self._paths_to_remove:
                dd_common.try_remove(self._context, dst)

