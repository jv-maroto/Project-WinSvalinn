"""
Backup Assistant for WinSvalinn (core engine, no GUI imports).

Backs up the bits of a Windows install that are painful to reconstruct after a
reinstall: third-party drivers, saved WiFi profiles, the installed-program
list, key registry hives, and a full systeminfo report. Backups land under
``~/.winsvalinn/backups``.

Logic migrated from the legacy ``plugin_backup`` filesystem plugin. All write
actions are destructive (they create files / read clear-text WiFi keys) except
``list_backups``, which is read-only.
"""

from __future__ import annotations

import json
import platform
import subprocess
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from winsvalinn.utils.logger import ModuleLogger

logger = ModuleLogger("BackupAssistant")

IS_WINDOWS = platform.system() == "Windows"
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

BACKUP_BASE = Path.home() / ".winsvalinn" / "backups"


class BackupAssistant:
    """Create and list backups of drivers, WiFi, programs, registry, sysinfo."""

    def __init__(self, callback: Callable[[str, str], None] | None = None) -> None:
        self._callback = callback or (lambda msg, level="info": None)

    def _log(self, msg: str, level: str = "info") -> None:
        getattr(logger, level, logger.info)(msg)
        self._callback(msg, level)

    @staticmethod
    def _timestamp() -> str:
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def _ensure_base(self) -> None:
        BACKUP_BASE.mkdir(parents=True, exist_ok=True)

    def backup_drivers(self) -> dict:
        """Export third-party drivers via DISM (requires admin)."""
        if not IS_WINDOWS:
            return {"success": False, "message": "Only available on Windows"}

        self._ensure_base()
        dest = BACKUP_BASE / f"drivers_{self._timestamp()}"
        dest.mkdir(parents=True, exist_ok=True)
        self._log("Backing up drivers (this may take a few minutes)...")

        try:
            result = subprocess.run(
                ["dism", "/online", "/export-driver", f"/destination:{dest}"],
                capture_output=True,
                text=True,
                timeout=300,
                creationflags=CREATE_NO_WINDOW,
            )
        except (subprocess.TimeoutExpired, OSError) as exc:
            self._log(f"Driver backup failed: {exc}", "error")
            return {"success": False, "message": str(exc)}

        if result.returncode == 0:
            count = sum(1 for f in dest.iterdir() if f.is_dir())
            self._log(f"Exported {count} driver packages to {dest}", "success")
            return {"success": True, "count": count, "path": str(dest)}
        self._log(
            f"Driver backup failed (need admin?): {result.stderr.strip()[:100]}",
            "error",
        )
        return {"success": False, "message": result.stderr.strip()[:200]}

    def backup_wifi(self) -> dict:
        """Export saved WiFi profiles (with clear-text keys)."""
        if not IS_WINDOWS:
            return {"success": False, "message": "Only available on Windows"}

        self._ensure_base()
        dest = BACKUP_BASE / f"wifi_{self._timestamp()}"
        dest.mkdir(parents=True, exist_ok=True)
        self._log("Backing up WiFi profiles...")

        try:
            subprocess.run(
                ["netsh", "wlan", "export", "profile", f"folder={dest}", "key=clear"],
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=CREATE_NO_WINDOW,
            )
        except (subprocess.TimeoutExpired, OSError) as exc:
            self._log(f"WiFi backup failed: {exc}", "error")
            return {"success": False, "message": str(exc)}

        count = len(list(dest.glob("*.xml")))
        self._log(f"Exported {count} WiFi profiles to {dest}", "success")
        return {"success": True, "count": count, "path": str(dest)}

    def backup_programs(self) -> dict:
        """Save the installed-program list as JSON (read of registry only)."""
        if not IS_WINDOWS:
            return {"success": False, "message": "Only available on Windows"}

        self._ensure_base()
        dest = BACKUP_BASE / f"programs_{self._timestamp()}.json"
        self._log("Saving installed programs list...")

        cmd = (
            "Get-ItemProperty "
            "HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*, "
            "HKLM:\\Software\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* "
            "-ErrorAction SilentlyContinue | "
            "Where-Object { $_.DisplayName -ne $null } | "
            "Select-Object DisplayName, DisplayVersion, Publisher, InstallDate "
            "| ConvertTo-Json -Compress"
        )

        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", cmd],
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=CREATE_NO_WINDOW,
            )
            if result.returncode != 0 or not result.stdout.strip():
                self._log("Could not retrieve program list", "error")
                return {"success": False, "message": "no program data"}

            programs = json.loads(result.stdout.strip())
            if isinstance(programs, dict):
                programs = [programs]

            dest.write_text(
                json.dumps(
                    {
                        "exported": datetime.now().isoformat(),
                        "count": len(programs),
                        "programs": programs,
                    },
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            self._log(f"Saved {len(programs)} programs to {dest}", "success")
            return {"success": True, "count": len(programs), "path": str(dest)}
        except (subprocess.TimeoutExpired, OSError, json.JSONDecodeError) as exc:
            self._log(f"Error: {exc}", "error")
            return {"success": False, "message": str(exc)}

    def backup_registry(self) -> dict:
        """Export key registry hives to .reg files."""
        if not IS_WINDOWS:
            return {"success": False, "message": "Only available on Windows"}

        self._ensure_base()
        dest = BACKUP_BASE / f"registry_{self._timestamp()}"
        dest.mkdir(parents=True, exist_ok=True)
        self._log("Backing up registry hives...")

        hives = {
            "HKCU_Software": r"HKCU\Software",
            "HKLM_Software": r"HKLM\SOFTWARE",
            "HKLM_System": r"HKLM\SYSTEM\CurrentControlSet",
        }
        exported = []
        for name, path in hives.items():
            reg_file = dest / f"{name}.reg"
            try:
                result = subprocess.run(
                    ["reg", "export", path, str(reg_file), "/y"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    creationflags=CREATE_NO_WINDOW,
                )
            except (subprocess.TimeoutExpired, OSError) as exc:
                self._log(f"  {name}: Error ({exc})", "error")
                continue

            if result.returncode == 0 and reg_file.exists():
                size_mb = reg_file.stat().st_size / (1024**2)
                self._log(f"  {name}: {size_mb:.1f} MB", "success")
                exported.append(name)
            else:
                self._log(f"  {name}: Failed", "warning")

        self._log(f"Registry backup saved to {dest}", "success")
        return {"success": bool(exported), "exported": exported, "path": str(dest)}

    def backup_sysinfo(self) -> dict:
        """Save a full systeminfo report to a text file."""
        if not IS_WINDOWS:
            return {"success": False, "message": "Only available on Windows"}

        self._ensure_base()
        dest = BACKUP_BASE / f"sysinfo_{self._timestamp()}.txt"
        self._log("Saving system information...")

        try:
            result = subprocess.run(
                ["systeminfo"],
                capture_output=True,
                text=True,
                timeout=60,
                creationflags=CREATE_NO_WINDOW,
            )
            header = (
                f"WinSvalinn System Info Backup\nDate: {datetime.now().isoformat()}\n{'=' * 60}\n\n"
            )
            dest.write_text(header + result.stdout, encoding="utf-8")
            self._log(f"System info saved to {dest}", "success")
            return {"success": True, "path": str(dest)}
        except (subprocess.TimeoutExpired, OSError) as exc:
            self._log(f"Error: {exc}", "error")
            return {"success": False, "message": str(exc)}

    def list_backups(self) -> dict:
        """List existing backups with sizes (read-only)."""
        self._log("Listing existing backups...")
        items = []
        total = 0

        if BACKUP_BASE.exists():
            for path in sorted(BACKUP_BASE.iterdir(), reverse=True):
                if path.is_dir():
                    size = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
                else:
                    size = path.stat().st_size
                total += size
                items.append({"name": path.name, "size_mb": round(size / (1024**2), 1)})

        self._log(f"{len(items)} backup(s), {total / (1024**2):.1f} MB at {BACKUP_BASE}")
        return {
            "backups": items,
            "count": len(items),
            "total_mb": round(total / (1024**2), 1),
            "location": str(BACKUP_BASE),
        }
