# -*- coding: utf-8 -*-
"""Core data models for GeoQA validation results: severity enums, issues, and layer/project summaries."""
from enum import Enum
from typing import List, Optional


class Severity(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class IssueCategory(Enum):
    GEOMETRY = "Geometry"
    CRS = "CRS"
    ATTRIBUTE = "Attribute"
    TOPOLOGY = "Topology"


class ValidationIssue:
    """Represents a quality issue detected by a specific framework Rule."""

    def __init__(
        self,
        rule_id: str,
        category: IssueCategory,
        severity: Severity,
        message: str,
        recommendation: str,
        affected_features: Optional[List[int]] = None,
        field_name: Optional[str] = None,
    ):
        self.rule_id = rule_id
        self.category = category
        self.severity = severity
        self.message = message
        self.recommendation = recommendation
        self.affected_features = affected_features or []  # List of Feature IDs (FIDs)
        self.field_name = field_name

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "category": self.category.value,
            "severity": self.severity.value,
            "message": self.message,
            "recommendation": self.recommendation,
            "affected_features": self.affected_features,
            "field_name": self.field_name,
        }


class LayerSummary:
    """Contains metadata, validation results, and Quality Score for a single GIS layer."""

    def __init__(
        self, layer_name: str, geometry_type: str, crs_authid: str, feature_count: int
    ):
        self.layer_name = layer_name
        self.geometry_type = geometry_type
        self.crs_authid = crs_authid
        self.feature_count = feature_count
        self.issues: List[ValidationIssue] = []
        self.rule_durations = {}  # Map of rule_id -> elapsed seconds
        self.executed_rules = []  # List of tuples (rule_id, category_value)

        # Stat counters
        self.error_count = 0
        self.warning_count = 0

    def add_issue(self, issue: ValidationIssue):
        self.issues.append(issue)
        if issue.severity in (Severity.CRITICAL, Severity.HIGH):
            self.error_count += 1
        else:
            self.warning_count += 1

    def calculate_score(self) -> int:
        """Computes Layer Quality Score (0-100) using a penalty deduction model.

        Penalties are scaled based on the proportion of features affected.
        """
        score = 100.0
        total_feats = max(1, self.feature_count)

        penalties = {
            Severity.CRITICAL: 30.0,
            Severity.HIGH: 15.0,
            Severity.MEDIUM: 5.0,
            Severity.LOW: 2.0,
        }

        for issue in self.issues:
            base_penalty = penalties.get(issue.severity, 2.0)

            # If the issue affects specific features, scale by the proportion of affected features
            if issue.affected_features and self.feature_count > 0:
                affected_ratio = len(issue.affected_features) / total_feats
                penalty = base_penalty * affected_ratio
            else:
                # Layer-level issue (e.g. missing CRS), apply full penalty
                penalty = base_penalty

            score -= penalty

        return max(0, min(100, round(score)))

    def calculate_category_scores(self) -> dict:
        """Returns isolated score (0-100) per category (Geometry, CRS, Attribute, Topology) based on executed rules."""
        total_feats = max(1, self.feature_count)
        penalties_config = {
            Severity.CRITICAL: 30.0,
            Severity.HIGH: 15.0,
            Severity.MEDIUM: 5.0,
            Severity.LOW: 2.0,
        }
        
        cat_scores = {
            "Geometry": 100.0,
            "CRS": 100.0,
            "Attribute": 100.0,
            "Topology": 100.0
        }
        
        for issue in self.issues:
            base_penalty = penalties_config.get(issue.severity, 2.0)
            if issue.affected_features and self.feature_count > 0:
                affected_ratio = len(issue.affected_features) / total_feats
                penalty = base_penalty * affected_ratio
            else:
                penalty = base_penalty
                
            cat_name = issue.category.value
            if cat_name in cat_scores:
                cat_scores[cat_name] -= penalty
                
        # Round and bound 0-100
        return {cat: max(0, min(100, round(score))) for cat, score in cat_scores.items()}


class ProjectSummary:
    """Aggregates layer summaries and computes final Audit Grade."""

    def __init__(self):
        self.layer_summaries: List[LayerSummary] = []
        self.project_issues: List[ValidationIssue] = []
        self.total_errors = 0
        self.total_warnings = 0
        self.execution_time = 0.0
        self.profile_name = "General"

    def add_layer_summary(self, summary: LayerSummary):
        self.layer_summaries.append(summary)
        self.total_errors += summary.error_count
        self.total_warnings += summary.warning_count

    def add_project_issue(self, issue: ValidationIssue):
        self.project_issues.append(issue)
        if issue.severity in (Severity.CRITICAL, Severity.HIGH):
            self.total_errors += 1
        else:
            self.total_warnings += 1

    def calculate_score(self) -> int:
        """Computes Project Quality Score by averaging Layer Quality Scores and deducting project-level penalties."""
        if not self.layer_summaries:
            return 100

        avg_layer_score = sum(
            layer_sum.calculate_score() for layer_sum in self.layer_summaries
        ) / len(self.layer_summaries)

        project_deductions = 0.0
        penalties = {
            Severity.CRITICAL: 30.0,
            Severity.HIGH: 15.0,
            Severity.MEDIUM: 5.0,
            Severity.LOW: 2.0,
        }
        for issue in self.project_issues:
            project_deductions += penalties.get(issue.severity, 2.0)

        return max(0, min(100, round(avg_layer_score - project_deductions)))

    def get_grade(self) -> str:
        """Maps final Quality Score to standard Letter Grades."""
        score = self.calculate_score()
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 50:
            return "D"
        else:
            return "F"

    def get_grade_description(self) -> str:
        """Gets description for letter grade."""
        grade = self.get_grade()
        descriptions = {
            "A": "Excellent (Safe for GIS Analysis)",
            "B": "Good (Minor Data Quality Warnings)",
            "C": "Needs Review (Tabular or Non-critical spatial issues)",
            "D": "Poor Quality (Multiple duplicates or partial geometric failures)",
            "F": "Unusable (Critical projection or validity errors detected)",
        }
        return descriptions.get(grade, "Unknown")
