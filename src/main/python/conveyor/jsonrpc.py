# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/jsonrpc.py
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

import cStringIO as StringIO
import errno
import json
import logging
import io
import operator
import os
import sys
import threading

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import conveyor.event
import conveyor.test
import conveyor.task

class socketadapter(object):
    '''A file-like wrapper for sockets.

    This differs from socket.makefile() in that the read() method doesn't
    buffer until the end of time and it only implements the methods required by
    the _JsonReader and JsonRpc class contracts.

    '''

    def flush(self):
        pass

    def write(self, data):
        self._fp.sendall(data)

    if 'nt' == os.name:
        def __init__(self, fp):
            self._fp = fp
            self._shutdown = False

        def read(self, size=-1):
            while True:
                if self._shutdown:
                    return ''
                else:
                    import select
                    rlist, wlist, xlist = select.select([self._fp], [], [], 1)
                    if 0 != len(rlist):
                        try:
                            data = self._fp.recv(size)
                        except IOError as e:
                            if errno.EBADF == e.errno:
                                data = ''
                            else:
                                raise
                        return data

        def shutdown(self):
            self._shutdown = True
            self._fp.close()
    else:
        def __init__(self, fp):
            self._fp = fp

        def read(self, size=-1):
            data = self._fp.recv(size)
            return data

        def shutdown(self):
            # NOTE: use SHUT_RD instead of SHUT_RDWR or you will get annoying
            # 'Connection reset by peer' errors.
            import socket
            self._fp.shutdown(socket.SHUT_RD)
            self._fp.close()

# See conveyor/doc/jsonreader.{dot,png}.
#
#   S0 - handles whitespace before the top-level JSON object or array
#   S1 - handles JSON text that is not a string
#   S2 - handles JSON strings
#   S3 - handles JSON string escape sequences
#
# The _JsonReader state machine invokes the event handler whenever it makes an
# invalid transition. This resets the machine to S0 and sends the invalid JSON
# to the event handler. The event handler is expected to try to parse the
# invalid JSON and issue an error.

class _JsonReader(object):
    def __init__(self):
        self.event = conveyor.event.Event('_JsonReader.event')
        self._log = logging.getLogger(self.__class__.__name__)
        self._reset()

    def _reset(self):
        self._log.debug('')
        self._state = 0
        self._stack = []
        self._buffer = StringIO.StringIO()

    def _transition(self, ch):
        if 0 == self._state:
            if ch in ('{', '['):
                self._state = 1
                self._stack.append(ch)
            elif ch not in (' ', '\t', '\n', '\r'):
                self._send()
        elif 1 == self._state:
            if '"' == ch:
                self._state = 2
            elif ch in ('{', '['):
                self._stack.append(ch)
            elif ch in ('}', ']'):
                send = False
                if 0 == len(self._stack):
                    send = True
                else:
                    firstch = self._stack.pop()
                    if ('{' == firstch and '}' != ch) or ('[' == firstch
                        and ']' != ch):
                            send = True
                    else:
                        send = (0 == len(self._stack))
                if send:
                    self._send()
        elif 2 == self._state:
            if '"' == ch:
                self._state = 1
            elif '\\' == ch:
                self._state = 3
        elif 3 == self._state:
            self._state = 2
        else:
            raise ValueError(self._state)

    def _send(self):
        data = self._buffer.getvalue()
        self._log.debug('data=%r', data)
        self._reset()
        if 0 != len(data.strip(' \t\n\r')):
            self.event(data)

    def feed(self, data):
        self._log.debug('data=%r', data)
        for ch in data:
            self._buffer.write(ch)
            self._transition(ch)

    def feedfile(self, fp):
        self._log.debug('starting')
        while True:
            try:
                data = fp.read(8192)
            except IOError as e:
                if errno.EINTR == e.errno:
                    continue
                else:
                    raise
            else:
                if 0 == len(data):
                    break
                else:
                    self.feed(data)
        self._log.debug('ending')

    def feedeof(self):
        self._send()

class JsonRpcException(Exception):
    def __init__(self, code, message, data):
        Exception.__init__(self, code, message)
        self.code = code
        self.message = message
        self.data = data

class JsonRpc(object):
    def __init__(self, infp, outfp):
        self._idcounter = 0
        self._idcounterlock = threading.Lock()
        self._infp = infp # contract: .read(int)
        self._jsonreader = _JsonReader()
        self._jsonreader.event.attach(self._jsonreadercallback)
        self._log = logging.getLogger(self.__class__.__name__)
        self._methods = {}
        self._methodsinfo={}
        self._outfp = outfp # contract: .write(str), .flush()
        self._outfplock = threading.Lock()
        self._tasks = {}

    #
    # Common part
    #

    def _jsonreadercallback(self, indata):
        self._log.debug('indata=%r', indata)
        try:
            parsed = json.loads(indata)
        except ValueError:
            response = self._parseerror()
        else:
            if isinstance(parsed, dict):
                response = self._handleobject(parsed)
            elif isinstance(parsed, list):
                response = self._handlearray(parsed)
            else:
                response = self._invalidrequest(None)
        self._log.debug('response=%r', response)
        if None is not response:
            outdata = json.dumps(response)
            self._send(outdata)

    def _handleobject(self, parsed):
        if not isinstance(parsed, dict):
            response = self._invalidrequest(None)
        else:
            id = parsed.get('id')
            if self._isrequest(parsed):
                response = self._handlerequest(parsed, id)
            elif self._isresponse(parsed):
                response = None
                self._handleresponse(parsed, id)
            else:
                response = self._invalidrequest(id)
        return response

    def _handlearray(self, parsed):
        if 0 == len(parsed):
            response = self._invalidrequest(None)
        else:
            response = []
            for subparsed in parsed:
                subresponse = self._handleobject(subparsed)
                if None is not subresponse:
                    response.append(subresponse)
            if 0 == len(response):
                response = None
        return response

    def _isrequest(self, parsed):
        result = (
            'jsonrpc' in parsed
            and '2.0' == parsed['jsonrpc']
            and 'method' in parsed
            and isinstance(parsed['method'], basestring))
        return result

    def _isresponse(self, parsed):
        result = (self._issuccessresponse(parsed)
            or self._iserrorresponse(parsed))
        return result

    def _issuccessresponse(self, parsed):
        result = (
            'jsonrpc' in parsed and '2.0' == parsed['jsonrpc']
            and 'result' in parsed)
        return result

    def _iserrorresponse(self, parsed):
        result = (
            'jsonrpc' in parsed and '2.0' == parsed['jsonrpc']
            and 'error' in parsed)
        return result

    def _successresponse(self, id, result):
        response = {'jsonrpc': '2.0', 'result': result, 'id': id}
        return response

    def _errorresponse(self, id, code, message, data=None):
        error = {'code': code, 'message': message}
        if None is not data:
            error['data'] = data
        response = {'jsonrpc': '2.0', 'error': error, 'id': id}
        return response

    def _parseerror(self):
        response = self._errorresponse(None, -32700, 'parse error')
        return response

    def _invalidrequest(self, id):
        response = self._errorresponse(id, -32600, 'invalid request')
        return response

    def _methodnotfound(self, id):
        response = self._errorresponse(id, -32601, 'method not found')
        return response

    def _invalidparams(self, id):
        response = self._errorresponse(id, -32602, 'invalid params')
        return response

    def _send(self, data):
        self._log.debug('data=%r', data)
        with self._outfplock:
            self._outfp.write(data)
            self._outfp.flush()

    def run(self):
        self._log.debug('starting')
        self._jsonreader.feedfile(self._infp)
        self._jsonreader.feedeof()
        self._log.debug('ending')

    #
    # Client part
    #

    def _handleresponse(self, response, id):
        self._log.debug('response=%r, id=%r', response, id)
        task = self._tasks.get(id)
        if None is task:
            self._log.debug('ignoring response for unknown id: %r', id)
        else:
            if self._issuccessresponse(response):
                result = response['result']
                task.end(result)
            elif self._iserrorresponse(response):
                error = response['error']
                task.fail(error)
            else:
                raise ValueError(response)

    def notify(self, method, params):
        self._log.debug('method=%r, params=%r', method, params)
        request = {'jsonrpc': '2.0', 'method': method, 'params': params}
        data = json.dumps(request)
        self._send(data)

    def request(self, method, params,methodcallback):
        """ Builds a jsonrpc request task.
        @param method: json rpc method to run as a task
        @param params: params for method
        @param methodcallback: callback to run when rpc reply is received
        @return a Task object with methods setup properly
        """
        with self._idcounterlock:
            id = self._idcounter
            self._idcounter += 1
        self._log.debug('method=%r, params=%r, id=%r', method, params, id)
        def runningevent(task):
            request = {
                'jsonrpc': '2.0', 'method': method, 'params': params, 'id': id}
            data = json.dumps(request)
            self._send(data)
            self._tasks[id] = task
        def stoppedevent(task):
            del self._tasks[id]
        task = conveyor.task.Task()
        task.runningevent.attach(runningevent)
        task.stoppedevent.attach(stoppedevent)
        if methodcallback != None :
                task.stoppedevent.attach(methodcallback) 
        return task

    #
    # Server part
    #

    def _handlerequest(self, request, id):
        self._log.debug('request=%r, id=%r', request, id)
        method = request['method']
        if method not in self._methods:
            response = self._methodnotfound(id)
        else:
            func = self._methods[method]
            if 'params' not in request:
                response = self._invokemethod(id, func, (), {})
            else:
                params = request['params']
                if isinstance(params, dict):
                    response = self._invokemethod(id, func, (), params)
                elif isinstance(params, list):
                    response = self._invokemethod(id, func, params, {})
                else:
                    response = self._invalidparams(id)
        return response

    def _invokemethod(self, id, func, args, kwargs):
        self._log.debug(
            'id=%r, func=%r, args=%r, kwargs=%r', id, func, args, kwargs)
        response = None
        try:
            result = func(*args, **kwargs)
        except TypeError as e:
            self._log.debug('exception', exc_info=True)
            if None is not id:
                response = self._invalidparams(id)
        except JsonRpcException as e:
            self._log.debug('exception', exc_info=True)
            if None is not id:
                response = self._errorresponse(id, e.code, e.message, e.data)
        except:
            self._log.exception('uncaught exception')
            if None is not id:
                e = sys.exc_info()[1]
                data = {
                    'name': e.__class__.__name__, 'args': e.args,
                    'message': e.message}
                response = self._errorresponse(
                    id, -32000, 'uncaught exception', data)
        else:
            if None is not id:
                response = self._successresponse(id, result)
        self._log.debug('response=%r', response)
        return response

    def addmethod(self, method, func, info=None):
        """ add a RPC callback method to a RPC client or server. If no
         usage info is defined, a generic message is added.
        """
        self._log.debug('method=%r, func=%r', method, func)
        self._methods[method] = func
        self._methodsinfo[func] = info if info else "no param info '" + str(method) + "' Guess?!"

    def dict_all_methods(self):
        """ @returns a dict of all RPC method names:info pairs """
        result = {}
        if self._methods:
            for key in self._methods:
                if self._methods[key] in self._methodsinfo:
                     result[key] = self._methodsinfo[self._methods[key]] #
                else:
                     results[key] = repr(self._methods[key])
        return result


class _SocketadapterStubFile(object):
    def __init__(self):
        self.recv = conveyor.event.Callback()
        self.sendall = conveyor.event.Callback()

class _SocketadapterTestCase(unittest.TestCase):
    def test_flush(self):
        adapter = socketadapter(None)
        adapter.flush()

    def test_read(self):
        '''Test that the socketadapter calls the recv method on the underlying
        socket.

        '''

        fp = _SocketadapterStubFile()
        adapter = socketadapter(fp)
        self.assertFalse(fp.recv.delivered)
        self.assertFalse(fp.sendall.delivered)
        adapter.read()
        self.assertTrue(fp.recv.delivered)
        self.assertEqual((-1,), fp.recv.args)
        self.assertEqual({}, fp.recv.kwargs)
        self.assertFalse(fp.sendall.delivered)
        fp.recv.reset()
        self.assertFalse(fp.recv.delivered)
        self.assertFalse(fp.sendall.delivered)
        adapter.read(8192)
        self.assertEqual((8192,), fp.recv.args)
        self.assertEqual({}, fp.recv.kwargs)
        self.assertFalse(fp.sendall.delivered)

    def test_write(self):
        '''Test that the socketadapter calls the sendall method on the
        underlying socket.

        '''

        fp = _SocketadapterStubFile()
        adapter = socketadapter(fp)
        self.assertFalse(fp.recv.delivered)
        self.assertFalse(fp.sendall.delivered)
        adapter.write('data')
        self.assertFalse(fp.recv.delivered)
        self.assertTrue(fp.sendall.delivered)
        self.assertEqual(('data',), fp.sendall.args)
        self.assertEqual({}, fp.sendall.kwargs)

class _JsonReaderStubFile(object):
    def __init__(self):
        self.exception = None
        self.data = None

    def read(self, size):
        if None is not self.exception:
            exception = self.exception
            self.exception = None
            raise exception
        else:
            data = self.data
            self.data = ''
            return data

class _JsonReaderTestCase(unittest.TestCase):
    def test_object(self):
        '''Test handline an object.'''

        eventqueue = conveyor.event.geteventqueue()

        jsonreader = _JsonReader()
        callback = conveyor.event.Callback()
        jsonreader.event.attach(callback)

        jsonreader.feed('{"key":"value"')
        eventqueue.runiteration(False)
        self.assertFalse(callback.delivered)

        jsonreader.feed('}')
        eventqueue.runiteration(False)
        self.assertTrue(callback.delivered)
        self.assertEqual(('{"key":"value"}',), callback.args)

    def test_nestedobject(self):
        '''Test handling a nested object.'''

        eventqueue = conveyor.event.geteventqueue()

        jsonreader = _JsonReader()
        callback = conveyor.event.Callback()
        jsonreader.event.attach(callback)

        jsonreader.feed('{"key0":{"key1":"value"')
        eventqueue.runiteration(False)
        self.assertFalse(callback.delivered)

        jsonreader.feed('}')
        eventqueue.runiteration(False)
        self.assertFalse(callback.delivered)

        jsonreader.feed('}')
        eventqueue.runiteration(False)
        self.assertTrue(callback.delivered)
        self.assertEqual(('{"key0":{"key1":"value"}}',), callback.args)

    def test_escape(self):
        '''Test handling a string escape sequence.'''

        eventqueue = conveyor.event.geteventqueue()

        jsonreader = _JsonReader()
        callback = conveyor.event.Callback()
        jsonreader.event.attach(callback)

        jsonreader.feed('{"key":"value\\"')
        eventqueue.runiteration(False)
        self.assertFalse(callback.delivered)

        jsonreader.feed('"')
        eventqueue.runiteration(False)
        self.assertFalse(callback.delivered)

        jsonreader.feed('}')
        eventqueue.runiteration(False)
        self.assertTrue(callback.delivered)
        self.assertEqual(('{"key":"value\\""}',), callback.args)

    def test__transition_ValueError(self):
        '''Test that the _transition method throws a ValueError when _state is
        an unknown value.

        '''

        jsonreader = _JsonReader()
        jsonreader._state = None
        with self.assertRaises(ValueError):
            jsonreader._transition('')

    def test_feedfile(self):
        '''Test that feedfile handles JSON data that is split across multiple
        calls to feedfile.

        '''

        eventqueue = conveyor.event.geteventqueue()

        jsonreader = _JsonReader()
        callback = conveyor.event.Callback()
        jsonreader.event.attach(callback)

        data0 = '{"key":"value"'
        stream0 = StringIO.StringIO(data0.encode())
        jsonreader.feedfile(stream0)
        eventqueue.runiteration(False)
        self.assertFalse(callback.delivered)

        data1 = '}'
        stream1 = StringIO.StringIO(data1.encode())
        jsonreader.feedfile(stream1)
        eventqueue.runiteration(False)
        self.assertTrue(callback.delivered)
        self.assertEqual(('{"key":"value"}',), callback.args)

    def test_feedfile_eintr(self):
        '''Test that feedfile handles EINTR.'''

        eventqueue = conveyor.event.geteventqueue()

        jsonreader = _JsonReader()
        callback = conveyor.event.Callback()
        jsonreader.event.attach(callback)

        stub = _JsonReaderStubFile()
        stub.exception = IOError(errno.EINTR, 'interrupted')
        stub.data = '{"key":"value"}'
        jsonreader.feedfile(stub)
        eventqueue.runiteration(False)
        self.assertTrue(callback.delivered)
        self.assertEqual(('{"key":"value"}',), callback.args)

    def test_feedfile_exception(self):
        '''Test that feedfile propagates exceptions.'''

        jsonreader = _JsonReader()
        stub = _JsonReaderStubFile()
        stub.exception = IOError(errno.EPERM, 'permission')
        with self.assertRaises(IOError) as cm:
            jsonreader.feedfile(stub)
        self.assertEqual(errno.EPERM, cm.exception.errno)
        self.assertEqual('permission', cm.exception.strerror)

    def test_invalid(self):
        '''Test the receipt of invalid JSON text.'''

        eventqueue = conveyor.event.geteventqueue()

        jsonreader = _JsonReader()
        callback = conveyor.event.Callback()
        jsonreader.event.attach(callback)

        jsonreader.feed(']')
        eventqueue.runiteration(False)
        self.assertTrue(callback.delivered)
        self.assertEqual((']',), callback.args)

    def test_emptystack(self):
        '''Test the receipt of a ']' when the stack is empty.'''

        eventqueue = conveyor.event.geteventqueue()

        jsonreader = _JsonReader()
        callback = conveyor.event.Callback()
        jsonreader.event.attach(callback)

        jsonreader._state = 1
        jsonreader.feed(']')
        eventqueue.runiteration(False)
        self.assertTrue(callback.delivered)
        self.assertEqual((']',), callback.args)

class _JsonRpcTest(unittest.TestCase):
    def setUp(self):
        logging.debug('_testMethodName=%r', self._testMethodName)
        eventqueue = conveyor.event.geteventqueue()
        eventqueue._queue.clear()

    def _assertsuccess(self, result, id, response):
        expected = {'jsonrpc': '2.0', 'result': result, 'id': id}
        self.assertEqual(expected, response)

    def _asserterror(self, code, message, id, response, data=None):
        expected = {
            'jsonrpc': '2.0', 'error': {'code': code, 'message': message},
            'id': id}
        if None is not data:
            expected['error']['data'] = data
        self.assertEqual(expected, response)

    def _addmethods(self, jsonrpcserver):
        jsonrpcserver.addmethod('subtract', self._subtract)
        jsonrpcserver.addmethod('update', self._notification)
        jsonrpcserver.addmethod('foobar', self._notification)
        jsonrpcserver.addmethod('sum', self._sum)
        jsonrpcserver.addmethod('notify_hello', self._notification)
        jsonrpcserver.addmethod('get_data', self._get_data)
        jsonrpcserver.addmethod('notify_sum', self._notification)
        jsonrpcserver.addmethod(
            'notification_noargs', self._notification_noargs)
        jsonrpcserver.addmethod(
            'raise_JsonRpcException', self._raise_JsonRpcException)
        jsonrpcserver.addmethod('raise_Exception', self._raise_Exception)

    def _subtract(self, minuend, subtrahend):
        result = minuend - subtrahend
        return result

    def _notification(self, *args, **kwargs):
        pass

    def _sum(self, *args):
        result = reduce(operator.add, args, 0)
        return result

    def _get_data(self):
        result = ['hello', 5]
        return result

    def _notification_noargs(self): # pragma: no cover
        pass

    def _raise_JsonRpcException(self):
        raise JsonRpcException(1, 'message', 'data')

    def _raise_Exception(selfF):
        raise Exception('message')

    def _test_stringresponse(self, data, addmethods):
        infp = StringIO.StringIO(data.encode())
        outfp = StringIO.StringIO()
        jsonrpcserver = JsonRpc(infp, outfp)
        if addmethods:
            self._addmethods(jsonrpcserver)
        jsonrpcserver.run()
        eventqueue = conveyor.event.geteventqueue()
        eventqueue.runiteration(False)
        response = outfp.getvalue()
        return response

    def _test_jsonresponse(self, data, addmethods):
        response = json.loads(self._test_stringresponse(data, addmethods))
        return response

    def test_invalidrequest(self):
        '''Test an invalid request.'''

        infp = None
        outfp = StringIO.StringIO()
        jsonrpcserver = JsonRpc(infp, outfp)
        jsonrpcserver._jsonreadercallback('1')
        response = json.loads(outfp.getvalue())
        self._asserterror(-32600, 'invalid request', None, response)

    def test_invalidparams_0(self):
        '''Test a request with an invalid type of paramters.'''

        data = '{"jsonrpc": "2.0", "method": "subtract", "params": "x", "id": "1"}'
        response = self._test_jsonresponse(data, True)
        self._asserterror(-32602, 'invalid params', '1', response)

    def test_invalidparams_1(self):
        '''Test a request with an incorrect number of parameters.'''

        data = '{"jsonrpc": "2.0", "method": "subtract", "params": [1], "id": "1"}'
        response = self._test_jsonresponse(data, True)
        self._asserterror(-32602, 'invalid params', '1', response)

    def test_invalidparams_notification(self):
        '''Test a notification with invalid parameters.'''

        data = '{"jsonrpc": "2.0", "method": "notification_noargs", "params": [1]}'
        response = self._test_stringresponse(data, True)
        self.assertEqual('', response)

    def test_JsonRpcException(self):
        '''Test a request that throws a JsonRpcException.'''

        data = '{"jsonrpc": "2.0", "method": "raise_JsonRpcException", "id": "1"}'
        response = self._test_jsonresponse(data, True)
        self._asserterror(1, 'message', '1', response, 'data')

    def test_JsonRpcException_notification(self):
        '''Test a notification that throws a JsonRpcException.'''

        data = '{"jsonrpc": "2.0", "method": "raise_JsonRpcException"}'
        response = self._test_stringresponse(data, True)
        self.assertEqual('', response)

    def test_Exception(self):
        '''Test a request that throws an unexpected exception.'''

        data = '{"jsonrpc": "2.0", "method": "raise_Exception", "id": "1"}'
        response = self._test_jsonresponse(data, True)
        self._asserterror(
            -32000, 'uncaught exception', '1', response,
            {'name': 'Exception', 'args': ['message'], 'message': 'message'})

    def test_Exception_notification(self):
        '''Test a notification that throws an unexpected exception.'''

        data = '{"jsonrpc": "2.0", "method": "raise_Exception"}'
        response = self._test_stringresponse(data, True)
        self.assertEqual('', response)

    #
    # Tests based on the examples from the JSON-RPC 2.0 specification (Section
    # 7, "Examples").
    #

    def test_spec_positional_0(self):
        data = '{"jsonrpc": "2.0", "method": "subtract", "params": [42, 23], "id": 1}'
        response = self._test_jsonresponse(data, True)
        self._assertsuccess(19, 1, response)

    def test_spec_positional_1(self):
        data = '{"jsonrpc": "2.0", "method": "subtract", "params": [23, 42], "id": 2}'
        response = self._test_jsonresponse(data, True)
        self._assertsuccess(-19, 2, response)

    def test_spec_named_0(self):
        data = '{"jsonrpc": "2.0", "method": "subtract", "params": {"subtrahend": 23, "minuend": 42}, "id": 3}'
        response = self._test_jsonresponse(data, True)
        self._assertsuccess(19, 3, response)

    def test_spec_named_1(self):
        data = '{"jsonrpc": "2.0", "method": "subtract", "params": {"minuend": 42, "subtrahend": 23}, "id": 4}'
        response = self._test_jsonresponse(data, True)
        self._assertsuccess(19, 4, response)

    def test_spec_notification_0(self):
        data = '{"jsonrpc": "2.0", "method": "update", "params": [1,2,3,4,5]}'
        response = self._test_stringresponse(data, True)
        self.assertEqual('', response)

    def test_spec_notification_1(self):
        data = '{"jsonrpc": "2.0", "method": "foobar"}'
        response = self._test_stringresponse(data, True)
        self.assertEqual('', response)

    def test_spec_nonexistent(self):
        data = '{"jsonrpc": "2.0", "method": "foobar", "id": "1"}'
        response = self._test_jsonresponse(data, False)
        self._asserterror(-32601, 'method not found', '1', response)

    def test_spec_invalidjson(self):
        data = '{"jsonrpc": "2.0", "method": "foobar, "params": "bar", "baz]'
        response = self._test_jsonresponse(data, False)
        self._asserterror(-32700, 'parse error', None, response)

    def test_spec_invalidrequest(self):
        data = '{"jsonrpc": "2.0", "method": 1, "params": "bar"}'
        response = self._test_jsonresponse(data, False)
        self._asserterror(-32600, 'invalid request', None, response)

    def test_spec_batch_invalidjson(self):
        data = '''
            [
              {"jsonrpc": "2.0", "method": "sum", "params": [1,2,4], "id": "1"},
              {"jsonrpc": "2.0", "method"
            ]
        '''
        response = self._test_jsonresponse(data, False)
        self._asserterror(-32700, 'parse error', None, response)

    def test_spec_batch_empty(self):
        data = '[]'
        response = self._test_jsonresponse(data, False)
        self._asserterror(-32600, 'invalid request', None, response)

    def test_spec_batch_invalidbatch_0(self):
        data = '[1]'
        response = self._test_jsonresponse(data, False)
        self.assertTrue(isinstance(response, list))
        self.assertEqual(1, len(response))
        self._asserterror(-32600, 'invalid request', None, response[0])

    def test_spec_batch_invalidbatch_1(self):
        data = '[1, 2, 3]'
        response = self._test_jsonresponse(data, False)
        self.assertTrue(isinstance(response, list))
        self.assertEqual(3, len(response))
        self._asserterror(-32600, 'invalid request', None, response[0])
        self._asserterror(-32600, 'invalid request', None, response[1])
        self._asserterror(-32600, 'invalid request', None, response[2])

    def test_spec_batch(self):
        data = '''
            [
                {"jsonrpc": "2.0", "method": "sum", "params": [1,2,4], "id": "1"},
                {"jsonrpc": "2.0", "method": "notify_hello", "params": [7]},
                {"jsonrpc": "2.0", "method": "subtract", "params": [42,23], "id": "2"},
                {"foo": "boo"},
                {"jsonrpc": "2.0", "method": "foo.get", "params": {"name": "myself"}, "id": "5"},
                {"jsonrpc": "2.0", "method": "get_data", "id": "9"} 
            ]
        '''
        response = self._test_jsonresponse(data, True)
        self.assertTrue(isinstance(response, list))
        self.assertEqual(5, len(response))
        self._assertsuccess(7, '1', response[0])
        self._assertsuccess(19, '2', response[1])
        self._asserterror(-32600, 'invalid request', None, response[2])
        self._asserterror(-32601, 'method not found', '5', response[3])
        self._assertsuccess(['hello', 5], '9', response[4])

    def test_spec_batch_notification(self):
        data = '''
            [
                {"jsonrpc": "2.0", "method": "notify_sum", "params": [1,2,4]},
                {"jsonrpc": "2.0", "method": "notify_hello", "params": [7]}
            ]
        '''
        response = self._test_stringresponse(data, True)
        self.assertEqual('', response)

    #
    # Bi-directional tests
    #

    def test_notify(self):
        '''Test the notify method.'''

        stoc = StringIO.StringIO()
        ctos = StringIO.StringIO()
        client = JsonRpc(stoc, ctos)
        server = JsonRpc(ctos, stoc)
        callback = conveyor.event.Callback()
        server.addmethod('method', callback)
        self.assertFalse(callback.delivered)
        client.notify('method', [1])
        ctos.seek(0)
        server.run()
        eventqueue = conveyor.event.geteventqueue()
        eventqueue.runiteration(False)
        self.assertTrue(callback.delivered)
        self.assertEqual((1,), callback.args)
        self.assertEqual({}, callback.kwargs)

    def test_request(self):
        '''Test the request method.'''

        stoc = StringIO.StringIO()
        ctos = StringIO.StringIO()
        client = JsonRpc(stoc, ctos)
        server = JsonRpc(ctos, stoc)
        callback = conveyor.event.Callback()
        def method(*args, **kwargs):
            callback(*args, **kwargs)
            return 2
        server.addmethod('method', method)
        self.assertFalse(callback.delivered)
        task = client.request('method', [1])
        task.start()
        eventqueue = conveyor.event.geteventqueue()
        while True:
            result = eventqueue.runiteration(False)
            if not result:
                break
        ctos.seek(0)
        server.run()
        while True:
            result = eventqueue.runiteration(False)
            if not result:
                break
        stoc.seek(0)
        client.run()
        while True:
            result = eventqueue.runiteration(False)
            if not result:
                break
        self.assertTrue(callback.delivered)
        self.assertEqual((1,), callback.args)
        self.assertEqual({}, callback.kwargs)
        self.assertTrue(conveyor.task.TaskState.STOPPED, task.state)
        self.assertTrue(conveyor.task.TaskConclusion.ENDED, task.conclusion)
        self.assertTrue(2, task.result)

    def test_request_error(self):
        '''Test that the request method handles a server-side exception.'''

        stoc = StringIO.StringIO()
        ctos = StringIO.StringIO()
        client = JsonRpc(stoc, ctos)
        server = JsonRpc(ctos, stoc)
        def method(*args, **kwargs):
            raise Exception('failure')
        server.addmethod('method', method)
        task = client.request('method', [1])
        task.start()
        eventqueue = conveyor.event.geteventqueue()
        while True:
            result = eventqueue.runiteration(False)
            if not result:
                break
        ctos.seek(0)
        server.run()
        while True:
            result = eventqueue.runiteration(False)
            if not result:
                break
        stoc.seek(0)
        client.run()
        while True:
            result = eventqueue.runiteration(False)
            if not result:
                break
        self.assertTrue(conveyor.task.TaskState.STOPPED, task.state)
        self.assertTrue(conveyor.task.TaskConclusion.FAILED, task.conclusion)
        expected = {
            'message': 'uncaught exception',
            'code': -32000,
            'data': {
                'message': 'failure',
                'args': ['failure'],
                'name': 'Exception'
            }
        }
        self.assertEqual(expected, task.failure)

    def test__handleresponse_unknown(self):
        '''Test that the _handleresponse method logs a debugging message when
        it reads a response for an unknown request.

        '''

        conveyor.test.listlogging(logging.DEBUG)
        jsonrpc = JsonRpc(None, None)
        conveyor.test.ListHandler.list = []
        jsonrpc._handleresponse(None, 0)
        self.assertEqual(2, len(conveyor.test.ListHandler.list))
        self.assertEqual(
            'ignoring response for unknown id: 0',
            conveyor.test.ListHandler.list[1].getMessage())

    def test__handleresponse_ValueError(self):
        '''Test that the _handleresponse method throws a ValueError when it
        reads an object that is neither a request nor a response.

        '''

        jsonrpc = JsonRpc(None, None)
        jsonrpc._tasks[0] = conveyor.task.Task()
        with self.assertRaises(ValueError) as cm:
            jsonrpc._handleresponse({}, 0)
        self.assertEqual(({},), cm.exception.args)
