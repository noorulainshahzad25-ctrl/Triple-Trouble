# Shared planning contract

The runtime calls the planning engine through this interface.

```python
from pathlib import Path
from typing import Callable
from engine.pipeline import process_input

# Signature implemented by the core engine
# process_input(input_path: Path, previous_state: dict | None,
#               llm: Callable[[str, str], str]) -> dict
result = process_input(input_path, previous_state, llm)
```

The only model interface available to the engine is `llm(area, prompt) -> str`.
Pass exactly one tag from reading, venue, schedule, food, judging and budget, and
the complete request text. All provider access, timing, limits and auditing
belong to the runtime. The UI consumes persisted outputs.

The canonical result is JSON-serializable and has the following shape.

```python
{
    "mode": "full" | "update",
    "state": {}, "plan": {}, "rejections": [],
    "changed_areas": [], "predicted_model_areas": [], "processed_messages": 0,
}
```

The public plan contains these fields.

```python
{
    "status": "valid" | "invalid" | "needs_review",
    "event": {}, "venue": {}, "schedule": [], "food": {}, "judging": {},
    "budget": {}, "validations": [], "unresolved": [], "source_ids": [],
}
```

Budget fields are currency, limit, line_items, total and remaining. Each line item
has name, cost and source_ids. Each rejection has message_id, status, reason,
affected_area and source_ids. Keep source identifiers stable within a session.

Append one JSON object per actual model request to the session trace. Include
run_id, call_number, area, model, input, output, input_tokens, output_tokens,
total_tokens, latency_ms and usage_source. Number attempts in order. Copy
provider counters exactly. Use null for missing counters, identify unavailable
usage, and retain failed attempts with their errors. Record the model identifier
returned by the provider when available. Never synthesize model calls or usage.

Run both initial and incremental inputs with `python main.py input/messages.txt`.
The full run budget is 120 seconds. Updates have 60 seconds and five calls.
Keep event facts in the input files. The engine owns parsing, conflict resolution,
planning and validation. The runtime owns main.py, the gateway, tracing, reporting,
tests, environment examples and operator documentation.
