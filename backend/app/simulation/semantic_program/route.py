# -*- coding: utf-8 -*-
"""Ghép các cổng TẤT ĐỊNH của route sinh ngữ nghĩa thành một phán quyết.

VÌ SAO TỒN TẠI: từng mảnh — grounding P2, C₁a, C₁b, C₂, binding fail-closed —
đều đã có và đều đã được test riêng, nhưng **chưa mảnh nào được ghép lại**.
`stage_semantic_program` trước hôm nay không có một ai gọi, và smoke script thì
tự dựng chuỗi riêng (prompt → validate → execute → compile), bỏ qua sạch các
cổng. Đánh giá luận văn mà chạy trên chuỗi ấy là đo một hệ **không phải hệ được
mô tả trong luận văn** — và bất biến #22 cấm đúng điều đó.

HAI TỈ LỆ, KHÔNG PHẢI MỘT. Đây là lý do hàm dưới đây trả về một bản ghi thay vì
một `bool`:

    executable  — máy có CHẠY ĐƯỢC bài này thành mô phỏng không?
    servable    — đã đủ bằng chứng để PHÁT cho học sinh như canonical chưa?

Gộp hai cái làm một là tự bịa ra một con số không tồn tại. Một chương trình chạy
trơn tru nhưng mang nghĩa vụ chưa có checker độc lập thì `executable=True`,
`servable=False`, `verification_gap` — không phải `capability_gap`, vì nói "hệ
không làm được" trong khi nó vừa làm xong là **báo cáo sai năng lực của chính
mình** theo hướng bi quan.

R0 nguyên vẹn: mọi phán quyết ở file này TẤT ĐỊNH, đọc từ contract đã đóng băng
và từ trace do interpreter sinh. Không có một lượt LLM nào.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.simulation.error_codes import SEMANTIC_FAILURE_CATEGORY, ErrorCode

from .contract import SemanticProgramSpec
from .coverage_gate import check_realized_coverage, check_structural_coverage
from .grounding_gate import check_grounding
from .interpreter import SemanticProgramInterpreter
from .pacer import DEFAULT_PRESENTATION_BUDGET
from .pipeline_adapter import (
    DEFAULT_EXECUTION_BUDGET,
    VisualBindingUnresolved,
    compile_semantic_program_to_envelope,
)
from .postconditions import check_postconditions
from .request_contract import RequestContract


class SemanticRouteOutcome(BaseModel):
    """Phán quyết đầy đủ của route — đủ để dựng envelope VÀ để chấm benchmark."""

    #: Cổng cuối cùng đã chạy tới. Dùng để chấm A/B mà không phải suy từ mã lỗi.
    stage_reached: str
    #: Máy có dựng được mô phỏng chạy được không (claim A).
    executable: bool
    #: Có đủ bằng chứng để phát canonical không (claim B). `executable` mà
    #: `not servable` chính là `verification_gap`.
    servable: bool
    error_code: str | None = None
    failure_category: str | None = None
    reason: str | None = None
    #: Nghĩa vụ hợp lệ nhưng KHÔNG có checker server-owned (mức yếu, §5.4).
    weak_kinds: list[str] = Field(default_factory=list)
    details: list[str] = Field(default_factory=list)
    exec_status: str | None = None
    total_steps: int | None = None
    frame_count: int | None = None
    #: Trạng thái bộ nhớ CUỐI do interpreter sinh. Đây là thứ duy nhất được đem
    #: so với ground truth độc lập — so với `envelope` là so với thứ đã qua tay
    #: adapter thị giác.
    final_memory: dict[str, Any] | None = None
    envelope: dict[str, Any] | None = None


def _hong(
    stage: str,
    code: ErrorCode,
    reason: str,
    *,
    executable: bool = False,
    details: list[str] | None = None,
    weak: list[str] | None = None,
    **extra: Any,
) -> SemanticRouteOutcome:
    return SemanticRouteOutcome(
        stage_reached=stage,
        executable=executable,
        servable=False,
        error_code=code.value,
        failure_category=SEMANTIC_FAILURE_CATEGORY.get(code.value),
        reason=reason,
        details=details or [],
        weak_kinds=weak or [],
        **extra,
    )


def verify_and_compile(
    contract: RequestContract,
    spec: SemanticProgramSpec,
    *,
    execution_budget: int = DEFAULT_EXECUTION_BUDGET,
    presentation_budget: int = DEFAULT_PRESENTATION_BUDGET,
) -> SemanticRouteOutcome:
    """Contract (đã đóng băng) + IR (LLM viết) → phán quyết tất định.

    THỨ TỰ CÓ Ý NGHĨA, không tuỳ tiện:

    1. **P2 grounding** trước hết — chương trình lấy dữ liệu ở đâu ra. Sai ở đây
       thì mọi kiểm định phía sau đều đang kiểm một bài KHÁC với đề.
    2. **C₁a** trước khi chạy — chương trình có *đường* tạo ra witness không.
       Chạy rồi mới hỏi là lãng phí, và lẫn "không có đường" với "có đường mà
       không đi".
    3. **Thực thi**.
    4. **C₁b** — witness có THẬT SỰ hiện ra trong lượt chạy này không.
    5. **C₂** — hậu điều kiện server-owned.
    6. **Biên dịch** — binding fail-closed (bất biến #34) nói lời cuối.
    """
    ground = check_grounding(contract, spec)
    if not ground.ok:
        return _hong(
            "grounding",
            ErrorCode.INPUT_NOT_GROUNDED,
            "Chương trình dùng dữ liệu không truy được về đề bài.",
            details=list(ground.unresolved),
        )

    c1a = check_structural_coverage(contract, spec)
    # C₁a trả `ok=False` cho CẢ HAI mức, và chúng hoàn toàn khác nhau:
    #   REQUESTED_OPERATION_UNCOVERED     — không có đường tạo witness ⇒ CHẶN
    #   SEMANTIC_VERIFICATION_UNAVAILABLE — có đường, chỉ thiếu checker ⇒ ĐI TIẾP
    # Chặn cả hai ở đây thì bài mức yếu không bao giờ được chạy, nên
    # `executable` của nó hoá False — tức route tự khai là "không làm được" một
    # bài mà nó làm được. Đó chính là chỗ hai tỉ lệ của luận văn bị bóp thành
    # một, và bóp một cách câm.
    if not c1a.ok and c1a.error_code == "REQUESTED_OPERATION_UNCOVERED":
        return _hong(
            "structural_coverage",
            ErrorCode[c1a.error_code],
            "Chương trình không có đường tạo ra thứ đề bài yêu cầu.",
            details=list(c1a.missing),
            weak=list(c1a.weak_kinds),
        )

    try:
        exec_res = SemanticProgramInterpreter(max_steps=execution_budget).execute(spec)
    except Exception as e:  # interpreter vỡ = hệ không thực thi được bài này
        return _hong(
            "execution",
            ErrorCode.SEMANTIC_PROGRAM_INVALID,
            f"Interpreter không thực thi được chương trình: {e}",
            weak=list(c1a.weak_kinds),
        )

    # Chạm trần thực thi phải BÁO, cấm cắt câm (luật cứng #12). Trace cụt thì
    # mọi kết luận phía sau đều dựa trên một lượt chạy DỞ DANG.
    if exec_res.status == "limit_reached":
        return _hong(
            "execution",
            ErrorCode.INTERPRETER_BUDGET_EXHAUSTED,
            f"Chương trình chạm trần thực thi ({execution_budget} bước) — "
            "hệ báo thay vì cắt câm rồi giao một mô phỏng dở dang.",
            weak=list(c1a.weak_kinds),
            exec_status=exec_res.status,
            total_steps=exec_res.total_steps,
        )

    # Từ đây trở xuống máy ĐÃ chạy xong bài. Mọi thất bại còn lại nói về BẰNG
    # CHỨNG, không nói về năng lực ⇒ `executable=True`.
    da_chay = {
        "executable": True,
        "exec_status": exec_res.status,
        "total_steps": exec_res.total_steps,
        "final_memory": dict(exec_res.final_memory),
        "weak": list(c1a.weak_kinds),
    }

    c1b = check_realized_coverage(contract, spec, exec_res)
    if not c1b.ok:
        return _hong(
            "realized_coverage",
            ErrorCode[c1b.error_code],
            "Có đường tạo witness nhưng lượt chạy này không đi qua.",
            details=list(c1b.missing),
            **da_chay,
        )

    post = check_postconditions(contract, spec, exec_res)
    # C₂ nay có HAI kết cục âm, và chúng khác hẳn nhau:
    #   POSTCONDITION_VIOLATED            — chương trình tự mâu thuẫn
    #   SEMANTIC_VERIFICATION_UNAVAILABLE — checker không biểu diễn được vị từ
    # Gộp chúng là kết tội một chương trình có thể hoàn toàn đúng — lượt pilot 4
    # đo được đúng chuyện đó xảy ra hai lần.
    if post.violations:
        return _hong(
            "postconditions",
            ErrorCode.POSTCONDITION_VIOLATED,
            "Chương trình tự mâu thuẫn với nghĩa vụ nó tự khai.",
            details=list(post.violations),
            **da_chay,
        )
    if post.weak_kinds:
        da_chay["weak"] = sorted(set(da_chay["weak"]) | set(post.weak_kinds))

    try:
        # Interpreter chạy lại bên trong `compile`. Tất định nên kết quả trùng
        # khít; đổi chữ ký public của adapter chỉ để tiết kiệm một lượt chạy
        # thuần tuý không đáng, và sẽ phải sửa kèm bộ test đang khoá nó.
        envelope = compile_semantic_program_to_envelope(
            spec,
            execution_budget=execution_budget,
            presentation_budget=presentation_budget,
        )
    except VisualBindingUnresolved as e:
        return _hong(
            "binding",
            ErrorCode.SEMANTIC_PROGRAM_INVALID,
            f"Hợp đồng thị giác không phân giải được: {e}",
            **da_chay,
        )
    except (ValueError, KeyError, TypeError) as e:
        return _hong(
            "compile",
            ErrorCode.SEMANTIC_PROGRAM_INVALID,
            f"Không biên dịch được envelope: {e}",
            **da_chay,
        )

    # Mức YẾU: chạy được, biên dịch được, nhưng chưa có checker độc lập cho
    # nghĩa vụ đề đòi ⇒ KHÔNG phát canonical. Đây là `verification_gap`, và nó
    # là chỗ hai tỉ lệ của luận văn tách nhau ra.
    weak_tong = sorted(set(da_chay["weak"]))
    if weak_tong:
        code = ErrorCode.SEMANTIC_VERIFICATION_UNAVAILABLE
        return SemanticRouteOutcome(
            stage_reached="verification",
            executable=True,
            servable=False,
            error_code=code.value,
            failure_category=SEMANTIC_FAILURE_CATEGORY[code.value],
            reason=(
                "Mô phỏng chạy được nhưng hệ chưa có cách kiểm chứng độc lập "
                f"nghĩa vụ: {', '.join(weak_tong)}."
            ),
            weak_kinds=weak_tong,
            exec_status=exec_res.status,
            total_steps=exec_res.total_steps,
            frame_count=len(envelope["config"]["frames"]),
            final_memory=dict(exec_res.final_memory),
            envelope=envelope,
        )

    return SemanticRouteOutcome(
        stage_reached="served",
        executable=True,
        servable=True,
        exec_status=exec_res.status,
        total_steps=exec_res.total_steps,
        frame_count=len(envelope["config"]["frames"]),
        final_memory=dict(exec_res.final_memory),
        envelope=envelope,
    )
