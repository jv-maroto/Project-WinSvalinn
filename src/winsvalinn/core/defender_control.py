"""
Windows Defender Control - Manage Windows Defender Security

This module allows users to:
1. Check Windows Defender status
2. Enable/disable real-time protection
3. Manage exclusions (files, folders, processes)
4. Configure ransomware protection
5. Control SmartScreen
6. Manage cloud-based protection
7. Configure scan settings

Author: WinGuardOptimizer Team
"""

import json
import logging
import subprocess
import winreg


class DefenderControl:
    """Manage Windows Defender settings."""

    def __init__(self, callback=None):
        """
        Initialize DefenderControl.

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

    def get_defender_status(self):
        """
        Get Windows Defender status.

        Returns:
            dict: {
                "enabled": bool,
                "real_time_protection": bool,
                "cloud_protection": bool,
                "tamper_protection": bool,
                "antivirus_enabled": bool,
                "firewall_enabled": bool,
                "smartscreen_enabled": bool,
                "ransomware_protection": bool
            }
        """
        try:
            status = {
                "enabled": False,
                "real_time_protection": False,
                "cloud_protection": False,
                "tamper_protection": False,
                "antivirus_enabled": False,
                "firewall_enabled": False,
                "smartscreen_enabled": False,
                "ransomware_protection": False,
            }

            # Check Defender status via PowerShell
            cmd = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "Get-MpComputerStatus | Select-Object RealTimeProtectionEnabled, "
                "IoavProtectionEnabled, AntivirusEnabled, AntispywareEnabled, "
                "BehaviorMonitorEnabled, NISEnabled, OnAccessProtectionEnabled, "
                "IsTamperProtected | ConvertTo-Json",
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

            if result.returncode == 0:
                try:
                    if not result.stdout or not result.stdout.strip():
                        return status
                    defender_data = json.loads(result.stdout)

                    status["real_time_protection"] = defender_data.get(
                        "RealTimeProtectionEnabled", False
                    )
                    status["antivirus_enabled"] = defender_data.get("AntivirusEnabled", False)
                    status["tamper_protection"] = defender_data.get("IsTamperProtected", False)
                    status["enabled"] = status["antivirus_enabled"]

                except json.JSONDecodeError:
                    pass

            # Check SmartScreen
            try:
                with winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer",
                    0,
                    winreg.KEY_READ,
                ) as key:
                    value, _ = winreg.QueryValueEx(key, "SmartScreenEnabled")
                    status["smartscreen_enabled"] = value == "On" or value == "Warn"
            except (FileNotFoundError, PermissionError, OSError) as e:
                self._log(f"Could not check SmartScreen: {str(e)}", "debug")

            # Check Controlled Folder Access (Ransomware Protection)
            cmd_ransomware = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "Get-MpPreference | Select-Object EnableControlledFolderAccess | ConvertTo-Json",
            ]

            result_ransomware = subprocess.run(
                cmd_ransomware,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW
                if hasattr(subprocess, "CREATE_NO_WINDOW")
                else 0,
            )

            if result_ransomware.returncode == 0:
                try:
                    if result_ransomware.stdout and result_ransomware.stdout.strip():
                        ransomware_data = json.loads(result_ransomware.stdout)
                        # 0 = Disabled, 1 = Enabled, 2 = Audit
                        status["ransomware_protection"] = (
                            ransomware_data.get("EnableControlledFolderAccess", 0) == 1
                        )
                except (json.JSONDecodeError, ValueError) as e:
                    self._log(f"Error parsing ransomware status: {str(e)}", "warning")

            self._log("✓ Estado de Defender obtenido", "success")
            return status

        except Exception as e:
            self._log(f"Error al obtener estado de Defender: {str(e)}", "error")
            return {
                "enabled": False,
                "real_time_protection": False,
                "cloud_protection": False,
                "tamper_protection": False,
                "antivirus_enabled": False,
                "firewall_enabled": False,
                "smartscreen_enabled": False,
                "ransomware_protection": False,
                "error": str(e),
            }

    def enable_real_time_protection(self):
        """
        Enable Windows Defender real-time protection.

        Returns:
            dict: {"success": bool, "message": str}
        """
        if not self._is_admin():
            return {"success": False, "message": "Se requieren privilegios de Administrador"}

        try:
            cmd = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "Set-MpPreference -DisableRealtimeMonitoring $false",
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

            if result.returncode == 0:
                self._log("✓ Protección en tiempo real habilitada", "success")
                return {"success": True, "message": "✓ Protección en tiempo real habilitada"}
            else:
                return {"success": False, "message": f"Error: {result.stderr}"}

        except Exception as e:
            self._log(f"Error al habilitar protección en tiempo real: {str(e)}", "error")
            return {"success": False, "message": f"Error: {str(e)}"}

    def disable_real_time_protection(self):
        """
        Disable Windows Defender real-time protection.

        WARNING: This reduces security. Only for testing or troubleshooting.

        Returns:
            dict: {"success": bool, "message": str}
        """
        if not self._is_admin():
            return {"success": False, "message": "Se requieren privilegios de Administrador"}

        try:
            cmd = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "Set-MpPreference -DisableRealtimeMonitoring $true",
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

            if result.returncode == 0:
                self._log("⚠️ Protección en tiempo real deshabilitada", "warning")
                return {"success": True, "message": "⚠️ Protección en tiempo real deshabilitada"}
            else:
                return {"success": False, "message": f"Error: {result.stderr}"}

        except Exception as e:
            self._log(f"Error al deshabilitar protección: {str(e)}", "error")
            return {"success": False, "message": f"Error: {str(e)}"}

    def enable_ransomware_protection(self):
        """
        Enable Controlled Folder Access (Ransomware Protection).

        Returns:
            dict: {"success": bool, "message": str}
        """
        if not self._is_admin():
            return {"success": False, "message": "Se requieren privilegios de Administrador"}

        try:
            cmd = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "Set-MpPreference -EnableControlledFolderAccess Enabled",
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

            if result.returncode == 0:
                self._log("✓ Protección contra ransomware habilitada", "success")
                return {"success": True, "message": "✓ Protección contra ransomware habilitada"}
            else:
                return {"success": False, "message": f"Error: {result.stderr}"}

        except Exception as e:
            self._log(f"Error al habilitar protección contra ransomware: {str(e)}", "error")
            return {"success": False, "message": f"Error: {str(e)}"}

    def disable_ransomware_protection(self):
        """
        Disable Controlled Folder Access (Ransomware Protection).

        Returns:
            dict: {"success": bool, "message": str}
        """
        if not self._is_admin():
            return {"success": False, "message": "Se requieren privilegios de Administrador"}

        try:
            cmd = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "Set-MpPreference -EnableControlledFolderAccess Disabled",
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

            if result.returncode == 0:
                self._log("⚠️ Protección contra ransomware deshabilitada", "warning")
                return {"success": True, "message": "⚠️ Protección contra ransomware deshabilitada"}
            else:
                return {"success": False, "message": f"Error: {result.stderr}"}

        except Exception as e:
            self._log(f"Error: {str(e)}", "error")
            return {"success": False, "message": f"Error: {str(e)}"}

    def quick_scan(self):
        """
        Run a quick Windows Defender scan.

        Returns:
            dict: {"success": bool, "message": str}
        """
        if not self._is_admin():
            return {"success": False, "message": "Se requieren privilegios de Administrador"}

        try:
            self._log("🔍 Iniciando escaneo rápido...", "info")

            cmd = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "Start-MpScan -ScanType QuickScan",
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=300,  # 5 minutes max
                creationflags=subprocess.CREATE_NO_WINDOW
                if hasattr(subprocess, "CREATE_NO_WINDOW")
                else 0,
            )

            if result.returncode == 0:
                self._log("✓ Escaneo rápido completado", "success")
                return {"success": True, "message": "✓ Escaneo rápido completado"}
            else:
                return {"success": False, "message": f"Error en escaneo: {result.stderr}"}

        except subprocess.TimeoutExpired:
            return {"success": False, "message": "Escaneo tomó demasiado tiempo (>5 min)"}
        except Exception as e:
            self._log(f"Error en escaneo: {str(e)}", "error")
            return {"success": False, "message": f"Error: {str(e)}"}

    def update_definitions(self):
        """
        Update Windows Defender virus definitions.

        Returns:
            dict: {"success": bool, "message": str}
        """
        if not self._is_admin():
            return {"success": False, "message": "Se requieren privilegios de Administrador"}

        try:
            self._log("📥 Actualizando definiciones de virus...", "info")

            cmd = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "Update-MpSignature",
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
                creationflags=subprocess.CREATE_NO_WINDOW
                if hasattr(subprocess, "CREATE_NO_WINDOW")
                else 0,
            )

            if result.returncode == 0:
                self._log("✓ Definiciones actualizadas", "success")
                return {"success": True, "message": "✓ Definiciones de virus actualizadas"}
            else:
                return {"success": False, "message": f"Error: {result.stderr}"}

        except Exception as e:
            self._log(f"Error al actualizar definiciones: {str(e)}", "error")
            return {"success": False, "message": f"Error: {str(e)}"}

    def get_threat_history(self):
        """
        Get recent threat detections.

        Returns:
            dict: {"success": bool, "threats": list, "count": int}
        """
        try:
            cmd = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "Get-MpThreatDetection | Select-Object -First 10 | "
                "Select-Object ThreatName, Resources, InitialDetectionTime | ConvertTo-Json",
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

            if result.returncode == 0 and result.stdout and result.stdout.strip():
                try:
                    threats_data = json.loads(result.stdout)

                    # Handle single threat vs array
                    if not isinstance(threats_data, list):
                        threats_data = [threats_data]

                    threats = []
                    for threat in threats_data:
                        threats.append(
                            {
                                "name": threat.get("ThreatName", "Unknown"),
                                "path": threat.get("Resources", ["Unknown"])[0]
                                if threat.get("Resources")
                                else "Unknown",
                                "time": threat.get("InitialDetectionTime", "Unknown"),
                            }
                        )

                    return {"success": True, "threats": threats, "count": len(threats)}
                except (json.JSONDecodeError, ValueError, KeyError) as e:
                    self._log(f"Error parsing threats data: {str(e)}", "warning")

            return {
                "success": True,
                "threats": [],
                "count": 0,
                "message": "No se encontraron amenazas recientes",
            }

        except Exception as e:
            return {"success": False, "threats": [], "count": 0, "message": f"Error: {str(e)}"}

    def detect_third_party_antivirus(self):
        """
        Detect third-party antivirus software.

        Returns:
            dict: {"found": bool, "products": list}
        """
        try:
            cmd = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct | "
                "Select-Object displayName, productState | ConvertTo-Json",
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

            if result.returncode == 0 and result.stdout and result.stdout.strip():
                try:
                    av_data = json.loads(result.stdout)

                    # Handle single product vs array
                    if not isinstance(av_data, list):
                        av_data = [av_data]

                    products = []
                    for av in av_data:
                        name = av.get("displayName", "Unknown")
                        # Skip Windows Defender
                        if "windows defender" not in name.lower():
                            # productState is a hex value: check if enabled
                            state = av.get("productState", 0)
                            enabled = (state & 0x1000) != 0  # Bit 12 indicates enabled

                            products.append({"name": name, "enabled": enabled})

                    if products:
                        self._log(
                            f"✓ Antivirus de terceros detectado: {', '.join([p['name'] for p in products])}",
                            "warning",
                        )
                        return {"found": True, "products": products, "count": len(products)}

                except (json.JSONDecodeError, ValueError, KeyError) as e:
                    self._log(f"Error parsing antivirus data: {str(e)}", "warning")

            return {"found": False, "products": [], "count": 0}

        except Exception as e:
            return {"found": False, "products": [], "count": 0, "error": str(e)}

    def detect_third_party_firewall(self):
        """
        Detect third-party firewall software.

        Returns:
            dict: {"found": bool, "products": list}
        """
        try:
            cmd = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "Get-CimInstance -Namespace root/SecurityCenter2 -ClassName FirewallProduct | "
                "Select-Object displayName, productState | ConvertTo-Json",
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

            if result.returncode == 0 and result.stdout and result.stdout.strip():
                try:
                    fw_data = json.loads(result.stdout)

                    # Handle single product vs array
                    if not isinstance(fw_data, list):
                        fw_data = [fw_data]

                    products = []
                    for fw in fw_data:
                        name = fw.get("displayName", "Unknown")
                        # Skip Windows Firewall
                        if "windows" not in name.lower() or "defender" in name.lower():
                            state = fw.get("productState", 0)
                            enabled = (state & 0x1000) != 0

                            products.append({"name": name, "enabled": enabled})

                    if products:
                        self._log(
                            f"✓ Firewall de terceros detectado: {', '.join([p['name'] for p in products])}",
                            "warning",
                        )
                        return {"found": True, "products": products, "count": len(products)}

                except (json.JSONDecodeError, ValueError, KeyError) as e:
                    self._log(f"Error parsing firewall data: {str(e)}", "warning")

            return {"found": False, "products": [], "count": 0}

        except Exception as e:
            return {"found": False, "products": [], "count": 0, "error": str(e)}
