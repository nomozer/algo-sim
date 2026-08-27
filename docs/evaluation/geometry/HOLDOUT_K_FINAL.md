# `k` ĐÃ CHỐT — điều kiện lấy mẫu của lượt held-out

> Chốt **2026-08-27 (Phase 7A.3)**, tại `641ac5f`, **trước** khi tiêu call đầu
> tiên của benchmark và **trước** khi có seed.
>
> Phân tích ba phương án: [HOLDOUT_K_DECISION.md](HOLDOUT_K_DECISION.md). File
> này chỉ ghi **quyết định** và cái giá của nó.

---

## 1. Quyết định

```
k = 3   cho CẢ 20 Ô        (14 tầng A + 6 tầng B)
```

= **Option B**. Mỗi bài chạy **3 lượt độc lập** trong **cùng một phiên đã niêm
phong**:

- **không** sửa hệ giữa các lượt — `measured_system_hash` phải giống hệt ở cả 3;
- **không** chọn lượt đẹp nhất — báo cáo là `x/k`, mọi lượt đều vào bảng;
- **không** chạy bù một lượt trượt.

Lượt trượt là **dữ liệu**, không phải sự cố cần khắc phục.

---

## 2. Ngân sách — phép tính hiện ra

```
mỗi lượt/bài    6 logic · 8 HTTP
                dẫn từ call graph: analyze ≤2 · semantic_analyze 1
                                   · semantic_program ≤3   (+ đệm transient)

logic    20 bài × 3 lượt × 6 logic  =  360
HTTP     20 bài × 3 lượt × 8 HTTP   =  480
```

| | N | k | logic | HTTP | so với trần DEV |
|---|--:|--:|--:|--:|---|
| DEV (đã duyệt) | 10 | 1 | 60 | 80 | 1,0× |
| Held-out, bản trước | 20 | 1 | 120 | 160 | 2,0× |
| **CHỐT** | 20 | **3** | **360** | **480** | **6,0×** |

**Hằng số mỗi lượt không đổi một đơn vị.** Toàn bộ phần tăng đến từ `N × k`, và
mỗi thừa số đều đọc được: `20` là số ô của `BANG_O`, `3` là `k`.

⚠️ `480` là **trần**, không phải mức tiêu dự kiến. Nó giả định mọi bài đều dùng
hết `semantic_program ≤3` lượt sửa; thực tế trên DEV phần lớn bài dùng 1.

---

## 3. Vì sao B, và vì sao không A

**Lý do quyết định là ⑤ `stability` đã đóng băng ở 7A.2 với `k ≥ 3` NẰM TRONG
ĐỊNH NGHĨA** (`PHASE7_METRIC_CONTRACT §2⑤`). `k = 1` không phải "báo cáo gọn
hơn" — nó buộc phải **phá một chỉ số vừa đóng băng**, ở đúng lượt đo chính thức,
và §4 lại cấm báo pass/fail cho một đề chạy `k` lượt. Đóng băng rồi phá ngay
lượt sau là đúng thứ việc đóng băng sinh ra để ngăn.

**Bằng chứng `k = 1` cho số không bền — đo được trên chính kho này:**

```
Phase 6.6   cùng mã, cùng ba đề, hai lượt liên tiếp:  0/3  rồi  3/3
Phase 7A    5-goc: lượt 1 và 3 QUA, lượt 2 TRƯỢT
            (`analyze` không tất định khi khai vai trò geometric_perpendicular)
```

Lượt trượt ấy, nếu là lượt **duy nhất**, vào luận văn thành *"mô hình không làm
được"*. Nó không đúng — và ở `k=1` thì **không có cách nào biết**.

**Vì sao `k=3` cả tầng B, không chỉ tầng A** (tức không chọn Option C): tầng B
kiểm *"gặp đề ngoài khả năng, hệ nói thẳng hay bịa hình?"*, và bằng chứng 7A cho
thấy **chính hành vi từ chối cũng không tất định**. `k=1` ở đó là tung đồng xu,
và ô **B03 — góc nhị diện** là ô quan trọng nhất cả tập: nó kiểm hệ có lặng lẽ
trả lời câu nhị diện bằng góc mặt–mặt hay không. Tiết kiệm 96 HTTP để đánh đổi
đúng câu hỏi mà tầng B sinh ra để trả lời là một món hời tồi.

**Phương án lui, nếu ngân sách bị từ chối:** Option C — `k=3` tầng A, `k=1` tầng
B (288 logic / 384 HTTP). Dùng C thì báo cáo **buộc phải viết** *"tầng B: 1
lượt/ô, chưa đo được độ ổn định của từ chối"*. **Không** lui về A.

---

## 4. Rủi ro chấp nhận — khai trước, không khai sau

| # | Rủi ro | Vì sao vẫn chấp nhận |
|---|---|---|
| 1 | **Chi phí 6,0× trần DEV.** Một lượt đo tốn 480 HTTP | Đây là **lượt đo chính thức của luận văn**, chạy **một lần**. Rẻ hơn phải chạy lại vì số không diễn giải được |
| 2 | **`k=3` vẫn là mẫu nhỏ.** `2/3` và `3/3` không phân biệt được về mặt thống kê | `§4` đã cấm suy tỉ lệ khi mẫu < 20. `x/k` đọc là **đếm thô** và **phân bố**, không phải xác suất. Báo cáo phải viết đúng thế |
| 3 | **Vẫn không tách được ô khỏi bài.** Một bài mỗi ô | `k` mua phương sai **giữa các lượt**, không mua phương sai **giữa các bài trong một ô**. Muốn thứ sau phải rút nhiều bài mỗi ô — một tập khác. `HOLDOUT_PROTOCOL §7` đã ghi |
| 4 | **Phiên dài hơn ⇒ nguy cơ đứt giữa chừng cao hơn** | Artifact ghi **từng lượt** (`case_id/run_00k/`), và bộ đo **từ chối ghi đè** thư mục đã có bản ghi. Đứt thì tiếp được, nhưng **phải khai** phiên bị chia và `measured_system_hash` không đổi giữa hai nửa |
| 5 | **Lượt trượt vì mạng/quota bị đọc nhầm thành lượt trượt của mô hình** | Taxonomy 4 nhóm (`§3`) không có nhóm cho lỗi hạ tầng ⇒ phải ghi riêng vào `FAILURE_LOG.md`, **không** nhét vào `model generation` |

---

## 5. Việc kèm theo — đã làm ở Phase 7A.3

- ✅ `HOLDOUT_PROTOCOL §2` — làm rõ *"một lượt"* = **một phiên gồm `k` lượt**,
  cấm lặp CÓ SỬA chứ không cấm cỡ mẫu.
- ✅ `HOLDOUT_PROTOCOL §5` — ngân sách `360/480`, phép tính hiện ra, kèm bảng so
  với trần DEV.
- ✅ `HOLDOUT_PROTOCOL §5⑤/⑥` — bước chạy đổi thành *"CHẠY MỘT PHIÊN"*; bước báo
  cáo đổi `obligation_match` → `construction_match` + `verification_match` +
  `stability (x/k)`, theo đúng bản tách ở 7A.2.
- ✅ `HOLDOUT_PROTOCOL §7` — hạn chế *"một bài mỗi ô"* thu hẹp lại, **không** bỏ.
- ✅ `PHASE7_METRIC_CONTRACT §7` — ghi là **đổi điều kiện lấy mẫu**, không đổi
  định nghĩa chỉ số nào. Không có số cũ để so vì ⑤ chưa từng đo trên held-out.

---

## 6. Điều file này KHÔNG làm

- **Không** chạy gì. 0 API call.
- **Không** rút seed, không niêm phong.
- **Không** duyệt ngân sách thay ai — nó **ghi** con số phải duyệt.
- `k` **đã đóng băng** kể từ đây: đổi `k` sau khi thấy số là chọn cỡ mẫu theo
  điểm, và phải khai ở `PHASE7_METRIC_CONTRACT §7` kèm cả hai lượt đo.
