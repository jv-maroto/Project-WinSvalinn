"""Shared test fixtures for WinSvalinn tests."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_psutil():
    """Mock psutil for tests that don't need real system data."""
    with (
        patch("psutil.virtual_memory") as mock_vm,
        patch("psutil.cpu_percent") as mock_cpu,
        patch("psutil.disk_usage") as mock_disk,
    ):
        mock_vm.return_value = MagicMock(
            total=16 * 1024**3,
            available=8 * 1024**3,
            percent=50.0,
            used=8 * 1024**3,
        )
        mock_cpu.return_value = 25.0
        mock_disk.return_value = MagicMock(
            total=500 * 1024**3,
            used=250 * 1024**3,
            free=250 * 1024**3,
            percent=50.0,
        )
        yield {
            "virtual_memory": mock_vm,
            "cpu_percent": mock_cpu,
            "disk_usage": mock_disk,
        }


@pytest.fixture
def mock_subprocess():
    """Mock subprocess for tests that don't need real command execution."""
    with patch("subprocess.run") as mock_run, patch("subprocess.Popen") as mock_popen:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr="",
        )
        yield {
            "run": mock_run,
            "popen": mock_popen,
        }


@pytest.fixture
def mock_windows():
    """Mock platform to simulate Windows environment."""
    with patch("platform.system", return_value="Windows"):
        yield
