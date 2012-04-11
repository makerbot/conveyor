# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:

from __future__ import (absolute_import, print_function, unicode_literals)

import PyQt4.QtCore
import conveyor.async
import sys
import unittest

#
# We need to keep a reference to the QCoreApplication or it gets garbage
# collected and QT stops working.
#

_application = None

def _initialize():
    global _application
    if None == _application:
        _application = PyQt4.QtCore.QCoreApplication(sys.argv)

def asyncfunc(func):
    _initialize()
    async = _QtAsync._create(func)
    return async

class _QtAsync(conveyor.async.Async):
    @classmethod
    def _create(cls, func):
        async = _QtAsync(func)
        return async

    def __init__(self, func):
        conveyor.async.Async.__init__(self)
        self._func = func

    def start(self):
        self._transition(conveyor.async.AsyncEvent.START, (), {})
        self._func(self)

    def wait(self):
        eventloop = PyQt4.QtCore.QEventLoop()
        def func(*args, **kwargs):
            eventloop.exit()
        for event in (self.reply_event, self.error_event, self.timeout_event,
            self.cancel_event):
                event.attach(func)
        if conveyor.async.AsyncState.PENDING == self.state:
            self.start()
        eventloop.exec_()

class _QtAsyncTestCase(unittest.TestCase):
    def test_reply(self):
        def func(async):
            def callable():
                async.reply_trigger('xyzzy')
                return False
            PyQt4.QtCore.QTimer.singleShot(1000, callable)
        async = asyncfunc(func)
        self.assertEqual(conveyor.async.AsyncState.PENDING, async.state)
        async.wait()
        self.assertEqual(conveyor.async.AsyncState.SUCCESS, async.state)
        self.assertEqual((('xyzzy',), {}), async.reply)

    def test_error(self):
        def func(async):
            def callable():
                async.error_trigger('xyzzy')
                return False
            PyQt4.QtCore.QTimer.singleShot(1000, callable)
        async = asyncfunc(func)
        self.assertEqual(conveyor.async.AsyncState.PENDING, async.state)
        async.wait()
        self.assertEqual(conveyor.async.AsyncState.ERROR, async.state)
        self.assertEqual((('xyzzy',), {}), async.error)

    def test_cancel(self):
        def func(async):
            def callable():
                async.cancel()
                return False
            PyQt4.QtCore.QTimer.singleShot(1000, callable)
        async = asyncfunc(func)
        self.assertEqual(conveyor.async.AsyncState.PENDING, async.state)
        async.wait()
        self.assertEqual(conveyor.async.AsyncState.CANCELED, async.state)

    def test_wait_started(self):
        def func(async):
            def callable():
                async.reply_trigger('xyzzy')
                return False
            PyQt4.QtCore.QTimer.singleShot(1000, callable)
        async = asyncfunc(func)
        self.assertEqual(conveyor.async.AsyncState.PENDING, async.state)
        async.start()
        async.wait()
        self.assertEqual(conveyor.async.AsyncState.SUCCESS, async.state)
        self.assertEqual((('xyzzy',), {}), async.reply)
