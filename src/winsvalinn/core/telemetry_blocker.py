"""
Telemetry Blocker - Disable ALL Windows Telemetry

Blocks all known Microsoft telemetry, tracking, and data collection services.
Based on O&O ShutUp10++ and privacy-focused tools.
"""

import platform
import subprocess
from datetime import datetime

from winsvalinn.utils.logger import ModuleLogger
from winsvalinn.utils.registry_helper import get_registry, set_registry

logger = ModuleLogger("TelemetryBlocker")


class TelemetryBlocker:
    """Comprehensive Windows telemetry blocker."""

    def __init__(self, callback=None):
        """
        Initialize telemetry blocker.

        Args:
            callback: Optional GUI logging callback
        """
        self.callback = callback or (lambda msg, level="info": None)
        self.is_windows = platform.system() == "Windows"

    def log(self, message, level="info"):
        """Log to both GUI and file."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.callback(f"[{timestamp}] {message}", level)
        log_method = getattr(logger, level.lower(), logger.info)
        log_method(message)

    # ═══════════════════════════════════════════════════════════════
    # Detection Methods
    # ═══════════════════════════════════════════════════════════════

    def detect_telemetry_status(self):
        """
        Detect current telemetry status.

        Returns:
            Dict with status of all telemetry components
        """
        logger.info("Detecting telemetry status...")
        self.log("Detectando estado de telemetría...", "info")

        results = {
            "diagtrack": self._check_diagtrack(),
            "dmwappushservice": self._check_dmwappush(),
            "data_collection": self._check_data_collection(),
            "advertising_id": self._check_advertising_id(),
            "activity_history": self._check_activity_history(),
            "timeline": self._check_timeline(),
            "feedback": self._check_feedback(),
            "cloud_content": self._check_cloud_content(),
            "consumer_features": self._check_consumer_features(),
            "error_reporting": self._check_error_reporting(),
            "app_telemetry": self._check_app_telemetry(),
        }

        # Count active
        active_count = sum(1 for r in results.values() if r.get("active", False))
        results["summary"] = {
            "total": len(results) - 1,  # -1 for summary itself
            "active": active_count,
            "blocked": len(results) - 1 - active_count,
        }

        self.log(
            f"Telemetría: {active_count} activas, {len(results) - 1 - active_count} bloqueadas",
            "warning" if active_count > 0 else "success",
        )

        return results

    def _check_diagtrack(self):
        """Check DiagTrack (Connected User Experiences and Telemetry) service."""
        try:
            result = subprocess.run(
                ["sc", "query", "DiagTrack"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW
                if hasattr(subprocess, "CREATE_NO_WINDOW")
                else 0,
            )
            is_running = "RUNNING" in result.stdout
            return {
                "name": "DiagTrack Service",
                "active": is_running,
                "description": "Servicio principal de telemetría de Windows",
                "privacy_impact": "HIGH",
            }
        except Exception as e:
            logger.error(f"Error checking DiagTrack: {e}")
            return {"name": "DiagTrack Service", "active": False, "error": str(e)}

    def _check_dmwappush(self):
        """Check dmwappushservice (WAP Push Message Routing)."""
        try:
            result = subprocess.run(
                ["sc", "query", "dmwappushservice"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW
                if hasattr(subprocess, "CREATE_NO_WINDOW")
                else 0,
            )
            is_running = "RUNNING" in result.stdout
            return {
                "name": "WAP Push Service",
                "active": is_running,
                "description": "Servicio de mensajes push de Microsoft",
                "privacy_impact": "MEDIUM",
            }
        except Exception:
            return {"name": "WAP Push Service", "active": False}

    def _check_data_collection(self):
        """Check Data Collection registry setting."""
        success, value = get_registry(
            r"HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection", "AllowTelemetry"
        )

        # 0 = Security, 1 = Basic, 2 = Enhanced, 3 = Full
        telemetry_level = int(value) if success and value else 3
        is_active = telemetry_level > 0

        return {
            "name": "Data Collection",
            "active": is_active,
            "level": telemetry_level,
            "description": f"Nivel de telemetría: {['Seguridad', 'Básico', 'Mejorado', 'Completo'][min(telemetry_level, 3)]}",
            "privacy_impact": "HIGH",
        }

    def _check_advertising_id(self):
        """Check Advertising ID setting."""
        success, value = get_registry(
            r"HKCU\Software\Microsoft\Windows\CurrentVersion\AdvertisingInfo", "Enabled"
        )
        is_enabled = value == "1" if success else True
        return {
            "name": "Advertising ID",
            "active": is_enabled,
            "description": "ID de publicidad para anuncios personalizados",
            "privacy_impact": "MEDIUM",
        }

    def _check_activity_history(self):
        """Check Activity History (Timeline)."""
        success, value = get_registry(
            r"HKLM\SOFTWARE\Policies\Microsoft\Windows\System", "EnableActivityFeed"
        )
        is_enabled = value != "0" if success else True
        return {
            "name": "Activity History",
            "active": is_enabled,
            "description": "Historial de actividad y Timeline",
            "privacy_impact": "MEDIUM",
        }

    def _check_timeline(self):
        """Check Timeline feature."""
        success, value = get_registry(
            r"HKLM\SOFTWARE\Policies\Microsoft\Windows\System", "PublishUserActivities"
        )
        is_enabled = value != "0" if success else True
        return {
            "name": "Timeline",
            "active": is_enabled,
            "description": "Línea de tiempo de Windows",
            "privacy_impact": "MEDIUM",
        }

    def _check_feedback(self):
        """Check Windows Feedback frequency."""
        success, value = get_registry(r"HKCU\Software\Microsoft\Siuf\Rules", "NumberOfSIUFInPeriod")
        is_enabled = value != "0" if success else True
        return {
            "name": "Windows Feedback",
            "active": is_enabled,
            "description": "Solicitudes de feedback de Windows",
            "privacy_impact": "LOW",
        }

    def _check_cloud_content(self):
        """Check Cloud Content/Consumer Features."""
        success, value = get_registry(
            r"HKCU\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager",
            "SubscribedContent-338389Enabled",
        )
        is_enabled = value != "0" if success else True
        return {
            "name": "Cloud Content",
            "active": is_enabled,
            "description": "Sugerencias y contenido de la nube",
            "privacy_impact": "MEDIUM",
        }

    def _check_consumer_features(self):
        """Check Consumer Features (App suggestions)."""
        success, value = get_registry(
            r"HKLM\SOFTWARE\Policies\Microsoft\Windows\CloudContent",
            "DisableWindowsConsumerFeatures",
        )
        is_disabled = value == "1" if success else False
        return {
            "name": "Consumer Features",
            "active": not is_disabled,
            "description": "Sugerencias de apps y contenido comercial",
            "privacy_impact": "MEDIUM",
        }

    def _check_error_reporting(self):
        """Check Windows Error Reporting."""
        success, value = get_registry(
            r"HKLM\SOFTWARE\Microsoft\Windows\Windows Error Reporting", "Disabled"
        )
        is_disabled = value == "1" if success else False
        return {
            "name": "Error Reporting",
            "active": not is_disabled,
            "description": "Informes de errores a Microsoft",
            "privacy_impact": "MEDIUM",
        }

    def _check_app_telemetry(self):
        """Check Application Telemetry."""
        success, value = get_registry(
            r"HKLM\SOFTWARE\Policies\Microsoft\Windows\AppCompat", "AITEnable"
        )
        is_enabled = value != "0" if success else True
        return {
            "name": "App Telemetry",
            "active": is_enabled,
            "description": "Telemetría de compatibilidad de aplicaciones",
            "privacy_impact": "MEDIUM",
        }

    # ═══════════════════════════════════════════════════════════════
    # Blocking Methods
    # ═══════════════════════════════════════════════════════════════

    def block_all_telemetry(self):
        """
        Block ALL telemetry at once.

        Returns:
            Dict with results
        """
        logger.info("Blocking all telemetry...")
        self.log("", "info")
        self.log("🛡️ Bloqueando TODA la telemetría de Windows...", "warning")

        results = {
            "services": self._disable_telemetry_services(),
            "registry": self._apply_telemetry_registry_tweaks(),
            "tasks": self._disable_telemetry_tasks(),
            "firewall": self._block_telemetry_domains(),
        }

        total_actions = sum(len(r.get("actions", [])) for r in results.values())
        self.log(f"✓ Telemetría bloqueada: {total_actions} cambios aplicados", "success")

        return results

    def _disable_telemetry_services(self):
        """Disable all telemetry services."""
        self.log("Deshabilitando servicios de telemetría...", "info")

        services_to_disable = [
            "DiagTrack",  # Connected User Experiences and Telemetry
            "dmwappushservice",  # WAP Push Message Routing Service
            "diagnosticshub.standardcollector.service",  # Diagnostic Hub
            "DPS",  # Diagnostic Policy Service
            "WerSvc",  # Windows Error Reporting
            "WMPNetworkSvc",  # Windows Media Player Network Sharing
            "RetailDemo",  # Retail Demo Service
            "RemoteRegistry",  # Remote Registry
        ]

        actions = []
        for service in services_to_disable:
            try:
                # Stop service
                subprocess.run(
                    ["sc", "stop", service],
                    capture_output=True,
                    timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW
                    if hasattr(subprocess, "CREATE_NO_WINDOW")
                    else 0,
                )

                # Disable service
                result = subprocess.run(
                    ["sc", "config", service, "start=", "disabled"],
                    capture_output=True,
                    timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW
                    if hasattr(subprocess, "CREATE_NO_WINDOW")
                    else 0,
                )

                if result.returncode == 0:
                    actions.append(f"Deshabilitado servicio: {service}")
                    logger.info(f"Disabled service: {service}")
            except Exception as e:
                logger.debug(f"Could not disable {service}: {e}")

        return {"success": True, "actions": actions}

    def _apply_telemetry_registry_tweaks(self):
        """Apply registry tweaks to block telemetry."""
        self.log("Aplicando ajustes de registro...", "info")

        tweaks = [
            # Data Collection
            (
                r"HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection",
                "AllowTelemetry",
                "0",
                "REG_DWORD",
            ),
            (
                r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\DataCollection",
                "AllowTelemetry",
                "0",
                "REG_DWORD",
            ),
            # Advertising ID
            (
                r"HKCU\Software\Microsoft\Windows\CurrentVersion\AdvertisingInfo",
                "Enabled",
                "0",
                "REG_DWORD",
            ),
            (
                r"HKLM\SOFTWARE\Policies\Microsoft\Windows\AdvertisingInfo",
                "DisabledByGroupPolicy",
                "1",
                "REG_DWORD",
            ),
            # Activity History
            (
                r"HKLM\SOFTWARE\Policies\Microsoft\Windows\System",
                "EnableActivityFeed",
                "0",
                "REG_DWORD",
            ),
            (
                r"HKLM\SOFTWARE\Policies\Microsoft\Windows\System",
                "PublishUserActivities",
                "0",
                "REG_DWORD",
            ),
            (
                r"HKLM\SOFTWARE\Policies\Microsoft\Windows\System",
                "UploadUserActivities",
                "0",
                "REG_DWORD",
            ),
            # Windows Feedback
            (r"HKCU\Software\Microsoft\Siuf\Rules", "NumberOfSIUFInPeriod", "0", "REG_DWORD"),
            (
                r"HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection",
                "DoNotShowFeedbackNotifications",
                "1",
                "REG_DWORD",
            ),
            # Cloud Content
            (
                r"HKCU\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager",
                "SubscribedContent-338389Enabled",
                "0",
                "REG_DWORD",
            ),
            (
                r"HKCU\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager",
                "SilentInstalledAppsEnabled",
                "0",
                "REG_DWORD",
            ),
            (
                r"HKCU\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager",
                "SystemPaneSuggestionsEnabled",
                "0",
                "REG_DWORD",
            ),
            # Consumer Features
            (
                r"HKLM\SOFTWARE\Policies\Microsoft\Windows\CloudContent",
                "DisableWindowsConsumerFeatures",
                "1",
                "REG_DWORD",
            ),
            # Error Reporting
            (
                r"HKLM\SOFTWARE\Microsoft\Windows\Windows Error Reporting",
                "Disabled",
                "1",
                "REG_DWORD",
            ),
            (
                r"HKLM\SOFTWARE\Policies\Microsoft\Windows\Windows Error Reporting",
                "Disabled",
                "1",
                "REG_DWORD",
            ),
            # App Telemetry
            (r"HKLM\SOFTWARE\Policies\Microsoft\Windows\AppCompat", "AITEnable", "0", "REG_DWORD"),
            (
                r"HKLM\SOFTWARE\Policies\Microsoft\Windows\AppCompat",
                "DisableInventory",
                "1",
                "REG_DWORD",
            ),
            # Location Tracking
            (
                r"HKLM\SOFTWARE\Policies\Microsoft\Windows\LocationAndSensors",
                "DisableLocation",
                "1",
                "REG_DWORD",
            ),
            (
                r"HKLM\SOFTWARE\Policies\Microsoft\Windows\LocationAndSensors",
                "DisableWindowsLocationProvider",
                "1",
                "REG_DWORD",
            ),
            # Steps Recorder
            (r"HKLM\SOFTWARE\Policies\Microsoft\Windows\AppCompat", "DisableUAR", "1", "REG_DWORD"),
            # Compatibility Telemetry
            (r"HKLM\SOFTWARE\Policies\Microsoft\Windows\AppCompat", "DisablePCA", "1", "REG_DWORD"),
            # CEIP (Customer Experience Improvement Program)
            (r"HKLM\SOFTWARE\Policies\Microsoft\SQMClient\Windows", "CEIPEnable", "0", "REG_DWORD"),
            # Prevent using diagnostic data
            (
                r"HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection",
                "LimitDiagnosticLogCollection",
                "1",
                "REG_DWORD",
            ),
            (
                r"HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection",
                "LimitDumpCollection",
                "1",
                "REG_DWORD",
            ),
        ]

        actions = []
        for reg_path, name, value, reg_type in tweaks:
            success, msg = set_registry(reg_path, name, value, reg_type)
            if success:
                actions.append(f"Registry: {name} = {value}")

        return {"success": True, "actions": actions}

    def _disable_telemetry_tasks(self):
        """Disable telemetry-related scheduled tasks."""
        self.log("Deshabilitando tareas programadas de telemetría...", "info")

        tasks_to_disable = [
            r"\Microsoft\Windows\Application Experience\Microsoft Compatibility Appraiser",
            r"\Microsoft\Windows\Application Experience\ProgramDataUpdater",
            r"\Microsoft\Windows\Autochk\Proxy",
            r"\Microsoft\Windows\Customer Experience Improvement Program\Consolidator",
            r"\Microsoft\Windows\Customer Experience Improvement Program\UsbCeip",
            r"\Microsoft\Windows\DiskDiagnostic\Microsoft-Windows-DiskDiagnosticDataCollector",
            r"\Microsoft\Windows\Feedback\Siuf\DmClient",
            r"\Microsoft\Windows\Feedback\Siuf\DmClientOnScenarioDownload",
            r"\Microsoft\Windows\Windows Error Reporting\QueueReporting",
            r"\Microsoft\Windows\Application Experience\MareBackup",
            r"\Microsoft\Windows\Application Experience\StartupAppTask",
            r"\Microsoft\Windows\Application Experience\PcaPatchDbTask",
            r"\Microsoft\Windows\Maps\MapsUpdateTask",
        ]

        actions = []
        for task in tasks_to_disable:
            try:
                result = subprocess.run(
                    ["schtasks", "/change", "/tn", task, "/disable"],
                    capture_output=True,
                    timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW
                    if hasattr(subprocess, "CREATE_NO_WINDOW")
                    else 0,
                )
                if result.returncode == 0:
                    actions.append(f"Tarea deshabilitada: {task.split('\\')[-1]}")
                    logger.info(f"Disabled task: {task}")
            except Exception as e:
                logger.debug(f"Could not disable task {task}: {e}")

        return {"success": True, "actions": actions}

    def _block_telemetry_domains(self):
        """
        Note: Actual hosts file blocking is handled by hosts_manager.py
        This just returns info about which domains should be blocked.
        """
        telemetry_domains = [
            "vortex.data.microsoft.com",
            "vortex-win.data.microsoft.com",
            "telecommand.telemetry.microsoft.com",
            "oca.telemetry.microsoft.com",
            "watson.telemetry.microsoft.com",
            "sqm.telemetry.microsoft.com",
            "corpext.msitadfs.glbdns2.microsoft.com",
            "watson.live.com",
            "watson.microsoft.com",
            "statsfe2.ws.microsoft.com",
            "reports.wes.df.telemetry.microsoft.com",
            "services.wes.df.telemetry.microsoft.com",
            "sqm.df.telemetry.microsoft.com",
        ]

        return {
            "success": True,
            "actions": [f"Dominio telemetría identificado: {len(telemetry_domains)} dominios"],
            "domains": telemetry_domains,
        }


# Example usage
if __name__ == "__main__":
    from winsvalinn.utils.logger import setup_logging

    setup_logging()

    blocker = TelemetryBlocker()

    print("\n=== DETECTING TELEMETRY STATUS ===\n")
    status = blocker.detect_telemetry_status()

    for key, value in status.items():
        if key != "summary" and isinstance(value, dict):
            status_icon = "🔴" if value.get("active") else "🟢"
            print(
                f"{status_icon} {value.get('name', key)}: {'ACTIVE' if value.get('active') else 'BLOCKED'}"
            )

    print(
        f"\n📊 Summary: {status['summary']['active']} active, {status['summary']['blocked']} blocked\n"
    )

    # Uncomment to block all telemetry
    # print("\n=== BLOCKING ALL TELEMETRY ===\n")
    # results = blocker.block_all_telemetry()
