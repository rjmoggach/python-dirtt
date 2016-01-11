# -*- coding: utf-8 -*-
"""provides custom Dirtt base and sub-classed exceptions"""

__all__ = [ 'InvalidDirttTemplateFile', 'DirttFormatError', 'DirttEnvError' ]

class BaseDirttException(Exception):
    """base exception for custom OpenClip exceptions"""
    def __init__(self, message=None):
        if not message:
            message = "Unknown OpenClip Exception."
        self.message = message
        super(BaseDirttException, self).__init__(self.message)


class InvalidDirttTemplateFile(BaseDirttException):
    """exception for invalid clip file errors"""
    def __init__(self, message=None):
        super(InvalidDirttTemplateFile, self).__init__(message)


class DirttFormatError(BaseDirttException):
    """exception for seq format errors"""
    def __init__(self, message=None):
        super(DirttFormatError, self).__init__(message)


class DirttEnvError(BaseDirttException):
    """exception for openclip environment errors"""
    def __init__(self, message=None):
        super(DirttEnvError, self).__init__(message)


