# -*- coding: utf-8 -*-
"""Attribute validation logic: null values, empty strings, duplicate IDs, reserved keywords, and numeric strings."""
from typing import List, Dict, Set, Any
from .base import BaseValidator
from ..models import ValidationIssue, IssueCategory, Severity


class AttributeValidator(BaseValidator):
    """Validator for tabular attribute issues in a layer."""

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

    ID_FIELD_KEYWORDS = {
        "id",
        "fid",
        "uuid",
        "objectid",
        "gid",
        "pk",
        "key",
        "identifier",
    }

    @property
    def name(self) -> str:
        return "Attribute Validator"

    def validate(self, layer) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []

        if not hasattr(layer, "fields"):
            return issues

        fields = layer.fields()
        field_names = [f.name() for f in fields]

        # 1. Field Name Checks (Long names & Reserved names)
        long_fields: List[str] = []
        reserved_fields: List[str] = []
        for name in field_names:
            if len(name) > 10:
                long_fields.append(name)
            if name.upper() in self.RESERVED_WORDS:
                reserved_fields.append(name)

        if long_fields:
            issues.append(
                ValidationIssue(
                    rule_id="A001",
                    category=IssueCategory.ATTRIBUTE,
                    severity=Severity.LOW,
                    message=f"Layer contains field names exceeding 10 characters: {', '.join(long_fields)}",
                    recommendation=(
                        "If exporting to ESRI Shapefile format, these field names "
                        "will be truncated, potentially causing data structure errors. "
                        "Keep field names under 10 characters."
                    ),
                )
            )

        if reserved_fields:
            issues.append(
                ValidationIssue(
                    rule_id="A002",
                    category=IssueCategory.ATTRIBUTE,
                    severity=Severity.LOW,
                    message=f"Layer contains fields matching database reserved words: {', '.join(reserved_fields)}",
                    recommendation=(
                        "Avoid using SQL or GIS system keywords as field names "
                        "to prevent errors when querying or exporting to databases "
                        "(SpatiaLite, PostGIS)."
                    ),
                )
            )

        # 2. Setup structures for feature-level checks
        null_fids_by_field: Dict[str, List[int]] = {name: [] for name in field_names}
        empty_str_fids_by_field: Dict[str, List[int]] = {
            name: [] for name in field_names
        }

        # ID fields duplicate check
        id_fields = [
            name
            for name in field_names
            if any(kw in name.lower() for kw in self.ID_FIELD_KEYWORDS)
        ]
        seen_values_by_field: Dict[str, Set[Any]] = {name: set() for name in id_fields}
        duplicate_fids_by_field: Dict[str, List[int]] = {name: [] for name in id_fields}

        # Numeric-in-text check
        # For string fields, check if all populated values are actually numbers (ints or floats)
        # We store: field_name -> (has_any_value: bool, all_numeric_so_far: bool)
        string_fields = [
            f.name()
            for f in fields
            if f.typeName().lower() in ("string", "text", "varchar")
        ]
        numeric_text_tracker: Dict[str, Dict[str, Any]] = {
            name: {"has_values": False, "only_numeric": True} for name in string_fields
        }

        # 3. Scan Features
        for feature in layer.getFeatures():
            fid = feature.id()

            for field in fields:
                name = field.name()
                val = feature[name]

                # Check for Null (None or QVariant NULL representation)
                # In QGIS API, a null value can be represented by None or QVariant NULL.
                # In python it's typically None or check using isNull()
                is_null = val is None
                if not is_null and hasattr(val, "isNull"):
                    is_null = val.isNull()

                if is_null:
                    null_fids_by_field[name].append(fid)
                    continue

                # Empty string check for string types
                if name in string_fields:
                    val_str = str(val).strip()
                    if val_str == "":
                        empty_str_fids_by_field[name].append(fid)
                    else:
                        numeric_text_tracker[name]["has_values"] = True
                        if numeric_text_tracker[name]["only_numeric"]:
                            try:
                                float(val_str)
                            except ValueError:
                                numeric_text_tracker[name]["only_numeric"] = False

                # Duplicate check for ID fields
                if name in id_fields:
                    if val in seen_values_by_field[name]:
                        duplicate_fids_by_field[name].append(fid)
                    else:
                        seen_values_by_field[name].add(val)

        # 4. Generate tabular check reports
        for name, fids in null_fids_by_field.items():
            if fids:
                issues.append(
                    ValidationIssue(
                        rule_id="A003",
                        category=IssueCategory.ATTRIBUTE,
                        severity=Severity.MEDIUM,
                        message=f"Field '{name}' contains {len(fids)} NULL values.",
                        recommendation="Fill in missing values or verify if NULL values are acceptable for this field.",
                        affected_features=fids,
                        field_name=name,
                    )
                )

        for name, fids in empty_str_fids_by_field.items():
            if fids:
                issues.append(
                    ValidationIssue(
                        rule_id="A004",
                        category=IssueCategory.ATTRIBUTE,
                        severity=Severity.MEDIUM,
                        message=f"Field '{name}' contains {len(fids)} empty/whitespace string values.",
                        recommendation=(
                            "Clean the dataset to replace empty string entries "
                            "with NULL or proper default values."
                        ),
                        affected_features=fids,
                        field_name=name,
                    )
                )

        for name, fids in duplicate_fids_by_field.items():
            if fids:
                issues.append(
                    ValidationIssue(
                        rule_id="A005",
                        category=IssueCategory.ATTRIBUTE,
                        severity=Severity.HIGH,
                        message=f"Identifier field '{name}' contains duplicate values across {len(fids)} features.",
                        recommendation=(
                            "Unique identifier fields should contain distinct values. "
                            "Regenerate unique IDs using QGIS Field Calculator ($id or uuid())."
                        ),
                        affected_features=fids,
                        field_name=name,
                    )
                )

        # Check numeric text fields
        for name, info in numeric_text_tracker.items():
            if info["has_values"] and info["only_numeric"]:
                issues.append(
                    ValidationIssue(
                        rule_id="A006",
                        category=IssueCategory.ATTRIBUTE,
                        severity=Severity.LOW,
                        message=f"String field '{name}' contains purely numeric values.",
                        recommendation=(
                            "Convert this field to an Integer or Double type to "
                            "allow mathematical operations and improve storage efficiency."
                        ),
                        field_name=name,
                    )
                )

        return issues
