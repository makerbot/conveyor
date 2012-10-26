import unittest

import sys
import os

#override sys.path for testing only 
sys.path.insert(0,'./src/main/python')
import conveyor
from conveyor.task import Task,TaskState,TaskEvent,IllegalTransitionException

class TaskTestCase(unittest.TestCase):
    

    def test_heartbeat_to_end(self):
        testTask = Task()

        # test heartbeat after start
        testTask.start() 
        testTask.heartbeat(None) 
        testTask.heartbeat(None) 
        testTask.heartbeat(None) 
        testTask.end(None)

 
    def test_heartbeat(self):
        testTask = Task()
        # Test failure to heartbeat before start, Illegal chage out of PENDING
        cur_progress = None
        with self.assertRaises(IllegalTransitionException):
            testTask.heartbeat(cur_progress)

        # test heartbeat after start
        testTask.start() 
        testTask.heartbeat(cur_progress) 
         
        testTask.end(None)
        with self.assertRaises(IllegalTransitionException):
            testTask.heartbeat(cur_progress) 
     
    def test_lazy_heartbeat(self):
        
        testTask = Task()
        # Test failure to heartbeat before start, Illegal chage out of PENDING
        cur_progress = None
        # TRICKY: lazy heartbeat won't throw exception, None case ignored
        testTask.lazy_heartbeat(cur_progress)
        
        cur_progress = {'task':'thing', 'percent':'0'}
        # TRICKY: lazy heartbeat throw exception progres is not None
        with self.assertRaises(IllegalTransitionException):
            testTask.lazy_heartbeat(cur_progress)

        old_progress = cur_progress
        # TRICKY: lazy heartbeat won't throw exception, dup progress ignored
        testTask.lazy_heartbeat(cur_progress, old_progress)
        new_progress = {'task':'thing','percent':'1'}
        with self.assertRaises(IllegalTransitionException):
            testTask.lazy_heartbeat(new_progress, cur_progress)

         
        # TRICKY: 
        #testTask.heartbeat(cur_progress)
#        self.assertEquals(testTask.data, cur_progress)
        


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

if __name__ == "__main__":
    unittest.main()


