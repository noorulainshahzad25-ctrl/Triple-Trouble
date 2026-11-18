"""Build the public planning result from resolved facts and validations."""

import re

from .schemas import number


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
