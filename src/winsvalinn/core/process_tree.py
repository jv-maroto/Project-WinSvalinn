"""
Process tree builder.

Constructs a parent-child tree of running processes (psutil) and computes a
SHA-256 of each process's executable for downstream lookups (VirusTotal, etc.).
Pure backend module — no GUI imports.
"""

import hashlib
import os

try:
    import psutil
except ImportError:
    psutil = None


def _safe_info(proc):
    """Read process info safely; some attrs raise on access.

    Only the fields the UI actually renders are collected. Notably we skip
    ``username()`` (resolves the SID via LookupAccountSid — very slow on Windows)
    and other unused attrs, which made the tree take seconds to build.
    """
    try:
        with proc.oneshot():
            return {
                "pid": proc.pid,
                "ppid": proc.ppid(),
                "name": proc.name(),
                "exe": proc.exe() if hasattr(proc, "exe") else "",
                "memory_mb": proc.memory_info().rss / (1024 * 1024),
            }
    except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
        return None


def build_process_tree() -> list[dict]:
    """
    Return a list of root nodes; each node has:
        pid, ppid, name, exe, username, cpu_percent, memory_mb, status,
        create_time, children: [...]
    """
    if psutil is None:
        return []

    nodes: dict[int, dict] = {}
    for proc in psutil.process_iter():
        info = _safe_info(proc)
        if info is None:
            continue
        info["children"] = []
        nodes[info["pid"]] = info

    roots: list[dict] = []
    for pid, info in nodes.items():
        ppid = info["ppid"]
        if ppid in nodes and ppid != pid:
            nodes[ppid]["children"].append(info)
        else:
            roots.append(info)

    # Sort children by name within each node
    def _sort(node):
        node["children"].sort(key=lambda c: (c["name"] or "").lower())
        for c in node["children"]:
            _sort(c)

    for r in roots:
        _sort(r)

    roots.sort(key=lambda c: (c["name"] or "").lower())
    return roots


def hash_executable(path: str, max_bytes: int = 64 * 1024 * 1024) -> str | None:
    """
    SHA-256 of the executable on disk. Caps at 64MB by default to avoid
    pinning huge installers; returns None if path is empty/inaccessible.
    """
    if not path or not os.path.isfile(path):
        return None
    try:
        h = hashlib.sha256()
        read = 0
        with open(path, "rb") as f:
            while True:
                chunk = f.read(1024 * 1024)
                if not chunk:
                    break
                read += len(chunk)
                if read > max_bytes:
                    return None
                h.update(chunk)
        return h.hexdigest()
    except (OSError, PermissionError):
        return None


def flatten(node: dict, depth: int = 0):
    """Yield (depth, node) pairs in a depth-first walk."""
    yield depth, node
    for c in node.get("children", []):
        yield from flatten(c, depth + 1)
