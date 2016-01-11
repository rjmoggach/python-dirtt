#!/usr/bin/env python
import unittest
import os
import shutil
import errno
import stat
import dirtt
from tempfile import NamedTemporaryFile


class IOModuleTestCase(unittest.TestCase):
    @classmethod
    def setup_class(cls):
        """setup any state specific to the execution of the given class"""
        cls.tests_dir = os.path.abspath(os.path.dirname(__file__))
        cls.testing_dirname = "_test"
        cls.testing_dirpath = os.path.join(cls.tests_dir, cls.testing_dirname)

    @classmethod
    def teardown_class(cls):
        if os.path.exists(cls.testing_dirpath):
            shutil.rmtree(cls.testing_dirpath)



    def test_01_create_dir_with_all_path_components_in_path_not_existing(self):
        """
        Test creating a directory where all components in path don't exist.
        """
        n_path_components = 5

        basedir = self.testing_dirpath

        for i in range(0,n_path_components):
            basedir = os.path.join(basedir, "dir%d" % i)

        dirtt.util.create_dir(basedir, dirtt.const('DIRTT_DEFAULT_PERMS'), dirtt.const('DIRTT_DEFAULT_USER'), dirtt.const('DIRTT_DEFAULT_GROUP'))

        self.assertEquals(True, os.path.exists(basedir))


    def test_02_create_existing_dir(self):
        """
        Make sure a directory is created even though some components in the path do exist
        """
        n_path_components = 5

        basedir = self.testing_dirpath

        for i in range(0,n_path_components):
            basedir = os.path.join(basedir, "dir%d" % i)

        os.makedirs(basedir)

        dirtt.util.create_dir(basedir, dirtt.const('DIRTT_DEFAULT_PERMS'), dirtt.const('DIRTT_DEFAULT_USER'), dirtt.const('DIRTT_DEFAULT_GROUP'))

        self.assertEquals(True, os.path.exists(basedir))

    def test_03_create_dir_with_None_perms_raises_AssertionError(self):
        """
        Make sure an AssertionError is raised if permission are set to None
        """
        self.assertRaises(AssertionError, dirtt.util.create_dir, self.testing_dirpath, None, dirtt.const('DIRTT_DEFAULT_USER'), dirtt.const('DIRTT_DEFAULT_USER'), dirtt.const('DIRTT_DEFAULT_GROUP'))

    def test_04_create_dir_with_string_perms_raises_TypeError(self):
        """
        Make sure an AssertionError is raised if permission parameter is not int
        """
        self.assertRaises(TypeError, dirtt.util.create_dir, self.testing_dirpath, "02775", dirtt.const('DIRTT_DEFAULT_USER'), dirtt.const('DIRTT_DEFAULT_USER'), dirtt.const('DIRTT_DEFAULT_GROUP'))

    def test_05_create_dir_with_None_basename_raises_AssertionError(self):
        """
        Make sure an AssertionError is raised if basename is None
        """
        self.assertRaises(AssertionError, dirtt.util.create_dir, None, dirtt.const('DIRTT_DEFAULT_PERMS'), dirtt.const('DIRTT_DEFAULT_USER'), dirtt.const('DIRTT_DEFAULT_GROUP'))


    def test_06_create_existing_dir_with_warn_True_raises_OSError(self):
        """
        Make sure an OSError is raised if the directory already exists and warn is set to True.
        """
        os.makedirs(self.testing_dirpath)
        exception = None

        try:
            dirtt.util.create_dir(self.testing_dirpath, dirtt.const('DIRTT_DEFAULT_PERMS'), dirtt.const('DIRTT_DEFAULT_USER'), dirtt.const('DIRTT_DEFAULT_GROUP'), True)
        except Exception as inst:
            exception = inst

        self.assertTrue(type(exception) == OSError)
        self.assertEquals(errno.EISDIR, exception.errno)


    def test_07_create_dir_with_existing_filename_and_warn_True_raises_OSError(self):
        """
        Make sure an OSError is raised if there is already a file with the same and warn
        is set to True.
        """
        tmp_file = NamedTemporaryFile(delete = False)
        exception = None

        try:
            dirtt.util.create_dir(tmp_file.name, dirtt.const('DIRTT_DEFAULT_PERMS'), dirtt.const('DIRTT_DEFAULT_USER'), dirtt.const('DIRTT_DEFAULT_GROUP'), True)
        except Exception as inst:
            exception = inst
        finally:
            if tmp_file:
                os.unlink(tmp_file.name)

        self.assertTrue(type(exception) == OSError)
        self.assertEquals(errno.EEXIST, exception.errno)

    def test_08_set_perms_uid_gid_with_None_target_raises_AssertionError(self):
        """
        Make sure an assertion error is raised if the target is None
        """
        self.assertRaises(AssertionError,dirtt.posix.set_perms, None, dirtt.const('DIRTT_DEFAULT_PERMS'), dirtt.const('DIRTT_DEFAULT_USER'), dirtt.const('DIRTT_DEFAULT_GROUP'))

    def test_09_set_perms_uid_gid_with_None_perms_raises_AssertionError(self):
        """
        Make sure an assertion error is raised if perms is None
        """
        os.makedirs(self.testing_dirpath)
        self.assertRaises(AssertionError,dirtt.posix.set_perms, self.testing_dirpath, None, dirtt.const('DIRTT_DEFAULT_USER'), dirtt.const('DIRTT_DEFAULT_GROUP'))

    def test_10_set_perms_uid_gid_with_none_existing_target_raises_OSError(self):
        """
        Make sure an OS error is raised if the path does not exist
        """
        self.assertRaises(OSError,dirtt.posix.set_perms, self.testing_dirpath, dirtt.const('DIRTT_DEFAULT_PERMS'), dirtt.const('DIRTT_DEFAULT_USER'), dirtt.const('DIRTT_DEFAULT_GROUP'))

    def test_11_set_perms_uid_gid_on_non_existing_directory_with_DIRTT_DEFAULT_PERMS(self):
        """
        Make sure permissions are properly set on directories
        """
        os.makedirs(self.testing_dirpath)
        dirtt.posix.set_perms(self.testing_dirpath, dirtt.const('DIRTT_DEFAULT_PERMS'), dirtt.const('DIRTT_DEFAULT_USER'), dirtt.const('DIRTT_DEFAULT_GROUP'))

        st_mode = os.stat(self.testing_dirpath).st_mode

        # Test user permissions
        self.assertEquals(stat.S_IRUSR, st_mode & stat.S_IRUSR)
        self.assertEquals(stat.S_IWUSR, st_mode & stat.S_IWUSR)
        self.assertEquals(stat.S_IXUSR, st_mode & stat.S_IXUSR)

        # Test group permissions
        self.assertEquals(stat.S_IRGRP, st_mode & stat.S_IRGRP)
        self.assertEquals(stat.S_IWGRP, st_mode & stat.S_IWGRP)
        self.assertEquals(stat.S_IXGRP, st_mode & stat.S_IXGRP)

        # Test others permissions
        self.assertEquals(stat.S_IROTH, st_mode & stat.S_IROTH)
        self.assertEquals(0, st_mode & stat.S_IWOTH)
        self.assertEquals(stat.S_IXOTH, st_mode & stat.S_IXOTH)


    def test_12_set_perms_uid_gid_on_non_existing_file(self):
        """
        Make sure permissions are properly set on files
        """
        tmp_file = NamedTemporaryFile(delete = False)
        exception = None

        try:
            dirtt.posix.set_perms(tmp_file.name, 0666, dirtt.const('DIRTT_DEFAULT_USER'), dirtt.const('DIRTT_DEFAULT_GROUP'))
            st_mode = os.stat(tmp_file.name).st_mode

            # Test user permissions
            self.assertEquals(stat.S_IRUSR, st_mode & stat.S_IRUSR)
            self.assertEquals(stat.S_IWUSR, st_mode & stat.S_IWUSR)
            self.assertEquals(0, st_mode & stat.S_IXUSR)

            # Test group permissions
            self.assertEquals(stat.S_IRGRP, st_mode & stat.S_IRGRP)
            self.assertEquals(stat.S_IWGRP, st_mode & stat.S_IWGRP)
            self.assertEquals(0, st_mode & stat.S_IXGRP)

            # Test others permissions
            self.assertEquals(stat.S_IROTH, st_mode & stat.S_IROTH)
            self.assertEquals(stat.S_IWOTH, st_mode & stat.S_IWOTH)
            self.assertEquals(0, st_mode & stat.S_IXOTH)
        finally:
            if tmp_file:
                os.unlink(tmp_file.name)


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(IOModuleTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
