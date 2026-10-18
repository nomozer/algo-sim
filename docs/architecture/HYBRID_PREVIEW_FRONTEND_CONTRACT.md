# Hợp đồng dữ liệu Hybrid Route D Preview → Scene3D

> Người đọc: agent/nhóm Scene3D (frontend). Nguồn sự thật là mã và fixture; tài liệu này mô tả chúng, không thay chúng.
> Thiết lập bởi run `hybrid-preview-contract-hardening` (2026-10-18). Phiên bản hợp đồng: `hybrid-route-d-preview/1`
> (envelope) · `hybrid-preview-adapter/2` (adapter; `/2` = lời từ chối mang `refusal_cause` và `failure_category` đã phân
> loại) · `hybrid-preview-envelope-fixture/1` (fixture).

## 0. Phạm vi và giới hạn

- Route D Preview là **endpoint offline chỉ cho operator** (`POST /api/preview/hybrid`). Mặc định nó TẮT, và
  `HYBRID_PRODUCT_ENABLEMENT = NO-GO`. `/api/analyze` (mặc định `LLM_ONLY`) không trả dữ liệu Route D.
- **Không xây browser caller** tới endpoint này: request có header `Origin` bị trả 403 theo thiết kế. Frontend chỉ đọc
  **fixture** (§1) trong test và harness.
- Tài liệu này chỉ mô tả dữ liệu. Nó không cho phép bật Hybrid, không cho phép nối Route D vào `/api/analyze`.

## 1. Fixture — nguồn dữ liệu duy nhất cho frontend

- Thư mục: `docs/evaluation/geometry/runs/hybrid-preview-contract-hardening/fixtures-adapter-2/`. File `manifest.json`
  liệt kê từng fixture (`id`, `kind`, `file`, `sha256`, `response_sha256`, `expected`, `covers`).
- Thư mục `fixtures/` cùng run **đã bị thay thế, không dùng**. Nó được xuất trước review và mang nhãn adapter `/1`,
  vốn là nhãn của adapter cũ chưa phân loại lời từ chối.
- Mỗi fixture là **phản hồi thật** của endpoint, gồm `source` (đề + phản hồi provider giả lập lấy từ corpus đã commit,
  kèm `input_sha256`), `injection` (lỗi tiêm có khai, hoặc `null`), `producer` (commit, product commit, băm mã sản phẩm,
  phiên bản adapter/envelope), `expected` và `response`. Không fixture nào viết tay.
- Tái tạo và kiểm: `cd backend && python scripts/export_hybrid_preview_fixtures.py --verify <thư mục>`. Lệnh này khoá
  trong `backend/tests/test_hybrid_preview_fixtures.py`. Bộ fixture **bất biến**: nếu hợp đồng đổi, sinh bộ mới ở một
  run mới (`--out` từ chối ghi đè).
- Loại fixture: `served-*` (12), `refusal-*` (25, trong đó 6 có lỗi tiêm `tampered` / `identity`, và có các đầu ra
  provider `malformed`), và `gate-*` (4 phản hồi HTTP của cổng, chỉ operator thấy).

## 2. Cấu trúc phản hồi

```text
{ schema_version: "hybrid-route-d-preview/1",
  envelope: <envelope ngữ nghĩa — đưa NGUYÊN khối này vào store.loadEnvelope>,
  route_d:  <siêu dữ liệu Route D — đọc riêng, KHÔNG nằm trong envelope> }
```

Phản hồi của cổng (`gate-*`) không có `envelope`. Nó chỉ có `{reason_code, error}` với HTTP 404 (`PREVIEW_DISABLED`),
403 (`PREVIEW_FORBIDDEN`), 422 (`PREVIEW_BODY_INVALID`) hoặc 503 (`OFFLINE_FIXTURE_REQUIRED`). Người học không bao giờ
thấy các phản hồi này.

### 2.1 Envelope phục vụ (`envelope.status == "ok"`)

| trường | giá trị / ý nghĩa |
|---|---|
| `simulation_id` | `generic.semantic_program` — cùng module với envelope `LLM_ONLY` |
| `config` | đã qua `validate_semantic_envelope_config` ở backend; `execution_truncated == false` |
| `domain` | `"geometry"` |
| `source` | `"hybrid_route_d_preview"` — chỉ dùng để phân biệt nguồn, không hiển thị |
| `description` | câu cố định: *"Quan sát mô hình dựng từ dữ kiện; các kiểm tra trên hình không phải chứng minh tổng quát."* |
| `scene3d.chart_metric` | ma trận Gram 3×3, phần tử là chuỗi số hữu tỉ. Backend chỉ phát ma trận đối xứng, xác định dương (`Metric`), nhưng renderer vẫn phải tự vệ (F2) |
| `scene3d.objects / events / formation` | cùng hợp đồng Scene3D hiện có. Thứ tự dựng đã được kiểm: không vật nào xuất hiện trước vật nó phụ thuộc |
| `scene3d.length_unit` | có khi đề cho độ dài theo `a` (§4); vắng khi đề dùng số |

### 2.2 `route_d` (khi phục vụ)

| khoá | nội dung |
|---|---|
| `runtime_identity` | phiên bản Registry/Planner/Engine, surface trích xuất, adapter/envelope, `fingerprint`, `provider_mode = OFFLINE_FIXTURE_ONLY`, `product_enablement = NO-GO`. **Không hiển thị** |
| `answers` | đáp số dạng chữ, ví dụ `"a³√3/3"` |
| `answer_exact` | `{coef, dim, unit}`: hệ số chính xác, bậc theo `a` (0 nếu đề dùng số), `unit = "a"` hoặc `null` |
| `planner.goal_checks` / `planner.negated_checks` | quan sát trên hình dựng (§3) |
| `source_provenance` | các lời gọi `{id, fn, args, quotes}`. `quotes` là đoạn **có thật trong đề** (đã qua cổng nguồn) |
| `construction_trace` | các bước dựng có quy tắc và `provenance` (ví dụ `LAYOUT_DERIVED` = bố cục hệ tự chọn, không phải dữ kiện) |
| `geometry_ir`, `kernel_check`, `length_unit` | IR đã thẩm định; `kernel_check == true`; `length_unit` bằng `scene3d.length_unit` |

## 3. Quan sát trên hình dựng ≠ chứng minh toán học tổng quát (BẮT BUỘC)

Mỗi mục của `goal_checks` / `negated_checks` có dạng
`{evidence_state, proof_status, can_present_as_proven}`:

- `evidence_state ∈ {TRUE_ON_CONFIGURATION, FALSE_ON_CONFIGURATION, UNVERIFIABLE}`: kết quả kiểm trên **một** hình mà
  hệ dựng từ giả thiết.
- `proof_status` luôn là `"UNVERIFIABLE"` và `can_present_as_proven` luôn là `false` ở phiên bản này. Backend từ chối mọi
  kết quả vi phạm điều đó (`PREVIEW_PROOF_STATUS_INVALID`), và có thêm một lớp chặn văn bản tự xưng "đã chứng minh"
  (`PREVIEW_PROOF_TEXT_INVALID`).

Frontend PHẢI:

1. Không bao giờ hiển thị "đã chứng minh", "điều phải chứng minh", "đpcm", dấu ✓ chứng minh, hay bất kỳ cách nói tương
   đương, trừ khi `can_present_as_proven === true`. Trường thiếu hoặc giá trị lạ đều coi như `false`.
2. Hiển thị `evidence_state` như một quan sát. Gợi ý cách nói:
   - `TRUE_ON_CONFIGURATION`: "Trên hình đã dựng, điều này đúng."
   - `FALSE_ON_CONFIGURATION`: "Trên hình đã dựng, điều này không đúng."
   - `UNVERIFIABLE`: "Chưa kiểm được trên hình đã dựng."

   Mọi cách nói phải kèm ý "đây là quan sát trên một hình, không phải chứng minh tổng quát".
3. Không suy ra "đề sai" từ `FALSE_ON_CONFIGURATION` của một mệnh đề phủ định. Backend đã từ chối loại đề này
   (`NEGATED_CLAUSE`, `verification_gap`).

Fixture kiểm: `served-H07_PROOF_GOAL_NOT_PREMISE_BUT_CHECKED` (quan sát `TRUE_ON_CONFIGURATION`),
`refusal-inconclusive-negated`, `refusal-inconclusive-proof-only`, `refusal-integrity-proof-status`.

## 4. `length_unit` và `display_scale`

`scene3d.length_unit = {symbol: "a", display_scale: "a = 1 đơn vị dựng", is_given: false}`

- Khi có trường này, cảnh PHẢI hiện câu `display_scale` (tiếng Việt, không thêm định danh kỹ thuật). `is_given == false`
  nghĩa là hình được vẽ ở `a = 1` như một **tỉ lệ hiển thị**, không phải dữ kiện của đề.
- Đáp số theo `a` đọc từ `route_d.answers` (đã kèm `a^dim`). Không tự nhân toạ độ hiển thị với `a`.
- Cảnh không có `length_unit` thì giữ nguyên hành vi hiện tại.

Fixture: `served-H01_CUBE`, `served-H07_…`, `served-H14_REGULAR_TETRAHEDRON` (có `length_unit`);
`served-pyramid-midpoint-area-AB` (không có).

## 5. Nguồn gốc dữ kiện (source provenance)

- `route_d.source_provenance[*].quotes` có thể hiện như "trích từ đề". Chỉ envelope **phục vụ** mới mang trường này.
- Envelope từ chối **cố ý không mang** lời gọi, trace hay quote: chúng là đầu ra mô hình chưa qua kiểm nguồn. Frontend
  không được tìm chúng ở đó.
- `objects[*].source.provenance` (`LAYOUT_DERIVED` …) nói vật/toạ độ do bố cục tất định chọn. Không trình bày chúng như
  dữ kiện đề.

## 6. Từ chối an toàn (`envelope.status == "unsupported"`)

Envelope từ chối có **đúng sáu khoá**: `status, reason_code, reason, learner_reason, failure_category, refusal_cause`.
Các giá trị đều thuộc từ vựng hệ đã có; preview không đặt mã mới.

| nhóm (phía server) | `failure_category` | `refusal_cause` | ví dụ `reason_code` | fixture |
|---|---|---|---|---|
| hệ thiếu năng lực | `capability_gap` | `UNKNOWN` | `UNSUPPORTED_CAPABILITY`, `CONDITIONAL_CLAUSE`, `OUT_OF_SCOPE` (*) | `refusal-capability-*` |
| thiếu / mơ hồ dữ kiện | `insufficient_specification` | `UNKNOWN` | `MISSING_DIMENSION`, `AMBIGUOUS_FACT` | `refusal-missing-*` |
| dữ kiện mâu thuẫn / suy biến | `geometry_generation_failed` | `SOURCE` chỉ khi bộ đọc đề của server tự đọc được độ dài ≤ 0 trong giả thiết (`NON_POSITIVE_LENGTH`); còn lại `UNKNOWN` | `INCONSISTENT_FACTS`, `COLLINEAR_POINTS`, `NON_POSITIVE_LENGTH` | `refusal-invalid-*` (`invalid-zero-length` = SOURCE, `invalid-zero-not-in-text` = UNKNOWN) |
| chưa xác minh được nguồn | `verification_gap` | `UNKNOWN` | `SOURCE_OBJECT_MISMATCH`, `QUOTE_NOT_IN_SOURCE` | `refusal-source-*` |
| kết quả / chứng nhận chưa qua kiểm (gồm lỗi interpreter/kernel khi dựng) | `verification_gap` | `UNKNOWN` | `ENGINE_SELF_CHECK_FAILED`, `PREVIEW_RESULT_INVALID`, `ENGINE_EXECUTION_FAILED` | `refusal-result-*` |
| không thể kết luận | `verification_gap` | `UNKNOWN` | `PROOF_UNVERIFIABLE`, `FIGURE_NOT_UNIQUE` | `refusal-inconclusive-*` |
| trích xuất / provider hỏng | `geometry_generation_failed` | `UNKNOWN` | `JSON_INVALID`, `FACT_INCOMPLETE` | `refusal-extraction-*` |
| toàn vẹn / identity | `geometry_generation_failed` | `UNKNOWN` | `PREVIEW_IDENTITY_CHANGED`, `PREVIEW_PROOF_STATUS_INVALID` | `refusal-integrity-*` |

(*) `OUT_OF_SCOPE` của Route D là lối thoát `unsupported` của bước trích xuất ("mệnh đề không ánh xạ được vào thư
viện hàm") trên một đề hình học. Nó KHÔNG phải phán quyết "môn học khác" của cổng phạm vi: preview không chạy phát hiện
miền. Vì vậy preview không bao giờ phát `out_of_scope`.

Bảng mã đầy đủ: `backend/app/ai/hybrid_preview.py::_NHOM`. Mã chưa có trong bảng rơi về `geometry_generation_failed` /
`UNKNOWN`, không bao giờ `capability_gap`. Nhóm là khái niệm phía server; frontend rẽ nhánh theo `failure_category` và
`refusal_cause`, không theo nhóm.

## 7. Thứ được phép hiển thị cho người học

- **Hiển thị:** `learner_reason` (tiếng Việt, đã kiểm: không định danh máy, không trường mẫu `{…}`, không trace, không
  quote của mô hình), và nhãn loại vấn đề tra từ `failure_category` qua `NHAN_LOAI_VAN_DE` có sẵn.
- **Luật về gợi ý:** chỉ `refusal_cause == "SOURCE"` mới được mời người học xem lại đề. Luồng hiện tại chỉ áp luật này
  cho `geometry_generation_failed`. Với `insufficient_specification`, `SimulationWorkspace` luôn hiện "Bổ sung dữ liệu
  còn thiếu vào đề rồi gửi lại — dạng bài này hệ có mô phỏng", bất kể `refusal_cause`. Preview phát loại này với
  `UNKNOWN` (ví dụ `AMBIGUOUS_FACT` khi mô hình tự đánh dấu mơ hồ), nên câu ấy vừa đổ cho đề vừa hứa năng lực. Đây là
  F6 (§9).
- **Không bao giờ hiển thị:** `reason_code`, tên nhóm, `runtime_identity`, `fingerprint`, `simulation_id`,
  `provider_mode`, `schema_version`, mã của cổng HTTP, `geometry_ir`, hay `construction_trace` thô. Khoá hiện có:
  `components/ui-hygiene.test.ts`.

## 8. Tương thích ngược

- Envelope phục vụ có cùng hình dạng với envelope `LLM_ONLY` (`generic.semantic_program` + `config` + `scene3d`).
  Khoá thêm duy nhất trong `scene3d` là `length_unit`, và frontend hiện bỏ qua nó. `route_d` nằm **ngoài** envelope.
- Frontend không được **đòi** `route_d` hay `length_unit`. Cảnh hiện có không mang chúng và phải chạy như cũ.
- Run này chưa nạp fixture vào frontend thật, vì không sửa `frontend/src`. Wave frontend phải chứng minh
  `store.loadEnvelope` nhận mọi `served-*` (vitest) trước khi dựa vào điều đó.

## 9. Việc frontend còn mở (nghiệm thu cho wave Scene3D)

| mã | việc | nghiệm thu |
|---|---|---|
| F1 | ký hiệu góc vuông chỉ vẽ từ chứng nhận backend | theo `hybrid-pre-main-hardening/frontend-handoff.md` F1; đối chiếu cổng P0 của `scene3d-plane-grid-camera` |
| F2 | `maTranKhung` tự vệ với ma trận không 3×3 / không đối xứng / không xác định dương | không toạ độ nào không hữu hạn; vitest với năm ma trận của test `Metric` backend |
| F3 | hiện `length_unit.display_scale` | §4; fixture có / không có `length_unit` |
| F4 | trình bày `goal_checks` như quan sát | §3; không chuỗi "đã chứng minh" nào trên mọi `served-*` |
| F6 (mới) | gợi ý của `insufficient_specification` phải đọc `refusal_cause` | với `UNKNOWN`: không mời sửa đề, không hứa "dạng bài này hệ có mô phỏng"; fixture `refusal-missing-*` |
| F5 (mới) | nhánh hiển thị riêng cho `verification_gap` | hiện nhãn `NHAN_LOAI_VAN_DE` đã có ("chạy được nhưng chưa đủ bằng chứng để phát"), nhưng tiêu đề/gợi ý rơi về mặc định "NGOÀI DANH MỤC MÔ PHỎNG", sai cho loại này; cần tiêu đề và gợi ý không hứa "dạng bài này hệ có mô phỏng" |
