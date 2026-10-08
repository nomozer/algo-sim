# ANALYZE_DEFINITIONAL_NORMALIZATION_PROMPT_FIX

> Sửa prompt, 2026-09-21, nhánh `feat/photo-problem-to-scene`.
> **0 request model · 0 request mạng.** Artifact:
> `docs/evaluation/geometry/photo-problem-to-scene/definitional-normalization-prompt-fix/`.

```text
PROMPT          5311 → 5672 byte  (+361)   5746c5e5… → 50a076e1…
SCHEMA          KHÔNG đổi một byte          0542161e… (3246 byte)
MODEL-FACING    đúng 1/5 băm đổi: prompts d157c6e1… → 5ec5a3c5…
CACHE_VERSION   98 → 99          CANDIDATE aadda232… → e7bae036…
WORDING         5/13 → 13/13 (PROMPT_INSTRUCTION_COVERAGE, không phải độ chính xác)
DEFAULT_MODE    LLM_ONLY (không đổi)        MERGE_ALLOWED = NO
```

## 1. Khoảng trống được đóng

Prompt `geometry_analyze.md` chỉ có **hai ngăn**: *"quan hệ đề NÓI"* và *"đề
KHÔNG nói mà bạn tự suy"*. Đề viết *"ABC là tam giác vuông tại A"* — nó **không**
viết *"AB ⟂ AC"* — nên phép viết lại rơi vào giữa hai ngăn, và lượt live
2026-09-21 đo được đúng hệ quả: mô hình khai `line(S,A) ⟂ plane(A,B,C)` nhưng bỏ
sót `line(A,B) ⟂ line(A,C)`, compiler từ chối `BASE_PERPENDICULAR_RELATION_MISSING`.

Wave này thêm **ngăn thứ ba**, bằng đúng khối luật đã đăng ký ở artifact chẩn
đoán — không sáng tác lại:

> Tính chất phát biểu bằng **LOẠI HÌNH** cũng là quan hệ đề NÓI. Đề viết *tam
> giác PQR vuông tại P* thì khai `perpendicular_lines` cho `PQ` và `PR`,
> `model_assumption` để `false`: đó là **viết lại** đúng điều đề đã nói bằng tên
> đỉnh, **không phải bạn tự suy**. Cùng cách với *góc PQR bằng 90°*.

Đặt **ngay dưới** luật cấm liệt kê hệ quả, để một luật MỞ và một luật ĐÓNG đứng
liền nhau. Tách xa nhau là mời đọc nhầm luật này thành luật kia.

## 2. Ranh giới ngữ nghĩa: 2 lớp → 4 lớp

| lớp | ví dụ | phải thành | luật trong prompt |
|---|---|---|---|
| `EXPLICIT_SURFACE_RELATION` | `PQ ⟂ PR` · *góc QPR bằng 90°* | **GIVEN** | khai lại bằng tên đỉnh · `90°` |
| `DEFINITIONAL_NORMALIZATION` | *tam giác PQR vuông tại P* | **GIVEN** | **khối mới** (3 luật con) |
| `LOGICAL_DERIVATION` | `SP ⟂ (PQR) ⇒ SP ⟂ PQ` | **DERIVED**, của FactGraph | *hệ tự suy, đừng liệt kê* |
| `LAYOUT_OR_CONSTRUCTION_ASSUMPTION` | `P = (0,0,0)` | **không phải dữ kiện** | *Hệ toạ độ KHÔNG phải dữ kiện* |

Câu phân xử, một câu: **có phải áp một ĐỊNH LÝ để ra quan hệ không?** Không ⇒
chuẩn hoá theo định nghĩa, vẫn GIVEN. Có ⇒ suy luận, việc của FactGraph.

## 3. Phạm vi: chỉ prompt, và chứng minh được là chỉ prompt

Phép kiểm mạnh nhất của wave: **gỡ khối luật ra khỏi prompt hiện tại thì phần
còn lại băm đúng `5746c5e5…` và dài đúng 5311 byte.** Không cần tin một con số
delta, không cần đọc Git — nếu wave đụng thêm chỗ nào khác, test đỏ.

```text
SCHEMA_CHANGED          NO    (keyset, required, enum kind — không đổi)
FACT_GRAPH_CHANGED      NO    ADAPTER_CHANGED  NO    COMPILER_CHANGED  NO
REQUEST_CONTRACT        NO    PIPELINE         NO
backend/app đổi đúng 2 tệp: skills/geometry_analyze.md · main.py (hằng số cache)
```

`test_F_compiler_VAN_khong_doc_problem_text` quét AST năm module compiler tìm
`.problem_text`, `["problem_text"]` và `getattr(..., "problem_text")` — **0
đường đọc**. Và `test_F_bo_quan_he_day_thi_VAN_tu_choi_dung_ma` dựng một hợp
đồng mà `problem_text` **nói rõ** *"tam giác PQR vuông tại P"* rồi đòi tầng dựng
vẫn từ chối: bằng chứng trực tiếp rằng bộ đọc câu chữ không quay lại.

## 4. Độ phủ chỉ dẫn — và nó KHÔNG phải độ chính xác

```text
trước:  phủ 5/13 · mơ hồ 1/13 · không phủ 7/13   (đo ở wave chẩn đoán)
sau:    phủ 13/13
```

Bảy ca chưa phủ đều thuộc `DEFINITIONAL_NORMALIZATION`; ca mơ hồ là *góc BAC
bằng 90°*, nay được khối mới nói thẳng.

⚠️ Đây là **`PROMPT_INSTRUCTION_COVERAGE`** — prompt **có nói** hay không. Nó
không nói gì về việc mô hình sẽ tuân, và **không** dự đoán lượt live.

Sổ đăng ký 13 cách viết bị khoá **hai lớp**: danh sách ID đóng băng **và** băm
nội dung chính tắc (`615c590a…`). Lý do rất cụ thể: một bộ test chỉ
`parametrize` theo chính danh sách cần kiểm thì **xoá một fixture làm ít test đi
mà vẫn xanh** — nó đo chính nó. Phép tiêm F10 chứng minh khoá ấy đỏ được.

## 5. Danh tính và cache

Bump **bắt buộc**, không phải theo lệ: khoá cache là *text đã chuẩn hoá +
`CACHE_VERSION`*, nên envelope đã cache chở đúng những hợp đồng **thiếu** lớp dữ
kiện mà lượt live đo được là thiếu. Không bump là đo prompt mới bằng kết quả
prompt cũ (tiền lệ bump 70 và 86).

Bốn cổng bump trả đủ: hằng số nguồn · assert khoá giá trị · bảng danh tính
`CURRENT_STATE` · manifest candidate. Vân tay môi trường đổi **đúng một thành
phần**:

```text
prompts           d157c6e1… → 5ec5a3c5…      ĐỔI
grammar_card · synthesis_schema · analyze_schema · capability   KHÔNG đổi một byte
```

`prompts_neu_chua_them_luat_chuan_hoa()` dựng lại đúng `d157c6e1…` bằng cách lùi
**đúng một tệp skill** — bằng chứng máy kiểm được rằng không prompt nào khác bị
chạm. Candidate đóng băng lại **trong worktree sạch** (`aadda232…` →
`e7bae036…`, vẫn 103 tệp), và độ lệch được **khai thành văn bản** ở
`CANDIDATE_DIVERGENCE.json` — mã sản phẩm được phép rời candidate đã đo, nhưng
không được rời trong im lặng.

## 6. Bộ đo tự bắt mình ba lần

Cả ba đều là **cổng phạt đúng phần hệ đang làm điều cổng ấy đòi** — cùng một chế
độ hỏng, ba biểu hiện:

1. `tính thể tích` trong danh sách cấm khớp vào **hàng của BẢNG DỊCH** câu hỏi
   đề sang nghĩa vụ (dòng 65).
2. `(0,0,0)` và `đặt hệ toạ độ` khớp vào **chính luật CẤM** khai toạ độ (dòng
   4 và 40).
3. `assert "call_gemini" not in nguồn` đỏ vì **danh sách cấm của chính nó** nằm
   trong nguồn.

Bài học ghi thẳng vào test: **ban theo từ khoá không phân biệt được *"hãy làm
X"* với *"đừng làm X"***. Hai lệnh cấm ở nhóm (1)(2) nay chỉ soi **khối wave này
thêm**; nhóm (3) chuyển sang quét `ast.Call` và `ast.Import`.

Nền đỏ sau khi sửa ba lỗi ấy: **18/48 đỏ**, và cả 18 đều nói về luật thiếu.

## 6b. Cổng ngân sách prompt bắt được wave này

Tập test tôi chạy trước commit 1 **không có** `tests/test_prompt_size_guard.py`.
Chỉ lượt **full backend trong worktree sạch** mới làm nó đỏ: trần của
`geometry_analyze.md` là **5350**, prompt mới **5672**.

Luật của chính cổng ấy đòi một câu hỏi **trước** khi nới — *"luật vừa thêm có mã
hoá xuống schema/validator được không?"* Câu trả lời là **KHÔNG**, và vì lý do
kiến trúc:

- **Lược đồ không nói được.** Nó ràng buộc *hình dạng* thứ mô hình viết ra
  (`enum` của `kind`, arity đường/mặt, `required: source_fact_id`). Không có ô
  nào diễn đạt *"gặp cách viết này thì phát quan hệ kia"* — đó là ánh xạ từ
  **ngữ nghĩa câu văn** sang trường có cấu trúc.
- **Validator càng không.** Muốn cưỡng chế thì nó phải đọc `problem_text` tìm
  chữ *"vuông tại"* — đúng **bộ đọc từ vựng văn bản mà `contract_adapter/2` vừa
  gỡ hẳn có chủ đích**, và là điều đặc tả wave này cấm thẳng.

Tức khoản này rơi đúng vào ngoại lệ ngân sách tự thừa nhận. Nới **5350 → 5700**,
dôi thật **28 byte**, và **không gọt văn cho vừa trần**: khối luật là bản đã
đăng ký, năm mệnh đề của nó mỗi mệnh đề chở một điều lược đồ không nói được. Đã
tiêm lại ở trần 5600 để chứng minh cổng vẫn cắn sau khi nới.

## 7. Phép tiêm lỗi

**11 tiêm · 11 bắt được · hoàn nguyên trùng byte · 0 dấu tiêm còn lại.**
Đáng chú ý ba cái:

- **F10** (xoá một wording fixture) — chính ca mà đặc tả §7.10 nhắm tới; khoá
  hai lớp của sổ đăng ký bắt được.
- **F8** (nối compiler vào `app/ai/pipeline.py`) — bị
  `test_Y_duong_mac_dinh_VAN_khong_tham_chieu_compiler` bắt, tức guard có sẵn
  từ wave trước vẫn sống.
- **F11** (hạ trần ngân sách xuống dưới kích thước thật) — nới một trần rồi
  không chứng minh nó còn cắn thì trần ấy thành lời chúc.

## 8. Giới hạn

1. **Chưa có lượt live nào sau khi sửa.** Wave chứng minh prompt **nói đủ**,
   không chứng minh mô hình **khai đủ**. `LIVE_RELATION_EXTRACTION = NOT_RUN`.
2. **13/13 là độ phủ CHỈ DẪN**, không phải tỉ lệ thành công.
3. **`CAUSALITY_STATUS` của chẩn đoán vẫn là `NOT_CAUSALLY_ESTABLISHED`** —
   `n = 1`. Sửa theo một chẩn đoán chưa được chứng minh nhân quả là quyết định
   có rủi ro đã biết, và lượt live sau mới trả lời được.
4. **Ca tiếng Anh (W08) nằm ngoài phạm vi sản phẩm** — giữ để kiểm tính tổng
   quát của luật; prompt không mở phạm vi sang đề tiếng Anh.
5. **Compiler vẫn ngoài đường mặc định.** `DEFAULT_MODE = LLM_ONLY`.
6. `EVALUATOR_INDEPENDENCE = OPERATOR_WAIVED`.

## 9. Không tuyên bố

```text
MODEL_ACCURACY                 = NOT_MEASURED
LIVE_RELATION_EXTRACTION       = NOT_RUN
TOKEN_OPTIMIZATION             = NOT_PRODUCTION_ESTABLISHED
PROMPT_TOKEN_ESTIMATE          = NOT_MEASURED   (kho không có tokenizer chính thức)
DEFAULT_ARCHITECTURE_CHANGED   = NO
MERGE_ALLOWED                  = NO
```

Kết quả lượt live cũ **giữ nguyên** `ANALYZE_RELATION_INCOMPLETE`; không artifact
lịch sử nào bị sửa.

## 10. Nợ ghi ngược

`CURRENT_STATE.md` chỉ được sửa **một dòng** (bảng danh tính, `CACHE_VERSION`) —
đó là cổng bump, không phải mục wave. `STATUS_LEDGER.md` và mục `### 1a-*` cho
ba wave gần nhất vẫn chưa có. Cộng vào khoảng trống đã biết: bảy wave 2026-09-15,
ba wave 2026-09-20, ba wave 2026-09-21.

```text
NEXT_ACTION = STRUCTURED_GEOMETRY_RELATION_ANALYZE_LIVE_REVALIDATION_WITH_BROWSER_CONTACT_SHEET
```
