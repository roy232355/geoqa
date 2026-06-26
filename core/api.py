# -*- coding: utf-8 -*-
from typing import List, Dict, Any
from .engine import ValidationEngine
from .models import LayerSummary, ProjectSummary
from .rules.loader import RuleLoader


class GeoQA:
    """Public API interface enabling other plugins, scripts, or packages to run GeoQA audits and query rule sets."""

    @staticmethod
    def validate_layer(layer, profile_name: str = "General") -> LayerSummary:
        """Audits a single GIS layer using the selected profile.

        Args:
            layer: Vector layer object (MockVectorLayer or QgsVectorLayer).
            profile_name: Name of profile filtering which rules run.

        Returns:
            LayerSummary: Contains audit scores, grades, and detected issues list.
        """
        engine = ValidationEngine(profile_name=profile_name)
        return engine.validate_layer(layer)

    @staticmethod
    def validate_project(layers: list, profile_name: str = "General") -> ProjectSummary:
        """Audits a list of GIS layers using the selected profile.

        Args:
            layers: List of vector layers.
            profile_name: Profile name.

        Returns:
            ProjectSummary: Aggregated audit summaries and cross-layer issues.
        """
        engine = ValidationEngine(profile_name=profile_name)
        return engine.validate_project(layers)

    @staticmethod
    def list_rules() -> List[Dict[str, Any]]:
        """Returns details of all discovered rules.

        Returns:
            List[Dict[str, Any]]: Metadata mappings for each discovered rule.
        """
        rules = RuleLoader.discover_rules()
        return [
            {
                "id": rule.rule_id,
                "name": rule.name,
                "description": rule.description,
                "severity": rule.severity.value,
                "category": rule.category.value,
                "version": rule.version,
                "author": rule.author,
                "tags": rule.tags,
                "requires_geometry": rule.requires_geometry,
                "requires_attributes": rule.requires_attributes,
                "requires_projection": rule.requires_projection,
            }
            for rule in sorted(rules, key=lambda r: r.rule_id)
        ]

    @staticmethod
    def list_profiles() -> List[str]:
        """Returns lists of preset validation profiles."""
        return list(RuleLoader.DEFAULT_PROFILES.keys())
