# -*- coding: utf-8 -*-
from typing import List
from ..base import Rule
from ...models import ValidationIssue, IssueCategory, Severity
from ...compat import GISCompat


class A004_EmptyStrings(Rule):
    """Rule to audit text fields for empty or whitespace-only strings."""

    def __init__(self):
        super().__init__(
            rule_id="A004",
            name="Empty Strings",
            description="Checks text fields for empty or whitespace-only records.",
            default_severity=Severity.MEDIUM,
            category=IssueCategory.ATTRIBUTE,
            recommendation="Clean empty text fields and convert them to standard NULL or default markers.",
        )

    def evaluate(self, layer, checker=None) -> List[ValidationIssue]:
        if not hasattr(layer, "fields"):
            return []

        fields = layer.fields()
        string_fields = [
            f.name()
            for f in fields
            if any(
                t in f.typeName().lower()
                for t in ("string", "text", "varchar", "char", "memo")
            )
        ]
        if not string_fields:
            return []

        empty_fids_by_field = {name: [] for name in string_fields}

        for idx, feature in enumerate(
            GISCompat.get_features_for_attributes(layer, string_fields)
        ):
            if idx % 5000 == 0 and checker:
                is_cancelled = (
                    checker.isCanceled()
                    if hasattr(checker, "isCanceled")
                    else checker.isCancelled()
                )
                if is_cancelled:
                    return []

            fid = feature.id()
            for name in string_fields:
                val = feature[name]
                if val is not None:
                    is_null = False
                    if hasattr(val, "isNull"):
                        is_null = val.isNull()
                    if not is_null:
                        if str(val).strip() == "":
                            empty_fids_by_field[name].append(fid)

        issues = []
        for name, fids in empty_fids_by_field.items():
            if fids:
                issues.append(
                    ValidationIssue(
                        rule_id=self.rule_id,
                        category=self.category,
                        severity=self.severity,
                        message=f"Field '{name}' contains {len(fids)} empty/whitespace strings.",
                        recommendation=self.recommendation,
                        affected_features=fids,
                        field_name=name,
                    )
                )
        return issues
