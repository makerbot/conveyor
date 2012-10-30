# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/thing.py
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

import conveyor.enum
import fractions
import json
import os
import os.path

Scale = conveyor.enum.enum('Scale', Millimeter=fractions.Fraction(1, 1000))


class ManifestItem(object):
    """ Base of all Manifest objects.
    @param parent manifest, if one is available
    @param name, default to an unnamed string if None
    """
    def __init__(self, manifest, name=None):
        """@param manifest parent manifest object
        @param name name of this object """
        self.manifest = manifest
        self.name = name if name is not None else 'Unnamed Manifest Item'

    def validate(self):
        if None == self.manifest or None == self.manifest.base:
            raise Exception("%s requires a parent manifest to be valid" %self.__class__)



class Manifest(object):

    
    @staticmethod
    def frompath(path):
        """ 
        @param path a path to a json file in a manifest
        @return a Manifest constructed from the json .thing manifest at the path 
        """
        with open(path) as stream:
            return Manifest.fromstream(stream, path)

    @classmethod
    def fromstream(cls, stream, path=None):
        data = json.load(stream)
        base = None
        if None is not path:
            base = os.path.dirname(path)
        manifest = Manifest(data, base)
        manifest._validate_namespace() 
        manifest._read_constructions()
        manifest._read_objects()
        manifest._read_instances()
        manifest._read_attribution()
        return manifest        

    def __init__(self, rawJson, base=None):
        self.objects = {}
        self.constructions = {}
        self.instances = {}
        self.attribution = None
        self.base = base
        self.unified_mesh_hack =None
        self.rawJson = rawJson

    def _validate_namespace(self):
        """ @return True on success, throws exception otherwise. """
        if 'namespace' not in self.rawJson:
            raise Exception("No namespace specified. Format invalid")
        elif 'http://spec.makerbot.com/ns/thing.0.1.1.1' != self.rawJson['namespace']:
            raise Exception


    def _read_objects(self):
        """ @raises Exception of no objects in data """ 
        if 'objects' not in self.rawJson:
            raise Exception("no object defined in this manifest")
        else:
            for json_name, json_value in self.rawJson['objects'].iteritems():
                manifest_object = ManifestObject._from_json(self,
                                                            json_name, json_value)
                self.objects[manifest_object.name] = manifest_object

    def _read_constructions(self):
        if 'constructions' not in self.rawJson:
            manifest_construction = ManifestConstruction(self, 'plastic A')
            self.constructions[
                manifest_construction.name] = manifest_construction
        else:
            for json_name, json_value in self.rawJson['constructions'].iteritems():
                manifest_construction = ManifestConstruction._from_json(
                    self , json_name, json_value)
                self.constructions[
                    manifest_construction.name] = manifest_construction

    def _read_instances( self ):
        if 'instances' not in self.rawJson:
            raise Exception
        else:
            for json_name, json_value in self.rawJson['instances'].iteritems():
                manifest_instance = ManifestInstance._from_json(self,
                                                                json_name, json_value)
                self.instances[manifest_instance.name] = manifest_instance

    def _read_attribution( self):
        if 'attribution' in self.rawJson:
            self.attribution = self.rawJson['attribution']

    def _read_unified_mesh_hack(self):
        """ due to needing a unified mesh for our beta release,
        we added this undocumented entry. This entry contains an entire
        print plate, in one material, as a single giant stl mesh, since
        the math for multiple object platcement was incomplete at ship time"""
        if 'UNIFIED_MESH_HACK' in self.rawJson:
            self.unified_mesh_hack = self.rawJson['UNIFIED_MESH_HACK']
        

    def validate(self):
        """ valides this Manifest, and all objects contained in it.
        raises exception on failure, no return on success 
        """
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

    def material_types(self):
        """ returns a set of all material types found in this manifest, as a list """
        l = []
        for k in self.instances.keys():
            l.append(self.instances[k].construction_key)
        setMaterials = set(l)
        return list(setMaterials)


class ManifestObject(ManifestItem):
    @classmethod
    def _from_json(cls, manifest, json_name, json_value):
        """ @param manifest container manifest """
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
    """ a Manifest Construciton defines what way an item is constructed """
    @classmethod
    def _from_json(cls, manifest, json_name, json_value):
        """ @param manifest container manifest """
        if {} != json_value:
            raise Exception("json_value not empty in %s" %cls.__class__)
        manifest_construction = ManifestConstruction(manifest, json_name)
        return manifest_construction


class ManifestInstance(ManifestItem):
    """ Represents an instance of an item specified in a manifest. That object
    MUST have a scale, object-key (ie, what mesh it is), and a construction (ie
    how to create the instance
    """

    @classmethod
    def _from_json(cls, manifest, json_name, json_value):
        """ @param manifest container manifest """
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
                raise Exception("undocumneted exception in %s", self.__class__)

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
        manifest_construction = self.manifest.constructions[
            self.construction_key]
        return manifest_construction

    def validate(self):
        """ validates the instance. 
        @return true on success, throws exception otherwise
        """
        if self.object_key not in self.manifest.objects:
            raise Exception
        elif self.construction_key not in self.manifest.constructions:
            raise Exception

