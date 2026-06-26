# -*- coding: utf-8 -*-
from typing import List
from ..base import Rule
from ...models import ValidationIssue, IssueCategory, Severity
from ...compat import GISCompat


class A005_DuplicateIdentifiers(Rule):
    """Rule to audit columns for duplicate identifier entries."""

    ID_KEYWORDS = {"id", "fid", "uuid", "objectid", "gid", "pk", "key", "identifier"}

    def __init__(self):
        super().__init__(
            rule_id="A005",
            name="Duplicate Identifiers",
            description="Checks columns identifying unique records (e.g. ID, OBJECTID) for duplicate values.",
            default_severity=Severity.HIGH,
            category=IssueCategory.ATTRIBUTE,
            recommendation=(
                "Unique identifier fields should contain distinct values. "
                "Regenerate unique IDs using QGIS Field Calculator ($id or uuid())."
            ),
        )

    def evaluate(self, layer, checker=None) -> List[ValidationIssue]:
        if not hasattr(layer, "fields"):
            return []

        fields = layer.fields()
        id_fields = [
            f.name()
            for f in fields
            if any(kw in f.name().lower() for kw in self.ID_KEYWORDS)
        ]
        if not id_fields:
            return []

        seen_values = {name: set() for name in id_fields}
        duplicate_fids_by_field = {name: [] for name in id_fields}

        for idx, feature in enumerate(
            GISCompat.get_features_for_attributes(layer, id_fields)
        ):
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
            for name in id_fields:
                val = feature[name]
                is_null = val is None
                if not is_null and hasattr(val, "isNull"):
                    is_null = val.isNull()
                if is_null:
                    continue

                if val in seen_values[name]:
                    duplicate_fids_by_field[name].append(fid)
                else:
                    seen_values[name].add(val)

        issues = []
        for name, fids in duplicate_fids_by_field.items():
            if fids:
                issues.append(
                    ValidationIssue(
                        rule_id=self.rule_id,
                        category=self.category,
                        severity=self.severity,
                        message=f"Identifier field '{name}' contains duplicate values across {len(fids)} features.",
                        recommendation=self.recommendation,
                        affected_features=fids,
                        field_name=name,
                    )
                )
        return issues
