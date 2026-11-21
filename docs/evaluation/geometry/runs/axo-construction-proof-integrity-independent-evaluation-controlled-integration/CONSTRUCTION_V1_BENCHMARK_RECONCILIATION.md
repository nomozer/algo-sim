# Construction /1 Benchmark Reconciliation (`AXO CONSTRUCTION /2`)

## 1. Tính bất biến của bằng chứng `/1`

Xác minh bằng `verify_v1_run_immutability()` trong `reconcile_and_compare_construction_v2.py`:
- **Số hiện vật `/1` được kiểm tra:** **`16/16` files** trong `docs/evaluation/geometry/runs/axo-construction-verified-graph-dynamic-planner-feasibility/`.
- **`v1_immutability.intact`:** **`True`** (`mismatches = []`). Không có byte nào của `/1` bị sửa; mọi đối chiếu sai lệch đều thực hiện qua Correction Layer tại wave `/2`.

## 2. Đối soát điểm số 40 ca dưới hai chính sách ([CONSTRUCTION_V1_METRIC_RECONCILIATION.json](CONSTRUCTION_V1_METRIC_RECONCILIATION.json))

| Hệ thống | Báo cáo lịch sử `/1` | Chính sách `P_metric` (`d(A,A)=0` hợp lệ) | Chính sách `P_strict_segment` (`AA` từ chối dựng đoạn) |
| --- | --- | --- | --- |
| **Baseline A** | `32/40` | **`33/40`** *(`D02` trả `"0a"` là đúng với khoảng cách 2 điểm)* | **`32/40`** *(`D02` phục vụ `"0a"` không từ chối dựng đoạn suy biến)* |
| **Candidate B (`/1`)** | `40/40` | **`39/40`** *(/1 chèn ép `connect_segment(A,A)` vào `"Tính AA."`)* | **`40/40` hành vi** *(từ chối đúng nhưng gán nhãn chưa chuẩn `CONTRADICTORY_CONSTRAINTS` thay vì `DEGENERATE_CONSTRUCTION`)* |
| **Candidate C (`/2`)** | — | **`40/40`** *(chọn `point_distance` -> `"0"`, L0–L4 PASS)* | **`40/40`** *(từ chối `DEGENERATE_CONSTRUCTION: DEGENERATE_COINCIDENT_POINTS`)* |

## 3. Phân rã 6 cờ trực giao cho 33 ca dương (`/1` `auxiliary_count > 0` = `26/33` vs `0` = `7/33`)

- Tuyên bố cũ `/1` gộp chung *"33/33 có witness construction"*, dù số ca thực sự có `auxiliary_count > 0` trong chính dữ liệu `/1` là **`26/33`** (`7/33` ca bằng `0` gồm các ca độ dài/thể tích trực tiếp + `E03` bản xếp hạng 1 dùng khoảng cách đường chéo sẵn có trước `Plan #2`).
- Bộ phân loại 6 cờ độc lập `/2` trên `33` ca dương tách bạch hoàn toàn:
  - `VERIFIED_GRAPH`: **`33`**
  - `HAS_CONSTRUCTION_WITNESS`: **`33`** *(bao gồm sửa lỗi `A07_angle_sc_base_square` giữ lại khóa `seg_C_A` trong `witness_keys`)*
  - `HAS_EXPLICIT_DEPENDENCY_CHAIN`: **`33`**
  - `ANSWER_VERIFIED_WITHOUT_AUXILIARY`: **`8`**
  - `HAS_AUXILIARY_OBJECT_HISTORICAL_V1_FIELD`: **`26`**
  - `HAS_GENUINE_IMPLICIT_AUXILIARY_OBJECT`: **`16`** *(ca tìm đối tượng phụ chưa nêu rõ trong đề như chân `H_A`, đường truyền `∥`, tia nhị diện)*
  - `HAS_MULTI_PLAN_ALTERNATIVES`: **`13`** *(`5/5` ở `Group E` + các ca khoảng cách/nhị diện ở `Group B, C`)*

## 4. Tái phân loại đa nhãn `N0`–`N5` cho 28 `CASE_B` của `/1` ([CONSTRUCTION_NOVELTY_RECLASSIFICATION.json](CONSTRUCTION_NOVELTY_RECLASSIFICATION.json))

- `N0_EXISTING_COMPLETE_RECIPE`: **`4`** (`A01, A05, A06, A08`)
- `N1_EXPLICIT_CONSTRUCTION_SCHEDULING`: **`12`** (chỉ sắp lịch/dựng các điểm/đối tượng đề bài đã gọi tên: `A02..A04, A09, B01, B02, B06..B10, C08`)
- `N2_OPERATOR_COMPOSITION`: **`22`** (tổ hợp chuỗi nhiều toán tử không có công thức sẵn hoàn chỉnh)
- `N3_IMPLICIT_AUXILIARY_DISCOVERY`: **`17`** (`A07, B03..B06, C01..C07, E01..E05` — search tự khám phá hình chiếu/đoạn chứng nhân hoặc chiến lược phụ chưa có trong `Arm A2`)
- `N4_ALTERNATIVE_VERIFIED_STRATEGY`: **`14`** (nhiều chiến lược chứng minh độc lập cùng về 1 đáp án chính xác)
- `N5_UNSUPPORTED_CAPABILITY`: **`1`** (`D06`) · `NEGATIVE_REFUSAL`: **`6`** (`D01..D05, D07`)
