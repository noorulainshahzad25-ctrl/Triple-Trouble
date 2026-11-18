"""Resolve propositions, keeping all decisions and their supporting sources."""

from __future__ import annotations

from datetime import datetime

from .schemas import EVENT, ITEM, clock, key, number

OWNER = {
    "attendance": "organizer",
    "venue": "venue",
    "food": "caterer",
    "judging": "judging",
    "budget": "finance",
    "schedule": "organizer",
}
TIME = {"available_from", "available_until", "earliest", "latest_end", "start"}
LABEL = {"required_facility", "required_menu", "required_venue", "facilities"}
MONEY = {"cost", "unit_price", "honorarium", "delivery", "ceiling"}
KINDS = {
    "quote",
    "fact",
    "requirement",
    "correction",
    "cancellation",
    "proposal",
    "tentative",
    "irrelevant",
    "rule",
}


def priority(f):
    role, area = f["role"], f["area"]
    if f["subject"] == "event" and f["attribute"] in {
        "meals",
        "occupancy",
        "required_menu",
        "required_venue",
        "required_facility",
    }:
        return 4 if role == "organizer" else 1
    if role == OWNER.get(area) or (
        role == "judge" and f["attribute"] in TIME and area == "judging"
    ):
        return 4
    return 3 if role == "organizer" else 1


def date_key(s):
    for fmt in ("%Y-%m-%d", "%d %b %Y", "%d %B %Y", "%d %b", "%d %B"):
        try:
            d = datetime.strptime(str(s).strip(), fmt)
            return ("%Y" in fmt, d.date())
        except ValueError:
            pass
    return None


def unsupported(f):
    if f["area"] not in EVENT:
        return True
    attrs = EVENT if f["subject"] == "event" else ITEM
    return f["attribute"] not in attrs[f["area"]] and (f["area"], f["attribute"]) != (
        "food",
        "delivery",
    )


def malformed(f):
    attr, val = f["attribute"], f["value"]
    if attr in TIME:
        clock(val)
    elif attr == "facilities":
        if not isinstance(val, list) or not all(isinstance(v, str) for v in val):
            raise ValueError("expected a list of facility names")
    elif attr in LABEL:
        if not isinstance(val, str) or not val.strip():
            raise ValueError("expected a name")
    else:
        n = number(val)
        if n < 0 or attr not in MONEY and n != int(n):
            raise ValueError("expected a nonnegative amount or whole count")


def resolve(messages, meal_requirement=None, meal_sources=()):
    winners, decisions, rules = {}, [], []
    disputes = {}
    for m in messages:
        if m.get("duplicate_of") or m.get("error"):
            continue
        for raw in m["facts"]:
            f = dict(
                raw,
                source=m["id"],
                role=m["role"],
                date=m.get("date"),
                sender=m.get("sender"),
            )
            for k in ("area", "subject", "attribute", "kind"):
                f[k] = key(f[k])
            a, s, k = f["area"], f["subject"], f["attribute"]
            d = {
                "source": m["id"],
                "area": a,
                "subject": s,
                "attribute": k,
                "status": "accepted",
                "reason": f["evidence"],
                "references": [m["id"]],
            }
            decisions.append(d)
            if (
                meal_requirement is not None
                and a == "food"
                and k == "order_quantity"
                and f["kind"] not in {"cancellation", "irrelevant"}
                and not f["condition"]
            ):
                try:
                    order = number(f["value"])
                except ValueError:
                    order = None
                if order is not None and order < meal_requirement:
                    d.update(
                        status="rejected",
                        reason=f"Order of {order} meals leaves {meal_requirement - order} of {meal_requirement} people unfed.",
                        references=sorted({m["id"], *meal_sources}),
                    )
                    continue
            if f["kind"] in {"proposal", "tentative", "irrelevant"}:
                d.update(
                    status="irrelevant" if f["kind"] == "irrelevant" else "rejected",
                    reason=f"{f['kind'].capitalize()} from {m.get('sender') or m['role']}, without a confirmed instruction: {f['evidence']}",
                )
                continue
            if (
                a == "attendance"
                and f["role"] in {"venue", "caterer", "judge", "participant"}
                and s == "event"
            ):
                d.update(
                    status="rejected",
                    reason=f"{m['role']} cannot revise the event attendance requirement: {f['evidence']}",
                )
                continue
            if a == "budget" and f["role"] in {
                "caterer",
                "venue",
                "judge",
                "participant",
            }:
                d.update(
                    status="rejected",
                    reason=f"The {f['role']} has no authority to approve {s}.{k}: {f['evidence']}",
                )
                continue
            if f["kind"] not in KINDS:
                d.update(status="unresolved", reason="Unknown claim type: " + f["kind"])
                continue
            if (
                f["condition"] is not None
                or f["kind"] == "rule"
                or unsupported(f)
                or f["operator"] not in (None, "=", "==")
            ):
                rules.append(f)
                continue
            if f["kind"] != "cancellation":
                try:
                    malformed(f)
                except (ValueError, TypeError) as exc:
                    d.update(
                        status="unresolved", reason=f"Cannot evaluate {s}.{k}: {exc}"
                    )
                    continue
            identity = (a, s, k, key(f["value"]) if k == "required_facility" else "")
            old = winners.get(identity)
            if old:
                prev, prior_d = old
                before, after = date_key(prev["date"]), date_key(f["date"])
                dated = before and after and before[0] == after[0]
                same_author = bool(
                    f["sender"] and key(f["sender"]) == key(prev["sender"])
                )
                delta = priority(f) - priority(prev)
                if delta < 0 or delta == 0 and dated and after < before:
                    d.update(
                        status="rejected",
                        references=[prev["source"], m["id"]],
                        reason=f"{s}.{k} remains {prev['value']} from {prev['source']}, which has higher authority or a later dated statement.",
                    )
                    continue
                agreement = (
                    f["value"] == prev["value"]
                    and f["kind"] != "cancellation"
                    and prev["kind"] != "cancellation"
                )
                if not (
                    delta > 0
                    or agreement
                    or dated
                    and after > before
                    or f["kind"] in {"correction", "cancellation"}
                    and (same_author or priority(f) >= 3)
                ):
                    d.update(
                        status="unresolved",
                        references=[prev["source"], m["id"]],
                        reason=f"Conflicting {s}.{k} values {prev['value']} and {f['value']} have no decisive revision or date.",
                    )
                    disputes.setdefault(identity, []).append((f, d))
                    continue
                if f["kind"] in {"correction", "cancellation"}:
                    for challenger, unresolved in disputes.get(identity, []):
                        if priority(f) >= priority(challenger):
                            unresolved.update(
                                status="superseded",
                                references=[challenger["source"], f["source"]],
                                reason=f"{f['source']} explicitly settles the disputed {s}.{k}.",
                            )
                prior_d.update(
                    status="corroborated" if agreement else "superseded",
                    references=[prev["source"], m["id"]],
                    reason=f"{m['id']} {'confirms' if agreement else 'revises'} {s}.{k} to {f['value']}.",
                )
            winners[identity] = (f, d)
    return (
        [f for f, d in winners.values() if f["kind"] != "cancellation"],
        rules,
        decisions,
    )
