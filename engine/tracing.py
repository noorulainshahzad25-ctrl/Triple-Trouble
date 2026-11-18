"""Append provider evidence before returning any response to the engine."""

import json
import os
import time
from uuid import uuid4

from .model_client import ModelClient

TAGS = {"reading", "venue", "schedule", "food", "judging", "budget"}
COUNTERS = ("input_tokens", "output_tokens", "total_tokens")


def totals(rows):
    return {
        **{
            field: sum(r[field] for r in rows if r[field] is not None)
            for field in COUNTERS
        },
        "calls": len(rows),
        "incomplete_usage_calls": sum(r["usage_source"] != "provider" for r in rows),
        "unreported_total_calls": sum(r["total_tokens"] is None for r in rows),
    }


def token_text(summary):
    return (
        f"{summary['total_tokens']} reported tokens "
        f"({summary['unreported_total_calls']} calls without a reported total)"
    )


def read_trace(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


class TraceRecorder:
    def __init__(self, path, deadline, update, client=None):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)
        self.history = read_trace(path)
        self.rows = []
        self.client = client
        self.run_id = uuid4().hex
        self.deadline = deadline
        self.update = update
        self.error = None

    def __call__(self, area, prompt):
        try:
            if area not in TAGS:
                raise ValueError(f"Invalid model area: {area!r}")
            if self.update and len(self.rows) >= 5:
                raise RuntimeError("Five-call update limit reached.")
            if self.client is None:
                self.client = ModelClient.configured()
            remaining = self.deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("Run deadline reached before dispatch.")
            return self._call(area, prompt, remaining)
        except Exception as exc:
            self.error = str(exc) or type(exc).__name__
            raise

    def _call(self, area, prompt, remaining):
        request = self.client.request(prompt)
        started = time.monotonic()
        row = {
            "run_id": self.run_id,
            "call_number": len(self.history) + len(self.rows) + 1,
            "area": area,
            "model": self.client.model,
            "model_source": "requested",
            "input": prompt,
            "request": request,
            "output": None,
            "usage_source": "unavailable",
            "input_tokens": None,
            "output_tokens": None,
            "total_tokens": None,
        }
        try:
            response = self.client.send(request, remaining)
            row["http_status"] = response.status_code
            # Retain the body even if the endpoint returns invalid JSON or an error.
            row["provider_response"] = response.text
            if not response.is_success:
                raise RuntimeError(
                    f"Provider HTTP {response.status_code}. See trace for response."
                )
            data = response.json()
            if isinstance(data.get("model"), str) and data["model"]:
                row.update(model=data["model"], model_source="provider")
            usage = data.get("usage") or {}
            for local, remote in zip(
                COUNTERS, ("prompt_tokens", "completion_tokens", "total_tokens")
            ):
                value = usage.get(remote)
                if type(value) is int and value >= 0:
                    row[local] = value
            if all(row[k] is not None for k in COUNTERS):
                row["usage_source"] = "provider"
            elif any(row[k] is not None for k in COUNTERS):
                row["usage_source"] = "partial"
            choice = data["choices"][0]
            row["output"] = choice["message"].get("content")
            if choice.get("finish_reason") in {"length", "content_filter"}:
                raise ValueError(
                    f"Provider stopped generation: {choice['finish_reason']}"
                )
            if not isinstance(row["output"], str) or not row["output"].strip():
                raise ValueError("Provider returned no text content.")
            return row["output"]
        except BaseException as exc:
            row["error"] = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            row["latency_ms"] = round((time.monotonic() - started) * 1000)
            with self.path.open("a", encoding="utf-8") as out:
                out.write(json.dumps(row, ensure_ascii=False) + "\n")
                out.flush()
                os.fsync(out.fileno())
            self.rows.append(row)
            print(
                f"\nCall {row['call_number']} | {area} | {row['model']}"
                f"\nInput\n{prompt}\nOutput\n{row['output']}"
                f"\nTokens (input / output / total): "
                f"{row['input_tokens']} / {row['output_tokens']} / {row['total_tokens']}",
                flush=True,
            )
            if "error" in row:
                print(row["error"])
