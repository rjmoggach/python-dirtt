# -*- coding: utf-8 -*-
"""dirtt/setup.py
=======================================

provides dirtt installation routines via setuptools
"""
import os
import sys
from setuptools import setup, find_packages

# make sure we're in the setup.py dir
ROOT_DIR = os.path.dirname(__file__)
if ROOT_DIR != '': os.chdir(ROOT_DIR)

# get version string from package
sys.path.insert(0, os.path.abspath('.'))
from dirtt import __version__

VERSION = __version__
MODULE_DIR = 'dirtt'
README=os.path.join(ROOT_DIR,'README.md')
DESCRIPTION = "Python Directory Tree Templater v{version}".format(version=VERSION)
LONG_DESCRIPTION = """\
Python Directory Tree Templater v{version}
===========================================

``python-dirtt`` is a standalone tool and library used to generate
directory and file structures from xml templates that describe
repeatedly used filesystem layouts such as project structures
or elements therein.

It provides a subclassed implementation of ``xml.sax.handler`` ``ContentHandler``
with internal methods that read,parse,render,and execute builds of
user defined XML directory tree templates.

License: **MIT License**.""".format(version=VERSION)

try:
    from pypandoc import convert
    read_markdown = lambda f: convert(f, 'rst', 'md')
except ImportError:
    print("warning: pypandoc module not found, could not convert Markdown to RST")
    read_markdown = lambda f: eval('LONG_DESCRIPTION')

setup(
    name = "python-dirtt",
    version = VERSION,
    description = DESCRIPTION,
    long_description = read_markdown(README),
    scripts=[
        'scripts/mkproject.py',
        'scripts/mktemplate.py',
        'scripts/mktree.py'
    ],
    packages = find_packages(),
    install_requires = [
        'colorlog',
        'lxml'
    ],
    package_data = {
        'dirtt': [
            'data/dirtt.dtd',
            'data/templates/*.xml',
            'data/templates/*.mel'
        ],
        'tests': [
            'templates/*.xml'
        ]
    },
    include_package_data = True,
    # metadata for upload to PyPI
    classifiers=[
        # 'Development Status :: 1 - Planning',
        # 'Development Status :: 2 - Pre-Alpha',
        # 'Development Status :: 3 - Alpha',
        'Development Status :: 4 - Beta',
        # 'Development Status :: 5 - Production/Stable',
        # 'Development Status :: 6 - Mature',
        # 'Development Status :: 7 - Inactive',
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
    url='http://robmoggach.github.io/python-dirtt/',
    download_url = 'https://github.com/robmoggach/python-dirtt/tarball/v{version}'.format(version=VERSION),
    author='Robert Moggach',
    author_email='rob@moggach.com',
    maintainer='Robert Moggach',
    maintainer_email='rob@moggach.com',
    license='MIT License'
)
