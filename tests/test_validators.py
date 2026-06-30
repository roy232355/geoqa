# -*- coding: utf-8 -*-
import unittest
from core.models import Severity, IssueCategory, LayerSummary, ProjectSummary
from core.rules.loader import RuleLoader
from core.rules.geometry.g001_invalid_geometry import G001_InvalidGeometry
from core.rules.geometry.g002_empty_geometry import G002_EmptyGeometry
from core.rules.geometry.g003_multipart_geometry import G003_MultipartGeometry
from core.rules.crs.c001_missing_crs import C001_MissingCRS
from core.rules.crs.c002_geographic_crs import C002_GeographicCRS
from core.rules.attributes.a001_long_field_names import A001_LongFieldNames
from core.rules.attributes.a002_reserved_keywords import A002_ReservedKeywords
from core.rules.attributes.a003_null_values import A003_NullValues
from core.rules.attributes.a004_empty_strings import A004_EmptyStrings
from core.rules.attributes.a005_duplicate_identifiers import A005_DuplicateIdentifiers
from core.rules.attributes.a006_numeric_strings import A006_NumericStrings
from tests.mocks import MockVectorLayer, MockFeature, MockGeometry, MockCRS, MockField


class TestRuleLoader(unittest.TestCase):
    def test_dynamic_discovery(self):
        rules = RuleLoader.discover_rules()
        rule_ids = {r.rule_id for r in rules}
        expected_ids = {
            "G001",
            "G002",
            "G003",
            "C001",
            "C002",
            "A001",
            "A002",
            "A003",
            "A004",
            "A005",
            "A006",
        }
        self.assertTrue(
            expected_ids.issubset(rule_ids),
            f"Missing discovered rules: {expected_ids - rule_ids}",
        )

    def test_profile_loading(self):
        geom_rules = RuleLoader.load_profile_rules("Geometry Only")
        geom_ids = {r.rule_id for r in geom_rules}
        self.assertEqual(geom_ids, {"G001", "G002", "G003", "G004", "G005"})

        attr_rules = RuleLoader.load_profile_rules("Attribute Only")
        attr_ids = {r.rule_id for r in attr_rules}
        self.assertEqual(attr_ids, {"A001", "A002", "A003", "A004", "A005", "A006", "A007"})


class TestGeometryRules(unittest.TestCase):
    def test_g001_invalid_geometry(self):
        rule = G001_InvalidGeometry()

        valid_geom = MockGeometry(is_valid=True)
        invalid_geom = MockGeometry(is_valid=False)

        features = [
            MockFeature(fid=1, geometry=valid_geom, attributes_dict={}),
            MockFeature(fid=2, geometry=invalid_geom, attributes_dict={}),
        ]
        layer = MockVectorLayer(features=features)

        issues = rule.evaluate(layer)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].rule_id, "G001")
        self.assertEqual(issues[0].affected_features, [2])

    def test_g002_empty_geometry(self):
        rule = G002_EmptyGeometry()

        valid_geom = MockGeometry(is_null=False, is_empty=False)
        empty_geom = MockGeometry(is_null=True, is_empty=True)

        features = [
            MockFeature(fid=1, geometry=valid_geom, attributes_dict={}),
            MockFeature(fid=2, geometry=empty_geom, attributes_dict={}),
        ]
        layer = MockVectorLayer(features=features)

        issues = rule.evaluate(layer)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].rule_id, "G002")
        self.assertEqual(issues[0].affected_features, [2])

    def test_g003_multipart_geometry(self):
        rule = G003_MultipartGeometry()

        single_geom = MockGeometry(is_multipart=False)
        multi_geom = MockGeometry(is_multipart=True)

        features = [
            MockFeature(fid=1, geometry=single_geom, attributes_dict={}),
            MockFeature(fid=2, geometry=multi_geom, attributes_dict={}),
        ]
        layer = MockVectorLayer(features=features)

        issues = rule.evaluate(layer)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].rule_id, "G003")
        self.assertEqual(issues[0].affected_features, [2])


class TestCRSRules(unittest.TestCase):
    def test_c001_missing_crs(self):
        rule = C001_MissingCRS()
        layer = MockVectorLayer(crs=MockCRS(valid=False))

        issues = rule.evaluate(layer)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].rule_id, "C001")

    def test_c002_geographic_crs(self):
        rule = C002_GeographicCRS()
        layer = MockVectorLayer(
            crs=MockCRS(authid="EPSG:4326", valid=True, geographic=True)
        )

        issues = rule.evaluate(layer)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].rule_id, "C002")


class TestAttributeRules(unittest.TestCase):
    def test_a003_null_values(self):
        rule = A003_NullValues()
        fields = [MockField("id"), MockField("name")]
        features = [
            MockFeature(
                fid=1,
                geometry=MockGeometry(),
                attributes_dict={"id": 1, "name": "Alice"},
            ),
            MockFeature(
                fid=2, geometry=MockGeometry(), attributes_dict={"id": 2, "name": None}
            ),
        ]
        layer = MockVectorLayer(fields=fields, features=features)

        issues = rule.evaluate(layer)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].rule_id, "A003")
        self.assertEqual(issues[0].field_name, "name")
        self.assertEqual(issues[0].affected_features, [2])

    def test_a005_duplicate_identifiers(self):
        rule = A005_DuplicateIdentifiers()
        fields = [MockField("id"), MockField("name")]
        features = [
            MockFeature(
                fid=1,
                geometry=MockGeometry(),
                attributes_dict={"id": 10, "name": "Alice"},
            ),
            MockFeature(
                fid=2,
                geometry=MockGeometry(),
                attributes_dict={"id": 10, "name": "Bob"},
            ),
        ]
        layer = MockVectorLayer(fields=fields, features=features)

        issues = rule.evaluate(layer)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].rule_id, "A005")
        self.assertEqual(issues[0].affected_features, [2])

    def test_a001_long_field_names(self):
        rule = A001_LongFieldNames()
        fields = [MockField("short"), MockField("extremely_long_fieldname")]
        layer = MockVectorLayer(fields=fields, features=[])
        issues = rule.evaluate(layer)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].rule_id, "A001")
        self.assertIn("extremely_long_fieldname", issues[0].message)

    def test_a002_reserved_keywords(self):
        rule = A002_ReservedKeywords()
        fields = [MockField("valid"), MockField("select")]
        layer = MockVectorLayer(fields=fields, features=[])
        issues = rule.evaluate(layer)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].rule_id, "A002")
        self.assertIn("select", issues[0].message)

    def test_a004_empty_strings(self):
        rule = A004_EmptyStrings()
        fields = [MockField("id"), MockField("name")]
        features = [
            MockFeature(
                fid=1,
                geometry=MockGeometry(),
                attributes_dict={"id": 1, "name": "Alice"},
            ),
            MockFeature(
                fid=2, geometry=MockGeometry(), attributes_dict={"id": 2, "name": "   "}
            ),
            MockFeature(
                fid=3, geometry=MockGeometry(), attributes_dict={"id": 3, "name": ""}
            ),
        ]
        layer = MockVectorLayer(fields=fields, features=features)
        issues = rule.evaluate(layer)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].rule_id, "A004")
        self.assertEqual(issues[0].affected_features, [2, 3])

    def test_a006_numeric_strings(self):
        rule = A006_NumericStrings()
        fields = [
            MockField("id", type_name="integer"),
            MockField("postal_code", type_name="string"),
        ]
        features = [
            MockFeature(
                fid=1,
                geometry=MockGeometry(),
                attributes_dict={"id": 1, "postal_code": "12345"},
            ),
            MockFeature(
                fid=2,
                geometry=MockGeometry(),
                attributes_dict={"id": 2, "postal_code": "67890"},
            ),
        ]
        layer = MockVectorLayer(fields=fields, features=features)
        issues = rule.evaluate(layer)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].rule_id, "A006")
        self.assertEqual(issues[0].field_name, "postal_code")


class TestScoringModel(unittest.TestCase):
    def test_layer_scoring_and_grading(self):
        # 1. Base Summary of 100 features
        summary = LayerSummary(
            layer_name="Roads",
            geometry_type="Line",
            crs_authid="EPSG:32632",
            feature_count=100,
        )
        self.assertEqual(summary.calculate_score(), 100)

        # 2. Add Critical check failure affecting 10 features
        # Penalty = CRITICAL (30 points) * (10 / 100) = 3 points
        from core.models import ValidationIssue

        summary.add_issue(
            ValidationIssue(
                rule_id="G001",
                category=IssueCategory.GEOMETRY,
                severity=Severity.CRITICAL,
                message="Invalid Geometry",
                recommendation="Fix",
                affected_features=[i for i in range(10)],
            )
        )

        # Add High check failure affecting 20 features
        # Penalty = HIGH (15 points) * (20 / 100) = 3 points
        summary.add_issue(
            ValidationIssue(
                rule_id="A005",
                category=IssueCategory.ATTRIBUTE,
                severity=Severity.HIGH,
                message="Duplicate IDs",
                recommendation="Fix",
                affected_features=[i for i in range(20)],
            )
        )

        # Expected score: 100 - 3 - 3 = 94
        self.assertEqual(summary.calculate_score(), 94)

        # Add Layer-level missing CRS (Critical - 30 points)
        summary.add_issue(
            ValidationIssue(
                rule_id="C001",
                category=IssueCategory.CRS,
                severity=Severity.CRITICAL,
                message="Missing CRS",
                recommendation="Fix",
                affected_features=[],  # Layer level
            )
        )

        # Expected score: 94 - 30 = 64
        self.assertEqual(summary.calculate_score(), 64)

    def test_project_grading(self):
        project = ProjectSummary()

        layer1 = LayerSummary("A", "Point", "EPSG:32632", 10)
        layer2 = LayerSummary("B", "Point", "EPSG:32632", 10)

        project.add_layer_summary(layer1)  # Score 100
        project.add_layer_summary(layer2)  # Score 100

        self.assertEqual(project.calculate_score(), 100)
        self.assertEqual(project.get_grade(), "A")

        # Add project level mixed CRS warning (High penalty - 15 points)
        from core.models import ValidationIssue

        project.add_project_issue(
            ValidationIssue(
                rule_id="P001",
                category=IssueCategory.CRS,
                severity=Severity.HIGH,
                message="Mixed CRS",
                recommendation="Fix",
            )
        )

        # Expected score: 100 (avg layer) - 15 (project issue) = 85
        self.assertEqual(project.calculate_score(), 85)
        self.assertEqual(project.get_grade(), "B")


class TestSDKManagers(unittest.TestCase):
    def test_event_bus(self):
        from core.events import EventBus

        bus = EventBus()
        events_received = []

        bus.subscribe("test_event", lambda val: events_received.append(val))
        bus.publish("test_event", "hello")

        self.assertEqual(events_received, ["hello"])

    def test_settings_manager_fallback(self):
        from core.settings import SettingsManager
        import tempfile
        import os

        temp_path = os.path.join(tempfile.gettempdir(), "test_geoqa_settings.json")
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass

        settings = SettingsManager(fallback_path=temp_path)
        settings.set_setting("test_key", "test_val")

        self.assertEqual(settings.get_setting("test_key"), "test_val")

        # Load from new instance to check disk persistence
        new_settings = SettingsManager(fallback_path=temp_path)
        self.assertEqual(new_settings.get_setting("test_key"), "test_val")

        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass

    def test_rule_registry(self):
        from core.rules.registry import RuleRegistry
        from core.rules.geometry.g001_invalid_geometry import G001_InvalidGeometry

        registry = RuleRegistry()
        rule = G001_InvalidGeometry()

        registry.register(rule)
        self.assertEqual(registry.get_rule("G001"), rule)
        self.assertEqual(len(registry.get_all_rules()), 1)

        registry.unregister("G001")
        self.assertIsNone(registry.get_rule("G001"))


class TestNewRules(unittest.TestCase):
    """Unit tests for the new validation rules in GeoQA v1.1.0 (G004, G005, A007)."""

    def test_g004_duplicate_geometries(self):
        from core.rules.geometry.g004_duplicate_geometries import G004_DuplicateGeometries
        from tests.mocks import MockVectorLayer, MockFeature, MockGeometry

        feat1 = MockFeature(1, MockGeometry(wkb=b"wkb_a"), {})
        feat2 = MockFeature(2, MockGeometry(wkb=b"wkb_b"), {})
        feat3 = MockFeature(3, MockGeometry(wkb=b"wkb_a"), {})  # Duplicate of 1

        layer = MockVectorLayer("Duplicate Test", geom_type=2, features=[feat1, feat2, feat3])
        rule = G004_DuplicateGeometries()
        issues = rule.evaluate(layer)

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].rule_id, "G004")
        self.assertEqual(issues[0].affected_features, [3])

        layer_no_dups = MockVectorLayer("Clean Test", geom_type=2, features=[feat1, feat2])
        self.assertEqual(len(rule.evaluate(layer_no_dups)), 0)

    def test_g005_sliver_polygons(self):
        from core.rules.geometry.g005_sliver_polygons import G005_SliverPolygons
        from tests.mocks import MockVectorLayer, MockFeature, MockGeometry

        normal_feat = MockFeature(1, MockGeometry(area=100.0, length=40.0), {})
        sliver_feat = MockFeature(2, MockGeometry(area=10.0, length=100.0), {})

        layer = MockVectorLayer("Sliver Test", geom_type=2, features=[normal_feat, sliver_feat])
        rule = G005_SliverPolygons()

        issues = rule.evaluate(layer)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].rule_id, "G005")
        self.assertEqual(issues[0].affected_features, [2])

        rule.load_config({"compactness_threshold": 0.01})
        self.assertEqual(len(rule.evaluate(layer)), 0)

    def test_a007_statistical_outliers(self):
        from core.rules.attributes.a007_statistical_outliers import A007_StatisticalOutliers
        from tests.mocks import MockVectorLayer, MockFeature, MockField

        fields = [MockField("val", "double")]
        features = [MockFeature(i, None, {"val": 10.0 + (i % 3)}) for i in range(1, 11)]
        features.append(MockFeature(11, None, {"val": 1000.0}))

        layer = MockVectorLayer("Outlier Test", geom_type=2, features=features, fields=fields)
        rule = A007_StatisticalOutliers()
        issues = rule.evaluate(layer)

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].rule_id, "A007")
        self.assertEqual(issues[0].affected_features, [11])

        small_layer = MockVectorLayer("Small Test", geom_type=2, features=features[:5], fields=fields)
        self.assertEqual(len(rule.evaluate(small_layer)), 0)


if __name__ == "__main__":
    unittest.main()
