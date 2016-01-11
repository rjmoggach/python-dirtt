# -*- coding: utf-8 -*-
"""This module builds a project template from an existing source tree.
"""
import os
import pwd
import grp
import stat
from xml.dom.minidom import Document


__all__ = [ 'TreeIntrospector' ]


class TreeIntrospector:

    def __init__(self, base="."):
        self.base = os.path.realpath(base)
        self.doc =  Document()
        self.idrefs = {}
        self.idref_count = 1

    def build_template(self):
        """List base dir and walk down child folders building a project template"""

        top_element = self._get_dirtt_element()
        self._update_element(top_element,self.base)
        top_element.setAttribute("dirname",self._get_parent_directory(os.path.realpath(self.base)))

        self.doc.appendChild(top_element)

        base_dirs = os.listdir(self.base)

        roots = {}

        roots[os.path.realpath(self.base)] = top_element

        for base_dir in base_dirs:
            abs_base = os.path.join(self.base,base_dir)

            if os.path.islink(abs_base):
                self.idrefs[abs_base] = os.path.realpath(abs_base)
                continue

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

        self._process_symlinks(roots)

        print self.doc.toprettyxml(indent="    ")

    def _process_symlinks(self, roots):
        for symlink,target in self.idrefs.iteritems():
            parent_directory = os.path.abspath(os.path.join(symlink,'..'))
            if roots.has_key(target):
                root_element = roots[target]

                if not root_element.getAttribute("id"):
                    root_element.setAttribute("id", self._get_new_idref())

                idref = root_element.getAttribute("id")

                parent_element = roots[parent_directory]

                _element = self._get_link_element()

                self._update_element(_element, symlink)
                _element.setAttribute("ref", target)
                _element.setAttribute("basename", parent_directory)
                _element.setAttribute("dirname", os.path.basename(symlink))

                parent_element.appendChild(_element)

    def _get_new_idref(self):
        idref = "%s_%d" % ("ref",self.idref_count)
        self.idref_count = self.idref_count + 1
        return idref

    def _add_child_dir(self, dir, roots):
        # We can't generate id/idref attributes until the entire
        # tree has been processed.
        if os.path.islink(dir):
            self.idrefs[dir] = os.path.realpath(dir)
            return

        parent_directory = self._get_parent_directory(dir)
        # We walk the tree top-down so the parent directory must has
        # been processed.

        parent_element = roots[parent_directory]

        _element = self._get_dir_element()
        self._update_element(_element, dir)

        roots[dir] = _element

        parent_element.appendChild(_element)

        return _element

    def _get_parent_directory(self,path):
        return os.path.realpath(os.path.join(path, '..'))

    def _get_dirtt_element(self):
        return self.doc.createElement("dirtt")

    def _get_link_element(self):
        return self.doc.createElement("link")

    def _get_dir_element(self):
        return self.doc.createElement("dir")

    def _update_element(self, element, dir):
        abs_path = os.path.abspath(dir)
        name = os.path.basename(abs_path)
        stat_info = os.stat(abs_path)
        perms = oct(stat.S_IMODE(stat_info.st_mode))
        owner = pwd.getpwuid(stat_info.st_uid).pw_name
        group = grp.getgrgid(stat_info.st_gid).gr_name

        element.setAttribute("name",name)
        element.setAttribute("basename",name)
        element.setAttribute("username",owner)
        element.setAttribute("group",group)
        element.setAttribute("perms",perms)
