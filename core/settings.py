# -*- coding: utf-8 -*-
"""Manages application settings, wrapping QgsSettings when inside QGIS or falling back to a local JSON cache."""

import json
import os
import tempfile
from .exceptions import ConfigurationException


def tempfile_dir_safe() -> str:
    """Helper to retrieve a secure, writable temporary directory across OS platforms."""
    return tempfile.gettempdir()


class SettingsManager:
    """Manages application settings, wrapping QgsSettings when inside QGIS or falling back to a local JSON cache."""

    def __init__(self, fallback_path: str = None):
        self.fallback_path = fallback_path or os.path.join(
            tempfile_dir_safe(), "geoqa_settings.json"
        )
        self.cache = {}
        self.qgis_available = False

        # Test if QgsSettings is available
        try:
            from qgis.core import QgsSettings

            self.qgs_settings = QgsSettings()
            self.qgis_available = True
        except ImportError:
            self.qgs_settings = None
            self.load_fallback_settings()

    def load_fallback_settings(self):
        """Loads settings from fallback JSON file when QGIS is not available."""
        if os.path.exists(self.fallback_path):
            try:
                with open(self.fallback_path, "r", encoding="utf-8") as f:
                    self.cache = json.load(f)
            except Exception:
                self.cache = {}

    def save_fallback_settings(self):
        """Persists settings cache to fallback JSON file."""
        try:
            dir_path = os.path.dirname(self.fallback_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
            with open(self.fallback_path, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            raise ConfigurationException(f"Failed to save offline settings: {str(e)}")

    def get_setting(self, key: str, default_value=None):
        """Retrieves a setting by key, converting string representations of booleans if needed."""
        if self.qgis_available:
            val = self.qgs_settings.value(key, default_value)
            if val is not None:
                # Normalize types returned by QgsSettings
                if isinstance(val, str):
                    if val.lower() == "true":
                        return True
                    if val.lower() == "false":
                        return False
                return val
            return default_value
        else:
            return self.cache.get(key, default_value)

    def set_setting(self, key: str, value):
        """Saves a setting value."""
        if self.qgis_available:
            self.qgs_settings.setValue(key, value)
        else:
            self.cache[key] = value
            self.save_fallback_settings()

    def remove_setting(self, key: str):
        """Removes a setting by key."""
        if self.qgis_available:
            self.qgs_settings.remove(key)
        else:
            if key in self.cache:
                del self.cache[key]
                self.save_fallback_settings()
