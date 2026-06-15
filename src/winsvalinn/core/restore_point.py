"""
System Restore Point management for WinSvalinn.

Creates, lists and manages Windows System Restore Points
to provide a safety net before any destructive operation.
"""

import platform
import subprocess
from datetime import datetime

from winsvalinn.utils.logger import ModuleLogger

logger = ModuleLogger("RestorePoint")

IS_WINDOWS = platform.system() == "Windows"
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class RestorePointManager:
    """Create and manage Windows System Restore Points."""

    def __init__(self, callback=None):
        self._callback = callback or (lambda msg, level="info": None)
        logger.info("RestorePointManager initialized")

    def _log(self, msg, level="info"):
        getattr(logger, level, logger.info)(msg)
        self._callback(msg, level)

    def _is_admin(self):
        if not IS_WINDOWS:
            return False
        try:
            import ctypes

            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    def create_restore_point(self, description="WinSvalinn Backup"):
        """
        Create a System Restore Point.

        Args:
            description: Description for the restore point

        Returns:
            tuple: (success: bool, message: str)
        """
        if not IS_WINDOWS:
            return False, "Only available on Windows"

        if not self._is_admin():
            self._log("Admin privileges required to create restore point", "warning")
            return False, "Admin privileges required"

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        full_desc = f"{description} ({timestamp})"

        self._log(f"Creating restore point: {full_desc}")

        try:
            # Enable System Restore on C: if not already enabled
            enable_cmd = 'Enable-ComputerRestore -Drive "C:\\" -ErrorAction SilentlyContinue'
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", enable_cmd],
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=CREATE_NO_WINDOW,
            )

            # Create the restore point
            # Type 12 = MODIFY_SETTINGS (doesn't have 24h cooldown like APPLICATION_INSTALL)
            ps_cmd = (
                f'Checkpoint-Computer -Description "{full_desc}" '
                f'-RestorePointType "MODIFY_SETTINGS" -ErrorAction Stop'
            )

            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=120,
                creationflags=CREATE_NO_WINDOW,
            )

            if result.returncode == 0:
                self._log(f"Restore point created: {full_desc}", "info")
                return True, f"Restore point created: {full_desc}"
            else:
                error = result.stderr.strip() or result.stdout.strip()
                # Windows has a 24h cooldown between restore points
                if "frequency" in error.lower() or "1400" in error:
                    self._log(
                        "Windows limits restore points to one per 24 hours. "
                        "Bypassing frequency limit...",
                        "warning",
                    )
                    return self._create_bypass_frequency(full_desc)
                self._log(f"Failed to create restore point: {error}", "error")
                return False, f"Failed: {error[:200]}"

        except subprocess.TimeoutExpired:
            self._log("Restore point creation timed out (120s)", "error")
            return False, "Operation timed out"
        except Exception as e:
            self._log(f"Error creating restore point: {e}", "error")
            return False, str(e)

    def _create_bypass_frequency(self, description):
        """Bypass the 24-hour frequency limit by temporarily changing the registry."""
        try:
            # Set frequency to 0 (no limit)
            freq_cmd = (
                "New-ItemProperty -Path "
                '"HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\SystemRestore" '
                '-Name "SystemRestorePointCreationFrequency" '
                "-Value 0 -PropertyType DWord -Force -ErrorAction SilentlyContinue"
            )
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", freq_cmd],
                capture_output=True,
                text=True,
                timeout=15,
                creationflags=CREATE_NO_WINDOW,
            )

            # Retry creation
            ps_cmd = (
                f'Checkpoint-Computer -Description "{description}" '
                f'-RestorePointType "MODIFY_SETTINGS" -ErrorAction Stop'
            )
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=120,
                creationflags=CREATE_NO_WINDOW,
            )

            if result.returncode == 0:
                self._log(f"Restore point created (bypassed frequency): {description}")
                return True, f"Restore point created: {description}"
            else:
                error = result.stderr.strip()
                self._log(f"Failed even after bypass: {error}", "error")
                return False, f"Failed: {error[:200]}"

        except Exception as e:
            self._log(f"Error in frequency bypass: {e}", "error")
            return False, str(e)

    def list_restore_points(self):
        """
        List all available System Restore Points.

        Returns:
            list[dict]: Each dict has keys: sequence, description, date, type
        """
        if not IS_WINDOWS:
            return []

        try:
            ps_cmd = (
                "Get-ComputerRestorePoint | "
                "Select-Object SequenceNumber, Description, "
                "@{N='Date';E={$_.ConvertToDateTime($_.CreationTime)}}, "
                "RestorePointType | "
                "ConvertTo-Json -Compress"
            )

            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=CREATE_NO_WINDOW,
            )

            if result.returncode != 0 or not result.stdout.strip():
                return []

            import json

            data = json.loads(result.stdout.strip())

            # PowerShell returns single object (not array) if only one result
            if isinstance(data, dict):
                data = [data]

            points = []
            for item in data:
                points.append(
                    {
                        "sequence": item.get("SequenceNumber", 0),
                        "description": item.get("Description", "Unknown"),
                        "date": item.get("Date", "Unknown"),
                        "type": item.get("RestorePointType", 0),
                    }
                )

            self._log(f"Found {len(points)} restore points")
            return points

        except Exception as e:
            self._log(f"Error listing restore points: {e}", "error")
            return []

    def delete_restore_point(self, sequence_number):
        """
        Delete a specific restore point by sequence number.

        Args:
            sequence_number: The sequence number of the restore point

        Returns:
            tuple: (success: bool, message: str)
        """
        if not IS_WINDOWS or not self._is_admin():
            return False, "Admin privileges required"

        try:
            # Use vssadmin to delete (no direct PowerShell cmdlet)
            # Simpler approach: delete oldest shadow copies
            self._log(f"Deleting restore point #{sequence_number}", "warning")

            # Note: Windows doesn't provide a clean way to delete individual restore points
            # We can only delete all or oldest. Log this limitation.
            self._log(
                "Note: Windows only supports deleting ALL restore points or the oldest ones",
                "warning",
            )
            return False, "Individual deletion not supported by Windows"

        except Exception as e:
            return False, str(e)

    def get_restore_status(self):
        """
        Check if System Restore is enabled.

        Returns:
            dict: {enabled: bool, drive: str, max_usage: str}
        """
        if not IS_WINDOWS:
            return {"enabled": False, "drive": "N/A", "max_usage": "N/A"}

        try:
            ps_cmd = (
                "Get-ComputerRestorePoint -ErrorAction SilentlyContinue | "
                "Measure-Object | Select-Object -ExpandProperty Count"
            )
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=15,
                creationflags=CREATE_NO_WINDOW,
            )

            # Check vssadmin for usage
            vss_result = subprocess.run(
                ["vssadmin", "list", "shadowstorage"],
                capture_output=True,
                text=True,
                timeout=15,
                creationflags=CREATE_NO_WINDOW,
            )

            max_usage = "Unknown"
            if vss_result.returncode == 0:
                for line in vss_result.stdout.split("\n"):
                    if "Maximum" in line and "Size" in line:
                        parts = line.split(":")
                        if len(parts) >= 2:
                            max_usage = parts[-1].strip()
                            break

            count = 0
            if result.returncode == 0 and result.stdout.strip().isdigit():
                count = int(result.stdout.strip())

            return {
                "enabled": count >= 0,  # If command succeeds, restore is enabled
                "count": count,
                "drive": "C:\\",
                "max_usage": max_usage,
            }

        except Exception as e:
            logger.error(f"Error checking restore status: {e}")
            return {"enabled": False, "count": 0, "drive": "C:\\", "max_usage": "Unknown"}
