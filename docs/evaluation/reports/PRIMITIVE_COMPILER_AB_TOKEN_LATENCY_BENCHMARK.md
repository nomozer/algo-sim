# PRIMITIVE_COMPILER_AB_TOKEN_LATENCY_BENCHMARK

> Nhánh `feat/photo-problem-to-scene` · 2026-09-20.
> START_HEAD `00ea40f` · commit đăng ký trước `d174d2b` · `main` giữ `085cae6`.
> Bằng chứng: `docs/evaluation/geometry/photo-problem-to-scene/primitive-compiler-ab-benchmark/`.
> **4 request Gemini synthesis · 0 vision · 0 analyze · 0 repair · 0 retry.**

```text
DATASET_CLASS               = DEVELOPMENT_PILOT_PAIRED_AB   (n = 4, MỘT họ hình)
COMPILER_QUALITY_PASS       = 4/4
GEMINI_FIRST_ATTEMPT_ACCEPT = 1/4
GEMINI_TOTAL_TOKENS         = 23 084      COMPILER_MODEL_TOKENS = 0
GEMINI_MEDIAN_LATENCY       = 9 978 ms    COMPILER_P50 = 0,11 ms
PRODUCT_CODE_CHANGED        = NO          CACHE_VERSION = 97 → 97
⚠️ MỘT TRỤC CỦA BỘ ĐO HỎNG — xem §3
```

## 1. Kết quả ghép cặp

Cùng bốn `RequestContract`, cùng validator/route/scene/visual gate, cùng một bộ
chấm.

| ca | compiler | Gemini | pha bác | topology | đáp số |
|---|---|---|---|---|---|
| B01 | **PASS** | REJECTED | `ROUTE_GROUNDING` / `input_not_grounded` | ✅ | ✅ |
| B02 | **PASS** | REJECTED | `PROGRAM_SCHEMA` / `SEMANTIC_PROGRAM_INVALID` | ❌ | ❌ |
| B03 | **PASS** | **ACCEPTED** | — | ✅ | ✅ |
| B04 | **PASS** | REJECTED | `ROUTE_GROUNDING` / `input_not_grounded` | ✅ | ✅ |

Ba ca Gemini bị chính **cổng của sản phẩm** bác, và **hai trong ba** (B01, B04)
có topology và đáp số **đúng** — chúng trượt ở grounding, tức chương trình không
ghim được dữ kiện về đề. Đó là `BASELINE_MODEL_REJECTION`, **không** phải "mô
hình tính sai".

Compiler: 4/4, không ca nào thất bại im lặng.

## 2. Token và độ trễ

| | Gemini | compiler |
|---|---|---|
| prompt | 15 129 | 0 |
| output | 3 405 | 0 |
| thought | 4 550 | 0 |
| **tổng** | **23 084** | **0** |
| median/ca | 5 735 | 0 |
| latency | median **9 978 ms** | p50 **0,11 ms** · p95 0,14 ms |

`SYNTHESIS_STAGE_TOKEN_REDUCTION = 100%` trên 4/4 ca compiler đạt.

⚠️ **Phải đi kèm mọi lần dẫn con số này:** đây **chỉ là tầng synthesis**; vision
và analyze **chưa** bị loại bỏ; compiler **chưa** là đường mặc định; **không**
phải mức tiết kiệm end-to-end; mẫu **bốn ca cùng một họ**; không có ý nghĩa
thống kê sản xuất.

## 3. ⚠️ Một trục của bộ đo hỏng — phát hiện SAU live

`construction_trace_ok` dùng **ngưỡng khác nhau cho hai nhánh**: compiler ≥ 10
bước dựng, Gemini ≥ 6 câu lệnh. Đó là **hai đại lượng khác nhau mang cùng một
tên**, nên nó vi phạm đúng điều kiện *"cùng một bộ chấm"* của §9.

Hậu quả đo được: **cả bốn** ca Gemini trượt trục ấy, kể cả B03 vốn đạt mọi trục
khác. Đọc nguyên `quality_pass` thì B03 bị gán nhãn `silent_quality_failure`
**oan**.

Không sửa lại được trong wave: chương trình của Gemini **không được lưu** (đúng
luật bảo mật §8), nên không chấm lại trục ấy được, và §18 cấm gửi lại request.

**Cách xử lý:** loại trục ấy khỏi phán quyết; **mọi con số ở §1–§2 tính theo
mười trục còn lại**, vốn được định nghĩa **giống hệt nhau** cho hai nhánh.
Phân loại: `MEASUREMENT_INVALID`, phạm vi **đúng một trục**.

## 4. Kỷ luật đã giữ

- **Đăng ký trước**: manifest + ground truth đóng băng bằng SHA-256 **trong
  test**, commit `d174d2b`, **trước** request đầu tiên.
- **Nhánh compiler chạy trước**: không đạt 4/4 ⇒ 0 request. Nó đạt 4/4.
- **Trần ở transport**: `CongHttp.truoc_khi_gui` chặn ngay trước `call_gemini`;
  gửi 4, chặn 0, `max_attempts=1`, không repair, không retry.
- **Tách biệt đáp án**: đáp số ở tệp riêng; compiler không import nó (quét AST);
  manifest/hợp đồng/prompt không mang đáp số; evaluator nhận đáp số như tham số.
- **Request equivalence**: dựng bằng **đúng builder sản phẩm**; system prompt và
  lược đồ **giống hệt** giữa bốn ca; chỉ khối dữ kiện khác.

## 5. Ba phép tiêm lỗi đi lọt — và đó là phần đáng giá nhất

| # | phép tiêm | vì sao lọt | bản sửa |
|---|---|---|---|
| **F2** | dùng output compiler làm cái được chấm cho nhánh Gemini | test chỉ **đếm** số chỗ gọi `cham`, mà số ấy không đổi. Benchmark khi ấy chấm compiler hai lần rồi gọi một nửa là "baseline" | quét AST: nhánh Gemini không được nhập/gọi gói compiler; nhánh compiler không được gọi provider |
| **F8** | evaluator bỏ `topology_ok` khỏi phán quyết | compiler vốn đúng topology nên phán quyết không đổi. Một trục được **tính** mà không được **dùng** là một trục không tồn tại | quét AST chính biểu thức `quality_pass`, buộc đủ mười trục |
| **F10** | lưu raw model output vào bản ghi nhánh Gemini | test rò rỉ cũ chỉ soi nhánh compiler; bản ghi Gemini chỉ sinh ra trong một lượt **live** mà bộ test không chạy | quét AST chỗ dựng bản ghi (lộ **trước** khi tiêu quota) + soi chính tệp đã ghi |

F2 là phép tiêm nguy hiểm nhất của cả wave: nó biến một benchmark A/B thành một
phép so compiler với chính nó, mà không một cổng nào đỏ.

## 6. Sản phẩm không đổi

`backend/app`, `frontend/src`, skills, schema, compiler, FactGraph, registry,
pipeline mặc định: **0 dòng**. Candidate giữ `f5d69a39…`, `CACHE_VERSION` giữ
97, `DEFAULT_MODE` vẫn `LLM_ONLY`.

## 7. Giới hạn

1. **n = 4, một họ hình.** Khoảng Wilson rất rộng; không kiểm định ý nghĩa.
2. **Một trục bộ đo hỏng** (§3) — đã loại khỏi mọi con số báo cáo.
3. **Chỉ tầng synthesis.** `END_TO_END_TOKEN_REDUCTION = NOT_MEASURED`.
4. **Baseline một lượt, không repair.** Đường sản phẩm thật cho phép ≤3 lượt sửa,
   nên 1/4 **không** phải tỉ lệ chấp nhận của sản phẩm — nó là tỉ lệ *first
   attempt*.
5. **Latency Gemini phụ thuộc mạng và tải provider** tại thời điểm đo.

```text
TOKEN_REDUCTION_EVIDENCE   = SUPPORTED_ON_FOUR_CASE_DEVELOPMENT_PILOT
TOKEN_OPTIMIZATION         = NOT_PRODUCTION_ESTABLISHED
END_TO_END_TOKEN_REDUCTION = NOT_MEASURED
STATISTICAL_SIGNIFICANCE   = NOT_ESTABLISHED
DEFAULT_ARCHITECTURE_CHANGED = NO
MERGE_ALLOWED              = NO
NEXT_ACTION                = BENCHMARK_MEASUREMENT_REPAIR
```
