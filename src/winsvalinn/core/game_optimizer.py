"""
Game / Streaming Optimizer - WinSvalinn

Backend engine for the native "gaming" options (migrated from the legacy
``plugin_gaming``, ``plugin_lol`` and ``plugin_streaming`` filesystem plugins).

No GUI imports — fully testable headless. All system mutation goes through
``winsvalinn.utils.registry_helper.set_registry`` (which honours dry-run and the
backup/changelog safety net) or ``subprocess.run(..., shell=False)``.

Every public method follows the callback-logging pattern used across
``winsvalinn.core``: a ``callback(msg, level)`` supplied at construction time.
Methods return plain dicts and never raise — failures are logged and surfaced
via the returned dict so the options layer can build a stable JSON response.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from winsvalinn.utils.registry_helper import set_registry

CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

# Ultimate Performance power scheme GUID (hidden Windows plan).
ULTIMATE_PERF_GUID = "e9a42b02-d5df-448d-aa00-03f14749eb61"

# Background processes that are safe to terminate during a gaming session.
KILLABLE_PROCESSES: tuple[str, ...] = (
    "OneDrive.exe",
    "Teams.exe",
    "Spotify.exe",
    "Discord.exe",
    "Slack.exe",
    "Skype.exe",
    "YourPhone.exe",
    "PhoneExperienceHost.exe",
    "SearchApp.exe",
    "SearchUI.exe",
    "Cortana.exe",
    "HxTsr.exe",
    "HxOutlook.exe",
    "HxCalendarAppImm.exe",
    "WidgetService.exe",
    "Widgets.exe",
    "GameBar.exe",
    "GameBarPresenceWriter.exe",
)

# Overlay processes that can cause frame drops while streaming.
OVERLAY_PROCESSES: tuple[str, ...] = (
    "DiscordHook",
    "nvspcaps64",
    "GameOverlayUI",
)

# Known gaming-platform install locations (first existing path wins).
PLATFORM_PATHS: dict[str, list[str]] = {
    "Steam": [
        r"C:\Program Files (x86)\Steam",
        r"C:\Program Files\Steam",
    ],
    "Epic Games": [
        r"C:\Program Files\Epic Games",
        r"C:\Program Files (x86)\Epic Games",
    ],
    "GOG Galaxy": [
        r"C:\Program Files (x86)\GOG Galaxy",
    ],
    "Xbox": [
        os.path.join(
            os.environ.get("LOCALAPPDATA", ""),
            "Packages",
            "Microsoft.GamingApp_8wekyb3d8bbwe",
        ),
    ],
    "EA App": [
        r"C:\Program Files\Electronic Arts",
    ],
    "Ubisoft Connect": [
        r"C:\Program Files (x86)\Ubisoft\Ubisoft Game Launcher",
    ],
}

# Directories whose contents are GPU shader caches (safe to delete).
SHADER_CACHE_DIRS: tuple[tuple[str, ...], ...] = (
    ("AppData", "Local", "D3DSCache"),
    ("AppData", "Local", "NVIDIA", "DXCache"),
    ("AppData", "Local", "NVIDIA", "GLCache"),
    ("AppData", "Local", "AMD", "DxCache"),
)


class GameOptimizer:
    """Apply gaming, League of Legends and OBS/streaming optimizations."""

    def __init__(self, callback: Callable[[str, str], None] | None = None) -> None:
        self.callback = callback or (lambda msg, level="info": None)
        self.is_windows = platform.system() == "Windows"

    def log(self, message: str, level: str = "info") -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.callback(f"[{timestamp}] {message}", level)

    # ─── Internal helpers ───────────────────────────────────────────────

    def _run(self, args: list[str], timeout: int = 15) -> subprocess.CompletedProcess | None:
        """Run a command with shell=False; return the result or None on failure."""
        try:
            return subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=timeout,
                creationflags=CREATE_NO_WINDOW,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
            self.log(f"Command failed ({args[0]}): {exc}", "error")
            return None

    def _set_reg(self, path: str, name: str, value, value_type: str = "REG_DWORD") -> bool:
        """Set a registry value via the safety-net helper; log the outcome."""
        success, msg = set_registry(path, name, value, value_type, tag="gaming")
        self.log(f"  {msg}", "success" if success else "warning")
        return success

    # ─── Platform detection (read-only) ─────────────────────────────────

    def detect_platforms(self) -> dict:
        """Detect installed gaming platforms by checking known paths."""
        self.log("Detecting gaming platforms...", "info")
        found: list[dict] = []
        for name, paths in PLATFORM_PATHS.items():
            for raw in paths:
                if raw and os.path.exists(raw):
                    found.append({"platform": name, "path": raw})
                    self.log(f"  Found: {name} ({raw})", "success")
                    break
        if not found:
            self.log("No gaming platforms detected", "info")
        else:
            self.log(f"Detected {len(found)} platform(s)", "success")
        return {"success": True, "platforms": found, "count": len(found)}

    # ─── Process control ────────────────────────────────────────────────

    def kill_background(self) -> dict:
        """Terminate non-essential background processes to free resources."""
        self.log("Killing background processes...", "warning")
        killed: list[str] = []
        for proc in KILLABLE_PROCESSES:
            result = self._run(["taskkill", "/f", "/im", proc])
            out = (result.stdout if result else "").upper()
            if result and ("SUCCESS" in out or "XITO" in out):
                self.log(f"  Killed: {proc}", "success")
                killed.append(proc)
        self.log(f"Killed {len(killed)} process(es)", "success")
        return {"success": True, "killed": killed, "count": len(killed)}

    def kill_overlays(self) -> dict:
        """Terminate streaming overlay processes that can cause frame drops."""
        self.log("Killing overlay processes...", "warning")
        killed: list[str] = []
        for proc in OVERLAY_PROCESSES:
            # taskkill image-name wildcard matches e.g. "nvspcaps64.exe".
            result = self._run(["taskkill", "/f", "/im", f"{proc}*"])
            out = (result.stdout if result else "").upper()
            if result and ("SUCCESS" in out or "XITO" in out):
                self.log(f"  Killed overlay: {proc}", "success")
                killed.append(proc)
        self.log(f"Killed {len(killed)} overlay(s)", "success")
        return {"success": True, "killed": killed, "count": len(killed)}

    # ─── Windows gaming features ────────────────────────────────────────

    def enable_game_mode(self) -> dict:
        """Enable Windows Game Mode and Hardware GPU Scheduling."""
        self.log("Enabling Game Mode + GPU scheduling...", "info")
        ok = True
        ok &= self._set_reg(r"HKCU\Software\Microsoft\GameBar", "AllowAutoGameMode", "1")
        ok &= self._set_reg(r"HKCU\Software\Microsoft\GameBar", "AutoGameModeEnabled", "1")
        ok &= self._set_reg(
            r"HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers", "HwSchMode", "2"
        )
        self.log("Game Mode and GPU Scheduling configured", "success" if ok else "warning")
        return {"success": ok}

    def apply_game_priority(self) -> dict:
        """Prioritize the 'Games' multimedia scheduling task."""
        self.log("Applying game scheduling priority...", "info")
        base = (
            r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion"
            r"\Multimedia\SystemProfile\Tasks\Games"
        )
        ok = True
        ok &= self._set_reg(base, "Priority", "6", "REG_DWORD")
        ok &= self._set_reg(base, "Scheduling Category", "High", "REG_SZ")
        ok &= self._set_reg(base, "SFIO Priority", "High", "REG_SZ")
        ok &= self._set_reg(base, "GPU Priority", "8", "REG_DWORD")
        self.log("Game priority configured", "success" if ok else "warning")
        return {"success": ok}

    # ─── Network ────────────────────────────────────────────────────────

    def optimize_network(self) -> dict:
        """Disable Nagle's algorithm on every NIC and raise throttling index."""
        self.log("Optimizing network for low latency...", "info")
        ifaces = self._enum_network_interfaces()
        applied = 0
        for subkey in ifaces:
            if self._set_reg(subkey, "TcpAckFrequency", "1"):
                applied += 1
            self._set_reg(subkey, "TCPNoDelay", "1")
            self._set_reg(subkey, "TcpDelAckTicks", "0")
        # Global throttling index (0xFFFFFFFF disables throttling).
        ok = self._set_reg(
            r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile",
            "NetworkThrottlingIndex",
            "4294967295",
            "REG_DWORD",
        )
        self.log(f"Network optimized ({applied} interface(s))", "success")
        return {"success": ok, "interfaces": applied}

    def _enum_network_interfaces(self) -> list[str]:
        """Return reg paths for every TCP/IP interface, or the parent on failure."""
        base = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces"
        full_base = f"HKLM\\{base}"
        if not self.is_windows:
            return [full_base]
        try:
            import winreg

            key = winreg.OpenKeyEx(
                winreg.HKEY_LOCAL_MACHINE,
                base,
                0,
                winreg.KEY_READ | winreg.KEY_WOW64_64KEY,
            )
            subkeys: list[str] = []
            i = 0
            while True:
                try:
                    iface = winreg.EnumKey(key, i)
                    subkeys.append(f"{full_base}\\{iface}")
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
            return subkeys or [full_base]
        except OSError as exc:
            self.log(f"Interface enumeration failed: {exc}", "warning")
            return [full_base]

    # ─── Power plan ─────────────────────────────────────────────────────

    def enable_ultimate_performance(self) -> dict:
        """Create and activate the hidden Ultimate Performance power plan."""
        self.log("Enabling Ultimate Performance power plan...", "info")
        # Duplicate the scheme (idempotent: harmless if it already exists).
        self._run(["powercfg", "-duplicatescheme", ULTIMATE_PERF_GUID])
        result = self._run(["powercfg", "-setactive", ULTIMATE_PERF_GUID])
        ok = bool(result and result.returncode == 0)
        if ok:
            self.log("Ultimate Performance plan activated", "success")
        else:
            self.log("Could not activate Ultimate Performance plan", "warning")
        return {"success": ok}

    # ─── Shader cache cleanup ───────────────────────────────────────────

    def clean_shader_cache(self) -> dict:
        """Delete DirectX / NVIDIA / AMD shader caches; report freed space."""
        self.log("Cleaning shader caches...", "info")
        home = Path(os.path.expanduser("~"))
        freed = 0
        cleaned: list[str] = []
        for parts in SHADER_CACHE_DIRS:
            path = home.joinpath(*parts)
            if not path.exists():
                continue
            size = self._dir_size(path)
            shutil.rmtree(path, ignore_errors=True)
            freed += size
            cleaned.append(path.name)
            self.log(f"  Cleaned: {path.name} ({size / (1024**2):.1f} MB)", "info")
        self.log(f"Total freed: {freed / (1024**2):.1f} MB", "success")
        return {"success": True, "freed_bytes": freed, "cleaned": cleaned}

    @staticmethod
    def _dir_size(path: Path) -> int:
        total = 0
        for dirpath, _dirs, files in os.walk(path):
            for f in files:
                try:
                    total += os.path.getsize(os.path.join(dirpath, f))
                except OSError:
                    pass
        return total

    # ─── League of Legends ──────────────────────────────────────────────

    def apply_lol_display(self) -> dict:
        """Disable fullscreen optimizations + High DPI override for LoL exes."""
        self.log("Applying LoL display optimizations...", "info")
        exes = self._find_lol_exes()
        applied = 0
        for exe_name, exe_path in exes.items():
            if exe_path is None:
                self.log(f"  {exe_name} not found — skipped", "warning")
                continue
            ok = self._set_reg(
                r"HKCU\SOFTWARE\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers",
                exe_path,
                "~ DISABLEDXMAXIMIZEDWINDOWEDMODE HIGHDPIAWARE",
                "REG_SZ",
            )
            if ok:
                applied += 1
        self.log("LoL display optimizations done", "success")
        return {"success": True, "applied": applied}

    def apply_lol_client_settings(self) -> dict:
        """Enable Low Spec Mode + Close Client During Game in PersistedSettings.json."""
        self.log("Applying LoL client settings...", "info")
        paths = self._find_lol_persisted_settings()
        if not paths:
            self.log("PersistedSettings.json not found", "warning")
            return {"success": False, "updated": []}
        updated: list[str] = []
        for p in paths:
            try:
                with open(p, encoding="utf-8") as f:
                    data = json.load(f)
                files = data.setdefault("files", {})
                gs = files.setdefault("GamePersistentSettings", {})
                gs["LowSpecMode"] = "1"
                gs["CloseClientDuringGame"] = "1"
                with open(p, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                updated.append(p)
                self.log(f"  Updated {p}", "success")
            except (OSError, ValueError) as exc:
                self.log(f"  Failed {p}: {exc}", "error")
        self.log("LoL client settings done", "success")
        return {"success": bool(updated), "updated": updated}

    def _find_lol_exes(self) -> dict[str, str | None]:
        exes: dict[str, str | None] = {"LeagueClient.exe": None, "League of Legends.exe": None}
        for drive in ("C", "D", "E"):
            base = f"{drive}:\\Riot Games\\League of Legends"
            if not os.path.isdir(base):
                continue
            for root, _dirs, files in os.walk(base):
                for f in files:
                    if f in exes and exes[f] is None:
                        exes[f] = os.path.join(root, f)
        return exes

    def _find_lol_persisted_settings(self) -> list[str]:
        candidates: list[str] = []
        for drive in ("C", "D", "E"):
            base = f"{drive}:\\Riot Games\\League of Legends"
            if not os.path.isdir(base):
                continue
            for root, _dirs, files in os.walk(base):
                for f in files:
                    if f.lower() == "persistedsettings.json":
                        candidates.append(os.path.join(root, f))
        return candidates

    # ─── OBS / streaming ────────────────────────────────────────────────

    def apply_obs_priority(self) -> dict:
        """Raise obs64.exe CPU priority to Above Normal via the IFEO key."""
        self.log("Applying OBS CPU priority...", "info")
        subkey = (
            r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion"
            r"\Image File Execution Options\obs64.exe\PerfOptions"
        )
        ok = self._set_reg(subkey, "CpuPriorityClass", "3")
        self.log("OBS priority done", "success" if ok else "warning")
        return {"success": ok}

    def apply_obs_dynamic_bitrate(self) -> dict:
        """Enable Dynamic Bitrate in the OBS Studio global.ini config."""
        self.log("Enabling OBS Dynamic Bitrate...", "info")
        obs_dir = os.path.join(os.environ.get("APPDATA", ""), "obs-studio")
        global_ini = os.path.join(obs_dir, "global.ini")
        if not os.path.isdir(obs_dir):
            self.log("OBS Studio config dir not found", "warning")
            return {"success": False}
        try:
            lines: list[str] = []
            if os.path.isfile(global_ini):
                with open(global_ini, encoding="utf-8") as f:
                    lines = f.readlines()
            found = False
            for i, line in enumerate(lines):
                if "DynamicBitrate" in line:
                    lines[i] = "DynamicBitrate=true\n"
                    found = True
                    break
            if not found:
                lines.append("\n[Output]\n")
                lines.append("DynamicBitrate=true\n")
            with open(global_ini, "w", encoding="utf-8") as f:
                f.writelines(lines)
            self.log(f"Updated {global_ini}", "success")
            return {"success": True, "path": global_ini}
        except OSError as exc:
            self.log(f"Failed: {exc}", "error")
            return {"success": False}

    def detect_encoder(self) -> dict:
        """Detect the GPU brand and recommend an OBS encoder (read-only)."""
        self.log("Detecting GPU for encoder recommendation...", "info")
        brand = "unknown"
        if self.is_windows:
            result = self._run(
                [
                    "powershell",
                    "-Command",
                    "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name",
                ],
            )
            lower = (result.stdout if result else "").lower()
            if "nvidia" in lower or "geforce" in lower or "rtx" in lower or "gtx" in lower:
                brand = "nvidia"
            elif "amd" in lower or "radeon" in lower:
                brand = "amd"
            elif "intel" in lower:
                brand = "intel"
        recommendations = {
            "nvidia": "Use NVENC H.264, CQP 18-20, Preset Quality, Profile High, Look-ahead ON.",
            "amd": "Use AMF H.264, CQP 18-20, Quality Preset, High Profile.",
            "intel": "Use QSV H.264 if available, otherwise x264 Medium.",
            "unknown": "Could not detect GPU — use x264 with Medium preset as fallback.",
        }
        recommendation = recommendations[brand]
        self.log(f"GPU brand: {brand} — {recommendation}", "success")
        return {"success": True, "brand": brand, "recommendation": recommendation}

    # ─── Aggregate profiles ─────────────────────────────────────────────

    def apply_gaming_profile(self) -> dict:
        """Run the full generic gaming optimization pass (plugin_gaming 'Apply All')."""
        self.log("=== Applying gaming profile ===", "warning")
        self.kill_background()
        self.enable_game_mode()
        self.optimize_network()
        self.enable_ultimate_performance()
        self.clean_shader_cache()
        self.log("=== Gaming profile applied ===", "success")
        return {"success": True}

    def apply_lol_profile(self) -> dict:
        """Run the full League of Legends optimization pass (plugin_lol 'Apply All')."""
        self.log("=== Applying League of Legends profile ===", "warning")
        self.optimize_network()
        self.apply_game_priority()
        self.apply_lol_display()
        self.enable_game_mode()
        self.apply_lol_client_settings()
        self.log("=== League of Legends profile applied ===", "success")
        return {"success": True}

    def apply_streaming_profile(self) -> dict:
        """Run the full OBS/streaming optimization pass (plugin_streaming 'Apply All')."""
        self.log("=== Applying streaming profile ===", "warning")
        self.apply_obs_priority()
        self.optimize_network()
        self.apply_obs_dynamic_bitrate()
        self.enable_ultimate_performance()
        self.enable_game_mode()
        self.log("=== Streaming profile applied ===", "success")
        return {"success": True}
