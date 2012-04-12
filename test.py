# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:

from __future__ import (absolute_import, print_function, unicode_literals)

import unittest
import xmlrunner

if '__main__' == __name__:
    unittest.main(
        module=None,
        testRunner=xmlrunner.XMLTestRunner(output=str('obj/')))
