# -*- coding: utf-8 -*-
"""Pipeline Adapter: SemanticProgramSpec → envelope mang FRAME TIMELINE.

KHÔNG đi qua `dsl/validator.py`: route này có hợp đồng riêng, nên nó tránh
được trần 20 bước cắt câm (`MAX_REVEAL_STEPS`) và bộ động từ 4 action của DSL.

BUG ĐÃ SHIP MÀ FILE NÀY SINH RA (bất biến #31, anti-pattern #15):
bản trước giữ `frames[0].objects` rồi vứt toàn bộ khung còn lại, nên trên màn
hình thuyết minh đọc *"lấy '[' ra khỏi ngăn xếp, so với ']', khớp nhau"* —
chính xác từng chi tiết — trong khi ngăn xếp RỖNG và các ô giá trị vẫn `0`.
Chương trình do LLM sinh đúng, interpreter chạy đúng, trace đúng; chỉ khúc nối
này vứt trạng thái. Đừng "tối ưu" bằng cách chỉ gửi khung đầu nữa.
"""
from __future__ import annotations

from typing import Any

from .contract import SemanticProgramSpec
from .interpreter import SemanticExecutionResult, SemanticProgramInterpreter
from .pacer import DEFAULT_PRESENTATION_BUDGET, pace
from .validator import validate_semantic_program
from .visual_adapter import VisualFrame, VisualTraceAdapter

DEFAULT_EXECUTION_BUDGET = 300

SIMULATION_ID = "generic.semantic_program"


class VisualBindingUnresolved(Exception):
    """Binding bắt buộc không phân giải được → fail-closed (bất biến #34).

    KHÔNG hạ cấp thành "bỏ đối tượng đó rồi vẫn render phần còn lại": học sinh
    thà không thấy gì còn hơn thấy một cảnh thiếu thành phần mà không ai nói
    cho biết là đang thiếu.
    """


def _assert_bindings_resolvable(
    spec: SemanticProgramSpec, exec_result: SemanticExecutionResult
) -> None:
    """Mỗi binding bắt buộc phải phân giải được ÍT NHẤT MỘT LẦN trong trace.

    Không đòi phân giải ở MỌI khung — một con trỏ chưa được gán ở bước 0 là
    bình thường. Nhưng một binding không bao giờ phân giải được là hỏng hợp
    đồng, và `validator.py` không bắt được vì `var_ref` có thể là `loop_var`
    (không nằm trong bảng ký hiệu tĩnh).
    """
    # Kiểm ở tầng BIẾN, không ở tầng id-đã-xuất-hiện: adapter phát `value_box`
    # VÔ ĐIỀU KIỆN (giá trị rỗng khi biến không có), nên đếm id sẽ bỏ lọt đúng
    # loại ghost mà bất biến này sinh ra để chặn.
    defined: set[str] = set()
    int_valued: set[str] = set()
    for step in exec_result.trace:
        for name, value in (step.memory_snapshot or {}).items():
            defined.add(name)
            # bool là subclass của int trong Python — loại ra, vì True/False
            # không phải chỉ số ô.
            if isinstance(value, int) and not isinstance(value, bool):
                int_valued.add(name)

    missing: list[str] = []

    for cb in spec.visual_bindings.containers:
        if cb.semantic_id not in defined:
            missing.append(f"container:{cb.semantic_id}")

    for pb in spec.visual_bindings.pointers:
        if pb.var_ref not in defined:
            missing.append(f"pointer:{pb.pointer_id} (biến '{pb.var_ref}' không tồn tại)")
        elif pb.var_ref not in int_valued:
            # Con trỏ phải neo vào một CHỈ SỐ. Buộc vào biến không bao giờ mang
            # giá trị nguyên thì nó không có ô nào để bám — đúng con trỏ trôi đè
            # lên chữ ở spec §0(b).
            missing.append(
                f"pointer:{pb.pointer_id} (biến '{pb.var_ref}' không bao giờ "
                "mang giá trị nguyên nên không neo được vào ô nào)"
            )

    for vb in spec.visual_bindings.value_boxes:
        if vb.var_ref not in defined:
            missing.append(f"value_box:{vb.box_id} (biến '{vb.var_ref}' không tồn tại)")

    if missing:
        raise VisualBindingUnresolved(
            "Binding bắt buộc không phân giải được ở bất kỳ khung nào: "
            + "; ".join(sorted(missing))
        )


def compile_semantic_program_to_envelope(
    spec: SemanticProgramSpec,
    execution_budget: int = DEFAULT_EXECUTION_BUDGET,
    presentation_budget: int = DEFAULT_PRESENTATION_BUDGET,
) -> dict[str, Any]:
    """Thẩm định → thực thi tất định → dựng khung → phân nhịp → envelope."""
    val_res = validate_semantic_program(spec)
    if not val_res.ok:
        raise ValueError(f"Thẩm định tĩnh SemanticProgramSpec thất bại: {val_res.error}")

    interpreter = SemanticProgramInterpreter(max_steps=execution_budget)
    exec_res: SemanticExecutionResult = interpreter.execute(spec)

    _assert_bindings_resolvable(spec, exec_res)
    frames: list[VisualFrame] = VisualTraceAdapter(spec).adapt(exec_res)

    pacing = pace(frames, budget=presentation_budget)

    config: dict[str, Any] = {
        "spec_version": "1.0",
        "title": spec.title,
        # TOÀN BỘ chuỗi khung, snapshot ĐẦY ĐỦ mỗi khung — không delta. Delta rẻ
        # hơn về byte nhưng buộc renderer có logic replay, mà logic replay chính
        # là chỗ trục hiển thị lệch khỏi trục ngữ nghĩa.
        "frames": [
            {
                "step_index": f.step_index,
                "narration": f.narration,
                "objects": f.objects,
                "highlighted_object_ids": f.highlighted_object_ids,
            }
            for f in frames
        ],
        "view_steps": [s.model_dump() for s in pacing.view_steps],
        "grouping_level": pacing.grouping_level,
        # Chạm trần TRÌNH BÀY không phải lỗi — nhưng phải KHAI đang xem ở mức nào.
        "presentation_overflow": pacing.overflow,
        # Chạm trần THỰC THI thì phải BÁO. Cấm cắt câm (luật cứng #12).
        "execution_truncated": len(frames) >= execution_budget,
    }

    return {
        "status": "ok",
        "simulation_id": SIMULATION_ID,
        "domain": "generic",
        "visual_mode": "2d",
        "title": spec.title,
        "description": spec.description or spec.title,
        "config": config,
        "notes": None,
    }
