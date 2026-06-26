# -*- coding: utf-8 -*-
"""Abstract base class for all GeoQA validator modules."""
from abc import ABC, abstractmethod
from typing import List
from ..models import ValidationIssue


class BaseValidator(ABC):
    """Abstract base class for all GeoQA validator modules."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the unique name of this validator."""
        pass

    @abstractmethod
    def validate(self, layer) -> List[ValidationIssue]:
        """Runs the validation logic on the given QGIS vector layer.

        Args:
            layer: QgsVectorLayer (or mock object in tests)

        Returns:
            List[ValidationIssue]: A list of detected validation issues.
        """
        pass
