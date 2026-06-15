"""
UI Tweaks engine — Windows 11 Start menu, Taskbar, Explorer and context menus.

Migrated from the legacy ``plugin_tweaks_ui`` plugin. No GUI imports: registry
writes happen through :mod:`winreg` and Explorer is restarted via subprocess
(``shell=False``). Each tweak is idempotent (it just writes a fixed value) and
failures are reported via the optional ``callback`` instead of raising.
"""

from __future__ import annotations

import platform
import subprocess
from collections.abc import Callable
from datetime import datetime

IS_WINDOWS = platform.system() == "Windows"
if IS_WINDOWS:
    import winreg

# Registry op tuple: (hive, subkey, value_name, value, kind)
# hive: "HKCU" | "HKLM"; kind: "DWORD" | "SZ"
RegOp = tuple

# Each tweak: id -> {"label", "ops": [RegOp, ...]}
TWEAKS: dict[str, dict] = {
    "start_left": {
        "label": "Alinear menú Inicio a la izquierda",
        "ops": [
            (
                "HKCU",
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
                "TaskbarAl",
                0,
                "DWORD",
            ),
        ],
    },
    "hide_search": {
        "label": "Ocultar barra de búsqueda en taskbar",
        "ops": [
            (
                "HKCU",
                r"Software\Microsoft\Windows\CurrentVersion\Search",
                "SearchboxTaskbarMode",
                0,
                "DWORD",
            ),
        ],
    },
    "hide_widgets": {
        "label": "Ocultar Widgets",
        "ops": [
            (
                "HKCU",
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
                "TaskbarDa",
                0,
                "DWORD",
            ),
        ],
    },
    "hide_taskview": {
        "label": "Ocultar Task View",
        "ops": [
            (
                "HKCU",
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
                "ShowTaskViewButton",
                0,
                "DWORD",
            ),
        ],
    },
    "hide_chat": {
        "label": "Ocultar icono Chat (Teams)",
        "ops": [
            (
                "HKCU",
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
                "TaskbarMn",
                0,
                "DWORD",
            ),
        ],
    },
    "classic_context": {
        "label": "Restaurar menú contextual clásico (Win10)",
        "ops": [
            # Setting the (default) value to "" enables the legacy menu.
            (
                "HKCU",
                r"Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32",
                "",
                "",
                "SZ",
            ),
        ],
    },
    "show_extensions": {
        "label": "Mostrar extensiones de archivo",
        "ops": [
            (
                "HKCU",
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
                "HideFileExt",
                0,
                "DWORD",
            ),
        ],
    },
    "show_hidden": {
        "label": "Mostrar archivos y carpetas ocultos",
        "ops": [
            (
                "HKCU",
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
                "Hidden",
                1,
                "DWORD",
            ),
        ],
    },
    "disable_bing_search": {
        "label": "Desactivar búsqueda Bing en menú Inicio",
        "ops": [
            (
                "HKCU",
                r"Software\Microsoft\Windows\CurrentVersion\Search",
                "BingSearchEnabled",
                0,
                "DWORD",
            ),
            (
                "HKCU",
                r"Software\Microsoft\Windows\CurrentVersion\Search",
                "CortanaConsent",
                0,
                "DWORD",
            ),
        ],
    },
    "small_taskbar": {
        "label": "Taskbar más pequeña",
        "ops": [
            (
                "HKCU",
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
                "TaskbarSi",
                0,
                "DWORD",
            ),
        ],
    },
}


class UITweaks:
    """Apply Windows 11 UI registry tweaks (Start/Taskbar/Explorer)."""

    def __init__(self, callback: Callable[[str, str], None] | None = None) -> None:
        self.callback = callback or (lambda msg, level="info": None)
        self.is_windows = IS_WINDOWS

    def log(self, message: str, level: str = "info") -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.callback(f"[{timestamp}] {message}", level)

    def _apply_op(self, op: RegOp) -> bool:
        """Apply a single registry op. Returns True on success."""
        hive_name, subkey, vname, value, kind = op
        try:
            hive = winreg.HKEY_CURRENT_USER if hive_name == "HKCU" else winreg.HKEY_LOCAL_MACHINE
            key = winreg.CreateKey(hive, subkey)
            try:
                if kind == "DWORD":
                    winreg.SetValueEx(key, vname, 0, winreg.REG_DWORD, int(value))
                else:
                    winreg.SetValueEx(key, vname, 0, winreg.REG_SZ, str(value))
            finally:
                winreg.CloseKey(key)
            return True
        except (OSError, PermissionError, ValueError) as exc:
            self.log(f"  {subkey}\\{vname}: {exc}", "error")
            return False

    def apply_tweak(self, tweak_id: str) -> bool:
        """Apply all registry ops for one tweak id. Returns True if all succeed."""
        tweak = TWEAKS.get(tweak_id)
        if tweak is None:
            self.log(f"Tweak desconocido: {tweak_id}", "error")
            return False
        ok_all = True
        for op in tweak["ops"]:
            if not self._apply_op(op):
                ok_all = False
        return ok_all

    def _read_op(self, op: RegOp) -> bool:
        """Return True if the registry value already equals the tweak's target."""
        hive_name, subkey, vname, value, kind = op
        if not self.is_windows:
            return False
        try:
            hive = winreg.HKEY_CURRENT_USER if hive_name == "HKCU" else winreg.HKEY_LOCAL_MACHINE
            key = winreg.OpenKey(hive, subkey)
            try:
                current, _ = winreg.QueryValueEx(key, vname)
            finally:
                winreg.CloseKey(key)
        except (OSError, FileNotFoundError):
            return False
        if kind == "DWORD":
            try:
                return int(current) == int(value)
            except (TypeError, ValueError):
                return False
        return str(current) == str(value)

    def is_applied(self, tweak_id: str) -> bool:
        """Return True if every registry op for ``tweak_id`` already matches."""
        tweak = TWEAKS.get(tweak_id)
        if tweak is None:
            return False
        return all(self._read_op(op) for op in tweak["ops"])

    def get_status(self) -> list[dict]:
        """Return [{id, label, applied}] for every known tweak (read-only)."""
        return [
            {"id": tid, "label": t["label"], "applied": self.is_applied(tid)}
            for tid, t in TWEAKS.items()
        ]

    def restart_explorer(self) -> bool:
        """Restart Explorer so taskbar/Start changes take effect."""
        if not self.is_windows:
            return False
        try:
            subprocess.run(
                ["taskkill", "/f", "/im", "explorer.exe"],
                capture_output=True,
                shell=False,
                timeout=10,
            )
            subprocess.Popen(["explorer.exe"], shell=False)
            self.log("Explorer reiniciado", "info")
            return True
        except (OSError, subprocess.SubprocessError) as exc:
            self.log(f"No pude reiniciar Explorer: {exc}", "warning")
            return False

    def apply_tweaks(self, tweak_ids: list[str], restart: bool = True) -> dict:
        """
        Apply a list of tweaks by id, optionally restarting Explorer.

        Returns {"success", "applied", "requested", "failed": [ids]}.
        """
        if not self.is_windows:
            self.log("No es Windows; no hago nada.", "warning")
            return {
                "success": False,
                "applied": 0,
                "requested": len(tweak_ids),
                "failed": list(tweak_ids),
            }

        valid_ids = [t for t in tweak_ids if t in TWEAKS]
        if not valid_ids:
            self.log("No hay tweaks válidos seleccionados.", "warning")
            return {"success": False, "applied": 0, "requested": len(tweak_ids), "failed": []}

        self.log(f"Aplicando {len(valid_ids)} tweaks…")
        applied = 0
        failed: list[str] = []
        for tweak_id in valid_ids:
            if self.apply_tweak(tweak_id):
                applied += 1
                self.log(f"✓ {TWEAKS[tweak_id]['label']}", "success")
            else:
                failed.append(tweak_id)
                self.log(f"✗ {TWEAKS[tweak_id]['label']}", "error")

        if restart and applied:
            self.restart_explorer()

        self.log(f"Hecho: {applied}/{len(valid_ids)}", "success")
        return {
            "success": applied == len(valid_ids),
            "applied": applied,
            "requested": len(valid_ids),
            "failed": failed,
        }

    def apply_all(self, restart: bool = True) -> dict:
        """Apply every known tweak."""
        return self.apply_tweaks(list(TWEAKS.keys()), restart=restart)
