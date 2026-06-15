"""
WinSvalinn FastAPI sidecar.

Endpoints (all return JSON):
  GET  /health                 — liveness check
  GET  /system/health          — score + cpu/ram/disk
  GET  /system/info            — OS, processor, memory totals
  GET  /security/audit         — full security scan + score (slow ~10-30s)
  GET  /security/ports         — open ports with risk classification
  GET  /security/processes     — suspicious processes heuristic
  GET  /optimization/score     — RAM+Disk-based optimization score
  POST /optimization/{action}  — apply: ram | gpu | visual | network | ssd | power
  GET  /memory/stats           — RAM totals + top 25 processes
  POST /memory/free            — free RAM (returns before/after)
  GET  /processes/tree         — full parent-child process tree
  GET  /network/connections    — top 150 active connections (cached PIDs)
  GET  /cleanup/analyze        — temp file locations + sizes
  POST /cleanup/clean          — clean temp files
  GET  /config                 — read user config
  PATCH /config                — update config keys
  GET  /license                — active edition + license status
  POST /license/activate       — validate + persist a license key
  POST /license/deactivate     — clear the saved license (back to free)
  POST /processes/{pid}/kill   — terminate a process by PID
  GET  /security/remediations  — controls we can auto-fix or navigate to
  POST /security/remediate/{control} — apply a safe remediation for a control
  GET  /options                — native options registry (optional ?section=)
  POST /options/{id}/run       — run a native option (edition-gated)
"""

import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Make winsvalinn importable when this is run as `python -m sidecar`
_HERE = Path(__file__).resolve().parent
_SRC = _HERE.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


app = FastAPI(title="WinSvalinn Sidecar", version="1.0.0")


@app.on_event("startup")
def _warmup() -> None:
    """Pre-warm the slow first process enumeration in the background.

    The packaged exe imports ``winsvalinn.core`` lazily and the very first
    ``psutil`` sweep pays the OS handle-cache cost, which made the first
    Processes view load take several seconds. Doing one sweep at startup (off
    the request path) means the user's first navigation is already warm.
    """
    import threading

    def _run() -> None:
        try:
            from winsvalinn.core import process_tree

            process_tree.build_process_tree()
        except Exception:
            pass

    threading.Thread(target=_run, daemon=True).start()

# The sidecar only serves the local Tauri app. Lock CORS to the app origins
# (not "*") so a web page can't read its responses cross-origin.
_ALLOWED_ORIGINS = [
    "tauri://localhost",
    "http://tauri.localhost",
    "https://tauri.localhost",
    "http://127.0.0.1:1420",  # Vite dev server
    "http://localhost:1420",
]
_ALLOWED_HOSTS = {"127.0.0.1", "localhost"}
_MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def _local_guard(request: Request, call_next):
    """Block DNS-rebinding (bad Host) and cross-site CSRF (missing app header)."""
    host = (request.headers.get("host") or "").split(":")[0]
    # FastAPI TestClient uses host "testserver"; browsers cannot spoof the Host
    # header, so exempting it is safe against the web/DNS-rebinding threat.
    if host == "testserver":
        return await call_next(request)
    if host and host not in _ALLOWED_HOSTS:
        return JSONResponse({"detail": "forbidden host"}, status_code=403)
    # Mutating requests must carry the app's custom header. A web page can't set
    # it cross-origin without a preflight, which the strict CORS above rejects.
    if request.method in _MUTATING_METHODS and request.headers.get("x-wsv-client") != "winsvalinn":
        return JSONResponse({"detail": "missing client header"}, status_code=403)
    return await call_next(request)


# Feature routers (Fase 3+) are auto-discovered from sidecar.routes/*.py
from sidecar import routes as _routes  # noqa: E402

_routes.include_all(app)


# ─── Lazy imports ───────────────────────────────────────────────────────


def _scanner():
    from winsvalinn.core import SecurityScanner

    return SecurityScanner()


def _audit():
    from winsvalinn.core import SecurityAudit

    return SecurityAudit()


def _ram():
    from winsvalinn.core import RAMOptimizer

    return RAMOptimizer()


def _gpu():
    from winsvalinn.core import GPUBrandOptimizer

    return GPUBrandOptimizer()


def _sys_optimizer():
    from winsvalinn.core import SystemOptimizer

    return SystemOptimizer()


# ─── Generic ────────────────────────────────────────────────────────────


@app.get("/health")
def health():
    return {"ok": True, "version": "1.0.0"}


@app.get("/system/info")
def system_info():
    import platform

    from winsvalinn.core.game_library import is_admin

    out = {
        "os": f"{platform.system()} {platform.release()}",
        "version": platform.version(),
        "processor": platform.processor(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "is_admin": is_admin(),
    }
    try:
        import psutil

        vm = psutil.virtual_memory()
        out["ram_total_gb"] = round(vm.total / (1024**3), 1)
        out["cpu_logical"] = psutil.cpu_count(logical=True)
        out["cpu_physical"] = psutil.cpu_count(logical=False)
    except Exception:
        pass
    return out


@app.get("/system/health")
def system_health():
    """Quick non-blocking CPU/RAM/Disk + computed health score."""
    import psutil

    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory().percent
    try:
        disk = psutil.disk_usage("C:\\").percent
    except Exception:
        disk = 0
    score = max(0, min(100, int((100 - cpu) * 0.30 + (100 - ram) * 0.45 + (100 - disk) * 0.25)))
    try:
        connections = len(psutil.net_connections(kind="inet"))
    except Exception:
        connections = 0
    return {
        "cpu": round(cpu, 1),
        "ram": round(ram, 1),
        "disk": round(disk, 1),
        "score": score,
        "connections": connections,
    }


# ─── Security ───────────────────────────────────────────────────────────


_audit_cache: dict = {"ts": 0.0, "data": None}
_AUDIT_TTL = 90.0  # seconds


@app.get("/security/audit")
def security_audit(refresh: bool = False):
    """Full security scan. Cached for 90s so re-opening the view is instant."""
    import time

    now = time.monotonic()
    if not refresh and _audit_cache["data"] is not None and (now - _audit_cache["ts"]) < _AUDIT_TTL:
        return _audit_cache["data"]
    try:
        data = _audit().run_security_scan() or {}
    except Exception as exc:
        raise HTTPException(500, str(exc))
    _audit_cache["data"] = data
    _audit_cache["ts"] = now
    return data


@app.get("/security/ports")
def security_ports():
    try:
        ports = _scanner().scan_external_ports() or []
        return {"ports": ports[:100]}
    except Exception as exc:
        raise HTTPException(500, str(exc))


@app.get("/security/processes")
def security_processes():
    try:
        procs = _scanner().analyze_processes() or []
        return {"processes": procs[:50]}
    except Exception as exc:
        raise HTTPException(500, str(exc))


# ─── Optimization ───────────────────────────────────────────────────────


@app.get("/optimization/score")
def optimization_score():
    """Score = share of detectable optimizations actually applied.

    Includes a per-item breakdown (what's left to apply). RAM/disk usage is
    still reported as context, but no longer drives the score.
    """
    import psutil

    from winsvalinn.core import optimization_score as optscore

    data = optscore.compute()
    ram = psutil.virtual_memory().percent
    try:
        disk = psutil.disk_usage("C:\\").percent
    except Exception:
        disk = 0
    data["ram"] = round(ram, 1)
    data["disk"] = round(disk, 1)
    return data


@app.post("/optimization/{action}")
def optimization_apply(action: str):
    try:
        opt = _sys_optimizer()
        if action == "ram":
            return _ram().free_ram()
        if action == "gpu":
            return _gpu().auto_optimize()
        if action == "visual":
            return opt.optimize_visual_effects()
        if action == "network":
            return opt.optimize_network()
        if action == "ssd":
            return opt.optimize_ssd()
        if action == "power":
            return {"plans": opt.get_power_plans() or []}
        if action == "tweaks":
            return opt.apply_performance_tweaks()
        if action == "ultimate":
            from winsvalinn.core.game_optimizer import GameOptimizer

            return GameOptimizer().enable_ultimate_performance()
        raise HTTPException(404, f"Unknown action: {action}")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, str(exc))


class UiTweaksApply(BaseModel):
    ids: list[str]
    restart: bool = False


@app.post("/optimization/uitweaks")
def optimization_uitweaks(body: UiTweaksApply):
    """Apply specific Windows-11 UI tweaks. ``restart`` restarts Explorer once."""
    from winsvalinn.core.ui_tweaks import UITweaks

    try:
        return UITweaks().apply_tweaks(body.ids, restart=body.restart)
    except Exception as exc:
        raise HTTPException(500, str(exc))


@app.get("/optimization/gpu/plan")
def optimization_gpu_plan():
    """Detected GPU brand + the tweaks it would apply (for the checkbox dropdown)."""
    return _gpu().plan()


class GpuApply(BaseModel):
    selected: list[str] | None = None


@app.post("/optimization/gpu/apply")
def optimization_gpu_apply(body: GpuApply):
    """Apply only the selected GPU tweaks (or all if ``selected`` is null)."""
    try:
        return _gpu().apply_selected(body.selected)
    except Exception as exc:
        raise HTTPException(500, str(exc))


# ─── Unified selectable optimization groups (GPU-style cards) ─────────────


@app.get("/optimization/plan/{group}")
def optimization_plan(group: str):
    """Per-tweak plan (with applied-state) for any optimization group."""
    if group == "gpu":
        p = _gpu().plan()
        return {
            "title": f"GPU · {p['brand']}",
            "subtitle": p.get("gpu_name"),
            "tweaks": [{**t, "applied": None} for t in p["tweaks"]],
        }
    if group == "ui_tweaks":
        from winsvalinn.core.ui_tweaks import UITweaks

        return {
            "title": "Tweaks de interfaz (UI)",
            "tweaks": UITweaks().get_status(),
            "restart": True,
        }
    if group == "power":
        from winsvalinn.core.game_library import _ultimate_active

        return {
            "title": "Plan de energía",
            "tweaks": [
                {
                    "id": "ultimate",
                    "label": "Plan Ultimate Performance",
                    "applied": _ultimate_active(),
                }
            ],
        }
    from winsvalinn.core import optimization_groups

    return optimization_groups.plan(group)


class GroupApply(BaseModel):
    selected: list[str] | None = None
    restart: bool = True


@app.post("/optimization/apply/{group}")
def optimization_apply_group(group: str, body: GroupApply):
    """Apply the selected tweaks of an optimization group."""
    try:
        if group == "gpu":
            return _gpu().apply_selected(body.selected)
        if group == "ui_tweaks":
            from winsvalinn.core.ui_tweaks import TWEAKS, UITweaks

            ids = body.selected if body.selected is not None else list(TWEAKS)
            return UITweaks().apply_tweaks(ids, restart=body.restart)
        if group == "power":
            from winsvalinn.core.game_optimizer import GameOptimizer

            return GameOptimizer().enable_ultimate_performance()
        from winsvalinn.core import optimization_groups

        return optimization_groups.apply(group, body.selected)
    except Exception as exc:
        raise HTTPException(500, str(exc))


# ─── Games (per-game optimization) ───────────────────────────────────────


@app.get("/games")
def games_list():
    """Detect installed games (Steam/Riot/standalone) with their profiles."""
    from winsvalinn.core import game_library

    return game_library.detect_games()


class GameOptimize(BaseModel):
    game_id: str


@app.post("/games/optimize")
def games_optimize(body: GameOptimize):
    """Apply the recommended (universal) profile for a detected game."""
    from winsvalinn.core import game_library

    return game_library.optimize_game(body.game_id)


class GameAction(BaseModel):
    game_id: str
    action: str


@app.post("/games/action")
def games_action(body: GameAction):
    """Run a single optimization action against a detected game."""
    from winsvalinn.core import game_library

    return game_library.run_action(body.game_id, body.action)


class GlobalAction(BaseModel):
    action: str


@app.post("/games/global")
def games_global(body: GlobalAction):
    """Run a system-wide gaming optimization (no game selected)."""
    from winsvalinn.core import game_library

    return game_library.run_global_action(body.action)


# ─── Run as Administrator ─────────────────────────────────────────────────


@app.get("/admin/status")
def admin_status():
    """Elevation status + whether 'always launch as admin' is set."""
    from winsvalinn.core import admin

    return admin.status()


class AlwaysAdmin(BaseModel):
    enabled: bool


@app.post("/admin/always")
def admin_always(body: AlwaysAdmin):
    """Enable/disable always-launch-as-Administrator for the app."""
    from winsvalinn.core import admin

    return admin.set_always_admin(body.enabled)


# ─── Memory ─────────────────────────────────────────────────────────────


@app.get("/memory/stats")
def memory_stats():
    import psutil

    vm = psutil.virtual_memory()
    procs = []
    for p in psutil.process_iter(["pid", "name", "memory_info"]):
        try:
            rss = p.info["memory_info"].rss / (1024 * 1024)
            procs.append(
                {
                    "pid": p.info["pid"],
                    "name": p.info["name"] or "?",
                    "memory_mb": round(rss, 1),
                }
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    procs.sort(key=lambda x: -x["memory_mb"])
    return {
        "total_gb": round(vm.total / (1024**3), 1),
        "used_gb": round(vm.used / (1024**3), 1),
        "available_gb": round(vm.available / (1024**3), 1),
        "percent": round(vm.percent, 1),
        "top_processes": procs[:30],
    }


@app.post("/memory/free")
def memory_free():
    import psutil

    before = psutil.virtual_memory().percent
    res = _ram().free_ram()
    after = psutil.virtual_memory().percent
    return {
        "result": res,
        "before_percent": round(before, 1),
        "after_percent": round(after, 1),
        "delta_percent": round(before - after, 1),
    }


# ─── Processes ──────────────────────────────────────────────────────────


@app.get("/processes/tree")
def processes_tree():
    from winsvalinn.core import process_tree

    return {"roots": process_tree.build_process_tree()}


# ─── Network ────────────────────────────────────────────────────────────


@app.get("/network/connections")
def network_connections():
    import psutil

    SUSPICIOUS_PORTS = {4444, 5555, 6666, 7777, 1337, 31337}
    PRIVATE = (
        "10.",
        "172.16.",
        "172.17.",
        "172.18.",
        "172.19.",
        "172.20.",
        "172.21.",
        "172.22.",
        "172.23.",
        "172.24.",
        "172.25.",
        "172.26.",
        "172.27.",
        "172.28.",
        "172.29.",
        "172.30.",
        "172.31.",
        "192.168.",
        "127.",
    )
    try:
        raw = list(psutil.net_connections(kind="inet"))
    except (PermissionError, psutil.AccessDenied):
        raise HTTPException(403, "Run as Administrator to enumerate connections")

    pid_names = {}
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            pid_names[proc.info["pid"]] = proc.info["name"] or "N/A"
        except Exception:
            pass

    rows = []
    for c in raw:
        laddr = f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "—"
        raddr = f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else "—"
        port = c.raddr.port if c.raddr else 0
        ip = c.raddr.ip if c.raddr else ""
        suspicious = (port in SUSPICIOUS_PORTS) or (
            bool(c.raddr)
            and not any(ip.startswith(p) for p in PRIVATE)
            and c.status == "ESTABLISHED"
            and port not in (80, 443, 53)
        )
        rows.append(
            {
                "pid": c.pid or 0,
                "process": pid_names.get(c.pid, "—") if c.pid else "—",
                "local": laddr,
                "remote": raddr,
                "status": c.status if hasattr(c, "status") else "—",
                "type": "TCP" if c.type == 1 else "UDP",
                "suspicious": suspicious,
            }
        )
    rows.sort(key=lambda r: (0 if r["suspicious"] else 1, 0 if r["status"] == "ESTABLISHED" else 1))
    return {"total": len(rows), "connections": rows[:150]}


# ─── Cleanup ────────────────────────────────────────────────────────────


@app.get("/cleanup/analyze")
def cleanup_analyze():
    return _sys_optimizer().analyze_temp_files()


@app.post("/cleanup/clean")
def cleanup_clean():
    return _sys_optimizer().clean_temp_files()


class DuplicateScan(BaseModel):
    folder: str = ""
    min_mb: float = 1.0


@app.post("/cleanup/duplicates")
def cleanup_duplicates(body: DuplicateScan):
    """Scan a folder (default: Downloads) for duplicate files by hash."""
    from pathlib import Path

    from winsvalinn.core.duplicate_finder import DuplicateFinder

    folder = body.folder.strip() or str(Path.home() / "Downloads")
    try:
        result = DuplicateFinder().find_duplicates(folder, min_mb=body.min_mb)
        result["folder"] = folder
        return result
    except Exception as exc:
        raise HTTPException(500, str(exc))


# ─── Config ─────────────────────────────────────────────────────────────


@app.get("/config")
def config_get():
    from winsvalinn.config import get_config

    return get_config().data


class ConfigPatch(BaseModel):
    keys: list  # e.g. ["ui", "theme"]
    value: object


@app.patch("/config")
def config_patch(patch: ConfigPatch):
    from winsvalinn.config import get_config

    cfg = get_config()
    cfg.set(*patch.keys, value=patch.value)
    cfg.save()
    return {"ok": True, "data": cfg.data}


# ─── Licensing ──────────────────────────────────────────────────────────


@app.get("/license")
def license_get():
    """Return the active edition resolved from the saved license."""
    from winsvalinn.core import licensing

    return licensing.current_edition()


class LicenseActivate(BaseModel):
    key: str


@app.post("/license/activate")
def license_activate(body: LicenseActivate):
    """
    Validate a license key and, if valid, persist it.

    Always returns HTTP 200. On invalid keys: ok=false, valid=false,
    edition="free", plus an `error` message.
    """
    from winsvalinn.core import licensing

    resolved = licensing.resolve_edition(body.key)
    if not resolved["valid"]:
        return {
            "ok": False,
            "error": "invalid_or_expired",
            **resolved,
        }

    try:
        licensing.save_license(body.key)
    except OSError as exc:
        return {"ok": False, "error": f"could_not_save: {exc}", **resolved}

    return {"ok": True, **resolved}


@app.post("/license/deactivate")
def license_deactivate():
    """Clear the saved license and revert to the free edition."""
    from winsvalinn.core import licensing

    licensing.clear_license()
    return {
        "ok": True,
        "edition": "free",
        "tier": None,
        "valid": False,
        "expiry": None,
        "email": None,
    }


# ─── Process control ────────────────────────────────────────────────────


@app.post("/processes/{pid}/kill")
def process_kill(pid: int):
    """Terminate a process by PID. 404 if missing, 403 if access denied."""
    import psutil

    try:
        proc = psutil.Process(pid)
        proc.terminate()
        return {"ok": True, "pid": pid}
    except psutil.NoSuchProcess:
        raise HTTPException(404, f"No process with PID {pid}")
    except psutil.AccessDenied:
        raise HTTPException(403, "Access denied — run as Administrator")
    except Exception as exc:
        return {"ok": False, "pid": pid, "error": str(exc)}


# ─── Security remediation ────────────────────────────────────────────────
#
# Maps the control identifiers emitted by SecurityAudit.run_security_scan()
# to safe, reusable remediations from winsvalinn.core. Controls with no safe
# automatic fix are exposed as "navigate" so the UI can deep-link instead.


def _remediate_defender():
    log: list = []
    from winsvalinn.core import DefenderControl

    res = DefenderControl(
        callback=lambda m, lvl="info": log.append(_norm_log(m, lvl))
    ).enable_real_time_protection()
    return res.get("success", False), log, res


def _remediate_firewall():
    log: list = []
    from winsvalinn.core import FirewallManager

    res = FirewallManager(
        callback=lambda m, lvl="info": log.append(_norm_log(m, lvl))
    ).enable_firewall("allprofiles")
    return res.get("success", False), log, res


def _remediate_autorun():
    log: list = []
    from winsvalinn.core import SecurityHardening

    res = SecurityHardening(
        callback=lambda m, lvl="info": log.append(_norm_log(m, lvl))
    ).disable_autorun()
    return res.get("success", False), log, res


def _remediate_rdp():
    log: list = []
    from winsvalinn.core import SecurityHardening

    res = SecurityHardening(
        callback=lambda m, lvl="info": log.append(_norm_log(m, lvl))
    ).disable_rdp()
    return res.get("success", False), log, res


def _remediate_smbv1():
    log: list = []
    from winsvalinn.core import SecurityHardening

    res = SecurityHardening(
        callback=lambda m, lvl="info": log.append(_norm_log(m, lvl))
    ).disable_smbv1()
    return res.get("success", False), log, res


def _norm_log(msg, level="info"):
    lvl = (level or "info").lower()
    if lvl in ("ok", "success"):
        lvl = "success"
    elif lvl in ("err", "error"):
        lvl = "error"
    elif lvl in ("warn", "warning"):
        lvl = "warning"
    elif lvl not in ("info", "success", "warning", "error"):
        lvl = "info"
    return {"msg": str(msg), "level": lvl}


# control -> (label, kind, section, fixer)
# kind "fix": fixer returns (ok, log, result). kind "navigate": no auto-fix.
_REMEDIATIONS = {
    "defender": (
        "Activar protección en tiempo real de Windows Defender",
        "fix",
        "security",
        _remediate_defender,
    ),
    "firewall": (
        "Activar el Firewall de Windows en todos los perfiles",
        "fix",
        "security",
        _remediate_firewall,
    ),
    "autorun": (
        "Deshabilitar AutoRun/AutoPlay (malware USB)",
        "fix",
        "security",
        _remediate_autorun,
    ),
    "rdp": ("Deshabilitar Escritorio Remoto (RDP)", "fix", "security", _remediate_rdp),
    "smbv1": ("Deshabilitar SMBv1 (vulnerable a WannaCry)", "fix", "security", _remediate_smbv1),
    # No safe one-click auto-fix — deep-link to the relevant view instead.
    "uac": ("Revisar la configuración de UAC", "navigate", "security", None),
    "bitlocker": ("Configurar el cifrado BitLocker", "navigate", "security", None),
    "secure_boot": ("Habilitar Secure Boot en BIOS/UEFI", "navigate", "security", None),
    "updates": ("Revisar Windows Update", "navigate", "security", None),
}


@app.get("/security/remediations")
def security_remediations():
    """List the security controls we can auto-fix or navigate to."""
    from winsvalinn.core.game_library import is_admin

    items = []
    for control, (label, kind, section, _fixer) in _REMEDIATIONS.items():
        items.append(
            {
                "control": control,
                "label": label,
                "kind": kind,
                "section": section,
                "needs_admin": kind == "fix",
            }
        )
    return {"items": items, "is_admin": is_admin()}


@app.post("/security/remediate/{control}")
def security_remediate(control: str):
    """Apply a safe remediation for the given control, or return a navigate hint."""
    entry = _REMEDIATIONS.get(control)
    if entry is None:
        raise HTTPException(404, f"Unknown control: {control}")

    label, kind, section, fixer = entry
    from winsvalinn.core.game_library import is_admin as _is_admin

    elevated = _is_admin()

    if kind == "navigate" or fixer is None:
        return {
            "ok": False,
            "control": control,
            "log": [{"msg": f"{label}: requiere acción manual", "level": "info"}],
            "navigate": section,
            "error": "manual",
            "is_admin": elevated,
        }

    # Every auto-fix writes to HKLM / runs elevated tools, so it needs admin.
    # Say so clearly instead of failing with a cryptic message.
    if not elevated:
        return {
            "ok": False,
            "control": control,
            "error": "needs_admin",
            "is_admin": False,
            "log": [
                _norm_log(
                    "Esta corrección necesita Administrador. Cierra y reinicia "
                    "WinSvalinn como Administrador y vuelve a intentarlo.",
                    "error",
                )
            ],
        }

    # Reversible remediation: create a best-effort restore point / registry
    # backup *before* applying the fix so the change can be rolled back.
    from winsvalinn.core import safe_change

    log: list = []
    checkpoint = safe_change.create_checkpoint(f"remediate:{control}")
    if checkpoint["created"]:
        log.append(_norm_log(f"Punto de restauración creado ({checkpoint['detail']})", "success"))
    else:
        log.append(
            _norm_log(
                f"Aviso: no se pudo crear el punto de restauración ({checkpoint['detail']})",
                "warning",
            )
        )

    try:
        ok, fix_log, result = fixer()
        log.extend(fix_log)
        # Surface the fixer's own message — it carries the real reason on failure.
        if isinstance(result, dict) and result.get("message"):
            log.append(_norm_log(result["message"], "success" if ok else "error"))
        out = {"ok": ok, "control": control, "log": log, "checkpoint": checkpoint, "is_admin": True}
        if not ok:
            out["error"] = "failed"
        return out
    except Exception as exc:
        log.append(_norm_log(f"Error: {exc}", "error"))
        return {
            "ok": False,
            "control": control,
            "log": log,
            "checkpoint": checkpoint,
            "error": str(exc),
            "is_admin": True,
        }


# ─── Native options registry ─────────────────────────────────────────────


@app.get("/options")
def options_list(section: str | None = None):
    """List native options, optionally filtered by section."""
    from sidecar import options

    return {"options": options.list_options(section)}


@app.post("/options/{option_id}/run")
def options_run(option_id: str):
    """
    Run a native option by id.

    Empresarial options require a valid license; otherwise HTTP 402 with
    {ok:false, locked:true, error:"locked"}.
    """
    from sidecar import options
    from winsvalinn.core import licensing

    option = options.get_option(option_id)
    if option is None:
        raise HTTPException(404, f"Unknown option: {option_id}")

    if option.edition == "empresarial" and not licensing.current_edition()["valid"]:
        raise HTTPException(402, detail={"ok": False, "locked": True, "error": "locked"})

    result = options.run_option(option_id)
    return {
        "ok": bool(result.get("ok", False)),
        "log": result.get("log", []),
        "result": result.get("result"),
        **({"error": result["error"]} if result.get("error") else {}),
    }
