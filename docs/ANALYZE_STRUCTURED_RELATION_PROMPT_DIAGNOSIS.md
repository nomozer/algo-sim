# ANALYZE_STRUCTURED_RELATION_PROMPT_DIAGNOSIS

> Wave **chẩn đoán**, 2026-09-21, nhánh `feat/photo-problem-to-scene`.
> **0 request model · 0 request mạng · 0 dòng mã sản phẩm · prompt không đổi.**
> Artifact: `docs/evaluation/geometry/photo-problem-to-scene/structured-relation-prompt-diagnosis/`.

```text
ROOT_CAUSE_CLASSIFICATION = PROMPT_INSTRUCTION_GAP
CAUSALITY_STATUS          = NOT_CAUSALLY_ESTABLISHED
EVIDENCE_STRENGTH         = SUPPORTED_BY_CURRENT_EVIDENCE   (n = 1)
SCHEMA_CAPABILITY_FOR_MISSING_RELATION = PRESENT
TEST_COUNT_DELTA_EXPLAINED = YES  (26 file mới + 2 parametrize)
```

## 1. Câu hỏi

Lượt live trước: mô hình khai đúng `line(S,A) ⟂ plane(A,B,C)` nhưng **không**
khai `line(A,B) ⟂ line(A,C)`, dù đề viết *"ABC là tam giác vuông tại A"* và
chính mô hình đã tạo mục `abc_tam_giac_vuong_tai_a`. Nguyên nhân thuộc loại nào?

## 2. Loại trừ trước, kết luận sau

**Schema — LOẠI.** Không đọc schema rồi suy; dựng một hợp đồng THẬT có quan hệ
ấy rồi chạy hết tầng. Mười phép kiểm, mười lần đạt:

```text
kind tồn tại · enum cho phép · arity đúng · AB ≡ BA
source_fact_id trỏ được vào abc_tam_giac_vuong_tai_a · model_assumption giữ false
Pydantic PASS · RequestContract PASS · FactGraph nhận quan hệ
compiler eligibility  UNSUPPORTED_STRUCTURED_RELATION_MISSING → SUPPORTED
```

Câu cuối là câu quan trọng nhất: **chỉ cần quan hệ ấy có mặt là cả đường ống
chạy tiếp**. Không tầng nào phải sửa.

**Ground truth và bộ chấm — LOẠI.** Quan hệ kỳ vọng đúng theo chính định nghĩa
tam giác vuông. Bộ chấm ghi `missing = 1`, `accuracy = 0.5`, và compiler từ chối
đúng nhánh `BASE_PERPENDICULAR_RELATION_MISSING`. Cả ba khớp nhau.

**Mô hình không tuân — KHÔNG kết luận được.** Nhãn ấy đòi điều kiện *"prompt đã
yêu cầu rõ và tổng quát"*, và điều kiện ấy **không đạt** (mục 3). Không đủ cơ sở
quy trách cho mô hình.

## 3. Prompt: đo được, không suy đoán

`geometry_analyze.md` tại START_HEAD, 5311 byte, băm `5746c5e5…` — đúng bản đã
gửi đi ở lượt live. Bề mặt Analyze **không** có thẻ văn phạm (`grammar_card` chỉ
được ghép ở `stage_semantic_program`; có test AST canh).

| câu hỏi | trả lời | bằng chứng |
|---|---|---|
| A. Có yêu cầu *tam giác PQR vuông tại P* → `perpendicular_lines(PQ, PR)`? | **KHÔNG** | **0 dòng** khớp `tam giác vuông\|vuông tại\|góc vuông\|90°` trong toàn bộ prompt |
| B. Có phân biệt chuẩn hoá theo định nghĩa với suy luận? | **KHÔNG** | Prompt chỉ có HAI ngăn: *"quan hệ đề NÓI"* (L36) và *"đề KHÔNG nói mà bạn tự suy"* (L34) |
| C. Ví dụ có chỉ dùng biểu thức trực tiếp? | **CÓ** | Ví dụ quan hệ ở L17 là `SA ⊥ (ABCD)`, `ABCD là hình vuông`, `M là trung điểm AB`; mục quan hệ nói *"quan hệ vuông góc **đã ghi thành câu** ở trên"* |
| D. *"Không suy diễn"* có nuốt mất phép chuẩn hoá? | **MƠ HỒ** | Đề nói *"tam giác vuông tại A"*, **không** nói *"AB ⟂ AC"*. Đọc theo mặt chữ, prompt **cho phép** xếp phép viết lại ấy vào ngăn *tự suy* |

Chỗ D đắt hơn nó trông: nếu xếp vào ngăn *tự suy* thì L34 buộc
`model_assumption = true`, mà cờ ấy làm quan hệ **vô dụng** cho tầng dựng, còn
L35 lại cảnh báo *"khai gian thì cả bài sai"*. Cả hai lối đều dẫn tới **không
khai**.

⚠️ Mọi câu trên nói về **văn bản prompt** và về **đầu ra quan sát được**. Không
có một bằng chứng nào về trạng thái nội tại của mô hình, và báo cáo này không
đưa ra phát biểu nào kiểu *"mô hình hiểu rằng…"*.

Một chi tiết đáng chú ý: `ABCD là hình vuông` **có mặt** trong prompt như một ví
dụ `input_facts`, nhưng **không** ví dụ nào cho thấy một vị từ về LOẠI HÌNH được
viết lại thành quan hệ. Khoảng trống không phải là prompt thiếu chữ; nó là prompt
thiếu **một ngăn**.

## 4. Ranh giới ngữ nghĩa — sản phẩm chính của wave

Bốn lớp, không chồng lấn (`SEMANTIC_NORMALIZATION_POLICY.json`):

| lớp | ví dụ | phải thành |
|---|---|---|
| **EXPLICIT_SURFACE_RELATION** | `AB ⟂ AC` · *góc BAC bằng 90°* | relation **GIVEN** |
| **DEFINITIONAL_NORMALIZATION** | *tam giác ABC vuông tại A* | relation **GIVEN** |
| **LOGICAL_DERIVATION** | `SA ⟂ (ABC) ⇒ SA ⟂ BC` | FactGraph sinh **DERIVED**, có parent proof |
| **LAYOUT_OR_CONSTRUCTION_ASSUMPTION** | `A = (0,0,0)` | **không bao giờ** là dữ kiện đề |

Câu hỏi phân xử, một câu: **có phải áp một ĐỊNH LÝ để ra quan hệ không?** Không
⇒ chuẩn hoá theo định nghĩa, vẫn GIVEN. Có ⇒ suy luận, việc của FactGraph.

Ma trận 13 cách diễn đạt (`WORDING_COVERAGE_MATRIX.json`) gồm cả bản tiếng Anh,
bản đổi nhãn `PMN`, và bản đảo thứ tự câu:

```text
prompt hiện tại phủ   5/13   ·  mơ hồ 1/13  ·  KHÔNG phủ 7/13
luật đề xuất phủ     13/13
```

Trong 7 ca không được phủ, **toàn bộ 7** thuộc `DEFINITIONAL_NORMALIZATION` —
tức lớp ấy bị bỏ trống **hoàn toàn**, không phải bỏ sót lẻ tẻ. Ca mơ hồ duy nhất
là *góc BAC bằng 90°*: L28 kích hoạt theo cụm *"quan hệ vuông góc"*, mà cách viết
ấy không chứa cụm đó.

## 5. Luật đề xuất — soạn xong, **chưa áp dụng**

Chèn ngay dưới luật *"Hệ quả … đừng liệt kê"* để một luật MỞ và một luật ĐÓNG
đứng cạnh nhau. `+361 byte` (5311 → 5672). Không đổi schema, FactGraph, adapter
hay compiler — `SCHEMA_CAPABILITY_AUDIT` đã chứng minh mọi tầng nhận được quan
hệ ấy khi nó có mặt.

Kiểm bằng máy, không bằng mắt:

```text
HARDCODES_LIVE_CASE_LABELS   false   (dùng PQR, không nhắc S/A/B/C)
WOULD_MAKE_LINE_PLANE_CONSEQUENCES_GIVEN  false
MENTIONS_COORDINATES  false   ASKS_MODEL_TO_COMPUTE  false   COPIES_SCHEMA  false
FILE_UNTOUCHED_ON_DISK  true   SIMULATION_IS_IN_MEMORY_ONLY  true
```

Nếu áp dụng thì kéo theo: **bump `CACHE_VERSION`** (prompt đổi ⇒ cùng một đề có
thể cho hợp đồng khác) · **đóng băng lại candidate** (`backend/app` nằm trong
`MEASURED_SYSTEM_PATHS`) · **một lượt live để xác nhận**. Không thứ nào trong đó
thuộc wave này.

## 6. Hai test chưa giải thích — đã truy ra, không phải lỗi đo

Báo cáo trước ghi `5539 → 5567`, file mới `26`, để lại `+2` chưa giải thích. Đã
so **node ID** ở hai worktree sạch, cùng venv, cùng lệnh:

```text
b6ec81b   5540 node        da6ad17   5568 node        +28, 0 node bị bỏ
  26  NEW_TEST_FILE            test_structured_relation_analyze_live_runner.py
   2  PARAMETRIZE_EXPANSION    tests/semantic_program/test_domain_string.py
```

Cơ chế, kiểm trên chính mã nguồn: hai test ấy khai
`@pytest.mark.parametrize("f", sorted(_SCRIPTS.glob("*.py")))` — chúng duyệt
**mọi** tệp `.py` trong `backend/scripts/`. Wave trước thêm đúng một script, nên
mỗi test nở thêm một node.

Và `passed` với `collected` cũng khớp: `5539 + 1 skipped = 5540`,
`5567 + 1 skipped = 5568`. **Số trong báo cáo lịch sử đúng; thứ thiếu chỉ là lời
giải thích, và nó nằm ở đây.** Báo cáo cũ không bị sửa một byte
(`LIVE_EVIDENCE_INTEGRITY.json`: 14/14 artifact khớp blob tại HEAD).

Dự báo đã tự kiểm: wave này thêm một script nữa ⇒ lại `+2` cùng cơ chế. Đo được:
`5602` node tại commit công cụ = `5568 + 32 + 2`.

## 7. Bộ đo tự bắt mình hai lần

**① `test_L` cấm TÊN thay vì cấm LỜI GỌI.** Nó đỏ ở một câu **chú thích** giải
thích rằng `stage_semantic_analyze` *không* ghép thẻ văn phạm — tức phạt đúng
phần tài liệu làm công cụ dễ kiểm hơn. Đã đổi sang quét `ast.Call`.

**② Công cụ chẩn đoán tự nạp khoá thật.** `identity_and_cache_decision` nhập
`app.main` để đọc `CACHE_VERSION`; `app/persistence/db.py` gọi `load_dotenv`, nên
`GEMINI_API_KEY` vào thẳng `os.environ` — và bản `PRECHECK` đầu khai
`GEMINI_API_KEY_LOADED = true` trong khi đặc tả đòi khoá **không** được nạp. Đã
đổi sang phân tích nguồn `app/main.py`; `test_L_ter` cấm nhập lại. Đo kèm:
`app.ai.gemini`, `app.ai.pipeline`, `analyze_contract`, `geometry_compiler` đều
sạch — chỉ `app.main` nạp.

Tám phép tiêm lỗi, **8/8 bắt được**, hoàn nguyên trùng byte. Phép tiêm đáng giá
nhất là **F6** — thay so-node-ID bằng so-tổng-số: nó tái hiện đúng cách hai test
đi lọt ở báo cáo trước.

## 8. Giới hạn

1. **`n = 1`.** Một request. `CAUSALITY_STATUS = NOT_CAUSALLY_ESTABLISHED`. Phát
   biểu đúng: khoảng trống chỉ dẫn **ASSOCIATED_WITH** hành vi quan sát được.
2. **Ma trận cách viết là audit CHỈ DẪN, không phải mô phỏng mô hình.** Không ô
   nào trong nó do model sinh ra. Nó trả lời *"prompt có nói không"*, không trả
   lời *"model sẽ làm gì"*.
3. **Luật đề xuất chưa từng chạm mô hình thật.** `13/13` là độ phủ **chỉ dẫn**,
   không phải tỉ lệ thành công.
4. **Ca tiếng Anh (W08) nằm ngoài phạm vi sản phẩm** — giữ để kiểm tính tổng quát
   của luật, không phải để mở phạm vi.
5. `EVALUATOR_INDEPENDENCE = OPERATOR_WAIVED`.

## 9. Không tuyên bố

```text
ANALYZE_RELATION_FIX           = NOT_RUN
LIVE_REVALIDATION              = NOT_RUN
TOKEN_OPTIMIZATION             = NOT_PRODUCTION_ESTABLISHED
DEFAULT_ARCHITECTURE_CHANGED   = NO
PRODUCTION_READY               = NO
MERGE_ALLOWED                  = NO
```

## 10. Nợ ghi ngược

Đặc tả §17 cấm backfill `CURRENT_STATE.md` / `STATUS_LEDGER.md` trong wave này,
nên hai sổ vẫn chưa có mục cho wave này lẫn wave live trước. Khoảng trống đã
biết: bảy wave của 2026-09-15, ba wave 2026-09-20, và hai wave 2026-09-21.

```text
NEXT_ACTION = ANALYZE_DEFINITIONAL_NORMALIZATION_PROMPT_FIX
```
