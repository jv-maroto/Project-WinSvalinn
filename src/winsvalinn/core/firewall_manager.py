"""
Firewall Manager - Manage Windows Firewall

This module allows users to:
1. Check firewall status for all profiles
2. Enable/disable firewall
3. View active firewall rules
4. Create custom rules
5. Block/allow specific applications
6. Reset firewall to defaults

Author: WinGuardOptimizer Team
"""

import logging
import subprocess


class FirewallManager:
    """Manage Windows Firewall settings."""

    def __init__(self, callback=None):
        """
        Initialize FirewallManager.

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

    def get_firewall_status(self):
        """
        Get firewall status for all profiles.

        Returns:
            dict: {
                "domain": {"enabled": bool, "inbound": str, "outbound": str},
                "private": {"enabled": bool, "inbound": str, "outbound": str},
                "public": {"enabled": bool, "inbound": str, "outbound": str}
            }
        """
        try:
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

            status = {
                "domain": {"enabled": False, "inbound": "Unknown", "outbound": "Unknown"},
                "private": {"enabled": False, "inbound": "Unknown", "outbound": "Unknown"},
                "public": {"enabled": False, "inbound": "Unknown", "outbound": "Unknown"},
            }

            if result.returncode == 0:
                output = result.stdout
                lines = output.split("\n")

                current_profile = None
                for line in lines:
                    line = line.strip()

                    if "Domain Profile" in line:
                        current_profile = "domain"
                    elif "Private Profile" in line:
                        current_profile = "private"
                    elif "Public Profile" in line:
                        current_profile = "public"

                    if current_profile and "State" in line and "ON" in line.upper():
                        status[current_profile]["enabled"] = True
                    elif current_profile and "State" in line and "OFF" in line.upper():
                        status[current_profile]["enabled"] = False

            return status

        except Exception as e:
            self._log(f"Error al obtener estado del firewall: {str(e)}", "error")
            return {
                "domain": {"enabled": False, "inbound": "Unknown", "outbound": "Unknown"},
                "private": {"enabled": False, "inbound": "Unknown", "outbound": "Unknown"},
                "public": {"enabled": False, "inbound": "Unknown", "outbound": "Unknown"},
                "error": str(e),
            }

    def enable_firewall(self, profile="allprofiles"):
        """
        Enable Windows Firewall.

        Args:
            profile: Profile to enable (allprofiles, domainprofile, privateprofile, publicprofile)

        Returns:
            dict: {"success": bool, "message": str}
        """
        if not self._is_admin():
            return {"success": False, "message": "Se requieren privilegios de Administrador"}

        try:
            cmd = ["netsh", "advfirewall", "set", profile, "state", "on"]

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
                self._log(f"✓ Firewall habilitado ({profile})", "success")
                return {"success": True, "message": f"✓ Firewall habilitado ({profile})"}
            else:
                return {"success": False, "message": f"Error: {result.stderr}"}

        except Exception as e:
            self._log(f"Error al habilitar firewall: {str(e)}", "error")
            return {"success": False, "message": f"Error: {str(e)}"}

    def disable_firewall(self, profile="allprofiles"):
        """
        Disable Windows Firewall.

        WARNING: This is a security risk. Only for troubleshooting.

        Args:
            profile: Profile to disable (allprofiles, domainprofile, privateprofile, publicprofile)

        Returns:
            dict: {"success": bool, "message": str}
        """
        if not self._is_admin():
            return {"success": False, "message": "Se requieren privilegios de Administrador"}

        try:
            cmd = ["netsh", "advfirewall", "set", profile, "state", "off"]

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
                self._log(f"⚠️ Firewall deshabilitado ({profile})", "warning")
                return {"success": True, "message": f"⚠️ Firewall deshabilitado ({profile})"}
            else:
                return {"success": False, "message": f"Error: {result.stderr}"}

        except Exception as e:
            self._log(f"Error: {str(e)}", "error")
            return {"success": False, "message": f"Error: {str(e)}"}

    def get_firewall_rules(self, limit=50):
        """
        Get list of firewall rules.

        Args:
            limit: Maximum number of rules to return

        Returns:
            dict: {"success": bool, "rules": list, "count": int}
        """
        try:
            cmd = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                f"Get-NetFirewallRule | Where-Object {{$_.Enabled -eq 'True'}} | "
                f"Select-Object -First {limit} DisplayName, Direction, Action, Enabled | ConvertTo-Json",
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

                try:
                    rules_data = json.loads(result.stdout)

                    # Handle single rule vs array
                    if not isinstance(rules_data, list):
                        rules_data = [rules_data]

                    rules = []
                    for rule in rules_data:
                        rules.append(
                            {
                                "name": rule.get("DisplayName", "Unknown"),
                                "direction": rule.get("Direction", "Unknown"),
                                "action": rule.get("Action", "Unknown"),
                                "enabled": rule.get("Enabled", False),
                            }
                        )

                    return {"success": True, "rules": rules, "count": len(rules)}
                except Exception as e:
                    self._log(f"Error: {str(e)}", "error")
                    pass

            return {"success": True, "rules": [], "count": 0}

        except Exception as e:
            self._log(f"Error al obtener reglas: {str(e)}", "error")
            return {"success": False, "rules": [], "count": 0, "message": f"Error: {str(e)}"}

    def block_application(self, app_path, rule_name=None):
        """
        Create firewall rule to block an application.

        Args:
            app_path: Full path to application executable
            rule_name: Name for the rule (optional, defaults to app name)

        Returns:
            dict: {"success": bool, "message": str}
        """
        if not self._is_admin():
            return {"success": False, "message": "Se requieren privilegios de Administrador"}

        try:
            import os

            if not os.path.exists(app_path):
                return {"success": False, "message": f"Aplicación no encontrada: {app_path}"}

            if not rule_name:
                rule_name = f"Block {os.path.basename(app_path)}"

            cmd = [
                "netsh",
                "advfirewall",
                "firewall",
                "add",
                "rule",
                f"name={rule_name}",
                "dir=out",
                "action=block",
                f"program={app_path}",
                "enable=yes",
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
                self._log(f"✓ Aplicación bloqueada: {os.path.basename(app_path)}", "success")
                return {"success": True, "message": f"✓ Regla creada: {rule_name}"}
            else:
                return {"success": False, "message": f"Error: {result.stderr}"}

        except Exception as e:
            self._log(f"Error al bloquear aplicación: {str(e)}", "error")
            return {"success": False, "message": f"Error: {str(e)}"}

    def allow_application(self, app_path, rule_name=None):
        """
        Create firewall rule to allow an application.

        Args:
            app_path: Full path to application executable
            rule_name: Name for the rule (optional, defaults to app name)

        Returns:
            dict: {"success": bool, "message": str}
        """
        if not self._is_admin():
            return {"success": False, "message": "Se requieren privilegios de Administrador"}

        try:
            import os

            if not os.path.exists(app_path):
                return {"success": False, "message": f"Aplicación no encontrada: {app_path}"}

            if not rule_name:
                rule_name = f"Allow {os.path.basename(app_path)}"

            cmd = [
                "netsh",
                "advfirewall",
                "firewall",
                "add",
                "rule",
                f"name={rule_name}",
                "dir=in",
                "action=allow",
                f"program={app_path}",
                "enable=yes",
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
                self._log(f"✓ Aplicación permitida: {os.path.basename(app_path)}", "success")
                return {"success": True, "message": f"✓ Regla creada: {rule_name}"}
            else:
                return {"success": False, "message": f"Error: {result.stderr}"}

        except Exception as e:
            self._log(f"Error: {str(e)}", "error")
            return {"success": False, "message": f"Error: {str(e)}"}

    def reset_firewall(self):
        """
        Reset firewall to default settings.

        WARNING: This will remove all custom rules.

        Returns:
            dict: {"success": bool, "message": str}
        """
        if not self._is_admin():
            return {"success": False, "message": "Se requieren privilegios de Administrador"}

        try:
            cmd = ["netsh", "advfirewall", "reset"]

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
                self._log("✓ Firewall restablecido a valores predeterminados", "success")
                return {
                    "success": True,
                    "message": "✓ Firewall restablecido a valores predeterminados",
                }
            else:
                return {"success": False, "message": f"Error: {result.stderr}"}

        except Exception as e:
            self._log(f"Error: {str(e)}", "error")
            return {"success": False, "message": f"Error: {str(e)}"}

    def block_port(self, port, protocol="TCP", direction="in", rule_name=None):
        """
        Block a specific port.

        Args:
            port: Port number to block
            protocol: TCP or UDP
            direction: in or out
            rule_name: Optional rule name

        Returns:
            dict: {"success": bool, "message": str}
        """
        if not self._is_admin():
            return {"success": False, "message": "Se requieren privilegios de Administrador"}

        try:
            if not rule_name:
                rule_name = f"Block {protocol} Port {port}"

            cmd = [
                "netsh",
                "advfirewall",
                "firewall",
                "add",
                "rule",
                f"name={rule_name}",
                f"dir={direction}",
                "action=block",
                f"protocol={protocol}",
                f"localport={port}",
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
                self._log(f"✓ Puerto bloqueado: {protocol}/{port}", "success")
                return {"success": True, "message": f"✓ Puerto bloqueado: {protocol}/{port}"}
            else:
                return {"success": False, "message": f"Error: {result.stderr}"}

        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
