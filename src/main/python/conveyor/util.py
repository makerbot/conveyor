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

import makerbot_driver


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

# TODO: now the bad coupling with the s3g module is here
def get_start_end_variables(profile, slicer_settings, material, dualstrusion):
    """
    This function is static so it can be invoked be the verify gcode task.
    @returns tuple of (start gcode block, end gcode block, variables)
    """
    tool_0, tool_1 = False, False
    if None is material:
        material = 'PLA'
    if dualstrusion:
        tool_0 = True
        tool_1 = True
    else:
        extruders = [e.strip() for e in slicer_settings.extruder.split(',')]
        if '0' in extruders:
            tool_0 = True
        if '1' in extruders:
            tool_1 = True
    ga = makerbot_driver.GcodeAssembler(profile._s3g_profile, profile._s3g_profile.path)
    start_template, end_template, variables = ga.assemble_recipe(
        tool_0=tool_0, tool_1=tool_1, material=material)
    start_gcode = ga.assemble_start_sequence(start_template)
    end_gcode = ga.assemble_end_sequence(end_template)
    variables['TOOL_0_TEMP'] = slicer_settings.extruder_temperature
    variables['TOOL_1_TEMP'] = slicer_settings.extruder_temperature
    variables['PLATFORM_TEMP'] = slicer_settings.platform_temperature
    start_position = profile._s3g_profile.values['print_start_sequence']['start_position']
    variables['START_X'] = start_position['start_x']
    variables['START_Y'] = start_position['start_y']
    variables['START_Z'] = start_position['start_z']
    return start_gcode, end_gcode, variables
