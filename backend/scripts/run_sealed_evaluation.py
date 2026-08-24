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

#: Tập DEV — 20 case, **được nhìn** (`dev/cases.json` tự khai: *"DEV được nhìn;
#: SEALED thì không"*). Chạy trên nó KHÔNG đốt tập held-out và KHÔNG cần seed
#: của GVHD, nên nó là cách duy nhất biết A/B của hệ hiện tại trước lượt #2.
#:
#: ⚠️ Số của DEV **không bao giờ** là số của luận văn: hệ đã được chỉnh trên
#: chính 20 case này (`dev/cases.json` → *"dùng để chỉnh IR/schema/prompt"*),
#: nên nó đo *đường hạnh phúc*, không đo năng lực tổng quát. Nó trả lời đúng
#: một câu: **bốn biên chuẩn hoá + vòng sửa có làm phễu thông hơn không.**
DEV = BENCH / "dev" / "cases.json"

# Phân loại V2 tách ra module riêng vì nó là phần dễ viết sai nhất VÀ đi thẳng
# vào bảng của luận văn — nên phải kiểm được offline bằng dữ liệu bịa, trong khi
# runner thì chỉ được chạy một lần.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from reliability_v2 import chi_so_case, tong_hop  # noqa: E402

sys.path.insert(0, str(BACKEND))

#: NGÂN SÁCH CUỐI CÙNG, chốt 2026-08-22 TRƯỚC khi custodian niêm phong và
#: TRƯỚC khi nhìn một case SEALED nào. Sửa hai số này SAU khi thấy kết quả là
#: mua thêm lượt cho tới khi số đẹp — xem `freeze_protocol.md §2`.
#:
#: 440 = 11 × 40, tức ĐÚNG upper bound của call graph nhân N_planned. Nó KHÔNG
#: có nghĩa hệ được phép "thử 11 lần cho đẹp": mỗi stage vẫn giữ nguyên retry
#: bound riêng đã định nghĩa trong production code từ trước evaluation. Đây chỉ
#: là tổng trần của những đường retry/reclassify ĐÃ TỒN TẠI.
#:
#: Trần cũ 160 bị bỏ vì nó XUNG ĐỘT với protocol chứ không chỉ tiết kiệm quota:
#: 4 × 40 = 160 đúng bằng trần, nên một lần retry duy nhất ở bất kỳ đâu cũng đủ
#: làm evaluation không hoàn tất — trong khi N=40 đã là mục tiêu nghiên cứu khoá.
#:
#: LƯỢT #2 (2026-08-23): 440 → 520 vì upper bound đi 11 → 13, xem
#: `LUOT_TOI_DA_MOI_CASE`. Chốt TRƯỚC khi SEALED #2 tồn tại.
TRAN_LOGIC = 520

#: ~18% headroom trên logical worst-case, để chịu transient HTTP (429/5xx).
#: KHÔNG phải chỗ để dò tìm kết quả tốt hơn. Vượt ⇒ `BUDGET_EXHAUSTED`,
#: `evaluation_complete=false`, và KHÔNG chạy bù.
#:
#: LƯỢT #2: 520 → 620 (= 520 × 1,19, giữ nguyên tỉ lệ headroom cũ).
TRAN_HTTP = 620

#: Trần của tập DEV — DẪN từ cùng call graph, N=20 thay vì 40, không phải một
#: con số chọn tay: 13 × 20 = 260, và headroom HTTP giữ đúng tỉ lệ 1,19 của
#: SEALED. Tách hằng số riêng để một lượt DEV **không bao giờ** tiêu được vào
#: ngân sách đã chốt cho lượt đo chính thức.
TRAN_LOGIC_DEV = 260
TRAN_HTTP_DEV = 310

#: Đường HẠNH PHÚC: analyze + classify + semantic_analyze + semantic_program.
#: Dưới ngần này thì một case chắc chắn không chạy trọn.
LUOT_TOI_THIEU_MOI_CASE = 4

#: UPPER BOUND THẬT, dẫn xuất từ call graph — KHÔNG phải ước lượng:
#:
#:     stage_analyze          `_call_json(retries=1)`         → tối đa 2
#:     stage_classify lần 1   `_call_json(retries=1)`         → tối đa 2
#:     one-route recovery     thêm một stage_classify         → tối đa 2
#:     stage_semantic_analyze không retry                     → 1
#:     stage_semantic_program `range(MAX_SEMANTIC_PROGRAM_ATTEMPTS)` → tối đa 3
#:     stage_simulate*        `for _attempt in range(3)`      → tối đa 3
#:                                                              ─────────
#:                                                              tối đa 13
#:
#: Con số này là CƠ SỞ của `TRAN_LOGIC`: 13 × 40 = 520. Ngân sách được dẫn xuất
#: từ call graph, không chọn bằng cảm tính.
#:
#: 11 → 13 (2026-08-23, LƯỢT #2): `stage_semantic_program` trước đây một lượt,
#: nay ≤3 và gửi lỗi validator ngược cho LLM sửa. Đổi này là HỆ QUẢ SỐ HỌC của
#: một thay đổi call graph, **không** phải nới trần vì số xấu — nó được chốt
#: TRƯỚC khi tập SEALED #2 tồn tại và trước khi biết seed #2. Luật "không nâng
#: sau khi thấy số" nguyên vẹn: số của lượt #1 đã đóng, và lượt #1 chạy dưới
#: trần 440 của chính nó (dùng 205/440).
LUOT_TOI_DA_MOI_CASE = 13


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


def _chay_replay(spec, ghi: dict | None, hop_dong: dict | None) -> bool | None:
    """Replay đa đầu vào cho MỘT case. **0 lượt LLM** — cùng spec, đổi dữ liệu.

    Trả `None` khi CHƯA ĐO được, không phải `False`: không có spec, chương trình
    chưa chạy nổi, hoặc hợp đồng không nêu container đầu vào. Trộn "chưa đo" với
    "trượt" là bịa thêm thất bại — bịa theo hướng bi quan cũng vẫn là bịa.

    Replay ở đây là **QUAN TRẮC**, không gác cửa phát (`RELIABILITY_EVALUATION_
    PLAN §2.1`): cho nó chặn `servable` là đổi hành vi sản phẩm, và biến `B` của
    V2 thành thứ không so được với `B` của lượt #1.
    """
    if spec is None or not (ghi or {}).get("executable"):
        return None
    obligations = (hop_dong or {}).get("obligations") or []
    if not obligations:
        return None
    containers = [o["container"] for o in obligations if o.get("container")]
    witness = next((o.get("witness") for o in obligations if o.get("witness")), None)
    if not containers:
        return None
    try:
        import importlib.util
        import sys as _sys

        p = Path(__file__).resolve().parent / "replay_harness.py"
        sp = importlib.util.spec_from_file_location("replay_harness", p)
        mod = importlib.util.module_from_spec(sp)
        _sys.modules["replay_harness"] = mod
        sp.loader.exec_module(mod)
        return bool(mod.replay(spec, containers, witness=witness).ok)
    except Exception:  # noqa: BLE001 — quan trắc không được giết lượt đo
        return None


async def _chay_mot_case(case: dict, api_key: str) -> dict:
    from app.ai import pipeline
    from app.ai.telemetry import reset_usage, usage_report
    from app.simulation.semantic_program.coercion_stats import (
        coercion_report,
        reset_coercion,
    )
    from app.simulation.semantic_program.route import verify_and_compile  # noqa: F401

    reset_usage()
    reset_coercion()

    # BẮT SPEC TỪ PHÍA HARNESS. Observer KHÔNG mang `SemanticProgramSpec`, mà
    # replay cần chính nó. Phát thêm spec ra observer là sửa `pipeline.py` —
    # tức sửa engine, thứ task này cấm. Nên ta BỌC hàm từ ngoài: proxy đi qua
    # nguyên vẹn, chỉ ghi lại kết quả. Cùng khuôn `monkeypatch.setattr(pipeline,
    # "call_gemini", …)` mà bộ test đã dùng từ lâu.
    #
    # Khôi phục trong `finally`: một lượt case ném lỗi mà để lại proxy thì mọi
    # case sau chạy qua một hàm đã bị bọc chồng nhiều lớp.
    bat: dict = {}
    goc_stage = pipeline.stage_semantic_program

    async def _bat_spec(*a, **kw):
        spec, err = await goc_stage(*a, **kw)
        bat["spec"] = spec
        return spec, err

    pipeline.stage_semantic_program = _bat_spec
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
    finally:
        pipeline.stage_semantic_program = goc_stage

    ghi = thu.dau_tien("semantic_route")
    hop_dong = thu.dau_tien("semantic_contract")
    outcome = _outcome_tu_event(ghi)
    token = usage_report()
    replay_ok = _chay_replay(bat.get("spec"), ghi, hop_dong)

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
        # Ba biên chuẩn hoá của `contract.py` đã phải ra tay bao nhiêu lần cho
        # case này. Gộp im lặng thì không phân biệt được "mô hình thỉnh thoảng
        # viết dạng khác" với "hợp đồng đang mô tả sai thứ mô hình phát".
        "coercion": coercion_report(),
        # KHỐI V2 — chỉ THÊM khoá. Mọi khoá cũ ở trên giữ nguyên byte-một-bit,
        # nếu không thì artifact của lượt #1 và lượt sau không so được nữa.
        # `renderer_V=None`: tầng ⑦ chạy ở PHA B (trình duyệt), không ở đây.
        "v2": chi_so_case(
            source_id=(case.get("source") or {}).get("source_id") or case.get("case_id"),
            semantic=ghi,
            cham=_cham(case, hop_dong, outcome),
            replay_ok=replay_ok,
            render_ok=None,
        ),
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


def _model_da_chay() -> str:
    """Model THẬT của lượt này. Import muộn để module còn nạp được khi test
    tổng-kết chạy không có `app` trên path."""
    try:
        from app.ai import gemini

        return gemini.MODEL
    except Exception:  # noqa: BLE001 — quan trắc không được giết lượt đo
        return "KHONG_XAC_DINH"


def _tong_ket(ket_qua: list[dict], n_planned: int, candidate: dict, van_tay: str,
              budget, dung_som: str | None, dataset: str = "sealed",
              tran_logic: int = TRAN_LOGIC, tran_http: int = TRAN_HTTP) -> dict:
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

    def _tok_ra(r, stages) -> int:
        """Token ĐẦU RA thật = `candidates` + `thoughts`.

        Bỏ `thoughts` là báo thiếu: token suy nghĩ do model phát ra và được tính
        tiền như đầu ra. Trên lượt SEALED đầu tiên nó lớn hơn `candidates`
        **gấp 2,6 lần** ở stage `semantic_program` — gọi riêng `candidates` là
        "token đầu ra" sẽ báo thấp đi gần ba lần.
        """
        return sum(v.get("candidates_tokens", 0) + v.get("thoughts_tokens", 0)
                   for k, v in (r["token"] or {}).items() if k in stages)

    _STAGE_NGU_NGHIA = {"semantic_analyze", "semantic_program"}
    _STAGE_LEGACY = {"analyze", "classify", "simulate", "simulate_family"}

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
        # HAI DANH TÍNH, đừng gộp — xem `_danh_tinh_harness`.
        "measured_system_candidate": candidate.get("commit_ngan"),
        "evaluation_harness_commit": _danh_tinh_harness(),
        "cache_version": candidate.get("cache_version"),
        # Model là MỘT PHẦN danh tính hệ được đo. Ghi giá trị THẬT đã chạy, đọc
        # từ `gemini.MODEL`, không suy từ mặc định — nay nó đọc được từ
        # `GEMINI_MODEL` nên mặc định không còn là sự thật.
        "model": _model_da_chay(),
        "sealed_fingerprint": van_tay,
        "dung_som": dung_som,
        "dataset": dataset,
        # Cờ này phải ĐI CÙNG mọi con số. Một artifact DEV lọt vào tay người đọc
        # mà không tự khai là DEV thì nó đọc y hệt một kết quả held-out.
        "canh_bao_dataset": (
            None if dataset == "sealed" else
            "DEV — tập ĐÃ ĐƯỢC NHÌN và hệ đã được chỉnh trên chính nó. "
            "Số ở đây đo ĐƯỜNG HẠNH PHÚC, KHÔNG phải năng lực tổng quát, và "
            "KHÔNG được viết vào luận văn như A/B chính thức. Oracle sẽ là "
            "UNGRADED vì ground truth của DEV còn ở định dạng cũ (khoá theo tên "
            "biến), không phải hợp đồng nghĩa-vụ + giá-trị mà `_cham` đòi."
        ),
        "ngan_sach": {
            "tran_logic": tran_logic,
            "tran_http": tran_http,
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
        "token_dau_ra_theo_route": {
            "khai": "Token ĐẦU RA (`candidates` + `thoughts`) — thứ tiền thật "
                    "trả cho phần model PHÁT ra. Telemetry HỖ TRỢ, KHÔNG phải "
                    "D2: hai route chạy trên hai population khác nhau (route "
                    "sinh phục vụ được ít case hơn nhiều), nên so hai cột này "
                    "với nhau là apples-to-oranges. D2 chỉ đọc trên "
                    "`D2_matched_subset`.",
            "route_sinh": {
                "tong": sum(_tok_ra(r, _STAGE_NGU_NGHIA) for r in ket_qua),
                "moi_case": round(
                    sum(_tok_ra(r, _STAGE_NGU_NGHIA) for r in ket_qua) / n, 1
                ) if n else None,
            },
            "route_module": {
                "tong": sum(_tok_ra(r, _STAGE_LEGACY) for r in ket_qua),
                "moi_case": round(
                    sum(_tok_ra(r, _STAGE_LEGACY) for r in ket_qua) / n, 1
                ) if n else None,
            },
        },
        "coercion_rate": {
            "khai": "Số lượt BIÊN CHUẨN HOÁ của `contract.py` phải ra tay. Cao "
                    "và dai dẳng KHÔNG phải tin tốt: nó nghĩa là mô hình đã "
                    "thành thói quen viết khác hợp đồng, và chỗ phải sửa là bề "
                    "mặt sinh (prompt/thẻ văn phạm), không phải thêm một lớp "
                    "gộp nữa. Cần con số này vì gộp im lặng không phân biệt "
                    "được 'thỉnh thoảng' với 'luôn luôn'.",
            "theo_lop": {
                lop: sum((r.get("coercion") or {}).get(lop, 0) for r in ket_qua)
                for lop in sorted(
                    {k for r in ket_qua for k in (r.get("coercion") or {})}
                )
            },
            "so_case_phai_gop": sum(
                1 for r in ket_qua if any((r.get("coercion") or {}).values())
            ),
            "tren_tong_case": n,
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
        # V2 — bảy tầng + taxonomy thất bại 8 lớp. ĐẶT CẠNH khối cũ, không thay
        # nó: `A_generative_executability` và `B_internal_servable` ở trên vẫn
        # là hai chỉ số so được trực tiếp với lượt #1.
        "reliability_v2": tong_hop([r["v2"] for r in ket_qua if r.get("v2")]),
    }


def _danh_tinh_harness() -> dict:
    """HEAD của BỘ ĐO tại thời điểm chạy — tách hẳn khỏi hệ ĐƯỢC ĐO.

    Hai danh tính, hai câu hỏi khác nhau:

        measured_system_candidate  — ĐO BẢN NÀO của hệ sinh mô phỏng
        evaluation_harness_commit  — BỘ ĐO phiên bản nào đã đo nó

    Cần tách vì harness (runner, validator, test instrumentation) còn có thể
    được siết chặt trước SEALED, và **không có lý do gì đóng băng lại candidate
    chỉ vì bộ đo cứng cáp hơn** — miễn thay đổi ấy không đụng vào NGỮ NGHĨA của
    hệ được đo. Gộp hai hash làm một thì hoặc phải refreeze mỗi lần thêm một
    test, hoặc phải im lặng để candidate trôi khỏi HEAD; cả hai đều tệ.

    Cây bẩn được ghi lại chứ không chặn: harness bẩn không làm sai kết quả đo,
    nhưng người đọc có quyền biết bộ đo lúc ấy chưa được commit.
    """
    def _git(*a: str):
        """Trả `(ok, stdout đã strip)`. Tách `ok` khỏi nội dung vì chuỗi RỖNG là
        một câu trả lời có nghĩa ("cây sạch"), không phải thất bại."""
        try:
            r = subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True)
            return r.returncode == 0, r.stdout.strip()
        except OSError:
            return False, ""

    ok_head, head = _git("rev-parse", "--short", "HEAD")
    ok_status, ban = _git("status", "--porcelain")
    return {
        "commit": head if ok_head else None,
        "cay_sach": (ban == "") if ok_status else None,
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
    la_dev = args.dataset == "dev"

    if la_dev:
        # KHÔNG kiểm vân tay con dấu: DEV không có con dấu, và giả vờ có là nói
        # dối về xuất xứ. Nhưng candidate VẪN phải khớp — chạy trên một cây mã
        # đã trôi thì con số không gắn với bản nào cả.
        van_tay = "KHONG_CO_CON_DAU__DEV"
        tran_logic, tran_http = TRAN_LOGIC_DEV, TRAN_HTTP_DEV
        cases = json.loads(DEV.read_text(encoding="utf-8"))["cases"]
        print(f"DEV: {len(cases)} case — ĐÃ ĐƯỢC NHÌN, không phải held-out")
        print("     Số của lượt này KHÔNG được viết vào luận văn như A/B chính thức.")
    else:
        van_tay = _kiem_seal()
        tran_logic, tran_http = TRAN_LOGIC, TRAN_HTTP
        cases = json.loads(SEALED.read_text(encoding="utf-8"))["cases"]
        print(f"SEALED: {len(cases)} case · vân tay {van_tay[:16]}")
    print(f"Candidate: {candidate['commit_ngan']} · CACHE_VERSION {candidate['cache_version']}")
    print(f"Ngân sách: {tran_logic} lượt logic · {tran_http} lần thử HTTP")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise DungSach("Thiếu GEMINI_API_KEY (đặt trong backend/.env).")

    # Trần cưỡng chế ở CẢ HAI trục. Chỉ chặn HTTP là không đủ: pipeline có
    # nhiều tầng retry tự nó (xem LUOT_TOI_DA_MOI_CASE), nên số lượt logic có
    # thể vượt xa ngân sách mà không gì chặn.
    budget = gemini.ApiBudget(
        max_api_calls=tran_http, max_logical_calls=tran_logic
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
            con_lai = tran_logic - budget.logical_calls
            if con_lai < LUOT_TOI_THIEU_MOI_CASE:
                dung_som = (
                    f"BUDGET_EXHAUSTED: đã dùng {budget.logical_calls}/{tran_logic} "
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

    bao_cao = _tong_ket(ket_qua, len(cases), candidate, van_tay, budget, dung_som,
                        dataset=args.dataset, tran_logic=tran_logic,
                        tran_http=tran_http)

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "sealed_summary.json").write_text(
        json.dumps(bao_cao, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "sealed_cases.json").write_text(
        json.dumps(ket_qua, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    oracle = bao_cao["dung_theo_oracle_doc_lap"]
    hn = bao_cao["evaluation_harness_commit"]
    print("\n── KẾT QUẢ ──")
    print(f"  hệ được đo            {bao_cao['measured_system_candidate']}"
          f"  ·  bộ đo {hn['commit']} (cây sạch: {hn['cay_sach']})")
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
    print(f"  token ĐẦU RA/case     sinh {bao_cao['token_dau_ra_theo_route']['route_sinh']['moi_case']}"
          f" · module {bao_cao['token_dau_ra_theo_route']['route_module']['moi_case']}")
    print(f"  phải gộp cách viết    {bao_cao['coercion_rate']['so_case_phai_gop']}"
          f"/{bao_cao['coercion_rate']['tren_tong_case']} case"
          f" — {bao_cao['coercion_rate']['theo_lop']}")
    print(f"  D2 matched subset     {bao_cao['D2_matched_subset']['so_case']} case")
    print(f"  phân bố thất bại      {bao_cao['phan_bo_that_bai']}")
    print(f"  ngân sách             {bao_cao['ngan_sach']}")
    print(f"\nĐã ghi: {out}")
    print("\nKHÔNG vá rồi chạy lại. Case hỏng vì thiếu năng lực thì ghi đúng như thế.")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dataset", choices=("sealed", "dev"), default="sealed",
                   help="sealed = lượt đo chính thức (MỘT LẦN). "
                        "dev = 20 case đã được nhìn, không phải held-out.")
    p.add_argument("--out-dir", default=None)
    args = p.parse_args()

    # Mặc định đầu ra ĐI THEO dataset, không để người chạy phải nhớ.
    if args.out_dir is None:
        args.out_dir = str(BENCH / ("results" if args.dataset == "sealed" else "dev-results"))

    # CHẶN CỨNG, không phải lời nhắc: một lượt DEV ghi đè `results/` là xoá mất
    # artifact held-out DUY NHẤT và thay bằng số của tập đã được nhìn. Không có
    # cờ nào mở được cửa này — muốn ghi vào `results/` thì phải chạy `sealed`.
    if args.dataset == "dev" and Path(args.out_dir).resolve() == (BENCH / "results").resolve():
        print("DỪNG: lượt DEV không được ghi vào `results/` — đó là chỗ của "
              "artifact held-out lượt #1.", file=sys.stderr)
        return 2

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
