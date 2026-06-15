"""
Duplicate file finder — locate identical files by size + SHA-256 hash.

Migrated from the legacy ``plugin_duplicates_finder`` plugin. No GUI imports
and no system mutation: it only reads files. Hashing is two-phase (bucket by
size, then hash collisions) to avoid hashing unique files. Read-only and safe.
"""

from __future__ import annotations

import hashlib
from collections import defaultdict
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

DEFAULT_MAX_BYTES = 256 * 1024 * 1024  # 256 MB per-file cap
_CHUNK = 1024 * 1024


def hash_file(path: Path, max_bytes: int = DEFAULT_MAX_BYTES) -> str | None:
    """Return the SHA-256 of ``path`` or None (too large / unreadable)."""
    try:
        if path.stat().st_size > max_bytes:
            return None
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(_CHUNK), b""):
                h.update(chunk)
        return h.hexdigest()
    except (OSError, PermissionError):
        return None


class DuplicateFinder:
    """Find duplicate files under a folder by content hash. Read-only."""

    def __init__(self, callback: Callable[[str, str], None] | None = None) -> None:
        self.callback = callback or (lambda msg, level="info": None)

    def log(self, message: str, level: str = "info") -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.callback(f"[{timestamp}] {message}", level)

    def find_duplicates(
        self,
        folder: str | Path,
        min_mb: float = 1.0,
        max_bytes: int = DEFAULT_MAX_BYTES,
    ) -> dict:
        """
        Scan ``folder`` and return duplicate groups.

        Returns {"success", "scanned", "groups": [{"size_bytes","hash",
        "paths","waste_bytes"}], "total_waste_bytes"}.
        """
        base = Path(folder)
        if not base.is_dir():
            self.log(f"Carpeta no válida: {folder}", "error")
            return {"success": False, "scanned": 0, "groups": [], "total_waste_bytes": 0}

        min_bytes = int(max(min_mb, 0) * 1024 * 1024)

        # Phase 1: bucket candidate files by size.
        by_size: dict[int, list[Path]] = defaultdict(list)
        scanned = 0
        for child in base.rglob("*"):
            try:
                if not child.is_file():
                    continue
                size = child.stat().st_size
            except (OSError, PermissionError):
                continue
            if size < min_bytes:
                continue
            by_size[size].append(child)
            scanned += 1
            if scanned % 200 == 0:
                self.log(f"Escaneados {scanned} archivos…", "info")

        # Phase 2: hash only files whose size collides.
        groups: list[dict] = []
        total_waste = 0
        for size, paths in by_size.items():
            if len(paths) < 2:
                continue
            hashes: dict[str, list[Path]] = defaultdict(list)
            for p in paths:
                digest = hash_file(p, max_bytes=max_bytes)
                if digest:
                    hashes[digest].append(p)
            for digest, group in hashes.items():
                if len(group) > 1:
                    waste = size * (len(group) - 1)
                    total_waste += waste
                    groups.append(
                        {
                            "size_bytes": size,
                            "hash": digest,
                            "paths": [str(p) for p in group],
                            "waste_bytes": waste,
                        }
                    )

        groups.sort(key=lambda g: -g["size_bytes"])
        self.log(
            f"Hecho. {scanned} archivos, {len(groups)} grupos duplicados, "
            f"{total_waste / 1024 / 1024:.1f} MB recuperables.",
            "success",
        )
        return {
            "success": True,
            "scanned": scanned,
            "groups": groups,
            "total_waste_bytes": total_waste,
        }
