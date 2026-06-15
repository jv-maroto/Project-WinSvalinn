"""
Hosts File Manager - Manage Windows hosts file for ad/tracking blocking

This module allows users to:
1. Backup and restore hosts file
2. Add custom entries to block domains
3. Import popular blocklists (ads, tracking, telemetry)
4. Enable/disable entries without deleting
5. Flush DNS cache after changes

The hosts file is at: C:\\Windows\\System32\\drivers\\etc\\hosts

Author: WinGuardOptimizer Team
"""

import logging
import os
import shutil
import subprocess
from datetime import datetime


class HostsManager:
    """Manage Windows hosts file for blocking ads and tracking."""

    # Path to hosts file
    HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts"
    BACKUP_DIR = os.path.join(os.path.expanduser("~"), ".winguardoptimizer", "hosts_backups")

    def __init__(self, callback=None):
        """
        Initialize HostsManager.

        Args:
            callback: Optional callback function for logging (func(message, level))
        """
        self.callback = callback
        self.logger = logging.getLogger(__name__)

        # Popular blocklists
        self.TELEMETRY_DOMAINS = [
            # Microsoft Telemetry
            "vortex.data.microsoft.com",
            "vortex-win.data.microsoft.com",
            "telecommand.telemetry.microsoft.com",
            "telecommand.telemetry.microsoft.com.nsatc.net",
            "oca.telemetry.microsoft.com",
            "oca.telemetry.microsoft.com.nsatc.net",
            "sqm.telemetry.microsoft.com",
            "sqm.telemetry.microsoft.com.nsatc.net",
            "watson.telemetry.microsoft.com",
            "watson.telemetry.microsoft.com.nsatc.net",
            "redir.metaservices.microsoft.com",
            "choice.microsoft.com",
            "choice.microsoft.com.nsatc.net",
            "df.telemetry.microsoft.com",
            "reports.wes.df.telemetry.microsoft.com",
            "wes.df.telemetry.microsoft.com",
            "services.wes.df.telemetry.microsoft.com",
            "sqm.df.telemetry.microsoft.com",
            "telemetry.microsoft.com",
            "watson.ppe.telemetry.microsoft.com",
            "telemetry.appex.bing.net",
            "telemetry.urs.microsoft.com",
            "telemetry.appex.bing.net:443",
            "settings-sandbox.data.microsoft.com",
            "vortex-sandbox.data.microsoft.com",
            "survey.watson.microsoft.com",
            "watson.live.com",
            "watson.microsoft.com",
            "statsfe2.ws.microsoft.com",
            "corpext.msitadfs.glbdns2.microsoft.com",
            "compatexchange.cloudapp.net",
            "cs1.wpc.v0cdn.net",
            "a-0001.a-msedge.net",
            "statsfe2.update.microsoft.com.akadns.net",
            "sls.update.microsoft.com.akadns.net",
            "fe2.update.microsoft.com.akadns.net",
            "diagnostics.support.microsoft.com",
            "corp.sts.microsoft.com",
            "statsfe1.ws.microsoft.com",
            "pre.footprintpredict.com",
            "i1.services.social.microsoft.com",
            "i1.services.social.microsoft.com.nsatc.net",
            "feedback.windows.com",
            "feedback.microsoft-hohm.com",
            "feedback.search.microsoft.com",
        ]

        self.AD_DOMAINS = [
            # Common ad servers
            "ads.microsoft.com",
            "adnxs.com",
            "adnexus.net",
            "doubleclick.net",
            "googleadservices.com",
            "googlesyndication.com",
            "google-analytics.com",
            "googletagmanager.com",
            "googletagservices.com",
            "scorecardresearch.com",
            "facebook.com",
            "fbcdn.net",
            "akamaihd.net",
        ]

        self.TRACKING_DOMAINS = [
            # Tracking/Analytics
            "www.google-analytics.com",
            "ssl.google-analytics.com",
            "analytics.google.com",
            "metrics.icloud.com",
            "metrics.apple.com",
            "metrics.mzstatic.com",
        ]

        # Ensure backup directory exists
        os.makedirs(self.BACKUP_DIR, exist_ok=True)

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

    def backup_hosts(self):
        """
        Create backup of current hosts file.

        Returns:
            dict: {"success": bool, "backup_path": str, "message": str}
        """
        try:
            if not os.path.exists(self.HOSTS_PATH):
                return {
                    "success": False,
                    "backup_path": None,
                    "message": "Archivo hosts no encontrado",
                }

            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"hosts_backup_{timestamp}.txt"
            backup_path = os.path.join(self.BACKUP_DIR, backup_filename)

            # Copy hosts file
            shutil.copy2(self.HOSTS_PATH, backup_path)

            self._log(f"✓ Backup creado: {backup_filename}", "success")

            return {
                "success": True,
                "backup_path": backup_path,
                "message": f"✓ Backup guardado en: {backup_path}",
            }

        except PermissionError:
            return {
                "success": False,
                "backup_path": None,
                "message": "Error: Se requieren privilegios de Administrador",
            }
        except Exception as e:
            self._log(f"Error al crear backup: {str(e)}", "error")
            return {"success": False, "backup_path": None, "message": f"Error: {str(e)}"}

    def restore_hosts(self, backup_path):
        """
        Restore hosts file from backup.

        Args:
            backup_path: Path to backup file

        Returns:
            dict: {"success": bool, "message": str}
        """
        if not self._is_admin():
            return {"success": False, "message": "Se requieren privilegios de Administrador"}

        try:
            if not os.path.exists(backup_path):
                return {"success": False, "message": "Archivo de backup no encontrado"}

            # Restore backup
            shutil.copy2(backup_path, self.HOSTS_PATH)

            # Flush DNS
            self.flush_dns()

            self._log("✓ Hosts restaurado desde backup", "success")

            return {"success": True, "message": "✓ Archivo hosts restaurado correctamente"}

        except PermissionError:
            return {"success": False, "message": "Error: Se requieren privilegios de Administrador"}
        except Exception as e:
            self._log(f"Error al restaurar hosts: {str(e)}", "error")
            return {"success": False, "message": f"Error: {str(e)}"}

    def read_hosts(self):
        """
        Read current hosts file entries.

        Returns:
            dict: {
                "success": bool,
                "entries": [{"ip": str, "domain": str, "comment": str, "enabled": bool}],
                "total_entries": int,
                "blocked_count": int
            }
        """
        try:
            if not os.path.exists(self.HOSTS_PATH):
                return {"success": False, "entries": [], "total_entries": 0, "blocked_count": 0}

            entries = []
            blocked_count = 0

            with open(self.HOSTS_PATH, encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()

                    # Skip empty lines
                    if not line:
                        continue

                    # Handle comments
                    comment = ""
                    enabled = True

                    if line.startswith("#"):
                        # Disabled entry
                        if " " in line[1:].strip():
                            enabled = False
                            line = line[1:].strip()
                        else:
                            # Pure comment line
                            continue

                    # Extract inline comment
                    if "#" in line:
                        parts = line.split("#", 1)
                        line = parts[0].strip()
                        comment = parts[1].strip()

                    # Parse IP and domain
                    parts = line.split()
                    if len(parts) >= 2:
                        ip = parts[0]
                        domain = parts[1]

                        entries.append(
                            {"ip": ip, "domain": domain, "comment": comment, "enabled": enabled}
                        )

                        if enabled and ip == "0.0.0.0":
                            blocked_count += 1

            return {
                "success": True,
                "entries": entries,
                "total_entries": len(entries),
                "blocked_count": blocked_count,
            }

        except Exception as e:
            self._log(f"Error al leer hosts: {str(e)}", "error")
            return {"success": False, "entries": [], "total_entries": 0, "blocked_count": 0}

    def add_entry(self, domain, ip="0.0.0.0", comment=""):
        """
        Add entry to hosts file.

        Args:
            domain: Domain to block
            ip: IP to redirect to (default: 0.0.0.0 for blocking)
            comment: Optional comment

        Returns:
            dict: {"success": bool, "message": str}
        """
        if not self._is_admin():
            return {"success": False, "message": "Se requieren privilegios de Administrador"}

        try:
            # Check if already exists
            hosts_data = self.read_hosts()
            for entry in hosts_data["entries"]:
                if entry["domain"].lower() == domain.lower():
                    return {"success": False, "message": f"El dominio {domain} ya existe en hosts"}

            # Add entry
            with open(self.HOSTS_PATH, "a", encoding="utf-8", errors="replace") as f:
                line = f"{ip} {domain}"
                if comment:
                    line += f" # {comment}"
                f.write(f"\n{line}")

            self._log(f"✓ Agregado: {domain}", "success")

            # Flush DNS
            self.flush_dns()

            return {"success": True, "message": f"✓ {domain} agregado correctamente"}

        except PermissionError:
            return {"success": False, "message": "Error: Se requieren privilegios de Administrador"}
        except Exception as e:
            self._log(f"Error al agregar entrada: {str(e)}", "error")
            return {"success": False, "message": f"Error: {str(e)}"}

    def remove_entry(self, domain):
        """
        Remove entry from hosts file.

        Args:
            domain: Domain to remove

        Returns:
            dict: {"success": bool, "message": str}
        """
        if not self._is_admin():
            return {"success": False, "message": "Se requieren privilegios de Administrador"}

        try:
            # Read all lines
            with open(self.HOSTS_PATH, encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            # Filter out the domain
            new_lines = []
            removed = False

            for line in lines:
                # Check if this line contains the domain
                if domain.lower() in line.lower():
                    removed = True
                    continue
                new_lines.append(line)

            if not removed:
                return {"success": False, "message": f"Dominio {domain} no encontrado"}

            # Write back
            with open(self.HOSTS_PATH, "w", encoding="utf-8", errors="replace") as f:
                f.writelines(new_lines)

            self._log(f"✓ Eliminado: {domain}", "success")

            # Flush DNS
            self.flush_dns()

            return {"success": True, "message": f"✓ {domain} eliminado correctamente"}

        except PermissionError:
            return {"success": False, "message": "Error: Se requieren privilegios de Administrador"}
        except Exception as e:
            self._log(f"Error al eliminar entrada: {str(e)}", "error")
            return {"success": False, "message": f"Error: {str(e)}"}

    def block_telemetry_domains(self):
        """
        Block Microsoft telemetry domains.

        Returns:
            dict: {"success": bool, "added_count": int, "message": str}
        """
        if not self._is_admin():
            return {
                "success": False,
                "added_count": 0,
                "message": "Se requieren privilegios de Administrador",
            }

        self._log(f"Bloqueando {len(self.TELEMETRY_DOMAINS)} dominios de telemetría...", "info")

        # Backup first
        backup_result = self.backup_hosts()
        if not backup_result["success"]:
            self._log("Advertencia: No se pudo crear backup", "warning")

        added_count = 0
        hosts_data = self.read_hosts()
        existing_domains = [entry["domain"].lower() for entry in hosts_data["entries"]]

        try:
            with open(self.HOSTS_PATH, "a", encoding="utf-8", errors="replace") as f:
                f.write("\n# Microsoft Telemetry Blocking - Added by WinGuardOptimizer\n")

                for domain in self.TELEMETRY_DOMAINS:
                    if domain.lower() not in existing_domains:
                        f.write(f"0.0.0.0 {domain}\n")
                        added_count += 1

            self._log(f"✓ {added_count} dominios de telemetría bloqueados", "success")

            # Flush DNS
            self.flush_dns()

            return {
                "success": True,
                "added_count": added_count,
                "message": f"✓ {added_count} dominios bloqueados",
            }

        except Exception as e:
            self._log(f"Error al bloquear telemetría: {str(e)}", "error")
            return {"success": False, "added_count": 0, "message": f"Error: {str(e)}"}

    def block_ad_domains(self):
        """
        Block common advertising domains.

        Returns:
            dict: {"success": bool, "added_count": int, "message": str}
        """
        if not self._is_admin():
            return {
                "success": False,
                "added_count": 0,
                "message": "Se requieren privilegios de Administrador",
            }

        self._log(f"Bloqueando {len(self.AD_DOMAINS)} dominios de publicidad...", "info")

        # Backup first
        backup_result = self.backup_hosts()
        if not backup_result["success"]:
            self._log("Advertencia: No se pudo crear backup", "warning")

        added_count = 0
        hosts_data = self.read_hosts()
        existing_domains = [entry["domain"].lower() for entry in hosts_data["entries"]]

        try:
            with open(self.HOSTS_PATH, "a", encoding="utf-8", errors="replace") as f:
                f.write("\n# Ad Blocking - Added by WinGuardOptimizer\n")

                for domain in self.AD_DOMAINS:
                    if domain.lower() not in existing_domains:
                        f.write(f"0.0.0.0 {domain}\n")
                        added_count += 1

            self._log(f"✓ {added_count} dominios de publicidad bloqueados", "success")

            # Flush DNS
            self.flush_dns()

            return {
                "success": True,
                "added_count": added_count,
                "message": f"✓ {added_count} dominios bloqueados",
            }

        except Exception as e:
            self._log(f"Error al bloquear ads: {str(e)}", "error")
            return {"success": False, "added_count": 0, "message": f"Error: {str(e)}"}

    def block_tracking_domains(self):
        """
        Block tracking/analytics domains.

        Returns:
            dict: {"success": bool, "added_count": int, "message": str}
        """
        if not self._is_admin():
            return {
                "success": False,
                "added_count": 0,
                "message": "Se requieren privilegios de Administrador",
            }

        self._log(f"Bloqueando {len(self.TRACKING_DOMAINS)} dominios de tracking...", "info")

        # Backup first
        backup_result = self.backup_hosts()
        if not backup_result["success"]:
            self._log("Advertencia: No se pudo crear backup", "warning")

        added_count = 0
        hosts_data = self.read_hosts()
        existing_domains = [entry["domain"].lower() for entry in hosts_data["entries"]]

        try:
            with open(self.HOSTS_PATH, "a", encoding="utf-8", errors="replace") as f:
                f.write("\n# Tracking/Analytics Blocking - Added by WinGuardOptimizer\n")

                for domain in self.TRACKING_DOMAINS:
                    if domain.lower() not in existing_domains:
                        f.write(f"0.0.0.0 {domain}\n")
                        added_count += 1

            self._log(f"✓ {added_count} dominios de tracking bloqueados", "success")

            # Flush DNS
            self.flush_dns()

            return {
                "success": True,
                "added_count": added_count,
                "message": f"✓ {added_count} dominios bloqueados",
            }

        except Exception as e:
            self._log(f"Error al bloquear tracking: {str(e)}", "error")
            return {"success": False, "added_count": 0, "message": f"Error: {str(e)}"}

    def block_all(self):
        """
        Block telemetry, ads, and tracking all at once.

        Returns:
            dict: {"success": bool, "total_added": int, "message": str}
        """
        self._log("Bloqueando TODOS los dominios (telemetría + ads + tracking)...", "info")

        telemetry = self.block_telemetry_domains()
        ads = self.block_ad_domains()
        tracking = self.block_tracking_domains()

        total_added = (
            telemetry.get("added_count", 0)
            + ads.get("added_count", 0)
            + tracking.get("added_count", 0)
        )

        self._log(f"✓ Total: {total_added} dominios bloqueados", "success")

        return {
            "success": True,
            "total_added": total_added,
            "telemetry_count": telemetry.get("added_count", 0),
            "ad_count": ads.get("added_count", 0),
            "tracking_count": tracking.get("added_count", 0),
            "message": f"✓ {total_added} dominios bloqueados en total",
        }

    def flush_dns(self):
        """
        Flush DNS cache after hosts file changes.

        Returns:
            dict: {"success": bool, "message": str}
        """
        try:
            result = subprocess.run(
                ["ipconfig", "/flushdns"],
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
                self._log("✓ Caché DNS limpiada", "success")
                return {"success": True, "message": "✓ DNS cache flushed"}
            else:
                return {"success": False, "message": "Error al limpiar DNS cache"}

        except Exception as e:
            self._log(f"Error al limpiar DNS: {str(e)}", "warning")
            return {"success": False, "message": f"Error: {str(e)}"}

    # ─── StevenBlack hosts integration ───────────────────────────────────
    #
    # Imports curated blocklists from github.com/StevenBlack/hosts.
    # Lines added by this importer are wrapped between two markers so they
    # can be removed cleanly without touching user entries.

    SB_MARKER_START = "# === WinSvalinn StevenBlack import START ==="
    SB_MARKER_END = "# === WinSvalinn StevenBlack import END ==="

    SB_BASE_URL = "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts"
    SB_ALT_URL = (
        "https://raw.githubusercontent.com/StevenBlack/hosts/master/alternates/{combo}/hosts"
    )

    SB_VALID_CATEGORIES = {"fakenews", "gambling", "porn", "social"}

    def _sb_url(self, categories):
        """Build StevenBlack URL given a list of extra categories."""
        cats = sorted(c for c in categories if c in self.SB_VALID_CATEGORIES)
        if not cats:
            return self.SB_BASE_URL
        return self.SB_ALT_URL.format(combo="-".join(cats))

    def import_steven_black(self, categories=None):
        """
        Download and merge a StevenBlack blocklist into the hosts file.

        Args:
            categories: list of extra categories to include
                        (subset of {"fakenews", "gambling", "porn", "social"}).
                        Empty/None imports just the unified base list.

        Returns:
            dict with success, count, message.
        """
        if not self._is_admin():
            return {"success": False, "message": "Se requieren privilegios de Administrador"}

        try:
            from urllib.request import Request, urlopen
        except ImportError:
            return {"success": False, "message": "urllib no disponible"}

        categories = categories or []
        url = self._sb_url(categories)
        self._log(f"Descargando lista StevenBlack ({url})…", "info")

        try:
            req = Request(url, headers={"User-Agent": "WinSvalinn/1.0"})
            with urlopen(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")
        except Exception as exc:
            self._log(f"Error descargando StevenBlack: {exc}", "error")
            return {"success": False, "message": f"Error de red: {exc}"}

        added_lines = []
        for line in raw.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            parts = stripped.split()
            if len(parts) >= 2 and parts[0] in ("0.0.0.0", "127.0.0.1"):
                domain = parts[1]
                if domain in ("0.0.0.0", "localhost"):
                    continue
                added_lines.append(f"0.0.0.0 {domain}")

        if not added_lines:
            return {"success": False, "message": "Lista descargada vacía"}

        # Backup before modifying
        self.backup_hosts()

        try:
            with open(self.HOSTS_PATH, encoding="utf-8", errors="ignore") as f:
                current = f.read()
        except Exception as exc:
            return {"success": False, "message": f"No se pudo leer hosts: {exc}"}

        # Strip any previous StevenBlack block
        if self.SB_MARKER_START in current and self.SB_MARKER_END in current:
            before = current.split(self.SB_MARKER_START, 1)[0].rstrip()
            after = current.split(self.SB_MARKER_END, 1)[1].lstrip("\n")
            current = before + ("\n" + after if after else "\n")

        block = "\n".join(
            [
                self.SB_MARKER_START,
                f"# Categories: {','.join(categories) if categories else 'unified'}",
                f"# Imported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"# Source: {url}",
                *added_lines,
                self.SB_MARKER_END,
                "",
            ]
        )

        try:
            with open(self.HOSTS_PATH, "a", encoding="utf-8") as f:
                if not current.endswith("\n"):
                    f.write("\n")
                f.write(block)
        except PermissionError:
            return {"success": False, "message": "Permiso denegado al escribir hosts"}
        except Exception as exc:
            return {"success": False, "message": f"Error al escribir hosts: {exc}"}

        self.flush_dns()
        self._log(f"✓ StevenBlack importado: {len(added_lines)} dominios", "success")
        return {
            "success": True,
            "count": len(added_lines),
            "message": f"✓ {len(added_lines):,} dominios bloqueados (StevenBlack)",
        }

    def remove_steven_black(self):
        """Remove only the StevenBlack-managed block from hosts."""
        if not self._is_admin():
            return {"success": False, "message": "Se requieren privilegios de Administrador"}

        try:
            with open(self.HOSTS_PATH, encoding="utf-8", errors="ignore") as f:
                current = f.read()
        except Exception as exc:
            return {"success": False, "message": f"No se pudo leer hosts: {exc}"}

        if self.SB_MARKER_START not in current:
            return {"success": True, "removed": 0, "message": "No había bloque StevenBlack"}

        self.backup_hosts()

        before = current.split(self.SB_MARKER_START, 1)[0].rstrip()
        after_part = current.split(self.SB_MARKER_END, 1)
        after = after_part[1].lstrip("\n") if len(after_part) > 1 else ""

        new_content = before + ("\n" + after if after else "\n")

        try:
            with open(self.HOSTS_PATH, "w", encoding="utf-8") as f:
                f.write(new_content)
        except PermissionError:
            return {"success": False, "message": "Permiso denegado al escribir hosts"}

        self.flush_dns()
        self._log("✓ Bloque StevenBlack eliminado de hosts", "success")
        return {"success": True, "message": "✓ Bloque StevenBlack eliminado"}

    def list_backups(self):
        """
        List all available backups.

        Returns:
            list: [{"filename": str, "path": str, "date": str, "size": int}]
        """
        backups = []

        try:
            if not os.path.exists(self.BACKUP_DIR):
                return backups

            for filename in os.listdir(self.BACKUP_DIR):
                if filename.startswith("hosts_backup_"):
                    filepath = os.path.join(self.BACKUP_DIR, filename)
                    stat = os.stat(filepath)

                    backups.append(
                        {
                            "filename": filename,
                            "path": filepath,
                            "date": datetime.fromtimestamp(stat.st_mtime).strftime(
                                "%Y-%m-%d %H:%M:%S"
                            ),
                            "size": stat.st_size,
                        }
                    )

            # Sort by date (newest first)
            backups.sort(key=lambda x: x["date"], reverse=True)

        except Exception as e:
            self._log(f"Error al listar backups: {str(e)}", "error")

        return backups
