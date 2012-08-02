from __future__ import (absolute_import, print_function, unicode_literals)

import sys
sys.path.insert(0,'src/main/python') # for testing only

from conveyor.event import *

try:
    import unittest2 as unittest
except ImportError:
    import unittest

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
        event.attach(eventqueue.quit)

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
        event.attach(eventqueue.quit)
        def target():
            time.sleep(0.1)
            event()
        thread = threading.Thread(target=target)
        thread.start()
        eventqueue.run()
        self.assertTrue(callback.delivered)

    def test_quit(self):
        '''Test the quit method.'''

        eventqueue = geteventqueue()
        eventqueue._queue.clear()

        event1 = Event('event1')
        callback1 = Callback()
        event1.attach(callback1)
        event2 = Event('event2')
        callback2 = Callback()
        event2.attach(callback2)
        event1()
        eventqueue.quit()
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

if __name__ == '__main__':
    unittest.main()


