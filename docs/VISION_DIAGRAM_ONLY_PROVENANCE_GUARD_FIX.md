# VISION_DIAGRAM_ONLY_PROVENANCE_GUARD_FIX

> Nhánh `feat/photo-problem-to-scene` · 2026-09-14 · START_HEAD `d8ad614` · `main` giữ `085cae6`.
> Lỗi sửa: **`DIAGRAM_OBSERVATION_PROVENANCE_LEAK`** — quan sát từ hình lọt vào trường mang nghĩa "đề phát biểu".
> Bằng chứng: `docs/evaluation/geometry/photo-problem-to-scene/diagram-only-provenance-guard/`.
> Ảnh ghép (chứa ảnh C03, không commit): `D:\tmp\algo-sim-diagram-only-provenance-guard\evidence\C03_CONTACT_SHEET.png`.

```text
VISION_DIAGRAM_ONLY_PROVENANCE_GUARD = FAIL   ← lượt live duy nhất: PROVIDER_ERROR ReadTimeout, KHÔNG có đầu ra mô hình
guard tất định (offline, đầu ra THẬT C03)     = XANH — 3 quan hệ cách ly, bản công khai rỗng dữ kiện, 7 quan sát giữ
MODEL_CONTRACT_ALIGNMENT                     = NOT_MEASURED (không có đầu ra để đo prompt mới)
request thật                                  = 1 (vision) · analyze 0 · synthesis 0 · retry 0 · request thứ hai KHÔNG gửi
NEXT_ACTION                                   = PROVIDER_FAILURE_DIAGNOSIS
```

## 1. Kết luận

Bản sửa làm đúng việc được giao, và điều đó đo được **offline**:
- **Prompt:** thêm luật "dữ kiện chỉ từ chữ".
- **Guard tất định:** chạy sau Pydantic, trước mọi consumer.
- **Runner:** chấm độc lập bản công khai.

Test viết trước ở START_HEAD cho 14 đỏ / 20 xanh, sau bản sửa 34 xanh. Bảy phép tiêm đỏ đúng test và hoàn lại trùng byte. Phát lại đầu ra thật của C01/C02 cho bản công khai và phán quyết trùng từng trường.

**Nghiệm thu live không đạt**, nhưng không vì guard hay mô hình. Request vision duy nhất (run `20260914T154550Z-d65ee279`) đã gửi, rồi nhận `ReadTimeout` sau **60 223 ms**, đúng trần `VISION_TIMEOUT_SECONDS = 60`. Không có HTTP status, không có `usageMetadata`, không có đầu ra.

Hệ quả:
- JSON, Pydantic, mã từ chối, RAW/SAFE facts đều **không đo được**.
- Lỗi provider không bao giờ được tính là từ chối an toàn.
- Theo spec, **không** gửi request thứ hai.

Một mẫu không đủ để quy nguyên nhân timeout. Lượt C03 trước với prompt cũ mất 6,86 s. Thân hai request chỉ khác system prompt (§9), nhưng điều đó **không** chứng minh prompt gây ra timeout.

## 2. Tiền kiểm — `PRECHECK.json` = PASS (0 request)

Kho `D:\Documents\projects\algo-sim` · nhánh đúng · HEAD `d8ad614` · `main` `085cae6` · cây sạch, 0 stash.

| thứ được kiểm | giá trị |
|---|---|
| C03 SHA-256 | `c416ce92…43ad` |
| `RUN_GROUND_TRUTH.json` | `5a4d21c7…9d8` (C03 kỳ vọng `MISSING_PROBLEM_TEXT`) |
| candidate | `b32887a9c2283ca2` |
| `CACHE_VERSION` | 95 |
| danh tính | `gemini-2.5-flash`, prompt `b499dc7a…`, lược đồ `77dfe727…` / `46810954…` |
| artifact lỗi C03 | có — `MISSING_PROBLEM_TEXT`, lời đề rỗng, `given_relations` 3 mục |
| khoá Gemini | có mặt, không in |

## 3. Bảng nguồn dữ kiện — `DIAGRAM_ONLY_FIELD_CLASSIFICATION.json`

Phân loại theo **nơi dùng thật** ở `d8ad614`, không theo tên trường:

| lớp | trường | dùng ở đâu |
|---|---|---|
| `TEXT_DERIVED_FACT` | `problem_text_verbatim/normalized` | → `assessment.problem_text` → ô dựng → `/api/analyze` |
| | `math_expressions` | UI "Công thức đã chuẩn hoá" + bộ chấm |
| | `given_relations` | phản hồi công khai + bộ chấm |
| | kích thước, yêu cầu bài | không có trường riêng — nằm trong văn bản/công thức |
| `OBSERVATION_ONLY` | `named_points/lines/planes/solids` | UI không hiện, không đi analyze |
| | `has_diagram` | |
| | `diagram_observations` | UI dưới nhãn "chỉ để tham khảo" |
| `METADATA` | `text_diagram_conflicts`, `uncertain_tokens`, `missing_regions`, `confidence`, assessment/provenance/image | |

**Phát hiện:** trong sản phẩm, `given_relations` **không** tới `/api/analyze`, vì payload dựng chỉ là văn bản. Nhưng nó nằm trong phản hồi công khai với nghĩa "đề cho", và bộ chấm dùng nó làm dữ kiện. Ca C03 của runner cũ không soi trường dữ kiện nào.

## 4. Test đỏ trước — `RED_BEFORE_GREEN_AFTER.json`

`backend/tests/test_vision_diagram_only_provenance_guard.py` chạy trên fixture là **đầu ra thật** của C03 đã che: `tests/fixtures/c03_vision_extraction_replay_redacted.json`. Fixture bỏ phong bì provider, URL, khoá, ảnh; băm canonical `6c0bbd8c…`.

| hợp đồng | ở `d8ad614` |
|---|---|
| **A** payload công khai không mang dữ kiện khi không có lời đề (3 biến thể) | **đỏ 3/3** |
| **B** quan sát giữ ở vùng quan sát | xanh (hồi quy) |
| **C** mã `MISSING_PROBLEM_TEXT` | xanh ×3 |
| **D** đường analyze cũ không tới pipeline; runner C03 chỉ gọi vision, không cảnh | xanh ×4 |
| **E** guard đúng khi mô hình vẫn trả dữ kiện: E1 ×3, E2 cache, E3 runner báo raw/công khai/cách ly, E4 runner FAIL khi guard bị vô hiệu | **đỏ 6/6** |
| **F** telemetry: tên trường · số mục · SHA-256, không nội dung thô | **đỏ 3/3** |
| **G** tài liệu có lời đề không đổi | xanh ×2 |
| **H** thiếu lời đề không rò giữ nguyên | xanh |
| **I** fixture giao diện = bản công khai backend dựng | **đỏ** |
| **I** giao diện vẽ bản ấy: quan sát dưới nhãn tham khảo, ô trống, nút khoá | xanh |
| **J** lỗi provider/JSON/Pydantic không phải từ chối an toàn (API ×4, runner ×3) | xanh |
| luật prompt 4/9 | **đỏ** |
| lược đồ gửi không đổi | xanh |

Sau bản sửa: **34/34 xanh**.

## 5. Bản sửa (commit `f4fa3e7`)

**Prompt `transcribe.md` — sửa hai luật, 1874 → 1967 byte, trong ngân sách 1970:**
- Luật 4: *"Dấu, nhãn, quan hệ chỉ thấy trên hình → `diagram_observations`."*
- Luật 9: *"Không có đề chữ đọc được: để rỗng hai trường văn bản và mục 3–4."*

Mô hình không có trường mã từ chối, nên "trả `MISSING_PROBLEM_TEXT`" được thực hiện bằng các trường dữ kiện rỗng cộng phán quyết của server. Mã ấy không được đưa vào prompt. Không thêm ví dụ, không thêm trường lược đồ.

**Guard `apply_diagram_only_provenance_guard`** chạy trong `ExtractionResult.__post_init__`, nên không lối dựng nào bỏ qua được:
- **Chỉ khi** phán quyết là `MISSING_PROBLEM_TEXT`: `FACT_BEARING_FIELDS` bị cách ly khỏi bản công khai. Không cắt, không đoán lại, không chép sang quan sát.
- `raw_extraction` chỉ phục vụ bộ đo; `to_response` không đọc nó.
- Cache giữ bản mô hình; guard chạy lại tất định mỗi lần trúng cache.
- Log `VISION_DIAGRAM_FACTS_QUARANTINED` chỉ mang tên trường, số mục và SHA-256.
- Tách rõ ba chỉ số: `RAW_MODEL_FACT_FIELDS_EMPTY`, `SAFE_PUBLIC_FACT_FIELDS_EMPTY`, `QUARANTINED_FACT_COUNT`.

**Runner:** ca C03 chấm bản công khai theo `TRUONG_DU_KIEN_C03`, khai riêng, không đọc tập trường của sản phẩm. `C03_SAFE_REJECTION` đòi thêm bản công khai sạch. `{ca}_RAW_EXTRACTION.json` ghi cả `extraction` (bản mô hình, chỉ ở thư mục chạy) lẫn `public_extraction`.

**Không tuyên bố** gì về nguồn gốc dữ kiện trong tài liệu vừa có chữ vừa có hình.

## 6. Tiêm lỗi — `FAULT_INJECTIONS.json`: 7/7 đỏ, 7/7 trùng byte

Mỗi phép sửa bằng Edit, chạy test, hoàn lại bằng Edit, rồi `cmp` với bản chụp.

| phép | tiêm | đỏ |
|---|---|---|
| F1 | bỏ qua guard | 12 (A, E1–E3, F, I) |
| F2 | bỏ `given_relations` khỏi trường cách ly — lọt payload | 12 |
| F3 | chép quan hệ bị cách ly thành văn bản đề | 15 (thêm C) |
| F4 | `/api/analyze` dạng ảnh cho ảnh chỉ có hình đi dựng cảnh | 5 (D1 ×3 + hai test cũ) |
| F4b | nút dựng mở khi ô trống (giao diện) | 3 (gồm test UI C03) |
| F5 | telemetry ghi nội dung thô | 3 (F) |
| F6 | áp guard cho mọi ảnh có hình | G[chữ + hình]; phát lại C01/C02 thật `PARITY = FAIL` |

## 7. Cổng offline — tại `e8560e7`, cây sạch, trước request

| cổng | kết quả |
|---|---|
| pytest | **5153 passed, 0 failed**, 1 skipped |
| vitest | **870/870** |
| `npm run build` | xanh |
| `freeze_evaluation_candidate --verify` | khớp `29720197…` |
| `lock_cache_identity --verify` | khớp |

Pytest bao trùm: test mới · đọc ảnh/API/lược đồ gửi · runner/checkpoint/scorer/repair-trace · ngân sách request · khử bí mật · danh tính.

**Phát lại đầu ra thật** — `GUARD_BEFORE_AFTER.json`:
- `C01_C02_BEHAVIOR_PARITY = PASS`: bản công khai và phán quyết trùng từng trường, 0 sự kiện.
- `C03_GUARD = PASS`.

Không chạy P1–P7 hay cổng camera, vì renderer không đổi.

## 8. Danh tính, cache, candidate — `IDENTITY_AND_CACHE_DECISION.json`

| thứ | trước → sau |
|---|---|
| prompt đọc ảnh | `b499dc7a…` → `748dfd3b…` |
| lược đồ gửi / đầy đủ | `46810954…` (1387 byte) / `77dfe727…` (1564 byte) — **không đổi** |
| `VISION_SCHEMA_IDENTITY` | không đổi |
| khoá danh tính cache | chỉ `prompts` đổi `c50c8c6b…` → `dceff16e…` |
| `CACHE_VERSION` | 95 → 95 |
| candidate | `b32887a9…` → `29720197…` (94 file) |

**Chỉ `transcribe.md` đổi, chứng minh bằng máy:** dựng lại băm `prompts` với `transcribe.md` bản `d8ad614` cho đúng `c50c8c6b…`. Bốn thành phần còn lại trùng. `tests/photo_problem_identity.py` giữ bằng chứng này, và hai ô ghim lịch sử được cập nhật kèm phép dựng lại.

**Không bump `CACHE_VERSION`:**
- Cache `/api/analyze` khoá theo văn bản, envelope do skill tầng B sinh — không đổi byte nào.
- Cache ảnh (trong tiến trình) đã tự đổi khoá theo băm prompt.
- Cùng quyết định với `8bb94ce`.

**Candidate đóng băng lại** trên cây sạch tại `f4fa3e7`, ở **commit riêng** `e8560e7`, trước request. Lệch candidate đã khai ở `CANDIDATE_DIVERGENCE.json`.

## 9. Lượt live — `REQUEST_GATE_PROOF.json` = PASS · `C03_LIVE_RESULT_REDACTED.json`

Trước request, trên cây sạch `e8560e7`:
- Tiền kiểm lúc live PASS: danh tính sau sửa, candidate đóng băng tại đúng commit cha, guard có mặt.
- Cổng trần 1 chặn request thứ 2 trước transport.
- Tự kiểm bẫy tầng B PASS.

Ngân sách: vision 1 · analyze 0 · synthesis 0 · một lần thử · tổng 1 · retry 0 · một lượt đầy đủ.

| trường | giá trị |
|---|---|
| request | gửi 1 · chặn 0 · `logical_call` 1 · `attempt` 1 · retry 0 |
| kết quả | HTTP status **không có** · `ReadTimeout` · 60 223 ms |
| đầu ra mô hình | **KHÔNG** · JSON / Pydantic / phán quyết không chạy |
| tầng B | analyze 0 · synthesis 0 · bẫy bị gọi 0 · `STAGE_B_HTTP_ATTEMPTS` 0 |
| cảnh | không tạo |
| runner | `status = ERROR` · `C03_SAFE_REJECTION = false` · exit 1 |
| log guard bắt trong tiến trình | 0 (không có đầu ra để guard xử lý) |

**Nguồn gốc thân request.** Thân request dựng lại offline bằng đúng đường của runner:
- prompt đã commit → `a18132a7…` = **thân request live**;
- prompt `d8ad614` → `02b2104d…` = thân request của lượt C03 trước.

Vậy hai request chỉ khác system prompt; ảnh chuẩn hoá, user text, lược đồ gửi và cấu hình sinh giống hệt.

**Token — `TOKEN_USAGE.json`:**
- Provider báo 0: không có `usageMetadata`. Đây **không** phải khẳng định request miễn phí; cách tính cho request timeout là không biết.
- `TEXT` prompt ước lượng ≈ 573 so với 548 đo trước. Tỉ lệ byte, **không đo** — không gọi `countTokens` để giữ đúng một request.
- Không tuyên bố tối ưu.

Lần chạy đầu của công cụ bằng chứng dừng sau khi ghi `C03_LIVE_RESULT_REDACTED.json`. Traceback bị lấn bởi lỗi huỷ vòng lặp asyncio, không lưu được. Chạy lại: tệp đã có trùng từng trường bản dựng lại, hai tệp còn lại được ghi. Nguyên nhân lần dừng đầu **chưa xác định**.

## 10. Giao diện — phát lại, 0 request model (`browser/BROWSER_REPLAY.json`)

Lượt live không có đầu ra. Nguồn phát lại là **đầu ra thật của run `20260914T144655Z-49ffa191` cho đi qua guard đã commit** (`REPLAY_UI_OF_PRIOR_REAL_OUTPUT_THROUGH_COMMITTED_GUARD`).

Cả **1440×900** và **390×844** đạt đủ:
- **G1** thông báo thiếu lời đề ở `role=alert`;
- **G2** nút dựng vô hiệu kể cả khi bấm, Enter, tích xác nhận; 0 `/api/analyze`;
- **G3** không cảnh 3D;
- **G4** Thay/Xoá ảnh dùng được;
- **G5** không tràn ngang;
- **G6** không chữ "điện thoại thật";
- **G7** 7/7 quan sát dưới nhãn "chỉ để tham khảo", không khối công thức, 0 chuỗi bị cách ly trên trang, ô dựng trống.

Lỗi trang: 0.

## 11. Cổng chấp nhận — `ACCEPTANCE_GATES.json` = FAIL

**Đạt:**
- analyze 0 · synthesis 0 · không cảnh;
- quan sát hiện + nút khoá · phát lại 2 khung;
- 0 request model khi phát lại · 0 bí mật (trước báo cáo);
- đúng 1 request · 0 retry · `main` không đổi.

**Không đạt — cả bảy đều cần đầu ra mô hình:**
- HTTP 200 · JSON · Pydantic · mã `MISSING_PROBLEM_TEXT`;
- không suy lời đề · `SAFE_PUBLIC_FACT_FIELDS_EMPTY` · quan sát không thành dữ kiện.

## 12. Commit và artifact

| commit | nội dung |
|---|---|
| `f4fa3e7` | `fix(vision)` — bản sửa + test, trước request |
| `e8560e7` | `eval:` — đóng băng lại candidate, commit riêng theo cơ chế hiện có, trước request |
| commit thứ ba | báo cáo này + artifact đã che |

Không trailer, không merge, không push.

Commit thứ hai **lệch** so với "Commit 1 / Commit 2" của spec. Lý do:
- Manifest candidate chỉ đóng băng được trên cây sạch **sau** commit bản sửa.
- Cổng niêm phong đòi cây sạch.
- Làm vậy cho request chạy trên cây sạch với mọi cổng offline xanh.

**Không commit:** ảnh C03, ảnh ghép, ảnh chụp giao diện, response thô của provider, prompt/base64/khoá. `run/` và `evidence/` đầy đủ nằm ở `D:\tmp\algo-sim-diagram-only-provenance-guard\`.

`STATUS_LEDGER.md` và `CURRENT_STATE.md` **chưa** ghi — nghiệm thu live chưa đạt.

## 13. Việc kế tiếp — `PROVIDER_FAILURE_DIAGNOSIS`

Nhãn `SYNTHESIS_MEMORY_DECLARATION_SCHEMA_PROMPT_ALIGNMENT` trong khuôn báo cáo giả định guard **đạt** live; ở đây chưa đạt.

Wave chẩn đoán cần trả lời:
- Timeout ở tầng mạng hay provider?
- Thời gian suy nghĩ của `gemini-2.5-flash` có phụ thuộc prompt mới không?
- Trần 60 s có còn hợp lý không?

Rồi mới quyết định một lượt C03 mới trên candidate `29720197…`. Wave này không đổi timeout, không thử lại, không gửi request thứ hai.
