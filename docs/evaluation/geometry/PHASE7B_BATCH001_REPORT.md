# PHASE 7B — BÁO CÁO BATCH 001

> **0 API call. Không ghi `pool.json`. Không sinh đề. Không tự ký `NGƯỜI CHÉP`.**
> `freeze --verify` PASS trên cùng băm `7ab25683…` của Phase 7A.2.

```
READY_FOR_NEXT_STEP:  NO
```

---

## 1. Số bài nhập

**0.** `batch_001.txt` vẫn là **khung chưa điền**.

```
python scripts/ingest_holdout_batch.py ../docs/evaluation/geometry/holdout/batch_001.txt
→ exit 2 · 11 lỗi · "NGƯỜI CHÉP: <tên bạn> … vẫn là CHỖ TRỐNG chưa điền"
```

Điều kiện nhận bài của pha này gồm **`✓ người đọc trực tiếp PDF/sách`**, và
ràng buộc gồm **`không tự điền NGƯỜI CHÉP`**. Hai câu ấy khoá cùng một chỗ:
bước xác minh **là** hành vi đọc của một người, và tôi không thay được.

## 2. Accepted / Rejected

| | |
|---|---|
| ACCEPTED | **0** |
| REJECTED | **0** *(không có bài nào được nhập để mà loại)* |

Ba bài đã có trong pool từ các pha trước, **không** thuộc batch này:

| id | reason | capability_boundary | oracle_issue | source_issue |
|---|---|---|---|---|
| `hp_a11_001` | `rejected_capability_boundary` | ⛔ `d = 3√6` vô tỉ ⇒ `GEOMETRY_IRRATIONAL_RESULT` | không biểu diễn được | — |
| `hp_a14_cand_001` | `rejected_capability_boundary` | ⛔ tham số ký hiệu `a, b, c`, không có tầng đại số | đáp án là **công thức** | — |
| `hp_a14_cand_002` | `needs_manual_review` | ✅ PASS (`V = 4` hữu tỉ) | ✅ PASS | ⛔ **trắc nghiệm 4 phương án** |

## 3. Coverage hiện tại

```
A01 0   A02 0   A03 0   A04 0   A05 0   A06 0   A07 0
A08 0   A09 0   A10 0   A11 0   A12 0   A13 0   A14 0
B01 0   B02 0   B03 0   B04 0   B05 0   B06 0
```

**20/20 ô còn thiếu.**

---

## 4. Lý do loại — và con số mới đo được ở lượt này

### 4a. Trích PDF làm mất phân biệt `2a` với `a√2`

Đối chiếu ảnh trang gốc với bản trích (`HOLDOUT_ACQUISITION_LOG §1f`):

```
gốc     AC = a√3        AC = 2a
trích   "3 AC a ="      "2 AC a ="
```

Hai thứ ra **cùng một dạng**. Đây là rào **nhận nhầm bài**, khác bốn rào trước
(đều là **mất bài**) — và `a√3` ngoài ranh giới còn `2a` thì trong.

### 4b. ⚠️ MỚI — tỉ lệ bài đủ tư cách trong nguồn A14 chỉ khoảng **2/11**

Đọc trang 46 của *Khối đa diện & thể tích* (11 bài liên tiếp):

| Bài | Dữ kiện | |
|---|---|:-:|
| Câu 2 | `SA = BC = a` | ✅ |
| Câu 3 | `AC = a√3`, `SB = a√5` | ⛔ căn |
| Câu 4 | `SA = 2√3a` | ⛔ căn |
| Câu 5 | `AC = 2a`, `∠BAC = 120°` | ⛔ góc 120° ⇒ toạ độ vô tỉ |
| Câu 6 | `SA = a√3`, `AC = a√2` | ⛔ căn |
| **Câu 7** | **`AB = 3a`, `AD = 2a`, `SB = 5a`** | ✅ |
| Câu 8 | `SA = a√3` | ⛔ căn |
| Câu 9 | `SA = a√6/2`, góc `60°` | ⛔ căn |
| Câu 10 | `SA = a√2` | ⛔ căn |
| Câu 11 | `SA = y`, `AM = x`, tìm GTLN | ⛔ tối ưu tham số |
| L2·Câu 1 | cạnh `2a`, góc `SC–(ABCD)` = `60°` | ⛔ `tan 60° = √3` |

**2 đạt / 11.** Muốn 3 bài A14 thì phải soi **≈ 17 bài**.

> **Ba luật bỏ nhanh** — rút từ chính bảng trên:
> - thấy **`√`** ở dữ kiện ⇒ **bỏ**
> - thấy góc **30° · 60° · 120°** ⇒ **bỏ** (`tan`/`cos` sinh `√3`)
> - giữ được: cạnh là **bội nguyên của `a`**, góc **vuông** hoặc **45°**
>
> Ba luật này là thứ tiết kiệm nhiều thời gian nhất khi chép — chúng loại được
> ~80% bài chỉ bằng liếc mắt.

---

## 5. ⚠️ SỬA KHUYẾN NGHỊ CỦA CHÍNH BÁO CÁO NÀY — **trang 80, không phải trang 46**

Bản trước chỉ vào **trang 46**. Đó là chỗ sai, và lý do đáng ghi:

Tài liệu là **hợp tuyển** — đánh số trang trong lặp lại nhiều lần (`Page 20`
rồi lại `Page 2`). Trang 45–47 là **danh sách đề không kèm lời giải**; lời giải
của chúng không nằm kề bên và không tra ra bằng phép cộng trừ số trang.

Mà `TASK 2` cấm *"tự suy luận đáp án nếu nguồn không có"*. Nên chép Câu 2 / Câu 7
ở trang 46 thì **kẹt ở dòng `ĐÁP ÁN:`**.

### Đo lại toàn tài liệu — chỗ đúng ở đâu

| | Số trang |
|---|--:|
| tự luận **CÓ lời giải kề bên** | **76** — bắt đầu **trang 80** |
| tự luận, **không** lời giải | 21 |
| trắc nghiệm + lời giải | 234 |

Kiểm bằng mắt trang 80 — đúng thứ cần:

> **Câu 1** *(nửa trên)* — `AB = a`, `AC = 2a`, `SA = 2a` → **Lời giải** →
> `V = 2a³/3`
> **Câu 2** — *"Cho hình chóp S.ABC có SA ⊥ (ABC), △ABC vuông cân tại A,
> SA = BC = a. Tính theo a thể tích V"* → **Lời giải** kề ngay dưới

Dữ kiện **hữu tỉ hoàn toàn**, đáp án là **phân số của `a³`**, và lời giải nằm
**cùng trang**. Ba điều kiện khó nhất thoả cùng lúc.

### Thứ tự nên lấp

| Ưu tiên | Ô | Nguồn | Vị trí |
|---|---|---|---|
| 1 | **A14** ×3 | *Khối đa diện & thể tích* (443tr) | **trang 80–94** — 76 trang tự luận có lời giải kề bên |
| 2 | **A09 · A10** ×2 | *Quan hệ vuông góc — Lê Minh Tâm* (217tr) | 117 trang tự luận, **0 trắc nghiệm**; mẫu trang 5, 6, 17, 18 |
| 3 | A01–A08 | *Quan hệ song song — Toán 11* (75tr) | 32 trang tự luận, **0 trắc nghiệm** |

Cả ba nguồn: `SOURCE_CANDIDATE_REPORT.md`.

⚠️ **A09/A10 có bẫy đơn vị riêng**: cặp đường–đường và mặt–mặt khai `cos²`,
nhưng cặp **đường–mặt** khai **`sin²`**. Khai nhầm là chấm sai **im lặng**.

---

## 6. Việc còn lại — một bước, và nó là bước của người

1. Mở *Khối đa diện & thể tích* → **trang 80** (rồi 81, 82… — 76 trang liền).
2. Chọn bài có dữ kiện **bội nguyên của `a`**, tránh `√` và góc `30°/60°/120°`.
3. Chép đề **và** đáp án (nằm ngay dưới, mục *Lời giải*) vào
   `holdout/batch_001.txt`, giữ đủ `= ⊥ √ ∥`.
4. Đáp án dạng `2a³/3` → dòng `ĐÁP ÁN:` ghi **`2/3`** (gán `a = 1`). Phép gán ấy
   là chỗ **duy nhất** người soạn được phép tính, và `ingest` sẽ ghi nó vào
   `phep_chuyen` để người khác kiểm lại.
5. Điền `NGƯỜI CHÉP: <tên> · <ngày> · <tài liệu, trang>`.
6. `ingest_holdout_batch.py …` (soi) → `--ghi`.

Từ đó tới coverage là **một lệnh**. Hạ tầng đã chạy nối đầu-cuối và có test
tiêm lỗi ở bốn chặng.
