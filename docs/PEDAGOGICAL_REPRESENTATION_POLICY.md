# CHÍNH SÁCH BIỂU DIỄN THEO PHÙ HỢP SƯ PHẠM (W4B-2S)

Baseline `1d0eba7`. Thay thế tiêu chí hẹp của W4B-2R. Tài liệu **hợp đồng +
bằng chứng**; số sống ở `docs/CURRENT_STATE.md`.

## 1. Luật cũ hẹp ở đâu

W4B-2R phán 3D bằng đúng một câu hỏi:

> *"Z có mã hoá một biến khái niệm không?"* → không thì 3D không chính đáng.

Câu đó **loại đúng target cần loại nhưng vì lý do sai**, và nếu giữ nguyên nó sẽ
loại nhầm về sau: một biểu diễn 3D có thể đáng giá vì giúp **nhận ra vật thể**,
**thấy quan hệ**, hoặc **thao tác dễ hơn**, dù Z không phải một biến của thuật
toán. `role: "pedagogical"` cũng chỉ là một **nhãn tự nhận** — chép nhãn vào là
qua cửa.

## 2. Luật mới: nêu ĐÍCH DANH tiêu chí

Một target chỉ được bày 3D cho học sinh khi khai được **`pedagogicalFit`** (3D
thắng ở tiêu chí nào) **và `whyNot2d`** (vì sao 2D không diễn đạt được). Thiếu
một trong hai ⇒ guard toàn danh mục chặn.

Tiêu chí (`PedagogicalFit` trong `simulations/types.ts`): `object_recognition` ·
`role_discrimination` · `relation_clarity` · `transition_clarity` ·
`direct_manipulation_fit` · `mechanism_fidelity` · `dimensional_value`.

Chủ sở hữu vẫn là **một** chỗ: `renderer.ts::representationPolicyOf` +
`representationPolicyProblems`. Không thêm cờ vào 22 module — chỉ target thật sự
có 3D mới phải khai.

## 3. Kết quả: 21 / 0 / 1 (không đổi con số, đổi LÝ DO)

### 3a. `network.protocol_encapsulation` → `2D_AND_3D_JUSTIFIED`

`pedagogicalFit: ["relation_clarity", "dimensional_value", "mechanism_fidelity"]`.
Cơ chế của bài là **LỒNG NHAU**: mỗi tầng bọc gói tin của tầng trên, tầng nhận
bóc ngược lại. Trên mặt phẳng, "bọc" phải quy ước hoá thành xếp chồng/thụt lề —
mượn một quy ước khác để nói chuyện chứa-đựng. Trong không gian, quan hệ
chứa-đựng **chính là** chiều sâu.

### 3b. `network.packet_routing` → `2D_ONLY` (giữ nguyên, lý do MỚI)

Chấm lại bằng 10 tiêu chí, không bằng câu hỏi "Z có phải biến không":

| tiêu chí | 3D so với 2D |
|---|---|
| object_recognition | **hoà** — hình laptop/router/tủ rack nhận ra được ở cả hai; 2D không bị phối cảnh làm méo |
| role_discrimination | **hoà** — đã giải quyết bằng từ vựng hình ở 2D |
| relation_clarity | **3D THUA** — topology là đồ thị; xoay là sinh che khuất nút sau nút |
| transition_clarity | **3D THUA nhẹ** — gói tin nhảy chặng đọc sạch trên mặt phẳng, 3D phải quản camera |
| direct_manipulation_fit | **3D THUA** — bấm vào liên kết ở 2D là bấm vào một đường; 3D thêm chọn theo chiều sâu |
| misconception_risk | **3D THUA** — phối cảnh làm độ dài/khoảng cách liên kết trông có nghĩa, trong khi topology phi-metric |
| visual_load | **3D THUA** — thêm điều khiển camera phải học |
| dimensional_value | **THẤP** — khả năng tới được trên đồ thị ≤ 8 nút không có chiều thứ ba; SGK vẽ topology phẳng |
| mechanism_fidelity | **hoà** |
| cost | **3D THUA** — thêm chunk Three.js + camera + picking, đổi lấy 0 tiêu chí thắng |

**3D không thắng một tiêu chí nào.** `2D_ONLY` đứng vững — nay bằng đo, không
bằng định nghĩa.

**Nhưng 2D thì PHẢI nâng cấp**, và đó mới là việc thật của wave này.

## 4. `DOMAIN_ROLE_CARRIED_BY_TEXT` — đo cả 22 target

| miền | vật thể chính | vai trò chở bằng | phán |
|---|---|---|---|
| **`network.packet_routing`** | `<circle>` cho cả 5 loại | **màu viền + chữ** | **HỎNG** |
| `graph_traversal` · `tree.traversal` | `<circle>` | đỉnh/nút vốn TRỪU TƯỢNG | đúng |
| 11 target mảng | cột/ô | giá trị vốn trừu tượng | đúng |
| `logic.and_gate` · `boolean_dag` | `<path>` hình cổng | hình | đúng |
| `database.relational_table_query` | `<table>` thật | cấu trúc | đúng |
| `protocol_encapsulation` | tầng/phong bì | cấu trúc | đúng |
| 3 target nhị phân | ô bit / trọng số vị trí | cấu trúc | đúng |

**Đúng MỘT target hỏng.** Đây là lý do wave này KHÔNG dựng "framework icon toàn
hệ": thay hình trừu tượng bằng tranh vẽ ở mảng/cây sẽ **làm hỏng** những chỗ
đang đúng. Ngữ pháp dùng chung là `OBJECT + ROLE + RELATION + TRANSITION +
PROGRESS`; **từ vựng hình thì theo miền**.

## 5. Đã sửa gì

Chủ sở hữu mới: **`domains/network/node-glyph.ts`** — `NodeType` (engine sở hữu)
→ hình. Laptop · router có ăng-ten · tủ rack có khe · switch nhiều cổng · đám mây
nhà mạng. Hàm thuần, **không màu** (màu thuộc renderer, hình thuộc vai trò), vẽ
tay bằng `path`, **không asset/không thư viện**.

`endpointRoleOf` tách **nguồn/đích** khỏi **loại thiết bị** — vì một mạng có thể
có hai máy chủ, glyph không phân biệt nổi. Đích có **vòng ngắm kép**; nguồn có
**cung phát**. Hình khác nhau, không chỉ khác màu.

Gói tin giữ hình **chấm tròn** ⇒ nay khác hẳn thiết bị (đều là `path`) — phân
biệt bằng HÌNH, không phải bằng màu.

## 6. Phép thử của chính lỗi

`semantic-roles-w4b2s.test.tsx` **xoá hết `<text>`** khỏi sân khấu rồi đòi vẫn
phân biệt được từng vai trò. Trước wave này, bỏ chữ đi thì còn lại năm vòng tròn
giống hệt.

Tiêm lỗi (4/4 ĐỎ, khôi phục XANH):

| lỗi tiêm | kết quả |
|---|---|
| thiết bị quay về cùng một `<circle>` (chính lỗi gốc) | **ĐỎ** (3 test) |
| hai vai trò dùng chung một hình | **ĐỎ** |
| bỏ dấu hiệu đích ⇒ đích chỉ còn chữ | **ĐỎ** |
| giữ 3D mà không khai `pedagogicalFit` | **ĐỎ** |

## 7. Sự thật vẫn thuộc engine

Không đổi một dòng nào của engine/`predict.check`/định tuyến. Renderer nhận
`NetNode.type` đã validate và tra bảng hình; nó **không** suy vai trò từ nhãn,
tiêu đề, đề bài hay thứ tự nút — có guard quét mã nguồn cho cả hai file. Ngắt
liên kết vẫn đi `net_disconnect` → `recompute` (BFS) → state mới → renderer đọc lại.

## 8. Giới hạn

- **3D của `packet_routing` KHÔNG được dựng lại.** Nếu sau này topology có ≥ 2
  tầng thật (vd mạng nhiều site/VLAN) thì đánh giá lại — điều kiện là khai được
  `pedagogicalFit`, không phải "cho có 3D".
- Dấu hiệu **nguồn** (cung phát) nhạt hơn dấu hiệu đích; chấp nhận được vì đích
  mới là thứ §14 đòi phân biệt, nhưng ghi nhận.
- 7 target vẫn `ENGINE_CONTRACT_MISSING` (`apply` = identity) — không bịa tương
  tác cho chúng.
- `tree.traversal`/`algorithm.scan` chưa có mẫu offline ⇒ vắng trong bộ ảnh;
  chính sách của chúng vẫn được guard toàn danh mục phủ (chạy trên registry).

## 9. Tuyên bố được phép

*"Chế độ hiển thị được chọn theo PHÙ HỢP SƯ PHẠM của cơ chế, không theo tính mới
lạ thị giác; mỗi miền dùng từ vựng hình của miền đó; renderer dẫn xuất từ state
tất định và không sở hữu kết quả; nơi có cả 2D lẫn 3D thì hai bên đọc cùng một
sự thật."*

**Không** được nói: 3D dạy tốt hơn · 3D trực quan hơn · học sinh học tốt hơn ·
biểu diễn giống thật thì tốt hơn. Giữ `LEARNER_IMPACT_NOT_EVALUATED`,
`CURRICULUM_SUPPORT_PARTIAL`.
