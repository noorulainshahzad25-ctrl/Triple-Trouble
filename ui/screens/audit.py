"""SCREEN 03: AUDIT TRAIL — Evidence, model inference trace, and rejection inspection."""

from __future__ import annotations

import html
from typing import Any

import streamlit as st

from ..components.badges import source_chips_html, status_badge_html
from ..components.empty_states import render_awaiting_input_state, render_empty_section_notice
from ..components.hero import render_editorial_hero
from ..tokens import TOKEN_UNAVAILABLE_LABEL


def render_audit_screen(bundle: dict[str, Any]) -> None:
    """Render SCREEN 03: AUDIT TRAIL."""
    render_editorial_hero(
        eyebrow="03 / AUDIT TRAIL — EVIDENCE & MODEL INFERENCE",
        headline="EVERY DECISION.\nACCOUNTED FOR.",
        subtitle="Inspect recorded model calls, exact prompts and responses, rejected instructions, deterministic rejection reasons and validation evidence.",
        bundle=bundle,
    )

    if not bundle.get("loaded"):
        render_awaiting_input_state("03 / AUDIT TRAIL")
        return

    # 1. RECORDED MODEL CALLS LEDGER
    st.markdown(
        """
<div class="mm-section-header">
  <div>
    <div class="mm-overline">SECTION 01 // INFERENCE TELEMETRY</div>
    <h2 class="mm-section-title">RECORDED MODEL CALLS</h2>
  </div>
  <div class="mm-mono" style="color:var(--text-secondary);">
    EXPAND ANY CALL ROW TO INSPECT EXACT ORIGINAL PROMPT & RAW RESPONSE
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    model_calls = bundle.get("model_calls", [])
    if not model_calls:
        predicted_tags = bundle.get("predicted_model_areas", [])
        if predicted_tags:
            render_empty_section_notice(
                "MODEL CALL TRACE LOG",
                f"Engine recorded model tags {predicted_tags}, but no external trace.jsonl prompt/response log was attached to this snapshot.",
                status_key="needs_review",
            )
        else:
            render_empty_section_notice(
                "ZERO LLM CALLS TRIGGERED",
                "No fresh unseen messages required LLM extraction in this run; 100% of planning was resolved deterministically.",
                status_key="valid",
            )
    else:
        for call in model_calls:
            c_idx = call.get("index", 1)
            c_id = str(call.get("call_id") or f"CALL-{c_idx:03d}")
            tag = str(call.get("tag") or "reading").upper()
            model_id = str(call.get("model") or "UNSPECIFIED")
            provider = str(call.get("provider") or "UNSPECIFIED")
            in_tok = call.get("input_tokens")
            out_tok = call.get("output_tokens")
            dur_ms = call.get("duration_ms")
            msg_ids = call.get("message_ids") or []

            if in_tok is not None or out_tok is not None:
                tok_str = f"{in_tok if in_tok is not None else '—'} IN / {out_tok if out_tok is not None else '—'} OUT TOKENS"
            else:
                tok_str = TOKEN_UNAVAILABLE_LABEL

            dur_str = f"{dur_ms:,.0f} ms ({dur_ms / 1000.0:.2f}s)" if isinstance(dur_ms, (int, float)) else "DURATION UNAVAILABLE"

            st.markdown(
                f"""
<div style="background:var(--stage-dark);color:var(--text-dark-primary);padding:1.1rem 1.4rem;border:1px solid var(--border-dark-hairline);display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:1rem;">
  <div style="display:flex;align-items:center;gap:1rem;flex-wrap:wrap;">
    <span style="font-family:var(--font-mono);font-size:12px;font-weight:700;color:var(--accent);">{html.escape(c_id)} // {html.escape(tag)}</span>
    <span style="font-family:var(--font-mono);font-size:12.5px;font-weight:700;">MODEL: {html.escape(model_id)}</span>
    <span style="font-family:var(--font-mono);font-size:11px;color:var(--text-dark-secondary);">PROVIDER: {html.escape(provider)}</span>
  </div>
  <div style="display:flex;align-items:center;gap:1.25rem;flex-wrap:wrap;font-family:var(--font-mono);font-size:11.5px;">
    <span style="color:var(--accent);">{html.escape(tok_str)}</span>
    <span style="color:var(--text-dark-secondary);">{html.escape(dur_str)}</span>
  </div>
</div>
                """,
                unsafe_allow_html=True,
            )
            with st.expander(f"Inspect Original Prompt & Raw Response — {c_id} ({model_id})"):
                if msg_ids:
                    st.markdown(
                        f'<div style="margin-bottom:0.6rem;"><span class="mm-overline">TARGET MESSAGE IDS: </span>{source_chips_html(msg_ids)}</div>',
                        unsafe_allow_html=True,
                    )
                p_col, r_col = st.columns(2)
                with p_col:
                    st.markdown('<div class="mm-overline">EXACT ORIGINAL PROMPT</div>', unsafe_allow_html=True)
                    st.code(str(call.get("prompt") or "Prompt payload not persisted in trace."), language="text")
                with r_col:
                    st.markdown('<div class="mm-overline">EXACT RAW MODEL RESPONSE</div>', unsafe_allow_html=True)
                    st.code(str(call.get("response") or "Response payload not persisted in trace."), language="json")

    # 2. REJECTED & CONFLICTING INSTRUCTIONS
    st.markdown(
        """
<div class="mm-section-header" style="margin-top:2.5rem;">
  <div>
    <div class="mm-overline">SECTION 02 // CONFLICT RESOLUTION & AUTHORITY GUARDRAILS</div>
    <h2 class="mm-section-title">REJECTED & SUPERSEDED INSTRUCTIONS</h2>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    rejected = bundle.get("rejected_messages", [])
    messages_by_id = {str(m.get("id")): m for m in bundle.get("messages", [])}

    if not rejected:
        render_empty_section_notice(
            "REJECTED INSTRUCTIONS",
            "No conflicting, unauthorized, or superseded instructions recorded in this run.",
            status_key="valid",
        )
    else:
        for r in rejected:
            src_id = str(r.get("source") or "UNKNOWN")
            status_str = str(r.get("status") or "rejected").upper()
            reason_str = str(r.get("reason") or "No reason provided.")
            refs = r.get("references") or [src_id]
            target_scope = ".".join(
                str(x) for x in (r.get("area"), r.get("subject"), r.get("attribute")) if x
            )
            msg_obj = messages_by_id.get(src_id, {})
            raw_text = str(msg_obj.get("raw") or "Original message text unavailable.").strip()
            sender_info = f"{msg_obj.get('sender') or 'Unknown Sender'} ({str(msg_obj.get('role') or 'other').upper()})"
            date_info = str(msg_obj.get("date") or "Undated")

            border_color = (
                "var(--failed)"
                if status_str in {"REJECTED", "UNRESOLVED"}
                else "var(--warning)"
            )

            st.markdown(
                f"""
<div class="mm-rejection-card" style="border-left-color:{border_color};">
  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.75rem;border-bottom:1px solid var(--border-hairline);padding-bottom:0.65rem;">
    <div style="display:flex;align-items:center;gap:0.75rem;flex-wrap:wrap;">
      <span style="font-family:var(--font-display);font-size:20px;font-weight:800;letter-spacing:-0.02em;">
        {html.escape(status_str)} // MESSAGE {html.escape(src_id)}
      </span>
      <span class="mm-mono" style="color:var(--text-secondary);">
        {html.escape(sender_info)} · {html.escape(date_info)}
      </span>
    </div>
    <div>
      <span class="mm-overline">CONFLICT REFERENCES: </span>
      {source_chips_html(refs)}
    </div>
  </div>
  <div class="mm-rejection-grid">
    <div>
      <div class="mm-overline" style="margin-bottom:0.3rem;">INCOMING INSTRUCTION ({html.escape(target_scope.upper() if target_scope else "MESSAGE LEVEL")})</div>
      <div style="background:var(--surface-secondary);border:1px solid var(--border-hairline);padding:0.75rem 0.9rem;font-family:var(--font-mono);font-size:12px;line-height:1.5;white-space:pre-wrap;">{html.escape(raw_text)}</div>
    </div>
    <div>
      <div class="mm-overline" style="color:{border_color};margin-bottom:0.3rem;">ACTUAL REJECTION / RESOLUTION REASON</div>
      <div style="font-size:15px;line-height:1.55;color:var(--text-primary);font-weight:500;padding:0.4rem 0;">
        {html.escape(reason_str)}
      </div>
    </div>
  </div>
</div>
                """,
                unsafe_allow_html=True,
            )

    # 3. VALIDATION EVIDENCE LEDGER
    st.markdown(
        """
<div class="mm-section-header" style="margin-top:2.5rem;">
  <div>
    <div class="mm-overline">SECTION 03 // CONSTRAINT VERIFICATION</div>
    <h2 class="mm-section-title">VALIDATION EVIDENCE</h2>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    validations = bundle.get("validations", [])
    if not validations:
        render_empty_section_notice(
            "VALIDATION EVIDENCE",
            "No validation checks were recorded in the loaded output.",
            status_key="needs_review",
        )
    else:
        val_rows_html = ""
        for v in validations:
            chk_name = str(v.get("check") or "check")
            passed = bool(v.get("passed"))
            unresolved = bool(v.get("unresolved"))
            v_state = "valid" if passed else ("needs_review" if unresolved else "invalid")
            val_rows_html += (
                f"<tr>"
                f'<td class="mm-mono" style="font-weight:700;">{html.escape(chk_name)}</td>'
                f"<td>{status_badge_html(v_state)}</td>"
                f"<td>{html.escape(str(v.get('reason') or ''))}</td>"
                f"<td>{source_chips_html(v.get('evidence'))}</td>"
                f"</tr>"
            )
        st.markdown(
            f"""
<div style="background:var(--surface-primary);border:1px solid var(--border-hairline);overflow-x:auto;">
  <table class="mm-ledger-table">
    <thead>
      <tr>
        <th>CHECK IDENTIFIER</th>
        <th>RESULT</th>
        <th>VERIFICATION REASON</th>
        <th>SOURCE EVIDENCE</th>
      </tr>
    </thead>
    <tbody>
      {val_rows_html}
    </tbody>
  </table>
</div>
            """,
            unsafe_allow_html=True,
        )

    # 4. SOURCE MESSAGE PROVENANCE INDEX
    st.markdown(
        """
<div class="mm-section-header" style="margin-top:2.5rem;">
  <div>
    <div class="mm-overline">SECTION 04 // RAW MESSAGE CORPUS</div>
    <h2 class="mm-section-title">SOURCE-MESSAGE REFERENCES</h2>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    messages = bundle.get("messages", [])
    if messages:
        f_col1, f_col2 = st.columns([4, 8])
        with f_col1:
            status_filter = st.selectbox(
                "Filter Messages by Disposition",
                options=["ALL", "ACCEPTED", "MIXED", "REJECTED", "SUPERSEDED", "IRRELEVANT", "UNRESOLVED", "DUPLICATE"],
                index=0,
            )
        for m in messages:
            m_st = str(m.get("status") or "accepted").upper()
            if status_filter != "ALL" and m_st != status_filter:
                continue
            mid = str(m.get("id") or "")
            sender = str(m.get("sender") or "Unspecified Sender")
            role = str(m.get("role") or "other").upper()
            m_date = str(m.get("date") or "Undated")
            doms = ", ".join(str(d).upper() for d in (m.get("domains") or [])) or "NONE"
            with st.expander(f"{mid} · {sender} [{role}] · {m_date} · Status: {m_st} · Domains: {doms}"):
                st.markdown('<div class="mm-overline">RAW SOURCE MESSAGE</div>', unsafe_allow_html=True)
                st.code(str(m.get("raw") or "").strip(), language="text")
                st.markdown(
                    f'<div class="mm-overline" style="margin-top:0.5rem;">DISPOSITION EXPLANATION</div>'
                    f'<p style="font-size:14px;margin:0.25rem 0 0.65rem 0;">{html.escape(str(m.get("explanation") or ""))}</p>',
                    unsafe_allow_html=True,
                )
                facts = m.get("facts") or []
                if facts:
                    f_rows = ""
                    for f in facts:
                        f_rows += (
                            f"<tr>"
                            f'<td class="mm-mono">{html.escape(str(f.get("area") or ""))}</td>'
                            f'<td class="mm-mono">{html.escape(str(f.get("subject") or ""))}</td>'
                            f'<td class="mm-mono">{html.escape(str(f.get("attribute") or ""))}</td>'
                            f'<td class="mm-mono" style="font-weight:700;">{html.escape(str(f.get("value")))}</td>'
                            f'<td class="mm-mono">{html.escape(str(f.get("kind") or ""))}</td>'
                            f'<td>"{html.escape(str(f.get("evidence") or ""))}"</td>'
                            f"</tr>"
                        )
                    st.markdown(
                        f"""
<table class="mm-ledger-table">
  <thead>
    <tr><th>AREA</th><th>SUBJECT</th><th>ATTRIBUTE</th><th>VALUE</th><th>KIND</th><th>LITERAL SUBSTRING EVIDENCE</th></tr>
  </thead>
  <tbody>{f_rows}</tbody>
</table>
                        """,
                        unsafe_allow_html=True,
                    )
