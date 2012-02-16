#!/usr/bin/env python

"""
  python-dirtt - Directory Tree Templater
  (c) 2012 Dashing Collective Inc. and contributors
  Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php

	mktemplate.py	
	
	This is a generic command line tool to create a tree template from an
	existing source path

"""

import os
import sys
from optparse import OptionParser
from dirtt.util.introspection import *


def main():
	usage = "usage: %prog [-p SOURCE_PATH]"
	version=__import__('dirtt').get_version()
	description="""Return an XML directory template from an existing directory tree."""
	parser = OptionParser(usage=usage, version=version, description=description)
	parser.add_option("-p", "--path", dest="source_path", help="Absolute path to source tree.")
	(options, args) = parser.parse_args()
	if options.project_path:
		project_path = options.project_path
	else:
		project_path = None
		print "\n  You must specify a source path to introspect\n  with -p or --path to run this script."
		sys.exit(-6)
        introspected_tree = TreeIntrospector(project_path)
        introspected_tree.build_template()
	sys.exit(0)


if __name__ == "__main__":
	main()



