#!/usr/bin/python

"""
  python-dirtt - Directory Tree Templater
  (c) 2012 Dashing Collective Inc. and contributors
  Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php

	mkproject.py
	
	This is a generic command line tool that prompts for template
	variables in a given template and renders the tree.

"""

import os
import sys
from optparse import OptionParser

from dirtt import DirectoryTreeHandler, list_available_templates
from dirtt.util.template import return_placeholders

ENABLED_USERS = [0,1111]

TEMPLATE_DIR="/dashing/tools/var/dirtt/templates"
PROJECT_ROOT="/dashing/jobs"
PROJECT_PATHS=["master", "production", "work"]
PROJECT_TEMPLATE=os.path.join(TEMPLATE_DIR,"project.xml")
PRODUCTION_TEMPLATE=os.path.join(TEMPLATE_DIR,"project_production.xml")
WORK_TEMPLATE=os.path.join(TEMPLATE_DIR,"project_work.xml")
MASTER_TEMPLATE=os.path.join(TEMPLATE_DIR,"project_master.xml")
SEQUENCE_TEMPLATE=os.path.join(TEMPLATE_DIR,"project_sequence.xml")
SHOT_TEMPLATE=os.path.join(TEMPLATE_DIR,"project_shot.xml")


def main():
	usage = "usage: %prog [-t TEMPLATE]"
	version=__import__('dirtt').get_version()
	description="""Interactively create a directory tree from template(s)."""
	parser = OptionParser(usage=usage, version=version, description=description)
#	parser.add_option("-t", "--template", dest="template_loc", help="Full path to template file.", metavar="XML_FILE")
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
#	if options.template_loc:
#		template_loc = options.template_loc
#	else:
#		template_loc = None
#		print "\n  You must specify a template file with -t or --template  to run this script.\n  Alternatively you can list  the available templates  with -l or --list.\n  For a complete list of options -h or --help.\n"
#		sys.exit(-6)
	if options.verbose: verbose = True
	else: verbose = False
	if options.interactive: interactive = True
	else: interactive = False
	if options.warn:  warn = True
	else: warn = False
	
	template_variables = {}
	template_variables["project_root"] = PROJECT_ROOT
	print "Enter the project_path:\n\tEg. hyundai/etne"
	project_path=raw_input("\tproject_path >  ")
	project_path_full=os.path.join(PROJECT_ROOT,project_path)
	template_variables["project_path"] = project_path
	if not os.path.isdir(project_path_full):
		c = DirectoryTreeHandler(verbose,PROJECT_TEMPLATE,template_variables,interactive,warn)
		c.run()
		print "Created Project Tree."
	else:
		print "Project Exists."

	print "Enter the sequence_name:\n\tEg. veloster"
	sequence_name=raw_input("\tsequence_name >  ")
	sequence_path=os.path.join(project_path_full,"sequences",sequence_name)
	template_variables["sequence_name"] = sequence_name
	if not os.path.isdir(sequence_path):
		c = DirectoryTreeHandler(verbose,SEQUENCE_TEMPLATE,template_variables,interactive,warn)
		c.run()
		print "Created Sequence Tree."
	else:
		print "Sequence Exists."
	
	print "Enter a shot_name or comma-separated list(NO SPACES):\n\tEg. vst010"
	shot_name_raw=raw_input("\tshot_name >  ")
	shot_list=shot_name_raw.split(",")
	for shot_name in shot_list:
		template_variables["shot_name"] = shot_name
		shot_path=os.path.join(sequence_path,shot_name)
		if not os.path.isdir(shot_path):
			c = DirectoryTreeHandler(verbose,SHOT_TEMPLATE,template_variables,interactive,warn)
			c.run()
			print "Created Shot Tree."
		else:
			print "Shot Exists."
		maya_scenes_path=os.path.join(project_path,"sequences",sequence_name,shot_name,"work/maya/scenes")
		if not os.path.isdir(maya_scenes_path):
			c = DirectoryTreeHandler(verbose,MAYA_TEMPLATE,template_variables,interactive,warn)
			c.run()
			print "Created Shot Maya Work Dir."

	print "Created Tree."
	sys.exit(0)


if __name__ == "__main__":
	main()

