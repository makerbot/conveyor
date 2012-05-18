Coding Standards
================

* [PEP-8](http://www.python.org/dev/peps/pep-0008/)
* [PEP-257](http://www.python.org/dev/peps/pep-0257/)
* [Mercurial Coding Style](http://mercurial.selenic.com/wiki/CodingStyle)

The overall structure of a file should be:

1. header
2. imports
3. classes and functions
4. unit tests
5. main (only for conveyor/\_\_main\_\_.py)

The standard header is:

    # vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
    # conveyor/path/to/file.extension
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

The import order is (from PEP-8):

1. standard library imports
2. related third party imports
3. local application/library specific imports

For brevity, imports of conveyor modules may be written like this:

    from conveyor import enum, event

Never use "from module import \*". Always list explicitly the names being
imported.

Identifier names should follow the Mercurial convention: all lowercase, with no
underbars between words. The exception to this rule is test methods. They
should start with the prefix `test_` and should use an underscore whenever a
variant suffix is appended to the test name:

    class ExampleTestCase(unittest.TestCase):
        def test_method(self):
            ...

        def test_method_ValueError(self):
            with self.assertRaises(ValueError):
                ...

Don't do work in constructors. They must contain *only* trivial assignment
statements and calls to other constructors. Use a `@classmethod` or
`@staticmethod` when you need to execute more complicated code during the
construction of an object (a.k.a a named constructor):

    class Example(object):
        @classmethod
        def create(cls, parameter):
            value = something(parameter)
            example = cls(value)
            return example

        def __init__(self, value):
            self.value = value

It is also acceptable to invoke a 'reset' method from the constructor:

    class Example(object):
        def __init__(self):
            self._reset()

        def _reset(self):
            self.value = 0

        def something(self):
            if condition:
                self._reset()

The named constructor pattern can be used to enforce initialization
requirements:

    class Example(object):
        @classmethod
        def create(cls):
            example = cls()
            example._initialize()
            return example

        def __init__(self):
            self.value = None

        def _initialize(self):
            self.value = something()

When a class has only a single named constructor, it should be called `create`.
When there is more than one, each named constructor should have a descriptive
name:

    class Example(object):
        @classmethod
        def frompath(cls, path):
            ...

        @classmethod
        def fromstream(cls, stream):
            ...

Avoid both multiple inheritance and `super`.

When testing for equality, literals and other constant values should appear on
the left hand of the `==` operator:

    if 1 == x:
       ...

Contrary to PEP 8, the preferred place to break around a binary operator is
*before* the operator, not after it.

<!-- vim:set ai et fenc=utf-8 ff=unix sw=4 syntax=markdown ts=4: -->
