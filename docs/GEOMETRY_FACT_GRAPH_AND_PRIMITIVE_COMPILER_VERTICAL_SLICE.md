# GEOMETRY_FACT_GRAPH_AND_PRIMITIVE_COMPILER_VERTICAL_SLICE

> Nhánh `feat/photo-problem-to-scene` · 2026-09-20.
> START_HEAD `771dca6` · commit mã `0b66cd0` · `main` giữ `085cae6` (không đổi).
> Bằng chứng: `docs/evaluation/geometry/photo-problem-to-scene/geometry-primitive-compiler-vertical-slice/`.
> **0 request Gemini · 0 request mạng.**

```text
GEOMETRY_FACT_GRAPH_AND_PRIMITIVE_COMPILER_VERTICAL_SLICE = PASS
SUPPORTED_FAMILY            = right_triangle_base_pyramid_volume
DEFAULT_MODE                = LLM_ONLY (không đổi)
SYNTHESIS_HTTP_REQUESTS     = 0 cho ca được hỗ trợ
CACHE_VERSION               = 97 → 97
CANDIDATE                   = b42f17f4… → f5d69a39…  (96 → 102 tệp, cây sạch)
TOKEN_OPTIMIZATION          = NOT_ESTABLISHED
```

## 1. Lát cắt làm được gì

Với họ *hình chóp đáy tam giác vuông, cạnh bên vuông góc với đáy, hỏi thể tích*:

```
RequestContract → GeometryFactGraph → eligibility → canonical layout
                → primitive calls → SemanticProgramSpec
                → validator · ir_static_check · grounding · route
                → scene builder · section normalization · visual gate
```

Route trả **`served`**, cổng trực quan **`COVERED`**, `final_memory` mang thể
tích đúng — **không một lượt gọi model nào**.

**Không DSL thứ hai.** Compiler sinh ra đúng `SemanticProgramSpec` đang dùng, nên
nó đi qua nguyên bộ cổng hiện có mà không phải nới một cổng nào. Mã nội bộ không
được miễn kiểm.

## 2. Audit đã chặn hai thiết kế sai trước khi viết mã

**① IR đã đủ.** `declare_point` · `construct_polygon` · `construct_solid` ·
`assign` + `MeasureExpr` phủ trọn họ bài. Không thiếu câu lệnh nào, nên không
có lý do đẻ primitive mới ở tầng IR.

**② `measure` là BIỂU THỨC, không phải câu lệnh.** Bản đầu dựng
`{"kind": "measure", "target_var": …}` và Pydantic bác ở tag union. Các chương
trình đã được nhận dùng `assign` + `MeasureExpr`, và `MemoryType` không có
`measure` — witness của phép đo khai `float`.

## 3. Khoảng trống hợp đồng — khai thẳng, không vá

`RequestContract` **không có biểu diễn có cấu trúc cho quan hệ vuông góc**.
`geometry_analyze.md` ghi thẳng: quan hệ có `kind="str"`, value là *"mệnh đề
đúng như đề viết"*; `SourceInvariant` chỉ có `segment_length` ·
`plane_equation` · `point_coordinate`.

Nên **độ dài** và **nghĩa vụ** đi qua đường có cấu trúc, còn **vuông góc** phải
đọc từ `InputFact.values` bằng một bộ đọc ký hiệu **từ vựng đóng**, siết hết mức:

- chỉ đọc `InputFact` — **không bao giờ** `problem_text` (`test_L` quét AST);
- ba khuôn: `X ⊥ (PQR)` · `X vuông góc (PQR)` · `… vuông tại P`;
- nhãn điểm phải **đã có** trong `source_invariants` — ký hiệu lạ không tự sinh
  ra điểm;
- mệnh đề không đọc được ⇒ cả ca rơi về `UNSUPPORTED`, **không** bỏ qua im lặng.

⚠️ Bộ đọc ấy vẫn tin một chuỗi do LLM viết. Nợ đã khai; cách trả là mở
`SourceInvariant` cho quan hệ — tức đổi bề mặt `analyze`, tức phải đo lại. Đó là
`FACT_GRAPH_CONTRACT_EXTENSION`, wave riêng.

## 4. Toạ độ không bao giờ là dữ kiện

Bố cục chính tắc: đỉnh vuông ở gốc, hai cạnh góc vuông theo hai trục độc lập,
đỉnh chóp theo pháp tuyến. **Độ dài lấy thẳng từ FactGraph, không số nào viết
cứng.** Số học là `Fraction` — chính xác.

Toạ độ ấy đi qua **`model_assumption`**, *không* qua `source_fact_id`. Gắn
`source_fact_id` vào một toạ độ là khai rằng đề đã cho con số ấy — đúng thứ cổng
grounding tồn tại để chặn, và đúng thứ `geometry_analyze.md` cấm (*"Hệ toạ độ
KHÔNG phải dữ kiện"*).

⚠️ **Đây không phải Spatial Layout Solver.** Nó là canonical construction cho
đúng một họ.

## 5. Bộ đo sai hai lần, cả hai tự bắt

| # | phép tiêm | vì sao lọt | bản sửa |
|---|---|---|---|
| **F7** | ghi toạ độ layout thành fact `GIVEN` | `test_layout_…` chỉ soi graph do **adapter** dựng; graph mà compiler tự sửa không lộ ra đâu cả. Luật *"toạ độ không bao giờ là dữ kiện"* khi ấy chỉ là lời hứa trong docstring | `kiem_xuat_xu` cưỡng chế trong `dung_graph` + hai test mới (một trong số đó quét AST cấm compiler gán nhãn `GIVEN`) |
| **F8** | cho unsupported graph sinh chương trình một phần | guard **đúng nhưng thừa**: `danh_gia_eligibility` hiện chỉ trả `binding` khi SUPPORTED, nên bỏ guard là no-op. Không test nào chứng minh guard tồn tại | `test_K_guard_…` gọi thẳng guard với `(status không hỗ trợ + binding)` |

F7 đáng giá nhất: nó cho thấy một bất biến **được viết ra** nhưng **không được
đo**. Tám phép tiêm còn lại bị bắt ngay lần đầu.

## 6. Cô lập tính năng — theo kiến trúc, không theo lời hứa

```
grep -rn geometry_compiler backend/app/ai backend/app/main.py  ⇒  RỖNG
git status  ⇒  chỉ một thư mục MỚI, không tệp sản phẩm cũ nào bị sửa
```

Chế độ mặc định vẫn `LLM_ONLY`. Đường chạy mặc định **không tham chiếu gói mới
một dòng nào**, nên parity không phụ thuộc vào việc một cờ có được đọc đúng hay
không. `CACHE_VERSION` giữ 97; năm băm model-facing không đổi.

Compiled output **không** ghi vào synthesis cache: khoá cache chưa chứa compiler
identity, nên một row do compiler sinh không phân biệt được với row do model
sinh.

## 7. Không hard-code — và được đo

`test_D` chạy lại toàn bộ với nhãn **M/N/Q/P** và khẳng định không nhãn
`S/A/B/C` nào xuất hiện. `test_E` chạy bốn bộ độ dài khác nhau, kể cả phân số
(`5/2`), và đáp số đổi **đúng theo dữ kiện**. `test_F` khẳng định đáp số kỳ vọng
**không có mặt** trong đầu vào compiler. `test_L`/`test_M` quét AST: không
`case_id`, không `problem_text`, không primitive riêng cho một bài.

## 8. Giới hạn — phải đi kèm mọi con số

1. **Một họ bài, một fixture.** Không nói được gì về tỉ lệ trên tập đề thật.
2. **Vision và analyze chưa bị loại bỏ.** Hợp đồng vẫn do LLM sinh; lát cắt chỉ
   bỏ được **lượt synthesis**. `5631` token là **tham chiếu một lượt lịch sử**,
   không phải mức tiết kiệm bảo đảm. `TOKEN_OPTIMIZATION = NOT_ESTABLISHED`.
3. **Chưa chạy lượt provider thật nào.** Compiler chưa gặp một hợp đồng do
   analyze sinh trong thực tế — fixture là hợp đồng kiểm soát.
4. **Chưa bật mặc định, và không nên bật** cho tới khi có A/B trên đề thật.
5. **Latency local không so được với provider** — không cùng điều kiện.
6. Bộ đọc quan hệ vẫn đọc một chuỗi do LLM viết (§3).

```text
TOKEN_OPTIMIZATION = NOT_ESTABLISHED
MERGE_ALLOWED      = NO
NEXT_ACTION        = PRIMITIVE_COMPILER_AB_TOKEN_LATENCY_BENCHMARK
```
