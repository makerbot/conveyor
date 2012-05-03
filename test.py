# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:

from __future__ import (absolute_import, print_function, unicode_literals)

import argparse
import logging
import logging.config
import sys

try:
    import unittest2 as unittest
except ImportError:
    import unittest

def _main(argv):
    parser = argparse.ArgumentParser(prog='conveyor-test')
    parser.add_argument(
        '--logging',
        default=None,
        metavar='FILE')
    parser.add_argument(
        '--xml',
        action='store_true',
        default=False)
    parser.add_argument('args', nargs=argparse.REMAINDER)
    args = parser.parse_args(argv[1:])
    testrunner = None
    if None is not args.logging:
        logging.config.fileConfig(args.logging)
    if args.xml:
        import xmlrunner
        testrunner = xmlrunner.XMLTestRunner(output=str('obj/'))
    if 0 != len(args.args) and '--' == args.args[0]:
        args.args = args.args[1:]
    sys.argv[1:] = args.args
    code = unittest.main(module=None, testRunner=testrunner)
    return code

if '__main__' == __name__:
    code = _main(sys.argv)
    if None is code:
        code = 0
    sys.exit(code)
