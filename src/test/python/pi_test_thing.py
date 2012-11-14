import unittest

import sys
import os
import mock

#override sys.path for testing only 
sys.path.insert(0,'./src/main/python')
import conveyor
import conveyor.thing
from conveyor.thing import Manifest, ManifestItem, Scale
from conveyor.thing import ManifestObject, ManifestConstruction, ManifestInstance

class TestManifestSubitems(unittest.TestCase):
    def test_manifest_base(self):
        x = ManifestItem(None,None)
        self.assertEquals(x.manifest,None)
        self.assertEquals(x.name,'Unnamed Manifest Item')
        with self.assertRaises(Exception):
            x.validate() # invalid, no parent manifest with a 'base' value

    def test_manifest_construction(self):
        x = ManifestConstruction(None,None)
        self.assertEquals(x.manifest,None)
        self.assertEquals(x.name,'Unnamed Manifest Item')
        with self.assertRaises(Exception):
            x.validate() # invalid, no parent manifest with a 'base' value

    def test_manifest_instance(self):
        x = ManifestInstance(None,None,None,None,None)
        self.assertEquals(x.manifest,None)
        self.assertEquals(x.name,'Unnamed Manifest Item')
        with self.assertRaises(Exception):
            x.validate() # invalid, no parent manifest with a 'base' value

    def test_manifest_Object(self):
        x = ManifestObject(None,None)
        self.assertEquals(x.manifest,None)
        self.assertEquals(x.name,'Unnamed Manifest Item')
        with self.assertRaises(Exception):
            x.validate() # invalid, no parent manifest with a 'base' value

    def test_manifest_insntace_factory(self):
        json_name, json_value = {'foo':'bar'},{'baz':'fuzz'}
        with self.assertRaises(Exception):
           x = ManifestConstruction._from_json(None,json_name, json_value)
        mock_parent = mock.Mock()
        mock_parent.manifest  = mock.Mock()
        mock_parent.manifest.base  = mock.Mock()
        x = ManifestConstruction._from_json(mock_parent,json_name,{}) 
        x.validate()

class _ThingTestCase(unittest.TestCase):
    def test_read_fails(self):
        # construct base manifest 
        manifest = Manifest.frompath('src/test/thing/rfc-4.1/manifest.json')
        manifest.validate()

        #munge the internal json dir, remove 'objects' and and run read_objects 
        rawJson = manifest.rawJson
        del manifest.rawJson['objects']
        with self.assertRaises(Exception):
            manifest._read_objects() # expceted to raise exception, no 'objects'
        manifest.validate()

        #munge the internal json dir, remove 'instances' and and run read_objects 
        del manifest.rawJson['instances']
        with self.assertRaises(Exception):
            manifest._read_instances() # expceted to raise exception, no 'objects'
        manifest.validate()

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

        manifest._validate_namespace() #throws exception on failure

        materials = manifest.material_types()
        self.assertTrue('plastic B' in materials)
        self.assertTrue('plastic A' in materials)

        manifest.rawJson['namespace'] = "unknown"
        with self.assertRaises(Exception):
            manifest._validate_namespace() # expects to throw, namespace name invalid
        del manifest.rawJson['namespace'] 
        with self.assertRaises(Exception):
            manifest._validate_namespace() # expects to throw, missing namespace

                
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
        self.assertEqual(
            {'author': 'Bob', 'license': 'foo'}, manifest.attribution)

    def test_rfc_5_4_hack(self):
        '''Test undocumented hack for the unified mesh hack.'''

        #verify function works for hacky files
        manifest = Manifest.frompath('src/test/thing/rfc-5.4-hack/manifest.json')
        manifest._read_unified_mesh_hack()
        self.assertIsNotNone(manifest.unified_mesh_hack)

class TestManifestInstance(unittest.TestCase):
        def test_manifest_instance(self):
            manifest = Manifest.frompath('src/test/thing/rfc-4.1/manifest.json')
            #mani_inst = manifest._read_instance(data,manifest)
            #mani_int.validate()
               

if __name__ == "__main__":
    unittest.main()


