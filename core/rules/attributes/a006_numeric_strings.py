# -*- coding: utf-8 -*-
from typing import List
from ..base import Rule
from ...models import ValidationIssue, IssueCategory, Severity
from ...compat import GISCompat


class A006_NumericStrings(Rule):
    """Rule to audit text fields for numeric values, recommending field type optimization."""

    def __init__(self):
        super().__init__(
            rule_id="A006",
            name="Numeric String Optimization",
            description="Checks text fields for columns containing exclusively numeric data.",
            default_severity=Severity.LOW,
            category=IssueCategory.ATTRIBUTE,
            recommendation=(
                "Convert this field to an Integer or Double type to allow "
                "mathematical operations and improve storage efficiency."
            ),
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

        numeric_text_tracker = {
            name: {"has_values": False, "only_numeric": True} for name in string_fields
        }

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

            for name in string_fields:
                val = feature[name]
                if val is not None:
                    is_null = False
                    if hasattr(val, "isNull"):
                        is_null = val.isNull()
                    if not is_null:
                        val_str = str(val).strip()
                        if val_str != "":
                            numeric_text_tracker[name]["has_values"] = True
                            if numeric_text_tracker[name]["only_numeric"]:
                                try:
                                    float(val_str)
                                except ValueError:
                                    numeric_text_tracker[name]["only_numeric"] = False

        issues = []
        for name, info in numeric_text_tracker.items():
            if info["has_values"] and info["only_numeric"]:
                issues.append(
                    ValidationIssue(
                        rule_id=self.rule_id,
                        category=self.category,
                        severity=self.severity,
                        message=f"String field '{name}' contains purely numeric values.",
                        recommendation=self.recommendation,
                        field_name=name,
                    )
                )
        return issues
