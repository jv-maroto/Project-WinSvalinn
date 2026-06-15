"""
Security Module - WinSvalinn
Handles all system security analysis functions.
"""

import concurrent.futures
import os
import platform
import re
import socket
import subprocess
import time
from datetime import datetime

try:
    import psutil
except ImportError:
    psutil = None


class SecurityScanner:
    """Core security scanning engine."""

    # Ports that must NEVER be blocked - blocking these can crash/restart Windows
    SYSTEM_CRITICAL_PORTS = {
        53: "DNS - blocks all internet",
        67: "DHCP Server - breaks IP assignment",
        68: "DHCP Client - breaks IP assignment",
        88: "Kerberos - breaks domain authentication",
        123: "NTP - breaks time synchronization",
        135: "RPC/DCOM - critical Windows service (BSOD risk)",
        137: "NetBIOS Name - breaks Windows networking",
        138: "NetBIOS Datagram - breaks Windows networking",
        139: "NetBIOS Session - breaks Windows networking",
        389: "LDAP - breaks domain authentication",
        443: "HTTPS - blocks secure web traffic",
        445: "SMB - critical Windows service (BSOD risk)",
        464: "Kerberos Password - breaks domain password changes",
        636: "LDAPS - breaks secure domain authentication",
        3389: "RDP - blocks remote desktop access",
        5985: "WinRM HTTP - breaks Windows remote management",
        5986: "WinRM HTTPS - breaks Windows remote management",
    }

    def __init__(self, callback=None):
        self.callback = callback or (lambda msg, level="info": None)
        self.scan_active = False

    def log(self, message, level="info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.callback(f"[{timestamp}] {message}", level)

    # ─── Network Connections & Filtered IPs ─────────────────────────────

    def get_active_connections(self):
        """Get all active network connections with process info."""
        connections = []
        if not psutil:
            return connections
        try:
            for conn in psutil.net_connections(kind="inet"):
                entry = {
                    "fd": conn.fd,
                    "family": "IPv4" if conn.family == socket.AF_INET else "IPv6",
                    "type": "TCP" if conn.type == socket.SOCK_STREAM else "UDP",
                    "local_addr": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "N/A",
                    "remote_addr": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A",
                    "status": conn.status if hasattr(conn, "status") else "N/A",
                    "pid": conn.pid,
                    "process": "N/A",
                }
                if conn.pid:
                    try:
                        proc = psutil.Process(conn.pid)
                        entry["process"] = proc.name()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                connections.append(entry)
        except (psutil.AccessDenied, PermissionError):
            self.log("Access denied reading network connections. Run as Administrator.", "warning")
        return connections

    def detect_suspicious_ips(self):
        """Detect suspicious remote IPs based on heuristics."""
        suspicious = []
        connections = self.get_active_connections()
        suspicious_ports = {
            4444,
            5555,
            6666,
            7777,
            8888,
            9999,
            1337,
            31337,
            4443,
            8443,
            3389,
            5900,
            5800,
            6667,
            6668,
            6669,
            12345,
            27374,
            65535,
            1234,
            54321,
        }

        private_ranges = [
            ("10.", "10."),
            ("172.16.", "172.31."),
            ("192.168.", "192.168."),
            ("127.", "127."),
        ]

        for conn in connections:
            if conn["remote_addr"] == "N/A":
                continue
            ip, port_str = conn["remote_addr"].rsplit(":", 1)
            port = int(port_str)

            is_private = any(ip.startswith(r[0]) for r in private_ranges)

            reasons = []
            if port in suspicious_ports:
                reasons.append(f"Suspicious port: {port}")
            if not is_private and conn["status"] == "ESTABLISHED":
                if port not in {80, 443, 53, 8080}:
                    reasons.append(f"Non-standard external connection on port {port}")

            if reasons:
                suspicious.append(
                    {
                        "ip": ip,
                        "port": port,
                        "process": conn["process"],
                        "pid": conn["pid"],
                        "reasons": reasons,
                        "status": conn["status"],
                    }
                )
        return suspicious

    # ─── Port Scanning ──────────────────────────────────────────────────

    WELL_KNOWN_PORTS = {
        20: "FTP-Data",
        21: "FTP",
        22: "SSH",
        23: "Telnet",
        25: "SMTP",
        53: "DNS",
        80: "HTTP",
        110: "POP3",
        135: "RPC",
        137: "NetBIOS",
        138: "NetBIOS",
        139: "NetBIOS",
        143: "IMAP",
        443: "HTTPS",
        445: "SMB",
        993: "IMAPS",
        995: "POP3S",
        1433: "MSSQL",
        1521: "Oracle",
        3306: "MySQL",
        3389: "RDP",
        5432: "PostgreSQL",
        5900: "VNC",
        6379: "Redis",
        8080: "HTTP-Proxy",
        8443: "HTTPS-Alt",
        27017: "MongoDB",
    }

    RISKY_PORTS = {23, 135, 137, 138, 139, 445, 3389, 5900, 1433, 3306, 5432, 6379, 27017}

    def _scan_single_port(self, port, timeout=0.5):
        """Scan a single port (thread-safe)."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex(("127.0.0.1", port))
            sock.close()

            if result == 0:
                service = self.WELL_KNOWN_PORTS.get(port, "Unknown")
                risk = (
                    "HIGH"
                    if port in self.RISKY_PORTS
                    else ("SYSTEM" if port in self.SYSTEM_CRITICAL_PORTS else "LOW")
                )
                return {"port": port, "service": service, "risk": risk, "state": "OPEN"}
        except OSError:
            pass
        return None

    def scan_local_ports(self, port_range=(1, 1024), timeout=0.5, max_workers=100):
        """
        Scan local machine for open ports using concurrent scanning.

        Uses ThreadPoolExecutor for parallel scanning (~96x faster than sequential).
        """
        open_ports = []
        total_ports = port_range[1] - port_range[0] + 1

        self.log(f"Scanning ports {port_range[0]}-{port_range[1]} (parallel mode)...")

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_port = {
                    executor.submit(self._scan_single_port, port, timeout): port
                    for port in range(port_range[0], port_range[1] + 1)
                }

                completed = 0
                for future in concurrent.futures.as_completed(future_to_port):
                    if not self.scan_active:
                        break

                    completed += 1
                    if completed % 100 == 0:
                        progress = (completed / total_ports) * 100
                        self.log(f"Progress: {completed}/{total_ports} ({progress:.0f}%)")

                    result = future.result()
                    if result:
                        open_ports.append(result)
                        risk_level = "warning" if result["risk"] in ("HIGH", "SYSTEM") else "info"
                        self.log(
                            f"Port {result['port']} ({result['service']}) - OPEN [{result['risk']} risk]",
                            risk_level,
                        )

        except Exception as e:
            self.log(f"Port scan error: {str(e)}", "error")

        self.log(f"Scan complete: {len(open_ports)} open ports found")
        return open_ports

    # ─── Process Analysis (Malware Detection) ───────────────────────────

    # Well-known Windows system processes that should not be flagged
    SYSTEM_PROCESS_WHITELIST = {
        "system",
        "registry",
        "memory compression",
        "csrss.exe",
        "smss.exe",
        "wininit.exe",
        "services.exe",
        "lsass.exe",
        "svchost.exe",
        "dwm.exe",
        "winlogon.exe",
        "fontdrvhost.exe",
        "spoolsv.exe",
        "searchindexer.exe",
        "idle",
        "system idle process",
        "secure system",
        "lsaiso.exe",
        "conhost.exe",
        "dllhost.exe",
        "sihost.exe",
        "taskhostw.exe",
        "runtimebroker.exe",
        "shellexperiencehost.exe",
        "startmenuexperiencehost.exe",
        "searchhost.exe",
        "explorer.exe",
        "ctfmon.exe",
        "audiodg.exe",
    }

    def analyze_processes(self):
        """Analyze running processes for suspicious behavior."""
        suspicious_processes = []
        if not psutil:
            return suspicious_processes

        # Whitelist: don't flag our own process or its children
        own_pid = os.getpid()
        own_name_lower = "winguardoptimizer"
        whitelist_pids = {own_pid}
        try:
            own_proc = psutil.Process(own_pid)
            whitelist_pids.add(own_proc.ppid())
            for child in own_proc.children(recursive=True):
                whitelist_pids.add(child.pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

        # Max possible CPU across all cores
        max_cpu = 100.0 * (os.cpu_count() or 1)

        suspicious_paths = [
            "temp",
            "tmp",
            "appdata\\local\\temp",
            "downloads",
            "public",
            "programdata",
        ]
        suspicious_names = [
            "cmd.exe",
            "powershell.exe",
            "wscript.exe",
            "cscript.exe",
            "mshta.exe",
            "regsvr32.exe",
            "rundll32.exe",
            "certutil.exe",
            "bitsadmin.exe",
        ]

        for proc in psutil.process_iter(
            [
                "pid",
                "name",
                "exe",
                "cmdline",
                "cpu_percent",
                "memory_percent",
                "create_time",
                "username",
            ]
        ):
            try:
                info = proc.info

                # Skip our own process and children
                if info["pid"] in whitelist_pids:
                    continue
                name_check = (info["name"] or "").lower()
                if own_name_lower in name_check or "winguard" in name_check:
                    continue
                # Skip if exe path contains our app directory
                if info["exe"] and own_name_lower in info["exe"].lower():
                    continue

                # Skip well-known Windows system processes (Issue 4)
                if name_check in self.SYSTEM_PROCESS_WHITELIST:
                    continue

                # Skip NT AUTHORITY\SYSTEM processes unless they have
                # genuinely suspicious command lines
                username = info["username"] or ""
                if (
                    "NT AUTHORITY\\SYSTEM" in username.upper()
                    or "NT AUTHORITY\\LOCAL SERVICE" in username.upper()
                    or "NT AUTHORITY\\NETWORK SERVICE" in username.upper()
                ):
                    # Only flag if command line is truly suspicious
                    has_suspicious_cmd = False
                    if info["cmdline"] and len(info["cmdline"]) > 1:
                        cmd = " ".join(info["cmdline"]).lower()
                        if any(
                            kw in cmd
                            for kw in [
                                "http",
                                "ftp",
                                "download",
                                "encode",
                                "decode",
                                "bypass",
                                "hidden",
                                "-w hidden",
                                "-enc",
                                "-encodedcommand",
                            ]
                        ):
                            has_suspicious_cmd = True
                    if not has_suspicious_cmd:
                        continue

                # Cap CPU reading and skip first-read artifacts (Issue 4)
                raw_cpu = info["cpu_percent"] or 0
                cpu_capped = min(raw_cpu, max_cpu)
                # If CPU > 100% per core, it's likely a first-read artifact
                if raw_cpu > max_cpu:
                    continue

                reasons = []
                risk_level = "LOW"

                # Check execution from suspicious paths
                if info["exe"]:
                    exe_lower = info["exe"].lower()
                    for susp_path in suspicious_paths:
                        if susp_path in exe_lower:
                            reasons.append(f"Running from suspicious path: {info['exe']}")
                            risk_level = "MEDIUM"

                # Check unsigned or suspicious process names
                name_lower = (info["name"] or "").lower()
                if name_lower in suspicious_names:
                    # These are legit Windows processes but often abused
                    if info["cmdline"] and len(info["cmdline"]) > 1:
                        cmd = " ".join(info["cmdline"]).lower()
                        if any(
                            kw in cmd
                            for kw in [
                                "http",
                                "ftp",
                                "download",
                                "encode",
                                "decode",
                                "bypass",
                                "hidden",
                                "-w hidden",
                                "-enc",
                                "-encodedcommand",
                            ]
                        ):
                            reasons.append(
                                f"Suspicious command line: {' '.join(info['cmdline'][:3])}"
                            )
                            risk_level = "HIGH"

                # High CPU/memory usage (use capped value)
                if cpu_capped and cpu_capped > 80:
                    # Normalize display: show per-core percentage if > 100
                    display_cpu = cpu_capped
                    if display_cpu > 100:
                        cores = os.cpu_count() or 1
                        display_cpu = cpu_capped / cores
                    reasons.append(f"High CPU usage: {display_cpu:.1f}%")
                    if risk_level == "LOW":
                        risk_level = "MEDIUM"

                if info["memory_percent"] and info["memory_percent"] > 15:
                    reasons.append(f"High memory usage: {info['memory_percent']:.1f}%")

                # Process with no name or hidden
                if not info["name"]:
                    reasons.append("Process with no name detected")
                    risk_level = "HIGH"

                if reasons:
                    suspicious_processes.append(
                        {
                            "pid": info["pid"],
                            "name": info["name"] or "Unknown",
                            "exe": info["exe"] or "N/A",
                            "reasons": reasons,
                            "risk": risk_level,
                            "cpu": cpu_capped,
                            "memory": info["memory_percent"],
                            "user": info["username"] or "N/A",
                        }
                    )

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        return suspicious_processes

    # ─── Startup Programs Analysis ──────────────────────────────────────

    def get_startup_programs(self):
        """Get all startup programs from registry and startup folders."""
        startup_items = []

        if platform.system() != "Windows":
            self.log("Startup analysis only available on Windows", "warning")
            return startup_items

        # Registry locations for startup
        reg_paths = [
            r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
            r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce",
            r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
            r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce",
            r"HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run",
        ]

        for reg_path in reg_paths:
            try:
                result = subprocess.run(
                    ["reg", "query", reg_path],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split("\n")
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith("HKEY"):
                            parts = re.split(r"\s{2,}", line, maxsplit=2)
                            if len(parts) >= 3:
                                startup_items.append(
                                    {
                                        "name": parts[0].strip(),
                                        "type": parts[1].strip(),
                                        "value": parts[2].strip(),
                                        "location": reg_path,
                                        "source": "Registry",
                                    }
                                )
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                continue

        # Startup folders
        startup_folders = []
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            startup_folders.append(
                os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs\Startup")
            )
        programdata = os.environ.get("PROGRAMDATA", "")
        if programdata:
            startup_folders.append(
                os.path.join(programdata, r"Microsoft\Windows\Start Menu\Programs\Startup")
            )

        for folder in startup_folders:
            if os.path.exists(folder):
                for item in os.listdir(folder):
                    startup_items.append(
                        {
                            "name": item,
                            "type": "File",
                            "value": os.path.join(folder, item),
                            "location": folder,
                            "source": "Startup Folder",
                        }
                    )

        return startup_items

    def disable_startup_program(self, item):
        """Disable a startup program by removing its registry entry or file.
        item: dict with 'name', 'source', 'location', 'value'."""
        if platform.system() != "Windows":
            return {"success": False, "error": "Windows only"}

        name = item.get("name", "")
        source = item.get("source", "")
        location = item.get("location", "")

        if source == "Registry" and location:
            # Delete registry value
            ok, out, err = self._run_cmd(["reg", "delete", location, "/v", name, "/f"])
            if ok:
                self.log(f"Disabled startup: {name}", "success")
                return {"success": True, "actions": [f"Removed {name} from {location}"]}
            return {"success": False, "error": f"Could not remove {name}: {err[:100]}"}

        elif source == "Startup Folder" and location:
            # Delete the shortcut file from startup folder
            file_path = os.path.join(location, name)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    self.log(f"Removed startup file: {name}", "success")
                    return {"success": True, "actions": [f"Removed {name} from startup folder"]}
                except OSError as e:
                    return {"success": False, "error": str(e)}

        return {"success": False, "error": f"Unknown startup item type: {source}"}

    # ─── Firewall Status ────────────────────────────────────────────────

    def check_firewall_status(self):
        """Check Windows Firewall status."""
        firewall_info = {
            "domain": "Unknown",
            "private": "Unknown",
            "public": "Unknown",
            "rules_count": 0,
        }

        if platform.system() != "Windows":
            return firewall_info

        try:
            result = subprocess.run(
                ["netsh", "advfirewall", "show", "allprofiles", "state"],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if result.returncode == 0:
                output = result.stdout
                profiles = {"Domain": "domain", "Private": "private", "Public": "public"}
                for profile_name, key in profiles.items():
                    pattern = rf"{profile_name}.*?State\s+(ON|OFF)"
                    match = re.search(pattern, output, re.IGNORECASE | re.DOTALL)
                    if match:
                        firewall_info[key] = match.group(1).upper()
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

        try:
            result = subprocess.run(
                ["netsh", "advfirewall", "firewall", "show", "rule", "name=all"],
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if result.returncode == 0:
                firewall_info["rules_count"] = result.stdout.count("Rule Name:")
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

        return firewall_info

    # ─── DNS Cache Analysis ─────────────────────────────────────────────

    def analyze_dns_cache(self):
        """Analyze DNS cache for suspicious entries."""
        dns_entries = []
        suspicious_tlds = [
            ".ru",
            ".cn",
            ".tk",
            ".ml",
            ".ga",
            ".cf",
            ".xyz",
            ".top",
            ".buzz",
            ".club",
        ]

        if platform.system() != "Windows":
            return dns_entries

        try:
            result = subprocess.run(
                ["ipconfig", "/displaydns"],
                capture_output=True,
                text=True,
                timeout=15,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if result.returncode == 0:
                current_entry = {}
                for line in result.stdout.split("\n"):
                    line = line.strip()
                    if "Record Name" in line:
                        if current_entry:
                            dns_entries.append(current_entry)
                        name = line.split(":")[-1].strip()
                        is_suspicious = any(name.endswith(tld) for tld in suspicious_tlds)
                        current_entry = {
                            "name": name,
                            "type": "",
                            "ttl": "",
                            "data": "",
                            "suspicious": is_suspicious,
                        }
                    elif "Record Type" in line and current_entry:
                        current_entry["type"] = line.split(":")[-1].strip()
                    elif "Time To Live" in line and current_entry:
                        current_entry["ttl"] = line.split(":")[-1].strip()
                    elif ("A (Host)" in line or "AAAA" in line) and current_entry:
                        current_entry["data"] = line.split(":")[-1].strip()

                if current_entry:
                    dns_entries.append(current_entry)
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

        return dns_entries

    # ─── ARP Table Analysis ─────────────────────────────────────────────

    def analyze_arp_table(self):
        """Analyze ARP table for potential ARP spoofing.
        Only flags duplicate MACs that involve the default gateway IP,
        which is the actual indicator of a MITM attack.
        Normal duplicate MACs (VMs, bridges, multiple adapters) are ignored."""
        arp_entries = []

        # Get the default gateway IP to check for real ARP spoofing
        gateway_ip = self._get_default_gateway()

        try:
            result = subprocess.run(
                ["arp", "-a"],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
                if platform.system() == "Windows"
                else 0,
            )
            if result.returncode == 0:
                mac_to_ips = {}  # mac -> list of IPs
                entries = []
                for line in result.stdout.split("\n"):
                    parts = line.split()
                    if len(parts) >= 3:
                        ip = parts[0]
                        mac = parts[1]
                        if re.match(r"\d+\.\d+\.\d+\.\d+", ip):
                            entry_type = parts[2] if len(parts) > 2 else "unknown"
                            entries.append({"ip": ip, "mac": mac, "type": entry_type})
                            if mac not in (
                                "ff-ff-ff-ff-ff-ff",
                                "(incomplete)",
                                "00-00-00-00-00-00",
                            ):
                                mac_to_ips.setdefault(mac, []).append(ip)

                # Only flag as spoofing if a duplicate MAC involves the gateway
                # This is the real indicator of a MITM/ARP spoofing attack
                spoofing_macs = set()
                if gateway_ip:
                    for mac, ips in mac_to_ips.items():
                        if len(ips) > 1 and gateway_ip in ips:
                            spoofing_macs.add(mac)

                for entry in entries:
                    entry["spoofing_risk"] = entry["mac"] in spoofing_macs
                    arp_entries.append(entry)

        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

        return arp_entries

    @staticmethod
    def _get_default_gateway():
        """Get the default gateway IP address."""
        if platform.system() != "Windows":
            return None
        try:
            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "(Get-NetRoute -DestinationPrefix '0.0.0.0/0' | "
                    "Select-Object -First 1).NextHop",
                ],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if result.returncode == 0 and result.stdout.strip():
                gw = result.stdout.strip()
                if re.match(r"\d+\.\d+\.\d+\.\d+", gw):
                    return gw
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
        # Fallback: parse ipconfig
        try:
            result = subprocess.run(
                ["ipconfig"],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if result.returncode == 0:
                match = re.search(r"Default Gateway.*?:\s*(\d+\.\d+\.\d+\.\d+)", result.stdout)
                if match:
                    return match.group(1)
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
        return None

    # ─── Scheduled Tasks Analysis ───────────────────────────────────────

    def analyze_scheduled_tasks(self):
        """Analyze scheduled tasks for suspicious entries."""
        tasks = []

        if platform.system() != "Windows":
            return tasks

        try:
            result = subprocess.run(
                ["schtasks", "/query", "/fo", "CSV", "/v"],
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                if len(lines) > 1:
                    lines[0].replace('"', "").split(",")
                    for line in lines[1:]:
                        values = line.replace('"', "").split(",")
                        if len(values) >= 9:
                            task_name = values[1] if len(values) > 1 else ""
                            task_action = values[8] if len(values) > 8 else ""

                            suspicious = False
                            reasons = []
                            action_lower = task_action.lower()
                            if any(
                                kw in action_lower
                                for kw in [
                                    "powershell",
                                    "cmd",
                                    "wscript",
                                    "cscript",
                                    "mshta",
                                    "http",
                                    "ftp",
                                    "temp",
                                    "tmp",
                                ]
                            ):
                                suspicious = True
                                reasons.append("Uses scripting engine or network access")

                            if task_name and not task_name.startswith("\\Microsoft"):
                                tasks.append(
                                    {
                                        "name": task_name,
                                        "action": task_action[:100],
                                        "status": values[3] if len(values) > 3 else "N/A",
                                        "next_run": values[2] if len(values) > 2 else "N/A",
                                        "suspicious": suspicious,
                                        "reasons": reasons,
                                    }
                                )
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

        return tasks

    # ─── Windows Defender Status ────────────────────────────────────────

    def check_defender_status(self):
        """Check Windows Defender / antivirus status."""
        defender_info = {
            "status": "Unknown",
            "real_time": "Unknown",
            "definitions": "Unknown",
            "last_scan": "Unknown",
        }

        if platform.system() != "Windows":
            return defender_info

        try:
            result = subprocess.run(
                [
                    "powershell",
                    "-Command",
                    "Get-MpComputerStatus | Select-Object "
                    "AntivirusEnabled,RealTimeProtectionEnabled,"
                    "AntivirusSignatureLastUpdated,"
                    "QuickScanEndTime | Format-List",
                ],
                capture_output=True,
                text=True,
                timeout=15,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if result.returncode == 0:
                output = result.stdout
                if "AntivirusEnabled" in output:
                    match = re.search(r"AntivirusEnabled\s*:\s*(\w+)", output)
                    if match:
                        defender_info["status"] = (
                            "Enabled" if match.group(1) == "True" else "Disabled"
                        )
                if "RealTimeProtectionEnabled" in output:
                    match = re.search(r"RealTimeProtectionEnabled\s*:\s*(\w+)", output)
                    if match:
                        defender_info["real_time"] = (
                            "Enabled" if match.group(1) == "True" else "Disabled"
                        )
                if "AntivirusSignatureLastUpdated" in output:
                    match = re.search(r"AntivirusSignatureLastUpdated\s*:\s*(.+)", output)
                    if match:
                        defender_info["definitions"] = match.group(1).strip()
                if "QuickScanEndTime" in output:
                    match = re.search(r"QuickScanEndTime\s*:\s*(.+)", output)
                    if match:
                        defender_info["last_scan"] = match.group(1).strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

        return defender_info

    # ─── Shared Resources ───────────────────────────────────────────────

    def check_shared_resources(self):
        """Check network shared folders/resources."""
        shares = []

        if platform.system() != "Windows":
            return shares

        try:
            result = subprocess.run(
                ["net", "share"],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                for line in lines[4:]:  # Skip header lines
                    parts = re.split(r"\s{2,}", line.strip())
                    if len(parts) >= 2 and parts[0] and not line.startswith("The command"):
                        shares.append(
                            {
                                "name": parts[0],
                                "resource": parts[1] if len(parts) > 1 else "N/A",
                                "remark": parts[2] if len(parts) > 2 else "",
                            }
                        )
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

        return shares

    # ─── Listening Services ─────────────────────────────────────────────

    def get_listening_services(self):
        """Get all services listening on network ports."""
        services = []
        if not psutil:
            return services

        try:
            for conn in psutil.net_connections(kind="inet"):
                if conn.status == "LISTEN":
                    proc_name = "N/A"
                    if conn.pid:
                        try:
                            proc = psutil.Process(conn.pid)
                            proc_name = proc.name()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                    services.append(
                        {
                            "port": conn.laddr.port,
                            "address": conn.laddr.ip,
                            "pid": conn.pid,
                            "process": proc_name,
                            "family": "IPv4" if conn.family == socket.AF_INET else "IPv6",
                        }
                    )
        except (psutil.AccessDenied, PermissionError):
            pass

        return services

    # ─── User Accounts Analysis ─────────────────────────────────────────

    def analyze_user_accounts(self):
        """Analyze local user accounts for security issues."""
        accounts = []

        if platform.system() != "Windows":
            return accounts

        try:
            result = subprocess.run(
                ["net", "user"],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                for line in lines[4:]:
                    names = line.split()
                    for name in names:
                        name = name.strip()
                        if name and name != "The" and name != "command":
                            accounts.append({"name": name, "groups": []})

            # Get admin group members
            result2 = subprocess.run(
                ["net", "localgroup", "Administrators"],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if result2.returncode == 0:
                admin_users = set()
                in_members = False
                for line in result2.stdout.split("\n"):
                    if "---" in line:
                        in_members = True
                        continue
                    if in_members and line.strip() and "The command" not in line:
                        admin_users.add(line.strip())
                for acc in accounts:
                    if acc["name"] in admin_users:
                        acc["groups"].append("Administrators")
                        acc["is_admin"] = True
                    else:
                        acc["is_admin"] = False

        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

        return accounts

    # ─── Windows Update Status ──────────────────────────────────────────

    def check_windows_updates(self):
        """Check Windows Update status and pending updates."""
        update_info = {"last_check": "Unknown", "pending_count": 0, "auto_update": "Unknown"}

        if platform.system() != "Windows":
            return update_info

        try:
            result = subprocess.run(
                [
                    "powershell",
                    "-Command",
                    "(Get-HotFix | Sort-Object InstalledOn -Descending "
                    "| Select-Object -First 1).InstalledOn",
                ],
                capture_output=True,
                text=True,
                timeout=20,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if result.returncode == 0 and result.stdout.strip():
                update_info["last_check"] = result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

        return update_info

    # ─── Full Security Scan ─────────────────────────────────────────────

    def run_full_scan(self, progress_callback=None):
        """Run a comprehensive security scan."""
        self.scan_active = True
        results = {}
        steps = [
            ("Active Connections", self.get_active_connections),
            ("Suspicious IPs", self.detect_suspicious_ips),
            ("Listening Services", self.get_listening_services),
            ("Process Analysis", self.analyze_processes),
            ("Firewall Status", self.check_firewall_status),
            ("Defender Status", self.check_defender_status),
            ("DNS Cache", self.analyze_dns_cache),
            ("ARP Table", self.analyze_arp_table),
            ("Startup Programs", self.get_startup_programs),
            ("Scheduled Tasks", self.analyze_scheduled_tasks),
            ("Shared Resources", self.check_shared_resources),
            ("User Accounts", self.analyze_user_accounts),
            ("Windows Updates", self.check_windows_updates),
            ("Installed Antivirus", self.detect_installed_antivirus),
            ("External Ports", self.scan_external_ports),
        ]

        for i, (name, func) in enumerate(steps):
            if not self.scan_active:
                break
            self.log(f"Scanning: {name}...")
            if progress_callback:
                progress_callback(i + 1, len(steps), name)
            try:
                results[name] = func()
            except Exception as e:
                results[name] = {"error": str(e)}
                self.log(f"Error in {name}: {e}", "error")

        self.scan_active = False
        return results

    def stop_scan(self):
        self.scan_active = False

    # ─── Third-Party Antivirus Detection ─────────────────────────────

    def detect_installed_antivirus(self):
        """Detect all installed antivirus products via WMI SecurityCenter2."""
        av_products = []

        if platform.system() != "Windows":
            return av_products

        try:
            result = subprocess.run(
                [
                    "powershell",
                    "-Command",
                    "Get-CimInstance -Namespace root/SecurityCenter2 "
                    "-ClassName AntiVirusProduct | "
                    "Select-Object displayName, productState, pathToSignedProductExe | "
                    "Format-List",
                ],
                capture_output=True,
                text=True,
                timeout=15,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if result.returncode == 0 and result.stdout.strip():
                current = {}
                for line in result.stdout.split("\n"):
                    line = line.strip()
                    if not line:
                        if current.get("name"):
                            av_products.append(current)
                        current = {}
                        continue
                    if "displayName" in line:
                        current["name"] = line.split(":", 1)[-1].strip()
                    elif "productState" in line:
                        try:
                            state = int(line.split(":", 1)[-1].strip())
                            # Decode productState bitmask (3-byte hex: XXYYZZ)
                            # XX = product status, YY = scanner state, ZZ = definitions
                            # Scanner byte (bits 8-15): non-zero means enabled
                            # Covers both 0x10 (Defender) and 0x01 (Kaspersky) styles
                            scanner_byte = (state >> 8) & 0xFF
                            enabled = scanner_byte != 0
                            # Definitions byte (bits 0-7): 0x00 = up to date
                            defs_byte = state & 0xFF
                            up_to_date = defs_byte == 0
                            current["enabled"] = enabled
                            current["up_to_date"] = up_to_date
                            current["state_raw"] = state
                        except (ValueError, TypeError):
                            current["enabled"] = None
                            current["up_to_date"] = None
                    elif "pathToSignedProductExe" in line:
                        current["path"] = line.split(":", 1)[-1].strip()
                if current.get("name"):
                    av_products.append(current)
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

        return av_products

    # ─── External Port Scan ──────────────────────────────────────────

    def scan_external_ports(self, port_range=(1, 1024), timeout=0.5):
        """Scan for ports open to external connections (not just localhost)."""
        exposed_ports = []
        well_known = {
            20: "FTP-Data",
            21: "FTP",
            22: "SSH",
            23: "Telnet",
            25: "SMTP",
            53: "DNS",
            80: "HTTP",
            110: "POP3",
            135: "RPC",
            137: "NetBIOS",
            138: "NetBIOS",
            139: "NetBIOS",
            143: "IMAP",
            443: "HTTPS",
            445: "SMB",
            993: "IMAPS",
            995: "POP3S",
            1433: "MSSQL",
            1521: "Oracle",
            3306: "MySQL",
            3389: "RDP",
            5432: "PostgreSQL",
            5900: "VNC",
            6379: "Redis",
            8080: "HTTP-Proxy",
            8443: "HTTPS-Alt",
            27017: "MongoDB",
        }
        risky_ports = {
            23,
            135,
            137,
            138,
            139,
            445,
            3389,
            5900,
            1433,
            3306,
            5432,
            6379,
            27017,
            21,
            22,
            25,
        }

        if not psutil:
            return exposed_ports

        try:
            for conn in psutil.net_connections(kind="inet"):
                if conn.status != "LISTEN":
                    continue
                if not conn.laddr:
                    continue

                port = conn.laddr.port
                addr = conn.laddr.ip

                # Check if listening on all interfaces (0.0.0.0 / ::)
                is_external = addr in ("0.0.0.0", "::", "")
                # Or on a specific non-localhost IP
                if not is_external and addr not in ("127.0.0.1", "::1"):
                    is_external = True

                if not is_external:
                    continue

                proc_name = "N/A"
                if conn.pid:
                    try:
                        proc = psutil.Process(conn.pid)
                        proc_name = proc.name()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                service = well_known.get(port, "Unknown")

                # System-critical ports: mark as SYSTEM risk (not blockable, not a threat)
                if port in self.SYSTEM_CRITICAL_PORTS:
                    risk = "SYSTEM"
                elif port in risky_ports:
                    risk = "HIGH"
                elif port < 1024:
                    risk = "MEDIUM"
                else:
                    risk = "LOW"

                exposed_ports.append(
                    {
                        "port": port,
                        "address": addr,
                        "service": service,
                        "process": proc_name,
                        "pid": conn.pid,
                        "risk": risk,
                        "external": True,
                    }
                )

        except (psutil.AccessDenied, PermissionError):
            self.log("Need Admin to check external ports", "warning")

        # Sort by risk (SYSTEM ports last since they can't be acted on)
        risk_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "SYSTEM": 3}
        exposed_ports.sort(key=lambda x: risk_order.get(x["risk"], 99))
        return exposed_ports

    # ─── Admin Detection & Command Execution ─────────────────────────

    @staticmethod
    def _is_admin():
        """Check if the current process has admin privileges."""
        if platform.system() != "Windows":
            return False
        try:
            import ctypes

            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    def _run_cmd(self, args, timeout=15):
        """Run a command directly. Since the app should be run as admin,
        no elevation dance is needed - just execute.
        Returns (success: bool, stdout: str, stderr: str)."""
        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=timeout,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except FileNotFoundError:
            return False, "", f"Command not found: {args[0]}"
        except OSError as e:
            return False, "", str(e)

    def _run_ps(self, ps_command, timeout=20):
        """Run a PowerShell command directly.
        Returns (success: bool, stdout: str, stderr: str)."""
        return self._run_cmd(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_command],
            timeout=timeout,
        )

    # ─── Auto-Fix Security Issues ────────────────────────────────────

    def fix_enable_firewall(self):
        """Enable all firewall profiles and verify they are actually ON.
        If a third-party security suite (Kaspersky, etc.) manages the firewall,
        reports success since the system is already protected."""
        if platform.system() != "Windows":
            return {"success": False, "error": "Windows only"}

        if not self._is_admin():
            return {"success": False, "error": "Must run as Administrator"}

        # Check if a third-party security suite manages the firewall
        av_products = self.detect_installed_antivirus()
        # Security suites that include their own firewall
        firewall_suites = [
            "kaspersky",
            "norton",
            "bitdefender",
            "eset",
            "mcafee",
            "avast",
            "avg",
            "comodo",
            "zonealarm",
            "f-secure",
            "trend micro",
            "panda",
            "bullguard",
        ]
        third_party_fw = None
        for av in av_products:
            if isinstance(av, dict) and av.get("enabled"):
                name_lower = av.get("name", "").lower()
                if any(suite in name_lower for suite in firewall_suites):
                    third_party_fw = av.get("name", "Unknown")
                    break

        if third_party_fw:
            self.log(
                f"{third_party_fw} manages the firewall - Windows Firewall OFF is normal", "success"
            )
            return {
                "success": True,
                "actions": [f"No action needed: {third_party_fw} manages firewall protection"],
            }

        # No third-party suite - try to enable Windows Firewall
        for profile in ["domainprofile", "privateprofile", "publicprofile"]:
            self._run_cmd(["netsh", "advfirewall", "set", profile, "state", "on"])

        # Also try via PowerShell as backup
        self._run_ps("Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True")

        # VERIFY actual state
        time.sleep(1)
        fw_status = self.check_firewall_status()
        still_off = []
        actions = []
        for profile in ["domain", "private", "public"]:
            if fw_status.get(profile, "").upper() == "ON":
                actions.append(f"Firewall {profile}: ON")
                self.log(f"Firewall {profile} verified ON", "success")
            else:
                still_off.append(profile)

        if still_off:
            self.log(f"Firewall still OFF for: {', '.join(still_off)}", "error")
            return {
                "success": False,
                "actions": actions,
                "error": f"Still OFF: {', '.join(still_off)} - may require Group Policy change",
            }
        return {"success": True, "actions": actions}

    def fix_enable_defender(self):
        """Enable Windows Defender real-time protection.
        Skips if a third-party AV (like Kaspersky) is active. Verifies result."""
        if platform.system() != "Windows":
            return {"success": False, "error": "Windows only"}

        if not self._is_admin():
            return {"success": False, "error": "Must run as Administrator"}

        # Check if third-party AV is active - don't try to enable Defender
        av_products = self.detect_installed_antivirus()
        has_third_party = any(
            isinstance(av, dict)
            and av.get("enabled")
            and "defender" not in av.get("name", "").lower()
            and "windows" not in av.get("name", "").lower()
            for av in av_products
        )
        if has_third_party:
            third_party_name = next(
                (
                    av.get("name", "Unknown")
                    for av in av_products
                    if isinstance(av, dict)
                    and av.get("enabled")
                    and "defender" not in av.get("name", "").lower()
                ),
                "Unknown",
            )
            self.log(f"{third_party_name} is active - Defender off is normal", "success")
            return {
                "success": True,
                "actions": [f"No action needed: {third_party_name} is your active antivirus"],
            }

        # Apply the fix
        ok, out, err = self._run_ps("Set-MpPreference -DisableRealtimeMonitoring $false")
        if not ok:
            self.log(f"PowerShell Set-MpPreference failed: {err[:100]}", "warning")

        # VERIFY actual state
        time.sleep(2)
        defender = self.check_defender_status()
        if defender.get("status") == "Enabled" or defender.get("real_time") == "Enabled":
            self.log("Windows Defender verified as enabled", "success")
            return {
                "success": True,
                "actions": ["Enabled Defender real-time protection (verified)"],
            }

        self.log(
            "Defender could not be enabled - check Windows Security > Tamper Protection", "error"
        )
        return {
            "success": False,
            "error": "Defender still disabled - Tamper Protection or Group Policy may block changes",
        }

    def fix_flush_dns(self):
        """Flush DNS cache and verify it's cleared."""
        if platform.system() != "Windows":
            return {"success": False, "error": "Windows only"}

        ok, out, err = self._run_cmd(["ipconfig", "/flushdns"])
        if not ok:
            return {"success": False, "error": f"ipconfig /flushdns failed: {err[:100]}"}

        # Verify: check DNS cache is smaller after flush
        dns_after = self.analyze_dns_cache()
        susp_after = [d for d in dns_after if d.get("suspicious")]
        if susp_after:
            self.log(f"DNS flushed but {len(susp_after)} suspicious entries reappeared", "warning")
            return {
                "success": True,
                "actions": [f"DNS flushed - {len(susp_after)} entries repopulated (normal)"],
            }
        self.log("DNS cache flushed and clean", "success")
        return {"success": True, "actions": ["DNS cache flushed and verified clean"]}

    def fix_kill_process(self, pid):
        """Kill a suspicious process by PID. Uses multiple methods."""
        if not psutil:
            return {"success": False, "error": "psutil not available"}

        # Get name first
        name = "Unknown"
        try:
            proc = psutil.Process(pid)
            name = proc.name()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

        # Method 1: psutil terminate + kill
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            proc.wait(timeout=3)
            self.log(f"Terminated {name} (PID: {pid})", "success")
            return {"success": True, "actions": [f"Terminated {name} (PID: {pid})"]}
        except psutil.NoSuchProcess:
            return {"success": True, "actions": [f"Process {pid} already terminated"]}
        except (psutil.AccessDenied, psutil.TimeoutExpired):
            pass

        # Method 2: psutil kill (SIGKILL)
        try:
            proc = psutil.Process(pid)
            proc.kill()
            proc.wait(timeout=3)
            self.log(f"Force killed {name} (PID: {pid})", "success")
            return {"success": True, "actions": [f"Force killed {name} (PID: {pid})"]}
        except psutil.NoSuchProcess:
            return {"success": True, "actions": [f"Process {pid} terminated"]}
        except (psutil.AccessDenied, psutil.TimeoutExpired):
            pass

        # Method 3: taskkill /F (Windows admin force kill)
        if platform.system() == "Windows":
            ok, out, err = self._run_cmd(["taskkill", "/F", "/PID", str(pid)])
            if ok:
                self.log(f"taskkill force killed {name} (PID: {pid})", "success")
                return {
                    "success": True,
                    "actions": [f"Force killed {name} (PID: {pid}) via taskkill"],
                }

            # Method 4: wmic (last resort)
            ok, out, err = self._run_cmd(["wmic", "process", "where", f"ProcessId={pid}", "delete"])
            if ok:
                self.log(f"wmic killed {name} (PID: {pid})", "success")
                return {"success": True, "actions": [f"Killed {name} (PID: {pid}) via wmic"]}

        # Verify if it's actually gone
        try:
            psutil.Process(pid)
            # Still alive
            self.log(f"Could not kill {name} (PID: {pid}) - protected process", "error")
            return {
                "success": False,
                "error": f"Cannot kill {name} (PID: {pid}) - protected system process",
            }
        except psutil.NoSuchProcess:
            # It's dead
            return {"success": True, "actions": [f"Terminated {name} (PID: {pid})"]}

    def fix_disable_task(self, task_name):
        """Disable a suspicious scheduled task and verify."""
        if platform.system() != "Windows":
            return {"success": False, "error": "Windows only"}

        if not self._is_admin():
            return {"success": False, "error": "Must run as Administrator"}

        ok, out, err = self._run_cmd(["schtasks", "/change", "/tn", task_name, "/disable"])
        if ok:
            self.log(f"Disabled task: {task_name}", "success")
            return {"success": True, "actions": [f"Disabled task: {task_name}"]}

        # Try via PowerShell
        ok2, out2, err2 = self._run_ps(
            f"Disable-ScheduledTask -TaskName '{task_name}' -ErrorAction SilentlyContinue"
        )
        if ok2:
            self.log(f"Disabled task via PowerShell: {task_name}", "success")
            return {"success": True, "actions": [f"Disabled task: {task_name}"]}

        return {"success": False, "error": f"Failed to disable: {err[:100]}"}

    def fix_close_risky_shares(self):
        """Remove non-default network shares."""
        if platform.system() != "Windows":
            return {"success": False, "error": "Windows only"}

        default_shares = {"C$", "D$", "E$", "ADMIN$", "IPC$", "print$"}
        shares = self.check_shared_resources()
        removed = []
        for share in shares:
            name = share["name"]
            if name not in default_shares:
                try:
                    subprocess.run(
                        ["net", "share", f"{name}", "/delete", "/yes"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                    )
                    removed.append(name)
                    self.log(f"Removed share: {name}", "success")
                except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                    pass

        return {
            "success": True,
            "actions": [f"Removed {len(removed)} shares"]
            if removed
            else ["No non-default shares to remove"],
        }

    def fix_flush_arp(self):
        """Flush ARP cache and verify no spoofing remains."""
        if platform.system() != "Windows":
            return {"success": False, "error": "Windows only"}

        # Try netsh first
        ok1, _, _ = self._run_cmd(["netsh", "interface", "ip", "delete", "arpcache"])
        # Also try arp -d
        ok2, _, _ = self._run_cmd(["arp", "-d", "*"])

        if not ok1 and not ok2:
            return {"success": False, "error": "Could not flush ARP cache - run as Administrator"}

        # VERIFY: wait for ARP to repopulate then check
        time.sleep(3)
        arp_entries = self.analyze_arp_table()
        spoofing = [e for e in arp_entries if e.get("spoofing_risk")]

        if spoofing:
            self.log(
                "ARP flushed but gateway spoofing persists - possible active MITM attack", "warning"
            )
            return {
                "success": False,
                "error": "Gateway MAC spoofing persists - possible active network attack",
                "actions": ["ARP flushed but spoofing redetected"],
            }

        self.log("ARP cache flushed and verified clean", "success")
        return {"success": True, "actions": ["ARP cache flushed - no spoofing detected"]}

    def is_port_critical(self, port):
        """Check if a port is a system-critical port that should not be blocked."""
        return int(port) in self.SYSTEM_CRITICAL_PORTS

    def get_port_critical_reason(self, port):
        """Get the reason why a port is critical."""
        return self.SYSTEM_CRITICAL_PORTS.get(int(port), "")

    def fix_block_port(self, port):
        """Block an exposed port: add firewall rule + kill the process using it.
        Refuses to block system-critical ports. Verifies result."""
        if platform.system() != "Windows":
            return {"success": False, "error": "Windows only"}

        try:
            port = int(port)
        except (ValueError, TypeError):
            return {"success": False, "error": "Invalid port number"}

        # SAFETY: refuse to block critical system ports
        if port in self.SYSTEM_CRITICAL_PORTS:
            reason = self.SYSTEM_CRITICAL_PORTS[port]
            self.log(f"BLOCKED: port {port} is a system-critical port ({reason})", "error")
            return {"success": False, "error": f"Cannot block port {port}: {reason}"}

        actions = []

        # Step 1: Find and kill the process using this port
        if psutil:
            try:
                for conn in psutil.net_connections(kind="inet"):
                    if conn.status == "LISTEN" and conn.laddr and conn.laddr.port == port:
                        if conn.pid:
                            try:
                                proc = psutil.Process(conn.pid)
                                proc_name = proc.name()
                                proc.terminate()
                                try:
                                    proc.wait(timeout=3)
                                except psutil.TimeoutExpired:
                                    proc.kill()
                                actions.append(
                                    f"Killed {proc_name} (PID:{conn.pid}) on port {port}"
                                )
                                self.log(f"Killed {proc_name} on port {port}", "success")
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                # Try taskkill
                                ok, _, _ = self._run_cmd(["taskkill", "/F", "/PID", str(conn.pid)])
                                if ok:
                                    actions.append(f"Force killed PID:{conn.pid} on port {port}")
                            break
            except (psutil.AccessDenied, PermissionError):
                pass

        # Step 2: Add firewall rule to block inbound
        rule_name = f"WinSvalinn_Block_{port}"
        ok, out, err = self._run_cmd(
            [
                "netsh",
                "advfirewall",
                "firewall",
                "add",
                "rule",
                f"name={rule_name}",
                "dir=in",
                "action=block",
                "protocol=TCP",
                f"localport={port}",
            ]
        )
        if ok:
            actions.append(f"Firewall rule added: block TCP {port} inbound")
        else:
            self.log(f"Failed to add firewall rule: {err[:80]}", "warning")

        # Also block outbound
        ok2, _, _ = self._run_cmd(
            [
                "netsh",
                "advfirewall",
                "firewall",
                "add",
                "rule",
                f"name={rule_name}_out",
                "dir=out",
                "action=block",
                "protocol=TCP",
                f"localport={port}",
            ]
        )
        if ok2:
            actions.append(f"Firewall rule added: block TCP {port} outbound")

        # Step 3: VERIFY port is no longer listening
        time.sleep(1)
        still_open = False
        if psutil:
            try:
                for conn in psutil.net_connections(kind="inet"):
                    if conn.status == "LISTEN" and conn.laddr and conn.laddr.port == port:
                        still_open = True
                        break
            except (psutil.AccessDenied, PermissionError):
                pass

        if still_open:
            actions.append(f"Warning: port {port} still listening (service restarted)")
            return {
                "success": len(actions) > 1,
                "actions": actions,
                "error": f"Port {port} still open - service may auto-restart",
            }

        self.log(f"Port {port} blocked and verified closed", "success")
        return {"success": True, "actions": actions}

    # ─── Antivirus Configuration Reader ──────────────────────────────

    def check_av_configuration(self):
        """Read the configuration of the active third-party antivirus (Kaspersky, etc.).
        Returns a dict with component statuses read from registry/WMI."""
        if platform.system() != "Windows":
            return {}

        av_products = self.detect_installed_antivirus()
        third_party = [
            av
            for av in av_products
            if isinstance(av, dict)
            and av.get("enabled")
            and "defender" not in av.get("name", "").lower()
            and "windows" not in av.get("name", "").lower()
        ]

        if not third_party:
            return {}

        av_name = third_party[0].get("name", "Unknown")
        av_name_lower = av_name.lower()
        config = {"av_name": av_name, "components": []}

        # ─── Kaspersky ──────────────────────────────────────────
        if "kaspersky" in av_name_lower:
            # Kaspersky stores settings in various registry locations
            # Try reading Kaspersky settings via PowerShell registry query
            ps_script = (
                "try {\n"
                "  $base = Get-ChildItem 'HKLM:\\SOFTWARE\\KasperskyLab' -Recurse -ErrorAction SilentlyContinue | "
                "Where-Object { $_.Name -match 'AVP|KES|PURE|KIS|KAV' } | Select-Object -First 1;\n"
                '  if ($base) { Write-Output "KASP_PATH=$($base.Name)" }\n'
                "} catch {}\n"
                # Check if Kaspersky services are running
                "Get-Service -Name 'AVP*','kavsvc*','klnagent*' -ErrorAction SilentlyContinue | "
                'ForEach-Object { Write-Output "SVC=$($_.Name)|$($_.Status)" }\n'
                # Check WMI for firewall product
                "try {\n"
                "  Get-CimInstance -Namespace root/SecurityCenter2 -ClassName FirewallProduct "
                "-ErrorAction SilentlyContinue | "
                'ForEach-Object { Write-Output "FW=$($_.displayName)|$($_.productState)" }\n'
                "} catch {}\n"
            )
            ok, out, _ = self._run_ps(ps_script, timeout=15)
            if ok and out:
                for line in out.strip().split("\n"):
                    line = line.strip()
                    if line.startswith("SVC="):
                        parts = line[4:].split("|", 1)
                        svc_name = parts[0] if parts else ""
                        svc_status = parts[1] if len(parts) > 1 else "Unknown"
                        friendly = svc_name
                        if "avp" in svc_name.lower():
                            friendly = "Kaspersky Protection Service"
                        elif "klnagent" in svc_name.lower():
                            friendly = "Kaspersky Network Agent"
                        config["components"].append(
                            {
                                "name": friendly,
                                "status": svc_status.strip(),
                                "enabled": "running" in svc_status.lower(),
                            }
                        )
                    elif line.startswith("FW="):
                        parts = line[3:].split("|", 1)
                        fw_name = parts[0] if parts else ""
                        config["components"].append(
                            {"name": f"Firewall ({fw_name})", "status": "Active", "enabled": True}
                        )

            # Also check for Kaspersky-specific components via the process list
            if psutil:
                kasp_procs = {
                    "avp.exe": "Kaspersky Real-time Protection",
                    "avpui.exe": "Kaspersky UI",
                    "klnagent.exe": "Kaspersky Network Agent",
                    "ksde.exe": "Kaspersky Secure Connection (VPN)",
                    "ksdeui.exe": "Kaspersky VPN UI",
                }
                found_procs = set()
                try:
                    for proc in psutil.process_iter(["name"]):
                        pname = (proc.info["name"] or "").lower()
                        if pname in kasp_procs and pname not in found_procs:
                            found_procs.add(pname)
                            config["components"].append(
                                {"name": kasp_procs[pname], "status": "Running", "enabled": True}
                            )
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    pass

                # Detect if Kaspersky web protection is running (by listening ports)
                try:
                    for conn in psutil.net_connections(kind="inet"):
                        if conn.status == "LISTEN" and conn.laddr:
                            if conn.laddr.port in (1110, 1111, 2080, 2081):
                                config["components"].append(
                                    {
                                        "name": "Web Protection (proxy)",
                                        "status": f"Listening on port {conn.laddr.port}",
                                        "enabled": True,
                                    }
                                )
                                break
                except (psutil.AccessDenied, PermissionError):
                    pass

        # ─── Generic AV (Norton, Bitdefender, ESET, etc.) ──────
        else:
            # Check services related to this AV
            brand_keywords = []
            if "norton" in av_name_lower or "symantec" in av_name_lower:
                brand_keywords = ["norton", "symantec", "nsservice", "ccsvchst"]
            elif "bitdefender" in av_name_lower:
                brand_keywords = ["bitdefender", "bdagent", "vsserv", "updatesrv"]
            elif "eset" in av_name_lower or "nod32" in av_name_lower:
                brand_keywords = ["eset", "ekrn", "egui"]
            elif "avast" in av_name_lower:
                brand_keywords = ["avast", "avastsvc"]
            elif "avg" in av_name_lower:
                brand_keywords = ["avg", "avgsvc"]
            elif "mcafee" in av_name_lower:
                brand_keywords = ["mcafee", "mfemms", "mfefire"]
            else:
                # Derive from the AV name
                brand_keywords = [av_name_lower.split()[0]]

            if brand_keywords:
                kw_filter = " -or ".join(f"$_.Name -like '*{kw}*'" for kw in brand_keywords)
                ps_cmd = (
                    f"Get-Service | Where-Object {{ {kw_filter} }} | "
                    'ForEach-Object { Write-Output "SVC=$($_.DisplayName)|$($_.Status)" }'
                )
                ok, out, _ = self._run_ps(ps_cmd, timeout=10)
                if ok and out:
                    for line in out.strip().split("\n"):
                        line = line.strip()
                        if line.startswith("SVC="):
                            parts = line[4:].split("|", 1)
                            svc_name = parts[0] if parts else ""
                            svc_status = parts[1] if len(parts) > 1 else "Unknown"
                            config["components"].append(
                                {
                                    "name": svc_name,
                                    "status": svc_status.strip(),
                                    "enabled": "running" in svc_status.lower(),
                                }
                            )

            # Check WMI FirewallProduct
            ok, out, _ = self._run_ps(
                "try { Get-CimInstance -Namespace root/SecurityCenter2 "
                "-ClassName FirewallProduct -ErrorAction SilentlyContinue | "
                'ForEach-Object { Write-Output "FW=$($_.displayName)" } } catch {}',
                timeout=10,
            )
            if ok and out:
                for line in out.strip().split("\n"):
                    if line.strip().startswith("FW="):
                        fw_name = line.strip()[3:]
                        if any(kw in fw_name.lower() for kw in brand_keywords):
                            config["components"].append(
                                {
                                    "name": f"Firewall ({fw_name})",
                                    "status": "Active",
                                    "enabled": True,
                                }
                            )

        # Remove duplicates by component name
        seen = set()
        unique = []
        for comp in config["components"]:
            if comp["name"] not in seen:
                seen.add(comp["name"])
                unique.append(comp)
        config["components"] = unique

        return config

    # ─── Startup Program Classification ──────────────────────────────

    # Well-known Windows system startup entries (essential, do not disable)
    SYSTEM_STARTUP_NAMES = {
        "securityhealthsystray",
        "windowsdefender",
        "windows defender notification",
        "securityhealth",
        "ctfmon",
        "msascuil",
        "vmware-tray",
        "igfxtray",
        "hkcmd",
        "hotkeyscmds",
        "persistencethread",
        "sihost",
        "windows security notification",
        "windows security",
    }

    # Keywords indicating hardware drivers
    DRIVER_KEYWORDS = [
        "nvidia",
        "geforce",
        "realtek",
        "intel",
        "amd",
        "radeon",
        "synaptics",
        "logitech",
        "corsair",
        "razer",
        "steelseries",
        "hyperx",
        "nahimic",
        "dolby",
        "waves",
        "maxx",
        "bang & olufsen",
        "conexant",
        "creative",
        "sound blaster",
        "asus",
        "msi",
        "gigabyte",
        "evga",
        "wacom",
        "brother",
        "canon",
        "epson",
        "hp",
        "qualcomm",
        "broadcom",
        "killer",
        "rivet",
        "dell",
        "lenovo",
        "toshiba",
        "acer",
        "samsung",
        "displaylink",
    ]

    def classify_startup_program(self, item):
        """Classify a startup program as 'system', 'driver', or 'external'.

        Returns:
            tuple: (type_key, can_disable)
                type_key: 'system' | 'driver' | 'external'
                can_disable: bool
        """
        name = (item.get("name", "") or "").lower().strip()
        value = (item.get("value", "") or "").lower().strip()
        combined = name + " " + value

        # Check system
        if name in self.SYSTEM_STARTUP_NAMES:
            return "system", False

        # Check known Windows system paths
        system_paths = ["\\windows\\system32\\", "\\windows\\syswow64\\", "\\windows\\security\\"]
        if any(sp in value for sp in system_paths):
            # Could be system or driver — check further
            if any(kw in combined for kw in self.DRIVER_KEYWORDS):
                return "driver", True  # driver can be disabled but with warning
            return "system", False

        # Check drivers
        if any(kw in combined for kw in self.DRIVER_KEYWORDS):
            return "driver", True

        # Everything else is external
        return "external", True

    # ─── Boot Speed Tweaks ───────────────────────────────────────────

    def apply_boot_tweak(self, tweak_key):
        """Apply a boot speed tweak. Returns dict with success/actions/error."""
        if platform.system() != "Windows":
            return {"success": False, "error": "Windows only"}

        tweaks = {
            "boot_timeout": {
                "commands": [
                    (
                        ["bcdedit", "/set", "{current}", "timeout", "3"],
                        "Reduced boot timeout to 3 seconds",
                    ),
                ],
            },
            "fast_startup": {
                "commands": [
                    (
                        ["powercfg", "/hibernate", "on"],
                        "Enabled hibernation (required for Fast Startup)",
                    ),
                    (
                        [
                            "reg",
                            "add",
                            r"HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Power",
                            "/v",
                            "HiberbootEnabled",
                            "/t",
                            "REG_DWORD",
                            "/d",
                            "1",
                            "/f",
                        ],
                        "Enabled Fast Startup (hybrid shutdown)",
                    ),
                ],
            },
            "disable_boot_log": {
                "commands": [
                    (["bcdedit", "/set", "{current}", "bootlog", "no"], "Disabled boot logging"),
                ],
            },
            "optimize_prefetch": {
                "commands": [
                    (
                        [
                            "reg",
                            "add",
                            r"HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters",
                            "/v",
                            "EnablePrefetcher",
                            "/t",
                            "REG_DWORD",
                            "/d",
                            "3",
                            "/f",
                        ],
                        "Set Prefetch to optimize boot + applications",
                    ),
                    (
                        [
                            "reg",
                            "add",
                            r"HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters",
                            "/v",
                            "EnableSuperfetch",
                            "/t",
                            "REG_DWORD",
                            "/d",
                            "3",
                            "/f",
                        ],
                        "Set Superfetch to full optimization",
                    ),
                ],
            },
        }

        tweak = tweaks.get(tweak_key)
        if not tweak:
            return {"success": False, "error": f"Unknown tweak: {tweak_key}"}

        actions = []
        errors = []
        for cmd_args, description in tweak["commands"]:
            ok, out, err = self._run_cmd(cmd_args, timeout=15)
            if ok:
                actions.append(description)
                self.log(f"  Boot tweak: {description}", "success")
            else:
                errors.append(f"{description}: {err[:60]}")
                self.log(f"  Boot tweak failed: {description} — {err[:60]}", "warning")

        if actions:
            return {"success": True, "actions": actions}
        return {
            "success": False,
            "error": "; ".join(errors) if errors else "No actions applied",
            "actions": actions,
        }
