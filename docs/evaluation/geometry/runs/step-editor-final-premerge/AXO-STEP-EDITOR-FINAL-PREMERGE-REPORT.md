# AXO Step Editor — Final Pre-Merge Verification & Root-Cause Hardening Report

- **Campaign:** `AXO STEP EDITOR — FINAL PRE-MERGE VERIFICATION & ROOT-CAUSE HARDENING`
- **Date:** `2026-11-18`
- **Branch / Worktree:** `feat/axo-geometry-library-verification` @ `D:/Documents/projects/axo-geometry-library`
- **Base HEAD Before This Run:** `ac8badd6366bb7b4df43297ef75f01a9aafa3c45` (`feat(step-editor): complete independent acceptance, localhost QA and REA MCP verification`)
- **Model Status:** `MODEL_NOT_TRAINED` (zero-LLM deterministic closed grammar + Exact Kernel; zero external LLM calls during step edits)
- **Physical Mobile Hardware:** `NOT_VERIFIED` (verified only under headless Chromium responsive + touch emulation `390×844`, `360×800`, `320×568`)

---

## 1. Branch, HEAD, Working Tree và Commit

| Hạng mục | Giá trị xác minh |
|---|---|
| Worktree đang kiểm chứng | `D:/Documents/projects/axo-geometry-library` |
| Root checkout được bảo vệ | `D:/Documents/projects/algo-sim` (branch `axo-ui-consistency`, không bị chạm tới) |
| Branch mục tiêu | `feat/axo-geometry-library-verification` |
| Commit nền trước chiến dịch | `ac8badd6366bb7b4df43297ef75f01a9aafa3c45` |
| Thay đổi phiên song song trên working tree | `77` file/hunk `OWNERSHIP_BLOCKED` (`backend/app/main.py`, `backend/app/accounts/*`, `backend/app/persistence/classroom_models.py`, `backend/alembic/versions/f8a2c41d9e05_remove_classroom_and_live_session_tables.py`, `backend/tests/test_postgres_axo_history_migration.py`, `docs/EVIDENCE_INDEX.md`, `frontend/package*.json`, Landing/Auth/Classroom components, và hunk Classroom trong `SimulationWorkspace.tsx`) được giữ nguyên hoàn toàn |
| Chính sách Git | Chỉ commit allowlist cục bộ trên `feat/axo-geometry-library-verification`; **không merge vào `main`, không `git push`** (chờ Owner nghiệm thu) |

---

## 2. Phạm Vi Thay Đổi Thực Tế

Kiến trúc thực thi thực tế đã đối chiếu từ UI tới persistence:

```text
ConstructionStepEditor.tsx (hover/focus/tap V1, Hủy/Chạy, draft theo stepIndex)
  └─ construction-step-edits.ts (client_seq, client_request_id, committed_version clock, POST /steps/cancel, bounded 1500ms /state recovery)
       └─ scene3d-model.ts (markVerifiedStepEditedScene, isVerifiedStepEditedScene — rebind Hybrid /4 answers)
            └─ POST /api/simulation/steps/edit & /steps/cancel (step_edit_router.py: per-session RLock, client_seq supersede, HTTP 409/422/503)
                 └─ step_edit_route.py (DEFAULT_SCENE3D_HOOKS IoC wrapper)
                      └─ step_editor.py (Parser FP-1 → DAG → Planner → Exact Kernel → Equivalence FP-2 & Global Invariants FP-3)
```

Chỉ **7** file sản phẩm/test/index và thư mục run mới dưới `docs/evaluation/geometry/runs/step-editor-final-premerge/` được sửa/tạo trong chiến dịch này. Không sửa Landing Page (`/` hoặc `/gioi-thieu`), không sửa `SimulationWorkspace.tsx`, `backend/app/main.py`, `accounts/*`, `alembic/*`, hoặc bất kỳ file `OWNERSHIP_BLOCKED` nào.

---

## 3. Bảng Nguyên Nhân Gốc Phát Hiện Mới (`FP-1` .. `FP-6` + Lỗi Khám Phá Khi Hardening)

| Mã lỗi | Tầng phát sinh | Biểu hiện tái hiện RED trước sửa | Nguyên nhân gốc | Sửa tận gốc |
|---|---|---|---|---|
| **FP-1** | `step_editor.py` (`_parse_single_clause`, `_split_compound_clauses`, `_symbol_index_before_step`, `_resolve_plane_id`) | `Dựng mặt phẳng trung trực của AB.` → `422 UNSUPPORTED_STEP_SYNTAX`; `P thuộc AB, AP/AB = 1/3` / `AP/PB = 1/3` / `AB/AP = 4` → từ chối sai; `d_khong_ton_tai` trong `vuông góc với d_khong_ton_tai` → `UNSUPPORTED_STEP_SYNTAX` thay vì `MISSING_DEPENDENCY`; bước 8 `hinh-non-cat-song-song-day` tạo `plane_MIS` giả khi đối chiếu identity | (a) Regex thiếu `(?-i:...)` khi bật `re.IGNORECASE`; (b) regex trung trực/trung điểm lồng đòi tên tường minh; (c) ratio parser thiếu cú pháp dấu phẩy & tỉ số đoạn con; (d) `5a`/`5b` không nhận snake_case `[a-zΔ][a-zA-Z0-9_']*`; (e) `_symbol_index_before_step` thiếu khóa `({label})` cho `plane3` và `_resolve_plane_id` chạy `_extract_points` lên văn xuôi Tiếng Việt `"Mặt phẳng..."` | Chuẩn hóa parser `FP-1`, mở rộng `line_id_pat` `5a`/`5b`, đăng ký `f"({nc})"` trong `_symbol_index_before_step`, và giới hạn `inner_pts` chỉ nhận nhãn mặt phẳng thuần ký hiệu đỉnh |
| **FP-2** | `step_editor.py` (`execute_step_edit`, `_exact_values_equivalent`, `section.py`) | Diễn đạt tương đương (`"Dựng mặt phẳng trung trực của AB."`, `"(MPN)"`) luôn trả `before_after_diff.changed = True`; thiết diện quay chu trình `MENPF` ↔ `NPFME` bị đánh giá sai khác | Hardcode `before_after_diff["changed"] = True` trước kiểm tra hình học; `Section` chưa đối chiếu tương đương nhị diện (cyclic + reversed) | Tính `before_after_diff["changed"] = not computed_equiv["geometrically_equivalent"]` trên giá trị Exact Kernel trước/sau + kiểm chứng hoán vị vòng & đảo chiều đa giác `Section` |
| **FP-3** | `step_editor.py` (`verify_rebuilt_geometry`) | Đổi tỉ số làm hỏng tâm mặt cầu ngoại tiếp hoặc phá vuông góc chung (`PQ ⊥ BD` ở Sample `khoang-cach-hai-duong-cheo-nhau`), góc nhị diện, chân hình chiếu mặt nghiêng, mặt phẳng `(MNP)` không đi qua `N, P`, hoặc biến dạng chiều cao `SA` vẫn commit `200` | Chỉ kiểm tra tính hợp lệ cục bộ; thiếu đối chiếu invariant toàn cục và bỏ sót `type == "quantity"` khi hydrate `before_mem` (dòng `2256`), khiến `b_q == Fraction(0)` không bao giờ kích hoạt | Hydrate cả `"quantity"` vào `before_mem`, bổ sung kiểm tra `PLANE_VERTEX_INCIDENCE_MISMATCH`, `DOWNSTREAM_PERPENDICULAR_INVARIANT_BROKEN`, `DOWNSTREAM_ORTHOGONALITY_BROKEN`, và `DOWNSTREAM_CIRCUMSCRIBED_SPHERE_BROKEN` |
| **FP-4** | `scene3d-model.ts`, `construction-step-edits.ts` | Sau khi edit hợp lệ đổi `M` (`z=3 → 9/2`) và diện tích `S_td`, đáp án Hybrid `/4` cũ bị kiểm tra chéo sai và gắn cờ `INVALID` / mâu thuẫn | Đáp án Hybrid `/4` đối chiếu hệ số snapshot gốc trước khi edit thay vì giá trị Exact Kernel vừa tái dựng | Thêm `markVerifiedStepEditedScene` / `isVerifiedStepEditedScene` gắn dấu đã kiểm chứng trên scene đã rebuild và cho phép rebind đáp án Hybrid tương thích |
| **FP-5** | `construction-step-edits.ts`, `step_edit_router.py` | Sau một lượt `422` (làm tăng `revision_count` mà không đổi `committed_version`), `fetchStepEditSessionState` nhầm version clock và có thể từ chối/đè state | Trộn lẫn `revision_count` (mọi attempt kể cả `422`) với `committed_version` (chỉ tăng khi commit `200`) | Tách bạch đồng hồ `committed_version` trên cả router `GET /state` và client cache `saveCachedStepEditState` |
| **FP-6** | `step_edit_router.py`, `construction-step-edits.ts` | Nhấn `Hủy` khi request đang chạy hoặc timeout/rớt mạng sau commit: server vẫn có thể commit âm thầm, timeout 25ms bị treo vào `fetch("/state")` không tín hiệu hủy, hoặc lỗi DB trả nhầm `422` thay vì `503` | Chưa có endpoint `POST /steps/cancel`, chưa kiểm `client_seq`, lỗi `OperationalError` rơi vào rollback chung, nhánh `abortReason === "timeout"` chạy vào `/state` recovery không signal | Thêm `POST /api/simulation/steps/cancel` (pre-commit & post-commit rollback), `client_seq` (`409 EDIT_SUPERSEDED`), `last_committed_request_id` để client hòa giải socket drop với timeout riêng 1500ms, trả `REQUEST_TIMEOUT` trước khi gọi `/state`, và trả `503 PERSISTENCE_UNAVAILABLE` khi lỗi DB |

---

## 4. Ma Trận Mutation & Independent Geometry Oracle (Nhóm A / B / C / D)

Xác minh trực tiếp qua [test_step_editor_final_premerge.py](../../../tests/geometry/test_step_editor_final_premerge.py) (`14 passed`) và host sống:

| Nhóm | Ca kiểm thử đại diện | Kết quả mong đợi | Kết quả thực tế |
|---|---|---|---|
| **Group A** (Tương đương ngữ nghĩa) | Sample 11 `(α)`: `"Dựng mặt phẳng trung trực của AB."`; Sample 1 `(MNP)` → `"(MPN)"` giữ `MENPF` ↔ `NPFME`; inline helper `H` tái định nghĩa → thu hồi helper cũ | `200`, `geometrically_equivalent = True`, `before_after_diff.changed = False`, `cycle MENPF` bảo toàn | **PASS** (`test_fp2_group_a_semantic_equivalence_no_false_diff_and_section_cycle` & host State 3) |
| **Group B** (Đột biến hình học hợp lệ + oracle độc lập) | Tứ diện vuông `O.ABC` dựng hoàn toàn tổng hợp với điểm tự do `Q` độc lập; đổi trung điểm `M` trên `OA` sang `OM/MA = 1/2` (`M=(2,0,0)`) → tái dựng `(α)`, tâm mặt cầu `I=(1/4,1/3,1/4)`, `r² = 59/144`, giữ nguyên `Q=(0,1/2,1)` qua `GET /state` | `200`, `changed = True`, tọa độ & bán kính khớp oracle giải tích độc lập, `Q` giữ nguyên tọa độ | **PASS** (`test_fp_group_b_valid_geometric_mutation_with_independent_analytical_oracle` + Sample 1 `M=(0,0,9/2)` trên host sống + `F5` reload) |
| **Group C** (Hợp lệ cục bộ nhưng phá invariant toàn cục — `6/6`) | (1) Dời trung trực trên Sample 11 → `DOWNSTREAM_CIRCUMSCRIBED_SPHERE_BROKEN`; (2) Dời chân `P` đường vuông góc chung `BP/BD = 1/5` trên `khoang-cach-hai-duong-cheo-nhau` → `DOWNSTREAM_ORTHOGONALITY_BROKEN`; (3) Dời `H` trên `goc-nhi-dien-hai-mat-phang` → `DOWNSTREAM_ORTHOGONALITY_BROKEN`; (4) Thay hình chiếu `H` trên `(SBC)` bằng trọng tâm → `DOWNSTREAM_ORTHOGONALITY_BROKEN`; (5) Đổi `(MNP)` qua `M // (ABCD)` làm rớt `N, P` → `PLANE_VERTEX_INCIDENCE_MISMATCH`; (6) Đổi `chieu_cao_SA` thành `SB` → `DOWNSTREAM_PERPENDICULAR_INVARIANT_BROKEN` | Tất cả **phải** fail-closed HTTP `422` đúng mã lỗi | **PASS** (`6/6` trong `test_fp3_group_c...` + xác minh `BP/BD = 1/5` trên host sống `:3001`) |
| **Group D** (Mutation lỗi + bảo toàn state — `9/9`) | Commit hợp lệ trước (`H` trung điểm `AB`), sau đó gửi lần lượt 9 input lỗi: thiếu điểm (`SZ`), thiếu đường snake_case (`d_khong_ton_tai`), cú pháp sai (`zz_khong_ton_tai`), 3 điểm thẳng hàng (`A, O, C`), sai loại bước (`Nối đoạn thẳng AB`), vòng phụ thuộc (`I`), khối cong ngoài phạm vi (`hình nón`), chưa hỗ trợ (`qua P song song AB`), tỉ số âm (`AH/HB = -1`) | HTTP `422 rolled_back`, `GET /state` vẫn giữ nguyên `committed_version` & `override` hợp lệ trước đó | **PASS** (`9/9` trong `test_group_d...` + xác minh `SZ` trên host sống `:3001`) |

---

## 5. Bằng Chứng Downstream Regeneration

- **Sample 1 (`chop-thiet-dien-ba-diem`) trên host sống (`:3001` + `:8000`):** Sửa `M` sang `"Lấy điểm M thuộc SA sao cho SM/SA = 1/4"` làm tái dựng chính xác **6** đối tượng downstream (`M` dịch tới `['0', '0', '9/2']`, `mp_MNP`, `E`, `F`, `thiet_dien`, `S_td`) trong khi `A, B, C, D, S, O, N, P` được DAG bảo toàn (`skipped_unaffected`), và sau `F5` reload bước 6 vẫn giữ nội dung `SM/SA = 1/4`.
- **Sample `lang-tru-tam-giac-thiet-dien` (Lăng trụ đứng `ABC.A′B′C′`):** Sửa `P` sang `"Lấy điểm P trên CC′ sao cho CP = 1/3 CC′"` → HTTP `200`, `changed = True`, UI dock hiển thị sạch `CC′`, **`0` rò rỉ `_prime`**.
- **Oracle độc lập `O.ABC`:** Nhánh độc lập `Q = midpoint(B, C)` giữ nguyên exact coords `['0', '1/2', '1']` qua partial rebuild và `GET /api/simulation/sessions/{id}/state`.

---

## 6. Concurrency, Atomic Commit, Cancel, Persistence & Production Boundary

- **Xác minh thực nghiệm (`test_fp6_...` & `backend-perf-comparison.json`):**
  - Hai request song song cùng `session_id`: `100%` mỗi vòng đua trả đúng một `200` + một `409 CONCURRENT_STEP_EDIT_CONFLICT` (3/3 rounds trong `backend-perf-comparison.json`; `RLock` serialize sạch khi dùng `step_edit_router`).
  - `client_seq` cũ đến sau (`seq=1` sau `seq=2`): từ chối với HTTP `409 EDIT_SUPERSEDED`, giữ nguyên commit của `seq=2`.
  - In-flight `POST /api/simulation/steps/cancel`: cả pre-commit (đóng cờ hủy trong `_CANCELLED_REQUESTS`) và post-commit (khôi phục `step_edit_sessions` về snapshot & `committed_version` trước đó) giữ nguyên state sạch — đã xác minh cả trong pytest và khi nhấn `Hủy` giữa chừng trên browser + `F5` reload (`cancelPostsDelta = 1`, `cancelHttpStatus = 200`, text đã hủy không tồn tại sau reload).
  - Mô phỏng `OperationalError` giữa giao dịch DB: router trả HTTP `503 PERSISTENCE_UNAVAILABLE` (`Cache-Control: no-store`), không ghi commit dở dang, `GET /state` trước đó không bị hỏng.
  - Đa tiến trình SQLite thật (2 tiến trình tranh chấp cùng `session_id` + 4 tiến trình song song `USER_0..USER_3` khác session): `test_fp6` **PASS** toàn bộ.
- **Ranh giới triển khai thực tế đã kiểm tra (`backend/Dockerfile` & `docker-compose.yml`):** Production chạy đơn tiến trình `uvicorn app.main:app --host 0.0.0.0 --port 8000` (không có `--workers`). Khóa in-process `_SESSION_LOCKS`, `_CANCELLED_REQUESTS`, `_LATEST_CLIENT_SEQ` an toàn cho mô hình đơn worker hiện tại; nếu tăng `--workers > 1` trong tương lai sẽ cần phân tán trạng thái khóa/cancel qua PostgreSQL row/advisory lock hoặc Redis.
- **Patch Alembic PostgreSQL cho `step_edit_*` (`BLOCKED_OWNERSHIP`):** Phiên song song giữ `AXO_HEAD = "f8a2c41d9e05"` trong `backend/tests/test_postgres_axo_history_migration.py` nên chưa được chèn file migration vào chuỗi Alembic lúc này. Patch độc lập để Owner/Admin áp dụng khi tích hợp:

```python
"""add step edit tables

Revision ID: 9c4d8e2b7a10
Revises: f8a2c41d9e05
Create Date: 2026-11-18
"""
from alembic import op
import sqlalchemy as sa

revision = "9c4d8e2b7a10"
down_revision = "f8a2c41d9e05"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "step_edit_sessions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("owner_scope", sa.String(length=96), nullable=False),
        sa.Column("session_id", sa.String(length=128), nullable=False),
        sa.Column("problem_key", sa.String(length=160), nullable=False, server_default=""),
        sa.Column("base_scene_sha256", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("committed_scene_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("step_overrides_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("dependency_graph_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("revision_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_scope", "session_id", name="uq_step_edit_session_owner_sid"),
    )
    op.create_index("ix_step_edit_sessions_owner_scope", "step_edit_sessions", ["owner_scope"])
    op.create_index("ix_step_edit_sessions_session_id", "step_edit_sessions", ["session_id"])

    op.create_table(
        "step_edit_revisions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("revision_id", sa.String(length=64), nullable=False),
        sa.Column("owner_scope", sa.String(length=96), nullable=False),
        sa.Column("session_id", sa.String(length=128), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("step_id", sa.String(length=80), nullable=False),
        sa.Column("step_index", sa.Integer(), nullable=False),
        sa.Column("previous_instruction", sa.Text(), nullable=False),
        sa.Column("edited_instruction", sa.Text(), nullable=False),
        sa.Column("normalized_intent_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("affected_dependencies_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("validation_status", sa.String(length=32), nullable=False),
        sa.Column("execution_status", sa.String(length=32), nullable=False),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("learner_error", sa.Text(), nullable=True),
        sa.Column("stage_timings_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("before_scene_digest", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("after_scene_digest", sa.String(length=64), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("revision_id"),
        sa.UniqueConstraint("owner_scope", "session_id", "version_number", name="uq_step_edit_revision_version"),
    )
    op.create_index("ix_step_edit_revisions_revision_id", "step_edit_revisions", ["revision_id"])
    op.create_index("ix_step_edit_revisions_owner_scope", "step_edit_revisions", ["owner_scope"])
    op.create_index("ix_step_edit_revisions_session_id", "step_edit_revisions", ["session_id"])

    op.create_table(
        "step_edit_feedback",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("feedback_id", sa.String(length=64), nullable=False),
        sa.Column("revision_id", sa.String(length=64), nullable=False),
        sa.Column("owner_scope", sa.String(length=96), nullable=False),
        sa.Column("session_id", sa.String(length=128), nullable=False),
        sa.Column("problem_group_key", sa.String(length=96), nullable=False),
        sa.Column("original_step", sa.Text(), nullable=False),
        sa.Column("corrected_step", sa.Text(), nullable=False),
        sa.Column("original_intent_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("corrected_intent_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("geometry_context_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("dependency_context_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("registry_operations_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("validation_result_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("execution_result_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("user_acceptance_status", sa.String(length=32), nullable=False, server_default="PENDING_VERIFICATION"),
        sa.Column("dataset_eligibility", sa.String(length=32), nullable=False, server_default="INELIGIBLE"),
        sa.Column("reviewer_note", sa.Text(), nullable=True),
        sa.Column("schema_version", sa.String(length=32), nullable=False, server_default="axo-step-feedback/1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("feedback_id"),
    )
    op.create_index("ix_step_edit_feedback_feedback_id", "step_edit_feedback", ["feedback_id"])
    op.create_index("ix_step_edit_feedback_revision_id", "step_edit_feedback", ["revision_id"])
    op.create_index("ix_step_edit_feedback_owner_scope", "step_edit_feedback", ["owner_scope"])
    op.create_index("ix_step_edit_feedback_session_id", "step_edit_feedback", ["session_id"])
    op.create_index("ix_step_edit_feedback_problem_group_key", "step_edit_feedback", ["problem_group_key"])
    op.create_index("ix_step_edit_feedback_user_acceptance_status", "step_edit_feedback", ["user_acceptance_status"])
    op.create_index("ix_step_edit_feedback_dataset_eligibility", "step_edit_feedback", ["dataset_eligibility"])


def downgrade() -> None:
    op.drop_table("step_edit_feedback")
    op.drop_table("step_edit_revisions")
    op.drop_table("step_edit_sessions")
```

---

## 7. Kết Quả Kiểm Thử Đầy Đủ (Chạy Sau Lần Sửa Code Cuối Cùng)

| Suite / Lệnh | Phạm vi | Kết quả quan sát | Phân loại |
|---|---|---|---|
| `pytest tests/geometry -q` (gồm cả 7 suite Step Editor & `test_step_editor_final_premerge.py`) | Toàn bộ `tests/geometry/` (`25` file) | **`11972 passed, 6 skipped, 1 deselected, 9 xfailed, 15 failed` (`440.01s`)**; **0 failure trong 7 suite Step Editor** (`163/163` PASS) | Step Editor **PASS**; 15 failure còn lại là `EXPECTED_EXCEPTION` / `BLOCKED_OWNERSHIP` / `PRE_EXISTING` (chi tiết mục 12) |
| `pytest tests/semantic_program --ignore=tests/semantic_program/test_evaluation_candidate.py -q` | Trình biên dịch / kernel IR | **`1166 passed, 1 skipped` (`6.61s`)** | **PASS** |
| `pytest tests/semantic_program/test_evaluation_candidate.py -q` | Đóng băng candidate `88ff25730` | `25 passed, 1 failed` (`30.69s`) | `EXPECTED_EXCEPTION` (`measured_system.tree_hash` `b1a8d439...` → `9a2cc013...`) |
| `pytest tests --ignore=tests/geometry --ignore=tests/semantic_program -q` | Core API / router / auth / history | **`793 passed, 2 deselected` (`92.81s`)** | **PASS** |
| `python scripts/replay_demo_cases.py` & `audit_demo_crash_surface.py` | 5 demo replay + 1 rút gọn + 6 biên lỗi | **`5/5 + 1/1` PASS**, **`6/6` bounded (`0` unhandled)** | **PASS** |
| `npx vitest run src/components/construction-step-editor.test.tsx src/code-index-sync.test.ts` | Unit + UI Step Editor + đồng bộ `CODE_INDEX` | **`23 passed (2 files)` (`20/20` + `3/3`, `5.04s`)** | **PASS** |
| `npx vitest run` (standalone) | Toàn bộ Frontend | **`192 passed (192)`, `2270 passed (2270)` (`155.08s`)** | **PASS** |
| `npx tsc -b` & `npx vite build` | TypeScript + Production bundle | `0` lỗi TS; `dist/` built trong `7.71s` | **PASS** |
| `backend/tests/scripts`: 22-sample round-trip (`backend_perf_comparison.py`) | 22 mẫu · `166` bước UI (`SimulationWorkspace` extractor) | `135` editable thử nghiệm, **`117 passed`** (tăng từ `110`), **`0` `identity_false_diff_changed`**, **`0` `_prime` leaks**, `18` ngoài phạm vi (hình cong / readout / tên trơn) | **PASS** |
| `python backend/scripts/audit_docs_information_architecture.py` | Cấu trúc tài liệu & liên kết | `Internal links broken: 0`, `Secret leaks: 0`, `Docs root closed list: True (29 root docs, 167 catalogued, unclassified [])`; exit `1` chỉ vì `CODE_INDEX stale paths: 4` | `BLOCKED_OWNERSHIP` (4 file Classroom dòng 4612–4653 bị xóa bởi phiên song song) |
| `node frontend/scripts/audit-layout.mjs --port 3001` | Script soát layout cũ | Exit `1` tại Landing `/` (`KHÔNG TỚI ĐƯỢC "Trang chủ"`) | `PRE_EXISTING` (Landing đặt tại `/` thay cho `/app`) |

---

## 8. Performance Before / After

Nguồn số liệu: [backend-perf-comparison.json](results/backend-perf-comparison.json), [backend-perf-oracle.json](../../step-editor-independent-acceptance/results/backend-perf-oracle.json), và [live-host-qa.json](results/live-host-qa.json).

| Chỉ số | Baseline (Independent Acceptance) | Final Pre-Merge (Observed) | Chênh lệch & Giải thích kỹ thuật |
|---|---|---|---|
| Compatible UI steps passing round-trip (22 mẫu) | `110` | **`117`** | **`+7` bước** nhờ parser `FP-1` và chuẩn hóa khóa nhãn mặt phẳng `({label})` |
| Identity round-trip false `changed=True` | Không đo (`N/A`; thủ công `True`) | **`0 / 117`** | Sửa `before_after_diff` + loại trừ lỗi `plane_MIS` |
| Backend stage median (`48` baseline / `50` steps sau) | `13.046 ms` (`p95 = 17.596 ms`) | **`18.699 ms`** (`p95 = 27.035 ms`) | `+5.653 ms` do `verify_rebuilt_geometry` hydrate đầy đủ `before_mem` (kể cả `quantity`) và đối chiếu Exact Kernel equivalence + invariant toàn cục (đúng quy tắc không giảm kiểm chứng toán học để lấy tốc độ) |
| 25-edit `tracemalloc` benchmark | `mean = 84.287 ms`, `peak = 733.51 KB` | **`mean = 134.679 ms`**, `peak = 754.22 KB`, `objects 24 → 24` | Không rò rỉ đối tượng hay bộ nhớ; tải tăng tương xứng kiểm chứng toàn cục mới |
| 2-thread cross-session (`10` ops) | Chưa đo | **`10/10` HTTP `200`**, `median = 103.424 ms`, `max = 257.736 ms` | Ổn định |
| 2-thread same-session race (`3` rounds) | Chưa đo | **`3/3` rounds trả đúng `[409, 200]`**, `median = 67.399 ms`, `max = 72.643 ms` | Tuần tự hóa an toàn bởi `RLock` |
| Live Browser 20-edit UI round-trip | `mean = 353.36 ms`, `p95 = 485.56 ms` | **`mean = 331.43 ms`**, **`p95 = 464.14 ms`**, `max = 577.91 ms` | **Nhanh hơn baseline `-21.93 ms`**, `canvasCountFinal = 1`, `heapStartMb = 77.63 === heapEndMb = 77.63` (`delta = 0 MB`) |

---

## 9. Live Browser & REA MCP CDP QA

- **Host sống kiểm chứng:** Backend `http://127.0.0.1:8000` (`PID 9868`, `/api/health → 200`) + Frontend `http://localhost:3001` (`PID 11008`, `/`, `/gioi-thieu`, `/gioi-thieu?preview=v1.4`, `/app → 200`, `overflowX = 0`).
- **8 trạng thái trực tiếp trên browser ([live-host-qa.json](results/live-host-qa.json)):**
  1. **State 1 (Baseline):** `defaultHeight = 56.875 px === hoverHeight = 56.875 px` (`heightDeltaPx = 0`), bút chì mặc định `opacity = "0"`, hover `opacity = "1"`.
  2. **State 2 (Editor open):** `openMs = 58.18 ms`, chỉ có `["Hủy", "Chạy"]`, nhấn `Space` / `ArrowLeft` không đổi bước đang chọn (`activeTitleBefore === activeTitleAfter`), `Escape` đóng editor.
  3. **State 3 (Group A — Sample 11 `"Dựng mặt phẳng trung trực của AB."`):** HTTP `200`, `before_after_diff.changed === false`, `postsTriggered = 1`.
  4. **State 4 (Group B — `chop-thiet-dien-ba-diem` `"Lấy điểm M thuộc SA sao cho SM/SA = 1/4"` + `F5` + prism `′`):** HTTP `200`, `before_after_diff.changed === true`, cập nhật đúng 6 đối tượng `["M", "mp_MNP", "E", "F", "thiet_dien", "S_td"]`, `M = ["0", "0", "9/2"]`, `frontendCommitRenderMs = 127.5 ms`, **sau `F5` reload bước 6 vẫn giữ nguyên nội dung `SM/SA = 1/4`**; trên `lang-tru-tam-giac-thiet-dien` edit `CP = 1/3 CC′` hiển thị `CC′`, `0` lỗi `_prime`.
  5. **State 5 (Group C & D `422`):** Sample `khoang-cach-hai-duong-cheo-nhau` sửa `P` thành `"Lấy điểm P thuộc BD sao cho BP/BD = 1/5"` → HTTP `422 DOWNSTREAM_ORTHOGONALITY_BROKEN`, giữ nguyên draft & dấu vuông góc 3D; Sample 11 `"Dựng mặt phẳng trung trực (P) của cạnh SZ."` → HTTP `422 MISSING_DEPENDENCY`, giữ nguyên step cũ & draft.
  6. **State 6 (Cancel giữa chừng + `F5` & Offline Recovery):** Nhấn `Hủy` khi `/edit` đang chạy gửi `POST /api/simulation/steps/cancel` (`200`), sau `F5` reload text đã hủy **không** lưu lên server; ngắt mạng tạm thời báo lỗi tiếng Việt & giữ draft, nối lại mạng nhấn `Chạy` → HTTP `200` commit sạch.
  7. **State 7 (`prefers-reduced-motion: reduce`):** Khớp media query và commit `200` sạch.
  8. **State 8 (20 edits tuần tự):** `mean = 331.43 ms`, `canvasCountFinal = 1`, `heapDeltaMb = 0`, `pageErrors = []`, `failedNetworkRequests = []`.
- **REA MCP CDP Inspection (`http://127.0.0.1:9338` trên `pyramid-three-point-section`, [rea-mcp-inspection.json](results/rea-mcp-inspection.json)):**
  - `list_browser_targets`: `ev_06bc8f7ca9acb0a2aa6ff3259d2422256e27559e62875c49c3273fc79e23a8e0`
  - `inspect_web_page`: `ev_1a7e8e432364b8a636e7b50a86d568601175f8d2d62a590bc96c235d89330053` (`console_errors = 0`, `115` scripts, `20` resources)
  - `capture_web_screenshot`: `ev_dd3aee13413e5a0d37ac65c0811db2caf92807923cd69c223b58b3a31faab5ad` (`sha256: 7c6be261d76b65f48d65b08adb7e88e027ed641f879c48783dd25edfe808574e`, `133855` bytes, ảnh lưu tại [rea-mcp-cdp-screenshot.png](images/rea-mcp-cdp-screenshot.png)).

---

## 10. Responsive 8-Viewport & Visual Inspection Evidence

Mọi viewport kiểm tra đều đạt `overflowX = 0`, `canvasVisible = true`, `dockVisible = true`, `runClipped = false`, `cancelClipped = false`, `textareaClipped = false`, `scrollHostIndependent = true`:

| Viewport | `overflowX` | Canvas & Dock hiển thị | Editor không cắt mép | Bằng chứng ảnh |
|---|---|---|---|---|
| `1920×1080` Desktop | `0` | `True` | `True` | [fp-1920-state1-before-hover.png](images/fp-1920-state1-before-hover.png), [fp-1920-state2-editing-open.png](images/fp-1920-state2-editing-open.png), [fp-1920-state4-group-b-mutated-reloaded.png](images/fp-1920-state4-group-b-mutated-reloaded.png), [fp-1920-state5-group-c-422.png](images/fp-1920-state5-group-c-422.png), [fp-1920-prism-prime-check.png](images/fp-1920-prism-prime-check.png) |
| `1440×900` Desktop | `0` | `True` | `True` | [fp-vp-1440x900-editing.png](images/fp-vp-1440x900-editing.png) |
| `1366×768` Laptop | `0` | `True` | `True` | [fp-vp-1366x768-editing.png](images/fp-vp-1366x768-editing.png) |
| `1024×768` Tablet ngang | `0` | `True` | `True` | Đo DOM trực tiếp (`live-host-qa.json`) |
| `768×1024` Tablet dọc | `0` | `True` | `True` | [fp-vp-768x1024-editing.png](images/fp-vp-768x1024-editing.png) |
| `390×844` Mobile (+ touch) | `0` | `True` | `True` | [fp-vp-390x844-editing.png](images/fp-vp-390x844-editing.png); touch `opacityBeforeTap="0" → opacityAfterRowSelect="1"`, mở editor thành công qua tap |
| `360×800` Mobile nhỏ | `0` | `True` | `True` | [fp-vp-360x800-editing.png](images/fp-vp-360x800-editing.png) |
| `320×568` Siêu hẹp | `0` | `True` | `True` | [fp-vp-320x568-editing.png](images/fp-vp-320x568-editing.png) |

> **Lưu ý trung thực:** Thiết bị di động iOS/Android vật lý thật giữ trạng thái **`PHYSICAL_MOBILE = NOT_VERIFIED`**; chỉ mô phỏng trong Chromium headless.

---

## 11. Ownership Audit

- Toàn bộ `77` file/hunk `OWNERSHIP_BLOCKED` từ phiên song song còn nguyên vẹn 100%, không stage, không commit, không checkout/restore.
- Root repo `D:/Documents/projects/algo-sim` (`axo-ui-consistency`) hoàn toàn nguyên vẹn.
- Commit chỉ dùng `git add <từng file cụ thể>` và kiểm tra `git diff --cached --name-only` trước khi commit cục bộ. Không lưu file `.webm` vào repo.

---

## 12. Những Vấn Đề Còn Tồn Tại (Phân Loại Trung Thực)

1. **`EXPECTED_EXCEPTION` — Frozen candidate `88ff25730` hash drift (14 test: 13 trong `tests/geometry` + 1 trong `test_evaluation_candidate.py`):** `measured_system.tree_hash` hiện là `9a2cc013...` (`109` file) so với mốc đóng băng `88ff25730` (`b1a8d439...`, `106` file). Không chạm manifest đóng băng vì đây là thay đổi sản phẩm hợp pháp sau mốc candidate.
2. **`BLOCKED_OWNERSHIP` — `CODE_INDEX.md` 4 stale Classroom paths (dòng 4612–4653):** `LiveClassDock.tsx`, `LiveClassStrip.tsx`, `MonitorView.tsx`, `classroom-sync.ts` đã bị phiên song song xóa (`f8a2c41d9e05`), gây exit `1` ở `audit_docs_information_architecture.py` và `test_inv_08_code_index_paths_exist`.
3. **`BLOCKED_OWNERSHIP` — Migration PostgreSQL Alembic cho `step_edit_*`:** Khóa head hiện ở `f8a2c41d9e05` trong `test_postgres_axo_history_migration.py`. Patch migration độc lập đã cung cấp tại mục 6; bản Dev/Test hiện dùng SQLite `ensure_step_edit_tables()`.
4. **`PRE_EXISTING`:**
   - `test_curriculum_coverage.py::test_KHONG_co_mat_cong...`: kiểm thử tài liệu cũ chưa cập nhật sau khi `kernel.py` bổ sung khối cong `sphere`.
   - `frontend/scripts/audit-layout.mjs --port 3001`: kịch bản cũ vào `/` tìm `.nav-link` `"Trang chủ"` trong khi Landing Page mới đang gắn ở `/`.
   - `touchMode.pencilVisibleOnActiveRow` trong Playwright DOM metric `isVisible()` báo `false` tại tích tắc kiểm tra dù `opacityAfterRowSelect === "1"` và tap trực tiếp mở được `<textarea>` (`editorOpenedViaTap === true`).
5. **`OUT_OF_SCOPE` / `NOT_VERIFIED`:** `18` bước hình cong / readout / tên trơn trong 22 mẫu giữ fail-closed; Model 2 **`MODEL_NOT_TRAINED`**; multi-worker Uvicorn / Postgres production deployment chưa kiểm chứng; thiết bị mobile vật lý **`NOT_VERIFIED`**.

---

## 13. Đánh Giá Merge Readiness

Mọi yêu cầu kỹ thuật cốt lõi trong phạm vi Step Editor trên kiến trúc Hybrid `/4` + đơn worker hiện hành đều đã đạt: đột biến hình học thật & kiểm chứng invariant toàn cục (`FP-1`..`FP-3`), rebind Hybrid (`FP-4`), đồng hồ `committed_version` (`FP-5`), hủy in-flight / supersede / DB fault isolation (`FP-6`), đồng bộ UI & reload `F5` trên host sống, responsive 8 viewport, zero ownership conflict. **Đủ điều kiện đề xuất Owner xem xét quyết định merge** (lưu ý chạy thêm patch Alembic mục 6 khi tích hợp cùng nhánh migration PostgreSQL của phiên song song).

---

## 14. Hướng Dẫn Owner Nghiệm Thu Trên Host Sống

Hai dịch vụ nền hiện đang giữ sống phục vụ Owner kiểm tra trực tiếp:
- **Frontend Vite:** `http://localhost:3001` (`/`, `/gioi-thieu`, `/app`, `/simulation/chop-thiet-dien-ba-diem`, `/simulation/chop-mat-cau-ngoai-tiep`, `/simulation/khoang-cach-hai-duong-cheo-nhau`, `/simulation/lang-tru-tam-giac-thiet-dien`)
- **Backend FastAPI:** `http://127.0.0.1:8000` (`http://127.0.0.1:8000/api/health → 200`)

Kịch bản nghiệm thu nhanh (5 bước):
1. Mở `http://localhost:3001/simulation/chop-mat-cau-ngoai-tiep`, di chuột lên bước 8 `(α)` (height giữ nguyên `56.875px`, chỉ hiện bút chì khi hover), bấm sửa thành `"Dựng mặt phẳng trung trực của AB."` → thấy commit `200`, `before_after_diff.changed = false`.
2. Mở `http://localhost:3001/simulation/chop-thiet-dien-ba-diem`, sửa bước 6 (`M`) thành `"Lấy điểm M thuộc SA sao cho SM/SA = 1/4"` → quan sát điểm `M` di chuyển lên `3/4` chiều cao (`z = 9/2`), sau đó nhấn `F5` reload: nội dung `SM/SA = 1/4` vẫn còn nguyên.
3. Mở `http://localhost:3001/simulation/khoang-cach-hai-duong-cheo-nhau`, sửa bước `P` thành `"Lấy điểm P thuộc BD sao cho BP/BD = 1/5"` → hệ thống từ chối `422` (`DOWNSTREAM_ORTHOGONALITY_BROKEN`), giữ draft & hình 3D sạch.
4. Trong Network DevTools bật Throttling `Slow 3G`, bấm `Chạy` một câu hợp lệ rồi bấm `Hủy` ngay khi đang xoay → kiểm tra Network có `POST /api/simulation/steps/cancel` (`200`), nhấn `F5` xác nhận thay đổi bị hủy không lưu.
5. Kiểm tra `/` và `/gioi-thieu` hiển thị Landing Page bình thường.

---

## 15. Danh Sách File Đã Sửa & Commit Allowlist

Các file nằm trong commit allowlist trên `feat/axo-geometry-library-verification`:
- `backend/app/simulation/geometry_functions/step_editor.py`
- `backend/app/simulation/step_edit_router.py`
- `backend/tests/geometry/test_step_editor_final_premerge.py`
- `frontend/src/simulations/domains/geometry/scene3d-model.ts`
- `frontend/src/state/construction-step-edits.ts`
- `frontend/src/components/construction-step-editor.test.tsx`
- `docs/CODE_INDEX.md`
- `docs/evaluation/geometry/runs/step-editor-final-premerge/run.json`
- `docs/evaluation/geometry/runs/step-editor-final-premerge/report.md`
- `docs/evaluation/geometry/runs/step-editor-final-premerge/AXO-STEP-EDITOR-FINAL-PREMERGE-REPORT.md`
- `docs/evaluation/geometry/runs/step-editor-final-premerge/results/backend-perf-comparison.json`
- `docs/evaluation/geometry/runs/step-editor-final-premerge/results/live-host-qa.json`
- `docs/evaluation/geometry/runs/step-editor-final-premerge/results/rea-mcp-inspection.json`
- `docs/evaluation/geometry/runs/step-editor-final-premerge/images/*.png` (16 ảnh chụp màn hình kiểm chứng)

```text
GEOMETRY_MUTATION = PASS
DOWNSTREAM_REBUILD = PASS
ATOMIC_COMMIT = PASS
MULTIPROCESS_CONCURRENCY = PASS
PERSISTENCE_INTEGRITY = PASS
STEP_EDITOR_UX = PASS
REGRESSION_GATES = PARTIAL
OWNERSHIP = CLEAN
HOST_QA = PASS
MODEL_STATUS = MODEL_NOT_TRAINED
MERGE_READINESS = READY
OWNER_APPROVAL = PENDING_OWNER_REVIEW
```
