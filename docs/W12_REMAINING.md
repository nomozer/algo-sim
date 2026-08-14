# W12_REMAINING.md — hai việc còn lại, đủ chi tiết để thi hành ngay

> Trạng thái tại `1647af3` · cây sạch · pytest 1255 · vitest 1423 · build xanh.
> File này tồn tại vì hai việc dưới đây **không bắt đầu được bằng nửa phiên**:
> một cái cần dựng renderer mới, một cái cần nguồn dữ liệu ngoài kho mã.

## Đã đóng trong M20 W12

| việc | bằng chứng |
|---|---|
| quyền sở hữu cuộn của vỏ | `w12-scroll-shell.json` — 20/20 |
| affordance công cụ (Policy B) | `w12-viewport-matrix.json` — 92/92 |
| phân loại ngữ nghĩa | `w12-interaction-semantics.json` — 11 / 9 / 3, `PROBE_LIMITED` 0 |
| trải nghiệm (công cụ vs chỉ lộ dần) | `w12-experience-audit.json` — 19 TOOL · 4 TRACE · 0 FAIL |
| **sức nặng thị giác** | `w12-visual-weight.json` — **23/23 lấy hình làm chính** |
| bề mặt công cụ CSS dẫn từ đặc tả | `domains/web/prop-registry.test.ts` |
| `protocol_encapsulation` → 3D công khai | `representation-intent-w4b2v.test.ts` |
| lớp CSS không có luật | `styles/class-coverage.test.ts` (+ 10 nợ đóng băng) |

---

## VIỆC 0 — 3D PHẢI ĐỌC ĐƯỢC TRƯỚC KHI BÀY RA (bài học đắt, đọc trước)

Tôi đã chuyển `protocol_encapsulation` sang 3D công khai bằng **một lời khai**
và **không nhìn kết quả**. Trên màn thật: nhãn tầng chồng nhãn MÁY GỬI, chữ trên
khối PDU không đọc nổi, bốn phiến gần nằm ngang nên mất hẳn cảm giác BỌC NHAU —
tức mất đúng lí do 3D tồn tại. Đã **trả về 2D** (`a5faf03`).

**Cơ chế công tắc rẻ, nên dễ tưởng việc thiết kế cũng rẻ. Không phải.**

Nên MỌI việc 3D dưới đây có chung một điều kiện xuất xưởng:

1. `certify-visual-weight-w12.mjs` — vẫn HÌNH LÀ CHÍNH.
2. `certify-viewports-w12.mjs` — dùng được ở **cả bốn bề rộng**, gồm 768px.
3. **Nhãn không chồng nhau** ở góc máy mặc định — đo bằng bbox, không bằng cảm nhận.
4. Chữ nhỏ nhất trên cảnh ≥ 12px sau chiếu.
5. Quan hệ mà chiều sâu sinh ra để nói (bọc nhau / tuyến thay thế) **nhìn ra được**
   ở góc mặc định, không cần xoay.

Chưa qua đủ 5 điều kiện thì **giữ 2D**, đừng khai `primary: "3d"`.

## VIỆC 1 — `network.packet_routing` sang 3D sư phạm

**Vì sao.** Người dùng nêu bốn lần. Màn hiện tại là bốn biểu tượng đứng yên trên
một hàng ngang + một chấm hồng chạy; nó **đạt mọi tiêu chí W12** nhưng nhìn vào
thì đọc ra một hình minh hoạ có chú thích. Đóng gói TCP/IP đã chuyển 3D và ăn
điểm rõ (`inkShare` 60,2%); định tuyến thì chưa có renderer 3D nào.

**Điểm xuất phát.** `encap-ui3d.tsx` là bản mẫu DUY NHẤT trong kho — đọc nó
trước, đừng dựng từ đầu. `network/index.ts:158` đang khai `["2d"]`.

**Trục không gian phải khai rõ nghĩa** (đây là điều kiện, không phải gợi ý):

| trục | nghĩa |
|---|---|
| X | hướng truyền: nguồn → đích |
| Z (chiều sâu) | **tuyến thay thế** — mỗi tuyến một lớp sâu, để học sinh thấy "có đường khác" |
| Y | bậc thiết bị (máy · router · ISP · máy chủ) |

**Tương tác bắt buộc — không có nó thì KHÔNG bày 3D ra cho học sinh:**

```
học sinh chọn một liên kết trong 3D
  → phát net_disconnect { a, b }        ← hợp đồng CÓ SẴN, xem simulations/types.ts
  → module.apply
  → engine tính lại tuyến / khả năng tới được
  → cảnh 3D vẽ lại tuyến mới hoặc trạng thái "không tới được"
```

Hợp đồng action **đã tồn tại và đã chạy ở 2D** (`domains/network/ui.tsx`,
`LinkHandle`) — việc ở đây là bề mặt, không phải ngữ nghĩa mới.

**Bắt buộc kèm theo:**

- Mỗi liên kết bấm được bằng chuột phải có **đường bàn phím tương đương**
  (`role="button"` + `tabIndex` + Enter/Space) — 2D đã làm đúng, chép sang.
- 2D **giữ nguyên**, lùi về nội bộ đúng cách `protocol_encapsulation` vừa làm:
  `representation: { primary: "3d", alternate: "NO_ALTERNATE_NEEDED" }`.
  Cơ chế công tắc đã có sẵn ở `simulations/renderer.ts` — **một lời khai**, không
  phải hạ tầng mới.
- Parity nội bộ 2D↔3D: cùng config đã validate ⇒ cùng state, cùng con trỏ, cùng
  kết quả tất định. Bản mẫu: `network/render-parity.test.tsx`.

**Nghiệm thu** (chạy được, không phải mô tả):

1. `certify-visual-weight-w12.mjs` — `packet_routing` vẫn HÌNH LÀ CHÍNH.
2. `certify-viewports-w12.mjs` — 92/92 giữ nguyên, cảnh 3D dùng được ở cả 768px.
3. `certify-experience-w12.mjs` — vẫn nhận `net_disconnect`.
4. Kịch bản: tuyến A đang dùng → cắt một liên kết → engine trả tuyến B **hoặc**
   trạng thái không-tới-được → nối lại → tuyến cũ trở lại.

**Cạm bẫy đã biết:** `traverse-module.tsx` phục vụ `graph_traversal`, KHÔNG phục
vụ `packet_routing` — `makeNetworkModule()` mới là chủ sở hữu của target này.
Sửa nhầm file là chuyện đã xảy ra một lần trong wave này.

---

## VIỆC 2 — benchmark theo ĐƠN VỊ chương trình

**Chặn bởi dữ liệu, không phải bởi code.**

Benchmark hiện phủ **26 đề / 7 mã đơn vị**:
`T10.CD1 · T10.CD2 · T10.CD5 · T11.CD4 · T11CS.CD6 · T12.CD2 · T12.CD4`

Thứ còn thiếu là **danh sách mã đơn vị SGK có thẩm quyền** để biết 7 mã ấy là
bao nhiêu phần của tổng. Nguồn `/data/` bị gitignore và không có mặt.

⚠️ **KHÔNG tự chế mã đơn vị.** `COVERAGE.md §15` cấm, và việc này đã xảy ra một
lần ở W2 (`T11.CD_hinhhoc`) — chính guard `check_anchor` bắt được.

**Khi có danh sách, phần code không khó:**

1. Registry đơn vị ở `app/evaluation/curriculum_schema.py` (đã có `unit_codes` +
   `NOT_ANCHORED`).
2. Đơn vị chưa có năng lực ⇒ benchmark trả **`capability_gap`**, không phải vắng
   mặt — nhờ vậy thêm đặc tả mới thì ô tự chuyển xanh, **không phải viết test
   mới**. Đây là yêu cầu gốc của người dùng.
3. Guard cấm khai mã mới không kèm dẫn chứng kho mã.

---

## Điều đáng nhớ nhất từ wave này

Tôi viết 8 phép đo trong chuỗi phiên này; **6 cái sai ở lần chạy đầu**, và gần
như cái nào cũng **đánh giá THẤP sản phẩm**:

| sai | vì sao im lặng |
|---|---|
| so `st.cursor` (không tồn tại ở tầng store) | `undefined === undefined` ⇒ vòng lặp thoát ngay, vẫn trả số hợp lệ |
| đoán hình dạng `SimAction` | action sai bị `module.apply` **trả lại state cũ**, không ném lỗi |
| đoán tên action theo tên field config | như trên |
| chỉ đếm `<svg>` | mù với `<canvas>` (3D) và DOM thật (`.web-page`) |
| ngưỡng "≥8 bộ phận đồ hoạ" | đo **kích thước dữ liệu**, không đo chất lượng |
| chỉ đo `.sim-stage` | dải quan sát là **anh em** của nó, không nằm trong |

**Hệ quả cho người đọc sau: khi bản soát báo "có lỗi", nghi phép đo trước.**
Ghi lại ở `simulations/action-probe.ts` — ngay cạnh chỗ sẽ thêm target mới.
