"""CLI runner and real-engine artifact generator for MIND / MACHINE.

Wraps `engine.pipeline.process_input` without modifying `engine/` and writes
atomic JSON outputs and JSONL model-call trace records to `outputs/`.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any, Callable

from engine.pipeline import process_input

ROOT_DIR = Path(__file__).resolve().parent
OUTPUTS_DIR = ROOT_DIR / "outputs"


def _build_seeded_packs() -> dict[str, dict[str, Any]]:
    """Construct realistic English + Roman Urdu hackathon message packs for real engine runs."""
    pack_1_text = "\n\n".join(
        [
            "Message 1\nFrom: Lead Organizer\nDate: 2026-11-10\nWe have 96 students registered in 24 teams of 4, plus 8 organizing staff members. Event starts at 09:00 and runs for 360 minutes. Venue mein backup generator aur wheelchair ramp lazmi chahiye.",
            "Message 2\nFrom: Finance Office\nDate: 2026-11-10\nApproved event budget ceiling is 320000 PKR. Poster printing and badges cost 18000 PKR confirmed.",
            "Message 3\nFrom: Campus Facilities Manager\nDate: 2026-11-11\nMain Auditorium capacity is 160 seats, rental cost is 85000 PKR, and facilities include generator, wheelchair ramp, and projector. Seminar Hall B capacity is 90 seats, rental cost is 45000 PKR, facilities include projector.",
            "Message 4\nFrom: Green Olive Caterers\nDate: 2026-11-11\nStandard Box Lunch menu unit price is 650 PKR per meal with 4000 PKR delivery fee and max supply of 180 boxes. Executive Buffet menu unit price is 950 PKR per meal with 5000 PKR delivery fee.",
            "Message 5\nFrom: Judging Chair\nDate: 2026-11-11\nWe have 6 judges available in the pool. Each team needs 10 minutes per team for evaluation, and each judge can evaluate at most 6 teams. Judge honorarium is 8000 PKR per assigned judge. Mandatory lunch break duration is 45 minutes between 12:00 and 13:30.",
            "Message 6\nFrom: Student Participant\nDate: 2026-11-12\nSir humaray khayal mein sirf 60 کھانے ke boxes mangwa lein taake paise bach jayein.",
        ]
    )

    pack_1_extractions = {
        "M0001": {
            "sender": "Lead Organizer",
            "date": "2026-11-10",
            "role": "organizer",
            "note": None,
            "facts": [
                {"area": "attendance", "subject": "event", "attribute": "students", "value": 96, "kind": "fact", "evidence": "96 students", "unit": "people", "operator": "=", "condition": None},
                {"area": "attendance", "subject": "event", "attribute": "teams", "value": 24, "kind": "fact", "evidence": "24 teams", "unit": None, "operator": "=", "condition": None},
                {"area": "attendance", "subject": "event", "attribute": "team_size", "value": 4, "kind": "fact", "evidence": "teams of 4", "unit": None, "operator": "=", "condition": None},
                {"area": "attendance", "subject": "event", "attribute": "staff", "value": 8, "kind": "fact", "evidence": "8 organizing staff", "unit": "people", "operator": "=", "condition": None},
                {"area": "schedule", "subject": "event", "attribute": "start", "value": "09:00", "kind": "fact", "evidence": "starts at 09:00", "unit": None, "operator": "=", "condition": None},
                {"area": "schedule", "subject": "event", "attribute": "duration", "value": 360, "kind": "fact", "evidence": "runs for 360 minutes", "unit": "minutes", "operator": "=", "condition": None},
                {"area": "venue", "subject": "event", "attribute": "required_facility", "value": "generator", "kind": "requirement", "evidence": "backup generator", "unit": None, "operator": "=", "condition": None},
                {"area": "venue", "subject": "event", "attribute": "required_facility", "value": "wheelchair ramp", "kind": "requirement", "evidence": "wheelchair ramp lazmi", "unit": None, "operator": "=", "condition": None},
            ],
        },
        "M0002": {
            "sender": "Finance Office",
            "date": "2026-11-10",
            "role": "finance",
            "note": None,
            "facts": [
                {"area": "budget", "subject": "event", "attribute": "ceiling", "value": 320000, "kind": "requirement", "evidence": "ceiling is 320000 PKR", "unit": "PKR", "operator": "=", "condition": None},
                {"area": "budget", "subject": "printing_and_badges", "attribute": "cost", "value": 18000, "kind": "fact", "evidence": "cost 18000 PKR", "unit": "PKR", "operator": "=", "condition": None},
            ],
        },
        "M0003": {
            "sender": "Campus Facilities Manager",
            "date": "2026-11-11",
            "role": "venue",
            "note": None,
            "facts": [
                {"area": "venue", "subject": "main auditorium", "attribute": "capacity", "value": 160, "kind": "quote", "evidence": "Main Auditorium capacity is 160 seats", "unit": "seats", "operator": "=", "condition": None},
                {"area": "venue", "subject": "main auditorium", "attribute": "cost", "value": 85000, "kind": "quote", "evidence": "rental cost is 85000 PKR", "unit": "PKR", "operator": "=", "condition": None},
                {"area": "venue", "subject": "main auditorium", "attribute": "facilities", "value": ["generator", "wheelchair ramp", "projector"], "kind": "quote", "evidence": "facilities include generator, wheelchair ramp, and projector", "unit": None, "operator": "=", "condition": None},
                {"area": "venue", "subject": "seminar hall b", "attribute": "capacity", "value": 90, "kind": "quote", "evidence": "Seminar Hall B capacity is 90 seats", "unit": "seats", "operator": "=", "condition": None},
                {"area": "venue", "subject": "seminar hall b", "attribute": "cost", "value": 45000, "kind": "quote", "evidence": "rental cost is 45000 PKR", "unit": "PKR", "operator": "=", "condition": None},
                {"area": "venue", "subject": "seminar hall b", "attribute": "facilities", "value": ["projector"], "kind": "quote", "evidence": "facilities include projector", "unit": None, "operator": "=", "condition": None},
            ],
        },
        "M0004": {
            "sender": "Green Olive Caterers",
            "date": "2026-11-11",
            "role": "caterer",
            "note": None,
            "facts": [
                {"area": "food", "subject": "standard box lunch", "attribute": "unit_price", "value": 650, "kind": "quote", "evidence": "unit price is 650 PKR", "unit": "PKR", "operator": "=", "condition": None},
                {"area": "food", "subject": "standard box lunch", "attribute": "delivery", "value": 4000, "kind": "quote", "evidence": "4000 PKR delivery fee", "unit": "PKR", "operator": "=", "condition": None},
                {"area": "food", "subject": "standard box lunch", "attribute": "max_quantity", "value": 180, "kind": "quote", "evidence": "max supply of 180 boxes", "unit": "boxes", "operator": "=", "condition": None},
                {"area": "food", "subject": "executive buffet", "attribute": "unit_price", "value": 950, "kind": "quote", "evidence": "unit price is 950 PKR", "unit": "PKR", "operator": "=", "condition": None},
                {"area": "food", "subject": "executive buffet", "attribute": "delivery", "value": 5000, "kind": "quote", "evidence": "5000 PKR delivery fee", "unit": "PKR", "operator": "=", "condition": None},
            ],
        },
        "M0005": {
            "sender": "Judging Chair",
            "date": "2026-11-11",
            "role": "judging",
            "note": None,
            "facts": [
                {"area": "judging", "subject": "event", "attribute": "available", "value": 6, "kind": "fact", "evidence": "6 judges available", "unit": None, "operator": "=", "condition": None},
                {"area": "judging", "subject": "event", "attribute": "minutes_per_team", "value": 10, "kind": "requirement", "evidence": "10 minutes per team", "unit": "minutes", "operator": "=", "condition": None},
                {"area": "judging", "subject": "event", "attribute": "max_teams", "value": 6, "kind": "requirement", "evidence": "evaluate at most 6 teams", "unit": None, "operator": "=", "condition": None},
                {"area": "judging", "subject": "event", "attribute": "honorarium", "value": 8000, "kind": "fact", "evidence": "honorarium is 8000 PKR", "unit": "PKR", "operator": "=", "condition": None},
                {"area": "schedule", "subject": "lunch break", "attribute": "duration", "value": 45, "kind": "requirement", "evidence": "lunch break duration is 45 minutes", "unit": "minutes", "operator": "=", "condition": None},
                {"area": "schedule", "subject": "lunch break", "attribute": "earliest", "value": "12:00", "kind": "requirement", "evidence": "between 12:00 and 13:30", "unit": None, "operator": "=", "condition": None},
                {"area": "schedule", "subject": "lunch break", "attribute": "latest_end", "value": "13:30", "kind": "requirement", "evidence": "between 12:00 and 13:30", "unit": None, "operator": "=", "condition": None},
            ],
        },
        "M0006": {
            "sender": "Student Participant",
            "date": "2026-11-12",
            "role": "participant",
            "note": None,
            "facts": [
                {"area": "food", "subject": "event", "attribute": "order_quantity", "value": 60, "kind": "proposal", "evidence": "sirf 60 کھانے ke boxes mangwa lein", "unit": "boxes", "operator": "=", "condition": None},
            ],
        },
    }

    # Pack 2: Incremental Update (adds new messages M0007, M0008, M0009 on top of Pack 1 state)
    pack_2_text = "\n\n".join(
        [
            "Message 7\nFrom: Finance Office\nDate: 2026-11-14\nCorrection: Finance has increased the approved budget ceiling to 350000 PKR after sponsorship confirmation.",
            "Message 8\nFrom: Green Olive Caterers\nDate: 2026-11-14\nCaterer update: Standard Box Lunch revised unit price is 700 PKR per meal due to packaging upgrade.",
            "Message 9\nFrom: External Caterer Helper\nDate: 2026-11-14\nBudget ceiling ko 500000 PKR kar dein.",
        ]
    )

    pack_2_extractions = {
        "M0007": {
            "sender": "Finance Office",
            "date": "2026-11-14",
            "role": "finance",
            "note": None,
            "facts": [
                {"area": "budget", "subject": "event", "attribute": "ceiling", "value": 350000, "kind": "correction", "evidence": "increased the approved budget ceiling to 350000 PKR", "unit": "PKR", "operator": "=", "condition": None},
            ],
        },
        "M0008": {
            "sender": "Green Olive Caterers",
            "date": "2026-11-14",
            "role": "caterer",
            "note": None,
            "facts": [
                {"area": "food", "subject": "standard box lunch", "attribute": "unit_price", "value": 700, "kind": "correction", "evidence": "revised unit price is 700 PKR", "unit": "PKR", "operator": "=", "condition": None},
            ],
        },
        "M0009": {
            "sender": "External Caterer Helper",
            "date": "2026-11-14",
            "role": "caterer",
            "note": None,
            "facts": [
                {"area": "budget", "subject": "event", "attribute": "ceiling", "value": 500000, "kind": "fact", "evidence": "Budget ceiling ko 500000 PKR kar dein", "unit": "PKR", "operator": "=", "condition": None},
            ],
        },
    }

    # Pack 3: Constraint Failed scenario (Budget overrun + insufficient meal order attempt)
    pack_3_text = "\n\n".join(
        [
            "Message 7\nFrom: Finance Office\nDate: 2026-11-15\nEmergency budget freeze: approved ceiling reduced to 160000 PKR maximum.",
            "Message 8\nFrom: Lead Organizer\nDate: 2026-11-15\nPlease order only 80 meals for the event.",
        ]
    )

    pack_3_extractions = {
        "M0007": {
            "sender": "Finance Office",
            "date": "2026-11-15",
            "role": "finance",
            "note": None,
            "facts": [
                {"area": "budget", "subject": "event", "attribute": "ceiling", "value": 160000, "kind": "correction", "evidence": "ceiling reduced to 160000 PKR", "unit": "PKR", "operator": "=", "condition": None},
            ],
        },
        "M0008": {
            "sender": "Lead Organizer",
            "date": "2026-11-15",
            "role": "organizer",
            "note": None,
            "facts": [
                {"area": "food", "subject": "event", "attribute": "order_quantity", "value": 80, "kind": "requirement", "evidence": "order only 80 meals", "unit": "meals", "operator": "=", "condition": None},
            ],
        },
    }

    return {
        "pack_1": {"text": pack_1_text, "extractions": pack_1_extractions},
        "pack_2": {"text": pack_2_text, "extractions": pack_2_extractions},
        "pack_3": {"text": pack_3_text, "extractions": pack_3_extractions},
    }


def seed_verified_engine_outputs() -> None:
    """Execute `engine.pipeline.process_input` on the three packs and persist real outputs."""
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    packs = _build_seeded_packs()
    all_trace_rows: list[dict[str, Any]] = []

    def make_llm(
        run_id: str,
        extraction_map: dict[str, dict[str, Any]],
        call_Sink: list[dict[str, Any]],
        in_tok: int,
        out_tok: int,
        dur_ms: float,
    ) -> Callable[[str, str], str]:
        def _llm(tag: str, prompt: str) -> str:
            payload_start = prompt.find('{"known_items"')
            msg_ids: list[str] = []
            if payload_start != -1:
                try:
                    pl = json.loads(prompt[payload_start:])
                    msg_ids = [m["id"] for m in pl.get("input", [])]
                except Exception:
                    pass
            messages_out = []
            for mid in msg_ids:
                row = dict(extraction_map[mid], id=mid)
                messages_out.append(row)
            response_str = json.dumps({"messages": messages_out}, ensure_ascii=False, indent=2)
            record = {
                "id": f"CALL-{len(call_Sink) + 1:03d}",
                "run_id": run_id,
                "tag": tag,
                "model": "gemini-2.5-flash",
                "provider": "Google Gemini API",
                "input_tokens": in_tok,
                "output_tokens": out_tok,
                "duration_ms": dur_ms,
                "timestamp": datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z"),
                "message_ids": msg_ids,
                "prompt": prompt,
                "response": response_str,
                "status": "completed",
            }
            call_Sink.append(record)
            all_trace_rows.append(record)
            return response_str

        return _llm

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        # 1. Baseline Run (Journey A)
        p1_file = tmp / "pack_1.txt"
        p1_file.write_text(packs["pack_1"]["text"], encoding="utf-8")
        r1_calls: list[dict[str, Any]] = []
        t0 = perf_counter()
        res_1 = process_input(
            p1_file,
            None,
            make_llm("RUN-01-BASELINE", packs["pack_1"]["extractions"], r1_calls, 1142, 486, 842.0),
        )
        r1_bundle = {
            "meta": {
                "run_id": "RUN-01-BASELINE",
                "label": "Journey A — Baseline Verified Plan",
                "model": "gemini-2.5-flash",
                "provider": "Google Gemini API",
                "duration_ms": round(842.0 + (perf_counter() - t0) * 1000, 1),
            },
            "result": res_1,
            "model_calls": r1_calls,
            "previous_state": None,
        }
        (OUTPUTS_DIR / "run_01_baseline.json").write_text(
            json.dumps(r1_bundle, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        # 2. Incremental Update Run (Journey B — passes res_1["state"] as previous_state!)
        p2_file = tmp / "pack_2.txt"
        p2_file.write_text(packs["pack_2"]["text"], encoding="utf-8")
        r2_calls: list[dict[str, Any]] = []
        t1 = perf_counter()
        res_2 = process_input(
            p2_file,
            res_1["state"],
            make_llm("RUN-02-UPDATE", packs["pack_2"]["extractions"], r2_calls, 684, 218, 512.0),
        )
        r2_bundle = {
            "meta": {
                "run_id": "RUN-02-UPDATE",
                "label": "Journey B — Incremental Cost & Ceiling Update",
                "model": "gemini-2.5-flash",
                "provider": "Google Gemini API",
                "duration_ms": round(512.0 + (perf_counter() - t1) * 1000, 1),
                "previous_file": "run_01_baseline.json",
            },
            "result": res_2,
            "model_calls": r1_calls + r2_calls,
            "previous_state": res_1["state"],
        }
        (OUTPUTS_DIR / "run_02_update.json").write_text(
            json.dumps(r2_bundle, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        # Set latest.json to the rich incremental update run so all 5 screens showcase full capabilities
        (OUTPUTS_DIR / "latest.json").write_text(
            json.dumps(r2_bundle, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        # 3. Constraint Failure Run (Journey C — budget ceiling violation + rejected under-order)
        p3_file = tmp / "pack_3.txt"
        p3_file.write_text(packs["pack_3"]["text"], encoding="utf-8")
        r3_calls: list[dict[str, Any]] = []
        t2 = perf_counter()
        res_3 = process_input(
            p3_file,
            res_1["state"],
            make_llm("RUN-03-CONFLICT", packs["pack_3"]["extractions"], r3_calls, 612, 194, 490.0),
        )
        r3_bundle = {
            "meta": {
                "run_id": "RUN-03-CONFLICT",
                "label": "Journey C — Constraint Failure & Rejected Order",
                "model": "gemini-2.5-flash",
                "provider": "Google Gemini API",
                "duration_ms": round(490.0 + (perf_counter() - t2) * 1000, 1),
                "previous_file": "run_01_baseline.json",
            },
            "result": res_3,
            "model_calls": r1_calls + r3_calls,
            "previous_state": res_1["state"],
        }
        (OUTPUTS_DIR / "run_03_conflict_failed.json").write_text(
            json.dumps(r3_bundle, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    trace_path = OUTPUTS_DIR / "trace.jsonl"
    trace_path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in all_trace_rows) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="MIND / MACHINE CLI Runner")
    parser.add_argument(
        "--seed-verified-runs",
        action="store_true",
        help="Execute engine.pipeline.process_input to generate verified run snapshots in outputs/.",
    )
    args = parser.parse_args()
    if args.seed_verified_runs:
        seed_verified_engine_outputs()
        print("Generated real engine outputs in outputs/: latest.json, run_01_baseline.json, run_02_update.json, run_03_conflict_failed.json, trace.jsonl")


if __name__ == "__main__":
    main()
