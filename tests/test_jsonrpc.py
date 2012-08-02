import sys
sys.path.insert(0,'src/main/python') # for testing only

from conveyor.jsonrpc import *

try:
    import unittest2 as unittest
except ImportError:
    import unittest

class _SocketadapterStubFile(object):
    def __init__(self):
        self.recv = conveyor.event.Callback()
        self.sendall = conveyor.event.Callback()


class SocketadapterTestCase(unittest.TestCase):


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


class JsonReaderStubFile(object):


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


class JsonReaderTestCase(unittest.TestCase):


    def test_object(self):
        '''Test handline an object.'''

        eventqueue = conveyor.event.geteventqueue()

        jsonreader = JsonReader()
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

        jsonreader = JsonReader()
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

        jsonreader = JsonReader()
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

        jsonreader = JsonReader()
        jsonreader._state = None
        with self.assertRaises(ValueError):
            jsonreader._transition('')


    def test_feedfile(self):
        '''Test that feedfile handles JSON data that is split across multiple
        calls to feedfile.

        '''

        eventqueue = conveyor.event.geteventqueue()

        jsonreader = JsonReader()
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

        jsonreader = JsonReader()
        callback = conveyor.event.Callback()
        jsonreader.event.attach(callback)

        stub = JsonReaderStubFile()
        stub.exception = IOError(errno.EINTR, 'interrupted')
        stub.data = '{"key":"value"}'
        jsonreader.feedfile(stub)
        eventqueue.runiteration(False)
        self.assertTrue(callback.delivered)
        self.assertEqual(('{"key":"value"}',), callback.args)


    def test_feedfile_exception(self):
        '''Test that feedfile propagates exceptions.'''

        jsonreader = JsonReader()
        stub = JsonReaderStubFile()
        stub.exception = IOError(errno.EPERM, 'permission')
        with self.assertRaises(IOError) as cm:
            jsonreader.feedfile(stub)
        self.assertEqual(errno.EPERM, cm.exception.errno)
        self.assertEqual('permission', cm.exception.strerror)


    def test_invalid(self):
        '''Test the receipt of invalid JSON text.'''

        eventqueue = conveyor.event.geteventqueue()

        jsonreader = JsonReader()
        callback = conveyor.event.Callback()
        jsonreader.event.attach(callback)

        jsonreader.feed(']')
        eventqueue.runiteration(False)
        self.assertTrue(callback.delivered)
        self.assertEqual((']',), callback.args)


    def test_emptystack(self):
        '''Test the receipt of a ']' when the stack is empty.'''

        eventqueue = conveyor.event.geteventqueue()

        jsonreader = JsonReader()
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
        task = client.request('method', [1], None)
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
        task = client.request('method', [1], None)
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


if __name__ == '__main__':
    unittest.main()
