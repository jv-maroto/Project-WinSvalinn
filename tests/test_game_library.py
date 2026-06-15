"""Tests for per-game detection/optimization (winsvalinn.core.game_library).

Detection is read-only; optimize_game is only exercised on a bogus id so the
suite never writes to the registry of a real game.
"""

from winsvalinn.core import game_library


def test_detect_games_shape():
    data = game_library.detect_games()
    assert set(data) >= {"games", "count", "is_admin"}
    assert data["count"] == len(data["games"])
    assert isinstance(data["is_admin"], bool)


def test_detected_game_fields():
    for g in game_library.detect_games()["games"]:
        assert {"id", "name", "source", "exes", "curated", "needs_admin"} <= set(g)
        assert isinstance(g["exes"], list)


def test_optimize_unknown_game_is_handled():
    result = game_library.optimize_game("steam:000000_does_not_exist")
    assert result["ok"] is False
    assert result["error"] == "not_found"
    assert result["applied"] == 0


def test_known_titles_registered():
    # The big titles the product advertises must stay mapped to a precise exe.
    for appid in ("730", "238960"):  # CS2, Path of Exile
        assert appid in game_library.KNOWN_STEAM_GAMES
        assert game_library.KNOWN_STEAM_GAMES[appid]["exe"]


def test_actions_lol_only_gating():
    generic = {a["id"] for a in game_library._actions_for("steam:730")}
    lol = {a["id"] for a in game_library._actions_for("riot:lol")}
    assert "lol_display" not in generic
    assert "lol_display" in lol
    # Per-game actions are exe-scoped; the global ones live separately.
    assert {"fullscreen_opt", "gpu_high"} <= generic
    assert "game_mode" not in generic


def test_global_actions_present():
    ids = {a["id"] for a in game_library.GLOBAL_ACTIONS}
    assert {"game_mode", "kill_background", "network"} <= ids
    r = game_library.run_global_action("nope_action")
    assert r["ok"] is False and r["error"] == "unknown_action"


def test_detected_games_include_actions():
    data = game_library.detect_games()
    assert isinstance(data["global_actions"], list) and data["global_actions"]
    for g in data["games"]:
        assert isinstance(g["actions"], list) and g["actions"]


def test_run_action_unknown_game():
    r = game_library.run_action("steam:000000_nope", "game_mode")
    assert r["ok"] is False
    assert r["error"] == "not_found"
