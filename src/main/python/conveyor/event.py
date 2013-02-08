# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/event.py
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

import collections
import logging
import threading
import time

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import conveyor.log
import conveyor.stoppable
import conveyor.test

_eventqueue = None

def geteventqueue():
    global _eventqueue
    if None is _eventqueue:
        _eventqueue = EventQueue()
    return _eventqueue

class EventQueueThread(conveyor.stoppable.StoppableThread):
    def __init__(self, eventqueue, name):
        conveyor.stoppable.StoppableThread.__init__(self, name=name)
        self._eventqueue = eventqueue
        self._log = conveyor.log.getlogger(self)

    def run(self):
        try:
            self._eventqueue.run()
        except:
            self._log.error('internal error', exc_info=True)

    def stop(self):
        self._eventqueue.stop()

class EventQueue(object):
    def __init__(self):
        self._lock = threading.Lock()
        self._log = conveyor.log.getlogger(self)
        self._condition = threading.Condition(self._lock)
        self._queue = collections.deque()
        self._stop = False

    def runiteration(self, block):
        self._log.debug('block=%r', block)
        with self._condition:
            if block:
                while 0 == len(self._queue) and not self._stop:
                    self._log.debug('waiting')
                    self._condition.wait()
                    self._log.debug('resumed')
            if 0 == len(self._queue):
                tuple_ = None
            else:
                tuple_ = self._queue.pop()
        if None is not tuple_:
            event, args, kwargs = tuple_
            event._deliver(args, kwargs)
        result = None is not tuple_
        self._log.debug('result=%r', result)
        return result

    def run(self):
        self._log.debug('starting')
        self._stop = False
        while not self._stop:
            self.runiteration(True)
        self._log.debug('ending')

    def stop(self):
        event = Event('EventQueue.quit', self)
        def func():
            with self._condition:
                self._stop = True
                self._condition.notify_all()
        event.attach(func)
        event()

    def _enqueue(self, event, args, kwargs):
        self._log.debug('event=%r, args=%r, kwargs=%r', event, args, kwargs)
        tuple_ = event, args, kwargs
        with self._condition:
            self._queue.appendleft(tuple_)
            self._condition.notify_all()

class Event(object):
    """ This represents some kind of event in the conveyor system, mostly 
    updates of data, heartbeat events, or other state-change information about
    a subproject or subsystem. 
    """

    def __init__(self, name, eventqueue=None):
        """ Creates an event object.
        @param eventqueue if a specifi eventqueue is desired.
        """
        self._name = name
        self._eventqueue = eventqueue
        self._handles = {}
        self._log = conveyor.log.getlogger(self)

    def attach(self, func):
        handle = object()
        self._handles[handle] = func
        self._log.debug(
            'name=%r, func=%r, handle=%r', self._name, func, handle)
        return handle

    def detach(self, handle):
        self._log.debug('handle=%r', handle)
        del self._handles[handle]

    def __call__(self, *args, **kwargs):
        """allows calls as Event(foo) to work  """
        self._log.debug(
            'name=%r, args=%r, kwargs=%r', self._name, args, kwargs)
        eventqueue = self._eventqueue
        if None is eventqueue:
            eventqueue = geteventqueue()
        eventqueue._enqueue(self, args, kwargs)

    def _deliver(self, args, kwargs):
        self._log.debug(
            'name=%r, args=%r, kwargs=%r', self._name, args, kwargs)
        for func in self._handles.itervalues():
            try:
                func(*args, **kwargs)
            except:
                self._log.exception('internal error')

    def __repr__(self):
        result = '%s(name=%r, eventqueue=%r)' % (
            self.__class__.__name__, self._name, self._eventqueue)
        return result

class Callback(object):
    def __init__(self):
        self._log = conveyor.log.getlogger(self)
        self.delivered = False
        self.args = None
        self.kwargs = None

    def reset(self):
        self._log.debug('')
        self.delivered = False
        self.args = None
        self.kwargs = None

    def __call__(self, *args, **kwargs):
        self._log.debug('args=%r, kwargs=%r', args, kwargs)
        self.delivered = True
        self.args = args
        self.kwargs = kwargs

class EventQueueTestCase(unittest.TestCase):
    def test(self):
        '''Test the event queue.'''

        eventqueue = geteventqueue()
        eventqueue._queue.clear()

        event = Event('event')
        callback1 = Callback()
        callback2 = Callback()
        handle1 = event.attach(callback1)
        handle2 = event.attach(callback2)
        event.attach(eventqueue.stop)

        self.assertFalse(callback1.delivered)
        self.assertFalse(callback2.delivered)
        event()
        eventqueue.run()
        self.assertTrue(callback1.delivered)
        self.assertTrue(callback2.delivered)

        callback1.reset()
        callback2.reset()
        event.detach(handle1)
        self.assertFalse(callback1.delivered)
        self.assertFalse(callback2.delivered)
        event()
        eventqueue.run()
        self.assertFalse(callback1.delivered)
        self.assertTrue(callback2.delivered)

        callback1.reset()
        callback2.reset()
        event.detach(handle2)
        self.assertFalse(callback1.delivered)
        self.assertFalse(callback2.delivered)
        event()
        eventqueue.run()
        self.assertFalse(callback1.delivered)
        self.assertFalse(callback2.delivered)

    def test_runiteration_empty(self):
        '''Test the runiteration method with an empty queue.'''

        eventqueue = geteventqueue()
        eventqueue._queue.clear()

        self.assertFalse(eventqueue.runiteration(False))

    def test_wait(self):
        '''Test waiting for an event to be delivered by a second thread.'''

        eventqueue = geteventqueue()
        eventqueue._queue.clear()

        event = Event('event')
        callback = Callback()
        event.attach(callback)
        event.attach(eventqueue.stop)
        def target():
            time.sleep(0.1)
            event()
        thread = threading.Thread(target=target)
        thread.start()
        eventqueue.run()
        self.assertTrue(callback.delivered)

    def test_stop(self):
        '''Test the stop method.'''

        eventqueue = geteventqueue()
        eventqueue._queue.clear()

        event1 = Event('event1')
        callback1 = Callback()
        event1.attach(callback1)
        event2 = Event('event2')
        callback2 = Callback()
        event2.attach(callback2)
        event1()
        eventqueue.stop()
        event2()
        eventqueue.run()
        self.assertTrue(callback1.delivered)
        self.assertFalse(callback2.delivered)

    def test_Exception(self):
        '''Test an event handler that throws an exception.'''

        eventqueue = geteventqueue()
        eventqueue._queue.clear()

        conveyor.test.listlogging('ERROR')
        conveyor.test.ListHandler.list = []

        def callback(*args, **kwargs):
            raise Exception('failure')
        event = Event('event')
        event.attach(callback)
        event()
        eventqueue.runiteration(False)

        self.assertEqual(1, len(conveyor.test.ListHandler.list))
        self.assertEqual('internal error', conveyor.test.ListHandler.list[0].msg)

class _EventTestCase(unittest.TestCase):
    def test___repr__(self):
        '''Test the __repr__ method of Event.'''

        event = Event('event')
        self.assertEqual(
            "Event(name=u'event', eventqueue=None)", repr(event))
