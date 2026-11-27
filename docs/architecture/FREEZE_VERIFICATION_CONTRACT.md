# Freeze Verification Contract — Historical Freeze Integrity vs Integrated Candidate Lifecycle

> **Trạng thái:** Hợp đồng vận hành hiện hành (cập nhật 2026-11-27 kèm quy trình Integrated Candidate Lifecycle).  
> **Nguyên tắc bất biến:** Không sửa bản lưu lịch sử, không sửa `freeze_protocol.md` lịch sử và không gán kết quả benchmark cũ thành phép đo mới cho candidate sau.

---

## 1. Dòng Phả Hệ Candidate (`4978ac01f` → Integrated Security Release)

1. **Mốc lịch sử được bảo toàn (`4978ac01f`, manifest tại `f2cc62b1e`):**
   - **Archive byte-identical:** [`prior-EVALUATION_CANDIDATE-4978ac01f.json`](../evaluation/geometry/runs/integrated-security-release/prior-EVALUATION_CANDIDATE-4978ac01f.json) (`SHA-256 = d5198276e8415014507f42502e7efeaacdf9767f3dc0c63fc17c40370c871a68`).
   - **Commit nguồn:** `4978ac01f3240d08ae259d532edcc83c2c5af5e4` (`product_commit_sha = 3104635dbd74118d2bb6db9b1f91fbd0a5f734ae`).
   - **Mã đo đạc:** `127` tệp · `tree_hash = 7bd85b6e2c8719e4fb6192e362ce17505588081623c90514dda0a83e88b4dd04` · `CACHE_VERSION = 158`.
   - **Mốc sớm hơn:** `600f5105d4222cd6835cc916b34d5cb3f11610e6` (`109` tệp, `CACHE_VERSION = 132`) vẫn được Git history & `test_I2_every_historical_candidate_reproduces_under_its_recorded_rule` xác minh tự động.
2. **Active Integrated Candidate (`EVALUATION_CANDIDATE.json` hiện hành):**
   - **Tệp manifest:** [`EVALUATION_CANDIDATE.json`](../evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json).
   - **Commit nguồn (`source` / `product_commit_sha`):** `473cb68ded13d35f413032e9c45aea36960928ea` (C5 auth/cookie/CORS/DB + proxy trust & CSRF closure).
   - **Mã đo đạc:** `127` tệp · `tree_hash = 92f8e24dd56b5bb0eda60fa85cdf3caabea71a0c7b5ed0e741922f7b2cbb1ab7` · `cay_lam_viec_sach = true` · `CACHE_VERSION = 158`.
   - **Biên thay đổi:** chỉ `backend/app/accounts/router.py`, `backend/app/main.py`, `backend/app/persistence/db.py` (`core_evaluation_changed == []`).
   - **Trạng thái đánh giá:** `OFFLINE_REVALIDATED_ONLY` · `LIVE_EVALUATION_PENDING_AUTHORIZATION` (xem [`candidate_lineage.json`](../evaluation/geometry/runs/integrated-security-release/candidate_lineage.json)).

---

## 2. Hai Chế Độ Kiểm Chứng Độc Lập (`freeze_evaluation_candidate.py`)

| Chế độ | Lệnh thực thi | Ý nghĩa kỹ thuật |
|---|---|---|
| **Active Strict Verification (`--verify`)** | `python backend/scripts/freeze_evaluation_candidate.py --verify` | Băm trực tiếp working tree / `HEAD` của `MEASURED_SYSTEM_PATHS` và `product_commit_sha` so với `EVALUATION_CANDIDATE.json` đang active. Phải trả exit `0` khi ở trạng thái phát hành sạch và báo `FAIL` (exit `1`) ngay nếu bất kỳ mã sản phẩm nào trôi. |
| **Historical Provenance Verification (`--verify-historical`)** | `python backend/scripts/freeze_evaluation_candidate.py --verify-historical --manifest <path> --json` | Kiểm tra từng byte của bản snapshot lịch sử (mặc định là active manifest, hoặc bản archive `prior-EVALUATION_CANDIDATE-*.json`) khớp với Git tree tại đúng commit nguồn lịch sử — bảo đảm dữ liệu nghiên cứu cũ không bao giờ bị sửa lặng lẽ. |

> **Ranh giới diễn giải bắt buộc:** Bảo toàn vùng lõi (`core_evaluation_changed == []`) chỉ chứng minh mã thuật toán hình học/AI không đổi; nó không tự động sao chép điểm benchmark lịch sử của `4978ac01f` làm kết quả đo mới của integrated candidate, và không tự cấp quyền chạy live evaluation (`PENDING_OWNER_DECISION` / `paid_project_confirmed=false`).

---

## 3. Quy Trình Phân Loại Thay Đổi & Tái Sử Dụng Candidate Lifecycle

| Loại thay đổi | Ví dụ vùng mã | Yêu cầu cập nhật Candidate & Kiểm chứng |
|---|---|---|
| **1. Product-only ngoài `MEASURED_SYSTEM_PATHS`** | Landing UI, Sidebar, static assets, `frontend/vercel.json` | Chú ý `product_commit_sha` đổi khi chạm `frontend/src/**`: nếu chỉ giữ snapshot cũ thì `--verify-historical` PASS còn `--verify` sẽ báo `product_commit_sha` drift; trước release sản phẩm tích hợp, xác lập integrated candidate mới theo đúng quy trình sạch. |
| **2. Measured-system ngoài lõi Hình học/AI** | HTTP/Auth/CSRF/Proxy (`accounts/`, `main.py`), `persistence/db.py`, Docker/deps | Lưu archive bản candidate cũ (`prior-*.json`), commit mã nguồn sạch trước (`<SOURCE_SHA>`), chạy `freeze_evaluation_candidate.py` từ bản clone/worktree sạch (`cay_lam_viec_sach=true`), giữ `core_evaluation_changed == []`, ghi `candidate_lineage.json` (kèm runtime env & dependency fingerprint), chạy `refresh_pending_templates.py` giữ nguyên `PENDING_OWNER_DECISION`, chạy offline revalidation & full regression. |
| **3. Thay đổi Lõi Đánh Giá (Core Evaluation)** | `backend/app/simulation/`, `backend/app/ai/`, prompts, taxonomy, schema IR, SLM, `CACHE_VERSION` | Bắt buộc tuân thủ đầy đủ chính sách đánh giá nghiên cứu (offline + đề xuất live pilot riêng nếu chạm bề mặt model/prompt), tuyệt đối không tái dùng kết quả cũ. |
| **4. Live Evaluation (`C21`/`C26`/Pilot mới)** | Chạy `run_s2_student_language_pilot.py` | Luôn đòi hỏi template khớp chính xác `measured_system` hiện hành và phê duyệt tường minh của Owner (`APPROVED_BY_USER` / `EXPLICIT_OWNER_DELEGATED_EXECUTION` + paid verification). Approval của `4978ac01f` bị từ chối tuyệt đối trên runtime mới. |

---

## 4. Lệnh Tái Kiểm Chứng Nhanh

```bash
python backend/scripts/freeze_evaluation_candidate.py --verify
python backend/scripts/freeze_evaluation_candidate.py --verify-historical --json
python backend/scripts/freeze_evaluation_candidate.py --verify-historical --manifest docs/evaluation/geometry/runs/integrated-security-release/prior-EVALUATION_CANDIDATE-4978ac01f.json --json
python backend/scripts/lock_cache_identity.py --verify
```
