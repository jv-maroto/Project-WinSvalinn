"""
Boot Timeline Analyzer for WinSvalinn (core engine, no GUI imports).

Estimates boot phases from the Windows Event Log rather than bundling the
full ETW stack (xperf/WPA, ~150 MB + admin). It reads:

  * Microsoft-Windows-Diagnostics-Performance/Operational (IDs 100-103),
    which Windows logs as BootTime / MainPathBootTime / BootPostBootTime.
  * Service Control Manager events (7036) for service start/stop times
    during boot.

Logic migrated from the legacy ``plugin_boot_timeline`` filesystem plugin.
Read-only: it only queries the event log via PowerShell (shell=False).
"""

from __future__ import annotations

import json
import platform
import subprocess
from collections.abc import Callable

from winsvalinn.utils.logger import ModuleLogger

logger = ModuleLogger("BootTimeline")

IS_WINDOWS = platform.system() == "Windows"
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

_PS_QUERY_BOOT = r"""
$evts = Get-WinEvent -LogName 'Microsoft-Windows-Diagnostics-Performance/Operational' -MaxEvents 50 -ErrorAction SilentlyContinue |
    Where-Object { $_.Id -in 100,101,102,103 }
$out = @()
foreach ($e in $evts) {
    $out += [pscustomobject]@{
        Time   = $e.TimeCreated.ToString('o')
        Id     = $e.Id
        Level  = $e.LevelDisplayName
        Source = $e.ProviderName
        Msg    = ($e.Message -split "`n")[0]
    }
}
$out | Select-Object -First 20 | ConvertTo-Json -Compress
"""

_PS_QUERY_SERVICES = r"""
$evts = Get-WinEvent -LogName System -MaxEvents 200 -FilterHashtable @{ProviderName='Service Control Manager'; Id=7036} -ErrorAction SilentlyContinue
$out = @()
foreach ($e in $evts) {
    $msg = ($e.Message -split "`n")[0]
    $out += [pscustomobject]@{
        Time = $e.TimeCreated.ToString('o')
        Msg  = $msg
    }
}
$out | Select-Object -First 50 | ConvertTo-Json -Compress
"""


class BootTimelineAnalyzer:
    """Read the last boot timeline from the Windows Event Log."""

    def __init__(self, callback: Callable[[str, str], None] | None = None) -> None:
        self._callback = callback or (lambda msg, level="info": None)

    def _log(self, msg: str, level: str = "info") -> None:
        getattr(logger, level, logger.info)(msg)
        self._callback(msg, level)

    def _run_ps(self, script: str, timeout: int = 30) -> list[dict]:
        if not IS_WINDOWS:
            return []
        try:
            cp = subprocess.run(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-NonInteractive",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    script,
                ],
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=False,
                creationflags=CREATE_NO_WINDOW,
            )
            if cp.returncode != 0 or not cp.stdout.strip():
                return []
            data = json.loads(cp.stdout)
            if isinstance(data, dict):
                data = [data]
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, subprocess.TimeoutExpired, OSError, ValueError) as exc:
            logger.error(f"Boot timeline PS error: {exc}")
            return []

    def analyze_last_boot(self) -> dict:
        """
        Analyze the last boot via the event log.

        Returns:
            dict: {boot_events: list, service_events: list,
                   boot_event_count: int, service_event_count: int}
        """
        if not IS_WINDOWS:
            self._log("Boot timeline is only available on Windows", "warning")
            return {
                "boot_events": [],
                "service_events": [],
                "boot_event_count": 0,
                "service_event_count": 0,
            }

        self._log("Analyzing last boot from the event log...")
        boot_events = self._run_ps(_PS_QUERY_BOOT)
        service_events = self._run_ps(_PS_QUERY_SERVICES)

        self._log(f"Boot events: {len(boot_events)} | service events: {len(service_events)}")
        return {
            "boot_events": boot_events,
            "service_events": service_events,
            "boot_event_count": len(boot_events),
            "service_event_count": len(service_events),
        }
