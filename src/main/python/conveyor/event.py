# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:

from __future__ import (absolute_import, print_function, unicode_literals)

import unittest

class Event(object):
    def __init__(self):
        self._counter = 0
        self._callbacks = {}

    def attach(self, callback):
        handle = self._counter
        self._counter += 1
        self._callbacks[handle] = callback
        return handle

    def detach(self, handle):
        del self._callbacks[handle]

    def __call__(self, *args, **kwargs):
        for callback in self._callbacks.itervalues():
            callback(*args, **kwargs)

class Callback(object):
    def __init__(self):
        self.reset()

    def reset(self):
        self.delivered = False
        self.args = None
        self.kwargs = None

    def __call__(self, *args, **kwargs):
        self.delivered = True
        self.args = args
        self.kwargs = kwargs

class _EventTestCase(unittest.TestCase):
    def test(self):
        event = Event()
        callback1 = Callback()
        callback2 = Callback()
        handle1 = event.attach(callback1)
        handle2 = event.attach(callback2)
        self.assertFalse(callback1.delivered)
        self.assertFalse(callback2.delivered)
        event(1, a=2)
        self.assertTrue(callback1.delivered)
        self.assertTrue(callback2.delivered)
        self.assertEqual((1,), callback1.args)
        self.assertEqual((1,), callback2.args)
        self.assertEqual({'a':2}, callback1.kwargs)
        self.assertEqual({'a':2}, callback2.kwargs)
        callback1.reset()
        callback2.reset()
        event.detach(handle2)
        self.assertFalse(callback1.delivered)
        self.assertFalse(callback2.delivered)
        event(3, b=4)
        self.assertTrue(callback1.delivered)
        self.assertFalse(callback2.delivered)
        self.assertEqual((3,), callback1.args)
        self.assertEqual({'b':4}, callback1.kwargs)
