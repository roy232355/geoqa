# -*- coding: utf-8 -*-
from qgis.core import QgsProcessingProvider
from .processing.validate_layer_algorithm import ValidateLayerAlgorithm


class GeoQAProvider(QgsProcessingProvider):
    """QGIS Processing Provider class for GeoQA."""

    def __init__(self):
        super().__init__()

    def loadAlgorithms(self, configuration=None):
        """Loads and adds all algorithms to the provider."""
        self.addAlgorithm(ValidateLayerAlgorithm())

    def id(self) -> str:
        """Returns the unique identifier for this provider."""
        return "geoqa"

    def name(self) -> str:
        """Returns the user-visible name for this provider."""
        return "GeoQA GIS Auditor"

    def icon(self):
        """Returns the GeoQA branded icon for this provider."""
        import os
        from qgis.PyQt.QtGui import QIcon
        from .core.resources import ResourceManager
        icon_path = ResourceManager.get_icon_path()
        if os.path.exists(icon_path):
            return QIcon(icon_path)
        return super().icon()
