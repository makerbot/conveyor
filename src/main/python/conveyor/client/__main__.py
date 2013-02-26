# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/client/__main__.py
#
# conveyor - Printing dispatch engine for 3D objects and their friends.
# Copyright ¬© 2012 Matthew W. Samsonoff <matthew.samsonoff@makerbot.com>
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
import sys

import conveyor.client
import conveyor.log
import conveyor.main

from conveyor.decorator import command


@command(conveyor.client.CancelCommand)
@command(conveyor.client.ConnectCommand)
@command(conveyor.client.CompatibleFirmware)
@command(conveyor.client.DefaultConfigCommand)
@command(conveyor.client.DirCommand)
@command(conveyor.client.DisconnectCommand)
@command(conveyor.client.DownloadFirmware)
@command(conveyor.client.DriverCommand)
@command(conveyor.client.DriversCommand)
@command(conveyor.client.GetMachineVersions)
@command(conveyor.client.GetUploadableMachines)
@command(conveyor.client.JobCommand)
@command(conveyor.client.JobsCommand)
@command(conveyor.client.PauseCommand)
@command(conveyor.client.PortsCommand)
@command(conveyor.client.PrintCommand)
@command(conveyor.client.PrintToFileCommand)
@command(conveyor.client.PrintersCommand)
@command(conveyor.client.ProfileCommand)
@command(conveyor.client.ProfilesCommand)
@command(conveyor.client.ReadEepromCommand)
@command(conveyor.client.ResetToFactoryCommand)
@command(conveyor.client.SliceCommand)
@command(conveyor.client.UnpauseCommand)
@command(conveyor.client.UploadFirmwareCommand)
@command(conveyor.client.VerifyS3gCommand)
@command(conveyor.client.WaitForServiceCommand)
@command(conveyor.client.WriteEepromCommand)
class ClientMain(conveyor.main.AbstractMain):
    _program_name = 'conveyor'

    _config_section = 'client'

    _logging_handlers = ['stdout', 'stderr',]

    def _run(self):
        self._log_startup(logging.DEBUG)
        self._init_event_threads()
        command = self._parsed_args.command_class(
            self._parsed_args, self._config)
        code = command.run()
        return code


def _main(argv): # pragma: no cover
    conveyor.log.earlylogging('conveyor')
    main = ClientMain()
    code = main.main(argv)
    return code


if '__main__' == __name__: # pragma: no cover
    sys.exit(_main(sys.argv))
