"""
python-dirtt - Directory Tree Templater
(c) 2012 Dashing Collective Inc. and contributors
Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php

dirtt is a standalone tool and library used to generate 
directory and file structures from xml templates that describe 
repeatedly used filesystem layouts such as project structures
or elements therein.

It provides a subclassed implementation of xml.sax.handler ContentHandler
with internal methods that read,parse,render,and execute builds of
user defined XML directory tree templates.
"""

__all__ = ['general','io','looper','template','introspection']
from general import *
import io
import looper
import template
