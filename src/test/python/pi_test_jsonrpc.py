from __future__ import (absolute_import, print_function, unicode_literals)

import unittest

import sys
import os
import json
import cStringIO as StringIO
import logging
import operator

#override sys.path for testing only 
sys.path.insert(0,'./src/main/python')
import conveyor
import conveyor.address 
import conveyor.jsonrpc 
from conveyor.jsonrpc import JsonRpc,JsonRpcException

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import mock 

class JsonReaderTestCase(unittest.TestCase):

    def test_constructor(self):
        jr = conveyor.jsonrpc._JsonReader()
        self.assertIsNotNone(jr._log)
        self.assertEqual(jr._state, 0)
        self.assertEqual(jr._stack, [])
        self.assertIsNotNone(jr._buffer)

    def test_reset(self):
        jr = conveyor.jsonrpc._JsonReader()
        jr._state = None
        jr._stack = None
        jr._buffer = None   
        jr._reset()
        self.assertEqual(jr._state, 0)
        self.assertEqual(jr._stack, [])
        self.assertIsNotNone(jr._buffer)

    def test_consume(self):
        def fake_call(self, *args, **kwargs):
            print *args
            print **kwargs

        mockEvent = mock.Mock(conveyor.event.Event)
        mockEvent.__call__ = fake_call
        jr = conveyor.jsonrpc._JsonReader(mockEvent)
        
        testBlock= (" ", #ignore, pre json block
            "{'testa':'value", # partial stream
            "A' }" ) # end of block, buffer clears
    
        # test pre-blocks is ignored
        for ch in testBlock[0]:
            jr._consume(ch)
        self.assertEqual(jr._state,0)
        self.assertEqual(jr._stack,[]) #nothing stacked
        self.assertEqual(jr._buffer.getvalue(),' ') #nothing buffered 
    
        for ch in testBlock[1]:
            jr._consume(ch)
        self.assertEqual(jr._state, 1)
        self.assertEqual(jr._stack,['{']) #nothing stacked
        self.assertEqual(jr._buffer.getvalue(),
            ''.join(testBlock[0:2])) # buffered 

        for ch in testBlock[2]:
            jr._consume(ch)
        self.assertEqual(jr._state, 0)
        self.assertEqual(jr._stack,[]) #nothing stacked
        self.assertEqual(jr._buffer.getvalue(),'') # buffered cleared
        
    
    def test_feed(self):
        jr = conveyor.jsonrpc._JsonReader()
        self.assertEqual(jr._stack,[]) #nothing stacked 
        testStr = "{ 'foox':'asdf' }"
        jr.feed(testStr)
        self.assertEqual(jr._buffer.getvalue(),'') #buffer has cleared  

        testStr = "{ 'foox':'a"
        jr.feed(testStr)
        self.assertEqual(jr._buffer.getvalue(), testStr)#buffer not cleared 
        testStr2 = "sdf' }"
        jr.feed(testStr2)
        self.assertEqual(jr._buffer.getvalue(),'' )# buffer has cleared w close bracket


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
        """ addsa bunch of test function to the JsonRpc server
        for testing reasons.
        @param jsonrpcserver object of JsonRpc type 
        """
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

    def _raise_Exception(self):
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
        
        logging.error('TRICKY: test %s expects to log a server exception', self._testMethodName)
        #with self.assertRaises(Exception):P
        response = self._test_jsonresponse(data, True)
        self._asserterror(
            -32000, 'uncaught exception', '1', response,
            {'name': 'Exception', 'args': ['message']})

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


if __name__ == '__main__':
    unittest.main()
