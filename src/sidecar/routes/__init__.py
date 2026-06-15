"""
Auto-discovered FastAPI feature routers (Fase 3+).

Each sibling submodule that should expose endpoints defines a module-level
``router = APIRouter()`` with its routes. :func:`include_all` imports every
submodule (whose name does not start with ``_``) and mounts its router on the
app — so adding a feature is a drop-in file, no edits to ``app.py``.
"""

from __future__ import annotations

import importlib
import pkgutil

from fastapi import FastAPI


def include_all(app: FastAPI) -> None:
    """Discover sibling submodules and mount each one's ``router`` on ``app``."""
    for mod in pkgutil.iter_modules(__path__):
        if mod.name.startswith("_"):
            continue
        module = importlib.import_module(f"{__name__}.{mod.name}")
        router = getattr(module, "router", None)
        if router is not None:
            app.include_router(router)
