"""WinSvalinn command-line interface.

A lightweight terminal front-end over the same GUI-free engines used by the
desktop app (``winsvalinn.core``). It needs no Node, WebView2 or Tauri — just
Python — so it runs on headless servers and very low-resource machines.

Both editions are supported: Empresarial features unlock with the same
Ed25519 license key as the desktop app (``winsvalinn license activate KEY``).

Use ``--json`` on any command for plain, machine-readable output (and to skip
the Rich rendering entirely on constrained terminals).
"""

import json
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

try:
    __version__ = _pkg_version("winsvalinn-sidecar")
except PackageNotFoundError:  # running from a source checkout without install
    __version__ = "1.0.1"

# Actions that mutate the system, mapped to a human label for confirmations.
_OPTIMIZE_ACTIONS = {
    "ram": "Free up RAM (trim working sets)",
    "gpu": "Apply GPU vendor tweaks",
    "visual": "Optimize Windows visual effects",
    "network": "Optimize TCP/IP network settings",
    "ssd": "Apply SSD tuning",
    "power": "List / set power plans",
}

console = Console()
_state = {"json": False}

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="WinSvalinn — Windows security auditor & system optimizer (terminal edition).",
)
license_app = typer.Typer(no_args_is_help=True, help="Show or change your edition / license.")
app.add_typer(license_app, name="license")


# ─── helpers ──────────────────────────────────────────────────────────────


def _emit(data: object, render) -> None:
    """Print ``data`` as JSON when --json is set, otherwise call ``render``."""
    if _state["json"]:
        typer.echo(json.dumps(data, default=str, ensure_ascii=False))
    else:
        render()


def _run_engine(label: str, fn):
    """Call a core engine, turning failures into a clean non-zero exit."""
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001 — surface any engine error to the user
        if _state["json"]:
            typer.echo(json.dumps({"ok": False, "error": str(exc)}))
        else:
            console.print(f"[red]✗ {label} failed:[/] {exc}")
        raise typer.Exit(1) from exc


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"WinSvalinn {__version__}")
        raise typer.Exit()


# ─── global options ─────────────────────────────────────────────────────────


@app.callback()
def _main(
    json_out: bool = typer.Option(
        False, "--json", "-j", help="Machine-readable JSON output (no styling)."
    ),
    _version: bool = typer.Option(
        False,
        "--version",
        "-V",
        callback=_version_callback,
        is_eager=True,
        help="Show the version and exit.",
    ),
) -> None:
    _state["json"] = json_out


# ─── info / health ──────────────────────────────────────────────────────────


@app.command()
def info() -> None:
    """Show OS and hardware summary."""
    import platform

    import psutil

    vm = psutil.virtual_memory()
    data = {
        "os": f"{platform.system()} {platform.release()}",
        "version": platform.version(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "ram_total_gb": round(vm.total / (1024**3), 1),
        "cpu_logical": psutil.cpu_count(logical=True),
        "cpu_physical": psutil.cpu_count(logical=False),
        "edition": _edition_label(),
    }

    def render() -> None:
        table = Table(title="System", show_header=False, box=None)
        for k, v in data.items():
            table.add_row(f"[dim]{k}[/]", str(v))
        console.print(table)

    _emit(data, render)


@app.command()
def health() -> None:
    """Quick CPU / RAM / disk health score (0–100)."""
    import psutil

    cpu = psutil.cpu_percent(interval=0.3)
    ram = psutil.virtual_memory().percent
    try:
        disk = psutil.disk_usage("C:\\").percent
    except Exception:  # noqa: BLE001 — non-Windows or missing C: drive
        disk = psutil.disk_usage("/").percent
    score = max(0, min(100, int((100 - cpu) * 0.30 + (100 - ram) * 0.45 + (100 - disk) * 0.25)))
    data = {"score": score, "cpu": round(cpu, 1), "ram": round(ram, 1), "disk": round(disk, 1)}

    def render() -> None:
        colour = "green" if score >= 70 else "yellow" if score >= 40 else "red"
        console.print(
            Panel(
                f"[{colour}]{score}/100[/]\n"
                f"CPU {data['cpu']}%   RAM {data['ram']}%   Disk {data['disk']}%",
                title="Health",
                expand=False,
            )
        )

    _emit(data, render)


# ─── security audit ─────────────────────────────────────────────────────────


@app.command()
def audit() -> None:
    """Run a security audit and print the score and findings."""
    result = _run_engine("Security audit", lambda: _security_audit())
    data = result or {}

    def render() -> None:
        score = data.get("score", data.get("security_score", "?"))
        console.print(Panel(f"Security score: [bold]{score}[/]", expand=False))
        findings = data.get("findings") or data.get("issues") or []
        if not findings:
            console.print("[green]No findings reported.[/]")
            return
        table = Table(title=f"{len(findings)} findings")
        table.add_column("Severity")
        table.add_column("Finding")
        for f in findings:
            if isinstance(f, dict):
                sev = str(f.get("severity", f.get("level", "info")))
                msg = str(f.get("title", f.get("message", f.get("name", f))))
            else:
                sev, msg = "info", str(f)
            table.add_row(sev, msg)
        console.print(table)

    _emit(data, render)


# ─── optimize / clean ───────────────────────────────────────────────────────


@app.command()
def optimize(
    action: str = typer.Argument(..., help="ram | gpu | visual | network | ssd | power"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip the confirmation prompt."),
) -> None:
    """Apply a system optimization. Changes the system — run as Administrator."""
    if action not in _OPTIMIZE_ACTIONS:
        console.print(
            f"[red]Unknown action '{action}'.[/] Choose one of: {', '.join(_OPTIMIZE_ACTIONS)}"
        )
        raise typer.Exit(2)
    if (
        not yes
        and not _state["json"]
        and action != "power"
        and not typer.confirm(f"Apply: {_OPTIMIZE_ACTIONS[action]}?")
    ):
        raise typer.Abort()

    result = _run_engine(f"optimize {action}", lambda: _do_optimize(action))
    _emit(result, lambda: console.print(f"[green]✓[/] {_OPTIMIZE_ACTIONS[action]}\n{result}"))


@app.command()
def clean(
    yes: bool = typer.Option(False, "--yes", "-y", help="Clean without confirmation."),
) -> None:
    """Analyze temporary files and optionally clean them."""
    analysis = _run_engine("cleanup analyze", lambda: _optimizer().analyze_temp_files())
    if not _state["json"]:
        console.print(Panel(str(analysis), title="Temp files", expand=False))
    if not yes and not _state["json"] and not typer.confirm("Delete these temporary files?"):
        raise typer.Abort()
    result = _run_engine("cleanup clean", lambda: _optimizer().clean_temp_files())
    _emit(result, lambda: console.print(f"[green]✓ Cleaned.[/]\n{result}"))


# ─── license ────────────────────────────────────────────────────────────────


@license_app.command("show")
def license_show() -> None:
    """Show the active edition and license status."""
    from winsvalinn.core import licensing

    data = licensing.current_edition()

    def render() -> None:
        valid = data.get("valid")
        colour = "green" if valid else "yellow"
        console.print(
            Panel(
                f"Edition: [{colour}]{data.get('edition', 'free')}[/]\n"
                f"Valid: {valid}   Tier: {data.get('tier')}\n"
                f"Email: {data.get('email') or '—'}   Expiry: {data.get('expiry') or '—'}",
                title="License",
                expand=False,
            )
        )

    _emit(data, render)


@license_app.command("activate")
def license_activate(key: str = typer.Argument(..., help="Your Ed25519 license key.")) -> None:
    """Validate and store an Empresarial license key (offline)."""
    from winsvalinn.core import licensing

    resolved = licensing.resolve_edition(key)
    if not resolved.get("valid"):
        _emit(
            {"ok": False, "error": "invalid_or_expired", **resolved},
            lambda: console.print("[red]✗ Invalid or expired license key.[/]"),
        )
        raise typer.Exit(1)
    licensing.save_license(key)
    _emit(
        {"ok": True, **resolved},
        lambda: console.print(
            f"[green]✓ Empresarial unlocked[/] "
            f"(tier: {resolved.get('tier')}, email: {resolved.get('email') or '—'})"
        ),
    )


@license_app.command("deactivate")
def license_deactivate() -> None:
    """Remove the stored license and revert to the Free edition."""
    from winsvalinn.core import licensing

    licensing.clear_license()
    _emit(
        {"ok": True, "edition": "free"},
        lambda: console.print("[yellow]Reverted to the Free edition.[/]"),
    )


# ─── lazy engine wrappers ────────────────────────────────────────────────────


def _edition_label() -> str:
    try:
        from winsvalinn.core import licensing

        return licensing.current_edition().get("edition", "free")
    except Exception:  # noqa: BLE001 — never let edition lookup break `info`
        return "free"


def _optimizer():
    from winsvalinn.core import SystemOptimizer

    return SystemOptimizer()


def _security_audit():
    from winsvalinn.core import SecurityAudit

    return SecurityAudit().run_security_scan() or {}


def _do_optimize(action: str):
    from winsvalinn.core import GPUBrandOptimizer, RAMOptimizer

    if action == "ram":
        return RAMOptimizer().free_ram()
    if action == "gpu":
        return GPUBrandOptimizer().auto_optimize()
    opt = _optimizer()
    if action == "visual":
        return opt.optimize_visual_effects()
    if action == "network":
        return opt.optimize_network()
    if action == "ssd":
        return opt.optimize_ssd()
    if action == "power":
        return {"plans": opt.get_power_plans() or []}
    raise ValueError(f"Unknown action: {action}")


if __name__ == "__main__":
    app()
