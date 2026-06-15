"""
Registry Backup & Rollback system for WinSvalinn.

Provides file-based registry backup/restore using reg.exe export/import.
Every registry modification should be preceded by a backup.
"""

import json
import os
import platform
import subprocess
from datetime import datetime

from winsvalinn.utils.logger import ModuleLogger

logger = ModuleLogger("RegistryBackup")

IS_WINDOWS = platform.system() == "Windows"
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

# Default backup directory
BACKUP_DIR = os.path.join(os.path.expanduser("~"), ".winsvalinn", "registry_backups")


class RegistryBackupManager:
    """
    File-based registry backup and restore manager.

    Exports registry keys to .reg files before modifications,
    allowing full rollback of any changes made by WinSvalinn.
    """

    MAX_BACKUPS = 50  # Maximum number of backup sets to keep

    def __init__(self, backup_dir=None, callback=None):
        self._backup_dir = backup_dir or BACKUP_DIR
        self._callback = callback or (lambda msg, level="info": None)
        self._manifest_path = os.path.join(self._backup_dir, "manifest.json")
        self._ensure_backup_dir()
        logger.info(f"RegistryBackupManager initialized at {self._backup_dir}")

    def _log(self, msg, level="info"):
        getattr(logger, level, logger.info)(msg)
        self._callback(msg, level)

    def _ensure_backup_dir(self):
        os.makedirs(self._backup_dir, exist_ok=True)

    def _load_manifest(self):
        """Load the backup manifest (index of all backups)."""
        if os.path.exists(self._manifest_path):
            try:
                with open(self._manifest_path, encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return {"backups": []}
        return {"backups": []}

    def _save_manifest(self, manifest):
        """Save the backup manifest."""
        try:
            with open(self._manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
        except OSError as e:
            self._log(f"Failed to save manifest: {e}", "error")

    def backup_key(self, registry_path, tag="manual"):
        """
        Backup a single registry key (and all its subkeys) to a .reg file.

        Args:
            registry_path: Full registry path (e.g., "HKLM\\SOFTWARE\\Microsoft\\Windows")
            tag: Operation tag for identification (e.g., "telemetry_block", "gpu_optimize")

        Returns:
            tuple: (success: bool, backup_id: str or error message)
        """
        if not IS_WINDOWS:
            return False, "Only available on Windows"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_path = registry_path.replace("\\", "_").replace("/", "_")
        filename = f"{timestamp}_{tag}_{safe_path[:80]}.reg"
        filepath = os.path.join(self._backup_dir, filename)

        try:
            result = subprocess.run(
                ["reg", "export", registry_path, filepath, "/y"],
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=CREATE_NO_WINDOW,
            )

            if result.returncode == 0:
                backup_id = f"{timestamp}_{tag}"
                file_size = os.path.getsize(filepath)

                # Update manifest
                manifest = self._load_manifest()
                manifest["backups"].append(
                    {
                        "id": backup_id,
                        "tag": tag,
                        "registry_path": registry_path,
                        "filename": filename,
                        "filepath": filepath,
                        "timestamp": datetime.now().isoformat(),
                        "size_bytes": file_size,
                    }
                )
                self._save_manifest(manifest)

                self._log(f"Backed up: {registry_path} ({file_size} bytes)")
                self._cleanup_old_backups()
                return True, backup_id
            else:
                error = result.stderr.strip() or result.stdout.strip()
                # Key might not exist yet — that's OK for new keys
                if "unable to find" in error.lower() or "no se encuentra" in error.lower():
                    self._log(f"Key does not exist yet (new key): {registry_path}", "info")
                    return True, "key_not_exists"
                self._log(f"Failed to backup {registry_path}: {error}", "error")
                return False, error[:200]

        except subprocess.TimeoutExpired:
            self._log(f"Timeout backing up {registry_path}", "error")
            return False, "Timeout"
        except Exception as e:
            self._log(f"Error backing up {registry_path}: {e}", "error")
            return False, str(e)

    def backup_keys(self, registry_paths, tag="batch"):
        """
        Backup multiple registry keys as a batch.

        Args:
            registry_paths: List of registry paths
            tag: Operation tag for the batch

        Returns:
            dict: {path: (success, backup_id)}
        """
        results = {}
        for path in registry_paths:
            results[path] = self.backup_key(path, tag)
        success_count = sum(1 for s, _ in results.values() if s)
        self._log(f"Batch backup: {success_count}/{len(registry_paths)} keys backed up [{tag}]")
        return results

    def restore_backup(self, backup_id=None, filename=None):
        """
        Restore a registry backup by ID or filename.

        Args:
            backup_id: The backup ID to restore
            filename: Direct filename to restore

        Returns:
            tuple: (success: bool, message: str)
        """
        if not IS_WINDOWS:
            return False, "Only available on Windows"

        filepath = None

        if filename:
            filepath = os.path.join(self._backup_dir, filename)
        elif backup_id:
            manifest = self._load_manifest()
            for entry in manifest["backups"]:
                if entry["id"] == backup_id:
                    filepath = entry["filepath"]
                    break

        if not filepath or not os.path.exists(filepath):
            return False, f"Backup file not found: {backup_id or filename}"

        try:
            self._log(f"Restoring registry backup: {os.path.basename(filepath)}")

            result = subprocess.run(
                ["reg", "import", filepath],
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=CREATE_NO_WINDOW,
            )

            if result.returncode == 0:
                self._log("Registry restored successfully", "info")
                return True, "Registry restored successfully"
            else:
                error = result.stderr.strip()
                self._log(f"Failed to restore: {error}", "error")
                return False, f"Failed: {error[:200]}"

        except subprocess.TimeoutExpired:
            return False, "Restore timed out"
        except Exception as e:
            return False, str(e)

    def restore_by_tag(self, tag):
        """
        Restore ALL backups associated with a specific operation tag.

        Args:
            tag: The operation tag (e.g., "telemetry_block")

        Returns:
            tuple: (success_count: int, total: int, errors: list)
        """
        manifest = self._load_manifest()
        matching = [e for e in manifest["backups"] if e["tag"] == tag]

        if not matching:
            return 0, 0, [f"No backups found for tag: {tag}"]

        success_count = 0
        errors = []
        for entry in matching:
            success, msg = self.restore_backup(filename=entry["filename"])
            if success:
                success_count += 1
            else:
                errors.append(f"{entry['registry_path']}: {msg}")

        self._log(f"Restored {success_count}/{len(matching)} backups for [{tag}]")
        return success_count, len(matching), errors

    def list_backups(self, tag=None):
        """
        List all available backups, optionally filtered by tag.

        Args:
            tag: Optional filter by operation tag

        Returns:
            list[dict]: Backup entries sorted by date (newest first)
        """
        manifest = self._load_manifest()
        backups = manifest.get("backups", [])

        if tag:
            backups = [b for b in backups if b["tag"] == tag]

        # Verify files still exist
        valid = []
        for b in backups:
            if os.path.exists(b.get("filepath", "")):
                valid.append(b)

        # Sort newest first
        valid.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return valid

    def get_tags(self):
        """
        Get all unique operation tags from backups.

        Returns:
            list[str]: Unique tags sorted alphabetically
        """
        manifest = self._load_manifest()
        tags = set(b["tag"] for b in manifest.get("backups", []))
        return sorted(tags)

    def get_backup_size(self):
        """
        Get total size of all backup files.

        Returns:
            tuple: (total_bytes: int, file_count: int)
        """
        total = 0
        count = 0
        if os.path.exists(self._backup_dir):
            for f in os.listdir(self._backup_dir):
                if f.endswith(".reg"):
                    fpath = os.path.join(self._backup_dir, f)
                    total += os.path.getsize(fpath)
                    count += 1
        return total, count

    def _cleanup_old_backups(self):
        """Remove oldest backups when exceeding MAX_BACKUPS."""
        manifest = self._load_manifest()
        backups = manifest.get("backups", [])

        if len(backups) <= self.MAX_BACKUPS:
            return

        # Sort by timestamp (oldest first) and remove excess
        backups.sort(key=lambda x: x.get("timestamp", ""))
        to_remove = backups[: len(backups) - self.MAX_BACKUPS]

        for entry in to_remove:
            filepath = entry.get("filepath", "")
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    self._log(f"Cleaned old backup: {os.path.basename(filepath)}")
                except OSError:
                    pass

        manifest["backups"] = backups[len(to_remove) :]
        self._save_manifest(manifest)

    def clear_all_backups(self):
        """
        Delete ALL backup files and reset manifest.

        Returns:
            tuple: (deleted_count: int, freed_bytes: int)
        """
        total_freed = 0
        deleted = 0

        if os.path.exists(self._backup_dir):
            for f in os.listdir(self._backup_dir):
                if f.endswith(".reg"):
                    fpath = os.path.join(self._backup_dir, f)
                    try:
                        total_freed += os.path.getsize(fpath)
                        os.remove(fpath)
                        deleted += 1
                    except OSError:
                        pass

        self._save_manifest({"backups": []})
        self._log(f"Cleared {deleted} backups, freed {total_freed / 1024:.1f} KB")
        return deleted, total_freed
