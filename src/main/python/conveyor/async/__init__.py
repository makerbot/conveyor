# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:

from __future__ import (absolute_import, print_function, unicode_literals)

import conveyor.event
import conveyor.enum
import unittest

AsyncState = conveyor.enum.enum('AsyncState', 'PENDING', 'RUNNING',
    'SUCCESS', 'ERROR', 'TIMEOUT', 'CANCELED')

AsyncEvent = conveyor.enum.enum('AsyncEvent', 'START', 'HEARTBEAT', 'REPLY',
    'ERROR', 'TIMEOUT', 'CANCEL')

def fromfunc(func):
    import conveyor.async.glib
    async = conveyor.async.glib.fromfunc(func)
    return async

class Async(object):
    def __init__(self):
        self.state = AsyncState.PENDING
        self.start_event = conveyor.event.Event()
        self.heartbeat_event = conveyor.event.Event()
        self.reply_event = conveyor.event.Event()
        self.error_event = conveyor.event.Event()
        self.timeout_event = conveyor.event.Event()
        self.cancel_event = conveyor.event.Event()
        self.heartbeat = None
        self.reply = None
        self.error = None

    def _transition(self, event, args, kwargs):
        if AsyncState.PENDING == self.state:
            if AsyncEvent.START == event:
                self.state = AsyncState.RUNNING
                self.start_event(*args, **kwargs)
            elif AsyncEvent.CANCEL == event:
                self.state = AsyncState.CANCELED
                self.cancel_event(*args, **kwargs)
            else:
                raise IllegalTransitionException(self.state, event)
        elif AsyncState.RUNNING == self.state:
            if AsyncEvent.HEARTBEAT == event:
                self.heartbeat = (args, kwargs)
                self.heartbeat_event(*args, **kwargs)
            elif AsyncEvent.REPLY == event:
                self.state = AsyncState.SUCCESS
                self.reply = (args, kwargs)
                self.reply_event(*args, **kwargs)
            elif AsyncEvent.ERROR == event:
                self.state = AsyncState.ERROR
                self.error = (args, kwargs)
                self.error_event(*args, **kwargs)
            elif AsyncEvent.TIMEOUT == event:
                self.state = AsyncState.TIMEOUT
                self.timeout_event(*args, **kwargs)
            elif AsyncEvent.CANCEL == event:
                self.state = AsyncState.CANCELED
                self.cancel_event(*args, **kwargs)
            else:
                raise IllegalTransitionException(self.state, event)
        else:
            assert self.state in (AsyncState.SUCCESS, AsyncState.ERROR,
                AsyncState.TIMEOUT, AsyncState.CANCELED)
            if AsyncEvent.CANCEL == event:
                pass
            else:
                raise IllegalTransitionException(self.state, event)

    def _trigger_transition(self, event, args, kwargs):
        try:
            self._transition(event, args, kwargs)
        except IllegalTransitionException:
            pass

    def start(self):
        raise NotImplementedError

    def cancel(self):
        self._trigger_transition(AsyncEvent.CANCEL, (), {})

    def heartbeat_trigger(self, *args, **kwargs):
        self._trigger_transition(AsyncEvent.HEARTBEAT, args, kwargs)

    def reply_trigger(self, *args, **kwargs):
        self._trigger_transition(AsyncEvent.REPLY, args, kwargs)

    def error_trigger(self, *args, **kwargs):
        self._trigger_transition(AsyncEvent.ERROR, args, kwargs)

    def timeout_trigger(self, *args, **kwargs):
        self._trigger_transition(AsyncEvent.TIMEOUT, args, kwargs)

class IllegalTransitionException(Exception):
    def __init__(self, state, event):
        self.state = state
        self.event = event

class _AsyncTestCase(unittest.TestCase):
    def _assert_transition(self, start_state, event, expected_state):
        async = Async()
        async.state = start_state
        args = ()
        kwargs = {}
        async._transition(event, args, kwargs)
        self.assertEqual(expected_state, async.state)

    def _illegal_transition(self, state, event):
        async = Async()
        async.state = state
        args = ()
        kwargs = {}
        with self.assertRaises(IllegalTransitionException):
            async._transition(event, args, kwargs)
        self.assertEqual(state, async.state)

    def test_transition_pending(self):
        self._assert_transition(AsyncState.PENDING, AsyncEvent.START,
            AsyncState.RUNNING)
        self._assert_transition(AsyncState.PENDING, AsyncEvent.CANCEL,
            AsyncState.CANCELED)
        for event in (AsyncEvent.HEARTBEAT, AsyncEvent.REPLY,
            AsyncEvent.ERROR, AsyncEvent.TIMEOUT):
                self._illegal_transition(AsyncState.PENDING, event)

    def test_transition_running(self):
        self._illegal_transition(AsyncState.RUNNING, AsyncEvent.START)
        self._assert_transition(AsyncState.RUNNING, AsyncEvent.HEARTBEAT,
            AsyncState.RUNNING)
        self._assert_transition(AsyncState.RUNNING, AsyncEvent.REPLY,
            AsyncState.SUCCESS)
        self._assert_transition(AsyncState.RUNNING, AsyncEvent.ERROR,
            AsyncState.ERROR)
        self._assert_transition(AsyncState.RUNNING, AsyncEvent.TIMEOUT,
            AsyncState.TIMEOUT)
        self._assert_transition(AsyncState.RUNNING, AsyncEvent.CANCEL,
            AsyncState.CANCELED)

    def test_transition_ended(self):
        for state in (AsyncState.SUCCESS, AsyncState.ERROR,
            AsyncState.TIMEOUT, AsyncState.CANCELED):
                for event in (AsyncEvent.START, AsyncEvent.HEARTBEAT,
                    AsyncEvent.REPLY, AsyncEvent.ERROR, AsyncEvent.TIMEOUT):
                        self._illegal_transition(state, event)
                self._assert_transition(state, AsyncEvent.CANCEL, state)

    def test_start(self):
        async = Async()
        with self.assertRaises(NotImplementedError):
            async.start()

    def _test_trigger(self, event_name, trigger_name, value_name, expected_state):
        async = Async()
        event = getattr(async, event_name)
        callback = conveyor.event.Callback()
        event.attach(callback)
        self.assertFalse(callback.delivered)

        trigger = getattr(async, trigger_name)

        async.state = AsyncState.PENDING
        trigger(1, b=2)
        self.assertFalse(callback.delivered)
        if None != value_name:
            value = getattr(async, value_name)
            self.assertIsNone(value)

        async.state = AsyncState.RUNNING
        trigger(3, c=4)
        self.assertTrue(callback.delivered)
        self.assertEqual((3,), callback.args)
        self.assertEqual({'c':4}, callback.kwargs)
        self.assertEqual(expected_state, async.state)
        if None != value_name:
            value = getattr(async, value_name)
            self.assertEqual(((3,), {'c':4}), value)

        for state in (AsyncState.SUCCESS, AsyncState.ERROR,
            AsyncState.TIMEOUT, AsyncState.CANCELED):
                callback.reset()
                async.state = state
                trigger(5, d=6)
                self.assertFalse(callback.delivered)
                if None != value_name:
                    value = getattr(async, value_name)
                    self.assertEqual(((3,), {'c':4}), value)

    def test_heartbeat_trigger(self):
        self._test_trigger('heartbeat_event', 'heartbeat_trigger',
            'heartbeat', AsyncState.RUNNING)

    def test_reply_trigger(self):
        self._test_trigger('reply_event', 'reply_trigger', 'reply',
            AsyncState.SUCCESS)

    def test_error_trigger(self):
        self._test_trigger('error_event', 'error_trigger', 'error',
            AsyncState.ERROR)

    def test_timeout_trigger(self):
        self._test_trigger('timeout_event', 'timeout_trigger', None,
            AsyncState.TIMEOUT)

    def test_cancel(self):
        async = Async()
        callback = conveyor.event.Callback()
        async.cancel_event.attach(callback)
        self.assertFalse(callback.delivered)

        async.state = AsyncState.PENDING
        async.cancel()
        self.assertEqual(AsyncState.CANCELED, async.state)
        self.assertTrue(callback.delivered)

        async.state = AsyncState.RUNNING
        async.cancel()
        self.assertEqual(AsyncState.CANCELED, async.state)
        self.assertTrue(callback.delivered)

        for state in (AsyncState.SUCCESS, AsyncState.ERROR,
            AsyncState.TIMEOUT, AsyncState.CANCELED):
                callback.reset()
                async.state = state
                async.cancel()
                self.assertFalse(callback.delivered)
