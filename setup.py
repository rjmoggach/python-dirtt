import os
from setuptools import setup


def read(fname):
	return open(os.path.join(os.path.dirname(__file__), fname)).read()


def here():
	return os.path.dirname(os.path.abspath(__file__))


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
	long_description=read('README.rst'),
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
	url='http://opensource.dashing.tv/python-dirtt',
	license='MIT',
	zip_safe=True
	)

