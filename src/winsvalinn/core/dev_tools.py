"""
Developer environment engine — detect dev tools, clean caches, configure
Defender exclusions and inspect WSL2/Docker.

Migrated from the legacy ``plugin_developer`` plugin. No GUI imports: all work
uses :mod:`subprocess` (``shell=False``), :mod:`pathlib` and :mod:`shutil`.
Failures are reported through the optional ``callback`` instead of raising.
"""

from __future__ import annotations

import platform
import shutil
import subprocess
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

DEV_ENVIRONMENTS: dict[str, dict] = {
    "VS Code": {
        "check": ["code", "--version"],
        "paths": [
            Path.home() / "AppData" / "Roaming" / "Code",
            Path.home() / "AppData" / "Local" / "Programs" / "Microsoft VS Code",
        ],
    },
    "Visual Studio": {
        "paths": [
            Path(r"C:\Program Files\Microsoft Visual Studio"),
            Path(r"C:\Program Files (x86)\Microsoft Visual Studio"),
        ],
    },
    "Node.js": {"check": ["node", "--version"]},
    "Python": {"check": ["python", "--version"]},
    "Git": {"check": ["git", "--version"]},
    "Docker": {"check": ["docker", "--version"]},
    "JetBrains": {
        "paths": [Path.home() / "AppData" / "Local" / "JetBrains"],
    },
}

# Cache locations safe to remove (fixed, well-known paths only).
CACHE_PATTERNS: dict[str, dict] = {
    ".gradle caches": {"path": Path.home() / ".gradle" / "caches"},
    "npm cache": {"path": Path.home() / "AppData" / "Local" / "npm-cache"},
    "pip cache": {"path": Path.home() / "AppData" / "Local" / "pip" / "cache"},
    "NuGet packages": {"path": Path.home() / ".nuget" / "packages"},
}


def _dir_size(path: Path) -> int:
    """Return total size in bytes of all files under ``path``."""
    total = 0
    try:
        for child in path.rglob("*"):
            try:
                if child.is_file():
                    total += child.stat().st_size
            except (OSError, PermissionError):
                continue
    except (OSError, PermissionError):
        pass
    return total


class DevTools:
    """Detect dev environments, clean caches and configure Defender exclusions."""

    def __init__(self, callback: Callable[[str, str], None] | None = None) -> None:
        self.callback = callback or (lambda msg, level="info": None)
        self.is_windows = platform.system() == "Windows"

    def log(self, message: str, level: str = "info") -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.callback(f"[{timestamp}] {message}", level)

    def _is_admin(self) -> bool:
        try:
            import ctypes

            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except (OSError, AttributeError):
            return False

    def detect_environments(self) -> dict:
        """Detect installed IDEs, runtimes and tools. Read-only."""
        self.log("Detectando entornos de desarrollo…", "info")
        found: dict[str, str] = {}
        for name, config in DEV_ENVIRONMENTS.items():
            detail = None
            if "check" in config:
                try:
                    result = subprocess.run(
                        config["check"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                        shell=False,
                        creationflags=CREATE_NO_WINDOW,
                    )
                    if result.returncode == 0:
                        detail = result.stdout.strip().splitlines()[0]
                except (FileNotFoundError, OSError, subprocess.SubprocessError):
                    pass
            if detail is None and "paths" in config:
                for p in config["paths"]:
                    if p and Path(p).exists():
                        detail = f"Found at {p}"
                        break
            if detail is not None:
                found[name] = detail
                self.log(f"  {name}: {detail}", "success")
            else:
                self.log(f"  {name}: no encontrado", "info")
        return {"success": True, "found": found, "checked": list(DEV_ENVIRONMENTS.keys())}

    def analyze_caches(self) -> dict:
        """Report the size of known dev caches without deleting. Read-only."""
        self.log("Analizando cachés de desarrollo…", "info")
        sizes: dict[str, int] = {}
        total = 0
        for name, config in CACHE_PATTERNS.items():
            path = config["path"]
            if path.exists():
                size = _dir_size(path)
                sizes[name] = size
                total += size
                level = "warning" if size > 100 * 1024**2 else "info"
                self.log(f"  {name}: {size / (1024**2):.1f} MB ({path})", level)
            else:
                self.log(f"  {name}: no encontrado", "info")
        self.log(f"Total caché dev: {total / (1024**2):.1f} MB", "warning")
        return {"success": True, "sizes": sizes, "total_bytes": total}

    def clean_caches(self) -> dict:
        """Delete known dev caches. Destructive (removes files)."""
        self.log("Limpiando cachés de desarrollo…", "warning")
        freed = 0
        cleaned: dict[str, int] = {}
        for name, config in CACHE_PATTERNS.items():
            path = config["path"]
            if path.exists():
                size = _dir_size(path)
                shutil.rmtree(path, ignore_errors=True)
                freed += size
                cleaned[name] = size
                self.log(f"  Limpiado {name}: {size / (1024**2):.1f} MB", "success")
        self.log(f"Total liberado: {freed / (1024**2):.1f} MB", "success")
        return {"success": True, "cleaned": cleaned, "freed_bytes": freed}

    def configure_defender_exclusions(self) -> dict:
        """Add common dev folders to Defender exclusions. Requires admin."""
        self.log("Configurando exclusiones de Defender para carpetas dev…", "info")
        if not self.is_windows:
            self.log("No es Windows; no hago nada.", "warning")
            return {"success": False, "excluded": []}

        home = Path.home()
        folders = [
            home / "Documents",
            home / "Projects",
            home / "source",
            home / ".npm",
            home / ".nuget",
        ]
        excluded: list[str] = []
        for folder in folders:
            if not folder.exists():
                continue
            # PowerShell receives the path as a single -ExclusionPath argument.
            cmd = f"Add-MpPreference -ExclusionPath '{folder}' -ErrorAction SilentlyContinue"
            try:
                result = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", cmd],
                    capture_output=True,
                    timeout=10,
                    shell=False,
                    creationflags=CREATE_NO_WINDOW,
                )
                if result.returncode == 0:
                    excluded.append(str(folder))
                    self.log(f"  Excluido: {folder}", "success")
                else:
                    self.log(f"  Falló: {folder} (requiere admin)", "warning")
            except (OSError, subprocess.SubprocessError):
                self.log(f"  Falló: {folder} (requiere admin)", "warning")
        self.log("Exclusiones de Defender configuradas (requiere admin)", "info")
        return {"success": bool(excluded), "excluded": excluded}

    def check_wsl_docker(self) -> dict:
        """Report WSL2 and Docker status. Read-only."""
        self.log("Comprobando WSL2 y Docker…", "info")
        wsl_installed = False
        docker_running = False
        docker_memory = None

        try:
            result = subprocess.run(
                ["wsl", "--status"],
                capture_output=True,
                text=True,
                timeout=10,
                shell=False,
                creationflags=CREATE_NO_WINDOW,
            )
            if result.returncode == 0:
                wsl_installed = True
                self.log("  WSL2: instalado", "success")
            else:
                self.log("  WSL2: no instalado", "info")
        except (FileNotFoundError, OSError, subprocess.SubprocessError):
            self.log("  WSL2: no disponible", "info")

        try:
            result = subprocess.run(
                ["docker", "info", "--format", "{{.MemTotal}}"],
                capture_output=True,
                text=True,
                timeout=10,
                shell=False,
                creationflags=CREATE_NO_WINDOW,
            )
            if result.returncode == 0:
                docker_running = True
                docker_memory = result.stdout.strip()
                self.log(f"  Docker: en ejecución (memoria: {docker_memory})", "success")
            else:
                self.log("  Docker: no en ejecución", "warning")
        except (FileNotFoundError, OSError, subprocess.SubprocessError):
            self.log("  Docker: no instalado", "info")

        return {
            "success": True,
            "wsl_installed": wsl_installed,
            "docker_running": docker_running,
            "docker_memory": docker_memory,
        }
