# Oracle Isolation Report (`AXO CONSTRUCTION /2`)

## 1. Kết quả kiểm toán cách ly Oracle (§8)

Chiến dịch tiến hành 4 lớp kiểm tra độc lập bằng `audit_proof_integrity_and_invariance_v2.py` (ghi vào [PROOF_MUTATION_TEST_RESULTS.json](PROOF_MUTATION_TEST_RESULTS.json)) và `test_axo_construction_v2_integrity_and_integration.py` (Category 17):

1. **Quét AST tĩnh toàn gói lõi (`construction_state.py`, `construction_operators.py`, `construction_search.py`, `construction_verifier.py`):**
   - Tìm `ast_oracle_parameter_hits = []` (`0` hàm nào có tham số chứa `independent_oracle`, `expected_answer`, hay `oracle_value`).
   - Toàn bộ hàm tìm kiếm (`DynamicConstructionPlanner.plan`) chỉ nhận `(frame: InitialGeometryFrame, goal_spec: GoalSpec, budget: SearchBudget)` — hoàn toàn mù trước oracle kiểm định.
2. **Thử nghiệm nhiễu oracle ngoài:**
   - Mọi đáp số do bộ giải sinh ra (`ProofGraph` SHA-256 trên `C01`: `d2ba32353460872a9154b66ff1d278cf6e9ed5e32dc8b3240bc33ae24dd5431f`) đều hoàn toàn bất biến dù evaluator gắn oracle giả hay đảo giá trị kiểm tra bên ngoài.
3. **Thử nghiệm tách mục tiêu trên cùng một `InitialGeometryFrame` (`C01` vs `solid_volume`):**
   - Cùng đầu vào tiền đề `f_c01`:
     - Với mục tiêu `distance_point_plane(A, [S, B, C])`, bộ tìm kiếm dựng chân đường cao phụ `H_A` và trả về **`a√21/7`**.
     - Với mục tiêu `solid_volume(apex="S", base=["A", "B", "C"])` trên cùng khung tiền đề đó, bộ tìm kiếm đi qua nhánh công thức thể tích trên chứng nhân đường cao sẵn có `SA ⊥ (ABC)` và trả về **`a³√3/12`**.
   - Chứng tỏ đường đi tìm kiếm và đồ thị chứng minh phụ thuộc thuần túy vào `GoalSpec` và cấu trúc hình học, không được lập trình trước theo từng ca.
4. **Không tồn tại bảng tra cứu tọa độ điểm phụ hay cấu hình giải riêng cho từng bài toán:**
   - Đã xóa bỏ hoàn toàn rẽ nhánh sớm theo `MS.sin_sq_line_plane` khỏi `_generate_candidates` trong `construction_search.py` và bảo đảm không hardcode nhãn bài/đỉnh/tọa độ/đáp số trong toàn bộ 14 module.
