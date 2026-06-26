# -*- coding: utf-8 -*-
import os
import sys
import tempfile
import platform
from typing import Dict, Tuple


class GeoQADiagnostics:
    """Executes environment checks, write access tests, rule loading validations, and platform audits."""

    @staticmethod
    def run_all() -> Tuple[Dict[str, bool], str]:
        """Runs the self-test diagnostic suite.

        Returns:
            Tuple[Dict[str, bool], str]: Map of test results and the formatted text log.
        """
        results = {}
        log_lines = []
        log_lines.append("=" * 60)
        log_lines.append("GeoQA Diagnostics Self-Test Panel")
        log_lines.append("=" * 60)

        # 1. Platform Details
        log_lines.append(
            f"OS Platform      : {platform.system()} ({platform.release()})"
        )
        log_lines.append(f"Python Version   : {sys.version.split()[0]}")
        log_lines.append(f"Path Separator   : '{os.sep}'")

        # 2. Check Temp Directory Write Access
        temp_dir = tempfile.gettempdir()
        temp_write_ok = False
        test_file = os.path.join(temp_dir, "geoqa_write_test.txt")
        try:
            with open(test_file, "w", encoding="utf-8") as f:
                f.write("write_test")
            if os.path.exists(test_file):
                os.remove(test_file)
                temp_write_ok = True
        except Exception:
            pass
        results["temp_write_access"] = temp_write_ok
        status_str = "[PASS] Writable" if temp_write_ok else "[FAIL] Read-only"
        log_lines.append(f"Temp Directory   : {temp_dir} -> {status_str}")

        # 3. Rule Loader Discovery check
        rules_discovered = 0
        loader_ok = False
        try:
            from .rules.loader import RuleLoader

            discovered = RuleLoader.discover_rules()
            rules_discovered = len(discovered)
            loader_ok = rules_discovered > 0
        except Exception as e:
            log_lines.append(f"Rule Loader Error: {str(e)}")

        results["rule_loader_ok"] = loader_ok
        status_reg = "[PASS]" if loader_ok else "[FAIL] No rules loaded"
        log_lines.append(
            f"Rule Registry    : Discovered {rules_discovered} rule modules -> {status_reg}"
        )

        # 4. Check QGIS Environment Context
        qgis_loaded = False
        try:
            import qgis.core  # noqa: F401

            qgis_loaded = True
        except ImportError:
            pass
        results["qgis_loaded"] = qgis_loaded
        status_qgis = (
            "[PASS] Loaded in QGIS"
            if qgis_loaded
            else "[NOTE] Running offline / test mode"
        )
        log_lines.append(f"QGIS PyQGIS API  : {status_qgis}")

        # Summary Audit Check
        log_lines.append("-" * 60)
        overall_pass = all(results[k] for k in ["temp_write_access", "rule_loader_ok"])
        results["overall"] = overall_pass
        status_diag = (
            "SUCCESS - Ready to audit GIS layers"
            if overall_pass
            else "WARNING - Resolve failures before audits"
        )
        log_lines.append(f"DIAGNOSTIC STATUS: {status_diag}")
        log_lines.append("=" * 60)

        return results, "\n".join(log_lines)
