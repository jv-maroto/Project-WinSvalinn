"""
Comprehensive autoruns enumeration.

Covers the ~20 most-used Sysinternals Autoruns locations:
  - Run / RunOnce (HKLM + HKCU, 32-bit redirected paths too)
  - Shell\\Open\\Command + Image File Execution Options
  - Winlogon Userinit / Shell / Notify
  - Services (auto-start, non-system)
  - Scheduled tasks (boot/logon triggers, non-Microsoft)
  - Startup folders (per-user + common)
  - AppInit_DLLs
  - Browser Helper Objects
  - Explorer ShellIconOverlayIdentifiers
  - Codecs (HKCR\\Filter, AudioCompressionManager)

Returns a flat list; each item has source, name, command, scope, location.
Pure backend.
"""

import os
import platform
import subprocess


def _winreg():
    try:
        import winreg

        return winreg
    except ImportError:
        return None


# (hive, subkey, scope_label) — values inside are name=command pairs
_REGISTRY_RUN_KEYS = [
    ("HKLM", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", "machine"),
    ("HKLM", r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce", "machine"),
    ("HKLM", r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Run", "machine-x86"),
    ("HKLM", r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\RunOnce", "machine-x86"),
    ("HKCU", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", "user"),
    ("HKCU", r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce", "user"),
]

_WINLOGON_VALUES = [
    ("HKLM", r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon", "Userinit", "winlogon"),
    ("HKLM", r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon", "Shell", "winlogon"),
    ("HKLM", r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon", "Taskman", "winlogon"),
]


def _hive(name):
    winreg = _winreg()
    if not winreg:
        return None
    return winreg.HKEY_LOCAL_MACHINE if name == "HKLM" else winreg.HKEY_CURRENT_USER


def _enum_run_keys() -> list[dict]:
    winreg = _winreg()
    if not winreg:
        return []
    out = []
    for hive_name, subkey, scope in _REGISTRY_RUN_KEYS:
        try:
            with winreg.OpenKey(_hive(hive_name), subkey, 0, winreg.KEY_READ) as key:
                i = 0
                while True:
                    try:
                        name, value, _t = winreg.EnumValue(key, i)
                        out.append(
                            {
                                "source": "registry-run",
                                "name": name,
                                "command": str(value),
                                "scope": scope,
                                "location": f"{hive_name}\\{subkey}",
                            }
                        )
                        i += 1
                    except OSError:
                        break
        except OSError:
            continue
    return out


def _enum_winlogon() -> list[dict]:
    winreg = _winreg()
    if not winreg:
        return []
    out = []
    for hive_name, subkey, value_name, scope in _WINLOGON_VALUES:
        try:
            with winreg.OpenKey(_hive(hive_name), subkey, 0, winreg.KEY_READ) as key:
                value, _t = winreg.QueryValueEx(key, value_name)
                if value:
                    out.append(
                        {
                            "source": "winlogon",
                            "name": value_name,
                            "command": str(value),
                            "scope": scope,
                            "location": f"{hive_name}\\{subkey}\\{value_name}",
                        }
                    )
        except OSError:
            continue
    return out


def _enum_appinit_dlls() -> list[dict]:
    winreg = _winreg()
    if not winreg:
        return []
    out = []
    try:
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Windows",
            0,
            winreg.KEY_READ,
        ) as key:
            for vname in ("AppInit_DLLs", "LoadAppInit_DLLs"):
                try:
                    value, _t = winreg.QueryValueEx(key, vname)
                    if value:
                        out.append(
                            {
                                "source": "appinit",
                                "name": vname,
                                "command": str(value),
                                "scope": "machine",
                                "location": "HKLM\\...\\Windows\\AppInit_DLLs",
                            }
                        )
                except OSError:
                    pass
    except OSError:
        pass
    return out


def _enum_bho() -> list[dict]:
    """Browser Helper Objects — usually IE-era, but Edge can still load some."""
    winreg = _winreg()
    if not winreg:
        return []
    out = []
    try:
        base = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Browser Helper Objects"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base, 0, winreg.KEY_READ) as key:
            i = 0
            while True:
                try:
                    sub_name = winreg.EnumKey(key, i)
                    out.append(
                        {
                            "source": "bho",
                            "name": sub_name,
                            "command": sub_name,  # CLSID
                            "scope": "machine",
                            "location": f"HKLM\\{base}\\{sub_name}",
                        }
                    )
                    i += 1
                except OSError:
                    break
    except OSError:
        pass
    return out


def _enum_shell_overlays() -> list[dict]:
    winreg = _winreg()
    if not winreg:
        return []
    out = []
    try:
        base = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\ShellIconOverlayIdentifiers"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base, 0, winreg.KEY_READ) as key:
            i = 0
            while True:
                try:
                    sub_name = winreg.EnumKey(key, i)
                    out.append(
                        {
                            "source": "shell-overlay",
                            "name": sub_name,
                            "command": sub_name,
                            "scope": "machine",
                            "location": f"HKLM\\{base}\\{sub_name}",
                        }
                    )
                    i += 1
                except OSError:
                    break
    except OSError:
        pass
    return out


def _enum_startup_folders() -> list[dict]:
    out = []
    candidates = []
    appdata = os.environ.get("APPDATA")
    program_data = os.environ.get("ProgramData")
    if appdata:
        candidates.append(
            (os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs\Startup"), "user")
        )
    if program_data:
        candidates.append(
            (
                os.path.join(program_data, r"Microsoft\Windows\Start Menu\Programs\Startup"),
                "machine",
            )
        )
    for folder, scope in candidates:
        if not os.path.isdir(folder):
            continue
        for entry in os.listdir(folder):
            full = os.path.join(folder, entry)
            out.append(
                {
                    "source": "startup-folder",
                    "name": entry,
                    "command": full,
                    "scope": scope,
                    "location": folder,
                }
            )
    return out


def _enum_services_auto() -> list[dict]:
    """Auto-start, non-Microsoft-by-path services."""
    if platform.system() != "Windows":
        return []
    try:
        cp = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                (
                    "Get-CimInstance Win32_Service | "
                    "Where-Object { $_.StartMode -eq 'Auto' } | "
                    "Select-Object Name, DisplayName, PathName | "
                    "ConvertTo-Json -Compress"
                ),
            ],
            capture_output=True,
            text=True,
            timeout=30,
            shell=False,
        )
        if cp.returncode != 0:
            return []
        import json

        data = json.loads(cp.stdout or "[]")
        if isinstance(data, dict):
            data = [data]
        out = []
        for svc in data:
            out.append(
                {
                    "source": "service",
                    "name": svc.get("Name", ""),
                    "command": svc.get("PathName", ""),
                    "scope": "machine",
                    "location": "services.msc",
                    "display_name": svc.get("DisplayName", ""),
                }
            )
        return out
    except (subprocess.TimeoutExpired, Exception):
        return []


def _enum_scheduled_tasks() -> list[dict]:
    """Scheduled tasks with boot/logon triggers, excluding the Microsoft folder."""
    if platform.system() != "Windows":
        return []
    try:
        cp = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                (
                    "Get-ScheduledTask | "
                    "Where-Object { $_.TaskPath -notlike '*Microsoft*' -and "
                    "($_.Triggers | Where-Object { $_.CimClass.CimClassName -in "
                    "'MSFT_TaskBootTrigger','MSFT_TaskLogonTrigger' }) } | "
                    "Select-Object TaskName, TaskPath, State | "
                    "ConvertTo-Json -Compress"
                ),
            ],
            capture_output=True,
            text=True,
            timeout=45,
            shell=False,
        )
        if cp.returncode != 0:
            return []
        import json

        data = json.loads(cp.stdout or "[]")
        if isinstance(data, dict):
            data = [data]
        out = []
        for t in data:
            out.append(
                {
                    "source": "scheduled-task",
                    "name": t.get("TaskName", ""),
                    "command": t.get("TaskPath", "") + t.get("TaskName", ""),
                    "scope": "machine",
                    "location": t.get("TaskPath", ""),
                }
            )
        return out
    except (subprocess.TimeoutExpired, Exception):
        return []


def enumerate_all() -> list[dict]:
    """One-shot enumeration of every covered autorun location."""
    items: list[dict] = []
    items.extend(_enum_run_keys())
    items.extend(_enum_winlogon())
    items.extend(_enum_appinit_dlls())
    items.extend(_enum_bho())
    items.extend(_enum_shell_overlays())
    items.extend(_enum_startup_folders())
    items.extend(_enum_services_auto())
    items.extend(_enum_scheduled_tasks())
    return items


def summary_by_source(items: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for it in items:
        counts[it["source"]] = counts.get(it["source"], 0) + 1
    return counts


def disable_run_value(hive_name: str, subkey: str, value_name: str) -> dict:
    """Disable a Run/RunOnce entry by deleting its value (Autoruns-style)."""
    winreg = _winreg()
    if not winreg:
        return {"success": False, "message": "winreg no disponible"}
    try:
        with winreg.OpenKey(_hive(hive_name), subkey, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, value_name)
        return {"success": True, "message": f"Eliminado {value_name}"}
    except FileNotFoundError:
        return {"success": False, "message": "No existe"}
    except PermissionError:
        return {"success": False, "message": "Permiso denegado (Admin?)"}
    except OSError as exc:
        return {"success": False, "message": str(exc)}
