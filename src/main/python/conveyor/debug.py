# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/debug.py
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
import logging
import signal
import sys
import threading
import traceback

def initdebug(): # pragma: no cover
    '''Initialize thread debugging support.

    The process will log the list of threads when it receives SIGUSR1 (on
    platforms that have SIGUSR1; sorry Windows).

    '''

    if hasattr(signal, 'SIGUSR1'):
        def _sigusr1(signum, frame): # pragma: no cover
            logthreads(logging.INFO)
        signal.signal(signal.SIGUSR1, _sigusr1)

def logthreads(level): # pragma: no cover
    '''Log the list of threads at the specified logging level.'''

    log = logging.getLogger('conveyor.debug')
    log.log(level, 'threads:')
    threads = {}
    for thread in threading.enumerate():
        threads[thread.ident] = thread
    for threadident, frame in sys._current_frames().iteritems():
        fp = StringIO.StringIO()
        print('thread=%r', file=fp)
        traceback.print_stack(frame, file=fp)
        message = fp.getvalue().strip()
        log.log(level, message, threads[threadident])
