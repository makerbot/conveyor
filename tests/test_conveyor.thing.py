from __future__ import (absolute_import, print_function, unicode_literals)

import sys
sys.path.insert(0,'src/main/python') # for testing only

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from conveyor.thing import *

class _ThingTestCase(unittest.TestCase):
    def test_rfc_4_1(self):
        '''Test example 4.1 from the .thing RFC.'''

        manifest = Manifest.frompath('src/test/thing/rfc-4.1/manifest.json')

        self.assertEqual(2, len(manifest.objects))

        self.assertIn('bunny.stl', manifest.objects)
        bunny = manifest.objects['bunny.stl']
        self.assertIs(manifest, bunny.manifest)
        self.assertEqual('bunny.stl', bunny.name)

        self.assertIn('bunny2.stl', manifest.objects)
        bunny2 = manifest.objects['bunny2.stl']
        self.assertIs(manifest, bunny2.manifest)
        self.assertEqual('bunny2.stl', bunny2.name)

        self.assertEqual(2, len(manifest.constructions))

        self.assertIn('plastic A', manifest.constructions)
        plastic_a = manifest.constructions['plastic A']
        self.assertIs(manifest, plastic_a.manifest)
        self.assertEqual('plastic A', plastic_a.name)

        self.assertIn('plastic B', manifest.constructions)
        plastic_b = manifest.constructions['plastic B']
        self.assertIs(manifest, plastic_b.manifest)
        self.assertEqual('plastic B', plastic_b.name)

        self.assertEqual(2, len(manifest.instances))

        self.assertIn('NameA', manifest.instances)
        instance_a = manifest.instances['NameA']
        self.assertIs(manifest, instance_a.manifest)
        self.assertEqual('NameA', instance_a.name)
        self.assertEqual('bunny.stl', instance_a.object_key)
        self.assertIs(bunny, instance_a.object)
        self.assertEqual('plastic A', instance_a.construction_key)
        self.assertIs(plastic_a, instance_a.construction)
        self.assertEqual(Scale.Millimeter, instance_a.scale)

        self.assertIn('NameB', manifest.instances)
        instance_b = manifest.instances['NameB']
        self.assertIs(manifest, instance_b.manifest)
        self.assertEqual('NameB', instance_b.name)
        self.assertEqual('bunny2.stl', instance_b.object_key)
        self.assertIs(bunny2, instance_b.object)
        self.assertEqual('plastic B', instance_b.construction_key)
        self.assertIs(plastic_b, instance_b.construction)
        self.assertEqual(Scale.Millimeter, instance_b.scale)

    def test_rfc_5_1(self):
        '''Test example 5.1 from the .thing RFC.'''

        manifest = Manifest.frompath('src/test/thing/rfc-5.1/manifest.json')

        self.assertEqual(1, len(manifest.objects))

        self.assertIn('bunny.stl', manifest.objects)
        bunny = manifest.objects['bunny.stl']
        self.assertIs(manifest, bunny.manifest)
        self.assertEqual('bunny.stl', bunny.name)

        self.assertEqual(1, len(manifest.constructions))

        self.assertIn('plastic A', manifest.constructions)
        plastic_a = manifest.constructions['plastic A']
        self.assertIs(manifest, plastic_a.manifest)
        self.assertEqual('plastic A', plastic_a.name)

        self.assertEqual(1, len(manifest.instances))

        self.assertIn('bunny', manifest.instances)
        instance = manifest.instances['bunny']
        self.assertIs(manifest, instance.manifest)
        self.assertEqual('bunny', instance.name)
        self.assertEqual('bunny.stl', instance.object_key)
        self.assertIs(bunny, instance.object)
        self.assertEqual('plastic A', instance.construction_key)
        self.assertIs(plastic_a, instance.construction)
        self.assertEqual(Scale.Millimeter, instance.scale)

    def test_rfc_5_2(self):
        '''Test example 5.2 from the .thing RFC.'''

        manifest = Manifest.frompath('src/test/thing/rfc-5.2/manifest.json')

        self.assertEqual(2, len(manifest.objects))

        self.assertIn('bunny.stl', manifest.objects)
        bunny = manifest.objects['bunny.stl']
        self.assertIs(manifest, bunny.manifest)
        self.assertEqual('bunny.stl', bunny.name)

        self.assertIn('bunny2.stl', manifest.objects)
        bunny2 = manifest.objects['bunny2.stl']
        self.assertIs(manifest, bunny2.manifest)
        self.assertEqual('bunny2.stl', bunny2.name)

        self.assertEqual(2, len(manifest.constructions))

        self.assertIn('plastic A', manifest.constructions)
        plastic_a = manifest.constructions['plastic A']
        self.assertIs(manifest, plastic_a.manifest)
        self.assertEqual('plastic A', plastic_a.name)

        self.assertIn('plastic B', manifest.constructions)
        plastic_b = manifest.constructions['plastic B']
        self.assertIs(manifest, plastic_b.manifest)
        self.assertEqual('plastic B', plastic_b.name)

        self.assertEqual(2, len(manifest.instances))

        self.assertIn('NameA', manifest.instances)
        instance_a = manifest.instances['NameA']
        self.assertIs(manifest, instance_a.manifest)
        self.assertEqual('NameA', instance_a.name)
        self.assertEqual('bunny.stl', instance_a.object_key)
        self.assertIs(bunny, instance_a.object)
        self.assertEqual('plastic B', instance_a.construction_key)
        self.assertIs(plastic_b, instance_a.construction)
        self.assertEqual(Scale.Millimeter, instance_a.scale)

        self.assertIn('NameB', manifest.instances)
        instance_b = manifest.instances['NameB']
        self.assertIs(manifest, instance_b.manifest)
        self.assertEqual('NameB', instance_b.name)
        self.assertEqual('bunny2.stl', instance_b.object_key)
        self.assertIs(bunny2, instance_b.object)
        self.assertEqual('plastic B', instance_b.construction_key)
        self.assertIs(plastic_b, instance_b.construction)
        self.assertEqual(Scale.Millimeter, instance_b.scale)

    def test_rfc_5_3(self):
        '''Test example 5.3 from the .thing RFC.'''

        # TODO: 5.3 is identical to 4.1?

        manifest = Manifest.frompath('src/test/thing/rfc-5.3/manifest.json')

        self.assertEqual(2, len(manifest.objects))

        self.assertIn('bunny.stl', manifest.objects)
        bunny = manifest.objects['bunny.stl']
        self.assertIs(manifest, bunny.manifest)
        self.assertEqual('bunny.stl', bunny.name)

        self.assertIn('bunny2.stl', manifest.objects)
        bunny2 = manifest.objects['bunny2.stl']
        self.assertIs(manifest, bunny2.manifest)
        self.assertEqual('bunny2.stl', bunny2.name)

        self.assertEqual(2, len(manifest.constructions))

        self.assertIn('plastic A', manifest.constructions)
        plastic_a = manifest.constructions['plastic A']
        self.assertIs(manifest, plastic_a.manifest)
        self.assertEqual('plastic A', plastic_a.name)

        self.assertIn('plastic B', manifest.constructions)
        plastic_b = manifest.constructions['plastic B']
        self.assertIs(manifest, plastic_b.manifest)
        self.assertEqual('plastic B', plastic_b.name)

        self.assertEqual(2, len(manifest.instances))

        self.assertIn('NameA', manifest.instances)
        instance_a = manifest.instances['NameA']
        self.assertIs(manifest, instance_a.manifest)
        self.assertEqual('NameA', instance_a.name)
        self.assertEqual('bunny.stl', instance_a.object_key)
        self.assertIs(bunny, instance_a.object)
        self.assertEqual('plastic A', instance_a.construction_key)
        self.assertIs(plastic_a, instance_a.construction)
        self.assertEqual(Scale.Millimeter, instance_a.scale)

        self.assertIn('NameB', manifest.instances)
        instance_b = manifest.instances['NameB']
        self.assertIs(manifest, instance_b.manifest)
        self.assertEqual('NameB', instance_b.name)
        self.assertEqual('bunny2.stl', instance_b.object_key)
        self.assertIs(bunny2, instance_b.object)
        self.assertEqual('plastic B', instance_b.construction_key)
        self.assertIs(plastic_b, instance_b.construction)
        self.assertEqual(Scale.Millimeter, instance_b.scale)

    def test_rfc_5_4(self):
        '''Test example 5.4 from the .thing RFC.'''

        manifest = Manifest.frompath('src/test/thing/rfc-5.4/manifest.json')

        self.assertEqual(1, len(manifest.objects))

        self.assertIn('bunny.stl', manifest.objects)
        bunny = manifest.objects['bunny.stl']
        self.assertIs(manifest, bunny.manifest)
        self.assertEqual('bunny.stl', bunny.name)

        self.assertEqual(1, len(manifest.constructions))

        self.assertIn('plastic A', manifest.constructions)
        plastic_a = manifest.constructions['plastic A']
        self.assertIs(manifest, plastic_a.manifest)
        self.assertEqual('plastic A', plastic_a.name)

        self.assertEqual(1, len(manifest.instances))

        self.assertIn('bunny', manifest.instances)
        instance = manifest.instances['bunny']
        self.assertIs(manifest, instance.manifest)
        self.assertEqual('bunny', instance.name)
        self.assertEqual('bunny.stl', instance.object_key)
        self.assertIs(bunny, instance.object)
        self.assertEqual('plastic A', instance.construction_key)
        self.assertIs(plastic_a, instance.construction)
        self.assertEqual(Scale.Millimeter, instance.scale)

        self.assertIsNotNone(manifest.attribution)
        self.assertEqual({'author': 'Bob', 'license': 'foo'}, manifest.attribution)

if __name__ == '__main__':
    unittest.main()


