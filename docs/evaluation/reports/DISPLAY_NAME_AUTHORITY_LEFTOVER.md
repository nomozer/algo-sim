# DISPLAY_NAME_AUTHORITY_LEFTOVER — gỡ thẩm quyền đặt tên cuối cùng ở frontend

> Thực hiện **2026-09-03**. **0 lượt gọi model.** Không năng lực hình học mới,
> không đổi lược đồ model-facing, không đổi một con số nào, không đụng giao diện.

---

## 1. Hai vấn đề, một nguyên nhân

| | triệu chứng |
|---|---|
| **A** | `Scene3DExplorer` giữ hai bảng `producer → tiếng Việt` và `type → tiếng Việt`, tức **một thẩm quyền đặt tên thứ hai** nằm ở frontend |
| **B** | câu của vật này nhúng **nguyên tên** của vật kia: *"Giao tuyến của Mặt phẳng qua B và vuông góc với SC và (ABCD)"* — ba chữ "và", không tách được đâu là hết toán hạng thứ nhất |

Cùng gốc: hợp đồng cảnh chỉ có **hai** ô tên (`label`, `notation`), nên `label`
phải gánh cả ba vai — tên của vật, cách nhắc vật trong câu khác, và *"vật này là
gì"*. Thiếu ô thì phía dùng phải tự chế: frontend chế bằng một bảng dịch, còn
formatter chế bằng cách nhét cả câu vào câu.

Bảng ở frontend **sống sót qua chính wave G1** — wave dựng thẩm quyền tên ở
backend — vì lúc ấy không ai soi tới dòng vai trò của ô soi. Nó chỉ lộ ra ở G4:
thêm `plane_perpendicular_to_line` thì bảng không có khoá, và ô soi lặng lẽ tụt
xuống *"Mặt phẳng"* trong khi backend đã có sẵn câu đầy đủ. **Một bảng phải nhớ
cập nhật là một bảng sẽ quên.**

---

## 2. Bốn vai, bốn trường

`display_names.ten_hien_thi` nay trả bốn trường thay vì hai:

| trường | vai | vắng được? |
|---|---|:-:|
| `label` | **TÊN** của vật — tiêu đề, cây thành phần | không |
| `notation` | **KÝ HIỆU** toán, in cạnh vật trên khung | **có** (`None` hợp lệ) |
| `reference` | **CÁCH GỌI NGẮN** khi vật bị nhắc *trong câu của vật khác* hoặc trong một danh sách | không |
| `role` | *"vật này LÀ GÌ"* — một dòng dưới tên | không |

### Cách gọi ngắn dừng đệ quy ở một tầng

Cùng **một** bảng công thức (`_CACH_GOI`), hai bộ toán hạng — nên không có chỗ
cho hai bản lệch nhau:

```
label      toán hạng = ký hiệu, hoặc CÁCH GỌI NGẮN của nó   → bọc nếu nhiều chữ
reference  toán hạng = ký hiệu, hoặc DANH TỪ theo kiểu      → không bao giờ bọc
```

Vì `reference` chỉ nhúng ký hiệu hoặc danh từ, nó **không bao giờ là một câu**,
nên chuỗi lồng nhau dừng lại sau một tầng.

### Bọc bằng «…», không bằng ngoặc đơn

```
trước:  Giao tuyến của Mặt phẳng qua B và vuông góc với SC và (ABCD)
sau:    Giao tuyến của «Mặt phẳng qua B và vuông góc với SC» và (ABCD)
```

Ngoặc đơn đã mang nghĩa *mặt phẳng* trong ký hiệu hình học (`(ABC)`); mượn nó ở
đây là dựng nghĩa thứ hai cho cùng một dấu. Guillemet thì trống chỗ.

⚠️ **Contract là CẤU TRÚC, không phải cách hành văn.** Ca test khẳng định *"có
bọc, và bọc đúng một toán hạng"*, không khẳng định một câu tiếng Việt cụ thể.

### `role` không lặp lại tên

Khi tên vốn đã là câu mô tả (`Mặt phẳng qua B và vuông góc với SC`), vai trò lùi
về danh từ theo kiểu (`Mặt phẳng`) — hai dòng giống hệt nhau không thêm thông
tin, chỉ chiếm chỗ. Khi tên là một ký hiệu (`(ABC)`), vai trò nói phép dựng
(`Mặt phẳng qua A, B, C`). Hai dòng bổ sung nhau.

---

## 3. Frontend

| gỡ | thay bằng |
|---|---|
| `TU_PHEP_DUNG` — 13 khoá `producer → cụm tiếng Việt` | `o.role` |
| `VAI_TRO` — 9 khoá `type → tiếng Việt` | `o.role` |
| `moTaNgan(o, ten)` | — |
| `ten()` trả `label` | `ten()` trả `reference` |
| *"Dựa trên"* dùng `notation ?? label` | `reference ?? notation ?? label` |

**Gỡ, không đổi tên.** Chuyển bảng sang một file khác rồi gọi tên khác vẫn là
cùng một thẩm quyền nằm sai chỗ.

Frontend còn được: chọn giữa bốn trường · cắt chữ · bố cục · ẩn/hiện · đổi mức
chi tiết. Không còn được: dịch `producer`, dịch `type`, ghép quan hệ toán học,
đọc ngược `id`, suy kiểu.

---

## 4. Guard — khoá bất biến, không khoá tên biến

`semantic-dumb-frontend.test.ts` quét mọi `.ts/.tsx` không-test dưới
`domains/geometry` và `components/`, **bỏ chú thích**, rồi bắt hai dấu vết của
việc dịch:

1. một định danh máy (`construct_*`, `measure.*`, `intersect_*`, tên
   `MemoryType`…) nằm **cùng dòng** với một chuỗi có dấu tiếng Việt;
2. `producer` dùng làm khoá tra bảng, hoặc đem so với một hằng chuỗi để rẽ nhánh.

Đổi tên `TU_PHEP_DUNG` không đi lọt: guard tìm theo *hành vi*, không theo tên.

⚠️ **Chống dương tính giả.** Có một ca đối chứng khẳng định *"Dựa trên"*, *"Xem
cấu tạo"*, *"Thành phần"*, *"Bước sau"* vẫn còn trong mã. Chúng gọi tên **thao
tác của người dùng**, không gọi tên **khái niệm hình học**, và một guard cấm mọi
chữ tiếng Việt là một guard vô dụng.

**Đã chứng minh guard đỏ được**, không chỉ xanh: tiêm một bảng giả
`{"construct_point.midpoint": "Trung điểm của"}` vào `scene3d-presentation.ts` →
ĐỎ ngay, nêu đúng dòng; gỡ ra → xanh lại.

---

## 5. `producer` vẫn còn, và vẫn xem được

Điều bị cấm là **frontend dịch** nó, không phải sự tồn tại của nó. Chế độ chi
tiết vẫn hiện `Loại · Phép dựng · Dựa trên` với giá trị kỹ thuật thật — đo được
trong trình duyệt: `"Loại section · Phép dựng construct_section · Dựa trên chop,
sac"`.

Ca `test_producer_VAN_CON_cho_che_do_ky_thuat` đỏ nếu ai đó gỡ `producer` khỏi
cảnh để "cho sạch".

⚠️ **Thứ tự đo có ý nghĩa** trong `certify-display-authority.mjs`: quét định danh
máy **trước** khi bật chế độ chi tiết. Bật rồi thì `construct_section` hiện ra
hợp lệ, và quét sau sẽ đỏ oan.

---

## 6. Sửa hai con số của báo cáo G4 (§34)

`G4_CONSTRUCTION_EXPRESSIVENESS_BRIDGE` ghi *"+31 byte"* cạnh *"4400 → 4450"* —
hai con số không khớp về số học. Đo lại từ nguồn: thẻ đi từ **4364 → 4431**, tức
**+67**. `31` là phần vượt **trần cũ**, `4450` là **trần mới**; báo cáo lấy nhầm
số của cổng ngân sách làm số của hợp đồng.

Thêm một điều bản đầu không nói: cổng đo `grammar_card()` (đầy đủ, mọi miền),
còn thứ **thật sự gửi cho mô hình hình học** là `grammar_card("hinh_hoc")` —
3316 byte, nhỏ hơn 1115. Delta bằng nhau nên kết luận không đổi.

Đã sửa ở cả báo cáo lẫn chú thích trong `test_grammar_card.py`. **Không** đụng
artifact lịch sử.

---

## 7. Giới hạn còn lại, khai chính xác

`NESTED_DESCRIPTION_AMBIGUITY = CLOSED` — sự **mơ hồ** đã hết: toán hạng nhiều
chữ luôn được bọc, nên ranh giới đọc được bằng cấu trúc.

Nhưng câu vẫn **dài**, và đó là giới hạn khác, chưa đóng: một vật do `assign`
sinh ra không có ô nhãn trong IR, nên nếu mô hình muốn gọi nó là `(α)` thì hiện
không có chỗ để nói. Mở ô ấy là **đổi lược đồ model-facing** — ngoài phạm vi wave
này, và cần cân nhắc riêng vì nó bắt mô hình sinh thêm token.

Không tự đặt `π`, `α`, `d₁`: §6 cấm bịa ký hiệu, và một ký hiệu bịa cạnh một vật
là một mệnh đề sai về hình.

---

## 8. Phiên bản

**`CACHE_VERSION` 62 → 63.** Bắt buộc: envelope **thành công** đã cache mang
`SceneObject` **thiếu hai trường mới**, nên trả lại sẽ cho ra ô soi rỗng dòng
vai trò và *"Dựa trên"* lùi về `notation ?? label`. Đây đúng loại hồi quy câm mà
bump sinh ra để chặn — khác wave G3, nơi không envelope thành công nào đổi byte.

**`stable_capability_hash()` KHÔNG đổi**, và đó là kiểm chứng: nó băm `_CHU_KY`,
`_KIEU_DUNG`, `_TOAN_HANG_LENH`, `_KIEU_DO`, `MemoryType`, `GEOMETRY_CHECKERS`.
Wave này không chạm bảng nào trong sáu — nó đổi **cách gọi tên**, không đổi
**năng lực**.

---

## 9. Cổng

| cổng | kết quả |
|---|---|
| `pytest` | **2829 passed**, 1 skipped |
| `vitest` | **672 passed** (49 tệp) |
| `npm run build` | PASS |
| `replay_demo_cases.py` · `audit_demo_crash_surface.py` | 5/5 · 1/1 · 6/6, ném 0 |
| `certify-display-authority.mjs` | **8/8**, 0 lỗi bảng điều khiển |
| `certify-construction-bridge-g4` · `section-coplanar-edge` · `display-metadata` | 7/7 · 7/7 · 4/4 |
| `certify-journey-integration` · `offline-journey` · `refusal-surface` | 13/13 · 11/11 · 21/21 |
