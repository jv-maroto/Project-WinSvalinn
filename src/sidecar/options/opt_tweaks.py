"""
Native "tweaks" options — migrated from the legacy plugins:

* ``plugin_tweaks_ui``       → Windows 11 UI registry tweaks (per-tweak + all).
* ``plugin_developer``       → dev environment detect / cache / Defender / WSL.
* ``plugin_duplicates_finder`` → SHA-256 duplicate file scan.

Every action becomes an :class:`Option` with ``section="tweaks"`` and
``edition="free"``. Handlers take no arguments, never raise, and delegate to
the GUI-free engines in :mod:`winsvalinn.core`.
"""

from __future__ import annotations

from pathlib import Path

from sidecar.options import HandlerResult, Option, _collect_logger, register

# ─── UI tweaks (plugin_tweaks_ui) ────────────────────────────────────────


def _make_ui_tweak_handler(tweak_id: str):
    """Build a no-arg handler that applies a single UI tweak."""

    def _handler() -> HandlerResult:
        log: list[dict] = []
        try:
            from winsvalinn.core.ui_tweaks import UITweaks

            engine = UITweaks(callback=_collect_logger(log))
            result = engine.apply_tweaks([tweak_id])
            return {"ok": bool(result.get("success")), "log": log, "result": result}
        except Exception as exc:  # noqa: BLE001 - surfaced to user, never raised
            log.append({"msg": f"Error: {exc}", "level": "error"})
            return {"ok": False, "log": log, "result": None}

    return _handler


def _handler_ui_apply_all() -> HandlerResult:
    """Apply every Windows 11 UI tweak at once."""
    log: list[dict] = []
    try:
        from winsvalinn.core.ui_tweaks import UITweaks

        result = UITweaks(callback=_collect_logger(log)).apply_all()
        return {"ok": bool(result.get("success")), "log": log, "result": result}
    except Exception as exc:  # noqa: BLE001
        log.append({"msg": f"Error: {exc}", "level": "error"})
        return {"ok": False, "log": log, "result": None}


# ─── Developer environment (plugin_developer) ────────────────────────────


def _handler_dev_detect() -> HandlerResult:
    """Detect installed dev environments (read-only)."""
    log: list[dict] = []
    try:
        from winsvalinn.core.dev_tools import DevTools

        result = DevTools(callback=_collect_logger(log)).detect_environments()
        return {"ok": bool(result.get("success")), "log": log, "result": result}
    except Exception as exc:  # noqa: BLE001
        log.append({"msg": f"Error: {exc}", "level": "error"})
        return {"ok": False, "log": log, "result": None}


def _handler_dev_analyze_caches() -> HandlerResult:
    """Report sizes of known dev caches (read-only)."""
    log: list[dict] = []
    try:
        from winsvalinn.core.dev_tools import DevTools

        result = DevTools(callback=_collect_logger(log)).analyze_caches()
        return {"ok": bool(result.get("success")), "log": log, "result": result}
    except Exception as exc:  # noqa: BLE001
        log.append({"msg": f"Error: {exc}", "level": "error"})
        return {"ok": False, "log": log, "result": None}


def _handler_dev_clean_caches() -> HandlerResult:
    """Delete known dev caches (destructive)."""
    log: list[dict] = []
    try:
        from winsvalinn.core.dev_tools import DevTools

        result = DevTools(callback=_collect_logger(log)).clean_caches()
        return {"ok": bool(result.get("success")), "log": log, "result": result}
    except Exception as exc:  # noqa: BLE001
        log.append({"msg": f"Error: {exc}", "level": "error"})
        return {"ok": False, "log": log, "result": None}


def _handler_dev_defender_exclusions() -> HandlerResult:
    """Add dev folders to Defender exclusions (system change, needs admin)."""
    log: list[dict] = []
    try:
        from winsvalinn.core.dev_tools import DevTools

        result = DevTools(callback=_collect_logger(log)).configure_defender_exclusions()
        return {"ok": bool(result.get("success")), "log": log, "result": result}
    except Exception as exc:  # noqa: BLE001
        log.append({"msg": f"Error: {exc}", "level": "error"})
        return {"ok": False, "log": log, "result": None}


def _handler_dev_check_wsl_docker() -> HandlerResult:
    """Report WSL2 and Docker status (read-only)."""
    log: list[dict] = []
    try:
        from winsvalinn.core.dev_tools import DevTools

        result = DevTools(callback=_collect_logger(log)).check_wsl_docker()
        return {"ok": bool(result.get("success")), "log": log, "result": result}
    except Exception as exc:  # noqa: BLE001
        log.append({"msg": f"Error: {exc}", "level": "error"})
        return {"ok": False, "log": log, "result": None}


# ─── Duplicate finder (plugin_duplicates_finder) ─────────────────────────


def _handler_find_duplicates() -> HandlerResult:
    """Scan the user's Downloads folder for duplicate files (read-only)."""
    log: list[dict] = []
    try:
        from winsvalinn.core.duplicate_finder import DuplicateFinder

        folder = Path.home() / "Downloads"
        result = DuplicateFinder(callback=_collect_logger(log)).find_duplicates(folder)
        return {"ok": bool(result.get("success")), "log": log, "result": result}
    except Exception as exc:  # noqa: BLE001
        log.append({"msg": f"Error: {exc}", "level": "error"})
        return {"ok": False, "log": log, "result": None}


# ─── Registration ────────────────────────────────────────────────────────

# Per-tweak UI options. Each writes the registry and restarts Explorer, so they
# are destructive. Labels/ids mirror the legacy TWEAKS table.
_UI_TWEAKS = [
    ("start_left", "UI: Alinear menú Inicio a la izquierda"),
    ("hide_search", "UI: Ocultar barra de búsqueda en taskbar"),
    ("hide_widgets", "UI: Ocultar Widgets"),
    ("hide_taskview", "UI: Ocultar Task View"),
    ("hide_chat", "UI: Ocultar icono Chat (Teams)"),
    ("classic_context", "UI: Restaurar menú contextual clásico (Win10)"),
    ("show_extensions", "UI: Mostrar extensiones de archivo"),
    ("show_hidden", "UI: Mostrar archivos y carpetas ocultos"),
    ("disable_bing_search", "UI: Desactivar búsqueda Bing en menú Inicio"),
    ("small_taskbar", "UI: Taskbar más pequeña"),
]

for _tw_id, _tw_label in _UI_TWEAKS:
    register(
        Option(
            id=f"ui_tweak_{_tw_id}",
            section="tweaks",
            label=_tw_label,
            edition="free",
            description=f"Aplica el tweak de UI de Windows 11: {_tw_label[4:]}.",
            is_destructive=True,
            handler=_make_ui_tweak_handler(_tw_id),
        )
    )

register(
    Option(
        id="ui_tweaks_apply_all",
        section="tweaks",
        label="UI: Aplicar todos los tweaks de UI",
        edition="free",
        description="Aplica todos los tweaks de Inicio/Taskbar/Explorer y reinicia Explorer.",
        is_destructive=True,
        handler=_handler_ui_apply_all,
    )
)

register(
    Option(
        id="dev_detect_environments",
        section="tweaks",
        label="Dev: Detectar entornos de desarrollo",
        edition="free",
        description="Busca IDEs, runtimes y herramientas instaladas (solo lectura).",
        is_destructive=False,
        handler=_handler_dev_detect,
    )
)
register(
    Option(
        id="dev_analyze_caches",
        section="tweaks",
        label="Dev: Analizar cachés de desarrollo",
        edition="free",
        description="Calcula el tamaño de cachés de npm/pip/gradle/NuGet (solo lectura).",
        is_destructive=False,
        handler=_handler_dev_analyze_caches,
    )
)
register(
    Option(
        id="dev_clean_caches",
        section="tweaks",
        label="Dev: Limpiar cachés de desarrollo",
        edition="free",
        description="Elimina cachés de npm/pip/gradle/NuGet para liberar espacio.",
        is_destructive=True,
        handler=_handler_dev_clean_caches,
    )
)
register(
    Option(
        id="dev_defender_exclusions",
        section="tweaks",
        label="Dev: Exclusiones de Defender para carpetas dev",
        edition="free",
        description="Añade carpetas de desarrollo a las exclusiones de Defender (requiere admin).",
        is_destructive=True,
        handler=_handler_dev_defender_exclusions,
    )
)
register(
    Option(
        id="dev_check_wsl_docker",
        section="tweaks",
        label="Dev: Estado de WSL2 y Docker",
        edition="free",
        description="Comprueba el estado de WSL2 y Docker Desktop (solo lectura).",
        is_destructive=False,
        handler=_handler_dev_check_wsl_docker,
    )
)

register(
    Option(
        id="find_duplicates_downloads",
        section="tweaks",
        label="Buscar archivos duplicados (Descargas)",
        edition="free",
        description=(
            "Busca archivos duplicados por hash SHA-256 en la carpeta Descargas (solo lectura)."
        ),
        is_destructive=False,
        handler=_handler_find_duplicates,
    )
)
