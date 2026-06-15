"""Comprehensive tests for WinSvalinn core modules.

Run with: pytest tests/test_core_modules.py -v --tb=short
Real-time output: pytest tests/test_core_modules.py -v -s
"""

from unittest.mock import MagicMock, patch

import pytest

# ── Scoring Engine ──────────────────────────────────────────────────────


class TestScoringEngine:
    """Tests for src/winsvalinn/scoring.py"""

    def test_import_scoring(self):
        from winsvalinn.scoring import ScoreEngine

        assert callable(ScoreEngine.calc_security_score)
        assert callable(ScoreEngine.calc_optimization_score)

    def test_security_score_range(self):
        from winsvalinn.scoring import ScoreEngine

        # Minimal results dict
        results = {"firewall": {"enabled": True}, "open_ports": [], "processes": []}
        score, recs = ScoreEngine.calc_security_score(results)
        assert isinstance(score, (int, float))
        assert 0 <= score <= 100

    def test_security_score_with_empty_results(self):
        from winsvalinn.scoring import ScoreEngine

        score, recs = ScoreEngine.calc_security_score({})
        assert isinstance(score, (int, float))
        assert isinstance(recs, list)


# ── Config Module ───────────────────────────────────────────────────────


class TestConfigModule:
    """Tests for src/winsvalinn/config.py"""

    def test_import_config(self):
        from winsvalinn.config import Config

        assert callable(Config)

    def test_get_config(self):
        from winsvalinn.config import get_config

        config = get_config()
        assert config is not None


# ── Security Scanner ───────────────────────────────────────────────────


class TestSecurityScanner:
    """Tests for src/winsvalinn/core/security.py"""

    def test_import_scanner(self):
        from winsvalinn.core.security import SecurityScanner

        scanner = SecurityScanner()
        assert scanner is not None

    @patch("subprocess.run")
    def test_get_firewall_status(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="State                                 ON\nState                                 ON\nState                                 ON",
            stderr="",
        )
        from winsvalinn.core.security import SecurityScanner

        scanner = SecurityScanner()
        result = scanner.check_firewall_status()
        assert isinstance(result, dict)

    def test_scanner_callback(self):
        messages = []
        from winsvalinn.core.security import SecurityScanner

        scanner = SecurityScanner(callback=lambda msg, level: messages.append((msg, level)))
        assert scanner.callback is not None


# ── Security Audit ─────────────────────────────────────────────────────


class TestSecurityAudit:
    """Tests for src/winsvalinn/core/security_audit.py"""

    def test_import_audit(self):
        from winsvalinn.core.security_audit import SecurityAudit

        audit = SecurityAudit()
        assert audit is not None

    @patch("subprocess.run")
    def test_run_security_scan_structure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="True", stderr="")
        from winsvalinn.core.security_audit import SecurityAudit

        audit = SecurityAudit()
        result = audit.run_security_scan()
        assert "issues" in result
        assert "warnings" in result
        assert "passed" in result
        assert "score" in result
        assert isinstance(result["score"], int)
        assert 0 <= result["score"] <= 100

    def test_detect_third_party_av_method_exists(self):
        from winsvalinn.core.security_audit import SecurityAudit

        audit = SecurityAudit()
        assert hasattr(audit, "_detect_third_party_av")

    def test_detect_third_party_firewall_method_exists(self):
        from winsvalinn.core.security_audit import SecurityAudit

        audit = SecurityAudit()
        assert hasattr(audit, "_detect_third_party_firewall")


# ── RAM Optimizer ──────────────────────────────────────────────────────


class TestRAMOptimizer:
    """Tests for src/winsvalinn/core/ram.py"""

    def test_import_ram(self):
        from winsvalinn.core.ram import RAMOptimizer

        opt = RAMOptimizer()
        assert opt is not None

    @patch("psutil.process_iter")
    @patch("psutil.virtual_memory")
    def test_get_detailed_memory_structure(self, mock_vm, mock_iter):
        mock_vm.return_value = MagicMock(
            total=16 * 1024**3, available=8 * 1024**3, percent=50.0, used=8 * 1024**3
        )
        mock_iter.return_value = []
        from winsvalinn.core.ram import RAMOptimizer

        opt = RAMOptimizer()
        result = opt.get_detailed_memory()
        assert isinstance(result, dict)


# ── System Optimizer ───────────────────────────────────────────────────


class TestSystemOptimizer:
    """Tests for src/winsvalinn/core/optimization.py"""

    def test_import_optimizer(self):
        from winsvalinn.core.optimization import SystemOptimizer

        opt = SystemOptimizer()
        assert opt is not None


# ── GPU Optimizer ──────────────────────────────────────────────────────


class TestGPUOptimizer:
    """Tests for src/winsvalinn/core/gpu.py"""

    def test_import_gpu(self):
        from winsvalinn.core.gpu import GPUBrandOptimizer

        opt = GPUBrandOptimizer()
        assert opt is not None

    @patch("subprocess.run")
    def test_detect_gpu_brand_returns_tuple(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="NVIDIA GeForce RTX 3080", stderr="")
        from winsvalinn.core.gpu import GPUBrandOptimizer

        opt = GPUBrandOptimizer()
        brand, name = opt.detect_gpu_brand()
        assert isinstance(brand, str)
        assert isinstance(name, str)


# ── Bloatware Remover ──────────────────────────────────────────────────


class TestBloatwareRemover:
    """Tests for src/winsvalinn/core/bloatware_remover.py"""

    def test_import_bloatware(self):
        from winsvalinn.core.bloatware_remover import BloatwareRemover

        remover = BloatwareRemover()
        assert remover is not None

    @patch("subprocess.run")
    def test_detect_installed_apps_returns_list(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        from winsvalinn.core.bloatware_remover import BloatwareRemover

        remover = BloatwareRemover()
        result = remover.detect_installed_apps()
        assert isinstance(result, (list, dict))


# ── Hardware Info ──────────────────────────────────────────────────────


class TestHardwareInfo:
    """Tests for src/winsvalinn/core/hardware_info.py"""

    def test_import_hardware(self):
        from winsvalinn.core.hardware_info import HardwareAnalyzer

        hw = HardwareAnalyzer()
        assert hw is not None


# ── Network Diagnostics ───────────────────────────────────────────────


class TestNetworkDiagnostics:
    """Tests for src/winsvalinn/core/network_diagnostics.py"""

    def test_import_netdiag(self):
        from winsvalinn.core.network_diagnostics import NetworkDiagnostics

        diag = NetworkDiagnostics()
        assert diag is not None

    @patch("subprocess.run")
    def test_ping_returns_dict(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Reply from 8.8.8.8: bytes=32 time=10ms TTL=117\n\nPing statistics for 8.8.8.8:\n    Packets: Sent = 1, Received = 1, Lost = 0 (0% loss),\nApproximate round trip times in milli-seconds:\n    Minimum = 10ms, Maximum = 10ms, Average = 10ms",
            stderr="",
        )
        from winsvalinn.core.network_diagnostics import NetworkDiagnostics

        diag = NetworkDiagnostics()
        result = diag.ping("8.8.8.8", count=1)
        assert isinstance(result, dict)


# ── Bandwidth Monitor ─────────────────────────────────────────────────


class TestBandwidthMonitor:
    """Tests for src/winsvalinn/core/bandwidth_monitor.py"""

    def test_import_bandwidth(self):
        from winsvalinn.core.bandwidth_monitor import BandwidthMonitor

        mon = BandwidthMonitor()
        assert mon is not None

    @patch("psutil.net_io_counters")
    def test_get_current_usage_returns_dict(self, mock_io):
        mock_io.return_value = MagicMock(
            bytes_sent=1024, bytes_recv=2048, packets_sent=10, packets_recv=20, errin=0, errout=0
        )
        from winsvalinn.core.bandwidth_monitor import BandwidthMonitor

        mon = BandwidthMonitor()
        result = mon.get_current_usage()
        assert isinstance(result, dict)


# ── Dry Run ────────────────────────────────────────────────────────────


class TestDryRun:
    """Tests for src/winsvalinn/core/dry_run.py"""

    def test_import_dry_run(self):
        from winsvalinn.core.dry_run import DryRunContext

        assert callable(DryRunContext)


# ── Restore Point ──────────────────────────────────────────────────────


class TestRestorePoint:
    """Tests for src/winsvalinn/core/restore_point.py"""

    def test_import_restore_point(self):
        from winsvalinn.core.restore_point import RestorePointManager

        mgr = RestorePointManager()
        assert mgr is not None


# ── Registry Backup ────────────────────────────────────────────────────


class TestRegistryBackup:
    """Tests for src/winsvalinn/core/registry_backup.py"""

    def test_import_registry_backup(self):
        from winsvalinn.core.registry_backup import RegistryBackupManager

        mgr = RegistryBackupManager()
        assert mgr is not None


# ── Change Logger ──────────────────────────────────────────────────────


class TestChangeLogger:
    """Tests for src/winsvalinn/core/change_log.py"""

    def test_import_change_log(self):
        from winsvalinn.core.change_log import ChangeLogger

        logger = ChangeLogger()
        assert logger is not None


# ── I18n ───────────────────────────────────────────────────────────────


class TestI18n:
    """Tests for src/winsvalinn/i18n/strings.py"""

    def test_import_i18n(self):
        from winsvalinn.i18n.strings import I18n

        i18n = I18n(lang="en")
        assert i18n is not None

    def test_i18n_english(self):
        from winsvalinn.i18n.strings import I18n

        i18n = I18n(lang="en")
        result = i18n.t("app_title")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_i18n_spanish(self):
        from winsvalinn.i18n.strings import I18n

        i18n = I18n(lang="es")
        result = i18n.t("app_title")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_i18n_missing_key_returns_bracketed(self):
        from winsvalinn.i18n.strings import I18n

        i18n = I18n(lang="en")
        result = i18n.t("nonexistent_key_12345")
        assert "[" in result or result == "nonexistent_key_12345"

    def test_i18n_switch_language(self):
        from winsvalinn.i18n.strings import I18n

        i18n = I18n(lang="en")
        title_en = i18n.t("app_title")
        i18n.lang = "es"
        title_es = i18n.t("app_title")
        # Both should return valid strings (may or may not differ)
        assert isinstance(title_en, str) and isinstance(title_es, str)


# ── Utils ──────────────────────────────────────────────────────────────


class TestUtils:
    """Tests for src/winsvalinn/utils/"""

    def test_import_logger(self):
        from winsvalinn.utils.logger import setup_logging

        assert callable(setup_logging)

    def test_import_scan_cache(self):
        from winsvalinn.utils.scan_cache import ScanCache

        cache = ScanCache()
        assert cache is not None

    def test_scan_cache_get_set(self):
        from winsvalinn.utils.scan_cache import ScanCache

        cache = ScanCache()
        cache.set("test_key", {"data": 42})
        result = cache.get("test_key")
        assert result is not None
        assert result.get("data") == 42

    def test_import_validation(self):
        from winsvalinn.utils.validation import validate_file_path

        assert callable(validate_file_path)

    def test_validate_port_range(self):
        from winsvalinn.utils.validation import validate_port_range

        result = validate_port_range(1, 1024)
        assert result is not None

    def test_validate_port_range_invalid(self):
        from winsvalinn.utils.validation import ValidationError, validate_port_range

        with pytest.raises((ValidationError, ValueError)):
            validate_port_range(1024, 1)


# ── Core __init__ exports ──────────────────────────────────────────────


class TestCoreExports:
    """Test that all core modules are importable."""

    CORE_CLASSES = [
        ("security", "SecurityScanner"),
        ("optimization", "SystemOptimizer"),
        ("gpu", "GPUBrandOptimizer"),
        ("ram", "RAMOptimizer"),
        ("restore_point", "RestorePointManager"),
        ("registry_backup", "RegistryBackupManager"),
        ("change_log", "ChangeLogger"),
        ("disk_health", "DiskHealthMonitor"),
        ("hardware_info", "HardwareAnalyzer"),
        ("driver_manager", "DriverManager"),
        ("thermal_monitor", "ThermalMonitor"),
        ("bandwidth_monitor", "BandwidthMonitor"),
        ("network_diagnostics", "NetworkDiagnostics"),
        ("vpn_detector", "VPNProxyDetector"),
        ("firewall_manager", "FirewallManager"),
        ("defender_control", "DefenderControl"),
        ("security_audit", "SecurityAudit"),
        ("bloatware_remover", "BloatwareRemover"),
        ("browser_cleanup", "BrowserCleanup"),
        ("privacy_cleaner", "PrivacyCleaner"),
        ("environment_manager", "EnvironmentManager"),
        ("dns_manager", "DNSManager"),
        ("hosts_manager", "HostsManager"),
        ("telemetry_blocker", "TelemetryBlocker"),
        ("update_control", "UpdateControl"),
        ("features_manager", "FeaturesManager"),
        ("package_manager", "PackageManager"),
        ("dry_run", "DryRunContext"),
    ]

    @pytest.mark.parametrize("module_name,class_name", CORE_CLASSES)
    def test_core_import(self, module_name, class_name):
        """Each core module should be importable and its class constructable."""
        import importlib

        mod = importlib.import_module(f"winsvalinn.core.{module_name}")
        cls = getattr(mod, class_name)
        instance = cls()
        assert instance is not None
