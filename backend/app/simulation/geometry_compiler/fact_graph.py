# -*- coding: utf-8 -*-
"""GEOMETRY FACT GRAPH — biểu diễn trung gian CÓ KIỂU giữa đề và chương trình.

`GEOMETRY_FACT_GRAPH_AND_PRIMITIVE_COMPILER_VERTICAL_SLICE` (2026-09-20).

Đây là tầng mà `RequestContract` (thứ LLM khai) được dịch sang **sự kiện hình học
có kiểu**, để một compiler TẤT ĐỊNH đọc được. Nó KHÔNG phải một DSL thứ hai:
nó không chạy được, không vẽ được, không đo được. Nó chỉ nói *đề cho những gì*.

─── BA LUẬT CỐT LÕI ────────────────────────────────────────────────────────

① **Toạ độ KHÔNG BAO GIỜ là dữ kiện đề.** Mọi toạ độ do compiler chọn mang
   `LAYOUT_DERIVED`. Ghi chúng thành `GIVEN` là biến một lựa chọn trình bày
   thành một lời khai về đề bài — đúng thứ `geometry_analyze.md` đã cấm
   (*"Hệ toạ độ KHÔNG phải dữ kiện"*).

② **Không mất `source_fact_id`.** Mỗi fact `GIVEN` phải truy được về đúng mục
   dữ kiện của đề, nếu không cổng grounding phía sau không có gì để ghim.

③ **Chính tắc và tất định.** Cùng một hợp đồng ⇒ cùng một JSON, từng byte, bất
   kể thứ tự đầu vào. Thứ tự các mục trong `source_invariants` là chi tiết của
   lượt `analyze`, không mang nghĩa hình học.

KHÔNG chứa: raw prompt · ảnh · `problem_text` · giá trị kỳ vọng của đáp số.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

FACT_GRAPH_VERSION = "geometry-fact-graph/1"

#: Loại NÚT. Bảng ĐÓNG — thêm loại là đổi hợp đồng, phải tăng phiên bản.
LOAI_NUT: tuple[str, ...] = (
    "point", "segment", "plane", "triangle", "pyramid", "measurement_request",
)

#: Loại SỰ KIỆN. Bảng ĐÓNG.
LOAI_FACT: tuple[str, ...] = (
    "incidence",
    "length",
    "perpendicular",
    "right_angle",
    "base_of",
    "apex_of",
    "lies_in_plane",
    "requested_operation",
)

#: Trạng thái của một fact. `GIVEN` = đề cho; `DERIVED` = tầng sau suy ra.
TRANG_THAI_FACT: tuple[str, ...] = ("GIVEN", "DERIVED")

#: Trạng thái xuất xứ của một NÚT. `LAYOUT_DERIVED` là toạ độ do compiler chọn —
#: xem luật ① ở đầu tệp.
XUAT_XU_NUT: tuple[str, ...] = ("GIVEN", "DERIVED", "LAYOUT_DERIVED")


@dataclass(frozen=True)
class Nut:
    """Một đối tượng hình học được NHẮC TỚI trong đề."""

    node_id: str
    kind: str
    #: Tên các nút thành phần, theo thứ tự có nghĩa (đỉnh của tam giác…).
    args: tuple[str, ...] = ()
    provenance: str = "GIVEN"

    def chinh_tac(self) -> dict[str, Any]:
        return {"node_id": self.node_id, "kind": self.kind,
                "args": list(self.args), "provenance": self.provenance}


@dataclass(frozen=True)
class Fact:
    """Một mệnh đề hình học có kiểu."""

    fact_id: str
    kind: str
    args: tuple[str, ...]
    #: Giá trị CHÍNH XÁC dạng chuỗi phân số (`"3"`, `"4/5"`) — không `float`.
    value: str | None = None
    #: Truy về đúng mục dữ kiện của đề. `None` chỉ hợp lệ với fact `DERIVED`.
    source_fact_id: str | None = None
    status: str = "GIVEN"

    def chinh_tac(self) -> dict[str, Any]:
        return {"fact_id": self.fact_id, "kind": self.kind, "args": list(self.args),
                "value": self.value, "source_fact_id": self.source_fact_id,
                "status": self.status}


class MauThuanFact(Exception):
    """Hai fact `GIVEN` nói hai điều không thể cùng đúng."""

    def __init__(self, ma: str, chi_tiet: str) -> None:
        super().__init__(chi_tiet)
        self.ma = ma
        self.chi_tiet = chi_tiet


@dataclass(frozen=True)
class GeometryFactGraph:
    nodes: tuple[Nut, ...]
    facts: tuple[Fact, ...]
    version: str = FACT_GRAPH_VERSION

    # ── CHÍNH TẮC HOÁ ────────────────────────────────────────────────────
    #
    # Sắp theo KHOÁ NGỮ NGHĨA (loại, args, id), không theo thứ tự đầu vào. Đó là
    # toàn bộ lý do `test_C` (đảo thứ tự facts) không làm đổi băm.
    def chinh_tac(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "nodes": [n.chinh_tac() for n in
                      sorted(self.nodes, key=lambda n: (n.kind, n.args, n.node_id))],
            "facts": [f.chinh_tac() for f in
                      sorted(self.facts, key=lambda f: (f.kind, f.args, f.fact_id))],
        }

    def json_chinh_tac(self) -> str:
        return json.dumps(self.chinh_tac(), sort_keys=True, ensure_ascii=False,
                          separators=(",", ":"))

    def graph_hash(self) -> str:
        return hashlib.sha256(self.json_chinh_tac().encode("utf-8")).hexdigest()

    # ── TRA CỨU ──────────────────────────────────────────────────────────
    def nut_theo_loai(self, kind: str) -> tuple[Nut, ...]:
        return tuple(n for n in self.nodes if n.kind == kind)

    def fact_theo_loai(self, kind: str) -> tuple[Fact, ...]:
        return tuple(f for f in self.facts if f.kind == kind)

    def do_dai(self, a: str, b: str) -> Fact | None:
        khoa = tuple(sorted((a, b)))
        for f in self.fact_theo_loai("length"):
            if tuple(sorted(f.args)) == khoa:
                return f
        return None


def _phan_so(v: str | None) -> Fraction | None:
    try:
        return Fraction(v) if v is not None else None
    except (ValueError, ZeroDivisionError):
        return None


def kiem_mau_thuan(facts: tuple[Fact, ...]) -> None:
    """Phát hiện fact `GIVEN` mâu thuẫn. Ném `MauThuanFact`, KHÔNG nuốt.

    Hai lớp, và chúng khác nhau về ý nghĩa nên khác nhau về mã:
      · cùng một đoạn, hai độ dài khác nhau ⇒ `INVALID_CONFLICT`
      · một quan hệ vừa được khai vừa bị phủ định ⇒ `INVALID_CONFLICT`
    """
    theo_doan: dict[tuple[str, ...], set[str]] = {}
    for f in facts:
        if f.kind != "length" or f.status != "GIVEN":
            continue
        khoa = tuple(sorted(f.args))
        gt = _phan_so(f.value)
        if gt is None:
            continue
        theo_doan.setdefault(khoa, set()).add(str(gt))
    for khoa, gts in sorted(theo_doan.items()):
        if len(gts) > 1:
            raise MauThuanFact(
                "INVALID_CONFLICT",
                f"đoạn {'-'.join(khoa)} được khai {len(gts)} độ dài khác nhau")

    thay: dict[tuple[str, tuple[str, ...]], set[str]] = {}
    for f in facts:
        if f.kind not in ("perpendicular", "right_angle") or f.status != "GIVEN":
            continue
        thay.setdefault((f.kind, tuple(f.args)), set()).add(f.value or "TRUE")
    for (kind, args), gts in sorted(thay.items()):
        if len(gts) > 1:
            raise MauThuanFact(
                "INVALID_CONFLICT",
                f"quan hệ {kind} trên {'-'.join(args)} vừa được khẳng định vừa bị phủ định")


#: Fact `GIVEN` được phép KHÔNG có `source_fact_id`: nó dẫn từ `obligations`,
#: vốn là cấu trúc của hợp đồng chứ không phải một mục dữ kiện.
_GIVEN_KHONG_CAN_NGUON = frozenset({"requested_operation"})


def kiem_xuat_xu(facts: tuple[Fact, ...]) -> None:
    """Mọi fact `GIVEN` phải TRUY ĐƯỢC về đề. Ném `MauThuanFact` nếu không.

    ⚠️ Luật này sinh ra vì một phép tiêm lỗi ĐI LỌT: ghi toạ độ do bố cục chọn
    vào graph dưới nhãn `GIVEN` mà không test nào đỏ. Một toạ độ `GIVEN` là lời
    khai *"đề đã cho con số này"* — trong khi `geometry_analyze.md` nói thẳng
    *"Hệ toạ độ KHÔNG phải dữ kiện"*. Ở đây nó thành điều kiểm được.
    """
    for f in facts:
        if f.status != "GIVEN" or f.kind in _GIVEN_KHONG_CAN_NGUON:
            continue
        if not f.source_fact_id:
            raise MauThuanFact(
                "GIVEN_FACT_WITHOUT_SOURCE",
                f"fact `{f.kind}` mang GIVEN nhưng không truy được về mục dữ "
                "kiện nào — toạ độ do bố cục chọn phải là DERIVED")


def dung_graph(nodes: tuple[Nut, ...], facts: tuple[Fact, ...]) -> GeometryFactGraph:
    """Dựng graph SAU khi đã kiểm mâu thuẫn VÀ kiểm xuất xứ. Không có đường bẩn."""
    kiem_mau_thuan(facts)
    kiem_xuat_xu(facts)
    return GeometryFactGraph(nodes=nodes, facts=facts)
