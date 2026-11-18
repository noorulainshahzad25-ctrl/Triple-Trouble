"""The sole network boundary. One POST, no redirects or automatic retries."""

import math
import os
from dataclasses import dataclass, field
from urllib.parse import urlsplit

import httpx


@dataclass
class ModelClient:
    base_url: str
    model: str
    key: str = field(repr=False)
    timeout: float
    ceiling: int
    temperature: float | None

    @classmethod
    def configured(cls):
        base = os.getenv("MODEL_BASE_URL", "").strip().rstrip("/")
        model = os.getenv("MODEL_NAME", "").strip()
        url = urlsplit(base)
        if not model or url.scheme not in ("http", "https") or not url.hostname:
            raise ValueError(
                "Set MODEL_NAME and an OpenAI-compatible MODEL_BASE_URL in .env."
            )
        if url.username or url.password or url.query or url.fragment:
            raise ValueError(
                "MODEL_BASE_URL must be a service URL without embedded credentials or query."
            )
        timeout = float(os.getenv("MODEL_TIMEOUT_SECONDS", "45"))
        ceiling = int(os.getenv("MODEL_MAX_TOKENS", "8192"))
        temp = os.getenv("MODEL_TEMPERATURE", "0").strip()
        temperature = float(temp) if temp else None
        if not math.isfinite(timeout) or timeout <= 0 or ceiling < 1:
            raise ValueError("Model timeout and token ceiling must be positive.")
        if temperature is not None and not 0 <= temperature <= 2:
            raise ValueError("MODEL_TEMPERATURE must be blank or between 0 and 2.")
        return cls(
            base, model, os.getenv("MODEL_API_KEY", ""), timeout, ceiling, temperature
        )

    def request(self, prompt):
        body = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.ceiling,
        }
        if self.temperature is not None:
            body["temperature"] = self.temperature
        return body

    def send(self, request, remaining):
        headers = {"Authorization": "Bearer " + self.key} if self.key else {}
        response = httpx.post(
            self.base_url + "/chat/completions",
            json=request,
            headers=headers,
            timeout=min(self.timeout, remaining),
            follow_redirects=False,
        )
        return response
