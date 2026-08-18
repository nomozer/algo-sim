# DESIGN_BRIEF.md — Bản tóm luồng & định hướng thiết kế cho AI/nhà thiết kế

> **Đọc file này nếu bạn được giao thiết kế UI/UX cho AlgoSim.** Nó tự chứa:
> sản phẩm là gì, người học là ai, luồng đi ra sao, những ràng buộc **không
> được phá**, và chỗ nào đang cần thiết kế.
>
> Phân biệt với hai file dễ nhầm:
> - `DESIGN.md` (gốc repo) = **file token ngôn ngữ thị giác** (màu/chữ/bo góc)
>   phân tích theo phong cách Notion — KHÔNG phải thiết kế sản phẩm.
> - `docs/ARCHITECTURE_MAP.md` = kiến trúc kỹ thuật, bất biến, luồng dữ liệu.
>
> File này là **cầu nối**: dịch ràng buộc kiến trúc thành ràng buộc thiết kế.

---

## 1. Sản phẩm là gì

**Tên đề tài:** *Hệ thống mô phỏng tương tác kết hợp LLM phân tích bài toán
bằng ngôn ngữ tự nhiên, hỗ trợ dạy học môn Tin học THPT.*

Học sinh **dán một đề bài bằng tiếng Việt**. LLM (Gemini) **chỉ đọc hiểu đề và
điền một bản đặc tả đã kiểm định**. Sau đó **một engine tất định chạy trên
trình duyệt** sinh ra toàn bộ diễn biến, hoạt cảnh và kết quả.

> **Câu một dòng cho người thiết kế:** *AI hiểu đề — máy tất định mới được
> phép "biết đáp án". Giao diện phải luôn nói đúng sự thật đó.*

**Người học:** học sinh THPT Việt Nam (lớp 10–12), môn Tin học, chương trình
GDPT 2018. Không phải lập trình viên. **Mọi chữ trên màn hình là tiếng Việt.**

**Quy mô hiện tại:** 9 họ năng lực · 19 mô phỏng · 6 miền hiển thị
(`algorithm`, `binary`, `logic`, `network`, `tree`, `generic`).

---

## 2. Luồng chính (the flow)

```
        ┌──────────────── TRANG CHỦ ────────────────┐
        │  Ô nhập đề (text / ảnh / .docx / .py)     │
        │  + Gợi ý khám phá (thẻ bài mẫu)           │
        └───────────────┬───────────────────────────┘
                        │ bấm gửi
                        ▼
              ┌─────────────────────┐
              │  AI phân tích đề    │   (server: analyze → classify → simulate,
              │  (chờ ~vài giây)    │    validate 2 tầng, tối đa 3 lần thử)
              └──────────┬──────────┘
                         │
        ┌────────────────┴─────────────────┐
        ▼                                  ▼
┌───────────────┐                 ┌──────────────────────────┐
│  WORKSPACE    │                 │  TỪ CHỐI TRUNG THỰC       │
│  (mô phỏng)   │                 │  — 2 loại, KHÁC NHAU:     │
│               │                 │  • CHƯA ĐỦ DỮ KIỆN        │
│  sân khấu +   │                 │    (dạng bài CÓ hỗ trợ,   │
│  panel + dòng │                 │     đề thiếu dữ liệu)     │
│  thời gian    │                 │  • NGOÀI DANH MỤC         │
└───────────────┘                 │    (chưa mô phỏng được)   │
                                  └──────────────────────────┘
```

**Bốn màn hình** (thanh điều hướng trên cùng): **Trang chủ** · **Thư viện** ·
**Lịch sử** · (**Workspace** hiện khi có mô phỏng đang mở).

- **Trang chủ** — ô nhập đề là nhân vật chính; dưới là thẻ "Gợi ý khám phá".
- **Thư viện** — danh mục bài mẫu công khai, mở được **không cần AI**.
- **Lịch sử** — phiên đã học, mở lại **không cần AI** (chạy lại engine tất định).
- **Workspace** — nơi diễn ra mô phỏng.

### Bố cục Workspace (2 cột)

| Vùng | Nội dung |
|---|---|
| **Sân khấu** (trái, lớn) | Hình ảnh mô phỏng: dãy cột, cây, đồ thị, mạch, bit… |
| **Panel trạng thái** (dưới sân khấu) | Ngăn xếp/hàng đợi/biến — **sự thật engine**, cập nhật từng bước |
| **Thuyết minh** (dưới panel) | Một câu nói **hành động & nguyên nhân** của bước hiện tại |
| **Quan sát** (phải) | Siêu dữ liệu: biến thể, gốc, tiến độ, "Hỏi AI về bước này" |
| **Dòng thời gian** (đáy, full width) | ⏮ ◀ ▶ Tự chạy ⏭ · Đặt lại · "Bước 12 / 22" · tốc độ · thanh trượt |

---

## 3. Bảy ràng buộc thiết kế KHÔNG ĐƯỢC PHÁ

Đây là ranh giới đã trả giá bằng bug thật. Vi phạm = thiết kế bị từ chối.

### 3.1. Giao diện không được "diễn" thứ engine không có
Mọi số, nhãn, mũi tên trên màn hình phải **đọc từ trạng thái engine**. Không
được vẽ một hoạt cảnh "cho đẹp" rồi ngụ ý đó là kết quả tính toán.

### 3.2. Không bịa affordance
Mô-đun nào **không khai** năng lực nào thì UI **không hiện nút** cho nó. Ví dụ:
bài *khám phá* (`logic.and_gate`, `binary.decimal_to_binary`) **không có dòng
thời gian** → **không được** vẽ nút Next/Prev mờ. Thiếu tính năng thì **vắng
mặt**, không phải "có nhưng disabled".

Ba năng lực tuỳ chọn: `timeline` (đi từng bước) · `predict` (nhịp dự đoán) ·
`edit` (sửa cảnh bằng lời).

### 3.3. Hiện dần — cấm lộ đáp án
Kết quả cuối **chỉ được công bố ở bước cuối**. Panel/inspector đang chạy giữa
chừng chỉ được nói *"Đã thăm 2/4: D → B"*, **không** được in sẵn
*"D → B → A → C"*.
*(Đã từng sai: inspector cây in cả thứ tự duyệt ngay bước 0 → học sinh mất cơ
hội tự suy luận. Nay có test khoá.)*

### 3.4. Thuật ngữ của học sinh, không phải của lập trình viên
**Được dùng:** nút gốc · con trái · con phải · nút hiện tại · đã thăm · ngăn
xếp · hàng đợi · thứ tự duyệt · dãy · bước · vòng lặp.

**Cấm tuyệt đối trên màn hình học sinh:** `algorithm.bubble_sort`,
`arbitrary_algorithm`, `capability_gap`, JSON path, thông báo schema, id nội
bộ, stack trace — và các nhãn generic vô nghĩa: **"Điểm 1", "Đoạn nối", "Vật di
chuyển", "GENERIC"**.

### 3.5. Màu không bao giờ là tín hiệu duy nhất
Mỗi trạng thái phải có **ít nhất hai kênh**: màu + (viền / nền / chữ / vị trí).
Ví dụ cây: *nút hiện tại* = cam **và** ở đầu đường active; *đã thăm* = xanh
**và** có trong dải "Đã thăm"; *gốc* = viền xanh dương dày.

### 3.6. Icon là SVG, không phải emoji
Emoji mỗi hệ điều hành vẽ một kiểu và không ăn theo màu chữ. **Có test tự động
chặn emoji** trong mọi component.

### 3.7. Trạng thái không chứa toạ độ
Engine chỉ giữ **ý nghĩa** (id nút, chỉ số, giá trị). **Bố cục là việc của
renderer.** Nhờ vậy cùng một trạng thái vẽ được 2D lẫn 3D.

---

## 4. Hợp đồng hiển thị theo từng miền

Mỗi mô phỏng phải thể hiện được **cơ chế ẩn** của nó — không chỉ vẽ đúng dữ liệu.

| Miền | Phải nhìn thấy | Panel |
|---|---|---|
| **algorithm** (tìm/đếm/tổng/sắp xếp) | dãy cột, ô đang xét, vùng đã sắp, biến chạy, dòng mã giả đang thực hiện | biến + mã giả |
| **tree** (duyệt cây) | gốc rõ, quan hệ **trái/phải** có nhãn, nút hiện tại/đã thăm/chưa thăm khác nhau, đường active | **ngăn xếp** (DFS) hoặc **hàng đợi** (theo mức) |
| **network** (định tuyến, duyệt đồ thị) | đỉnh–cạnh, gói tin/nút đang xét, đường đi dựng dần | hàng đợi / ngăn xếp |
| **network** (đóng gói TCP/IP) | chồng tầng hai đầu gửi–nhận, PDU dày thêm/mỏng đi qua từng tầng | delta từng bước |
| **binary** (bit, đổi cơ số) | ô bit + hàng trọng số, hoặc bảng chia-lấy-dư / trọng số vị trí | tiến trình chuyển đổi |
| **logic** (cổng, mạch) | cổng và dây, đầu vào bật/tắt, đầu ra sáng/tắt | **bảng chân trị** |
| **generic** (cảnh tự dựng) | đúng các đối tượng đề khai (nút, cạnh, công tắc, đèn, ô giá trị) | — |

**Phép thử vàng:** *người xem phải phân biệt được bốn biến thể duyệt cây mà
KHÔNG cần đọc tiêu đề.* Nếu chỉ khác nhau ở chữ trên đầu thì thiết kế chưa đạt.

**Về 3D:** 3D **không phải một miền riêng**, chỉ là renderer thứ hai đọc **cùng
trạng thái**. Chỉ dùng 3D khi **trục sâu mang ý nghĩa thật** (ví dụ: Z = tầng
giao thức). 3D xoay cho đẹp = bị cấm.

---

## 5. Ngôn ngữ thị giác (lấy từ `DESIGN.md` + `tokens.css`)

Tinh thần: **giấy trắng yên tĩnh, chữ gần đen, một sắc xanh tự tin**, màu rực
chỉ dùng cho "sticker" ngữ nghĩa.

| Vai trò | Token | Giá trị |
|---|---|---|
| Nhấn chính (nút, gốc cây) | `--primary` | `#0075de` |
| Nền trang / thẻ | `--canvas` / `--canvas-soft` | `#ffffff` / `#f6f5f4` |
| Chữ chính / phụ / mờ | `--ink` / `--ink-muted` / `--ink-faint` | `#000` / `#615d59` / `#a39e98` |
| Đường kẻ, cạnh đồ thị | `--ink-faint` (cạnh), `--hairline` (viền chrome) | |
| Đang xử lý | `--accent-orange` | `#dd5b00` |
| Đã xong / đúng | `--accent-green` | `#1aae39` |
| Chữ | Inter, thang cách **bội số 4px** (`--sp-*`) | |

> ⚠️ **Bẫy đã cháy hai lần:** gọi `var(--ten-khong-ton-tai)` thì trình duyệt
> **vứt im lặng cả dòng khai báo** — không lỗi, không cảnh báo. Đã làm mất toàn
> bộ cạnh cây và cạnh đồ thị (dùng `--border`, tên thật là `--hairline`).
> **Chỉ dùng token có thật**; có test tự động quét cả `.css` lẫn `.tsx`.

---

## 6. Giọng văn với người học

- **Xưng hô:** gọi học sinh là **"em"**. Ví dụ: *"Em muốn khám phá bài toán nào?"*
- **Khi thành công:** câu thuyết minh nói **hành động + lý do**, không chỉ vị trí.
  - ✅ *"Đi xuống con PHẢI của A → C (đẩy vào ngăn xếp)."*
  - ❌ *"Đang ở nút C."*
- **Khi từ chối:** phải **thành thật và chỉ đường**, không đổ lỗi cho học sinh.
  - *Thiếu dữ liệu* → **"CHƯA ĐỦ DỮ KIỆN"** + nêu **thiếu gì** + **ví dụ cách
    viết** + trấn an *"dạng bài này hệ có mô phỏng"*.
  - *Chưa hỗ trợ* → **"NGOÀI DANH MỤC MÔ PHỎNG"** + gợi ý thử bài mẫu.
  - **Không bao giờ** đưa lỗi kỹ thuật cho học sinh đọc.

> Vì sao quan trọng: hệ **thà từ chối còn hơn mô phỏng sai**. Màn hình từ chối
> vì thế là **một phần của sản phẩm**, không phải trạng thái lỗi — phải được
> thiết kế tử tế như màn hình thành công.

---

## 7. Quy trình kiểm thiết kế (bắt buộc)

Test đơn vị **không chạy CSS**, và SSR chỉ so chữ — nên **không đủ** để kết luận
giao diện đạt.

1. Chạy thật trên trình duyệt (`npm run dev`).
2. Chụp **initial / giữa chừng / cuối** cho mỗi trạng thái tiêu biểu.
3. **Nhìn ảnh**, đối chiếu checklist: cấu trúc rõ · trạng thái rõ · **cơ chế
   rõ** · panel đúng loại · thuật ngữ đúng · bố cục không chồng/tràn.
4. Kết luận: `REAL_VISUAL` / `PARTIAL_VISUAL` / `BROKEN_VISUAL`.
   **Không được chấm đạt chỉ vì test xanh.**

Công cụ sẵn có: `npm run audit:layout` (đo lệch/chồng/tràn/lưới 4px trên Chrome
thật) · `scripts/capture-tree-visual.mjs` (chụp theo kịch bản).

---

## 8. Chỗ đang cần thiết kế

| Việc | Trạng thái |
|---|---|
| Cây 1 nút để lại khoảng trắng lớn dưới khung | thẩm mỹ, chưa xử lý |
| Nhãn cạnh 9px khi cây dày hơn 8 nút | cần đo lại nếu nới giới hạn |
| Miền **bảng/CSDL** (`relational_table_query`) | **chưa mở** — sẽ cần ngôn ngữ thị giác cho lưới dữ liệu, vị từ lọc, tổng hợp |
| Chế độ luyện tập / tự kiểm | ngoài phạm vi hiện tại, cần duyệt riêng |

**Đang bị đóng băng phạm vi** (đừng thiết kế nếu chưa được duyệt): miền chuyên
biệt mới, trình soạn thảo mã, undo/redo, phóng to/kéo thả khung nhìn, trình sửa
kiểu, sửa topology.

---

## 9. Ba câu hỏi tự kiểm trước khi nộp thiết kế

1. **Mọi thứ tôi vẽ có nguồn từ trạng thái engine không?** (Nếu là số liệu do
   tôi tự nghĩ ra → sai.)
2. **Học sinh có hiểu được *cơ chế* chỉ bằng cách nhìn, không cần đọc tiêu đề
   không?**
3. **Khi hệ từ chối, học sinh có biết phải làm gì tiếp không?**
