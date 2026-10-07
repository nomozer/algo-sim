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

> **Đính chính 2026-10-03 (W15 Task 6, quyết định U3 của người dùng).** Nối cổng như bảng
> trên — `UNDETERMINED` bị từ chối MỌI NƠI — làm đỏ 182 test backend: 12 đã biết (candidate
> cũ, cây bẩn) và ~170 ca ĐÚNG, đề xác định, trước đó được phục vụ (khối cong cho bằng độ
> dài, bài điểm/đoạn không toạ độ, toạ độ có literal dẫn xuất) — lớp mà census vòng 1 không
> đo. Cột "Route" nay chỉ áp khi đề nêu một khối ĐA DIỆN theo từ vựng đóng
> (`shape_constraint.neu_khoi_da_dien`: ký hiệu chóp/lăng trụ, hoặc lăng trụ đứng không
> tên) — vùng có lỗ W12/W14 đã đo và có chứng chỉ C0/C1. Ngoài vùng: cổng VẪN tính, route
> ghi `assumption_status`/`assumption_certificate` cùng `assumption_enforced = False` và
> giữ hành vi + các cổng cũ; mối nguy "kích thước tự đặt" ngoài vùng là một vấn đề mở,
> không phải một an toàn. Lỗi bên trong bộ đọc vùng ⇒ coi là TRONG vùng (đóng an toàn).
> Ngoại lệ (U5, §3): nhiều định nghĩa với tới bị từ chối ở MỌI vùng.

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

> **Đính chính 2026-10-03 (W15 Task 6, quyết định U5 của người dùng).** (i) Một ngoại lệ hẹp
> cho "ghi lần hai": khi định nghĩa của một tên là ĐÚNG một khai báo có `initial_value` cộng
> ĐÚNG một câu lệnh dựng nó (một lần ghi động) và không câu lệnh nào TRƯỚC câu lệnh ấy đọc
> tên đó, literal khai báo không với tới ai — câu lệnh dựng là định nghĩa duy nhất. Đây là
> quy tắc sản phẩm có từ trước (`test_derived_point_construction::test_B3`: *"giá trị đến từ
> phép dựng ⇒ khai báo không gánh thông tin"*). Không đọc được một câu lệnh đứng trước ⇒ coi
> như có đọc (đóng an toàn). Ghi đè rồi đọc rồi khôi phục, bí danh của tên bị ghi đè, literal
> bị đọc trước khi bị ghi đè: vẫn `CLOSURE_MULTIPLE_DEFINITIONS`. (ii) Census vòng 2 thấy hai
> hàng `MUST_REFUSE` (ghi đè + khôi phục, bí danh trên đề hình thoi phẳng n1) được PHỤC VỤ vì
> nằm ngoài vùng đa diện của U3. Nhiều định nghĩa với tới là lỗi toàn vẹn của chương trình,
> không phải câu hỏi giả định: route từ chối nó ở MỌI vùng (`assumption_enforced = True`,
> `assumption_gate.MA_NHIEU_DINH_NGHIA`).

> **Đính chính 2026-10-03 (đánh giá cuối toàn nhánh, `41a26f11`).** Ngoại lệ (i) phải xét cả
> CHÍNH câu lệnh dựng: "không câu lệnh nào TỚI VÀ GỒM câu lệnh ấy đọc tên đó". Bản trước chỉ
> xét các câu lệnh TRƯỚC; mà bộ đi lát cắt bỏ qua việc một câu lệnh đọc chính tên nó định
> nghĩa. Vì thế với `X = trung điểm(X, N)`, literal khai báo của X (giả định của mô hình) vẫn
> quyết định giá trị mà không bao giờ vào lát cắt. Trên đề toạ độ n1, C0 đã trả `PROVEN_SAFE`
> cho một đáp số đổi theo literal ấy
> (`test_lenh_dung_doc_chinh_literal_no_ghi_de_van_la_nhieu_dinh_nghia`, ĐỎ trước bản sửa).
> Nay ca này là `CLOSURE_MULTIPLE_DEFINITIONS`. Quy tắc B3 (lệnh dựng không đọc tên đích)
> không đổi. Census vòng 3: không hàng nào đổi trạng thái.

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

> **Đính chính W16 (§14.1).** Dòng hệ số `construct_plane_from_equation` nay đòi CÙNG mặt
> phẳng: tỉ lệ với phương trình của ĐÚNG mặt phẳng đề mà biến gắn được (theo tên, hoặc duy
> nhất theo đếm) — không còn "tỉ lệ với một `plane_equation` bất kỳ".

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

> **Đính chính 2026-10-03 (U3).** "Từ chối" ở đoạn trên chỉ áp TRONG vùng khối đa diện (§1,
> đính chính U3). Đề không nêu khối đa diện theo từ vựng đóng — khối cong cho bằng độ dài,
> bài điểm/đoạn, toạ độ không kèm ký hiệu khối, `tứ diện ABCD` — được tính trạng thái và ghi
> lại, không bị từ chối theo cổng này.

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

> **Đính chính 2026-10-03 (W15 Task 10, đo ở trình duyệt).** Mô hình phối màu ở trên giả định
> phần tô ĐƯỢC VẼ. Lượt trình duyệt có thẩm quyền đầu tiên (`c1638891`) đo ΔE = 0 ở mọi mẫu.
> Phần tô vẫn kiểm chiều sâu, mà lớp chiều sâu đục của khối chạy trước toàn bộ hàng đợi trong
> suốt; thiết diện nằm trong khối nên bị loại ở mọi điểm ảnh. Đó cũng là nguyên nhân thật của
> "vùng thiết diện hoà mất" ở w14. Sản phẩm được sửa (`909a3a2d`: phần tô không kiểm chiều
> sâu), KHÔNG sửa ngưỡng. Sau bản sửa đo được 33,9/25,3 (desktop) và 33,8/25,9 (mobile),
> khớp mô hình (≥ 31,9).

> **Đính chính W16 (§14.4).** Bộ lấy mẫu W15 chỉ chừa lề quanh cạnh của đa giác thiết diện,
> hẹp hơn câu "quanh MỌI cạnh và dấu điểm" ở trên; W16 sửa bộ lấy mẫu cho khớp, ngưỡng giữ
> nguyên. Phần tô chuyển xuống DƯỚI các nét, kèm phép đo `SECTION_FILL_UNDER_EDGES`.

## 12. Không được

Nới cổng grounding; nâng chú thích của mô hình thành tiền đề hay GIVEN; dùng
`FIXTURE_TIN_CAY` ngoài fixture đã kiểm kê; sửa đề hoặc đáp án để chứng chỉ xanh; đổi bề
mặt mô hình (prompt, lược đồ, thẻ văn phạm, bảng năng lực); đổi
`DEFAULT_MODE = LLM_ONLY`; gọi model để đo.

## 13. Tác động lên ma trận năng lực (ghi 2026-10-03, sau w15)

Ma trận theo tầng [`geometry_capability_matrix_v2.json`](geometry_capability_matrix_v2.json)
là kiểm kê w13 (`as_of_head` `bf5a7907`) và không bị sửa. W15 đổi các tầng sau:

| Tầng | Trước w15 | Sau w15 |
|---|---|---|
| L03 `source_grounding` | GIVEN phải có trong câu đề (w12); toạ độ bố cục và giả thiết không bị kiểm | thêm bộ đọc ràng buộc hình dạng `shape_constraint.py`, chỉ xác nhận, từ vựng đóng §2.1 |
| L10 `measurement_provenance` | provenance chỉ là nhãn (GIVEN / DERIVED / LAYOUT_DERIVED / model_assumption) | mọi giá trị số người học thấy cần chứng chỉ C0/C1 trong vùng đa diện; nhãn không bao giờ là bằng chứng |
| L11 `renderer` | phần tô thiết diện bị lớp chiều sâu của khối loại | phần tô thiết diện khép kín là vật riêng, không kiểm chiều sâu (§11) |
| L15 `fail_closed` | từ chối ở kernel, grounding, kiểm tĩnh, cổng phạm vi | thêm chặng `assumption`: `ASSUMPTION_DETERMINES_ANSWER` / `ASSUMPTION_INVARIANCE_UNPROVEN` |
| L16 `browser_evidence` | — | ba loại từ chối mỗi họ, `SECTION_FILL_DISTINGUISHABLE`, phán quyết U2 |

- **Năng lực SẢN PHẨM theo họ không đổi:** không thêm họ nào, `product_capability.py`
  giữ nguyên. Cái đổi là điều kiện để một đáp số trong vùng đa diện được phục vụ.
- **Hệ quả cần khai khi trích năng lực.** Bài đa diện viết ngoài từ vựng đóng bị từ chối
  dù đề xác định đáp số (`ISSUE-ARCH-SHAPE-CONSTRAINT-VOCABULARY-COVERAGE`). Ngoài vùng
  đa diện, cổng chỉ ghi (U3).

## 14. W16 — sửa đổi trước merge (đăng ký 2026-10-03, TRƯỚC mọi bản sửa)

**Nguồn:** brief W16 (`W16_PREMERGE_SOUNDNESS_AND_VISUAL_EVIDENCE_CLOSURE`). Tái hiện ở
[`runs/w16-premerge-closure`](../evaluation/geometry/runs/w16-premerge-closure/)
(`diagnostics/logs/PROBE_W16_PHASE1.log`, tại `8a339d17`, 0 lượt gọi model).
**Trạng thái:** REGISTERED — chưa đo. Phạm vi thi hành của U3 giữ nguyên.

### 14.1 Hệ số mặt phẳng phải thuộc CÙNG mặt phẳng của đề (sửa §4)

Đây là bản sửa dòng "hệ số `construct_plane_from_equation`" của §4.

**Bằng chứng từ đề.** `plane_equation.doc_mat_phang_de(đề)` trả mỗi phương trình đọc trọn
với ba thứ:
- `ten`: tên viết trong chính mệnh đề, như `(α): …` hay `(P) có phương trình …`; không có
  tên thì `None`;
- bộ hệ số;
- `span` trong đề gốc.

**Tên phía chương trình.** `ten_mat_phang_cua_bien(tên biến)` cắt tên biến theo ký tự
không phải chữ hay số, và theo chỗ chữ thường chuyển sang chữ hoa. Mỗi mẩu được nhận là
tên mặt phẳng khi nó là:
- một chữ Hy Lạp;
- một tên phiên âm trong bảng ĐÓNG 24 chữ (`alpha`→α … `omega`→ω);
- hoặc MỘT chữ in hoa, có thể kèm chữ số.

Ví dụ: `alpha_plane`, `mat_phang_alpha`, `plane_beta`, `mp_P` cho lần lượt α, α, β, P.

> **Đính chính 2026-10-03 (W16, đánh giá trước bằng chứng; red `2dc55f1b`, sửa `6b120036`).**
> Luật trên bỏ mất dấu phẩy trên: biến `mp_P_prime` cho ra P, nên (P′) có thể mang phương
> trình của (P) mà C0 vẫn chứng nhận (dạng bí danh của A2). Dấu phẩy trên là một phần của
> tên, ở CẢ HAI phía:
> - Phía đề: `′` và `’` chuẩn hoá thành `'`, nên `(P′): …` cho tên `P'`.
> - Phía chương trình: một dấu phẩy trên viết liền sau mẩu, hoặc một token `prime`/`phay`
>   đứng ngay sau nó, cho tên có dấu phẩy. Ví dụ `mp_P_prime` cho P′, không cho P.
>
> Luật gắn (i)–(iii) bên dưới không đổi. Tiêm lỗi FA3/FA4 bỏ từng phía thì test đỏ.

**Khi nào là `SOURCE_DATUM`.** Chỉ khi gắn được với DUY NHẤT một phương trình:
- (i) **Biến có tên.** Đúng một phương trình của đề mang một trong các tên ấy, và hệ số
  tỉ lệ với nó (`tuong_duong`).
- (ii) **Biến không có tên nào.** Cần cả hai điều kiện: đề nhắc mặt phẳng đúng MỘT lần
  (`so_lan_nhac_mat_phang = 1`, tức một cụm `mặt phẳng`/`mp` và không có chữ Hy Lạp nào
  trong ngoặc), và chương trình dựng đúng một mặt phẳng từ phương trình. Đếm cho ra cặp
  duy nhất; sau đó mới kiểm hệ số.
- (iii) **Mọi trường hợp khác** không có vai trò. Detail ghi
  `PLANE_BINDING <biến>: <lý do>`.

Trùng bộ số không có nghĩa là trùng thực thể. Một biến tên β mang hệ số của (α) không có
vai trò, kể cả khi đề không cho phương trình nào của β.

`SourceInvariant plane_equation` của sản phẩm không đổi. Đó là hậu điều kiện "có một mặt
phẳng tỉ lệ với phương trình của đề"; nó không tuyên bố gì về thực thể. Đổi nó tức là đổi
phản hồi nằm ngoài phạm vi chứng chỉ.

**Giới hạn A′.** C0 gắn mỗi literal với thực thể của nó. Nó KHÔNG kiểm một phép dựng có
dùng đúng thực thể mà đề nói hay không. Ví dụ: đề nói (T) do (β) cắt, nhưng chương trình
cắt (T) bằng (α), và (α) đã được ghim đúng. Đây là lỗi quan hệ dựng, không phải literal tự
đặt. Muốn kiểm nó cần bộ đọc mẫu "(X) cắt … theo thiết diện (T)", tức là mở rộng từ vựng,
mà việc đó chờ quyết định W15-H3 của người dùng. Ghi ở
`ISSUE-ARCH-ASSUMPTION-CONSTRUCTION-RELATION-NOT-SOURCE-BOUND`.

### 14.2 Quan hệ nằm trong yêu cầu chứng minh không bao giờ là tiền đề (sửa §2)

**Span mục tiêu.** `shape_constraint.khoang_muc_tieu(đề)` đánh dấu hai loại span:
- Từ một từ khoá tới hết mệnh đề. Từ khoá là `chứng minh`, `chứng tỏ`, `CMR`, `kiểm tra`,
  `hỏi`; so theo ranh giới từ, không phân biệt hoa thường. Mệnh đề hết ở `.`, `?`, `!`,
  `;` hoặc chỗ xuống dòng.
- Một mệnh đề kết thúc bằng `?`, tính từ ranh giới đứng trước nó (`.`, `?`, `!`, `;`,
  `,`, `:` hoặc xuống dòng).

`Tính` KHÔNG là từ khoá, vì mệnh đề hỏi giá trị có thể mang theo `biết <giả thiết>`.

**Che span.** `che_muc_tieu(đề)` thay các span mục tiêu bằng khoảng trắng và giữ nguyên độ
dài, nên span của mọi bộ đọc vẫn đúng trên đề gốc.

**Đọc tiền đề.** Mọi tiền đề của chứng chỉ đọc từ đề ĐÃ CHE: `doc_rang_buoc`, bốn bộ phát
bất biến, `bang_chung_doan` và `doc_mat_phang_de`. Ràng buộc chỉ đọc được bên trong span
mục tiêu thì:
- không là tiền đề và không bao giờ là `SERVER_CONFIRMED`;
- nhưng VẪN chặn phản ví dụ: nó vào `CE_CONSTRAINT_NOT_CHECKED`.

`phan_chua_doc` vẫn chạy trên đề gốc. Detail ghi `GOAL_CLAUSE @[a,b]`.

**Giữ nguyên.** Giả thiết đứng TRƯỚC yêu cầu trong cùng một câu vẫn là tiền đề
(`Biết SA ⊥ (ABC), chứng minh …`). Câu phủ định trong giả thiết vẫn không phát gì, vì từ
vựng không đổi.

**Ngoài W16 (chỉ ghi, không sửa):**
- Độ dài và toạ độ nằm trong yêu cầu chứng minh vẫn được cổng grounding của sản phẩm đọc.
  Đó là một thẩm quyền khác, không phải chứng chỉ.
- `biết chiều cao bằng …` đứng sau `Tính` không được đọc, nên kết quả là `UNDETERMINED`:
  từ chối thừa nhưng vẫn đóng an toàn.

### 14.3 Bốn nhánh đóng an toàn đã có test

Mục này đóng `ISSUE-EVAL-ASSUMPTION-GATE-UNTESTED-GUARDS`. Mỗi nhánh có:
- một ca kích hoạt từ chương trình HỢP LỆ;
- mã lý do `ASSUMPTION_INVARIANCE_UNPROVEN` kèm detail của nhánh;
- một ca hợp lệ để đối chứng;
- một phép tiêm lỗi gỡ nhánh đi và làm test đỏ.

Bốn nhánh và ca kích hoạt:
- `CLOSURE_UNSUPPORTED_KIND`: có lệnh `if`;
- `TEMPLATE_CONSTRAINT_VIOLATED`: S rời pháp tuyến tại A;
- `FRAME_DEPENDENT`: mặt phẳng cho bằng phương trình nằm trên lát cắt C1;
- `FORMATION_REJECTED`: một mặt chỉ có hai đỉnh.

### 14.4 Phần tô thiết diện nằm DƯỚI các cạnh (sửa §11; ngưỡng của §11 KHÔNG đổi)

**Renderer.** Phần tô vẽ ở thứ tự 7:
- sau mặt khối và mặt cắt (0), sau lớp chiều sâu (5);
- trước mọi nét (8) và trước viền thiết diện (10).

`depthTest:false`, `depthWrite:false`, độ lệch và độ đục giữ nguyên. Phần tô vẫn không che
vật nào.

**Bộ lấy mẫu của `SECTION_FILL_DISTINGUISHABLE`.** Bản W15 chỉ chừa lề quanh cạnh của chính
đa giác thiết diện. §11 đăng ký "bỏ một lề `margin_px` quanh MỌI cạnh và dấu điểm đã
chiếu", nên bộ lấy mẫu được sửa cho khớp. Ngưỡng `{20, 12, 3, 3}` giữ nguyên.

**Phép đo mới `SECTION_FILL_UNDER_EDGES`.** Đo ở bước khép-và-tô, trên cùng cặp ảnh tô bật
và tô tắt.
- **Cạnh được xét:** mỗi cạnh khối theo bảng mặt của cảnh có ít nhất 3 điểm (bước 1 px CSS)
  nằm trong đa giác thiết diện chiếu. Mỗi điểm phải cách biên đa giác và mọi dấu điểm ít
  nhất `margin_px`.
- **Lõi:** điểm ảnh TỐI NHẤT trên ảnh tô tắt, trong dải ±1 px CSS quanh các điểm ấy.
- **Tham chiếu:** trung vị ΔE76(bật, tắt) tại ±4 px CSS về hai phía các điểm ấy. Các điểm
  tham chiếu phải vẫn nằm trong vùng và cách mọi cạnh khác cùng mọi dấu điểm ít nhất
  `margin_px`.
- **Đạt** khi có đủ hai điều kiện:
  - ρ = ΔE76(bật, tắt) tại lõi / tham chiếu < 1;
  - ΔE76(lõi lúc tắt, trung vị tham chiếu lúc tắt) ≥ `T_ON_MIN`, tức là cạnh thật sự được
    vẽ.

Vì sao ranh giới là 1: theo mô hình phối màu "over", nét 1 px có độ phủ MSAA c ≥ ½ và độ
đục α ≥ 0,9.
- Cạnh nằm TRÊN phần tô: ρ = 1 − cα ≤ 0,55.
- Phần tô nằm TRÊN cạnh tối `#1e293b`: ρ ≈ 1,2–1,5.

Vậy 1 là ranh giới cấu trúc ("cạnh che một phần tô"), không phải con số chỉnh theo ảnh.

Không có cạnh nào cắt qua vùng thì kết quả là `NOT_APPLICABLE`, không tính là đạt. Họ
cross-section phải có ít nhất một cạnh cắt qua ở cả hai viewport. Không bao giờ chỉnh theo
ảnh sản phẩm: nếu trượt, sửa thứ tự vẽ của sản phẩm.

> **Đính chính W16 T5 (tính trên mô hình, TRƯỚC mọi phép đo trình duyệt).** Test node của
> bộ chấm cho số chính xác thay cho ước lượng ở trên:
> - cạnh nằm TRÊN phần tô: ρ = 0 (c = 1, α = 1) … 0,58 (c = ½, α = 0,9);
> - phần tô nằm TRÊN cạnh: ρ = 1,09 (c = ½, α = 0,9) … 1,39 (c = 1, α = 1);
> - độ tương phản của cạnh lúc tắt: 28,1 … 67,2 (≥ `T_ON_MIN`).
>
> Ranh giới ρ < 1 không đổi.

### 14.5 Ô từ chối trên sheet bằng chứng

**Duyệt.** Ô âm duyệt `{kind: {viewport}}` đúng như bộ chạy ghi: ba loại
(`ungrounded_source`, `assumption`, `topology_kernel`) nhân hai viewport (desktop, mobile).
Mỗi loại có chú thích tiếng Việt riêng, lấy từ một bảng đóng; gặp loại lạ thì báo lỗi.

**Điều kiện cho mỗi ô:**
- Nguồn ảnh là `images/<họ>/negative/<loại>/<viewport>/refusal.png`.
- Bản ghi có `pass`, không có canvas, `learner_reason` khác rỗng.
- Hộp chữ lời từ chối có mực (điểm ảnh độ sáng < 100) chiếm ít nhất 0,5 %. Hộp này là
  `refusal_message_box`, do bộ chạy ghi lúc chụp.

**Thất bại.** Bộ dựng THẤT BẠI khi thiếu bất kỳ ảnh nào (trạng thái, bảng lời giải, từ chối,
bước dựng) hoặc khi một ô từ chối không đọc được. Không bao giờ thay bằng ô trắng.

## 15. W17 — binding phép dựng, grounding không lấy mục tiêu, nguyên nhân từ chối, số đo trên hình (đăng ký 2026-10-03, TRƯỚC mọi bản sửa)

**Nguồn:** brief W17 (`W17_OPERATION_BINDING_AND_ON_SCENE_ANNOTATIONS`) và quyết định U-W17-1 của
người dùng (nhãn "Kết quả" và "Số đo" BẬT mặc định). Tái hiện và bằng chứng ở
[`runs/w17-operation-annotations`](../evaluation/geometry/runs/w17-operation-annotations/).
**Trạng thái:** REGISTERED — chưa đo. Phạm vi thi hành của U3 giữ nguyên.

### 15.1 Phép dựng phải dùng ĐÚNG thực thể mà đề nói (đóng giới hạn A′ của §14.1)

**Quan hệ cắt đọc từ đề.** `shape_constraint.doc_quan_he_cat(đề)` đọc, trên bản đề đã che
mệnh đề mục tiêu, mỗi câu nói *mặt phẳng nào cắt khối nào theo thiết diện nào*. Từ vựng ĐÓNG:
- `(X) cắt <khối> theo thiết diện (T)`, có hoặc không có `Mặt phẳng` đứng trước;
- `Mặt phẳng (X): <phương trình> cắt <khối> theo thiết diện (T)` — phương trình viết ngay
  trong câu;
- `Mặt phẳng <phương trình> cắt <khối> theo thiết diện (T)` — mặt phẳng không tên;
- `thiết diện (T) của <khối> cắt bởi (mặt phẳng) (X)` và `cắt <khối> bởi (mặt phẳng) (X)
  (được) thiết diện (T)` — cùng quan hệ, viết theo chiều bị động;
- `<khối>` là `khối chóp`/`hình chóp`/`khối lăng trụ`/`hình lăng trụ`/`hình hộp`/`hình lập
  phương`, có thể kèm ký hiệu (`S.ABCD`); thiết diện có thể không tên (`theo một thiết diện`).
- Cách viết nằm ngoài các dạng trên không cho quan hệ nào. Khi đó một `construct_section`
  trên lát cắt KHÔNG được chứng nhận (`UNDETERMINED`, lý do "chưa đọc được quan hệ cắt"),
  nhưng lý do ấy là giới hạn từ vựng, không phải `CONSTRUCTION_NOT_TEXT_BOUND`: mã ấy chỉ
  dùng khi quan hệ ĐỌC ĐƯỢC mà phép dựng lệch nó.

Kết quả: `QuanHeCat(mat_phang, khoi, thiet_dien, span)`; `mat_phang` là tên (`α`, `P'`) hoặc
khoá của phương trình không tên đọc tại câu đó; `khoi` là ký hiệu khối hoặc `None` (khi đề có
đúng một khối thì đó là khối ấy); `thiet_dien` là tên hoặc `None`.

**Danh tính của một mặt phẳng trong chương trình** (thứ tự ưu tiên):
1. **Theo nguồn.** Câu lệnh mang `source_fact_id` trỏ tới một InputFact của hợp đồng; giá
   trị nguyên văn của fact xuất hiện ĐÚNG một lần trong đề; trong đoạn đó có đúng một phương
   trình mặt phẳng đọc trọn (`doc_mat_phang_de`). Danh tính là mặt phẳng ấy (tên, hoặc khoá
   span nếu không tên). Hệ số của câu lệnh vẫn phải tỉ lệ với phương trình ấy.
2. **Không có tham chiếu nguồn dùng được** ⇒ luật W16 (§14.1): theo tên, hoặc duy nhất theo
   đếm.
3. Tên biến nói một mặt phẳng và nguồn nói mặt phẳng KHÁC ⇒ không có danh tính (từ chối).

Đổi tên biến máy không đổi danh tính theo nguồn. **Trùng phương trình không phải trùng thực
thể:** (α): z = 3 và (β): z = 3 là hai mặt phẳng khác nhau trong đề; phép dựng đề nói dùng (β)
mà chương trình dùng mặt phẳng có danh tính (α) thì không được chứng nhận, dù số đo bằng nhau.

**Luật phép dựng.** Với MỌI `construct_section` trên lát cắt của một giá trị hiển thị:
- thiết diện của chương trình phải gắn được với đúng một quan hệ cắt của đề: đề có một quan
  hệ và chương trình có một thiết diện trên lát cắt; hoặc theo nguồn (`source_fact_id` của
  khai báo thiết diện trỏ tới fact chứa tên thiết diện); hoặc theo tên thiết diện;
- mặt phẳng cắt của câu lệnh phải có danh tính BẰNG mặt phẳng của quan hệ;
- khối bị cắt phải có tập đỉnh bằng tập đỉnh của khối trong đề (ký hiệu khối, hoặc khối duy
  nhất của đề khi quan hệ không ghi ký hiệu).

Vi phạm một quan hệ đọc được ⇒ `UNDETERMINED`, detail `OPERATION_BINDING <thiết diện>: <lý
do>`, `reason_code = CONSTRUCTION_NOT_TEXT_BOUND`, `reason_subjects` = ký hiệu mặt phẳng/khối
liên quan.

> **Đính chính 2026-10-03 (W17 Task 2 — sau bản sửa, TRƯỚC census và mọi phép đo).** Full suite
> sau bản sửa cho thấy hai gold đã phục vụ trước W17 (d7 `gold_section_discoverability`, e7
> `gold_affordance_ab`: *"Mặt phẳng đi qua ba điểm A, C và B′ cắt hình lập phương theo một thiết
> diện"*) bị từ chối vì từ vựng trên thiếu dạng ấy — một hồi quy, không phải giới hạn chấp nhận
> được. Ba điểm chốt:
> - **Từ vựng thêm một dạng chủ thể:** `Mặt phẳng [(X)] (đi) qua (ba|các điểm) A, B (,|và) C`;
>   danh tính là TẬP BA ĐIỂM (tên trong ngoặc, nếu có, bỏ qua).
> - **Mặt phẳng gọi bằng điểm** (`(MNP)`, hoặc dạng "qua ba điểm") có danh tính là tập điểm;
>   `construct_plane` của chương trình có danh tính là tập `through` (theo khoá ký hiệu). Hai mặt
>   phẳng trùng hình học nhưng khác tập điểm vẫn là hai thực thể (§15.1 không đổi).
> - **Tham chiếu nguồn có cấu trúc** của một biến mặt phẳng/thiết diện là `source_fact_id` của
>   KHAI BÁO biến: IR không có ô ấy trên `construct_plane_from_equation`/`construct_section`,
>   và `SemanticProgramSpec._nang_xuat_xu_cau_lenh` nâng ô mô hình ghi ở câu lệnh về khai báo
>   cùng tên (không có khai báo thì ô bị bỏ). Thêm ô vào câu lệnh là đổi bề mặt mô hình — ngoài
>   W17. Từ chối ở chặng `assumption` trong vùng thi hành (U3), không gửi đi sửa. Không gắn
được vì đề không có quan hệ đọc được ⇒ `UNDETERMINED` với `ASSUMPTION_INVARIANCE_UNPROVEN`
(fail-closed, giới hạn từ vựng). Luật này là ĐIỀU KIỆN THÊM cho C0 và C1: nó chỉ chặn một kết
luận `PROVEN_SAFE`, không thay chẩn đoán của các nhánh khác (detail của nó được nối thêm).

### 15.2 Mục tiêu cần chứng minh không bao giờ thành GIVEN (grounding)

`grounding_gate.check_grounding` đọc bằng chứng GIVEN (độ dài, toạ độ, giá trị số) trên
`che_muc_tieu(đề)` — cùng bản che của §14.2, cùng độ dài, span không đổi. Một giá trị CHỈ xuất
hiện trong mệnh đề mục tiêu ⇒ từ chối ở chặng `grounding`, `reason_code =
GIVEN_ONLY_IN_GOAL_CLAUSE`, không gửi đi sửa. Dữ kiện trong câu `Tính …, biết …` vẫn là dữ
kiện (`Tính` không phải từ khoá mục tiêu). Đây là sửa grounding, không mở rộng chứng chỉ: B6b
vẫn là từ chối thừa đã ghi.

> **Đính chính 2026-10-03 (W17 Task 3 — sau bản sửa, TRƯỚC census và mọi phép đo).**
> - **Cách đọc:** thân `check_grounding` chạy trên đề đã che; lời từ chối mã nguồn (`MA_LOI_NGUON`)
>   chỉ đổi thành `GIVEN_ONLY_IN_GOAL_CLAUSE` khi CÙNG thân chạy trên đề gốc qua được — lần đọc
>   ấy phân loại, không bao giờ cấp phép. Tên thực thể vẫn đọc trên đề gốc.
> - **`Chứng minh X, biết Y`:** `khoang_muc_tieu` (§14.2) kết thúc mệnh đề mục tiêu ở `, biết`.
>   Y là giả thiết — nếu không, bản sửa grounding sẽ từ chối dữ kiện hợp lệ đứng sau `biết` và
>   bảo học sinh rằng nó "chỉ có trong yêu cầu chứng minh" (tái hiện: test G5 đỏ trước đính
>   chính). Đổi này áp cho cả chứng chỉ (cùng bản che).
> - **§15.3, thi hành:** nguyên nhân nằm trên MỌI envelope từ chối hình học (`_hong` của route
>   gắn theo bảng; `NON_POSITIVE_LENGTH` của compiler và `PLANE_DOES_NOT_CUT` của kernel phân xử
>   theo đề tại nơi từ chối; biên API mặc định `UNKNOWN`). Lời chung `geometry_generation_failed`
>   (nay là lời `UNKNOWN`) và câu gợi ý của giao diện thôi mời học sinh viết lại đề; chỉ
>   `SOURCE` mời sửa dữ kiện trong đề. Fixture âm "độ dài không dương" GHI số 0 vào chính đề
>   (lập phương: "cạnh bằng 0"); ca đề hợp lệ + hợp đồng sai là fixture riêng
>   `cube_system_cause` (`CONSTRUCTION`).

> **Đính chính 2026-10-04 (W17, tự rà soát cuối toàn nhánh, SAU lần đóng băng đầu).** Ba lỗi đọc
> sai đều được tái hiện qua cổng trước khi sửa. Nhãn W17C và test đỏ commit trước bản sửa
> (`01b0c27c`). Từ vựng không mở rộng; ba bản sửa giữ đúng nghĩa đã đăng ký.
>
> 1. **Tân ngữ của `với` không phải mặt phẳng cắt.** Câu "(Q) qua M và song song với (ABCD) cắt
>    khối chóp theo thiết diện (T)" từng được đọc thành "(ABCD) cắt …". Cùng lỗi với "vuông góc
>    với (SBC)". Bộ đọc nay bỏ mọi khớp có mặt phẳng đứng ngay sau `với` (`_TAN_NGU_VOI`). Câu ấy
>    không còn quan hệ nào đọc được: từ chối `ASSUMPTION_INVARIANCE_UNPROVEN`, giới hạn từ vựng.
> 2. **Danh tính không ghim được là CHƯA CHỨNG MINH, không phải LỆCH.** Mã
>    `CONSTRUCTION_NOT_TEXT_BOUND` (nguyên nhân `CONSTRUCTION`) chỉ dùng khi cả hai danh tính đều
>    xác định và khác nhau. Các trường hợp sau không xác định được danh tính:
>    - mặt phẳng đề có tên mà không có phương trình và không gọi bằng điểm, như "(Q), song song
>      với (ABCD),";
>    - mặt phẳng của chương trình không gắn được với đề;
>    - khối mà đề hoặc chương trình không ghim;
>    - thiết diện không câu cắt nào gọi tên.
>
>    Những trường hợp này cho `ASSUMPTION_INVARIANCE_UNPROVEN` (nguyên nhân `UNKNOWN`). Lời "đề
>    không cần sửa, gửi lại để hệ dựng lại" là lời hứa sai khi hệ không bao giờ chứng minh được.
>    Cả hai đường vẫn TỪ CHỐI; chỉ điều được khẳng định thay đổi.
> 3. **`…, biết Y?` trong câu hỏi.** Luật câu hỏi của `khoang_muc_tieu` lấy ranh giới cuối trước
>    `?`, tức dấu phẩy của `, biết`. Vì vậy nó che chính giả thiết Y và để lộ câu hỏi. Mệnh đề mở
>    bằng `biết` sau dấu phẩy nay là giả thiết, và mục tiêu là mệnh đề hỏi đứng trước nó
>    (`_MO_BIET`).
>
> Không có yêu cầu nào đổi từ "từ chối" sang "phục vụ" sai. G6/G7 trước đây bị từ chối, nay
> được phục vụ đúng. `CACHE_VERSION` giữ 109, vì 109 chưa phát hành và mọi row v108 đã trượt.

### 15.3 Nguyên nhân từ chối — lời cho người học dựa trên lý do có cấu trúc

Mỗi envelope `unsupported` mang `refusal_cause` ∈ {`SOURCE`, `CONSTRUCTION`, `UNKNOWN`},
quyết định CHỈ từ mã có cấu trúc và bộ đọc đề của server:
- `SOURCE` — chính dữ kiện của đề gây từ chối: thiếu (`GIVEN_VALUE_NOT_IN_SOURCE`,
  `ASSUMPTION_DETERMINES_ANSWER`), mâu thuẫn (`SOURCE_*`), chỉ có trong mục tiêu
  (`GIVEN_ONLY_IN_GOAL_CLAUSE`), suy biến (độ dài ≤ 0 mà ĐỀ ghi), mặt phẳng ĐỀ cho không cắt
  khối (`PLANE_DOES_NOT_CUT` với mặt phẳng ghim bởi đề).
- `CONSTRUCTION` — đề đủ và hợp lệ nhưng chương trình/hợp đồng hệ sinh ra sai:
  `CONSTRUCTION_NOT_TEXT_BOUND`, độ dài ≤ 0 mà đề KHÔNG ghi, lỗi kernel trên giá trị đề không
  ghim.
- `UNKNOWN` — mọi trường hợp còn lại; lời chung, không đổ cho đề.

Lời cho người học nêu (i) thực thể/dữ kiện gây lỗi bằng ký hiệu đọc được, (ii) lý do ngắn,
(iii) hành động hợp với nguyên nhân. Với `CONSTRUCTION` và `UNKNOWN`, lời KHÔNG yêu cầu người
học sửa đề.

> **Đính chính 2026-10-03 (W17 Task 1, TRƯỚC bản sửa).** `SOURCE_EVIDENCE_CONFLICT` và
> `SOURCE_SPAN_MISMATCH` nói rằng số liệu HỆ dùng lệch với câu chữ của đề; đề là thẩm quyền,
> nên nguyên nhân là khâu đọc đề của hệ: `CONSTRUCTION`, không phải `SOURCE`. Bảng chốt:
> - `SOURCE`: `GIVEN_VALUE_NOT_IN_SOURCE`, `ASSUMPTION_DETERMINES_ANSWER`,
>   `GIVEN_ONLY_IN_GOAL_CLAUSE`, `SOURCE_TEXT_MISSING`; `NON_POSITIVE_LENGTH` khi bộ đọc đề của
>   server đọc đúng độ dài ≤ 0 ấy cho đúng đoạn ấy (hoặc cạnh hình lập phương); thiết diện rỗng
>   (`PLANE_DOES_NOT_CUT`) khi mặt phẳng cắt tỉ lệ với một phương trình mặt phẳng của đề.
> - `CONSTRUCTION`: `CONSTRUCTION_NOT_TEXT_BOUND`, `SOURCE_EVIDENCE_CONFLICT`,
>   `SOURCE_SPAN_MISMATCH`; `NON_POSITIVE_LENGTH` và `PLANE_DOES_NOT_CUT` khi đề KHÔNG ghi giá
>   trị ấy.
> - `UNKNOWN`: mọi mã khác (kể cả `ASSUMPTION_INVARIANCE_UNPROVEN`, giữ lời W15 của nó).

### 15.4 Số đo trên hình — hợp đồng gắn đối tượng

Mỗi vật `quantity` có thể mang `annotation = {kind, category, subject_ids, anchor, unit}`:
- `kind` ∈ {`length`, `area`, `volume`, `distance`, `angle`}; `category` ∈ {`measurement`,
  `result`} — `result` khi đại lượng là đích của đề (đích, hoặc được một đích `alias_of`), còn
  lại `measurement`; đích dùng CHUNG danh tính với đại lượng nó trỏ tới (một nhãn, không hai);
- `subject_ids` là định danh vật/điểm CÓ trong cảnh; `anchor` ∈ {`segment`, `region`,
  `solid`, `pair`}; `unit` chỉ khi payload có đơn vị.

Luật gắn (backend sở hữu):
- độ dài đề cho: đoạn mà bộ đọc đề của server đọc tại span bằng chứng GIVEN, và khoảng cách
  chính xác giữa hai điểm trong bộ nhớ cuối bằng đúng giá trị — không thì không gắn;
- đại lượng suy ra: toán hạng IR của phép đo (`measure … of/wrt`): diện tích → đa giác/thiết
  diện (`region`), thể tích → khối (`solid`), khoảng cách → cặp (`pair`), độ dài đoạn → đoạn;
- không gắn được ⇒ không có `annotation` và có diagnostic `ANNOTATION_UNBOUND <id>: <lý do>`;
  đại lượng vẫn ở bảng chi tiết.

> **Ghi chú thi hành 2026-10-03 (W17 Task 5 — trước census và mọi phép đo).** Thẩm quyền gắn:
> `semantic_program/quantity_annotations.py` (gọi từ `build_simulation_state`; lớp chiếu không tự
> tính hình), `scene3d._gan_so_do` quyết `category` và chở `diagnostics` ở gốc cảnh. Ba điểm phạm
> vi:
> - `distance` giữa hai ĐIỂM là độ dài đoạn (`kind = length`, `anchor = segment`); điểm–đường và
>   điểm–mặt là `pair`, neo TẠI ĐIỂM của cặp. Phía trình bày chỉ được lấy trung bình toạ độ
>   backend phát (chân đường vuông góc là suy luận hình học, cấm ở frontend — `scene3d.test.tsx`
>   5D), nên góc giữa hai đường/mặt và khoảng cách giữa hai vật không phải điểm KHÔNG gắn (Task 6);
> - vật CONG (đường tròn, elip, khối tròn xoay) chưa có điểm neo đăng ký ⇒ không gắn, có chẩn
>   đoán; giá trị vẫn ở bảng chi tiết (lộ trình);
> - MỘT chủ thể, MỘT nhãn: cùng `kind`, `anchor` và tập chủ thể (hình hộp: độ dài đề cho AA′ và
>   chiều cao đo được AA′) ⇒ giữ nhãn của dữ kiện, cái còn lại có chẩn đoán `same subject as …`.

Frontend chỉ chiếu, đặt nhãn, tránh chồng và bật/tắt; không tính giá trị, không suy gắn từ tên.
Một nhãn hiện ở bước dựng `k` chỉ khi chủ thể đã có mặt và đại lượng đã khả dụng ở `k` (cùng
luật với lớp lời giải). Bật/tắt "Số đo"/"Kết quả" không đổi hình, camera, timeline, chuỗi nhân
quả hay chính sách nét liền/đứt.

### 15.5 Kiểm trên trình duyệt (đăng ký trước mọi phép đo)

- **Bật/tắt:** tắt "Số đo" và "Kết quả" ⇒ 0 nhãn số đo trong DOM; `__geo3d_edge_dash_signature`,
  `__geo3d_rendered_object_ids` và ảnh chụp camera KHÔNG đổi giữa bật và tắt.
- **Gắn đúng chủ thể:** mỗi nhãn hiện có điểm gần nhất của hộp nhãn cách điểm neo chiếu của
  chủ thể ≤ 24 px CSS.
- **Không lộ trước:** ở mỗi bước dựng (tiến rồi lùi), không có nhãn của đại lượng chưa khả
  dụng; nhãn kết quả chỉ từ bước nó được tính.
- **Trong khung, không đè:** mọi nhãn hiện nằm trong khung canvas; không hộp nhãn số đo nào
  giao hộp nhãn điểm hiện; xoay quỹ đạo và đổi cỡ vẫn giữ hai luật này.
- **Nhân quả:** trung tính → chọn → khôi phục đo ở CÙNG camera và CÙNG vị trí cuộn; ghi riêng
  camera, lựa chọn và vị trí cuộn. Ảnh đã cuộn mất canvas không chứng minh camera đặt lại.
- **Từ chối:** mặt phẳng sai (đề nói (β), chương trình dùng (α)) bị từ chối với nguyên nhân
  `CONSTRUCTION`; mặt phẳng đúng được phục vụ.

Các ngưỡng trên không bao giờ chỉnh theo ảnh sản phẩm: nếu trượt, sửa sản phẩm.

**Đính chính cách đo — lượt trình duyệt đầu (Task 7, 2026-10-04; trước mọi phép đo nghiệm thu;
không ngưỡng nào đổi).** Lượt đầu đỏ ở cả sáu họ. Hai nguyên nhân là lỗi sản phẩm và được sửa
trong sản phẩm: nhãn đáy bị ẩn khi bốn phía đều kín (bộ đặt nhãn thêm bốn góc), và câu gợi ý của
thẻ từ chối nhắc lại lời backend. Bốn nguyên nhân còn lại là cách đo đọc sai một trạng thái đúng,
nên được sửa trong bộ đo:
- "Camera không đổi" nghĩa là chuyển động ma trận ≤ `CAMERA_SETTLE_TOLERANCE` (1e-9, w09).
  Damping của OrbitControls viết lại các ULP cuối ở mỗi khung. Lượt đầu báo đổi camera với độ
  lệch 1e-14, trong khi khung canvas trùng từng byte.
- Khung dùng để so sánh khi khôi phục nhân quả phải là khung NGHỈ ở cả hai đầu, tức hai lần chụp
  liền nhau trùng byte. Ở lượt đầu, khung trung tính (cuboid, mobile) bị chụp giữa chừng. Lượt
  chẩn đoán chạy cùng luồng cho khung trung tính trùng khung khôi phục.
- Phép đo điểm ảnh của HÌNH (sắc vai trò W12, mẫu tô §11/§14.4) che mọi lớp phủ DOM trên canvas,
  nay gồm cả nhãn số đo — giống nhãn điểm từ W12. Viền xanh "đang xét" của nhãn vật đang chọn là
  chữ, không phải một vật được vẽ. Mẫu tô nằm dưới nền nhãn (90 % màu giấy) đọc ra màu nền nhãn:
  ở lượt đầu, min ΔE = 2.8 < `T_ON_MIN` nằm dưới nhãn "Diện tích thiết diện = 9", trong khi mean
  vẫn 30.9.

**Đính chính cách đo — lượt đo nghiệm thu đầu trên candidate cuối (measurement `83f101e4`,
2026-10-04; ĐĂNG KÝ trước lượt đo lại; không ngưỡng nào khác đổi).** Lượt đo đỏ đúng một ô:
cube/mobile `causal_restore` = `CANVAS_NOT_RESTORED`. Khung trung tính là `b9c334f7…`, khung khôi
phục là `2090af68…` và chưa nghỉ. Mã sản phẩm và fixture trùng lượt đo `c5592c1a` (khác nhau chỉ ở
trường danh tính); lượt ấy PASS ô này với `45e45c71…` ở cả hai đầu.

Hai lượt chẩn đoán chạy cùng luồng, một lượt có thêm tải CPU. Cả hai cho `45e45c71…` ở cả hai đầu.
Mỗi lượt chụp chuỗi 40 khung ở mỗi đầu. Khung lúc nghỉ giữ nguyên camera, hộp nhãn, độ mờ nhãn và
vị trí cuộn, nhưng 4/160 lần chụp lệch trên TOÀN khung, mỗi kênh 8-bit lệch tối đa 1. So từng byte
vì thế đọc nhiễu chụp thành "không khôi phục".

Luật mới:
- Khung khôi phục trùng khung trung tính khi cùng cỡ và mọi kênh lệch ≤ `NHIEU_KHUNG_TOI_DA` = 1.
- Bất kỳ điểm ảnh nào lệch ≥ 2, khác cỡ, hoặc không đo được độ lệch ⇒ `CANVAS_NOT_RESTORED`.
- Khi hai khung khác byte, bộ đo lưu cả hai ảnh để xem lại.

Ngưỡng 1 là đặc trưng nhiễu đo được, đặt TRƯỚC lượt đo lại. Nếu lượt đo lại trượt, đọc hai ảnh đã
lưu, không nới ngưỡng. Lượt đỏ không lưu khung, nên độ lệch thật của nó là `NOT_RECOVERABLE`. Bằng
chứng: `docs/evaluation/geometry/runs/w17-operation-annotations/diagnostics/browser-final-attempt1-83f101e4/`.

## 16. W18 — binding phép dựng điểm, nhãn tập trung, một nơi giải thích (đăng ký 2026-10-04, TRƯỚC mọi bản sửa)

**Nguồn:** brief W18 (`W18_CONSTRUCTION_BINDING_AND_FOCUSED_ANNOTATIONS`). Tái hiện và bằng chứng ở
[`runs/w18-binding-focus`](../evaluation/geometry/runs/w18-binding-focus/).
**Trạng thái:** REGISTERED, chưa đo. Phạm vi thi hành U3 và luật §15.1 (thiết diện) giữ nguyên.

Phép dò Phase 1 (trước bản sửa, 0 lượt gọi) cho thấy:
- hình chiếu lên sai đường/mặt phẳng được PHỤC VỤ với giá trị sai;
- "M, N lần lượt là trung điểm của SA, SB" với hai đích bị tráo được phục vụ (3√6 thay cho 9);
- đích đổi tên và một điểm trùng toạ độ nhưng khác danh tính được phục vụ.

Trung điểm sai đoạn khi tên khớp đã bị bất biến toạ độ `segment_division` chặn, nhưng với mã chung
(nguyên nhân UNKNOWN).

### 16.1 Quan hệ dựng điểm đọc từ đề

`construction_binding.doc_quan_he_dung(đề)` đọc trên đề đã che mệnh đề mục tiêu (§14.2). Từ vựng
ĐÓNG, viết hoa/thường tự do:

- **Trung điểm:**
  - `<X> là trung điểm [của] [đoạn [thẳng]|cạnh] <A><B>`;
  - danh sách `<X>, <Y> [và|,] <Z> lần lượt là trung điểm [của] [các (cạnh|đoạn [thẳng])] <AB>,
    <CD> [và|,] <EF>`. Số đích phải bằng số đoạn; ghép theo thứ tự.
- **Phép chiếu:**
  - `<X> là hình chiếu [vuông góc] của <P> (lên|trên|xuống) <đích nhận>`;
  - `<X> là chân (đường vuông góc|đường cao) [kẻ|hạ] từ <P> (xuống|đến|tới|lên) <đích nhận>`.
- **Đích nhận:**
  - `[mặt phẳng|mp] (<ba điểm trở lên>)`: mặt phẳng gọi bằng điểm;
  - `[mặt [phẳng]] đáy`: đáy của khối DUY NHẤT đề nêu theo từ vựng §5;
  - `[đường thẳng|cạnh|đoạn [thẳng]] <A><B>`: đường qua hai điểm.

Kết quả: `QuanHeDung(kind ∈ {midpoint, projection}, dich, toan_hang, nhan_hoc_sinh, span)`.
- Trung điểm: toán hạng là cặp KHÔNG thứ tự.
- Phép chiếu: toán hạng là (điểm nguồn, đích nhận), hai vai trò riêng.

Một đích được hai câu nói khác nhau thì bị bỏ cả hai (không phân xử). Cách nói ngoài các dạng trên
không cho quan hệ nào.

### 16.2 Danh tính

**Danh tính điểm của một biến chương trình**, xét lần lượt:
1. đi theo bí danh `assign var` về định nghĩa gốc;
2. khoá ký hiệu `_khoa` (A′ ≡ A' ≡ A’ ≡ A_prime ≡ Aprime);
3. nhãn (`label`) của câu lệnh/khai báo;
4. fact nguồn: `source_fact_id` của khai báo trỏ tới fact nêu đúng một ký hiệu điểm của đề;
5. lưới hoà giải C₁a.

Các nguồn chỉ hai thực thể khác nhau ⇒ danh tính MƠ HỒ. Một biến không ra ký hiệu điểm nào của đề
là một thực thể KHÔNG có trong đề. **Toạ độ hay giá trị bằng nhau không bao giờ tạo bí danh.**

**Đích nhận:**
- mặt phẳng = tập điểm; hai mặt phẳng khớp khi chung ≥ 3 điểm và tập này chứa tập kia (ba điểm
  phân biệt của mặt phẳng đề nêu xác định chính nó);
- đường = cặp điểm không thứ tự;
- mặt phẳng phương trình hay đường dẫn xuất khác ⇒ không ghim.

### 16.3 Trạng thái đối chiếu

Phép dựng trong phạm vi:
- mọi `construct_point` có biểu thức `midpoint`, `project_onto` hoặc `divide_segment`;
- mọi `construct_point` có đích là điểm ĐỀ GIỚI THIỆU (`source_entities.la_ten_suy_ra`) mà đề có
  quan hệ §16.1 cho nó.

Mọi điểm dựng ra đều hiện trên hình, nên luật áp cho mọi phép dựng ấy, kể cả khi đáp số cuối tình
cờ bằng nhau.

| Trạng thái | Khi nào |
|---|---|
| MATCHED | Đích là điểm đề giới thiệu, có quan hệ cùng loại, toán hạng khớp. Trung điểm: cặp không thứ tự; `divide_segment(A, B, 1/2)` tương đương. Phép chiếu: cùng điểm nguồn và cùng đích nhận |
| MISMATCHED | Chỉ khi mọi danh tính liên quan đều xác định: khác loại, khác toán hạng, khác đích nhận. Gồm cả hai đích đề giới thiệu bị tráo, và đổi tên đích: quan hệ của đề không được dựng dưới tên đích, mà được dựng nguyên vẹn (cùng loại, cùng toán hạng) dưới một tên không có trong đề |
| UNVERIFIED | Một trong ba: điểm đề giới thiệu mà không đọc được quan hệ (cách nói ngoài từ vựng); quan hệ đọc được nhưng dựng bằng phép khác ba loại trên; danh tính mơ hồ hoặc đích nhận không ghim |
| AUXILIARY | Đích không có trong đề và không thay cho quan hệ nào của đề: phép dựng phụ trợ của hệ. Điểm mang `source.binding = "AUXILIARY"` trong cảnh và không bao giờ là dữ kiện đề cho |
| OUT_OF_SCOPE | Điểm đề giới thiệu với vai trò ngoài từ vựng W18 (giao điểm, trọng tâm, tâm, điểm đối xứng), dựng bằng phép khác ba loại trên. Hành vi cũ giữ nguyên (giới hạn khai) |
| NOT_REALIZED | Quan hệ của đề không ứng với phép dựng nào. Chỉ ghi |

Điểm MATCHED mang `source.binding = "TEXT_RELATION"`.

> **Đính chính 2026-10-04 (W18 Task 2).** Phán quyết ghi vào sổ của wave lúc sửa, TRƯỚC census và mọi
> phép đo; chép vào đây ở Task 8, sau lượt đo đầu, không đổi nội dung. Bảng trên
> chưa nói, hoặc nói sai, ba điểm:
> - **(i) Vai trò ngoài từ vựng W18.** Điểm đề giới thiệu với vai trò tâm, trọng tâm, trực tâm,
>   giao điểm hay điểm đối xứng là OUT_OF_SCOPE dù dựng bằng phép NÀO, kể cả `midpoint`. Theo
>   bảng gốc, "O là tâm của hình vuông ABCD" dựng (đúng) bằng `midpoint(A, C)` sẽ là UNVERIFIED và
>   bị từ chối trong U3. Giá phải trả: phép dựng sai cho các điểm này vẫn không được đối chiếu,
>   như trước W18 (giới hạn khai).
> - **(ii) Đích nhận không ghim, đầu mút thì ghim.** Đích nhận đi qua một điểm KHÔNG có trong đề
>   (điểm phụ của hệ), là mặt phẳng phương trình hay đường dẫn xuất ⇒ không ghim ⇒ UNVERIFIED.
>   Ngược lại, đầu mút trung điểm hay điểm nguồn phép chiếu ra một thực thể không có trong đề là
>   danh tính XÁC ĐỊNH (thực thể ngoài đề) ⇒ MISMATCHED. Lý do: một đường hay một mặt có thể được
>   gọi qua bất kỳ điểm nào của nó, còn một đầu mút thì không.
> - **(iii) Đỉnh không được giới thiệu.** Đỉnh đề nêu mà đề không giới thiệu như điểm dẫn xuất và
>   không có quan hệ §16.1 là OUT_OF_SCOPE, kể cả khi dựng bằng `midpoint`, `divide_segment` hay
>   `project_onto` (thường là bố cục). Toạ độ của nó do chứng chỉ W15 (C0/C1) quản, không phải
>   binding.

### 16.4 Thi hành

Chặng `construction_binding` chạy ngay sau thực thi, trước `source_invariant`. Bất biến toạ độ
`segment_division` giữ làm lưới thứ hai.

- **MISMATCHED ⇒ từ chối ở MỌI vùng.** Đây là lỗi toàn vẹn của chương trình, như U5.
  - Mã: `INPUT_NOT_GROUNDED`, `reason_code = CONSTRUCTION_NOT_TEXT_BOUND`, nguyên nhân
    CONSTRUCTION (§15.3).
  - `reason_subjects` = [quan hệ đề nêu, quan hệ chương trình dựng], viết theo ký hiệu học sinh
    (`M là trung điểm của SA`).
  - Không gửi đi sửa. Lời cho người học nêu cả hai quan hệ và không bảo sửa đề.
- **UNVERIFIED ⇒ từ chối trong vùng thi hành U3; ngoài vùng chỉ ghi trạng thái.**
  - `reason_code = CONSTRUCTION_BINDING_UNVERIFIED`, nguyên nhân UNKNOWN.
  - Lời người học: hệ CHƯA đối chiếu được phép dựng với câu của đề — không bao giờ "đề sai".
- **MATCHED / AUXILIARY / OUT_OF_SCOPE / NOT_REALIZED ⇒ đi tiếp.** Quan trắc đếm theo trạng thái.

### 16.5 Chính sách nhãn (thay quyết định U-W17-1)

- **Mặc định:** nhãn điểm, và nhãn dữ kiện đề cho (`annotation.role = given`) khả dụng ở bước
  đang xem.
- **Chọn một đại lượng:** nhãn của nó, cùng nhãn các đại lượng trong chuỗi số của nó
  (`tangNhanManh`: dữ kiện số, trung gian).
- **Chọn một vật:** nhãn các đại lượng có chủ thể là vật ấy.
- **"Hiện tất cả":** mọi nhãn khả dụng; một công tắc thay hai công tắc W17.

Khả dụng (không lộ trước) và đặt chỗ giữ luật §15.4/§15.5. Hết chỗ thì nhãn ưu tiên thấp bị ẩn;
giá trị vẫn có ở bảng chi tiết và lời giải. Không có trần số nhãn cố định.

Nhãn bấm được (chuột, Enter/Space): bấm là chọn đại lượng. Backend phát
`annotation.role ∈ {given, intermediate, result}`; `category` giữ cho tương thích với envelope
v109.

> **Đính chính 2026-10-04 (W18 Task 4 và rà soát rút gọn trước đóng băng; ghi vào sổ lúc ấy, chép vào
> đây ở Task 8).**
> - Backend vẫn phát `category`, nhưng frontend không còn đọc trường này (`7a06ee47`); vai trò
>   lấy từ `role`.
> - "Hiện tất cả" và trạng thái mở lời giải là sở thích của người học, giữ qua các bài như
>   `chiTiet`. Mọi trạng thái gắn với cảnh vẫn đặt lại khi đổi bài (khoá bằng test).

### 16.6 Một nơi giải thích

- **Ô soi là bảng chi tiết của vật đang chọn.** Với một đại lượng, ô soi có công thức có tham
  chiếu, nguồn dữ kiện (dữ kiện số trong chuỗi) và phụ thuộc trực tiếp. Desktop đặt bên phải
  khung, mobile đặt dưới khung.
- **Lời giải đầy đủ thu gọn mặc định.** Khi lời giải mở, ô soi bỏ khối công thức: không hai bản
  sao cùng lúc.
- **Gộp trình bày (`annotation.same_as`).** Một khoảng cách đo giữa hai điểm, có cùng tập chủ thể
  với một độ dài đề cho đã gắn, được trình bày như dữ kiện ấy: một nhãn, một dòng. Ngoại lệ: nó
  là đáp số của đề. Giá trị bằng nhau không bao giờ là tiêu chí gộp.

> **Đính chính 2026-10-04 (W18 Task 3–4; phán quyết ghi vào sổ trước mọi phép đo, chép vào đây ở Task 8).**
> - **(i) Ký hiệu `S(T)`.** Ký hiệu ngắn cho diện tích thiết diện do server gắn, lấy tên từ bộ đọc
>   câu cắt `doc_quan_he_cat`, không lấy từ nhãn mô hình. Khi có nhiều thiết diện và chương trình
>   gọi thiết diện khác tên đề, server không gắn ký hiệu; nhãn dài giữ nguyên.
> - **(ii) Lời giải thu gọn.** Dòng Kết quả chỉ mang `ký hiệu = giá trị`, không có "Dựa trên".
>   Công thức, dữ kiện và đầu vào của đại lượng đang chọn nằm ở ô soi. Mở lời giải thì công thức
>   chuyển về lời giải, ô soi bỏ khối công thức. Chỉ đại lượng mang công thức.
> - **(iii) Bản đo trùng.** Bản đo trùng của một dữ kiện GIỮ annotation, kèm `same_as` (W17 xoá
>   nó), để bảng lời giải gộp nó vào dòng dữ kiện. Đáp số của đề không bao giờ mang `same_as`.
>   Khi hai vai trò cùng một chủ thể, mỗi vai trò giữ nhãn riêng.

### 16.7 Nhân chứng khoảng cách

- **Backend** phát nhân chứng cho khoảng cách điểm → đường và điểm → mặt phẳng:
  `annotation.witness = {from, foot (chính xác), on, marker}`, tính bằng
  `kernel.project_point_onto_line/plane`. Neo nhãn `witness` là trung điểm đoạn từ điểm tới chân.
  Ký hiệu vuông góc là hình trình bày do backend phát.
- **Frontend** vẽ đoạn, chân và ký hiệu vuông góc CHỈ khi nhãn khoảng cách đang hiện (đang chọn,
  hoặc "Hiện tất cả"). Lớp này không thêm bước dựng và không tính gì.
- **Khoảng cách khác** (hai đường, đường–mặt, hai mặt) không có nhân chứng. Giá trị ở bảng chi
  tiết, chủ thể được làm nổi, và trên hình không có nhãn. Đây là giới hạn khai.

> **Đính chính 2026-10-04 (W18 Task 3–4; phán quyết ghi vào sổ trước mọi phép đo, chép vào đây ở Task 8).**
> - **Ký hiệu vuông góc.** `marker = {u, v}` là hai vectơ hướng CHÍNH XÁC: u dọc đích nhận, v từ
>   chân tới điểm. Frontend chỉ chuẩn hoá và co về cỡ ký hiệu cố định (15% độ dài nhân chứng, tối
>   đa 0,5 đơn vị cảnh). Đó là trình bày; frontend không tính chân hay phép chiếu.
> - **Lớp nhân chứng.** Lớp này vẽ đè (không kiểm độ sâu), bằng màu "đang xét". Nó không chọn được
>   và không nằm trong kiểm khuất/hiện. Vì vậy một nhân chứng đi xuyên khối không được vẽ như nửa
>   khuất (giới hạn khai).

### 16.8 Kiểm trên trình duyệt và tiêm lỗi (đăng ký trước mọi phép đo)

**Trình duyệt:**
- **Mặc định gọn:** tập nhãn số đo đang hiện = tập dữ kiện đề cho khả dụng. Oracle độc lập đọc
  payload, không nhập module trình bày.
- **Chọn từng đại lượng** qua bảng lời giải:
  - nhãn hiện ⊇ {đại lượng} ∪ chuỗi số của nó, mỗi nhãn ≤ 24 px quanh neo đúng chủ thể;
  - ô soi có công thức;
  - đúng một vùng chi tiết mang công thức ấy.
- **"Hiện tất cả" bật → tắt → bật:** dash, vật hiện, camera, bước và lựa chọn không đổi.
- **Nhân chứng:** chọn khoảng cách có nhân chứng ⇒ đoạn tới chân xuất hiện. Không nhân chứng ⇒
  lối dự phòng đã khai.
- Giữ mọi kiểm W17: đặt chỗ, xoay, đổi cỡ, nhân quả, khôi phục, playback, tô thiết diện.

**Tiêm lỗi tối thiểu:**
- đổi SA thành SB mà giữ nguyên giá trị;
- đổi đích mà giữ nguyên toạ độ;
- bỏ kiểm binding;
- nhãn gắn sai chủ thể;
- kết quả hiện quá sớm;
- mặc định bật mọi nhãn;
- hai bảng chi tiết trùng nội dung;
- tô sáng đổi nét đứt thành nét liền.

> **Đính chính 2026-10-04 (W18 Task 7 — sau lượt đo nghiệm thu đầu tại `8caa8307`, TRƯỚC khi đo lại).**
> Lượt tiêm lỗi frontend đầu tiên bắt được 8/8 phép tiêm đơn vị và FW3. Ba phép tiêm trình duyệt KHÔNG
> bị bắt; mỗi phép chỉ ra một điểm mù của bộ đo (sản phẩm đúng, và test đơn vị bắt được cả ba lỗi):
> - **FW1 — tô sáng đổi nét.** Kiểm nét đứt của bộ đo chỉ chạy ở trạng thái nhân quả, và đại lượng đang
>   chọn ở đó không tô sáng cạnh nào, nên kiểm này rỗng. Thêm: ở MỌI bước dựng (nơi cạnh đang dựng được tô
>   sáng), mỗi đoạn sản phẩm phân loại khuất phải được vẽ nét đứt, mỗi đoạn thấy vẽ nét liền
>   (`assessDashFollowsSpans`, mã `DASH_DIFFERS_FROM_OCCLUSION`). Bằng chứng ghi các cạnh khuất được tô
>   sáng ở từng họ (`formation.dash_under_highlight`) để chứng minh kiểm không rỗng.
> - **FW2 — công tắc có tác dụng phụ.** Mốc của kiểm cô lập "Hiện tất cả" là trạng thái SAU lần bấm đầu,
>   nên một tác dụng phụ lặp ở mọi lần bấm (tua về bước 0) không lộ ra. Mốc mới là trạng thái TRƯỚC lần bấm
>   đầu; mã `SHOW_ALL_{ON,OFF,BACK}_CHANGED_*`. Ngoài ra bộ chạy từng ném lỗi và chết mà không ghi bằng
>   chứng. Nay một lượt dương ném lỗi được ghi là FAIL kèm nguyên nhân (`run_completed`, `run_error`),
>   phần đã đo được giữ lại.
> - **FW4 — hai bản công thức.** Vòng chọn chưa từng chọn một đáp số có công thức tham chiếu khi lời giải
>   đang MỞ, trong khi đó là trạng thái duy nhất có thể có hai bản công thức. Thêm `detail_region_open`:
>   đúng một vùng (dòng lời giải), ô soi bỏ khối công thức.
>
> **Đổi đích tiêm lỗi.** FW1 dự đoán `DASH_DIFFERS_FROM_OCCLUSION` (thay `dash_signature_preserved`, một
> kiểm rỗng). FW4 chạy trên một họ có đáp số mang công thức tham chiếu (`triangular_pyramid`); họ
> `cross_section` không có công thức nào như vậy. FW2 giữ nguyên dự đoán. Sản phẩm và candidate `d3b4cab9`
> không đổi. Mọi lượt đo nghiệm thu chạy lại ở commit đo mới; lượt `8caa8307` được giữ riêng làm lần thử 1.

> **Đính chính 2026-10-04 (W18 Task 7 — sau lượt trình duyệt lần thử 2 tại `0ca3accf`, TRƯỚC lượt tiêm lỗi
> frontend thứ hai).** Bằng chứng không rỗng của kiểm nét đứt theo bước (`formation.dash_under_highlight`)
> cho thấy chỉ họ `cross_section` có bước dựng tô sáng một cạnh khuất (A-B, A-D, S-A, cả hai khổ). Năm họ
> còn lại không tô sáng cạnh khuất ở bước nào, nên ở đó luật "tô sáng không đổi nét" chỉ được test đơn vị
> giữ (`scene3d-hidden-lines.test.tsx`). Vì vậy FW1 chạy trên `cross_section`/desktop (đã khai là giới
> hạn của bằng chứng trình duyệt).

## 17. W20 — đích của quan hệ dựng điểm đặt bằng toạ độ (ghi 2026-10-04, SAU bản sửa)

**Nguồn:** brief W20 (`W20_REPOSITORY_CLEANUP_AND_PREMERGE_CORRECTNESS_CLOSURE`); đóng
`ISSUE-ARCH-CONSTRUCTION-BINDING-LITERAL-TARGET`. Tái hiện và bằng chứng ở
[`runs/w20-cleanup-premerge`](../evaluation/geometry/runs/w20-cleanup-premerge/).
**Đăng ký trước bản sửa:** nhãn của probe `diagnostics/literal_target_corpus/LABELS.json` (27 hàng, `f0edcd11`, kèm
`amendment_1` cũng trước bản sửa). Mục này ghi luật SAU khi đo, không phải bản đăng ký.

Phép dò trước bản sửa (biên `run_pipeline`, 0 lượt gọi) khớp nhãn 20/27. Với đích của một quan hệ §16.1 mà chương
trình khai bằng toạ độ:
- trung điểm (mọi vùng) và hình chiếu khai bằng giả thiết mô hình (vùng U3) bị grounding ⑥/⑦ chặn sớm
  (`DERIVED_ENTITY_WITHOUT_PRODUCER`);
- hình chiếu trích fact trong U3 chỉ bị cổng giả định chặn, với mã chung;
- ngoài U3, hình chiếu đặt bằng toạ độ được PHỤC VỤ, một ca với đáp số sai (2√14 thay vì 3√6);
- toạ độ rồi mới dựng lại, bí danh `assign H = var A` (H của đề lấy trùng đỉnh A) và bí danh của một điểm đặt bằng
  toạ độ đều được PHỤC VỤ, và `construction_binding` không ghi trạng thái nào cho đích ấy.

### 17.1 Luật

- Mỗi tên chương trình mang ĐÚNG MỘT ký hiệu đích của một quan hệ §16.1 được lần theo chuỗi `assign X = var Y` tới
  gốc. Danh tính lấy theo nguồn §16.2 của riêng tên ấy, không qua nhóm bí danh, để đỉnh `A` không bị coi là `H`.
- Có khai báo toạ độ ở bất kỳ mắt nào của chuỗi ⇒ trạng thái `DEFINED_BY_COORDINATES`. Khai báo toạ độ là một
  `point3` mang giá trị không phải hạt giống (`grounding_gate._is_seed`), kể cả `declare_point` đã nâng về khai báo.
  Mắt ấy có thể là chính tên đó, hay điểm nó trỏ tới, kể cả một đỉnh đề cho.
- Có toạ độ rồi mới dựng lại vẫn tính: chương trình đã khẳng định toạ độ của một điểm đề bắt phải dựng.
- Module không đọc giá trị toạ độ, chỉ hỏi CÓ toạ độ hay không. Trùng toạ độ không bao giờ là trùng danh tính (§16.2).
- Không đổi: khai báo không kèm giá trị rồi dựng (vẫn MATCHED), bí danh của một điểm được dựng (vẫn đối chiếu theo
  §16.3), và toạ độ bố cục của các điểm không là đích quan hệ.

### 17.2 Thi hành

- Từ chối ở MỌI vùng tại chặng `construction_binding`.
  - Mã: `INPUT_NOT_GROUNDED`, `reason_code = CONSTRUCTION_REPLACED_BY_COORDINATES`, nguyên nhân CONSTRUCTION
    (§15.3). Không gửi đi sửa.
  - Thứ tự mã: `CONSTRUCTION_NOT_TEXT_BOUND` (có MISMATCHED), rồi mã này, rồi `CONSTRUCTION_BINDING_UNVERIFIED`.
    Một tên có nhiều trạng thái thì giữ MISMATCHED > DEFINED_BY_COORDINATES > UNVERIFIED > phần còn lại.
  - `reason_subjects` = các cặp [quan hệ đề nêu, việc chương trình đã làm] (`đặt H bằng toạ độ cho sẵn`,
    `lấy H trùng với điểm A`).
- Lời cho người học nêu quan hệ của đề và việc chương trình đã làm, rồi nói hệ CHƯA KIỂM CHỨNG được điểm ấy đúng là
  điểm đề nói. Toạ độ có thể đúng, nên lời không nói "hình khác", không bảo sửa đề.
- Grounding ⑥/⑦ giữ nguyên và vẫn chặn sớm hơn các ca của chúng. Gỡ một trong hai thì các ca ấy vẫn bị từ chối ở
  chặng này (tiêm lỗi FL8/FL9 của run W20).

### 17.3 Đo

- Probe sau bản sửa (`65c90bde`): 26/27 khớp nhãn. Hàng còn lại (C7) bị cổng miền của pipeline từ chối vì lý do khác,
  đã ghi ở `amendment_1` trước bản sửa; đối chứng thay thế C9 được phục vụ.
- Census W14–W18: 179 hàng so với census W18, không hàng nào đổi tuyến; luật SHIP §9 giữ (AC2 18/18).
- Quét 527 chương trình đã lưu trong kho: chỉ hàng L16 của corpus W20 vừa khai toạ độ vừa dựng cùng một điểm.
- `CACHE_VERSION` 110 → 111: sáu yêu cầu từng được phục vụ vẫn HIT dưới 110 (`PROOF_CACHE_ROW_W20.json`).

**Giới hạn:** chỉ quan hệ trong từ vựng §16.1; bí danh chỉ lần theo `assign X = var Y`. Một đích được định nghĩa bằng
phép khác (tịnh tiến, giao) đi theo §16.3 như trước.

> **Đính chính 2026-10-05.** Mã và bằng chứng W20 trước `a4f771b3` trích luật này là "§16.5". Số đó là chính sách
> nhãn của W18 (§16.5 ở trên); luật của W20 là §17. Log và output đã commit giữ nguyên chữ cũ.

> **Bổ sung 2026-10-05 (run `cuboid-final-review`) — thẻ từ chối.** Luật §17.1 và mã không đổi; đổi cách nói:
> - Vế sau của mỗi cặp `reason_subjects` viết ở thể bị động, không kèm tên điểm: `được đặt bằng toạ độ`,
>   `được lấy trùng với điểm A` (W20 viết `đặt H bằng toạ độ cho sẵn`, `lấy H trùng với điểm A`).
> - Lời cho người học: *"Hệ chưa kiểm chứng được ‹quan hệ của đề›, vì điểm này ‹cách đặt› thay vì dựng từ quan hệ
>   trong đề. Hệ tạm dừng để tránh đưa ra kết quả chưa kiểm chứng."* Tên và quan hệ đọc từ chủ thể, không viết cứng.
>   Câu đuôi "đề không cần sửa — em có thể gửi lại để hệ dựng lại" bị bỏ: chưa có cơ chế bảo đảm gửi lại sẽ sửa được.
> - Nhãn "loại vấn đề" trên thẻ: "chưa kiểm chứng được phép dựng" (frontend đọc `reason_code`, không hiển thị nó), không
>   phải "hệ dựng lệch với đề bài" — nhãn ấy chỉ dành cho ca lệch đã chứng minh (§16.4), và nhãn ấy giữ nguyên.

## 18. regular-triangular-pyramid-w01 — chóp tam giác đều, tứ diện đều, độ dài căn (đăng ký 2026-10-07, TRƯỚC mọi bản sửa)

Nhãn ghi trước: `docs/evaluation/geometry/runs/regular-triangular-pyramid-w01/diagnostics/corpus/LABELS.json` (oracle
độc lập `oracle_rtp_w01.py`). Quyết định người dùng 2026-10-07: miền hẹp ℚ³ — không khung đồng dạng, không toạ độ vô tỉ.

### 18.1 Từ vựng thêm vào §2.1

| kind | Mẫu | entities |
|---|---|---|
| `regular_triangular_pyramid` | `hình/khối chóp tam giác đều S.ABC` | (đỉnh, *đáy) |
| `base_equilateral` | phát kèm dòng trên; `đáy ABC là tam giác đều (cạnh b)?` (đáy của khối đã nêu) | (*đáy); value = cạnh khi đề viết |
| `regular_tetrahedron` | `(hình/khối)? tứ diện đều ABCD`; `chóp tam giác đều … có tất cả các cạnh (đều)? bằng a` | như `pyramid` |
| `pyramid` (thêm) | `(hình/khối)? tứ diện đều ABCD` — đỉnh là ký hiệu ĐẦU, đáy ba ký hiệu sau (xem đính chính dưới) | (A, B, C, D) |
| `edge_all` | `tứ diện đều ABCD (có)? cạnh (bằng)? a`, `tất cả các cạnh bằng a` | như khối; value = cạnh |
| `lateral_edge` · `height` | như T7, gắn khối chóp tam giác đều duy nhất | như khối |
| `base_equilateral` có value | `cạnh đáy bằng b` của khối chóp tam giác đều duy nhất | (*đáy) |
| `base_centre` (mở cho đáy tam giác) | `G là trọng tâm (của)? (tam giác)? ABC`; `O là tâm (của)? (mặt)? đáy`; `O là tâm (của)? tam giác (đều)? ABC` | (tâm, *đáy) |

> **Đính chính 2026-10-07 (trước mọi phép đo, sau lượt test hồi quy đầu).** Dòng `pyramid` (thêm) ghi lúc đăng ký là `tứ diện ABCD` (không cần "đều"). Thử trên bộ test: mọi đề tứ diện vào vùng đa diện, và ba đề tứ diện đang phục vụ (tứ diện vuông OABC, mặt cầu ngoại tiếp tứ diện, dữ kiện vô hướng) bị từ chối ở `assumption` — trái quyết định U3 (cổng chỉ từ chối trong vùng có chứng chỉ). Nay chỉ `tứ diện đều` phát `pyramid`; "tứ diện ABCD" trơn không phát gì (như trước). Hệ quả đã khai: đề tứ diện KHÔNG đều vẫn ngoài vùng đa diện, được phục vụ không cần chứng chỉ (`ISSUE-ARCH-TETRAHEDRON-OUTSIDE-POLYHEDRAL-REGION`).

Chữ "đều" của ba mẫu đầu ĐÃ ĐỌC (luật đọc trọn §7). `tam giác đều` KHÔNG BAO GIỜ thành `regular_tetrahedron`; ba cạnh
bên bằng nhau KHÔNG làm đáy đều; "tứ diện" không có "đều" chỉ là `pyramid`.

### 18.2 T8 — chóp đáy tam giác đều, chân đường cao ở trọng tâm

Nhận khi khối là `pyramid S.XYZ` và: `regular_triangular_pyramid`/`regular_tetrahedron` cùng khối; **hoặc** đáy đều
(`base_equilateral`, hoặc ba cạnh đáy có độ dài nguồn bằng nhau) **và** ba cạnh bên có độ dài nguồn bằng nhau (chân
cách đều ba đỉnh đáy ⇒ tâm ngoại tiếp ⇒ trọng tâm của đáy đều). Nguồn chiều cao (bình phương, mọi nguồn phải trùng,
khác ⇒ `TEMPLATE_CONTRADICTION T8`): `height`; độ dài nguồn S–tâm đề gọi tên; `l² − b²/3` (cạnh bên); `2b²/3` (tứ diện
đều). Cạnh bên khác nhau ⇒ mâu thuẫn. h² ≤ 0 ⇒ `TEMPLATE_NOT_MATCHED T8: degenerate height`.

Ràng buộc chính xác trên đỉnh: ba cạnh đáy bằng nhau; (S − G)·(Y − X) = (S − G)·(Z − X) = 0 với G = (X+Y+Z)/3; S ≠ G;
cạnh đáy² = b²; |SG|² = h²; mọi cạnh bên² = l² (khi đề cho). Kích thước bắt buộc: cạnh đáy, chiều cao (phản ví dụ
`vi_tu_mat`, `phap_tuyen` như T7).

**Miền biểu diễn (khai, không làm tròn):** toạ độ ở ℚ³ ⇔ b² ∈ {2k², 6k²} và h² = 3t² (k, t hữu tỉ). Hiện thực chính
tắc: N1 `X=(k,0,0), Y=(0,k,0), Z=(0,0,k)`, N3 `X=(k,−k,0), Y=(0,k,−k), Z=(−k,0,k)`; S = G + t(1,1,1). Ngoài miền ⇒
`TEMPLATE_NOT_REPRESENTABLE T8: <lý do>` ⇒ UNDETERMINED (từ chối). Tam giác đều hữu tỉ khác (b² = 2N·q², N chuẩn
Eisenstein khác 1, 3) có hiện thực nhưng không có khung chính tắc — giới hạn đã khai.

Khuôn T1–T7 không có hiện thực cho độ dài căn (khung trục toạ độ): khối của chúng gặp độ dài căn của đề ⇒
`TEMPLATE_NOT_REPRESENTABLE <khuôn>` trước mọi phép tính của khuôn (không ngoại lệ, không ép kiểu).

### 18.3 Độ dài căn của nguồn (sửa W12 cho độ dài, không cho toạ độ/tỉ số)

`k√n` (`3√2`, `√3`, `3√2/2`) là MỘT con số độ dài: bộ đọc độ dài nguồn (`MAU_DO_DAI`, các cụm `cạnh đáy/cạnh bên/
chiều cao/cạnh` của §2.1) đọc nó bằng `radical.parse_exact`; bất biến `segment_length` mang `display(...)`; hậu điều kiện
so `d² == square(giá trị)`; grounding ① so chính xác. Toạ độ điểm, hệ số mặt phẳng, tỉ số chia đoạn vẫn chỉ hữu tỉ.
Chia đoạn ② không dùng độ dài căn (không kiểm được ⇒ như trước).

### 18.4 Binding trọng tâm (mở §16.1)

`centroid(G; X, Y, Z)` đọc từ `base_centre` của §18.1 với đáy tam giác của khối duy nhất. Chương trình khớp khi G là
`intersect_line_line` của hai TRUNG TUYẾN (đường qua một đỉnh và một điểm dựng bằng `midpoint` hai đỉnh còn lại) hoặc
`divide_segment(đỉnh, trung điểm cạnh đối, 2/3)`; phép khác ⇒ MISMATCHED; trung tuyến không ghim được ⇒ UNVERIFIED.
Chân đường cao của bước dựng (`formation._tam_day_deu`) nhận đúng các phép này — theo tên, không theo toạ độ.

### 18.5 Không được

Toạ độ bố trí thành dữ kiện; nhận diện tâm bằng so toạ độ; đọc "đều" của mục tiêu chứng minh làm tiền đề (§14.2);
phục vụ khi chiều cao không xác định; nâng `product_capability` lên `supported` (mô hình chưa đo — `foundation_only`).
