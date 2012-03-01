"""
python-dirtt - Directory Tree Templater
(c) 2012 Dashing Collective Inc. and contributors
Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php

	io.py
	
	These are helper functions for dealing with filesystem IO.
	Creating directories, files, symlinks, and reading files, urls
	are handled here.
	
"""

import os
import sys
import urllib


def set_perms_uid_gid(target, perms, uid, gid):
	"""
	given a provided permission, uid & gid
	set the the owner, group and permissions
	for a given path (directory, file, etc.)
	"""
	os.chmod(target,perms)
	if uid and gid:
		os.chown(target,uid,gid)
	elif uid:
		os.chown(target,uid,0)
	else:
		return


def create_dir(basename, perms=None, uid=None, gid=None, warn=False):
	"""
	creates a directory unless a regular file
	is in the way. If more than one component in
	path it creates parent as necessary.
	If it already exists it completes silently.
	"""
	if os.path.isdir(basename):
		if warn:
			print >> sys.stderr, "A directory exists with that name ('%s'). \
				\nAborting directory creation." % basename
			sys.exit(-1)
	elif os.path.isfile(basename):
		if warn:
			print >> sys.stderr, "A file exists with the name of the desired dir ('%s'). \
				\nAborting directory creation." % basename
			sys.exit(-2)
	else:
		head, tail = os.path.split(basename)
		if head and not os.path.isdir(head):
			create_dir(head, perms, uid, gid)
		if tail:
			os.mkdir(basename)
			set_perms_uid_gid(basename,perms,uid,gid)
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



	
