# CONTEXTUAL_TOOL_CAPABILITY_MATRIX — 22/22 target

**Đây là bằng chứng QUY HOẠCH KIẾN TRÚC TƯƠNG TÁC, không phải bằng chứng học
tập.** `LEARNER_IMPACT_NOT_EVALUATED` · `CURRICULUM_SUPPORT_PARTIAL`.

Chụp tại `0a71268`. Ma trận này **không** được triển khai trong cùng wave sinh ra
nó (§8 của đề bài) — nó là căn cứ để quyết định wave sau.

## Luật phân loại — đọc trước khi dùng bảng

Cột **"ai kiểm định"** quyết định mọi thứ khác. Trong kho mã này, bên chấm
đúng/sai tất định là **`SimulationModule.predict.check`**. Tra thật (`grep -rl
"predict:" simulations/domains/`) cho đúng **ba** file:

| File | Target được cấp `predict` |
|---|---|
| `domains/algorithm/index.ts` | **9** target thuật toán trực tiếp |
| `domains/network/index.ts` | `network.packet_routing` |
| `domains/network/encap.ts` | `network.protocol_encapsulation` |

⇒ **11/22 target có bên chấm tất định.** 11 target còn lại có `apply` (thao tác
đổi state) nhưng **không có** `predict`. Theo §5, thiếu bên kiểm định thì
**không được** gắn `EXPERIMENT_READY` — dù UI có vẽ được nút hay không.

`OBSERVE_ONLY` **không phải khuyết điểm**: nhiều cơ chế dạy tốt nhất bằng cách
xem diễn biến, và bịa một câu hỏi để "có tương tác" chính là thứ
`interaction-policy.ts` gọi là **trang trí** và cấm admit.

## A. Chín target thuật toán trực tiếp

`decision.ts` sở hữu ba mô hình tương tác: `scanInteractionOf` ·
`searchInteractionOf` · `sortInteractionOf`. Cả ba **không** mang `correctActionId`
/ `evidence` — đáp án chỉ sống trong `predict.check`.

| # | Target | Cơ chế học chính | Quan sát phải nói được | Thao tác hiện có | Ai kiểm định | Thí nghiệm có nghĩa? | Kiểu tương tác | Sẵn sàng | Wave đề xuất | Căn cứ |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `algorithm.find_max` | bất biến "chỉ nhớ tốt nhất đã gặp" | đang xét · max hiện tại · đã duyệt · quan hệ | cam kết (Scan) + kéo what-if | `predict.check` | **có** | commitment + what-if | **IMPLEMENTED — VERIFIED** | — (xong) | pilot W4B-2B, browser 17/17 |
| 2 | `algorithm.find_min` | như trên, cực trị ngược | đang xét · min hiện tại · đã duyệt · quan hệ | cam kết (Scan) + kéo what-if | `predict.check` | **có** | commitment + what-if | **EXPERIMENT_READY** | W4B-2C | cùng `runFindExtreme`; đã hưởng bản vá cue ở `9d56f18` |
| 3 | `algorithm.count_if` | biến đếm có điều kiện | đang xét · vị từ · đếm hiện tại · tiến độ | cam kết (Scan); **kéo `hidden`** | `predict.check` | **có** | commitment | **EXPERIMENT_READY** | W4B-2C | `scanInteractionOf` cấp nhãn "Đếm X vào nhóm"/"Bỏ qua"; policy `hidden` vì đếm bất biến theo thứ tự duyệt |
| 4 | `algorithm.sum_if` | biến tích luỹ có điều kiện | đang xét · vị từ · tổng hiện tại · tiến độ | cam kết (Scan); **kéo `hidden`** | `predict.check` | **có** | commitment | **EXPERIMENT_READY** | W4B-2C | như trên, nhãn "Cộng X vào tổng"/"Bỏ qua" |
| 5 | `algorithm.linear_search` | CHI PHÍ phụ thuộc vị trí đích | đang xét · đích · số lần so sánh | cam kết (Search) + kéo `framed` | `predict.check` | **có** | commitment + what-if | **EXPERIMENT_READY** | W4B-2D (họ tìm kiếm) | `searchInteractionOf`; policy `framed` |
| 6 | `algorithm.binary_search` | tiền điều kiện "dãy đã sắp" | vùng còn lại · vùng bị loại · mốc giữa | cam kết (Search) + kéo `challenge` | `predict.check` | **có** | commitment + what-if | **EXPERIMENT_READY** | W4B-2D | đã có `challengeLabel` phá tiền điều kiện |
| 7 | `algorithm.bubble_sort` | đổi chỗ kề nhau | cặp đang so · phần đã sắp | cam kết (Sort) + kéo `free` | `predict.check` | **có** | commitment + what-if | **EXPERIMENT_READY** | W4B-2E (họ sắp xếp) | hai cột NGANG VAI — cue vai trò của find_max **không** áp được |
| 8 | `algorithm.selection_sort` | chọn cực trị của phần chưa sắp | ranh giới chưa sắp · ứng viên | cam kết (Sort) + kéo `free` | `predict.check` | **có** | commitment + what-if | **EXPERIMENT_READY** | W4B-2E | `sortInteractionOf.kind = select-candidate` |
| 9 | `algorithm.insertion_sort` | dời chỗ tới vị trí chèn | quân đang giữ · ô trống · vùng đã sắp · so sánh | cam kết (Sort) + kéo what-if | `predict.check` | **có** | commitment + what-if | **IMPLEMENTED — VERIFIED** | — (xong) | pilot W4B-2B, browser 17/17 |

## B. Mười ba target còn lại

| # | Target | Cơ chế học chính | Quan sát phải nói được | Thao tác hiện có | Ai kiểm định | Thí nghiệm có nghĩa? | Kiểu tương tác | Sẵn sàng | Wave đề xuất | Căn cứ |
|---|---|---|---|---|---|---|---|---|---|---|
| 10 | `algorithm.scan` | quét dãy tổng quát do đề khai | phần tử đang xét · biến tích luỹ | timeline | **không có `predict`** | chưa — chưa có điểm quyết định khai báo | — | `NEEDS_ENGINE_CONTRACT` | sau W4B-2E | `scan-module.tsx` không khai `predict` |
| 11 | `algorithm.bounded_control_flow` | luồng điều khiển: gán · rẽ nhánh · lặp có biên | câu lệnh đang chạy · giá trị biến · nhánh được chọn · số lượt | timeline | **không có `predict`** | **có tiềm năng** — "điều kiện này ĐÚNG hay SAI?" là quyết định thật của cơ chế | prediction | `NEEDS_ENGINE_CONTRACT` | wave riêng | engine ĐÃ có `evaluate_condition` + `enter_branch`; thiếu `DecisionPoint`/`predict` |
| 12 | `binary.decimal_to_binary` | trọng số vị trí | bit · hàng trọng số · giá trị dựng dần | bật/tắt bit (`apply`) | không có `predict` | có tiềm năng — "bit này 0 hay 1?" | what-if | `WHAT_IF_READY` | sau họ sắp xếp | `apply` có, `predict` không |
| 13 | `binary.base_conversion` | chia lấy dư | phép chia · số dư · kết quả dựng dần | timeline | không có `predict` | có tiềm năng — "số dư bước này là mấy?" | prediction | `NEEDS_ENGINE_CONTRACT` | wave riêng | `divideSteps` đã tất định; chưa khai điểm quyết định |
| 14 | `binary.character_encoding` | ký tự → mã → thập phân → nhị phân | từng mắt xích của chuỗi ánh xạ | timeline | không có `predict` | có tiềm năng, hẹp | prediction | `NEEDS_ENGINE_CONTRACT` | wave riêng | dùng lại `toBase`; chưa có `DecisionPoint` |
| 15 | `logic.and_gate` | bảng chân trị của cổng | đầu vào · đầu ra · dây | bật/tắt đầu vào (`apply`) | không có `predict` | **thao tác ĐÃ là cơ chế** — cổng Thí nghiệm sẽ chỉ làm khó | what-if | `WHAT_IF_READY` | không cần gác | bài khám phá, không timeline |
| 16 | `logic.boolean_dag` | lan truyền tín hiệu qua mạch | giá trị từng cổng theo bước | bật/tắt đầu vào (`apply`) | không có `predict` | **có tiềm năng cao** — "đầu ra cổng này sẽ là gì?" | prediction | `NEEDS_ENGINE_CONTRACT` | wave riêng | sân khấu đã giấu đầu ra bằng "?" (dag.test.tsx) ⇒ nửa đầu của vòng dự đoán đã có |
| 17 | `network.packet_routing` | chọn chặng kế tiếp | đỉnh · cạnh · gói tin · đường dựng dần | **cam kết (`predict`)** | **`predict.check`** | **có** | prediction | `EXPERIMENT_READY` | sau các họ thuật toán | `network/index.ts` khai `predict` |
| 18 | `network.graph_traversal` | biên (frontier) của BFS/DFS | hàng đợi/ngăn xếp · đã thăm · biên | timeline | **không có `predict`** | có tiềm năng — "nút kế tiếp rời biên là nút nào?" | prediction | `NEEDS_ENGINE_CONTRACT` | wave riêng | `traverse-module.tsx` không khai `predict` |
| 19 | `network.protocol_encapsulation` | đóng/mở gói qua từng tầng | chồng tầng hai đầu · PDU dày/mỏng dần | **cam kết (`predict`)** | **`predict.check`** | **có** | prediction | `EXPERIMENT_READY` | sau các họ thuật toán | `encap.ts` khai `predict`; Z = tầng giao thức (bất biến #18) |
| 20 | `tree.traversal` | thứ tự duyệt theo biến thể | gốc · trái/phải · ngăn xếp hoặc hàng đợi · đã thăm | timeline | **không có `predict`** | **có tiềm năng cao** — "nút nào được thăm tiếp?" | prediction | `NEEDS_ENGINE_CONTRACT` | wave riêng | executor khung ngăn xếp đã tất định; chưa khai `DecisionPoint` |
| 21 | `database.relational_table_query` | lọc · chọn cột · sắp xếp | bảng nguồn · vị từ · kết quả | timeline | **không có `predict`** | có tiềm năng — "hàng này có qua bộ lọc không?" | prediction | `NEEDS_ENGINE_CONTRACT` | wave riêng | claim hiện tại chỉ VERIFIED cho truy vấn 1–2 tầng |
| 22 | `generic.rule_scene` | cảnh do LLM soạn trong DSL | đúng đối tượng/luật mà đề khai | `apply` theo `EditPolicy` | không có `predict` | **CHỈ** theo luật đã validate — không được bịa | what-if / edit | `WHAT_IF_READY` | không mở rộng | authenticity vẫn PARTIAL; §5 cấm nghĩ ra tương tác ngoài hợp đồng |

## C. Tổng hợp

| Lớp | Số | Target |
|---|---|---|
| **IMPLEMENTED — VERIFIED** | 2 | `find_max` · `insertion_sort` |
| **EXPERIMENT_READY** | 9 | `find_min` · `count_if` · `sum_if` · `linear_search` · `binary_search` · `bubble_sort` · `selection_sort` · `packet_routing` · `protocol_encapsulation` |
| **WHAT_IF_READY** | 3 | `decimal_to_binary` · `and_gate` · `generic.rule_scene` |
| **NEEDS_ENGINE_CONTRACT** | 8 | `algorithm.scan` · `bounded_control_flow` · `base_conversion` · `character_encoding` · `boolean_dag` · `graph_traversal` · `tree.traversal` · `relational_table_query` |
| **OBSERVE_ONLY thuần** | 0 | mọi target đều có ít nhất điều khiển timeline |

> 2 + 9 + 3 + 8 = **22**. Số EXPERIMENT_READY (9) khớp đúng với số target có
> `predict` (11) trừ hai target đã triển khai — không phải trùng hợp: **có bên
> kiểm định tất định là điều kiện cần và đủ để vào lớp này**.

## D. Ba điều bảng này KHÔNG nói

1. **Không nói tương tác giúp học tốt hơn.** Nó chỉ nói cơ chế nào có bên kiểm
   định tất định để một cam kết của học sinh được chấm mà không cần LLM.
2. **`NEEDS_ENGINE_CONTRACT` không có nghĩa "sắp làm".** Mở một `DecisionPoint`
   mới là mở hợp đồng engine mới, phải duyệt riêng theo `RULES §3`.
3. **Không đề xuất nào ở đây được triển khai trong wave sinh ra bảng.**
