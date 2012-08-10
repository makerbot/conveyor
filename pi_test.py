# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/pi_test.py
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

import sys

def _main(argv):
	
	code = 0 # no err
    try:
        import conveyor
    except ImportError as e:
        print(e)
	    code +=1
    else:
        code = 0
    
    try:
        import makerbot_driver 
    except ImportError as e:
		print(e)
	    code +=1
    else:
        code = 0

    try:
        import serial	
	    if(serial.__version__.index('mb') < 0):
			code +=1 # not makerbot's serial
    except ImportError as e :
		print(e)
	    code +=1
    else:
        code = 0 
    return code
	
    try:
        import serial.tools.list_ports as lp
		vid_pid_scan = lp.get_ports_by_vid_pid 
    except ImportError as e :
		print(e)
	    code +=1
    else:
        code = 0 
    return code
	
	
if '__main__' == __name__:
    code = _main(sys.argv)
    if None is code:
        code = 0
    sys.exit(code)
