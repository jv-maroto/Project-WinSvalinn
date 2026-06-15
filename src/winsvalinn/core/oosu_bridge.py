"""
O&O ShutUp10++ bridge - download and launch the official privacy tool.

ShutUp10++ is the reference tool for fine-grained Windows 10/11 privacy
configuration (Copilot, Recall, telemetry, etc.). WinSvalinn does not
re-implement it; this module just provides a programmatic bridge that
downloads the official ``OOSU10.exe`` (if missing) and launches it.

No GUI imports - this is a core engine usable from the sidecar/CLI.
"""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


class OOSUBridge:
    """Download and launch O&O ShutUp10++ (OOSU10.exe)."""

    OOSU_URL = "https://dl5.oo-software.com/files/ooshutup1011/OOSU10.exe"
    OOSU_PATH = Path.home() / "AppData" / "Local" / "WinSvalinn" / "tools" / "OOSU10.exe"

    def __init__(self, callback: Callable[[str, str], None] | None = None) -> None:
        """
        Initialize the bridge.

        Args:
            callback: Optional logging callback ``func(message, level)``.
        """
        self.callback = callback

    def _log(self, message: str, level: str = "info") -> None:
        """Forward a message to the optional callback."""
        if self.callback:
            self.callback(message, level)

    def get_status(self) -> dict:
        """
        Report whether OOSU10.exe has been downloaded.

        Returns:
            dict: {"installed": bool, "path": str, "size_bytes": int}
        """
        path = self.OOSU_PATH
        if path.exists():
            try:
                size = path.stat().st_size
            except OSError:
                size = 0
            return {"installed": True, "path": str(path), "size_bytes": size}
        return {"installed": False, "path": str(path), "size_bytes": 0}

    def download(self) -> dict:
        """
        Download the official OOSU10.exe to the local tools directory.

        Idempotent: overwrites any existing copy with the latest version.

        Returns:
            dict: {"success": bool, "path": str|None, "message": str}
        """
        self._log(f"Descargando {self.OOSU_URL} …", "info")
        try:
            self.OOSU_PATH.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            self._log(f"No se pudo crear el directorio de destino: {exc}", "error")
            return {
                "success": False,
                "path": None,
                "message": f"Error al crear directorio: {exc}",
            }

        try:
            req = Request(self.OOSU_URL, headers={"User-Agent": "WinSvalinn/1.0"})
            with urlopen(req, timeout=60) as resp:
                data = resp.read()
        except (URLError, TimeoutError, OSError) as exc:
            self._log(f"Error de descarga: {exc}", "error")
            return {"success": False, "path": None, "message": f"Error de red: {exc}"}

        try:
            self.OOSU_PATH.write_bytes(data)
        except OSError as exc:
            self._log(f"Error al guardar el binario: {exc}", "error")
            return {
                "success": False,
                "path": None,
                "message": f"Error al guardar: {exc}",
            }

        size_mb = len(data) / (1024 * 1024)
        msg = f"✓ Descargado en {self.OOSU_PATH} ({size_mb:.1f} MB)"
        self._log(msg, "success")
        return {"success": True, "path": str(self.OOSU_PATH), "message": msg}

    def launch(self) -> dict:
        """
        Launch the downloaded OOSU10.exe (downloads first if missing).

        Returns:
            dict: {"success": bool, "message": str}
        """
        if not self.OOSU_PATH.exists():
            self._log("OOSU10.exe no encontrado; descargando primero…", "info")
            result = self.download()
            if not result["success"]:
                return {"success": False, "message": result["message"]}

        try:
            subprocess.Popen([str(self.OOSU_PATH)], shell=False)
        except OSError as exc:
            self._log(f"Error al lanzar OOSU10: {exc}", "error")
            return {"success": False, "message": f"Error al lanzar: {exc}"}

        self._log("✓ O&O ShutUp10++ lanzado", "success")
        return {"success": True, "message": "✓ O&O ShutUp10++ lanzado"}
