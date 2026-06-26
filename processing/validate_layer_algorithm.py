# -*- coding: utf-8 -*-
import os
from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterEnum,
    QgsProcessing,
)
from ..core.engine import ValidationEngine
from ..reporting.html import generate_html_report
from ..reporting.csv import generate_csv_report


class ValidateLayerAlgorithm(QgsProcessingAlgorithm):
    """QGIS Processing Algorithm to perform data quality audits on a vector layer using profiles."""

    INPUT_LAYER = "INPUT_LAYER"
    PROFILE = "PROFILE"
    OUTPUT_REPORT_HTML = "OUTPUT_REPORT_HTML"
    OUTPUT_REPORT_CSV = "OUTPUT_REPORT_CSV"

    PROFILE_OPTIONS = [
        "General",
        "Geometry Only",
        "Attribute Only",
        "Database Compliance",
    ]

    def initAlgorithm(self, config=None):
        """Defines parameters for vector inputs, profile selections, and report exports."""
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_LAYER,
                "Vector layer to audit",
                types=[QgsProcessing.TypeVectorAnyGeometry],
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                self.PROFILE,
                "Validation Profile",
                options=self.PROFILE_OPTIONS,
                defaultValue=0,
            )
        )

        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT_REPORT_HTML,
                "Audit Report (HTML)",
                fileFilter="HTML Files (*.html)",
                optional=True,
            )
        )

        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT_REPORT_CSV,
                "Audit Report (CSV)",
                fileFilter="CSV Files (*.csv)",
                optional=True,
            )
        )

    def name(self) -> str:
        return "validate_layer"

    def displayName(self) -> str:
        return "Validate GIS Layer Quality"

    def group(self) -> str:
        return "Quality Assurance"

    def groupId(self) -> str:
        return "qa"

    def shortHelpString(self) -> str:
        return (
            "Audits a GIS vector layer for spatial and attribute quality issues.\n\n"
            "Checks performed are based on the selected Validation Profile:\n"
            "- General: Runs all geometry, CRS, and attribute checks.\n"
            "- Geometry Only: Audits geometry validity, emptiness, and multipart structures.\n"
            "- Attribute Only: Audits nulls, duplicate IDs, reserved names, "
            "shapefile limits, and string optimizations.\n"
            "- Database Compliance: Checks for missing projection, duplicate IDs, and reserved SQL words.\n\n"
            "Generates HTML Dashboard and tabular CSV quality assurance reports."
        )

    def createInstance(self):
        return ValidateLayerAlgorithm()

    def processAlgorithm(self, parameters, context, feedback):
        """Executes the validation with the chosen profile and writes reports."""
        source = self.parameterAsSource(parameters, self.INPUT_LAYER, context)
        if not source:
            raise RuntimeError("Invalid input vector layer provided.")

        # Materialise to a QgsVectorLayer for engine compatibility
        layer = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER, context)
        if layer is None:
            # Fallback: convert source to a temp layer via processing context
            raise RuntimeError(
                "Could not resolve input to a vector layer. Ensure the layer is loaded in QGIS."
            )

        profile_idx = self.parameterAsEnum(parameters, self.PROFILE, context)
        profile_name = self.PROFILE_OPTIONS[profile_idx]

        feedback.pushInfo(
            f"Starting GeoQA audit on layer: {layer.name()} using profile: {profile_name}"
        )

        # Instantiate engine with the chosen profile
        engine = ValidationEngine(profile_name=profile_name)
        project_summary = engine.validate_project([layer], task=feedback)

        score = project_summary.calculate_score()
        grade = project_summary.get_grade()

        feedback.pushInfo(
            f"Audit completed. Quality Score: {score}/100, Grade: {grade}."
        )
        feedback.pushInfo(
            f"Found {project_summary.total_errors} errors and {project_summary.total_warnings} warnings."
        )

        # Write HTML report
        html_dest = self.parameterAsFileOutput(
            parameters, self.OUTPUT_REPORT_HTML, context
        )
        if html_dest:
            feedback.pushInfo(f"Generating HTML report: {html_dest}")
            html_content = generate_html_report(project_summary)
            html_dir = os.path.dirname(html_dest)
            if html_dir and not os.path.exists(html_dir):
                os.makedirs(html_dir, exist_ok=True)
            with open(html_dest, "w", encoding="utf-8") as f:
                f.write(html_content)

        # Write CSV report
        csv_dest = self.parameterAsFileOutput(
            parameters, self.OUTPUT_REPORT_CSV, context
        )
        if csv_dest:
            feedback.pushInfo(f"Generating CSV report: {csv_dest}")
            csv_content = generate_csv_report(project_summary)
            # Create directory if it doesn't exist
            csv_dir = os.path.dirname(csv_dest)
            if csv_dir and not os.path.exists(csv_dir):
                os.makedirs(csv_dir, exist_ok=True)
            with open(csv_dest, "w", encoding="utf-8") as f:
                f.write(csv_content)

        outputs = {}
        if html_dest:
            outputs[self.OUTPUT_REPORT_HTML] = html_dest
        if csv_dest:
            outputs[self.OUTPUT_REPORT_CSV] = csv_dest

        return outputs
