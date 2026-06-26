# -*- coding: utf-8 -*-
from qgis.core import QgsTask
from qgis.PyQt.QtCore import pyqtSignal


class AuditTask(QgsTask):
    """QgsTask wrapper to perform GIS Quality Audits on a background thread without freezing the QGIS GUI."""

    completed = pyqtSignal(
        object
    )  # Emitted when validation completes successfully with a ProjectSummary
    failed = pyqtSignal(object)  # Emitted when validation fails, passing the Exception

    def __init__(self, engine, layers):
        super().__init__("GeoQA Quality Audit", QgsTask.CanCancel)
        self.engine = engine
        self.layers = layers
        self.summary = None
        self.exception = None

    def run(self) -> bool:
        """Executes the validation engine in the background thread."""
        try:
            # Execute validation project, passing this task instance to track progress and cancellation
            self.summary = self.engine.validate_project(self.layers, task=self)
            return True
        except Exception as e:
            self.exception = e
            return False

    def finished(self, result: bool):
        """Called automatically in the main QGIS thread when run() completes."""
        if result and self.summary:
            self.completed.emit(self.summary)
        else:
            self.failed.emit(
                self.exception or Exception("Unknown background thread failure.")
            )
