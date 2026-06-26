# -*- coding: utf-8 -*-
import time
from typing import Dict, Optional

from .models import (
    ProjectSummary,
    LayerSummary,
    ValidationIssue,
    IssueCategory,
    Severity,
)
from .rules.registry import RuleRegistry
from .rules.loader import RuleLoader
from .settings import SettingsManager
from .events import EventBus
from .compat import GISCompat
from .logger import log_info, log_warning, log_exception


class ValidationEngine:
    """Core rule execution engine supporting Dependency Injection, Event Bus, logging, and QgsTask progression hooks."""

    def __init__(
        self,
        registry: Optional[RuleRegistry] = None,
        settings_manager: Optional[SettingsManager] = None,
        event_bus: Optional[EventBus] = None,
        profile_name: str = "General",
    ):
        self.settings = settings_manager or SettingsManager()
        self.registry = registry or RuleRegistry()
        self.events = event_bus or EventBus()

        self.profile_name = profile_name
        # Load and register rules for the selected profile
        RuleLoader.populate_registry(self.registry, self.settings, profile_name)
        log_info(
            f"ValidationEngine initialized with profile '{profile_name}'. "
            f"{len(self.registry.get_enabled_rules())} active rules loaded."
        )

    def validate_layer(self, layer, task=None) -> LayerSummary:
        """Evaluates all registered active rules on a single vector layer."""
        layer_name = layer.name() if hasattr(layer, "name") else "Unnamed Layer"

        # Resolve basic layer metadata using the PyQGIS Compatibility Layer
        geom_type_str = "No Geometry"
        if hasattr(layer, "geometryType"):
            geom_code = layer.geometryType()
            geom_map = {0: "Point", 1: "Line", 2: "Polygon", 3: "No Geometry"}
            geom_type_str = geom_map.get(geom_code, "Unknown")

        crs = GISCompat.get_crs(layer)
        crs_authid = (
            GISCompat.get_crs_authid(crs)
            if GISCompat.is_crs_valid(crs)
            else "Undefined"
        )
        feat_count = layer.featureCount() if hasattr(layer, "featureCount") else 0

        summary = LayerSummary(
            layer_name=layer_name,
            geometry_type=geom_type_str,
            crs_authid=crs_authid,
            feature_count=feat_count,
        )

        active_rules = self.registry.get_enabled_rules()
        for rule in active_rules:
            self.events.publish(
                "rule_started", layer_name=layer_name, rule_id=rule.rule_id
            )
            start_time = time.time()
            try:
                issues = rule.evaluate(layer, checker=task)
                for issue in issues:
                    summary.add_issue(issue)
            except Exception as e:
                # Catching execution exceptions gracefully
                err_msg = f"Rule '{rule.rule_id}' failed during evaluation on layer '{layer_name}': {str(e)}"
                log_exception(err_msg)

                summary.add_issue(
                    ValidationIssue(
                        rule_id=rule.rule_id,
                        category=rule.category,
                        severity=Severity.CRITICAL,
                        message=f"Rule evaluation crash: {str(e)}",
                        recommendation="Ensure your dataset is valid or report this rule crash to developer support.",
                    )
                )
            finally:
                rule.execution_time = time.time() - start_time
                summary.rule_durations[rule.rule_id] = rule.execution_time
                summary.executed_rules.append((rule.rule_id, rule.category.value))
                self.events.publish(
                    "rule_completed",
                    layer_name=layer_name,
                    rule_id=rule.rule_id,
                    duration=rule.execution_time,
                )

        return summary

    def validate_project(self, layers: list, task=None) -> ProjectSummary:
        """Validates all target layers, triggers event updates, and checks for background thread cancellations."""
        project_start_time = time.time()
        project_summary = ProjectSummary()
        project_summary.profile_name = self.profile_name
        self.events.publish("validation_started", layer_count=len(layers))
        log_info(f"Started project audit. Target layer count: {len(layers)}")

        if not layers:
            project_summary.add_project_issue(
                ValidationIssue(
                    rule_id="P000",
                    category=IssueCategory.GEOMETRY,
                    severity=Severity.LOW,
                    message="No vector layers were provided for validation.",
                    recommendation="Select or load vector layers into QGIS before running the auditor.",
                )
            )
            self.events.publish("validation_completed", summary=project_summary)
            project_summary.execution_time = time.time() - project_start_time
            return project_summary

        # Validate each individual layer sequentially
        total_layers = len(layers)
        for idx, layer in enumerate(layers):
            # Check for background QgsTask cancellation triggers
            is_cancelled = False
            if task:
                is_cancelled = (
                    task.isCanceled()
                    if hasattr(task, "isCanceled")
                    else task.isCancelled()
                )
            if is_cancelled:
                log_warning("Project audit cancelled by user.")
                self.events.publish("validation_cancelled")
                return project_summary

            layer_summary = self.validate_layer(layer, task=task)
            project_summary.add_layer_summary(layer_summary)

            # Update progress percent (allocate 0-90% range to layer audits)
            if task:
                progress = int(((idx + 1) / total_layers) * 90)
                task.setProgress(progress)

        # Cross-layer Checks (only ran if audit wasn't cancelled)
        is_cancelled = False
        if task:
            is_cancelled = (
                task.isCanceled() if hasattr(task, "isCanceled") else task.isCancelled()
            )
        if is_cancelled:
            log_warning("Project audit cancelled during cross-layer evaluation.")
            self.events.publish("validation_cancelled")
            return project_summary

        # 1. Mixed CRS check
        crs_sets = set()
        for summary in project_summary.layer_summaries:
            if summary.crs_authid and summary.crs_authid != "Undefined":
                crs_sets.add(summary.crs_authid)

        if len(crs_sets) > 1:
            project_summary.add_project_issue(
                ValidationIssue(
                    rule_id="P001",
                    category=IssueCategory.CRS,
                    severity=Severity.HIGH,
                    message=f"Project contains layers with mixed Coordinate Reference Systems: {', '.join(crs_sets)}",
                    recommendation=(
                        "Reproject layers to a unified coordinate reference system "
                        "(e.g. your QGIS Project CRS) before overlay analysis."
                    ),
                )
            )

        # 2. Duplicate Layer Names
        name_counts: Dict[str, int] = {}
        for summary in project_summary.layer_summaries:
            name_counts[summary.layer_name] = name_counts.get(summary.layer_name, 0) + 1

        dup_names = [name for name, count in name_counts.items() if count > 1]
        if dup_names:
            project_summary.add_project_issue(
                ValidationIssue(
                    rule_id="P002",
                    category=IssueCategory.ATTRIBUTE,
                    severity=Severity.MEDIUM,
                    message=f"Project contains duplicate layer names: {', '.join(dup_names)}",
                    recommendation="Rename duplicate layers in the QGIS layers panel to avoid report ambiguity.",
                )
            )

        # 3. Empty Layer Check
        empty_layers = [
            s.layer_name
            for s in project_summary.layer_summaries
            if s.feature_count == 0
        ]
        if empty_layers:
            project_summary.add_project_issue(
                ValidationIssue(
                    rule_id="P003",
                    category=IssueCategory.GEOMETRY,
                    severity=Severity.LOW,
                    message=f"Project contains empty layers (0 features): {', '.join(empty_layers)}",
                    recommendation=(
                        "Ensure these layers are supposed to be empty or check "
                        "if data import was successful."
                    ),
                )
            )

        # Complete audit reporting
        if task:
            task.setProgress(100)

        self.events.publish("validation_completed", summary=project_summary)
        log_info(
            f"Project audit complete. Score: {project_summary.calculate_score()}, "
            f"Grade: {project_summary.get_grade()}. Errors: {project_summary.total_errors}, "
            f"Warnings: {project_summary.total_warnings}"
        )
        project_summary.execution_time = time.time() - project_start_time
        return project_summary
