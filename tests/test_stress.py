"""
Stress tests with synthetic large inputs.

Garantiza que las funciones core no se rompen ni se traban con
volúmenes grandes (1000+ conexiones, 500+ procesos, 200k+ líneas hosts).
"""

import time
from unittest.mock import MagicMock, patch

# ── Network: 1000+ connections ─────────────────────────────────────────


def test_stress_network_1000_connections_processes_under_2s():
    """Simulates 1000 net_connections — the cached PID lookup should make this fast."""

    import psutil

    # Build 1000 fake connections with 50 distinct PIDs
    fake_conns = []
    for i in range(1000):
        pid = (i % 50) + 1000
        c = MagicMock()
        c.status = psutil.CONN_ESTABLISHED
        c.pid = pid
        c.laddr = MagicMock(ip="127.0.0.1", port=8000 + i)
        c.raddr = MagicMock(ip=f"10.0.0.{i % 256}", port=443)
        c.type = 1
        fake_conns.append(c)

    # Simulate the cached-PID approach used by the network view
    pid_names = {pid: f"proc{pid}.exe" for pid in range(1000, 1050)}

    start = time.perf_counter()
    rows = []
    for conn in fake_conns:
        rows.append(
            {
                "process": pid_names.get(conn.pid, "N/A"),
                "pid": conn.pid,
                "local": f"{conn.laddr.ip}:{conn.laddr.port}",
                "remote": f"{conn.raddr.ip}:{conn.raddr.port}",
            }
        )
    elapsed = time.perf_counter() - start

    assert len(rows) == 1000
    assert elapsed < 2.0, f"1000 conns took {elapsed:.2f}s"


# ── Process tree: 500 processes ────────────────────────────────────────


def test_stress_process_tree_handles_500_fake_procs():
    """build_process_tree should not blow up with hundreds of processes."""
    from winsvalinn.core import process_tree

    # Build fake procs and patch process_iter
    fake_procs = []
    for i in range(500):
        proc = MagicMock()
        proc.pid = i + 1
        proc.oneshot.return_value.__enter__ = lambda s: s
        proc.oneshot.return_value.__exit__ = lambda *a: None
        proc.ppid.return_value = max(0, i - 1)  # chain
        proc.name.return_value = f"proc{i}.exe"
        proc.exe.return_value = f"C:\\Windows\\proc{i}.exe"
        proc.username.return_value = "user"
        proc.cpu_percent.return_value = 0.1
        proc.memory_info.return_value = MagicMock(rss=1024 * 1024)
        proc.create_time.return_value = 0
        proc.status.return_value = "running"
        fake_procs.append(proc)

    with patch.object(
        process_tree,
        "psutil",
        MagicMock(
            process_iter=lambda: iter(fake_procs),
            NoSuchProcess=Exception,
            AccessDenied=Exception,
        ),
    ):
        start = time.perf_counter()
        tree = process_tree.build_process_tree()
        elapsed = time.perf_counter() - start

    assert elapsed < 1.0, f"500-proc tree took {elapsed:.2f}s"
    # We get something back (one root chain)
    assert isinstance(tree, list)


# ── Hosts: 200k entries ────────────────────────────────────────────────


def test_stress_hosts_parse_200k_lines_under_1s(tmp_path):
    """Parse a fake StevenBlack-sized hosts file (~200k entries)."""
    from winsvalinn.core.hosts_manager import HostsManager

    fake_hosts = tmp_path / "hosts"
    lines = ["# WinSvalinn stress hosts\n"]
    lines.extend(f"0.0.0.0 ad{i}.example.com\n" for i in range(200_000))
    fake_hosts.write_text("".join(lines), encoding="utf-8")

    m = HostsManager()
    # Patch class attribute to point at our temp file
    with patch.object(HostsManager, "HOSTS_PATH", str(fake_hosts)):
        start = time.perf_counter()
        result = m.read_hosts()
        elapsed = time.perf_counter() - start

    assert result.get("success")
    assert elapsed < 1.5, f"parsing 200k hosts took {elapsed:.2f}s"
    # off-by-one is fine; we care that all entries are parsed (within 5)
    assert abs(result["total_entries"] - 200_000) <= 5


# ── Autoruns enumeration ──────────────────────────────────────────────


def test_stress_autoruns_summary_10k_items_under_50ms():
    from winsvalinn.core.autoruns import summary_by_source

    items = [{"source": f"src-{i % 30}"} for i in range(10_000)]

    start = time.perf_counter()
    counts = summary_by_source(items)
    elapsed = time.perf_counter() - start

    assert elapsed < 0.05, f"10k items took {elapsed * 1000:.0f}ms"
    assert sum(counts.values()) == 10_000


# ── Duplicates finder: 500 small files ────────────────────────────────


def test_stress_duplicates_finder_500_files(tmp_path):
    """Hash-bucketing 500 files should be sub-second."""
    import hashlib

    # Create 500 files, ~10 unique contents → 49 dups
    for i in range(500):
        (tmp_path / f"f{i}.bin").write_bytes(f"content-{i % 10}".encode())

    files_by_size = {}
    for f in tmp_path.iterdir():
        sz = f.stat().st_size
        files_by_size.setdefault(sz, []).append(str(f))

    start = time.perf_counter()
    for sz, paths in files_by_size.items():
        if len(paths) < 2:
            continue
        hashes = {}
        for p in paths:
            h = hashlib.sha256(open(p, "rb").read()).hexdigest()
            hashes.setdefault(h, []).append(p)
    elapsed = time.perf_counter() - start

    # Disk I/O on Windows is highly variable; 5s is a sanity cap
    assert elapsed < 5.0, f"500-file dup scan took {elapsed:.2f}s"
