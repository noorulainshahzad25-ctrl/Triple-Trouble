"""Deterministic validation of comparisons and the constructed plan."""

from __future__ import annotations

import operator

from .schemas import AREAS, check, key, number

OPS = {
    "=": operator.eq,
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
}
ALIASES = {
    "cost": "cost",
    "ceiling": "ceiling",
    "meals": "quantity",
    "occupancy": "occupancy",
    "unit_price": "unit_price",
    "duration": "duration",
    "available": "available",
    "teams": "teams",
    "students": "students",
    "max_teams": "max_teams",
    "minutes_per_team": "minutes_per_team",
}


def compare(actual, op, expected):
    if actual is None or expected is None:
        return None
    if op == "contains":
        if isinstance(actual, list):
            return key(expected) in {key(v) for v in actual}
        return None
    if op not in OPS:
        return None
    try:
        return OPS[op](number(actual), number(expected))
    except ValueError:
        if op in {"=", "==", "!="} and type(actual) is type(expected):
            return OPS[op](key(actual), key(expected))
        return None


def lookup(ref, context):
    area = context.get(key(ref.get("area", "")))
    if not isinstance(area, dict):
        return None
    subject = key(ref.get("subject", "event"))
    if subject not in {"event", key(area.get("name", ""))}:
        return None
    attribute = key(ref.get("attribute", ""))
    return area.get(ALIASES.get(attribute, attribute))


def rule_result(rule, context):
    condition = rule.get("condition")
    if condition is not None:
        if not isinstance(condition, dict):
            return None
        applies = compare(
            lookup(condition, context),
            condition.get("operator", "="),
            condition.get("value"),
        )
        if applies is not True:
            return True if applies is False else None
    # An option-specific rule only applies when that option is in use.
    area = context.get(rule["area"], {})
    if area.get("name") and rule["subject"] not in {"event", key(area["name"])}:
        known = {key(v["name"]) for v in area.get("alternatives", [])}
        if rule["subject"] in known:
            return True
        return None
    attr = rule["attribute"]
    unit = key(rule.get("unit") or "")
    allowed_units = {
        "duration": {"min", "minute", "minutes"},
        "capacity": {"people", "seats", "persons"},
        "quantity": {"meals", "boxes", "people"},
        "cost": {"rs", "pkr", "rupees"},
        "total": {"rs", "pkr", "rupees"},
        "occupancy": {"people", "persons"},
    }
    if unit and unit not in allowed_units.get(attr, set()):
        return None
    return compare(lookup(rule, context), rule.get("operator") or "=", rule["value"])


def validate(plan, checks, rules):
    checks.append(
        check(
            "five_domains",
            all(a in plan for a in AREAS),
            "Five domain records required.",
        )
    )
    for rule in rules:
        outcome = rule_result(rule, plan)
        checks.append(
            check(
                "rule." + rule["attribute"],
                outcome is True,
                rule["evidence"]
                + (
                    " (could not evaluate)"
                    if outcome is None
                    else " (evaluated against selected plan)"
                ),
                [rule["source"]],
                unknown=outcome is None,
            )
        )
    timeline = plan["schedule"].get("timeline", [])
    if timeline:
        contiguous = timeline[0]["start_min"] == 0 and all(
            t["end_min"] - t["start_min"] == t["duration"] > 0
            and (i == 0 or t["start_min"] == timeline[i - 1]["end_min"])
            for i, t in enumerate(timeline)
        )
        checks.append(
            check(
                "schedule.coverage",
                contiguous and timeline[-1]["end_min"] == plan["schedule"]["duration"],
                "Activities must cover the event exactly, in order, without overlaps.",
                plan["schedule"]["sources"],
            )
        )
    venue, food, judging = plan["venue"], plan["food"], plan["judging"]
    if venue.get("name"):
        checks.append(
            check(
                "venue.capacity",
                number(venue["capacity"]) >= venue["required"],
                f"{venue['capacity']} seats for {venue['required']} people.",
                venue["sources"],
            )
        )
    if food.get("name"):
        checks.append(
            check(
                "food.quantity",
                food["quantity"] >= food["required"],
                f"{food['quantity']} meals for {food['required']} people.",
                food["sources"],
            )
        )
        food_total = number(food["unit_price"]) * food["quantity"] + number(
            food["delivery"]
        )
        checks.append(
            check(
                "food.price",
                number(food["cost"]) == food_total,
                "Quantity multiplied by the quote, plus the delivery fee.",
                food["sources"],
            )
        )
    assignments = judging.get("assignments", [])
    if assignments:
        block = next((t for t in timeline if t["activity"] == "judging"), {})
        enough = (
            len(assignments) == judging["assigned"] <= judging["available"]
            and sum(a["teams"] for a in assignments) == judging["teams"]
            and all(
                (judging["max_teams"] is None or a["teams"] <= judging["max_teams"])
                and block.get("start_min", float("inf"))
                <= a["start_min"]
                <= a["end_min"]
                <= block.get("end_min", -1)
                and a["end_min"] - a["start_min"]
                == a["teams"] * judging["minutes_per_team"]
                for a in assignments
            )
        )
        checks.append(
            check(
                "judging.assignments",
                enough,
                "Each team's evaluation fits an assigned judge's workload and scheduled block.",
                judging["sources"],
            )
        )
    budget = plan["budget"]
    if budget["total"] is not None:
        total = sum(number(v["cost"]) for v in budget["lines"])
        checks.append(
            check(
                "budget.sum",
                total == number(budget["total"]),
                "Sum of all committed line items.",
                budget["sources"],
            )
        )
    status = "valid"
    failed = [c for c in checks if not c["passed"]]
    if failed:
        status = (
            "invalid" if any(not c["unresolved"] for c in failed) else "needs_review"
        )
    return status
