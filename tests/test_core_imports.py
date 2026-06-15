"""
Smoke test: verify all 12 new core modules can be imported.

Run with:
    pytest tests/test_core_imports.py -v
"""

import unittest


class TestCoreImports(unittest.TestCase):
    """Verify all new core modules import without error."""

    def test_import_defender_control(self):
        from winsvalinn.core.defender_control import DefenderControl

        self.assertTrue(hasattr(DefenderControl, "__init__"))

    def test_import_firewall_manager(self):
        from winsvalinn.core.firewall_manager import FirewallManager

        self.assertTrue(hasattr(FirewallManager, "__init__"))

    def test_import_security_audit(self):
        from winsvalinn.core.security_audit import SecurityAudit

        self.assertTrue(hasattr(SecurityAudit, "__init__"))

    def test_import_bloatware_remover(self):
        from winsvalinn.core.bloatware_remover import BloatwareRemover

        self.assertTrue(hasattr(BloatwareRemover, "__init__"))

    def test_import_telemetry_blocker(self):
        from winsvalinn.core.telemetry_blocker import TelemetryBlocker

        self.assertTrue(hasattr(TelemetryBlocker, "__init__"))

    def test_import_dns_manager(self):
        from winsvalinn.core.dns_manager import DNSManager

        self.assertTrue(hasattr(DNSManager, "__init__"))

    def test_import_hosts_manager(self):
        from winsvalinn.core.hosts_manager import HostsManager

        self.assertTrue(hasattr(HostsManager, "__init__"))

    def test_import_package_manager(self):
        from winsvalinn.core.package_manager import PackageManager

        self.assertTrue(hasattr(PackageManager, "__init__"))

    def test_import_update_control(self):
        from winsvalinn.core.update_control import UpdateControl

        self.assertTrue(hasattr(UpdateControl, "__init__"))

    def test_import_features_manager(self):
        from winsvalinn.core.features_manager import FeaturesManager

        self.assertTrue(hasattr(FeaturesManager, "__init__"))

    def test_import_ai_windows(self):
        from winsvalinn.core.ai_windows import AIWindowsRemover

        self.assertTrue(hasattr(AIWindowsRemover, "__init__"))

    def test_core_init_exports_all(self):
        """Verify core __init__ exports all 16 classes."""
        from winsvalinn import core

        expected = [
            "SecurityScanner",
            "SystemOptimizer",
            "GPUBrandOptimizer",
            "RAMOptimizer",
            "DefenderControl",
            "FirewallManager",
            "SecurityAudit",
            "BloatwareRemover",
            "TelemetryBlocker",
            "DNSManager",
            "HostsManager",
            "PackageManager",
            "UpdateControl",
            "FeaturesManager",
            "AIWindowsRemover",
        ]
        for name in expected:
            self.assertTrue(hasattr(core, name), f"core module missing export: {name}")

    def test_utils_imports(self):
        """Verify utils package imports work."""
        from winsvalinn.utils import set_registry
        from winsvalinn.utils.validation import validate_port_range

        self.assertTrue(callable(validate_port_range))
        self.assertTrue(callable(set_registry))

    def test_config_import(self):
        """Verify config module imports."""
        from winsvalinn.config import get_config

        self.assertTrue(callable(get_config))


if __name__ == "__main__":
    unittest.main(verbosity=2)
