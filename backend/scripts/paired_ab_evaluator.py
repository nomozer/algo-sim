# -*- coding: utf-8 -*-
"""BỘ CHẤM GHÉP CẶP v2 — cùng định nghĩa, cùng predicate, cùng ngưỡng cho HAI NHÁNH.

`BENCHMARK_MEASUREMENT_REPAIR` (2026-09-20).

─── VÌ SAO CÓ BẢN 2 ────────────────────────────────────────────────────────

Bản 1 (`run_primitive_compiler_ab.cham`) nhận `arm` và dùng nó để ĐỔI LUẬT ở
đúng một chỗ:

    construction_trace_ok = (số bước dựng ≥ 10) nếu COMPILER
                            (len(spec.statements) ≥ 6) nếu GEMINI

Hai đại lượng khác nhau mang một tên. Tệ hơn — và chỉ lộ ra khi đo lại —
**vế Gemini luôn SAI**: `validate_semantic_program` có
`model_validator(mode="before")` nâng `declare_point` RA KHỎI `statements`, nên
một chương trình ĐÚNG của họ này có 9 câu lệnh thô chỉ còn **5** sau thẩm định.
Ngưỡng `≥ 6` vì thế không thể đạt, kể cả với chương trình hoàn hảo.

Nên bản 2 đặt một luật cứng: **predicate ghép cặp KHÔNG BAO GIỜ nhận tên nhánh.**
Hai nhánh được chuẩn hoá thành CÙNG một `QuanSat`, và mọi trục ghép cặp là một
hàm thuần tuý trên `QuanSat` ấy. Đổi nhãn nhánh không thể đổi phán quyết, vì
nhãn không đi vào hàm.

─── BA TRẠNG THÁI, KHÔNG PHẢI HAI ──────────────────────────────────────────

Thiếu dữ liệu trả `NOT_MEASURED`, KHÔNG biến thành `FAIL`. Một thứ không quan
sát được không phải một thứ sai — gộp hai cái đó là cách một bộ đo biến khoảng
trống thành bằng chứng.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

EVALUATOR_VERSION = "paired-ab-evaluator/2"

PASS = "PASS"
FAIL = "FAIL"
NOT_MEASURED = "NOT_MEASURED"
TRANG_THAI = (PASS, FAIL, NOT_MEASURED)


@dataclass(frozen=True)
class QuanSat:
    """Quan sát đã CHUẨN HOÁ của một ca, ở MỘT nhánh.

    ⚠️ `arm` có mặt để truy vết và để ghi telemetry riêng. Nó **không được**
    xuất hiện trong bất kỳ predicate ghép cặp nào — `test_F` quét AST để chắc.
    """

    case_id: str
    arm: str
    #: `None` = không quan sát được (không phải False).
    validation_ok: bool | None = None
    route_servable: bool | None = None
    scene_non_empty: bool | None = None
    point_labels_ok: bool | None = None
    topology_ok: bool | None = None
    squared_lengths_ok: bool | None = None
    perpendicular_ok: bool | None = None
    non_collinear_ok: bool | None = None
    final_memory_ok: bool | None = None
    answer_ok: bool | None = None
    visual_gate: str | None = None
    #: TELEMETRY RIÊNG — không bao giờ vào phán quyết ghép cặp.
    construction_step_count: int | None = None
    semantic_statement_count: int | None = None


def _bool_axis(ten: str) -> Callable[[QuanSat], str]:
    """Trục boolean: `None` ⇒ NOT_MEASURED, còn lại ⇒ PASS/FAIL.

    MỘT hàm dựng cho MỌI trục boolean, nên không có chỗ nào để một ngưỡng riêng
    lẻn vào một nhánh.
    """
    def f(q: QuanSat) -> str:
        v = getattr(q, ten)
        return NOT_MEASURED if v is None else (PASS if v else FAIL)
    f.__name__ = f"axis_{ten}"
    return f


def _axis_visual_gate(q: QuanSat) -> str:
    if q.visual_gate is None:
        return NOT_MEASURED
    return PASS if q.visual_gate == "COVERED" else FAIL


#: TRỤC GHÉP CẶP — đăng ký TƯỜNG MINH. Mọi trục dùng trong `quality_pass` phải
#: có mặt ở đây; trục nào không có mặt thì KHÔNG được vào phán quyết.
PAIRED_AXES: dict[str, Callable[[QuanSat], str]] = {
    "validation_ok": _bool_axis("validation_ok"),
    "route_servable": _bool_axis("route_servable"),
    "scene_non_empty": _bool_axis("scene_non_empty"),
    "point_labels_ok": _bool_axis("point_labels_ok"),
    "topology_ok": _bool_axis("topology_ok"),
    "squared_lengths_ok": _bool_axis("squared_lengths_ok"),
    "perpendicular_ok": _bool_axis("perpendicular_ok"),
    "non_collinear_ok": _bool_axis("non_collinear_ok"),
    "final_memory_ok": _bool_axis("final_memory_ok"),
    "answer_ok": _bool_axis("answer_ok"),
    "visual_gate": _axis_visual_gate,
}

#: TELEMETRY RIÊNG TỪNG NHÁNH — quan sát được, nhưng KHÔNG so sánh được, nên
#: KHÔNG vào phán quyết nào. Hai tên khác nhau cho hai đại lượng khác nhau.
DIAGNOSTIC_AXES: tuple[str, ...] = (
    "compiler_construction_step_count",
    "gemini_semantic_statement_count",
)


@dataclass(frozen=True)
class PhanQuyet:
    case_id: str
    arm: str
    axes: dict[str, str]
    quality_pass: bool
    not_measured_count: int
    silent_quality_failure: bool
    diagnostics: dict[str, Any] = field(default_factory=dict)
    evaluator_version: str = EVALUATOR_VERSION

    def canonical(self) -> dict[str, Any]:
        """Bản chính tắc KHÔNG chứa `arm` — hai nhánh cùng quan sát phải cùng
        JSON, và đó là thứ `test_D` so từng byte."""
        return {"evaluator_version": self.evaluator_version,
                "axes": dict(sorted(self.axes.items())),
                "quality_pass": self.quality_pass,
                "not_measured_count": self.not_measured_count,
                "silent_quality_failure": self.silent_quality_failure}


def danh_gia(q: QuanSat) -> PhanQuyet:
    """Chấm MỘT quan sát. KHÔNG nhận tên nhánh làm tham số điều khiển."""
    axes = {ten: f(q) for ten, f in PAIRED_AXES.items()}
    chua_do = sum(1 for v in axes.values() if v == NOT_MEASURED)
    dat = all(v == PASS for v in axes.values())
    # Route nhận mà một trục ghép cặp FAIL ⇒ thất bại IM LẶNG. `NOT_MEASURED`
    # KHÔNG tính là thất bại — không quan sát được thì không kết tội.
    im_lang = bool(axes.get("route_servable") == PASS
                   and any(v == FAIL for v in axes.values()))
    tele: dict[str, Any] = {}
    if q.construction_step_count is not None:
        tele["compiler_construction_step_count"] = q.construction_step_count
    if q.semantic_statement_count is not None:
        tele["gemini_semantic_statement_count"] = q.semantic_statement_count
    return PhanQuyet(q.case_id, q.arm, axes, dat, chua_do, im_lang, tele)


def tu_ban_ghi(case_id: str, arm: str, cham: dict[str, Any],
               construction_step_count: int | None = None,
               semantic_statement_count: int | None = None) -> QuanSat:
    """Bản ghi RÚT GỌN đã commit → `QuanSat`. Không suy đoán giá trị nào.

    Khoá vắng mặt ⇒ `None` ⇒ `NOT_MEASURED`. Đây là cửa duy nhất để dữ liệu
    lịch sử vào bộ chấm v2, và nó cố ý KHÔNG đọc `construction_trace_ok`.
    """
    lay = lambda k: cham.get(k) if k in cham else None  # noqa: E731
    return QuanSat(
        case_id=case_id, arm=arm,
        validation_ok=lay("validation_ok"),
        route_servable=lay("route_servable"),
        scene_non_empty=lay("scene_non_empty"),
        point_labels_ok=lay("point_labels_ok"),
        topology_ok=lay("topology_ok"),
        squared_lengths_ok=lay("squared_lengths_ok"),
        perpendicular_ok=lay("perpendicular_ok"),
        non_collinear_ok=lay("non_collinear_ok"),
        final_memory_ok=lay("final_memory_ok"),
        answer_ok=lay("answer_ok"),
        visual_gate=lay("visual_gate"),
        construction_step_count=construction_step_count,
        semantic_statement_count=semantic_statement_count,
    )
