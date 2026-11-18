"""Official CLI. Run from the repository root on Linux, macOS or WSL."""

import sys

if sys.version_info < (3, 10):
    sys.exit("Python 3.10 or newer is required. Found " + sys.version.split()[0] + ".")

import argparse
import fcntl
import json
import os
import signal
import sys
import time
from contextlib import contextmanager
from pathlib import Path

from dotenv import load_dotenv

from engine.pipeline import process_input
from engine.reporting import publish, render
from engine.schemas import AREAS
from engine.tracing import TraceRecorder, token_text, totals


@contextmanager
def time_limit(deadline):
    def expired(*_):
        raise TimeoutError("Competition wall-clock deadline exceeded.")

    old = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, max(0.000001, deadline - time.monotonic()))
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old)


def run(path, root, client=None):
    started = time.monotonic()
    state_dir = root / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    with (state_dir / ".lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError(
                "Another run is already processing this session."
            ) from None
        state_path = state_dir / "engine_state.json"
        previous = (
            json.loads(state_path.read_text(encoding="utf-8"))
            if state_path.exists()
            else None
        )
        seconds = 60 if previous is not None else 120
        deadline = started + seconds
        trace = TraceRecorder(
            root / "output/trace.jsonl", deadline, previous is not None, client
        )
        try:
            with time_limit(deadline):
                result = process_input(path, previous, trace)
                if trace.error:
                    raise RuntimeError(trace.error)
                errors = [
                    m["error"] for m in result["state"]["messages"] if m.get("error")
                ]
                if errors:
                    raise ValueError(
                        "Extraction incomplete: " + "; ".join(dict.fromkeys(errors))
                    )
                state, candidate = result["state"], result["plan"]
                # Stage infeasible revisions for reconciliation. Keep the last validated
                # plan visible and expose what failed, so a later correction can repair it.
                prior_valid = (previous or {}).get("last_valid_plan")
                staged = prior_valid is not None and candidate["status"] != "valid"
                pending_ids = (
                    list((previous or {}).get("pending_ids", [])) if staged else []
                )
                if staged:
                    result["plan"] = dict(
                        prior_valid,
                        status="needs_review",
                        pending_candidate=candidate,
                        unresolved=candidate["unresolved"],
                        validations=candidate["validations"],
                    )
                    result["changed_areas"] = []
                    reason = "Held pending review: " + " ".join(
                        c["reason"] for c in candidate["unresolved"]
                    )
                    pending_ids.extend(
                        m["id"]
                        for m in state["messages"][len(previous["messages"]) :]
                        if not m.get("duplicate_of") and m["facts"]
                    )
                    for m in state["messages"]:
                        if m["id"] in pending_ids:
                            result["rejections"].append(
                                {
                                    "message_id": m["id"],
                                    "status": "pending_review",
                                    "reason": reason,
                                    "affected_area": ", ".join(m["domains"]),
                                    "source_ids": [m["id"]],
                                }
                            )
                elif prior_valid is not None:
                    result["changed_areas"] = [
                        area for area in AREAS if prior_valid[area] != candidate[area]
                    ]
                state["pending_ids"] = pending_ids
                state["last_valid_plan"] = (
                    candidate if candidate["status"] == "valid" else prior_valid
                )
                rows = trace.history + trace.rows
                summary = {
                    k: v
                    for k, v in result.items()
                    if k not in ("plan", "rejections", "state")
                }
                summary.update(
                    run_id=trace.run_id,
                    previous_run_id=state_path.resolve().parent.name if previous else None,
                    status=result["plan"]["status"],
                    pending_review=staged,
                    actual_model_areas=[r["area"] for r in trace.rows],
                    run_usage=totals(trace.rows),
                    session_usage=totals(rows),
                    limit_seconds=seconds,
                )
                display, submission = render(result, rows, summary)
                print("\n" + display)
                elapsed = time.monotonic() - started
                summary["elapsed_seconds_before_publish"] = round(elapsed, 4)
                if elapsed >= seconds * 0.8 or (previous and len(trace.rows) >= 4):
                    print("Warning: approaching a competition limit.", file=sys.stderr)
                publish(root, trace.run_id, result, summary, submission)
                return summary
        finally:
            print(f"Elapsed {time.monotonic() - started:.3f}s / {seconds}s")
            print("Run total: " + token_text(totals(trace.rows)))
            print("Session total: " + token_text(totals(trace.history + trace.rows)))


def main():
    parser = argparse.ArgumentParser(
        description="Plan a hackathon from a UTF-8 message file."
    )
    parser.add_argument("input_path", type=Path)
    args = parser.parse_args()
    load_dotenv(Path.cwd() / ".env")
    try:
        result = run(args.input_path, Path(os.getenv("PLANNER_SESSION_DIR", ".")))
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Run failed: {exc}", file=sys.stderr)
        return 1
    return 0 if result["status"] == "valid" else 2


if __name__ == "__main__":
    sys.exit(main())
