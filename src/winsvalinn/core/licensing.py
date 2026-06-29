"""
Licensing - Offline Ed25519 license verification for WinSvalinn.

This module is GUI-free and fully testable. It verifies signed license keys
against an embedded public key, resolves the active edition (free vs.
empresarial), and persists the validated key under %LOCALAPPDATA%.

License key format (exact):

    WSV-<payload_b64url_no_padding>.<sig_b64url_no_padding>

- The Ed25519 signature is computed over the ASCII bytes of the
  *base64url payload string* (NOT the decoded JSON).
- The decoded payload is a JSON object with fields:
    email (str), edition ("empresarial"|"free"), tier (str),
    expiry (null or "YYYY-MM-DD"), id (str).
- base64url is decoded by re-adding padding: s + "=" * (-len(s) % 4).
"""

from __future__ import annotations

import base64
import json
import logging
import os
from datetime import date
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

logger = logging.getLogger(__name__)

# 32-byte raw Ed25519 public key (hex). Single source of truth for verification.
PUBLIC_KEY_HEX = "dbb11a1150b061c253da02ade1e2d767e96ce956babbd9e7482e7bebd0bc7534"

_KEY_PREFIX = "WSV-"
_LICENSE_FILENAME = "license.key"


def _b64url_decode(data: str) -> bytes:
    """Decode a base64url string with padding re-added."""
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def verify_license_key(key: str | None) -> dict | None:
    """
    Parse and verify the signature of a license key.

    Returns the decoded payload dict if the signature is valid (expiry is NOT
    checked here), or None if the format or signature is invalid.
    """
    if not key or not isinstance(key, str):
        return None

    key = key.strip()
    if not key.startswith(_KEY_PREFIX):
        return None

    body = key[len(_KEY_PREFIX) :]
    if body.count(".") != 1:
        return None

    payload_b64, sig_b64 = body.split(".", 1)
    if not payload_b64 or not sig_b64:
        return None

    try:
        sig_raw = _b64url_decode(sig_b64)
        payload_raw = _b64url_decode(payload_b64)
    except (ValueError, base64.binascii.Error):
        return None

    try:
        public_key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(PUBLIC_KEY_HEX))
        # Signature is over the ASCII bytes of the base64url payload string.
        public_key.verify(sig_raw, payload_b64.encode("ascii"))
    except (InvalidSignature, ValueError):
        return None

    try:
        payload = json.loads(payload_raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None

    if not isinstance(payload, dict):
        return None

    return payload


def resolve_edition(key: str | None) -> dict:
    """
    Verify the key and check expiry, returning the resolved edition info.

    Returns a dict with keys: edition, tier, valid, expiry, email.
    Edition is "free" when the key is missing, malformed, badly signed, or
    expired. Any non-"empresarial" edition value is normalized to "free".
    """
    free = {
        "edition": "free",
        "tier": None,
        "valid": False,
        "expiry": None,
        "email": None,
    }

    payload = verify_license_key(key)
    if payload is None:
        return free

    expiry = payload.get("expiry")
    if expiry is not None:
        try:
            if date.fromisoformat(str(expiry)) < date.today():
                # Expired: signature valid but no longer usable.
                return {**free, "expiry": expiry, "email": payload.get("email")}
        except (ValueError, TypeError):
            # Unparseable expiry -> treat as invalid.
            return free

    edition = payload.get("edition")
    if edition != "empresarial":
        edition = "free"

    return {
        "edition": edition,
        "tier": payload.get("tier"),
        "valid": edition == "empresarial",
        "expiry": expiry,
        "email": payload.get("email"),
    }


def _license_dir() -> Path:
    """Return the directory where the license file is stored.

    Uses %APPDATA% (Roaming), NOT %LOCALAPPDATA%: the app installs under
    %LOCALAPPDATA%\\WinSvalinn, so storing the license there would wipe it on
    every reinstall/update. Roaming survives updates.
    """
    base = os.environ.get("APPDATA")
    if base:
        return Path(base) / "WinSvalinn"
    return Path.home() / "WinSvalinn"


def _license_path() -> Path:
    """Return the full path to the license key file."""
    return _license_dir() / _LICENSE_FILENAME


def _legacy_license_path() -> Path:
    """Old location (%LOCALAPPDATA%) — read-only, for migration."""
    base = os.environ.get("LOCALAPPDATA")
    root = Path(base) if base else Path.home()
    return root / "WinSvalinn" / _LICENSE_FILENAME


def load_saved_license() -> str | None:
    """Read the saved license key from disk, or None if not present/unreadable.

    Falls back to the legacy %LOCALAPPDATA% location and migrates it so users who
    activated before the move don't lose their license.
    """
    for path in (_license_path(), _legacy_license_path()):
        try:
            if path.is_file():
                content = path.read_text(encoding="utf-8").strip()
                if content:
                    if path != _license_path():
                        try:
                            save_license(content)
                        except OSError:
                            pass
                    return content
        except OSError as exc:
            logger.warning("Could not read saved license at %s: %s", path, exc)
    return None


def save_license(key: str) -> None:
    """Persist the license key (only the key string) under %APPDATA%."""
    path = _license_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(key.strip(), encoding="utf-8")
    except OSError as exc:
        logger.error("Could not save license: %s", exc)
        raise


def clear_license() -> None:
    """Remove the saved license file if it exists."""
    path = _license_path()
    try:
        path.unlink(missing_ok=True)
    except OSError as exc:
        logger.warning("Could not clear license: %s", exc)


def current_edition() -> dict:
    """Resolve the edition for the currently saved license."""
    return resolve_edition(load_saved_license())
