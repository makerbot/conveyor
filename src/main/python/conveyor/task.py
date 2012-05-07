# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:

from __future__ import (absolute_import, print_function, unicode_literals)

import threading
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from conveyor import enum, event

TaskState = enum.enum('TaskState', 'PENDING', 'RUNNING', 'STOPPED')

TaskEvent = enum.enum(
    'TaskEvent', 'START', 'HEARTBEAT', 'END', 'FAIL', 'CANCEL')

TaskConclusion = enum.enum('TaskConclusion', 'ENDED', 'FAILED', 'CANCELED')

class IllegalTransitionException(Exception):
    def __init__(self, state, event):
        Exception.__init__(self, state, event)
        self.state = state
        self.event = event

class Task(object):
    def __init__(self, eventqueue=None):
        self.state = TaskState.PENDING
        self.conclusion = None

        self.progress = None # data from 'heartbeat'
        self.result = None   # data from 'end'
        self.failure = None  # data from 'fail'

        # Event events (edge-ish events)
        self.startevent = event.Event('Task.startevent', eventqueue)
        self.heartbeatevent = event.Event('Task.heartbeatevent', eventqueue)
        self.endevent = event.Event('Task.endevent', eventqueue)
        self.failevent = event.Event('Task.failevent', eventqueue)
        self.cancelevent = event.Event('Task.cancelevent', eventqueue)

        # State events (level-ish events)
        self.runningevent = event.Event('Task.runningevent', eventqueue)
        self.stoppedevent = event.Event('Task.stoppedevent', eventqueue)

    def _transition(self, event, data):
        if TaskState.PENDING == self.state:
            if TaskEvent.START == event:
                self.state = TaskState.RUNNING
                self.startevent(self)
                self.runningevent(self)
            elif TaskEvent.CANCEL == event:
                self.state = TaskState.STOPPED
                self.conclusion = TaskConclusion.CANCELED
                self.cancelevent(self)
                self.stoppedevent(self)
            else:
                raise IllegalTransitionException(self.state, event)
        elif TaskState.RUNNING == self.state:
            if TaskEvent.HEARTBEAT == event:
                self.progress = data
                self.heartbeatevent(self)
            elif TaskEvent.END == event:
                self.state = TaskState.STOPPED
                self.conclusion = TaskConclusion.ENDED
                self.result = data
                self.endevent(self)
                self.stoppedevent(self)
            elif TaskEvent.FAIL == event:
                self.state = TaskState.STOPPED
                self.conclusion = TaskConclusion.FAILED
                self.failure = data
                self.failevent(self)
                self.stoppedevent(self)
            elif TaskEvent.CANCEL == event:
                self.state = TaskState.STOPPED
                self.conclusion = TaskConclusion.CANCELED
                self.cancelevent(self)
                self.stoppedevent(self)
            else:
                raise IllegalTransitionException(self.state, event)
        elif TaskState.STOPPED == self.state:
            raise IllegalTransitionException(self.state, event)
        else:
            raise ValueError(self.state)

    def start(self):
        self._transition(TaskEvent.START, None)

    def heartbeat(self, progress):
        self._transition(TaskEvent.HEARTBEAT, progress)

    def end(self, result):
        self._transition(TaskEvent.END, result)

    def fail(self, failure):
        self._transition(TaskEvent.FAIL, failure)

    def cancel(self):
        self._transition(TaskEvent.CANCEL, None)

class TaskTestCase(unittest.TestCase):
    def _reset(self, callbacks):
        for callback in callbacks:
            callback.reset()

    def _runeventqueue(self, eventqueue):
        while eventqueue.runiteration(False):
            pass

    def test_events(self):
        eventqueue = event.geteventqueue()
        task = Task()

        startcallback = event.Callback()
        task.startevent.attach(startcallback)

        heartbeatcallback = event.Callback()
        task.heartbeatevent.attach(heartbeatcallback)

        endcallback = event.Callback()
        task.endevent.attach(endcallback)

        failcallback = event.Callback()
        task.failevent.attach(failcallback)

        cancelcallback = event.Callback()
        task.cancelevent.attach(cancelcallback)

        runningcallback = event.Callback()
        task.runningevent.attach(runningcallback)

        stoppedcallback = event.Callback()
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

    def test__transition_notastate(self):
        task = Task()
        task.state = None
        with self.assertRaises(ValueError):
            task._transition(None, None)

    def test__transition_IllegalTransitionException(self):
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
