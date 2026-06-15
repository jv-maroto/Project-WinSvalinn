"""
Security Audit - Comprehensive Security Scanning

This module provides:
1. Full security audit/scan
2. BitLocker status and management
3. Secure Boot verification
4. TPM status check
5. Security recommendations
6. Vulnerability detection

Author: WinGuardOptimizer Team
"""

import logging
import subprocess

from winsvalinn.core import cis_mapping  # noqa: E402  (sibling submodule, no GUI)


class SecurityAudit:
    """Comprehensive security auditing and management."""

    def __init__(self, callback=None):
        """
        Initialize SecurityAudit.

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

    # ========== Security Audit ==========

    def run_security_scan(self):
        """
        Run comprehensive security scan.

        Returns:
            dict: {
                "issues": list,
                "warnings": list,
                "passed": list,
                "score": int (0-100)
            }
        """
        try:
            issues = []
            warnings = []
            passed = []

            # Check critical security features
            checks = [
                ("defender", self._check_defender),
                ("firewall", self._check_firewall),
                ("autorun", self._check_autorun),
                ("rdp", self._check_rdp),
                ("smbv1", self._check_smbv1),
                ("uac", self._check_uac),
                ("bitlocker", self._check_bitlocker),
                ("secure_boot", self._check_secure_boot),
                ("updates", self._check_updates),
            ]

            # Run the checks concurrently — each is an independent subprocess /
            # PowerShell call, so wall-clock drops from the sum to ~the slowest.
            from concurrent.futures import ThreadPoolExecutor

            def _run_check(item):
                check_name, check_func = item
                try:
                    result = check_func()
                    result["control"] = check_name
                    return result
                except Exception as e:  # noqa: BLE001
                    self._log(f"Error en verificación {check_name}: {e}", "error")
                    return None

            with ThreadPoolExecutor(max_workers=len(checks)) as pool:
                results = list(pool.map(_run_check, checks))

            for result in results:
                if result is None:
                    continue
                if result["status"] == "fail":
                    issues.append(result)
                elif result["status"] == "warning":
                    warnings.append(result)
                else:
                    passed.append(result)

            # Calculate security score
            total_checks = len(checks)
            passed_count = len(passed)
            score = int((passed_count / total_checks) * 100)

            # Enrich each finding with its CIS Benchmark reference (additive).
            issues = cis_mapping.annotate(issues)
            warnings = cis_mapping.annotate(warnings)
            passed = cis_mapping.annotate(passed)

            return {
                "issues": issues,
                "warnings": warnings,
                "passed": passed,
                "score": score,
                "total_checks": total_checks,
            }

        except Exception as e:
            self._log(f"Error en escaneo de seguridad: {str(e)}", "error")
            return {"issues": [], "warnings": [], "passed": [], "score": 0, "error": str(e)}

    def _detect_third_party_av(self):
        """Detect installed third-party antivirus via WMI."""
        try:
            cmd = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct "
                "| Select-Object -ExpandProperty displayName",
            ]
            result = subprocess.run(
                cmd,
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
                products = [
                    p.strip()
                    for p in result.stdout.strip().splitlines()
                    if p.strip() and "windows defender" not in p.strip().lower()
                ]
                return products
        except Exception:
            pass
        return []

    def _detect_third_party_firewall(self):
        """Detect installed third-party firewall via WMI."""
        try:
            cmd = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "Get-CimInstance -Namespace root/SecurityCenter2 -ClassName FirewallProduct "
                "| Select-Object -ExpandProperty displayName",
            ]
            result = subprocess.run(
                cmd,
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
                products = [p.strip() for p in result.stdout.strip().splitlines() if p.strip()]
                return products
        except Exception:
            pass
        return []

    def _check_defender(self):
        """Check Windows Defender status and detect third-party AV."""
        try:
            # First check for third-party AV
            third_party = self._detect_third_party_av()
            if third_party:
                av_names = ", ".join(third_party)
                return {
                    "name": "Antivirus",
                    "status": "pass",
                    "message": f"✓ Antivirus de terceros detectado: {av_names}",
                }

            cmd = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "Get-MpComputerStatus | Select-Object -ExpandProperty RealTimeProtectionEnabled",
            ]

            result = subprocess.run(
                cmd,
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
                enabled = result.stdout.strip().lower() == "true"

                if enabled:
                    return {
                        "name": "Windows Defender",
                        "status": "pass",
                        "message": "✓ Protección en tiempo real activa",
                    }
                else:
                    return {
                        "name": "Windows Defender",
                        "status": "fail",
                        "message": "❌ Protección en tiempo real desactivada",
                        "recommendation": "Activar Windows Defender o instalar un antivirus",
                    }
            else:
                return {
                    "name": "Windows Defender",
                    "status": "warning",
                    "message": "⚠️ No se pudo verificar el estado",
                }

        except Exception:
            return {
                "name": "Windows Defender",
                "status": "warning",
                "message": "⚠️ Error al verificar",
            }

    def _check_firewall(self):
        """Check Windows Firewall status and detect third-party firewalls."""
        try:
            # Check for third-party firewall first
            third_party_fw = self._detect_third_party_firewall()
            if third_party_fw:
                fw_names = ", ".join(third_party_fw)
                return {
                    "name": "Firewall",
                    "status": "pass",
                    "message": f"✓ Firewall de terceros detectado: {fw_names}",
                }

            cmd = ["netsh", "advfirewall", "show", "allprofiles", "state"]

            result = subprocess.run(
                cmd,
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
                enabled_count = result.stdout.upper().count(
                    "STATE                                 ON"
                )

                if enabled_count >= 2:
                    return {
                        "name": "Windows Firewall",
                        "status": "pass",
                        "message": "✓ Firewall activo",
                    }
                else:
                    return {
                        "name": "Windows Firewall",
                        "status": "fail",
                        "message": "❌ Firewall desactivado o parcialmente activo",
                        "recommendation": "Activar Firewall en todos los perfiles",
                    }

        except Exception as e:
            self._log(f"Error: {str(e)}", "error")

        return {
            "name": "Windows Firewall",
            "status": "warning",
            "message": "⚠️ No se pudo verificar",
        }

    def _check_autorun(self):
        """Check AutoRun status."""
        try:
            from winsvalinn.utils.registry_helper import get_registry

            value, success = get_registry(
                r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer",
                "NoDriveTypeAutoRun",
            )

            if success and value == 255:
                return {
                    "name": "AutoRun/AutoPlay",
                    "status": "pass",
                    "message": "✓ AutoRun deshabilitado",
                }
            else:
                return {
                    "name": "AutoRun/AutoPlay",
                    "status": "fail",
                    "message": "❌ AutoRun habilitado (riesgo de malware USB)",
                    "recommendation": "Deshabilitar AutoRun para prevenir malware de USB",
                }

        except Exception:
            return {
                "name": "AutoRun/AutoPlay",
                "status": "warning",
                "message": "⚠️ No se pudo verificar",
            }

    def _check_rdp(self):
        """Check Remote Desktop status."""
        try:
            from winsvalinn.utils.registry_helper import get_registry

            value, success = get_registry(
                r"HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Terminal Server",
                "fDenyTSConnections",
            )

            if success and value == 1:
                return {
                    "name": "Remote Desktop (RDP)",
                    "status": "pass",
                    "message": "✓ RDP deshabilitado",
                }
            else:
                return {
                    "name": "Remote Desktop (RDP)",
                    "status": "warning",
                    "message": "⚠️ RDP habilitado (riesgo de ataques remotos)",
                    "recommendation": "Deshabilitar RDP si no se usa",
                }

        except Exception:
            return {
                "name": "Remote Desktop (RDP)",
                "status": "warning",
                "message": "⚠️ No se pudo verificar",
            }

    def _check_smbv1(self):
        """Check SMBv1 protocol status."""
        try:
            cmd = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "Get-WindowsOptionalFeature -Online -FeatureName SMB1Protocol | Select-Object -ExpandProperty State",
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
                state = result.stdout.strip().lower()

                if state == "disabled":
                    return {
                        "name": "SMBv1 Protocol",
                        "status": "pass",
                        "message": "✓ SMBv1 deshabilitado",
                    }
                else:
                    return {
                        "name": "SMBv1 Protocol",
                        "status": "fail",
                        "message": "❌ SMBv1 habilitado (vulnerable a WannaCry)",
                        "recommendation": "CRÍTICO: Deshabilitar SMBv1 inmediatamente",
                    }

        except Exception as e:
            self._log(f"Error: {str(e)}", "error")
            pass

        return {"name": "SMBv1 Protocol", "status": "warning", "message": "⚠️ No se pudo verificar"}

    def _check_uac(self):
        """Check UAC status."""
        try:
            from winsvalinn.utils.registry_helper import get_registry

            value, success = get_registry(
                r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System",
                "ConsentPromptBehaviorAdmin",
            )

            if success and value > 0:
                return {
                    "name": "UAC (Control de Cuentas)",
                    "status": "pass",
                    "message": "✓ UAC activo",
                }
            else:
                return {
                    "name": "UAC (Control de Cuentas)",
                    "status": "fail",
                    "message": "❌ UAC desactivado",
                    "recommendation": "Activar UAC para prevenir ejecución no autorizada",
                }

        except Exception:
            return {
                "name": "UAC (Control de Cuentas)",
                "status": "warning",
                "message": "⚠️ No se pudo verificar",
            }

    def _check_bitlocker(self):
        """Check BitLocker encryption status."""
        try:
            cmd = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "Get-BitLockerVolume -MountPoint C: | Select-Object -ExpandProperty ProtectionStatus",
            ]

            result = subprocess.run(
                cmd,
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
                status = result.stdout.strip()

                if "On" in status:
                    return {
                        "name": "BitLocker Encryption",
                        "status": "pass",
                        "message": "✓ Disco C: encriptado con BitLocker",
                    }
                else:
                    return {
                        "name": "BitLocker Encryption",
                        "status": "warning",
                        "message": "⚠️ Disco C: no encriptado",
                        "recommendation": "Considerar habilitar BitLocker para proteger datos",
                    }

        except Exception as e:
            self._log(f"Error: {str(e)}", "error")
            pass

        return {
            "name": "BitLocker Encryption",
            "status": "warning",
            "message": "⚠️ No disponible o no se pudo verificar",
        }

    def _check_secure_boot(self):
        """Check Secure Boot status."""
        try:
            cmd = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "Confirm-SecureBootUEFI",
            ]

            result = subprocess.run(
                cmd,
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
                enabled = result.stdout.strip().lower() == "true"

                if enabled:
                    return {
                        "name": "Secure Boot",
                        "status": "pass",
                        "message": "✓ Secure Boot habilitado",
                    }
                else:
                    return {
                        "name": "Secure Boot",
                        "status": "warning",
                        "message": "⚠️ Secure Boot deshabilitado",
                        "recommendation": "Habilitar Secure Boot en BIOS/UEFI",
                    }

        except Exception as e:
            self._log(f"Error: {str(e)}", "error")
            pass

        return {
            "name": "Secure Boot",
            "status": "warning",
            "message": "⚠️ No disponible (sistema no UEFI) o no se pudo verificar",
        }

    def _check_updates(self):
        """Check Windows Update status."""
        try:
            cmd = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "(New-Object -ComObject Microsoft.Update.AutoUpdate).Settings.NotificationLevel",
            ]

            result = subprocess.run(
                cmd,
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
                level = result.stdout.strip()

                # 1 = Disabled, 2 = Notify, 3 = Download, 4 = Automatic
                if level in ["3", "4"]:
                    return {
                        "name": "Windows Updates",
                        "status": "pass",
                        "message": "✓ Updates automáticas activas",
                    }
                else:
                    return {
                        "name": "Windows Updates",
                        "status": "warning",
                        "message": "⚠️ Updates no automáticas",
                        "recommendation": "Habilitar updates automáticas para parches de seguridad",
                    }

        except Exception as e:
            self._log(f"Error: {str(e)}", "error")
            pass

        return {"name": "Windows Updates", "status": "warning", "message": "⚠️ No se pudo verificar"}

    # ========== BitLocker Management ==========

    def get_bitlocker_status(self):
        """
        Get BitLocker status for all drives.

        Returns:
            dict: {"success": bool, "drives": list}
        """
        try:
            cmd = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "Get-BitLockerVolume | Select-Object MountPoint, VolumeStatus, "
                "EncryptionPercentage, ProtectionStatus | ConvertTo-Json",
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

            if result.returncode == 0 and result.stdout.strip():
                import json

                drives_data = json.loads(result.stdout)

                # Handle single drive vs array
                if not isinstance(drives_data, list):
                    drives_data = [drives_data]

                drives = []
                for drive in drives_data:
                    drives.append(
                        {
                            "mount_point": drive.get("MountPoint", "Unknown"),
                            "status": drive.get("VolumeStatus", "Unknown"),
                            "encryption_percentage": drive.get("EncryptionPercentage", 0),
                            "protection_status": drive.get("ProtectionStatus", "Unknown"),
                        }
                    )

                return {"success": True, "drives": drives}

        except Exception as e:
            self._log(f"Error: {str(e)}", "error")

        return {
            "success": False,
            "drives": [],
            "message": "BitLocker no disponible o error al leer estado",
        }

    def enable_bitlocker(self, drive="C:"):
        """
        Enable BitLocker on a drive.

        Args:
            drive: Drive letter (e.g., "C:")

        Returns:
            dict: {"success": bool, "message": str}
        """
        if not self._is_admin():
            return {"success": False, "message": "Se requieren privilegios de Administrador"}

        return {
            "success": False,
            "message": "BitLocker debe habilitarse manualmente desde Configuración de Windows.\n"
            "Panel de Control > Sistema y Seguridad > Cifrado de unidad BitLocker",
        }

    def get_tpm_status(self):
        """
        Get TPM (Trusted Platform Module) status.

        Returns:
            dict: {"present": bool, "ready": bool, "version": str}
        """
        try:
            cmd = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "Get-Tpm | Select-Object TpmPresent, TpmReady, ManufacturerVersion | ConvertTo-Json",
            ]

            result = subprocess.run(
                cmd,
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
                import json

                tpm_data = json.loads(result.stdout)

                return {
                    "present": tpm_data.get("TpmPresent", False),
                    "ready": tpm_data.get("TpmReady", False),
                    "version": tpm_data.get("ManufacturerVersion", "Unknown"),
                }

        except Exception as e:
            self._log(f"Error: {str(e)}", "error")
            pass

        return {
            "present": False,
            "ready": False,
            "version": "Unknown",
            "error": "TPM no disponible",
        }
