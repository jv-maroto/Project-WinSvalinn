"""
Windows Privacy Deep Cleaner for WinSvalinn.

Cleans recent files, jump lists, clipboard history,
thumbnail/icon/shader caches, search history, error reports,
and other Windows privacy traces.
"""

import glob
import os
import platform
import shutil
import subprocess

from winsvalinn.utils.logger import ModuleLogger

logger = ModuleLogger("PrivacyCleaner")

IS_WINDOWS = platform.system() == "Windows"
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class PrivacyCleaner:
    """Deep Windows privacy cleaning."""

    def __init__(self, callback=None):
        self._callback = callback or (lambda msg, level="info": None)
        self._home = os.path.expanduser("~")

    def _log(self, msg, level="info"):
        getattr(logger, level, logger.info)(msg)
        self._callback(msg, level)

    def _safe_rmtree(self, path):
        """Remove directory tree safely, return bytes freed."""
        if not os.path.exists(path):
            return 0
        size = self._dir_size(path)
        try:
            shutil.rmtree(path, ignore_errors=True)
            return size
        except (OSError, PermissionError):
            return 0

    def _safe_remove_files(self, pattern):
        """Remove files matching glob pattern, return (count, bytes)."""
        count = 0
        freed = 0
        for f in glob.glob(pattern):
            try:
                size = os.path.getsize(f)
                os.remove(f)
                count += 1
                freed += size
            except (OSError, PermissionError):
                pass
        return count, freed

    def _dir_size(self, path):
        total = 0
        try:
            for dirpath, _, filenames in os.walk(path):
                for f in filenames:
                    try:
                        total += os.path.getsize(os.path.join(dirpath, f))
                    except (OSError, PermissionError):
                        pass
        except (OSError, PermissionError):
            pass
        return total

    def analyze(self):
        """
        Analyze all cleanable privacy data.

        Returns:
            dict: {categories: list[dict], total_bytes, total_mb}
        """
        self._log("Analyzing privacy data...")

        categories = [
            self._analyze_recent_files(),
            self._analyze_jump_lists(),
            self._analyze_thumbnail_cache(),
            self._analyze_icon_cache(),
            self._analyze_shader_cache(),
            self._analyze_search_history(),
            self._analyze_error_reports(),
            self._analyze_font_cache(),
            self._analyze_temp_internet(),
            self._analyze_activity_timeline(),
        ]

        total = sum(c["size_bytes"] for c in categories)
        self._log(f"Total cleanable privacy data: {total / (1024**2):.1f} MB")

        return {
            "categories": categories,
            "total_bytes": total,
            "total_mb": round(total / (1024**2), 1),
        }

    def _analyze_recent_files(self):
        path = os.path.join(self._home, "AppData", "Roaming", "Microsoft", "Windows", "Recent")
        size = self._dir_size(path)
        count = len(glob.glob(os.path.join(path, "*"))) if os.path.exists(path) else 0
        return {
            "name": "Recent Files",
            "key": "recent",
            "path": path,
            "size_bytes": size,
            "items": count,
        }

    def _analyze_jump_lists(self):
        path = os.path.join(
            self._home,
            "AppData",
            "Roaming",
            "Microsoft",
            "Windows",
            "Recent",
            "AutomaticDestinations",
        )
        size = self._dir_size(path)
        path2 = os.path.join(
            self._home, "AppData", "Roaming", "Microsoft", "Windows", "Recent", "CustomDestinations"
        )
        size += self._dir_size(path2)
        return {
            "name": "Jump Lists",
            "key": "jumplists",
            "path": path,
            "size_bytes": size,
            "items": 0,
        }

    def _analyze_thumbnail_cache(self):
        path = os.path.join(self._home, "AppData", "Local", "Microsoft", "Windows", "Explorer")
        size = 0
        count = 0
        if os.path.exists(path):
            for f in glob.glob(os.path.join(path, "thumbcache_*")):
                try:
                    size += os.path.getsize(f)
                    count += 1
                except OSError:
                    pass
        return {
            "name": "Thumbnail Cache",
            "key": "thumbnails",
            "path": path,
            "size_bytes": size,
            "items": count,
        }

    def _analyze_icon_cache(self):
        path = os.path.join(self._home, "AppData", "Local", "Microsoft", "Windows", "Explorer")
        size = 0
        for f in glob.glob(os.path.join(path, "iconcache_*")):
            try:
                size += os.path.getsize(f)
            except OSError:
                pass
        icon_db = os.path.join(self._home, "AppData", "Local", "IconCache.db")
        if os.path.exists(icon_db):
            try:
                size += os.path.getsize(icon_db)
            except OSError:
                pass
        return {"name": "Icon Cache", "key": "icons", "path": path, "size_bytes": size, "items": 0}

    def _analyze_shader_cache(self):
        paths = [
            os.path.join(self._home, "AppData", "Local", "D3DSCache"),
            os.path.join(self._home, "AppData", "Local", "NVIDIA", "DXCache"),
            os.path.join(self._home, "AppData", "Local", "NVIDIA", "GLCache"),
            os.path.join(self._home, "AppData", "Local", "AMD", "DxCache"),
        ]
        size = sum(self._dir_size(p) for p in paths)
        return {
            "name": "Shader Cache (DirectX/GPU)",
            "key": "shaders",
            "path": paths[0],
            "size_bytes": size,
            "items": 0,
        }

    def _analyze_search_history(self):
        path = os.path.join(
            self._home,
            "AppData",
            "Local",
            "Packages",
            "Microsoft.Windows.Search_cw5n1h2txyewy",
            "LocalState",
        )
        size = self._dir_size(path) if os.path.exists(path) else 0
        return {
            "name": "Windows Search History",
            "key": "search",
            "path": path,
            "size_bytes": size,
            "items": 0,
        }

    def _analyze_error_reports(self):
        paths = [
            os.path.join(self._home, "AppData", "Local", "Microsoft", "Windows", "WER"),
            os.path.join(self._home, "AppData", "Local", "CrashDumps"),
        ]
        size = sum(self._dir_size(p) for p in paths)
        return {
            "name": "Error Reports & Crash Dumps",
            "key": "errors",
            "path": paths[0],
            "size_bytes": size,
            "items": 0,
        }

    def _analyze_font_cache(self):
        path = os.path.join(
            os.environ.get("SYSTEMROOT", "C:\\Windows"),
            "ServiceProfiles",
            "LocalService",
            "AppData",
            "Local",
            "FontCache",
        )
        size = self._dir_size(path) if os.path.exists(path) else 0
        return {"name": "Font Cache", "key": "fonts", "path": path, "size_bytes": size, "items": 0}

    def _analyze_temp_internet(self):
        path = os.path.join(self._home, "AppData", "Local", "Microsoft", "Windows", "INetCache")
        size = self._dir_size(path)
        return {
            "name": "Temporary Internet Files",
            "key": "inet",
            "path": path,
            "size_bytes": size,
            "items": 0,
        }

    def _analyze_activity_timeline(self):
        path = os.path.join(self._home, "AppData", "Local", "ConnectedDevicesPlatform")
        size = self._dir_size(path) if os.path.exists(path) else 0
        return {
            "name": "Activity Timeline",
            "key": "timeline",
            "path": path,
            "size_bytes": size,
            "items": 0,
        }

    def clean(self, categories=None):
        """
        Clean selected privacy categories.

        Args:
            categories: List of category keys to clean. None = clean all.

        Returns:
            dict: {cleaned: list, total_freed_bytes, total_freed_mb}
        """
        all_categories = {
            "recent": self._clean_recent,
            "jumplists": self._clean_jumplists,
            "thumbnails": self._clean_thumbnails,
            "icons": self._clean_icons,
            "shaders": self._clean_shaders,
            "search": self._clean_search,
            "errors": self._clean_errors,
            "fonts": self._clean_fonts,
            "inet": self._clean_inet,
            "timeline": self._clean_timeline,
        }

        if categories is None:
            categories = list(all_categories.keys())

        self._log(f"Cleaning {len(categories)} privacy categories...")
        cleaned = []
        total_freed = 0

        for cat_key in categories:
            cleaner = all_categories.get(cat_key)
            if cleaner:
                freed = cleaner()
                cleaned.append({"key": cat_key, "freed_bytes": freed})
                total_freed += freed

        self._log(f"Privacy cleanup complete: {total_freed / (1024**2):.1f} MB freed")
        return {
            "cleaned": cleaned,
            "total_freed_bytes": total_freed,
            "total_freed_mb": round(total_freed / (1024**2), 1),
        }

    def _clean_recent(self):
        path = os.path.join(self._home, "AppData", "Roaming", "Microsoft", "Windows", "Recent")
        count, freed = self._safe_remove_files(os.path.join(path, "*.lnk"))
        self._log(f"  Recent files: {count} items, {freed / 1024:.1f} KB")
        return freed

    def _clean_jumplists(self):
        freed = 0
        for sub in ["AutomaticDestinations", "CustomDestinations"]:
            path = os.path.join(
                self._home, "AppData", "Roaming", "Microsoft", "Windows", "Recent", sub
            )
            freed += self._safe_rmtree(path)
        self._log(f"  Jump lists: {freed / 1024:.1f} KB")
        return freed

    def _clean_thumbnails(self):
        path = os.path.join(self._home, "AppData", "Local", "Microsoft", "Windows", "Explorer")
        _, freed = self._safe_remove_files(os.path.join(path, "thumbcache_*"))
        self._log(f"  Thumbnail cache: {freed / (1024**2):.1f} MB")
        return freed

    def _clean_icons(self):
        path = os.path.join(self._home, "AppData", "Local", "Microsoft", "Windows", "Explorer")
        _, freed = self._safe_remove_files(os.path.join(path, "iconcache_*"))
        icon_db = os.path.join(self._home, "AppData", "Local", "IconCache.db")
        if os.path.exists(icon_db):
            try:
                freed += os.path.getsize(icon_db)
                os.remove(icon_db)
            except (OSError, PermissionError):
                pass
        self._log(f"  Icon cache: {freed / 1024:.1f} KB")
        return freed

    def _clean_shaders(self):
        freed = 0
        for path in [
            os.path.join(self._home, "AppData", "Local", "D3DSCache"),
            os.path.join(self._home, "AppData", "Local", "NVIDIA", "DXCache"),
            os.path.join(self._home, "AppData", "Local", "NVIDIA", "GLCache"),
            os.path.join(self._home, "AppData", "Local", "AMD", "DxCache"),
        ]:
            freed += self._safe_rmtree(path)
        self._log(f"  Shader cache: {freed / (1024**2):.1f} MB")
        return freed

    def _clean_search(self):
        path = os.path.join(
            self._home,
            "AppData",
            "Local",
            "Packages",
            "Microsoft.Windows.Search_cw5n1h2txyewy",
            "LocalState",
        )
        freed = self._safe_rmtree(path)
        self._log(f"  Search history: {freed / (1024**2):.1f} MB")
        return freed

    def _clean_errors(self):
        freed = 0
        for path in [
            os.path.join(self._home, "AppData", "Local", "Microsoft", "Windows", "WER"),
            os.path.join(self._home, "AppData", "Local", "CrashDumps"),
        ]:
            freed += self._safe_rmtree(path)
        self._log(f"  Error reports: {freed / (1024**2):.1f} MB")
        return freed

    def _clean_fonts(self):
        try:
            subprocess.run(
                ["net", "stop", "FontCache"],
                capture_output=True,
                timeout=10,
                creationflags=CREATE_NO_WINDOW,
            )
        except Exception:
            pass

        path = os.path.join(
            os.environ.get("SYSTEMROOT", "C:\\Windows"),
            "ServiceProfiles",
            "LocalService",
            "AppData",
            "Local",
            "FontCache",
        )
        freed = self._safe_rmtree(path)

        try:
            subprocess.run(
                ["net", "start", "FontCache"],
                capture_output=True,
                timeout=10,
                creationflags=CREATE_NO_WINDOW,
            )
        except Exception:
            pass

        self._log(f"  Font cache: {freed / (1024**2):.1f} MB")
        return freed

    def _clean_inet(self):
        path = os.path.join(self._home, "AppData", "Local", "Microsoft", "Windows", "INetCache")
        freed = self._safe_rmtree(path)
        self._log(f"  Temp internet: {freed / (1024**2):.1f} MB")
        return freed

    def _clean_timeline(self):
        path = os.path.join(self._home, "AppData", "Local", "ConnectedDevicesPlatform")
        freed = self._safe_rmtree(path)
        self._log(f"  Activity timeline: {freed / (1024**2):.1f} MB")
        return freed
