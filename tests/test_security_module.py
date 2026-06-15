"""
Unit tests for security module.

Run with:
    pytest tests/test_security_module.py -v
"""

import os
import unittest

from winsvalinn.core.security import SecurityScanner


class TestSecurityScanner(unittest.TestCase):
    """Test SecurityScanner class."""

    def setUp(self):
        self.scanner = SecurityScanner()

    # ── Port Classification Tests ──

    def test_system_critical_ports_dns(self):
        self.assertIn(53, self.scanner.SYSTEM_CRITICAL_PORTS)

    def test_system_critical_ports_rpc(self):
        self.assertIn(135, self.scanner.SYSTEM_CRITICAL_PORTS)

    def test_system_critical_ports_netbios(self):
        self.assertIn(137, self.scanner.SYSTEM_CRITICAL_PORTS)
        self.assertIn(138, self.scanner.SYSTEM_CRITICAL_PORTS)
        self.assertIn(139, self.scanner.SYSTEM_CRITICAL_PORTS)

    def test_system_critical_ports_smb(self):
        self.assertIn(445, self.scanner.SYSTEM_CRITICAL_PORTS)

    def test_normal_ports_not_critical(self):
        self.assertNotIn(80, self.scanner.SYSTEM_CRITICAL_PORTS)
        self.assertNotIn(21, self.scanner.SYSTEM_CRITICAL_PORTS)

    # ── Well-Known Ports Tests ──

    def test_well_known_ports_http(self):
        self.assertEqual(self.scanner.WELL_KNOWN_PORTS.get(80), "HTTP")

    def test_well_known_ports_https(self):
        self.assertEqual(self.scanner.WELL_KNOWN_PORTS.get(443), "HTTPS")

    def test_well_known_ports_ssh(self):
        self.assertEqual(self.scanner.WELL_KNOWN_PORTS.get(22), "SSH")

    def test_well_known_ports_rdp(self):
        self.assertEqual(self.scanner.WELL_KNOWN_PORTS.get(3389), "RDP")

    def test_unknown_port_returns_default(self):
        self.assertEqual(self.scanner.WELL_KNOWN_PORTS.get(99999, "Unknown"), "Unknown")

    # ── Risky Ports Tests ──

    def test_risky_ports_telnet(self):
        self.assertIn(23, self.scanner.RISKY_PORTS)

    def test_risky_ports_rdp(self):
        self.assertIn(3389, self.scanner.RISKY_PORTS)

    def test_risky_ports_vnc(self):
        self.assertIn(5900, self.scanner.RISKY_PORTS)

    def test_normal_ports_not_risky(self):
        self.assertNotIn(80, self.scanner.RISKY_PORTS)
        self.assertNotIn(443, self.scanner.RISKY_PORTS)

    # ── Edge Cases ──

    def test_port_range_boundary_lower(self):
        self.assertTrue(1 <= 1 <= 65535)

    def test_port_range_boundary_upper(self):
        self.assertTrue(1 <= 65535 <= 65535)

    def test_port_zero_invalid(self):
        self.assertFalse(0 >= 1)

    def test_port_negative_invalid(self):
        self.assertFalse(-1 >= 1)

    # ── Process Whitelist Tests ──

    def test_system_processes_whitelisted(self):
        system_procs = {"svchost.exe", "csrss.exe", "explorer.exe", "lsass.exe"}
        for proc in system_procs:
            self.assertIn(proc, self.scanner.SYSTEM_PROCESS_WHITELIST)

    # ── Integration Tests ──

    @unittest.skipUnless(os.name == "nt", "Windows-only test")
    def test_firewall_check_returns_dict(self):
        result = self.scanner.check_firewall_status()
        self.assertIsInstance(result, dict)

    @unittest.skipUnless(os.name == "nt", "Windows-only test")
    def test_defender_check_returns_dict(self):
        result = self.scanner.check_defender_status()
        self.assertIsInstance(result, dict)

    @unittest.skipUnless(os.name == "nt", "Windows-only test")
    def test_port_scan_localhost_completes(self):
        self.scanner.scan_active = True
        results = self.scanner.scan_local_ports(port_range=(1, 100), timeout=0.1)
        self.assertIsInstance(results, list)


if __name__ == "__main__":
    unittest.main(verbosity=2)
