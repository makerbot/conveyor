# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/stoppable.py
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

import gc
import threading
import weakref


class StoppableInterface(object):
    """ Class defines the interface to a stoppable object
    these objects require a '.stop() and .run() functions
    """
    def __init__(self):
        stoppablemanager = StoppableManager.getinstance()
        stoppablemanager._addstoppable(self)

    def stop(self):
        raise NotImplementedError

    def run(self):
        raise NotImplementedError


class StoppableThread(threading.Thread, StoppableInterface):
    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)
        StoppableInterface.__init__(self)


class StoppableManager(object):
    _instance = None

    @staticmethod
    def getinstance():
        if None is StoppableManager._instance:
            StoppableManager._instance = StoppableManager()
        return StoppableManager._instance

    @staticmethod
    def stopall():
        stoppablemanager = StoppableManager.getinstance()
        stoppablemanager._stopall()

    def __init__(self):
        self._reset()

    def _makeref(self, object):
        def callback(ref):
            self._stoppables.remove(ref)
        ref = weakref.ref(object, callback)
        return ref

    def _filter(self, ref):
        stoppable = ref()
        result = None is not stoppable
        return result

    def _reset(self):
        self._stoppables = []

    def _addstoppable(self, stoppable):
        ref = self._makeref(stoppable)
        self._stoppables.append(ref)
        self._stoppables = filter(self._filter, self._stoppables)

    def _removestoppable(self, stoppable):
        ref = self._makeref(stoppable)
        try:
            self._stoppables.remove(ref)
        except ValueError:
            pass
        self._stoppables = filter(self._filter, self._stoppables)

    def _stopall(self):
        for ref in self._stoppables:
            stoppable = ref()
            if None is not stoppable:
                stoppable.stop()
