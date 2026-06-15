"""
Privacy options group — native successors to the legacy privacy plugins.

Migrates the user actions from three filesystem plugins into the native
:class:`~sidecar.options.Option` registry:

* ``plugin_doh_setup``        -> DNS over HTTPS (enable / disable / status)
* ``plugin_hosts_steven_black`` -> StevenBlack hosts import / removal
* ``plugin_oo_shutup_bridge`` -> O&O ShutUp10++ download / launch bridge

Each option reuses the existing core engines (``DNSManager``,
``HostsManager``, ``OOSUBridge``) wired to the option's log via
:func:`_collect_logger`. Handlers never raise: all failures are captured
into the ``log``/``ok`` fields.
"""

from __future__ import annotations

from sidecar.options import HandlerResult, LogEntry, Option, _collect_logger, register

# ─── DNS over HTTPS (plugin_doh_setup) ───────────────────────────────────


def _handler_doh_enable() -> HandlerResult:
    """Enable DoH (mandatory mode) for the current DNS via DNSManager."""
    log: list[LogEntry] = []
    try:
        from winsvalinn.core import DNSManager

        result = DNSManager(callback=_collect_logger(log)).enable_doh_for_current_dns(
            mandatory=True
        )
        ok = bool(result.get("success", False))
        if not log:
            log.append(
                {
                    "msg": result.get("message", "DoH enabled"),
                    "level": "success" if ok else "warning",
                }
            )
        return {"ok": ok, "log": log, "result": result}
    except Exception as exc:  # noqa: BLE001 - surfaced to the user, never raised
        log.append({"msg": f"Error: {exc}", "level": "error"})
        return {"ok": False, "log": log, "result": None}


def _handler_doh_disable() -> HandlerResult:
    """Disable DoH globally via DNSManager."""
    log: list[LogEntry] = []
    try:
        from winsvalinn.core import DNSManager

        result = DNSManager(callback=_collect_logger(log)).disable_doh()
        ok = bool(result.get("success", False))
        if not log:
            log.append(
                {
                    "msg": result.get("message", "DoH disabled"),
                    "level": "success" if ok else "warning",
                }
            )
        return {"ok": ok, "log": log, "result": result}
    except Exception as exc:  # noqa: BLE001
        log.append({"msg": f"Error: {exc}", "level": "error"})
        return {"ok": False, "log": log, "result": None}


def _handler_doh_status() -> HandlerResult:
    """Report which well-known DoH servers are registered (read-only)."""
    log: list[LogEntry] = []
    try:
        from winsvalinn.core import DNSManager

        entries = DNSManager(callback=_collect_logger(log)).get_doh_status()
        registered = sum(1 for e in entries if e.get("registered"))
        log.append(
            {
                "msg": f"Servidores DoH registrados: {registered}/{len(entries)}",
                "level": "success" if registered else "info",
            }
        )
        return {"ok": True, "log": log, "result": {"servers": entries}}
    except Exception as exc:  # noqa: BLE001
        log.append({"msg": f"Error: {exc}", "level": "error"})
        return {"ok": False, "log": log, "result": None}


# ─── StevenBlack hosts (plugin_hosts_steven_black) ───────────────────────


def _handler_hosts_sb_import() -> HandlerResult:
    """Import the unified StevenBlack blocklist via HostsManager."""
    log: list[LogEntry] = []
    try:
        from winsvalinn.core import HostsManager

        result = HostsManager(callback=_collect_logger(log)).import_steven_black([])
        ok = bool(result.get("success", False))
        if not log:
            log.append(
                {
                    "msg": result.get("message", "StevenBlack imported"),
                    "level": "success" if ok else "warning",
                }
            )
        return {"ok": ok, "log": log, "result": result}
    except Exception as exc:  # noqa: BLE001
        log.append({"msg": f"Error: {exc}", "level": "error"})
        return {"ok": False, "log": log, "result": None}


def _handler_hosts_sb_remove() -> HandlerResult:
    """Remove the StevenBlack-managed block from the hosts file."""
    log: list[LogEntry] = []
    try:
        from winsvalinn.core import HostsManager

        result = HostsManager(callback=_collect_logger(log)).remove_steven_black()
        ok = bool(result.get("success", False))
        if not log:
            log.append(
                {
                    "msg": result.get("message", "StevenBlack removed"),
                    "level": "success" if ok else "warning",
                }
            )
        return {"ok": ok, "log": log, "result": result}
    except Exception as exc:  # noqa: BLE001
        log.append({"msg": f"Error: {exc}", "level": "error"})
        return {"ok": False, "log": log, "result": None}


# ─── O&O ShutUp10++ bridge (plugin_oo_shutup_bridge) ─────────────────────


def _handler_oosu_download() -> HandlerResult:
    """Download the official O&O ShutUp10++ binary via OOSUBridge."""
    log: list[LogEntry] = []
    try:
        from winsvalinn.core.oosu_bridge import OOSUBridge

        result = OOSUBridge(callback=_collect_logger(log)).download()
        ok = bool(result.get("success", False))
        if not log:
            log.append(
                {
                    "msg": result.get("message", "OOSU10 downloaded"),
                    "level": "success" if ok else "warning",
                }
            )
        return {"ok": ok, "log": log, "result": result}
    except Exception as exc:  # noqa: BLE001
        log.append({"msg": f"Error: {exc}", "level": "error"})
        return {"ok": False, "log": log, "result": None}


def _handler_oosu_launch() -> HandlerResult:
    """Launch O&O ShutUp10++ (downloads first if missing) via OOSUBridge."""
    log: list[LogEntry] = []
    try:
        from winsvalinn.core.oosu_bridge import OOSUBridge

        result = OOSUBridge(callback=_collect_logger(log)).launch()
        ok = bool(result.get("success", False))
        if not log:
            log.append(
                {
                    "msg": result.get("message", "OOSU10 launched"),
                    "level": "success" if ok else "warning",
                }
            )
        return {"ok": ok, "log": log, "result": result}
    except Exception as exc:  # noqa: BLE001
        log.append({"msg": f"Error: {exc}", "level": "error"})
        return {"ok": False, "log": log, "result": None}


# ─── Registration ────────────────────────────────────────────────────────

register(
    Option(
        id="doh_enable",
        section="privacy",
        label="Habilitar DNS over HTTPS",
        edition="free",
        description=(
            "Registra servidores DoH conocidos (Cloudflare, Google, Quad9, AdGuard) "
            "y los hace obligatorios. Requiere Windows 11 21H2+ o Server 2022."
        ),
        is_destructive=True,
        handler=_handler_doh_enable,
    )
)
register(
    Option(
        id="doh_disable",
        section="privacy",
        label="Deshabilitar DNS over HTTPS",
        edition="free",
        description="Desactiva DoH globalmente (EnableAutoDoh=0).",
        is_destructive=True,
        handler=_handler_doh_disable,
    )
)
register(
    Option(
        id="doh_status",
        section="privacy",
        label="Estado de DNS over HTTPS",
        edition="free",
        description="Comprueba qué servidores DoH conocidos están registrados (solo lectura).",
        is_destructive=False,
        handler=_handler_doh_status,
    )
)
register(
    Option(
        id="hosts_steven_black_import",
        section="privacy",
        label="Importar bloqueo StevenBlack",
        edition="free",
        description=(
            "Descarga e importa la lista unificada de StevenBlack (~200,000 dominios "
            "de ads/tracking). Hace backup del archivo hosts antes de modificarlo."
        ),
        is_destructive=True,
        handler=_handler_hosts_sb_import,
    )
)
register(
    Option(
        id="hosts_steven_black_remove",
        section="privacy",
        label="Eliminar bloqueo StevenBlack",
        edition="free",
        description="Quita solo el bloque gestionado por StevenBlack del archivo hosts.",
        is_destructive=True,
        handler=_handler_hosts_sb_remove,
    )
)
register(
    Option(
        id="oosu_download",
        section="privacy",
        label="Descargar O&O ShutUp10++",
        edition="free",
        description="Descarga el binario oficial OOSU10.exe en la carpeta de herramientas.",
        is_destructive=True,
        handler=_handler_oosu_download,
    )
)
register(
    Option(
        id="oosu_launch",
        section="privacy",
        label="Lanzar O&O ShutUp10++",
        edition="free",
        description=(
            "Lanza O&O ShutUp10++ (lo descarga primero si falta) para ajustes finos "
            "de privacidad de Windows."
        ),
        is_destructive=True,
        handler=_handler_oosu_launch,
    )
)
