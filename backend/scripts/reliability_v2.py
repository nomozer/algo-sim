# -*- coding: utf-8 -*-
"""Chỉ số Reliability V2 — phân loại thất bại theo CỔNG ĐẦU TIÊN. **0 API call.**

Thuần harness: file này chỉ **đọc** bản ghi observer và **suy ra** nhãn. Không
gọi engine, không đổi hành vi, không quyết định gì trong đường phát.

VÌ SAO TÁCH RA KHỎI RUNNER: phần phân loại là thứ dễ viết sai nhất và là thứ đi
thẳng vào bảng của luận văn, nên nó phải **kiểm được offline bằng dữ liệu bịa**,
không cần chạy lượt đo. Runner thì chỉ được chạy một lần.

LUẬT PHÂN LOẠI (`RELIABILITY_EVALUATION_PLAN §4`): mỗi case nhận **đúng một**
nhãn, gán theo **cổng ĐẦU TIÊN** nó chết. Gán theo cổng cuối cùng chạm tới là
đếm một case vào nhiều lớp và tổng vượt N.

RANH GIỚI ĐÃ ĐO ĐƯỢC (2026-08-24): `semantic_program_invalid` **gộp hai lớp
khác hẳn nhau** — lỗi cú pháp Pydantic (lớp 2) và lỗi thẩm định ngữ nghĩa
(lớp 3). Phân biệt bằng chuỗi lý do: Pydantic luôn có `"validation error… for
SemanticProgramSpec"`. Không tách thì lớp 2 nuốt trọn lớp 3, và bảng thất bại
nói sai chỗ phải sửa.
"""
from __future__ import annotations

from typing import Any

# ── Nhãn tầng, ĐÓNG. Thứ tự = thứ tự cổng trong pipeline. ──────────────────
LAYER_CONTRACT = 0
LAYER_GENERATION = 1
LAYER_SCHEMA = 2
LAYER_SEMANTIC_VALIDATION = 3
LAYER_INTERPRETER = 4
LAYER_REPLAY = 5
LAYER_ASSURANCE = 6
LAYER_RENDERING = 7

TEN_TANG: dict[int, str] = {
    LAYER_CONTRACT: "contract_failure",
    LAYER_GENERATION: "generation_failure",
    LAYER_SCHEMA: "schema_failure",
    LAYER_SEMANTIC_VALIDATION: "semantic_validation_failure",
    LAYER_INTERPRETER: "interpreter_failure",
    LAYER_REPLAY: "replay_failure",
    LAYER_ASSURANCE: "assurance_failure",
    LAYER_RENDERING: "rendering_failure",
}

#: `stage_reached` khi route chết TRƯỚC khi LLM kịp phát IR ⇒ lớp 0.
#: `scope` và `execution_authority` KHÔNG phải thất bại sinh: chặn một đề ngoài
#: môn là hành vi ĐÚNG. Báo riêng, đừng gộp vào tử số thất bại (§4 luật 1).
_STAGE_LOP_0 = {"scope", "execution_authority", "grounding", "semantic_analyze"}

#: Mã lỗi ở cổng assurance — chạy được nhưng không đủ bằng chứng để phát.
_MA_ASSURANCE = {
    "requested_operation_uncovered",
    "postcondition_violated",
    "verification_gap",
    "realized_coverage_unwitnessed",
}

#: Dấu vân tay của lỗi Pydantic. `stage_semantic_program` bọc nó thành
#: `"SEMANTIC_PROGRAM_INVALID: Lỗi cú pháp schema SemanticProgramSpec: …"`, còn
#: validator ngữ nghĩa trả câu khác hẳn.
_DAU_PYDANTIC = ("validation error", "SemanticProgramSpec")

#: LLM không phát nổi đầu ra dùng được — khác hẳn "phát ra nhưng sai hình dạng".
_DAU_GENERATION = ("JSON không parse được", "không phải một đối tượng JSON")


def _la_loi_pydantic(reason: str) -> bool:
    return all(d in reason for d in _DAU_PYDANTIC)


def _la_loi_generation(reason: str) -> bool:
    return any(d in reason for d in _DAU_GENERATION)


def phan_loai(
    semantic: dict[str, Any] | None,
    replay_ok: bool | None = None,
    render_ok: bool | None = None,
) -> tuple[int | None, str | None]:
    """Bản ghi route → `(layer, failure_code)`. `(None, None)` = đi trọn đường.

    `replay_ok`/`render_ok` là **None khi CHƯA ĐO**, không phải False. Trộn
    "chưa đo" với "trượt" là bịa thêm thất bại — và bịa theo hướng bi quan cũng
    vẫn là bịa.
    """
    if semantic is None:
        return LAYER_CONTRACT, "no_semantic_record"

    stage = semantic.get("stage_reached")
    code = semantic.get("error_code")
    reason = semantic.get("reason") or ""

    # ── cổng ① hợp đồng / phạm vi ────────────────────────────────────────
    if stage in _STAGE_LOP_0:
        return LAYER_CONTRACT, code or stage

    # ── cổng ② sinh IR ───────────────────────────────────────────────────
    if stage == "semantic_program":
        if _la_loi_generation(reason):
            return LAYER_GENERATION, "llm_output_unusable"
        if _la_loi_pydantic(reason):
            return LAYER_SCHEMA, code or "semantic_program_invalid"
        # Không mang dấu Pydantic ⇒ validator NGỮ NGHĨA từ chối. Gộp nó vào
        # lớp 2 là chỉ sai chỗ phải sửa: lớp 2 chữa bằng biên chuẩn hoá, lớp 3
        # thì không.
        return LAYER_SEMANTIC_VALIDATION, code or "semantic_program_invalid"

    # ── cổng ④ interpreter ───────────────────────────────────────────────
    if stage == "execution" or code in (
        "interpreter_budget_exhausted", "semantic_execution_error"
    ):
        return LAYER_INTERPRETER, code or "execution_failed"

    # ── cổng ⑥ assurance ─────────────────────────────────────────────────
    if code in _MA_ASSURANCE or stage in (
        "structural_coverage", "realized_coverage", "postconditions", "verification"
    ):
        return LAYER_ASSURANCE, code or stage

    # ── cổng ⑦ dựng cảnh ─────────────────────────────────────────────────
    if stage in ("binding", "compile"):
        return LAYER_RENDERING, code or stage

    # Tới đây route đã nói `served`. Hai tầng quan trắc mới xét SAU, và chỉ khi
    # THẬT SỰ đã đo — `None` thì im lặng, không phán.
    if replay_ok is False:
        return LAYER_REPLAY, "replay_input_ignored_or_dead_state"
    if render_ok is False:
        return LAYER_RENDERING, "render_failed"

    if code:
        return LAYER_ASSURANCE, code
    return None, None


def obligation_match(
    mong_doi: list[str] | None, khai: list[str] | None
) -> dict[str, Any]:
    """Nghĩa vụ LLM khai có ĐÚNG LOẠI đề hỏi không.

    VÌ SAO CẦN, và vì sao KHÔNG cổng nào bắt được: checker chỉ kiểm nghĩa vụ
    **đã khai** có được thoả không. Đề hỏi *"chứng minh SA ⊥ (ABCD)"* mà LLM
    khai `volume` rồi tính thể tích đúng thì checker PASS, C₂ PASS, oracle
    PASS — hệ trả lời **đúng một câu không ai hỏi**.

    Chỗ duy nhất phát hiện được là ở đây, vì chỉ bộ đo mới biết đề **mong đợi**
    gì (`expected_obligations` của DEV set).

    ⚠️ **QUAN TRẮC, KHÔNG gác cửa** — cố ý không vào `servable`, và cố ý không
    vào `ok` của bất kỳ cổng nào. Lý do: "đề mong đợi nghĩa vụ nào" là phán
    đoán của **người soạn đề**, không phải sự thật toán học. Một đề có thể
    chứng minh được bằng nhiều đường, và biến phán đoán ấy thành cổng là dựng
    một oracle thứ hai không ai kiểm chứng.
    """
    m, k = set(mong_doi or ()), set(khai or ())
    return {
        "mong_doi": sorted(m),
        "khai": sorted(k),
        "khop": sorted(m & k),
        "thieu": sorted(m - k),
        "thua": sorted(k - m),
        # `khop_hoan_toan` chỉ đúng khi hai tập TRÙNG NHAU. Khai thừa cũng là
        # lệch: nó nghĩa là mô hình trả lời thêm thứ đề không hỏi, và ở một bài
        # đánh giá thì thừa cũng che mất chỗ nó thiếu.
        "khop_hoan_toan": bool(m) and m == k,
    }


def chi_so_case(
    source_id: str | None,
    semantic: dict[str, Any] | None,
    cham: dict[str, Any] | None = None,
    replay_ok: bool | None = None,
    render_ok: bool | None = None,
    mong_doi_obl: list[str] | None = None,
    khai_obl: list[str] | None = None,
) -> dict[str, Any]:
    """Khối V2 của MỘT case. Chỉ thêm khoá, không đụng khoá cũ của runner."""
    layer, code = phan_loai(semantic, replay_ok, render_ok)
    s = semantic or {}
    stage = s.get("stage_reached")
    reason = s.get("reason") or ""

    da_qua_sinh = stage not in (None, *_STAGE_LOP_0, "semantic_program")
    g1 = da_qua_sinh or (stage == "semantic_program" and not _la_loi_pydantic(reason)
                         and not _la_loi_generation(reason))
    g2 = da_qua_sinh

    verdict = (cham or {}).get("verdict")
    oracle_o = True if verdict == "PASS" else (False if verdict == "FAIL" else None)

    return {
        "source_id": source_id,
        # G1/G2 chỉ có nghĩa khi LLM đã phát ra một cái gì đó. Chết ở lớp 0 thì
        # cả hai là None — báo `False` ở đó là đổ lỗi sinh cho một case chưa
        # bao giờ tới bước sinh.
        "G1_schema_pass": None if stage in (None, *_STAGE_LOP_0) else bool(g1),
        "G2_semantic_validation_pass": None if stage in (None, *_STAGE_LOP_0) else bool(g2),
        "executable_A": bool(s.get("executable")),
        "replay_R": replay_ok,
        "assurance_B": bool(s.get("servable")),
        "renderer_V": render_ok,
        "oracle_O": oracle_o,
        "failure_layer": layer,
        "failure_layer_ten": TEN_TANG.get(layer) if layer is not None else None,
        "failure_code": code,
        # QUAN TRẮC, không gác cửa. `None` khi bộ đo không khai `expected` —
        # phân biệt "không lệch" với "chưa đo", cùng luật `replay_R`.
        "obligation_match": (
            obligation_match(mong_doi_obl, khai_obl)
            if mong_doi_obl is not None else None
        ),
    }


def tong_hop(khoi: list[dict[str, Any]]) -> dict[str, Any]:
    """Gộp per-case → bảng V2. **Chỉ số ĐẾM, không phần trăm.**

    `RELIABILITY_EVALUATION_PLAN §3.3` cấm viết phần trăm khi mẫu số < 20, và
    mẫu số của `R`/`O`/`V` là *số ca đã qua tầng trước* — ở lượt #1 con số đó là
    3 và 1. Nên hàm này **không tính tỉ lệ**: nó phát ra tử số và mẫu số, còn
    việc có được phép chia hay không thuộc về người viết báo cáo.
    """
    n = len(khoi)

    def dem(khoa: str, mau: list[dict] | None = None) -> dict[str, Any]:
        nguon = khoi if mau is None else mau
        that = [k for k in nguon if k[khoa] is True]
        chua_do = [k for k in nguon if k[khoa] is None]
        return {"tu_so": len(that), "mau_so": len(nguon) - len(chua_do),
                "chua_do": len(chua_do)}

    co_a = [k for k in khoi if k["executable_A"]]
    co_b = [k for k in khoi if k["assurance_B"]]
    phan_bo: dict[str, int] = {}
    for k in khoi:
        ten = k["failure_layer_ten"] or "di_tron_duong"
        phan_bo[ten] = phan_bo.get(ten, 0) + 1

    return {
        "khai": "ĐẾM THÔ, không phần trăm — §3.3 cấm chia khi mẫu số < 20, và "
                "mẫu số của R/O/V là số ca đã qua tầng trước.",
        "N": n,
        "G1_schema": dem("G1_schema_pass"),
        "G2_semantic_validation": dem("G2_semantic_validation_pass"),
        "A_executable": {"tu_so": len(co_a), "mau_so": n},
        "R_replay": dem("replay_R", co_a),
        "B_assurance": {"tu_so": len(co_b), "mau_so": n},
        "V_renderer": dem("renderer_V", co_b),
        "O_oracle": dem("oracle_O"),
        "phan_bo_tang_that_bai": dict(sorted(phan_bo.items(), key=lambda kv: -kv[1])),
        "tong_kiem": sum(phan_bo.values()),
        "obligation_match": _gop_obligation_match(khoi),
    }


def _gop_obligation_match(khoi: list[dict[str, Any]]) -> dict[str, Any]:
    """Gộp `obligation_match`. ĐẾM THÔ, và báo RIÊNG khỏi mọi chỉ số cổng.

    Đặt cạnh `A`/`B` chứ không trộn vào: một ca `khop_hoan_toan=False` vẫn có
    thể `executable` và `servable` — nó chỉ nghĩa là mô hình giải một bài khác.
    Trộn hai thứ lại là bịa ra một con số không đo cái gì cả.
    """
    co = [k["obligation_match"] for k in khoi if k.get("obligation_match")]
    if not co:
        return {"chua_do": len(khoi), "khai": "bộ đo không cung cấp expected"}
    thieu = sorted({o for m in co for o in m["thieu"]})
    thua = sorted({o for m in co for o in m["thua"]})
    return {
        "khai": "QUAN TRẮC — không gác cửa, không vào A/B. Lệch nghĩa là mô "
                "hình giải một bài KHÁC, dù chương trình có thể vẫn chạy đúng.",
        "khop_hoan_toan": sum(1 for m in co if m["khop_hoan_toan"]),
        "mau_so": len(co),
        "chua_do": len(khoi) - len(co),
        "nghia_vu_hay_bi_THIEU": thieu,
        "nghia_vu_hay_bi_KHAI_THUA": thua,
    }
