# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/json.py
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

import StringIO
import decimal
import json


# Float is an abomination.
# http://stackoverflow.com/questions/1960516/python-json-serialize-a-decimal-object
class DecimalEncoder(json.JSONEncoder):
    def iterencode(self, o, *args, **kwargs):
        if isinstance(o, decimal.Decimal):
            result = (str(o),)
        else:
            result = json.JSONEncoder.iterencode(self, o, *args, **kwargs)
        return result


def dump(obj, fp, *args, **kwargs):
    kwargs[str('cls')] = DecimalEncoder
    result = json.dump(obj, fp, *args, **kwargs)
    return result


def dumps(obj, *args, **kwargs):
    kwargs[str('cls')] = DecimalEncoder
    result = json.dumps(obj, *args, **kwargs)
    return result


def loads(s, *args, **kwargs):
    '''
    A wrapper around the built-in `json.loads` that uses the `JsonReader` to
    strip comments. It supports all of the same positional and keyword
    arguments as `json.loads`.

    '''

    slot = [None]
    def callback(result):
        if None is not slot[0]:
            raise ValueError('Extra data')
        else:
            slot[0] = json.loads(result, *args, **kwargs)
    reader = JsonReader(callback, True)
    reader.feed(s)
    reader.feedeof()
    return slot[0]


def load(fp, *args, **kwargs):
    '''
    A wrapper around the built-in `json.load` that uses the `JsonReader` to
    strip comments. It supports all of the same positional and keyword
    arguments as `json.load`.

    '''

    data = fp.read()
    result = loads(data, *args, **kwargs)
    return result


# NOTES:
#
# The reader uses a (formerly) simple state machine. See
# conveyor/doc/jsonreader.{dot,png}.
#
#   S0  - handles whitespace before the top-level JSON object or array
#   S1  - handles JSON text that is not a string or comment
#   S2  - handles JSON strings
#   S3  - handles escape characters within JSON strings
#
#   S4  - handles a the first '/' of comment before the top-level JSON object
#         or array
#   S5  - handles a `//` comment before the top-level JSON object or array
#   S6  - handles a `/*` comment before the top-level JSON object or array
#   S7  - handles a `*` character within a `/*` comment before the top-level
#         JSON object or array
#
#   S8  - handles the first '/' of a comment
#   S9  - handles a `//` comment
#   S10 - handles a `/*` comment
#   S11 - handles a `*` character within a `/*` comment
#
# A stack is used in S1 to match object and array start characters to their
# respective end characters. When the stack is empty the buffer should contain
# a complete top-level object or array.
#
# Transitions to S4 and S8 are only enabled if the `strip_comments` option is
# enabled.
#
# The sub-machines {S4,S5,S6,S7} and {S8,S9,S10,S11} are identical in that they
# both handle comments except that the former handles comments before the
# top-level JSON object or array and the latter handles them after. They return
# to S0 and S1 respectively.
#
# The issue described below where if `strip_comments` is disabled and a comment
# appears before a top-level JSON object or array then each character of the
# comment is passed to the callback individually is caused by the difference in
# validation performed by S0 and S1: S0 only accepts whitespace while S1 will
# accept anything. This is a subtle effect. Changing the validation will merely
# have other subtle effects. Tread carefully.

class JsonReader(object):
    '''
    A JSON reader that can incrementally parse continuous streams of JSON
    objects or arrays and optionally strip JavaScript comments.

    The reader invokes `callback` both when it detects the end of a top-level
    JSON object or array and when it detects certain kinds of invalid input.
    The callback must be prepared to handle invalid JSON.

    `callback` is invoked under `feed` and `feedeof`. If it raises an exception
    then `feed` or `feedeof` will raise the same exception. The reader will be
    in its initial state with an empty buffer.  `callback` will not be invoked
    again until a subsequent call to `feed` or `feedeof`.

    When `strip_comments` is enabled each non-whitespace character is replaced
    by a single space. This means that line and column numbers are correct even
    when the JSON text includes tabs within comments.

    When `strip_comments` is disabled comment characters are passed to the
    callback unmodified. This can have a surprising effect if `callback` does
    not raise an exception and a comment appears before a top-level JSON object
    or array: each non-whitespace character of the comment will be sent
    individually to `callback`.

    '''

    def __init__(self, callback, strip_comments):
        self._callback = callback
        self._strip_comments = strip_comments
        self._reset()

    def _reset(self):
        '''Reset the reader.'''

        self._buffer = StringIO.StringIO()
        self._stack = []
        self._state = 0

    def _consume(self, ch):
        '''
        Update the state machine by consuming a single character of JSON text.

        '''

        # To support the invariant that the reader is in its initial state
        # whenever it invokes the callback, statements must be executed in this
        # order:
        #
        #   1. zero or more calls to self._buffer.write
        #   2. zero or one calls to self._stack.append OR zero or one calls to
        #      self._stack.pop
        #   3. zero or one assignment to self._state
        #   4. zero or one calls to self._send
        #
        # Conditionals may used freely as long as the statements ultimately
        # executed by the interpreter for a single call to _consume follow the
        # conditions above.

        if 0 == self._state:
            if ch in ('{', '['):
                self._buffer.write(ch)
                self._stack.append(ch)
                self._state = 1
            elif self._strip_comments and '/' == ch:
                self._state = 4
            elif ch not in (' ', '\t', '\n', '\r'):
                self._buffer.write(ch)
                self._send()
            else:
                self._buffer.write(ch)
        elif 1 == self._state:
            if '"' == ch:
                self._buffer.write(ch)
                self._state = 2
            elif ch in ('{', '['):
                self._buffer.write(ch)
                self._stack.append(ch)
            elif ch in ('}', ']'):
                self._buffer.write(ch)
                send = False
                if 0 == len(self._stack):
                    send = True
                else:
                    firstch = self._stack.pop()
                    if (('{' == firstch and '}' != ch)
                            or ('[' == firstch and ']' != ch)):
                        send = True
                    else:
                        send = (0 == len(self._stack))
                if send:
                    self._send()
            elif self._strip_comments and '/' == ch:
                self._state = 8
            else:
                self._buffer.write(ch)
        elif 2 == self._state:
            self._buffer.write(ch)
            if '"' == ch:
                self._state = 1
            elif '\\' == ch:
                self._state = 3
        elif 3 == self._state:
            self._buffer.write(ch)
            self._state = 2
        elif 4 == self._state:
            if '*' == ch:
                self._buffer.write(' ') # matched '/' in S0
                self._buffer.write(' ')
                self._state = 6
            elif '/' == ch:
                self._buffer.write(' ') # matched '/' in S0
                self._buffer.write(' ')
                self._state = 5
            else:
                self._buffer.write('/') # matched '/' in S0
                self._buffer.write(ch)
                self._send()
        elif 5 == self._state:
            if ch in ('\n', '\r'):
                self._buffer.write(ch)
                self._state = 0
            else:
                if '\t' == ch:
                    self._buffer.write(ch)
                else:
                    self._buffer.write(' ')
        elif 6 == self._state:
            self._buffer.write(' ')
            if '*' == ch:
                self._state = 7
        elif 7 == self._state:
            self._buffer.write(' ')
            if '/' == ch:
                self._state = 0
            else:
                self._state = 6
        elif 8 == self._state:
            if '*' == ch:
                self._buffer.write(' ') # matched '/' in S1
                self._buffer.write(' ')
                self._state = 10
            elif '/' == ch:
                self._buffer.write(' ') # matched '/' in S1
                self._buffer.write(' ')
                self._state = 9
            else:
                self._buffer.write('/') # matched '/' in S1
                self._buffer.write(ch)
                self._send()
        elif 9 == self._state:
            if ch in ('\n', '\r'):
                self._buffer.write(ch)
                self._state = 1
            else:
                if '\t' == ch:
                    self._buffer.write(ch)
                else:
                    self._buffer.write(' ')
        elif 10 == self._state:
            self._buffer.write(' ')
            if '*' == ch:
                self._state = 11
        elif 11 == self._state:
            self._buffer.write(' ')
            if '/' == ch:
                self._state = 1
            else:
                self._state = 10
        else:
            raise ValueError(self._state)

    def _send(self):
        '''
        Invokes the callback, sending it the JSON text for the current
        top-level object or array.

        This method invoked both when a complete and correct object or array is
        detected and when the state machine makes an invalid transition. The
        callback is expected to try to parse the invalid JSON and issue an
        error.

        The callback is not invoked if the JSON text consists only of
        whitespace. This accounts for whitespace that may appear between a
        top-level JSON array or object and the end of a file.

        '''

        data = self._buffer.getvalue()
        self._reset()
        if 0 != len(data.strip(' \t\n\r')):
            self._callback(data)

    def feed(self, data):
        '''Feed data to the reader.'''

        for ch in data:
            self._consume(ch)

    def feedeof(self):
        '''
        Feed an end-of-file to the reader. This simply sends the accumulated
        JSON text to the callback.

        '''

        self._send()
