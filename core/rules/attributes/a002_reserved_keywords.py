# -*- coding: utf-8 -*-
from typing import List
from ..base import Rule
from ...models import ValidationIssue, IssueCategory, Severity


class A002_ReservedKeywords(Rule):
    """Rule to audit fields named after SQL/DB reserved words."""

    RESERVED_WORDS = {
        "SELECT",
        "INSERT",
        "UPDATE",
        "DELETE",
        "WHERE",
        "FROM",
        "TABLE",
        "JOIN",
        "INDEX",
        "GROUP",
        "ORDER",
        "AS",
        "AND",
        "OR",
        "NOT",
        "NULL",
        "UNION",
        "ALL",
        "CREATE",
        "DROP",
        "ALTER",
        "GEOMETRY",
        "FID",
        "OID",
        "OBJECTID",
        "SHAPE",
        "X",
        "Y",
    }

    def __init__(self):
        super().__init__(
            rule_id="A002",
            name="Reserved Database Keywords",
            description="Flags fields matching SQL or GIS database reserved keywords.",
            default_severity=Severity.LOW,
            category=IssueCategory.ATTRIBUTE,
            recommendation="Rename columns to avoid errors when exporting to SpatiaLite, PostGIS, or databases.",
        )

    def evaluate(self, layer, checker=None) -> List[ValidationIssue]:
        if not hasattr(layer, "fields"):
            return []

        reserved_fields = [
            f.name() for f in layer.fields() if f.name().upper() in self.RESERVED_WORDS
        ]

        if reserved_fields:
            return [
                ValidationIssue(
                    rule_id=self.rule_id,
                    category=self.category,
                    severity=self.severity,
                    message=f"Layer contains fields matching reserved words: {', '.join(reserved_fields)}",
                    recommendation=self.recommendation,
                )
            ]
        return []
