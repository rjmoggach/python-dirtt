# -*- coding: utf-8 -*-
"""Python Directory Tree Templater
========================================

``python-dirtt`` is a python package used to generate
directory and file structures from XML templates that describe
repeatedly used filesystem layouts such as project structures
or elements therein.

It provides a subclassed implementation of ``xml.sax.handler`` ``ContentHandler``
with internal methods that read,parse,render,and execute builds of
user defined XML directory tree templates.

It also defines it's own XML schema for validation and standardization purposes.

License: **MIT License**.
"""

__version__ = "0.3.1"

__docformat__ = 'reStructuredText'

__name__ = 'dirtt'


# logger relies on: constants
import sys as _sys
from logger import DirttLogger
LOG = DirttLogger().LOG


# constants relies on: exceptions, LOG, internal
import constants
_module_name = _sys.modules[__name__]
setattr(_module_name, '_c', constants)


# const relies on: constants, exceptions, internal
from const import const, set_const
__all__  = [ '_c', 'const', 'set_const' ]


import handler
from handler import *
__all__.extend(handler.__all__)


import introspection
from introspection import *
__all__.extend(introspection.__all__)


import util
__all__.append('util')

import string
__all__.append('string')

import posix
__all__.append('posix')

import exceptions
from exceptions import *
__all__.append(exceptions.__all__)

from template import Template
__all__.append('Template')