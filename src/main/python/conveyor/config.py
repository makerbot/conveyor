# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/config.py
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
This module defines the structure and default values of the conveyor
configuration file.

The configuration file is stored on disk in JSON format. It is loaded with
Python's built-in JSON parser, yielding a set of nested dicts with primitive
bool, float, int, and string values at the leaves. This module's `convert`
method transforms those nested dicts, applying validation rules and default
values, to obtain a completely populated configuration with richer values at
the leaves (i.e., the `address` field will contain a valid `Address` object
instead of a plain string).

This module also exports a `get` function which is useful for accessing values
deep within the configuration. The configuration should be fully populated
after conversion, so any `ConfigKeyError` raised by the `get` method indicates
a programming error.

Internally, defaults are applied during conversion by the method
`_Group.convert`. This has the (minor) consequence that the top-level
configuration must be a group/dict.

'''

from __future__ import (absolute_import, print_function, unicode_literals)

import decimal
import json
import os.path
import textwrap

import conveyor.address
import conveyor.json
import conveyor.error
import conveyor.platform
import conveyor.visitor


class Config(object):
    def __init__(self, config_path, root):
        self._config_path = config_path
        self._root = root

    def get(self, *path):
        key = []
        value = self._root
        for p in path:
            key.append(p)
            if isinstance(value, dict) and p in value:
                value = value[p]
            else:
                raise conveyor.error.ConfigKeyError(
                    self._config_path, '.'.join(key))
        return value


def convert(config_path, dct):
    '''
    Validate and convert the raw configuration using default values wherever
    necessary.

    '''

    type_ = _gettype()
    config = type_.convert(config_path, '', dct)
    return config


def get(config_path, dct, *path):
    '''
    Return a value from deep within a nested set of dicts. Raises a
    `ConfigKeyError` if the value is not found.

    Since there are default values, the configuration should always be fully
    populated and any `ConfigKeyError` indicates a programming error.

    >>> dct = {'a': {'b': {'c': 1}}}
    >>> get(dct, 'a', 'b', 'c')
    1
    >>> get(dct, 'a', 'b', 'X')
    Traceback (most recent call last):
        ...
    ConfigKeyError: a.b.X

    '''

    key = []
    value = dct
    for p in path:
        key.append(p)
        if isinstance(value, dict) and p in value:
            value = value[p]
        else:
            raise conveyor.error.ConfigKeyError(config_path, '.'.join(key))
    return value


def format_default(fp):
    formatter = _Formatter(fp)
    type_ = _gettype()
    formatter.visit(type_)


class _Type(object):
    '''
    An abstract type for the configuration file schema. Types convert low-level
    configuration file elements to more useful high-level values and they
    provide default values for missing elements.

    '''

    def _getdefault(self):
        '''
        Return the default value for the type. The default value is
        un-converted.

        Default values are handled during conversion. The method
        `_Group.convert` calls `_getdefault` whenever a field is missing.

        '''
        raise NotImplementedError

    def convert(self, config_path, key, value):
        '''
        Convert `value` into the appropriate Python type using default values
        wherever necessary.

        The `config_path` parameter is the path to the configuration file.

        The `key` parameter is the dotted name of the configuration element
        (i.e.  `common.address`).

        '''
        raise NotImplementedError


class _Primitive(_Type):
    '''A type representing a built-in Python type.'''

    def __init__(self, type, default):
        self._type = type
        self._default = default

    def _getdefault(self):
        return self._default

    def convert(self, config_path, key, value):
        if not isinstance(value, self._type):
            raise conveyor.error.ConfigTypeError(config_path, key, value)
        else:
            return value


class _Bool(_Primitive):
    '''A type representing a built-in Python bool.'''

    def __init__(self, default):
        _Primitive.__init__(self, bool, default)


class _Decimal(_Primitive):
    def __init__(self, s):
        default = decimal.Decimal(s)
        _Primitive.__init__(self, (float, decimal.Decimal), default)
        #                         ^^^^^^^^^^^^^^^^^^^^^^^^
        # NOTE: this misuses the fact that `self._type` is passed as the second
        # argument to `isinstance` and that will accept a tuple. The
        # consequence is that the default values are stored as `Decimal` but
        # read back as `float`. It prevents values like `0.27` from being
        # rendered as `0.27000000000000002` in the default configuration file.
        # However, values may still appear in other files with excessive
        # precision (i.e., in a Miracle Grue configuration file).


class _Float(_Primitive):
    '''A type representing a built-in Python float.'''

    def __init__(self, default):
        _Primitive.__init__(self, float, default)


class _Int(_Primitive):
    '''A type representing a built-in Python int.'''

    def __init__(self, default):
        _Primitive.__init__(self, int, default)


class _Str(_Primitive):
    '''
    A type representing a built-in Python string (any basestring; str or
    unicode).

    '''

    def __init__(self, default):
        _Primitive.__init__(self, basestring, default)


class _Address(_Type):
    '''A type representing a conveyor service address.'''

    def _getdefault(self):
        return conveyor.platform.DEFAULT_CONFIG_COMMON_ADDRESS

    def convert(self, config_path, key, value):
        if not isinstance(value, basestring):
            raise conveyor.error.ConfigTypeError(config_path, key, value)
        else:
            # Delegate to the Address parser. It will throw an exception if the
            # address is invalid.
            result = conveyor.address.Address.address_factory(value)
            return result


class _LogLevel(_Type):
    '''A type representing a log level.'''

    def __init__(self, default):
        self._default = default

    def _getdefault(self):
        return self._default

    def convert(self, config_path, key, value):
        if not isinstance(value, basestring):
            raise conveyor.error.ConfigTypeError(config_path, key, value)
        elif value not in ('CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG',
                'NOTSET',):
            raise conveyor.error.ConfigValueError(config_path, key, value)
        else:
            return value


class _FilesystemItem(_Type):
    '''
    An abstract type that represents a filesystem item. No check is made for
    the existence of the filesystem item.

    '''

    def __init__(self, *path):
        self._path = path

    def _getdefault(self):
        default = os.path.join(*self._path)
        return default

    def convert(self, config_path, key, value):
        if not isinstance(value, basestring):
            raise conveyor.error.ConfigTypeError(config_path, key, value)
        else:
            return value


class _Directory(_FilesystemItem):
    '''A type that represents a directory.'''


class _Executable(_FilesystemItem):
    '''A type that represents an executable.'''


class _File(_FilesystemItem):
    '''A type that represents a file.'''


class _Group(_Type):
    '''A type that represents a group of name/value pairs.'''

    def __init__(self, *fields):
        self._fields = fields

    def _getdefault(self):
        dct = {}
        for field in self._fields:
            dct[field.name] = field.value._getdefault()
        return dct

    def convert(self, config_path, key, value):
        if not isinstance(value, dict):
            raise conveyor.error.ConfigTypeError(config_path, key, value)
        else:
            group = value
            result = {}
            for field in self._fields:
                if 0 == len(key):
                    k = field.name
                else:
                    k = ''.join((key, '.', field.name))
                if field.name in group:
                    v = group[field.name]
                else:
                    # NOTE: this is where default values are applied to the
                    # configuration.
                    v = field.value._getdefault()
                result[field.name] = field.value.convert(config_path, k, v)
            return result


class _Field(object):
    '''A name/value pair within a _Group.'''

    def __init__(self, comment, name, value):
        self.comment = comment
        self.name = name
        self.value = value


class _Formatter(conveyor.visitor.Visitor):
    def __init__(self, fp):
        self._fp = fp
        self._level = 0
        self._need_indent = True

    def _indent(self):
        self._level += 2

    def _dedent(self):
        self._level -= 2

    def _newline(self):
        self._fp.write('\n')
        self._need_indent = True

    def _text(self, s):
        if self._need_indent:
            self._need_indent = False
            for i in range(self._level):
                self._fp.write(' ')
        self._fp.write(s)

    def accept__Primitive(self, primitive):
        self._text(conveyor.json.dumps(primitive._default))
        self._newline()

    def accept__Address(self, address):
        self._text(conveyor.json.dumps(str(address._getdefault())))
        self._newline()

    def accept__LogLevel(self, level):
        self._text(conveyor.json.dumps(level._default))
        self._newline()

    def accept__FilesystemItem(self, filesystem_item):
        self._text(conveyor.json.dumps(os.path.join(*filesystem_item._path)))
        self._newline()

    def accept__Group(self, group):
        self._text('{')
        first_in_group = True
        for field in group._fields:
            self._field(field, first_in_group)
            first_in_group = False
        self._text('}')
        self._newline()

    def _field(self, field, first_in_group):
        if first_in_group:
            self._text(' ')
        else:
            # self._newline()
            self._text(', ')
        self._indent()
        if None is not field.comment:
            # The text wrapping width is 78 characters, minus the indentation,
            # minus 3 to account for the '// ', but not less than 40
            # characters.
            width = max(40, 78 - self._level - 3)
            lines = textwrap.wrap(field.comment, width)
            if 0 != lines:
                for line in lines:
                    self._text('// ')
                    self._text(line)
                    self._newline()
        self._text(conveyor.json.dumps(field.name))
        self._text(':')
        if not isinstance(field.value, _Group):
            self._text(' ')
            self.visit(field.value)
        else:
            self._newline()
            self._indent()
            self.visit(field.value)
            self._dedent()
        self._dedent()


def _gettype():
    type_ = _Group(
        _Field(
            'Basic configuration parameters used by both the conveyor client and service.',
            'common',
            _Group(
                _Field(
                    'The address of the conveyor service.',
                    'address',
                    _Address(),
                ),
                _Field(
                    'The location of the conveyor service PID file.',
                    'pid_file',
                    _File(conveyor.platform.DEFAULT_CONFIG_COMMON_PID_FILE),
                ),
            ),
        ),
        _Field(
            'Configuration parameters for the MakerBot driver.',
            'makerbot_driver',
            _Group(
                _Field(
                    'The path to the avrdude executable.',
                    'avrdude_exe',
                    _Executable(conveyor.platform.DEFAULT_CONFIG_MAKERBOT_DRIVER_AVRDUDE_EXE),
                ),
                _Field(
                    'The location of the avrdude.conf configuration file.',
                    'avrdude_conf_file',
                    _File(conveyor.platform.DEFAULT_CONFIG_MAKERBOT_DRIVER_AVRDUDE_CONF_FILE),
                ),
                _Field(
                    'The directory containing the MakerBot machine profiles.',
                    'profile_dir',
                    _Directory(conveyor.platform.DEFAULT_CONFIG_MAKERBOT_DRIVER_PROFILE_DIR),
                ),
            ),
        ),
        _Field(
            'Configuration parameters for the Miracle Grue slicer.',
            'miracle_grue',
            _Group(
                _Field(
                    'The path to the Miracle-Grue executable.',
                    'exe',
                    _Executable(conveyor.platform.DEFAULT_CONFIG_MIRACLE_GRUE_EXE),
                ),
                _Field(
                    'The directory containing the default Miracle-Grue slicing profiles.',
                    'profile_dir',
                    _Directory(conveyor.platform.DEFAULT_CONFIG_MIRACLE_GRUE_PROFILE_DIR),
                ),
            ),
        ),
        _Field(
            'Configuration parameters for the Skeinforge slicer.',
            'skeinforge',
            _Group(
                _Field(
                    'The path to the Skeinforge application file.',
                    'file',
                    _File(conveyor.platform.DEFAULT_CONFIG_SKEINFORGE_FILE),
                ),
                _Field(
                    'The directory containing the default Skeinforge slicing profiles.',
                    'profile_dir',
                    _Directory(conveyor.platform.DEFAULT_CONFIG_SKEINFORGE_PROFILE_DIR),
                ),
                _Field(
                    'The default Skeinforge profile.',
                    'profile',
                    _Str('Replicator slicing defaults'),
                ),
            ),
        ),
        _Field(
            'Configuration parameters for the conveyor service.',
            'server',
            _Group(
                _Field(
                    'Whether or not the conveyor service should change directory to the root directory after launching.',
                    'chdir',
                    _Bool(False),
                ),
                _Field(
                    'The number of threads available for handling events.',
                    'event_threads',
                    _Int(4),
                ),
                _Field(
                    'The logging configuration for the conveyor service.',
                    'logging',
                    _Group(
                        _Field(
                            'Whether or not logging is enabled for the conveyor service.',
                            'enabled',
                            _Bool(True),
                            ),
                        _Field(
                            'The path for the conveyor service log file.',
                            'file',
                            _File(conveyor.platform.DEFAULT_CONFIG_SERVER_LOGGING_FILE),
                            ),
                        _Field(
                            'The logging level for the conveyor service.',
                            'level',
                            _LogLevel('INFO'),
                        ),
                    ),
                ),
                _Field(
                    'The path to the mesh extraction program.',
                    'unified_mesh_hack_exe',
                    _File(conveyor.platform.DEFAULT_CONFIG_SERVER_UNIFIED_MESH_HACK_EXE),
                ),
            ),
        ),
        _Field(
            'Configuration parameters for the conveyor client.',
            'client',
            _Group(
                _Field(
                    'The number of threads available for handling events.',
                    'event_threads',
                    _Int(2),
                ),
                _Field(
                    'The logging configuration for the conveyor client.',
                    'logging',
                    _Group(
                        _Field(
                            'Whether or not logging is enabled for the conveyor client.',
                            'enabled',
                            _Bool(True),
                        ),
                        _Field(
                            'The path for the conveyor client log file.',
                            'file',
                            _File('conveyorc.log'),
                        ),
                        _Field(
                            'The logging level for the conveyor service.',
                            'level',
                            _LogLevel('INFO'),
                        ),
                    ),
                ),
                _Field(
                    'Default driver. This setting applies to the conveyor command-line client only. It has no effect on MakerWare',
                    'driver',
                    _Str('s3g'),
                ),
                _Field(
                    'Default profile. This setting applies to the conveyor command-line client only. It has no effect on MakerWare.',
                    'profile',
                    _Str('Replicator2'),
                ),
                _Field(
                    'Default slicing settings. These settings apply to the conveyor command-line client only. They have no effect on MakerWare.',
                    'slicing',
                    _Group(
                        _Field(
                            'Whether or not to print a raft.',
                            'raft',
                            _Bool(False),
                        ),
                        _Field(
                            'Whether no not to print support material.',
                            'support',
                            _Bool(False),
                        ),
                        _Field(
                            'The infill density.',
                            'infill',
                            _Decimal('0.1'),
                        ),
                        _Field(
                            'The layer height.',
                            'layer_height',
                            _Decimal('0.27'),
                        ),
                        _Field(
                            'The number of shells.',
                            'shells',
                            _Int(2),
                        ),
                        _Field(
                            'The extruder temperature.',
                            'extruder_temperature',
                            _Decimal('230.0'),
                        ),
                        _Field(
                            'The platform temperature.',
                            'platform_temperature',
                            _Decimal('110.0'),
                        ),
                        _Field(
                            'The print speed.',
                            'print_speed',
                            _Decimal('80.0'),
                        ),
                        _Field(
                            'The travel speed.',
                            'travel_speed',
                            _Decimal('100.0'),
                        ),
                    ),
                ),
            ),
        ),
    )
    return type_
