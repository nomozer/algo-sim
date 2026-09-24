# PHOTO_PROBLEM_TO_SCENE_END_TO_END_IMPLEMENTATION (2026-09-13)

> Nhánh `feat/photo-problem-to-scene`, tách từ `085cae6`. **CHƯA merge vào
> `main`** — blocker ở §10. Mọi số dưới đây đo trên nhánh.

Chụp hoặc tải ảnh đề hình học → đọc nội dung → chuẩn hoá chữ và công thức →
bản ghi có cấu trúc → người học xem lại, sửa, xác nhận → **văn bản** đi đúng
đường gõ tay → kiểm chứng → dựng 3D từng bước.

## 0. Kết luận, tách riêng

- **Ảnh tải lên được?** Có — nút *Chụp ảnh* (`capture="environment"`) và *Tải
  ảnh* ở khung soạn; PNG/JPEG/WEBP; định dạng soi theo NỘI DUNG. Đã kiểm trên
  Chrome thật ở 1440×900 và 390×844 — **bằng chứng FIXTURE**.
- **Model đọc được nội dung?** **CHƯA CHỨNG MINH.** Phiên không có credential:
  `REAL_PROVIDER_EVIDENCE = NOT_ESTABLISHED`. Hợp đồng đọc ảnh chỉ được kiểm
  bằng provider giả.
- **Semantic program hợp lệ?** Có, ở mức sau: văn bản rút từ ảnh đi
  `run_pipeline` THẬT; tầng B phát lại byte đóng băng của `thesis-final` (kể cả
  lượt sửa của p3) ⇒ chóp + thiết diện, cầu, trụ, nón đều `status = ok`.
- **Hình 3D dựng được?** Có — `scene3d` không rỗng và có trace ở cả bốn họ;
  canvas hiện ở cả hai khổ (fixture).
- **Dữ liệu thiếu bị từ chối an toàn?** Có — ảnh chỉ có hình ⇒
  `MISSING_PROBLEM_TEXT`, không tới tầng B, không dựng; đề ngoài năng lực vẫn
  `unsupported`; dữ kiện không có trong đề bị cổng grounding chặn.
- **Fixture và provider thật là hai loại bằng chứng khác nhau** — §9 ghi loại
  của từng ô.

## 1. Đường xử lý TRƯỚC wave (đo, không nhớ)

```text
START_HEAD             = 085cae6 · WORKING_TREE_BEFORE = CLEAN
CAMERA_PATCH_PRESENT   = YES — cam.up.set(0,0,1) ở scene3d-view.tsx:769, trước new OrbitControls (:779)

IMAGE_UPLOAD_CURRENTLY       = CÓ MỘT PHẦN — nút "+", phân loại theo ĐUÔI tệp, xem trước, bỏ tệp;
                               không chụp, không xoay, không xem lại
IMAGE_TRANSPORT_CURRENTLY    = JSON base64 trong POST /api/analyze (InputPayload type="image")
VISION_PROVIDER_CURRENTLY    = Gemini inline_data qua call_gemini; model = GEMINI_MODEL
IMAGE_TO_SEMANTIC_CURRENTLY  = ingest_to_text → skill transcribe.md (viết cho đề TIN HỌC, văn bản tự do,
                               không lược đồ) → đẩy THẲNG vào pipeline, người học không xem lại được
VALIDATION_CURRENTLY         = chỉ magic bytes + trần 4 MB; không giải mã, không EXIF, không trần điểm ảnh
RENDERER_REUSE_POSSIBLE      = YES
MISSING_LINKS                = giải mã/chuẩn hoá/gỡ EXIF · output có cấu trúc + chỗ không chắc · màn xem lại ·
                               chụp · xoay · cache theo hash ảnh · prompt hình học · chống gửi lặp
```

## 2. Phản biện — ghi TRƯỚC khi làm

1. **Multipart là sai hướng.** Kiến trúc sẵn có là JSON base64; multipart kéo
   thêm `python-multipart`. Giữ JSON base64 (§7 "ưu tiên kiến trúc sẵn có").
2. **Nguồn gốc dữ kiện (chữ/hình) KHÔNG đi vào Semantic Program.** Làm vậy là
   đổi bề mặt mô hình của tuyến dựng hình, và mở cửa cho "quan sát từ hình" thành
   dữ kiện — trái R0 và §2. Nguồn gốc nằm ở tầng A + màn xem lại; tầng B nhận
   văn bản đã xác nhận; `grounding_gate` vốn buộc dữ kiện truy về đề chữ.
3. **"12 ảnh thật" không dựng được trong phiên.** Bộ nghiệm thu là 12 ảnh
   **TỔNG HỢP** tất định, nhãn `SYNTHETIC_RENDERED`; `REAL_PHOTO_CORPUS =
   NOT_ESTABLISHED`.
4. **Không có credential** (không `GEMINI_API_KEY` trong môi trường, không
   `backend/.env`, Docker tắt). `.secrets/` là service account của dịch vụ khác —
   không dùng.
5. **Lược đồ chỉ xanh trên fixture chưa chứng minh gì với API thật.** Tiền lệ
   trong `gemini.py`: lược đồ xanh offline mà API trả HTTP 400 mọi lượt.
6. **Huỷ chỉ ở phía client.** FastAPI không tự huỷ lượt gọi provider khi client
   ngắt.
7. **Cache ảnh chỉ trong bộ nhớ tiến trình.** Lưu bền cần bảng mới + migration,
   và lưu kết quả đọc ảnh người dùng.
8. **Dự kiến không bump `CACHE_VERSION`** — xác nhận ở §4, đúng thủ tục cổng.
9. **"Tối đa 3 commit" mâu thuẫn lệ đóng băng candidate ở commit riêng.** Theo
   yêu cầu: gộp đóng băng vào commit 3, khai lệch.

## 3. Đã triển khai

**Tầng A** — `backend/app/ingestion/`:

- `image.py` — thẩm quyền DUY NHẤT chuẩn hoá ảnh: base64 có trần → định dạng
  theo nội dung, so MIME khai → header → trần **40 MP kiểm TRƯỚC giải nén** →
  giải mã → xoay EXIF → xoay của người học (`transpose`, hoán vị chính xác) → RGB
  nền trắng → thu nhỏ về cạnh 3072 → **SHA-256 trên điểm ảnh** → mã hoá JPEG từ
  `frombytes` (không mang EXIF/GPS/ICC). Trần tệp 10 MB.
- `image_extraction.py` — `ImageProblemExtraction` (`extra="forbid"`, NFC, gỡ
  ký tự nhóm C); lược đồ Gemini **viết tay, không `$ref`** (test khoá khớp
  model và khoá rằng `_sanitize_gemini_schema` không bỏ nó); `assess_extraction`
  **tất định**: `IMAGE_NOT_READABLE` · `MISSING_PROBLEM_TEXT` ·
  `UNSUPPORTED_PROBLEM`, cờ xem lại `UNCERTAIN_TOKENS` · `MISSING_REGIONS` ·
  `TEXT_DIAGRAM_CONFLICT` · `AMBIGUOUS_DIAGRAM` · `LOW_CONFIDENCE` ·
  `DIAGRAM_OBSERVATIONS_NOT_USED`; cache LRU 64 mục; trần 2 lượt đồng thời; hai
  yêu cầu cùng khoá dùng chung một lượt gọi.
- `POST /api/image/extract` — cổng lượt thử (dùng CHUNG `_cong_luot_thu` với
  `/api/analyze`) → chuẩn hoá (400, không cần key) → key (503) → provider
  (429 · 502 · 503; thông điệp không mang chi tiết provider).
- `call_gemini`: `max_attempts` / `timeout_seconds` chỉ **hạ** được trần; đường
  ảnh dùng 2 lượt / 60 s; mặc định mọi stage khác không đổi.
- `skills/transcribe.md` viết lại cho hình học (ngân sách 1050 → 1970 byte, lý
  do ghi trong `test_prompt_size_guard.py`).
- Nhánh `image` cũ của `ingest_to_text` ủy cho hai module trên và **đóng chặt
  hơn**: bị từ chối hoặc cần xem lại ⇒ `IngestError`.

**Tầng B** — không đổi một dòng. Văn bản đã xác nhận đi `analyzeViaServer`
dạng `text`.

**Giao diện** — `ProblemInput.tsx` + `PhotoProblemPanel.tsx` +
`photo-problem-flow.ts` (trạng thái thuần): Chụp/Tải/`+` cùng một luồng · xem
trước · xoay/thay/xoá (huỷ yêu cầu đang đọc) · bản chép nguyên văn · công thức
chuẩn hoá · chỗ đọc chưa chắc · vùng mất · mâu thuẫn chữ–hình · quan sát từ hình
gắn nhãn *chỉ để tham khảo* · ô nội dung có `label` · ô xác nhận · vùng
`aria-live`. Bị từ chối hoặc cần xác nhận ⇒ phải đánh dấu mới dựng. Dựng không
thành ⇒ GIỮ ảnh và nội dung. CSS chỉ THÊM lớp (182 dòng thêm, 0 dòng xoá).

## 4. Danh tính — candidate, cache, prompt

```text
MODEL_FACING_CHANGED  = YES — CHỈ bề mặt đọc ảnh (transcribe.md + VISION_RESPONSE_SCHEMA)
SEMANTIC_SURFACE      = KHÔNG ĐỔI — thẻ văn phạm, synthesis_schema, analyze_schema, capability giữ từng byte
CACHE_VERSION         = 95 → 95
CANDIDATE             = 96a9368b… (92 file) → 13e2aaaa… (94 file)
```

- **Không bump.** Cổng `test_cache_identity` tự nêu thủ tục: *"envelope đã cache
  CÒN đúng ⇒ chỉ khoá lại"*. Cache `/api/analyze` khoá theo VĂN BẢN; prompt đọc
  ảnh không tham gia ánh xạ văn bản → envelope. Khoá làm lại bằng
  `lock_cache_identity.py`; bản khoá mới cho thấy ĐÚNG MỘT thành phần đổi.
- **`prompts` 55ac1ca6 → c50c8c6b — chứng minh bằng máy, không bằng lời.**
  Thành phần ấy băm GỘP mọi skill. `tests/photo_problem_identity.py` dựng lại
  đúng giá trị lịch sử từ skill hiện tại, chỉ trả `transcribe.md` về băm tại
  `085cae6`. Có hai phép tiêm (sửa thêm một skill tầng B · thêm một skill mới)
  cho thấy bằng chứng ấy đỏ được.
- **Năm ô danh tính lịch sử** (oblique ellipse ×2, nonconvex, thesis runner
  alignment, point initialization) khai đính chính và gọi bằng chứng trên;
  **không artifact nào bị sửa**. `test_B1_G1` DỰNG LẠI băm model-facing của con
  dấu thesis-final thay vì nới cờ bằng lời.
- `CANDIDATE_DIVERGENCE.json` khai candidate mới, giữ lịch sử băm cũ, thêm lý do
  wave (3). Đóng băng lại candidate ở commit 3.

## 5. Kiểm thử

Backend mới: `test_image_normalization.py` · `test_image_extraction.py` ·
`test_image_extract_api.py` · `test_photo_problem_semantic_integration.py` ·
`test_photo_problem_identity.py`. Frontend mới: `photo-problem-flow.test.ts` ·
`photo-problem-panel.test.tsx` · `extract-image.test.ts` + mở rộng
`input.test.ts`.

**Tầng B phát lại theo thứ tự lượt gọi.** `replay_negative_boundaries` giữ MỘT
bản ghi mỗi chặng; phát lại p3 bằng nó ra `ir_static` y như lượt đầu — trông
giống hệt một hồi quy sản phẩm. Thêm `doc_raw_theo_thu_tu` +
`ProviderPhatLaiTheoThuTu` (hết bản ghi mà pipeline còn gọi ⇒ ném; còn thừa ⇒
đỏ).

**Phép tiêm — mỗi phép đỏ đúng chỗ rồi gỡ; candidate về đúng `13e2aaaa…`:**

| # | phép tiêm | bị bắt ở |
|---|---|---|
| 1 | bỏ nhánh `MISSING_PROBLEM_TEXT` | 4 test ở 4 file |
| 2 | bỏ xoay EXIF | 3 test tham số + `--kiem` `EXIF_ORIENTATION = FAIL` |
| 3 | bỏ kiểm `requestId` | test đọc → xoay → đọc lại |
| 4 | ảnh gửi đi mang EXIF nguồn | test GPS + `--kiem` `EXIF_GPS_REMOVED = FAIL` |
| 5 | bỏ `CACHE_VERSION` khỏi khoá | 2 test cache |
| 6 | bỏ chặn `build-start` | 2 test |
| 7 | chèn bản chép qua `dangerouslySetInnerHTML` | test thoát ký tự |
| 8 | trang: so văn bản gửi đi với bản CHƯA sửa | ô 6, cả hai khổ |
| 9 | trang: khối ảnh rộng 900 px | ô 8 ở 390×844 (sau khi sửa bộ đo) |

⚠️ **Phép tiêm 3 lộ một lỗ của chính bộ test**: trước khi viết test đọc → xoay →
đọc lại, ba test "phản hồi cũ bị bỏ" chỉ đạt nhờ `phase`, không nhờ `requestId`.

## 6. Bằng chứng trình duyệt — và bộ đo tự sửa

`frontend/scripts/photo-problem-browser-check.mjs`, bản dựng tĩnh, mọi `/api/*`
chặn ở biên mạng, **0 lượt gọi model**: **10/10 ô ở 1440×900 · 10/10 ô ở
390×844**, 0 lỗi trang. Artifact:
`docs/evaluation/geometry/photo-problem-to-scene/browser/PHOTO_BROWSER_CHECK.json`.

⚠️ **Bộ đo nói dối một lần, và phép tiêm là thứ bắt được nó.** Ô "không tràn
ngang" bản đầu so `scrollWidth` với `innerWidth`. Dưới giả lập di động, trang
rộng hơn thiết bị làm trình duyệt THU NHỎ, và `innerWidth` phình theo nội dung
(đo được **924** khi khối ảnh bị tiêm rộng 900 px) — nên ô ấy **về cấu tạo không
thể đỏ** ở 390×844, và phép tiêm `tran-ngang` trả ĐẠT. Chẩn đoán riêng xác nhận
sản phẩm thật sự vừa khung (390 = 390 = 390, 0 phần tử vượt); nay ô so với bề
rộng THIẾT BỊ và phép tiêm đỏ. Lượt ĐẠT trước bản sửa đúng **tình cờ**.

Một lượt chạy khác không in phán quyết nào (lỗi hạ tầng Chrome/cổng, không phải
KHÔNG ĐẠT) — chạy lại, không tính.

## 7. Camera — không hồi quy, và một giả định của §13 sai

```text
đường dựng hình (simulations · state · core · App.tsx · main.tsx)   git diff 085cae6: 0 dòng
cổng quay p1–p7 trên bản dựng 085cae6   p1 DAT · p2 THIEU_HUONG_NHIN · p3 DAT · p4 THIEU · p5 THIEU · p6 DAT · p7 DAT
cổng quay p1–p7 trên bản dựng 537f6d8   p1 DAT · p2 THIEU_HUONG_NHIN · p3 DAT · p4 THIEU · p5 THIEU · p6 DAT · p7 DAT
trục (hai bản)                          Z ‖0,990–1,000‖ ở p1/p2/p3/p6/p7 · p4/p5 báo Y ‖0,991–1,000‖, cos ∈ [−1; 0]
CAMERA_Z_UP_REGRESSION                  = 0  (cùng phán quyết, cùng mã dựng hình)
```

⚠️ **§13 giả định `085cae6` có `TOP/BOTTOM_VIEW = PASS`. Cổng quay trên chính
`085cae6` nói KHÔNG ở p2, p4, p5.** Wave Z-up chỉ chạy cổng ở bộ ca mặc định
p1/p6/p7. Wave này không sửa camera — yêu cầu là giữ nguyên hành vi tại
`085cae6` — nên đây là một phát hiện được khai, không phải một bản vá.
Artifact: `orbit-gate-baseline-085cae6/` và `orbit-gate-537f6d8/`.

## 8. Lượt provider thật (§11)

```text
PRE-REGISTERED            c01 rõ có đề · c05 nghiêng + công thức + hình · c11 chỉ có hình
MEASUREMENT_CLASS         DEVELOPMENT_DIAGNOSTIC · HELD_OUT_CLAIM = NO · OPERATOR_IS_DEVELOPER
CALL_CEILING_LOGICAL      11 (3 đọc ảnh + 2 × (1 đọc đề + 3 tổng hợp)), chặn bằng ApiBudget
REAL_PROVIDER_EVIDENCE    = NOT_ESTABLISHED — thiếu ALLOW_LIVE_AI=1 và GEMINI_API_KEY
APPLICATION_LLM_CALLS     = 0 · REAL_PROVIDER_CALLS = 0
MODEL_IDENTITY            gemini-2.5-flash (mặc định GEMINI_MODEL) — CHƯA được gọi
FIXTURE_DRY_RUN           3/3 đúng kỳ vọng, 0 lượt gọi thật, 0 chạm mạng — chứng nhận RUNNER, không phải provider
```

Runner: `backend/scripts/run_photo_problem_live.py`.

## 9. Cổng nghiệm thu §12

| cổng | kết quả | loại bằng chứng |
|---|---|---|
| VALID_IMAGE_UPLOAD | PASS | test + trình duyệt (fixture) |
| CORRUPT_OR_FAKE_IMAGE_REJECTED | PASS | test |
| EXIF_ORIENTATION | PASS | test + bộ ảnh (khớp từng điểm ảnh) |
| EXIF_GPS_REMOVED | PASS | test + bộ ảnh |
| VISION_STRUCTURED_OUTPUT | **PASS_FIXTURE_ONLY** | provider giả; **API thật chưa gọi** |
| UNCERTAINTY_PRESERVED | PASS | test (fixture) |
| SEMANTIC_SCHEMA_VALIDATION | PASS | phát lại byte thật qua validator hiện hành |
| EMPTY_SCENE_COUNT | 0 | phát lại p1/p3/p4/p5 + tiêm cảnh rỗng |
| SILENT_HALLUCINATION_COUNT | 0 | fixture — **chưa đo trên provider thật** |
| AMBIGUOUS_CASE_SAFE_REJECTION | PASS | test + trình duyệt (fixture) |
| TEXT_ONLY_REGRESSION | 0 | test + trình duyệt |
| CAMERA_Z_UP_REGRESSION | 0 | §7 |
| GEOMETRY/ANSWER_REGRESSION | 0 | demo 5/5 + rút gọn 1/1 · bề mặt sập 6/6, 0 lỗi 500 |
| MOBILE_UPLOAD_AND_PREVIEW | PASS | trình duyệt 390×844 (sau khi sửa bộ đo) |
| CACHE_IDENTITY | PASS | test + khoá danh tính |
| Ảnh rõ: tên điểm, công thức, topology đúng | **NOT_ESTABLISHED** | cần provider thật |

## 10. Quy tắc §14 — KHÔNG merge

Hai ô cuối của §9 không đạt được trong phiên: không có lượt đọc ảnh THẬT nào, nên
không có bằng chứng rằng provider trả đúng lược đồ (tiền lệ HTTP 400 ở §2.5) hay
đọc đúng tên điểm, công thức, topology của một ảnh rõ. Theo §14: mã sản phẩm ở
lại nhánh `feat/photo-problem-to-scene`, `main` giữ `085cae6`.

```text
MERGE_BLOCKER = REAL_PROVIDER_EVIDENCE_NOT_ESTABLISHED
GỠ BLOCKER    = cd backend && ALLOW_LIVE_AI=1 GEMINI_API_KEY=<key> PYTHONIOENCODING=utf-8 \
                .venv/Scripts/python.exe scripts/run_photo_problem_live.py
```

## 11. Báo cáo §15

```text
PHOTO_PROBLEM_TO_SCENE_END_TO_END
START_HEAD                 = 085cae6
END_HEAD                   = <commit 3 trên feat/photo-problem-to-scene> — main KHÔNG đổi
IMAGE_UPLOAD               = YES (Tải ảnh + nút +)
IMAGE_CAPTURE              = YES (capture="environment"; trình duyệt máy tính mở hộp chọn tệp)
SUPPORTED_FORMATS          = PNG · JPEG · WEBP (soi nội dung)
MAX_FILE_SIZE              = 10 MB · 40 MP (kiểm từ header) · cạnh gửi đi ≤ 3072
EXIF_ORIENTATION           = PASS
EXIF_GPS_REMOVAL           = PASS
VISION_PROVIDER            = Gemini generateContent (call_gemini, inline_data, JSON mode + responseSchema)
VISION_MODEL               = gemini-2.5-flash (GEMINI_MODEL) — chưa gọi thật
VISION_PROMPT_VERSION      = sha256(transcribe.md) b499dc7a…
VISION_SCHEMA_VERSION      = photo-problem-extraction/1
SEMANTIC_PIPELINE_REUSED   = YES
PARALLEL_PIPELINE_CREATED  = NO
SUPPORTED_CASES            = chóp + thiết diện · cầu · trụ · nón — dựng được (fixture tầng A, tầng B phát lại byte thật)
SAFE_REJECTION_CASES       = chỉ có hình · không đọc được · không phải hình học · ngoài năng lực · dữ kiện không có trong đề
TEXT_EXTRACTION_RESULTS    = NOT_MEASURED — cần provider thật
TOPOLOGY_RESULTS           = NOT_MEASURED trên ảnh; loại cảnh của bốn họ khớp fixture
EMPTY_SCENE_COUNT          = 0
SILENT_HALLUCINATION_COUNT = 0 (fixture) · thật: chưa đo
TEXT_ONLY_REGRESSION       = 0
CAMERA_Z_UP_REGRESSION     = 0
P1_P7_REGRESSION           = 0 (cùng phán quyết với 085cae6; p2/p4/p5 THIEU_HUONG_NHIN có sẵn)
BACKEND_CHANGED            = YES
MODEL_FACING_CHANGED       = YES — chỉ bề mặt đọc ảnh
CANDIDATE_HASH_BEFORE/AFTER = 96a9368b… / 13e2aaaa…
CACHE_VERSION_BEFORE/AFTER = 95 / 95
APPLICATION_LLM_CALLS      = 0
REAL_PROVIDER_CALLS        = 0
TEST_RESULTS               = pytest 4910 đạt · 2 đỏ TẤT YẾU trước commit 3 (holdout 7B: cây bẩn · candidate: chưa đóng băng)
                             → sau đóng băng trên cây sạch: test_evaluation_candidate 13/13 · holdout kiểm lại sau commit 3
                             · vitest 869/869 · tsc ✓ · build ✓ · trình duyệt 20/20 ô
CANDIDATE_REFROZEN         = commit 537f6d8 · cay_lam_viec_sach = true · 94 file · 13e2aaaa… · --verify khớp
FAULT_INJECTIONS           = 9/9 đỏ đúng chỗ (+ 2 phép tiêm của bằng chứng danh tính)
COMMITS_CREATED            = 3 (8bb94ce backend · 537f6d8 frontend · commit 3 bằng chứng + tài liệu + đóng băng candidate)
WORKING_TREE               = sạch
USER_VISUAL_APPROVAL       = PENDING
NEXT_ACTION                = USER_TESTS_REAL_PHOTO_INPUT
```

## 12. Giới hạn đã khai

- Bộ ảnh là **tổng hợp**: không nền giấy thật, bóng tay, nếp gấp, chữ viết tay.
- Cache ảnh chỉ trong tiến trình; khởi động lại là mất.
- Huỷ chỉ phía client; lượt gọi provider phía server vẫn chạy hết.
- `capture` chỉ là gợi ý — trình duyệt máy tính mở hộp chọn tệp.
- Không suy dữ kiện từ hình vẽ: đề chỉ cho dữ kiện trong hình sẽ bị từ chối
  hoặc thiếu dữ kiện ở tầng B, và người học phải gõ bổ sung.
- Candidate đóng băng lại khi cây sạch bằng cách tạm cất (stash) thư mục bằng
  chứng chưa commit — vì luật ≤ 3 commit không cho một commit đóng băng riêng.
- Trường `source_artifact_path` được thêm tay vào ba artifact đã sinh trước khi
  script sinh được sửa để tự ghi nó (cùng giá trị); lệnh xoá-rồi-sinh-lại bị từ
  chối trong phiên nên không chạy.

## 13. Artifact

`docs/evaluation/geometry/photo-problem-to-scene/`: `corpus/` + `CORPUS.json` +
`OFFLINE_NORMALIZATION.json` · `browser_fixture_{review,rejected}.json` ·
`browser/` (kết quả + ảnh chụp + hai phép tiêm) · `live/` (lượt
`NOT_ESTABLISHED` + lượt `FIXTURE_DRY_RUN`) · `orbit-gate/` ·
`orbit-gate-baseline-085cae6/` · `orbit-gate-537f6d8/`.
