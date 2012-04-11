# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:

from __future__ import (absolute_import, print_function, unicode_literals)

import conveyor.async
import glib
import unittest

def _initialize():
    pass

def asyncfunc(func):
    _initialize()
    async = _GlibAsync._create(func)
    return async

class _GlibAsync(conveyor.async.Async):
    @classmethod
    def _create(cls, func):
        async = _GlibAsync(func)
        return async

    def __init__(self, func):
        conveyor.async.Async.__init__(self)
        self._func = func

    def start(self):
        self._transition(conveyor.async.AsyncEvent.START, (), {})
        self._func(self)

    def wait(self):
        mainloop = glib.MainLoop()
        def func(*args, **kwargs):
            mainloop.quit()
        for event in (self.reply_event, self.error_event, self.timeout_event,
            self.cancel_event):
                event.attach(func)
        if conveyor.async.AsyncState.PENDING == self.state:
            self.start()
        mainloop.run()

class _GlibAsyncTestCase(unittest.TestCase):
    def test_reply(self):
        def func(async):
            def callable():
                async.reply_trigger('xyzzy')
                return False
            glib.timeout_add(1000, callable)
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
            glib.timeout_add(1000, callable)
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
            glib.timeout_add(1000, callable)
        async = asyncfunc(func)
        self.assertEqual(conveyor.async.AsyncState.PENDING, async.state)
        async.wait()
        self.assertEqual(conveyor.async.AsyncState.CANCELED, async.state)

    def test_wait_started(self):
        def func(async):
            def callable():
                async.reply_trigger('xyzzy')
                return False
            glib.timeout_add(1000, callable)
        async = asyncfunc(func)
        self.assertEqual(conveyor.async.AsyncState.PENDING, async.state)
        async.start()
        async.wait()
        self.assertEqual(conveyor.async.AsyncState.SUCCESS, async.state)
        self.assertEqual((('xyzzy',), {}), async.reply)
