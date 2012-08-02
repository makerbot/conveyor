from __future__ import (absolute_import, print_function, unicode_literals)

import sys
sys.path.insert(0,'src/main/python') # for testing only

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from conveyor.task import * 

class TaskTestCase(unittest.TestCase):
    def _reset(self, callbacks):
        for callback in callbacks:
            callback.reset()

    def _runeventqueue(self, eventqueue):
        while eventqueue.runiteration(False):
            pass

    def test_events(self):
        '''Test event delivery.'''

        eventqueue = conveyor.event.geteventqueue()
        task = Task()

        startcallback = conveyor.event.Callback()
        task.startevent.attach(startcallback)

        heartbeatcallback = conveyor.event.Callback()
        task.heartbeatevent.attach(heartbeatcallback)

        endcallback = conveyor.event.Callback()
        task.endevent.attach(endcallback)

        failcallback = conveyor.event.Callback()
        task.failevent.attach(failcallback)

        cancelcallback = conveyor.event.Callback()
        task.cancelevent.attach(cancelcallback)

        runningcallback = conveyor.event.Callback()
        task.runningevent.attach(runningcallback)

        stoppedcallback = conveyor.event.Callback()
        task.stoppedevent.attach(stoppedcallback)

        callbacks = (
            startcallback, heartbeatcallback, endcallback, failcallback,
            cancelcallback, runningcallback, stoppedcallback)

        self.assertFalse(startcallback.delivered)
        self.assertFalse(heartbeatcallback.delivered)
        self.assertFalse(endcallback.delivered)
        self.assertFalse(failcallback.delivered)
        self.assertFalse(cancelcallback.delivered)
        self.assertFalse(runningcallback.delivered)
        self.assertFalse(stoppedcallback.delivered)

        task.start()
        self._runeventqueue(eventqueue)
        self.assertEqual(TaskState.RUNNING, task.state)
        self.assertTrue(startcallback.delivered)
        self.assertFalse(heartbeatcallback.delivered)
        self.assertFalse(endcallback.delivered)
        self.assertFalse(failcallback.delivered)
        self.assertFalse(cancelcallback.delivered)
        self.assertTrue(runningcallback.delivered)
        self.assertFalse(stoppedcallback.delivered)

        self._reset(callbacks)
        task.progress = None
        task.result = None
        task.failure = None
        task.heartbeat('progress')
        self._runeventqueue(eventqueue)
        self.assertEqual(TaskState.RUNNING, task.state)
        self.assertEqual('progress', task.progress)
        self.assertIsNone(task.result)
        self.assertIsNone(task.failure)
        self.assertFalse(startcallback.delivered)
        self.assertTrue(heartbeatcallback.delivered)
        self.assertFalse(endcallback.delivered)
        self.assertFalse(failcallback.delivered)
        self.assertFalse(cancelcallback.delivered)
        self.assertFalse(runningcallback.delivered)
        self.assertFalse(stoppedcallback.delivered)

        self._reset(callbacks)
        task.progress = None
        task.result = None
        task.failure = None
        task.end('result')
        self._runeventqueue(eventqueue)
        self.assertEqual(TaskState.STOPPED, task.state)
        self.assertIsNone(task.progress)
        self.assertEqual('result', task.result)
        self.assertIsNone(task.failure)
        self.assertFalse(startcallback.delivered)
        self.assertFalse(heartbeatcallback.delivered)
        self.assertTrue(endcallback.delivered)
        self.assertFalse(failcallback.delivered)
        self.assertFalse(cancelcallback.delivered)
        self.assertFalse(runningcallback.delivered)
        self.assertTrue(stoppedcallback.delivered)

        self._reset(callbacks)
        task.progress = None
        task.result = None
        task.failure = None
        task.state = TaskState.RUNNING
        task.fail('failure')
        self._runeventqueue(eventqueue)
        self.assertEqual(TaskState.STOPPED, task.state)
        self.assertIsNone(task.progress)
        self.assertIsNone(task.result)
        self.assertEqual('failure', task.failure)
        self.assertFalse(startcallback.delivered)
        self.assertFalse(heartbeatcallback.delivered)
        self.assertFalse(endcallback.delivered)
        self.assertTrue(failcallback.delivered)
        self.assertFalse(cancelcallback.delivered)
        self.assertFalse(runningcallback.delivered)
        self.assertTrue(stoppedcallback.delivered)

        self._reset(callbacks)
        task.progress = None
        task.result = None
        task.failure = None
        task.state = TaskState.PENDING
        task.cancel()
        self._runeventqueue(eventqueue)
        self.assertEqual(TaskState.STOPPED, task.state)
        self.assertIsNone(task.progress)
        self.assertIsNone(task.result)
        self.assertIsNone(task.failure)
        self.assertFalse(startcallback.delivered)
        self.assertFalse(heartbeatcallback.delivered)
        self.assertFalse(endcallback.delivered)
        self.assertFalse(failcallback.delivered)
        self.assertTrue(cancelcallback.delivered)
        self.assertFalse(runningcallback.delivered)
        self.assertTrue(stoppedcallback.delivered)

        self._reset(callbacks)
        task.progress = None
        task.result = None
        task.failure = None
        task.state = TaskState.RUNNING
        task.cancel()
        self._runeventqueue(eventqueue)
        self.assertEqual(TaskState.STOPPED, task.state)
        self.assertIsNone(task.progress)
        self.assertIsNone(task.result)
        self.assertIsNone(task.failure)
        self.assertFalse(startcallback.delivered)
        self.assertFalse(heartbeatcallback.delivered)
        self.assertFalse(endcallback.delivered)
        self.assertFalse(failcallback.delivered)
        self.assertTrue(cancelcallback.delivered)
        self.assertFalse(runningcallback.delivered)
        self.assertTrue(stoppedcallback.delivered)

    def test__transition_ValueError(self):
        '''Test that the _transition method throws a ValueError when state is
        an unknown value.

        '''

        task = Task()
        task.state = None
        with self.assertRaises(ValueError):
            task._transition(None, None)

    def test__transition_IllegalTransitionException(self):
        '''Test that the _transition method throws an
        IllegalTransitionException when the lifecycle methods are called in the
        wrong order.

        '''

        task = Task()

        def func(state, events):
            task.state = state
            for event in events:
                with self.assertRaises(IllegalTransitionException) as cm:
                    task._transition(event, None) # pragma: no cover
                self.assertEqual(state, cm.exception.state)
                self.assertEqual(event, cm.exception.event)

        events = (TaskEvent.HEARTBEAT, TaskEvent.END, TaskEvent.FAIL,)
        func(TaskState.PENDING, events)

        events = (TaskEvent.START,)
        func(TaskState.RUNNING, events)

        events = (
            TaskEvent.START, TaskEvent.HEARTBEAT, TaskEvent.END,
            TaskEvent.FAIL, TaskEvent.CANCEL,)
        func(TaskState.STOPPED, events)

if __name__ == '__main__':
    unittest.main()


