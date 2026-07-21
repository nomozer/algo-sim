# -*- coding: utf-8 -*-
"""M17-Lite W1 — targeted LIVE SMOKE (user-approved budget ≤6 case / ≤20 HTTP).

Chạy 6 prompt ĐẠI DIỆN đã user duyệt qua production `run_pipeline` THẬT (Gemini
gemini-2.5-flash) với `AttemptObserver` thụ động + `ApiBudget` (đếm HTTP thật,
trần cứng 20). Ghi artifact máy-đọc + in report. KHÔNG đụng dataset/frozen M16.

OPT-IN CỨNG: cần ALLOW_LIVE_AI=1 + GEMINI_API_KEY (đọc backend/.env).
    ALLOW_LIVE_AI=1 python scripts/live_smoke_m17_wave1.py

Sáu case (4 supported + 2 unsupported) — prompt diễn đạt CƠ CHẾ tự nhiên, không
gọi thẳng tên simulation_id; kỳ vọng lấy từ scope Wave 1 (KHÔNG chỉnh để làm
pass).
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ai import gemini  # noqa: E402
from app.ai.gemini import ApiBudget, BudgetExceeded  # noqa: E402
from app.ai import pipeline  # noqa: E402
from app.evaluation.observer import AttemptObserver  # noqa: E402
from app.simulation.catalog import CATALOG  # noqa: E402

OUT = Path(__file__).resolve().parents[2] / "docs" / "evaluation" / "m17" / "wave1" / "live_smoke.json"
MAX_HTTP = 20

# Config config-key hợp lệ của base_conversion (chống LLM nhét result/steps).
_BASECONV_ALLOWED = {"sourceBase", "targetBase", "inputValue", "strategy", "notes"}


# case_id, prompt, expected {status, route|None, family|None, checks}
CASES = [
    {
        "id": "w1-selection-sort",
        "prompt": "Sắp xếp dãy [7, 3, 9, 1] bằng cách mỗi lượt chọn phần tử nhỏ nhất còn "
                  "lại và đưa nó về đầu phần chưa sắp xếp.",
        "expect_status": "ok",
        "expect_route": "algorithm.selection_sort",
        "expect_family": "comparison_sort",
        "note": "KHÔNG được route thành bubble/insertion.",
    },
    {
        "id": "w1-base-conversion-hex",
        "prompt": "Chuyển số 3A hệ 16 sang hệ 2 và mô phỏng từng bước.",
        "expect_status": "ok",
        "expect_route": "binary.base_conversion",
        "expect_family": "positional_representation",
        "note": "Config KHÔNG chứa result/steps (đáp số do engine FE tính, không phải LLM).",
    },
    {
        "id": "w1-boolean-dag",
        "prompt": "Mô phỏng mạch F = (A AND B) XOR (NOT C), với A=1, B=0, C=1 và tạo "
                  "bảng chân trị.",
        "expect_status": "ok",
        "expect_route": "logic.boolean_dag",
        "expect_family": "boolean_composition",
        "note": "KHÔNG được hạ thành logic.and_gate đơn.",
    },
    {
        "id": "w1-graph-traversal-dfs",
        "prompt": "Duyệt đồ thị theo chiều sâu từ A, với các cạnh A-B, A-C, B-D, C-E; "
                  "thứ tự láng giềng theo bảng chữ cái.",
        "expect_status": "ok",
        "expect_route": "network.graph_traversal",
        "expect_family": "graph_traversal",
        "note": "KHÔNG được route về network.packet_routing; variant phải là dfs.",
    },
    {
        "id": "w1-nm-quicksort",
        "prompt": "Sắp xếp [8, 3, 5, 1] bằng Quick Sort, mô phỏng quá trình partition đệ quy.",
        "expect_status": "unsupported",
        "expect_route": None,
        "expect_family": None,
        "note": "Quick Sort (partition) vẫn intentional gap → capability_gap trung thực.",
    },
    {
        "id": "w1-base-out-of-range",
        "prompt": "Chuyển số 243 từ hệ 5 sang hệ 10 và mô phỏng từng bước.",
        "expect_status": "unsupported",
        "expect_route": None,
        "expect_family": None,
        "note": "Cơ số 5 ngoài {2,8,10,16} → unsupported trung thực (không false-positive sim).",
    },
]


def _families(sim_id: str | None) -> list[str]:
    if not sim_id or sim_id not in CATALOG:
        return []
    return sorted({m.family_id.value for m in CATALOG[sim_id].family_memberships})


def _git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True,
            cwd=Path(__file__).resolve().parents[2],
        ).stdout.strip()
    except Exception:
        return "unknown"


async def _run_case(case: dict, api_key: str, budget: ApiBudget) -> dict:
    obs = AttemptObserver()
    before = budget.http_requests
    envelope: dict | None = None
    pipeline_error: str | None = None
    try:
        envelope = await pipeline.run_pipeline(case["prompt"], api_key, pattern_store=None, observer=obs)
    except BudgetExceeded:
        raise
    except Exception as err:
        pipeline_error = str(err)
    http_delta = budget.http_requests - before

    classify = obs.classify()
    status = envelope.get("status") if isinstance(envelope, dict) else None
    route = envelope.get("simulation_id") if isinstance(envelope, dict) else None
    config = envelope.get("config") if isinstance(envelope, dict) else None
    gates = [dict(g) for g in obs.gates()]

    # ── chấm theo acceptance ──
    checks: dict[str, bool] = {}
    if case["expect_status"] == "ok":
        checks["status_ok"] = status == "ok"
        checks["route_match"] = route == case["expect_route"]
        checks["family_match"] = case["expect_family"] in _families(route)
        checks["concrete_executor"] = route in CATALOG  # id concrete thật, không token
        checks["no_pipeline_error"] = pipeline_error is None
        if case["id"] == "w1-base-conversion-hex":
            # authoritative result KHÔNG do LLM: config chỉ mang input, không result/steps
            keys = set(config.keys()) if isinstance(config, dict) else set()
            checks["config_no_llm_result"] = bool(keys) and keys.issubset(_BASECONV_ALLOWED)
        if case["id"] == "w1-graph-traversal-dfs":
            checks["variant_dfs"] = isinstance(config, dict) and config.get("variant") == "dfs"
            checks["not_packet_routing"] = route != "network.packet_routing"
    else:  # unsupported
        checks["status_unsupported"] = status == "unsupported"
        checks["capability_gap"] = (
            isinstance(envelope, dict) and envelope.get("failure_category") == "capability_gap"
        )
        checks["no_generic_leak"] = route != "generic.rule_scene"
        checks["no_simulation"] = route is None

    passed = all(checks.values())
    return {
        "case_id": case["id"],
        "prompt": case["prompt"],
        "expect": {k: case[k] for k in ("expect_status", "expect_route", "expect_family")},
        "note": case["note"],
        "actual": {
            "status": status,
            "initial_route": classify.get("simulation_id") if classify else None,
            "final_route": route,
            "family": _families(route),
            "failure_category": envelope.get("failure_category") if isinstance(envelope, dict) else None,
            "error_code": envelope.get("error_code") if isinstance(envelope, dict) else None,
            "config_keys": sorted(config.keys()) if isinstance(config, dict) else None,
            "reclassify_attempted": obs.reclassify_attempted() is not None,
            "simulate_attempts": len(obs.simulate_attempts()),
            "gates_fired": [g.get("gate") for g in gates if g.get("fired")],
            "pipeline_error": pipeline_error,
            "http_calls": http_delta,
        },
        "checks": checks,
        "passed": passed,
    }


async def _main() -> int:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("CHƯA có GEMINI_API_KEY.")
        return 1
    budget = ApiBudget(max_api_calls=MAX_HTTP)
    gemini.set_budget(budget)
    results: list[dict] = []
    aborted = None
    try:
        for case in CASES:
            try:
                results.append(await _run_case(case, api_key, budget))
            except BudgetExceeded as err:
                aborted = str(err)
                break
    finally:
        gemini.set_budget(None)

    payload = {
        "schema_version": "1",
        "run_label": "wave1-live-smoke",
        "run_meta": {
            "git_commit": _git_commit(),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "model": gemini.MODEL,
            "budget_cap_http": MAX_HTTP,
        },
        "budget_final": {
            "http_requests": budget.http_requests,
            "logical_calls": budget.logical_calls,
            "retry_requests": budget.retry_requests,
            "transient_hits": budget.transient_hits,
        },
        "aborted_reason": aborted,
        "cases": results,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # ── report ──
    print(f"\n=== M17 W1 LIVE SMOKE ({gemini.MODEL}) ===")
    for r in results:
        flag = "PASS" if r["passed"] else "FAIL"
        a = r["actual"]
        print(f"[{flag}] {r['case_id']}: status={a['status']} route={a['final_route']} "
              f"http={a['http_calls']} reclass={a['reclassify_attempted']} "
              f"sim_attempts={a['simulate_attempts']} err={a['error_code']}")
        if not r["passed"]:
            print(f"        checks: {r['checks']}")
    b = payload["budget_final"]
    n_pass = sum(1 for r in results if r["passed"])
    print(f"\nTổng: {n_pass}/{len(results)} PASS · HTTP {b['http_requests']}/{MAX_HTTP} · "
          f"retry {b['retry_requests']} · transient {b['transient_hits']} · "
          f"aborted={aborted}")
    print(f"Artifact: {OUT}")
    return 0 if (n_pass == len(CASES) and aborted is None) else 2


def main() -> int:
    if os.getenv("ALLOW_LIVE_AI") != "1":
        print("TỪ CHỐI: live smoke gọi Gemini THẬT. Chạy với ALLOW_LIVE_AI=1.")
        return 1
    return asyncio.run(_main())


if __name__ == "__main__":
    sys.exit(main())
