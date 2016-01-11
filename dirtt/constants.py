# -*- coding: utf-8 -*-
""" These are constants used by various dirtt submodules.

The ``dirtt.constants`` module provides module constants used for various reusable needs.
The constants take their value from the calling program environment
(if available), and default to the expected values.

.. note:: if bash environment variable Eg. ``DIRTT_TEMPLATES_DIR`` is set it will be used
    by python scripts running in that environment (if not set programmatically)
"""
import os
import inspect
import sys
import errno
import dirtt
from .internal import _MODULE_PATH



TEMPLATES_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data', 'templates')

try:
    DIRTT_TEMPLATES_DIR = os.environ.get('DIRTT_TEMPLATES_DIR', TEMPLATES_DIR )
    """path to test template xml file"""

    DIRTT_DEFAULT_PERMS = os.environ.get('DIRTT_DEFAULT_PERMS', "02775")
    """default posix permissions for elements without a permissions attribute"""

    DIRTT_DEFAULT_USER = os.environ.get('DIRTT_DEFAULT_USER', 0)
    """default user for elements without a user attribute"""

    DIRTT_DEFAULT_GROUP = os.environ.get('DIRTT_DEFAULT_GROUP', 20)
    """default group for elements without a group attribute"""

    DIRTT_PATH = os.environ.get('DIRTT_PATH', _MODULE_PATH)
    """the module's path attribute for convenience

    this uses the internal attribute ``_MODULE_PATH`` to generate it's path"""

    DIRTT_DEVEL = True if os.environ.get('DIRTT_DEVEL', False) in ['1', 'true', 'True'] else False
    """``DEVEL`` state for more verbose logging
    ie. If you want more debugging set the ``DIRTT_DEVEL`` environment variable"""

    dirtt.LOG.debug(u'DIRTT_DEVEL attribute is {0}'.format(DIRTT_DEVEL) )

except ValueError, e:
    dirtt.LOG.error(errno.EINVAL, e.message)

