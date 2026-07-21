# -*- coding: utf-8 -*-
"""M17-Lite W2A — targeted LIVE SMOKE (user-approved ≤6 case / ≤20 HTTP).

Chạy 6 prompt đã user duyệt qua production `run_pipeline` THẬT (gemini-2.5-flash)
với AttemptObserver + ApiBudget (trần cứng 20). Ghi artifact máy-đọc + report.

Lưu ý: thứ tự duyệt AUTHORITATIVE do ENGINE FE tính (không có trong envelope
backend) — đã chứng minh offline bằng oracle đệ quy độc lập (tree.test.tsx 39
test). Live smoke kiểm: route + variant + spec hợp lệ + KHÔNG order trong config
+ cross-family + insufficient. OPT-IN: ALLOW_LIVE_AI=1.
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

OUT = Path(__file__).resolve().parents[2] / "docs" / "evaluation" / "m17" / "wave2a" / "live_smoke.json"
MAX_HTTP = 20
_TREE_ALLOWED = {"specVersion", "variant", "rootId", "nodes", "notes"}
_FORBIDDEN_TREE = {"visitedOrder", "steps", "result", "order", "timeline"}

CASES = [
    {
        "id": "w2a-preorder-vi",
        "prompt": "Mô phỏng duyệt cây nhị phân theo thứ tự thăm gốc trước, sau đó duyệt toàn bộ "
                  "cây con trái rồi cây con phải. Cây có A là gốc; A có con trái B, con phải C; "
                  "B có hai con D và E.",
        "expect_status": "ok", "expect_route": "tree.traversal",
        "expect_variant": "preorder", "expect_family": "tree_traversal",
    },
    {
        "id": "w2a-inorder-incomplete",
        "prompt": "Duyệt trung thứ tự cây có A là gốc, B là con trái và C là con phải; B chỉ có con trái D.",
        "expect_status": "ok", "expect_route": "tree.traversal",
        "expect_variant": "inorder", "expect_family": "tree_traversal",
    },
    {
        "id": "w2a-postorder-en",
        "prompt": "Simulate postorder traversal for a binary tree where A is the root, A has left "
                  "child B, B has left child C, and C has left child D.",
        "expect_status": "ok", "expect_route": "tree.traversal",
        "expect_variant": "postorder", "expect_family": "tree_traversal",
    },
    {
        "id": "w2a-levelorder-vi",
        "prompt": "Mô phỏng duyệt cây theo từng tầng từ trên xuống, trái sang phải. Cây có A là gốc; "
                  "A có B và C; B có D và E; C có F và G.",
        "expect_status": "ok", "expect_route": "tree.traversal",
        "expect_variant": "level_order", "expect_family": "tree_traversal",
    },
    {
        "id": "w2a-crossfamily-graph-dfs",
        "prompt": "Duyệt đồ thị theo chiều sâu từ đỉnh A, với các cạnh A-B, A-C, B-D, C-E; "
                  "thứ tự láng giềng theo bảng chữ cái.",
        "expect_status": "ok", "expect_route": "network.graph_traversal",
        "expect_variant": "dfs", "expect_family": "graph_traversal",
    },
    {
        "id": "w2a-insufficient",
        "prompt": "Mô phỏng duyệt cây preorder.",
        "expect_status": "unsupported", "expect_route": None,
        "expect_variant": None, "expect_family": None,
    },
]


def _families(sim_id):
    if not sim_id or sim_id not in CATALOG:
        return []
    return sorted({m.family_id.value for m in CATALOG[sim_id].family_memberships})


def _git_commit():
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                              check=True, cwd=Path(__file__).resolve().parents[2]).stdout.strip()
    except Exception:
        return "unknown"


def _clean_learner(text):
    """Thông điệp learner KHÔNG lộ token kỹ thuật/JSON path/schema."""
    if not isinstance(text, str):
        return True
    import re
    return re.search(r"[a-z]+_[a-z_]+|\$\.|\{|\}|Traceback|schema", text) is None


async def _run_case(case, api_key, budget):
    obs = AttemptObserver()
    before = budget.http_requests
    envelope, pipeline_error = None, None
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
    variant = config.get("variant") if isinstance(config, dict) else None

    checks = {}
    if case["expect_status"] == "ok":
        checks["status_ok"] = status == "ok"
        checks["route_match"] = route == case["expect_route"]
        checks["family_match"] = case["expect_family"] in _families(route)
        checks["variant_match"] = variant == case["expect_variant"]
        checks["concrete_executor"] = route in CATALOG
        checks["no_pipeline_error"] = pipeline_error is None
        if case["expect_route"] == "tree.traversal":
            keys = set(config.keys()) if isinstance(config, dict) else set()
            # thứ tự duyệt KHÔNG nằm trong LLM spec (engine FE tính)
            checks["order_not_in_spec"] = bool(keys) and keys.issubset(_TREE_ALLOWED)
            checks["no_forbidden_order_field"] = not (keys & _FORBIDDEN_TREE)
        if case["id"] == "w2a-crossfamily-graph-dfs":
            checks["not_tree"] = route != "tree.traversal"
    else:  # insufficient → unsupported
        checks["status_unsupported"] = status == "unsupported"
        checks["no_route"] = route is None
        checks["no_generic_leak"] = route != "generic.rule_scene"
        checks["not_fabricated_tree"] = route != "tree.traversal"  # KHÔNG tự dựng cây
        checks["learner_msg_clean"] = _clean_learner(
            (envelope or {}).get("learner_reason") or (envelope or {}).get("reason")
        )

    return {
        "case_id": case["id"], "prompt": case["prompt"],
        "expect": {k: case[k] for k in ("expect_status", "expect_route", "expect_variant", "expect_family")},
        "actual": {
            "status": status, "initial_route": classify.get("simulation_id") if classify else None,
            "final_route": route, "family": _families(route), "variant": variant,
            "config_keys": sorted(config.keys()) if isinstance(config, dict) else None,
            "failure_category": (envelope or {}).get("failure_category") if isinstance(envelope, dict) else None,
            "reclassify_attempted": obs.reclassify_attempted() is not None,
            "simulate_attempts": len(obs.simulate_attempts()),
            "pipeline_error": pipeline_error, "http_calls": http_delta,
        },
        "checks": checks, "passed": all(checks.values()),
    }


async def _main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("CHƯA có GEMINI_API_KEY."); return 1
    budget = ApiBudget(max_api_calls=MAX_HTTP)
    gemini.set_budget(budget)
    results, aborted = [], None
    try:
        for case in CASES:
            try:
                results.append(await _run_case(case, api_key, budget))
            except BudgetExceeded as err:
                aborted = str(err); break
    finally:
        gemini.set_budget(None)

    payload = {
        "schema_version": "1", "run_label": "wave2a-live-smoke",
        "run_meta": {"git_commit": _git_commit(), "generated_at": datetime.now(timezone.utc).isoformat(),
                     "model": gemini.MODEL, "budget_cap_http": MAX_HTTP},
        "budget_final": {"http_requests": budget.http_requests, "logical_calls": budget.logical_calls,
                         "retry_requests": budget.retry_requests, "transient_hits": budget.transient_hits},
        "aborted_reason": aborted, "cases": results,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"\n=== M17 W2A LIVE SMOKE ({gemini.MODEL}) ===")
    for r in results:
        a = r["actual"]
        print(f"[{'PASS' if r['passed'] else 'FAIL'}] {r['case_id']}: status={a['status']} "
              f"route={a['final_route']} variant={a['variant']} http={a['http_calls']} "
              f"reclass={a['reclassify_attempted']} sim={a['simulate_attempts']}")
        if not r["passed"]:
            print(f"        checks: {r['checks']}")
    b = payload["budget_final"]
    n_pass = sum(1 for r in results if r["passed"])
    print(f"\nTổng: {n_pass}/{len(results)} PASS · HTTP {b['http_requests']}/{MAX_HTTP} · "
          f"retry {b['retry_requests']} · transient {b['transient_hits']} · aborted={aborted}")
    print(f"Artifact: {OUT}")
    return 0 if (n_pass == len(CASES) and aborted is None) else 2


def main():
    if os.getenv("ALLOW_LIVE_AI") != "1":
        print("TỪ CHỐI: cần ALLOW_LIVE_AI=1."); return 1
    return asyncio.run(_main())


if __name__ == "__main__":
    sys.exit(main())
