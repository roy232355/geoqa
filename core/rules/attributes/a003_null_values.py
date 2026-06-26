# -*- coding: utf-8 -*-
from typing import List
from ..base import Rule
from ...models import ValidationIssue, IssueCategory, Severity
from ...compat import GISCompat


class A003_NullValues(Rule):
    """Rule to audit fields for NULL values."""

    def __init__(self):
        super().__init__(
            rule_id="A003",
            name="Null Values",
            description="Checks columns for NULL (missing) values.",
            default_severity=Severity.MEDIUM,
            category=IssueCategory.ATTRIBUTE,
            recommendation="Verify if missing values are expected for this field or populate with default values.",
        )

    def evaluate(self, layer, checker=None) -> List[ValidationIssue]:
        if not hasattr(layer, "fields"):
            return []

        fields = layer.fields()
        field_names = [f.name() for f in fields]
        null_fids_by_field = {name: [] for name in field_names}

        for idx, feature in enumerate(GISCompat.get_features_for_attributes(layer)):
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

            fid = feature.id()
            for field in fields:
                name = field.name()
                val = feature[name]
                is_null = val is None
                if not is_null and hasattr(val, "isNull"):
                    is_null = val.isNull()
                if is_null:
                    null_fids_by_field[name].append(fid)

        issues = []
        for name, fids in null_fids_by_field.items():
            if fids:
                issues.append(
                    ValidationIssue(
                        rule_id=self.rule_id,
                        category=self.category,
                        severity=self.severity,
                        message=f"Field '{name}' contains {len(fids)} NULL values.",
                        recommendation=self.recommendation,
                        affected_features=fids,
                        field_name=name,
                    )
                )
        return issues
