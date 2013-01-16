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

import sys

import conveyor.client
import conveyor.log
import conveyor.main

from conveyor.decorator import command


@command(conveyor.client._CancelCommand)
@command(conveyor.client._CompatibleFirmware)
@command(conveyor.client._DirCommand)
@command(conveyor.client._DownloadFirmware)
@command(conveyor.client._GetMachineVersions)
@command(conveyor.client._GetUploadableMachines)
@command(conveyor.client._JobCommand)
@command(conveyor.client._JobsCommand)
@command(conveyor.client._PrintCommand)
@command(conveyor.client._PrintToFileCommand)
@command(conveyor.client._PrintersCommand)
@command(conveyor.client._ReadEepromCommand)
@command(conveyor.client._ResetToFactoryCommand)
@command(conveyor.client._SliceCommand)
@command(conveyor.client._UploadFirmwareCommand)
@command(conveyor.client._VerifyS3gCommand)
@command(conveyor.client._WaitForServiceCommand)
@command(conveyor.client._WriteEepromCommand)
class ClientMain(conveyor.main.AbstractMain):
    _program_name = 'conveyor'

    _config_section = 'client'

    _logging_handlers = ['stdout', 'stderr',]

    def _run(self):
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
