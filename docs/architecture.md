# WinSvalinn Architecture

## Overview

WinSvalinn is a Tauri 2 desktop shell (Rust) that loads a React/TypeScript frontend and
talks to a local Python FastAPI sidecar. All system work happens in GUI-free Python engines
under `winsvalinn.core`, reused by both the sidecar and the headless CLI.

```
┌─────────────────────────────┐      HTTP 127.0.0.1:8731      ┌──────────────────────┐
│ Tauri shell (src-tauri/)    │  ───────────────────────────▶ │ FastAPI sidecar      │
│  └─ React frontend          │   X-WSV-Client header         │ (src/sidecar/)       │
│     (frontend/)             │ ◀───────────────────────────  │                      │
└─────────────────────────────┘                               └──────────┬───────────┘
                                                                          │
                                                              ┌───────────▼───────────┐
                                                              │ winsvalinn.core        │
                                                              │ engines (no GUI)       │
                                                              │ security / optimization│
                                                              │ gpu / ram / hardening… │
                                                              └────────────────────────┘
```

## Components

### Tauri shell (`src-tauri/`)
- Custom decoration-less window, size/position persisted via `tauri-plugin-window-state`.
- Auto-spawns the bundled Python sidecar (`externalBin: binaries/winsvalinn-sidecar`).
- Bundles MSI + NSIS installers (es-ES / en-US).

### Frontend (`frontend/`)
- React 19 + TypeScript + Vite + Tailwind v4 + shadcn/ui (Nord theme).
- `src/lib/api.ts` — thin sidecar client; every request carries `X-WSV-Client: winsvalinn`.
- State via lightweight pub/sub stores: `lib/edition.ts` (license), `lib/i18n.tsx` (es/en),
  `lib/cache.ts` (scan results).
- One view per page under `src/views/`; reusable pieces under `src/components/`.

### Sidecar (`src/sidecar/`)
- FastAPI app on `127.0.0.1:8731`.
- Local guard middleware: validates `Host` (anti-DNS-rebind) and requires the
  `X-WSV-Client` header on mutating methods (anti-CSRF). CORS restricted to Tauri/dev origins.
- Auto-discovered routers (`routes/`) and options (`options/`).

### Core engines (`src/winsvalinn/core/`)
- Pure backend logic — **no GUI imports** — so it is testable without a display and reusable
  from the CLI.
- Each engine performs one concern (security scan, optimization, GPU/RAM tweaks, hardening,
  audit, etc.) via `subprocess` (`shell=False`), `psutil`, `winreg` or Win32 APIs.

## Native Options Registry

The legacy filesystem plugin system was removed and replaced by a native options registry in
`src/sidecar/options/`. Each option is a GUI-free action backed by a `winsvalinn.core` engine.

- Option groups live in sibling `opt_*.py` submodules that call `register(Option(...))` at
  import time; the package auto-discovers them on load (drop-in file, no `__init__.py` edits).
- An `Option` carries metadata (`id`, `section`, `label`, `edition`, `description`,
  `is_destructive`) and a zero-argument `handler` returning
  `{"ok": bool, "log": [...], "result": Any}`. Handlers never raise.
- `empresarial` options require a valid license; gating is enforced by the API layer
  (`POST /options/{id}/run` returns HTTP 402 when locked).
- Exposed via `GET /options` (optional `?section=`) and `POST /options/{id}/run`.

See [plugin-development.md](plugin-development.md) for how to add an option.

## Safety Model

- Destructive operations require admin and create a checkpoint **before** running
  (System Restore point + registry backup), with rollback support.
- Edition gating (Free / Empresarial) is enforced server-side in the sidecar via Ed25519
  license verification.

## Data Flow

```
User action → React view → api.ts → sidecar endpoint → winsvalinn.core engine → System
                                                              │
                                                  normalized result → UI feedback
```
