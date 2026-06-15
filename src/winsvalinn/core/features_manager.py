"""
Windows Features Manager - Manage Windows Optional Features

This module allows users to:
1. List all Windows optional features
2. Enable features (Hyper-V, WSL, IIS, etc.)
3. Disable features
4. Check feature status
5. Get feature recommendations

Common features:
- Hyper-V (virtualization)
- WSL2 (Windows Subsystem for Linux)
- .NET Framework versions
- Windows Sandbox
- Internet Information Services (IIS)
- Telnet Client
- And many more...

Author: WinGuardOptimizer Team
"""

import logging
import subprocess


class FeaturesManager:
    """Manage Windows Optional Features."""

    # Categorized popular features
    POPULAR_FEATURES = {
        # Virtualization & Development
        "Microsoft-Hyper-V-All": {
            "name": "Hyper-V",
            "description": "Hardware virtualization platform",
            "category": "Virtualization",
            "requires_restart": True,
        },
        "VirtualMachinePlatform": {
            "name": "Virtual Machine Platform",
            "description": "Required for WSL2",
            "category": "Virtualization",
            "requires_restart": True,
        },
        "Microsoft-Windows-Subsystem-Linux": {
            "name": "Windows Subsystem for Linux",
            "description": "Run Linux distributions on Windows",
            "category": "Development",
            "requires_restart": True,
        },
        "Containers-DisposableClientVM": {
            "name": "Windows Sandbox",
            "description": "Isolated desktop environment for testing",
            "category": "Virtualization",
            "requires_restart": True,
        },
        # Web & Server
        "IIS-WebServerRole": {
            "name": "Internet Information Services",
            "description": "Web server (IIS)",
            "category": "Web & Server",
            "requires_restart": False,
        },
        "IIS-WebServer": {
            "name": "IIS Web Server",
            "description": "Core web server functionality",
            "category": "Web & Server",
            "requires_restart": False,
        },
        # .NET Framework
        "NetFx3": {
            "name": ".NET Framework 3.5",
            "description": "Legacy .NET framework",
            "category": ".NET",
            "requires_restart": False,
        },
        "NetFx4-AdvSrvs": {
            "name": ".NET Framework 4.x Advanced",
            "description": "Advanced .NET 4.x features",
            "category": ".NET",
            "requires_restart": False,
        },
        # Networking
        "TelnetClient": {
            "name": "Telnet Client",
            "description": "Legacy terminal protocol",
            "category": "Networking",
            "requires_restart": False,
        },
        "TFTP": {
            "name": "TFTP Client",
            "description": "Trivial File Transfer Protocol",
            "category": "Networking",
            "requires_restart": False,
        },
        "SMB1Protocol": {
            "name": "SMB 1.0/CIFS File Sharing",
            "description": "Legacy file sharing (insecure, not recommended)",
            "category": "Networking",
            "requires_restart": True,
        },
        # Media
        "MediaPlayback": {
            "name": "Media Features",
            "description": "Windows Media Player and codecs",
            "category": "Media",
            "requires_restart": False,
        },
        "WindowsMediaPlayer": {
            "name": "Windows Media Player",
            "description": "Legacy media player",
            "category": "Media",
            "requires_restart": False,
        },
        # Legacy
        "LegacyComponents": {
            "name": "Legacy Components",
            "description": "DirectPlay and other legacy features",
            "category": "Legacy",
            "requires_restart": False,
        },
        "DirectPlay": {
            "name": "DirectPlay",
            "description": "Legacy gaming API",
            "category": "Legacy",
            "requires_restart": False,
        },
        # Remote
        "Printing-XPSServices-Features": {
            "name": "XPS Viewer & Services",
            "description": "XPS document support",
            "category": "Printing",
            "requires_restart": False,
        },
    }

    def __init__(self, callback=None):
        """
        Initialize FeaturesManager.

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

    def _is_admin(self):
        """Check if running as administrator."""
        try:
            import ctypes

            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    def list_all_features(self):
        """
        List all Windows optional features.

        Returns:
            dict: {
                "success": bool,
                "features": [{"name": str, "state": str, "restart_required": bool}],
                "count": int
            }
        """
        self._log("Listando características de Windows...", "info")

        try:
            # Use DISM to list features
            cmd = ["dism", "/online", "/get-features", "/format:table"]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
                creationflags=subprocess.CREATE_NO_WINDOW
                if hasattr(subprocess, "CREATE_NO_WINDOW")
                else 0,
            )

            if result.returncode != 0:
                self._log("Error al listar características", "error")
                return {"success": False, "features": [], "count": 0}

            features = self._parse_dism_features(result.stdout)

            self._log(f"✓ {len(features)} características encontradas", "success")

            return {"success": True, "features": features, "count": len(features)}

        except subprocess.TimeoutExpired:
            self._log("Timeout al listar características", "error")
            return {"success": False, "features": [], "count": 0}
        except Exception as e:
            self._log(f"Error al listar características: {str(e)}", "error")
            return {"success": False, "features": [], "count": 0}

    def _parse_dism_features(self, output):
        """
        Parse DISM output to extract features.

        Args:
            output: DISM command output

        Returns:
            list: [{"name": str, "state": str, "restart_required": bool}]
        """
        features = []
        lines = output.split("\n")

        for line in lines:
            # Look for feature names (format: "Feature Name : FeatureName")
            if "|" in line:
                parts = [p.strip() for p in line.split("|")]

                if len(parts) >= 2:
                    feature_name = parts[0]
                    state = parts[1] if len(parts) > 1 else "Unknown"

                    # Skip header and separator lines
                    if feature_name in ["Feature Name", "---", ""]:
                        continue

                    features.append(
                        {
                            "name": feature_name,
                            "state": state,
                            "restart_required": False,  # Would need to check individually
                        }
                    )

        return features

    def get_feature_info(self, feature_name):
        """
        Get detailed information about a feature.

        Args:
            feature_name: Feature name

        Returns:
            dict: {
                "success": bool,
                "name": str,
                "state": str,
                "description": str,
                "restart_required": bool
            }
        """
        try:
            cmd = ["dism", "/online", f"/get-featureinfo:{feature_name}"]

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
                    "name": feature_name,
                    "state": "Unknown",
                    "description": "",
                    "restart_required": False,
                }

            output = result.stdout

            # Parse output
            state = "Unknown"
            description = ""
            restart_required = False

            for line in output.split("\n"):
                if "State :" in line:
                    state = line.split(":", 1)[1].strip()
                elif "Description :" in line:
                    description = line.split(":", 1)[1].strip()
                elif "Restart Required :" in line:
                    restart_value = line.split(":", 1)[1].strip()
                    restart_required = restart_value.lower() in ["yes", "possible"]

            # Add info from POPULAR_FEATURES if available
            if feature_name in self.POPULAR_FEATURES:
                popular_info = self.POPULAR_FEATURES[feature_name]
                if not description:
                    description = popular_info["description"]

            return {
                "success": True,
                "name": feature_name,
                "state": state,
                "description": description,
                "restart_required": restart_required,
            }

        except Exception as e:
            self._log(f"Error al obtener info de {feature_name}: {str(e)}", "error")
            return {
                "success": False,
                "name": feature_name,
                "state": "Unknown",
                "description": "",
                "restart_required": False,
            }

    def enable_feature(self, feature_name, restart_now=False):
        """
        Enable a Windows feature.

        Args:
            feature_name: Feature name to enable
            restart_now: If True, restart immediately if required

        Returns:
            dict: {"success": bool, "message": str, "restart_required": bool}
        """
        if not self._is_admin():
            return {
                "success": False,
                "message": "Se requieren privilegios de Administrador",
                "restart_required": False,
            }

        self._log(f"Habilitando {feature_name}...", "info")

        try:
            cmd = [
                "dism",
                "/online",
                "/enable-feature",
                f"/featurename:{feature_name}",
                "/norestart",
            ]

            # Add /all to enable dependencies
            cmd.append("/all")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=300,  # 5 minutes for feature installation
                creationflags=subprocess.CREATE_NO_WINDOW
                if hasattr(subprocess, "CREATE_NO_WINDOW")
                else 0,
            )

            output = result.stdout + result.stderr

            # Check if restart is required
            restart_required = "restart" in output.lower() and "required" in output.lower()

            if result.returncode == 0 or "completed successfully" in output.lower():
                msg = f"✓ {feature_name} habilitada"
                if restart_required:
                    msg += " (se requiere reinicio)"

                self._log(msg, "success")

                # Restart if requested
                if restart_now and restart_required:
                    self._restart_computer()

                return {"success": True, "message": msg, "restart_required": restart_required}
            else:
                return {
                    "success": False,
                    "message": f"Error: {output[:200]}",
                    "restart_required": False,
                }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "message": "Timeout: La operación tardó demasiado",
                "restart_required": False,
            }
        except Exception as e:
            self._log(f"Error al habilitar feature: {str(e)}", "error")
            return {"success": False, "message": f"Error: {str(e)}", "restart_required": False}

    def disable_feature(self, feature_name, restart_now=False):
        """
        Disable a Windows feature.

        Args:
            feature_name: Feature name to disable
            restart_now: If True, restart immediately if required

        Returns:
            dict: {"success": bool, "message": str, "restart_required": bool}
        """
        if not self._is_admin():
            return {
                "success": False,
                "message": "Se requieren privilegios de Administrador",
                "restart_required": False,
            }

        self._log(f"Deshabilitando {feature_name}...", "info")

        try:
            cmd = [
                "dism",
                "/online",
                "/disable-feature",
                f"/featurename:{feature_name}",
                "/norestart",
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=300,  # 5 minutes for feature removal
                creationflags=subprocess.CREATE_NO_WINDOW
                if hasattr(subprocess, "CREATE_NO_WINDOW")
                else 0,
            )

            output = result.stdout + result.stderr

            # Check if restart is required
            restart_required = "restart" in output.lower() and "required" in output.lower()

            if result.returncode == 0 or "completed successfully" in output.lower():
                msg = f"✓ {feature_name} deshabilitada"
                if restart_required:
                    msg += " (se requiere reinicio)"

                self._log(msg, "success")

                # Restart if requested
                if restart_now and restart_required:
                    self._restart_computer()

                return {"success": True, "message": msg, "restart_required": restart_required}
            else:
                return {
                    "success": False,
                    "message": f"Error: {output[:200]}",
                    "restart_required": False,
                }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "message": "Timeout: La operación tardó demasiado",
                "restart_required": False,
            }
        except Exception as e:
            self._log(f"Error al deshabilitar feature: {str(e)}", "error")
            return {"success": False, "message": f"Error: {str(e)}", "restart_required": False}

    def enable_wsl2(self):
        """
        Quick setup for WSL2 (enables required features).

        Returns:
            dict: {"success": bool, "message": str, "restart_required": bool}
        """
        self._log("Configurando WSL2...", "info")

        # Enable Virtual Machine Platform
        result1 = self.enable_feature("VirtualMachinePlatform")

        # Enable WSL
        result2 = self.enable_feature("Microsoft-Windows-Subsystem-Linux")

        success = result1["success"] and result2["success"]
        restart_required = result1.get("restart_required", False) or result2.get(
            "restart_required", False
        )

        if success:
            msg = "✓ WSL2 configurado. Después del reinicio, ejecuta 'wsl --set-default-version 2'"
            self._log(msg, "success")

            return {"success": True, "message": msg, "restart_required": restart_required}
        else:
            return {
                "success": False,
                "message": "Error al configurar WSL2",
                "restart_required": False,
            }

    def _restart_computer(self, delay_seconds=10):
        """
        Restart computer with delay.

        Args:
            delay_seconds: Seconds to wait before restart
        """
        self._log(f"⚠️  Reiniciando en {delay_seconds} segundos...", "warning")

        try:
            subprocess.run(
                [
                    "shutdown",
                    "/r",
                    "/t",
                    str(delay_seconds),
                    "/c",
                    "WinGuardOptimizer - Reinicio requerido",
                ],
                creationflags=subprocess.CREATE_NO_WINDOW
                if hasattr(subprocess, "CREATE_NO_WINDOW")
                else 0,
            )
        except Exception as e:
            self._log(f"Error al programar reinicio: {str(e)}", "error")

    def get_popular_features(self):
        """
        Get list of popular features with descriptions.

        Returns:
            dict: POPULAR_FEATURES dictionary
        """
        return self.POPULAR_FEATURES

    def get_feature_recommendations(self):
        """
        Get feature recommendations based on common use cases.

        Returns:
            dict: {
                "developers": [...],
                "gamers": [...],
                "security_disable": [...]
            }
        """
        return {
            "developers": [
                "Microsoft-Windows-Subsystem-Linux",
                "VirtualMachinePlatform",
                "Microsoft-Hyper-V-All",
                "Containers-DisposableClientVM",
                "IIS-WebServerRole",
                "TelnetClient",
            ],
            "gamers": ["DirectPlay", "LegacyComponents"],
            "security_disable": [
                "SMB1Protocol",  # Insecure, should be disabled
                "TelnetClient",  # Insecure if not needed
            ],
            "privacy": [
                "Containers-DisposableClientVM"  # Windows Sandbox for testing
            ],
        }
