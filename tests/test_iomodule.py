#!/usr/bin/env python


import unittest,os, shutil, errno
from dirtt.util.io import create_dir, create_file, create_symlink, set_perms_uid_gid, read_file, read_url
from tempfile import NamedTemporaryFile

DEFAULT_PERMS = int("02775", 8)
DEFAULT_USER = 0
DEFAULT_GROUP = 0

class IOModuleTestCase(unittest.TestCase):
    def setUp(self):
        self.tests_dir = os.path.abspath(os.path.dirname(__file__))
        self.test_dirname = os.path.join(self.tests_dir, "dirname")

    def tearDown(self):
        if os.path.exists(self.test_dirname):
            shutil.rmtree(self.test_dirname)



    def test_01_create_dir_with_all_path_components_in_path_not_existing(self):
        """
        Test creating a directory where all components in path don't exist.
        """
        n_path_components = 5
    
        basedir = self.test_dirname

        for i in range(0,n_path_components):
            basedir = os.path.join(basedir, "dir%d" % i)

        create_dir(basedir, DEFAULT_PERMS, DEFAULT_USER, DEFAULT_GROUP)

        self.assertEquals(True, os.path.exists(basedir)) 


    def test_02_create_existing_dir(self):
        """
        Make sure a directory is created even though some components in the path do exist
        """
        n_path_components = 5

        basedir = self.test_dirname

        for i in range(0,n_path_components):
            basedir = os.path.join(basedir, "dir%d" % i)

        os.makedirs(basedir)

        create_dir(basedir, DEFAULT_PERMS, DEFAULT_USER, DEFAULT_GROUP)

        self.assertEquals(True, os.path.exists(basedir)) 

    def test_03_create_dir_with_None_perms_raises_AssertionError(self):
        """
        Make sure an AssertionError is raised if permission are set to None
        """
        self.assertRaises(AssertionError, create_dir, self.test_dirname, None, DEFAULT_USER, DEFAULT_USER, DEFAULT_GROUP) 

    def test_04_create_dir_with_string_perms_raises_TypeError(self):
        """
        Make sure an AssertionError is raised if permission parameter is not int
        """
        self.assertRaises(TypeError, create_dir, self.test_dirname, "02775", DEFAULT_USER, DEFAULT_USER, DEFAULT_GROUP) 

    def test_05_create_dir_with_None_basename_raises_AssertionError(self):
        """
        Make sure an AssertionError is raised if basename is None
        """
        self.assertRaises(AssertionError, create_dir, None, DEFAULT_PERMS, DEFAULT_USER, DEFAULT_GROUP)


    def test_06_create_existing_dir_with_warn_True_raises_OSError(self):
        """
        Make sure an OSError is raised if the directory already exists and warn is set to True.
        """
        os.makedirs(self.test_dirname)
        exception = None

        try:
            create_dir(self.test_dirname, DEFAULT_PERMS, DEFAULT_USER, DEFAULT_GROUP, True)
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
            create_dir(tmp_file.name, DEFAULT_PERMS, DEFAULT_USER, DEFAULT_GROUP, True)
        except Exception as inst:
            exception = inst
        finally:
            if tmp_file:
                os.unlink(tmp_file.name)

        self.assertTrue(type(exception) == OSError)
        self.assertEquals(errno.EEXIST, exception.errno)
 
if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(IOModuleTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
