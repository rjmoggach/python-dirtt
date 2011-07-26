"""
python-dirtt - Directory Tree Templater
(c) 2011 Dashing Collective Inc. and contributors
Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php

dirtt is a standalone tool and library used to generate 
directory and file structures from xml templates that describe 
repeatedly used filesystem layouts such as project structures
or elements therein.

This module builds a project template from an existing source tree.
"""

import os,pwd,grp
from xml.dom.minidom import Document
from stat import *

class ProjectBuilder:

	def __init__(self, base="."):
		self.base = base
		self.doc =  Document()

	def build_template(self):
		"""
		List base dir and walk down child folders building a project template
		"""

		top_element = self._get_dirtt_element() 
		self._update_element(top_element,self.base)
		top_element.setAttribute("dirname",self._get_parent_directory(os.path.abspath(self.base)))

		self.doc.appendChild(top_element)

		base_dirs = os.listdir(self.base)

		roots = {}
		roots[os.path.abspath(self.base)] = top_element
	
		for base_dir in base_dirs:
			abs_base = os.path.abspath(os.path.join(self.base,base_dir))
		
			current_element = self._get_dir_element() 
			self._update_element(current_element,abs_base)

			top_element.appendChild(current_element)
			
			roots[abs_base] = current_element 
		
			if os.path.isdir(abs_base):
				for root,dirs,files in os.walk(abs_base):
					if not roots[root]:
						self._add_child_dir(root, roots)
					for _dir in dirs:
						self._add_child_dir(os.path.join(root,_dir), roots)

		print self.doc.toprettyxml(indent="	")

	def _add_child_dir(self, dir, roots):
		parent_directory = self._get_parent_directory(dir)
		# We walk the tree top-down so the parent directory must has
		# been processed.

		parent_element = roots[parent_directory] 
		_element = self._get_dir_element()
		self._update_element(_element, dir)
		roots[dir] = _element

		parent_element.appendChild(_element)
	
	def _get_parent_directory(self,path):
		return os.path.abspath(os.path.join(path, '..'))

	def _get_dirtt_element(self):
		return self.doc.createElement("dirtt")

	def _get_dir_element(self):
		return self.doc.createElement("dir")
	
	
	def _update_element(self, element, dir):
		abs_path = os.path.abspath(dir)
		name = os.path.basename(abs_path)
		stat_info = os.stat(abs_path)
		perms = oct(S_IMODE(stat_info.st_mode))
		owner = pwd.getpwuid(stat_info.st_uid).pw_name
		group = grp.getgrgid(stat_info.st_gid).gr_name

		element.setAttribute("name",name)
		element.setAttribute("basename",name)
		element.setAttribute("username",owner)
		element.setAttribute("group",group)
		element.setAttribute("perms",perms)
