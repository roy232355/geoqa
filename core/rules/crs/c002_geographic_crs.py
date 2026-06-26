# -*- coding: utf-8 -*-
from typing import List
from ..base import Rule
from ...models import ValidationIssue, IssueCategory, Severity


class C002_GeographicCRS(Rule):
    """Rule to audit geographic (degree-based) projections."""

    def __init__(self):
        super().__init__(
            rule_id="C002",
            name="Geographic CRS Warning",
            description="Flags layers using WGS84 or other geographic degree coordinate systems.",
            default_severity=Severity.LOW,
            category=IssueCategory.CRS,
            recommendation=(
                "Reproject the layer to a projected coordinate reference system "
                "(e.g. UTM) for accurate metric distance, area, and buffer calculations."
            ),
        )

    def evaluate(self, layer, checker=None) -> List[ValidationIssue]:
        if not hasattr(layer, "crs"):
            return []

        crs = layer.crs()
        if crs is not None and crs.isValid() and crs.isGeographic():
            auth_id = crs.authid() or "Unknown"
            return [
                ValidationIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    severity=self.severity,
                    message=f"Layer uses a geographic coordinate system ({auth_id}).",
                    recommendation=self.recommendation,
                )
            ]
        return []
