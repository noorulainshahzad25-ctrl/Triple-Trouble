"""SCREEN 01: OVERVIEW — Editorial landing experience & 'THE PLAN, EXPLAINED.' dark showcase."""

from __future__ import annotations

import html
from typing import Any

import streamlit as st

from ..adapter import domain_validation_summary
from ..components.badges import fmt_amount, fmt_int, source_chips_html, status_badge_html
from ..components.empty_states import render_awaiting_input_state, render_empty_section_notice
from ..components.hero import render_editorial_hero
from ..components.metrics import render_metric_rail


def _render_dark_showcase(bundle: dict[str, Any]) -> None:
    """Render the dark showcase stage 'THE PLAN, EXPLAINED.' with 5 asymmetric domain cards."""
    plan = bundle.get("plan", {})
    currency = plan.get("budget", {}).get("currency") or ""
    att = plan.get("attendance", {})
    venue = plan.get("venue", {})
    sched = plan.get("schedule", {})
    food = plan.get("food", {})
    judg = plan.get("judging", {})
    bud = plan.get("budget", {})

    v_val = domain_validation_summary(bundle, "venue")
    s_val = domain_validation_summary(bundle, "schedule")
    f_val = domain_validation_summary(bundle, "food")
    j_val = domain_validation_summary(bundle, "judging")
    b_val = domain_validation_summary(bundle, "budget")

    # 01 / VENUE metrics
    v_name = str(venue.get("name") or "NO VENUE SELECTED").upper()
    v_cap = venue.get("capacity")
    v_req = venue.get("required") or att.get("occupancy")
    try:
        v_pct = min(100, round((float(v_req) / float(v_cap)) * 100)) if v_cap and v_req else 0
    except (ValueError, ZeroDivisionError):
        v_pct = 0
    v_bar_color = "#C9E76B" if v_val["status"] == "valid" else ("#EF6E6D" if v_val["status"] == "invalid" else "#EAB64D")
    v_facilities = ", ".join(str(x).upper() for x in (venue.get("facilities") or [])) or "STANDARD"

    # 05 / BUDGET metrics
    b_total = bud.get("total")
    b_ceil = bud.get("ceiling")
    b_rem = bud.get("remaining")
    try:
        b_pct = min(100, round((float(b_total) / float(b_ceil)) * 100)) if b_total is not None and b_ceil else 0
    except (ValueError, ZeroDivisionError):
        b_pct = 0
    b_bar_color = "#C9E76B" if b_val["status"] == "valid" else "#EF6E6D"

    # 02 / SCHEDULE mini timeline
    timeline = sched.get("timeline") or []
    total_dur = sched.get("duration") or sum(int(t.get("duration", 0)) for t in timeline) or 1
    seg_colors = ["#C9E76B", "#7FA792", "#D9D6CE", "#9BA7B6", "#EAB64D"]
    sched_bars_html = ""
    for i, item in enumerate(timeline):
        dur = max(1, int(item.get("duration", 1)))
        w_pct = max(6.0, round((dur / float(total_dur)) * 100, 1))
        col = "#C9E76B" if item.get("activity") == "judging" else seg_colors[i % len(seg_colors)]
        sched_bars_html += (
            f'<div title="{html.escape(str(item.get("activity")))}: {dur}m" '
            f'style="width:{w_pct}%;background:{col};height:100%;border-right:1px solid #151719;"></div>'
        )
    if not sched_bars_html:
        sched_bars_html = '<div style="width:100%;background:#2F3337;height:100%;"></div>'

    # 03 / FOOD metrics
    f_name = str(food.get("name") or "NO CATERING SELECTED").upper()
    f_qty = food.get("quantity")
    f_req = food.get("required") or att.get("meals")
    try:
        f_pct = min(100, round((float(f_qty) / max(1.0, float(f_req))) * 100)) if f_qty and f_req else 0
    except (ValueError, ZeroDivisionError):
        f_pct = 0
    f_bar_color = "#C9E76B" if f_val["status"] == "valid" else "#EF6E6D"

    # 04 / JUDGING metrics
    j_ass = judg.get("assigned")
    j_avail = judg.get("available")
    j_teams = judg.get("teams")
    j_rate = judg.get("minutes_per_team")
    try:
        j_pct = min(100, round((float(j_ass) / max(1.0, float(j_avail))) * 100)) if j_ass and j_avail else 0
    except (ValueError, ZeroDivisionError):
        j_pct = 0
    j_bar_color = "#C9E76B" if j_val["status"] == "valid" else "#EF6E6D"

    st.markdown(
        f"""
<section class="mm-dark-stage" aria-label="The Plan Explained Showcase">
  <div class="mm-dark-stage-header">
    <div>
      <div class="mm-dark-domain-num">DECISION STUDIO // FIVE-DOMAIN ARCHITECTURE</div>
      <h2 class="mm-dark-stage-title">THE PLAN, EXPLAINED.</h2>
    </div>
    <div style="max-width:44ch;font-size:14.5px;line-height:1.5;color:var(--text-dark-secondary);">
      Every domain selection below is synthesized from verified message propositions and checked against cross-domain constraints.
    </div>
  </div>

  <!-- Top Asymmetric Row: 7fr (01 Venue) / 5fr (05 Budget) -->
  <div class="mm-dark-grid-top">
    <div class="mm-dark-card">
      <div>
        <div style="display:flex;justify-content:space-between;align-items:center;gap:0.75rem;flex-wrap:wrap;">
          <span class="mm-dark-domain-num">01 / VENUE</span>
          {status_badge_html(v_val["status"], dark_stage=True)}
        </div>
        <div class="mm-dark-headline">{html.escape(v_name)}</div>
        <div style="font-size:13.5px;color:var(--text-dark-secondary);margin-top:0.25rem;">
          {html.escape(str(v_val["reason"]))}
        </div>
      </div>
      <div>
        <div style="display:flex;justify-content:space-between;font-family:var(--font-mono);font-size:11.5px;color:var(--text-dark-secondary);">
          <span>OCCUPANCY: {html.escape(fmt_int(v_req))} REQUIRED</span>
          <span>CAPACITY: {html.escape(fmt_int(v_cap))} SEATS ({v_pct}%)</span>
        </div>
        <div class="mm-track-outer-dark">
          <div style="width:{v_pct}%;background:{v_bar_color};height:100%;"></div>
        </div>
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.5rem;margin-top:0.65rem;">
          <span style="font-family:var(--font-mono);font-size:11px;color:var(--text-dark-secondary);">
            COST: <strong style="color:var(--text-dark-primary);">{html.escape(fmt_amount(venue.get("cost"), currency))}</strong> · FACILITIES: {html.escape(v_facilities)}
          </span>
          <div>{source_chips_html(venue.get("sources"), dark_stage=True)}</div>
        </div>
      </div>
    </div>

    <div class="mm-dark-card">
      <div>
        <div style="display:flex;justify-content:space-between;align-items:center;gap:0.75rem;flex-wrap:wrap;">
          <span class="mm-dark-domain-num">05 / BUDGET</span>
          {status_badge_html(b_val["status"], dark_stage=True)}
        </div>
        <div class="mm-dark-headline">{html.escape(fmt_amount(b_total, currency))}</div>
        <div style="font-size:13.5px;color:var(--text-dark-secondary);margin-top:0.25rem;">
          {html.escape(str(b_val["reason"]))}
        </div>
      </div>
      <div>
        <div style="display:flex;justify-content:space-between;font-family:var(--font-mono);font-size:11.5px;color:var(--text-dark-secondary);">
          <span>CEILING: {html.escape(fmt_amount(b_ceil, currency))}</span>
          <span>REMAINING: {html.escape(fmt_amount(b_rem, currency))}</span>
        </div>
        <div class="mm-track-outer-dark">
          <div style="width:{b_pct}%;background:{b_bar_color};height:100%;"></div>
        </div>
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.5rem;margin-top:0.65rem;">
          <span style="font-family:var(--font-mono);font-size:11px;color:var(--text-dark-secondary);">
            {len(bud.get("lines") or [])} COMMITTED LEDGER LINES
          </span>
          <div>{source_chips_html(bud.get("sources"), dark_stage=True)}</div>
        </div>
      </div>
    </div>
  </div>

  <!-- Bottom 3-Column Row: 02 Schedule / 03 Food / 04 Judging -->
  <div class="mm-dark-grid-bottom">
    <div class="mm-dark-card">
      <div>
        <div style="display:flex;justify-content:space-between;align-items:center;gap:0.5rem;flex-wrap:wrap;">
          <span class="mm-dark-domain-num">02 / SCHEDULE</span>
          {status_badge_html(s_val["status"], dark_stage=True)}
        </div>
        <div class="mm-dark-headline">{html.escape(fmt_int(sched.get("duration"), " MIN"))}</div>
        <div style="font-size:13px;color:var(--text-dark-secondary);margin-top:0.2rem;">
          START: {html.escape(str(sched.get("start") or "RELATIVE (+00:00)"))} · {len(timeline)} BLOCKS
        </div>
      </div>
      <div>
        <div class="mm-track-outer-dark">{sched_bars_html}</div>
        <div style="font-size:12.5px;color:var(--text-dark-secondary);margin:0.45rem 0;">
          {html.escape(str(s_val["reason"]))}
        </div>
        <div>{source_chips_html(sched.get("sources"), dark_stage=True)}</div>
      </div>
    </div>

    <div class="mm-dark-card">
      <div>
        <div style="display:flex;justify-content:space-between;align-items:center;gap:0.5rem;flex-wrap:wrap;">
          <span class="mm-dark-domain-num">03 / FOOD</span>
          {status_badge_html(f_val["status"], dark_stage=True)}
        </div>
        <div class="mm-dark-headline">{html.escape(f_name)}</div>
        <div style="font-size:13px;color:var(--text-dark-secondary);margin-top:0.2rem;">
          {html.escape(fmt_int(f_qty))} ORDERED / {html.escape(fmt_int(f_req))} REQUIRED MEALS
        </div>
      </div>
      <div>
        <div class="mm-track-outer-dark">
          <div style="width:{f_pct}%;background:{f_bar_color};height:100%;"></div>
        </div>
        <div style="font-family:var(--font-mono);font-size:11px;color:var(--text-dark-secondary);margin:0.45rem 0;">
          UNIT: {html.escape(fmt_amount(food.get("unit_price"), currency))} · TOTAL: {html.escape(fmt_amount(food.get("cost"), currency))}
        </div>
        <div>{source_chips_html(food.get("sources"), dark_stage=True)}</div>
      </div>
    </div>

    <div class="mm-dark-card">
      <div>
        <div style="display:flex;justify-content:space-between;align-items:center;gap:0.5rem;flex-wrap:wrap;">
          <span class="mm-dark-domain-num">04 / JUDGING</span>
          {status_badge_html(j_val["status"], dark_stage=True)}
        </div>
        <div class="mm-dark-headline">{html.escape(f"{fmt_int(j_ass)} / {fmt_int(j_avail)} JUDGES")}</div>
        <div style="font-size:13px;color:var(--text-dark-secondary);margin-top:0.2rem;">
          {html.escape(fmt_int(j_teams))} TEAMS · {html.escape(fmt_int(j_rate, " MIN/TEAM"))}
        </div>
      </div>
      <div>
        <div class="mm-track-outer-dark">
          <div style="width:{j_pct}%;background:{j_bar_color};height:100%;"></div>
        </div>
        <div style="font-size:12.5px;color:var(--text-dark-secondary);margin:0.45rem 0;">
          {html.escape(str(j_val["reason"]))}
        </div>
        <div>{source_chips_html(judg.get("sources"), dark_stage=True)}</div>
      </div>
    </div>
  </div>
</section>
        """,
        unsafe_allow_html=True,
    )


def render_overview_screen(bundle: dict[str, Any]) -> None:
    """Render SCREEN 01: OVERVIEW."""
    render_editorial_hero(
        eyebrow="01 / OVERVIEW — THE DECISION STUDIO",
        headline="MESSY INPUT.\nCLEAR DECISIONS.",
        subtitle="The plan isn't a guess. Every choice has a reason, a source and a validation result.",
        bundle=bundle,
        show_overview_actions=True,
    )

    st.markdown("<div style='height:0.75rem;'></div>", unsafe_allow_html=True)
    render_metric_rail(bundle)

    if not bundle.get("loaded"):
        render_awaiting_input_state("01 / OVERVIEW")
        return

    _render_dark_showcase(bundle)

    # Latest Conflicts & Source Evidence Ledger
    col_conflicts, col_sources = st.columns([5.5, 6.5], gap="large")

    with col_conflicts:
        st.markdown(
            """
<div class="mm-section-header">
  <div>
    <div class="mm-overline">DISPOSITION & GUARDRAILS</div>
    <h3 class="mm-section-title" style="font-size:clamp(26px, 2.6vw, 38px);">LATEST CONFLICTS</h3>
  </div>
</div>
            """,
            unsafe_allow_html=True,
        )
        rejected = bundle.get("rejected_messages", [])
        if not rejected:
            render_empty_section_notice(
                "CONFLICT DIGEST",
                "Zero rejected or conflicting instructions in the active run.",
                status_key="valid",
            )
        else:
            for item in rejected[:6]:
                src = str(item.get("source") or "UNKNOWN")
                st_raw = str(item.get("status") or "rejected").upper()
                area_attr = ".".join(
                    str(x)
                    for x in (item.get("area"), item.get("subject"), item.get("attribute"))
                    if x
                )
                reason = str(item.get("reason") or "Rejected by conflict resolver.")
                refs_html = source_chips_html(item.get("references"))
                border_col = (
                    "var(--failed)"
                    if st_raw in {"REJECTED", "UNRESOLVED"}
                    else "var(--warning)"
                )
                st.markdown(
                    f"""
<div class="mm-rejection-card" style="border-left-color:{border_col};">
  <div style="display:flex;justify-content:space-between;align-items:center;gap:0.5rem;flex-wrap:wrap;">
    <span class="mm-mono" style="font-weight:700;color:var(--text-primary);">
      SOURCE {html.escape(src)} {f"· {html.escape(area_attr.upper())}" if area_attr else ""}
    </span>
    <span class="mm-overline" style="color:{border_col};font-weight:700;">{html.escape(st_raw)}</span>
  </div>
  <div style="font-size:14.5px;line-height:1.5;color:var(--text-primary);margin:0.5rem 0;">
    {html.escape(reason)}
  </div>
  <div style="display:flex;align-items:center;gap:0.4rem;flex-wrap:wrap;">
    <span class="mm-overline" style="font-size:10px;">EVIDENCE REFS:</span>
    {refs_html}
  </div>
</div>
                    """,
                    unsafe_allow_html=True,
                )

    with col_sources:
        st.markdown(
            """
<div class="mm-section-header">
  <div>
    <div class="mm-overline">PROVENANCE LEDGER</div>
    <h3 class="mm-section-title" style="font-size:clamp(26px, 2.6vw, 38px);">SOURCE EVIDENCE</h3>
  </div>
</div>
            """,
            unsafe_allow_html=True,
        )
        messages = bundle.get("messages", [])
        if not messages:
            render_empty_section_notice(
                "SOURCE EVIDENCE",
                "No source messages recorded in state.",
                status_key="needs_review",
            )
        else:
            rows_html = ""
            for m in messages[:8]:
                mid = html.escape(str(m.get("id") or ""))
                sender = html.escape(str(m.get("sender") or m.get("role") or "Unknown"))
                role = html.escape(str(m.get("role") or "other").upper())
                m_status = str(m.get("status") or "accepted").lower()
                raw_excerpt = str(m.get("raw") or "").strip().replace("\n", " ")
                if len(raw_excerpt) > 135:
                    raw_excerpt = raw_excerpt[:132] + "..."
                doms = ", ".join(str(d).upper() for d in (m.get("domains") or [])) or "NONE"
                s_badge = status_badge_html(
                    "valid"
                    if m_status in {"accepted", "corroborated"}
                    else ("invalid" if m_status in {"rejected", "unresolved"} else "needs_review")
                )
                rows_html += (
                    f"<tr>"
                    f'<td class="mm-mono" style="font-weight:700;white-space:nowrap;">{mid}</td>'
                    f'<td><div style="font-weight:600;">{sender}</div>'
                    f'<div class="mm-overline" style="font-size:9.5px;">{role} · {html.escape(doms)}</div></td>'
                    f'<td style="font-size:13.5px;line-height:1.45;">{html.escape(raw_excerpt)}</td>'
                    f"<td style='white-space:nowrap;'>{s_badge}</td>"
                    f"</tr>"
                )
            st.markdown(
                f"""
<div style="background:var(--surface-primary);border:1px solid var(--border-hairline);overflow-x:auto;">
  <table class="mm-ledger-table">
    <thead>
      <tr>
        <th>ID</th>
        <th>SENDER / ROLE</th>
        <th>MESSAGE EVIDENCE</th>
        <th>STATE</th>
      </tr>
    </thead>
    <tbody>
      {rows_html}
    </tbody>
  </table>
</div>
                """,
                unsafe_allow_html=True,
            )
