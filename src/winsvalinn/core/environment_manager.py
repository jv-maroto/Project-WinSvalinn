"""
Environment & PATH Manager for WinSvalinn.

Manages system/user PATH, detects invalid/duplicate entries,
and lists environment variables.
"""

import os
import platform
import subprocess

from winsvalinn.utils.logger import ModuleLogger

logger = ModuleLogger("EnvManager")

IS_WINDOWS = platform.system() == "Windows"
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class EnvironmentManager:
    """Manage environment variables and PATH."""

    def __init__(self, callback=None):
        self._callback = callback or (lambda msg, level="info": None)

    def _log(self, msg, level="info"):
        getattr(logger, level, logger.info)(msg)
        self._callback(msg, level)

    def _run_ps(self, cmd, timeout=15):
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", cmd],
                capture_output=True,
                text=True,
                timeout=timeout,
                creationflags=CREATE_NO_WINDOW,
            )
            return result.stdout.strip() if result.returncode == 0 else ""
        except Exception:
            return ""

    def get_system_path(self):
        """Get system-level PATH entries."""
        if not IS_WINDOWS:
            return []

        cmd = (
            "[Environment]::GetEnvironmentVariable('Path', 'Machine') -split ';' | "
            "Where-Object { $_ -ne '' }"
        )
        output = self._run_ps(cmd)
        return [p.strip() for p in output.split("\n") if p.strip()]

    def get_user_path(self):
        """Get user-level PATH entries."""
        if not IS_WINDOWS:
            return []

        cmd = (
            "[Environment]::GetEnvironmentVariable('Path', 'User') -split ';' | "
            "Where-Object { $_ -ne '' }"
        )
        output = self._run_ps(cmd)
        return [p.strip() for p in output.split("\n") if p.strip()]

    def detect_invalid_paths(self):
        """
        Find PATH entries pointing to non-existent directories.

        Returns:
            dict: {system: list, user: list, total: int}
        """
        self._log("Checking for invalid PATH entries...")

        sys_path = self.get_system_path()
        usr_path = self.get_user_path()

        sys_invalid = [p for p in sys_path if not os.path.exists(p)]
        usr_invalid = [p for p in usr_path if not os.path.exists(p)]

        total = len(sys_invalid) + len(usr_invalid)
        if total > 0:
            self._log(f"Found {total} invalid PATH entries", "warning")

        return {
            "system": sys_invalid,
            "user": usr_invalid,
            "total": total,
        }

    def detect_duplicate_paths(self):
        """
        Find duplicate entries in PATH.

        Returns:
            dict: {system: list, user: list, total: int}
        """
        self._log("Checking for duplicate PATH entries...")

        def find_dupes(entries):
            seen = set()
            dupes = []
            for p in entries:
                normalized = p.lower().rstrip("\\")
                if normalized in seen:
                    dupes.append(p)
                else:
                    seen.add(normalized)
            return dupes

        sys_dupes = find_dupes(self.get_system_path())
        usr_dupes = find_dupes(self.get_user_path())

        return {
            "system": sys_dupes,
            "user": usr_dupes,
            "total": len(sys_dupes) + len(usr_dupes),
        }

    def get_all_env_vars(self):
        """
        Get all environment variables.

        Returns:
            dict: {name: value}
        """
        return dict(os.environ)

    def get_temp_dirs(self):
        """Get TEMP/TMP directories with sizes."""
        dirs = {}
        for var in ["TEMP", "TMP"]:
            path = os.environ.get(var, "")
            if path and os.path.exists(path):
                total_size = 0
                file_count = 0
                try:
                    for dirpath, _, filenames in os.walk(path):
                        for f in filenames:
                            try:
                                total_size += os.path.getsize(os.path.join(dirpath, f))
                                file_count += 1
                            except (OSError, PermissionError):
                                pass
                except (OSError, PermissionError):
                    pass

                dirs[var] = {
                    "path": path,
                    "size_mb": round(total_size / (1024**2), 1),
                    "files": file_count,
                }

        return dirs

    def get_summary(self):
        """Environment health summary."""
        invalid = self.detect_invalid_paths()
        dupes = self.detect_duplicate_paths()
        temps = self.get_temp_dirs()
        sys_path = self.get_system_path()
        usr_path = self.get_user_path()

        health = "Good"
        if invalid["total"] > 5:
            health = "Warning"
        if invalid["total"] > 15:
            health = "Critical"

        total_temp_mb = sum(t.get("size_mb", 0) for t in temps.values())

        return {
            "system_path_entries": len(sys_path),
            "user_path_entries": len(usr_path),
            "invalid_entries": invalid["total"],
            "duplicate_entries": dupes["total"],
            "temp_size_mb": total_temp_mb,
            "health": health,
        }
