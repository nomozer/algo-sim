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
Các dữ kiện tường minh vẫn ánh xạ một lần. Mục tiêu khoảng cách điểm–đường, và khoảng cách từ một điểm KHÔNG TÊN do đề mô tả
("trung điểm của SC") tới mặt / đường / giao tuyến, phân giải typed needs từ `PlanningContract` của Registry (`_EffectResolver`):
producer tìm theo hiệu ứng + kiểu toán hạng, lời gọi viết từ khuôn của contract — một hàm có contract được dùng mà planner
không cần nhánh riêng cho nó. Ngân sách hữu hạn, tái sử dụng producer đã khai; không tìm hình bằng số, suy tiền đề hoặc lấy
mẫu đáp số. Quá ngân sách ⇒ `PLAN_TOO_LARGE`, không phục vụ một phần.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .registry import AUXILIARY_RULES, MAT_SONG_SONG, MAT_HAI_DUONG, ExactNumber, Label, TuChoi, nhan_cua_de, nhan_phu_da_dung
from .registry import REGISTRY, doc_ke_hoach, render_call, same_call, planning_contracts

PLANNER_VERSION = "geometry-fact-planner/7"
#: Nhãn điểm phụ: chuỗi H, H1, H2, …; nhãn đầu tiên không có trong đề lẫn dữ kiện (Label của Registry không cho namespace
#: riêng mà không đổi bề mặt nhà cung cấp của A ⇒ "dành riêng" = chọn tươi + cổng kiểm `AUXILIARY_LABEL_COLLISION`).
def _nhan_tuoi(stem: str) -> tuple[str, ...]:
    return (stem, *(f"{stem}{i}" for i in range(1, 100)))


_NHAN_PHU = _nhan_tuoi("H")
MAX_CALLS = 64
#: Bound of the goal-directed decomposition `MAT_SONG_SONG`: derived planes per problem (each costs two auxiliary points).
MAX_DERIVED_PLANES = 4
MAX_EFFECT_DEPTH = 3
MAX_EFFECT_NEEDS = 32
MAX_EFFECT_CANDIDATES = 8
MAX_RESULT_LINES = 4
MAX_RESULT_FEET = 8

FactKind = Literal["solid", "polygon_shape", "right_angle", "length", "equal_lengths", "perpendicular", "altitude",
                   "projection", "point_def", "section", "intersection_line", "question", "unsupported"]


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
    line_ref: str | None = Field(None, min_length=1, description="ID dữ kiện intersection_line có nguồn, cho distance/projection; không phải nhãn điểm hay chương trình")
    quantity: Literal["volume", "area", "length", "distance", "angle"] | None = None
    plane_relation: Literal["parallel", "perpendicular", "parallel_two_lines"] | None = Field(
        None, description="thiết diện / diện tích thiết diện với mặt cắt cho bằng QUAN HỆ: mặt qua `point`, song song "
        "(parallel) hay vuông góc (perpendicular) với mặt `points_b`; khi đó không có `points`")
    plane_name: Label | None = Field(None, description="tên mặt phẳng cắt trong đề; bắt buộc cho parallel_two_lines")
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
    derived_planes: dict[tuple, dict] = field(default_factory=dict)  # (khối, điểm, mặt tham chiếu) → khai báo `MAT_SONG_SONG`
    resolver: Any = field(default=None, repr=False)  # ephemeral view of existing calls; no geometry/semantic state


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
        "section": ("solid", "points"), "intersection_line": ("points_a", "points_b"),
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
        if f.kind == "question" and f.point_kind is not None:
            _doc_toan_hang_mo_ta(f)
        if f.line_ref is not None:
            if f.kind == "question" and f.quantity == "distance" and (len(f.points_a or []) == 1 or f.point_kind):
                if (f.points and not f.point_kind) or f.points_b or f.plane_relation:
                    raise TuChoi("SCHEMA_INVALID", f"{f.id}: line_ref thay cho toán hạng đường", (f.id,))
            elif f.kind == "projection" and not f.points and not f.points_a and not f.points_b:
                required = ("point", "at", "line_ref")
            else:
                raise TuChoi("SCHEMA_INVALID", f"{f.id}: line_ref chỉ cho distance / projection", (f.id,))
        if f.kind == "point_def" and f.point_kind in ("intersect_line_line", "intersect_line_plane"):
            required = ("point", "point_kind", "points_a", "points_b")
        if f.plane_relation is not None:                # mặt cắt cho bằng quan hệ: điểm đi qua + mặt tham chiếu, không ba điểm
            if f.kind not in ("section", "question") or f.points:
                raise TuChoi("SCHEMA_INVALID", f"{f.id}: plane_relation chỉ cho thiết diện, và thay cho `points`", (f.id,))
            required = ("solid", "point", "points_b") + (("quantity",) if f.kind == "question" else ())
            if f.plane_relation == "parallel_two_lines":
                required += ("points_a", "plane_name")
                for line in (f.points_a, f.points_b):
                    if line is None or len(line) != 2:
                        raise TuChoi("FACT_INCOMPLETE", f"{f.id}: mỗi đường cần đúng hai điểm đã định danh", (f.id,))
                    if len(set(line)) != 2:
                        raise TuChoi("DEGENERATE_LINE", f"{f.id}: hai đầu mút đường trùng nhau", (f.id,))
        if thieu := [k for k in required if getattr(f, k) in (None, [])]:
            raise TuChoi("FACT_INCOMPLETE", f"{f.id} ({f.kind}) thiếu {thieu}", (f.id,))
    by_id = {f.id: f for f in facts}
    for f in facts:
        if f.line_ref is None:
            continue
        producer = by_id.get(f.line_ref)
        if producer is None:
            raise TuChoi("UNKNOWN_DERIVED_REFERENCE", f"{f.id}: producer {f.line_ref!r} không tồn tại", (f.id,))
        if producer.kind != "intersection_line":
            raise TuChoi("DERIVED_REFERENCE_TYPE_MISMATCH", f"{f.id}: producer không sinh đường", (f.id, producer.id))
        for obj in (f, producer):
            if obj.role == "prove":
                raise TuChoi("GOAL_CLAUSE_NOT_PREMISE", "reference không dùng mục tiêu chứng minh", (obj.id,))
            if obj.role == "condition":
                raise TuChoi("CONDITIONAL_CLAUSE", "reference không dùng điều kiện", (obj.id,))
            if obj.negated:
                raise TuChoi("NEGATED_CLAUSE", "reference không dùng phủ định", (obj.id,))
        if any(len(p or []) != 3 or len(set(p or [])) != 3 for p in (producer.points_a, producer.points_b)):
            raise TuChoi("FACT_INCOMPLETE", "reference cần hai mặt có đúng ba nhãn phân biệt", (producer.id,))
    return facts


def _doc_toan_hang_mo_ta(f: TypedFact) -> None:
    """A question whose first operand is a point the source DESCRIBES but does not name: `point_kind` + `points`,
    no `points_a`/`point`. Which descriptions exist and their arity come from Registry contracts, not from a planner table."""
    if f.points_a or f.point or f.plane_relation:
        raise TuChoi("SCHEMA_INVALID", f"{f.id}: điểm không tên cần hợp đồng mục tiêu đã hỗ trợ "
                     "(point_kind + points; không points_a, không point)", (f.id,))
    goals = [c for s in REGISTRY.values() for c in planning_contracts(s) if c.goal == f.quantity]
    if f.quantity != "distance" and not goals:
        raise TuChoi("UNSUPPORTED_CAPABILITY", f"{f.id}: chưa có hợp đồng mục tiêu cho {f.quantity} với điểm được mô tả", (f.id,))
    contracts = [s.planning for s in REGISTRY.values() if s.planning is not None and s.planning.descriptor == f.point_kind]
    if not contracts:
        raise TuChoi("UNSUPPORTED_CAPABILITY", f"{f.id}: không hàm nào của thư viện dựng được {f.point_kind}", (f.id,))
    pts = f.points or []
    if len(set(pts)) != len(pts) or all(len(c.inputs) != len(pts) for c in contracts):
        raise TuChoi("FACT_INCOMPLETE", f"{f.id}: {f.point_kind} cần {sorted({len(c.inputs) for c in contracts})} điểm "
                     "phân biệt", (f.id,))
    if goals:
        point_arities = {len(c.inputs) - 1 for c in goals
                         if c.inputs and all(t.kind == "Point" and len(t.operands) == 1 for t in c.inputs)}
        if not point_arities:
            raise TuChoi("UNSUPPORTED_CAPABILITY", f"{f.id}: hợp đồng mục tiêu {f.quantity} cần toán hạng phân biệt vai trò", (f.id,))
        b = f.points_b or []
        if f.line_ref or len(set(b)) != len(b) or len(b) not in point_arities:
            raise TuChoi('FACT_INCOMPLETE', f'{f.id}: mục tiêu {f.quantity} cần {sorted(point_arities)} điểm đích phân biệt', (f.id,))
    elif f.line_ref is None and len(set(f.points_b or [])) < 2:
        raise TuChoi("FACT_INCOMPLETE", f"{f.id}: thiếu đích của khoảng cách (đường, mặt hay line_ref)", (f.id,))


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

    k.resolver = _EffectResolver(facts, k, phat, problem_text)

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

    # Bind all explicit producers before resolving goals, independently of provider order.
    for f in sorted(facts, key=lambda f: (f.kind == "question", f.id)):
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
        # Referenced line declarations retain their IDs/quotes for Registry validation; Engine coalesces verified aliases.
        khoa = (c['id'] if c['fn'].startswith('ask_')
                or c['fn']=='intersection_line' and k.resolver.aliases.get(c['id'],c['id']) in k.resolver.lines else
                c['fn'] + json.dumps(c['args'],sort_keys=True,ensure_ascii=False))
        if khoa not in gon:
            gon[khoa] = c
        elif c["fn"] not in ("segment_length", "height"):
            gon[khoa]["source"]["quotes"] = list(dict.fromkeys(gon[khoa]["source"]["quotes"] + c["source"]["quotes"]))
    k.calls = list(gon.values())
    for c in k.calls:
        if c['fn']=='orthogonal_projection_line' and c['args'].get('line_ref') and c['id'] in k.fact_ids:
            k.auxiliary.append({'rule':'result-line-reference', 'consumer':c['id'], 'line_ref':c['args']['line_ref']})
            k.resolver.used = True
    for alias, canonical in k.resolver.aliases.items():
        if alias!=canonical and canonical in k.resolver.lines:
            k.auxiliary.append({'rule':'result-line-alias','producer':alias,'canonical':canonical,'line_ref':canonical})
    _sap_xep_phu_thuoc_loi_goi(k)
    if k.resolver.used:
        _bind_result_dependencies(k)
    return k


_NON_POINT_ARG_KEYS = frozenset({"line_ref", "solid", "value", "side", "reason", "right"})


def _diem_cua_loi_goi(c: dict[str, Any]) -> list[str]:
    a = c.get("args") or {}
    pts: list[str] = []
    for key, val in a.items():
        if key in _NON_POINT_ARG_KEYS:
            continue
        if isinstance(val, list):
            pts.extend(x for x in val if isinstance(x, str))
        elif isinstance(val, str):
            pts.append(val)
    return pts


def _sap_xep_phu_thuoc_loi_goi(k: KeHoach) -> None:
    """Dependency-aware topological ordering over `k.calls` (`GAP-C1` / `ISSUE-RESEARCH-HYBRID-AUXILIARY-BEFORE-SOLID`).

    Builds an explicit directed dependency graph `prereq_id -> call_id`:
    - Data dependencies (`direct_deps`) from derived point producers (`midpoint`, `centroid`, `intersect_*`,
      `orthogonal_projection_line`, `translate_point`, and forward `orthogonal_projection`), `intersection_line`
      `line_ref` producers, sub-solids (`M.ABC`), and `section -> ask_section_area`.
    - Pedagogical foundation tiers (`Tier 0` root solid declarations -> `Tier 1` base foundation -> `Tier 2` apex-foot
      point constructors -> `Tier 3` apex/solid metric & perpendicularity premises -> `Tier 4` auxiliary point/line/
      section/sub-solid constructions -> `Tier 5` `ask_*` / `unsupported` queries).
    - Fail-closed rejection on dangling dependencies (`DANGLING_DEPENDENCY`) and cycles (`DEPENDENCY_CYCLE`).
    - Preserves `k.calls` in its exact original order whenever no dependency edge is violated.
    """
    import heapq

    calls = k.calls
    if not calls:
        return
    by_id = {c["id"]: c for c in calls}
    idx_of = {c["id"]: i for i, c in enumerate(calls)}

    raw_point_outputs: set[str] = set()
    for c in calls:
        fn, a = c["fn"], c.get("args") or {}
        if fn in ("midpoint", "centroid", "intersect_line_line", "intersect_line_plane") and isinstance(a.get("point"), str):
            raw_point_outputs.add(a["point"])
        elif fn in ("orthogonal_projection", "orthogonal_projection_line", "translate_point") and isinstance(a.get("image"), str):
            raw_point_outputs.add(a["image"])

    solids_list = list(k.solids.values())
    if solids_list:
        unproduced_solids = [
            kh
            for kh in solids_list
            if not ((set(kh.day) | ({kh.dinh} if kh.dinh else set()) | set(kh.tren)) & raw_point_outputs)
        ]
        root_solids = unproduced_solids if unproduced_solids else [solids_list[0]]
    else:
        root_solids = []

    base_vertices = {v for kh in root_solids for v in kh.day}
    apex_vertices = {kh.dinh for kh in root_solids if kh.dinh} | {v for kh in root_solids for v in kh.tren}
    solid_vertices = base_vertices | apex_vertices
    root_solid_call_ids = {kh.fact for kh in root_solids}

    explicit_point_producers: dict[str, list[str]] = {}
    for c in calls:
        fn, a = c["fn"], c.get("args") or {}
        if fn in ("midpoint", "centroid", "intersect_line_line", "intersect_line_plane") and isinstance(a.get("point"), str):
            pt = a["point"]
            if pt not in solid_vertices:
                explicit_point_producers.setdefault(pt, []).append(c["id"])
        elif fn in ("orthogonal_projection_line", "translate_point") and isinstance(a.get("image"), str):
            pt = a["image"]
            if pt not in solid_vertices:
                explicit_point_producers.setdefault(pt, []).append(c["id"])

    point_producers: dict[str, list[str]] = {p: list(ids) for p, ids in explicit_point_producers.items()}
    produced_point_of_call: dict[str, str] = {
        cid: pt for pt, cids in explicit_point_producers.items() for cid in cids
    }
    for c in calls:
        fn, a = c["fn"], c.get("args") or {}
        if fn == "orthogonal_projection" and isinstance(a.get("image"), str):
            pt = a["image"]
            is_apex_foot_proj = (
                a.get("point") in apex_vertices
                and set(a.get("plane") or ()) <= base_vertices
                and (pt in base_vertices or pt in explicit_point_producers)
            )
            if not is_apex_foot_proj and pt not in solid_vertices:
                point_producers.setdefault(pt, []).append(c["id"])
                produced_point_of_call[c["id"]] = pt

    direct_deps: dict[str, set[str]] = {c["id"]: set() for c in calls}
    consumed_points_of_call: dict[str, list[str]] = {}
    for c in calls:
        cid, fn, a = c["id"], c["fn"], c.get("args") or {}
        out_pt = produced_point_of_call.get(cid)
        pts = [p for p in _diem_cua_loi_goi(c) if p != out_pt]
        consumed_points_of_call[cid] = pts
        for pt in pts:
            for p_cid in point_producers.get(pt, ()):
                if p_cid != cid:
                    direct_deps[cid].add(p_cid)
        if a.get("line_ref"):
            ref = a["line_ref"]
            if ref not in by_id:
                raise TuChoi("DANGLING_DEPENDENCY", f"{cid} phụ thuộc lời gọi không tồn tại {[ref]}", (cid,))
            direct_deps[cid].add(ref)
        for dep_id in c.get("depends_on") or ():
            if dep_id not in by_id:
                raise TuChoi("DANGLING_DEPENDENCY", f"{cid} phụ thuộc lời gọi không tồn tại {[dep_id]}", (cid,))
            direct_deps[cid].add(dep_id)

    for kh in k.solids.values():
        if kh.fact in by_id and kh.fact not in root_solid_call_ids:
            for v in calls:
                if v["id"] != kh.fact and (v.get("args") or {}).get("solid") == kh.ten:
                    direct_deps[v["id"]].add(kh.fact)

    for u in calls:
        if u["fn"] == "section":
            u_solid = (u.get("args") or {}).get("solid")
            u_plane = frozenset((u.get("args") or {}).get("plane") or ())
            for v in calls:
                if (
                    v["fn"] == "ask_section_area"
                    and (v.get("args") or {}).get("solid") == u_solid
                    and frozenset((v.get("args") or {}).get("plane") or ()) == u_plane
                ):
                    direct_deps[v["id"]].add(u["id"])

    # Determine goal-reachable calls (ask_*, section, explicit line_ref / depends_on)
    goal_roots = [
        c["id"]
        for c in calls
        if c["fn"].startswith("ask_")
        or c["fn"] == "section"
        or bool(c.get("depends_on"))
        or bool((c.get("args") or {}).get("line_ref"))
    ]
    reachable_from_goals: set[str] = set(goal_roots) if goal_roots else set(by_id)
    if k.resolver.used:
        reachable_from_goals = set(by_id)
    else:
        r_queue = list(reachable_from_goals)
        while r_queue:
            curr = r_queue.pop()
            for prereq in direct_deps.get(curr, ()):
                if prereq not in reachable_from_goals:
                    reachable_from_goals.add(prereq)
                    r_queue.append(prereq)

    # Cycle detection on direct_deps (fail-closed on goal-reachable or explicit cycles)
    state: dict[str, int] = {}
    back_edges_to_drop: list[tuple[str, str]] = []

    def _visit(u_id: str) -> None:
        state[u_id] = 1
        for v_id in sorted(direct_deps[u_id]):
            if state.get(v_id) == 1:
                if u_id in reachable_from_goals or v_id in reachable_from_goals:
                    raise TuChoi("DEPENDENCY_CYCLE", f"phụ thuộc vòng qua {u_id} → {v_id}", (u_id, v_id))
                back_edges_to_drop.append((u_id, v_id))
            elif v_id not in state:
                _visit(v_id)
        state[u_id] = 2

    for cid in [c["id"] for c in calls]:
        if cid not in state:
            _visit(cid)

    for u_id, v_id in back_edges_to_drop:
        direct_deps[u_id].discard(v_id)

    # Identify derived points that serve as the foot of a root solid's apex
    apex_foot_points: set[str] = set()
    for c in calls:
        cid, fn, a = c["id"], c["fn"], c.get("args") or {}
        if fn == "perpendicular_line_plane":
            line_pts = set(a.get("line") or ())
            plane_pts = set(a.get("plane") or ())
            if (line_pts & apex_vertices) and plane_pts <= base_vertices:
                apex_foot_points |= (line_pts - apex_vertices) & set(point_producers)
        elif fn == "altitude" and a.get("apex") in apex_vertices and a.get("foot") in point_producers:
            apex_foot_points.add(a["foot"])
        elif fn == "orthogonal_projection" and cid not in produced_point_of_call and a.get("image") in point_producers:
            apex_foot_points.add(a["image"])

    # Close apex_foot_points transitively over point_producers
    queue = list(apex_foot_points)
    while queue:
        pt = queue.pop()
        for p_cid in point_producers.get(pt, ()):
            for in_pt in consumed_points_of_call.get(p_cid, ()):
                if in_pt in point_producers and in_pt not in apex_foot_points:
                    apex_foot_points.add(in_pt)
                    queue.append(in_pt)

    apex_foot_calls = {p_cid for pt in apex_foot_points for p_cid in point_producers.get(pt, ())}

    tier_of: dict[str, int] = {}
    for c in calls:
        cid, fn = c["id"], c["fn"]
        pts = set(_diem_cua_loi_goi(c))
        if fn in ("pyramid", "regular_pyramid", "prism") and cid in root_solid_call_ids and not direct_deps[cid]:
            tier_of[cid] = 0
        elif fn.startswith("ask_") or fn == "unsupported":
            tier_of[cid] = 5
        elif cid in apex_foot_calls:
            tier_of[cid] = 2
        elif (
            fn in ("regular_polygon", "rectangle", "right_angle", "segment_length", "equal_length")
            and pts
            and pts <= base_vertices
            and not direct_deps[cid]
        ):
            tier_of[cid] = 1
        elif (
            cid not in produced_point_of_call
            and fn
            in (
                "regular_polygon",
                "rectangle",
                "right_angle",
                "perpendicular_line_plane",
                "altitude",
                "orthogonal_projection",
                "perpendicular_lines",
                "face_perpendicular_base",
                "height",
                "segment_length",
                "equal_length",
                "parallel_lines",
                "parallel_planes",
            )
            and pts <= (solid_vertices | apex_foot_points)
            and not direct_deps[cid]
        ):
            tier_of[cid] = 3
        else:
            tier_of[cid] = 4

    tiers: dict[int, list[str]] = {t: [] for t in range(6)}
    for c in calls:
        tiers[tier_of[c["id"]]].append(c["id"])

    ordering_deps: dict[str, set[str]] = {cid: set(deps) for cid, deps in direct_deps.items()}
    for cid in calls:
        u_id = cid["id"]
        t = tier_of[u_id]
        if t >= 1:
            ordering_deps[u_id].update(tiers[0])
        if t >= 2:
            ordering_deps[u_id].update(tiers[1])
        if t >= 3:
            ordering_deps[u_id].update(tiers[2])
        if t >= 4:
            ordering_deps[u_id].update(tiers[3])
        if t >= 5:
            ordering_deps[u_id].update(tiers[4])
        ordering_deps[u_id].discard(u_id)

    # Preserve exact original order if all prerequisites already precede their dependents
    if all(idx_of[prereq] < idx_of[cid] for cid, deps in ordering_deps.items() for prereq in deps):
        return

    in_degree = {cid: len(ordering_deps[cid]) for cid in by_id}
    dependents: dict[str, list[str]] = {cid: [] for cid in by_id}
    for cid, deps in ordering_deps.items():
        for prereq in deps:
            dependents[prereq].append(cid)

    heap: list[tuple[int, int, str]] = [
        (tier_of[cid], idx_of[cid], cid) for cid, deg in in_degree.items() if deg == 0
    ]
    heapq.heapify(heap)
    ordered_ids: list[str] = []
    while heap:
        _t, _i, u_id = heapq.heappop(heap)
        ordered_ids.append(u_id)
        for v_id in dependents[u_id]:
            in_degree[v_id] -= 1
            if in_degree[v_id] == 0:
                heapq.heappush(heap, (tier_of[v_id], idx_of[v_id], v_id))

    if len(ordered_ids) != len(calls):
        rem = sorted(cid for cid, deg in in_degree.items() if deg > 0)
        raise TuChoi("DEPENDENCY_CYCLE", f"phụ thuộc vòng trong kế hoạch lời gọi {rem}", tuple(rem[:2]))

    k.calls = [by_id[cid] for cid in ordered_ids]


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
        if f.line_ref:
            ref = k.resolver.aliases.get(f.line_ref,f.line_ref)
            k.resolver.used = True
            k.resolver.lines.add(ref)
            if len(k.resolver.lines)>MAX_RESULT_LINES:
                raise TuChoi('PLAN_TOO_LARGE','quá trần line results')
            return phat(f.id, "orthogonal_projection_line", {"point": f.point, "line_ref": ref, "image": f.at}, q,
                        "projection(point, result line)")
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
    if f.kind == "section" and f.plane_relation:                     # mục tiêu: thiết diện với một mặt DỰNG từ quan hệ
        return _mat_qua_diem(f, q, k, phat, khoi_cua(f.solid, f).ten, "section")
    if f.kind == "section":                                         # dựng thiết diện: khối × mặt phẳng qua ba điểm có tên
        return phat(f.id, "section", {"solid": khoi_cua(f.solid, f).ten, "plane": f.points}, q, "section(solid, plane)")
    if f.kind == "intersection_line":
        return phat(f.id, "intersection_line", {"plane1": f.points_a, "plane2": f.points_b}, q, "intersection_line(plane, plane)")
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


_DIEN_TICH_THIET_DIEN = re.compile(r"diện tích\s+(?:của\s+)?thiết diện", re.IGNORECASE)
_DIEN_TICH_DA_GIAC = re.compile(r"(?i:diện tích)\s+(?:(?i:của)\s+)?(?:(?i:tam giác|tứ giác|hình|đa giác|mặt|đáy)|[A-Z])")


def _cau_hoi(f: TypedFact, q: list[str], k: KeHoach, khoi_cua, phat) -> dict:
    n = f.quantity
    # Diện tích THIẾT DIỆN chỉ khi câu hỏi gọi tên đúng đối tượng ấy ("diện tích (của) thiết diện"); "diện tích tam giác MAB"
    # có ô `solid` vẫn là đa giác; một dữ kiện hỏi CẢ HAI là mơ hồ (review 2, I2). Cổng nguồn kiểm lại cụm mặt cắt.
    hoi_td = any(_DIEN_TICH_THIET_DIEN.search(x) for x in q)
    if n == "area" and hoi_td and any(_DIEN_TICH_DA_GIAC.search(x) for x in q):
        raise TuChoi("AMBIGUOUS_FACT", f"{f.id}: một câu hỏi diện tích nêu cả thiết diện lẫn một đa giác — tách hai câu hỏi", (f.id,))
    if n == "area" and f.plane_relation and hoi_td and not f.negated and f.role == "question":
        return _mat_qua_diem(f, q, k, phat, khoi_cua(f.solid, f).ten, "ask_section_area")
    if f.plane_relation:
        raise TuChoi("UNSUPPORTED_CAPABILITY", f"{f.id}: mặt cho bằng quan hệ chỉ dùng cho thiết diện / diện tích thiết diện",
                     (f.id,))
    if n == "area" and f.solid and len(f.points or []) >= 3 and hoi_td:
        return phat(f.id, "ask_section_area", {"solid": khoi_cua(f.solid, f).ten, "plane": f.points}, q,
                    "question(area of section)")
    entries = [c for s in REGISTRY.values() for c in planning_contracts(s) if c.goal == n]
    if entries and f.role == 'question' and not f.negated and (
            f.point_kind is not None or len(f.points or []) <= max(len(c.effect.operands) for c in entries)):
        return k.resolver.goal(f, entries)
    if f.point_kind is not None:                       # distance from an unnamed, described point: one typed goal
        if f.role == "prove":
            raise TuChoi("GOAL_CLAUSE_NOT_PREMISE", f"{f.id}: điểm không tên chỉ cho câu hỏi được hỏi", (f.id,))
        if f.negated:
            raise TuChoi("NEGATED_CLAUSE", f"{f.id}: câu hỏi khoảng cách bị phủ định", (f.id,))
        b = list(dict.fromkeys(f.points_b or []))
        target = (("result", f.line_ref) if f.line_ref else ("named", tuple(sorted(b))) if len(b) == 2 else tuple(b[:3]))
        return k.resolver.distance(f, ("desc", f.point_kind, tuple(sorted(f.points))), target)
    if f.line_ref:
        return k.resolver.distance(f, f.points_a[0], ("result", f.line_ref))
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


def _mat_qua_diem(f: TypedFact, q: list[str], k: KeHoach, phat, khoi: str, fn: str) -> dict:
    """PHÂN RÃ MỤC TIÊU, độ sâu 1 (`MAT_SONG_SONG`): Section(khối, mặt qua M ∥ (Q)).

    Kiểu: Point M × Plane Q (≥ 3 nhãn) → Plane → Section. Phụ thuộc: M và Q đã có tên (cổng nguồn kiểm nhãn và mệnh đề
    định nghĩa) → hai điểm phụ = M tịnh tiến theo hai vectơ chỉ phương của (Q) → thiết diện qua (M, X₁, X₂). Engine kiểm
    hậu điều kiện độc lập (qua M, song song (Q), không trùng (Q), không phải mặt biên). Một mặt dẫn xuất chỉ dựng MỘT lần
    dù được dùng để dựng và để hỏi diện tích. Mặt qua một điểm VUÔNG GÓC với một mặt phẳng không duy nhất ⇒ từ chối."""
    if f.plane_relation == "perpendicular":
        raise TuChoi("PLANE_NOT_UNIQUE", f"{f.id}: mặt qua {f.point} vuông góc với ({''.join(f.points_b)}) có vô số — cần "
                     "thêm một ràng buộc để xác định duy nhất", (f.id,))
    if f.role not in ("premise", "question") or f.negated:
        raise TuChoi("UNSUPPORTED_CAPABILITY", f"{f.id}: mặt dựng từ quan hệ chỉ cho thiết diện được yêu cầu", (f.id,))
    two = f.plane_relation == "parallel_two_lines"
    rule = MAT_HAI_DUONG if two else MAT_SONG_SONG
    m, ref = f.point, list(dict.fromkeys(f.points_b))
    directions = [list(f.points_a), list(f.points_b)] if two else [[ref[0], ref[1]], [ref[0], ref[2]]] if len(ref) >= 3 else []
    if not two and len(ref) < 3:
        raise TuChoi("FACT_INCOMPLETE", f"{f.id}: mặt tham chiếu cần ít nhất ba điểm", (f.id,))
    if not two and m in ref:
        raise TuChoi("DERIVED_PLANE_IS_REFERENCE", f"{f.id}: {m} thuộc ({''.join(ref)}) — mặt qua {m} song song với nó là chính nó",
                     (f.id,))
    khoa = ((khoi, m, f.plane_name, frozenset(frozenset(v) for v in directions)) if two else (khoi, m, frozenset(ref)))
    d = k.derived_planes.get(khoa)
    if d is None:
        if len(k.derived_planes) >= MAX_DERIVED_PLANES:
            raise TuChoi("PLAN_TOO_LARGE", f"{f.id}: quá {MAX_DERIVED_PLANES} mặt dẫn xuất", (f.id,))
        xs = [ten for ten in _NHAN_PHU if ten not in k.taken][:2]
        if len(xs) < 2:
            raise TuChoi("PLAN_TOO_LARGE", f"{f.id}: hết nhãn điểm phụ", (f.id,))
        k.taken |= set(xs)
        dung, cids = {c["id"] for c in k.calls}, []
        for i, (x, v) in enumerate(zip(xs, directions), 1):
            cid = next(j for j in (f"{f.id}_plane{i}", *(f"{f.id}_plane{i}_{n}" for n in range(2, 1000)))
                       if j not in k.fact_ids | dung)
            phat(cid, "translate_point", {"point": m, "vector": v, "image": x}, q,
                 f"{rule}→translate_point (điểm phụ {x} = {m} + {v[0]}{v[1]}→)")
            k.trace[-1]["fact"] = f.id
            cids.append(cid)
        d = {"labels": xs, "rule": rule, "goal": f.id, "constructs": cids, "targets": [], "point": m,
             "parallel_to": ref, "solid": khoi, "quotes": list(dict.fromkeys(q)), "provenance": "DERIVED",
             "binding": "AUXILIARY"}
        if two:
            d.update(lines=directions, plane_name=f.plane_name)
        k.derived_planes[khoa] = d
        k.auxiliary.append(d)
    d["quotes"] = list(dict.fromkeys(d["quotes"] + q))
    c = phat(f.id, fn, {"solid": khoi, "plane": [m, *d["labels"]]}, d["quotes"], f"{rule}→{fn}")
    k.trace[-1]["fact"] = f.id
    d["targets"].append(f.id)
    for call in k.calls:                                  # một khai báo, một tập quote cho mọi lời gọi của nó
        if call["id"] in d["constructs"] + d["targets"]:
            call["source"]["quotes"] = list(d["quotes"])
    k.trace.append({"fact": f.id, "step": "decompose_goal", "rule": rule,
                    "goal": f"Section({khoi}, Plane({m} ∥ ({''.join(ref)})))",
                    "dependencies": ([f"VerifiedPoint {m}", *[f"VerifiedLine {''.join(v)}" for v in directions]] if two else
                                     [f"VerifiedPoint {m}", f"ParallelPlane({m}, {''.join(ref)})", f"{fn}({khoi})"]),
                    "calls": d["constructs"] + [f.id], "auxiliary": d["labels"],
                    "reason": f"mặt qua {m} và hai ảnh tịnh tiến theo " + ', '.join(''.join(v)+'→' for v in directions)
                              + " (IR sẵn có; engine kiểm các quan hệ trên hình đã dựng)",
                    "provenance": "DERIVED", "binding": "AUXILIARY"})
    return c


def _phan_ra(f: TypedFact, q: list[str], k: KeHoach, phat, p: str, dt: list[str]) -> dict:
    return k.resolver.distance(f, p, ("named", tuple(sorted(dt))))


@dataclass
class _Choice:
    fn: str | None
    env: dict
    inputs: list["_Choice"] = field(default_factory=list)
    existing: dict | None = None
    cost: int = 0
    contract: Any = None


def _loai(v) -> str | None:
    """Kind of a typed-need operand: a point (label, or `("desc", kind, operands)` for an unnamed described point), a line
    (`("named", (X, Y))` / `("result", fact_id)`) or a plane (≥ 3 labels)."""
    if isinstance(v, str) or (isinstance(v, tuple) and v[:1] == ("desc",)):
        return "Point"
    if isinstance(v, tuple) and len(v) == 2 and v[0] in ("named", "result"):
        return "Line"
    if isinstance(v, tuple) and len(v) >= 3 and all(isinstance(x, str) for x in v):
        return "Plane"
    return None


class _EffectResolver:
    """Bounded backward search over Registry effects. A need (kind + operands) is solved by every contract whose effect has
    that kind and kind-compatible operands — its inputs become sub-needs; a call already in the plan with the same effect
    is reused at cost 0; the cheapest choice wins (ties by function name, never by catalog order). Calls are WRITTEN from
    the winner's contract template (`registry.render_call`), so a function the planner never names can be used once its
    contract is registered. Proposed bindings are NEVER geometric truth: the gate and the engine re-check them."""

    def __init__(self, facts, plan, emit, text=""):
        self.facts = {f.id: f for f in facts}
        self.plan, self.emit, self.text = plan, emit, text
        self.needs = self.candidates = self.feet = self.depth_max = 0  # feet: every fresh point (feet, unnamed operands)
        self.trail: list[dict] = []
        self.quet = {"H"}                     # label stems already scanned in the text (`lap_ke_hoach` scans H itself)
        self.lines = set()
        self.used = False
        self.active = set()
        self.memo = {}
        groups = {}
        for f in facts:
            if (f.kind=='intersection_line' and f.role in ('premise','question') and not f.negated
                    and all(len(p or [])==3 and len(set(p))==3 for p in (f.points_a,f.points_b))):
                key=tuple(sorted((tuple(sorted(f.points_a)),tuple(sorted(f.points_b)))))
                groups.setdefault(key,[]).append(f.id)
        self.aliases = {fid:min(ids) for ids in groups.values() for fid in ids}

    def _resolve(self, kind, operands, depth=0):
        key = (kind, operands)
        if not kind.startswith('Answer') and key in self.memo:
            return self.memo[key]  # available producer binding only; Engine still verifies every given later
        self.needs += 1
        if self.needs > MAX_EFFECT_NEEDS:
            raise TuChoi("PLAN_TOO_LARGE", "quá trần typed needs")
        if key in self.active:
            raise TuChoi("DEPENDENCY_CYCLE", "typed need phụ thuộc chính nó")
        self.depth_max = max(self.depth_max, depth)
        if kind in ('Point', 'Line', 'Plane') and _loai(operands[0]) != kind:
            raise TuChoi('UNSUPPORTED_CAPABILITY', f'typed need {kind} không khớp kiểu toán hạng')
        if kind == 'Plane' or (kind == 'Point' and isinstance(operands[0], str)):
            if not all(p in self.plan.taken for p in (operands[0] if kind == 'Plane' else operands)):
                raise TuChoi('UNSUPPORTED_CAPABILITY', f'typed need {kind} không khớp kiểu toán hạng')
            return _Choice(None, {})
        if kind == "Line" and operands[0][0] == "named":
            return _Choice(None, {})
        if depth >= MAX_EFFECT_DEPTH:
            raise TuChoi("PLAN_TOO_LARGE", "quá trần phân rã effect")
        self.active.add(key)
        choices = []
        try:
            contracts = [(s,c) for s in sorted(REGISTRY.values(), key=lambda s: s.name) for c in planning_contracts(s)]
            for spec, contract in contracts:
                if contract.effect.kind != kind or len(contract.effect.operands) != len(operands):
                    continue
                desc = operands[0] if kind == 'Point' else None      # an unnamed point: only producers of its description
                if desc and (contract.descriptor != desc[1] or len(contract.inputs) != len(desc[2])):
                    continue
                typed = {t.operands[0]: t.kind for t in contract.inputs if t.kind in ('Point', 'Line', 'Plane')}
                if any(v is not None and typed.get(s, _loai(v)) != _loai(v) for s, v in zip(contract.effect.operands, operands)):
                    continue  # an operand of the wrong kind is not a candidate; excluded before it is counted
                self.candidates += 1
                if self.candidates > MAX_EFFECT_CANDIDATES:
                    raise TuChoi("PLAN_TOO_LARGE", "quá trần candidate")
                env = dict(zip(contract.effect.operands, operands))
                if desc:
                    env.update(zip((t.operands[0] for t in contract.inputs), desc[2]))
                existing = None
                if contract.source_policy == "declared_intersection":
                    ref = env["L"][1]
                    producer = self.facts[ref]
                    env.update(A=tuple(producer.points_a), B=tuple(producer.points_b))
                    existing = next((c for c in self.plan.calls if c['id'] == ref and c['fn'] == spec.name), None)
                    if existing is None:
                        continue
                    self.lines.add(ref)
                    if len(self.lines) > MAX_RESULT_LINES:
                        raise TuChoi("PLAN_TOO_LARGE", "quá trần line results")
                try:
                    children = [self._resolve(term.kind, tuple(env.get(slot) for slot in term.operands), depth+1)
                                for term in contract.inputs]
                except TuChoi as e:
                    if e.code=='UNSUPPORTED_CAPABILITY':
                        continue  # exclude incompatible symbolic candidates; never skip a geometric/source failure
                    raise
                cost = sum(c.cost for c in children)
                if contract.fresh:              # the source (or an earlier goal) may already hold this exact construction
                    out = contract.effect.operands[0]
                    arg = next(a for a, s in contract.call if s == out)
                    for c in self.plan.calls:
                        if c['fn'] != spec.name:
                            continue
                        bound = {**env, out: c['args'].get(arg)}
                        if same_call(contract, render_call(contract, bound), c['args']):
                            self.candidates += 1
                            if self.candidates > MAX_EFFECT_CANDIDATES:
                                raise TuChoi('PLAN_TOO_LARGE','quá trần available-binding candidates')
                            choices.append(_Choice(spec.name, bound, children, c, cost, contract))
                    cost += 1
                choices.append(_Choice(spec.name, env, children, existing, cost, contract))
            if not choices:
                raise TuChoi("UNSUPPORTED_CAPABILITY", f"không effect nào giải được {kind}")
            selected = min(choices, key=lambda c: (c.cost, c.fn, _nhan_ra(c), c.existing['id'] if c.existing else ''))
            if not kind.startswith('Answer'):
                self.memo[key]=selected
            return selected
        finally:
            self.active.remove(key)

    def _emit(self, choice, fact):
        if choice.fn is None:
            return choice.env
        contract = choice.contract
        env = dict(choice.env)
        for t, child in zip(contract.inputs, choice.inputs):  # an input slot takes its producer's effect, by position
            got = self._emit(child, fact)
            if child.fn is not None:
                env.update({s: got[c] for s, c in zip(t.operands, child.contract.effect.operands)})
        if choice.existing:
            self._ghi(choice.existing, env, contract)
            return env
        if not contract.call:
            raise TuChoi('UNSUPPORTED_CAPABILITY', 'producer chưa được khai trong nguồn')
        answer = contract.effect.kind.startswith('Answer')
        if contract.fresh:
            self.feet += 1
            if self.feet > MAX_RESULT_FEET:
                raise TuChoi("PLAN_TOO_LARGE", "quá trần điểm tươi")
            if contract.fresh not in self.quet:
                self.quet.add(contract.fresh)
                self.plan.taken |= nhan_phu_da_dung(self.text, contract.fresh)
            x = next((n for n in _nhan_tuoi(contract.fresh) if n not in self.plan.taken), None)
            if x is None:
                raise TuChoi("PLAN_TOO_LARGE", "hết nhãn điểm phụ")
            self.plan.taken.add(x)
            env[contract.effect.operands[0]] = x
        cid = fact.id if answer else next(i for i in (f'{fact.id}_aux', *(f'{fact.id}_aux{n}' for n in range(2,1000)))
                                          if i not in self.plan.fact_ids | {c['id'] for c in self.plan.calls})
        call = self.emit(cid, choice.fn, render_call(contract, env), fact.quotes, f'effect({contract.effect.kind})→{choice.fn}')
        self.plan.trace[-1]['fact'] = fact.id
        self._ghi(call, env, contract)
        if not answer:
            choice.env.update(env)
            choice.existing, choice.cost = call, 0
        return env

    def _ghi(self, call, env, contract):
        """Trail of the goal being resolved: the calls of its derivation, each with the slot bindings it was written from."""
        if all(e['call'] != call['id'] for e in self.trail):
            self.trail.append({'call': call['id'], 'fn': call['fn'], 'env': json.loads(json.dumps(env)),
                               'fresh': call['id'] not in self.plan.fact_ids})
            if contract is not REGISTRY[call['fn']].planning:
                self.trail[-1]['effect'] = contract.effect.kind

    def goal(self, fact, entries):
        """Typed semantic entry: quantity selects a contract effect; operands carry no function recipe."""
        kinds = {c.effect.kind for c in entries}
        if len(kinds) != 1:
            raise TuChoi('AMBIGUOUS_FACT', 'mục tiêu có nhiều cách hiểu kiểu', (fact.id,))
        if fact.point_kind:
            operands = (('desc', fact.point_kind, tuple(sorted(fact.points))), *fact.points_b)
        else:
            operands = tuple(fact.points or (fact.points_a or []) + (fact.points_b or []))
        if not any(len(c.effect.operands) == len(operands) for c in entries):
            raise TuChoi('FACT_INCOMPLETE', 'số toán hạng không khớp hợp đồng mục tiêu', (fact.id,))
        self.used, self.trail = True, []
        choice = self._resolve(next(iter(kinds)), operands)
        env = self._emit(choice, fact)
        if fact.point_kind:
            target = operands[1] if len(operands) == 2 else ('points', operands[1:])
            return self._chuoi(fact, operands[0], target, choice, env)
        return next(c for c in self.plan.calls if c['id'] == fact.id)

    def distance(self, fact, point, line):
        self.used = True
        if line[0]=='result':
            line=('result',self.aliases.get(line[1],line[1]))
        self.trail = []
        choice = self._resolve('AnswerDistance', (point,line))
        env = self._emit(choice, fact)
        if not isinstance(point, str):
            return self._chuoi(fact, point, line, choice, env)
        foot = next((c for c in self.plan.calls if c['fn']=='orthogonal_projection_line'
                     and c['args']['point']==point and c['args']['image']==env.get('F')), None)
        if foot is None:                                  # a resolution that wrote no foot is refused, never a crash
            raise TuChoi('AUXILIARY_RULE_MISMATCH', f'{fact.id}: phân giải không viết chân vuông góc', (fact.id,))
        cert = {'label':env['F'], 'rule':'distance(point,line)', 'goal':fact.id, 'construct':foot['id'], 'ask':fact.id,
                'point':point, 'line':list(line[1]) if line[0]=='named' else [],
                'quotes':list(dict.fromkeys(fact.quotes)), 'provenance':'DERIVED', 'binding':'AUXILIARY'}
        # Preserve the old source certificate for a fresh named-line foot; reuse that validator instead of duplicating it.
        if line[0]=='result' or choice.cost==0:
            cert.update(line_ref=line[1] if line[0]=='result' else None,
                        fresh=foot['id'] not in self.plan.fact_ids,effect_binding=True)
        self.plan.auxiliary.append(cert)
        self.plan.trace.append({'fact':fact.id,'step':'decompose_goal','rule':cert['rule'],
                                'calls':[foot['id'],fact.id], 'auxiliary':env['F'],
                                'provenance':'DERIVED','binding':'AUXILIARY'})
        self.plan.trace.append({'fact':fact.id,'step':'effect_resolution','selection':'registry-effects',
                                'new_constructions':choice.cost})
        return next(c for c in self.plan.calls if c['id']==fact.id)

    def _chuoi(self, fact, point, target, choice, env):
        """`effect-chain` certificate of a goal on an unnamed described point: the trail of calls with their bindings, the
        goal (description + target) and the fresh labels. The gate re-writes every call from its contract; the engine checks
        the description and the answer on the built figure."""
        answer = choice.contract
        fresh = [e for e in self.trail if e['fresh'] and REGISTRY[e['fn']].planning and REGISTRY[e['fn']].planning.fresh]
        cert = {'rule': 'effect-chain', 'effect_binding': True, 'goal': fact.id, 'ask': fact.id,
                'operand': {'descriptor': point[1], 'points': list(fact.points), 'label': env[answer.effect.operands[0]]},
                'target': ({'point': target} if isinstance(target, str)
                           else {'points': list(target[1])} if target[0] == 'points'
                           else {'line_ref': target[1]} if target[0] == 'result'
                           else {'line': list(target[1])} if target[0] == 'named'
                           else {'plane': list(target)}),
                'chain': self.trail,
                'labels': [e['env'][REGISTRY[e['fn']].planning.effect.operands[0]] for e in fresh],
                'quotes': list(dict.fromkeys(fact.quotes)), 'provenance': 'DERIVED', 'binding': 'AUXILIARY'}
        if not isinstance(target, str) and target[0] == 'result':
            cert['line_ref'] = target[1]
        self.plan.auxiliary.append(cert)
        self.plan.trace.append({'fact': fact.id, 'step': 'decompose_goal', 'rule': cert['rule'],
                                'calls': [e['call'] for e in self.trail], 'auxiliary': cert['labels'],
                                'provenance': 'DERIVED', 'binding': 'AUXILIARY'})
        self.plan.trace.append({'fact': fact.id, 'step': 'effect_resolution', 'selection': 'registry-effects',
                                'new_constructions': len([e for e in self.trail if e['fresh'] and e['call'] != fact.id]),
                                'needs': self.needs, 'candidates': self.candidates, 'depth': self.depth_max})
        return next(c for c in self.plan.calls if c['id'] == fact.id)


def _nhan_ra(c: _Choice) -> str:
    """Output label of an available-binding choice (tie-break); '' for a new construction or an answer."""
    contract = c.contract
    x = c.env.get(contract.effect.operands[0]) if contract.fresh else None
    return x if isinstance(x, str) else ''


def _bind_result_dependencies(k):
    """Call edges are a view of the existing producers, not another FactGraph."""
    producers = {}
    for c in k.calls:
        a, fn = c['args'], c['fn']
        label = (a.get('image') if fn in ('orthogonal_projection_line','orthogonal_projection','translate_point')
                 else a.get('point') if fn in ('midpoint','centroid','intersect_line_line','intersect_line_plane') else None)
        if label:
            producers.setdefault(label, []).append(c['id'])
    for c in k.calls:
        a = c['args']
        points = [x for v in a.values() if isinstance(v,list) for x in v]
        if c['fn'].startswith('orthogonal_projection') or c['fn']=='translate_point' or c['fn'].startswith('ask_'):
            points += [a['point']] if isinstance(a.get('point'), str) else []
        output = a.get('image') or (a.get('point') if c['fn'] in ('midpoint','centroid','intersect_line_line','intersect_line_plane') else None)
        if output:
            points = [x for x in points if x != output]
        deps = {p for x in points for p in producers.get(x,()) if p != c['id']}
        if a.get('line_ref'):
            deps.add(a['line_ref'])
        c['depends_on'] = sorted(deps)
    doc_ke_hoach({'calls':k.calls})  # existing cycle/dangling/type authority
