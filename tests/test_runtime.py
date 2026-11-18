import ast
import fcntl
import json
import os
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import httpx
import pytest
from conftest import FIX, extraction
from dotenv import load_dotenv

from engine.tracing import TraceRecorder, totals
from main import run, time_limit

ROOT = Path(__file__).resolve().parents[1]


def test_update_cap_before_dispatch(tmp_path, client):
    rec = TraceRecorder(tmp_path / "trace.jsonl", time.monotonic() + 30, True, client)
    for _ in range(5):
        rec("reading", '{"input":[]}')
    with pytest.raises(RuntimeError, match="Five-call"):
        rec("reading", '{"input":[]}')
    assert len(client.requests) == len(rec.rows) == 5
    assert [r["call_number"] for r in rec.rows] == list(range(1, 6))
    assert totals(rec.rows)["total_tokens"] == 5 * 58


def test_invalid_tag_and_config_are_not_calls(tmp_path, monkeypatch):
    for name in ("MODEL_BASE_URL", "MODEL_NAME"):
        monkeypatch.delenv(name, raising=False)
    rec = TraceRecorder(tmp_path / "trace.jsonl", time.monotonic() + 5, False)
    for tag in ("fake", "reading"):
        with pytest.raises(ValueError):
            rec(tag, "text")
    assert rec.path.read_text() == ""


@pytest.mark.parametrize(
    "fault", ["timeout", "invalid envelope", "invalid extraction", "truncated", "http"]
)
def test_failures_keep_audit_and_checkpoint(tmp_path, client, fault):
    run(FIX / "practice.txt", tmp_path, client)
    pointer = (tmp_path / "state/current").readlink()

    def fail(req, remaining):
        if fault == "timeout":
            raise httpx.ReadTimeout("endpoint timeout")
        if fault == "invalid envelope":
            return httpx.Response(200, text="not JSON")
        if fault == "http":
            return httpx.Response(429, json={"error": "rate limit"})
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {"content": "{"},
                        "finish_reason": "length" if fault == "truncated" else "stop",
                    }
                ]
            },
        )

    client.send = fail
    with pytest.raises((RuntimeError, ValueError)):
        run(FIX / "printing.txt", tmp_path, client)
    assert (tmp_path / "state/current").readlink() == pointer
    lines = [
        json.loads(s)
        for s in (tmp_path / "output/trace.jsonl").read_text().splitlines()
    ]
    assert len(lines) == 2 and lines[-1]["total_tokens"] is None
    if fault != "invalid extraction":
        assert lines[-1]["error"]


@pytest.mark.parametrize(
    "usage,expected",
    [
        ({}, "unavailable"),
        ({"prompt_tokens": 7}, "partial"),
        ({"prompt_tokens": 7, "completion_tokens": 3, "total_tokens": 12}, "provider"),
    ],
)
def test_exact_provider_counters(tmp_path, client, usage, expected):
    # Some providers count extra tokens. Preserve the declared total as received.
    def answer(req, seconds):
        return httpx.Response(
            200,
            json={
                "model": "provider-revision",
                "choices": [{"message": {"content": "ok"}}],
                "usage": usage,
            },
        )

    client.send = answer
    trace = TraceRecorder(tmp_path / "trace.jsonl", time.monotonic() + 5, False, client)
    assert trace("food", "exact text") == "ok"
    row = trace.rows[0]
    assert row["input"] == "exact text" and row["model"] == "provider-revision"
    assert row["usage_source"] == expected
    assert row["total_tokens"] == usage.get("total_tokens")
    assert totals([row])["unreported_total_calls"] == int("total_tokens" not in usage)


def test_run_deadline_interrupts_blocking_work():
    with (
        pytest.raises(TimeoutError, match="deadline"),
        time_limit(time.monotonic() + 0.02),
    ):
        time.sleep(1)


def test_concurrent_writer(tmp_path, client):
    (tmp_path / "state").mkdir()
    with (tmp_path / "state/.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        with pytest.raises(RuntimeError, match="already processing"):
            run(FIX / "practice.txt", tmp_path, client)
    assert not client.requests


def test_only_gateway_imports_network_clients():
    net = {
        "httpx",
        "requests",
        "urllib.request",
        "openai",
        "anthropic",
        "litellm",
        "google.genai",
        "aiohttp",
        "http.client",
        "socket",
        "subprocess",
    }
    for path in [ROOT / "main.py", *(ROOT / "engine").glob("*.py")]:
        if path.name == "model_client.py":
            continue
        for node in ast.walk(ast.parse(path.read_text())):
            imports = []
            if isinstance(node, ast.Import):
                imports = [n.name for n in node.names]
            if isinstance(node, ast.ImportFrom) and node.module:
                imports = [node.module] + [
                    node.module + "." + n.name for n in node.names
                ]
            assert not any(
                i == k or i.startswith(k + ".") for i in imports for k in net
            ), path


def test_cli_over_http(tmp_path):
    received = []

    class Provider(BaseHTTPRequestHandler):
        def do_POST(self):
            assert self.path == "/v1/chat/completions"
            data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            received.append(data)
            answer = extraction(data["messages"][0]["content"])
            self.send_response(200)
            self.end_headers()
            self.wfile.write(
                json.dumps(
                    {
                        "model": "loopback-test",
                        "choices": [{"message": {"content": answer}}],
                        "usage": {
                            "prompt_tokens": 5,
                            "completion_tokens": 7,
                            "total_tokens": 12,
                        },
                    }
                ).encode()
            )

    with ThreadingHTTPServer(("127.0.0.1", 0), Provider) as server:
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            env = dict(
                os.environ,
                MODEL_BASE_URL=f"http://127.0.0.1:{server.server_port}/v1",
                MODEL_NAME="test-model",
                MODEL_API_KEY="",
                PLANNER_SESSION_DIR=str(tmp_path),
            )
            input_file = tmp_path / "input/messages.txt"
            input_file.parent.mkdir()
            for name, calls in [
                ("practice", 1),
                ("printing", 2),
                ("food", 3),
                ("food", 3),
            ]:
                input_file.write_bytes((FIX / (name + ".txt")).read_bytes())
                out = subprocess.run(
                    [sys.executable, str(ROOT / "main.py"), "input/messages.txt"],
                    cwd=tmp_path,
                    check=False,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=20,
                )
                assert out.returncode == 0, out.stderr
                assert "HACKATHON PLAN  |  VALID" in out.stdout
                assert out.stdout.rstrip().endswith(
                    f"Session total: {12 * calls} reported tokens (0 calls without a reported total)"
                )
        finally:
            server.shutdown()
            worker.join()
    rows = [
        json.loads(row)
        for row in (tmp_path / "output/trace.jsonl").read_text().splitlines()
    ]
    assert [r["request"] for r in rows] == received
    assert [r["call_number"] for r in rows] == [1, 2, 3]
    assert all(r["model"] == "loopback-test" for r in rows)


def test_live_provider(tmp_path):
    if os.environ.get("RUN_LIVE_MODEL") != "1":
        pytest.skip("Opt in with RUN_LIVE_MODEL=1")
    load_dotenv(ROOT / ".env")
    summary = run(FIX / "practice.txt", tmp_path)
    assert summary["status"] == "valid"
    assert summary["run_usage"]["calls"] >= 1
    assert summary["run_usage"]["incomplete_usage_calls"] == 0
    assert summary["elapsed_seconds_before_publish"] < 120


def test_snapshot_failure_keeps_previous_generation(tmp_path, client, monkeypatch):
    run(FIX / "practice.txt", tmp_path, client)
    summary = (tmp_path / "output/run_summary.json").read_text()
    checkpoint = (tmp_path / "state/engine_state.json").read_text()

    def interrupt(source, target):
        raise OSError("simulated publication failure")

    monkeypatch.setattr("engine.reporting.os.replace", interrupt)
    with pytest.raises(OSError):
        run(FIX / "printing.txt", tmp_path, client)
    assert (tmp_path / "state/engine_state.json").read_text() == checkpoint
    assert (tmp_path / "output/run_summary.json").read_text() == summary
    assert len((tmp_path / "output/trace.jsonl").read_text().splitlines()) == 2
