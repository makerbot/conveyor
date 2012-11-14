from __future__ import (absolute_import, print_function, unicode_literals)

import unittest

import sys
import os
import json
import cStringIO as StringIO
import logging
import operator
import weakref

#override sys.path for testing only
sys.path.insert(0, './src/main/python')
from conveyor.stoppable import StoppableManager, StoppableInterface

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import mock


class _StoppableTestObject(StoppableInterface):
    def __init__(self):
        StoppableInterface.__init__(self)
        import conveyor.event
        self.callback = conveyor.event.Callback()

    def stop(self):
        self.callback()


class _NotInitializedStoppableTestObject(StoppableInterface):
    def __init__(self):
        import conveyor.event
        self.callback = conveyor.event.Callback()


class _NotStoppableTestObject(object):
    pass


class _StoppableTestCase(unittest.TestCase):

    def test_NotImplementedError(self):
        s = StoppableInterface()
        with self.assertRaises(NotImplementedError):
            s.stop()
        with self.assertRaises(NotImplementedError):
            s.run()

    def test_removestoppable_unknown(self):
        stoppablemanager = StoppableManager.getinstance()
        stoppablemanager._reset()
        s1 = _NotStoppableTestObject()
        stoppablemanager._removestoppable(s1)

    def test_stopall(self):
        stoppablemanager = StoppableManager.getinstance()
        stoppablemanager._reset()
        s1 = _StoppableTestObject()
        s2 = _StoppableTestObject()
        self.assertFalse(s1.callback.delivered)
        self.assertFalse(s2.callback.delivered)
        stoppablemanager._removestoppable(s2)
        StoppableManager.stopall()
        self.assertTrue(s1.callback.delivered)
        self.assertFalse(s2.callback.delivered)

        stoppablemanager._stopall()

    def test_stale_weakref(self):
        stoppablemanager = StoppableManager.getinstance()
        stoppablemanager._reset()
        s1 = _StoppableTestObject()
        s2 = _NotInitializedStoppableTestObject()
        ref = weakref.ref(s2)  # no callback
        stoppablemanager._stoppables.append(ref)
        c2 = s2.callback
        self.assertFalse(s1.callback.delivered)
        self.assertFalse(s2.callback.delivered)
        del s2
        s2 = None
        StoppableManager.stopall()
        self.assertTrue(s1.callback.delivered)
        self.assertFalse(c2.delivered)

    def test_not_init_stoppable(self):
        x = _NotInitializedStoppableTestObject()
        self.assertIsNotNone(x.callback)
        y = _NotStoppableTestObject()

if __name__ == '__main__':
    unittest.main()
