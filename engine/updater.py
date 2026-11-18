"""Persistent message ledger and deterministic dependency tracking."""

from __future__ import annotations

import json
from copy import deepcopy

from .schemas import AREAS, DEPENDENCIES, SCHEMA_VERSION


def append_messages(previous, incoming):
    if previous is not None and previous.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported planning state schema version")
    history = deepcopy((previous or {}).get("messages", []))
    known = {m["fingerprint"]: m for m in history if not m.get("duplicate_of")}
    fresh = []
    for msg in incoming:
        prior = known.get(msg["fingerprint"])
        record = dict(
            msg,
            id=f"M{len(history) + 1:04d}",
            order=len(history) + 1,
            facts=[],
            constraints=[],
            domains=[],
            role="other",
        )
        history.append(record)
        if prior:
            record.update(
                duplicate_of=prior["id"],
                status="duplicate",
                explanation="Repeated content from " + prior["id"],
            )
            if prior.get("error") and prior not in fresh:
                fresh.append(prior)
        else:
            known[msg["fingerprint"]] = record
            fresh.append(record)
    return history, fresh


def affected(previous, facts, rules):
    def by_area(rows):
        groups = {}
        for f in rows:
            groups.setdefault(f["area"], set()).add(
                json.dumps(f, sort_keys=True, ensure_ascii=False)
            )
        return groups

    if previous is None:
        return list(AREAS)
    before = by_area(previous["facts"] + previous["rules"])
    after = by_area(facts + rules)
    domains = set()
    for a in before.keys() | after.keys():
        if before.get(a) != after.get(a):
            domains.update(DEPENDENCIES.get(a, AREAS))
    return [a for a in AREAS if a in domains]
