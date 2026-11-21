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


# (/13) `VisualBindingUnresolved` / `_assert_bindings_resolvable` đã gỡ cùng `visual_bindings` (bất biến #34 thuộc
# đường container 2D của miền Tin học; khung hình học không mang đối tượng 2D nào để phân giải).


def validate_semantic_envelope_config(config: Any) -> str | None:
    """Kiểm HÌNH DẠNG một `config` do compiler trên sinh ra. `None` = hợp lệ.

    Vì sao ở đây chứ không ở nơi gọi: file này SỞ HỮU hình dạng ấy. Đặt luật
    cạnh nơi khác thì hai bên trôi khỏi nhau, và bên kiểm sẽ nới dần cho tới lúc
    không còn kiểm gì.

    Vì sao cần một cổng riêng: `CATALOG[sim_id].validate` không dùng được — tuyến
    ngữ nghĩa KHÔNG nằm trong `CATALOG` (nó không phải một target chuyên biệt).
    Trước bản này, cổng giao bài từ chối thẳng mọi envelope hình học, nên giáo
    viên không giao được đúng miền mà đề tài nói về.

    Luật soi đúng thứ renderer dựa vào, **mirror `validateSemanticConfig`** ở
    `frontend/src/simulations/domains/semantic/model.ts`: `view_steps` phải phủ
    kín và phủ đúng một lần `[0, len(frames) - 1]`. Lệch là học sinh gặp một
    bước trắng giữa tiết — đúng ca mà cổng này sinh ra để chặn.
    """
    if not isinstance(config, dict):
        return "Cấu hình rỗng."
    frames = config.get("frames")
    steps = config.get("view_steps")
    if not isinstance(frames, list) or not frames:
        return "Mô phỏng không có khung hình nào."
    if not isinstance(steps, list) or not steps:
        return "Mô phỏng không có bước xem nào."

    doan: list[tuple[int, int]] = []
    for s in steps:
        if not isinstance(s, dict):
            return "Bước xem không hợp lệ."
        lo, hi = s.get("frame_lo"), s.get("frame_hi")
        # `bool` là `int` trong Python — chặn thẳng, nếu không `True` lọt làm 1.
        if not isinstance(lo, int) or not isinstance(hi, int) \
                or isinstance(lo, bool) or isinstance(hi, bool):
            return "Bước xem không trỏ tới khung hình nào."
        doan.append((lo, hi))

    doan.sort()
    n = len(frames)
    if doan[0][0] != 0 or doan[-1][1] != n - 1:
        return "Các bước xem không phủ hết chuỗi khung hình."
    for i, (lo, hi) in enumerate(doan):
        if lo < 0 or hi >= n or lo > hi:
            return "Bước xem trỏ ra ngoài chuỗi khung hình."
        if i > 0 and lo != doan[i - 1][1] + 1:
            return "Các bước xem chồng lấn hoặc bỏ sót khung hình."
    return None


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
