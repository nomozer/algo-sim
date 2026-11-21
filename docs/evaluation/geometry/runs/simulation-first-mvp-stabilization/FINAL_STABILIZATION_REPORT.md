# FINAL_STABILIZATION_REPORT — Ổn Định Nền Tảng Mô Phỏng 3D & Sẵn Sàng Pilot Nội Bộ (`simulation-first-mvp-stabilization`)

- **Run ID:** `simulation-first-mvp-stabilization`
- **Nhánh / Worktree:** `feat/local-first-geometry-understanding` (`D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding`)
- **Mốc ban đầu (`start_head`):** `9f8fc53e6b9269ec4ff0d7197096ef470e4c8532`
- **Product commit:** `4d81be4b85e164c8596d2e9b53351b5df0a244f0` (`fix(geometry): restore undotted primed prism Scene3D topology and witnesses, cache 141`)
- **Candidate freeze commit:** `077e3671ac2fdaa4cb9ddb584a583e92667cda21` (`measured_system`: `120` file, SHA-256 `beb18ce56298f1022f628fd923dffd98c0134b2d1ffd9cbc5b87efa280a408b3`, `CACHE_VERSION = "141"`, `semantic_environment_hash = "6233c43c395c9b493d31d3dbb5d0ca952604730f6185cf541d2f179c077f955b"`)
- **Môi trường kiểm chứng:** `ALLOW_LIVE_AI = 0`, `GEMINI_API_KEY = ""`, `HYBRID_ROUTE_MODE = local-first` (trong Playwright E2E) / mặc định `live` (trong pytest hợp đồng), **`0` lượt gọi AI live**.

---

## 1. Định Vị Sản Phẩm Cốt Lõi (Không Lệch Hướng)

Axo là **hệ thống mô phỏng hình học không gian 3D có kiểm chứng toán học**, giúp học sinh trực quan hóa các đối tượng, quan hệ hình học và tiến trình dựng từng bước — **không phải** hệ thống giải bài tập tự động, viết lời giải đại số hay cung cấp máy chọn trắc nghiệm `A/B/C/D`.

Toàn bộ wave này bảo toàn nguyên vẹn `output-policy/1` và **Chế độ A (`dapAnAn`)**: đáp số cuối (`FINAL_RESULT` / `route_d.answers`) được ẩn khỏi canvas 3D, thẻ soi đối tượng và danh sách bước dựng, trong khi các đối tượng nhân chứng dựng hình (`witnessesShown`, `angleConstructionsAt`, `altitudeConstructionsAt`) và thuyết minh sư phạm tiếng Việt vẫn hiển thị đầy đủ để học sinh quan sát cách dựng.

---

## 2. Kết Quả 5 Cổng Kiểm Chứng (`Phase A`–`Phase E`)

### 2.1 Phase A — Kiểm Toán Sự Thật Toán Học (`MATH_TRUTH_AUDIT.md`)
Báo cáo chi tiết: [`MATH_TRUTH_AUDIT.md`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/simulation-first-mvp-stabilization/MATH_TRUTH_AUDIT.md)

1. **Nguyên nhân gốc rễ các sai khác A2 (`vmmu_r537`, `vmmu_r460`, `vmmu_r463`):** **100% là lỗi chép tóm tắt văn xuôi (prose-summary transcription errors)** trong báo cáo markdown của wave trước (`AXO_DIMENSION_AWARE_VERIFIED_CONSTRUCTION_REPORT.md`, các dòng **`34`, `205`, `214`, `215`**); **0 lỗi** trong Parser, Source Gate, Planner, Exact Kernel hay kho dữ kiện JSON (`r537_development_regression.json`, `r460_development_regression.json`, `r463_development_regression.json` đều chính xác nguyên văn với ảnh gốc VMMU).
2. **Đối chiếu kết quả Exact Kernel & phản thực:**
   - `vmmu_r537`: `a√6/3` (Key C — khớp chứng minh độc lập). Biến thể tóm tắt sai A2 bị parser từ chối an toàn (`LOCAL_PARSE_AMBIGUOUS`), không bịa dữ kiện.
   - `vmmu_r460`: `a³√2/3` (Key C — khớp `△ABC` vuông cân ở `B`, `△SAB` cân ở `A`). Biến thể phản thực `∠(SB,(ABC))=60°` trả đúng `'a³√6/3'`.
   - `vmmu_r463`: `4a³√3` (Key D — khớp thoi `60°`, `AA'=2a`, `30°`). Biến thể phản thực `AB=2a, ∠BAD=120°, 60°` trả đúng `'12a³'`.
3. **Correction Layer (`AGENTS.md` §4):** Không sửa bất kỳ byte nào của báo cáo cũ; đăng ký chuỗi `CORRECTS` / `CORRECTED_BY` hai chiều trong [`docs/EVIDENCE_INDEX.md`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/EVIDENCE_INDEX.md).
4. **Kiến trúc `route_d.scene_configuration = None`:** Chỉ khác `None` khi mô hình không xác định duy nhất (`unique = false`). Cả `r537`, `r460`, `r463` đều duy nhất đến phép vị tự theo đơn vị ký hiệu `a`, nên `scene_configuration = None` là đúng thiết kế.

### 2.2 Phase B — Sửa Lỗi Lăng Trụ Không Dấu Chấm & Kiểm Toán Mô Phỏng (`SIMULATION_INTEGRITY_REPORT.md`)
Báo cáo chi tiết: [`SIMULATION_INTEGRITY_REPORT.md`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/simulation-first-mvp-stabilization/SIMULATION_INTEGRITY_REPORT.md)

1. **Sửa lỗi P1 tại [`engine.py::hop_dong_to_po_da_khai`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/app/simulation/geometry_functions/engine.py#L351-L397):** Áp dụng cùng quy tắc đóng với `registry._tach_lang_tru_lien` cho ký hiệu lăng trụ viết liền không dấu chấm (`ABCDA'B'C'D'`, 3–6 đỉnh đáy, không giữ `ENGINE_VERSION` đổi), giúp `vmmu_r463` phục hồi từ **10 đối tượng / 3 bước / `0` `perpendicular_witness`** lên **16 đối tượng** (`day_ABCD`, `day_A_primeB_primeC_primeD_prime`, `canh_ben_A_A_prime..D_D_prime`, `khoi_...`, `kq_q1`), **4 `ENGINE_VERIFIED` `perpendicular_witness`**, **6 bước dựng nhân quả**, khớp **từng byte** với `ABCD.A'B'C'D'`.
2. **Nâng `CACHE_VERSION` (`140 -> 141`) & Khoá danh tính:** Đã cập nhật [`backend/app/main.py`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/app/main.py#L934-L938), tạo lại [`backend/cache_identity.lock.json`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/cache_identity.lock.json), và khóa bởi bài test hồi quy mới [`test_undotted_prism_scene3d_topology.py`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/tests/geometry/test_undotted_prism_scene3d_topology.py) (xác nhận hàng cache `140:route-d` cũ bị vô hiệu hóa MISS sạch sẽ).
3. **Tính liên tục & nhân chứng trên toàn bộ 9 họ hình + 2 cấu hình minh họa:** **`11/11` ca đạt `0` lỗi continuity** qua `validate_construction_continuity(scene3d, trace=...)` và **`0` phụ thuộc sớm**. Trên thiết diện phương pháp vết `(MAB)` / `(MNP)`, backend phát đúng `auxiliary_points` và thuyết minh `COPLANAR_TRACE_INTERSECTION` (*"gọi I là giao điểm..."*).

### 2.3 Phase C — Đối Chiếu Handoff Frontend (`FRONTEND_HANDOFF_STATUS.md`)
Báo cáo chi tiết: [`FRONTEND_HANDOFF_STATUS.md`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/simulation-first-mvp-stabilization/FRONTEND_HANDOFF_STATUS.md)

- Kiểm tra chỉ đọc trên worktree `D:/Documents/projects/axo-geometry-library` (nhánh `feat/axo-geometry-library-verification`, `HEAD = 1bfc2bc361c2a887e5d826996e365154cb09c41d`, đang có `77` thay đổi làm việc dở dang của phiên Frontend — **`0` tệp bị sửa trong phiên này**).
- **`FE-2`**: `BLOCKED_OWNERSHIP` (đã xác nhận patch `fe2-multi-layer-aux-readout-ids.diff` áp thử khô `git apply --check` trả `rc = 0`).
- **`FE-3`**: `BLOCKED_OWNERSHIP + BLOCKED_DEPENDENCY` (chờ năng lực mặt cầu ngoại tiếp `GEO-BE-V9415-003`).
- **`FE-4`**: `BLOCKED_OWNERSHIP` (backend đã phát `auxiliary_points`, `frontend/src/` hiện chưa render chấm 3D ngoài miền trên canvas).
- **`FE-6`**: `BLOCKED_OWNERSHIP` (`MERGE_NOTE` dùng bản `axo-geometry-library` kèm áp patch `FE-2` khi merge).

### 2.4 Phase D & E3 — Kiểm Chứng Chromium Thật & Hành Trình Học Sinh (`STUDENT_PILOT_E2E.json`)
Biên bản máy: [`STUDENT_PILOT_E2E.json`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/simulation-first-mvp-stabilization/STUDENT_PILOT_E2E.json) (kịch bản [`student_pilot_e2e.mjs`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/simulation-first-mvp-stabilization/tools/student_pilot_e2e.mjs))

- **Môi trường:** `frontend/dist` + loopback `uvicorn` (`HYBRID_ROUTE_MODE=local-first`, `ALLOW_LIVE_AI=0`, `0` VLM/LLM live calls), dọn sạch tệp tạm sau khi chạy (`temp_files_cleaned_up = true`).
- **`D1` (14 bước hành trình học sinh đầy đủ tại `1920x1080`):** **PASS** — Light Mode (`BODY rgb(246, 245, 244)`, luminance `0.961`), nhập đề `r537`, xoay/thu-phóng/kéo/đặt-lại camera, chọn điểm (`kq_q1__foot1`) / cạnh (`kq_q1__perp_seg`) / mặt (`mp_q1`) xác nhận `#ctx-obj-title` & `#dock-prob-statement` không token máy, duyệt timeline `6/6` bước (`0` phụ thuộc sớm), bật/tắt `#chk-aux`, `#chk-axes`, `#chk-grid`, `#btn-xray`, chuyển sang `r463` lăng trụ viết liền (`16` đối tượng, `4` `ENGINE_VERIFIED` `perpendicular_witness`, `0` đối tượng ngoại lai, `0` chữ thừa), và xác nhận thiết diện vết `(MNP)` hiện `.geo3d-cac-buoc-vi-sao` (*"Giao tuyến trên từng mặt..."*).
- **`D2` (OCR ảnh & tách trang nhiều bài tại `1366x768`, `0` VLM calls):** **PASS** — Ảnh đề thi `r537` (định dạng JPEG) đi qua `/api/input/prepare` → `needs_confirmation`, giữ nguyên `'a²'`, dựng `Scene3D` (`a√6/3` ẩn trên UI). Trang 2 bài xếp chồng đi qua `needs_selection` (`2` ứng viên) → chọn bài 1 → `ready`, `0` rò rỉ nội dung bài 2 (`MNPQ`), dựng `Scene3D` (`8a³/3` ẩn trên UI).
- **`D3` (Responsive 4 viewport `1920x1080`, `1366x768`, `768x1024`, `390x844`):** **4/4 PASS** (`12/12` bước chuyển đề liên tiếp sạch, canvas không cắt xén, toolbar phủ `<= 3.7%`, nút bước `>= 40px` trên mobile, `horizontal_overflow_px = 0`, `0` lỗi `pageerror`).
- **`D4` (Trung thực phân loại từ chối tại `1366x768`):** **3/3 PASS** — `cap_oblique_triangle` và `cap_non_special_70deg` trả `unsupported` / `capability_gap` / `EXACT_DOMAIN_EXCEEDED` với Toast tiếng Việt rõ ràng (*"Axo chưa hỗ trợ phép dựng này"*), `0` canvas, `0` token máy, **không bao giờ nói thiếu dữ kiện hay khuyên sửa giả thiết**; `true_missing_dimension` trả `insufficient_specification` / `AMBIGUOUS_FACT`.
- **`D5` (Không biến thành Solver / Không lộ đáp án):** **16/16 lượt kiểm tra PASS** (`0` rò rỉ đáp án ngoài đề bài, `0` UI chọn `A/B/C/D`).
- **`E3` (Đo độ trễ trên host SwiftShader — `INCONCLUSIVE_SHARED_HOST_SWIFTSHADER`, `PHYSICAL_LOW_END_NOT_MEASURED`):** `first_model_ms` trung vị `381` ms (`n=17`, min `245`, max `4903` gồm cả OCR hai lượt), `orbit_ms` trung vị `299.4` ms (`n=5`), `timeline_next_ms` trung vị `123.95` ms (`n=68`).

---

## 3. Tổng Hợp 8 KPI Simulation-First & Kiểm Thử Hồi Quy (`REGRESSION_SUMMARY.json`)

Biên bản máy đầy đủ: [`REGRESSION_SUMMARY.json`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/simulation-first-mvp-stabilization/REGRESSION_SUMMARY.json)

### 3.1 8 KPI Simulation-First Chính Thức
| KPI | Giá trị đo được | Trạng thái |
|---|---|---|
| `VERIFIED_3D_MODEL_RATE` | `11/11 (100.0%)` (Phase B) · `3/3 (100.0%)` (VMMU audit) · `14/14 (100.0%)` (Chromium E2E) | **PASS** |
| `OBJECT_RELATION_COVERAGE` | `16/16` đối tượng & `4/4` `ENGINE_VERIFIED` `perpendicular_witness` trên `ABCDA'B'C'D'` (`r463`) | **PASS** |
| `AUXILIARY_CONSTRUCTION_COMPLETENESS` | `trace_holds=true`, `auxiliary_points` có mặt, `#chk-aux` bật/tắt khôi phục chuẩn trong Chromium | **PASS** |
| `TIMELINE_CONTINUITY_PASS_RATE` | `11/11` (Phase B) & `100.0%` Chromium E2E (`0` phụ thuộc sớm) | **PASS** |
| `PEDAGOGICAL_EXPLANATION_COVERAGE` | `100.0%` (`6/6` bước `r537`, `4/4` `r463`, `.geo3d-cac-buoc-vi-sao` trên `(MNP)`, `0` token máy) | **PASS** |
| `STUDENT_JOURNEY_E2E_PASS_RATE` | `D1` `PASS` · `D2` `PASS` (`0` VLM) · `D3` `4/4` viewport · `D5` `16/16` sạch spoiler · Light Mode `PASS` | **PASS** |
| `TAXONOMY_REFUSAL_HONESTY_RATE` | `3/3 (100.0%)` trong Chromium + test xác định (`0` gán nhầm `capability_gap`, `0` token máy) | **PASS** |
| `STUDENT_PERCEIVED_LATENCY_MS` | `first_model_ms` median `381` ms · `orbit_ms` median `299.4` ms · `timeline_next_ms` median `123.95` ms | **`INCONCLUSIVE_SHARED_HOST_SWIFTSHADER`** |

- **Chỉ số kiểm chứng phụ (`INTERNAL_MATHEMATICAL_TRUTH_AUDIT_ONLY`):** `SERVED_MATCHES_DATASET_KEY = 3/3 (100.0%)` trên nhóm VMMU được phục vụ (`r537 -> C: a√6/3`, `r460 -> C: a³√2/3`, `r463 -> D: 4a³√3`), luôn ẩn khỏi màn hình học sinh theo `output-policy/1`.

### 3.2 Kết Quả Hồi Quy Toàn Repo (`11/11` Cổng Offline Đạt)
| Cổng kiểm | Lệnh & Phạm vi | Kết quả thực tế |
|---|---|---|
| `backend_pytest` | `pytest -c backend/pytest.ini backend/tests -q` (`ALLOW_LIVE_AI=0`) | **PASS** — **`14,829 passed`**, `7 skipped`, `3 deselected`, `17 xfailed`, **`0 failed`** (`613.7s`) |
| `frontend_test_wave` | `npm.cmd run test:wave` (`vitest run && tsc -b && vite build`) | **PASS** — **`142` file / `2,062 tests passed`**, `0` lỗi TS, build `3.47s` |
| `demo_replay` | `backend/scripts/replay_demo_cases.py --json` | **PASS** — `5/5`, `REDUCED_CHAIN_CASES = 1/1` |
| `crash_audit` | `backend/scripts/audit_demo_crash_surface.py --json` | **PASS** — `6/6`, `uncaught = 0` |
| `hybrid_preview_fixtures` | `export_hybrid_preview_fixtures.py --verify .../fixtures-dimension-aware` | **PASS** — exit `0` |
| `docs_ia` | `audit_docs_information_architecture.py --json` | **PASS** — `broken_links = 0`, `stale_code_index_paths = 0`, `secret_leaks = 0` |
| `publication_range` | `check_publication_safety.py --range 9f8fc53e6b9269ec4ff0d7197096ef470e4c8532..HEAD` | **PASS** — `scanned=34, messages=2, violations=0` |
| `publication_head` | `check_publication_safety.py --head` | `violations=97, pending_exception=97` (`0` vi phạm mới; giữ nguyên `BLOCKED_PENDING_OWNER_REVIEW`) |
| `freeze_verify` | `freeze_evaluation_candidate.py --verify` | **PASS** — khớp `120` file (`beb18ce56298f102…`) |
| `cache_lock_verify` | `lock_cache_identity.py --verify` | **PASS** — `CACHE_VERSION 141`, môi trường `6233c43c395c9b49…` |
| `zero_hardcode_scan` | Quét `backend/app` + `frontend/src` (`198` file sản phẩm) | **PASS** — `0` vết hardcode `vmmu_/r537/r460/r463/r266/r411` |

---

## 4. Bốn Phán Quyết Chính Thức Tách Biệt (Không Gộp Chung)

1. **`PRODUCT_TECHNICAL_VERDICT = PASS`** — Mã sản phẩm sạch (`0` hardcode, `14,829` backend pytest & `2,062` frontend vitest đạt, `Scene3D` lăng trụ viết liền khôi phục hoàn chỉnh lên `16` đối tượng + `4` chứng chỉ vuông góc với `CACHE_VERSION = 141`, `0` lỗi toán học khi đối chiếu VMMU gốc).
2. **`SIMULATION_READINESS = READY_WITHIN_SUPPORTED_SCOPE`** — Sẵn sàng về mặt kỹ thuật mô phỏng trong **9 họ hình đang hỗ trợ** và các cấu hình minh họa có chứng chỉ bất biến, bảo toàn đúng `output-policy/1` (Chế độ A).
3. **`INTERNAL_PILOT_READINESS = READY_FOR_CONTROLLED_INTERNAL_PILOT`** — Sẵn sàng cho **pilot nội bộ có kiểm soát** (có giám sát phạm vi hỗ trợ và đối chiếu xác nhận ảnh khi dùng OCR local).
4. **`FULL_RELEASE_GATE = BLOCKED_GATES_REMAIN`** — **Chưa được phép phát hành rộng rãi / hợp nhất mặc định toàn sản phẩm** vì còn các cổng chưa đóng theo quy tắc trung thực bằng chứng:
   - `INDEPENDENT_H1_VALIDATION = NOT_MEASURED` (tập niêm phong `H-1` chưa đo ở wave này).
   - `REAL_STUDENT_USABILITY = NOT_MEASURED` (chưa thử nghiệm với học sinh thật; Chromium E2E là `AUTOMATED_BROWSER_NOT_HUMAN_STUDY`).
   - `PHYSICAL_LOW_END = PHYSICAL_LOW_END_NOT_MEASURED` (hiệu năng đo trên máy host chia sẻ SwiftShader).
   - Chiến dịch live Gemini `K-1` / `S-2` / `R-1`: vẫn `PENDING_OWNER_DECISION` (`paid_project_confirmed = false`, `0` lượt live được cấp phép).
   - Đồng bộ worktree `D:/Documents/projects/axo-geometry-library` (`FE-2`, `FE-3`, `FE-4`, `FE-6`): `BLOCKED_OWNERSHIP`.
   - Cổng xuất bản lịch sử `--head`: `BLOCKED_PENDING_OWNER_REVIEW` (`97` mục lịch sử có sẵn trước wave).
