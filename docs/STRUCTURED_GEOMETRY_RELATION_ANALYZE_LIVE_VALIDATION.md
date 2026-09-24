# STRUCTURED_GEOMETRY_RELATION_ANALYZE_LIVE_VALIDATION

> Lượt live **một request**. Đóng 2026-09-21 trên `feat/photo-problem-to-scene`.
> Artifact: `docs/evaluation/geometry/photo-problem-to-scene/structured-relation-analyze-live/`.

```text
OUTCOME                      = ANALYZE_RELATION_INCOMPLETE
ANALYZE_HTTP_REQUESTS        = 1      VISION = 0   SYNTHESIS = 0   RETRIES = 0
CRITICAL_RELATION_ACCURACY   = 0.5    (1/2 quan hệ bắt buộc)
COMPILER_ELIGIBILITY         = UNSUPPORTED_STRUCTURED_RELATION_MISSING
PRODUCT_CODE_CHANGED = NO    CACHE_VERSION 98 → 98    CANDIDATE aadda232… (không đổi)
DEFAULT_MODE = LLM_ONLY      DEFAULT_ARCHITECTURE_CHANGED = NO    MERGE_ALLOWED = NO
```

## 1. Câu hỏi

`FACT_GRAPH_CONTRACT_EXTENSION` (2026-09-20) chứng minh hệ **đọc được** ô
`geometric_relations`. Mọi hợp đồng trong wave đó do test dựng tay, nên nó
không nói gì về việc mô hình thật **khai đúng** ô ấy. Wave này tiêu đúng một
request để hỏi phần còn lại.

## 2. Kết quả — mô hình khai ĐÚNG MỘT trong HAI

| quan hệ đề cho | model khai? | xuất xứ | phán quyết |
|---|---|---|---|
| `line(S,A) ⟂ plane(A,B,C)` | **CÓ** | `sa_vuong_goc_abc`, truy được | đúng, không phải giả định |
| `line(A,B) ⟂ line(A,C)` | **KHÔNG** | — | `MISSING` |

Mọi thứ *khác* đều sạch, và đây là phần đáng chú ý: lượt này **không** hỏng theo
bất kỳ kiểu nào mà bộ đo dự phòng cho.

```text
JSON_PARSE                    PASS        PYDANTIC                 PASS
SOURCE_FACT_RESOLUTION        PASS        POINT_REFERENCE          PASS
MODEL_ASSUMPTION_COUNT        0           UNVERIFIED_EXTRA         0
DUPLICATE_RELATION_COUNT      0           CONTRADICTORY            0
EXTRA_DERIVED_AS_GIVEN_COUNT  0
```

Nói riêng: mô hình **không** liệt kê `SA ⟂ AB`, `SA ⟂ AC`, `SA ⟂ BC` thành dữ
kiện đề cho — đúng như `geometry_analyze.md` dặn (*"hệ quả … hệ tự suy, đừng
liệt kê"*). Luật *"đừng khai hệ quả"* được tuân; luật *"khai lại quan hệ đã
viết thành câu"* thì chỉ được tuân một nửa.

## 3. Tầng dựng từ chối ĐÚNG, và từ chối vì đúng lý do

Chạy tiếp hoàn toàn offline, 0 lượt gọi model:

```text
adapter/2        VALID            fact-graph/2   8 nút · 5 GIVEN · 6 DERIVED
eligibility      UNSUPPORTED_STRUCTURED_RELATION_MISSING
reason_code      BASE_PERPENDICULAR_RELATION_MISSING
diagnostics      ["perpendicular_lines"]
compile          NOT_ELIGIBLE     (không sinh chương trình một phần)
```

Đây **không phải lỗi mới**. `compiler.py` khai sẵn trạng thái này kèm lời giải
thích của chính nó: *"Đề CÓ THỂ nói rõ … bằng câu chữ — nhưng không ai khai nó
thành quan hệ CÓ CẤU TRÚC. Đây là phán quyết cố ý của `/2`, không phải một lỗ
hổng: tầng dựng không đọc câu chữ."* Lượt live vừa cho thấy nhánh ấy **có thật
trên mô hình thật**, không chỉ trong test.

Ba quan hệ suy ra vẫn **đúng cả ba** và mỗi cái nêu được cha — vì chúng dẫn từ
quan hệ đường–mặt mà mô hình đã khai:

```text
DERIVED_PERPENDICULAR_COUNT                 3
DERIVED_PERPENDICULAR_MATCHES_GROUND_TRUTH  true
EVERY_DERIVED_RELATION_HAS_PARENT_PROOF     true
```

## 4. Giả thuyết về nguyên nhân — CHƯA KIỂM, và cố ý không sửa

Hai câu đề có hình dạng khác nhau:

- *"Cạnh SA **vuông góc** với mặt phẳng (ABC)"* — mang đúng chữ *vuông góc*;
- *"đáy ABC là tam giác **vuông tại A**"* — quan hệ vuông góc nằm trong một
  **vị từ về loại tam giác**, không phải một câu về hai đường thẳng.

Prompt nói *"Mỗi quan hệ vuông góc đã ghi thành câu ở trên, khai thêm ở đây"* —
câu ấy đọc như thể quan hệ luôn được phát biểu trực tiếp. Giả thuyết: mô hình
không nhận ra *"vuông tại A"* là một quan hệ phải khai lại.

⚠️ **Đây là GIẢ THUYẾT.** `n = 1`, một ca, một lượt. Nó chưa được kiểm, và wave
này **không** sửa prompt — đó là việc của `ANALYZE_STRUCTURED_RELATION_PROMPT_DIAGNOSIS`.

Một dữ kiện bổ trợ, đo được: mô hình **đã** tạo mục `abc_tam_giac_vuong_tai_a`
và neo `AB = 3`, `AC = 4` vào đó. Nghĩa là mục dữ kiện để trỏ `source_fact_id`
**có sẵn** — cái thiếu chỉ là bản ghi quan hệ, không phải chỗ để ghim nó.

## 5. Bộ đo tự bắt mình hai lần

**① Phạm vi `parent proof` bị đặt rộng hơn luật sản phẩm.** Bản đầu của bộ chấm
đòi **mọi** fact `DERIVED` phải có `derived_from`, và vì thế chấm một ca ĐÚNG
thành `DOWNSTREAM_COMPILER_FAILURE`. Luật thật (`fact_graph.kiem_xuat_xu`) chỉ
ép với quan hệ **vuông góc**, có nêu lý do: đó là loại fact mà một lời khai và
một suy diễn có cùng hình dạng. `lies_in_plane` cố ý không mang cha. Đã thu hẹp
bộ đo **theo luật sản phẩm**, và tách thành hai trường riêng để lần sau không ai
gộp lại.

**② Cổng quét ground truth chưa từng đỏ.** Phép tiêm lỗi F3 (tắt hẳn vòng quét)
**đi lọt** — cả 25 test vẫn xanh, vì `GROUND_TRUTH_ABSENT_FROM_REQUEST = True`
cũng đúng khi bộ quét *không chạy*. Đã thêm **cửa sổ chứng**: một test cố ý nhét
chuỗi cấm vào thân request và đòi bộ quét phải báo. Tiêm lại ⇒ đỏ đúng một test.

**③ Một test của chính tôi sai giả định (không phải sản phẩm sai).** Test J bản
đầu gỡ mục `input_facts` chở `SA = 5` rồi chờ compiler từ chối — nhưng kết quả
là `PASS`, vì `build_request_contract` **neo literal từ `problem_text`** và gắn
`SA = 5` vào mục dữ kiện còn lại có nhắc `SA`. Giữ lại thành
`test_J_bis_do_dai_do_SERVER_neo_tu_cau_de`: đây là một đường phụ thuộc THẬT —
tầng dựng không đọc câu chữ, nhưng thứ nuôi nó thì có.

## 6. Bằng chứng ngân sách và danh tính request

```text
MAX_HTTP_REQUESTS 1   ATTEMPTED 1   SENT 1   BLOCKED 0
STAGE_SUM_EQUALS_SENT  true         SENT_WITHIN_BUDGET  true
endpoint               …/models/gemini-2.5-flash:generateContent
generationConfig keys  ["responseMimeType","responseSchema","temperature"]
UNEXPECTED_KEYS []     FORBIDDEN_KEYS []   (0 thinkingConfig, 0 maxOutputTokens)
temperature quan sát   0.1
system prompt SHA256   5746c5e5…  ≡ load_skill("geometry_analyze") tại START_HEAD
user text SHA256       6d4fef1c…  ≡ sha('Đề bài:\n"""\n<văn bản đóng băng>\n"""')
GROUND_TRUTH_ABSENT_FROM_REQUEST  true
```

Trần đặt **ở transport**, không ở logic: `CongQuetCam.handle_async_request` chặn
trước `client.post`, trần từng tầng `{vision: 0, analyze: 1, synthesis: 0}`, cộng
`ApiBudget(max_api_calls=1, max_attempts=1, max_logical_calls=1)`. Hai lớp, cố ý.

Launcher gọi thẳng `pipeline.stage_semantic_analyze`; một test **quét mã nguồn**
của nó, đòi có `pipeline.stage_semantic_analyze` và **cấm** `call_gemini` — để
không ai lặng lẽ dựng một request riêng rồi gọi đó là đường sản phẩm.

## 7. Token · độ trễ

```text
input 1432 · output 413 · thought 174 · total 2019
analyze HTTP 5082,5 ms · end-to-end 5117,4 ms · fact graph 0,14 ms · compiler n/a
HISTORICAL_ANALYZE_TOKEN_COMPARISON = NOT_COMPARABLE
TOKEN_OPTIMIZATION = NOT_PRODUCTION_ESTABLISHED
```

`NOT_COMPARABLE` vì số Analyze lịch sử gần nhất đo trên **văn bản khác** (B01–B04
do manifest sinh) và **prompt khác** (4442 → 5311 byte). `n = 1` ⇒ không nói gì
về độ ổn định.

## 8. Giới hạn — đọc kèm mọi lần dẫn số của wave này

1. **`n = 1`, một ca, một lượt.** Không có gì ở đây là tỉ lệ. *"Mô hình khai
   thiếu quan hệ"* đúng với **lượt này**, không phải một tần suất.
2. **Không phải held-out.** `DATASET_CLASS = CONTROLLED_TEXT_VALIDATION_CASE`,
   `dataset_split = DEVELOPMENT_PILOT_FOLLOWUP` — không vào mẫu số độ chính xác
   của khoá luận.
3. **KHÔNG phải C01.** Khuôn ground truth C01 chưa từng được điền, nên không có
   bản văn C01 nào chứng minh được nguồn + hash. Văn bản ở đây do đặc tả wave
   đóng băng; **đừng** gọi nó là trùng byte với C01 lịch sử.
4. **`EVALUATOR_INDEPENDENCE = OPERATOR_WAIVED`** — người viết bộ đo cũng là
   người chạy lượt đo.
5. **Compiler vẫn ngoài đường mặc định.** `DEFAULT_MODE = LLM_ONLY`;
   `grep -rn geometry_compiler backend/app/ai backend/app/main.py` ⇒ rỗng.
6. **Một ca không nói được prompt sai ở đâu.** Mục 4 là giả thuyết.

## 9. Không tuyên bố

```text
DEFAULT_ARCHITECTURE_CHANGED   = NO
DETERMINISTIC_FIRST            = NOT_ENABLED
TOKEN_OPTIMIZATION             = NOT_PRODUCTION_ESTABLISHED
END_TO_END_TOKEN_REDUCTION     = NOT_ESTABLISHED
PRODUCTION_READY               = NO
MERGE_ALLOWED                  = NO
```

## 10. Nợ ghi ngược CHƯA trả trong wave này

Đặc tả wave giới hạn thay đổi ở *runner · test · manifest · artifact · báo cáo*
và trần **hai** commit, nên **`STATUS_LEDGER.md` và `CURRENT_STATE.md` chưa có
mục cho wave này** — cố ý, theo đặc tả, không phải bỏ quên. Nó cộng vào khoảng
trống đã biết: bảy wave của 2026-09-15 và ba wave mới nhất cũng chưa có mục
`### 1a-*`. Wave kế tiếp có đụng mã thì trả luôn cả cụm.

```text
NEXT_ACTION = ANALYZE_STRUCTURED_RELATION_PROMPT_DIAGNOSIS
```
