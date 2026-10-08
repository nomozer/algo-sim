# BENCHMARK_MEASUREMENT_REPAIR

> Nhánh `feat/photo-problem-to-scene` · 2026-09-20.
> START_HEAD `606586b` · `main` giữ `085cae6`.
> Bằng chứng: `docs/evaluation/geometry/photo-problem-to-scene/benchmark-measurement-repair/`.
> **0 request Gemini · 0 request mạng · 0 dòng mã sản phẩm.**

```text
HISTORICAL_BENCHMARK_STATUS      = MEASUREMENT_INVALID   (KHÔNG đổi)
CORRECTED_SHARED_AXIS_EVALUATION = VALID
PAIRED_EVALUATOR_VERSION         = paired-ab-evaluator/2
TỔNG TRỤC AUDIT = 12   COMPARABLE = 11   INVALID_OTHER = 1
FULL BACKEND (worktree sạch, f68c39a) = 5481 passed · 1 skipped · 0 FAILED
CANDIDATE f5d69a39… → f5d69a39… (không đổi)   CACHE_VERSION 97 → 97
```

## 1. Lỗi nặng hơn báo cáo cũ nói

Wave trước khai `construction_trace_ok` dùng **hai ngưỡng khác nhau** (compiler
≥ 10 bước dựng, Gemini ≥ 6 câu lệnh). Đo lại cho thấy nó còn hỏng ở một tầng sâu
hơn: **vế Gemini luôn SAI, kể cả với chương trình hoàn hảo.**

`validate_semantic_program` có `model_validator(mode="before")` **nâng
`declare_point` ra khỏi `statements`**. Một chương trình đúng của họ này có **9**
câu lệnh thô, nhưng sau thẩm định chỉ còn **5**. Ngưỡng `≥ 6` vì thế **không thể
đạt** — trục ấy suy biến, không chỉ lệch.

Đó là lý do cả **4/4** ca Gemini trượt nó, kể cả **B03** vốn đạt mọi trục khác,
và bị gán nhãn `silent_quality_failure` **oan**.

Phép kiểm `test_A_ve_GEMINI_cua_truc_cu_LUON_SAI…` dựng lại đúng điều đó bằng
chính chương trình của compiler, và nó sẽ đỏ nếu chẩn đoán này sai.

## 2. Phạm vi lỗi: đúng một trục — đã chứng minh bằng máy

Quét AST hàm `cham` của bản 1: `arm` chỉ ảnh hưởng phán quyết ở **đúng một
dòng**. Mười một trục còn lại dùng chung định nghĩa, chung predicate, chung
ngưỡng. Không phát hiện bất tương xứng nào khác.

| phân loại | số trục |
|---|---|
| COMPARABLE | 11 |
| INVALID_OTHER (`construction_trace_ok`) | 1 |
| ARM_SPECIFIC_DIAGNOSTIC | 0 |
| HISTORICAL_NOT_RECOVERABLE | 0 |

## 3. Bộ chấm v2

**Luật cứng: predicate ghép cặp không nhận tên nhánh.** Hai nhánh chuẩn hoá
thành cùng một `QuanSat`; mọi trục là hàm thuần tuý trên nó. Đổi nhãn nhánh
không thể đổi phán quyết vì nhãn không đi vào hàm — và `canonical()` cố ý
**không chứa** `arm`, nên hai nhánh cùng quan sát cho JSON trùng byte.

**Ba trạng thái, không phải hai.** Thiếu dữ liệu trả `NOT_MEASURED`, không thành
`FAIL`. Một thứ không quan sát được không phải một thứ sai — gộp hai cái đó
chính là cách bản 1 biến khoảng trống thành bằng chứng.

`construction_trace_ok` được thay bằng **hai telemetry mang hai tên khác nhau**,
và chúng không vào bất kỳ phán quyết nào:

- `compiler_construction_step_count` = 11 cho cả bốn ca — **OBSERVED**;
- `gemini_semantic_statement_count` — **HISTORICAL_NOT_RECOVERABLE** (không lưu
  trong bản ghi rút gọn; không suy từ token, latency, topology hay route).

## 4. Kết quả lịch sử tính lại — chỉ từ dữ liệu còn quan sát được

| | compiler | Gemini |
|---|---|---|
| shared-axis quality pass | **4/4** | **1/4** (B03) |
| topology | 4 | 3 |
| answer | 4 | 3 |
| route servable | 4 | 1 |
| silent failure | 0 | 0 |
| trục NOT_MEASURED | 0 | 1 (`visual_gate` của B02) |

Ba ca Gemini bị chính cổng của sản phẩm bác: B01 và B04 ở `ROUTE_GROUNDING`
(`input_not_grounded`) — **topology và đáp số của cả hai đều đúng**; B02 ở
`PROGRAM_SCHEMA`.

**Đính chính duy nhất so với bản 1:** B03 `silent_quality_failure` **True → False**.

## 5. Bằng chứng lịch sử bất biến

Ghi băm 16 artifact **trước** khi sửa; 8 artifact chính bị ghim băm trong
`test_Q`. Không artifact live nào bị chạm, không tái sinh manifest hay ground
truth, không đổi token/latency/nhãn rejection. Lớp đính chính nằm ở thư mục
**riêng**, đặt cạnh.

Trạng thái lịch sử **giữ nguyên**:
`PRIMITIVE_COMPILER_AB_TOKEN_LATENCY_BENCHMARK = MEASUREMENT_INVALID`.

## 6. Token — kết luận được phép giữ

Compiler 4/4 trên trục chung, 0 token model; Gemini tiêu **23 084** token
(15 129 + 3 405 + 4 550), lấy nguyên từ artifact đã commit và khớp tổng.

```text
SYNTHESIS_STAGE_TOKEN_REDUCTION = 100% ON FOUR SUPPORTED DEVELOPMENT CASES
TOKEN_REDUCTION_EVIDENCE        = SUPPORTED_ON_FOUR_CASE_DEVELOPMENT_PILOT
```

Đi kèm bắt buộc: `END_TO_END_TOKEN_REDUCTION = NOT_MEASURED` ·
`TOKEN_OPTIMIZATION = NOT_PRODUCTION_ESTABLISHED` ·
`STATISTICAL_SIGNIFICANCE = NOT_ESTABLISHED` ·
`DATASET_SCOPE = FOUR_CASE_SINGLE_FAMILY_DEVELOPMENT_PILOT` ·
`DEFAULT_ARCHITECTURE_CHANGED = NO`.

## 7. Giới hạn

1. **1/4 không phải tỉ lệ chấp nhận của sản phẩm** — đường sản phẩm cho phép
   ≤3 lượt sửa; đây là *first attempt*.
2. **Không kết luận "Gemini chỉ đạt 1/4 chất lượng"**: hai trong ba ca bị bác có
   topology và đáp số **đúng**, chúng trượt ở grounding.
3. **`gemini_semantic_statement_count` mất vĩnh viễn** cho lượt này. Muốn so
   sánh được phải có một wave benchmark **mới, đăng ký trước**, lưu số ấy ở dạng
   rút gọn — **không** thực hiện ở đây.
4. **Bốn ca, một họ hình.** Không có ý nghĩa thống kê.
5. Wave này **không** chạy lại live, không tối ưu compiler, không đổi sản phẩm.

```text
PRODUCT_CODE_CHANGED         = NO
DEFAULT_ARCHITECTURE_CHANGED = NO
MERGE_ALLOWED                = NO
NEXT_ACTION                  = FACT_GRAPH_CONTRACT_EXTENSION
```
