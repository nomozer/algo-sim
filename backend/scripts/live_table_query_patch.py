# -*- coding: utf-8 -*-
"""M17 W2B-PATCH LIVE — kiểm chứng lại 3 finding đã vá, trên LLM THẬT.

KHÔNG phải routing smoke. Bốn case, ngân sách chặt, kỳ vọng KHÓA TRƯỚC khi thấy
bất kỳ output live nào:

    P1 = L3  ô trống viết bằng chữ  → AVG 8.25 trên 4 ô (không hoá 0)
    P2 = L4  pipeline NĂM tầng      → đủ 5 tầng, 3 dòng, AVG 8.5
    P3 = L5  không có bảng          → insufficient_specification (KHÔNG "tách")
    P4 = L1  đối chứng không hồi quy → lọc + chiếu, grounding perfect

Bất biến tôn trọng: production `run_pipeline` (invariant #22); oracle =
`run_table_query` (chính engine tất định). KHÔNG sửa production code trong run,
KHÔNG đổi prompt/expected/tolerance sau khi thấy kết quả.

    # KHÓA kỳ vọng bằng oracle + tự kiểm máy audit, KHÔNG gọi API:
    python scripts/live_table_query_patch.py --lock
    python scripts/live_table_query_patch.py --selftest

    # CHẠY THẬT (bắt buộc opt-in):
    ALLOW_LIVE_AI=1 PYTHONIOENCODING=utf-8 \
      python scripts/live_table_query_patch.py --live \
      --out ../docs/evaluation/m17/w2b-patch
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import json
import os
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.simulation.table_query_engine import (  # noqa: E402
    PIPELINE_STAGE_ORDER,
    run_table_query,
    stages_of,
)

ROOT = Path(__file__).resolve().parents[2]
TARGET = "database.relational_table_query"

# Field CẤM xuất hiện trong candidate config (rò rỉ kết quả executor).
LEAK_FIELDS = (
    "aggregateResult", "result_rows", "filtered_indices", "ordered_indices",
    "projected_columns", "accepted", "rejected", "kept", "kept_indices",
    "steps", "ordered", "final", "results",
)


def _slug(header: str) -> str:
    s = header.replace("đ", "d").replace("Đ", "D")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return "".join(c if c.isalnum() else "_" for c in s.strip().lower()).strip("_")


def _norm(s) -> str:
    return unicodedata.normalize("NFC", str(s)).strip().casefold()


# ════════════════════════════════════════════════════════════════════════
# BỐN CASE — prompt NGUYÊN VĂN như trước bản vá
# ════════════════════════════════════════════════════════════════════════
class Case:
    def __init__(self, cid, finding, kind, columns, rows, ask, *, query=None,
                 expected_ops=None, expected_stages=(), refusal_category=None,
                 note=""):
        self.cid = cid
        self.finding = finding
        self.kind = kind                      # "supported" | "refusal"
        self.columns = columns                # [(header, type)]
        self.rows = rows                      # [[cell,...]]  (None = ô trống)
        self.ask = ask
        self.query = query or {}
        self.expected_ops = expected_ops or {}
        self.expected_stages = tuple(expected_stages)
        self.refusal_category = refusal_category
        self.expected_final = None            # khoá bằng oracle ở lock_expected()
        self.note = note

    def prompt(self) -> str:
        """Bảng ghi bằng CHỮ "trống" cho ô thiếu — đúng cách đề thật viết, và
        đúng đầu vào đã làm live L3 thất bại trước bản vá."""
        if not self.columns:
            return self.ask
        head = " | ".join(h for h, _ in self.columns)
        lines = [head]
        for r in self.rows:
            lines.append(" | ".join("trống" if c is None else str(c) for c in r))
        return f"Cho bảng dữ liệu sau:\n\n" + "\n".join(lines) + f"\n\n{self.ask}"

    def oracle_config(self) -> dict:
        schema = [{"name": _slug(h), "type": t, "label": h} for h, t in self.columns]
        keys = [c["name"] for c in schema]
        rows = [{keys[j]: self.rows[i][j] for j in range(len(keys))}
                for i in range(len(self.rows))]
        cfg = {"specVersion": "table-1.0", "schema": schema, "rows": rows,
               "normalizations": []}
        cfg.update(self.query)
        return cfg


P1 = Case(
    "P1", "L3", "supported",
    [("Học sinh", "text"), ("Điểm kiểm tra", "number")],
    [["An", 8], ["Bình", None], ["Chi", 9.5], ["Dũng", 7], ["Hà", None], ["Lan", 8.5]],
    "Tính điểm trung bình của các ô có dữ liệu.",
    query={"aggregate": {"func": "avg", "column": "diem_kiem_tra"}},
    expected_ops={"filter": None, "projection": None, "sort": None,
                  "limit": None, "aggregate": ("avg", "Điểm kiểm tra")},
    expected_stages=("aggregate",),
    note="AVG bỏ 2 ô trống: sum=33, count=4, avg=8.25 (empty≠0).",
)

P2 = Case(
    "P2", "L4", "supported",
    [("Tên", "text"), ("Tổ", "text"), ("Điểm", "number"), ("Số buổi vắng", "number")],
    [["An", "A", 9.0, 1], ["Bình", "B", 8.5, 0], ["Chi", "A", 6.0, 2],
     ["Dũng", "A", 9.0, 0], ["Hà", "B", 7.5, 3], ["Lan", "A", 7.5, 1],
     ["Minh", "A", 6.0, 0], ["Nga", "B", 9.5, 2]],
    ("Trong tổ A, chỉ hiển thị Tên và Điểm, sắp xếp Điểm giảm dần, lấy 3 học "
     "sinh đầu, rồi tính điểm trung bình của 3 học sinh đó."),
    query={"filter": {"op": "=", "column": "to", "value": "A"},
           "projection": ["ten", "diem"],
           "sort": {"column": "diem", "direction": "desc"},
           "limit": 3,
           "aggregate": {"func": "avg", "column": "diem"}},
    expected_ops={"filter": True, "projection": ["Tên", "Điểm"],
                  "sort": ("Điểm", "desc"), "limit": 3,
                  "aggregate": ("avg", "Điểm")},
    expected_stages=("filter", "projection", "sort", "limit", "aggregate"),
    note=("NĂM tầng; aggregate SAU limit. Tổ A 5 hs → sort desc "
          "[An9,Dũng9,Lan7.5,Chi6,Minh6] → limit3 → avg=8.5."),
)

P3 = Case(
    "P3", "L5", "refusal", [], [],
    "Lọc các học sinh có điểm từ 8 trở lên và sắp xếp giảm dần.",
    refusal_category="insufficient_specification",
    note="KHÔNG có bảng → đòi bảng, KHÔNG xui tách truy vấn.",
)

P4 = Case(
    "P4", "L1", "supported",
    [("Tên", "text"), ("Tổ", "text"), ("Điểm", "number")],
    [["An", "A", 7.5], ["Bình", "B", 8.0], ["Chi", "A", 9.25],
     ["Dũng", "B", 6.75], ["Hà", "A", 8.5], ["Lan", "B", 9.0]],
    "Giữ các học sinh có điểm từ 8 trở lên và chỉ hiển thị Tên, Điểm.",
    query={"filter": {"op": ">=", "column": "diem", "value": 8},
           "projection": ["ten", "diem"]},
    expected_ops={"filter": True, "projection": ["Tên", "Điểm"], "sort": None,
                  "limit": None, "aggregate": None},
    expected_stages=("filter", "projection"),
    note="ĐỐI CHỨNG không hồi quy — giữ nguyên hành vi đã đạt ở run 0afcb37.",
)

CASES = [P1, P2, P3, P4]


# ════════════════════════════════════════════════════════════════════════
# ORACLE — khoá expected_final TẤT ĐỊNH (offline, không API)
# ════════════════════════════════════════════════════════════════════════
def _final_from_engine(cfg: dict) -> dict:
    out = run_table_query(cfg)
    label = {c["name"]: (c.get("label") or c["name"]) for c in cfg["schema"]}
    agg = out.get("aggregateResult")
    rows = [{label[k]: v for k, v in r.items()} for r in out["result_rows"]]
    return {
        "rows": rows,
        "aggregate": None if agg is None
        else {"value": agg.get("value"), "counted": agg.get("counted")},
    }


def lock_expected() -> None:
    for c in CASES:
        c.expected_final = None if c.kind != "supported" else _final_from_engine(
            c.oracle_config())


# ════════════════════════════════════════════════════════════════════════
# GROUNDING MATRIX — so ô-theo-ô bảng nguồn ↔ candidate spec
# ════════════════════════════════════════════════════════════════════════
def _num_equiv(a, b) -> bool:
    if isinstance(a, bool) or isinstance(b, bool):
        return a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return float(a) == float(b)
    return False


def grounding_matrix(case: Case, config: dict) -> dict:
    src_cols = [h for h, _ in case.columns]
    src_types = {h: t for h, t in case.columns}
    spec_schema = config.get("schema") or []
    spec_label = {}
    for col in spec_schema:
        spec_label[_norm(col.get("label") or col.get("name"))] = col
    col_map, dropped_cols, type_mismatch = {}, [], []
    for h in src_cols:
        sc = spec_label.get(_norm(h))
        if sc is None:
            dropped_cols.append(h)
        else:
            col_map[h] = sc
            if sc.get("type") != src_types[h]:
                type_mismatch.append({"column": h, "expected": src_types[h],
                                      "actual": sc.get("type")})
    matched = {sc["name"] for sc in col_map.values()}
    added_cols = [c.get("label") or c.get("name") for c in spec_schema
                  if c["name"] not in matched]

    spec_rows = config.get("rows") or []
    src_n, spec_n = len(case.rows), len(spec_rows)
    cells, mism, empty_to_zero, unicode_changes = 0, [], [], []
    for i in range(min(src_n, spec_n)):
        srow, prow = case.rows[i], spec_rows[i]
        for j, h in enumerate(src_cols):
            if h not in col_map:
                continue
            cells += 1
            want, got = srow[j], prow.get(col_map[h]["name"])
            if want is None:
                # Ô trống PHẢI còn là trống sau chuẩn hoá — hoá 0 là mất dữ liệu.
                if got is None:
                    continue
                if got == 0 or got == "0":
                    empty_to_zero.append({"row": i + 1, "column": h, "got": got})
                mism.append({"row": i + 1, "column": h, "expected": None, "actual": got})
                continue
            if isinstance(want, (int, float)) and not isinstance(want, bool):
                if not _num_equiv(want, got):
                    mism.append({"row": i + 1, "column": h, "expected": want, "actual": got})
                continue
            if _norm(want) != _norm(got):
                mism.append({"row": i + 1, "column": h, "expected": want, "actual": got})
            elif str(want).strip() != str(got if got is not None else "").strip():
                unicode_changes.append({"row": i + 1, "column": h,
                                        "expected": want, "actual": got})

    # THỨ TỰ DÒNG NGUỒN phải được giữ (spec là bảng nguồn, không phải kết quả).
    order_ok = True
    key_col = next((h for h in src_cols if src_types[h] == "text"), None)
    if key_col and key_col in col_map and spec_n == src_n:
        name = col_map[key_col]["name"]
        got_order = [_norm(r.get(name)) for r in spec_rows]
        want_order = [_norm(r[src_cols.index(key_col)]) for r in case.rows]
        order_ok = got_order == want_order

    perfect = (not dropped_cols and not added_cols and not type_mismatch
               and src_n == spec_n and not mism and not empty_to_zero
               and not unicode_changes and order_ok)
    return {
        "source_columns": len(src_cols), "spec_columns": len(spec_schema),
        "source_rows": src_n, "spec_rows": spec_n,
        "added_columns": added_cols, "dropped_columns": dropped_cols,
        "added_rows": max(0, spec_n - src_n), "dropped_rows": max(0, src_n - spec_n),
        "type_mismatches": type_mismatch,
        "modified_cells": mism,
        "empty_to_zero": empty_to_zero,
        "unicode_changes": unicode_changes,
        "cells_compared": cells,
        "source_row_order_preserved": order_ok,
        "row_preservation": src_n == spec_n,
        "column_preservation": not dropped_cols and not added_cols,
        "grounding_perfect": perfect,
    }


def leakage_scan(config: dict) -> list[str]:
    return sorted(f for f in LEAK_FIELDS
                  if f in config and config[f] not in (None, [], {}))


def _ops_from_config(config: dict) -> dict:
    label = {c["name"]: (c.get("label") or c["name"]) for c in config.get("schema", [])}
    f, s, a = config.get("filter"), config.get("sort"), config.get("aggregate")
    proj = config.get("projection")
    return {
        "filter": bool(f),
        "projection": [label.get(x, x) for x in proj] if proj else None,
        "sort": (label.get(s["column"], s["column"]), s["direction"]) if s else None,
        "limit": config.get("limit"),
        "aggregate": (a["func"], label.get(a.get("column"), a.get("column"))) if a else None,
    }


def _stage_list(config: dict) -> list[str]:
    on = stages_of(config)
    return [s for s in PIPELINE_STAGE_ORDER if on.get(s)]


# ════════════════════════════════════════════════════════════════════════
# LIVE RUN
# ════════════════════════════════════════════════════════════════════════
async def run_live(out_dir: Path, max_http: int, max_attempts: int) -> int:
    from app.persistence.db import init_db  # noqa: F401 — load_dotenv()
    from app.ai import gemini
    from app.ai.gemini import ApiBudget, BudgetExceeded
    from app.ai.pipeline import run_pipeline
    from app.evaluation.observer import AttemptObserver
    from app.runtime_identity import runtime_identity

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("CHƯA có GEMINI_API_KEY. DỪNG.")
        return 2
    if os.getenv("ALLOW_LIVE_AI") != "1":
        print("Thiếu opt-in ALLOW_LIVE_AI=1 — ABORT trước call đầu tiên.")
        return 2

    lock_expected()   # khoá kỳ vọng TRƯỚC khi thấy output live

    ident = runtime_identity()
    import subprocess
    sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                         text=True, cwd=ROOT).stdout.strip()

    budget = ApiBudget(max_api_calls=max_http, max_attempts=max_attempts)
    gemini.set_budget(budget)

    records, stop_reason = [], None

    def snap():
        return {"logical": budget.logical_calls, "http": budget.http_requests,
                "retry": budget.retry_requests, "transient": budget.transient_hits}

    for case in CASES:
        if stop_reason:
            break
        before = snap()
        obs = AttemptObserver()
        env, err = None, None
        try:
            # pattern_store=None ⇒ KHÔNG dùng cache/pattern reuse: mỗi case đi
            # fresh analyze → classify → simulate (yêu cầu của ngân sách).
            env = await run_pipeline(case.prompt(), api_key, observer=obs)
        except BudgetExceeded as e:
            stop_reason = f"BUDGET: {e}"
            break
        except Exception as e:
            err = str(e)
        after = snap()
        delta = {k: after[k] - before[k] for k in before}

        rec = _record_case(case, env, err, obs, delta)
        records.append(rec)

        sc = _stop_check(case, rec)
        if sc:
            stop_reason = f"{case.cid}: {sc}"
            break
        if budget.retry_requests > 1:
            stop_reason = f"{case.cid}: retry HTTP vượt 1 ({budget.retry_requests})"
            break

    total = snap()
    _write_artifacts(out_dir, records, total, stop_reason, ident, sha,
                     max_http, max_attempts)
    _print_summary(records, total, stop_reason)
    return 1 if stop_reason else 0


def _record_case(case: Case, env: dict | None, err: str | None, obs, delta: dict) -> dict:
    az = obs.analyze() or {}
    cz = obs.classify() or {}
    sim_attempts = obs.simulate_attempts()
    status = (env or {}).get("status") if env else ("error" if err else None)
    route = (env or {}).get("simulation_id")
    config = (env or {}).get("config") if env else None
    fail_cat = (env or {}).get("failure_category")

    rec = {
        "case_id": case.cid, "finding": case.finding, "kind": case.kind,
        "prompt": case.prompt(), "note": case.note,
        "http": delta["http"], "logical_calls": delta["logical"],
        "http_retry": delta["retry"], "transient": delta["transient"],
        "analyze_result_ownership": az.get("result_ownership"),
        "analyze_prescribed": az.get("prescribed_procedure"),
        "analyze_requested_operations": az.get("requested_operations"),
        "analyze_requested_requirements": az.get("requested_requirements"),
        "initial_route": cz.get("simulation_id"),
        "final_route": route,
        "reclassification": 1 if obs.reclassify_attempted() else 0,
        "simulate_attempts": len(sim_attempts),
        "valid_spec_first_attempt": (bool(sim_attempts) and sim_attempts[0].get("ok") is True),
        "simulate_attempt_detail": [
            {"n": a.get("n"), "ok": a.get("ok"), "error_code": a.get("error_code"),
             "message": (a.get("message") or "")[:400]} for a in sim_attempts],
        "cache_hit": False,        # pattern_store=None ⇒ không có đường cache
        "cache_source": "none",
        "status": status, "failure_category": fail_cat,
        "error_code": (env or {}).get("error_code"),
        "pipeline_error": err,
        "learner_reason": (env or {}).get("learner_reason") or (env or {}).get("reason"),
        "simulation_created": bool(config) and status == "ok",
    }

    if case.kind == "supported":
        passed, problems = True, []
        if status != "ok":
            passed = False
            problems.append(f"status={status} (mong ok)")
        if route != TARGET:
            passed = False
            problems.append(f"route={route}")
        gm = leak = ops = final = stages = None
        dropped_stages = []
        if isinstance(config, dict) and route == TARGET:
            gm = grounding_matrix(case, config)
            leak = leakage_scan(config)
            ops = _ops_from_config(config)
            final = _final_from_engine(config)
            stages = _stage_list(config)
            dropped_stages = [s for s in case.expected_stages if s not in stages]
            if not gm["grounding_perfect"]:
                passed = False
                problems.append("grounding không hoàn hảo")
            if leak:
                passed = False
                problems.append(f"rò rỉ kết quả: {leak}")
            if dropped_stages:
                passed = False
                problems.append(f"thiếu tầng: {dropped_stages}")
            if final != case.expected_final:
                passed = False
                problems.append("engine final ≠ expected (operation/spec sai)")
        else:
            passed = False
            problems.append("không có config hợp lệ để audit")
        rec.update({
            "grounding": gm, "leakage": leak or [], "operations": ops,
            "expected_operations": case.expected_ops,
            "requested_stages_expected": list(case.expected_stages),
            "represented_stages": stages,
            "dropped_pipeline_stages": dropped_stages,
            "completeness_evidence": (env or {}).get("completeness"),
            "expected_final": case.expected_final, "actual_final": final,
            "result_leakage": bool(leak),
            "generic_leak": route == "generic.rule_scene",
            "false_positive_simulation": False,
            "false_refusal": status == "unsupported",
            "passed": passed, "problems": problems,
        })
    else:
        passed, problems = True, []
        if status != "unsupported":
            passed = False
            problems.append(f"status={status} (mong unsupported)")
        if fail_cat != case.refusal_category:
            passed = False
            problems.append(f"failure_category={fail_cat} (mong {case.refusal_category})")
        if isinstance(config, dict):
            passed = False
            problems.append("có config khi lẽ ra phải từ chối")
        msg = (rec["learner_reason"] or "").lower()
        if "tách" in msg:
            passed = False
            problems.append("thông điệp vẫn xui TÁCH truy vấn dù lỗi là thiếu bảng")
        if "bảng" not in msg:
            passed = False
            problems.append("thông điệp không nói tới BẢNG")
        rec.update({
            "input_sufficiency": (env or {}).get("input_sufficiency"),
            "generic_leak": route == "generic.rule_scene",
            "false_positive_simulation": status == "ok",
            "false_refusal": False,
            "passed": passed, "problems": problems,
        })
    return rec


def _stop_check(case: Case, rec: dict) -> str | None:
    """STOP CONDITIONS — dừng NGAY, không sửa production code."""
    if rec["final_route"] == "generic.rule_scene":
        return "route sang generic"
    if case.kind == "supported":
        gm = rec.get("grounding")
        if gm:
            if gm["empty_to_zero"]:
                return "ô trống biến thành 0"
            if gm["modified_cells"] or gm["added_rows"] or gm["dropped_rows"]:
                return "supported case mất/thêm/sửa cell"
            if gm["added_columns"] or gm["dropped_columns"]:
                return "schema mất/thêm cột"
        if rec.get("result_leakage"):
            return "candidate spec chứa kết quả cuối"
        if rec["status"] == "ok" and rec.get("dropped_pipeline_stages"):
            return "status=ok nhưng THIẾU TẦNG"
        if rec["status"] == "error":
            return "cạn lượt simulate (retries exhaust)"
    else:
        if rec["status"] == "ok":
            return "đề thiếu bảng nhưng hệ tự dựng mô phỏng"
        if rec["failure_category"] == "semantic_incomplete":
            return "vẫn báo semantic_incomplete cho ca thiếu bảng"
    return None


# ════════════════════════════════════════════════════════════════════════
# ARTIFACTS
# ════════════════════════════════════════════════════════════════════════
def _rate(num, den):
    return None if den == 0 else round(num / den, 4)


def _summ(records, total, stop_reason):
    sup = [r for r in records if r["kind"] == "supported"]
    neg = [r for r in records if r["kind"] == "refusal"]
    passed = [r for r in records if r["passed"]]
    grounded = [r for r in sup if r.get("grounding")]
    return {
        "cases_run": len(records), "cases_passed": len(passed),
        "strict_cases": f"{len(passed)}/{len(records)}",
        "supported_run": len(sup),
        "supported_passed": sum(1 for r in sup if r["passed"]),
        "negative_run": len(neg),
        "negative_passed": sum(1 for r in neg if r["passed"]),
        "total_http": total["http"], "total_logical": total["logical"],
        "http_retry": total["retry"], "transient": total["transient"],
        "reclassification": sum(r["reclassification"] for r in records),
        "cache_hits": sum(1 for r in records if r.get("cache_hit")),
        "valid_spec_first_attempt": _rate(
            sum(1 for r in sup if r["valid_spec_first_attempt"]), len(sup)),
        "simulate_attempts_per_case": {r["case_id"]: r["simulate_attempts"]
                                       for r in records},
        "grounding_perfect": _rate(
            sum(1 for r in grounded if r["grounding"]["grounding_perfect"]),
            len(grounded)),
        "modified_cells": sum(len(r["grounding"]["modified_cells"]) for r in grounded),
        "empty_to_zero": sum(len(r["grounding"]["empty_to_zero"]) for r in grounded),
        "type_mismatches": sum(len(r["grounding"]["type_mismatches"]) for r in grounded),
        "generic_leak": sum(1 for r in records if r.get("generic_leak")),
        "false_positive_simulation": sum(
            1 for r in records if r.get("false_positive_simulation")),
        "false_refusal": sum(1 for r in records if r.get("false_refusal")),
        "result_leakage": sum(1 for r in sup if r.get("result_leakage")),
        "semantic_loss": sum(len(r.get("dropped_pipeline_stages") or []) for r in sup),
        "stop_reason": stop_reason,
        "all_passed": (len(passed) == len(records) and stop_reason is None
                       and len(records) == len(CASES)),
    }


def _write_artifacts(out_dir, records, total, stop_reason, ident, sha,
                     max_http, max_attempts):
    out_dir.mkdir(parents=True, exist_ok=True)
    summ = _summ(records, total, stop_reason)
    run_meta = {
        "wave": "M17 W2B-PATCH LIVE",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": "gemini-2.5-flash", "execution_environment": "local_python",
        "git_sha": sha, "cache_version": ident["cache_version"],
        "family_count": ident["family_count"], "target_count": ident["target_count"],
        "stable_catalog_hash": ident["stable_catalog_hash"],
        "budget": {"max_cases": len(CASES), "max_http": max_http,
                   "max_http_retry": 1, "max_attempts_per_call": max_attempts},
        "execution_note": (
            "production run_pipeline (bất biến #22), pattern_store=None nên KHÔNG "
            "có đường cache/pattern-reuse: mỗi case đi FRESH analyze → classify → "
            "simulate. Danh tính container xác minh RIÊNG bằng runtime_doctor "
            "(runtime_identity_w2b_patch.json) — PASS trước khi chạy live."),
        "retry_note": (
            "`http_retry` = retry ở TẦNG HTTP (transient). `simulate_attempts` = "
            "lượt sinh spec của product semantics — HAI thứ KHÁC NHAU, báo riêng."),
    }
    (out_dir / "live_table_query_patch.json").write_text(
        json.dumps({"run_meta": run_meta, "summary": summ, "cases": records},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    matrix = {r["case_id"]: r.get("grounding") for r in records
              if r["kind"] == "supported"}
    present = {k: v for k, v in matrix.items() if v}
    (out_dir / "live_table_patch_grounding_matrix.json").write_text(
        json.dumps({"run_meta": run_meta, "matrix": matrix, "acceptance": {
            "grounding_perfect": _rate(
                sum(1 for m in present.values() if m["grounding_perfect"]), len(present)),
            "row_preservation": _rate(
                sum(1 for m in present.values() if m["row_preservation"]), len(present)),
            "column_preservation": _rate(
                sum(1 for m in present.values() if m["column_preservation"]), len(present)),
            "source_row_order_preserved": _rate(
                sum(1 for m in present.values() if m["source_row_order_preserved"]),
                len(present)),
            "modified_cells": summ["modified_cells"],
            "empty_to_zero": summ["empty_to_zero"],
            "type_mismatches": summ["type_mismatches"],
        }}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    _write_report_md(out_dir, run_meta, summ, records)
    _write_ledger_md(out_dir, records, stop_reason)


def _write_report_md(out_dir, meta, summ, records):
    L = [
        "# M17 W2B-PATCH LIVE — kiểm chứng lại 3 finding đã vá", "",
        f"- Model **{meta['model']}** · env **{meta['execution_environment']}** · "
        f"SHA `{meta['git_sha'][:12]}` · cache **{meta['cache_version']}** · "
        f"family **{meta['family_count']}** · target **{meta['target_count']}** · "
        f"hash `{meta['stable_catalog_hash'][:12]}`",
        f"- Strict **{summ['strict_cases']}** · supported "
        f"**{summ['supported_passed']}/{summ['supported_run']}** · negative "
        f"**{summ['negative_passed']}/{summ['negative_run']}**",
        f"- HTTP **{summ['total_http']}**/{meta['budget']['max_http']} · "
        f"http-retry **{summ['http_retry']}** · transient **{summ['transient']}** · "
        f"reclassify **{summ['reclassification']}** · cache-hit **{summ['cache_hits']}**",
        f"- valid-spec-first-attempt **{summ['valid_spec_first_attempt']}** · "
        f"simulate attempts {summ['simulate_attempts_per_case']}",
        f"- grounding **{summ['grounding_perfect']}** · empty→0 "
        f"**{summ['empty_to_zero']}** · modified cells **{summ['modified_cells']}** · "
        f"generic-leak **{summ['generic_leak']}** · fp-sim "
        f"**{summ['false_positive_simulation']}** · false-refusal "
        f"**{summ['false_refusal']}** · result-leak **{summ['result_leakage']}** · "
        f"semantic-loss **{summ['semantic_loss']}**",
        f"- STOP: **{summ['stop_reason'] or 'không'}** · all_passed: "
        f"**{summ['all_passed']}**", "",
        f"> {meta['execution_note']}", "",
        f"> {meta['retry_note']}", "",
        "| Case | Finding | Loại | HTTP | sim | route | grounding | final | đạt |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in records:
        if r["kind"] == "supported":
            gm = r.get("grounding")
            g = "perfect" if gm and gm["grounding_perfect"] else "LỖI"
            fin = "khớp" if r.get("actual_final") == r.get("expected_final") else "LỆCH"
            L.append(f"| {r['case_id']} | {r['finding']} | supported | {r['http']} | "
                     f"{r['simulate_attempts']} | `{r['final_route']}` | {g} | {fin} | "
                     f"{'✔' if r['passed'] else '✘'} |")
        else:
            L.append(f"| {r['case_id']} | {r['finding']} | refusal | {r['http']} | "
                     f"{r['simulate_attempts']} | {r['status']}/{r['failure_category']} "
                     f"| — | — | {'✔' if r['passed'] else '✘'} |")
    L += ["", "## Chi tiết từng case", ""]
    for r in records:
        L.append(f"### {r['case_id']} ({r['finding']}) — "
                 f"{'ĐẠT' if r['passed'] else 'KHÔNG ĐẠT'}")
        L.append(f"- kỳ vọng: {r['note']}")
        L.append(f"- prompt: `{r['prompt'].splitlines()[-1]}`")
        L.append(f"- route: initial=`{r['initial_route']}` → final=`{r['final_route']}` "
                 f"· reclassify={r['reclassification']} · simulate_attempts="
                 f"{r['simulate_attempts']} · valid-spec-first="
                 f"{r['valid_spec_first_attempt']} · cache_hit={r['cache_hit']}")
        L.append(f"- analyze: result_ownership={r['analyze_result_ownership']!r} · "
                 f"requested_operations={r['analyze_requested_operations']}")
        if r["simulate_attempts"] > 1:
            L.append("- **PHẢN HỒI GIỮA CÁC LƯỢT SIMULATE:**")
            for a in r["simulate_attempt_detail"]:
                L.append(f"  - lượt {a['n']}: ok={a['ok']} · code={a['error_code']} "
                         f"· {a['message']}")
        if r["kind"] == "supported":
            gm = r.get("grounding") or {}
            L.append(f"- grounding: rows {gm.get('source_rows')}→{gm.get('spec_rows')} · "
                     f"cols {gm.get('source_columns')}→{gm.get('spec_columns')} · "
                     f"cells {gm.get('cells_compared')} · modified="
                     f"{len(gm.get('modified_cells', []))} · empty→0="
                     f"{len(gm.get('empty_to_zero', []))} · type_mismatch="
                     f"{len(gm.get('type_mismatches', []))} · order_preserved="
                     f"{gm.get('source_row_order_preserved')}")
            L.append(f"- tầng: mong {r['requested_stages_expected']} · dựng được "
                     f"{r['represented_stages']} · thiếu {r['dropped_pipeline_stages']}")
            L.append(f"- operations: {r.get('operations')}  (mong "
                     f"{r.get('expected_operations')})")
            L.append(f"- executor: expected_final={r.get('expected_final')} · "
                     f"actual_final={r.get('actual_final')} · leakage={r.get('leakage')}")
        else:
            L.append(f"- failure_category=`{r['failure_category']}` · "
                     f"error_code=`{r['error_code']}` · simulation_created="
                     f"{r['simulation_created']}")
            L.append(f"- input_sufficiency: {r.get('input_sufficiency')}")
            L.append(f"- learner_reason: {r.get('learner_reason')!r}")
        if r["problems"]:
            L.append(f"- **VẤN ĐỀ:** {r['problems']}")
        L.append("")
    (out_dir / "live_table_query_patch_report.md").write_text(
        "\n".join(L) + "\n", encoding="utf-8")


def _write_ledger_md(out_dir, records, stop_reason):
    fails = [r for r in records if not r["passed"]]
    L = ["# M17 W2B-PATCH LIVE — Failure ledger", "",
         f"STOP: **{stop_reason or 'không'}** · case KHÔNG đạt: **{len(fails)}**", ""]
    if not fails:
        L.append("Không case nào thất bại. Ba finding L3/L4/L5 đã được kiểm chứng "
                 "trên LLM thật, và đối chứng L1 không hồi quy.")
    else:
        L.append("KHÔNG sửa production code, KHÔNG đổi expected/tolerance trong run:")
        L.append("")
        for r in fails:
            L.append(f"## {r['case_id']} ({r['finding']})")
            L.append(f"- vấn đề: {r['problems']}")
            gm = r.get("grounding")
            if gm:
                if gm["empty_to_zero"]:
                    L.append(f"- empty_to_zero: {gm['empty_to_zero']}")
                if gm["modified_cells"]:
                    L.append(f"- modified_cells: {gm['modified_cells']}")
            if r.get("dropped_pipeline_stages"):
                L.append(f"- thiếu tầng: {r['dropped_pipeline_stages']}")
            L.append("")
    (out_dir / "live_table_patch_failure_ledger.md").write_text(
        "\n".join(L) + "\n", encoding="utf-8")


def _print_summary(records, total, stop_reason):
    s = _summ(records, total, stop_reason)
    print("\n=== M17 W2B-PATCH LIVE ===")
    print(f"strict {s['strict_cases']} · supported {s['supported_passed']}/"
          f"{s['supported_run']} · negative {s['negative_passed']}/{s['negative_run']}")
    print(f"HTTP {s['total_http']} · http-retry {s['http_retry']} · transient "
          f"{s['transient']} · reclassify {s['reclassification']} · cache-hit "
          f"{s['cache_hits']}")
    print(f"valid-spec-first {s['valid_spec_first_attempt']} · simulate attempts "
          f"{s['simulate_attempts_per_case']}")
    print(f"grounding {s['grounding_perfect']} · empty→0 {s['empty_to_zero']} · "
          f"generic-leak {s['generic_leak']} · fp-sim "
          f"{s['false_positive_simulation']} · false-refusal {s['false_refusal']} · "
          f"result-leak {s['result_leakage']} · semantic-loss {s['semantic_loss']}")
    print(f"STOP: {stop_reason or 'không'} · all_passed: {s['all_passed']}")
    for r in records:
        print(f"  [{r['case_id']}/{r['finding']}] "
              f"{'ĐẠT' if r['passed'] else 'KHÔNG ĐẠT'} · http={r['http']} · "
              f"sim={r['simulate_attempts']} · {r['problems'] or 'ok'}")


# ════════════════════════════════════════════════════════════════════════
# OFFLINE — khoá kỳ vọng + tự kiểm máy audit (fault injection)
# ════════════════════════════════════════════════════════════════════════
def _print_lock() -> int:
    lock_expected()
    print("=== W2B-PATCH — KHÓA KỲ VỌNG (oracle tất định, KHÔNG API) ===\n")
    ok = True
    for c in CASES:
        print(f"[{c.cid}/{c.finding}] {c.kind} · {c.note}")
        print(f"     prompt: {c.ask}")
        if c.kind == "supported":
            print(f"     KHÓA tầng: {list(c.expected_stages)}")
            if c.expected_final["aggregate"] is not None:
                print(f"     KHÓA aggregate: {c.expected_final['aggregate']}")
            print(f"     KHÓA rows ({len(c.expected_final['rows'])}): "
                  f"{c.expected_final['rows']}")
            if _final_from_engine(c.oracle_config()) != c.expected_final:
                ok = False
                print("     !! ORACLE KHÔNG TẤT ĐỊNH — DỪNG")
        else:
            print(f"     → refuse [{c.refusal_category}]")
        print()
    print("oracle self-consistency:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def _selftest() -> int:
    """Chạy máy audit trên config ORACLE: sạch phải sạch, và FAULT phải bị bắt."""
    lock_expected()
    ok = True
    for c in CASES:
        if c.kind != "supported":
            continue
        cfg = c.oracle_config()
        gm, leak = grounding_matrix(c, cfg), leakage_scan(cfg)
        stages = _stage_list(cfg)
        final = _final_from_engine(cfg)
        good = (gm["grounding_perfect"] and not leak and final == c.expected_final
                and tuple(stages) == c.expected_stages)
        print(f"[{c.cid}] clean: grounding={gm['grounding_perfect']} leak={leak} "
              f"stages={stages} final_match={final == c.expected_final} → "
              f"{'OK' if good else 'LỖI CODE'}")
        ok = ok and good

        # FAULT 1 — ô trống hoá 0 PHẢI bị bắt (chính là finding L3).
        if any(v is None for r in cfg["rows"] for v in r.values()):
            f1 = copy.deepcopy(cfg)
            for r in f1["rows"]:
                for k in list(r):
                    if r[k] is None:
                        r[k] = 0
            assert grounding_matrix(c, f1)["empty_to_zero"], f"{c.cid}: empty→0 lọt"
        # FAULT 2 — bỏ một tầng PHẢI bị bắt (chính là finding L4).
        if len(c.expected_stages) > 1:
            f2 = copy.deepcopy(cfg)
            f2.pop(c.expected_stages[-1], None)
            missing = [s for s in c.expected_stages if s not in _stage_list(f2)]
            assert missing, f"{c.cid}: thiếu tầng lọt"
        # FAULT 3 — đổi một ô số PHẢI bị bắt.
        f3 = copy.deepcopy(cfg)
        numk = next((col["name"] for col in f3["schema"] if col["type"] == "number"), None)
        if numk:
            for r in f3["rows"]:
                if r.get(numk) is not None:
                    r[numk] = 999999
                    break
            assert grounding_matrix(c, f3)["modified_cells"], f"{c.cid}: sửa ô lọt"
        # FAULT 4 — rò rỉ kết quả PHẢI bị bắt.
        f4 = copy.deepcopy(cfg)
        f4["aggregateResult"] = {"value": 1, "counted": 1}
        assert leakage_scan(f4), f"{c.cid}: rò rỉ lọt"
        # FAULT 5 — đảo thứ tự dòng nguồn PHẢI bị bắt.
        f5 = copy.deepcopy(cfg)
        f5["rows"] = list(reversed(f5["rows"]))
        assert not grounding_matrix(c, f5)["source_row_order_preserved"], \
            f"{c.cid}: đảo thứ tự dòng lọt"
    print("\nselftest:", "PASS (audit đúng + biết kêu khi fault)" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--lock", action="store_true")
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--live", action="store_true")
    p.add_argument("--out", default=str(ROOT / "docs/evaluation/m17/w2b-patch"))
    p.add_argument("--max-http", type=int, default=14)
    p.add_argument("--max-attempts", type=int, default=2)
    args = p.parse_args()
    if args.lock:
        return _print_lock()
    if args.selftest:
        return _selftest()
    if args.live:
        return asyncio.run(run_live(Path(args.out), args.max_http, args.max_attempts))
    print("Chọn --lock / --selftest (offline) hoặc --live (cần ALLOW_LIVE_AI=1).")
    return 2


if __name__ == "__main__":
    sys.exit(main())
