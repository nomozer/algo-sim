# Gói Hướng Dẫn Xây Dựng Tập Đề Độc Lập H-1 (`H1_AUTHORING_HANDOFF`)

> **Tài liệu bàn giao độc lập cho tác giả biên soạn tập đề kiểm định mù `H-1` (60 đề hình học không gian tiếng Việt).**
> Tài liệu này được biên soạn tách biệt với nhật ký phát triển và **không chứa** bất kỳ danh sách ca lỗi hay giải thích sửa lỗi nội bộ nào nhằm bảo đảm tính mù (blindness) của phép đo.

---

## 1. Điều Kiện Độc Lập Của Tác Giả (`AUTHORING_INDEPENDENCE`)

1. **Ai được phép biên soạn:** Một cá nhân độc lập do Owner trực tiếp chỉ định (ví dụ giáo viên Toán THPT, giảng viên hướng dẫn, hoặc chính Owner nếu không tham gia chỉnh prompt/gate cho bộ đề này).
2. **Ai không được phép biên soạn:** Người trực tiếp cài đặt/tinh chỉnh hệ thống và mọi AI coding agent của kho mã nguồn này.
3. **Quy tắc cách ly thông tin trước niêm phong:**
   - Tác giả **không chạy thử** bất kỳ đề nháp nào trên AlgoSim (`LLM_ONLY` hoặc `HYBRID`) trước khi toàn bộ 60 đề và đáp án chuẩn được bàn giao, kiểm tra toàn vẹn và đóng băng mã băm SHA-256.
   - Tác giả **không sao chép, trích xuất hoặc biến thể** từ bất kỳ tập đề, bài test, fixture, tập thăm dò (probe) hay tài liệu nào đã có trong kho mã nguồn AlgoSim.
   - **Cấm tái sử dụng trá hình:** Không lấy một đề có sẵn rồi chỉ đổi tên đỉnh (`S.ABCD` → `P.MNPQ`), nhân/chia tỉ lệ số đo, hoặc viết lại câu chữ tương đương rồi tính là đề mới.
   - Tác giả không xem danh sách lỗi phát triển hoặc chi tiết các bản vá nội bộ trước khi hoàn tất bộ đề.

---

## 2. Quy Mô & Cấu Trúc Phân Tầng Bắt Buộc (60 Đề)

Bộ đề `H-1` gồm đúng **60 bài toán tiếng Việt**, chia thành hai nhóm cố định theo giao thức đã đăng ký trước:

### 2.1. Nhóm A — 45 bài khả giải (`expect = "SERVE"`)

Phản ánh cách học sinh lớp 11–12 tại Việt Nam thực sự nhập đề hình học không gian trong phạm vi sản phẩm đã công bố:

- **Số liệu cụ thể:** Mọi kích thước cho bằng số tường minh (số nguyên, phân số hoặc căn thức chính xác như `2`, `3/2`, `2√3`). **Không dùng tham số chữ** kiểu `"cạnh a"`, `"bán kính R = a√2"` vì hai nhánh hệ thống quy ước đơn vị tham số khác nhau.
- **Không kèm hình ảnh:** Đề văn bản thuần túy, tự đủ dữ kiện; viết tiếng Việt chuẩn có dấu (bao gồm lối viết tự nhiên của học sinh như `SA ⊥ (ABCD)`, `mp(SBC)`, `k/c`, `đt`, `vuông góc với đáy`). Không viết đề gõ hoàn toàn không dấu tiếng Việt.
- **Yêu cầu định lượng:** Mỗi bài phải hỏi **ít nhất một đại lượng số chính xác** thuộc tập khóa `oracle` ở Mục 4. Không đưa vào bài **chỉ yêu cầu dựng/vẽ hình mà không hỏi đại lượng số**, và không đưa vào bài yêu cầu **chứng minh** (`"Chứng minh rằng …"`).
- **Độ phủ họ hình học (mỗi họ tối thiểu `≥ 3` bài):**
  1. Hình chóp đa giác (`pyramid`: chóp tam giác, tứ giác, chóp đều, tứ diện vuông/đều).
  2. Hình lăng trụ (`prism`: lăng trụ đứng, lăng trụ đều, lăng trụ xiên có hình chiếu đỉnh).
  3. Hình hộp chữ nhật / hình hộp (`cuboid`).
  4. Hình lập phương (`cube`).
  5. Mặt cầu (`sphere`: mặt cầu độc lập hoặc mặt cầu ngoại tiếp / nội tiếp khối đa diện, tiếp xúc mặt phẳng).
  6. Hình trụ tròn xoay (`cylinder`: thể tích, diện tích xung quanh, bán kính, thiết diện qua trục hoặc song song đáy).
  7. Hình nón tròn xoay (`cone`: thể tích, diện tích xung quanh, bán kính, đường sinh – chiều cao, thiết diện, tỉ số thể tích / phần còn lại khi cắt bởi mặt phẳng song song đáy).
- **Độ phủ loại câu hỏi (mỗi nhóm tối thiểu `≥ 3` bài):**
  - `section_measure`: diện tích thiết diện cắt bởi mặt phẳng (hoặc bán kính đường tròn giao tuyến với mặt cầu/trụ/nón).
  - `distance`: độ dài đoạn thẳng, khoảng cách điểm–đường, điểm–mặt, hai đường chéo nhau, đường–mặt song song, hai mặt song song.
  - `angle`: góc giữa hai đường thẳng, đường thẳng và mặt phẳng, góc nhị diện / hai mặt phẳng (ghi giá trị chính xác theo `angle_cos_sq` hoặc `angle_cos`).
  - `volume`: thể tích khối đa diện / khối tròn xoay, tỉ số thể tích (`volume_ratio`), thể tích phần còn lại (`residual_volume`).
  - `area`: diện tích tam giác/đa giác, diện tích xung quanh hình trụ/hình nón, diện tích mặt cầu (`lateral_area`), hoặc bán kính (`radius`).

### 2.2. Nhóm B — 15 bài kiểm tra từ chối an toàn & làm rõ (`expect = "REFUSE"`, phân bố `5 / 5 / 5`)

Chia chính xác **5 bài cho mỗi lớp**:

1. **`OUT_OF_DOMAIN` (5 bài — ngoài phạm vi hỗ trợ đã công bố):**
   - Ví dụ: hình học giải tích tọa độ `Oxyz` (phương trình mặt phẳng/mặt cầu/đường thẳng theo tọa độ), bài toán tìm giá trị lớn nhất / nhỏ nhất (cực trị hình học), bài toán quỹ tích / tập hợp điểm chuyển động, hình chóp cụt độc lập, hoặc bài toán đại số / giải tích / vật lý ngoài hình học không gian.
   - **Không dùng** câu hỏi `"Chứng minh …"` làm bài `OUT_OF_DOMAIN`.
2. **`CONTRADICTORY_DATA` (5 bài — dữ kiện tự mâu thuẫn toán học):**
   - Ví dụ: độ dài âm hoặc bằng `0`; ba cạnh đáy vi phạm bất đẳng thức tam giác; hình vuông cạnh `2` nhưng đường chéo bằng `5`; hai giả thiết cùng quy định chiều cao/cạnh dẫn đến hai giá trị khác nhau; mặt phẳng vừa cắt vừa tiếp xúc cùng một mặt cầu tại khoảng cách mâu thuẫn với bán kính; đường sinh hình nón ngắn hơn chiều cao.
3. **`MISSING_DATA` (5 bài — thiếu dữ kiện hoặc mơ hồ chưa đủ xác định duy nhất đáp số):**
   - Ví dụ: cho đáy hình chữ nhật mới biết một cạnh mà hỏi thể tích; cho hình chóp chưa chỉ rõ chân đường cao hay góc nghiêng của cạnh bên; nói `"điểm M nằm trên cạnh SB"` không cho tỉ số mà hỏi diện tích thiết diện phụ thuộc vị trí `M`; mặt phẳng đi qua 2 điểm chưa xác định duy nhất thiết diện.

---

## 3. Quy Ước Ngữ Nghĩa Cho Câu Hỏi Thiết Diện & Mục Tiêu

Để bộ chấm ba tầng (Mathematical / Semantic Goal / Strict Contract) đối chiếu nhất quán mà không cần đoán ý sau khi chạy:

- **Dạng 1 — Câu hỏi gộp hai mệnh lệnh tường minh:**
  > *"Xác định thiết diện của hình chóp cắt bởi mặt phẳng (P) và tính diện tích thiết diện đó."* (hoặc dùng động từ tường minh *"Tìm thiết diện … và tính …"*, *"Dựng thiết diện … rồi tính …"*).
  - Trong `semantic_annotations.explicit_goals`, ghi rõ cả hai mục tiêu người học yêu cầu: `["construct_plane_section", "area"]`.
- **Dạng 2 — Câu hỏi chỉ hỏi đại lượng số:**
  > *"Tính diện tích thiết diện của hình chóp cắt bởi mặt phẳng (P)."*
  - Trong `semantic_annotations.explicit_goals`, chỉ ghi `["area"]` (việc dựng giao tuyến là bước trung gian nội bộ).
- **Không hỏi chung trong cùng một bài:** Không hỏi đồng thời `volume` (thể tích toàn khối) cùng với `volume_ratio` hoặc `residual_volume` trong cùng một đề; hãy tách thành các bài riêng biệt để tránh nhập nhằng giữa đại lượng mục tiêu và đại lượng trung gian.

---

## 4. Quy Tắc Đáp Án Chuẩn Độc Lập (`oracle`)

1. **Nguồn tính toán độc lập bắt buộc:**
   - Mọi đáp số trong `oracle` phải do tác giả tính **bằng tay** hoặc kiểm tra bằng công cụ đại số máy tính độc lập ngoài kho mã nguồn (ví dụ SymPy/GeoGebra/Mathematica viết riêng bởi tác giả) **trước mọi lần chạy hệ thống**.
   - **Tuyệt đối cấm** lấy kết quả từ AlgoSim `HYBRID`, cấm lấy kết quả từ `LLM_ONLY`, và cấm dùng Gemini tự chấm lời giải của chính nó làm oracle duy nhất.
2. **Ngữ pháp biểu thức chính xác (`radical.parse_exact`):**
   - Chỉ chấp nhận chuỗi biểu thức chính xác: số nguyên (`"12"`), phân số tối giản (`"8/3"`), căn bậc hai rút gọn (`"√3/4"`, `"2√6/3"`), bội số của `π` (`"36π"`, `"32π/3"`), hoặc tích của `π` với căn bậc hai.
   - **Cấm số thập phân xấp xỉ** (`"2.67"`, `"113.097"`): bộ kiểm định sẽ từ chối ngay khi kiểm tra định dạng.
   - **Thứ tự bắt buộc khi có cả `π` và `√`:** Viết `π` **trước** dấu căn: `"4π√2"` hoặc `"4π√3/3"` (**không** viết `"4√2π"`).
   - **Mỗi giá trị phân biệt trong cùng một khóa chỉ liệt kê một lần:** Nếu đề hỏi hai khoảng cách và cả hai đều bằng `12`, ghi `{"distance": ["12"]}`; nếu một bằng `2` và một bằng `√6`, ghi `{"distance": ["2", "√6"]}`.
3. **Danh mục khóa `oracle` hợp lệ duy nhất:**
   - `"distance"`: độ dài đoạn thẳng và mọi loại khoảng cách.
   - `"angle_cos_sq"`: giá trị $\cos^2\varphi$ chính xác của góc $\varphi$ được hỏi (ví dụ góc $30^\circ \Rightarrow$ `"3/4"`, góc $60^\circ \Rightarrow$ `"1/4"`), hoặc dùng `"angle_cos"` nếu đề yêu cầu trực tiếp $\cos\varphi$.
   - `"volume"`: thể tích khối đa diện hoặc khối tròn xoay.
   - `"area"`: diện tích đa giác, diện tích mặt hoặc diện tích thiết diện (kể cả thiết diện hình tròn có `π`).
   - `"lateral_area"`: diện tích xung quanh của hình trụ / hình nón **và diện tích mặt cầu** ($4\pi R^2$). *(Lưu ý: không hỏi `"diện tích toàn phần"` của hình trụ hoặc hình nón vì cả hai nhánh hệ thống không xuất khóa chấm riêng cho đại lượng gộp này; hãy hỏi diện tích xung quanh, thể tích hoặc bán kính).*
   - `"radius"`: bán kính mặt cầu / đáy trụ / đáy nón / đường tròn giao tuyến.
   - `"volume_ratio"`: tỉ số hai thể tích.
   - `"residual_volume"`: thể tích phần khối còn lại.

---

## 5. Định Dạng File JSON Bàn Giao (`schema = "hybrid-master-paired-heldout/2"`)

> [!WARNING]
> **Cấm sao chép hoặc biến thể từ ví dụ minh họa dưới đây:**
> Hai câu đề mẫu `H1-S01` và `H1-R01` bên dưới **đã nằm công khai trong kho mã nguồn AlgoSim**. Tác giả **tuyệt đối không** đưa nguyên văn hai câu này vào `h1-independent-corpus.json`, và **tuyệt đối không** chỉ đổi tên đỉnh/mặt phẳng (`S.ABCD` → `P.MNPQ`, `(P)` → `(Q)`) hoặc đổi số đo (`4` → `6`, `3` → `5`) trên cùng khung câu chữ. Bộ kiểm định niêm phong tự động quét cả trùng khớp nguyên văn (`exact_overlap_cases`) lẫn trùng khớp khung cấu trúc đã che nhãn đỉnh/số đo (`structural_template_clones`) và sẽ chặn không cho niêm phong bộ đề.

File bàn giao đặt tên `h1-independent-corpus.json` (mã hóa `UTF-8`, không chứa trường `dry_run`), tuân thủ cấu trúc tương thích ngược hoàn toàn với bộ chạy kiểm định bắt cặp và bổ sung đầy đủ trường kiểm toán độc lập:

```json
{
  "schema": "hybrid-master-paired-heldout/2",
  "author": "<Họ tên và vai trò của tác giả độc lập>",
  "author_affiliation": "<Đơn vị / trường / vai trò>",
  "authoring_independence": "ESTABLISHED",
  "written_before_any_system_run": true,
  "independence_evidence": "<Cam kết ngắn gọn: tự biên soạn mới 100%, giải độc lập bằng tay/SymPy ngày YYYY-MM-DD, không truy cập kho đề phát triển và chưa chạy thử trên AlgoSim>",
  "cases": [
    {
      "id": "H1-S01",
      "problem_text": "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 4, cạnh bên SA vuông góc với mặt phẳng đáy và SA = 3. Gọi M là trung điểm của cạnh SB. Mặt phẳng (P) đi qua M và song song với mặt phẳng (ABCD). Xác định thiết diện của hình chóp S.ABCD cắt bởi (P) và tính diện tích thiết diện đó.",
      "expect": "SERVE",
      "oracle": {
        "area": ["4"]
      },
      "premise_sentences": [
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 4, cạnh bên SA vuông góc với mặt phẳng đáy và SA = 3.",
        "Gọi M là trung điểm của cạnh SB.",
        "Mặt phẳng (P) đi qua M và song song với mặt phẳng (ABCD)."
      ],
      "stratum": {
        "family": "pyramid",
        "question": "section_measure"
      },
      "expected_capability": "polyhedron_parallel_section_and_area",
      "semantic_annotations": {
        "explicit_goals": ["construct_plane_section", "area"],
        "requires_auxiliary_section_construction": true
      },
      "oracle_derivation": "M là trung điểm SB nên tỉ số đồng dạng k = SM/SB = 1/2. Thiết diện là hình vuông đồng dạng với đáy ABCD theo tỉ số k = 1/2 => S_td = (1/2)^2 * 4^2 = 4.",
      "rationale": "Kiểm tra bài toán chóp tứ giác kết hợp xác định thiết diện song song đáy và tính diện tích.",
      "author": "<Tên tác giả>",
      "provenance": "Biên soạn mới độc lập ngày YYYY-MM-DD, giải tay + kiểm chéo đại số độc lập."
    },
    {
      "id": "H1-R01",
      "problem_text": "Cho hình chóp S.ABC có đáy ABC là tam giác với AB = 2, BC = 3, AC = 7 và SA vuông góc với (ABC), SA = 4. Tính thể tích khối chóp S.ABC.",
      "expect": "REFUSE",
      "refusal_class": "CONTRADICTORY_DATA",
      "expected_capability": "fail_closed_triangle_inequality",
      "expected_clarification_or_refusal_note": "Từ chối do AB + BC = 5 < AC = 7 vi phạm bất đẳng thức tam giác, đáy ABC không tồn tại.",
      "rationale": "Kiểm tra tính an toàn fail-closed trước tam giác đáy bất khả.",
      "author": "<Tên tác giả>",
      "provenance": "Biên soạn mới độc lập ngày YYYY-MM-DD."
    }
  ]
}
```

---

## 6. Checklist Tự Kiểm Trước Khi Tác Giả Gửi Lại Cho Owner

- [ ] Tổng số đề đúng **60** (`id` duy nhất, không có hai `problem_text` trùng nhau).
- [ ] Đúng **45** đề `expect = "SERVE"` và đúng **15** đề `expect = "REFUSE"` gồm **5** `OUT_OF_DOMAIN`, **5** `CONTRADICTORY_DATA`, **5** `MISSING_DATA`.
- [ ] Mọi họ hình (`pyramid`, `prism`, `cuboid`, `cube`, `sphere`, `cylinder`, `cone`) và mọi nhóm câu hỏi đều có ít nhất `3` bài `SERVE`.
- [ ] Không có câu `"Chứng minh …"`, không có bài chỉ dựng hình không hỏi đại lượng, không có tham số chữ `"cạnh a"`, không có số thập phân xấp xỉ, và mọi đáp số chứa cả `π` lẫn `√` đều viết `π` trước `√`.
- [ ] Mọi `oracle` đều có `oracle_derivation` giải độc lập; mọi bài đều có `provenance` rõ ràng; không chép nguyên văn hay đổi tên đỉnh/số đo từ ví dụ trong tài liệu này hoặc bất kỳ đề có sẵn nào; không đề nào từng được chạy qua AlgoSim trước khi niêm phong.
