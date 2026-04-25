import argparse
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CASES_PATH = ROOT_DIR / "eval" / "eval_cases.jsonl"
DEFAULT_REPORT_PATH = ROOT_DIR / "eval" / "eval_report.md"
DEFAULT_BACKEND_URL = "http://127.0.0.1:8000"
REQUEST_TIMEOUT = 120


def load_cases(cases_path: Path = DEFAULT_CASES_PATH) -> List[Dict[str, Any]]:
    cases: List[Dict[str, Any]] = []
    with cases_path.open("r", encoding="utf-8") as file:
        for line_no, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                # JSONL 逐行解析，出错时带上行号方便定位坏用例。
                cases.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at line {line_no}: {exc}") from exc
    return cases


def _normalize_backend_url(backend_url: str) -> str:
    return backend_url.rstrip("/")


def _extract_error(response_data: Optional[Dict[str, Any]], request_error: Optional[str]) -> Optional[str]:
    # 同时兼容接口业务 error、FastAPI detail 和 requests 层错误。
    if request_error:
        return request_error
    if not response_data:
        return None
    error = response_data.get("error")
    if error:
        return str(error)
    detail = response_data.get("detail")
    if detail:
        return str(detail)
    return None


def _field_exists(data: Optional[Dict[str, Any]], field: str, error: Optional[str]) -> bool:
    # error 是 eval 期望字段，不一定存在于成功响应体里。
    if field == "error":
        return bool(error)
    if not data or field not in data:
        return False
    value = data[field]
    return value is not None and value != "" and value != []


def missing_outputs(data: Optional[Dict[str, Any]], expected_outputs: List[str], error: Optional[str]) -> List[str]:
    return [field for field in expected_outputs if not _field_exists(data, field, error)]


def call_case(case: Dict[str, Any], backend_url: str) -> Dict[str, Any]:
    backend_url = _normalize_backend_url(backend_url)
    input_type = case["input_type"]

    if input_type == "text":
        endpoint = f"{backend_url}/digest/text"
        payload = {"text": case["input"]}
    elif input_type == "video_url":
        endpoint = f"{backend_url}/digest/video-url"
        payload = {"url": case["input"]}
    else:
        raise ValueError(f"Unsupported input_type: {input_type}")

    started_at = time.perf_counter()
    response_data: Optional[Dict[str, Any]] = None
    request_error: Optional[str] = None
    status_code: Optional[int] = None

    try:
        response = requests.post(endpoint, json=payload, timeout=REQUEST_TIMEOUT)
        status_code = response.status_code
        try:
            response_data = response.json()
        except ValueError:
            request_error = "Response is not valid JSON."
        if status_code >= 400 and not request_error:
            request_error = f"HTTP {status_code}"
    except requests.exceptions.RequestException as exc:
        request_error = str(exc)

    latency_ms = int((time.perf_counter() - started_at) * 1000)
    error = _extract_error(response_data, request_error)
    expected_outputs = list(case.get("expected_outputs", []))
    missing = missing_outputs(response_data, expected_outputs, error)
    success = request_error is None and not missing

    # 第一版只做链路可用性和字段完整性检查，不做语义质量评分。
    return {
        "case_id": case.get("id", ""),
        "input_type": input_type,
        "expected_route": case.get("expected_route", ""),
        "success": success,
        "missing_outputs": missing,
        "trace_id": response_data.get("trace_id") if response_data else None,
        "latency_ms": latency_ms,
        "error": error,
        "status_code": status_code,
    }


def summarize_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_cases = len(results)
    passed_cases = sum(1 for item in results if item["success"])
    failed_cases = total_cases - passed_cases
    average_latency_ms = (
        round(sum(item["latency_ms"] for item in results) / total_cases, 2)
        if total_cases
        else 0
    )
    success_rate = round((passed_cases / total_cases) * 100, 2) if total_cases else 0

    return {
        "total_cases": total_cases,
        "passed_cases": passed_cases,
        "failed_cases": failed_cases,
        "success_rate": success_rate,
        "average_latency_ms": average_latency_ms,
    }


def _escape_table(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def build_report(results: List[Dict[str, Any]], summary: Dict[str, Any]) -> str:
    # 直接生成 Markdown，方便 CI 或人工复盘时打开同一份报告。
    lines = [
        "# Eval Report",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Total Cases | {summary['total_cases']} |",
        f"| Passed Cases | {summary['passed_cases']} |",
        f"| Failed Cases | {summary['failed_cases']} |",
        f"| Success Rate | {summary['success_rate']}% |",
        f"| Average Latency | {summary['average_latency_ms']} ms |",
        "",
        "## Case Results",
        "",
        "| Case ID | Input Type | Expected Route | Success | Missing Outputs | Trace ID | Latency | Error |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for item in results:
        missing = ", ".join(item["missing_outputs"])
        lines.append(
            "| "
            f"{_escape_table(item['case_id'])} | "
            f"{_escape_table(item['input_type'])} | "
            f"{_escape_table(item['expected_route'])} | "
            f"{'yes' if item['success'] else 'no'} | "
            f"{_escape_table(missing)} | "
            f"{_escape_table(item.get('trace_id'))} | "
            f"{item['latency_ms']} ms | "
            f"{_escape_table(item.get('error'))} |"
        )

    lines.extend(
        [
            "",
            "## Findings",
            "",
            "- 第一版 eval 只检查接口可用性、字段完整性、trace_id、latency 和 error。",
            "- 语义质量需要人工复盘或后续接入更专业的评测工具。",
        ]
    )
    return "\n".join(lines) + "\n"


def write_report(results: List[Dict[str, Any]], report_path: Path = DEFAULT_REPORT_PATH) -> Path:
    summary = summarize_results(results)
    report = build_report(results, summary)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    return report_path


def run_eval(backend_url: str = DEFAULT_BACKEND_URL, cases_path: Path = DEFAULT_CASES_PATH, report_path: Path = DEFAULT_REPORT_PATH) -> Dict[str, Any]:
    cases = load_cases(cases_path)
    results = [call_case(case, backend_url) for case in cases]
    write_report(results, report_path)
    summary = summarize_results(results)
    return {"summary": summary, "results": results, "report_path": str(report_path)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run VideoMind Agent eval cases.")
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--cases-path", default=str(DEFAULT_CASES_PATH))
    parser.add_argument("--report-path", default=str(DEFAULT_REPORT_PATH))
    args = parser.parse_args()

    result = run_eval(
        backend_url=args.backend_url,
        cases_path=Path(args.cases_path),
        report_path=Path(args.report_path),
    )
    summary = result["summary"]
    print(
        "Eval finished: "
        f"{summary['passed_cases']}/{summary['total_cases']} passed, "
        f"success_rate={summary['success_rate']}%, "
        f"report={result['report_path']}"
    )


if __name__ == "__main__":
    main()
