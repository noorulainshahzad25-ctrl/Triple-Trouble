"""The sole network boundary. One POST, no redirects or automatic retries."""

import math
import os
import ssl
import time
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
        max_retries = 3
        backoff_base = 1.0

        for attempt in range(max_retries + 1):
            cur_remaining = remaining
            if cur_remaining <= 0:
                raise TimeoutError("Deadline exceeded before dispatch.")

            try:
                # Use a fresh Client with configured SSL and connection pooling
                with httpx.Client(
                    timeout=min(self.timeout, cur_remaining),
                    follow_redirects=False,
                    verify=True,
                    http2=False,
                ) as client:
                    response = client.post(
                        self.base_url + "/chat/completions",
                        json=request,
                        headers=headers,
                    )
                # If server returns transient 503 or 429, retry with backoff
                if response.status_code in (429, 502, 503, 504) and attempt < max_retries:
                    sleep_time = min(backoff_base * (2**attempt), cur_remaining)
                    if sleep_time > 0 and remaining - sleep_time > 0:
                        time.sleep(sleep_time)
                        continue
                return response
            except (
                httpx.ConnectError,
                httpx.ReadError,
                httpx.WriteError,
                httpx.NetworkError,
                httpx.TimeoutException,
                ssl.SSLError,
            ) as exc:
                if attempt >= max_retries:
                    raise
                # Exponential backoff: 1s, 2s, 4s...
                sleep_time = min(backoff_base * (2**attempt), cur_remaining)
                if sleep_time <= 0 or remaining - sleep_time <= 0:
                    raise
                time.sleep(sleep_time)
