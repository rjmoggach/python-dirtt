#!/usr/bin/python

"""
  python-dirtt - Directory Tree Templater
  (c) 2015 Robert Moggach and contributors
  Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php

    mktree.py

    This is a generic command line tool that prompts for template
    variables in a given template and renders the tree.

"""

import os
import sys
from optparse import OptionParser
from dirtt import DirectoryTreeHandler, list_available_templates
from dirtt.util.template import return_placeholders

ENABLED_USERS = [0,1111,1003]


def main():
    usage = "usage: %prog [-t TEMPLATE]"
    version=__import__('dirtt').get_version()
    description="""Interactively create a directory tree from template(s)."""
    parser = OptionParser(usage=usage, version=version, description=description)
    parser.add_option("-t", "--template", dest="template_loc", help="Full path to template file.", metavar="XML_FILE")
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=False)
    parser.add_option("-i", "--interactive", dest="interactive", action="store_true", default=False)
    parser.add_option("-w", "--stop-on-warning",dest="warn",action="store_true",default=False)
    parser.add_option("-l", "--list",dest="list",action="store_true",default=False)
    (options, args) = parser.parse_args()

    if os.geteuid() not in ENABLED_USERS:
        print "You are not authorized to run this script."
        sys.exit(-6)

    if options.list:
      list_available_templates()
      sys.exit(-6)

    if options.template_loc:
        template_loc = options.template_loc
    else:
        template_loc = None
        print "\n  You must specify a template file with -t or --template  to run this script.\n  Alternatively you can list  the available templates  with -l or --list.\n  For a complete list of options -h or --help.\n"
        sys.exit(-6)

    if options.verbose: verbose = True
    else: verbose = False

    if options.interactive: interactive = True
    else: interactive = False

    if options.warn:  warn = True
    else: warn = False

    template_file = open(template_loc,'r')
    template_str = template_file.read()
    template_file.close()
    placeholders = return_placeholders(template_str)
    if not placeholders == []:
        print "The template is looking for the following attributes:"
        for key in placeholders:
            print "\t%s" % key
        print "\nPlease enter appropriate values below."
        template_variables = {}
        for key in placeholders:
            prompt = "\t%s >  " % key
            exec_str = "%s = raw_input('%s')" % (key,prompt)
            exec(exec_str)
            template_variables[key]=eval(key)
    else: template_variables = {}

    c = DirectoryTreeHandler(verbose,template_loc,template_variables,interactive,warn)
    c.run()
    print "Created Tree."
    sys.exit(0)


if __name__ == "__main__":
    main()

