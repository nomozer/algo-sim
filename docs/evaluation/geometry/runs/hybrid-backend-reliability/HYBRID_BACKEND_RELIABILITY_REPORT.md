# Hybrid backend reliability — báo cáo

Run `hybrid-backend-reliability` · 2026-11-07 · nhánh `feat/hybrid-backend-reliability` · không merge, không push,
không viết lại lịch sử. Nhãn: **[test]** khoá bằng test tự động · **[đo]** số đo của run này (tệp trong `results/`) ·
**[mã]** suy từ mã nguồn · **[chưa kiểm]**.

## 1. Git baseline và commit cuối

| | |
|---|---|
| baseline | `main = origin/main = e1a41ebe` (sau `git fetch`), cây sạch; worktree khác: `axo-pedagogical-integration`, `w3-f2-ratio-projection-language-grounding` (detached, không đụng) |
| product | `05cf4db1` (narration + công tắc dừng đọc ảnh) → **`cb79848f`** (rò payload) |
| candidate | `7d05948e` (đóng băng tại 05cf4db1) → **`2eba49ed`**: 103 file, `measured_system` `be2c37fd…`, đóng băng trong worktree detached sạch; template K-1/R-1/S-2 ràng buộc lại cơ học, không ghi phê duyệt |
| khác | `fd125f93` bundle fixture preview mới (`fixtures-adapter-2-narration/`); commit tài liệu + bằng chứng của run |
| `CACHE_VERSION` | **132, không đổi** (§4) |
| `Co-Authored-By` | 0 trong mọi commit |

## 2. Lỗi thực tế phát hiện

| # | mức | lỗi | phát hiện bởi | trạng thái |
|---|---|---|---|---|
| F1 | **P1** | Mỗi lần trích xuất bị từ chối bởi một model validator (`UNKNOWN_SOLID_ID`, `INVALID_MATH_GOAL`, `INVALID_DERIVED_SECTION`, …) **rò vĩnh viễn** cả đồ thị payload đã parse: +3 payload sống mỗi vòng 60 đề, 3 → 90 sau 30 vòng, không bão hoà | kiểm tải có giới hạn (`concurrency_reliability.py`: bộ nhớ +120–140 KB/vòng) → `memory_retention_probe.py` + duyệt referrer | **sửa** `cb79848f` [test] |
| F2 | **P1** | `POST /api/image/extract` **bỏ qua** công tắc dừng khẩn cấp `ALLOW_LIVE_AI=0` (AGENTS §3) — `/api/analyze` dừng, đọc ảnh vẫn gọi provider thật và vẫn phục vụ cache | chính sự cố của run này (§9) | **sửa** `05cf4db1` [test] |
| F3 | P2 | Lời kể bước (`envelope.config.frames[].narration`, `view_steps[].narration`) in repr Python của kernel: `"Ghi nhận giá trị vừa tính được: Circle3(center=Vec3(x=Fraction(0, 1), …"` — 24 lời kể / 15 bài phục vụ (thiết diện tròn trụ/nón/cầu, diện tích toàn phần, mặt phẳng trung trực + trục của mặt cầu ngoại tiếp). Đây là hiện tượng A3 của đề bài, **vẫn còn trên `main`** | `http_e2e_replay.py` (quét repr trong envelope) | **sửa** `05cf4db1` [test] |
| R1 | P3 | `config` vẫn kể toạ độ khung dựng ở bước dựng điểm (`"Dựng điểm = (1, 0, 0)."`) | như F3 | mở `ISSUE-ARCH-CONFIG-NARRATION-CHART-COORDINATES` |
| R2 | P3 | `gemini.call_gemini` (chỉ đọc ảnh dùng) gửi khoá trong query `?key=`; tuyến Hybrid dùng header. Tiềm ẩn: `app` không cấu hình logging nên dòng INFO của httpx không tới handler nào [mã] | rà F2 | mở `ISSUE-OPS-VISION-TRANSPORT-KEY-IN-URL` |
| R3 | P3 | `envelope.visual_mode = "2d"` dù có `scene3d` (hiện tượng A3) | HTTP replay | **không phải lỗi**: hiển thị chọn chế độ qua `effectiveVisualMode(module, …)`, không đọc trường này; thuộc tàn dư từ vựng IR đã ghi ở `ISSUE-ARCH-INFORMATICS-MODEL-SURFACE-AND-IR-VOCABULARY` [mã] |

Không phát hiện lỗi nào ở Source Gate, Planner, Registry, Exact Kernel, Scene3D hay construction continuity (§5–§6).

## 3. Nguyên nhân gốc

**F1.** `typed_fact_next._parse` bắt `ValidationError` của pydantic, tìm lỗi có kiểu trong `errors()[i]['ctx']['error']` và
`raise inner from exc` **bên trong** khối `except`. `ValidationError` giữ chính `inner` trong ctx; frame `_parse` nằm trong
traceback của `inner` và vẫn với tới `ValidationError` qua `exc`, qua `__cause__` và qua bound method `errors`. Chu trình đi qua
một đối tượng pydantic-core nên `gc.collect()` không bao giờ giải phóng (đo: số đối tượng sống tăng tuyến tính sau
`gc.collect()` mỗi vòng). Lần sửa thử đầu (đưa `raise` ra ngoài `except`, bỏ `from`) **vẫn đỏ** vì local `errors` còn giữ
`ValidationError` — đó cũng là phép tiêm lỗi chứng minh test phân biệt được.

**F2.** Công tắc chỉ được kiểm ở `_analyze_hybrid_route` và trong transport Hybrid (`function_calling.live_transport`); đọc ảnh đi
qua transport khác (`gemini.call_gemini`) không kiểm nó.

**F3.** Lời kể dự phòng của `AssignStmt` trong `semantic_program/interpreter.py` định dạng giá trị bằng `str()`. Bản sửa trước
(`ISSUE-ARCH-LLM-VECTOR-ASSIGN-NARRATION`) chỉ áp cho chương trình compiler (`_compiler_geometry`) để envelope `LLM_ONLY` giữ
nguyên byte; sau cutover không còn chương trình compiler nào nên Hybrid `/4` luôn rơi vào nhánh chưa sửa.

## 4. Thay đổi mã nguồn

| file | thay đổi |
|---|---|
| `backend/app/simulation/geometry_functions/typed_fact_next.py` | gỡ lỗi validator trong helper riêng `_validator_error` (frame tự kết thúc); `raise inner` ngoài `except`, không chain. Cùng đối tượng lỗi, cùng mã |
| `backend/app/main.py` | `image_extract`: `ALLOW_LIVE_AI=0` ⇒ `_hybrid_infra_error("LIVE_AI_DISABLED")` (503, `no-store`, `INFRASTRUCTURE_FAILURE`), sau kiểm ảnh (ảnh hỏng vẫn 400 của người học), trước cache và provider — cùng thứ tự với `/api/analyze` |
| `backend/app/simulation/semantic_program/interpreter.py` | giữ `_kieu_khai` (kiểu KHAI của biến); giá trị có kiểu hình học được **gọi tên** bằng `display_names.MO_TA_KIEU` (`"Dựng đường tròn cần dùng."`); vô hướng giữ giá trị (`9/2`, `4π`, `2π√3`) |
| test | `tests/geometry/test_typed_fact_next_extraction.py::test_a_refused_extraction_releases_its_payload_and_error` (đỏ 50/50 → xanh, đối chứng schema thường 0 rò); `tests/test_image_extract_api.py::test_cong_tac_dung_ALLOW_LIVE_AI_0_chan_ca_doc_anh`; `tests/geometry/test_step_narration_no_kernel_repr.py` (13/28 ca dương đỏ → 30/30 xanh, kèm đối chứng vô hướng); `tests/test_hybrid_preview_fixtures.py` trỏ sang bundle mới |

Reuse: `MO_TA_KIEU`, `ky_hieu_dai_luong`, `GEOMETRY_TYPES`, `_hybrid_infra_error`, fixture `route_client`/`payload()` có sẵn.
Không tạo module sản phẩm mới. Chống viết trùng: `postconditions._kieu_runtime` đã cân nhắc và loại (thiếu `Circle3`).

**`CACHE_VERSION` không bump.** Không đổi prompt, bề mặt trích xuất (`typed_fact_next_surface_fingerprint` băm khung request,
không băm mã nguồn; `test_cache_identity.py` 15/15) hay chính sách định tuyến. F3 chỉ đổi chữ trong `envelope.config`, thứ
workspace hiện hành không hiển thị (`AxoWorkspaceV62` chỉ nhận `scene3d`) [mã]; cảnh, đáp số, chứng chỉ giống từng byte
(bundle fixture: 1/41 fixture khác nội dung, đúng 2 lời kể). Hàng cache cũ còn lời kể repr là vô hại với giao diện hiện tại.
`PRODUCTION_DEPLOYMENT_VERIFIED = NO` nên không có cache production nào để vô hiệu hoá.

## 5. Correctness trước/sau — trích xuất, Source Gate, Planner/Kernel

**Source Gate với méo nghĩa (Phase B)** [đo] `results/source-gate-distortion.json` (`tools/source_gate_distortion_probe.py`).
Mỗi ca lấy một payload đang **SERVED** từ kho, thay một cụm trong đề **và** trong mọi quote (quote vẫn nguyên văn), giữ nguyên
khẳng định có kiểu — đúng hình dạng "trích dẫn trung thực, gõ sai quan hệ". 48 méo nghĩa (38 đổi chữ + 10 đổi cấu trúc) +
2 đối chứng, chạy trên candidate cuối:

- **0 wrong-served, 50/50 đúng kỳ vọng**; mọi méo nghĩa bị từ chối với mã đúng lớp (một ca, `two-goals-operand`, bị từ chối
  chỉ vì quote không còn nguyên văn — `QUOTE_NOT_IN_SOURCE` — nên không tính là phép thử ngữ nghĩa): `SA ⟂ SB`/`SA ⟂ AB` gõ thành `SA ⟂ (ABCD)` ⇒ `PLANE_NOT_IN_QUOTE`;
  `M ∈ AB`/trọng tâm gõ thành trung điểm, hình thoi/chữ nhật gõ thành hình vuông, lăng trụ xiên gõ thành đứng ⇒ `PREDICATE_NOT_IN_QUOTE`;
  góc đường–đường gõ thành đường–mặt, khoảng cách điểm–đường gõ thành điểm–mặt, `S.ABC` gõ thành `S.ABCD`, nội tiếp ↔ ngoại tiếp,
  `∥` ↔ `⟂` của mặt cắt ⇒ `SOURCE_OBJECT_MISMATCH`; số đo/toán hạng sai ⇒ `UNGROUNDED_VALUE`; bỏ phủ định ⇒ `UNGROUNDED_VALUE`;
  hỏi chu vi gõ thành diện tích ⇒ `NOT_ASKED_IN_SOURCE`; đường kính gõ thành bán kính ⇒ `CURVED_WORDING_UNSUPPORTED`.
- Cấu trúc: bỏ một trong hai mục tiêu ⇒ `REQUEST_NOT_ANSWERED` (4/4); bịa tiền đề dưới quote thật ⇒ `ROLE_NOT_IN_QUOTE` /
  `UNGROUNDED_VALUE`; bỏ ngầm tiền đề đề nêu ⇒ `SOURCE_PREMISE_UNREAD`.
- Đối chứng (đổi thứ tự hai câu hỏi; lặp một mục tiêu) vẫn SERVED.

Không sửa Source Gate — không có lỗi để sửa (đề bài §II). Đây là bằng chứng **phát triển**: kho đã có, méo nghĩa do run này
soạn; **không** phải H-1, không chứng minh khái quát hoá độc lập.

**Phân lớp phòng thủ** [đo]: 25/994 payload bị bộ kiểm trích xuất từ chối **trước** route với mã cụ thể hơn
(`CONDITIONAL_CLAUSE`, `NEGATED_CLAUSE`, `QUOTE_NOT_IN_SOURCE`, …) mà route trần cũng từ chối; 0 ca SERVED ở lớp này mà từ chối ở lớp kia.

**Planner/Kernel**: không thay. Đáp số khớp oracle được các bộ hiện có khoá (bộ hình học 13 077 test, gồm oracle đóng độc lập
`curved_probe`, `circumscribed_sphere_probe`, …) — chạy lại xanh (§10). Không có đáp số nào đổi: bundle fixture chỉ khác lời kể.

## 6. Scene3D và tính liên tục của bước dựng

[đo] `results/http-e2e-summary.json`: 548 phản hồi SERVED qua HTTP, **0** phát hiện hợp đồng: mỗi bước đủ `step_id`,
`depends_on`, `created_ids`, `reused_ids`, `highlighted_ids`, `retired_ids`, `verification_refs`, `coordinate_frame_id`,
`step_summary.what`; mọi id tham chiếu có trong `scene3d.objects`; `depends_on` (id hình học, không phải id bước) và
`reused_ids` chỉ trỏ vật đã tạo ở bước trước; không vật nào bị tạo hai lần; mọi đáp số chính xác có mặt trong envelope; không
repr nội bộ nào trong envelope (sau F3). 7 bất biến `construction_continuity` do test hiện có khoá, chạy lại xanh.
Bộ kiểm frontend trên chính các body HTTP: §7.

## 7. Tích hợp frontend/backend

Phân tầng, không trộn:

| tầng | đã làm | kết quả |
|---|---|---|
| hàm trực tiếp | `run_typed_fact_next_v2_route` trên 994 payload | dùng làm đối chiếu |
| **HTTP** | `TestClient` (đã enter) → `POST /api/analyze`, `staging-replay`, middleware + idempotency + sổ lượt dùng + cache + JSON thật | 994/994 HTTP 200 (548 SERVED, 445 từ chối có kiểu, 1 cổng miền: đề toạ độ Oxyz, route cũng từ chối); body HTTP = body bộ điều phối 994/994; lần hai 548/548 `hit` giống từng byte |
| **frontend (Node)** | chính `docPhanHoiPhanTich` của `llm/client.ts` + `verifySceneMathematicalConsistency` + `buildPedagogicalConstructionPlan` + `evaluateStudentPresentationPolicy` trên body HTTP (harness tạm, bản sao `tools/authority_audit.vitest.ts.txt`) | **392/392** body SERVED có đáp số: giải mã được, toán học hợp lệ, mục tiêu `reached`, mọi đáp số `DERIVED_VERIFIED`, không thông báo chẩn đoán, không repr trong chữ người học (`results/frontend-authority-audit.json`); 156 body SERVED còn lại là bài chỉ dựng hình, không có đáp số để kiểm |
| trình duyệt | [chưa kiểm] ở run này — run `axo-end-to-end-authority-scene3d-usability` đã đo trên trình duyệt thật; mã frontend không đổi ở run này |
| provider live | `LIVE_SMOKE_NOT_AUTHORIZED` (§9) |

Frontend hiện tại tiêu thụ `/api/analyze` và `/api/image/extract` (`llm/client.ts`); ảnh được gửi nguyên tệp (chưa có bước
khoanh vùng trên `main`). **Biên ảnh** [đo] `results/image-boundary.json` (mạng bị chặn, không khoá ⇒ ảnh hợp lệ dừng ở 503):
PNG/JPEG/WEBP cắt 300×80, PNG RGBA (canvas), JPEG có EXIF xoay, 1×1, 6000×4000, xoay 90° đều qua kiểm định; PNG gắn nhãn JPEG ⇒
`IMAGE_TYPE_MISMATCH`, bom giải nén 9000×9000 ⇒ `IMAGE_TOO_MANY_PIXELS`, GIF ⇒ `IMAGE_UNSUPPORTED_FORMAT`, >10 MB ⇒
`IMAGE_TOO_LARGE`; `ALLOW_LIVE_AI=0` ⇒ 503 `LIVE_AI_DISABLED`. Văn bản đọc từ ảnh không vào `/api/analyze` khi chưa được người học
duyệt (test sẵn có `test_hai_tang_image_extract_sang_analyze_text_di_qua_hybrid`).

Không sửa `frontend/**`. Không có việc nào cần giao cho phiên frontend: các trường bước dựng mới đã được backend xuất và frontend
đọc qua `scene3d.formation`; `config` không được hiển thị khi có `scene3d`.

## 8. Hiệu năng

[đo] `results/stage-profile.json` (`tools/stage_profile.py`): 994 đề, `staging-replay`, 0 lượt gọi provider, Python 3.12.10,
Windows, SQLite, `TestClient` đã enter, candidate `cb79848f`. Thời gian **bao hàm** (lồng nhau, không cộng được): HTTP ⊃ bộ
điều phối ⊃ {kiểm trích xuất, bridge, planner, engine, adapter}; engine ⊃ {Source Gate, kiểm IR, thực thi IR}.

| giai đoạn (ms) | miss SERVED p50 | p95 | p99 | hit SERVED p50 | từ chối p50 |
|---|---|---|---|---|---|
| **HTTP tổng** | **75.8** | **122.1** | 156.1 | **32.3** | **31.0** |
| bộ điều phối Hybrid | 37.2 | 63.9 | 113.1 | — | 5.0 |
| · kiểm trích xuất TypedFactNext | 2.2 | 3.6 | 4.0 | — | 2.2 |
| · bridge_v2 / FactGraph | 0.7 | 1.1 | 1.5 | — | 0.7 |
| · planner | 1.2 | 1.9 | 2.8 | — | 1.2 |
| · engine (tổng) | 18.7 | 35.2 | 45.1 | — | 3.5 |
| ·· Source Gate | 9.0 | 19.0 | 21.2 | — | 3.2 |
| ·· kiểm IR | 0.4 | 0.7 | 0.9 | — | 0.5 |
| ·· thực thi IR (Exact Kernel) | 6.2 | 12.0 | 65.1 | — | 1.5 |
| · Scene3D build | 0.5 | 0.8 | 1.3 | — | — |
| · continuity enrich / validate | 0.3 / 0.4 | 0.5 / 0.6 | 0.8 / 0.9 | — | — |
| · Adapter `/4` | 7.6 | 11.5 | 68.7 | — | 0.02 |
| JSON serialization (body trả về) | 0.65 | 0.98 | 1.3 | 0.63 | 0.02 |
| sổ lượt dùng: giữ chỗ / chốt | 10.4 / 3.7 | 13.7 / 4.8 | 16.4 / 7.5 | 10.3 / 3.5 | 10.3 / 4.0 |
| cache: đọc / ghi | 0.6 / 5.8 | 0.8 / 7.3 | 1.2 / 9.9 | 0.8 / — | 0.6 / — |
| chuẩn bị replay (đọc kho) | 2.2 | 2.6 | 3.8 | 2.2 | 2.2 |
| telemetry (background) | 5.5 | 7.5 | 9.8 | 5.4 | 4.5 |

- **Cold ≈ warm** (cold miss p50 77.0 / p95 124.3): không có chi phí khởi động đáng kể sau import. **Cache hit rate** của
  lượt thứ hai cho cùng đề phục vụ: **100%** (548/548), body giống từng byte (§7). Từ chối không vào cache (đúng hợp đồng).
- **CPU** p50 62.5 ms/miss, 31.3 ms/hit — bước đo `process_time` Windows là 15,6 ms nên chỉ là cỡ.
- **Bộ nhớ đỉnh** mỗi request miss: p50 0.66 MB, p95 1.04 MB, max 12.2 MB; body p50 70.9 KB, max 119.8 KB.
- Telemetry chạy **sau** khi gửi phản hồi trên máy chủ thật (Starlette background task); `TestClient` chờ nó, nên HTTP tổng ở đây
  cao hơn độ trễ người học khoảng 5 ms.
- **Provider** (Gemini live): request count, token, độ trễ, tỉ lệ lỗi kỹ thuật **NOT_MEASURED** (§9). Tỉ lệ lỗi kỹ thuật offline:
  0/994 (+0/304 dưới tải đồng thời).

**Tối ưu: không giữ thay đổi nào — có chủ đích.** Phần tất định của một lượt phục vụ là ~38 ms p50 / ~64 ms p95; một lượt trích
xuất Gemini live là cỡ giây (chưa đo ở run này), nên tối ưu backend tất định đổi không quá vài phần trăm độ trễ người học thấy.
Không có điểm nghẽn đo được: không tính hình lặp (cache hit 100%, cold ≈ warm), không serialize thừa (JSON < 1 ms), Scene3D
dựng một lần (< 1 ms). Chi phí lớn nhất ngoài route là sổ lượt dùng (~14 ms, commit SQLite) — thuộc hợp đồng nguyên tử của sổ
(run `axo-final-reliability-premerge-gate`) và phụ thuộc DB: phải đo trên Postgres trước khi đụng (`POSTGRES_NOT_TESTED`).
Không đề xuất Rust: không kernel CPU-bound nào nặng (đuôi p99 65–69 ms của thực thi IR/Adapter rơi vào vài bài mặt cầu ngoại tiếp).

**Bộ nhớ và tải** [đo] `results/memory-retention.json`, `results/concurrency-reliability.json`: trước `cb79848f`, +3 payload
sống/vòng (3 → 90 sau 30 vòng, ~120–140 KB/vòng 76 request); sau: **0** payload và 0 lỗi validator sống ở mọi vòng, bộ nhớ
traced nửa sau −16 KB. Tải đồng thời có giới hạn (8 luồng, 4 vòng × 76 request trộn SERVED/từ chối/đầu vào hỏng): **0** body
khác bản tuần tự, **0** 5xx; dồn 8 luồng vào một đề chưa cache: 8× HTTP 200, body giống nhau, đúng 1 hàng cache. Đầu vào hỏng
(JSON hỏng, thiếu trường, sai kiểu, `image` trực tiếp, rỗng, quá ngắn, 2 MB): 4xx có kiểu, không lộ traceback/khoá. Timeout,
lỗi mạng, thiếu khoá, hủy, `JSON_INVALID` của provider đã có test riêng (chạy lại xanh, §10) — không viết trùng.

## 9. Live smoke và một sự cố phải khai

**`LIVE_SMOKE_NOT_AUTHORIZED`.** Đề bài chỉ *đề xuất* ngân sách (25 request, USD 1.00) và yêu cầu phê duyệt chi tiêu hợp lệ;
không có phê duyệt nào trong phiên. 0 lượt live có chủ đích; không dùng ngân sách H-1 hay phần dư C26.

**Sự cố (không được phép):** phiên bản đầu của công cụ offline gỡ `GEMINI_API_KEY` **trước** khi import `app`, trong khi
`app/persistence/db.py` gọi `load_dotenv` lúc import và nạp lại khoá thật từ `backend/.env`. Phép thử biên ảnh khi đó gửi các ảnh
**trắng tổng hợp** (không dữ liệu người học) tới `/api/image/extract`, endpoint không tôn trọng `ALLOW_LIVE_AI=0` (F2) ⇒
provider thị giác thật nhận **tối đa 8** request thành công. Số chính xác là **UNKNOWN**: cache ảnh nằm trong bộ nhớ của tiến
trình đã thoát, ảnh chuẩn hoá giống nhau có thể đã trúng cache, retry không quan sát được. Chi phí ước tính không đáng kể
(ảnh trắng nhỏ, `gemini-2.5-flash`) nhưng **không được phê duyệt**. Xử lý: (1) dừng ngay; (2) công cụ dùng đúng hai lớp chặn của
`backend/conftest.py` (`block_network`: import `db` trước rồi gỡ khoá, chặn mọi transport httpx thật) — chạy lại xác nhận 503;
(3) sửa gốc F2. Không có số liệu nào của báo cáo dựa trên các lượt gọi ấy.

## 10. Regression và Full T3

Theo thứ tự (mọi test 0 lượt gọi mạng, guard `conftest.py`):

| bước | kết quả |
|---|---|
| test mới, đỏ trước khi sửa | narration 13/28 đỏ → 30/30; công tắc dừng ảnh đỏ → 13/13 `test_image_extract_api.py`; rò payload 50/50 đỏ → 32/32 `test_typed_fact_next_extraction.py` |
| `tests/semantic_program` + `tests/geometry` (gồm source-grounding, TypedFactNext, Planner/Registry/Kernel, Scene3D, continuity) | 13 063 passed, 14 failed — **cả 14** là "measured_system differs from frozen EVALUATION_CANDIDATE.json" (con dấu candidate) → xanh 216/216 sau khi đóng băng lại |
| `tests` còn lại (API, tích hợp HTTP, cache/rollback, ảnh, sổ lượt dùng) | 831 passed, 1 failed (`test_committed_fixtures_regenerate_identically_from_the_endpoint`: bundle fixture chứa lời kể repr cũ) → bundle mới, 6/6 |
| `test_cache_identity.py` | 15/15 (bề mặt mô hình không đổi) |
| `freeze_evaluation_candidate.py --verify` | khớp: 103 file `be2c37fd…` |

**Full T3** (`frontend/scripts/full-gate.mjs` = pytest · vitest · typecheck + build · demo replay · crash surface), một lượt,
worktree detached sạch tại **`f453065e`** (HEAD chứa product `cb79848f` + candidate `2eba49ed` + bằng chứng), `git status` sạch
trước và sau: **`FULL_PRODUCT_GATE_PASS`** 516.6 s — pytest **13 911 passed** / 7 skipped / 3 deselected / 9 xfailed; vitest
**135 file / 2 007 test** passed; typecheck + build production PASS; demo `DEMO_REPLAY_PASS 5/5`; bề mặt sập 6/6 đúng kỳ vọng,
0 lần ném 500. Log ngoài kho (không commit traceback thô), sha256 `229e5ffd383c8c6d7990f5e5fd2508652c864a24bf81b67a2cde2a9e09111bd5`.
Commit sau đó chỉ sửa báo cáo này (không đổi mã) — không chạy lại T3. Publication `--range origin/main..HEAD`: 78 blob,
0 vi phạm, **PASS**.

## 11. Giới hạn còn lại

- `INDEPENDENT_H1_VALIDATION = NOT_MEASURED`; méo nghĩa §5 là bộ phát triển do run này soạn trên kho đã có.
- `LIVE_SMOKE_NOT_AUTHORIZED`; độ trễ/token/lỗi của Gemini live **không đo** (đo ở §8 là offline).
- `POSTGRES_NOT_TESTED`: chi phí sổ lượt dùng/cache đo trên SQLite Windows; Postgres có thể khác.
- Hiệu năng đo bằng `TestClient` trong tiến trình (không có socket/uvicorn); `process_time` của Windows có bước 15,6 ms.
- Trình duyệt thật không chạy lại ở run này (frontend không đổi).
- Mở: R1, R2 (P3) trong `OPEN_ISSUES.md`; các issue cũ giữ nguyên.

## 12. Quyết định cuối

**`HYBRID_BACKEND_RELIABILITY_COMPLETE`** — cho phần offline, trên candidate `cb79848f`.

Đối chiếu tiêu chí §XIII của nhiệm vụ: (1) đường HTTP Hybrid xác minh trên frontend/backend hiện tại — 994 đề HTTP + 392/392
qua bộ đọc frontend; (2) không còn P0/P1 đã phát hiện mà chưa xử lý — F1, F2 sửa; (3)–(4) Source Gate giữ đúng 48/48 méo nghĩa,
trích xuất đã lưu không bị chấp nhận sai; (5)–(6) đáp số khớp oracle của các bộ hiện có, 0 wrong-served; (7)–(9) Scene3D, bước
dựng và đáp số nhất quán (0 phát hiện hợp đồng, `DERIVED_VERIFIED` 392/392); (10) cache và lỗi provider đúng hợp đồng; (11)–(12)
có baseline hiệu năng, không giữ tối ưu nào vì không có điểm nghẽn đáng sửa; (13)–(14) regression mục tiêu và Full T3 PASS;
(15) mọi thay đổi đã commit trên nhánh.

Không suy ra từ đây: Gemini live đạt (`LIVE_SMOKE_NOT_AUTHORIZED`), khái quát hoá độc lập (`INDEPENDENT_H1_VALIDATION =
NOT_MEASURED`), hay Postgres/production (`POSTGRES_NOT_TESTED`, `PRODUCTION_DEPLOYMENT_VERIFIED = NO`).

Việc của Owner: (a) xem nhánh `feat/hybrid-backend-reliability` và quyết merge/push (agent không tự làm); (b) nếu muốn live
smoke, phê duyệt ngân sách cụ thể — đề xuất của nhiệm vụ (≤ 25 request, ≤ USD 1.00) vẫn chờ; (c) ghi nhận sự cố §9.
