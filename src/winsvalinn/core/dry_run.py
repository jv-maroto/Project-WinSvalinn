"""
Dry-Run Mode for WinSvalinn.

Context manager that intercepts all destructive operations
and records what WOULD happen without actually executing.
"""

import threading

from winsvalinn.utils.logger import ModuleLogger

logger = ModuleLogger("DryRun")

# Global dry-run state
_dry_run_active = False
_dry_run_lock = threading.Lock()
_planned_actions = []


def is_dry_run():
    """Check if dry-run mode is active."""
    return _dry_run_active


def get_planned_actions():
    """Get list of planned actions (only meaningful during dry-run)."""
    with _dry_run_lock:
        return list(_planned_actions)


def record_action(module, action, details):
    """Record a planned action during dry-run mode."""
    with _dry_run_lock:
        _planned_actions.append(
            {
                "module": module,
                "action": action,
                "details": details,
            }
        )
    logger.info(f"[DRY-RUN] Would {action}: {details}")


class DryRunContext:
    """
    Context manager for dry-run mode.

    Usage:
        with DryRunContext() as ctx:
            # All registry writes, service changes, etc. are intercepted
            optimizer.apply_all_tweaks()

        planned = ctx.get_planned_actions()
        # Show user what WOULD have happened
    """

    def __init__(self):
        self._previous_state = False

    def __enter__(self):
        global _dry_run_active, _planned_actions
        with _dry_run_lock:
            self._previous_state = _dry_run_active
            _dry_run_active = True
            _planned_actions = []
        logger.info("Dry-run mode ENABLED")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        global _dry_run_active
        with _dry_run_lock:
            _dry_run_active = self._previous_state
        logger.info("Dry-run mode DISABLED")
        return False

    def get_planned_actions(self):
        """Get all actions that were planned during this dry-run session."""
        return get_planned_actions()


def enable_dry_run():
    """Enable dry-run mode globally."""
    global _dry_run_active, _planned_actions
    with _dry_run_lock:
        _dry_run_active = True
        _planned_actions = []
    logger.info("Dry-run mode ENABLED (global)")


def disable_dry_run():
    """Disable dry-run mode globally."""
    global _dry_run_active
    with _dry_run_lock:
        _dry_run_active = False
    logger.info("Dry-run mode DISABLED (global)")


def clear_planned_actions():
    """Clear the planned actions list."""
    global _planned_actions
    with _dry_run_lock:
        _planned_actions = []
