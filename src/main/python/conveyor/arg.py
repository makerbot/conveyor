# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/arg.py
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

'''
This module contains functions for configuring argparse with all of the
command-line arguments and options used by both the conveyor client and
service. These functions should be used with the `@args` class decorator.

All of the options are collected here, in one place, to avoid conflicts and
confusion.

'''

from __future__ import (absolute_import, print_function, unicode_literals)

import conveyor.platform


def install(parser, cls):
    '''
    Install into `parser` all of the command-line arguments and options
    registered with the `@args` decorator against class `cls` and its parent
    classes.

    '''

    args_funcs = getattr(cls, '_args_funcs', None)
    if None is not args_funcs:
        for func in args_funcs:
            func(parser)


# Positional Arguments ########################################################


def positional_driver(parser):
    parser.add_argument(
        'driver_name',
        help='use DRIVER',
        metavar='DRIVER',
        )


def positional_firmware_version(parser):
    parser.add_argument(
        'firmware_version',
        help='the FIRMWARE-VERSION',
        metavar='FIRMWARE-VERSION',
        )


def positional_input_file(parser):
    parser.add_argument(
        'input_file',
        help='read input from INPUT-FILE',
        metavar='INPUT-FILE',
        )


def positional_job(parser):
    parser.add_argument(
        'job_id',
        type=int,
        help='execute command on JOB',
        metavar='JOB',
        )


def positional_output_file(parser):
    parser.add_argument(
        'output_file',
        help='write output to OUTPUT-FILE',
        metavar='OUTPUT-FILE',
        )


def positional_output_file_optional(parser):
    parser.add_argument(
        'output_file',
        nargs='?',
        help='write output to OUTPUT-FILE',
        metavar='OUTPUT-FILE',
        )


def positional_profile(parser):
    parser.add_argument(
        'profile_name',
        help='use PROFILE',
        metavar='PROFILE',
        )


# Options #####################################################################


def add_start_end(parser):
    parser.add_argument(
        '--add-start-end',
        action='store_true',
        help='add start/end G-code to OUTPUT-PATH',
        dest='add_start_end',
        )


def config(parser):
    parser.add_argument(
        '-c',
        '--config',
        action='store',
        default=conveyor.platform.DEFAULT_CONFIG_FILE,
        type=str,
        required=False,
        help='read configuration from FILE',
        metavar='FILE',
        dest='config_file',
        )


def driver(parser):
    parser.add_argument(
        '-d',
        '--driver',
        action='store',
        default=None,
        type=str,
        required=False,
        help='use DRIVER to control the machine',
        metavar='DRIVER',
        dest='driver_name',
        )


def extruder(parser):
    parser.add_argument(
        '-e',
        '--extruder',
        action='store',
        default='right',
        type=str,
        choices=('left', 'right', 'both',),
        required=False,
        help='use EXTRUDER to print',
        metavar='EXTRUDER',
        dest='extruder_name',
        )


def file_type(parser):
    parser.add_argument(
        '--file-type',
        action='store',
        default='x3g',
        type=str,
        choices=('s3g', 'x3g',),
        required=False,
        help='use the FILE-TYPE format for the OUTPUT-FILE',
        metavar='FILE-TYPE',
        dest='file_type',
        )


def gcode_processor(parser):
    parser.add_argument(
        '--gcode-processor',
        action='append',
        default=None,
        type=str,
        required=False,
        help='run PROCESSOR on .gcode files',
        metavar='PROCESSOR',
        dest='gcode_processor_names',
        )


def has_start_end(parser):
    parser.add_argument(
        '--has-start-end',
        action='store_true',
        help='INPUT-PATH includes custom start/end .gcode',
        dest='has_start_end',
        )


def json(parser):
    parser.add_argument(
        '-j',
        '--json',
        action='store_true',
        help='print output in JSON format',
        dest='json',
        )


def level(parser):
    parser.add_argument(
        '-l',
        '--level',
        action='store',
        default=None,
        type=str,
        choices=('CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET',),
        required=False,
        help='set logging to LEVEL',
        metavar='LEVEL',
        dest='level_name',
        )


def machine(parser):
    parser.add_argument(
        '-m',
        '--machine',
        action='store',
        default=None,
        type=str,
        required=False,
        help='execute command on MACHINE',
        metavar='MACHINE',
        dest='machine_name',
        )


def machine_type(parser):
    parser.add_argument(
        '--machine-type',
        action='store',
        default='TheReplicator',
        type=str,
        required=False,
        help='the MACHINE-TYPE',
        metavar='MACHINE-TYPE',
        dest='machine_type',
        )


def firmware_version(parser):
    parser.add_argument(
        '--machine-version',
        action='store',
        default='7.0',
        type=str,
        required=False,
        help='the firmware VERSION',
        metavar='VERSION',
        dest='firmware_version',
        )


def material(parser):
    parser.add_argument(
        '-M',
        '--material',
        action='store',
        default='PLA',
        type=str,
        choices=('ABS', 'PLA',),
        required=False,
        help='print using MATERIAL',
        metavar='MATERIAL',
        dest='material_name',
        )


def port(parser):
    parser.add_argument(
        '-p',
        '--port',
        action='store',
        default=None,
        type=str,
        required=False,
        help='connect to PORT',
        metavar='PORT',
        dest='port_name',
        )


def profile(parser):
    parser.add_argument(
        '-P',
        '--profile',
        action='store',
        default=None,
        type=str,
        required=False,
        help='use machine PROFILE',
        metavar='PROFILE',
        dest='profile_name',
        )


def nofork(parser):
    parser.add_argument(
        '--nofork',
        action='store_true',
        help='do not fork nor detach from the controlling terminal',
        dest='nofork',
        )


def slicer(parser):
    parser.add_argument(
        '-s',
        '--slicer',
        action='store',
        default='miraclegrue',
        type=str,
        choices=('miraclegrue', 'skeinforge',),
        required=False,
        help='slice model with SLICER',
        metavar='SLICER',
        dest='slicer_name',
        )


def slicer_settings(parser):
    parser.add_argument(
        '-S',
        '--slicer-settings',
        action='store',
        default=None,
        type=str,
        required=False,
        help='use custom SLICER-SETTINGS-PATH',
        metavar='SLICER-SETTINGS-PATH',
        dest='slicer_settings_path',
        )


def version(parser):
    parser.add_argument(
        '-v',
        '--version',
        action='version',
        help='show the verison message and exit',
        version='%(prog) 1.2.0.0',
        )
