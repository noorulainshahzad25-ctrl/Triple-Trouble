# MIND / MACHINE — Axial-Inspired Visual Design System & Architecture

**Product:** `MIND / MACHINE` (`M//M`)  
**Tagline:** `Messy messages. Defensible decisions.`  
**Creative Direction:** `EDITORIAL / INTELLIGENCE`  
**Visual Concept:** `THE DECISION STUDIO`  
**Design Reference:** [Axial Studio](https://axialstudioads.com/start) (translated into an original decision-intelligence editorial interface)

---

## 1. Explicit Implementation Priority Order

To guarantee a zero-breakage, cohesive build across parallel agents while preserving `engine/` 100% unchanged, implementation follows a strict five-phase priority sequence (`P0` $\rightarrow$ `P4`):

### Priority P0 — Shared Foundation, Tokens & Read-Only Backend Adapter (Integration Owner)
1. **`ui/tokens.py`**: Define immutable color tokens (`#F5F4F0` canvas, `#151719` dark showcase stage, `#C9E76B` strategic accent, `#2D7452` verified, `#B63E3D` failed, `#9B680B` warning), typography scale, validation state mapping (`VERIFIED`, `CONSTRAINT FAILED`, `NEEDS REVIEW`, `AWAITING INPUT`, `TOKEN USAGE UNAVAILABLE`), and domain metadata.
2. **`ui/styles.py`**: Implement scoped CSS rules for Streamlit containers, editorial display typography (`clamp(44px, 6.5vw, 96px)`), asymmetric showcase grids, tabular numerals, dark-stage contrast blocks, keyboard focus outlines (`2px solid`), responsive breakpoints (`1440px`, `1024px`, `768px`), and `@media (prefers-reduced-motion: reduce)`.
3. **`ui/adapter.py`**: Build the read-only data adapter that discovers and loads persisted backend outputs (`outputs/*.json`, `trace.jsonl`, previous state snapshots, or user-selected output files) without ever calling an LLM or mutating `engine/`. Provide deterministic report formatting for export.

### Priority P1 — Reusable Editorial Component Library & Application Shell (Integration Owner)
1. **`ui/components/badges.py`**: Validation status pills (`VERIFIED`, `CONSTRAINT FAILED`, `NEEDS REVIEW`, `AWAITING INPUT`), monospace source reference chips (`M0001`), role badges, and domain tags.
2. **`ui/components/empty_states.py`**: Art-directed empty, incomplete, and error state panels (`AWAITING INPUT`, `NO PRIOR SNAPSHOT`, `TOKEN USAGE UNAVAILABLE`) that never fabricate success or placeholder numbers.
3. **`ui/components/hero.py`**: Full-width asymmetric editorial hero component pairing oversized grotesk headlines with live run validation monuments.
4. **`ui/components/metrics.py`**: Minimalist 4-column hairline metric rail with tabular numerals and source provenance captions.
5. **`ui/components/shell.py` & `app.py`**: Top instrument strip, minimalist sidebar navigation (`01 OVERVIEW` through `05 SYSTEM`), active run switcher, and session-state screen router.

### Priority P2 — Core Decision & Planning Experience (UI Agent A & UI Agent B in Parallel)
1. **`ui/screens/overview.py` (UI Agent A — SCREEN 01: OVERVIEW)**:
   - Hero (`MESSY INPUT. / CLEAR DECISIONS.`) with `View the Plan` and `Inspect Evidence` actions + live plan status monument.
   - Minimalist metric rail (`Plan Status`, `Source Messages`, `Model Calls`, `Token Usage`).
   - Dark showcase centerpiece (`#151719` stage): **`THE PLAN, EXPLAINED.`** — asymmetric 5-domain visual composition with bespoke mini-instruments.
   - Latest conflicts digest and source evidence ledger below the showcase.
2. **`ui/screens/plan.py` (UI Agent B — SCREEN 02: THE PLAN)**:
   - Hero (`FIVE DECISIONS. / ONE ACCOUNTABLE PLAN.`).
   - Five distinct, non-repetitive domain instruments:
     - `01 / VENUE`: Occupancy gauge, mandatory facility checklist, and excluded venue ledger.
     - `02 / SCHEDULE`: Proportional horizontal sequence bar and vertical chronological time rail.
     - `03 / FOOD`: Attendee group meal demand vs. supply coverage bar and unit/delivery price equation.
     - `04 / JUDGING`: Judge-to-team assignment workload matrix and time-window utilization bars.
     - `05 / BUDGET`: Multi-segment proportional allocation bar (`venue`, `food`, `judging`, extras, headroom/overrun) and double-rule financial ledger.

### Priority P3 — Trust, Change Intelligence & Operational Receipts (UI Agent C)
1. **`ui/screens/audit.py` (SCREEN 03: AUDIT TRAIL)**:
   - Hero (`EVERY DECISION. / ACCOUNTED FOR.`).
   - Recorded model inference ledger (`model_id`, `input_tokens`, `output_tokens`, `duration`, expandable raw prompts & responses).
   - Restrained high-contrast rejection evidence (`INCOMING CLAIM` vs. `WHY IT FAILED` + conflicting source IDs).
   - Complete deterministic validation check ledger and filterable source message corpus.
2. **`ui/screens/updates.py` (SCREEN 04: UPDATES)**:
   - Hero (`THE CHANGE. / AND THE REASON.`).
   - Strict visual and logical separation between **`DOMAINS RECOMPUTED (DETERMINISTIC SOLVER)`** (`state.affected_areas` / `changed_areas`) and **`MODEL TAGS ACTUALLY CALLED (LLM INFERENCE)`** (`predicted_model_areas` / trace calls).
   - Real before/after field-level snapshot diff when `previous_state` exists (and an honest `BASELINE RUN` state when no prior snapshot exists).
3. **`ui/screens/system.py` (SCREEN 05: SYSTEM)**:
   - Hero (`THE RECEIPTS.`).
   - Quiet, high-precision operational ledger: Run ID, data freshness, model/provider telemetry, token usage, execution time, output file inventory with SHA-256 hashes, error diagnostics, and one-click report/JSON exports.

### Priority P4 — Real Backend Verification, CLI Harness & Responsive QA (All Agents)
1. **`cli.py` & `outputs/`**: Provide a non-invasive CLI runner that invokes `engine.pipeline.process_input`, records real execution telemetry to `outputs/trace.jsonl`, and writes atomic snapshots (`outputs/run_01_baseline.json`, `outputs/run_02_update.json`, `outputs/run_03_conflict_failed.json`) so all five screens and all user journeys (`VERIFIED`, `INCREMENTAL UPDATE`, `CONSTRAINT FAILED`, `AWAITING INPUT`) are verified against real `engine/` output.
2. Verify responsive rendering (`1440×900` desktop, tablet, mobile) and WCAG AA contrast.

---

## 2. Exact Streamlit File Structure

```text
Triple-Trouble/
├── app.py                                         # [Integration Owner] Main Streamlit entrypoint, page config & screen router
├── cli.py                                         # [Integration Owner] CLI runner wrapping engine.pipeline.process_input + trace logger
├── requirements.txt                               # [Integration Owner] Python dependencies (streamlit)
├── 07_VISUAL_DESIGN_SYSTEM_AXIAL_INSPIRED.md      # [Integration Owner] Master design system, priority order & file structure spec
├── engine/                                        # [BACKEND — UNCHANGED] Deterministic event planning & conflict engine
│   ├── conflict_resolver.py
│   ├── domain_holdout.json
│   ├── domain_model.json
│   ├── domain_model.py
│   ├── domain_training.json
│   ├── extractor.py
│   ├── ingest.py
│   ├── pipeline.py
│   ├── planner.py
│   ├── schemas.py
│   ├── updater.py
│   └── validator.py
├── outputs/                                       # [PERSISTED RUN ARTIFACTS] Real engine outputs & JSONL inference traces
│   ├── latest.json                                # Active run bundle (result + metadata + trace + optional previous snapshot)
│   ├── run_01_baseline.json                       # Journey A: Baseline verified hackathon plan from engine.pipeline
│   ├── run_02_update.json                         # Journey B: Incremental update with real previous_state snapshot diff
│   ├── run_03_conflict_failed.json                # Journey C: Constraint failure & rejected conflicting instructions
│   └── trace.jsonl                                # Recorded model call audit log
└── ui/                                            # [FRONTEND PACKAGE — THE DECISION STUDIO]
    ├── __init__.py
    ├── tokens.py                                  # [Integration Owner] Palette, typography, status semantics & domain labels
    ├── styles.py                                  # [Integration Owner] Scoped Axial-inspired editorial CSS
    ├── adapter.py                                 # [Integration Owner] Read-only backend output loader, diff computer & exporter
    ├── components/                                # [Integration Owner] Shared UI primitives
    │   ├── __init__.py
    │   ├── badges.py                              # Status pills, monospace source chips, role & domain badges
    │   ├── empty_states.py                        # AWAITING INPUT, NEEDS REVIEW, and missing-snapshot states
    │   ├── hero.py                                # Editorial hero header + live status monument
    │   ├── metrics.py                             # Minimalist 4-column metric rail
    │   └── shell.py                               # Sidebar navigation, top instrument strip & run selector
    └── screens/                                   # [Multi-Agent Screen Modules]
        ├── __init__.py
        ├── overview.py                            # [UI Agent A] SCREEN 01: OVERVIEW & Dark Showcase ("THE PLAN, EXPLAINED.")
        ├── plan.py                                # [UI Agent B] SCREEN 02: THE PLAN (5 bespoke domain instruments)
        ├── audit.py                               # [UI Agent C] SCREEN 03: AUDIT TRAIL (Model calls, prompts, rejections, sources)
        ├── updates.py                             # [UI Agent C] SCREEN 04: UPDATES (Recomputed vs. LLM tags + snapshot diffs)
        └── system.py                              # [UI Agent C] SCREEN 05: SYSTEM ("THE RECEIPTS." operational ledger & export)
```

---

## 3. Design Tokens & Visual Language

| Token | CSS Variable | Hex | Role |
| :--- | :--- | :--- | :--- |
| Main background | `--bg-main` | `#F5F4F0` | Warm editorial off-white reading canvas |
| Primary surface | `--surface-primary` | `#FFFFFF` | Elevated cards, ledgers, and instruments on light canvas |
| Secondary surface | `--surface-secondary` | `#ECEAE4` | Quiet structural wells, secondary cells, metadata rails |
| Primary typography | `--text-primary` | `#141414` | Oversized headlines, primary figures, body copy |
| Secondary typography | `--text-secondary` | `#676B69` | Editorial captions, overlines, secondary labels |
| Hairline borders | `--border-hairline` | `#D8D8D2` | `1px solid` architectural grid rules and dividers |
| Dark showcase stage | `--stage-dark` | `#151719` | Dramatic high-contrast showcase (`THE PLAN, EXPLAINED.`) |
| Elevated dark surface | `--surface-dark-elevated` | `#232629` | Domain instruments inside the dark showcase stage |
| Accent | `--accent` | `#C9E76B` | Strategic acid-lime signal for active indicators and dark-stage highlights |
| Verified | `--status-verified` | `#2D7452` | Mandatory constraints verified (`VERIFIED`) |
| Failed | `--status-failed` | `#B63E3D` | Mandatory constraint violation or rejected claim (`CONSTRAINT FAILED`) |
| Warning | `--status-warning` | `#9B680B` | Missing verification or unresolved conflict (`NEEDS REVIEW`) |

### Validation Semantics Contract

| Backend Condition | UI Canonical Label | Token | Meaning |
| :--- | :--- | :--- | :--- |
| `result["status"] == "valid"` | `VERIFIED` | `#2D7452` | All applicable mandatory constraints pass. |
| `result["status"] == "invalid"` | `CONSTRAINT FAILED` | `#B63E3D` | At least one known mandatory requirement fails. |
| `result["status"] == "needs_review"` | `NEEDS REVIEW` | `#9B680B` | Essential verification is missing or unknown. |
| `result is None` | `AWAITING INPUT` | `#676B69` | No run has been loaded. |
| `tokens is None` | `TOKEN USAGE UNAVAILABLE` | `#676B69` | The provider did not report token usage. |
