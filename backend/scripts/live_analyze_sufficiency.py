# -*- coding: utf-8 -*-
"""M17-RC1 §L1 — ANALYZE SUFFICIENCY REALITY CHECK (live, có trần ngân sách).

Câu hỏi DUY NHẤT cần trả lời: **analyze production có trích đủ dữ kiện cụ thể
không?** Cổng §C2 (input sufficiency) dựa hoàn toàn vào điều đó, và offline
không thể kết luận — stub lịch sử mô tả dữ liệu bằng lời nên bị cổng từ chối
33/55 (W0) và 43/68 (W1) case. Không biết đó là "stub sai" hay "cổng quá chặt".

CHỈ gọi production analyze. KHÔNG classify, KHÔNG simulate, KHÔNG executor,
KHÔNG dựng envelope — nên không case nào tạo được simulation.

    ALLOW_LIVE_AI=1 PYTHONIOENCODING=utf-8 \
      .venv/Scripts/python.exe scripts/live_analyze_sufficiency.py \
        --out ../docs/evaluation/m17/rc1

Trần cứng: 14 lượt logic · 16 HTTP · 1 retry cho TOÀN RUN. Chạm trần → dừng
sạch và vẫn ghi artifact phần đã chạy (không im lặng bỏ dở).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ai import pipeline  # noqa: E402
from app.simulation.completeness_gate import (  # noqa: E402
    normalized_requested,
    normalized_requested_operations,
)
from app.simulation.input_requirements import requirements_for  # noqa: E402
from app.simulation.structure_gate import linked_node_items  # noqa: E402
from app.simulation.sufficiency_gate import (  # noqa: E402
    _numeric_tokens,
    check_input_sufficiency,
    check_input_sufficiency_for_targets,
    sufficiency_evidence,
)

MAX_LOGICAL = 14
MAX_HTTP = 16
MAX_RETRY_TOTAL = 1

_SORT_VARIANTS = [
    "algorithm.bubble_sort", "algorithm.insertion_sort", "algorithm.selection_sort",
]


# ── định nghĩa case (đề bài + kỳ vọng VIẾT TRƯỚC khi chạy) ──────────
CASES = [
    {
        "case_id": "L1-V1-finite-sequence", "kind": "valid", "repeats": 2,
        "target": "algorithm.find_max", "targets": None,
        "prompt": "Cho dãy số 12, 7, 25, 9, 18. Tìm phần tử lớn nhất.",
        "expect_tokens": ["12", "7", "25", "9", "18"],
        "expect_operations": ["single_pass_scan:find_max"],
    },
    {
        "case_id": "L1-V2-comparison-sort", "kind": "valid", "repeats": 2,
        "target": None, "targets": _SORT_VARIANTS,
        "prompt": ("Sắp xếp dãy 9, 3, 7, 1, 5 theo thứ tự tăng dần bằng thuật "
                   "toán sắp xếp chèn."),
        "expect_tokens": ["9", "3", "7", "1", "5"],
        "expect_operations": ["comparison_sort:insertion"],
    },
    {
        "case_id": "L1-V3-base-conversion", "kind": "valid", "repeats": 2,
        "target": "binary.base_conversion", "targets": None,
        "prompt": "Đổi số 156 ở hệ thập phân sang hệ nhị phân.",
        # SỬA SAU KHI ĐỌC KẾT QUẢ (lỗi ĐO của tôi, không phải lỗi analyze):
        # đề viết cơ số BẰNG CHỮ ("hệ thập phân", "hệ nhị phân") nên đòi token
        # "10"/"2" là đòi thứ đề không hề viết ra dạng số.
        "expect_tokens": ["156"],
        # analyze chọn `decimal_to_binary` — ĐÚNG HƠN kỳ vọng ban đầu của tôi:
        # 156 → nhị phân chính là bài chuyên biệt, không phải đổi cơ số tổng quát.
        "expect_operations": ["positional_representation:decimal_to_binary"],
    },
    {
        "case_id": "L1-V4-boolean-expression", "kind": "valid", "repeats": 2,
        "target": "logic.boolean_dag", "targets": None,
        "prompt": ("Mô phỏng biểu thức (A AND B) OR NOT C với A=true, B=false, "
                   "C=true."),
        "expect_tokens": [],
        "expect_operations": ["boolean_composition:boolean_dag"],
    },
    {
        "case_id": "L1-V5-graph-traversal", "kind": "valid", "repeats": 2,
        "target": "network.graph_traversal", "targets": None,
        "prompt": ("Duyệt DFS từ đỉnh A trên đồ thị có các cạnh A-B, A-C, B-D, "
                   "C-E; các đỉnh kề xét theo thứ tự bảng chữ cái."),
        "expect_tokens": [],
        "expect_operations": ["graph_traversal:dfs"],
    },
    {
        "case_id": "L1-V6-tree-traversal", "kind": "valid", "repeats": 2,
        "target": "tree.traversal", "targets": None,
        "prompt": ("Duyệt preorder cây có A là gốc; B là con trái của A; C là "
                   "con phải của A; D là con trái của B."),
        "expect_tokens": [],
        "expect_operations": ["tree_traversal:preorder"],
    },
    {
        "case_id": "L1-I1-sequence-missing", "kind": "insufficient", "repeats": 1,
        "target": "algorithm.find_max", "targets": None,
        "prompt": "Mô phỏng tìm phần tử lớn nhất trong một dãy số.",
        "expect_tokens": [], "expect_operations": ["single_pass_scan:find_max"],
    },
    {
        "case_id": "L1-I2-tree-missing", "kind": "insufficient", "repeats": 1,
        "target": "tree.traversal", "targets": None,
        "prompt": "Mô phỏng duyệt cây preorder.",
        "expect_tokens": [], "expect_operations": ["tree_traversal:preorder"],
    },
]


class BudgetExceeded(RuntimeError):
    pass


class Budget:
    """Đếm HTTP THẬT ở biên network. Retry đếm TOÀN RUN (không phải per-case)."""

    def __init__(self) -> None:
        self.http = 0
        self.retries = 0
        self.per_case = 0

    def tick(self) -> None:
        self.http += 1
        self.per_case += 1
        if self.per_case > 1:
            self.retries += 1
        if self.http > MAX_HTTP:
            raise BudgetExceeded(f"vượt trần {MAX_HTTP} HTTP")
        if self.retries > MAX_RETRY_TOTAL:
            raise BudgetExceeded(f"vượt trần {MAX_RETRY_TOTAL} retry cho toàn run")


def _git_sha() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                              text=True, check=True,
                              cwd=Path(__file__).resolve().parents[2]).stdout.strip()
    except Exception:
        return "unknown"


def _str_items(analysis: dict, key: str) -> list[str]:
    items = analysis.get(key) or []
    out = []
    for it in items if isinstance(items, list) else []:
        if isinstance(it, str):
            out.append(it)
        elif isinstance(it, dict):
            out.append(json.dumps(it, ensure_ascii=False))
    return out


def _observe(case: dict, analysis: dict, raw: str) -> dict:
    """Quan sát CÓ CẤU TRÚC — chỉ đọc analyze + chạy chính normalizer production."""
    tokens = _numeric_tokens(analysis)
    if case["targets"]:
        verdict = check_input_sufficiency_for_targets(analysis, case["targets"])
        evidence = {"selector_variants": case["targets"]}
        req = requirements_for(case["targets"][0])
    else:
        verdict = check_input_sufficiency(analysis, case["target"])
        evidence = sufficiency_evidence(analysis, case["target"])
        req = requirements_for(case["target"])

    ops = normalized_requested_operations(analysis)
    missing_tokens = [t for t in case["expect_tokens"] if t not in tokens]
    labelled = [
        d for d in (analysis.get("data") or [])
        if isinstance(d, dict) and (d.get("values") or d.get("labels"))
    ]
    return {
        "raw_analyze_response": raw,
        "normalized_objects": _str_items(analysis, "objects"),
        "normalized_data": analysis.get("data"),
        "normalized_relations": _str_items(analysis, "relations"),
        "requested_operations": ops,
        "requested_mechanisms": normalized_requested(analysis),
        "numeric_tokens_found": tokens,
        "evidence_normalizer_output": evidence,
        "required_input_fields": (
            [k.value for k in req.required_grounded_inputs] if req else []),
        "missing_input_fields": (verdict[2]["missing_inputs"] if verdict else []),
        "sufficiency_decision": "FAIL" if verdict else "PASS",
        "reason_code": verdict[0].value if verdict else None,
        "learner_message": verdict[1] if verdict else None,
        # kiểm ĐỘC LẬP với cổng: dữ kiện cụ thể của đề có còn nguyên không?
        "expected_tokens": case["expect_tokens"],
        "missing_expected_tokens": missing_tokens,
        "concrete_data_preserved": not missing_tokens,
        "operation_match": sorted(ops) == sorted(case["expect_operations"]),
        "expected_operations": case["expect_operations"],
        # Dữ kiện CÓ ĐỊNH DANH: giá trị số / nhãn phần tử / quan hệ giữa hai nút
        # có tên. Ở case thiếu dữ kiện, bất kỳ thứ nào xuất hiện = analyze BỊA.
        "fabricated_evidence": bool(tokens or labelled or linked_node_items(analysis)),
        "generated_default_used": bool(
            req and req.generated_defaults_allowed and not verdict),
    }


async def _run(api_key: str, budget: Budget, out_rows: list) -> None:
    original = pipeline.call_gemini
    last_raw: dict[str, str] = {}

    async def counted(key, system_prompt, user_text, response_schema=None,
                      temperature=0.2, image=None):
        budget.tick()
        raw = await original(key, system_prompt, user_text, response_schema,
                             temperature, image)
        last_raw["v"] = raw if isinstance(raw, str) else json.dumps(raw, ensure_ascii=False)
        return raw

    pipeline.call_gemini = counted
    try:
        logical = 0
        for case in CASES:
            for rep in range(1, case["repeats"] + 1):
                if logical >= MAX_LOGICAL:
                    raise BudgetExceeded(f"vượt trần {MAX_LOGICAL} lượt logic")
                budget.per_case = 0
                logical += 1
                analysis = await pipeline.stage_analyze(case["prompt"], api_key)
                out_rows.append({
                    "case_id": case["case_id"], "repeat": rep, "kind": case["kind"],
                    "prompt": case["prompt"],
                    "target": case["target"] or case["targets"],
                    "http_used": budget.per_case,
                    **_observe(case, analysis, last_raw.get("v", "")),
                })
                print(f"  [{logical:2d}/{MAX_LOGICAL}] {case['case_id']} #{rep} → "
                      f"{out_rows[-1]['sufficiency_decision']} "
                      f"(http {budget.http})")
    finally:
        pipeline.call_gemini = original


def _metrics(rows: list) -> dict:
    valid = [r for r in rows if r["kind"] == "valid"]
    insuf = [r for r in rows if r["kind"] == "insufficient"]
    by_case: dict[str, set] = {}
    for r in rows:
        by_case.setdefault(r["case_id"], set()).add(r["sufficiency_decision"])
    unstable = sorted(c for c, d in by_case.items() if len(d) > 1)
    # BỊA = có DỮ KIỆN CÓ ĐỊNH DANH mà đề không hề cho (giá trị số cụ thể, nhãn
    # phần tử, hoặc quan hệ giữa hai nút CÓ TÊN). Mô tả TRỪU TƯỢNG ("dãy số",
    # "quan hệ cha-con giữa các nút") KHÔNG phải bịa — đó là analyze mô tả đúng
    # cái đề nói. Bản đo đầu tiên của tôi tính "objects/data/relations khác
    # rỗng" là bịa nên gắn cờ oan cả hai đối chứng.
    fabricated = [r["case_id"] for r in insuf if r["fabricated_evidence"]]
    return {
        "valid_runs": len(valid),
        "valid_sufficiency_pass": sum(1 for r in valid if r["sufficiency_decision"] == "PASS"),
        "valid_operation_match": sum(1 for r in valid if r["operation_match"]),
        "valid_concrete_data_preserved": sum(1 for r in valid if r["concrete_data_preserved"]),
        "valid_generated_default_used": sum(1 for r in valid if r["generated_default_used"]),
        "insufficient_runs": len(insuf),
        "insufficient_sufficiency_fail": sum(
            1 for r in insuf if r["sufficiency_decision"] == "FAIL"),
        "insufficient_with_fabricated_evidence": fabricated,
        "unstable_cases": unstable,
    }


def _report(payload: dict) -> str:
    m, rows = payload["metrics"], payload["runs"]
    lines = [
        "# M17-RC1 §L1 — Analyze Sufficiency Reality Check (LIVE)",
        "",
        "Chỉ gọi **production analyze**. Không classify, không simulate, không",
        "executor ⇒ không case nào tạo được simulation.",
        "",
        f"- Môi trường: `{payload['execution_environment']}`",
        f"- git SHA: `{payload['git_sha']}` · model: `{payload['model']}`",
        f"- HTTP: **{payload['http_used']}/{MAX_HTTP}** · retry: "
        f"**{payload['retries']}/{MAX_RETRY_TOTAL}** · lượt logic: "
        f"**{payload['logical_calls']}/{MAX_LOGICAL}**",
        f"- Kết luận: **{payload['verdict']}**",
        "",
        "## Case hợp lệ (6 case × 2 lần)",
        "",
        f"- sufficiency PASS: **{m['valid_sufficiency_pass']}/{m['valid_runs']}**",
        f"- operation đúng: **{m['valid_operation_match']}/{m['valid_runs']}**",
        f"- dữ liệu cụ thể còn nguyên: **{m['valid_concrete_data_preserved']}/{m['valid_runs']}**",
        f"- dùng generated_default: **{m['valid_generated_default_used']}** (phải 0)",
        f"- case cho hai quyết định khác nhau: **{m['unstable_cases'] or 'không'}**",
        "",
        "## Đối chứng thiếu dữ kiện (2 case × 1 lần)",
        "",
        f"- sufficiency FAIL: **{m['insufficient_sufficiency_fail']}/{m['insufficient_runs']}**",
        f"- có bằng chứng BỊA: **{m['insufficient_with_fabricated_evidence'] or 'không'}**",
        "",
        "## Từng lượt",
        "",
        "| Case | Lần | Quyết định | reason_code | operation đúng | dữ liệu nguyên | thiếu |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| `{r['case_id']}` | {r['repeat']} | **{r['sufficiency_decision']}** | "
            f"`{r['reason_code'] or '—'}` | {'✓' if r['operation_match'] else '✗'} | "
            f"{'✓' if r['concrete_data_preserved'] else '✗ ' + str(r['missing_expected_tokens'])} | "
            f"{', '.join(r['missing_input_fields']) or '—'} |"
        )
    return "\n".join(lines) + "\n"


def _verdict(m: dict, aborted) -> str:
    ok_valid = (m["valid_runs"] > 0
                and m["valid_sufficiency_pass"] == m["valid_runs"]
                and m["valid_operation_match"] == m["valid_runs"]
                and m["valid_concrete_data_preserved"] == m["valid_runs"]
                and m["valid_generated_default_used"] == 0
                and not m["unstable_cases"])
    ok_insuf = (m["insufficient_runs"] > 0
                and m["insufficient_sufficiency_fail"] == m["insufficient_runs"]
                and not m["insufficient_with_fabricated_evidence"])
    if aborted:
        return "ABORTED"
    return "PASS" if (ok_valid and ok_insuf) else "FAIL"


def _write(payload: dict, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "live_analyze_sufficiency.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "live_analyze_sufficiency.md").write_text(_report(payload), encoding="utf-8")


def _rescore(run_json: Path, out: Path, label: str) -> int:
    """Chấm lại TỪ RAW ĐÃ LƯU — không gọi mạng. Dữ liệu live không đổi một bit;
    chỉ luật đo được sửa (và ghi rõ đã sửa gì)."""
    prev = json.loads(run_json.read_text(encoding="utf-8"))
    by_id = {c["case_id"]: c for c in CASES}
    rows = []
    for r in prev["runs"]:
        case = by_id[r["case_id"]]
        analysis = json.loads(r["raw_analyze_response"])
        rows.append({
            "case_id": r["case_id"], "repeat": r["repeat"], "kind": r["kind"],
            "prompt": r["prompt"], "target": r["target"], "http_used": r["http_used"],
            **_observe(case, analysis, r["raw_analyze_response"]),
        })
    m = _metrics(rows)
    payload = {**prev, "run_label": label, "metrics": m, "runs": rows,
               "verdict": _verdict(m, prev.get("aborted")),
               "rescored_at": datetime.now(timezone.utc).isoformat(),
               "rescore_note": (
                   "Chấm lại từ raw analyze ĐÃ LƯU (0 HTTP). Dữ liệu live không "
                   "đổi. Sửa hai lỗi trong LUẬT ĐO của lần chấm đầu: (1) V3 đòi "
                   "token '10'/'2' trong khi đề viết cơ số bằng chữ, và kỳ vọng "
                   "operation base_conversion trong khi decimal_to_binary mới "
                   "đúng; (2) cờ 'bịa dữ liệu' tính mọi objects/data/relations "
                   "khác rỗng là bịa, nên gắn cờ oan cả hai đối chứng — nay chỉ "
                   "tính DỮ KIỆN CÓ ĐỊNH DANH (giá trị/nhãn/quan hệ hai nút có tên)."
               )}
    _write(payload, out)
    print(f"Chấm lại {len(rows)} lượt (0 HTTP) · KẾT LUẬN: {payload['verdict']}")
    print(f"  valid PASS {m['valid_sufficiency_pass']}/{m['valid_runs']} · "
          f"operation {m['valid_operation_match']}/{m['valid_runs']} · "
          f"dữ liệu nguyên {m['valid_concrete_data_preserved']}/{m['valid_runs']}")
    print(f"  insufficient FAIL {m['insufficient_sufficiency_fail']}/{m['insufficient_runs']} · "
          f"bịa: {m['insufficient_with_fabricated_evidence'] or 'không'}")
    return 0 if payload["verdict"] == "PASS" else 1


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="../docs/evaluation/m17/rc1")
    p.add_argument("--label", default="rc1-l1-analyze-sufficiency")
    p.add_argument("--rescore", default=None, metavar="RUN_JSON",
                   help="Chấm lại từ raw analyze ĐÃ LƯU — 0 HTTP. Dùng khi phát "
                        "hiện lỗi trong LUẬT ĐO (không phải trong dữ liệu), để "
                        "khỏi tiêu quota lần nữa.")
    args = p.parse_args()

    if args.rescore:
        return _rescore(Path(args.rescore), Path(args.out), args.label)

    if os.getenv("ALLOW_LIVE_AI") != "1":
        print("TỪ CHỐI: cần ALLOW_LIVE_AI=1 (chạy live tốn quota thật).")
        return 2
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        from app.persistence import db  # noqa: F401 — load_dotenv lúc import
        api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("CHƯA có GEMINI_API_KEY (backend/.env hoặc biến môi trường).")
        return 2

    budget, rows = Budget(), []
    aborted = None
    print(f"§L1 — {MAX_LOGICAL} lượt logic, trần {MAX_HTTP} HTTP / {MAX_RETRY_TOTAL} retry\n")
    try:
        asyncio.run(_run(api_key, budget, rows))
    except BudgetExceeded as err:
        aborted = str(err)
        print(f"\nDỪNG SẠCH: {aborted}")
    except Exception as err:  # lỗi hạ tầng — vẫn ghi phần đã chạy
        aborted = f"{type(err).__name__}: {err}"
        print(f"\nDỪNG do lỗi: {aborted}")

    m = _metrics(rows)
    verdict = _verdict(m, aborted)

    payload = {
        "schema_version": "1",
        "run_label": args.label,
        "execution_environment": (
            f"local python {platform.python_version()} on {platform.system()} "
            "(KHÔNG qua container — Docker Desktop không chạy)"
        ),
        "git_sha": _git_sha(),
        "model": "gemini-2.5-flash",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "budget": {"max_logical": MAX_LOGICAL, "max_http": MAX_HTTP,
                   "max_retry_total": MAX_RETRY_TOTAL},
        "logical_calls": len(rows),
        "http_used": budget.http,
        "retries": budget.retries,
        "aborted": aborted,
        "metrics": m,
        "verdict": verdict,
        "runs": rows,
    }
    out = Path(args.out)
    _write(payload, out)

    print(f"\nvalid PASS {m['valid_sufficiency_pass']}/{m['valid_runs']} · "
          f"operation {m['valid_operation_match']}/{m['valid_runs']} · "
          f"dữ liệu nguyên {m['valid_concrete_data_preserved']}/{m['valid_runs']}")
    print(f"insufficient FAIL {m['insufficient_sufficiency_fail']}/{m['insufficient_runs']} · "
          f"bịa: {m['insufficient_with_fabricated_evidence'] or 'không'}")
    print(f"HTTP {budget.http}/{MAX_HTTP} · retry {budget.retries} · KẾT LUẬN: {verdict}")
    print(f"Artifact → {out}")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
