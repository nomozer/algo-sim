# Construction Goal Semantics & Error Classification (`AXO CONSTRUCTION /2`)

## 1. Phân tách triệt để 3 ngữ nghĩa trên bài toán trùng điểm (`D02: "Tính AA."`)

Trong chiến dịch `/1`, ca `D02_degenerate_coincident_points` bị gộp làm một khi Evaluator vừa chèn nhân tạo `PendingConstruction("op.connect_segment", "A", "A")` cho `Candidate B`, vừa gán nhãn kỳ vọng `CONTRADICTORY_CONSTRAINTS`, còn `Baseline A` trả về `"0a"`. Hợp đồng `/2` phân tách rõ thành 3 câu hỏi độc lập:

| Ngữ nghĩa mục tiêu | Mục tiêu hình thức (`GoalSpec`) | Ý nghĩa toán học | Kết quả chuẩn hóa trên `/2` (`construction-exact-verifier/2`) | Nhận xét về `/1` & `Baseline A` |
| --- | --- | --- | --- | --- |
| **Khoảng cách giữa 2 điểm** | `point_distance(a="A", b="A")` | Khoảng cách Euclid trong Gram metric $d(A, A) = 0$ | **`GOAL_VERIFIED` (`"0"`, `L0`–`L4 PASS`)** | `Baseline A` phục vụ `"0a"` **đúng** dưới chính sách `P_metric`; `/1` sai khi tự chèn `connect_segment(A,A)` vào `"Tính AA."`. |
| **Độ dài đoạn thẳng dựng hình** | `segment_length(a="A", b="A")` | Dựng một `Segment3` không suy biến nối $A \ne B$ | **`DEGENERATE_CONSTRUCTION`** (`failure_code = "DEGENERATE_COINCIDENT_POINTS"`) | `Baseline A` sai dưới `P_strict_segment` (`0a`); `/1` từ chối đúng hành vi nhưng đặt sai mã `CONTRADICTORY_CONSTRAINTS`. |
| **Tính nhất quán của tiền đề** | Kiến trúc `InitialGeometryFrame` | Đề bài `S.ABCD` với câu hỏi `AA` có mâu thuẫn hệ tiền đề hay không | **Nhất quán (`premises_contradictory = False`)** | Một câu hỏi suy biến (`AA`) không biến tập giả thiết khối chóp thành mâu thuẫn (`CONTRADICTORY_CONSTRAINTS`). |

## 2. Bảng phân biệt mã trạng thái thất bại (Fail-Closed Taxonomy `/2`)

| Nhóm nguyên nhân | Trạng thái `DynamicPlannerResult.status` | Bản chất | Không bao giờ nhầm thành |
| --- | --- | --- | --- |
| Thiếu dữ kiện đề bài / đỉnh mục tiêu | `MISSING_PRECONDITION` | Thiếu độ dài, góc hoặc đỉnh chưa được khai báo | `CONTRADICTORY_CONSTRAINTS` |
| Giả thiết mâu thuẫn không thể dựng hình | `CONTRADICTORY_CONSTRAINTS` | Ví dụ bất đẳng thức tam giác, cạnh bên `< R_đáy`, cạnh `<= 0` | `NO_PLAN_FOUND_WITHIN_BUDGET` |
| Phép dựng hình học suy biến | `DEGENERATE_CONSTRUCTION` | Trùng điểm trên đoạn (`DEGENERATE_COINCIDENT_POINTS`), 3 điểm thẳng hàng (`DEGENERATE_COLLINEAR_POINTS`), hai đối tượng song song (`DEGENERATE_PARALLEL_NO_INTERSECTION`) | `CONTRADICTORY_CONSTRAINTS` |
| Ngoài năng lực thư viện toán tử | `UNSUPPORTED_OPERATOR` | Mặt cầu, hình trụ/nón, cực trị quỹ tích | `GOAL_VERIFIED` |
| Hết ngân sách tìm kiếm | `SEARCH_RESOURCE_LIMIT` / `SEARCH_TIMEOUT` / `NO_PLAN_FOUND_WITHIN_BUDGET` | Hết số trạng thái, hết tường đồng hồ hoặc không tìm thấy đường chứng minh trong `SearchBudget` | **`CONTRADICTORY_CONSTRAINTS`** (khẳng định được kiểm tại `SEARCH_STRESS_BENCHMARK.json`) |
