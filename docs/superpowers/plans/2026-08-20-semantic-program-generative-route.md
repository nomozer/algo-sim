# Đường sinh ngữ nghĩa `generic.semantic_program` — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Nối `semantic_program` vào pipeline sản xuất thành một route riêng, nơi LLM sinh bounded Semantic IR còn engine tất định thực thi, kiểm chứng và diễn hoạt — sửa dứt điểm lỗi "narration bước 15, hình bước 0".

**Architecture:** Route mới `generic.semantic_program` chạy song song đường module. Chuỗi: `analyze → RequestContract (đóng băng nghĩa vụ) → stage_semantic_program (LLM, 1 lượt) → validator tĩnh → interpreter (execution budget) → VisualTraceAdapter (1:1 với trace) → PresentationPacer (presentation budget) → envelope mang frame timeline`. Cổng: `scope_gate` giữ nguyên · `execution_authority_gate` thay `computation_gate` · `SemanticCoverageGate` C₁a/C₁b thay `completeness_gate` · `semantic_input_grounding_gate` thay `check_input_sufficiency`.

**Tech Stack:** Python 3.12 + Pydantic v2 + FastAPI (backend) · React 18 + TypeScript + Zustand + Vite (frontend) · pytest · vitest · Playwright · Gemini API (structured output).

**Spec:** `docs/superpowers/specs/2026-08-20-semantic-program-generative-route-design.md` (APPROVED DESIGN, commit `0c53882`)

## Global Constraints

Sao nguyên văn từ spec §1.1. Mọi task đều ngầm chịu các ràng buộc này.

- **MVP route:** `generic.semantic_program` v1 = **algorithmic bounded IR + 2D only + không mở primitive/type mới.**
- **R0:** LLM **không bao giờ** là authority của kết quả. `SemanticProgramInterpreter` được công nhận là authority tất định cho một lớp algorithmic computation có biên.
- **Hard scope lock:** Sau khi SEALED niêm phong — KHÔNG thêm `MemoryType`, statement kind, visual primitive, obligation checker, hay template theo target để cải thiện kết quả SEALED. Thay đổi như vậy làm seal **mất hiệu lực**.
- **Luật con dấu:** DEV được phép làm thay đổi IR. SEALED chỉ được phép làm thay đổi **kết luận của luận văn**.
- **Cấm cắt câm:** chạm trần ngân sách phải **báo**, không được lặng lẽ giao một phần.
- **Serving gate:** đăng ký route ≠ bật cho học sinh. Learner-facing chỉ bật sau khi đủ chuỗi `RequestContract → P2 → C₁a → validator → interpreter → C₁b → C₂ → STRONG`.
- **Không** đi qua `dsl/validator.py` trên route mới (tránh trần 20 bước + bộ 4 action).
- **Offline-first:** `pytest`/`vitest` = **0 API call thật**. Live AI cần `ALLOW_LIVE_AI=1` + **xin phép user trước**.
- **Tiếng Việt trên mọi bề mặt học sinh.** Định danh kĩ thuật (`simulation_id`, reason_code, tên field) **không được lọt lên UI**.
- **Commit:** conventional commit, scope theo miền, **không** dùng trailer `Co-Authored-By`.
- **Lệnh:** Python luôn dùng `backend/.venv/Scripts/python.exe`, chạy **từ `backend/`**. Đặt `PYTHONIOENCODING=utf-8`.

## Machine gate, không phải cổng xin phép

Mỗi task kết thúc bằng test xanh → **tự động đi tiếp**. Chỉ DỪNG và hỏi user khi:

1. test/invariant bắt buộc không qua sau khi đã thử sửa;
2. cần mở phạm vi ngoài §1.1;
3. cần mở IR vì một case SEALED;
4. phải hạ assurance để serve;
5. phải làm một thứ trong §9 "không thuộc spec";
6. live call cần vượt budget đã định;
7. kiến trúc thực tế mâu thuẫn với spec.

Lỗi code thường: **tự sửa và tiếp tục.**

## File Structure

| File | Trách nhiệm |
|---|---|
| `backend/app/simulation/semantic_program/pacer.py` | **Mới.** `PresentationPacer` — gộp khung máy thành bước xem; presentation budget |
| `backend/app/simulation/semantic_program/pipeline_adapter.py` | **Sửa nặng.** Envelope mang frame timeline; fail-closed binding |
| `backend/app/simulation/semantic_program/visual_adapter.py` | **Sửa.** Thêm nhánh `bar_chart`; khai `HANDLED_PRIMITIVES` |
| `backend/app/simulation/semantic_program/obligations.py` | **Mới.** Obligation taxonomy + checker server-owned |
| `backend/app/simulation/semantic_program/request_contract.py` | **Mới.** `RequestContract` — đóng băng nghĩa vụ |
| `backend/app/simulation/semantic_program/coverage_gate.py` | **Mới.** C₁a structural + C₁b realized |
| `backend/app/simulation/semantic_program/grounding_gate.py` | **Mới.** P2 tất định + khai giới hạn P1 |
| `backend/app/simulation/execution_authority_gate.py` | **Mới.** Thay khái niệm `computation_gate` |
| `backend/app/ai/pipeline.py` | **Sửa.** `stage_semantic_program`; nhánh route mới; bỏ enum catalog khỏi analyze |
| `backend/app/ai/telemetry.py` | **Mới.** Ghi `usage_metadata` theo stage |
| `frontend/src/simulations/domains/semantic/` | **Mới.** Module render frame timeline (2D) |
| `docs/evaluation/semantic-benchmark/` | **Mới.** DEV + SEALED + fingerprint |

---

## Task 0: Scope rebaseline — mở khoá phạm vi trước mọi thứ khác

**Files:**
- Modify: `docs/STATUS_LEDGER.md` (§0)
- Modify: `docs/RULES.md`
- Modify: `docs/ARCHITECTURE_MAP.md`

**Interfaces:**
- Consumes: spec §8
- Produces: quyền hợp lệ để mọi task sau chạy mà không bị scope guard bắt dừng

> **Vì sao đây là bước 0:** chừng nào ledger còn xếp hướng này ngoài mục tiêu thì mọi phiên agent sau — kể cả phiên đang thực thi plan này — đều có nghĩa vụ tự dừng theo `RULES.md §3d`.

- [ ] **Step 1: Đọc §0 của ledger để biết chính xác dòng nào khoá phạm vi**

Run: `grep -n "KHÔNG phải mục tiêu\|đóng băng\|ngoài phạm vi" docs/STATUS_LEDGER.md | head -20`

- [ ] **Step 2: Cập nhật `docs/STATUS_LEDGER.md §0`**

Thêm vào §0, giữ nguyên phần còn lại:

```markdown
### 2026-08-20 — MỞ LẠI phạm vi "sinh mô phỏng" (nguồn: giáo viên hướng dẫn)

Khoá phạm vi 2026-08 (24 target, không sinh tự động) **được thay thế ở đúng
phần sinh mô phỏng** bởi `docs/superpowers/specs/2026-08-20-semantic-program-generative-route-design.md`.

- Phạm vi mới **hẹp và có hàng rào**: xem §1.1 của spec (2D only · bounded IR ·
  6 ranh giới · hard scope lock).
- **Vẫn ngoài mục tiêu:** HTML/CSS · CSDL · đóng gói giao thức generative ·
  3D cho route mới · tắt 24 module cũ · pattern reuse · explicit context caching.
- Task rơi vào danh sách "vẫn ngoài mục tiêu" → `docs/POST_THESIS_BACKLOG.md`.
```

- [ ] **Step 3: Cập nhật `docs/RULES.md` — ba luật cứng, giữ đúng vai con trỏ**

`rules-hygiene.test.ts` khoá file này giữ vai con trỏ — viết **ngắn, trỏ sang spec**, không chép kiến trúc vào:

```markdown
- **Authority của kết quả** (làm sắc R0, không nới): kết quả phải có một
  **authority tất định** sở hữu. `SemanticProgramInterpreter` là một authority.
  LLM **không bao giờ** là authority. Chi tiết: spec 2026-08-20 §3.3.
- **Cấm cắt câm**: chạm trần ngân sách phải BÁO, không được lặng lẽ giao một
  phần. Sinh ra từ `MAX_REVEAL_STEPS` cắt `steps[:20]` không báo lỗi. §4.3.
- **Nghĩa vụ đóng băng trước khi sinh chương trình**: `analyze` khai, server
  đóng băng thành `RequestContract`; stage sinh **không** được khai lại. §5.2.
```

- [ ] **Step 4: Cập nhật `docs/ARCHITECTURE_MAP.md`**

Bảng sở hữu — thêm hàng: `interpreter` sở hữu trace · `VisualTraceAdapter` sở hữu frame · `PresentationPacer` sở hữu bước xem · renderer vẫn **chỉ ĐỌC**.

Hướng phụ thuộc: `contract ← validator ← interpreter ← adapter ← pacer ← envelope` — không được đảo.

Bất biến đánh số mới (mỗi cái kèm nơi thực thi + test khoá):

```markdown
| #31 | Khung ⇔ trạng thái: frame k suy hoàn toàn từ trace[k].memory_snapshot | `visual_adapter.py` | `test_frame_state_invariant.py` |
| #32 | Pacer phân hoạch đầy đủ, không chồng lấn, không sinh khung mới | `pacer.py` | `test_pacer_partition.py` |
| #33 | Mọi primitive trong enum có nhánh adapter | `visual_adapter.py` | `test_primitive_coverage.py` |
| #34 | Binding bắt buộc phải phân giải được — fail-closed | `pipeline_adapter.py` | `test_binding_fail_closed.py` |
```

Anti-pattern — thêm mục: *"Cầu nối giữ khung đầu rồi phát narration chạy"* — đã ship bug thật, spec §0(b).

- [ ] **Step 5: Chạy guard hygiene**

Run: `cd frontend && npx vitest run src/rules-hygiene.test.ts`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add docs/STATUS_LEDGER.md docs/RULES.md docs/ARCHITECTURE_MAP.md
git commit -m "docs(scope): rebaseline pham vi cho duong sinh semantic_program"
```

---

## Task 1: Dựng DEV + SEALED, đóng băng rubric và fingerprint

**Files:**
- Create: `docs/evaluation/semantic-benchmark/eligibility_rubric.md`
- Create: `docs/evaluation/semantic-benchmark/freeze_protocol.md`
- Create: `docs/evaluation/semantic-benchmark/dev/cases.json`
- Create: `docs/evaluation/semantic-benchmark/sealed/cases.json`
- Create: `docs/evaluation/semantic-benchmark/sealed/FINGERPRINT.txt`
- Create: `backend/scripts/seal_benchmark.py`
- Test: `backend/tests/semantic_program/test_benchmark_seal.py`

**Interfaces:**
- Consumes: spec §7.2 (rubric), §7.3 (freeze protocol), §7.4 (luật con dấu)
- Produces: `sealed/FINGERPRINT.txt` (sha256 của `sealed/cases.json`); `dev/cases.json` là **nguồn duy nhất** được dùng để chỉnh IR/schema/prompt

> **RÀNG BUỘC NGƯỜI THỰC HIỆN — DỪNG VÀ HỎI USER Ở STEP 3.**
> Agent viết prompt/schema **không được là người soạn SEALED** — đã đọc case là
> đã rò con dấu qua ngữ cảnh. DEV do agent soạn; **SEALED phải do user cung cấp
> nguồn ngoài** (SGK, đề thi, bài tập có sẵn). Agent chỉ **audit theo rubric** rồi
> khoá fingerprint.

- [ ] **Step 1: Viết `eligibility_rubric.md` (chép nguyên §7.2 của spec)**

```markdown
# Eligibility rubric — định nghĩa population, độc lập cài đặt

Chốt 2026-08-20, TRƯỚC khi dựng benchmark. KHÔNG tham chiếu Semantic IR.

Một bài **in-scope** khi thoả TẤT CẢ:

1. Rời rạc, đầu vào hữu hạn.
2. Có thủ tục tất định, execution hữu hạn / có biên.
3. Trạng thái gồm scalar và cấu trúc dữ liệu rời rạc: dãy/chuỗi, stack, queue,
   set, map, matrix, tree, graph.
4. Thao tác thuộc: gán · so sánh · truy cập · cập nhật · duyệt · push/pop ·
   enqueue/dequeue.
5. KHÔNG phụ thuộc solver liên tục, môi trường bên ngoài, miền phi-thuật-toán.

Không thoả rubric → NGOÀI population, không đưa vào benchmark.
Thoả rubric nhưng IR hiện tại không diễn đạt được → VẪN Ở TRONG benchmark,
kết quả `capability_gap`. Đó là phát hiện phải báo cáo, không phải sự cố cần vá.
```

- [ ] **Step 2: Viết `freeze_protocol.md` (chép §7.3)**

```markdown
# Freeze protocol

Đóng băng TRƯỚC khi seal, không sửa về sau:
- eligibility rubric · N và cách lấy mẫu · primary metrics (A và B đồng-primary)
- assurance policy (thanh STRONG/WEAK cố định) · ground-truth procedure
- cách tính refusal/success · trường hợp bị loại · obligation taxonomy

KHÔNG đặt pass mark tuỳ tiện. Luận văn báo kết quả như nó là.
Thứ đóng băng là CÁCH ĐO, không phải mức điểm mong muốn.

Release cho học sinh: canonical case biết là sai → FAIL RELEASE.
Không hạ thanh assurance để tỉ lệ đẹp hơn.
```

- [ ] **Step 3: DỪNG — xin user nguồn cho SEALED**

Hỏi user: nguồn đề cho SEALED (SGK lớp mấy / đề thi / bài tập), số lượng N mong muốn, và ai soạn ground truth. **Không tự bịa case SEALED.**

- [ ] **Step 4: Soạn DEV cases (agent làm được)**

`dev/cases.json` — mỗi case:

```json
{
  "case_id": "dev_001",
  "prompt": "Mô phỏng thuật toán tìm giá trị lớn nhất trong dãy [3, 9, 2, 7].",
  "eligibility": {
    "discrete_finite_input": true,
    "deterministic_bounded_procedure": true,
    "state_kinds": ["array", "int"],
    "operation_kinds": ["gán", "so sánh", "duyệt"],
    "no_continuous_solver": true
  },
  "metadata": {
    "no_specialized_module": false,
    "no_target_template": false,
    "not_prompt_example": true,
    "expressible_in_ir": true
  },
  "expected_obligations": ["extremum(a, max)"],
  "ground_truth": {"source": "human_authored", "final_state": {"max_val": 9}}
}
```

- [ ] **Step 5: Viết `seal_benchmark.py`**

```python
# -*- coding: utf-8 -*-
"""Khoá fingerprint cho SEALED benchmark. Chạy MỘT LẦN, trước khi phát triển."""
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEALED = ROOT / "docs" / "evaluation" / "semantic-benchmark" / "sealed" / "cases.json"
FINGERPRINT = SEALED.parent / "FINGERPRINT.txt"


def fingerprint_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    if not SEALED.exists():
        print(f"Thiếu {SEALED}")
        return 2
    digest = fingerprint_of(SEALED)
    if FINGERPRINT.exists():
        old = FINGERPRINT.read_text(encoding="utf-8").strip()
        if old != digest:
            print(f"SEAL VỠ: fingerprint cũ {old} != mới {digest}")
            return 1
        print("Fingerprint khớp — seal còn nguyên.")
        return 0
    FINGERPRINT.write_text(digest + "\n", encoding="utf-8")
    print(f"Đã niêm phong: {digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 6: Viết test khoá con dấu**

```python
# backend/tests/semantic_program/test_benchmark_seal.py
# -*- coding: utf-8 -*-
import hashlib
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[3]
SEALED = ROOT / "docs" / "evaluation" / "semantic-benchmark" / "sealed" / "cases.json"
FINGERPRINT = SEALED.parent / "FINGERPRINT.txt"


@pytest.mark.skipif(not SEALED.exists(), reason="SEALED chưa được dựng (Task 1 step 3)")
def test_sealed_khong_bi_sua_sau_khi_niem_phong():
    expected = FINGERPRINT.read_text(encoding="utf-8").strip()
    actual = hashlib.sha256(SEALED.read_bytes()).hexdigest()
    assert actual == expected, (
        "SEALED benchmark đã bị sửa sau khi niêm phong. Theo luật con dấu "
        "(spec §7.4), dataset này trở thành DEV/history và phải tạo SEALED mới."
    )
```

- [ ] **Step 7: Chạy test**

Run: `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/semantic_program/test_benchmark_seal.py -v`
Expected: PASS (hoặc SKIP nếu chưa có SEALED)

- [ ] **Step 8: Commit**

```bash
git add docs/evaluation/semantic-benchmark backend/scripts/seal_benchmark.py backend/tests/semantic_program/test_benchmark_seal.py
git commit -m "test(semantic-program): dung DEV/SEALED benchmark va khoa fingerprint"
```

---

## Task 2: Bất biến L3 — viết test ĐỎ chứng minh E1 là thật

**Files:**
- Create: `backend/tests/semantic_program/test_frame_state_invariant.py`

**Interfaces:**
- Consumes: `compile_semantic_program_to_envelope(spec)` · `SemanticProgramInterpreter` · `VisualTraceAdapter` · fixture `P01_STACK_BRACKET` từ `fixtures_coverage_18.py`
- Produces: bất biến #31 — hợp đồng mà Task 3 phải làm thoả

- [ ] **Step 1: Viết test**

```python
# backend/tests/semantic_program/test_frame_state_invariant.py
# -*- coding: utf-8 -*-
"""Bất biến #31 — khung hình k suy hoàn toàn từ trạng thái bước k.

Test này ĐỎ trước khi Task 3 sửa: `pipeline_adapter` hiện chỉ giữ
`frames[0].objects` rồi vứt mọi khung sau (spec E1).
"""
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.pipeline_adapter import compile_semantic_program_to_envelope
from app.simulation.semantic_program.validator import validate_semantic_program
from app.simulation.semantic_program.visual_adapter import VisualTraceAdapter
from tests.semantic_program.fixtures_coverage_18 import P01_STACK_BRACKET


def _frames_of(spec):
    val = validate_semantic_program(spec)
    assert val.ok, val.error
    exec_res = SemanticProgramInterpreter(max_steps=300).execute(spec)
    return VisualTraceAdapter(spec).adapt(exec_res)


def test_envelope_giu_du_moi_khung_cua_adapter():
    spec = P01_STACK_BRACKET
    frames = _frames_of(spec)
    env = compile_semantic_program_to_envelope(spec)

    cfg_frames = env["config"]["frames"]
    assert len(cfg_frames) == len(frames), (
        f"Envelope giữ {len(cfg_frames)} khung nhưng adapter sinh {len(frames)}"
    )
    for k, f in enumerate(frames):
        assert cfg_frames[k]["objects"] == f.objects, f"Khung {k} lệch trạng thái"


def test_ngan_xep_khong_dong_bang_o_khung_0():
    """Hồi quy trực tiếp cho ảnh chụp ở spec §0(b): narration chạy, hình đứng."""
    env = compile_semantic_program_to_envelope(P01_STACK_BRACKET)
    stacks = [
        obj
        for frame in env["config"]["frames"]
        for obj in frame["objects"]
        if obj.get("type") == "stack_view"
    ]
    assert stacks, "Không có stack_view nào trong timeline"
    assert any(s.get("items") for s in stacks), (
        "Mọi khung đều có ngăn xếp RỖNG — hình đóng băng ở bước 0 (lỗi E1)"
    )
```

- [ ] **Step 2: Chạy test để xác nhận nó ĐỎ**

Run: `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/semantic_program/test_frame_state_invariant.py -v`
Expected: **FAIL** với `KeyError: 'frames'` — envelope hiện chưa có khoá `frames`.

> Nếu test này **XANH** ngay: dừng lại, kiến trúc thực tế mâu thuẫn với spec E1 (điều kiện dừng #7).

- [ ] **Step 3: Commit test đỏ**

```bash
git add backend/tests/semantic_program/test_frame_state_invariant.py
git commit -m "test(semantic-program): khoa bat bien khung-trang thai (RED)"
```

---

## Task 3: Frame timeline + PresentationPacer + hai ngân sách + bar_chart + fail-closed

**Files:**
- Create: `backend/app/simulation/semantic_program/pacer.py`
- Modify: `backend/app/simulation/semantic_program/pipeline_adapter.py` (viết lại `compile_semantic_program_to_envelope`)
- Modify: `backend/app/simulation/semantic_program/visual_adapter.py` (thêm `HANDLED_PRIMITIVES`, nhánh `bar_chart`)
- Modify: `backend/app/simulation/semantic_program/__init__.py` (export mới)
- Test: `backend/tests/semantic_program/test_pacer_partition.py`
- Test: `backend/tests/semantic_program/test_primitive_coverage.py`
- Test: `backend/tests/semantic_program/test_binding_fail_closed.py`

**Interfaces:**
- Consumes: `SemanticExecutionResult` · `VisualFrame` (`step_index`, `narration`, `objects`, `highlighted_object_ids`)
- Produces:
  - `pace(frames: list[VisualFrame], budget: int = 60) -> PacingResult`
  - `PacingResult(view_steps: list[ViewStep], grouping_level: Literal["step","iteration"], overflow: bool)`
  - `ViewStep(view_index: int, frame_lo: int, frame_hi: int, narration: str)`
  - `VisualBindingUnresolved(Exception)`
  - `VisualTraceAdapter.HANDLED_PRIMITIVES: frozenset[str]`
  - envelope `config` mới: `{"spec_version", "title", "frames": [...], "view_steps": [...], "grouping_level", "execution_truncated": bool}`

- [ ] **Step 1: Viết test phân hoạch của pacer**

```python
# backend/tests/semantic_program/test_pacer_partition.py
# -*- coding: utf-8 -*-
"""Bất biến #32 — pacer gộp, KHÔNG bỏ."""
import pytest
from app.simulation.semantic_program.pacer import pace
from app.simulation.semantic_program.visual_adapter import VisualFrame


def _frames(n: int) -> list[VisualFrame]:
    return [
        VisualFrame(step_index=i, narration=f"buoc {i}", tier1_fact=f"buoc {i}", objects=[])
        for i in range(n)
    ]


def test_phan_hoach_day_du_khong_chong_lan():
    res = pace(_frames(50), budget=10)
    steps = res.view_steps
    assert steps[0].frame_lo == 0
    assert steps[-1].frame_hi == 49
    for a, b in zip(steps, steps[1:]):
        assert b.frame_lo == a.frame_hi + 1, "Có khung bị bỏ hoặc chồng lấn"


def test_khong_sinh_khung_moi():
    res = pace(_frames(50), budget=10)
    total = sum(s.frame_hi - s.frame_lo + 1 for s in res.view_steps)
    assert total == 50


def test_vua_ngan_sach_thi_khong_gop():
    res = pace(_frames(8), budget=10)
    assert res.grouping_level == "step"
    assert len(res.view_steps) == 8


def test_qua_ngan_sach_thi_gop_va_khai_bao():
    res = pace(_frames(500), budget=10)
    assert res.grouping_level == "iteration"
    assert len(res.view_steps) <= 10
    assert res.overflow is False


def test_khong_bao_gio_cat_bo_khung():
    """Trần trình bày KHÔNG phải lỗi và KHÔNG được cắt (spec §4.3)."""
    res = pace(_frames(5000), budget=10)
    total = sum(s.frame_hi - s.frame_lo + 1 for s in res.view_steps)
    assert total == 5000, "Pacer đã CẮT khung — vi phạm luật cấm cắt câm"
```

- [ ] **Step 2: Chạy test — xác nhận ĐỎ**

Run: `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/semantic_program/test_pacer_partition.py -v`
Expected: FAIL — `ModuleNotFoundError: app.simulation.semantic_program.pacer`

- [ ] **Step 3: Viết `pacer.py`**

```python
# -*- coding: utf-8 -*-
"""PresentationPacer — gộp khung máy thành bước xem.

Gộp nằm NGOÀI VisualTraceAdapter: adapter phải giữ song ánh
frame k ⇔ trace[k] thì bất biến #31 mới là định lý (spec §4.4).

Presentation budget TÁCH HẲN execution budget: chạm trần trình bày KHÔNG
phải lỗi — hạ mức chi tiết, không bao giờ cắt khung (spec §4.3).
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
    view_steps: list[ViewStep]
    grouping_level: Literal["step", "iteration"]
    overflow: bool = Field(
        False, description="True khi mức thô nhất vẫn vượt ngân sách — phải BÁO"
    )


def pace(
    frames: list[VisualFrame], budget: int = DEFAULT_PRESENTATION_BUDGET
) -> PacingResult:
    if not frames:
        return PacingResult(view_steps=[], grouping_level="step", overflow=False)

    if len(frames) <= budget:
        return PacingResult(
            view_steps=[
                ViewStep(view_index=i, frame_lo=i, frame_hi=i, narration=f.narration)
                for i, f in enumerate(frames)
            ],
            grouping_level="step",
            overflow=False,
        )

    # Gộp đều: mỗi bước xem ôm `size` khung máy liên tiếp. Phân hoạch đầy đủ.
    size = -(-len(frames) // budget)  # ceil
    steps: list[ViewStep] = []
    lo = 0
    while lo < len(frames):
        hi = min(lo + size - 1, len(frames) - 1)
        steps.append(
            ViewStep(
                view_index=len(steps),
                frame_lo=lo,
                frame_hi=hi,
                narration=frames[hi].narration,
            )
        )
        lo = hi + 1

    return PacingResult(
        view_steps=steps,
        grouping_level="iteration",
        overflow=len(steps) > budget,
    )
```

- [ ] **Step 4: Chạy test pacer — XANH**

Run: `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/semantic_program/test_pacer_partition.py -v`
Expected: PASS (5 test)

- [ ] **Step 5: Viết test phủ primitive**

```python
# backend/tests/semantic_program/test_primitive_coverage.py
# -*- coding: utf-8 -*-
"""Bất biến #33 — mọi primitive trong enum phải có nhánh adapter.

Vá riêng `bar_chart` thì primitive kế tiếp lại rơi y hệt (spec §4.6).
"""
import typing
from app.simulation.semantic_program.contract import VisualContainerBinding
from app.simulation.semantic_program.visual_adapter import VisualTraceAdapter


def test_moi_primitive_deu_co_nhanh_xu_ly():
    field = VisualContainerBinding.model_fields["primitive"]
    declared = set(typing.get_args(field.annotation))
    missing = declared - VisualTraceAdapter.HANDLED_PRIMITIVES
    assert not missing, (
        f"Primitive khai trong contract nhưng adapter không xử lý: {sorted(missing)}"
    )


def test_khong_khai_thua_trong_adapter():
    field = VisualContainerBinding.model_fields["primitive"]
    declared = set(typing.get_args(field.annotation))
    extra = VisualTraceAdapter.HANDLED_PRIMITIVES - declared
    assert not extra, f"Adapter xử lý primitive không có trong contract: {sorted(extra)}"
```

- [ ] **Step 6: Chạy — ĐỎ**

Run: `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/semantic_program/test_primitive_coverage.py -v`
Expected: FAIL — `AttributeError: HANDLED_PRIMITIVES`

- [ ] **Step 7: Sửa `visual_adapter.py`**

Thêm vào đầu class `VisualTraceAdapter`:

```python
    HANDLED_PRIMITIVES: frozenset[str] = frozenset({
        "array_strip", "queue_view", "stack_view", "table_grid",
        "tree_element", "bit_register", "bar_chart",
    })
```

Trong `_adapt_single_step`, thêm nhánh `bar_chart` ngay sau nhánh `table_grid`:

```python
            elif cb.primitive == "bar_chart":
                # Cột = phần tử số của container. Renderer chỉ ĐỌC, không tự tính
                # chiều cao từ biểu thức nào khác.
                obj_dict["items"] = [
                    v for v in (val if isinstance(val, (list, tuple)) else [])
                ]
```

- [ ] **Step 8: Chạy — XANH**

Run: `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/semantic_program/test_primitive_coverage.py -v`
Expected: PASS

- [ ] **Step 9: Viết test fail-closed cho binding**

```python
# backend/tests/semantic_program/test_binding_fail_closed.py
# -*- coding: utf-8 -*-
"""Bất biến #34 — binding bắt buộc không phân giải được thì KHÔNG phát envelope.

Luật KHÔNG phải "bỏ con trỏ rồi vẫn render phần còn lại" — đó là hạ cấp âm
thầm, đúng loại lỗi ở spec §0(b).
"""
import pytest
from app.simulation.semantic_program.contract import (
    AssignStmt, LiteralExpr, MemoryDeclaration, SemanticProgramSpec,
    VisualBindings, VisualContainerBinding, VisualPointerBinding,
)
from app.simulation.semantic_program.pipeline_adapter import (
    VisualBindingUnresolved, compile_semantic_program_to_envelope,
)


def _spec_voi_con_tro_khong_bao_gio_gan() -> SemanticProgramSpec:
    return SemanticProgramSpec(
        title="Con trỏ không bao giờ được gán",
        memory_declarations=[
            MemoryDeclaration(name="a", type="array", element_type="int",
                              initial_value=[1, 2, 3]),
            MemoryDeclaration(name="i", type="int", initial_value=None),
        ],
        statements=[AssignStmt(target_var="i", expr=LiteralExpr(value=0))],
        visual_bindings=VisualBindings(
            containers=[VisualContainerBinding(
                semantic_id="a", primitive="array_strip", label="Dãy")],
            pointers=[VisualPointerBinding(
                pointer_id="p_ghost", var_ref="khong_ton_tai",
                target_container="a", label="k")],
        ),
    )


def test_binding_khong_phan_giai_duoc_thi_khong_phat_envelope():
    with pytest.raises(VisualBindingUnresolved):
        compile_semantic_program_to_envelope(_spec_voi_con_tro_khong_bao_gio_gan())
```

- [ ] **Step 10: Chạy — ĐỎ**

Run: `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/semantic_program/test_binding_fail_closed.py -v`
Expected: FAIL — `ImportError: VisualBindingUnresolved`

- [ ] **Step 11: Viết lại `pipeline_adapter.py`**

```python
# -*- coding: utf-8 -*-
"""Pipeline Adapter: SemanticProgramSpec → envelope mang FRAME TIMELINE.

KHÔNG đi qua dsl/validator.py — route này có hợp đồng riêng, tránh trần 20
bước cắt câm và bộ động từ 4 action của DSL (spec §3.1).
"""
from __future__ import annotations
from typing import Any

from .contract import SemanticProgramSpec
from .interpreter import SemanticExecutionResult, SemanticProgramInterpreter
from .pacer import DEFAULT_PRESENTATION_BUDGET, pace
from .validator import validate_semantic_program
from .visual_adapter import VisualFrame, VisualTraceAdapter

DEFAULT_EXECUTION_BUDGET = 300


class VisualBindingUnresolved(Exception):
    """Binding bắt buộc không phân giải được → fail-closed (spec §4.5)."""


def _assert_bindings_resolvable(
    spec: SemanticProgramSpec, frames: list[VisualFrame]
) -> None:
    """Mỗi binding bắt buộc phải phân giải được ÍT NHẤT MỘT LẦN trong trace.

    Không đòi phân giải ở MỌI khung: một con trỏ chưa được gán ở bước 0 là
    bình thường. Nhưng một binding không bao giờ phân giải được là hỏng hợp
    đồng — và render một phần chính là lỗi §0(b).
    """
    seen: set[str] = set()
    for f in frames:
        for obj in f.objects:
            oid = obj.get("id")
            if isinstance(oid, str):
                seen.add(oid)

    required: list[tuple[str, str]] = []
    required += [(cb.semantic_id, "container") for cb in spec.visual_bindings.containers]
    required += [(pb.pointer_id, "pointer") for pb in spec.visual_bindings.pointers]
    required += [(vb.box_id, "value_box") for vb in spec.visual_bindings.value_boxes]

    missing = [f"{kind}:{bid}" for bid, kind in required if bid not in seen]
    if missing:
        raise VisualBindingUnresolved(
            "Binding bắt buộc không phân giải được ở bất kỳ khung nào: "
            + ", ".join(sorted(missing))
        )


def compile_semantic_program_to_envelope(
    spec: SemanticProgramSpec,
    execution_budget: int = DEFAULT_EXECUTION_BUDGET,
    presentation_budget: int = DEFAULT_PRESENTATION_BUDGET,
) -> dict[str, Any]:
    val_res = validate_semantic_program(spec)
    if not val_res.ok:
        raise ValueError(f"Thẩm định tĩnh SemanticProgramSpec thất bại: {val_res.error}")

    interpreter = SemanticProgramInterpreter(max_steps=execution_budget)
    exec_res: SemanticExecutionResult = interpreter.execute(spec)

    frames: list[VisualFrame] = VisualTraceAdapter(spec).adapt(exec_res)
    _assert_bindings_resolvable(spec, frames)

    pacing = pace(frames, budget=presentation_budget)

    config = {
        "spec_version": "1.0",
        "title": spec.title,
        # TOÀN BỘ chuỗi khung — snapshot đầy đủ mỗi khung, không delta (§4.1).
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
        "presentation_overflow": pacing.overflow,
        # Cấm cắt câm: nếu chạm trần execution thì BÁO, không lặng lẽ giao một phần.
        "execution_truncated": len(frames) >= execution_budget,
    }

    return {
        "status": "ok",
        "simulation_id": "generic.semantic_program",
        "domain": "generic",
        "visual_mode": "2d",
        "title": spec.title,
        "description": spec.description or spec.title,
        "config": config,
        "notes": None,
    }
```

- [ ] **Step 12: Export symbol mới**

Trong `backend/app/simulation/semantic_program/__init__.py`, thêm vào import và `__all__`:

```python
from .pacer import PacingResult, ViewStep, pace
from .pipeline_adapter import VisualBindingUnresolved, compile_semantic_program_to_envelope
```

```python
    "pace", "PacingResult", "ViewStep", "VisualBindingUnresolved",
```

- [ ] **Step 13: Chạy toàn bộ test semantic_program**

Run: `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/semantic_program/ -v`
Expected: PASS — gồm cả `test_frame_state_invariant.py` (Task 2) nay XANH.

> `test_generation_equivalence.py` sẽ ĐỎ vì nó assert hình dạng envelope cũ (`config["objects"]`, `config["processes"]`). Cập nhật nó sang hợp đồng mới — đây là thay đổi hợp đồng có chủ đích, không phải hồi quy.

- [ ] **Step 14: Đo kích thước payload thật (spec §4.1)**

```bash
cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "import json; from app.simulation.semantic_program.pipeline_adapter import compile_semantic_program_to_envelope; from tests.semantic_program.fixtures_coverage_18 import P01_STACK_BRACKET as S; e=compile_semantic_program_to_envelope(S); b=len(json.dumps(e,ensure_ascii=False).encode('utf-8')); print(f'frames={len(e[\"config\"][\"frames\"])} bytes={b}')"
```

Ghi số vào `docs/evaluation/semantic-benchmark/payload_size.md`. **Không** quyết delta trước khi có số.

- [ ] **Step 15: Chạy full backend suite**

Run: `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest -q`
Expected: PASS

- [ ] **Step 16: Commit**

```bash
git add backend/app/simulation/semantic_program backend/tests/semantic_program docs/evaluation/semantic-benchmark/payload_size.md
git commit -m "fix(semantic-program): phat frame timeline day du thay vi giu moi khung dau

Sua E1/E2: envelope nay mang toan bo chuoi khung + view_steps tu
PresentationPacer. Tach execution budget khoi presentation budget, cam cat cam.
Them nhanh bar_chart + cong doi sanh enum-adapter. Binding khong phan giai
duoc thi fail-closed thay vi render mot phan."
```

---

## Task 4: `stage_semantic_program` — lõi của Mission

**Files:**
- Modify: `backend/app/ai/pipeline.py` (thêm `stage_semantic_program`)
- Modify: `backend/app/ai/skills/semantic_program.md` (rút gọn — luật cấu trúc đã ở schema)
- Test: `backend/tests/semantic_program/test_stage_synthesis.py`

**Interfaces:**
- Consumes: `call_gemini(prompt, api_key, response_schema=...)` từ `app/ai/gemini.py` · `generate_json_schema()` từ `semantic_program/contract.py`
- Produces: `async def stage_semantic_program(text: str, analysis: dict, api_key: str) -> tuple[SemanticProgramSpec | None, str | None]` — trả `(spec, None)` khi ok, `(None, error)` khi hỏng

- [ ] **Step 1: Viết test (mock ở biên mạng, 0 API call)**

```python
# backend/tests/semantic_program/test_stage_synthesis.py
# -*- coding: utf-8 -*-
import json
import pytest
from app.ai.pipeline import stage_semantic_program


@pytest.mark.asyncio
async def test_tra_ve_spec_khi_llm_tra_json_hop_le(monkeypatch):
    payload = {
        "spec_version": "1.0",
        "title": "Tìm lớn nhất",
        "memory_declarations": [
            {"name": "a", "type": "array", "element_type": "int",
             "initial_value": [3, 9, 2]},
            {"name": "m", "type": "int", "initial_value": 0},
        ],
        "statements": [
            {"kind": "assign", "target_var": "m",
             "expr": {"kind": "index", "container": "a",
                      "index": {"kind": "literal", "value": 0}}}
        ],
        "visual_bindings": {
            "containers": [{"semantic_id": "a", "primitive": "array_strip",
                            "label": "Dãy"}],
            "pointers": [], "value_boxes": [],
        },
    }

    async def fake_call(*args, **kwargs):
        return json.dumps(payload, ensure_ascii=False)

    monkeypatch.setattr("app.ai.pipeline.call_gemini", fake_call)
    spec, err = await stage_semantic_program("Tìm max của 3, 9, 2", {}, "k")
    assert err is None
    assert spec.title == "Tìm lớn nhất"


@pytest.mark.asyncio
async def test_bao_loi_khi_json_khong_parse_duoc(monkeypatch):
    """L1 constrained decoding KHÔNG phải đảm bảo tuyệt đối (spec §7)."""
    async def fake_call(*args, **kwargs):
        return "{\"title\": \"hong"  # cụt giữa chừng

    monkeypatch.setattr("app.ai.pipeline.call_gemini", fake_call)
    spec, err = await stage_semantic_program("bất kỳ", {}, "k")
    assert spec is None
    assert "SEMANTIC_PROGRAM_INVALID" in err
```

- [ ] **Step 2: Chạy — ĐỎ**

Run: `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/semantic_program/test_stage_synthesis.py -v`
Expected: FAIL — `ImportError: cannot import name 'stage_semantic_program'`

- [ ] **Step 3: Thêm stage vào `pipeline.py`**

```python
async def stage_semantic_program(
    text: str, analysis: dict, api_key: str
) -> tuple["SemanticProgramSpec | None", str | None]:
    """LLM tổng hợp SemanticProgramSpec — ĐÚNG MỘT LƯỢT.

    Cấu trúc và enum do responseSchema cưỡng chế (constrained decoding), nên
    prompt chỉ còn phần KHÔNG mã hoá được. R0: LLM viết chương trình, KHÔNG
    quyết kết quả — interpreter mới là authority.
    """
    from app.simulation.semantic_program.contract import (
        SemanticProgramSpec, generate_json_schema,
    )
    from app.simulation.semantic_program.validator import validate_semantic_program

    prompt = f"{load_skill('semantic_program')}\n\nĐỀ BÀI:\n{text}"
    raw = await call_gemini(prompt, api_key, response_schema=generate_json_schema())

    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as e:
        return None, f"SEMANTIC_PROGRAM_INVALID: JSON không parse được ({e})"

    val = validate_semantic_program(payload)
    if not val.ok:
        return None, f"SEMANTIC_PROGRAM_INVALID: {val.error}"
    return val.spec, None
```

- [ ] **Step 4: Rút gọn `skills/semantic_program.md`**

Xoá mọi dòng mô tả **cấu trúc JSON và danh sách enum** — schema đã cưỡng chế (spec §6.3.1). Giữ lại phần không mã hoá được: vai trò, nguyên tắc chọn cấu trúc dữ liệu theo bản chất thuật toán, yêu cầu tiếng Việt cho `pedagogical_intent`.

⚠️ Sửa file này ⇒ **bump `CACHE_VERSION`** ở ba chỗ cùng một commit (`app/main.py` · assert ở `tests/test_api.py` · bảng ở `docs/CURRENT_STATE.md`), kèm comment *vì sao* bump.

- [ ] **Step 5: Chạy test + full suite**

Run: `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/ai/pipeline.py backend/app/ai/skills/semantic_program.md backend/app/main.py backend/tests docs/CURRENT_STATE.md
git commit -m "feat(semantic-program): them stage_semantic_program (1 luot, constrained decoding)"
```

---

## Task 5: Telemetry token

**Files:**
- Create: `backend/app/ai/telemetry.py`
- Modify: `backend/app/ai/gemini.py` (trả `usage_metadata` kèm text)
- Test: `backend/tests/test_token_telemetry.py`

**Interfaces:**
- Produces: `record_usage(stage: str, usage: dict) -> None` · `usage_report() -> dict[str, dict]` với khoá `prompt_tokens`, `candidates_tokens`, `cached_content_tokens`, `total_tokens`, `thoughts_tokens`, `calls`

- [ ] **Step 1: Viết test**

```python
# backend/tests/test_token_telemetry.py
# -*- coding: utf-8 -*-
from app.ai.telemetry import record_usage, reset_usage, usage_report


def test_ghi_du_nam_truong_theo_stage():
    reset_usage()
    record_usage("analyze", {
        "promptTokenCount": 1200, "candidatesTokenCount": 300,
        "cachedContentTokenCount": 800, "totalTokenCount": 1500,
        "thoughtsTokenCount": 40,
    })
    rep = usage_report()["analyze"]
    assert rep["prompt_tokens"] == 1200
    assert rep["candidates_tokens"] == 300
    assert rep["cached_content_tokens"] == 800
    assert rep["total_tokens"] == 1500
    assert rep["thoughts_tokens"] == 40
    assert rep["calls"] == 1


def test_thieu_thoughts_thi_ve_0_khong_no():
    reset_usage()
    record_usage("classify", {"promptTokenCount": 10, "totalTokenCount": 12})
    assert usage_report()["classify"]["thoughts_tokens"] == 0


def test_cong_don_nhieu_luot_cung_stage():
    reset_usage()
    record_usage("simulate", {"totalTokenCount": 100})
    record_usage("simulate", {"totalTokenCount": 250})
    assert usage_report()["simulate"]["total_tokens"] == 350
    assert usage_report()["simulate"]["calls"] == 2
```

- [ ] **Step 2: Chạy — ĐỎ**

Run: `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/test_token_telemetry.py -v`
Expected: FAIL — `ModuleNotFoundError: app.ai.telemetry`

- [ ] **Step 3: Viết `telemetry.py`**

```python
# -*- coding: utf-8 -*-
"""Ghi token usage theo TỪNG STAGE.

Không có baseline thì mọi tối ưu token là cảm tính (spec §6.1).
Lấy ĐỦ: prompt / candidates / cached / total / thoughts.
"""
from __future__ import annotations
from collections import defaultdict
from typing import Any

_FIELDS = {
    "prompt_tokens": "promptTokenCount",
    "candidates_tokens": "candidatesTokenCount",
    "cached_content_tokens": "cachedContentTokenCount",
    "total_tokens": "totalTokenCount",
    "thoughts_tokens": "thoughtsTokenCount",
}

_usage: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))


def reset_usage() -> None:
    _usage.clear()


def record_usage(stage: str, usage: dict[str, Any] | None) -> None:
    if not usage:
        return
    bucket = _usage[stage]
    for local, remote in _FIELDS.items():
        bucket[local] += int(usage.get(remote) or 0)
    bucket["calls"] += 1


def usage_report() -> dict[str, dict[str, int]]:
    return {stage: dict(vals) for stage, vals in _usage.items()}
```

- [ ] **Step 4: Nối vào `gemini.py`**

Trong hàm gọi Gemini, sau khi có response JSON, gọi `record_usage(stage, data.get("usageMetadata"))`. Thêm tham số `stage: str = "unknown"` vào chữ ký `call_gemini`.

- [ ] **Step 5: Static guard token (spec §6.4 — hard-fail ở tầng tĩnh)**

```python
# backend/tests/test_prompt_size_guard.py
# -*- coding: utf-8 -*-
"""Cổng tĩnh: prompt phình là gãy build. Live regression thì CHỈ BÁO CÁO."""
from pathlib import Path
import pytest

SKILLS = Path(__file__).resolve().parents[1] / "app" / "ai" / "skills"

# Ngưỡng chốt 2026-08-20. Hạ được thì hạ; TĂNG phải kèm lý do trong commit.
BUDGET_BYTES = {
    "analyze.md": 7000,
    "classify.md": 4600,
    "simulate.md": 1600,
    "semantic_program.md": 2100,
}


@pytest.mark.parametrize("name,budget", sorted(BUDGET_BYTES.items()))
def test_prompt_khong_vuot_ngan_sach_byte(name, budget):
    actual = (SKILLS / name).stat().st_size
    assert actual <= budget, (
        f"{name} = {actual} byte, vượt ngân sách {budget}. "
        "Luật nào mã hoá được thì chuyển sang schema/validator, đừng nhồi prompt."
    )
```

- [ ] **Step 6: Chạy full suite**

Run: `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest -q`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/ai/telemetry.py backend/app/ai/gemini.py backend/tests/test_token_telemetry.py backend/tests/test_prompt_size_guard.py
git commit -m "feat(telemetry): ghi token theo stage + cong tinh chan prompt phinh"
```

---

## Task 6: `RequestContract` + obligation taxonomy + C₁a

**Files:**
- Create: `backend/app/simulation/semantic_program/obligations.py`
- Create: `backend/app/simulation/semantic_program/request_contract.py`
- Create: `backend/app/simulation/semantic_program/coverage_gate.py`
- Test: `backend/tests/semantic_program/test_coverage_gate_c1a.py`

**Interfaces:**
- Produces:
  - `Obligation(kind: str, container: str, params: dict)` · `OBLIGATION_KINDS: frozenset[str]`
  - `RequestContract(obligations: list[Obligation], input_facts: list[InputFact])` — **immutable** (`model_config = ConfigDict(frozen=True)`)
  - `check_structural_coverage(contract, spec) -> CoverageResult(ok: bool, error_code: str | None, missing: list[str])`

- [ ] **Step 1: Viết test C₁a**

```python
# backend/tests/semantic_program/test_coverage_gate_c1a.py
# -*- coding: utf-8 -*-
"""C₁a — structural coverage, TRƯỚC execution (spec §5.3)."""
from app.simulation.semantic_program.coverage_gate import check_structural_coverage
from app.simulation.semantic_program.obligations import Obligation
from app.simulation.semantic_program.request_contract import RequestContract
from tests.semantic_program.fixtures_coverage_18 import P02_FIND_MAX


def test_du_nghia_vu_thi_pass():
    contract = RequestContract(
        obligations=[Obligation(kind="extremum", container="a",
                                params={"cmp": "max", "witness": "max_val"})],
        input_facts=[],
    )
    res = check_structural_coverage(contract, P02_FIND_MAX)
    assert res.ok, res.missing


def test_de_hoi_hai_viec_ma_chuong_trinh_lam_mot_thi_tu_choi():
    contract = RequestContract(
        obligations=[
            Obligation(kind="extremum", container="a",
                       params={"cmp": "max", "witness": "max_val"}),
            Obligation(kind="extremum", container="a",
                       params={"cmp": "min", "witness": "min_val"}),
        ],
        input_facts=[],
    )
    res = check_structural_coverage(contract, P02_FIND_MAX)
    assert not res.ok
    assert res.error_code == "REQUESTED_OPERATION_UNCOVERED"
    assert any("min_val" in m for m in res.missing)


def test_witness_dangling_thi_tu_choi():
    contract = RequestContract(
        obligations=[Obligation(kind="extremum", container="a",
                                params={"cmp": "max", "witness": "khong_khai_bao"})],
        input_facts=[],
    )
    res = check_structural_coverage(contract, P02_FIND_MAX)
    assert not res.ok
    assert res.error_code == "REQUESTED_OPERATION_UNCOVERED"


def test_contract_la_bat_bien_khong_sua_duoc():
    """Nghĩa vụ đóng băng — stage sinh KHÔNG có quyền khai lại (spec §5.2)."""
    import pydantic, pytest
    c = RequestContract(obligations=[], input_facts=[])
    with pytest.raises(pydantic.ValidationError):
        c.obligations = []
```

- [ ] **Step 2: Chạy — ĐỎ.** Expected: `ModuleNotFoundError: ...obligations`

- [ ] **Step 3: Viết `obligations.py`**

```python
# -*- coding: utf-8 -*-
"""Obligation taxonomy — khoá vào HỆ KIỂU của IR, không khoá vào catalog.

Ba nguồn (spec §5.1): IR type semantics + expression/statement semantics +
reusable server-owned checker. Điều kiện thứ ba là điều kiện CHẶN: không có
checker server-owned thì KHÔNG được vào bảng.

ĐÓNG BĂNG TRƯỚC SEALED. Sau khi seal: không thêm checker để cứu từng case.
"""
from __future__ import annotations
from typing import Any
from pydantic import BaseModel, ConfigDict

# kind -> kiểu container hợp lệ
OBLIGATION_KINDS: dict[str, frozenset[str]] = {
    "extremum": frozenset({"array", "matrix"}),
    "count_matching": frozenset({"array", "set", "map"}),
    "ordering": frozenset({"array"}),
    "membership": frozenset({"set", "map", "array"}),
    "total_mapping": frozenset({"map"}),
    "reachability": frozenset({"graph"}),
    "structural_traversal": frozenset({"tree_node"}),
}


class Obligation(BaseModel):
    model_config = ConfigDict(frozen=True)
    kind: str
    container: str
    params: dict[str, Any] = {}

    @property
    def witness(self) -> str | None:
        w = self.params.get("witness")
        return w if isinstance(w, str) else None
```

- [ ] **Step 4: Viết `request_contract.py`**

```python
# -*- coding: utf-8 -*-
"""RequestContract — server ĐÓNG BĂNG nghĩa vụ do analyze khai.

Đây là separation of responsibility, KHÔNG phải independent oracle: nó chặn
chương trình tự sửa đề cho vừa mình, nhưng KHÔNG chặn cùng một model hiểu sai
đề nhất quán ở cả hai lượt (spec §5.2).
"""
from __future__ import annotations
from pydantic import BaseModel, ConfigDict

from .obligations import Obligation


class InputFact(BaseModel):
    model_config = ConfigDict(frozen=True)
    fact_id: str
    label: str
    values: list = []


class RequestContract(BaseModel):
    model_config = ConfigDict(frozen=True)
    obligations: list[Obligation] = []
    input_facts: list[InputFact] = []
```

- [ ] **Step 5: Viết `coverage_gate.py` (phần C₁a)**

```python
# -*- coding: utf-8 -*-
"""SemanticCoverageGate — thay completeness_gate THEO-TARGET bằng bản không
phụ thuộc catalog.

C₁a: nghĩa vụ có witness hợp lệ VỀ CẤU TRÚC không? (trước execution)
C₁b: witness đó có THẬT SỰ được hiện thực hoá không? (sau execution, Task 9)
"""
from __future__ import annotations
from pydantic import BaseModel

from .contract import SemanticProgramSpec
from .obligations import OBLIGATION_KINDS
from .request_contract import RequestContract


class CoverageResult(BaseModel):
    ok: bool
    error_code: str | None = None
    missing: list[str] = []


def _assigned_targets(statements) -> set[str]:
    """Mọi biến có ÍT NHẤT MỘT producer trong chương trình (chưa xét có chạy)."""
    found: set[str] = set()
    for st in statements:
        kind = getattr(st, "kind", None)
        if kind == "assign":
            found.add(st.target_var)
        elif kind in ("pop", "dequeue") and getattr(st, "dest_var", None):
            found.add(st.dest_var)
        for attr in ("body", "then_body", "else_body"):
            sub = getattr(st, attr, None)
            if sub:
                found |= _assigned_targets(sub)
    return found


def check_structural_coverage(
    contract: RequestContract, spec: SemanticProgramSpec
) -> CoverageResult:
    declared = {d.name: d.type for d in spec.memory_declarations}
    producers = _assigned_targets(spec.statements)
    missing: list[str] = []

    for ob in contract.obligations:
        allowed = OBLIGATION_KINDS.get(ob.kind)
        if allowed is None:
            missing.append(f"{ob.kind}: nghĩa vụ không có checker server-owned")
            continue
        if declared.get(ob.container) not in allowed:
            missing.append(
                f"{ob.kind}({ob.container}): kiểu '{declared.get(ob.container)}' "
                f"không hợp với nghĩa vụ này"
            )
            continue
        w = ob.witness
        if not w:
            missing.append(f"{ob.kind}({ob.container}): thiếu witness")
        elif w not in declared:
            missing.append(f"{ob.kind}({ob.container}): witness '{w}' chưa khai báo")
        elif w not in producers:
            missing.append(f"{ob.kind}({ob.container}): witness '{w}' không có producer")

    if missing:
        return CoverageResult(
            ok=False, error_code="REQUESTED_OPERATION_UNCOVERED", missing=missing
        )
    return CoverageResult(ok=True)
```

- [ ] **Step 6: Chạy — XANH.** Run: `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/semantic_program/test_coverage_gate_c1a.py -v`

- [ ] **Step 7: Commit**

```bash
git add backend/app/simulation/semantic_program backend/tests/semantic_program/test_coverage_gate_c1a.py
git commit -m "feat(semantic-program): RequestContract + obligation taxonomy + C1a coverage gate"
```

---

## Task 7: Tách `analyze` khỏi enum catalog + `semantic_input_grounding_gate` (P2)

**Files:**
- Modify: `backend/app/ai/pipeline.py:149,164` (schema của `analyze`)
- Create: `backend/app/simulation/semantic_program/grounding_gate.py`
- Create: `docs/evaluation/semantic-benchmark/P1_LIMITATION.md`
- Test: `backend/tests/semantic_program/test_grounding_gate.py`

**Interfaces:**
- Produces: `check_grounding(contract: RequestContract, spec: SemanticProgramSpec) -> GroundingResult(ok, error_code, unresolved: list[str])`

- [ ] **Step 1: Viết test**

```python
# backend/tests/semantic_program/test_grounding_gate.py
# -*- coding: utf-8 -*-
"""P2 (IR → RequestContract) — kiểm tất định, mạnh (spec §3.4)."""
from app.simulation.semantic_program.grounding_gate import check_grounding
from app.simulation.semantic_program.request_contract import InputFact, RequestContract
from app.simulation.semantic_program.contract import MemoryDeclaration, SemanticProgramSpec, AssignStmt, LiteralExpr


def _spec(values):
    return SemanticProgramSpec(
        title="Tìm max",
        memory_declarations=[
            MemoryDeclaration(name="a", type="array", element_type="int",
                              initial_value=values, source_fact_id="f1"),
            MemoryDeclaration(name="m", type="int", initial_value=0),
        ],
        statements=[AssignStmt(target_var="m", expr=LiteralExpr(value=0))],
    )


_CONTRACT = RequestContract(
    input_facts=[InputFact(fact_id="f1", label="dãy đề cho", values=[4, 7, 2])]
)


def test_khop_dung_muc_du_lieu_thi_pass():
    assert check_grounding(_CONTRACT, _spec([4, 7, 2])).ok


def test_them_gia_tri_khong_co_nguon_thi_fail():
    """Đề cho 4,7,2 mà IR khai [4,7,2,9] → 9 không truy được nguồn."""
    res = check_grounding(_CONTRACT, _spec([4, 7, 2, 9]))
    assert not res.ok
    assert res.error_code == "INPUT_NOT_GROUNDED"


def test_tham_chieu_fact_khong_ton_tai_thi_fail():
    spec = _spec([4, 7, 2])
    spec.memory_declarations[0].source_fact_id = "f_ma"
    res = check_grounding(_CONTRACT, spec)
    assert not res.ok
```

- [ ] **Step 2: Chạy — ĐỎ.** Expected: `ModuleNotFoundError` + `source_fact_id` chưa có trong `MemoryDeclaration`

- [ ] **Step 3: Thêm `source_fact_id` vào `MemoryDeclaration`** (`contract.py`)

```python
    source_fact_id: Optional[str] = Field(
        None,
        description="ID mục dữ liệu trong RequestContract mà initial_value lấy từ đó. "
                    "BẮT BUỘC khi initial_value mang nghĩa input đề cho.",
    )
```

⚠️ Đổi contract ⇒ chạy `backend/scripts/export_semantic_program_schema.py` (ghi **hai** bản: `docs/schemas/` + `frontend/src/simulations/domains/generic/`), nếu không `test_schema_sync.py` ĐỎ.

- [ ] **Step 4: Viết `grounding_gate.py`**

```python
# -*- coding: utf-8 -*-
"""semantic_input_grounding_gate — thay check_input_sufficiency (target-bound).

Chuỗi provenance HAI ĐOẠN (spec §3.4):
    Original input --P1--> RequestContract fact --P2--> IR reference

P2 kiểm được tất định và mạnh. P1 chỉ mạnh nếu có source_span/extractor
evidence — xem docs/evaluation/semantic-benchmark/P1_LIMITATION.md.
"""
from __future__ import annotations
from pydantic import BaseModel

from .contract import SemanticProgramSpec
from .request_contract import RequestContract

_INPUT_TYPES = {"array", "matrix", "map", "set", "stack", "queue", "graph"}


class GroundingResult(BaseModel):
    ok: bool
    error_code: str | None = None
    unresolved: list[str] = []


def check_grounding(
    contract: RequestContract, spec: SemanticProgramSpec
) -> GroundingResult:
    facts = {f.fact_id: f for f in contract.input_facts}
    unresolved: list[str] = []

    for decl in spec.memory_declarations:
        if decl.initial_value in (None, [], {}, ""):
            continue
        if decl.type not in _INPUT_TYPES:
            continue

        fid = decl.source_fact_id
        if not fid:
            unresolved.append(f"{decl.name}: thiếu source_fact_id")
            continue
        fact = facts.get(fid)
        if fact is None:
            unresolved.append(f"{decl.name}: source_fact_id '{fid}' không tồn tại")
            continue

        allowed = list(fact.values)
        for v in (decl.initial_value if isinstance(decl.initial_value, list) else []):
            if v not in allowed:
                unresolved.append(f"{decl.name}: giá trị {v!r} không có trong '{fid}'")

    if unresolved:
        return GroundingResult(
            ok=False, error_code="INPUT_NOT_GROUNDED", unresolved=unresolved
        )
    return GroundingResult(ok=True)
```

- [ ] **Step 5: Khai giới hạn P1 — viết `P1_LIMITATION.md`**

```markdown
# Giới hạn P1 — khai tường minh, không lấp liếm

`semantic_input_grounding_gate` đóng HOÀN TOÀN đoạn P2 (IR → RequestContract).
Nó **thu hẹp, chứ KHÔNG đóng** đoạn P1 (RequestContract → đề gốc).

Kịch bản còn hở khi chưa làm full source-span:
    analyze bịa [4,7,2,9] → RequestContract chứa 9 → IR tham chiếu đúng mục
    chứa 9 → **P2 vẫn PASS**.

Do đó KHÔNG được tuyên bố gate này đã diệt mọi hallucination của `analyze`.
Nó là điều kiện CẦN, CHƯA ĐỦ.
```

- [ ] **Step 6: Bỏ enum catalog khỏi schema `analyze` trên route semantic**

Tại `pipeline.py:149` và `:164`, `requested_operations`/`requested_mechanisms` đang dùng `"enum": list(analyze_exposed_operations())` — **khoá catalog nằm ngay trong response schema** (E5). Tách: giữ nguyên schema cũ cho đường module; route semantic dùng schema khai `obligations` theo `OBLIGATION_KINDS` (§3.5 — Catalog operation taxonomy tách khỏi Semantic obligation taxonomy).

- [ ] **Step 7: Chạy full suite + regen schema**

```bash
cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/export_semantic_program_schema.py
cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest -q
```
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add backend/app docs/schemas frontend/src/simulations/domains/generic/semantic_program.schema.json docs/evaluation/semantic-benchmark/P1_LIMITATION.md backend/tests
git commit -m "feat(semantic-program): grounding gate P2 + tach analyze khoi enum catalog"
```

---

## Task 8: Route + `execution_authority_gate` + `verification_gap` + module frontend

**Files:**
- Create: `backend/app/simulation/execution_authority_gate.py`
- Modify: `backend/app/simulation/error_codes.py`
- Modify: `backend/app/ai/pipeline.py` (nhánh route mới, **sau feature flag**)
- Create: `frontend/src/simulations/domains/semantic/index.ts`
- Create: `frontend/src/simulations/domains/semantic/model.ts`
- Create: `frontend/src/simulations/domains/semantic/ui.tsx`
- Modify: `frontend/src/simulations/index.ts` (một dòng `registerSemanticDomain()`)
- Test: `backend/tests/test_execution_authority_gate.py`
- Test: `frontend/src/simulations/domains/semantic/semantic.test.ts`

**Interfaces:**
- Produces: `check_execution_authority(analysis, plan, has_interpreter: bool) -> str | None` · `ErrorCode.SEMANTIC_VERIFICATION_UNAVAILABLE` · `registerSemanticDomain(): void`

> **SERVING GATE:** bước này chỉ đăng ký route ở chế độ **nội bộ/shadow sau feature flag** `SEMANTIC_ROUTE_SERVING=0`. Learner-facing chỉ bật sau Task 10.

- [ ] **Step 1: Viết test authority gate**

```python
# backend/tests/test_execution_authority_gate.py
# -*- coding: utf-8 -*-
"""execution_authority_gate — làm sắc R0, KHÔNG nới (spec §3.3)."""
from app.simulation.execution_authority_gate import check_execution_authority


def test_provided_thi_qua():
    assert check_execution_authority(
        {"result_ownership": "provided"}, {}, has_interpreter=False) is None


def test_rule_derivable_thi_qua():
    assert check_execution_authority(
        {"result_ownership": "rule_derivable"}, {}, has_interpreter=False) is None


def test_algorithmic_khong_co_interpreter_thi_gap():
    reason = check_execution_authority(
        {"result_ownership": "algorithmic"}, {}, has_interpreter=False)
    assert reason is not None


def test_algorithmic_CO_interpreter_thi_qua():
    """Thay đổi duy nhất so với computation_gate cũ."""
    assert check_execution_authority(
        {"result_ownership": "algorithmic"}, {}, has_interpreter=True) is None


def test_thieu_ownership_thi_fail_closed():
    assert check_execution_authority({}, {}, has_interpreter=True) is not None
```

- [ ] **Step 2: Chạy — ĐỎ.** Expected: `ModuleNotFoundError`

- [ ] **Step 3: Viết `execution_authority_gate.py`**

```python
# -*- coding: utf-8 -*-
"""Kết quả phải có một AUTHORITY TẤT ĐỊNH sở hữu.

Luật cũ đọc là "algorithmic thì từ chối"; luật THẬT đằng sau nó luôn là câu
trên. Khi chưa có interpreter, hai câu trùng nhau nên viết tắt được.

R0 nguyên vẹn: LLM vẫn KHÔNG BAO GIỜ là authority.
"""
from __future__ import annotations
from app.simulation.dsl.manifest import known_gap_roles


def check_execution_authority(
    analysis: dict, plan: dict, has_interpreter: bool
) -> str | None:
    gaps = sorted(set(plan.get("unsupported_capabilities", [])) & known_gap_roles())
    if gaps:
        return (
            f"Bài cần cơ chế chưa có engine tất định sở hữu ({', '.join(gaps)}) — "
            "hệ từ chối trung thực thay vì dựng cảnh xấp xỉ."
        )

    ownership = analysis.get("result_ownership")
    if ownership in ("provided", "rule_derivable"):
        return None
    if ownership == "algorithmic":
        if has_interpreter:
            return None
        return (
            "Kết quả của bài phải được TÍNH qua cơ chế thuật toán mà không authority "
            "tất định nào của hệ sở hữu — hệ từ chối trung thực."
        )
    return (
        f"Phân tích không xác định được nguồn kết quả (result_ownership = "
        f"{ownership!r}) — hệ từ chối an toàn thay vì đoán."
    )
```

- [ ] **Step 4: Thêm error code mới vào `error_codes.py`**

```python
    SEMANTIC_PROGRAM_INVALID = "semantic_program_invalid"
    INTERPRETER_BUDGET_EXHAUSTED = "interpreter_budget_exhausted"
    OBLIGATION_WITNESS_UNREALIZED = "obligation_witness_unrealized"
    SEMANTIC_VERIFICATION_UNAVAILABLE = "semantic_verification_unavailable"
    INPUT_NOT_GROUNDED = "input_not_grounded"
    POSTCONDITION_VIOLATED = "postcondition_violated"
    ORACLE_SEMANTIC_MISMATCH = "oracle_semantic_mismatch"
```

`failure_category` mới `verification_gap` — map `SEMANTIC_VERIFICATION_UNAVAILABLE → verification_gap`.

- [ ] **Step 5: Viết test frontend cho module semantic**

```typescript
// frontend/src/simulations/domains/semantic/semantic.test.ts
import { describe, expect, it } from "vitest";
import { buildSemanticState } from "./model";

const CONFIG = {
  spec_version: "1.0",
  title: "Kiểm tra ngoặc",
  frames: [
    { step_index: 0, narration: "Bắt đầu", objects: [{ id: "s", type: "stack_view", label: "Ngăn xếp", items: [] }], highlighted_object_ids: [] },
    { step_index: 1, narration: "Đẩy '['", objects: [{ id: "s", type: "stack_view", label: "Ngăn xếp", items: ["["] }], highlighted_object_ids: ["s"] },
  ],
  view_steps: [
    { view_index: 0, frame_lo: 0, frame_hi: 0, narration: "Bắt đầu" },
    { view_index: 1, frame_lo: 1, frame_hi: 1, narration: "Đẩy '['" },
  ],
  grouping_level: "step",
  presentation_overflow: false,
  execution_truncated: false,
};

describe("semantic program module", () => {
  it("timeline có đúng số bước xem", () => {
    const s = buildSemanticState(CONFIG);
    expect(s.timeline).toHaveLength(2);
  });

  it("bước xem trỏ đúng khung — KHÔNG đóng băng ở khung 0", () => {
    const s = buildSemanticState(CONFIG);
    const last = s.timeline[1];
    const stack = last.objects.find((o) => o.id === "s");
    expect(stack?.items).toEqual(["["]);
  });

  it("không có định danh kĩ thuật nào lọt lên bề mặt hiển thị", () => {
    const s = buildSemanticState(CONFIG);
    const surface = JSON.stringify(s.timeline.map((t) => t.narration));
    expect(surface).not.toContain("generic.semantic_program");
    expect(surface).not.toContain("stack_view");
  });
});
```

- [ ] **Step 6: Chạy — ĐỎ.** Run: `cd frontend && npx vitest run src/simulations/domains/semantic/`

- [ ] **Step 7: Viết `model.ts`, `ui.tsx`, `index.ts`**

`model.ts` — `buildSemanticState(config)` trả `{ timeline: Array<{ viewIndex, narration, objects }> }`; mỗi bước xem đọc **khung `frame_hi`** của đoạn. Renderer **chỉ ĐỌC**, không đánh giá lại biểu thức.

`ui.tsx` — vẽ 2D thuần SVG: `array_strip` · `stack_view` · `queue_view` · `table_grid` · `bar_chart` · `bit_register` · `tree_element` · `pointer` · `value_box`. Dùng `var(--token)` **có định nghĩa** (`styles/tokens.test.ts` khoá).

`index.ts` — `export function registerSemanticDomain(): void` gọi `registerSimulation("generic.semantic_program", {...})`.

- [ ] **Step 8: Đăng ký một dòng trong `frontend/src/simulations/index.ts`**

```typescript
import { registerSemanticDomain } from "./domains/semantic";
// ... trong registerAllSimulations():
  registerSemanticDomain(); // 2026-08-20 — đường sinh ngữ nghĩa
```

- [ ] **Step 9: Chạy vitest + build**

```bash
cd frontend && npx vitest run && npm run build
```
Expected: PASS

- [ ] **Step 10: Commit**

```bash
git add backend/app frontend/src backend/tests
git commit -m "feat(semantic-program): dang ky route (shadow-only) + execution_authority_gate + verification_gap"
```

---

## Task 9: C₁b — realized coverage

**Files:**
- Modify: `backend/app/simulation/semantic_program/coverage_gate.py`
- Test: `backend/tests/semantic_program/test_coverage_gate_c1b.py`

**Interfaces:**
- Produces: `check_realized_coverage(contract, spec, exec_result) -> CoverageResult` với `error_code = "OBLIGATION_WITNESS_UNREALIZED"`

- [ ] **Step 1: Viết test — ví dụ dead-branch của spec §5.3**

```python
# backend/tests/semantic_program/test_coverage_gate_c1b.py
# -*- coding: utf-8 -*-
"""C₁b — realized coverage, SAU execution.

C₁a một mình không phân biệt được "có viết" với "có chạy" (spec §5.3).
"""
from app.simulation.semantic_program.coverage_gate import (
    check_realized_coverage, check_structural_coverage,
)
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.obligations import Obligation
from app.simulation.semantic_program.request_contract import RequestContract
from app.simulation.semantic_program.contract import (
    AssignStmt, CompareCond, IfStmt, LiteralExpr, MemoryDeclaration,
    SemanticProgramSpec, VarRefExpr,
)

_CONTRACT = RequestContract(
    obligations=[Obligation(kind="extremum", container="a",
                            params={"cmp": "min", "witness": "min_value"})]
)


def _spec_dead_branch() -> SemanticProgramSpec:
    """`assign min_value` nằm trong nhánh không bao giờ đúng."""
    return SemanticProgramSpec(
        title="Nhánh chết",
        memory_declarations=[
            MemoryDeclaration(name="a", type="array", element_type="int",
                              initial_value=[5, 1, 9]),
            MemoryDeclaration(name="min_value", type="int", initial_value=None),
        ],
        statements=[
            IfStmt(
                condition=CompareCond(op="==", left=LiteralExpr(value=1),
                                      right=LiteralExpr(value=2)),
                then_body=[AssignStmt(target_var="min_value",
                                      expr=LiteralExpr(value=1))],
                else_body=[],
            )
        ],
    )


def test_c1a_pass_nhung_c1b_fail():
    spec = _spec_dead_branch()
    assert check_structural_coverage(_CONTRACT, spec).ok, "C₁a phải PASS ở ví dụ này"

    exec_res = SemanticProgramInterpreter(max_steps=300).execute(spec)
    res = check_realized_coverage(_CONTRACT, spec, exec_res)
    assert not res.ok
    assert res.error_code == "OBLIGATION_WITNESS_UNREALIZED"
    assert any("min_value" in m for m in res.missing)
```

- [ ] **Step 2: Chạy — ĐỎ.** Expected: `ImportError: check_realized_coverage`

- [ ] **Step 3: Thêm `check_realized_coverage` vào `coverage_gate.py`**

```python
def check_realized_coverage(
    contract: RequestContract,
    spec: SemanticProgramSpec,
    exec_result,
) -> CoverageResult:
    """C₁b — witness có THẬT SỰ được tạo/đạt tới trong lượt chạy này không?"""
    realized: set[str] = set()
    for step in exec_result.trace:
        snap = step.memory_snapshot or {}
        for name, value in snap.items():
            if value is not None:
                realized.add(name)

    missing = [
        f"{ob.kind}({ob.container}): witness '{ob.witness}' không được hiện thực hoá "
        "trong lượt chạy (nhánh chết hoặc không đạt tới)"
        for ob in contract.obligations
        if ob.witness and ob.witness not in realized
    ]

    if missing:
        return CoverageResult(
            ok=False, error_code="OBLIGATION_WITNESS_UNREALIZED", missing=missing
        )
    return CoverageResult(ok=True)
```

- [ ] **Step 4: Chạy — XANH.** Run: `... -m pytest tests/semantic_program/test_coverage_gate_c1b.py -v`

- [ ] **Step 5: Commit**

```bash
git add backend/app/simulation/semantic_program/coverage_gate.py backend/tests/semantic_program/test_coverage_gate_c1b.py
git commit -m "feat(semantic-program): C1b realized coverage (bat witness trong nhanh chet)"
```

---

## Task 10: C₂ hậu điều kiện + bật serving gate

**Files:**
- Create: `backend/app/simulation/semantic_program/postconditions.py`
- Modify: `backend/app/ai/pipeline.py` (bật `SEMANTIC_ROUTE_SERVING` khi đủ chuỗi)
- Test: `backend/tests/semantic_program/test_postconditions.py`

**Interfaces:**
- Produces: `check_postconditions(contract, spec, exec_result) -> PostconditionResult(ok, error_code, violations)`; checker server-owned cho mỗi `kind` trong `OBLIGATION_KINDS`

- [ ] **Step 1: Viết test**

```python
# backend/tests/semantic_program/test_postconditions.py
# -*- coding: utf-8 -*-
"""C₂ — hậu điều kiện SERVER-OWNED, executable (spec §5.3, §3.6).

POSTCONDITION_VIOLATED KHÔNG có nghĩa "chứng minh AI hiểu sai đề".
"""
from app.simulation.semantic_program.postconditions import check_postconditions
from app.simulation.semantic_program.obligations import Obligation
from app.simulation.semantic_program.request_contract import RequestContract
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from tests.semantic_program.fixtures_coverage_18 import P02_FIND_MAX

_OK = RequestContract(obligations=[
    Obligation(kind="extremum", container="a",
               params={"cmp": "max", "witness": "max_val"})])

_SAI = RequestContract(obligations=[
    Obligation(kind="extremum", container="a",
               params={"cmp": "min", "witness": "max_val"})])


def test_hau_dieu_kien_dung_thi_pass():
    res = SemanticProgramInterpreter(max_steps=300).execute(P02_FIND_MAX)
    assert check_postconditions(_OK, P02_FIND_MAX, res).ok


def test_witness_khong_thoa_tinh_chat_thi_violated():
    """max_val giữ giá trị LỚN nhất, nên nghĩa vụ 'min' phải vi phạm."""
    res = SemanticProgramInterpreter(max_steps=300).execute(P02_FIND_MAX)
    out = check_postconditions(_SAI, P02_FIND_MAX, res)
    assert not out.ok
    assert out.error_code == "POSTCONDITION_VIOLATED"
```

- [ ] **Step 2: Chạy — ĐỎ.** Expected: `ModuleNotFoundError`

- [ ] **Step 3: Viết `postconditions.py`**

```python
# -*- coding: utf-8 -*-
"""Checker SERVER-OWNED cho từng obligation kind.

Chỉ chạy trên nghĩa vụ ĐÃ qua C₁a và C₁b. Vi phạm → POSTCONDITION_VIOLATED,
nghĩa là "hậu điều kiện server-owned bị vi phạm" — KHÔNG phải "AI hiểu sai đề".
"""
from __future__ import annotations
from typing import Any, Callable
from pydantic import BaseModel


class PostconditionResult(BaseModel):
    ok: bool
    error_code: str | None = None
    violations: list[str] = []


def _final(exec_result) -> dict[str, Any]:
    return exec_result.trace[-1].memory_snapshot if exec_result.trace else {}


def _extremum(snap, ob) -> str | None:
    seq = snap.get(ob.container)
    w = snap.get(ob.witness)
    if not isinstance(seq, (list, tuple)) or not seq:
        return f"extremum({ob.container}): container rỗng hoặc sai kiểu"
    want = max(seq) if ob.params.get("cmp") == "max" else min(seq)
    return None if w == want else (
        f"extremum({ob.container}, {ob.params.get('cmp')}): witness "
        f"'{ob.witness}' = {w!r}, đúng phải là {want!r}"
    )


def _ordering(snap, ob) -> str | None:
    seq = snap.get(ob.container)
    if not isinstance(seq, (list, tuple)):
        return f"ordering({ob.container}): sai kiểu"
    asc = ob.params.get("cmp", "asc") == "asc"
    ok = all((seq[i] <= seq[i + 1]) if asc else (seq[i] >= seq[i + 1])
             for i in range(len(seq) - 1))
    return None if ok else f"ordering({ob.container}): dãy chưa đúng thứ tự"


def _membership(snap, ob) -> str | None:
    box = snap.get(ob.container)
    item = ob.params.get("item")
    if box is None:
        return f"membership({ob.container}): container không tồn tại"
    return None if (item in box) == bool(ob.params.get("expected", True)) else (
        f"membership({ob.container}): kết quả không như hậu điều kiện"
    )


CHECKERS: dict[str, Callable] = {
    "extremum": _extremum,
    "ordering": _ordering,
    "membership": _membership,
}


def check_postconditions(contract, spec, exec_result) -> PostconditionResult:
    snap = _final(exec_result)
    violations: list[str] = []
    for ob in contract.obligations:
        fn = CHECKERS.get(ob.kind)
        if fn is None:
            # Không có checker server-owned → MỨC YẾU, xử lý ở §5.4, không phải
            # vi phạm hậu điều kiện.
            continue
        msg = fn(snap, ob)
        if msg:
            violations.append(msg)
    if violations:
        return PostconditionResult(
            ok=False, error_code="POSTCONDITION_VIOLATED", violations=violations
        )
    return PostconditionResult(ok=True)
```

- [ ] **Step 4: Bật serving gate**

Chuỗi assurance nay đã đủ. Trong `pipeline.py`, cho phép route phục vụ learner khi **và chỉ khi** tất cả các bước đều PASS:

```python
    # Serving gate (spec §10.2): chỉ tới đây mới được phát canonical cho học sinh.
    # Nghĩa vụ không có checker server-owned → MỨC YẾU → verification_gap,
    # KHÔNG phục vụ (spec §5.4).
    weak = [ob.kind for ob in contract.obligations if ob.kind not in CHECKERS]
    if weak:
        return {
            "status": "unsupported",
            "failure_category": "verification_gap",
            "error_code": ErrorCode.SEMANTIC_VERIFICATION_UNAVAILABLE.value,
            "reason": "Hệ chạy được bài này nhưng chưa có cách kiểm chứng độc lập "
                      "kết quả, nên chưa hiển thị cho người học.",
        }
```

- [ ] **Step 5: Chạy full suite + build**

```bash
cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest -q
cd frontend && npx vitest run && npm run build
```
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app backend/tests
git commit -m "feat(semantic-program): C2 hau dieu kien server-owned + bat serving gate"
```

---

## Task 10b: ⛔ CỔNG CHẶN — trả DỨT ĐIỂM nợ W13 (chốt 2026-08-21)

**Task 11 KHÔNG được bắt đầu trước khi cổng này xanh. Không vá lẻ.**

### Hiện trạng đo được (2026-08-21, trên `main` sạch)

| | |
|---|---|
| `npx vitest run` | **111 test ĐỎ** (đo sau khi stash toàn bộ việc của wave này) |
| `npx tsc -b` | **ĐỎ** |
| Số file test dính | **26** |

**Không phải do wave sinh ngữ nghĩa.** Kiểm bằng cách stash rồi chạy lại; và
`grep semantic_program` trên đầu ra vitest = **0**.

Nguyên nhân: W13 gỡ quiz khỏi production nhưng **không dọn test**. `types.ts` có
nguyên đoạn ghi *"W13 — KHÔNG CÒN `PredictionCapability`"*, trong khi 26 file
test vẫn gọi những thứ đã bị gỡ:

```
mod.predict            AppState.challengeOpen      AppState.setChallengeOpen
AppState.prediction    challengeEntry              challengeSurfaceVisible
components/SearchActionZone   (module không còn tồn tại)
```

### Vì sao là CỔNG chặn, không phải việc dọn dẹp

- **T2/T3 không dùng được.** `npm run test:wave` = `vitest run && tsc -b &&
  vite build` — cả ba đỏ, nên không có cách nào đóng wave đúng luật dự án.
- **L5a cần nền xanh.** Visual regression trên một suite đã đỏ thì không phân
  biệt được lỗi mới với lỗi cũ.

### Luật xử lý

- **Dứt điểm, không vá lẻ** (quyết định của chủ đề tài, 2026-08-21). Vá từng
  file theo nhu cầu của Task 11 sẽ để lại phần còn lại đỏ mãi, và cổng T2/T3
  vẫn không dùng được.
- Với mỗi file: hoặc **viết lại theo kiến trúc sau W13** (nếu điều nó kiểm vẫn
  còn ý nghĩa), hoặc **xoá kèm lý do trong commit** (nếu nó kiểm một năng lực
  đã bị gỡ có chủ đích). **Không** khôi phục `predict`/`challengeOpen` cho test
  chạy được — `types.ts` đã cấm: *"ĐỪNG khôi phục cho gọn"*.
- Cổng xanh = `npx vitest run` **0 fail** và `npx tsc -b` **0 lỗi**.

## Task 11: L5a — visual regression nhỏ, đại diện

**Files:**
- Create: `frontend/scripts/capture-semantic-route.mjs`
- Create: `frontend/tests/visual/semantic-route.spec.ts`

**Interfaces:**
- Consumes: `npm run dev` chạy ở cửa sổ khác
- Produces: baseline screenshot cho 3 case đại diện × 2 bề rộng

> L3 chứng minh **semantic visual fidelity**; nó **KHÔNG** chứng minh màn hình nhìn được. L5a bắt chữ đè, clipping, con trỏ chui vào label, vỡ responsive — đúng ràng buộc "hiển thị chuẩn xác".

- [ ] **Step 1: Viết Playwright spec**

```typescript
// frontend/tests/visual/semantic-route.spec.ts
import { expect, test } from "@playwright/test";

const CASES = ["stack_bracket", "find_max", "bfs_queue"];
const WIDTHS = [1366, 1920]; // school laptop + desktop

for (const c of CASES) {
  for (const w of WIDTHS) {
    test(`${c} @${w} không vỡ bố cục`, async ({ page }) => {
      await page.setViewportSize({ width: w, height: 900 });
      await page.goto(`http://localhost:3000/?fixture=${c}`);
      // Dấu vân tay trang: khẳng định đúng route, sai thì đỏ (ARCHITECTURE_MAP §8 #14)
      await expect(page.locator("[data-route='semantic']")).toBeVisible();
      await expect(page).toHaveScreenshot(`${c}-${w}.png`, { maxDiffPixelRatio: 0.01 });
    });
  }
}

test("không có tràn ngang", async ({ page }) => {
  await page.setViewportSize({ width: 1366, height: 900 });
  await page.goto("http://localhost:3000/?fixture=stack_bracket");
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth > document.documentElement.clientWidth
  );
  expect(overflow).toBe(false);
});
```

- [ ] **Step 2: Tiêm lỗi giả để chứng minh guard đỏ được**

Tạm đặt `width: 4000px` cho `.semantic-stage`, chạy lại, xác nhận test **ĐỎ**, rồi hoàn tác. Guard chưa từng đỏ là guard chưa được chứng minh (`ARCHITECTURE_MAP §8` #14).

- [ ] **Step 3: Sinh baseline và chạy**

```bash
cd frontend && npx playwright test tests/visual/semantic-route.spec.ts --update-snapshots
cd frontend && npx playwright test tests/visual/semantic-route.spec.ts
```
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/tests/visual frontend/scripts/capture-semantic-route.mjs
git commit -m "test(semantic-program): L5a visual regression cho 3 case dai dien"
```

---

## Task 12: Mở SEALED — ĐÚNG MỘT LẦN

**Files:**
- Create: `backend/scripts/run_sealed_evaluation.py`
- Create: `docs/evaluation/semantic-benchmark/results/RESULTS.md`

**Interfaces:**
- Consumes: `sealed/cases.json` + `FINGERPRINT.txt` + freeze protocol
- Produces: `results/raw.jsonl` · `results/RESULTS.md` với A và B **đồng-primary**, D1/D2 tách bạch

> **LIVE AI — DỪNG VÀ XIN PHÉP USER trước khi chạy.** Cần `ALLOW_LIVE_AI=1` và budget đã chốt. Đây là điều kiện dừng #6.

- [ ] **Step 1: Kiểm con dấu còn nguyên TRƯỚC khi chạy**

```bash
cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/seal_benchmark.py
```
Expected: `Fingerprint khớp — seal còn nguyên.` (exit 0). Lệch → **DỪNG**, seal đã vỡ (§7.4).

- [ ] **Step 2: DỪNG — xin user duyệt budget live**

- [ ] **Step 3: Chạy evaluation một lần**

```bash
cd backend && ALLOW_LIVE_AI=1 PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe \
  scripts/run_sealed_evaluation.py --out-dir ../docs/evaluation/semantic-benchmark/results \
  --max-api-calls <budget đã duyệt>
```

- [ ] **Step 4: Viết `RESULTS.md`**

Báo cáo **đúng những gì đã đóng băng**, không thêm chỉ số mới sau khi thấy số:

```markdown
## Kết quả — SEALED benchmark, mở 1 lần

Fingerprint: <sha256>   ·   N = <N>   ·   Budget đã dùng: <x>/<y> call

| Chỉ số | Giá trị |
|---|---|
| **A — Generative executability rate** | <a>/<N> |
| **B — Safe serve rate** (STRONG assurance) | <b>/<N> |
| capability_gap | <c> |
| verification_gap | <v> |

Khoảng cách A − B = <a-b>. Phân tích vì sao khoảng cách đó tồn tại: …

### D1 (cấu trúc) — đúng theo cấu tạo
Sau khi IR đã sinh, số bước runtime KHÔNG tiêu thêm token LLM.
Bằng chứng: <số bước trung bình> bước / <token của stage sinh> token.

### D2 (thực nghiệm) — matched subset
Chỉ trên <m> bài cả hai route đều phục vụ thành công.
Token/mô phỏng giao thành công: cũ <x> vs mới <y>. Shadow cost báo riêng: <z>.
```

- [ ] **Step 5: Commit — kể cả lượt thất bại**

```bash
git add docs/evaluation/semantic-benchmark/results backend/scripts/run_sealed_evaluation.py
git commit -m "eval(semantic-program): mo SEALED benchmark, bao cao A/B dong-primary + D1/D2"
```

---

## Task 13: Artifact về repo + phần còn lại của §8

**Files:**
- Move: artifact từ `C:\Users\Bunny\.gemini\antigravity-ide\brain\…` → `docs/evaluation/semantic-program-cert/`
- Modify: `backend/scripts/run_live_gemini_semantic_smoke.py:29` (`ARTIFACT_DIR`)
- Modify: `docs/CURRENT_STATE.md` · `docs/CODE_INDEX.md` · `docs/CORRECTNESS.md`

- [ ] **Step 1: Sửa `ARTIFACT_DIR` trỏ vào repo**

```python
ARTIFACT_DIR = Path(__file__).resolve().parents[2] / "docs" / "evaluation" / "semantic-program-cert"
```

- [ ] **Step 2: Chuyển artifact cũ vào repo** (E13 — kể cả lượt thất bại)

- [ ] **Step 3: Cập nhật `docs/CURRENT_STATE.md`** — thêm route mới vào bảng danh tính; cập nhật `CACHE_VERSION` nếu đã bump ở Task 4.

- [ ] **Step 4: Cập nhật `docs/CODE_INDEX.md`** — mọi module mới, **mô tả nó sở hữu gì**, không chép mỗi tên file:

`pacer.py` · `obligations.py` · `request_contract.py` · `coverage_gate.py` · `grounding_gate.py` · `postconditions.py` · `execution_authority_gate.py` · `telemetry.py` · `domains/semantic/*` · `seal_benchmark.py` · `run_sealed_evaluation.py`

- [ ] **Step 5: Cập nhật `docs/CORRECTNESS.md`** — ghi §5.4 (hai mức đảm bảo) vào trục canonical.

- [ ] **Step 6: Chạy cổng T3 đầy đủ**

```bash
cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest -q
cd frontend && npm run test:full
```
Expected: `FULL_PRODUCT_GATE_PASS`

- [ ] **Step 7: Commit**

```bash
git add docs backend/scripts
git commit -m "docs(semantic-program): dua artifact ve repo + cap nhat CURRENT_STATE/CODE_INDEX/CORRECTNESS"
```

---

## Self-Review

**Spec coverage:** §1.1 → Global Constraints · §3.1 → T8 · §3.2 → T6/T7/T8 · §3.3 → T8 · §3.4 → T7 · §3.5 → T7 · §3.6 → T8 · §3.7 → ngoài phạm vi (SUPPORTING) · §4.1–4.6 → T3 · §5.1–5.3 → T6/T9/T10 · §5.4 → T10 · §5.5 → SUPPORTING · §6.1–6.4 → T5 · §6.5 → T12 · §7 L1/L2 → đã có · L3 → T2/T3 · L5a → T11 · §7.1–7.4 → T1/T12 · §8 → T0/T13 · §10.2 → T8/T10.

**Placeholder scan:** không có TBD/TODO; mọi step có mã thật hoặc lệnh chạy thật. Ba chỗ **cố ý dừng hỏi user** (T1 step 3 nguồn SEALED · T12 step 2 budget live · T4 bump `CACHE_VERSION`) đều là điều kiện dừng đã thoả thuận, không phải placeholder.

**Type consistency:** `VisualFrame(step_index, narration, tier1_fact, objects, highlighted_object_ids)` dùng nhất quán T2/T3/T8 · `CoverageResult(ok, error_code, missing)` dùng chung C₁a (T6) và C₁b (T9) · `Obligation.witness` là property đọc từ `params["witness"]`, dùng ở T6/T9/T10 · `check_execution_authority(analysis, plan, has_interpreter)` khớp T8.
