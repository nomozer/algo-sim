# Freeze Verification Contract — Historical Freeze Integrity vs Current Product Integrity

> **Trạng thái:** Hợp đồng vận hành hiện hành (bổ sung theo Phương án 1, 2026-11-21).  
> **Nguyên tắc bất biến:** Không sửa [EVALUATION_CANDIDATE.json](../evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json), không sửa `freeze_protocol.md` lịch sử và không sửa kết quả benchmark đã niêm phong.

---

## 1. Mốc Candidate Lịch Sử Hiện Đang Bảo Toàn

- **Tệp manifest:** `docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json`
- **Commit nguồn đã đóng băng:** `600f5105d4222cd6835cc916b34d5cb3f11610e6` (`2026-11-19T10:09:18+00:00`)
- **Luật danh tính sản phẩm:** `product-paths-excluding-test-only/1` (`product_commit_sha = 600f5105d4222cd6835cc916b34d5cb3f11610e6`)
- **Mã sản phẩm đo đạc (`measured_system`):** `109` tệp · `tree_hash = 78edfa1784625e9bca8f1a4cd70b60359d198ba77530986903175a57e18206a7`
- **Phiên bản bộ nhớ đệm & hợp đồng IR:** `CACHE_VERSION = 132` · `spec_version_ir = 1.0` · `SEALED = DA_NIEM_PHONG`

---

## 2. Hai Chế Độ Kiểm Chứng Độc Lập (`freeze_evaluation_candidate.py`)

| Chế độ | Lệnh thực thi | Ý nghĩa kỹ thuật | Kết quả kỳ vọng sau khi phát triển thêm Landing / Auth |
|---|---|---|---|
| **Historical Freeze Integrity (`--verify-historical`)** | `python backend/scripts/freeze_evaluation_candidate.py --verify-historical --json` | Đọc `EVALUATION_CANDIDATE.json`, xác minh `commit` tồn tại trong Git object DB, băm lại trực tiếp toàn bộ `measured_system.paths`, `schema_semantic_program`, `dev/cases.json` và `product_commit_sha` từ **Git tree tại đúng commit nguồn** (không checkout, không chạm working tree), đồng thời đối chiếu byte của manifest trong working tree với `HEAD`. | **PASS (exit `0`)** chừng nào bản đóng băng lịch sử và Git history gốc còn nguyên vẹn. |
| **Strict Current Verification (`--verify`)** | `python backend/scripts/freeze_evaluation_candidate.py --verify` | Băm trực tiếp **working tree / HEAD hiện tại** của `MEASURED_SYSTEM_PATHS` (`backend/app`, `frontend/src/simulations/domains/semantic/...`) và `product_commit_sha` hiện tại so với `EVALUATION_CANDIDATE.json`. | **FAIL (exit `1`)** là kết quả **đúng theo hợp đồng** khi có thay đổi mã sản phẩm hợp lệ sau mốc `600f5105d` (vd: `backend/app/accounts/` hoặc Landing frontend). |

> **Ranh giới diễn giải bắt buộc:** Một kết quả `--verify-historical` đạt **PASS** chỉ chứng minh bản đóng băng nghiên cứu tại `600f5105d` còn nguyên vẹn và tái lập được; nó **không** khẳng định mã sản phẩm ở `HEAD` hiện tại đồng nhất với bản đóng băng hay tự động kế thừa kết quả benchmark cũ.

---

## 3. Phân Tách Tác Động Của Thay Đổi Sản Phẩm Sau Mốc Đóng Băng

1. **Thay đổi tầng ứng dụng ngoài vùng đánh giá** (như giao diện Landing `/about`, đăng nhập Admin tại `backend/app/accounts/`, CLI `manage_admin.py`):
   - **Không** sửa dữ liệu hay kết quả nghiên cứu lịch sử.
   - Phải được kiểm chứng bằng bộ hồi quy sản phẩm (Frontend Vitest, Backend Auth/Security/DB Pytest, Playwright E2E) và kiểm chứng bảo toàn vùng lõi (`diff_measured_system_vs_commit` xác nhận `core_evaluation_changed == []`).
   - Không khẳng định hệ tích hợp hiện hành đã chạy lại benchmark mới.
2. **Khi nào bắt buộc chạy lại benchmark:**
   - Bất kỳ chỉnh sửa nào trong vùng lõi đánh giá: `backend/app/simulation/`, `backend/app/ai/`, `frontend/src/simulations/domains/semantic/`, prompt trích xuất, taxonomy nghĩa vụ, tập visual primitives, schema IR, hoặc `CACHE_VERSION`.
   - Khi đó bài kiểm thử bảo toàn vùng lõi (`test_ma_san_pham_khong_troi_khoi_ban_da_dong_bang`) sẽ báo **FAIL** ngay lập tức.
3. **Khi nào tạo candidate nghiên cứu mới:**
   - Chỉ khi khởi động một chiến dịch đánh giá mới được Owner phê duyệt, với quy trình ghi nhận phiên bản, commit sạch (`cay_lam_viec_sach = true`) và provenance riêng — **không** ghi đè candidate lịch sử để dập tắt cảnh báo của các tính năng sản phẩm không thuộc nghiên cứu.

---

## 4. Cách Tái Kiểm Chứng Snapshot Lịch Sử

Chạy từ gốc kho hoặc từ bất kỳ Git worktree nào (không làm bẩn working tree):

```bash
python backend/scripts/freeze_evaluation_candidate.py --verify-historical --json
python backend/scripts/lock_cache_identity.py --verify
```

Để kiểm tra xem working tree hiện tại đã khác gì so với mốc đóng băng:

```bash
python backend/scripts/freeze_evaluation_candidate.py --verify
```

---

## 5. Giới Hạn Bảo Đảm Của Cơ Chế Kiểm Chứng

- **Phát hiện được:** sửa hash/số file trong manifest; trỏ tới commit không tồn tại hoặc Git object bị hỏng; sửa metadata không hợp lệ (`cay_lam_viec_sach=false`, rule lạ, JSON hỏng); sửa **đồng thời** cả `commit` lẫn `tree_hash` của `EVALUATION_CANDIDATE.json` trong working tree (bị chặn bởi `git_head_provenance: manifest_modified_vs_head`); sửa bất kỳ tệp nào trong vùng lõi `backend/app/simulation/`, `backend/app/ai/`, `frontend/src/simulations/domains/semantic/`.
- **Giới hạn trung thực:** Cơ chế `git_head_provenance` dựa trên lịch sử Git `HEAD` cục bộ. Nếu một tác nhân có toàn quyền viết lại lịch sử commit Git (rewrite history + sửa manifest đã commit), việc chống giả mạo tuyệt đối đòi hỏi chữ ký commit mật mã (GPG/SSH signed commits) hoặc bản ghi chứng thực bất biến ngoài kho Git (external attestation / immutable release artifact).
