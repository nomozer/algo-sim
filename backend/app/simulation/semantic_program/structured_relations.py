# -*- coding: utf-8 -*-
"""QUAN HỆ HÌNH HỌC CÓ CẤU TRÚC — dữ kiện có kiểu, có tham chiếu, có xuất xứ.

`FACT_GRAPH_CONTRACT_EXTENSION` (2026-09-20).

─── KHOẢNG TRỐNG NÓ ĐÓNG ───────────────────────────────────────────────────

Trước bản này, *"AB ⟂ AC"* và *"SA ⟂ (ABC)"* chỉ sống trong `InputFact.values`
dưới dạng **một câu tiếng Việt**. Compiler tất định vì thế phải đọc câu chữ, và
đo được ba hệ quả:

  · cùng một quan hệ, hai cách viết ⇒ hai FactGraph khác nhau;
  · một câu có chữ *"vuông góc"* là đủ để compiler nhận bài, dù không ai khai
    quan hệ ấy như một dữ kiện;
  · không phân biệt được *đề cho* với *mô hình tự giả định*.

Ở đây quan hệ thành **dữ kiện có kiểu**: hai đầu mút là tham chiếu điểm kiểm
được, xuất xứ là `source_fact_id`, và giả định của mô hình mang cờ riêng.

─── VÌ SAO KHÔNG NHÉT VÀO `SourceInvariant` ────────────────────────────────

`SourceInvariant` do **SERVER** phát, từ chính câu văn của đề (7/7 điểm phát là
server-side; không điểm nào do mô hình viết), và được tiêu thụ như **hậu điều
kiện** — `NormalizedSourceInvariantGate` kiểm nó trên trạng thái CUỐI.

Quan hệ ở đây là **tiền đề** cho tầng dựng, và nó **không được phép** sinh ra từ
việc đọc câu văn: nếu server tự trích *"SA vuông góc (ABC)"* thành quan hệ thì
trạng thái *"đề có chữ vuông góc nhưng không ai khai quan hệ"* trở nên bất khả —
và đó đúng là trạng thái tầng dựng phải phân biệt được. Trộn hai vai vào một
collection là đổi nghĩa của cổng hậu điều kiện.

Xem `CONTRACT_EXTENSION_AUDIT.json` để biết hai phương án còn lại bị loại vì sao.

─── LUẬT CHUẨN HOÁ ─────────────────────────────────────────────────────────

`AB` và `BA` là MỘT đường thẳng; mọi hoán vị của `A, B, C` là MỘT mặt phẳng.
Chuẩn hoá bằng cách sắp tên — không phụ thuộc thứ tự mô hình viết ra, không phụ
thuộc nhãn cụ thể, và hai lần chuẩn hoá cho kết quả trùng byte.

KHÔNG BAO GIỜ: đọc `problem_text` · suy quan hệ từ tên điểm · tự bù một quan hệ
thiếu · nâng một giả định chưa xác nhận thành dữ kiện đề cho.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ConfigDict

#: Hai loại quan hệ hợp đồng biểu diễn được. Bảng **ĐÓNG** — thêm loại là đổi
#: bề mặt mô hình, kéo theo cả nhịp đo lại (`CLAUDE.md §2b`).
RELATION_KINDS: tuple[str, ...] = (
    "perpendicular_lines",
    "perpendicular_line_plane",
)

#: Số nhãn điểm của mỗi vai. Một chỗ khai, mọi nơi đọc — để phép kiểm arity
#: không bị chép ra hai bản rồi lệch.
SO_DIEM_DUONG = 2
SO_DIEM_MAT = 3

#: Mã từ chối — ỔN ĐỊNH, chữ IN HOA, cùng quy ước với `contract_adapter` và
#: `compiler` (mã `reason_code` của tầng dựng; `ErrorCode` là taxonomy của cổng
#: pipeline, không phải của tầng này).
MA_REFERENCE_UNKNOWN = "STRUCTURED_RELATION_REFERENCE_UNKNOWN"
MA_LINE_DEGENERATE = "STRUCTURED_LINE_DEGENERATE"
MA_PLANE_DEGENERATE = "STRUCTURED_PLANE_DEGENERATE"
MA_RELATION_INVALID = "STRUCTURED_RELATION_INVALID"

MA_QUAN_HE: tuple[str, ...] = (
    MA_REFERENCE_UNKNOWN, MA_LINE_DEGENERATE, MA_PLANE_DEGENERATE,
    MA_RELATION_INVALID,
)


class GeometricRelation(BaseModel):
    """Một quan hệ hình học CÓ KIỂU, do `analyze` khai và server đóng băng.

    Nhãn điểm là **chuỗi trần**, đúng quy ước đã có của `SourceInvariant.points`
    — kho này không có `PointRef`/`EntityRef`, và dựng một hệ định danh thứ hai
    chỉ cho hai loại quan hệ là tạo ra đúng thứ `CLAUDE.md §2b` cấm.
    """

    model_config = ConfigDict(frozen=True)

    kind: str
    #: Đường thẳng thứ nhất — ĐÚNG hai nhãn điểm phân biệt.
    line: tuple[str, ...] = ()
    #: Đường thẳng thứ hai — chỉ với `perpendicular_lines`.
    other_line: tuple[str, ...] = ()
    #: Mặt phẳng — ĐÚNG ba nhãn điểm phân biệt, chỉ với `perpendicular_line_plane`.
    plane: tuple[str, ...] = ()
    #: Truy về đúng mục dữ kiện của đề. `None` ⇔ không ghim được vào đâu.
    source_fact_id: str | None = None
    #: Mô hình TỰ GIẢ ĐỊNH, đề không nói. Tầng dựng KHÔNG được coi đây là dữ
    #: kiện đề cho — xem `dung_duoc_cho_tang_dung`.
    model_assumption: bool = False


@dataclass(frozen=True)
class QuanHeChinhTac:
    """Quan hệ đã chuẩn hoá — đây là thứ tầng dựng đọc, không phải model thô."""

    kind: str
    #: Đường (2 nhãn đã sắp) + đường thứ hai (2) hoặc mặt phẳng (3 đã sắp).
    args: tuple[str, ...]
    source_fact_id: str | None
    model_assumption: bool

    @property
    def khoa(self) -> tuple[str, tuple[str, ...]]:
        """Danh tính NGỮ NGHĨA — hai quan hệ cùng khoá là một quan hệ."""
        return (self.kind, self.args)

    @property
    def duong(self) -> tuple[str, ...]:
        return self.args[:SO_DIEM_DUONG]

    @property
    def duong_kia(self) -> tuple[str, ...]:
        return (self.args[SO_DIEM_DUONG:]
                if self.kind == "perpendicular_lines" else ())

    @property
    def mat(self) -> tuple[str, ...]:
        return (self.args[SO_DIEM_DUONG:]
                if self.kind == "perpendicular_line_plane" else ())

    def dung_duoc_cho_tang_dung(self) -> bool:
        """Tầng dựng chỉ được dùng quan hệ TRUY ĐƯỢC VỀ ĐỀ.

        Giả định của mô hình không bị xoá — nó ở lại hợp đồng để đọc và để giải
        thích — nhưng nó **không** được âm thầm nâng thành `GIVEN`.
        """
        return bool(self.source_fact_id) and not self.model_assumption


@dataclass(frozen=True)
class LoiQuanHe:
    """Một quan hệ bị từ chối, kèm mã ổn định. KHÔNG chở nguyên văn đề."""

    ma: str
    kind: str
    #: Chỉ số trong `contract.geometric_relations` — truy vết được mà không lộ
    #: nhãn nào của đề.
    chi_so: int


@dataclass(frozen=True)
class KetQuaQuanHe:
    relations: tuple[QuanHeChinhTac, ...] = ()
    loi: tuple[LoiQuanHe, ...] = ()

    @property
    def hop_le(self) -> bool:
        return not self.loi


def chuan_hoa_duong(diem: tuple[str, ...]) -> tuple[str, ...] | None:
    """`(B, A)` → `(A, B)`. `None` nếu suy biến — hai đầu trùng hoặc sai số."""
    ten = tuple(str(p) for p in diem)
    if len(ten) != SO_DIEM_DUONG or len(set(ten)) != SO_DIEM_DUONG:
        return None
    return tuple(sorted(ten))


def chuan_hoa_mat(diem: tuple[str, ...]) -> tuple[str, ...] | None:
    """Mọi hoán vị của ba điểm phân biệt → MỘT bộ ba đã sắp. `None` nếu suy biến."""
    ten = tuple(str(p) for p in diem)
    if len(ten) != SO_DIEM_MAT or len(set(ten)) != SO_DIEM_MAT:
        return None
    return tuple(sorted(ten))


def diem_hop_dong(contract: Any) -> frozenset[str]:
    """Nhãn điểm mà hợp đồng THẬT SỰ nhắc tới, qua đường CÓ CẤU TRÚC.

    Đọc `source_invariants` và `solid_topology` — các nơi trong hợp đồng mà một
    nhãn điểm xuất hiện với kiểu và xuất xứ. **Không** quét `problem_text`: làm
    vậy là để một ký hiệu bất kỳ trong câu văn sinh ra một điểm, đúng phép đoán
    mà cả module này lẫn `SourceInvariant` được viết ra để bỏ đi.
    """
    ra: set[str] = set()
    for b in getattr(contract, "source_invariants", None) or ():
        ra.update(str(p) for p in (getattr(b, "points", None) or ()))
    topo = getattr(contract, "solid_topology", None)
    if topo is not None:
        ra.update(str(p) for p in (getattr(topo, "base_cycle", ()) or ()))
        ra.update(str(p) for p in (getattr(topo, "top_cycle", ()) or ()))
        if getattr(topo, "apex", None):
            ra.add(str(topo.apex))
    return frozenset(ra)


def _chuan_hoa_mot(rel: Any, biet: frozenset[str], chi_so: int
                   ) -> tuple[QuanHeChinhTac | None, LoiQuanHe | None]:
    kind = str(getattr(rel, "kind", "") or "")
    if kind not in RELATION_KINDS:
        return None, LoiQuanHe(MA_RELATION_INVALID, kind, chi_so)

    duong = chuan_hoa_duong(tuple(getattr(rel, "line", None) or ()))
    if duong is None:
        return None, LoiQuanHe(MA_LINE_DEGENERATE, kind, chi_so)

    if kind == "perpendicular_lines":
        if getattr(rel, "plane", None):
            # Ô SAI ĐƯỢC ĐIỀN. Bỏ qua im lặng thì hợp đồng nói một đằng, tầng
            # dựng đọc một nẻo — đúng chế độ hỏng module này dọn đi.
            return None, LoiQuanHe(MA_RELATION_INVALID, kind, chi_so)
        kia = chuan_hoa_duong(tuple(getattr(rel, "other_line", None) or ()))
        if kia is None:
            return None, LoiQuanHe(MA_LINE_DEGENERATE, kind, chi_so)
        if kia == duong:
            # Một đường không vuông góc với chính nó.
            return None, LoiQuanHe(MA_LINE_DEGENERATE, kind, chi_so)
        # Cặp đường cũng phải chính tắc: `(d₁, d₂)` và `(d₂, d₁)` là một quan hệ.
        a, b = sorted((duong, kia))
        args = (*a, *b)
    else:
        if getattr(rel, "other_line", None):
            return None, LoiQuanHe(MA_RELATION_INVALID, kind, chi_so)
        mat = chuan_hoa_mat(tuple(getattr(rel, "plane", None) or ()))
        if mat is None:
            return None, LoiQuanHe(MA_PLANE_DEGENERATE, kind, chi_so)
        args = (*duong, *mat)

    la = [t for t in args if t not in biet]
    if la:
        return None, LoiQuanHe(MA_REFERENCE_UNKNOWN, kind, chi_so)

    sfid = getattr(rel, "source_fact_id", None)
    return QuanHeChinhTac(
        kind=kind, args=args,
        source_fact_id=str(sfid) if sfid else None,
        model_assumption=bool(getattr(rel, "model_assumption", False)),
    ), None


def _uu_tien(q: QuanHeChinhTac) -> tuple[int, str]:
    """Thứ tự chọn khi hai bản ghi cùng khoá — TẤT ĐỊNH, không phụ thuộc đầu vào.

    Bản TRUY ĐƯỢC VỀ ĐỀ thắng bản giả định: gộp hai cái đó rồi giữ bản giả định
    là cách một giả định lẻn vào chỗ của một dữ kiện.
    """
    return (0 if q.dung_duoc_cho_tang_dung() else 1, q.source_fact_id or "")


def kiem_va_chuan_hoa(contract: Any) -> KetQuaQuanHe:
    """`RequestContract` → quan hệ CHÍNH TẮC, đã khử trùng, đã kiểm tham chiếu.

    Từ chối bằng **mã ổn định**, không im lặng bỏ qua: một quan hệ khai sai mà
    bị nuốt thì tầng dựng thấy một hợp đồng *thiếu* chứ không thấy một hợp đồng
    *hỏng*, và hai thứ ấy cần hai lời trả lời khác nhau.
    """
    biet = diem_hop_dong(contract)
    tho = tuple(getattr(contract, "geometric_relations", None) or ())

    ok: list[QuanHeChinhTac] = []
    loi: list[LoiQuanHe] = []
    for i, rel in enumerate(tho):
        q, e = _chuan_hoa_mot(rel, biet, i)
        if e is not None:
            loi.append(e)
        elif q is not None:
            ok.append(q)

    gom: dict[tuple[str, tuple[str, ...]], QuanHeChinhTac] = {}
    for q in sorted(ok, key=_uu_tien):
        gom.setdefault(q.khoa, q)

    return KetQuaQuanHe(
        relations=tuple(sorted(gom.values(),
                               key=lambda q: (q.kind, q.args,
                                              q.source_fact_id or ""))),
        loi=tuple(loi),
    )
