# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/task.py
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

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import conveyor.enum
import conveyor.event

TaskState = conveyor.enum.enum('TaskState', 'PENDING', 'RUNNING', 'STOPPED')

TaskEvent = conveyor.enum.enum(
    'TaskEvent', 'START', 'HEARTBEAT', 'END', 'FAIL', 'CANCEL')

TaskConclusion = conveyor.enum.enum(
    'TaskConclusion', 'ENDED', 'FAILED', 'CANCELED')

class IllegalTransitionException(Exception):
    def __init__(self, state, event):
        Exception.__init__(self, state, event)
        self.state = state
        self.event = event

class Task(object):
    def __init__(self, eventqueue=None):
        self.state = TaskState.PENDING
        self.conclusion = None
        self.name = None
        self.data = None

        self.progress = None # data from 'heartbeat'
        self.result = None   # data from 'end'
        self.failure = None  # data from 'fail'

        # Event events (edge-ish events)
        self.startevent = conveyor.event.Event('Task.startevent', eventqueue)
        self.heartbeatevent = conveyor.event.Event(
            'Task.heartbeatevent', eventqueue)
        self.endevent = conveyor.event.Event('Task.endevent', eventqueue)
        self.failevent = conveyor.event.Event('Task.failevent', eventqueue)
        self.cancelevent = conveyor.event.Event('Task.cancelevent', eventqueue)

        # State events (level-ish events)
        self.runningevent = conveyor.event.Event(
            'Task.runningevent', eventqueue)
        self.stoppedevent = conveyor.event.Event(
            'Task.stoppedevent', eventqueue)

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

    def ispending(self):
        pending = TaskState.PENDING == self.state
        return pending

    def isrunning(self):
        running = TaskState.RUNNING == self.state
        return running

    def isstopped(self):
        stopped = TaskState.STOPPED == self.state
        return stopped

    def isended(self):
        ended = TaskConclusion.ENDED == self.conclusion
        return ended

    def isfailed(self):
        failed = TaskConclusion.FAILED == self.conclusion
        return failed

    def iscanceled(self):
        canceled = TaskConclusion.CANCELED == self.conclusion
        return canceled

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
