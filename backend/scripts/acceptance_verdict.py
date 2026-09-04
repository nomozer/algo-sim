# -*- coding: utf-8 -*-
"""PHÁN QUYẾT MỘT CA ĐO — trích kết quả, tách lỗi HỆ khỏi lỗi MÔ HÌNH.

    `ACCEPTANCE_RUNNER_INTEGRITY`, 2026-09-04. **0 lượt gọi model.**

Bộ đo, ở `scripts/` — không thuộc `MEASURED_SYSTEM_PATHS`. Nó ĐỌC thẩm quyền
sản phẩm và không sửa gì trong `app/`.

─── BA CÂU KHÁC NHAU MÀ RUNNER CŨ GỘP LÀM MỘT ─────────────────────────────

    ① kết quả toán học là gì?          → `final_memory` (THẨM QUYỀN)
    ② hệ có chạy được bài không?       → `executable`
    ③ hệ có DÁM PHÁT kết quả không?    → `servable`

Runner V1/V2 rút cả ba thành `dap_so_khop: bool`, và rút nó từ **`scene3d`** —
tức từ tầng vẽ. Hệ quả đo được ở probe §18: `ball_1` tính đúng `R = 6`,
`V = 288π`, bị chặn ở `postconditions` nên không có `scene3d`, nên
`dai_luong = []`, nên `dap_so_khop = False`, nên bị xếp
**`MODEL_COMPOSITION_FAILURE`** — một lỗi HỆ bị tính vào cột năng lực mô hình.
Bản báo cáo sau đó phải đính chính bằng tay.
"""
from __future__ import annotations

from typing import Any

__all__ = [
    "LOP_PHAN_QUYET",
    "co_giai_doan",
    "cham_ca_am",
    "phan_loai",
    "sua_duoc",
    "trich_ket_qua",
]

#: §11 — chỗ DUY NHẤT được coi là thẩm quyền kết quả. `route.SemanticRouteOutcome`
#: nói thẳng trong docstring của trường: *"Trạng thái bộ nhớ CUỐI do interpreter
#: sinh. Đây là thứ duy nhất được đem so với ground truth độc lập — so với
#: `envelope` là so với thứ đã qua tay adapter thị giác."*
THAM_QUYEN_KET_QUA = "outcome.final_memory"

#: Những chỗ TUYỆT ĐỐI không được đọc làm kết quả toán học. Danh sách này có
#: mặt để `test_acceptance_runner_integrity` quét được mã runner.
CAM_DOC_KET_QUA = ("scene3d", "envelope", "display", "transport", "render")


def trich_ket_qua(outcome: Any) -> dict[str, Any]:
    """§11 — đại lượng chính xác, lấy từ `final_memory`.

    Trả `{"dai_luong": {tên: chuỗi hiển thị}, "nguon": …}`. Dùng `display()` của
    miền số chính xác, nên `288π` ra đúng `"288π"` chứ không phải `904.77…`.

    KHÔNG chạm `scene3d`: ở đó đại lượng chỉ xuất hiện khi ca đã `servable`, nên
    đọc nó là trộn câu hỏi *"kết quả là gì"* với *"hệ có dám phát không"*.
    """
    from app.simulation.geometry.radical import display, is_exact_number

    mem = getattr(outcome, "final_memory", None) or {}
    return {
        "nguon": THAM_QUYEN_KET_QUA,
        "dai_luong": {k: display(v) for k, v in sorted(mem.items())
                      if is_exact_number(v)},
    }


def co_giai_doan(outcome: Any, *, schema_ok: bool) -> dict[str, bool | str]:
    """§12 — bảy cờ RIÊNG BIỆT, không rút thành `correct`.

    `stage_reached` là thứ tự tuyến tính của route, nên "đã qua cổng X" =
    "dừng ở cổng sau X, hoặc chạy tới cùng". Đọc từ chính route chứ không suy
    từ mã lỗi (§13).
    """
    thu_tu = ["grounding", "structural_coverage", "ir_static", "execution",
              "realized_coverage", "source_invariant", "postconditions",
              "binding", "compile", "transport", "verification",
              "learner_surface", "served"]
    stage = getattr(outcome, "stage_reached", None) if outcome else None
    vi_tri = thu_tu.index(stage) if stage in thu_tu else -1

    def qua(ten: str) -> bool:
        return outcome is not None and vi_tri > thu_tu.index(ten)

    return {
        "schema_valid": bool(schema_ok),
        "grounding_pass": qua("grounding"),
        "coverage_pass": qua("structural_coverage"),
        "static_valid": qua("ir_static"),
        "runtime_executable": bool(getattr(outcome, "executable", False)),
        "postconditions_pass": qua("postconditions"),
        "servable": bool(getattr(outcome, "servable", False)),
        "stage_reached": stage or "khong_toi_route",
    }


#: §16 — repair-eligible ĐỌC TỪ LUẬT SẢN PHẨM, không phải luật của bộ đo.
#: `pipeline._sinh_chuong_trinh` gửi ngược đúng ba lớp lỗi cho mô hình sửa;
#: runtime xảy ra ở `verify_and_compile`, NGOÀI vòng sửa. Cho một ca runtime đi
#: sửa là dựng một hành vi sản phẩm không có, và con số thu được sẽ nói về
#: runner chứ không nói về hệ.
_STAGE_SUA_DUOC = ("ir_static", "grounding")


def sua_duoc(outcome: Any, *, schema_ok: bool,
             error_code: str | None = None) -> tuple[bool, str]:
    """Ca này có repair-eligible không, và VÌ SAO — cả hai đều phải ghi lại.

    ⚠️ Bản cũ đoán bằng cách khớp CHUỖI tiếng Việt trong thông báo lỗi
    (`"validation error" in err`, `"xuất xứ dữ liệu chưa đủ" in err`). Đổi một
    chữ trong thông điệp là đổi con số `REPAIR_ELIGIBLE` — và probe §18 ghi
    đúng vết ấy: *"bộ đo chạy 2; LUẬT SẢN PHẨM cho 3"*. Nay đọc `stage_reached`
    và `error_code`, tức đọc chính thứ route phát ra.
    """
    from app.simulation.error_codes import ErrorCode

    if not schema_ok:
        return True, "schema: lược đồ hỏng — pipeline gửi lỗi Pydantic ngược"
    if outcome is None:
        return False, "không có phán quyết route để đọc"
    if getattr(outcome, "servable", False):
        return False, "đã phục vụ được — không có gì để sửa"
    stage = getattr(outcome, "stage_reached", None)
    ma = error_code or getattr(outcome, "error_code", None)
    if stage in _STAGE_SUA_DUOC:
        if ma == ErrorCode.INPUT_NOT_GROUNDED.value:
            return True, f"{stage}: {ma} — pipeline gửi ngược cho mô hình sửa"
        if ma == ErrorCode.SEMANTIC_PROGRAM_INVALID.value:
            return True, f"{stage}: {ma} — kiểm tĩnh gửi ngược"
    return False, (
        f"stage '{stage}' (mã {ma}) nằm NGOÀI vòng sửa của "
        f"`pipeline._sinh_chuong_trinh` — cho nó đi sửa là dựng một hành vi "
        f"sản phẩm không có")


#: Thứ tự ưu tiên phân loại. Đọc từ TRÊN xuống, dừng ở nhánh khớp đầu tiên.
LOP_PHAN_QUYET = (
    "CORRECT_SERVABLE_RESULT",
    "CORRECT_EXECUTABLE_IR",
    "HONEST_UNSUPPORTED_REFUSAL",
    "UNRELATED_FAIL_CLOSED",
    "SYSTEM_COVERAGE_FAILURE",
    "SYSTEM_VERIFICATION_FAILURE",
    "SYSTEM_RUNTIME_FAILURE",
    "SYSTEM_TRANSPORT_FAILURE",
    "MODEL_SCHEMA_FAILURE",
    "MODEL_STATIC_FAILURE",
    "MODEL_GROUNDING_FAILURE",
    "MODEL_FIRST_BINDING_FAILURE",
    "MODEL_COMPOSITION_FAILURE",
)

#: `_LECH` của `geometry_obligations` — checker nói *"giá trị không khớp"* khi
#: nó ĐÃ tính lại được đại lượng từ hình. Đó là ranh giới §14: tính lại được mà
#: số lệch ⇒ chương trình sai (MÔ HÌNH); không tính nổi vì không nhận chủ thể ⇒
#: bộ kiểm hụt (HỆ).
def _postcondition_la_loi_mo_hinh(outcome: Any) -> bool:
    from app.simulation.semantic_program.geometry_obligations import _LECH

    chi_tiet = list(getattr(outcome, "details", None) or [])
    ly_do = getattr(outcome, "reason", None) or ""
    van = " · ".join([*chi_tiet, ly_do])
    return _LECH in van


def _cong_phu_hep_hon_bo_kiem() -> list[str]:
    """Có kiểu chủ thể nào bộ kiểm chứng thực được mà CỔNG PHỦ vẫn bác không?

    Đây là hình dạng chính xác của sự cố `CURVED_MODEL_ACCEPTANCE_V1`: bảng
    kiểu ở `OBLIGATION_KINDS` chép tay, thiếu `curved_solid`, trong khi
    `check_volume` xử lý được nó ⇒ chương trình ĐÚNG bị bác ở cổng phủ. Đó là
    đường DUY NHẤT còn lại để `REQUESTED_OPERATION_UNCOVERED` là lỗi HỆ.

    Trả danh sách `"nghia_vu:kieu"` bị bỏ rơi — rỗng nghĩa là hai bảng khớp, và
    khi ấy một lượt bác ở cổng phủ nói về CHƯƠNG TRÌNH chứ không về hệ.

    Cùng tiêu chí `test_measure_checker_subject_drift` dùng ở tầng tĩnh — một
    tiêu chí, hai người đọc. Từ 2026-09-03 `OBLIGATION_KINDS` DẪN XUẤT từ
    `BANG_PHEP_DO` nên bình thường danh sách này rỗng; hàm vẫn phải đo thật,
    vì cái đã trôi một lần thì trôi lại được, và bộ đo không được tin vào một
    bất biến mà chính nó không kiểm.
    """
    from app.simulation.semantic_program.geometry_obligations import (
        kieu_kiem_chung_duoc)
    from app.simulation.semantic_program.measure_contract import NGHIA_VU_DO
    from app.simulation.semantic_program.obligations import OBLIGATION_KINDS

    bo_roi = []
    for nv in NGHIA_VU_DO:
        cong = OBLIGATION_KINDS.get(nv, frozenset())
        for kieu in sorted(kieu_kiem_chung_duoc(nv) - cong):
            bo_roi.append(f"{nv}:{kieu}")
    return bo_roi


def phan_loai(outcome: Any, *, schema_ok: bool, la_ca_am: bool = False,
              boundary_ok: bool | None = None) -> str:
    """§13–§14 — phân loại TẤT ĐỊNH từ mã lỗi và `stage_reached`.

    ─── BẤT BIẾN TRUNG TÂM (§14) ───────────────────────────────────────────

    Chương trình HỢP LỆ theo hợp đồng gửi cho mô hình mà hệ hiện tại vẫn bác ⇒
    **SYSTEM_FAILURE**, không được tính vào độ chính xác của mô hình.

    Hai họ mã nói đúng điều đó, và cả hai đã xảy ra thật:

    `REQUESTED_OPERATION_UNCOVERED` — cổng phủ bác một phép hệ THẬT SỰ làm
    được. `CURVED_MODEL_ACCEPTANCE_V1`: ba chương trình cong ĐÚNG bị bác, 26
    lượt model để phát hiện một dòng lệch. ⚠️ Mã này **không tự nó** là lỗi hệ
    — nó cũng nổ khi chương trình khai sai kiểu một vật thẻ đã mô tả đúng.
    Phải ĐO bằng `_cong_phu_hep_hon_bo_kiem`; xem đính chính 2026-09-04 ở
    `phan_loai`.

    `POSTCONDITION_VIOLATED` / `SEMANTIC_VERIFICATION_UNAVAILABLE` với
    `failure_category = verification_gap` — *"hệ thực thi được bài này, nó chỉ
    chưa đủ điều kiện để PHÁT"*. Probe §18 `ball_1`: `V = 288π` đúng, checker
    không nhận `curved_solid`.

    ⚠️ Nhưng `POSTCONDITION_VIOLATED` **cũng** nổ khi chương trình khai một con
    số sai — và ca ấy là lỗi MÔ HÌNH thật. Phân biệt bằng chính lời checker:
    nói *"giá trị không khớp"* nghĩa là nó ĐÃ tính lại được từ hình rồi thấy
    lệch (mô hình sai); từ chối chủ thể hay không tính nổi nghĩa là bộ kiểm
    không với tới (hệ hụt). Cùng tiêu chí mà
    `test_measure_checker_subject_drift` dùng — một tiêu chí, hai người đọc.
    """
    from app.simulation.error_codes import ErrorCode

    if la_ca_am:
        # §15 — fail-closed CHƯA phải là chứng minh ranh giới.
        if boundary_ok is True:
            return "HONEST_UNSUPPORTED_REFUSAL"
        if boundary_ok is False:
            return "UNRELATED_FAIL_CLOSED"

    if not schema_ok:
        return "MODEL_SCHEMA_FAILURE"
    if outcome is None:
        return "MODEL_SCHEMA_FAILURE"

    if getattr(outcome, "servable", False):
        return "CORRECT_SERVABLE_RESULT"

    stage = getattr(outcome, "stage_reached", None)
    ma = getattr(outcome, "error_code", None)

    # ── Cổng phủ bác: HỆ hay MÔ HÌNH? Phải HỎI, không được đoán ──────────
    #
    # ⚠️ ĐÍNH CHÍNH 2026-09-04 (probe `probe-contract-waves`, ca `cylinder_2`).
    # Mã này TỪNG được xếp thẳng `SYSTEM_COVERAGE_FAILURE`, vì sự cố sinh ra
    # nhánh này — `CURVED_MODEL_ACCEPTANCE_V1` — đúng là lỗi hệ: bảng kiểu chép
    # tay thiếu `curved_solid`, nên ba chương trình cong ĐÚNG bị bác.
    #
    # Nhưng cùng một mã cũng nổ khi chương trình tự khai sai. `cylinder_2` đo
    # được: thẻ văn phạm ghi rõ `construct_section: solid:tên<solid>` và
    # `radius(of:tên<circle3|curved_solid>)`; mô hình vẫn cắt khối CONG bằng
    # `construct_section` rồi đo `radius` trên một `section`. Hệ có sẵn đường
    # đúng (`intersect_plane_curved` → `circle3`) và đã khai nó trên thẻ. Cổng
    # phán ĐÚNG; bên thiếu là mô hình.
    #
    # Xếp ca ấy vào cột HỆ là lỗi ngược chiều của cùng một bệnh đã đính chính ở
    # `LEARNER_SURFACE_INCOMPLETE` bên dưới: đọc MÃ LỖI thay vì đọc câu hỏi mà
    # bất biến §14 thật sự đặt ra — *chương trình có HỢP LỆ theo hợp đồng gửi
    # cho mô hình không?* Và nó tốn thật: luật DỪNG-KHI-LỖI-HỆ nổ nhầm, lượt đo
    # chết trước ca thứ hai.
    #
    # Nay hỏi thẳng hai thẩm quyền. `REQUESTED_OPERATION_UNCOVERED` chỉ phát ra
    # từ nhánh `missing` của `coverage_gate` — mọi mục `missing` đều nói về thứ
    # CHƯƠNG TRÌNH khai (chưa khai container · sai kiểu · witness không dẫn
    # xuất). Kind nằm ngoài taxonomy thì rơi vào `weak`, tức mã KHÁC. Nên lỗi
    # hệ chỉ còn một đường: bảng kiểu của cổng HẸP HƠN thứ bộ kiểm chứng thực
    # được — đúng vết V1. `_cong_phu_hep_hon_bo_kiem` đo lại đường ấy mỗi lượt;
    # trôi trở lại thì nhãn tự lật về HỆ mà không cần ai nhớ ra.
    if ma == ErrorCode.REQUESTED_OPERATION_UNCOVERED.value:
        return ("SYSTEM_COVERAGE_FAILURE"
                if _cong_phu_hep_hon_bo_kiem()
                else "MODEL_COMPOSITION_FAILURE")
    if ma == ErrorCode.OBLIGATION_WITNESS_UNREALIZED.value:
        return "MODEL_COMPOSITION_FAILURE"

    # ── HỆ: chạy đúng nhưng không chứng thực được ────────────────────────
    if ma == ErrorCode.SEMANTIC_VERIFICATION_UNAVAILABLE.value:
        # KHÔNG CÓ checker cho nghĩa vụ ấy — hệ hụt, không phải mô hình sai.
        return "SYSTEM_VERIFICATION_FAILURE"

    # ⚠️ ĐÍNH CHÍNH 2026-09-04 (probe V2 lượt 1). `LEARNER_SURFACE_INCOMPLETE`
    # TỪNG bị xếp `SYSTEM_VERIFICATION_FAILURE` ở đây, vì `failure_category`
    # của nó là `verification_gap` và tôi đọc nhãn ấy thay vì đọc cổng.
    #
    # Sai. `learner_surface` hỏi *"biến ĐÁNG THẤY có được khai binding không"*
    # — tức hỏi về thứ **chương trình** cung cấp. Ca `ball_1` lượt 1 phơi ra:
    # chương trình chạy đúng, `postconditions_pass=True`, `R = 6`, `V = 288π`,
    # rồi `visual_bindings` rỗng nên `IA_dist` (mang dữ kiện đề) không có đường
    # lên màn hình. Cổng phán ĐÚNG; mô hình mới là bên thiếu.
    #
    # Xếp nó vào cột HỆ là đúng cái lỗi mà cả tuyến này dựng ra để chặn, chỉ
    # theo chiều ngược: thay vì đổ lỗi hệ cho mô hình, nó đổ lỗi mô hình cho
    # hệ — và một bộ đo như thế sẽ báo "hệ hỏng" mãi trong khi prompt mới là
    # chỗ cần sửa. Nó còn làm luật DỪNG-KHI-LỖI-HỆ nổ nhầm, và lượt đo chết
    # giữa chừng đúng như đã xảy ra.
    #
    # Cùng họ với stage `binding` (`VisualBindingUnresolved`): hai chiều của
    # một hợp đồng thị giác, cả hai đều do chương trình khai thiếu.
    if ma == ErrorCode.LEARNER_SURFACE_INCOMPLETE.value:
        return "MODEL_FIRST_BINDING_FAILURE"
    if ma == ErrorCode.POSTCONDITION_VIOLATED.value:
        return ("MODEL_COMPOSITION_FAILURE"
                if _postcondition_la_loi_mo_hinh(outcome)
                else "SYSTEM_VERIFICATION_FAILURE")

    # ── MÔ HÌNH ──────────────────────────────────────────────────────────
    if stage == "grounding":
        return "MODEL_GROUNDING_FAILURE"
    if stage == "ir_static":
        return "MODEL_STATIC_FAILURE"
    if stage == "binding":
        return "MODEL_FIRST_BINDING_FAILURE"
    if stage == "execution":
        if ma == ErrorCode.INTERPRETER_BUDGET_EXHAUSTED.value:
            return "SYSTEM_RUNTIME_FAILURE"
        return "MODEL_COMPOSITION_FAILURE"
    if stage in ("compile", "transport"):
        return "SYSTEM_TRANSPORT_FAILURE"

    if getattr(outcome, "executable", False):
        return "CORRECT_EXECUTABLE_IR"
    return "MODEL_COMPOSITION_FAILURE"


def cham_ca_am(ca: dict, outcome: Any, *, schema_ok: bool,
               error_code: str | None = None) -> dict[str, Any]:
    """§15 — ca âm chỉ ĐẠT khi chạm ĐÚNG ranh giới nó tuyên bố nhắm tới.

    ⚠️ SỰ CỐ ⑥: một ca âm nhắm *"thiết diện cong xiên chưa hỗ trợ"* chết sớm ở
    `UNANCHORED_DERIVED_ASSUMPTION` (R0). Fail-closed thì đúng — nhưng nó
    **không chứng minh** ranh giới định đo, vì chương trình chưa bao giờ chạm
    tới đó. Gọi nó `HONEST_REFUSAL` là ghi công cho một phép thử chưa diễn ra.

    Ca âm phải khai trước `target_boundary` + `expected_codes`; chỉ khi mã lỗi
    thật thuộc họ ấy thì `TARGET_BOUNDARY_DEMONSTRATED = True`.
    """
    ma = error_code or getattr(outcome, "error_code", None)
    stage = getattr(outcome, "stage_reached", None)
    mong_ma = tuple(ca.get("expected_codes") or ())
    mong_stage = tuple(ca.get("expected_stages") or ())
    if not mong_ma and not mong_stage:
        raise ValueError(
            f"ca âm '{ca.get('id')}' phải khai `expected_codes` hoặc "
            f"`expected_stages` — không khai thì không có gì để chứng minh, "
            f"và mọi lượt chết đều trông như thành công")

    fail_closed = not bool(getattr(outcome, "servable", False))
    trung = (ma in mong_ma) if mong_ma else False
    trung = trung or ((stage in mong_stage) if mong_stage else False)
    return {
        "target_boundary": ca.get("target_boundary"),
        "expected_codes": list(mong_ma),
        "expected_stages": list(mong_stage),
        "actual_code": ma,
        "actual_stage": stage,
        "fail_closed": fail_closed,
        "target_boundary_demonstrated": bool(fail_closed and trung),
        "ghi_chu": (
            "" if trung else
            f"DỪNG SỚM: chạm '{ma or stage}' trước khi tới ranh giới định đo "
            f"'{ca.get('target_boundary')}' — fail-closed đúng, nhưng KHÔNG "
            f"chứng minh ranh giới ấy"),
    }
