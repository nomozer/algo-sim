# Báo Cáo Sửa Chữa Tính Đồng Bộ Schema và Đóng Băng Lại Candidate Ngoại Tuyến
**WAVE_ID:** `SCHEMA_SYNC_AND_CANDIDATE_REFREEZE_REPAIR_OFFLINE`  
**NGÀY:** 2026-09-23  
**START_HEAD:** `c69eef966fffb4f7a8fc788b7982d02bc76baa1e`  
**PHẠM VI:** Offline 100%, 0 cuộc gọi mạng, 0 Gemini API call, bảo toàn working tree (`favicon.svg`).

---

## 1. Bối Cảnh và Nguyên Nhân Gốc (Root Cause)

1. **Divergence Tồn Tại Sẵn Trong Candidate 5a5534fe:**
   Tại commit `5a5534fe` (`feat(geometry): implement right prism compiler vertical slice offline`), mã Pydantic trong `backend/app/simulation/semantic_program/contract.py` đã được thêm trường `provenance: Optional[Literal["GIVEN", "MODEL_ASSUMPTION", "LAYOUT_DERIVED"]]` vào cả `MemoryDeclaration` và `DeclarePointStmt`. Tuy nhiên, kịch bản xuất lược đồ chuẩn tắc `backend/scripts/export_semantic_program_schema.py` đã không được chạy lại trước khi đóng băng candidate. Do đó, cả hai file schema JSON trên đĩa (`docs/schemas/semantic_program.schema.json` và `frontend/src/simulations/domains/semantic/semantic_program.schema.json`) đã bị thiếu hai trường này. Con dấu candidate tại `5a5534fe` (`tree_hash = fc88b200e9de094b…`) đã vô tình đóng băng một sự bất nhất nội tại giữa Pydantic model và JSON schema.

2. **Sự Cố Làm Yếu Test Sync ở Gate 2:**
   Trong đợt sửa chữa hồi quy Gate 2, để giữ nguyên con dấu candidate `5a5534fe` mà không vi phạm lệnh cấm sửa đổi candidate, file `backend/tests/semantic_program/test_schema_sync.py` đã được nới lỏng bằng một nhánh điều kiện ngoại lệ bỏ qua sự vắng mặt của trường `provenance`. Nhánh ngoại lệ này giúp full-suite của Gate 2 xanh (6.142 passed), nhưng đã vi phạm bất biến đồng bộ nghiêm ngặt (strict schema synchronization invariant).

---

## 2. Các Biện Pháp Kỹ Thuật Đã Thực Hiện

### 2.1. Tái Xuất Lược Đồ Chuẩn Tắc (Canonical Schema Re-export)
Đã chạy kịch bản canonical `backend/scripts/export_semantic_program_schema.py` để sinh lại đồng nhất hai file schema:
- `docs/schemas/semantic_program.schema.json`
- `frontend/src/simulations/domains/semantic/semantic_program.schema.json`

Giá trị băm SHA-256 sau khi xuất lại (chuẩn hóa LF):
`7610ff090b50646fb98a46dd261b2f82014c292dcd6f74392a5f95c850016fa1`  
Khớp 100% từng byte giữa hai bản docs và frontend, bổ sung đầy đủ trường `provenance` vào thuộc tính của `MemoryDeclaration` và `DeclarePointStmt`.

### 2.2. Khôi Phục Kiểm Thử Đồng Bộ Nghiêm Ngặt (Strict Schema Sync Restoration)
File `backend/tests/semantic_program/test_schema_sync.py` đã được gỡ bỏ hoàn toàn nhánh ngoại lệ, khôi phục các xác nhận bình đẳng nghiêm ngặt:
- `docs_str == expected_str`
- `frontend_str == expected_str`
- `docs_str == frontend_str`
- Xác nhận trực tiếp sự hiện diện của trường `provenance` trong `MemoryDeclaration` và `DeclarePointStmt`.
- Thêm kiểm tra `test_exporter_idempotence` xác nhận việc chạy lại exporter không tạo ra diff.

Thay đổi này đã được đóng gói độc lập tại **Commit 1**:  
[`6eb23e8d`](file:///d:/Documents/projects/algo-sim) `fix(schema): restore semantic program schema coherence`

### 2.3. Đóng Băng Lại Candidate Chuẩn Tắc (Candidate Refreeze)
Vì `frontend/src/simulations/domains/semantic/semantic_program.schema.json` nằm trong `MEASURED_SYSTEM_PATHS` (thuộc 103 file mã sản phẩm đo lường), việc cập nhật schema làm thay đổi `measured_system.tree_hash`.
Đã chạy công cụ canonical `backend/scripts/freeze_evaluation_candidate.py` để cập nhật `docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json`:
- `measured_system.tree_hash`: `fc88b200e9de094b…` → `669ea2f160810c4f89e24fbe985abfefcc2f82a8f65e1a8fe0b9e1e9b47f9f95`
- `schema_semantic_program.hash`: `3db1e1cfeb320eb1…` → `7610ff090b50646fb98a46dd261b2f82014c292dcd6f74392a5f95c850016fa1`
- `so_file`: 103 file
- `commit`: `6eb23e8daef5ece1349859a5a73641f245ca8a42` (`6eb23e8d`)
- `cay_lam_viec_sach`: `true` (kịch bản đã ghi nhận ngoại lệ hợp lệ cho `favicon.svg` của người dùng và chính file freeze đang chạy)

Đồng thời, cập nhật nhật ký độ lệch candidate tại `docs/evaluation/geometry/product-response-contract-alignment/CANDIDATE_DIVERGENCE.json` với giá trị băm mới `669ea2f160810c4f89e24fbe985abfefcc2f82a8f65e1a8fe0b9e1e9b47f9f95`.

### 2.4. Chính Sách Cache (Cache Policy Stability)
- `CACHE_VERSION` được giữ nguyên ở mức **100**.
- Căn cứ: Theo `backend/app/runtime_identity.py`, hàm `semantic_environment_fingerprint()` băm trực tiếp `generate_json_schema()`. Do hàm Python này vốn dĩ đã sinh ra cấu trúc có `provenance` từ commit `5a5534fe`, `semantic_environment_hash` runtime không thay đổi một bit nào (`e79a0b7aaba34ce7…`).
- Lệnh `python backend/scripts/lock_cache_identity.py --verify` thoát mã 0, xác nhận không cần và không được phép tăng cache lên 101.

### 2.5. Không Biến Động Mã Sản Phẩm và Bảo Toàn Working Tree
- `git diff START_HEAD..HEAD -- backend/app` hoàn toàn rỗng (0 bytes).
- Không có bất kỳ thay đổi nào trong logic compiler, fact graph, hay routing.
- Tệp `frontend/public/favicon.svg` bị xóa bởi người dùng được giữ nguyên trạng thái uncommitted, không bị stage hay can thiệp.

---

## 3. Kết Quả Kiểm Thử Thẩm Quyền (Verification Results)

1. **Targeted Tests:**
   - `test_schema_sync.py`: 2 passed (Strict sync + Exporter idempotence)
   - `test_evaluation_candidate.py`: 13 passed (Candidate freeze verification)
   - `test_cache_identity.py`: 15 passed (Cache identity stability)
   - `test_prism_primitive_compiler.py`: 25 passed
   - `test_geometry_primitive_compiler.py`: 42 passed
   - `test_docs_information_architecture.py`: 38 passed
   - `test_thesis_acceptance_matrix.py`: 52 passed
   - Tổng cộng: **187 passed** liên quan trực tiếp.

2. **Candidate & Cache Verifications:**
   - `python backend/scripts/freeze_evaluation_candidate.py --verify` → **PASS** (Exit 0)
   - `python backend/scripts/lock_cache_identity.py --verify` → **PASS** (Exit 0)

---

## 4. Kết Luận

Wave sửa chữa đã giải quyết dứt điểm sự bất nhất lịch sử giữa Pydantic model và schema JSON, khôi phục hoàn toàn tính nghiêm ngặt của CI assertion, cập nhật con dấu candidate chính xác mà không phá vỡ tính ổn định của cache version 100 hay thay đổi mã sản phẩm.

Hệ thống đã đạt đầy đủ điều kiện để chuyển sang wave tiền đăng ký kiểm chứng trực tiếp:  
`NEXT_ACTION = SECOND_FAMILY_LIVE_SCHEMA_REVALIDATION_PREREGISTRATION`
