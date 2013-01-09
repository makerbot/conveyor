# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/util.py
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

"""
This module is a collection of utility functions that don't fit somewhere more
specific.

"""

from __future__ import (absolute_import, print_function, unicode_literals)


def exception_to_failure(exception, **kwargs):
    """
    Convert an exception to a failure dict suitable for passing to Task.fail.

    @param exception the exception
    @param kwargs additional data that will be included in the failure dict.

    """

    exception_data = None
    if None is not exception:
        exception_data = {
            'name': exception.__class__.__name__,
            'args': exception.args,
            'errno': getattr(exception, 'errno', None),
            'strerror': getattr(exception, 'strerror', None),
            'filename': getattr(exception, 'filename', None),
            'winerror': getattr(exception, 'winerror', None),
            'message': unicode(exception),
        }
    failure = {'exception': exception_data,}
    failure.update(kwargs)
    return failure
