# -*- coding: utf-8 -*-
import os
import tempfile
import webbrowser

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QPixmap
from qgis.PyQt.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QFileDialog,
    QComboBox,
    QTabWidget,
    QWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QProgressBar,
    QTextEdit,
    QMenu,
    QAction,
    QLineEdit,
    QGridLayout,
)
from qgis.core import QgsProject, QgsMapLayer, QgsApplication

from ..core.settings import SettingsManager
from ..core.resources import ResourceManager
from ..core.diagnostics import GeoQADiagnostics
from ..processing.task import AuditTask


class ReportDialog(QDialog):
    """A professional QGIS PyQt dialog providing asynchronous layer quality validation.

    Handles settings configuration and diagnostic checks.
    """

    def __init__(self, iface, parent=None):
        super().__init__(parent or iface.mainWindow())
        self.iface = iface
        self.last_project_summary = None
        self.active_task = None
        self.temp_files = []  # Keep track of temporary report paths for auto-cleanup

        # Instantiate Core Managers via Dependency Injection
        self.settings = SettingsManager()
        self._table_loading = False

        self.setWindowTitle("GeoQA GIS Quality Auditor")
        self.resize(520, 620)
        self.setMinimumSize(480, 560)

        # Apply style sheets from Resource Manager
        self.setStyleSheet(ResourceManager.get_dialog_stylesheet())

        self.setup_ui()
        self.load_saved_profile()
        self.populate_layers()
        self.populate_rules_table()

    def setup_ui(self):
        """Builds dialog structure, tabs, and widgets."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)

        # Header block
        header_layout = QHBoxLayout()
        title_lbl = QLabel("GeoQA Quality Auditor")
        title_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E3A8A;")
        version_lbl = QLabel("v1.1.0")
        version_lbl.setStyleSheet("font-weight: bold; color: #94A3B8; font-size: 11px;")

        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        header_layout.addWidget(version_lbl)
        main_layout.addLayout(header_layout)

        # Tab layout
        self.tab_widget = QTabWidget()

        self.setup_validation_tab()
        self.tab_widget.addTab(self.tab_validation, "Validation")

        self.setup_settings_tab()
        self.tab_widget.addTab(self.tab_settings, "Rule Settings")

        self.setup_about_tab()
        self.tab_widget.addTab(self.tab_about, "About")

        main_layout.addWidget(self.tab_widget)

        # Footer Actions
        bottom_layout = QHBoxLayout()

        footer_brand_lbl = QLabel("GeoQA v1.1.0")
        footer_brand_lbl.setStyleSheet("font-weight: bold; color: #94A3B8; font-size: 11px;")

        self.open_last_report_btn = QPushButton("Open Last Report")
        self.open_last_report_btn.setVisible(False)
        self.open_last_report_btn.clicked.connect(self.open_last_report)
        self.open_last_report_btn.setStyleSheet("color: #2563EB; font-weight: bold;")

        self.export_btn = QPushButton("Export")
        self.export_btn.setEnabled(False)

        export_menu = QMenu(self)
        export_html_action = QAction("Export HTML", self)
        export_html_action.triggered.connect(self.open_last_report)
        export_csv_action = QAction("Export CSV", self)
        export_csv_action.triggered.connect(self.export_csv)
        export_menu.addAction(export_html_action)
        export_menu.addAction(export_csv_action)
        self.export_btn.setMenu(export_menu)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)

        bottom_layout.addWidget(footer_brand_lbl)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.open_last_report_btn)
        bottom_layout.addWidget(self.export_btn)
        bottom_layout.addWidget(close_btn)
        main_layout.addLayout(bottom_layout)

    def setup_validation_tab(self):
        """Creates the audit validation controls panel."""
        self.tab_validation = QWidget()
        layout = QVBoxLayout(self.tab_validation)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Profile combobox
        profile_layout = QHBoxLayout()
        profile_lbl = QLabel("Audit Profile:")
        profile_lbl.setStyleSheet("font-weight: bold; color: #334155; font-size: 11px;")
        self.profile_combo = QComboBox()
        self.profile_combo.addItems(
            ["General", "Geometry Only", "Attribute Only", "Database Compliance"]
        )
        self.profile_combo.currentIndexChanged.connect(self.save_selected_profile)

        profile_layout.addWidget(profile_lbl)
        profile_layout.addWidget(self.profile_combo, 1)
        layout.addLayout(profile_layout)

        layers_lbl = QLabel("Select vector layers to validate:")
        layers_lbl.setStyleSheet("font-weight: bold; color: #475569; font-size: 11px;")
        layout.addWidget(layers_lbl)

        # Layer list
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        # Helper selectors
        selection_layout = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all)
        select_none_btn = QPushButton("Clear")
        select_none_btn.clicked.connect(self.select_none)
        refresh_btn = QPushButton("Refresh Layers")
        refresh_btn.clicked.connect(self.populate_layers)

        selection_layout.addWidget(select_all_btn)
        selection_layout.addWidget(select_none_btn)
        selection_layout.addStretch()
        selection_layout.addWidget(refresh_btn)
        layout.addLayout(selection_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet(
            "QProgressBar { min-height: 15px; font-size: 10px; }"
        )
        layout.addWidget(self.progress_bar)

        # Status output
        self.status_lbl = QLabel("Ready to analyze GIS data layers.")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setWordWrap(True)
        self.status_lbl.setStyleSheet(
            "background-color: #F1F5F9; border: 1px solid #E2E8F0; "
            "border-radius: 6px; padding: 10px; color: #475569; "
            "font-weight: 500; font-size: 11px; min-height: 50px;"
        )
        layout.addWidget(self.status_lbl)

        # Audit triggers (Run and Cancel buttons)
        btn_box = QHBoxLayout()
        self.run_btn = QPushButton("Start Audit")
        self.run_btn.setObjectName("primaryBtn")
        self.run_btn.clicked.connect(self.run_audit)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.cancel_audit)

        btn_box.addWidget(self.run_btn, 2)
        btn_box.addWidget(self.cancel_btn, 1)
        layout.addLayout(btn_box)

    def setup_settings_tab(self):
        """Creates the settings overrides panel."""
        self.tab_settings = QWidget()
        layout = QVBoxLayout(self.tab_settings)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        info_lbl = QLabel(
            "Customize active rules and their severities. "
            "Changes persist automatically in QGIS user settings."
        )
        info_lbl.setStyleSheet("color: #64748B; font-size: 11px;")
        info_lbl.setWordWrap(True)
        layout.addWidget(info_lbl)

        # Search Bar
        self.rule_search = QLineEdit()
        self.rule_search.setPlaceholderText("Search rule...")
        self.rule_search.textChanged.connect(self.filter_rules)
        layout.addWidget(self.rule_search)

        # Rules config Table
        self.rules_table = QTableWidget()
        self.rules_table.setColumnCount(4)
        self.rules_table.setHorizontalHeaderLabels(
            ["Active", "Code", "Name", "Severity"]
        )

        header = self.rules_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Fixed)

        self.rules_table.setColumnWidth(0, 50)
        self.rules_table.setColumnWidth(1, 60)
        self.rules_table.setColumnWidth(3, 110)

        self.rules_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.rules_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        layout.addWidget(self.rules_table)

        # Reset button — clears all user-persisted rule overrides
        reset_rules_btn = QPushButton("Reset All Rules to Defaults")
        reset_rules_btn.setObjectName("resetBtn")
        reset_rules_btn.setToolTip(
            "Removes all custom severity and enabled/disabled overrides. "
            "Rules will revert to the factory defaults from rules.json."
        )
        reset_rules_btn.clicked.connect(self.reset_rules_to_defaults)
        layout.addWidget(reset_rules_btn)

        # Advanced Section — visible only to developers
        # (developer_mode persists via settings; not exposed in UI for end users)

    def setup_about_tab(self):
        """Creates the branding and diagnostics utility panel."""
        self.tab_about = QWidget()
        layout = QVBoxLayout(self.tab_about)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignTop)

        # Icon logo
        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignCenter)

        icon_path = ResourceManager.get_icon_path()
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                icon_lbl.setPixmap(
                    pixmap.scaled(70, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
        layout.addWidget(icon_lbl)

        title_lbl = QLabel("GeoQA – GIS Data Quality Auditor")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #1E3A8A;")
        title_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_lbl)

        philosophy_lbl = QLabel("“Validate first. Analyze second.”")
        philosophy_lbl.setStyleSheet(
            "font-style: italic; color: #2563EB; font-weight: bold; "
            "background-color: #EFF6FF; border: 1px solid #BFDBFE; "
            "padding: 6px; border-radius: 4px; font-size: 11px;"
        )
        philosophy_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(philosophy_lbl)

        cards_layout = QGridLayout()
        cards_layout.setSpacing(8)

        def make_card(title, value):
            card = QWidget()
            card.setStyleSheet(
                "background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 4px;"
            )
            vbox = QVBoxLayout(card)
            vbox.setContentsMargins(10, 10, 10, 10)
            vbox.setSpacing(2)
            lbl_title = QLabel(title)
            lbl_title.setStyleSheet("color: #64748B; font-size: 10px; font-weight: bold; border: none;")
            lbl_title.setAlignment(Qt.AlignCenter)
            lbl_val = QLabel(value)
            lbl_val.setStyleSheet("color: #0F172A; font-size: 14px; font-weight: bold; border: none;")
            lbl_val.setAlignment(Qt.AlignCenter)
            vbox.addWidget(lbl_title)
            vbox.addWidget(lbl_val)
            return card

        try:
            from ..core.rules.loader import RuleLoader
            rule_count = str(len(RuleLoader.discover_rules()))
        except Exception:
            rule_count = "14"

        cards_layout.addWidget(make_card("Version", "1.1.0"), 0, 0)
        cards_layout.addWidget(make_card("License", "GPL v3"), 0, 1)
        cards_layout.addWidget(make_card("Rules", rule_count), 1, 0)
        cards_layout.addWidget(make_card("QGIS", "3.28+"), 1, 1)

        layout.addLayout(cards_layout)

        layout.addSpacing(5)

        # Action links
        links_layout = QHBoxLayout()
        help_btn = QPushButton("Open User Guide")
        help_btn.clicked.connect(self.open_user_guide)
        diag_btn = QPushButton("Run Self-Test Diagnostics")
        diag_btn.clicked.connect(self.run_self_diagnostics)
        repo_btn = QPushButton("View on GitHub")
        repo_btn.clicked.connect(self.open_repo)

        links_layout.addWidget(help_btn)
        links_layout.addWidget(diag_btn)
        links_layout.addWidget(repo_btn)
        layout.addLayout(links_layout)

    # --- Data Population ---

    def populate_layers(self):
        """Discovers vector layers loaded in the active QGIS project."""
        self.list_widget.clear()
        layers = QgsProject.instance().mapLayers().values()
        vector_layers = [lyr for lyr in layers if lyr.type() == QgsMapLayer.VectorLayer]

        if not vector_layers:
            item = QListWidgetItem("No vector layers loaded in project.")
            item.setFlags(Qt.NoItemFlags)
            self.list_widget.addItem(item)
            self.run_btn.setEnabled(False)
            return

        self.run_btn.setEnabled(True)
        for layer in vector_layers:
            # Gather context: geometry type and CRS
            try:
                geom_type = layer.geometryType()
                geom_str = "Unknown"
                if geom_type == 0:
                    geom_str = "Point"
                elif geom_type == 1:
                    geom_str = "Line"
                elif geom_type == 2:
                    geom_str = "Polygon"

                crs_str = layer.crs().authid() if layer.crs().isValid() else "No CRS"
                display_text = f"{layer.name()}  ({geom_str} - {crs_str})"
            except Exception:
                display_text = layer.name()

            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, layer.id())
            item.setCheckState(Qt.Checked)
            self.list_widget.addItem(item)

    def select_all(self):
        """Checks all layer items in the list widget."""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.flags() & Qt.ItemIsUserCheckable:
                item.setCheckState(Qt.Checked)

    def select_none(self):
        """Unchecks all layer items in the list widget."""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.flags() & Qt.ItemIsUserCheckable:
                item.setCheckState(Qt.Unchecked)

    def populate_rules_table(self):
        """Populates the rules list, mapping active states and severities."""
        self._table_loading = True
        self.rules_table.setRowCount(0)

        from ..core.rules.loader import RuleLoader

        all_rules = RuleLoader.discover_rules()
        all_rules.sort(key=lambda r: r.rule_id)

        self.rules_table.setRowCount(len(all_rules))

        for idx, rule in enumerate(all_rules):
            rule_id = rule.rule_id

            # Read settings overrides from SettingsManager
            saved_enabled = self.settings.get_setting(
                f"GeoQA/rules/{rule_id}/enabled", None
            )
            rule_enabled = (
                bool(saved_enabled) if saved_enabled is not None else rule.enabled
            )

            saved_severity = self.settings.get_setting(
                f"GeoQA/rules/{rule_id}/severity", None
            )
            rule_severity = saved_severity if saved_severity else rule.severity.value

            # 1. Active Checkbox Column
            active_item = QTableWidgetItem()
            active_item.setCheckState(Qt.Checked if rule_enabled else Qt.Unchecked)
            active_item.setData(Qt.UserRole, rule_id)
            self.rules_table.setItem(idx, 0, active_item)

            # 2. Code Column
            code_item = QTableWidgetItem(rule_id)
            code_item.setTextAlignment(Qt.AlignCenter)
            code_item.setToolTip(rule.description)
            self.rules_table.setItem(idx, 1, code_item)

            # 3. Name Column
            name_item = QTableWidgetItem(rule.name)
            name_item.setToolTip(rule.description)
            self.rules_table.setItem(idx, 2, name_item)

            # 4. Severity Combo Column
            sev_combo = QComboBox()
            sev_combo.addItems(["Low", "Medium", "High", "Critical"])
            title_severity = (
                rule_severity.title()
                if hasattr(rule_severity, "title")
                else rule_severity
            )
            combo_index = sev_combo.findText(title_severity)
            if combo_index >= 0:
                sev_combo.setCurrentIndex(combo_index)

            sev_combo.currentIndexChanged.connect(
                lambda _, r_id=rule_id, combo=sev_combo: self.save_rule_severity(
                    r_id, combo.currentText()
                )
            )
            self.rules_table.setCellWidget(idx, 3, sev_combo)

        # Connect itemChanged signal — do this before clearing _table_loading guard
        try:
            self.rules_table.itemChanged.disconnect()
        except Exception:
            pass
        self.rules_table.itemChanged.connect(self.on_table_item_changed)

        self._table_loading = False

    # --- Configuration State Handlers ---

    def load_saved_profile(self):
        """Loads the previously saved audit profile from settings and restores the combo selection."""
        saved_profile = self.settings.get_setting("GeoQA/selected_profile", "General")
        index = self.profile_combo.findText(saved_profile)
        if index >= 0:
            self.profile_combo.setCurrentIndex(index)

    def save_selected_profile(self):
        """Persists the currently selected audit profile to settings."""
        self.settings.set_setting(
            "GeoQA/selected_profile", self.profile_combo.currentText()
        )

    def on_table_item_changed(self, item):
        if self._table_loading or item.column() != 0:
            return
        rule_id = item.data(Qt.UserRole)
        if rule_id:
            is_checked = item.checkState() == Qt.Checked
            self.settings.set_setting(f"GeoQA/rules/{rule_id}/enabled", is_checked)

    def save_rule_severity(self, rule_id, severity_value):
        if self._table_loading:
            return
        self.settings.set_setting(f"GeoQA/rules/{rule_id}/severity", severity_value)

    def reset_rules_to_defaults(self):
        """Removes all custom severity and enabled overrides from settings."""
        from ..core.rules.loader import RuleLoader
        all_rules = RuleLoader.discover_rules()
        for rule in all_rules:
            self.settings.remove_setting(f"GeoQA/rules/{rule.rule_id}/enabled")
            self.settings.remove_setting(f"GeoQA/rules/{rule.rule_id}/severity")
        self.populate_rules_table()
        QMessageBox.information(self, "Rules Reset", "All rules have been restored to their default configurations.")

    # --- Asynchronous Auditing Worker Context (QgsTask) ---

    def run_audit(self):
        """Assembles variables, instantiates validation worker, and submits to QgsTaskManager."""
        selected_layers = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.Checked:
                layer_id = item.data(Qt.UserRole)
                layer = QgsProject.instance().mapLayer(layer_id)
                if layer:
                    selected_layers.append(layer)

        if not selected_layers:
            QMessageBox.warning(
                self, "No Layers Selected", "Please select at least one layer to audit."
            )
            return

        profile_name = self.profile_combo.currentText()

        # 1. UI updates: Disable controls, show progress bar and cancel button
        self.run_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.list_widget.setEnabled(False)
        self.profile_combo.setEnabled(False)
        self.tab_widget.setEnabled(False)

        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.status_lbl.setText("Initializing audit engine...")
        self.repaint()

        try:
            from ..core.engine import ValidationEngine

            # Dependency injection: passes our central settings manager instance
            engine = ValidationEngine(
                settings_manager=self.settings, profile_name=profile_name
            )

            # Subscribe progress callback to update UI status label
            engine.events.subscribe(
                "validation_started", self._on_validation_started
            )

            # Create the background execution QgsTask
            self.active_task = AuditTask(engine, selected_layers)

            # Hook task completion signals
            self.active_task.completed.connect(self.on_audit_completed)
            self.active_task.failed.connect(self.on_audit_failed)

            # Connect task progress changed to sync the PyQt progress bar
            # Cast the emitted float from QgsTask to an int to prevent PyQt TypeError
            self.active_task.progressChanged.connect(
                lambda v: self.progress_bar.setValue(int(v))
            )

            # Submit task to QGIS Task Manager
            QgsApplication.taskManager().addTask(self.active_task)
            self.progress_sequence = ["Starting audit..."]
            self.status_lbl.setText("\n".join(self.progress_sequence))

        except Exception as e:
            QMessageBox.critical(
                self,
                "Audit Launch Failed",
                f"Could not initialize background task: {str(e)}",
            )
            self.reset_ui_controls()

    def update_task_message(self, message):
        """Helper callback executed by events to update text logs."""
        self.status_lbl.setText(message)

    def _on_validation_started(self, layer_count):
        """Callback to report progress on validation startup."""
        if len(self.progress_sequence) > 0:
            self.progress_sequence[-1] = self.progress_sequence[-1].replace("...", " done.")
        self.progress_sequence.append(f"Auditing {layer_count} layer(s)...")
        self.update_task_message("\n".join(self.progress_sequence))

    def cancel_audit(self):
        """Instructs the active background task to cancel execution."""
        if self.active_task:
            self.status_lbl.setText("Requesting cancel...")
            self.active_task.cancel()
            self.cancel_btn.setEnabled(False)

    def on_audit_completed(self, project_summary):
        """Triggered in main thread when QgsTask finishes successfully."""
        self.last_project_summary = project_summary

        score = project_summary.calculate_score()
        grade = project_summary.get_grade()

        # Write HTML dashboard report to a secure temporary file
        try:
            from ..reporting.html import generate_html_report

            # Resolve QGIS version string for telemetry metadata
            try:
                from qgis.core import Qgis
                qgis_ver = f"QGIS {Qgis.QGIS_VERSION}"
            except Exception:
                qgis_ver = "QGIS 3.x"

            html_content = generate_html_report(project_summary, qgis_version=qgis_ver)

            with tempfile.NamedTemporaryFile(
                suffix=".html",
                prefix="geoqa_report_",
                delete=False,
                mode="w",
                encoding="utf-8",
            ) as temp_file:
                temp_file.write(html_content)
                report_path = temp_file.name

            self.temp_files.append(report_path)
            webbrowser.open(f"file:///{report_path.replace(os.sep, '/')}")

            self.export_btn.setEnabled(True)
            self.open_last_report_btn.setVisible(True)

            # Build Executive Summary
            status_text = "Ready for Analysis" if grade in ["A", "B"] else "Review Required"
            if score == 100:
                rec_text = "No issues detected. Dataset is suitable for GIS analysis."
            else:
                rec_text = "Data quality issues detected. Review the report before analysis."

            layers_count = len(project_summary.layer_summaries)
            total_issues = sum(len(ls.issues) for ls in project_summary.layer_summaries)
            critical = sum(1 for ls in project_summary.layer_summaries for i in ls.issues if i.severity.name == "CRITICAL")
            warnings = total_issues - critical

            exec_summary = (
                f"GeoQA Audit Complete\n"
                f"--------------------------\n"
                f"Status:          {status_text}\n"
                f"Quality Score:   {score}/100  (Grade {grade})\n"
                f"Layers Audited:  {layers_count}\n"
                f"Critical Issues: {critical}  |  Warnings: {warnings}\n\n"
                f"{rec_text}"
            )

            grade_status_colors = {
                "A": {"bg": "#DCFCE7", "fg": "#15803D"},
                "B": {"bg": "#EFF6FF", "fg": "#1D4ED8"},
                "C": {"bg": "#FEF3C7", "fg": "#B45309"},
                "D": {"bg": "#FFF7ED", "fg": "#C2410C"},
                "F": {"bg": "#FEF2F2", "fg": "#B91C1C"},
            }
            palette = grade_status_colors.get(grade, {"bg": "#F1F5F9", "fg": "#475569"})

            self.status_lbl.setStyleSheet(
                f"background-color: {palette['bg']}; color: {palette['fg']}; "
                f"border: 1px solid #E2E8F0; border-radius: 6px; padding: 10px; "
                f"font-family: monospace; font-size: 11px;"
            )
            self.status_lbl.setText(exec_summary)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Report Export Failed",
                f"Audit succeeded but report generation failed: {str(e)}",
            )
            self.status_lbl.setText("Audit succeeded, report generation failed.")

        self.reset_ui_controls()

    def on_audit_failed(self, exception):
        """Triggered in main thread when QgsTask encounters a processing exception."""
        QMessageBox.critical(
            self,
            "Audit Failed",
            f"Background validation task crashed:\n{str(exception)}",
        )
        self.status_lbl.setText("Validation failed. Check details in dialog.")
        self.reset_ui_controls()

    def reset_ui_controls(self):
        """Restores UI control states when validation finishes or crashes."""
        self.run_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.list_widget.setEnabled(True)
        self.profile_combo.setEnabled(True)
        self.tab_widget.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.active_task = None
        # Reset status label back to neutral style so it looks clean on next audit launch
        self.status_lbl.setStyleSheet(
            "background-color: #F1F5F9; border: 1px solid #E2E8F0; "
            "border-radius: 6px; padding: 10px; color: #475569; "
            "font-weight: 500; font-size: 11px; min-height: 50px;"
        )

    # --- Extra Utilities ---

    def run_self_diagnostics(self):
        """Runs the diagnostics self-test suite and shows reports inside a scrollable textbox popup."""
        results, log_text = GeoQADiagnostics.run_all()

        diag_dialog = QDialog(self)
        diag_dialog.setWindowTitle("GeoQA Diagnostics Self-Test Log")
        diag_dialog.resize(450, 300)

        v_layout = QVBoxLayout(diag_dialog)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setText(log_text)
        text_edit.setFontFamily("monospace")
        text_edit.setStyleSheet(
            "background-color: #1E293B; color: #E2E8F0; padding: 8px; border-radius: 4px;"
        )
        v_layout.addWidget(text_edit)

        ok_btn = QPushButton("Close")
        ok_btn.clicked.connect(diag_dialog.accept)
        v_layout.addWidget(ok_btn)

        diag_dialog.exec_()

    def export_csv(self):
        """Saves a CSV spreadsheet report to a location chosen by user."""
        if not self.last_project_summary:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV Quality Report", "", "CSV Files (*.csv)"
        )
        if file_path:
            try:
                from ..reporting.csv import generate_csv_report

                csv_content = generate_csv_report(self.last_project_summary)
                with open(file_path, "w", newline="", encoding="utf-8") as f:
                    f.write(csv_content)
                QMessageBox.information(
                    self, "Export Successful", f"CSV quality report saved:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Export Failed", f"Failed to save CSV report: {str(e)}"
                )

    def open_user_guide(self):
        """Opens user guide documentation. Falls back to info dialog if file missing."""
        doc_path = ResourceManager.get_docs_path("user_guide.md")
        if os.path.exists(doc_path):
            # Open as plain text in browser — works cross-platform
            webbrowser.open(f"file:///{doc_path.replace(os.sep, '/')}")
        else:
            QMessageBox.information(
                self,
                "User Guide",
                "GeoQA User Guide\n\n"
                "1. Select your target vector layers in the Validation tab.\n"
                "2. Choose an Audit Profile (General, Geometry Only, etc.).\n"
                "3. Click 'Start Audit' to run validation.\n"
                "4. The HTML report opens automatically in your browser.\n"
                "5. Use Export to save a CSV copy of the results.\n\n"
                "For full documentation, visit the GitHub repository.",
            )

    def open_repo(self):
        """Opens the plugin GitHub repository in the user's default browser."""
        import configparser
        repo_url = "https://github.com/roy232355/geoqa"
        try:
            meta_path = ResourceManager.get_config_path("metadata.txt")
            cfg = configparser.ConfigParser()
            cfg.read(meta_path, encoding="utf-8")
            repo_url = cfg.get("general", "repository", fallback=repo_url)
        except Exception:
            pass
        webbrowser.open(repo_url)

    def filter_rules(self, text):
        """Filters the rules table based on search input."""
        search_text = text.lower()
        for i in range(self.rules_table.rowCount()):
            code_item = self.rules_table.item(i, 1)
            name_item = self.rules_table.item(i, 2)
            if not code_item or not name_item:
                continue
            match = search_text in code_item.text().lower() or search_text in name_item.text().lower()
            self.rules_table.setRowHidden(i, not match)

    def open_last_report(self):
        """Opens the last generated HTML report."""
        if self.temp_files:
            last_report = self.temp_files[-1]
            if os.path.exists(last_report):
                webbrowser.open(f"file:///{last_report.replace(os.sep, '/')}")

    def closeEvent(self, event):
        """Cleans up temporary report files on dialog closure."""
        if self.active_task:
            try:
                self.active_task.cancel()
            except Exception:
                pass
        for path in self.temp_files:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass
        super().closeEvent(event)
