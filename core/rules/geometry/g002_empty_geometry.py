# -*- coding: utf-8 -*-
from typing import List
from ..base import Rule
from ...models import ValidationIssue, IssueCategory, Severity
from ...compat import GISCompat


class G002_EmptyGeometry(Rule):
    """Rule to audit empty geometry records."""

    def __init__(self):
        super().__init__(
            rule_id="G002",
            name="Empty Geometry",
            description="Checks features for empty geometry definitions.",
            default_severity=Severity.CRITICAL,
            category=IssueCategory.GEOMETRY,
            recommendation="Remove empty features or rebuild their spatial coordinates using editing tools.",
        )

    def evaluate(self, layer, checker=None) -> List[ValidationIssue]:
        if not GISCompat.is_spatial(layer):
            return []

        empty_fids = []
        for idx, feature in enumerate(GISCompat.get_features_for_geometry(layer)):
            if idx % 5000 == 0 and checker:
                is_cancelled = (
                    checker.isCanceled()
                    if hasattr(checker, "isCanceled")
                    else checker.isCancelled()
                )
                if is_cancelled:
                    return []

            geom = GISCompat.get_geometry(feature)
            if GISCompat.is_geometry_null_or_empty(geom):
                empty_fids.append(feature.id())

        if empty_fids:
            return [
                ValidationIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    severity=self.severity,
                    message=f"Layer contains {len(empty_fids)} features with empty geometries.",
                    recommendation=self.recommendation,
                    affected_features=empty_fids,
                )
            ]
        return []
