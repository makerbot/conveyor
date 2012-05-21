# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/test.py
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
import logging.config

try:
    import unittest2 as unittest
except ImportError:
    import unittest

class ListHandler(logging.Handler):
    list = []

    def emit(self, record):
        ListHandler.list.append(record)

def listlogging(level):
    dct = {
        'version': 1,
        'formatters' : {
            'formatter': {
                'format': '%(message)s'
            }
        },
        'filters': {
        },
        'handlers': {
            'list': {
                'class': 'conveyor.test.ListHandler',
                'level': 'DEBUG',
                'formatter': 'formatter',
                'filters': []
            }
        },
        'loggers': {
        },
        'root': {
            'level': level,
            'propagate': True,
            'filters': [],
            'handlers': ['list']
        },
        'incremental': False,
        'disable_existing_loggers': False
    }
    logging.config.dictConfig(dct)

class _ListHandlerTestCase(unittest.TestCase):
    def setUp(self):
        listlogging('INFO')

    def test_emit(self):
        '''Test that the ListHandler collects log messages into its list.'''

        ListHandler.list = []
        log = logging.getLogger('ListHandlerTestCase')
        log.info('info')
        self.assertEqual(1, len(ListHandler.list))
        self.assertEqual('info', ListHandler.list[0].msg)
