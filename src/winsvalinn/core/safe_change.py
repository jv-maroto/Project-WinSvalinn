"""
Safe-change checkpoints for WinSvalinn.

Best-effort safety net executed *before* a system-modifying change. It tries
to create a Windows System Restore Point and/or a registry backup so the
change can be rolled back. It is intentionally defensive: it never raises,
captures every failure, and reports what was actually created.

GUI-free and fully testable: restore_point / registry_backup are imported
lazily so they can be mocked in tests without a display or admin rights.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def create_checkpoint(label: str) -> dict:
    """
    Create a best-effort safety checkpoint before applying a change.

    Attempts, independently and without ever raising:
      1. A Windows System Restore Point (via RestorePointManager).
      2. A registry backup of WinSvalinn-relevant hives (via
         RegistryBackupManager), tagged with ``label``.

    Args:
        label: Human-readable identifier for the checkpoint (e.g.
            ``"remediate:firewall"``). Used as the restore-point description
            and as the registry-backup tag.

    Returns:
        dict with keys:
          - ``created`` (bool): True if *any* checkpoint mechanism succeeded.
          - ``restore_point`` (bool): True if a restore point was created.
          - ``registry_backup`` (bool): True if at least one registry key was
            backed up.
          - ``detail`` (str): Short human-readable summary.
    """
    safe_label = str(label or "checkpoint").strip() or "checkpoint"

    restore_ok, restore_detail = _try_restore_point(safe_label)
    registry_ok, registry_detail = _try_registry_backup(safe_label)

    created = restore_ok or registry_ok
    detail = "; ".join([restore_detail, registry_detail])

    return {
        "created": created,
        "restore_point": restore_ok,
        "registry_backup": registry_ok,
        "detail": detail,
    }


def _try_restore_point(label: str) -> tuple[bool, str]:
    """Attempt a System Restore Point; never raises."""
    try:
        from winsvalinn.core.restore_point import RestorePointManager

        manager = RestorePointManager()
        ok, message = manager.create_restore_point(f"WinSvalinn: {label}")
        if ok:
            return True, f"restore point: {message}"
        return False, f"restore point skipped: {message}"
    except Exception as exc:  # best-effort: report, never propagate
        logger.warning("Restore point checkpoint failed: %s", exc)
        return False, f"restore point error: {exc}"


# WinSvalinn touches these hives across its remediations; backing them up
# gives a file-based rollback even when System Restore is unavailable.
_REGISTRY_KEYS = (
    r"HKLM\SOFTWARE\Policies\Microsoft\Windows Defender",
    r"HKLM\SYSTEM\CurrentControlSet\Services\SharedAccess\Parameters\FirewallPolicy",
    r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer",
    r"HKLM\SYSTEM\CurrentControlSet\Control\Terminal Server",
    r"HKLM\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters",
)


def _try_registry_backup(label: str) -> tuple[bool, str]:
    """Attempt a registry backup of relevant hives; never raises."""
    try:
        from winsvalinn.core.registry_backup import RegistryBackupManager

        manager = RegistryBackupManager()
        results = manager.backup_keys(list(_REGISTRY_KEYS), tag=label)
        success = sum(1 for ok, _ in results.values() if ok)
        if success:
            return True, f"registry backup: {success}/{len(_REGISTRY_KEYS)} keys"
        return False, "registry backup: no keys backed up"
    except Exception as exc:  # best-effort: report, never propagate
        logger.warning("Registry backup checkpoint failed: %s", exc)
        return False, f"registry backup error: {exc}"
