# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/client/__init__.py
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

import logging
import os.path
import socket
import threading
import pdb
import tempfile
try:
    import unittest2 as unittest
except ImportError:
    import unittest

import conveyor.jsonrpc
import conveyor.main
import conveyor.task
import conveyor.main

class ClientMain(conveyor.main.AbstractMain):
    def __init__(self):
        conveyor.main.AbstractMain.__init__(self, 'conveyor', 'client')

    def _initparser_common(self, parser):
        conveyor.main.AbstractMain._initparser_common(self, parser)

    def _initsubparsers(self):
        subparsers = self._parser.add_subparsers(dest='command', title='Commands')
        for method in (
            self._initsubparser_print,
            self._initsubparser_printers,
            self._initsubparser_printtofile,
            self._initsubparser_slice,
			self._initsubparser_ping,
			self._initsubparser_scan,
			self._initsubparser_dir
            ):
                method(subparsers)

	def _initsubparser_ping(self,subparsers):
		parser = subparsers.add_parser('ping',help='ping a service or tool')
		parser.set_defaults(func=self._run_ping)
		self._initparser_common(parser)

	def _initsubparser_scan(self,subparsers):
		parser = subparsers.add_parser('scan',help='ping a service or tool')
		parser.set_defaults(func=self._run_scan)
		self._initparser_common(parser)
        pdb.set_trace()
        parser.add_argument('--vid', action='store', 
                            type=int, default = 0x23C1,
                            help='Limit printer scan by USB VendorId')
        parser.add_argument('--pid', action='store', 
                            type=int, default = None,
                            help='Limit printer scan by USB ProductId')

	def _initsubparser_dir(self,subparsers):
		parser = subparsers.add_parser('dir',help='ping a service or tool')
		parser.set_defaults(func=self._run_dir)
		self._initparser_common(parser)

    def _initsubparser_printers(self, subparsers):
        parser = subparsers.add_parser('printers', help='list connected printers')
        parser.set_defaults(func=self._run_printers)
        self._initparser_common(parser)
        parser.add_argument(
            '--json',
            action='store_true',
            default=False,
            help='print in JSON format')

    def _initsubparser_print(self, subparsers):
        parser = subparsers.add_parser('print', help='print an object')
        parser.set_defaults(func=self._run_print)
        self._initparser_common(parser)
        parser.add_argument(
            'thing', help='the path to the object file', metavar='PATH')
        parser.add_argument(
            '--skip-start-end', action='store_true', default=False,
            help='use start/end gcode provided by file')
        parser.add_argument('--preprocessor', dest='preprocessor',
            default=False, help='preprocessor to run on the gcode file')

    def _initsubparser_printtofile(self, subparsers):
        parser = subparsers.add_parser('printtofile', help='print an object to an .s3g file')
        parser.set_defaults(func=self._run_printtofile)
        self._initparser_common(parser)
        parser.add_argument(
            'thing', help='the path to the object file', metavar='PATH')
        parser.add_argument(
            's3g', help='the output path for the .s3g file', metavar='S3G')
        parser.add_argument(
            '--skip-start-end', action='store_true', default=False,
            help='use start/end gcode provided by file')
        parser.add_argument('--preprocessor', dest='preprocessor',
            default=False, help='preprocessor to run on the gcode file')

    def _initsubparser_slice(self, subparsers):
        parser = subparsers.add_parser('slice', help='slice an object into .gcode')
        parser.set_defaults(func=self._run_slice)
        self._initparser_common(parser)
        parser.add_argument('thing', help='the path to the object file', metavar='PATH')
        parser.add_argument(
            'gcode', help='the output path for the .gcode file',
            metavar='GCODE')
        parser.add_argument(
            '--with-start-end', action='store_true', default=False,
            help='append start and end gcode to .gcode file')
        parser.add_argument(
            '--preprocessor', dest='preprocessor', default=False,
            help='preprocessor to run on the gcode file')

    def _run(self):
        self._initeventqueue()
        try:
            self._socket = self._address.connect()
        except EnvironmentError as e:
            code = 1
            self._log.critical(
                'failed to open socket: %s: %s',
                self._config['common']['socket'], e.strerror, exc_info=True)
            if not self._has_daemon_lock():
              self._log.critical(
                'no server lock found. Verify conveyor service is running')
        else:
            code = self._parsedargs.func()
        return code

    def _run_print(self):
        params = [
            os.path.abspath(self._parsedargs.thing),
            self._parsedargs.preprocessor,
            self._parsedargs.skip_start_end]
        self._log.info('printing: %s', self._parsedargs.thing)
        code = self._run_client('print', params)
        return code

    def _run_ping(self):
		params = ['fail','sauce']
        code = self._run_client('ping',params) #from server/__init__.py
		return code	
  
    def _run_scan(self):
        pdb.set_trace()
		params = {"vid":self._parsedargs.vid, "pid":self._parsedargs.pid}
        code = self._run_client('printer_scan',params) #from server/__init__.py
		return code 
  
    def _run_dir(self):
		params = ['fail','sauce']
        code = self._run_client('dir',params) #from server/__init__.py
		return code
  

    def _run_printers(self):
        code = self.run_client('printer_scan',params)
        return code

    def _run_printtofile(self):
        params = [
            os.path.abspath(self._parsedargs.thing),
            os.path.abspath(self._parsedargs.s3g),
            self._parsedargs.preprocessor,
            self._parsedargs.skip_start_end]
        self._log.info(
            'printing to file: %s -> %s', self._parsedargs.thing,
            self._parsedargs.s3g)
        code = self._run_client('printtofile', params)
        return code

    def _run_slice(self):
        params = [
            os.path.abspath(self._parsedargs.thing),
            os.path.abspath(self._parsedargs.gcode),
            self._parsedargs.preprocessor,
            self._parsedargs.with_start_end]
        self._log.info(
            'slicing to file: %s -> %s', self._parsedargs.thing,
            self._parsedargs.gcode)
        code = self._run_client('slice', params)
        return code

    def _run_client(self, method, params):
        client = conveyor.client.Client.create(self._socket, method, params)
        code = client.run()
        return code

    def _has_daemon_lock(self):
        """ 
        Returns true of a conveyor service 'lock' file is found,
        indicating converyor daemon is running
        @param self
        @returns True if lockfile found, false otherwise
        """
        lock_filename = 'conveyord.lock'
        try: 
            lock_filename = self._config['common']['daemon_lockfile']
        except KeyError as e:
            self._log.critical("no config['common'][daemon_lockfile'] found")
        return os.path.isfile(lock_filename)

class _ClientMainTestCase(unittest.TestCase):
    pass

class Client(object):
    @classmethod
    def create(cls, sock, method, params):
        fp = conveyor.jsonrpc.socketadapter(sock)
        jsonrpc = conveyor.jsonrpc.JsonRpc(fp, fp)
        client = Client(sock, fp, jsonrpc, method, params)
        return client

    def __init__(self, sock, fp, jsonrpc, method, params, customcallback=None):
        """ Create a client object to throw a request to the server,
        and receive a reply. If no callback is specified, a generic callback
        that stores return values to a tmpfile is called when a reply is received. 
        """
        self._code = None
        self._fp = fp
        self._jsonrpc = jsonrpc
        self._log = logging.getLogger(self.__class__.__name__)
        self._method = method
        self._methodcallback = customcallback if customcallback else self.defaultcallback
        self._params = params
        self._sock = sock

    def _shutdown(self):
        self._fp.shutdown()

    def _notify(self, job, state, conclusion):
        self._log.debug('job=%r, state=%r, conclusion=%r', job, state, conclusion)
        if conveyor.task.TaskState.STOPPED == state:
            if conveyor.task.TaskConclusion.ENDED == conclusion:
                self._code = 0
            elif conveyor.task.TaskConclusion.FAILED == conclusion:
                self._log.error('job failed')
                self._code = 1
            elif conveyor.task.TaskConclusion.CANCELED == conclusion:
                self._log.warning('job canceled')
                self._code = 1
            else:
                raise ValueError(task.conclusion)
            self._shutdown()

    def _hellocallback(self, task):
        """ default callback to handle reply to a 'hello' event """
        callback = self._methodcallback
        self._log.debug('task=%r', task)
        task1 = self._jsonrpc.request(self._method, self._params, self._methodcallback)
        task1.start()

    def defaultcallback(self, task):
        self._log.debug('task=%r', task)
        pdb.set_trace()
        if conveyor.task.TaskState.STOPPED == task.state:
            if conveyor.task.TaskConclusion.ENDED == task.conclusion:
                if  task.result == None:
                    self._log.error('task success, result: None')
                else:
                    pdb.set_trace()
                    fh = tempfile.NamedTemporaryFile(suffix="result.txt",delete=False)
                    fh.write(str(task.result))
                    self._log.error('task success, results in: %s', str(fh.name))
                    fh.close()
                self._code = 0
                self._shutdown()
            elif conveyor.task.TaskConclusion.FAILED == task.conclusion:
                self._log.error('task failed: %r', task.failure)
                self._code = 1
                self._shutdown()
            elif conveyor.task.TaskConclusion.CANCELED == task.conclusion:
                self._log.warning('task canceled')
                self._code = 1
                self._shutdown()
            else:
                raise ValueError(task.conclusion)

    def run(self):
        self._jsonrpc.addmethod('notify', self._notify)
        task = self._jsonrpc.request("hello", [], self._hellocallback)
        task.start()
        self._jsonrpc.run()
        return self._code
