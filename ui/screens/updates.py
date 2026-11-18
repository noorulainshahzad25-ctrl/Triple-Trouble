"""SCREEN 04: UPDATES — Change intelligence, recomputed domains vs. model tags called, and diffs."""

from __future__ import annotations

import html
from typing import Any

import streamlit as st

from ..adapter import compute_snapshot_diffs
from ..components.badges import source_chips_html, status_badge_html
from ..components.empty_states import render_awaiting_input_state, render_empty_section_notice
from ..components.hero import render_editorial_hero
from ..tokens import DOMAINS


def render_updates_screen(bundle: dict[str, Any]) -> None:
    """Render SCREEN 04: UPDATES."""
    render_editorial_hero(
        eyebrow="04 / UPDATES — CHANGE INTELLIGENCE",
        headline="THE CHANGE.\nAND THE REASON.",
        subtitle="How new messages affect an existing plan — strictly separating deterministic Python solver recomputation from actual LLM inference calls.",
        bundle=bundle,
    )

    if not bundle.get("loaded"):
        render_awaiting_input_state("04 / UPDATES")
        return

    recomputed = set(bundle.get("recomputed_areas") or [])
    changed = set(bundle.get("changed_areas") or [])
    called_tags = list(bundle.get("called_model_tags") or [])
    tel = bundle.get("telemetry", {})

    # 1. CHANGE RADAR: DOMAINS RECOMPUTED vs MODEL TAGS ACTUALLY CALLED
    st.markdown(
        """
<div class="mm-section-header">
  <div>
    <div class="mm-overline">SECTION 01 // ARCHITECTURAL SEPARATION OF CONCERNS</div>
    <h2 class="mm-section-title">CHANGE RADAR</h2>
  </div>
  <div class="mm-mono" style="color:var(--text-secondary);">
    DETERMINISTIC SOLVER PROPAGATION ≠ LLM INFERENCE CALLS
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    # Build domain pills for DOMAINS RECOMPUTED
    domain_cells_html = ""
    for d in DOMAINS:
        d_key = d["key"]
        is_recomp = d_key in recomputed
        is_changed = d_key in changed
        if is_changed:
            state_lbl = "RECOMPUTED · OUTPUT CHANGED"
            bg = "var(--stage-dark)"
            fg = "var(--accent)"
            bdr = "var(--stage-dark)"
        elif is_recomp:
            state_lbl = "RECOMPUTED · UNCHANGED VALUE"
            bg = "var(--surface-secondary)"
            fg = "var(--text-primary)"
            bdr = "var(--text-primary)"
        else:
            state_lbl = "CACHED · NOT TOUCHED"
            bg = "var(--surface-primary)"
            fg = "var(--text-secondary)"
            bdr = "var(--border-hairline)"

        domain_cells_html += (
            f'<div style="background:{bg};color:{fg};border:1px solid {bdr};padding:0.95rem 1.1rem;">'
            f'<div style="font-family:var(--font-mono);font-size:10px;letter-spacing:0.13em;opacity:0.8;">{html.escape(d["code"])}</div>'
            f'<div style="font-family:var(--font-display);font-size:22px;font-weight:800;margin:0.2rem 0;">{html.escape(d["title"])}</div>'
            f'<div style="font-family:var(--font-mono);font-size:10px;font-weight:700;letter-spacing:0.08em;">{state_lbl}</div>'
            f"</div>"
        )

    # Build tags for MODEL TAGS ACTUALLY CALLED
    all_possible_tags = [
        ("reading", "LLM MESSAGE EXTRACTION (FRESH INPUTS)"),
        ("venue", "VENUE SOLVER (DETERMINISTIC PYTHON — 0 LLM)"),
        ("schedule", "SCHEDULE SOLVER (DETERMINISTIC PYTHON — 0 LLM)"),
        ("food", "FOOD SOLVER (DETERMINISTIC PYTHON — 0 LLM)"),
        ("judging", "JUDGING SOLVER (DETERMINISTIC PYTHON — 0 LLM)"),
        ("budget", "BUDGET SOLVER (DETERMINISTIC PYTHON — 0 LLM)"),
    ]
    model_tag_rows = ""
    for tag_key, desc in all_possible_tags:
        was_called = tag_key in called_tags
        pill_bg = "#C9E76B" if was_called else "rgba(255,255,255,0.06)"
        pill_fg = "#141414" if was_called else "#9EA3A0"
        status_txt = "LLM CALLED" if was_called else "0 LLM CALLS"
        model_tag_rows += (
            f'<div style="display:flex;justify-content:space-between;align-items:center;padding:0.62rem 0;'
            f'border-bottom:1px solid var(--border-dark-hairline);">'
            f'<div>'
            f'<span style="font-family:var(--font-mono);font-size:12.5px;font-weight:700;color:var(--text-dark-primary);text-transform:uppercase;">TAG: {html.escape(tag_key)}</span>'
            f'<div style="font-size:12px;color:var(--text-dark-secondary);">{html.escape(desc)}</div>'
            f"</div>"
            f'<span style="font-family:var(--font-mono);font-size:10.5px;font-weight:700;letter-spacing:0.12em;'
            f'background:{pill_bg};color:{pill_fg};padding:0.25rem 0.6rem;">{status_txt}</span>'
            f"</div>"
        )

    st.markdown(
        f"""
<div style="display:grid;grid-template-columns:6.5fr 5.5fr;gap:1.5rem;margin-bottom:2.5rem;">
  <!-- Left Panel: DOMAINS RECOMPUTED (SOLVER) -->
  <div style="background:var(--surface-primary);border:1px solid var(--border-hairline);border-top:3px solid var(--text-primary);padding:1.65rem 1.75rem;">
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.5rem;margin-bottom:0.65rem;">
      <span class="mm-overline">DETERMINISTIC DEPENDENCY GRAPH</span>
      <span class="mm-mono" style="font-weight:700;">{len(recomputed)} / 5 DOMAINS RECOMPUTED</span>
    </div>
    <h3 style="font-family:var(--font-display);font-size:clamp(26px, 2.6vw, 36px);font-weight:800;letter-spacing:-0.03em;margin:0 0 0.5rem 0;">
      DOMAINS RECOMPUTED
    </h3>
    <p style="font-size:14px;color:var(--text-secondary);line-height:1.5;margin:0 0 1.15rem 0;">
      Computed in pure Python via <code>updater.affected()</code> and <code>planner.build()</code>. Recomputing these domains never invokes an external LLM.
    </p>
    <div style="display:grid;grid-template-columns:repeat(auto-fill, minmax(175px, 1fr));gap:0.75rem;">
      {domain_cells_html}
    </div>
  </div>

  <!-- Right Panel: MODEL TAGS ACTUALLY CALLED (LLM) -->
  <div style="background:var(--stage-dark);color:var(--text-dark-primary);border:1px solid var(--stage-dark);border-top:3px solid var(--accent);padding:1.65rem 1.75rem;">
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.5rem;margin-bottom:0.65rem;">
      <span class="mm-overline" style="color:var(--accent);">ACTUAL MODEL INFERENCE</span>
      <span class="mm-mono" style="color:var(--accent);font-weight:700;">{tel.get("call_count", 0)} TOTAL LLM CALLS</span>
    </div>
    <h3 style="font-family:var(--font-display);font-size:clamp(26px, 2.6vw, 36px);font-weight:800;letter-spacing:-0.03em;color:var(--text-dark-primary);margin:0 0 0.5rem 0;">
      MODEL TAGS ACTUALLY CALLED
    </h3>
    <p style="font-size:14px;color:var(--text-dark-secondary);line-height:1.5;margin:0 0 1rem 0;">
      Only fresh, non-duplicate messages trigger a single batched <code>reading</code> call. Domain planning and validation execute with zero model calls.
    </p>
    <div>
      {model_tag_rows}
    </div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    # 2. PREVIOUS VS CURRENT SNAPSHOT DIFFS
    st.markdown(
        """
<div class="mm-section-header">
  <div>
    <div class="mm-overline">SECTION 02 // STATE TRANSITION LEDGER</div>
    <h2 class="mm-section-title">PREVIOUS VS. CURRENT VALUES</h2>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    prev_state = bundle.get("previous_state")
    if prev_state is None:
        render_empty_section_notice(
            "BASELINE SNAPSHOT — NO PRIOR RUN ATTACHED",
            "This run was executed without a prior state snapshot (previous_state is None). All 5 domains were initialized from scratch. Select an incremental update run (e.g. run_02_update.json) to inspect before/after field diffs.",
            status_key="needs_review",
        )
    else:
        diffs = compute_snapshot_diffs(bundle)
        if not diffs:
            render_empty_section_notice(
                "ZERO PLAN DELTAS",
                "A previous snapshot was compared, and all final domain plan values remained identical after evaluating incoming messages.",
                status_key="valid",
            )
        else:
            diff_rows = ""
            for d in diffs:
                diff_rows += (
                    f"<tr>"
                    f'<td class="mm-mono" style="font-weight:700;text-transform:uppercase;">{html.escape(str(d["area"]))}</td>'
                    f'<td class="mm-mono">{html.escape(str(d["field"]))}</td>'
                    f'<td class="mm-mono" style="color:var(--text-secondary);text-decoration:line-through;">{html.escape(str(d["previous"]))}</td>'
                    f'<td class="mm-mono" style="font-weight:700;color:var(--verified);">{html.escape(str(d["current"]))}</td>'
                    f"<td>{source_chips_html(d.get('sources'))}</td>"
                    f"</tr>"
                )
            st.markdown(
                f"""
<div style="background:var(--surface-primary);border:1px solid var(--border-hairline);overflow-x:auto;margin-bottom:2rem;">
  <table class="mm-ledger-table">
    <thead>
      <tr>
        <th>DOMAIN</th>
        <th>AFFECTED FIELD</th>
        <th>PREVIOUS SNAPSHOT VALUE</th>
        <th>UPDATED CURRENT VALUE</th>
        <th>PROVENANCE SOURCES</th>
      </tr>
    </thead>
    <tbody>
      {diff_rows}
    </tbody>
  </table>
</div>
                """,
                unsafe_allow_html=True,
            )

    # 3. REJECTED UPDATES & MESSAGE DISPOSITION
    st.markdown(
        """
<div class="mm-section-header">
  <div>
    <div class="mm-overline">SECTION 03 // UPDATE DISPOSITION & PROVENANCE</div>
    <h2 class="mm-section-title">DECISION & REJECTION PROVENANCE</h2>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    decisions = bundle.get("decisions", [])
    if not decisions:
        render_empty_section_notice(
            "PROPOSITION DECISIONS",
            "No proposition-level decisions recorded in state.",
            status_key="needs_review",
        )
    else:
        d_rows = ""
        for dec in decisions:
            d_st = str(dec.get("status") or "accepted").lower()
            badge_key = (
                "valid"
                if d_st in {"accepted", "corroborated"}
                else ("invalid" if d_st in {"rejected", "unresolved"} else "needs_review")
            )
            d_rows += (
                f"<tr>"
                f'<td class="mm-mono" style="font-weight:700;">{html.escape(str(dec.get("source") or ""))}</td>'
                f'<td class="mm-mono" style="text-transform:uppercase;">{html.escape(str(dec.get("area") or ""))}</td>'
                f'<td class="mm-mono">{html.escape(str(dec.get("subject") or ""))}.{html.escape(str(dec.get("attribute") or ""))}</td>'
                f"<td>{status_badge_html(badge_key)} <span class='mm-mono' style='font-size:10.5px;'>({html.escape(d_st.upper())})</span></td>"
                f"<td>{html.escape(str(dec.get('reason') or ''))}</td>"
                f"<td>{source_chips_html(dec.get('references'))}</td>"
                f"</tr>"
            )
        st.markdown(
            f"""
<div style="background:var(--surface-primary);border:1px solid var(--border-hairline);overflow-x:auto;">
  <table class="mm-ledger-table">
    <thead>
      <tr>
        <th>SOURCE</th>
        <th>DOMAIN</th>
        <th>TARGET ATTRIBUTE</th>
        <th>DISPOSITION</th>
        <th>REASON / EVIDENCE</th>
        <th>REFERENCES</th>
      </tr>
    </thead>
    <tbody>
      {d_rows}
    </tbody>
  </table>
</div>
            """,
            unsafe_allow_html=True,
        )
