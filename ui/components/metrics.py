"""Minimalist 4-column metric rail with tabular numerals and provenance captions."""

from __future__ import annotations

import html
from typing import Any

import streamlit as st

from ..tokens import TOKEN_UNAVAILABLE_LABEL


def render_metric_rail(bundle: dict[str, Any]) -> None:
    """Render the 4-cell minimalist metric rail: Plan Status, Source Messages, Model Calls, Token Usage."""
    loaded = bool(bundle.get("loaded"))
    s_meta = bundle.get("status_meta", {})
    status_label = s_meta.get("label", "AWAITING INPUT")
    status_color = s_meta.get("color", "#676B69")

    validations = bundle.get("validations", [])
    passed_checks = sum(1 for c in validations if c.get("passed"))
    failed_checks = sum(1 for c in validations if not c.get("passed"))
    status_foot = (
        f"{passed_checks} passed · {failed_checks} failed/review"
        if loaded
        else "Load a run to evaluate constraints"
    )

    messages = bundle.get("messages", [])
    msg_total = len(messages) if loaded else "—"
    accepted_msgs = sum(
        1 for m in messages if m.get("status") in {"accepted", "corroborated", "mixed"}
    )
    rejected_msgs = len(bundle.get("rejected_messages", []))
    msg_foot = (
        f"{accepted_msgs} active · {rejected_msgs} rejected/flagged"
        if loaded
        else "0 messages ingested"
    )

    tel = bundle.get("telemetry", {})
    call_count = tel.get("call_count", 0) if loaded else "—"
    called_tags = bundle.get("called_model_tags", [])
    calls_foot = (
        f"Tags: {', '.join(called_tags).upper()}"
        if loaded and called_tags
        else ("0 LLM calls triggered" if loaded else "No inference recorded")
    )

    if not loaded:
        token_html = f'<div class="mm-metric-value-compact" style="color:var(--text-secondary);">AWAITING INPUT</div>'
        token_foot = "No provider telemetry loaded"
    elif tel.get("tokens_available"):
        tot = tel.get("total_tokens", 0)
        in_t = tel.get("input_tokens", 0)
        out_t = tel.get("output_tokens", 0)
        token_html = f'<div class="mm-metric-value">{tot:,}</div>'
        token_foot = f"{in_t:,} IN / {out_t:,} OUT tokens"
    else:
        token_html = (
            f'<div class="mm-metric-value-compact" style="color:var(--text-secondary);">'
            f"{html.escape(TOKEN_UNAVAILABLE_LABEL)}</div>"
        )
        token_foot = "Provider did not report token usage"

    st.markdown(
        f"""
<div class="mm-metric-rail" role="region" aria-label="Operational Metric Rail">
  <div class="mm-metric-cell">
    <div class="mm-overline">01 // PLAN STATUS</div>
    <div class="mm-metric-value-compact" style="color:{status_color};">{html.escape(status_label)}</div>
    <div class="mm-metric-foot">{html.escape(status_foot)}</div>
  </div>
  <div class="mm-metric-cell">
    <div class="mm-overline">02 // SOURCE MESSAGES</div>
    <div class="mm-metric-value">{html.escape(str(msg_total))}</div>
    <div class="mm-metric-foot">{html.escape(msg_foot)}</div>
  </div>
  <div class="mm-metric-cell">
    <div class="mm-overline">03 // MODEL CALLS</div>
    <div class="mm-metric-value">{html.escape(str(call_count))}</div>
    <div class="mm-metric-foot">{html.escape(calls_foot)}</div>
  </div>
  <div class="mm-metric-cell">
    <div class="mm-overline">04 // TOKEN USAGE</div>
    {token_html}
    <div class="mm-metric-foot">{html.escape(token_foot)}</div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )
