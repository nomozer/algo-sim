# -*- coding: utf-8 -*-
"""M17-RC1 §R1 — ẢNH CHỤP ĐẦU VÀO của từng wave đã đóng băng.

Lỗi tái lập phát hiện ở RC1-C: `generate_m17_wave0_artifacts.py` chạy lại HÔM
NAY đọc registry MỚI NHẤT nên sinh số của Wave 2A (73 case / 19 target) thay vì
số đã công bố của Wave 1 (68 / 18). Bằng chứng lịch sử KHÔNG tái lập được —
chỉ còn "tin vào file đã commit". Đó là lỗi, không phải đặc tính.

Cách sửa — phương án C của §R1: **đọc frozen input matrix thay vì registry
sống**. Mỗi wave đóng băng có `input_snapshot.json` nằm NGAY CẠNH artifact nó
mô tả, chứa TOÀN BỘ đầu vào:

- `cases[]`     — đúng tập case, đúng thứ tự, kèm archetype/expected/prompt VÀ
  `script` (analysis + classify_seq + simulate_seq) NGUYÊN BẢN của wave đó;
- `gate_names`  — cổng TỒN TẠI ở wave đó (cổng thêm sau vẫn CHẠY thật nhưng
  không được ghi vào bản ghi lịch sử — cùng nguyên tắc `M16_GATE_NAMES`);
- `target_ids`  — target AI-reachable tại wave đó;
- `git_commit` + `generated_at` — để `run_meta` tái lập byte;
- `artifact_sha256` — khoá nội dung từng file đã công bố;
- `input_snapshot_id` + `generator_version`.

Vì sao phải ghim CẢ SCRIPT chứ không chỉ danh sách case: chính định nghĩa case
cũng trôi. W2A viết lại `aud-regression-tree-*` (classify từ `generic.rule_scene`
sang `tree.traversal`) để ghi nhận năng lực mới — chạy lại bằng fixture sống
cho ra `ok → tree.traversal` thay vì `capability_gap` đã công bố, dù pipeline
xử ĐÚNG ở cả hai thời điểm.

Snapshot được TRÍCH TỰ ĐỘNG từ chính source tại commit của wave (git worktree),
KHÔNG viết tay và KHÔNG suy đoán từ kết quả.

Điều snapshot KHÔNG đóng băng: bản thân `run_pipeline`. Đó là chủ đích — nếu
một thay đổi production làm kết quả case lịch sử đổi, test tái lập sẽ ĐỎ. Đó
là điều cần biết, không phải điều cần che.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_WAVE_DIR = Path(__file__).resolve().parents[3] / "docs" / "evaluation" / "m17"
GENERATOR_VERSION = "m17-wave-artifacts-2"

# Wave ĐÃ ĐÓNG BĂNG (có input_snapshot.json). Wave đang mở không nằm ở đây →
# generator đọc registry sống như trước.
FROZEN_WAVES: tuple[str, ...] = ("wave0", "wave1")


@dataclass(frozen=True)
class CaseSnapshot:
    """Đầu vào đã đóng băng của MỘT case — đủ để replay không cần fixture sống."""

    case_id: str
    sim_id: str | None
    archetype: str
    prompt_vi: str
    expected_status: str
    expected_route: str | None
    mechanism: str | None
    note: str
    analysis: dict
    classify_seq: list
    simulate_seq: list


@dataclass(frozen=True)
class WaveSnapshot:
    wave_id: str
    input_snapshot_id: str
    generator_version: str
    git_commit: str
    generated_at: str
    gate_names: frozenset[str]
    target_ids: tuple[str, ...]
    cases: tuple[CaseSnapshot, ...]
    artifact_sha256: dict[str, str]

    @property
    def case_ids(self) -> tuple[str, ...]:
        return tuple(c.case_id for c in self.cases)

    @property
    def case_count(self) -> int:
        return len(self.cases)

    @property
    def target_count(self) -> int:
        return len(self.target_ids)

    @property
    def family_count(self) -> int:
        """Family của wave — suy từ target CỦA WAVE qua CATALOG hiện tại
        (target lịch sử vẫn tồn tại; family của chúng không đổi)."""
        from app.simulation.catalog import CATALOG

        return len({
            m.family_id.value
            for t in self.target_ids if t in CATALOG
            for m in CATALOG[t].family_memberships
        })


@lru_cache(maxsize=None)
def snapshot_for(wave_id: str) -> WaveSnapshot | None:
    """Ảnh chụp của wave đã đóng băng; None nếu wave còn mở (đọc registry sống)."""
    path = _WAVE_DIR / wave_id / "input_snapshot.json"
    if wave_id not in FROZEN_WAVES or not path.exists():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    return WaveSnapshot(
        wave_id=raw["wave_id"],
        input_snapshot_id=raw["input_snapshot_id"],
        generator_version=raw["generator_version"],
        git_commit=raw["git_commit"],
        generated_at=raw["generated_at"],
        gate_names=frozenset(raw["gate_names"]),
        target_ids=tuple(raw["target_ids"]),
        cases=tuple(
            CaseSnapshot(
                case_id=c["case_id"], sim_id=c["sim_id"], archetype=c["archetype"],
                prompt_vi=c["prompt_vi"], expected_status=c["expected_status"],
                expected_route=c["expected_route"], mechanism=c["mechanism"],
                note=c.get("note", ""), analysis=c["script"]["analysis"],
                classify_seq=c["script"]["classify_seq"],
                simulate_seq=c["script"]["simulate_seq"],
            )
            for c in raw["cases"]
        ),
        artifact_sha256=dict(raw["artifact_sha256"]),
    )


__all__ = [
    "FROZEN_WAVES",
    "GENERATOR_VERSION",
    "CaseSnapshot",
    "WaveSnapshot",
    "snapshot_for",
]
