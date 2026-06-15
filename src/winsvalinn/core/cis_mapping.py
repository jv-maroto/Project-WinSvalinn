"""
CIS mapping - Annotate security findings with CIS Benchmark references.

GUI-free and fully testable. Maps WinSvalinn security controls to a readable
reference from the CIS Microsoft Windows Benchmark, and annotates findings
produced by :func:`SecurityAudit.run_security_scan` with a ``cis`` field.

Matching is done by case-insensitive *inclusion*: a control's keyword is
matched against a finding's ``control``, ``category``, ``name``, ``text`` and
``message`` fields, so it works whether or not findings carry an explicit
``control`` identifier.
"""

from __future__ import annotations

# Control keyword -> human-readable CIS Benchmark reference.
# Keys match the control identifiers used by SecurityAudit.run_security_scan().
CIS_CONTROLS: dict[str, str] = {
    "smbv1": "CIS 18.3.1 — Deshabilitar SMBv1",
    "defender": "CIS 8.x — Antivirus / Microsoft Defender",
    "firewall": "CIS 9.x — Windows Defender Firewall",
    "autorun": "CIS 18.9.x — Deshabilitar AutoRun/AutoPlay",
    "rdp": "CIS 18.x — Remote Desktop (RDP)",
    "uac": "CIS 2.3.17 — Control de Cuentas de Usuario (UAC)",
    "bitlocker": "CIS 18.9.x — Cifrado de unidad BitLocker",
    "secure_boot": "CIS 18.9.x — Secure Boot",
    "updates": "CIS 18.9.x — Windows Update",
}

# Extra inclusion aliases -> control key, for findings without a ``control``
# field. Matched (lower-cased) against name/text/message/category.
_ALIASES: dict[str, str] = {
    "smbv1": "smbv1",
    "smb1": "smbv1",
    "smb v1": "smbv1",
    "defender": "defender",
    "antivirus": "defender",
    "firewall": "firewall",
    "autorun": "autorun",
    "autoplay": "autorun",
    "remote desktop": "rdp",
    "rdp": "rdp",
    "uac": "uac",
    "control de cuentas": "uac",
    "bitlocker": "bitlocker",
    "secure boot": "secure_boot",
    "update": "updates",
    "actualizaci": "updates",  # actualización/actualizaciones
}

# Fields scanned, in priority order, for inclusion matching.
_MATCH_FIELDS = ("control", "category", "name", "text", "message")


def cis_for_control(control: str | None) -> str | None:
    """Return the CIS reference for a known control key, or ``None``."""
    if not control:
        return None
    return CIS_CONTROLS.get(str(control).strip().lower())


def _match_finding(finding: dict) -> str | None:
    """Resolve the CIS reference for a single finding by inclusion."""
    # 1) Explicit control identifier wins.
    ref = cis_for_control(finding.get("control"))
    if ref:
        return ref

    # 2) Fall back to inclusion over text-ish fields via aliases.
    haystack = " ".join(
        str(finding[field]).lower() for field in _MATCH_FIELDS if finding.get(field)
    )
    if not haystack:
        return None

    for alias, control in _ALIASES.items():
        if alias in haystack:
            return CIS_CONTROLS.get(control)
    return None


def annotate(findings: list[dict] | None) -> list[dict]:
    """
    Add a ``cis`` field to each finding that maps to a CIS control.

    Returns a new list of new dicts (inputs are not mutated). Findings with no
    match are returned unchanged (no ``cis`` key added).
    """
    if not findings:
        return []

    annotated: list[dict] = []
    for finding in findings:
        if not isinstance(finding, dict):
            annotated.append(finding)
            continue
        ref = _match_finding(finding)
        new_finding = dict(finding)
        if ref:
            new_finding["cis"] = ref
        annotated.append(new_finding)
    return annotated


def annotate_audit(audit: dict | None) -> dict:
    """
    Annotate every finding bucket (issues/warnings/passed) of an audit dict.

    Returns a new dict with the same shape; non-list values are preserved.
    """
    if not audit:
        return {}

    result = dict(audit)
    for bucket in ("issues", "warnings", "passed"):
        if isinstance(result.get(bucket), list):
            result[bucket] = annotate(result[bucket])
    return result
