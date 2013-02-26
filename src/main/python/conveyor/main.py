# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/main.py
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

import argparse
import decimal
import logging
import os
import platform
import struct
import sys

import conveyor.address
import conveyor.arg
import conveyor.config
import conveyor.debug
import conveyor.json
import conveyor.log
import conveyor.platform

from conveyor.decorator import args


@args(conveyor.arg.config)
@args(conveyor.arg.level)
@args(conveyor.arg.version)
class AbstractMain(object):
    _program_name = None

    _config_section = None

    _logging_handlers = None

    def __init__(self):
        self._log = conveyor.log.getlogger(self)
        self._unparsed_args = None
        self._parser = None
        self._config = None
        self._event_threads = []

    def main(self, args):
        self._unparsed_args = args
        def func():
            try:
                conveyor.debug.initdebug()
                self._init_parser()
                self._init_subparsers()
                self._parsed_args = self._parser.parse_args(
                    self._unparsed_args[1:])
                if None is not self._parsed_args.level_name:
                    root = logging.getLogger()
                    root.setLevel(self._parsed_args.level_name)
                self._load_config()
                self._init_logging()
                code = self._run()
            finally:
                conveyor.stoppable.StoppableManager.stopall()
                for thread in self._event_threads:
                    thread.join(1)
                    if thread.is_alive():
                        self._log.debug('thread not terminated: %r', thread)
            return code
        code = conveyor.error.guard(self._log, func)
        if 0 == code:
            level = logging.INFO
        else:
            level = logging.ERROR
        self._log.log(
            level, '%s terminating with exit code %d', self._program_name,
            code)
        # Uncomment this to log lingering threads.
        # conveyor.debug.logthreads(logging.INFO)
        return code

    def _init_parser(self):
        self._parser = argparse.ArgumentParser(prog=self._program_name)
        def error(message):
            self._log.error(message)
            sys.exit(2)
        self._parser.error = error # monkey patch!
        conveyor.arg.install(self._parser, self.__class__)

    def _init_subparsers(self):
        command_classes = getattr(self.__class__, '_command_classes', [])
        if 0 != len(command_classes):
            subparsers = self._parser.add_subparsers(
                dest='command_name', title='Commands')
            for command_class in command_classes:
                subparser = subparsers.add_parser(
                    str(command_class.name), help=command_class.help)
                conveyor.arg.install(subparser, command_class)
                subparser.set_defaults(command_class=command_class)

    def _load_config(self):
        try:
            with open(self._parsed_args.config_file) as fp:
                dct = conveyor.json.load(fp)
        except EnvironmentError as e:
            self._log.critical(
                'failed to read configuration file: %s: %s',
                self._parsed_args.config_file, e.strerror, exc_info=True)
            sys.exit(1)
        except ValueError:
            self._log.critical(
                'failed to parse configuration file: %s',
                self._parsed_args.config_file, exc_info=True)
            sys.exit(1)
        else:
            dct = conveyor.config.convert(self._parsed_args.config_file, dct)
            self._config = conveyor.config.Config(
                self._parsed_args.config_file, dct)

    def _init_logging(self):
        enabled = self._config.get(self._config_section, 'logging', 'enabled')
        filename = self._config.get(self._config_section, 'logging', 'file')
        if None is not self._parsed_args.level_name:
            level = self._parsed_args.level_name
        else:
            level = self._config.get(self._config_section, 'logging', 'level')
        handlers = self._logging_handlers
        if enabled:
            handlers.append('log')
        dct = self._get_logging_dct(filename, level, handlers)
        logging.config.dictConfig(dct)

    def _get_logging_dct(self, filename, level, handlers):
        dct = {
            'version': 1,
            'incremental': False,
            'disable_existing_loggers': False,
            'formatters': {
                'console': {
                    '()': 'conveyor.log.ConsoleFormatter',
                    'format': 'conveyor: %(levelname)s: %(message)s',
                },
                'log': {
                    '()': 'conveyor.log.DebugFormatter',
                    'format': '%(asctime)s - %(levelname)s - %(message)s',
                    'datefmt': None,
                    'debugformat': '%(asctime)s - %(levelname)s - %(pathname)s:%(lineno)d - %(funcName)s - %(message)s',
                },
            },
            'filters': {
                'stdout': {
                    '()': 'conveyor.log.StdoutFilter',
                },
                'stderr': {
                    '()': 'conveyor.log.StderrFilter',
                },
            },
            'handlers': {
                'stdout': {
                    'class': 'logging.StreamHandler',
                    'level': 'INFO',
                    'formatter': 'console',
                    'filters': ['stdout'],
                    'stream': 'ext://sys.stdout',
                },
                'stderr': {
                    'class': 'logging.StreamHandler',
                    'level': 'WARNING',
                    'formatter': 'console',
                    'filters': ['stderr'],
                    'stream': 'ext://sys.stderr',
                },
            },
            'loggers': {
                # 'conveyor.machine': {
                #     'level': 'DEBUG',
                #     'propagate': False,
                #     'filters': [],
                #     'handlers': handlers,
                # },
            },
            'root': {
                'level': level,
                'propagate': True,
                'filters': [],
                'handlers': handlers,
            },
        }
        if 'log' in handlers:
            # NOTE: only add this handler if the log file is enabled, otherwise
            # the logging system (at least on Windows) will try to create the
            # log file whether or not it is actually used.
            dct['handlers']['log'] = {
                'class': 'logging.FileHandler',
                'level': 'NOTSET',
                'formatter': 'log',
                'filters': [],
                'filename': filename,
            }
        return dct

    def _init_event_threads(self):
        event_threads = self._config.get(self._config_section, 'event_threads')
        eventqueue = conveyor.event.geteventqueue()
        for i in range(event_threads):
            name = 'event_thread-%d' % (i,)
            thread = conveyor.event.EventQueueThread(eventqueue, name)
            thread.start()
            self._event_threads.append(thread)

    def _get_pointer_size(self):
        size = 8 * struct.calcsize('P')
        return size

    def _log_startup(self, level):
        self._log.log(
            level, '%s %s started', self._program_name, conveyor.__version__)
        self._log.log(level, 'process id: %r', os.getpid())
        self._log.log(level, 'python version: %r', sys.version)
        self._log.log(level, 'python platform: %r', platform.platform())
        self._log.log(level, 'python pointer size: %r', self._get_pointer_size())

    def _run(self):
        raise NotImplementedError


@args(conveyor.arg.config)
@args(conveyor.arg.level)
@args(conveyor.arg.version)
class Command(object):
    def __init__(self, parsed_args, config):
        self._parsed_args = parsed_args
        self._config = config
        self._log = conveyor.log.getlogger(self)

    def run(self):
        raise NotImplementedError
