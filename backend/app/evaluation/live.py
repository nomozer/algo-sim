# -*- coding: utf-8 -*-
"""Chạy đánh giá LIVE với Gemini thật (M7 §7, M7.14T).

BẮT BUỘC OPT-IN — không có ALLOW_LIVE_AI=1 thì ABORT trước call đầu tiên:

    ALLOW_LIVE_AI=1 python -m app.evaluation.live --suite smoke
    ALLOW_LIVE_AI=1 python -m app.evaluation.live --suite full --max-api-calls 150

Cần GEMINI_API_KEY (đọc từ backend/.env hoặc biến môi trường). KHÔNG chạy
trong CI. Chỉ sau lệnh này mới có metric AI composition THẬT (§8).

Chính sách chạy live (docs/CORRECTNESS.md §8 / CLAUDE.md): thay đổi UI/CSS/
viewport → KHÔNG cần live; engine/validator tất định → offline trước, live có
mục tiêu nếu chạm hợp đồng AI; prompt/schema/classifier → smoke; kết thúc
milestone lớn/lấy số liệu → full. Không chạy full theo thói quen.

## M16 Task 7 — trace/resume/label (KHÔNG đổi ngữ nghĩa opt-in/budget cũ)

Ba cờ mới, mặc định KHÔNG kích hoạt gì (không truyền = hành vi cũ nguyên vẹn):

- `--label {baseline,postfix}` (mặc định `baseline`) — chỉ ghi vào
  `trace["run_label"]`, không đổi cách chạy.
- `--out <path>` — ghi một trace JSON (`M16CaseRecord` từng case qua
  `evaluate_item(..., record_sink=...)` — Task 2 đã có sẵn tham số này, ở đây
  chỉ NỐI DÂY) + budget cuối run + run_meta. Dùng cho hồ sơ live sau này
  (baseline/postfix) và để `--resume-from` đọc lại.
- `--resume-from <path>` — nạp trace cũ, BỎ QUA case đã `status_final=="ok"`
  VÀ khớp expectation (tái dùng nguyên luật
  `m16_artifacts._outcome_matches_expectation` — KHÔNG chế luật mới), chỉ
  chạy lại case còn thiếu/sai; report budget cộng dồn vào
  `trace["budget_cumulative"]`.

`harness.py` KHÔNG nằm trong phạm vi sửa của Task 7 (`run_eval` không có
tham số `record_sink`) nên khi cần trace, live.py tự lặp qua `evaluate_item`
(`_run_eval_with_records`, bản sao TỐI THIỂU vòng lặp `run_eval`) thay vì gọi
`run_eval` — khi không có `--out`/`--resume-from`, đường gọi CŨ (`run_eval`)
được dùng y nguyên, không có rủi ro lệch hành vi.
"""

from __future__ import annotations

import argparse
import asyncio
import dataclasses
import json
import os
import sys
from datetime import datetime, timezone

from app.persistence.db import init_db  # noqa: F401 (đảm bảo .env được nạp qua db module)
from app.ai import gemini
from app.ai.gemini import ApiBudget, BudgetExceeded
from app.evaluation.dataset import EvalItem
from app.evaluation.datasets import POOLS, get_pool
from app.evaluation.harness import (
    EvalReport,
    ItemResult,
    evaluate_item,
    format_report,
    run_eval,
    select_suite,
)
from app.evaluation.m16_record import M16CaseRecord
from app.evaluation.m16_schema import M16_DATASET_VERSION

# Tái dùng luật outcome-matches-expectation CÓ SẴN của m16_artifacts (brief
# Phụ lục: "dùng đúng luật ... nếu import được, KHÔNG chế luật mới"). Tên có
# gạch dưới (private theo quy ước) nhưng không có vòng import (m16_artifacts
# không import live.py) nên import trực tiếp an toàn — không nhân bản logic.
from app.evaluation.m16_artifacts import _outcome_matches_expectation

SUITES = ("smoke", "full", "boundary", "smoke_v2", "flagship", "L3", "system_flow", "m10_route", "m11_compose", "m12_scan", "m13_soundness", "m14_sorting", "m15_wave1", "m16_offline", "m16_catalog_live")
DATASETS = tuple(sorted(POOLS))

_BUDGET_COUNTERS = ("logical_calls", "http_requests", "retry_requests", "transient_hits")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="python -m app.evaluation.live",
        description="Đánh giá AI composition với Gemini THẬT (cần ALLOW_LIVE_AI=1).",
    )
    p.add_argument("--dataset", choices=DATASETS, default="regression",
                   help="regression (mặc định — 30 case lịch sử, ĐÓNG BĂNG) | curriculum | "
                        "capability | cross_domain | thesis (bộ flagship)")
    p.add_argument("--suite", choices=SUITES, default="smoke",
                   help="full (toàn bộ pool) | hoặc lọc theo tag: smoke | boundary | "
                        "smoke_v2 | flagship | L3 | system_flow")
    p.add_argument("--max-cases", type=int, default=None, help="Chỉ chạy N đề đầu của suite.")
    p.add_argument("--case", default=None,
                   help="Chỉ chạy ĐÚNG MỘT đề theo id (rerun có mục tiêu sau vá — M15 T11).")
    p.add_argument("--max-api-calls", type=int, default=None,
                   help="Trần request HTTP thật; chạm trần → dừng sạch và vẫn in report.")
    p.add_argument("--max-retries", type=int, default=None,
                   help="Trần retry TRANSIENT (429/5xx) mỗi call. KHÔNG đụng 3 lần retry "
                        "validation của pipeline (đó là ngữ nghĩa sản phẩm).")
    p.add_argument("--label", choices=("baseline", "postfix"), default="baseline",
                   help="M16 Task 7 — nhãn run ghi vào trace['run_label']. KHÔNG đổi cách chạy.")
    p.add_argument("--out", default=None,
                   help="M16 Task 7 — ghi trace JSON (M16CaseRecord từng case + budget) ra đường dẫn này.")
    p.add_argument("--resume-from", default=None,
                   help="M16 Task 7 — nạp trace JSON cũ, bỏ qua case đã OK & khớp expectation, "
                        "chỉ chạy lại case còn thiếu/sai.")
    return p.parse_args(argv)


# ── M16 Task 7: helpers trace/resume (KHÔNG đụng harness.py) ───────────────

def _budget_snapshot(budget: ApiBudget | None) -> dict:
    """Giống hệt `harness._budget_snapshot` (M16 Task 2) — nhân bản CÓ CHỦ Ý
    (4 dòng, không đáng để reach vào private của module khác qua ranh giới
    CLI/harness); giữ đúng 4 khoá để không lệch hợp đồng budget_delta."""
    if budget is None:
        return {k: 0 for k in _BUDGET_COUNTERS}
    return {k: getattr(budget, k) for k in _BUDGET_COUNTERS}


def _status_final(record: M16CaseRecord) -> str:
    """"ok" | "refused" | "error" — dẫn xuất TẤT ĐỊNH từ envelope_status
    (brief Phụ lục: status_final ∈ {"ok","refused","error"})."""
    if record.envelope_status == "ok":
        return "ok"
    if record.envelope_status == "unsupported":
        return "refused"
    return "error"


async def _run_eval_with_records(
    items: list[EvalItem], api_key: str, budget: ApiBudget | None, record_sink: list | None
) -> EvalReport:
    """Bản sao TỐI THIỂU vòng lặp `harness.run_eval`, nối thêm `record_sink`
    để `evaluate_item` phát `M16CaseRecord` SONG SONG cho trace mà KHÔNG chạy
    pipeline hai lần. `harness.py` ngoài phạm vi sửa của Task 7 nên không
    thêm tham số `record_sink` ở đó — đường KHÔNG cờ mới (`--out`/
    `--resume-from` đều vắng) tiếp tục gọi `run_eval` gốc, không đi qua hàm
    này, nên hành vi cũ giữ nguyên tuyệt đối."""
    report = EvalReport(planned=len(items))
    for item in items:
        try:
            report.results.append(
                await evaluate_item(item, api_key, budget=budget, record_sink=record_sink)
            )
        except BudgetExceeded as err:  # chạm trần API → DỪNG cả bộ, vẫn in report
            report.aborted_reason = str(err)
            break
        except Exception as err:  # lỗi mạng/pipeline → ghi nhận, không dừng cả bộ
            report.results.append(
                ItemResult(item.id, item.group, None, False, failure="pipeline_error", detail=str(err)[:200])
            )
    if budget is not None:
        report.budget = budget
    return report


def _load_trace(path: str) -> dict | None:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as err:
        print(f"KHÔNG đọc được trace cũ '{path}': {err}")
        return None


def _entry_matches_expectation(entry: dict) -> bool:
    """"đã ĐÚNG expectation" — dựng lại `M16CaseRecord` TỪ dict đã json
    round-trip rồi gọi ĐÚNG luật `_outcome_matches_expectation` của
    m16_artifacts (không phát minh tiêu chí mới). Review Task 7 (Important):
    KHÔNG gate literal `status_final=="ok"` — case unsupported bị TỪ CHỐI ĐÚNG
    có status_final=="refused" và cũng phải được skip (mục đích tiết kiệm
    ngân sách live của --resume-from); "error" tự trượt vì
    `_outcome_matches_expectation` không bao giờ nhận envelope_status=None.
    Entry hỏng/thiếu field (schema trace cũ lệch) → coi như CHƯA khớp (an
    toàn: chạy lại thay vì bỏ sót)."""
    if entry.get("status_final") not in ("ok", "refused"):
        return False
    record_dict = entry.get("record")
    if not isinstance(record_dict, dict):
        return False
    try:
        record = M16CaseRecord(**record_dict)
    except TypeError:
        return False
    return _outcome_matches_expectation(record)


def _split_resume(items: list[EvalItem], old_trace: dict) -> tuple[list[EvalItem], list[dict]]:
    """Trả (case cần chạy lại, entry trace cũ được GIỮ NGUYÊN vì đã OK+khớp)."""
    old_by_id = {c.get("case_id"): c for c in (old_trace.get("cases") or []) if isinstance(c, dict)}
    to_run: list[EvalItem] = []
    kept: list[dict] = []
    for it in items:
        entry = old_by_id.get(it.id)
        if entry is not None and _entry_matches_expectation(entry):
            kept.append(entry)
        else:
            to_run.append(it)
    return to_run, kept


def _sum_budget(old_trace: dict, budget: ApiBudget) -> dict:
    old_cumulative = old_trace.get("budget_cumulative") or old_trace.get("budget") or {}
    new = _budget_snapshot(budget)
    return {k: int(old_cumulative.get(k, 0) or 0) + new[k] for k in _BUDGET_COUNTERS}


def _write_trace(
    path: str,
    args: argparse.Namespace,
    all_items: list[EvalItem],
    sink: list,
    kept_entries: list[dict],
    budget: ApiBudget,
    old_trace: dict | None,
    started_at: str,
) -> None:
    """Ghi trace JSON đúng schema Phụ lục brief: schema_version/dataset_version/
    run_label/run_meta/budget/cases(+budget_cumulative khi resume). `cases`
    giữ THỨ TỰ `all_items` (đề đã chọn qua --dataset/--suite/--case/--max-cases,
    TRƯỚC khi lọc resume) — mỗi id là entry cũ được giữ (kept) hoặc record mới
    chạy trong phiên này (sink); case chưa chạy tới (vd dừng sớm vì chạm trần)
    không xuất hiện — lần resume sau coi như "chưa có trong trace" nên tự
    động chạy lại, không cần xử lý đặc biệt."""
    records_by_id = {r.case_id: r for r in sink}
    kept_by_id = {e.get("case_id"): e for e in kept_entries}

    cases: list[dict] = []
    for it in all_items:
        if it.id in kept_by_id:
            cases.append(kept_by_id[it.id])
        elif it.id in records_by_id:
            record = records_by_id[it.id]
            cases.append({
                "case_id": it.id,
                "status_final": _status_final(record),
                "record": dataclasses.asdict(record),
            })

    trace: dict = {
        "schema_version": "1",
        "dataset_version": M16_DATASET_VERSION,
        "run_label": args.label,
        "run_meta": {
            "started_at": started_at,
            "suite": args.suite,
            "dataset": args.dataset,
            "model": gemini.MODEL,
        },
        "budget": _budget_snapshot(budget),
        "cases": cases,
    }
    if old_trace is not None:
        trace["budget_cumulative"] = _sum_budget(old_trace, budget)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(trace, f, ensure_ascii=False, indent=2)


async def _main(args: argparse.Namespace) -> int:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("CHƯA có GEMINI_API_KEY — không thể chạy live evaluation.")
        print("Tạo backend/.env với GEMINI_API_KEY=<key> rồi chạy lại.")
        return 1

    pool = get_pool(args.dataset)
    items = select_suite(args.suite, pool)
    if args.case is not None:
        items = [it for it in items if it.id == args.case]
    if args.max_cases is not None:
        items = items[: max(0, args.max_cases)]
    if not items:
        print(f"Dataset '{args.dataset}' + suite '{args.suite}': không có đề nào.")
        return 1

    old_trace: dict | None = None
    kept_entries: list[dict] = []
    to_run = items
    if args.resume_from is not None:
        old_trace = _load_trace(args.resume_from)
        if old_trace is None:
            return 1
        to_run, kept_entries = _split_resume(items, old_trace)
        print(f"--resume-from '{args.resume_from}': {len(kept_entries)}/{len(items)} case đã OK "
              f"(bỏ qua), {len(to_run)} case chạy lại.\n")

    budget = ApiBudget(
        max_api_calls=args.max_api_calls,
        max_attempts=(args.max_retries + 1) if args.max_retries is not None else None,
    )
    gemini.set_budget(budget)
    started_at = datetime.now(timezone.utc).isoformat()
    print(f"Dataset '{args.dataset}' · suite '{args.suite}': {len(to_run)} đề với Gemini THẬT "
          f"(trần API: {args.max_api_calls or 'không giới hạn'})...\n")

    record_sink: list | None = [] if args.out else None
    try:
        if old_trace is not None or record_sink is not None:
            report = await _run_eval_with_records(to_run, api_key, budget, record_sink)
        else:
            report = await run_eval(items, api_key, budget=budget)
    finally:
        gemini.set_budget(None)  # không để trần rò sang tiến trình khác

    print(format_report(report))

    if args.out:
        _write_trace(args.out, args, items, record_sink or [], kept_entries, budget, old_trace, started_at)
        print(f"\nĐã ghi trace: {args.out}")

    return 2 if report.aborted_reason else 0


def main(argv: list[str] | None = None) -> int:
    # OPT-IN CỨNG (M7.14T §6): không có cờ thì DỪNG, không phải cảnh báo rồi chạy.
    if os.getenv("ALLOW_LIVE_AI") != "1":
        print("TỪ CHỐI: live evaluation gọi Gemini THẬT (tốn quota).")
        print("Chạy lại với opt-in tường minh, ví dụ:")
        print("    ALLOW_LIVE_AI=1 python -m app.evaluation.live --suite smoke")
        return 1
    return asyncio.run(_main(_parse_args(argv)))


if __name__ == "__main__":
    sys.exit(main())
