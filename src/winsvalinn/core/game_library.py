"""Per-game optimization: detect installed games and apply game-specific tweaks.

Detects games across Steam (via ``appmanifest_*.acf``), Riot (League of Legends)
and known standalone installs (Path of Exile), then applies a profile to the
game the user picks:

* **Universal** (every game, per-exe, HKCU — no admin): disable Fullscreen
  Optimizations and force the high-performance GPU for each game executable,
  plus enable Auto Game Mode once.
* **Curated** extras for big titles (currently League of Legends via
  :class:`~winsvalinn.core.game_optimizer.GameOptimizer`).

Every action reports whether it needs Administrator. The universal tweaks live
under HKCU, so they do not; the result still includes ``is_admin`` so the UI can
warn when a future curated tweak would.
"""

from __future__ import annotations

import os
import platform
import re
import subprocess
from collections.abc import Callable
from pathlib import Path

_CREATE_NO_WINDOW = 0x08000000

IS_WINDOWS = platform.system() == "Windows"
if IS_WINDOWS:
    import winreg

# Steam appid -> {name, exe (relative to the game's install dir)}.
# A wrong/missing exe is safe: detection falls back to a best-effort guess.
KNOWN_STEAM_GAMES: dict[str, dict] = {
    "730": {"name": "Counter-Strike 2", "exe": r"game\bin\win64\cs2.exe"},
    "570": {"name": "Dota 2", "exe": r"game\bin\win64\dota2.exe"},
    "578080": {"name": "PUBG: BATTLEGROUNDS", "exe": r"TslGame\Binaries\Win64\TslGame.exe"},
    "1172470": {"name": "Apex Legends", "exe": "r5apex.exe"},
    "252490": {"name": "Rust", "exe": "RustClient.exe"},
    "271590": {"name": "Grand Theft Auto V", "exe": "GTA5.exe"},
    "238960": {"name": "Path of Exile", "exe": "PathOfExileSteam.exe"},
    "2694490": {"name": "Path of Exile 2", "exe": "PathOfExile.exe"},
    "1086940": {"name": "Baldur's Gate 3", "exe": r"bin\bg3.exe"},
    "1245620": {"name": "Elden Ring", "exe": r"Game\eldenring.exe"},
    "359550": {"name": "Rainbow Six Siege", "exe": "RainbowSix.exe"},
    "1085660": {"name": "Destiny 2", "exe": "destiny2.exe"},
    "230410": {"name": "Warframe", "exe": "Warframe.x64.exe"},
    "1599340": {"name": "Lost Ark", "exe": r"Binaries\Win64\LOSTARK.exe"},
}

# Curated, research-backed recommendations shown to the user as guidance.
# IMPORTANT: these are NOT auto-applied — many of these titles run kernel-level
# anti-cheat (Vanguard/EAC/BattlEye/VAC) and editing their config files from
# outside the game can trigger flags or bans. Only the OS-level universal tweaks
# (GPU preference, Fullscreen Optimizations, Game Mode) are applied automatically;
# they are invisible to anti-cheat. Sources: community/pro optimization guides
# (Fortnite/Valorant/CS2 performance guides, 2025-2026).
CURATED: dict[str, dict] = {
    "steam:730": {
        "anticheat": "VAC",
        "tips": [
            "Opciones de lanzamiento: -high -novid -nojoy +fps_max 0 (pon -freq a tu Hz real)",
            "Vídeo: Multicore Rendering ON; sombras Low; modelos/texturas Low para más FPS",
            "Activa NVIDIA Reflex si tu GPU lo soporta",
        ],
    },
    "steam:570": {
        "anticheat": "VAC",
        "tips": [
            "Opciones de lanzamiento: -high -novid +fps_max 0",
            "Render API: Vulkan suele dar más FPS estables que DX11",
        ],
    },
    "steam:1172470": {
        "anticheat": "Easy Anti-Cheat",
        "tips": [
            "Opciones de lanzamiento: +fps_max unlimited",
            "Modelo de ejecución en config: Adaptive Resolution FPS Target alto, sombras bajas",
        ],
    },
    "steam:578080": {
        "anticheat": "BattlEye",
        "tips": [
            "Calidad general 'Muy bajo' salvo distancia de visión y texturas (visibilidad)",
            "Desactiva V-Sync y motion blur",
        ],
    },
    "riot:lol": {
        "anticheat": "Vanguard",
        "tips": [
            "En Ajustes del cliente: activa 'Low Spec Mode' y 'Cerrar cliente durante la partida'",
            "En el juego: límite de FPS = Hz del monitor (o +10); calidad de gráficos baja",
            "Desactiva animaciones del cliente para que vaya más fluido",
        ],
    },
    "riot:valorant": {
        "anticheat": "Vanguard",
        "tips": [
            "Pantalla completa; Límite de FPS = Hz del monitor o sin límite",
            "Calidad de material/textura/detalle en Bajo; sombras de primera persona OFF",
            "Activa NVIDIA Reflex + Boost; Multithreaded Rendering ON",
        ],
    },
    "epic:fortnite": {
        "anticheat": "Easy Anti-Cheat / BattlEye",
        "tips": [
            "Modo Rendimiento (baja fidelidad gráfica) para máximo FPS y menos input lag",
            "V-Sync OFF, Motion Blur OFF, sombras OFF, ray tracing OFF",
            "Activa NVIDIA Reflex Low Latency; polling del ratón a 1000 Hz",
        ],
    },
    "steam:359550": {  # Rainbow Six Siege
        "anticheat": "BattlEye",
        "tips": [
            "Render scaling 100% (la nitidez importa para ver enemigos)",
            "V-Sync OFF, filtrado de texturas y efectos de lente al mínimo",
            "Limita FPS a tu Hz; texturas según VRAM",
        ],
    },
    "steam:252490": {  # Rust
        "anticheat": "Easy Anti-Cheat",
        "tips": [
            "Calidad gráfica baja, distancia de sombras corta, hierba/agua al mínimo",
            "V-Sync OFF; sube 'Max GIB' y memoria de gráficos si tienes VRAM",
        ],
    },
    "steam:271590": {  # Grand Theft Auto V
        "anticheat": "BattlEye (Online)",
        "tips": [
            "MSAA OFF, densidad de población media, hierba en Normal",
            "Desactiva 'Extended Distance Scaling' y reflejos altos para FPS",
        ],
    },
}

# Optimization actions. "global" ones are system-wide and run WITHOUT a game
# selected (the classic "gaming tweaks"). "per_game" ones target the chosen
# game's executables. `lol_only` appears only for League. `needs_admin` ones
# touch HKLM/powercfg/other processes; the rest are HKCU/user-scope.
GAME_ACTIONS: list[dict] = [
    # ── Global (no game needed) ──────────────────────────────────────────
    {
        "id": "game_mode",
        "scope": "global",
        "label": "Game Mode + GPU Scheduling",
        "needs_admin": True,
        "destructive": False,
    },
    {
        "id": "kill_background",
        "scope": "global",
        "label": "Cerrar procesos en segundo plano",
        "needs_admin": True,
        "destructive": True,
    },
    {
        "id": "kill_overlays",
        "scope": "global",
        "label": "Cerrar overlays (Discord/Steam/GeForce)",
        "needs_admin": True,
        "destructive": True,
    },
    {
        "id": "game_priority",
        "scope": "global",
        "label": "Prioridad alta de CPU para juegos",
        "needs_admin": True,
        "destructive": False,
    },
    {
        "id": "network",
        "scope": "global",
        "label": "Optimizar red (desactivar Nagle)",
        "needs_admin": True,
        "destructive": False,
    },
    {
        "id": "ultimate_perf",
        "scope": "global",
        "label": "Plan de energía Ultimate Performance",
        "needs_admin": True,
        "destructive": False,
    },
    {
        "id": "shader_cache",
        "scope": "global",
        "label": "Limpiar caché de shaders",
        "needs_admin": False,
        "destructive": True,
    },
    # ── Per-game (target the chosen game's exe) ──────────────────────────
    {
        "id": "fullscreen_opt",
        "scope": "per_game",
        "label": "Desactivar Fullscreen Optimizations (por exe)",
        "needs_admin": False,
        "destructive": False,
    },
    {
        "id": "gpu_high",
        "scope": "per_game",
        "label": "Forzar GPU de alto rendimiento (por exe)",
        "needs_admin": False,
        "destructive": False,
    },
    {
        "id": "lol_display",
        "scope": "per_game",
        "label": "LoL: optimizar display (fullscreen/DPI)",
        "needs_admin": False,
        "destructive": False,
        "lol_only": True,
    },
]

GLOBAL_ACTIONS: list[dict] = [a for a in GAME_ACTIONS if a["scope"] == "global"]


def _actions_for(game_id: str) -> list[dict]:
    """Per-game actions for a game (global actions are offered separately)."""
    is_lol = game_id == "riot:lol"
    return [
        a for a in GAME_ACTIONS if a["scope"] == "per_game" and ((not a.get("lol_only")) or is_lol)
    ]


# Executable names to ignore when guessing a generic game's main exe.
_EXE_BLOCKLIST = (
    "unins",
    "crashhandler",
    "crashreport",
    "vcredist",
    "dxsetup",
    "dxwebsetup",
    "redist",
    "launcher_installer",
    "touchup",
    "notification_helper",
)

_STEAM_REG = r"Software\Valve\Steam"
_FULLSCREEN_OPT_LAYER = "~ DISABLEDXMAXIMIZEDWINDOWEDMODE"
_GPU_PREF_HIGH = "GpuPreference=2;"


def is_admin() -> bool:
    """Return True if the process is running elevated (Windows)."""
    if not IS_WINDOWS:
        return False
    try:
        import ctypes

        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:  # noqa: BLE001
        return False


# ─── Steam detection ────────────────────────────────────────────────────


def _steam_root() -> str | None:
    if not IS_WINDOWS:
        return None
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _STEAM_REG)
        try:
            path, _ = winreg.QueryValueEx(key, "SteamPath")
        finally:
            winreg.CloseKey(key)
        if path and os.path.isdir(path):
            return path
    except OSError:
        pass
    for cand in (r"C:\Program Files (x86)\Steam", r"C:\Program Files\Steam"):
        if os.path.isdir(cand):
            return cand
    return None


def _steam_libraries(steam_root: str) -> list[str]:
    """All Steam library folders (the root plus extra drives)."""
    libs = [steam_root]
    vdf = Path(steam_root) / "steamapps" / "libraryfolders.vdf"
    try:
        text = vdf.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r'"path"\s*"([^"]+)"', text):
            p = m.group(1).replace("\\\\", "\\")
            if os.path.isdir(p) and p not in libs:
                libs.append(p)
    except OSError:
        pass
    return libs


def _guess_exe(game_dir: Path) -> str | None:
    """Best-effort main executable for a generic Steam game."""
    candidates: list[Path] = []
    try:
        for depth_dir in (game_dir, *[d for d in game_dir.iterdir() if d.is_dir()]):
            for exe in depth_dir.glob("*.exe"):
                low = exe.name.lower()
                if any(b in low for b in _EXE_BLOCKLIST):
                    continue
                candidates.append(exe)
    except OSError:
        return None
    if not candidates:
        return None
    # Prefer an exe whose name matches the install dir, else the largest file.
    dir_token = game_dir.name.lower().replace(" ", "")
    for exe in candidates:
        if exe.stem.lower().replace(" ", "") in dir_token or dir_token in exe.stem.lower():
            return str(exe)
    try:
        return str(max(candidates, key=lambda p: p.stat().st_size))
    except OSError:
        return str(candidates[0])


def _detect_steam() -> list[dict]:
    root = _steam_root()
    if not root:
        return []
    games: list[dict] = []
    for lib in _steam_libraries(root):
        steamapps = Path(lib) / "steamapps"
        try:
            manifests = list(steamapps.glob("appmanifest_*.acf"))
        except OSError:
            continue
        for mf in manifests:
            try:
                text = mf.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            appid = (re.search(r'"appid"\s*"(\d+)"', text) or [None, None])[1]
            name = (re.search(r'"name"\s*"([^"]+)"', text) or [None, None])[1]
            installdir = (re.search(r'"installdir"\s*"([^"]+)"', text) or [None, None])[1]
            if not appid or not installdir:
                continue
            game_dir = steamapps / "common" / installdir
            if not game_dir.is_dir():
                continue
            known = KNOWN_STEAM_GAMES.get(appid)
            if known and (game_dir / known["exe"]).exists():
                exes = [str(game_dir / known["exe"])]
                display = known["name"]
            else:
                guess = _guess_exe(game_dir)
                exes = [guess] if guess else []
                display = (known or {}).get("name") or name or installdir
            if exes:
                games.append(
                    {
                        "id": f"steam:{appid}",
                        "name": display,
                        "source": "Steam",
                        "exes": exes,
                        "curated": False,
                        "needs_admin": False,
                    }
                )
    return games


# ─── Riot / standalone detection ────────────────────────────────────────


def _detect_riot() -> list[dict]:
    if not IS_WINDOWS:
        return []
    out: list[dict] = []
    for drive in ("C", "D", "E", "F"):
        base = Path(f"{drive}:\\Riot Games\\League of Legends")
        if base.is_dir():
            exes = [
                str(base / "LeagueClient.exe"),
                str(base / "Game" / "League of Legends.exe"),
            ]
            exes = [e for e in exes if os.path.exists(e)]
            if exes:
                out.append(
                    {
                        "id": "riot:lol",
                        "name": "League of Legends",
                        "source": "Riot",
                        "exes": exes,
                        "curated": True,
                        "needs_admin": False,
                    }
                )
                break
    for drive in ("C", "D", "E", "F"):
        live = Path(f"{drive}:\\Riot Games\\VALORANT\\live")
        client = live / "VALORANT.exe"
        shipping = live / "ShooterGame" / "Binaries" / "Win64" / "VALORANT-Win64-Shipping.exe"
        if client.exists():
            exes = [str(client)] + ([str(shipping)] if shipping.exists() else [])
            out.append(
                {
                    "id": "riot:valorant",
                    "name": "VALORANT",
                    "source": "Riot",
                    "exes": exes,
                    "curated": False,
                    "needs_admin": False,
                }
            )
            break
    return out


def _detect_epic() -> list[dict]:
    if not IS_WINDOWS:
        return []
    bases = (
        r"C:\Program Files\Epic Games",
        r"C:\Program Files (x86)\Epic Games",
        r"D:\Epic Games",
        r"E:\Epic Games",
    )
    for pf in bases:
        exe = (
            Path(pf)
            / "Fortnite"
            / "FortniteGame"
            / "Binaries"
            / "Win64"
            / "FortniteClient-Win64-Shipping.exe"
        )
        if exe.exists():
            return [
                {
                    "id": "epic:fortnite",
                    "name": "Fortnite",
                    "source": "Epic",
                    "exes": [str(exe)],
                    "curated": False,
                    "needs_admin": False,
                }
            ]
    return []


def _detect_standalone() -> list[dict]:
    if not IS_WINDOWS:
        return []
    games: list[dict] = []
    standalone = {
        "poe": (
            "Path of Exile (standalone)",
            [r"C:\Program Files (x86)\Grinding Gear Games\Path of Exile\PathOfExile.exe"],
        ),
    }
    for slug, (name, paths) in standalone.items():
        for p in paths:
            if os.path.exists(p):
                games.append(
                    {
                        "id": f"standalone:{slug}",
                        "name": name,
                        "source": "Standalone",
                        "exes": [p],
                        "curated": False,
                        "needs_admin": False,
                    }
                )
                break
    return games


def _reg_read(hive, subkey: str, name: str):
    """Read a registry value, or None if missing/unreadable."""
    if not IS_WINDOWS:
        return None
    try:
        key = winreg.OpenKey(hive, subkey)
        try:
            val, _ = winreg.QueryValueEx(key, name)
        finally:
            winreg.CloseKey(key)
        return val
    except OSError:
        return None


def _ultimate_active() -> bool:
    """True if the active power plan is the Ultimate Performance plan."""
    if not IS_WINDOWS:
        return False
    try:
        out = subprocess.run(
            ["powercfg", "/getactivescheme"],
            capture_output=True,
            text=True,
            timeout=8,
            creationflags=_CREATE_NO_WINDOW,
        ).stdout.lower()
    except (OSError, subprocess.SubprocessError):
        return False
    return "e9a42b02" in out or "ultimate" in out


def _global_action_applied(action_id: str):
    """Detected applied-state for a global action (True/False, or None=unknown)."""
    if action_id == "game_mode":
        am = _reg_read(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\GameBar", "AllowAutoGameMode")
        hw = _reg_read(
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers",
            "HwSchMode",
        )
        return (am == 1) and (hw == 2)
    if action_id == "ultimate_perf":
        return _ultimate_active()
    return None


def _per_game_action_applied(game: dict, action_id: str):
    """Detected applied-state for a per-game action (True/False, or None=unknown)."""
    exes = game.get("exes") or []
    if not exes:
        return None
    if action_id == "fullscreen_opt":
        layers = r"Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers"
        return all(
            "DISABLEDXMAXIMIZEDWINDOWEDMODE"
            in str(_reg_read(winreg.HKEY_CURRENT_USER, layers, e) or "")
            for e in exes
        )
    if action_id == "gpu_high":
        pref = r"Software\Microsoft\DirectX\UserGpuPreferences"
        return all(
            "GpuPreference=2" in str(_reg_read(winreg.HKEY_CURRENT_USER, pref, e) or "")
            for e in exes
        )
    return None


def detect_games() -> dict:
    """Return all detected installed games (read-only)."""
    games: list[dict] = []
    for fn in (_detect_steam, _detect_riot, _detect_epic, _detect_standalone):
        try:
            games.extend(fn())
        except Exception:  # noqa: BLE001 - one bad source must not break the list
            pass
    # Dedupe by id, then enrich with curated guidance / anti-cheat info.
    seen: set[str] = set()
    unique = []
    for g in games:
        if g["id"] in seen:
            continue
        seen.add(g["id"])
        curated = CURATED.get(g["id"], {})
        g["anticheat"] = curated.get("anticheat")
        g["tips"] = curated.get("tips", [])
        g["curated"] = bool(g.get("curated") or g["tips"])
        g["actions"] = [
            {**a, "applied": _per_game_action_applied(g, a["id"])} for a in _actions_for(g["id"])
        ]
        unique.append(g)
    # Curated titles first, then alphabetical.
    unique.sort(key=lambda x: (not x["curated"], x["name"].lower()))
    global_actions = [{**a, "applied": _global_action_applied(a["id"])} for a in GLOBAL_ACTIONS]
    return {
        "games": unique,
        "count": len(unique),
        "is_admin": is_admin(),
        "global_actions": global_actions,
    }


# ─── Apply per-exe universal tweaks ──────────────────────────────────────


def _set_hkcu(subkey: str, name: str, value: str) -> bool:
    if not IS_WINDOWS:
        return False
    try:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, subkey)
        try:
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)
        finally:
            winreg.CloseKey(key)
        return True
    except OSError:
        return False


def _apply_universal(exe: str, log: list[dict]) -> int:
    """Per-exe HKCU tweaks. Returns the number applied."""
    applied = 0
    if _set_hkcu(
        r"Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers",
        exe,
        _FULLSCREEN_OPT_LAYER,
    ):
        applied += 1
        log.append(
            {"msg": f"Fullscreen Optimizations off: {os.path.basename(exe)}", "level": "success"}
        )
    if _set_hkcu(r"Software\Microsoft\DirectX\UserGpuPreferences", exe, _GPU_PREF_HIGH):
        applied += 1
        log.append({"msg": f"GPU alto rendimiento: {os.path.basename(exe)}", "level": "success"})
    return applied


def _enable_game_mode(log: list[dict]) -> None:
    if not IS_WINDOWS:
        return
    try:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\GameBar")
        try:
            winreg.SetValueEx(key, "AllowAutoGameMode", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "AutoGameModeEnabled", 0, winreg.REG_DWORD, 1)
        finally:
            winreg.CloseKey(key)
        log.append({"msg": "Game Mode automático activado", "level": "success"})
    except OSError:
        pass


def _apply_curated(game_id: str, log: list[dict], callback: Callable | None) -> None:
    """Curated, game-specific extras. Only OS-safe ones are auto-applied.

    LoL now runs Vanguard (kernel anti-cheat), so we only touch the OS-level
    per-exe display tweak (HKCU) and leave the in-client settings to the user
    (surfaced as tips) — editing the game's own files could trip the anti-cheat.
    """
    if game_id == "riot:lol":
        try:
            from winsvalinn.core.game_optimizer import GameOptimizer

            GameOptimizer(callback=callback).apply_lol_display()
            log.append({"msg": "LoL: display optimizado (a nivel de Windows)", "level": "success"})
        except Exception as exc:  # noqa: BLE001
            log.append({"msg": f"Curado LoL no aplicado: {exc}", "level": "warning"})


def optimize_game(game_id: str, callback: Callable | None = None) -> dict:
    """
    Apply the optimization profile for ``game_id``.

    Returns ``{ok, game, log, applied, needs_admin, is_admin}``. ``needs_admin``
    is True only if the profile contains a tweak that requires elevation.
    """
    log: list[dict] = []
    game = next((g for g in detect_games()["games"] if g["id"] == game_id), None)
    if game is None:
        return {
            "ok": False,
            "error": "not_found",
            "log": [{"msg": f"Juego no detectado: {game_id}", "level": "error"}],
            "applied": 0,
            "needs_admin": False,
            "is_admin": is_admin(),
        }

    applied = 0
    for exe in game["exes"]:
        applied += _apply_universal(exe, log)
    _enable_game_mode(log)
    _apply_curated(game_id, log, callback)

    curated = CURATED.get(game_id, {})
    return {
        "ok": applied > 0,
        "game": game["name"],
        "log": log,
        "applied": applied,
        "needs_admin": bool(game.get("needs_admin")),
        "is_admin": is_admin(),
        "anticheat": curated.get("anticheat"),
        "tips": curated.get("tips", []),
    }


def _dispatch_action(game: dict | None, action_id: str, log: list[dict], cb: Callable) -> int:
    """Run one action. ``game`` is None for global (system-wide) actions."""
    if action_id in ("fullscreen_opt", "gpu_high") and not game:
        log.append({"msg": "Esta acción necesita un juego seleccionado", "level": "error"})
        return 0
    if action_id == "fullscreen_opt":
        n = 0
        for exe in game["exes"]:
            if _set_hkcu(
                r"Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers",
                exe,
                _FULLSCREEN_OPT_LAYER,
            ):
                n += 1
                log.append(
                    {
                        "msg": f"Fullscreen Optimizations off: {os.path.basename(exe)}",
                        "level": "success",
                    }
                )
        return n
    if action_id == "gpu_high":
        n = 0
        for exe in game["exes"]:
            if _set_hkcu(r"Software\Microsoft\DirectX\UserGpuPreferences", exe, _GPU_PREF_HIGH):
                n += 1
                log.append(
                    {"msg": f"GPU alto rendimiento: {os.path.basename(exe)}", "level": "success"}
                )
        return n

    try:
        from winsvalinn.core.game_optimizer import GameOptimizer

        opt = GameOptimizer(callback=cb)
    except Exception as exc:  # noqa: BLE001
        log.append({"msg": f"Motor de juegos no disponible: {exc}", "level": "error"})
        return 0

    mapping = {
        "game_mode": opt.enable_game_mode,
        "kill_background": opt.kill_background,
        "kill_overlays": opt.kill_overlays,
        "game_priority": opt.apply_game_priority,
        "network": opt.optimize_network,
        "ultimate_perf": opt.enable_ultimate_performance,
        "shader_cache": opt.clean_shader_cache,
        "lol_display": opt.apply_lol_display,
    }
    fn = mapping.get(action_id)
    if fn is None:
        log.append({"msg": f"Acción desconocida: {action_id}", "level": "error"})
        return 0
    try:
        res = fn()
        return 1 if (not isinstance(res, dict) or res.get("success", True)) else 0
    except Exception as exc:  # noqa: BLE001
        log.append({"msg": f"Error: {exc}", "level": "error"})
        return 0


def run_action(game_id: str, action_id: str, callback: Callable | None = None) -> dict:
    """Run a single optimization action for a detected game."""
    log: list[dict] = []
    game = next((g for g in detect_games()["games"] if g["id"] == game_id), None)
    if game is None:
        return {
            "ok": False,
            "error": "not_found",
            "log": [{"msg": f"Juego no detectado: {game_id}", "level": "error"}],
            "applied": 0,
            "is_admin": is_admin(),
        }

    def _cb(msg: str, level: str = "info") -> None:
        lvl = (level or "info").lower()
        lvl = {"ok": "success", "err": "error", "warn": "warning"}.get(lvl, lvl)
        if lvl not in ("info", "success", "warning", "error"):
            lvl = "info"
        log.append({"msg": str(msg), "level": lvl})

    applied = _dispatch_action(game, action_id, log, callback or _cb)
    return {
        "ok": applied > 0,
        "game": game["name"],
        "action": action_id,
        "log": log,
        "applied": applied,
        "is_admin": is_admin(),
    }


def run_global_action(action_id: str, callback: Callable | None = None) -> dict:
    """Run a single system-wide ('global') optimization action — no game needed."""
    log: list[dict] = []
    if action_id not in {a["id"] for a in GLOBAL_ACTIONS}:
        return {
            "ok": False,
            "error": "unknown_action",
            "log": [{"msg": f"Acción global desconocida: {action_id}", "level": "error"}],
            "applied": 0,
            "is_admin": is_admin(),
        }

    def _cb(msg: str, level: str = "info") -> None:
        lvl = (level or "info").lower()
        lvl = {"ok": "success", "err": "error", "warn": "warning"}.get(lvl, lvl)
        if lvl not in ("info", "success", "warning", "error"):
            lvl = "info"
        log.append({"msg": str(msg), "level": lvl})

    applied = _dispatch_action(None, action_id, log, callback or _cb)
    return {
        "ok": applied > 0,
        "action": action_id,
        "log": log,
        "applied": applied,
        "is_admin": is_admin(),
    }
