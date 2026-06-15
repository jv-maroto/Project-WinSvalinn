"""
Driver Manager for WinSvalinn.

Lists, audits, and backs up Windows drivers. Detects unsigned,
outdated, and problematic drivers. No automatic installation.
"""

import json
import os
import platform
import subprocess
from datetime import datetime

from winsvalinn.utils.logger import ModuleLogger

logger = ModuleLogger("DriverManager")

IS_WINDOWS = platform.system() == "Windows"
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class DriverManager:
    """Audit and manage Windows drivers."""

    def __init__(self, callback=None):
        self._callback = callback or (lambda msg, level="info": None)

    def _log(self, msg, level="info"):
        getattr(logger, level, logger.info)(msg)
        self._callback(msg, level)

    def _run_ps(self, cmd, timeout=30):
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", cmd],
                capture_output=True,
                text=True,
                timeout=timeout,
                creationflags=CREATE_NO_WINDOW,
            )
            return result.stdout.strip() if result.returncode == 0 else ""
        except Exception as e:
            logger.error(f"PS error: {e}")
            return ""

    def list_all_drivers(self):
        """
        List all installed drivers with details.

        Returns:
            list[dict]: Driver entries
        """
        if not IS_WINDOWS:
            return []

        self._log("Listing all drivers...")

        cmd = (
            "Get-CimInstance Win32_PnPSignedDriver | "
            "Where-Object { $_.DeviceName -ne $null } | "
            "Select-Object DeviceName, DriverVersion, DriverDate, "
            "Manufacturer, DeviceClass, IsSigned, InfName, "
            "DriverProviderName "
            "| ConvertTo-Json -Compress"
        )
        output = self._run_ps(cmd, timeout=30)
        if not output:
            return []

        try:
            data = json.loads(output)
            if isinstance(data, dict):
                data = [data]

            drivers = []
            for d in data:
                driver_date = d.get("DriverDate", "")
                if driver_date and "/Date(" in str(driver_date):
                    try:
                        ts = int(str(driver_date).split("(")[1].split(")")[0][:10])
                        driver_date = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
                    except Exception:
                        driver_date = str(driver_date)

                drivers.append(
                    {
                        "name": d.get("DeviceName", "Unknown"),
                        "version": d.get("DriverVersion", "N/A"),
                        "date": driver_date,
                        "manufacturer": d.get("Manufacturer", "Unknown"),
                        "class": d.get("DeviceClass", "Unknown"),
                        "signed": d.get("IsSigned", False),
                        "inf": d.get("InfName", ""),
                        "provider": d.get("DriverProviderName", ""),
                    }
                )

            self._log(f"Found {len(drivers)} drivers")
            return drivers
        except (json.JSONDecodeError, TypeError):
            return []

    def get_unsigned_drivers(self):
        """
        Get drivers that are not digitally signed (security risk).

        Returns:
            list[dict]: Unsigned driver entries
        """
        self._log("Checking for unsigned drivers...")
        all_drivers = self.list_all_drivers()
        unsigned = [d for d in all_drivers if not d.get("signed", True)]
        self._log(f"Found {len(unsigned)} unsigned drivers", "warning" if unsigned else "info")
        return unsigned

    def get_problematic_drivers(self):
        """
        Get drivers with errors (ConfigManagerErrorCode != 0).

        Returns:
            list[dict]: Problematic devices with error codes
        """
        if not IS_WINDOWS:
            return []

        self._log("Checking for problematic drivers...")

        cmd = (
            "Get-CimInstance Win32_PnPEntity | "
            "Where-Object { $_.ConfigManagerErrorCode -ne 0 } | "
            "Select-Object Name, DeviceID, ConfigManagerErrorCode, "
            "Status, Manufacturer "
            "| ConvertTo-Json -Compress"
        )
        output = self._run_ps(cmd)
        if not output:
            self._log("No problematic drivers found")
            return []

        try:
            data = json.loads(output)
            if isinstance(data, dict):
                data = [data]

            error_map = {
                1: "Not configured correctly",
                3: "Driver corrupted",
                10: "Device cannot start",
                12: "Not enough free resources",
                14: "Requires restart",
                18: "Reinstall drivers",
                22: "Device disabled",
                24: "Device not present",
                28: "Drivers not installed",
                31: "Device not working properly",
                43: "Windows stopped this device (error reported)",
            }

            problems = []
            for d in data:
                code = d.get("ConfigManagerErrorCode", 0)
                problems.append(
                    {
                        "name": d.get("Name", "Unknown"),
                        "device_id": d.get("DeviceID", ""),
                        "error_code": code,
                        "error_desc": error_map.get(code, f"Error code {code}"),
                        "status": d.get("Status", "Unknown"),
                        "manufacturer": d.get("Manufacturer", "Unknown"),
                    }
                )

            self._log(f"Found {len(problems)} problematic devices", "warning")
            return problems
        except (json.JSONDecodeError, TypeError):
            return []

    def get_outdated_drivers(self, days_old=365):
        """
        Get drivers older than a specified number of days.

        Args:
            days_old: Threshold in days

        Returns:
            list[dict]: Outdated driver entries
        """
        self._log(f"Checking for drivers older than {days_old} days...")
        all_drivers = self.list_all_drivers()
        cutoff = datetime.now()

        outdated = []
        for d in all_drivers:
            try:
                date_str = d.get("date", "")
                if not date_str or date_str == "N/A":
                    continue
                driver_date = datetime.strptime(date_str[:10], "%Y-%m-%d")
                age_days = (cutoff - driver_date).days
                if age_days > days_old:
                    d["age_days"] = age_days
                    outdated.append(d)
            except (ValueError, TypeError):
                continue

        outdated.sort(key=lambda x: x.get("age_days", 0), reverse=True)
        self._log(f"Found {len(outdated)} drivers older than {days_old} days")
        return outdated

    def backup_drivers(self, destination=None):
        """
        Export all third-party drivers to a folder.

        Args:
            destination: Target directory (default: ~/.winsvalinn/driver_backup/)

        Returns:
            tuple: (success: bool, message: str)
        """
        if not IS_WINDOWS:
            return False, "Only available on Windows"

        if destination is None:
            destination = os.path.join(
                os.path.expanduser("~"),
                ".winsvalinn",
                "driver_backup",
                datetime.now().strftime("%Y%m%d_%H%M%S"),
            )

        os.makedirs(destination, exist_ok=True)
        self._log(f"Backing up drivers to {destination}...")

        try:
            result = subprocess.run(
                ["dism", "/online", "/export-driver", f"/destination:{destination}"],
                capture_output=True,
                text=True,
                timeout=300,
                creationflags=CREATE_NO_WINDOW,
            )

            if result.returncode == 0:
                # Count exported drivers
                count = sum(
                    1
                    for f in os.listdir(destination)
                    if os.path.isdir(os.path.join(destination, f))
                )
                msg = f"Exported {count} driver packages to {destination}"
                self._log(msg)
                return True, msg
            else:
                error = result.stderr.strip() or result.stdout.strip()
                self._log(f"Driver backup failed: {error}", "error")
                return False, error[:200]

        except subprocess.TimeoutExpired:
            return False, "Driver backup timed out (5 min)"
        except Exception as e:
            return False, str(e)

    def get_driver_summary(self, all_drivers=None):
        """
        Quick summary of driver health.
        Accepts pre-fetched all_drivers to avoid redundant WMI calls.
        """
        if all_drivers is None:
            all_drivers = self.list_all_drivers()
        unsigned = [d for d in all_drivers if not d.get("signed", True)]
        problematic = self.get_problematic_drivers()

        # Filter outdated from already-fetched list (no extra WMI call)
        cutoff = datetime.now()
        outdated = []
        for d in all_drivers:
            try:
                date_str = d.get("date", "")
                if not date_str or date_str == "N/A":
                    continue
                driver_date = datetime.strptime(date_str[:10], "%Y-%m-%d")
                if (cutoff - driver_date).days > 730:
                    outdated.append(d)
            except (ValueError, TypeError):
                continue

        health = "Good"
        if len(problematic) > 0:
            health = "Warning"
        if len(unsigned) > 3:
            health = "Warning"
        if len(problematic) > 3:
            health = "Critical"

        return {
            "total": len(all_drivers),
            "unsigned": len(unsigned),
            "unsigned_list": unsigned,
            "problematic": len(problematic),
            "problematic_list": problematic,
            "outdated": len(outdated),
            "outdated_list": outdated,
            "health": health,
        }
