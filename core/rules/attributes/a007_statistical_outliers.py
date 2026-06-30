# -*- coding: utf-8 -*-
import math
from typing import List
from ..base import Rule
from ...models import ValidationIssue, IssueCategory, Severity
from ...compat import GISCompat


class A007_StatisticalOutliers(Rule):
    """Rule to audit fields for statistical outliers using Z-score (3 standard deviations)."""

    def __init__(self):
        super().__init__(
            rule_id="A007",
            name="Statistical Outliers",
            description="Checks numeric columns for statistical outliers exceeding 3 standard deviations.",
            default_severity=Severity.LOW,
            category=IssueCategory.ATTRIBUTE,
            recommendation="Value deviates significantly from the field average (greater than 3 standard deviations). Verify if this is a data entry typo.",
        )

    def evaluate(self, layer, checker=None) -> List[ValidationIssue]:
        if not hasattr(layer, "fields"):
            return []

        fields = layer.fields()
        numeric_field_names = []
        for field in fields:
            if hasattr(field, "isNumeric") and field.isNumeric():
                numeric_field_names.append(field.name())

        if not numeric_field_names:
            return []

        # Pass 1: Collect numeric values to compute mean and standard deviation
        values_by_field = {name: [] for name in numeric_field_names}

        for idx, feature in enumerate(
            # Fetch numeric attributes only
            GISCompat.get_features_for_attributes(layer, numeric_field_names)
        ):
            if idx % 5000 == 0 and checker:
                is_cancelled = (
                    checker.isCanceled()
                    if hasattr(checker, "isCanceled")
                    else checker.isCancelled()
                )
                if is_cancelled:
                    return []

            for name in numeric_field_names:
                val = feature[name]
                if val is not None:
                    try:
                        float_val = float(val)
                        values_by_field[name].append((feature.id(), float_val))
                    except (ValueError, TypeError):
                        continue

        issues = []
        for name in numeric_field_names:
            records = values_by_field[name]
            n = len(records)
            if n < 10:
                # We need at least 10 samples to calculate standard deviation meaningfully
                continue

            vals = [rec[1] for rec in records]
            mean = sum(vals) / n

            # Calculate standard deviation
            variance = sum((x - mean) ** 2 for x in vals) / n
            std_dev = math.sqrt(variance)

            if std_dev <= 0:
                continue

            outlier_fids = []
            for fid, val in records:
                z_score = abs(val - mean) / std_dev
                if z_score > 3.0:
                    outlier_fids.append(fid)

            if outlier_fids:
                issues.append(
                    ValidationIssue(
                        rule_id=self.rule_id,
                        category=self.category,
                        severity=self.severity,
                        message=(
                            f"Field '{name}' contains {len(outlier_fids)} statistical outliers "
                            f"exceeding 3 standard deviations (Mean: {mean:.2f}, StdDev: {std_dev:.2f})."
                        ),
                        recommendation=self.recommendation,
                        affected_features=outlier_fids,
                        field_name=name,
                    )
                )

        return issues
