# KẾ HOẠCH MỞ RỘNG TẬP HELD-OUT — từ 0 tới 40 bài / 20 ô

> Gom những thứ đang nằm rải trong `HOLDOUT_ACQUISITION_LOG`,
> `SOURCE_CANDIDATE_REPORT` và `PHASE7B_BATCH001_REPORT` thành **một danh sách
> việc**. Không thêm phát hiện mới; chỉ xếp lại thành thứ thi hành được.
>
> **Chưa chạy Phase 7B.** Kế hoạch này kết thúc ở `accepted = 40`, không đi xa hơn.

---

## 0. Trạng thái xuất phát

```
accepted 0/40 · coverage 0/20 ô
pool có 3 bài: 2 rejected_capability_boundary · 1 needs_manual_review
```

Hạ tầng **đã xong và đã chứng minh chạy nối đầu-cuối**: `ingest` → `capability
boundary` → `oracle` → `coverage` → `seal`, có test tiêm lỗi ở bốn chặng. Cái
thiếu **duy nhất** là dữ liệu do người xác minh.

---

## 1. Thứ tự lấp — và vì sao đúng thứ tự này

Xếp theo **tỉ lệ loại thấp nhất trước**, không theo tầm quan trọng. Lý do: mỗi
bài `accepted` sớm là một lần chạy thật của cả dây, và dây chạy được sớm thì
lỗi lộ ra khi còn rẻ.

| # | Ô | Số bài | Nguồn | Vì sao thứ tự này |
|---|---|--:|---|---|
| 1 | **A14** thể tích | 2–3 | *Khối đa diện & thể tích* tr 80+ | **đề kèm lời giải cùng trang** — chỗ duy nhất tìm được có cả hai |
| 2 | **A09 · A10** góc | 4 | *Quan hệ vuông góc — Lê Minh Tâm* | `cos²`/`sin²` **luôn hữu tỉ** khi toạ độ hữu tỉ ⇒ không vướng rào vô tỉ ở đáp án |
| 3 | **A01–A08** quan hệ | 16 | *Quan hệ song song — Toán 11* (75tr, **0 trắc nghiệm**) + *Quan hệ vuông góc* | đáp án **true/false** ⇒ **không cần `phep_chuyen`**, không có đơn vị để nhầm |
| 4 | **A13** thiết diện | 2 | *Quan hệ song song* | cần khối **lồi**; đề thiết diện hay kèm hình vẽ ⇒ soi kỹ |
| 5 | **A11 · A12** khoảng cách | 4 | — | **khó nhất**, chờ quyết định ①/② (xem §3) |
| 6 | **B01–B06** ngoài phủ | 6+ | bất kỳ | **không cần đáp án** — chỉ cần đúng loại. Dễ nhất về dữ liệu |

**Mỗi ô cần ≥ 1 bài; tổng ≥ 40** ⇒ trung bình 2 bài/ô. Ô nào dễ tìm thì lấy
nhiều hơn, nhưng **không ô nào được để trống** — ô thiếu ⇒ `seal` dừng.

---

## 2. Luật sàng — thứ tự thao tác khi ngồi trước tài liệu

1. **Nhìn ĐÁP ÁN trước.** Có `√` ⇒ **bỏ ngay.**
   Đây là phép kiểm chắc chắn nhất: căn có thể sinh ra **trong lúc giải** từ
   dữ kiện hoàn toàn sạch (tr 81 · Câu 3: `AB, AC, SB` hữu tỉ → `V = a³√2/3`).
2. Đáp án sạch rồi mới xét **dữ kiện**: có `√`, hoặc góc `30°/60°/120°` ⇒ bỏ.
3. Bỏ tiếp: **trắc nghiệm** · **tham chiếu hình vẽ** không có trong văn bản ·
   **mặt cong** · **Oxyz cho sẵn toạ độ** · bài **tối ưu tham số**.
4. Giữ: đáp án là **phân số của `a³`** hoặc **true/false**, dữ kiện là **bội
   nguyên của `a`**, góc **vuông** hoặc **45°**.

**Tỉ lệ đạt đo được: ≈ 2/11.** Muốn 40 bài thì phải soi **≈ 220 bài** — nghe
nhiều, nhưng ở vùng trang 80+ mỗi trang có 2–3 bài kèm lời giải, nên là
**≈ 80–100 trang**, và luật 1 loại phần lớn chỉ bằng liếc mắt.

### Đơn vị `ĐÁP ÁN` theo ô — chép sai là chấm sai IM LẶNG

| Ô | Đơn vị | Bẫy |
|---|---|---|
| A14 | phân số (gán `a = 1`: `2a³/3` → `2/3`) | — |
| A09 (đường–đường) · A08 (mặt–mặt) | **`cos²`** | — |
| **A10** (đường–**mặt**) | **`sin²`** | ⚠️ **cùng tên trường `angle_cos_sq`** — khai `cos²` ở đây là sai mà không cổng nào báo |
| A11 · A12 | phân số, **phải hữu tỉ** | engine **ném** khi vô tỉ |
| A01–A08 · A13 | `true` / `false` | — |
| B01–B06 | **bỏ trống** | có đáp án ⇒ `kiem_pool` ĐỎ |

---

## 3. Hai quyết định phải chốt TRƯỚC khi lấp xong

| | Quyết định | Chặn ô nào | Cái giá |
|---|---|---|---|
| ① | **A11/A12**: chỉ nhận `distance` hữu tỉ, hay mở một ô tầng B cho lớp vô tỉ | A11 · A12 | mở ô ⇒ **N đổi khỏi 20** ⇒ ngân sách và `HOLDOUT_K_FINAL` chốt lại |
| ② | **Đề trắc nghiệm**: nhận nguyên văn / đổi nguồn sang tự luận | ảnh hưởng tốc độ mọi ô | viết lại đề ⇒ **CẤM** |

Cả hai **không chặn** việc bắt đầu: ô A14, A09, A10, A01–A08 lấp được ngay.
Nhưng ① phải xong **trước khi rút seed**, vì nó đổi số ô.

---

## 4. Mốc kiểm — chạy sau **mỗi lô**, không đợi tới cuối

```bash
python scripts/ingest_holdout_batch.py <lô>.txt          # soi
python scripts/ingest_holdout_batch.py <lô>.txt --ghi    # ghi
python scripts/seal_geometry_holdout.py --seed 0 --chi-kiem-pool
python scripts/holdout_coverage_matrix.py --md docs/evaluation/geometry/holdout/COVERAGE_MATRIX.md
python scripts/report_holdout_readiness.py --md
```

| Mốc | Điều kiện | Ý nghĩa |
|---|---|---|
| **M1** | 1 bài `accepted` | cả dây chạy thật lần đầu — **mốc quan trọng nhất**, không phải mốc 40 |
| M2 | 3 bài A14 | một ô đầy, ma trận đổi màu |
| M3 | 14 ô tầng A có bài | phần khó xong |
| M4 | 20/20 ô · ≥40 bài | `--chi-kiem-pool` thoát `0` |
| M5 | `expectations/holdout.json` đủ | soạn **sau** M4 |
| M6 | runtime dọn · seed GVHD · ngân sách duyệt | rồi mới `seal` |

⚠️ **M1 mới là mốc đáng ăn mừng.** Từ 0 → 1 chứng minh dây hoạt động trên dữ
liệu thật; từ 1 → 40 chỉ là lặp lại.

---

## 5. Việc KHÔNG thuộc kế hoạch này

- **Không** chạy Phase 7B, kể cả khi đủ 40 bài — còn seed và ngân sách.
- **Không** soạn `expectations` trước M4: soạn kỳ vọng cho bài chưa biết có
  nhận được không là làm hai lần.
- **Không** nới ranh giới năng lực để lấp ô. Ô không lấp được bằng đề hợp lệ
  thì đó là **kết quả**, không phải trở ngại — và phải khai khi báo số.
