# -*- coding: utf-8 -*-
class MockCRS:
    """Mock for QgsCoordinateReferenceSystem."""

    def __init__(self, authid="EPSG:4326", valid=True, geographic=True):
        self._authid = authid
        self._valid = valid
        self._geographic = geographic

    def isValid(self):
        return self._valid

    def isGeographic(self):
        return self._geographic

    def authid(self):
        return self._authid


class MockField:
    """Mock for QgsField."""

    def __init__(self, name, type_name="string"):
        self._name = name
        self._type_name = type_name

    def name(self):
        return self._name

    def typeName(self):
        return self._type_name

    def isNumeric(self):
        return self._type_name.lower() in ("int", "integer", "double", "real", "longlong")


class MockFields:
    """Mock for QgsFields."""

    def __init__(self, fields_list):
        self._fields = fields_list

    def __iter__(self):
        return iter(self._fields)

    def __len__(self):
        return len(self._fields)

    def names(self):
        return [f.name() for f in self._fields]

    def indexFromName(self, name):
        try:
            return [f.name() for f in self._fields].index(name)
        except ValueError:
            return -1


class MockGeometry:
    """Mock for QgsGeometry."""

    def __init__(
        self, is_null=False, is_empty=False, is_valid=True, is_multipart=False,
        wkb=b"mock_wkb", area=100.0, length=40.0
    ):
        self._is_null = is_null
        self._is_empty = is_empty
        self._is_valid = is_valid
        self._is_multipart = is_multipart
        self._wkb = wkb
        self._area = area
        self._length = length

    def isNull(self):
        return self._is_null

    def isEmpty(self):
        return self._is_empty

    def isValid(self):
        return self._is_valid

    def isMultipart(self):
        return self._is_multipart

    def asWkb(self):
        return self._wkb

    def area(self):
        return self._area

    def length(self):
        return self._length


class MockFeature:
    """Mock for QgsFeature."""

    def __init__(self, fid, geometry, attributes_dict):
        self._fid = fid
        self._geometry = geometry
        self._attributes = attributes_dict

    def id(self):
        return self._fid

    def geometry(self):
        return self._geometry

    def __getitem__(self, key):
        return self._attributes.get(key, None)


class MockVectorLayer:
    """Mock for QgsVectorLayer."""

    def __init__(
        self,
        name="Test Layer",
        geom_type=2,
        crs=None,
        features=None,
        fields=None,
        spatial=True,
    ):
        self._name = name
        self._geom_type = geom_type
        self._crs = crs or MockCRS()
        self._features = features or []
        self._fields = MockFields(fields or [])
        self._spatial = spatial

    def name(self):
        return self._name

    def geometryType(self):
        # 0: Point, 1: Line, 2: Polygon, 3: NoGeometry
        return self._geom_type

    def crs(self):
        return self._crs

    def featureCount(self):
        return len(self._features)

    def fields(self):
        return self._fields

    def getFeatures(self):
        return self._features

    def isSpatial(self):
        return self._spatial
