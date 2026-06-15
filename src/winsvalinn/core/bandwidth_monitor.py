"""
Bandwidth Monitor for WinSvalinn.

Monitors network usage per interface and per process,
detects unusual traffic patterns.
"""

import platform
import time

from winsvalinn.utils.logger import ModuleLogger

logger = ModuleLogger("BandwidthMonitor")

IS_WINDOWS = platform.system() == "Windows"


class BandwidthMonitor:
    """Monitor network bandwidth usage."""

    def __init__(self, callback=None):
        self._callback = callback or (lambda msg, level="info": None)

    def _log(self, msg, level="info"):
        getattr(logger, level, logger.info)(msg)
        self._callback(msg, level)

    def get_current_usage(self):
        """
        Get current network usage per interface.

        Returns:
            dict: {interfaces: list[dict], total_sent_mb, total_recv_mb}
        """
        try:
            import psutil

            counters = psutil.net_io_counters(pernic=True)
            total = psutil.net_io_counters()

            interfaces = []
            for name, stats in counters.items():
                sent_mb = round(stats.bytes_sent / (1024**2), 1)
                recv_mb = round(stats.bytes_recv / (1024**2), 1)
                if sent_mb > 0 or recv_mb > 0:
                    interfaces.append(
                        {
                            "name": name,
                            "sent_mb": sent_mb,
                            "recv_mb": recv_mb,
                            "packets_sent": stats.packets_sent,
                            "packets_recv": stats.packets_recv,
                            "errors_in": stats.errin,
                            "errors_out": stats.errout,
                            "drops_in": stats.dropin,
                            "drops_out": stats.dropout,
                        }
                    )

            interfaces.sort(key=lambda x: x["sent_mb"] + x["recv_mb"], reverse=True)

            return {
                "interfaces": interfaces,
                "total_sent_mb": round(total.bytes_sent / (1024**2), 1),
                "total_recv_mb": round(total.bytes_recv / (1024**2), 1),
                "total_packets_sent": total.packets_sent,
                "total_packets_recv": total.packets_recv,
            }
        except ImportError:
            return {"interfaces": [], "total_sent_mb": 0, "total_recv_mb": 0}

    def get_per_process_connections(self):
        """
        Get network connections grouped by process.

        Returns:
            list[dict]: {process, pid, connections, remote_addrs}
        """
        try:
            import psutil

            proc_map = {}
            for conn in psutil.net_connections(kind="inet"):
                pid = conn.pid
                if not pid:
                    continue

                if pid not in proc_map:
                    try:
                        proc = psutil.Process(pid)
                        proc_map[pid] = {
                            "process": proc.name(),
                            "pid": pid,
                            "connections": 0,
                            "established": 0,
                            "remote_addrs": set(),
                        }
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        proc_map[pid] = {
                            "process": f"PID {pid}",
                            "pid": pid,
                            "connections": 0,
                            "established": 0,
                            "remote_addrs": set(),
                        }

                proc_map[pid]["connections"] += 1
                if conn.status == "ESTABLISHED":
                    proc_map[pid]["established"] += 1
                if conn.raddr:
                    proc_map[pid]["remote_addrs"].add(conn.raddr.ip)

            results = []
            for pid, info in proc_map.items():
                info["remote_addrs"] = list(info["remote_addrs"])[:10]
                results.append(info)

            results.sort(key=lambda x: x["connections"], reverse=True)
            return results

        except ImportError:
            return []

    def get_top_consumers(self, duration=5):
        """
        Sample network usage over a duration to find top bandwidth consumers.

        Args:
            duration: Sampling duration in seconds

        Returns:
            list[dict]: {process, pid, sent_bytes, recv_bytes}
        """
        try:
            import psutil

            self._log(f"Sampling network usage for {duration}s...")

            # Snapshot connections before
            before = {}
            for conn in psutil.net_connections(kind="inet"):
                if conn.pid and conn.status == "ESTABLISHED":
                    before[conn.pid] = before.get(conn.pid, 0) + 1

            # Get IO counters before
            io_before = psutil.net_io_counters()

            time.sleep(duration)

            # Get IO counters after
            io_after = psutil.net_io_counters()

            total_sent = io_after.bytes_sent - io_before.bytes_sent
            total_recv = io_after.bytes_recv - io_before.bytes_recv

            # Get current connections with process info
            consumers = {}
            for conn in psutil.net_connections(kind="inet"):
                pid = conn.pid
                if not pid or conn.status != "ESTABLISHED":
                    continue

                if pid not in consumers:
                    try:
                        proc = psutil.Process(pid)
                        consumers[pid] = {
                            "process": proc.name(),
                            "pid": pid,
                            "connections": 0,
                        }
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

                consumers[pid]["connections"] += 1

            # Estimate per-process based on connection count ratio
            total_conns = sum(c["connections"] for c in consumers.values()) or 1
            results = []
            for pid, info in consumers.items():
                ratio = info["connections"] / total_conns
                info["est_sent_bytes"] = int(total_sent * ratio)
                info["est_recv_bytes"] = int(total_recv * ratio)
                info["est_sent_kb"] = round(info["est_sent_bytes"] / 1024, 1)
                info["est_recv_kb"] = round(info["est_recv_bytes"] / 1024, 1)
                results.append(info)

            results.sort(key=lambda x: x["est_sent_bytes"] + x["est_recv_bytes"], reverse=True)

            self._log(
                f"Sampled: {total_sent / 1024:.1f} KB sent, {total_recv / 1024:.1f} KB recv in {duration}s"
            )
            return results[:15]

        except ImportError:
            return []

    def detect_unusual_traffic(self):
        """
        Detect processes with unusually high network activity.

        Returns:
            list[dict]: Processes with suspicious network behavior
        """
        try:
            import psutil

            self._log("Detecting unusual network traffic...")

            suspicious = []
            for conn in psutil.net_connections(kind="inet"):
                if not conn.pid or conn.status != "ESTABLISHED":
                    continue

                if not conn.raddr:
                    continue

                remote_ip = conn.raddr.ip
                remote_port = conn.raddr.port

                # Skip common safe destinations
                if remote_ip.startswith(("10.", "192.168.", "172.16.", "127.")):
                    continue

                # Suspicious: non-standard ports for unknown processes
                suspicious_ports = {4444, 5555, 6666, 7777, 8888, 9999, 1337, 31337}
                if remote_port in suspicious_ports:
                    try:
                        proc = psutil.Process(conn.pid)
                        suspicious.append(
                            {
                                "process": proc.name(),
                                "pid": conn.pid,
                                "remote": f"{remote_ip}:{remote_port}",
                                "reason": f"Connection to suspicious port {remote_port}",
                                "risk": "HIGH",
                            }
                        )
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

            if suspicious:
                self._log(f"Found {len(suspicious)} suspicious connections", "warning")
            else:
                self._log("No unusual traffic detected")

            return suspicious

        except ImportError:
            return []

    def get_summary(self):
        """
        Network bandwidth summary.

        Returns:
            dict: {total_sent, total_recv, active_connections, interfaces}
        """
        usage = self.get_current_usage()
        procs = self.get_per_process_connections()

        total_connections = sum(p["connections"] for p in procs)
        established = sum(p["established"] for p in procs)

        return {
            "total_sent_mb": usage.get("total_sent_mb", 0),
            "total_recv_mb": usage.get("total_recv_mb", 0),
            "active_interfaces": len(usage.get("interfaces", [])),
            "total_connections": total_connections,
            "established_connections": established,
            "processes_with_network": len(procs),
        }
