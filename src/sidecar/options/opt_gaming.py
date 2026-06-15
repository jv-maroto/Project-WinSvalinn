"""
Native "gaming" option group.

Migrates the legacy filesystem plugins ``plugin_gaming``, ``plugin_lol`` and
``plugin_streaming`` to native :class:`~sidecar.options.Option` entries. Each
user action becomes a free option in the ``gaming`` section, backed by the
:class:`~winsvalinn.core.game_optimizer.GameOptimizer` engine.

Handlers never raise: every failure is captured into the normalized result
``{"ok": bool, "log": [...], "result": Any}``.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sidecar.options import HandlerResult, LogEntry, Option, _collect_logger, register


def _run(method_name: str) -> HandlerResult:
    """Instantiate GameOptimizer and invoke ``method_name``, collecting logs."""
    log: list[LogEntry] = []
    try:
        from winsvalinn.core.game_optimizer import GameOptimizer

        optimizer = GameOptimizer(callback=_collect_logger(log))
        result: Any = getattr(optimizer, method_name)()
        ok = bool(result.get("success", True)) if isinstance(result, dict) else True
        return {"ok": ok, "log": log, "result": result}
    except Exception as exc:  # noqa: BLE001 - surfaced to the user, never raised
        log.append({"msg": f"Error: {exc}", "level": "error"})
        return {"ok": False, "log": log, "result": None}


def _handler(method_name: str) -> Callable[[], HandlerResult]:
    """Build a zero-argument handler bound to a GameOptimizer method."""
    return lambda: _run(method_name)


# id, label, method, is_destructive, description
_SPECS: tuple[tuple[str, str, str, bool, str], ...] = (
    # ── Generic gaming (plugin_gaming) ──────────────────────────────────
    (
        "gaming_detect_platforms",
        "Detectar plataformas de juego",
        "detect_platforms",
        False,
        "Busca plataformas instaladas (Steam, Epic, GOG, Xbox, EA, Ubisoft).",
    ),
    (
        "gaming_kill_background",
        "Cerrar procesos en segundo plano",
        "kill_background",
        True,
        "Cierra procesos no esenciales (OneDrive, Teams, Discord, etc.) para liberar recursos.",
    ),
    (
        "gaming_game_mode",
        "Activar Game Mode y GPU Scheduling",
        "enable_game_mode",
        True,
        "Habilita el Modo Juego de Windows y la planificacion de GPU por hardware.",
    ),
    (
        "gaming_clean_shaders",
        "Limpiar caché de shaders",
        "clean_shader_cache",
        True,
        "Borra las cachés de shaders de DirectX, NVIDIA y AMD para forzar su regeneracion.",
    ),
    (
        "gaming_optimize_network",
        "Optimizar red para juego",
        "optimize_network",
        True,
        "Desactiva el algoritmo de Nagle en cada interfaz y maximiza el Network Throttling Index.",
    ),
    (
        "gaming_ultimate_power",
        "Activar plan Ultimate Performance",
        "enable_ultimate_performance",
        True,
        "Crea y activa el plan de energia oculto Ultimate Performance.",
    ),
    (
        "gaming_apply_all",
        "Aplicar perfil gaming completo",
        "apply_gaming_profile",
        True,
        "Aplica todas las optimizaciones gaming: procesos, Game Mode, red, energia y shaders.",
    ),
    # ── League of Legends (plugin_lol) ──────────────────────────────────
    (
        "gaming_lol_priority",
        "LoL: prioridad de juego",
        "apply_game_priority",
        True,
        "Configura la tarea multimedia 'Games' con prioridad alta y prioridad de GPU.",
    ),
    (
        "gaming_lol_display",
        "LoL: optimizaciones de pantalla",
        "apply_lol_display",
        True,
        "Desactiva optimizaciones de pantalla completa y aplica High DPI a los ejecutables de LoL.",
    ),
    (
        "gaming_lol_client",
        "LoL: ajustes del cliente",
        "apply_lol_client_settings",
        True,
        "Activa Low Spec Mode y Cerrar Cliente Durante Partida en PersistedSettings.json.",
    ),
    (
        "gaming_lol_apply_all",
        "LoL: aplicar perfil completo",
        "apply_lol_profile",
        True,
        "Aplica todas las optimizaciones de League of Legends: red, prioridad, pantalla y cliente.",
    ),
    # ── Streaming / OBS (plugin_streaming) ──────────────────────────────
    (
        "gaming_obs_priority",
        "OBS: prioridad de CPU",
        "apply_obs_priority",
        True,
        "Sube la prioridad de CPU de obs64.exe a Above Normal via registro IFEO.",
    ),
    (
        "gaming_obs_encoder",
        "OBS: recomendar encoder",
        "detect_encoder",
        False,
        "Detecta la GPU y recomienda el encoder OBS adecuado (solo lectura).",
    ),
    (
        "gaming_obs_dynamic_bitrate",
        "OBS: bitrate dinamico",
        "apply_obs_dynamic_bitrate",
        True,
        "Habilita Dynamic Bitrate en la configuracion global de OBS Studio.",
    ),
    (
        "gaming_kill_overlays",
        "Cerrar overlays de streaming",
        "kill_overlays",
        True,
        "Cierra overlays (Discord, NVIDIA, Steam) que pueden causar caidas de FPS.",
    ),
    (
        "gaming_streaming_apply_all",
        "Streaming: aplicar perfil completo",
        "apply_streaming_profile",
        True,
        "Aplica todas las optimizaciones de streaming: OBS, red, energia y Game Mode.",
    ),
)


for _id, _label, _method, _destructive, _desc in _SPECS:
    register(
        Option(
            id=_id,
            section="gaming",
            label=_label,
            edition="free",
            description=_desc,
            is_destructive=_destructive,
            handler=_handler(_method),
            meta={"engine": "GameOptimizer", "method": _method},
        )
    )
