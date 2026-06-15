"""Run-as-administrator helpers.

Lets the app report whether it's elevated and toggle a persistent
"always launch as Administrator" flag for the desktop executable. The flag is
Windows' per-exe RUNASADMIN compatibility layer (HKCU — no admin needed to set),
which makes Windows always launch that .exe elevated (with a UAC prompt).

The "app exe" is the parent process of the sidecar (the Tauri shell that
spawned it); in dev (sidecar launched from a terminal) it resolves to the
launcher instead, which is fine — the toggle just won't apply to the real app.
"""

from __future__ import annotations

import os
import platform

IS_WINDOWS = platform.system() == "Windows"
if IS_WINDOWS:
    import winreg

_LAYERS = r"Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers"


def is_admin() -> bool:
    if not IS_WINDOWS:
        return False
    try:
        import ctypes

        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:  # noqa: BLE001
        return False


def _app_exe() -> str | None:
    """Best-effort path to the desktop app exe (parent of the sidecar)."""
    try:
        import psutil

        return psutil.Process(os.getppid()).exe()
    except Exception:  # noqa: BLE001
        return None


def status() -> dict:
    """Return current elevation + whether 'always admin' is set for the app."""
    exe = _app_exe()
    always = False
    if IS_WINDOWS and exe:
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _LAYERS)
            try:
                val, _ = winreg.QueryValueEx(key, exe)
            finally:
                winreg.CloseKey(key)
            always = "RUNASADMIN" in str(val)
        except OSError:
            always = False
    return {"is_admin": is_admin(), "always_admin": always, "exe": exe}


def set_always_admin(enabled: bool) -> dict:
    """Enable/disable the always-run-as-admin flag for the app exe (HKCU)."""
    exe = _app_exe()
    if not IS_WINDOWS or not exe:
        return {"ok": False, "error": "app_exe_not_found", "always_admin": False}
    try:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, _LAYERS)
        try:
            if enabled:
                winreg.SetValueEx(key, exe, 0, winreg.REG_SZ, "~ RUNASADMIN")
            else:
                try:
                    winreg.DeleteValue(key, exe)
                except FileNotFoundError:
                    pass
        finally:
            winreg.CloseKey(key)
        return {"ok": True, "always_admin": enabled, "exe": exe}
    except OSError as exc:
        return {"ok": False, "error": str(exc), "always_admin": False}
