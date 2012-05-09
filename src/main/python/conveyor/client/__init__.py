# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:

from __future__ import (absolute_import, print_function, unicode_literals)

import logging
import socket
import threading

import conveyor.jsonrpc
import conveyor.task

class Client(object):
    @classmethod
    def create(cls, sock, method, params):
        fp = conveyor.jsonrpc.socketadapter(sock)
        jsonrpc = conveyor.jsonrpc.JsonRpc(fp, fp)
        client = Client(sock, fp, jsonrpc, method, params)
        return client

    def __init__(self, sock, fp, jsonrpc, method, params):
        self._code = None
        self._fp = fp
        self._jsonrpc = jsonrpc
        self._log = logging.getLogger(self.__class__.__name__)
        self._method = method
        self._params = params
        self._sock = sock

    def _shutdown(self):
        self._sock.shutdown(socket.SHUT_RDWR)
        eventqueue = conveyor.event.geteventqueue()
        eventqueue.quit()

    def _notify(self, job, state, conclusion):
        self._log.debug('job=%r, state=%r, conclusion=%r', job, state, conclusion)
        if conveyor.task.TaskState.STOPPED == state:
            if conveyor.task.TaskConclusion.ENDED == conclusion:
                self._code = 0
            elif conveyor.task.TaskConclusion.FAILED == conclusion:
                self._log.error('job failed: %r', task.failure)
                self._code = 1
            elif conveyor.task.TaskConclusion.CANCELED == conclusion:
                self._log.warning('job canceled')
                self._code = 1
            else:
                raise ValueError(task.conclusion)
            self._shutdown()

    def _hellocallback(self, task):
        self._log.debug('task=%r', task)
        task1 = self._jsonrpc.request(self._method, self._params)
        task1.stoppedevent.attach(self._methodcallback)

    def _methodcallback(self, task):
        self._log.debug('task=%r', task)
        if conveyor.task.TaskState.STOPPED == task.state:
            if conveyor.task.TaskConclusion.ENDED == task.conclusion:
                pass
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
        eventqueue = conveyor.event.geteventqueue()
        eventqueuethread = threading.Thread(target=eventqueue.run, name='eventqueue')
        eventqueuethread.start()
        try:
            self._jsonrpc.addmethod('notify', self._notify)
            task = self._jsonrpc.request("hello", [])
            task.stoppedevent.attach(self._hellocallback)
            self._jsonrpc.run()
        finally:
            eventqueue.quit()
            eventqueuethread.join(5)
        print('code = %r' % (self._code,))
        return self._code
