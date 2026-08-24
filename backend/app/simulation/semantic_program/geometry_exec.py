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
from ..geometry.section import Polyhedron, Section, cross_section

#: Đối tượng lạ trong bộ nhớ khi phép dựng cần một kiểu cụ thể.
ERR_SAI_LOAI = "GEOMETRY_OPERAND_TYPE"
#: Tên không có trong bộ nhớ.
ERR_KHONG_KHAI = "GEOMETRY_UNDECLARED"


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
