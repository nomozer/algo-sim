# Goal-directed function composition — báo cáo run (Hybrid Wave 2A)

- **Run:** `goal-directed-function-composition` · nhánh `research/hybrid-wave2a-function-composition` từ `main` = `origin/main` = `ce5b2575`
- **Ủy quyền:** `GO_HYBRID_WAVE2A_LOCAL_IMPLEMENTATION` (không merge/push, không GO LIVE, không bật Hybrid)
- **Commit:** product `a45a043f` → `b70e4769` (sửa review N-1) · holdout lock `50ac258a` · candidate freeze `594870fc` (thay thế) → **`3a57f5d3`** (112 file, `e2109ef1cde5deaf9624acd19d19a622dc8d8e5747b749e146ad93996e728766`) · evaluation `5f2e8390`, chạy lại trên candidate cuối ở `results/evaluation-final-candidate/` (4 nhánh chạy trên mã cuối: mọi chỉ số trùng, trừ thời gian; nhánh `pre-composition-main` chạy mã `ce5b2575` mà bản sửa không chạm, nên được MANG SANG nguyên byte, không chạy lại — review R2-N1)
- **Live provider calls:** 0 (`ALLOW_LIVE_AI=0` mọi lượt) · `CACHE_VERSION` 127 (không bump, §9) · `DEFAULT_MODE` `LLM_ONLY` · response contract `flat`
- **T3 có thẩm quyền:** `FULL_PRODUCT_GATE_PASS` tại `9f46a637` (backend 11076/0, frontend 1146/0, build, demo 5/5, crash 6/6; `authoritative-t3.json`) · **review độc lập:** vòng 1 FAIL (I-1) → vòng 2 `INDEPENDENT_REVIEW_PASS` (`review.md`)

## 0. Câu hỏi nghiên cứu và trả lời ngắn

> Planner có tự tìm, chọn và phối hợp các Geometry Functions đã khai báo để giải mục tiêu dựng hình mới, không cần LLM
> sinh mã dựng hình và không cần chuỗi xử lý viết riêng cho từng dạng đề không?

Trong phạm vi đã đo: **có, theo nghĩa hẹp sau**, với giới hạn ở §10. Run này THÊM dữ liệu vào Registry (contract
producer `centroid`, contract mục tiêu góc, primitive `ask_angle_lines`) và một lần tổng quát hoá phần nhận mục tiêu theo
slot; sau đó **cùng một mã planner, không có nhánh nào gọi tên một cặp hàm**, tự phối hợp các contract ấy với các
contract đã có. Tính "mới" của các tổ hợp đến từ contract thêm trong chính wave này — bằng chứng là về **phối hợp từ
contract**, không phải về việc không cần contract mới.

- So với **baseline thật duy nhất** — `main` trước run (`pre-composition-main`, mã `ce5b2575`, cùng đầu vào, oracle độc
  lập): holdout khoá trước (24 ca, 6 cấu hình khối khác bộ dev, có metric không trực chuẩn) **16/16** so với **1/16**;
  **13/13** bài cần một tổ hợp mà `main` không giải (8 chữ ký), từ chối đúng mã **8/8**, **0/24** dương tính giả.
- **Bật/tắt dữ liệu, cùng mã:** gỡ contract `centroid` (chỉ dữ liệu) ⇒ cùng planner từ chối; đặt lại ⇒ phục vụ
  (`test_slice_a_zero_planner_edit_discovery_centroid_to_area`, `test_removing_one_contract_removes_exactly_that_composition`).
  Không dòng nào trong phần tìm kiếm / nhận mục tiêu gọi tên một hàm (`test_no_planner_branch_names_a_composed_pair`).
- Các nhánh `rule-based` và `no-composition` là **ablation**, không phải baseline độc lập: `rule-based` = planner
  production với mọi điểm mô tả bị cấm (review I-1: trùng `no-composition` ở mọi tổng, khác mã từ chối ở 33/48 dòng), nên
  2/16 của chúng đúng theo cấu tạo. Không có baseline "luật viết tay cho từng tổ hợp" nào được xây (PROPOSED nếu cần).
- Ngôn từ holdout là chính văn phạm đóng mà cùng tác giả viết vào Registry: 16/16 chứng minh phối hợp chạy đúng trên
  những cách viết ấy, **không** chứng minh khái quát ngôn ngữ (review N-2).

## 1. Cái gì đã IMPLEMENTED (product `a45a043f` + `b70e4769`)

| Thành phần | Thay đổi | File |
|---|---|---|
| `centroid` producer contract | Contract thực nghiệm `measure_function_discovery.experimental_centroid_contract` đưa vào Registry **nguyên văn** (test khẳng định bằng nhau) | `registry.py` |
| `ask_angle_line_plane` goal contract | `(Point P, Point Q, Plane R) → AnswerAngleLinePlane`, `goal="angle"`, verifier `angle_line_plane`, hai cách viết đóng "nối … với …" | `registry.py` |
| `ask_angle_lines` (primitive mới) | Hàm hỏi góc hai đường (cos²) — kernel/IR đã có `angle_cos_sq(line3,line3)`; goal contract `(Point P, Point Q, Line L) → AnswerAngleLines`; **`provider_offered=False`**: chỉ planner nhánh B, không vào khai báo tuyến A | `registry.py`, `engine.py` |
| Đọc slot có kiểu một chỗ | `goal_slots`, `goal_target_keys`, `GOAL_VERIFIER_TARGET` — planner điền slot, cổng nguồn kiểm lại slot, engine chọn verifier, cùng một bộ đọc | `registry.py` |
| Cổng chứng chỉ `effect-chain` | Ba nhánh cứng theo loại mục tiêu (`length`/`area`/khoảng cách) thay bằng kiểm đích theo kiểu slot; verifier khai báo phải đo đúng đích slot mô tả (verifier "nói dối" ⇒ `AUXILIARY_RULE_MISMATCH`) | `registry.py::_kiem_result_binding` |
| Nhận mục tiêu theo slot | `_toan_hang_muc_tieu`: điểm mô tả điền slot đầu; `points_a` = điểm thứ hai có tên của một **đường** qua điểm mô tả; `points_b` = đích (n điểm / đường 2 nhãn / mặt ≥ 3). Không đoán vị trí trong một danh sách | `planner.py` |
| Bẫy 1 | Câu hỏi có tên chỉ vào resolver khi mọi slot là điểm (length, area như trước); góc có tên giữ luật trực tiếp | `planner.py::_cau_hoi` |
| Góc hai đường có tên | Luật trực tiếp `(line, line) → ask_angle_lines` | `planner.py::_cau_hoi` |
| Verifier độc lập | `_goc_hai_duong_cos2` = ⟨u,v⟩²_G / (⟨u,u⟩_G⟨v,v⟩_G); `_KIEM_DICH["angle_lines"]`; hậu kiểm mọi `ask_angle_lines`; tiền kiểm đường suy biến | `engine.py` |
| Tuyến A | Provider gọi hàm không được mời ⇒ `FUNCTION_NOT_OFFERED` | `function_calling.py` |
| v3 (nghiên cứu) | Câu hỏi trên điểm mô tả sinh từ goal contract của Registry (area, angle) — lấp khoảng trống POC-3 #1 | `fact_extraction.py` |
| Version | `geometry-functions/7`, `geometry-fact-planner/8`, `geometry-function-engine/6` (owner chọn bump) | ba module |
| Fixture `--verify` | `IDENTITY_DELTAS`: chỉ cặp version cũ→mới đã khai và fingerprint tính lại hai phía được khôi phục; mọi byte khác phải trùng | `export_hybrid_preview_fixtures.py` |

**Không làm (đúng phạm vi):** hình thang vuông, lăng trụ xiên, khối con, mặt cong, Adapter /3, bật Hybrid, `divide_segment`,
`ask_distance_line_plane`, mặt qua điểm ⊥ đường.

## 2. Thuật toán tìm kiếm và hợp đồng giới hạn

`_EffectResolver` (đã có từ trước, **không viết lại**) là tìm kiếm ngược có giới hạn trên hiệu ứng của Registry:

1. Mục tiêu = `(effect kind, operands có kiểu)`; với điểm mô tả, `_toan_hang_muc_tieu` điền slot theo `goal_slots` của mỗi
   goal contract cùng `quantity`; đúng một kiểu effect khớp, nếu không ⇒ `AMBIGUOUS_FACT` / `FACT_INCOMPLETE`.
2. Một nhu cầu `(kind, operands)` được giải bởi **mọi** contract có effect cùng kiểu và toán hạng cùng kiểu; input của
   contract thành nhu cầu con. Lá: điểm/mặt có nhãn trong nguồn, đường có tên.
3. Tái dùng: lời gọi đã có trong kế hoạch với cùng hiệu ứng ⇒ chi phí 0; dựng mới ⇒ +1. Chọn chi phí nhỏ nhất, hoà theo tên
   hàm và nhãn (không theo thứ tự catalog — `reversed` registry cho cùng kế hoạch).
4. Chu trình (`active`) ⇒ `DEPENDENCY_CYCLE`; trần `MAX_EFFECT_DEPTH=3`, `MAX_EFFECT_NEEDS=32`, `MAX_EFFECT_CANDIDATES=8`,
   `MAX_RESULT_FEET=8` ⇒ `PLAN_TOO_LARGE`, không phục vụ một phần.
5. Lời gọi **viết từ khuôn của contract** (`render_call`); chứng chỉ `effect-chain` ghi chuỗi; cổng nguồn viết lại từng
   lời gọi từ contract và buộc cụm hỏi đúng nhãn; engine kiểm mô tả (`_MO_TA`), đáp số qua kernel và verifier Gram độc lập;
   thứ tự phụ thuộc Wave 1 (`_sap_xep_phu_thuoc_loi_goi`) xếp lời gọi.

Đo được trên mọi bài VERIFIED (dev + holdout): `needs` ≤ 7, `candidates` ≤ 3, `depth_max` ≤ 2 — xa dưới trần.

## 3. Tổ hợp mới tìm được (EXECUTED_PASS)

Chữ ký = các hàm của chuỗi → hàm hỏi, đọc từ chứng chỉ thật của kế hoạch. "Mới" = không chữ ký nào trong số này được
`main` trước run (`pre-composition-main`, mã `ce5b2575`) giải trên cùng đầu vào.

Holdout (8): `centroid→ask_area`, `centroid→ask_length`, `centroid→ask_distance_point_plane`,
`centroid→orthogonal_projection_line→ask_length`, `centroid→ask_angle_line_plane`, `centroid→ask_angle_lines`,
`midpoint→ask_angle_line_plane`, `midpoint→ask_angle_lines`. Dev thêm tổ hợp nhiều mục tiêu của W2-EXP-15
(`ask_angle_lines | ask_volume | centroid→ask_distance_point_plane`).

## 4. Rule-based vs goal-directed, ablation (`results/evaluation/metrics.json`)

Cùng TypedFact, cùng Registry (không nhánh nào bị bớt hàm), cùng engine, cùng oracle.

| Nhánh | Dev: bài VERIFIED | Dev: mục tiêu | Holdout: bài VERIFIED | Holdout: tổ hợp mới | Từ chối đúng mã (dev · holdout) | Dương tính giả |
|---|---|---|---|---|---|---|
| goal-directed (độ sâu 3) | 15/16 | 17/18 | **16/16** | **13/13** | 8/8 · 8/8 | 0/24 · 0/24 |
| single-step (độ sâu 2) | 15/16 | 17/18 | 16/16 | 13/13 | 8/8 · 8/8 | 0/24 · 0/24 |
| no-composition (độ sâu 1) | 2/16 | 2/18 | 2/16 | 0/13 | 5/8 · 6/8 | 0/24 · 0/24 |
| rule-based | 2/16 | 2/18 | 2/16 | 0/13 | 5/8 · 6/8 | 0/24 · 0/24 |
| pre-composition-main (`ce5b2575`) | 3/16 | 3/18 | 1/16 | 0/13 | 1/8 · 0/8 | 0/24 · 0/24 |

- Ca dev không VERIFIED: **W2-EXP-02** nguyên văn — `AMBIGUOUS_VALUE_QUOTE` ở cổng tiền đề (câu "cạnh đáy bằng a và chiều
  cao bằng a" mang hai số; luật: quote của một ô số giữ đúng MỘT số). Biến thể tách câu `W2-EXP-02-split` VERIFIED cos²=9/11.
  Đây là giới hạn grounding tiền đề, không phải composition.
- Nhánh "khác mã" của rule-based/no-composition là từ chối an toàn với mã khác (vd. `UNSUPPORTED_CAPABILITY` thay vì
  `SOURCE_OBJECT_MISMATCH`): chúng dừng trước khi tới cổng nguồn. Hai nhánh này là ablation (xem §0), id nhánh giữ nguyên
  trong `results/` để truy vết.
- **Độ sâu 2 = độ sâu 3 trên corpus của run**: không ca dev/holdout nào cần hai tầng producer. Để tách hai mức, đo
  **bổ sung (sau đánh giá chính, không đổi thuật toán)** trên bundle 174 dòng đăng ký trước, kỳ vọng từ corpus nguồn
  (`results/supplementary-bundle-174/`): VERIFIED **70** (độ sâu 3) · **61** (độ sâu 2) · **41** (độ sâu 1) · **48**
  (rule-based) · **65** (`pre-composition-main`). 9 dòng chỉ độ sâu 3 giải được đều là chuỗi giao tuyến
  (`midpoint/centroid → intersection_line → orthogonal_projection_line → ask_length` và các khoảng cách tới giao tuyến), độ
  sâu 2 từ chối `PLAN_TOO_LARGE`. Một dòng `FALSE_SERVE` ở nhánh goal-directed là `new/negative/centroid-without-contract`:
  đầu vào **trùng hệt** `new/discovery/centroid-to-plane`, chỉ "âm" vì Registry thời ấy thiếu contract; đáp số 16/9 bằng kỳ
  vọng đăng ký trước của dòng sinh đôi — delta đã khai (§6), không phải sai toán.

## 5. Oracle độc lập và W2-EXP

- `oracle.py`: không import `app.*`; mỗi ca tự khai khung toạ độ (Euclid, hoặc affine + Gram G hữu tỉ: lăng trụ đều, chóp
  đều với h²=7, tứ diện đều, tam giác 120° với g₁₂=−15/2) và tự dựng điểm mô tả từ định nghĩa. Engine không thấy khung này.
  Khớp mọi phép tính tay của run (7/144, 9/11, 9/52, 75/4, 4/9, 20/29, 2/29, 13/9, 29/9, 16/9, 25/9, 8/17, 2/13).
- Kiểm toán W2-EXP (`w2-exp-audit.json`): **W2-EXP-11A det Gram = −105/4 a⁴** (không phải −45/4) — xác nhận đính chính
  của owner; W2-EXP-03 9/5 và W2-EXP-07 1/48 xác nhận lại độc lập. Đếm lại theo row ID: **12 id dương + 12 id âm + 2 họ
  tính chất = 26 đơn vị theo cách đếm này; 16 mục tiêu dương** — con số "22" của báo cáo bị bác.
- Thực thi (`results/w2-exp-execution.json`, `corpus-dev.json`): W2-EXP-01, 02-split, 10A-2, 15 (3/3 mục tiêu) **VERIFIED**;
  09A, 09B, 10A-1, 11A, 11B, 11C, 12A, 12B, 13A, 14B **EXECUTED_PASS** (đúng mã kỳ vọng); 10B, 13B, 14A **từ chối an
  toàn nhưng mã báo cáo sai**: `SKEW_NO_INTERSECTION` (không phải `PARALLEL_NO_INTERSECTION`), `NOT_ASKED_IN_SOURCE` (với
  cách mã hoá này), `TAMPERED_WITNESS_FOOT` (mã `NON_ZERO_INNER_PRODUCT_U` **không tồn tại** trong `certificates.py`).
  03, 05, 06A, 06B, 07 **NOT_EXECUTED** (phạm vi 2B/2C; toán đã duyệt); 04, 08 năng lực có sẵn, phủ bởi hồi quy 174.
- W2-EXP-16 (bất biến): thực thi trên 8 tổ hợp chóp vuông × 4 phép biến đổi (thứ tự fact, thứ tự toán hạng mô tả, đổi
  nhãn, nhân 2) = 32 ca PASS — **không** trên chính W2-EXP-01/15 như báo cáo đề xuất (lệch, đã ghi).

## 6. Âm / từ chối và tương thích ngược

- Test đích: `test_goal_directed_function_composition.py` **83/83** GREEN; cùng file trên mã `ce5b2575` (worktree tạm,
  đã gỡ): **77 ĐỎ / 6 xanh** — 6 test xanh là chốt tương thích (Bẫy 1 ×2, Bẫy 2, từ chối `point`, từ chối partner ở diện
  tích, chu trình) (`verification/red-on-base.log`).
- Fail-closed đã khoá: hai partner, partner giấu trong `points_b`, nhãn đích trùng, đích 1 nhãn, `point`, trọng tâm 4
  điểm, phủ định, `prove`, `condition`, `ambiguous`, partner lạ (`UNKNOWN_LABEL`), sai mô tả / sai mặt đích / sai partner
  so với nguồn (`SOURCE_OBJECT_MISMATCH`), verifier nói dối, đường suy biến, nhu cầu tự phụ thuộc (`DEPENDENCY_CYCLE`).
- **Sửa sau review (N-1, product `b70e4769`):** một mục tiêu mô tả loại độ dài hoặc góc theo sau bởi câu hỏi thứ hai trong
  cùng câu ("…, và độ dài SC.") từng được PHỤC VỤ MỘT PHẦN — câu hỏi sau bị bỏ im lặng (có từ trước run cho độ dài, run này
  mở rộng sang góc). Gốc: `_duoc_hoi`/`_vung_hoi` đọc dấu dữ kiện "với" trên văn bản thô, nên "với" BÊN TRONG cụm đối tượng
  ("nối S với …") cắt động từ hỏi. Nay đọc trên `_bo_cum(...)` (giữ độ dài) ⇒ `REQUEST_NOT_ANSWERED`. ĐỎ 3/3 → XANH; hồi
  quy 174, ma trận v3, NLU gold không đổi; đánh giá chạy lại trên candidate cuối trùng mọi chỉ số.
- Bẫy 1: góc hai mặt / đường–mặt có tên giữ luật trực tiếp, không chứng chỉ chuỗi, không `effect_resolution`.
  Bẫy 2: mặt qua điểm ⊥ **mặt** vẫn `PLANE_NOT_UNIQUE`.
- **Adapter /2: 41/41** fixture tái sinh trùng byte **ngoài** cặp version/fingerprint đã khai; trước khi bump: trùng byte
  tuyệt đối. Tiêm lỗi: version không khai, fingerprint giả, nội dung khác — đều bị bắt (`test_hybrid_preview_fixtures.py`).
- **Hồi quy 174 dòng** (`results/historical-regression-delta.json`, máy sinh): 168/174 trùng tuyệt đối (status, mã, bình
  phương đáp số); 6 dòng đổi, mỗi dòng có kỳ vọng độc lập: 5 capability gap `centroid` nay VERIFIED (16/9, 25/9, 40/9, 29/9,
  41/9 — kỳ vọng đăng ký trước) + `centroid-without-contract` (sinh đôi của `centroid-to-plane`). Cảnh phục vụ 84 → 90, mọi
  timeline đóng phụ thuộc. "126 ca đóng băng" của báo cáo Gemini: **NOT_FOUND** trong kho (khả năng nhầm với
  `CACHE_VERSION` 126); mốc có thật là bundle 174 này.
- **Ma trận v3 (8 ô)**: LOCKED 4/4 ô không đổi; PILOT 4/4 ô đổi đúng một dòng `dev05` FALSE_REFUSAL_CAPABILITY_GAP →
  CORRECT_COMPLETE (kỳ vọng đăng ký trước value² = 16). **NLU GOLD 60 dòng**: phục vụ 10 → 10; D09, D12, L19, L29 vẫn từ
  chối, mã `UNSUPPORTED_CAPABILITY` → `SOURCE_OBJECT_MISMATCH` (năng lực nay có; cách viết — phép thế "đó/này", khoảng cách
  tới một điểm, thứ tự ngược — nằm ngoài văn phạm đóng) (`results/historical-gold-delta.json`, lớp delta thứ ba).
- Bề mặt mô hình: `function_declarations` `5ceb0f99…`, tuyến A `7ea511a6…`, `flat` `485d3834…`, `TypedFact` schema
  `aa9d93ee…` **không đổi**; v3 (nghiên cứu) `90bf8f03…` → `4bff35bb…` (34 → 40 nhánh, cấu trúc ~29,7k ký tự; Gemini có
  biên dịch nổi hay không: **NOT_MEASURED**).
- Không GOLD nào bị sửa; các corpus đóng băng giữ nguyên byte; delta đi qua lớp khai báo.

## 7. Scene3D / IR

Mọi bài phục vụ (dev 15, holdout 16, bundle 90) qua `validate_semantic_program`, kernel thực thi khớp bố cục engine, và
timeline đóng phụ thuộc (`depends` sinh trước); điểm tổ hợp xuất hiện sau khối mà nó nằm trên
(`test_scene_timeline_builds_dependencies_first`). `ask_angle_lines` không thêm loại đối tượng Scene3D mới (đo bằng
`angle_cos_sq` hai `line3`, như góc đường–mặt). Mã Scene3D/frontend **không đổi**.

## 8. Chi phí hiệu năng

Lập kế hoạch: trung vị 0,77–0,80 ms trên bài VERIFIED (main trước run: 0,73–1,19 ms trên tập nhỏ hơn). Tuyến đầy đủ trung
vị 8,6 ms/bài phục vụ. Một mẫu mỗi bài, không cô lập máy ⇒ **chỉ báo hướng**, không phải phép đo hiệu năng có thẩm quyền.

## 9. Quyết định cache

**Không bump (127 giữ).** `/api/analyze` mặc định không nạp module nào run này sửa ở mức module: đường duy nhất là import
lười `pipeline.py:89` bên trong `route_policy_snapshot`, chỉ chạy khi preview Hybrid bật; preview không ghi cache
(`_policy_identity` từ chối fingerprint preview). Bao đóng import khoá bởi
`test_structured_geometry_relations.py::test_Y…`; `test_preview_policy_does_not_change_analyze_or_default_cache_identity` xanh.

## 10. Khoảng trống còn lại (UNSUPPORTED) và đề xuất Wave 2B (PROPOSED)

UNSUPPORTED (từ chối có mã, không đoán): hai điểm mô tả trong một câu hỏi (không có ô cấu trúc cho toán hạng thứ hai không
tên); khoảng cách tới một **điểm** viết "khoảng cách … đến điểm X" (D09, L19); phép thế "hai đường thẳng đó/này" (D12,
L29); hai giá trị trong một câu tiền đề (W2-EXP-02); chia đoạn theo tỉ số, mặt ⊥ đường, đường–mặt, khối con, đáy hình
thang, lăng trụ xiên; `_EffectResolver.distance` vẫn gọi tên `orthogonal_projection_line` khi viết chứng chỉ chân vuông
góc (coupling có từ trước run, ngoài phần tìm kiếm). Review N-3: chốt `FUNCTION_NOT_OFFERED` chỉ ở `parse_response` của
tuyến A; `dung_tu_loi_goi` nhận `ask_angle_lines` từ mọi kế hoạch (vô hại khi tuyến A chưa nối preview) và mã này chưa có
lớp từ chối preview riêng. Review N-4: mã mới của ca blocker được ghi đè ở ba test bằng dict riêng thay vì một file delta
(mọi chỗ vẫn đòi REFUSED, không đáp số, không cảnh).

PROPOSED cho 2B: (1) `divide_segment` producer contract + ngữ pháp tỉ số đóng (Bẫy 4); (2) mặt qua điểm ⊥ đường
(`PlanePerpendicularToLineExpr`) giữ `PLANE_NOT_UNIQUE`; (3) mục tiêu độ dài viết "khoảng cách … đến điểm" như một
`phrase` thứ ba của goal contract length; (4) ô cấu trúc cho toán hạng mô tả thứ hai (thay đổi bề mặt trích xuất ⇒ đo lại);
(5) `solid` trên độ dài đoạn ở v3 (POC-3 #2); (6) đo Gemini chấp nhận lược đồ v3 40 nhánh trước mọi lượt live.

Provenance corpus: `AGENT_AUTHORED_WITH_INDEPENDENT_ORACLE_NOT_HUMAN_VALIDATED`; holdout khoá ở `50ac258a` trước mọi lần
chạy (`holdout-lock.json`), không thay đổi thuật toán nào sau khoá.
