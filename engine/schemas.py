"""Versioned engine interchange format. The return value is JSON-compatible."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

AREAS = ("venue", "schedule", "food", "judging", "budget")
SCHEMA_VERSION = 1
# Attributes for event-level facts. Named subjects represent individual options,
# activities, expenses, attendance groups or judges.
EVENT = {
    "attendance": {
        "students",
        "team_size",
        "teams",
        "staff",
        "additional_people",
        "occupancy",
        "meals",
        "judges_attending",
    },
    "venue": {"required_facility", "required_venue"},
    "schedule": {"duration", "start"},
    "food": {"required_menu", "delivery", "order_quantity"},
    "judging": {
        "available",
        "minutes_per_team",
        "max_teams",
        "honorarium",
        "window",
        "start",
        "required_judges",
    },
    "budget": {"ceiling"},
}
ITEM = {
    "attendance": {"people", "meal_people"},
    "venue": {"capacity", "cost", "facilities"},
    "schedule": {"duration", "start", "earliest", "latest_end"},
    "food": {
        "unit_price",
        "delivery",
        "max_quantity",
        "min_quantity",
        "order_quantity",
    },
    "judging": {"available_from", "available_until"},
    "budget": {"cost"},
}
DEPENDENCIES = {
    "attendance": set(AREAS),
    "venue": {"venue", "budget"},
    "food": {"food", "budget"},
    "judging": set(AREAS),
    "schedule": {"schedule", "judging", "venue", "food", "budget"},
    "budget": {"budget"},
}


def key(value):
    return " ".join(str(value).strip().casefold().split())


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float, str, Decimal)):
        raise ValueError("expected a finite number")
    try:
        result = Decimal(str(value).strip())
    except InvalidOperation as exc:
        raise ValueError("expected a finite number") from exc
    if (
        not result.is_finite()
        or abs(result) > 10**15
        or result.as_tuple().exponent < -9
    ):
        raise ValueError("unsupported numeric range or precision")
    return result


def wire(value):
    if value == value.to_integral_value():
        return int(value)
    return format(value.normalize(), "f")


def clock(value):
    if isinstance(value, str) and re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", value):
        h, m = value.split(":")
        return int(h) * 60 + int(m)
    raise ValueError("expected a 24-hour HH:MM time")


def check(name, ok, reason, sources=(), *, unknown=False):
    return {
        "check": name,
        "passed": bool(ok),
        "reason": reason,
        "evidence": sorted(set(sources)),
        "unresolved": bool(unknown and not ok),
    }
