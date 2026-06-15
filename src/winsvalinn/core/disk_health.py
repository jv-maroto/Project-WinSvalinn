"""
Disk Health Monitor for WinSvalinn.

Reads S.M.A.R.T. data, disk details, temperature, and error status
using PowerShell and WMI queries. No GUI imports.
"""

import json
import platform
import subprocess

from winsvalinn.utils.logger import ModuleLogger

logger = ModuleLogger("DiskHealth")

IS_WINDOWS = platform.system() == "Windows"
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class DiskHealthMonitor:
    """Monitor disk health via S.M.A.R.T., WMI, and system commands."""

    def __init__(self, callback=None):
        self._callback = callback or (lambda msg, level="info": None)

    def _log(self, msg, level="info"):
        getattr(logger, level, logger.info)(msg)
        self._callback(msg, level)

    def _run_ps(self, cmd, timeout=30):
        """Run a PowerShell command and return stdout."""
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", cmd],
                capture_output=True,
                text=True,
                timeout=timeout,
                creationflags=CREATE_NO_WINDOW,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return ""
        except Exception as e:
            logger.error(f"PowerShell error: {e}")
            return ""

    def get_disk_list(self):
        """
        List all physical disks with basic info.

        Returns:
            list[dict]: Each dict has model, serial, size_gb, media_type, bus_type, status
        """
        if not IS_WINDOWS:
            return []

        cmd = (
            "Get-PhysicalDisk | Select-Object "
            "DeviceId, FriendlyName, SerialNumber, "
            "@{N='SizeGB';E={[math]::Round($_.Size/1GB,1)}}, "
            "MediaType, BusType, HealthStatus, OperationalStatus "
            "| ConvertTo-Json -Compress"
        )
        output = self._run_ps(cmd)
        if not output:
            return []

        try:
            data = json.loads(output)
            if isinstance(data, dict):
                data = [data]

            disks = []
            for d in data:
                disks.append(
                    {
                        "id": d.get("DeviceId", "?"),
                        "model": d.get("FriendlyName", "Unknown"),
                        "serial": d.get("SerialNumber", "N/A"),
                        "size_gb": d.get("SizeGB", 0),
                        "media_type": d.get("MediaType", "Unknown"),
                        "bus_type": d.get("BusType", "Unknown"),
                        "health": d.get("HealthStatus", "Unknown"),
                        "status": d.get("OperationalStatus", "Unknown"),
                    }
                )

            self._log(f"Found {len(disks)} physical disk(s)")
            return disks
        except (json.JSONDecodeError, TypeError):
            return []

    def get_smart_status(self):
        """
        Get S.M.A.R.T. reliability counters for all disks.

        Returns:
            list[dict]: Per-disk reliability data
        """
        if not IS_WINDOWS:
            return []

        cmd = (
            "Get-PhysicalDisk | Get-StorageReliabilityCounter | "
            "Select-Object DeviceId, Temperature, Wear, "
            "ReadErrorsTotal, ReadErrorsCorrected, ReadErrorsUncorrected, "
            "WriteErrorsTotal, WriteErrorsCorrected, WriteErrorsUncorrected, "
            "PowerOnHours, StartStopCycleCount "
            "| ConvertTo-Json -Compress"
        )
        output = self._run_ps(cmd, timeout=30)
        if not output:
            return []

        try:
            data = json.loads(output)
            if isinstance(data, dict):
                data = [data]

            results = []
            for d in data:
                temp = d.get("Temperature")
                wear = d.get("Wear")
                power_hours = d.get("PowerOnHours")
                read_errors = d.get("ReadErrorsTotal", 0) or 0
                write_errors = d.get("WriteErrorsTotal", 0) or 0

                # Health assessment
                health = "Good"
                if wear is not None and wear > 80:
                    health = "Critical"
                elif wear is not None and wear > 50 or read_errors > 100 or write_errors > 100:
                    health = "Warning"
                elif read_errors > 1000 or write_errors > 1000:
                    health = "Critical"

                if temp is not None and temp > 60:
                    health = "Critical"
                elif temp is not None and temp > 50:
                    if health == "Good":
                        health = "Warning"

                results.append(
                    {
                        "device_id": d.get("DeviceId", "?"),
                        "temperature_c": temp,
                        "wear_percent": wear,
                        "power_on_hours": power_hours,
                        "start_stop_cycles": d.get("StartStopCycleCount"),
                        "read_errors_total": read_errors,
                        "read_errors_corrected": d.get("ReadErrorsCorrected", 0) or 0,
                        "read_errors_uncorrected": d.get("ReadErrorsUncorrected", 0) or 0,
                        "write_errors_total": write_errors,
                        "write_errors_corrected": d.get("WriteErrorsCorrected", 0) or 0,
                        "write_errors_uncorrected": d.get("WriteErrorsUncorrected", 0) or 0,
                        "health_assessment": health,
                    }
                )

            return results
        except (json.JSONDecodeError, TypeError):
            return []

    def get_disk_temperature(self):
        """
        Get temperature for all physical disks.

        Returns:
            list[dict]: [{device_id, model, temperature_c, status}]
        """
        disks = self.get_disk_list()
        smart = self.get_smart_status()

        # Map smart data by device_id
        smart_map = {str(s["device_id"]): s for s in smart}

        results = []
        for disk in disks:
            did = str(disk["id"])
            temp = None
            status = "Unknown"

            if did in smart_map:
                temp = smart_map[did].get("temperature_c")

            if temp is not None:
                if temp > 60:
                    status = "Critical"
                elif temp > 50:
                    status = "Warning"
                elif temp > 0:
                    status = "Normal"

            results.append(
                {
                    "device_id": did,
                    "model": disk["model"],
                    "temperature_c": temp,
                    "status": status,
                }
            )

        return results

    def check_disk_errors(self, drive="C"):
        """
        Run a read-only disk error check via chkdsk.

        Args:
            drive: Drive letter (without colon)

        Returns:
            dict: {clean: bool, output: str, errors_found: bool}
        """
        if not IS_WINDOWS:
            return {"clean": True, "output": "Not Windows", "errors_found": False}

        self._log(f"Checking disk errors on {drive}:")

        try:
            # chkdsk /scan is read-only on NTFS (Windows 8+)
            result = subprocess.run(
                ["chkdsk", f"{drive}:", "/scan"],
                capture_output=True,
                text=True,
                timeout=300,
                creationflags=CREATE_NO_WINDOW,
            )

            output = result.stdout.strip()
            errors_found = (
                "found" in output.lower()
                and "error" in output.lower()
                and "0 errors" not in output.lower()
            )

            return {
                "clean": not errors_found,
                "output": output[-2000:] if len(output) > 2000 else output,
                "errors_found": errors_found,
            }
        except subprocess.TimeoutExpired:
            return {"clean": False, "output": "Scan timed out (5 min)", "errors_found": False}
        except Exception as e:
            return {"clean": False, "output": str(e), "errors_found": False}

    def get_partition_info(self):
        """
        Get logical partition details with usage.

        Returns:
            list[dict]: Per-partition data
        """
        if not IS_WINDOWS:
            return []

        try:
            import psutil

            partitions = []
            for part in psutil.disk_partitions(all=False):
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    partitions.append(
                        {
                            "device": part.device,
                            "mountpoint": part.mountpoint,
                            "fstype": part.fstype,
                            "total_gb": round(usage.total / (1024**3), 1),
                            "used_gb": round(usage.used / (1024**3), 1),
                            "free_gb": round(usage.free / (1024**3), 1),
                            "percent": usage.percent,
                        }
                    )
                except (PermissionError, OSError):
                    pass
            return partitions
        except ImportError:
            return []

    def predict_health(self):
        """
        Aggregate health prediction across all disks.

        Returns:
            dict: {overall: str, disks: list[dict], warnings: list[str]}
        """
        disks = self.get_disk_list()
        smart = self.get_smart_status()
        smart_map = {str(s["device_id"]): s for s in smart}

        warnings = []
        disk_reports = []
        overall = "Healthy"

        for disk in disks:
            did = str(disk["id"])
            report = {
                "model": disk["model"],
                "size_gb": disk["size_gb"],
                "type": disk["media_type"],
                "health": disk["health"],
            }

            if disk["health"] != "Healthy":
                overall = "Warning"
                warnings.append(f"Disk {disk['model']}: status is {disk['health']}")

            if did in smart_map:
                s = smart_map[did]
                report["temperature_c"] = s.get("temperature_c")
                report["wear_percent"] = s.get("wear_percent")
                report["power_on_hours"] = s.get("power_on_hours")
                report["smart_health"] = s.get("health_assessment", "Unknown")

                if s.get("health_assessment") == "Critical":
                    overall = "Critical"
                    warnings.append(f"Disk {disk['model']}: S.M.A.R.T. reports CRITICAL")
                elif s.get("health_assessment") == "Warning" and overall != "Critical":
                    overall = "Warning"
                    warnings.append(f"Disk {disk['model']}: S.M.A.R.T. reports WARNING")

                temp = s.get("temperature_c")
                if temp and temp > 55:
                    warnings.append(f"Disk {disk['model']}: temperature {temp}°C")

                hours = s.get("power_on_hours")
                if hours and hours > 40000:
                    warnings.append(f"Disk {disk['model']}: {hours} power-on hours (aging)")

            disk_reports.append(report)

        self._log(f"Disk health: {overall} ({len(warnings)} warning(s))")
        return {
            "overall": overall,
            "disks": disk_reports,
            "warnings": warnings,
        }
