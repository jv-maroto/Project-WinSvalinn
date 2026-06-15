"""
Bloatware Remover - Detect and remove Windows bloatware and UWP apps

This module allows users to:
1. Detect all installed UWP/AppX packages
2. Categorize apps (System Critical, Bloatware, Games, etc.)
3. Safely uninstall unwanted apps
4. Special handling for OneDrive, Edge, and other protected apps
5. Bulk operations for quick cleanup

Author: WinGuardOptimizer Team
"""

import logging
import os
import subprocess


class BloatwareRemover:
    """Detect and remove Windows bloatware and UWP applications."""

    def __init__(self, callback=None):
        """
        Initialize BloatwareRemover.

        Args:
            callback: Optional callback function for logging (func(message, level))
        """
        self.callback = callback
        self.logger = logging.getLogger(__name__)

        # Bloatware categories
        self.BLOATWARE_APPS = {
            # Gaming
            "Microsoft.XboxApp": {
                "name": "Xbox Console Companion",
                "category": "gaming",
                "safe": True,
            },
            "Microsoft.XboxGamingOverlay": {
                "name": "Xbox Game Bar",
                "category": "gaming",
                "safe": True,
            },
            "Microsoft.XboxGameOverlay": {
                "name": "Xbox Game Overlay",
                "category": "gaming",
                "safe": True,
            },
            "Microsoft.XboxIdentityProvider": {
                "name": "Xbox Identity Provider",
                "category": "gaming",
                "safe": True,
            },
            "Microsoft.XboxSpeechToTextOverlay": {
                "name": "Xbox Speech To Text",
                "category": "gaming",
                "safe": True,
            },
            "Microsoft.Xbox.TCUI": {"name": "Xbox Live", "category": "gaming", "safe": True},
            "Microsoft.GamingApp": {"name": "Xbox Gaming App", "category": "gaming", "safe": True},
            # Bloatware/Ads
            "Microsoft.GetHelp": {"name": "Get Help", "category": "bloatware", "safe": True},
            "Microsoft.Getstarted": {"name": "Tips App", "category": "bloatware", "safe": True},
            "Microsoft.MicrosoftOfficeHub": {
                "name": "Office Hub",
                "category": "bloatware",
                "safe": True,
            },
            "Microsoft.MicrosoftSolitaireCollection": {
                "name": "Microsoft Solitaire",
                "category": "games",
                "safe": True,
            },
            "Microsoft.People": {"name": "People App", "category": "bloatware", "safe": True},
            "Microsoft.WindowsFeedbackHub": {
                "name": "Feedback Hub",
                "category": "bloatware",
                "safe": True,
            },
            "Microsoft.YourPhone": {"name": "Your Phone", "category": "bloatware", "safe": True},
            "Microsoft.ZuneMusic": {"name": "Groove Music", "category": "bloatware", "safe": True},
            "Microsoft.ZuneVideo": {"name": "Movies & TV", "category": "bloatware", "safe": True},
            "Microsoft.BingWeather": {"name": "Weather", "category": "bloatware", "safe": True},
            "Microsoft.BingNews": {"name": "News", "category": "bloatware", "safe": True},
            "Microsoft.BingFinance": {"name": "Finance", "category": "bloatware", "safe": True},
            "Microsoft.BingSports": {"name": "Sports", "category": "bloatware", "safe": True},
            "Microsoft.WindowsMaps": {"name": "Maps", "category": "bloatware", "safe": True},
            "Microsoft.WindowsSoundRecorder": {
                "name": "Sound Recorder",
                "category": "bloatware",
                "safe": True,
            },
            "Microsoft.MixedReality.Portal": {
                "name": "Mixed Reality Portal",
                "category": "bloatware",
                "safe": True,
            },
            "Microsoft.Messaging": {"name": "Messaging", "category": "bloatware", "safe": True},
            "Microsoft.Print3D": {"name": "Print 3D", "category": "bloatware", "safe": True},
            "Microsoft.OneConnect": {
                "name": "Paid WiFi & Cellular",
                "category": "bloatware",
                "safe": True,
            },
            "Microsoft.Wallet": {"name": "Microsoft Wallet", "category": "bloatware", "safe": True},
            "Microsoft.ScreenSketch": {
                "name": "Snip & Sketch",
                "category": "bloatware",
                "safe": False,
            },  # Some users like it
            "Microsoft.549981C3F5F10": {"name": "Cortana", "category": "bloatware", "safe": True},
            "MicrosoftCorporationII.QuickAssist": {
                "name": "Quick Assist",
                "category": "bloatware",
                "safe": False,
            },
            # Third-party bloatware (OEM installed)
            "king.com.CandyCrushSaga": {
                "name": "Candy Crush Saga",
                "category": "games",
                "safe": True,
            },
            "king.com.CandyCrushSodaSaga": {
                "name": "Candy Crush Soda",
                "category": "games",
                "safe": True,
            },
            "king.com.FarmHeroesSaga": {
                "name": "Farm Heroes Saga",
                "category": "games",
                "safe": True,
            },
            "king.com.BubbleWitch3Saga": {
                "name": "Bubble Witch 3",
                "category": "games",
                "safe": True,
            },
            "Microsoft.MinecraftUWP": {
                "name": "Minecraft (Trial)",
                "category": "games",
                "safe": True,
            },
            "SpotifyAB.SpotifyMusic": {"name": "Spotify", "category": "bloatware", "safe": True},
            "Disney.37853FC22B2CE": {"name": "Disney+", "category": "bloatware", "safe": True},
            "Facebook.Facebook": {"name": "Facebook", "category": "bloatware", "safe": True},
            "Twitter.Twitter": {"name": "Twitter", "category": "bloatware", "safe": True},
            "Clipchamp.Clipchamp": {
                "name": "Clipchamp Video Editor",
                "category": "bloatware",
                "safe": True,
            },
            # Communication (some users may want to keep)
            "Microsoft.SkypeApp": {"name": "Skype", "category": "communication", "safe": True},
            "MicrosoftTeams": {
                "name": "Microsoft Teams",
                "category": "communication",
                "safe": False,
            },
            # OneDrive (special handling required)
            "Microsoft.OneDrive": {"name": "OneDrive (UWP)", "category": "cloud", "safe": False},
            # Edge (requires special removal process)
            "Microsoft.MicrosoftEdge": {
                "name": "Edge Legacy",
                "category": "browser",
                "safe": False,
            },
            "Microsoft.MicrosoftEdgeDevToolsClient": {
                "name": "Edge DevTools",
                "category": "browser",
                "safe": True,
            },
        }

        # Apps that should NEVER be removed (system critical)
        self.CRITICAL_APPS = [
            "Microsoft.Windows.ShellExperienceHost",
            "Microsoft.Windows.ContentDeliveryManager",
            "Microsoft.WindowsStore",
            "Microsoft.StorePurchaseApp",
            "Microsoft.Windows.Photos",
            "Microsoft.WindowsCalculator",
            "Microsoft.Windows.PeopleExperienceHost",
            "Microsoft.AAD.BrokerPlugin",
            "Microsoft.AccountsControl",
            "Microsoft.CredDialogHost",
            "Microsoft.LockApp",
            "Microsoft.Windows.StartMenuExperienceHost",
            "Microsoft.UI.Xaml",
            "Microsoft.VCLibs",
            "Microsoft.NET.Native",
            "Windows.immersivecontrolpanel",
        ]

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

    def detect_installed_apps(self):
        """
        Detect all installed UWP/AppX packages.

        Returns:
            dict: {
                "installed": [...],  # List of installed apps
                "bloatware": [...],  # Known bloatware
                "safe_to_remove": [...],  # Safe to remove
                "critical": [...],  # Critical apps (never remove)
                "total_count": int,
                "bloatware_count": int
            }
        """
        self._log("Escaneando aplicaciones instaladas...", "info")

        try:
            # Get all installed AppX packages
            cmd = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "Get-AppxPackage | Select-Object Name, PackageFullName, Publisher, Version | ConvertTo-Json",
            ]

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
                self._log(f"Error al escanear apps: {result.stderr}", "error")
                return self._empty_result()

            # Parse JSON output
            import json

            try:
                apps_data = json.loads(result.stdout)
            except json.JSONDecodeError:
                self._log("Error al parsear datos de aplicaciones", "error")
                return self._empty_result()

            # Handle single app vs array
            if not isinstance(apps_data, list):
                apps_data = [apps_data]

            # Categorize apps
            installed = []
            bloatware = []
            safe_to_remove = []
            critical = []

            for app in apps_data:
                app_name = app.get("Name", "")
                package_full_name = app.get("PackageFullName", "")
                publisher = app.get("Publisher", "")
                version = app.get("Version", "")

                app_info = {
                    "name": app_name,
                    "package_full_name": package_full_name,
                    "publisher": publisher,
                    "version": version,
                    "is_bloatware": False,
                    "is_critical": False,
                    "safe_to_remove": False,
                    "category": "unknown",
                    "display_name": app_name,
                }

                # Check if critical
                if app_name in self.CRITICAL_APPS:
                    app_info["is_critical"] = True
                    critical.append(app_info)
                # Check if known bloatware
                elif app_name in self.BLOATWARE_APPS:
                    bloatware_info = self.BLOATWARE_APPS[app_name]
                    app_info["is_bloatware"] = True
                    app_info["safe_to_remove"] = bloatware_info["safe"]
                    app_info["category"] = bloatware_info["category"]
                    app_info["display_name"] = bloatware_info["name"]
                    bloatware.append(app_info)

                    if bloatware_info["safe"]:
                        safe_to_remove.append(app_info)

                installed.append(app_info)

            self._log(f"✓ Encontradas {len(installed)} aplicaciones instaladas", "success")
            self._log(f"  • {len(bloatware)} aplicaciones de bloatware detectadas", "info")
            self._log(f"  • {len(safe_to_remove)} seguras para eliminar", "info")
            self._log(f"  • {len(critical)} aplicaciones críticas del sistema", "warning")

            return {
                "installed": installed,
                "bloatware": bloatware,
                "safe_to_remove": safe_to_remove,
                "critical": critical,
                "total_count": len(installed),
                "bloatware_count": len(bloatware),
                "safe_count": len(safe_to_remove),
                "critical_count": len(critical),
            }

        except subprocess.TimeoutExpired:
            self._log("Timeout al escanear aplicaciones", "error")
            return self._empty_result()
        except Exception as e:
            self._log(f"Error al detectar aplicaciones: {str(e)}", "error")
            return self._empty_result()

    def _empty_result(self):
        """Return empty result structure."""
        return {
            "installed": [],
            "bloatware": [],
            "safe_to_remove": [],
            "critical": [],
            "total_count": 0,
            "bloatware_count": 0,
            "safe_count": 0,
            "critical_count": 0,
        }

    def remove_app(self, package_name):
        """
        Remove a single UWP app by package name.

        Args:
            package_name: Full package name or app name

        Returns:
            dict: {"success": bool, "message": str, "actions": []}
        """
        # Check admin
        if not self._is_admin():
            return {
                "success": False,
                "message": "Se requieren privilegios de Administrador",
                "actions": [],
            }

        # Check if critical
        if package_name in self.CRITICAL_APPS:
            return {
                "success": False,
                "message": f"⚠️  {package_name} es crítica del sistema y NO debe eliminarse",
                "actions": [],
            }

        self._log(f"Eliminando {package_name}...", "info")
        actions = []

        try:
            # Remove for current user
            cmd = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                f"Get-AppxPackage *{package_name}* | Remove-AppxPackage",
            ]

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

            if result.returncode == 0:
                actions.append("Eliminada para el usuario actual")
                self._log("  ✓ Eliminada para usuario actual", "success")
            else:
                self._log(f"  ⚠️  Error al eliminar: {result.stderr}", "warning")

            # Remove provisioned package (prevents reinstall for new users)
            cmd_provisioned = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                f"Get-AppxProvisionedPackage -Online | Where-Object {{$_.DisplayName -like '*{package_name}*'}} | Remove-AppxProvisionedPackage -Online",
            ]

            result_prov = subprocess.run(
                cmd_provisioned,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
                creationflags=subprocess.CREATE_NO_WINDOW
                if hasattr(subprocess, "CREATE_NO_WINDOW")
                else 0,
            )

            if result_prov.returncode == 0 and result_prov.stdout.strip():
                actions.append("Eliminado paquete provisionado")
                self._log("  ✓ Paquete provisionado eliminado", "success")

            if len(actions) > 0:
                return {
                    "success": True,
                    "message": f"✓ {package_name} eliminada correctamente",
                    "actions": actions,
                }
            else:
                return {
                    "success": False,
                    "message": f"No se pudo eliminar {package_name}",
                    "actions": [],
                }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "message": "Timeout al intentar eliminar aplicación",
                "actions": actions,
            }
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}", "actions": actions}

    def remove_all_bloatware(self, safe_only=True):
        """
        Remove all detected bloatware.

        Args:
            safe_only: If True, only remove apps marked as safe

        Returns:
            dict: {
                "success": bool,
                "removed_count": int,
                "failed_count": int,
                "removed": [...],
                "failed": [...]
            }
        """
        if not self._is_admin():
            self._log("⚠️  Se requieren privilegios de Administrador", "error")
            return {
                "success": False,
                "removed_count": 0,
                "failed_count": 0,
                "removed": [],
                "failed": [],
            }

        self._log("Iniciando eliminación masiva de bloatware...", "info")

        # Get installed apps
        detection = self.detect_installed_apps()

        if safe_only:
            apps_to_remove = detection["safe_to_remove"]
            self._log(f"Eliminando {len(apps_to_remove)} aplicaciones seguras...", "info")
        else:
            apps_to_remove = detection["bloatware"]
            self._log(f"Eliminando {len(apps_to_remove)} aplicaciones de bloatware...", "warning")

        removed = []
        failed = []

        for app in apps_to_remove:
            app_name = app["name"]
            result = self.remove_app(app_name)

            if result["success"]:
                removed.append(app_name)
            else:
                failed.append(app_name)

        self._log("✓ Eliminación completada:", "success")
        self._log(f"  • {len(removed)} aplicaciones eliminadas", "success")
        if len(failed) > 0:
            self._log(f"  • {len(failed)} aplicaciones fallaron", "warning")

        return {
            "success": len(removed) > 0,
            "removed_count": len(removed),
            "failed_count": len(failed),
            "removed": removed,
            "failed": failed,
        }

    def remove_onedrive(self):
        """
        Remove OneDrive completely (requires special handling).

        Returns:
            dict: {"success": bool, "message": str, "actions": []}
        """
        if not self._is_admin():
            return {
                "success": False,
                "message": "Se requieren privilegios de Administrador",
                "actions": [],
            }

        self._log("Eliminando OneDrive...", "info")
        actions = []

        try:
            # Kill OneDrive processes
            subprocess.run(
                ["taskkill", "/f", "/im", "OneDrive.exe"],
                capture_output=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW
                if hasattr(subprocess, "CREATE_NO_WINDOW")
                else 0,
            )
            actions.append("Procesos de OneDrive detenidos")

            # Uninstall OneDrive (32-bit)
            onedrive_32 = r"C:\Windows\System32\OneDriveSetup.exe"
            if os.path.isfile(onedrive_32):
                subprocess.run(
                    [onedrive_32, "/uninstall"],
                    capture_output=True,
                    timeout=30,
                    creationflags=subprocess.CREATE_NO_WINDOW
                    if hasattr(subprocess, "CREATE_NO_WINDOW")
                    else 0,
                )
                actions.append("OneDrive (32-bit) desinstalado")

            # Uninstall OneDrive (64-bit)
            onedrive_64 = r"C:\Windows\SysWOW64\OneDriveSetup.exe"
            if os.path.isfile(onedrive_64):
                subprocess.run(
                    [onedrive_64, "/uninstall"],
                    capture_output=True,
                    timeout=30,
                    creationflags=subprocess.CREATE_NO_WINDOW
                    if hasattr(subprocess, "CREATE_NO_WINDOW")
                    else 0,
                )
                actions.append("OneDrive (64-bit) desinstalado")

            # Remove from startup
            from winsvalinn.utils.registry_helper import set_registry

            set_registry(
                r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run", "OneDrive", "", "REG_SZ"
            )
            actions.append("Eliminado del inicio automático")

            # Disable OneDrive via Group Policy
            set_registry(
                r"HKLM\SOFTWARE\Policies\Microsoft\Windows\OneDrive",
                "DisableFileSyncNGSC",
                "1",
                "REG_DWORD",
            )
            actions.append("Deshabilitado vía Group Policy")

            self._log(f"✓ OneDrive eliminado - {len(actions)} cambios aplicados", "success")

            return {
                "success": True,
                "message": "✓ OneDrive eliminado correctamente",
                "actions": actions,
            }

        except Exception as e:
            self._log(f"Error al eliminar OneDrive: {str(e)}", "error")
            return {"success": False, "message": f"Error: {str(e)}", "actions": actions}

    def remove_edge(self):
        """
        Remove Microsoft Edge (Chromium) - requires special handling.

        Returns:
            dict: {"success": bool, "message": str, "actions": []}
        """
        if not self._is_admin():
            return {
                "success": False,
                "message": "Se requieren privilegios de Administrador",
                "actions": [],
            }

        self._log("⚠️  Eliminando Microsoft Edge (Chromium)...", "warning")
        self._log("ADVERTENCIA: Esto puede causar problemas con algunas apps de Windows", "warning")
        actions = []

        try:
            # Find Edge installer
            edge_paths = [
                r"C:\Program Files (x86)\Microsoft\Edge\Application",
                r"C:\Program Files\Microsoft\Edge\Application",
            ]

            setup_found = False
            for edge_path in edge_paths:
                # Look for setup.exe in version folders
                if os.path.isdir(edge_path):
                    for item in os.listdir(edge_path):
                        version_path = os.path.join(edge_path, item)
                        if os.path.isdir(version_path):
                            setup_path = os.path.join(version_path, "Installer", "setup.exe")
                            if os.path.isfile(setup_path):
                                # Run uninstaller
                                result = subprocess.run(
                                    [
                                        setup_path,
                                        "--uninstall",
                                        "--force-uninstall",
                                        "--system-level",
                                    ],
                                    capture_output=True,
                                    timeout=60,
                                    creationflags=subprocess.CREATE_NO_WINDOW
                                    if hasattr(subprocess, "CREATE_NO_WINDOW")
                                    else 0,
                                )

                                if result.returncode == 0:
                                    actions.append("Edge desinstalado")
                                    setup_found = True
                                    break

            if not setup_found:
                self._log("No se encontró el instalador de Edge", "warning")

            # Prevent Edge reinstall via updates
            from winsvalinn.utils.registry_helper import set_registry

            set_registry(
                r"HKLM\SOFTWARE\Microsoft\EdgeUpdate",
                "DoNotUpdateToEdgeWithChromium",
                "1",
                "REG_DWORD",
            )
            actions.append("Deshabilitadas actualizaciones de Edge")

            if len(actions) > 0:
                self._log(f"✓ Edge procesado - {len(actions)} cambios aplicados", "success")
                return {
                    "success": True,
                    "message": "✓ Microsoft Edge procesado",
                    "actions": actions,
                }
            else:
                return {
                    "success": False,
                    "message": "No se pudieron aplicar cambios a Edge",
                    "actions": [],
                }

        except Exception as e:
            self._log(f"Error al eliminar Edge: {str(e)}", "error")
            return {"success": False, "message": f"Error: {str(e)}", "actions": actions}

    def get_bloatware_by_category(self):
        """
        Get bloatware apps grouped by category.

        Returns:
            dict: {category_name: [apps]}
        """
        detection = self.detect_installed_apps()
        categories = {}

        for app in detection["bloatware"]:
            category = app["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append(app)

        return categories
