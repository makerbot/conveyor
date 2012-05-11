# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:

from __future__ import (absolute_import, print_function, unicode_literals)

import logging
import threading

import conveyor.jsonrpc

class _ClientThread(threading.Thread):
    @classmethod
    def create(cls, server, fp, id):
        jsonrpc = conveyor.jsonrpc.JsonRpc(fp, fp)
        clientthread = _ClientThread(server, jsonrpc, id)
        return clientthread

    def __init__(self, server, jsonrpc, id):
        threading.Thread.__init__(self)
        self._log = logging.getLogger(self.__class__.__name__)
        self._server = server
        self._id = id
        self._jsonrpc = jsonrpc

    def _hello(self, *args, **kwargs):
        self._log.debug('args=%r, kwargs=%r', args, kwargs)
        return None

    def _print(self, *args, **kwargs):
        self._log.debug('args=%r, kwargs=%r', args, kwargs)
        params = [
            self._id, conveyor.task.TaskState.STOPPED,
            conveyor.task.TaskConclusion.ENDED]
        self._jsonrpc.notify('notify', params)
        return None

    def _printtofile(self, *args, **kwargs):
        self._log.debug('args=%r, kwargs=%r', args, kwargs)
        params = [
            self._id, conveyor.task.TaskState.STOPPED,
            conveyor.task.TaskConclusion.ENDED]
        self._jsonrpc.notify('notify', params)
        return None

    def run(self):
        self._jsonrpc.addmethod('hello', self._hello)
        self._jsonrpc.addmethod('print', self._print)
        self._jsonrpc.addmethod('printtofile', self._printtofile)
        self._server.appendclientthread(self)
        try:
            self._jsonrpc.run()
        finally:
            self._server.removeclientthread(self)

class Server(object):
    def __init__(self, sock):
        self._clientthreads = []
        self._idcounter = 0
        self._lock = threading.Lock()
        self._sock = sock

    def appendclientthread(self, clientthread):
        with self._lock:
            self._clientthreads.append(clientthread)

    def removeclientthread(self, clientthread):
        with self._lock:
            self._clientthreads.remove(clientthread)

    def run(self):
        eventqueue = conveyor.event.geteventqueue()
        eventqueuethread = threading.Thread(target=eventqueue.run, name='eventqueue')
        eventqueuethread.start()
        try:
            while True:
                conn, addr = self._sock.accept()
                fp = conveyor.jsonrpc.socketadapter(conn)
                id = self._idcounter
                self._idcounter += 1
                clientthread = _ClientThread.create(self, fp, id)
                clientthread.start()
        finally:
            eventqueue.quit()
            eventqueuethread.join(5)
        return 0
