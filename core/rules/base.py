# -*- coding: utf-8 -*-
"""Abstract base class defining the Rule interface for all GeoQA validation rules."""
from abc import ABC, abstractmethod
from typing import List
from ..models import Severity, IssueCategory, ValidationIssue


class Rule(ABC):
    """Base abstract class for all GeoQA validation rules."""

    def __init__(
        self,
        rule_id: str,
        name: str,
        description: str,
        default_severity: Severity,
        category: IssueCategory,
        recommendation: str,
        enabled: bool = True,
        version: str = "1.0.0",
        fix_available: bool = False,
        doc_url: str = "",
        author: str = "GeoQA Devs",
        introduced_version: str = "1.0.0",
        deprecated: bool = False,
        tags: list = None,
        requires_geometry: bool = True,
        requires_attributes: bool = True,
        requires_projection: bool = True,
    ):
        self.rule_id = rule_id
        self.name = name
        self.description = description
        self.severity = default_severity
        self.category = category
        self.recommendation = recommendation
        self.enabled = enabled
        self.version = version
        self.fix_available = fix_available
        self.doc_url = doc_url
        self.author = author
        self.introduced_version = introduced_version
        self.deprecated = deprecated
        self.tags = tags or []
        self.requires_geometry = requires_geometry
        self.requires_attributes = requires_attributes
        self.requires_projection = requires_projection
        self.execution_time = 0.0  # Tracked dynamically by the engine

    @abstractmethod
    def evaluate(self, layer, checker=None) -> List[ValidationIssue]:
        """Evaluates this rule against a vector layer.

        Args:
            layer: QgsVectorLayer or simulated MockVectorLayer.
            checker: Optional object (e.g. QgsTask) to check for cancellation.

        Returns:
            List[ValidationIssue]: A list of issues detected by this rule.
        """
        pass
