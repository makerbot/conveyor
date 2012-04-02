# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:

from __future__ import (absolute_import, print_function, unicode_literals)

try:
    import unittest2 as unittest
except:
    import unittest

class Recipe(object):
    pass

class Dispatcher(object):
    def start(self):
        raise NotImplementedError

    def build(self, recipe, *things):
        raise NotImplementedError

class Job(object):
    def is_complete(self):
        raise NotImplementedError

    def is_successful(self):
        raise NotImplementedError

    def wait(self, timeout):
        raise NotImplementedError

class Task(object):
    pass

class SequenceTask(Task):
    pass

class ToolpathTask(Task):
    pass

class PrintTask(Task):
    pass

class DispatcherTestCase(unittest.TestCase):
    def _create_conveyor(self):
        conveyor = self._create_conveyor_celery()
        conveyor.start()
        return conveyor

    def _create_conveyor_celery(self):
        import conveyor.celery
        conveyor = conveyor.celery.CeleryDispatcher()
        return conveyor

    def _wait_for_success(self, job, timeout):
        job.wait(timeout)
        self.assertTrue(job.is_complete())
        self.assertTrue(job.is_successful())

    @unittest.skip('totally unimplemented')
    def test_single(self):
        recipe = None
        conveyor = self._create_conveyor()
        thing = {'surface': 'single.stl', 'material': 'blue',
            'extruder': 'left'}
        job = conveyor.build(recipe, thing)
        self._wait_for_success(job, 60.0)

    @unittest.skip('totally unimplemented')
    def test_dual(self):
        recipe = None
        conveyor = self._create_conveyor()
        left = {'surface': 'left.stl', 'material': 'blue',
            'extruder': 'left'}
        right = {'surface': 'right.stl', 'material': 'red',
            'extruder': 'right'}
        job = conveyor.build(recipe, left, right)
        self._wait_for_success(job, 60.0)
