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

import StringIO
import codecs
import errno
import json
import logging
import io
import os
import sys
import threading


import conveyor.event
from conveyor.event import Event
import conveyor.stoppable
import conveyor.test
import conveyor.task

# See conveyor/doc/jsonreader.{dot,png}.
#
#   State 0 - handles whitespace before the top-level JSON object or array
#   State 1 - handles JSON text that is not a string
#   State 2 - handles JSON strings
#   State 3 - handles JSON string escape sequences
#
# The _JsonReader state machine invokes the event handler whenever it makes an
# invalid transition. This resets the machine to S0 and sends the invalid JSON
# to the event handler. The event handler is expected to try to parse the
# invalid JSON and issue an error.


class _JsonReader(object):
    """ Basic class to handle reading a JSON stream. Reads data via the
   'feed' and 'feedeof' functions. Waits for completed JSON chunks, and
    then passes them to self.event when a complete block is detected 
    """
    def __init__(self, inEvent=None):
        """ 
        @param conveyor event object, if None a new event object is created
        """ 
        # v Event to consume data
        self.event = inEvent if inEvent is not None else Event('_JsonReader.event')
        self._log = logging.getLogger(self.__class__.__name__)
        self._reset()

    def _reset(self):
        """ Resets our JSON stream. """
        self._log.debug('')
        self._state = 0
        self._stack = [] #json bracket-stack. stores JSON nesting level
        self._buffer = StringIO.StringIO()

    def _consume(self, ch):
        """ consume a single charachter, storing it and updating JSON stream 
        state. If char is mid-block, it is stored and state is updated. If
        the charachter completes a JSON block, the complete block is sent to 
        the associated Event, and the buffer is cleared. 
        @param ch is assumed to be a unicode char, in a JSON stream
        """
        self._buffer.write(ch) # buffer our new char
        # handle 'before top lvl json object' setup.
        if 0 == self._state:
            if ch in ('{', '['):
                self._state = 1
                self._stack.append(ch)
            elif ch not in (' ', '\t', '\n', '\r'):
                self._send()
        # handle during JSON object  
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
        # handle json strings
        elif 2 == self._state:
            if '"' == ch:
                self._state = 1
            elif '\\' == ch:
                self._state = 3
        # handle json string escapes 
        elif 3 == self._state:
            self._state = 2
        else:
            raise ValueError(self._state)

    def _send(self):
        """ posts _buffer to out registered Event, stripping edge chars"""
        data = self._buffer.getvalue()
        self._log.debug('data=%r', data)
        self._reset()
        if 0 != len(data.strip(' \t\n\r')):
            self.event(data)

    def feed(self, data):
        """ 
        Feed a chunk of data to the reader. If this chunk completes a JSON  dict, 
        that full be automatically be passed to the attached Event as part of 
        transition. 
        @param data, assumed to be unicode JSON data
        """
        self._log.debug('data=%r', data)
        for ch in data:
            self._consume(ch)

    def feedeof(self):
        """ send EOF """
        self._send()


class JsonRpcException(Exception):
    def __init__(self, code, message, data):
        Exception.__init__(self, code, message)
        self.code = code
        self.message = message
        self.data = data

# TODO: This TaskFactory nonsense is a pretty terrible hack. Ugh.

class TaskFactory(object):
    def __call__(self, *args, **kwargs):
        raise NotImplementedError

class JsonRpc(conveyor.stoppable.StoppableInterface):
    """ JsonRpc handles a json stream, to gaurentee the output file pointer 
    gets entire valid JSON blocks of data to process, by buffering up data 
    into complete blocks and only passing on entirer JSON blocks 
    """
    def __init__(self, infp, outfp):
        """
        @param infp input file pointer must have .read() and .stop()
        @param outfp output file pointer. must have .write()
        """
        self._condition = threading.Condition()
        self._idcounter = 0
        self._infp = infp # contract: .read(), .stop(), .close()
        self._jsonreader = _JsonReader()
        self._jsonreader.event.attach(self._jsonreadercallback)
        self._log = logging.getLogger(self.__class__.__name__)
        self._methods = {}
        self._methodsinfo={}
        self._outfp = outfp # contract: .write(str), .close()
        self._stopped = False
        self._tasks = {}
        reader_class = codecs.getreader('UTF-8')
        self._infp_reader = reader_class(self._infp)
        writer_class = codecs.getwriter('UTF-8')
        self._outfp_writer = writer_class(self._outfp)

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
        self._outfp_writer.write(data)

    def run(self):
        """ This loop will run until self._stopped is set true."""
        self._log.debug('starting')
        while True:
            with self._condition:
                stopped = self._stopped
            if self._stopped:
                break
            else:
                data = self._infp_reader.read()
                if 0 == len(data):
                    break
                else:
                    self._jsonreader.feed(data)
        self._jsonreader.feedeof()
        self._log.debug('ending')
        self.close()

    def stop(self):
        """ required as a stoppable object. """
        with self._condition:
            self._stopped = True
        self._infp.stop()

    def close(self):
        try:
            self._infp_reader.close()
        except:
            self._log.debug('handled exception', exc_info=True)
        try:
            self._outfp_writer.close()
        except:
            self._log.debug('handled exception', exc_info=True)

    #
    # Client part
    #

    def _handleresponse(self, response, id):
        self._log.debug('response=%r, id=%r', response, id)
        task = self._tasks.pop(id, None)
        if None is task:
            self._log.debug('ignoring response for unknown id: %r', id)
        elif self._iserrorresponse(response):
            error = response['error']
            task.fail(error)
        elif self._issuccessresponse(response):
            result = response['result']
            task.end(result)
        else:
            raise ValueError(response)

    def notify(self, method, params):
        self._log.debug('method=%r, params=%r', method, params)
        request = {'jsonrpc': '2.0', 'method': method, 'params': params}
        data = json.dumps(request)
        self._send(data)

    def request(self, method, params):
        """ Builds a jsonrpc request task.
        @param method: json rpc method to run as a task
        @param params: params for method
        @return a Task object with methods setup properly
        """
        with self._condition:
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
            if id in self._tasks.keys():
                del self._tasks[id]
            else:
                self._log.debug('stoppeevent fail for id=%r', id)
        task = conveyor.task.Task()
        task.runningevent.attach(runningevent)
        task.stoppedevent.attach(stoppedevent)
        return task

    #
    # Server part
    #

    def _handlerequest(self, request, id):
        self._log.debug('request=%r, id=%r', request, id)
        method = request['method']
        if method in self._methods:
            func = self._methods[method]
            if 'params' not in request:
                response = self._invokesomething(id, func, (), {})
            else:
                params = request['params']
                if isinstance(params, dict):
                    response = self._invokesomething(id, func, (), params)
                elif isinstance(params, list):
                    response = self._invokesomething(id, func, params, {})
                else:
                    response = self._invalidparams(id)
        else:
            response = self._methodnotfound(id)
        return response

    def _invokesomething(self, id, func, args, kwargs):
        if not isinstance(func, TaskFactory):
            response = self._invokemethod(id, func, args, kwargs)
        else:
            response = self._invoketask(id, func, args, kwargs)
        return response

    def _fixkwargs(self, kwargs):
        kwargs1 = {}
        for k, v in kwargs.items():
            k = str(k)
            kwargs1[k] = v
        return kwargs1

    def _invokemethod(self, id, func, args, kwargs):
        self._log.debug(
            'id=%r, func=%r, args=%r, kwargs=%r', id, func, args, kwargs)
        response = None
        kwargs = self._fixkwargs(kwargs)
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
                data = {'name': e.__class__.__name__, 'args': e.args}
                response = self._errorresponse(
                    id, -32000, 'uncaught exception', data)
        else:
            if None is not id:
                response = self._successresponse(id, result)
        self._log.debug('response=%r', response)
        return response

    def _invoketask(self, id, func, args, kwargs):
        self._log.debug(
            'id=%r, func=%r, args=%r, kwargs=%r', id, func, args, kwargs)
        response = None
        kwargs = self._fixkwargs(kwargs)
        try:
            task = func(*args, **kwargs)
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
                data = {'name': e.__class__.__name__, 'args': e.args}
                response = self._errorresponse(
                    id, -32000, 'uncaught exception', data)
        else:
            def stoppedcallback(task):
                if conveyor.task.TaskConclusion.ENDED == task.conclusion:
                    response = self._successresponse(id, task.result)
                elif conveyor.task.TaskConclusion.FAILED == task.conclusion:
                    response = self._errorresponse(id, -32001, 'task failed', task.failure)
                elif conveyor.task.TaskConclusion.CANCELED == task.conclusion:
                    response = self._errorresponse(id, -32002, 'task canceled', None)
                else:
                    raise ValueError(task.conclusion)
                outdata = json.dumps(response)
                self._send(outdata)
            task.stoppedevent.attach(stoppedcallback)
            task.start()
            response = None
        return response

    def addmethod(self, method, func, info=None):
        self._log.debug('method=%r, func=%r', method, func)
        self._methods[method] = func

    def getmethods(self):
        return self._methods


