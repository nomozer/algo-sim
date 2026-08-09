# SIMULATION_VS_ILLUSTRATION_CONTRACT.md

**Ba mức, một luật.** Tài liệu này định nghĩa AlgoSim gọi cái gì là *mô phỏng*,
và vạch ranh giới mà không renderer nào được bước qua. Nó là tài liệu **hợp
đồng**, không phải báo cáo trạng thái — số liệu sống ở `docs/CURRENT_STATE.md`.

Nguồn có thẩm quyền cho các bất biến được nhắc: `docs/ARCHITECTURE_MAP.md §5`.

## 1. Ba mức, phân biệt bằng AI SỞ HỮU DIỄN BIẾN

| Mức | Định nghĩa | Điều kiện đủ | Có trong AlgoSim? |
|---|---|---|---|
| **ILLUSTRATION** | hình ảnh tĩnh hoặc do sinh ra, **không** có chuyển trạng thái tất định độc lập | không | **KHÔNG được admit** |
| **STEP_VISUALIZATION** | khung hình của một `Trace` biểu diễn quá trình thực thi tất định | engine sở hữu `state k → k+1 → result` | có |
| **INTERACTIVE_SIMULATION** | như trên, **cộng** thao tác/dự đoán của học sinh mà **engine** phán quyết | thêm `predict.check` tất định hoặc what-if sinh nhánh tất định | có |

Ba mức là **thang năng lực**, không phải thang chất lượng. Một target
`STEP_VISUALIZATION` không phải bản thiếu sót của `INTERACTIVE_SIMULATION`:
nhiều cơ chế dạy tốt nhất bằng cách xem diễn biến, và bịa một câu hỏi để "có
tương tác" chính là thứ `interaction-policy.ts` gọi là **trang trí** và cấm
admit (`COVERAGE.md §2.6`).

Điều bị cấm là mức thứ nhất: **dựng hình nhìn có vẻ đúng mà không có cơ chế ở
dưới.** Tiền lệ đã ship bug thật — bài hình học được render bằng node/edge với
toạ độ **do LLM đoán**: kéo M thì E/F/P đứng yên (`CORRECTNESS.md`, mở đầu).
Đó là ILLUSTRATION đội lốt mô phỏng, và là lý do tồn tại của `capability_gap`.

## 2. PHÉP THỬ: BỎ RENDERER ĐI

Một target chỉ được gọi là mô phỏng nếu, **khi xoá sạch renderer**, engine vẫn
còn sở hữu:

```
state k  →  state k+1  →  result
```

và với target có dự đoán, thêm:

```
action A → verdict     action B → verdict
```

Ảnh chụp màn hình **không phải** bằng chứng mô phỏng. Nó là bằng chứng *trình
bày*. Bằng chứng mô phỏng là engine chạy được mà không cần ai vẽ.

Phép thử này đã có bằng chứng chạy sẵn, không phải lời hứa:
`core/algorithms.test.ts` và `generic.test.ts` gọi thẳng engine — dựng `Trace`,
kiểm từng bước và kết quả — **không render một component nào**. Suite mặc định
cũng chạy 0 API call thật (bất biến #13), nên "engine đúng" không phụ thuộc cả
mạng lẫn màn hình.

## 3. Renderer KHÔNG BAO GIỜ sở hữu sự thật thuật toán

| Thứ | Ai sở hữu |
|---|---|
| timeline · state · kết quả | **engine tất định** (bất biến #2) |
| đúng/sai thao tác học sinh | **chỉ rule tất định**; không có rule → `unsupported_to_verify` (bất biến #11) |
| vị trí ngữ nghĩa của đối tượng | engine (`GenericState.pos`, toạ độ miền 0–100) |
| bố cục · toạ độ pixel · camera | **renderer**, và cấm nằm trong state (§3b, bất biến #3) |
| chế độ 2D/3D đang xem | store — lát trình bày, **không** do LLM chọn (bất biến #16) |

Hệ quả thực thi được: **2D và 3D đọc CÙNG một state.** Không có
`simulation_id` riêng cho 3D, không fork engine. Renderer 3D được phép nội suy
hình ảnh giữa hai bước ngữ nghĩa nhưng **không bịa trạng thái trung gian** —
sự thật vẫn là bước hiện tại (bất biến #16, #18; khoá bởi `render3d.test.tsx`,
`encap-render3d.test.tsx`).

Nói cách khác: **2D và 3D không được có hai sự thật thuật toán khác nhau.**

## 4. LLM đứng ở đâu

```
NL  →  LLM trích ngữ nghĩa  →  spec ỨNG VIÊN  →  VALIDATOR / CATALOG ĐÓNG
                                                    ↓ (chỉ khi hợp lệ)
                                            ENGINE TẤT ĐỊNH  →  state/trace
                                                    ↓
                                            RENDERER (chỉ ĐỌC)
```

LLM **chỉ** được đề xuất các trường mà schema đã validate chấp nhận. Nó không
sinh layout, HTML, CSS, kết quả thuật toán, hay đáp án đúng (bất biến #1).

Cơ chế không được hỗ trợ ⇒ **`capability_gap`**, không phải "vẽ đại một hình".
Fail-closed có hai kênh bổ sung nhau chứ không dựa vào một prompt duy nhất:
`known_gap_roles()` trong representation plan, và `analysis.result_ownership`
fail-closed ở computation gate (bất biến #21). Cộng thêm mechanism ownership
gate (bất biến #23) và operand coherence ở validator hai tầng (bất biến #20).

## 5. Ngữ cảnh đổi NHÃN, cơ chế đổi HÀNH VI

Đây là điều kiện để hệ tái dụng được thay vì thành một tập bài đặt hàng riêng:

> **ngữ cảnh NL khác nhau + cùng cơ chế tính toán
> = cùng target · cùng engine · cùng chủ sở hữu biểu diễn
> ≠ dữ liệu, ≠ nhãn ngữ nghĩa.**

"Tìm điểm 8,5 trong sổ điểm" và "tìm số báo danh 189 trong danh sách đã sắp"
phải là **cùng** `algorithm.binary_search`, **không** phải hai renderer viết
tay. Spec đã validate cấp *giá trị + nhãn + ngữ cảnh*; target cấp *cơ chế*
(current · mid · bounds · relation · progress).

**Bị cấm** (§17 · anti-pattern #2): rẽ nhánh renderer theo nội dung đề —
`if (summary.includes("học sinh"))`, `if (algorithm_id === "...")`.
Renderer được tra qua `rendererFor(module, mode)`, **dẫn xuất từ hợp đồng
module**, nên hai đề khác nhau nhận về cùng một tham chiếu component.

Khoá bằng `simulations/spec-reuse.test.tsx`: ba cặp ngữ cảnh
(binary_search điểm↔số báo danh · count_if điểm↔nhiệt độ · find_max học
sinh↔lượng mưa) phải cho **cùng chuỗi kiểu sự kiện engine** và **cùng tham
chiếu renderer**, trong khi dữ liệu/nhãn phải KHÁC. Test không so pixel — nó
so **sở hữu**. Kèm một guard quét mã nguồn cấm renderer rẽ theo ngữ cảnh/định
danh, và guard đó tự kiểm bằng ba mẫu vi phạm tổng hợp trước khi tin số 0.

## 6. Phân mức hiện tại của 22 target

Suy từ **ai có bên chấm tất định**, không phải từ cảm nhận thị giác. Nguồn:
`grep -rl "predict:" simulations/domains/` → đúng ba file, cộng
`CONTEXTUAL_TOOL_CAPABILITY_MATRIX.md`.

| Mức | Số | Target |
|---|---|---|
| **INTERACTIVE_SIMULATION** (có `predict.check`) | **11** | 9 target thuật toán trực tiếp · `network.packet_routing` · `network.protocol_encapsulation` |
| **INTERACTIVE_SIMULATION** (what-if, chưa có `predict`) | **3** | `binary.decimal_to_binary` · `logic.and_gate` · `generic.rule_scene` |
| **STEP_VISUALIZATION** | **8** | `algorithm.scan` · `algorithm.bounded_control_flow` · `binary.base_conversion` · `binary.character_encoding` · `logic.boolean_dag` · `network.graph_traversal` · `tree.traversal` · `database.relational_table_query` |
| **ILLUSTRATION** | **0** | *(không được admit — đây là con số phải giữ bằng 0)* |

11 + 3 + 8 = 22.

## 7. Tuyên bố ĐƯỢC PHÉP và BỊ CẤM

Được nói: trạng thái mô phỏng là tất định; biểu diễn dẫn xuất từ state; ngữ
cảnh NL ánh xạ vào target tái dụng đã validate; thao tác học sinh được engine
chấm ở nơi có hợp đồng; 2D/3D chia sẻ cùng sự thật.

**Không** được nói: học sinh học tốt hơn · có cải thiện kết quả học tập · 3D
dạy tốt hơn 2D. Giữ nguyên `LEARNER_IMPACT_NOT_EVALUATED` và
`CURRICULUM_SUPPORT_PARTIAL` (`docs/COVERAGE.md`).
