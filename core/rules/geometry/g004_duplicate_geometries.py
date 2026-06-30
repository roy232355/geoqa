# -*- coding: utf-8 -*-
from typing import List
from ..base import Rule
from ...models import ValidationIssue, IssueCategory, Severity
from ...compat import GISCompat


class G004_DuplicateGeometries(Rule):
    """Rule to audit duplicate geometries in vector layers."""

    def __init__(self):
        super().__init__(
            rule_id="G004",
            name="Duplicate Geometries",
            description="Checks for features with identical geometry coordinates.",
            default_severity=Severity.HIGH,
            category=IssueCategory.GEOMETRY,
            recommendation="Remove duplicate features or use the QGIS 'Delete duplicate geometries' processing tool.",
        )

    def evaluate(self, layer, checker=None) -> List[ValidationIssue]:
        if not GISCompat.is_spatial(layer):
            return []

        seen_wkbs = {}
        duplicate_fids = []

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
                continue

            try:
                wkb = geom.asWkb()
            except Exception:
                continue

            if wkb in seen_wkbs:
                duplicate_fids.append(feature.id())
            else:
                seen_wkbs[wkb] = feature.id()

        if duplicate_fids:
            return [
                ValidationIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    severity=self.severity,
                    message=f"Layer contains {len(duplicate_fids)} features with duplicate geometries.",
                    recommendation=self.recommendation,
                    affected_features=duplicate_fids,
                )
            ]
        return []
