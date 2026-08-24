# -*- coding: utf-8 -*-
"""SemanticCoverageGate — thay `completeness_gate` THEO-TARGET.

`completeness_gate` cũ nhận `target_id` và tra registry, nên nó vô nghĩa với bài
không có module. Nhưng bảo vệ sư phạm mà nó giữ thì THẬT: *đề hỏi hai việc mà
mô phỏng chỉ làm một thì phải từ chối, không được im lặng làm một nửa.* File này
giữ đúng bảo vệ đó mà không cần catalog.

BA CÂU HỎI KHÁC NHAU, đừng gộp (spec §5.3):
    C₁a — nghĩa vụ có witness hợp lệ VỀ CẤU TRÚC không?   (trước execution, ở đây)
    C₁b — witness đó có THẬT SỰ được hiện thực hoá không?  (sau execution, ở đây)
    C₂  — chạy xong có thoả TÍNH CHẤT không?               (postconditions.py)
"""
from __future__ import annotations

from typing import Any, Iterable

from pydantic import BaseModel, Field

from .contract import SemanticProgramSpec
from .obligations import (
    OBLIGATION_KINDS,
    accepts_container_type,
    has_server_owned_checker,
)
from .request_contract import RequestContract


class CoverageResult(BaseModel):
    ok: bool
    error_code: str | None = None
    missing: list[str] = Field(default_factory=list)
    #: Nghĩa vụ hợp lệ nhưng KHÔNG có checker server-owned → mức yếu (§5.4).
    #: Tách khỏi `missing` vì "chưa chứng minh được" ≠ "thiếu".
    weak_kinds: list[str] = Field(default_factory=list)


def _producers(statements: Iterable) -> set[str]:
    """Mọi biến có ÍT NHẤT MỘT câu lệnh tạo ra nó.

    C₁a chỉ hỏi "có ai viết vào biến này không", KHÔNG hỏi "câu lệnh đó có chạy
    không" — nên nhánh lồng vẫn tính là có. Việc nó có đạt tới hay không là câu
    hỏi của C₁b, và tách hai câu hỏi chính là điểm của thiết kế này.
    """
    found: set[str] = set()
    for st in statements or ():
        kind = getattr(st, "kind", None)
        if kind == "assign":
            found.add(st.target_var)
        # Ba câu lệnh dựng TẠO RA `target_var` — cùng vai với `assign`.
        # Thiếu nhánh này thì C₁a báo *"witness không có producer hợp lệ"* cho
        # mọi chương trình hình học, kể cả chương trình dựng đúng. Đây là nửa
        # thứ hai của cùng một lỗ với `_phu_thuoc`: một bên thiếu *ai tạo ra*,
        # một bên thiếu *tạo ra từ cái gì* — và phải vá cả hai mới thông.
        elif kind in ("construct_point", "construct_line", "construct_section"):
            found.add(st.target_var)
        elif kind in ("pop", "dequeue"):
            dest = getattr(st, "dest_var", None)
            if dest:
                found.add(dest)
        elif kind in ("write_index", "map_set", "swap", "push", "enqueue",
                      "set_insert", "set_remove"):
            found.add(st.container)
        elif kind in ("for_range", "for_each"):
            var = getattr(st, "loop_var", None) or getattr(st, "item_var", None)
            if var:
                found.add(var)
        for attr in ("body", "then_body", "else_body"):
            sub = getattr(st, attr, None)
            if sub:
                found |= _producers(sub)
    return found


def _doc(node: Any) -> set[str]:
    """Tên bộ nhớ mà một biểu thức/điều kiện ĐỌC.

    Duyệt tổng quát trên cây Pydantic thay vì liệt kê từng lớp: ngữ pháp IR còn
    mở rộng, và một bảng liệt kê tay sẽ lặng lẽ bỏ sót lớp mới — đúng kiểu lỗi
    câm mà bất biến #33 sinh ra để chặn.
    """
    ra: set[str] = set()

    def di(x: Any) -> None:
        if isinstance(x, BaseModel):
            if getattr(x, "kind", None) == "var" and isinstance(getattr(x, "name", None), str):
                ra.add(x.name)
            for ten, gt in x:
                # Ba trường này mang TÊN vùng nhớ, không phải dữ liệu — và tên
                # là một chuỗi trần nên nhánh đệ quy bên dưới sẽ bỏ qua nó.
                # `container_or_expr` (của `for_each`) từng bị bỏ sót đúng vì
                # thế: hai fixture dùng vòng lặp trên chuỗi bị chấm là "không
                # dẫn xuất từ đầu vào" trong khi chúng dẫn xuất rõ ràng.
                if ten in ("container", "graph", "container_or_expr") and isinstance(gt, str):
                    ra.add(gt)
                else:
                    di(gt)
        elif isinstance(x, (list, tuple)):
            for y in x:
                di(y)
        elif isinstance(x, dict):
            for y in x.values():
                di(y)

    di(node)
    return ra


def _ten_trong_bieu_thuc_hinh_hoc(expr: Any) -> set[str]:
    """Tên vùng nhớ mà một biểu thức HÌNH HỌC đọc.

    Tách khỏi `_doc` vì hai cái trả lời hai câu khác nhau: `_doc` duyệt CÂY và
    nhặt `kind == "var"`; ở đây trường mang tên là **chuỗi trần** nên phải tra
    theo `kind`. Bảng tra nhập từ `validator` — nó là chủ sở hữu, và bảng ấy
    cố ý không gồm `ratio` (một phân số, KHÔNG phải tên vùng nhớ).
    """
    from .validator import _BIEU_THUC_HINH_HOC

    truong = _BIEU_THUC_HINH_HOC.get(getattr(expr, "kind", None))
    if not truong:
        return set()
    return {t for t in (getattr(expr, f, None) for f in truong) if isinstance(t, str)}


def _phu_thuoc(statements: Iterable, ngoai: frozenset[str],
               ra: dict[str, set[str]] | None = None) -> dict[str, set[str]]:
    """Mỗi biến PHỤ THUỘC vào những biến nào — kể cả qua NHÁNH.

    `ngoai` là phụ thuộc ĐIỀU KHIỂN đang có hiệu lực: điều kiện của `if`/`while`
    và nguồn duyệt của vòng lặp bao quanh. Thiếu vế này thì
    `result = "KHÔNG HỢP LỆ"` nằm trong nhánh so sánh đỉnh ngăn xếp bị coi là
    hằng không phụ thuộc gì — và một chương trình ĐÚNG bị kết tội.
    """
    if ra is None:
        ra = {}

    def them(ten: str | None, nguon: set[str]) -> None:
        if ten:
            ra.setdefault(ten, set()).update(nguon | ngoai)

    for st in statements or ():
        kind = getattr(st, "kind", None)
        if kind == "assign":
            them(st.target_var, _doc(st.expr))
        # ── DỰNG HÌNH (2026-08-24) ───────────────────────────────────────
        #
        # Thiếu ba nhánh này, `_phu_thuoc` trả về `{}` cho MỌI chương trình
        # hình học, và C₁b kết luận *"witness khai đáp án chứ không tính nó"*
        # — tức **từ chối oan toàn bộ miền**, kèm thông báo nói sai bệnh.
        # Đo được trước khi chạy Phase 5: `H = project_onto(S, day)` ghi nhận
        # phụ thuộc rỗng, nên `point_on_plane(day, witness=H)` trượt C₁b.
        #
        # `_doc` không tự bắt được vì trường của biểu thức hình học là **chuỗi
        # trần** (`line`, `plane_a`, `point`…), mà nhánh đệ quy của `_doc` bỏ
        # qua chuỗi. Bảng tên trường lấy từ `validator` — MỘT nguồn sự thật,
        # không chép bản thứ hai.
        elif kind == "construct_point":
            them(st.target_var, _ten_trong_bieu_thuc_hinh_hoc(st.expr) | _doc(st.expr))
        elif kind == "construct_line":
            them(st.target_var, {st.through_a, st.through_b})
        elif kind == "construct_section":
            them(st.target_var, {st.solid, st.plane})
        elif kind in ("pop", "dequeue"):
            them(getattr(st, "dest_var", None), {st.container})
            them(st.container, set())
        elif kind in ("write_index", "map_set", "swap", "push", "enqueue",
                      "set_insert", "set_remove"):
            them(st.container, _doc(st))
        elif kind == "for_range":
            nguon = _doc(getattr(st, "start", None)) | _doc(getattr(st, "end", None))
            them(getattr(st, "loop_var", None), nguon)
            _phu_thuoc(st.body, ngoai | nguon, ra)
            continue
        elif kind == "for_each":
            # `for_each` duyệt `container_or_expr`: hoặc TÊN một container,
            # hoặc một biểu thức danh sách. Hai dạng, hai cách đọc.
            src = getattr(st, "container_or_expr", None)
            nguon = {src} if isinstance(src, str) else _doc(src)
            them(getattr(st, "item_var", None), nguon)
            _phu_thuoc(st.body, ngoai | frozenset(nguon), ra)
            continue

        # Nhánh/thân vòng lặp: điều kiện bao quanh trở thành phụ thuộc ĐIỀU KHIỂN.
        dk = _doc(getattr(st, "condition", None)) if hasattr(st, "condition") else set()
        for attr in ("body", "then_body", "else_body"):
            sub = getattr(st, attr, None)
            if sub:
                _phu_thuoc(sub, ngoai | frozenset(dk), ra)
    return ra


def _bao_dong(dep: dict[str, set[str]], ten: str) -> set[str]:
    """Bao đóng bắc cầu — `S` phụ thuộc `arr` qua bao nhiêu bước cũng tính."""
    thay: set[str] = set()
    hang = [ten]
    while hang:
        x = hang.pop()
        for y in dep.get(x, ()):
            if y not in thay:
                thay.add(y)
                hang.append(y)
    return thay


def check_structural_coverage(
    contract: RequestContract, spec: SemanticProgramSpec
) -> CoverageResult:
    """C₁a — chạy TRƯỚC execution."""
    declared = {d.name: d.type for d in spec.memory_declarations}
    producers = _producers(spec.statements)
    phu_thuoc = _phu_thuoc(spec.statements, frozenset())

    missing: list[str] = []
    weak: list[str] = []

    for ob in contract.obligations:
        # Kind NGOÀI taxonomy: không có miền kiểu nào để đối chiếu, nên kiểm
        # cấu trúc là BẤT KHẢ THI chứ không phải đã qua ⇒ mức yếu ngay.
        # (Đường production không tới đây được — `build_request_contract` lọc
        # tại biên — nhưng C₁a không được phép dựa vào lời hứa của khâu khác.)
        if ob.kind not in OBLIGATION_KINDS:
            weak.append(ob.kind)
            continue

        # Kind TRONG taxonomy: THỨ TỰ CÓ Ý NGHĨA — kiểm CẤU TRÚC trước,
        # kiểm-chứng-được sau. Hỏi ngược lại thì một nghĩa vụ mức yếu gắn nhầm
        # container (vd `structural_traversal` gắn lên mảng) thoát khỏi mọi
        # kiểm tra cấu trúc, và một lỗi thật lọt qua dưới danh nghĩa "chưa kiểm
        # chứng được".
        ctype = declared.get(ob.container)
        if ctype is None:
            missing.append(f"{ob.describe()}: container '{ob.container}' chưa khai báo")
            continue
        if not accepts_container_type(ob.kind, ctype):
            missing.append(
                f"{ob.describe()}: kiểu '{ctype}' không hợp với nghĩa vụ này"
            )
            continue

        w = ob.witness
        if not w:
            missing.append(f"{ob.describe()}: thiếu witness")
            continue
        if w not in declared:
            missing.append(f"{ob.describe()}: witness '{w}' chưa khai báo")
            continue
        if w not in producers:
            missing.append(f"{ob.describe()}: witness '{w}' không có producer hợp lệ")
            continue

        # WITNESS PHẢI DẪN XUẤT TỪ DỮ LIỆU, không được là hằng gán thẳng.
        #
        # ─── LỖ HỔNG ĐÃ ĐO ĐƯỢC (live 2026-08-24) ────────────────────────────
        # Đề chuỗi ngoặc: LLM chép đúng `{[()]}`, khai đủ `stack`/`char`/
        # `top_char`, rồi gán thẳng `hop_le = true`. Vòng lặp KHÔNG chạy —
        # `total_steps=2`, `stack=null`. Mọi cổng phía trước đều xanh: có
        # producer, kiểu hợp, và C₂ tính lại độc lập cũng ra `True` nên KHỚP.
        #
        # Với phán quyết nhị phân, đoán bừa đúng 50%. Oracle kiểm ĐÁP ÁN không
        # phân biệt được "tính đúng" với "đoán trúng" — và đó là giới hạn cấu
        # trúc, không phải lỗi cài đặt. Phép kiểm này bổ khuyết đúng chỗ ấy: nó
        # hỏi về CÔNG VIỆC chứ không về đáp án.
        #
        # Tổng quát cho MỌI nghĩa vụ, không riêng `predicate_verdict`:
        # `extremum(arr, max_val)` gán thẳng `max_val = 89` cũng qua C₂ y hệt.
        #
        # Phụ thuộc tính cả qua NHÁNH (`_phu_thuoc`): `result = "KHÔNG HỢP LỆ"`
        # trong nhánh so sánh đỉnh ngăn xếp vẫn là dẫn xuất thật.
        if ob.container not in _bao_dong(phu_thuoc, w):
            missing.append(
                f"{ob.describe()}: witness '{w}' không dẫn xuất từ "
                f"'{ob.container}' — chương trình khai đáp án chứ không tính nó"
            )
            continue

        # Cấu trúc sạch. Còn lại là một câu hỏi KHÁC HẲN: chạy xong rồi thì có
        # cách nào kiểm chứng độc lập không? Không → mức YẾU, và mức yếu KHÔNG
        # phải `capability_gap`: nói "không làm được" về một bài máy làm được là
        # báo cáo sai năng lực của chính mình (§5.4).
        if not has_server_owned_checker(ob.kind):
            weak.append(ob.kind)

    if missing:
        return CoverageResult(
            ok=False,
            error_code="REQUESTED_OPERATION_UNCOVERED",
            missing=missing,
            weak_kinds=sorted(set(weak)),
        )
    if weak:
        return CoverageResult(
            ok=False,
            error_code="SEMANTIC_VERIFICATION_UNAVAILABLE",
            weak_kinds=sorted(set(weak)),
        )
    return CoverageResult(ok=True)


def check_realized_coverage(
    contract: RequestContract, spec: SemanticProgramSpec, exec_result
) -> CoverageResult:
    """C₁b — chạy SAU execution.

    Trả lời câu mà C₁a không trả lời được: witness có THẬT SỰ được tạo ra trong
    lượt chạy này không, hay chỉ tồn tại trên giấy?

    Ví dụ tách được hai tầng: `assign min_value = 1` nằm trong `if 1 == 2`.
    C₁a thấy biến khai đúng kiểu và có producer ⇒ PASS. Nhưng nhánh ấy không bao
    giờ đạt tới, nên mô phỏng sẽ phát ra một "nghĩa vụ" chưa từng xảy ra.

    Nghĩa vụ MỨC YẾU bị bỏ qua ở đây: C₁a đã xử chúng bằng
    `SEMANTIC_VERIFICATION_UNAVAILABLE`, và kết tội chúng lần nữa dưới nhãn
    "witness chưa hiện thực hoá" là nói sai bản chất.
    """
    realized: set[str] = set()
    for step in getattr(exec_result, "trace", ()) or ():
        for name, value in (step.memory_snapshot or {}).items():
            if value is not None:
                realized.add(name)

    missing = [
        f"{ob.describe()}: witness '{ob.witness}' không được hiện thực hoá trong "
        "lượt chạy (nhánh chết, hoặc không đạt tới)"
        for ob in contract.obligations
        if has_server_owned_checker(ob.kind) and ob.witness and ob.witness not in realized
    ]

    if missing:
        return CoverageResult(
            ok=False, error_code="OBLIGATION_WITNESS_UNREALIZED", missing=missing
        )
    return CoverageResult(ok=True)
