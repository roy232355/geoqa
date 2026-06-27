# -*- coding: utf-8 -*-
import os


class ResourceManager:
    """Manages application assets, paths, styles, and documentation resources across OS environments."""

    @staticmethod
    def get_plugin_root() -> str:
        """Returns the absolute path to the plugin root folder."""
        # This file is located under core/
        core_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return core_dir

    @classmethod
    def get_icon_path(cls) -> str:
        """Returns the absolute path to the plugin icon file."""
        return os.path.join(cls.get_plugin_root(), "icons", "icon.png")

    @classmethod
    def get_docs_path(cls, filename: str) -> str:
        """Returns the absolute path to a specific documentation file."""
        return os.path.join(cls.get_plugin_root(), "docs", filename)

    @classmethod
    def get_config_path(cls, filename: str) -> str:
        """Returns the absolute path to a configuration JSON file."""
        return os.path.join(cls.get_plugin_root(), filename)

    @staticmethod
    def get_dialog_stylesheet() -> str:
        """Returns the premium QSS stylesheet for PyQt dialog styling."""
        return """
        * {
            outline: none;
        }

        QDialog {
            background-color: #F8FAFC;
        }

        QTabWidget::pane {
            border: 1px solid #E2E8F0;
            background-color: #FFFFFF;
            border-radius: 6px;
            top: -1px;
        }
        QTabBar::tab {
            background-color: #EDF2F7;
            border: 1px solid #CBD5E0;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            padding: 6px 12px;
            min-width: 90px;
            margin-right: 4px;
            color: #4A5568;
            font-weight: bold;
            font-size: 11px;
        }
        QTabBar::tab:selected {
            background-color: #FFFFFF;
            border-color: #E2E8F0;
            border-bottom-color: #FFFFFF;
            color: #2563EB;
        }
        QTabBar::tab:hover:!selected {
            background-color: #E2E8F0;
            color: #2D3748;
        }

        QPushButton {
            background-color: #FFFFFF;
            border: 1px solid #CBD5E1;
            border-radius: 4px;
            padding: 6px 14px;
            color: #334155;
            font-weight: 600;
            font-size: 11px;
        }
        QPushButton:hover {
            background-color: #F1F5F9;
            border-color: #94A3B8;
        }
        QPushButton:pressed {
            background-color: #E2E8F0;
        }
        QPushButton:disabled {
            background-color: #E2E8F0;
            color: #94A3B8;
            border-color: #E2E8F0;
        }

        QPushButton#primaryBtn {
            background-color: #2563EB;
            color: #FFFFFF;
            border: 1px solid #1D4ED8;
            padding: 8px 14px;
            font-size: 12px;
        }
        QPushButton#primaryBtn:hover {
            background-color: #1D4ED8;
            border-color: #1E40AF;
        }
        QPushButton#primaryBtn:pressed {
            background-color: #1E40AF;
        }

        QPushButton#cancelBtn {
            padding: 8px 14px;
            font-size: 12px;
            color: #B91C1C;
            border-color: #FCA5A5;
        }
        QPushButton#cancelBtn:hover {
            background-color: #FEF2F2;
            border-color: #F87171;
        }
        QPushButton#cancelBtn:disabled {
            color: #94A3B8;
            border-color: #E2E8F0;
        }

        QComboBox {
            border: 1px solid #CBD5E1;
            border-radius: 4px;
            padding: 5px 8px;
            background-color: #FFFFFF;
            color: #1E293B;
            min-height: 22px;
        }
        QComboBox:hover {
            border-color: #94A3B8;
        }

        QListWidget {
            border: 1px solid #E2E8F0;
            border-radius: 6px;
            padding: 4px;
            background-color: #FFFFFF;
        }
        QListWidget::item {
            padding: 6px 8px;
            border-bottom: 1px solid #F1F5F9;
            border-radius: 4px;
        }
        QListWidget::item:hover {
            background-color: #F8FAFC;
        }
        QListWidget::item:selected {
            background-color: #EFF6FF;
            color: #1E3A8A;
            border: 1px solid #BFDBFE;
        }

        QLineEdit {
            border: 1px solid #CBD5E1;
            border-radius: 4px;
            padding: 5px 8px;
            background-color: #FFFFFF;
            color: #1E293B;
            font-size: 11px;
        }
        QLineEdit:focus {
            border-color: #2563EB;
        }

        QTableWidget {
            border: 1px solid #E2E8F0;
            border-radius: 6px;
            background-color: #FFFFFF;
            gridline-color: #F1F5F9;
        }
        QHeaderView::section {
            background-color: #F1F5F9;
            padding: 6px;
            border: 1px solid #E2E8F0;
            font-weight: bold;
            color: #475569;
            font-size: 11px;
        }
        """
