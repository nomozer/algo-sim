# -*- coding: utf-8 -*-
"""Task 12 — chạy benchmark SEALED ĐÚNG MỘT LẦN, trong ngân sách đã duyệt.

VIẾT TRƯỚC KHI THẤY SEALED, có chủ đích. Một runner viết sau khi đã đọc dữ liệu
thì mọi lựa chọn trong nó — chấm thế nào, tính cái gì là đạt, bỏ qua case nào —
đều có thể bị dẫn dắt bởi thứ đã thấy, và không ai chứng minh được là không.

LUẬT KHI CHẠY (spec §7.4, `freeze_protocol.md`):

    Mở SEALED một lần. Chạy. Báo cáo.
    Case hỏng vì thiếu checker / thiếu primitive / IR không diễn đạt được thì
    GHI ĐÚNG cái hỏng đó. KHÔNG vá rồi chạy lại — một lần vá là con dấu mất
    hiệu lực và phải niêm phong tập mới.

Bốn con số phải báo, và chúng KHÁC NHAU:

    A  — generative executability rate: máy dựng được mô phỏng chạy được
    B  — safe serve rate: đủ bằng chứng để phát canonical
    D1 — token/case của route ngữ nghĩa
    D2 — so token với đường module, CHỈ trên matched subset

A ≥ B luôn đúng, và khoảng cách giữa chúng chính là `verification_gap`.

    cd backend && ALLOW_LIVE_AI=1 PYTHONIOENCODING=utf-8 \\
      .venv/Scripts/python.exe scripts/run_sealed_evaluation.py \\
      --out-dir ../docs/evaluation/semantic-benchmark/results
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
BENCH = ROOT / "docs" / "evaluation" / "semantic-benchmark"
SEALED = BENCH / "sealed" / "cases.json"
FINGERPRINT = BENCH / "sealed" / "FINGERPRINT.txt"

sys.path.insert(0, str(BACKEND))

#: Ngân sách đã duyệt 2026-08-21. Sửa hai số này SAU khi thấy kết quả là mua
#: thêm lượt cho tới khi số đẹp — xem `freeze_protocol.md §2`.
TRAN_LOGIC = 160
TRAN_HTTP = 200
LUOT_MOI_CASE = 4


class DungSach(RuntimeError):
    """Dừng có kiểm soát — đã ghi lý do, không phải crash."""


def _bat_buoc_live() -> None:
    if os.environ.get("ALLOW_LIVE_AI") != "1":
        raise DungSach(
            "Thiếu ALLOW_LIVE_AI=1. Lượt này TIÊU QUOTA THẬT và chỉ được chạy "
            "một lần trên SEALED."
        )
    if not os.environ.get("GEMINI_API_KEY"):
        # `.env` được nạp ở dưới; đây chỉ là lời nhắc sớm.
        pass


def _kiem_candidate() -> dict:
    """Candidate phải KHỚP bản đã đóng băng, nếu không thì không biết đang đo gì."""
    kq = subprocess.run(
        [sys.executable, str(BACKEND / "scripts" / "freeze_evaluation_candidate.py"),
         "--verify"],
        cwd=BACKEND, capture_output=True, text=True,
    )
    if kq.returncode != 0:
        raise DungSach(
            "EVALUATION_CANDIDATE lệch so với mã hiện tại:\n"
            f"{kq.stdout}{kq.stderr}\n"
            "Đóng băng lại TRƯỚC khi mở SEALED — sau khi mở thì mọi thay đổi hệ "
            "đều vi phạm luật con dấu."
        )
    return json.loads((BENCH / "EVALUATION_CANDIDATE.json").read_text(encoding="utf-8"))


def _duong_ngan(p: Path) -> str:
    """Đường dẫn gọn để in. KHÔNG được ném — một script chỉ chạy một lần mà vỡ
    lúc đang dựng thông báo lỗi thì mất luôn cả thông báo."""
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def _kiem_seal() -> str:
    if not SEALED.exists():
        raise DungSach(
            f"Chưa có {_duong_ngan(SEALED)}. SEALED do CUSTODIAN ĐỘC LẬP "
            "chuẩn bị và niêm phong ngoài ngữ cảnh phát triển — xem README.md."
        )
    van_tay = hashlib.sha256(SEALED.read_bytes()).hexdigest()
    if not FINGERPRINT.exists():
        raise DungSach(
            "Có cases.json nhưng KHÔNG có FINGERPRINT.txt. Một tập chưa niêm "
            "phong thì không chứng minh được là nó chưa bị sửa sau khi thấy số."
        )
    da_niem = FINGERPRINT.read_text(encoding="utf-8").strip().split()[0]
    if da_niem != van_tay:
        raise DungSach(
            f"SEALED đã BỊ SỬA sau khi niêm phong.\n  niêm phong: {da_niem}\n"
            f"  hiện tại:   {van_tay}\nCon dấu mất hiệu lực; phải niêm phong tập mới."
        )
    return van_tay


def _chuan(v):
    """So sánh không phụ thuộc list/tuple và không phụ thuộc str/số."""
    from app.simulation.semantic_program.request_contract import norm_value

    if isinstance(v, (list, tuple)):
        return [_chuan(x) for x in v]
    if isinstance(v, dict):
        return {k: _chuan(x) for k, x in v.items()}
    return norm_value(v)


def _cham(case: dict, outcome) -> dict:
    """So kết quả máy với ground truth ĐỘC LẬP.

    Chỉ hỗ trợ dạng `expected` = ánh xạ biến-bộ-nhớ → giá trị. Dạng khác trả
    `UNGRADED` và được đếm RIÊNG — đoán bừa rồi tính là đạt thì con số B mất
    nghĩa, mà tính là trượt thì vu oan cho hệ.
    """
    gt = case.get("ground_truth") or {}
    expected = gt.get("expected")
    if not isinstance(expected, dict) or not expected:
        return {"verdict": "UNGRADED", "ly_do": "ground_truth.expected không phải "
                "ánh xạ biến → giá trị"}

    if outcome is None or outcome.final_memory is None:
        return {"verdict": "NO_RESULT", "ly_do": "route không sinh được kết quả"}

    lech = []
    for ten, mong in expected.items():
        thuc = outcome.final_memory.get(ten, "<KHÔNG CÓ BIẾN NÀY>")
        if _chuan(thuc) != _chuan(mong):
            lech.append(f"{ten}: máy={thuc!r} · đúng={mong!r}")
    return {"verdict": "PASS" if not lech else "FAIL", "lech": lech}


class _Thu:
    """Observer THỤ ĐỘNG (bất biến #22) — chỉ thu, không đổi routing."""

    def __init__(self):
        self.events: list[tuple[str, dict]] = []

    def emit(self, name, data):
        self.events.append((name, data))

    def dau_tien(self, name):
        return next((d for n, d in self.events if n == name), None)


async def _chay_mot_case(case: dict, api_key: str) -> dict:
    from app.ai import pipeline
    from app.ai.telemetry import reset_usage, usage_report
    from app.simulation.semantic_program.route import verify_and_compile  # noqa: F401

    reset_usage()
    thu = _Thu()
    text = case["problem_text"]

    loi = None
    env = None
    try:
        # SHADOW: route chạy đủ cổng và thu đủ bằng chứng, nhưng đầu ra trả về
        # vẫn là đường cũ — nên MỘT lượt chạy đo được CẢ HAI route, và không
        # lượt nào phải chạy hai lần.
        env = await pipeline.run_pipeline(
            text, api_key, observer=thu, semantic_route="shadow"
        )
    except Exception as e:  # noqa: BLE001 — hỏng một case không được giết cả lượt
        loi = f"{type(e).__name__}: {e}"

    ghi = thu.dau_tien("semantic_route")
    outcome = _outcome_tu_event(ghi)

    return {
        "case_id": case.get("case_id"),
        "source": case.get("source"),
        "loi_runner": loi,
        "legacy": {
            "status": (env or {}).get("status"),
            "simulation_id": (env or {}).get("simulation_id"),
            "failure_category": (env or {}).get("failure_category"),
        },
        "semantic": ghi,
        "cham": _cham(case, outcome),
        "token": usage_report(),
    }


class _OutcomeNhe:
    """Đủ để chấm — event của observer đã phẳng hoá `SemanticRouteOutcome`."""

    def __init__(self, d: dict):
        self.final_memory = d.get("final_memory")
        self.executable = bool(d.get("executable"))
        self.servable = bool(d.get("servable"))


def _outcome_tu_event(ghi: dict | None):
    return _OutcomeNhe(ghi) if ghi else None


def _tong_ket(ket_qua: list[dict], candidate: dict, van_tay: str,
              budget, dung_som: str | None) -> dict:
    n = len(ket_qua)
    thuc_thi = [r for r in ket_qua if (r["semantic"] or {}).get("executable")]
    phat = [r for r in ket_qua if (r["semantic"] or {}).get("servable")]
    dung = [r for r in ket_qua if r["cham"]["verdict"] == "PASS"]
    sai = [r for r in ket_qua if r["cham"]["verdict"] == "FAIL"]
    chua_cham = [r for r in ket_qua if r["cham"]["verdict"] == "UNGRADED"]

    def _tok(r) -> int:
        return sum(v.get("total_tokens", 0) for v in (r["token"] or {}).values())

    def _tok_stage(r, stages) -> int:
        return sum(v.get("total_tokens", 0)
                   for k, v in (r["token"] or {}).items() if k in stages)

    # D2 — matched subset: CHỈ case cả hai route đều phục vụ thành công. Quy tắc
    # chọn đã khoá trước ở `freeze_protocol.md §3`; không chọn lại theo kết quả.
    giao = sorted(
        (r for r in ket_qua
         if (r["semantic"] or {}).get("servable") and r["legacy"]["status"] == "ok"),
        key=lambda r: str(r["case_id"]),
    )
    if len(giao) > 12:
        m = len(giao)
        chi_so = sorted({round(i * (m - 1) / 11) for i in range(12)})
        giao = [giao[i] for i in chi_so]

    return {
        "chay_luc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "candidate_commit": candidate.get("commit_ngan"),
        "cache_version": candidate.get("cache_version"),
        "sealed_fingerprint": van_tay,
        "dung_som": dung_som,
        "ngan_sach": {
            "tran_logic": TRAN_LOGIC,
            "tran_http": TRAN_HTTP,
            "logic_da_dung": getattr(budget, "logical_calls", None),
            "http_da_dung": getattr(budget, "http_requests", None),
            "retry": getattr(budget, "retry_requests", None),
        },
        "N": n,
        "A_generative_executability": {
            "so": len(thuc_thi), "tren": n,
            "ti_le": round(len(thuc_thi) / n, 4) if n else None,
        },
        "B_safe_serve": {
            "so": len(phat), "tren": n,
            "ti_le": round(len(phat) / n, 4) if n else None,
            "ghi_chu": "A - B = verification_gap. Hai con số này KHÔNG được gộp.",
        },
        "dung_so_voi_ground_truth": {
            "pass": len(dung), "fail": len(sai), "ungraded": len(chua_cham),
            "ghi_chu": "UNGRADED đếm RIÊNG — không tính vào tử số lẫn mẫu số của "
                       "bất kỳ tỉ lệ nào.",
        },
        "D1_token_case_ngu_nghia": {
            "trung_binh": round(sum(_tok(r) for r in ket_qua) / n, 1) if n else None,
            "chi_stage_ngu_nghia": round(
                sum(_tok_stage(r, {"semantic_analyze", "semantic_program"})
                    for r in ket_qua) / n, 1) if n else None,
        },
        "D2_matched_subset": {
            "so_case": len(giao),
            "case_id": [r["case_id"] for r in giao],
            "ngu_nghia": sum(_tok_stage(r, {"semantic_analyze", "semantic_program"})
                             for r in giao),
            "module": sum(_tok_stage(r, {"simulate", "simulate_family"}) for r in giao),
            "chung": sum(_tok_stage(r, {"analyze", "classify"}) for r in giao),
            "ghi_chu": "Ba con số báo RIÊNG. Tập giao rỗng là một KẾT QUẢ hợp lệ "
                       "và phải được ghi đúng như thế, không phải lỗi runner.",
        },
        "phan_bo_that_bai": _phan_bo(ket_qua),
    }


def _phan_bo(ket_qua: list[dict]) -> dict:
    bo: dict[str, int] = {}
    for r in ket_qua:
        s = r["semantic"] or {}
        if s.get("servable"):
            continue
        khoa = s.get("error_code") or ("KHONG_DUNG_DUOC_IR" if not s else "?")
        bo[khoa] = bo.get(khoa, 0) + 1
    return dict(sorted(bo.items(), key=lambda kv: -kv[1]))


async def _main_async(args) -> int:
    from app.ai import gemini

    _bat_buoc_live()
    candidate = _kiem_candidate()
    van_tay = _kiem_seal()

    cases = json.loads(SEALED.read_text(encoding="utf-8"))["cases"]
    print(f"SEALED: {len(cases)} case · vân tay {van_tay[:16]}")
    print(f"Candidate: {candidate['commit_ngan']} · CACHE_VERSION {candidate['cache_version']}")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise DungSach("Thiếu GEMINI_API_KEY (đặt trong backend/.env).")

    budget = gemini.ApiBudget(max_api_calls=TRAN_HTTP)
    gemini.set_budget(budget)

    ket_qua: list[dict] = []
    dung_som = None
    try:
        for i, case in enumerate(cases, 1):
            # Trần LOGIC kiểm trước mỗi case: chặn giữa chừng một case thì lượt
            # ấy vừa tốn quota vừa không dùng được.
            if budget.logical_calls + LUOT_MOI_CASE > TRAN_LOGIC:
                dung_som = (
                    f"BUDGET_EXHAUSTED: đã dùng {budget.logical_calls} lượt logic, "
                    f"case tiếp theo cần {LUOT_MOI_CASE} nữa, trần {TRAN_LOGIC}."
                )
                print(f"\n{dung_som}")
                break
            print(f"[{i}/{len(cases)}] {case.get('case_id')}", flush=True)
            ket_qua.append(await _chay_mot_case(case, api_key))
    except gemini.BudgetExceeded as e:
        dung_som = f"BUDGET_EXHAUSTED (HTTP): {e}"
        print(f"\n{dung_som}")
    finally:
        gemini.set_budget(None)

    bao_cao = _tong_ket(ket_qua, candidate, van_tay, budget, dung_som)

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "sealed_summary.json").write_text(
        json.dumps(bao_cao, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "sealed_cases.json").write_text(
        json.dumps(ket_qua, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("\n── KẾT QUẢ ──")
    print(f"  N                     {bao_cao['N']}")
    print(f"  A executability       {bao_cao['A_generative_executability']}")
    print(f"  B safe serve          {bao_cao['B_safe_serve']['so']}/{bao_cao['N']}")
    print(f"  đúng/sai/chưa chấm    {bao_cao['dung_so_voi_ground_truth']}")
    print(f"  D1 token/case         {bao_cao['D1_token_case_ngu_nghia']}")
    print(f"  D2 matched subset     {bao_cao['D2_matched_subset']['so_case']} case")
    print(f"  phân bố thất bại      {bao_cao['phan_bo_that_bai']}")
    print(f"  ngân sách             {bao_cao['ngan_sach']}")
    print(f"\nĐã ghi: {out}")
    print("\nKHÔNG vá rồi chạy lại. Case hỏng vì thiếu năng lực thì ghi đúng như thế.")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-dir", default=str(BENCH / "results"))
    args = p.parse_args()

    try:
        from dotenv import load_dotenv

        load_dotenv(BACKEND / ".env")
    except ImportError:
        pass

    try:
        return asyncio.run(_main_async(args))
    except DungSach as e:
        print(f"DỪNG: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
