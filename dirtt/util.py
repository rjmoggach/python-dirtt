# -*- coding: utf-8 -*-
import os
import errno
import re
import pwd
import grp
import sys
import urllib
import dirtt.posix

def list_available_templates():
    print "\n    These are the available templates. Reference using the full path provided."
    template_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data', 'templates')
    print "Template Path: %s" % template_dir
    template_list = []
    for filename in os.listdir(template_dir):
        print "    %s" % os.path.join(template_dir,filename)


def print_array(array,tab=0):
    """
    function to iterate through an array
    """
    # are there any keys?
    indexes = array.keys()
    indexes.sort()
    for i in indexes:
        # check if the value is another array?
        if type(array[i]) is dict:
            # value is an array
            print "%s * %s =>" % ('\t'*tab,i)
            # print the key, and spawn print_array again to print the next level of the array
            print_array(array[i],tab=tab+1)
        else:
            # value is not an array - print the key and the value
            print "%s + %s => %s" % ('\t'*tab,i,array[i])


def create_dir(basename, perms, uid, gid, warn=False):
    """
    creates a directory unless a regular file
    is in the way. If more than one component in
    path it creates parent as necessary.
    If it already exists it completes silently.
    """
    assert basename is not None
    assert perms is not None and isinstance(perms,int)
    assert uid is not None and isinstance(uid,int)
    assert gid is not None and isinstance(gid,int)
    if os.path.isdir(basename):
        if warn:
            error = OSError()
            error.errno = errno.EISDIR
            raise error
    elif os.path.isfile(basename):
        if warn:
            error = OSError()
            error.errno = errno.EEXIST
            raise error
    else:
        head, tail = os.path.split(basename)
        if head and not os.path.isdir(head):
            create_dir(head, perms, uid, gid)
        if tail:
            os.mkdir(basename)
            dirtt.posix.set_perms(basename,perms,uid,gid)
    return basename


def create_file(basename, content=None, perms=None, uid=None, gid=None):
    """
    create file of name 'basename'
    optionally with content 'content' & with
    permissions ('perms'), ownership ('uid') &
    group ('gid').
    *Important*
    uid & gid must be integers
    content should be ready to go (no parsing done here)
    """
    if os.path.exists(basename):
        print >> sys.stderr, "A file or directory exists with the same name ('%s'). \
            \nAborting file creation." % basename
        sys.exit(-2)
    if content is None:
        open(basename,"w").close()
    else:
        file = open(basename,"w")
        file.writelines(content)
        file.close()


def create_symlink(ref, target):
    """
    creates symlink from ref to target
    """
    if not os.path.exists(target):
        os.symlink(ref,target)
    else:
        print >> sys.stderr, "A file or directory exists with the same name ('%s'). \
            \nAborting link creation." % target
        sys.exit(-2)


def read_file(path):
    """
    read a file and return the content
    *currently only suitable for text*
    *need to add filetype checking of some sort*
    """
    if os.path.isfile(path):
        file = open(path,"r")
        content = file.read()
        file.close()
        return content
    else:
        raise OSError, "File '%s' does not exist or is not a file" %  path


def read_url(href):
    """
    read a url and return the content
    *currently only suitable for text*
    *need to add filetype checking of some sort*
    """
    opener = urllib.FancyURLopener({})
    href = opener.open(href)
    content = href.read()
    return content




