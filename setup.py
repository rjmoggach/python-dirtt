import os
from setuptools import setup


def read(fname):
	return open(os.path.join(os.path.dirname(__file__), fname)).read()


def here():
	return os.path.dirname(os.path.abspath(__file__))


def return_version():
	return __import__('dirtt').get_version()

kw = {}

setup(
	name='python-dirtt',
	version=return_version(),
	description="Directory Tree Templater",
	long_description=read('README.rst'),
	classifiers=[
		'Development Status :: 3 - Alpha',
		'Intended Audience :: Developers',
		'License :: OSI Approved :: MIT License',
		'Programming Language :: Python :: 2.5',
		'Programming Language :: Python :: 2.6',
		'Programming Language :: Python :: 2.7',
		'Programming Language :: Python :: 3',
		'Programming Language :: Python :: 3.1',
		'Programming Language :: Python :: 3.2',
	],
	keywords='filesystem template utilities',
	author='Robert Moggach',
	author_email='rob@dashing.tv',
	maintainer='Dashing Collective Inc.',
	maintainer_email='opensource@dashing.tv',
	url='http://opensource.dashing.tv/python-dirtt',
	license='MIT',
	packages=['dirtt','dirtt.util'],
	**kw
	)

