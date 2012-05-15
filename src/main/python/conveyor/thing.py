# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:

from __future__ import (absolute_import, print_function, unicode_literals)

import conveyor.enum
import fractions
import json
import os
import os.path
import unittest

Scale = conveyor.enum.enum('Scale', Millimeter=fractions.Fraction(1, 1000))

class Manifest(object):
    @classmethod
    def frompath(cls, path):
        with open(path) as stream:
            manifest = Manifest.fromstream(stream, path)
        return manifest

    @classmethod
    def fromstream(cls, stream, path=None):
        data = json.load(stream)
        if None == path:
            base = None
        else:
            base = os.path.dirname(path)
        manifest = cls(base)
        for func in (Manifest._read_namespace, Manifest._read_constructions,
            Manifest._read_objects, Manifest._read_instances,
            Manifest._read_attribution):
                func(data, manifest)
        return manifest

    @staticmethod
    def _read_namespace(data, manifest):
        if 'namespace' not in data:
            raise Exception
        elif 'http://spec.makerbot.com/ns/thing.0.1.1.1' != data['namespace']:
            raise Exception

    @staticmethod
    def _read_objects(data, manifest):
        if 'objects' not in data:
            raise Exception
        else:
            for json_name, json_value in data['objects'].iteritems():
                manifest_object = ManifestObject._from_json(manifest,
                    json_name, json_value)
                manifest.objects[manifest_object.name] = manifest_object

    @staticmethod
    def _read_constructions(data, manifest):
        if 'constructions' not in data:
            manifest_construction = ManifestConstruction(manifest, 'plastic A')
            manifest.constructions[manifest_construction.name] = manifest_construction
        else:
            for json_name, json_value in data['constructions'].iteritems():
                manifest_construction = ManifestConstruction._from_json(
                    manifest, json_name, json_value)
                manifest.constructions[manifest_construction.name] = manifest_construction

    @staticmethod
    def _read_instances(data, manifest):
        if 'instances' not in data:
            raise Exception
        else:
            for json_name, json_value in data['instances'].iteritems():
                manifest_instance = ManifestInstance._from_json(manifest,
                    json_name, json_value)
                manifest.instances[manifest_instance.name] = manifest_instance

    @staticmethod
    def _read_attribution(data, manifest):
        if 'attribution' in data:
            manifest.attribution = data['attribution']

    def __init__(self, base=None):
        self.objects = {}
        self.constructions = {}
        self.instances = {}
        self.attribution = None
        self.base = base

    def validate(self):
        for name, manifest_object in self.objects.iteritems():
            if name != manifest_object.name:
                raise Exception
            else:
                manifest_object.validate()
        for name, manifest_construction in self.constructions.iteritems():
            if name != manifest_construction.name:
                raise Exception
            else:
                manifest_construction.validate()
        for name, manifest_instance in self.instances.iteritems():
            if name != manifest_instance.name:
                raise Exception
            else:
                manifest_instance.validate()

class ManifestItem(object):
    def __init__(self, manifest, name):
        self.manifest = manifest
        self.name = name

    def validate(self):
        raise NotImplementedError

class ManifestObject(ManifestItem):
    @classmethod
    def _from_json(cls, manifest, json_name, json_value):
        if {} != json_value:
            raise Exception
        else:
            manifest_object = ManifestObject(manifest, json_name)
            return manifest_object

    def validate(self):
        if None == self.manifest.base:
            raise Exception
        else:
            object_path = os.path.join(self.manifest.base, self.name)
            if not os.path.exists(object_path):
                raise Exception

class ManifestConstruction(ManifestItem):
    @classmethod
    def _from_json(cls, manifest, json_name, json_value):
        if {} != json_value:
            raise Exception
        else:
            manifest_construction = ManifestConstruction(manifest, json_name)
            return manifest_construction

    def validate(self):
        pass

class ManifestInstance(ManifestItem):
    @classmethod
    def _from_json(cls, manifest, json_name, json_value):
        if 'object' not in json_value:
            raise Exception
        else:
            object_key = json_value['object']
            if 'construction' not in json_value:
                construction_key = 'plastic A'
            else:
                construction_key = json_value['construction']
            if 'scale' not in json_value or 'mm' == json_value['scale']:
                scale = Scale.Millimeter
            else:
                raise Exception
            manifest_object = ManifestInstance(manifest, json_name, object_key,
                construction_key, scale)
            return manifest_object

    def __init__(self, manifest, name, object_key, construction_key, scale):
        ManifestItem.__init__(self, manifest, name)
        self.object_key = object_key
        self.construction_key = construction_key
        self.scale = scale

    @property
    def object(self):
        manifest_object = self.manifest.objects[self.object_key]
        return manifest_object

    @property
    def construction(self):
        manifest_construction = self.manifest.constructions[self.construction_key]
        return manifest_construction

    def validate(self):
        if self.object_key not in self.manifest.objects:
            raise Exception
        elif self.construction_key not in self.manifest.constructions:
            raise Exception

class _ThingTestCase(unittest.TestCase):
    def test_rfc_4_1(self):
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
