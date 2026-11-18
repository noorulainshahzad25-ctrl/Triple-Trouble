"""Translate the core engine result and publish a consistent filesystem snapshot."""

import json
import os
from pathlib import Path

from .tracing import token_text


def pretty(value):
    return json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)


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
