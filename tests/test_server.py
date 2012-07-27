# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/server/__init__.py
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

import collections
import errno
import logging
import os
import sys
import threading

import conveyor.jsonrpc
import conveyor.main
import conveyor.recipe
import conveyor.server

try: 
    import unittest2
except ImportError:
    import unittest

class ServerTests(unittest.TestCase):
    def setUp(self): #runs before each test
        self.serverMain = conveyor.server.ServerMain()
    
    def tearDown(self):#runs after each test
        self.obj = None

    def test_build(self):
        self.assertTrue(self.serverMain != None)

    #def test_configd(self):
        #self.assertTrue(self.serverMain._config!= None)

g_server = None
class ServerRunningTest(unittest.TestCase):

    @classmethod
    def get_gserver(cls):
        global g_server
        if g_server == None:
            g_server = conveyor.server.ServerMain()
        return g_server

    def test_run(self):
        server = self.get_gserver()
        from  multiprocessing import Process
        p = Process(target=server.main,args=('a'))
        p.start()
        p.join()
        

#class ClientThreadTest(unittest.TestCase):
#    def setUp(self):
#        self.clientThread = conveyor.server._ClientThread.factory()
#    
#    def tearDown(self):
#        self.clientThread = None
#
#    def test_build(self):
#        
#        self.assertTrue(isinstance(self.clientThread,conveyor.server._ClientThread))

if __name__ == '__main__':
    unittest.main()
