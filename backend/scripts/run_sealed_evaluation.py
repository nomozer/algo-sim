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

Các con số phải báo, và chúng KHÁC NHAU:

    A   — generative executability rate: máy dựng được mô phỏng CHẠY ĐƯỢC
    B   — internal servable rate (STRONG-assurance): qua HẾT cổng nội bộ.
          KHÔNG phải "đúng" — cổng nội bộ không phải oracle độc lập.
    A−B — chạy được nhưng không phát được, PHẢI PHÂN RÃ theo nguyên nhân:
          `verification_gap` (thiếu checker) · C₁b · C₂ · binding/compile.
          Gọi cả khối là `verification_gap` là báo cáo sai — chỉ một nhánh
          trong đó mới là "thiếu cách kiểm chứng".
    oracle độc lập — pass/fail/ungraded/no_result, tách hẳn khỏi B. Case
          `servable=True` mà ground truth nói SAI là con số đáng sợ nhất trong
          báo cáo: nó nói cổng nội bộ chưa đủ.
    D1  — claim CẤU TRÚC: sau khi IR được sinh, interpreter chạy bao nhiêu bước
          cũng không tốn thêm một lượt LLM nào. Kiểm bằng call graph, không
          phải bằng giá đo được. Token/case là telemetry HỖ TRỢ, không phải D1.
    D2  — claim thực nghiệm về token, CHỈ trên matched subset.

A ≥ B luôn đúng. Khoảng cách giữa chúng KHÔNG được gọi bằng một cái tên duy nhất.

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

#: Đường HẠNH PHÚC: analyze + classify + semantic_analyze + semantic_program.
#: Dưới ngần này thì một case chắc chắn không chạy trọn.
LUOT_TOI_THIEU_MOI_CASE = 4

#: UPPER BOUND THẬT, dẫn xuất từ call graph — KHÔNG phải ước lượng:
#:
#:     stage_analyze          `_call_json(retries=1)`         → tối đa 2
#:     stage_classify lần 1   `_call_json(retries=1)`         → tối đa 2
#:     one-route recovery     thêm một stage_classify         → tối đa 2
#:     stage_semantic_analyze không retry                     → 1
#:     stage_semantic_program không retry                     → 1
#:     stage_simulate*        `for _attempt in range(3)`      → tối đa 3
#:                                                              ─────────
#:                                                              tối đa 11
#:
#: Hệ quả phải nói thẳng: trần 160 chỉ đủ cho 40 case Ở ĐÚNG ĐƯỜNG HẠNH PHÚC
#: (4 × 40 = 160), không còn một slot dự phòng. Retry ở bất kỳ đâu ⇒ lượt chạy
#: dừng trước case thứ 40 và `evaluation_complete` = false. Đó là hành vi ĐÚNG
#: theo ngân sách đã duyệt, không phải lỗi — nhưng phải biết trước khi chạy.
LUOT_TOI_DA_MOI_CASE = 11


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


def _cham(case: dict, contract_event: dict | None, outcome) -> dict:
    """So kết quả máy với ground truth ĐỘC LẬP — KHÔNG phụ thuộc tên biến.

    VÌ SAO KHÔNG NHẬN `{tên_biến: giá_trị}`: tên biến trong bộ nhớ do LLM tự
    đặt. Một chương trình hoàn toàn đúng gọi biến là `ket_qua` trong khi custodian
    ghi `max_value` sẽ FAIL oan — và cái FAIL oan ấy đi thẳng vào con số chính
    của luận văn. Custodian không được phép phải đoán tên biến của LLM.

    Hợp đồng đúng: custodian khai **nghĩa vụ + giá trị đúng**, còn ánh xạ
    nghĩa-vụ → tên-biến thì đọc từ `RequestContract` mà server đã đóng băng::

        "expected": [
          {"obligation_kind": "extremum", "value": 89},
          {"obligation_kind": "aggregate_matching", "value": 3, "index": 0}
        ]

    `index` chỉ cần khi đề có NHIỀU nghĩa vụ cùng loại. Không có index mà nhập
    nhằng ⇒ `UNGRADED`, không đoán.
    """
    gt = case.get("ground_truth") or {}
    expected = gt.get("expected")
    if not isinstance(expected, list) or not expected:
        return {"verdict": "UNGRADED",
                "ly_do": "ground_truth.expected không phải danh sách nghĩa vụ + giá trị"}

    if outcome is None or outcome.final_memory is None:
        return {"verdict": "NO_RESULT", "ly_do": "route không sinh được kết quả"}

    obligations = (contract_event or {}).get("obligations") or []
    lech: list[str] = []
    khong_cham: list[str] = []

    for muc in expected:
        if not isinstance(muc, dict) or "obligation_kind" not in muc:
            khong_cham.append(f"mục kỳ vọng sai dạng: {muc!r}")
            continue
        kind = muc["obligation_kind"]
        ung_vien = [o for o in obligations if o.get("kind") == kind]
        if not ung_vien:
            khong_cham.append(
                f"{kind}: hệ KHÔNG khai nghĩa vụ này nên không có witness để tra"
            )
            continue
        if len(ung_vien) > 1:
            idx = muc.get("index")
            if not isinstance(idx, int) or not (0 <= idx < len(ung_vien)):
                khong_cham.append(
                    f"{kind}: có {len(ung_vien)} nghĩa vụ cùng loại, thiếu `index` "
                    "hợp lệ để chỉ đúng cái nào"
                )
                continue
            ob = ung_vien[idx]
        else:
            ob = ung_vien[0]

        witness = ob.get("witness")
        if not witness:
            khong_cham.append(f"{kind}: nghĩa vụ không có witness")
            continue
        if witness not in outcome.final_memory:
            lech.append(f"{kind} (witness '{witness}'): biến không có trong bộ nhớ cuối")
            continue
        thuc = outcome.final_memory[witness]
        if _chuan(thuc) != _chuan(muc.get("value")):
            lech.append(
                f"{kind} (witness '{witness}'): máy={thuc!r} · đúng={muc.get('value')!r}"
            )

    if lech:
        # Sai CHỨNG MINH ĐƯỢC thắng mọi thứ chưa chấm được: một câu trả lời đã
        # biết là sai thì không còn là "chưa kết luận".
        return {"verdict": "FAIL", "lech": lech, "khong_cham": khong_cham}
    if khong_cham:
        return {"verdict": "UNGRADED", "ly_do": "; ".join(khong_cham)}
    return {"verdict": "PASS", "lech": []}


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
    hop_dong = thu.dau_tien("semantic_contract")
    outcome = _outcome_tu_event(ghi)
    token = usage_report()

    return {
        "case_id": case.get("case_id"),
        "source": case.get("source"),
        "loi_runner": loi,
        "ngat_vi_ngan_sach": bool(loi and "BudgetExceeded" in loi),
        "legacy": {
            "status": (env or {}).get("status"),
            "simulation_id": (env or {}).get("simulation_id"),
            "failure_category": (env or {}).get("failure_category"),
        },
        "semantic": ghi,
        "contract": hop_dong,
        "cham": _cham(case, hop_dong, outcome),
        "token": token,
        # Số LƯỢT LLM của case này — bằng chứng cho claim D1 cấu trúc: nó KHÔNG
        # thay đổi theo số bước mô phỏng.
        "so_luot_llm": sum(v.get("calls", 0) for v in token.values()),
    }


class _OutcomeNhe:
    """Đủ để chấm — event của observer đã phẳng hoá `SemanticRouteOutcome`."""

    def __init__(self, d: dict):
        self.final_memory = d.get("final_memory")
        self.executable = bool(d.get("executable"))
        self.servable = bool(d.get("servable"))


def _outcome_tu_event(ghi: dict | None):
    return _OutcomeNhe(ghi) if ghi else None


#: `stage_reached` → nhóm giải thích "chạy được nhưng KHÔNG phát được".
#: Đây là phân rã của A − B. Gọi cả khối đó là `verification_gap` là SAI: chỉ
#: một nhánh trong đó mới là "thiếu cách kiểm chứng", ba nhánh còn lại là
#: chương trình tự mâu thuẫn hoặc không dựng nổi bề mặt thị giác.
_NHOM_KHONG_PHAT = {
    "verification": "verification_gap",       # thiếu checker độc lập (§5.4)
    "realized_coverage": "C1b_witness_unrealized",
    "postconditions": "C2_postcondition_violated",
    "binding": "binding_unresolved",
    "compile": "compile_failed",
}


def _tong_ket(ket_qua: list[dict], n_planned: int, candidate: dict, van_tay: str,
              budget, dung_som: str | None) -> dict:
    n = len(ket_qua)
    thuc_thi = [r for r in ket_qua if (r["semantic"] or {}).get("executable")]
    phat = [r for r in ket_qua if (r["semantic"] or {}).get("servable")]
    dung = [r for r in ket_qua if r["cham"]["verdict"] == "PASS"]
    sai = [r for r in ket_qua if r["cham"]["verdict"] == "FAIL"]
    chua_cham = [r for r in ket_qua if r["cham"]["verdict"] == "UNGRADED"]
    khong_kq = [r for r in ket_qua if r["cham"]["verdict"] == "NO_RESULT"]

    # A − B: phân rã theo NGUYÊN NHÂN, không gộp thành một nhãn.
    chay_khong_phat = [r for r in thuc_thi if not (r["semantic"] or {}).get("servable")]
    phan_ra: dict[str, int] = {}
    for r in chay_khong_phat:
        stage = (r["semantic"] or {}).get("stage_reached") or "?"
        khoa = _NHOM_KHONG_PHAT.get(stage, f"khac:{stage}")
        phan_ra[khoa] = phan_ra.get(khoa, 0) + 1

    # Đúng/sai theo ORACLE ĐỘC LẬP, tách hẳn khỏi phán quyết nội bộ. Case mà hệ
    # tự cho là phát được NHƯNG ground truth nói sai là con số đáng sợ nhất
    # trong cả báo cáo — nó nói checker nội bộ chưa đủ.
    phat_nhung_sai = [
        r for r in ket_qua
        if (r["semantic"] or {}).get("servable") and r["cham"]["verdict"] == "FAIL"
    ]

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
        "N_planned": n_planned,
        "N_processed": n,
        # Chạy thiếu case mà báo A/B trên mẫu số đã co lại thì con số đọc như
        # thể benchmark chỉ có ngần ấy bài. Protocol đã khoá N=40.
        "evaluation_complete": n == n_planned and dung_som is None,
        "canh_bao": None if (n == n_planned and dung_som is None) else (
            f"LƯỢT CHẠY KHÔNG ĐẦY ĐỦ ({n}/{n_planned}). KHÔNG được công bố A/B "
            "dưới đây như kết quả chính; chúng chỉ mô tả tập con đã chạy."
        ),
        "A_generative_executability": {
            "so": len(thuc_thi), "tren": n,
            "ti_le": round(len(thuc_thi) / n, 4) if n else None,
        },
        "B_internal_servable": {
            "so": len(phat), "tren": n,
            "ti_le": round(len(phat) / n, 4) if n else None,
            "khai": "STRONG-assurance rate — tỉ lệ case QUA HẾT cổng nội bộ. "
                    "ĐÂY KHÔNG PHẢI 'đúng': cổng nội bộ không phải oracle độc "
                    "lập. Xem `dung_theo_oracle_doc_lap`.",
        },
        "A_tru_B_phan_ra": {
            "tong": len(chay_khong_phat),
            "theo_nguyen_nhan": dict(sorted(phan_ra.items(), key=lambda kv: -kv[1])),
            "khai": "Chạy được nhưng không phát được. CHỈ nhánh "
                    "`verification_gap` mới là 'thiếu cách kiểm chứng'; các "
                    "nhánh còn lại là chương trình tự mâu thuẫn (C₁b/C₂) hoặc "
                    "không dựng nổi bề mặt thị giác. Gọi cả khối là "
                    "verification_gap là báo cáo sai.",
        },
        "dung_theo_oracle_doc_lap": {
            "pass": len(dung), "fail": len(sai), "ungraded": len(chua_cham),
            "no_result": len(khong_kq),
            "tong_kiem": len(dung) + len(sai) + len(chua_cham) + len(khong_kq),
            "ti_le_tren_so_cham_duoc": (
                round(len(dung) / (len(dung) + len(sai)), 4)
                if (len(dung) + len(sai)) else None
            ),
            "phat_nhung_oracle_noi_SAI": {
                "so": len(phat_nhung_sai),
                "case_id": [r["case_id"] for r in phat_nhung_sai],
                "khai": "Case hệ tự cho là phát được nhưng ground truth độc lập "
                        "nói sai. Khác 0 ⇒ cổng nội bộ CHƯA ĐỦ, và không được "
                        "viết trong luận văn rằng những case ấy 'an toàn'.",
            },
            "ghi_chu": "UNGRADED/NO_RESULT đếm RIÊNG, không vào tử số lẫn mẫu số. "
                       "`tong_kiem` phải bằng N_processed.",
        },
        "D1_structural_interpreter_khong_ton_token": {
            "khai": "Sau khi IR được sinh, interpreter chạy bao nhiêu bước cũng "
                    "KHÔNG tốn thêm một lượt LLM nào. Đây là claim CẤU TRÚC, "
                    "kiểm bằng call graph, không phải claim thực nghiệm về giá.",
            "so_luot_llm_phan_bo": sorted({r["so_luot_llm"] for r in ket_qua}),
            "so_buoc_min_max": _min_max_buoc(ket_qua),
            "bang_chung": [
                {"case_id": r["case_id"],
                 "so_buoc": (r["semantic"] or {}).get("total_steps"),
                 "so_luot_llm": r["so_luot_llm"]}
                for r in ket_qua if (r["semantic"] or {}).get("total_steps")
            ],
        },
        "semantic_token_per_case": {
            "khai": "Telemetry hỗ trợ, KHÔNG phải D1. Claim thực nghiệm về "
                    "token là D2.",
            "tat_ca_stage": round(sum(_tok(r) for r in ket_qua) / n, 1) if n else None,
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


def _min_max_buoc(ket_qua: list[dict]) -> dict:
    """Khoảng số bước đã chạy. Rộng mà số lượt LLM không nhúc nhích chính là
    bằng chứng của D1 cấu trúc."""
    buoc = [(r["semantic"] or {}).get("total_steps") for r in ket_qua]
    buoc = [b for b in buoc if isinstance(b, int)]
    return {"min": min(buoc), "max": max(buoc)} if buoc else {"min": None, "max": None}


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

    # Trần cưỡng chế ở CẢ HAI trục. Chỉ chặn HTTP là không đủ: pipeline có
    # nhiều tầng retry tự nó (xem LUOT_TOI_DA_MOI_CASE), nên số lượt logic có
    # thể vượt xa ngân sách mà không gì chặn.
    budget = gemini.ApiBudget(
        max_api_calls=TRAN_HTTP, max_logical_calls=TRAN_LOGIC
    )
    gemini.set_budget(budget)

    ket_qua: list[dict] = []
    dung_som = None
    try:
        for i, case in enumerate(cases, 1):
            # Không KHỞI ĐỘNG một case khi chắc chắn không đủ chỗ cho đường
            # hạnh phúc của nó — case dở dang vừa tốn quota vừa không dùng được.
            # Đây là ngưỡng TỐI THIỂU, không phải upper bound: trần cứng trong
            # `ApiBudget` mới là thứ chặn khi retry làm case vượt dự kiến.
            con_lai = TRAN_LOGIC - budget.logical_calls
            if con_lai < LUOT_TOI_THIEU_MOI_CASE:
                dung_som = (
                    f"BUDGET_EXHAUSTED: đã dùng {budget.logical_calls}/{TRAN_LOGIC} "
                    f"lượt logic, còn {con_lai} — không đủ cho một case "
                    f"({LUOT_TOI_THIEU_MOI_CASE} lượt ở đường hạnh phúc)."
                )
                print(f"\n{dung_som}")
                break
            print(f"[{i}/{len(cases)}] {case.get('case_id')}", flush=True)
            r = await _chay_mot_case(case, api_key)
            if r["ngat_vi_ngan_sach"]:
                # Case bị cắt GIỮA CHỪNG: không phải hệ thất bại, nên không được
                # tính vào mẫu số. Ghi lại rồi dừng.
                dung_som = (
                    f"BUDGET_EXHAUSTED giữa case {case.get('case_id')}: "
                    f"{r['loi_runner']}"
                )
                print(f"\n{dung_som}")
                break
            ket_qua.append(r)
    except gemini.BudgetExceeded as e:
        dung_som = f"BUDGET_EXHAUSTED: {e}"
        print(f"\n{dung_som}")
    finally:
        gemini.set_budget(None)

    bao_cao = _tong_ket(ket_qua, len(cases), candidate, van_tay, budget, dung_som)

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "sealed_summary.json").write_text(
        json.dumps(bao_cao, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "sealed_cases.json").write_text(
        json.dumps(ket_qua, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    oracle = bao_cao["dung_theo_oracle_doc_lap"]
    print("\n── KẾT QUẢ ──")
    print(f"  N                     {bao_cao['N_processed']}/{bao_cao['N_planned']}"
          f"  (đầy đủ: {bao_cao['evaluation_complete']})")
    if bao_cao["canh_bao"]:
        print(f"  ⚠ {bao_cao['canh_bao']}")
    print(f"  A executability       {bao_cao['A_generative_executability']['so']}"
          f"/{bao_cao['N_processed']}")
    print(f"  B internal servable   {bao_cao['B_internal_servable']['so']}"
          f"/{bao_cao['N_processed']}  (STRONG-assurance, KHÔNG phải 'đúng')")
    print(f"  A−B phân rã           {bao_cao['A_tru_B_phan_ra']['theo_nguyen_nhan']}")
    print(f"  oracle độc lập        pass={oracle['pass']} fail={oracle['fail']} "
          f"ungraded={oracle['ungraded']} no_result={oracle['no_result']}")
    print(f"  phát nhưng oracle SAI {oracle['phat_nhung_oracle_noi_SAI']['so']}"
          f"  {oracle['phat_nhung_oracle_noi_SAI']['case_id']}")
    print(f"  D1 cấu trúc           lượt LLM/case "
          f"{bao_cao['D1_structural_interpreter_khong_ton_token']['so_luot_llm_phan_bo']}"
          f" · số bước "
          f"{bao_cao['D1_structural_interpreter_khong_ton_token']['so_buoc_min_max']}")
    print(f"  token/case (hỗ trợ)   {bao_cao['semantic_token_per_case']['chi_stage_ngu_nghia']}")
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
