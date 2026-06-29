"""
Windows Registry helper utilities.

Provides safe, logged, and validated registry operations.
All writes are automatically backed up before modification.
"""

import platform
import subprocess

from winsvalinn.utils.logger import ModuleLogger

logger = ModuleLogger("RegistryHelper")

IS_WINDOWS = platform.system() == "Windows"

# Global reference to the app's RegistryBackupManager and ChangeLogger.
# Set by WinSvalinnApp.__init__ after creating the managers.
_backup_mgr = None
_change_logger = None


def init_safety_net(backup_mgr=None, change_logger=None):
    """Initialize the safety net references. Called once from app.py."""
    global _backup_mgr, _change_logger
    _backup_mgr = backup_mgr
    _change_logger = change_logger
    logger.info("Registry safety net initialized")


def set_registry(path, name, value, value_type="REG_DWORD", timeout=10, tag="registry"):
    """
    Set Windows registry value safely with logging.

    Args:
        path: Registry path (e.g., "HKLM\\SOFTWARE\\...")
        name: Value name
        value: Value data
        value_type: Registry value type (REG_DWORD, REG_SZ, REG_BINARY, etc.)
        timeout: Command timeout in seconds

    Returns:
        tuple: (success: bool, message: str)
    """
    if not IS_WINDOWS:
        logger.warning("Cannot modify registry on non-Windows system")
        return False, "Not Windows system"

    # Dry-run intercept
    from winsvalinn.core.dry_run import is_dry_run, record_action

    if is_dry_run():
        record_action(tag, "set_registry", f"{path}\\{name} = {value} ({value_type})")
        return True, f"[DRY-RUN] Would set: {path}\\{name} = {value}"

    # Normalize the type: reg.exe needs "REG_DWORD", but callers often pass
    # the short form ("DWORD", "SZ"). Without this, reg add fails with a syntax
    # error and the remediation appears broken.
    if value_type and not value_type.upper().startswith("REG_"):
        value_type = "REG_" + value_type.upper()

    try:
        logger.info(f"Setting registry: {path}\\{name} = {value} ({value_type})")

        # Auto-backup before modification
        backup_id = None
        previous_value = None
        if _backup_mgr:
            _backup_mgr.backup_key(path, tag=tag)
        # Read current value for changelog
        success_read, prev = get_registry(path, name, timeout=5)
        if success_read:
            previous_value = prev

        result = subprocess.run(
            ["reg", "add", path, "/v", name, "/t", value_type, "/d", str(value), "/f"],
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )

        if result.returncode == 0:
            logger.info(f"Successfully set: {path}\\{name}")
            # Log the change
            if _change_logger:
                _change_logger.log_change(
                    module=tag,
                    action="set_registry",
                    details=f"{path}\\{name} = {value} ({value_type})",
                    previous_state=previous_value,
                    new_state=str(value),
                    reversible=True,
                    backup_id=backup_id,
                )
            return True, f"OK: {path}\\{name} = {value}"
        else:
            error = result.stderr.strip() or result.stdout.strip()
            logger.error(f"Failed to set {path}\\{name}: {error}")
            return False, f"FAIL: {error[:100]}"

    except subprocess.TimeoutExpired:
        logger.error(f"Timeout setting {path}\\{name}")
        return False, "Operation timed out"

    except FileNotFoundError:
        logger.error("reg.exe command not found - is this Windows?")
        return False, "Registry command not available"

    except Exception as e:
        logger.exception(f"Unexpected error setting {path}\\{name}")
        return False, f"Error: {str(e)[:100]}"


def get_registry(path, name, timeout=10):
    """
    Get Windows registry value.

    Args:
        path: Registry path
        name: Value name
        timeout: Command timeout in seconds

    Returns:
        tuple: (success: bool, value: str or None)
    """
    if not IS_WINDOWS:
        logger.warning("Cannot read registry on non-Windows system")
        return False, None

    try:
        logger.debug(f"Reading registry: {path}\\{name}")

        result = subprocess.run(
            ["reg", "query", path, "/v", name],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )

        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            for line in lines:
                if name in line:
                    parts = line.split(maxsplit=3)
                    if len(parts) >= 4:
                        value = parts[3]
                        logger.debug(f"Found: {path}\\{name} = {value}")
                        return True, value

            logger.warning(f"Value {name} not found in output")
            return False, None
        else:
            logger.error(f"Failed to query {path}\\{name}")
            return False, None

    except subprocess.TimeoutExpired:
        logger.error(f"Timeout reading {path}\\{name}")
        return False, None

    except Exception:
        logger.exception(f"Error reading {path}\\{name}")
        return False, None


def delete_registry(path, name, timeout=10, tag="registry"):
    """
    Delete Windows registry value.

    Args:
        path: Registry path
        name: Value name
        timeout: Command timeout in seconds
        tag: Operation tag for backup/changelog

    Returns:
        tuple: (success: bool, message: str)
    """
    if not IS_WINDOWS:
        return False, "Not Windows system"

    # Dry-run intercept
    from winsvalinn.core.dry_run import is_dry_run, record_action

    if is_dry_run():
        record_action(tag, "delete_registry", f"Delete {path}\\{name}")
        return True, f"[DRY-RUN] Would delete: {path}\\{name}"

    try:
        logger.info(f"Deleting registry value: {path}\\{name}")

        # Auto-backup before deletion
        if _backup_mgr:
            _backup_mgr.backup_key(path, tag=tag)
        # Read current value for changelog
        previous_value = None
        success_read, prev = get_registry(path, name, timeout=5)
        if success_read:
            previous_value = prev

        result = subprocess.run(
            ["reg", "delete", path, "/v", name, "/f"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )

        if result.returncode == 0:
            logger.info(f"Deleted: {path}\\{name}")
            if _change_logger:
                _change_logger.log_change(
                    module=tag,
                    action="delete_registry",
                    details=f"Deleted {path}\\{name}",
                    previous_state=previous_value,
                    new_state=None,
                    reversible=True,
                )
            return True, f"Deleted: {path}\\{name}"
        else:
            error = result.stderr.strip()
            logger.error(f"Failed to delete {path}\\{name}: {error}")
            return False, f"FAIL: {error[:100]}"

    except Exception as e:
        logger.exception(f"Error deleting {path}\\{name}")
        return False, str(e)


class RegistryBackup:
    """Backup and restore registry values."""

    def __init__(self):
        self.backups = {}
        logger.info("Registry backup system initialized")

    def backup(self, path, name):
        """Backup a single registry value before modification."""
        success, value = get_registry(path, name)

        if success:
            key = f"{path}\\{name}"
            self.backups[key] = {"path": path, "name": name, "value": value}
            logger.info(f"Backed up: {key} = {value}")
            return True
        else:
            logger.warning(f"Could not backup {path}\\{name} (may not exist)")
            return False

    def restore(self, path, name):
        """Restore a single backed-up value."""
        key = f"{path}\\{name}"

        if key not in self.backups:
            logger.error(f"No backup found for {key}")
            return False

        backup = self.backups[key]
        success, msg = set_registry(path, name, backup["value"])

        if success:
            logger.info(f"Restored: {key}")
            return True
        else:
            logger.error(f"Failed to restore {key}: {msg}")
            return False

    def restore_all(self):
        """Restore all backed-up values."""
        logger.info(f"Restoring {len(self.backups)} registry values...")

        results = {}
        for key, backup in self.backups.items():
            success = self.restore(backup["path"], backup["name"])
            results[key] = success

        success_count = sum(results.values())
        logger.info(f"Restored {success_count}/{len(self.backups)} values")

        return results
