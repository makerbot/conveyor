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

import threading


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


