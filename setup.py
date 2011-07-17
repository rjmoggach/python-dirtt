import os
from setuptools import setup


def return_version():
	return __import__('dirtt').get_version()

def dirtt(s):
	return "dirtt"+s

setup(
	name='python-dirtt',
	packages=[
		dirtt(''),
		dirtt('.util'),
		],
	package_dir={dirtt(''):'dirtt'},
	scripts=['scripts/mkdirt',],
	data_files=[
		('var/dirtt/templates',['templates/project.xml','templates/sequence.xml','templates/shot.xml']),
		('var/dirtt/dtds',['dtds/dirtt.dtd','dtds/dirtt-0_1_1.dtd']),
		],
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
	license='MIT',
	zip_safe=True
	)

