# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:

# See conveyor/doc/process.md.

from __future__ import (absolute_import, print_function, unicode_literals)

import conveyor.async
import conveyor.event
import conveyor.visitor
try:
    import unittest2 as unittest
except ImportError:
    import unittest

def asyncsequence(async_list):
    async = _ProcessAsync.create(async_list)
    return async

class _ProcessAsync(conveyor.async.Async):
    @classmethod
    def create(cls, async_list):
        term = reduce(_TermSequence,
            (_TermYield(_TermAsync(a)) for a in async_list))
        machine = _Machine.create(term)
        async = _ProcessAsync(machine)
        return async

    def __init__(self, machine):
        conveyor.async.Async.__init__(self)
        self._machine = machine
        self._async = None

    def _heartbeat_handler(self, *args, **kwargs):
        self.heartbeat_trigger(*args, **kwargs)

    def _reply_handler(self, *args, **kwargs):
        assert self._machine.is_yielded()
        self._machine.send()
        self._reply_or_next()

    def _error_handler(self, *args, **kwargs):
        self.error_trigger(*args, **kwargs)

    def _timeout_handler(self, *args, **kwargs):
        self.timeout_trigger(*args, **kwargs)

    def _cancel_handler(self, *args, **kwargs):
        self.cancel()

    def _reply_or_next(self):
        self._async = None
        if self._machine.is_aborted():
            self.reply_trigger()
        else:
            assert self._machine.is_yielded()
            self._async = self._machine.get_yield_value()
            self._async.heartbeat_event.attach(self._heartbeat_handler)
            self._async.reply_event.attach(self._reply_handler)
            self._async.error_event.attach(self._error_handler)
            self._async.timeout_event.attach(self._timeout_handler)
            self._async.cancel_event.attach(self._cancel_handler)
            self._async.start()

    def start(self):
        self._transition(conveyor.async.AsyncEvent.START, (), {})
        self._machine.evaluate()
        self._reply_or_next()

    def wait(self):
        if conveyor.async.AsyncState.PENDING == self.state:
            self.start()
        while self.state not in (conveyor.async.AsyncState.SUCCESS,
            conveyor.async.AsyncState.ERROR, conveyor.async.AsyncState.TIMEOUT,
            conveyor.async.AsyncState.CANCELED):
                self._async.wait()

    def cancel(self):
        self._transition(conveyor.async.AsyncEvent.CANCEL, (), {})
        if None != self._async:
            self._async.cancel()

class _Term(object):
    '''\
    An abstract term.
    '''
    pass

class _TermAbort(_Term):
    '''\
    The abort term evaluates its inner term and then aborts the process and
    returns the inner term value. It does not necessarily indicate an error,
    only termination of the process.
    '''

    def __init__(self, term):
        self.term = term

class _TermAsync(_Term):
    '''\
    The async term is a literal that evaluates to an Async value.
    '''

    # Future Implementation Note: this could be changed to a generic literal
    # term or a generic primitive literal term.

    def __init__(self, async):
        self.async = async

class _TermSequence(_Term):
    '''\
    The sequence term evaluates the first term, discards its value, and then
    evaluates the second term. The value of the entire term is the value of the
    second term.
    '''

    # Future Implementation Note: this (and the corresponding context) can be
    # removed if and when we add Abs and App.

    def __init__(self, term1, term2):
        self.term1 = term1
        self.term2 = term2

class _TermYield(_Term):
    '''\
    The yield term evaluates its inner term and then suspends the machine.
    '''

    def __init__(self, term):
        self.term = term

class _Context(object):
    '''\
    An abstract evaluation context. Evaluation contexts with limited
    functionality are often called "stack frames".
    '''
    pass

class _ContextAbort(_Context):
    '''\
    The context under which an abort term is evaluated. This context is special
    as it has no enclosing context. If it is evaluated under an enclosing
    context, that enclosing context is discarded.
    '''

class _ContextSequence(_Context):
    '''\
    The context under which a sequence term is evaluated.
    '''

    # Future Implementation Note: this (and the corresponding term) can be
    # removed if and when we add Abs and App.

    def __init__(self, context, term, environment):
        self.context = context
        self.term = term
        self.environment = environment

class _ContextYield(_Context):
    '''\
    The context under which a yield term is evaluated.
    '''

    def __init__(self, context):
        self.context = context

class _Phase(object):
    '''\
    An abstract machine phase. Normally this would be called a 'state', but we
    use the word 'phase' here to avoid a terminology conflict with the world
    state that is threaded through the machine.
    '''
    pass

class _PhaseAbort(_Phase):
    '''\
    This is the machine phase after an abort term is fully evaluated. The
    machine cannot proceed after this phase.
    '''

    def __init__(self, value, state):
        self.value = value
        self.state = state

class _PhaseRefocus(_Phase, conveyor.visitor.Visitor):
    '''\
    This is the refocusing machine phase. It represents the 'eval' transition.
    '''

    def __init__(self, term, environment, context, state):
        self.term = term
        self.environment = environment
        self.context = context
        self.state = state

    def refocus(self):
        '''\
        'refocus' is the 'eval' transition function. It dispatches on closures
        (which are explicitly stored here as two fields, 'term' and
        'environment').
        '''

        try:
            phase = self.visit(self.term)
            return phase
        except conveyor.visitor.NoAcceptorException:
            raise _UnknownTermException(self.term)

    def accept__TermAbort(self, term):
        new_term = self.term.term
        new_environment = self.environment
        new_context = _ContextAbort()
        new_state = self.state
        phase = _PhaseRefocus(new_term, new_environment, new_context,
            new_state)
        return phase

    def accept__TermAsync(self, term):
        new_context = self.context
        new_value = self.term.async
        new_state = self.state
        phase = _PhaseRefocusAux(new_context, new_value, new_state)
        return phase

    def accept__TermSequence(self, term):
        new_term = self.term.term1
        new_environment = self.environment
        new_context = _ContextSequence(self.context, self.term,
            self.environment)
        new_state = self.state
        phase = _PhaseRefocus(new_term, new_environment, new_context,
            new_state)
        return phase

    def accept__TermYield(self, term):
        new_term = self.term.term
        new_environment = self.environment
        new_context = _ContextYield(self.context)
        new_state = self.state
        phase = _PhaseRefocus(new_term, new_environment, new_context,
            new_state)
        return phase

class _PhaseRefocusAux(_Phase, conveyor.visitor.Visitor):
    '''\
    This is the auxillary refocusing machine phase. It represents the 'apply'
    transition.
    '''

    def __init__(self, context, value, state):
        self.context = context
        self.value = value
        self.state = state

    def refocus_aux(self):
        '''\
        'refocus_aux' is the 'apply' transition function. It dispatches on
        contexts.
        '''

        try:
            phase = self.visit(self.context)
            return phase
        except conveyor.visitor.NoAcceptorException:
            raise _UnknownContextException(self.context)

    def accept__ContextAbort(self, context):
        phase = _PhaseAbort(self.value, self.state)
        return phase

    def accept__ContextSequence(self, context):
        new_term = self.context.term.term2
        new_environment = self.context.environment
        new_context = self.context.context
        new_state = self.state
        phase = _PhaseRefocus(new_term, new_environment, new_context,
            new_state)
        return phase

    def accept__ContextYield(self, context):
        phase = _PhaseYield(self.value, self.context.context, self.state)
        return phase

class _PhaseYield(_Phase):
    '''\
    This is the yield phase. It suspends the machine and produces a value.
    '''

    def __init__(self, value, context, state):
        self.value = value
        self.context = context
        self.state = state

    def send(self, value):
        phase = _PhaseRefocusAux(self.context, value, self.state)
        return phase

class _InternalException(Exception):
    '''\
    This class represents exceptions internal to this module. This exception
    and those derived from it indicate an internal implementation error.
    '''
    pass

class _UnknownTermException(_InternalException):
    '''\
    The evaluator throws this exception when it encounters an unknown term. It
    indicates an internal implementation error.
    '''

    def __init__(self, unknown_term):
        _InternalException.__init__(self, unknown_term)
        self.unknown_term = unknown_term

class _UnknownContextException(_InternalException):
    '''\
    The evaluator throws this exception when it encounters an unknown context.
    It indicates an internal implementation error.
    '''

    def __init__(self, unknown_context):
        _InternalException.__init__(self, unknown_context)
        self.unknown_context = unknown_context

class _UnknownPhaseException(_InternalException):
    '''\
    The evaluator throws this exception when it encounters an unknown phase. It
    indicates an internal implementation error.
    '''

    def __init__(self, unknown_phase):
        _InternalException.__init__(self, unknown_phase)
        self.unknown_phase = unknown_phase

class _NotAbortedException(_InternalException):
    '''\
    The evaluator throws this exception when '_Machine.get_abort_value' is
    called and the current phase is not a '_PhaseAbort'. It indicates an
    internal implementation error.
    '''

class _NotYieldedException(_InternalException):
    '''\
    The evaluator throws this exception when '_Machine.get_yield_value' is
    called and the current phase is not a '_PhaseYield'. It indicates an
    internal implementation error.
    '''

class _Machine(object):
    @classmethod
    def create(cls, term):
        initial_term = _TermAbort(term)
        initial_environment = None
        initial_context = None
        initial_state = None
        phase = _PhaseRefocus(initial_term, initial_environment,
            initial_context, initial_state)
        machine = _Machine(phase)
        return machine

    def __init__(self, phase):
        self._phase = phase

    def is_aborted(self):
        result = isinstance(self._phase, _PhaseAbort)
        return result

    def get_abort_value(self):
        if not self.is_aborted():
            raise _NotAbortedException
        else:
            value = self._phase.value
            return value

    def is_yielded(self):
        result = isinstance(self._phase, _PhaseYield)
        return result

    def get_yield_value(self):
        if not self.is_yielded():
            raise _NotYieldedException
        else:
            value = self._phase.value
            return value

    def evaluate(self):
        self._trampoline()

    def send(self, value=None):
        if not isinstance(self._phase, _PhaseYield):
            raise _NotYieldedException
        else:
            self._phase = self._phase.send(value)
            self._trampoline()

    def _trampoline(self):
        while True:
            if isinstance(self._phase, (_PhaseAbort, _PhaseYield)):
                break
            elif isinstance(self._phase, _PhaseRefocus):
                self._phase = self._phase.refocus()
            elif isinstance(self._phase, _PhaseRefocusAux):
                self._phase = self._phase.refocus_aux()
            else:
                raise _UnknownPhaseException(self._phase)

class _ProcessAsyncTestCase(unittest.TestCase):
    def test_single(self):
        callback = conveyor.event.Callback()
        self.assertFalse(callback.delivered)
        def func(async):
            callback()
            async.reply_trigger()
        async = conveyor.async.asyncfunc(func)
        process = conveyor.async.asyncsequence([async])
        process.start()
        self.assertTrue(callback.delivered)

    def test_multiple(self):
        callback1 = conveyor.event.Callback()
        callback2 = conveyor.event.Callback()
        self.assertFalse(callback1.delivered)
        self.assertFalse(callback2.delivered)
        def func1(async):
            self.assertFalse(callback1.delivered)
            self.assertFalse(callback2.delivered)
            callback1()
            async.reply_trigger()
        def func2(async):
            self.assertTrue(callback1.delivered)
            self.assertFalse(callback2.delivered)
            callback2()
            async.reply_trigger()
        async1 = conveyor.async.asyncfunc(func1)
        async2 = conveyor.async.asyncfunc(func2)
        process = conveyor.async.asyncsequence([async1, async2])
        process.start()
        self.assertTrue(callback1.delivered)
        self.assertTrue(callback2.delivered)

    def test_heartbeat(self):
        def func(async):
            self.assertFalse(callback.delivered)
            async.heartbeat_trigger()
            async.reply_trigger()
        async = conveyor.async.asyncfunc(func)
        process = conveyor.async.asyncsequence([async])
        callback = conveyor.event.Callback()
        process.heartbeat_event.attach(callback)
        self.assertFalse(callback.delivered)
        process.start()
        self.assertTrue(callback.delivered)

    def test_error(self):
        callback1 = conveyor.event.Callback()
        callback2 = conveyor.event.Callback()
        self.assertFalse(callback1.delivered)
        self.assertFalse(callback2.delivered)
        def func1(async):
            self.assertFalse(callback1.delivered)
            self.assertFalse(callback2.delivered)
            callback1()
            async.error_trigger()
        async1 = conveyor.async.asyncfunc(func1)
        async2 = conveyor.async.asyncfunc(None) # not actually called
        process = conveyor.async.asyncsequence([async1, async2])
        process.start()
        self.assertTrue(callback1.delivered)
        self.assertFalse(callback2.delivered)

    def test_timeout(self):
        callback1 = conveyor.event.Callback()
        callback2 = conveyor.event.Callback()
        self.assertFalse(callback1.delivered)
        self.assertFalse(callback2.delivered)
        def func1(async):
            self.assertFalse(callback1.delivered)
            self.assertFalse(callback2.delivered)
            callback1()
            async.timeout_trigger()
        async1 = conveyor.async.asyncfunc(func1)
        async2 = conveyor.async.asyncfunc(None) # not actually called
        process = conveyor.async.asyncsequence([async1, async2])
        process.start()
        self.assertTrue(callback1.delivered)
        self.assertFalse(callback2.delivered)

    def test_cancel_async(self):
        callback1 = conveyor.event.Callback()
        callback2 = conveyor.event.Callback()
        self.assertFalse(callback1.delivered)
        self.assertFalse(callback2.delivered)
        def func1(async):
            self.assertFalse(callback1.delivered)
            self.assertFalse(callback2.delivered)
            callback1()
            async.cancel()
        async1 = conveyor.async.asyncfunc(func1)
        async2 = conveyor.async.asyncfunc(None) # not actually called
        process = conveyor.async.asyncsequence([async1, async2])
        process.start()
        self.assertTrue(callback1.delivered)
        self.assertFalse(callback2.delivered)

    def test_cancel_process(self):
        callback = conveyor.event.Callback()
        self.assertFalse(callback.delivered)
        async = conveyor.async.asyncfunc(None) # not actually called
        process = conveyor.async.asyncsequence([async])
        process.cancel()
        self.assertEqual(conveyor.async.AsyncState.CANCELED, process.state)
        self.assertFalse(callback.delivered)

class _MachineTestCase(unittest.TestCase):
    def test_abort(self):
        term = _TermAsync(1)
        machine = _Machine.create(term)
        machine.evaluate()
        self.assertTrue(machine.is_aborted())
        self.assertFalse(machine.is_yielded())
        self.assertEqual(1, machine.get_abort_value())

    def test_sequence(self):
        term = _TermSequence(_TermAsync(1), _TermAsync(2))
        machine = _Machine.create(term)
        machine.evaluate()
        self.assertTrue(machine.is_aborted())
        self.assertFalse(machine.is_yielded())
        self.assertEqual(2, machine.get_abort_value())

    def test_yield(self):
        term = _TermYield(_TermAsync(1))
        machine = _Machine.create(term)
        machine.evaluate()
        self.assertFalse(machine.is_aborted())
        self.assertTrue(machine.is_yielded())
        self.assertEqual(1, machine.get_yield_value())
        machine.send(2)
        self.assertTrue(machine.is_aborted())
        self.assertFalse(machine.is_yielded())
        self.assertEqual(2, machine.get_abort_value())

    def test_sequence_yield(self):
        term = _TermSequence(
            _TermYield(
                _TermAsync(1)),
            _TermYield(
                _TermAsync(2)))
        machine = _Machine.create(term)
        machine.evaluate()
        self.assertFalse(machine.is_aborted())
        self.assertTrue(machine.is_yielded())
        self.assertEqual(1, machine.get_yield_value())
        machine.send('xyzzy')
        self.assertFalse(machine.is_aborted())
        self.assertTrue(machine.is_yielded())
        self.assertEqual(2, machine.get_yield_value())
        machine.send(3)
        self.assertTrue(machine.is_aborted())
        self.assertFalse(machine.is_yielded())
        self.assertEqual(3, machine.get_abort_value())

    def test__UnknownTermException(self):
        term = 1
        phase = _PhaseRefocus(term, None, None, None)
        with self.assertRaises(_UnknownTermException):
            phase.refocus()

    def test__UnknownContextException(self):
        context = 1
        phase = _PhaseRefocusAux(context, None, None)
        with self.assertRaises(_UnknownContextException):
            phase.refocus_aux()

    def test__UnknownPhaseException(self):
        phase = 1
        machine = _Machine(phase)
        with self.assertRaises(_UnknownPhaseException):
            machine.evaluate()

    def test__NotAbortedException(self):
        term = _TermYield(_TermAsync(1))
        machine = _Machine.create(term)
        machine.evaluate()
        self.assertFalse(machine.is_aborted())
        with self.assertRaises(_NotAbortedException):
            machine.get_abort_value()

    def test__NotYieldedException_get_yield_value(self):
        term = _TermAsync(1)
        machine = _Machine.create(term)
        machine.evaluate()
        self.assertFalse(machine.is_yielded())
        with self.assertRaises(_NotYieldedException):
            machine.get_yield_value()

    def test__NotYieldedException_send(self):
        term = _TermAsync(1)
        machine = _Machine.create(term)
        machine.evaluate()
        self.assertFalse(machine.is_yielded())
        with self.assertRaises(_NotYieldedException):
            machine.send()
