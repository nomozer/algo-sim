# -*- coding: utf-8 -*-
"""M17 W2B-LIVE — GROUNDING VERIFICATION cho database.relational_table_query.

KHÔNG phải routing smoke. Đây là kiểm chứng production LLM orchestration thật có
GROUNDING trung thực: trích đúng schema, chép đúng từng ô, giữ kiểu, giữ ô trống
là trống (không hoá 0), route đúng, và ĐỂ executor tất định sở hữu toàn bộ kết
quả (LLM không nhét đáp án vào candidate spec).

Hai chế độ:

    # KHÓA kỳ vọng bằng oracle tất định — KHÔNG gọi API:
    python scripts/live_table_query.py --lock

    # CHẠY THẬT (bắt buộc opt-in), ngân sách 6 case / ≤20 HTTP / ≤1 retry:
    ALLOW_LIVE_AI=1 PYTHONIOENCODING=utf-8 \
      python scripts/live_table_query.py --live --out ../docs/evaluation/m17/rc1

Bất biến tôn trọng: run_pipeline production (invariant #22); oracle =
`run_table_query` (chính engine tất định). Không sửa production code trong run.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.simulation.table_query_engine import run_table_query  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]

# ── field bị CẤM xuất hiện trong candidate config (rò rỉ kết quả executor) ──
LEAK_FIELDS = (
    "aggregateResult", "result_rows", "filtered_indices", "ordered_indices",
    "projected_columns", "accepted", "rejected", "kept", "kept_indices",
    "steps", "ordered", "final", "results",
)


def _slug(header: str) -> str:
    """Header tiếng Việt → id an toàn ascii (chỉ để dựng config ORACLE của ta;
    LLM tự chọn id của nó — ta so khớp trên NHÃN, không trên id). đ/Đ không
    phân rã NFKD nên thay tay trước, kẻo 'Điểm' rớt thành 'iem'."""
    s = header.replace("đ", "d").replace("Đ", "D")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return "".join(c if c.isalnum() else "_" for c in s.strip().lower()).strip("_")


def _norm(s) -> str:
    return unicodedata.normalize("NFC", str(s)).strip().casefold()


# ════════════════════════════════════════════════════════════════════════
# ĐỊNH NGHĨA 6 CASE — bảng nguồn, prompt, kỳ vọng (KHÔNG dùng bảng gần 30×8)
# ════════════════════════════════════════════════════════════════════════
class Case:
    def __init__(self, cid, kind, columns, rows, ask, *, expected_route=None,
                 expected_family=None, query=None, expected_final=None,
                 expected_ops=None, refusal_category=None, note=""):
        self.cid = cid
        self.kind = kind                      # "supported" | "refusal"
        self.columns = columns                # [(header, type)]
        self.rows = rows                      # [[cell,...]] (None = trống)
        self.ask = ask
        self.expected_route = expected_route
        self.expected_family = expected_family
        self.query = query or {}              # filter/projection/sort/limit/aggregate (ORACLE)
        self.expected_final = expected_final  # normalized dict (KHÓA bằng oracle)
        self.expected_ops = expected_ops or {}
        self.refusal_category = refusal_category
        self.note = note

    def prompt(self) -> str:
        if not self.columns:
            return self.ask
        head = " | ".join(h for h, _ in self.columns)
        lines = [head]
        for r in self.rows:
            lines.append(" | ".join("trống" if c is None else str(c) for c in r))
        table = "\n".join(lines)
        return f"Cho bảng dữ liệu sau:\n\n{table}\n\n{self.ask}"

    def oracle_config(self) -> dict:
        schema = [{"name": _slug(h), "type": t, "label": h} for h, t in self.columns]
        keys = [c["name"] for c in schema]
        rows = [{keys[j]: self.rows[i][j] for j in range(len(keys))}
                for i in range(len(self.rows))]
        cfg = {"specVersion": "table-1.0", "schema": schema, "rows": rows}
        cfg.update(self.query)
        return cfg


# ── bảng dùng chung ──
def _c(*pairs):
    return list(pairs)


L1 = Case(
    "L1", "supported",
    _c(("Tên", "text"), ("Tổ", "text"), ("Điểm", "number")),
    [["An", "A", 7.5], ["Bình", "B", 8.0], ["Chi", "A", 9.25],
     ["Dũng", "B", 6.75], ["Hà", "A", 8.5], ["Lan", "B", 9.0]],
    "Giữ các học sinh có điểm từ 8 trở lên và chỉ hiển thị Tên, Điểm.",
    expected_route="database.relational_table_query",
    query={"filter": {"op": ">=", "column": "diem", "value": 8},
           "projection": ["ten", "diem"]},
    expected_ops={"filter": True, "projection": ["Tên", "Điểm"], "sort": None,
                  "limit": None, "aggregate": None},
    note="filter score>=8 + projection Tên,Điểm; không sort.",
)

L2 = Case(
    "L2", "supported",
    _c(("STT", "number"), ("Tên", "text"), ("Điểm", "number")),
    [[1, "An", 8.5], [2, "Bình", 9.0], [3, "Chi", 8.5],
     [4, "Dũng", 7.0], [5, "Hà", 9.0], [6, "Lan", 8.5]],
    "Sắp xếp giảm dần theo Điểm.",
    expected_route="database.relational_table_query",
    query={"sort": {"column": "diem", "direction": "desc"}},
    expected_ops={"filter": None, "projection": None,
                  "sort": ("Điểm", "desc"), "limit": None, "aggregate": None},
    note="stable sort desc: Bình<Hà (9.0); An<Chi<Lan (8.5).",
)

L3 = Case(
    "L3", "supported",
    _c(("Học sinh", "text"), ("Điểm kiểm tra", "number")),
    [["An", 8], ["Bình", None], ["Chi", 9.5], ["Dũng", 7],
     ["Hà", None], ["Lan", 8.5]],
    "Tính điểm trung bình của các ô có dữ liệu.",
    expected_route="database.relational_table_query",
    query={"aggregate": {"func": "avg", "column": "diem_kiem_tra"}},
    expected_ops={"filter": None, "projection": None, "sort": None,
                  "limit": None, "aggregate": ("avg", "Điểm kiểm tra")},
    note="AVG bỏ 2 ô trống: sum=33, count=4, avg=8.25 (empty≠0).",
)

# L4 — pipeline gộp. NGỮ NGHĨA AGGREGATE ĐÃ KHÓA TỪ ENGINE (đọc code, không
# đọc output): filter→projection→sort→LIMIT→aggregate. Aggregate tính SAU limit,
# trên đúng các dòng còn lại sau khi cắt.
L4 = Case(
    "L4", "supported",
    _c(("Tên", "text"), ("Tổ", "text"), ("Điểm", "number"), ("Số buổi vắng", "number")),
    [["An", "A", 9.0, 1], ["Bình", "B", 8.5, 0], ["Chi", "A", 6.0, 2],
     ["Dũng", "A", 9.0, 0], ["Hà", "B", 7.5, 3], ["Lan", "A", 7.5, 1],
     ["Minh", "A", 6.0, 0], ["Nga", "B", 9.5, 2]],
    ("Trong tổ A, chỉ hiển thị Tên và Điểm, sắp xếp Điểm giảm dần, lấy 3 học "
     "sinh đầu, rồi tính điểm trung bình của 3 học sinh đó."),
    expected_route="database.relational_table_query",
    query={"filter": {"op": "=", "column": "to", "value": "A"},
           "projection": ["ten", "diem"],
           "sort": {"column": "diem", "direction": "desc"},
           "limit": 3,
           "aggregate": {"func": "avg", "column": "diem"}},
    expected_ops={"filter": True, "projection": ["Tên", "Điểm"],
                  "sort": ("Điểm", "desc"), "limit": 3,
                  "aggregate": ("avg", "Điểm")},
    note=("pipeline 5 tầng; aggregate SAU limit (khóa từ engine). Tổ A: 5 hs → "
          "sort desc [An9,Dũng9,Lan7.5,Chi6,Minh6] → limit3 [An9,Dũng9,Lan7.5] "
          "→ avg=8.5."),
)

L5 = Case(
    "L5", "refusal", [], [],
    "Lọc các học sinh có điểm từ 8 trở lên và sắp xếp giảm dần.",
    refusal_category="insufficient_specification",
    note="không có bảng → refuse an toàn, KHÔNG tự dựng bảng mẫu.",
)

L6 = Case(
    "L6", "refusal",
    _c(("Tên", "text"), ("Tổ", "text")),
    [["An", "A"], ["Bình", "B"], ["Chi", "A"], ["Dũng", "B"], ["Hà", "A"]],
    "Đếm số học sinh tổ A và đếm số học sinh tổ B.",
    refusal_category="semantic_incomplete",
    note="2 goal độc lập → completeness FAIL, KHÔNG âm thầm chạy 1 COUNT.",
)

CASES = [L1, L2, L3, L4, L5, L6]


# ════════════════════════════════════════════════════════════════════════
# ORACLE — khóa expected_final tất định (offline, không API)
# ════════════════════════════════════════════════════════════════════════
def _final_from_engine(cfg: dict) -> dict:
    """Chuẩn hoá kết quả engine về dạng so sánh được (không phụ thuộc id cột)."""
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
    """Chạy oracle trên config TA tự dựng để KHÓA expected_final trước live."""
    for c in CASES:
        if c.kind != "supported":
            c.expected_final = None
            continue
        c.expected_final = _final_from_engine(c.oracle_config())


def _print_lock() -> int:
    lock_expected()
    print("=== M17 W2B-LIVE — KHÓA KỲ VỌNG (oracle tất định, KHÔNG API) ===\n")
    ok = True
    for c in CASES:
        print(f"[{c.cid}] {c.kind} · {c.note}")
        if c.kind == "supported":
            print(f"     prompt: {c.ask}")
            ef = c.expected_final
            if ef["aggregate"] is not None:
                print(f"     KHÓA aggregate: {ef['aggregate']}")
            print(f"     KHÓA rows ({len(ef['rows'])}): {ef['rows']}")
            # tự kiểm oracle: chạy lại phải ra y hệt (tất định)
            again = _final_from_engine(c.oracle_config())
            if again != ef:
                ok = False
                print("     !! ORACLE KHÔNG TẤT ĐỊNH — DỪNG")
        else:
            print(f"     prompt: {c.ask!r}  → refuse [{c.refusal_category}]")
        print()
    print("oracle self-consistency:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


# ════════════════════════════════════════════════════════════════════════
# GROUNDING MATRIX — so ô-theo-ô bảng nguồn ↔ candidate spec (§9)
# ════════════════════════════════════════════════════════════════════════
def _num_equiv(a, b) -> bool:
    if isinstance(a, bool) or isinstance(b, bool):
        return a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return float(a) == float(b)
    return False


def grounding_matrix(case: Case, config: dict) -> dict:
    """So bảng nguồn (ground truth của ta) với schema/rows trong candidate spec."""
    src_cols = [h for h, _ in case.columns]
    src_types = {h: t for h, t in case.columns}
    spec_schema = config.get("schema") or []
    # map cột: header nguồn → cột spec theo NHÃN (label ưu tiên, fallback name)
    spec_label = {}
    for col in spec_schema:
        lbl = col.get("label") or col.get("name")
        spec_label[_norm(lbl)] = col
    col_map = {}          # header nguồn → spec col
    dropped_cols, type_mismatch = [], []
    for h in src_cols:
        sc = spec_label.get(_norm(h))
        if sc is None:
            dropped_cols.append(h)
        else:
            col_map[h] = sc
            if sc.get("type") != src_types[h]:
                type_mismatch.append({"column": h, "expected": src_types[h],
                                      "actual": sc.get("type")})
    matched_names = {sc["name"] for sc in col_map.values()}
    added_cols = [c.get("label") or c.get("name") for c in spec_schema
                  if c["name"] not in matched_names]

    spec_rows = config.get("rows") or []
    src_n, spec_n = len(case.rows), len(spec_rows)
    added_rows = max(0, spec_n - src_n)
    dropped_rows = max(0, src_n - spec_n)

    cells, mism, empty_to_zero, unicode_changes = 0, [], [], []
    for i in range(min(src_n, spec_n)):
        srow = case.rows[i]
        prow = spec_rows[i]
        for j, h in enumerate(src_cols):
            if h not in col_map:
                continue
            cells += 1
            want = srow[j]
            got = prow.get(col_map[h]["name"])
            if want is None:
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
            # text: NFC + trim; giữ nguyên nội dung Unicode
            if _norm(want) != _norm(got):
                mism.append({"row": i + 1, "column": h, "expected": want, "actual": got})
            elif str(want).strip() != str(got if got is not None else "").strip():
                unicode_changes.append({"row": i + 1, "column": h,
                                        "expected": want, "actual": got})

    perfect = (not dropped_cols and not added_cols and not type_mismatch
               and added_rows == 0 and dropped_rows == 0 and not mism
               and not empty_to_zero and not unicode_changes)
    return {
        "source_columns": len(src_cols), "spec_columns": len(spec_schema),
        "source_rows": src_n, "spec_rows": spec_n,
        "added_columns": added_cols, "dropped_columns": dropped_cols,
        "added_rows": added_rows, "dropped_rows": dropped_rows,
        "type_mismatches": type_mismatch,
        "modified_cells": mism,
        "empty_to_zero": empty_to_zero,
        "unicode_changes": unicode_changes,
        "cells_compared": cells,
        "row_preservation": src_n == spec_n and dropped_rows == 0 and added_rows == 0,
        "column_preservation": not dropped_cols and not added_cols,
        "grounding_perfect": perfect,
    }


def leakage_scan(config: dict) -> list[str]:
    """Field kết quả executor bị rò vào candidate config?"""
    found = []
    for f in LEAK_FIELDS:
        if f in config and config[f] not in (None, [], {}):
            found.append(f)
    return sorted(found)


def _ops_from_config(config: dict) -> dict:
    label = {c["name"]: (c.get("label") or c["name"]) for c in config.get("schema", [])}
    f = config.get("filter")
    s = config.get("sort")
    a = config.get("aggregate")
    proj = config.get("projection")
    return {
        "filter": bool(f),
        "projection": [label.get(x, x) for x in proj] if proj else None,
        "sort": (label.get(s["column"], s["column"]), s["direction"]) if s else None,
        "limit": config.get("limit"),
        "aggregate": (a["func"], label.get(a.get("column"), a.get("column"))) if a else None,
    }


def _actual_final(config: dict) -> dict:
    return _final_from_engine(config)


# ════════════════════════════════════════════════════════════════════════
# LIVE RUN
# ════════════════════════════════════════════════════════════════════════
async def run_live(out_dir: Path, max_http: int, max_attempts: int) -> int:
    from app.persistence.db import init_db  # noqa: F401 — import gọi load_dotenv() → nạp backend/.env
    from app.ai import gemini
    from app.ai.gemini import ApiBudget, BudgetExceeded
    from app.ai.pipeline import run_pipeline
    from app.evaluation.observer import AttemptObserver
    from app.runtime_identity import runtime_identity

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("CHƯA có GEMINI_API_KEY (backend/.env hoặc env). DỪNG.")
        return 2
    if os.getenv("ALLOW_LIVE_AI") != "1":
        print("Thiếu opt-in ALLOW_LIVE_AI=1 — ABORT trước call đầu tiên.")
        return 2

    lock_expected()  # khóa expected TRƯỚC khi thấy bất kỳ output live nào

    ident = runtime_identity()
    import subprocess
    sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                         text=True, cwd=ROOT).stdout.strip()

    budget = ApiBudget(max_api_calls=max_http, max_attempts=max_attempts)
    gemini.set_budget(budget)

    records = []
    stop_reason = None

    def snap():
        return {"logical": budget.logical_calls, "http": budget.http_requests,
                "retry": budget.retry_requests, "transient": budget.transient_hits}

    for case in CASES:
        if stop_reason:
            break
        before = snap()
        obs = AttemptObserver()
        env = None
        err = None
        try:
            env = await run_pipeline(case.prompt(), api_key, observer=obs)
        except BudgetExceeded as e:
            stop_reason = f"BUDGET: {e}"
            break
        except Exception as e:  # RuntimeError sau 3 lần simulate, v.v.
            err = str(e)
        after = snap()
        delta = {k: after[k] - before[k] for k in before}

        rec = _record_case(case, env, err, obs, delta)
        records.append(rec)

        # STOP CONDITIONS (§12) — dừng NGAY nếu một supported case sai grounding
        sc = _stop_check(case, rec)
        if sc:
            stop_reason = f"{case.cid}: {sc}"
            break
        if budget.retry_requests > 1:
            stop_reason = f"{case.cid}: retry vượt 1 (retry={budget.retry_requests})"
            break

    total = snap()
    _write_artifacts(out_dir, records, total, stop_reason, ident, sha,
                     max_http, max_attempts)
    _print_summary(records, total, stop_reason)
    return 1 if stop_reason else 0


def _record_case(case: Case, env: dict | None, err: str | None,
                 obs, delta: dict) -> dict:
    az = obs.analyze() or {}
    cz = obs.classify() or {}
    recl = obs.reclassify_attempted()
    sim_attempts = obs.simulate_attempts()
    status = (env or {}).get("status") if env else ("error" if err else None)
    route = (env or {}).get("simulation_id")
    config = (env or {}).get("config") if env else None
    fail_cat = (env or {}).get("failure_category")

    rec = {
        "case_id": case.cid, "kind": case.kind, "prompt": case.prompt(),
        "http": delta["http"], "logical_calls": delta["logical"],
        "retry": delta["retry"], "transient": delta["transient"],
        "analyze_result_ownership": az.get("result_ownership"),
        "analyze_prescribed": az.get("prescribed_procedure"),
        "initial_route": cz.get("simulation_id"),
        "final_route": route,
        "reclassification": 1 if recl else 0,
        "simulate_attempts": len(sim_attempts),
        "status": status, "failure_category": fail_cat,
        "pipeline_error": err,
        "learner_reason": (env or {}).get("reason") or (env or {}).get("learner_reason"),
    }

    if case.kind == "supported":
        passed = True
        problems = []
        if status != "ok":
            passed = False
            problems.append(f"status={status} (mong ok)")
        if route != case.expected_route:
            passed = False
            problems.append(f"route={route}")
        gm = leak = ops = final = oracle_agree = None
        if isinstance(config, dict) and route == case.expected_route:
            gm = grounding_matrix(case, config)
            leak = leakage_scan(config)
            ops = _ops_from_config(config)
            final = _actual_final(config)
            # independent oracle (bảng NGUỒN + query của TA) đã khóa = expected_final
            oracle_agree = (case.expected_final == _final_from_engine(case.oracle_config()))
            if not gm["grounding_perfect"]:
                passed = False
                problems.append("grounding không hoàn hảo")
            if leak:
                passed = False
                problems.append(f"rò rỉ kết quả: {leak}")
            if final != case.expected_final:
                passed = False
                problems.append("engine final ≠ expected (operation/spec sai)")
        else:
            passed = False
            problems.append("không có config hợp lệ để audit")
        rec.update({
            "grounding": gm, "leakage": leak or [], "operations": ops,
            "expected_operations": case.expected_ops,
            "expected_final": case.expected_final, "actual_final": final,
            "oracle_agreement": oracle_agree,
            "result_leakage": bool(leak),
            "generic_leak": route == "generic.rule_scene",
            "false_positive_simulation": False,
            "false_refusal": status == "unsupported",
            "passed": passed, "problems": problems,
        })
    else:
        passed = True
        problems = []
        if status != "unsupported":
            passed = False
            problems.append(f"status={status} (mong unsupported)")
        if fail_cat != case.refusal_category:
            passed = False
            problems.append(f"failure_category={fail_cat} (mong {case.refusal_category})")
        if isinstance(config, dict):
            passed = False
            problems.append("có config khi lẽ ra phải từ chối")
        rec.update({
            "generic_leak": route == "generic.rule_scene",
            "false_positive_simulation": status == "ok",
            "false_refusal": False,
            "passed": passed, "problems": problems,
        })
    return rec


def _stop_check(case: Case, rec: dict) -> str | None:
    """§12 — điều kiện DỪNG NGAY. Trả lý do hoặc None."""
    if case.kind == "supported":
        gm = rec.get("grounding")
        if rec["final_route"] == "generic.rule_scene":
            return "route sang generic"
        if gm:
            if gm["modified_cells"] or gm["added_rows"] or gm["dropped_rows"]:
                return "supported case mất/thêm/sửa cell"
            if gm["empty_to_zero"]:
                return "ô trống biến thành 0"
            if gm["added_columns"] or gm["dropped_columns"]:
                return "schema mất/thêm cột"
        if rec.get("result_leakage"):
            return "candidate spec chứa final result"
    else:
        if rec["status"] == "ok":
            return ("insufficient prompt tự sinh bảng" if case.cid == "L5"
                    else "multi-goal chạy một nửa")
        if rec["final_route"] == "generic.rule_scene":
            return "route sang generic"
    return None


# ════════════════════════════════════════════════════════════════════════
# ARTIFACTS + SUMMARY
# ════════════════════════════════════════════════════════════════════════
def _summ(records, total, stop_reason):
    supported = [r for r in records if r["kind"] == "supported"]
    negative = [r for r in records if r["kind"] == "refusal"]
    passed = [r for r in records if r["passed"]]
    return {
        "cases_run": len(records), "cases_passed": len(passed),
        "supported_run": len(supported),
        "supported_passed": sum(1 for r in supported if r["passed"]),
        "negative_run": len(negative),
        "negative_passed": sum(1 for r in negative if r["passed"]),
        "total_http": total["http"], "total_logical": total["logical"],
        "retry": total["retry"], "transient": total["transient"],
        "reclassification": sum(r["reclassification"] for r in records),
        "routing_accuracy": _rate(
            sum(1 for r in records
                if (r["kind"] == "supported" and r["final_route"] == "database.relational_table_query")
                or (r["kind"] == "refusal" and r["status"] == "unsupported")),
            len(records)),
        "grounding_accuracy": _rate(
            sum(1 for r in supported if r.get("grounding") and r["grounding"]["grounding_perfect"]),
            len(supported)),
        "generic_leak": sum(1 for r in records if r.get("generic_leak")),
        "false_positive_simulation": sum(1 for r in records if r.get("false_positive_simulation")),
        "false_refusal": sum(1 for r in records if r.get("false_refusal")),
        "result_leakage": sum(1 for r in supported if r.get("result_leakage")),
        "stop_reason": stop_reason,
        "all_passed": len(passed) == len(records) and stop_reason is None and len(records) == len(CASES),
    }


def _rate(num, den):
    return None if den == 0 else round(num / den, 4)


def _write_artifacts(out_dir, records, total, stop_reason, ident, sha,
                     max_http, max_attempts):
    out_dir.mkdir(parents=True, exist_ok=True)
    summ = _summ(records, total, stop_reason)
    run_meta = {
        "wave": "M17 W2B-LIVE", "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": "gemini-2.5-flash", "execution_environment": "local_python",
        "git_sha": sha, "cache_version": ident["cache_version"],
        "family_count": ident["family_count"], "target_count": ident["target_count"],
        "stable_catalog_hash": ident["stable_catalog_hash"],
        "budget": {"max_cases": len(CASES), "max_http": max_http,
                   "max_attempts_per_call": max_attempts},
        "note": ("run_pipeline production (invariant #22) gọi trực tiếp trong "
                 "process local; danh tính container xác minh RIÊNG bằng "
                 "runtime_doctor. Không tuyên bố container parity ngoài kết quả "
                 "doctor."),
    }
    (out_dir / "live_table_query.json").write_text(
        json.dumps({"run_meta": run_meta, "summary": summ, "cases": records},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # grounding matrix riêng
    matrix = {r["case_id"]: r.get("grounding") for r in records
              if r["kind"] == "supported"}
    (out_dir / "live_table_grounding_matrix.json").write_text(
        json.dumps({"run_meta": run_meta, "matrix": matrix,
                    "acceptance": {
                        "row_preservation": _rate(sum(1 for m in matrix.values() if m and m["row_preservation"]), len(matrix)),
                        "column_preservation": _rate(sum(1 for m in matrix.values() if m and m["column_preservation"]), len(matrix)),
                        "grounding_perfect": _rate(sum(1 for m in matrix.values() if m and m["grounding_perfect"]), len(matrix)),
                    }}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    _write_report_md(out_dir, run_meta, summ, records)
    _write_ledger_md(out_dir, records, stop_reason)


def _write_report_md(out_dir, meta, summ, records):
    L = [
        "# M17 W2B-LIVE — Grounding Verification `database.relational_table_query`", "",
        "Kiểm chứng production LLM orchestration THẬT có grounding trung thực — "
        "không phải routing smoke.", "",
        f"- Model **{meta['model']}** · env **{meta['execution_environment']}** · "
        f"SHA `{meta['git_sha'][:12]}` · cache **{meta['cache_version']}** · "
        f"family **{meta['family_count']}** · target **{meta['target_count']}** · "
        f"hash `{meta['stable_catalog_hash'][:12]}`",
        f"- Case **{summ['cases_passed']}/{summ['cases_run']}** đạt · "
        f"supported **{summ['supported_passed']}/{summ['supported_run']}** · "
        f"negative **{summ['negative_passed']}/{summ['negative_run']}**",
        f"- HTTP **{summ['total_http']}** · retry **{summ['retry']}** · "
        f"transient **{summ['transient']}** · reclassification **{summ['reclassification']}**",
        f"- routing **{summ['routing_accuracy']}** · grounding **{summ['grounding_accuracy']}** · "
        f"generic-leak **{summ['generic_leak']}** · false-positive-sim "
        f"**{summ['false_positive_simulation']}** · false-refusal **{summ['false_refusal']}** · "
        f"result-leakage **{summ['result_leakage']}**",
        f"- STOP: **{summ['stop_reason'] or 'không'}** · all_passed: "
        f"**{summ['all_passed']}**", "",
        "| Case | Loại | HTTP | route | grounding | leak | final | đạt |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in records:
        if r["kind"] == "supported":
            gm = r.get("grounding")
            g = "perfect" if gm and gm["grounding_perfect"] else "LỖI"
            fin = "khớp" if r.get("actual_final") == r.get("expected_final") else "LỆCH"
            leak = "—" if not r.get("leakage") else ",".join(r["leakage"])
            L.append(f"| {r['case_id']} | supported | {r['http']} | "
                     f"`{r['final_route']}` | {g} | {leak} | {fin} | "
                     f"{'✔' if r['passed'] else '✘'} |")
        else:
            L.append(f"| {r['case_id']} | refusal | {r['http']} | "
                     f"{r['status']}/{r['failure_category']} | — | — | — | "
                     f"{'✔' if r['passed'] else '✘'} |")
    L += ["", "## Chi tiết từng case", ""]
    for r in records:
        L.append(f"### {r['case_id']} — {'ĐẠT' if r['passed'] else 'KHÔNG ĐẠT'}")
        L.append(f"- prompt: `{r['prompt'].splitlines()[-1]}`")
        L.append(f"- route: initial=`{r['initial_route']}` → final=`{r['final_route']}` · "
                 f"reclassify={r['reclassification']} · simulate_attempts={r['simulate_attempts']}")
        L.append(f"- analyze: result_ownership={r['analyze_result_ownership']!r} · "
                 f"prescribed={r['analyze_prescribed']!r}")
        if r["kind"] == "supported":
            gm = r.get("grounding") or {}
            L.append(f"- grounding: rows {gm.get('source_rows')}→{gm.get('spec_rows')} · "
                     f"cols {gm.get('source_columns')}→{gm.get('spec_columns')} · "
                     f"cells {gm.get('cells_compared')} · "
                     f"modified={len(gm.get('modified_cells', []))} · "
                     f"empty→0={len(gm.get('empty_to_zero', []))} · "
                     f"added/dropped rows={gm.get('added_rows')}/{gm.get('dropped_rows')} · "
                     f"type_mismatch={len(gm.get('type_mismatches', []))}")
            L.append(f"- operations: {r.get('operations')}  (mong {r.get('expected_operations')})")
            L.append(f"- executor: expected_final={r.get('expected_final')} · "
                     f"actual_final={r.get('actual_final')} · "
                     f"oracle_agreement={r.get('oracle_agreement')} · "
                     f"leakage={r.get('leakage')}")
        else:
            L.append(f"- learner_reason: {r.get('learner_reason')!r}")
        if r["problems"]:
            L.append(f"- **VẤN ĐỀ:** {r['problems']}")
        L.append("")
    (out_dir / "live_table_query_report.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def _write_ledger_md(out_dir, records, stop_reason):
    fails = [r for r in records if not r["passed"]]
    L = ["# M17 W2B-LIVE — Failure ledger", "",
         f"STOP: **{stop_reason or 'không'}** · case KHÔNG đạt: **{len(fails)}**", ""]
    if not fails:
        L.append("Không có case nào thất bại. Grounding/authenticity/routing/refusal "
                 "đều đạt trong ngân sách.")
    else:
        L.append("Phân loại lỗi (KHÔNG tự sửa fixture/tolerance; KHÔNG sửa "
                 "production code trong cùng run):")
        L.append("")
        for r in fails:
            cat = _classify_failure(r)
            L.append(f"## {r['case_id']} — {cat}")
            L.append(f"- vấn đề: {r['problems']}")
            if r.get("grounding"):
                gm = r["grounding"]
                if gm["modified_cells"]:
                    L.append(f"- modified_cells: {gm['modified_cells']}")
                if gm["empty_to_zero"]:
                    L.append(f"- empty_to_zero: {gm['empty_to_zero']}")
                if gm["added_columns"] or gm["dropped_columns"]:
                    L.append(f"- cột +{gm['added_columns']} / -{gm['dropped_columns']}")
            L.append("")
    (out_dir / "live_table_failure_ledger.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def _classify_failure(r: dict) -> str:
    if r["kind"] == "supported":
        gm = r.get("grounding")
        if gm and gm.get("empty_to_zero"):
            return "type-coercion error (empty→0)"
        if gm and (gm.get("added_columns") or gm.get("dropped_columns")):
            return "analyze extraction error (schema)"
        if gm and gm.get("modified_cells"):
            return "analyze extraction error (cell)"
        if gm and gm.get("type_mismatches"):
            return "type-coercion error (column type)"
        if r.get("result_leakage"):
            return "spec generation error (result leakage)"
        if r.get("actual_final") != r.get("expected_final"):
            return "spec generation error (operation)"
        if r["final_route"] != "database.relational_table_query":
            return "routing error"
    return "refusal/routing error"


def _print_summary(records, total, stop_reason):
    summ = _summ(records, total, stop_reason)
    print("\n=== M17 W2B-LIVE SUMMARY ===")
    print(f"cases {summ['cases_passed']}/{summ['cases_run']} · "
          f"supported {summ['supported_passed']}/{summ['supported_run']} · "
          f"negative {summ['negative_passed']}/{summ['negative_run']}")
    print(f"HTTP {summ['total_http']} · retry {summ['retry']} · "
          f"transient {summ['transient']} · reclassify {summ['reclassification']}")
    print(f"routing {summ['routing_accuracy']} · grounding {summ['grounding_accuracy']} · "
          f"generic-leak {summ['generic_leak']} · fp-sim {summ['false_positive_simulation']} · "
          f"false-refusal {summ['false_refusal']} · result-leak {summ['result_leakage']}")
    print(f"STOP: {stop_reason or 'không'} · all_passed: {summ['all_passed']}")
    for r in records:
        print(f"  [{r['case_id']}] {'ĐẠT' if r['passed'] else 'KHÔNG ĐẠT'} · "
              f"http={r['http']} · {r['problems'] if r['problems'] else 'ok'}")


def _selftest() -> int:
    """Chạy TOÀN BỘ máy audit (grounding/leak/authenticity) trên config ORACLE
    của chính ta — KHÔNG API. Config đúng ⇒ grounding perfect, 0 leak, final
    khớp. Bắt lỗi code TRƯỚC khi đốt budget; đồng thời chứng minh khi FAULT
    (đổi ô/empty→0/thêm cột) máy audit BIẾT KÊU."""
    lock_expected()
    ok = True
    for c in CASES:
        if c.kind != "supported":
            continue
        cfg = c.oracle_config()
        gm = grounding_matrix(c, cfg)
        leak = leakage_scan(cfg)
        final = _actual_final(cfg)
        good = gm["grounding_perfect"] and not leak and final == c.expected_final
        print(f"[{c.cid}] clean: grounding_perfect={gm['grounding_perfect']} "
              f"leak={leak} final_match={final == c.expected_final} → "
              f"{'OK' if good else 'LỖI CODE'}")
        ok = ok and good
        # FAULT INJECTION — máy audit phải phát hiện:
        import copy
        # 1) đổi một ô số
        f1 = copy.deepcopy(cfg)
        num_key = next((col["name"] for col in f1["schema"] if col["type"] == "number"), None)
        if num_key:
            for row in f1["rows"]:
                if row.get(num_key) is not None:
                    row[num_key] = 999999
                    break
            g1 = grounding_matrix(c, f1)
            assert g1["modified_cells"], f"{c.cid}: fault ô số KHÔNG bị bắt"
        # 2) empty→0
        f2 = copy.deepcopy(cfg)
        hit = False
        for row in f2["rows"]:
            for k in list(row):
                if row[k] is None:
                    row[k] = 0
                    hit = True
        if hit:
            g2 = grounding_matrix(c, f2)
            assert g2["empty_to_zero"], f"{c.cid}: fault empty→0 KHÔNG bị bắt"
        # 3) thêm cột lạ
        f3 = copy.deepcopy(cfg)
        f3["schema"].append({"name": "x_extra", "type": "text", "label": "Cột lạ"})
        for row in f3["rows"]:
            row["x_extra"] = "z"
        g3 = grounding_matrix(c, f3)
        assert g3["added_columns"], f"{c.cid}: fault thêm cột KHÔNG bị bắt"
        # 4) rò rỉ kết quả
        f4 = copy.deepcopy(cfg)
        f4["aggregateResult"] = {"value": 1, "counted": 1}
        assert leakage_scan(f4), f"{c.cid}: rò rỉ aggregateResult KHÔNG bị bắt"
    print("\nselftest:", "PASS (audit đúng + biết kêu khi fault)" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--lock", action="store_true", help="Chỉ khóa expected (offline)")
    p.add_argument("--selftest", action="store_true", help="Tự kiểm máy audit (offline)")
    p.add_argument("--live", action="store_true", help="Chạy live (cần opt-in)")
    p.add_argument("--out", default=str(ROOT / "docs/evaluation/m17/rc1"))
    p.add_argument("--max-http", type=int, default=20)
    p.add_argument("--max-attempts", type=int, default=2)
    args = p.parse_args()
    if args.lock:
        return _print_lock()
    if args.selftest:
        return _selftest()
    if args.live:
        return asyncio.run(run_live(Path(args.out), args.max_http, args.max_attempts))
    print("Chọn --lock (offline) hoặc --live (cần ALLOW_LIVE_AI=1).")
    return 2


if __name__ == "__main__":
    sys.exit(main())
