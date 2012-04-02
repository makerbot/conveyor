# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:

from __future__ import (absolute_import, print_function, unicode_literals)

import conveyor.async
import glib
import unittest

class _GlibAsync(conveyor.async.Async):
    @classmethod
    def _create(cls, func):
        async = _GlibAsync(func)
        async._attach()
        return async

    def __init__(self, func):
        conveyor.async.Async.__init__(self)
        self._func = func
        self._mainloop = None

    def _attach(self):
        self.reply_event.attach(self._mainloop_callback)
        self.error_event.attach(self._mainloop_callback)
        self.timeout_event.attach(self._mainloop_callback)

    def _quit(self):
        if None != self._mainloop:
            self._mainloop.quit()

    def _mainloop_callback(self, *args, **kwargs):
        self._quit()

    def start(self):
        self._transition(conveyor.async.AsyncEvent.START, (), {})
        self._func(self)

    def wait(self):
        if conveyor.async.AsyncState.PENDING == self.state:
            self.start()
        if conveyor.async.AsyncState.RUNNING == self.state:
            assert None == self._mainloop
            self._mainloop = glib.MainLoop()
            try:
                self._mainloop.run()
            finally:
                self._mainloop = None

    def cancel(self):
        self._transition(conveyor.async.AsyncEvent.CANCEL, (), {})
        self._quit()

def fromfunc(func):
    async = _GlibAsync._create(func)
    return async

class _GlibAsyncTestCase(unittest.TestCase):
    def test_reply(self):
        def func(async):
            def callable():
                async.reply_trigger('xyzzy')
                return False
            glib.timeout_add(1000, callable)
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
            glib.timeout_add(1000, callable)
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
            glib.timeout_add(1000, callable)
        async = fromfunc(func)
        self.assertEqual(conveyor.async.AsyncState.PENDING, async.state)
        async.wait()
        self.assertEqual(conveyor.async.AsyncState.CANCELED, async.state)
