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
