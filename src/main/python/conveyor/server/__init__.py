# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/server/__init__.py
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
import errno
import logging
import os
import sys
import threading

import conveyor.jsonrpc
import conveyor.main
import conveyor.recipe

class ServerMain(conveyor.main.AbstractMain):
    def __init__(self):
        conveyor.main.AbstractMain.__init__(self, 'conveyord', 'server')

    def _initparser_common(self, parser):
        conveyor.main.AbstractMain._initparser_common(self, parser)
        parser.add_argument(
            '--nofork', action='store_true', default=False,
            help='do not fork nor detach from the terminal')

    def _initsubparsers(self):
        return None

    def _run(self):
        has_daemon = False
        code = -17 #failed to run err
        try:
            import daemon
            import daemon.pidfile
            import lockfile
            has_daemon = True
        except ImportError:
            self._log.debug('handled exception', exc_info=True)
		if (self._parsedargs and self._parsedargs.nofork) or (not has_daemon):
            code = self._run_server()
        else:
            files_preserve = list(conveyor._log.getfiles())
            pidfile = self._config['server']['pidfile']
            dct = {
                'files_preserve': files_preserve,
                'pidfile': daemon.pidfile.TimeoutPIDLockFile(pidfile, 0)
            }
            if not self._config['server']['chdir']:
                dct['working_directory'] = os.getcwd()
            context = daemon.DaemonContext(**dct)
            def terminate(signal_number, stack_frame):
                # The daemon module's implementation of terminate()
                # raises a SystemExit with a string message instead of
                # an exit code. This monkey patch fixes it.
                sys.exit(0)
            context.terminate = terminate # monkey patch!
            try:
                with context:
                    code = self._run_server()
            except lockfile.NotLocked as e:
                self._log.critical('deamon file is not locked: %r',e);
                code = 0 #assume we closed the thread ...
        return code

    def _run_server(self):
        self._initeventqueue()
        with self._address:
            self._socket = self._address.listen()
            with self._advertise_deamon() as lockfile:
                try:
                    server = conveyor.server.Server(self._config, self._socket)
                    code = server.run()
                    return code
                finally:
                    os.unlink(lockfile.name) 
        return 0

    def _advertise_deamon(self):
        """
        Advertise that the deamon is available
        by writing a conveyord.lock file to advertise that conveyord is available
        Existance of that file indicates that the conveyor service is up and running
        @return a file object pointing to the lockfile
        """
        if not self._config['common']['daemon_lockfile']:
            return None
        lock_filename = self._config['common']['daemon_lockfile']
        return open(lock_filename, 'w+')


class _ClientThread(threading.Thread):
	

    @classmethod
    def factory(cls, config, server, fp, id):
        jsonrpc = conveyor.jsonrpc.JsonRpc(fp, fp)
        clientthread = _ClientThread(config, server, jsonrpc, id)
        return clientthread

    def __init__(self, config, server, jsonrpc, id):
        threading.Thread.__init__(self)
        self._config = config
        self._log = logging.getLogger(self.__class__.__name__)
        self._server = server
        self._id = id
        self._jsonrpc = jsonrpc

    def _hello(self, *args, **kwargs):
        self._log.debug('args=%r, kwargs=%r', args, kwargs)
        return None

    def _stoppedcallback(self, task):
        if conveyor.task.TaskConclusion.ENDED == task.conclusion:
            self._log.info('job %d ended', self._id)
        elif conveyor.task.TaskConclusion.FAILED == task.conclusion:
            self._log.info('job %d failed', self._id)
        elif conveyor.task.TaskConclusion.CANCELED == task.conclusion:
            self._log.info('job %d canceled', self._id)
        else:
            raise ValueError(task.conclusion)
        params = [self._id, conveyor.task.TaskState.STOPPED, task.conclusion]
        self._jsonrpc.notify('notify', params)

    def _print(self, thing, preprocessor, skip_start_end):
        self._log.debug('thing=%r, preprocessor=%r, skip_start_end=%r', thing, preprocessor, skip_start_end)
        def runningcallback(task):
            self._log.info(
                'printing: %s (job %d)', thing, self._id)
        def heartbeatcallback(task):
            self._log.info('%r', task.progress)
        recipemanager = conveyor.recipe.RecipeManager(self._config)
        recipe = recipemanager.getrecipe(thing, preprocessor)
        task = recipe.print(skip_start_end)
        task.runningevent.attach(runningcallback)
        task.heartbeatevent.attach(heartbeatcallback)
        task.stoppedevent.attach(self._stoppedcallback)
        self._server.appendtask(task)
        return None

    def _printtofile(self, thing, s3g, preprocessor, skip_start_end):
        self._log.debug('thing=%r, s3g=%r, preprocessor=%r, skip_start_end=%r', thing, s3g, preprocessor, skip_start_end)
        def runningcallback(task):
            self._log.info(
                'printing to file: %s -> %s (job %d)', thing, s3g, self._id)
        def heartbeatcallback(task):
            self._log.info('%r', task.progress)
        recipemanager = conveyor.recipe.RecipeManager(self._config)
        recipe = recipemanager.getrecipe(thing, preprocessor)
        task = recipe.printtofile(s3g, skip_start_end)
        task.runningevent.attach(runningcallback)
        task.heartbeatevent.attach(heartbeatcallback)
        task.stoppedevent.attach(self._stoppedcallback)
        self._server.appendtask(task)
        return None

    def _slice(self, thing, gcode, preprocessor, with_start_end):
        self._log.debug('thing=%r, gcode=%r', thing, gcode)
        def runningcallback(task):
            self._log.info(
                'slicing: %s -> %s (job %d)', thing, gcode, self._id)
        recipemanager = conveyor.recipe.RecipeManager(self._config)
        recipe = recipemanager.getrecipe(thing, preprocessor)
        task = recipe.slice(gcode, with_start_end)
        task.runningevent.attach(runningcallback)
        task.stoppedevent.attach(self._stoppedcallback)
        self._server.appendtask(task)
        return None

    def run(self):
        self._jsonrpc.addmethod('hello', self._hello)
        self._jsonrpc.addmethod('print', self._print)
        self._jsonrpc.addmethod('printtofile', self._printtofile)
        self._jsonrpc.addmethod('slice', self._slice)
        self._server.appendclientthread(self)
        try:
            self._jsonrpc.run()
        finally:
            self._server.removeclientthread(self)

class Queue(object):
    def __init__(self):
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)
        self._log = logging.getLogger(self.__class__.__name__)
        self._queue = collections.deque()
        self._quit = False

    def _runiteration(self):
        with self._condition:
            if 0 == len(self._queue):
                self._log.debug('waiting')
                self._condition.wait()
                self._log.debug('resumed')
            if 0 == len(self._queue):
                task = None
            else:
                task = self._queue.pop()
        if None is not task:
            tasklock = threading.Lock()
            taskcondition = threading.Condition(tasklock)
            def stoppedcallback(unused):
                with taskcondition:
                    taskcondition.notify_all()
            task.stoppedevent.attach(stoppedcallback)
            task.start()
            with taskcondition:
                taskcondition.wait()

    def appendtask(self, task):
        with self._condition:
            self._queue.appendleft(task)
            self._condition.notify_all()

    def run(self):
        self._log.debug('starting')
        self._quit = False
        while not self._quit:
            self._runiteration()
        self._log.debug('ending')

    def quit(self):
        with self._condition:
            self._quit = True
            self._condition.notify_all()

class Server(object):
    def __init__(self, config, sock):
        self._clientthreads = []
        self._config = config
        self._idcounter = 0
        self._lock = threading.Lock()
        self._queue = Queue()
        self._sock = sock

    def appendclientthread(self, clientthread):
        with self._lock:
            self._clientthreads.append(clientthread)

    def removeclientthread(self, clientthread):
        with self._lock:
            self._clientthreads.remove(clientthread)

    def appendtask(self, task):
        self._queue.appendtask(task)

    def run(self):
        taskqueuethread = threading.Thread(target=self._queue.run, name='taskqueue')
        taskqueuethread.start()
        try:
            while True:
                try:
                    conn, addr = self._sock.accept()
                except IOError as e:
                    if errno.EINTR == e.args[0]:
                        continue
                    else:
                        raise
                else:
                    fp = conveyor.jsonrpc.socketadapter(conn)
                    id = self._idcounter
                    self._idcounter += 1
                    clientthread = _ClientThread.create(self._config, self, fp, id)
                    clientthread.start()
        finally:
            self._queue.quit()
            taskqueuethread.join(5)
        return 0

