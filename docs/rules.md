# GeoQA Quality Assurance Rules Catalog

This document lists all built-in validation rules supported by the GeoQA framework, categorized by domain.

---

## 📐 Geometry Rules (`G0xx`)

### `G001`: Invalid Geometry
* **Default Severity**: `Critical`
* **Description**: Checks for self-intersecting polygons, slivers, open loops, or otherwise invalid geometry records as defined by OGC standards.
* **Recommendation**: Run the QGIS 'Fix Geometries' processing tool or manually edit the affected features using the Node Tool.

### `G002`: Empty Geometry
* **Default Severity**: `Critical`
* **Description**: Checks for features with no coordinate values (empty shape records).
* **Recommendation**: Re-digitize the shape components or delete the empty rows if they do not contain valid tabular information.

### `G003`: Multipart Geometry
* **Default Severity**: `Medium`
* **Description**: Flags features containing multiple disjoint spatial parts (e.g. multi-polygons).
* **Recommendation**: If your downstream GIS analysis requires singlepart features, execute the QGIS 'Multipart to singleparts' tool.

### `G004`: Duplicate Geometries
* **Default Severity**: `High`
* **Description**: Flags features containing identical geometry coordinate footprints.
* **Logic:** Computes the Well-Known Binary (WKB) bytes representation of each feature geometry and flags exact matching byte sequences in a single-pass hash map check.
* **Limitations/False Positives:** Points, lines, or polygons that represent different spatial objects but are stacked exactly on top of each other will be flagged.
* **Recommendation**: Remove duplicate features or use the QGIS 'Delete duplicate geometries' processing tool.

### `G005`: Sliver Polygons
* **Default Severity**: `Medium`
* **Description**: Flags extremely narrow or thin polygons typical of clipping boundary mismatches.
* **Logic:** Computes the Polsby-Popper compactness metric:
  $$PP = \frac{4\pi \times \text{Area}}{\text{Perimeter}^2}$$
  Flags any polygon with $PP$ below the configured threshold (default: `0.05`).
* **Limitations/False Positives:** Legitimate elongated features such as rivers, roads, medians, or thin buffer zones will be flagged. Inspect visually before deleting.
* **Recommendation**: Verify if this polygon is an accidental sliver artifact from clipping/alignment. Clean using the QGIS 'Snap geometries to layer' tool or perform manual vertex editing.

---

## 🌐 Coordinate Reference System Rules (`C0xx`)

### `C001`: Missing CRS
* **Default Severity**: `Critical`
* **Description**: Flags layers that have an undefined or invalid Coordinate Reference System.
* **Recommendation**: Assign the correct coordinate projection using the QGIS 'Assign projection' tool before carrying out any spatial analysis.

### `C002`: Geographic CRS Warning
* **Default Severity**: `Low`
* **Description**: Flags layers projected in geographic degrees (e.g. EPSG:4326 WGS84) instead of projected linear units (meters, feet).
* **Recommendation**: Area, distance, and buffer operations calculated in degrees will yield inaccurate/unexpected planar measurements. Reproject the layer to a projected coordinate reference system (such as UTM).

---

## 📊 Tabular Attribute Rules (`A0xx`)

### `A001`: Long Field Names (Shapefile Limit)
* **Default Severity**: `Low`
* **Description**: Checks if field column names exceed 10 characters in length.
* **Recommendation**: Shapefiles truncate field names to a maximum of 10 characters. If exporting to Shapefiles, rename fields to avoid name overlap or structure corruption.

### `A002`: Database Reserved Keywords
* **Default Severity**: `Low`
* **Description**: Flags fields that match database keywords (e.g. `SELECT`, `WHERE`, `TABLE`, `GEOMETRY`, `OID`).
* **Recommendation**: Rename columns to avoid syntax conflicts when exporting to SQL databases like PostGIS or SQLite/SpatiaLite.

### `A003`: NULL Attribute Values
* **Default Severity**: `Medium`
* **Description**: Identifies field columns containing NULL (missing) values.
* **Recommendation**: Populate missing fields with default values, or verify if NULL values are expected for this field.

### `A004`: Empty String Attributes
* **Default Severity**: `Medium`
* **Description**: Detects string fields containing only whitespace characters or completely empty strings.
* **Recommendation**: Clean the dataset to convert empty spaces to proper NULL markers or standardized default values.

### `A005`: Duplicate Identifiers
* **Default Severity**: `High`
* **Description**: Identifies duplicate values within identifier fields (e.g. `id`, `fid`, `uuid`, `objectid`).
* **Recommendation**: Primary keys must contain unique values. Regenerate unique IDs using the QGIS Field Calculator (`$id` or `uuid()`).

### `A006`: Numeric String Optimization
* **Default Severity**: `Low`
* **Description**: Checks if string-type fields contain exclusively numeric data.
* **Recommendation**: Convert the field data type to Integer or Double to optimize storage size and enable mathematical operations.

### `A007`: Statistical Outliers
* **Default Severity**: `Low`
* **Description**: Flags values in numeric columns that deviate significantly from the column mean.
* **Logic:** Calculates the mean ($\mu$) and standard deviation ($\sigma$) for each numeric field. Any feature with a value $x$ satisfying $|x - \mu| > 3\sigma$ is flagged as an outlier.
* **Limitations/False Positives:** Highly skewed datasets (e.g. populations, areas, income) naturally have valid outliers at the high end. The rule is only executed on fields with 10 or more records.
* **Recommendation**: Value deviates significantly from the field average (greater than 3 standard deviations). Verify if this is a data entry typo.
