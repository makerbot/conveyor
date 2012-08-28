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
import os.path
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

    def printeradded(self, params):
        self._jsonrpc.notify('printeradded', params)

    def printerchanged(self, params):
        self._jsonrpc.notify('printerchanged', params)

    def printerremoved(self, params):
        self._jsonrpc.notify('printerremoved', params)

    def _stoppedcallback(self, job):
        def callback(task):
            if conveyor.task.TaskConclusion.ENDED == task.conclusion:
                self._log.info('job %d ended', job)
            elif conveyor.task.TaskConclusion.FAILED == task.conclusion:
                self._log.info('job %d failed', job)
            elif conveyor.task.TaskConclusion.CANCELED == task.conclusion:
                self._log.info('job %d canceled', job)
            else:
                raise ValueError(task.conclusion)
            params = [job, conveyor.task.TaskState.STOPPED, task.conclusion]
            self._jsonrpc.notify('notify', params)
        return callback

    @export('hello')
    def _hello(self, *args, **kwargs):
        self._log.debug('args=%r, kwargs=%r', args, kwargs)
        return 'world'

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
        if self._jsonrpc:
            result = self._jsonrpc.dict_all_methods()
        result['__version__'] = conveyor.__version__
        return result

    def _findprinter(self, name):
        printerthread = None
        if None is name:
            printerthread = self._findprinter_default()
            if None is printerthread:
                raise Exception('no printer connected') # TODO: custom exception
        else:
            printerthread = self._server.findprinter_printerid(name)
            if None is printerthread:
                printerthread = self._server.findprinter_portname(name)
            if None is printerthread:
                raise Exception('unknown printer: %s' % (name,)) # TODO: custom exception
        return printerthread

    def _findprinter_default(self):
        printerthreads = self._server.getprinterthreads()
        keys = printerthreads.keys()
        if 0 == len(keys):
            printerthread = None
        else:
            key = keys[0]
            printerthread = self._server._printerthreads[key]
        return printerthread

    def _findprofile(self, name):
        if None is name:
            name = self._config['common']['profile']
        profile = makerbot_driver.Profile(name, self._config['common']['profiledir'])
        return profile

    def _getbuildname(self, path):
        root, ext = os.path.splitext(path)
        buildname = os.path.basename(root)
        return buildname

    @export('print')
    def _print(
        self, printername, inputpath, preprocessor, skip_start_end, archive_lvl,
        archive_dir, slicer_settings, material):
            self._log.debug(
                'printername=%r, inputpath=%r, preprocessor=%r, skip_start_end=%r, archive_lvl=%r, archive_dir=%r, slicer_settings=%r, material=%r',
                printername, inputpath, preprocessor, skip_start_end,
                archive_lvl, archive_dir, slicer_settings, material)
            recipemanager = conveyor.recipe.RecipeManager(
                self._server, self._config)
            build_name = self._getbuildname(inputpath)
            job = self._server.createjob(
                build_name, inputpath, self._config, preprocessor,
                skip_start_end, False)
            recipe = recipemanager.getrecipe(job)
            printerthread = self._findprinter(printername)
            process = recipe.print(printerthread)
            def runningcallback(task):
                self._log.info(
                    'printing: %s (job %d)', inputpath, job.id)
            process.runningevent.attach(runningcallback)
            def heartbeatcallback(task):
                self._log.info('progress: (job %d) %r', job.id, task.progress)
            process.heartbeatevent.attach(heartbeatcallback)
            process.stoppedevent.attach(self._stoppedcallback)
            process.start()
            dct = job.todict()
            return dct

    @export('printtofile')
    def _printtofile(
        self, profilename, inputpath, outputpath, preprocessor, skip_start_end,
        archive_lvl, archive_dir, slicer_settings, material):
            self._log.debug(
                'profilename=%r, inputpath=%r, outputpath=%r, preprocessor=%r, skip_start_end=%r, printer=%r, archive_lvl=%r, archive_dir=%r, slicer_settings=%r, material=%r',
                profilename, inputpath, outputpath, preprocessor,
                skip_start_end, archive_lvl, archive_dir, slicer_settings,
                material)
            recipemanager = conveyor.recipe.RecipeManager(
                self._server, self._config)
            build_name = self._getbuildname(inputpath)
            job = self._server.createjob(
                build_name, inputpath, self._config, preprocessor,
                skip_start_end, False)
            recipe = recipemanager.getrecipe(job)
            profile = self._findprofile(profilename)
            process = recipe.printtofile(profile, outputpath)
            def runningcallback(task):
                self._log.info(
                    'printing to file: %s -> %s (job %d)', inputpath,
                    outputpath, job.id)
            process.runningevent.attach(runningcallback)
            def heartbeatcallback(task):
                self._log.info('progress: (job %d) %r', job.id, task.progress)
            process.heartbeatevent.attach(heartbeatcallback)
            process.stoppedevent.attach(self._stoppedcallback)
            process.start()
            dct = job.todict()
            return dct

    @export('slice')
    def _slice(
        self, profilename, inputpath, outputpath, preprocessor,
        with_start_end, slicer_settings, material):
            self._log.debug(
                'profilename=%r, inputpath=%r, outputpath=%r, preprocessor=%r, with_start_end=%r, slicer_settings=%r, material=%r',
                profilename, inputpath, outputpath, preprocessor,
                with_start_end, slicer_settings, material)
            recipemanager = conveyor.recipe.RecipeManager(
                self._server, self._config)
            build_name = self._getbuildname(inputpath)
            job = self._server.createjob(
                build_name, inputpath, self._config, preprocessor, False,
                with_start_end)
            recipe = recipemanager.getrecipe(job)
            profile = self._findprofile(profilename)
            process = recipe.slice(profile, outputpath)
            def runningcallback(task):
                self._log.info(
                    'slicing: %s -> %s (job %d)', inputpath, outputpath,
                    job.id)
            process.runningevent.attach(runningcallback)
            def heartbeatcallback(task):
                self._log.info('progress: (job %d) %r', job.id, task.progress)
            process.heartbeatevent.attach(heartbeatcallback)
            process.stoppedevent.attach(self._stoppedcallback)
            process.start()
            dct = job.todict()
            return dct

    @export('cancel')
    def _cancel(self, id):
        self._server.canceljob(id)

    @export('getprinters')
    def _getprinters(self):
        result = []
        printerthreads = self._server.getprinterthreads()
        for portname, printerthread in printerthreads.items():
            profile = printerthread.getprofile()
            printerid = printerthread.getprinterid()
            data = {
                'displayName': profile.values['type'],
                'uniqueName': printerid,
                'printerType': profile.values['type'],
                'canPrint': True,
                'canPrintToFile': True,
                'hasHeatedPlatform': len(profile.values['heated_platforms']) != 0,
                'numberOfToolheads': len(profile.values['tools']),
                'connectionStatus': 'connected',
                'temperature': None # TODO
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
                self._log.debug('queue is empty')
                func = None
            else:
                self._log.debug('queue is not empty')
                func = self._queue.pop()
        if None is not func:
            try:
                self._log.debug('running func')
                func()
                self._log.debug('func ended')
            except:
                self._log.exception('unhandled exception')

    def appendfunc(self, func):
        with self._condition:
            self._queue.appendleft(func)
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

class Server(object):
    def __init__(self, config, sock):
        self._clientthreads = []
        self._config = config
        self._detectorthread = None
        self._idcounter = 0
        self._jobcounter = 0
        self._lock = threading.Lock()
        self._log = logging.getLogger(self.__class__.__name__)
        self._queue = Queue()
        self._sock = sock
        self._printerthreads = {}

    def _invokeclients(self, methodname, *args, **kwargs):
        with self._lock:
            clientthreads = self._clientthreads[:]
        for clientthread in clientthreads:
            try:
                method = getattr(clientthread, methodname)
                method(*args, **kwargs)
            except:
                self._log.exception('unhandled exception')

    def getprinterthreads(self):
        with self._lock:
            printerthreads = self._printerthreads.copy()
        return printerthreads

    def findprinter_printerid(self, name):
        with self._lock:
            for printerthread in self._printerthreads.values():
                if name == printerthread.getprinterid():
                    return printerthread
            return None

    def findprinter_portname(self, name):
        with self._lock:
            for printerthread in self._printerthreads.values():
                if name == printerthread.getportname():
                    return printerthread
            return None

    def createjob(
        self, build_name, path, config, preprocessor, skip_start_end,
        with_start_end):
            with self._lock:
                id = self._jobcounter
                self._jobcounter += 1
            job = conveyor.job.Job(
                id, build_name, path, config, preprocessor, skip_start_end,
                with_start_end)
            return job

    def appendclientthread(self, clientthread):
        with self._lock:
            self._clientthreads.append(clientthread)

    def removeclientthread(self, clientthread):
        with self._lock:
            self._clientthreads.remove(clientthread)

    def appendprinter(self, portname, printerthread):
        self._log.info('printer connected: %s', portname)
        with self._lock:
            self._printerthreads[portname] = printerthread
        printerid = printerthread.getprinterid()
        params = {'id': printerid}
        self._invokeclients('printeradded', params)

    def changeprinter(self, portname, temperature):
        printerthread = self.findprinter_portname(portname)
        printerid = printerthread.getprinterid()
        profile = printerthread.getprofile()
        params = {
            'displayName': profile.values['type'],
            'uniqueName': printerid,
            'printerType': profile.values['type'],
            'canPrint': True,
            'canPrintToFile': True,
            'hasHeatedPlatform': len(profile.values['heated_platforms']) != 0,
            'numberOfToolheads': len(profile.values['tools']),
            'connectionStatus': 'connected',
            'temperature': temperature
        }
        self._invokeclients('printerchanged', params)

    def evictprinter(self, portname, fp):
        self._log.info('printer evicted due to error: %s', portname)
        self._detectorthread.blacklist(portname)
        self.removeprinter(portname)
        fp.close()

    def removeprinter(self, portname):
        self._log.info('printer disconnected: %s', portname)
        with self._lock:
            if portname in self._printerthreads:
                printerthread = self._printerthreads.pop(portname)
            else:
                printerthread = None
        if None is printerthread:
            self._log.debug(
                'disconnected unconnected printer: %s', portname)
        else:
            printerthread.stop()
            printerid = printerthread.getprinterid()
            params = {'id': printerid}
            self._invokeclients('printerremoved', params)

    def printtofile(
        self, profile, buildname, inputpath, outputpath, skip_start_end,
        task):
            def func():
                driver = conveyor.printer.s3g.S3gDriver()
                driver.printtofile(
                    outputpath, profile, buildname, inputpath, skip_start_end,
                    task)
            self._queue.appendfunc(func)

    def _getslicer(self, slicername):
        if 'miraclegrue' == slicername:
            configuration = conveyor.toolpath.miraclegrue.MiracleGrueConfiguration()
            configuration.miraclegruepath = self._config['miraclegrue']['path']
            configuration.miracleconfigpath = self._config['miraclegrue']['config']
            slicer = conveyor.toolpath.miraclegrue.MiracleGrueToolpath(configuration)
        elif 'skeinforge' == slicername:
            configuration = conveyor.toolpath.skeinforge.SkeinforgeConfiguration()
            configuration.skeinforgepath = self._config['skeinforge']['path']
            configuration.profile = self._config['skeinforge']['profile']
            slicer = conveyor.toolpath.skeinforge.SkeinforgeToolpath(configuration)
        else:
            raise ValueError(slicer)
        return slicer

    def slice(self, profile, inputpath, outputpath, with_start_end, task):
        def func():
            slicername = self._config['common']['slicer']
            slicer = self._getslicer(slicername)
            slicer.slice(profile, inputpath, outputpath, with_start_end, task)
        self._queue.appendfunc(func)

    def run(self):
        self._detectorthread = conveyor.printer.s3g.S3gDetectorThread(
            self._config, self)
        self._detectorthread.start()
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
                    with self._lock:
                        id = self._idcounter
                        self._idcounter += 1
                    clientthread = _ClientThread.create(
                        self._config, self, fp, id)
                    clientthread.start()
        finally:
            self._queue.stop()
            taskqueuethread.join(1)
        return 0
