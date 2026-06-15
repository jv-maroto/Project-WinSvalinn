"""
Lightweight registration tests for the privacy options group.

These tests verify only that the migrated privacy options register with the
correct section/edition/metadata. They never execute the handlers and never
touch the real system (no DNS, hosts file, network, or subprocess calls).
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# Importing the package auto-imports opt_privacy and registers its options.
import sidecar.options as options  # noqa: E402

# The privacy options migrated from the legacy plugins.
EXPECTED_PRIVACY_IDS = {
    "doh_enable",
    "doh_disable",
    "doh_status",
    "hosts_steven_black_import",
    "hosts_steven_black_remove",
    "oosu_download",
    "oosu_launch",
}

# Options that change the system in a notable way must be flagged destructive.
EXPECTED_DESTRUCTIVE = {
    "doh_enable",
    "doh_disable",
    "hosts_steven_black_import",
    "hosts_steven_black_remove",
    "oosu_download",
    "oosu_launch",
}


def _privacy_meta() -> dict[str, dict]:
    """Return {id: public_meta} for the registered privacy options."""
    return {o["id"]: o for o in options.list_options("privacy")}


def test_privacy_options_are_registered():
    meta = _privacy_meta()
    missing = EXPECTED_PRIVACY_IDS - meta.keys()
    assert not missing, f"missing privacy options: {missing}"


@pytest.mark.parametrize("option_id", sorted(EXPECTED_PRIVACY_IDS))
def test_privacy_option_section_and_edition(option_id):
    opt = options.get_option(option_id)
    assert opt is not None, f"option not registered: {option_id}"
    assert opt.section == "privacy"
    assert opt.edition == "free"
    assert callable(opt.handler)


@pytest.mark.parametrize("option_id", sorted(EXPECTED_PRIVACY_IDS))
def test_privacy_option_has_label_and_description(option_id):
    opt = options.get_option(option_id)
    assert opt.label.strip(), f"empty label for {option_id}"
    assert opt.description.strip(), f"empty description for {option_id}"


@pytest.mark.parametrize("option_id", sorted(EXPECTED_PRIVACY_IDS))
def test_privacy_option_destructive_flag(option_id):
    opt = options.get_option(option_id)
    assert opt.is_destructive is (option_id in EXPECTED_DESTRUCTIVE)


def test_list_options_filter_only_returns_privacy_section():
    for meta in options.list_options("privacy"):
        assert meta["section"] == "privacy"
