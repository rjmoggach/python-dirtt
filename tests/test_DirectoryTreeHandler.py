#!/usr/bin/env python

import unittest
from dirtt import DirectoryTreeHandler

class DirectoryTreeHandlerTestCase(unittest.TestCase):
    def setUp(self):
        self.default_project_location = "project.xml"

    def test_01_new_DirectoryTreeHandler_with_None_tree_template(self):
        self.assertRaises(AssertionError, DirectoryTreeHandler,True,None,{})

    # Create a DirectoryTreeHandler with verbose set to True
    def test_02_new_DirectoryTreeHandler_with_verbose_True(self):
        handler = DirectoryTreeHandler(True,self.default_project_location,{})
        self.assertEqual(True, handler.verbose, "Verbose level must be true")

    # Create a DirectoryTreeHandler with verbose set to False
    def test_03_new_DirectoryTreeHandler_with_verbose_False(self):
        handler = DirectoryTreeHandler(False,self.default_project_location,{})
        self.assertEqual(False, handler.verbose, "Verbose level must be false")

    def test_04_new_DirectoryTreeHandler_with_non_existing_tree_template(self):
        handler = DirectoryTreeHandler(False,"non_existing_file_location.xml",{})
        handler.run()

    




if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(DirectoryTreeHandlerTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
