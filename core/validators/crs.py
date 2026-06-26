# -*- coding: utf-8 -*-
"""CRS validation logic for missing or geographic coordinate reference system checks."""
from typing import List
from .base import BaseValidator
from ..models import ValidationIssue, IssueCategory, Severity


class CRSValidator(BaseValidator):
    """Validator for Coordinate Reference System (CRS) issues on a layer."""

    @property
    def name(self) -> str:
        return "CRS Validator"

    def validate(self, layer) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []

        # Check if layer has a CRS
        if not hasattr(layer, "crs"):
            return issues

        crs = layer.crs()

        if crs is None or not crs.isValid():
            issues.append(
                ValidationIssue(
                    rule_id="C001",
                    category=IssueCategory.CRS,
                    severity=Severity.CRITICAL,
                    message="Layer Coordinate Reference System (CRS) is undefined or invalid.",
                    recommendation=(
                        "Assign an appropriate CRS using QGIS 'Assign projection' "
                        "tool before running analysis."
                    ),
                )
            )
            return issues

        # Check if the CRS is geographic (uses degrees, e.g. WGS84 EPSG:4326)
        if crs.isGeographic():
            auth_id = crs.authid() or "Unknown"
            issues.append(
                ValidationIssue(
                    rule_id="C002",
                    category=IssueCategory.CRS,
                    severity=Severity.LOW,
                    message=f"Layer uses a geographic CRS ({auth_id}).",
                    recommendation=(
                        "Distance, area, and buffer calculations will be computed "
                        "in degrees. Reproject layer to a projected CRS (e.g. UTM) "
                        "for accurate metric measurements."
                    ),
                )
            )

        return issues
