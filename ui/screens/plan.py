"""SCREEN 02: THE PLAN — Five distinct domain instruments for accountable planning."""

from __future__ import annotations

import html
from typing import Any

import streamlit as st

from ..adapter import domain_validation_summary
from ..components.badges import fmt_amount, fmt_int, source_chips_html, status_badge_html
from ..components.empty_states import render_awaiting_input_state
from ..components.hero import render_editorial_hero


def _render_venue_instrument(bundle: dict[str, Any]) -> None:
    """01 / VENUE — Minimalist occupancy & facility verification instrument."""
    plan = bundle.get("plan", {})
    venue = plan.get("venue", {}) or {}
    att = plan.get("attendance", {}) or {}
    val = domain_validation_summary(bundle, "venue")

    v_name = str(venue.get("name") or "NO ELIGIBLE VENUE").upper()
    cap = venue.get("capacity")
    req = venue.get("required") if venue.get("required") is not None else att.get("occupancy")
    cost = venue.get("cost")
    facilities = [str(f).upper() for f in (venue.get("facilities") or [])]

    try:
        cap_num = float(cap) if cap is not None else 0.0
        req_num = float(req) if req is not None else 0.0
        occ_pct = min(100.0, round((req_num / cap_num) * 100.0, 1)) if cap_num > 0 else 0.0
        headroom = int(cap_num - req_num) if cap_num > 0 else 0
    except (ValueError, TypeError):
        occ_pct = 0.0
        headroom = 0

    bar_color = (
        "var(--verified)"
        if val["status"] == "valid"
        else ("var(--failed)" if val["status"] == "invalid" else "var(--warning)")
    )

    fac_chips = (
        "".join(
            f'<span class="mm-source-chip" style="background:var(--surface-primary);border-color:var(--text-primary);">✓ {html.escape(f)}</span>'
            for f in facilities
        )
        if facilities
        else '<span class="mm-overline">NO EXPLICIT FACILITIES REPORTED</span>'
    )

    alts = venue.get("alternatives") or []
    alt_rows = ""
    for alt in alts:
        alt_rows += (
            f"<tr>"
            f'<td style="font-weight:700;text-transform:uppercase;">{html.escape(str(alt.get("name") or ""))}</td>'
            f'<td>{html.escape(str(alt.get("reason") or ""))}</td>'
            f'<td>{source_chips_html(alt.get("sources"))}</td>'
            f"</tr>"
        )
    alt_table_html = (
        f"""
<div style="margin-top:1.35rem;">
  <div class="mm-overline" style="margin-bottom:0.45rem;">EVALUATED ALTERNATIVES & EXCLUSIONS</div>
  <table class="mm-ledger-table">
    <thead><tr><th>OPTION</th><th>DISPOSITION / EXCLUSION REASON</th><th>SOURCES</th></tr></thead>
    <tbody>{alt_rows}</tbody>
  </table>
</div>
        """
        if alt_rows
        else ""
    )

    st.markdown(
        f"""
<section class="mm-domain-section" aria-label="01 Venue Decision">
  <div class="mm-domain-layout">
    <div>
      <div class="mm-overline">DOMAIN INSTRUMENT // 01</div>
      <div class="mm-domain-index-big">01 / VENUE</div>
      <div style="margin:0.75rem 0;">{status_badge_html(val["status"])}</div>
      <div style="margin-top:1.1rem;">
        <div class="mm-overline">WHY THIS DECISION WAS MADE</div>
        <p style="font-size:14.5px;line-height:1.55;color:var(--text-primary);margin:0.35rem 0 0.9rem 0;">
          {html.escape(str(val["reason"]))}
        </p>
        <div class="mm-overline" style="margin-bottom:0.35rem;">SUPPORTING SOURCES</div>
        <div>{source_chips_html(venue.get("sources"))}</div>
      </div>
    </div>

    <div>
      <div style="display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:1rem;border-bottom:1px solid var(--border-hairline);padding-bottom:0.85rem;">
        <div>
          <div class="mm-overline">SELECTED VENUE</div>
          <div class="mm-decision-monument">{html.escape(v_name)}</div>
        </div>
        <div style="text-align:right;">
          <div class="mm-overline">COMMITTED RENTAL COST</div>
          <div style="font-family:var(--font-display);font-size:clamp(26px, 2.8vw, 38px);font-weight:800;font-variant-numeric:tabular-nums;">
            {html.escape(fmt_amount(cost))}
          </div>
        </div>
      </div>

      <!-- Occupancy Visualization Instrument -->
      <div style="background:var(--surface-secondary);border:1px solid var(--border-hairline);padding:1.25rem 1.4rem;margin-top:1.15rem;">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.5rem;">
          <span class="mm-overline">OCCUPANCY INSTRUMENT // SEATING UTILIZATION</span>
          <span class="mm-mono" style="font-weight:700;">
            {html.escape(fmt_int(req))} REQUIRED / {html.escape(fmt_int(cap))} CAPACITY ({occ_pct}%)
          </span>
        </div>
        <div class="mm-track-outer" style="height:20px;background:var(--surface-primary);">
          <div style="width:{occ_pct}%;background:{bar_color};height:100%;transition:width 180ms;"></div>
        </div>
        <div style="display:grid;grid-template-columns:repeat(4, 1fr);gap:0.75rem;margin-top:0.85rem;font-family:var(--font-mono);font-size:11.5px;">
          <div><span style="color:var(--text-secondary);">STUDENTS:</span> <strong>{html.escape(fmt_int(att.get("students")))}</strong></div>
          <div><span style="color:var(--text-secondary);">STAFF:</span> <strong>{html.escape(fmt_int(att.get("staff")))}</strong></div>
          <div><span style="color:var(--text-secondary);">TOTAL OCCUPANCY:</span> <strong>{html.escape(fmt_int(req))}</strong></div>
          <div><span style="color:var(--text-secondary);">SEAT BUFFER:</span> <strong>{headroom:+d} SEATS</strong></div>
        </div>
      </div>

      <div style="margin-top:1.1rem;">
        <div class="mm-overline" style="margin-bottom:0.4rem;">CONFIRMED VENUE FACILITIES</div>
        <div>{fac_chips}</div>
      </div>
      {alt_table_html}
    </div>
  </div>
</section>
        """,
        unsafe_allow_html=True,
    )


def _render_schedule_instrument(bundle: dict[str, Any]) -> None:
    """02 / SCHEDULE — Horizontal proportional gantt + vertical chronological time rail."""
    plan = bundle.get("plan", {})
    sched = plan.get("schedule", {}) or {}
    val = domain_validation_summary(bundle, "schedule")

    duration = sched.get("duration")
    start_clock = sched.get("start") or "00:00 (RELATIVE)"
    timeline = sched.get("timeline") or []
    total_dur = float(duration) if duration else sum(float(t.get("duration", 0)) for t in timeline) or 1.0

    palette_cycle = ["#151719", "#2D7452", "#676B69", "#9B680B", "#3B4248"]
    horiz_segments = ""
    rail_rows = ""

    for idx, block in enumerate(timeline):
        act_name = str(block.get("activity") or "Activity")
        b_dur = int(block.get("duration") or 0)
        s_min = int(block.get("start_min") or 0)
        e_min = int(block.get("end_min") or 0)
        s_lbl = str(block.get("start") or f"+{s_min}m")
        e_lbl = str(block.get("end") or f"+{e_min}m")
        w_pct = max(5.0, round((b_dur / total_dur) * 100.0, 1))

        is_judging = act_name.lower() == "judging"
        is_work = "work" in act_name.lower()
        seg_bg = "#151719" if is_judging else ("#ECEAE4" if is_work else palette_cycle[idx % len(palette_cycle)])
        seg_fg = "#C9E76B" if is_judging else ("#141414" if is_work else "#FFFFFF")
        tag_type = "EVALUATION WINDOW" if is_judging else ("CORE SPRINT" if is_work else "MANDATORY BREAK / SESSION")

        horiz_segments += (
            f'<div style="width:{w_pct}%;background:{seg_bg};color:{seg_fg};padding:0.45rem 0.55rem;'
            f'border-right:1px solid var(--border-hairline);overflow:hidden;white-space:nowrap;text-overflow:ellipsis;">'
            f'<div style="font-family:var(--font-mono);font-size:10px;font-weight:700;">{html.escape(act_name.upper())}</div>'
            f'<div style="font-family:var(--font-mono);font-size:9.5px;opacity:0.85;">{b_dur}m</div>'
            f"</div>"
        )

        marker_col = "var(--stage-dark)" if is_judging else ("var(--verified)" if not is_work else "var(--text-secondary)")
        rail_rows += (
            f'<div style="display:grid;grid-template-columns:130px 18px 1fr 110px;gap:0.9rem;align-items:center;'
            f'padding:0.75rem 0;border-bottom:1px solid var(--border-hairline);">'
            f'<div class="mm-mono" style="font-weight:700;color:var(--text-primary);">{html.escape(s_lbl)} → {html.escape(e_lbl)}</div>'
            f'<div style="width:10px;height:10px;background:{marker_col};border-radius:1px;"></div>'
            f'<div>'
            f'<div style="font-weight:700;font-size:15px;text-transform:uppercase;">{html.escape(act_name)}</div>'
            f'<div class="mm-overline" style="font-size:9.5px;">{tag_type} · MINUTE {s_min} TO {e_min}</div>'
            f"</div>"
            f'<div class="mm-mono" style="text-align:right;font-weight:700;">{b_dur} MIN</div>'
            f"</div>"
        )

    if not rail_rows:
        rail_rows = '<div style="padding:1rem 0;color:var(--text-secondary);">Timeline blocks could not be synthesized from current inputs.</div>'

    st.markdown(
        f"""
<section class="mm-domain-section" aria-label="02 Schedule Decision">
  <div class="mm-domain-layout">
    <div>
      <div class="mm-overline">DOMAIN INSTRUMENT // 02</div>
      <div class="mm-domain-index-big">02 / SCHEDULE</div>
      <div style="margin:0.75rem 0;">{status_badge_html(val["status"])}</div>
      <div style="margin-top:1.1rem;">
        <div class="mm-overline">WHY THIS DECISION WAS MADE</div>
        <p style="font-size:14.5px;line-height:1.55;color:var(--text-primary);margin:0.35rem 0 0.9rem 0;">
          {html.escape(str(val["reason"]))}
        </p>
        <div class="mm-overline" style="margin-bottom:0.35rem;">SUPPORTING SOURCES</div>
        <div>{source_chips_html(sched.get("sources"))}</div>
      </div>
    </div>

    <div>
      <div style="display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:1rem;border-bottom:1px solid var(--border-hairline);padding-bottom:0.85rem;">
        <div>
          <div class="mm-overline">TOTAL EVENT DURATION</div>
          <div class="mm-decision-monument">{html.escape(fmt_int(duration, " MINUTES"))}</div>
        </div>
        <div style="text-align:right;">
          <div class="mm-overline">ANCHOR START TIME</div>
          <div style="font-family:var(--font-display);font-size:clamp(26px, 2.8vw, 38px);font-weight:800;font-variant-numeric:tabular-nums;">
            {html.escape(str(start_clock))}
          </div>
        </div>
      </div>

      <!-- Proportional Sequence Strip -->
      <div style="margin-top:1.15rem;">
        <div class="mm-overline" style="margin-bottom:0.4rem;">PROPORTIONAL SEQUENCE RIBBON</div>
        <div style="display:flex;width:100%;border:1px solid var(--text-primary);overflow:hidden;">
          {horiz_segments}
        </div>
      </div>

      <!-- Chronological Vertical Time Rail -->
      <div style="margin-top:1.25rem;background:var(--surface-secondary);border:1px solid var(--border-hairline);padding:1rem 1.35rem;">
        <div class="mm-overline" style="margin-bottom:0.4rem;">CHRONOLOGICAL TIMELINE RAIL ({len(timeline)} CONTIGUOUS BLOCKS)</div>
        {rail_rows}
      </div>
    </div>
  </div>
</section>
        """,
        unsafe_allow_html=True,
    )


def _render_food_instrument(bundle: dict[str, Any]) -> None:
    """03 / FOOD — Meal coverage & unit/delivery cost equation instrument."""
    plan = bundle.get("plan", {})
    food = plan.get("food", {}) or {}
    att = plan.get("attendance", {}) or {}
    val = domain_validation_summary(bundle, "food")

    f_name = str(food.get("name") or "NO CATERING SELECTED").upper()
    qty = food.get("quantity")
    req = food.get("required") if food.get("required") is not None else att.get("meals")
    u_price = food.get("unit_price")
    delivery = food.get("delivery")
    total_cost = food.get("cost")

    try:
        qty_num = float(qty) if qty is not None else 0.0
        req_num = float(req) if req is not None else 0.0
        cov_pct = min(100.0, round((qty_num / max(1.0, req_num)) * 100.0, 1)) if req_num > 0 else 0.0
        surplus = int(qty_num - req_num)
    except (ValueError, TypeError):
        cov_pct = 0.0
        surplus = 0

    bar_color = "var(--verified)" if val["status"] == "valid" else "var(--failed)"

    alts = food.get("alternatives") or []
    alt_rows = ""
    for alt in alts:
        alt_rows += (
            f"<tr>"
            f'<td style="font-weight:700;text-transform:uppercase;">{html.escape(str(alt.get("name") or ""))}</td>'
            f'<td>{html.escape(str(alt.get("reason") or ""))}</td>'
            f'<td>{source_chips_html(alt.get("sources"))}</td>'
            f"</tr>"
        )
    alt_html = (
        f"""
<div style="margin-top:1.25rem;">
  <div class="mm-overline" style="margin-bottom:0.45rem;">ALTERNATIVE CATERING QUOTES & EXCLUSIONS</div>
  <table class="mm-ledger-table">
    <thead><tr><th>MENU / SUPPLIER</th><th>DISPOSITION</th><th>SOURCES</th></tr></thead>
    <tbody>{alt_rows}</tbody>
  </table>
</div>
        """
        if alt_rows
        else ""
    )

    st.markdown(
        f"""
<section class="mm-domain-section" aria-label="03 Food Decision">
  <div class="mm-domain-layout">
    <div>
      <div class="mm-overline">DOMAIN INSTRUMENT // 03</div>
      <div class="mm-domain-index-big">03 / FOOD</div>
      <div style="margin:0.75rem 0;">{status_badge_html(val["status"])}</div>
      <div style="margin-top:1.1rem;">
        <div class="mm-overline">WHY THIS DECISION WAS MADE</div>
        <p style="font-size:14.5px;line-height:1.55;color:var(--text-primary);margin:0.35rem 0 0.9rem 0;">
          {html.escape(str(val["reason"]))}
        </p>
        <div class="mm-overline" style="margin-bottom:0.35rem;">SUPPORTING SOURCES</div>
        <div>{source_chips_html(food.get("sources"))}</div>
      </div>
    </div>

    <div>
      <div style="display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:1rem;border-bottom:1px solid var(--border-hairline);padding-bottom:0.85rem;">
        <div>
          <div class="mm-overline">SELECTED MENU / CATERER</div>
          <div class="mm-decision-monument">{html.escape(f_name)}</div>
        </div>
        <div style="text-align:right;">
          <div class="mm-overline">TOTAL CATERING COMMITMENT</div>
          <div style="font-family:var(--font-display);font-size:clamp(26px, 2.8vw, 38px);font-weight:800;font-variant-numeric:tabular-nums;">
            {html.escape(fmt_amount(total_cost))}
          </div>
        </div>
      </div>

      <!-- Meal Coverage Instrument -->
      <div style="display:grid;grid-template-columns:7fr 5fr;gap:1.25rem;margin-top:1.15rem;">
        <div style="background:var(--surface-secondary);border:1px solid var(--border-hairline);padding:1.2rem 1.35rem;">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <span class="mm-overline">MEAL COVERAGE INSTRUMENT</span>
            <span class="mm-mono" style="font-weight:700;">{cov_pct}% COVERAGE ({surplus:+d} SURPLUS)</span>
          </div>
          <div class="mm-track-outer" style="height:18px;background:var(--surface-primary);">
            <div style="width:{cov_pct}%;background:{bar_color};height:100%;"></div>
          </div>
          <div style="display:flex;justify-content:space-between;font-family:var(--font-mono);font-size:12px;margin-top:0.55rem;">
            <span>REQUIRED MEALS: <strong>{html.escape(fmt_int(req))}</strong></span>
            <span>ORDERED QUANTITY: <strong>{html.escape(fmt_int(qty))}</strong></span>
          </div>
        </div>

        <div style="background:var(--stage-dark);color:var(--text-dark-primary);padding:1.2rem 1.35rem;display:flex;flex-direction:column;justify-content:space-between;">
          <div class="mm-overline" style="color:var(--accent);">AUDITED PRICING FORMULA</div>
          <div class="mm-mono" style="font-size:13px;line-height:1.65;margin-top:0.4rem;">
            <div>{html.escape(fmt_int(qty))} meals × {html.escape(fmt_amount(u_price))} unit</div>
            <div>+ {html.escape(fmt_amount(delivery))} delivery fee</div>
            <div style="border-top:1px solid var(--border-dark-hairline);margin-top:0.3rem;padding-top:0.3rem;color:var(--accent);font-weight:700;">
              = {html.escape(fmt_amount(total_cost))}
            </div>
          </div>
        </div>
      </div>
      {alt_html}
    </div>
  </div>
</section>
        """,
        unsafe_allow_html=True,
    )


def _render_judging_instrument(bundle: dict[str, Any]) -> None:
    """04 / JUDGING — Structured matrix visualization of judge assignments & capacity."""
    plan = bundle.get("plan", {})
    judg = plan.get("judging", {}) or {}
    val = domain_validation_summary(bundle, "judging")

    avail = judg.get("available")
    assigned = judg.get("assigned")
    teams = judg.get("teams")
    rate = judg.get("minutes_per_team")
    max_t = judg.get("max_teams")
    cost = judg.get("cost")
    assignments = judg.get("assignments") or []

    matrix_cards = ""
    for a in assignments:
        j_name = str(a.get("judge") or "Judge")
        j_teams = int(a.get("teams") or 0)
        s_min = int(a.get("start_min") or 0)
        e_min = int(a.get("end_min") or 0)
        cap_lim = int(max_t) if max_t else max(1, j_teams)
        util_pct = min(100, round((j_teams / max(1, cap_lim)) * 100))
        matrix_cards += (
            f'<div style="background:var(--surface-primary);border:1px solid var(--border-hairline);padding:1rem 1.15rem;">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;">'
            f'<span style="font-weight:800;font-size:14.5px;text-transform:uppercase;">{html.escape(j_name)}</span>'
            f'<span class="mm-mono" style="font-weight:700;color:var(--verified);">{j_teams} TEAMS</span>'
            f"</div>"
            f'<div class="mm-track-outer" style="height:10px;margin:0.55rem 0;">'
            f'<div style="width:{util_pct}%;background:var(--stage-dark);height:100%;"></div>'
            f"</div>"
            f'<div class="mm-mono" style="font-size:11px;color:var(--text-secondary);display:flex;justify-content:space-between;">'
            f"<span>WINDOW: +{s_min}m → +{e_min}m ({e_min - s_min}m)</span>"
            f"<span>LOAD: {j_teams}/{cap_lim} MAX</span>"
            f"</div>"
            f"</div>"
        )

    if not matrix_cards:
        matrix_cards = (
            '<div style="grid-column:1 / -1;padding:1rem;background:var(--surface-secondary);border:1px solid var(--border-hairline);">'
            "No judge-to-team assignments could be scheduled under current constraints."
            "</div>"
        )

    st.markdown(
        f"""
<section class="mm-domain-section" aria-label="04 Judging Decision">
  <div class="mm-domain-layout">
    <div>
      <div class="mm-overline">DOMAIN INSTRUMENT // 04</div>
      <div class="mm-domain-index-big">04 / JUDGING</div>
      <div style="margin:0.75rem 0;">{status_badge_html(val["status"])}</div>
      <div style="margin-top:1.1rem;">
        <div class="mm-overline">WHY THIS DECISION WAS MADE</div>
        <p style="font-size:14.5px;line-height:1.55;color:var(--text-primary);margin:0.35rem 0 0.9rem 0;">
          {html.escape(str(val["reason"]))}
        </p>
        <div class="mm-overline" style="margin-bottom:0.35rem;">SUPPORTING SOURCES</div>
        <div>{source_chips_html(judg.get("sources"))}</div>
      </div>
    </div>

    <div>
      <div style="display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:1rem;border-bottom:1px solid var(--border-hairline);padding-bottom:0.85rem;">
        <div>
          <div class="mm-overline">ASSIGNED EVALUATION ROSTER</div>
          <div class="mm-decision-monument">{html.escape(f"{fmt_int(assigned)} OF {fmt_int(avail)} JUDGES")}</div>
        </div>
        <div style="text-align:right;">
          <div class="mm-overline">HONORARIUM ALLOCATION</div>
          <div style="font-family:var(--font-display);font-size:clamp(26px, 2.8vw, 38px);font-weight:800;font-variant-numeric:tabular-nums;">
            {html.escape(fmt_amount(cost) if cost is not None else "PKR 0 / NONE")}
          </div>
        </div>
      </div>

      <div style="display:grid;grid-template-columns:repeat(3, 1fr);gap:0.85rem;margin:1.1rem 0;background:var(--surface-secondary);padding:0.95rem 1.2rem;border:1px solid var(--border-hairline);font-family:var(--font-mono);font-size:12px;">
        <div><span style="color:var(--text-secondary);">TOTAL TEAMS:</span> <strong>{html.escape(fmt_int(teams))}</strong></div>
        <div><span style="color:var(--text-secondary);">PACE:</span> <strong>{html.escape(fmt_int(rate, " MIN / TEAM"))}</strong></div>
        <div><span style="color:var(--text-secondary);">PER-JUDGE CAP:</span> <strong>{html.escape(fmt_int(max_t, " TEAMS") if max_t else "UNBOUNDED")}</strong></div>
      </div>

      <div class="mm-overline" style="margin-bottom:0.5rem;">JUDGE WORKLOAD & TIME-WINDOW MATRIX</div>
      <div style="display:grid;grid-template-columns:repeat(auto-fill, minmax(250px, 1fr));gap:0.85rem;">
        {matrix_cards}
      </div>
    </div>
  </div>
</section>
        """,
        unsafe_allow_html=True,
    )


def _render_budget_instrument(bundle: dict[str, Any]) -> None:
    """05 / BUDGET — Segmented allocation bar and double-rule financial ledger."""
    plan = bundle.get("plan", {})
    bud = plan.get("budget", {}) or {}
    val = domain_validation_summary(bundle, "budget")

    ceiling = bud.get("ceiling")
    total = bud.get("total")
    remaining = bud.get("remaining")
    lines = bud.get("lines") or []

    try:
        ceil_num = float(ceiling) if ceiling is not None else 0.0
        tot_num = float(total) if total is not None else 0.0
        rem_num = float(remaining) if remaining is not None else 0.0
    except (ValueError, TypeError):
        ceil_num, tot_num, rem_num = 0.0, 0.0, 0.0

    denom = max(ceil_num, tot_num, 1.0)
    seg_palette = ["#151719", "#2D7452", "#676B69", "#9B680B", "#4A525A"]
    seg_bars_html = ""
    ledger_rows_html = ""

    for idx, line in enumerate(lines):
        item_name = str(line.get("item") or "Expense").upper()
        c_val = line.get("cost")
        try:
            c_num = float(c_val)
        except (ValueError, TypeError):
            c_num = 0.0
        share_pct = round((c_num / denom) * 100.0, 1) if denom > 0 else 0.0
        col = seg_palette[idx % len(seg_palette)]
        srcs = line.get("sources") or ([line["source"]] if line.get("source") else [])

        if share_pct > 0:
            seg_bars_html += (
                f'<div title="{html.escape(item_name)}: {html.escape(fmt_amount(c_val))} ({share_pct}%)" '
                f'style="width:{max(2.0, share_pct)}%;background:{col};height:100%;border-right:1px solid #FFFFFF;"></div>'
            )

        ledger_rows_html += (
            f"<tr>"
            f'<td><span style="display:inline-block;width:10px;height:10px;background:{col};margin-right:8px;"></span>'
            f'<strong>{html.escape(item_name)}</strong></td>'
            f'<td class="mm-mono">{share_pct:.1f}%</td>'
            f'<td class="mm-mono" style="font-weight:700;">{html.escape(fmt_amount(c_val))}</td>'
            f"<td>{source_chips_html(srcs)}</td>"
            f"</tr>"
        )

    if rem_num > 0 and ceil_num > 0:
        rem_pct = round((rem_num / denom) * 100.0, 1)
        seg_bars_html += (
            f'<div title="UNALLOCATED HEADROOM: {html.escape(fmt_amount(remaining))}" '
            f'style="width:{max(2.0, rem_pct)}%;background:#C9E76B;height:100%;"></div>'
        )
    elif rem_num < 0:
        over_pct = min(35.0, round((abs(rem_num) / denom) * 100.0, 1))
        seg_bars_html += (
            f'<div title="CEILING OVERRUN: {html.escape(fmt_amount(abs(int(rem_num))))}" '
            f'style="width:{max(4.0, over_pct)}%;background:var(--failed);height:100%;"></div>'
        )

    rem_color = "var(--verified)" if rem_num >= 0 else "var(--failed)"

    st.markdown(
        f"""
<section class="mm-domain-section" aria-label="05 Budget Decision">
  <div class="mm-domain-layout">
    <div>
      <div class="mm-overline">DOMAIN INSTRUMENT // 05</div>
      <div class="mm-domain-index-big">05 / BUDGET</div>
      <div style="margin:0.75rem 0;">{status_badge_html(val["status"])}</div>
      <div style="margin-top:1.1rem;">
        <div class="mm-overline">WHY THIS DECISION WAS MADE</div>
        <p style="font-size:14.5px;line-height:1.55;color:var(--text-primary);margin:0.35rem 0 0.9rem 0;">
          {html.escape(str(val["reason"]))}
        </p>
        <div class="mm-overline" style="margin-bottom:0.35rem;">SUPPORTING SOURCES</div>
        <div>{source_chips_html(bud.get("sources"))}</div>
      </div>
    </div>

    <div>
      <div style="display:grid;grid-template-columns:repeat(3, 1fr);gap:1rem;border-bottom:1px solid var(--border-hairline);padding-bottom:0.95rem;">
        <div>
          <div class="mm-overline">COMMITTED TOTAL</div>
          <div class="mm-decision-monument" style="font-size:clamp(26px, 2.8vw, 42px);">{html.escape(fmt_amount(total))}</div>
        </div>
        <div>
          <div class="mm-overline">APPROVED CEILING</div>
          <div class="mm-decision-monument" style="font-size:clamp(26px, 2.8vw, 42px);color:var(--text-secondary);">{html.escape(fmt_amount(ceiling))}</div>
        </div>
        <div style="text-align:right;">
          <div class="mm-overline">REMAINING BALANCE</div>
          <div class="mm-decision-monument" style="font-size:clamp(26px, 2.8vw, 42px);color:{rem_color};">{html.escape(fmt_amount(remaining))}</div>
        </div>
      </div>

      <!-- Segmented Allocation Bar -->
      <div style="margin-top:1.15rem;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <span class="mm-overline">SEGMENTED ALLOCATION BAR (COMMITTED LINES VS. HEADROOM)</span>
          <span class="mm-mono" style="font-size:11px;">CURRENCY: PKR (RS)</span>
        </div>
        <div class="mm-track-outer" style="height:22px;border-color:var(--text-primary);">
          {seg_bars_html}
        </div>
      </div>

      <!-- Financial Ledger -->
      <div style="margin-top:1.25rem;">
        <div class="mm-overline" style="margin-bottom:0.45rem;">COMMITTED FINANCIAL LEDGER</div>
        <table class="mm-ledger-table">
          <thead>
            <tr>
              <th>COMMITTED LINE ITEM</th>
              <th>SHARE</th>
              <th>AMOUNT (PKR)</th>
              <th>PROVENANCE SOURCES</th>
            </tr>
          </thead>
          <tbody>
            {ledger_rows_html}
          </tbody>
        </table>
      </div>
    </div>
  </div>
</section>
        """,
        unsafe_allow_html=True,
    )


def render_plan_screen(bundle: dict[str, Any]) -> None:
    """Render SCREEN 02: THE PLAN."""
    render_editorial_hero(
        eyebrow="02 / THE PLAN — ACCOUNTABLE ARCHITECTURE",
        headline="FIVE DECISIONS.\nONE ACCOUNTABLE PLAN.",
        subtitle="Each domain is evaluated by a dedicated deterministic instrument backed by source message IDs and explicit constraint checks.",
        bundle=bundle,
    )

    if not bundle.get("loaded"):
        render_awaiting_input_state("02 / THE PLAN")
        return

    _render_venue_instrument(bundle)
    _render_schedule_instrument(bundle)
    _render_food_instrument(bundle)
    _render_judging_instrument(bundle)
    _render_budget_instrument(bundle)
