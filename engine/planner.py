"""Construct a plan from accepted propositions. Times in solver space are event-relative."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from itertools import product
from math import ceil
from time import monotonic

from .schemas import check, clock, key, number, wire
from .validator import rule_result


class Facts:
    def __init__(self, rows):
        self.data = defaultdict(lambda: defaultdict(dict))
        for row in rows:
            obj = self.data[row["area"]][row["subject"]]
            attr = row["attribute"]
            if attr == "required_facility":
                obj.setdefault(attr, []).append(row)
            else:
                obj[attr] = row

    def get(self, a, k, subject="event", default=None):
        row = self.data[a][subject].get(k)
        return row["value"] if row else default

    def count(self, a, k, subject="event", default=None):
        v = self.get(a, k, subject)
        return int(number(v)) if v is not None else default

    def names(self, a):
        return sorted(s for s in self.data[a] if s != "event")

    def sources(self, *areas):
        return sorted(
            {
                row["source"]
                for a in areas
                for obj in self.data[a].values()
                for val in obj.values()
                for row in (val if isinstance(val, list) else [val])
            }
        )


def attendance(f, checks):
    def g(k):
        return f.count("attendance", k)

    students, teams, size = g("students"), g("teams"), g("team_size")
    if teams is None and students and size:
        teams = ceil(students / size)
    known = bool(teams and students)
    checks.append(
        check(
            "attendance.figures",
            known and (size is None or size > 0 and teams == ceil(students / size)),
            f"{students} students, {teams} teams, team size {size}.",
            f.sources("attendance"),
            unknown=not known,
        )
    )
    return {
        "students": students,
        "teams": teams,
        "team_size": size,
        "staff": g("staff") or 0,
    }


def place_jobs(jobs, length, judging_fits):
    """Enumerate earliest feasible starts in each activity order; bound ambiguous packs."""
    attempts = 0

    def visit(pending, now, timeline):
        nonlocal attempts
        if not pending:
            return timeline
        if sum(j[1] for j in pending) > length - now:
            return None
        for i, (name, dur, lo, hi) in enumerate(pending):
            start = max(now, lo)
            if name == "judging":
                while start + dur <= hi and not judging_fits(start, dur):
                    attempts += 1
                    if attempts > 40000:
                        raise ArithmeticError
                    start += 1
            if start + dur > hi:
                continue
            attempts += 1
            if attempts > 40000:
                raise ArithmeticError
            out = visit(
                pending[:i] + pending[i + 1 :],
                start + dur,
                timeline + [(name, start, start + dur)],
            )
            if out is not None:
                return out
        return None

    return visit(sorted(jobs, key=lambda j: (j[3], j[2], j[0])), 0, [])


def timing(f, people, checks):
    duration = f.count("schedule", "duration")
    start_text = f.get("schedule", "start")
    origin = clock(start_text) if start_text is not None else None
    available = f.count("judging", "available")
    rate = f.count("judging", "minutes_per_team")
    limit = f.count("judging", "max_teams")
    teams = people["teams"]
    award = f.get("judging", "honorarium")
    schedule = {
        "duration": duration,
        "start": start_text,
        "timeline": [],
        "sources": f.sources("schedule", "judging"),
    }
    judges = {
        "available": available,
        "minutes_per_team": rate,
        "max_teams": limit,
        "teams": teams,
        "assigned": None,
        "assignments": [],
        "cost": None,
        "sources": f.sources("judging", "attendance", "schedule"),
    }

    def test(name, ok, reason, unknown=False):
        checks.append(check(name, ok, reason, judges["sources"], unknown=unknown))

    if any(v is None for v in (teams, duration, available, rate)):
        test(
            "judging.inputs",
            False,
            "Need team count, event duration, judge availability and minutes per team.",
            True,
        )
        return schedule, judges
    limit = teams if limit is None else limit
    if min(teams, duration, available, rate, limit) <= 0:
        test(
            "judging.capacity",
            False,
            "A positive team load requires time and available judging capacity.",
        )
        return schedule, judges
    named = f.names("judging")
    activity_names = f.names("schedule")
    if len(named) > available:
        test(
            "judging.roster",
            False,
            "Individual availability records exceed the confirmed pool.",
        )
        return schedule, judges
    if duration > 10080 or available > 2000 or len(activity_names) > 20:
        test(
            "schedule.search",
            False,
            "Pack exceeds the bounded scheduling search.",
            True,
        )
        return schedule, judges

    def relative(area, k, name, default):
        val = f.get(area, k, name)
        if val is None:
            return default
        if origin is None:
            raise ValueError("Clock-time constraints need an event start time.")
        return clock(val) - origin

    try:
        slots = [
            (
                name,
                relative("judging", "available_from", name, 0),
                relative("judging", "available_until", name, duration),
            )
            for name in named
        ]
        slots += [
            (f"Pool judge {i + 1}", 0, duration) for i in range(available - len(named))
        ]
        jobs = []
        for name in activity_names:
            if name == "judging":
                continue
            dur = f.count("schedule", "duration", name)
            if dur is None or dur <= 0:
                raise ValueError(f"Need a positive duration for {name}.")
            fixed = relative("schedule", "start", name, None)
            lo = relative("schedule", "earliest", name, 0)
            hi = relative("schedule", "latest_end", name, duration)
            jobs.append(
                (
                    name,
                    dur,
                    max(lo, fixed if fixed is not None else 0),
                    min(hi, fixed + dur if fixed is not None else duration, duration),
                )
            )
        fixed = relative("judging", "start", "event", None)
        activity_start = relative("schedule", "start", "judging", None)
        lo = max(0, relative("schedule", "earliest", "judging", 0))
        end = min(duration, relative("schedule", "latest_end", "judging", duration))
        window = f.count("judging", "window", default=duration)
        if fixed is not None:
            lo = max(lo, fixed)
            end = min(end, fixed + window)
        target = f.count("schedule", "duration", "judging")
        if activity_start is not None:
            lo = max(lo, activity_start)
        low = max(
            1, f.count("judging", "required_judges", default=0), ceil(teams / limit)
        )
        high = min(available, max(teams, low))
        found = None
        attempts = 0
        deadline = monotonic() + 2
        for count in range(low, high + 1):
            # A partially available judge may need a longer block than full-round arithmetic.
            shortest = ceil(teams / count) * rate
            bound = min(window, end - lo, duration - sum(j[1] for j in jobs))
            durations = (
                [target]
                if target is not None
                else range(shortest, bound + 1)
                if named
                else [shortest]
            )
            for dur in durations:
                attempts += 1
                if attempts > 5000 or monotonic() > deadline:
                    raise ArithmeticError
                if dur < shortest or dur > bound:
                    continue

                def capacities(start, span, roster_size=count):
                    return sorted(
                        [
                            (
                                min(
                                    limit,
                                    max(0, min(start + span, b) - max(start, a))
                                    // rate,
                                ),
                                name,
                                max(start, a),
                            )
                            for name, a, b in slots
                        ],
                        key=lambda v: (-v[0], v[1]),
                    )[:roster_size]

                def fits(start, span):
                    if monotonic() > deadline:
                        raise ArithmeticError
                    cap = capacities(start, span)
                    return (
                        (fixed is None or start == fixed)
                        and (activity_start is None or start == activity_start)
                        and sum(c[0] for c in cap) >= teams
                        and all(c[0] > 0 for c in cap)
                    )

                found = place_jobs(jobs + [("judging", dur, lo, end)], duration, fits)
                if found is not None:
                    break
            if found is not None:
                break
        if found is None:
            test(
                "judging.schedule",
                False,
                "No placement satisfies activity bounds, judge availability and team workload.",
            )
            return schedule, judges
    except (ValueError, ArithmeticError) as exc:
        test(
            "schedule.inputs",
            False,
            str(exc) or "Scheduling search limit reached.",
            True,
        )
        return schedule, judges
    # For an unconstrained running order, reserve work time before judging and
    # spread required activities across that time. Fixed windows keep the solved order.
    if (
        not named
        and fixed is None
        and activity_start is None
        and lo == 0
        and end == duration
        and all(a == 0 and b == duration for _, _, a, b in jobs)
    ):
        slack = duration - sum(b - a for _, a, b in found)
        ordering = sorted(found, key=lambda entry: entry[0] == "judging")
        placed = []
        cursor = 0
        for idx, (name, a, b) in enumerate(ordering):
            cursor += slack // len(ordering) + (idx < slack % len(ordering))
            placed.append((name, cursor, cursor + b - a))
            cursor += b - a
        found = placed
    timeline = schedule["timeline"]

    def add(name, a, b):
        item = {"activity": name, "start_min": a, "end_min": b, "duration": b - a}
        if origin is not None:
            for k, v in (("start", a), ("end", b)):
                h, m = divmod(origin + v, 60)
                item[k] = f"{h:02d}:{m:02d}"
        timeline.append(item)

    cursor = 0
    for name, a, b in found:
        if a > cursor:
            add("Hackathon work", cursor, a)
        add(name, a, b)
        cursor = b
        if name == "judging":
            remaining = teams
            for cap, judge, t in capacities(a, b - a):
                load = min(cap, remaining)
                judges["assignments"].append(
                    {
                        "judge": judge,
                        "teams": load,
                        "start_min": t,
                        "end_min": t + load * rate,
                    }
                )
                remaining -= load
    if cursor < duration:
        add("Hackathon work", cursor, duration)
    judges.update(
        assigned=count, cost=wire(number(award) * count) if award is not None else None
    )
    test(
        "judging.coverage",
        sum(j["teams"] for j in judges["assignments"]) == teams,
        f"{count} assigned judges cover {teams} teams within confirmed availability.",
    )
    return schedule, judges


def options(f, area, quantity):
    cost_attr = "cost" if area == "venue" else "unit_price"
    required = f.get(area, "required_venue" if area == "venue" else "required_menu")
    facilities = [
        key(r["value"]) for r in f.data["venue"]["event"].get("required_facility", [])
    ]
    candidates, excluded = [], []
    for name in f.names(area):
        facts = f.data[area][name]
        item = {k: r["value"] for k, r in facts.items()}
        item.update(name=name, sources=sorted({r["source"] for r in facts.values()}))
        reason = None
        unknown = False
        if required and key(required) != name:
            reason = f"Selection must be {required}."
        elif quantity is None:
            reason, unknown = "Required headcount is unresolved.", True
        elif area == "venue" and f.count(area, "capacity", name, 0) < quantity:
            reason, unknown = (
                f"Capacity {item.get('capacity')} cannot establish seating for {quantity}.",
                "capacity" not in item,
            )
        elif area == "venue" and set(facilities) - {
            key(x) for x in item.get("facilities", [])
        }:
            reason = "Missing confirmation of mandatory facilities: " + ", ".join(
                facilities
            )
            unknown = "facilities" not in item
        elif (
            area == "food" and f.count(area, "max_quantity", name, quantity) < quantity
        ):
            reason = f"Supply cap falls below {quantity} meals."
        elif cost_attr not in item:
            reason, unknown = "Missing price quote.", True
        if reason:
            excluded.append(
                {
                    "name": name,
                    "reason": reason,
                    "unresolved": unknown,
                    "sources": item["sources"],
                }
            )
            continue
        if area == "food":
            qty = max(
                quantity,
                f.count(area, "min_quantity", name, 0),
                f.count(area, "order_quantity", name, 0),
                f.count(area, "order_quantity", default=0),
            )
            if f.count(area, "max_quantity", name, qty) < qty:
                excluded.append(
                    {
                        "name": name,
                        "reason": "Order exceeds the supplier's capacity.",
                        "unresolved": False,
                        "sources": item["sources"],
                    }
                )
                continue
            delivery = f.get(area, "delivery", name, f.get(area, "delivery", default=0))
            item.update(
                quantity=qty,
                delivery=delivery,
                cost=wire(number(item[cost_attr]) * qty + number(delivery)),
            )
        else:
            item["occupancy"] = quantity
        candidates.append(item)
    return sorted(candidates, key=lambda v: (number(v["cost"]), v["name"])), excluded


def build(facts, rules, checks):
    f = Facts(facts)
    people = attendance(f, checks)
    schedule, judges = timing(f, people, checks)
    selected = judges["assigned"]
    judges_in_room = f.count("attendance", "judges_attending", default=selected)
    if (
        selected is not None
        and judges_in_room is not None
        and judges_in_room < selected
    ):
        checks.append(
            check(
                "attendance.judges",
                False,
                "Assigned judges exceed the stated attending judge count.",
                f.sources("attendance", "judging"),
            )
        )
    counts = {
        "students": people["students"],
        "staff": people["staff"],
        "judges": judges_in_room,
        "additional_people": f.count("attendance", "additional_people", default=0),
    }
    for group in f.names("attendance"):
        stated = f.count("attendance", "people", group)
        if group in counts and stated is not None and counts[group] != stated:
            checks.append(
                check(
                    "attendance.group",
                    False,
                    f"Conflicting counts for {group}.",
                    f.sources("attendance"),
                )
            )
        counts[group] = stated if stated is not None else counts.get(group)
    group_meals = {
        group: f.count("attendance", "meal_people", group, n)
        for group, n in counts.items()
    }
    known_occupants = sum(n for n in counts.values() if n is not None)
    occupancy = f.count(
        "attendance",
        "occupancy",
        default=known_occupants if None not in counts.values() else None,
    )
    default_meals = None
    if None not in group_meals.values() and occupancy is not None:
        default_meals = sum(group_meals.values()) + max(0, occupancy - known_occupants)
    meals = f.count("attendance", "meals", default=default_meals)
    if occupancy is not None and occupancy < known_occupants:
        checks.append(
            check(
                "attendance.occupancy",
                False,
                "Explicit occupancy is below known attending groups.",
                f.sources("attendance", "judging"),
            )
        )
    people.update(occupancy=occupancy, meals=meals)
    venues, v_out = options(f, "venue", occupancy)
    food, h_out = options(f, "food", meals)
    costs = [
        {
            "item": s,
            "cost": wire(number(f.get("budget", "cost", s))),
            "source": f.data["budget"][s]["cost"]["source"],
        }
        for s in f.names("budget")
        if f.get("budget", "cost", s) is not None
    ]
    ceiling = f.get("budget", "ceiling")
    plan = {"attendance": people, "schedule": schedule, "judging": judges}

    def combination(v, h):
        lines = list(costs)
        for area, item in (("venue", v), ("food", h), ("judging", judges)):
            if item.get("cost") is not None:
                lines.append(
                    {"item": area, "cost": item["cost"], "sources": item["sources"]}
                )
        total = sum((number(row["cost"]) for row in lines), Decimal(0))
        complete = all(item.get("cost") is not None for item in (v, h, judges))
        budget = {
            "ceiling": ceiling,
            "lines": lines,
            "total": wire(total) if complete else None,
            "remaining": wire(number(ceiling) - total)
            if complete and ceiling is not None
            else None,
            "sources": f.sources("budget", "venue", "food", "judging", "attendance"),
        }
        return dict(plan, venue=v, food=h, budget=budget)

    best = None
    for idx, (v, h) in enumerate(product(venues or [{}], food or [{}])):
        if idx >= 10000:
            checks.append(
                check(
                    "options.search",
                    False,
                    "Too many option combinations for exhaustive evaluation.",
                    unknown=True,
                )
            )
            break
        trial = combination(v, h)
        context = dict(trial)
        for domain, items in (("venue", venues), ("food", food)):
            context[domain] = dict(trial[domain], alternatives=items)
        outcomes = [rule_result(rule, context) for rule in rules]
        over = (
            ceiling is not None
            and trial["budget"]["remaining"] is not None
            and number(trial["budget"]["remaining"]) < 0
        )
        rank = (
            int(over) + outcomes.count(False),
            outcomes.count(None),
            sum(number(i.get("cost", 0)) for i in (v, h)),
        )
        if best is None or rank < best[0]:
            best = (rank, trial)
    result = best[1]
    for area, needed, choices, reasons in (
        ("venue", occupancy, venues, v_out),
        ("food", meals, food, h_out),
    ):
        picked = result[area].copy()
        for item in choices:
            if item["name"] != picked.get("name"):
                reasons.append(
                    {
                        "name": item["name"],
                        "reason": f"Alternative quote {item['cost']}; selected combination ranks first on constraints and total cost.",
                        "sources": item["sources"],
                    }
                )
        picked.update(required=needed, alternatives=reasons)
        result[area] = picked
        checks.append(
            check(
                area + ".selection",
                bool(choices),
                f"{picked.get('name', 'No eligible option')} for {needed} people.",
                f.sources(area, "attendance", "judging"),
                unknown=not f.names(area)
                or needed is None
                or any(r.get("unresolved") for r in reasons),
            )
        )
    b = result["budget"]
    known = b["remaining"] is not None
    checks.append(
        check(
            "budget.ceiling",
            known and number(b["remaining"]) >= 0,
            f"Total {b['total']}, ceiling {ceiling}, remaining {b['remaining']}.",
            b["sources"],
            unknown=not known,
        )
    )
    return result
