# -*- coding: utf-8 -*-
"""Compatibility layer for PyQGIS APIs across different versions."""


class GISCompat:
    """Compatibility abstraction layer wrapping PyQGIS layer and geometry operations."""

    @staticmethod
    def is_spatial(layer) -> bool:
        """Determines if a vector layer contains geometry features."""
        if hasattr(layer, "isSpatial"):
            return layer.isSpatial()
        # Fallback check
        return hasattr(layer, "geometryType") and layer.geometryType() != 3

    @staticmethod
    def get_crs(layer):
        """Retrieves the coordinate reference system of the layer."""
        if hasattr(layer, "crs"):
            return layer.crs()
        return None

    @staticmethod
    def is_crs_valid(crs) -> bool:
        """Determines if the CRS is valid."""
        if crs is not None and hasattr(crs, "isValid"):
            return crs.isValid()
        return False

    @staticmethod
    def is_crs_geographic(crs) -> bool:
        """Determines if the CRS is geographic (degree-based)."""
        if crs is not None and hasattr(crs, "isGeographic"):
            return crs.isGeographic()
        return False

    @staticmethod
    def get_crs_authid(crs) -> str:
        """Retrieves the EPSG/auth identifier (e.g. EPSG:4326)."""
        if crs is not None and hasattr(crs, "authid"):
            return crs.authid() or "Unknown"
        return "Unknown"

    @staticmethod
    def get_geometry(feature):
        """Retrieves geometry data from a feature."""
        if hasattr(feature, "geometry"):
            return feature.geometry()
        return None

    @staticmethod
    def is_geometry_null_or_empty(geom) -> bool:
        """Checks if a geometry is null or empty."""
        if geom is None:
            return True
        is_null = False
        if hasattr(geom, "isNull"):
            is_null = geom.isNull()

        is_empty = False
        if hasattr(geom, "isEmpty"):
            is_empty = geom.isEmpty()

        return is_null or is_empty

    @staticmethod
    def is_geometry_multipart(geom) -> bool:
        """Checks if a geometry is multipart (e.g. MultiPolygon)."""
        if geom is not None and hasattr(geom, "isMultipart"):
            return geom.isMultipart()
        return False

    @staticmethod
    def is_geometry_valid(geom) -> bool:
        """Checks if the geometry is structurally valid."""
        if geom is not None and hasattr(geom, "isValid"):
            return geom.isValid()
        return True

    @staticmethod
    def get_features_for_geometry(layer):
        """Retrieves layer features optimized for geometry inspection (no attributes)."""
        try:
            from qgis.core import QgsFeatureRequest

            request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoAttributes)
            return layer.getFeatures(request)
        except Exception:
            return layer.getFeatures() if hasattr(layer, "getFeatures") else []

    @staticmethod
    def get_features_for_attributes(layer, field_names: list = None):
        """Retrieves layer features optimized for attribute inspection (no geometries, optional subset of fields)."""
        try:
            from qgis.core import QgsFeatureRequest

            request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry)
            if field_names and hasattr(layer, "fields"):
                fields = layer.fields()
                indices = [
                    fields.indexFromName(name)
                    for name in field_names
                    if fields.indexFromName(name) >= 0
                ]
                if indices:
                    request.setSubsetOfAttributes(indices)
            return layer.getFeatures(request)
        except Exception:
            return layer.getFeatures() if hasattr(layer, "getFeatures") else []
