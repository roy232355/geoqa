# GeoQA Sample Datasets

This folder contains sample GIS datasets for testing GeoQA validation rules.

Each subfolder represents a specific data quality scenario. Load any dataset into
QGIS and run GeoQA to see how the plugin identifies and reports issues.

---

## Datasets

| Folder | Expected GeoQA Result | Rules Triggered |
|--------|----------------------|-----------------|
| `valid_dataset/` | Grade A — READY FOR ANALYSIS | None |
| `invalid_geometry/` | Grade F — FAILED VALIDATION | G001, G002 |
| `missing_crs/` | Grade F — FAILED VALIDATION | C001 |
| `duplicate_ids/` | Grade D — REVIEW REQUIRED | A005 |
| `empty_attributes/` | Grade C — REVIEW REQUIRED | A003, A004 |

---

## How to Use

1. Open QGIS and drag any `.gpkg` or `.shp` file from these folders into the canvas.
2. Open GeoQA via **Plugins → GeoQA Quality Auditor**.
3. Select the loaded layer and click **Start Audit**.
4. Review the generated HTML report.

---

## Contributing Sample Data

If you have a dataset that exposes a GeoQA bug or edge case, please open an issue
on GitHub and attach the dataset. We will add it to this folder as a regression test.

https://github.com/roy232355/geoqa/issues
