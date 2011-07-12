import os

from xml.etree import ElementTree
from xml.sax import make_parser
from xml.sax.handler import ContentHandler

from dirtt.util import get_uid_for_name, get_gid_for_name
from dirtt.io import create_dir, create_file, create_symlink, set_perms_uid_gid, read_file, read_url
from dirtt.util.template import Template

DEFAULT_PERMS = "02775"
DEFAULT_USER = "root"
DEFAULT_GROUP = "root"


class CreateDirectoryTreeHandler(ContentHandler):

	def __init__(self, verbose, tree_template, **kwargs):
		self.verbose = verbose
		self.tree_template = tree_template
		self.start_dir = self.dirname = os.path.abspath(".")
		if kwargs is None:
			kwargs = {}
		self.kwargs = kwargs
		
	def run(self):
		parser = make_parser()
		parser.setContentHandler(self)
		tree_template_str = self._read_template(self.tree_template)
		tree_template_str = self._parse_template(tree_template_str,self.tree_template)
		parser.parse(tree_template_str)
		os.chdir(self.start_dir)
	
	def startElement(self, name, attrs):
		warn = False
		self.current_dir = os.path.abspath(".")
		basename = attrs.get("basename", None)
		perms,uid,gid = self._return_perms_uid_gid()
		# base directory
		if name == 'dirtt':
			self.dirname = attrs.get("dirname")
			os.chdir(self.dirname)
		if basename:
			# directories
			if name in ('dirtt','dir'):	
				if self.verbose: print "creating dir: %s/%s (%s/%i:%i)" % (self.current_dir, basename, oct(perms), uid, gid)
				create_dir(basename, perms, uid, gid, warn)
				os.chdir(basename)
			# files
			if name == 'file':
				if self.verbose: print "creating file: %s/%s (%s/%i:%i)" % (self.current_dir, basename, oct(perms), uid, gid)
				href = attrs.get("href",None)
				if not href is None:
					template_str = self._read_template(href)
					content = self._parse_template(template_str, href)
				create_file(basename, content, perms, uid, gid)
			# links
			if name == 'link':
				if self.verbose: print "creating symlink: %s/%s" % (self.current_dir, basename)
				create_symlink(ref, basename)
		return
			
	def _return_perms_uid_gid(self):
		perms = int(attrs.get("perms", DEFAULT_PERMS),8)
		username = attrs.get("username", DEFAULT_USER)
		uid = get_uid_for_name(username)
		group = attrs.get("group", DEFAULT_GROUP)
		gid = get_gid_for_name(group)
		return (perms, uid, gid)

	def _read_template(self, template_ref=None):
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
		if template_str is None:
			return None
		template = Template(template_str,template_ref)
		content = template.substitute(self.kwargs)
		return content

	def characters (self, ch):
		pass
	
	def endElement(self, name):
		os.chdir("..")
