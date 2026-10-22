# DESIGN_BRIEF.md — Định hướng thiết kế UI/UX và Scene3D cho AlgoSim

> **Đọc tài liệu này trước khi thiết kế UI/UX hoặc trực quan hóa Scene3D cho AlgoSim.**
> Tài liệu này dịch các ràng buộc kiến trúc và sư phạm của hệ thống mô phỏng 3D hình học không gian thành quy chuẩn thiết kế giao diện.
>
> **Phân biệt rõ vai trò của các tài liệu:**
> - [`DESIGN.md`](../DESIGN.md) (gốc repo): **Tài liệu tham khảo giao diện website** theo phong cách Notion (Light Mode, typography, spacing, bố cục khung trang). **Tuyệt đối không lấy bảng màu trang trí (sticker palette) của Notion trong `DESIGN.md` làm quy chuẩn bắt buộc cho vật liệu hình học 3D của Scene3D.**
> - [`docs/ARCHITECTURE_MAP.md`](ARCHITECTURE_MAP.md): Bản đồ kiến trúc kỹ thuật, sở hữu dữ liệu và các bất biến có kiểm thử khóa.
> - [`docs/architecture/OCCLUSION_AND_SCENE_IDENTITY_AMENDMENT.md`](architecture/OCCLUSION_AND_SCENE_IDENTITY_AMENDMENT.md): Hợp đồng định danh cạnh, mặt che khuất (`VISIBLE`/`HIDDEN`) và danh tính thực thể trong Scene3D.
> - [`docs/legacy/DESIGN_BRIEF_INFORMATICS_ERA.md`](legacy/DESIGN_BRIEF_INFORMATICS_ERA.md): Bản lưu lịch sử của giai đoạn mô phỏng Tin học đã gỡ bỏ (chỉ giữ để tra cứu lịch sử, không dùng cho thiết kế hay phát triển hiện tại).

---

## 1. Sản phẩm và mục tiêu cốt lõi

**Tên đề tài:** *Nghiên cứu và xây dựng hệ thống mô phỏng 3D hình học không gian* (`STATUS_LEDGER §0-2026-08-24`).

**Mục tiêu sản phẩm:** Chuyển đề bài hình học không gian tiếng Việt (Toán 11–12 THPT) thành **mô phỏng 3D hình học không gian tương tác** có kiểm chứng tất định, giúp học sinh quan sát trực quan cấu trúc khối, từng bước dựng hình, thiết diện và các quan hệ vuông góc/song song/khoảng cách/góc/thể tích. AlgoSim **không phải** hệ thống tự động giải và chứng minh mọi bài toán toán học tổng quát.

**Phân biệt trạng thái kiến trúc (AS-IS vs. TO-BE):**
- **AS-IS (Tuyến sản phẩm mặc định hiện hành — `DEFAULT_MODE = LLM_ONLY`):**
  Đề bài tiếng Việt → AI trích xuất `RequestContract` → AI tổng hợp `SemanticProgramSpec` → Chuỗi cổng kiểm định tất định fail-closed (`validator`, `ir_static_check`, `formation`, `interpreter`/kernel chính xác, `construction_binding`, `grounding_gate`, `assumption_gate`, `visual_obligation_gate`) → `Scene3D`.
- **TO-BE (Kiến trúc mục tiêu — Hybrid):**
  Đề bài tiếng Việt → AI trích xuất JSON Typed Facts (`TypedFact` / `TypedFactNext`) → Semantic Grounding (kiểm chứng căn cứ nguyên văn từ câu đề) → Goal-Directed Construction Planner tất định tự phối hợp Geometry Functions → Compiler / Construction IR → Geometry Functions / Engine / Kernel chính xác → `Scene3D`.
  *(Lưu ý: Tuyến **Hybrid** đã triển khai các thành phần cốt lõi và đường kiểm thử/preview nhưng chưa bật làm tuyến sản phẩm mặc định cho tới khi vượt qua đầy đủ các cổng tại [`docs/MIGRATION_CHECKLIST.md`](MIGRATION_CHECKLIST.md).)*

> **Nguyên tắc vàng cho người thiết kế:** *AI chỉ trích xuất ngữ nghĩa từ đề bài — mọi tọa độ, phép dựng, phân loại nét hiện/khuất và kết quả đo đều thuộc thẩm quyền của Engine/Kernel tất định. Giao diện chỉ trình bày trung thực trạng thái đã kiểm chứng đó.*

**Người dùng mục tiêu:** Học sinh và giáo viên THPT Việt Nam (chương trình Toán 11–12, phần hình học không gian). Toàn bộ ngôn ngữ hiển thị trên giao diện là tiếng Việt chuẩn sư phạm.

---

## 2. Luồng trải nghiệm chính

```text
         ┌────────────────────── TRANG CHỦ ──────────────────────┐
         │  Ô nhập đề tiếng Việt (văn bản / .docx / ảnh chụp có   │
         │  bước học sinh duyệt và xác nhận văn bản trích xuất)  │
         │  + Thẻ bài mẫu khám phá nhanh (không tốn lượt gọi AI)  │
         └──────────────────────────┬────────────────────────────┘
                                    │ Gửi phân tích
                                    ▼
         ┌───────────────────────────────────────────────────────┐
         │  Máy chủ xử lý & kiểm chứng tất định (Fail-Closed)    │
         │  • Tuyến mặc định AS-IS (LLM_ONLY)                    │
         │  • Kiến trúc mục tiêu TO-BE (Hybrid)                  │
         └──────────────────────────┬────────────────────────────┘
                                    │
                   ┌────────────────┴────────────────┐
                   ▼                                 ▼
     ┌───────────────────────────┐     ┌─────────────────────────────────┐
     │  WORKSPACE MÔ PHỎNG 3D    │     │  TỪ CHỐI TRUNG THỰC             │
     │  (`Scene3DExplorer`)      │     │  (`UnsupportedNotice`)          │
     │  • Sân khấu 3D tương tác  │     │  • Nêu rõ chặng dừng & nguyên   │
     │  • Thanh bước dựng hình   │     │    nhân (thiếu dữ kiện nguồn,   │
     │  • Chế độ Mô phỏng (A) /  │     │    mâu thuẫn hình học, hoặc     │
     │    Phân tích & Lời giải(B)│     │    ngoài phạm vi dựng hình)     │
     └───────────────────────────┘     └─────────────────────────────────┘
```

**Bốn màn hình** (thanh điều hướng trên cùng): **Trang chủ** · **Thư viện** · **Lịch sử** · (**Workspace** hiện khi có mô phỏng đang mở).

- **Trang chủ:** Ô nhập đề và danh sách bài mẫu hình học không gian.
- **Thư viện:** Các mô phỏng mẫu đã kiểm chứng, mở tức thì không gọi AI.
- **Lịch sử:** Mở lại các phiên mô phỏng đã lưu từ `localStorage` hoàn toàn tất định (`ZERO-AI`).
- **Workspace (`Scene3DExplorer`):** Không gian quan sát và tương tác 3D, gồm sân khấu Three.js, điều khiển góc nhìn/chế độ hiển thị, thanh tua theo bước dựng hình (`geometryTimeline`), và bảng phân tích/lời giải thu gọn mặc định.

---

## 3. Các nguyên tắc UX bắt buộc

### 3.1. Không hiển thị dữ kiện không có căn cứ
Mọi điểm, đoạn thẳng, mặt phẳng, khối đa diện, khối tròn xoay, thiết diện, nhãn độ dài và công thức hiển thị trên màn hình phải bắt nguồn từ dữ kiện có căn cứ trong đề bài và trạng thái đã được backend kiểm chứng. Tuyệt đối không vẽ thêm đối tượng trang trí tùy tiện hoặc tự suy diễn số đo ở tầng frontend.

### 3.2. Không bịa affordance (chống điều khiển rỗng)
Giao diện chỉ hiển thị các nút điều khiển và bảng thông tin khi cảnh `Scene3D` thực sự có dữ liệu hoặc năng lực tương ứng. Tính năng hoặc thành phần không tồn tại trong cảnh hiện tại thì **vắng mặt**, không hiển thị nút giả hay khung rỗng gây hiểu nhầm.

### 3.3. Ưu tiên khả năng quan sát và tương tác — không lộ đáp án ở chế độ mặc định
- Khi mở mô phỏng, hệ thống mặc định ở **Chế độ A (Mô phỏng / Quan sát)**: học sinh tự do xoay, thu phóng, dịch chuyển camera, tua qua từng bước dựng hình (`GEOMETRY_CONSTRUCTION`), bật/tắt nhãn, chọn hoặc cô lập thực thể mà **không bị lộ ngay đáp số cuối cùng** trên sân khấu.
- Chỉ khi học sinh chủ động chuyển sang bước kết luận hoặc mở **Chế độ B (Phân tích / Lời giải)** thì các đại lượng mục tiêu (`COMPUTE_TARGET`) và công thức/chứng chỉ tính toán mới được trình bày chi tiết.

### 3.4. Phân biệt rõ cạnh hiện và cạnh khuất
Trong hình học không gian 3D, việc phân biệt cạnh nhìn thấy (`VISIBLE` — nét liền) và cạnh bị che khuất (`HIDDEN` — nét đứt) là quy chuẩn sư phạm bắt buộc của sách giáo khoa Toán THPT:
- Danh tính cạnh chuẩn tắc và quyền che khuất (`SOLID_FACE` / khối cong) do hệ thống phân loại theo góc nhìn camera thực tế ([`architecture/OCCLUSION_AND_SCENE_IDENTITY_AMENDMENT.md`](architecture/OCCLUSION_AND_SCENE_IDENTITY_AMENDMENT.md)).
- Các đối tượng dẫn xuất chỉ đóng vai trò chọn/nhấn sáng (highlight/hit proxy), không vẽ đè lớp nét liền/đứt thứ hai làm hỏng nét khuất chuẩn tắc.

### 3.5. Ngôn ngữ phù hợp học sinh THPT
- Sử dụng thuật ngữ hình học phổ thông chuẩn xác: *đỉnh, cạnh đáy, cạnh bên, đường cao, hình chiếu vuông góc, trung điểm, trọng tâm, giao điểm, giao tuyến, mặt phẳng cắt, thiết diện, khối chóp, khối lăng trụ, hình hộp, hình trụ, hình nón, mặt cầu*.
- **Cấm tuyệt đối trên màn hình học sinh:** mã lỗi nội bộ (`SOURCE_OBJECT_MISMATCH`, `capability_gap`, `TYPED_FACT_NEXT_*`), tên hàm/module kỹ thuật, đường dẫn JSON schema hoặc stack trace.

### 3.6. Không chỉ dùng màu sắc để truyền đạt thông tin
Mỗi vai trò hình học và mỗi trạng thái tương tác phải kết hợp **tối thiểu hai kênh tín hiệu thị giác**: màu sắc + kiểu nét (liền / đứt / độ dày nét) + độ trong suốt của mặt + ký hiệu hình học (góc vuông, nhãn điểm/đoạn) + cấu trúc phân nhóm trên giao diện. Biểu tượng điều khiển phải dùng **SVG**, không dùng emoji hoặc ký tự Unicode đặc biệt dễ lỗi font (tofu).

---

## 4. Ba lớp thiết kế tách biệt (Three Design Layers)

Để tránh nhầm lẫn giữa giao diện khung web và trực quan hóa hình học 3D, hệ thống thiết kế của AlgoSim được tách nghiêm ngặt thành **ba lớp độc lập**:

### Lớp 1: Website UI Tokens (`frontend/src/styles/tokens.css`, `global.css`)
- Quản lý bề mặt ứng dụng web xung quanh sân khấu 3D: nền trang Light Mode (`--canvas`, `--canvas-soft`), màu chữ (`--ink`, `--ink-muted`, `--ink-faint`), đường viền khung (`--hairline`), màu nhấn hành động của nút bấm (`--primary`), kiểu chữ (`Inter`) và thang khoảng cách (`--sp-*`).
- [`DESIGN.md`](../DESIGN.md) là tài liệu tham khảo cho lớp Website UI này.
- **Quy tắc cứng:** Mọi lệnh gọi `var(--token)` trong CSS/TSX phải trỏ tới token đã định nghĩa trong `tokens.css` (được khóa bởi `frontend/src/styles/tokens.test.ts`). **Không lấy bảng màu sticker trang trí của `DESIGN.md` áp vào vật liệu 3D của Scene3D.**

### Lớp 2: Scene3D Geometry Semantic Roles (`scene3d-roles.ts`, `scene3d-view.tsx`)
- Quản lý ngôn ngữ thị giác của các thực thể hình học trong không gian 3D dựa trên **vai trò ngữ nghĩa (semantic roles)** chứ không thiết kế bảng màu riêng cho từng loại hình học rời rạc:
  1. **Khối chính và mặt biên (`SOLID_FACE`, `BASE_REGION`, `mesh`, `curved_solid`):** Khối đa diện hoặc khối tròn xoay làm nền không gian trung tính, đủ rõ cấu trúc khối nhưng không che lấp các yếu tố dựng hình bên trong.
  2. **Cạnh cấu trúc hiện / khuất (`VISIBLE` / `HIDDEN`):** Cạnh thấy vẽ nét liền sắc nét; cạnh bị che vẽ nét đứt rõ nhịp, đọc được ngay trên nền mặt khối.
  3. **Hình phụ và mặt phẳng phụ (`AUXILIARY_SURFACE`, `plane3`, đường dựng phụ):** Các mặt phẳng hoặc đường mở rộng giúp học sinh hiểu phép dựng mà không lấn át khối chính.
  4. **Đối tượng dẫn xuất và quan hệ hình học (`altitude`, `projection`, `intersection_line`, góc vuông):** Đường cao, hình chiếu, giao tuyến và ký hiệu vuông góc giúp nhận diện ngay cơ chế hình học.
  5. **Thiết diện (`SECTION_REGION`, `section_fill`, `section_border`):** Đa giác hoặc hình tròn/elip giao của mặt phẳng cắt với khối, có phần tô mặt và viền hiện/khuất nổi bật, tách biệt rõ với mặt bên của khối chính.
  6. **Nội dung mục tiêu đang học (`COMPUTE_TARGET`):** Đại lượng hoặc thực thể mà câu hỏi yêu cầu tìm.
- **Trạng thái bảng màu Scene3D:** *Chưa chốt bảng màu Scene3D cuối cùng trong đợt sửa tài liệu này. Việc lựa chọn và phê duyệt bảng màu/vật liệu Scene3D thuộc phiên nghiên cứu thiết kế trực quan riêng đang chờ Owner phê duyệt.*

### Lớp 3: Interaction States (`interaction-state.ts`, `Scene3DExplorer.tsx`)
- Quản lý trạng thái tương tác của người học tại thời điểm xem (hoàn toàn thuộc tầng trình bày, không làm thay đổi tọa độ hay số đo của engine):
  - **Trạng thái chọn & tập trung:** Mặc định (`default`), di chuột (`hover`), đang chọn (`selected`), cô lập đối tượng (`isolated` / làm mờ phần còn lại), và bung hình (`explode`).
  - **Chế độ chiều sâu / nhìn xuyên:** Chế độ thường (`Normal` — mặt trước của khối che khuất phần nằm sau) và chế độ nhìn xuyên (`X-ray` — hỗ trợ quan sát cấu trúc và thiết diện bên trong khối).
  - **Trạng thái dòng thời gian & chế độ học:** Bước dựng hiện tại trên `geometryTimeline` và chuyển đổi giữa **Chế độ A (Mô phỏng)** với **Chế độ B (Phân tích / Lời giải)**.

---

## 5. Giọng văn sư phạm và màn hình từ chối

- **Xưng hô:** Gọi người học là **"em"**, ngôn phong rõ ràng, tôn trọng và khích lệ tư duy hình học.
- **Thuyết minh bước dựng:** Nêu rõ **phép dựng hình học + căn cứ**, ví dụ: *"Dựng hình chiếu vuông góc H của S lên mặt phẳng đáy (ABCD)"* hoặc *"Xác định giao tuyến MN của mặt phẳng cắt với mặt bên (SAB)"*.
- **Khi từ chối phục vụ (`UnsupportedNotice`):**
  - Hệ thống tuân thủ nguyên tắc **thà từ chối trung thực còn hơn vẽ hình xấp xỉ gây hiểu lầm** (`fail-closed`).
  - Màn hình từ chối là trải nghiệm hạng nhất của sản phẩm: phân biệt rõ nguyên nhân thuộc về dữ kiện đề bài (`SOURCE` — thiếu kích thước, dữ kiện mâu thuẫn, gợi ý học sinh kiểm tra/bổ sung đề) hay giới hạn phạm vi dựng hình hiện tại của hệ thống (`CONSTRUCTION` / `UNKNOWN`), tuyệt đối không đổ lỗi mơ hồ hay hiển thị mã lỗi kỹ thuật.

---

## 6. Quy trình kiểm chứng giao diện và trực quan 3D

Kiểm thử đơn vị (`vitest`) và kiểm thử SSR không thay thế được kiểm chứng thị giác trên trình duyệt thật với WebGL:

1. Chạy kiểm thử đơn vị và vệ sinh giao diện: `npx vitest run` (bao gồm `tokens.test.ts`, `ui-hygiene.test.ts`, `rules-hygiene.test.ts`, `scene3d-occlusion-gates.test.ts`).
2. Kiểm tra trực quan trên trình duyệt thật / WebGL (`npm run dev`, `node scripts/spot-check-demo.mjs`):
   - Đảm bảo khung nhìn camera (`scene3d-camera.ts`) căn chỉnh hình học nằm trọn trong vùng an toàn, không bị bảng phân tích che khuất.
   - Đảm bảo cạnh hiện/khuất, thiết diện, nhãn điểm (`display_label`) không chồng lấn và đọc rõ ở cả góc nhìn mặc định lẫn khi xoay camera.
   - Không tuyên bố hoàn tất thiết kế trực quan Scene3D khi chưa có ảnh chụp so sánh và phê duyệt của Owner.

---

## 7. Ba câu hỏi tự kiểm trước khi đề xuất thiết kế

1. **Mọi thực thể, nhãn và con số hiển thị có xuất phát 100% từ dữ liệu đã kiểm chứng của engine không?** (Nếu giao diện tự suy đoán hoặc vẽ xấp xỉ → loại.)
2. **Học sinh nhìn vào Scene3D có phân biệt được ngay khối chính, hình phụ, cạnh hiện/khuất, đối tượng dẫn xuất và thiết diện mà không bị rối mắt hay lộ đáp số sớm không?**
3. **Ba lớp thiết kế (Website UI Tokens · Scene3D Semantic Roles · Interaction States) đã được tách bạch, không lấy màu trang trí của `DESIGN.md` áp cứng vào vật liệu hình học 3D chưa?**
