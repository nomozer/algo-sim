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
    {"point3", "vector3", "line3", "plane3", "polygon3", "solid"}
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
    if isinstance(gt, (Vec3, Line3, Plane3, Polyhedron, Section)):
        return True
    # `polygon3` sống dưới dạng tuple các đỉnh — không có lớp riêng.
    return bool(isinstance(gt, tuple) and gt
                and all(isinstance(v, Vec3) for v in gt))


def la_dai_luong_do(gt: Any, kieu_khai: str | None) -> bool:
    """Giá trị này có phải một **đại lượng đo được** không?

    Không vẽ được, nhưng phải HIỆN LÊN: nó là câu trả lời của bài. Bỏ nó khỏi
    màn hình thì mô phỏng chạy xong mà học sinh không thấy đáp số.
    """
    return isinstance(gt, Fraction) and kieu_khai in KIEU_DAI_LUONG


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


# ── phép ĐO: engine trả SỐ HỮU TỈ, IR chỉ nói đo cái gì ───────────────────
def _do(node: Any, mem: dict[str, Any]) -> Fraction:
    """`measure` → `Fraction`. Không có float ở đâu trong đường này.

    `distance` trả **bình phương khoảng cách** hay khoảng cách? — Trả KHOẢNG
    CÁCH khi nó hữu tỉ, và NÉM khi nó vô tỉ. Lý do: `oracle_result` của tập DEV
    khai `distance: "2"` (một khoảng cách thật), còn `angle` khai `cos²`. Hai
    đại lượng, hai quy ước, và cả hai đều được nói thẳng ra — cái nguy hiểm là
    một quy ước ngầm mà hai phía hiểu khác nhau.

    Vô tỉ thì NÉM chứ không làm tròn: một `√2` lặng lẽ thành `1.414…` là đúng
    cách sai số float quay lại qua cửa sau, sau khi cả kernel đã dựng bằng
    `Fraction` để tránh nó.
    """
    q = node.quantity
    a = mem.get(node.of)
    b = mem.get(node.wrt) if node.wrt else None

    if q == "volume":
        if not isinstance(a, Polyhedron):
            raise GeometryError(ERR_SAI_LOAI, f"'{node.of}' phải là một khối")
        return volume_polyhedron(a)

    if b is None:
        raise GeometryError(
            ERR_SAI_LOAI, f"đo '{q}' cần hai đối tượng, thiếu `wrt`"
        )

    if q == "angle_cos_sq":
        if isinstance(a, Line3) and isinstance(b, Line3):
            return M.cos_sq_between_lines(a, b)
        if isinstance(a, Plane3) and isinstance(b, Plane3):
            return M.cos_sq_between_planes(a, b)
        if isinstance(a, Line3) and isinstance(b, Plane3):
            return M.sin_sq_line_plane(a, b)
        if isinstance(a, Plane3) and isinstance(b, Line3):
            return M.sin_sq_line_plane(b, a)
        raise GeometryError(ERR_SAI_LOAI, "cặp đối tượng không hợp lệ cho góc")

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
    else:
        raise GeometryError(
            ERR_SAI_LOAI, "cặp đối tượng không hợp lệ cho khoảng cách"
        )
    d = _can_huu_ti(d2)
    if d is None:
        raise GeometryError(
            ERR_VO_TI,
            f"khoảng cách là căn của {d2}, một số vô tỉ — không biểu diễn "
            "chính xác được. Hãy hỏi bình phương khoảng cách, hoặc chọn hệ toạ "
            "độ cho số đo hữu tỉ.",
        )
    return d


def _can_huu_ti(x: Fraction) -> Fraction | None:
    """Căn bậc hai CHÍNH XÁC của một phân số, hoặc `None` nếu vô tỉ.

    `math.isqrt` trên tử và mẫu, rồi **kiểm ngược bằng phép nhân**. Không dùng
    `x ** 0.5`: nó đi qua float, và với mẫu số lớn thì `int(sqrt(n))**2 == n`
    trở thành một phép so gần đúng đội lốt phép so bằng.
    """
    import math

    if x < 0:
        return None
    tu, mau = math.isqrt(x.numerator), math.isqrt(x.denominator)
    if tu * tu != x.numerator or mau * mau != x.denominator:
        return None
    return Fraction(tu, mau)


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
