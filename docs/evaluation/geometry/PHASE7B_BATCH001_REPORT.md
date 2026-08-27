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

### 4c. Bảng sàng có EVIDENCE — vùng trang 80–81 (đề kèm lời giải)

| `case_id` dự kiến | Vị trí | Kết quả | Lý do | Evidence |
|---|---|---|---|---|
| — | tr 80 · Câu 1 | ✅ **PASS** | dữ kiện hữu tỉ, đáp án phân số | `AB = a`, `AC = 2a`, `SA = 2a` → **`V = 2a³/3`** |
| — | tr 80 · Câu 2 | ✅ **PASS** | dữ kiện toàn `a` | `SA ⊥ (ABC)`, `△ABC` vuông cân tại `A`, `SA = BC = a` |
| `cand_tr81_c3` | tr 81 · Câu 3 | ⛔ REJECT | **đáp án vô tỉ** dù dữ kiện sạch | `BC = √(AC²−AB²) = a√2` ⇒ **`V = a³√2/3`** |
| `cand_tr81_c4` | tr 81 · Câu 4 | ⛔ REJECT | căn ở dữ kiện | `SA = 2√3a`, đáy đều cạnh `a` |
| `cand_tr46_c3` | tr 46 · Câu 3 | ⛔ REJECT | căn ở dữ kiện | `AC = a√3`, `SB = a√5` |
| `cand_tr46_c4` | tr 46 · Câu 4 | ⛔ REJECT | căn ở dữ kiện | `SA = 2√3a` |
| `cand_tr46_c5` | tr 46 · Câu 5 | ⛔ REJECT | góc sinh vô tỉ | `∠BAC = 120°` ⇒ đỉnh ở `(−a, a√3, 0)` |
| `cand_tr46_c6` | tr 46 · Câu 6 | ⛔ REJECT | căn ở dữ kiện | `SA = a√3`, `AC = a√2` |
| `cand_tr46_c7` | tr 46 · Câu 7 | ⚠️ **hoãn** | dữ kiện hữu tỉ (`3a, 2a, 5a`) nhưng **lời giải không kề bên** | trang 45–47 là danh sách đề, không có `Lời giải` |
| `cand_tr46_c8..11` | tr 46 | ⛔ REJECT | căn / tối ưu tham số | `SA = a√3` · `a√6/2` · `a√2` · `x²+y²=a²` tìm GTLN |

**Không bài nào trong bảng này vào `pool.json`** — chúng là ghi chép sàng
nguồn, không phải case. Bài `PASS` chỉ thành case khi **người** chép và ký.

### ⚠️ SỬA LUẬT SÀNG CỦA CHÍNH TÔI — nhìn **ĐÁP ÁN**, đừng chỉ nhìn dữ kiện

Bản trước tôi đưa ba luật dựa trên **dữ kiện**: bỏ khi thấy `√`, bỏ khi thấy
góc `30°/60°/120°`. **Ba luật ấy CHƯA ĐỦ**, và trang 81 cho phản ví dụ:

> **Câu 3** — dữ kiện `AB = a`, `AC`, `SB` đều **hữu tỉ**, không một dấu căn.
> Lời giải: `SA = √(SB²−AB²) = 2a` (hữu tỉ), nhưng
> `BC = √(AC²−AB²) = a√2` ⇒ `V = a³√2/3` — **VÔ TỈ**.

Dữ kiện sạch, **đáp án vẫn vô tỉ**: căn sinh ra từ **định lí Pythagoras**
trong lúc giải, không có mặt trong đề. Một tam giác vuông có cạnh `a` và
`a√2` thì **không đặt được cả ba đỉnh vào toạ độ hữu tỉ** — ngoài ranh giới.

> **LUẬT SÀNG ĐÚNG, theo thứ tự:**
> 1. **Nhìn ĐÁP ÁN trước.** Có `√` ⇒ **bỏ ngay.** Đây là phép kiểm chắc chắn
>    nhất, và ở vùng trang 80+ thì lời giải nằm ngay dưới đề nên **không tốn
>    thêm công**.
> 2. Đáp án sạch rồi mới xét dữ kiện: có `√` hoặc góc `30°/60°/120°` ⇒ bỏ.
> 3. Giữ: đáp án là **phân số của `a³`** (`2a³/3`, `a³/6`…), dữ kiện là **bội
>    nguyên của `a`**.
>
> Luật 1 làm được luật 2 gần như thừa — nhưng giữ cả hai vì luật 2 bắt được
> bài mà lời giải bị cắt trang.

⚠️ Đây là **lớp thứ ba** của rào vô tỉ, khác hai lớp đã ghi ở
`CAPABILITY_BOUNDARY §2.1` (đáp án `distance` vô tỉ) và `§2.2` (tỉ số dữ kiện
vô tỉ): **dữ kiện hữu tỉ mà HÌNH buộc toạ độ vô tỉ**. Pha này cấm sửa
`CAPABILITY_BOUNDARY`, nên ghi ở đây như một **đề nghị bổ sung `§2.2b`** cho
lượt nào được phép sửa tài liệu ấy.

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
