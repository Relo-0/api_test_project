from __future__ import annotations 

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))

import os, json
from typing import Any, Dict, List
from jsonschema import validate, ValidationError
from utils.http_client import HttpClient
from utils.reporter import ExcelReporter

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config" / "endpoints.json"
REPORT_PATH = BASE_DIR / "reports" / "api_test_result.xlsx"

def load_endpoints(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def run_case(name: str, cfg: Dict[str, Any], http: HttpClient) -> Dict[str, Any]:
    method = cfg.get("method", "GET").upper()
    url = cfg["url"]
    expected_status = int(cfg.get("expected_status", 200))
    timeout_sec = int(cfg.get("timeout_sec", 15))
    headers = cfg.get("headers")
    params = cfg.get("params")
    body = cfg.get("body")
    schema = cfg.get("schema")

    row = {
        "case_name": name,
        "method": method,
        "url": url,
        "expected_status": expected_status,
        "actual_status": None,
        "pass": False,
        "latency_ms": 0.0,
        "error": ""
    }

    try:
        resp, elapsed_ms = http.send(
            method=method, url=url, headers=headers, params=params,
            json_body=body, timeout_sec=timeout_sec
        )
        row["latency_ms"] = elapsed_ms
        row["actual_status"] = resp.status_code

        # 狀態碼檢查
        if resp.status_code != expected_status:
            row["error"] = f"status_mismatch: got {resp.status_code}"
            return row

        # JSON Schema 檢查（選填）
        if schema:
            try:
                data = resp.json()
            except ValueError:
                row["error"] = "non_json_response"
                return row

            try:
                validate(instance=data, schema=schema)
            except ValidationError as ve:
                row["error"] = f"schema_error: {ve.message}"
                return row

        # 全通過
        row["pass"] = True
        return row

    except Exception as e:
        row["error"] = f"exception: {type(e).__name__}: {e}"
        return row

def main() -> None:
    endpoints = load_endpoints(CONFIG_PATH)
    http = HttpClient()
    results: List[Dict[str, Any]] = []

    print("=== API 測試開始 ===")
    for name, cfg in endpoints.items():
        r = run_case(name, cfg, http)
        results.append(r)
        status = "PASS" if r["pass"] else "FAIL"
        print(f"[{status}] {name} {r['method']} {r['url']} "
              f"→ {r['actual_status']} ({r['latency_ms']:.1f} ms)"
              + ("" if r["pass"] else f"  |  {r['error']}"))

    ExcelReporter(REPORT_PATH).write(results)
    total = len(results)
    passed = sum(1 for r in results if r["pass"])
    print("=== 測試完成 ===")
    print(f"通過 {passed}/{total}  項，報告：{REPORT_PATH}")

if __name__ == "__main__":
    main()
