# Adding a Native Option

> The legacy filesystem plugin system (`PLUGIN_INFO` dict + `Plugin` class loaded from a
> `plugins/` directory) has been **removed**. Functionality is now exposed through the
> **native options registry** in `src/sidecar/options/`. This guide explains how to add a
> new option.

## What an Option Is

An *option* is a single, GUI-free user action backed by an engine in `winsvalinn.core`.
Each option carries metadata and a zero-argument `handler` that performs the work and returns
a normalized result. Options are exposed over the FastAPI sidecar via:

- `GET  /options` (optional `?section=`) — list option metadata
- `POST /options/{id}/run` — run an option (edition-gated)

The React frontend renders options per section and calls `optionRun(id)`.

## Where Options Live

```
src/sidecar/options/
├── __init__.py        # Option dataclass + register/list/get/run + auto-discovery
├── opt_gaming.py      # one submodule per option group
├── opt_privacy.py
├── opt_hardening.py
├── opt_audit_system.py
├── opt_threat.py
└── opt_<your_group>.py
```

Every `opt_*.py` submodule calls `register(Option(...))` at import time. The package
auto-discovers all sibling submodules on load, so **adding a group is a drop-in file** — no
edits to `__init__.py` are required.

## The `Option` Dataclass

```python
@dataclass
class Option:
    id: str               # unique, e.g. "hardening_disable_smbv1"
    section: str          # "gaming" | "tweaks" | "privacy" | "optimization"
                          # | "security" | "hardening" | "audit" | "threat"
    label: str            # user-facing label (Spanish by default)
    edition: str          # "free" | "empresarial"
    description: str      # short explanation shown in the UI
    is_destructive: bool  # True if it changes system state
    handler: Callable[[], HandlerResult]
    meta: dict = {}       # optional extra metadata
```

`empresarial` options require a valid license; gating is enforced by the API layer
(`POST /options/{id}/run` returns HTTP 402 when locked). The handler itself is not
responsible for gating.

## The Handler Contract

A handler takes **no arguments** and **never raises**. It returns:

```python
{
    "ok": bool,                                   # did the action succeed?
    "log": [{"msg": str, "level": str}, ...],     # level: info|success|warning|error
    "result": Any,                                # JSON-safe payload (optional)
}
```

Reuse an existing `winsvalinn.core` engine and wire its callback to the option's log via
the `_collect_logger` helper. Catch all exceptions and fold them into the log/`ok` fields.

## Minimal Example

```python
# src/sidecar/options/opt_example.py
"""Example option group."""

from __future__ import annotations

from sidecar.options import HandlerResult, LogEntry, Option, _collect_logger, register


def _handler_example_status() -> HandlerResult:
    """Read-only status check (free)."""
    log: list[LogEntry] = []
    try:
        from winsvalinn.core import SomeEngine

        result = SomeEngine(callback=_collect_logger(log)).get_summary()
        return {"ok": True, "log": log, "result": result}
    except Exception as exc:  # noqa: BLE001 - surfaced to the user, never raised
        log.append({"msg": f"Error: {exc}", "level": "error"})
        return {"ok": False, "log": log, "result": None}


register(Option(
    id="example_status",
    section="audit",
    label="Comprobar estado de ejemplo",
    edition="free",
    description="Devuelve un resumen de solo lectura del subsistema de ejemplo.",
    is_destructive=False,
    handler=_handler_example_status,
))
```

## Conventions

- **No GUI imports** anywhere in the option modules or the core engines they call.
- **Reuse, don't duplicate**: instantiate an existing `winsvalinn.core` engine with
  `callback=_collect_logger(log)` and call its public method. Do not re-implement logic.
- **`subprocess` must use `shell=False`**; catch specific exceptions.
- Mark anything that changes system state with `is_destructive=True`.
- Keep `id` globally unique across all sections.

## Testing

Add a test under `tests/` (e.g. `tests/<group>_test.py`) that imports
`from sidecar import options` and asserts your option ids are registered with the expected
`section`, `edition`, and `is_destructive` flags. Tests should verify **registration only** —
do not execute handlers (they touch the real system). Mock `psutil`/`subprocess`/`winreg`
if you need to exercise a handler.

Run the suite before committing:

```bash
pytest
```
