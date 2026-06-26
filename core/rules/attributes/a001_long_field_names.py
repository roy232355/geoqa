# -*- coding: utf-8 -*-
from typing import List
from ..base import Rule
from ...models import ValidationIssue, IssueCategory, Severity


class A001_LongFieldNames(Rule):
    """Rule to audit long field names that trigger ESRI Shapefile truncation."""

    def __init__(self):
        super().__init__(
            rule_id="A001",
            name="Long Field Names",
            description="Checks for field names exceeding 10 characters in length.",
            default_severity=Severity.LOW,
            category=IssueCategory.ATTRIBUTE,
            recommendation=(
                "If exporting to Shapefile format, field names will be "
                "truncated. Rename fields to be 10 characters or less."
            ),
        )

    def evaluate(self, layer, checker=None) -> List[ValidationIssue]:
        if not hasattr(layer, "fields"):
            return []

        long_fields = [f.name() for f in layer.fields() if len(f.name()) > 10]

        if long_fields:
            return [
                ValidationIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    severity=self.severity,
                    message=f"Layer contains field names exceeding 10 characters: {', '.join(long_fields)}",
                    recommendation=self.recommendation,
                )
            ]
        return []
