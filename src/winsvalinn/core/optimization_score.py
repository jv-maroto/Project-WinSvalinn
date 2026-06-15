"""Optimization score based on which tweaks are actually applied.

The previous score was ``(100 - %RAM) * .55 + (100 - %disk) * .45`` — a snapshot
of live resource usage that never moved when the user applied optimizations.
This module reads the *real system state* of each detectable optimization and
scores the share that are active, so applying tweaks raises the number and the
per-item breakdown shows exactly what is left to do.

All checks are read-only and Windows-only; on other platforms or when a value
can't be read, an item is simply reported as not applied.
"""

from __future__ import annotations

# Power-plan names (any locale fragment) that count as a performance plan.
_PERF_PLAN_HINTS = (
    "high perf",
    "ultimate",
    "alto rendi",
    "máximo rendi",
    "maximo rendi",
)


def _ui_tweaks_status() -> list[dict]:
    """Per-tweak applied state for the Windows 11 UI tweaks."""
    try:
        from winsvalinn.core.ui_tweaks import UITweaks

        return UITweaks().get_status()
    except Exception:  # noqa: BLE001 - never let one source break the score
        return []


def _perf_status() -> list[dict]:
    """Applied state for the heavier performance optimizations."""
    items: list[dict] = []
    try:
        from winsvalinn.core.optimization import SystemOptimizer

        opt = SystemOptimizer()

        try:
            mode = (opt.get_visual_effects_status() or {}).get("current_mode")
            items.append(
                {
                    "id": "visual_effects_performance",
                    "label": "Efectos visuales en modo rendimiento",
                    "applied": mode == "Best performance",
                }
            )
        except Exception:  # noqa: BLE001
            pass

        try:
            plans = opt.get_power_plans() or []
            active = next((p for p in plans if p.get("active")), None)
            name = (active or {}).get("name", "").lower()
            items.append(
                {
                    "id": "power_plan_performance",
                    "label": "Plan de energía de alto rendimiento",
                    "applied": any(hint in name for hint in _PERF_PLAN_HINTS),
                }
            )
        except Exception:  # noqa: BLE001
            pass
    except Exception:  # noqa: BLE001
        pass
    return items


def compute(include_breakdown: bool = True) -> dict:
    """
    Compute the optimization score from applied tweaks.

    Returns ``{"score", "applied", "total"[, "items"]}`` where ``score`` is the
    percentage of detectable optimizations currently active.
    """
    items = _ui_tweaks_status() + _perf_status()
    total = len(items)
    applied = sum(1 for it in items if it.get("applied"))
    score = int(round(applied / total * 100)) if total else 0
    out: dict = {"score": score, "applied": applied, "total": total}
    if include_breakdown:
        out["items"] = items
    return out
