# -*- coding: utf-8 -*-
"""Dynamically discovers and registers validation rules for the GeoQA engine."""
import os
import json
from typing import List

from .base import Rule
from ..models import Severity
from .registry import RuleRegistry
from ..settings import SettingsManager


class RuleLoader:
    """Dynamically discovers and registers validation rules using SettingsManager and RuleRegistry."""

    DEFAULT_PROFILES = {
        "General": [
            "G001",
            "G002",
            "G003",
            "C001",
            "C002",
            "A001",
            "A002",
            "A003",
            "A004",
            "A005",
            "A006",
        ],
        "Geometry Only": ["G001", "G002", "G003"],
        "Attribute Only": ["A001", "A002", "A003", "A004", "A005", "A006"],
        "Database Compliance": ["C001", "A002", "A005"],
    }

    @staticmethod
    def discover_rules() -> List[Rule]:
        """Returns instantiated rules via explicit imports to guarantee stability in QGIS."""
        from .geometry.g001_invalid_geometry import G001_InvalidGeometry
        from .geometry.g002_empty_geometry import G002_EmptyGeometry
        from .geometry.g003_multipart_geometry import G003_MultipartGeometry

        from .crs.c001_missing_crs import C001_MissingCRS
        from .crs.c002_geographic_crs import C002_GeographicCRS

        from .attributes.a001_long_field_names import A001_LongFieldNames
        from .attributes.a002_reserved_keywords import A002_ReservedKeywords
        from .attributes.a003_null_values import A003_NullValues
        from .attributes.a004_empty_strings import A004_EmptyStrings
        from .attributes.a005_duplicate_identifiers import A005_DuplicateIdentifiers
        from .attributes.a006_numeric_strings import A006_NumericStrings

        return [
            G001_InvalidGeometry(),
            G002_EmptyGeometry(),
            G003_MultipartGeometry(),
            C001_MissingCRS(),
            C002_GeographicCRS(),
            A001_LongFieldNames(),
            A002_ReservedKeywords(),
            A003_NullValues(),
            A004_EmptyStrings(),
            A005_DuplicateIdentifiers(),
            A006_NumericStrings(),
        ]

    @staticmethod
    def populate_registry(
        registry: RuleRegistry,
        settings_manager: SettingsManager,
        profile_name: str = "General",
    ):
        """Discovers, configures, and registers active rules matching a profile into the registry."""
        registry.clear()
        all_rules = RuleLoader.discover_rules()
        rules_map = {rule.rule_id: rule for rule in all_rules}

        # 1. Apply rules.json configuration overrides (packaged defaults)
        rules_dir = os.path.dirname(os.path.abspath(__file__))
        plugin_root = os.path.dirname(os.path.dirname(rules_dir))
        rules_json_path = os.path.join(plugin_root, "rules.json")
        profiles_json_path = os.path.join(plugin_root, "profiles.json")

        if os.path.exists(rules_json_path):
            try:
                with open(rules_json_path, "r", encoding="utf-8") as f:
                    overrides = json.load(f)
                    for rule_id, config in overrides.items():
                        if rule_id in rules_map:
                            rule = rules_map[rule_id]
                            rule.enabled = config.get("enabled", rule.enabled)
                            severity_str = config.get("severity")
                            if severity_str:
                                try:
                                    title_severity = (
                                        severity_str.title()
                                        if hasattr(severity_str, "title")
                                        else severity_str
                                    )
                                    rule.severity = Severity(title_severity)
                                except ValueError:
                                    pass
            except Exception as e:
                from ..logger import log_warning
                log_warning(f"Error reading rules.json configuration: {str(e)}")

        # 2. Apply user-defined SettingsManager overrides
        for rule_id, rule in rules_map.items():
            enabled_override = settings_manager.get_setting(
                f"GeoQA/rules/{rule_id}/enabled", None
            )
            if enabled_override is not None:
                rule.enabled = bool(enabled_override)

            severity_override = settings_manager.get_setting(
                f"GeoQA/rules/{rule_id}/severity", None
            )
            if severity_override:
                try:
                    title_severity = (
                        severity_override.title()
                        if hasattr(severity_override, "title")
                        else severity_override
                    )
                    rule.severity = Severity(title_severity)
                except ValueError:
                    pass

        # 3. Resolve profile rule IDs
        profile_rule_ids = None
        if os.path.exists(profiles_json_path):
            try:
                with open(profiles_json_path, "r", encoding="utf-8") as f:
                    profiles = json.load(f)
                    profile_rule_ids = profiles.get(profile_name)
            except Exception as e:
                from ..logger import log_warning
                log_warning(f"Error reading profiles.json: {str(e)}")

        if profile_rule_ids is None:
            profile_rule_ids = RuleLoader.DEFAULT_PROFILES.get(
                profile_name, RuleLoader.DEFAULT_PROFILES["General"]
            )

        # 4. Register enabled rules matching profile selection
        for r_id in profile_rule_ids:
            if r_id in rules_map:
                rule = rules_map[r_id]
                if rule.enabled:
                    registry.register(rule)

    @staticmethod
    def load_profile_rules(profile_name: str = "General") -> List[Rule]:
        """Backward-compatible utility returning loaded rules list for a profile."""
        registry = RuleRegistry()
        settings = SettingsManager()
        RuleLoader.populate_registry(registry, settings, profile_name)
        return registry.get_enabled_rules()
