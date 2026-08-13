# -*- coding: utf-8 -*-
"""WAVE 2 — TẦNG PHÂN LOẠI ỔN ĐỊNH CHO BENCHMARK CHƯƠNG TRÌNH HỌC.

─── VẤN ĐỀ NÓ GIẢI ────────────────────────────────────────────────────────

Benchmark cũ (`DATASET`, 30 case) mô tả **hiện thực hôm nay**: mỗi case ghi
`expect_simulation_id` là một target cụ thể. Hệ quả là thêm một năng lực mới
buộc phải sửa benchmark — tức thước đo trôi theo thứ nó đang đo.

Tầng này tách hai thứ vốn khác nhau:

  ỔN ĐỊNH  — case mô tả KIẾN THỨC và CƠ CHẾ: thuộc chương trình nào, có đáng
             mô phỏng không, cần biến gì, quan hệ nào phải hiện ra.
  DẪN XUẤT — "hệ hiện có làm được chưa" đọc TỪ REGISTRY lúc chạy.

Nhờ vậy thêm một target mới KHÔNG phải viết lại benchmark: cùng một case, hôm
nay đòi `capability_gap`, ngày mai đòi một spec hợp lệ — và chính sự chuyển đó
là bằng chứng năng lực vừa tăng.

─── VÌ SAO KHÔNG DÙNG `result_mode` CÓ SẴN ────────────────────────────────

`result_mode` trả lời "hệ trả ra cái gì" (executable / interactive_viz /
practice / unsupported) — nó nói về HIỆN THỰC. `SIMULATABILITY` trả lời một câu
khác hẳn: "bản chất kiến thức này có đáng mô phỏng không, và ở dạng nào" — đúng
sai không phụ thuộc AlgoSim có làm được hay không. Một chủ đề có thể là
`INTERACTIVE_MODEL` mà hệ chưa làm được; gộp hai trường sẽ xoá mất phân biệt ấy.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


# `DomainScope`/`Simulatability` KHÔNG định nghĩa ở đây: bản chính thuộc tầng
# production (`app/simulation/scope.py`) vì production mới là nơi PHÁN — cổng
# phạm vi đọc chính hai enum này để từ chối. Benchmark chỉ ĐO, nên nó import
# xuống chứ không dựng bộ thứ hai; hai bộ trôi khỏi nhau ở đúng chỗ quyết định
# "từ chối hay không" là kiểu trôi tệ nhất. Re-export để mọi import cũ còn chạy.
from app.simulation.scope import (  # noqa: F401  (re-export có chủ đích)
    REQUIRES_SIMULATION,
    DomainScope,
    Simulatability,
)


class CapabilityStatus(str, Enum):
    """DẪN XUẤT lúc chạy — không bao giờ viết tay vào case."""

    SUPPORTED = "SUPPORTED"          # phải ra spec tất định hợp lệ
    UNIMPLEMENTED = "UNIMPLEMENTED"  # phải ra capability_gap trung thực


#: Tên cũ của `REQUIRES_SIMULATION`. Giữ làm alias, KHÔNG dựng lại tập thứ hai —
#: hai tập cùng nghĩa mà lệch nhau thì cổng phạm vi và báo cáo sẽ phán khác nhau.
SIMULATABILITY_REQUIRES_SIMULATION = REQUIRES_SIMULATION


@dataclass(frozen=True)
class CurriculumClassification:
    """Phần ỔN ĐỊNH của một case. Không trường nào nói về target hiện tại."""

    grade: str                       # "10" | "11-CS" | "11-ICT" | "12-CS" | "12-ICT"
    domain_scope: DomainScope
    simulatability: Simulatability
    #: biến học sinh phải thấy/đổi được (vd "dãy số", "ngưỡng", "R/G/B")
    required_variables: tuple[str, ...] = ()
    #: quan hệ phải hiện ra (vd "bit ↔ trọng số", "ngưỡng ↔ tập kết quả")
    expected_relationships: tuple[str, ...] = ()
    #: có được bày cho học sinh không (fixture nội bộ thì False)
    public_eligibility: bool = True
    #: nhóm biến hình: các case cùng nhóm PHẢI cho cùng phán quyết
    metamorphic_group: str | None = None
    #: bề mặt câu chuyện (để đo "cùng cơ chế, khác vỏ")
    surface_story: str = ""


def capability_status(expect_simulation_id: str | None,
                      known_targets: frozenset[str]) -> CapabilityStatus:
    """Hệ HIỆN TẠI có target nào sở hữu cơ chế này không — đọc từ registry.

    `expect_simulation_id is None` nghĩa là case cố ý không neo vào target nào
    (câu hỏi phạm vi, câu hỏi chỉ-giải-thích) ⇒ UNIMPLEMENTED, và đúng kỳ vọng
    là hệ từ chối trung thực.
    """
    if expect_simulation_id and expect_simulation_id in known_targets:
        return CapabilityStatus.SUPPORTED
    return CapabilityStatus.UNIMPLEMENTED


def expected_outcome(classification: CurriculumClassification,
                     status: CapabilityStatus) -> str:
    """Kỳ vọng CUỐI CÙNG của một case, dẫn xuất từ hai vế trên.

    Đây là chỗ hai tầng gặp nhau, và là lý do benchmark ổn định được:
    phán quyết sư phạm giữ nguyên, năng lực đổi, kỳ vọng tự đổi theo.
    """
    if classification.domain_scope is DomainScope.OUT_OF_SCOPE:
        return "refuse_out_of_scope"
    if classification.simulatability in (Simulatability.EXPLANATION_ONLY,
                                         Simulatability.NOT_SIMULATION_SUITABLE):
        return "explanation_only"
    if status is CapabilityStatus.SUPPORTED:
        return "valid_deterministic_spec"
    return "capability_gap"

# ── NEO CHƯƠNG TRÌNH: MÃ, KHÔNG PHẢI GHI CHÚ ────────────────────────────────
#
# ⚠️ Hai lần đếm sai liên tiếp ở chính chỗ này, cùng một kiểu: coi TRƯỜNG NEO là
# văn bản tự do rồi đếm nó.
#
#   Lần 1 — đếm distinct chuỗi thô ⇒ "14 đơn vị được phủ", trong đó sáu "đơn vị"
#           thực ra là những CÂU GHI CHÚ nói rằng case đó KHÔNG neo được. Con số
#           phủ được thổi lên bằng chính lời thú nhận chưa phủ.
#   Lần 2 — sửa thành rút mã bằng regex ⇒ vẫn sai, vì câu "T10.CD1 chỉ phủ NHỊ
#           PHÂN; hệ thập lục phân ngoài phạm vi anchor" có chứa `T10.CD1`.
#           Regex ghi công đơn vị mà câu văn vừa phủ nhận, thổi T10.CD1 từ 9 lên
#           12 case.
#
# Nên trường neo nay chỉ nhận HAI dạng, và `check_anchor` từ chối dạng thứ ba:
#   · một hay nhiều MÃ  — "T10.CD1", "T11.CD4 / T10.CD2", "T11CS.CD6 (ghi chú)"
#   · khai KHÔNG NEO    — "NOT_ANCHORED — <lý do>"

#: Mã đơn vị SGK: `T10.CD1`, `T11CS.CD6`, `T12ICT.CD4`…
UNIT_CODE = re.compile(r"T\d{2}(?:CS|ICT)?\.CD\d+")

#: Tiền tố khai case CỐ Ý không neo được vào SGK. Đứng đầu chuỗi mới tính.
NOT_ANCHORED = "NOT_ANCHORED"


def unit_codes(curriculum_area: str | None) -> tuple[str, ...]:
    """Mã đơn vị mà case này THỰC SỰ phủ. Rỗng = không neo.

    Chuỗi mở đầu bằng `NOT_ANCHORED` trả về rỗng **dù bên trong có nhắc mã** —
    mã ở đó là lời giải thích *ranh giới*, không phải tuyên bố phủ.

    Trường hợp ghép ("T11.CD4 / T10.CD2") trả CẢ HAI: case ấy chạm hai đơn vị.
    """
    if not curriculum_area:
        return ()
    if curriculum_area.strip().startswith(NOT_ANCHORED):
        return ()
    return tuple(dict.fromkeys(UNIT_CODE.findall(curriculum_area)))


def check_anchor(curriculum_area: str | None) -> str | None:
    """Trả lý do trường neo KHÔNG hợp lệ, hoặc `None` nếu hợp lệ.

    Đây là cổng chặn dạng thứ ba — văn xuôi vừa không phải mã, vừa không tự khai
    là không-neo — tức đúng dạng đã hai lần làm hỏng phép đếm phủ.
    """
    if not curriculum_area or not curriculum_area.strip():
        return "trống"
    text = curriculum_area.strip()
    if text.startswith(NOT_ANCHORED):
        reason = text[len(NOT_ANCHORED):].lstrip(" —-:")
        if len(reason) < 20:
            return "khai NOT_ANCHORED nhưng không nói vì sao"
        return None
    if not UNIT_CODE.match(text):
        return (f"không mở đầu bằng mã đơn vị và không khai {NOT_ANCHORED}: {text[:60]!r}")
    return None
