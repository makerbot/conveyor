# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:

from __future__ import (absolute_import, print_function, unicode_literals)

import collections
import errno
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

    def _print(self, toolpathgeneratorbusname, printerbusname, thing):
        self._log.debug(
            'toolpathgeneratorbusname=%r, printerbusname=%r, thing=%r',
            toolpathgeneratorbusname, printerbusname, thing)
        task = conveyor.task.Task()
        def runningcallback(unused):
            print('printing')
            import time
            time.sleep(5)
            task.end(None)
        task.runningevent.attach(runningcallback)
        def stoppedcallback(unused):
            params = [
                self._id, conveyor.task.TaskState.STOPPED,
                conveyor.task.TaskConclusion.ENDED]
            self._jsonrpc.notify('notify', params)
        task.stoppedevent.attach(stoppedcallback)
        self._server.appendtask(task)
        return None

    def _printtofile(self, toolpathgeneratorbusname, printerbusname, thing, s3g):
        self._log.debug(
            'toolpathgeneratorbusname=%r, printerbusname=%r, thing=%r, s3g=%r',
            toolpathgeneratorbusname, printerbusname, thing, s3g)
        task = conveyor.task.Task()
        def runningcallback(unused):
            print('printing-to-file')
            import time
            time.sleep(5)
            task.end(None)
        task.runningevent.attach(runningcallback)
        def stoppedcallback(unused):
            params = [
                self._id, conveyor.task.TaskState.STOPPED,
                conveyor.task.TaskConclusion.ENDED]
            self._jsonrpc.notify('notify', params)
        task.stoppedevent.attach(stoppedcallback)
        self._server.appendtask(task)
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

class Queue(object):
    def __init__(self):
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)
        self._log = logging.getLogger(self.__class__.__name__)
        self._queue = collections.deque()
        self._quit = False

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
        self._quit = False
        while not self._quit:
            self._runiteration()
        self._log.debug('ending')

    def quit(self):
        with self._condition:
            self._quit = True
            self._condition.notify_all()

class Server(object):
    def __init__(self, sock):
        self._clientthreads = []
        self._idcounter = 0
        self._lock = threading.Lock()
        self._queue = Queue()
        self._sock = sock

    def appendclientthread(self, clientthread):
        with self._lock:
            self._clientthreads.append(clientthread)

    def removeclientthread(self, clientthread):
        with self._lock:
            self._clientthreads.remove(clientthread)

    def appendtask(self, task):
        self._queue.appendtask(task)

    def run(self):
        taskqueuethread = threading.Thread(target=self._queue.run, name='taskqueue')
        taskqueuethread.start()
        eventqueue = conveyor.event.geteventqueue()
        eventqueuethread = threading.Thread(target=eventqueue.run, name='eventqueue')
        eventqueuethread.start()
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
                    clientthread = _ClientThread.create(self, fp, id)
                    clientthread.start()
        finally:
            self._queue.quit()
            eventqueue.quit()
            taskqueuethread.join(5)
            eventqueuethread.join(5)
        return 0
