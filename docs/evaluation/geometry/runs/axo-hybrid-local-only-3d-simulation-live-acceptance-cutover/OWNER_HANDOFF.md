# Owner handoff — các blocker còn lại

Nhánh: `integration/local-only-3d-live-acceptance` (worktree `.superpowers/worktrees/local-only-3d-live-acceptance`), rẽ từ
`38c6efbdb` (/9). **Chưa merge, chưa push, `main` không đổi.** Mặc định `HYBRID_ROUTE_MODE` vẫn `live`.

## Quyết định cần owner (theo thứ tự)

### 1. Merge hai commit sản phẩm (khuyến nghị: có, độc lập với cutover)

| Commit | Vì sao |
|---|---|
| `7554e2b72` fix(local-slm) keep-alive | Lỗi thật, tái hiện tất định: sau > 5 s nghỉ, mọi lượt SLM thứ hai ⇒ 503 và server bị dừng. Ảnh hưởng `local-only-*`, `offline-lab`, `local-slm`, `local-first`, `local-shadow`. Test có nền đỏ. Candidate đã đóng băng lại (`a0f979392`). `CACHE_VERSION` không đổi (chỉ vận chuyển). |
| `e10697092` frontend keyless | Bản vá /9 + thông điệp 503 cục bộ; chỉ đổi hành vi khi `/api/health` báo `localOnlyMode`/`aiAvailable` — ở `live` hành vi cũ giữ nguyên (test `keeps the cloud wording in live mode`). |

Chạy trước khi merge: kết quả T3 trong `SIMULATION_REGRESSION_REPORT.md`.

### 2. Mở rộng câu lệnh mô phỏng của parser tất định (blocker chính của Mode A)

- **Root cause:** `backend/app/ai/local_geometry_parser.py` luật 7b (`:3881`) chỉ nhận
  `^(Hãy )?(mô phỏng|vẽ) hình( chóp| lăng trụ)?( và điểm X)?$`. Câu "Hãy mô phỏng hình lập phương / tứ diện / hình hộp chữ nhật / lăng trụ",
  "Hãy dựng hình chóp", "Vẽ hình chóp S.ABCD.", "Mô phỏng hình hộp chữ nhật đó", "Hãy mô phỏng hình chóp đều đó" ⇒ `UNPARSED_GOAL_CANDIDATE`
  ⇒ SLM ⇒ Source Gate chặn. 11/28 ca SIMULATE_ONLY.
- **Đề xuất (không viết trong /10):** một luật dùng chung: động từ `{mô phỏng, vẽ, dựng, biểu diễn}` + danh từ khối bất kỳ đã có trong
  `_SOLID_WORDS` (cùng tệp, dùng ở 7c-0) + tuỳ chọn ký hiệu khối **phải trùng** khối đã khai báo + tuỳ chọn "đó/này" ⇒ `construct_object`
  cho khối chính. Không theo đề, không nới Source Gate (trích dẫn vẫn là nguyên văn). Bề mặt parser đổi ⇒ quyết định `CACHE_VERSION`
  theo §5 CLAUDE.md và **đo lại trên một bộ mới, mù** — bộ của run này đã lộ.

### 3. Thông điệp thiếu dữ kiện (UX, an toàn không đổi)

`hybrid_preview.classify_refusal` gắn `capability_gap` khi kiểm tra xác định "UNPROVED_DUE_TO_CAPABILITY_GAP"; UI hiện
"Axo chưa hỗ trợ phép dựng này" cho đề chỉ thiếu số đo, trong khi `route_d.refusal.clarification` (`MISSING_DATA`, "nói rõ các số đo cần
thiết") đã có. Đề xuất: frontend ưu tiên hiện `clarification.question` khi có. (`local_ai_ux` cũng gắn sai `OUT_OF_SUPPORTED_SCOPE` cho ca này.)

### 4. Đề không dấu bị gắn "thuộc môn học khác"

V18, C24 (đề hình học không dấu) ⇒ `out_of_scope` + "Bài này thuộc môn học khác". Ma trận /9 ghi hỗ trợ VN11 — trên đường sản phẩm
live thì không. Cần tra cổng miền trước provider.

### 5. Client thử lại 504 cho runtime cục bộ

`frontend/src/llm/client.ts::postJsonWithBoundedRetry` thử lại tối đa 2 lần với 502/504 ⇒ một `LOCAL_SLM_TIMEOUT` (45 s) giữ loading
~135 s. Đề xuất: không thử lại khi `reason_code` là `LOCAL_SLM_TIMEOUT`/`LOCAL_SLM_BUSY` (backend đã nói rõ), hoặc ngân sách thời gian tổng.

### 6. Nhỏ

- Điểm bố trí `O` (tâm đáy chóp đều/tứ diện đều) nằm trong nhóm hiển thị `given` dù đề không nêu (`V04, V27, C04, C05, C16, C19`).
- V20: quan hệ "(SAB) ⊥ (ABCD)" thoả nhưng không có bước dựng nào nêu ra cho người học.
- V17: kéo bắt đầu ở tâm canvas không xoay (2/2 lượt); root cause chưa xác lập.
- U08: đặt lại góc nhìn lần hai làm một nhãn DOM lệch 8 px (camera trùng).
- C20: góc AB'–BC' trong lập phương không cho cạnh (xác định tới đồng dạng) bị từ chối `MISSING_DIMENSION`.

### 7. Đổi mặc định sang `local-only-scoped`

Không khuyến nghị lúc này (`PRODUCTION_CUTOVER_DECISION.md`). Bản vá /9 vẫn áp được; quyết định là của owner.

## Chưa đo (không suy ra từ im lặng)

`PHYSICAL_TARGET_HARDWARE` (4–8 GiB), `FULLY_OFFLINE_RUNTIME` (ngắt mạng thật), `GEMINI_PARITY`, `EXTERNAL_INDEPENDENCE` (bộ của run do
agent viết), `REAL_STUDENT_USABILITY`, RSS Chromium dài hạn / bộ nhớ WebGL.
