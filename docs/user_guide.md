# GeoQA Quality Auditor User Guide

Welcome to GeoQA! This guide helps you install the plugin, run audits, interpret the scoring system, and generate professional reports.

---

## 1. Installation

1. Copy the `GeoQA` directory into your active QGIS user profile's plugin folder:
   - **Windows**: `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`
   - **Linux/macOS**: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
2. Open QGIS.
3. Select **Plugins > Manage and Install Plugins**.
4. Check the box next to **GeoQA** to enable the plugin.

---

## 2. Using the User Interface Dialog

Open the UI panel by clicking the GeoQA icon in the **Vector Toolbar** or selecting **Vector > GeoQA > GeoQA Auditor**.

```
+------------------------------------------+
| GeoQA Auditor                            |
|                                          |
| [ Validation ]  [ About ]                |
|                                          |
| Audit Profile: [ General             v ] |
|                                          |
| Target Layers:                           |
| [x] Administrative_Boundaries            |
| [x] Health_Clinics_Point                 |
| [ ] Regional_Roads                       |
|                                          |
| [ Select All ] [ Clear ] [ Refresh ]     |
|                                          |
| +--------------------------------------+ |
| | Ready to audit layer(s).             | |
| +--------------------------------------+ |
|                                          |
| [ Start Audit ]                          |
+------------------------------------------+
```

1. **Select Audit Profile**: Choose a preset profile depending on your dataset focus (e.g. Geometry Only to bypass attribute scans).
2. **Select Layers**: Check the layers in the project you want to audit.
3. **Start Audit**: Click **Start Audit**. 
   - The engine validates all checked layers, computes statistics, and automatically launches the **HTML Audit Dashboard** in your system default web browser.
4. **Save Reports**: Once the browser opens, you can print the HTML report as a PDF, or look for the CSV outputs saved in your plugin's default directory.

---

## 3. Running via Processing Toolbox

For automation, model builders, or batch processes:
1. Open the QGIS **Processing Toolbox** panel.
2. Expand **GeoQA GIS Auditor** and double-click **Validate GIS Layer Quality**.
3. Choose the input layer, optionally set file paths to write HTML/CSV reports directly, and click **Run**.

---

## 4. Understanding Scores & Grades

GeoQA computes a Quality Score (0 to 100) and maps it to a letter grade:

* **Grade A (Score >= 90)**: **Excellent Quality**. No critical issues, and few minor warnings. Safe for GIS analysis.
* **Grade B (Score >= 80)**: **Good Quality**. Minor attribute cleanups or multipart warnings. Double-check before large calculations.
* **Grade C (Score >= 70)**: **Needs Review**. Several medium-severity attribute issues or warnings exist.
* **Grade D (Score >= 50)**: **Poor Quality**. Multiple high-severity issues (like duplicate IDs) or critical issues on a portion of features.
* **Grade F (Score < 50)**: **Unusable**. Critical errors (invalid geometry, missing projection) affect major parts of the dataset.

Always aim for a **Grade A** before running buffer, overlay, or network analyses.
