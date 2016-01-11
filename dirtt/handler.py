# -*- coding: utf-8 -*-
import os,sys
import logging
import errno
from xml.etree import ElementTree
from xml.sax import parseString
from xml.sax.handler import ContentHandler
import dirtt


__all__ = [ 'DirectoryTreeHandler' ]


class DirectoryTreeHandler(ContentHandler):
    """Main SAX Interface for handling directory tree XML templates

    This is the main callback interface subclassed from ``xml.sax.handler``
    ``ContentHandler``. It provides custom methods for reading, parsing, rendering
    and executing the xml elements and their attributes.

    Args:
        verbose (bool): verbosity
        tree_template (str): path to template to use (can be a file or url)
        kwargs (dict): dictionary of keyword arguments
        interactive (bool): whether to create the tree interactively or not
        warn (bool): warn on errors
    """

    def __init__(self, verbose, tree_template, kwargs, interactive = False, warn = False, processed_templates=[]):
        """
        define from the class initialization the verbosity level,
        the template to use, the user's starting directory, and any
        keyword arguments defined in the initialization. All are
        defined as part of the self context to allow for local
        reference in the builtin functions
        """
        assert tree_template is not None
        self.verbose = verbose
        self.tree_template = tree_template
        # Location of tree_template
        self.tree_template_loc = os.path.dirname(self.tree_template)
        if kwargs is None:
            kwargs = {}
        self.interactive = interactive
        self.kwargs = kwargs
        self.skip_entity = 0
        self.warn = warn
        self.idrefs = {}
        self.links = []
        #List of templates been processed
        if not self.tree_template in processed_templates:
                self.processed_templates = processed_templates[:]
                self.processed_templates.append(self.tree_template)
        else:
                raise Exception("Template %s already in process" % self.tree_template)
        self.path_stack = []

    def _set_verbosity(self, value):
        if value is True:
            dirtt.LOG.setLevel(logging.DEBUG)
            self.verbose = True
        else:
            self.verbose = False

    def _get_verbosity(self):
        if self.verbose is True:
            dirtt.LOG.setLevel(logging.DEBUG)
        return self.verbose
    verbose = property(_get_verbosity,_set_verbosity)

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

        # read and parse the template
        tree_template_str = self._read_template(self.tree_template)
        tree_template_str = self._parse_template(tree_template_str, self.tree_template)


        # now we can parse the string as XML
        parseString(tree_template_str, self)
        self.current_dir = os.path.abspath(".")

        self._create_symlinks()

    def _create_symlinks(self):
        for link_info in self.links:
            parent_dir = link_info['parent_dir']
            link_name = link_info['basename']
            ref = link_info['ref']
            link = os.path.join(parent_dir, link_name)

            dirtt.LOG.debug("Creating symlink: %s => %s" % (link, ref))
            dirtt.util.create_symlink(ref, link)


    def startElement(self, name, attrs):
        """
        When an XML element is first read, this function is run
        to process it's attributes and content before moving on
        to it's contents and then endElement
        """

        # set the current directory
        self.current_dir = os.path.abspath(".")

        # get the basename attribute or None
        basename = attrs.get("basename", None)

        # get the permissions and ownership
        perms, uid, gid = self._return_perms_uid_gid(attrs)
        uid, gid = dirtt.posix.get_user(uid).pw_uid, dirtt.posix.get_group(gid).gr_gid

        # get the directory name attribute or None
        self.dirname = attrs.get("dirname", None)

        # if xml elementname is dirtt let's get started
        if name == 'dirtt':
            dirtt.LOG.debug("Starting Directory Tree Template Build...")
            dirtt.LOG.debug("Changing current directory to: %s" % self.dirname)
            # change to our starting directory
            if not basename:
                self.dirname, basename = os.path.split(self.dirname)
            os.chdir(self.dirname)
            self.current_dir = os.path.abspath(".")
            self.idrefs[attrs.get("id", "root-dir")] = self.current_dir

        if basename:
            if self.skip_entity: self.skip_entity += 1

            # if the entity is our main dirtt entity or a directory proceed here
            if name in ('dirtt','dir'):
                dirname = attrs.get("dirname", None)
                if self.interactive:
                    if not self.skip_entity:
                        if not raw_input("Create Directory %s (yes/no)?" % os.path.join(self.current_dir,basename)) in ("yes","Yes","YES","Y","y"):
                            self.skip_entity += 1
                            dirtt.LOG.debug("Skipping dir: %s" % os.path.join(self.current_dir,basename))
                        else:
                            dirtt.LOG.debug("Creating dir: %s/%s (perms:%s uid:%i gid:%i)" % (self.current_dir, basename, oct(perms), uid, gid))
                            if dirname:
                                if name == 'dirtt':
                                        # When dealding with a 'dirtt' tag use self.dirname as the current dirname
                                        # as at this point self.dirname has been properly set (i.e if no basename was
                                        # provided then the value for the basename it's inferred from dirname)
                                        dirname = self.dirname
                                newdir = os.path.join(dirname,basename)
                            else:
                                newdir = basename

                        try:
                                dirtt.util.create_dir(newdir, perms, uid, gid, self.warn)
                        except OSError as oserror:
                                if oserror.errno == errno.EISDIR:
                                        print >> sys.stderr, "A directory exists with that name ('%s'). \
                                         \nAborting directory creation." % basename
                                        sys.exit(-1)
                                elif oserror.errno == errno.EISDIR:
                                        print >> sys.stderr, "A file exists with the name of the desired dir ('%s'). \
                                         \nAborting directory creation." % basename
                                        sys.exit(-2)

                        self._push_dir()
                        os.chdir(basename)
                        self.current_dir = os.path.abspath(".")

                else:
                    if dirname:
                        if name == 'dirtt':
                                # When dealding with a 'dirtt' tag use self.dirname as the current dirname
                                # as at this point self.dirname has been properly set (i.e if no basename was
                                # provided then the value for the basename it's inferred from dirname)
                                dirname = self.dirname
                        newdir = os.path.join(dirname,basename)
                    else:
                        newdir = basename

                    try:
                        dirtt.util.create_dir(newdir, perms, uid, gid, self.warn)
                        dirtt.LOG.debug("Creating dir: %s/%s (perms:%s uid:%i gid:%i)" % (self.current_dir, basename, oct(perms), uid, gid))
                    except OSError as oserror:
                        if oserror.errno == errno.EISDIR:
                                print >> sys.stderr, "A directory exists with that name ('%s'). \
                                        \nAborting directory creation." % basename
                                sys.exit(-1)
                        elif oserror.errno == errno.EISDIR:
                                print >> sys.stderr, "A file exists with the name of the desired dir ('%s'). \
                                        \nAborting directory creation." % basename
                                sys.exit(-2)

                    self._push_dir()
                    os.chdir(newdir)
                    self.current_dir = os.path.abspath(".")

                if attrs.get("id"):
                    self.idrefs[attrs.get("id")] = self.current_dir

            if name == 'file':
                dirtt.LOG.debug("Creating file: %s/%s (perms:%s uid:%i gid:%i)" % (self.current_dir, basename, oct(perms), uid, gid))
                href = attrs.get("href",None)
                content = ""
                if not href is None:
                    template_file = os.path.join(dirtt.const('DIRTT_TEMPLATES_DIR'),href)
                    template_str = self._read_template(template_file)
                    content = self._parse_template(template_str, template_file)
                dirtt.util.create_file(basename, content, perms, uid, gid)

        else:
            if name in ('dirtt', 'dir'):
                if not self.skip_entity:
                    self.skip_entity += 1

        if name == 'link':
            try:
                if (not attrs.get("idref", attrs.get("ref", None))) or (not attrs.get("basename", None)):
                     return
                ref = attrs.get("idref", attrs.get("ref"))
                link_name = attrs.get("basename")
                if ref == attrs.get("idref", None):
                    ref = self.idrefs[ref]
                target_dir = attrs.get("dirname",self.current_dir)
                self.links.append({'basename': link_name, 'parent_dir': target_dir, 'ref': ref})
            except:
                pass

        if name == 'xi:include':
            href = attrs.get("href")
            # Check for an HTTP url or an absolute file location
            if href[0:7] in ('http://'):
                template_loc = href
            elif href[0:8] in ('file:///'):
                template_loc = href
            else:
                template_loc = os.path.join(self.tree_template_loc,href)
            c = DirectoryTreeHandler(self.verbose, template_loc, self.kwargs, self.interactive, self.warn, self.processed_templates)
            c.run()
        return

    def _return_perms_uid_gid(self,attrs):
        """
        internal function to return the OS uid and gid numbers
        from a provided username or group. This allows for more
        generic name based ids and is useful for developing on
        different OS's
        """
        perms = int(attrs.get("perms", dirtt.const('DIRTT_DEFAULT_PERMS')),8)
        username = attrs.get("username", dirtt.const('DIRTT_DEFAULT_USER'))
        uid = dirtt.posix.get_user(username)
        group = attrs.get("group", dirtt.const('DIRTT_DEFAULT_GROUP'))
        gid = dirtt.posix.get_group(group).gr_gid
        return (perms, uid, gid)

    def _read_template(self, template_ref = None):
        """
        internal function that checks if an element
        has provided a reference to a template or use
        the main template. It also checks for a urllib
        style reference or reads the file directly. It
        returns the unprocessed content of the template.
        """
        if template_ref is None:
            template_ref = self.template
        if template_ref[0:7] in ('http://','file://'):
                content = dirtt.util.read_url(template_ref)
        else:
                content = dirtt.util.read_file(template_ref)
        return content

    def _parse_template(self, template_str = None, template_ref = None):
        """
        use our built-in Template class and substitute the
        provided placeholder attributes where possible
        and return the rendered template
        """
        if template_str is None:
            return None
        template = dirtt.Template(template_str,template_ref)
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
                self._pop_dir()
                self.current_dir = os.path.abspath(".")
        if self.skip_entity: self.skip_entity -= 1
        pass

    def _push_dir(self):
        dir = os.path.abspath(".")
        self.path_stack.append(dir)

    def _pop_dir(self):
        dir = self.path_stack.pop()
        os.chdir(dir)
