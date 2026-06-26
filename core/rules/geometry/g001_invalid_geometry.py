# -*- coding: utf-8 -*-
from typing import List
from ..base import Rule
from ...models import ValidationIssue, IssueCategory, Severity
from ...compat import GISCompat


class G001_InvalidGeometry(Rule):
    """Rule to audit geometry validity."""

    def __init__(self):
        super().__init__(
            rule_id="G001",
            name="Invalid Geometry",
            description="Checks features for invalid geometry elements (e.g. self-intersecting polygons).",
            default_severity=Severity.CRITICAL,
            category=IssueCategory.GEOMETRY,
            recommendation="Run the QGIS 'Fix Geometries' processing tool or manually resolve topological anomalies.",
        )

    def evaluate(self, layer, checker=None) -> List[ValidationIssue]:
        if not GISCompat.is_spatial(layer):
            return []

        invalid_fids = []
        for idx, feature in enumerate(GISCompat.get_features_for_geometry(layer)):
            if (
                idx % 5000 == 0
                and checker
                and (
                    checker.isCanceled()
                    if hasattr(checker, "isCanceled")
                    else checker.isCancelled()
                )
            ):
                return []

            geom = GISCompat.get_geometry(feature)
            if GISCompat.is_geometry_null_or_empty(geom):
                continue
            if not GISCompat.is_geometry_valid(geom):
                invalid_fids.append(feature.id())

        if invalid_fids:
            return [
                ValidationIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    severity=self.severity,
                    message=f"Layer contains {len(invalid_fids)} features with invalid geometries.",
                    recommendation=self.recommendation,
                    affected_features=invalid_fids,
                )
            ]
        return []
