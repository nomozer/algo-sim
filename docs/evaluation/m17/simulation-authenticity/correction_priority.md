# Ưu tiên sửa — Simulation Authenticity Audit Part A

**Ngày:** 2026-07-27 · **Nguồn:** [simulation_authenticity_audit.md](simulation_authenticity_audit.md)
**Trạng thái:** đề xuất. **Chưa việc nào được thực hiện** trong checkpoint này.

Xếp hạng theo **mức thiệt hại cho luận văn**, không theo độ khó.

---

## P0 — `visual_mode` phản chứng chính tên đề tài

**Vấn đề.** Backend `CATALOG` khai `visual_mode = "2d"` cho **cả 22 target**, kể cả
`network.graph_traversal` và `network.protocol_encapsulation` — hai target thực sự
render 3D. Nguồn sự thật 3D nằm ở frontend `supportedVisualModes`
(`network/index.ts:100`, `network/encap.ts:42`).

**Vì sao P0.** Tên đề tài chứa "**2D/3D**". Bất kỳ bảng năng lực nào sinh từ field
backend sẽ ghi **3D = 0 / 22** và tự bác bỏ tên đề tài. Đây là lỗi *mô tả* — sản phẩm
vẫn render 3D đúng — nhưng nó khiến luận văn tự mâu thuẫn bằng chính dữ liệu của mình.

**Hướng sửa.** Cho backend đọc đúng khả năng 3D thay vì khai cứng `"2d"`, hoặc bỏ hẳn
field và chỉ dùng một nguồn sự thật. **Không** sửa bằng cách viết tay `"2d_3d"` vào hai
dòng — đó đúng **anti-pattern #1** (enum chép tay song song nguồn sự thật) mà kho mã
đã cấm.

**Nghiệm thu.** Bảng năng lực sinh tự động ghi đúng 2 target có 3D; có test khoá để
target 3D mới không lặng lẽ bị khai là 2D.

---

## P1a — W3 mượn hàm đổi cơ số nhưng bỏ qua cơ chế đổi cơ số

**Vấn đề.** `runCharacterEncoding` gọi thẳng `toBase(cp, 2)` và **bỏ qua
`buildConvSteps()` / `divideSteps()` nằm trong chính `convert-module.tsx` mà nó
import**. Dãy bit hiện ra như một **tuyên bố**, trong khi cơ chế dẫn ra nó đã tồn tại
sẵn cách đó vài chục dòng.

**Vì sao P1.** Đây là **khoảng cách duy nhất giữa REAL_SIMULATION và
PARTIAL_SIMULATION** trong toàn sản phẩm. Nó cũng là chỗ dễ bị hỏi nhất khi bảo vệ:
*"chỗ này mô phỏng cái gì?"* — hiện tại câu trả lời trung thực là "mô phỏng bước tra
mã; bước đổi cơ số thì hiện kết quả".

**Chi phí thấp bất thường.** Không phải viết cơ chế mới. `divideSteps` đã chạy, đã có
test, đã có ảnh RC1 (`binary-base-conversion-hex-mid-*`) chứng minh nó hiển thị được.
Việc cần làm là **nối**, không phải **xây**.

**Rủi ro phải cân.** Nối vào sẽ làm timeline dài thêm đáng kể (mỗi ký tự thêm ~n bước
chia). Với chuỗi 12 code point thì có thể quá dài. Cần một quyết định thiết kế: chỉ mở
chuỗi chia cho **ký tự đang xét**, hay cho ký tự đầu tiên như một ví dụ mẫu.
**Đây là quyết định của người dùng, không phải mặc định kỹ thuật.**

**Nghiệm thu.** Học sinh xem được chuỗi chia cho ít nhất một ký tự; không có bộ chuyển
đổi thứ hai ra đời; test hiện có (`rows[0].binary === toBase(65, 2)`) vẫn xanh.

---

## P1b — Ghi rõ `rule_scene` là PROGRESSIVE_VISUALIZATION

**Vấn đề.** `generic.rule_scene` là hé lộ dần, không phải mô phỏng. **Code hoàn toàn
trung thực** — registry đã tự khai `result_authority = REPRESENTATION`, family duy
nhất làm vậy. Rủi ro nằm ở **cách trích dẫn**.

**Vì sao P1.** Nếu luận văn đếm nó chung với 21 target còn lại như "mô phỏng thuật
toán", đó là **tuyên bố quá mức** — và là loại dễ bị bắt nhất, vì chính kho mã đã ghi
ngược lại.

**Hướng sửa.** Không sửa code. Sửa **cách mô tả**: tách bạch "mô phỏng cơ chế" (10
family, `computation`) khỏi "biểu diễn tiến triển" (1 family, `representation`) ở mọi
bảng đếm.

**Nghiệm thu.** Không bảng nào gộp 22 target thành một con số "mô phỏng" phẳng.

---

## P2 — Bề mặt tương tác đang thoái lui

**Vấn đề.** 6/15 target đại diện chỉ có `apply: (state) => state` — tua băng. Trong đó
có **cả hai năng lực mới nhất** (W2C, W3) và **`database.relational_table_query`**,
target có mô hình dữ liệu giàu nhất sản phẩm (5 cơ chế, pipeline thật) nhưng bề mặt
tương tác nghèo nhất.

Trong khi đó `logic` đã cho học sinh **bật/tắt đầu vào và xem hạ nguồn đổi theo** từ
rất sớm. Nghĩa là năng lực này **đã từng có**, và các module mới không kế thừa.

**Vì sao chỉ P2.** Tên đề tài nói "**tương tác**", và TIMELINE_CONTROL *vẫn là* tương
tác — nên đây không phải tuyên bố sai như P0/P1, mà là **cơ hội bỏ lỡ**.

**Ứng viên đáng giá nhất:** database (đổi ngưỡng lọc → xem pipeline chạy lại) và W2C
(đoán giá trị biến trước khi bước tiếp — đúng khuôn `predict` đã có sẵn ở `algorithm`).

---

## P3 — Hai cách chặn "kết quả nằm trong config"

**Vấn đề.** Luật R0 "spec không được mang kết quả" đang được thi hành bằng hai cơ chế:
`FORBIDDEN_SPEC_KEYS` tường minh (2 family mới) và schema chặt (các family cũ). Cả hai
đều **đang hoạt động đúng** — audit không tìm thấy chỗ rò.

**Vì sao P3.** Không có lỗi hiện tại. Nhưng khi thêm family thứ 12, không có chỗ nào
**bắt buộc** chọn một trong hai, nên dễ quên cả hai.

**Hướng sửa.** Một test conformance duyệt mọi family và yêu cầu bằng chứng có phòng
thủ — bất kể phòng thủ theo cách nào.

---

## Khuyến nghị bao trùm

> **Không mở family thứ 12 trước khi đóng P0 và P1.**

Thêm family làm tăng **bề rộng**; P0/P1 sửa **độ tin cậy**. Trong một luận văn, một
sản phẩm **11 family nói đúng về chính nó** phòng thủ được tốt hơn **12 family có một
chỗ nói quá** — vì hội đồng kiểm tra chiều sâu của vài chỗ, không đếm số family.

Thứ tự đề xuất: **P0 → P1b → P1a → (dừng, đánh giá lại) → P2.**
P0 và P1b rẻ. P1a cần một quyết định thiết kế về độ dài timeline.
