# DANH SÁCH ỨNG VIÊN ĐÃ SOI — vùng trang 80–83

> Soi bằng cách **dựng ảnh trang PDF rồi đọc**. Bảng này là **kết quả sàng**,
> **không** phải đề để chép: `CANDIDATE_REVIEW` chỉ ghi **tóm tắt dữ kiện** đủ
> để quyết định nhận/loại. Đề **nguyên văn** phải do người mở nguồn gõ lại —
> `HOLDOUT_SOURCE_POLICY §4`.
>
> Nguồn: *Tài liệu chuyên đề khối đa diện và thể tích khối đa diện* (443 trang) ·
> [toanmath](https://toanmath.com/2023/07/tai-lieu-chuyen-de-khoi-da-dien-va-the-tich-khoi-da-dien.html)

---

## 1. Ứng viên ĐẠT — 2/8

### ⭐ `cand_A14_01` — trang 80, Câu 1 · **khuyến nghị cho M1**

| | |
|---|---|
| Ô dự kiến | **A14** · `rational_volume` · `exact_fraction` |
| Dữ kiện | `ABC` vuông tại `A` · `AB = a` · `AC = 2a` · `SA ⊥ đáy` · `SA = 2a` |
| Lời giải nguồn | `S_ABC = AB·AC/2 = a²` ⇒ `V = (1/3)·a²·2a = 2a³/3` |
| **`ĐÁP ÁN`** | **`2/3`** *(gán `a = 1`)* |
| Toạ độ hữu tỉ | `A(0,0,0)` `B(1,0,0)` `C(0,2,0)` `S(0,0,2)` ✅ |
| **Lý do phù hợp** | dữ kiện toàn bội nguyên của `a`; không góc đặc biệt; **đề ngắn**; lời giải **cùng trang** |
| **Rủi ro** | **thấp nhất trong bảng** — không có bước trung gian nào sinh căn |

### `cand_A14_02` — trang 82, Câu 7

| | |
|---|---|
| Ô dự kiến | **A14** · `rational_volume` · `exact_fraction` |
| Dữ kiện | đáy hình chữ nhật · `SA ⊥ (ABCD)` · `AB = 3a` · `AD = 2a` · `SB = 5a` |
| Suy ra | `SA = √(SB²−AB²) = √(25−9)·a = 4a` — **hữu tỉ** *(bộ ba 3-4-5)* |
| **`ĐÁP ÁN`** | **`8/3`** — `V = (1/3)·(3a·2a)·4a = 8a³/3` |
| Toạ độ hữu tỉ | `A(0,0,0)` `B(3,0,0)` `D(0,2,0)` `S(0,0,4)` ✅ |
| **Lý do phù hợp** | đi qua Pythagoras mà **vẫn hữu tỉ** — kiểm được nhánh dựng sâu hơn `cand_01` |
| **Rủi ro** | trung bình — `SA` là **suy ra**, không cho sẵn; người chép phải xác nhận lời giải nguồn ra `8a³/3` chứ không tự tính |

---

## 2. Ứng viên LOẠI — 6/8, kèm lý do

| id | Trang · Câu | Dữ kiện | Loại vì |
|---|---|---|---|
| `rej_01` | tr 80 · Câu 2 | vuông **cân** tại `A`, `SA = BC = a` | **§2.2c** — đáp án `a³/12` **hữu tỉ**, nhưng `AB : BC = 1 : √2` ⇒ toạ độ vô tỉ |
| `rej_02` | tr 81 · Câu 3 | `AB`, `AC`, `SB` hữu tỉ | **§2.2b** — `BC = √(AC²−AB²) = a√2` ⇒ `V = a³√2/3` |
| `rej_03` | tr 81 · Câu 4 | `SA = 2√3a`, đáy đều cạnh `a` | căn ở dữ kiện **và** tam giác đều |
| `rej_04` | tr 82 · Câu 6 | `SA = a√3`, `AC = a√2` | căn ở dữ kiện ⇒ `V = a³√3/3` |
| `rej_05` | tr 83 · Câu 8 | `SA = a√3` | căn ở dữ kiện ⇒ `V = a³√3/6` |
| `rej_06` | tr 83 · Câu 9 | hình thoi, `∠BAD = 60°`, `SA = a√6/2` | căn **và** góc `60°` ⇒ đường chéo `a√3` |

**Tỉ lệ đạt: 2/8 = 25%** — khớp mức `≈ 2/11` đo ở lượt trước.

> `rej_01` là ca đáng nhớ nhất: **dữ kiện sạch, đáp án sạch, vẫn ngoài phủ**.
> Nó là lý do luật sàng đủ phải là *"đặt được vào toạ độ hữu tỉ không?"* chứ
> không phải *"đáp án có căn không?"*.

---

## 3. Trạng thái theo ô — kế hoạch 40 bài

| Ô | Cần | Nguồn tốt nhất | Trạng thái |
|---|--:|---|---|
| **A14** | 10 | *Khối đa diện & thể tích* tr 80–94 (76tr tự luận kèm lời giải) | **available** · 2 ứng viên đã soi · `needs_human_copy` |
| **A09 · A10** | 8 | *Quan hệ vuông góc — Lê Minh Tâm* (117tr, **0 trắc nghiệm**) | **available** · chưa soi · `needs_human_copy` |
| **A01–A08 · A13** | 16 | *Quan hệ song song Toán 11* (32tr, **0 trắc nghiệm**) + `.docx` thuvienhoclieu (74 bài) | **available** · chưa soi · `needs_human_copy` |
| **A11 · A12** | 4 | — | ⛔ **blocked** — chờ quyết định ①/② về `distance` vô tỉ |
| **B01–B06** | 6 | bất kỳ | **available** — không cần đáp án, chỉ cần đúng loại |

**Ước lượng công**: tỉ lệ đạt 25% ⇒ soi ~160 bài cho 40 ô. Vùng tr 80–94 có
2–3 bài/trang kèm lời giải ⇒ **≈ 60 trang**. Luật sàng loại phần lớn bằng liếc
mắt (thấy `√` ⇒ bỏ), nên phần lớn thời gian là **gõ lại 40 đề**, không phải tìm.

---

## 4. Việc còn lại

Chọn **`cand_A14_01`** (trang 80, Câu 1) cho M1 — đề ngắn nhất, rủi ro thấp
nhất, lời giải cùng trang.

1. Mở nguồn → trang 80 → đọc Câu 1.
2. Gõ nguyên văn vào `batch_001.txt` *(khuôn sẵn ở `batch_001.candidates.txt`)*.
3. Ký `NGƯỜI CHÉP:`.
4. `python scripts/run_m1_pipeline.py …/batch_001.txt --ghi`

⚠️ **Không chép đề từ bảng này** — nó chỉ có **tóm tắt dữ kiện**, không phải
nguyên văn, và chính nó là thứ giao thức cấm dùng làm nguồn.
