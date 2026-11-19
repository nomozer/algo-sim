# Final Master Report — `AXO HYBRID /9`

## Local AI Replacement, Vietnamese NLU Generalization & Offline Production Cutover

- **Run ID:** `axo-hybrid-local-ai-replacement-vietnamese-nlu-offline-cutover`
- **Branch:** `feat/local-first-geometry-understanding` · **Base Commit:** `c73506cb23b0b365d8e475c6b5386a31176a669b`
- **Product Commit:** `f285fcec1afc097084e3fab154f583f01620cab7` (`7` owned backend files modified; `0` edits to `frontend/**`, `registry.py`, `planner.py`, `engine.py`, `backend/experimental/construction_planner/**`, and all 4 locked Gemini modules)
- **Measured System Tree Hash (`123` files):** `a7a6bc4157d02018d5a67e5ee408469f22795385f920444eafc39d4772fa8330` · **`CACHE_VERSION = "145"`** (`145:route-d`)
- **Offline Security Invariant:** `ALLOW_LIVE_AI = "0"`, `GEMINI_API_KEY = ""`, `external_ai_calls = 0`, `gemini_invocations = 0`, `silent_cloud_fallbacks = 0`, `sealed_H1` & `locked_W2_W3` unopened
- **Clean-Tree Freeze & Full Backend Pytest:** *PEND_CLEAN_TREE_PYTEST*
- **Final Verdicts (`Goal A` vs. `Goal B`):**
  - **Goal A (Scoped Local-Only Backend Operation, Opt-In `local-only-scoped` / `offline-lab`):** **`LOCAL_ONLY_SCOPED_RELEASE_READY`** (technical readiness met; default `HYBRID_ROUTE_MODE = "live"` & frontend keyless UX switch remain **`BLOCKED_OWNERSHIP`** pending owner patch application in [`handoff/`](./handoff/))
  - **Goal B (Equivalent General Gemini Replacement):** **`NOT_EQUIVALENT_FULL_REPLACEMENT`** (`local-only-general` gated; cloud VLM OCR blocked `503 LOCAL_ONLY_CLOUD_VISION_DISABLED`; `EXTERNAL_INDEPENDENCE`, `GEMINI_PARITY`, `PHYSICAL_TARGET_HARDWARE`, `INDEPENDENT_H1_VALIDATION`, `REAL_STUDENT_USABILITY` = `NOT_MEASURED`)

---

## 1. Phase-by-Phase Execution Summary (`P0`–`P10`)

| Phase / Gate | Deliverable & Verified Outcome |
|---|---|
| **P0 (`G0`) Baseline & Ownership** | Verified clean start at `c73506cb2`, `CACHE_VERSION = "145"`, locked Gemini surface digests (`typed_fact_next = 33197a45…`, `TypedFactNextPayloadV2 = fc10ddab…`), frozen `/7` `AxoV7` (`36e784d1…`), base `Qwen3-0.6B-Q4_K_M` (`ac2d9771…`), and `AXO CONSTRUCTION /2` (`26c9b505…`). ([`BASELINE_AND_OWNERSHIP_AUDIT.md`](./BASELINE_AND_OWNERSHIP_AUDIT.md)) |
| **P1 (`G1`) C60 Root Cause** | 4-arm Gold intervention (`42` positives): `Arm A (/7) = 13/42 (30.95%)`, `Arm B Gold Raw = 15/42 (35.71%)`, **`Arm B Gold Canon = 33/42 (78.57%)`**, `Arm C Raw = 5/42 (11.90%)`, `Arm C Canon = 18/42 (42.86%)`, all `0` wrong-served. (`9/42` upstream unsolvable even with perfect V2 extraction). ([`SLM_V9_BOTTLENECK_REPORT.md`](./SLM_V9_BOTTLENECK_REPORT.md)) |
| **P2 (`G2`) Deterministic Closure** | Added `slm-verified-normalizer/3` (`VN06`–`VN11`), `local-slm-extractor/4` (`closure_mode="v9"`, tetrahedron `OABC -> O.ABC` fix, 4-goal GBNF cap, `cent` in GBNF, cube edge grounding, `REQUEST_NOT_ANSWERED` incomplete multi-goal guard), and `LOCAL_PARSER_AFTER_V3_NORMALIZER` fast-path. Lifted `AxoV7` on `C60` from `13/42 -> 26/42 (61.90%)` (`23` fast-path + `3` SLM), leaving `13` genuine solvable SLM misses (`7` `C60` + `6` `/7` residuals). ([`DETERMINISTIC_VIETNAMESE_CLOSURE.md`](./DETERMINISTIC_VIETNAMESE_CLOSURE.md)) |
| **P3 (`G3`) Targeted LoRA (`AxoV9`)** | Built disjoint `train_v9.jsonl` (`474`: `386+/88-`) & `val_v9.jsonl` (`126`: `94+/32-`, `0` overlaps vs `565` external items, `max_4gram = 0.3611`). Trained 3 epochs LoRA on `NVIDIA GeForce GTX 1650` (`10,092,544` trainable params, Epoch 3 `val_loss=0.0203`), exported `Qwen3-0.6B-AxoV9-Q4_K_M.gguf` (`396,704,736` B, SHA-256 `73f1484b…`). With GBNF on `val_v9.jsonl`: **`94/94 (100%)` pos + `32/32 (100%)` neg, `0` wrong-served**. On `C60`: **`32/42 (76.19%)`** (`23` fast + `9` SLM = **`96.97%` of `Arm B Gold Canon` ceiling**, `+6` SLM rescues `D09, D11, L19, L21, L24, L30`, `0` wrong-served). ([`SLM_V9_TRAINING_DECISION.md`](./SLM_V9_TRAINING_DECISION.md)) |
| **P4 (`G4`) Runtime Optimization** | Registered `local-slm-runtime/4` (`HYBRID_V9_LOCAL_SLM`, `-b 512 -ub 512`, `max_tokens=256`, fixed `use_cache=True` w/ explicit `runtime`, single-flight coalescing `_V9_INFLIGHT_EVENTS`). **Mixed warm uncached (`n=100`, `50` fast + `50` SLM): `100/100`, `p50 = 1,270.35 ms`, `p95 = 4,109.98 ms <= 5,000 ms`**; pure SLM uncached (`n=100`, `6T`): `p50 = 4,011.93 ms`, `p95 = 5,411.75 ms`, `33.0 tok/s`; warm cached (`n=25`): `p50 = 29.24 ms`; cold start `6,104.96 ms` (`load=970.24 ms`); peak combined WS **`973.28 MiB`**, peak private commit **`637.5 MiB`**. ([`SLM_V9_SYSTEM_RESOURCE_REPORT.md`](./SLM_V9_SYSTEM_RESOURCE_REPORT.md)) |
| **P5 (`G5`) Single-Shot Unseen 150** | Freeze Commit `f285fcec1` -> `--verify-manifest-only` (`0` SLM calls, `0` overlaps across `1,165` ref items) -> single-shot execution: **`SLM_V9_UNSEEN_150 = 94/105 (89.52%, Wilson 95% CI [0.8221, 0.9405])` pos (`54` fast + `40` SLM) + `45/45 (100%, [0.9213, 1.0000])` neg = `139/150 (92.67%, [0.8735, 0.9586])`, `0` wrong-served** (`EXTERNAL17 = 12/12 + 5/5`, `0` wrong-served; `EXTERNAL_INDEPENDENCE = NOT_MEASURED`). ([`SLM_V9_UNSEEN_EVALUATION.json`](./SLM_V9_UNSEEN_EVALUATION.json)) |
| **P6 (`G6`) Gemini Audit** | Audited `9` Gemini surfaces (`11` backend / `4` frontend files): `3` `REPLACE_WITH_LOCAL`, `2` `DISABLE_AS_UNSUPPORTED`, `1` `REPLACE_WITH_DETERMINISTIC`, `2` `RETAIN_CODE_DISABLED`, `1` `OUTSIDE_APPROVED_SCOPE` (`frontend/`). ([`GEMINI_DEPENDENCY_INVENTORY.json`](./GEMINI_DEPENDENCY_INVENTORY.json), [`LOCAL_REPLACEMENT_COVERAGE_REPORT.md`](./LOCAL_REPLACEMENT_COVERAGE_REPORT.md)) |
| **P7–P8 (`G7–G8`) Product & Isolation** | Added `offline-lab`, `local-only-scoped`, gated `local-only-general` (`503 LOCAL_ONLY_GENERAL_NOT_APPROVED` w/o `AXO_ALLOW_GENERAL_LOCAL_CUTOVER=1`), `local-shadow`, keyless `/api/health` readiness, `503 LOCAL_ONLY_CLOUD_VISION_DISABLED`, 10 clean Vietnamese UX states, atomic `active_model.json` `--rollback v7`/`--activate v9`, `3` `git apply --check` `handoff/*.patch`, AST `0` cloud imports, egress guard `0` external calls (`test_api.py 14/14`, `test_local_only_product_and_network_isolation.py 5/5`). ([`LOCAL_ONLY_ROUTING_DESIGN.md`](./LOCAL_ONLY_ROUTING_DESIGN.md), [`OFFLINE_NETWORK_ISOLATION_REPORT.md`](./OFFLINE_NETWORK_ISOLATION_REPORT.md)) |
| **P9 (`G9`) Regressions** | `0` regressions across all 11 baseline suites, `0` Mode A leaks, `0` continuity errors, `0` internal token leaks, `Construction /2` freeze SHA-256 `26c9b505…` (`14` files) intact, `16/16` security/fault checks PASS, net `+14` solved positives across 5 historical SLM suites (`0` wrong-served). ([`SLM_V9_REGRESSION_REPORT.md`](./SLM_V9_REGRESSION_REPORT.md)) |
| **P10 (`G10`) Cutover Decision** | Backend opt-in scoped route **`LOCAL_ONLY_SCOPED_RELEASE_READY`**; default switch, UI integration & Source Gate conversational grammar **`BLOCKED_OWNERSHIP`** (`handoff/*.patch`); full general replacement **`NOT_EQUIVALENT_FULL_REPLACEMENT`**. ([`LOCAL_ONLY_CUTOVER_DECISION.md`](./LOCAL_ONLY_CUTOVER_DECISION.md)) |

---

## 2. Single-Shot `SLM_V9_UNSEEN_150` Per-Group Breakdown (`external_ai_calls = 0`)

| Group | Total | Exact Strict | Rate | Fast-Path | SLM Grounded | Wrong-Served |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `G01_COLLOQUIAL_CONVERSATIONAL` | `12` | `12` | `100.00%` | `6` | `6` | `0` |
| `G02_REORDERED_PREMISES` | `10` | `6` | `60.00%` | `5` | `1` | `0` (`u9_014/020/022` `SOURCE_PREMISE_UNREAD`, `u9_016` `SOURCE_OBJECT_MISMATCH`) |
| `G03_IMPLICIT_BIET_SHAPE_WITHOUT_DAY` | `10` | `5` | `50.00%` | `0` | `5` | `0` (`u9_023/025/027/029/031` `UNGROUNDED_VALUE` on implicit `rect`/`rhom`) |
| `G04_TETRAHEDRON_ORTHO_AND_REGULAR` | `12` | `11` | `91.67%` | `0` | `11` | `0` (`u9_042` `SOURCE_PREMISE_UNREAD`) |
| `G05_PRISM_CUBOID_CUBE` | `12` | `12` | `100.00%` | `4` | `8` | `0` |
| `G06_MULTI_GOAL_2_TO_4` | `14` | `13` | `92.86%` | `4` | `9` | `0` (`u9_062` `REQUEST_NOT_ANSWERED`) |
| `G07_AUXILIARY_MID_CENTROID_PROJ_DIV` | `12` | `12` | `100.00%` | `12` | `0` | `0` |
| `G08_ANGLE_LINE_PLANE_DIHEDRAL` | `12` | `12` | `100.00%` | `12` | `0` | `0` |
| `G09_DISTANCE_PT_PLANE_AND_SKEW` | `11` | `11` | `100.00%` | `11` | `0` | `0` |
| `G10_NEG_MISSING_AND_AMBIGUOUS` | `15` | `15` | `100.00%` | — | — | `0` |
| `G11_NEG_CONTRADICTORY_NEGATED_CONDITIONAL` | `15` | `15` | `100.00%` | — | — | `0` |
| `G12_NEG_OUT_OF_SCOPE_TYPO_INJECTION` | `15` | `15` | `100.00%` | — | — | `0` |
| **Total (`105+ / 45-`)** | **`150`** | **`139`** | **`92.67%`** | **`54`** | **`40`** | **`0`** |

- Positives: **`94 / 105` (`89.52%`)**, Wilson 95% CI **`[0.8221, 0.9405]`**
- Negatives/Adversarials: **`45 / 45` (`100.00%`)**, Wilson 95% CI **`[0.9213, 1.0000]`**
- Overall: **`139 / 150` (`92.67%`)**, Wilson 95% CI **`[0.8735, 0.9586]`**

---

## 3. Explicit Answers to All 28 Mandatory §42 Questions

1. **Bao nhiêu lỗi C60 thực sự do Qwen3-0.6B?**
   Sau khi đóng các lỗ hổng tất định ở P2 (`v9`/`v3`), còn đúng **`7` ca dương `C60`** trượt trực tiếp do extraction của `AxoV7` (`D09, D11, L19, L21, L24, L27, L30`); trước P2 ở `Arm A` gốc là `10` `MODEL_SEMANTIC_ERROR`, `6` `MODEL_ENTITY_BINDING_ERROR`, `2` `MODEL_GOAL_EXTRACTION_ERROR` (đa nhãn).
2. **Bao nhiêu lỗi do Local Parser?**
   Trên `42` ca dương `C60` ban đầu, **`22` ca** mang nhãn `PARSER_COVERAGE_GAP` do `local_geometry_parser` chưa tự đọc được biến thể câu/nhiều mục tiêu; nâng cấp normalizer `v3` + fast-path đưa số ca `C60` giải trực tiếp không cần SLM từ `12` lên **`23/42`**.
3. **Bao nhiêu lỗi do normalizer?**
   Ở đầu vào `/7`, **`10` ca** mang nhãn `NORMALIZER_LANGUAGE_GAP` (gồm cả `=mấy` trên `L03`, `CO'` thay `CO` ở `L21`, mở đầu thiếu `Cho`, dấu chấm phẩy, `mp(...)`, tách câu nhiều mục tiêu); `18` ca cần `v3` canonicalization khi đối chiếu ở `Arm B Gold Canon`. P2 `slm-verified-normalizer/3` (`VN06`–`VN11`) đóng toàn bộ nhóm này.
4. **Bao nhiêu lỗi do Source Gate?**
   Trên `C60` ban đầu có **`11` ca** vướng nhãn `SOURCE_GATE_GRAMMAR_GAP` (`D02, D03, D06, D11, L12, L13, L21, L22, L25, L30, L38`), hầu hết đã vượt qua Source Gate nguyên vẹn nhờ chuẩn hóa `v3` ở bình diện trước (`Arm B Canon = 33/42`). Trái lại, `6` ca tồn đọng `/7` (`v7h_p8_01..05` & `v7h_p5_09`) vẫn dừng ở `SOURCE_PREMISE_UNREAD` do khóa sở hữu `registry.py` (đã tạo [`source_gate_optional_grammar.patch`](./handoff/source_gate_optional_grammar.patch)).
5. **Bao nhiêu lỗi do giới hạn Typed Facts hoặc multi-goal?**
   Trên `C60` ghi nhận **`5` ca** `TYPED_FACT_SCHEMA_LIMITATION` (`D09, L10, L19, L21, L22` — chủ yếu trong `compact_clause/1`) và **`5` ca** `MULTI_GOAL_CONTRACT_LIMITATION` (`D12, L23, L27, L28, L30` — phần lớn do GBNF cũ trần `2` mục tiêu và `area`/`đoạn thẳng` thiếu ở Kernel). Mở trần GBNF lên `4` mục tiêu và thêm `cent` + `cube edge` giải quyết được `D09, D12, L19, L21, L22, L30`.
6. **Bao nhiêu bài có thể giải nếu Gold Typed Facts đúng?**
   **`15/42` (`35.71%`)** trên văn bản thô không chuẩn hóa (`Arm B Raw`) và **`33/42` (`78.57%`)** trên văn bản chuẩn hóa bảo toàn nghĩa (`Arm B Canon`). `9/42` ca còn lại (`D05, D13, L10, L12, L23, L28, L31, L36, L38`) nằm ngoài năng lực hạ tầng hoặc chính sách an toàn (`đoạn thẳng` hữu hạn, `SC²`, `area`, câu điều kiện `Nếu`, câu hội thoại thiếu ngữ cảnh trước).
7. **Có cần fine-tuning thêm không?**
   Trong chiến dịch `/9`, P3 fine-tuning LoRA có mục tiêu là **cần thiết và đã hoàn tất (`AxoV9-Q4_K_M`)** vì sau P2 vẫn còn `13` ca SLM trượt dù downstream giải được (`7` `C60` + `6` `/7`) và `0/14` multi-goal mới. Sau `/9`, `C60` đã đạt **`32/33` (`96.97%`) trần khả giải**, nên không cần tiếp tục train thêm khi chưa mở rộng `Source Gate` & ngữ liệu thực tế ngoài.
8. **Nếu có, model mới cải thiện đúng những nhóm lỗi nào?**
   Trên `val_v9.jsonl` (+GBNF), `AxoV9` nâng hiệu suất từ `70/94 (74.47%)` của `AxoV7` lên **`94/94 (100.00%)`**: đa mục tiêu `2–4` ý (`0/14 -> 14/14`), tứ diện/lăng trụ/hộp chữ nhật tách rời (`5/12 -> 12/12`), lăng trụ chiếu mặt (`17/20 -> 20/20`). Trên `C60` (+`6` ca SLM thực tế), giải mới `D09, D11, L19, L21, L24, L30` (`26/42 -> 32/42`, `SLM_V9_UNSEEN_150` đạt `94/105`).
9. **Có hồi quy so với AxoV7 không?**
   **Không có hồi quy trên 11 bộ nền (`0` regressions, `0` Mode A leaks) và `0` wrong-served ở mọi bộ.** Trên 5 bộ lịch sử SLM có xê dịch an toàn fail-closed nhẹ ở các bộ mẫu `/6`–`/7` (`DEV_CALIBRATION_16` `9/10 -> 8/10`, `SLM_NEW_HOLDOUT_48` `32/32 -> 31/32`, `SLM_V7_HOLDOUT_112` `74/80 -> 70/80`) trong khi tăng mạnh ở `C60` (`13/42 -> 32/42`), `HOLDOUT_40` (`24/28 -> 25/28`), tổng hợp `+14` ca dương trên 5 bộ lịch sử (`164 -> 178 / 224`) với `0` đáp số sai.
10. **Độ chính xác trên dữ liệu mới là bao nhiêu?**
    Trên tập đơn lần chạy duy nhất `SLM_V9_UNSEEN_150` (`0` trùng khung qua `1,165` ca đã biết): **`94/105` (`89.52%`, Wilson 95% CI `[0.8221, 0.9405]`)** ca dương (`54` fast-path + `40` SLM), **`45/45` (`100.00%`, `[0.9213, 1.0000]`)** ca âm an toàn, tổng **`139/150` (`92.67%`, `[0.8735, 0.9586]`)**; `EXTERNAL17` giữ **`12/12 + 5/5` (`100%`)**; `C60` đạt **`32/42` (`76.19%`) + `18/18`**. Lưu ý: `EXTERNAL_INDEPENDENCE = NOT_MEASURED` (chưa mở `sealed_H1` và chưa có nhật ký học sinh bên thứ ba).
11. **Có wrong-served mới không?**
    **`0` trên toàn bộ mọi phép đo `/9`** (`0/150` `SLM_V9_UNSEEN_150`, `0/17` `EXTERNAL17`, `0/60` `C60`, `0/126` `val_v9`, `0` trên `11` bộ nền và `5` bộ lịch sử). Tuy nhiên, `0` lỗi quan sát được không đồng nghĩa xác suất lỗi bằng `0` ngoài phân phối.
12. **Tốc độ CPU đã cải thiện bao nhiêu?**
    Mixed warm uncached (`n=100`, `6T`) từ `p50/p95 = 3,630.08 / 6,898.88 ms` (`/8`) giảm xuống **`1,270.35 / 4,109.98 ms`** (**`-65.0%` `p50`**, **`-40.4%` `p95`**); fast-path giảm `51.50 -> 33.90 ms`; cache hit khi truyền tường minh `runtime=rt` giảm từ `4,315.38 ms` xuống **`29.24 ms`**; trên `n=24` ablation thuần SLM `6T`, `AxoV9` (`max_tokens=256`, `-b 512 -ub 512`) đạt `3,912.89 / 5,311.37 ms` vs `AxoV7` `4,720.78 / 7,463.90 ms`.
13. **Warm uncached p95 có đạt ngưỡng chưa?**
    **Đạt trên workload hỗn hợp (`mixed n=100 p95 = 4,109.98 ms <= 5,000 ms`)**, nhưng **chưa đạt trên workload 100% SLM dài uncached (`pure n=100 p95 = 5,411.75 ms`, `2`-thread simulated `n=24 p95 = 10,196.66 ms`)**.
14. **Máy RAM 6–8 GiB thực tế có chạy ổn định không?**
    **`PHYSICAL_TARGET_HARDWARE = NOT_MEASURED`.** Trên host phát triển `15.78 GiB`, backend + `llama-server.exe` chỉ chiếm **`973.28 MiB`** peak working set (`637.5 MiB` private commit), nhỏ hơn rất nhiều so với ngưỡng `2,048 MiB`, nhưng đồng cư trú toàn trình duyệt Chromium + OS trên máy thật 6–8 GiB chưa được đo vật lý.
15. **Những nhóm hình học nào được hỗ trợ?**
    Chóp tam giác/tứ giác (đều, vuông, cân, vuông cân, chữ nhật, thoi, bình hành, hình thang vuông/thường trong `Source Gate`), tứ diện trực giao/đều, lăng trụ đứng/đều, hình hộp đứng/chữ nhật, hình lập phương; điểm phụ (`mid`, `cent`, `proj`, `div`, `face_perp`); các câu hỏi `vol`, `len`, `dist_pt_plane`, `dist_pt_line`, `dist_line_line`, `ang_lp`, `ang_pp`, `ang_ll` và đa mục tiêu tới `4` ý; nhập văn bản, `.docx` và PDF có tầng chữ thuần cục bộ (`SLM_V9_CAPABILITY_MATRIX.json`).
16. **Những nhóm nào phải từ chối?**
    Thiếu dữ kiện kích thước, tham chiếu cạnh/mặt mơ hồ, giả thiết phủ định/mâu thuẫn tam giác/độ dài không dương, câu điều kiện `nếu/khi/giả sử`, lỗi chính tả (`TYPO_REQUIRES_CONFIRMATION`), prompt injection, đa mục tiêu trích xuất thiếu (`REQUEST_NOT_ANSWERED`), ảnh quét đòi cloud VLM (`503 LOCAL_ONLY_CLOUD_VISION_DISABLED`), mặt cầu/nón/trụ/Oxyz/giải tích/hình phẳng 2D (`GATE_OUT_OF_SCOPE`), và biểu thức bình phương `SC²`/diện tích tam giác/đoạn thẳng hữu hạn ngoài năng lực hạ tầng.
17. **Bao nhiêu đường gọi Gemini đã được thay?**
    Đã kiểm toán toàn bộ **`9` bề mặt Gemini**: thay cục bộ hoàn toàn **`3`** (`POST /api/analyze` `live`/`local-first` bằng `local-only-scoped`, `/api/health`), thay tất định **`1`** (`/api/input/prepare` văn bản/`.docx`/PDF + OCR span), chặn có chủ đích ở chế độ offline **`2`** (legacy image `/api/analyze`, `/api/image/extract`), giữ vô hiệu không gọi **`2`** (4 module Gemini khóa & `skills/*.md`), và **`1`** ở `frontend/` bàn giao patch.
18. **Có còn cloud fallback không?**
    **Không (`silent_cloud_fallbacks = 0`).** Trong `local-only-scoped`, `local-only-general` và `offline-lab`, `main.py` buộc `api_key = None`, `vision_allowed = False`, và `LocalSlmHybridRun` không có nhánh gọi lại Gemini kể cả khi biến môi trường đặt sẵn key giả + `ALLOW_LIVE_AI=1` (`verify_offline_network_isolation_v9.py` + `test_local_only_product_and_network_isolation.py`).
19. **Có chạy được không cần Gemini API key không?**
    **Có.** Với `HYBRID_ROUTE_MODE=local-only-scoped` hoặc `offline-lab` và `GEMINI_API_KEY=""`, `/api/health` trả `aiAvailable=True, localOnlyMode=True, localSlmReady=True, hasKey=False`, `/api/analyze` dựng hình và kiểm chứng bình thường, `/api/input/prepare` xử lý `.docx`/PDF văn bản không cần key.
20. **Có hoạt động khi mất Internet không, trong phạm vi đã kiểm thử?**
    **Có (với điều kiện runtime & GGUF đã provisioning trước ở `%LOCALAPPDATA%\axo-slm`).** Khi chặn toàn bộ `socket.connect` / `socket.create_connection` / `httpx` ngoài loopback `127.0.0.1`, các tác vụ text, `.docx` và GGUF chạy trọn vẹn với **`0`** kết nối ra ngoài (`OFFLINE_NETWORK_ISOLATION_REPORT.md`).
21. **Backend sản phẩm đã thực sự chuyển sang local-only chưa?**
    **Đã hỗ trợ đầy đủ qua opt-in `HYBRID_ROUTE_MODE=local-only-scoped` (và `offline-lab`, `local-shadow`, gated `local-only-general`), nhưng mặc định khi không đặt biến môi trường vẫn giữ `"live"`** cho tới khi chủ sở hữu phê duyệt áp dụng [`default_cutover_local_only_scoped.patch`](./handoff/default_cutover_local_only_scoped.patch) và bản vá UI tương ứng.
22. **Frontend có còn phụ thuộc vào các endpoint Gemini không?**
    **Có — ở giao diện hiện tại chưa sửa (`BLOCKED_OWNERSHIP`):** `frontend/src/llm/client.ts` và `ProblemInput.tsx` hiện vẫn kiểm `hasKey` cho thông báo thiếu key; [`frontend_local_ai_status_and_keyless_ux.patch`](./handoff/frontend_local_ai_status_and_keyless_ux.patch) (đã kiểm `git apply --check`) chuyển sang `aiAvailable` / `localOnlyMode` và hỗ trợ `/api/analyze` + `.docx`/PDF không key, còn OCR ảnh chụp scan từ giao diện nếu chưa dùng luồng span confirmation cục bộ vẫn chờ cloud VLM ở chế độ `live`.
23. **Có thể rollback an toàn không?**
    **Có ở cả 3 tầng:** (a) Runtime model tức thì qua `python backend/scripts/provision_local_slm.py --rollback v7` (về `AxoV7` `36e784d1…`) hoặc `--rollback orig` (`ac2d9771…`) thông qua ghi nguyên tử `active_model.json`; (b) Cấu hình route bằng giữ `HYBRID_ROUTE_MODE=live`; (c) Git revert hoặc checkout tag `pre-hybrid-cutover-f986e897` / baseline `c73506cb2`.
24. **Những thành phần nào còn bị chặn ownership?**
    `frontend/**` (`axo-geometry-library`, bản vá UI `handoff/frontend_local_ai_status_and_keyless_ux.patch`), đổi mặc định `HYBRID_ROUTE_MODE` (`handoff/default_cutover_local_only_scoped.patch`), mở rộng cụm từ mở đầu tùy chọn trong `registry.py` (`handoff/source_gate_optional_grammar.patch`), 4 module Gemini đã khóa (`typed_fact_next_extraction.py`, `function_calling.py`, `fact_extraction.py`, `gemini.py`), và `Planner /26` / `Engine /24`.
25. **Có đủ điều kiện chuyển mặc định local-only trong phạm vi nào?**
    Đủ điều kiện kỹ thuật để chủ sở hữu xem xét chuyển mặc định **trong phạm vi hẹp có công bố rõ ràng (`LOCAL_ONLY_SCOPED_RELEASE_READY` — bài toán hình học không gian đa diện tiếng Việt dạng văn bản / `.docx` / PDF có tầng chữ)** sau khi áp dụng 2 bản vá `default_cutover` + `frontend` và xác nhận phần cứng RAM 6–8 GiB; **chưa đủ điều kiện** cho `local-only-general` hay thay thế toàn bộ năng lực Gemini.
26. **Những giới hạn nào cần công khai cho người dùng?**
    10 trạng thái UX tiếng Việt minh bạch ([`LOCAL_AI_USER_EXPERIENCE_REPORT.md`](./LOCAL_AI_USER_EXPERIENCE_REPORT.md)) cùng thông báo rõ: chế độ ngoại tuyến chỉ giải các bài đa diện được hỗ trợ qua Exact Kernel, từ chối hình tròn xoay/Oxyz/ảnh chụp cần VLM (`CLOUD_OCR_DISABLED_OFFLINE`), và xử lý đề dài trên CPU có thể mất `~4–6 giây` khi chưa warm cache.
27. **Điều kiện nào còn thiếu để thay thế tương đương Gemini?**
    (1) OCR ảnh toán học cục bộ đạt độ phủ tương đương multimodal VLM trên ảnh chụp viết tay/nhiễu; (2) Mở rộng thượng tầng `TypedFactNext /2` + `Registry /33` + `Source Gate` cho thiết diện/diện tích/hình tròn xoay; (3) Đo đối chứng trực tiếp `GEMINI_PARITY` có ngân sách; (4) Đo `EXTERNAL_INDEPENDENCE` (`sealed_H1`, dữ liệu học sinh ngoài thật); (5) Đo lường thực tế trên máy 6–8 GiB cùng trình duyệt (`PHYSICAL_TARGET_HARDWARE`, `REAL_STUDENT_USABILITY`).
28. **Khi nào có thể quay lại tích hợp Dynamic Construction Planner?**
    Ngay ở wave kế tiếp (**`AXO CONSTRUCTION INTEGRATION`**) sau khi owner tiếp nhận `handoff/*.patch` của `/9`: hiện tại `backend/experimental/construction_planner/` (`CANDIDATE_V2_FREEZE_SHA256 = 26c9b505…`) đã được chứng minh hoàn toàn nguyên vẹn (`matched = true`), sẵn sàng tích hợp tuần tự tách biệt khỏi đợt đổi NLU `/9` để tránh chồng chéo nguyên nhân.

---

## 4. Checklist Xác Minh (§41) & Định Hướng Sau `/9` (§43)

- `[x]` Mọi lỗi C60 được chẩn đoán từng case kèm Gold intervention.
- `[x]` Ngữ pháp đóng tất định (`v3`/`v9`) tách biệt và giữ nguyên Source Grounding & Exact Kernel.
- `[x]` Fine-tuning có mục tiêu chỉ chạy sau bằng chứng residual; candidate `AxoV9-Q4_K_M` đóng băng trên `val_v9.jsonl` disjoint.
- `[x]` Đánh giá unseen single-shot `SLM_V9_UNSEEN_150` (`0` wrong-served, CI 95% Wilson, blocker `EXTERNAL_INDEPENDENCE = NOT_MEASURED` công khai).
- `[x]` Profiling CPU (`cold` / `pure warm` / `mixed warm` / `cached`), RAM (`973.28 MiB` WS), concurrency & fault recovery (`16/16`).
- `[x]` `9` bề mặt Gemini được kiểm toán; route `local-only-scoped` không cần API key (`external_ai_calls = 0`, `gemini_invocations = 0`, `silent_cloud_fallbacks = 0`).
- `[x]` Đóng gói model provisioning/rollback & 3 bản vá owner `git apply --check` PASS.
- `[x]` Toàn bộ regression & `AXO CONSTRUCTION /2` freeze integrity xác minh nguyên vẹn.
- **Định hướng tiếp theo (§43):** Wave kế tiếp là **`AXO CONSTRUCTION INTEGRATION`** (tích hợp Dynamic Construction Planner `/2` hiện giữ nguyên ở `Level 2 — BACKEND_INTEGRATION_READY`), tiếp theo sau đó mới là **`AXO MODEL 2` / Needle 3**.
