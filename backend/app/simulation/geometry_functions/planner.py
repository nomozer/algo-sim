# -*- coding: utf-8 -*-
"""NHÁNH B (thực nghiệm, run `hybrid-compiler-selection`): DỮ KIỆN CÓ KIỂU → PLANNER chọn và kết hợp hàm của REGISTRY.

    AI: trích dữ kiện (đối tượng, quan hệ, giá trị, vai trò mệnh đề, phủ định, nguồn) — KHÔNG chọn hàm
    planner (module này): kiểm dữ kiện → chọn hàm theo LOẠI + KIỂU toán hạng → mở rộng định nghĩa → lời gọi `{"calls": [...]}`
    sau đó: ĐÚNG đường của nhánh A — lược đồ → cổng nguồn → engine → IR → kernel → Scene3D (`app/ai/function_route.run_fact_route`)

Interface của module: `lap_ke_hoach(raw) -> KeHoach` (lời gọi, mục tiêu chứng minh, mệnh đề phủ định cần kiểm, trace) hoặc
`TuChoi` có mã. Không dựng hình, không tính toán hình học: phần ấy thuộc engine; planner chỉ quyết ĐỊNH GỌI GÌ.

─── VÌ SAO KHÔNG CÓ HỌ BÀI ─────────────────────────────────────────────────────
Mỗi loại dữ kiện có MỘT luật ánh xạ (bảng `_LUAT`), cộng mở rộng định nghĩa cho từ ngữ hình học chuẩn ("chóp đều", "lập phương",
"hình hộp chữ nhật", "tứ diện đều"). Không có luật nào nhìn vào tổ hợp dữ kiện để nhận dạng "dạng bài".

─── DỪNG VÀ GIỚI HẠN ─────────────────────────────────────────────────────────
Một lượt qua danh sách dữ kiện, mỗi dữ kiện qua đúng một luật (độ sâu mở rộng định nghĩa = 1), không tìm kiếm; quá `MAX_CALLS`
lời gọi ⇒ `PLAN_TOO_LARGE`. Không suy ra dữ kiện từ dữ kiện; không chọn vị trí; không lấy mẫu một hình để đọc đại lượng.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .registry import AUXILIARY_RULES, ExactNumber, Label, TuChoi, nhan_cua_de, nhan_phu_da_dung

PLANNER_VERSION = "geometry-fact-planner/3"
#: Nhãn điểm phụ: chuỗi H, H1, H2, …; nhãn đầu tiên không có trong đề lẫn dữ kiện (Label của Registry không cho namespace
#: riêng mà không đổi bề mặt nhà cung cấp của A ⇒ "dành riêng" = chọn tươi + cổng kiểm `AUXILIARY_LABEL_COLLISION`).
_NHAN_PHU = ("H", *(f"H{i}" for i in range(1, 100)))
MAX_CALLS = 64

FactKind = Literal["solid", "polygon_shape", "right_angle", "length", "equal_lengths", "perpendicular", "altitude",
                   "projection", "point_def", "question", "unsupported"]


class TypedFact(BaseModel):
    """MỘT dữ kiện có kiểu. Phẳng (một đối tượng, các ô theo `kind`) để lược đồ structured output của provider diễn đạt được."""

    model_config = ConfigDict(extra="forbid")
    id: str = Field(..., min_length=1)
    kind: FactKind
    role: Literal["premise", "prove", "condition", "question"] = Field(
        ..., description="premise = đề cho; prove = điều phải chứng minh; condition = trong 'nếu … thì'; question = đề hỏi")
    negated: bool = Field(False, description="mệnh đề bị phủ định trong đề")
    ambiguous: bool = Field(False, description="AI không chắc cách hiểu ⇒ planner từ chối, không đoán")
    quotes: Annotated[list[str], Field(min_length=1)] = Field(..., description="đoạn NGUYÊN VĂN của đề làm căn cứ")
    solid: str | None = Field(None, description="ký hiệu khối như đề viết: S.ABC, ABC.A'B'C', ABCD (tứ diện)")
    solid_type: Literal["pyramid", "prism", "tetrahedron", "cube", "cuboid"] | None = None
    regular: bool | None = Field(None, description="đề nói khối ĐỀU")
    right: bool | None = Field(None, description="đề nói lăng trụ ĐỨNG")
    points: list[Label] | None = Field(None, description="đỉnh đa giác / đoạn / mặt phẳng tuỳ loại")
    shape: Literal["equilateral_triangle", "square", "regular_hexagon", "regular_polygon", "rectangle", "triangle"] | None = None
    at: Label | None = Field(None, description="đỉnh góc vuông · ảnh hình chiếu")
    point: Label | None = None
    point_kind: Literal["midpoint", "centroid", "intersect_line_line", "intersect_line_plane"] | None = None
    value: ExactNumber | None = None
    measure: Literal["segment", "base_edge", "lateral_edge", "height", "edge"] | None = Field(
        None, description="độ dài này là của gì: một đoạn có tên, cạnh đáy, cạnh bên, chiều cao, mọi cạnh (lập phương, tứ diện đều)")
    points_a: list[Label] | None = Field(None, description="toán hạng 1: 1 điểm, 2 điểm = đường thẳng, ≥3 = mặt phẳng")
    points_b: list[Label] | None = Field(None, description="toán hạng 2")
    quantity: Literal["volume", "area", "length", "distance", "angle"] | None = None
    reason: str | None = None


@dataclass
class KeHoach:
    calls: list[dict[str, Any]] = field(default_factory=list)
    goals: list[dict[str, Any]] = field(default_factory=list)       # điều phải chứng minh: kiểm SAU khi dựng
    negated: list[dict[str, Any]] = field(default_factory=list)     # mệnh đề phủ định: phải SAI trên hình
    trace: list[dict[str, Any]] = field(default_factory=list)
    auxiliary: list[dict[str, Any]] = field(default_factory=list)  # điểm phụ do luật phân rã mục tiêu đưa vào (`_phan_ra`)
    taken: set[str] = field(default_factory=set)                    # nhãn của đề + của dữ kiện: điểm phụ không được trùng
    fact_ids: set[str] = field(default_factory=set)                 # id lời gọi điểm phụ không được trùng id dữ kiện
    heights: dict[str, str] = field(default_factory=dict)           # khối → id dữ kiện chiều cao (chẩn đoán tính duy nhất)
    volume_asks: dict[str, str] = field(default_factory=dict)       # id câu hỏi thể tích → khối
    solids: dict[str, "_Khoi"] = field(default_factory=dict)


@dataclass
class _Khoi:
    ky_hieu: str                 # như đề viết
    ten: str                     # tên khối của engine (S.ABC · ABC.A'B'C' · D.ABC cho tứ diện ABCD)
    loai: str
    day: list[str]
    dinh: str | None = None
    tren: list[str] = field(default_factory=list)
    deu: bool = False
    dung: bool = False
    fact: str = ""
    quotes: list[str] = field(default_factory=list)
    kieu: str = ""               # solid_type như AI trích (tetrahedron · cube · cuboid · pyramid · prism)


def _nhan(s: str) -> list[str]:
    import re

    return re.findall(r"[A-Z][0-9]*'?", s)


def _doc_khoi(f: TypedFact) -> _Khoi:
    kh = _doc_khoi_tho(f)
    kh.kieu = f.solid_type or ""
    if f.negated:                    # "không phải là hình chóp đều S.ABC": khối vẫn có, tính ĐỀU bị phủ định ⇒ không dùng
        kh.deu = False
    return kh


def _doc_khoi_tho(f: TypedFact) -> _Khoi:
    s, t = (f.solid or "").replace("’", "'"), f.solid_type
    if t == "tetrahedron":
        p = _nhan(s)
        if len(p) != 4:
            raise TuChoi("FACT_INCOMPLETE", f"{f.id}: tứ diện cần đúng 4 đỉnh", (f.id,))
        return _Khoi(s, f"{p[3]}.{''.join(p[:3])}", "pyramid", p[:3], dinh=p[3], deu=bool(f.regular), fact=f.id,
                     quotes=list(f.quotes))
    if "." not in s:
        raise TuChoi("FACT_INCOMPLETE", f"{f.id}: ký hiệu khối {s!r} không đọc được", (f.id,))
    a, b = s.split(".", 1)
    if t == "pyramid":
        if len(_nhan(a)) != 1:
            raise TuChoi("FACT_INCOMPLETE", f"{f.id}: chóp phải có một đỉnh", (f.id,))
        return _Khoi(s, s, "pyramid", _nhan(b), dinh=_nhan(a)[0], deu=bool(f.regular), fact=f.id, quotes=list(f.quotes))
    day, tren = _nhan(a), _nhan(b)
    if len(day) != len(tren):
        raise TuChoi("FACT_INCOMPLETE", f"{f.id}: hai đáy lăng trụ khác số đỉnh", (f.id,))
    return _Khoi(s, s, t or "prism", day, tren=tren, deu=bool(f.regular),
                 dung=bool(f.right) or bool(f.regular) or t in ("cube", "cuboid"), fact=f.id, quotes=list(f.quotes))


_CAN = {"solid": ("solid", "solid_type"), "polygon_shape": ("points", "shape"), "right_angle": ("at", "points"),
        "length": ("value", "measure"), "equal_lengths": ("points_a", "points_b"), "perpendicular": ("points_a", "points_b"),
        "altitude": ("points", "solid"), "projection": ("point", "points", "at"), "point_def": ("point", "point_kind", "points"),
        "question": ("quantity",), "unsupported": ("reason",)}
_DA_GIAC_DEU = {"equilateral_triangle": 3, "square": 4, "regular_hexagon": 6, "regular_polygon": None}


def doc_du_kien(raw: Any) -> list[TypedFact]:
    try:
        facts = [TypedFact.model_validate(f) for f in (raw or {}).get("facts") or []]
    except (ValidationError, AttributeError) as e:
        raise TuChoi("SCHEMA_INVALID", f"dữ kiện sai lược đồ: {e}") from None
    if not facts:
        raise TuChoi("SCHEMA_INVALID", "không có dữ kiện nào")
    if len({f.id for f in facts}) != len(facts):
        raise TuChoi("SCHEMA_INVALID", "id dữ kiện trùng")
    for f in facts:
        required = _CAN[f.kind]
        if f.kind == "point_def" and f.point_kind in ("intersect_line_line", "intersect_line_plane"):
            required = ("point", "point_kind", "points_a", "points_b")
        if thieu := [k for k in required if getattr(f, k) in (None, [])]:
            raise TuChoi("FACT_INCOMPLETE", f"{f.id} ({f.kind}) thiếu {thieu}", (f.id,))
    return facts


def lap_ke_hoach(raw: Any, problem_text: str = "") -> KeHoach:
    """Dữ kiện có kiểu → kế hoạch lời gọi. Từ chối (`TuChoi`) khi dữ kiện mơ hồ, có điều kiện, thiếu ô, hay không ánh xạ được.
    `problem_text` chỉ dùng để chọn nhãn điểm phụ không trùng đề (cổng nguồn kiểm lại độc lập)."""
    facts = doc_du_kien(raw)
    k = KeHoach()
    k.fact_ids = {f.id for f in facts}
    k.taken = nhan_cua_de(problem_text) | nhan_phu_da_dung(problem_text) | {n for f in facts for v in (f.points, f.points_a, f.points_b, [f.at, f.point],
                                                                       _nhan(f.solid or "")) for n in (v or []) if n}
    if mo := [f.id for f in facts if f.ambiguous]:
        raise TuChoi("AMBIGUOUS_FACT", f"AI đánh dấu mơ hồ: {mo} — không đoán cách hiểu", tuple(mo))
    if dk := [f.id for f in facts if f.role == "condition"]:
        raise TuChoi("CONDITIONAL_CLAUSE", f"dữ kiện trong mệnh đề điều kiện {dk} — không phải giả thiết vô điều kiện", tuple(dk))
    for f in facts:
        if f.kind == "solid" and f.role != "question":
            kh = _doc_khoi(f)
            k.solids[kh.ky_hieu] = kh
    ten = {s: kh.ten for s, kh in k.solids.items()} | {kh.ten: kh.ten for kh in k.solids.values()}
    deu: dict[frozenset, dict] = {}                                     # đáy → lời gọi regular_polygon (để gắn cạnh)

    def phat(fid: str, fn: str, args: dict, quotes: list[str], luat: str, dich: str = "calls") -> dict:
        c = {"id": fid, "fn": fn, "args": args, "source": {"quotes": list(dict.fromkeys(quotes))}}
        getattr(k, dich).append(c) if dich == "calls" else None
        k.trace.append({"fact": fid.split("_")[0], "rule": luat, "fn": fn, "call": fid})
        return c

    def khoi_cua(s: str | None, f: TypedFact) -> _Khoi:
        kh = k.solids.get(s or "") or next((x for x in k.solids.values() if x.ten == s), None)
        if kh is None:
            raise TuChoi("UNKNOWN_SOLID", f"{f.id}: khối {s!r} không có trong dữ kiện", (f.id,))
        return kh

    # ── khối + mở rộng định nghĩa ───────────────────────────────────────────
    for kh in k.solids.values():
        if kh.loai == "pyramid":
            phat(kh.fact, "regular_pyramid" if kh.deu else "pyramid", {"apex": kh.dinh, "base": kh.day}, kh.quotes,
                 "solid→" + ("regular_pyramid (định nghĩa chóp đều)" if kh.deu else "pyramid"))
            if kh.deu:
                deu[frozenset(kh.day)] = phat(kh.fact + "_day", "regular_polygon", {"vertices": kh.day}, kh.quotes,
                                              "chóp đều ⇒ đáy đa giác đều")
        else:
            phat(kh.fact, "prism", {"base": kh.day, "top": kh.tren, "right": kh.dung}, kh.quotes,
                 f"solid({kh.loai})→prism (right={kh.dung})")
            if kh.deu or kh.loai == "cube":
                if kh.loai == "cube" and len(kh.day) != 4:
                    raise TuChoi("FACT_INCOMPLETE", f"{kh.fact}: lập phương cần đáy 4 đỉnh", (kh.fact,))
                deu[frozenset(kh.day)] = phat(kh.fact + "_day", "regular_polygon", {"vertices": kh.day}, kh.quotes,
                                              "lăng trụ đều / lập phương ⇒ đáy đa giác đều")
            elif kh.loai == "cuboid":
                phat(kh.fact + "_day", "rectangle", {"vertices": kh.day}, kh.quotes, "hình hộp chữ nhật ⇒ đáy hình chữ nhật")

    for f in facts:
        if f.kind == "solid" and f.role != "question":
            continue
        if f.role == "prove":
            c = _anh_xa(f, k, ten, deu, khoi_cua, lambda *a, **kw: phat(*a, **kw, dich="goals"))
            k.goals.append({"fact": f.id, "call": c})
            continue
        if f.negated:
            c = _anh_xa(f, k, ten, deu, khoi_cua, lambda *a, **kw: phat(*a, **kw, dich="negated"))
            k.negated.append({"fact": f.id, "call": c})
            continue
        _anh_xa(f, k, ten, deu, khoi_cua, phat)
    for f in facts:
        if f.kind == "length" and f.measure == "height" and f.role == "premise" and not f.negated:
            k.heights[khoi_cua(f.solid, f).ten] = f.id
    if len(k.calls) > MAX_CALLS:
        raise TuChoi("PLAN_TOO_LARGE", f"kế hoạch {len(k.calls)} lời gọi > trần {MAX_CALLS}")
    # Lời gọi y hệt (cùng hàm, cùng đối số) từ hai dữ kiện: giữ MỘT. Đa giác/khối gộp nguồn (từ khoá có thể ở quote kia);
    # độ dài giữ quote của lời gọi đầu (gộp có thể đưa hai số vào cùng một lời gọi). Câu hỏi không bao giờ gộp.
    gon: dict[str, dict] = {}
    for c in k.calls:
        khoa = c["id"] if c["fn"].startswith("ask_") else c["fn"] + json.dumps(c["args"], sort_keys=True, ensure_ascii=False)
        if khoa not in gon:
            gon[khoa] = c
        elif c["fn"] not in ("segment_length", "height"):
            gon[khoa]["source"]["quotes"] = list(dict.fromkeys(gon[khoa]["source"]["quotes"] + c["source"]["quotes"]))
    k.calls = list(gon.values())
    return k


def _toan_hang(p: list[str] | None) -> str:
    return "point" if len(p or []) == 1 else "line" if len(p or []) == 2 else "plane"


def _anh_xa(f: TypedFact, k: KeHoach, ten: dict, deu: dict, khoi_cua, phat) -> dict | None:
    """MỘT dữ kiện → lời gọi. Chọn hàm theo `kind` + KIỂU toán hạng; vai trò độ dài ("cạnh bên") giải theo khối."""
    q = list(f.quotes)
    if f.kind == "unsupported":
        return phat(f.id, "unsupported", {"reason": f.reason}, q, "unsupported")
    if f.kind == "polygon_shape":
        if f.shape in _DA_GIAC_DEU:
            n = _DA_GIAC_DEU[f.shape]
            if n and len(f.points) != n:
                raise TuChoi("FACT_INCOMPLETE", f"{f.id}: {f.shape} cần {n} đỉnh", (f.id,))
            if (cu := deu.get(frozenset(f.points))) is not None:       # đáy đã được khai đều qua khối: gắn cạnh + nguồn
                cu["source"]["quotes"] = list(dict.fromkeys(cu["source"]["quotes"] + q))
                if f.value:
                    cu["args"]["side"] = f.value
                return cu
            c = phat(f.id, "regular_polygon", {"vertices": f.points, **({"side": f.value} if f.value else {})}, q,
                     f"polygon_shape({f.shape})→regular_polygon")
            deu[frozenset(f.points)] = c
            return c
        if f.shape == "rectangle":
            return phat(f.id, "rectangle", {"vertices": f.points}, q, "polygon_shape(rectangle)→rectangle")
        return None                                                    # "tam giác ABC": chỉ đặt tên, không ràng buộc
    if f.kind == "right_angle":
        return phat(f.id, "right_angle", {"vertex": f.at, "rays": f.points}, q, "right_angle")
    if f.kind == "equal_lengths":
        return phat(f.id, "equal_length", {"segment_a": f.points_a, "segment_b": f.points_b}, q, "equal_lengths→equal_length")
    if f.kind == "length":
        return _do_dai(f, q, deu, khoi_cua, phat)
    if f.kind == "perpendicular":
        ta, tb = _toan_hang(f.points_a), _toan_hang(f.points_b)
        a, b = (f.points_a, f.points_b) if (ta, tb) != ("plane", "line") else (f.points_b, f.points_a)
        ta, tb = _toan_hang(a), _toan_hang(b)
        if (ta, tb) == ("line", "plane"):
            return phat(f.id, "perpendicular_line_plane", {"line": a, "plane": b}, q, "perpendicular(line, plane)")
        if (ta, tb) == ("line", "line"):
            return phat(f.id, "perpendicular_lines", {"line1": a, "line2": b}, q, "perpendicular(line, line)")
        if (ta, tb) == ("plane", "plane"):
            for mat, day in ((a, b), (b, a)):
                kh = next((x for x in k.solids.values() if frozenset(x.day) == frozenset(day)), None)
                if kh is not None and len(mat) == 3 and len([v for v in mat if v not in kh.day]) == 1:
                    return phat(f.id, "face_perpendicular_base", {"face": mat, "base": day}, q,
                                "perpendicular(face, base)→face_perpendicular_base")
            raise TuChoi("UNSUPPORTED_CAPABILITY", f"{f.id}: hai mặt phẳng vuông góc mà không mặt nào là (mặt bên, đáy) — "
                         "chưa có phép dựng", (f.id,))
        raise TuChoi("UNSUPPORTED_CAPABILITY", f"{f.id}: vuông góc giữa {ta} và {tb}", (f.id,))
    if f.kind == "altitude":
        kh = khoi_cua(f.solid, f)
        x, y = f.points
        dinh, chan = (x, y) if x == kh.dinh else (y, x)
        return phat(f.id, "altitude", {"apex": dinh, "foot": chan, "solid": kh.ten}, q, "altitude")
    if f.kind == "projection":
        if len(f.points) == 2:
            return phat(f.id, "orthogonal_projection_line", {"point": f.point, "line": f.points, "image": f.at}, q, "projection(point, line)")
        return phat(f.id, "orthogonal_projection", {"point": f.point, "plane": f.points, "image": f.at}, q, "projection")
    if f.kind == "point_def":
        if f.point_kind == "intersect_line_line":
            return phat(f.id, f.point_kind, {"point": f.point, "line1": f.points_a, "line2": f.points_b}, q, "point_def(line–line)")
        if f.point_kind == "intersect_line_plane":
            return phat(f.id, f.point_kind, {"point": f.point, "line": f.points_a, "plane": f.points_b}, q, "point_def(line–plane)")
        fn = "midpoint" if f.point_kind == "midpoint" else "centroid"
        args = {"point": f.point, ("segment" if fn == "midpoint" else "polygon"): f.points}
        return phat(f.id, fn, args, q, f"point_def({f.point_kind})")
    if f.kind == "question":
        return _cau_hoi(f, q, k, khoi_cua, phat)
    raise TuChoi("UNSUPPORTED_CAPABILITY", f"{f.id}: loại dữ kiện {f.kind} chưa có luật", (f.id,))


def _do_dai(f: TypedFact, q: list[str], deu: dict, khoi_cua, phat) -> dict:
    m = f.measure
    if m == "segment":
        if not f.points or len(f.points) != 2:
            raise TuChoi("FACT_INCOMPLETE", f"{f.id}: độ dài đoạn cần hai điểm", (f.id,))
        return phat(f.id, "segment_length", {"segment": f.points, "value": f.value}, q, "length(segment)")
    kh = khoi_cua(f.solid, f)
    if m == "height":
        return phat(f.id, "height", {"solid": kh.ten, "value": f.value}, q, "length(height)→height")

    def canh_day() -> dict:
        reg = deu.get(frozenset(kh.day))
        if reg is None:
            raise TuChoi("AMBIGUOUS_REFERENCE", f"{f.id}: 'cạnh đáy' của đáy không đều — không biết là cạnh nào", (f.id,))
        reg["args"]["side"] = f.value
        reg["source"]["quotes"] = list(dict.fromkeys(reg["source"]["quotes"] + q))
        return reg

    def canh_ben(fid: str, qs: list[str], luat: str) -> dict:
        if kh.loai == "pyramid":
            if not kh.deu:
                raise TuChoi("AMBIGUOUS_REFERENCE", f"{f.id}: 'cạnh bên' của chóp không đều — các cạnh bên không chắc bằng nhau",
                             (f.id,))
            return phat(fid, "segment_length", {"segment": [kh.dinh, kh.day[0]], "value": f.value}, qs, luat)
        return phat(fid, "segment_length", {"segment": [kh.day[0], kh.tren[0]], "value": f.value}, qs, luat)

    if m == "base_edge":
        k_ = canh_day()
        return k_
    if m == "lateral_edge":
        return canh_ben(f.id, q, "length(lateral_edge)→segment_length (mọi cạnh bên bằng nhau)")
    if m == "edge":
        dung_moi_canh = kh.kieu == "cube" or (kh.kieu == "tetrahedron" and kh.deu)
        if not dung_moi_canh:
            raise TuChoi("AMBIGUOUS_REFERENCE", f"{f.id}: 'cạnh' chỉ xác định khi mọi cạnh bằng nhau (lập phương, tứ diện đều)",
                         (f.id,))
        canh_day()
        return canh_ben(f.id, list(dict.fromkeys(kh.quotes + q)), "length(edge)→cạnh đáy + cạnh bên (định nghĩa)")
    raise TuChoi("FACT_INCOMPLETE", f"{f.id}: measure {m!r}", (f.id,))


def _cau_hoi(f: TypedFact, q: list[str], k: KeHoach, khoi_cua, phat) -> dict:
    n = f.quantity
    if n == "volume":
        kh = khoi_cua(f.solid, f)
        k.volume_asks[f.id] = kh.ten
        return phat(f.id, "ask_volume", {"solid": kh.ten}, q, "question(volume)")
    if n == "area":
        return phat(f.id, "ask_area", {"polygon": f.points}, q, "question(area)")
    if n == "length" or (n == "distance" and _toan_hang(f.points_a) == _toan_hang(f.points_b) == "point"):
        seg = f.points or (f.points_a or []) + (f.points_b or [])
        return phat(f.id, "ask_length", {"segment": seg}, q, "question(length)")
    a, b = f.points_a, f.points_b
    loai = (_toan_hang(a), _toan_hang(b))
    if n == "distance":
        if loai == ("plane", "point"):
            a, b, loai = b, a, ("point", "plane")
        if loai == ("point", "plane"):
            return phat(f.id, "ask_distance_point_plane", {"point": a[0], "plane": b[:3]}, q, "question(distance point–plane)")
        if loai == ("line", "line"):
            return phat(f.id, "ask_distance_lines", {"line1": a, "line2": b}, q, "question(distance line–line)")
        if loai in (("point", "line"), ("line", "point")) and f.role == "question" and not f.negated:
            p, dt = (a, b) if loai == ("point", "line") else (b, a)
            return _phan_ra(f, q, k, phat, p[0], dt)
    if n == "angle":
        if loai == ("plane", "line"):
            a, b, loai = b, a, ("line", "plane")
        if loai == ("line", "plane"):
            return phat(f.id, "ask_angle_line_plane", {"line": a, "plane": b}, q, "question(angle line–plane)")
        if loai == ("plane", "plane"):
            return phat(f.id, "ask_angle_plane_plane", {"plane1": a, "plane2": b}, q, "question(angle plane–plane)")
    raise TuChoi("UNSUPPORTED_CAPABILITY", f"{f.id}: câu hỏi {n} giữa {loai} chưa có hàm", (f.id,))


def _phan_ra(f: TypedFact, q: list[str], k: KeHoach, phat, p: str, dt: list[str]) -> dict:
    """PHÂN RÃ MỤC TIÊU, độ sâu 1: khoảng cách (điểm, đường) = độ dài từ điểm tới chân vuông góc PHỤ trên đường.
    Chỉ cho câu hỏi khẳng định (đã chặn điều kiện/mơ hồ ở `lap_ke_hoach`, phủ định/chứng minh ở `_cau_hoi`). Không thêm dữ
    kiện: hai lời gọi mang ĐÚNG quote của câu hỏi; cổng `kiem_nguon` kiểm lại khai báo này."""
    luat = "distance(point,line)"
    x = next((n for n in _NHAN_PHU if n not in k.taken), None)
    if x is None:
        raise TuChoi("PLAN_TOO_LARGE", f"{f.id}: hết nhãn điểm phụ", (f.id,))
    k.taken.add(x)
    fn_dung, fn_hoi = AUXILIARY_RULES[luat]
    dung = {c["id"] for c in k.calls}
    cid = next(i for i in (f"{f.id}_aux", *(f"{f.id}_aux{n}" for n in range(2, 1000))) if i not in k.fact_ids | dung)
    phat(cid, fn_dung, {"point": p, "line": dt, "image": x}, q, f"{luat}→{fn_dung} (điểm phụ {x})")
    c = phat(f.id, fn_hoi, {"segment": [p, x]}, q, f"{luat}→{fn_hoi}")
    k.trace[-2]["fact"] = k.trace[-1]["fact"] = f.id                   # id có "_" (cau_2): `phat` tách sai dữ kiện nguồn
    d = {"label": x, "rule": luat, "goal": f.id, "construct": cid, "ask": f.id, "point": p, "line": list(dt),
         "quotes": list(dict.fromkeys(q)), "provenance": "DERIVED", "binding": "AUXILIARY"}
    k.auxiliary.append(d)
    k.trace.append({"fact": f.id, "step": "decompose_goal", "rule": luat, "calls": [cid, f.id], "auxiliary": x,
                    "provenance": "DERIVED", "binding": "AUXILIARY"})
    return c
