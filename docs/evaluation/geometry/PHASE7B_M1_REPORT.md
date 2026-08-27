# PHASE 7B — BÁO CÁO MỐC M1

> **0 API call. Không chạy benchmark. Không sửa `backend/app`, prompt, DSL,
> kernel, renderer, metric, capability boundary.**

```
M1 (accepted ≥ 1):   CHƯA ĐẠT
accepted:            0
rejected:            0   (chưa nhập được bài nào để mà loại)
READY_FOR_PHASE7B:   NO
```

**Chặn ở đúng MỘT chỗ: chữ ký `NGƯỜI CHÉP`.** Mọi cổng khác đã qua — chứng
minh bên dưới.

> ### ⛔ Bản nháp đã bị LOẠI khỏi danh sách nguồn
>
> Phase 7B · TASK 1 ghi thẳng: *"Không dùng: `batch_001.draft.txt` · OCR
> output · text trích từ PDF · **nội dung AI đọc lại**"*.
>
> Bản nháp tôi soạn ở lượt trước thuộc mục cuối, nên nó **không** phải lối
> tắt: đề trong `batch_001.txt` phải do **người mở nguồn gốc, đọc trực tiếp,
> chép nguyên văn**. Bản nháp giữ lại chỉ để ghi nhận nó từng tồn tại và để
> lưu phần phân tích Câu 2; đã dán cảnh báo ở đầu file.
>
> Đây cũng là câu trả lời cho đề nghị tôi nêu ở lượt trước ("tôi có thể soạn
> nháp nếu bạn muốn"): **không**, và ranh giới ấy nay đã rõ.

---

## 1. Bài ứng viên — `Câu 1 trang 80`

| | |
|---|---|
| `case_id` (khi nạp) | `hp_a14_001` |
| Ô coverage | **A14** |
| `capability_tag` | `rational_volume` |
| `answer_shape` | `exact_fraction` |
| `oracle_ref` | `volume` |
| `oracle_result` | `{"volume": "2/3"}` |
| `expected_obligations` | `["volume"]` |
| Nguồn | *Tài liệu chuyên đề khối đa diện và thể tích khối đa diện* — **trang 80, Câu 1** |

**Đề** *(bản nháp máy đọc — chờ người đối chiếu)*:

> Cho hình chóp `S.ABC` có đáy `ABC` là tam giác vuông tại `A`, `AB = a`,
> `AC = 2a`. Cạnh bên `SA` vuông góc với đáy và `SA = 2a`. Tính thể tích `V`
> của khối chóp `S.ABC`.

**Đáp án**, theo lời giải in ngay dưới đề cùng trang:
`S_ABC = AB·AC/2 = a²` · `V = (1/3)·S_ABC·SA = 2a³/3` → gán `a = 1` ⇒ **`2/3`**.

**Toạ độ hữu tỉ hoá được**: `A(0,0,0)` · `B(1,0,0)` · `C(0,2,0)` · `S(0,0,2)`.

## 2. Trạng thái cổng — chạy thật trên bài này

```
phan_tich            : không lỗi
capability_boundary  : PASS
kiem_pool            : PASS
ingest (bản nháp)    : ⛔ 1 LỖI — "THIẾU dòng NGƯỜI CHÉP:"
```

Chỉ **một** lỗi, và nó là lỗi **cố ý không sửa được bằng máy**. Thêm chữ ký
thì cả dây qua sạch — đã mô phỏng để xác nhận, **không** ghi vào pool.

## 3. ⚠️ `Câu 2 trang 80` — ĐÃ SOI VÀ PHẢI LOẠI

Phase này chỉ định dùng cả Câu 1 và Câu 2. **Câu 2 không dùng được.**

> *"Cho hình chóp `S.ABC` có `SA ⊥ (ABC)`, `△ABC` vuông cân tại `A`,
> `SA = BC = a`. Tính theo `a` thể tích `V`."*

Đáp án `V = a³/12` — **hữu tỉ**. Dữ kiện `SA = BC = a` — **không một dấu căn**.
Vẫn ngoài ranh giới:

```
vuông cân tại A, cạnh huyền BC = a  ⇒  AB = AC = a/√2
tỉ số AB : BC = 1 : √2  →  VÔ TỈ
⇒ không hệ trục nào đặt được cả ba đỉnh vào toạ độ hữu tỉ
```

### Đây là LỚP THỨ TƯ của rào vô tỉ — và nó phá luật sàng của lượt trước

| | Lớp | Dữ kiện | Đáp án | Toạ độ |
|---|---|:-:|:-:|:-:|
| §2.1 | `distance` vô tỉ | hữu tỉ | **vô tỉ** | — |
| §2.2 | tỉ số dữ kiện vô tỉ | **vô tỉ** | — | vô tỉ |
| §2.2b | căn sinh khi giải | hữu tỉ | **vô tỉ** | vô tỉ |
| **MỚI** | **Câu 2** | hữu tỉ | **hữu tỉ** | **vô tỉ** |

Lượt trước tôi đưa luật *"nhìn ĐÁP ÁN trước"*. **Câu 2 phá luật ấy**: đáp án
sạch mà bài vẫn ngoài phủ.

> **LUẬT SÀNG ĐỦ — và là luật duy nhất đủ:**
> **"Đặt được cả hình vào toạ độ HỮU TỈ không?"**
>
> Kiểm nhanh — mọi **tỉ số độ dài suy ra được từ đề** có hữu tỉ không?
>
> | Hình | Tỉ số | |
> |---|---|:-:|
> | tam giác vuông cân | `1 : 1 : √2` | ⛔ |
> | tam giác đều (đường cao) | `a√3/2` | ⛔ |
> | góc `30°` · `60°` · `120°` | `tan`/`cos` sinh `√3` | ⛔ |
> | tam giác vuông, hai cạnh góc vuông **bội nguyên của `a`** | `1 : 2 : √5` nhưng **cạnh huyền không dùng tới** | ✅ |
>
> ⚠️ Ô cuối là chỗ tinh tế: Câu 1 có `BC = a√5` (cạnh huyền vô tỉ), **vẫn
> dùng được**, vì thể tích chỉ cần `AB`, `AC`, `SA` — cả ba hữu tỉ. Cái quyết
> định là **toạ độ đỉnh**, không phải mọi độ dài trong hình.

Pha này cấm sửa `capability_boundary`, nên ghi ở đây như **đề nghị bổ sung
`§2.2c`** cho lượt nào được phép sửa tài liệu ấy.

## 4. Coverage

```
A01 0  A02 0  A03 0  A04 0  A05 0  A06 0  A07 0
A08 0  A09 0  A10 0  A11 0  A12 0  A13 0  A14 0
B01 0  B02 0  B03 0  B04 0  B05 0  B06 0
```

## 5. Việc còn lại để đạt M1

1. Mở [tài liệu](https://toanmath.com/2023/07/tai-lieu-chuyen-de-khoi-da-dien-va-the-tich-khoi-da-dien.html)
   → **trang 80** → đọc **Câu 1** trên chính trang đó.
2. **Gõ lại nguyên văn** vào `holdout/batch_001.txt`, giữ đủ `= ⊥ √ ∥`.
   *(Không chép từ bản nháp — TASK 1 loại nó khỏi danh sách nguồn.)*
3. `NGUỒN:` — tên tài liệu + trang 80 + Câu 1.
4. `ĐÁP ÁN: 2/3` — lời giải in ngay dưới đề cho `V = 2a³/3`; gán `a = 1`.
5. `NGƯỜI CHÉP: <tên> · <ngày> · <tài liệu, trang>`.
6. `ingest_holdout_batch.py … ` (soi) → `--ghi`.

Khối cần điền, đúng khuôn:

```
NGƯỜI CHÉP: <tên bạn> · 2026-08-28 · Khối đa diện & thể tích, trang 80

[A14] <gõ nguyên văn Câu 1 từ trang 80>
      NGUỒN: Tài liệu chuyên đề khối đa diện và thể tích khối đa diện — trang 80, Câu 1
      ĐÁP ÁN: 2/3
```

Ba dòng còn lại (`NGUỒN`, `ĐÁP ÁN`) đã xác định chắc chắn; dòng duy nhất cần
bạn đọc nguồn để viết là **đề bài**.
