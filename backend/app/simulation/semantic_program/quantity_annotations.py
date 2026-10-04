# -*- coding: utf-8 -*-
"""W17 §15.4 — SỐ ĐO TRÊN HÌNH: mỗi đại lượng hiển thị gắn với CHỦ THỂ hình học của nó.

Backend sở hữu nghĩa; frontend chỉ chiếu, đặt nhãn và bật/tắt — không suy chủ thể từ tên biến,
không tự tính giá trị. Hai nguồn gắn, cả hai tất định:
- đại lượng ĐO: toán hạng IR của `measure` — diện tích → đa giác/thiết diện (`region`), thể tích →
  khối đa diện (`solid`), khoảng cách có một toán hạng là ĐIỂM → cặp (`pair`; hai ĐIỂM ⇒ độ dài đoạn,
  `segment`); góc chưa có điểm neo (xem `_DO`);
- độ dài ĐỀ CHO: đoạn mà bộ đọc đề của server đọc ngay trước span bằng chứng GIVEN (cùng thẩm quyền
  `grounding_gate`), VÀ khoảng cách CHÍNH XÁC giữa hai điểm trong bộ nhớ cuối bằng đúng giá trị.
Không gắn được ⇒ không có nhãn, chẩn đoán `ANNOTATION_UNBOUND <id>: <lý do>`; đại lượng vẫn ở bảng
chi tiết. `category` (`measurement`/`result`) và `role` do `scene3d` quyết: chúng cần nhóm `target`
và bí danh.

W18 (§16.6–16.7): cùng chủ thể ⇒ `same_as` (một nhãn, một dòng — không còn bỏ gắn); khoảng cách điểm →
đường/mặt phẳng mang `witness` — chân CHÍNH XÁC do kernel tính, neo nhãn ở trung điểm đoạn tới chân.
Đăng ký: `docs/architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md` §15.4, §16.6, §16.7.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Any

from ..geometry import kernel as K
from ..geometry.exact import Line3, Plane3, Vec3
from .grounding_gate import _bang_chung_do_dai
from .segment_relation import nhan_doan_truoc
from .shape_constraint import che_muc_tieu
from .source_entities import dinh_danh_thuc_the

#: `measure.quantity` → (kind, anchor, kiểu được phép của toán hạng `of` — None: mọi kiểu).
#: Điểm neo phải đặt được ở phía trình bày CHỈ bằng trung bình toạ độ (frontend cấm suy luận hình
#: học, kể cả chân đường vuông góc): khoảng cách cần một toán hạng là ĐIỂM (neo ở điểm ấy; hai
#: điểm ⇒ đoạn); góc giữa hai đường/mặt và vật cong (đường tròn, elip, khối tròn xoay) chưa có
#: điểm neo đăng ký ⇒ không gắn.
_DO: dict[str, tuple[str, str, frozenset[str] | None]] = {
    "area": ("area", "region", frozenset({"polygon3", "section"})),
    "volume": ("volume", "solid", frozenset({"solid"})),
    "distance": ("distance", "pair", None),
}


def gan_so_do(spec: Any, final_memory: dict[str, Any], contract: Any,
              objects: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """→ ({id đại lượng: {kind, subject_ids, anchor, unit}}, chẩn đoán) cho mọi vật `quantity`."""
    loai = {o["id"]: o["type"] for o in objects}
    dinh_nghia = {getattr(s, "target_var", None): s for s in spec.statements}
    khai = {d.name: d for d in spec.memory_declarations}
    de = che_muc_tieu(getattr(contract, "problem_text", "") or "")
    gan: dict[str, dict[str, Any]] = {}
    chan_doan: list[str] = []
    for o in objects:
        if o["type"] != "quantity":
            continue
        kq = _gan_mot(o["id"], dinh_nghia.get(o["id"]), khai.get(o["id"]), loai, final_memory, de)
        if isinstance(kq, dict):
            gan[o["id"]] = kq
        else:
            chan_doan.append(f"ANNOTATION_UNBOUND {o['id']}: {kq}")
    # Một chủ thể, một nhãn: độ dài đề cho AA′ và chiều cao đo được AA′ (hình hộp) là cùng một phép
    # đo trên cùng một đoạn. Nhãn thuộc DỮ KIỆN (không có câu lệnh định nghĩa), rồi theo thứ tự cảnh;
    # vật sau trỏ `same_as` về nó (W18 §16.6). Tiêu chí là chủ thể — KHÔNG BAO GIỜ là giá trị.
    da_co: dict[tuple, str] = {}
    for q in sorted(gan, key=lambda q: dinh_nghia.get(q) is not None):
        k = (gan[q]["kind"], gan[q]["anchor"], frozenset(gan[q]["subject_ids"]))
        if k in da_co:
            chan_doan.append(f"ANNOTATION_SAME_AS {q}: {da_co[k]}")
            gan[q]["same_as"] = da_co[k]
        else:
            da_co[k] = q
    return gan, chan_doan


def _xau(v: Vec3) -> list[str]:
    return [str(v.x), str(v.y), str(v.z)]


def _nhan_chung(diem: str, nhan: str, mem: dict[str, Any]) -> dict[str, Any] | None:
    """W18 §16.7 — chân đường vuông góc CHÍNH XÁC từ `diem` tới đường/mặt phẳng `nhan` (kernel), và hai
    phương của ký hiệu vuông góc tại chân: `u` dọc vật nhận, `v` từ chân tới điểm. Vật nhận khác (đa
    giác, khối…) hay khoảng cách 0 ⇒ không có nhân chứng."""
    p, r = mem.get(diem), mem.get(nhan)
    if isinstance(r, Line3):
        chan, u = K.project_point_onto_line(p, r), r.direction
    elif isinstance(r, Plane3):
        chan = K.project_point_onto_plane(p, r)
        u = r.point - chan
        if u.is_zero():
            u = next(w for w in (r.normal.cross(Vec3.of(*e)) for e in ((1, 0, 0), (0, 1, 0), (0, 0, 1)))
                     if not w.is_zero())
    else:
        return None
    v = p - chan
    if v.is_zero():
        return None
    return {"from": diem, "foot": _xau(chan), "on": nhan, "marker": {"u": _xau(u), "v": _xau(v)}}


def _gan_mot(q: str, st: Any, decl: Any, loai: dict[str, str], mem: dict[str, Any],
             de: str) -> dict[str, Any] | str:
    expr = getattr(st, "expr", None)
    if getattr(expr, "kind", None) == "measure":
        kind, anchor, cho_phep = _DO.get(expr.quantity, (None, None, None))
        chu_the = [x for x in (expr.of, expr.wrt) if x]
        if kind is None:
            return f"measure {expr.quantity} has no registered anchor"
        if any(x not in loai for x in chu_the):
            return "a measured operand is not a scene object"
        if cho_phep is not None and loai[expr.of] not in cho_phep:
            return f"{expr.quantity} of a {loai[expr.of]} has no registered anchor"
        nhan_chung = None
        if expr.quantity == "distance":
            if all(loai[x] == "point3" for x in chu_the):
                kind, anchor = "length", "segment"
            elif not any(loai[x] == "point3" for x in chu_the):
                return "distance between two non-point objects has no registered anchor"
            else:
                diem = next(x for x in chu_the if loai[x] == "point3")
                nhan_chung = _nhan_chung(diem, next(x for x in chu_the if x != diem), mem)
        if nhan_chung is not None:
            return {"kind": kind, "subject_ids": chu_the, "anchor": "witness", "unit": None, "witness": nhan_chung}
        return {"kind": kind, "subject_ids": chu_the, "anchor": anchor, "unit": None}
    if getattr(expr, "kind", None) == "var":
        return f"copy of {expr.name} — shares its identity"
    if st is None and decl is not None and decl.initial_value is not None:
        return _do_dai_de_cho(q, loai, mem, de)
    return "computed by a statement that measures no single subject"


def _do_dai_de_cho(q: str, loai: dict[str, str], mem: dict[str, Any], de: str) -> dict[str, Any] | str:
    """Độ dài ĐỀ CHO: đoạn đề gọi tên ngay trước con số bằng chứng, kiểm bằng khoảng cách chính xác."""
    v = mem.get(q)
    try:
        so: Fraction | str = Fraction(str(v))
    except (ValueError, ZeroDivisionError):
        so = str(v)
    ma, bc, _ = _bang_chung_do_dai(de, q, so, None) if de else ("NO_TEXT", None, "")
    if ma or not bc or not bc.get("span"):
        return "no GIVEN evidence span in the text"
    doan = nhan_doan_truoc(de[:bc["span"][0]])
    if doan is None:
        return "the text gives the number without naming a segment"
    p, r = (dinh_danh_thuc_the(t)[0] for t in doan)
    if loai.get(p) != "point3" or loai.get(r) != "point3":
        return "the named segment's endpoints are not scene points"
    d = mem[r] - mem[p]
    try:
        bang = d.dot(d) == v * v
    except TypeError:
        bang = False
    if not bang:
        return f"the figure's {p}{r} is not {v}"
    return {"kind": "length", "subject_ids": [p, r], "anchor": "segment", "unit": bc.get("unit")}
