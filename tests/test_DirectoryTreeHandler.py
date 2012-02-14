#!/usr/bin/env python

import unittest,os
from dirtt import DirectoryTreeHandler

class DirectoryTreeHandlerTestCase(unittest.TestCase):
    def setUp(self):
        self.default_project_location = "project.xml"

    def test_01_new_DirectoryTreeHandler_with_None_tree_template_raises_AssertError(self):
        """
        Create a DirectoryTreeHandler with a None tree template path
        """
        self.assertRaises(AssertionError, DirectoryTreeHandler,True,None,{})

    def test_02_get_verbose_after_create_DirectoryTreeHandler_with_verbose_True_returns_True(self):
        """
        Create a DirectoryTreeHandler with verbose set to True
        """
        handler = DirectoryTreeHandler(True,self.default_project_location,{})
        self.assertEqual(True, handler.verbose, "Verbose level must be true")

    def test_03_get_verbose_after_create_DirectoryTreeHandler_with_verbose_False_returns_False(self):
        """
        Create a DirectoryTreeHandler with verbose set to False
        """
        handler = DirectoryTreeHandler(False,self.default_project_location,{})
        self.assertEqual(False, handler.verbose, "Verbose level must be false")

    def test_04_new_DirectoryTreeHandler_with_non_existing_tree_template_raises_OSError(self):
        """
        Create a DirectoryTreeHandler with a path to a non existing tree template path. We expect
        an OSError exception to be raised.
        """
        handler = DirectoryTreeHandler(False,"non_existing_file_location.xml",{})
        self.assertRaises(OSError, handler.run)

    def test_05_new_DirectoryTreeHandler_with_directory_path_as_tree_template_raises_OSError(self):
        """
        Create a DirectoryTreeHandler with a tree template path pointing to a directory. We expect
        an OSError exception to be raised.
        """
        test_dir_name = "test_dir"
        if not os.path.exists(test_dir_name):
            os.mkdir(test_dir_name)
        else:
            os.rmdir(test_dir_name)

        handler = DirectoryTreeHandler(False,test_dir_name, {})
        self.assertRaises(OSError, handler.run)

    def test_06_get_tree_template_after_create_DirectoryTreeHandler_with_tree_template_location_X_returns_X(self):
        """
        Create a DirectoryTreeHandler with a tree template path and make sure the tree_template variable from
        DirectoryTreeHandler is properly set.
        """
        handler = DirectoryTreeHandler(False,self.default_project_location, {})
        self.assertEquals(self.default_project_location, handler.tree_template)

    
if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(DirectoryTreeHandlerTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
