# -*- coding: utf-8 -*-
"""HỢP ĐỒNG PHÉP ĐO — một bảng, ba người đọc. Thẩm quyền kiểu của `measure`.

─── VÌ SAO TỒN TẠI: THẨM QUYỀN ĐANG RẢI BA CHỖ ────────────────────────────

    validator.py      `angle_cos` phải là `vector3`  ← viết cứng
    validator.py      chỉ `volume` đo một toán hạng  ← viết cứng
    geometry_exec.py  cặp kiểu nào kernel tính được  ← viết cứng, lần thứ hai
    grammar_card      … KHÔNG NÓI GÌ CẢ

Chỗ thứ tư là chỗ đau: thẻ gửi cho mô hình liệt kê `quantity(distance|
angle_cos_sq|angle_cos|volume)` mà không nói **lượng đo nào nhận kiểu nào**.
Mô hình chọn đúng chỗ điền, sai thứ điền vào — rồi ta đọc lỗi ấy như "mô hình
kém". AUDIT 2026-08-31 đếm được: `angle_cos` trên `line3` **14 lượt / 220.898
token**, bệnh tốn kém nhất trong cả ba tuyến đo.

─── HAI THỨ BẢNG NÀY CỐ Ý LÀM ─────────────────────────────────────────────

**① MODEL-FACING HẸP HƠN RUNTIME-ACCEPTED.** `_CHU_KY` cho `distance` nhận cả
`polygon3`, `solid`, `section`; kernel thì chỉ có nhánh cho điểm · đường · mặt.
Bảng này khai phần **chạy được**, không khai phần *lọt qua thẩm định tĩnh*.
Dạy mô hình một cửa rộng hơn cửa thật là đẩy nó vào lỗi runtime — mà lỗi runtime
KHÔNG được gửi ngược để sửa, nên nó giết cả ca.

**② NGỮ NGHĨA, KHÔNG TỪ KHOÁ.** `nghia` mô tả *phép đo làm gì*, tuyệt đối không
nhắc "nhị diện" hay dạng bài. Prompt cũ viết *"góc CÓ CHIỀU (nhị diện nhọn/tù)"*
cạnh `angle_cos`; cộng thêm việc tên phép đo chứa sẵn chữ "cos", đề nào hỏi
"côsin" là mô hình chọn nó — kể cả `gm_07`, đề KHÔNG có chữ "nhị diện" nào.
Mô hình phải chọn theo *"tôi có cần DẤU không"*, không theo chữ trong đề.

─── CHỐNG TRÔI ────────────────────────────────────────────────────────────

Không dẫn xuất được 100%: cặp kiểu mà kernel tính được nằm trong luồng điều
khiển của `_do()`, không trong một cấu trúc dữ liệu. Nên bảng này viết tay, và
đổi lại phải có `test_measure_contract.py` khoá ba điều: mọi `quantity` trong
`Literal` đều có dòng · validator xử đúng như bảng nói · thẻ văn phạm in ra
đúng bảng. Thêm một lượng đo mà quên dòng ⇒ ĐỎ.
"""
from __future__ import annotations

import typing
from dataclasses import dataclass

__all__ = ["PhepDo", "BANG_PHEP_DO", "phep_do", "mo_ta_phep_do"]


@dataclass(frozen=True)
class PhepDo:
    """Một lượng đo: nhận gì, mấy toán hạng, để làm gì."""

    quantity: str
    #: Kiểu khai hợp lệ cho `of`. Rỗng = không ràng buộc tĩnh.
    kieu_of: tuple[str, ...]
    #: Kiểu khai hợp lệ cho `wrt`; `()` khi phép đo chỉ có một toán hạng.
    kieu_wrt: tuple[str, ...]
    #: MỘT dòng ngữ nghĩa. Không nêu dạng bài, không nêu từ khoá đề.
    nghia: str
    #: Câu CHỈ ĐƯỜNG khi toán hạng sai kiểu. Ở trong bảng chứ không ở nhánh
    #: `if` của validator: chọn thông điệp theo tên phép đo viết cứng là cách
    #: một luật thứ tư ra đời, và `test_measure_contract` chặn đúng chỗ đó.
    goi_y: str = ""

    @property
    def hai_toan_hang(self) -> bool:
        return bool(self.kieu_wrt)

    def kieu_sai(self, truong: str, kieu_khai: str) -> bool:
        """Kiểu khai này có vi phạm hợp đồng ở trường ấy không?"""
        cho = self.kieu_of if truong == "of" else self.kieu_wrt
        return bool(cho) and kieu_khai not in cho


#: Ba kiểu hình học KHÔNG CÓ CHIỀU. Góc giữa chúng chỉ có độ lớn.
_VO_HUONG = ("point3", "line3", "plane3")

BANG_PHEP_DO: dict[str, PhepDo] = {
    p.quantity: p for p in (
        PhepDo(
            "distance", _VO_HUONG, _VO_HUONG,
            "khoảng cách giữa hai đối tượng (điểm · đường · mặt)",
        ),
        PhepDo(
            # Đại lượng là cos²θ ở CẢ BỐN cặp — đường×đường, mặt×mặt,
            # đường×mặt và cặp đảo. Trước 2026-08-31 cặp (đường, mặt) trả
            # sin², tức cùng một opcode mang hai nghĩa; xem
            # `measure.cos_sq_giua`.
            "angle_cos_sq", ("line3", "plane3"), ("line3", "plane3"),
            "cos² của góc giữa hai đối tượng KHÔNG có chiều — đường, mặt, "
            "hoặc đường với mặt. Góc luôn trong [0°, 90°]. Mặc định cho mọi "
            "câu hỏi về góc",
        ),
        PhepDo(
            # Vì sao KHÔNG nhận `point3` dù runtime thấy cả hai là `Vec3`: dấu
            # là một mệnh đề toán học, nên nó chỉ được đến từ một toán hạng
            # KHAI là có hướng. Chỉ tầng đọc được `memory_declarations` phân
            # biệt nổi — kernel thì không.
            "angle_cos", ("vector3",), ("vector3",),
            "góc giữa hai vectơ CÓ HƯỚNG — trả cos CÓ DẤU. Chỉ dùng khi kết "
            "luận phụ thuộc chiều; dựng vectơ bằng `vector_from_points`",
            "Đường thẳng không có chiều nên không cho được dấu — dựng vectơ "
            "bằng `vector_from_points`, hoặc dùng `angle_cos_sq` nếu chỉ cần "
            "độ lớn của góc.",
        ),
        PhepDo(
            # MỘT tên cho MỘT khái niệm: `curved_solid` vào đây chứ không đẻ
            # `curved_volume`. Thể tích khối cầu và thể tích khối chóp là cùng
            # một đại lượng; tách tên là dạy mô hình rằng chúng khác nhau.
            "volume", ("solid", "curved_solid"), (),
            "thể tích một khối — đa diện hoặc khối cong",
        ),
        PhepDo(
            # Nhận CẢ HAI kiểu phẳng mà runtime dựng được, và đúng hai kiểu ấy.
            # `polygon3` sống dưới dạng tuple đỉnh, `section` là `Section` có
            # `.polygon` — cùng một bài toán, một thẩm quyền (`area_polygon`).
            #
            # KHÔNG nhận `solid`: "diện tích một khối" là diện tích TOÀN PHẦN,
            # một đại lượng khác, và cộng diện tích các mặt lại thì rơi đúng
            # vào tổng nhiều căn thức mà miền số từ chối. Hứa nó ở đây là dạy
            # mô hình một cửa dẫn tới lỗi runtime — mà lỗi runtime không được
            # gửi ngược để sửa (§① của bảng này).
            # `circle3` vào cùng lượng đo `area` (2026-09-03) chứ không đẻ
            # `circle_area`: diện tích hình tròn và diện tích đa giác là cùng
            # một đại lượng, chỉ khác công thức — và công thức là việc của
            # kernel, không phải của từ vựng gửi cho mô hình.
            "area", ("polygon3", "section", "circle3"), (),
            "diện tích một hình PHẲNG — đa giác, thiết diện, hoặc hình tròn",
            "Diện tích chỉ đo được trên hình phẳng đã dựng: dựng đa giác bằng "
            "`construct_polygon`, thiết diện bằng `construct_section`, hoặc "
            "đường tròn bằng `intersect_plane_curved`.",
        ),
        PhepDo(
            # ─── VÌ SAO CÓ `radius` MÀ KHÔNG CÓ `height`/`slant` ────────────
            #
            # Chiều cao trụ = `distance(anchor, apex_or_top)`; đường sinh nón =
            # `distance(apex_or_top, rim_point)`. Cả hai toán hạng đều là ĐIỂM
            # CÓ TÊN ngay trong chương trình đã dựng khối, nên `distance` diễn
            # đạt được — thêm lượng đo riêng là lặp lỗi mà cổng hợp thành G4 đã
            # chặn.
            #
            # `radius` thì KHÔNG: một `circle3` sinh từ `intersect_plane_curved`
            # có tâm và vành mà chương trình **không có tên nào trỏ tới**. Đây
            # là khoảng trống thật, và là lượng đo cong duy nhất thuộc loại ấy.
            "radius", ("circle3", "curved_solid"), (),
            "bán kính một đường tròn hoặc một khối cong",
            "Bán kính đo trên đường tròn hoặc khối cong đã dựng. Khoảng cách "
            "giữa hai điểm có tên thì dùng `distance`.",
        ),
        PhepDo(
            # ─── VÌ SAO `lateral_area` MÀ KHÔNG PHẢI `surface_area` ─────────
            #
            # Diện tích TOÀN PHẦN của nón `= πrl + πr²` có hai căn thức khác
            # nhau, và miền số cố ý từ chối tổng ấy. Một lượng đo mà những ca
            # hợp lệ thường gặp đều ném là dạy mô hình một cửa dẫn thẳng vào
            # lỗi runtime — thứ KHÔNG được gửi ngược để sửa, nên nó giết cả ca.
            #
            # Ba công thức mặt cong (`4πR²`, `2πrh`, `πrl`) thì LUÔN biểu diễn
            # được: mỗi cái là một hữu tỉ nhân π nhân đúng MỘT căn.
            "lateral_area", ("curved_solid",), (),
            "diện tích MẶT CONG: mặt cầu, hoặc mặt xung quanh trụ và nón — "
            "KHÔNG phải diện tích toàn phần",
            "Diện tích mặt cong chỉ đo trên khối cong. Hình phẳng thì dùng "
            "`area`.",
        ),
    )
}


def phep_do(quantity: str) -> PhepDo | None:
    return BANG_PHEP_DO.get(quantity)


def mo_ta_phep_do() -> str:
    """Bảng phép đo ở dạng gửi cho mô hình — kiểu ĐI KÈM từng lượng đo.

    Đặt cạnh `quantity` trong thẻ văn phạm chứ không thành một mục riêng ở đầu
    prompt: bắt mô hình nhớ một bảng kiểu đặt xa chỗ dùng là bắt nó làm việc mà
    ta làm hộ được (§3 — kỳ vọng kiểu phải CỤC BỘ).
    """
    # `tên<…>` chứ không phải `…` trần: hai toán hạng này là ô TÊN, và bảng
    # kiểu trần nói được *kiểu gì* mà không nói được *điền TÊN hay điền vật*.
    # Đo được ở artifact live: 2 lần mô hình lồng thẳng `vector_from_points`
    # vào `of`/`wrt`. Ký hiệu này là cùng một ký hiệu thẻ văn phạm dùng cho mọi
    # ô TÊN khác — một quy ước, không phải hai.
    dong = []
    for p in BANG_PHEP_DO.values():
        chu_ky = (f"{p.quantity}(of:tên<{'|'.join(p.kieu_of)}>, "
                  f"wrt:tên<{'|'.join(p.kieu_wrt)}>)" if p.hai_toan_hang
                  else f"{p.quantity}(of:tên<{'|'.join(p.kieu_of)}>) "
                       "— không có wrt")
        dong.append(f"    {chu_ky}\n      {p.nghia}")
    return "\n".join(dong)


def quantity_trong_contract() -> tuple[str, ...]:
    """Enum `quantity` đọc từ chính `contract.py` — dùng cho guard chống trôi."""
    from .contract import MeasureExpr

    return tuple(
        typing.get_args(MeasureExpr.model_fields["quantity"].annotation))
