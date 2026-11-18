"""Public API: process a UTF-8 file, optionally passing the previous result's state."""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Callable

from .conflict_resolver import resolve
from .domain_model import triage
from .extractor import extract
from .ingest import segment
from .public_plan import public_result
from .planner import build
from .schemas import AREAS, SCHEMA_VERSION, check, key
from .updater import affected, append_messages
from .validator import validate


def process_input(
    input_path: Path, previous_state: dict | None, llm: Callable[[str, str], str]
) -> dict:
    if previous_state is not None and "state" in previous_state:
        previous_state = previous_state["state"]
    incoming = segment(Path(input_path))
    history, fresh = append_messages(previous_state, incoming)
    model_areas = ["reading"] if fresh else []
    if fresh:
        subjects = sorted(
            {
                (f["area"], f["subject"])
                for f in (previous_state or {}).get("facts", [])
                if f["subject"] != "event"
            }
        )
        extracted = extract(fresh, llm, subjects)
        for m in fresh:
            row = extracted[m["id"]]
            m.pop("error", None)
            m.pop("domain_hints", None)
            if "error" in row:
                m.update(
                    error=row["error"],
                    status="unresolved",
                    explanation=row["error"],
                    domain_hints=triage(m["raw"]),
                )
            else:
                m.update(
                    sender=m["sender"] or row["sender"],
                    date=m["date"] or row["date"],
                    facts=row["facts"],
                    role=row["role"],
                    note=row["note"],
                )
                m["constraints"] = [
                    f
                    for f in m["facts"]
                    if f["kind"] in {"rule", "requirement"} or f["condition"]
                ]
                m["domains"] = sorted({key(f["area"]) for f in m["facts"]})
    facts, rules, decisions = resolve(history)
    # Order instructions and genuine limits of supply have different consequences.
    # Compute demand independently of proposed order sizes before resolving them.
    if any(
        key(f["attribute"]) == "order_quantity" for m in history for f in m["facts"]
    ):
        baseline = build(
            [f for f in facts if f["attribute"] != "order_quantity"], rules, []
        )
        needed = baseline["attendance"]["meals"]
        sources = [f["source"] for f in facts if f["area"] in {"attendance", "judging"}]
        facts, rules, decisions = resolve(history, needed, sources)
    touched = affected(previous_state, facts, rules)
    checks = []
    if previous_state and not touched:
        plan = deepcopy(previous_state["plan"])
        checks = deepcopy(previous_state["planning_checks"])
    else:
        plan = build(facts, rules, checks)
    planning_checks = deepcopy(checks)
    if not history:
        checks.append(
            check("input.messages", False, "No messages in the pack.", unknown=True)
        )
    by_id = defaultdict(list)
    for d in decisions:
        by_id[d["source"]].append(d)
        if d["status"] == "unresolved":
            checks.append(
                check(
                    "source.conflict", False, d["reason"], d["references"], unknown=True
                )
            )
    for m in history:
        if m.get("error"):
            checks.append(
                check("extraction.complete", False, m["error"], [m["id"]], unknown=True)
            )
            continue
        if m.get("duplicate_of"):
            continue
        entries = by_id[m["id"]]
        statuses = {d["status"] for d in entries}
        m["status"] = (
            next(iter(statuses))
            if len(statuses) == 1
            else "mixed"
            if statuses
            else "irrelevant"
        )
        m["explanation"] = (
            " ".join(d["reason"] for d in entries)
            or m.get("note")
            or "No planning facts."
        )
    status = validate(plan, checks, rules)
    rejected = [
        d
        for d in decisions
        if d["status"] in {"rejected", "superseded", "irrelevant", "unresolved"}
    ]
    rejected.extend(
        {
            "source": m["id"],
            "status": m["status"],
            "reason": m["explanation"],
            "references": [m.get("duplicate_of", m["id"])],
        }
        for m in history
        if m.get("duplicate_of")
        or m.get("error")
        or not m["facts"]
        and m["status"] == "irrelevant"
    )
    changed = [
        a
        for a in AREAS
        if previous_state is None or plan[a] != previous_state["plan"][a]
    ]
    state = {
        "schema_version": SCHEMA_VERSION,
        "messages": history,
        "facts": facts,
        "rules": rules,
        "decisions": decisions,
        "plan": plan,
        "planning_checks": planning_checks,
        "affected_areas": touched,
    }
    raw = {
        "status": status,
        "plan": plan,
        "validations": checks,
        "rejected_messages": rejected,
        "changed_areas": changed,
        "predicted_model_areas": model_areas,
        "state": state,
    }
    return public_result(raw, previous_state)
