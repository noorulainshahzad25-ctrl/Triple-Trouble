"""Verification suite for MIND / MACHINE UI adapter, validation semantics, and all 5 screens."""

from __future__ import annotations

import sys
import types
import unittest
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from ui.adapter import (
    compute_snapshot_diffs,
    discover_run_files,
    domain_validation_summary,
    empty_bundle,
    format_audit_report,
    inspect_workspace_files,
    load_run_bundle,
)
from ui.tokens import DOMAINS, PALETTE, SCREENS, TOKEN_UNAVAILABLE_LABEL, status_meta


class _DummyStreamlit:
    """Lightweight Streamlit harness to capture all rendered HTML/Markdown and widget calls."""

    def __init__(self) -> None:
        self.markdowns: list[str] = []
        self.codes: list[str] = []
        self.buttons: list[str] = []
        self.downloads: list[str] = []
        self.session_state: dict[str, Any] = {"mm_active_screen": "overview"}
        self.sidebar = self

    def __enter__(self) -> "_DummyStreamlit":
        return self

    def __exit__(self, *args: object) -> None:
        pass

    def set_page_config(self, **kwargs: object) -> None:
        pass

    def markdown(self, body: str, unsafe_allow_html: bool = False) -> None:
        self.markdowns.append(str(body))

    def code(self, body: str, language: str | None = None) -> None:
        self.codes.append(str(body))

    def button(self, label: str, **kwargs: object) -> bool:
        self.buttons.append(label)
        return False

    def download_button(self, label: str, **kwargs: object) -> bool:
        self.downloads.append(label)
        return False

    def selectbox(self, label: str, options: list[Any], index: int = 0, **kwargs: object) -> Any:
        return options[index] if options else None

    def radio(self, label: str, options: list[Any], index: int = 0, **kwargs: object) -> Any:
        return options[index] if options else None

    def file_uploader(self, label: str, **kwargs: object) -> None:
        return None

    def columns(self, spec: int | list[float], **kwargs: object) -> list["_DummyStreamlit"]:
        count = spec if isinstance(spec, int) else len(spec)
        return [self for _ in range(count)]

    @contextmanager
    def expander(self, label: str, **kwargs: object):
        self.markdowns.append(f"EXPANDER:{label}")
        yield self

    def rerun(self) -> None:
        pass


class TestMindMachineDecisionStudio(unittest.TestCase):
    def test_palette_and_validation_semantics_contract(self) -> None:
        self.assertEqual(PALETTE["bg_main"], "#F5F4F0")
        self.assertEqual(PALETTE["surface_primary"], "#FFFFFF")
        self.assertEqual(PALETTE["surface_secondary"], "#ECEAE4")
        self.assertEqual(PALETTE["text_primary"], "#141414")
        self.assertEqual(PALETTE["text_secondary"], "#676B69")
        self.assertEqual(PALETTE["border_hairline"], "#D8D8D2")
        self.assertEqual(PALETTE["stage_dark"], "#151719")
        self.assertEqual(PALETTE["surface_dark_elevated"], "#232629")
        self.assertEqual(PALETTE["accent"], "#C9E76B")
        self.assertEqual(PALETTE["verified"], "#2D7452")
        self.assertEqual(PALETTE["failed"], "#B63E3D")
        self.assertEqual(PALETTE["warning"], "#9B680B")

        self.assertEqual(status_meta("valid")["label"], "VERIFIED")
        self.assertEqual(status_meta("invalid")["label"], "CONSTRAINT FAILED")
        self.assertEqual(status_meta("needs_review")["label"], "NEEDS REVIEW")
        self.assertEqual(status_meta(None)["label"], "AWAITING INPUT")
        self.assertEqual(TOKEN_UNAVAILABLE_LABEL, "TOKEN USAGE UNAVAILABLE")

    def test_five_screens_and_five_domains_configured(self) -> None:
        self.assertEqual([s["id"] for s in SCREENS], ["overview", "plan", "audit", "updates", "system"])
        self.assertEqual([d["key"] for d in DOMAINS], ["venue", "schedule", "food", "judging", "budget"])

    def test_persisted_runs_and_adapter(self) -> None:
        files = discover_run_files()
        names = {f.name for f in files}
        self.assertIn("latest.json", names)
        self.assertIn("run_01_baseline.json", names)
        self.assertIn("run_02_update.json", names)
        self.assertIn("run_03_conflict_failed.json", names)

        # Baseline run verification
        b1 = load_run_bundle(Path("outputs/run_01_baseline.json"))
        self.assertTrue(b1["loaded"])
        self.assertEqual(b1["status"], "valid")
        self.assertEqual(b1["status_meta"]["label"], "VERIFIED")
        self.assertIsNone(b1["previous_state"])
        self.assertEqual(compute_snapshot_diffs(b1), [])

        # Update run verification (recomputed areas vs called model tags + real snapshot diffs)
        b2 = load_run_bundle(Path("outputs/run_02_update.json"))
        self.assertTrue(b2["loaded"])
        self.assertEqual(b2["status"], "valid")
        self.assertIsNotNone(b2["previous_state"])
        self.assertIn("food", b2["recomputed_areas"])
        self.assertIn("budget", b2["recomputed_areas"])
        self.assertEqual(b2["called_model_tags"], [])
        self.assertEqual(b2["telemetry"]["call_count"], 0)
        self.assertEqual(b2["predicted_model_areas"], ["reading"])
        diffs = compute_snapshot_diffs(b2)
        self.assertTrue(len(diffs) >= 2)

        # Conflict / constraint failed run verification
        b3 = load_run_bundle(Path("outputs/run_03_conflict_failed.json"))
        self.assertTrue(b3["loaded"])
        self.assertEqual(b3["status"], "invalid")
        self.assertEqual(b3["status_meta"]["label"], "CONSTRAINT FAILED")
        b_dom = domain_validation_summary(b3, "budget")
        self.assertEqual(b_dom["status"], "invalid")

        # Empty / awaiting input verification
        b_empty = empty_bundle()
        self.assertFalse(b_empty["loaded"])
        self.assertEqual(b_empty["status_meta"]["label"], "AWAITING INPUT")
        self.assertFalse(b_empty["telemetry"]["tokens_available"])

        # Audit report & file inventory
        rep = format_audit_report(b2)
        self.assertIn("MIND / MACHINE — AUDITED DECISION REPORT", rep)
        inv = inspect_workspace_files(b2)
        self.assertTrue(any(item["present"] for item in inv))

    def test_all_five_screens_render_Across_all_states(self) -> None:
        dummy_st = _DummyStreamlit()
        sys.modules["streamlit"] = dummy_st  # type: ignore[assignment]

        from ui.components.shell import render_sidebar_and_load_bundle, render_top_instrument_strip
        from ui.screens.audit import render_audit_screen
        from ui.screens.overview import render_overview_screen
        from ui.screens.plan import render_plan_screen
        from ui.screens.system import render_system_screen
        from ui.screens.updates import render_updates_screen
        from ui.styles import inject_editorial_styles

        inject_editorial_styles()
        active_screen, loaded_bundle = render_sidebar_and_load_bundle()
        self.assertEqual(active_screen, "overview")
        self.assertTrue(loaded_bundle["loaded"])

        bundles = [
            load_run_bundle(Path("outputs/run_01_baseline.json")),
            load_run_bundle(Path("outputs/run_02_update.json")),
            load_run_bundle(Path("outputs/run_03_conflict_failed.json")),
            empty_bundle(),
        ]

        for b in bundles:
            dummy_st.markdowns.clear()
            render_top_instrument_strip("overview", b)
            render_overview_screen(b)
            render_plan_screen(b)
            render_audit_screen(b)
            render_updates_screen(b)
            render_system_screen(b)
            combined = "\n".join(dummy_st.markdowns)
            self.assertIn("MESSY INPUT.", combined)
            self.assertIn("CLEAR DECISIONS.", combined)
            self.assertIn("FIVE DECISIONS.", combined)
            self.assertIn("ONE ACCOUNTABLE PLAN.", combined)
            self.assertIn("EVERY DECISION.", combined)
            self.assertIn("ACCOUNTED FOR.", combined)
            self.assertIn("THE CHANGE.", combined)
            self.assertIn("AND THE REASON.", combined)
            self.assertIn("THE RECEIPTS.", combined)
            if b["loaded"]:
                self.assertIn("THE PLAN, EXPLAINED.", combined)
                self.assertIn("DOMAINS RECOMPUTED", combined)
                self.assertIn("MODEL TAGS ACTUALLY CALLED", combined)
            else:
                self.assertIn("AWAITING INPUT.", combined)


if __name__ == "__main__":
    unittest.main()


def test_dashboard_reads_published_sessions(execute, tmp_path):
    summary, baseline, _ = execute("practice")
    latest = tmp_path / "output/run_summary.json"
    bundle = load_run_bundle(latest)
    assert bundle["run_id"] == summary["run_id"]
    assert bundle["telemetry"]["total_tokens"] == 58
    assert bundle["plan"]["budget"]["currency"] == "Rs"
    assert bundle["previous_state"] is None

    execute("overspend")
    held = load_run_bundle(latest)
    assert held["status"] == "needs_review"
    assert held["plan"]["budget"]["total"] == baseline["budget"]["total"]
    assert held["previous_state"]["plan"]["budget"] == held["plan"]["budget"]

    execute("overspend")
    replay = load_run_bundle(latest)
    assert replay["telemetry"]["call_count"] == 0
    assert replay["called_model_tags"] == []
