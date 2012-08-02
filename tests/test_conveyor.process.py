from __future__ import (absolute_import, print_function, unicode_literals)

import sys
sys.path.insert(0,'src/main/python') # for testing only

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from conveyor.process import * 

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
        task.runningevent.attach(func)
        process = tasksequence([task])
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
        task1 = conveyor.task.Task()
        task1.runningevent.attach(func1)
        task2 = conveyor.task.Task()
        task2.runningevent.attach(func2)
        process = tasksequence([task1, task2])
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
        process = tasksequence([task])
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
        task1 = conveyor.task.Task()
        task1.runningevent.attach(func1)
        task2 = conveyor.task.Task()
        process = tasksequence([task1, task2])
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
        process = tasksequence([task1, task2])
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
        process = tasksequence([task])
        process.start()
        process.cancel()
        self._runeventqueue(eventqueue)
        self.assertEqual(conveyor.task.TaskState.STOPPED, process.state)
        self.assertEqual(
            conveyor.task.TaskConclusion.CANCELED, process.conclusion)
        self.assertFalse(callback.delivered)

class MachineTestCase(unittest.TestCase):
    def test_abort(self):
        '''Test the abort term.'''

        term = TermTask(1)
        machine = Machine.create(term)
        machine.evaluate()
        self.assertTrue(machine.is_aborted())
        self.assertFalse(machine.is_yielded())
        self.assertEqual(1, machine.get_abort_value())

    def test_sequence(self):
        '''Test the sequence term.'''

        term = TermSequence(TermTask(1), TermTask(2))
        machine = Machine.create(term)
        machine.evaluate()
        self.assertTrue(machine.is_aborted())
        self.assertFalse(machine.is_yielded())
        self.assertEqual(2, machine.get_abort_value())

    def test_yield(self):
        '''Test the yield term.'''

        term = TermYield(TermTask(1))
        machine = Machine.create(term)
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

        term = TermSequence(
            TermYield(
                TermTask(1)),
            TermYield(
                TermTask(2)))
        machine = Machine.create(term)
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

    def test_UnknownTermException(self):
        '''Test that the machine throws an UnknownTermException when it gets
        an unknown term.

        '''

        term = 1
        phase = PhaseRefocus(term, None, None, None)
        with self.assertRaises(UnknownTermException):
            phase.refocus()

    def test_UnknownContextException(self):
        '''Test that the machine throws an UnknownContextException when it
        gets an unknown context.

        '''

        context = 1
        phase = PhaseRefocusAux(context, None, None)
        with self.assertRaises(UnknownContextException):
            phase.refocus_aux()

    def test_UnknownPhaseException(self):
        '''Test that the machine throws an UnknownPhaseException when it gets
        an unknown phase.

        '''

        phase = 1
        machine = Machine(phase)
        with self.assertRaises(UnknownPhaseException):
            machine.evaluate()

    def test_NotAbortedException(self):
        '''Test that the machine throws an NotAbortedException when
        get_abort_value() is called and the machine has not aborted.

        '''

        term = TermYield(TermTask(1))
        machine = Machine.create(term)
        machine.evaluate()
        self.assertFalse(machine.is_aborted())
        with self.assertRaises(NotAbortedException):
            machine.get_abort_value()

    def test_NotYieldedException_get_yield_value(self):
        '''Test that the machine throws a _NotYieldException when
        get_yield_value() is called and the machine is not yielded.

        '''

        term = TermTask(1)
        machine = Machine.create(term)
        machine.evaluate()
        self.assertFalse(machine.is_yielded())
        with self.assertRaises(NotYieldedException):
            machine.get_yield_value()

    def test_NotYieldedException_send(self):
        '''Test that the machine throws a NotYieldedException when send() is
        called and the machine is not yielded.

        '''

        term = TermTask(1)
        machine = Machine.create(term)
        machine.evaluate()
        self.assertFalse(machine.is_yielded())
        with self.assertRaises(NotYieldedException):
            machine.send()

if __name__ == '__main__':
    unittest.main()


