# -*- coding: utf-8 -*-
"""Generates a professional HTML audit report for GeoQA validation results."""
import datetime
import html
import hashlib
from ..core.models import ProjectSummary


def generate_html_report(
    project_summary: ProjectSummary,
    qgis_version: str = "3.x",
) -> str:
    """Generates a professional, sanitized HTML validation report.

    Args:
        project_summary: The validation execution summary.
        qgis_version: QGIS software version string.

    Returns:
        str: Full HTML page as a string.
    """
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    score = project_summary.calculate_score()
    grade = project_summary.get_grade()

    # Unique report ID derived from content fingerprint
    raw_seed = f"{now}_{score}_{grade}_{len(project_summary.layer_summaries)}"
    report_id = hashlib.sha256(raw_seed.encode()).hexdigest()[:16].upper()

    # --- Theme colours ---
    themes = {
        "A": {"accent": "#16A34A", "accent_bg": "#F0FDF4", "accent_border": "#BBF7D0", "bar": "#16A34A", "verdict": "READY FOR ANALYSIS"},
        "B": {"accent": "#2563EB", "accent_bg": "#EFF6FF", "accent_border": "#BFDBFE", "bar": "#2563EB", "verdict": "READY FOR ANALYSIS"},
        "C": {"accent": "#D97706", "accent_bg": "#FFFBEB", "accent_border": "#FDE68A", "bar": "#D97706", "verdict": "REVIEW REQUIRED"},
        "D": {"accent": "#EA580C", "accent_bg": "#FFF7ED", "accent_border": "#FED7AA", "bar": "#EA580C", "verdict": "REVIEW REQUIRED"},
        "F": {"accent": "#DC2626", "accent_bg": "#FEF2F2", "accent_border": "#FECACA", "bar": "#DC2626", "verdict": "FAILED VALIDATION"},
    }
    t = themes.get(grade, themes["A"])

    # --- Aggregate metrics ---
    total_layers = len(project_summary.layer_summaries)
    total_features = sum(ls.feature_count for ls in project_summary.layer_summaries)
    total_rules = sum(len(ls.executed_rules) for ls in project_summary.layer_summaries)
    elapsed = f"{project_summary.execution_time:.2f}s" if project_summary.execution_time else "N/A"

    # --- Executive Decision content ---
    if score == 100:
        decision_detail = (
            "All validation checks have passed. No geometry, CRS, or attribute "
            "issues were detected. This dataset is cleared for use in production GIS analysis."
        )
    elif grade in ["A", "B"]:
        decision_detail = (
            "Minor quality issues were identified. The dataset is broadly suitable for "
            "analysis but you should review the flagged items before critical workflows."
        )
    elif grade == "C":
        decision_detail = (
            "Moderate quality issues detected. Resolve the flagged errors before "
            "performing spatial analysis to avoid unreliable results."
        )
    else:
        decision_detail = (
            "Significant quality issues found. This dataset requires remediation before "
            "it can be used in any analytical workflow."
        )

    # --- Severity badge HTML helper ---
    def sev_badge(sev_value: str) -> str:
        colours = {
            "low":      ("E0F2FE", "0369A1"),
            "medium":   ("FEF9C3", "854D0E"),
            "high":     ("FEF3C7", "C2410C"),
            "critical": ("FEE2E2", "991B1B"),
        }
        bg, fg = colours.get(sev_value.lower(), ("F1F5F9", "475569"))
        return (
            f'<span style="display:inline-block;padding:2px 8px;border-radius:3px;'
            f'background:#{bg};color:#{fg};font-size:11px;font-weight:700;'
            f'letter-spacing:.04em;text-transform:uppercase;">'
            f"{html.escape(sev_value)}</span>"
        )

    # --- Build Project Issues section ---
    proj_issues_html = ""
    if project_summary.project_issues:
        rows = ""
        for issue in project_summary.project_issues:
            rows += f"""
            <tr>
              <td class="mono">{html.escape(issue.rule_id)}</td>
              <td>{html.escape(issue.category.value)}</td>
              <td>{sev_badge(issue.severity.value)}</td>
              <td>{html.escape(issue.message)}</td>
              <td class="muted">{html.escape(issue.recommendation)}</td>
            </tr>"""
        proj_issues_html = f"""
        <section class="card">
          <div class="card-head">Project-Level Issues</div>
          <div class="card-body p0">
            <table>
              <thead>
                <tr>
                  <th style="width:8%">Code</th>
                  <th style="width:13%">Category</th>
                  <th style="width:10%">Severity</th>
                  <th style="width:40%">Message</th>
                  <th>Recommendation</th>
                </tr>
              </thead>
              <tbody>{rows}</tbody>
            </table>
          </div>
        </section>"""

    # --- Build per-layer sections ---
    layers_html = ""
    for layer in project_summary.layer_summaries:
        ls = layer.calculate_score()
        cat_scores = layer.calculate_category_scores()

        # Status
        if ls >= 90:
            status_label = "PASS"
            status_style = "color:#166534;background:#DCFCE7;border-color:#BBF7D0;"
        elif ls >= 70:
            status_label = "REVIEW"
            status_style = "color:#92400E;background:#FEF9C3;border-color:#FDE68A;"
        else:
            status_label = "FAIL"
            status_style = "color:#991B1B;background:#FEE2E2;border-color:#FECACA;"

        # Checks transparency
        n_executed = len(layer.executed_rules)
        n_failed = len(set(i.rule_id for i in layer.issues))
        n_passed = n_executed - n_failed
        checks_label = f"{n_passed}/{n_executed} checks passed" if n_executed else "No checks executed"

        # Category sub-scores bar
        cat_bars = ""
        for cat, val in cat_scores.items():
            bar_color = "#16A34A" if val == 100 else "#D97706" if val >= 70 else "#DC2626"
            cat_bars += f"""
              <div class="cat-row">
                <span class="cat-name">{html.escape(cat)}</span>
                <div class="cat-track">
                  <div class="cat-fill" style="width:{val}%;background:{bar_color};"></div>
                </div>
                <span class="cat-val">{val}/100</span>
              </div>"""

        # Issues table rows
        if not layer.issues:
            issue_rows = f"""
            <tr>
              <td colspan="7" class="pass-cell">
                <div class="pass-title">All checks passed</div>
                <div class="pass-checks">
                  {"".join(f'<span>{html.escape(cat)} verified</span>' for cat in cat_scores.keys())}
                </div>
              </td>
            </tr>"""
        else:
            issue_rows = ""
            for issue in layer.issues:
                affected_html = "—"
                if issue.affected_features:
                    fids = [str(f) for f in issue.affected_features[:20]]
                    extra = f" +{len(issue.affected_features) - 20} more" if len(issue.affected_features) > 20 else ""
                    affected_html = (
                        f'<span class="count">{len(issue.affected_features)} features</span><br>'
                        f'<span class="mono small muted">{html.escape(", ".join(fids))}{html.escape(extra)}</span>'
                    )
                issue_rows += f"""
                <tr>
                  <td class="mono">{html.escape(issue.rule_id)}</td>
                  <td>{html.escape(issue.category.value)}</td>
                  <td>{sev_badge(issue.severity.value)}</td>
                  <td class="mono">{html.escape(issue.field_name or "—")}</td>
                  <td>{html.escape(issue.message)}</td>
                  <td class="muted">{html.escape(issue.recommendation)}</td>
                  <td>{affected_html}</td>
                </tr>"""

        # Rule timing block — always shown when rules were executed
        timing_html = ""
        if layer.rule_durations:
            timing_rows = "".join(
                f'<tr><td class="mono">{html.escape(r_id)}</td><td>{dur:.4f} s</td></tr>'
                for r_id, dur in sorted(layer.rule_durations.items())
            )
            timing_html = f"""
            <div class="timing-block">
              <div class="timing-head">Validation Performance</div>
              <table style="width:auto;font-size:12px;">
                <thead><tr><th>Rule</th><th>Duration</th></tr></thead>
                <tbody>{timing_rows}</tbody>
              </table>
            </div>"""

        layer_name_esc = html.escape(layer.layer_name)
        geom_esc = html.escape(layer.geometry_type)
        crs_esc = html.escape(layer.crs_authid)

        layers_html += f"""
        <section class="card">
          <div class="card-head layer-head">
            <div class="layer-left">
              <span class="layer-name">{layer_name_esc}</span>
              <span class="pill">{geom_esc}</span>
              <span class="pill">{crs_esc}</span>
              <span class="pill">{layer.feature_count:,} features</span>
            </div>
            <div class="layer-right">
              <span class="muted small" style="margin-right:8px;">{checks_label}</span>
              <span class="layer-score">{ls}/100</span>
              <span class="status-badge" style="{status_style}">{status_label}</span>
            </div>
          </div>
          <div class="cat-breakdown">
            {cat_bars}
          </div>
          <div class="card-body p0">
            <table>
              <thead>
                <tr>
                  <th style="width:7%">Code</th>
                  <th style="width:11%">Category</th>
                  <th style="width:9%">Severity</th>
                  <th style="width:10%">Field</th>
                  <th style="width:28%">Message</th>
                  <th style="width:25%">Recommendation</th>
                  <th style="width:10%">Affected</th>
                </tr>
              </thead>
              <tbody>{issue_rows}</tbody>
            </table>
          </div>
          {timing_html}
        </section>"""

    # ============================================================
    # HTML TEMPLATE
    # ============================================================
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GeoQA Validation Report — {report_id}</title>
<style>
  /* ── Reset ── */
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  /* ── Base ── */
  body {{
    font-family: "Segoe UI", system-ui, -apple-system, Helvetica, Arial, sans-serif;
    font-size: 14px;
    line-height: 1.55;
    color: #1E293B;
    background: #F1F5F9;
  }}

  a {{ color: #2563EB; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}

  /* ── Layout ── */
  .wrap {{
    max-width: 1140px;
    margin: 0 auto;
    padding: 36px 24px 60px;
  }}

  /* ── Header ── */
  .report-header {{
    background: #1E293B;
    color: #F8FAFC;
    padding: 28px 32px;
    border-radius: 8px;
    margin-bottom: 28px;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    gap: 24px;
    flex-wrap: wrap;
  }}
  .report-header h1 {{
    font-size: 22px;
    font-weight: 700;
    letter-spacing: -.01em;
    color: #F8FAFC;
  }}
  .report-header .tagline {{
    font-size: 13px;
    color: #94A3B8;
    margin-top: 4px;
  }}
  .meta-list {{
    display: flex;
    gap: 0 28px;
    flex-wrap: wrap;
    text-align: right;
    font-size: 12.5px;
    color: #94A3B8;
    justify-content: flex-end;
  }}
  .meta-list .m-item {{
    display: flex;
    flex-direction: column;
    gap: 1px;
  }}
  .meta-list .m-lbl {{
    font-size: 10.5px;
    text-transform: uppercase;
    letter-spacing: .06em;
    color: #64748B;
    font-weight: 600;
  }}
  .meta-list .m-val {{
    color: #CBD5E1;
    font-weight: 600;
  }}

  /* ── Verdict Banner ── */
  .verdict-banner {{
    background: {t['accent_bg']};
    border: 1px solid {t['accent_border']};
    border-left: 5px solid {t['accent']};
    border-radius: 8px;
    padding: 24px 28px;
    margin-bottom: 28px;
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 24px;
    align-items: start;
  }}
  .verdict-label {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: .1em;
    text-transform: uppercase;
    color: {t['accent']};
    margin-bottom: 6px;
  }}
  .verdict-title {{
    font-size: 26px;
    font-weight: 800;
    color: {t['accent']};
    letter-spacing: -.02em;
    margin-bottom: 10px;
  }}
  .verdict-detail {{
    font-size: 14px;
    color: #334155;
    line-height: 1.65;
    max-width: 620px;
  }}
  .verdict-metrics {{
    display: flex;
    flex-direction: column;
    gap: 12px;
    min-width: 180px;
    border-left: 1px solid {t['accent_border']};
    padding-left: 24px;
  }}
  .v-metric {{ display: flex; flex-direction: column; gap: 1px; }}
  .v-metric .v-val {{
    font-size: 22px;
    font-weight: 800;
    color: {t['accent']};
    line-height: 1;
  }}
  .v-metric .v-lbl {{
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: .06em;
    color: #64748B;
    font-weight: 600;
  }}

  /* ── Score Bar ── */
  .score-bar-wrap {{
    background: #E2E8F0;
    border-radius: 4px;
    height: 8px;
    overflow: hidden;
    margin-bottom: 28px;
  }}
  @keyframes growBar {{
    from {{ width: 0; }}
    to   {{ width: {score}%; }}
  }}
  .score-bar-fill {{
    height: 100%;
    background: {t['bar']};
    border-radius: 4px;
    animation: growBar .9s ease-out forwards;
  }}

  /* ── Dashboard Cards ── */
  .dashboard {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 16px;
    margin-bottom: 28px;
  }}
  .d-card {{
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 18px 20px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }}
  .d-val {{
    font-size: 28px;
    font-weight: 800;
    color: #1E293B;
    line-height: 1;
  }}
  .d-lbl {{
    font-size: 11.5px;
    text-transform: uppercase;
    letter-spacing: .06em;
    color: #64748B;
    font-weight: 600;
    margin-top: 4px;
  }}
  .d-card.accent {{ border-top: 3px solid {t['accent']}; }}

  /* ── Cards ── */
  .card {{
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    margin-bottom: 20px;
    overflow: hidden;
  }}
  .card-head {{
    padding: 14px 20px;
    border-bottom: 1px solid #E2E8F0;
    background: #F8FAFC;
    font-weight: 700;
    font-size: 14px;
    color: #1E293B;
  }}
  .layer-head {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;
  }}
  .layer-left {{
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }}
  .layer-name {{
    font-size: 15px;
    font-weight: 700;
    color: #1E293B;
  }}
  .layer-right {{
    display: flex;
    align-items: center;
    gap: 10px;
  }}
  .layer-score {{
    font-size: 15px;
    font-weight: 800;
    color: #1E293B;
  }}
  .status-badge {{
    padding: 3px 10px;
    border-radius: 3px;
    border: 1px solid;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: .06em;
    text-transform: uppercase;
  }}

  /* ── Category breakdown ── */
  .cat-breakdown {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 8px 24px;
    padding: 14px 20px;
    border-bottom: 1px solid #E2E8F0;
    background: #FAFAFA;
  }}
  .cat-row {{ display: flex; align-items: center; gap: 8px; }}
  .cat-name {{
    font-size: 12px;
    font-weight: 600;
    color: #64748B;
    width: 72px;
    flex-shrink: 0;
  }}
  .cat-track {{
    flex: 1;
    height: 6px;
    background: #E2E8F0;
    border-radius: 3px;
    overflow: hidden;
  }}
  .cat-fill {{
    height: 100%;
    border-radius: 3px;
    transition: width .4s ease;
  }}
  .cat-val {{
    font-size: 12px;
    font-weight: 700;
    color: #475569;
    width: 52px;
    text-align: right;
    flex-shrink: 0;
  }}

  /* ── Pill badges ── */
  .pill {{
    display: inline-block;
    padding: 2px 8px;
    background: #E2E8F0;
    color: #475569;
    border-radius: 3px;
    font-size: 12px;
    font-weight: 600;
    white-space: nowrap;
  }}

  /* ── Card body / table ── */
  .card-body {{ padding: 20px; }}
  .p0 {{ padding: 0 !important; }}
  .card-body.p0 table {{ margin: 0; }}

  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
  }}
  thead tr {{ background: #F8FAFC; }}
  th {{
    padding: 9px 16px;
    text-align: left;
    font-size: 11.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .05em;
    color: #64748B;
    border-bottom: 1px solid #E2E8F0;
    white-space: nowrap;
  }}
  td {{
    padding: 11px 16px;
    border-bottom: 1px solid #F1F5F9;
    vertical-align: top;
    color: #334155;
  }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td {{ background: #FAFAFA; }}

  /* ── Pass cell ── */
  .pass-cell {{
    text-align: center;
    padding: 32px !important;
    background: #F8FAFC;
  }}
  .pass-title {{
    font-size: 15px;
    font-weight: 700;
    color: #16A34A;
    margin-bottom: 10px;
  }}
  .pass-checks {{
    display: flex;
    justify-content: center;
    gap: 20px;
    flex-wrap: wrap;
    font-size: 12.5px;
    color: #64748B;
    font-weight: 600;
  }}

  /* ── Timing block ── */
  .timing-block {{
    border-top: 1px solid #E2E8F0;
    padding: 14px 20px;
    background: #F8FAFC;
  }}
  .timing-head {{
    font-size: 11.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .06em;
    color: #94A3B8;
    margin-bottom: 8px;
  }}

  /* ── Utility ── */
  .mono {{ font-family: "Consolas", "Courier New", monospace; font-size: 12.5px; }}
  .muted {{ color: #64748B; }}
  .small {{ font-size: 12px; }}
  .count {{ font-weight: 700; color: #1E293B; }}

  /* ── Footer ── */
  footer {{
    margin-top: 48px;
    padding-top: 20px;
    border-top: 1px solid #E2E8F0;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
    font-size: 12.5px;
    color: #94A3B8;
  }}
  footer .brand {{
    font-weight: 700;
    color: #64748B;
    font-style: italic;
  }}
  footer .links {{ display: flex; gap: 16px; }}
  footer .links span {{ color: #94A3B8; font-weight: 600; }}

  /* ── Print ── */
  @media print {{
    body {{ background: #FFF; }}
    .wrap {{ padding: 0; }}
    .report-header {{ border-radius: 0; }}
    .card {{ break-inside: avoid; }}
  }}
</style>
</head>
<body>
<div class="wrap">

  <!-- Header -->
  <header class="report-header">
    <div>
      <h1>GeoQA Validation Report</h1>
      <div class="tagline">GIS Data Quality Audit — Validate first. Analyze second.</div>
    </div>
    <div class="meta-list">
      <div class="m-item"><div class="m-lbl">Report ID</div><div class="m-val mono">{report_id}</div></div>
      <div class="m-item"><div class="m-lbl">Profile</div><div class="m-val">{html.escape(project_summary.profile_name)}</div></div>
      <div class="m-item"><div class="m-lbl">Plugin</div><div class="m-val">GeoQA v1.0.0</div></div>
      <div class="m-item"><div class="m-lbl">QGIS</div><div class="m-val">{html.escape(qgis_version)}</div></div>
      <div class="m-item"><div class="m-lbl">Generated</div><div class="m-val">{now}</div></div>
    </div>
  </header>

  <!-- Verdict Banner -->
  <div class="verdict-banner">
    <div>
      <div class="verdict-label">Executive Decision</div>
      <div class="verdict-title">{t['verdict']}</div>
      <div class="verdict-detail">{decision_detail}</div>
    </div>
    <div class="verdict-metrics">
      <div class="v-metric">
        <div class="v-val">{score}/100</div>
        <div class="v-lbl">Quality Score</div>
      </div>
      <div class="v-metric">
        <div class="v-val">{grade}</div>
        <div class="v-lbl">Audit Grade</div>
      </div>
      <div class="v-metric">
        <div class="v-val">{project_summary.total_errors}</div>
        <div class="v-lbl">Errors</div>
      </div>
    </div>
  </div>

  <!-- Score bar -->
  <div class="score-bar-wrap">
    <div class="score-bar-fill"></div>
  </div>

  <!-- Dashboard -->
  <div class="dashboard">
    <div class="d-card accent">
      <div class="d-val">{total_layers}</div>
      <div class="d-lbl">Layers Audited</div>
    </div>
    <div class="d-card">
      <div class="d-val">{total_features:,}</div>
      <div class="d-lbl">Total Features</div>
    </div>
    <div class="d-card">
      <div class="d-val">{project_summary.total_errors}</div>
      <div class="d-lbl">Errors</div>
    </div>
    <div class="d-card">
      <div class="d-val">{project_summary.total_warnings}</div>
      <div class="d-lbl">Warnings</div>
    </div>
    <div class="d-card">
      <div class="d-val">{total_rules}</div>
      <div class="d-lbl">Rules Executed</div>
    </div>
    <div class="d-card">
      <div class="d-val">{elapsed}</div>
      <div class="d-lbl">Elapsed Time</div>
    </div>
  </div>

  <!-- Project Issues -->
  {proj_issues_html}

  <!-- Layer Audits -->
  {layers_html}

  <!-- Footer -->
  <footer>
    <span class="brand">GeoQA — GIS Data Quality Auditor</span>
    <div class="links">
      <span>Open Source</span>
      <span>|</span>
      <span>GPL v3</span>
      <span>|</span>
      <span>Report ID: {report_id}</span>
    </div>
  </footer>

</div>
</body>
</html>
"""
