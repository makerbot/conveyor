# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/toolpath/miraclegrue.py
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

from decimal import *

import logging
import os
import subprocess
import sys
import threading

import conveyor.event
import conveyor.task

# TODO: this is also in skeinforge.py
_CONVEYORDIR = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), '../../../../../')

class MiracleGrueConfiguration(object):
    def __init__(self):
        self.miraclegruepath = None
        self.miracleconfigpath = None

class MiracleGrueToolpath(object):
    def __init__(self):
        self._log = logging.getLogger(self.__class__.__name__)

    def generate(self, stlpath, gcodepath, configuration=None):
        if None is configuration:
            configuration = MiracleGrueConfiguration()
        def runningcallback(task):
            try:
                arguments = list(self._getarguments(
                    configuration, stlpath, gcodepath))
                print('arguments:')
                print(arguments)
                popen = subprocess.Popen(arguments)
                code = popen.wait()
                if 0 != code:
                    raise Exception(code)
            except Exception as e:
                self._log.exception('unhandled exception')
                task.fail(e)
            else:
                task.end(None)
        task = conveyor.task.Task()
        task.runningevent.attach(runningcallback)
        return task

    def _getarguments(self, configuration, stlpath, gcodepath):
        for method in (
            self._getarguments_executable,
            self._getarguments_miraclegrue,
            ):
                for iterable in method(configuration, stlpath, gcodepath):
                    for value in iterable:
                        yield value

    def _getarguments_executable(self, configuration, stlpath, gcodepath):
        path = configuration.miraclegruepath
        if None is path:
            path = os.path.abspath(os.path.join(
                _CONVEYORDIR, 'submodule/Miracle-Grue/bin/miracle_grue'))
        yield (path,)

    def _getarguments_miraclegrue(self, configuration, stlpath, gcodepath):
        configpath = configuration.miraclegruepath
        if None is configpath:
            configpath = os.path.abspath(os.path.join(
                _CONVEYORDIR, 'submodule/Miracle-Grue/miracle.config'))
        startpath = os.path.abspath(os.path.join(
            _CONVEYORDIR, 'submodule/Miracle-Grue/start_replicator_dual.gcode'))
        endpath = os.path.abspath(os.path.join(
            _CONVEYORDIR, 'submodule/Miracle-Grue/end_replicator_dual.gcode'))
        yield ('-c', configpath,)
        yield ('-s', startpath,)
        yield ('-e', endpath,)
        yield (stlpath,)

def _main(argv):
    if 3 != len(argv):
        print('usage: %s STL GCODE' % (argv[0],), file=sys.stderr)
        code = 1
    else:
        logging.basicConfig()
        eventqueue = conveyor.event.geteventqueue()
        thread = threading.Thread(target=eventqueue.run)
        thread.start()
        try:
            condition = threading.Condition()
            def stoppedcallback(task):
                with condition:
                    condition.notify_all()
            generator = MiracleGrueToolpath()
            task = generator.generate(argv[1], argv[2])
            task.stoppedevent.attach(stoppedcallback)
            task.start()
            with condition:
                condition.wait()
            if conveyor.task.TaskConclusion.ENDED == task.conclusion:
                code = 0
            else:
                code = 1
        finally:
            eventqueue.quit()
            thread.join(1)
    return code

if '__main__' == __name__:
    code = _main(sys.argv)
    if None is code:
        code = 0
    sys.exit(code)
