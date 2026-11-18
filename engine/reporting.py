"""Translate the core engine result and publish a consistent filesystem snapshot."""

import json
import os
import re
from pathlib import Path

from .schemas import number
from .tracing import token_text


def pretty(value):
    return json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)


def currency(facts):
    units = set()
    for fact in facts:
        if fact["attribute"] in {
            "cost",
            "ceiling",
            "honorarium",
            "unit_price",
            "delivery",
        }:
            for token in re.findall(
                r"(?i)\b(PKR|USD|EUR|GBP|INR|Rs)\b",
                f"{fact.get('unit') or ''} {fact['evidence']}",
            ):
                units.add(token.upper() if token.lower() != "rs" else "Rs")
    if len(units) == 1:
        return units.pop()
    if "Rs" in units and len(units) == 2 and units & {"PKR", "INR"}:
        return (units - {"Rs"}).pop()
    return None


def public_result(raw, previous):
    state, plan, checks = raw["state"], raw["plan"], list(raw["validations"])
    timeline = plan["schedule"]["timeline"]
    for fact in state["facts"]:
        if (
            fact["area"] == "schedule"
            and fact["attribute"] == "duration"
            and fact["subject"] != "event"
        ):
            ok = any(
                t["activity"] == fact["subject"]
                and t["duration"] == number(fact["value"])
                for t in timeline
            )
            checks.append(
                {
                    "check": "schedule.required_activity",
                    "passed": ok,
                    "unresolved": False,
                    "reason": f"Required {fact['subject']} for {fact['value']} minutes.",
                    "evidence": [fact["source"]],
                }
            )
    status = (
        "invalid"
        if any(not c["passed"] and not c["unresolved"] for c in checks)
        else raw["status"]
    )
    budget = plan["budget"]
    public = {
        "status": status,
        "event": {
            **plan["attendance"],
            "start": plan["schedule"]["start"],
            "duration_minutes": plan["schedule"]["duration"],
        },
        "venue": plan["venue"],
        "schedule": timeline,
        "food": plan["food"],
        "judging": plan["judging"],
        "budget": {
            "currency": currency(state["facts"]),
            "limit": budget["ceiling"],
            "line_items": [
                {
                    "name": r["item"],
                    "cost": r["cost"],
                    "source_ids": r.get("sources") or [r["source"]],
                }
                for r in budget["lines"]
            ],
            "total": budget["total"],
            "remaining": budget["remaining"],
        },
        "validations": checks,
        "unresolved": [c for c in checks if not c["passed"]],
        "source_ids": sorted({f["source"] for f in state["facts"] + state["rules"]}),
    }
    rejections = [
        {
            "message_id": r["source"],
            "status": r["status"],
            "reason": r["reason"],
            "affected_area": r.get("area", "reading"),
            "source_ids": r["references"],
        }
        for r in raw["rejected_messages"]
    ]
    old_count = len(previous["messages"]) if previous else 0
    fresh = [m for m in state["messages"][old_count:] if not m.get("duplicate_of")]
    return {
        "mode": "update" if previous else "full",
        "state": state,
        "plan": public,
        "rejections": rejections,
        "changed_areas": raw["changed_areas"],
        "predicted_model_areas": raw["predicted_model_areas"],
        "processed_messages": len(fresh),
    }


def plan_text(p):
    money, event = p["budget"], p["event"]
    lines = [
        f"HACKATHON PLAN  |  {p['status'].upper()}",
        f"{event['students']} students   {event['teams']} teams   {event['meals']} meals",
        (
            f"Venue   {p['venue'].get('name', 'Unresolved')}   "
            f"({p['venue'].get('capacity', '?')} seats)"
        ),
        f"Judging   {p['judging'].get('assigned')} assigned judges",
        f"Food    {p['food'].get('quantity', '?')} × {p['food'].get('name', 'unresolved')}",
        "",
        "Schedule (minutes from start)",
    ]
    lines += [
        f"  {s['start_min']:>4}–{s['end_min']:<4} {s['activity']}"
        for s in p["schedule"]
    ]
    lines += ["", f"Budget ({money['currency'] or 'currency unspecified'})"]
    lines += [f"  {r['name']:<22} {r['cost']}" for r in money["line_items"]]
    lines += [
        f"  Total {money['total']}   Limit {money['limit']}   Remaining {money['remaining']}"
    ]
    lines += ["", "Validation"]
    lines += [
        f"  {'PASS' if c['passed'] else 'CHECK'}  {c['check']} — {c['reason']}"
        for c in p["validations"]
    ]
    return "\n".join(lines)


def render(result, rows, summary):
    plan = result["plan"]
    decisions = ["Message decisions"] + [
        f"  {r['message_id']}  {r['status']}  [{r['affected_area']}]  {r['reason']}"
        for r in result["rejections"]
    ]
    if len(decisions) == 1:
        decisions.append("  None")
    display = plan_text(plan) + "\n\n" + "\n".join(decisions)
    submission = [
        display,
        "\nComplete plan and sources",
        pretty(plan),
        "\nSession model trace (one JSON record per call)",
    ]
    submission.extend(json.dumps(r, ensure_ascii=False) for r in rows)
    submission.append("Session total: " + token_text(summary["session_usage"]))
    return display, "\n".join(submission) + "\n"


def publish(root, run_id, result, summary, submission):
    state, out = root / "state", root / "output"
    directory = state / "runs" / run_id
    directory.mkdir(parents=True)
    artifacts = {
        "engine_state.json": pretty(result["state"]),
        "plan.json": pretty(result["plan"]),
        "rejections.json": pretty(result["rejections"]),
        "run_summary.json": pretty(summary),
        "final_submission.txt": submission,
    }
    for name, value in artifacts.items():
        (directory / name).write_text(
            value + ("" if value.endswith("\n") else "\n"), encoding="utf-8"
        )
        path = (state if name == "engine_state.json" else out) / name
        target = (
            Path("current") / name
            if name == "engine_state.json"
            else Path("../state/current") / name
        )
        if not path.is_symlink():
            path.symlink_to(target)
        elif path.readlink() != target:
            raise ValueError(f"Unexpected artifact symlink: {path}")
    # One atomic switch publishes state, plan, rejections and submission together.
    pointer = state / (".current-" + run_id)
    pointer.symlink_to(Path("runs") / run_id)
    os.replace(pointer, state / "current")
