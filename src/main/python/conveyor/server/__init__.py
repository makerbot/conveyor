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
import sets

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import conveyor
import conveyor.jsonrpc
import conveyor.main
import conveyor.recipe
import conveyor.main

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
        if self._parsedargs.nofork or (not has_daemon):
            code = self._run_server()
        else:
            files_preserve = list(conveyor.log.getfiles())
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

class ServerMainTestCase(unittest.TestCase):
    pass


class _ClientThread(threading.Thread):
    @classmethod
    def create(cls, config, server, fp, id):
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
        self._printers_seen = [] 
        self._printers_queried = [] 
        self._printers_open = []


    #@exportdFuction('hello')
    def _hello(self, *args, **kwargs):
        self._log.debug('args=%r, kwargs=%r', args, kwargs)
        return 'world'
 

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

    
    #@exportedFunction('printer_query')
    def _printer_query(self,*args,**kwargs):
        """ Queries a printer for it's name, extruder count, uuid, and other EEPROM info."""
        if  'port' in kwargs:
            s3gBot = makerbot_driver.s3g.from_filename(kwargs['port'])
            if s3gBot :
                version = s3gBot.get_version()
                if(version >= 506):   #newer that 5.6 has 'advanced' version
                    version = s3gBot.get_advanced_version()
                name, uuid = s3gBot.get_advanced_name()
                toolheads = s3gBot.get_toolhead_count()
                verified = s3gBot.get_verified_status() 
                s3gBot.close()
                info = { 'port':'port', 'class':ptr['class'],
                    'version':version, 'uuid':uuid,
                    'extruders':toolheads, 'displayname':name,
                    'verified':verified 
                } 
                return info
            else:
               self._log.error("no bot at port %s", port)
        return None      

    #@exportedFunction('printer_scan')
    def _printer_scan(self,*args,**kwargs):
        """ uses pyserial-mb to scan for ports, and return a list of ports
        that have a machine matching the specifed VID/PID pair
        """
        result = None
        self._log.debug("doing a printer scan via conveyor service")
        vid, pid = None, None
        #annoying case handling
        if 'vid' in kwargs:
            if kwargs['vid'] == None:           pass
            elif isinstance(kwargs['vid'],int): vid = kwargs['vid']
            else:                               vid = int(kwargs['vid'],16)
        if 'pid' in kwargs:
            if kwargs['pid'] == None:           pass
            elif isinstance(kwargs['pid'],int): pid = kwargs['pid']
            else:                               pid = int(kwargs['pid'],16)
        try:
            import serial.tools.list_ports as lp
            ports = lp.list_ports_by_vid_pid(vid,pid)
            result = list(ports)
            for r in result:
                self._printers_seen.append(r)
            if result == None:
              self._log.error("port= None")
            else:
              for port in result:
                self._log.error("port= %r", port)
        except Exception as e:
            self._log.exception('unhandled exception')
            result = None
        return result
   

    #@exportedFunction('dir')
    def _dir(self, *args, **kwards):
        result = {}
        self._log.debug("doing a services dir conveyor service")
        def dir_callback(task):
            self._log.debug("doing a dir to task")  
        if(self._jsonrpc):
            result = self._jsonrpc.dict_all_methods()
        result['__version__'] = conveyor.__version__
        return result



    #@exportedFunction('print')
    def _print(self, thing, preprocessor, skip_start_end, endpoint=None):
        self._log.debug('thing=%r, preprocessor=%r, skip_start_end=%r', thing, preprocessor, skip_start_end)
        def runningcallback(task):
            self._log.info(
                'printing: %s (job %d)', thing, self._id)
        def heartbeatcallback(task):
            self._log.info('%r', task.progress)
        recipemanager = conveyor.recipe.RecipeManager(self._config)
        recipe = recipemanager.getrecipe(thing, preprocessor)
        task = recipe.print(skip_start_end,endpoint)
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

    def _load_services(self):
        self._jsonrpc.addmethod('hello', self._hello, "no params. Returns 'world'")
        self._jsonrpc.addmethod('print', self._print, 
			": takes (thing-filename, preprocessor, skip_start_end_bool, [endpoint)" )
        self._jsonrpc.addmethod('printtofile', self._printtofile,
			": takes (inputfile, outputfile) pair" )
        self._jsonrpc.addmethod('slice', self._slice,
			": takes (inputfile, outputfile) pair" )
        self._jsonrpc.addmethod('printer_scan',self._printer_scan,
			": takes {'vid':int(VID), 'pid':int(PID) } for USB target id's")
        self._jsonrpc.addmethod('printer_query',self._printer_query,
			": takes {'port':string(port) } printer to query for data.")
		self._jsonrpc.addmethod('dir',self._dir, "takes no params ") 
    def run(self):
        # add our available functions to the json methods list
        self._load_services()
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
