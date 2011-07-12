import os
import sys
from optparse import OptionParser

from dirtt.create import CreateDirectoryTreeHandler
from dirtt.util.template import return_placeholders


version = __import__('dirtt').get_version()


def setopts():
	usage = "usage: %prog [-t TEMPLATE]"
	version=version
	description="""Interactively create a directory tree from template(s)."""
	parser = OptionParser(usage=usage, version=version, description=description)
	parser.add_option("-t", "--template", dest="template", help="Full path to template file.", metavar="XML_FILE")
	parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=False)
	(options, args) = parser.parse_args()
	if options.template: template = options.template
	if options.verbose: verbose = True

	
if __name__ == '__main__':
	setopts()
	import os
	if os.geteuid() != 0:
		print "You must be root to run this script."
		sys.exit(-6)
	placeholders = return_placeholders(template)
	if not placeholders is None:
		print "The template is looking for the following attributes:\n"
		for key in placeholders:
			print "\t%s\n" % key
		print "\nPlease enter appropriate values below.\n"
		kwargs = {}
		for key in placeholders:
			prompt = "\t%s >  " % key
			exec_str = "%s = raw_input(%s)" % (key,prompt)
			exec(exec_str)
			kwargs[key]=eval(key)

	if verbose:
		print "Starting Directory Tree Template Build:"
	c = CreateDirectoryTreeHandler(verbose,template,kwargs)
	c.run()
	print "Created Tree."
	sys.exit(0)


