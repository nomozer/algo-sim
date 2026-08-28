# PHASE 7B — CHECKLIST THI HÀNH

> Danh sách này là **cổng**, không phải lời nhắc. Mỗi ô có **lệnh kiểm** hoặc
> **tên cổng máy** đứng sau; ô nào chỉ kiểm được bằng mắt thì ghi rõ *(người)*.
>
> Trạng thái cập nhật cuối: **2026-08-28** tại `3a289d5`.
> **Trạng thái sống — SINH RA, không gõ tay**: [PHASE7B_READINESS_REPORT.md](PHASE7B_READINESS_REPORT.md)
> (`scripts/report_holdout_readiness.py --md`). Đừng sửa nó bằng tay.
>
> ⚠️ [PHASE7B_READINESS.md](PHASE7B_READINESS.md) là **bản tường thuật ĐÔNG CỨNG**
> của 7A.3 tại `641ac5f` — tên gần giống, nội dung KHÔNG tự cập nhật. Tra nó để
> biết *vì sao*, đừng đọc như trạng thái hiện tại.

---

## A. PRECONDITION — chưa đủ thì KHÔNG rút seed

| | Việc | Kiểm bằng | Trạng thái |
|---|---|---|---|
| ☑ | **`k` đã freeze** | [HOLDOUT_K_FINAL.md](HOLDOUT_K_FINAL.md) — `k = 3`, 360/480 | ✅ **XONG** (7A.3) |
| ☑ | **Protocol đã freeze** | `HOLDOUT_PROTOCOL §2` (làm rõ *"một lượt"*) · `§5` (ngân sách) | ✅ **XONG** (7A.3) |
| ☑ | **Metric đã freeze** | `PHASE7_METRIC_CONTRACT §6` · `test_expectation_contract_7a2.py` | ✅ **XONG** (7A.2) |
| ☐ | **Pool đủ bài** | `seal_geometry_holdout.py --seed 0 --chi-kiem-pool` → exit 0 (canh **cả hai** ngưỡng: ≥1 mỗi ô **và** ≥40 tổng) | ⛔ **0/40 bài · 0/20 ô** |
| ☐ | **Nợ đối chiếu đã trả** | `kiem_pool` không còn báo `can_kiem_tay` *(người mở url đọc)* | ⚙️ **chưa kiểm tới** — cổng dừng ở coverage trước |
| ☐ | **Expectation đủ** | `pytest tests/geometry/test_holdout_readiness_7b.py -q` — hai cổng `skip` phải TỰ BẬT | ⛔ chưa có `holdout.json` |
| ☐ | **Ngân sách được duyệt** | 360 logic / 480 HTTP *(người)* | ⛔ chờ |
| ☐ | **Seed GVHD** | một số nguyên, **không** do người đo chọn *(người)* | ⛔ chờ |
| — | ~~Runtime identity PASS~~ | **chuyển xuống §B** — xem ghi chú dưới | ⚙️ |
| ☐ | **Cây sạch + hệ đúng bản** | `git status --porcelain` rỗng · `freeze_evaluation_candidate.py --verify` PASS | ✅ đang PASS, **kiểm lại ngay trước ④** |
| ☐ | **Cache sạch** | lượt đo gọi `run_pipeline` thẳng, **không qua HTTP** ⇒ không có cache để dính. Kiểm: runner không import `main.py` | ✅ theo thiết kế bộ đo |

> ⚠️ **Thứ tự bắt buộc**: dọn runtime **TRƯỚC** khi niêm phong. Con dấu ghi
> `measured_system_hash`; chạm `backend/app` sau khi niêm phong là **hỏng con
> dấu**, và lối thoát duy nhất là niêm phong lại — tức khai ra đây là lượt khác,
> trên một hệ khác.
>
> ⚠️ **`runtime_doctor` KHÔNG phải ô tick một lần.** Nó so **git SHA**, nên
> *mọi* commit — kể cả commit chỉ sửa tài liệu — làm image cũ đi và nó FAIL lại.
> Đó là hành vi đúng. Vì thế nó nằm ở **§B, bước áp chót**, sau commit cuối
> cùng và ngay trước `seal`. Đặt nó ở PRECONDITION là tự tạo một cổng luôn đỏ.

---

## B. EXECUTION — theo thứ tự, không đảo

| | Bước | Lệnh / cổng |
|---|---|---|
| ☐ | **Dọn runtime** | `GIT_SHA=$(git rev-parse HEAD) BUILD_TIME=$(date -u +%FT%TZ) docker compose up -d --build --force-recreate backend` |
| ☐ | **Xác nhận danh tính** | `runtime_doctor.py` → exit 0 · `freeze_evaluation_candidate.py --verify` → PASS |
| ☐ | **Rút seed** | `seal_geometry_holdout.py --seed <SỐ CỦA GVHD>` — **một bài mỗi ô**, ô thiếu ⇒ dừng, KHÔNG rút bù |
| ☐ | **Niêm phong + COMMIT** | `HOLDOUT_SEAL.json` + `cases.json` vào lịch sử **trước** khi chạy. Không có con dấu trong lịch sử = không chứng minh được tập không bị sửa |
| ☐ | **Chạy `k=3` lượt** | `ALLOW_LIVE_AI=1 … run_geometry_dev_evaluation.py --holdout` — runner đối chiếu **cả hai băm** trước call đầu tiên |

### Nạp dữ liệu — MỘT lệnh, chạy trước mọi bước ở bảng trên

```bash
cd backend
python scripts/make_human_copy_packet.py --ghi                # sinh gói (một lần)
python scripts/validate_human_copy_packet.py <gói>.txt        # soi giữa chừng
python scripts/run_phase7b_data_pipeline.py <gói>.txt         # soi cả tuyến
python scripts/run_phase7b_data_pipeline.py <gói>.txt --ghi   # ghi thật
```

Tuyến: `soi gói → ingest → pool → scaffold → freeze check → coverage →
ngưỡng ≥40 → readiness`, rồi báo đang ở mốc M mấy. Hỏng
thì dừng ở chặng đầu tiên và in `FAILED_STAGE` · `REASON` · `FIX_REQUIRED`.

⚠️ `seal` **không** nằm trong chuỗi, có chủ đích: nó tiêu seed của GVHD và chỉ
chạy được một lần.
| ☐ | **Lưu artifact từng lượt** | `case_id/run_00k/` — bộ đo **từ chối ghi đè** thư mục đã có bản ghi |
| ☐ | **Không sửa code** | `freeze --verify` phải vẫn PASS **sau** khi chạy xong. Lệch = lượt đo không còn là held-out |

**Trong lúc chạy, gặp lỗi thì CHỈ ghi `FAILURE_LOG.md`** (`case · run · symptom ·
classification · evidence`). Không sửa prompt, không bump cache, không chạy lại
để cải thiện điểm, không loại bài khó.

⚠️ **Lỗi hạ tầng (mạng, quota, timeout) KHÔNG thuộc taxonomy 4 nhóm.** Ghi riêng
trong `FAILURE_LOG.md`; nhét nó vào `model generation` là kết tội mô hình một sự
cố đường truyền.

⚠️ **Phiên bị đứt giữa chừng**: tiếp được, nhưng phải khai phiên bị chia và
chứng minh `measured_system_hash` không đổi giữa hai nửa.

---

## C. REPORT — bảy mục, KHÔNG gộp

| | Chỉ số | Đơn vị | Luật riêng |
|---|---|---|---|
| ☐ | ① `served` | `x/3` mỗi bài | không báo một mình — luôn kèm ③ |
| ☐ | ② `oracle` | `x/3` | **ba** trạng thái; `None` ≠ `False` |
| ☐ | ③a `construction_match` | `x/k'` | `k'` = số lượt **chấm được**; `None` = không áp dụng |
| ☐ | ③b `verification_match` | `x/3` | so **bằng đúng**; khai thừa cũng là lệch |
| ☐ | ④ `construction_validity` | 4 số rời | `literal_substitution` · `dependency_construction` · `witness_derived` · `max_depth` — **không gộp** |
| ☐ | ⑤ `stability` | `x/3` + **phân bố** | không chỉ trung bình; nêu cả phân bố `so_nghia_vu` |
| ☐ | Taxonomy lỗi | 4 nhóm ĐÓNG | `model generation` · `contract` · `validator` · `routing` |

**Nhóm `contract` và `validator` CHỈ ghi khi CHỨNG MINH ĐƯỢC**: chạy lại chính
IR đã lưu sau khi sửa, không sửa một ký tự nào của chương trình. Qua ⇒ lỗi thuộc
hệ. Không qua ⇒ thuộc mô hình. Ghi lỗi validator vào nhóm 1 là báo số thấp hơn
thực tế **và** kết tội mô hình ở đúng chỗ nó làm đúng — đã xảy ra một lần
(Phase 6.7, 2/15 lượt).

### Ba điều báo cáo cuối KHÔNG được viết

- ❌ *"AI hiểu hình học"* → ✅ **"Hệ chuyển ngôn ngữ tự nhiên thành chương trình
  hình học thực thi được với tỉ lệ …"**
- ❌ Số held-out đặt chung bảng với số của bốn vòng DEV mà không nhắc **hai
  thước khác nhau** (`obligation_match` cũ ≠ ③a+③b mới — `METRIC_CONTRACT §7`).
- ❌ Suy tỉ lệ khi mẫu `< 20`. Tầng A có **14** bài; `x/k` đọc là **đếm thô**.

### Phải khai kèm, không được im

- Tập **không phải blind thật**: người soạn pool đã đọc mọi đề. Bảo đảm thật là
  *"không viết ra đề và không sửa được đáp án"*.
- `k=3` mua phương sai **giữa các lượt**, **không** mua phương sai giữa các bài
  trong cùng một ô. `2/3` là *"bài ấy đạt 2/3 lượt"*, **không** phải *"ô A11 đạt
  67%"*.
- Tập đại diện **chủ đề**, không đại diện **tần suất** đề thi.
- Họ `proof_verification` **không có ô tầng A** ⇒ không tách được *"chứng minh
  được quan hệ"* khỏi *"nhận ra quan hệ"* (`COVERAGE_MATRIX §4`).

---

## D. SAU KHI CHẠY

| | Việc |
|---|---|
| ☐ | **DỪNG.** Không sửa hệ, không chạy lại |
| ☐ | Commit artifact **kể cả lượt thất bại** — không sửa artifact lượt cũ |
| ☐ | `freeze --verify` PASS lần cuối, ghi vào báo cáo |
| ☐ | Sinh `PHASE7B_RESULT.md`: environment · dataset · bảng từng bài · aggregate · failure analysis · limitations · so với DEV baseline |
| ☐ | Mọi kết luận truy ngược được: `problem_text → LLM output → semantic program → execution → simulation → metric` |

Sửa hệ **chỉ** sau khi benchmark kết thúc và kết quả đã commit.
