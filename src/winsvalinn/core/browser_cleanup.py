"""
Browser Cleanup Engine for WinSvalinn.

Detects installed browsers and cleans cache, cookies,
history, downloads history, and autofill data.
"""

import glob
import os
import platform
import shutil

from winsvalinn.utils.logger import ModuleLogger

logger = ModuleLogger("BrowserCleanup")

IS_WINDOWS = platform.system() == "Windows"

# Browser profile paths (relative to user home)
BROWSER_PATHS = {
    "Chrome": {
        "base": os.path.join("AppData", "Local", "Google", "Chrome", "User Data"),
        "profiles": ["Default", "Profile 1", "Profile 2", "Profile 3"],
        "cache_dirs": ["Cache", "Code Cache", "GPUCache", "Service Worker", "ShaderCache"],
        "cookie_files": ["Cookies", "Cookies-journal"],
        "history_files": ["History", "History-journal", "Visited Links", "Top Sites"],
        "autofill_files": ["Web Data", "Web Data-journal"],
        "session_files": ["Sessions", "Session Storage"],
    },
    "Edge": {
        "base": os.path.join("AppData", "Local", "Microsoft", "Edge", "User Data"),
        "profiles": ["Default", "Profile 1", "Profile 2"],
        "cache_dirs": ["Cache", "Code Cache", "GPUCache", "Service Worker", "ShaderCache"],
        "cookie_files": ["Cookies", "Cookies-journal"],
        "history_files": ["History", "History-journal", "Visited Links", "Top Sites"],
        "autofill_files": ["Web Data", "Web Data-journal"],
        "session_files": ["Sessions", "Session Storage"],
    },
    "Brave": {
        "base": os.path.join("AppData", "Local", "BraveSoftware", "Brave-Browser", "User Data"),
        "profiles": ["Default", "Profile 1"],
        "cache_dirs": ["Cache", "Code Cache", "GPUCache", "Service Worker", "ShaderCache"],
        "cookie_files": ["Cookies", "Cookies-journal"],
        "history_files": ["History", "History-journal"],
        "autofill_files": ["Web Data", "Web Data-journal"],
        "session_files": ["Sessions", "Session Storage"],
    },
    "Opera": {
        "base": os.path.join("AppData", "Roaming", "Opera Software", "Opera Stable"),
        "profiles": [""],  # Opera uses base dir directly
        "cache_dirs": ["Cache", "Code Cache", "GPUCache", "ShaderCache"],
        "cookie_files": ["Cookies", "Cookies-journal"],
        "history_files": ["History", "History-journal"],
        "autofill_files": ["Web Data", "Web Data-journal"],
        "session_files": ["Sessions", "Session Storage"],
    },
    "Vivaldi": {
        "base": os.path.join("AppData", "Local", "Vivaldi", "User Data"),
        "profiles": ["Default", "Profile 1"],
        "cache_dirs": ["Cache", "Code Cache", "GPUCache", "ShaderCache"],
        "cookie_files": ["Cookies", "Cookies-journal"],
        "history_files": ["History", "History-journal"],
        "autofill_files": ["Web Data", "Web Data-journal"],
        "session_files": ["Sessions", "Session Storage"],
    },
    "Firefox": {
        "base": os.path.join("AppData", "Roaming", "Mozilla", "Firefox", "Profiles"),
        "profiles": ["*"],  # Firefox uses random profile names
        "cache_dirs": ["cache2", "startupCache", "shader-cache"],
        "cookie_files": ["cookies.sqlite", "cookies.sqlite-wal"],
        "history_files": ["places.sqlite", "places.sqlite-wal", "formhistory.sqlite"],
        "autofill_files": ["formhistory.sqlite"],
        "session_files": ["sessionstore.jsonlz4", "sessionstore-backups"],
    },
}


class BrowserCleanup:
    """Detect and clean browser data."""

    def __init__(self, callback=None):
        self._callback = callback or (lambda msg, level="info": None)
        self._home = os.path.expanduser("~")

    def _log(self, msg, level="info"):
        getattr(logger, level, logger.info)(msg)
        self._callback(msg, level)

    def detect_installed_browsers(self):
        """
        Detect which browsers are installed.

        Returns:
            list[str]: Names of detected browsers
        """
        installed = []
        for browser, config in BROWSER_PATHS.items():
            base = os.path.join(self._home, config["base"])
            if os.path.exists(base):
                installed.append(browser)

        self._log(f"Detected browsers: {', '.join(installed) if installed else 'None'}")
        return installed

    def _get_profile_paths(self, browser):
        """Get actual profile directory paths for a browser."""
        config = BROWSER_PATHS.get(browser)
        if not config:
            return []

        base = os.path.join(self._home, config["base"])
        if not os.path.exists(base):
            return []

        paths = []
        for profile in config["profiles"]:
            if profile == "*":
                # Firefox: glob for profile dirs
                for p in glob.glob(os.path.join(base, "*.default*")):
                    if os.path.isdir(p):
                        paths.append(p)
                for p in glob.glob(os.path.join(base, "*.default-release*")):
                    if os.path.isdir(p):
                        paths.append(p)
            elif profile == "":
                paths.append(base)
            else:
                full = os.path.join(base, profile)
                if os.path.exists(full):
                    paths.append(full)

        return paths

    def _dir_size(self, path):
        """Get total size of a directory in bytes."""
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

    def _file_size(self, path):
        try:
            return os.path.getsize(path) if os.path.exists(path) else 0
        except (OSError, PermissionError):
            return 0

    def get_browser_sizes(self, browser):
        """
        Get data sizes for a browser.

        Returns:
            dict: {cache_bytes, cookies_bytes, history_bytes, autofill_bytes, total_bytes}
        """
        config = BROWSER_PATHS.get(browser)
        if not config:
            return {}

        profiles = self._get_profile_paths(browser)
        sizes = {"cache": 0, "cookies": 0, "history": 0, "autofill": 0}

        for profile_path in profiles:
            for cache_dir in config["cache_dirs"]:
                sizes["cache"] += self._dir_size(os.path.join(profile_path, cache_dir))

            for f in config["cookie_files"]:
                sizes["cookies"] += self._file_size(os.path.join(profile_path, f))

            for f in config["history_files"]:
                sizes["history"] += self._file_size(os.path.join(profile_path, f))

            for f in config["autofill_files"]:
                sizes["autofill"] += self._file_size(os.path.join(profile_path, f))

        total = sum(sizes.values())
        return {
            "cache_bytes": sizes["cache"],
            "cache_mb": round(sizes["cache"] / (1024**2), 1),
            "cookies_bytes": sizes["cookies"],
            "cookies_mb": round(sizes["cookies"] / (1024**2), 1),
            "history_bytes": sizes["history"],
            "history_mb": round(sizes["history"] / (1024**2), 1),
            "autofill_bytes": sizes["autofill"],
            "autofill_mb": round(sizes["autofill"] / (1024**2), 1),
            "total_bytes": total,
            "total_mb": round(total / (1024**2), 1),
        }

    def analyze_all(self):
        """
        Analyze all detected browsers.

        Returns:
            dict: {browsers: dict[str, sizes], total_mb, browsers_found}
        """
        self._log("Analyzing browser data...")
        installed = self.detect_installed_browsers()

        browsers = {}
        total = 0
        for browser in installed:
            sizes = self.get_browser_sizes(browser)
            browsers[browser] = sizes
            total += sizes.get("total_bytes", 0)

        self._log(
            f"Total browser data: {total / (1024**2):.1f} MB across {len(installed)} browsers"
        )
        return {
            "browsers": browsers,
            "total_bytes": total,
            "total_mb": round(total / (1024**2), 1),
            "browsers_found": len(installed),
        }

    def clean_cache(self, browser):
        """Clean cache for a browser. Returns (files_cleaned, bytes_freed)."""
        config = BROWSER_PATHS.get(browser)
        if not config:
            return 0, 0

        profiles = self._get_profile_paths(browser)
        files_cleaned = 0
        bytes_freed = 0

        for profile_path in profiles:
            for cache_dir in config["cache_dirs"]:
                cache_path = os.path.join(profile_path, cache_dir)
                if os.path.exists(cache_path):
                    size = self._dir_size(cache_path)
                    try:
                        shutil.rmtree(cache_path, ignore_errors=True)
                        bytes_freed += size
                        files_cleaned += 1
                        self._log(f"  Cleaned {browser} cache: {cache_dir}")
                    except (OSError, PermissionError):
                        pass

        return files_cleaned, bytes_freed

    def clean_cookies(self, browser):
        """Clean cookies for a browser. Returns (files_cleaned, bytes_freed)."""
        config = BROWSER_PATHS.get(browser)
        if not config:
            return 0, 0

        profiles = self._get_profile_paths(browser)
        files_cleaned = 0
        bytes_freed = 0

        for profile_path in profiles:
            for f in config["cookie_files"]:
                fpath = os.path.join(profile_path, f)
                if os.path.exists(fpath):
                    size = self._file_size(fpath)
                    try:
                        os.remove(fpath)
                        bytes_freed += size
                        files_cleaned += 1
                    except (OSError, PermissionError):
                        pass

        return files_cleaned, bytes_freed

    def clean_history(self, browser):
        """Clean history for a browser. Returns (files_cleaned, bytes_freed)."""
        config = BROWSER_PATHS.get(browser)
        if not config:
            return 0, 0

        profiles = self._get_profile_paths(browser)
        files_cleaned = 0
        bytes_freed = 0

        for profile_path in profiles:
            for f in config["history_files"]:
                fpath = os.path.join(profile_path, f)
                if os.path.exists(fpath):
                    size = self._file_size(fpath)
                    try:
                        os.remove(fpath)
                        bytes_freed += size
                        files_cleaned += 1
                    except (OSError, PermissionError):
                        pass

        return files_cleaned, bytes_freed

    def clean_autofill(self, browser):
        """Clean autofill data for a browser. Returns (files_cleaned, bytes_freed)."""
        config = BROWSER_PATHS.get(browser)
        if not config:
            return 0, 0

        profiles = self._get_profile_paths(browser)
        files_cleaned = 0
        bytes_freed = 0

        for profile_path in profiles:
            for f in config["autofill_files"]:
                fpath = os.path.join(profile_path, f)
                if os.path.exists(fpath):
                    size = self._file_size(fpath)
                    try:
                        os.remove(fpath)
                        bytes_freed += size
                        files_cleaned += 1
                    except (OSError, PermissionError):
                        pass

        return files_cleaned, bytes_freed

    def clean_browser(self, browser, cache=True, cookies=True, history=True, autofill=False):
        """
        Clean selected data for a browser.

        Returns:
            dict: {files_cleaned, bytes_freed, freed_mb}
        """
        self._log(f"Cleaning {browser}...")
        total_files = 0
        total_freed = 0

        if cache:
            f, b = self.clean_cache(browser)
            total_files += f
            total_freed += b

        if cookies:
            f, b = self.clean_cookies(browser)
            total_files += f
            total_freed += b

        if history:
            f, b = self.clean_history(browser)
            total_files += f
            total_freed += b

        if autofill:
            f, b = self.clean_autofill(browser)
            total_files += f
            total_freed += b

        self._log(
            f"  {browser}: {total_files} items cleaned, {total_freed / (1024**2):.1f} MB freed"
        )
        return {
            "files_cleaned": total_files,
            "bytes_freed": total_freed,
            "freed_mb": round(total_freed / (1024**2), 1),
        }

    def clean_all_browsers(self, cache=True, cookies=True, history=True, autofill=False):
        """
        Clean all detected browsers.

        Returns:
            dict: {per_browser: dict, total_freed_mb}
        """
        self._log("Cleaning all browsers...")
        installed = self.detect_installed_browsers()
        results = {}
        total_freed = 0

        for browser in installed:
            result = self.clean_browser(browser, cache, cookies, history, autofill)
            results[browser] = result
            total_freed += result["bytes_freed"]

        self._log(f"Total freed: {total_freed / (1024**2):.1f} MB")
        return {
            "per_browser": results,
            "total_freed_bytes": total_freed,
            "total_freed_mb": round(total_freed / (1024**2), 1),
        }
