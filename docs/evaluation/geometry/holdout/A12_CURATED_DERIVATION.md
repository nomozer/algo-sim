# A12_CURATED_DERIVATION — bài duy nhất KHÔNG phải held-out, và vì sao

**Ngày**: 2026-08-29 · **Case**: `hp_a12_001` · **Ô**: A12 (khoảng cách từ
điểm đến đường thẳng) · **Chế độ**: `SOẠN-NỘI-BỘ` → `internal_author`.

---

## 1. Vì sao ô A12 không lấp được bằng nguồn công khai

Ba lượt quét, **673 url**, 9 tài liệu chuyên đề đã tải về và soi tận trang.
Ô A12 đòi đồng thời hai điều kiện mà đề Việt Nam hiếm khi thoả cùng lúc:
khoảng cách **điểm → ĐƯỜNG THẲNG** (không phải điểm → mặt phẳng, vốn phổ
biến hơn nhiều), và đáp án **hữu tỉ** (đa số bài dạng này ra `a√k`).

Hai ứng viên gần nhất đều rớt, và rớt vì hai lý do khác nhau — đáng ghi lại
vì chúng là hai lớp lỗi khác nhau:

| Ứng viên | Chuyện gì xảy ra | Phán quyết |
|---|---|---|
| VietJack — `SH² = 9a² + 4a²` | Lời giải **in trong nguồn** dùng `AH = 2a`, làm rơi hệ số ½, ra `a√13`. Số học của ta ra `5a` và **đúng**. | **REJECTED** — giao thức đòi *đáp án CỦA NGUỒN*, không đòi *đáp án đúng*. Kiểm phép tính KHÔNG thay được kiểm nguồn. |
| SGK Cánh Diều | Đáp án là ký hiệu `b`, không phải số. | `REJECT_SYMBOLIC_ORACLE` — xác nhận lại bằng `check_capability_boundary` và một ca đã bị loại sẵn trong pool. |

`HOLDOUT_PROTOCOL §5③` **cấm rút bù từ ô khác** — rút bù là lặng lẽ đổi tập
đo thành tập dễ hơn. Nên chỉ còn hai lối: chấp nhận phủ 19/20, hoặc lấp bằng
một bài tự soạn **mang đúng tên của nó**.

## 2. Luật bị nới là luật của ai

Đã soát toàn bộ `docs/`. Cả hai luật đang chặn đều nằm trong tài liệu **do
chính dự án viết**:

| Luật | Ở đâu | Nguồn |
|---|---|---|
| "đề phải từ nguồn công khai" | `HOLDOUT_PROTOCOL §1`, `§5①` | tài liệu của dự án |
| "seed do GVHD cấp" | `HOLDOUT_PROTOCOL §5②`, `PHASE7B_PREFLIGHT` | tài liệu của dự án |

**Không có chỉ thị nào từ bên ngoài** áp đặt hai luật này lên tuyến hình học.
(Có một tiền lệ GVHD **đã** cấp seed `23082026` — nhưng cho benchmark ngữ
nghĩa, không phải cho held-out hình học.)

Vậy đây là **lựa chọn nội bộ**, nới được. Nhưng nới thì phải khai cái mất:

> `§1` nói điểm mạnh KHÔNG nằm ở chỗ *"tôi chưa nhìn"* mà ở chỗ **tôi không
> viết được ra đề, và không sửa được đáp án**.

Bài dưới đây mất đúng bảo đảm ấy. Nó **không** phải held-out.

## 3. Đề

> Cho hình chóp `S.ABCD` có đáy `ABCD` là hình vuông cạnh `3a`, cạnh bên `SA`
> vuông góc với mặt phẳng đáy và `SA = 4a`. Tính khoảng cách từ điểm `A` đến
> đường thẳng `SB`.

Chuẩn hoá `a = 1`. Đáp án: **`12/5`**.

## 4. Ba suy dẫn tất định, độc lập nhau

Cả ba dùng `Fraction` chính xác — không dấu phẩy động, không epsilon.

**① Hệ thức lượng trong tam giác vuông.** `SA ⊥ (ABCD)` ⇒ `SA ⊥ AB`, nên
`△SAB` vuông tại `A` với `SA = 4`, `AB = 3` ⇒ `SB = 5` (hữu tỉ). Khoảng cách
từ `A` đến `SB` là đường cao hạ từ đỉnh góc vuông:

```
d = SA·AB/SB = (4·3)/5 = 12/5
```

**② Tích có hướng, tính tay.** Đặt `A(0,0,0)`, `B(3,0,0)`, `S(0,0,4)`.
Phương của `SB`: `u = B − S = (3,0,−4)`, `|u|² = 25`. Vectơ `w = S − A =
(0,0,4)`.

```
w × u = (0·(−4) − 4·0,  4·3 − 0·(−4),  0·0 − 0·3) = (0, 12, 0)
d² = |w × u|² / |u|² = 144/25   ⇒   d = 12/5
```

Độc lập với ①: không dùng hệ thức lượng nào, chỉ đại số vectơ.

**③ Oracle custodian.** `docs/evaluation/geometry/custodian/geometry_oracle.py`
— bản cài **độc lập với kernel**, thuộc **bộ đo** chứ không phải hệ được đo.
Ghép từ các primitive `Fraction` của nó (`V`, `sub`, `cross`, `dot`):

```
dot(cross(w,u), cross(w,u)) / dot(u,u) = 144/25   ✓ khớp ① và ②
```

> ⚠️ **KHÔNG** dùng `backend/app/simulation/geometry/`. Đó là **hệ đang được
> đo** (`MEASURED_SYSTEM_PATHS`), và dùng nó để soạn đáp án là tự chấm bài
> mình. `measured_output_used_for_source_verification` của bài này vẫn là
> `false`, và đó là lời khai đúng.

Ba suy dẫn đồng thuận: **`d = 12/5`**, hữu tỉ ⇒ trong ranh giới kernel.

## 5. Bài này mang những dấu hiệu gì

| Trường | Giá trị | Vì sao |
|---|---|---|
| `curated_preseal` | `true` | cờ máy tra được, không phải ghi chú văn xuôi |
| `verification_mode` | `SOẠN-NỘI-BỘ` | không phải `NGƯỜI`, không phải `MÁY-TỪ-NGUỒN` |
| `internal_author` | có | và **không** có `human_verifier`/`machine_verifier` |
| `nguon.loai` | `soan_noi_bo` | không đội lốt `web`/`sach_in` |
| `han_che` | có | tự khai mất bảo đảm gì |
| `suy_dan` | 3 mục | `kiem_pool` đòi ≥ 2 cách **độc lập** |

`kiem_pool` đặt **trần ĐÚNG MỘT** bài `curated_preseal` trong toàn pool.
Ngoại lệ không có trần thì nó không còn là ngoại lệ: lối rẻ nhất để "phủ đủ
20/20 ô" sẽ là tự soạn nốt phần khó, và tập held-out biến thành tập tự viết
mà vẫn mang tên held-out.

## 6. Luật báo cáo — bắt buộc

Mọi số đo của Phase 7B phải được nêu **hai lần**:

- **20/20 ô** (có A12) — con số đầy đủ về độ phủ chương trình;
- **19/20 ô** (bỏ A12) — **con số held-out thật**, vì 19 ô kia đến từ nguồn
  công khai có trích dẫn với đáp án của nguồn.

Câu được phép viết: *"42 bài, phủ 20/20 ô, trong đó 1 bài (ô A12) là bài soạn
nội bộ vì không tìm được nguồn công khai thoả điều kiện — số held-out thật là
41 bài / 19 ô."*

Câu **KHÔNG** được phép viết: *"42 bài held-out"*, *"phủ đủ 20/20 ô từ nguồn
công khai"*.
