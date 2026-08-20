# -*- coding: utf-8 -*-
"""PresentationPacer — gộp khung máy thành BƯỚC XEM.

VÌ SAO GỘP NẰM Ở ĐÂY, KHÔNG NẰM TRONG VisualTraceAdapter:
adapter phải giữ song ánh `frame k ⇔ trace[k]`; có song ánh đó thì bất biến
#31 (khung ⇔ trạng thái) mới là ĐỊNH LÝ chứ không phải lời hứa. Gộp bên trong
adapter là phá chính song ánh ấy.

HAI NGÂN SÁCH TÁCH HẲN (bất biến #12 của RULES, sinh từ sự cố `steps[:20]`):
- ngân sách THỰC THI  → interpreter; chạm trần phải BÁO.
- ngân sách TRÌNH BÀY → ở đây; chạm trần KHÔNG phải lỗi, hạ mức chi tiết.

Gộp "chạy được bao xa" với "xem được bao nhiêu" vào một con số chính là cách
DSL cũ cắt câm 280 bước mà không ai biết.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .visual_adapter import VisualFrame

DEFAULT_PRESENTATION_BUDGET = 60


class ViewStep(BaseModel):
    view_index: int = Field(..., description="Chỉ số bước xem")
    frame_lo: int = Field(..., description="Khung máy đầu của đoạn (inclusive)")
    frame_hi: int = Field(..., description="Khung máy cuối của đoạn (inclusive)")
    narration: str = Field(..., description="Thuyết minh của bước xem")


class PacingResult(BaseModel):
    view_steps: list[ViewStep] = Field(default_factory=list)
    grouping_level: Literal["step", "iteration"] = "step"
    overflow: bool = Field(
        False,
        description="True khi mức thô nhất VẪN vượt ngân sách — phải BÁO, "
        "không được lặng lẽ cắt",
    )


def pace(
    frames: list[VisualFrame], budget: int = DEFAULT_PRESENTATION_BUDGET
) -> PacingResult:
    """Phân hoạch `frames` thành các bước xem liên tiếp.

    Bất biến: các đoạn phủ ĐẦY ĐỦ dãy khung, KHÔNG chồng lấn, và KHÔNG sinh
    khung mới. Khung máy được *gộp*, không bị *bỏ*.
    """
    if not frames:
        return PacingResult()

    if len(frames) <= budget:
        return PacingResult(
            view_steps=[
                ViewStep(view_index=i, frame_lo=i, frame_hi=i, narration=f.narration)
                for i, f in enumerate(frames)
            ],
            grouping_level="step",
            overflow=False,
        )

    # Gộp đều: mỗi bước xem ôm `size` khung liên tiếp. Lấy trần để số đoạn
    # không bao giờ vượt ngân sách, và đoạn cuối tự ngắn lại — phân hoạch vẫn
    # đầy đủ vì `hi` bị kẹp về khung cuối.
    size = -(-len(frames) // budget)
    steps: list[ViewStep] = []
    lo = 0
    while lo < len(frames):
        hi = min(lo + size - 1, len(frames) - 1)
        steps.append(
            ViewStep(
                view_index=len(steps),
                frame_lo=lo,
                frame_hi=hi,
                # Thuyết minh của bước xem = thuyết minh khung CUỐI đoạn: đó là
                # trạng thái người học nhìn thấy sau khi đoạn này chạy xong.
                narration=frames[hi].narration,
            )
        )
        lo = hi + 1

    return PacingResult(
        view_steps=steps,
        grouping_level="iteration",
        overflow=len(steps) > budget,
    )
