# ALGOSIM — SIMULATION MECHANISM QUALITY AUDIT

**Lượt READ-ONLY.** Không sửa một dòng production nào. Không commit. Không gọi
live model. Không đổi catalog. Không kết luận về tác động học tập.

| | |
|---|---|
| Nhánh · HEAD | `main` · `cc449d59e603bd460ca53c771c2061a95e24fc09` |
| Working tree | sạch, trừ 2 thư mục untracked (`ui-baseline/`, `pedagogical-alignment/`) — **không đụng** |
| Family / Target | **11 / 22** |
| Nguồn canonical | `backend/scripts/catalog_runtime_matrix.py` → `registered_target_ids`, `stable_catalog_hash = 4d7c8e65e1fa421e26779ca722cde020a31ab7939a40559730c3823edf607f29` |
| Bằng chứng | `screenshots/` (69 ảnh) · `raw-observations.json` · `fixture-verify.json` |

---

## 1. Executive verdict

**A = 16 · B = 5 · C = 1 · D = 0.**

Kết luận một câu: **AlgoSim phần lớn ĐÃ vượt qua mức "trình chiếu lại trace"** —
nhưng phần vượt qua được tập trung gần như trọn vẹn ở **một renderer duy nhất**
(`ArrayView` của domain algorithm), và **đúng những cơ chế không vẽ được bằng dãy
cột thì tụt lại**: vòng lặp, hàng đợi/ngăn xếp, và thao tác "cầm một giá trị rồi
dời chỗ" của sắp xếp chèn.

Nói cách khác: chất lượng sân khấu hiện **phụ thuộc vào việc cơ chế có tình cờ
hợp với hình dạng "dãy cột" hay không**, chứ chưa phải kết quả của một luật thiết
kế áp cho mọi cơ chế. Đó là phát hiện quan trọng nhất của lượt này.

Không có target nào ở mức D. Target duy nhất ở C là `generic.rule_scene`, và nó ở
đó **đúng theo thiết kế** (`result_authority = representation`), không phải lỗi.

---

## 2. Phân biệt engine / visualization / simulation

Ba thứ này bị lẫn với nhau rất dễ, nên nói rõ trước khi chấm:

| | Câu hỏi kiểm | Trạng thái ở AlgoSim |
|---|---|---|
| **A. Engine correctness** | state/timeline có đúng không? | **Đã có và đã được khoá bằng test** trên cả 22 target. Lượt này KHÔNG kiểm lại. |
| **B. Execution visualization** | UI có phát lại trace không? | Có ở **22/22**: dòng mã giả sáng, số đổi, bảng mở dần, con trỏ bước. |
| **C. Mechanism simulation** | học sinh có **nhìn thấy** đối tượng, hành động, thay đổi, và lý do chọn bước kế tiếp không? | **16/22**. |

Điểm mấu chốt: **B đúng không chứng minh C**. `algorithm.bounded_control_flow` có
engine đúng, timeline đúng, narration đúng từng bước — và vẫn không cho học sinh
thấy vòng lặp *là* cái gì. Ngược lại `logic.and_gate` chỉ có **một** khung, không
timeline, nhưng cơ chế thì nhìn phát ra ngay.

Vì vậy audit này **không** dùng tiêu chí "có engine + Tiến/Lùi = mô phỏng tốt".

---

## 3. Phương pháp quan sát

- Chrome thật (headless) qua CDP, desktop **1440×1000**.
- Mỗi target: **nạp fixture → chụp trạng thái đầu → bấm `Tiến` THẬT tới ~40%
  timeline → chụp → bấm `Đến cuối` THẬT → chụp**; target có tương tác riêng thì
  chụp thêm một ảnh sau khi tương tác.
- Store **chỉ** dùng để (a) nạp fixture ban đầu và (b) đọc state đối chiếu.
  **Không** đặt cursor/state bằng script — mọi bước đi là click chuột thật lên
  nút của sản phẩm (`Input.dispatchMouseEvent`). Số lần click thật ghi trong
  `raw-observations.json`.
- Chấm bằng **mắt trên ảnh**, không theo tên class/test/mô tả code. Dữ kiện DOM
  (diện tích sân khấu, số hình SVG, số bảng, số dòng mã giả) chỉ dùng để **định
  hướng chú ý**, không thay cho việc nhìn.

**Fixture** — ưu tiên canonical, theo ba nguồn:
13 target lấy envelope **thẳng từ `offline-catalog.ts` của chính sản phẩm**;
`bounded_control_flow` lấy nguyên `program-normalized-envelope.json` (sinh từ
backend `validate_program_config`, khoá hai chiều bằng test);
7 target còn lại dùng shape đã được validator của chính module chấp nhận
(scan · base_conversion · character_encoding · table · dag · graph · tree);
`selection_sort` nhân bản envelope `bubble_sort` rồi đổi đúng hai trường định
tuyến. **22/22 mở được, 0 lỗi** (`fixture-verify.json`) — điều kiện dừng #2 không
kích hoạt.

---

## 4. Catalog 22 target (canonical)

`algorithm.binary_search` · `algorithm.bounded_control_flow` ·
`algorithm.bubble_sort` · `algorithm.count_if` · `algorithm.find_max` ·
`algorithm.find_min` · `algorithm.insertion_sort` · `algorithm.linear_search` ·
`algorithm.scan` · `algorithm.selection_sort` · `algorithm.sum_if` ·
`binary.base_conversion` · `binary.character_encoding` ·
`binary.decimal_to_binary` · `database.relational_table_query` ·
`generic.rule_scene` · `logic.and_gate` · `logic.boolean_dag` ·
`network.graph_traversal` · `network.packet_routing` ·
`network.protocol_encapsulation` · `tree.traversal`

---

## 5. Ma trận 22 target

Năm câu hỏi, theo thứ tự: **Q1** đối tượng đang xử lý · **Q2** hành động của bước
hiện tại · **Q3** trạng thái trước/sau · **Q4** vì sao chọn bước kế tiếp ·
**Q5** nhận ra cơ chế mà không cần đọc đoạn giải thích dài.
`Y` = YES · `P` = PARTIAL · `N` = NO.

| Target | Học sinh cần hiểu gì | Biểu diễn chính hiện tại | Tương tác thật | Q1 Q2 Q3 Q4 Q5 | Mức | Vì sao | Thiếu cơ chế nào | Sửa tối thiểu |
|---|---|---|---|---|---|---|---|---|
| `algorithm.find_max` | quét một lượt, giữ giá trị lớn nhất | dãy cột + vùng đã duyệt xám + cột đang xét + cột đang giữ max | dự đoán · what-if | Y Y Y Y Y | **A** | thấy được vùng đã qua, phần tử hiện tại, biến tích luỹ, phép so sánh | — | giữ nguyên |
| `algorithm.find_min` | như trên (đối xứng) | như trên | dự đoán · what-if | Y Y Y Y Y | **A** | như trên | — | giữ nguyên |
| `algorithm.count_if` | duyệt + đếm theo điều kiện | cột thoả xanh / loại xám / đang xét xanh đậm + chip `đếm` | dự đoán | Y Y Y Y Y | **A** | phân biệt rõ "đã tính vào" với "đã loại" | — | giữ nguyên |
| `algorithm.sum_if` | duyệt + cộng dồn theo điều kiện | như count_if, tích luỹ tổng | dự đoán | Y Y Y Y Y | **A** | như trên | — | giữ nguyên |
| `algorithm.binary_search` | mỗi lần loại một nửa | nửa bị loại xám · vùng còn lại xanh nhạt · phần tử giữa đậm + dải quyết định | dự đoán · thí nghiệm phá thứ tự | Y Y Y Y Y | **A** | thấy vùng chưa xét co lại sau mỗi bước — chính là cơ chế | — | giữ nguyên |
| `algorithm.linear_search` | duyệt tuần tự tới khi khớp | dãy cột + cột đang xét + so sánh với khoá | dự đoán | Y Y Y P Y | **A−** | cơ chế đơn giản và hiện đủ | ranh giới "vùng còn lại" không vẽ (khác binary_search) | chỉnh nhẹ: làm mờ vùng đã loại |
| `algorithm.bubble_sort` | so sánh cặp kề, đổi chỗ, đuôi lớn dần | cặp kề tô đậm + ▲▲ · đuôi đã ổn định xanh | dự đoán · **kéo thả what-if** | Y P Y Y Y | **A−** | đối tượng và quyết định rất rõ | **hành động đổi chỗ** chỉ suy ra từ hai ảnh trạng thái, không được *diễn ra* | diễn tả bước đổi chỗ như một hành động (hai cột hoán vị) |
| `algorithm.selection_sort` | mỗi lượt chọn phần tử nhỏ nhất còn lại | dãy cột + phần tử đang xét + nhỏ nhất đang giữ | dự đoán | Y P Y Y Y | **A−** | dùng chung renderer mạnh của họ | ranh giới "vùng đã chọn xong" mờ hơn bubble | chỉnh nhẹ: đánh dấu vùng đã cố định |
| `algorithm.scan` | quét một lượt theo spec DSL | dãy cột + biến tích luỹ + mã giả | không có dự đoán | Y Y Y Y Y | **A−** | như find_max | thiếu nhịp dự đoán | chỉnh nhẹ (tuỳ chọn) |
| `algorithm.insertion_sort` | rút một quân ra, dời chỗ, chèn vào | dãy cột + cặp đang so + vùng đã sắp | dự đoán · kéo thả | Y P **N** Y P | **B+** | **giá trị đang cầm không có trên sân khấu**, ô trống hiện thành **số lặp lại** | "cầm một giá trị · để lại ô trống · dời sang phải · thả vào" | vẽ giá trị đang cầm tách khỏi dãy + ô trống là ô rỗng |
| `algorithm.bounded_control_flow` | điều kiện → thân → cập nhật → quay lại → dừng | **2 dòng mã giả** + 3 dòng chữ + 1 chip biến | không có | P **N** **N** P **N** | **B−** | mọi thứ về cơ chế là **chữ**; sân khấu chỉ là code được tô | quỹ đạo biến, biên dừng, **cạnh quay lại**, tích luỹ qua các lượt | thiết kế lại sân khấu (xem §8) |
| `binary.decimal_to_binary` | giá trị vị trí của từng bit | ô bit + trọng số 8·4·2·1 + đóng góp `+8 +4 +1` + tổng | **bấm từng bit** | Y Y P — Y | **A−** | quan hệ bit ↔ trọng số ↔ tổng nhìn thấy và bấm được | quy trình **đổi** 13 → 1101 (chia lấy dư) không có ở đây | nói rõ đây là mô hình trọng số; quy trình chia đã có ở `base_conversion` |
| `binary.base_conversion` | chia liên tiếp, gom số dư, đọc ngược | **bảng chia** (Phép chia · Thương · Dư · Chữ số) mọc dần + dãy đã thu | không có | P P Y Y Y | **A−** | bảng ở đây **chính là cơ chế**, không phải bảng chép kết quả | **không đánh dấu hàng đang tính** | tô hàng hiện tại (đúng như `character_encoding` đã làm) |
| `binary.character_encoding` | ký tự → code point → thập phân → nhị phân | bảng ký tự (bit ẩn tới lúc tính) + bảng chia **có tô hàng hiện tại** | không có | Y Y Y Y Y | **A−** | chuỗi biến đổi hiện đủ bốn chặng, không lộ kết quả sớm | mũi tên cho "đọc ngược" vẫn là chữ | chỉnh nhẹ |
| `database.relational_table_query` | dòng dữ liệu đi qua filter → chọn cột → sắp → lấy N → tổng hợp | bảng nguồn với **nhãn trạng thái từng dòng** (Giữ/Loại/Đang xét) + dải 5 chip tầng | không có | Y Y Y Y Y | **A−** | bảng **là** đối tượng của cơ chế; trạng thái từng dòng đổi theo bước | tầng đang chạy không nổi bật trong dải chip | chỉnh nhẹ: làm nổi tầng đang chạy |
| `generic.rule_scene` | quy tắc do AI mô tả tác động lên đối tượng | hai công tắc + một ô kết quả rời nhau | bấm công tắc | P P P — P | **C** | **không vẽ quan hệ** — không dây, không cổng; chỉ số đổi theo số | đường đi nhân–quả giữa đầu vào và đầu ra | giữ nguyên — family này khai `representation`, không phải mô phỏng cơ chế |
| `logic.and_gate` | AND chỉ ra 1 khi cả hai vào là 1 | công tắc → dây → cổng AND hình D → đèn ra + bảng chân trị | bấm công tắc | Y Y Y — Y | **A−** | mạch được vẽ đúng như mạch; bấm là thấy hệ quả | không chú giải màu | chỉnh nhẹ: chú giải tín hiệu |
| `logic.boolean_dag` | tín hiệu lan truyền qua nhiều cổng theo thứ tự phụ thuộc | **sơ đồ node-edge** + dây đổi màu theo giá trị + cổng đang tính viền xanh + `?` cho cổng chưa tới lượt | **bấm node đầu vào** (chuột + bàn phím) | Y Y Y Y P | **A−** | xem §7 | chú giải màu; xanh lá mang hai nghĩa | thêm chú giải tín hiệu |
| `network.protocol_encapsulation` | mỗi tầng thêm/gỡ phần của mình; tháo gói là quá trình ngược | hai chồng tầng (gửi/nhận) + các phân đoạn PDU thêm dần | dự đoán · 2D↔3D | Y Y Y Y Y | **A−** | thấy PDU lớn dần rồi nhỏ lại theo tầng | chiều truyền chỉ ngụ ý qua vị trí | giữ nguyên |
| `network.packet_routing` | gói tin đi từng chặng theo tuyến | 4 nút trên một tuyến + chấm gói tin ở nút hiện tại | **dự đoán chặng kế tiếp** · 2D↔3D | Y P Y Y Y | **B+** | vị trí hiện tại rõ, quyết định chặng kế đưa vào ô dự đoán | **đoạn đã đi vs còn lại không phân biệt**; không có hướng | tô đoạn đã đi, thêm hướng |
| `tree.traversal` | thứ tự duyệt do **ngăn xếp** quyết định | cây có nhãn trái/phải + node đổi màu + **cạnh đang đi được tô** | không có | Y Y P **N** P | **B+** | phần cây rất tốt; nhưng cấu trúc quyết định thứ tự thì không vẽ | **ngăn xếp chỉ là một dòng chữ** | vẽ ngăn xếp như một cột có đẩy/lấy ra |
| `network.graph_traversal` | BFS/DFS khác nhau ở **hàng đợi vs ngăn xếp** | đồ thị + node đổi màu theo trạng thái | không có | P P P **N** **N** | **B** | node đổi màu nhưng cơ chế thì nằm trong chữ | **hàng đợi chỉ là dòng chữ**; **không cạnh nào được tô** | vẽ hàng đợi + tô cạnh đang đi |

---

## 6. Nhận xét theo 11 family

1. **`single_pass_scan` / `interval_elimination` / `comparison_sort`** (10 target
   dùng chung `ArrayView`) — chỗ mạnh nhất của sản phẩm. Vùng đã xử lý, phần tử
   hiện tại, biến tích luỹ, biểu thức quyết định, ô dự đoán: đủ cả. **Đây nên
   được coi là chuẩn tham chiếu nội bộ cho các family khác.**
2. **`bounded_control_flow`** — điểm yếu rõ nhất. Xem §8.
3. **`positional_representation`** (3 target binary) — hai cách kể khác nhau cho
   *cùng một cơ chế chia lấy dư*: `character_encoding` **tô hàng đang tính**,
   `base_conversion` **không**. Cùng family, cùng phép toán, khác độ trung thực.
4. **`relational_table_query`** — ví dụ tốt cho luật "bảng có thể là sân khấu
   đúng": nhãn trạng thái từng dòng biến bảng thành nơi *nhìn thấy* dòng dữ liệu
   bị giữ/loại, không phải nơi chép kết quả.
5. **`boolean_composition`** (and_gate + boolean_dag) — cả hai vẽ mạch thật.
6. **`layered_pdu_transform`** — PDU thêm/gỡ theo tầng là cơ chế nhìn thấy được.
7. **`graph_traversal` + `tree_traversal`** — cùng một lỗ hổng: **cấu trúc
   frontier (hàng đợi/ngăn xếp) là dòng chữ**, trong khi nó chính là thứ phân
   biệt BFS với DFS. `tree` nhỉnh hơn vì có tô cạnh.
8. **`structural_progressive_representation`** (`generic.rule_scene`) — C đúng
   theo vai trò đã khai, không phải lỗi.

---

## 7. Boolean DAG — phán quyết

### **A — mechanism simulation** (mức phụ **A−**)

**Phần đã là mô phỏng:** sơ đồ node-edge vẽ đúng cấu trúc mạch; dây đổi màu theo
giá trị đang mang; cổng đang được tính có viền xanh dương; cổng chưa tới lượt
hiện `?` (không lộ đáp án sớm); ba node đầu vào **chính là control** — bấm chuột
hoặc Enter/Space đổi giá trị và engine tính lại downstream ngay trên sơ đồ.
Học sinh thấy được **tín hiệu đi từ đâu tới đâu và cổng nào đang quyết định**.

**Phần vẫn giống bảng/trình bày:** bảng "Chi tiết các cổng" lặp lại đúng thông
tin đã có trên sơ đồ (Cổng · Phép · Vào · Ra). Với mạch 3 cổng nó gần như thừa về
mặt cơ chế — giá trị của nó là *đối chiếu dạng chữ* và là
`gate_table_with_engine_outputs` trong hợp đồng authenticity.

**Chú giải màu — KHÔNG có, và màu bị quá tải.** Trên cùng một sân khấu:
xanh lá = tín hiệu 1 (dây + chữ số) **và đồng thời** = viền của cổng đầu ra;
xám = tín hiệu 0 **và** = dây chưa biết giá trị; xanh dương = cổng đang tính.
Hệ quả cụ thể nhìn thấy trong ảnh `logic-boolean_dag-2-mechanism-active.png`:
cổng `OR` có **viền xanh lá** trong khi giá trị của nó là `?` — một học sinh rất
dễ đọc thành "OR đang ra 1". **Không**, học sinh không thể tự biết xanh lá là
tín hiệu 1 hay là trạng thái/vai trò, vì không có chỗ nào nói.

**Focus outline:** không gây nhiễu ở trạng thái thường (chỉ hiện khi dùng bàn
phím, đúng ý đồ).

**Bảng "Chi tiết các cổng" có cần giữ không:** **có** — nó là yêu cầu renderer
trong hợp đồng authenticity và là đường đọc thay thế bằng chữ. Đã hạ trọng lượng
thị giác đúng mức ở bản hiện tại.

**Đã đủ để pilot chưa:** **đủ**, với một điều kiện rẻ — thêm chú giải tín hiệu
(1 = xanh lá, 0 = xám, đang tính = viền xanh dương, đầu ra = ...) và tách màu
"đầu ra" khỏi màu "tín hiệu 1". Không cần đổi engine, state hay cấu trúc.

---

## 8. Vòng lặp — phán quyết

### `algorithm.bounded_control_flow` = **B− (execution trace viewer)**, không phải mechanism simulation

Ba thứ phải tách bạch:

- **engine simulation** — có: `evaluate_condition`, `enter_branch`,
  `loop_iteration`, `assign_var` đều nằm trong trace và đã khoá bằng test;
- **execution trace viewer** — đây là thứ UI đang làm: tô dòng mã giả hiện tại,
  in "Điều kiện x <= 14 → ĐÚNG", "Chạy: vào thân vòng lặp", "Lượt lặp thứ 3", và
  một chip `x 8` ở panel Quan sát;
- **pedagogical mechanism simulation** — **chưa có**.

Bằng chứng: `screenshots/algorithm-bounded_control_flow-2-mechanism-active.png`.
Sân khấu ở bước 5/12 gồm **hai dòng mã giả** và **ba dòng chữ**. Không có một
hình nào. Học sinh không thấy `x` đã đi qua những giá trị nào, còn cách biên
`14` bao xa, vì sao vòng lặp **quay lại**, và khi nào thì dừng. Trace đúng không
cứu được điều đó — và theo đúng luật của đề bài, **không được chấm A chỉ vì trace
đúng**.

### Sân khấu tối thiểu (mô tả ý nghĩa — KHÔNG triển khai trong lượt này)

**Vòng `while` / bounded control flow**
- một **trục giá trị của biến lặp** với vị trí hiện tại và **biên dừng** đánh dấu
  rõ (ở đây: `x` hiện tại so với `14`);
- **phép kiểm tra điều kiện** hiện thành một hành động có hai ngả nhìn thấy được
  (ĐÚNG → vào thân · SAI → thoát), không phải một câu chữ;
- **bước cập nhật** hiện thành một chuyển động/mũi tên trên chính trục đó
  (`x` nhảy từ 8 → 11), để "cập nhật" là thứ *xảy ra*, không phải thứ được kể;
- **cạnh quay lại** (back edge) vẽ tường minh — đây là thứ làm vòng lặp *là* vòng
  lặp và hiện đang hoàn toàn vắng mặt;
- **lịch sử các lượt** (2 → 5 → 8 → 11 → …) giữ lại được, để thấy quỹ đạo chứ
  không chỉ giá trị hiện thời.

**Vòng `for`** (chưa có target riêng; áp dụng khi có)
- **miền giá trị** của biến lặp vẽ thành một dải rời rạc;
- **con trỏ `i`** đứng trên dải đó;
- **lượt hiện tại** và phần miền **đã đi qua / còn lại** phân biệt được;
- **thân vòng lặp** và trạng thái **tích luỹ** sau mỗi lượt;
- **hết miền → kết thúc** là một trạng thái nhìn thấy trên dải, không phải câu kết.

Chỉ tô dòng `for`/`while` **không đủ để đạt A**.

---

## 9. Top 5 ưu tiên

Lưu ý về tiêu chí: đề bài ưu tiên "hiện đang ở mức C hoặc D", nhưng **chỉ có 1
target ở C và 0 target ở D** — và target C đó (`generic.rule_scene`) ở đó đúng
theo vai trò đã khai. Vì vậy top 5 được rút từ **dải B**, xếp theo *trọng số
chương trình × khoảng cách cơ chế × nguy cơ hiểu sai*.

| Hạng | Target | Mức hiện tại | Vì sao ưu tiên | Hướng tối thiểu |
|---|---|---|---|---|
| 1 | `algorithm.bounded_control_flow` | **B−** | Cấu trúc lặp/rẽ nhánh là **T10 B16–B19**, trọng số chương trình cao nhất trong nhóm B; và đây là target duy nhất mà sân khấu **hoàn toàn không có hình**. Dữ liệu cần đã có sẵn trong trace. | trục giá trị biến + biên dừng + cạnh quay lại + lịch sử các lượt |
| 2 | `network.graph_traversal` | **B** | BFS/DFS **khác nhau ở đúng cái đang bị giấu** (hàng đợi vs ngăn xếp). Học sinh xem xong không phân biệt được hai thuật toán — nguy cơ hiểu sai cao. | vẽ hàng đợi thành cấu trúc có vào/ra + tô cạnh đang đi |
| 3 | `tree.traversal` | **B+** | Cùng lỗ hổng với #2 và cùng cách chữa → làm chung một mẫu thiết kế. Duyệt cây là nội dung THPT có neo. | vẽ ngăn xếp có đẩy/lấy ra, đồng bộ với cạnh đã tô |
| 4 | `algorithm.insertion_sort` | **B+** | **Nguy cơ hiểu sai cụ thể**: sân khấu hiện một số **lặp lại hai lần** và giá trị đang chèn **biến mất khỏi dãy**. Học sinh có thể học nhầm rằng thuật toán nhân bản phần tử. | vẽ giá trị đang cầm tách khỏi dãy + ô trống là ô rỗng |
| 5 | `network.packet_routing` | **B+** | Có neo chương trình (mạng), và khoảng cách nhỏ: chỉ thiếu phân biệt đoạn đã đi / còn lại và hướng truyền. | tô đoạn đã đi + thêm hướng |

**Không ưu tiên** vì đã đủ hoặc chỉ cần chỉnh nhẹ: toàn bộ nhóm `ArrayView`,
ba target binary, `relational_table_query`, hai target logic,
`protocol_encapsulation`.

---

## 10. Đề xuất pilot redesign đầu tiên

### `algorithm.bounded_control_flow`

Lý do chọn đúng target này chứ không phải bốn cái còn lại:

1. **Trọng số chương trình cao nhất** trong nhóm B — cấu trúc lặp là nội dung
   lõi của T10, và cả `for` lẫn `while` sau này đều đi qua chính module này.
2. **Khoảng cách lớn nhất giữa engine và sân khấu.** Engine đã có đủ sự kiện
   (`evaluate_condition` / `enter_branch` / `loop_iteration` / `assign_var`);
   sân khấu đang dùng gần như **không** một sự kiện nào trong số đó để vẽ.
   Đây là target mà *cùng một lượng dữ liệu* cho ra chênh lệch lớn nhất.
3. **Không cần mở rộng gì.** Không engine mới, không state mới, không schema,
   không capability, không family/target mới — chỉ đọc trace đã có.
4. **Kết quả dùng lại được**: mẫu thiết kế "trục giá trị + biên + cạnh quay lại"
   chính là thứ `for` sẽ cần khi có target `for`.
5. Nó cũng là target **duy nhất** rơi vào đúng mô tả mà đề bài cảnh báo: "nếu
   hiện chỉ có code/mã giả, biến và highlight thì không được chấm A".

Hai target tiếp theo: **`network.graph_traversal`** và **`tree.traversal`** (làm
chung một mẫu "frontier nhìn thấy được").
Hai target hoãn: **`algorithm.insertion_sort`** và **`network.packet_routing`**.

---

## 11. Những target giữ nguyên

`algorithm.find_max` · `algorithm.find_min` · `algorithm.count_if` ·
`algorithm.sum_if` · `algorithm.binary_search` ·
`network.protocol_encapsulation` · `generic.rule_scene` (C **đúng theo vai trò
`representation` đã khai** — không phải mục tiêu redesign).

## 12. Những target chỉ cần chỉnh nhẹ

| Target | Chỉnh nhẹ |
|---|---|
| `binary.base_conversion` | tô hàng chia đang tính (copy đúng cách `character_encoding` đã làm) |
| `binary.character_encoding` | hình/mũi tên cho "đọc ngược số dư" |
| `binary.decimal_to_binary` | nói rõ đây là mô hình **trọng số vị trí**, không phải quy trình đổi |
| `logic.and_gate`, `logic.boolean_dag` | **chú giải tín hiệu**; tách màu "đầu ra" khỏi màu "tín hiệu 1" |
| `database.relational_table_query` | làm nổi tầng pipeline đang chạy |
| `algorithm.linear_search` | làm mờ vùng đã loại |
| `algorithm.bubble_sort`, `algorithm.selection_sort` | diễn tả bước **đổi chỗ** như một hành động; đánh dấu vùng đã cố định |
| `algorithm.scan` | (tuỳ chọn) thêm nhịp dự đoán |

## 13. Những target cần thiết kế lại sân khấu

`algorithm.bounded_control_flow` (pilot) · `network.graph_traversal` ·
`tree.traversal` · `algorithm.insertion_sort`.

---

## 14. Giới hạn của audit

1. **Không phải correctness audit.** Không dựng oracle, không đối chiếu mọi con
   số, không kiểm mọi trace. Ba ghi nhận `OBVIOUS_PRESENTATION_CORRECTNESS_RISK`
   dưới đây là **thứ đập vào mắt**, không phải kết quả kiểm chứng hệ thống:
   - `algorithm.insertion_sort` — sân khấu hiện **số `7` hai lần** và giá trị
     đang chèn (`4`) **không có mặt** trong dãy. Nhiều khả năng đây là cách biểu
     diễn "ô trống trong lúc dời chỗ" chứ không phải lỗi engine, nhưng ở góc nhìn
     học sinh nó đọc thành *dữ liệu bị nhân bản và bị mất*.
   - `tree.traversal` — ở bước 9/22, cạnh được tô là **A–B** trong khi câu thuyết
     minh nói "Xong nhánh của **E** — lấy ra khỏi ngăn xếp". Cần người hiểu
     ngữ nghĩa xác nhận cạnh nào mới đúng ở bước "pop".
   - **Toàn catalog** — cùng một màu mang nghĩa khác nhau giữa các target
     (xanh lá = "đã đếm" ở `count_if`, "đã ổn định" ở `bubble_sort`, "đã thăm" ở
     `tree`, "tín hiệu 1" ở `boolean_dag`) và **không target nào có chú giải**.
2. **Không đánh giá tác động học tập.** Không có dữ liệu người học; lượt này chỉ
   nói *cơ chế có nhìn thấy được không*, không nói *học sinh có học tốt hơn không*.
3. **Một viewport.** Chấm ở desktop 1440×1000. Responsive đã được kiểm ở lượt
   `ui-baseline` trước và không kiểm lại ở đây.
4. **Fixture là mẫu, không phải toàn miền.** Mỗi target được xem với **một** cấu
   hình. Một cơ chế có thể hiện rõ với dãy 7 phần tử mà rối với dãy 100 phần tử.
5. **`selection_sort` dùng envelope nhân bản từ `bubble_sort`**, nên phần "XÁC
   ĐỊNH BÀI TOÁN" trong panel Quan sát của nó mang đề của bubble_sort. Đó là
   **giới hạn của fixture audit, không phải lỗi sản phẩm** — catalog công khai
   không có mẫu riêng cho `selection_sort`.
6. **Không chạy live model**, không đi qua đường NL → LLM → envelope. Audit này
   nói về **sân khấu**, không nói về chất lượng định tuyến.

---

## 15. Screenshot index

69 ảnh trong `screenshots/`, đặt tên `<target>-<số>-<pha>.png`
(dấu `.` trong target id đổi thành `-`).

| Pha | Hậu tố | Nội dung |
|---|---|---|
| 1 | `-1-initial` | trạng thái đầu, trước khi đi bước nào |
| 2 | `-2-mechanism-active` | sau khi bấm `Tiến` thật tới ~40% timeline |
| 3 | `-3-final` | sau khi bấm `Đến cuối` thật |
| 4 | `-4-interaction` / `-4-interaction-3d` | sau tương tác riêng (control trong sân khấu, hoặc chuyển 3D) |

Ảnh mang bằng chứng của các kết luận chính:

| Kết luận | Ảnh |
|---|---|
| Vòng lặp chỉ là code + chữ (§8) | `algorithm-bounded_control_flow-2-mechanism-active.png` |
| Chuẩn tham chiếu nội bộ — dãy cột (§6.1) | `algorithm-find_max-2-mechanism-active.png`, `algorithm-count_if-2-mechanism-active.png` |
| Loại bỏ nửa dãy nhìn thấy được | `algorithm-binary_search-2-mechanism-active.png` |
| Số lặp lại + giá trị đang cầm biến mất | `algorithm-insertion_sort-2-mechanism-active.png` |
| Bảng chia **có** tô hàng hiện tại | `binary-character_encoding-2-mechanism-active.png` |
| Bảng chia **không** tô hàng hiện tại | `binary-base_conversion-2-mechanism-active.png` |
| DAG: lan truyền + `?` + màu quá tải | `logic-boolean_dag-2-mechanism-active.png` |
| Hàng đợi chỉ là dòng chữ, không cạnh nào tô | `network-graph_traversal-2-mechanism-active.png` |
| Ngăn xếp là dòng chữ, nhưng cạnh **có** tô | `tree-traversal-2-mechanism-active.png` |
| Tuyến đi không phân biệt đã đi/còn lại | `network-packet_routing-2-mechanism-active.png` |
| Quan hệ nhân–quả không được vẽ | `generic-rule_scene-1-initial.png` |
| Trọng số vị trí bấm được | `binary-decimal_to_binary-1-initial.png` |

Dữ liệu thô: `raw-observations.json` (mỗi target: cách nạp fixture, số click
thật, dữ kiện DOM từng pha) · `fixture-verify.json` (22/22 mở được).
