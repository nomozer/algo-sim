# Assumption Certificate Amendment (W15)

**Effective date:** 2026-10-03

**Authority:** registered in W15 Task 3, **before** `semantic_program/shape_constraint.py`
and `semantic_program/assumption_gate.py` exist and before any measurement. Code, census
and browser gates are judged against this text; a mismatch is a code or measurement
defect, never a reason to edit this registration.

**Verification state:** REGISTERED — not measured. The census verdict lives in
`docs/evaluation/geometry/runs/w15-assumption-closure/diagnostics/ASSUMPTION_MECHANISM_DECISION_W15.json`
once Task 5 has run.

Tài liệu này sửa đổi §3 của
[`GENERIC_GEOMETRY_FOUNDATION_PREREGISTRATION.md`](GENERIC_GEOMETRY_FOUNDATION_PREREGISTRATION.md)
(chính sách giả định — §3.4 "cơ chế ứng viên, phải đo, chưa chọn"). Nó không viết lại
lịch sử W14: kết luận W14 (`ASSUMPTION_POLICY_INCOMPLETE`, census
`ASSUMPTION_CENSUS.json` sha `32d0d9cf…`) giữ nguyên.

## 0. Vì sao có bản sửa đổi

W14 dừng Track B: AC2 0/18 có chứng chỉ, 11 phản ví dụ SAI trên hàng bất biến. W15
Task 1 đã kiểm từng nhận định bằng phép tính độc lập
([`TRACK_B_ROOT_CAUSE_TABLE`](../evaluation/geometry/runs/w15-assumption-closure/diagnostics/TRACK_B_ROOT_CAUSE_TABLE.md),
[`GOLD_ROW_VERIFICATION.json`](../evaluation/geometry/runs/w15-assumption-closure/diagnostics/GOLD_ROW_VERIFICATION.json)):
18/18 hàng AC2 được đề xác định và mọi đáp số bằng oracle; năm nguyên nhân gốc:

| RC | Tóm tắt | Hệ quả cho thiết kế |
|---|---|---|
| RC1 | C0 của W14 coi toạ độ đề cho là lớp C | tiền đề C0 = bất biến đọc từ đề cho CÙNG thực thể |
| RC2 | C1 của W14 xét quan hệ theo CHÚ THÍCH (`claimed`/`confirmed`) | chú thích không bao giờ là tiền đề; bộ đọc đề (U1) |
| RC3 | C1 = bộ nhận dạng compiler, hợp đồng demo không có quan hệ có kiểu | khuôn nhận từ KÝ HIỆU KHỐI trong đề |
| RC4 | phản ví dụ phá ràng buộc hình dạng đề nêu | kiểm hợp lệ trên MỌI ràng buộc đọc được |
| RC5 | nhân chứng AC1 dời một đỉnh nắp (phá lăng trụ) | DEPENDENT chỉ từ phép co giãn đúng chiều thiếu |

Cùng với F6–F11 của bảng ấy (hợp đồng demo cũ không lưu bất biến; bộ phát đọc cả NHÃN
của InputFact; bước con `section_edge`; giá trị số hiện ra ngoài nghĩa vụ; …).

Quyết định ràng buộc: W15-D1/D2/D3, U1 (bộ đọc ràng buộc từ đề), U2 (chờ người duyệt,
không tính lỗi), R1–R4 — nguyên văn ở
[`W15_SCOPE_DECISIONS.json`](../evaluation/geometry/runs/w15-assumption-closure/inputs/W15_SCOPE_DECISIONS.json).

## 1. Trạng thái, mã, và cái được chứng nhận

| Trạng thái | Khi nào | Route |
|---|---|---|
| `PROVEN_SAFE` | MỌI giá trị bị phủ có chứng chỉ C0 hoặc C1 | đi tiếp (các cổng khác vẫn có quyền nói không) |
| `DEPENDENT_ON_UNSTATED_ASSUMPTION` | §7: khuôn khớp + một kích thước bắt buộc không có trong đề + phép co giãn HỢP LỆ theo đúng kích thước ấy làm đổi một giá trị bị phủ | từ chối, `reason_code = ASSUMPTION_DETERMINES_ANSWER`, `reason_subjects` = kích thước thiếu |
| `UNDETERMINED` | mọi trường hợp còn lại | từ chối, `reason_code = ASSUMPTION_INVARIANCE_UNPROVEN` |
| `NOT_APPLICABLE_NO_NUMERIC_ANSWER` | không có giá trị số nào bị phủ | chỉ ghi nhận |

- Từ chối: `stage = "assumption"`, `ErrorCode.INPUT_NOT_GROUNDED`, `executable = True`
  (máy đã chạy xong bài; cái thiếu là bằng chứng), `servable = False`; hai mã thuộc
  `pipeline.KHONG_SUA_NGUON` — viết lại chương trình không thêm được dữ kiện vào đề.
- **Giá trị bị phủ** (F9): mọi giá trị số người học thấy — giá trị của MỌI bước
  `MEASUREMENT` trong trace và mọi witness của nghĩa vụ. Một giá trị không có chứng chỉ
  ⇒ từ chối CẢ bài. (Fixture (11) của W14 khai nghĩa vụ `angle_cos_sq` — không thuộc
  `OBLIGATION_KINDS` nên bị bỏ ở biên hợp đồng; `g` vẫn hiện cho người học.)
- Không bao giờ: gắn nhãn "giả thiết" rồi vẫn tính đáp số phụ thuộc nó (W15-D2); coi
  "từ chối tất cả" là xong (W15-D2); đổi đề/đáp án để chứng chỉ xanh.

API (khoá bởi test W14/W15): `assumption_gate.danh_gia_doc_lap(contract, spec) ->
KetQuaGiaDinh(status, certificate, reason_code, subjects, details, witness)` (cùng bước
bổ sung dựng hình + thực thi của route), `kiem_gia_dinh(...)` cho route,
`NGAN_SACH_CHAY_LAI`, `TOAN_HANG` + `kieu_ir_chua_phu()`.

## 2. Nguồn bằng chứng — CHỈ server, CHỈ từ câu đề

1. **Bất biến văn bản** — bốn bộ phát sẵn có, gọi với `contract=None` (F7: bộ phát đọc
   cả nhãn InputFact, tức một gắn thực thể do mô hình viết):
   `bat_bien_toa_do`, `bat_bien_mat_phang`, `bat_bien_do_dai`, `bat_bien_chia_doan`;
   cộng `grounding_gate.bang_chung_doan` cho độ dài của một đoạn cụ thể. Đọc LẠI lúc
   chạy cổng (F6: hợp đồng demo lưu trước khi có bộ phát).
2. **Ràng buộc hình dạng** — `shape_constraint.doc_rang_buoc(problem_text) ->
   tuple[RangBuoc, ...]`, `RangBuoc(kind, entities, value, span)`; entities là định danh
   thực thể (`dinh_danh_thuc_the`), `span` là `[đầu, cuối)` trong đề gốc. Từ vựng ĐÓNG
   (§2.1); lối viết ngoài từ vựng không phát gì.
3. **Không bao giờ là tiền đề**: `provenance` (`claimed`/`confirmed`/…), `source_fact_id`,
   `model_assumption`, `provenance=GIVEN`, quan hệ có kiểu, `solid_topology` của hợp đồng.
   Không cờ nào được nâng thành GIVEN; `claimed` vẫn là `claimed`.

### 2.1 Từ vựng đóng (thứ tự `entities` khoá ở `tests/geometry/test_shape_constraint.py`)

"Phần dữ kiện" = đề cắt tại chữ `Tính` đầu tiên. "Khối đã nêu" = khối DUY NHẤT có ký
hiệu trong phần dữ kiện.

| kind | Mẫu (ví dụ) | entities |
|---|---|---|
| `pyramid` | `hình chóp S.ABCD`, `khối chóp S.ABC` | (đỉnh, *đáy) |
| `prism` | `lăng trụ ABC.A'B'C'`, `hình hộp ABCD.A'B'C'D'` (đáy, nắp cùng số đỉnh) | (*đáy, *nắp) — tương ứng theo VỊ TRÍ |
| `right_prism` · `oblique_prism` · `cuboid` · `cube` | `lăng trụ đứng X.Y` · `lăng trụ xiên X.Y` · `hình hộp chữ nhật X.Y` · `hình lập phương X.Y` | như `prism` |
| `cube_edge` | `hình lập phương X.Y có cạnh bằng 4` | như `cube`; value = cạnh |
| `base_rectangle` · `base_square` · `base_parallelogram` · `base_rhombus` | `đáy ABCD là hình chữ nhật`; `đáy là hình vuông` gắn vào đáy của khối đã nêu; tên đáy khác đáy khối ⇒ không phát | (*đáy); `base_square` có value = cạnh khi viết `hình vuông cạnh 3` |
| `right_triangle` | `đáy ABC là tam giác vuông tại A`, `tam giác ABC vuông tại C` (đỉnh vuông phải thuộc tam giác) | (đỉnh vuông, hai đỉnh còn lại theo thứ tự đề) |
| `line_perp_plane` | `SA vuông góc với (mặt phẳng)? (ABC)`, `SA ⊥ (ABC)`, `SA vuông góc với (mặt phẳng)? đáy` (đáy của khối đã nêu; không có hoặc hai khối ⇒ không phát) | (P, Q, *mặt) |
| `line_perp_line` | `AB vuông góc với AD`, `AB ⊥ AD`, `góc BAD = 90°` | (P, Q, R, T); `góc YXZ` ⇒ (X, Y, X, Z) |
| `height` | `chiều cao bằng 7` gắn vào khối DUY NHẤT của phần dữ kiện | entities của khối (hoặc `()` nếu khối không tên); value |
| khối không tên | phần dữ kiện nhắc đúng MỘT khối và không có ký hiệu khối: `lăng trụ đứng có đáy là hình vuông cạnh 3, chiều cao bằng 7` ⇒ `right_prism ()`, `base_square ()=3`, `height ()=7` | `()` — cổng gắn vào khối DUY NHẤT của chương trình |

Ngoài từ vựng (ví dụ, không phát gì): `SA là đường cao`, `AB và AD tạo với nhau một góc
vuông`, `đáy có bốn góc vuông`, `các cạnh bên vuông góc với mặt đáy`, chia đoạn viết
`thuộc cạnh SB` (bộ phát chia đoạn chưa đọc — §8).

> **Đính chính 2026-10-03 (W15 Task 6, quyết định U4 · G1).** Nối cổng vào route làm đỏ sáu
> test mà đề viết góc vuông của đáy theo lối thường gặp ngoài bảng trên — `đáy ABC vuông tại
> A` (không có "là tam giác"), `tam giác vuông đỉnh G`, `tam giác vuông ở đỉnh E`. Dòng
> `right_triangle` nay nhận thêm: `đáy XYZ vuông (cân)? <tại> X` và `tam giác … vuông (cân)?
> <tại> X` với `<tại>` ∈ {`tại`, `ở đỉnh`, `ở`, `đỉnh`}; vẫn chỉ khi đỉnh vuông thuộc tam giác
> có tên (đáy tứ giác `đáy ABCD vuông tại A` không phát). `cân` vẫn là thông tin span nuốt mà
> không phát — luật đọc trọn §7 chặn DEPENDENT. Khoá: `test_shape_constraint.py`
> (`test_goc_vuong_cua_day_moi_loi_viet_gan_dung_dinh`, `test_goc_vuong_sai_thuc_the_khong_phat`).

### 2.2 Bốn trạng thái bằng chứng của một quan hệ của mô hình

Mỗi quan hệ có kiểu của hợp đồng được ghi một trạng thái trong `details`
(`RELATION <kind>(<entities>): <state> [by <RangBuoc> @[a,b]]`):

| Trạng thái | Nghĩa |
|---|---|
| `UNCONFIRMED` | server không đọc thấy gì, theo chiều nào cũng không — `claimed` chỉ nghĩa là "bộ trích giá trị chưa xác nhận", KHÔNG nghĩa là "đề không nói" |
| `REFUTED_BY_SOURCE` | server đọc thấy điều trái ngược — danh sách đóng: `oblique_prism` ↔ cạnh bên ⊥ đáy; `right_triangle` vuông tại đỉnh khác ↔ vuông góc tại một đỉnh của cùng tam giác; độ dài đề cho ≠ độ dài chương trình dựng (`SOURCE_EVIDENCE_CONFLICT`) |
| `MODEL_ASSUMPTION` | hợp đồng tự gắn cờ giả định |
| `SERVER_CONFIRMED` | một `RangBuoc` cùng kind, cùng thực thể, cùng phạm vi (cùng khối/mặt) |

Chỉ `RangBuoc` của server là tiền đề; quan hệ của mô hình chỉ được BÁO trạng thái. Một
chương trình hiện thực một quan hệ `REFUTED_BY_SOURCE` không được chứng nhận (detail
`RELATION_REFUTED_BY_SOURCE`). Không có quyền phủ quyết theo chú thích (bỏ ý "claimed ⇒
veto" của W14).

## 3. Lát cắt và định nghĩa với tới (R3)

- **Lát cắt** của một giá trị bị phủ đi theo `TOAN_HANG` (kind IR → các trường mang TÊN).
  `kieu_ir_chua_phu()` so bảng với lược đồ `contract.py`: thiếu một kind/trường ⇒ khác
  rỗng (test khoá). Gặp kind/trường ngoài bảng lúc chạy ⇒ `CLOSURE_INCOMPLETE` ⇒
  `UNDETERMINED`.
- **Một định nghĩa với tới duy nhất**: mỗi tên trong lát cắt có đúng MỘT thể hiện câu
  lệnh định nghĩa nó (khai báo có `initial_value` cũng là một định nghĩa). Các bước con
  của CÙNG một câu lệnh là một thể hiện — danh sách đóng: chuỗi bước `section_edge` khép
  bởi bước `construct_section` cùng `target` (F8). Ghi lần hai bất kỳ (ghi đè trước phép
  đo, khôi phục sau, gán lại, vòng lặp) ⇒ `CLOSURE_MULTIPLE_DEFINITIONS` ⇒ `UNDETERMINED`
  ngay, không chạy phản ví dụ. Bí danh (`assign B = var A`) là định nghĩa của B, đọc
  định nghĩa DUY NHẤT của A.
- **Giá trị đọc tại lúc định nghĩa**: từ `memory_snapshot` của bước định nghĩa (khai báo:
  giá trị khởi tạo), không bao giờ từ `final_memory`.
- Không xử lý được (container, bước không `target`, không định danh được thể hiện câu
  lệnh) ⇒ `UNDETERMINED`.

## 4. Vai trò và nguồn của mọi literal trên lát cắt (R1)

| Vai trò | Literal | Điều kiện (chỉ bằng chứng §2) | Dùng ở |
|---|---|---|---|
| `SOURCE_DATUM` | toạ độ một điểm | `point_coordinate` cho CÙNG điểm, CÙNG bộ ba | C0, C1 |
| | hệ số `construct_plane_from_equation` | tỉ lệ với một `plane_equation` của đề | C0, C1 |
| | vô hướng khai báo `XY_length` | `bang_chung_doan(đề, (X, Y), giá trị)` — đề nói độ dài CHÍNH đoạn XY bằng giá trị ấy | C0, C1 |
| | tỉ số `divide_segment(a, b, t)` tạo M | `segment_division` (A, B, M) của đề cho CÙNG M, `{a, b} = {A, B}`, cùng `t` theo chiều | C0, C1 |
| `FORMULA_COEFFICIENT` | — | **RỖNG ở W15**: `arith` của IR chỉ có `+ − * // %` và literal `"1/3"` là CHUỖI, nên không công thức hệ số hữu tỉ nào biểu diễn được; hằng số công thức nằm trong `measure` của kernel | — |
| `LAYOUT_FRONTIER` | toạ độ một đỉnh khuôn | đỉnh nằm trong ký hiệu khối của đề (hoặc khối không tên); giá trị tại lúc định nghĩa thoả MỌI ràng buộc ánh xạ (§6) | chỉ C1 |

Literal khác — tỉ số, góc, vị trí mặt phẳng, hệ số do mô hình chọn, kể cả khi không thứ
nguyên và chỉ đi qua phép dựng không phụ thuộc khung — **không vai trò ⇒ không chứng
chỉ**. Phân tích thứ nguyên là điều kiện cần, không bao giờ đủ.

> **Đính chính 2026-10-03 (W15 Task 6, quyết định U4 · G2).** "CÙNG điểm" / "đỉnh nằm trong
> ký hiệu khối" so tên phía chương trình (hay hợp đồng) với thực thể của đề qua
> `domain_profile.geometry_symbol_key` — thẩm quyền có sẵn gộp bốn lối viết một điểm bậc một
> đo được ở lượt sinh thật: `A′` ≡ `A1` ≡ `A_prime` ≡ `Aprime`. Một phép dò cho thấy chương
> trình hộp chữ nhật ĐÚNG viết đỉnh nắp là `A1`/`Aprime` bị từ chối (`T4 TEMPLATE_VERTEX_
> MISSING`). Khoá mà hai tên chương trình cùng mang (vd `A` và `A_`) — hoặc hai đỉnh của
> khối trong đề cùng mang — thì không gắn: không đoán tên nào là điểm nào (đóng an toàn).
> Vô hướng `XY_length` vẫn theo `bang_chung_doan` như grounding (chỉ lối viết `_prime`):
> hai thẩm quyền không được lệch nhau.

## 5. C0 — lát cắt ghim bởi nguồn

Mọi literal trên lát cắt của mọi giá trị bị phủ là `SOURCE_DATUM`; mọi giá trị ghim
(đọc tại lúc định nghĩa) bằng bất biến của đề. Phép đo: bất kỳ phép `measure` nào của
kernel (thể tích, diện tích, khoảng cách, góc, cos², diện tích xung quanh, …), và `arith`
`+ − *` giữa các giá trị đã phủ (không literal).

## 6. C1 — cấu hình do đề xác định

**6.1 Nhận khuôn.** Đỉnh khuôn lấy từ KÝ HIỆU KHỐI trong đề (`pyramid`/`prism` + kiểu)
— không từ `construct_solid` của chương trình (t3/t4/n2 không dựng khối nào). Khối không
tên: gắn vào khối DUY NHẤT của chương trình qua mọi cách đọc
`solid_faces.phan_loai_bang_mat`; nhận khi có một cách đọc thoả MỌI ràng buộc không tên.
Mọi đỉnh khuôn phải có trong chương trình, mỗi đỉnh một định nghĩa.

**6.2 Bảng xác định (đóng).** Ràng buộc ánh xạ = các `RangBuoc` + độ dài đề cho của các
cạnh khuôn; kiểm CHÍNH XÁC trên giá trị đỉnh tại lúc định nghĩa.

| Khuôn | Ràng buộc cấu trúc | Kích thước BẮT BUỘC (đề phải cho) | Vì sao duy nhất (sai khác một phép đẳng cự) |
|---|---|---|---|
| T1 chóp đáy tam giác vuông | `pyramid S.XYZ`, `right_triangle` tại X ∈ đáy, `line_perp_plane(S, X, đáy)` | XY, XZ, SX (hoặc `height`) | tam giác vuông xác định bởi hai cạnh góc vuông (c.g.c); S nằm trên pháp tuyến tại X, cách X đúng SX — hai vị trí đối xứng qua mặt đáy |
| T2 chóp đáy chữ nhật/vuông | `pyramid S.ABCD`, `base_rectangle`/`base_square`, hoặc `base_parallelogram` + `line_perp_line` tại một đỉnh đáy (hình bình hành có một góc vuông là hình chữ nhật); `line_perp_plane(S, X, đáy)` với X ∈ đáy | hai cạnh kề tại X (vuông: một cạnh), SX (hoặc `height`) | hình chữ nhật xác định bởi hai cạnh kề; S như T1 |
| T3 lăng trụ đứng đáy tam giác vuông | `prism` + `right_prism`, `right_triangle` tại một đỉnh đáy | hai cạnh góc vuông, một cạnh bên (hoặc `height`) | đáy như T1; nắp = đáy + t, t ⊥ đáy, \|t\| = cạnh bên — hai hướng ±t đối xứng |
| T4 hình hộp chữ nhật | `prism` + `cuboid` | một độ dài cho mỗi phương cạnh (ba lớp cạnh song song) | khối hộp xác định bởi ba cạnh tại một đỉnh |
| T5 lập phương | `prism` + `cube` | một cạnh (`cube_edge` hoặc độ dài một cạnh bất kỳ) | cùng lập luận, ba cạnh bằng nhau |
| T6 lăng trụ đứng đáy vuông | `prism` + `right_prism` + `base_square` (có tên hoặc không tên) | cạnh đáy, cạnh bên (hoặc `height`) | đáy vuông xác định bởi cạnh; nắp như T3 |

"Góc vuông tại X" (T1, T3) đọc từ `right_triangle` tại X **hoặc** `line_perp_line(X, Y,
X, Z)` với Y, Z là hai đỉnh đáy còn lại (`góc YXZ = 90°`, `XY ⊥ XZ`).
Mọi ràng buộc đề nêu cho các đỉnh khuôn (kể cả ràng buộc ngoài cột "cấu trúc") đều
phải thoả. Mỗi `RangBuoc` dùng làm tiền đề được ghi vào `details` dạng
`PREMISE <kind>(<entities>)[=<value>] @[<đầu>,<cuối>]` — tiền đề của chứng chỉ truy được về
đúng cụm chữ trong đề, không bao giờ về một InputFact. Quan hệ ngầm định của kiểu: lăng trụ ⇒ các cạnh bên là MỘT phép tịnh tiến;
đứng ⇒ cạnh bên ⊥ đáy; hình hộp chữ nhật ⇒ đáy chữ nhật + đứng; lập phương ⇒ hộp chữ
nhật + mọi cạnh bằng nhau; hình vuông ⇒ chữ nhật + hai cạnh kề bằng nhau.

**6.3 Lát cắt cho phép.** Đỉnh khuôn (biên), phép dựng không phụ thuộc khung trên chúng
(trung điểm; `divide_segment` có tỉ số `SOURCE_DATUM`; giao; hình chiếu; tịnh tiến theo
`vector_from_points`; đường/mặt qua điểm của lát cắt; đa giác/khối/thiết diện trên vật
của lát cắt; bí danh), và literal có vai trò. Phụ thuộc khung — mặt phẳng từ phương
trình, vectơ có thành phần literal, điểm literal ngoài khuôn — ⇒ không C1.

**6.4 Phép đo trong C1:** thể tích, diện tích, khoảng cách, và `arith` `+ − *` giữa giá
trị đã phủ (không literal). **Ngoài C1:** góc và cos² (W14 test (11) giữ nguyên), `//`,
`%`, mọi literal số học.

**6.5 Đối chiếu độc lập.** Khi hợp đồng là dạng compiler nhận được
(`danh_gia_eligibility` = `SUPPORTED`), bình phương khoảng cách từng cặp đỉnh khuôn của
ứng viên phải bằng của chương trình tham chiếu `compiler.bien_dich`; lệch ⇒ `UNDETERMINED`
+ detail `C1_CROSS_CHECK_DISAGREES` (báo động: hai thẩm quyền bất đồng). Lượt chạy tham
chiếu tính vào `NGAN_SACH_CHAY_LAI`.

> **Đính chính 2026-10-03 (W15 Task 5, trước census).** Câu trên không làm được trên đường
> sản phẩm: bất biến có từ trước `test_structured_geometry_relations::test_Y` cấm mọi tệp
> sản phẩm ngoài gói compiler tham chiếu gói ấy (`DEFAULT_MODE = LLM_ONLY`, compiler CÓ
> nhưng CHƯA BẬT). Thực chất giữ nguyên, cơ chế đổi: cổng dựng một **hiện thực chính tắc**
> của khuôn từ kích thước đề cho (không từ toạ độ ứng viên), đặt lại literal của các đỉnh
> khuôn theo nó, **chạy lại chính chương trình** và đòi mọi giá trị bị phủ TRÙNG KHÍT; lệch
> ⇒ `UNDETERMINED` + `C1_CROSS_CHECK_DISAGREES`. Áp cho MỌI hàng C1 (không chỉ hợp đồng
> compiler nhận), lượt chạy lại tính vào `NGAN_SACH_CHAY_LAI`. So với compiler chuyển sang
> census W15 (chẩn đoán): mỗi hàng C1 compiler nhận được ghi `AGREES`/`DISAGREES`. Cái giá:
> hiện thực chính tắc dùng chung bảng khuôn với phép kiểm ràng buộc — độc lập yếu hơn
> compiler; census bù bằng phép so ấy.

## 7. Phản ví dụ — DEPENDENT chỉ từ một kích thước thiếu có thật

- Chỉ khi một khuôn §6.2 khớp trên ràng buộc ĐỌC ĐƯỢC và một kích thước BẮT BUỘC không
  có trong đề. (F4/F11: phản ví dụ sai sinh ra khi phép biến dạng giữ ràng buộc đọc được
  nhưng phá ràng buộc không đọc được; gắn DEPENDENT với một đọc cấu trúc dương tính là
  cách đóng lớp lỗi ấy.)
- Phép biến dạng: co giãn ×2 theo ĐÚNG phương của kích thước thiếu, neo tại đỉnh khuôn
  của nó (chiều cao/cạnh bên: theo pháp tuyến đáy, tính từ các đỉnh — bền với phép quay;
  cạnh đáy: theo phương cạnh ấy; lập phương thiếu cạnh: phép vị tự ×2), áp lên MỌI
  literal điểm không phải `SOURCE_DATUM`; điểm dẫn xuất đi theo khi chạy lại.
- Hợp lệ khi và chỉ khi: chạy được; mọi bất biến văn bản (§2.1) và mọi `RangBuoc` đều
  thoả CHÍNH XÁC trên cấu hình mới; `source_invariants` đã lưu của hợp đồng thoả; hậu
  điều kiện thoả.
- Hợp lệ và một giá trị bị phủ đổi ⇒ `DEPENDENT`, `subjects` = kích thước thiếu theo nhãn
  thực thể (cạnh đại diện: `AD`, `SA`, `AA′`, …).
- Ngoại lệ, hết `NGAN_SACH_CHAY_LAI`, cấu hình suy biến ⇒ không kết luận — không bao giờ là
  phản ví dụ, không bao giờ là an toàn.
- **Phán quyết:** nhiều định nghĩa ⇒ `UNDETERMINED`; C0 hoặc C1 ⇒ `PROVEN_SAFE`; phản ví
  dụ hợp lệ ⇒ `DEPENDENT`; còn lại ⇒ `UNDETERMINED`.

> **Đính chính 2026-10-03 (W15 Task 6, sau census vòng 1, trước khi nối route).** Luật hợp
> lệ ở trên chỉ kiểm cái server ĐỌC ĐƯỢC, nên nó chưa đủ để nói "đề không cho": một phép dò
> tìm ra hai lỗ, cả hai đều cho `DEPENDENT` trên chương trình ĐÚNG mà corpus đăng ký không
> có hàng nào thuộc lớp ấy (`diagnostics/logs/RED_UNREAD_TEXT.log`).
> (i) Đề cho kích thước thiếu bằng một câu NGOÀI từ vựng — `góc giữa SB và mặt phẳng đáy
> bằng 45°`, `SA = AB`, `tam giác SAB vuông cân tại A`, `SB = 3√2` — phép kéo phá câu ấy mà
> không ai kiểm. (ii) Một `RangBuoc` đọc được nhưng KHÔNG là tiền đề của khuôn (`AC ⊥ BD`
> trên đáy chữ nhật ⇒ hình vuông) không được kiểm trên nhân chứng, trái câu "mọi `RangBuoc`
> đều thoả" ở trên. Luật bổ sung, áp TRƯỚC mọi phép kéo: phản ví dụ chỉ được thử khi
> `shape_constraint.phan_chua_doc` rỗng — phần dữ kiện (trước `Tính`) sau khi xoá span của
> bộ đọc và câu độ dài số (`segment_relation.MAU_DO_DAI`) chỉ còn từ nối `cho · có · và ·
> cạnh · bên`, không span nào nuốt thông tin nó bỏ (`đều`, `cân`, cạnh của đáy không vuông)
> — VÀ mọi `RangBuoc` của đề nằm trong tiền đề của khuôn. Không thoả ⇒ `UNDETERMINED`
> (detail `CE_TEXT_NOT_FULLY_READ` / `CE_CONSTRAINT_NOT_CHECKED`): vẫn từ chối, lời "chưa
> chứng minh", không bao giờ nêu một kích thước đề thực ra đã cho. `PROVEN_SAFE` không đổi:
> tiền đề C0/C1 là tập con của đề, câu đề thêm chỉ thu hẹp cấu hình. Census chạy lại trên
> cổng đã sửa (vòng 2) cùng lớp bổ sung `assumption_corpus_w15b`.

## 8. Phạm vi chứng nhận

**Được chứng nhận:** sáu họ khi đề cho đủ kích thước (T1–T6); bài cho toạ độ (C0), kể cả
khối cong dựng từ điểm đề cho (p4–p7) và thiết diện có mặt phẳng đề cho bằng phương trình.

**Không chứng nhận — từ chối `UNDETERMINED`:** khối cong hoặc khối đều không toạ độ; góc
dưới C1; lối viết ngoài từ vựng (kể cả chia đoạn viết `thuộc cạnh XY` — bộ phát chia đoạn
chưa đọc, một chương trình đúng tỉ số theo lối viết ấy cũng bị từ chối, là giới hạn độ
phủ); tham số đề không nêu; literal số học; công thức có hệ số; câu trả lời không phải số
(`NOT_APPLICABLE`, không thuộc phạm vi W15).

## 9. Luật SHIP (đăng ký trước; census chạy TRƯỚC khi nối route)

Trên corpus W14 (giữ nguyên byte) + corpus W15 (`assumption_corpus_w15/`):

- (a) 0 `PROVEN_SAFE` trên hàng `DEPENDS` hoặc `MUST_REFUSE`;
- (b) mọi hàng `AC1`/`ADVERSARIAL`/`DEPENDS`/`MUST_REFUSE` bị từ chối;
- (c) 0 `DEPENDENT_ON_UNSTATED_ASSUMPTION` trên hàng `INVARIANT` (không phản ví dụ sai);
- (d) 18/18 hàng AC2 của W14 `PROVEN_SAFE`, trừ hàng có đính chính toán học ở lớp mới
  (Task 1: không có);
- (e) route: danh sách GUARD của W14 (sáu họ + gold p1, p2, p4–p7) và bốn demo PASS (n1,
  n2, t3, t4) được phục vụ;
- (f) test metamorphic xanh.

Không đạt ⇒ `ASSUMPTION_POLICY_INCOMPLETE`, không nối route. Báo cáo (không gác): hàng
W15 `INVARIANT` có kỳ vọng `PROVEN_SAFE` mà không đạt. Lời tuyên bố được phép: "0 vi
phạm trên corpus đã đo, trong phạm vi chứng chỉ" — không phải chứng minh tổng quát.

## 10. U2 — kết luận khuất/hiện cho bốn cảnh W14 làm đổi

Bốn cảnh có kỳ vọng người không chuyển được (`SCENE_GEOMETRY_CHANGED`) được ghi
`HUMAN_REVIEW_PENDING`, **không** tính lỗi, khi và chỉ khi: sản phẩm khớp oracle ở mọi
trạng thái, và chẩn đoán chuyển giao tái tạo đúng tập đã duyệt. Bất kỳ
`REVIEWED_SETS_DIFFER` hay sản phẩm ≠ oracle là lỗi. Registry kỳ vọng người không đổi;
không bao giờ ghi `APPROVED_BY_USER` (W15-D3).

## 11. Tô thiết diện — ngưỡng đăng ký TRƯỚC mọi phép đo

```text
SECTION_FILL_THRESHOLDS = {"T_ON": 20, "T_ON_MIN": 12, "T_OFF": 3, "margin_px": 3}
```

- **Phép đo** (`SECTION_FILL_DISTINGUISHABLE`): cùng khung, cùng camera, cùng trạng thái
  hình; chụp khi tô BẬT, gọi `window.__geo3d_set_section_fill_visible(false)`, chụp lại;
  mẫu = điểm ảnh bên trong đa giác thiết diện CUỐI chiếu bằng camera đã ghi, bỏ một lề
  `margin_px` quanh MỌI cạnh và dấu điểm đã chiếu; ΔE76 (CIE76, sRGB D65) từng mẫu.
- **Bước khép-và-tô:** trung bình ≥ `T_ON` và từng mẫu ≥ `T_ON_MIN` (bắt tô thiếu/quá nhạt).
- **Mọi bước trước khi khép** (từ bước có mặt cắt) và **sau khi tua ngược** khỏi bước
  khép: max ≤ `T_OFF` (bắt tô hiện sớm, tô không mất khi tua ngược).
- Không mẫu nào, hoặc bước khép không có vật tô để bật/tắt ⇒ trượt.
- **Vì sao những con số này** (mô hình phối màu "over" trên sRGB của cảnh: nền trắng, mặt
  sau khối xám `#64748b` 0.22, mặt cắt tím `#7c3aed` 0.2, mặt trước khối 0.22; mức sáng
  0.55–1): renderer CŨ (hổ phách `#f59e0b` 0.16 nằm DƯỚI mặt cắt và mặt trước) cho
  ΔE76 6.6–9.0; tô vẽ SAU CÙNG ở 0.45 cho ≥ 31.9. Ngưỡng nhận biết ≈ 2.3: `T_ON_MIN` ≈ 5×,
  `T_ON` ≈ 9×; `T_OFF` ≈ 1.3× để chịu nhiễu khử răng cưa bên trong mẫu.
- Không bao giờ chỉnh theo ảnh sản phẩm: sản phẩm trượt ⇒ đổi hằng độ đục của sản phẩm,
  không đổi ngưỡng. Khoá: test node đối chiếu `NGUONG_TO_THIET_DIEN` trong
  `compiler-scene-replay-lib.mjs` với dòng trên.

## 12. Không được

Nới cổng grounding; nâng chú thích của mô hình thành tiền đề hay GIVEN; dùng
`FIXTURE_TIN_CAY` ngoài fixture đã kiểm kê; sửa đề hoặc đáp án để chứng chỉ xanh; đổi bề
mặt mô hình (prompt, lược đồ, thẻ văn phạm, bảng năng lực); đổi
`DEFAULT_MODE = LLM_ONLY`; gọi model để đo.
