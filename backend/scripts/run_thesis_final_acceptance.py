# -*- coding: utf-8 -*-
"""RUNNER LƯỢT ĐÁNH GIÁ CUỐI của khoá luận.

    cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe \\
        scripts/run_thesis_final_acceptance.py --certify --out-dir <thư mục>

    cd backend && ALLOW_LIVE_AI=1 GEMINI_API_KEY=… PYTHONIOENCODING=utf-8 \\
        .venv/Scripts/python.exe scripts/run_thesis_final_acceptance.py \\
        --live --out-dir <thư mục>          ⚠️ TIÊU QUOTA THẬT

    `THESIS_FINAL_ACCEPTANCE_RUNNER_ALIGNMENT`, 2026-09-08.

Bộ đo, ở `scripts/` — ngoài `MEASURED_SYSTEM_PATHS`. Nó ĐỌC thẩm quyền sản
phẩm và không sửa gì trong `app/`.

─── HAI CHẾ ĐỘ, VÀ VÌ SAO KHÔNG CÓ CHẾ ĐỘ MẶC ĐỊNH GỌI PROVIDER ───────────

`--certify` chạy trọn vòng đời với **provider giả**; `--live` là đường duy
nhất chạm provider thật. Không cờ nào ⇒ in hướng dẫn rồi thoát. Một runner mà
lệnh ngắn nhất của nó tiêu quota là một runner sẽ tiêu quota vì gõ nhầm.

─── ĐIỀU RUNNER NÀY LÀM KHÁC RUNNER V3 ───────────────────────────────────

Năm khoảng trống đã đo ở `RUN_PLAN.json` của wave trước, đóng đúng năm:

    G1  bộ ca CỐ ĐỊNH, đọc thẳng `CORPUS.json` — không seed, không con dấu,
        không rút. `nap_ca_v3` không xuất hiện ở file này.
    G2  giữ NGUYÊN VĂN từng raw response: analyze · synthesis · repair, mỗi
        cái một file kèm băm, chỉ số lượt logic và số lần thử vật lý.
    G3  chấm bằng `acceptance_verdict` cho ca dương VÀ ca âm; không danh sách
        mã hình cong chép tay nào.
    G4  hai chặng, chặng B đúng MỘT lượt sửa.
    G5  nạp chính sách/bộ ca/danh tính của `thesis-final-acceptance`.

─── CHẶNG B TIẾP TỤC, KHÔNG CHẠY LẠI (§3) ────────────────────────────────

Đây là chỗ đáng nói nhất. Chặng B **không** gọi lại analyze và **không** sinh
lại candidate đầu: nó nhận `RequestContract` đã đóng băng, raw candidate hỏng
và chẩn đoán từ chặng A, rồi tiêu đúng **một** lượt sửa. Nhờ vậy trần chặng B
tụt từ `7 × 3 = 21` xuống `7 × 1 = 7`.

Làm được vì `pipeline` phơi đủ helper để **tái dùng**, không phải chép:

    `_prompt_sua`   — chính hàm sản phẩm dựng prompt sửa
    `load_skill` · `program_skill_for` · `generate_json_schema`
    `validate_semantic_program` · `kiem_tinh` · `check_grounding`
    `KHONG_DUOC_SUA`

Còn `base` — đề + dữ kiện + nghĩa vụ + thẻ văn phạm — là biến CỤC BỘ của
`stage_semantic_program`, không lấy ra được. Nên runner **không dựng lại nó**:
ở lượt đầu `prompt = base` nguyên văn, nên cổng bọc `call_gemini` **chụp** lại
đúng chuỗi ấy. Không có bản sao nào để trôi.

⚠️ Chuỗi chẩn đoán thì phải dựng lại (ba nhánh `loi` nằm trong thân vòng lặp).
Đó là chỗ DUY NHẤT có nguy cơ lệch khỏi sản phẩm, và nó bị khoá bằng một phép
so BYTE: `test_thesis_runner_alignment.py` chạy `stage_semantic_program` THẬT
với trần 2 lượt, chụp prompt lượt thứ hai, rồi đòi prompt chặng B của runner
trùng từng byte.
"""
from __future__ import annotations

import argparse
import asyncio
import contextlib
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

BACKEND = Path(__file__).resolve().parents[1]
GOC = BACKEND.parent
for _p in (str(BACKEND), str(BACKEND / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

THU_MUC_KHOA = (GOC / "docs" / "evaluation" / "geometry"
                / "thesis-final-acceptance")
CHINH_SACH = BACKEND / "scripts" / "policies" / "thesis_final_acceptance_policy.json"

#: File nằm trong `RUNNER_HASH`. CỐ Ý chỉ có entrypoint: đưa thêm module vào
#: đây thì mỗi lần sửa một module dùng chung sẽ đổi danh tính runner, và
#: `IDENTITY_LOCK` sẽ trôi vì một lý do không nói gì về runner. Các module bộ
#: đo khác được ghim RIÊNG ở `RUNNER_MODULE_HASHES` — xem `bam_runner()`.
RUNNER_ENTRYPOINT = "backend/scripts/run_thesis_final_acceptance.py"
RUNNER_MODULE_SET = (
    "backend/scripts/thesis_acceptance_corpus.py",
    "backend/scripts/thesis_acceptance_oracle.py",
    "backend/scripts/acceptance_integrity.py",
    "backend/scripts/measurement_policy.py",
)

__all__ = [
    "BoDo",
    "CanhGac",
    "NGUON_ARTIFACT",
    "RUNNER_ENTRYPOINT",
    "RUNNER_MODULE_SET",
    "bam_runner",
    "bao_provider",
    "chan_doan_san_pham",
    "cham_mot_ca",
    "chay_lut",
    "ghim_so_luot_tong_hop",
    "nap_bo_do",
    "prompt_sua_chang_b",
]

#: Artifact bắt buộc phải có mặt và phải KHỚP BĂM trước khi xử lý ca đầu tiên.
NGUON_ARTIFACT = ("CORPUS.json", "EXPECTED_RESULTS.json", "GOLD_PREFLIGHT.json",
                  "EVALUATION_POLICY.json", "IDENTITY_LOCK.json")


class RunnerError(RuntimeError):
    """Runner DỪNG. Không có nhánh nào đi tiếp bằng một giả định."""


def _bam_tep(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _bam_chuoi(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _bay_gio() -> str:
    return datetime.now(timezone.utc).isoformat()


def bam_runner() -> dict[str, str]:
    """Danh tính runner. Hai lớp, cố ý tách.

    `RUNNER_HASH` là băm của **đúng file entrypoint** — cùng quy ước
    `acceptance_integrity.mo_run` đã dùng, nên hai chỗ nói cùng một thứ.
    `RUNNER_MODULE_HASHES` ghim từng module bộ đo mà runner dựa vào; trôi ở đó
    vẫn thấy được, nhưng nó không giả vờ là runner đã đổi.

    ⚠️ **Không file artifact nào có mặt ở đây.** `IDENTITY_LOCK.json` chứa
    `RUNNER_HASH`, nên nếu băm runner lại đọc artifact thì mỗi lần ghi lock sẽ
    đổi băm và không bao giờ hội tụ. Vòng ấy bị chặn bằng cách chọn tập file,
    không bằng một mẹo tính toán.
    """
    return {
        "RUNNER_HASH": _bam_tep(GOC / RUNNER_ENTRYPOINT),
        "RUNNER_ENTRYPOINT": RUNNER_ENTRYPOINT,
        "RUNNER_MODULE_HASHES": {m: _bam_tep(GOC / m)
                                 for m in RUNNER_MODULE_SET},
    }


# ══════════════════════════════════════════════════════════════════════════
# §6 · BỘ NẠP BỘ CA CỐ ĐỊNH — kiểm MỌI băm trước khi xử lý ca đầu tiên
# ══════════════════════════════════════════════════════════════════════════
class BoDo:
    """Mọi thứ lượt đo cần, đã kiểm băm. Dựng xong là bất biến."""

    def __init__(self, thu_muc: Path) -> None:
        import measurement_policy as MP
        import thesis_acceptance_corpus as C

        self.thu_muc = thu_muc
        thieu = [t for t in NGUON_ARTIFACT if not (thu_muc / t).exists()]
        if thieu:
            raise RunnerError(f"thiếu artifact đã khoá: {thieu}")

        self.corpus = json.loads((thu_muc / "CORPUS.json").read_text("utf-8"))
        self.expected = json.loads(
            (thu_muc / "EXPECTED_RESULTS.json").read_text("utf-8"))
        self.gold = json.loads(
            (thu_muc / "GOLD_PREFLIGHT.json").read_text("utf-8"))
        self.lock = json.loads(
            (thu_muc / "IDENTITY_LOCK.json").read_text("utf-8"))
        self.nguong, self.bam_nguong = MP.doc_chinh_sach(CHINH_SACH)

        self.kiem: dict[str, bool] = {}
        self.lech: list[str] = []
        self._kiem_bam(MP, C)

    def _kiem_bam(self, MP, C) -> None:
        import freeze_evaluation_candidate as F
        from acceptance_integrity import moi_truong_hien_tai

        he, _n = F.measured_system_hash()
        mt = moi_truong_hien_tai()
        ban_sao_cs = json.loads(
            (self.thu_muc / "EVALUATION_POLICY.json").read_text("utf-8"))

        so = [
            ("CORPUS_HASH_MATCH",
             MP.bam_chinh_tac(self.corpus), C.CORPUS_HASH),
            ("EXPECTED_RESULTS_HASH_MATCH",
             MP.bam_chinh_tac(self.expected), C.EXPECTED_RESULTS_HASH),
            ("GOLD_PREFLIGHT_HASH_MATCH",
             _bam_tep(self.thu_muc / "GOLD_PREFLIGHT.json"),
             self.lock.get("GOLD_PREFLIGHT_HASH")),
            ("POLICY_HASH_MATCH", self.bam_nguong, self.lock.get("POLICY_HASH")),
            ("POLICY_MIRROR_MATCH",
             MP.bam_chinh_tac(ban_sao_cs), MP.bam_chinh_tac(self.nguong)),
            ("CANDIDATE_HASH_MATCH", he, self.lock.get("CANDIDATE_HASH")),
            ("CACHE_VERSION_MATCH",
             mt["cache_version"], self.lock.get("CACHE_VERSION")),
            ("MODEL_FACING_HASHES_MATCH",
             _bam_chuoi("|".join([
                 mt["components"]["prompts"], mt["components"]["grammar_card"],
                 mt["components"]["analyze_schema"],
                 mt["components"]["synthesis_schema"],
                 mt["stable_capability_hash"]])),
             _bam_chuoi("|".join([
                 self.lock.get("PROMPT_HASH", ""),
                 self.lock.get("GRAMMAR_CARD_HASH", ""),
                 self.lock.get("ANALYZE_SCHEMA_HASH", ""),
                 self.lock.get("SYNTHESIS_SCHEMA_HASH", ""),
                 self.lock.get("CAPABILITY_HASH", "")]))),
        ]
        for ten, thuc, mong in so:
            ok = bool(mong) and thuc == mong
            self.kiem[ten] = ok
            if not ok:
                self.lech.append(
                    f"{ten}: thực {str(thuc)[:16]}… ≠ khoá {str(mong)[:16]}…")

    @property
    def ca_duong(self) -> list[dict]:
        return list(self.corpus["positive_cases"])

    @property
    def ca_am(self) -> list[dict]:
        return list(self.corpus["negative_cases"])

    @property
    def moi_ca(self) -> list[dict]:
        return self.ca_duong + self.ca_am

    def payload_gui_model(self, ca: dict) -> dict[str, str]:
        """ĐƯỜNG DUY NHẤT tới provider. Đúng một trường.

        Đọc lại từ corpus đã khoá chứ không từ đối tượng ca đang cầm: ca trong
        bộ nhớ mang cả `gold_program` lẫn `expected_scene3d_kinds`, và một
        `**ca` vô ý ở chỗ dựng prompt sẽ gửi cả gold đi mà không ai thấy.
        """
        return {"problem_text": ca["problem_text"]}


def nap_bo_do(thu_muc: Path | None = None) -> BoDo:
    return BoDo(Path(thu_muc) if thu_muc else THU_MUC_KHOA)


# ══════════════════════════════════════════════════════════════════════════
# §5 · CỔNG CANH — danh tính và ngân sách, TRƯỚC mỗi lượt gọi logic
# ══════════════════════════════════════════════════════════════════════════
class CanhGac:
    """Đếm và canh. Mọi lượt gọi logic đi qua đây, không có đường vòng."""

    def __init__(self, bo_do: BoDo, thu_muc: Path, *, gia_lap: bool) -> None:
        self.bo_do = bo_do
        self.thu_muc = Path(thu_muc)
        self.gia_lap = gia_lap
        ns = bo_do.nguong["budget"]
        self.tran_logic = int(ns["MAX_LOGICAL_CALLS"])
        self.tran_vat_ly = int(ns["MAX_PHYSICAL_ATTEMPTS"])
        self.tran_token = int(ns["HARD_TOKEN_BUDGET"])
        self.dat_cho = ns["dan_xuat"]
        self.logic = 0
        self.vat_ly = 0
        self.token_da_dat_cho = 0
        self.su_kien: list[dict[str, Any]] = []
        self.raw: list[dict[str, Any]] = []

    # ── nhật ký sự kiện: bằng chứng ĐƯỜNG ĐI, không phải log gỡ rối ──────
    def ghi(self, ten: str, **kw: Any) -> None:
        self.su_kien.append({"event": ten, "at": _bay_gio(),
                             "logical_call_index": self.logic, **kw})

    def _dat_cho_token(self, stage: str) -> int:
        return int(self.dat_cho["reservation_analyze" if stage == "analyze"
                                else "reservation_synthesis"])

    def truoc_luot_goi(self, stage: str) -> None:
        """Danh tính chưa trôi, và còn đủ chỗ cho lượt này chứ?

        Kiểm TRƯỚC, không phải sau: một lượt gọi đã đi rồi thì tiền đã tiêu,
        và một cổng chạy sau chỉ báo cáo lại điều nó đáng lẽ phải chặn.
        """
        mf = self.thu_muc / "manifest.json"
        if not mf.exists():
            raise RunnerError("chưa có manifest — không lượt gọi nào được "
                              "phép đi trước ảnh chụp danh tính")
        from acceptance_integrity import doc_artifact, kiem_ghim_bo_do

        d = doc_artifact(mf)
        if loi := kiem_ghim_bo_do(d):
            raise RunnerError("DANH TÍNH BỘ ĐO TRÔI:\n  " + "\n  ".join(loi))
        lai = BoDo(self.bo_do.thu_muc)
        if lai.lech:
            raise RunnerError("BĂM ĐÃ KHOÁ TRÔI:\n  " + "\n  ".join(lai.lech))
        if self.logic >= self.tran_logic:
            raise RunnerError(f"HẾT TRẦN lượt gọi logic ({self.tran_logic})")
        dc = self._dat_cho_token(stage)
        if self.token_da_dat_cho + dc > self.tran_token:
            raise RunnerError(
                f"HẾT TRẦN token: đã đặt chỗ {self.token_da_dat_cho} + {dc} "
                f"> {self.tran_token}")
        self.ghi("identity_guard_pass", stage=stage)
        self.ghi("budget_guard_pass", stage=stage,
                 token_reservation=dc,
                 token_reserved_total=self.token_da_dat_cho + dc)

    def sau_luot_goi(self, stage: str, prompt: str, raw: str,
                     case_id: str, attempt: int, lan_thu_vat_ly: int) -> dict:
        """Giữ NGUYÊN VĂN. Một response parse lỗi vẫn được giữ."""
        self.logic += 1
        self.vat_ly += lan_thu_vat_ly
        self.token_da_dat_cho += self._dat_cho_token(stage)
        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, TypeError) as e:
            parsed, loi_parse = None, f"{type(e).__name__}: {e}"
        else:
            loi_parse = None
        ban_ghi = {
            "case_id": case_id, "stage": stage, "attempt_index": attempt,
            "logical_call_index": self.logic - 1,
            "physical_attempts": lan_thu_vat_ly,
            "at": _bay_gio(),
            "prompt_sha256": _bam_chuoi(prompt),
            "prompt_bytes": len(prompt.encode("utf-8")),
            "raw_text": raw, "raw_sha256": _bam_chuoi(raw),
            "parsed": parsed, "parse_error": loi_parse,
        }
        self.raw.append(ban_ghi)
        self.ghi(f"{stage}_call", case_id=case_id, attempt=attempt,
                 raw_sha256=ban_ghi["raw_sha256"])
        return ban_ghi


# ══════════════════════════════════════════════════════════════════════════
# §13 · BỌC PROVIDER — phủ MỌI reference, hoàn nguyên trong `finally`
# ══════════════════════════════════════════════════════════════════════════
#
# `pipeline` làm `from app.ai.gemini import call_gemini`, nên có HAI tên trỏ
# cùng một hàm. Vá một tên là để hở tên kia — và tên bị bỏ sót chính là tên đi
# thẳng ra mạng. Danh sách dưới đây liệt kê mọi module giữ một tham chiếu.
_NOI_GIU_THAM_CHIEU = ("app.ai.pipeline", "app.ai.gemini")


@contextlib.contextmanager
def bao_provider(thay: Callable):
    """Thay `call_gemini` ở MỌI nơi giữ tham chiếu; hoàn nguyên trong `finally`.

    Sau khi gỡ, `dang_bi_vá()` phải trả `False` — nếu một tham chiếu còn trỏ
    stub thì lượt sau sẽ "chạy" mà không gọi mạng, và mọi con số của nó là
    bịa. Guard ấy nằm ở `test_thesis_runner_alignment.py`.
    """
    import importlib

    goc: dict[str, Callable] = {}
    mods = {}
    for ten in _NOI_GIU_THAM_CHIEU:
        m = importlib.import_module(ten)
        mods[ten] = m
        goc[ten] = getattr(m, "call_gemini")
    try:
        for ten, m in mods.items():
            setattr(m, "call_gemini", thay)
        yield goc
    finally:
        for ten, m in mods.items():
            setattr(m, "call_gemini", goc[ten])


def dang_bi_va() -> dict[str, bool]:
    """Tham chiếu nào còn KHÔNG trỏ về `app.ai.gemini.call_gemini` gốc?"""
    import importlib

    that = importlib.import_module("app.ai.gemini")
    goc = getattr(that, "_call_gemini_goc", None) or that.call_gemini
    return {ten: getattr(importlib.import_module(ten), "call_gemini") is not goc
            for ten in _NOI_GIU_THAM_CHIEU}


@contextlib.contextmanager
def ghim_so_luot_tong_hop(n: int):
    """Ghim `MAX_SEMANTIC_PROGRAM_ATTEMPTS` — hằng số SẢN PHẨM, không phải một
    runner riêng. Hoàn nguyên trong `finally` sau TỪNG ca: một bản vá toàn cục
    sống sót qua ngoại lệ sẽ rò sang ca sau, và thứ rò ra là trần lượt gọi."""
    from app.ai import pipeline

    goc = pipeline.MAX_SEMANTIC_PROGRAM_ATTEMPTS
    pipeline.MAX_SEMANTIC_PROGRAM_ATTEMPTS = n
    try:
        yield
    finally:
        pipeline.MAX_SEMANTIC_PROGRAM_ATTEMPTS = goc


# ══════════════════════════════════════════════════════════════════════════
# §3 · CHẨN ĐOÁN + PROMPT SỬA — tái dùng helper sản phẩm, khoá parity bằng test
# ══════════════════════════════════════════════════════════════════════════
def chan_doan_san_pham(raw: str, contract: Any) -> tuple[str | None, str]:
    """Chuỗi `loi` mà `stage_semantic_program` SẼ gửi ngược, và tên nhánh.

    Ba nhánh, đúng thứ tự của vòng lặp sản phẩm: lược đồ → thẩm định tĩnh →
    xuất xứ. Đảo thứ tự là gửi cho mô hình một lời sửa nói về tầng sai.

    `(None, lý_do)` nghĩa là KHÔNG có gì để sửa — hoặc chương trình hợp lệ,
    hoặc nó chết bằng một mã nằm trong `KHONG_DUOC_SUA` (lỗi trung thực năng
    lực: gửi đi sửa là trả tiền cho một lượt giấu khéo hơn).
    """
    from app.ai.pipeline import KHONG_DUOC_SUA
    from app.simulation.semantic_program.grounding_gate import check_grounding
    from app.simulation.semantic_program.ir_static_check import kiem_tinh
    from app.simulation.semantic_program.validator import validate_semantic_program

    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as e:
        return f"JSON không parse được ({e})", "parse"
    if not isinstance(payload, dict):
        return (f"đầu ra không phải một đối tượng JSON "
                f"(nhận {type(payload).__name__})"), "shape"
    val = validate_semantic_program(payload)
    if not val.ok:
        return val.error, "schema"
    t = kiem_tinh(val.spec)
    if not t.ok:
        return "chương trình không thực thi được — " + t.phan_hoi(), "ir_static"
    if contract is not None:
        g = check_grounding(contract, val.spec)
        if not g.ok and g.error_code in KHONG_DUOC_SUA:
            return None, "khong_duoc_sua"
        if not g.ok:
            return ("xuất xứ dữ liệu chưa đủ — "
                    + "; ".join(g.unresolved[:4])), "grounding"
    return None, "khong_co_gi_de_sua"


def prompt_sua_chang_b(base_da_chup: str, raw_hong: str, chan_doan: str,
                       de: str, domain: str) -> str:
    """Prompt chặng B — dựng bằng CHÍNH `_prompt_sua` của sản phẩm.

    `base_da_chup` là chuỗi runner CHỤP ở lượt tổng hợp đầu tiên, không phải
    một bản dựng lại. Ở lượt đầu `stage_semantic_program` đặt `prompt = base`
    nguyên văn, nên chụp là cách duy nhất lấy được nó mà không tạo bản sao.
    """
    from app.ai.pipeline import _prompt_sua

    return _prompt_sua(base_da_chup, raw_hong, chan_doan, de=de, domain=domain)


# ══════════════════════════════════════════════════════════════════════════
# §11 · CHẤM — adapter MỎNG quanh scorer canonical
# ══════════════════════════════════════════════════════════════════════════
def _kieu_canh(canh: dict | None) -> list[str]:
    return sorted({o.get("type") for o in (canh or {}).get("objects", [])})


def cham_mot_ca(ca: dict, bo_do: BoDo, *, contract, spec, outcome,
                schema_ok: bool, canh: dict | None,
                la_am: bool) -> dict[str, Any]:
    """Mọi chiều ghi RIÊNG. Không cột nào suy từ cột khác.

    ⚠️ Hai lớp mà `acceptance_verdict.phan_loai` KHÔNG tự sinh được, đã khoá
    trong policy (`error_accounting.khong_co_trong_scorer_canonical`) và xử lý
    Ở ĐÂY, ngoài scorer:

        MODEL_ANALYZE_FAILURE   analyze hỏng ⇒ chưa có `RequestContract` ⇒
                                `phan_loai` chưa từng được gọi.
        SYSTEM_SCENE3D_FAILURE  `servable` nhưng cảnh sai. `phan_loai` trả
                                `CORRECT_SERVABLE_RESULT` ngay khi `servable`,
                                nên nhãn không tự hạ.

    THỨ TỰ ƯU TIÊN, khoá trước: analyze đứng trước mọi thứ (không có hợp đồng
    thì không có gì để chấm); Scene3D đứng SAU phán quyết canonical và chỉ HẠ
    một nhãn đã `CORRECT_SERVABLE_RESULT` — nó không bao giờ nâng.
    """
    import acceptance_verdict as AV
    import thesis_acceptance_oracle as O

    if contract is None:
        return {"CANONICAL_VERDICT": "MODEL_ANALYZE_FAILURE",
                "runner_owned_class": True,
                "vi_sao": "analyze không tạo được RequestContract",
                "SCOPE_PASS": True, "ANALYZE_CONTRACT_CORRECT": False,
                "SERVABLE": False}

    gd = AV.co_giai_doan(outcome, schema_ok=schema_ok)
    kq = AV.trich_ket_qua(outcome) if outcome is not None else {
        "nguon": "outcome.final_memory", "dai_luong": {}}

    if la_am:
        bien = AV.cham_ca_am(_ca_am_cho_scorer(ca), outcome,
                             schema_ok=schema_ok)
        lop = AV.phan_loai(
            outcome, schema_ok=schema_ok, la_ca_am=True,
            boundary_ok=bien["target_boundary_demonstrated"],
            contract=contract, spec=spec)
        return {
            "NEGATIVE_FAIL_CLOSED": bien["fail_closed"],
            "TARGET_BOUNDARY_PASS": bien["target_boundary_demonstrated"],
            "EXPECTED_BOUNDARY": ca["target_boundary"],
            "EXPECTED_CODES": bien["expected_codes"],
            "EXPECTED_STAGES": bien["expected_stages"],
            "ACTUAL_BOUNDARY": {"code": bien["actual_code"],
                                "stage": bien["actual_stage"]},
            "SERVED_ANY_QUANTITY": sorted(kq["dai_luong"].values()),
            "SERVABLE": gd["servable"],
            "CANONICAL_VERDICT": lop,
            "runner_owned_class": False,
            "ghi_chu": bien["ghi_chu"],
        }

    mong = bo_do.expected["cases"][ca["id"]]
    song_anh = _song_anh_witness(ca, contract)
    dl = {}
    for ten, m in mong.items():
        ten_that = song_anh.get(ten, ten)
        hien = kq["dai_luong"].get(ten_that)
        khop_so, sai_so = False, None
        if hien is not None:
            try:
                sai_so = O.sai_so_tuong_doi(hien, m["oracle_value"])
                khop_so = sai_so <= bo_do.expected["oracle_tolerance"][
                    m["oracle_method"]]
            except O.OracleError:
                khop_so, sai_so = False, None
        dl[ten] = {"expected_display": m["display"], "actual_display": hien,
                   "exact_answer_match": hien == m["display"],
                   "oracle_numeric_agreement": khop_so,
                   "relative_error": sai_so}

    kieu = _kieu_canh(canh)
    scene_ok = set(ca["expected_scene3d_kinds"]) <= set(kieu)
    lop = AV.phan_loai(outcome, schema_ok=schema_ok, contract=contract,
                       spec=spec)
    if gd["servable"] and not scene_ok:
        lop, runner_owned = "SYSTEM_SCENE3D_FAILURE", True
    else:
        runner_owned = False
    return {
        "SCOPE_PASS": True,
        "ANALYZE_CONTRACT_CORRECT": True,
        "PROGRAM_SCHEMA_VALID": schema_ok,
        "IR_STATIC_PASS": gd["static_valid"],
        "GROUNDING_PASS": gd["grounding_pass"],
        "COVERAGE_PASS": gd["coverage_pass"],
        "SOURCE_INVARIANTS_PASS": gd["stage_reached"] not in
        ("source_invariant",) and gd["grounding_pass"],
        "RUNTIME_PASS": gd["runtime_executable"],
        "POSTCONDITIONS_PASS": gd["postconditions_pass"],
        "EXACT_ANSWER_MATCH": bool(dl) and all(
            q["exact_answer_match"] for q in dl.values()),
        "ORACLE_NUMERIC_AGREEMENT": bool(dl) and all(
            q["oracle_numeric_agreement"] for q in dl.values()),
        "TRACE_PASS": bool((outcome and getattr(outcome, "trace", None))
                           or gd["runtime_executable"]),
        "SCENE3D_PASS": scene_ok,
        "SERVABLE": gd["servable"],
        "CANONICAL_VERDICT": lop,
        "runner_owned_class": runner_owned,
        "stage_reached": gd["stage_reached"],
        "error_code": getattr(outcome, "error_code", None),
        "quantities": dl,
        "scene3d_kinds": kieu,
        "scene3d_kinds_missing": sorted(
            set(ca["expected_scene3d_kinds"]) - set(kieu)),
        "exact_result_authority": kq["nguon"],
        "final_memory": kq["dai_luong"],
        # Ánh xạ tên GOLD → tên MÔ HÌNH TỰ ĐẶT. Ghi ra để soát được: nếu nó
        # rỗng trong khi ca có nghĩa vụ, phép tra đáp số đang nhìn sai chỗ.
        "witness_mapping": song_anh,
    }


def _song_anh_witness(ca: dict, contract: Any) -> dict[str, str]:
    """`{witness của GOLD → witness mà MÔ HÌNH thật sự dùng}`, khớp theo KIND.

    ⚠️ **Lỗi này đã xảy ra thật, ở đúng lượt đo cuối.** Bản trước tra đáp số
    bằng `final_memory[<tên của GOLD>]` — nhưng tên biến là thứ MÔ HÌNH tự đặt.
    Lượt live 2026-09-08 cho `the_volume_sabcd`, `V_S_MNPQR`,
    `dien_tich_elip_e`… trong khi gold dùng `V`, `S_T`, `S_E`. Kết quả:
    `actual_display = None` ở 6/7 ca **có đáp số hoàn toàn đúng**, và
    `SILENT_WRONG_ANSWER_COUNT` báo **6** thay vì **0** — tức bộ đo tố cáo hệ
    một tội nó không phạm.

    Thứ KHÔNG đổi giữa gold và bản mô hình viết là **loại nghĩa vụ**
    (`volume` · `area` · `lateral_area` · `distance`): nó do `analyze` khai và
    do taxonomy đóng băng quyết định, không do mô hình đặt tên. Nên ánh xạ đi
    qua kind.

    ⚠️ Chỉ đúng khi **kind là khoá duy nhất trong một ca**. Đo trên cả 9 ca của
    corpus: đúng. Guard dưới đây ném khi điều đó thôi đúng, thay vì lặng lẽ
    ghép nhầm hai nghĩa vụ cùng loại.
    """
    gold = [(o["kind"], (o.get("params") or {}).get("witness"))
            for o in ca["request_contract_gold"]["obligations"]]
    live = [(o.kind, (o.params or {}).get("witness"))
            for o in (contract.obligations or ())]
    for ten, ds in (("gold", gold), ("live", live)):
        k = [x for x, _w in ds]
        if len(set(k)) != len(k):
            raise RunnerError(
                f"ca '{ca['id']}': hợp đồng {ten} có HAI nghĩa vụ cùng kind "
                f"{k} — ánh xạ theo kind không còn phân biệt được, và ghép "
                f"nhầm ở đây sẽ chấm một đại lượng bằng kỳ vọng của đại lượng "
                f"khác")
    theo_kind = {k: w for k, w in live if w}
    return {w: theo_kind[k] for k, w in gold if w and k in theo_kind}


def _ca_am_cho_scorer(ca: dict) -> dict:
    """`cham_ca_am` NÉM khi ca không khai `expected_codes`/`expected_stages`.
    Corpus đã khai cả hai; hàm này chỉ rút đúng ba khoá nó đọc."""
    return {"id": ca["id"], "target_boundary": ca["target_boundary"],
            "expected_codes": ca["expected_codes"],
            "expected_stages": ca["expected_stages"]}


# ══════════════════════════════════════════════════════════════════════════
# §9 · CHẶNG A — một analyze, một tổng hợp, KHÔNG sửa
# ══════════════════════════════════════════════════════════════════════════
async def _chay_stage_a(ca: dict, bo_do: BoDo, gac: CanhGac,
                        api_key: str) -> dict[str, Any]:
    from app.ai import pipeline
    from app.simulation.semantic_program.domain_profile import (
        DOMAIN_HINH_HOC, co_duong_thuc_thi, detect_domain)
    from app.simulation.semantic_program.route import verify_and_compile

    de = bo_do.payload_gui_model(ca)["problem_text"]
    la_am = "target_boundary" in ca
    ra: dict[str, Any] = {"id": ca["id"], "loai": "am" if la_am else "duong",
                          "problem_sha256": _bam_chuoi(de)}

    # ── ① CỔNG PHẠM VI — tất định, 0 lượt gọi ───────────────────────────
    mien = detect_domain(de)
    co_duong = co_duong_thuc_thi(de, DOMAIN_HINH_HOC) if mien == DOMAIN_HINH_HOC \
        else False
    gac.ghi("scope", case_id=ca["id"], domain=mien, co_duong_thuc_thi=co_duong)
    ra["scope"] = {"domain": mien, "co_duong_thuc_thi": co_duong,
                   "provider_needed": mien == DOMAIN_HINH_HOC and co_duong}
    if not ra["scope"]["provider_needed"]:
        ra["cham"] = {"SCOPE_PASS": False, "SERVABLE": False,
                      "CANONICAL_VERDICT": "HONEST_UNSUPPORTED_REFUSAL"
                      if la_am else "MODEL_ANALYZE_FAILURE",
                      "runner_owned_class": True,
                      "vi_sao": "dừng ở cổng phạm vi, KHÔNG chạm provider"}
        ra["stopped_before_provider"] = True
        return ra
    ra["stopped_before_provider"] = False

    # ── ② ANALYZE — đúng MỘT lượt ───────────────────────────────────────
    gac.truoc_luot_goi("analyze")
    contract, loi = await pipeline.stage_semantic_analyze(
        de, api_key, domain=DOMAIN_HINH_HOC)
    if contract is None:
        ra["analyze_error"] = loi
        ra["cham"] = cham_mot_ca(ca, bo_do, contract=None, spec=None,
                                 outcome=None, schema_ok=False, canh=None,
                                 la_am=la_am)
        return ra

    # ── ③ ĐÓNG BĂNG HỢP ĐỒNG ────────────────────────────────────────────
    hd = {"problem_text": contract.problem_text,
          "input_facts": [f.model_dump(mode="json")
                          for f in contract.input_facts],
          "obligations": [o.model_dump(mode="json")
                          for o in contract.obligations]}
    ra["request_contract"] = hd
    ra["frozen_contract_sha256"] = _bam_chuoi(
        json.dumps(hd, sort_keys=True, ensure_ascii=False))
    gac.ghi("freeze_contract", case_id=ca["id"],
            sha256=ra["frozen_contract_sha256"])

    # ── ④ TỔNG HỢP — đúng MỘT lượt, trần ghim xuống 1 ───────────────────
    gac.truoc_luot_goi("synthesis")
    with ghim_so_luot_tong_hop(1):
        spec, serr = await pipeline.stage_semantic_program(
            de, {}, api_key, contract, domain=DOMAIN_HINH_HOC)
    ra["synthesis_error"] = serr
    ra["schema_ok"] = spec is not None
    ra["chuong_trinh"] = spec.model_dump(mode="json") if spec else None

    # ── ⑤ ĐƯỜNG SẢN PHẨM ────────────────────────────────────────────────
    outcome = verify_and_compile(contract, spec) if spec is not None else None
    canh = pipeline._dung_scene3d(spec, contract) \
        if (outcome is not None and outcome.executable) else None
    ra["cham"] = cham_mot_ca(ca, bo_do, contract=contract, spec=spec,
                             outcome=outcome, schema_ok=spec is not None,
                             canh=canh, la_am=la_am)
    gac.ghi("score_stage_a", case_id=ca["id"],
            verdict=ra["cham"]["CANONICAL_VERDICT"])

    # ── ⑥ ĐỦ ĐIỀU KIỆN SỬA? Đọc luật SẢN PHẨM, không luật của bộ đo ─────
    import acceptance_verdict as AV

    ok_sua, ly_do = AV.sua_duoc(outcome, schema_ok=spec is not None,
                                error_code=None if spec is not None
                                else "schema")
    ra["repair_eligible"] = bool(ok_sua) and not la_am
    ra["repair_reason"] = ly_do if not la_am else "ca ÂM không được sửa"
    return ra


# ══════════════════════════════════════════════════════════════════════════
# §10 · CHẶNG B — TIẾP TỤC, đúng MỘT lượt sửa
# ══════════════════════════════════════════════════════════════════════════
async def _chay_stage_b(ca: dict, a: dict, bo_do: BoDo, gac: CanhGac,
                        api_key: str, base_da_chup: str,
                        raw_hong: dict) -> dict[str, Any]:
    from app.ai import gemini, pipeline
    from app.simulation.semantic_program.contract import generate_json_schema
    from app.simulation.semantic_program.domain_profile import (
        DOMAIN_HINH_HOC, program_skill_for)
    from app.simulation.semantic_program.obligations import Obligation
    from app.simulation.semantic_program.request_contract import RequestContract
    from app.simulation.semantic_program.route import verify_and_compile
    from app.simulation.semantic_program.validator import validate_semantic_program

    de = bo_do.payload_gui_model(ca)["problem_text"]
    hd = a["request_contract"]
    contract = RequestContract(
        problem_text=hd["problem_text"], input_facts=hd["input_facts"],
        obligations=tuple(Obligation(**o) for o in hd["obligations"]))

    chan_doan, nhanh = chan_doan_san_pham(raw_hong["raw_text"], contract)
    if chan_doan is None:
        return {"id": ca["id"], "bo_qua": True,
                "vi_sao": f"không có chẩn đoán để sửa ({nhanh})"}

    prompt = prompt_sua_chang_b(base_da_chup, raw_hong["raw_text"],
                                chan_doan, de, DOMAIN_HINH_HOC)
    gac.ghi("select_repair", case_id=ca["id"], nhanh_chan_doan=nhanh,
            frozen_contract_sha256=a["frozen_contract_sha256"],
            raw_candidate_sha256=raw_hong["raw_sha256"],
            diagnostic_sha256=_bam_chuoi(chan_doan))

    gac.truoc_luot_goi("repair")
    from app.ai.telemetry import stage_scope

    with stage_scope("semantic_program"):
        raw = await pipeline.call_gemini(
            api_key, gemini.load_skill(program_skill_for(DOMAIN_HINH_HOC)),
            prompt, generate_json_schema(), 0.1)
    ban = gac.sau_luot_goi("repair", prompt, raw, ca["id"], 1, 1)

    spec = None
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        payload = None
    if isinstance(payload, dict):
        v = validate_semantic_program(payload)
        spec = v.spec if v.ok else None
    outcome = verify_and_compile(contract, spec) if spec is not None else None
    canh = pipeline._dung_scene3d(spec, contract) \
        if (outcome is not None and outcome.executable) else None
    cham = cham_mot_ca(ca, bo_do, contract=contract, spec=spec,
                       outcome=outcome, schema_ok=spec is not None,
                       canh=canh, la_am=False)
    gac.ghi("score_stage_b", case_id=ca["id"],
            verdict=cham["CANONICAL_VERDICT"])
    return {
        "id": ca["id"], "bo_qua": False,
        "reuses": {
            "frozen_contract_sha256": a["frozen_contract_sha256"],
            "raw_initial_candidate_sha256": raw_hong["raw_sha256"],
            "diagnostic_sha256": _bam_chuoi(chan_doan),
            "base_prompt_sha256": _bam_chuoi(base_da_chup),
            "analyze_calls_in_stage_b": 0,
            "initial_synthesis_calls_in_stage_b": 0,
        },
        "diagnostic": chan_doan, "diagnostic_branch": nhanh,
        "repair_raw_sha256": ban["raw_sha256"],
        "chuong_trinh": spec.model_dump(mode="json") if spec else None,
        "cham": cham,
        "nhan": "RECOVERY_WITHIN_ONE_REPAIR",
    }


# ══════════════════════════════════════════════════════════════════════════
# ĐIỀU PHỐI
# ══════════════════════════════════════════════════════════════════════════
async def chay_lut(thu_muc: Path, *, provider: Callable | None,
                   api_key: str, bo_do: BoDo | None = None,
                   bo_qua_dirty: bool = False) -> dict[str, Any]:
    """Trọn vòng đời. `provider=None` ⇒ LIVE; khác `None` ⇒ stub.

    Cùng một thân hàm cho cả hai chế độ, cố ý: một đường chứng nhận đi khác
    đường live thì nó chứng nhận một thứ khác thứ sẽ chạy — đúng lỗ mà
    `V3_LIVE_ENTRYPOINT_INTEGRATION_BLOCKER` đã trả giá.
    """
    from acceptance_integrity import ghi_artifact, mo_run
    from app.ai import telemetry
    import measurement_policy as MP

    thu_muc = Path(thu_muc)
    bo_do = bo_do or nap_bo_do()
    if bo_do.lech:
        raise RunnerError("BĂM ĐÃ KHOÁ TRÔI:\n  " + "\n  ".join(bo_do.lech))

    gac = CanhGac(bo_do, thu_muc, gia_lap=provider is not None)
    gac.ghi("load_identity", candidate=bo_do.lock["CANDIDATE_HASH"][:16])
    gac.ghi("load_policy", policy_hash=bo_do.bam_nguong[:16])
    gac.ghi("load_corpus", positive=len(bo_do.ca_duong), negative=len(bo_do.ca_am))
    gac.ghi("verify_hashes", **bo_do.kiem)

    # ── MANIFEST TRƯỚC LƯỢT GỌI ĐẦU TIÊN ────────────────────────────────
    ns = bo_do.nguong["budget"]
    mo_run(
        thu_muc, run_id=thu_muc.name,
        muc_dich=("CHỨNG NHẬN runner — provider GIẢ, 0 lượt gọi thật"
                  if provider is not None
                  else "THESIS_FINAL_ACCEPTANCE — lượt đánh giá cuối"),
        runner=str(Path(__file__).resolve()), ca=bo_do.moi_ca,
        model=({"provider": "STUB", "application_llm_calls": 0}
               if provider is not None else MP.cau_hinh_model_hien_tai()),
        chinh_sach_sua="acceptance_verdict.sua_duoc — đọc luật sản phẩm",
        ngan_sach_goi=int(ns["MAX_LOGICAL_CALLS"]),
        bo_qua_dirty=bo_qua_dirty or provider is not None,
        duong_chinh_sach=CHINH_SACH,
        bo_sung={"thesis_final_acceptance": {
            "evaluation_class": bo_do.nguong["evaluation_class"][
                "EVALUATION_CLASS"],
            "created_before_first_call": True,
            "corpus_hash": bo_do.lock["CORPUS_HASH"],
            "expected_results_hash": bo_do.lock["EXPECTED_RESULTS_HASH"],
            "gold_preflight_hash": bo_do.lock["GOLD_PREFLIGHT_HASH"],
            "prompt_hash": bo_do.lock["PROMPT_HASH"],
            "grammar_card_hash": bo_do.lock["GRAMMAR_CARD_HASH"],
            "analyze_schema_hash": bo_do.lock["ANALYZE_SCHEMA_HASH"],
            "synthesis_schema_hash": bo_do.lock["SYNTHESIS_SCHEMA_HASH"],
            "capability_hash": bo_do.lock["CAPABILITY_HASH"],
            "max_logical_calls": int(ns["MAX_LOGICAL_CALLS"]),
            "max_physical_attempts": int(ns["MAX_PHYSICAL_ATTEMPTS"]),
            "hard_token_budget": int(ns["HARD_TOKEN_BUDGET"]),
            **bam_runner(),
        }})
    gac.ghi("write_manifest", sha256=_bam_tep(thu_muc / "manifest.json"))

    telemetry.reset_usage()
    #: case_id → `base` CHỤP ở lượt tổng hợp đầu tiên. Đây là cách duy nhất
    #: lấy được `base` mà không dựng lại nó — xem docstring module.
    chup: dict[str, str] = {}
    #: Ô ghi "đang chạy ca nào". Cổng bọc đọc STAGE từ `telemetry`, tức từ
    #: thẩm quyền của sản phẩm, chứ không đoán bằng nội dung prompt.
    dang: dict[str, Any] = {"id": "?", "attempt": 0}
    goc_call = __import__("app.ai.gemini", fromlist=["call_gemini"]).call_gemini
    ket_qua_a: list[dict] = []
    ket_qua_b: list[dict] = []

    async def _cong_bao(api, skill, prompt, schema, temp, *a, **kw):
        """CỔNG DUY NHẤT tới provider: chụp prompt · giữ raw · đếm."""
        stage = {"semantic_analyze": "analyze",
                 "semantic_program": "synthesis"}.get(
                     telemetry.current_stage(), "synthesis")
        if dang.get("stage") == "repair":
            stage = "repair"
        raw = await (provider(api, skill, prompt, schema, temp, *a, **kw)
                     if provider is not None
                     else goc_call(api, skill, prompt, schema, temp, *a, **kw))
        if stage != "repair":                 # chặng B tự ghi, tránh đếm đôi
            gac.sau_luot_goi(stage, prompt, raw, dang["id"], dang["attempt"], 1)
            if stage == "synthesis" and dang["attempt"] == 0:
                chup[dang["id"]] = prompt
        return raw

    with bao_provider(_cong_bao):
        # ── CHẶNG A ────────────────────────────────────────────────────
        for ca in bo_do.moi_ca:
            dang.update(id=ca["id"], attempt=0, stage="a")
            r = await _chay_stage_a(ca, bo_do, gac, api_key)
            ket_qua_a.append(r)
            print(f"  [A] {ca['id']:<34} {r['cham']['CANONICAL_VERDICT']}",
                  flush=True)

        _dong_chang_a(thu_muc, gac, ket_qua_a)

        # ── CHẶNG B ────────────────────────────────────────────────────
        theo_id = {c["id"]: c for c in bo_do.ca_duong}
        for r in ket_qua_a:
            if r["loai"] != "duong" or r["cham"].get("SERVABLE") \
                    or not r.get("repair_eligible") \
                    or "request_contract" not in r:
                continue
            raw_hong = _raw_cuoi(gac, r["id"], "synthesis")
            if raw_hong is None or r["id"] not in chup:
                continue
            dang.update(id=r["id"], attempt=1, stage="repair")
            b = await _chay_stage_b(theo_id[r["id"]], r, bo_do, gac, api_key,
                                    chup[r["id"]], raw_hong)
            dang["stage"] = "a"
            ket_qua_b.append(b)
            if not b["bo_qua"]:
                print(f"  [B] {r['id']:<34} "
                      f"{b['cham']['CANONICAL_VERDICT']}", flush=True)

    tt = _tong_ket(bo_do, gac, ket_qua_a, ket_qua_b, telemetry.usage_report())
    ghi_artifact(thu_muc / "stage_b_recovery.json",
                 {"artifact_schema_version": "1.2", "cases": ket_qua_b})
    for r in gac.raw:
        ghi_artifact(
            thu_muc / "raw" / r["case_id"]
            / f"{r['stage']}_{r['attempt_index']}.json", r)

    # ── DANH TÍNH SAU RUN, rồi mới ĐÓNG artifact ───────────────────────
    #
    # ⚠️ Ghi ĐÚNG MỘT LẦN. `ghi_artifact` từ chối đè — có chủ đích, bộ đo không
    # ghi đè lượt cũ — nên một bản nháp ghi trước rồi ghi lại sau phép kiểm sẽ
    # NÉM ở lần thứ hai. Thứ tự đúng: kiểm xong, gắn kết quả vào tổng kết, ghi.
    lai = BoDo(bo_do.thu_muc)
    tt["IDENTITY_AFTER_RUN_STABLE"] = not lai.lech
    tt["IDENTITY_AFTER_RUN_DRIFT"] = lai.lech
    gac.ghi("verify_identity_after", stable=not lai.lech)
    ghi_artifact(thu_muc / "final_scoring.json", tt)
    gac.ghi("write_final", sha256=_bam_tep(thu_muc / "final_scoring.json"))
    ghi_artifact(thu_muc / "event_log.json",
                 {"artifact_schema_version": "1.2", "events": gac.su_kien})
    return tt


def _raw_cuoi(gac: CanhGac, case_id: str, stage: str) -> dict | None:
    for r in reversed(gac.raw):
        if r["case_id"] == case_id and r["stage"] == stage:
            return r
    return None


def _dong_chang_a(thu_muc: Path, gac: CanhGac,
                  ket_qua: list[dict]) -> None:
    """ĐÓNG và BĂM chặng A trước khi chặng B chạy — §9.

    Không phải nghi thức: con số one-shot chỉ có nghĩa khi nó được ghi TRƯỚC
    khi bất kỳ lượt sửa nào có cơ hội làm nó đẹp lên."""
    from acceptance_integrity import ghi_artifact

    p = thu_muc / "stage_a_first_attempt.json"
    ghi_artifact(p, {"artifact_schema_version": "1.2",
                     "khai": "Chặng A — MỘT analyze, MỘT tổng hợp, 0 lượt sửa. "
                             "Đóng và băm TRƯỚC chặng B.",
                     "logical_calls_so_far": gac.logic,
                     "cases": ket_qua})
    gac.ghi("write_stage_a", sha256=_bam_tep(p))


def _tong_ket(bo_do: BoDo, gac: CanhGac, a: list[dict], b: list[dict],
              tk: dict) -> dict[str, Any]:
    duong = [r for r in a if r["loai"] == "duong"]
    am = [r for r in a if r["loai"] == "am"]
    cuoi = {r["id"]: r["cham"] for r in a}
    for x in b:
        if not x["bo_qua"]:
            cuoi[x["id"]] = x["cham"]
    dat = [i for i, c in cuoi.items() if c.get("SERVABLE")]
    tong_token = sum(v.get("total_tokens", 0) for v in tk.values())
    return {
        "artifact_schema_version": "1.2",
        "khai": "Chấm từng ca và tổng hợp. Ba cột EXACT · SCENE3D · SERVABLE "
                "ĐỘC LẬP; không cột nào suy từ cột khác.",
        "POSITIVE_CASES": len(duong), "NEGATIVE_CASES": len(am),
        "FIRST_ATTEMPT_SERVABLE": sum(
            1 for r in duong if r["cham"].get("SERVABLE")),
        "RECOVERY_WITHIN_ONE_REPAIR": sum(
            1 for x in b if not x["bo_qua"] and x["cham"].get("SERVABLE")),
        "FINAL_SERVABLE": sum(1 for r in duong if cuoi[r["id"]].get("SERVABLE")),
        "NEGATIVE_FAIL_CLOSED": sum(
            1 for r in am if r["cham"].get("NEGATIVE_FAIL_CLOSED")),
        "TARGET_BOUNDARY_PASS": sum(
            1 for r in am if r["cham"].get("TARGET_BOUNDARY_PASS")),
        # ⚠️ Ca ÂM được PHỤC VỤ cũng là một đáp số sai phát ra — policy nói
        # thẳng: *"gồm cả ca âm được phục vụ BẤT KỲ đáp số nào"*. Bản đầu chỉ
        # đếm `EXACT_ANSWER_MATCH is False`, mà ca âm không có cột ấy, nên
        # `.get()` trả `None` và một ca âm `servable` lọt qua với con số 0.
        # Bài chứng nhận bắt được đúng hình ấy: hai ca âm `servable` mà
        # `SILENT_WRONG_ANSWER_COUNT` vẫn báo 0.
        "SILENT_WRONG_ANSWER_COUNT": sum(
            1 for i, c in cuoi.items()
            if c.get("SERVABLE") and (c.get("EXACT_ANSWER_MATCH") is False
                                      or "NEGATIVE_FAIL_CLOSED" in c)),
        "SERVED_SCENE3D_MISMATCH_COUNT": sum(
            1 for i, c in cuoi.items()
            if c.get("SERVABLE") and c.get("SCENE3D_PASS") is False),
        "LOGICAL_CALLS": gac.logic,
        "PHYSICAL_ATTEMPTS": gac.vat_ly,
        "TOKEN_RESERVED": gac.token_da_dat_cho,
        "TOKENS_ACTUAL": tong_token,
        "TOKENS_PER_CORRECT_SERVABLE": (
            round(tong_token / len(dat)) if dat else None),
        "CALLS_PER_CORRECT_SERVABLE": (
            round(gac.logic / len(dat), 2) if dat else None),
        "DENOMINATOR_NOTE": "mẫu số là SỐ CA ĐẠT — in kèm, và KHÔNG so được "
                            "với một lượt đo có mẫu số khác",
        "budget": {"max_logical": gac.tran_logic,
                   "max_physical": gac.tran_vat_ly,
                   "hard_token": gac.tran_token},
        "verdicts": {i: c.get("CANONICAL_VERDICT") for i, c in cuoi.items()},
        "runner_owned_verdicts": sorted(
            i for i, c in cuoi.items() if c.get("runner_owned_class")),
        "stage_a": {r["id"]: r["cham"] for r in a},
        "stage_b": {x["id"]: x.get("cham") for x in b if not x["bo_qua"]},
        "negative_case_provider_calls": {
            r["id"]: (0 if r.get("stopped_before_provider") else
                      sum(1 for x in gac.raw if x["case_id"] == r["id"]))
            for r in am},
        "token_theo_stage": tk,
    }


# ══════════════════════════════════════════════════════════════════════════
def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--certify", action="store_true",
                   help="provider STUB, 0 lượt gọi thật")
    p.add_argument("--live", action="store_true",
                   help="⚠️ TIÊU QUOTA THẬT — lượt đánh giá cuối")
    p.add_argument("--out-dir", default=None)
    a = p.parse_args()

    if not (a.certify or a.live):
        print(__doc__.split("─── HAI CHẾ ĐỘ")[0])
        print("Chọn MỘT chế độ:  --certify  (0 lượt gọi)  |  --live  (tiêu quota)")
        bd = nap_bo_do()
        print(f"\n  bộ ca      {len(bd.ca_duong)} dương + {len(bd.ca_am)} âm")
        print(f"  băm đã khoá {'KHỚP' if not bd.lech else 'TRÔI'}")
        for l in bd.lech:
            print(f"    ✗ {l}")
        return 0 if not bd.lech else 1

    if a.certify and a.live:
        print("DỪNG: chọn MỘT chế độ.", file=sys.stderr)
        return 2
    if a.live:
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if os.environ.get("ALLOW_LIVE_AI") != "1" or not api_key:
            print("DỪNG: cần ALLOW_LIVE_AI=1 và GEMINI_API_KEY",
                  file=sys.stderr)
            return 2
        if not a.out_dir:
            print("DỪNG: --live đòi --out-dir", file=sys.stderr)
            return 2
        out = Path(a.out_dir)
        print("LƯỢT ĐÁNH GIÁ CUỐI — TIÊU QUOTA THẬT\n")
        tt = asyncio.run(chay_lut(out, provider=None, api_key=api_key))
    else:
        import certify_thesis_final_acceptance as CT

        return CT.main_tu_runner(a.out_dir)

    for k in ("POSITIVE_CASES", "NEGATIVE_CASES", "FIRST_ATTEMPT_SERVABLE",
              "RECOVERY_WITHIN_ONE_REPAIR", "FINAL_SERVABLE",
              "NEGATIVE_FAIL_CLOSED", "SILENT_WRONG_ANSWER_COUNT",
              "LOGICAL_CALLS", "TOKENS_ACTUAL"):
        print(f"  {k:34} {tt[k]}")
    return 0


if __name__ == "__main__":
    try:
        from dotenv import load_dotenv

        load_dotenv(BACKEND / ".env")
    except ImportError:
        pass
    raise SystemExit(main())
