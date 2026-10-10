# hybrid-compiler-selection — báo cáo

Trạng thái: **`HYBRID_COMPILER_SELECTION_OFFLINE_EVALUATION_AWAITING_REVIEW`**.

- Nhánh nghiên cứu `feat/text-to-geometry-functions` (local, chưa push, chưa merge).
- **Số lời gọi Gemini thật: 0.**
- `LLM_ONLY` vẫn mặc định.
- ADR kiến trúc đích giữ nguyên; đánh giá này là tài liệu bổ sung.

Mọi kết quả là `foundation_only`: đầu ra "AI" viết tay hoặc sinh cơ học. Không kết quả nào nói về năng lực của Gemini. Không
tuyên bố Hybrid tốt hơn.

## 1. Sản phẩm bàn giao

| # | sản phẩm | tệp |
|---|---|---|
| 1 | so sánh kiến trúc | [`ARCHITECTURE_COMPARISON.md`](ARCHITECTURE_COMPARISON.md) |
| 2 | hợp đồng Typed Facts | [`TYPED_FACTS_CONTRACT.md`](TYPED_FACTS_CONTRACT.md) |
| 3 | bản đồ triển khai planner | [`PLANNER_MAP.md`](PLANNER_MAP.md) §1–§3 |
| 4 | kết quả A/B offline | [`AB_OFFLINE_RESULTS.md`](AB_OFFLINE_RESULTS.md) §1–§3, `offline/ab_results.json` |
| 5 | oracle độc lập | [`AB_OFFLINE_RESULTS.md`](AB_OFFLINE_RESULTS.md) §4, `diagnostics/independent_oracle_check.{py,log}` |
| 6 | đúng ngữ nghĩa và từ chối | [`AB_OFFLINE_RESULTS.md`](AB_OFFLINE_RESULTS.md) §5–§6 |
| 7 | kiểm toán tái sử dụng / trùng lặp | [`PLANNER_MAP.md`](PLANNER_MAP.md) §4–§5 |
| 8 | cập nhật khoảng trống nghiên cứu | [`RESEARCH_GAP_UPDATE.md`](RESEARCH_GAP_UPDATE.md) |
| 9 | giao thức pilot A/B thật (chưa chạy) | [`REAL_MODEL_AB_PROTOCOL.md`](REAL_MODEL_AB_PROTOCOL.md) |
| 10 | git, candidate, test, skills | §4–§6 dưới đây, `run.json`, `handoff.md` |

## 2. Kết luận theo nhãn

| kết luận | nhãn | bằng chứng |
|---|---|---|
| B dựng trên cùng registry / cổng nguồn / engine / IR / kernel / Scene3D; không back end thứ hai; không lùi về `LLM_ONLY` | `VERIFIED` | `PLANNER_MAP.md` §4; `test_khong_lui_ve_llm_only`; guard `test_Y` |
| Parity 58/58 (dữ kiện B sinh cơ học từ lời gọi A) | `VERIFIED` | `test_parity_58_ca_cu`; `diagnostics/ab_offline.log` |
| Holdout 14/14 khớp tiền đăng ký ở cả hai nhánh; 8 phục vụ đúng, 4 từ chối đúng, 2 ngoài năng lực; 0 phục vụ sai, 0 từ chối oan | `VERIFIED` | `offline/ab_results.json` |
| Oracle toạ độ độc lập 28/28; renderer 16/16 cảnh (256 cặp điểm) | `VERIFIED` | `diagnostics/independent_oracle_check.log`, `renderer_metric_check.log` |
| B kiểm điều phải chứng minh và mệnh đề phủ định trên hình; chẩn đoán `FIGURE_NOT_UNIQUE` mà không lấy hình mẫu | `VERIFIED` (cơ chế) | H05, H07, H13; đột biến 10/10 |
| Tự rà soát tìm 2 lỗi của B (phủ định không kiểm được bị phục vụ im lặng; checker coi câu hỏi / `unsupported` là đúng) | `FAILED` → đã sửa `91e2edf9` | test đỏ trước; đột biến m9, m10 |
| Cổng nguồn được **nới** ("lập phương", "chữ nhật") cho cả hai nhánh | khai báo | `AB_OFFLINE_RESULTS.md` §6; `diagnostics/old_cue_probe.log` |
| Lược đồ B ngắn hơn A khoảng 6,6 lần theo ký tự (2 999 so với 19 816) | `VERIFIED` (ký tự) | `diagnostics/responsibility_and_surface.log` |
| Token thật của mỗi nhánh | `NOT_MEASURED` | |
| B giảm lỗi chọn hàm / tăng lỗi trích (H-AB1); kiêng trả lời tốt hơn (H-AB2); ít token ra hơn (H-AB3) | `HYPOTHESIS` | `RESEARCH_GAP_UPDATE.md` §5; `REAL_MODEL_AB_PROTOCOL.md` |
| Hybrid là kiến trúc tốt hơn | `NOT_VERIFIED` — không tuyên bố | |
| Đổi kiến trúc đích, đổi mặc định, xoá `LLM_ONLY`, gọi API có phí | `OUT_OF_SCOPE` | |

Đọc kết quả: **khi AI trích đúng**, hai nhánh cho cùng kết cục trên 72 ca. Khác biệt nằm ở **ai chịu trách nhiệm** quyết định
nào: trên 14 ca, B chuyển 51 quyết định từ mô hình sang planner. B cũng **chẩn đoán** tốt hơn ở ba chỗ (H05, H08, H13) và kiểm
được mục tiêu (H07). Câu hỏi còn mở là mô hình thật trích dữ kiện (B) hay chọn hàm (A) ít sai hơn. Offline không trả lời được
câu đó.

## 3. Khoảng trống nghiên cứu (tóm tắt `RESEARCH_GAP_UPDATE.md`)

- 10 công trình mới H01–H10, đều `VERIFIED_PRIMARY` (PDF gốc). Câu trích phải đối chiếu số trang trước khi đưa vào khoá luận.
- So sánh có kiểm soát "LLM trích dữ kiện + bộ giải" với "LLM viết chương trình" chỉ có **ngoài hình học** (SatLM,
  He-Yueya et al.). Kết quả phụ thuộc loại bài.
- Trong tập đọc, chưa có A/B nào cho **dựng hình**, và chưa có công trình nào từ chối có lý do khi đề hình không gian thiếu
  xác định. Đây là khoảng trống trong tập đọc, **không** phải tuyên bố tính mới.
- Văn liệu GCS (Hoffmann et al. 2001, Jermann et al. 2006) cảnh báo: đếm bậc tự do không chứng minh được tính duy nhất. Vì thế
  B chẩn đoán bằng dựng tường minh, không bằng đếm.

## 4. Test và kiểm tra

| bộ | kết quả |
|---|---|
| `test_hybrid_compiler_selection.py` | 107 passed (đỏ trước khi có planner; 3 test mới của bản sửa đỏ trước khi sửa) |
| `test_ai_function_route.py` + `test_text_to_geometry_functions.py` + `test_structured_geometry_relations.py` (cùng bộ trên) | 278 passed |
| đột biến nhánh B | 10/10 bị bắt |
| oracle toạ độ độc lập | `ORACLE_OK` 28/28 |
| renderer metric (`scene_world_metric_check.ts` qua `veKhongGian`) | `RENDER_METRIC_OK` 16/16 cảnh |
| A/B offline tạo lại sau bản sửa | trùng từng byte |
| candidate + node harness Tier-A | 112 passed; `compiler-scene-replay-lib.node-test.mjs` 88/88 |
| cổng tài liệu | 67/67 |
| full backend suite (worktree detached sạch tại `bf05d397`, sau đóng băng) | **7953 passed, 0 failed**, 1 skipped, 2 deselected (`diagnostics/full_backend_suite_bf05d397.log`) — đo trong worktree vì cây chính có `frontend/public/favicon.svg` chưa theo dõi |

Không chạy vitest / T3: không đổi `frontend/src`, chỉ đổi ghim manifest Tier-A.

## 5. Git và danh tính

| commit | vai trò |
|---|---|
| `f6b1a551` | tiền đăng ký 14 ca holdout + `plan.md` (trước planner) |
| `65fd0328` | nhánh B: planner, adapter dữ kiện, `run_fact_route`, test, bằng chứng offline |
| `6c94a2a8` | đóng băng lại candidate `2c4ea2d2…` (trung gian) |
| `91e2edf9` | bản sửa của tự rà soát (phủ định không kiểm được; checker) + oracle toạ độ |
| `c748c682` | đóng băng lại candidate **`e9d20aa2…`** (110 tệp, worktree detached sạch, `--verify` khớp) |
| (commit tài liệu của run) | báo cáo, sổ trạng thái |

`CACHE_VERSION` giữ 125: B không thuộc bề mặt mô hình có băm của `LLM_ONLY`, và đường mặc định không với tới B (bao đóng import
`test_Y`). Khoá cache `--verify` khớp, môi trường `b1714b56…` không đổi. Không push, không merge. Nhánh pilot
`feat/real-model-pilot-tooling` @ `471a2c79` giữ nguyên. `frontend/public/favicon.svg` chưa theo dõi của người dùng: không
stage, không xoá.

## 6. Skills đã dùng

`superpowers:verification-before-completion` (mọi con số có lệnh và log), `superpowers:test-driven-development` (test holdout và
test bản sửa đỏ trước), `mattpocock-skills:codebase-design` (đặt seam: B đổ vào `{"calls": [...]}` của A, không back end thứ hai),
một tác tử nền (Agent) đọc văn liệu H01–H10.
