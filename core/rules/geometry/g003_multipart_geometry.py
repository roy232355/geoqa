# -*- coding: utf-8 -*-
from typing import List
from ..base import Rule
from ...models import ValidationIssue, IssueCategory, Severity
from ...compat import GISCompat


class G003_MultipartGeometry(Rule):
    """Rule to audit multipart geometries."""

    def __init__(self):
        super().__init__(
            rule_id="G003",
            name="Multipart Geometry",
            description="Checks features for multipart geometry types (e.g. MultiPolygon).",
            default_severity=Severity.MEDIUM,
            category=IssueCategory.GEOMETRY,
            recommendation=(
                "Run the QGIS 'Multipart to singleparts' tool if your spatial "
                "operations require singlepart inputs."
            ),
        )

    def evaluate(self, layer, checker=None) -> List[ValidationIssue]:
        if not GISCompat.is_spatial(layer):
            return []

        multipart_fids = []
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
            if GISCompat.is_geometry_multipart(geom):
                multipart_fids.append(feature.id())

        if multipart_fids:
            return [
                ValidationIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    severity=self.severity,
                    message=f"Layer contains {len(multipart_fids)} multipart features.",
                    recommendation=self.recommendation,
                    affected_features=multipart_fids,
                )
            ]
        return []
