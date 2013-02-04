#! /usr/bin/env python

from __future__ import (absolute_import, print_function, unicode_literals)

import sys

import conveyor.server.__main__


if '__main__' == __name__:
    sys.exit(conveyor.server.__main__._main(sys.argv))
