"""
smartmontools (smartctl) wrapper for WinSvalinn (core engine, no GUI imports).

Reads advanced S.M.A.R.T. attributes via the external ``smartctl`` binary
(smartmontools), which exposes far more detail than Windows' built-in storage
reliability counters. Falls back gracefully when smartmontools is not
installed.

Logic migrated from the legacy ``plugin_smartctl`` filesystem plugin.
``read_smart_info`` is read-only. ``start_short_self_test`` instructs the
drive firmware to begin a background self-test, which changes device state, so
callers should treat it as destructive.
"""

from __future__ import annotations

import platform
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

from winsvalinn.utils.logger import ModuleLogger

logger = ModuleLogger("SmartCtl")

IS_WINDOWS = platform.system() == "Windows"
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

_CANDIDATES = (
    r"C:\Program Files\smartmontools\bin\smartctl.exe",
    r"C:\Program Files (x86)\smartmontools\bin\smartctl.exe",
)


def find_smartctl() -> str | None:
    """Locate the smartctl binary on PATH or in known install dirs."""
    found = shutil.which("smartctl")
    if found:
        return found
    for candidate in _CANDIDATES:
        if Path(candidate).is_file():
            return candidate
    return None


class SmartCtlRunner:
    """Run smartctl to read SMART data and launch self-tests."""

    def __init__(self, callback: Callable[[str, str], None] | None = None) -> None:
        self._callback = callback or (lambda msg, level="info": None)
        self._smartctl = find_smartctl()

    def _log(self, msg: str, level: str = "info") -> None:
        getattr(logger, level, logger.info)(msg)
        self._callback(msg, level)

    @property
    def available(self) -> bool:
        """Whether the smartctl binary was found."""
        return self._smartctl is not None

    def scan_devices(self) -> list[str]:
        """
        List SMART-capable device paths via ``smartctl --scan``.

        Returns:
            list[str]: device paths (e.g. /dev/sda)
        """
        if not self._smartctl:
            return []
        try:
            cp = subprocess.run(
                [self._smartctl, "--scan"],
                capture_output=True,
                text=True,
                timeout=10,
                shell=False,
                creationflags=CREATE_NO_WINDOW,
            )
        except (subprocess.TimeoutExpired, OSError) as exc:
            self._log(f"smartctl scan failed: {exc}", "error")
            return []

        devices = []
        for line in cp.stdout.splitlines():
            parts = line.strip().split()
            if parts and parts[0].startswith(("/dev/", "\\\\")):
                devices.append(parts[0])
        return devices

    def read_smart_info(self, device: str | None = None) -> dict:
        """
        Read all SMART attributes for a device (read-only).

        Args:
            device: device path; defaults to the first scanned device.

        Returns:
            dict: {success, device, output, available}
        """
        if not self._smartctl:
            self._log(
                "smartctl not found. Install smartmontools (winget install smartmontools).",
                "warning",
            )
            return {"success": False, "device": device, "output": "", "available": False}

        if not device:
            devices = self.scan_devices()
            device = devices[0] if devices else "/dev/sda"

        self._log(f"Reading SMART info for {device}...")
        try:
            cp = subprocess.run(
                [self._smartctl, "-a", device],
                capture_output=True,
                text=True,
                timeout=30,
                shell=False,
                creationflags=CREATE_NO_WINDOW,
            )
            output = cp.stdout or cp.stderr
            return {
                "success": cp.returncode == 0,
                "device": device,
                "output": output,
                "available": True,
            }
        except (subprocess.TimeoutExpired, OSError) as exc:
            self._log(f"smartctl error: {exc}", "error")
            return {"success": False, "device": device, "output": str(exc), "available": True}

    def start_short_self_test(self, device: str | None = None) -> dict:
        """
        Start a short SMART self-test on a device (changes device state).

        Args:
            device: device path; defaults to the first scanned device.

        Returns:
            dict: {success, device, output, available}
        """
        if not self._smartctl:
            self._log(
                "smartctl not found. Install smartmontools (winget install smartmontools).",
                "warning",
            )
            return {"success": False, "device": device, "output": "", "available": False}

        if not device:
            devices = self.scan_devices()
            device = devices[0] if devices else "/dev/sda"

        self._log(f"Starting short self-test on {device}...", "warning")
        try:
            cp = subprocess.run(
                [self._smartctl, "-t", "short", device],
                capture_output=True,
                text=True,
                timeout=20,
                shell=False,
                creationflags=CREATE_NO_WINDOW,
            )
            output = cp.stdout or cp.stderr
            return {
                "success": cp.returncode == 0,
                "device": device,
                "output": output,
                "available": True,
            }
        except (subprocess.TimeoutExpired, OSError) as exc:
            self._log(f"smartctl error: {exc}", "error")
            return {"success": False, "device": device, "output": str(exc), "available": True}
