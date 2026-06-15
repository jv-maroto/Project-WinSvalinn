"""
VPN & Proxy Detector for WinSvalinn.

Detects VPN adapters, proxy settings, VPN software,
and checks for DNS leaks.
"""

import json
import platform
import re
import subprocess

from winsvalinn.utils.logger import ModuleLogger

logger = ModuleLogger("VPNDetector")

IS_WINDOWS = platform.system() == "Windows"
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

VPN_ADAPTER_KEYWORDS = [
    "tap",
    "tun",
    "wireguard",
    "vpn",
    "virtual",
    "pptp",
    "l2tp",
    "sstp",
    "openvpn",
    "nordlynx",
    "wintun",
    "cloudflare",
    "proton",
]

VPN_PROCESS_NAMES = [
    "openvpn",
    "nordvpn",
    "expressvpn",
    "surfshark",
    "protonvpn",
    "wireguard",
    "mullvad",
    "cyberghost",
    "pia",
    "windscribe",
    "hotspotshield",
    "tunnelbear",
    "cloudflare-warp",
    "warp-svc",
]


class VPNProxyDetector:
    """Detect VPN connections, proxy settings, and DNS leaks."""

    def __init__(self, callback=None):
        self._callback = callback or (lambda msg, level="info": None)

    def _log(self, msg, level="info"):
        getattr(logger, level, logger.info)(msg)
        self._callback(msg, level)

    def _run_ps(self, cmd, timeout=15):
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", cmd],
                capture_output=True,
                text=True,
                timeout=timeout,
                creationflags=CREATE_NO_WINDOW,
            )
            return result.stdout.strip() if result.returncode == 0 else ""
        except Exception:
            return ""

    def detect_vpn_adapters(self):
        """
        Detect VPN network adapters.

        Returns:
            list[dict]: {name, description, status, type}
        """
        if not IS_WINDOWS:
            return []

        self._log("Scanning for VPN adapters...")

        cmd = (
            "Get-NetAdapter | Select-Object Name, InterfaceDescription, "
            "Status, InterfaceType | ConvertTo-Json -Compress"
        )
        output = self._run_ps(cmd)
        if not output:
            return []

        try:
            data = json.loads(output)
            if isinstance(data, dict):
                data = [data]

            vpn_adapters = []
            for a in data:
                name = (a.get("Name") or "").lower()
                desc = (a.get("InterfaceDescription") or "").lower()
                combined = f"{name} {desc}"

                if any(kw in combined for kw in VPN_ADAPTER_KEYWORDS):
                    vpn_adapters.append(
                        {
                            "name": a.get("Name", "Unknown"),
                            "description": a.get("InterfaceDescription", ""),
                            "status": a.get("Status", "Unknown"),
                            "type": "VPN Adapter",
                        }
                    )

            self._log(f"Found {len(vpn_adapters)} VPN adapter(s)")
            return vpn_adapters
        except (json.JSONDecodeError, TypeError):
            return []

    def detect_proxy_settings(self):
        """
        Check system proxy configuration.

        Returns:
            dict: {proxy_enabled, proxy_server, proxy_override, auto_config}
        """
        if not IS_WINDOWS:
            return {}

        self._log("Checking proxy settings...")

        cmd = (
            "Get-ItemProperty -Path "
            "'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings' "
            "-ErrorAction SilentlyContinue | "
            "Select-Object ProxyEnable, ProxyServer, ProxyOverride, AutoConfigURL "
            "| ConvertTo-Json -Compress"
        )
        output = self._run_ps(cmd)
        if not output:
            return {"proxy_enabled": False}

        try:
            data = json.loads(output)
            enabled = bool(data.get("ProxyEnable", 0))
            return {
                "proxy_enabled": enabled,
                "proxy_server": data.get("ProxyServer", "") or "",
                "proxy_override": data.get("ProxyOverride", "") or "",
                "auto_config_url": data.get("AutoConfigURL", "") or "",
            }
        except (json.JSONDecodeError, TypeError):
            return {"proxy_enabled": False}

    def detect_vpn_software(self):
        """
        Detect running VPN software processes.

        Returns:
            list[dict]: {name, pid, path}
        """
        if not IS_WINDOWS:
            return []

        self._log("Scanning for VPN software...")

        try:
            import psutil

            found = []
            for proc in psutil.process_iter(["name", "pid", "exe"]):
                try:
                    pname = (proc.info["name"] or "").lower()
                    if any(vpn in pname for vpn in VPN_PROCESS_NAMES):
                        found.append(
                            {
                                "name": proc.info["name"],
                                "pid": proc.info["pid"],
                                "path": proc.info.get("exe", ""),
                            }
                        )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            self._log(f"Found {len(found)} VPN process(es)")
            return found
        except ImportError:
            return []

    def check_dns_leak(self):
        """
        Check for potential DNS leaks by comparing DNS resolver with public IP.

        Returns:
            dict: {public_ip, dns_servers, potential_leak, details}
        """
        self._log("Checking for DNS leaks...")

        # Get public IP
        public_ip = None
        try:
            result = subprocess.run(
                ["nslookup", "myip.opendns.com", "resolver1.opendns.com"],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=CREATE_NO_WINDOW,
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if "Address" in line:
                        match = re.search(r"(\d+\.\d+\.\d+\.\d+)", line)
                        if match:
                            ip = match.group(1)
                            if not ip.startswith("208.67"):
                                public_ip = ip
        except Exception:
            pass

        # Get configured DNS servers
        dns_servers = []
        cmd = (
            "Get-DnsClientServerAddress -AddressFamily IPv4 | "
            "Where-Object { $_.ServerAddresses.Count -gt 0 } | "
            "Select-Object InterfaceAlias, ServerAddresses | "
            "ConvertTo-Json -Compress"
        )
        output = self._run_ps(cmd)
        if output:
            try:
                data = json.loads(output)
                if isinstance(data, dict):
                    data = [data]
                for d in data:
                    addrs = d.get("ServerAddresses", [])
                    if isinstance(addrs, list):
                        for addr in addrs:
                            if addr and addr not in dns_servers:
                                dns_servers.append(addr)
            except (json.JSONDecodeError, TypeError):
                pass

        # Analyze: if VPN is active but DNS goes to ISP, it's a leak
        vpn_active = len(self.detect_vpn_adapters()) > 0 or len(self.detect_vpn_software()) > 0
        potential_leak = False
        details = "No VPN detected - DNS leak check not applicable"

        if vpn_active:
            # Known public DNS (not leaking if using these)
            safe_dns = [
                "1.1.1.1",
                "1.0.0.1",
                "8.8.8.8",
                "8.8.4.4",
                "9.9.9.9",
                "208.67.222.222",
                "208.67.220.220",
            ]

            isp_dns = [
                d
                for d in dns_servers
                if d not in safe_dns and not d.startswith("10.") and not d.startswith("172.")
            ]
            if isp_dns:
                potential_leak = True
                details = (
                    f"VPN active but DNS may be leaking through ISP servers: {', '.join(isp_dns)}"
                )
            else:
                details = "VPN active and DNS appears to be tunneled correctly"

        return {
            "public_ip": public_ip,
            "dns_servers": dns_servers,
            "vpn_active": vpn_active,
            "potential_leak": potential_leak,
            "details": details,
        }

    def get_full_status(self):
        """
        Complete VPN/proxy detection report.

        Returns:
            dict: Combined status
        """
        self._log("Running full VPN/proxy detection...")

        adapters = self.detect_vpn_adapters()
        proxy = self.detect_proxy_settings()
        software = self.detect_vpn_software()

        vpn_active = len(adapters) > 0 or len(software) > 0
        proxy_active = proxy.get("proxy_enabled", False)

        status = "No VPN/Proxy"
        if vpn_active and proxy_active:
            status = "VPN + Proxy active"
        elif vpn_active:
            status = "VPN active"
        elif proxy_active:
            status = "Proxy active"

        return {
            "status": status,
            "vpn_active": vpn_active,
            "proxy_active": proxy_active,
            "vpn_adapters": adapters,
            "vpn_software": software,
            "proxy_settings": proxy,
        }
