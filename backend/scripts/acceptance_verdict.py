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

from dataclasses import dataclass
from typing import Any

__all__ = [
    "LOP_PHAN_QUYET",
    "co_giai_doan",
    "cham_ca_am",
    "YeuCauNangLuc",
    "duong_hop_le_ton_tai",
    "nghia_vu_du_noi_dung_hut_ten",
    "o_vo_huong_bi_rang_buoc_mo_ho",
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
    # ─── 2026-09-04 · `ACCEPTANCE_SCORER_EXPRESSIVENESS_CLASS` ────────────
    #
    # Hệ CHƯA CÓ ĐƯỜNG biểu đạt cho một phép toán ĐÚNG mà đề đòi. Khác hẳn
    # `MODEL_*`: ở đó mô hình đi sai một đường đang tồn tại; ở đây **không có
    # đường nào để đi**.
    #
    # Lỗ nó bịt, đo được ở pre-draw guard của `CURVED_V3_LIVE_ACCEPTANCE`: đề
    # cho ĐƯỜNG KÍNH thì `r = d/2` là bước đúng về toán, nhưng `arith` cho kiểu
    # tĩnh `unknown` và ô `radius` chỉ nhận `scalar|float|int` ⇒ chương trình
    # chết ở `ir_static` và bị xếp `MODEL_STATIC_FAILURE`. Quy sai trách nhiệm
    # đúng chiều mà cả tuyến probe này tồn tại để chặn.
    "SYSTEM_EXPRESSIVENESS_GAP",
    "SYSTEM_RUNTIME_FAILURE",
    "SYSTEM_TRANSPORT_FAILURE",
    "MODEL_SCHEMA_FAILURE",
    "MODEL_STATIC_FAILURE",
    "MODEL_GROUNDING_FAILURE",
    "MODEL_FIRST_BINDING_FAILURE",
    "MODEL_COMPOSITION_FAILURE",
    # ─── CHƯA KẾT LUẬN, và đó là một phán quyết ĐẦY ĐỦ ───────────────────
    #
    # Thiếu bằng chứng về `valid_path_exists` thì bộ đo **không được** chọn
    # bừa một bên. Quy cho mô hình khi chưa biết là bơm sai số vào cột năng
    # lực mô hình; quy cho hệ khi chưa biết là bơm sai số vào cột lỗi hệ. Cả
    # hai đều tệ hơn một ô ghi "chưa biết" mà người đọc thấy được.
    "ATTRIBUTION_UNRESOLVED",
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


@dataclass(frozen=True)
class YeuCauNangLuc:
    """Điều một ca ĐÒI HỎI, khai bằng **KIỂU**, không bằng câu chữ của đề.

    Đây là *input contract* của bộ chấm cho câu hỏi trách nhiệm. Nó cố ý KHÔNG
    chở đề bài, không chở đáp số, không chở case id — bộ chấm không được phép
    nhận ra một ca bằng nội dung, chỉ bằng hình dạng NĂNG LỰC.

    `can_bien_doi` là trục phân biệt trung tâm, và nó là lý do quy tắc này
    không biến mọi lỗi `radius` thành lỗi hệ:

        đề cho THẲNG bán kính   → can_bien_doi=False → dùng ngay, ĐƯỜNG CÓ
        đề cho ĐƯỜNG KÍNH       → can_bien_doi=True  → phải chia đôi, ĐƯỜNG KHÔNG
    """

    #: Tên ô toán hạng đích, vd `"radius"`. Chỉ để đọc — không dùng để phán.
    o_dich: str
    #: Kiểu tĩnh ô ấy nhận. DẪN từ `_TOAN_HANG_LENH`, không gõ tay.
    kieu_o_dich: frozenset[str]
    #: Kiểu tĩnh của dữ kiện ĐÃ GROUNDED mà ca cấp cho ô ấy.
    kieu_nguon: frozenset[str]
    #: Ca có đòi một phép BIẾN ĐỔI giá trị không, hay dùng thẳng dữ kiện?
    can_bien_doi: bool
    #: Mô tả phép biến đổi, cho người đọc. Không tham gia phán quyết.
    phep_can: str = ""


def _phep_bien_doi_giu_kieu(nguon: frozenset[str],
                            dich: frozenset[str]) -> list[str]:
    """Phép nào nhận kiểu `nguon` và trả một kiểu `dich` NHẬN ĐƯỢC?

    ─── VÌ SAO ĐI TỪ CHỮ KÝ, KHÔNG TỪ CHUỖI LỖI ───────────────────────────

    `ERR_RANG_BUOC_MO_HO` và cái tên `radius` chỉ là **dấu hiệu**. Một bộ chấm
    kết luận "lỗi hệ" từ một mã lỗi sẽ nói sai ngay lần đầu mô hình viết
    `arith` bậy trên một ca mà đường hợp lệ vốn có sẵn.

    Nên câu hỏi phải hỏi thẳng vào **bảng chữ ký**: trong toàn bộ tập phép của
    IR, có phép nào biến một giá trị kiểu `nguon` thành một giá trị mà ô đích
    nhận không? Rỗng ⇒ hệ không có đường, bất kể mô hình viết gì.
    """
    from app.simulation.semantic_program.ir_static_check import (
        _CHU_KY, _kieu_ket_qua)

    class _Nut:                       # nút giả, chỉ mang `kind`
        def __init__(self, k): self.kind = k

    ra = []
    for k in sorted(set(_CHU_KY) | {"arith", "unary", "literal", "measure", "var"}):
        if k in _CHU_KY:
            vao = {t for (_n, tt) in _CHU_KY[k][0] for t in tt}
            kq = _CHU_KY[k][1]
        else:
            # `arith`/`unary` nhận biểu thức bất kỳ (kể cả vô hướng);
            # `measure` nhận đúng những kiểu `BANG_PHEP_DO` khai.
            if k == "measure":
                from app.simulation.semantic_program.measure_contract import (
                    BANG_PHEP_DO)
                vao = {t for p in BANG_PHEP_DO.values() for t in p.kieu_of}
            elif k in ("arith", "unary"):
                vao = set(nguon)      # nhận mọi biểu thức
            else:
                vao = set()
            kq = _kieu_ket_qua(_Nut(k), {})
        if (vao & nguon) and kq in dich:
            ra.append(f"{k}→{kq}")
    return ra


def duong_hop_le_ton_tai(yc: YeuCauNangLuc | None) -> str:
    """`"YES"` · `"NO"` · `"UNKNOWN"` — hệ có đường cho điều ca đòi không?

    `UNKNOWN` khi không có bằng chứng năng lực. Đó là một phán quyết đầy đủ,
    không phải một chỗ trống để đoán: bộ đo thà ghi "chưa biết" còn hơn quy
    trách nhiệm sai.
    """
    if yc is None:
        return "UNKNOWN"
    if not yc.can_bien_doi:
        # Dùng thẳng: đường tồn tại ⟺ kiểu nguồn đã được ô đích nhận.
        return "YES" if (yc.kieu_nguon & yc.kieu_o_dich) else "NO"
    return "YES" if _phep_bien_doi_giu_kieu(yc.kieu_nguon, yc.kieu_o_dich) else "NO"


#: Giai đoạn mà một khoảng trống NĂNG LỰC biểu đạt có thể lộ ra. Ngoài hai chỗ
#: này thì chương trình đã qua được tầng kiểu, nên thất bại nói về thứ khác.
_GIAI_DOAN_LO_NANG_LUC = ("ir_static", "structural_coverage")


def o_vo_huong_bi_rang_buoc_mo_ho(outcome: Any, spec: Any) -> list[str]:
    """Ô toán hạng đòi VÔ HƯỚNG nào đang được nuôi bằng một ràng buộc mơ hồ?

    ─── VAI TRÒ: KHÔNG kết luận, chỉ TỪ CHỐI kết luận ─────────────────────

    Hình dạng này **không đủ** để nói "hệ thiếu năng lực" — §B nói rõ
    `ERR_RANG_BUOC_MO_HO` và cái tên `radius` chỉ là dấu hiệu. Nhưng nó **đủ để
    không quy cho mô hình**: đúng hình dạng ấy là thứ xuất hiện khi đề đòi một
    phép biến đổi vô hướng mà IR không biểu đạt được, và cũng là thứ xuất hiện
    khi mô hình viết bậy. Hai nguyên nhân, một dấu hiệu ⇒ chưa kết luận được.

    Ô nào "đòi vô hướng" **dẫn từ `_TOAN_HANG_LENH`**, không gõ tên `radius`:
    thêm một ô vô hướng sau này là quy tắc tự nhận, không phải một dòng phải sửa.
    """
    from app.simulation.semantic_program.ir_static_check import (
        _TOAN_HANG_LENH, ERR_RANG_BUOC_MO_HO, SO_DO)

    if spec is None:
        return []
    van = " ".join(str(x) for x in (getattr(outcome, "details", None) or []))
    if ERR_RANG_BUOC_MO_HO not in van:
        return []
    vo_huong = {SO_DO, "float", "int"}
    o_vh = {lenh: {n for n, kieu, _l in oper if set(kieu) & vo_huong}
            for lenh, oper in _TOAN_HANG_LENH.items()}
    ra = []
    for st in (getattr(spec, "statements", None) or ()):
        for ten_o in o_vh.get(getattr(st, "kind", None), ()):
            if (gt := getattr(st, ten_o, None)) and isinstance(gt, str):
                ra.append(f"{st.kind}.{ten_o}={gt}")
    return ra


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


def nghia_vu_du_noi_dung_hut_ten(contract: Any, spec: Any) -> list[str]:
    """Nghĩa vụ nào chương trình ĐÃ tính đúng, và chỉ hụt ở chỗ BUỘC TÊN?

    Đo được ở `probe-contract-waves-2` ca `circumsphere`. Mô hình dựng tâm mặt
    cầu ngoại tiếp bằng phép dựng hợp lệ, `construct_curved_solid` ra quả cầu,
    rồi `R = measure(radius, of=circumsphere)` — đúng lượng đo, đúng witness
    hợp đồng đòi, chủ thể đúng kiểu `curved_solid`. Cổng phủ vẫn bác, vì
    `container` của hợp đồng là `OABC` (tứ diện). Chạy lại tất định cùng
    chương trình ấy, chỉ thêm khai báo và đổi tên quả cầu thành `OABC`, thì
    tuyến chạy tới `served` và trả `R = √3`.

    Nên câu *"mô hình soạn hỏng"* là SAI ở ca ấy: chương trình đáp ứng nghĩa vụ
    về NỘI DUNG. Hai điều chặn nó — mọi vật dựng ra phải có mặt trong
    `memory_declarations`, và vật mang số đo phải trùng tên `container` của
    nghĩa vụ — **không nằm trong thẻ văn phạm lẫn skill prompt**. Một đòi hỏi
    không khai với mô hình mà vẫn bác chương trình là lỗi HỢP ĐỒNG, tức lỗi
    HỆ theo §14.

    Phân biệt được với `cylinder_2` mà không cần đoán: ở đó chủ thể phép đo là
    một `section`, kiểu `radius` KHÔNG nhận — thẻ ghi rõ
    `radius(of:tên<circle3|curved_solid>)`, nên chương trình sai thật.
    """
    from app.simulation.semantic_program.ir_static_check import _KIEU_DUNG
    from app.simulation.semantic_program.obligations import (
        accepts_container_type)

    if contract is None or spec is None:
        return []
    # Kiểu của vật theo thứ nó ĐƯỢC DỰNG, không theo thứ nó được khai: cả câu
    # hỏi ở đây là *"chương trình đã tạo ra đúng vật chưa"*.
    kieu = {d.name: d.type for d in (spec.memory_declarations or ())}
    for st in (spec.statements or ()):
        if (t := getattr(st, "target_var", None)):
            kieu[t] = _KIEU_DUNG.get(getattr(st, "kind", None), kieu.get(t))

    do_theo_witness: dict[str, tuple[str, str | None]] = {}
    for st in (spec.statements or ()):
        e = getattr(st, "expr", None)
        if getattr(e, "kind", None) == "measure":
            do_theo_witness[getattr(st, "target_var", "")] = (
                getattr(e, "quantity", ""), getattr(e, "of", None))

    ra = []
    for ob in (contract.obligations or ()):
        w = (ob.params or {}).get("witness")
        luong, chu_the = do_theo_witness.get(w, ("", None))
        if luong == ob.kind and accepts_container_type(ob.kind,
                                                       kieu.get(chu_the)):
            ra.append(f"{ob.kind}: witness '{w}' đo trên '{chu_the}'"
                      f"<{kieu.get(chu_the)}> — hụt tên container "
                      f"'{ob.container}'")
    return ra


def phan_loai(outcome: Any, *, schema_ok: bool, la_ca_am: bool = False,
              boundary_ok: bool | None = None,
              contract: Any = None, spec: Any = None,
              yeu_cau: "YeuCauNangLuc | None" = None) -> str:
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
        he = (_cong_phu_hep_hon_bo_kiem()
              or nghia_vu_du_noi_dung_hut_ten(contract, spec))
        return "SYSTEM_COVERAGE_FAILURE" if he else "MODEL_COMPOSITION_FAILURE"
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
    #
    # ⚠️ THỨ TỰ Ở ĐÂY LÀ MỘT QUYẾT ĐỊNH, không phải ngẫu nhiên.
    #
    # `grounding` đứng TRƯỚC quy tắc năng lực: một dữ kiện chưa truy được về đề
    # thì câu hỏi *"hệ có đường biểu đạt không"* còn chưa đặt ra được — chương
    # trình đang nói về một bài KHÁC. Che nó bằng `SYSTEM_EXPRESSIVENESS_GAP`
    # là xoá mất lớp lỗi R0, thứ đắt nhất trong cả taxonomy.
    # (`schema` đã chặn ở trên, cùng lý do.)
    if stage == "grounding":
        return "MODEL_GROUNDING_FAILURE"
    if stage in _GIAI_DOAN_LO_NANG_LUC:
        duong = duong_hop_le_ton_tai(yeu_cau)
        if duong == "NO":
            return "SYSTEM_EXPRESSIVENESS_GAP"
        if duong == "UNKNOWN":
            # KHÔNG có bằng chứng năng lực. Chỉ từ chối kết luận khi thất bại
            # MANG HÌNH DẠNG của một khoảng trống năng lực; ngoài hình dạng ấy
            # thì `ir_static` vẫn là lỗi soạn thảo như trước, và lịch sử không
            # bị xếp lại (đo được: 0 artifact lịch sử có `stage=ir_static`).
            if o_vo_huong_bi_rang_buoc_mo_ho(outcome, spec):
                return "ATTRIBUTION_UNRESOLVED"
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
