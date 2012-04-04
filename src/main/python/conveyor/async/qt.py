# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:

from __future__ import (absolute_import, print_function, unicode_literals)

import PyQt4.QtCore
import conveyor.async
import sys
import unittest

class _QtAsync(conveyor.async.Async):
    @classmethod
    def _create(cls, func):
        async = _QtAsync(func)
        async._attach()
        return async

    def __init__(self, func):
        conveyor.async.Async.__init__(self)
        self._func = func
        self._eventloop = None

    def _attach(self):
        for event in (self.reply_event, self.error_event,
            self.timeout_event):
                event.attach(self._eventloop_callback)

    def _quit(self):
        if None != self._eventloop:
            self._eventloop.exit()

    def _eventloop_callback(self, *args, **kwargs):
        self._quit()

    def start(self):
        self._transition(conveyor.async.AsyncEvent.START, (), {})
        self._func(self)

    def wait(self):
        if conveyor.async.AsyncState.PENDING == self.state:
            self.start()
        if conveyor.async.AsyncState.RUNNING == self.state:
            assert None == self._eventloop
            self._eventloop = PyQt4.QtCore.QEventLoop()
            try:
                self._eventloop.exec_()
            finally:
                self._eventloop = None

    def cancel(self):
        self._transition(conveyor.async.AsyncEvent.CANCEL, (), {})
        self._quit()

def fromfunc(func):
    async = _QtAsync._create(func)
    return async

class _QtAsyncTestCase(unittest.TestCase):
    def setUp(self):
        self.application = PyQt4.QtCore.QCoreApplication(sys.argv)

    def test_reply(self):
        def func(async):
            def callable():
                async.reply_trigger('xyzzy')
                return False
            PyQt4.QtCore.QTimer.singleShot(1000, callable)
        async = fromfunc(func)
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
        async = fromfunc(func)
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
        async = fromfunc(func)
        self.assertEqual(conveyor.async.AsyncState.PENDING, async.state)
        async.wait()
        self.assertEqual(conveyor.async.AsyncState.CANCELED, async.state)
