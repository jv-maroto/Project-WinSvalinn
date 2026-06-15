"""
Thermal & Performance Monitor for WinSvalinn.

Reads CPU/GPU temperatures, detects thermal throttling,
and reports performance counters.
"""

import json
import platform
import subprocess

from winsvalinn.utils.logger import ModuleLogger

logger = ModuleLogger("ThermalMonitor")

IS_WINDOWS = platform.system() == "Windows"
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class ThermalMonitor:
    """Monitor system temperatures and performance counters."""

    def __init__(self, callback=None):
        self._callback = callback or (lambda msg, level="info": None)

    def _log(self, msg, level="info"):
        getattr(logger, level, logger.info)(msg)
        self._callback(msg, level)

    def _run_ps(self, cmd, timeout=20):
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

    def get_cpu_temperature(self):
        """
        Get CPU temperature via WMI thermal zones.

        Returns:
            dict: {temperature_c: float or None, source: str, status: str}
        """
        if not IS_WINDOWS:
            return {"temperature_c": None, "source": "N/A", "status": "Unknown"}

        # Try MSAcpi_ThermalZoneTemperature first (requires admin)
        cmd = (
            "Get-CimInstance -Namespace root/WMI -ClassName MSAcpi_ThermalZoneTemperature "
            "-ErrorAction SilentlyContinue | "
            "Select-Object CurrentTemperature, InstanceName "
            "| ConvertTo-Json -Compress"
        )
        output = self._run_ps(cmd)

        if output:
            try:
                data = json.loads(output)
                if isinstance(data, dict):
                    data = [data]

                # Temperature is in tenths of Kelvin
                temps = []
                for d in data:
                    raw = d.get("CurrentTemperature", 0)
                    if raw and raw > 0:
                        celsius = (raw / 10.0) - 273.15
                        if 0 < celsius < 120:  # Sanity check
                            temps.append(celsius)

                if temps:
                    avg_temp = round(sum(temps) / len(temps), 1)
                    status = "Normal"
                    if avg_temp > 90:
                        status = "Critical"
                    elif avg_temp > 75:
                        status = "Warning"
                    elif avg_temp > 60:
                        status = "Warm"

                    return {
                        "temperature_c": avg_temp,
                        "source": "WMI ThermalZone",
                        "status": status,
                        "zones": len(temps),
                    }
            except (json.JSONDecodeError, TypeError):
                pass

        # Fallback: try performance counters
        cmd2 = (
            "Get-Counter '\\Thermal Zone Information(*)\\Temperature' "
            "-ErrorAction SilentlyContinue | "
            "Select-Object -ExpandProperty CounterSamples | "
            "Select-Object Path, CookedValue | ConvertTo-Json -Compress"
        )
        output2 = self._run_ps(cmd2)
        if output2:
            try:
                data = json.loads(output2)
                if isinstance(data, dict):
                    data = [data]

                temps = []
                for d in data:
                    kelvin = d.get("CookedValue", 0)
                    if kelvin > 200:  # Kelvin values
                        celsius = round(kelvin - 273.15, 1)
                        if 0 < celsius < 120:
                            temps.append(celsius)

                if temps:
                    avg_temp = round(sum(temps) / len(temps), 1)
                    status = "Normal"
                    if avg_temp > 90:
                        status = "Critical"
                    elif avg_temp > 75:
                        status = "Warning"

                    return {
                        "temperature_c": avg_temp,
                        "source": "Performance Counter",
                        "status": status,
                    }
            except (json.JSONDecodeError, TypeError):
                pass

        return {"temperature_c": None, "source": "Unavailable", "status": "Unknown"}

    def get_gpu_temperature(self):
        """
        Get GPU temperature via nvidia-smi or WMI.

        Returns:
            dict: {temperature_c: float or None, gpu_name: str, source: str, status: str}
        """
        if not IS_WINDOWS:
            return {"temperature_c": None, "gpu_name": "N/A", "source": "N/A", "status": "Unknown"}

        # Try nvidia-smi first
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=temperature.gpu,name", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=CREATE_NO_WINDOW,
            )
            if result.returncode == 0 and result.stdout.strip():
                parts = result.stdout.strip().split(",")
                if len(parts) >= 2:
                    temp = float(parts[0].strip())
                    name = parts[1].strip()
                    status = "Normal"
                    if temp > 90:
                        status = "Critical"
                    elif temp > 80:
                        status = "Warning"
                    elif temp > 70:
                        status = "Warm"

                    return {
                        "temperature_c": temp,
                        "gpu_name": name,
                        "source": "nvidia-smi",
                        "status": status,
                    }
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
            pass

        # Fallback: try Win32_VideoController for basic info (no temp)
        cmd = (
            "Get-CimInstance Win32_VideoController | "
            "Select-Object Name, Status | ConvertTo-Json -Compress"
        )
        output = self._run_ps(cmd)
        if output:
            try:
                data = json.loads(output)
                if isinstance(data, dict):
                    data = [data]
                if data:
                    return {
                        "temperature_c": None,
                        "gpu_name": data[0].get("Name", "Unknown"),
                        "source": "WMI (no temp sensor)",
                        "status": data[0].get("Status", "Unknown"),
                    }
            except (json.JSONDecodeError, TypeError):
                pass

        return {
            "temperature_c": None,
            "gpu_name": "Unknown",
            "source": "Unavailable",
            "status": "Unknown",
        }

    def detect_thermal_throttling(self):
        """
        Detect if CPU is being thermally throttled.

        Returns:
            dict: {throttled: bool, current_speed_mhz, max_speed_mhz, percentage, status}
        """
        if not IS_WINDOWS:
            return {"throttled": False, "status": "Unknown"}

        cmd = (
            "Get-CimInstance Win32_Processor | "
            "Select-Object CurrentClockSpeed, MaxClockSpeed, Name "
            "| ConvertTo-Json -Compress"
        )
        output = self._run_ps(cmd)
        if not output:
            return {"throttled": False, "status": "Unknown"}

        try:
            data = json.loads(output)
            if isinstance(data, dict):
                data = [data]

            cpu = data[0]
            current = cpu.get("CurrentClockSpeed", 0) or 0
            max_speed = cpu.get("MaxClockSpeed", 0) or 0

            if max_speed == 0:
                return {"throttled": False, "status": "Unknown"}

            percentage = round((current / max_speed) * 100, 1)
            throttled = percentage < 85  # Below 85% of max = likely throttling

            status = "Normal"
            if percentage < 70:
                status = "Heavy Throttling"
            elif percentage < 85:
                status = "Light Throttling"

            return {
                "throttled": throttled,
                "current_speed_mhz": current,
                "max_speed_mhz": max_speed,
                "percentage": percentage,
                "cpu_name": cpu.get("Name", "").strip(),
                "status": status,
            }
        except (json.JSONDecodeError, TypeError):
            return {"throttled": False, "status": "Unknown"}

    def get_performance_counters(self):
        """
        Get key performance counters.

        Returns:
            dict: Various performance metrics
        """
        if not IS_WINDOWS:
            return {}

        try:
            import psutil

            cpu_freq = psutil.cpu_freq()
            mem = psutil.virtual_memory()
            disk_io = psutil.disk_io_counters()
            cpu_pct = psutil.cpu_percent(interval=1)
            per_cpu = psutil.cpu_percent(interval=0, percpu=True)

            return {
                "cpu_percent": cpu_pct,
                "cpu_per_core": per_cpu,
                "cpu_freq_current_mhz": round(cpu_freq.current) if cpu_freq else 0,
                "cpu_freq_max_mhz": round(cpu_freq.max) if cpu_freq else 0,
                "ram_percent": mem.percent,
                "ram_available_gb": round(mem.available / (1024**3), 1),
                "disk_read_mb": round(disk_io.read_bytes / (1024**2)) if disk_io else 0,
                "disk_write_mb": round(disk_io.write_bytes / (1024**2)) if disk_io else 0,
                "context_switches": psutil.cpu_stats().ctx_switches
                if hasattr(psutil, "cpu_stats")
                else 0,
            }
        except ImportError:
            return {"error": "psutil not available"}
        except Exception as e:
            return {"error": str(e)}

    def run_power_report(self):
        """
        Generate a power efficiency report (60 seconds).

        Returns:
            dict: {success: bool, report_path: str, message: str}
        """
        if not IS_WINDOWS:
            return {"success": False, "message": "Only available on Windows"}

        import os

        report_dir = os.path.join(os.path.expanduser("~"), ".winsvalinn")
        os.makedirs(report_dir, exist_ok=True)
        report_path = os.path.join(report_dir, "energy-report.html")

        self._log("Running power efficiency report (this takes ~60 seconds)...")

        try:
            result = subprocess.run(
                ["powercfg", "/energy", f"/output:{report_path}", "/duration:10"],
                capture_output=True,
                text=True,
                timeout=120,
                creationflags=CREATE_NO_WINDOW,
            )

            if result.returncode == 0 and os.path.exists(report_path):
                size = os.path.getsize(report_path)
                self._log(f"Power report generated: {report_path} ({size} bytes)")
                return {
                    "success": True,
                    "report_path": report_path,
                    "message": f"Report saved to {report_path}",
                }
            else:
                error = result.stderr.strip() or result.stdout.strip()
                return {"success": False, "report_path": "", "message": error[:200]}

        except subprocess.TimeoutExpired:
            return {"success": False, "report_path": "", "message": "Report timed out"}
        except Exception as e:
            return {"success": False, "report_path": "", "message": str(e)}

    def get_full_thermal_report(self):
        """
        Complete thermal and performance snapshot.

        Returns:
            dict: Combined thermal and performance data
        """
        self._log("Generating thermal report...")

        cpu_temp = self.get_cpu_temperature()
        gpu_temp = self.get_gpu_temperature()
        throttle = self.detect_thermal_throttling()
        counters = self.get_performance_counters()

        overall = "Good"
        warnings = []

        if cpu_temp.get("status") == "Critical":
            overall = "Critical"
            warnings.append(f"CPU temperature: {cpu_temp.get('temperature_c')}°C")
        elif cpu_temp.get("status") == "Warning":
            overall = "Warning"
            warnings.append(f"CPU temperature elevated: {cpu_temp.get('temperature_c')}°C")

        if gpu_temp.get("status") == "Critical":
            overall = "Critical"
            warnings.append(f"GPU temperature: {gpu_temp.get('temperature_c')}°C")

        if throttle.get("throttled"):
            if overall != "Critical":
                overall = "Warning"
            warnings.append(f"CPU throttling: running at {throttle.get('percentage')}% speed")

        self._log(f"Thermal report: {overall} ({len(warnings)} warning(s))")

        return {
            "overall": overall,
            "cpu_temperature": cpu_temp,
            "gpu_temperature": gpu_temp,
            "throttling": throttle,
            "performance": counters,
            "warnings": warnings,
        }
