"""
Local Network Scanner for WinSvalinn (core engine, no GUI imports).

Discovers devices on the local subnet via an ARP sweep, identifies them by
MAC vendor prefix, and flags unknown hosts. Also reports the default gateway,
DNS servers, active TCP connections, and listening ports.

Logic migrated from the legacy ``plugin_netscan`` filesystem plugin.
Read-only: it only reads ARP/route tables and network configuration. The ping
sweep is a discovery probe; it does not change system state.
"""

from __future__ import annotations

import contextlib
import json
import platform
import re
import subprocess
from collections.abc import Callable

from winsvalinn.utils.logger import ModuleLogger

logger = ModuleLogger("NetworkScanner")

IS_WINDOWS = platform.system() == "Windows"
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

# Common MAC prefixes for device identification.
MAC_VENDORS = {
    "00:50:56": "VMware",
    "00:0c:29": "VMware",
    "00:15:5d": "Hyper-V",
    "08:00:27": "VirtualBox",
    "b8:27:eb": "Raspberry Pi",
    "dc:a6:32": "Raspberry Pi",
    "e4:5f:01": "Raspberry Pi",
    "3c:22:fb": "Apple",
    "a4:83:e7": "Apple",
    "f0:18:98": "Apple",
    "88:e9:fe": "Apple",
    "ac:de:48": "Apple",
    "00:17:88": "Philips Hue",
    "ec:fa:bc": "Philips Hue",
    "30:05:5c": "Google",
    "f4:f5:d8": "Google",
    "54:60:09": "Google",
    "a4:77:33": "Google",
    "44:07:0b": "Google",
    "fc:e8:06": "Amazon",
    "40:b4:cd": "Amazon",
    "f0:f0:a4": "Amazon",
    "68:54:fd": "Amazon",
    "74:c2:46": "Amazon",
    "50:dc:e7": "Amazon",
    "b0:fc:0d": "Samsung",
    "a8:7c:01": "Samsung",
    "5c:3a:45": "Samsung",
    "44:4e:1a": "Samsung",
    "c0:97:27": "Samsung",
    "a0:ab:1b": "Samsung",
    "d4:6e:0e": "TP-Link",
    "50:c7:bf": "TP-Link",
    "70:4f:57": "TP-Link",
    "b0:be:76": "TP-Link",
    "a8:42:a1": "NETGEAR",
    "28:c6:8e": "NETGEAR",
    "c0:3f:0e": "NETGEAR",
    "20:cf:30": "ASUSTek",
    "04:d4:c4": "ASUSTek",
    "ac:9e:17": "ASUSTek",
}


class NetworkScanner:
    """Scan the local network and report devices, gateway, and connections."""

    def __init__(self, callback: Callable[[str, str], None] | None = None) -> None:
        self._callback = callback or (lambda msg, level="info": None)

    def _log(self, msg: str, level: str = "info") -> None:
        getattr(logger, level, logger.info)(msg)
        self._callback(msg, level)

    def _identify_vendor(self, mac: str) -> str:
        """Identify a device vendor from its MAC prefix."""
        prefix = mac.upper().replace("-", ":")[:8].lower()
        return MAC_VENDORS.get(prefix, "Unknown")

    def _run_ps(self, cmd: str, timeout: int = 30) -> str:
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", cmd],
                capture_output=True,
                text=True,
                timeout=timeout,
                creationflags=CREATE_NO_WINDOW,
            )
            return result.stdout.strip() if result.returncode == 0 else ""
        except (subprocess.TimeoutExpired, OSError) as exc:
            logger.error(f"Network PS error: {exc}")
            return ""

    def scan_network(self) -> list[dict]:
        """
        Discover devices on the local subnet via ARP (after a ping sweep).

        Returns:
            list[dict]: [{ip, mac, type, vendor}] sorted by IP
        """
        if not IS_WINDOWS:
            self._log("Network scan is only available on Windows", "warning")
            return []

        self._log("Scanning local network (ARP)...")

        local_ip = self._run_ps(
            "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object { "
            "$_.InterfaceAlias -notlike '*Loopback*' -and $_.IPAddress -notlike "
            "'169.*' } | Select-Object -First 1).IPAddress",
            timeout=10,
        )

        parts = local_ip.split(".")
        if len(parts) == 4:
            subnet = f"{parts[0]}.{parts[1]}.{parts[2]}"
            self._log(f"Local IP: {local_ip} (subnet: {subnet}.0/24)")
            self._log("Ping sweeping subnet (this takes ~10 seconds)...")
            self._run_ps(
                f"1..254 | ForEach-Object -Parallel {{ Test-Connection "
                f"-ComputerName '{subnet}.$_' -Count 1 -TimeoutSeconds 1 -Quiet }} "
                f"-ThrottleLimit 50",
                timeout=40,
            )

        try:
            result = subprocess.run(
                ["arp", "-a"],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=CREATE_NO_WINDOW,
            )
        except (subprocess.TimeoutExpired, OSError) as exc:
            self._log(f"ARP read failed: {exc}", "error")
            return []

        devices = []
        for line in result.stdout.split("\n"):
            match = re.match(r"\s*(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F-]{17})\s+(\w+)", line.strip())
            if not match:
                continue
            ip, mac, dtype = match.group(1), match.group(2), match.group(3)
            if mac.lower() == "ff-ff-ff-ff-ff-ff":
                continue
            devices.append(
                {
                    "ip": ip,
                    "mac": mac,
                    "type": dtype,
                    "vendor": self._identify_vendor(mac),
                }
            )

        devices.sort(key=lambda x: [int(p) for p in x["ip"].split(".")])
        unknown = sum(1 for d in devices if d["vendor"] == "Unknown")
        self._log(
            f"Found {len(devices)} device(s), {unknown} unknown",
            "warning" if unknown else "info",
        )
        return devices

    def get_gateway_info(self) -> dict:
        """
        Report the default gateway route and configured DNS servers.

        Returns:
            dict: {gateway: str, dns: list[str]}
        """
        if not IS_WINDOWS:
            return {"gateway": "", "dns": []}

        self._log("Reading gateway and DNS configuration...")
        gateway = self._run_ps(
            "(Get-NetRoute -DestinationPrefix '0.0.0.0/0' | Select-Object -First 1).NextHop",
            timeout=10,
        )

        dns_raw = self._run_ps(
            "Get-DnsClientServerAddress -AddressFamily IPv4 | "
            "Where-Object { $_.ServerAddresses.Count -gt 0 } | "
            "ForEach-Object { $_.ServerAddresses } | Sort-Object -Unique | "
            "ConvertTo-Json -Compress",
            timeout=10,
        )
        dns: list[str] = []
        if dns_raw:
            try:
                data = json.loads(dns_raw)
                dns = data if isinstance(data, list) else [data]
            except (json.JSONDecodeError, ValueError):
                dns = []

        return {"gateway": gateway, "dns": dns}

    def get_active_connections(self, limit: int = 50) -> list[dict]:
        """
        Report established TCP connections with owning process names.

        Returns:
            list[dict]: [{process, local, remote, pid}]
        """
        try:
            import psutil
        except ImportError:
            self._log("psutil required for this feature", "error")
            return []

        connections = psutil.net_connections(kind="inet")
        established = [c for c in connections if c.status == "ESTABLISHED" and c.raddr]
        established.sort(key=lambda c: c.pid or 0)

        results = []
        for c in established[:limit]:
            name = "N/A"
            with contextlib.suppress(psutil.NoSuchProcess, psutil.AccessDenied):
                name = psutil.Process(c.pid).name() if c.pid else "N/A"
            results.append(
                {
                    "process": name,
                    "local": f"{c.laddr.ip}:{c.laddr.port}",
                    "remote": f"{c.raddr.ip}:{c.raddr.port}",
                    "pid": c.pid or 0,
                }
            )

        self._log(f"Found {len(results)} established connection(s)")
        return results

    def get_listening_ports(self, limit: int = 60) -> list[dict]:
        """
        Report listening sockets with owning process names.

        Returns:
            list[dict]: [{port, process, address, pid}]
        """
        try:
            import psutil
        except ImportError:
            self._log("psutil required for this feature", "error")
            return []

        connections = psutil.net_connections(kind="inet")
        listening = [c for c in connections if c.status == "LISTEN"]
        listening.sort(key=lambda c: c.laddr.port)

        results = []
        for c in listening[:limit]:
            name = "N/A"
            with contextlib.suppress(psutil.NoSuchProcess, psutil.AccessDenied):
                name = psutil.Process(c.pid).name() if c.pid else "N/A"
            results.append(
                {
                    "port": c.laddr.port,
                    "process": name,
                    "address": c.laddr.ip,
                    "pid": c.pid or 0,
                }
            )

        self._log(f"Found {len(results)} listening port(s)")
        return results

    def audit(self) -> dict:
        """
        Full read-only network audit: devices, gateway, connections, ports.

        Returns:
            dict: aggregated audit result
        """
        devices = self.scan_network()
        gateway = self.get_gateway_info()
        connections = self.get_active_connections()
        listening = self.get_listening_ports()
        unknown = [d for d in devices if d["vendor"] == "Unknown"]

        return {
            "devices": devices,
            "device_count": len(devices),
            "unknown_devices": len(unknown),
            "gateway": gateway,
            "active_connections": connections,
            "listening_ports": listening,
        }
