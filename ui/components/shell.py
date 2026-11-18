"""Sidebar navigation, top instrument strip, and read-only run selector."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

import streamlit as st

from ..adapter import discover_run_files, empty_bundle, format_audit_report, load_run_bundle
from ..tokens import (
    CREATIVE_DIRECTION,
    MONOGRAM,
    PRODUCT_NAME,
    SCREENS,
    TAGLINE,
    VISUAL_CONCEPT,
)
from .badges import status_badge_html


def render_sidebar_and_load_bundle() -> tuple[str, dict[str, Any]]:
    """Render the dark editorial studio sidebar and return (active_screen_id, run_bundle)."""
    if "mm_active_screen" not in st.session_state:
        st.session_state["mm_active_screen"] = "overview"

    screen_ids = [s["id"] for s in SCREENS]
    screen_labels = {s["id"]: s["nav_label"] for s in SCREENS}

    with st.sidebar:
        st.markdown(
            f"""
<div style="padding:0.35rem 0 1.25rem 0;border-bottom:1px solid var(--border-dark-hairline);margin-bottom:1.1rem;">
  <div style="display:flex;justify-content:space-between;align-items:center;">
    <span style="font-family:var(--font-display);font-size:24px;font-weight:900;letter-spacing:-0.04em;color:var(--text-dark-primary);">{MONOGRAM}</span>
    <span style="font-family:var(--font-mono);font-size:10px;font-weight:700;letter-spacing:0.14em;color:var(--accent);border:1px solid rgba(201,231,107,0.4);padding:2px 6px;">STUDIO</span>
  </div>
  <div style="font-family:var(--font-mono);font-size:10.5px;letter-spacing:0.16em;color:var(--text-dark-secondary);margin-top:0.35rem;">
    {PRODUCT_NAME}
  </div>
  <div style="font-size:12.5px;color:var(--text-dark-secondary);margin-top:0.2rem;">
    {TAGLINE}
  </div>
</div>
            """,
            unsafe_allow_html=True,
        )

        current_idx = (
            screen_ids.index(st.session_state["mm_active_screen"])
            if st.session_state["mm_active_screen"] in screen_ids
            else 0
        )
        selected_screen = st.radio(
            "NAVIGATION",
            options=screen_ids,
            index=current_idx,
            format_func=lambda sid: screen_labels[sid],
            label_visibility="collapsed",
        )
        if selected_screen != st.session_state["mm_active_screen"]:
            st.session_state["mm_active_screen"] = selected_screen
            st.rerun()

        st.markdown(
            '<hr style="border:none;border-top:1px solid var(--border-dark-hairline);margin:1.25rem 0 1rem 0;">',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="mm-overline" style="color:var(--text-dark-secondary);margin-bottom:0.45rem;">PERSISTED RUN SOURCE</div>',
            unsafe_allow_html=True,
        )

        discovered = discover_run_files()
        options_map: dict[str, Path | None] = {}
        for p in discovered:
            label = p.parent.name if p.name == "run_summary.json" else p.name
            options_map[label] = p
        options_map["[AWAITING INPUT — NO RUN]"] = None

        option_keys = list(options_map.keys())
        default_idx = 0
        selected_source_key = st.selectbox(
            "Active Output Snapshot",
            options=option_keys,
            index=default_idx,
            label_visibility="collapsed",
        )

        uploaded = st.file_uploader(
            "Load External Output (.json)",
            type=["json"],
            help="Read-only inspection of any persisted engine output JSON.",
        )

        bundle: dict[str, Any]
        if uploaded is not None:
            try:
                raw_json = json.loads(uploaded.getvalue().decode("utf-8"))
                bundle = load_run_bundle(uploaded_json=raw_json)
            except Exception:
                bundle = empty_bundle()
        else:
            chosen_path = options_map.get(selected_source_key)
            bundle = load_run_bundle(path=chosen_path)

        tel = bundle.get("telemetry", {})
        models_list = tel.get("models") or ["DETERMINISTIC / NONE"]
        s_meta = bundle.get("status_meta", {})
        s_color = s_meta.get("dark_color", "#9FA4A2")

        st.markdown(
            f"""
<div style="background:var(--surface-dark-elevated);border:1px solid var(--border-dark-hairline);padding:0.95rem 1rem;margin-top:0.85rem;">
  <div style="font-family:var(--font-mono);font-size:10px;letter-spacing:0.14em;color:var(--text-dark-secondary);">TELEMETRY READOUT</div>
  <div style="margin-top:0.55rem;font-family:var(--font-mono);font-size:11.5px;line-height:1.65;">
    <div><span style="color:var(--text-dark-secondary);">RUN   /</span> {html.escape(str(bundle.get("run_id")))}</div>
    <div><span style="color:var(--text-dark-secondary);">MODEL /</span> {html.escape(", ".join(models_list))}</div>
    <div><span style="color:var(--text-dark-secondary);">STATE /</span> <span style="color:{s_color};font-weight:700;">{html.escape(s_meta.get("label", "AWAITING INPUT"))}</span></div>
  </div>
</div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("REFRESH FROM DISK", use_container_width=True):
            st.rerun()

    return st.session_state["mm_active_screen"], bundle


def render_top_instrument_strip(active_screen_id: str, bundle: dict[str, Any]) -> None:
    """Render the top editorial instrument bar across all screens."""
    screen_meta = next((s for s in SCREENS if s["id"] == active_screen_id), SCREENS[0])
    loaded = bool(bundle.get("loaded"))
    raw_status = bundle.get("status") if loaded else "awaiting_input"
    badge = status_badge_html(raw_status)
    run_id = html.escape(str(bundle.get("run_id") or "NONE"))
    freshness = html.escape(str(bundle.get("freshness") or "AWAITING INPUT"))

    st.markdown(
        f"""
<div class="mm-top-strip">
  <div class="mm-top-strip-left">
    <span style="font-family:var(--font-mono);font-size:11.5px;font-weight:700;letter-spacing:0.15em;color:var(--text-primary);">
      {MONOGRAM} // {VISUAL_CONCEPT}
    </span>
    <span class="mm-overline">ROUTE: {html.escape(screen_meta["nav_label"])}</span>
    <span class="mm-overline">DIRECTION: {CREATIVE_DIRECTION}</span>
  </div>
  <div class="mm-top-strip-right">
    <span class="mm-mono" style="color:var(--text-secondary);">RUN: <strong style="color:var(--text-primary);">{run_id}</strong></span>
    <span class="mm-mono" style="color:var(--text-secondary);">UPDATED: {freshness}</span>
    {badge}
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )
    report_txt = format_audit_report(bundle)
    return None
