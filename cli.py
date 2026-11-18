"""Generate offline dashboard examples from labeled fixtures."""

import argparse
import json
from pathlib import Path

from engine.pipeline import process_input

ROOT = Path(__file__).resolve().parent


def seed_verified_engine_outputs():
    fixtures = ROOT / "tests/fixtures/studio"
    labels = json.loads((fixtures / "extractions.json").read_text())
    output = ROOT / "outputs"
    output.mkdir(exist_ok=True)
    baseline = None
    for index, name in enumerate(("baseline", "update", "conflict_failed"), 1):
        pack = f"pack_{index}"
        def fixture_response(area, prompt):
            return json.dumps({"messages": [dict(row, id=mid) for mid, row in labels[pack].items()]})

        result = process_input(fixtures / f"{pack}.txt", baseline, fixture_response)
        snapshot = {
            "meta": {"run_id": f"DEMO-{index}", "label": f"Offline example · {name}"},
            "result": result,
            "previous_state": baseline,
            "model_calls": [],
        }
        data = json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n"
        (output / f"run_{index:02}_{name}.json").write_text(data)
        if index == 1:
            baseline = result["state"]
        if index == 2:
            (output / "latest.json").write_text(data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-verified-runs", action="store_true", required=True)
    parser.parse_args()
    seed_verified_engine_outputs()
