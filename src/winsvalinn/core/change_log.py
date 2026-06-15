"""
Change Log / Audit Trail for WinSvalinn.

Records every system modification made by the application,
enabling full traceability and supporting undo operations.
"""

import json
import os
import threading
from datetime import datetime

from winsvalinn.utils.logger import ModuleLogger

logger = ModuleLogger("ChangeLog")

# Default storage
CHANGELOG_DIR = os.path.join(os.path.expanduser("~"), ".winsvalinn")
CHANGELOG_FILE = os.path.join(CHANGELOG_DIR, "changelog.json")
MAX_ENTRIES = 2000
MAX_FILE_SIZE_MB = 10


class ChangeLogger:
    """
    Audit trail that records every change WinSvalinn makes to the system.

    Thread-safe. All writes are serialized via a lock.
    """

    def __init__(self, changelog_path=None, callback=None):
        self._path = changelog_path or CHANGELOG_FILE
        self._callback = callback or (lambda msg, level="info": None)
        self._lock = threading.Lock()
        self._ensure_dir()
        self._entries = self._load()
        logger.info(f"ChangeLogger initialized ({len(self._entries)} entries)")

    def _log(self, msg, level="info"):
        getattr(logger, level, logger.info)(msg)
        self._callback(msg, level)

    def _ensure_dir(self):
        os.makedirs(os.path.dirname(self._path), exist_ok=True)

    def _load(self):
        """Load existing changelog from disk."""
        if os.path.exists(self._path):
            try:
                with open(self._path, encoding="utf-8") as f:
                    data = json.load(f)
                return data.get("entries", [])
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Could not load changelog: {e}")
                return []
        return []

    def _save(self):
        """Save changelog to disk. Must be called with lock held."""
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump({"version": 1, "entries": self._entries}, f, indent=2, ensure_ascii=False)
        except OSError as e:
            logger.error(f"Failed to save changelog: {e}")

    def log_change(
        self,
        module,
        action,
        details,
        previous_state=None,
        new_state=None,
        reversible=True,
        backup_id=None,
    ):
        """
        Record a system change.

        Args:
            module: Module that made the change (e.g., "telemetry_blocker", "gpu")
            action: What was done (e.g., "disable_service", "set_registry")
            details: Human-readable description
            previous_state: State before the change (for undo)
            new_state: State after the change
            reversible: Whether this change can be undone
            backup_id: Associated registry backup ID (if any)

        Returns:
            str: Entry ID
        """
        entry_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

        entry = {
            "id": entry_id,
            "timestamp": datetime.now().isoformat(),
            "module": module,
            "action": action,
            "details": details,
            "previous_state": previous_state,
            "new_state": new_state,
            "reversible": reversible,
            "backup_id": backup_id,
            "reverted": False,
        }

        with self._lock:
            self._entries.append(entry)
            self._trim_if_needed()
            self._save()

        logger.info(f"[{module}] {action}: {details}")
        return entry_id

    def get_history(self, module=None, limit=100, include_reverted=True):
        """
        Get change history, optionally filtered.

        Args:
            module: Filter by module name
            limit: Maximum entries to return
            include_reverted: Whether to include reverted entries

        Returns:
            list[dict]: Entries sorted newest first
        """
        with self._lock:
            entries = list(self._entries)

        if module:
            entries = [e for e in entries if e["module"] == module]

        if not include_reverted:
            entries = [e for e in entries if not e.get("reverted", False)]

        # Newest first
        entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return entries[:limit]

    def get_modules(self):
        """Get all unique module names from the changelog."""
        with self._lock:
            return sorted(set(e["module"] for e in self._entries))

    def get_entry(self, entry_id):
        """Get a specific entry by ID."""
        with self._lock:
            for entry in self._entries:
                if entry["id"] == entry_id:
                    return dict(entry)
        return None

    def mark_reverted(self, entry_id):
        """
        Mark a changelog entry as reverted/undone.

        Args:
            entry_id: The entry ID to mark

        Returns:
            bool: Whether the entry was found and marked
        """
        with self._lock:
            for entry in self._entries:
                if entry["id"] == entry_id:
                    entry["reverted"] = True
                    entry["reverted_at"] = datetime.now().isoformat()
                    self._save()
                    self._log(f"Marked as reverted: {entry['action']} ({entry['module']})")
                    return True
        return False

    def get_reversible_changes(self, module=None):
        """
        Get all changes that can be undone (reversible and not yet reverted).

        Returns:
            list[dict]: Reversible, non-reverted entries (newest first)
        """
        with self._lock:
            entries = [
                e
                for e in self._entries
                if e.get("reversible", False) and not e.get("reverted", False)
            ]

        if module:
            entries = [e for e in entries if e["module"] == module]

        entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return entries

    def get_stats(self):
        """
        Get changelog statistics.

        Returns:
            dict: Statistics about the changelog
        """
        with self._lock:
            total = len(self._entries)
            modules = {}
            reversible = 0
            reverted = 0

            for e in self._entries:
                mod = e.get("module", "unknown")
                modules[mod] = modules.get(mod, 0) + 1
                if e.get("reversible"):
                    reversible += 1
                if e.get("reverted"):
                    reverted += 1

        file_size = 0
        if os.path.exists(self._path):
            file_size = os.path.getsize(self._path)

        return {
            "total_entries": total,
            "by_module": modules,
            "reversible": reversible,
            "reverted": reverted,
            "file_size_bytes": file_size,
        }

    def export_report(self, output_path, fmt="json"):
        """
        Export the full changelog to a file.

        Args:
            output_path: Path to write the report
            fmt: Format - "json" or "txt"

        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            with self._lock:
                entries = list(self._entries)

            if fmt == "json":
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(
                        {
                            "exported_at": datetime.now().isoformat(),
                            "total_entries": len(entries),
                            "entries": entries,
                        },
                        f,
                        indent=2,
                        ensure_ascii=False,
                    )
            else:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write("WinSvalinn Change Log Report\n")
                    f.write(f"Exported: {datetime.now().isoformat()}\n")
                    f.write(f"Total entries: {len(entries)}\n")
                    f.write("=" * 70 + "\n\n")

                    for entry in reversed(entries):
                        status = "[REVERTED]" if entry.get("reverted") else "[ACTIVE]"
                        undo = "Yes" if entry.get("reversible") else "No"
                        f.write(f"{entry['timestamp']}  {status}\n")
                        f.write(f"  Module:   {entry['module']}\n")
                        f.write(f"  Action:   {entry['action']}\n")
                        f.write(f"  Details:  {entry['details']}\n")
                        f.write(f"  Undoable: {undo}\n")
                        if entry.get("backup_id"):
                            f.write(f"  Backup:   {entry['backup_id']}\n")
                        f.write("-" * 70 + "\n")

            self._log(f"Changelog exported to {output_path}")
            return True, output_path

        except Exception as e:
            self._log(f"Failed to export changelog: {e}", "error")
            return False, str(e)

    def clear(self):
        """Clear all changelog entries."""
        with self._lock:
            count = len(self._entries)
            self._entries = []
            self._save()
        self._log(f"Changelog cleared ({count} entries removed)", "warning")
        return count

    def _trim_if_needed(self):
        """Remove oldest entries if exceeding limits. Must be called with lock held."""
        if len(self._entries) > MAX_ENTRIES:
            excess = len(self._entries) - MAX_ENTRIES
            self._entries = self._entries[excess:]
            logger.info(f"Trimmed {excess} old changelog entries")
