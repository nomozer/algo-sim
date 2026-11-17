# FINAL MASTER REPORT — AXO HYBRID /4: STUDENT-READY GEOMETRY SIMULATION & INPUT RELIABILITY (`CACHE_VERSION = 145`)

- **Run ID:** `student-ready-geometry-simulation-input-reliability`
- **Branch:** `feat/local-first-geometry-understanding` (campaign range base `ce280140bf89ad72e8724993f75f98edcce01e55`)
- **Product Commit:** `ac0ea63dd462c92a8736b607764d1df552d29329`
- **Clean Candidate Freeze Commit:** `4c463d154885e99ad9bf07e3898d11c619eb63c4`
- **Measured System Hash:** `8a88dbfe9ddc35e38639c7c81e8c7741b1ea1dd1cd848bc9e7dc6bf16885b0c6` (`120` measured files)
- **Cache Identity:** `CACHE_VERSION = "145"` · `ROUTE_D_CACHE_POLICY = "145:route-d"` · `stable_capability_hash = a2e8131eeeab638f0567b8962317c3d92c9d5a7a0b4ee9e2e74bbcb78d62751a`
- **Bản gốc đối chứng (`v144`):** `real-world-geometry-input-verified-simulation` (product `b806e359fcceb268c065013d5cf7fb2ff278f1c1`, freeze `003104fd5`)

---

## 1. Bảng Điểm Cổng Nghiệm Thu (Gate Scorecard — Trung Thực Tuyệt Đối)

| Cổng / Nhãn Kiểm Chứng | Trạng thái | Bằng chứng & Điều kiện |
| :--- | :--- | :--- |
| **Gate A — Input Reliability & OCR Split Cache** | `PASS` *(Offline)* | `local-ocr-worker/5` (`32`/`512`), `layout-aware-ocr-reconcile/4` (fix `vmmu_r538`, `ext_prt_01`), `glyph_topology 12/12`, `rendered_pos 4/4`, `adv_neg 3/3` blocked (`0` false auto), `real27` span-only `18/27` (`+3` whole-draft tách riêng), `external15` `1` auto + `8/12` conf + `2/6` bands |
| **Gate B — Geometry Understanding & Autonomous Composition** | `PASS` *(Offline)* | `REAL27_TEXT 21/27` (`0` wrong; +`vmmu_r254/r277/r488`), `NC 21/21` NL & Gold (`11/11` neg), `A4 6/6`, `r1_probe 13/13+6/6`, `RM72 61/62+10/10`, `0` continuity errors, `0` wrong served |
| **Gate C — Direct Frontend Ownership Integration** | **`BLOCKED_OWNERSHIP`** | `FRONTEND_INTEGRATION = BLOCKED_OWNERSHIP`. `git diff ce280140b..4c463d154 -- frontend/` trống `100%`; `4` patch trong `handoff/` kiểm `git apply --check` đạt `rc=0`. |
| **Gate D — Automated 4-Viewport Browser E2E** | `PASS` *(AUTOMATED_BROWSER_NOT_HUMAN_STUDY)* | `browser_e2e_4viewports.json`: `1920×1080`, `1366×768`, `768×1024`, `390×844` đều `PASS` (`0` console/page/request errors), `multi_problem_sheet_1366x768.pass = true`, `camera_orbit_1920x1080.changed = true`, `live_provider_calls = 0` trên `frontend/dist` chưa sửa |
| **Gate E — Evaluation Candidate Freeze & Cache Lock** | `PASS` | `freeze_evaluation_candidate.py --verify` (`MATCH`), `lock_cache_identity.py --verify` (`MATCH`, `145:route-d`), `locked_surfaces.all_match = true`, `hygiene_and_cache_145.passed = true` |
| **Gate F — Replay / Crash / Preview Fixtures** | `PASS` | `replay_demo_cases.py` (`5/5` + reduced `1/1`), `audit_demo_crash_surface.py` (`6/6`), `export_hybrid_preview_fixtures.py --verify` (`41` verified, `0` problems) |
| **Gate G — Full Clean-Tree Backend `pytest` & Publication Safety** | `PENDING_EXECUTION_ON_CLEAN_TREE` | Sẽ chạy đầy đủ sau khi commit bộ deliverables/docs và xác nhận cây sạch |
| **K-1 / S-2 / R-1 Pending Owner Decisions** | **`PENDING_OWNER_DECISION`** | `pending_template_refresh.json`: `K-1/S-2/R-1` gắn `8a88dbfe9ddc...`, `paid_project_confirmed: false` |
| **Các Giới Hạn Không Đo Trong Chiến Dịch** | `NOT_MEASURED` | `INDEPENDENT_H1_VALIDATION = NOT_MEASURED` · `INDEPENDENT_GENERALIZATION = NOT_MEASURED` · `REAL_STUDENT_USABILITY = NOT_MEASURED` · `PHYSICAL_LOW_END = NOT_MEASURED` · `live_gemini_vision = NOT_MEASURED` · `PUBLICATION_HEAD = BLOCKED_PENDING_OWNER_REVIEW` |

---

## 2. Chỉ Số Bắt Buộc `v145` So Với Baseline `v144`

| Chỉ số | Baseline `v144` (`b806e359f`) | Hiện tại `v145` (`ac0ea63dd` / `4c463d154`) | Ghi chú |
| :--- | :--- | :--- | :--- |
| `TEXT_TO_SCENE3D` trên `REAL27` | `18/27` (`0` wrong) | **`21/27`** (`0` wrong) | Thăng hạng `vmmu_r254` (`9a³√13/2`), `r277` (`8a³`), `r488` (`a³/3`); `6` ca còn lại từ chối đúng |
| `SPAN_ONLY_SCENE3D_SUCCESS_RATE` (`real27`) | `13/27` | **`18/27`** (`0` wrong) | Phát triển `2/6`, đóng băng `14/19`, tươi `2/2` |
| `whole_draft_fallback_served` (`real27`, tách riêng) | `+5` | **`+3`** (`r254`, `r284`, `r488`) | Tách khỏi span-only do cần sửa tự do ngoài span gắn cờ |
| `AUTO_ACCEPT` đúng / sai (`real27`) | `0/27` (`0` wrong) | `0/27` (`0` wrong) | Bảo toàn bất biến an toàn |
| `external15_printed` (auto / span conf / bands / wdf) | `1/15` + `9/15` + `2/6` (`0` wdf) | `1/15` (`ext_prt_01`) + `8/12` conf + `2/6` bands (`0` wdf, `0` wrong) | Fix `ext_prt_01` khôi phục `LOCAL_OCR_ACCEPT` (`a³√3/3`, `a√21/21`) |
| `real27` CER median & Critical Facts | `0.0944 -> 0.0533` | `0.0944 -> 0.0553`, facts `176/188 -> 187/188` (`0.9947`) | Thiếu duy nhất `AA'=2√13a` trên `r254`; effort median `2` actions / `0` chars typed (`42/6098`) |
| `NC NL` (`21`) & `NC Gold` (`21`) & `Neg` (`11`) | `NC NL 4/21` trước chiến dịch | **`21/21` NL**, `21/21` Gold, **`11/11` neg (`0` false)** | NL p50/p95: `47.6 / 100.852 ms` |
| `RM72` (`62` pos + `10` neg) | — | **`61/62` pos + `10/10` neg (`0` false)** | `33` EXPLICIT, `25` REGISTERED, `3` DISCOVERED, `8` reuse, `MG9` -> `IR_MEMORY_BUDGET_EXCEEDED` |
| `COMP112` / `DEV37` / `PROBES39` | `66/112` / `DEV37` / `PROBES39` | `68/112` / `30/37` / `23/39` | Tăng `66 -> 68` là 2 ca dương hợp lệ (`dp_reflection -> a√2/2`, `dp_projection_unnamed_image -> a√6/3`) gắn nhãn âm lịch sử |
| `Scene3D Continuity Errors` & `wrong_scene_served` | `0` / `0` | **`0` / `0`** | Tuyệt đối không phục vụ Scene3D đứt gãy hay sai đáp án |
| `Mode A Trig Policy` & `Learner Machine Leaks` | Compliant | **`true` / `0` leaks** | `mode_a_answers_dict = {"q1": "cos²=1/2"}` |

Chi tiết từng mảng xem thêm tại:
- [INPUT_RELIABILITY_IMPLEMENTATION.md](./INPUT_RELIABILITY_IMPLEMENTATION.md)
- [STUDENT_FRONTEND_INTEGRATION.md](./STUDENT_FRONTEND_INTEGRATION.md)
- [GEOMETRY_CAPABILITY_REPORT.md](./GEOMETRY_CAPABILITY_REPORT.md)

---

## 3. Khoá Bề Mặt Gemini (Không Đổi Trên Bất Kỳ Hash Nào)

| Surface | SHA-256 Expected & Observed (`all_match = true`) |
| :--- | :--- |
| `function_calling` | `7ea511a6e3828c9adcc8402aa2d7d6b1d433e67a01ec4329c3009c46af652b25` |
| `fact_extraction_flat` | `485d3834db8b18cfdb24143bfbb14deb8f5b7a9d74cb612d48db8c08252e507a` |
| `fact_extraction_v3` | `4bff35bbf690a9973b2b7834019b908d507bbbb4277928e36d12dcff657e226f` |
| `typed_fact_next` | `33197a45e0620d94a669047b47907479d1e7f07b1dc76e7c6abd75ada7a6df14` |

---

## 4. Tập Mù `frozen_unseen_vmmu20` (Tách Biệt Tuyệt Đối)

- `ground_truth_status = "GROUND_TRUTH_UNVERIFIED"` · `independent_ground_truth_validation = "NOT_MEASURED"`.
- `19` ảnh từ `frozen_unseen_vmmu20_manifest.json` (`13` `polyhedron_3d`, `6` `curved_or_mixed_solid`): `18` `needs_confirmation` (`LOCAL_OCR_REVIEW_REQUIRED`), `1` `ready` (`LOCAL_OCR_ACCEPT`, `unseen_vmmu_13`, từ chối `LIVE_AI_DISABLED` ở hạ nguồn), tuyến nháp đạt `2 SERVED / 17 REFUSED`, `0` lỗi continuity, cold prepare `p50 = 2636.49 / p95 = 3430.40 ms`, warm `226.36 / 441.96 ms`. Không tính vào mọi mẫu số độ chính xác.

---

## 5. Danh Mục Hiện Vật Đồng Bộ (`run.json`)

Bảng băm đầy đủ (kích thước bytes + SHA-256) của toàn bộ hiện vật trong thư mục run này được tạo và kiểm xác thực trong [`run.json`](./run.json).
