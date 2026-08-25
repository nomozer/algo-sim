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
from .learner_surface import check_learner_surface
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
    #: QUAN TRẮC grounding — không gác cửa, không vào A/B, không tầng nào đọc để
    #: chấm. Có mặt vì PHASE 5 lượt 2 không đo được **mức lệch danh xưng giữa hai
    #: lượt LLM**: mọi ca grounding đều phát cùng một câu `reason`, còn số lượng
    #: giả thiết và trích dẫn hỏng thì mất hẳn. Ghi ra đây để lượt sau đếm được
    #: thay vì suy.
    grounding_assumptions: list[str] = Field(default_factory=list)
    grounding_unresolved_citations: list[str] = Field(default_factory=list)
    #: Cảnh 3D của miền hình học — **một Ô TRỐNG, không phải một phép tính**.
    #:
    #: `route` KHÔNG dựng nó và KHÔNG import `scene3d`: hướng phụ thuộc một
    #: chiều (engine không được biết tới tầng trình bày) là thứ
    #: `test_scene3d.py::test_KHONG_module_nao_o_TANG_DUOI_nhap_scene3d` giữ.
    #: Khai kiểu `dict` ở đây cho phép người GỌI đổ vào mà không ai phải nới
    #: ranh giới ấy — `pipeline._dung_scene3d` là người đổ.
    #:
    #: `None` khi bài không phải hình học, hoặc khi chương trình không chạy nổi.
    scene3d: dict[str, Any] | None = None


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
    """Bọc mỏng quanh `_sau_grounding` để **gắn quan trắc grounding ở MỘT chỗ**.

    Thân hàm có 11 điểm thoát. Gắn tay vào từng chỗ thì lần thêm nhánh tiếp theo
    chắc chắn sót một cái, và sót ở đây là im lặng: trường quan trắc rỗng đọc
    y hệt "không có giả thiết nào", nên số liệu sai mà không ai thấy.
    """
    ground = check_grounding(contract, spec)
    kq = _sau_grounding(
        contract, spec, ground,
        execution_budget=execution_budget,
        presentation_budget=presentation_budget,
    )
    return kq.model_copy(update={
        "grounding_assumptions": list(ground.assumptions),
        "grounding_unresolved_citations": list(ground.unresolved_citations),
    })


def _sau_grounding(
    contract: RequestContract,
    spec: SemanticProgramSpec,
    ground,
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
    if not ground.ok:
        # `ErrorCode` giữ nguyên — đây vẫn là một thất bại grounding, và mở rộng
        # enum là đụng vào bề mặt mọi tầng phía sau đọc. Nhưng mã CHI TIẾT phải
        # lộ ra ở `details`: "khai đáp án làm giả thiết" và "không truy được về
        # đề bài" là hai bệnh khác hẳn nhau, và gộp chúng thì lượt phân loại
        # thất bại sau sẽ đếm nhầm — đúng cái Phase 5 vừa phải khai là thiếu sót.
        chi_tiet = list(ground.unresolved)
        if ground.error_code and ground.error_code != "INPUT_NOT_GROUNDED":
            chi_tiet.insert(0, f"[{ground.error_code}]")
        return _hong(
            "grounding",
            ErrorCode.INPUT_NOT_GROUNDED,
            "Chương trình dùng dữ liệu không truy được về đề bài.",
            details=chi_tiet,
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
        # `details` phải có LOẠI lỗi tách khỏi lời kể. Đo được ở Wave 3.5: đây
        # là tầng DUY NHẤT trong bốn tầng phát ra `details` rỗng, nên một lượt
        # vỡ ở kernel chỉ để lại một câu tiếng Việt — và phân loại thất bại sau
        # đó không phân biệt được "song song nên không giao" với "chỉ số đỉnh
        # ngoài biên", hai bệnh mà kernel đã cố ý tách bằng mã lỗi riêng.
        ma = getattr(e, "code", None)
        return _hong(
            "execution",
            ErrorCode.SEMANTIC_PROGRAM_INVALID,
            f"Interpreter không thực thi được chương trình: {e}",
            details=[f"[{ma or type(e).__name__}]", str(e)],
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

    c1b = check_realized_coverage(contract, spec, exec_res,
                                  ten_da_hoa_giai=c1a.ten_da_hoa_giai)
    if not c1b.ok:
        return _hong(
            "realized_coverage",
            ErrorCode[c1b.error_code],
            "Có đường tạo witness nhưng lượt chạy này không đi qua.",
            details=list(c1b.missing),
            **da_chay,
        )

    post = check_postconditions(contract, spec, exec_res,
                                ten_da_hoa_giai=c1a.ten_da_hoa_giai)
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

    # BỀ MẶT HỌC SINH — cổng cuối, và là cổng DUY NHẤT quay về phía màn hình.
    #
    # Mọi cổng phía trên nhìn về phía CHƯƠNG TRÌNH: cú pháp, dữ liệu, phủ nghĩa
    # vụ, hậu điều kiện, binding có phân giải được. Qua hết chúng vẫn còn lọt
    # được đúng thứ đã ship: chương trình chạy đúng, lời kể đúng, envelope sạch —
    # mà ngăn xếp trên hình rỗng suốt bảy bước. Chạy SAU `compile` vì câu hỏi là
    # về những khung SẼ ĐƯỢC PHÁT, không phải về ý định của chương trình.
    surface = check_learner_surface(contract, spec, exec_res, envelope)
    if not surface.ok:
        code = ErrorCode.LEARNER_SURFACE_INCOMPLETE
        return SemanticRouteOutcome(
            stage_reached="learner_surface",
            # `executable=True` là CÓ CHỦ ĐÍCH: hệ chạy được bài này. Cái thiếu
            # là đường lên màn hình, không phải năng lực.
            executable=True,
            servable=False,
            error_code=code.value,
            failure_category=SEMANTIC_FAILURE_CATEGORY[code.value],
            reason=(
                "Mô phỏng chạy được nhưng màn hình chưa mang đủ thông tin để "
                "hiểu bài: " + "; ".join(surface.invisible)
            ),
            details=list(surface.invisible),
            weak_kinds=sorted(set(da_chay["weak"])),
            exec_status=exec_res.status,
            total_steps=exec_res.total_steps,
            frame_count=len(envelope["config"]["frames"]),
            final_memory=dict(exec_res.final_memory),
            envelope=envelope,
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
