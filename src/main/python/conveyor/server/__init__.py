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
import makerbot_driver
import os
import sys
import threading

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import conveyor.jsonrpc
import conveyor.main
import conveyor.printer.s3g
import conveyor.recipe
import conveyor.stoppable

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

def export(name):
    def decorator(func):
        return func
    return decorator

class _ClientThread(conveyor.stoppable.StoppableThread):
    @classmethod
    def create(cls, config, server, fp, id):
        jsonrpc = conveyor.jsonrpc.JsonRpc(fp, fp)
        clientthread = _ClientThread(config, server, jsonrpc, id)
        return clientthread

    def __init__(self, config, server, jsonrpc, id):
        conveyor.stoppable.StoppableThread.__init__(self)
        self._config = config
        self._log = logging.getLogger(self.__class__.__name__)
        self._server = server
        self._id = id
        self._jsonrpc = jsonrpc
        self._printers_seen = []

    def printeradded(self, id, printer):
        params = {'id': id}
        self._jsonrpc.notify('printeradded', params)

    def printerremoved(self, id, printer):
        params = {'id': id}
        self._jsonrpc.notify('printerremoved', params)

    @export('hello')
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

    # TODO: broken, attempts to open a port that is already open
    @export('printer_query')
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

    @export('printer_scan')
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

    @export('dir')
    def _dir(self, *args, **kwargs):
        result = {}
        self._log.debug("doing a services dir conveyor service")
        if(self._jsonrpc):
            result = self._jsonrpc.dict_all_methods()
        result['__version__'] = conveyor.__version__
        return result

    def _findprinter(self, printername):
        if None is not printername:
            if printername not in self._server._printers:
                raise Exception('unknown printer: %s' % (printername,))
            else:
                printer = self._server._printers[printername]
        else:
            keys = self._server._printers.keys()
            if 0 == len(keys):
                # TODO: this is awful
                profile = makerbot_driver.Profile('ReplicatorSingle')
                printer = conveyor.printer.s3g.S3gPrinter(None, profile)
            else:
                printername = keys[0]
                printer = self._server._printers[printername]
        return printer

    @export('print')
    def _print(
        self, printername, inputpath, preprocessor, skip_start_end, archive_lvl,
        archive_dir):
            self._log.debug(
                'printername=%r, inputpath=%r, preprocessor=%r, skip_start_end=%r, archive_lvl=%r, archive_dir=%r',
                printername, inputpath, preprocessor, skip_start_end,
                archive_lvl, archive_dir)
            def runningcallback(task):
                self._log.info(
                    'printing: %s (job %d)', inputpath, self._id)
            def heartbeatcallback(task):
                self._log.info('%r', task.progress)
            recipemanager = conveyor.recipe.RecipeManager(self._config)
            recipe = recipemanager.getrecipe(inputpath, preprocessor)
            printer = self._findprinter(printername)
            if None is printer:
                raise Exception('printer not connected') # TODO: this is also awful
            task = recipe.print(skip_start_end, printer)
            task.runningevent.attach(runningcallback)
            task.heartbeatevent.attach(heartbeatcallback)
            task.stoppedevent.attach(self._stoppedcallback)
            self._server.appendtask(task)
            return None

    @export('printtofile')
    def _printtofile(
        self, printername, inputpath, outputpath, preprocessor, skip_start_end,
        archive_lvl, archive_dir):
            self._log.debug(
                'printername=%r, inputpath=%r, outputpath=%r, preprocessor=%r, skip_start_end=%r, printer=%r, archive_lvl=%r, archive_dir=%r',
                printername, inputpath, outputpath, preprocessor,
                skip_start_end, archive_lvl, archive_dir)
            def runningcallback(task):
                self._log.info(
                    'printing to file: %s -> %s (job %d)', inputpath,
                    outputpath, self._id)
            def heartbeatcallback(task):
                self._log.info('%r', task.progress)
            recipemanager = conveyor.recipe.RecipeManager(self._config)
            recipe = recipemanager.getrecipe(inputpath, preprocessor)
            printer = self._findprinter(printername)
            task = recipe.printtofile(outputpath, skip_start_end, printer)
            task.runningevent.attach(runningcallback)
            task.heartbeatevent.attach(heartbeatcallback)
            task.stoppedevent.attach(self._stoppedcallback)
            self._server.appendtask(task)
            return None

    @export('slice')
    def _slice(
        self, printername, inputpath, outputpath, preprocessor=None, with_start_end=False):
            self._log.debug(
                'inputpath=%r, outputpath=%r, preprocessor=%r, with_start_end=%r',
                inputpath, outputpath, preprocessor, with_start_end)
            def runningcallback(task):
                self._log.info(
                    'slicing: %s -> %s (job %d)', thing, gcode, self._id)
            recipemanager = conveyor.recipe.RecipeManager(self._config)
            recipe = recipemanager.getrecipe(inputpath, preprocessor)
            printer = self._findprinter(printername)
            task = recipe.slice(outputpath, with_start_end, printer)
            task.runningevent.attach(runningcallback)
            task.stoppedevent.attach(self._stoppedcallback)
            self._server.appendtask(task)
            return None

    @export('cancel')
    def _cancel(self,*args, **kwargs):
        self._log.debug('ABORT ABORT ABORT! (conveyord print cancel)' )
        self._log.error('server print cancel not yet implemented')
        return None

    @export('getprinters')
    def _getprinters(self):
        result = []
        for id, printer in self._server._printers.items():
            data = {
                'displayName': printer._profile.values['type'],
                'uniqueName': printer._device,
                'printerType': printer._profile.values['type'],
                'canPrint': True,
                'canPrintToFile': True,
                'hasHeatedPlatform': len(
                    printer._profile.values['heated_platforms']) != 0,
                'numberOfToolheads': len(printer._profile.values['tools']),
                'connectionStatus': 'connected'
            }
            result.append(data)
        return result

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
        self._jsonrpc.addmethod('cancel',self._cancel, 
                "takes {'port':string(port) 'job_id':jobid}"
                        "if Job is None, cancels by port. If port is None, cancels first bot")
        self._jsonrpc.addmethod('getprinters', self._getprinters)

    def run(self):
        # add our available functions to the json methods list
        self._load_services()
        self._server.appendclientthread(self)
        try:
            self._jsonrpc.run()
        finally:
            self._server.removeclientthread(self)

    def stop(self):
        self._jsonrpc.stop()

class Queue(object):
    def __init__(self):
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)
        self._log = logging.getLogger(self.__class__.__name__)
        self._queue = collections.deque()
        self._stop = False

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
        self._stop = False
        while not self._stop:
            self._runiteration()
        self._log.debug('ending')

    def stop(self):
        with self._condition:
            self._stop = True
            self._condition.notify_all()

class _TaskQueueThread(threading.Thread, conveyor.stoppable.Stoppable):
    def __init__(self, queue):
        threading.Thread.__init__(self, name='taskqueue')
        conveyor.stoppable.Stoppable.__init__(self)
        self._log = logging.getLogger(self.__class__.__name__)
        self._queue = queue

    def run(self):
        try:
            self._queue.run()
        except:
            self._log.error('internal error', exc_info=True)

    def stop(self):
        self._queue.stop()

class _PrinterThread(threading.Thread, conveyor.stoppable.Stoppable):
    pass

class Server(object):
    def __init__(self, config, sock):
        self._clientthreads = []
        self._config = config
        self._idcounter = 0
        self._lock = threading.Lock()
        self._log = logging.getLogger(self.__class__.__name__)
        self._queue = Queue()
        self._sock = sock
        self._printers = {}

    def appendclientthread(self, clientthread):
        with self._lock:
            self._clientthreads.append(clientthread)

    def removeclientthread(self, clientthread):
        with self._lock:
            self._clientthreads.remove(clientthread)

    def appendtask(self, task):
        with self._lock:
            self._queue.appendtask(task)

    def appendprinter(self, id, printer):
        self._log.info('printer connected: %s', id)
        with self._lock:
            self._printers[id] = printer
            clientthreads = self._clientthreads[:]
        for clientthread in clientthreads:
            clientthread.printeradded(id, printer)

    def removeprinter(self, id):
        self._log.info('printer disconnected: %s', id)
        with self._lock:
            printer = self._printers.pop(id)
            # TODO: printer.stop()
            clientthreads = self._clientthreads[:]
        for clientthread in clientthreads:
            clientthread.printerremoved(id, printer)

    def run(self):
        detectorthread = conveyor.printer.s3g.S3gDetectorThread(
            self._config, self)
        detectorthread.start()
        taskqueuethread = _TaskQueueThread(self._queue)
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
                    clientthread = _ClientThread.create(
                        self._config, self, fp, id)
                    clientthread.start()
        finally:
            self._queue.stop()
            taskqueuethread.join(5)
        return 0
