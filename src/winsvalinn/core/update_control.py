"""
Windows Update Control - Manage Windows Update settings

This module allows users to:
1. Check Windows Update status
2. Pause/resume updates
3. Disable/enable automatic updates
4. Configure update behavior (metered connection trick)
5. Check for updates manually
6. View update history

Author: WinGuardOptimizer Team
"""

import logging
import subprocess
from datetime import datetime, timedelta


class UpdateControl:
    """Manage Windows Update settings and behavior."""

    def __init__(self, callback=None):
        """
        Initialize UpdateControl.

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

    def get_update_status(self):
        """
        Get current Windows Update status.

        Returns:
            dict: {
                "success": bool,
                "paused": bool,
                "paused_until": str,
                "auto_updates_enabled": bool,
                "metered_connection": bool,
                "pending_updates": int
            }
        """
        try:
            from winsvalinn.utils.registry_helper import get_registry

            status = {
                "success": True,
                "paused": False,
                "paused_until": None,
                "auto_updates_enabled": True,
                "metered_connection": False,
                "pending_updates": 0,
            }

            # Check if updates are paused
            pause_key = r"HKLM\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings"

            success, pause_until = get_registry(pause_key, "PauseUpdatesExpiryTime")
            if success and pause_until:
                status["paused"] = True
                status["paused_until"] = str(pause_until)

            # Check auto update setting
            au_key = r"HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU"
            success, no_auto_update = get_registry(au_key, "NoAutoUpdate")
            if success and no_auto_update == 1:
                status["auto_updates_enabled"] = False

            # Check metered connection
            # Note: This is per-connection, would need to check all connections
            # Simplified check for now

            return status

        except Exception as e:
            self._log(f"Error al obtener estado de updates: {str(e)}", "error")
            return {
                "success": False,
                "paused": False,
                "paused_until": None,
                "auto_updates_enabled": True,
                "metered_connection": False,
                "pending_updates": 0,
            }

    def pause_updates(self, days=35):
        """
        Pause Windows Updates for specified days.

        Args:
            days: Number of days to pause (max 35)

        Returns:
            dict: {"success": bool, "message": str, "paused_until": str}
        """
        if not self._is_admin():
            return {
                "success": False,
                "message": "Se requieren privilegios de Administrador",
                "paused_until": None,
            }

        # Limit to 35 days (Windows limit)
        days = min(days, 35)

        self._log(f"Pausando actualizaciones por {days} días...", "info")

        try:
            # Use PowerShell to pause updates
            pause_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
            pause_value = f"{pause_date}T00:00:00Z"

            cmd = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "Set-ItemProperty",
                "-Path",
                "HKLM:\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings",
                "-Name",
                "PauseUpdatesExpiryTime",
                "-Value",
                pause_value,
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
                self._log(f"✓ Actualizaciones pausadas hasta {pause_date}", "success")
                return {
                    "success": True,
                    "message": f"✓ Actualizaciones pausadas por {days} días",
                    "paused_until": pause_date,
                }
            else:
                return {
                    "success": False,
                    "message": f"Error: {result.stderr}",
                    "paused_until": None,
                }

        except Exception as e:
            self._log(f"Error al pausar updates: {str(e)}", "error")
            return {"success": False, "message": f"Error: {str(e)}", "paused_until": None}

    def resume_updates(self):
        """
        Resume Windows Updates.

        Returns:
            dict: {"success": bool, "message": str}
        """
        if not self._is_admin():
            return {"success": False, "message": "Se requieren privilegios de Administrador"}

        self._log("Reanudando actualizaciones...", "info")

        try:
            from winsvalinn.utils.registry_helper import delete_registry

            # Remove pause setting
            success, msg = delete_registry(
                r"HKLM\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings", "PauseUpdatesExpiryTime"
            )

            if success:
                self._log("✓ Actualizaciones reanudadas", "success")
                return {"success": True, "message": "✓ Actualizaciones reanudadas"}
            else:
                return {"success": False, "message": "No se pudo reanudar actualizaciones"}

        except Exception as e:
            self._log(f"Error al reanudar updates: {str(e)}", "error")
            return {"success": False, "message": f"Error: {str(e)}"}

    def disable_auto_updates(self):
        """
        Disable automatic Windows Updates.

        WARNING: This prevents security updates!

        Returns:
            dict: {"success": bool, "message": str, "actions": []}
        """
        if not self._is_admin():
            return {
                "success": False,
                "message": "Se requieren privilegios de Administrador",
                "actions": [],
            }

        self._log("⚠️  Deshabilitando actualizaciones automáticas...", "warning")
        self._log("ADVERTENCIA: Esto previene actualizaciones de seguridad", "warning")

        actions = []

        try:
            from winsvalinn.utils.registry_helper import set_registry

            # Disable auto update via Group Policy
            set_registry(
                r"HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU",
                "NoAutoUpdate",
                "1",
                "REG_DWORD",
            )
            actions.append("Deshabilitadas actualizaciones automáticas (GPO)")

            # Disable Windows Update service
            try:
                result = subprocess.run(
                    ["sc", "config", "wuauserv", "start=", "disabled"],
                    capture_output=True,
                    timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW
                    if hasattr(subprocess, "CREATE_NO_WINDOW")
                    else 0,
                )

                if result.returncode == 0:
                    actions.append("Servicio Windows Update deshabilitado")
            except Exception:
                pass

            # Stop Windows Update service
            try:
                subprocess.run(
                    ["net", "stop", "wuauserv"],
                    capture_output=True,
                    timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW
                    if hasattr(subprocess, "CREATE_NO_WINDOW")
                    else 0,
                )
                actions.append("Servicio Windows Update detenido")
            except Exception:
                pass

            self._log(
                f"✓ Actualizaciones automáticas deshabilitadas - {len(actions)} cambios", "success"
            )

            return {
                "success": True,
                "message": "✓ Actualizaciones automáticas deshabilitadas",
                "actions": actions,
            }

        except Exception as e:
            self._log(f"Error al deshabilitar updates: {str(e)}", "error")
            return {"success": False, "message": f"Error: {str(e)}", "actions": actions}

    def enable_auto_updates(self):
        """
        Enable automatic Windows Updates.

        Returns:
            dict: {"success": bool, "message": str, "actions": []}
        """
        if not self._is_admin():
            return {
                "success": False,
                "message": "Se requieren privilegios de Administrador",
                "actions": [],
            }

        self._log("Habilitando actualizaciones automáticas...", "info")
        actions = []

        try:
            from winsvalinn.utils.registry_helper import delete_registry

            # Remove GPO setting
            success, msg = delete_registry(
                r"HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU", "NoAutoUpdate"
            )

            if success:
                actions.append("Habilitadas actualizaciones automáticas (GPO)")

            # Enable Windows Update service
            try:
                result = subprocess.run(
                    ["sc", "config", "wuauserv", "start=", "auto"],
                    capture_output=True,
                    timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW
                    if hasattr(subprocess, "CREATE_NO_WINDOW")
                    else 0,
                )

                if result.returncode == 0:
                    actions.append("Servicio Windows Update habilitado")
            except Exception:
                pass

            # Start Windows Update service
            try:
                subprocess.run(
                    ["net", "start", "wuauserv"],
                    capture_output=True,
                    timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW
                    if hasattr(subprocess, "CREATE_NO_WINDOW")
                    else 0,
                )
                actions.append("Servicio Windows Update iniciado")
            except Exception:
                pass

            self._log(
                f"✓ Actualizaciones automáticas habilitadas - {len(actions)} cambios", "success"
            )

            return {
                "success": True,
                "message": "✓ Actualizaciones automáticas habilitadas",
                "actions": actions,
            }

        except Exception as e:
            self._log(f"Error al habilitar updates: {str(e)}", "error")
            return {"success": False, "message": f"Error: {str(e)}", "actions": actions}

    def set_metered_connection(self, enable=True):
        """
        Set network as metered to prevent automatic updates.

        Note: This is a workaround - Windows won't download updates on metered connections.

        Args:
            enable: True to set as metered, False to remove

        Returns:
            dict: {"success": bool, "message": str}
        """
        if not self._is_admin():
            return {"success": False, "message": "Se requieren privilegios de Administrador"}

        try:
            from winsvalinn.utils.registry_helper import set_registry

            # This sets the active network as metered
            # Note: This is a simplified approach - proper implementation would need to identify
            # the specific network GUID

            if enable:
                self._log("Configurando conexión como limitada (metered)...", "info")

                # Set default cost to metered (2 = metered)
                set_registry(
                    r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\NetworkList\DefaultMediaCost",
                    "Default",
                    "2",
                    "REG_DWORD",
                )

                self._log("✓ Conexión configurada como limitada", "success")
                return {
                    "success": True,
                    "message": "✓ Conexión configurada como limitada (previene updates automáticos)",
                }
            else:
                # Reset to unrestricted (1)
                set_registry(
                    r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\NetworkList\DefaultMediaCost",
                    "Default",
                    "1",
                    "REG_DWORD",
                )

                self._log("✓ Conexión configurada como ilimitada", "success")
                return {"success": True, "message": "✓ Conexión configurada como ilimitada"}

        except Exception as e:
            self._log(f"Error al configurar conexión: {str(e)}", "error")
            return {"success": False, "message": f"Error: {str(e)}"}

    def check_for_updates(self):
        """
        Manually trigger Windows Update check.

        Returns:
            dict: {"success": bool, "message": str}
        """
        self._log("Buscando actualizaciones...", "info")

        try:
            # Use PowerShell to trigger update check
            cmd = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "(New-Object -ComObject Microsoft.Update.AutoUpdate).DetectNow()",
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

            # The command doesn't give much output, but if it runs without error it worked
            if result.returncode == 0 or not result.stderr:
                self._log("✓ Búsqueda de actualizaciones iniciada", "success")
                return {
                    "success": True,
                    "message": "✓ Búsqueda de actualizaciones iniciada. Revisa Windows Update.",
                }
            else:
                return {"success": False, "message": f"Error: {result.stderr}"}

        except Exception as e:
            self._log(f"Error al buscar updates: {str(e)}", "error")
            return {"success": False, "message": f"Error: {str(e)}"}

    def get_update_history(self):
        """
        Get Windows Update history.

        Returns:
            dict: {
                "success": bool,
                "updates": [{"title": str, "date": str, "status": str}],
                "count": int
            }
        """
        try:
            # Use PowerShell to get update history
            cmd = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "(New-Object -ComObject Microsoft.Update.Session).CreateUpdateSearcher().GetTotalHistoryCount()",
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
                count = int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0

                return {
                    "success": True,
                    "updates": [],  # Simplified - would need more complex PS to get details
                    "count": count,
                    "message": f"✓ {count} actualizaciones en historial",
                }
            else:
                return {
                    "success": False,
                    "updates": [],
                    "count": 0,
                    "message": "No se pudo obtener historial",
                }

        except Exception as e:
            self._log(f"Error al obtener historial: {str(e)}", "error")
            return {"success": False, "updates": [], "count": 0, "message": f"Error: {str(e)}"}

    def defer_feature_updates(self, days=365):
        """
        Defer feature updates (major Windows versions).

        Args:
            days: Number of days to defer (0-365)

        Returns:
            dict: {"success": bool, "message": str}
        """
        if not self._is_admin():
            return {"success": False, "message": "Se requieren privilegios de Administrador"}

        days = min(max(days, 0), 365)

        try:
            from winsvalinn.utils.registry_helper import set_registry

            # Defer feature updates
            set_registry(
                r"HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate",
                "DeferFeatureUpdates",
                "1",
                "REG_DWORD",
            )

            set_registry(
                r"HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate",
                "DeferFeatureUpdatesPeriodInDays",
                str(days),
                "REG_DWORD",
            )

            self._log(f"✓ Feature updates diferidas por {days} días", "success")

            return {"success": True, "message": f"✓ Feature updates diferidas por {days} días"}

        except Exception as e:
            self._log(f"Error al diferir updates: {str(e)}", "error")
            return {"success": False, "message": f"Error: {str(e)}"}

    def defer_quality_updates(self, days=30):
        """
        Defer quality updates (security/bug fixes).

        Args:
            days: Number of days to defer (0-30)

        Returns:
            dict: {"success": bool, "message": str}
        """
        if not self._is_admin():
            return {"success": False, "message": "Se requieren privilegios de Administrador"}

        days = min(max(days, 0), 30)

        try:
            from winsvalinn.utils.registry_helper import set_registry

            # Defer quality updates
            set_registry(
                r"HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate",
                "DeferQualityUpdates",
                "1",
                "REG_DWORD",
            )

            set_registry(
                r"HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate",
                "DeferQualityUpdatesPeriodInDays",
                str(days),
                "REG_DWORD",
            )

            self._log(f"✓ Quality updates diferidas por {days} días", "success")

            return {"success": True, "message": f"✓ Quality updates diferidas por {days} días"}

        except Exception as e:
            self._log(f"Error al diferir updates: {str(e)}", "error")
            return {"success": False, "message": f"Error: {str(e)}"}
