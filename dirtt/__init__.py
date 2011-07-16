"""
python-dirtt - Directory Tree Templater
(c) 2011 Dashing Collective Inc. and contributors
Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php

dirtt is a standalone tool and library used to generate 
directory and file structures from xml templates that describe 
repeatedly used filesystem layouts such as project structures
or elements therein.

It provides a subclassed implementation of xml.sax.handler ContentHandler
with internal methods that read,parse,render,and execute builds of
user defined XML directory tree templates.
"""

#v0.1.3
VERSION = (0, 1, 3, 'final', 0)

STATUSES = {'alpha': 'a', 'beta': 'b', 'releasecandidiate': 'rc' }


def get_version():
    version = '%s.%s' % (VERSION[0], VERSION[1])
    if VERSION[2]:
        version = '%s.%s' % (version, VERSION[2])
    if VERSION[3:] == ('alpha', 0):
        version = '%s pre-alpha' % version
    else:
        if VERSION[3] != 'final':
            version = '%s%s%s' % (version, STATUSES[VERSION[3]], VERSION[4])
    return version

__version__ = get_version()
__all__ = ['util']


import os

from xml.etree import ElementTree
#from xml.sax import make_parser
from xml.sax import parseString
from xml.sax.handler import ContentHandler

from dirtt.util import get_uid_for_name, get_gid_for_name
from dirtt.util.io import create_dir, create_file, create_symlink, set_perms_uid_gid, read_file, read_url
from dirtt.util.template import Template

DEFAULT_PERMS = "02775"
DEFAULT_USER = "root"
DEFAULT_GROUP = "root"


class CreateDirectoryTreeHandler(ContentHandler):
	"""
	Main SAX Interface for handling directory tree XML templates

	This is the main callback interface subclassed from xml.sax.handler
	ContentHandler. It provides custom methods for reading,parsing,rendering
	and executing the xml elements and their attributes.
	"""

	def __init__(self, verbose, tree_template, kwargs, interactive=False):
		"""
		define from the class initialization the verbosity level,
		the template to use, the user's starting directory, and any
		keyword arguments defined in the initialization. All are
		defined as part of the self context to allow for local
		reference in the builtin functions
		"""
		self.verbose = verbose
		self.tree_template = tree_template
		self.start_dir = self.dirname = os.path.abspath(".")
		if kwargs is None:
			kwargs = {}
		self.interactive = interactive
		self.kwargs = kwargs
		self.skip_entity = 0
		
	def run(self):
		"""
		top level application logic. From here we read, parse and perform any
		operations before returning to the start dir
		"""
		# parser is only necessary if we're reading an xml file directly
		# but we want to replace template variables first
		# parser = make_parser()
		# parser.setContentHandler(self)
		# parser.parse(self.tree_template)
		tree_template_str = self._read_template(self.tree_template)
		tree_template_str = self._parse_template(tree_template_str,self.tree_template)
		parseString(tree_template_str,self)
		if self.verbose: print "Returning to start dir: %s" % self.start_dir
		os.chdir(self.start_dir)
		self.current_dir = os.path.abspath(".")
	
	def startElement(self, name, attrs):
		"""
		When an XML element is first read, this function is run
		to process it's attributes and content before moving on
		to it's contents and then endElement
		"""
		warn = False
		self.current_dir = os.path.abspath(".")
		basename = attrs.get("basename", None)
		perms,uid,gid = self._return_perms_uid_gid(attrs)
		if name == 'dirtt':
			if self.verbose: print "Starting Directory Tree Template Build..."
			self.dirname = attrs.get("dirname")
			if self.verbose: print "\tChanging current directory to: %s" % self.dirname
			os.chdir(self.dirname)
			self.current_dir = os.path.abspath(".")
		if basename:
			if self.skip_entity: self.skip_entity += 1
			if name in ('dirtt','dir'):
				if self.interactive:
					if not self.skip_entity:
						if not raw_input("Create Directory %s (yes/no)?" % os.path.join(self.current_dir,basename)) in ("yes","Yes","YES","Y","y"):
							self.skip_entity += 1
							if self.verbose: print "\tSkipping dir: %s" % os.path.join(self.current_dir,basename)
						else:
							if self.verbose: print "\tCreating dir: %s/%s (perms:%s uid:%i gid:%i)" % (self.current_dir, basename, oct(perms), uid, gid)
							create_dir(basename, perms, uid, gid, warn)
							os.chdir(basename)
							self.current_dir = os.path.abspath(".")
				else:
					if self.verbose: print "\tCreating dir: %s/%s (perms:%s uid:%i gid:%i)" % (self.current_dir, basename, oct(perms), uid, gid)
					create_dir(basename, perms, uid, gid, warn)
					os.chdir(basename)
					self.current_dir = os.path.abspath(".")
			if name == 'file':
				if self.verbose: print "\tCreating file: %s/%s (%s/%i:%i)" % (self.current_dir, basename, oct(perms), uid, gid)
				href = attrs.get("href",None)
				if not href is None:
					template_str = self._read_template(href)
					content = self._parse_template(template_str, href)
				create_file(basename, content, perms, uid, gid)
			if name == 'link':
				if self.verbose: print "\tCreating symlink: %s/%s" % (self.current_dir, basename)
				create_symlink(ref, basename)
		return
			
	def _return_perms_uid_gid(self,attrs):
		"""
		internal function to return the OS uid and gid numbers
		from a provided username or group. This allows for more
		generic name based ids and is useful for developing on
		different OS's
		"""
		perms = int(attrs.get("perms", DEFAULT_PERMS),8)
		username = attrs.get("username", DEFAULT_USER)
		uid = get_uid_for_name(username)
		group = attrs.get("group", DEFAULT_GROUP)
		gid = get_gid_for_name(group)
		return (perms, uid, gid)

	def _read_template(self, template_ref=None):
		"""
		internal function that checks if an element
		has provided a reference to a template or use
		the main template. It also checks for a urllib
		style reference or reads the file directly. It
		returns the unprocessed content of the template.
		"""
		if template_ref is None:
			template_ref = self.template
		try:
			if template_ref[0:7] in ('http://','file://'):
				content = read_url(template_ref)
			else:
				content = read_file(template_ref)
		except:
			content = None
		return content

	def _parse_template(self, template_str=None, template_ref=None):
		"""
		use our built-in Template class and substitute the
		provided placeholder attributes where possible
		and return the rendered template
		"""
		if template_str is None:
			return None
		template = Template(template_str,template_ref)
		content = template.substitute(self.kwargs)
		return content

	def characters (self, ch):
		"""
		required method from the original SAX class
		"""
		pass
	
	def endElement(self, name):
		"""
		if our element is a directory, close it when
		we're done processing it's contents, otherwise
		pass silently
		"""
		if not self.skip_entity:
			if name in ('dir','dirtt'):
					os.chdir("..")
					self.current_dir = os.path.abspath(".")
		if self.skip_entity: self.skip_entity -= 1
		pass


