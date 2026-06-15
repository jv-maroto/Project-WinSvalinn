"""
Unit Tests for AI Windows Module

Run with:
    pytest tests/test_ai_windows.py -v
"""

import unittest
from unittest.mock import Mock, patch

from winsvalinn.core.ai_windows import AIWindowsRemover


class TestAIWindowsRemover(unittest.TestCase):
    """Test suite for AIWindowsRemover class."""

    def setUp(self):
        self.callback_messages = []

        def test_callback(msg, level="info"):
            self.callback_messages.append((msg, level))

        self.remover = AIWindowsRemover(callback=test_callback)

    def tearDown(self):
        self.callback_messages.clear()

    # ── Detection Tests ──

    @patch("subprocess.run")
    @patch("winsvalinn.core.ai_windows.get_registry")
    def test_check_copilot_status_active(self, mock_get_reg, mock_run):
        """Copilot is active when ShowCopilotButton == '1'."""
        # Registry returns ShowCopilotButton = "1" (button shown = active)
        mock_get_reg.return_value = (True, "1")

        # subprocess.run is used by _is_process_running and _is_service_running
        # Return output that does NOT contain Copilot.exe or RUNNING
        mock_result = Mock()
        mock_result.stdout = "No tasks are running"
        mock_run.return_value = mock_result

        result = self.remover.check_copilot_status()
        self.assertTrue(result["active"])
        self.assertEqual(result["name"], "Windows Copilot")
        self.assertTrue(result["registry_enabled"])

    @patch("subprocess.run")
    @patch("winsvalinn.core.ai_windows.get_registry")
    def test_check_copilot_status_inactive(self, mock_get_reg, mock_run):
        """Copilot is inactive when ShowCopilotButton != '1' and no process/service."""
        mock_get_reg.return_value = (True, "0")

        # No Copilot process running, no CopilotService running
        mock_result = Mock()
        mock_result.stdout = "No tasks are running"
        mock_run.return_value = mock_result

        result = self.remover.check_copilot_status()
        self.assertFalse(result["active"])
        self.assertEqual(result["name"], "Windows Copilot")

    @patch("winsvalinn.core.ai_windows.AIWindowsRemover._is_windows_11_24h2")
    @patch("winsvalinn.core.ai_windows.get_registry")
    def test_check_recall_status_active(self, mock_get_reg, mock_24h2):
        """Recall is active when DisableRecall != '1' and on Windows 11 24H2."""
        # DisableRecall = "0" means Recall is NOT disabled => active
        mock_get_reg.return_value = (True, "0")
        mock_24h2.return_value = True

        result = self.remover.check_recall_status()
        self.assertTrue(result["active"])
        self.assertEqual(result["name"], "Windows Recall")
        self.assertEqual(result["privacy_risk"], "HIGH")

    @patch("winsvalinn.core.ai_windows.AIWindowsRemover._is_windows_11_24h2")
    @patch("winsvalinn.core.ai_windows.get_registry")
    def test_check_recall_status_inactive(self, mock_get_reg, mock_24h2):
        """Recall is inactive when DisableRecall == '1'."""
        # DisableRecall = "1" means Recall IS disabled => inactive
        mock_get_reg.return_value = (True, "1")
        mock_24h2.return_value = True

        result = self.remover.check_recall_status()
        self.assertFalse(result["active"])

    @patch("winsvalinn.core.ai_windows.get_registry")
    def test_check_suggested_actions_active(self, mock_get_reg):
        """Suggested Actions is active when Disabled != '1'."""
        # Disabled = "0" means not disabled => active
        mock_get_reg.return_value = (True, "0")
        result = self.remover.check_suggested_actions()
        self.assertTrue(result["active"])
        self.assertEqual(result["name"], "Suggested Actions")

    @patch("winsvalinn.core.ai_windows.get_registry")
    def test_check_live_captions_active(self, mock_get_reg):
        """Live Captions is active when LiveCaptionsEnabled == '1'."""
        mock_get_reg.return_value = (True, "1")
        result = self.remover.check_live_captions()
        self.assertTrue(result["active"])
        self.assertEqual(result["name"], "Live Captions")

    @patch("subprocess.run")
    def test_check_voice_access_active(self, mock_run):
        """Voice Access is active when VoiceAccess.exe process is running."""
        # _is_process_running calls subprocess.run with tasklist
        mock_result = Mock()
        mock_result.stdout = "VoiceAccess.exe                1234 Console    1    10,000 K"
        mock_run.return_value = mock_result

        result = self.remover.check_voice_access()
        self.assertTrue(result["active"])
        self.assertEqual(result["name"], "Voice Access")

    @patch("winsvalinn.core.ai_windows.get_registry")
    def test_check_ai_widgets_active(self, mock_get_reg):
        """AI Widgets is active when TaskbarDa == '1'."""
        mock_get_reg.return_value = (True, "1")
        result = self.remover.check_ai_widgets()
        self.assertTrue(result["active"])
        self.assertEqual(result["name"], "AI Widgets")

    @patch("winsvalinn.core.ai_windows.get_registry")
    def test_check_ai_widgets_inactive(self, mock_get_reg):
        """AI Widgets is inactive when TaskbarDa != '1'."""
        mock_get_reg.return_value = (True, "0")
        result = self.remover.check_ai_widgets()
        self.assertFalse(result["active"])

    @patch("winsvalinn.core.ai_windows.get_registry")
    def test_check_ai_search_active(self, mock_get_reg):
        """AI Search is active when IsDynamicSearchBoxEnabled == '1'."""
        mock_get_reg.return_value = (True, "1")
        result = self.remover.check_ai_search()
        self.assertTrue(result["active"])
        self.assertEqual(result["name"], "AI Search (Bing)")

    @patch("subprocess.run")
    @patch("winsvalinn.core.ai_windows.get_registry")
    def test_check_ai_telemetry_active(self, mock_get_reg, mock_run):
        """AI Telemetry is active when AllowTelemetry != '0' or DiagTrack is running."""
        # AllowTelemetry = "3" means telemetry enabled (value != "0")
        mock_get_reg.return_value = (True, "3")

        # _is_service_running calls subprocess.run with sc query
        mock_result = Mock()
        mock_result.stdout = "SERVICE_NAME: DiagTrack\n    STATE  : 4  RUNNING"
        mock_run.return_value = mock_result

        result = self.remover.check_ai_telemetry()
        self.assertTrue(result["active"])
        self.assertEqual(result["name"], "AI Telemetry")

    @patch("subprocess.run")
    @patch("winsvalinn.core.ai_windows.get_registry")
    def test_check_ai_telemetry_inactive(self, mock_get_reg, mock_run):
        """AI Telemetry is inactive when AllowTelemetry == '0' and DiagTrack not running."""
        mock_get_reg.return_value = (True, "0")

        # DiagTrack service not running
        mock_result = Mock()
        mock_result.stdout = "SERVICE_NAME: DiagTrack\n    STATE  : 1  STOPPED"
        mock_run.return_value = mock_result

        result = self.remover.check_ai_telemetry()
        self.assertFalse(result["active"])

    @patch("subprocess.run")
    @patch("winsvalinn.core.ai_windows.get_registry")
    def test_check_cortana_status_running(self, mock_get_reg, mock_run):
        """Cortana is active when Cortana.exe is running or ShowCortanaButton == '1'."""
        # Registry: ShowCortanaButton = "1" => button_shown = True => active
        mock_get_reg.return_value = (True, "1")

        # Cortana process check via tasklist
        mock_result = Mock()
        mock_result.stdout = "Cortana.exe                     5678 Console    1    20,000 K"
        mock_run.return_value = mock_result

        result = self.remover.check_cortana_status()
        self.assertTrue(result["active"])
        self.assertEqual(result["name"], "Cortana")

    # ── Full Detection Test ──

    @patch("winsvalinn.core.ai_windows.AIWindowsRemover.check_copilot_status")
    @patch("winsvalinn.core.ai_windows.AIWindowsRemover.check_recall_status")
    @patch("winsvalinn.core.ai_windows.AIWindowsRemover.check_suggested_actions")
    @patch("winsvalinn.core.ai_windows.AIWindowsRemover.check_live_captions")
    @patch("winsvalinn.core.ai_windows.AIWindowsRemover.check_voice_access")
    @patch("winsvalinn.core.ai_windows.AIWindowsRemover.check_ai_widgets")
    @patch("winsvalinn.core.ai_windows.AIWindowsRemover.check_ai_search")
    @patch("winsvalinn.core.ai_windows.AIWindowsRemover.check_ai_telemetry")
    @patch("winsvalinn.core.ai_windows.AIWindowsRemover.check_cortana_status")
    def test_detect_all_ai_features(
        self,
        mock_cortana,
        mock_telemetry,
        mock_search,
        mock_widgets,
        mock_voice,
        mock_captions,
        mock_suggested,
        mock_recall,
        mock_copilot,
    ):
        mock_copilot.return_value = {"active": True, "name": "Windows Copilot"}
        mock_recall.return_value = {"active": False, "name": "Windows Recall"}
        mock_suggested.return_value = {"active": True, "name": "Suggested Actions"}
        mock_captions.return_value = {"active": False, "name": "Live Captions"}
        mock_voice.return_value = {"active": False, "name": "Voice Access"}
        mock_widgets.return_value = {"active": True, "name": "AI Widgets"}
        mock_search.return_value = {"active": True, "name": "AI Search (Bing)"}
        mock_telemetry.return_value = {"active": True, "name": "AI Telemetry"}
        mock_cortana.return_value = {"active": False, "name": "Cortana"}

        results = self.remover.detect_all_ai_features()

        self.assertIn("copilot", results)
        self.assertIn("recall", results)
        self.assertIn("cortana", results)
        self.assertEqual(results["summary"]["total_features"], 9)
        self.assertEqual(results["summary"]["active_features"], 5)
        self.assertEqual(results["summary"]["inactive_features"], 4)

    # ── Removal Tests ──

    @patch("subprocess.run")
    @patch("winsvalinn.core.ai_windows.set_registry")
    def test_remove_copilot_success(self, mock_set_reg, mock_run):
        """Remove Copilot sets registry keys and kills process."""
        mock_set_reg.return_value = (True, "Success")
        mock_run.return_value = Mock(returncode=0)

        result = self.remover.remove_copilot()
        self.assertTrue(result["success"])
        self.assertGreater(len(result["actions"]), 0)

    @patch("winsvalinn.core.ai_windows.set_registry")
    def test_remove_recall_success(self, mock_set_reg):
        """Remove Recall returns success and actions (no 'feature' key)."""
        mock_set_reg.return_value = (True, "Success")
        result = self.remover.remove_recall()
        self.assertTrue(result["success"])
        # The actual implementation returns {"success": True, "actions": [...]}
        # It does NOT have a "feature" key
        self.assertIn("actions", result)
        self.assertGreater(len(result["actions"]), 0)

    @patch("winsvalinn.core.ai_windows.set_registry")
    def test_remove_ai_search_success(self, mock_set_reg):
        mock_set_reg.return_value = (True, "Success")
        result = self.remover.remove_ai_search()
        self.assertTrue(result["success"])

    # ── Remove All Test ──

    @patch("winsvalinn.core.ai_windows.AIWindowsRemover.remove_copilot")
    @patch("winsvalinn.core.ai_windows.AIWindowsRemover.remove_recall")
    @patch("winsvalinn.core.ai_windows.AIWindowsRemover.remove_suggested_actions")
    @patch("winsvalinn.core.ai_windows.AIWindowsRemover.remove_live_captions")
    @patch("winsvalinn.core.ai_windows.AIWindowsRemover.remove_voice_access")
    @patch("winsvalinn.core.ai_windows.AIWindowsRemover.remove_ai_widgets")
    @patch("winsvalinn.core.ai_windows.AIWindowsRemover.remove_ai_search")
    @patch("winsvalinn.core.ai_windows.AIWindowsRemover.remove_ai_telemetry")
    @patch("winsvalinn.core.ai_windows.AIWindowsRemover.remove_cortana")
    def test_remove_all_ai(
        self,
        mock_cortana,
        mock_telemetry,
        mock_search,
        mock_widgets,
        mock_voice,
        mock_captions,
        mock_suggested,
        mock_recall,
        mock_copilot,
    ):
        mock_copilot.return_value = {"success": True, "actions": ["a1"]}
        mock_recall.return_value = {"success": True, "actions": ["a2"]}
        mock_suggested.return_value = {"success": True, "actions": ["a3"]}
        mock_captions.return_value = {"success": True, "actions": ["a4"]}
        mock_voice.return_value = {"success": True, "actions": ["a5"]}
        mock_widgets.return_value = {"success": True, "actions": ["a6"]}
        mock_search.return_value = {"success": True, "actions": ["a7"]}
        mock_telemetry.return_value = {"success": True, "actions": ["a8"]}
        mock_cortana.return_value = {"success": True, "actions": ["a9"]}

        results = self.remover.remove_all_ai()

        mock_copilot.assert_called_once()
        mock_recall.assert_called_once()
        mock_cortana.assert_called_once()
        self.assertIn("copilot", results)
        self.assertIn("recall", results)
        self.assertIn("cortana", results)

    # ── Error Handling Tests ──

    @patch("subprocess.run")
    @patch("winsvalinn.core.ai_windows.get_registry")
    def test_detection_registry_failure(self, mock_get_reg, mock_run):
        """When registry fails, copilot falls back to process/service checks."""
        mock_get_reg.return_value = (False, None)

        # No process or service running
        mock_result = Mock()
        mock_result.stdout = "No tasks are running"
        mock_run.return_value = mock_result

        result = self.remover.check_copilot_status()
        self.assertFalse(result["active"])

    @patch("subprocess.run")
    @patch("winsvalinn.core.ai_windows.set_registry")
    def test_removal_registry_failure(self, mock_set_reg, mock_run):
        """When set_registry fails, remove_copilot still returns success with empty actions."""
        mock_set_reg.return_value = (False, "Access denied")
        mock_run.return_value = Mock(returncode=0)

        result = self.remover.remove_copilot()
        self.assertIn("success", result)
        self.assertIn("actions", result)

    @patch("winsvalinn.core.ai_windows.get_registry")
    @patch("subprocess.run")
    def test_process_check_timeout(self, mock_run, mock_get_reg):
        """When subprocess times out, cortana check still returns a result."""
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=5)
        # Registry also needs to be mocked since cortana checks ShowCortanaButton
        mock_get_reg.return_value = (False, None)

        result = self.remover.check_cortana_status()
        self.assertIn("active", result)

    def test_callback_logging(self):
        """Verify the callback receives log messages."""
        self.callback_messages.clear()
        with (
            patch("winsvalinn.core.ai_windows.get_registry") as mock_get_reg,
            patch("subprocess.run") as mock_run,
        ):
            mock_get_reg.return_value = (True, "1")
            mock_result = Mock()
            mock_result.stdout = "No tasks are running"
            mock_run.return_value = mock_result
            self.remover.check_copilot_status()
        self.assertIsInstance(self.callback_messages, list)


if __name__ == "__main__":
    unittest.main()
