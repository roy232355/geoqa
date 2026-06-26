# -*- coding: utf-8 -*-
"""GeoQA QGIS Plugin entry point — manages plugin lifecycle (init, unload, run)."""
import os
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsApplication

from .provider import GeoQAProvider
from .ui.report_dialog import ReportDialog


class GeoQAPlugin:
    """Plugin Lifecycle Manager for QGIS integration."""

    def __init__(self, iface):
        self.iface = iface
        self.provider = None
        self.action = None
        self.dialog = None

    def initGui(self):
        """Initializes GUI menu items, toolbar icons, and Processing Provider."""
        # 1. Register Processing Provider
        self.provider = GeoQAProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

        # 2. Add Toolbar Button & Menu Action
        from .core.resources import ResourceManager

        icon_path = ResourceManager.get_icon_path()
        icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()

        self.action = QAction(icon, "GeoQA Data Auditor", self.iface.mainWindow())
        self.action.triggered.connect(self.run)

        # Add to Vector Toolbar and Vector Menu
        self.iface.addVectorToolBarIcon(self.action)
        self.iface.addPluginToVectorMenu("GeoQA", self.action)

    def unload(self):
        """Removes menu items, toolbar icons, and unregisters Processing Provider."""
        # 1. Remove GUI items
        if self.action:
            self.iface.removePluginVectorMenu("GeoQA", self.action)
            self.iface.removeVectorToolBarIcon(self.action)
            self.action.deleteLater()
            self.action = None

        # 2. Close and delete dialog to prevent memory leakages
        if self.dialog:
            try:
                self.dialog.close()
                self.dialog.deleteLater()
            except Exception:
                pass
            self.dialog = None

        # 3. Unregister Processing Provider
        if self.provider:
            QgsApplication.processingRegistry().removeProvider(self.provider)
            self.provider = None

    def run(self):
        """Triggered when the user clicks the plugin button or menu item."""
        if not self.dialog:
            self.dialog = ReportDialog(self.iface)
        else:
            try:
                self.dialog.populate_layers()
            except Exception:
                pass
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()
