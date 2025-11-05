from __future__ import annotations
import time
import requests
from typing import Any, Dict, Tuple
print("LOADED HTTP.PY from", __file__)

class HttpClient:
    def __init__(self, default_timeout: int = 15):
        self.default_timeout = default_timeout
        self.session = requests.Session()

    def send(self, method: str, url: str, *, headers: Dict[str, str] | None = None,
             params: Dict[str, Any] | None = None, json_body: Any | None = None,
             timeout_sec: int | None = None) -> Tuple[requests.Response, float]:
        timeout = timeout_sec or self.default_timeout
        start = time.perf_counter()
        resp = self.session.request(
            method=method.upper(),
            url=url,
            headers=headers,
            params=params,
            json=json_body,
            timeout=timeout
        )
        elapsed = (time.perf_counter() - start) * 1000.0  # ms
        return resp, elapsed
