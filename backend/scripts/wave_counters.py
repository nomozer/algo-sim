# -*- coding: utf-8 -*-
"""Ba bộ đếm của một wave đo — mỗi cái một nghĩa, không cái nào suy ra cái kia.

─── VÌ SAO CÓ FILE NÀY (REPAIR_PROBE_COUNTER_DECOMPOSITION, 2026-09-07) ────

`POINT_INITIALIZATION_REPAIR_EFFICACY` công bố `PHYSICAL_ATTEMPTS = 2` cho một
lượt chỉ phát **một** request. Bộ đếm của probe tăng ở *mọi* lần provider
callable được gọi — kể cả nhánh trả thẳng raw candidate **đọc từ artifact**,
nhánh không chạm mạng. Con số không sai; **cái tên** sai, và tên sai thì người
đọc sau kết luận sai về quota.

Ba khái niệm bị gộp làm một, tách ra ở đây:

    logical_application_calls  thao tác ứng dụng LLM mà phép đo CỐ Ý thực hiện
                               (1 synthesis mỗi arm). = `ApiBudget.logical_calls`
    physical_api_attempts      request THẬT rời tiến trình, KỂ CẢ retry
                               transport.                = `ApiBudget.http_requests`
    candidate_attempts         ứng viên chương trình đã xử lý, KỂ CẢ ứng viên
                               nạp từ artifact (0 request, 0 token)

⚠️ **KHÔNG dựng thẩm quyền đếm thứ hai.** Hai trường đầu là `@property` **đọc
thẳng** `app.ai.gemini.ApiBudget` — nơi `call_gemini` đã đếm sẵn, và là chỗ duy
nhất nhìn thấy vòng retry bên trong. Nhờ dẫn xuất chứ không đếm song song,
`physical_api_attempts` **không có đường nào** để tăng vì một ứng viên đọc từ
file: cái tăng nó nằm trong `call_gemini`, và nhánh đọc file không đi qua đó.
Đó là bằng chứng cấu trúc, và `test_counter_decomposition.py` khoá nó bằng stub.

Chỉ `candidate_attempts` là đếm tay, vì `ApiBudget` không biết tới khái niệm
"ứng viên" — nó ở tầng transport, dưới tầng chương trình.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.ai.gemini import ApiBudget  # noqa: E402

#: Nguồn ứng viên — `ARTIFACT` là ứng viên nạp từ file của lượt đo TRƯỚC.
TU_ARTIFACT = "ARTIFACT"
TU_API = "API"


class BoDemWave:
    """Ba bộ đếm, hai trong số đó DẪN XUẤT từ `ApiBudget`."""

    def __init__(self, budget: ApiBudget) -> None:
        self._budget = budget
        #: `[{"nguon": TU_ARTIFACT|TU_API, "ghi_chu": str}]` — giữ nguyên thứ tự.
        self.ung_vien: list[dict[str, str]] = []

    # ── HAI TRƯỜNG DẪN XUẤT — không có setter, cố ý ──────────────────────
    @property
    def logical_application_calls(self) -> int:
        return self._budget.logical_calls

    @property
    def physical_api_attempts(self) -> int:
        return self._budget.http_requests

    @property
    def retry_requests(self) -> int:
        """Request phát sinh do retry transient — phần CHÊNH giữa hai trường trên."""
        return self._budget.retry_requests

    # ── TRƯỜNG ĐẾM TAY ──────────────────────────────────────────────────
    @property
    def candidate_attempts(self) -> int:
        return len(self.ung_vien)

    @property
    def candidate_attempts_tu_artifact(self) -> int:
        return sum(1 for u in self.ung_vien if u["nguon"] == TU_ARTIFACT)

    def theo_ghi_chu(self) -> dict[str, int]:
        """Đếm ứng viên theo `ghi_chu` — runner truyền TÊN TẦNG vào đó."""
        ra: dict[str, int] = {}
        for u in self.ung_vien:
            k = u["ghi_chu"] or "?"
            ra[k] = ra.get(k, 0) + 1
        return ra

    def ghi_ung_vien(self, nguon: str, ghi_chu: str = "") -> None:
        if nguon not in (TU_ARTIFACT, TU_API):
            raise ValueError(f"nguồn ứng viên không hợp lệ: {nguon!r}")
        self.ung_vien.append({"nguon": nguon, "ghi_chu": ghi_chu})

    # ── BÁO CÁO ─────────────────────────────────────────────────────────
    def bao_cao(self) -> dict[str, Any]:
        """Ba trường có nghĩa riêng + phần phân rã đủ để kiểm lại."""
        return {
            "logical_application_calls": self.logical_application_calls,
            "physical_api_attempts": self.physical_api_attempts,
            "candidate_attempts": self.candidate_attempts,
            "phan_ra": {
                "candidate_attempts_tu_artifact": self.candidate_attempts_tu_artifact,
                "candidate_attempts_tu_api": (
                    self.candidate_attempts - self.candidate_attempts_tu_artifact),
                # ─── PHÂN RÃ THEO TẦNG ──────────────────────────────────
                #
                # Một wave end-to-end gọi model ở NHIỀU tầng: `analyze` trả
                # một HỢP ĐỒNG, `semantic_program` trả một CHƯƠNG TRÌNH. Gộp
                # cả hai vào `candidate_attempts` rồi đọc nó như "số ứng viên
                # chương trình" là đúng lớp hiểu nhầm mà chính đính chính này
                # đi sửa — nên tổng đi kèm phân rã, không đi một mình.
                "candidate_attempts_theo_tang": self.theo_ghi_chu(),
                "retry_requests": self.retry_requests,
                "transient_hits": self._budget.transient_hits,
                "budget_aborted": self._budget.aborted,
            },
            "dinh_nghia": {
                "logical_application_calls": "so lan call_gemini duoc goi (ApiBudget.logical_calls)",
                "physical_api_attempts": "so request HTTP THAT, ke ca retry (ApiBudget.http_requests)",
                "candidate_attempts": "so ung vien da xu ly, KE CA ung vien nap tu artifact",
            },
        }
