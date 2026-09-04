# -*- coding: utf-8 -*-
"""Cầu nối IR ↔ geometry kernel — nơi ranh giới R0 được thực thi ở miền hình học.

VÌ SAO TÁCH KHỎI `interpreter.py`: interpreter đã dài và sở hữu **mô hình thực
thi** (bước, trace, ngân sách). File này sở hữu **phép dịch**: một câu lệnh dựng
trong IR → một lời gọi kernel → một giá trị hình học trong bộ nhớ. Trộn hai
trách nhiệm thì mỗi lần thêm một phép dựng lại phải đọc lại cả vòng thực thi.

LUẬT CỐT LÕI, và là chỗ dễ vỡ nhất:

> Hàm ở đây nhận **TÊN** đối tượng, đọc chúng từ bộ nhớ, rồi gọi kernel.
> Không hàm nào nhận **toạ độ kết quả** từ IR.

Nếu một ngày có ai thêm một trường `result` vào `ConstructPointStmt` để "cho
nhanh", thì LLM sở hữu kết quả và toàn bộ luận điểm của đề tài mất hiệu lực.
`test_r0_geometry.py` khoá điều đó lại.

FAIL-CLOSED: mọi `GeometryError` của kernel đi thẳng lên trên, không nuốt. Kernel
đã phân biệt *song song nên không giao* với *nằm trong nên giao vô số điểm* —
nuốt lỗi ở đây là xoá mất phân biệt ấy.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Any

from ..geometry import GeometryError, Line3, Plane3, Point3, Vec3
from ..geometry import kernel as K
from ..geometry import measure as M
from ..geometry.radical import (
    ExactNumber,
    Radical,
    RadicalDomainError,
    sqrt_rational,
)
from ..geometry import curved as CV
from ..geometry.curved import Circle3, CurvedSolid
from ..geometry.section import Polyhedron, Section, cross_section

#: Đối tượng lạ trong bộ nhớ khi phép dựng cần một kiểu cụ thể.
ERR_SAI_LOAI = "GEOMETRY_OPERAND_TYPE"
#: Tên không có trong bộ nhớ.
ERR_KHONG_KHAI = "GEOMETRY_UNDECLARED"
#: Đại lượng đúng nhưng VÔ TỈ — không phải lỗi của chương trình, là giới hạn
#: biểu diễn. Mã riêng để phân loại thất bại không nhầm nó với "tính sai".
ERR_VO_TI = "GEOMETRY_IRRATIONAL_RESULT"


def _lay(mem: dict[str, Any], ten: str, loai: type, mo_ta: str) -> Any:
    """Đọc một đối tượng hình học theo TÊN, fail-closed cả sự tồn tại lẫn kiểu."""
    if ten not in mem:
        raise GeometryError(
            ERR_KHONG_KHAI, f"{mo_ta} '{ten}' chưa khai trong memory_declarations"
        )
    v = mem[ten]
    if not isinstance(v, loai):
        raise GeometryError(
            ERR_SAI_LOAI,
            f"{mo_ta} '{ten}' là {type(v).__name__}, cần {loai.__name__}",
        )
    return v


def _lay_dai_luong(mem: dict[str, Any], ten: str, mo_ta: str) -> Any:
    """Đọc một VÔ HƯỚNG chính xác theo TÊN. Song sinh của `_lay` cho đại lượng.

    Tách khỏi `_lay` vì `_lay` kiểm bằng `isinstance` một lớp DUY NHẤT, còn
    miền số chính xác là một hợp (`Fraction | Radical | int`). Nhét một `tuple`
    kiểu vào `_lay` sẽ làm thông điệp lỗi của nó nói *"cần tuple"* — vô nghĩa
    với người đọc.
    """
    from ..geometry.radical import is_exact_number

    if ten not in mem:
        raise GeometryError(
            ERR_KHONG_KHAI, f"{mo_ta} '{ten}' chưa khai trong memory_declarations")
    v = mem[ten]
    if not is_exact_number(v):
        raise GeometryError(
            ERR_SAI_LOAI,
            f"{mo_ta} '{ten}' là {type(v).__name__}, cần một SỐ chính xác")
    return v


# ── dựng giá trị hình học từ `initial_value` của IR ───────────────────────
def build_initial(mtype: str, raw: Any, ten: str) -> Any:
    """`initial_value` dạng JSON → đối tượng hình học. Sai hình dạng thì NÉM.

    Đây là **dữ kiện ĐỀ CHO** — điểm `A(0,0,0)`, khối chóp với bảng mặt. LLM
    được phép khai những thứ này vì chúng có trong đề bài; nó KHÔNG được khai
    thứ phải tính ra.
    """
    # Ô TRỐNG hợp lệ: đối tượng sẽ được DỰNG bởi một câu lệnh phía sau.
    #
    # Không có nhánh này thì khai `{"name":"H","type":"point3","initial_value":
    # null}` sẽ vỡ, và LLM buộc phải điền một toạ độ giả cho chỗ nó chưa biết —
    # tức hợp đồng đang ĐẨY mô hình về phía vi phạm R0. Ô trống không phải một
    # giá trị mặc định bịa ra: nó là "chưa dựng", và mọi phép đọc nó trước khi
    # dựng sẽ gặp `None` rồi hỏng ở kiểm kiểu, đúng chỗ.
    if raw is None:
        return None
    try:
        if mtype == "point3" or mtype == "vector3":
            return Vec3.of(*raw)
        if mtype == "line3":
            return Line3.through(Vec3.of(*raw["through"][0]), Vec3.of(*raw["through"][1]))
        if mtype == "plane3":
            p = [Vec3.of(*t) for t in raw["through"]]
            return Plane3.through(*p[:3])
        if mtype == "polygon3":
            return tuple(Vec3.of(*t) for t in raw)
        if mtype == "solid":
            return Polyhedron(
                vertices=tuple(Vec3.of(*t) for t in raw["vertices"]),
                faces=tuple(tuple(f) for f in raw["faces"]),
            )
    except GeometryError:
        raise
    except Exception as e:  # noqa: BLE001 — hình dạng sai là lỗi hợp đồng
        raise GeometryError(
            ERR_SAI_LOAI, f"'{ten}' ({mtype}) khai sai hình dạng: {e}"
        ) from e
    raise GeometryError(ERR_SAI_LOAI, f"'{ten}': kiểu {mtype} không phải hình học")


GEOMETRY_TYPES = frozenset(
    {"point3", "vector3", "line3", "plane3", "polygon3", "solid", "section",
     "circle3", "curved_solid"}
)

#: Kiểu KHAI của một đại lượng đo được. `measure` trả `Fraction`, và IR khai nó
#: bằng kiểu số thường — nên nhận diện phải xét CẢ giá trị lẫn kiểu khai.
KIEU_DAI_LUONG = ("float", "int")


def la_doi_tuong_hinh_hoc(gt: Any) -> bool:
    """Giá trị này có phải một **đối tượng hình học** không?

    ─── VÌ SAO VỊ TỪ NÀY Ở ĐÂY, KHÔNG Ở TẦNG TRÌNH BÀY ──────────────────────

    Hai nơi cần nó, và chúng nằm ở hai tầng **không được biết tới nhau**:

      · `simulation_state.build_scene` — nhặt đối tượng để chiếu ra cảnh
      · `learner_surface` — hỏi *"biến này có hiện trên màn hình không?"*

    `learner_surface` là một CỔNG, nên nó không được phụ thuộc vào tầng mô
    phỏng (`test_KHONG_module_nao_o_TANG_DUOI_nhap_lop_nay` giữ luật ấy). Nhưng
    nếu mỗi bên tự viết một chuỗi `isinstance` thì có hai nguồn sự thật, và
    chúng sẽ trôi khỏi nhau đúng vào ngày thêm một kiểu hình học mới: cổng bảo
    "có trên hình", cảnh thì không vẽ. Đưa vị từ xuống **tầng kernel** — nơi
    kiểu dữ liệu được định nghĩa — là chỗ duy nhất cả hai cùng nhìn được mà
    không đảo chiều phụ thuộc.

    Xét **GIÁ TRỊ**, không xét kiểu khai: `construct_point` có thể ghi một `Vec3`
    vào một biến khai kiểu khác, và cái quyết định vẽ được hay không là thứ thật
    sự nằm trong bộ nhớ.
    """
    if isinstance(gt, (Vec3, Line3, Plane3, Polyhedron, Section,
                       Circle3, CurvedSolid)):
        return True
    # `polygon3` sống dưới dạng tuple các đỉnh — không có lớp riêng.
    return bool(isinstance(gt, tuple) and gt
                and all(isinstance(v, Vec3) for v in gt))


def la_dai_luong_do(gt: Any, kieu_khai: str | None) -> bool:
    """Giá trị này có phải một **đại lượng đo được** không?

    Không vẽ được, nhưng phải HIỆN LÊN: nó là câu trả lời của bài. Bỏ nó khỏi
    màn hình thì mô phỏng chạy xong mà học sinh không thấy đáp số.

    `Radical` cũng là đại lượng đo (2026-08-31). Quên nhánh này thì `d = 3√2/5`
    tính đúng, chấm đúng, rồi **không hiện lên màn hình** — đúng loại lỗi mà
    `learner_surface` sinh ra để chặn, chỉ khác là lần này do miền số mở rộng
    mà bộ lọc không mở theo.
    """
    return isinstance(gt, (Fraction, Radical)) and kieu_khai in KIEU_DAI_LUONG


def chuan_hoa_dai_luong(kieu_khai: str | None, raw: Any, *,
                        mien_hinh_hoc: bool) -> Any:
    """`initial_value` VÔ HƯỚNG → miền số chính xác. Đọc không được ⇒ GIỮ NGUYÊN.

    ─── LỖ NÓ BỊT (`SCALAR_FACT_VISIBILITY`, 2026-09-04) ────────────────────

    Interpreter nạp `initial_value` **nguyên văn** cho mọi kiểu không-hình-học,
    nên `IA = 6` nằm trong bộ nhớ dưới dạng `str "6"`. Cả hai người đọc miền
    hình học đều hỏi `la_dai_luong_do`, và nó chỉ nhận `Fraction | Radical`:

        build_scene       bỏ qua ⇒ đại lượng KHÔNG lên cảnh
        learner_surface   thấy "không hiện" ⇒ từ chối phục vụ

    Đo được: `str "6"`, `int 6`, `float 6.0` đều trả `False`. Nghĩa là **không
    một dữ kiện đề vô hướng nào** có thể qua cổng, bất kể mô hình viết gì — và
    cổng ấy nằm ngoài vòng sửa nên mô hình cũng không được biết. `ball_1` của
    probe V2: toán đúng tuyệt đối, `R = 6`, `V = 288π` đã kiểm, `servable=False`.

    ─── VÌ SAO CHUẨN HOÁ Ở ĐÂY, KHÔNG DẠY CỔNG ĐỌC CHUỖI ───────────────────

    Cổng **đang nói thật**: giá trị ấy thật sự không có trên cảnh, vì
    `build_scene` dùng CHÍNH vị từ đó để quyết cái gì thành `quantity`. Dạy
    riêng `learner_surface` chấp nhận một chuỗi thô sẽ cho cổng xanh trong khi
    cảnh vẫn trống — đúng cái hình lỗi mà `la_doi_tuong_hinh_hoc` viết ra để
    tránh: *"cổng bảo 'có trên hình', cảnh thì không vẽ"*.

    Chuẩn hoá MỘT lần ở biên ngữ nghĩa/thực thi thì hai người đọc — vốn đã dùng
    chung một vị từ — cùng thấy sự thật, và không ai phải học cách diễn giải
    lại chuỗi thô. Một nguồn sự thật, hai người đọc, không đổi.

    ─── BA RANH GIỚI ──────────────────────────────────────────────────────

    **① KIỂU KHAI KHÔNG ĐỔI.** Đây là chuẩn hoá *biểu diễn runtime*, không phải
    đổi kiểu ngữ nghĩa: `decl.type` vẫn là `float`. Cùng nguyên tắc đã dựng cho
    `point3` ↔ `vector3` — cùng `Vec3` ở runtime, hai kiểu khai khác nhau.

    **② KHÔNG NỚI VĂN PHẠM.** Dùng đúng `parse_exact` đang có, không viết thêm
    một bộ đọc số thứ hai. Thứ nó nhận hôm nay là thứ nhận được, không hơn.

    **③ ĐỌC KHÔNG ĐƯỢC THÌ GIỮ NGUYÊN — FAIL CLOSED.** Một chuỗi vô nghĩa vẫn
    nằm im dưới dạng chuỗi, vẫn vô hình, và `learner_surface` vẫn từ chối. Ép
    nó thành 0 là biến "không đọc được" thành một con số — đúng lỗi mà
    `parse_exact` đã ghi rõ là không được mắc.

    ─── VÌ SAO PHẢI GIỚI HẠN Ở MIỀN HÌNH HỌC ──────────────────────────────

    `KIEU_DAI_LUONG` là `("float", "int")`, và IR **dùng chung** cho cả miền
    Tin học, nơi một `int` là **chỉ số** hoặc **biến đếm**. Bản đầu chuẩn hoá
    mọi vô hướng và 14 ca Tin học đỏ ngay:

        INDEX_OUT_OF_RANGE: chars[Fraction(0, 1)] ngoài [0, 5)

    Một chỉ số hữu tỉ không phải một chỉ số. Toàn bộ lý do bản vá này tồn tại
    — `la_dai_luong_do`, `build_scene` chiếu ra `quantity` — là **của miền hình
    học**; nên phạm vi của nó cũng phải là miền ấy, không rộng hơn một chữ.
    """
    from ..geometry.radical import parse_exact

    if not mien_hinh_hoc or kieu_khai not in KIEU_DAI_LUONG or raw is None:
        return raw
    # `bool` là subclass của `int`; một cờ đúng/sai trôi vào chỗ một số đo là
    # loại lỗi im lặng nhất (cùng lý do `is_exact_number` chặn nó).
    if isinstance(raw, bool) or isinstance(raw, (Fraction, Radical)):
        return raw
    gt = parse_exact(raw)
    return raw if gt is None else gt


def volume_polyhedron(sol: Polyhedron) -> Fraction:
    """Thể tích một khối — phân rã quạt từ đỉnh đầu qua MỌI mặt.

    MỘT nguồn sự thật, dùng chung cho `measure` (phép đo của IR) và
    `check_volume` (cổng C₂). Trước Wave 2, phép này nằm inline trong
    `geometry_obligations.check_volume`; để nguyên đó rồi viết bản thứ hai ở
    đây là đúng cái bẫy `ARCHITECTURE_MAP §8` gọi tên — hai bản sẽ lệch, và
    lệch câm vì cả hai đều "chạy ra một con số".

    `abs` trong `volume_tetrahedron` khiến kết quả không phụ thuộc chiều khai
    mặt, nên bảng `faces` viết thuận hay nghịch kim đồng hồ đều ra cùng số.
    """
    tong = Fraction(0)
    tam = sol.vertices[0]
    for f in sol.faces:
        for i in range(1, len(f) - 1):
            tong += M.volume_tetrahedron(
                tam, sol.vertices[f[0]], sol.vertices[f[i]], sol.vertices[f[i + 1]]
            )
    return tong


def volume_of(x: Any) -> ExactNumber:
    """Thể tích — MỘT cửa điều phối cho cả HAI họ khối.

    ─── VÌ SAO HÀM NÀY TỒN TẠI (2026-09-03, `VOLUME_VERIFICATION_BRIDGE`) ──

    Phép điều phối *"đa diện hay khối cong"* từng nằm inline trong `_do`, và
    `check_volume` thì **không có nó** — nó `isinstance(sol, Polyhedron)` rồi
    thôi. Hệ quả đo được: `ball_1` của probe §18 tính đúng `V = 288π` rồi bị
    chính `postconditions` từ chối phục vụ, vì đường CHẤM không biết một họ
    khối mà đường CHẠY đã biết từ Phase 2.

    Viết lại nhánh ấy lần thứ hai trong checker là dựng đúng bản sao mà
    `cos_sq_giua` và `volume_polyhedron` đã phải đi dọn — hai bản của một luật,
    và chúng lệch CÂM vì cả hai đều "chạy ra một con số". Nên: một hàm, hai
    người đọc.

    ─── RANH GIỚI ─────────────────────────────────────────────────────────

    Hàm này **không** kiểm kiểu — người gọi kiểm, vì mỗi bên nói một thứ tiếng
    khác nhau khi từ chối (`_do` ném `GeometryError` kèm tên biến của IR;
    checker trả một câu tiếng Việt cho học sinh). Trộn hai cách từ chối vào đây
    là bắt một trong hai bên dịch ngược.

    Và nó **không** biết `4/3·π·R³` là của hình nào: `KHOI_CONG` giữ ba công
    thức ấy, `CV.the_tich` tra bảng. Ở đây không có `if ball / cylinder / cone`,
    và sự vắng mặt đó là luật (`CHECK_VOLUME_FAMILY_DISPATCH = 0`).
    """
    if isinstance(x, CurvedSolid):
        return CV.the_tich(x)
    return volume_polyhedron(x)


# ── phép ĐO: engine trả SỐ HỮU TỈ, IR chỉ nói đo cái gì ───────────────────
def _do(node: Any, mem: dict[str, Any]) -> ExactNumber:
    """`measure` → số CHÍNH XÁC. Không có float ở đâu trong đường này.

    `distance` trả **bình phương khoảng cách** hay khoảng cách? — Trả KHOẢNG
    CÁCH. Lý do: `oracle_result` của tập DEV khai `distance: "2"` (một khoảng
    cách thật), còn `angle` khai `cos²`. Hai đại lượng, hai quy ước, và cả hai
    đều được nói thẳng ra — cái nguy hiểm là một quy ước ngầm mà hai phía hiểu
    khác nhau.

    ─── 2026-08-31: TỪ CHỐI VÔ TỈ ĐÃ BIẾN MẤT ──────────────────────────────

    Bản trước trả `Fraction` và NÉM `GEOMETRY_IRRATIONAL_RESULT` khi căn không
    hữu tỉ — tức từ chối phần lớn bài khoảng cách của hình học THPT, đúng lúc
    phép tính đã xong và chỉ còn thiếu một cách VIẾT kết quả. Vấn đề chưa bao
    giờ là tính được hay không; nó là biểu diễn.

    Nay trả `ExactNumber` (`Fraction | Radical`), và `sqrt_rational` **không có
    nhánh thất bại**: mọi `√(p/q)` với `p/q ≥ 0` đều viết được dưới dạng `a·√b`.
    Vẫn KHÔNG làm tròn — một `√2` lặng lẽ thành `1.414…` là đúng cách sai số
    float quay lại qua cửa sau, sau khi cả kernel đã dựng bằng `Fraction` để
    tránh nó.
    """
    q = node.quantity
    a = mem.get(node.of)
    b = mem.get(node.wrt) if node.wrt else None

    if q == "volume":
        # Một tên, hai họ khối. Điều phối theo LỚP runtime ở `volume_of` —
        # dùng CHUNG với `check_volume`, nên đường chạy và đường chấm không thể
        # biết hai tập kiểu khác nhau (đó đúng là lỗi `ball_1` của probe §18).
        if not isinstance(a, (Polyhedron, CurvedSolid)):
            raise GeometryError(ERR_SAI_LOAI, f"'{node.of}' phải là một khối")
        return volume_of(a)

    if q == "radius":
        if not isinstance(a, (Circle3, CurvedSolid)):
            raise GeometryError(
                ERR_SAI_LOAI,
                f"'{node.of}' phải là một đường tròn hoặc một khối cong")
        return CV.ban_kinh(a)

    if q == "lateral_area":
        if not isinstance(a, CurvedSolid):
            raise GeometryError(
                ERR_SAI_LOAI,
                f"'{node.of}' phải là một khối cong — diện tích mặt cong không "
                "định nghĩa cho hình phẳng hay khối đa diện")
        return CV.dien_tich_mat_cong(a)

    if q == "area":
        # HAI kiểu phẳng, MỘT thẩm quyền toán học. `Section` chỉ khác ở chỗ
        # đa giác nằm trong `.polygon`, nên nó đi qua `area_section` — một
        # adapter ba dòng, không phải một thuật toán thứ hai (`§17`).
        #
        # Thứ tự nhánh: `Section` trước, vì `polygon3` ở runtime là một tuple
        # trần và một phép thử `Sequence` sẽ nuốt luôn `Section` nếu nó đứng
        # sau.
        if isinstance(a, Circle3):
            return CV.dien_tich_hinh_tron(a)
        if isinstance(a, Section):
            return M.area_section(a)
        if isinstance(a, tuple) and a and all(isinstance(p, Vec3) for p in a):
            return M.area_polygon(a)
        raise GeometryError(
            ERR_SAI_LOAI,
            f"'{node.of}' phải là một đa giác hoặc một thiết diện — diện tích "
            "chỉ đo được trên hình PHẲNG đã dựng")

    if b is None:
        raise GeometryError(
            ERR_SAI_LOAI, f"đo '{q}' cần hai đối tượng, thiếu `wrt`"
        )

    if q == "angle_cos_sq":
        # MỘT THẨM QUYỀN. Nhánh `isinstance` từng nằm ở đây và một bản SAO của
        # nó nằm ở `geometry_obligations.check_angle` — hai bản của cùng một
        # luật, và cả hai cùng gọi `sin_sq_line_plane` cho cặp (đường, mặt) rồi
        # cùng gọi kết quả là cos². Bộ chấm không bắt được vì nó tính cùng một
        # đại lượng sai. Xem `measure.cos_sq_giua`.
        try:
            return M.cos_sq_giua(a, b)
        except GeometryError as e:
            raise GeometryError(ERR_SAI_LOAI, str(e)) from e

    if q == "angle_cos":
        # CHỈ vectơ. Không có nhánh `Line3` ở đây, và sự vắng mặt ấy là luật:
        # một đường thẳng không có chiều, nên lấy dấu từ nó là để thứ tự hai
        # điểm lúc dựng quyết một mệnh đề toán học.
        #
        # Ở runtime `vector3` và `point3` cùng là `Vec3`, nên tầng này KHÔNG
        # phân biệt được "vectơ" với "điểm" — thẩm quyền ấy nằm ở validator,
        # nơi đọc được `memory_declarations`. Nhánh dưới chỉ là lưới cuối.
        if isinstance(a, Vec3) and isinstance(b, Vec3):
            return M.cos_between_vectors(a, b)
        raise GeometryError(
            ERR_SAI_LOAI,
            "`angle_cos` cần HAI VECTƠ có hướng. Đường thẳng không có chiều — "
            "dựng vectơ bằng `vector_from_points`, hoặc dùng `angle_cos_sq`.",
        )

    # q == "distance"
    if isinstance(a, Vec3) and isinstance(b, Plane3):
        d2 = M.distance_sq_point_plane(a, b)
    elif isinstance(a, Plane3) and isinstance(b, Vec3):
        d2 = M.distance_sq_point_plane(b, a)
    elif isinstance(a, Vec3) and isinstance(b, Line3):
        d2 = M.distance_sq_point_line(a, b)
    elif isinstance(a, Line3) and isinstance(b, Vec3):
        d2 = M.distance_sq_point_line(b, a)
    elif isinstance(a, Vec3) and isinstance(b, Vec3):
        d2 = M.distance_sq(a, b)
    # ── BA CẶP MỞ THÊM 2026-08-30 ────────────────────────────────────────
    #
    # Kernel đã có `distance_sq_skew_lines` và `distance_sq_parallel_lines`
    # từ đầu, nhưng cầu nối này chưa nối — nên `hp_b01_032` chết hai lượt ở
    # Phase 7B với đúng câu *"cặp đối tượng không hợp lệ"*, trong khi phép
    # tính nằm sẵn trong kho. Một năng lực không có cầu nối là một năng lực
    # KHÔNG TỒN TẠI với hệ.
    #
    # `distance_sq_lines` tự phân ba trường hợp (cắt · song song · chéo) chứ
    # không bắt tầng này đoán trước — đoán trước là đặt một kết luận hình học
    # vào chỗ chỉ được phép chuyển tiếp.
    elif isinstance(a, Line3) and isinstance(b, Line3):
        d2 = M.distance_sq_lines(a, b)
    elif isinstance(a, Line3) and isinstance(b, Plane3):
        d2 = M.distance_sq_line_plane(a, b)
    elif isinstance(a, Plane3) and isinstance(b, Line3):
        d2 = M.distance_sq_line_plane(b, a)
    elif isinstance(a, Plane3) and isinstance(b, Plane3):
        d2 = M.distance_sq_planes(a, b)
    else:
        raise GeometryError(
            ERR_SAI_LOAI, "cặp đối tượng không hợp lệ cho khoảng cách"
        )
    try:
        return sqrt_rational(d2)
    except RadicalDomainError as e:
        # Miền số là tầng DƯỚI hình học, nên nó ném lỗi của nó. Dịch sang mã
        # lỗi hình học ở đây — tầng dưới không được biết tên mã lỗi tầng trên.
        #
        # Nhánh này nay gần như không tới được: `d2` là bình phương nên luôn
        # `≥ 0`, và mọi căn của hữu tỉ không âm đều biểu diễn được. Nó còn sống
        # cho đúng MỘT ca thật: toạ độ khổng lồ đẩy căn thức vượt `MAX_RADICAND`.
        # Giữ lại là fail-closed; bỏ đi là để một lượt treo trông giống một lượt
        # chạy chậm.
        raise GeometryError(ERR_VO_TI, str(e)) from e


# ── biểu thức: engine TỰ TÍNH ─────────────────────────────────────────────
def eval_geometry_expr(kind: str, node: Any, mem: dict[str, Any]) -> Any:
    """Một biểu thức hình học → giá trị. Toạ độ do KERNEL sinh, không do IR."""
    if kind == "intersect_line_plane":
        return K.intersect_line_plane(
            _lay(mem, node.line, Line3, "đường thẳng"),
            _lay(mem, node.plane, Plane3, "mặt phẳng"),
        )
    if kind == "intersect_plane_plane":
        return K.intersect_plane_plane(
            _lay(mem, node.plane_a, Plane3, "mặt phẳng"),
            _lay(mem, node.plane_b, Plane3, "mặt phẳng"),
        )
    if kind == "intersect_line_line":
        # Kernel NÉM khi hai đường chéo nhau — và phải ném: trên hình biểu diễn
        # phẳng chúng trông như cắt nhau, nên trả một điểm "gần đúng" là dạy sai.
        return K.intersect_line_line(
            _lay(mem, node.line_a, Line3, "đường thẳng"),
            _lay(mem, node.line_b, Line3, "đường thẳng"),
        )
    if kind == "midpoint":
        return K.midpoint(
            _lay(mem, node.a, Vec3, "điểm"), _lay(mem, node.b, Vec3, "điểm")
        )
    if kind == "translate":
        # `Vec3` cho CẢ HAI toán hạng: ở runtime điểm và vectơ cùng lớp, và
        # phân biệt affine `ĐIỂM + VECTƠ` chỉ tồn tại ở tầng KHAI — nơi
        # validator đọc được `memory_declarations`. Cùng ranh giới mà
        # `angle_cos` đã dựng: kernel là lưới cuối, không phải thẩm quyền.
        return K.translate(
            _lay(mem, node.point, Vec3, "điểm"),
            _lay(mem, node.vector, Vec3, "vectơ"),
        )
    if kind == "divide_segment":
        try:
            t = Fraction(node.ratio)
        except (ValueError, ZeroDivisionError) as e:
            raise GeometryError(
                ERR_SAI_LOAI, f"tỉ lệ '{node.ratio}' không phải phân số hợp lệ"
            ) from e
        return K.divide_segment(
            _lay(mem, node.a, Vec3, "điểm"), _lay(mem, node.b, Vec3, "điểm"), t
        )
    if kind == "measure":
        return _do(node, mem)
    if kind == "project_onto":
        p = _lay(mem, node.point, Vec3, "điểm")
        muc = mem.get(node.target)
        if isinstance(muc, Plane3):
            return K.project_point_onto_plane(p, muc)
        if isinstance(muc, Line3):
            return K.project_point_onto_line(p, muc)
        raise GeometryError(
            ERR_SAI_LOAI,
            f"'{node.target}' phải là mặt phẳng hoặc đường thẳng để chiếu lên",
        )
    if kind == "plane_perpendicular_to_line":
        # Pháp tuyến CHÍNH LÀ phương của đường — không có tự do dư nào để chọn
        # bừa, nên phép này xác định duy nhất. Kernel đã có sẵn từ đầu; đây
        # thuần tuý là bỏ sót ở tầng nối, cùng lớp với `intersect_line_line` và
        # `distance` cặp đường–đường.
        return K.plane_through_point_perpendicular_to(
            _lay(mem, node.point, Vec3, "điểm"),
            _lay(mem, node.line, Line3, "đường thẳng"),
        )

    if kind == "intersect_plane_curved":
        # Trả ĐÚNG `Circle3` như `_CHU_KY` khai, hoặc ném. Mọi ca suy biến do
        # `curved.intersect_plane_curved` từ chối, kèm tên phép dựng đúng —
        # tầng này không được tự chế một nhánh trả `point3`.
        return CV.intersect_plane_curved(
            _lay(mem, node.solid, CurvedSolid, "khối cong"),
            _lay(mem, node.plane, Plane3, "mặt phẳng"),
        )
    if kind == "vector_from_points":
        # Phép TRỪ, không phải đại số vectơ: không cộng, không nhân vô hướng,
        # không tích có hướng. Nó tồn tại để `angle_cos` có một toán hạng KHAI
        # là có hướng — xem `VectorFromPointsExpr`.
        return (_lay(mem, node.to_point, Vec3, "điểm")
                - _lay(mem, node.from_point, Vec3, "điểm"))
    raise GeometryError(ERR_SAI_LOAI, f"biểu thức hình học lạ: {kind}")


# ── câu lệnh dựng: trả (giá trị, mô tả bước) ──────────────────────────────
def exec_construct_point(node: Any, mem: dict[str, Any]) -> tuple[Point3, str]:
    p = eval_geometry_expr(node.expr.kind, node.expr, mem)
    ten = node.label or node.target_var
    return p, f"Dựng điểm {ten} = ({p.x}, {p.y}, {p.z})."


def exec_construct_line(node: Any, mem: dict[str, Any]) -> tuple[Line3, str]:
    a = _lay(mem, node.through_a, Vec3, "điểm")
    b = _lay(mem, node.through_b, Vec3, "điểm")
    ten = node.label or node.target_var
    return Line3.through(a, b), f"Dựng đường thẳng {ten} qua hai điểm đã có."


def exec_construct_plane(node: Any, mem: dict[str, Any]) -> tuple[Plane3, str]:
    """Mặt phẳng qua BA ĐIỂM ĐÃ CÓ. Ba điểm thẳng hàng ⇒ kernel NÉM, không đoán."""
    p = [_lay(mem, t, Vec3, "điểm") for t in node.through]
    ten = node.label or node.target_var
    return Plane3.through(p[0], p[1], p[2]), (
        f"Dựng mặt phẳng {ten} qua ba điểm {', '.join(node.through)}."
    )


def exec_construct_polygon(
    node: Any, mem: dict[str, Any]
) -> tuple[tuple[Vec3, ...], str]:
    """Đa giác từ các ĐỈNH ĐÃ ĐẶT TÊN. Trả tuple các `Vec3` — đúng hình dạng mà
    `polygon3` vốn đã dùng từ Wave 2, nên không tầng nào phía sau phải đổi.

    KIỂM HAI ĐIỀU, và cả hai bằng thứ kernel ĐÃ CÓ (không sửa kernel):

    · **trùng đỉnh** — `A B C A` không phải đa giác, nó là một đường gấp khúc
      khép sớm. Bắt ở đây vì `Polyhedron`/`Section` phía sau sẽ vỡ muộn với một
      thông báo không nói được đỉnh nào lặp.
    · **đồng phẳng** (từ đỉnh thứ tư trở đi) — một "đa giác" bốn đỉnh không đồng
      phẳng KHÔNG phải một hình phẳng. Cho nó qua là dựng một vật không tồn tại,
      rồi renderer sẽ vẽ ra một thứ trông hợp lý mà sai. `predicates.coplanar`
      so bằng ĐÚNG trên `Fraction`, không epsilon.
    """
    from ..geometry import predicates as P

    ten = node.label or node.target_var
    dinh = tuple(_lay(mem, t, Vec3, "đỉnh") for t in node.vertices)

    for i in range(len(dinh)):
        for j in range(i + 1, len(dinh)):
            if P.same_point(dinh[i], dinh[j]):
                raise GeometryError(
                    ERR_SAI_LOAI,
                    f"đa giác '{ten}': đỉnh '{node.vertices[i]}' và "
                    f"'{node.vertices[j]}' TRÙNG NHAU",
                )
    for k in range(3, len(dinh)):
        if not P.coplanar(dinh[0], dinh[1], dinh[2], dinh[k]):
            raise GeometryError(
                ERR_SAI_LOAI,
                f"đa giác '{ten}': đỉnh '{node.vertices[k]}' KHÔNG đồng phẳng "
                f"với ba đỉnh đầu — bốn điểm ấy không tạo thành một hình phẳng",
            )
    return dinh, (
        f"Dựng đa giác {ten} qua {len(dinh)} đỉnh "
        f"{', '.join(node.vertices)}."
    )


def exec_construct_solid(node: Any, mem: dict[str, Any]) -> tuple[Polyhedron, str]:
    """Khối từ ĐỈNH ĐÃ ĐẶT TÊN + bảng mặt.

    Kiểm chỉ số mặt tại đây chứ không để `Polyhedron` vỡ muộn: `faces` là thứ
    LLM viết ra, nên chỉ số ngoài biên là ca thường gặp chứ không phải ngoại
    lệ, và `IndexError` trần thì không nói được đỉnh nào thiếu.
    """
    dinh = tuple(_lay(mem, t, Vec3, "đỉnh") for t in node.vertices)
    n = len(dinh)
    for i, f in enumerate(node.faces):
        if len(f) < 3:
            raise GeometryError(
                ERR_SAI_LOAI, f"mặt thứ {i + 1} có {len(f)} đỉnh, cần ít nhất 3"
            )
        xau = [j for j in f if not 0 <= j < n]
        if xau:
            raise GeometryError(
                ERR_SAI_LOAI,
                f"mặt thứ {i + 1} trỏ tới chỉ số đỉnh {xau} ngoài khoảng "
                f"0..{n - 1} — khối chỉ khai {n} đỉnh",
            )
    ten = node.label or node.target_var
    khoi = Polyhedron(vertices=dinh, faces=tuple(tuple(f) for f in node.faces))
    return khoi, f"Dựng khối {ten} từ {n} đỉnh và {len(node.faces)} mặt."


def exec_construct_section(node: Any, mem: dict[str, Any]) -> tuple[Section, list[str]]:
    """Thiết diện → **nhiều** lời kể, mỗi cạnh một bước.

    Trả danh sách vì một câu lệnh IR ở đây sinh ra nhiều bước timeline: đó
    chính là dãy thao tác học sinh phải làm trên giấy.
    """
    sol = _lay(mem, node.solid, Polyhedron, "khối")
    pl = _lay(mem, node.plane, Plane3, "mặt phẳng")
    s = cross_section(sol, pl)
    ke = [
        f"Trên mặt thứ {st.face_index + 1} của khối, nối "
        f"({st.a.x}, {st.a.y}, {st.a.z}) với ({st.b.x}, {st.b.y}, {st.b.z})."
        for st in s.steps
    ]
    return s, ke


def exec_construct_curved_solid(
    node: Any, mem: dict[str, Any]
) -> tuple[CurvedSolid, str]:
    """Khối cong từ các ĐIỂM ĐÃ ĐẶT TÊN — **một** câu lệnh cho cả ba hình.

    Không ô nào nhận một con số: bán kính, chiều cao và trục đều dẫn xuất từ ba
    điểm mà kernel đã dựng. Nên mô hình không có đường nào khai thẳng một bán
    kính nó tự tính — R0 giữ nguyên hình dạng đã có với đa diện.

    Mọi phép kiểm bất biến ba điểm (vành khác tâm · trục không suy biến · vành
    vuông góc trục) nằm ở `CurvedSolid.__post_init__`, tức ở **thẩm quyền của
    LOẠI**; tầng này chỉ đọc tên và chuyển tiếp. Nhân đôi chúng ra đây là dựng
    một bản luật thứ hai sẽ trôi.
    """
    kc = CV.KHOI_CONG.get(node.curved_kind)
    if kc is None:
        raise GeometryError(
            CV.ERR_LOAI_KHOI_LA,
            f"loại khối cong '{node.curved_kind}' không có trong "
            f"{sorted(CV.KHOI_CONG)}")
    tam = _lay(mem, node.anchor, Vec3, "tâm")
    vanh = (_lay(mem, node.rim_point, Vec3, "điểm trên vành")
            if node.rim_point else None)
    dinh = (_lay(mem, node.apex_or_top, Vec3, kc.vai_dinh or "đỉnh")
            if node.apex_or_top else None)
    # BÁN KÍNH KHAI THẲNG — đọc từ bộ nhớ như mọi toán hạng khác, rồi bình
    # phương ở đúng biên miền số. Lược đồ đã bảo đảm đúng một trong hai có mặt.
    q = None
    if getattr(node, "radius", None):
        q = CV.binh_phuong_ban_kinh(
            _lay_dai_luong(mem, node.radius, "bán kính"))
    kh = CurvedSolid(node.curved_kind, tam, dinh, vanh, q)
    ten = node.label or node.target_var
    if q is not None:
        ke = (f"Dựng {kc.danh_tu.lower()} {ten}: tâm {node.anchor}, bán kính "
              f"{node.radius}.")
    elif kc.co_truc:
        ke = (f"Dựng {kc.danh_tu.lower()} {ten}: đáy tâm {node.anchor} đi qua "
              f"{node.rim_point}, {kc.vai_dinh} {node.apex_or_top}.")
    else:
        ke = (f"Dựng {kc.danh_tu.lower()} {ten}: tâm {node.anchor}, đi qua "
              f"{node.rim_point}.")
    return kh, ke
