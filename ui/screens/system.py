"""SCREEN 05: SYSTEM — Operational ledger, telemetry receipts, file inventory, and export."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

import streamlit as st

from ..adapter import ROOT_DIR, format_audit_report, inspect_workspace_files
from ..components.badges import source_chips_html, status_badge_html
from ..components.empty_states import render_awaiting_input_state, render_empty_section_notice
from ..components.hero import render_editorial_hero
from ..tokens import TOKEN_UNAVAILABLE_LABEL


def render_system_screen(bundle: dict[str, Any]) -> None:
    """Render SCREEN 05: SYSTEM ('THE RECEIPTS.')."""
    render_editorial_hero(
        eyebrow="05 / SYSTEM — OPERATIONAL LEDGER",
        headline="THE RECEIPTS.",
        subtitle="Verifiable operational telemetry: run identity, data freshness, provider usage, persisted file checksums, error diagnostics and report export.",
        bundle=bundle,
    )

    loaded = bool(bundle.get("loaded"))
    tel = bundle.get("telemetry", {})
    models_str = ", ".join(tel.get("models") or []) or "NONE / DETERMINISTIC"
    providers_str = ", ".join(tel.get("providers") or []) or "NONE / LOCAL ENGINE"
    dur_ms = tel.get("duration_ms")
    dur_str = (
        f"{dur_ms:,.1f} ms ({dur_ms / 1000.0:.2f} s)"
        if isinstance(dur_ms, (int, float))
        else "NOT REPORTED"
    )
    if loaded and tel.get("tokens_available"):
        tok_summary = f"{tel['total_tokens'] if tel.get('total_tokens') is not None else '—'} TOTAL ({tel['input_tokens'] if tel.get('input_tokens') is not None else '—'} IN / {tel['output_tokens'] if tel.get('output_tokens') is not None else '—'} OUT)"
    else:
        tok_summary = TOKEN_UNAVAILABLE_LABEL

    # Read domain classifier metadata if available
    clf_path = ROOT_DIR / "engine" / "domain_model.json"
    clf_info = "UNAVAILABLE"
    if clf_path.is_file():
        try:
            clf_data = json.loads(clf_path.read_text(encoding="utf-8"))
            clf_info = (
                f"Mode: {clf_data.get('mode')} · Examples: {clf_data.get('training_examples')} "
                f"· LOO Micro-F1: {clf_data.get('selection_micro_f1')}"
            )
        except Exception:
            clf_info = "PRESENT (PARSE ERROR)"

    # 1. OPERATIONAL TELEMETRY LEDGER
    st.markdown(
        f"""
<div class="mm-section-header">
  <div>
    <div class="mm-overline">SECTION 01 // RUN TELEMETRY & PROVENANCE</div>
    <h2 class="mm-section-title">OPERATIONAL LEDGER</h2>
  </div>
</div>

<div style="background:var(--surface-primary);border:1px solid var(--border-hairline);border-top:2px solid var(--text-primary);margin-bottom:2.25rem;">
  <table class="mm-ledger-table">
    <tbody>
      <tr>
        <td class="mm-overline" style="width:28%;background:var(--surface-secondary);">RUN IDENTIFIER</td>
        <td class="mm-mono" style="font-weight:700;">{html.escape(str(bundle.get("run_id")))}</td>
        <td class="mm-overline" style="width:24%;background:var(--surface-secondary);">DATA FRESHNESS</td>
        <td class="mm-mono">{html.escape(str(bundle.get("freshness")))}</td>
      </tr>
      <tr>
        <td class="mm-overline" style="background:var(--surface-secondary);">ACTUAL MODEL NAMES</td>
        <td class="mm-mono" style="font-weight:700;">{html.escape(models_str)}</td>
        <td class="mm-overline" style="background:var(--surface-secondary);">PROVIDER NAMES</td>
        <td class="mm-mono">{html.escape(providers_str)}</td>
      </tr>
      <tr>
        <td class="mm-overline" style="background:var(--surface-secondary);">MODEL-CALL TOTALS</td>
        <td class="mm-mono" style="font-weight:700;">{html.escape(str(tel.get("call_count", 0)))} CALLS ({len(bundle.get("model_calls", []))} TRACE RECORDS)</td>
        <td class="mm-overline" style="background:var(--surface-secondary);">REPORTED TOKEN USAGE</td>
        <td class="mm-mono" style="font-weight:700;">{html.escape(tok_summary)}</td>
      </tr>
      <tr>
        <td class="mm-overline" style="background:var(--surface-secondary);">EXECUTION TIME</td>
        <td class="mm-mono">{html.escape(dur_str)}</td>
        <td class="mm-overline" style="background:var(--surface-secondary);">SCHEMA VERSION</td>
        <td class="mm-mono">v{html.escape(str(bundle.get("state", {}).get("schema_version", 1)))}</td>
      </tr>
      <tr>
        <td class="mm-overline" style="background:var(--surface-secondary);">FALLBACK DOMAIN CLASSIFIER</td>
        <td class="mm-mono" colspan="3">{html.escape(clf_info)}</td>
      </tr>
    </tbody>
  </table>
</div>
        """,
        unsafe_allow_html=True,
    )

    # 2. AVAILABLE OUTPUT FILES INVENTORY
    st.markdown(
        """
<div class="mm-section-header">
  <div>
    <div class="mm-overline">SECTION 02 // DISK ARTIFACTS</div>
    <h2 class="mm-section-title">AVAILABLE OUTPUT FILES</h2>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    files_inventory = inspect_workspace_files(bundle)
    f_rows = ""
    for f_rec in files_inventory:
        present = bool(f_rec.get("present"))
        st_badge = status_badge_html("valid" if present else "awaiting_input")
        sz_str = f"{f_rec['size_bytes']:,} B" if f_rec.get("size_bytes") is not None else "—"
        f_rows += (
            f"<tr>"
            f'<td><strong>{html.escape(str(f_rec["role"]))}</strong></td>'
            f'<td class="mm-mono">{html.escape(str(f_rec["path"]))}</td>'
            f"<td>{st_badge}</td>"
            f'<td class="mm-mono">{html.escape(sz_str)}</td>'
            f'<td class="mm-mono">{html.escape(str(f_rec["sha256"]))}</td>'
            f'<td class="mm-mono">{html.escape(str(f_rec["modified"]))}</td>'
            f"</tr>"
        )

    st.markdown(
        f"""
<div style="background:var(--surface-primary);border:1px solid var(--border-hairline);overflow-x:auto;margin-bottom:2.25rem;">
  <table class="mm-ledger-table">
    <thead>
      <tr>
        <th>ARTIFACT ROLE</th>
        <th>RELATIVE PATH</th>
        <th>AVAILABILITY</th>
        <th>SIZE</th>
        <th>SHA-256 PREFIX</th>
        <th>LAST MODIFIED</th>
      </tr>
    </thead>
    <tbody>
      {f_rows}
    </tbody>
  </table>
</div>
        """,
        unsafe_allow_html=True,
    )

    # 3. ERROR & UNRESOLVED DIAGNOSTICS
    st.markdown(
        """
<div class="mm-section-header">
  <div>
    <div class="mm-overline">SECTION 03 // SYSTEM RELIABILITY & TRIAGE</div>
    <h2 class="mm-section-title">ERROR & EXCEPTION LEDGER</h2>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    if not loaded:
        render_awaiting_input_state("05 / SYSTEM")
        return

    error_msgs = [m for m in bundle.get("messages", []) if m.get("error")]
    unresolved_checks = [c for c in bundle.get("validations", []) if not c.get("passed")]

    if not error_msgs and not unresolved_checks:
        render_empty_section_notice(
            "ZERO OPERATIONAL ERRORS",
            "All ingested messages parsed cleanly and all mandatory validation checks passed without unresolved exceptions.",
            status_key="valid",
        )
    else:
        for em in error_msgs:
            hints = em.get("domain_hints") or []
            st.markdown(
                f"""
<div class="mm-rejection-card">
  <div style="display:flex;justify-content:space-between;align-items:center;">
    <span class="mm-mono" style="font-weight:700;">EXTRACTION FAILURE // MESSAGE {html.escape(str(em.get("id")))}</span>
    {status_badge_html("invalid")}
  </div>
  <p style="font-size:14.5px;margin:0.45rem 0;">{html.escape(str(em.get("error")))}</p>
  <div class="mm-mono" style="font-size:11.5px;color:var(--text-secondary);">
    SUPERVISED CLASSIFIER TRIAGE HINTS: {html.escape(", ".join(hints).upper() if hints else "NONE")}
  </div>
</div>
                """,
                unsafe_allow_html=True,
            )

        for uc in unresolved_checks:
            st_key = "needs_review" if uc.get("unresolved") else "invalid"
            st.markdown(
                f"""
<div class="mm-rejection-card" style="border-left-color:{"var(--warning)" if uc.get("unresolved") else "var(--failed)"};">
  <div style="display:flex;justify-content:space-between;align-items:center;">
    <span class="mm-mono" style="font-weight:700;">CHECK // {html.escape(str(uc.get("check")))}</span>
    {status_badge_html(st_key)}
  </div>
  <p style="font-size:14.5px;margin:0.45rem 0;">{html.escape(str(uc.get("reason")))}</p>
  <div>{source_chips_html(uc.get("evidence"))}</div>
</div>
                """,
                unsafe_allow_html=True,
            )

    # 4. EXPORT FUNCTIONALITY
    st.markdown(
        """
<div class="mm-section-header" style="margin-top:2.25rem;">
  <div>
    <div class="mm-overline">SECTION 04 // AUDITABLE RECEIPTS</div>
    <h2 class="mm-section-title">EXPORT FUNCTIONALITY</h2>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    report_md = format_audit_report(bundle)
    raw_json_str = json.dumps(
        {
            "run_id": bundle.get("run_id"),
            "freshness": bundle.get("freshness"),
            "status": bundle.get("status"),
            "plan": bundle.get("plan"),
            "validations": bundle.get("validations"),
            "rejected_messages": bundle.get("rejected_messages"),
            "changed_areas": bundle.get("changed_areas"),
            "predicted_model_areas": bundle.get("predicted_model_areas"),
            "model_calls": bundle.get("model_calls"),
        },
        indent=2,
        ensure_ascii=False,
    )

    exp_col1, exp_col2, exp_col3 = st.columns([3.5, 3.5, 5.0])
    with exp_col1:
        st.download_button(
            label="DOWNLOAD AUDIT REPORT (.MD)",
            data=report_md.encode("utf-8"),
            file_name=f"{bundle.get('run_id', 'mind_machine').lower()}_audit_report.md",
            mime="text/markdown",
            type="primary",
            use_container_width=True,
        )
    with exp_col2:
        st.download_button(
            label="DOWNLOAD ENGINE RECEIPT (.JSON)",
            data=raw_json_str.encode("utf-8"),
            file_name=f"{bundle.get('run_id', 'mind_machine').lower()}_output.json",
            mime="application/json",
            use_container_width=True,
        )

    with st.expander("Preview Formatted Auditable Decision Report"):
        st.code(report_md, language="markdown")
