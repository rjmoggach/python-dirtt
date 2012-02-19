#!/usr/bin/env python

import unittest,os,shutil
import threading
import SimpleHTTPServer
import SocketServer
import logging
from dirtt import DirectoryTreeHandler

class HttpServerThread(threading.Thread):
    
    def __init__(self, start_dir, port = 8080):
        threading.Thread.__init__(self)
        self.start_dir = start_dir
        self.port = port
        self.running = False
        self.httpd = None
        os.chdir(self.start_dir)

    def run(self):
        os.chdir(self.start_dir)
        Handler = SimpleHTTPServer.SimpleHTTPRequestHandler

        self.running = True
        try:
            self.httpd = SocketServer.TCPServer(("", self.port), Handler)
            self.httpd.handle_request()
        except Exception as e:
            self.running = False
            raise e

    def stop(self):
        if self.running and self.httpd is not None:
            self.httpd.server_close()
            self.running = False




class DirectoryTreeHandlerTestCase(unittest.TestCase):
    def setUp(self):
        self.tests_dir = os.path.abspath(os.path.dirname(__file__))
        self.templates_dir = os.path.join(self.tests_dir, "templates")
        self.project_path = "data"
        self.default_project_location = os.path.join(self.templates_dir, "default_test_project.xml")
        self.default_args = {"project_root":self.tests_dir, "project_path": self.project_path}
        self.http_port = 8080

    def test_01_new_DirectoryTreeHandler_with_None_tree_template_raises_AssertError(self):
        """
        Create a DirectoryTreeHandler with a None tree template path
        """
        self.assertRaises(AssertionError, DirectoryTreeHandler,True,None,{})

#    def test_02_get_logger_level_after_create_DirectoryTreeHandler_with_verbose_True_returns_DEBUG(self):
#        """
#        Create a DirectoryTreeHandler with verbose set to True
#        """
#        handler = DirectoryTreeHandler(True,self.default_project_location,{})
#        self.assertEquals(logging.DEBUG, handler.logger.level)
#
#    def test_03_get_logger_level_after_create_DirectoryTreeHandler_with_verbose_False_returns_ERROR(self):
#        """
#        Create a DirectoryTreeHandler with verbose set to False
#        """
#        handler = DirectoryTreeHandler(False,self.default_project_location,{})
#        self.assertEquals(logging.ERROR, handler.logger.level)
#
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
        test_dir_name = os.path.join(os.path.abspath(os.path.dirname(__file__)),"test_dir")
        if os.path.exists(test_dir_name):
            os.rmdir(test_dir_name)
        os.mkdir(test_dir_name)

        handler = DirectoryTreeHandler(False,test_dir_name, {})
        self.assertRaises(OSError, handler.run)

    def test_06_get_tree_template_after_create_DirectoryTreeHandler_with_tree_template_location_X_returns_X(self):
        """
        Create a DirectoryTreeHandler with a tree template path and make sure the tree_template variable from
        DirectoryTreeHandler is properly set.
        """
        handler = DirectoryTreeHandler(False,self.default_project_location, {})
        self.assertEquals(self.default_project_location, handler.tree_template)


    def test_07_get_interactive_after_create_DirectoryTreeHandler_with_interactive_True_returns_True(self):
        """
        Create a directory with interactive set to True and make sure the value is properly set.
        """
        handler = DirectoryTreeHandler(True,self.default_project_location,{},True)
        self.assertEquals(True,handler.interactive)

    def test_08_get_interactive_after_create_DirectoryTreeHandler_with_interactive_False_returns_False(self):
        """
        Create a DirectoryTreeHandler with interactive set to True and make sure the value is properly set.
        """
        handler = DirectoryTreeHandler(True,self.default_project_location,{},False)
        self.assertEquals(False,handler.interactive)

    def test_09_get_interactive_after_create_DirectoryTreeHandler_with_default_interactive_value_returns_Fale(self):
        """
        Make sure DirectoryTreeHandler.interactive is set to default value (False) after created.
        """
        handler = DirectoryTreeHandler(True,self.default_project_location,{})
        self.assertEquals(False,handler.interactive)

    def test_10_get_kwargs_after_create_DirectoryTreeHandler_with_None_kwargs_returns_empty_dictionary(self):
        """
        If argument kwargs is set to None then DirectoryTreeHandler.kwargs must return an emtpy dictionary
        """
        handler = DirectoryTreeHandler(True, self.default_project_location, None)
        self.assertEquals({}, handler.kwargs)

    def test_11_get_kwargs_after_create_DirectoryTreeHandler_with_dictionary_X_returns_dictionary_X(self):
        """
        If DirectoryTreeHandler is created with a non empty dictionary, then we need to make sure the
        kwargs variable is properly set
        """
        kwargs = {"key_1":"value_1", "key_2":"value_2"}
        handler = DirectoryTreeHandler(True, self.default_project_location, kwargs)
        self.assertEquals(kwargs, handler.kwargs)

    def test_12_get_warn_after_create_DirectoryTreeHandler_with_warn_False_returns_False(self):
        """
        Create a DirectoryTreeHandler with warn set to True and make sure the value is properly set.
        """
        handler = DirectoryTreeHandler(True, self.default_project_location, {}, warn = False)
        self.assertEquals(False, handler.warn)

    def test_13_get_warn_after_create_DirectoryTreeHandler_with_warn_True_returns_True(self):
        """
        Create a DirectoryTreeHandler with warn set to True and make sure the value is properly set.
        """
        handler = DirectoryTreeHandler(True, self.default_project_location, {}, warn = True)
        self.assertEquals(True, handler.warn)

    def test_14_get_warn_after_create_DirectoryTreeHandler_with_warn_default_value_returns_False(self):
        """
        Create a DirectoryTreeHandler with warn set to True and make sure the value is properly set.
        """
        handler = DirectoryTreeHandler(True, self.default_project_location, {})
        self.assertEquals(False, handler.warn)

    def test_15_get_processed_templates_after_create_DirectoryTreeHandler_with_processed_templates_default_value_returns_list_containin_tree_template_location(self):
        """
        Make sure the tree template location is included in the list of processed templates.
        """
        handler = DirectoryTreeHandler(True, self.default_project_location, {})
        self.assertTrue(self.default_project_location in handler.processed_templates)
    
    def test_16_get_processed_templates_after_create_DirectoryTreeHandler_with_list_X_returns_list_containing_all_elements_from_list_X(self):
        """
        Create a DirectoryTreeHandler with a list of already processed templates. Make sure all elements from the given list
        are present in DirectoryTreeHandler.processed_templates
        """
        p_templates = ["template_1.xml", "template_2.xml", "template_3.xml"]
        handler = DirectoryTreeHandler(True, self.default_project_location, {}, processed_templates = p_templates)

        for p_template in p_templates:
            self.assertTrue(p_template in handler.processed_templates)

    def test_17_run_with_tree_template_location_from_local_filesystem(self):
        """
        Create a DirectoryTreeHandler poiting to a valid existing tree template in the local filesystem.
        """
        handler = DirectoryTreeHandler(False, self.default_project_location, self.default_args)
        handler.run()

#    def test_18_run_with_tree_template_location_from_http_resource(self):
#        """
#        Create a DirectoryTreeHandler with a tree template location pointing to an HTTP resource.
#        """
#        http_server_thread = HttpServerThread(self.templates_dir)
#        http_server_thread.start()
#
#
#        # Wait for the server to start
#        while not http_server_thread.running:
#            pass
#
#        handler = DirectoryTreeHandler(False, "http://localhost:%s/%s" % (self.http_port, "default_test_project.xml"), self.default_args) 
#        handler.run()
#        
#        # Wait for the server to stop
#        while http_server_thread.running:
#            http_server_thread.stop()
 
    def test_19_run_with_tree_template_location_from_file_resource(self):
        """
        Create a DirectoryTreeHandler with a tree template location pointing to a file resource (url is of the form
        file:///
        """
        handler = DirectoryTreeHandler(False,"file://%s" % self.default_project_location, self.default_args)
        handler.run()


    def test_20_variables_substitution(self):
        """
        Make sure variables gets substituted
        """
        handler = DirectoryTreeHandler(False, self.default_project_location, self.default_args)  
        tree_template_str = handler._read_template(handler.tree_template)
        tree_template_str = handler._parse_template(tree_template_str, handler.tree_template)
        self.assertFalse("project_root" in tree_template_str)
        self.assertFalse("project_path" in tree_template_str)
        self.assertTrue('dirname="%s"' % self.tests_dir in tree_template_str)
        self.assertTrue('basename="%s"' % self.project_path in tree_template_str)


    def test_21_create_DirectoryTreeHandler_with_verbose_True_logs_messages(self):
        """
        Make sure messages gets logged when verbose is set to true. We expect the following lines
        (path will vary) :

        Starting Directory Tree Template Build...
        Changing current directory to: /Volumes/Data/Dashing.TV/python-dirtt/tests
        Creating dir: /Volumes/Data/Dashing.TV/python-dirtt/tests/data (perms:02755 uid:0 gid:0)
        Creating dir: /Volumes/Data/Dashing.TV/python-dirtt/tests/data/dir1 (perms:02755 uid:0 gid:0)
        Creating file: /Volumes/Data/Dashing.TV/python-dirtt/tests/data/file.txt (02775/0:0)
        Creating symlink: /Volumes/Data/Dashing.TV/python-dirtt/tests/data/images => dir1

        """
        data_dir = os.path.join(self.tests_dir,"data")
        log_file = os.path.join(self.tests_dir, "test_21.log")

        if os.path.exists(data_dir):
            shutil.rmtree(data_dir)

        if os.path.exists(log_file):
            os.unlink(log_file)

        handler = DirectoryTreeHandler(True, os.path.join(self.templates_dir,"test_logging.xml"), self.default_args)
        # Small hack to make sure log messages won't be sent out to sys.stdout 
        handler.logger.handlers = []
        handler.logger.addHandler(logging.FileHandler(log_file))
        handler.run()

        _file = open(log_file)

        try:
            lines = [line.lower().replace('\n','').replace('\r\n','') for line in _file]

            expected_lines = []
            expected_lines.append("Starting Directory Tree Template Build...")
            expected_lines.append("Changing current directory to: %s" % self.tests_dir)
            expected_lines.append("Creating dir: %s (perms:02755 uid:0 gid:0)" % data_dir)
            expected_lines.append("Creating dir: %s (perms:02775 uid:0 gid:0)" % os.path.join(data_dir,"dir1"))
            expected_lines.append("Creating file: %s (perms:02775 uid:0 gid:0)" % os.path.join(data_dir,"file.txt"))
            expected_lines.append("Creating symlink: %s => %s" % ((os.path.join(data_dir,"images"), "dir1")))
            expected_lines = [line.lower() for line in expected_lines]

            self.assertEquals(6, len(lines))

            self.assertEquals(expected_lines[0], lines[0])
            self.assertEquals(expected_lines[1], lines[1])
            self.assertEquals(expected_lines[2], lines[2])
            self.assertEquals(expected_lines[3], lines[3])
            self.assertEquals(expected_lines[4], lines[4])
            self.assertEquals(expected_lines[5], lines[5])
        finally:
            _file.close()


    

            
if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(DirectoryTreeHandlerTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
