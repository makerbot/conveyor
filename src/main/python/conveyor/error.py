# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/error.py
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


class Handleable(object):
    def handle(self, log):
        '''
        Handle the error by writing it to the specified log and returning an
        exit code.

        '''
        raise NotImplementedError


# NOTE: some exceptions end with `Error` and others with `Exception`. The name
# should have the same ending as the base class. Most of the `Error` classes
# derive from the built-in `KeyError`.


class ConfigKeyError(KeyError, Handleable):
    '''
    Raised when the configuration is missing a key. Since there are default
    values, the configuration should always be fully populated and this
    exception indicates a programming error.

    '''

    def __init__(self, config_path, key):
        KeyError.__init__(self, key)
        self.config_path = config_path
        self.key = key

    def handle(self, log):
        log.critical('internal error', exc_info=True)
        return 1


class ConfigTypeError(TypeError, Handleable):
    '''
    Raised when a configuration file element has an invalid type (e.g., it is a
    string instead of a number).

    '''

    def __init__(self, config_path, key, value):
        TypeError.__init__(self, value)
        self.config_path = config_path
        self.key = key
        self.value = value

    def handle(self, log):
        log.critical(
            'invalid type for configuration file element: %s: %s: %s',
            e.config_path, e.key, e.value, exc_info=True)
        return 1


class ConfigValueError(ValueError, Handleable):
    '''
    Raised when a configuration file element has an invalid value (e.g., the
    value for the logging level parameter is not one of the valid logging
    levels).

    '''

    def __init__(self, config_path, key, value):
        ValueError.__init__(self, key, value)
        self.config_path = config_path
        self.key = key
        self.value = value

    def handle(self, log):
        log.critical(
            'invalid value for configuration file element: %s: %s: %s',
            e.config_path, e.key, e.value, exc_info=True)
        return 1


class DriverMismatchException(Exception, Handleable):
    def handle(self, log):
        log.critical(
            'the requested driver does not match the machine\'s current driver',
            exc_info=True)
        return 1


class MachineStateException(Exception, Handleable):
    def handle(self, log):
        log.critical(
            'the machine is in an invalid state for that operation',
            exc_info=True)
        return 1


class MissingExecutableException(Exception, Handleable):
    def __init__(self, path):
        Exception.__init__(self, path)
        self.path = path

    def handle(self, log):
        log.critical('missing executable: %s', self.path, exc_info=True)
        return 1


class MissingFileException(Exception, Handleable):
    def __init__(self, path):
        Exception.__init__(self, path)
        self.path = path

    def handle(self, log):
        log.critical('missing file: %s', self.path, exc_info=True)
        return 1


class MissingMachineNameException(Exception, Handleable):
    def handle(self, log):
        log.critical(
            'unable to automatically detect the machine name; please specify a machine name',
            exc_info=True)
        return 1


class MultipleDriversException(Exception, Handleable):
    def handle(self, log):
        log.critical(
            'there are multiple drivers available; please specify a driver',
            exc_info=True)
        return 1


class MultiplePortsException(Exception, Handleable):
    def handle(self, log):
        log.critical(
            'there are multiple ports available; please specify a port',
            exc_info=True)
        return 1


class NoDriversException(Exception, Handleable):
    def handle(self, log):
        log.critical('there are no drivers available', exc_info=True)
        return 1


class NoPortsException(Exception, Handleable):
    def handle(self, log):
        log.critical('there are no ports available', exc_info=True)
        return 1


class NotFileException(Exception, Handleable):
    def __init__(self, path):
        Exception.__init__(self, path)

    def handle(self, log):
        log.critical('not a file: %s', self.path, exc_info=True)
        return 1


class PortMismatchException(Exception, Handleable):
    def handle(self, log):
        log.critical(
            'the requested port does not match the machine\'s current port',
            exc_info=True)
        return 1


class PrintQueuedException(Exception, Handleable):
    def handle(self, log):
        log.error('a print is already queued for the machine', exc_info=True)
        return 1


class ProfileMismatchException(Exception, Handleable):
    def handle(self, log):
        log.critical(
            'the requested profile does not match the machine\'s current profile',
            exc_info=True)
        return 1


class UnknownDriverError(KeyError, Handleable):
    def __init__(self, driver_name):
        KeyError.__init__(self, driver_name)
        self.driver_name = driver_name

    def handle(self, log):
        log.critical('unknown driver: %s', e.driver_name, exc_info=True)
        return 1


class UnknownJobError(KeyError, Handleable):
    def __init__(self, job_id):
        KeyError.__init__(self, job_id)
        self.job_id = job_id

    def handle(self, log):
        log.critical('unknown job: %s', e.job_id, exc_info=True)
        return 1


class UnknownMachineError(KeyError, Handleable):
    def __init__(self, machine_name):
        KeyError.__init__(self, machine_name)
        self.machine_name = machine_name

    def handle(self, log):
        log.critical('unknown machine: %s', e.machine_name, exc_info=True)
        return 1


class UnknownPortError(KeyError, Handleable):
    def __init__(self, port_name):
        KeyError.__init__(self, port_name)
        self.port_name = port_name

    def handle(self, log):
        log.critical('unknown port: %s', e.port_name, exc_info=True)
        return 1


class UnknownProfileError(KeyError, Handleable):
    def __init__(self, profile_name):
        KeyError.__init__(self, profile_name)
        self.profile_name = profile_name

    def handle(self, log):
        log.critical('unknown profile: %s', e.profile_name, exc_info=True)
        return 1


class UnsupportedModelTypeException(Exception, Handleable):
    def __init__(self, path):
        Exception.__init__(self, path)
        self.path = path

    def handle(self, log):
        log.critical(
            'not a supported model type: %s', self.path, exc_info=True)
        return 1


class UnsupportedPlatformException(Exception, Handleable):
    '''Raised when conveyor does not support your operating system.'''

    def handle(self, log):
        log.critical('conveyor does not support your platform', exc_info=True)
        return 1


def guard(log, func):
    try:
        code = func()
    except Handleable as e:
        code = e.handle(log)
    except KeyboardInterrupt:
        code = 0
        log.warning('interrupted')
        log.debug('handled exception', exc_info=True)
    except SystemExit as e:
        code = e.code
        log.debug('handled exception', exc_info=True)
    except:
        code = 1
        log.critical('internal error', exc_info=True)
    return code
