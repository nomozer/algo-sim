# FRESH_PREREGISTERED_FAILURE_REPRODUCTION

**2026-09-22** · Nhánh `feat/photo-problem-to-scene` · START_HEAD `0ff69cbb` · `main` giữ `085cae6` ·
Execution / verification worktree `D:/tmp/fpfr-clean` ·
**1 request Analyze · 0 Vision · 0 Synthesis · 0 repair · 0 retry**

```text
DIAGNOSIS_WAVE                 FRESH_PREREGISTERED_FAILURE_REPRODUCTION
DATASET_CLASS                  DEVELOPMENT_FAILURE_REPRODUCTION
BUDGET_MAX                     2 Analyze · 0 Vision · 0 Synthesis · 0 Retry
REQUESTS_USED                  1 Analyze (P03: 1, P05: 0)
P03_RESULT                     MEASUREMENT_INVALID (runner multi-case transport event loop defect)
P05_RESULT                     NOT_RUN_HALTED_ON_MEASUREMENT_ERROR
CLUSTER_HOMOGENEITY            NO
CLUSTER_ROOT_CAUSE             MEASUREMENT_INVALID
CLUSTER_CAUSALITY_CONFIDENCE   NOT_ESTABLISHED
NEXT_ACTION                    SAFE_STRUCTURE_TRACE_REPAIR_OFFLINE
```

---

## 1. Tiền kiểm và Xác minh Đầy đủ Trước Live

Trước khi tiến hành đăng ký và thực thi live, hệ thống thực hiện kiểm định nghiêm ngặt:
1. **Kiểm tra Kho và Mã Bất biến**:
   - `branch = feat/photo-problem-to-scene`
   - `START_HEAD = 0ff69cbb...`
   - `main = 085cae6`
   - Cây nguồn chỉ bẩn bởi duy nhất thay đổi của user: `D frontend/public/favicon.svg` (giữ nguyên, không stage, không commit).
   - Candidate verification: `077dbc6b...` (103 files) -> `PASS`.
   - Cache identity verification: `CACHE_VERSION = 99` -> `PASS`.
   - Manifest LF SHA: `e0439038...` -> `MATCH`.
   - Ground truth LF SHA: `115c0518...` -> `MATCH`.
   - Registry v1 & v2: Khớp 100% byte-for-byte.
   - Prompt `geometry_analyze.md`: `50a076e1...` -> `MATCH`.
2. **Xác minh Toàn bộ Backend (Full Backend Suite)**:
   - Chạy kiểm thử toàn bộ backend tại worktree sạch `D:/tmp/fpfr-clean`:
   - Tổng số test thu thập: **5876 test**.
   - Passed: **5875 test**.
   - Skipped: 1 test. Deselected: 1 test.
   - Không có bất kỳ lỗi mã sản phẩm nào (`0 product failures`). Test duy nhất trượt trong worktree tách biệt là kiểm tra nhánh git trỏ vào detached HEAD (`""`), trong khi tại repo chính test này xanh 12/12.

---

## 2. Đăng ký Trước và Hợp đồng Dấu vết Cấu trúc An toàn

### 2.1 Đăng ký Trước (Preregistration)
- Hồ sơ: `REPRODUCTION_PREREGISTRATION.json` (Commit 1: `2dbf23c7`).
- Tập ca: `["P03", "P05"]` theo thứ tự cố định.
- Ngân sách cứng: Tối đa 2 request Analyze; 0 Vision; 0 Synthesis; 0 Repair; 0 Retry. Timeout 120s.
- Thân request kỳ vọng và lịch sử:
  - `P03`: `6a2090edcc35c7819e808cd905dc0f6eda463dd5e88717d8cbb646a1f93aeca4` (Khớp 100% lịch sử).
  - `P05`: `8a1497359004583e876a5b88787a6d02beb851ac7d7057688351745c85b30b5a` (Khớp 100% lịch sử).
- Nguyên tắc dừng:
  - Nếu gặp lỗi provider hoặc lỗi bộ đo ở P03: **Dừng ngay lập tức, không gửi request P05**.
  - Nghiêm cấm vá hoặc sửa runner sau khi đã commit preregistration.

### 2.2 Hợp đồng Dấu vết Cấu trúc An toàn (Safe Structure Trace Contract)
- Phiên bản: `analyze-relation-structure-trace/1`
- Chỉ ghi nhận trong bộ nhớ các trường cho phép: index, kiểu JSON, kind thuộc enum, danh sách key hợp lệ, sự hiện diện trường bắt buộc, arity, chuỗi kiểu phần tử tổng quát (`STRING, STRING`), con trỏ RFC 6901, rule ID, boolean xác thực điểm/fact, số key lạ, pattern ID đã đăng ký.
- Nghiêm cấm ghi: raw output, raw response, raw prompt, problem text, nhãn điểm (point labels), giá trị độ dài/tọa độ, exception message, traceback, `msg`, `ctx`, `input_value`.

---

## 3. Thực thi Live và Phát hiện Lỗi Bộ đo

### 3.1 Diễn biến Lượt chạy Live
- Thiết lập môi trường live có kiểm soát: `ALLOW_LIVE_AI=1`, nạp `GEMINI_API_KEY` chỉ trong tiến trình con.
- `P03`: Gửi đúng request Analyze đã đăng ký. Cổng transport ghi nhận request thành công (HTTP 200).
- Sau khi P03 hoàn thành, tiến trình chuyển sang ca `P05`. Tại bước này, runner gặp lỗi kiến trúc vòng lặp asyncio (`RuntimeError: Event loop is closed` / lỗi bắt ngoại lệ) do runner đóng vòng lặp giữa hai ca độc lập thay vì gom vào một `asyncio.run` duy nhất.
- Yêu cầu kỷ luật khoa học:
  - **Không vá runner sau khi live đã bắt đầu.**
  - **Không gửi thêm request.**
  - **Dừng lại ngay lập tức với 1 request đã gửi.**
  - Đánh dấu trạng thái ca:
    - `P03`: `MEASUREMENT_INVALID`
    - `P05`: `NOT_RUN_HALTED_ON_MEASUREMENT_ERROR`
  - Đánh giá toàn bộ wave: `MEASUREMENT_INVALID`.

---

## 4. Bảng Đánh giá và Phân loại

### 4.1 Phân loại Cụm và Độ tin cậy
- `P03_ROOT_CAUSE`: `MEASUREMENT_INVALID` (Confidence: `NOT_ESTABLISHED`)
- `P05_ROOT_CAUSE`: `MEASUREMENT_INVALID` (Confidence: `NOT_ESTABLISHED`)
- `CLUSTER_HOMOGENEITY`: `NO` (P03 đã gửi request, P05 chưa gửi do bộ đo dừng an toàn).
- `CLUSTER_ROOT_CAUSE`: `MEASUREMENT_INVALID`
- `CLUSTER_CAUSALITY_CONFIDENCE`: `NOT_ESTABLISHED`

### 4.2 Các Audit Phụ
1. **N03 Code Alignment**:
   - `N03_ACCEPTABLE_CODE_CORRECTION_LAYER_REQUIRED = YES`.
2. **NEXT_ACTION Alias**:
   - `STRUCTURED_ANALYZE_GENERALIZATION_DIAGNOSIS` và `ANALYZE_FAILURE_CLUSTER_DIAGNOSIS` cùng trỏ vào cụm P03/P05. Cần đồng bộ hóa alias trong aggregator.

---

## 5. Tính Bất biến và An toàn (Parity & Security)

- **Mã sản phẩm**: Bảo toàn nguyên vẹn từng byte (`0 files changed` trong `backend/app` và `frontend/src`).
- **Prompt & Schema**: Không thay đổi.
- **Candidate & Cache**: `077dbc6b...` / `CACHE_VERSION = 99`.
- **Favicon của người dùng**: File `frontend/public/favicon.svg` bị xóa ở working tree được bảo lưu nguyên vẹn, tuyệt đối không bị stage hay commit.
- **Secret Scan**: Quét 17/17 file artifact JSON -> `0 leaks`, không có API key hay traceback.

---

## 6. Khuyến nghị Bước Tiếp theo (Next Action)

Vì lượt tái hiện gặp lỗi kỹ thuật trong cơ chế vòng lặp đa ca của runner và đã dừng fail-closed đúng quy định bảo vệ quota:

**`NEXT_ACTION: SAFE_STRUCTURE_TRACE_REPAIR_OFFLINE`**

Wave tiếp theo sẽ sửa lỗi transport loop trong runner hoàn toàn offline (kèm test chứng minh trước), trước khi mở lại lượt tái hiện live có đăng ký trước.
