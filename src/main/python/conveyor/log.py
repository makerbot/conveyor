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

import json
import logging
import logging.config
import os.path
import sys
import time

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import conveyor.event

if not hasattr(logging.config, 'dictConfig'):
    import conveyor.dictconfig
    logging.config.dictConfig = conveyor.dictconfig.dictConfig

if hasattr(logging, '_checkLevel'):
    _checkLevel = logging._checkLevel
else:
    import conveyor.dictconfig
    _checkLevel = conveyor.dictconfig._checkLevel

def checklevel(level):
    return _checkLevel(level)

def getlogger(o):
    if not hasattr(o, '__module__'):
        name = o.__class__.__name__
    else:
        name = '.'.join((o.__module__, o.__class__.__name__))
    logger = logging.getLogger(name)
    return logger

def earlylogging(program, early_debugging=False): # pragma: no cover
    '''Initialize console logging for the early part of a conveyor process.'''

    dct = {
        'version': 1,
        'formatters': {
            'console': {
                '()': 'conveyor.log.ConsoleFormatter',
                'format': '%s: %%(levelname)s: %%(message)s' % (program,),
            },
            'log': {
                '()': 'conveyor.log.DebugFormatter',
                'format': '%(asctime)s - %(levelname)s - %(message)s',
                'datefmt': None,
                'debugformat': '%(asctime)s - %(levelname)s - %(pathname)s:%(lineno)d - %(funcName)s - %(message)s',
            },
        },
        'filters': {
            'stdout': { '()': 'conveyor.log.StdoutFilter' },
            'stderr': { '()': 'conveyor.log.StderrFilter' },
        },
        'handlers': {
            'stdout': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'console',
                'filters': ['stdout'],
                'stream': 'ext://sys.stdout',
            },
            'stderr': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'console',
                'filters': ['stderr'],
                'stream': 'ext://sys.stderr',
            },
        },
        'loggers': {
        },
        'root': {
            'level': 'INFO',
            'propagate': True,
            'filters': [],
            'handlers': ['stdout', 'stderr'],
        },
        'incremental': False,
        'disable_existing_loggers': True,
    }
    if early_debugging:
        filename = ''.join((program, '-startup.log'))
        dct['handlers']['log'] = {
            'class': 'logging.FileHandler',
            'level': 'NOTSET',
            'formatter': 'log',
            'filters': [],
            'filename': filename,
        }
        dct['root']['level'] = 'NOTSET'
        dct['root']['handlers'].append('log')
    logging.config.dictConfig(dct)

def getfiles():
    '''Return an iterator of the files open by the logging system.

    This assumes that the relevant logging handlers are subclasses of
    logging.StreamHandler.

    This function relies on internal logging module voodoo.

    '''

    logging._acquireLock()
    try:
        for handler in logging._handlerList:
            if callable(handler):
                handler = handler() # The handler is a weakref.ref as of Python 2.7
            if isinstance(handler, logging.StreamHandler):
                yield handler.stream
    finally:
        logging._releaseLock()

class ConsoleFormatter(logging.Formatter):
    '''A log formatter that does not emit the exception stack trace unless
    DEBUG is enabled.

    '''

    def format(self, record):
        log = logging.getLogger(record.name)
        if logging.DEBUG == log.getEffectiveLevel():
            s = logging.Formatter.format(self, record)
        else:
            record.message = record.getMessage()
            if '%(asctime)' in self._fmt:
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

class _ConsoleFormatterTestCase(unittest.TestCase):
    def test_stacktrace(self):
        '''Test that the ConsoleFormatter only prints the stack trace when the
        log level is set to DEBUG.

        '''

        name = 'conveyor.log._ConsoleFormatterTestCase'
        log = logging.getLogger(name)
        formatter = ConsoleFormatter()
        for level in (
            logging.CRITICAL,
            logging.ERROR,
            logging.WARNING,
            logging.INFO,
            ):
                log.setLevel(level)
                try:
                    raise Exception('message')
                except:
                    record = logging.LogRecord(
                        name, level, 'pathname', 1, 'message', {},
                        sys.exc_info())
                    s = formatter.format(record)
                    self.assertNotIn('Traceback (most recent call last):', s)
                    record = logging.LogRecord(
                        name, level, 'pathname', 1, 'message', {},
                        sys.exc_info())
                    s = formatter.format(record)
                    self.assertNotIn('Traceback (most recent call last):', s)
        log.setLevel(logging.DEBUG)
        try:
            raise Exception('message')
        except:
            record = logging.LogRecord(
                name, logging.DEBUG, 'pathname', 1, 'message', {},
                sys.exc_info())
            s = formatter.format(record)
            self.assertIn('Traceback (most recent call last):', s)

    def test_formatTime(self):
        '''Test that the ConsoleFormatter formats time correctly.

        NOTE: this test may fail if you run it near midnight on December 31st.

        '''

        name = 'conveyor.log._ConsoleFormatterTestCase'
        log = logging.getLogger(name)
        log.setLevel(logging.INFO)
        formatter = ConsoleFormatter('%(asctime)s', '%Y')
        record = logging.LogRecord(
            name, logging.INFO, 'pathname', 1, 'message', {}, False)
        s = formatter.format(record)
        self.assertEqual(time.strftime('%Y'), s)

class _StubFormatter(object):
    def __init__(self):
        self.formatcallback = conveyor.event.Callback()
        self.formattimecallback = conveyor.event.Callback()
        self.formatexceptioncallback = conveyor.event.Callback()

    def format(self, record):
        self.formatcallback(record)

    def formatTime(self, record, datefmt=None):
        self.formattimecallback(record, datefmt)

    def formatException(self, exc_info):
        self.formatexceptioncallback(exc_info)

class _DebugFormatterTestCase(unittest.TestCase):
    def _resetcallbacks(self, stubformatter, stubdebugformatter):
        for stub in (stubformatter, stubdebugformatter):
            for callback in (
                stub.formatcallback,
                stub.formattimecallback,
                stub.formatexceptioncallback,
                ):
                    callback.reset()

    def test_format(self):
        '''Test that the DebugFormatter uses the appropriate formatter instance
        to format messages.

        '''

        stubformatter = _StubFormatter()
        stubdebugformatter = _StubFormatter()
        debugformatter = DebugFormatter('', '', None)
        debugformatter._formatter = stubformatter
        debugformatter._debugformatter = stubdebugformatter
        for level in (
            logging.CRITICAL,
            logging.ERROR,
            logging.WARNING,
            logging.INFO,
            ):
                self._resetcallbacks(stubformatter, stubdebugformatter)
                record = logging.LogRecord(
                    'name', level, 'pathname', 1, 'message', {}, False)
                debugformatter.format(record)
                self.assertTrue(stubformatter.formatcallback.delivered)
                self.assertFalse(stubdebugformatter.formatcallback.delivered)
        self._resetcallbacks(stubformatter, stubdebugformatter)
        record = logging.LogRecord(
            'name', logging.DEBUG, 'pathname', 1, 'message', {}, False)
        debugformatter.format(record)
        self.assertFalse(stubformatter.formatcallback.delivered)
        self.assertTrue(stubdebugformatter.formatcallback.delivered)

    def test_formatTime(self):
        '''Test that the DebugFormatter uses the appropriate formatter instance
        to format the time.

        '''

        stubformatter = _StubFormatter()
        stubdebugformatter = _StubFormatter()
        debugformatter = DebugFormatter('', '', None)
        debugformatter._formatter = stubformatter
        debugformatter._debugformatter = stubdebugformatter
        for level in (
            logging.CRITICAL,
            logging.ERROR,
            logging.WARNING,
            logging.INFO,
            ):
                self._resetcallbacks(stubformatter, stubdebugformatter)
                record = logging.LogRecord(
                    'name', level, 'pathname', 1, 'message', {}, False)
                debugformatter.formatTime(record)
                self.assertTrue(stubformatter.formattimecallback.delivered)
                self.assertFalse(
                    stubdebugformatter.formattimecallback.delivered)
        self._resetcallbacks(stubformatter, stubdebugformatter)
        record = logging.LogRecord(
            'name', logging.DEBUG, 'pathname', 1, 'message', {}, False)
        debugformatter.formatTime(record)
        self.assertFalse(stubformatter.formattimecallback.delivered)
        self.assertTrue(stubdebugformatter.formattimecallback.delivered)

    def test_formatException(self):
        '''Test that the DebugFormatter uses its _debugformatter instance to
        format exceptions.

        '''

        stubformatter = _StubFormatter()
        stubdebugformatter = _StubFormatter()
        debugformatter = DebugFormatter('', '', None)
        debugformatter._formatter = stubformatter
        debugformatter._debugformatter = stubdebugformatter
        for level in (
            logging.CRITICAL,
            logging.ERROR,
            logging.WARNING,
            logging.INFO,
            logging.DEBUG,
            ):
                self._resetcallbacks(stubformatter, stubdebugformatter)
                record = logging.LogRecord(
                    'name', level, 'pathname', 1, 'message', {}, False)
                debugformatter.formatException(record)
                self.assertFalse(
                    stubformatter.formatexceptioncallback.delivered)
                self.assertTrue(
                    stubdebugformatter.formatexceptioncallback.delivered)

class _StdoutFilterTestCase(unittest.TestCase):
    def test_filter(self):
        '''Test that the StdoutFilter only accepts INFO message.'''

        filter = StdoutFilter()
        record = logging.LogRecord(
            'name', logging.INFO, 'pathname', 1, 'message', {}, False)
        self.assertTrue(filter.filter(record))
        for level in (
            logging.CRITICAL,
            logging.ERROR,
            logging.WARNING,
            logging.DEBUG,
            ):
                record = logging.LogRecord(
                    'name', level, 'pathname', 1, 'message', {}, False)
                self.assertFalse(filter.filter(record))

class _StderrFilterTestCase(unittest.TestCase):
    def test_filter(self):
        '''Test that the StderrFilter accepts only CRITICAL, ERROR, and WARNING
        messages.

        '''

        filter = StderrFilter()
        record = logging.LogRecord(
            'name', logging.INFO, 'pathname', 1, 'message', {}, False)
        for level in (
            logging.CRITICAL,
            logging.ERROR,
            logging.WARNING,
            ):
                record = logging.LogRecord(
                    'name', level, 'pathname', 1, 'message', {}, False)
                self.assertTrue(filter.filter(record))
        for level in (
            logging.INFO,
            logging.DEBUG,
            ):
                record = logging.LogRecord(
                    'name', level, 'pathname', 1, 'message', {}, False)
                self.assertFalse(filter.filter(record))
