# -*- coding: utf-8 -*-
"""Geometry validation logic for empty, invalid, and multipart geometry checks."""
from typing import List
from .base import BaseValidator
from ..models import ValidationIssue, IssueCategory, Severity


class GeometryValidator(BaseValidator):
    """Validator for GIS geometry issues (invalid, empty, and multipart geometries)."""

    @property
    def name(self) -> str:
        return "Geometry Validator"

    def validate(self, layer) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []

        # Check if layer has geometry (e.g. is not a geometryless attribute table)
        if not hasattr(layer, "isSpatial") or not layer.isSpatial():
            return issues

        invalid_fids: List[int] = []
        empty_fids: List[int] = []
        multipart_fids: List[int] = []

        for feature in layer.getFeatures():
            fid = feature.id()
            geom = feature.geometry()

            if geom.isNull() or geom.isEmpty():
                empty_fids.append(fid)
                continue

            if not geom.isValid():
                invalid_fids.append(fid)

            if geom.isMultipart():
                multipart_fids.append(fid)

        if empty_fids:
            issues.append(
                ValidationIssue(
                    rule_id="G002",
                    category=IssueCategory.GEOMETRY,
                    severity=Severity.CRITICAL,
                    message=f"Layer contains {len(empty_fids)} empty geometry records.",
                    recommendation="Remove empty features or rebuild their spatial components using digitizing tools.",
                    affected_features=empty_fids,
                )
            )

        if invalid_fids:
            issues.append(
                ValidationIssue(
                    rule_id="G001",
                    category=IssueCategory.GEOMETRY,
                    severity=Severity.CRITICAL,
                    message=f"Layer contains {len(invalid_fids)} features with invalid geometries.",
                    recommendation=(
                        "Use QGIS 'Fix Geometries' tool, or manually resolve "
                        "self-intersections and slivers."
                    ),
                    affected_features=invalid_fids,
                )
            )

        if multipart_fids:
            issues.append(
                ValidationIssue(
                    rule_id="G003",
                    category=IssueCategory.GEOMETRY,
                    severity=Severity.MEDIUM,
                    message=f"Layer contains {len(multipart_fids)} multipart geometry features.",
                    recommendation=(
                        "If your analysis requires singlepart features (e.g., "
                        "certain spatial joins), run the QGIS 'Multipart to "
                        "singleparts' tool."
                    ),
                    affected_features=multipart_fids,
                )
            )

        return issues
