# GeoQA – GIS Data Quality Auditor

[![QGIS Plugin](https://img.shields.io/badge/QGIS-Plugin%20Repository-589632?logo=qgis&logoColor=white)](https://plugins.qgis.org/plugins/GeoQA)
[![Version](https://img.shields.io/badge/version-1.1.0-blue)](https://github.com/roy232355/geoqa/releases/tag/v1.1.0)
[![License](https://img.shields.io/badge/license-GPL%20v3-green)](LICENSE)
[![QGIS](https://img.shields.io/badge/QGIS-%3E%3D%203.28-589632)](https://qgis.org)
[![Status](https://img.shields.io/badge/status-stable-brightgreen)]()

> **Validate first. Analyze second.**

Validate your GIS data before analysis.

GeoQA is an open-source Quality Assurance plugin for QGIS that helps identify geometry, CRS, and attribute issues through a modular rule-based validation engine. Generate professional audit reports, improve data reliability, and ensure reproducible GIS workflows.

- Lightweight
- Offline
- Rule-based
- Extensible
- Open Source
- Professional Reports

---

## Short Description
GeoQA is an open-source QGIS plugin that helps GIS professionals, researchers, and students identify common data quality issues before performing spatial analysis. It automatically audits vector layers for geometry, coordinate reference system (CRS), and attribute problems, then generates a professional validation report with severity levels and recommended fixes.

Designed as a lightweight, extensible quality assurance framework, GeoQA simplifies data validation while promoting reproducible and reliable GIS workflows.

## Long Description
Many GIS workflows fail because of hidden data issues such as invalid geometries, missing coordinate reference systems, duplicate identifiers, or incomplete attribute information. GeoQA provides an automated validation engine that detects these issues, categorizes them by severity, and generates professional reports with practical recommendations.

Rather than replacing existing QGIS Processing tools, GeoQA acts as a pre-analysis auditing layer that helps ensure datasets are reliable before they enter any GIS workflow.

GeoQA is designed with a modular architecture that allows future expansion into domain-specific quality assurance profiles for health, infrastructure, climate, environmental, and urban planning applications.

## Objectives
- Improving GIS data quality
- Reducing preprocessing time
- Increasing reproducibility
- Providing professional audit reports
- Supporting researchers and GIS professionals

## Target Users
* GIS Analysts
* Remote Sensing Specialists
* Civil Engineers
* Environmental Scientists
* Public Health Researchers
* Urban Planners
* Students
* Universities
* Government Agencies
* Consultants

## Features

### Geometry Validation
* **Invalid geometries (`G001`):** Self-intersections, open loops, and OGC boundary violations.
* **Empty geometries (`G002`):** Null shapes or missing coordinates records.
* **Multipart geometries (`G003`):** Identifies geometry parts that can be split to singlepart vectors.
* **Duplicate geometries (`G004`):** Fast O(N) coordinates byte-matching check.
* **Sliver geometries (`G005`):** Thin, narrow polygon artifacts checked via the scale-invariant Polsby-Popper compactness metric.

### CRS Validation
* **Missing CRS (`C001`):** Vector layers with undefined coordinate reference systems.
* **Geographic CRS warnings (`C002`):** Warns if working in degrees (EPSG:4326) instead of meters (projected UTM) for planar measurements.

### Attribute Validation
* **Long field names (`A001`):** Warns if column headers exceed Shapefile's 10-character limitation.
* **Reserved SQL keywords (`A002`):** Flags column names matching SQL commands (e.g. `SELECT`, `WHERE`).
* **Null values (`A003`):** Missing values detection.
* **Empty strings (`A004`):** Flags columns with empty spaces or whitespace strings.
* **Duplicate identifiers (`A005`):** Flags duplicate primary keys or IDs.
* **Numeric strings (`A006`):** Identifies text columns containing exclusively numeric digits for conversion.
* **Statistical outliers (`A007`):** Highlights extreme values deviating by more than 3 standard deviations ($3\sigma$).

---

## Performance & Benchmarking
The modular engine is designed to run efficiently on small laptops and server environments alike. Below are performance results on mock vector layers:

| Scale (Features) | Execution Time (Seconds) | Throughput (Features/Sec) |
|------------------|--------------------------|---------------------------|
| 1,000            | 0.0089s                  | 112,810 features/sec      |
| 10,000           | 0.0582s                  | 171,745 features/sec      |
| 100,000          | 0.5222s                  | 191,510 features/sec      |
| 500,000          | 2.4918s                  | 200,658 features/sec      |

*Tested on standard development environment. Execution time includes parsing geometries, attribute tables, and evaluating 14 validation rules.*

---

## User Workflow
Load Layers → Open GeoQA → Select Layers → Run Validation → Review Issues → Export Report

Simple and linear.

## Future Roadmap
* **Version 1.2:** Topology validation (gaps, overlaps), Batch validation command line, Better reports
* **Version 1.3:** Auto-fix suggestions, Project summary, Rule profiles
* **Version 2.0:** Raster validation, Database validation, Quality score improvements
* **Version 3.0:** Domain profiles (Health GIS, Climate, Infrastructure, Urban Planning)
* **Version 4.0:** Auto-fix engine, Plugin SDK, Python API

---

## Release Notes

### Version 1.1.0
GeoQA v1.1.0 expands the auditing capability with advanced geometry and statistical validation rules, alongside critical scaling performance upgrades.

**Highlights:**
* **Duplicate Geometries (`G004`):** Fast O(N) coordinate byte-matching check.
* **Sliver Polygons (`G005`):** Area-perimeter compactness threshold check using the scale-invariant Polsby-Popper compactness metric (configurable default: `0.05`).
* **Statistical Outliers (`A007`):** Statistical standard deviation check ($3\sigma$) on numeric columns.
* **Performance Benchmarks:** Optimized execution loops to validate large vectors at a rate of 200,000 features per second (auditing 500k features in 2.5 seconds).
* **Robustness & Code Quality:** Added support for custom rule configurations from `rules.json` and resolved all packaging styling warnings.

### Version 1.0.0
Initial Release. Geometry, CRS, and attribute validation with HTML and CSV reporting, scoring, and QGIS Processing integration.
