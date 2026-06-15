# WinSvalinn — Documentación técnica

<img src="https://cdn.7tv.app/emote/01FEV00990000FCZBKX8KY8JRF/2x.webp" alt="nerd" width="28" align="left" />

Cómo está montado WinSvalinn por dentro, cómo se ejecuta en desarrollo y cómo
funciona el sistema de licencias y ediciones.

---

## Arquitectura

```
┌──────────────────────────┐     HTTP (127.0.0.1:8731)      ┌───────────────────────────┐
│  Shell Tauri 2 (Rust)     │  ───────────────────────────▶ │  Sidecar Python (FastAPI) │
│  + React 19 / Vite / TS   │  ◀─────────────────────────── │  motores winsvalinn.core  │
│  shadcn + Tailwind v4     │            JSON                │  (seguridad, optimización,│
│  barra de título propia   │                                │   privacidad, auditorías) │
└──────────────────────────┘                                └───────────────────────────┘
```

- **`frontend/`** — React 19 + Vite + TypeScript, shadcn/ui + Tailwind v4.
- **`src/sidecar/`** — app FastAPI; el registro de **opciones nativas** (`options/`) y los
  **routers** (`routes/`) se auto-descubren (módulos drop-in, sin cableado central).
- **`src/winsvalinn/core/`** — motores **sin GUI** (totalmente testeables). Los reutilizan tanto el
  sidecar como la CLI.
- **`src-tauri/`** — shell Rust de Tauri 2; arranca el sidecar al abrir y lo cierra al salir.

El shell y el sidecar hablan por HTTP local en `127.0.0.1:8731` (puerto elegido para evitar los
rangos excluidos de Windows/Hyper-V).

## Stack

`Tauri 2` · `React 19` · `TypeScript` · `Vite` · `Tailwind v4` · `shadcn/ui` · `FastAPI` ·
`Python 3.12+` · `cryptography (Ed25519)` · `psutil`

## Desarrollo

> Requiere: Windows 10/11, Python 3.12+, Node 18+, toolchain de Rust y WebView2.

```bash
# 1) Dependencias Python
pip install -e .

# 2) Dependencias del frontend
npm --prefix frontend install

# 3) Sidecar (backend)  — sirve en 127.0.0.1:8731
python run_sidecar.py

# 4) App (shell Rust + Vite), desde src-tauri:
cargo tauri dev
```

Tests:

```bash
pytest                              # backend (pytest, ~380 tests)
npm --prefix frontend run build     # type-check + build de la UI
npm --prefix frontend run test      # vitest (gating Free/Pro)
```

## Build

```bash
cargo tauri build                   # genera instaladores MSI / NSIS en src-tauri/target
```

El **release** automático (`.github/workflows/release.yml`) compila los instaladores x64 y un
`.exe` autónomo del sidecar/CLI al publicar un tag `v*`.

## Edición de terminal (CLI)

Para PCs de muy pocos recursos o uso headless, los mismos motores se exponen como CLI (sin Node,
WebView2 ni Tauri):

```bash
pipx install winsvalinn-sidecar

winsvalinn info        # OS + hardware
winsvalinn health      # CPU/RAM/disco
winsvalinn audit       # auditoría de seguridad
winsvalinn optimize ram -y
winsvalinn license activate <KEY>
winsvalinn --json health   # salida JSON para scripts
```

## Ediciones y licencias

La edición se resuelve a partir de una **clave firmada con Ed25519**, verificada en local — sin
servidor, 100 % offline. La app solo incrusta la clave **pública**; una clave válida desbloquea la
edición Empresarial y sus funciones. Los secretos (p. ej. la API key de VirusTotal) se guardan
cifrados con **Windows DPAPI**, nunca en texto plano.

```bash
# Emitir una clave (dev): la privada vive en tools/dev_private_key.hex (git-ignored)
python tools/issue_license.py --email tu@correo.com --edition empresarial --tier lifetime
```

> **VirusTotal:** la API pública gratuita de VirusTotal no puede usarse en productos comerciales,
> así que cada usuario aporta su propia API key (guardada con DPAPI).

Reparto open-source vs propietario: ver [LICENSING.md](../LICENSING.md).

## Roadmap

- Baselining de configuración (diff en el tiempo) · ficheros señuelo anti-ransomware · tendencia de
  la puntuación de seguridad.
- Escaneo CVE de apps de terceros · mapeo de cumplimiento (Cyber Essentials, NIST CSF).
- Firma de código (Authenticode) + auto-update · informes PDF de cliente con marca.

## Desarrollado con ayuda de IA

Partes de WinSvalinn se desarrollaron con apoyo de herramientas de IA
([Claude Code](https://claude.com/claude-code)) para scaffolding, refactors, tests y documentación.
Todo el código está revisado, mantenido y es propiedad del autor.
