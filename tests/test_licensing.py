"""
Tests for winsvalinn.core.licensing.

No GUI, no real system calls. Keypairs are generated in-test and the embedded
public key is monkeypatched so the tests are self-contained and deterministic.
"""

from __future__ import annotations

import base64
import json
from datetime import date, timedelta

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from winsvalinn.core import licensing

# ─── Helpers ─────────────────────────────────────────────────────────────


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _make_keypair():
    sk = Ed25519PrivateKey.generate()
    pub_hex = (
        sk.public_key()
        .public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        .hex()
    )
    return sk, pub_hex


def _issue(
    sk,
    *,
    email="user@example.com",
    edition="empresarial",
    tier="enterprise",
    expiry=None,
    lic_id="LIC-TEST",
):
    payload = {
        "email": email,
        "edition": edition,
        "tier": tier,
        "expiry": expiry,
        "id": lic_id,
    }
    payload_b64 = _b64url(
        json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    )
    sig_b64 = _b64url(sk.sign(payload_b64.encode("ascii")))
    return f"WSV-{payload_b64}.{sig_b64}"


@pytest.fixture
def signed(monkeypatch):
    """Yield an issuer bound to a fresh keypair, with PUBLIC_KEY_HEX patched."""
    sk, pub_hex = _make_keypair()
    monkeypatch.setattr(licensing, "PUBLIC_KEY_HEX", pub_hex)
    return sk


# ─── (a) Valid key -> empresarial ────────────────────────────────────────


def test_valid_key_resolves_empresarial(signed):
    key = _issue(signed, edition="empresarial", tier="enterprise")

    payload = licensing.verify_license_key(key)
    assert payload is not None
    assert payload["edition"] == "empresarial"
    assert payload["email"] == "user@example.com"

    resolved = licensing.resolve_edition(key)
    assert resolved["edition"] == "empresarial"
    assert resolved["valid"] is True
    assert resolved["tier"] == "enterprise"
    assert resolved["email"] == "user@example.com"


def test_valid_key_with_future_expiry(signed):
    future = (date.today() + timedelta(days=365)).isoformat()
    key = _issue(signed, expiry=future)
    resolved = licensing.resolve_edition(key)
    assert resolved["valid"] is True
    assert resolved["edition"] == "empresarial"
    assert resolved["expiry"] == future


def test_free_edition_value_is_normalized(signed):
    key = _issue(signed, edition="free")
    resolved = licensing.resolve_edition(key)
    assert resolved["edition"] == "free"
    assert resolved["valid"] is False


# ─── (b) Tampered key -> None / free ─────────────────────────────────────


def test_tampered_payload_fails_verification(signed):
    key = _issue(signed, edition="free")
    # Flip the edition in the payload without re-signing.
    prefix, body = key.split("WSV-", 1)
    payload_b64, sig_b64 = body.split(".", 1)
    decoded = base64.urlsafe_b64decode(payload_b64 + "=" * (-len(payload_b64) % 4))
    tampered = decoded.replace(b'"free"', b'"empresarial"')
    tampered_b64 = _b64url(tampered)
    bad_key = f"WSV-{tampered_b64}.{sig_b64}"

    assert licensing.verify_license_key(bad_key) is None
    assert licensing.resolve_edition(bad_key)["edition"] == "free"
    assert licensing.resolve_edition(bad_key)["valid"] is False


def test_wrong_public_key_rejects_valid_signature(signed, monkeypatch):
    key = _issue(signed)
    # Swap in a different (valid-format) public key -> signature no longer matches.
    _other_sk, other_pub = _make_keypair()
    monkeypatch.setattr(licensing, "PUBLIC_KEY_HEX", other_pub)
    assert licensing.verify_license_key(key) is None
    assert licensing.resolve_edition(key)["valid"] is False


# ─── (c) Expired key -> free ─────────────────────────────────────────────


def test_expired_key_resolves_free(signed):
    past = (date.today() - timedelta(days=1)).isoformat()
    key = _issue(signed, expiry=past)

    # Signature is still valid (verify_license_key ignores expiry)...
    assert licensing.verify_license_key(key) is not None
    # ...but resolution downgrades to free.
    resolved = licensing.resolve_edition(key)
    assert resolved["edition"] == "free"
    assert resolved["valid"] is False
    assert resolved["expiry"] == past


def test_unparseable_expiry_resolves_free(signed):
    key = _issue(signed, expiry="not-a-date")
    resolved = licensing.resolve_edition(key)
    assert resolved["valid"] is False
    assert resolved["edition"] == "free"


# ─── (d) Invalid format -> None ──────────────────────────────────────────


@pytest.mark.parametrize(
    "bad",
    [
        None,
        "",
        "garbage",
        "WSV-onlyonepart",
        "WSV-.",
        "WSV-abc.",
        "WSV-.def",
        "NOPREFIX-abc.def",
        "WSV-!!!.???",
        "WSV-a.b.c",
    ],
)
def test_invalid_format_returns_none(signed, bad):
    assert licensing.verify_license_key(bad) is None
    assert licensing.resolve_edition(bad)["edition"] == "free"


# ─── Persistence (uses a tmp LOCALAPPDATA, no real system writes) ─────────


def test_save_load_clear_roundtrip(signed, tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    key = _issue(signed)

    assert licensing.load_saved_license() is None

    licensing.save_license(key)
    assert licensing.load_saved_license() == key

    # current_edition should reflect the persisted key.
    edition = licensing.current_edition()
    assert edition["valid"] is True
    assert edition["edition"] == "empresarial"

    licensing.clear_license()
    assert licensing.load_saved_license() is None
    assert licensing.current_edition()["edition"] == "free"


def test_clear_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    # No file present — must not raise.
    licensing.clear_license()
    assert licensing.load_saved_license() is None
