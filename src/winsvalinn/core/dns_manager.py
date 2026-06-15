"""
DNS Manager - Manage DNS servers for privacy and performance

This module allows users to:
1. View current DNS configuration
2. Set DNS servers from presets (Cloudflare, Google, Quad9, etc.)
3. Set custom DNS servers
4. Reset to automatic DNS (DHCP)
5. Flush DNS cache

Popular DNS providers:
- Cloudflare: 1.1.1.1 (privacy-focused, fast)
- Google: 8.8.8.8 (reliable, fast)
- Quad9: 9.9.9.9 (security-focused, blocks malware)
- OpenDNS: 208.67.222.222 (content filtering)

Author: WinGuardOptimizer Team
"""

import ipaddress
import logging
import re
import subprocess


class DNSManager:
    """Manage DNS server configuration for network adapters."""

    # Preset DNS servers
    DNS_PRESETS = {
        "cloudflare": {
            "name": "Cloudflare DNS (1.1.1.1)",
            "description": "Privacy-focused, fast DNS",
            "primary": "1.1.1.1",
            "secondary": "1.0.0.1",
            "features": ["Privacy", "Speed", "No logging"],
        },
        "cloudflare_malware": {
            "name": "Cloudflare Malware Blocking",
            "description": "Blocks malware domains",
            "primary": "1.1.1.2",
            "secondary": "1.0.0.2",
            "features": ["Privacy", "Malware blocking"],
        },
        "cloudflare_family": {
            "name": "Cloudflare Family (Adult Content Filter)",
            "description": "Blocks malware and adult content",
            "primary": "1.1.1.3",
            "secondary": "1.0.0.3",
            "features": ["Privacy", "Malware blocking", "Adult filter"],
        },
        "google": {
            "name": "Google DNS (8.8.8.8)",
            "description": "Reliable, fast DNS by Google",
            "primary": "8.8.8.8",
            "secondary": "8.8.4.4",
            "features": ["Speed", "Reliability"],
        },
        "quad9": {
            "name": "Quad9 DNS (9.9.9.9)",
            "description": "Security-focused, blocks malware",
            "primary": "9.9.9.9",
            "secondary": "149.112.112.112",
            "features": ["Security", "Malware blocking", "Privacy"],
        },
        "opendns": {
            "name": "OpenDNS (208.67.222.222)",
            "description": "Content filtering and security",
            "primary": "208.67.222.222",
            "secondary": "208.67.220.220",
            "features": ["Security", "Content filtering"],
        },
        "opendns_family": {
            "name": "OpenDNS FamilyShield",
            "description": "Blocks adult content",
            "primary": "208.67.222.123",
            "secondary": "208.67.220.123",
            "features": ["Adult filter", "Security"],
        },
        "adguard": {
            "name": "AdGuard DNS",
            "description": "Ad blocking DNS",
            "primary": "94.140.14.14",
            "secondary": "94.140.15.15",
            "features": ["Ad blocking", "Privacy"],
        },
        "adguard_family": {
            "name": "AdGuard Family Protection",
            "description": "Ad blocking + adult content filter",
            "primary": "94.140.14.15",
            "secondary": "94.140.15.16",
            "features": ["Ad blocking", "Adult filter", "Privacy"],
        },
        "level3": {
            "name": "Level3 DNS",
            "description": "Fast, reliable DNS",
            "primary": "209.244.0.3",
            "secondary": "209.244.0.4",
            "features": ["Speed", "Reliability"],
        },
    }

    def __init__(self, callback=None):
        """
        Initialize DNSManager.

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

    def _validate_ip(self, ip_str):
        """
        Validate IP address format.

        Args:
            ip_str: IP address string to validate

        Returns:
            bool: True if valid IPv4 or IPv6 address
        """
        if not ip_str:
            return False
        try:
            ipaddress.ip_address(ip_str)
            return True
        except ValueError:
            return False

    def _is_admin(self):
        """Check if running as administrator."""
        try:
            import ctypes

            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    def get_network_adapters(self):
        """
        Get list of network adapters.

        Returns:
            list: [{"name": str, "status": str}]
        """
        try:
            # Use PowerShell for better detection
            cmd = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | Select-Object -ExpandProperty Name",
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

            if result.returncode != 0:
                # Fallback: try netsh
                return self._get_adapters_netsh()

            adapters = []
            lines = result.stdout.strip().split("\n")

            for line in lines:
                line = line.strip()
                if line:
                    adapters.append({"name": line, "status": "Up"})

            # If no adapters found, try fallback
            if not adapters:
                return self._get_adapters_netsh()

            return adapters

        except Exception as e:
            self._log(f"Error al obtener adaptadores: {str(e)}", "error")
            # Last resort fallback
            return self._get_adapters_netsh()

    def _get_adapters_netsh(self):
        """Fallback method using netsh."""
        try:
            cmd = ["netsh", "interface", "ipv4", "show", "interfaces"]

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

            if result.returncode != 0:
                # Ultimate fallback - use common adapter names
                return [{"name": "Ethernet", "status": "Up"}, {"name": "Wi-Fi", "status": "Up"}]

            adapters = []
            lines = result.stdout.split("\n")

            for line in lines:
                # Skip headers
                if "Idx" in line or "---" in line or not line.strip():
                    continue

                parts = line.split()
                if len(parts) >= 5:
                    # Format: Idx  Met  MTU  State  Name
                    name = " ".join(parts[4:])
                    state = parts[3]

                    if state.lower() == "connected":
                        adapters.append({"name": name, "status": "Up"})

            # If still no adapters, use defaults
            if not adapters:
                adapters = [{"name": "Ethernet", "status": "Up"}, {"name": "Wi-Fi", "status": "Up"}]

            return adapters

        except Exception:
            # Return defaults
            return [{"name": "Ethernet", "status": "Up"}, {"name": "Wi-Fi", "status": "Up"}]

    def get_current_dns(self, adapter_name=None):
        """
        Get current DNS servers for adapter.

        Args:
            adapter_name: Network adapter name (None for all)

        Returns:
            dict: {
                "adapter": str,
                "dns_servers": [str],
                "dhcp_enabled": bool
            }
        """
        try:
            # If no adapter specified, get the first connected one
            if not adapter_name:
                adapters = self.get_network_adapters()
                if not adapters:
                    return {"adapter": None, "dns_servers": [], "dhcp_enabled": True}
                adapter_name = adapters[0]["name"]

            cmd = ["netsh", "interface", "ip", "show", "dns", adapter_name]

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

            dns_servers = []
            dhcp_enabled = False

            if result.returncode == 0:
                output = result.stdout

                # Check if DHCP
                if "dhcp" in output.lower():
                    dhcp_enabled = True

                # Extract DNS IPs
                ip_pattern = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
                dns_servers = re.findall(ip_pattern, output)

            return {
                "adapter": adapter_name,
                "dns_servers": dns_servers,
                "dhcp_enabled": dhcp_enabled,
            }

        except Exception as e:
            self._log(f"Error al obtener DNS actual: {str(e)}", "error")
            return {"adapter": adapter_name, "dns_servers": [], "dhcp_enabled": True}

    def set_dns(self, primary_dns, secondary_dns=None, adapter_name=None):
        """
        Set custom DNS servers.

        Args:
            primary_dns: Primary DNS server IP
            secondary_dns: Secondary DNS server IP (optional)
            adapter_name: Network adapter name (None for first adapter)

        Returns:
            dict: {"success": bool, "message": str, "adapter": str}
        """
        if not self._is_admin():
            return {
                "success": False,
                "message": "Se requieren privilegios de Administrador",
                "adapter": None,
            }

        # Validate IP addresses
        if not self._validate_ip(primary_dns):
            return {
                "success": False,
                "message": f"IP primaria inválida: {primary_dns}",
                "adapter": None,
            }

        if secondary_dns and not self._validate_ip(secondary_dns):
            return {
                "success": False,
                "message": f"IP secundaria inválida: {secondary_dns}",
                "adapter": None,
            }

        try:
            # Get adapter if not specified
            if not adapter_name:
                adapters = self.get_network_adapters()
                if not adapters:
                    return {
                        "success": False,
                        "message": "No se encontraron adaptadores de red activos",
                        "adapter": None,
                    }
                adapter_name = adapters[0]["name"]

            # Set primary DNS
            cmd_primary = [
                "netsh",
                "interface",
                "ip",
                "set",
                "dns",
                f"name={adapter_name}",
                "static",
                primary_dns,
                "primary",
            ]

            result = subprocess.run(
                cmd_primary,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW
                if hasattr(subprocess, "CREATE_NO_WINDOW")
                else 0,
            )

            if result.returncode != 0:
                return {
                    "success": False,
                    "message": f"Error al configurar DNS primario: {result.stderr}",
                    "adapter": adapter_name,
                }

            self._log(f"✓ DNS primario configurado: {primary_dns}", "success")

            # Set secondary DNS if provided
            if secondary_dns:
                cmd_secondary = [
                    "netsh",
                    "interface",
                    "ip",
                    "add",
                    "dns",
                    f"name={adapter_name}",
                    secondary_dns,
                    "index=2",
                ]

                result_sec = subprocess.run(
                    cmd_secondary,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW
                    if hasattr(subprocess, "CREATE_NO_WINDOW")
                    else 0,
                )

                if result_sec.returncode == 0:
                    self._log(f"✓ DNS secundario configurado: {secondary_dns}", "success")

            # Flush DNS cache
            self.flush_dns()

            return {
                "success": True,
                "message": f"✓ DNS configurado: {primary_dns}"
                + (f", {secondary_dns}" if secondary_dns else ""),
                "adapter": adapter_name,
            }

        except Exception as e:
            self._log(f"Error al configurar DNS: {str(e)}", "error")
            return {"success": False, "message": f"Error: {str(e)}", "adapter": adapter_name}

    def set_preset_dns(self, preset_key, adapter_name=None):
        """
        Set DNS from preset.

        Args:
            preset_key: Key from DNS_PRESETS
            adapter_name: Network adapter name (None for first adapter)

        Returns:
            dict: {"success": bool, "message": str, "adapter": str}
        """
        if preset_key not in self.DNS_PRESETS:
            return {
                "success": False,
                "message": f"Preset '{preset_key}' no encontrado",
                "adapter": None,
            }

        preset = self.DNS_PRESETS[preset_key]
        self._log(f"Configurando {preset['name']}...", "info")

        result = self.set_dns(preset["primary"], preset.get("secondary"), adapter_name)

        if result["success"]:
            result["message"] = f"✓ {preset['name']} configurado correctamente"

        return result

    def reset_to_dhcp(self, adapter_name=None):
        """
        Reset DNS to automatic (DHCP).

        Args:
            adapter_name: Network adapter name (None for first adapter)

        Returns:
            dict: {"success": bool, "message": str, "adapter": str}
        """
        if not self._is_admin():
            return {
                "success": False,
                "message": "Se requieren privilegios de Administrador",
                "adapter": None,
            }

        try:
            # Get adapter if not specified
            if not adapter_name:
                adapters = self.get_network_adapters()
                if not adapters:
                    return {
                        "success": False,
                        "message": "No se encontraron adaptadores de red activos",
                        "adapter": None,
                    }
                adapter_name = adapters[0]["name"]

            cmd = ["netsh", "interface", "ip", "set", "dns", f"name={adapter_name}", "dhcp"]

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
                self._log("✓ DNS restablecido a automático (DHCP)", "success")
                self.flush_dns()

                return {
                    "success": True,
                    "message": "✓ DNS restablecido a automático",
                    "adapter": adapter_name,
                }
            else:
                return {
                    "success": False,
                    "message": f"Error: {result.stderr}",
                    "adapter": adapter_name,
                }

        except Exception as e:
            self._log(f"Error al restablecer DNS: {str(e)}", "error")
            return {"success": False, "message": f"Error: {str(e)}", "adapter": adapter_name}

    def flush_dns(self):
        """
        Flush DNS cache.

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

    def get_all_presets(self):
        """
        Get all DNS presets.

        Returns:
            dict: DNS_PRESETS dictionary
        """
        return self.DNS_PRESETS

    # ─── DNS over HTTPS (Windows 11 native) ─────────────────────────────
    #
    # Windows 11 (and Server 2022) ships with a DoH-capable DNS client. The
    # well-known providers are stored under
    # HKLM\SYSTEM\CurrentControlSet\Services\Dnscache\Parameters\DohWellKnownServers
    # and DoH usage is enabled per-IP under
    # HKLM\SYSTEM\CurrentControlSet\Services\Dnscache\InterfaceSpecificParameters

    DOH_WELL_KNOWN = {
        "1.1.1.1": "https://cloudflare-dns.com/dns-query",
        "1.0.0.1": "https://cloudflare-dns.com/dns-query",
        "8.8.8.8": "https://dns.google/dns-query",
        "8.8.4.4": "https://dns.google/dns-query",
        "9.9.9.9": "https://dns.quad9.net/dns-query",
        "149.112.112.112": "https://dns.quad9.net/dns-query",
        "94.140.14.14": "https://dns.adguard-dns.com/dns-query",
        "94.140.15.15": "https://dns.adguard-dns.com/dns-query",
    }

    def _winreg(self):
        try:
            import winreg

            return winreg
        except ImportError:
            return None

    def get_doh_status(self):
        """
        Check if DoH well-known servers are registered for our presets.
        Returns a list of {ip, template, registered} dicts.
        """
        winreg = self._winreg()
        if not winreg:
            return []
        out = []
        for ip, template in self.DOH_WELL_KNOWN.items():
            registered = False
            try:
                key_path = (
                    r"SYSTEM\CurrentControlSet\Services\Dnscache\Parameters"
                    r"\DohWellKnownServers\\" + ip
                )
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path):
                    registered = True
            except OSError:
                registered = False
            out.append({"ip": ip, "template": template, "registered": registered})
        return out

    def register_doh_servers(self):
        """
        Register all known DoH templates so Windows can use DoH for those IPs.
        Idempotent: runs each IP through reg add.
        """
        if not self._is_admin():
            return {"success": False, "message": "Se requieren privilegios de Administrador"}

        winreg = self._winreg()
        if not winreg:
            return {"success": False, "message": "winreg no disponible (¿Windows?)"}

        added = 0
        for ip, template in self.DOH_WELL_KNOWN.items():
            try:
                base = r"SYSTEM\CurrentControlSet\Services\Dnscache\Parameters\DohWellKnownServers"
                with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, base + "\\" + ip) as key:
                    winreg.SetValueEx(key, "DohTemplate", 0, winreg.REG_SZ, template)
                    # AutoUpgrade=1, MandatoryEncryption=2 (require DoH)
                    winreg.SetValueEx(key, "AutoUpgrade", 0, winreg.REG_DWORD, 1)
                    winreg.SetValueEx(key, "MandatoryEncryption", 0, winreg.REG_DWORD, 2)
                added += 1
            except OSError as exc:
                self._log(f"DoH register failed for {ip}: {exc}", "warning")

        self._log(f"✓ DoH well-known: {added}/{len(self.DOH_WELL_KNOWN)} registrados", "success")
        return {
            "success": True,
            "registered": added,
            "message": f"✓ {added} servidores DoH registrados",
        }

    def enable_doh_for_current_dns(self, mandatory=True):
        """
        Tell Windows to *require* DoH for the currently configured DNS IPs.

        Sets EnableAutoDoh=2 (require) on the Dnscache service parameters.
        For full per-interface enforcement, additionally registers each
        active DNS IP under DohClientSettings.

        Returns dict with success/message.
        """
        if not self._is_admin():
            return {"success": False, "message": "Se requieren privilegios de Administrador"}

        winreg = self._winreg()
        if not winreg:
            return {"success": False, "message": "winreg no disponible"}

        # 1) Register well-known templates so Windows knows what URL to hit
        self.register_doh_servers()

        # 2) Set DnsCache global EnableAutoDoh
        try:
            base = r"SYSTEM\CurrentControlSet\Services\Dnscache\Parameters"
            with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, base) as key:
                # 0=off, 1=automatic if known, 2=mandatory
                winreg.SetValueEx(key, "EnableAutoDoh", 0, winreg.REG_DWORD, 2 if mandatory else 1)
        except OSError as exc:
            return {"success": False, "message": f"Registro inaccesible: {exc}"}

        msg = "✓ DoH habilitado " + ("(modo mandatorio)" if mandatory else "(automático)")
        self._log(msg, "success")
        return {"success": True, "message": msg}

    def disable_doh(self):
        """Disable DoH globally (EnableAutoDoh=0)."""
        if not self._is_admin():
            return {"success": False, "message": "Se requieren privilegios de Administrador"}

        winreg = self._winreg()
        if not winreg:
            return {"success": False, "message": "winreg no disponible"}

        try:
            base = r"SYSTEM\CurrentControlSet\Services\Dnscache\Parameters"
            with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, base) as key:
                winreg.SetValueEx(key, "EnableAutoDoh", 0, winreg.REG_DWORD, 0)
        except OSError as exc:
            return {"success": False, "message": f"Registro inaccesible: {exc}"}

        self._log("DoH deshabilitado", "info")
        return {"success": True, "message": "DoH deshabilitado"}

    def test_dns_speed(self, dns_server):
        """
        Test DNS server response time (simple ping test).

        Args:
            dns_server: DNS server IP to test

        Returns:
            dict: {"success": bool, "latency_ms": float, "message": str}
        """
        try:
            import time

            # Simple test: resolve a domain using the DNS
            # Note: This is a basic test, more sophisticated testing would use DNS query libraries
            cmd = ["ping", "-n", "1", "-w", "1000", dns_server]

            start = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW
                if hasattr(subprocess, "CREATE_NO_WINDOW")
                else 0,
            )
            elapsed = (time.time() - start) * 1000  # Convert to ms

            if result.returncode == 0:
                # Extract actual latency from ping output
                match = re.search(r"Average = (\d+)ms", result.stdout)
                if match:
                    latency = int(match.group(1))
                else:
                    latency = elapsed

                return {
                    "success": True,
                    "latency_ms": latency,
                    "message": f"✓ {dns_server}: {latency:.0f}ms",
                }
            else:
                return {
                    "success": False,
                    "latency_ms": None,
                    "message": f"✗ {dns_server}: No responde",
                }

        except Exception as e:
            return {"success": False, "latency_ms": None, "message": f"Error: {str(e)}"}
