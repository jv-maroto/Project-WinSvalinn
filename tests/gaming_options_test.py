"""
Lightweight registration tests for the native "gaming" option group.

These tests only assert that the options are registered with the correct
section/edition and metadata shape. They never invoke handlers or touch the
real system (no registry, subprocess, or filesystem mutation).
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import sidecar.options as options  # noqa: E402

# Every option this group is expected to register: id -> is_destructive.
EXPECTED_GAMING_OPTIONS = {
    "gaming_detect_platforms": False,
    "gaming_kill_background": True,
    "gaming_game_mode": True,
    "gaming_clean_shaders": True,
    "gaming_optimize_network": True,
    "gaming_ultimate_power": True,
    "gaming_apply_all": True,
    "gaming_lol_priority": True,
    "gaming_lol_display": True,
    "gaming_lol_client": True,
    "gaming_lol_apply_all": True,
    "gaming_obs_priority": True,
    "gaming_obs_encoder": False,
    "gaming_obs_dynamic_bitrate": True,
    "gaming_kill_overlays": True,
    "gaming_streaming_apply_all": True,
}


def _gaming_options():
    return {opt["id"]: opt for opt in options.list_options("gaming")}


def test_all_gaming_options_registered():
    registered = _gaming_options()
    missing = set(EXPECTED_GAMING_OPTIONS) - set(registered)
    assert not missing, f"missing gaming options: {missing}"


def test_gaming_options_have_correct_section_and_edition():
    for opt in options.list_options("gaming"):
        assert opt["section"] == "gaming"
        assert opt["edition"] == "free"


def test_gaming_options_destructive_flags():
    registered = _gaming_options()
    for opt_id, destructive in EXPECTED_GAMING_OPTIONS.items():
        assert registered[opt_id]["is_destructive"] is destructive, opt_id


@pytest.mark.parametrize("opt_id", sorted(EXPECTED_GAMING_OPTIONS))
def test_gaming_option_has_label_and_handler(opt_id):
    opt = options.get_option(opt_id)
    assert opt is not None
    assert opt.label and isinstance(opt.label, str)
    assert callable(opt.handler)
    public = opt.to_public()
    assert public["description"]
