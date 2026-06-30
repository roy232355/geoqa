# -*- coding: utf-8 -*-
import math
from typing import List
from ..base import Rule
from ...models import ValidationIssue, IssueCategory, Severity
from ...compat import GISCompat


class G005_SliverPolygons(Rule):
    """Rule to audit sliver (thin, narrow) polygons in vector layers."""

    def __init__(self):
        super().__init__(
            rule_id="G005",
            name="Sliver Polygons",
            description="Checks for extremely thin or narrow polygons.",
            default_severity=Severity.MEDIUM,
            category=IssueCategory.GEOMETRY,
            recommendation=(
                "Verify if this polygon is an accidental sliver artifact from clipping/alignment. "
                "Clean using 'Snap geometries to layer' or manual vertex editing."
            ),
        )
        self.compactness_threshold = 0.05

    def load_config(self, config: dict):
        """Loads custom parameters from json configuration overrides."""
        self.compactness_threshold = config.get(
            "compactness_threshold", self.compactness_threshold
        )

    def evaluate(self, layer, checker=None) -> List[ValidationIssue]:
        if not GISCompat.is_spatial(layer):
            return []

        # Sliver polygons are only relevant for Polygon layers
        if hasattr(layer, "geometryType") and layer.geometryType() != 2:
            return []

        sliver_fids = []

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

            area = geom.area()
            perimeter = geom.length()

            if area <= 0 or perimeter <= 0:
                continue

            polsby_popper = (4.0 * math.pi * area) / (perimeter * perimeter)

            if polsby_popper < self.compactness_threshold:
                sliver_fids.append(feature.id())

        if sliver_fids:
            return [
                ValidationIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    severity=self.severity,
                    message=(
                        f"Layer contains {len(sliver_fids)} sliver polygons "
                        f"(compactness < {self.compactness_threshold})."
                    ),
                    recommendation=self.recommendation,
                    affected_features=sliver_fids,
                )
            ]
        return []
