# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/process.py
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

# See conveyor/doc/process.md.

from __future__ import (absolute_import, print_function, unicode_literals)

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import conveyor.event
import conveyor.task
import conveyor.visitor

def tasksequence(job, tasklist):
    """
    @param a job object
    @param tasklist list of Task objects to run
    """
    term = reduce(
        _TermSequence, (_TermYield(_TermTask(t)) for t in tasklist))
    machine = _Machine.create(term)
    processhandler = _ProcessHandler(job, machine, job.task)

class _ProcessHandler(object):
    def __init__(self, job, machine, task):
        self._child = None
        self._job = job
        self._machine = machine
        self._task = task
        self._task.startevent.attach(self._taskstartcallback)
        self._task.cancelevent.attach(self._taskcancelcallback)

    def _next(self):
        if self._machine.is_aborted():
            result = self._child.result
            self._child = None
            self._task.end(result)
        else:
            assert self._machine.is_yielded()
            self._child = self._machine.get_yield_value()
            self._child.heartbeatevent.attach(self._childheartbeatcallback)
            self._child.endevent.attach(self._childendcallback)
            self._child.failevent.attach(self._childfailcallback)
            self._child.cancelevent.attach(self._childcancelcallback)
            self._child.start()

    def _taskstartcallback(self, unused):
        self._machine.evaluate()
        self._next()

    def _taskcancelcallback(self, unused):
        if (None is not self._child
            and conveyor.task.TaskState.STOPPED != self._child.state):
                self._child.cancel()

    def _childheartbeatcallback(self, unused):
        self._task.heartbeat(self._child)

    def _childendcallback(self, unused):
        assert self._machine.is_yielded()
        self._machine.send()
        self._next()

    def _childfailcallback(self, unused):
        failure = self._child
        self._child = None
        self._task.fail(failure)

    def _childcancelcallback(self, unused):
        if conveyor.task.TaskState.STOPPED != self._task.state:
            self._task.cancel()

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

class _TermTask(_Term):
    '''\
    The task term is a literal that evaluates to an Task value.
    '''

    # Future Implementation Note: this could be changed to a generic literal
    # term or a generic primitive literal term.

    def __init__(self, task):
        self.task = task

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

    def accept__TermTask(self, term):
        new_context = self.context
        new_value = self.term.task
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

class _ProcessTaskTestCase(unittest.TestCase):
    def _runeventqueue(self, eventqueue):
        while eventqueue.runiteration(False):
            pass

    def test_single(self):
        '''Test a process with a single task.'''

        eventqueue = conveyor.event.geteventqueue()
        callback = conveyor.event.Callback()
        self.assertFalse(callback.delivered)
        def func(task):
            callback()
            task.end(None)
        task = conveyor.task.Task()
        fakeJob = conveyor.domain.Job(None,None,None,None,None,None,None,None,None,None)
        task.runningevent.attach(func)
        process = tasksequence(fakeJob,[task])
        process.start()
        self._runeventqueue(eventqueue)
        self.assertTrue(callback.delivered)

    def test_multiple(self):
        '''Test a process with multiple tasks.'''

        eventqueue = conveyor.event.geteventqueue()
        callback1 = conveyor.event.Callback()
        callback2 = conveyor.event.Callback()
        self.assertFalse(callback1.delivered)
        self.assertFalse(callback2.delivered)
        def func1(task):
            self.assertFalse(callback1.delivered)
            self.assertFalse(callback2.delivered)
            callback1()
            task.end(None)
        def func2(task):
            self.assertTrue(callback1.delivered)
            self.assertFalse(callback2.delivered)
            callback2()
            task.end(None)

        fakeJob = conveyor.domain.Job(None,None,None,None,None,None,None,None,None,None)
        task1 = conveyor.task.Task()
        task1.runningevent.attach(func1)
        task2 = conveyor.task.Task()
        task2.runningevent.attach(func2)
        process = tasksequence(fakeJob,[task1, task2])
        process.start()
        self._runeventqueue(eventqueue)
        self.assertTrue(callback1.delivered)
        self.assertTrue(callback2.delivered)

    def test_heartbeat(self):
        '''Test process heartbeat events.'''

        eventqueue = conveyor.event.geteventqueue()
        def func(task):
            self.assertFalse(callback.delivered)
            task.heartbeat(None)
            task.end(None)
        task = conveyor.task.Task()
        task.runningevent.attach(func)
        fakeJob = conveyor.domain.Job(None,None,None,None,None,None,None,None,None,None)
        process = tasksequence(fakeJob,[task])
        callback = conveyor.event.Callback()
        process.heartbeatevent.attach(callback)
        self.assertFalse(callback.delivered)
        process.start()
        self._runeventqueue(eventqueue)
        self.assertTrue(callback.delivered)

    def test_error(self):
        '''Test process error events.'''

        eventqueue = conveyor.event.geteventqueue()
        callback1 = conveyor.event.Callback()
        callback2 = conveyor.event.Callback()
        self.assertFalse(callback1.delivered)
        self.assertFalse(callback2.delivered)
        def func1(task):
            self.assertFalse(callback1.delivered)
            self.assertFalse(callback2.delivered)
            callback1()
            task.fail(None)
        fakeJob = conveyor.domain.Job(None,None,None,None,None,None,None,None,None,None)
        task1 = conveyor.task.Task()
        task1.runningevent.attach(func1)
        task2 = conveyor.task.Task()
        process = tasksequence(fakeJob,[task1, task2])
        process.start()
        self._runeventqueue(eventqueue)
        self.assertTrue(callback1.delivered)
        self.assertFalse(callback2.delivered)

    def test_cancel_task(self):
        '''Test cancellation of a task.'''

        eventqueue = conveyor.event.geteventqueue()
        callback1 = conveyor.event.Callback()
        callback2 = conveyor.event.Callback()
        self.assertFalse(callback1.delivered)
        self.assertFalse(callback2.delivered)
        def func1(task):
            self.assertFalse(callback1.delivered)
            self.assertFalse(callback2.delivered)
            callback1()
            task.cancel()
        task1 = conveyor.task.Task()
        task1.runningevent.attach(func1)
        task2 = conveyor.task.Task()
        fakeJob = conveyor.domain.Job(None,None,None,None,None,None,None,None,None,None)
        process = tasksequence(fakeJob,[task1, task2])
        process.start()
        self._runeventqueue(eventqueue)
        self.assertTrue(callback1.delivered)
        self.assertFalse(callback2.delivered)

    def test_cancel_process(self):
        '''Test cancellation of an entire process.'''

        eventqueue = conveyor.event.geteventqueue()
        callback = conveyor.event.Callback()
        self.assertFalse(callback.delivered)
        task = conveyor.task.Task()
        fakeJob = conveyor.domain.Job(None,None,None,None,None,None,None,None,None,None)
        process = tasksequence(fakeJob,[task])
        process.start()
        process.cancel()
        self._runeventqueue(eventqueue)
        self.assertEqual(conveyor.task.TaskState.STOPPED, process.state)
        self.assertEqual(
            conveyor.task.TaskConclusion.CANCELED, process.conclusion)
        self.assertFalse(callback.delivered)

class _MachineTestCase(unittest.TestCase):
    def test_abort(self):
        '''Test the abort term.'''

        term = _TermTask(1)
        machine = _Machine.create(term)
        machine.evaluate()
        self.assertTrue(machine.is_aborted())
        self.assertFalse(machine.is_yielded())
        self.assertEqual(1, machine.get_abort_value())

    def test_sequence(self):
        '''Test the sequence term.'''

        term = _TermSequence(_TermTask(1), _TermTask(2))
        machine = _Machine.create(term)
        machine.evaluate()
        self.assertTrue(machine.is_aborted())
        self.assertFalse(machine.is_yielded())
        self.assertEqual(2, machine.get_abort_value())

    def test_yield(self):
        '''Test the yield term.'''

        term = _TermYield(_TermTask(1))
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
        '''Test a sequence of yield terms.'''

        term = _TermSequence(
            _TermYield(
                _TermTask(1)),
            _TermYield(
                _TermTask(2)))
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
        '''Test that the machine throws an _UnknownTermException when it gets
        an unknown term.

        '''

        term = 1
        phase = _PhaseRefocus(term, None, None, None)
        with self.assertRaises(_UnknownTermException):
            phase.refocus()

    def test__UnknownContextException(self):
        '''Test that the machine throws an _UnknownContextException when it
        gets an unknown context.

        '''

        context = 1
        phase = _PhaseRefocusAux(context, None, None)
        with self.assertRaises(_UnknownContextException):
            phase.refocus_aux()

    def test__UnknownPhaseException(self):
        '''Test that the machine throws an _UnknownPhaseException when it gets
        an unknown phase.

        '''

        phase = 1
        machine = _Machine(phase)
        with self.assertRaises(_UnknownPhaseException):
            machine.evaluate()

    def test__NotAbortedException(self):
        '''Test that the machine throws an _NotAbortedException when
        get_abort_value() is called and the machine has not aborted.

        '''

        term = _TermYield(_TermTask(1))
        machine = _Machine.create(term)
        machine.evaluate()
        self.assertFalse(machine.is_aborted())
        with self.assertRaises(_NotAbortedException):
            machine.get_abort_value()

    def test__NotYieldedException_get_yield_value(self):
        '''Test that the machine throws a _NotYieldException when
        get_yield_value() is called and the machine is not yielded.

        '''

        term = _TermTask(1)
        machine = _Machine.create(term)
        machine.evaluate()
        self.assertFalse(machine.is_yielded())
        with self.assertRaises(_NotYieldedException):
            machine.get_yield_value()

    def test__NotYieldedException_send(self):
        '''Test that the machine throws a _NotYieldedException when send() is
        called and the machine is not yielded.

        '''

        term = _TermTask(1)
        machine = _Machine.create(term)
        machine.evaluate()
        self.assertFalse(machine.is_yielded())
        with self.assertRaises(_NotYieldedException):
            machine.send()
