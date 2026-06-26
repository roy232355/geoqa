# -*- coding: utf-8 -*-
import os
import logging
import tempfile


class GeoQALogger:
    """Decoupled logging coordinator writing to a physical log file and echoing to QGIS Log Messages Panel."""

    _logger_instance = None

    @classmethod
    def get_logger(cls):
        """Initializes and returns the singleton logger instance."""
        if cls._logger_instance is None:
            cls._logger_instance = cls()
        return cls._logger_instance

    def __init__(self):
        self.log_file = os.path.join(tempfile.gettempdir(), "GeoQA.log")

        # Configure logging file handler
        self.logger = logging.getLogger("GeoQA")
        self.logger.setLevel(logging.INFO)
        self.logger.handlers.clear()

        try:
            handler = logging.FileHandler(self.log_file, mode="a", encoding="utf-8")
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        except Exception:
            # Fallback if writing fails
            pass

        # Try to resolve QGIS native message logging reference
        self.qgis_available = False
        try:
            from qgis.core import QgsMessageLog

            self.qgs_message_log = QgsMessageLog
            self.qgis_available = True
        except ImportError:
            self.qgs_message_log = None

    def set_verbose(self, enabled: bool):
        """Toggles logger level between DEBUG and INFO."""
        self.logger.setLevel(logging.DEBUG if enabled else logging.INFO)

    def info(self, msg: str):
        self.logger.info(msg)
        self._qgis_log(msg, 0)  # 0 is Info level in QGIS 3

    def warning(self, msg: str):
        self.logger.warning(msg)
        self._qgis_log(msg, 1)  # 1 is Warning level in QGIS 3

    def error(self, msg: str):
        self.logger.error(msg)
        self._qgis_log(msg, 2)  # 2 is Critical level in QGIS 3

    def exception(self, msg: str):
        self.logger.exception(msg)
        self._qgis_log(f"{msg} - Stack trace written to GeoQA.log file.", 2)

    def _qgis_log(self, msg: str, qgis_level: int):
        """Writes messages directly to QGIS native message log panel when running inside QGIS."""
        if self.qgis_available and self.qgs_message_log:
            try:
                # Log to "GeoQA" tab in QGIS Log Messages panel
                self.qgs_message_log.logMessage(msg, "GeoQA", qgis_level)
            except Exception:
                pass


# Convenience functions
def log_info(msg: str):
    GeoQALogger.get_logger().info(msg)


def log_warning(msg: str):
    GeoQALogger.get_logger().warning(msg)


def log_error(msg: str):
    GeoQALogger.get_logger().error(msg)


def log_exception(msg: str):
    GeoQALogger.get_logger().exception(msg)
