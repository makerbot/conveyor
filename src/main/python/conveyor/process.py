# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:

from __future__ import (absolute_import, print_function, unicode_literals)

import unittest

# This module is structured like a lambda calculus evaluator. The rationale is:
#
# 1. We already need something isomorphic to evaluation contexts to track
#    progress through a process. We might as well model and use evaluation
#    contexts directly.
#
# 2. In the future we might want to add control structures. This implementation
#    provides a good foundation upon which they can be built (and note that
#    there is currently *zero* code to support this future possibility).
#
# 3. It's well-known and less complicated than this description may lead you to
#    believe.
#
# It is a refocusing evaluator because the complexity of a refocusing evaluator
# is at worst the same as that of a traditional decompose/plug evaluator. It is
# usually better.
#
# It is structured as a state machine. Here states are called "phases" in order
# to avoid a terminology conflict with the world state that is threaded through
# the evaluator.
#
# Traditionally a refocusing interpreter has two states: refocus and
# refocus_aux. This implementation adds states for abort and yield.
#
# 1. _PhaseAbort
# 2. _PhaseRefocus
# 3. _PhaseRefocusAux
# 4. _PhaseYield
#
# The state machine implementation is trampolined because:
#
# 1. Python is not tail recursive (!&#!**!@).
#
# 2. We need to suspend the machine while evaluating a yield term. Yield simply
#    stores the current thunk (_PhaseYield) and exits the trampoline loop.
#
#    Threads might work, but this implementation is less complex than threads.
#    Threads would also preclude us from storing a partially evaluated process
#    on disk and resuming it in a subsequent execution of conveyor (i.e., with
#    this design we can resume a process even if your computer crashes).
#
# 3. It is almost always a mistake to tie an evaluator to the host language's
#    call stack. Here it is even more of a mistake because we need to suspend
#    the machine while evaluating a yield term.
#
# The environment represents information that is passed top-down through the
# tree of terms. Values represent information that is passed bottom-up through
# the tree of terms. The world state represents information that is passed
# through the term tree in evaluation order (which is defined as left-to-right
# for this machine).
#
# The environment and state (and frequently the values) are threaded through
# the evaluator even though they are unused. It's cheap to do now and much
# harder to retrofit later (and, from personal experience, each time I have
# omitted them from an evaluator I had to go back and add them.) This is the
# only unused code in the implementation.
#
# See:
#
#   * Refocusing in Reduction Semantics
#     http://www.brics.dk/RS/04/26/BRICS-RS-04-26.pdf

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

    def __repr__(self):
        return '_TermAbort(term=%r)' % (self.term,)

class _TermAsync(_Term):
    '''\
    The async term is a literal that evaluates to an Async value.
    '''

    # Future Implementation Note: this could be changed to a generic literal
    # term or a generic primitive literal term.

    def __init__(self, async):
        self.async = async

    def __repr__(self):
        return '_TermAsync(async=%r)' % (self.async,)

class _TermSequence(_Term):
    '''\
    The sequence term evaluates the first term, discards its value, and then
    evaluates the second term. The value of the entire term is the value of the
    second term The value of the entire term is the value of the second term.
    '''

    # Future Implementation Note: this (and the corresponding context) can be
    # removed if and when we add Abs and App.

    def __init__(self, term1, term2):
        self.term1 = term1
        self.term2 = term2

    def __repr__(self):
        return '_TermSequence(term1=%r, term2=%r)' % (self.term1, self.term2)

class _TermYield(_Term):
    '''\
    The yield term evaluates its inner term and then suspends the machine.
    '''

    def __init__(self, term):
        self.term = term

    def __repr__(self):
        return '_TermYield(term=%r)' % (self.term,)

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

    def __repr__(self):
        return '_ContextAbort()'

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

    def __repr__(self):
        return '_ContextSequence(context=%r, term=%r, environment=%r)' % (
            self.context, self.term, self.environment)

class _ContextYield(_Context):
    '''\
    The context under which a yield term is evaluated.
    '''

    def __init__(self, context):
        self.context = context

    def __repr__(self):
        return '_ContextYield(context=%r)' % (self.context,)

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

    def __repr__(self):
        return '_PhaseAbort(value=%r, state=%r)' % (self.value, self.state)

class _PhaseRefocus(_Phase):
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

        if isinstance(self.term, _TermAbort):
            new_term = self.term.term
            new_environment = self.environment
            new_context = _ContextAbort()
            new_state = self.state
            phase = _PhaseRefocus(new_term, new_environment, new_context,
                new_state)
        elif isinstance(self.term, _TermAsync):
            new_context = self.context
            new_value = self.term.async
            new_state = self.state
            phase = _PhaseRefocusAux(new_context, new_value, new_state)
        elif isinstance(self.term, _TermSequence):
            new_term = self.term.term1
            new_environment = self.environment
            new_context = _ContextSequence(self.context, self.term, self.environment)
            new_state = self.state
            phase = _PhaseRefocus(new_term, new_environment, new_context,
                new_state)
        elif isinstance(self.term, _TermYield):
            new_term = self.term.term
            new_environment = self.environment
            new_context = _ContextYield(self.context)
            new_state = self.state
            phase = _PhaseRefocus(new_term, new_environment, new_context,
                new_state)
        else:
            raise _UnknownTermException(self.term)
        return phase

    def __repr__(self):
        return '_PhaseRefocus(term=%r, environment=%r, context=%r, state=%r)' % (
            self.term, self.environment, self.context, self.state)

class _PhaseRefocusAux(_Phase):
    '''\
    This is the auxillary refocusing machine phase. It represents the 'apply'
    transition.
    '''

    def __init__(self, context, value, state):
        self.context = context
        self.value = value
        self.state = state

    def __repr__(self):
        return '_PhaseRefocusAux(context=%r, value=%r, state=%r)' % (
            self.context, self.value, self.state)

    def refocus_aux(self):
        '''\
        'refocus_aux' is the 'apply' transition function. It dispatches on
        contexts.
        '''

        if isinstance(self.context, _ContextAbort):
            phase = _PhaseAbort(self.value, self.state)
        elif isinstance(self.context, _ContextSequence):
            new_term = self.context.term.term2
            new_environment = self.context.environment
            new_context = self.context.context
            new_state = self.state
            phase = _PhaseRefocus(new_term, new_environment, new_context,
                new_state)
        elif isinstance(self.context, _ContextYield):
            phase = _PhaseYield(self.value, self.context.context, self.state)
        else:
            raise _UnknownContextException(self.context)
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

    def __repr__(self):
        return '_PhaseYield(value=%r, context=%r, state=%r)' % (self.value,
            self.context, self.state)

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
            # print('-------------------------------------------------------------------------------')
            # print(self._phase)
            if isinstance(self._phase, (_PhaseAbort, _PhaseYield)):
                break
            elif isinstance(self._phase, _PhaseRefocus):
                self._phase = self._phase.refocus()
            elif isinstance(self._phase, _PhaseRefocusAux):
                self._phase = self._phase.refocus_aux()
            else:
                raise _UnknownPhaseException(self._phase)

    def __repr__(self):
        return '_Machine(phase=%r)' % (self._phase,)

class _ProcessTestCase(unittest.TestCase):
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
        print(machine)
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
