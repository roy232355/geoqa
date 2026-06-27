# -*- coding: utf-8 -*-
import sys
import os
import time

# Setup python path
current_dir = os.path.dirname(os.path.abspath(__file__))
plugin_root = os.path.dirname(current_dir)
if plugin_root not in sys.path:
    sys.path.insert(0, plugin_root)

from core.engine import ValidationEngine  # noqa: E402
from core.models import Severity  # noqa: E402
from tests.mocks import MockVectorLayer, MockFeature, MockGeometry, MockCRS, MockField  # noqa: E402


def run_stress_test(feature_count=10000):
    print("=" * 60)
    print("GeoQA Performance Stress Test Benchmarking")
    print(f"Target Feature Count: {feature_count:,} features")
    print("-" * 60)

    # 1. Setup fields
    fields = [
        MockField("id", "int"),
        MockField("name", "string"),
        MockField("null_col", "string"),
        MockField("str_num", "string"),
        MockField("select", "string"),  # Reserved word check
    ]

    # 2. Build geometries
    valid_geom = MockGeometry(is_valid=True)
    invalid_geom = MockGeometry(is_valid=False)
    empty_geom = MockGeometry(is_null=True, is_empty=True)
    multipart_geom = MockGeometry(is_multipart=True)

    features = []
    print("Generating simulated dataset...")

    for i in range(1, feature_count + 1):
        # Inject geometry defects (1% invalid, 0.5% empty, 2% multipart)
        if i % 100 == 0:
            geom = invalid_geom
        elif i % 200 == 0:
            geom = empty_geom
        elif i % 50 == 0:
            geom = multipart_geom
        else:
            geom = valid_geom

        # Inject attribute defects:
        # - 1% duplicate IDs (using 101 for i % 100 == 0)
        fid_val = 101 if (i % 100 == 0) else i

        # - 5% null values
        null_val = None if (i % 20 == 0) else "Data Value"

        # - 100% numeric text
        str_num_val = str(i)

        features.append(
            MockFeature(
                fid=i,
                geometry=geom,
                attributes_dict={
                    "id": fid_val,
                    "name": f"Feature Name {i}",
                    "null_col": null_val,
                    "str_num": str_num_val,
                    "select": "Reserved usage",
                },
            )
        )

    crs = MockCRS(authid="EPSG:32632", valid=True, geographic=False)
    layer = MockVectorLayer(
        name="Stress Test Layer", features=features, fields=fields, crs=crs
    )
    print("Dataset generation complete.")
    print("-" * 60)

    # 3. Initialize Engine
    engine = ValidationEngine(profile_name="General")

    # 4. Measure validation speed
    print("Running audit engine...")
    start_time = time.perf_counter()
    summary = engine.validate_layer(layer)
    end_time = time.perf_counter()

    elapsed = end_time - start_time
    features_per_second = feature_count / elapsed if elapsed > 0 else 0

    score = summary.calculate_score()

    print("-" * 60)
    print("PERFORMANCE RESULTS:")
    print(f"Total Execution Time : {elapsed:.4f} seconds")
    print(f"Execution Throughput : {features_per_second:.1f} features/sec")
    print("-" * 60)
    print("QUALITY AUDIT RESULTS:")
    print(f"Layer Quality Score  : {score}/100")
    print(f"Total Issues Found   : {len(summary.issues)}")

    critical_count = sum(1 for i in summary.issues if i.severity == Severity.CRITICAL)
    high_count = sum(1 for i in summary.issues if i.severity == Severity.HIGH)
    medium_count = sum(1 for i in summary.issues if i.severity == Severity.MEDIUM)
    low_count = sum(1 for i in summary.issues if i.severity == Severity.LOW)

    print(f" -> Critical Errors  : {critical_count}")
    print(f" -> High Severity    : {high_count}")
    print(f" -> Medium Severity  : {medium_count}")
    print(f" -> Low Severity     : {low_count}")
    print("=" * 60)

    # Verify performance threshold
    if elapsed < 2.0:
        print("PERFORMANCE PASS: Validation finished in under 2.0 seconds.")
        return True
    else:
        print("PERFORMANCE WARNING: Validation exceeded 2.0 seconds.")
        return False


if __name__ == "__main__":
    run_stress_test(feature_count=10000)
