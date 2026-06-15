"""Asset path utilities for WinSvalinn."""

import os

_ASSETS_DIR = os.path.dirname(os.path.abspath(__file__))


def get_asset_path(filename):
    """Get absolute path to an asset file."""
    return os.path.join(_ASSETS_DIR, filename)


def get_icon_path():
    """Get path to the application icon."""
    return get_asset_path("icon.ico")


def get_logo_path(variant="logo"):
    """Get path to a logo variant: 'logo', 'logo_small', 'logo_splash'."""
    return get_asset_path(f"{variant}.png")
