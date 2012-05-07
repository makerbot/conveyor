# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:

from __future__ import (absolute_import, print_function, unicode_literals)

import PyQt4.QtCore
import dbus.mainloop.qt
import unittest
import sys
import threading

import conveyor.event

try:
    import unittest2 as unittest
except ImportError:
    import unittest

dbus.mainloop.qt.DBusQtMainLoop(set_as_default=True)

class DbusTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._application = PyQt4.QtCore.QCoreApplication(sys.argv)
        cls._eventqueue = conveyor.event.geteventqueue()
        cls._thread = threading.Thread(
            target=cls._eventqueue.run, name='eventqueue')
        cls._thread.start()

    @classmethod
    def tearDownClass(cls):
        cls._eventqueue.quit()
        cls._thread.join(1)

    def _wait(self, task):
        condition = threading.Condition()
        eventloop = PyQt4.QtCore.QEventLoop()
        def target():
            with condition:
                condition.wait(30)
            eventloop.quit()
        thread = threading.Thread(target=target, name='wait')
        thread.start()
        def notify(*args, **kwargs):
            with condition:
                condition.notify_all()
        task.stoppedevent.attach(notify)
        task.start()
        eventloop.exec_()
        thread.join(1)
