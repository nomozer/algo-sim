# -*- coding: utf-8 -*-
"""CỔNG BỀ MẶT HỌC SINH — thứ CHẠY ĐƯỢC chưa chắc thứ XEM ĐƯỢC.

─── VÌ SAO CẦN MỘT CỔNG NỮA ───────────────────────────────────────────────────

Chuỗi cổng hiện có kiểm rất kỹ *chương trình*: cú pháp (validator), dữ liệu đề
(P1/P2), phủ nghĩa vụ (C₁a/C₁b), hậu điều kiện (C₂), và binding có phân giải
được không (`_assert_bindings_resolvable`). Qua hết chuỗi đó, `servable=True`.

Nhưng mọi cổng ấy đều nhìn về phía CHƯƠNG TRÌNH. Không cổng nào quay lại hỏi câu
của người học:

    những gì thuật toán làm CÓ HIỆN RA trên màn hình không?

Sự cố vNext đã chụp được màn hình chính là câu đó bị bỏ trống: chương trình chạy
đúng, lời kể đúng, envelope biên dịch sạch — và ngăn xếp trên hình vẫn rỗng suốt
bảy bước.

─── CHIỀU CÒN THIẾU CỦA HỢP ĐỒNG THỊ GIÁC ────────────────────────────────────

`_assert_bindings_resolvable` (bất biến #34) hỏi: *mỗi binding đã khai có phân
giải về một biến không?* Đó là chiều **binding → bộ nhớ**.

Chiều ngược lại chưa ai hỏi: *mỗi biến ĐÁNG THẤY có được khai binding không?*

Thiếu chiều này, một chương trình hoàn toàn hợp lệ vẫn có thể đẩy/lấy một ngăn
xếp suốt 20 bước, chỉ bind mỗi ô kết quả, rồi được phát đi. Học sinh nghe kể về
một ngăn xếp không có trên hình. Cả hai cổng đều xanh vì cả hai đều đúng — chúng
chỉ không cùng nhìn về phía màn hình.

─── VÌ SAO CHỈ ĐÒI ĐÚNG HAI LỚP, KHÔNG ĐÒI MỌI BIẾN ──────────────────────────

Đòi mọi biến phải có hình là từ chối oan hàng loạt mô phỏng đúng: biến đếm vòng
lặp, biến tạm khi hoán đổi, cờ nội bộ — chúng không phải nội dung bài học, và bắt
vẽ hết chỉ làm màn hình rối thêm.

Hai lớp bị đòi, và cả hai đều có lý do hẹp:

  1. **Container BIẾN ĐỘNG** — một tập hợp thay đổi qua các bước CHÍNH LÀ cơ chế
     mà bài đang dạy. Ngăn xếp, hàng đợi, mảng đang sắp: không thấy chúng đổi thì
     không còn gì để xem. Container đứng yên cả lượt thì không đòi — nó là dữ
     liệu nền, không phải diễn tiến.

  2. **Witness của nghĩa vụ** — chỗ chứa CÂU TRẢ LỜI. Phát một mô phỏng mà học
     sinh không bao giờ thấy đáp án thì `servable` đang nói dối về chính nghĩa
     của nó.

Ngoài hai lớp đó, cổng im lặng. Một cổng kêu oan là một cổng sẽ bị tắt.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .contract import SemanticProgramSpec
from .interpreter import SemanticExecutionResult
from .request_contract import RequestContract

#: Chuỗi kỹ thuật KHÔNG BAO GIỜ được đi tới bề mặt học sinh. Cùng danh sách với
#: `frontend/src/simulations/learner-gate.ts` — hai đầu của cùng một luật.
PLACEHOLDER_LEAKS = ("undefined", "null", "[object Object]", "NaN", "Infinity")

#: Kiểu bộ nhớ mà "đổi giá trị" nghĩa là DIỄN TIẾN chứ không phải một phép gán
#: nội bộ. Vô hướng cố ý nằm ngoài — xem docstring module.
CONTAINER_TYPES = frozenset(
    {"array", "stack", "queue", "matrix", "map", "set", "graph"}
)


class LearnerSurfaceResult(BaseModel):
    ok: bool
    error_code: str | None = None
    #: Mỗi mục là MỘT câu nói rõ cái gì không thấy được, để telemetry (§5) chỉ
    #: thẳng chỗ sửa thay vì báo "không phát được".
    invisible: list[str] = Field(default_factory=list)


def _bound_names(spec: SemanticProgramSpec) -> set[str]:
    """Mọi tên bộ nhớ có ÍT NHẤT MỘT đường lên màn hình."""
    vb = spec.visual_bindings
    if vb is None:
        return set()
    ra: set[str] = set()
    for cb in vb.containers or ():
        ra.add(cb.semantic_id)
        # `graph_view` tô trạng thái qua hai biến phụ — chúng cũng là đường lên
        # màn hình, nên biến được tham chiếu ở đây coi như đã hiện.
        for phu in (getattr(cb, "visited_ref", None), getattr(cb, "current_ref", None)):
            if phu:
                ra.add(phu)
    for pb in vb.pointers or ():
        ra.add(pb.var_ref)
    for box in vb.value_boxes or ():
        ra.add(box.var_ref)
    return ra


def _bien_dong(exec_res: SemanticExecutionResult, ten: str) -> bool:
    """Biến này có ĐỔI giá trị trong lượt chạy không?

    So bằng `repr` chứ không bằng `==`: giá trị có thể là list/dict lồng nhau, và
    một vài kiểu không so sánh trực tiếp được. `repr` đủ để trả lời câu hỏi duy
    nhất ở đây — *có khác đi không* — mà không cần biết kiểu.
    """
    thay: set[str] = set()
    for step in exec_res.trace:
        thay.add(repr((step.memory_snapshot or {}).get(ten)))
        if len(thay) > 1:
            return True
    return False


def _ro_ri(envelope: dict[str, Any]) -> list[str]:
    """Chuỗi kỹ thuật lọt vào giá trị hiển thị của bất kỳ khung nào."""
    ra: list[str] = []
    for frame in envelope.get("config", {}).get("frames", ()) or ():
        for obj in frame.get("objects", ()) or ():
            ung = list(obj.get("items") or ())
            if "value" in obj:
                ung.append(obj["value"])
            for v in ung:
                if isinstance(v, str) and v.strip() in PLACEHOLDER_LEAKS:
                    ra.append(f"{obj.get('id')}: \"{v}\"")
    return sorted(set(ra))


def check_learner_surface(
    contract: RequestContract,
    spec: SemanticProgramSpec,
    exec_res: SemanticExecutionResult,
    envelope: dict[str, Any],
) -> LearnerSurfaceResult:
    """Chạy được RỒI, nhưng học sinh có thấy đủ để hiểu không?

    Chạy SAU `compile` vì nó cần envelope đã dựng: câu hỏi là về những khung sẽ
    thật sự được phát, không phải về ý định của chương trình.
    """
    thieu: list[str] = []
    da_bind = _bound_names(spec)

    # (1) Container BIẾN ĐỘNG mà không có đường lên màn hình.
    for decl in spec.memory_declarations:
        if decl.type not in CONTAINER_TYPES:
            continue
        if decl.name in da_bind:
            continue
        if _bien_dong(exec_res, decl.name):
            thieu.append(
                f"'{decl.name}' ({decl.type}) đổi giá trị trong lượt chạy nhưng "
                "không có binding nào — học sinh nghe kể về nó mà không thấy nó"
            )

    # (2) Chỗ chứa CÂU TRẢ LỜI phải nhìn thấy được.
    for ob in contract.obligations:
        witness = (ob.params or {}).get("witness")
        if witness and witness not in da_bind:
            thieu.append(
                f"witness '{witness}' của nghĩa vụ '{ob.kind}' không hiện trên "
                "màn hình — mô phỏng chạy xong mà học sinh không thấy đáp án"
            )

    # (3) Không có khung nào thì không có gì để xem, dù mọi tầng trên đều xanh.
    frames = envelope.get("config", {}).get("frames") or ()
    if not frames:
        thieu.append("envelope không có khung nào để trình bày")

    # (4) Giá trị kỹ thuật rò lên bề mặt.
    thieu.extend(_ro_ri(envelope))

    if thieu:
        return LearnerSurfaceResult(
            ok=False, error_code="LEARNER_SURFACE_INCOMPLETE", invisible=thieu
        )
    return LearnerSurfaceResult(ok=True)
