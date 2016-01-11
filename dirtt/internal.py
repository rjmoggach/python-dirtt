# -*- coding: utf-8 -*-
"""non-public methods for internal module consumption"""
import os
import inspect
import sys

_MODULE_PATH = os.path.dirname(inspect.getfile(sys._getframe(0)))
"""system path to openclip module"""