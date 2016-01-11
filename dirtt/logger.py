# -*- coding: utf-8 -*-
"""wraps python logging to ease logging

    Below are the logging levels for reference:

    * `DEBUG`       Detailed information, typically of interest only when diagnosing problems.
    * `INFO`        Confirmation that things are working as expected.
    * `WARNING`     An indication that something unexpected happened,
                    or indicative of some problem in the near future
                    (e.g. 'disk space low'). The software is still working as expected.
    * `ERROR`       Due to a more serious problem, the software has not
                    been able to perform some function.
    * `CRITICAL`    A serious error, indicating that the program itself
                    may be unable to continue running.
"""
import os
import sys
import logging
import types
try:
    from colorlog import ColoredFormatter
    COLORED=True
    LOG_COLORS = {
        'DEBUG':    'cyan',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'red',
    }
except:
    COLORED=False


class DirttLogger(object):
    """
    Dirtt logging class

    Usage:

        LOG.debug('this is an exception.')
    """
    def __init__(self):
        self.set_formatters()

        self.stream_handler = logging.StreamHandler()
        self.stream_handler.setFormatter(self.formatter)
        self.stream_handler.setLevel(self.level)

        self.LOG = logging.getLogger('dirtt')
        self.LOG.addHandler(self.stream_handler)
        sys.excepthook = self.exception_handler
        self.LOG.flush = types.MethodType(self.__flush_log, self.LOG)
        self.LOG.remove_stream_handler = types.MethodType(self.__remove_stream_handler, self.LOG)
        self.LOG.setLevel(self.level)

    @property
    def level(self):
        if os.environ.get("DIRTT_DEVEL", False) in ['1', 'true', 'True']:
            return logging.DEBUG
        else:
            return logging.INFO

    def __flush_log(self, log):
        """Flush a log"""
        for handler in log.handlers:
            if hasattr(handler,'flush'):
                handler.flush()

    def __remove_stream_handler(self, log):
        """remove stream handler from a given log object"""
        handlers_to_remove = []
        for i,handler in enumerate(log.handlers):
            if handler == self.stream_handler:
                handlers_to_remove.append(i)
        for x in reversed(handlers_to_remove):
            del log.handlers[x]

    def exception_handler(self, exception_type, exception_value, traceback):
        """Creates an exception handler to replace the standard except hook"""
        self.stream_handler.setFormatter(self.exc_formatter)
        self.LOG.critical("Uncaught exception", exc_info=(exception_type, exception_value, traceback))
        self.stream_handler.setFormatter(self.formatter)

    def set_formatters(self):
        if not COLORED:
            default_format = '%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s'
            exc_format = '%(asctime)s %(levelname)s: %(message)s'
            date_format = '%Y-%m-%d %H:%M:%S'
            self.exc_formatter = logging.Formatter(exc_format, date_format)
            self.formatter = logging.Formatter(format, date_format)
        else:
            default_format = '%(log_color)s%(levelname)s%(reset)s %(filename)s:%(lineno)d %(message)s'
            exc_format = '%(log_color)s%(levelname)s%(reset)s: %(message)s'
            date_format = '%Y-%m-%d %H:%M:%S'
            self.exc_formatter = ColoredFormatter( exc_format, datefmt=date_format, reset=True, log_colors = LOG_COLORS, secondary_log_colors={}, style='%' )
            self.formatter = ColoredFormatter( default_format, datefmt=date_format, reset=True, log_colors = LOG_COLORS, secondary_log_colors={}, style='%' )


