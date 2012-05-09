# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/log.py
#
# conveyor - Printing dispatch engine for 3D objects and their friends.
# Copyright © 2012 Matthew W. Samsonoff <matthew.samsonoff@makerbot.com>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from __future__ import (absolute_import, print_function, unicode_literals)

import logging

try:
    import unittest2 as unittest
except ImportError:
    import unittest

class ConsoleFormatter(logging.Formatter):
    '''A log formatter that does not emit the exception stack trace.'''

    def format(self, record):
        record.message = record.getMessage()
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)
        s = self._fmt % record.__dict__
        return s

class DebugFormatter(object):  
    '''A log formatter that has a second format for DEBUG messages.'''

    def __init__(self, format, datefmt, debugformat):
        self._formatter = logging.Formatter(format, datefmt)
        self._debugformatter = logging.Formatter(debugformat, datefmt)

    def format(self, record):
        if logging.DEBUG != record.levelno:
            result = self._formatter.format(record)
        else:
            result = self._debugformatter.format(record)
        return result

    def formatTime(self, record, datefmt=None):
        if logging.DEBUG != record.levelno:
            result = self._formatter.formatTime(record, datefmt)
        else:
            result = self._debugformatter.formatTime(record, datefmt)
        return result

    def formatException(self, exc_info):
        if logging.DEBUG != record.levelno:
            result = self._formatter.formatException(exc_info)
        else:
            result = self._debugformatter.formatException(exc_info)
        return result

class StdoutFilter(object):
    '''A log filter that only accepts INFO messages.'''

    def filter(self, record):
        result = (record.levelno == logging.INFO)
        return result

class StderrFilter(object):
    '''A log filter that only accepts WARNING, ERROR, and CRITICAL messages.'''

    def filter(self, record):
        result = (record.levelno >= logging.WARNING)
        return result
