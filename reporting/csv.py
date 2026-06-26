# -*- coding: utf-8 -*-
import csv
import io
from ..core.models import ProjectSummary


def sanitize_csv_value(val) -> str:
    """Sanitizes cells starting with characters that trigger formula execution (CSV injection)."""
    if val is None:
        return ""
    val_str = str(val).strip()
    if val_str and val_str[0] in ("=", "+", "-", "@"):
        # Prepend a single quote to prevent spreadsheet engines from executing the value as an expression
        return "'" + val_str
    return val_str


def generate_csv_report(project_summary: ProjectSummary) -> str:
    """Generates a CSV report string from a ProjectSummary.

    Args:
        project_summary: The aggregated validation results.

    Returns:
        str: CSV content as a string.
    """
    output = io.StringIO()
    output.write("\ufeff")  # UTF-8 BOM — ensures Excel on Windows opens with correct encoding
    writer = csv.writer(output, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)

    # Write CSV Header
    writer.writerow(
        [
            "Layer Name",
            "Rule Code",
            "Category",
            "Severity",
            "Field Name",
            "Issue Message",
            "Recommendation",
            "Affected Features Count",
            "Affected Feature IDs",
        ]
    )

    # Write Project/Cross-Layer issues first
    for issue in project_summary.project_issues:
        ids_list = issue.affected_features[:1000]
        ids_str = ";".join(str(fid) for fid in ids_list)
        if len(issue.affected_features) > 1000:
            ids_str += f";...and {len(issue.affected_features) - 1000} more"

        row = [
            "PROJECT_LEVEL",
            issue.rule_id,
            issue.category.value,
            issue.severity.value,
            issue.field_name or "",
            issue.message,
            issue.recommendation,
            len(issue.affected_features),
            ids_str,
        ]
        writer.writerow([sanitize_csv_value(cell) for cell in row])

    # Write individual Layer issues
    for layer in project_summary.layer_summaries:
        if not layer.issues:
            row = [
                layer.layer_name,
                "None",
                "None",
                "None",
                "",
                "No issues detected.",
                "None",
                0,
                "",
            ]
            writer.writerow([sanitize_csv_value(cell) for cell in row])
            continue

        for issue in layer.issues:
            ids_list = issue.affected_features[:1000]
            ids_str = ";".join(str(fid) for fid in ids_list)
            if len(issue.affected_features) > 1000:
                ids_str += f";...and {len(issue.affected_features) - 1000} more"

            row = [
                layer.layer_name,
                issue.rule_id,
                issue.category.value,
                issue.severity.value,
                issue.field_name or "",
                issue.message,
                issue.recommendation,
                len(issue.affected_features),
                ids_str,
            ]
            writer.writerow([sanitize_csv_value(cell) for cell in row])

    return output.getvalue()
