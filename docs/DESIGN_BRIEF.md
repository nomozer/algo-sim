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
>
> **Giai đoạn (2026-10-05, `cuboid-final-review`).** Brief này viết lần đầu cho sản phẩm Tin học. §1, bố cục
> workspace, §4 và §8 nay mô tả miền hình học; phần cũ chép nguyên văn ở
> [`legacy/DESIGN_BRIEF_INFORMATICS_ERA.md`](legacy/DESIGN_BRIEF_INFORMATICS_ERA.md). Các **luật** ở §3, §5–§7, §9
> vẫn hiệu lực; ví dụ minh hoạ của chúng (cây, cổng logic, cơ số) là ví dụ của giai đoạn cũ.

---

## 1. Sản phẩm là gì

**Tên đề tài:** *Nghiên cứu và xây dựng hệ thống mô phỏng 3D hình học không gian* (`STATUS_LEDGER
§0-2026-08-24`).

Học sinh **gõ đề hình học không gian bằng tiếng Việt** (hoặc chụp ảnh đề: hệ chép lại, học sinh duyệt/sửa trước
khi gửi). LLM **chỉ đọc đề** và viết các bước dựng hình bằng **tên** của vật đã dựng — không bao giờ phán toạ
độ. **Engine hình học tất định** ở máy chủ dựng hình chính xác và kiểm định; trình duyệt diễn hoạt từng bước
trong Scene3D (`ARCHITECTURE_MAP.md` §1–§2).

> **Câu một dòng cho người thiết kế:** *AI hiểu đề — máy tất định mới được
> phép "biết đáp án". Giao diện phải luôn nói đúng sự thật đó.*

**Người học:** học sinh THPT Việt Nam, Toán 11–12, phần hình học không gian. Không phải lập trình viên. **Mọi
chữ trên màn hình là tiếng Việt.**

**Quy mô hiện tại:** một mô phỏng sản phẩm (`generic.semantic_program`); họ hình được hỗ trợ:
`backend/app/simulation/product_capability.py`.

*(Ba đoạn mô tả sản phẩm Tin học — tên đề tài 2026-08-18, người học môn Tin học, quy mô 19 mô phỏng / 6 miền —
nguyên văn ở [`legacy/DESIGN_BRIEF_INFORMATICS_ERA.md`](legacy/DESIGN_BRIEF_INFORMATICS_ERA.md).)*

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

*Hộp máy chủ và hai loại từ chối trong sơ đồ là luồng Tin học. Luồng hiện hành: `ARCHITECTURE_MAP.md` §2a; thẻ
từ chối nêu đúng chặng đã dừng và lý do của chặng ấy (`frontend/src/components/SimulationWorkspace.tsx`).*

**Bốn màn hình** (thanh điều hướng trên cùng): **Trang chủ** · **Thư viện** ·
**Lịch sử** · (**Workspace** hiện khi có mô phỏng đang mở).

- **Trang chủ** — ô nhập đề là nhân vật chính; dưới là thẻ "Gợi ý khám phá".
- **Thư viện** — danh mục bài mẫu công khai, mở được **không cần AI**.
- **Lịch sử** — phiên đã học, mở lại **không cần AI** (chạy lại engine tất định).
- **Workspace** — nơi diễn ra mô phỏng.

### Bố cục Workspace

Workspace là `Scene3DExplorer`: sân khấu 3D, dòng thời gian từng bước, vùng soi chi tiết của đại lượng đang
chọn và lời giải (thu gọn mặc định) — mô tả và chủ sở hữu ở `CODE_INDEX.md` (miền hình học). Bảng bố cục hai
cột của giai đoạn Tin học: nguyên văn ở [`legacy/DESIGN_BRIEF_INFORMATICS_ERA.md`](legacy/DESIGN_BRIEF_INFORMATICS_ERA.md).

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

Hợp đồng hiển thị hiện hành của miền hình học: định danh cạnh, chủ sở hữu thị giác và nét khuất ở
[`architecture/OCCLUSION_AND_SCENE_IDENTITY_AMENDMENT.md`](architecture/OCCLUSION_AND_SCENE_IDENTITY_AMENDMENT.md);
bất biến khoá bằng test ở `ARCHITECTURE_MAP.md` §5 (#31, #35, #38, #39). Bảng hợp đồng theo bảy miền Tin học
và đoạn *Về 3D*: nguyên văn ở [`legacy/DESIGN_BRIEF_INFORMATICS_ERA.md`](legacy/DESIGN_BRIEF_INFORMATICS_ERA.md).

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

Yêu cầu giao diện đang chờ (chưa làm) ghi ở [`ROADMAP.md`](ROADMAP.md). Bảng việc thiết kế của giai đoạn Tin học (cây, bảng/CSDL) và danh sách đóng băng của nó: nguyên văn ở [`legacy/DESIGN_BRIEF_INFORMATICS_ERA.md`](legacy/DESIGN_BRIEF_INFORMATICS_ERA.md).

---

## 9. Ba câu hỏi tự kiểm trước khi nộp thiết kế

1. **Mọi thứ tôi vẽ có nguồn từ trạng thái engine không?** (Nếu là số liệu do
   tôi tự nghĩ ra → sai.)
2. **Học sinh có hiểu được *cơ chế* chỉ bằng cách nhìn, không cần đọc tiêu đề
   không?**
3. **Khi hệ từ chối, học sinh có biết phải làm gì tiếp không?**
