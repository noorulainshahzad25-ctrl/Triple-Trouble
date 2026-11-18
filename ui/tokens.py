"""Shared design tokens, validation semantics, and editorial copy dictionary for MIND / MACHINE."""

from __future__ import annotations

PRODUCT_NAME = "MIND / MACHINE"
MONOGRAM = "M//M"
TAGLINE = "Messy messages. Defensible decisions."
CREATIVE_DIRECTION = "EDITORIAL / INTELLIGENCE"
VISUAL_CONCEPT = "THE DECISION STUDIO"

# Section 3: Exact Visual Design System Palette
PALETTE = {
    "bg_main": "#F5F4F0",
    "surface_primary": "#FFFFFF",
    "surface_secondary": "#ECEAE4",
    "text_primary": "#141414",
    "text_secondary": "#676B69",
    "border_hairline": "#D8D8D2",
    "stage_dark": "#151719",
    "surface_dark_elevated": "#232629",
    "accent": "#C9E76B",
    "verified": "#2D7452",
    "failed": "#B63E3D",
    "warning": "#9B680B",
}

# Section 6: Exact Validation Semantics
VALIDATION_SEMANTICS = {
    "valid": {
        "label": "VERIFIED",
        "symbol": "✓",
        "color": PALETTE["verified"],
        "dark_color": PALETTE["accent"],
        "bg": "rgba(45, 116, 82, 0.10)",
        "border": "rgba(45, 116, 82, 0.35)",
        "description": "All applicable mandatory constraints pass.",
    },
    "invalid": {
        "label": "CONSTRAINT FAILED",
        "symbol": "✕",
        "color": PALETTE["failed"],
        "dark_color": "#EF6E6D",
        "bg": "rgba(182, 62, 61, 0.10)",
        "border": "rgba(182, 62, 61, 0.38)",
        "description": "At least one known mandatory requirement fails.",
    },
    "needs_review": {
        "label": "NEEDS REVIEW",
        "symbol": "?",
        "color": PALETTE["warning"],
        "dark_color": "#EAB64D",
        "bg": "rgba(155, 104, 11, 0.10)",
        "border": "rgba(155, 104, 11, 0.38)",
        "description": "Essential verification is missing or unknown.",
    },
    "awaiting_input": {
        "label": "AWAITING INPUT",
        "symbol": "○",
        "color": PALETTE["text_secondary"],
        "dark_color": "#9FA4A2",
        "bg": "rgba(103, 107, 105, 0.10)",
        "border": "rgba(103, 107, 105, 0.32)",
        "description": "No run has been loaded.",
    },
}

TOKEN_UNAVAILABLE_LABEL = "TOKEN USAGE UNAVAILABLE"

SCREENS = [
    {
        "id": "overview",
        "index": "01",
        "nav_label": "01 / OVERVIEW",
        "short_label": "OVERVIEW",
        "eyebrow": "01 / OVERVIEW — COMMAND CENTER",
        "headline": "MESSY INPUT.\nCLEAR DECISIONS.",
        "subtitle": "The plan isn't a guess. Every choice has a reason, a source and a validation result.",
    },
    {
        "id": "plan",
        "index": "02",
        "nav_label": "02 / THE PLAN",
        "short_label": "THE PLAN",
        "eyebrow": "02 / THE PLAN — DOMAIN INSTRUMENTS",
        "headline": "FIVE DECISIONS.\nONE ACCOUNTABLE PLAN.",
        "subtitle": "Constraint-validated selections across venue, schedule, catering, judging workload and financial ceiling.",
    },
    {
        "id": "audit",
        "index": "03",
        "nav_label": "03 / AUDIT TRAIL",
        "short_label": "AUDIT TRAIL",
        "eyebrow": "03 / AUDIT TRAIL — EVIDENCE & INFERENCE",
        "headline": "EVERY DECISION.\nACCOUNTED FOR.",
        "subtitle": "Recorded model calls, exact prompts and responses, rejected instructions and deterministic validation checks.",
    },
    {
        "id": "updates",
        "index": "04",
        "nav_label": "04 / UPDATES",
        "short_label": "CHANGE INTELLIGENCE",
        "eyebrow": "04 / UPDATES — CHANGE INTELLIGENCE",
        "headline": "THE CHANGE.\nAND THE REASON.",
        "subtitle": "Selective state propagation separating deterministic domain recomputation from actual LLM inference calls.",
    },
    {
        "id": "system",
        "index": "05",
        "nav_label": "05 / SYSTEM",
        "short_label": "SYSTEM HEALTH",
        "eyebrow": "05 / SYSTEM — OPERATIONAL LEDGER",
        "headline": "THE RECEIPTS.",
        "subtitle": "Run identity, data freshness, provider telemetry, persisted output verification and auditable report export.",
    },
]

DOMAINS = [
    {
        "key": "venue",
        "index": "01",
        "code": "01 / VENUE",
        "title": "VENUE",
        "instrument": "OCCUPANCY & FACILITY INSTRUMENT",
    },
    {
        "key": "schedule",
        "index": "02",
        "code": "02 / SCHEDULE",
        "title": "SCHEDULE",
        "instrument": "CHRONOLOGICAL TIMELINE RAIL",
    },
    {
        "key": "food",
        "index": "03",
        "code": "03 / FOOD",
        "title": "FOOD",
        "instrument": "MEAL COVERAGE & SUPPLY INSTRUMENT",
    },
    {
        "key": "judging",
        "index": "04",
        "code": "04 / JUDGING",
        "title": "JUDGING",
        "instrument": "EVALUATION CAPACITY MATRIX",
    },
    {
        "key": "budget",
        "index": "05",
        "code": "05 / BUDGET",
        "title": "BUDGET",
        "instrument": "SEGMENTED ALLOCATION & FINANCIAL LEDGER",
    },
]


def status_meta(raw_status: str | None) -> dict:
    """Return canonical validation metadata for a backend status string."""
    if not raw_status:
        return VALIDATION_SEMANTICS["awaiting_input"]
    normalized = str(raw_status).strip().lower()
    if normalized in VALIDATION_SEMANTICS:
        return VALIDATION_SEMANTICS[normalized]
    if normalized in {"pass", "passed", "verified", "ok", "accepted"}:
        return VALIDATION_SEMANTICS["valid"]
    if normalized in {"fail", "failed", "rejected", "error", "constraint_failed"}:
        return VALIDATION_SEMANTICS["invalid"]
    return VALIDATION_SEMANTICS["needs_review"]
