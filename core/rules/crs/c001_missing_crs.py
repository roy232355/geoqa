# -*- coding: utf-8 -*-
from typing import List
from ..base import Rule
from ...models import ValidationIssue, IssueCategory, Severity


class C001_MissingCRS(Rule):
    """Rule to audit missing/invalid coordinate projection settings."""

    def __init__(self):
        super().__init__(
            rule_id="C001",
            name="Missing CRS",
            description="Checks if the layer coordinate reference system is undefined or invalid.",
            default_severity=Severity.CRITICAL,
            category=IssueCategory.CRS,
            recommendation="Assign the correct Coordinate Reference System using QGIS 'Assign projection' tool.",
        )

    def evaluate(self, layer, checker=None) -> List[ValidationIssue]:
        if not hasattr(layer, "crs"):
            return []

        crs = layer.crs()
        if crs is None or not crs.isValid():
            return [
                ValidationIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    severity=self.severity,
                    message="Layer Coordinate Reference System (CRS) is undefined or invalid.",
                    recommendation=self.recommendation,
                )
            ]
        return []
