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

TaskState = conveyor.enum.enum('TaskState',  # enum name
        'PENDING', 'RUNNING', 'STOPPED')
# Valid State Transitions are limited. see docs/task.png for state diagram

TaskEvent = conveyor.enum.enum(
    'TaskEvent', 'START', 'HEARTBEAT', 'END', 'FAIL', 'CANCEL')
# Valid State Transitions are limited. see docs/task.png for state diagram

TaskConclusion = conveyor.enum.enum(
    'TaskConclusion', 'ENDED', 'FAILED', 'CANCELED')
# Valid State Transitions are limited. see docs/task.png for state diagram


class IllegalTransitionException(Exception):
    """ Exception for an illegal state change of Task state machine """
    def __init__(self, state, event):
        Exception.__init__(self, state, event)
        self.state = state
        self.event = event


class Task(object):
    """ Class for managing an ongoing task, including starting, stopping, 
        hearbeat (updates) and related tools.       
    """
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
        # import cStringIO as StringIO
        # import logging
        # import traceback
        # fp = StringIO.StringIO()
        # traceback.print_stack(file=fp)
        # log = logging.getLogger()
        # log.debug('state=%r, event=%r, date=%r, traceback=%r', self.state, event, data, fp.getvalue())
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
        """ Sets the Task in to active mode, where it can accept heartbeats,
        events, etc 
        """ 
        self._transition(TaskEvent.START, None)


    def heartbeat(self, progress):
        """Post a heartbeat update. 
        @param progress dict of { 'name':$PROGRESS, 'progress':$INT_PERCENT_PROGRESS }
        """
        self._transition(TaskEvent.HEARTBEAT, progress)

    def lazy_heartbeat(self, progress):
        if self.progress != progress:
            self.heartbeat(progress)

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


