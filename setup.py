import os
from distutils.core import setup

# is_package and find_package code borrowed from:
#  http://wiki.python.org/moin/Distutils/Cookbook/AutoPackageDiscovery
def is_package(path):
	return (
		os.path.isdir(path) and
		os.path.isfile(os.path.join(path, '__init__.py'))
		)

def find_packages(path, base="" ):
	""" Find all packages in path """
	packages = {}
	for item in os.listdir(path):
		dir = os.path.join(path, item)
		if is_package(dir):
    			if base:
				module_name = "%(base)s.%(item)s" % vars()
    			else:
				module_name = item
    			packages[module_name] = dir
			packages.update(find_packages(dir, module_name))
	return packages

# Builds a list of data files to be installed aside from 
# in-package data.
def find_data_files(base):
	data_files = []
	for item in os.listdir(base):
		_files = []
		if os.path.isdir(os.path.join(base,item)):
			for root, dirs, files in os.walk(os.path.join(base,item)):
				_files.extend([os.path.join(base,item,f) for f in files])	
		if len(_files) > 0:
			data_files.append((item,_files))
	return data_files	
	

def return_version():
	return __import__('dirtt').get_version()

def dirtt(s):
	return "dirtt"+s

setup(
	name='python-dirtt',
	packages=find_packages('.'),
	package_dir={dirtt(''):'dirtt'},
	package_data={dirtt('') : ['data/templates/*.xml','data/dtds/*.dtd']},
	scripts=['scripts/mkdirt',],
	data_files = find_data_files(os.path.join('dirtt','data')),
	version=return_version(),
	description="Directory Tree Templater",
	long_description="""
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
		
		https://github.com/dshng/python-dirtt/
	
		http://opensource.dashing.tv/python-dirtt/
		""",
	classifiers=[
		'Development Status :: 3 - Alpha',
		'Intended Audience :: Developers',
		'Intended Audience :: System Administrators',
		'License :: OSI Approved :: MIT License',
		'Programming Language :: Python',
		'Natural Language :: English',
		'Operating System :: POSIX :: Linux',
		'Operating System :: MacOS :: MacOS X',
		'Topic :: System :: Systems Administration',
		'Topic :: Text Processing :: Markup :: XML'
	],
	keywords='filesystem template utilities',
	author='Robert Moggach',
	author_email='rob@dashing.tv',
	maintainer='Dashing Collective Inc.',
	maintainer_email='rob@dashing.tv',
	url='https://github.com/dshng/python-dirtt/',
	license='MIT'
	)

