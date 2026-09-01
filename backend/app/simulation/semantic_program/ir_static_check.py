# -*- coding: utf-8 -*-
"""Thẩm định TĨNH chương trình hình học — TRƯỚC khi kernel chạm vào nó.

    hợp schema  ≠  thực thi được

V3 đo được đúng chỗ ấy: 4/7 lượt hỏng chết ở `execution` với
`GEOMETRY_OPERAND_TYPE` — *"điểm 'P' là NoneType, cần Vec3"*, *"tỉ lệ '2:1'
không phải phân số hợp lệ"*, *"cặp đối tượng không hợp lệ"*. Cả ba đều là lỗi
**đọc được từ chính chương trình**, không cần chạy: `P` chưa bao giờ được dựng,
`2:1` không phải phân số, đối số sai kiểu.

Chết ở runtime thì mô hình **không có cơ hội sửa**: vòng sửa của
`stage_semantic_program` kết thúc trước khi `route` gọi interpreter. Đưa các
lỗi này lên tầng thẩm định là biến một cái chết câm thành một lời từ chối có
địa chỉ — và lời từ chối ấy đi thẳng vào vòng sửa đã có.

─── BA CÂU HỎI, TẤT ĐỊNH CẢ BA ────────────────────────────────────────────

  ① ĐỊNH NGHĨA TRƯỚC KHI DÙNG — mọi tên được tham chiếu phải có giá trị tại
    thời điểm ấy. Khai trong `memory_declarations` mà không có `initial_value`
    thì tên TỒN TẠI nhưng giá trị là `None`; đó chính là `điểm 'P' là NoneType`.
  ② KIỂU TOÁN HẠNG — `midpoint` cần hai `point3`, `intersect_line_plane` cần
    một `line3` và một `plane3`. Bảng chữ ký ở `_CHU_KY`, không rải rác.
  ③ SỐ HỮU TỈ CHÍNH XÁC — `ratio` phải là thứ `Fraction` đọc được. `2:1` là
    cách viết tỉ lệ của SGK, không phải cú pháp phân số, và **không được tự ý
    diễn giải lại**: `2:1` có thể là `2/1` mà cũng có thể là `2/3` của đoạn,
    tuỳ quy ước. Đoán một trong hai là dựng sai hình mà vẫn xanh.

─── VÌ SAO FAIL-OPEN Ở NHÁNH LỒNG ────────────────────────────────────────

Trong `if`/`while`/`for`, một câu lệnh có thể không chạy. Đòi thứ tự chặt bên
trong nhánh sẽ từ chối oan các chương trình đúng, nên ở đó chỉ hỏi câu ① dạng
YẾU: tên phải được định nghĩa **ở đâu đó** trong chương trình. Câu hỏi *"lượt
chạy này có đi qua không"* thuộc C₁b, và tách hai câu hỏi là có chủ đích.

─── GIỚI HẠN CÒN LẠI, KHAI THẲNG ────────────────────────────────────────

Hệ quả trực tiếp của fail-open ấy: một điểm **chỉ được dựng trong một nhánh
không chạy** rồi dùng ở ngoài vẫn qua được tầng này, và kernel sẽ nhận `None`.

    ⇒ "None không bao giờ tới kernel" là một tuyên bố SAI. Đúng là:
      *ba họ lỗi đã QUAN SÁT ĐƯỢC ở V3 không còn tới kernel nữa.*

Kernel vẫn fail-closed ở đó (`GEOMETRY_UNDECLARED`/`GEOMETRY_OPERAND_TYPE`),
nên kết cục vẫn AN TOÀN — chỉ là bị bắt muộn một tầng, và mô hình không có cơ
hội sửa. Đóng nốt lỗ này đòi phân tích luồng theo nhánh (mỗi đường đi một bảng
ký hiệu); chưa làm vì chương trình hình học gần như không dùng rẽ nhánh, và
`test_GIOI_HAN_nhanh_khong_chay_van_lot` khoá cho lời khai này không tự mục đi.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Any

from pydantic import BaseModel, Field

from .measure_contract import BANG_PHEP_DO as _BANG_PHEP_DO

#: Mã lỗi TĨNH. Không thêm vào `ErrorCode` — enum ấy là bề mặt mọi tầng phía
#: sau đọc, và ở đây đi đúng đường mà `grounding` đã đi: giữ mã ngoài, đẩy chi
#: tiết vào `details`. Bốn mã tách rời vì chúng đòi bốn phép sửa khác nhau.
ERR_CHUA_DINH_NGHIA = "IR_UNDEFINED_OBJECT"
ERR_DUNG_TRUOC_KHI_DUNG = "IR_USE_BEFORE_CONSTRUCTION"
ERR_SAI_KIEU = "IR_OPERAND_TYPE"
ERR_KHONG_HUU_TI = "IR_NOT_EXACT_RATIONAL"
#: Ràng buộc LẦN ĐẦU một vật hình học bên trong một nhánh có thể không chạy.
#:
#: Tách khỏi `ERR_DUNG_TRUOC_KHI_DUNG`: kia nói *"dùng trước khi dựng"*, mã này
#: nói *"dựng ở một chỗ có thể không tới"*. Hai lời chẩn đoán khác nhau, và gộp
#: chúng thì lời sửa gửi cho mô hình chỉ đúng một nửa.
ERR_RANG_BUOC_TRONG_NHANH = "CONDITIONAL_UNINITIALIZED_TARGET"
#: Toán hạng hình học trỏ một tên mà kiểu TĨNH không suy ra được — nó được ràng
#: buộc bằng `assign … = arith/literal/…`. Không nâng được (§3 đòi kiểu duy
#: nhất, §6 cấm tự đăng ký giá trị thô), nên phải từ chối TRƯỚC runtime.
ERR_RANG_BUOC_MO_HO = "AMBIGUOUS_FIRST_BINDING"

#: Kiểu chuẩn của một vật hình học. `scalar` là kết quả của `measure` — không
#: phải đối tượng, và không bao giờ được đem làm điểm/đường/mặt.
DIEM, DUONG, MAT, DA_GIAC, KHOI, THIET_DIEN = (
    "point3", "line3", "plane3", "polygon3", "solid", "section")
#: Vectơ CÓ HƯỚNG. Ở runtime nó cùng lớp `Vec3` với điểm, nên khác biệt giữa
#: "điểm" và "vectơ" chỉ tồn tại ở tầng KHAI — và đó là lý do `angle_cos` phải
#: được canh ở đây chứ không ở kernel.
VECTO = "vector3"
SO_DO = "scalar"

#: Kiểu mà mỗi câu lệnh dựng SINH RA.
_KIEU_DUNG = {
    "construct_point": DIEM, "construct_line": DUONG, "construct_plane": MAT,
    "construct_polygon": DA_GIAC, "construct_solid": KHOI,
    "construct_section": THIET_DIEN,
}

#: `(kind biểu thức) → (danh sách (tên trường, kiểu chấp nhận), kiểu trả về)`.
#:
#: Một trường có thể nhận NHIỀU kiểu (`project_onto.target`), nên vế phải là
#: tuple. Bảng này là bản sao ngữ nghĩa của `eval_geometry_expr` — và đó là rủi
#: ro thật: hai bên trôi khỏi nhau thì thẩm định tĩnh nói OK còn kernel ném.
#:
#: Khoá bởi `tests/semantic_program/test_type_authority.py` — nó ĐỌC AST của
#: `eval_geometry_expr` rồi so hai tập. Chú thích cũ ở đây khai một guard tên
#: `test_chu_ky_phu_het_bieu_thuc_hinh_hoc` **chưa bao giờ tồn tại**; một lời
#: hứa trong chú thích không chặn được gì, và bảng đã trôi thật hai lần.
#:
#: `validator._BIEU_THUC_HINH_HOC` nay DẪN XUẤT từ bảng này, nên thêm một biểu
#: thức chỉ phải sửa MỘT chỗ.
_CHU_KY: dict[str, tuple[tuple[tuple[str, tuple[str, ...]], ...], str]] = {
    "intersect_line_plane": ((("line", (DUONG,)), ("plane", (MAT,))), DIEM),
    "intersect_plane_plane": ((("plane_a", (MAT,)), ("plane_b", (MAT,))), DUONG),
    "intersect_line_line": ((("line_a", (DUONG,)), ("line_b", (DUONG,))), DIEM),
    "midpoint": ((("a", (DIEM,)), ("b", (DIEM,))), DIEM),
    "divide_segment": ((("a", (DIEM,)), ("b", (DIEM,))), DIEM),
    "project_onto": ((("point", (DIEM,)), ("target", (MAT, DUONG))), DIEM),
    "vector_from_points": (
        (("from_point", (DIEM,)), ("to_point", (DIEM,))), VECTO),
    # ĐIỂM + VECTƠ → ĐIỂM. Phép affine cơ bản, thêm 2026-09-01 sau khi
    # `audit_translation_gap.py` chứng minh từ văn phạm rằng KHÔNG phép sinh
    # điểm nào nhận vectơ — `vector3` trước đó là kiểu CHỈ-GHI: dựng được
    # nhưng không phép dựng nào tiêu thụ, chỉ `angle_cos` đo nó.
    "translate": ((("point", (DIEM,)), ("vector", (VECTO,))), DIEM),
}

#: Toán hạng TÊN của các câu lệnh dựng. `construct_point` không có ở đây: toán
#: hạng của nó nằm trong `expr`, và `_CHU_KY` lo.
_TOAN_HANG_LENH: dict[str, tuple[tuple[str, tuple[str, ...], bool], ...]] = {
    # (tên trường, kiểu chấp nhận, trường là DANH SÁCH tên?)
    "construct_line": (("through_a", (DIEM,), False), ("through_b", (DIEM,), False)),
    "construct_plane": (("through", (DIEM,), True),),
    "construct_polygon": (("vertices", (DIEM,), True),),
    "construct_solid": (("vertices", (DIEM,), True),),
    "construct_section": (("solid", (KHOI,), False), ("plane", (MAT,), False)),
}

#: `measure` theo `quantity` — DẪN XUẤT từ `measure_contract.BANG_PHEP_DO`.
#:
#: ─── VÌ SAO KHÔNG CÒN VIẾT TAY Ở ĐÂY (2026-08-31) ─────────────────────────
#:
#: Bảng này từng là bản viết tay THỨ BA của cùng một luật: validator có bản
#: của nó, kernel có bản của nó, đây là bản thứ ba — và không bản nào được
#: gửi cho mô hình. Chú thích cũ ngay tại dòng `angle_cos` kể đúng cái giá:
#: `vector3` được thêm vào `_CHU_KY` mà quên bảng này, nên một chương trình
#: dựng vectơ hoàn toàn đúng bị từ chối bằng *"cần point3 hoặc line3 … có
#: vector3"* — mô hình làm đúng, hệ nói sai, và bốn lượt live chết vì thế.
#:
#: Nay một thẩm quyền, ba người đọc (validator · tầng này · thẻ văn phạm).
#: Thêm một lượng đo mà quên dòng ⇒ `test_measure_contract.py` ĐỎ.
#:
#: ─── MỘT CHỖ HẸP LẠI, CÓ CHỦ ĐÍCH ────────────────────────────────────────
#:
#: `angle_cos_sq` trước nhận cả `polygon3`/`solid`/`section`, với lý do *"cặp
#: hợp lệ do kernel quyết"*. Nhưng kernel chỉ có nhánh cho đường và mặt, nên
#: cái "để kernel quyết" ấy chỉ đổi chỗ báo lỗi từ TRƯỚC khi chạy sang GIỮA
#: lúc chạy — và lỗi runtime KHÔNG được gửi ngược để sửa. Đó đúng là lập luận
#: mà chú thích của `_DO_KHOANG_CACH` ngay dưới đã dùng cho `distance`; nay áp
#: nốt cho góc.
_DOI_TUONG = (DIEM, DUONG, MAT, DA_GIAC, KHOI, THIET_DIEN)
_KIEU_DO = {
    q: (p.kieu_of, p.kieu_wrt if p.hai_toan_hang else None)
    for q, p in _BANG_PHEP_DO.items()
}


class StaticIssue(BaseModel):
    """Một lời từ chối, đủ để MÁY hành động: mã · vị trí · vật · mong đợi."""

    error_code: str
    instruction: int
    object_id: str
    expected: str
    actual: str

    def dong(self) -> str:
        return (f"#{self.instruction} {self.error_code}: '{self.object_id}' — "
                f"cần {self.expected}, có {self.actual}")


class StaticCheckResult(BaseModel):
    ok: bool
    issues: list[StaticIssue] = Field(default_factory=list)

    def phan_hoi(self, toi_da: int = 4) -> str:
        """Lời nhắn gửi ngược cho mô hình. NGẮN — prompt chính không đổi."""
        return "; ".join(i.dong() for i in self.issues[:toi_da])


def _la_huu_ti(raw: Any) -> bool:
    if isinstance(raw, bool):
        return False
    if isinstance(raw, int):
        return True
    if isinstance(raw, float):
        return False          # hợp đồng đòi CHÍNH XÁC; float là chỗ mất nó
    try:
        Fraction(str(raw).strip())
    except (ValueError, ZeroDivisionError, TypeError):
        return False
    return True


def _kieu_khai(spec) -> dict[str, str]:
    """Tên → kiểu, cho MỌI khai báo. Có kiểu ≠ có giá trị."""
    return {d.name: d.type for d in (spec.memory_declarations or ())}


def _co_gia_tri_ban_dau(d) -> bool:
    """Khai báo này có mang giá trị ngay từ đầu không?

    `initial_value=None` nghĩa là ô trống — biến tồn tại, giá trị `None`, và
    kernel sẽ ném `NoneType` khi ai đó dùng nó. Đó đúng là lỗi cần bắt ở đây.
    """
    return getattr(d, "initial_value", None) is not None


#: Kiểu mà `initial_value` PHẢI là ba toạ độ hữu tỉ. Hẹp có chủ đích: chỉ hai
#: kiểu này có hợp đồng *"đúng ba số"*. `polygon3`/`solid` khai bằng TÊN ĐỈNH,
#: và đòi chúng hữu tỉ sẽ từ chối oan.
_KIEU_TOA_DO = (DIEM, VECTO)


def _kiem_toa_do(spec, issues: list) -> None:
    """Câu ③ áp cho TOẠ ĐỘ, không chỉ cho `ratio`.

    ─── LỖ NÀY LỘ RA KHI CHẠY LẠI LỊCH SỬ (2026-09-01) ────────────────────

    `at: list[Any]` và `initial_value: Any` nhận mọi thứ, nên một toạ độ KÝ
    HIỆU đi thẳng tới kernel:

        {"name": "A", "type": "point3", "at": [{"kind":"var","name":"a"}, 0, 0]}

    Mô hình đang nói *"cạnh đáy là a"* — đúng thói quen SGK, và sai với một hệ
    tính bằng số hữu tỉ chính xác. Kernel ném `ZERO_VECTOR: toạ độ không hợp
    lệ`, tức một tiền điều kiện TĨNH bị canh ở tầng RUNTIME, nơi vòng sửa
    không với tới — đúng lớp lỗi mà docstring của module này tồn tại để diệt.

    Nó vốn đã lọt từ trước; ở artifact `dihedral-probe-ergonomics` nó bị một
    lỗi schema khác che mất. Bịt phép nâng toán hạng làm nó lộ ra, nên bịt nốt
    ở đây — nếu không thì phép nâng đổi một ca chết-có-lời-sửa thành một ca
    chết câm.
    """
    for d in (spec.memory_declarations or ()):
        if getattr(d, "type", None) not in _KIEU_TOA_DO:
            continue
        gt = getattr(d, "initial_value", None)
        if not isinstance(gt, (list, tuple)):
            continue
        for j, x in enumerate(gt):
            if _la_huu_ti(x):
                continue
            issues.append(StaticIssue(
                error_code=ERR_KHONG_HUU_TI, instruction=0,
                object_id=f"{d.name}[{j}]",
                expected="số hữu tỉ chính xác, vd 3 hoặc -1/2 hoặc \"4/3\"",
                actual=repr(x)[:60] + " — toạ độ phải là SỐ; một cạnh ký hiệu "
                       "(a, x…) thì hãy chọn một giá trị số cụ thể"))


def kiem_tinh(spec) -> StaticCheckResult:
    """Duyệt chương trình MỘT LƯỢT theo thứ tự, dựng bảng ký hiệu, thẩm định."""
    kieu = _kieu_khai(spec)
    #: Tên ĐÃ CÓ GIÁ TRỊ tại điểm đang duyệt.
    co: dict[str, str] = {
        d.name: d.type for d in (spec.memory_declarations or ())
        if _co_gia_tri_ban_dau(d)
    }
    #: Tên được định nghĩa ở ĐÂU ĐÓ trong chương trình — dùng cho nhánh lồng.
    moi_noi = set(co) | _moi_dinh_nghia(spec.statements)
    issues: list[StaticIssue] = []
    _kiem_toa_do(spec, issues)
    _duyet(spec.statements, co, moi_noi, kieu, issues, [0], long=False)
    return StaticCheckResult(ok=not issues, issues=issues)


def _moi_dinh_nghia(stmts) -> set[str]:
    ra: set[str] = set()
    for st in stmts or ():
        k = getattr(st, "kind", None)
        if k in _KIEU_DUNG or k == "assign":
            ra.add(st.target_var)
        for attr in ("body", "then_body", "else_body"):
            if (sub := getattr(st, attr, None)):
                ra |= _moi_dinh_nghia(sub)
    return ra


def _duyet(stmts, co, moi_noi, kieu, issues, dem, *, long: bool) -> None:
    for st in stmts or ():
        dem[0] += 1
        i = dem[0]
        k = getattr(st, "kind", None)

        if k == "construct_point":
            _kiem_bieu_thuc(st.expr, co, moi_noi, kieu, issues, i, long=long)
        elif k in _TOAN_HANG_LENH:
            for truong, nhan, la_ds in _TOAN_HANG_LENH[k]:
                gt = getattr(st, truong, None)
                for ten in (gt or ()) if la_ds else ([gt] if gt else ()):
                    _kiem_ten(ten, nhan, co, moi_noi, kieu, issues, i, long=long)
        elif k == "assign":
            _kiem_bieu_thuc(getattr(st, "expr", None), co, moi_noi, kieu,
                            issues, i, long=long)
            # ─── RÀNG BUỘC LẦN ĐẦU TRONG NHÁNH — TỪ CHỐI Ở ĐÂY ───────────
            #
            # `contract._rang_buoc_lan_dau` chỉ nâng `assign` hình học ở TẦNG
            # NGOÀI CÙNG. Trong `if`/`while` thì không: nâng nó là khai một
            # tên ở scope ngoài rồi để nó mang `None` khi nhánh không chạy —
            # đúng món nợ `RUNTIME_NONE_OPERAND_REACHABLE` mà docstring module
            # này đã khai, và §4 cấm nới.
            #
            # Nên ca ấy phải chết Ở ĐÂY, nơi vòng sửa với tới được, thay vì ở
            # kernel với `GEOMETRY_UNDECLARED` — một tiền điều kiện TĨNH bị
            # canh ở tầng runtime là đổi một lượt sửa rẻ thành một ca mất
            # trắng. Đó chính là thứ đã giết 4/6 ca của CLEAN_BASELINE_V1.
            if long and getattr(getattr(st, "expr", None), "kind", None) in _CHU_KY:
                ten = getattr(st, "target_var", None)
                if ten and ten not in kieu:
                    issues.append(StaticIssue(
                        error_code=ERR_RANG_BUOC_TRONG_NHANH, instruction=i,
                        object_id=str(ten),
                        expected="khai trong memory_declarations, hoặc dựng "
                                 "ngoài nhánh",
                        actual="ràng buộc lần đầu bên trong một nhánh có thể "
                               "không chạy",
                    ))

        if k in _KIEU_DUNG:
            co[st.target_var] = _KIEU_DUNG[k]
        elif k == "assign":
            co[st.target_var] = _kieu_ket_qua(getattr(st, "expr", None), kieu)

        for attr in ("body", "then_body", "else_body"):
            if (sub := getattr(st, attr, None)):
                # Nhánh lồng: chỉ hỏi câu ① dạng YẾU. Xem docstring module.
                _duyet(sub, co, moi_noi, kieu, issues, dem, long=True)


def _kieu_ket_qua(node, kieu) -> str:
    k = getattr(node, "kind", None)
    if k in _CHU_KY:
        return _CHU_KY[k][1]
    if k == "measure":
        return SO_DO
    if k == "var":
        return kieu.get(getattr(node, "name", ""), "unknown")
    return "unknown"


def _kiem_bieu_thuc(node, co, moi_noi, kieu, issues, i, *, long: bool) -> None:
    k = getattr(node, "kind", None)
    if k in _CHU_KY:
        for truong, nhan in _CHU_KY[k][0]:
            _kiem_ten(getattr(node, truong, None), nhan, co, moi_noi, kieu,
                      issues, i, long=long)
        if k == "divide_segment":
            r = getattr(node, "ratio", None)
            if not _la_huu_ti(r):
                issues.append(StaticIssue(
                    error_code=ERR_KHONG_HUU_TI, instruction=i,
                    object_id="ratio",
                    expected="phân số chính xác, vd 2/3 hoặc 2 hoặc -3",
                    actual=repr(r)))
    elif k == "measure":
        nhan_of, nhan_wrt = _KIEU_DO.get(getattr(node, "quantity", ""),
                                         (_DOI_TUONG, _DOI_TUONG))
        _kiem_ten(getattr(node, "of", None), nhan_of, co, moi_noi, kieu,
                  issues, i, long=long)
        if (w := getattr(node, "wrt", None)) and nhan_wrt:
            _kiem_ten(w, nhan_wrt, co, moi_noi, kieu, issues, i, long=long)


def _kiem_ten(ten, nhan, co, moi_noi, kieu, issues, i, *, long: bool) -> None:
    if not isinstance(ten, str) or not ten:
        return
    mong = " hoặc ".join(nhan)
    if ten not in moi_noi and ten not in kieu:
        issues.append(StaticIssue(
            error_code=ERR_CHUA_DINH_NGHIA, instruction=i, object_id=ten,
            expected=mong, actual="không có trong chương trình"))
        return
    if ten not in co:
        if long:
            return          # nhánh lồng: chỉ đòi tồn tại, xem docstring module
        issues.append(StaticIssue(
            error_code=ERR_DUNG_TRUOC_KHI_DUNG, instruction=i, object_id=ten,
            expected=mong,
            actual=("khai báo nhưng chưa có giá trị" if ten in kieu
                    else "được dựng ở câu lệnh SAU")))
        return
    that = co[ten]
    if that == "unknown":
        # ─── KIỂU KHÔNG SUY ĐƯỢC Ở CHỖ ĐÒI KIỂU HÌNH HỌC ────────────────
        #
        # `_kiem_ten` chỉ được gọi ở đường HÌNH HỌC (toán hạng của `construct_*`
        # và của `_CHU_KY`), nên `nhan` luôn là kiểu hình học. Một tên mang
        # kiểu tĩnh `unknown` ở đây là một tên được ràng buộc bằng
        # `assign … = arith/literal/index/…` — không phép dựng nào, không kiểu
        # nào suy ra được.
        #
        # Bản trước có `and that != "unknown"`, tức CHO QUA. Hệ quả đo được ở
        # `CLEAN_BASELINE_V1 cb_04`: mô hình viết `assign C = arith(...)` để
        # tính một ĐIỂM, thẩm định tĩnh im lặng, rồi `construct_solid` ném
        # `GEOMETRY_UNDECLARED` ở kernel — nơi vòng sửa không với tới.
        #
        # `unknown` KHÔNG được nâng thành điểm (§3 đòi kiểu suy được duy nhất;
        # §6 cấm tự đăng ký giá trị thô). Nên nó phải bị TỪ CHỐI, và từ chối ở
        # đây thì mô hình còn một lượt để dựng lại bằng `midpoint`/`divide_
        # segment` — thứ nó vốn định nói.
        issues.append(StaticIssue(
            error_code=ERR_RANG_BUOC_MO_HO, instruction=i, object_id=ten,
            expected=mong,
            actual="ràng buộc bằng một biểu thức không suy ra kiểu hình học "
                   "(arith/literal/…) — hãy dùng một phép DỰNG"))
        return
    if that not in nhan:
        issues.append(StaticIssue(
            error_code=ERR_SAI_KIEU, instruction=i, object_id=ten,
            expected=mong, actual=that))
