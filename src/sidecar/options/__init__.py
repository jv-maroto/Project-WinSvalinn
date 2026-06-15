"""
Native options registry — the successor to the legacy filesystem plugins.

Each :class:`Option` describes a single user-facing action with metadata
(section, label, edition gating, destructiveness) and a zero-argument
``handler`` that performs the work and returns a normalized result:

    {"ok": bool, "log": [{"msg": str, "level": str}], "result": Any}

Handlers reuse existing engines from :mod:`winsvalinn.core`. They never raise:
all failures are captured into the log/ok fields so the API layer can return
a stable JSON shape.

This is a *package*: option groups live in sibling submodules (e.g.
``opt_gaming.py``, ``opt_privacy.py``). Each submodule calls :func:`register`
at import time; every submodule is auto-imported when this package loads, so
adding a new group is a drop-in file with no edits here.
"""

from __future__ import annotations

import importlib
import pkgutil
from collections.abc import Callable
from dataclasses import dataclass, field

# A log entry is {"msg": str, "level": "info"|"success"|"warning"|"error"}
LogEntry = dict
HandlerResult = dict


@dataclass
class Option:
    """A single executable option in the native registry."""

    id: str
    section: str
    label: str
    edition: str  # "free" | "empresarial"
    description: str
    is_destructive: bool
    handler: Callable[[], HandlerResult]
    meta: dict = field(default_factory=dict)

    def to_public(self) -> dict:
        """Return the JSON-safe metadata (without the handler)."""
        return {
            "id": self.id,
            "section": self.section,
            "label": self.label,
            "edition": self.edition,
            "description": self.description,
            "is_destructive": self.is_destructive,
        }


# ─── Handler helpers ─────────────────────────────────────────────────────


def _collect_logger(log: list[LogEntry]) -> Callable[[str, str], None]:
    """Build a callback that appends normalized log entries to ``log``."""

    def _cb(msg: str, level: str = "info") -> None:
        norm = level.lower()
        if norm in ("ok", "success"):
            norm = "success"
        elif norm in ("err", "error"):
            norm = "error"
        elif norm in ("warn", "warning"):
            norm = "warning"
        elif norm not in ("info", "success", "warning", "error"):
            norm = "info"
        log.append({"msg": str(msg), "level": norm})

    return _cb


# ─── Registry ────────────────────────────────────────────────────────────

OPTIONS: dict[str, Option] = {}


def register(option: Option) -> Option:
    """Register an :class:`Option` (last registration wins on id clash)."""
    OPTIONS[option.id] = option
    return option


def list_options(section: str | None = None) -> list[dict]:
    """Return public metadata for all options, optionally filtered by section."""
    out = []
    for opt in OPTIONS.values():
        if section and opt.section != section:
            continue
        out.append(opt.to_public())
    return out


def get_option(option_id: str) -> Option | None:
    """Return an :class:`Option` by id, or None."""
    return OPTIONS.get(option_id)


def run_option(option_id: str) -> dict:
    """
    Execute an option's handler by id.

    Returns the normalized handler result, or an error dict if the id is
    unknown. Edition gating is enforced by the API layer, not here.
    """
    option = OPTIONS.get(option_id)
    if option is None:
        return {"ok": False, "log": [], "result": None, "error": "unknown_option"}
    return option.handler()


# ─── Built-in sample handlers (Fase 0) ───────────────────────────────────


def _handler_free_ram() -> HandlerResult:
    """Free RAM via the existing RAMOptimizer (free, non-destructive)."""
    log: list[LogEntry] = []
    try:
        from winsvalinn.core import RAMOptimizer

        result = RAMOptimizer(callback=_collect_logger(log)).free_ram()
        ok = bool(result.get("success", True))
        if not log:
            freed = result.get("freed_readable", "?")
            log.append({"msg": f"RAM optimization complete (freed {freed})", "level": "success"})
        return {"ok": ok, "log": log, "result": result}
    except Exception as exc:  # noqa: BLE001 - surfaced to the user, never raised
        log.append({"msg": f"Error: {exc}", "level": "error"})
        return {"ok": False, "log": log, "result": None}


def _handler_flush_dns() -> HandlerResult:
    """Flush the DNS resolver cache via DNSManager (free privacy action)."""
    log: list[LogEntry] = []
    try:
        from winsvalinn.core import DNSManager

        result = DNSManager(callback=_collect_logger(log)).flush_dns()
        ok = bool(result.get("success", False))
        if not log:
            log.append(
                {
                    "msg": result.get("message", "DNS cache flushed"),
                    "level": "success" if ok else "warning",
                }
            )
        return {"ok": ok, "log": log, "result": result}
    except Exception as exc:  # noqa: BLE001
        log.append({"msg": f"Error: {exc}", "level": "error"})
        return {"ok": False, "log": log, "result": None}


def _handler_defender_status() -> HandlerResult:
    """Report Windows Defender / Firewall posture (free, read-only)."""
    log: list[LogEntry] = []
    try:
        from winsvalinn.core import DefenderControl, FirewallManager

        defender = DefenderControl(callback=_collect_logger(log)).get_defender_status()
        firewall = FirewallManager(callback=_collect_logger(log)).get_firewall_status()

        rtp = defender.get("real_time_protection", False)
        log.append(
            {
                "msg": f"Defender real-time protection: {'ON' if rtp else 'OFF'}",
                "level": "success" if rtp else "warning",
            }
        )
        fw_on = any(p.get("enabled") for p in firewall.values() if isinstance(p, dict))
        log.append(
            {
                "msg": f"Windows Firewall: {'active on at least one profile' if fw_on else 'inactive'}",
                "level": "success" if fw_on else "warning",
            }
        )
        return {
            "ok": True,
            "log": log,
            "result": {"defender": defender, "firewall": firewall},
        }
    except Exception as exc:  # noqa: BLE001
        log.append({"msg": f"Error: {exc}", "level": "error"})
        return {"ok": False, "log": log, "result": None}


def _handler_block_telemetry() -> HandlerResult:
    """Block all Windows telemetry (empresarial, destructive system change)."""
    log: list[LogEntry] = []
    try:
        from winsvalinn.core import TelemetryBlocker

        result = TelemetryBlocker(callback=_collect_logger(log)).block_all_telemetry()
        if not log:
            log.append({"msg": "Telemetry blocking applied", "level": "success"})
        return {"ok": True, "log": log, "result": result}
    except Exception as exc:  # noqa: BLE001
        log.append({"msg": f"Error: {exc}", "level": "error"})
        return {"ok": False, "log": log, "result": None}


register(
    Option(
        id="ram_free",
        section="optimization",
        label="Liberar RAM",
        edition="free",
        description="Libera memoria RAM recortando working sets y cachés del sistema.",
        is_destructive=False,
        handler=_handler_free_ram,
    )
)
register(
    Option(
        id="dns_flush",
        section="privacy",
        label="Limpiar caché DNS",
        edition="free",
        description="Vacía la caché del resolutor DNS para limpiar dominios cacheados.",
        is_destructive=False,
        handler=_handler_flush_dns,
    )
)
register(
    Option(
        id="security_status",
        section="security",
        label="Estado de Defender y Firewall",
        edition="free",
        description="Comprueba el estado de Windows Defender y el Firewall (solo lectura).",
        is_destructive=False,
        handler=_handler_defender_status,
    )
)
register(
    Option(
        id="telemetry_block_all",
        section="privacy",
        label="Bloquear toda la telemetría",
        edition="empresarial",
        description="Deshabilita servicios, tareas y dominios de telemetría de Windows.",
        is_destructive=True,
        handler=_handler_block_telemetry,
    )
)


# ─── Auto-discover option-group submodules ───────────────────────────────
# Importing each sibling submodule triggers its register(...) calls. Runs last,
# after the public API (register/Option/_collect_logger) is defined, so
# submodules can `from sidecar.options import register, Option`.

for _mod in pkgutil.iter_modules(__path__):
    if _mod.name.startswith("_"):
        continue
    importlib.import_module(f"{__name__}.{_mod.name}")
