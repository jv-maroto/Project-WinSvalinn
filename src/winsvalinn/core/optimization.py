"""
Optimization Module - WinSvalinn
Handles all system optimization functions for Windows.
"""

import os
import platform
import re
import subprocess
from datetime import datetime

try:
    import psutil
except ImportError:
    psutil = None


class SystemOptimizer:
    """Core system optimization engine."""

    def __init__(self, callback=None):
        self.callback = callback or (lambda msg, level="info": None)
        self.is_windows = platform.system() == "Windows"

    def log(self, message, level="info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.callback(f"[{timestamp}] {message}", level)

    # ─── System Information ─────────────────────────────────────────────

    def get_system_info(self):
        """Get comprehensive system information."""
        info = {
            "os": platform.system(),
            "os_version": platform.version(),
            "os_release": platform.release(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "hostname": platform.node(),
        }

        if psutil:
            mem = psutil.virtual_memory()
            info["ram_total"] = f"{mem.total / (1024**3):.1f} GB"
            info["ram_used"] = f"{mem.used / (1024**3):.1f} GB"
            info["ram_percent"] = f"{mem.percent}%"
            info["ram_available"] = f"{mem.available / (1024**3):.1f} GB"

            info["cpu_cores_physical"] = psutil.cpu_count(logical=False)
            info["cpu_cores_logical"] = psutil.cpu_count(logical=True)
            info["cpu_freq"] = (
                f"{psutil.cpu_freq().current:.0f} MHz" if psutil.cpu_freq() else "N/A"
            )
            info["cpu_usage"] = f"{psutil.cpu_percent(interval=1)}%"

            disks = []
            for part in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    disks.append(
                        {
                            "device": part.device,
                            "mountpoint": part.mountpoint,
                            "fstype": part.fstype,
                            "total": f"{usage.total / (1024**3):.1f} GB",
                            "used": f"{usage.used / (1024**3):.1f} GB",
                            "free": f"{usage.free / (1024**3):.1f} GB",
                            "percent": f"{usage.percent}%",
                        }
                    )
                except (PermissionError, OSError):
                    pass
            info["disks"] = disks

            info["boot_time"] = datetime.fromtimestamp(psutil.boot_time()).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        return info

    # ─── Temp Files Cleanup ─────────────────────────────────────────────

    def analyze_temp_files(self):
        """Analyze temporary files that can be cleaned."""
        temp_locations = []
        total_size = 0

        paths_to_check = []
        if self.is_windows:
            temp = os.environ.get("TEMP", "")
            tmp = os.environ.get("TMP", "")
            userprofile = os.environ.get("USERPROFILE", "")
            windir = os.environ.get("WINDIR", "C:\\Windows")

            if temp:
                paths_to_check.append(("User Temp", temp))
            if tmp and tmp != temp:
                paths_to_check.append(("System Temp", tmp))
            paths_to_check.append(("Windows Temp", os.path.join(windir, "Temp")))
            paths_to_check.append(("Prefetch", os.path.join(windir, "Prefetch")))
            if userprofile:
                paths_to_check.append(
                    (
                        "Thumbnail Cache",
                        os.path.join(
                            userprofile, "AppData", "Local", "Microsoft", "Windows", "Explorer"
                        ),
                    )
                )
                paths_to_check.append(
                    (
                        "Recent Files",
                        os.path.join(
                            userprofile, "AppData", "Roaming", "Microsoft", "Windows", "Recent"
                        ),
                    )
                )
                paths_to_check.append(
                    (
                        "IE Cache",
                        os.path.join(
                            userprofile, "AppData", "Local", "Microsoft", "Windows", "INetCache"
                        ),
                    )
                )
                paths_to_check.append(
                    (
                        "Windows Update Cache",
                        os.path.join(windir, "SoftwareDistribution", "Download"),
                    )
                )
        else:
            paths_to_check.append(("Temp", "/tmp"))

        for name, path in paths_to_check:
            if os.path.exists(path):
                dir_size = 0
                file_count = 0
                try:
                    for dirpath, dirnames, filenames in os.walk(path):
                        for f in filenames:
                            try:
                                fp = os.path.join(dirpath, f)
                                dir_size += os.path.getsize(fp)
                                file_count += 1
                            except (OSError, PermissionError):
                                pass
                except (OSError, PermissionError):
                    pass

                temp_locations.append(
                    {
                        "name": name,
                        "path": path,
                        "size_bytes": dir_size,
                        "size_readable": self._format_size(dir_size),
                        "file_count": file_count,
                    }
                )
                total_size += dir_size

        return {
            "locations": temp_locations,
            "total_size": total_size,
            "total_readable": self._format_size(total_size),
        }

    def clean_temp_files(self, paths=None):
        """Clean temporary files from specified paths."""
        cleaned = 0
        errors = 0
        freed_space = 0

        if paths is None:
            analysis = self.analyze_temp_files()
            paths = [loc["path"] for loc in analysis["locations"]]

        for path in paths:
            if not os.path.exists(path):
                continue
            self.log(f"Cleaning: {path}")
            for dirpath, dirnames, filenames in os.walk(path, topdown=False):
                for f in filenames:
                    try:
                        fp = os.path.join(dirpath, f)
                        size = os.path.getsize(fp)
                        os.remove(fp)
                        cleaned += 1
                        freed_space += size
                    except (OSError, PermissionError):
                        errors += 1
                for d in dirnames:
                    try:
                        dp = os.path.join(dirpath, d)
                        if not os.listdir(dp):
                            os.rmdir(dp)
                    except (OSError, PermissionError):
                        pass

        return {
            "files_cleaned": cleaned,
            "errors": errors,
            "freed_space": self._format_size(freed_space),
            "freed_bytes": freed_space,
        }

    # ─── RAM Optimization ───────────────────────────────────────────────

    def get_memory_usage(self):
        """Get detailed memory usage information."""
        if not psutil:
            return {}

        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()

        # Top memory consuming processes
        processes = []
        for proc in psutil.process_iter(["pid", "name", "memory_percent", "memory_info"]):
            try:
                info = proc.info
                if info["memory_percent"] and info["memory_percent"] > 0.1:
                    processes.append(
                        {
                            "pid": info["pid"],
                            "name": info["name"],
                            "memory_percent": round(info["memory_percent"], 2),
                            "memory_mb": round(info["memory_info"].rss / (1024 * 1024), 1)
                            if info["memory_info"]
                            else 0,
                        }
                    )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        processes.sort(key=lambda x: x["memory_percent"], reverse=True)

        return {
            "total": self._format_size(mem.total),
            "available": self._format_size(mem.available),
            "used": self._format_size(mem.used),
            "percent": mem.percent,
            "swap_total": self._format_size(swap.total),
            "swap_used": self._format_size(swap.used),
            "swap_percent": swap.percent,
            "top_processes": processes[:20],
        }

    def optimize_memory(self):
        """Attempt to free up RAM by clearing caches."""
        results = {"actions": [], "before": 0, "after": 0}

        if not psutil:
            return results

        mem_before = psutil.virtual_memory()
        results["before"] = mem_before.percent

        if self.is_windows:
            # Clear file system cache
            try:
                subprocess.run(
                    [
                        "powershell",
                        "-Command",
                        "[System.GC]::Collect();[System.GC]::WaitForPendingFinalizers()",
                    ],
                    capture_output=True,
                    timeout=10,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                results["actions"].append("Triggered garbage collection")
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                pass

            # Clear DNS cache
            try:
                subprocess.run(
                    ["ipconfig", "/flushdns"],
                    capture_output=True,
                    timeout=10,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                results["actions"].append("Flushed DNS cache")
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                pass

        import time

        time.sleep(2)
        mem_after = psutil.virtual_memory()
        results["after"] = mem_after.percent
        results["freed"] = self._format_size(max(0, mem_before.used - mem_after.used))

        return results

    # ─── Startup Management ─────────────────────────────────────────────

    def get_startup_impact(self):
        """Get startup programs with their performance impact."""
        programs = []

        if not self.is_windows:
            return programs

        try:
            result = subprocess.run(
                [
                    "powershell",
                    "-Command",
                    "Get-CimInstance Win32_StartupCommand | "
                    "Select-Object Name, Command, Location, User | "
                    "Format-List",
                ],
                capture_output=True,
                text=True,
                timeout=20,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if result.returncode == 0:
                current = {}
                for line in result.stdout.split("\n"):
                    line = line.strip()
                    if ":" in line:
                        key, _, value = line.partition(":")
                        key = key.strip()
                        value = value.strip()
                        if key == "Name":
                            if current:
                                programs.append(current)
                            current = {
                                "name": value,
                                "command": "",
                                "location": "",
                                "user": "",
                                "can_disable": True,
                            }
                        elif key == "Command" and current:
                            current["command"] = value
                        elif key == "Location" and current:
                            current["location"] = value
                        elif key == "User" and current:
                            current["user"] = value
                if current:
                    programs.append(current)
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

        return programs

    def disable_startup_program(self, program_name, location):
        """Disable a startup program via registry."""
        if not self.is_windows:
            return False

        try:
            result = subprocess.run(
                ["reg", "delete", location, "/v", program_name, "/f"],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False

    # ─── Service Optimization ───────────────────────────────────────────

    def get_services_info(self):
        """Get Windows services information with optimization suggestions."""
        services = []

        if not self.is_windows:
            return services

        # Services that can typically be safely disabled for performance
        optional_services = {
            "DiagTrack": "Connected User Experiences and Telemetry",
            "dmwappushservice": "WAP Push Message Routing Service",
            "SysMain": "Superfetch (can help on HDD, less on SSD)",
            "WSearch": "Windows Search Indexing",
            "Fax": "Fax Service",
            "XblAuthManager": "Xbox Live Auth Manager",
            "XblGameSave": "Xbox Live Game Save",
            "XboxNetApiSvc": "Xbox Live Networking Service",
            "XboxGipSvc": "Xbox Accessory Management",
            "RetailDemo": "Retail Demo Service",
            "MapsBroker": "Downloaded Maps Manager",
            "lfsvc": "Geolocation Service",
            "SharedAccess": "Internet Connection Sharing",
            "RemoteRegistry": "Remote Registry",
            "WMPNetworkSvc": "Windows Media Player Network Sharing",
            "wisvc": "Windows Insider Service",
        }

        try:
            result = subprocess.run(
                [
                    "powershell",
                    "-Command",
                    "Get-Service | Select-Object Name, DisplayName, Status, "
                    "StartType | ConvertTo-Csv -NoTypeInformation",
                ],
                capture_output=True,
                text=True,
                timeout=20,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                for line in lines[1:]:
                    parts = line.replace('"', "").split(",")
                    if len(parts) >= 4:
                        svc_name = parts[0].strip()
                        services.append(
                            {
                                "name": svc_name,
                                "display_name": parts[1].strip(),
                                "status": parts[2].strip(),
                                "start_type": parts[3].strip(),
                                "can_optimize": svc_name in optional_services,
                                "description": optional_services.get(svc_name, ""),
                            }
                        )
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

        return services

    def disable_service(self, service_name):
        """Disable a Windows service."""
        if not self.is_windows:
            return False

        try:
            # Stop the service
            subprocess.run(
                ["sc", "stop", service_name],
                capture_output=True,
                timeout=15,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            # Disable it
            result = subprocess.run(
                ["sc", "config", service_name, "start=", "disabled"],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False

    # ─── Visual Effects Optimization ────────────────────────────────────

    def get_visual_effects_status(self):
        """Get current visual effects settings."""
        effects = {
            "current_mode": "Unknown",
            "animations_enabled": "Unknown",
            "transparency_enabled": "Unknown",
            "shadow_enabled": "Unknown",
        }

        if not self.is_windows:
            return effects

        try:
            result = subprocess.run(
                [
                    "reg",
                    "query",
                    r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects",
                    "/v",
                    "VisualFXSetting",
                ],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if result.returncode == 0:
                match = re.search(r"0x(\d+)", result.stdout)
                if match:
                    val = int(match.group(1))
                    modes = {
                        0: "Let Windows decide",
                        1: "Best appearance",
                        2: "Best performance",
                        3: "Custom",
                    }
                    effects["current_mode"] = modes.get(val, "Custom")
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

        try:
            result = subprocess.run(
                [
                    "reg",
                    "query",
                    r"HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
                    "/v",
                    "EnableTransparency",
                ],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if result.returncode == 0:
                effects["transparency_enabled"] = (
                    "1" in result.stdout.split("0x")[-1] if "0x" in result.stdout else "Unknown"
                )
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

        return effects

    def optimize_visual_effects(self, mode="performance"):
        """Set visual effects for best performance."""
        if not self.is_windows:
            return False

        results = {"actions": [], "success": True}

        try:
            if mode == "performance":
                # Set to best performance
                subprocess.run(
                    [
                        "reg",
                        "add",
                        r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects",
                        "/v",
                        "VisualFXSetting",
                        "/t",
                        "REG_DWORD",
                        "/d",
                        "2",
                        "/f",
                    ],
                    capture_output=True,
                    timeout=10,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                results["actions"].append("Set visual effects to Best Performance")

                # Disable animations
                subprocess.run(
                    [
                        "reg",
                        "add",
                        r"HKCU\Control Panel\Desktop\WindowMetrics",
                        "/v",
                        "MinAnimate",
                        "/t",
                        "REG_SZ",
                        "/d",
                        "0",
                        "/f",
                    ],
                    capture_output=True,
                    timeout=10,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                results["actions"].append("Disabled window animations")

                # Disable transparency
                subprocess.run(
                    [
                        "reg",
                        "add",
                        r"HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
                        "/v",
                        "EnableTransparency",
                        "/t",
                        "REG_DWORD",
                        "/d",
                        "0",
                        "/f",
                    ],
                    capture_output=True,
                    timeout=10,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                results["actions"].append("Disabled transparency effects")

                # Disable fancy cursor shadow
                subprocess.run(
                    [
                        "reg",
                        "add",
                        r"HKCU\Control Panel\Desktop",
                        "/v",
                        "UserPreferencesMask",
                        "/t",
                        "REG_BINARY",
                        "/d",
                        "9012038010000000",
                        "/f",
                    ],
                    capture_output=True,
                    timeout=10,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                results["actions"].append("Optimized desktop preferences")

            elif mode == "balanced":
                subprocess.run(
                    [
                        "reg",
                        "add",
                        r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects",
                        "/v",
                        "VisualFXSetting",
                        "/t",
                        "REG_DWORD",
                        "/d",
                        "0",
                        "/f",
                    ],
                    capture_output=True,
                    timeout=10,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                results["actions"].append("Set visual effects to Let Windows Decide")

        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
            results["success"] = False
            results["error"] = str(e)

        return results

    # ─── Power Plan Optimization ────────────────────────────────────────

    def get_power_plans(self):
        """Get available power plans."""
        plans = []

        if not self.is_windows:
            return plans

        try:
            result = subprocess.run(
                ["powercfg", "/list"],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    match = re.search(r"GUID:\s+([a-f0-9-]+)\s+\((.+?)\)(\s*\*)?", line)
                    if match:
                        plans.append(
                            {
                                "guid": match.group(1),
                                "name": match.group(2),
                                "active": bool(match.group(3)),
                            }
                        )
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

        return plans

    def set_power_plan(self, plan_guid):
        """Set active power plan."""
        if not self.is_windows:
            return False

        try:
            result = subprocess.run(
                ["powercfg", "/setactive", plan_guid],
                capture_output=True,
                timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False

    def create_ultimate_performance_plan(self):
        """Create/enable Ultimate Performance power plan."""
        if not self.is_windows:
            return False

        try:
            result = subprocess.run(
                ["powercfg", "-duplicatescheme", "e9a42b02-d5df-448d-aa00-03f14749eb61"],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if result.returncode == 0:
                match = re.search(r"([a-f0-9-]{36})", result.stdout)
                if match:
                    return self.set_power_plan(match.group(1))
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
        return False

    # ─── GPU / Graphics Optimization ────────────────────────────────────

    def get_gpu_info(self):
        """Get GPU information."""
        gpu_info = []

        if not self.is_windows:
            return gpu_info

        try:
            result = subprocess.run(
                [
                    "powershell",
                    "-Command",
                    "Get-CimInstance Win32_VideoController | "
                    "Select-Object Name, DriverVersion, AdapterRAM, "
                    "VideoModeDescription, CurrentRefreshRate, Status | "
                    "Format-List",
                ],
                capture_output=True,
                text=True,
                timeout=15,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if result.returncode == 0:
                current = {}
                for line in result.stdout.split("\n"):
                    line = line.strip()
                    if ":" in line:
                        key, _, value = line.partition(":")
                        key = key.strip()
                        value = value.strip()
                        if key == "Name":
                            if current:
                                gpu_info.append(current)
                            current = {"name": value}
                        elif current:
                            current[key.lower().replace(" ", "_")] = value
                if current:
                    gpu_info.append(current)
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

        return gpu_info

    def optimize_gpu_settings(self):
        """Apply GPU optimization settings."""
        results = {"actions": [], "success": True}

        if not self.is_windows:
            return results

        try:
            # Disable Game DVR / Game Bar
            subprocess.run(
                [
                    "reg",
                    "add",
                    r"HKCU\Software\Microsoft\Windows\CurrentVersion\GameDVR",
                    "/v",
                    "AppCaptureEnabled",
                    "/t",
                    "REG_DWORD",
                    "/d",
                    "0",
                    "/f",
                ],
                capture_output=True,
                timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            results["actions"].append("Disabled Game DVR")

            subprocess.run(
                [
                    "reg",
                    "add",
                    r"HKCU\System\GameConfigStore",
                    "/v",
                    "GameDVR_Enabled",
                    "/t",
                    "REG_DWORD",
                    "/d",
                    "0",
                    "/f",
                ],
                capture_output=True,
                timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            results["actions"].append("Disabled Game Bar recording")

            # Enable Hardware-accelerated GPU scheduling
            subprocess.run(
                [
                    "reg",
                    "add",
                    r"HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers",
                    "/v",
                    "HwSchMode",
                    "/t",
                    "REG_DWORD",
                    "/d",
                    "2",
                    "/f",
                ],
                capture_output=True,
                timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            results["actions"].append("Enabled Hardware-accelerated GPU scheduling")

            # Disable fullscreen optimizations globally
            subprocess.run(
                [
                    "reg",
                    "add",
                    r"HKCU\System\GameConfigStore",
                    "/v",
                    "GameDVR_FSEBehaviorMode",
                    "/t",
                    "REG_DWORD",
                    "/d",
                    "2",
                    "/f",
                ],
                capture_output=True,
                timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            results["actions"].append("Optimized fullscreen behavior")

            # Set GPU preference to high performance
            subprocess.run(
                [
                    "reg",
                    "add",
                    r"HKCU\Software\Microsoft\DirectX\UserGpuPreferences",
                    "/v",
                    "DirectXUserGlobalSettings",
                    "/t",
                    "REG_SZ",
                    "/d",
                    "SwapEffectUpgradeEnable=1;",
                    "/f",
                ],
                capture_output=True,
                timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            results["actions"].append("Set GPU to high performance preference")

        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
            results["success"] = False
            results["error"] = str(e)

        return results

    # ─── Network Optimization ───────────────────────────────────────────

    def optimize_network(self):
        """Optimize network settings for better performance."""
        results = {"actions": [], "success": True}

        if not self.is_windows:
            return results

        try:
            # Flush DNS
            subprocess.run(
                ["ipconfig", "/flushdns"],
                capture_output=True,
                timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            results["actions"].append("Flushed DNS cache")

            # Reset Winsock
            subprocess.run(
                ["netsh", "winsock", "reset"],
                capture_output=True,
                timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            results["actions"].append("Reset Winsock catalog")

            # Optimize TCP settings
            subprocess.run(
                ["netsh", "int", "tcp", "set", "global", "autotuninglevel=normal"],
                capture_output=True,
                timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            results["actions"].append("Set TCP auto-tuning to normal")

            # Enable TCP timestamps
            subprocess.run(
                ["netsh", "int", "tcp", "set", "global", "timestamps=enabled"],
                capture_output=True,
                timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            results["actions"].append("Enabled TCP timestamps")

            # Disable Nagle's algorithm for lower latency
            subprocess.run(
                [
                    "reg",
                    "add",
                    r"HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters",
                    "/v",
                    "TcpNoDelay",
                    "/t",
                    "REG_DWORD",
                    "/d",
                    "1",
                    "/f",
                ],
                capture_output=True,
                timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            results["actions"].append("Disabled Nagle's algorithm (lower latency)")

        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
            results["success"] = False
            results["error"] = str(e)

        return results

    # ─── Disk Optimization ──────────────────────────────────────────────

    def get_disk_health(self):
        """Get disk health information."""
        disks = []

        if not psutil:
            return disks

        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                health = "Good"
                if usage.percent > 90:
                    health = "Critical"
                elif usage.percent > 75:
                    health = "Warning"

                disks.append(
                    {
                        "device": part.device,
                        "mountpoint": part.mountpoint,
                        "fstype": part.fstype,
                        "total_gb": round(usage.total / (1024**3), 1),
                        "used_gb": round(usage.used / (1024**3), 1),
                        "free_gb": round(usage.free / (1024**3), 1),
                        "percent": usage.percent,
                        "health": health,
                    }
                )
            except (PermissionError, OSError):
                pass

        return disks

    def run_disk_cleanup(self, drive="C:"):
        """Trigger Windows disk cleanup."""
        if not self.is_windows:
            return False

        try:
            # Set all cleanup flags
            cleanup_flags = {
                "Active Setup Temp Folders": 1,
                "Downloaded Program Files": 1,
                "Internet Cache Files": 1,
                "Old ChkDsk Files": 1,
                "Recycle Bin": 1,
                "Setup Log Files": 1,
                "System error memory dump files": 1,
                "System error minidump files": 1,
                "Temporary Files": 1,
                "Thumbnail Cache": 1,
                "Upgrade Discarded Files": 1,
                "Windows Error Reporting": 1,
            }

            # Pre-configure cleanup options
            for flag_name, value in cleanup_flags.items():
                subprocess.run(
                    [
                        "reg",
                        "add",
                        r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer"
                        r"\VolumeCaches\\" + flag_name,
                        "/v",
                        "StateFlags0064",
                        "/t",
                        "REG_DWORD",
                        "/d",
                        str(value),
                        "/f",
                    ],
                    capture_output=True,
                    timeout=10,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )

            # Run cleanup silently
            subprocess.Popen(
                ["cleanmgr", "/sagerun:64", f"/d{drive[0]}"],
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            return True

        except (FileNotFoundError, OSError):
            return False

    # ─── Windows Tweaks for Gaming/Performance ──────────────────────────

    def apply_performance_tweaks(self):
        """Apply comprehensive Windows performance tweaks."""
        results = {"actions": [], "success": True}

        if not self.is_windows:
            return results

        tweaks = [
            # Disable Cortana
            (
                r"HKLM\SOFTWARE\Policies\Microsoft\Windows\Windows Search",
                "AllowCortana",
                "REG_DWORD",
                "0",
                "Disabled Cortana",
            ),
            # Disable Tips and Suggestions
            (
                r"HKCU\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager",
                "SubscribedContent-338389Enabled",
                "REG_DWORD",
                "0",
                "Disabled tips and suggestions",
            ),
            # Disable lock screen tips
            (
                r"HKCU\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager",
                "RotatingLockScreenOverlayEnabled",
                "REG_DWORD",
                "0",
                "Disabled lock screen tips",
            ),
            # Disable Start menu suggestions
            (
                r"HKCU\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager",
                "SystemPaneSuggestionsEnabled",
                "REG_DWORD",
                "0",
                "Disabled Start menu suggestions",
            ),
            # Disable background apps
            (
                r"HKCU\Software\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications",
                "GlobalUserDisabled",
                "REG_DWORD",
                "1",
                "Disabled background apps",
            ),
            # Disable mouse acceleration
            (
                r"HKCU\Control Panel\Mouse",
                "MouseSpeed",
                "REG_SZ",
                "0",
                "Disabled mouse acceleration",
            ),
            # Set process priority higher for foreground apps
            (
                r"HKLM\SYSTEM\CurrentControlSet\Control\PriorityControl",
                "Win32PrioritySeparation",
                "REG_DWORD",
                "38",
                "Optimized process priority for foreground apps",
            ),
            # Disable hibernation file (saves disk space)
            # This is done via command, not registry
            # Increase system responsiveness
            (
                r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile",
                "SystemResponsiveness",
                "REG_DWORD",
                "0",
                "Maximized system responsiveness",
            ),
            # Optimize GPU thread priority
            (
                r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games",
                "GPU Priority",
                "REG_DWORD",
                "8",
                "Optimized GPU thread priority for games",
            ),
            (
                r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games",
                "Priority",
                "REG_DWORD",
                "6",
                "Set game task priority to high",
            ),
            (
                r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games",
                "Scheduling Category",
                "REG_SZ",
                "High",
                "Set game scheduling to high",
            ),
        ]

        for reg_path, name, reg_type, value, description in tweaks:
            try:
                subprocess.run(
                    ["reg", "add", reg_path, "/v", name, "/t", reg_type, "/d", value, "/f"],
                    capture_output=True,
                    timeout=10,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                results["actions"].append(description)
                self.log(f"Applied: {description}")
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                pass

        # Disable hibernation
        try:
            subprocess.run(
                ["powercfg", "/hibernate", "off"],
                capture_output=True,
                timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            results["actions"].append("Disabled hibernation (freed disk space)")
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

        return results

    # ─── SSD Optimization ───────────────────────────────────────────────

    def optimize_ssd(self):
        """Apply SSD-specific optimizations."""
        results = {"actions": [], "success": True}

        if not self.is_windows:
            return results

        try:
            # Disable Superfetch for SSD
            subprocess.run(
                ["sc", "config", "SysMain", "start=", "disabled"],
                capture_output=True,
                timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            subprocess.run(
                ["sc", "stop", "SysMain"],
                capture_output=True,
                timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            results["actions"].append("Disabled Superfetch (SysMain)")

            # Enable TRIM
            subprocess.run(
                ["fsutil", "behavior", "set", "DisableDeleteNotify", "0"],
                capture_output=True,
                timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            results["actions"].append("Enabled TRIM support")

            # Disable last access timestamp
            subprocess.run(
                ["fsutil", "behavior", "set", "disablelastaccess", "1"],
                capture_output=True,
                timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            results["actions"].append("Disabled last access timestamps")

        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
            results["success"] = False
            results["error"] = str(e)

        return results

    # ─── Full Optimization ──────────────────────────────────────────────

    def run_full_optimization(self, progress_callback=None):
        """Run comprehensive system optimization."""
        results = {}
        steps = [
            ("System Info", self.get_system_info),
            ("Temp Files Analysis", self.analyze_temp_files),
            ("Memory Usage", self.get_memory_usage),
            ("Disk Health", self.get_disk_health),
            ("Power Plans", self.get_power_plans),
            ("GPU Info", self.get_gpu_info),
            ("Visual Effects", self.get_visual_effects_status),
            ("Services", self.get_services_info),
            ("Startup Impact", self.get_startup_impact),
        ]

        for i, (name, func) in enumerate(steps):
            self.log(f"Analyzing: {name}...")
            if progress_callback:
                progress_callback(i + 1, len(steps), name)
            try:
                results[name] = func()
            except Exception as e:
                results[name] = {"error": str(e)}
                self.log(f"Error in {name}: {e}", "error")

        return results

    # ─── Helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _format_size(size_bytes):
        """Format bytes to human-readable size."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} PB"
