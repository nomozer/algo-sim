# MULTICASE_STRUCTURED_ANALYZE_COMPILER_BENCHMARK

**Ngày chạy:** 2026-09-21 · **Nhánh:** `feat/photo-problem-to-scene` ·
**OUTCOME = `PROVIDER_INCOMPLETE`** ·
**NEXT_ACTION = `RETRY_REMAINING_PREREGISTERED_CASES_LATER`**

| nhãn bắt buộc | giá trị |
|---|---|
| `MEASUREMENT_CLASS` | `DEVELOPMENT_HOLDOUT_PILOT` |
| `DATASET_CLASS` | `DEVELOPMENT_HOLDOUT_PILOT` |
| `HELD_OUT_CLAIM` | **NO** — bộ ca do người vận hành soạn **sau** khi prompt và kiến trúc đã tồn tại |
| `EVALUATOR_INDEPENDENCE` | `OPERATOR_WAIVED` — tôi vừa soạn đề, vừa viết bộ chấm, vừa đọc kết quả |
| `STATISTICAL_SIGNIFICANCE` | `NOT_ESTABLISHED` |
| `PRODUCT_BEHAVIOR_CHANGED` | **NO** — wave này chỉ đo; 0 dòng `backend/app` đổi |
| `MERGE_ALLOWED` | **NO** (không đổi — §0e vẫn chờ người) |

---

## 1. Câu hỏi wave này đi hỏi

Lượt trước (`…LIVE_REVALIDATION…`) cho thấy **một** ca controlled đi trọn
`đề → Analyze → RequestContract → FactGraph → compiler tất định → cảnh`. Một ca
không nói được gì về **tính tổng quát**. Wave này hỏi: *cùng một họ bài, viết
theo nhiều kiểu khác nhau, thì tuyến ấy còn đứng được bao nhiêu lần?*

12 ca đóng băng trước khi gọi provider (commit `1f0b645`): 8 ca dương P01–P08
thuộc họ `right_triangle_base_pyramid_volume`, 4 ca đối chứng âm N01–N04 mỗi ca
mang **một** khiếm khuyết đã đặt tên. Không ca nào dùng lại bộ nhãn điểm của ca
controlled cũ.

## 2. Kết quả thật — 7/12 ca chạy, 5 ca chưa chạy

| ca | lớp cách viết | Analyze | quan hệ đúng | compiler | kết cục |
|---|---|---|---|---|---|
| P01 | `DEFINITIONAL_NORMALIZATION` | PASS | 2/2 (1.0) | COMPILED | **FULL_PIPELINE_PASS** (V = 40) |
| P02 | `EXPLICIT_SURFACE_RELATION` | PASS | 2/2 (1.0) | COMPILED | **FULL_PIPELINE_PASS** (V = 14) |
| P03 | `EXPLICIT_SURFACE_RELATION` | **FAIL** | 0/2 (0.0) | không chạy | `ANALYZE_INCOMPLETE_OR_UNSAFE` |
| N01 | `RIGHT_ANGLE_VERTEX_UNDETERMINED` | — | — | **từ chối** | **SAFE_REJECTION** |
| P04 | `DEFINITIONAL_NORMALIZATION` | PASS | 2/2 (1.0) | COMPILED | **FULL_PIPELINE_PASS** (V = 20) |
| P05 | `EXPLICIT_SURFACE_RELATION` | **FAIL** | 0/2 (0.0) | không chạy | `ANALYZE_INCOMPLETE_OR_UNSAFE` |
| P06 | `DEFINITIONAL_NORMALIZATION` | — | — | — | **`PROVIDER_ERROR`** — ReadTimeout |
| P07 P08 N02 N03 N04 | — | — | — | — | **CHƯA CHẠY** |

Gộp lại: **3/6 ca dương chạy được đi trọn tuyến**, **1/1 ca âm bị từ chối an
toàn**, **0 lượt Synthesis**, **0 lượt Vision**, **0 lần thử lại**,
`SILENT_QUALITY_FAILURE_COUNT = 0`, `DETERMINISTIC_ALL = true`.

Khoảng tin cậy Wilson 95 % cho tỉ lệ đi trọn tuyến ở ca dương:
**[0,19 ; 0,81]** trên n = 6. Khoảng ấy rộng gần hết trục — đó chính là điều nó
phải nói, và là lý do §6 cấm đọc 3/6 thành "50 %".

## 3. Cổng Stage A đã mở đúng luật

Ngưỡng đăng ký trước: ≥ 2 ca dương đi trọn tuyến trên 3 ca dương của Stage A,
≥ 1 ca âm bị từ chối an toàn, không có chấp nhận không an toàn, không có thất
bại im lặng, không có lỗi provider. Đạt được: 2 / 1, cả bốn điều kiện phụ đều
đúng ⇒ `MO_STAGE_B = true`. Cổng này chạy **trước** vòng B chứ không phải sau,
và nó đóng được — `test_10_bis` chứng minh bằng ba cách làm nó đóng.

## 4. Chế độ hỏng MỚI mà lượt controlled không thấy: `MODEL_MALFORMED_RELATION`

P03 và P05 hỏng **cùng một kiểu, và kiểu ấy chưa từng xuất hiện**: mô hình
**có** khai đủ hai quan hệ (`RAW_RELATION_COUNT = 2`), nhưng điền **sai tổ hợp
trường**, nên cả hai bị bác `STRUCTURED_RELATION_INVALID` ngay ở tầng lược đồ và
`ACTUAL_GIVEN_RELATION_COUNT` tụt về 0.

Phân biệt này đắt và bộ chấm được viết riêng để không lẫn:

- **không phải** `MODEL_UNDER_DECLARED` — mô hình không hề bỏ sót, nó khai rồi;
- **không phải** `SERVER_POINT_BINDING_GAP` — mọi nhãn điểm đều đã vào hợp đồng,
  `POINT_REFERENCE_VALIDATION = PASS`, `SOURCE_FACT_RESOLUTION = PASS`.

Trên bảng số thô, cả ba chế độ này đều hiện ra là `MISSING_RELATION_COUNT = 2`.
Chúng đòi ba bản sửa ở ba tầng khác nhau. Đây là lý do wave ghi
`FAILURE_ATTRIBUTION` theo tầng thay vì đếm pass/fail.

**Chưa sửa gì.** Sửa prompt hay lược đồ ngay trong wave đo là chấm lại điểm của
chính mình. Chế độ hỏng này là đầu vào cho wave sau.

⚠️ **Quy kết của P03/P05 tính SAU lượt chạy.** Nối quy kết trong runner bị mất
khi một lượt sửa abort giữa chừng trước live, nên hai file output live —
`CASE_RESULTS_REDACTED.json` (giữ nguyên nội dung, sha chuẩn LF `7b9fa1fc…`) và
`ACCEPTANCE_STATISTICS.json` — **không** mang quy kết cho hai ca này; bảng thống
kê chỉ đếm `ANALYZE_OUTPUT_INVALID: 1` (P06). Quy kết được tính từ bằng chứng đã
ghi, 0 request, và chỉ sống ở artifact dẫn xuất
`RELATION_QUALITY_BY_CASE.json → _QUY_KET_HAU_KIEM` cùng contact sheet. Một bản
trước của commit này từng ghi thêm trường vào chính file live; đã trả về byte gốc.

Một quan sát có ích, nhưng **chưa đủ mạnh để gọi là phát hiện**: cả hai ca hỏng
đều thuộc `EXPLICIT_SURFACE_RELATION`, còn cả hai ca `DEFINITIONAL_NORMALIZATION`
chạy được đều đi trọn tuyến — tức lớp cách viết mà bản vá prompt nhắm vào thì
chạy, lớp vốn đã được coi là dễ lại hỏng. Với n = 2 mỗi lớp, đó là **giả thuyết
cho wave sau**, không phải kết luận.

## 5. Ca âm N01 — kênh "khai thật một giả định" chạy đúng, và bộ đo của tôi chấm sai nó

N01 cố ý thiếu: đề nói đáy là tam giác vuông nhưng **không nói vuông tại đỉnh
nào**. Mô hình khai hai quan hệ:

| quan hệ | `model_assumption` | `usable_by_construction` |
|---|---|---|
| `WX ⊥ (XYZ)` — **đề nói thẳng** | `false` | `true` |
| `XY ⊥ XZ` — **đỉnh vuông tự chọn** | **`true`** | `false` |

Mô hình đánh dấu đúng cái nó phải đoán. Server loại quan hệ mang giả định ra
khỏi tập dùng được, rồi compiler từ chối bằng mã đã đăng ký
`BASE_PERPENDICULAR_RELATION_MISSING`. `UNSAFE_ACCEPTANCE = 0`,
`SYNTHESIS_REQUESTS = 0` — không có đường vòng nào dựng đại một cảnh.

⚠️ **Đính chính bộ đo, bảng số gốc giữ nguyên.**
`ACCEPTANCE_STATISTICS.json` ghi `HALLUCINATED_CRITICAL_FACT_COUNT = 2`. Con số
ấy **thổi phồng**: với ca âm, ground truth đặt `EXPECTED_GIVEN_RELATION_COUNT = 0`,
nên bộ đo đếm **mọi** quan hệ mô hình khai là "bịa" — kể cả `WX ⊥ (XYZ)`, thứ đề
viết nguyên văn. Số đúng là **1**. Chi tiết và cách sửa:
`NEGATIVE_SAFETY_RESULTS.json → DINH_CHINH_BO_DO`; trạng thái
`KNOWN_SCORER_DEFECT_NOT_FIXED_IN_THIS_WAVE` — sửa bộ chấm sau khi lượt đã chạy
là chấm lại điểm của chính mình.

Đây là **lần thứ hai trong hai wave liên tiếp** bộ đo của tôi sai về phía bi
quan. Lần trước là `sess.eval` trả giá trị JS chứ không trả chuỗi `"true"`, làm
cổng trình duyệt báo "không có canvas" trong khi cảnh đã dựng xong.

## 6. Cái wave này KHÔNG được dùng để nói

- **KHÔNG** đọc 3/6 thành "tỉ lệ thành công 50 %" của 12 ca. 5 ca chưa chạy, và
  chúng không phải 5 ca ngẫu nhiên — chúng là phần đuôi của một thứ tự đóng băng.
- **KHÔNG** tuyên bố độ phủ họ bài, độ chính xác sản phẩm, hay production
  readiness. `TOKEN_OPTIMIZATION = NOT_PRODUCTION_ESTABLISHED`.
- **KHÔNG** so token với một baseline synthesis — không có lượt ghép cặp nào.
- **KHÔNG** đọc `ANALYZE_P95 = 120 002,8 ms` như độ trễ: đó là **trần timeout**
  của P06, không phải một phép đo.
- 1/1 ca âm **không** là bằng chứng an toàn. Ba khiếm khuyết còn lại
  (N02 bộ số 3–4–5 trông như vuông · N03 thiếu đường cao · N04 mâu thuẫn) chưa
  ca nào được thử, và N02 là ca tôi ngờ nhất.

## 7. Ngân sách, và lượt vượt trần user đã duyệt

| | |
|---|---|
| đăng ký trước | 12 request |
| user duyệt | **13** (12 + 1), để không phải bỏ một ca đã đóng băng |
| **thực tiêu** | **8** — 2 ở lượt void + 6 ở lượt hợp lệ |
| trần tầng | `{vision: 0, analyze: 12, synthesis: 0}` — 0 byte Vision/Synthesis xuống transport |
| thử lại | 0 |

Trần là trần **HTTP ở transport**, không phải trần logic:
`HTTP_REQUESTS_SENT = 6`, `STAGE_SUM_EQUALS_SENT = true`, mỗi ca đúng 1 request.

**Lượt void.** Lần chạy đầu tiên hỏng vì **bộ đo**, không vì provider: một
`asyncio.run` cho mỗi ca đã đóng vòng lặp mang `AsyncHTTPTransport` dùng chung,
và — tệ hơn — kết quả bị quy thành `PROVIDER_INCOMPLETE`. Một sự cố bộ đo đội
lốt lỗi provider là đúng cái sẽ làm người đọc kết luận ngược. Sửa ở `19d1a6d`:
một vòng lặp cho cả wave, cộng `loai_su_co()` tách `APPARATUS` khỏi `PROVIDER`.
Giá phải trả: **2 request**. Bằng chứng giữ nguyên ở `attempt-1-void/`, không
xoá — trong đó P01 vẫn là một phép đo hợp lệ và được `--tiep-tuc` mang sang.

**P06 là lỗi provider thật**, không phải bộ đo: ReadTimeout sau 120 s,
`loai_su_co()` trả `PROVIDER`. Theo chính sách đăng ký trước, benchmark **dừng**
tại đó thay vì bỏ qua ca — bỏ qua một ca hỏng rồi chạy tiếp là cách êm ái nhất
để một bộ số tự đẹp lên.

## 8. Phát lại trình duyệt

P02 và P04: **11/11 ô kiểm** ở cả 1440×900 và 390×844 (DPR 2), **0 request model**
— envelope đọc từ file, mọi `/api/*` chặn ở biên mạng. Ảnh:
`browser/P02/`, `browser/P04/`, và `CONTACT_SHEET.png` (12 hàng, 5 hàng chưa
chạy ghi rõ là chưa chạy).

⚠️ **P01 không phát lại được** — lượt void **chưa bao giờ ghi envelope ra đĩa**
(nó chỉ để lại ba file ở `attempt-1-void/`), và `--tiep-tuc` chở kết quả chấm
sang lượt 2 nhưng **không** chở envelope. Đã kiểm: không bản envelope P01 nào
còn tồn tại, kể cả trong worktree thực thi. Đó là **lỗ hổng công cụ của tôi**,
không phải lỗi sản phẩm: kết quả compiler của P01 vẫn hợp lệ. Bản sửa đúng chỗ
là runner ghi envelope **ngay khi mỗi ca xong**, không đợi cuối lượt. **Không**
chạy lại một request chỉ để lấy ảnh.

`USER_VISUAL_APPROVAL = PENDING` — chưa ai duyệt ảnh.

Hai lỗi thẩm mỹ của **chính contact sheet**, không phải của sản phẩm: font vẽ ảnh
không có glyph `⊥` nên P04/P05/P06 hiện `□` ở chỗ ký hiệu vuông góc (đề gốc trong
`CASE_REGISTRY.json` đúng), và cột lớp cách viết đè lên dòng đề.

## 9. Chỗ tôi đoán sai

Trước lượt live, tôi dự đoán offline rằng **P02 sẽ hỏng** ở
`SERVER_POINT_BINDING_GAP`. P02 đi trọn tuyến, quan hệ đúng 2/2, đáp số 14 đúng.
Dự đoán của tôi sai, và nó sai theo hướng bi quan — cùng hướng với hai lỗi bộ đo
ở §5. Ghi lại vì một chuỗi sai cùng hướng là tín hiệu về **cách tôi ước lượng**,
không phải ba sự cố rời rạc.

## 10. Việc kế tiếp

`RETRY_REMAINING_PREREGISTERED_CASES_LATER` — chạy **đúng 5 ca còn lại theo đúng
thứ tự đã đóng băng** (P07, P08, N02, N03, N04), không đổi ca, không thêm ca.
Băm chính tắc của dataset (đề + đáp án + **thứ tự**) khoá điều đó: xoá một ca
hoặc đổi thứ tự là test ĐỎ.

Hai món nợ riêng, **không** trộn vào lượt đo: chế độ hỏng
`MODEL_MALFORMED_RELATION` (§4) và lỗi bộ chấm ca âm (§5).

## 11. Lệch khỏi đặc tả — khai thẳng

- **Ba commit thay vì hai.** Đặc tả cho phép một commit trước live và một sau
  live. `19d1a6d` là commit thứ ba bắt buộc: bản sửa runner sau sự cố bộ đo ở
  lượt void (§7), kèm bằng chứng lượt void. Không amend để cho vừa con số — gộp
  nó vào commit khác là giấu việc bộ đo từng hỏng.
- **Commit sau live mang thêm tooling**: `run_multicase_benchmark.py` (dựng
  contact sheet, `--tiep-tuc`) và `compiler-scene-replay.mjs` (tham số hoá
  `--ca`, ba chỗ đo sai ở §8/§5). Thiếu chúng thì artifact không tái lập được.
- **Commit sau live sửa `docs/CODE_INDEX.md`**: entry `compiler-scene-replay.mjs`
  đã sai về chính file wave này đổi (chín ô, nhãn cứng `S A B C`), và bốn runner
  của tuyến quan hệ có cấu trúc chưa có entry nào. Chỉ tài liệu, 0 dòng mã.
- **Ngân sách request** — xem §7: duyệt 13, tiêu 8.

**KHÔNG làm trong wave này — nợ ghi ngược còn nguyên:** `STATUS_LEDGER.md` và
mục `### 1a-*` của `CURRENT_STATE.md` vẫn thiếu cho **tám** wave liên tiếp,
`PRIMITIVE_COMPILER_AB_TOKEN_LATENCY_BENCHMARK` (chỉ có hàng ledger, thiếu mục
`1a-*`) tới wave này. Đặc tả §15 liệt kê nội dung commit sau live mà không có
hai sổ ấy, và bốn đặc tả trước còn cấm backfill thẳng. Cộng với bảy wave
2026-09-15 đã biết. Nên là một wave tài liệu riêng, không trộn vào lượt đo.

## 12. Kiểm cuối

Full backend trên cây nguồn: **1 đỏ** —
`test_holdout_readiness_7b.py::test_bao_cao_da_sinh_va_KHONG_TROI`. Nó đòi báo cáo
Phase 7B ghi `READY_FOR_PHASE7B: NO` khi **cây làm việc bẩn**; cây nguồn luôn bẩn
vì xoá `favicon.svg` của user, thứ wave không được đụng. Không phải hồi quy sản
phẩm; phán quyết cuối lấy ở lượt chạy trong worktree sạch tại END_HEAD.

## 13. Artifact

`docs/evaluation/geometry/photo-problem-to-scene/multicase-benchmark/` — 33 file:
`CASE_REGISTRY` · `GROUND_TRUTH` · `BENCHMARK_MANIFEST` · `DATA_LEAKAGE_PROOF` ·
`LAUNCHER_OFFLINE_PROOF` (27 test, 10 kịch bản lỗi, 0 request) · `PRECHECK` ·
`CASE_RESULTS_REDACTED` · `ACCEPTANCE_STATISTICS` · `REQUEST_BUDGET_PROOF` ·
`STAGE_A_GATE` · `RELATION_QUALITY_BY_CASE` · `COMPILER_QUALITY_BY_CASE` ·
`NEGATIVE_SAFETY_RESULTS` · `TOKEN_USAGE_BY_CASE` · `LATENCY_BY_CASE` ·
`BROWSER_REPLAY_RESULTS` · `REPLAY_ENVELOPES` · `SECRET_SCAN` ·
`CONTACT_SHEET.png` + manifest · `attempt-1-void/` · `browser/`.

`SECRET_SCAN = CLEAN`: 33 file artifact + báo cáo này, 0 phát hiện, **9/9 mẫu quét đều có cửa sổ chứng**
(mồi giả bị bắt) — kể cả phép so với chính khoá thật, mà khoá không được in ra ở
bất kỳ đâu.
