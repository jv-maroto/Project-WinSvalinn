"""Selectable optimization groups — each is a list of sub-tweaks the user can
toggle individually (the same pattern as the GPU card).

Mirrors the monolithic ``optimize_visual_effects`` / ``optimize_network`` /
``optimize_ssd`` / ``apply_performance_tweaks`` engines, but exposes a per-tweak
``plan()`` (with applied-state) and ``apply()`` of only the selected ids.

Registry tweaks report their applied-state; command-based ones report ``None``
(unknown) since there's no cheap, reliable way to read them back.
"""

from __future__ import annotations

import platform
import subprocess

from winsvalinn.utils.registry_helper import set_registry

IS_WINDOWS = platform.system() == "Windows"
_NO_WIN = 0x08000000
if IS_WINDOWS:
    import winreg


def _read_reg(path: str, name: str):
    if not IS_WINDOWS:
        return None
    try:
        hive_name, sub = path.split("\\", 1)
        hive = winreg.HKEY_CURRENT_USER if hive_name == "HKCU" else winreg.HKEY_LOCAL_MACHINE
        key = winreg.OpenKey(hive, sub)
        try:
            val, _ = winreg.QueryValueEx(key, name)
        finally:
            winreg.CloseKey(key)
        return val
    except OSError:
        return None


def _reg(tid: str, label: str, path: str, name: str, type_: str, value: str) -> dict:
    def _apply() -> bool:
        ok, _msg = set_registry(path, name, value, type_)
        return ok

    def _applied():
        cur = _read_reg(path, name)
        if cur is None:
            return False
        if type_ == "REG_DWORD":
            try:
                return int(cur) == int(value)
            except (TypeError, ValueError):
                return False
        if type_ == "REG_BINARY":
            return True  # present == applied (don't parse the blob)
        return str(cur) == str(value)

    return {"id": tid, "label": label, "apply": _apply, "applied": _applied}


def _cmd(tid: str, label: str, args: list[str]) -> dict:
    def _apply() -> bool:
        try:
            return (
                subprocess.run(
                    args, capture_output=True, timeout=15, creationflags=_NO_WIN
                ).returncode
                == 0
            )
        except (OSError, subprocess.SubprocessError):
            return False

    return {"id": tid, "label": label, "apply": _apply, "applied": lambda: None}


_MM = r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"
_CDM = r"HKCU\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager"

GROUPS: dict[str, dict] = {
    "visual": {
        "title": "Efectos visuales",
        "tweaks": [
            _reg(
                "vfx",
                "Efectos visuales: máximo rendimiento",
                r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects",
                "VisualFXSetting",
                "REG_DWORD",
                "2",
            ),
            _reg(
                "anim",
                "Desactivar animaciones de ventanas",
                r"HKCU\Control Panel\Desktop\WindowMetrics",
                "MinAnimate",
                "REG_SZ",
                "0",
            ),
            _reg(
                "transp",
                "Desactivar transparencias",
                r"HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
                "EnableTransparency",
                "REG_DWORD",
                "0",
            ),
            _reg(
                "deskpref",
                "Optimizar preferencias de escritorio",
                r"HKCU\Control Panel\Desktop",
                "UserPreferencesMask",
                "REG_BINARY",
                "9012038010000000",
            ),
        ],
    },
    "network": {
        "title": "Red TCP/IP",
        "tweaks": [
            _cmd("flushdns", "Vaciar caché DNS", ["ipconfig", "/flushdns"]),
            _cmd("winsock", "Resetear catálogo Winsock", ["netsh", "winsock", "reset"]),
            _cmd(
                "autotune",
                "TCP auto-tuning = normal",
                ["netsh", "int", "tcp", "set", "global", "autotuninglevel=normal"],
            ),
            _cmd(
                "timestamps",
                "Activar TCP timestamps",
                ["netsh", "int", "tcp", "set", "global", "timestamps=enabled"],
            ),
            _reg(
                "nagle",
                "Desactivar Nagle (menos latencia)",
                r"HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters",
                "TcpNoDelay",
                "REG_DWORD",
                "1",
            ),
        ],
    },
    "ssd": {
        "title": "Optimización SSD",
        "tweaks": [
            _cmd(
                "superfetch",
                "Desactivar Superfetch (SysMain)",
                ["sc", "config", "SysMain", "start=", "disabled"],
            ),
            _cmd(
                "trim",
                "Activar soporte TRIM",
                ["fsutil", "behavior", "set", "DisableDeleteNotify", "0"],
            ),
            _cmd(
                "lastaccess",
                "Desactivar marca de último acceso",
                ["fsutil", "behavior", "set", "disablelastaccess", "1"],
            ),
        ],
    },
    "perf": {
        "title": "Tweaks de rendimiento",
        "tweaks": [
            _reg(
                "cortana",
                "Desactivar Cortana",
                r"HKLM\SOFTWARE\Policies\Microsoft\Windows\Windows Search",
                "AllowCortana",
                "REG_DWORD",
                "0",
            ),
            _reg(
                "tips",
                "Desactivar consejos y sugerencias",
                _CDM,
                "SubscribedContent-338389Enabled",
                "REG_DWORD",
                "0",
            ),
            _reg(
                "lockscreen",
                "Desactivar tips de pantalla de bloqueo",
                _CDM,
                "RotatingLockScreenOverlayEnabled",
                "REG_DWORD",
                "0",
            ),
            _reg(
                "startsug",
                "Desactivar sugerencias del menú Inicio",
                _CDM,
                "SystemPaneSuggestionsEnabled",
                "REG_DWORD",
                "0",
            ),
            _reg(
                "bgapps",
                "Desactivar apps en segundo plano",
                r"HKCU\Software\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications",
                "GlobalUserDisabled",
                "REG_DWORD",
                "1",
            ),
            _reg(
                "mouseaccel",
                "Desactivar aceleración del ratón",
                r"HKCU\Control Panel\Mouse",
                "MouseSpeed",
                "REG_SZ",
                "0",
            ),
            _reg(
                "prio",
                "Prioridad a apps en primer plano",
                r"HKLM\SYSTEM\CurrentControlSet\Control\PriorityControl",
                "Win32PrioritySeparation",
                "REG_DWORD",
                "38",
            ),
            _reg(
                "sysresp",
                "Maximizar capacidad de respuesta del sistema",
                _MM,
                "SystemResponsiveness",
                "REG_DWORD",
                "0",
            ),
            _reg(
                "gpuprio",
                "Prioridad de hilo GPU para juegos",
                _MM + r"\Tasks\Games",
                "GPU Priority",
                "REG_DWORD",
                "8",
            ),
            _reg(
                "gameprio",
                "Prioridad alta de tareas de juego",
                _MM + r"\Tasks\Games",
                "Priority",
                "REG_DWORD",
                "6",
            ),
            _reg(
                "gamesched",
                "Programación de juegos = alta",
                _MM + r"\Tasks\Games",
                "Scheduling Category",
                "REG_SZ",
                "High",
            ),
            _cmd(
                "hibernate",
                "Desactivar hibernación (libera disco)",
                ["powercfg", "/hibernate", "off"],
            ),
        ],
    },
}


def plan(group: str) -> dict:
    """Group title + its tweaks with applied-state (no changes made)."""
    g = GROUPS.get(group)
    if not g:
        return {"title": group, "tweaks": []}
    return {
        "title": g["title"],
        "tweaks": [
            {"id": t["id"], "label": t["label"], "applied": t["applied"]()} for t in g["tweaks"]
        ],
    }


def apply(group: str, selected: list[str] | None = None) -> dict:
    """Apply the selected tweak ids of a group (or all when ``selected`` is None)."""
    g = GROUPS.get(group)
    if not g:
        return {"ok": False, "applied": 0, "error": "unknown_group", "actions": []}
    chosen = set(selected) if selected is not None else None
    actions: list[str] = []
    for t in g["tweaks"]:
        if chosen is not None and t["id"] not in chosen:
            continue
        if t["apply"]():
            actions.append(t["label"])
    return {"ok": bool(actions), "applied": len(actions), "actions": actions}
