"""Editorial hero component with asymmetric live status monument."""

from __future__ import annotations

import html
from typing import Any

import streamlit as st

from .badges import status_badge_html


def render_editorial_hero(
    *,
    eyebrow: str,
    headline: str,
    subtitle: str,
    bundle: dict[str, Any],
    show_overview_actions: bool = False,
) -> None:
    """Render the oversized Axial-inspired editorial hero and live run status monument."""
    loaded = bool(bundle.get("loaded"))
    raw_status = bundle.get("status") if loaded else "awaiting_input"
    s_meta = bundle.get("status_meta", {})
    badge_html = status_badge_html(raw_status)
    run_id = html.escape(str(bundle.get("run_id") or "NONE"))
    freshness = html.escape(str(bundle.get("freshness") or "AWAITING INPUT"))

    validations = bundle.get("validations", [])
    passed_count = sum(1 for c in validations if c.get("passed"))
    total_checks = len(validations)
    check_summary = (
        f"{passed_count} / {total_checks} CONSTRAINTS PASSED"
        if loaded and total_checks > 0
        else "NO VALIDATIONS RECORDED"
    )
    accent_border = s_meta.get("color", "#141414")
    headline_html = html.escape(headline)

    st.markdown(
        f"""
<div class="mm-hero-grid">
  <div>
    <div class="mm-overline">{html.escape(eyebrow)}</div>
    <h1 class="mm-display-headline">{headline_html}</h1>
    <p class="mm-hero-subtitle">{html.escape(subtitle)}</p>
  </div>
  <div class="mm-hero-monument" style="border-top-color:{accent_border};">
    <div style="display:flex;justify-content:space-between;align-items:center;gap:0.75rem;flex-wrap:wrap;">
      <span class="mm-overline">ACTUAL PLAN STATUS</span>
      {badge_html}
    </div>
    <div style="padding:0.5rem 0;border-top:1px solid var(--border-hairline);border-bottom:1px solid var(--border-hairline);">
      <div style="font-family:var(--font-display);font-size:clamp(26px, 2.8vw, 40px);font-weight:800;letter-spacing:-0.035em;line-height:1.0;color:{accent_border};">
        {html.escape(s_meta.get("label", "AWAITING INPUT"))}
      </div>
      <div style="font-size:13.5px;color:var(--text-secondary);margin-top:0.35rem;">
        {html.escape(s_meta.get("description", "No run has been loaded."))}
      </div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.75rem;">
      <div>
        <div class="mm-overline" style="font-size:10px;">RUN IDENTIFIER</div>
        <div class="mm-mono" style="font-weight:700;color:var(--text-primary);margin-top:0.2rem;">{run_id}</div>
      </div>
      <div>
        <div class="mm-overline" style="font-size:10px;">VALIDATION GATE</div>
        <div class="mm-mono" style="font-weight:700;color:var(--text-primary);margin-top:0.2rem;">{html.escape(check_summary)}</div>
      </div>
    </div>
    <div class="mm-mono" style="font-size:11px;color:var(--text-secondary);">
      FRESHNESS // {freshness}
    </div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    if show_overview_actions:
        col_a, col_b, col_spacer = st.columns([2.2, 2.2, 7.6])
        with col_a:
            if st.button("VIEW THE PLAN →", key="hero_btn_view_plan", type="primary", use_container_width=True):
                st.session_state["mm_active_screen"] = "plan"
                st.rerun()
        with col_b:
            if st.button("INSPECT EVIDENCE →", key="hero_btn_inspect_audit", use_container_width=True):
                st.session_state["mm_active_screen"] = "audit"
                st.rerun()
