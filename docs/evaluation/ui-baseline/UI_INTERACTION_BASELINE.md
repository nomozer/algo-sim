# UI_INTERACTION_BASELINE.md — Khung giao diện chung của AlgoSim

**Tài liệu QUY ĐỊNH.** Nó nói cái gì bắt buộc, cái gì tuỳ chọn, module được đổi
gì, không được đổi gì, và khi nào được phép sửa UI.

> **Một sản phẩm có giao diện chung ổn định; mỗi module chỉ thay phần biểu diễn
> cơ chế bên trong sân khấu.**

Chốt từ lượt đo READ-ONLY tại `main @ b7ec7dc` trên 5 target đại diện × 2
viewport. Bằng chứng và lý do đầy đủ: `ui_interaction_baseline_audit.md`.
Phán quyết: **`KEEP_WITH_TARGETED_FIXES`** — khung đúng, ba lỗi phải sửa (§6).

Tài liệu này **không** thay `docs/ARCHITECTURE_MAP.md` (bất biến kiến trúc) hay
`docs/DESIGN_BRIEF.md` (ràng buộc thiết kế). Nếu mâu thuẫn: hai file đó thắng.
Nếu mâu thuẫn với **code/test**: code/test thắng — sửa file này.

---

## 1. BẮT BUỘC — mọi mô phỏng, mọi viewport

Một phiên học **phải** có đủ, ở đúng vị trí:

| # | Thành phần | Ràng buộc |
|---|---|---|
| B1 | **Header sản phẩm** | wordmark + Trang chủ / Thư viện / Lịch sử; trong workspace thêm nút bật/tắt `Quan sát`. Không module nào được thay/ẩn. |
| B2 | **Nhãn miền + tên mô phỏng** | badge tiếng Việt cho **người học** (không bao giờ là `simulation_id`) + tiêu đề lấy từ envelope. |
| B3 | **Sân khấu** | đúng **một** vùng, do module sở hữu hoàn toàn. |
| B4 | **Thuyết minh bước hiện tại** | **một câu cho bước đang xem**, ngay dưới sân khấu. Khe là của **shell**; chữ là của **module**. Module timeline **không được** thiếu thành phần này. |
| B5 | **Panel Quan sát** | luôn ở cột phải (desktop) / drawer (narrow), tiêu đề `QUAN SÁT`, nội dung do module cấp. |
| B6 | **Timeline** | thanh tua có `aria-label` + chỉ báo `Bước n / N`. |
| B7 | **Sáu nút điều khiển, đúng thứ tự** | `Về đầu · Lùi một bước · Tự chạy/Dừng · Tiến một bước · Đến cuối · Đặt lại`. Cộng: điều khiển tốc độ, gợi ý phím tắt `← → Space`. |
| B8 | **Trạng thái từ chối** | một trong bốn tiêu đề đã chuẩn hoá, kèm `learner_reason` + một câu bảo học sinh làm gì tiếp. |
| B9 | **Không tràn ngang** | ở mọi viewport ≥ 768px. |
| B10 | **Điều khiển nằm trong màn hình đầu tiên** | ở **mọi** bước và **mọi** viewport ≥ 768×900, không phụ thuộc chiều cao nội dung module. *(hôm nay narrow đang vi phạm — FIX-1)* |

**Luật B7 phụ:** module **không có timeline** (exploratory) chỉ hiện `Đặt lại` +
một câu giải thích. **Cấm nút bước giả.**

---

## 2. TUỲ CHỌN — chỉ khi module thật sự khai capability

| Thành phần | Điều kiện |
|---|---|
| **Ô dự đoán** (`PredictionBar`) | module khai `predict`. Dùng **một** UI chung của shell — cấm bản riêng cho 3D. |
| **Toggle 2D/3D** | module có **≥2 renderer thật**. Dưới 2 → **không** hiện nút nào (cấm affordance rỗng). |
| **Thao tác riêng trên sân khấu** | thao tác **chạm cơ chế ẩn** và sinh hệ quả tất định (COVERAGE §2.6). Tương tác trang trí **không được admit**. |
| **Control nằm TRONG sân khấu** | khi đối tượng thao tác đã có mặt trên sân khấu (vd node đầu vào của mạch logic), **chính nó** là control — **cấm** dựng thêm một hàng nút song song cho cùng thứ đó. Một đối tượng, một chỗ bấm. |
| **Mục tiêu học tập / Nhiệm vụ** | *(khe dành sẵn, CHƯA mở)* chỉ hiện khi target có neo chương trình thật qua `check_admission`. **Cấm bịa mục tiêu để lấp khe.** |

**Luật affordance (mới, từ lượt đo này):** mỗi thao tác riêng **phải** có một câu
nói rõ *bấm/kéo được gì và để làm gì*, ngay cạnh chỗ thao tác. Tương tác mà học
sinh phải đoán ra thì trên thực tế không tồn tại.

**Luật control tự chế:** một control không phải `<button>` thật (vd `<g>` trong
SVG) phải tự mang đủ hợp đồng: `role="button"` · `tabindex="0"` · `aria-pressed`
khi là hai trạng thái · tên khả truy cập nói *cái gì, đang bao nhiêu, bấm được
gì* · Enter và Space · focus indicator thấy rõ · con trỏ/hover.
Và nó **phải chặn phím ở tầng native** (`stopPropagation`) nếu phím đó trùng phím
tắt toàn cục — đã cháy: Space trên node đầu vào vừa đổi giá trị vừa bật Tự chạy.

---

## 3. MODULE ĐƯỢC THAY

1. **Nội dung sân khấu** — 2D hay 3D, dựng gì trong đó là toàn quyền module.
2. **Dữ liệu quan sát** — nội dung `Inspector`.
3. **Chữ thuyết minh** cho từng bước.
4. **Đánh dấu ngữ nghĩa** — dòng hiện tại, ô đang xét, phần tử vừa đổi…
5. **Thao tác riêng** (tuỳ chọn, theo §2).
6. **Renderer 3D** (tuỳ chọn) — đọc **nguyên** state của 2D.

---

## 4. MODULE KHÔNG ĐƯỢC THAY

1. **Không** tự dựng một layout khác với khung §1.
2. **Không** đổi vị trí, thứ tự, nhãn của 6 nút điều khiển; **không** tự thêm nút
   bước riêng bên trong sân khấu.
3. **Không** tự tính lại kết quả trong renderer — renderer chỉ ĐỌC state và phát
   `SimAction`.
4. **Không** công bố đáp án trước khi engine chạy tới bước đó.
5. **Không** dùng màu làm tín hiệu duy nhất — luôn kèm chữ hoặc icon.
6. **Không** biến workspace thành chatbot; AI chỉ ở 4 chỗ tại §5.
7. **Không** dùng ký tự Unicode/emoji làm icon — icon là SVG trong
   `components/icons.tsx`.
8. **Không** đưa dữ liệu trình bày (toạ độ pixel, kích thước canvas) vào engine
   state.
9. **Không** rò chuỗi kỹ thuật (`simulation_id`, `algorithm_id`, mã lỗi,
   đường dẫn validator) ra UI học sinh.

---

## 5. AI ĐƯỢC XUẤT HIỆN Ở ĐÂU — DANH SÁCH ĐÓNG

AlgoSim là **hệ mô phỏng tương tác có AI hỗ trợ phân tích đề và sinh đặc tả**.
Không phải chatbot. AI làm việc ở giai đoạn **hiểu đề**, rồi đứng sang một bên.

1. Ô nhập đề tự nhiên (Trang chủ).
2. Trạng thái "đang phân tích".
3. Bản tóm tắt ngắn "hệ thống đã hiểu" trong panel Quan sát.
4. Phản hồi thiếu dữ kiện / ngoài phạm vi.

**Bốn chỗ. Hết.** Không chỗ nào nằm trong workspace.

**Trong workspace, AI không được có control learner-facing nào** — không nút hỏi,
không accordion, không "Trợ lý AI", không "Giải thích bằng AI", không ô nhập mới,
không nút gọi model khác. Narration + panel Quan sát **phải tự đủ** để giải thích
bước hiện tại; nếu chúng chưa đủ thì việc phải làm là **sửa narration/Observer**,
không phải gắn thêm một đường tiêu token ngay cạnh timeline.
Thực thi: guard quét mã nguồn (`components/ui-hygiene.test.ts`) + render thật
(`components/ux-shell.test.tsx`).

> **Lịch sử — không viết lại.** Mục thu gọn *"Hỏi AI về bước này"* ĐÃ từng tồn
> tại ở đáy panel Quan sát, và audit READ-ONLY tại `b7ec7dc` ghi nhận nó như một
> ngoại lệ được phép (`ui_interaction_baseline_audit.md §2, §8`). Audit đó là
> **bằng chứng lịch sử tại thời điểm đó** và **giữ nguyên, không sửa**. Mục này
> là quyết định sản phẩm **sau** audit: ngoại lệ bị gỡ, danh sách còn đúng bốn.

Đây là R0 (LLM không sở hữu runtime) phản chiếu lên giao diện — dành cho AI một
góc thường trực trong workspace là đang nói ngược lại kiến trúc.

---

## 6. Ba việc phải sửa trước pilot

| | Việc | Loại | Ràng buộc khi sửa |
|---|---|---|---|
| **FIX-1** | Giữ thanh điều khiển trong màn hình đầu tiên ở narrow (đang tụt 99px khi ô dự đoán hiện) | `RESPONSIVE_DEFECT` | chỉ CSS; **không** đổi DOM của module; giữ nguyên hành vi desktop |
| **FIX-2** | Đưa khe thuyết minh về shell; module chỉ trả chuỗi | `STRUCTURAL_INCONSISTENCY` | **không** đụng engine/state/timeline; ba hiện thực hiện tại quy về một |
| **FIX-3** | Thêm câu affordance cho thao tác toggle của `logic.boolean_dag` | `PEDAGOGICAL_VISIBILITY_DEFECT` | chỉ chữ; **không** đổi cơ chế, không thêm capability |

Không mở việc thứ tư trong cùng đợt.

---

## 7. Khi nào được phép sửa UI sau này

**ĐƯỢC sửa khi:**

1. Sửa một trong ba việc ở §6.
2. Một mô phỏng **vi phạm** §1 hoặc §4 → kéo nó về đúng baseline.
3. Có **bằng chứng từ người dùng thật** (pilot, giáo viên rà) chỉ ra một chỗ gây
   hiểu nhầm hoặc không thao tác được — kèm ảnh/ghi chép, không phải cảm nhận.
4. Một **năng lực mới** cần một affordance mà baseline chưa có → bổ sung vào §2
   (tuỳ chọn) **trước**, chỉ nâng lên §1 (bắt buộc) khi ≥2 module cần.
5. Sửa lỗi accessibility có thể chứng minh (thiếu tên khả truy cập, thiếu thông
   báo đổi bước, màu là tín hiệu duy nhất).
6. Mở khe **Mục tiêu học tập / Nhiệm vụ** — **chỉ sau khi** target có neo chương
   trình thật qua `check_admission`.

**KHÔNG được sửa khi:**

1. "Cho đẹp hơn" mà không có ràng buộc học tập nào đằng sau.
2. Chỉ để một module trông khác các module còn lại.
3. Đổi vỏ chung để né một lỗi của **một** module.
4. Thêm chat/dashboard/gamification/LMS/đăng nhập/quản lý lớp — ngoài phạm vi
   đề tài.
5. Thêm module riêng cho mỗi bài học (ưu tiên: specialized có sẵn → generic DSL →
   năng lực tái sử dụng → từ chối trung thực).
6. Sửa production code chỉ để chụp được ảnh review.

**Luật cuối:** thay đổi UI **không** được đổi ai sở hữu sự thật. Engine tất định
giữ state/timeline/result; renderer giữ bố cục/camera; LLM không giữ gì trong
runtime. Một thay đổi giao diện làm lệch ranh giới đó là thay đổi **kiến trúc**,
phải đi qua `docs/ARCHITECTURE_MAP.md`, không đi qua file này.
