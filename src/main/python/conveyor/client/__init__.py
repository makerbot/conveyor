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
            self._initsubparser_query_printer,
            self._initsubparser_list_printers,
            self._initsubparser_printers,
            self._initsubparser_printtofile,
            self._initsubparser_slice,
            self._initsubparser_scan,
            self._initsubparser_verify_usb_detect,
            self._initsubparser_dir,
            self._initsubparser_cancel
            self._initsubparser_listen,
        ):
                method(subparsers)


    def _initsubparser_printers(self, subparsers):
        parser = subparsers.add_parser('printers', help='list connected printers')
        parser.set_defaults(func=self._list_printers)
        self._initparser_common(parser)
        parser.add_argument(
            '--json',
            action='store_true',
            default=False,
            help='print in JSON format')
        parser.add_argument('--vid', action='store', 
            type=int, default = 0x23C1, dest ='vid',
            help='Limit printer scan by USB VendorId')
        parser.add_argument('--pid', action='store', 
             type=int, default = None, dest = 'pid',
             help='Limit printer scan by USB ProductId')
        parser.add_argument( '--port',dest='endpoint', default=None,
             help="specify a connection for a printer ex. 'COM3' or '/dev/tty1'")
 

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
        parser.add_argument( '--port',dest='endpoint', default=None,
             help="specify a connection for a printer ex. 'COM3' or '/dev/tty1'")


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
        parser.add_argument( '--port',dest='endpoint', default=None,
             help="specify a connection for a printer ex. 'COM3' or '/dev/tty1'")


    def _initsubparser_query_printer(self, subparsers):
        """ setup parser options for query printers """
        parser = subparsers.add_parser('query_printer',help='connect to printers for status/data query')
        parser.set_defaults(func=self._query_printer)
        self._initparser_common(parser)
        parser.add_argument( '--port',dest='endpoint', default=None,
            help="specify a connection for a printer ex. 'COM3' or '/dev/tty1'")


    def _initsubparser_cancel(self, subparsers):
        """ setup parser options for query printers """
        parser = subparsers.add_parser('cancel',help='connect to printers for status/data query')
        parser.set_defaults(func=self._cancel_print)
        self._initparser_common(parser)
        parser.add_argument( '--job',dest='job_id', default=None,
             help="specify a job to print by id string.")
        parser.add_argument( '--port',dest='endpoint', default=None,
             help="specify a connection for a printer ex. 'COM3' or '/dev/tty1'")

    def _initsubparser_list_printers(self,subparsers):
        """ setup parser options for 'list printers' option """
        parser = subparsers.add_parser('list_printers',help='list known or found printers')
        parser.set_defaults(func=self._list_printers)
        self._initparser_common(parser)
        parser.add_argument('--vid', action='store', 
            type=int, default = 0x23C1, dest ='vid',
            help='Limit printer scan by USB VendorId')
        parser.add_argument('--pid', action='store', 
             type=int, default = None, dest = 'pid',
             help='Limit printer scan by USB ProductId')
        parser.add_argument( '--port',dest='endpoint', default=None,
             help="specify a connection for a printer ex. 'COM3' or '/dev/tty1'")

    def _initsubparser_scan(self,subparsers):
        """ setup parser options for 'scan for printers' option """
        parser = subparsers.add_parser('scan',help='ping a service or tool')
        parser.set_defaults(func=self._run_scan)
        self._initparser_common(parser)
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

    def _initsubparser_listen(self, subparsers):
        parser = subparsers.add_parser('listen')
        parser.set_defaults(func=self._run_listen)
        self._initparser_common(parser)

    def _initsubparser_verify_usb_detect(self,subparsers):
        """ setup parser options for 'verify USB' option """
        parser = subparsers.add_parser('verify_usb_detect', help='functional test, does usb work?')
        parser.set_defaults(func=self._verify_usb_detect)
        self._initparser_common(parser)

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
            self._parsedargs.skip_start_end,
            self._parsedargs.endpoint]
        self._log.info('printing: %s', self._parsedargs.thing)
        code = self._run_client('print', params)
        return code

    def _run_scan(self):
        params = {"vid":self._parsedargs.vid, "pid":self._parsedargs.pid}
        code = self._run_client('printer_scan', params) #from server/__init__.py
        return code 

    def _cancel_print(self):
        params = { 'port':self._parsedargs.endpoint, 'job_id':self._parsedargs.job_id} 
        code = self._run_client('cancel', params ) #from server/__init__.py
        return code

    def _query_printer(self):
        params = { 'port':self._parsedargs.endpoint} 
        code = self._run_client('printer_query', params, self._show_query_printer_result) #from server/__init__.py
        return code 

    def _list_printers(self):
        import pdb
        pdb.set_trace()
        params = {'pid':self._parsedargs.pid,
                'vid':self._parsedargs.vid,
                'endpoint':self._parsedargs.endpoint } 
        code = self._run_client('printer_scan', params, self._show_list_printers_result) #from server/__init__.py
        return code 

    def _run_dir(self):
        params = []
        code = self._run_client('dir', params, self._show_results_to_user ) #from server/__init__.py
        return code

    def _show_results_to_user(self, task):
        """ prints servers response to the end user that called
        the task. """
        import json
        import sys
        x = json.dumps(task.result, sys.stderr, indent = 2)
        print(x)

    def _show_list_printers_result(self, task):
        """ custom callback to display results to the user.  Must match 
        behavior and core of Client.defaultcallback """
        # do activity of default callback
        printers = []
        for dict in task.result:
            r = { 'name' : 'Name Not Fetched',
                'displayname': 'display not fetched',
                 'kind': 'kind not fetched',
                 'extruders':1,
                 'port': dict['port']
            }
            printers.append(r)
        import json
        import sys
        x = json.dumps(task.result, sys.stderr)
        print(x)

    def _verify_usb_detect(self):
        """ interactive test to verify that bot printers are listed correctly """

        endpoint = raw_input("Verify a printer is plugged in and type the port here: ")

        # Params for the fuction to send to the server
        params = {'pid':None, 'vid':None, 'endpoint':endpoint }
        # Run the standard list printers' function, using the 'show the list to a user' callback
        # TODO: Un-comment when master is merged into release branch
        # code = self._run_client('printer_scan', params, self._show_list_printers_result) 
        code = 0
        if code != 0: return code

        # Ask for confirmation the tech read the list
        answer = raw_input("Did you see a printer listed above (y/N)?:")
        if answer.lower() == 'n': return -40

        raw_input("Please unplug printer and hit <enter> to continue")

        # TODO: Un-comment when master is merged into release branch
        # code = self._run_client('printer_scan',params, self._show_list_printers_result)
        if code != 0: return code

        answer = raw_input("Did you see no printers listed above (y/N)?:")
        if answer.lower() == 'n': return -60

        return 0

    def _show_query_printer_result(self, task):
        """ custom callback to display results to the user.  Must match 
        behavior and core of Client.defaultcallback """
        # do activity of default callback
        import json
        import sys
        x = json.dumps(task.result, sys.stderr)
        print(x)

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

    def _run_listen(self):
        fp = conveyor.jsonrpc.socketadapter(self._socket)
        jsonrpc = conveyor.jsonrpc.JsonRpc(fp, fp)
        jsonrpc.run()
        code = 0
        return code

    def _run_client(self, method, params, displaycallback=None):
        """ Creates a client object to run a single command to the server, 
        then waits for a reply and return the success code.
        """
        client = conveyor.client.Client.clientFactory(self._socket, method, params, displaycallback)
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
    """ Client object represents one complete task transaction to the server,
         including verification 'hello', waiting for task completin for syncronous
         tasks, and returning an error code. 
    """

    @classmethod
    def clientFactory(cls, sock, method, params, displaycallback=None):
        """constructs a client to execute a command, send cmd to the server, and wait for reply """
        fp = conveyor.jsonrpc.socketadapter(sock)
        jsonrpc = conveyor.jsonrpc.JsonRpc(fp, fp)
        client = Client(sock, fp, jsonrpc, method, params, displaycallback)
        return client

    def __init__(self, sock, fp, jsonrpc, method, params, displaycallback=None):
        """ Create a client object to throw a request to the server,
        and receive a reply. If no callback is specified, a generic callback
        that stores return values to a tmpfile is called when a reply is received. 
        """
        self._code = None
        self._fp = fp
        self._jsonrpc = jsonrpc
        self._log = logging.getLogger(self.__class__.__name__)
        self._method = method
        self._params = params
        self._sock = sock
        self._methodcallback = self.defaultcallback
        self._displaycallback = displaycallback

    def _stop(self):
        self._fp.stop()

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
            self._stop()

    def _hellocallback(self, task):
        """ default callback to handle reply to a 'hello' event """
        self._log.debug('task=%r', task)
        #hello was a success. do core method calls now that we verified a server 
        task1 = self._jsonrpc.request(self._method, self._params, self._methodcallback)
        task1.start()

    def _write_result_to_tmpfile(self, task, suffix='.results.txt', delete=False):
        try:
            fh = tempfile.NamedTemporaryFile('w+', suffix=suffix, delete=delete)
            fh.write(str(task.result))
            self._log.info('task results stored in: %s',  str(fh.name) )
            fh.close()
        except Exception, e:
            self.log.error('Attempt to store task results failed %r', e)
 
    def defaultcallback(self, task):
        """ default callback. Checks for errors, tries to write
        any return values to a temp file for end user user
        """
        self._log.debug('task=%r', task)
        if conveyor.task.TaskState.STOPPED == task.state:
            if conveyor.task.TaskConclusion.ENDED == task.conclusion:
                 if  task.result == None:
                    self._log.error('task success. Error: task result: None')
                 else:
                     self._write_result_to_tmpfile(task, suffix="result.txt")
                     if self._displaycallback :
                           self._displaycallback(task)
                 self._code = 0
                 self._stop()
            elif conveyor.task.TaskConclusion.FAILED == task.conclusion:
                self._log.error('task failed: %r', task.failure)
                self._code = 1
                self._stop()
            elif conveyor.task.TaskConclusion.CANCELED == task.conclusion:
                self._log.warning('task canceled')
                self._code = 1
                self._stop()
            else:
                raise ValueError(task.conclusion)

    def run(self):
        self._jsonrpc.addmethod('notify', self._notify)
        task = self._jsonrpc.request("hello", [], self._hellocallback)
        task.start()
        self._jsonrpc.run()
        return self._code
