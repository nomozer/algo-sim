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

FACT_GRAPH_VERSION = "geometry-fact-graph/2"

#: Loại NÚT. Bảng ĐÓNG — thêm loại là đổi hợp đồng, phải tăng phiên bản.
LOAI_NUT: tuple[str, ...] = (
    "point", "segment", "plane", "triangle", "pyramid", "measurement_request",
)

#: Loại SỰ KIỆN. Bảng ĐÓNG.
#:
#: ⚠️ `/2` (`FACT_GRAPH_CONTRACT_EXTENSION`) **THAY** `perpendicular` và
#: `right_angle` bằng hai loại có kiểu dưới đây. Giữ cả bốn là để hai cách nói
#: về cùng một sự thật cùng sống trong một bảng — đúng thứ `CLAUDE.md §2b` mục 2
#: cấm, và tầng dựng sẽ phải chọn tin cái nào.
LOAI_FACT: tuple[str, ...] = (
    "incidence",
    "length",
    #: `line(P₁,P₂) ⟂ line(P₃,P₄)` — `args` = hai đường đã chuẩn hoá, nối lại.
    "perpendicular_lines",
    #: `line(P₁,P₂) ⟂ plane(P₃,P₄,P₅)` — `args` = đường (2) + mặt phẳng (3).
    "perpendicular_line_plane",
    "base_of",
    "apex_of",
    "lies_in_plane",
    "requested_operation",
)

#: Loại quan hệ VUÔNG GÓC — dùng chung cho phép kiểm mâu thuẫn và cho tầng dựng,
#: nên không có chỗ nào chép lại bảng này rồi quên một dòng.
LOAI_VUONG_GOC: tuple[str, ...] = (
    "perpendicular_lines", "perpendicular_line_plane",
)

#: Mã từ chối khi các quan hệ CÓ CẤU TRÚC tự mâu thuẫn, và luật cụ thể đã bắt nó.
MA_MAU_THUAN_QUAN_HE = "STRUCTURED_RELATION_CONTRADICTION"
LUAT_NHIEU_DINH_VUONG = "MULTIPLE_RIGHT_ANGLE_VERTICES_IN_TRIANGLE"

#: Mọi mã mà tầng sau phải đọc là "dữ kiện tự mâu thuẫn" ⇒ TỪ CHỐI, không lùi về
#: LLM (lùi về là mời mô hình chọn một nửa mâu thuẫn). Bảng DUY NHẤT — định tuyến
#: đọc nó, không chép lại.
MA_MAU_THUAN: frozenset[str] = frozenset({"INVALID_CONFLICT", MA_MAU_THUAN_QUAN_HE})

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
    #: CHỨNG MINH của một fact `DERIVED` — `fact_id` của các fact cha.
    #:
    #: Thêm ở `/2`. Không có nó thì `SA ⟂ AB` suy từ `SA ⟂ (ABC)` trông y hệt
    #: `SA ⟂ AB` do đề cho: cùng kiểu, cùng args, cùng `DERIVED`, và không ai
    #: đọc ngược được *suy từ đâu*. Một suy diễn không nêu được cha của nó thì
    #: về giá trị bằng một lời khai.
    derived_from: tuple[str, ...] = ()

    def chinh_tac(self) -> dict[str, Any]:
        return {"fact_id": self.fact_id, "kind": self.kind, "args": list(self.args),
                "value": self.value, "source_fact_id": self.source_fact_id,
                "status": self.status, "derived_from": list(self.derived_from)}


class MauThuanFact(Exception):
    """Hai fact `GIVEN` nói hai điều không thể cùng đúng.

    `rule_id`, `chan_doan` và `bang_chung` là TỪ VỰNG ĐÓNG — không nhãn điểm thô,
    không câu chữ của đề — để tầng sau ghi được mà không rò nội dung.
    """

    def __init__(self, ma: str, chi_tiet: str, *, rule_id: str | None = None,
                 chan_doan: tuple[str, ...] = (),
                 bang_chung: tuple[tuple[str, str], ...] = ()) -> None:
        super().__init__(chi_tiet)
        self.ma = ma
        self.chi_tiet = chi_tiet
        self.rule_id = rule_id
        self.chan_doan = chan_doan
        self.bang_chung = bang_chung


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

    Ba lớp, và chúng khác nhau về ý nghĩa nên khác nhau về mã:
      · cùng một đoạn, hai độ dài khác nhau ⇒ `INVALID_CONFLICT`
      · một quan hệ vừa được khai vừa bị phủ định ⇒ `INVALID_CONFLICT`
      · một tam giác vuông ở HAI đỉnh trở lên ⇒ `STRUCTURED_RELATION_CONTRADICTION`
        (luật `MULTIPLE_RIGHT_ANGLE_VERTICES_IN_TRIANGLE`, xem `_kiem_nhieu_dinh_vuong`)
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
        if f.kind not in LOAI_VUONG_GOC or f.status != "GIVEN":
            continue
        thay.setdefault((f.kind, tuple(f.args)), set()).add(f.value or "TRUE")
    for (kind, args), gts in sorted(thay.items()):
        if len(gts) > 1:
            raise MauThuanFact(
                "INVALID_CONFLICT",
                f"quan hệ {kind} trên {'-'.join(args)} vừa được khẳng định vừa bị phủ định")

    _kiem_nhieu_dinh_vuong(facts)


def _goc_vuong(f: Fact) -> tuple[frozenset[str], str] | None:
    """`(tam giác, đỉnh)` nếu `f` khẳng định MỘT góc vuông của một tam giác; không thì `None`.

    `AB ⟂ AC` — hai đường, mỗi đường hai điểm phân biệt, chung ĐÚNG một điểm A —
    là góc vuông tại A của tam giác {A, B, C}. Đọc bằng TẬP điểm, không bằng vị
    trí trong `args`, nên đảo đầu mút cạnh hay đảo thứ tự hai đường không tạo ra
    một góc mới. Hai đường không chung điểm (`SA ⟂ BC`, chéo nhau) không phải
    một góc của tam giác nào.
    """
    if f.kind != "perpendicular_lines" or len(f.args) != 4 or (f.value or "TRUE") != "TRUE":
        return None
    d1, d2 = set(f.args[:2]), set(f.args[2:])
    if len(d1) != 2 or len(d2) != 2:
        return None
    chung = d1 & d2
    if len(chung) != 1:
        return None
    return frozenset(d1 | d2), next(iter(chung))


def _kiem_nhieu_dinh_vuong(facts: tuple[Fact, ...]) -> None:
    """Một tam giác không thể vuông ở hai đỉnh — `MULTIPLE_RIGHT_ANGLE_VERTICES_IN_TRIANGLE`.

    Với ba điểm PHÂN BIỆT A, B, C: `AB ⟂ AC` và `BA ⟂ BC` làm tổng hai góc của tam
    giác ABC bằng 180°; còn nếu A, B, C thẳng hàng thì không đường nào trong số
    đó vuông góc được. Hai quan hệ ấy nhắc ĐỦ ba cạnh AB, AC, BC, nên chính chúng
    xác định tam giác — không cần một nút `triangle` (adapter không dựng nút ấy).

    Chỉ tính fact TIN ĐƯỢC: `GIVEN`, hoặc `DERIVED` nêu được cha. Giả định của mô
    hình không bao giờ tới đây — adapter đã loại nó (`RELATION_NOT_GROUNDED`).
    Không đọc nhãn cụ thể, không đọc câu chữ: luật chạy trên tập điểm.
    """
    theo_tam_giac: dict[frozenset[str], dict[str, list[Fact]]] = {}
    for f in facts:
        if not (f.status == "GIVEN" or (f.status == "DERIVED" and f.derived_from)):
            continue
        g = _goc_vuong(f)
        if g is None:
            continue
        tam_giac, dinh = g
        theo_tam_giac.setdefault(tam_giac, {}).setdefault(dinh, []).append(f)
    for tam_giac in sorted(theo_tam_giac, key=sorted):
        dinh = theo_tam_giac[tam_giac]
        if len(dinh) < 2:
            continue
        cac_fact = [f for fs in dinh.values() for f in fs]
        so = str(len(dinh))
        raise MauThuanFact(
            MA_MAU_THUAN_QUAN_HE,
            f"{LUAT_NHIEU_DINH_VUONG}: một tam giác được khai vuông tại {so} đỉnh phân biệt",
            rule_id=LUAT_NHIEU_DINH_VUONG,
            chan_doan=(f"DISTINCT_RIGHT_ANGLE_VERTEX_COUNT={so}", "PHASE=FACT_GRAPH",
                       f"RULE_ID={LUAT_NHIEU_DINH_VUONG}"),
            bang_chung=(
                ("RULE_ID", LUAT_NHIEU_DINH_VUONG),
                ("PHASE", "FACT_GRAPH"),
                ("TRIANGLE_SHA256",
                 hashlib.sha256("|".join(sorted(tam_giac)).encode("utf-8")).hexdigest()),
                ("DISTINCT_RIGHT_ANGLE_VERTEX_COUNT", so),
                ("SOURCE_FACT_IDS", ",".join(sorted({f.source_fact_id for f in cac_fact
                                                     if f.source_fact_id}))),
                ("DERIVED_FACTS_INVOLVED", str(sum(1 for f in cac_fact if f.status == "DERIVED"))),
            ))


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
    co = {f.fact_id for f in facts}
    for f in facts:
        if f.status == "GIVEN":
            if f.kind in _GIVEN_KHONG_CAN_NGUON:
                continue
            if not f.source_fact_id:
                raise MauThuanFact(
                    "GIVEN_FACT_WITHOUT_SOURCE",
                    f"fact `{f.kind}` mang GIVEN nhưng không truy được về mục "
                    "dữ kiện nào — toạ độ do bố cục chọn phải là DERIVED")
            continue

        # ── DERIVED: quan hệ suy ra phải NÊU ĐƯỢC CHA (`/2`) ────────────────
        #
        # Chỉ ép với quan hệ vuông góc, và có chủ đích: đó là loại fact mà một
        # lời khai và một suy diễn có **cùng hình dạng**, nên không nêu cha thì
        # không ai phân biệt nổi. Toạ độ `LAYOUT_DERIVED` thì khác — chúng là
        # lựa chọn trình bày của compiler, không phải mệnh đề về đề bài.
        if f.kind not in LOAI_VUONG_GOC:
            continue
        if not f.derived_from:
            raise MauThuanFact(
                "DERIVED_RELATION_WITHOUT_PROOF",
                f"quan hệ `{f.kind}` mang DERIVED nhưng không nêu fact cha nào")
        thieu = sorted(p for p in f.derived_from if p not in co)
        if thieu:
            raise MauThuanFact(
                "DERIVED_RELATION_PARENT_MISSING",
                f"quan hệ `{f.kind}` trỏ tới fact cha không có trong graph")


def dung_graph(nodes: tuple[Nut, ...], facts: tuple[Fact, ...]) -> GeometryFactGraph:
    """Dựng graph SAU khi đã kiểm mâu thuẫn VÀ kiểm xuất xứ. Không có đường bẩn."""
    kiem_mau_thuan(facts)
    kiem_xuat_xu(facts)
    return GeometryFactGraph(nodes=nodes, facts=facts)
