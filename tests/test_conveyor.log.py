from __future__ import (absolute_import, print_function, unicode_literals)

import sys
sys.path.insert(0,'src/main/python') # for testing only

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from conveyor.log import *

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

if __name__ == '__main__':
    unittest.main()


