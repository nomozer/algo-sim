# -*- coding: utf-8 -*-
"""KHỐI CONG CÓ BIÊN — cầu · trụ · nón trên MỘT nền chung, chính xác tuyệt đối.

Phase 2 của `docs/CURVED_GEOMETRY_FOUNDATION_DESIGN.md`.

─── VÌ SAO KHÔNG PHẢI QUADRIC ─────────────────────────────────────────────

Một mặt bậc hai tổng quát `xᵀAx + bᵀx + c = 0` biểu diễn được cả ba hình, và
vẫn là lựa chọn **sai** ở đây, vì hai lý do đo được:

**① Quadric mất BIÊN.** Hình trụ hữu hạn *không phải* một quadric — quadric cho
một ống vô hạn. Muốn có KHỐI thì vẫn phải kèm mô tả biên, tức đã là biểu diễn
này rồi, chỉ khoác một cái áo phức tạp hơn.

**② Quadric mất DANH TÍNH THAM SỐ.** Từ `A, b, c` muốn biết *"đây là trụ, bán
kính r, chiều cao h"* phải chéo hoá, mà trị riêng của ma trận hữu tỉ **không
hữu tỉ**. Tầng đo sẽ phải suy lại thứ constructor vốn đã biết — đúng lối kho
này đã gỡ hai lần (`producer`-sniffing ở frontend, bảng `TU_PHEP_DUNG`).

`V = πr²h` cần `r` và `h` **được gọi tên**, không cần một phương trình.

─── PHÁT HIỆN TRUNG TÂM: KHAI BẰNG BA ĐIỂM, KHÔNG BẰNG (TRỤC, BÁN KÍNH) ────

Khai `(trục d, bán kính r)` thì để dựng bất cứ thứ gì trên vành phải tìm
`v ⊥ d` với `|v| = r`. Với `d = (1,1,1)` vectơ vuông góc hữu tỉ gần nhất có
`|v| = √2` — **vô tỉ**. Thiết diện qua trục lập tức rời ℚ³.

Khai bằng **ba điểm hữu tỉ** — đúng thành ngữ mà IR đã dùng cho đa diện — thì
mọi thứ ở lại ℚ³, **kể cả khi bán kính vô tỉ và trục xiên**:

    trụ (O,O′,A) = ((0,0,0), (0,0,2), (1,0,0))
      chữ nhật qua trục:  (1,0,0) (−1,0,0) (−1,0,2) (1,0,2)   ← toàn hữu tỉ
    trục XIÊN (1,2,2), A = (2,−1,0):  r = √5 VÔ TỈ mà mọi ĐỈNH vẫn hữu tỉ

Bán kính được phép vô tỉ vì nó là **đại lượng ĐO**, đi qua `sqrt_rational` ở
đúng biên đo — y hệt `distance_sq`. Toạ độ thì không bao giờ.

Hệ quả: **thiết diện qua trục KHÔNG cần phép dựng mới.** Điểm xuyên tâm đối
`B = 2O − A` là `divide_segment(A, O, ratio="2")`; nối `S, A, B` là
`construct_polygon`; đo là `measure area` của Phase 1. Ba phép đã có.

─── ĐIỀU MODULE NÀY CỐ Ý KHÔNG LÀM ────────────────────────────────────────

**Không sinh ĐIỂM trên mặt cong.** Giao một *đường thẳng* với mặt cong cho
`t = (−B ± √Δ)/2A`, và toạ độ giao điểm rơi vào `ℚ(√Δ)³` mà `Vec3` không chở
nổi. Đó là ràng buộc cứng hơn "chưa có mặt", và nó quyết định toàn bộ hình
dáng của v1. Yêu cầu phép ấy ⇒ **từ chối có mã**, không bao giờ xấp xỉ nghiệm.

**Không có kiểu conic.** Mặt phẳng xiên cắt trụ/nón cho elip; nó nằm ngoài bao
đóng v1 và bị từ chối bằng một mã nói đúng *"ngoài bao đóng"*, không phải một
mã nói *"khối hỏng"*.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Callable, Optional

from .exact import GeometryError, Line3, Plane3, Point3, Vec3
from .kernel import intersect_line_plane, project_point_onto_plane
from .radical import (
    ExactNumber,
    Radical,
    display,
    multiply,
    radical,
    sqrt_rational,
    times_rational,
)

__all__ = [
    "Circle3",
    "CurvedSolid",
    "GOC_CANONICAL",
    "HUONG_TRUC_CANONICAL",
    "KHOI_CONG",
    "KhoiCong",
    "PI",
    "ERR_KHOI_CONG_HONG",
    "ERR_LOAI_KHOI_LA",
    "ERR_KHONG_CAT",
    "ERR_TIEP_XUC",
    "ERR_NGOAI_BAO_DONG",
    "ERR_KHONG_DO_DUOC",
    "intersect_plane_curved",
    "the_tich",
    "dien_tich_mat_cong",
    "ban_kinh",
    "binh_phuong_ban_kinh",
    "ERR_BAN_KINH_NGOAI_MIEN",
]

# ── MÃ LỖI ────────────────────────────────────────────────────────────────
#
# Tách riêng khỏi mã của `section.py` có chủ đích. `MALFORMED_SOLID` nói *"khối
# này hỏng"*; một mặt phẳng xiên cắt một hình trụ HOÀN TOÀN LÀNH LẶN thì khối
# không hỏng — chỉ là kết quả nằm ngoài thứ v1 biểu diễn được. Dùng lại mã cũ
# ở đây là lặp đúng lỗi mà `SECTION_COPLANAR_EDGE_GAP` đã phải đi sửa.

#: Ba điểm neo không dựng nên một khối cong (vành trùng tâm, trục suy biến,
#: vành không vuông góc trục). Đây là **khối hỏng thật**.
ERR_KHOI_CONG_HONG = "MALFORMED_CURVED_SOLID"
#: `kind` không có trong `KHOI_CONG`. Không bao giờ tới được từ IR (lược đồ đã
#: đóng enum), nên nó canh đường gọi thẳng từ mã.
ERR_LOAI_KHOI_LA = "UNKNOWN_CURVED_KIND"
#: Mặt phẳng không chạm khối.
ERR_KHONG_CAT = "CURVED_PLANE_DOES_NOT_CUT"
#: Mặt phẳng TIẾP XÚC — giao là một ĐIỂM, không phải đường tròn.
ERR_TIEP_XUC = "CURVED_PLANE_TANGENT"
#: Giao tồn tại nhưng không phải đường tròn (elip, conic, thiết diện qua trục).
#: **Khối không hỏng** — v1 không biểu diễn được kết quả.
ERR_NGOAI_BAO_DONG = "CURVED_SECTION_OUTSIDE_V1_CLOSURE"
#: Đại lượng không định nghĩa được cho loại khối này (vd chiều cao của khối cầu).
ERR_KHONG_DO_DUOC = "CURVED_MEASURE_UNDEFINED"
#: Bán kính khai thẳng nằm ngoài miền số: không dương, hoặc bình phương của nó
#: không hữu tỉ (bán kính có chứa π). **Không** phải "khối hỏng" — nó là biên
#: của MIỀN SỐ, và nói đúng tên biên là điều kiện để vòng sửa hành động được.
ERR_BAN_KINH_NGOAI_MIEN = "CURVED_RADIUS_OUTSIDE_DOMAIN"

#: `π` như một số chính xác. Dựng qua `radical()` để nó chính tắc như mọi số
#: khác — không có một hằng số π riêng ở đâu trong hệ.
PI: ExactNumber = radical(1, 1, 1)


# ── CIRCLE3 ───────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Circle3:
    """Đường tròn trong không gian: tâm ℚ³ · pháp tuyến ℚ³ · **bình phương**
    bán kính hữu tỉ.

    Giữ `radius_sq` chứ không giữ `radius` là cùng một mẹo mà `distance_sq` đã
    dùng từ đầu: bán kính có thể vô tỉ, bình phương của nó thì không. Nhờ vậy
    một đường tròn giao tuyến là **hoàn toàn chính xác trong ℚ** — và chỉ tới
    biên ĐO mới có một phép căn.

    `radius_sq > 0` là bất biến, không phải một phép kiểm phòng xa: `radius_sq
    == 0` nghĩa là hình ấy **là một điểm**, và trả về một `Circle3` bán kính 0
    là nói dối về kiểu. Đường sinh ra nó (`intersect_plane_curved`) từ chối ca
    tiếp xúc và chỉ sang `project_onto` — phép dựng ĐÚNG cho một điểm.
    """

    center: Point3
    normal: Vec3
    radius_sq: Fraction

    def __post_init__(self) -> None:
        if self.normal.is_zero():
            raise GeometryError(
                ERR_KHOI_CONG_HONG, "đường tròn cần pháp tuyến khác vectơ không")
        if self.radius_sq <= 0:
            raise GeometryError(
                ERR_KHOI_CONG_HONG,
                f"bán kính² phải dương, nhận {self.radius_sq} — một hình bán "
                "kính 0 là một ĐIỂM, không phải đường tròn")


# ── THẨM QUYỀN DUY NHẤT CỦA LOẠI KHỐI CONG ───────────────────────────────
@dataclass(frozen=True)
class KhoiCong:
    """Một loại khối cong: cần neo nào, kiểm gì, đo bằng công thức nào.

    ⚠️ **Đây là thẩm quyền DUY NHẤT.** Thẩm định, phép đo, chiếu cảnh và đặt
    tên đều tra bảng này; không tầng nào được mọc thêm một dãy
    `if ball / if cylinder / if cone` của riêng nó. Thêm một hình sau này =
    thêm **một hàng**, không thêm một module.
    """

    kind: str
    #: Khối này có điểm thứ hai trên trục không? Cầu thì không.
    co_truc: bool
    #: Danh từ tiếng Việt — dùng cho tên hiển thị. Thuộc về bảng này vì nó là
    #: metadata của LOẠI, và tách nó ra là dựng thẩm quyền thứ hai.
    danh_tu: str
    #: Tên của "mặt cong" theo cách SGK gọi, cho `lateral_area`.
    ten_mat_cong: str
    #: Vai của điểm thứ hai, cho thông báo lỗi đọc được.
    vai_dinh: str
    #: Loại này có được khai bằng **tâm + bán kính** thay cho một điểm vành
    #: không? (2026-09-04)
    #:
    #: Là một CỘT của bảng chứ không phải một phép so `kind == "ball"` ở tầng
    #: trên: `test_04c` cấm mọi tầng ngoài file này mọc nhánh theo tên hình, và
    #: cấm đúng — bản điều phối thứ hai là thứ trôi. Thêm hình thứ tư = thêm
    #: một hàng, và hàng ấy tự khai luôn nó nhận cách khai nào.
    #:
    #: ⚠️ **MỞ CHO CẢ BA từ `CURVED_CONSTRUCTION_GROUNDING_FOUNDATION`**
    #: (2026-09-05). Bản trước để trụ/nón `False` và gọi đó là quyết định
    #: phạm vi — *"lớp bài ấy đã có đường diễn đạt chạy được"*. Lượt V3
    #: held-out chứng minh câu ấy **SAI**: đường duy nhất cho trụ/nón là
    #: `rim_point`, tức một điểm trên vành đáy, mà đề SGK **không bao giờ đặt
    #: tên** cho điểm ấy — nên grounding gate chặn mọi cách khai nó, kể cả
    #: cách DỰNG. 0/6 ca trụ+nón đi qua được.
    khai_bang_ban_kinh: bool
    #: Khối này có cần một chiều cao VÔ HƯỚNG khi dựng bằng pose canonical
    #: không? Cầu thì không — bán kính đã xác định trọn hình.
    can_chieu_cao: bool
    #: Nghĩa vụ `area` của khối này THỰC RA là lượng đo nào — hoặc `None` nếu
    #: `area` không có nghĩa cho nó.
    #:
    #: ⚠️ Chỉ **khối cầu** có giá trị, và lý do là hình học chứ không phải tiện
    #: lợi: mặt cầu **không có đáy**, nên "diện tích mặt cầu" và "diện tích mặt
    #: cong" là CÙNG MỘT số, `4πR²`. Trụ và nón thì `S_tp = S_xq + S_đáy` — hai
    #: số khác nhau, và gộp chúng là nói dối về hình học.
    #:
    #: Là một CỘT của bảng vì họ hình là thứ quyết định, và `MemoryType` một
    #: mình KHÔNG đủ: cầu, trụ, nón dùng chung `curved_solid`, nên quyết định
    #: bằng kiểu bộ nhớ sẽ kéo cả trụ lẫn nón vào theo.
    nghia_vu_area_la: Optional[str]
    #: Khối này có được dựng bằng **pose canonical** không, tức khi đề chỉ cho
    #: vô hướng và **không đặt tên điểm nào**.
    #:
    #: Pose canonical là một lựa chọn HỆ QUY CHIẾU, không phải một dữ kiện.
    #: Nó không vào bộ nhớ ngữ nghĩa dưới bất kỳ cái tên nào, nên không phép
    #: đo hay quan hệ nào lấy nó làm chứng cứ được — đó là điều kiện để nó
    #: không thành một cửa rửa năng lực.
    cho_pose_canonical: bool
    #: `khoi → thể tích`, chính xác.
    the_tich: Callable[["CurvedSolid"], ExactNumber]
    #: `khoi → diện tích mặt cong`, chính xác.
    mat_cong: Callable[["CurvedSolid"], ExactNumber]


def _the_tich_cau(s: "CurvedSolid") -> ExactNumber:
    """`V = (4/3)πR³`.

    `R³ = R²·R = q·√q` với `q = radius_sq` hữu tỉ, nên tích ở lại dạng
    `he·π·√can` — **không** bao giờ phải bình phương một đại lượng chứa π.
    """
    q = s.radius_sq
    return multiply(times_rational(sqrt_rational(q), q * Fraction(4, 3)), PI)


def _mat_cau(s: "CurvedSolid") -> ExactNumber:
    """`S = 4πR² = 4πq` — hữu tỉ nhân π, luôn MỘT hạng tử."""
    return multiply(Fraction(4) * s.radius_sq, PI)


def _the_tich_tru(s: "CurvedSolid") -> ExactNumber:
    """`V = πr²h = π·q·√(h²)` — một căn duy nhất."""
    return multiply(times_rational(sqrt_rational(s.height_sq), s.radius_sq), PI)


def _mat_tru(s: "CurvedSolid") -> ExactNumber:
    """`S_xq = 2πrh = 2π√(q·h²)` — tích DƯỚI một dấu căn, nên vẫn một hạng tử.

    Nhân hai căn rồi mới lấy căn (`√q·√h² = √(q·h²)`) là điều kiện để kết quả
    ở lại trong miền: giữ chúng tách ra thì đây là tích hai căn thức, thứ miền
    số cố ý không nhận.
    """
    return multiply(times_rational(sqrt_rational(s.radius_sq * s.height_sq), 2), PI)


def _the_tich_non(s: "CurvedSolid") -> ExactNumber:
    """`V = (1/3)πr²h`."""
    return multiply(
        times_rational(sqrt_rational(s.height_sq), s.radius_sq * Fraction(1, 3)), PI)


def _mat_non(s: "CurvedSolid") -> ExactNumber:
    """`S_xq = πrl` với `l² = r² + h²` ⇒ `= π√(q·(q + h²))` — một căn."""
    q = s.radius_sq
    return multiply(sqrt_rational(q * (q + s.height_sq)), PI)


#: BA HÀNG. Thêm hình thứ tư = thêm hàng thứ tư.
#: POSE CANONICAL — hệ quy chiếu TRÌNH BÀY, không phải dữ kiện của đề.
#:
#: Dùng khi đề chỉ cho vô hướng và không đặt tên điểm nào. Hai hằng số này là
#: một lựa chọn hệ trục, và chúng phải **tất định** (cùng đề ⇒ cùng pose, mọi
#: lượt replay) và **hữu tỉ** (toạ độ ở lại ℚ³).
#:
#: ⚠️ Chúng KHÔNG bao giờ vào bộ nhớ ngữ nghĩa dưới một cái tên. Đó là toàn bộ
#: lý do chúng an toàn: không tên ⇒ không `distance(O, X)` nào viện được tới,
#: nên chúng không thể biến thành chứng cứ cho một phép đo.
GOC_CANONICAL = Point3(Fraction(0), Fraction(0), Fraction(0))
HUONG_TRUC_CANONICAL = Vec3(Fraction(0), Fraction(0), Fraction(1))

KHOI_CONG: dict[str, KhoiCong] = {
    k.kind: k for k in (
        KhoiCong("ball", False, "Khối cầu", "mặt cầu", "",
                 True, False, "lateral_area", True, _the_tich_cau, _mat_cau),
        KhoiCong("cylinder", True, "Hình trụ", "mặt xung quanh", "tâm đáy trên",
                 True, True, None, True, _the_tich_tru, _mat_tru),
        KhoiCong("cone", True, "Hình nón", "mặt xung quanh", "đỉnh",
                 True, True, None, True, _the_tich_non, _mat_non),
    )
}


# ── KHỐI CONG ─────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class CurvedSolid:
    """Khối cong có biên, khai bằng **ba điểm neo hữu tỉ đã được dựng**.

        ball      (I,  —,  A)   tâm · điểm trên mặt
        cylinder  (O,  O′, A)   tâm đáy · tâm đáy kia · điểm trên vành đáy
        cone      (O,  S,  A)   tâm đáy · đỉnh · điểm trên vành đáy

    Mọi tham số (bán kính, chiều cao, trục) **dẫn xuất** từ ba điểm ấy và không
    được lưu trùng: một sự thật, một chỗ. Chúng là `@property` tính lại mỗi lần
    — phép tính là vài phép nhân hữu tỉ, và cái giá ấy rẻ hơn nhiều so với một
    trường có thể lệch khỏi các điểm sinh ra nó.
    """

    kind: str
    anchor: Point3
    apex_or_top: Optional[Point3]
    rim_point: Optional[Point3] = None
    #: HAI CÁCH KHAI BÁN KÍNH, và đúng một cái được dùng mỗi lần.
    #:
    #: `rim_point` là cách gốc: bán kính DẪN XUẤT từ một điểm đã dựng. Cách này
    #: giữ mọi toạ độ trong ℚ³ và không cho mô hình khai thẳng một con số.
    #:
    #: `radius_sq_khai` là cách thứ hai, mở 2026-09-04. Nó **bắt buộc phải có**
    #: vì cách gốc KHÔNG diễn đạt nổi lớp bài *"mặt cầu tâm O bán kính r"*:
    #: không phép dựng nào sinh được một điểm CÁCH một điểm cho trước đúng một
    #: độ dài cho trước, và ngay cả khi engine tự dựng thì nó vẫn bất khả —
    #: định lý ba bình phương hữu tỉ nói `r² = 7` **không** là tổng ba bình
    #: phương hữu tỉ, nên mặt cầu bán kính `√7` không có MỘT điểm vành hữu tỉ
    #: nào. Bịt bằng một điểm phụ là bịt bằng một thứ không tồn tại.
    #:
    #: Đây KHÔNG phải cửa cho toạ độ thô: `radius_sq` là một VÔ HƯỚNG, không
    #: phải một vị trí, và R0 vẫn đòi nó truy được về đề (xem `grounding_gate`).
    radius_sq_khai: Optional[Fraction] = None
    #: CHIỀU CAO² khai thẳng — song sinh của `radius_sq_khai`, thêm 2026-09-05
    #: (`CURVED_CONSTRUCTION_GROUNDING_FOUNDATION`).
    #:
    #: Cần vì cùng một lý do: đề *"hình trụ bán kính 7, chiều cao 10"* không
    #: đặt tên điểm nào, nên không có `apex_or_top` nào dựng được. Và giữ
    #: **bình phương** chứ không giữ chiều cao vì `h = √7` không hữu tỉ trong
    #: khi `h² = 7` thì có — y hệt mẹo của `radius_sq`.
    height_sq_khai: Optional[Fraction] = None
    #: Khối này được đặt bằng **pose canonical** (hệ quy chiếu trình bày) hay
    #: bằng các điểm của đề?
    #:
    #: Khai TƯỜNG MINH thay vì suy ra từ `anchor == gốc`: một đề hoàn toàn có
    #: thể cho tâm ở đúng gốc toạ độ, và khi ấy suy ra sẽ nói dối rằng vật
    #: không có liên kết với đề. Cột này là thứ `simulation_state` đọc để đánh
    #: dấu `presentation_only`, nên nó phải nói đúng nguồn gốc.
    pose_canonical: bool = False

    def __post_init__(self) -> None:
        kc = KHOI_CONG.get(self.kind)
        if kc is None:
            raise GeometryError(
                ERR_LOAI_KHOI_LA,
                f"loại khối cong '{self.kind}' không có trong {sorted(KHOI_CONG)}")
        # ⓪ ĐÚNG MỘT cách khai bán kính. Cho cả hai là mở đường cho hai lời
        #    khai mâu thuẫn về cùng một hình — và khi ấy phải CHỌN HỘ, thứ
        #    `_nang_declare_point` đã học là không được làm.
        if (self.rim_point is None) == (self.radius_sq_khai is None):
            raise GeometryError(
                ERR_KHOI_CONG_HONG,
                f"{kc.danh_tu.lower()}: phải khai ĐÚNG MỘT trong hai — một "
                "điểm trên vành, hoặc bán kính")
        if self.radius_sq_khai is not None:
            if self.radius_sq_khai <= 0:
                raise GeometryError(
                    ERR_BAN_KINH_NGOAI_MIEN,
                    f"{kc.danh_tu.lower()}: bán kính² = {self.radius_sq_khai} "
                    "phải dương — bán kính 0 là một ĐIỂM, không phải khối")
        # ① VÀNH KHÁC TÂM — chung cho cả ba loại. Bán kính 0 không phải một
        #    khối; nó là một điểm, và mọi phép đo phía sau sẽ vô nghĩa.
        elif (self.rim_point - self.anchor).is_zero():
            raise GeometryError(
                ERR_KHOI_CONG_HONG,
                f"{kc.danh_tu.lower()}: điểm trên vành TRÙNG với tâm — bán "
                "kính bằng 0")
        # ⓪b CHIỀU CAO KHAI THẲNG — miền và tính nhất quán với loại.
        if self.height_sq_khai is not None:
            if not kc.can_chieu_cao:
                raise GeometryError(
                    ERR_KHOI_CONG_HONG,
                    f"{kc.danh_tu.lower()} không có chiều cao — bán kính đã "
                    "xác định trọn hình")
            if self.height_sq_khai <= 0:
                raise GeometryError(
                    ERR_BAN_KINH_NGOAI_MIEN,
                    f"{kc.danh_tu.lower()}: chiều cao² = {self.height_sq_khai} "
                    "phải dương — chiều cao 0 thì không có khối")
        if not kc.co_truc:
            if self.apex_or_top is not None:
                raise GeometryError(
                    ERR_KHOI_CONG_HONG,
                    f"{kc.danh_tu.lower()} chỉ cần tâm và một điểm trên mặt")
            return
        # Trục do ĐÚNG MỘT trong hai xác định: một điểm thứ hai đã dựng, hoặc
        # một chiều cao vô hướng truy được về đề. Cho cả hai là mở đường cho
        # hai lời khai mâu thuẫn về cùng một trục.
        if (self.apex_or_top is None) == (self.height_sq_khai is None):
            raise GeometryError(
                ERR_KHOI_CONG_HONG,
                f"{kc.danh_tu.lower()}: trục phải do ĐÚNG MỘT trong hai xác "
                f"định — {kc.vai_dinh}, hoặc chiều cao khai thẳng")
        if self.apex_or_top is None:
            return
        truc = self.apex_or_top - self.anchor
        # ② TRỤC KHÔNG SUY BIẾN — chiều cao 0 thì không có khối.
        if truc.is_zero():
            raise GeometryError(
                ERR_KHOI_CONG_HONG,
                f"{kc.danh_tu.lower()}: {kc.vai_dinh} TRÙNG tâm đáy — chiều "
                "cao bằng 0")
        # ③ VÀNH VUÔNG GÓC TRỤC — bất biến ba điểm. So BẰNG trên `Fraction`,
        #    không epsilon: lệch một phần triệu vẫn là một hình không tồn tại,
        #    và cho nó qua là dựng một vật rồi để renderer vẽ ra thứ trông hợp
        #    lý mà sai.
        #
        #    Khai bằng bán kính thì bất biến này KHÔNG áp được và cũng không
        #    cần: không có điểm vành nào để lệch. Mặt đáy vẫn xác định duy nhất
        #    bởi (tâm ⊥ trục), y như trước.
        if self.rim_point is not None and (self.rim_point - self.anchor).dot(truc) != 0:
            raise GeometryError(
                ERR_KHOI_CONG_HONG,
                f"{kc.danh_tu.lower()}: điểm trên vành KHÔNG nằm trong mặt đáy "
                "— nó phải vuông góc với trục tại tâm đáy")

    # ── tham số DẪN XUẤT, chính xác, không lưu trùng ──────────────────────
    @property
    def loai(self) -> KhoiCong:
        return KHOI_CONG[self.kind]

    @property
    def radius_sq(self) -> Fraction:
        """MỘT cửa duy nhất cho bán kính², bất kể khai bằng cách nào.

        Mọi phép đo và mọi phép cắt đọc thuộc tính này, nên hai cách khai không
        đẻ ra hai đường tính — đó là điều kiện để `KHOI_CONG` vẫn là thẩm quyền
        duy nhất và không tầng nào mọc `if rim_point else`.
        """
        if self.radius_sq_khai is not None:
            return self.radius_sq_khai
        v = self.rim_point - self.anchor
        return v.dot(v)

    @property
    def truc(self) -> Vec3:
        """Vectơ trục. `Vec3` không (chỉ với khối cầu) — cầu không có trục."""
        if self.apex_or_top is None:
            return Vec3(Fraction(0), Fraction(0), Fraction(0))
        return self.apex_or_top - self.anchor

    @property
    def huong_truc(self) -> Vec3:
        """HƯỚNG trục — tách khỏi `truc` vì độ dài có thể vô tỉ.

        Khai bằng chiều cao thì `h = √7` không có điểm hữu tỉ nào cách tâm
        đúng `h`, nên `truc` (một vectơ MANG độ dài) không dựng được. Nhưng
        *hướng* thì luôn dựng được, và hướng là thứ duy nhất mà mặt phẳng đáy
        và trục cần. Hai khái niệm khác nhau, nên hai thuộc tính.
        """
        if self.apex_or_top is not None:
            return self.truc
        if self.height_sq_khai is not None:
            return HUONG_TRUC_CANONICAL
        return Vec3(Fraction(0), Fraction(0), Fraction(0))

    @property
    def height_sq(self) -> Fraction:
        """MỘT cửa duy nhất cho chiều cao², bất kể khai bằng cách nào —
        y hệt hợp đồng của `radius_sq`."""
        if self.height_sq_khai is not None:
            return self.height_sq_khai
        d = self.truc
        return d.dot(d)

    @property
    def axis(self) -> Line3:
        if not self.loai.co_truc:
            raise GeometryError(
                ERR_KHONG_DO_DUOC, "khối cầu không có trục")
        return Line3(self.anchor, self.huong_truc)


# ── PHÉP ĐO — công thức nằm ở BẢNG, đây chỉ là cửa ───────────────────────
def the_tich(s: CurvedSolid) -> ExactNumber:
    return s.loai.the_tich(s)


def dien_tich_mat_cong(s: CurvedSolid) -> ExactNumber:
    """Diện tích **mặt cong**: mặt cầu · xung quanh trụ · xung quanh nón.

    ⚠️ **KHÔNG phải diện tích TOÀN PHẦN**, và sự vắng mặt ấy là một quyết định
    được chứng minh, không phải một thiếu sót. `S_tp` của nón `= πrl + πr²` có
    hai căn thức khác nhau, và miền số cố ý từ chối tổng ấy (`radical.add`).
    Mở một phép đo mà những ca hợp lệ thường gặp đều ném là dạy mô hình một cửa
    dẫn thẳng vào lỗi runtime — mà lỗi runtime không được gửi ngược để sửa.

    Ngược lại, ba công thức ở đây **luôn** biểu diễn được: mỗi cái là một phân
    số nhân π nhân **đúng một** căn của một số hữu tỉ không âm, và
    `sqrt_rational` không có nhánh thất bại trên miền ấy.
    """
    return s.loai.mat_cong(s)


def binh_phuong_ban_kinh(r: ExactNumber) -> Fraction:
    """`r → r²` cho một bán kính khai thẳng. **Nghịch đảo đúng của `ban_kinh`.**

    ─── HỢP ĐỒNG MIỀN SỐ ──────────────────────────────────────────────────

    Miền số là `he·π^mu·√can`. Bình phương nó cho `he²·π^(2mu)·can`, và thứ đó
    HỮU TỈ **khi và chỉ khi** `mu = 0`. Nên hàm này nhận trọn miền số trừ đúng
    một lát: bán kính có chứa π.

        13    → 169        hữu tỉ
        5/2   → 25/4       hữu tỉ
        √3    → 3          vô tỉ mà bình phương hữu tỉ — đúng chỗ mẹo
                           `radius_sq` phát huy
        2π    → TỪ CHỐI    `CURVED_RADIUS_OUTSIDE_DOMAIN`

    Từ chối bằng **mã có cấu trúc**, không bằng một phép làm tròn: một bán kính
    chứa π nghĩa là đề đang nói về thứ khác (chu vi? diện tích?), và đoán hộ ở
    đây là dựng một hình không ai định vẽ.
    """
    # DẤU phải kiểm TRƯỚC khi bình phương — bình phương xoá mất nó, và một
    # bán kính `-3` sẽ lặng lẽ thành `9`. Đúng lớp lỗi mà miền số này sinh ra
    # để chặn: một con số đi qua mà không ai nói nó vô nghĩa.
    if isinstance(r, Radical):
        if r.mu != 0:
            raise GeometryError(
                ERR_BAN_KINH_NGOAI_MIEN,
                f"bán kính {display(r)} chứa π — bình phương của nó không hữu "
                "tỉ, nên khối không biểu diễn được chính xác")
        am = r.he <= 0
        q = r.he * r.he * Fraction(r.can)
    elif isinstance(r, (Fraction, int)) and not isinstance(r, bool):
        am = Fraction(r) <= 0
        q = Fraction(r) * Fraction(r)
    else:
        raise GeometryError(
            ERR_BAN_KINH_NGOAI_MIEN,
            f"bán kính phải là một số chính xác, nhận {type(r).__name__}")
    if am or q <= 0:
        raise GeometryError(
            ERR_BAN_KINH_NGOAI_MIEN,
            f"bán kính {display(r)} phải DƯƠNG")
    return q


def ban_kinh(x: CurvedSolid | Circle3) -> ExactNumber:
    """Bán kính — dùng lại `sqrt_rational`, không tự viết phép căn."""
    return sqrt_rational(x.radius_sq)


def dien_tich_hinh_tron(c: Circle3) -> ExactNumber:
    """`S = πr²` — hữu tỉ nhân π, luôn một hạng tử."""
    return multiply(c.radius_sq, PI)


# ── GIAO MẶT PHẲNG × KHỐI CONG ───────────────────────────────────────────
#
# HỢP ĐỒNG KIỂU: hàm này trả về **`Circle3` hoặc ném**. Không bao giờ trả một
# `Point3` lén lút.
#
# Ca tiếp xúc (giao là MỘT ĐIỂM) bị từ chối, và lời từ chối **nêu tên phép dựng
# đúng**: `project_onto(tâm, mặt phẳng)` cho ra chính điểm ấy, chính xác, bằng
# IR đã có. Nên đây không phải một năng lực bị cắt — nó là một lối đi được chỉ
# sang đúng primitive, và nhờ vậy `_CHU_KY` khai được đúng MỘT kiểu trả về.


def _cat_truc(s: CurvedSolid, pl: Plane3) -> Fraction:
    """Tham số `t` nơi mặt phẳng cắt trục: `t = 0` ở `anchor`, `1` ở đỉnh/đáy kia.

    Hữu tỉ, vì mặt phẳng và trục đều hữu tỉ.
    """
    p = intersect_line_plane(s.axis, pl)
    d = s.truc
    return (p - s.anchor).dot(d) / d.dot(d)


def intersect_plane_curved(s: CurvedSolid, pl: Plane3) -> Circle3:
    """Giao của một mặt phẳng với một khối cong, **khi kết quả là đường tròn**.

    Bao đóng v1, khai thẳng:

        cầu   · MỌI mặt phẳng cắt thật     → đường tròn
        trụ   · mặt phẳng ⊥ trục, trong biên → đường tròn
        nón   · mặt phẳng ⊥ trục, trong biên, chưa tới đỉnh → đường tròn

    Mọi thứ khác **từ chối có mã**. Không xấp xỉ, không trả một đa giác gần
    đúng, không mượn mã lỗi của đa diện.
    """
    if s.kind == "ball":
        return _giao_cau(s, pl)
    return _giao_tron_xoay(s, pl)


def _giao_cau(s: CurvedSolid, pl: Plane3) -> Circle3:
    """`d² = distance²(tâm, mp)`; `r'² = r² − d²`. Toàn bộ hữu tỉ.

    Tâm đường tròn là **hình chiếu chính xác** của tâm cầu lên mặt phẳng, nên
    nó ở lại ℚ³ — đó là lý do ca này không cần một miền toạ độ rộng hơn.
    """
    from .measure import distance_sq_point_plane

    d2 = distance_sq_point_plane(s.anchor, pl)
    q = s.radius_sq
    if d2 > q:
        raise GeometryError(
            ERR_KHONG_CAT,
            "mặt phẳng không cắt khối cầu — nó nằm xa tâm hơn bán kính")
    if d2 == q:
        raise GeometryError(
            ERR_TIEP_XUC,
            "mặt phẳng TIẾP XÚC khối cầu: giao là một ĐIỂM, không phải đường "
            "tròn. Dựng điểm ấy bằng hình chiếu của tâm lên mặt phẳng "
            "(`project_onto`).")
    return Circle3(project_point_onto_plane(s.anchor, pl), pl.normal, q - d2)


def _giao_tron_xoay(s: CurvedSolid, pl: Plane3) -> Circle3:
    """Trụ và nón — chỉ mặt phẳng VUÔNG GÓC TRỤC cho đường tròn."""
    kc = s.loai
    d = s.truc
    # ⊥ trục ⇔ pháp tuyến CÙNG PHƯƠNG trục. Tích có hướng bằng vectơ không là
    # phép kiểm chính xác, không cần chuẩn hoá độ dài.
    if not d.cross(pl.normal).is_zero():
        raise GeometryError(
            ERR_NGOAI_BAO_DONG,
            f"{kc.danh_tu.lower()}: mặt phẳng không vuông góc với trục. Giao "
            "khi ấy là một elip (hoặc conic khác), thứ phiên bản này không "
            "biểu diễn được. Thiết diện QUA TRỤC thì dựng bằng đa giác: lấy "
            "điểm xuyên tâm đối bằng `divide_segment` rồi nối bằng "
            "`construct_polygon`.")
    t = _cat_truc(s, pl)
    if t < 0 or t > 1:
        raise GeometryError(
            ERR_KHONG_CAT,
            f"{kc.danh_tu.lower()}: mặt phẳng cắt trục NGOÀI khối "
            f"(vị trí {t} trên trục, cần trong khoảng 0…1)")
    tam = s.anchor + d.scale(t)
    if s.kind == "cylinder":
        return Circle3(tam, d, s.radius_sq)
    # Nón: bán kính co tuyến tính từ đáy (t=0) tới đỉnh (t=1).
    he = (1 - t) ** 2
    if he == 0:
        raise GeometryError(
            ERR_TIEP_XUC,
            "mặt phẳng đi qua ĐỈNH nón: giao là chính điểm đỉnh, không phải "
            "đường tròn. Đỉnh đã là một điểm có tên trong chương trình.")
    return Circle3(tam, d, he * s.radius_sq)


def khong_sinh_diem_tren_mat_cong(ten_phep: str) -> GeometryError:
    """Lời từ chối CHUNG cho mọi phép đòi một điểm nằm trên mặt cong.

    Giao đường thẳng với mặt cong cho `t = (−B ± √Δ)/2A`, và toạ độ rơi vào
    `ℚ(√Δ)³`. `Vec3` là ℚ³ và **phải ở lại ℚ³**: mọi vị từ so bằng của kernel
    (`same_point`, `coplanar`, `point_on_plane`) dựa vào điều đó. Xấp xỉ nghiệm
    là đưa float vào đúng chỗ cả nhân này được dựng để tránh.
    """
    return GeometryError(
        ERR_NGOAI_BAO_DONG,
        f"'{ten_phep}' cần một điểm NẰM TRÊN mặt cong, và toạ độ của nó nói "
        "chung không hữu tỉ — phiên bản này không biểu diễn được. Các điểm "
        "hữu tỉ trên mặt (tâm, điểm vành đã khai) thì dùng được.")
