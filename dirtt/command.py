"""
dirtt - Directory Tree Templater
(c) 2011 Dashing Collective Inc. and contributors
Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php

	command.py
	
	This is a generic command line tool that prompts for template
	variables in a given template and renders the tree.

"""

import os
import sys
from optparse import OptionParser

from dirtt.create import CreateDirectoryTreeHandler
from dirtt.util.template import return_placeholders


def main():
	usage = "usage: %prog [-t TEMPLATE]"
	version=__import__('dirtt').get_version()
	description="""Interactively create a directory tree from template(s)."""
	parser = OptionParser(usage=usage, version=version, description=description)
	parser.add_option("-t", "--template", dest="template_loc", help="Full path to template file.", metavar="XML_FILE")
	parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=False)
	(options, args) = parser.parse_args()
	if options.template_loc:
		template_loc = options.template_loc
	else:
		template_loc = None
		print "You must specify a template file with -t or --template to run this script."
		sys.exit(-6)
	if options.verbose:
		verbose = True
	else:
		verbose = False
	if os.geteuid() != 0:
		print "You must be root to run this script."
		sys.exit(-6)
	template_file = open(template_loc,'r')
	template_str = template_file.read()
	template_file.close()
	placeholders = return_placeholders(template_str)
	if not placeholders is None:
		print "The template is looking for the following attributes:"
		for key in placeholders:
			print "\t%s" % key
		print "\nPlease enter appropriate values below."
		kwargs = {}
		for key in placeholders:
			prompt = "\t%s >  " % key
			exec_str = "%s = raw_input('%s')" % (key,prompt)
			exec(exec_str)
			kwargs[key]=eval(key)

	if verbose:
		print "Starting Directory Tree Template Build:"
	c = CreateDirectoryTreeHandler(verbose,template_loc,kwargs)
	c.run()
	print "Created Tree."
	sys.exit(0)

