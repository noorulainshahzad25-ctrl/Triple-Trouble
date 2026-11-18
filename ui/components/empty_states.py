"""Art-directed empty, awaiting-input, and missing-snapshot states."""

from __future__ import annotations

import html
import streamlit as st

from .badges import status_badge_html


def render_awaiting_input_state(screen_title: str) -> None:
    """Render a deliberate editorial AWAITING INPUT state when no backend run is loaded."""
    badge = status_badge_html("awaiting_input")
    st.markdown(
        f"""
<div style="background:var(--surface-primary);border:1px solid var(--border-hairline);border-top:3px solid var(--text-secondary);padding:2.75rem 2.5rem;margin:1.5rem 0 2.5rem 0;">
  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:1rem;margin-bottom:1.25rem;">
    <span class="mm-overline">OPERATIONAL STATE // {html.escape(screen_title)}</span>
    {badge}
  </div>
  <div style="font-family:var(--font-display);font-size:clamp(32px, 4vw, 52px);font-weight:800;letter-spacing:-0.04em;line-height:0.96;text-transform:uppercase;color:var(--text-primary);margin-bottom:0.85rem;">
    AWAITING INPUT.
  </div>
  <p style="font-size:16px;line-height:1.55;color:var(--text-secondary);max-width:64ch;margin:0 0 1.5rem 0;">
    No persisted backend run has been selected or loaded into the studio. Select an existing run snapshot in the left instrument panel, upload a backend output JSON file, or execute the CLI pipeline against an event message pack:
  </p>
  <div style="background:var(--surface-secondary);border:1px solid var(--border-hairline);padding:0.95rem 1.2rem;font-family:var(--font-mono);font-size:12.5px;color:var(--text-primary);">
    python cli.py &lt;path-to-messages.txt&gt; --output outputs/latest.json
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_section_notice(title: str, reason: str, status_key: str = "needs_review") -> None:
    """Render a restrained editorial notice when a section has no records."""
    badge = status_badge_html(status_key)
    st.markdown(
        f"""
<div style="background:var(--surface-secondary);border:1px solid var(--border-hairline);padding:1.5rem 1.75rem;margin-bottom:1.25rem;">
  <div style="display:flex;justify-content:space-between;align-items:center;gap:1rem;margin-bottom:0.45rem;">
    <span class="mm-overline">{html.escape(title)}</span>
    {badge}
  </div>
  <div style="font-size:15px;color:var(--text-primary);line-height:1.5;">
    {html.escape(reason)}
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )
