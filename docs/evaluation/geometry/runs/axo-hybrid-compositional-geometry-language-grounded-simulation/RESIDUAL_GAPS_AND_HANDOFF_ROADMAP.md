# AXO HYBRID /12 — Residual Gaps & Owner Handoff Roadmap

Tài liệu tổng hợp trung thực toàn bộ **17 ca in-scope chưa hoàn tất** (`88/105 = 0.8381`, thiếu `2` ca để đạt ngưỡng `0.85`), **`6` ca bất định `VD01..VD06`**, sự cố chọn mẫu kịch bản UI `I05`, và các gói bàn giao quyền sở hữu đã chuẩn bị sẵn. Tuyệt đối không vá ngược mã sản phẩm hay chạy lại trên tập `V12` sau khi đã xem kết quả.

---

## 1. Taxonomy of the 17 Uncompleted In-Scope Cases

| Nhóm nguyên nhân gốc | Số lượng | Case IDs | Chi tiết chẩn đoán | Tầng cần xử lý (Wave sau) |
| --- | --- | --- | --- | --- |
| **G1 — Tứ diện có ba cạnh xuất phát từ đỉnh không cùng một ký tự (`KE, EF, EG` / `OM, ON, OP`):** `LOCAL_SLM_GROUNDING_REJECTED` (`AMBIGUOUS_FACT`) | **4** | `V027`, `V047`, `V098`, `V104` | Câu dạng *"tứ diện O.MNP có OM, ON, OP đôi một vuông góc"* (hoặc *"KE, EF, EG đôi một vuông góc"* ở `V098`): SLM extractor/parser chưa ánh xạ ổn định quan hệ `perp` từng cặp hoặc chọn nhầm mặt trích dẫn khiến `slm-grounding-validator/6` từ chối an toàn (`AMBIGUOUS_FACT`, `0` wrong-served). | `local_geometry_parser.py` + `local_slm_extractor.py` (tách cụm ba cạnh đôi một vuông góc) |
| **G2 — Giá trị không neo đúng cạnh/mặt (`UNGROUNDED_VALUE`, `verification_gap`):** SLM hạ sai vai cạnh hoặc gán nhầm cạnh bằng cạnh khác | **4** | `V006`, `V030`, `V070`, `V088` | Ví dụ: *"KF vuông góc với đáy và KF = 2"* (`V006`), *"hai mặt bên (KEF) và (KEG) cùng vuông góc với đáy, tam giác EFG đều cạnh a và KE = 2a"* (`V030`, `V088` tương tự với `HM = 3`), hoặc *"chiều cao bằng 4; tính độ dài cạnh bên HM"* (`V070`). Mô hình trích sai quote/slot (`UNGROUNDED_VALUE`), Source Gate chặn an toàn. | Source Gate / SLM compact slot alignment + normalizer cho *"hai mặt bên ... cùng vuông góc với đáy"* & *"chiều cao bằng X"* khi đi kèm mục tiêu phụ |
| **G3 — Tiền đề hợp lệ bị bỏ sót ở Source Gate (`SOURCE_PREMISE_UNREAD`, `verification_gap`)** | **4** | `V031`, `V032`, `V033`, `V067` | Các câu phức hợp như *"biết rằng tam giác ABC vuông tại B ...; đường thẳng PB vuông góc với (ABC) ... Không cần tính toán, hãy vẽ hình"* (`V031`), *"gọi I là trung điểm của đoạn LL' để hiển thị thêm điểm I"* (`V032`), *"lăng trụ tam giác ... có cạnh bên KK' vuông góc với đáy"* (`V033`), *"Biểu diễn đường cao KE và hình chóp ... rồi tính thể tích"* (`V067`). Source Gate hoặc extractor bỏ sót một mệnh đề liên kết mục tiêu hiển thị / lồng câu. | `registry.py` (`Source Gate` đuôi mục đích `"để hiển thị..."`, `"Biểu diễn <cạnh> và <khối>"`) + `local_slm_extractor.py` |
| **G4 — Parser nhận đủ cấu trúc nhưng đụng giới hạn `PARSER_COMPLETE` ở Backend / Bridge** | **2** | `V008` (`CONDITIONAL_CLAUSE`), `V072` (`BRIDGE_UNSUPPORTED_MEASUREMENT`) | `V008` dùng từ nối `"với MN = 3, MP = 4"` làm Source Gate nhận nhầm vào vùng `_CAU_DIEU_KIEN`; `V072` hỏi đồng thời *"tính diện tích tam giác MNP cùng thể tích khối lăng trụ"* (`ask_area` mặt đáy chưa được Bridge `/2` nối vào goal đa mục tiêu). | `registry.py` (guard `"với <cạnh>=..."` không phải điều kiện) & `TypedFactNextBridge /2` (`ask_area` trên đáy đã dựng) |
| **G5 — Các trường hợp đơn lẻ khác (`MISSING_DIMENSION`, `REPLAY_SOURCE_IDENTITY_MISMATCH`, `QUESTION_CONTEXT_UNSUPPORTED`)** | **3** | `V029`, `V040`, `V062` | `V029` (hình thoi + `góc NMP = 60°` + hai mặt cùng vuông góc, SLM sót một độ dài -> `MISSING_DIMENSION`); `V040` (đề không dấu với hai mặt vuông góc đáy -> SLM trả `REPLAY_SOURCE_IDENTITY_MISMATCH`); `V062` (hình thoi góc `60°` + vẽ biểu diễn kèm tính thể tích -> `QUESTION_CONTEXT_UNSUPPORTED`). | SLM ASCII-quote mapper (`_orig_quote_slm` với câu dài 2 mặt vuông góc) + Source Gate ngữ cảnh hỏi |

> **Nhận xét quan trọng:** Chỉ riêng việc xử lý nhóm `G1` (`đôi một vuông góc` trên tứ diện) hoặc nhóm `G3`/`G4` (`với <cạnh>=...`, `để hiển thị...`) có thể vượt xa khoảng cách 2 ca (`88 -> 90/105 = 85.7%`), cho thấy hệ không có lỗ hổng kiến trúc hay sai số toán học mà đang dừng bảo thủ tại các mẫu câu phức hợp còn lại.

---

## 2. Underdetermined Diagnostic `VD01..VD06` & UI Scenario `I05`

- Trong `6` ca bất định chẩn đoán:
  - `VD01, VD02, VD06` (lập phương, tứ diện đều, chóp tứ giác đều chỉ-mô-phỏng không nêu độ dài cạnh): đúng như báo cáo P7 §17 ([`SIMULATION_GOAL_SEMANTICS_REPORT.md`](SIMULATION_GOAL_SEMANTICS_REPORT.md)), `planner.py` / `engine.py` bị khóa theo `A4` nên từ chối với `capability_gap / MISSING_DIMENSION` (`UNPROVED_DUE_TO_CAPABILITY_GAP`).
  - `VD03, VD04` (thiếu 1 kích thước giữa đáy và chiều cao trên chóp vuông / lăng trụ đều): `capability_gap / AMBIGUOUS_FACT`.
  - `VD05` (đáy tam giác vuông tại B không cạnh, `PA ⊥ (ABC)`): `insufficient_specification / MISSING_DIMENSION` (`PROVED_UNDERDETERMINED`).
- **`I05` trong `v12_ui_scenarios.mjs` (`9/10` pass):** Kịch bản `I05` tự động chọn ca đầu tiên khác `SERVE` là `VD01`, dẫn đến UI hiển thị thông báo hệ thống của §17 (*"Axo chưa hỗ trợ phép dựng này — Các giả thiết chưa cố định duy nhất hình dạng..."*) thay vì câu hỏi làm rõ `AMBIGUOUS_FACT` / `insufficient_specification` (`route-d-clarification/1`). Các ca `AMBIGUOUS_FACT` ở `VN*` và `VD05` vẫn thuộc nhóm `insufficient_specification`.

---

## 3. Latency & Owner Handoff Packages Ready

1. **SLM Uncached `p95 = 6,703 ms > 5,000 ms`:** Dù `deterministic` rất nhanh (`p50/p95 = 152.0 / 413.0 ms`), nhánh `live_slm_contributed_served` (`n=17`) có `p50/p95/max = 4,511.0 / 6,703.0 / 9,148.0 ms` trên CPU host, chủ yếu do các đề dài có lồng ghép cần 200+ token JSON compact-clause.
2. **Handoff từ P7 còn chờ Chủ sở hữu quyết định:**
   - **§17 Unit-Similarity Policy (`A4`-locked `planner.py` / `engine.py`):** đặc tả tại [`SIMULATION_GOAL_SEMANTICS_REPORT.md`](SIMULATION_GOAL_SEMANTICS_REPORT.md) + `backend/tests/geometry/test_v12_similarity_semantics_handoff.py`.
   - **§19 Derived Point `O` Provenance (`A4`-locked `engine.py`):** bản vá [`handoff/derived_point_o_provenance.patch`](handoff/derived_point_o_provenance.patch) (`git apply --check` OK) + [`DERIVED_OBJECT_PROVENANCE_HANDOFF.md`](DERIVED_OBJECT_PROVENANCE_HANDOFF.md) + `backend/tests/geometry/test_v12_point_o_provenance_handoff.py`.
   - **Chuyển đổi mặc định (`local-only-scoped` vs `live`) & `AXO CONSTRUCTION /2`:** giữ nguyên `HYBRID_ROUTE_MODE = "live"` mặc định và khóa `construction_planner/` trong `/12`; hai mảng này sẵn sàng ở wave kế tiếp khi chủ sở hữu phê duyệt.
