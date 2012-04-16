Makerbot Industries RFC 03: Multi-object file with object meta-info

* Doc Revision: 0.1.0.0
* Protocol Revision: 0.1.0.0

# Abstract:
A file format that can be used to facilitate transfer of properly-attributed designs for physical objects, and how they should be constructed. This may include information at various levels of detail, from simple shape data, to material types, temperatures, full toolpaths, etc. It may also contain information about the chain of attribution for objects, and possibly the other meta-info as well.

## 0. Terms (just a few):
* `.json` - A JavaScript Object Notation file (see [RFC-4627](http://www.ietf.org/rfc/rfc4627.txt))
* meta-info - I'm using this to refer to any information that describes the process of making the object, but there could be room for specifying expected properties of objects (for smarter slicing) or other things.

## 1. Goals:
* To have a way to store objects arranged on a build plate
* To store information about how those objects should be created
* To track the chains of attribution for objects
* Openness? By keeping the format clear/simple we make it easier for us and them to develop against it.
* Extensibility. This RFC should help define version 0.1.0.0 of this file format, but should leave the format flexible enough that future details can be added.

## 2. Uses Cases:
* User uploads a `.thing` file to thingiverse to share.
* User uploads an `.stl` to thingiverse which is converted to `.thing`.
* User downloads a `.thing` file from thingiverse for printing.
* User downloads a `.thing` file from thingiverse for editing.
* User creates a plate of things, assigns colors, toolheads, etc., saves as `.thing`.

## 3. Overview::
This format consists of files stored in a folder. The folder MAY contain one or more files describing one or more 3D solid geometries and one or more `.json` files with details about those geometries. The file MUST contain exactly one well specified `.json` file named `manifest.json` with information about the other files stored in the `.thing` folder.

For forward/backward compatibility the meanings of JSON names (names of `.json` files and the names of name/value pairs within `.json` files) should never change. If, when parsing a `.json` file, an unrecognized name is encountered it MUST be ignored *loudly* via logging or displaying a warning message.

## 4. Current Version Overview (Version 0.1.0.0):
* A `.thing` file can hold `.stl` and `.json` files.
* A `.thing` MUST contain a well defined `manifest.json` (section 4.1).
* A `.thing` MUST contain an object in `.stl` format (section 4.2).
* A `.thing` MAY contain other files (unspecified).
* Any name in `.thing` which MAY point to a JSON file of settings or details, MUST be interpreted as a text string if the file name does not resolve.

### 4.1 Example `manifest.json`
    { "namespace": "http://spec.makerbot.com/ns/thing.0.1.1.1"
    , "objects":
        { "bunny.stl": {}
        , "bunny2.stl": {}
        }
    , "constructions":
        { "plastic A": {}
        , "plastic B": {}
        }
    , "instances":
        { "NameA":
            { "object": "bunny.stl"
            , "scale": "mm"
            , "construction": "plastic A"
            }
        , "NameB":
            { "object": "bunny2.stl"
            , "scale": "mm"
            , "construction": "plastic B"
            }
        }
    }

#### 4.1.1 Example Details
The above `manifest.json` entry expects to find a namespace at that URL which contains DOM info and human readable info for what this specification is, etc. It also expects to find two `.stl` files (`bunny.stl`, `bunny2.stl`) at the same directory level as the file is. The above JSON also defines two construction types, `plastic A`, and `plastic B`, which it assumes the calling/using program or person using the file can decode and use. The file then defines a single build plate with two objects (named `NameA`, and `NameB`) to create, each item based on an `.stl` object defined in the object section, using a construction system defined in the constructions section.

### 4.2 namespace entry:
Version information on this file format. Used to verify compatibility and namespace/specification URI. Each manifest MUST contain exactly one namespace definition.

### 4.3 objects entry:
List of objects bundled into this package. `.stl` files are located relative to the `manifest.json` directory. Will support external links and URI in the future. Each manifest MUST contain at least one object key.

### 4.4 constructions entry:
List of construction systems. For version 0.0.1.0 these can be only the text string `Plastic A`, and `Plastic B` Future revisions may specify a JSON file of construction methodology, or slice/tool control details.

### 4.5 instances:
List of all items that bundle together to make this print grouping. List of how many and what objects we want instances of, in key-value pairs. Each key is a unique id string containing one object name, each matched value in instances contains a dictionary of details on the instance. Details MUST include at least one object source, and MAY contain contain more construction or metadata. Unique key names SHOULD be used as display names by the program using them.

The instance dictionary MUST contain at least one object, with a matching object in the `objects` list, MAY contain at most one scale entry, default to mm, and it MAY contain at most one construction entry.

## 5 Examples manifest files:

### 5.1 Total Minimum. Specify one object, assume the program can use the file as it wants.
    { "namespace": "http://spec.makerbot.com/ns/thing.0.1.1.1"
    , "objects":
        { "bunny.stl": {}
        }
    , "instances":
        { "bunny":
            { "object": "bunny.stl"
            , "scale": "mm"
            }
        }
    }

### 5.2 Material Minimum. Specify two objects, two materials, one object of both.
    { "namespace": "http://spec.makerbot.com/ns/thing.0.1.1.1"
    , "objects":
        { "bunny.stl": {}
        , "bunny2.stl": {}
        }
    , "constructions":
        { "plastic A": {}
        , "plastic B": {}
        }
    , "instances":
        { "NameA":
            { "object": "bunny.stl"
            , "scale": "mm"
            , "construction": "plastic B"
            }
        , "NameB":
            { "object": "bunny2.stl"
            , "scale": "mm"
            , "construction": "plastic B"
            }
        }
    }

### 5.3 Material Minimum. Specify two objects, two materials, one object of each.
    { "namespace": "http://spec.makerbot.com/ns/thing.0.1.1.1"
    , "objects":
        { "bunny.stl": {}
        , "bunny2.stl": {}
        }
    , "constructions":
        { "plastic A": {}
        , "plastic B": {}
        }
    , "instances":
        { "NameA":
            { "object": "bunny.stl"
            , "scale": "mm"
            , "construction": "plastic A"
            }
        , "NameB":
            { "object": "bunny2.stl"
            , "scale": "mm"
            , "construction": "plastic B"
            }
        }
    }

### 5.4 Attribution Minimum. Specify one object, creator, license.
    { "namespace": "http://spec.makerbot.com/ns/thing.0.1.1.1"
    , "objects":
        { "bunny.stl": {}
        }
    , "instances":
        { "bunny":
            { "object": "bunny.stl"
            , "scale": "mm"
            }
        }
    , "attribution":
        { "author": "Bob"
        , "license": "foo"
        }
    }
