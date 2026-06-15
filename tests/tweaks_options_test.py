"""Registration tests for the native 'tweaks' options (no handler execution)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import sidecar.options as options  # noqa: E402

# All option ids registered by opt_tweaks.py, mapped to expected destructiveness.
EXPECTED_TWEAKS = {
    "ui_tweak_start_left": True,
    "ui_tweak_hide_search": True,
    "ui_tweak_hide_widgets": True,
    "ui_tweak_hide_taskview": True,
    "ui_tweak_hide_chat": True,
    "ui_tweak_classic_context": True,
    "ui_tweak_show_extensions": True,
    "ui_tweak_show_hidden": True,
    "ui_tweak_disable_bing_search": True,
    "ui_tweak_small_taskbar": True,
    "ui_tweaks_apply_all": True,
    "dev_detect_environments": False,
    "dev_analyze_caches": False,
    "dev_clean_caches": True,
    "dev_defender_exclusions": True,
    "dev_check_wsl_docker": False,
    "find_duplicates_downloads": False,
}


def test_all_tweaks_options_registered():
    ids = {opt["id"] for opt in options.list_options("tweaks")}
    missing = set(EXPECTED_TWEAKS) - ids
    assert not missing, f"missing tweaks options: {missing}"


def test_tweaks_options_have_correct_section_and_edition():
    for opt in options.list_options("tweaks"):
        if opt["id"] in EXPECTED_TWEAKS:
            assert opt["section"] == "tweaks", opt["id"]
            assert opt["edition"] == "free", opt["id"]


def test_tweaks_options_destructiveness():
    by_id = {opt["id"]: opt for opt in options.list_options("tweaks")}
    for opt_id, destructive in EXPECTED_TWEAKS.items():
        assert by_id[opt_id]["is_destructive"] is destructive, opt_id


def test_tweaks_options_have_handlers():
    for opt_id in EXPECTED_TWEAKS:
        opt = options.get_option(opt_id)
        assert opt is not None, opt_id
        assert callable(opt.handler), opt_id


def test_tweaks_options_have_nonempty_labels_and_descriptions():
    for opt in options.list_options("tweaks"):
        if opt["id"] in EXPECTED_TWEAKS:
            assert opt["label"].strip(), opt["id"]
            assert opt["description"].strip(), opt["id"]
