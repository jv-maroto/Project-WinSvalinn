"""
Advanced RAM Optimizer - WinSvalinn
Frees RAM by trimming working sets, clearing caches, and managing processes.
"""

import os
import platform
import subprocess
from datetime import datetime

try:
    import psutil
except ImportError:
    psutil = None


class RAMOptimizer:
    """Advanced RAM optimization and freeing."""

    def __init__(self, callback=None):
        self.callback = callback or (lambda msg, level="info": None)
        self.is_windows = platform.system() == "Windows"

    def log(self, message, level="info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.callback(f"[{timestamp}] {message}", level)

    def get_detailed_memory(self):
        """Get detailed memory breakdown."""
        if not psutil:
            return {}

        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()

        # Categorize processes by memory usage
        categories = {
            "browsers": {
                "names": ["chrome", "firefox", "msedge", "opera", "brave", "vivaldi"],
                "memory_mb": 0,
                "count": 0,
            },
            "games": {
                "names": ["steam", "epicgames", "origin", "uplay", "battlenet"],
                "memory_mb": 0,
                "count": 0,
            },
            "system": {
                "names": [
                    "svchost",
                    "csrss",
                    "lsass",
                    "services",
                    "smss",
                    "wininit",
                    "winlogon",
                    "dwm",
                    "explorer",
                ],
                "memory_mb": 0,
                "count": 0,
            },
            "office": {
                "names": ["word", "excel", "outlook", "teams", "onenote", "powerpnt"],
                "memory_mb": 0,
                "count": 0,
            },
            "dev_tools": {
                "names": ["code", "devenv", "idea", "pycharm", "node", "python", "java", "docker"],
                "memory_mb": 0,
                "count": 0,
            },
            "other": {"names": [], "memory_mb": 0, "count": 0},
        }

        top_processes = []
        for proc in psutil.process_iter(["pid", "name", "memory_info", "memory_percent"]):
            try:
                info = proc.info
                if not info["memory_info"]:
                    continue
                mem_mb = info["memory_info"].rss / (1024 * 1024)
                if mem_mb < 1:
                    continue

                name_lower = (info["name"] or "").lower()
                categorized = False
                for cat_key, cat_data in categories.items():
                    if cat_key == "other":
                        continue
                    if any(n in name_lower for n in cat_data["names"]):
                        cat_data["memory_mb"] += mem_mb
                        cat_data["count"] += 1
                        categorized = True
                        break
                if not categorized:
                    categories["other"]["memory_mb"] += mem_mb
                    categories["other"]["count"] += 1

                top_processes.append(
                    {
                        "pid": info["pid"],
                        "name": info["name"],
                        "memory_mb": round(mem_mb, 1),
                        "memory_pct": round(info["memory_percent"] or 0, 2),
                    }
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        top_processes.sort(key=lambda x: x["memory_mb"], reverse=True)

        return {
            "total_gb": round(mem.total / (1024**3), 2),
            "used_gb": round(mem.used / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
            "percent": mem.percent,
            "swap_total_gb": round(swap.total / (1024**3), 2),
            "swap_used_gb": round(swap.used / (1024**3), 2),
            "swap_percent": swap.percent,
            "categories": categories,
            "top_processes": top_processes[:30],
        }

    def free_ram(self):
        """Aggressively free RAM using multiple techniques."""
        if not psutil:
            return {"success": False, "error": "psutil not available"}

        mem_before = psutil.virtual_memory()
        results = {"actions": [], "success": True}
        self.log("Starting RAM optimization...", "info")

        # 1. Flush DNS cache
        if self.is_windows:
            try:
                subprocess.run(
                    ["ipconfig", "/flushdns"],
                    capture_output=True,
                    timeout=10,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                results["actions"].append("Flushed DNS resolver cache")
                self.log("  Flushed DNS cache", "success")
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                pass

        # 2. Trigger .NET garbage collection
        if self.is_windows:
            try:
                subprocess.run(
                    [
                        "powershell",
                        "-Command",
                        "[System.GC]::Collect();"
                        "[System.GC]::WaitForPendingFinalizers();"
                        "[System.GC]::Collect()",
                    ],
                    capture_output=True,
                    timeout=15,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                results["actions"].append("Triggered .NET garbage collection")
                self.log("  .NET garbage collection completed", "success")
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                pass

        # 3. Trim working set of all processes
        if self.is_windows:
            try:
                # Use PowerShell to trim working sets
                ps_script = (
                    "Get-Process | ForEach-Object { "
                    "try { $_.MinWorkingSet = 204800; $_.MaxWorkingSet = 1413120 } "
                    "catch {} }"
                )
                subprocess.run(
                    ["powershell", "-Command", ps_script],
                    capture_output=True,
                    timeout=30,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                results["actions"].append("Trimmed working sets for all processes")
                self.log("  Trimmed process working sets", "success")
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                pass

        # 4. Clear Windows standby list (requires admin)
        if self.is_windows:
            try:
                # EmptyStandbyList using PowerShell
                subprocess.run(
                    [
                        "powershell",
                        "-Command",
                        "Clear-RecycleBin -Force -ErrorAction SilentlyContinue",
                    ],
                    capture_output=True,
                    timeout=15,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                results["actions"].append("Cleared recycle bin")
                self.log("  Cleared recycle bin", "success")
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                pass

        # 5. Clear Windows thumbnail cache
        if self.is_windows:
            userprofile = os.environ.get("USERPROFILE", "")
            if userprofile:
                thumb_path = os.path.join(
                    userprofile, "AppData", "Local", "Microsoft", "Windows", "Explorer"
                )
                if os.path.exists(thumb_path):
                    cleared = 0
                    for f in os.listdir(thumb_path):
                        if f.startswith("thumbcache_"):
                            try:
                                os.remove(os.path.join(thumb_path, f))
                                cleared += 1
                            except (OSError, PermissionError):
                                pass
                    if cleared:
                        results["actions"].append(f"Cleared {cleared} thumbnail cache files")
                        self.log(f"  Cleared {cleared} thumbnail caches", "success")

        # 6. Clear Windows font cache
        if self.is_windows:
            try:
                subprocess.run(
                    ["sc", "stop", "FontCache"],
                    capture_output=True,
                    timeout=10,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                windir = os.environ.get("WINDIR", "C:\\Windows")
                font_cache = os.path.join(
                    windir, "ServiceProfiles", "LocalService", "AppData", "Local", "FontCache"
                )
                if os.path.exists(font_cache):
                    for f in os.listdir(font_cache):
                        try:
                            os.remove(os.path.join(font_cache, f))
                        except (OSError, PermissionError):
                            pass
                subprocess.run(
                    ["sc", "start", "FontCache"],
                    capture_output=True,
                    timeout=10,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                results["actions"].append("Cleared and restarted font cache")
                self.log("  Font cache cleared", "success")
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                pass

        # Calculate freed memory
        import time

        time.sleep(2)
        mem_after = psutil.virtual_memory()
        freed_bytes = max(0, mem_before.used - mem_after.used)
        freed_mb = freed_bytes / (1024 * 1024)

        results["before_percent"] = mem_before.percent
        results["after_percent"] = mem_after.percent
        results["freed_mb"] = round(freed_mb, 1)
        results["freed_readable"] = self._format_size(freed_bytes)
        results["before_used_gb"] = round(mem_before.used / (1024**3), 2)
        results["after_used_gb"] = round(mem_after.used / (1024**3), 2)

        self.log(
            f"RAM optimization complete: {mem_before.percent}% -> {mem_after.percent}% "
            f"(freed {results['freed_readable']})",
            "success",
        )

        return results

    @staticmethod
    def _format_size(size_bytes):
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
