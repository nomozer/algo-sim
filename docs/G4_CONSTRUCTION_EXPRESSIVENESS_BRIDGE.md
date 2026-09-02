# G4_CONSTRUCTION_EXPRESSIVENESS_BRIDGE — đóng G4

> Thực hiện **2026-09-03**. **0 lượt gọi model.** Thêm **một** biểu thức IR,
> không phải bốn — và số một ấy là kết quả của một cổng, không phải một sở
> thích.

---

## 1. Câu hỏi đặt đúng

`kernel.py` có bốn phép dựng dạng *"qua một điểm, song song/vuông góc với …"*,
cả bốn **0 lượt gọi** từ ngoài kernel. Câu hỏi **không** phải *"thêm bốn
primitive chứ?"* mà là, cho từng phép:

> IR hiện tại đã diễn đạt được nó chưa?

Hỏi bằng **chương trình chạy thật** — schema → thẩm định tĩnh → cổng xuất xứ →
interpreter → vị từ chính xác — chứ không bằng mắt. Đây là điều lượt soát kiến
trúc đã bỏ qua: nó thấy *"không có phép dựng trực tiếp"* rồi kết luận *"không
diễn đạt được"*, mà hai điều ấy khác nhau.

---

## 2. Bốn ứng viên, bốn câu trả lời

| # | hàm kernel | chữ ký | duy nhất? | diễn đạt được bằng IR cũ? | phân loại |
|:-:|---|---|:-:|:-:|---|
| 1 | `line_through_point_parallel_to` | `point + line → line` | ✅ | **CÓ** — 3 câu lệnh | `EXISTING_COMPOSITION` |
| 2 | `plane_through_point_parallel_to` | `point + plane → plane` | ✅ | **CÓ** — 5 câu lệnh | `EXISTING_COMPOSITION` |
| 3 | `plane_through_point_perpendicular_to` | `point + line → plane` | ✅ | **KHÔNG** | `FOUNDATIONAL_IR_EXTENSION` |
| 4 | `perpendicular_foot_line` | `point + plane → line` | ✅ | **CÓ** — 2 câu lệnh | `EXISTING_COMPOSITION` |

Không ứng viên nào `SEMANTICALLY_UNDERDETERMINED`: mỗi cặp toán hạng xác định
đúng một vật, không có tự do dư để kernel phải chọn bừa.

⚠️ Phép *"đường thẳng qua M vuông góc với đường d"* **không có trong kernel**, và
đó là đúng: trong không gian, những đường ấy nhiều vô hạn. Nó cũng không được
thêm.

### Ba witness — bằng chứng cho quyết định KHÔNG làm

```
① đường qua M ∥ d      v = vector_from_points(A, B)
                       N = translate(M, v)
                       construct_line(M, N)

② mặt qua M ∥ (ABC)    u = vector_from_points(A, B); w = vector_from_points(A, C)
                       N = translate(M, u); Q = translate(M, w)
                       construct_plane([M, N, Q])

④ đường qua M ⊥ (ABC)  H = project_onto(M, abc)
                       construct_line(M, H)
```

Cả ba qua **cổng xuất xứ** với đề chỉ nêu những điểm chúng dùng, chạy được, và
vị từ chính xác xác nhận. Chúng nằm ở
`tests/geometry/test_construction_bridge_g4.py::test_A*` — xoá đi thì lần sau ai
đó sẽ thêm ba primitive vì *"kernel có mà IR thiếu"*.

Thêm cửa riêng cho một phép đã nói được chính là cái bẫy `translate` từng suýt
rơi vào, nơi một tiện nghi bị gọi nhầm là năng lực mới.

---

## 3. Vì sao ③ thì khác — có chứng minh, không phải cảm giác

Không phải vì dài. Vì **không tồn tại** đường vòng.

**Bổ đề (kiểm bằng vét cạn).** Mọi phép sinh điểm của IR — `midpoint`,
`divide_segment`, `translate`, `project_onto`, ba phép `intersect_*` — **bảo
toàn bao affine** của các điểm đã khai.

Đề điển hình cho `A`, `B` (định nghĩa `d`) và `M`. Bao affine của chúng là mặt
phẳng `(ABM)`. Mặt phẳng qua `M` vuông góc `d` **không** nằm trong `(ABM)`; giao
của hai mặt ấy là một **ĐƯỜNG**. Nên mọi điểm lấy được của mặt phẳng cần dựng
đều **thẳng hàng**, và `construct_plane` — cần ba điểm không thẳng hàng — luôn
ném `COLLINEAR_POINTS`.

Đo được, không suy: **24** điểm sinh ở độ sâu 2 từ `{A, B, M}`, **0** điểm nằm
ngoài `(ABM)`.

**Lối thoát duy nhất bị cổng thứ hai chặn.** Khai thêm hai điểm phụ ngoài mặt
phẳng ấy thì dựng được — và `grounding_gate` từ chối đúng điều đó:

```
UNANCHORED_DERIVED_ASSUMPTION
X: không có trong đề bài. `model_assumption` chỉ nói về CÁCH ĐẶT một đối
   tượng đề đã nêu; một điểm suy ra phải được DỰNG…
```

Đó là chốt chống **rửa năng lực**, và nó đang làm đúng việc. Hai cổng vì thế
khoá chặt nhau: khoảng trống là **THẬT**, không phải "dài dòng".

Nếu một ngày grounding nới ra, ca
`test_B_loi_thoat_duy_nhat_bi_CONG_XUAT_XU_tu_choi` sẽ ĐỎ và quyết định thêm
primitive phải được xem lại.

---

## 4. Phần được thêm — tối thiểu

Một biểu thức, ở **đúng thẩm quyền chữ ký**:

```python
# ir_static_check._CHU_KY  — MỘT nguồn sự thật
"plane_perpendicular_to_line": ((("point", (DIEM,)), ("line", (DUONG,))), MAT),
```

Mọi thứ khác **dẫn xuất**, không viết tay lần thứ hai: lược đồ JSON, thẻ văn
phạm, `validator._BIEU_THUC_HINH_HOC`, xuất xứ ở `simulation_state`. Thêm một
dòng vào `display_names._CACH_GOI` để vật có tên tiếng Việt, và một nhánh
`eval_geometry_expr` gọi hàm kernel **đã có** — không viết lại phép toán nào.

Đặt ở `ValueExpr` chứ **không** ở `PointExpr`: nó trả `plane3`, và cho vào
`PointExpr` là nói với mô hình rằng `construct_point` nhận nó — nó sẽ thử.

R0 nguyên vẹn: hai trường đều là **TÊN**, cưỡng chế ở lược đồ.
`test_C_R0_toan_hang_chi_nhan_TEN` khoá lại.

---

## 5. Sau cầu nối

| | |
|---|---|
| dựng được với ĐÚNG những điểm đề cho | ✅ một câu lệnh, không điểm phụ nào |
| sai kiểu toán hạng bị bắt ở tầng **tĩnh** | ✅ trước runtime, nơi vòng sửa còn với tới |
| số chính xác | ✅ hữu tỉ vào ⇒ hữu tỉ ra; bài mẫu cho `5√6/3` |
| hợp thành xuôi dòng | ✅ mặt ⊥ đường → `intersect_plane_plane` → `project_onto` → `measure` |
| xuất xứ | ✅ `producer` · `depends` · kiểu khai · tên hiển thị |
| vết | ✅ một câu lệnh ⇒ một bước |
| cảnh 3D | ✅ **tuyến vẽ CŨ** (`surface`) — 0 loại vẽ mới |
| frontend | ✅ **0 dòng đổi**, 0 suy ngữ nghĩa thêm |

---

## 6. Điều KHÔNG làm

| | vì sao |
|---|---|
| Không thêm 3 primitive cho ①②④ | cổng hợp thành trả lời **CÓ** cho cả ba |
| Không thêm *"đường qua M ⊥ đường d"* | không xác định duy nhất trong không gian |
| Không thêm checker mới | `parallel`, `perpendicular`, `point_on_plane` đã đủ |
| Không thêm loại hình vẽ | `plane3` đã vẽ bằng `surface` |
| Không nhồi prompt | thẻ dẫn từ hợp đồng; **+67 byte**, đúng một từ vựng |
| Không đo độ phát hiện của mô hình | `MODEL_DISCOVERABILITY = NOT_MEASURED_THIS_WAVE` — wave này hỏi *hệ diễn đạt được gì*, không hỏi *mô hình có tìm ra không*. Đốt token cho câu thứ hai khi câu thứ nhất vừa đổi là đo một thứ sắp cũ |

---

## 7. Một chỗ đáng ghi, KHÔNG sửa ở wave này

`Scene3DExplorer.TU_PHEP_DUNG` — một bảng **producer → cụm tiếng Việt** ở
**frontend**, dùng cho dòng vai trò trong ô soi. Nó lặp lại đúng việc mà
`display_names._CACH_GOI` làm ở backend, tức là một **thẩm quyền tên thứ hai**,
đúng thứ G1 sinh ra để dẹp.

Nó **không** sai với phép mới: thiếu khoá thì nó lùi về mô tả theo kiểu
(*"Mặt phẳng"*) — truthful, chỉ nghèo hơn. Nên đây là nợ, không phải lỗi.

Cũng ghi luôn một giới hạn về **NHÃN LỒNG**: một vật do `assign` sinh ra không
có ô nhãn trong IR, nên tên của nó do formatter dựng; lồng câu ấy vào câu sau
cho ra *"Giao tuyến của Mặt phẳng qua B và vuông góc với SC và (ABCD)"* — đúng
ngữ nghĩa mà mơ hồ khi đọc. Bài mẫu vì thế dừng trước chỗ đó; chuỗi dài hơn nằm
trong test, nơi không cần đọc đẹp.

---

## 7b. SỬA HAI CON SỐ CỦA CHÍNH BÁO CÁO NÀY (2026-09-03)

Bản đầu ghi *"+31 byte"* cạnh *"4400 → 4450"*, và hai con số ấy không khớp nhau
về số học. Đo lại từ nguồn:

| | thẻ đầy đủ `grammar_card()` | thẻ miền hình học `grammar_card("hinh_hoc")` |
|---|---|---|
| trước G4 | 4364 byte | 3249 byte |
| sau G4 | 4431 byte | 3316 byte |
| **delta** | **+67** | **+67** |

`31` là **phần vượt trần cũ** (`4431 − 4400`), không phải mức tăng — báo cáo lấy
nhầm một con số của cổng ngân sách làm con số của hợp đồng. `4450` là **trần
mới**, cũng không phải kích thước.

Và một điều bản đầu không nói: cổng ngân sách đo `grammar_card()` (thẻ đầy đủ,
mọi miền), trong khi thứ **thật sự gửi cho mô hình hình học** là
`grammar_card("hinh_hoc")` — nhỏ hơn 1115 byte. Delta thì bằng nhau, nên kết
luận *"một từ vựng, không nhồi prompt"* không đổi.

---

## 8. Phiên bản

**`CACHE_VERSION` 61 → 62.** Bắt buộc: văn phạm **model-facing** đổi. Envelope
cache sinh dưới thẻ cũ đến từ một hệ **không nói nổi** mặt phẳng qua một điểm
vuông góc một đường — cùng lý do bump 58 và 59.

**`stable_capability_hash()` ĐỔI.** Nó băm `_CHU_KY`, và `_CHU_KY` có một chữ ký
mới. Đúng: đây là năng lực mới thật, khác hẳn wave G1/G2 (chỉ đổi cách gọi tên)
và G3 (chỉ sửa tính đúng).

Bảng danh tính ở `CURRENT_STATE.md`: **8 → 9 phép dựng**, dẫn từ thẩm quyền chứ
không gõ tay (`test_nang_luc_hinh_hoc_trong_bang_danh_tinh_khop_tham_quyen`).

---

## 9. Cổng

| cổng | kết quả |
|---|---|
| `pytest` | **2818 passed**, 1 skipped (+18 ca mới) |
| `vitest` | **668 passed** (48 tệp) — frontend không đổi một dòng |
| `npm run build` | PASS |
| `replay_demo_cases.py` · `audit_demo_crash_surface.py` | 5/5 · 1/1 · 6/6, ném 0 |
| `certify-construction-bridge-g4.mjs` | **7/7**, 0 lỗi bảng điều khiển |
| `certify-display-metadata` · `section-coplanar-edge` | 4/4 · 7/7 |
| `certify-journey-integration` · `offline-journey` · `refusal-surface` | 13/13 · 11/11 · 21/21 |

Bài mẫu offline mới **`mp-vuong-goc-duong`** — mặt phẳng qua `B` vuông góc `SC`,
rồi đo khoảng cách từ `S`. Cạnh bên **xiên** có chủ đích: mặt phẳng qua `B`
vuông góc cạnh **đứng** `SA` lại chính là mặt đáy, và đó là một ca suy biến chứ
không phải một bài.
