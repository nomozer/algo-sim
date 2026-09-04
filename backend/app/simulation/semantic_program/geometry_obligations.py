# -*- coding: utf-8 -*-
"""CHÍN checker nghĩa vụ hình học — tầng C₂ của miền không gian. **0 API call.**

VÌ SAO MIỀN NÀY CÓ ĐỦ CHECKER CHO MỌI NGHĨA VỤ, trong khi miền Tin học phải để
`predicate_verdict` ở mức yếu suốt nhiều tháng: ở đó, kiểm *"dãy này có được
sắp đúng không"* đòi **cài lại chính thuật toán đang kiểm**, nên oracle mất tính
độc lập. Ở hình học, câu trả lời là **giải tích**: `u · v == 0` là một phép
tính, không phải một cách giải bài. Kiểm không dùng lại lời giải.

RANH GIỚI VỚI KERNEL: file này **gọi vị từ**, không cài lại toán. Cài lại là đẻ
ra tầng hình học thứ hai, và hai tầng chắc chắn sẽ lệch nhau ở một ca nào đó —
lệch im lặng, vì cả hai đều "chạy".

RANH GIỚI VỚI ORACLE: đây **không** phải oracle. Đây là cổng **nội bộ** (C₂):
nó hỏi *"chương trình có tự mâu thuẫn với nghĩa vụ nó tự khai không"*. Oracle
độc lập (`docs/evaluation/geometry/custodian/geometry_oracle.py`) hỏi câu khác:
*"kết quả có khớp ground truth do người ngoài dựng không"*. Hai câu, hai tầng —
gộp lại là mất tính độc lập.
"""
from __future__ import annotations

from typing import Any

from ..geometry import Line3, Plane3, Vec3
from ..geometry import measure as M
from ..geometry import predicates as P
from ..geometry.radical import display, is_exact_number, parse_exact, square
from ..geometry.section import Polyhedron, Section

#: Sai lệch giữa giá trị máy tính ra và giá trị đề mong đợi.
_LECH = "giá trị không khớp"


def _lay(snapshot: dict[str, Any], ten: str | None) -> Any:
    return snapshot.get(ten) if ten else None


def _so(raw: Any):
    """Giá trị mong đợi trong nghĩa vụ → `ExactNumber`. Không đọc được ⇒ `None`
    (mức yếu), KHÔNG phải 0 — nhầm hai cái là biến 'không biết' thành 'bằng 0'.

    Nhận cả căn thức viết bằng chữ (`"sqrt(2)"`, `"3*sqrt(2)/5"`) qua văn phạm
    HẸP của `parse_exact` — đó là chỗ DUY NHẤT căn thức đi VÀO hệ, và nó hẹp có
    chủ đích: không eval, không parser biểu thức tổng quát.
    """
    return parse_exact(raw)


# ── nhóm QUAN HỆ: trả lời đúng/sai ────────────────────────────────────────
def check_point_on_line(snapshot: dict, ob) -> str | None:
    ln, p = _lay(snapshot, ob.container), _lay(snapshot, ob.witness)
    if not isinstance(ln, Line3) or not isinstance(p, Vec3):
        return "cần một `line3` và một `point3`"
    return None if P.point_on_line(p, ln) else "điểm KHÔNG thuộc đường thẳng"


def check_point_on_plane(snapshot: dict, ob) -> str | None:
    pl, p = _lay(snapshot, ob.container), _lay(snapshot, ob.witness)
    if not isinstance(pl, Plane3) or not isinstance(p, Vec3):
        return "cần một `plane3` và một `point3`"
    return None if P.point_on_plane(p, pl) else "điểm KHÔNG thuộc mặt phẳng"


def check_parallel(snapshot: dict, ob) -> str | None:
    a, b = _lay(snapshot, ob.container), _lay(snapshot, ob.witness)
    if isinstance(a, Line3) and isinstance(b, Line3):
        return None if P.parallel_lines(a, b) else "hai đường KHÔNG song song"
    if isinstance(a, Plane3) and isinstance(b, Plane3):
        return None if P.parallel_planes(a, b) else "hai mặt KHÔNG song song"
    # Đường ∥ mặt là quan hệ THẬT SỰ khác: nó đòi đường KHÔNG nằm trong mặt.
    if isinstance(a, Line3) and isinstance(b, Plane3):
        return None if P.parallel_line_plane(a, b) else \
            "đường KHÔNG song song mặt phẳng (hoặc nằm TRONG nó)"
    if isinstance(a, Plane3) and isinstance(b, Line3):
        return None if P.parallel_line_plane(b, a) else \
            "đường KHÔNG song song mặt phẳng (hoặc nằm TRONG nó)"
    return "cặp đối tượng không hợp lệ cho quan hệ song song"


def check_perpendicular(snapshot: dict, ob) -> str | None:
    a, b = _lay(snapshot, ob.container), _lay(snapshot, ob.witness)
    if isinstance(a, Line3) and isinstance(b, Line3):
        return None if P.perpendicular_lines(a, b) else "hai đường KHÔNG vuông góc"
    if isinstance(a, Plane3) and isinstance(b, Plane3):
        return None if P.perpendicular_planes(a, b) else "hai mặt KHÔNG vuông góc"
    # ⚠️ Đường ⊥ mặt ⇔ phương đường CÙNG PHƯƠNG pháp tuyến — không phải `dot==0`.
    # Chỗ lộn dấu kinh điển; kernel đã viết đúng, ở đây chỉ gọi.
    if isinstance(a, Line3) and isinstance(b, Plane3):
        return None if P.line_perpendicular_plane(a, b) else \
            "đường KHÔNG vuông góc mặt phẳng"
    if isinstance(a, Plane3) and isinstance(b, Line3):
        return None if P.line_perpendicular_plane(b, a) else \
            "đường KHÔNG vuông góc mặt phẳng"
    return "cặp đối tượng không hợp lệ cho quan hệ vuông góc"


def check_coplanar(snapshot: dict, ob) -> str | None:
    c = _lay(snapshot, ob.container)
    diem = list(c) if isinstance(c, (list, tuple)) else \
        (list(c.polygon) if isinstance(c, Section) else None)
    if diem is None and isinstance(c, Polyhedron):
        return "một KHỐI thì hiển nhiên không đồng phẳng — nghĩa vụ gắn sai chủ thể"
    if not diem or len(diem) < 4:
        return "cần ít nhất 4 điểm để hỏi về đồng phẳng"
    a = diem[0]
    return None if all(P.coplanar(a, diem[1], diem[2], p) for p in diem[3:]) \
        else "các điểm KHÔNG đồng phẳng"


# ── nhóm ĐẠI LƯỢNG: trả lời một số ────────────────────────────────────────
#
# So sánh làm trên BÌNH PHƯƠNG với `distance`, và trên `cos²` với `angle` —
# hai đại lượng ấy vô tỉ, còn bình phương của chúng thì hữu tỉ. Lấy căn rồi so
# là đưa sai số float quay lại qua cửa sau.
#
# ─── HAI HÌNH DẠNG WITNESS, và vì sao phải nhận cả hai (Wave 2) ────────────
#
# HÌNH DẠNG CŨ: `witness` là ĐỐI TƯỢNG thứ hai của phép đo, và giá trị mong đợi
# nằm ở `params["value"]`. Giữ nguyên, không hồi quy.
#
# HÌNH DẠNG MỚI: `witness` là CON SỐ mà chương trình đo ra (qua biểu thức
# `measure`), đối tượng thứ hai nằm ở `params["wrt"]`.
#
# Hình dạng mới MẠNH HƠN, và đó là lý do nó có mặt: cổng tính lại đại lượng từ
# hình rồi so với con số chương trình khai. Hình dạng cũ chỉ so được với con số
# do `analyze` khai — tức so lời một model với lời chính model ấy. Ngoài ra
# `cham_oracle` đọc `final_memory[witness]`, nên nếu witness không bao giờ là
# một con số thì `distance`/`angle`/`volume` **không chấm được bằng oracle** —
# đúng 4/10 bài của tập DEV.
def _la_so(v) -> bool:
    return is_exact_number(v)


def check_distance(snapshot: dict, ob) -> str | None:
    a = _lay(snapshot, ob.container)
    b = _lay(snapshot, ob.witness)
    khai = None
    if _la_so(b):
        khai = b
        b = _lay(snapshot, ob.params.get("wrt"))
    mong = _so(ob.params.get("value"))
    if mong is None and khai is None:
        return None  # không khai giá trị ⇒ chỉ kiểm được cấu trúc, mức yếu
    try:
        # ⚠️ KHOẢNG CÁCH ĐỐI XỨNG, nên cả HAI thứ tự đều phải nhận. Bản trước chỉ
        # nhận `(mặt, điểm)` và `(đường, điểm)`; một chương trình đo
        # `distance(A, L)` — thứ tự `_do` chấp nhận hoàn toàn bình thường — rơi
        # xuống nhánh cuối và nhận *"cặp đối tượng không hợp lệ"*. Đó không phải
        # một phép kiểm bỏ sót mà là một phép kiểm SAI: chương trình đúng bị
        # đánh trượt, và thông điệp đổ lỗi cho hình thay vì cho cổng.
        if isinstance(a, Plane3) and isinstance(b, Vec3):
            d2 = M.distance_sq_point_plane(b, a)
        elif isinstance(a, Vec3) and isinstance(b, Plane3):
            d2 = M.distance_sq_point_plane(a, b)
        elif isinstance(a, Line3) and isinstance(b, Vec3):
            d2 = M.distance_sq_point_line(b, a)
        elif isinstance(a, Vec3) and isinstance(b, Line3):
            d2 = M.distance_sq_point_line(a, b)
        elif isinstance(a, Vec3) and isinstance(b, Vec3):
            d2 = M.distance_sq(a, b)
        # Ba cặp mở thêm 2026-08-30. Bộ kiểm TỰ TÍNH LẠI từ hình — nó không
        # bao giờ đọc con số chương trình khai rồi gật đầu.
        elif isinstance(a, Line3) and isinstance(b, Line3):
            d2 = M.distance_sq_lines(a, b)
        elif isinstance(a, Line3) and isinstance(b, Plane3):
            d2 = M.distance_sq_line_plane(a, b)
        elif isinstance(a, Plane3) and isinstance(b, Line3):
            d2 = M.distance_sq_line_plane(b, a)
        elif isinstance(a, Plane3) and isinstance(b, Plane3):
            d2 = M.distance_sq_planes(a, b)
        else:
            return "cặp đối tượng không hợp lệ cho khoảng cách"
    except Exception as e:  # noqa: BLE001 — lỗi hình học là kết luận, không phải sự cố
        return f"không đo được khoảng cách: {e}"
    # SO TRÊN MIỀN BÌNH PHƯƠNG, và đó là lý do bộ chấm không phải viết lại khi
    # miền số mở rộng sang căn thức: `square()` của một căn LUÔN hữu tỉ, nên
    # phép so vẫn đi hết trong ℚ. `d = 3√2/5` chấm được mà không cần so hai căn.
    if khai is not None and d2 != square(khai):
        return f"{_LECH}: chương trình khai d = {display(khai)}, hình cho d² = {d2}"
    if mong is not None and d2 != square(mong):
        return f"{_LECH}: d² = {d2}, đề mong {display(mong)}²"
    return None


def check_radius(snapshot: dict, ob) -> str | None:
    """Bán kính — MỘT checker cho cả đường tròn lẫn ba hình cong.

    ─── LỖ NÓ BỊT ──────────────────────────────────────────────────────────

    `RADIUS_OBLIGATION_COVERAGE` mở nghĩa vụ `radius` nhưng **không** thêm
    checker, nên mọi đề hỏi bán kính chạy được mà `servable=False` — hệ tính ra
    đúng con số rồi không dám phục vụ nó. Đây là chỗ đóng khoảng ấy.

    ─── VÌ SAO KHÔNG CÓ `check_ball_radius` / `check_cylinder_radius` ───────

    Hình nào là **dữ liệu** (`curved_kind`), và `radius_sq` là một `@property`
    dẫn từ ba điểm neo — cùng một công thức cho cả ba. Ba checker sẽ là ba bản
    của một phép trừ vectơ, và chúng sẽ lệch nhau ở ca thứ ba.

    `Circle3` vào cùng cửa vì nó cũng chở `radius_sq`. Không `check_circle_
    radius` riêng.

    ─── SO TRÊN MIỀN BÌNH PHƯƠNG ───────────────────────────────────────────

    Cùng lý do `check_distance` so `d²`: `square()` của một căn LUÔN hữu tỉ,
    nên phép so đi hết trong ℚ kể cả khi đáp số là `√3`. So hai căn thức trực
    tiếp thì đúng, nhưng nó buộc bộ chấm phải biết miền số — và bộ chấm càng
    biết ít về thứ nó chấm thì càng khó sai theo cùng một cách.

    ⚠️ Lấy `radius_sq` từ chính vật, KHÔNG gọi `curved.ban_kinh` rồi bình
    phương lại: `ban_kinh` là `sqrt_rational(radius_sq)`, nên đi vòng chỉ thêm
    một phép căn rồi một phép bình phương để về đúng chỗ cũ. Và `radius_sq` là
    property tính lại từ ba điểm neo mỗi lần, nên **không có bản lưu nào để
    trôi**.
    """
    from ..geometry.curved import Circle3, CurvedSolid

    x = _lay(snapshot, ob.container)
    if not isinstance(x, (Circle3, CurvedSolid)):
        return "cần một `circle3` hoặc một `curved_solid`"
    w = _lay(snapshot, ob.witness)
    khai = w if _la_so(w) else None
    mong = _so(ob.params.get("value"))
    if mong is None and khai is None:
        return None  # không khai giá trị ⇒ chỉ kiểm được cấu trúc, mức yếu
    r2 = x.radius_sq
    if khai is not None and square(khai) != r2:
        return f"{_LECH}: chương trình khai R = {display(khai)}, hình cho R² = {r2}"
    if mong is not None and square(mong) != r2:
        return f"{_LECH}: R² = {r2}, đề mong {display(mong)}²"
    return None


def check_angle(snapshot: dict, ob) -> str | None:
    a = _lay(snapshot, ob.container)
    b = _lay(snapshot, ob.witness)
    khai = None
    if _la_so(b):
        khai = b
        b = _lay(snapshot, ob.params.get("wrt"))
    mong = _so(ob.params.get("cos_sq"))
    if mong is None and khai is None:
        return None
    # CÙNG hàm mà đường thực thi dùng (`geometry_exec._do`). Trước bản này ở
    # đây có một bản SAO của phép phân phối theo cặp kiểu, và bản sao ấy mang
    # đúng con bug của bản gốc: cặp (đường, mặt) gọi `sin_sq_line_plane` rồi
    # được gọi là cos². Bộ chấm vì thế **không thể** bắt được lỗi ấy — nó tính
    # lại cùng một đại lượng sai. Một bộ chấm chép luật của thứ nó chấm thì nó
    # chỉ chấm được lỗi gõ nhầm.
    try:
        c2 = M.cos_sq_giua(a, b)
    except Exception as e:  # noqa: BLE001
        return f"không đo được góc: {e}"
    if khai is not None and c2 != khai:
        return f"{_LECH}: chương trình khai cos² = {khai}, hình cho {c2}"
    if mong is not None and c2 != mong:
        return f"{_LECH}: cos² = {c2}, đề mong {mong}"
    return None


def check_volume(snapshot: dict, ob) -> str | None:
    """Thể tích — MỘT checker cho cả đa diện lẫn ba khối cong.

    ─── LỖ NÓ BỊT (`VOLUME_VERIFICATION_BRIDGE`, 2026-09-03) ───────────────

    `CURVED_OBLIGATION_COVERAGE_BRIDGE` nới `volume` sang `curved_solid` ở
    **cổng phủ**; hàm này vẫn đòi `Polyhedron`. Đúng MỘT dòng lệch giữa hai
    thẩm quyền, và nó đủ để hệ tính xong rồi từ chối phục vụ chính con số nó
    vừa tính:

        ball_1 (probe §18)   executable True · servable False
                             engine ra R = 6, V = 288π  ← ĐÚNG ĐÁP SỐ
                             postcondition_violated: ['cần một `solid`']

    ⚠️ Lỗi này là hậu duệ trực tiếp của `RADIUS_VERIFICATION_BRIDGE`: wave ấy
    đóng đúng chỗ hụt này cho `radius` rồi **không soát dòng `volume`** mà wave
    trước đó vừa nới. Sửa hàng đang nhìn, không soát bảng. Cổng chống tái phát
    nay là `test_measure_checker_subject_drift.py`, và nó soát cả bảng.

    ─── VÌ SAO KHÔNG CÓ `check_ball_volume` / `check_cylinder_volume` ──────

    Hình nào là **dữ liệu** (`curved_kind`), và ba công thức `4/3·πR³`, `πr²h`,
    `1/3·πr²h` đã có chủ: bảng `KHOI_CONG`. Chép chúng vào đây là dựng thẩm
    quyền toán học thứ hai — thứ kho này đã đi dọn ba lần (`volume_polyhedron`,
    `cos_sq_giua`, `area_polygon`). Điều phối nằm ở `geometry_exec.volume_of`,
    **dùng chung với đường chạy**, nên hai đường không thể biết hai tập kiểu
    khác nhau lần nữa.

    ─── VÌ SAO KHÔNG CÒN `Fraction(w)` ────────────────────────────────────

    Bản trước ép nhân chứng về `Fraction`. Thể tích khối cong là `288π` — một
    `Radical`, và `Fraction(Radical)` ném. Nghĩa là ngay cả khi kiểu chủ thể đã
    được nới, dòng ấy vẫn giết mọi ca cong. Giữ nguyên `ExactNumber` như
    `check_radius` đã làm; phép so đi trong miền chính xác, không qua float.
    """
    from ..geometry.curved import CurvedSolid

    sol = _lay(snapshot, ob.container)
    if not isinstance(sol, (Polyhedron, CurvedSolid)):
        return "cần một `solid` hoặc một `curved_solid`"
    w = _lay(snapshot, ob.witness)
    khai = w if _la_so(w) else None
    mong = _so(ob.params.get("value"))
    if mong is None and khai is None:
        return None  # không khai giá trị ⇒ chỉ kiểm được cấu trúc, mức yếu
    # MỘT nguồn sự thật, dùng chung với phép `measure` của IR: hai bản rời nhau
    # sẽ lệch, và lệch CÂM vì cả hai đều "chạy ra một con số". Đa diện thì phân
    # rã quạt từ đỉnh đầu (`abs` nên không phụ thuộc hướng khai mặt); khối cong
    # thì tra bảng `KHOI_CONG`. Tầng này không biết cái nào là cái nào.
    from .geometry_exec import volume_of

    tong = volume_of(sol)
    if khai is not None and tong != khai:
        return f"{_LECH}: chương trình khai V = {display(khai)}, khối cho V = {display(tong)}"
    if mong is not None and tong != mong:
        return f"{_LECH}: V = {display(tong)}, đề mong {display(mong)}"
    return None


def check_area(snapshot: dict, ob) -> str | None:
    """Diện tích một hình PHẲNG — đa giác · thiết diện · hình tròn.

    ─── LỖ NÓ BỊT (2026-09-04, `ANALYZE_OBLIGATION_SURFACE_COMPLETION`) ────

    `area` đã là một **lượng đo** từ Phase 1 nhưng chưa bao giờ là một **nghĩa
    vụ**, nên `analyze_contract` loại im lặng mọi đề hỏi diện tích (dòng 489).
    Đo trên pool V3: 8 lượt dùng `area`, và **14/18 ca dương** mang ít nhất một
    nghĩa vụ bị loại như thế — phép đo hỏng vì một lý do không liên quan gì tới
    năng lực hình học.

    ─── MỘT CỬA, DÙNG CHUNG VỚI ĐƯỜNG CHẠY ────────────────────────────────

    Gọi `geometry_exec.area_of` — đúng hàm mà `measure` của IR gọi. Viết lại
    phép phân phối ba kiểu ở đây là dựng bản sao thứ hai của một luật, và
    `check_volume` đã trả giá cho đúng lỗi ấy với `curved_solid`.

    Ba kiểu chủ thể **không** liệt kê tay: `kieu_chu_the_nghia_vu("area")` dẫn
    chúng từ `BANG_PHEP_DO`, nên mở `area` cho một kiểu mới là checker tự nhận.
    """
    from .geometry_exec import area_of, la_hinh_phang

    x = _lay(snapshot, ob.container)
    if not la_hinh_phang(x):
        return "cần một hình PHẲNG — đa giác, thiết diện, hoặc đường tròn"
    w = _lay(snapshot, ob.witness)
    khai = w if _la_so(w) else None
    mong = _so(ob.params.get("value"))
    if mong is None and khai is None:
        return None  # không khai giá trị ⇒ chỉ kiểm được cấu trúc, mức yếu
    s = area_of(x)
    if khai is not None and s != khai:
        return f"{_LECH}: chương trình khai S = {display(khai)}, hình cho S = {display(s)}"
    if mong is not None and s != mong:
        return f"{_LECH}: S = {display(s)}, đề mong {display(mong)}"
    return None


def check_lateral_area(snapshot: dict, ob) -> str | None:
    """Diện tích MẶT CONG — mặt cầu · xung quanh trụ · xung quanh nón.

    Cùng lỗ với `check_area`: pool V3 dùng `lateral_area` 6 lượt và cả 6 đều
    rơi vào nhóm bị loại im lặng.

    ⚠️ **KHÔNG phải diện tích TOÀN PHẦN**, và nghĩa hẹp ấy kế thừa nguyên vẹn
    từ `curved.dien_tich_mat_cong`: `S_tp` của nón có hai căn thức khác nhau và
    miền số cố ý từ chối tổng ấy. Nghĩa vụ **không được** rộng hơn lượng đo nó
    dựa vào — rộng hơn là hứa một thứ kernel không tính được.

    `area` và `lateral_area` giữ HAI nghĩa riêng: một cái đo hình phẳng, một
    cái đo mặt cong của khối. Gộp chúng sẽ làm *"diện tích đáy"* và *"diện tích
    xung quanh"* thành cùng một câu hỏi.
    """
    from ..geometry.curved import CurvedSolid
    from .geometry_exec import lateral_area_of

    x = _lay(snapshot, ob.container)
    if not isinstance(x, CurvedSolid):
        return "cần một `curved_solid` — diện tích mặt cong không định nghĩa " \
               "cho hình phẳng hay khối đa diện"
    w = _lay(snapshot, ob.witness)
    khai = w if _la_so(w) else None
    mong = _so(ob.params.get("value"))
    if mong is None and khai is None:
        return None
    s = lateral_area_of(x)
    if khai is not None and s != khai:
        return f"{_LECH}: chương trình khai S = {display(khai)}, khối cho S = {display(s)}"
    if mong is not None and s != mong:
        return f"{_LECH}: S = {display(s)}, đề mong {display(mong)}"
    return None


def check_section_matches(snapshot: dict, ob) -> str | None:
    """THIẾT DIỆN — dựng lại từ `khối + mặt phẳng` rồi so CHU TRÌNH.

    ─── VÌ SAO KHÔNG DÙNG `coplanar` NỮA ───────────────────────────────────

    `coplanar` trên một thiết diện gần như **luôn đúng**: mọi đỉnh của nó sinh
    ra từ giao với đúng một mặt phẳng, nên chúng đồng phẳng theo định nghĩa.
    Một chương trình trả ba đỉnh của thiết diện thật và bỏ đỉnh thứ tư vẫn
    "đồng phẳng" — cổng xanh, hình sai. Nghĩa vụ này hỏi câu mạnh hơn: *"đa
    giác ấy có ĐÚNG LÀ thiết diện của khối này với mặt phẳng này không"*.

    ─── KHỐI VÀ MẶT PHẲNG LẤY TỪ ĐÂU ──────────────────────────────────────

    Từ **`ob.params`**, tức từ phía ĐỀ, không từ câu lệnh của chương trình.
    Lấy từ chương trình thì checker đang hỏi *"cắt cái mà anh đã cắt có ra cái
    anh đã ra không"* — một tautology, và ca "cắt nhầm mặt phẳng" sẽ không bao
    giờ bị bắt.

    Thiếu `solid`/`plane` ⇒ trả `None` (mức yếu), không bịa: một nghĩa vụ khai
    thiếu là chuyện của C₁a, không phải chỗ này kết tội.
    """
    from ..geometry.section import cross_section, same_section_cycle
    from ..geometry.exact import GeometryError

    c = _lay(snapshot, ob.container)
    poly = list(c.polygon) if isinstance(c, Section) else \
        (list(c) if isinstance(c, (list, tuple)) else None)
    if poly is None or not all(isinstance(p, Vec3) for p in poly):
        return "cần một `section` (hoặc dãy điểm) làm chủ thể"

    sol = _lay(snapshot, ob.params.get("solid"))
    pl = _lay(snapshot, ob.params.get("plane"))
    if sol is None and pl is None:
        return None
    if not isinstance(sol, Polyhedron):
        return "nghĩa vụ trỏ `solid` không phải một KHỐI"
    if not isinstance(pl, Plane3):
        return "nghĩa vụ trỏ `plane` không phải một MẶT PHẲNG"

    try:
        chuan = cross_section(sol, pl)
    except GeometryError as e:
        # Đề bảo cắt, kernel bảo không cắt được ⇒ nói đúng mã suy biến. Nuốt
        # nó thành "không khớp" là giấu đi lời chẩn đoán hữu ích nhất.
        return f"mặt phẳng của nghĩa vụ không cắt được khối: {e.code}"

    if same_section_cycle(poly, chuan.polygon):
        return None
    return (
        f"{_LECH}: thiết diện chương trình có {len(poly)} đỉnh, thiết diện "
        f"dựng lại từ khối và mặt phẳng có {len(chuan.polygon)} đỉnh"
        if len(poly) != len(chuan.polygon) else
        f"{_LECH}: cùng số đỉnh nhưng KHÔNG cùng một đa giác — chu trình khác"
    )


GEOMETRY_CHECKERS = {
    "point_on_line": check_point_on_line,
    "point_on_plane": check_point_on_plane,
    "parallel": check_parallel,
    "perpendicular": check_perpendicular,
    "coplanar": check_coplanar,
    "section_matches": check_section_matches,
    "distance": check_distance,
    "angle": check_angle,
    "volume": check_volume,
    # 2026-09-03 · `RADIUS_VERIFICATION_BRIDGE`. Đăng ký ở ĐÂY là đủ:
    # `postconditions.CHECKERS` dẫn xuất bằng `**GEOMETRY_CHECKERS`, nên không
    # có bảng thứ hai để quên.
    "radius": check_radius,
    # 2026-09-04 · `ANALYZE_OBLIGATION_SURFACE_COMPLETION`. Mở nghĩa vụ mà
    # KHÔNG thêm checker chính là lỗ `RADIUS_OBLIGATION_COVERAGE` đã mắc: hệ
    # tính đúng rồi `servable=False`. Nên hai dòng này đi cùng commit với hai
    # dòng ở `NGHIA_VU_DO`.
    "area": check_area,
    "lateral_area": check_lateral_area,
}


#: ─── CHỖ BỘ KIỂM **KHÔNG** VỚI TỚI, DÙ HỢP ĐỒNG CHO PHÉP ─────────────────
#:
#: `VERIFICATION_CAPABILITY_IDENTITY`, 2026-09-03.
#:
#: ⚠️ Đây **KHÔNG** phải bảng "lượng đo nào nhận kiểu nào" — câu ấy chỉ
#: `measure_contract.BANG_PHEP_DO` được trả lời, và nó vẫn là thẩm quyền duy
#: nhất (`MEASURE_SUBJECT_COMPATIBILITY_AUTHORITIES = 1`). Bảng này trả lời một
#: câu KHÁC, và là câu chưa ai viết ra ở đâu:
#:
#:     hợp đồng CHO PHÉP chủ thể ấy · bộ kiểm có CHỨNG THỰC được nó không?
#:
#: Hai câu ấy đã lệch nhau hai lần trong bốn ngày (`radius`, rồi `volume`), và
#: cả hai lần đều lệch CÂM. Năng lực kiểm chứng vì thế là **hiệu**:
#:
#:     kiểm được = `kieu_chu_the_nghia_vu(nv)` − {kiểu khai ở đây}
#:
#: Viết dưới dạng hiệu chứ không dưới dạng danh sách kiểu-kiểm-được là có chủ
#: đích: một danh sách sẽ là **bản sao thứ hai** của `BANG_PHEP_DO`, và bản sao
#: chính là con bug này. Ở đây chỉ khai phần TRỪ ĐI, tức đúng phần thông tin
#: chưa nằm ở đâu cả.
#:
#: ─── NỢ CHỈ ĐƯỢC NGẮN ĐI ────────────────────────────────────────────────
#:
#: Mỗi mục phải nêu LÝ DO, và `test_measure_checker_subject_drift.py` bắt nó
#: vẫn còn THẬT: vá xong mà quên xoá mục ⇒ ĐỎ, bắt xoá. Thêm một mục là tự khai
#: vừa thu hẹp năng lực kiểm chứng của sản phẩm — và nay việc đó **làm đổi
#: `stable_capability_hash`**, nên nó không thể lặng lẽ.
KHONG_KIEM_DUOC: dict[tuple[str, str], str] = {
    ("angle", "vector3"): (
        "`angle` hiện thực hoá bởi HAI lượng đo: `angle_cos_sq` (line3|plane3, "
        "trả cos²) và `angle_cos` (vector3, trả cos CÓ DẤU). `check_angle` chỉ "
        "tính lại cos² (`measure.cos_sq_giua`, không có nhánh Vec3×Vec3), nên "
        "nó không chứng thực được nhân chứng của `angle_cos`; ô giá trị mong "
        "đợi của nghĩa vụ cũng chỉ có `cos_sq`. Đóng khoảng này đòi một quyết "
        "định NGỮ NGHĨA — nghĩa vụ `angle` trỏ lượng đo nào, và đáp số CÓ DẤU "
        "viết vào đâu — chứ không phải một phép nới kiểu."),
}


def kieu_kiem_chung_duoc(nghia_vu: str) -> frozenset[str]:
    """Kiểu chủ thể mà bộ kiểm của nghĩa vụ ĐO này **thật sự chứng thực được**.

    DẪN XUẤT: `BANG_PHEP_DO` (qua `kieu_chu_the_nghia_vu`) trừ đi phần khai ở
    `KHONG_KIEM_DUOC`. Không có danh sách viết tay nào để trôi.

    Đây là thứ `runtime_identity.capability_fingerprint` băm, và là lý do hai
    container — một cái `check_volume` bác `curved_solid`, một cái chứng thực
    được nó — nay có **hai** vân tay năng lực khác nhau.
    """
    from .measure_contract import kieu_chu_the_nghia_vu

    return frozenset(
        k for k in kieu_chu_the_nghia_vu(nghia_vu)
        if (nghia_vu, k) not in KHONG_KIEM_DUOC)
