"""
Package Manager - GUI wrapper for winget (Windows Package Manager)

This module allows users to:
1. Search for software packages
2. Install packages
3. Uninstall packages
4. Update packages
5. List installed packages
6. Export/import package lists

Requires Windows Package Manager (winget) to be installed.
Pre-installed on Windows 11, available for Windows 10.

Author: WinGuardOptimizer Team
"""

import json
import logging
import os
import re
import subprocess


class PackageManager:
    """Wrapper for winget (Windows Package Manager)."""

    def __init__(self, callback=None):
        """
        Initialize PackageManager.

        Args:
            callback: Optional callback function for logging (func(message, level))
        """
        self.callback = callback
        self.logger = logging.getLogger(__name__)

    def _log(self, message, level="info"):
        """Log message via callback and logger."""
        if self.callback:
            self.callback(message, level)

        if level == "error":
            self.logger.error(message)
        elif level == "warning":
            self.logger.warning(message)
        else:
            self.logger.info(message)

    def _validate_package_id(self, package_id):
        """
        Validate package ID to prevent command injection.

        Args:
            package_id: Package identifier to validate

        Returns:
            bool: True if valid, False otherwise
        """
        if not package_id or not isinstance(package_id, str):
            return False

        # Allow only alphanumeric, dots, hyphens, and underscores
        # This matches typical winget package IDs like "Microsoft.PowerToys"
        pattern = r"^[a-zA-Z0-9._-]+$"
        return re.match(pattern, package_id) is not None

    def is_winget_available(self):
        """
        Check if winget is installed and available.

        Returns:
            dict: {"available": bool, "version": str, "message": str}
        """
        try:
            result = subprocess.run(
                ["winget", "--version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW
                if hasattr(subprocess, "CREATE_NO_WINDOW")
                else 0,
            )

            if result.returncode == 0:
                version = result.stdout.strip()
                return {
                    "available": True,
                    "version": version,
                    "message": f"✓ winget {version} disponible",
                }
            else:
                return {"available": False, "version": None, "message": "winget no está instalado"}

        except FileNotFoundError:
            return {
                "available": False,
                "version": None,
                "message": "winget no encontrado. Instalar desde Microsoft Store: 'App Installer'",
            }
        except Exception as e:
            return {"available": False, "version": None, "message": f"Error: {str(e)}"}

    def search_package(self, query, exact=False):
        """
        Search for packages.

        Args:
            query: Search query
            exact: If True, search for exact match

        Returns:
            dict: {
                "success": bool,
                "packages": [{"id": str, "name": str, "version": str, "source": str}],
                "count": int
            }
        """
        self._log(f"Buscando '{query}'...", "info")

        try:
            cmd = ["winget", "search", query, "--accept-source-agreements"]

            if exact:
                cmd.append("--exact")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW
                if hasattr(subprocess, "CREATE_NO_WINDOW")
                else 0,
            )

            if result.returncode != 0:
                return {
                    "success": False,
                    "packages": [],
                    "count": 0,
                    "message": "No se encontraron paquetes",
                }

            # Parse output
            packages = self._parse_winget_output(result.stdout)

            self._log(f"✓ Encontrados {len(packages)} paquetes", "success")

            return {"success": True, "packages": packages, "count": len(packages)}

        except subprocess.TimeoutExpired:
            self._log("Timeout al buscar paquetes", "error")
            return {"success": False, "packages": [], "count": 0}
        except Exception as e:
            self._log(f"Error al buscar: {str(e)}", "error")
            return {"success": False, "packages": [], "count": 0}

    def _parse_winget_output(self, output):
        """
        Parse winget table output.

        Args:
            output: winget command output

        Returns:
            list: [{"id": str, "name": str, "version": str, "source": str}]
        """
        packages = []
        lines = output.split("\n")

        # Skip header and separator lines
        data_started = False

        for line in lines:
            # Skip empty lines
            if not line.strip():
                continue

            # Skip header lines
            if "Name" in line and "Id" in line:
                data_started = True
                continue

            if not data_started or "-" * 5 in line:
                continue

            # Parse package line
            # Format is typically: Name  Id  Version  Source
            parts = line.split()

            if len(parts) >= 3:
                # Name might contain spaces, Id is usually the last part before version
                # This is a simplified parser - winget output can be complex

                # Try to extract ID (usually has dots or dashes)
                package_id = None
                version = None
                source = "winget"

                for i, part in enumerate(parts):
                    if "." in part or "-" in part:
                        # Likely the ID
                        package_id = part
                        # Next might be version
                        if i + 1 < len(parts):
                            version = parts[i + 1]
                        if i + 2 < len(parts):
                            source = parts[i + 2]
                        break

                if package_id:
                    # Name is everything before the ID
                    name_parts = []
                    for part in parts:
                        if part == package_id:
                            break
                        name_parts.append(part)

                    name = " ".join(name_parts) if name_parts else package_id

                    packages.append(
                        {
                            "id": package_id,
                            "name": name,
                            "version": version or "Unknown",
                            "source": source,
                        }
                    )

        return packages

    def install_package(self, package_id, silent=True):
        """
        Install a package.

        Args:
            package_id: Package ID to install
            silent: Install silently without prompts

        Returns:
            dict: {"success": bool, "message": str}
        """
        # Validate package ID
        if not self._validate_package_id(package_id):
            return {"success": False, "message": f"ID de paquete inválido: {package_id}"}

        # Check if winget is available
        winget_check = self.is_winget_available()
        if not winget_check.get("available", False):
            return {
                "success": False,
                "message": "winget no está disponible. " + winget_check.get("message", ""),
            }

        self._log(f"Instalando {package_id}...", "info")

        try:
            cmd = [
                "winget",
                "install",
                "--id",
                package_id,
                "--accept-source-agreements",
                "--accept-package-agreements",
            ]

            if silent:
                cmd.append("--silent")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=300,  # 5 minutes for installation
                creationflags=subprocess.CREATE_NO_WINDOW
                if hasattr(subprocess, "CREATE_NO_WINDOW")
                else 0,
            )

            if result.returncode == 0:
                self._log(f"✓ {package_id} instalado correctamente", "success")
                return {"success": True, "message": f"✓ {package_id} instalado"}
            else:
                error_msg = result.stderr or result.stdout
                self._log(f"Error al instalar {package_id}: {error_msg}", "error")
                return {"success": False, "message": f"Error: {error_msg[:200]}"}

        except subprocess.TimeoutExpired:
            return {"success": False, "message": "Timeout: La instalación tardó demasiado"}
        except Exception as e:
            self._log(f"Error al instalar: {str(e)}", "error")
            return {"success": False, "message": f"Error: {str(e)}"}

    def uninstall_package(self, package_id, silent=True):
        """
        Uninstall a package.

        Args:
            package_id: Package ID to uninstall
            silent: Uninstall silently without prompts

        Returns:
            dict: {"success": bool, "message": str}
        """
        # Validate package ID
        if not self._validate_package_id(package_id):
            return {"success": False, "message": f"ID de paquete inválido: {package_id}"}

        # Check if winget is available
        winget_check = self.is_winget_available()
        if not winget_check.get("available", False):
            return {
                "success": False,
                "message": "winget no está disponible. " + winget_check.get("message", ""),
            }

        self._log(f"Desinstalando {package_id}...", "info")

        try:
            cmd = ["winget", "uninstall", "--id", package_id, "--accept-source-agreements"]

            if silent:
                cmd.append("--silent")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=300,  # 5 minutes for uninstallation
                creationflags=subprocess.CREATE_NO_WINDOW
                if hasattr(subprocess, "CREATE_NO_WINDOW")
                else 0,
            )

            if result.returncode == 0:
                self._log(f"✓ {package_id} desinstalado correctamente", "success")
                return {"success": True, "message": f"✓ {package_id} desinstalado"}
            else:
                error_msg = result.stderr or result.stdout
                self._log(f"Error al desinstalar {package_id}: {error_msg}", "error")
                return {"success": False, "message": f"Error: {error_msg[:200]}"}

        except subprocess.TimeoutExpired:
            return {"success": False, "message": "Timeout: La desinstalación tardó demasiado"}
        except Exception as e:
            self._log(f"Error al desinstalar: {str(e)}", "error")
            return {"success": False, "message": f"Error: {str(e)}"}

    def update_package(self, package_id=None, update_all=False):
        """
        Update a package or all packages.

        Args:
            package_id: Package ID to update (None if update_all=True)
            update_all: If True, update all packages

        Returns:
            dict: {"success": bool, "message": str, "updated_count": int}
        """
        if update_all:
            self._log("Actualizando todos los paquetes...", "info")
            cmd = [
                "winget",
                "upgrade",
                "--all",
                "--accept-source-agreements",
                "--accept-package-agreements",
                "--silent",
            ]
        else:
            if not package_id:
                return {
                    "success": False,
                    "message": "Se requiere package_id o update_all=True",
                    "updated_count": 0,
                }
            self._log(f"Actualizando {package_id}...", "info")
            cmd = [
                "winget",
                "upgrade",
                "--id",
                package_id,
                "--accept-source-agreements",
                "--accept-package-agreements",
                "--silent",
            ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=600,  # 10 minutes for updates
                creationflags=subprocess.CREATE_NO_WINDOW
                if hasattr(subprocess, "CREATE_NO_WINDOW")
                else 0,
            )

            if result.returncode == 0:
                if update_all:
                    self._log("✓ Paquetes actualizados", "success")
                    message = "✓ Todos los paquetes actualizados"
                else:
                    self._log(f"✓ {package_id} actualizado", "success")
                    message = f"✓ {package_id} actualizado"

                return {"success": True, "message": message, "updated_count": 1}
            else:
                # Check if there are no updates available
                if (
                    "No applicable update found" in result.stdout
                    or "No installed package found" in result.stdout
                ):
                    return {
                        "success": True,
                        "message": "No hay actualizaciones disponibles",
                        "updated_count": 0,
                    }

                error_msg = result.stderr or result.stdout
                return {
                    "success": False,
                    "message": f"Error: {error_msg[:200]}",
                    "updated_count": 0,
                }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "message": "Timeout: La actualización tardó demasiado",
                "updated_count": 0,
            }
        except Exception as e:
            self._log(f"Error al actualizar: {str(e)}", "error")
            return {"success": False, "message": f"Error: {str(e)}", "updated_count": 0}

    def list_installed(self):
        """
        List all installed packages.

        Returns:
            dict: {
                "success": bool,
                "packages": [{"id": str, "name": str, "version": str, "available_version": str}],
                "count": int
            }
        """
        self._log("Listando paquetes instalados...", "info")

        try:
            result = subprocess.run(
                ["winget", "list", "--accept-source-agreements"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW
                if hasattr(subprocess, "CREATE_NO_WINDOW")
                else 0,
            )

            if result.returncode != 0:
                return {"success": False, "packages": [], "count": 0}

            packages = self._parse_winget_output(result.stdout)

            self._log(f"✓ {len(packages)} paquetes instalados", "success")

            return {"success": True, "packages": packages, "count": len(packages)}

        except Exception as e:
            self._log(f"Error al listar paquetes: {str(e)}", "error")
            return {"success": False, "packages": [], "count": 0}

    def list_upgradable(self):
        """
        List packages with available updates.

        Returns:
            dict: {
                "success": bool,
                "packages": [{"id": str, "name": str, "current_version": str, "available_version": str}],
                "count": int
            }
        """
        self._log("Buscando actualizaciones...", "info")

        try:
            result = subprocess.run(
                ["winget", "upgrade", "--accept-source-agreements"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW
                if hasattr(subprocess, "CREATE_NO_WINDOW")
                else 0,
            )

            packages = self._parse_winget_output(result.stdout)

            self._log(f"✓ {len(packages)} actualizaciones disponibles", "success")

            return {"success": True, "packages": packages, "count": len(packages)}

        except Exception as e:
            self._log(f"Error al buscar actualizaciones: {str(e)}", "error")
            return {"success": False, "packages": [], "count": 0}

    def export_packages(self, output_file):
        """
        Export list of installed packages to JSON file.

        Args:
            output_file: Path to output JSON file

        Returns:
            dict: {"success": bool, "message": str, "package_count": int}
        """
        try:
            result = subprocess.run(
                ["winget", "export", "-o", output_file, "--accept-source-agreements"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW
                if hasattr(subprocess, "CREATE_NO_WINDOW")
                else 0,
            )

            if result.returncode == 0:
                # Count packages in exported file
                if os.path.exists(output_file):
                    with open(output_file) as f:
                        data = json.load(f)
                        count = len(data.get("Sources", [{}])[0].get("Packages", []))

                    self._log(f"✓ {count} paquetes exportados a {output_file}", "success")

                    return {
                        "success": True,
                        "message": f"✓ Exportados {count} paquetes",
                        "package_count": count,
                    }

            return {"success": False, "message": "Error al exportar paquetes", "package_count": 0}

        except Exception as e:
            self._log(f"Error al exportar: {str(e)}", "error")
            return {"success": False, "message": f"Error: {str(e)}", "package_count": 0}

    def import_packages(self, input_file):
        """
        Import and install packages from JSON file.

        Args:
            input_file: Path to JSON file with package list

        Returns:
            dict: {"success": bool, "message": str}
        """
        if not os.path.exists(input_file):
            return {"success": False, "message": "Archivo no encontrado"}

        self._log(f"Importando paquetes desde {input_file}...", "info")

        try:
            result = subprocess.run(
                [
                    "winget",
                    "import",
                    "-i",
                    input_file,
                    "--accept-source-agreements",
                    "--accept-package-agreements",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=600,  # 10 minutes for importing
                creationflags=subprocess.CREATE_NO_WINDOW
                if hasattr(subprocess, "CREATE_NO_WINDOW")
                else 0,
            )

            if result.returncode == 0:
                self._log("✓ Paquetes importados correctamente", "success")
                return {"success": True, "message": "✓ Paquetes importados e instalados"}
            else:
                return {"success": False, "message": f"Error: {result.stderr or result.stdout}"}

        except subprocess.TimeoutExpired:
            return {"success": False, "message": "Timeout: La importación tardó demasiado"}
        except Exception as e:
            self._log(f"Error al importar: {str(e)}", "error")
            return {"success": False, "message": f"Error: {str(e)}"}

    def get_popular_packages(self):
        """
        Get list of popular/recommended packages.

        Returns:
            list: [{"id": str, "name": str, "description": str, "category": str}]
        """
        return [
            # Browsers
            {
                "id": "Mozilla.Firefox",
                "name": "Firefox",
                "description": "Privacy-focused browser",
                "category": "Browser",
            },
            {
                "id": "Google.Chrome",
                "name": "Google Chrome",
                "description": "Popular browser",
                "category": "Browser",
            },
            {
                "id": "Brave.Brave",
                "name": "Brave",
                "description": "Privacy browser with ad blocking",
                "category": "Browser",
            },
            # Development
            {
                "id": "Microsoft.VisualStudioCode",
                "name": "VS Code",
                "description": "Code editor",
                "category": "Development",
            },
            {
                "id": "Git.Git",
                "name": "Git",
                "description": "Version control",
                "category": "Development",
            },
            {
                "id": "Python.Python.3.11",
                "name": "Python 3.11",
                "description": "Programming language",
                "category": "Development",
            },
            # Utilities
            {
                "id": "7zip.7zip",
                "name": "7-Zip",
                "description": "File archiver",
                "category": "Utilities",
            },
            {
                "id": "VideoLAN.VLC",
                "name": "VLC",
                "description": "Media player",
                "category": "Media",
            },
            {
                "id": "Notepad++.Notepad++",
                "name": "Notepad++",
                "description": "Text editor",
                "category": "Utilities",
            },
            # Communication
            {
                "id": "Discord.Discord",
                "name": "Discord",
                "description": "Chat platform",
                "category": "Communication",
            },
            {
                "id": "Zoom.Zoom",
                "name": "Zoom",
                "description": "Video conferencing",
                "category": "Communication",
            },
            # Productivity
            {
                "id": "Notion.Notion",
                "name": "Notion",
                "description": "Notes and productivity",
                "category": "Productivity",
            },
            {
                "id": "Obsidian.Obsidian",
                "name": "Obsidian",
                "description": "Knowledge base",
                "category": "Productivity",
            },
        ]
