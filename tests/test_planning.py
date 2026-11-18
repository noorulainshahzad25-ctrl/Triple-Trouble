import json

import pytest
from conftest import FIX

from engine.pipeline import process_input
from main import run


def test_complete_practice_pack(execute):
    summary, plan, decisions = execute("practice")
    assert (
        summary["actual_model_areas"] == summary["predicted_model_areas"] == ["reading"]
    )
    assert summary["mode"] == "full" and summary["processed_messages"] == 8
    assert plan["status"] == "valid"
    assert plan["event"]["teams"] == 50 and plan["event"]["meals"] == 177
    assert plan["venue"]["name"] == "hall a"
    assert plan["food"]["unit_price"] == 800 and plan["food"]["delivery"] == 0
    assert plan["judging"]["assigned"] == 17
    assert sum(a["teams"] for a in plan["judging"]["assignments"]) == 50
    assert plan["budget"]["total"] == 476600 and plan["budget"]["remaining"] == 173400
    assert plan["budget"]["currency"] == "Rs"
    assert sum(s["duration"] for s in plan["schedule"]) == 240
    assert ("prayer break", 15) in [
        (s["activity"], s["duration"]) for s in plan["schedule"]
    ]
    assert any(
        r["message_id"] == "M0003" and r["status"] == "superseded" for r in decisions
    )
    assert any(
        r["message_id"] == "M0007" and r["status"] == "rejected" for r in decisions
    )
    assert all(r["source_ids"] for r in plan["budget"]["line_items"])


def test_missing_required_prayer_break(monkeypatch):
    from engine.planner import build

    def omit_break(*args):
        plan = build(*args)
        timeline = plan["schedule"]["timeline"]
        timeline[:] = [t for t in timeline if t["activity"] != "prayer break"]
        return plan

    monkeypatch.setattr("engine.pipeline.build", omit_break)
    from conftest import extraction

    result = process_input(
        FIX / "practice.txt", None, lambda area, prompt: extraction(prompt)
    )
    assert result["plan"]["status"] == "invalid"
    assert any(
        c["check"] == "schedule.required_activity" for c in result["plan"]["unresolved"]
    )


def test_printing_and_wrong_food(execute, tmp_path, capsys):
    _, original, _ = execute("practice")
    summary, revised, _ = execute("printing")
    assert summary["mode"] == "update" and summary["changed_areas"] == ["budget"]
    assert revised["budget"]["total"] - original["budget"]["total"] == 5000
    summary, plan, rejected = execute("food")
    assert plan["status"] == "valid" and plan["food"]["quantity"] == 177
    assert summary["changed_areas"] == []
    reason = next(
        r["reason"]
        for r in rejected
        if r["status"] == "rejected" and r["affected_area"] == "food"
    )
    assert "77" in reason and reason in capsys.readouterr().out
    report = (tmp_path / "output/final_submission.txt").read_text()
    assert reason in report and "Session total: 174 reported tokens" in report
    assert summary["run_usage"]["total_tokens"] == 58


def test_supplier_cannot_revise_attendance(execute):
    execute("practice")
    summary, plan, rejected = execute("supplier")
    assert plan["event"]["students"] == 150 and summary["changed_areas"] == []
    assert any("cannot revise" in r["reason"] for r in rejected)


def test_new_venue_requirement(execute):
    execute("practice")
    summary, plan, _ = execute("venue")
    assert plan["venue"]["name"] == "hall b"
    assert set(summary["changed_areas"]) == {"venue", "budget"}


@pytest.mark.parametrize(
    "name,check",
    [
        ("overspend", "budget.ceiling"),
        ("judges", "judging.schedule"),
        ("capacity", "venue.selection"),
        ("unknown", "rule.induction_loop"),
    ],
)
def test_hold_infeasible_update(execute, name, check):
    _, old, _ = execute("practice")
    summary, p, rejected = execute(name)
    assert summary["pending_review"] and p["status"] == "needs_review"
    assert p["budget"] == old["budget"] and p["venue"] == old["venue"]
    failed = [c["check"] for c in p["unresolved"]]
    assert check in failed
    assert any(r["status"] == "pending_review" for r in rejected)


def test_recover_from_overspend(execute):
    execute("practice")
    execute("overspend")
    _, p, _ = execute("printing")
    assert p["status"] == "valid" and p["budget"]["total"] == 481600


def test_same_file_and_duplicate_message(execute, client):
    execute("practice")
    summary, p, rejected = execute("practice")
    assert summary["actual_model_areas"] == [] and summary["processed_messages"] == 0
    assert len(client.requests) == 1 and p["budget"]["total"] == 476600
    assert sum(r["status"] == "duplicate" for r in rejected) == 8
    execute("printing")
    summary, p, _ = execute("printing")
    assert summary["run_usage"]["calls"] == 0 and p["budget"]["total"] == 481600


def test_new_session(tmp_path, client):
    for session, name in [("practice", "practice"), ("official", "new_event")]:
        root = tmp_path / session
        s = run(FIX / (name + ".txt"), root, client)
        assert s["mode"] == "full" and s["session_usage"]["calls"] == 1
    state = json.loads((root / "state/engine_state.json").read_text())
    assert len(state["messages"]) == 1 and state["plan"]["attendance"]["students"] == 29


def test_mixed_batch_with_rejected_instruction(tmp_path, client):
    run(FIX / "practice.txt", tmp_path, client)
    batch = tmp_path / "mixed.txt"
    batch.write_text(
        (FIX / "printing.txt").read_text() + "\n" + (FIX / "food.txt").read_text()
    )
    summary = run(batch, tmp_path, client)
    plan = json.loads((tmp_path / "output/plan.json").read_text())
    assert summary["processed_messages"] == 2
    assert summary["actual_model_areas"] == ["reading"]
    assert summary["changed_areas"] == ["budget"]
    assert plan["budget"]["total"] == 481600 and plan["food"]["quantity"] == 177


def test_review_reasons_survive_duplicate(execute):
    execute("practice")
    execute("overspend")
    summary, plan, decisions = execute("overspend")
    assert summary["pending_review"] and summary["actual_model_areas"] == []
    assert plan["pending_candidate"]["budget"]["remaining"] < 0
    assert any(d["status"] == "pending_review" for d in decisions)
