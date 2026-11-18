"""Read-only backend output adapter for MIND / MACHINE.

Reads persisted engine outputs, state snapshots, and model-call JSONL traces
without ever calling an LLM or mutating backend logic.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .tokens import DOMAINS, TOKEN_UNAVAILABLE_LABEL, status_meta

ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIRS = (
    ROOT_DIR / "outputs",
    ROOT_DIR / "runs",
    ROOT_DIR / "artifacts",
    ROOT_DIR,
)


def _safe_read_json(path: Path) -> dict[str, Any] | list[Any] | None:
    try:
        if not path.is_file():
            return None
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _safe_read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        if not path.is_file():
            return rows
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            item = json.loads(stripped)
            if isinstance(item, dict):
                rows.append(item)
    except Exception:
        pass
    return rows


def _is_engine_payload(data: Any) -> bool:
    if not isinstance(data, dict):
        return False
    if "event" in data and "validations" in data and isinstance(data.get("schedule"), list):
        return True
    if "mode" in data and isinstance(data.get("plan"), dict):
        return True
    if "plan" in data and "validations" in data and "status" in data:
        return True
    if "result" in data and isinstance(data["result"], dict):
        inner = data["result"]
        return _is_engine_payload(inner)
    if "schema_version" in data and "plan" in data and "messages" in data:
        return True
    if "run_id" in data and "actual_model_areas" in data and "run_usage" in data:
        return True
    return False


def discover_run_files(custom_dir: str | Path | None = None) -> list[Path]:
    """Return all valid engine output JSON files discovered on disk."""
    env_session = os.environ.get("PLANNER_SESSION_DIR")
    env_dir = os.environ.get("MIND_MACHINE_OUTPUT_DIR") or os.environ.get("MM_OUTPUT_DIR")
    session = Path(env_session or ROOT_DIR)
    search_dirs = [session / "output"]
    # Only follow published predecessors. A failed publication may leave a staged directory.
    current = session / "state/current/run_summary.json"
    published = set()
    while current.is_file() and current.resolve() not in published:
        current = current.resolve()
        published.add(current)
        search_dirs.append(current.parent)
        summary = _safe_read_json(current)
        prior = summary.get("previous_run_id") if isinstance(summary, dict) else None
        if not isinstance(prior, str) or not prior.isalnum():
            break
        current = session / "state/runs" / prior / "run_summary.json"
    if custom_dir or env_dir:
        search_dirs = [Path(custom_dir or env_dir)]
    elif session.resolve() == ROOT_DIR:
        search_dirs.extend(DEFAULT_OUTPUT_DIRS)

    seen: set[Path] = set()
    candidates: list[Path] = []
    excluded_names = {
        "domain_model.json",
        "domain_training.json",
        "domain_holdout.json",
        "mock_extractions.json",
        "package.json",
        "tsconfig.json",
        "rejections.json",
    }

    for folder in search_dirs:
        if not folder.exists() or not folder.is_dir():
            continue
        # If this folder is a main.py run directory containing run_summary.json, prefer run_summary.json
        summary_file = folder / "run_summary.json"
        if summary_file.is_file():
            resolved = summary_file.resolve()
            if resolved not in seen:
                seen.add(resolved)
                candidates.append(resolved)
            continue
        for p in sorted(folder.glob("*.json")):
            resolved = p.resolve()
            if resolved in seen or p.name in excluded_names:
                continue
            seen.add(resolved)
            payload = _safe_read_json(resolved)
            if _is_engine_payload(payload):
                candidates.append(resolved)

    candidates.sort(
        key=lambda p: (
            0 if p.name == "run_summary.json" else 1 if p.name == "latest.json" else 2,
            -p.stat().st_mtime,
            p.name,
        )
    )
    return candidates


def _display_plan(plan):
    event, budget = plan["event"], plan["budget"]
    return {
        "attendance": event,
        "venue": plan["venue"], "food": plan["food"], "judging": plan["judging"],
        "schedule": {"timeline": plan["schedule"], "start": event.get("start"),
                     "duration": event.get("duration_minutes")},
        "budget": {**budget, "ceiling": budget.get("limit"), "lines": [
            {"item": item["name"], "cost": item["cost"], "sources": item["source_ids"]}
            for item in budget["line_items"]
        ]},
    }


def _normalize_payload(
    raw: dict[str, Any], source_path: Path | None = None
) -> dict[str, Any]:
    """Normalize an engine output dict, main.py run_summary, or wrapper bundle into a canonical read-only bundle."""
    if "run_id" in raw and "actual_model_areas" in raw and source_path is not None:
        # Loaded a main.py run_summary.json artifact directory
        run_dir = source_path.resolve().parent
        eng_state = _safe_read_json(run_dir / "engine_state.json") or _safe_read_json(
            run_dir.parent / "state" / "engine_state.json"
        )
        pub_plan = _safe_read_json(run_dir / "plan.json") or {}
        rejs = _safe_read_json(run_dir / "rejections.json") or []
        state_dict = eng_state if isinstance(eng_state, dict) else {}
        internal_plan = state_dict.get("plan") if isinstance(state_dict.get("plan"), dict) else {}
        validations = (
            pub_plan.get("validations")
            if isinstance(pub_plan, dict) and "validations" in pub_plan
            else state_dict.get("planning_checks", [])
        )
        normalized_rejs = [
            {
                "source": r.get("message_id") or r.get("source"),
                "status": r.get("status"),
                "reason": r.get("reason"),
                "area": r.get("affected_area") or r.get("area"),
                "references": r.get("source_ids") or r.get("references", []),
            }
            for r in (rejs if isinstance(rejs, list) else [])
            if isinstance(r, dict)
        ]
        result = {
            "status": raw.get("status", pub_plan.get("status", "needs_review") if isinstance(pub_plan, dict) else "needs_review"),
            "plan": _display_plan(pub_plan) if pub_plan else internal_plan,
            "validations": validations,
            "rejected_messages": normalized_rejs,
            "changed_areas": raw.get("changed_areas", []),
            "predicted_model_areas": raw.get("predicted_model_areas", []),
            "state": state_dict,
        }
        meta = {
            "run_id": raw.get("run_id"),
            "duration_ms": round(float(raw["elapsed_seconds_before_publish"]) * 1000.0, 1)
            if raw.get("elapsed_seconds_before_publish") is not None
            else None,
        }
        trace = []
        prev = None
        if run_dir.parent.name == "runs":
            session = run_dir.parent.parent.parent
            trace = [row for row in _safe_read_jsonl(session / "output/trace.jsonl")
                     if row.get("run_id") == raw["run_id"]]
            previous_id = raw.get("previous_run_id")
            if isinstance(previous_id, str) and previous_id.isalnum():
                prior = _safe_read_json(run_dir.parent / previous_id / "plan.json")
                if isinstance(prior, dict):
                    prev = {"plan": _display_plan(prior)}
    elif "result" in raw and isinstance(raw["result"], dict):
        result = raw["result"]
        meta = raw.get("meta", {}) if isinstance(raw.get("meta"), dict) else {}
        trace = raw.get("model_calls") or raw.get("trace") or []
        prev = raw.get("previous_state") or raw.get("previous_result")
    elif "schema_version" in raw and "plan" in raw and "validations" not in raw:
        # Raw state object loaded directly
        result = {
            "status": raw.get("status", "needs_review"),
            "plan": raw.get("plan", {}),
            "validations": raw.get("planning_checks", []),
            "rejected_messages": [],
            "changed_areas": raw.get("affected_areas", []),
            "predicted_model_areas": [],
            "state": raw,
        }
        meta = raw.get("meta", {}) if isinstance(raw.get("meta"), dict) else {}
        trace = raw.get("model_calls") or raw.get("trace") or []
        prev = raw.get("previous_state")
    else:
        result = raw
        meta = raw.get("meta", {}) if isinstance(raw.get("meta"), dict) else {}
        trace = raw.get("model_calls") or raw.get("trace") or []
        prev = raw.get("previous_state") or raw.get("previous_result")

    if "event" in result and isinstance(result.get("schedule"), list):
        result = {"plan": result}
    public = result.get("plan", {})
    if "event" in public and isinstance(public.get("schedule"), list):
        result = {**result, "plan": _display_plan(public), "status": public["status"],
                  "validations": public["validations"], "rejected_messages": [
                      {"source": r["message_id"], "area": r["affected_area"],
                       "references": r["source_ids"], "reason": r["reason"], "status": r["status"]}
                      for r in result.get("rejections", [])
                  ]}

    state = result.get("state", {}) if isinstance(result.get("state"), dict) else {}

    # Check companion trace.jsonl if no embedded trace records
    if not trace and source_path is not None:
        run_id_hint = meta.get("run_id") or source_path.stem
        for trace_name in (f"{source_path.stem}.trace.jsonl", "trace.jsonl", "llm_trace.jsonl"):
            trace_file = source_path.parent / trace_name
            rows = _safe_read_jsonl(trace_file)
            if rows:
                matching = [
                    r for r in rows if not r.get("run_id") or r.get("run_id") == run_id_hint
                ]
                trace = matching
                break

    # Derive file metadata and freshness
    if source_path is not None and source_path.is_file():
        stat = source_path.stat()
        mtime_dt = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).astimezone()
        freshness_str = mtime_dt.strftime("%Y-%m-%d %H:%M:%S %Z")
        digest = hashlib.sha256(source_path.read_bytes()).hexdigest()[:12]
        run_id = meta.get("run_id") or f"RUN-{source_path.stem.upper()}-{digest[:6].upper()}"
        file_size = stat.st_size
    else:
        freshness_str = meta.get("timestamp") or "Uploaded in session"
        digest = hashlib.sha256(
            json.dumps(result, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()[:12]
        run_id = meta.get("run_id") or f"RUN-SESSION-{digest[:6].upper()}"
        file_size = len(json.dumps(result, default=str).encode("utf-8"))

    # Normalize model calls & token accounting
    normalized_calls: list[dict[str, Any]] = []
    counters = {"input_tokens": [], "output_tokens": [], "total_tokens": []}
    total_duration_ms = 0.0
    any_duration_reported = False
    models_seen: list[str] = []
    providers_seen: list[str] = []
    called_tags: list[str] = []

    for idx, call in enumerate(trace if isinstance(trace, list) else [], start=1):
        if not isinstance(call, dict):
            continue
        in_tok = call.get("input_tokens")
        out_tok = call.get("output_tokens")
        for name, values in counters.items():
            value = call.get(name)
            if type(value) is int and value >= 0:
                values.append(value)

        dur_ms = call.get("duration_ms")
        if dur_ms is None:
            dur_ms = call.get("latency_ms")
        if dur_ms is None and call.get("duration_s") is not None:
            try:
                dur_ms = float(call["duration_s"]) * 1000.0
            except (TypeError, ValueError):
                dur_ms = None
        if isinstance(dur_ms, (int, float)) and dur_ms >= 0:
            total_duration_ms += float(dur_ms)
            any_duration_reported = True
        else:
            dur_ms = None

        model_name = str(call.get("model") or meta.get("model") or "UNSPECIFIED")
        provider_name = str(
            call.get("provider")
            or call.get("model_source")
            or meta.get("provider")
            or "UNSPECIFIED"
        )
        tag = str(call.get("tag") or call.get("area") or "reading")
        if model_name not in models_seen and model_name != "UNSPECIFIED":
            models_seen.append(model_name)
        if provider_name not in providers_seen and provider_name != "UNSPECIFIED":
            providers_seen.append(provider_name)
        if tag not in called_tags:
            called_tags.append(tag)

        call_num = call.get("call_number") or idx
        normalized_calls.append(
            {
                "index": call_num,
                "call_id": call.get("id") or f"CALL-{int(call_num):03d}",
                "tag": tag,
                "model": model_name,
                "provider": provider_name,
                "input_tokens": in_tok,
                "output_tokens": out_tok,
                "total_tokens": call.get("total_tokens"),
                "usage_source": call.get("usage_source"),
                "error": call.get("error"),
                "duration_ms": dur_ms,
                "timestamp": call.get("timestamp"),
                "prompt": call.get("prompt") if call.get("prompt") is not None else call.get("input"),
                "response": call.get("response") if call.get("response") is not None else call.get("output"),
                "message_ids": call.get("message_ids", []),
                "status": "error" if call.get("error") else call.get("status", "completed"),
            }
        )

    predicted_model_areas = list(result.get("predicted_model_areas") or [])
    # Normalize previous state if available
    prev_state: dict[str, Any] | None = None
    if isinstance(prev, dict):
        if "state" in prev and isinstance(prev["state"], dict):
            prev_state = prev["state"]
        elif "plan" in prev:
            prev_state = prev

    return {
        "loaded": True,
        "run_id": run_id,
        "label": meta.get("label") or (source_path.name if source_path else run_id),
        "description": meta.get("description") or "",
        "source_path": str(source_path) if source_path else None,
        "file_size": file_size,
        "checksum": digest,
        "freshness": freshness_str,
        "status": result.get("status", "needs_review"),
        "status_meta": status_meta(result.get("status")),
        "plan": result.get("plan", {}),
        "validations": result.get("validations", []),
        "rejected_messages": result.get("rejected_messages", []),
        "changed_areas": result.get("changed_areas", []),
        "recomputed_areas": state.get("affected_areas", result.get("changed_areas", [])),
        "predicted_model_areas": predicted_model_areas,
        "called_model_tags": called_tags,
        "state": state,
        "messages": state.get("messages", []),
        "facts": state.get("facts", []),
        "rules": state.get("rules", []),
        "decisions": state.get("decisions", []),
        "previous_state": prev_state,
        "model_calls": normalized_calls,
        "telemetry": {
            "call_count": len(normalized_calls),
            "recorded_call_rows": len(normalized_calls),
            "tokens_available": any(counters.values()),
            **{name: sum(values) if values else None for name, values in counters.items()},
            "duration_ms": round(total_duration_ms, 1)
            if any_duration_reported
            else meta.get("duration_ms"),
            "models": models_seen or ([meta["model"]] if meta.get("model") else []),
            "providers": providers_seen
            or ([meta["provider"]] if meta.get("provider") else []),
        },
    }


def empty_bundle() -> dict[str, Any]:
    """Return an honest AWAITING INPUT bundle when no backend output is loaded."""
    return {
        "loaded": False,
        "run_id": "NONE",
        "label": "AWAITING INPUT",
        "description": "No backend run output loaded.",
        "source_path": None,
        "file_size": 0,
        "checksum": None,
        "freshness": "AWAITING INPUT",
        "status": "awaiting_input",
        "status_meta": status_meta(None),
        "plan": {},
        "validations": [],
        "rejected_messages": [],
        "changed_areas": [],
        "recomputed_areas": [],
        "predicted_model_areas": [],
        "called_model_tags": [],
        "state": {},
        "messages": [],
        "facts": [],
        "rules": [],
        "decisions": [],
        "previous_state": None,
        "model_calls": [],
        "telemetry": {
            "call_count": 0,
            "recorded_call_rows": 0,
            "tokens_available": False,
            "input_tokens": None,
            "output_tokens": None,
            "total_tokens": None,
            "duration_ms": None,
            "models": [],
            "providers": [],
        },
    }


def load_run_bundle(
    path: Path | str | None = None, uploaded_json: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Load a specific run bundle from disk or uploaded JSON dict."""
    if uploaded_json is not None and _is_engine_payload(uploaded_json):
        return _normalize_payload(uploaded_json, source_path=None)
    if path is None:
        return empty_bundle()
    target = Path(path).resolve()
    raw = _safe_read_json(target)
    if not isinstance(raw, dict) or not _is_engine_payload(raw):
        return empty_bundle()
    return _normalize_payload(raw, source_path=target)


def domain_validation_summary(bundle: dict[str, Any], domain_key: str) -> dict[str, Any]:
    """Compute truthful validation status and check list for a single planning domain."""
    if not bundle.get("loaded"):
        return {
            "status": "awaiting_input",
            "meta": status_meta(None),
            "checks": [],
            "reason": "No run has been loaded.",
        }

    checks = bundle.get("validations", [])
    rules = bundle.get("rules", [])
    rule_attrs_for_domain = {
        r.get("attribute") for r in rules if r.get("area") == domain_key
    }

    matched: list[dict[str, Any]] = []
    for c in checks:
        name = str(c.get("check", ""))
        if name.startswith(f"{domain_key}."):
            matched.append(c)
        elif domain_key == "venue" and name.startswith("attendance."):
            matched.append(c)
        elif name.startswith("rule.") and name.removeprefix("rule.") in rule_attrs_for_domain:
            matched.append(c)

    if not matched:
        return {
            "status": "needs_review",
            "meta": status_meta("needs_review"),
            "checks": [],
            "reason": "No domain-specific validation check recorded.",
        }

    failed = [c for c in matched if not c.get("passed")]
    if not failed:
        dom_status = "valid"
    elif any(not c.get("unresolved") for c in failed):
        dom_status = "invalid"
    else:
        dom_status = "needs_review"

    primary_reason = (
        failed[0].get("reason")
        if failed
        else matched[-1].get("reason", "All domain checks passed.")
    )
    return {
        "status": dom_status,
        "meta": status_meta(dom_status),
        "checks": matched,
        "reason": primary_reason,
    }


def compute_snapshot_diffs(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    """Compare previous_state.plan and current plan when both snapshots exist."""
    prev_state = bundle.get("previous_state")
    if not bundle.get("loaded") or not isinstance(prev_state, dict):
        return []
    prev_plan = prev_state.get("plan")
    curr_plan = bundle.get("plan")
    if not isinstance(prev_plan, dict) or not isinstance(curr_plan, dict):
        return []

    diffs: list[dict[str, Any]] = []
    all_areas = ("attendance", "venue", "schedule", "food", "judging", "budget")
    key_fields = {
        "attendance": ("students", "teams", "team_size", "staff", "occupancy", "meals"),
        "venue": ("name", "capacity", "required", "cost", "facilities"),
        "schedule": ("start", "duration", "timeline"),
        "food": ("name", "quantity", "required", "unit_price", "delivery", "cost"),
        "judging": ("available", "assigned", "teams", "minutes_per_team", "max_teams", "cost"),
        "budget": ("ceiling", "total", "remaining"),
    }

    for area in all_areas:
        before_obj = prev_plan.get(area, {}) or {}
        after_obj = curr_plan.get(area, {}) or {}
        for field in key_fields.get(area, ()):
            b_val = before_obj.get(field)
            a_val = after_obj.get(field)
            if field == "timeline":
                b_summary = [
                    f"{t.get('activity')} ({t.get('start', t.get('start_min'))}-{t.get('end', t.get('end_min'))})"
                    for t in (b_val or [])
                ]
                a_summary = [
                    f"{t.get('activity')} ({t.get('start', t.get('start_min'))}-{t.get('end', t.get('end_min'))})"
                    for t in (a_val or [])
                ]
                if b_summary != a_summary:
                    diffs.append(
                        {
                            "area": area,
                            "field": "timeline",
                            "previous": " → ".join(b_summary) if b_summary else "None",
                            "current": " → ".join(a_summary) if a_summary else "None",
                            "sources": after_obj.get("sources", []),
                        }
                    )
                continue
            if b_val != a_val:
                diffs.append(
                    {
                        "area": area,
                        "field": field,
                        "previous": b_val,
                        "current": a_val,
                        "sources": after_obj.get("sources", []),
                    }
                )
    return diffs


def inspect_workspace_files(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    """Return operational metadata for persisted output and classifier files."""
    files_to_check: list[tuple[str, Path]] = []
    if bundle.get("source_path"):
        src = Path(bundle["source_path"])
        files_to_check.append(("Active Run Output", src))
        if src.name == "run_summary.json" and src.parent.parent.name == "runs":
            files_to_check.append(("Session trace", src.parents[3] / "output/trace.jsonl"))
            for name in ("plan.json", "rejections.json", "engine_state.json", "final_submission.txt"):
                files_to_check.append(("Published snapshot", src.parent / name))
        for companion in ("trace.jsonl", f"{src.stem}.trace.jsonl", "latest.json"):
            cand = src.parent / companion
            if cand != src and cand.exists():
                files_to_check.append((f"Output Artifact ({companion})", cand))
    else:
        out_dir = ROOT_DIR / "outputs"
        for name in ("latest.json", "trace.jsonl"):
            files_to_check.append((f"Output Artifact ({name})", out_dir / name))

    files_to_check.extend(
        [
            ("Domain Classifier Model", ROOT_DIR / "engine" / "domain_model.json"),
            ("Classifier Training Set", ROOT_DIR / "engine" / "domain_training.json"),
            ("Classifier Holdout Set", ROOT_DIR / "engine" / "domain_holdout.json"),
        ]
    )

    records: list[dict[str, Any]] = []
    seen: set[Path] = set()
    for role, path in files_to_check:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.is_file():
            stat = resolved.stat()
            mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).astimezone()
            sha = hashlib.sha256(resolved.read_bytes()).hexdigest()[:12]
            records.append(
                {
                    "role": role,
                    "name": resolved.name,
                    "path": str(resolved.relative_to(ROOT_DIR))
                    if resolved.is_relative_to(ROOT_DIR)
                    else str(resolved),
                    "present": True,
                    "size_bytes": stat.st_size,
                    "modified": mtime.strftime("%Y-%m-%d %H:%M:%S"),
                    "sha256": sha,
                }
            )
        else:
            records.append(
                {
                    "role": role,
                    "name": path.name,
                    "path": str(path),
                    "present": False,
                    "size_bytes": None,
                    "modified": "MISSING",
                    "sha256": "—",
                }
            )
    return records


def format_audit_report(bundle: dict[str, Any]) -> str:
    """Format a complete, auditable Markdown/text decision receipt from real backend data."""
    if not bundle.get("loaded"):
        return "# MIND / MACHINE — AUDIT RECEIPT\n\nSTATUS: AWAITING INPUT (No run loaded)\n"

    plan = bundle.get("plan", {})
    status_info = bundle.get("status_meta", {})
    tel = bundle.get("telemetry", {})
    tok_text = (
        f"{tel.get('total_tokens')} ({tel.get('input_tokens')} IN / {tel.get('output_tokens')} OUT)"
        if tel.get("tokens_available")
        else TOKEN_UNAVAILABLE_LABEL
    )

    lines = [
        "# MIND / MACHINE — AUDITED DECISION REPORT",
        f"RUN ID:         {bundle.get('run_id')}",
        f"PLAN STATUS:    {status_info.get('label')} ({bundle.get('status')})",
        f"DATA FRESHNESS: {bundle.get('freshness')}",
        f"SOURCE FILE:    {bundle.get('source_path') or 'Session upload'}",
        f"MODEL CALLS:    {tel.get('call_count')}",
        f"TOKEN USAGE:    {tok_text}",
        "",
        "---",
        "## 01 / FIVE-DOMAIN ACCOUNTABLE PLAN",
    ]

    att = plan.get("attendance", {})
    lines.append(
        f"- ATTENDANCE: {att.get('occupancy')} total occupancy "
        f"({att.get('students')} students, {att.get('teams')} teams, {att.get('staff')} staff, {att.get('meals')} meals)"
    )

    venue = plan.get("venue", {})
    lines.append(
        f"- 01 / VENUE: {venue.get('name') or 'Unresolved'} | Capacity: {venue.get('capacity')} "
        f"(Required: {venue.get('required')}) | Cost: {venue.get('cost')} | Sources: {', '.join(venue.get('sources', []))}"
    )

    sched = plan.get("schedule", {})
    tl_str = ", ".join(
        f"{t.get('activity')} [{t.get('start', t.get('start_min'))}-{t.get('end', t.get('end_min'))}]"
        for t in sched.get("timeline", [])
    )
    lines.append(
        f"- 02 / SCHEDULE: Start {sched.get('start')} | Duration {sched.get('duration')} min | "
        f"Timeline: {tl_str or 'Unresolved'} | Sources: {', '.join(sched.get('sources', []))}"
    )

    food = plan.get("food", {})
    lines.append(
        f"- 03 / FOOD: {food.get('name') or 'Unresolved'} | Quantity: {food.get('quantity')} "
        f"(Required: {food.get('required')}) | Unit: {food.get('unit_price')} + Delivery: {food.get('delivery')} "
        f"= Total: {food.get('cost')} | Sources: {', '.join(food.get('sources', []))}"
    )

    judg = plan.get("judging", {})
    lines.append(
        f"- 04 / JUDGING: {judg.get('assigned')} assigned of {judg.get('available')} available | "
        f"Teams: {judg.get('teams')} ({judg.get('minutes_per_team')} min/team) | Cost: {judg.get('cost')} "
        f"| Sources: {', '.join(judg.get('sources', []))}"
    )

    bud = plan.get("budget", {})
    lines.append(
        f"- 05 / BUDGET: Total {bud.get('total')} / Ceiling {bud.get('ceiling')} "
        f"(Remaining: {bud.get('remaining')}) | Sources: {', '.join(bud.get('sources', []))}"
    )

    lines.extend(["", "---", "## 02 / DETERMINISTIC VALIDATION RECEIPTS"])
    for c in bundle.get("validations", []):
        mark = "PASS" if c.get("passed") else ("UNKNOWN" if c.get("unresolved") else "FAIL")
        ev = ", ".join(c.get("evidence", []))
        lines.append(f"- [{mark}] {c.get('check')}: {c.get('reason')} (Sources: {ev or '—'})")

    lines.extend(["", "---", "## 03 / REJECTED & CONFLICTING INSTRUCTIONS"])
    for r in bundle.get("rejected_messages", []):
        refs = ", ".join(r.get("references", []))
        lines.append(
            f"- [{str(r.get('status', '')).upper()}] Source {r.get('source')}: "
            f"{r.get('reason')} (Refs: {refs})"
        )

    lines.extend(["", "---", "## 04 / CHANGE INTELLIGENCE"])
    lines.append(f"- DOMAINS RECOMPUTED (SOLVER): {', '.join(bundle.get('recomputed_areas', [])) or 'None'}")
    lines.append(f"- DOMAINS WITH CHANGED OUTPUT: {', '.join(bundle.get('changed_areas', [])) or 'None'}")
    lines.append(f"- MODEL TAGS ACTUALLY CALLED:  {', '.join(bundle.get('called_model_tags', [])) or 'None'}")

    lines.extend(["", "---", "## 05 / RECORDED MODEL INFERENCE TRACE"])
    for call in bundle.get("model_calls", []):
        tok_pair = (
            f"{call.get('input_tokens')} IN / {call.get('output_tokens')} OUT"
            if call.get("input_tokens") is not None
            else TOKEN_UNAVAILABLE_LABEL
        )
        lines.append(
            f"- {call.get('call_id')} | Tag: {call.get('tag')} | Model: {call.get('model')} | "
            f"Tokens: {tok_pair} | Duration: {call.get('duration_ms')} ms"
        )

    return "\n".join(lines) + "\n"
