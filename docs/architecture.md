# GeoQA Framework Architecture

GeoQA is designed as a decoupled, extensible **GIS Quality Assurance Framework** rather than a standard, monolithic QGIS plugin. This documentation outlines the system design, the component interactions, and the data flow.

## 1. Architectural Philosophy

The core philosophy of GeoQA is **decoupling**. The framework is divided into three distinct layers:

1. **GeoQA Core (Pure Python)**: Manages data structures, loads rules dynamically, executes rules, and computes metrics like Quality Scores and Audit Grades. This layer does not import QGIS GUI modules and can run completely standalone (e.g. in command-line environments or web services).
2. **Adapters**: Integration points that wrap the Core. Currently, the primary adapter is the **QGIS Adapter**, which translates QGIS-specific layer structures and manages the QGIS Processing Provider and PyQt dialogs.
3. **Reporting Engine**: Translates validation results into high-quality human-readable deliverables (HTML dashboards, CSV spreadsheets).

```
+-----------------------------------------------------------+
|                      QGIS ADAPTER                         |
|   - Processing Toolbox   - QAction menus   - PyQt GUI     |
+-----------------------------+-----------------------------+
                              |
                              v (Passes layer data)
+-----------------------------------------------------------+
|                       GEOQA CORE                          |
|                                                           |
|    +------------------+             +-----------------+   |
|    |  Rule Loader     |             |  Rule Engine    |   |
|    |  (Auto-discovers)|             |  (Executes rules|   |
|    +--------+---------+             |   from config)  |   |
|             |                       +--------+--------+   |
|             v                                |            |
|    [Rule Library (G001-A006)]                v            |
|    (Single-rule file classes)       [Aggregated Results]  |
+----------------------------------------------+------------+
                                               |
                                               v
+-----------------------------------------------------------+
|                     REPORT ENGINE                         |
|   - HTML Dashboard (KPIs, Grade)  - Tabular CSV Exports   |
+-----------------------------------------------------------+
```

---

## 2. Component Directory Structure

- `core/`: Python validation framework.
  - `models.py`: Declares structures (`Severity`, `IssueCategory`, `ValidationIssue`, `LayerSummary`, `ProjectSummary`).
  - `engine.py`: Runs evaluations on active layers.
  - `rules/`: Modular check files.
    - `base.py`: The `Rule` abstract base class defining parameters and requirements.
    - `loader.py`: Auto-discovers and returns subclasses of `Rule` from folders.
- `processing/`: Integrates GeoQA rules inside QGIS Processing Toolbox.
- `reporting/`: Renders validation results.
- `ui/`: PyQt interface panels.

---

## 3. Dynamic Rule Loading & Discovery

Instead of hardcoding checks inside large validator classes, each check resides in its own class inheriting from `Rule` (e.g., `G001_InvalidGeometry`). 

At runtime:
1. `RuleLoader` scans the `core/rules/` directory recursively.
2. It discovers all Python modules and imports them.
3. It identifies all classes subclassing `Rule` (excluding the base class itself) and instantiates them.
4. The engine checks `rules.json` to filter disabled rules and override default severities.
5. Enabled rules are executed against the input GIS layer.

This makes adding a rule as simple as dropping a single Python file into the appropriate subdirectory.
