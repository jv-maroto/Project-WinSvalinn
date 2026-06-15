"""
Network Diagnostics Toolkit for WinSvalinn.

Provides ping, traceroute, DNS lookup, routing table,
ARP table, and basic speed test utilities.
"""

import platform
import re
import socket
import subprocess
import time

from winsvalinn.utils.logger import ModuleLogger

logger = ModuleLogger("NetworkDiag")

IS_WINDOWS = platform.system() == "Windows"
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class NetworkDiagnostics:
    """Network diagnostic tools."""

    def __init__(self, callback=None):
        self._callback = callback or (lambda msg, level="info": None)

    def _log(self, msg, level="info"):
        getattr(logger, level, logger.info)(msg)
        self._callback(msg, level)

    def _run_cmd(self, args, timeout=30):
        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=timeout,
                creationflags=CREATE_NO_WINDOW,
            )
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            return "Command timed out"
        except Exception as e:
            return f"Error: {e}"

    def ping(self, host, count=4, timeout_ms=3000):
        """
        Ping a host and return statistics.

        Returns:
            dict: {host, sent, received, lost, loss_pct, min_ms, max_ms, avg_ms, raw}
        """
        self._log(f"Pinging {host}...")

        args = ["ping", "-n", str(count), "-w", str(timeout_ms), host]
        output = self._run_cmd(args, timeout=count * 5 + 10)

        result = {
            "host": host,
            "sent": count,
            "received": 0,
            "lost": count,
            "loss_pct": 100,
            "min_ms": 0,
            "max_ms": 0,
            "avg_ms": 0,
            "raw": output[-1000:] if len(output) > 1000 else output,
        }

        # Parse stats
        for line in output.split("\n"):
            lower = line.lower().strip()
            # Packets: Sent = 4, Received = 4, Lost = 0
            if "received" in lower or "recibidos" in lower:
                nums = re.findall(r"(\d+)", line)
                if len(nums) >= 3:
                    result["sent"] = int(nums[0])
                    result["received"] = int(nums[1])
                    result["lost"] = int(nums[2])
                    if result["sent"] > 0:
                        result["loss_pct"] = round((result["lost"] / result["sent"]) * 100, 1)

            # Minimum = 1ms, Maximum = 3ms, Average = 2ms
            if ("minimum" in lower or "m\u00ednimo" in lower) and "ms" in lower:
                nums = re.findall(r"(\d+)\s*ms", line)
                if len(nums) >= 3:
                    result["min_ms"] = int(nums[0])
                    result["max_ms"] = int(nums[1])
                    result["avg_ms"] = int(nums[2])

        self._log(
            f"Ping {host}: {result['received']}/{result['sent']} received, avg {result['avg_ms']}ms"
        )
        return result

    def traceroute(self, host, max_hops=20):
        """
        Traceroute to a host.

        Returns:
            list[dict]: Per-hop {hop, ip, hostname, rtt_ms}
        """
        self._log(f"Traceroute to {host} (max {max_hops} hops)...")

        output = self._run_cmd(["tracert", "-d", "-h", str(max_hops), host], timeout=max_hops * 5)

        hops = []
        for line in output.split("\n"):
            # Match: "  1    <1 ms    <1 ms    <1 ms  192.168.1.1"
            match = re.match(r"\s*(\d+)\s+(.+?)\s+(\d+\.\d+\.\d+\.\d+|\*)", line.strip())
            if match:
                hop_num = int(match.group(1))
                ip = match.group(3)

                # Extract RTT values
                rtts = re.findall(r"(\d+)\s*ms", line)
                avg_rtt = 0
                if rtts:
                    avg_rtt = round(sum(int(r) for r in rtts) / len(rtts))

                hops.append(
                    {
                        "hop": hop_num,
                        "ip": ip if ip != "*" else "* (timeout)",
                        "rtt_ms": avg_rtt,
                        "timeout": ip == "*",
                    }
                )

        self._log(f"Traceroute complete: {len(hops)} hops")
        return hops

    def port_check_remote(self, host, port, timeout=5):
        """
        Check if a remote port is open.

        Returns:
            dict: {host, port, open, latency_ms}
        """
        self._log(f"Checking {host}:{port}...")

        try:
            start = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            latency = round((time.time() - start) * 1000, 1)
            sock.close()

            is_open = result == 0
            return {
                "host": host,
                "port": port,
                "open": is_open,
                "latency_ms": latency if is_open else 0,
            }
        except socket.gaierror:
            return {"host": host, "port": port, "open": False, "error": "DNS resolution failed"}
        except Exception as e:
            return {"host": host, "port": port, "open": False, "error": str(e)}

    def get_routing_table(self):
        """
        Get the system routing table.

        Returns:
            list[dict]: {destination, netmask, gateway, interface, metric}
        """
        if not IS_WINDOWS:
            return []

        output = self._run_cmd(["route", "print", "-4"])
        routes = []

        in_routes = False
        for line in output.split("\n"):
            stripped = line.strip()
            if "Network Destination" in line or "Destino de red" in line:
                in_routes = True
                continue
            if in_routes and stripped:
                parts = stripped.split()
                if len(parts) >= 5 and re.match(r"\d+\.\d+", parts[0]):
                    routes.append(
                        {
                            "destination": parts[0],
                            "netmask": parts[1],
                            "gateway": parts[2],
                            "interface": parts[3],
                            "metric": parts[4] if len(parts) > 4 else "0",
                        }
                    )
                elif not parts[0][0].isdigit():
                    in_routes = False

        return routes

    def get_arp_table(self):
        """
        Get ARP table entries.

        Returns:
            list[dict]: {ip, mac, type, interface}
        """
        if not IS_WINDOWS:
            return []

        output = self._run_cmd(["arp", "-a"])
        entries = []
        current_interface = ""

        for line in output.split("\n"):
            stripped = line.strip()

            if "Interface" in line or "Interfaz" in line:
                match = re.search(r"(\d+\.\d+\.\d+\.\d+)", stripped)
                if match:
                    current_interface = match.group(1)
                continue

            # Match: "192.168.1.1   aa-bb-cc-dd-ee-ff   dynamic"
            match = re.match(r"(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F-]{17})\s+(\w+)", stripped)
            if match:
                entries.append(
                    {
                        "ip": match.group(1),
                        "mac": match.group(2),
                        "type": match.group(3),
                        "interface": current_interface,
                    }
                )

        return entries

    def dns_lookup(self, domain):
        """
        Perform DNS lookup for a domain.

        Returns:
            dict: {domain, addresses, raw}
        """
        self._log(f"DNS lookup: {domain}")

        output = self._run_cmd(["nslookup", domain], timeout=10)

        addresses = []
        for line in output.split("\n"):
            stripped = line.strip()
            if "Address" in stripped or "Direcci" in stripped:
                match = re.search(r"(\d+\.\d+\.\d+\.\d+)", stripped)
                if match:
                    ip = match.group(1)
                    if ip not in addresses:
                        addresses.append(ip)

        # Also try Python socket for reliability
        try:
            _, _, ips = socket.gethostbyname_ex(domain)
            for ip in ips:
                if ip not in addresses:
                    addresses.append(ip)
        except socket.gaierror:
            pass

        return {
            "domain": domain,
            "addresses": addresses,
            "raw": output[-500:] if len(output) > 500 else output,
        }

    def check_internet(self):
        """
        Check internet connectivity with multiple servers.

        Returns:
            dict: {connected, latency_ms, dns_ok, server}
        """
        self._log("Checking internet connectivity...")

        servers = [
            ("8.8.8.8", 53, "Google DNS"),
            ("1.1.1.1", 53, "Cloudflare DNS"),
            ("208.67.222.222", 53, "OpenDNS"),
        ]

        for ip, port, name in servers:
            try:
                start = time.time()
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                result = sock.connect_ex((ip, port))
                latency = round((time.time() - start) * 1000, 1)
                sock.close()

                if result == 0:
                    # Test DNS resolution
                    dns_ok = True
                    try:
                        socket.gethostbyname("www.google.com")
                    except socket.gaierror:
                        dns_ok = False

                    return {
                        "connected": True,
                        "latency_ms": latency,
                        "dns_ok": dns_ok,
                        "server": name,
                    }
            except Exception:
                continue

        return {"connected": False, "latency_ms": 0, "dns_ok": False, "server": "None"}

    def get_public_ip(self):
        """
        Get public IP address via DNS query (no HTTP needed).

        Returns:
            str or None
        """
        try:
            # Use OpenDNS resolver to get public IP
            import subprocess

            result = subprocess.run(
                ["nslookup", "myip.opendns.com", "resolver1.opendns.com"],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=CREATE_NO_WINDOW,
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if "Address" in line and "resolver" not in line.lower():
                        match = re.search(r"(\d+\.\d+\.\d+\.\d+)", line)
                        if match:
                            ip = match.group(1)
                            if not ip.startswith("208.67"):  # Skip OpenDNS server IP
                                return ip
        except Exception:
            pass
        return None
