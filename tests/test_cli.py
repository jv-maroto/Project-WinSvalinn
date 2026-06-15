"""Tests for the terminal edition (winsvalinn.cli).

Only cover read-only commands so the suite never mutates the host system.
"""

import json

from typer.testing import CliRunner

from winsvalinn.cli import app

runner = CliRunner()


def test_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "WinSvalinn" in result.stdout


def test_help_lists_commands():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for cmd in ("info", "health", "audit", "optimize", "clean", "license"):
        assert cmd in result.stdout


def test_info_json_is_machine_readable():
    result = runner.invoke(app, ["--json", "info"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert "os" in data
    assert "python" in data
    assert data["edition"] in ("free", "empresarial")


def test_license_show_json():
    result = runner.invoke(app, ["--json", "license", "show"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data.get("edition") in ("free", "empresarial")


def test_optimize_rejects_unknown_action():
    result = runner.invoke(app, ["optimize", "definitely-not-an-action"])
    assert result.exit_code == 2
