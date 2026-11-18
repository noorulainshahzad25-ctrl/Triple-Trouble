import json
from pathlib import Path

import httpx
import pytest

from engine.model_client import ModelClient
from main import run

FIX = Path(__file__).parent / "fixtures"


def extraction(prompt):
    payload = json.loads(prompt.splitlines()[-1])
    examples = json.loads((FIX / "mock_extractions.json").read_text())
    return json.dumps(
        {
            "messages": [
                dict(examples[row["text"].strip()], id=row["id"])
                for row in payload["input"]
            ]
        }
    )


class FixtureClient(ModelClient):
    def __init__(self):
        super().__init__("http://localhost", "test-request", "", 1, 8192, 0)
        self.requests = []

    def send(self, request, remaining):
        self.requests.append(request)
        output = extraction(request["messages"][0]["content"])
        return httpx.Response(
            200,
            json={
                "model": "fixture-model",
                "choices": [{"message": {"content": output}, "finish_reason": "stop"}],
                "usage": {
                    "prompt_tokens": 41,
                    "completion_tokens": 17,
                    "total_tokens": 58,
                },
            },
        )


@pytest.fixture
def client():
    return FixtureClient()


@pytest.fixture
def execute(tmp_path, client):
    def process(name):
        summary = run(FIX / (name + ".txt"), tmp_path, client)

        def read(file):
            return json.loads((tmp_path / "output" / file).read_text())

        return summary, read("plan.json"), read("rejections.json")

    return process
