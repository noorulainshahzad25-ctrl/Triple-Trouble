"""Validation status badges, source reference chips, and role/domain pills."""

from __future__ import annotations

import html
from typing import Iterable

from ..tokens import PALETTE, status_meta


def status_badge_html(raw_status: str | None, *, dark_stage: bool = False) -> str:
    """Render an accessible validation status badge with symbol + canonical uppercase label."""
    meta = status_meta(raw_status)
    color = meta["dark_color"] if dark_stage else meta["color"]
    bg = "rgba(255, 255, 255, 0.05)" if dark_stage else meta["bg"]
    border = color if dark_stage else meta["border"]
    label = html.escape(meta["label"])
    symbol = html.escape(meta["symbol"])
    return (
        f'<span class="mm-status-badge" style="color:{color};background:{bg};border-color:{border};">'
        f"<span>{symbol}</span><span>{label}</span>"
        f"</span>"
    )


def source_chips_html(sources: Iterable[str] | None, *, dark_stage: bool = False) -> str:
    """Render monospace source-reference chips (e.g., M0001, M0004)."""
    items = [str(s).strip() for s in (sources or []) if str(s).strip()]
    if not items:
        cls = "mm-source-chip-dark" if dark_stage else "mm-source-chip"
        return f'<span class="{cls}" style="opacity:0.65;">NO SOURCE REF</span>'
    cls = "mm-source-chip-dark" if dark_stage else "mm-source-chip"
    return "".join(f'<span class="{cls}">{html.escape(s)}</span>' for s in items)


def fmt_amount(val: object, currency: str = "PKR") -> str:
    """Format numeric currency or count values cleanly without inventing missing data."""
    if val is None or val == "":
        return "UNRESOLVED"
    try:
        num = int(str(val))
        return f"{currency} {num:,}" if currency else f"{num:,}"
    except ValueError:
        try:
            flt = float(str(val))
            return f"{currency} {flt:,.2f}" if currency else f"{flt:,.2f}"
        except ValueError:
            return str(val)


def fmt_int(val: object, suffix: str = "") -> str:
    """Format an integer metric or return UNRESOLVED if None."""
    if val is None or val == "":
        return "UNRESOLVED"
    try:
        num = int(str(val))
        return f"{num:,}{suffix}"
    except ValueError:
        return f"{val}{suffix}"
