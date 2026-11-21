# Simulation-intent generalization: design (P2)

## Vấn đề

Học sinh viết "Hãy mô phỏng hình chóp S.ABCD.", "Vẽ hình hộp chữ nhật đó.", "Chỉ cần vẽ hình, không cần tính toán.",
"Cho mình xem hình lập phương ABCD.A'B'C'D' giúp em." để xin **chỉ dựng hình**. Ở /10, ba tầng đọc câu loại này theo
ba văn phạm khác nhau, và văn phạm nào cũng hẹp:

- parser luật 7b chỉ nhận vài cụm cố định;
- Source Gate (`_VAT_MO_PHONG`) chỉ nhận `mô phỏng hình (chóp|lăng trụ)`;
- GBNF của SLM không có nhánh "không hỏi gì", nên buộc mô hình phải sinh một mục tiêu số hoặc `u`.

Cùng một câu vì thế có thể được parser đọc nhưng bị Source Gate từ chối, hoặc ngược lại.

## Thiết kế: một văn phạm, ba người đọc

**Parser** (`local_geometry_parser.py`, `0557dcaf6`). Văn phạm dựng từ bốn phần có tên, dùng chung cho luật 7b và cho
kiểm phủ mệnh đề con (`_SUBCLAUSE_SHOW_RE`):

- `_SIM_VERB`: vẽ · dựng · mô phỏng · minh hoạ · biểu diễn · hiển thị · cho (mình|em|tôi|tớ) xem. Tiền tố tuỳ chọn
  em/bạn · hãy · chỉ cần; hậu tố tuỳ chọn giúp (…) · lại.
- `_SIM_SOLID`: (hình|khối)? + chóp | lăng trụ | hộp (chữ nhật)? | lập phương | tứ diện, kèm bổ ngữ đứng/đều/xiên/tam
  giác/… và nhãn tuỳ chọn `S.ABCD` / `ABC.A'B'C'`.
- `_SIM_FIGURE`: hình (vẽ|3D|không gian|ba chiều)? (theo giả thiết (trên|đã cho))?
- `_SIM_OBJECT`: SOLID | FIGURE, kèm chỉ định tuỳ chọn này/đó/đã cho/trên, "và các điểm M, N", và đuôi không nội dung
  ", không cần tính toán" / "giúp em".

`_SIM_REQUEST_RE` = động từ + đối tượng. Phần câu hỏi đi sau là tuỳ chọn (", rồi tính …" / "và tính …"). Phần đó được
đọc bằng luật hỏi sẵn có, **không** bằng văn phạm này.

**Chọn đích** (`_sim_request_target`), quyết định tất định:

1. Có nhãn ⇒ nhãn phải bằng **đúng** tập đỉnh của một khối đã khai. Không khớp ⇒ không có đích (từ chối, không đoán).
2. Chỉ có loại khối ⇒ chọn khối **duy nhất** thuộc lớp chóp/lăng trụ đó. Có hai khối cùng lớp ⇒ không có đích.
3. Chỉ "hình" trần ⇒ chọn khối chính. Nhưng nếu đề khai nhiều khối mà câu dùng từ chỉ định ("hình đó") ⇒ không có đích.

**Phủ mệnh đề**: hai kiểm phủ (`_unread_subclauses` và kiểm giá trị chưa đọc) nay so trên **toàn bộ**
`builder.simulation_goals` thay vì lát `[pre3[2]:]`. Lát cũ rỗng sau khi luật 7b thay danh sách, khiến "Chỉ cần vẽ
hình, không cần tính toán" bị gắn cờ `UNREAD_SUBCLAUSE`.

**Source Gate** (`registry.py`, `806a7d338`, owner duyệt **chỉ** `_VAT_MO_PHONG`):

- nhận cùng tập danh từ khối, bổ ngữ và nhãn;
- `_MO_YEU_CAU_MO_PHONG` cho tiền tố (không|chưa|chỉ) cần;
- `_DUOI_MO_PHONG` đọc đuôi không nội dung.

Ràng buộc an toàn: danh từ khối hoặc bổ ngữ cụ thể chỉ được chấp nhận khi `_loai_cum_dung(...)` xác nhận cụm đó khớp
**loại** và **ký hiệu** (`_ky_hieu_khoi`) của một lời gọi dựng khối đã kiểm. "Mô phỏng hình lập phương" trên đề khai
hình chóp ⇒ không đọc được ⇒ từ chối. Ngoài đúng văn phạm này, Source Gate không được nới thêm chỗ nào.

**SLM** (`local_slm_extractor.py`, `fcf68e91b`, `local-slm-extractor/5`):

- `is_simulation_only_source` đúng khi không mệnh đề nào khớp `_GOAL_VERB_RE` **và** có một yêu cầu `_SIM_REQUEST_RE`.
- Khi đó GBNF bỏ lối lùi `_GOAL_MARKERS`, và gốc văn phạm thành
  `{"s":…,"r":[…],"g":[],"u":[]} | {"s":…,"r":[""],"g":[],"u":[unres]}`. Mô hình không thể bịa mục tiêu số, và chỉ báo
  "chưa rõ" khi không đọc được dữ kiện nào.
- Lowering: đề chỉ-mô-phỏng nhận 0 mục tiêu (`mg_status = "SIMULATION_ONLY"`). Trích dẫn `construct_object` là
  **khoảng mệnh đề yêu cầu** (`simulation_request_span`), không phải mệnh đề khai báo. Cue góc vuông là
  `vuông( cân)? (tại|ở) <đỉnh>` khi mệnh đề có cụm đó.

## Bất biến được kiểm

- Không đọc câu phủ định ("Không mô phỏng…", "Đừng dựng…") thành yêu cầu (N01, N02).
- Không chọn khối khi nhãn lạ (N07 `M.PQR`), khi hai khối cùng lớp, hay khi chỉ định nhập nhằng (N08).
- Không thêm mục tiêu cho đề chỉ-mô-phỏng (an toàn: "fabricated math goal on SIMULATE_ONLY = 0").
- Kiểm biến đổi giữ nghĩa (metamorphic): đổi động từ hay đuôi lịch sự không đổi kết quả. Riêng "!" không có trong tập
  này, vì Source Gate (khoá) chưa nhận dấu chấm than làm cuối câu.

Test: `PARSER_GENERALIZATION_TEST_RESULTS.json` (parser 31, Source Gate 34, hợp đồng SLM 6; ngoại tuyến, 0 lượt AI).
