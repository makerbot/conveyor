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

# NOTE: some exceptions end with `Error` and others with `Exception`. The name
# should have the same ending as the base class. Most of the `Error` classes
# derive from the built-in `KeyError`.


class ConfigKeyError(KeyError):
    '''
    Raised when the configuration is missing a key. Since there are default
    values, the configuration should always be fully populated and this
    exception indicates a programming error.

    '''

    def __init__(self, config_path, key):
        KeyError.__init__(self, key)
        self.config_path = config_path
        self.key = key


class ConfigTypeError(TypeError):
    '''
    Raised when a configuration file element has an invalid type (e.g., it is a
    string instead of a number).

    '''

    def __init__(self, config_path, key, value):
        TypeError.__init__(self, value)
        self.config_path = config_path
        self.key = key
        self.value = value


class ConfigValueError(ValueError):
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


class MachineStateException(Exception):
    pass


class ProfileMismatchException(Exception):
    pass


class UnknownDriverError(KeyError):
    def __init__(self, driver_name):
        KeyError.__init__(self, driver_name)
        self.driver_name = driver_name


class UnknownMachineError(KeyError):
    def __init__(self, machine_name):
        KeyError.__init__(self, machine_name)
        self.machine_name = machine_name


class UnknownPortError(KeyError):
    def __init__(self, port_name):
        KeyError.__init__(self, port_name)
        self.port_name = port_name


class UnknownProfileError(KeyError):
    def __init__(self, profile_name):
        KeyError.__init__(self, profile_name)
        self.profile_name = profile_name


class UnsupportedPlatformException(Exception):
    '''Raised when conveyor does not support your operating system.'''


def guard(log, func):
    try:
        code = func()
    except ConfigKeyError as e:
        code = 1
        log.critical('internal error', exc_info=True)
    except ConfigTypeError as e:
        code = 1
        log.critical(
            'invalid type for configuration file element: %s: %s: %s',
            e.config_path, e.key, e.value, exc_info=True)
    except ConfigValueError as e:
        code = 1
        log.critical(
            'invalid value for configuration file element: %s: %s: %s',
            e.config_path, e.key, e.value, exc_info=True)
    except MachineStateException as e:
        code = 1
        log.critical(
            'the machine is in an invalid state for that operation',
            exc_info=True)
    except ProfileMismatchException as e:
        code = 1
        log.critical(
            'the requested profile does not match the machine\'s current profile',
            exc_info=True)
    except UnknownDriverError as e:
        code = 1
        log.critical('unknown driver: %s', e.driver_name, exc_info=True)
    except UnknownMachineError as e:
        code = 1
        log.critical('unknown machine: %s', e.machine_name, exc_info=True)
    except UnknownPortError as e:
        code = 1
        log.critical('unknown port: %s', e.port_name, exc_info=True)
    except UnknownProfileError as e:
        code = 1
        log.critical('unknown profile: %s', e.profile_name, exc_info=True)
    except UnsupportedPlatformException as e:
        code = 1
        log.critical('conveyor does not support your platform', exc_info=True)
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
