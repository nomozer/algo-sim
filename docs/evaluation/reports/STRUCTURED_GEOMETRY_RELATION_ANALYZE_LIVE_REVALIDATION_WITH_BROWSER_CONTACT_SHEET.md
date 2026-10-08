# STRUCTURED_GEOMETRY_RELATION_ANALYZE_LIVE_REVALIDATION_WITH_BROWSER_CONTACT_SHEET

> Lượt live **một request**, 2026-09-21, nhánh `feat/photo-problem-to-scene`.
> Artifact: `docs/evaluation/geometry/photo-problem-to-scene/structured-relation-revalidation/`.
> **`USER_VISUAL_APPROVAL = PENDING`** — contact sheet chờ người xem.

```text
OUTCOME = PASS      CRITICAL_RELATION_ACCURACY 0.5 → 1.0      2/2 quan hệ GIVEN
analyze 1 · vision 0 · synthesis 0 · repair 0 · retry 0 · HTTP 200
compiler SUPPORTED → COMPILED → route served → cổng trực quan COVERED → đáp số 10
trình duyệt 1440×900 và 390×844: 11/11 ô ĐẠT · 0 request model
PROMPT_FIX_EFFECT = SUPPORTED_ON_ONE_CONTROLLED_REVALIDATION
```

## 1. Câu hỏi, và câu trả lời

Lượt trước (prompt cũ) mô hình khai `line(S,A) ⟂ plane(A,B,C)` nhưng **bỏ sót**
`line(A,B) ⟂ line(A,C)` cho đề *"ABC là tam giác vuông tại A"*. Sau khi prompt
thêm lớp `DEFINITIONAL_NORMALIZATION`, cùng đề ấy, cùng model, cùng nhiệt độ:

| | trước | nay |
|---|---|---|
| `perpendicular_line_plane(S,A ⟂ A,B,C)` | có | **có** |
| `perpendicular_lines(A,B ⟂ A,C)` | **thiếu** | **có** — `← abc_vuong_a` |
| accuracy | 0.5 | **1.0** |
| compiler | `BASE_PERPENDICULAR_RELATION_MISSING` | **`SUPPORTED`** |

Mọi trục an toàn vẫn sạch: 0 quan hệ trùng · 0 mâu thuẫn · 0 thừa chưa xác minh
· **0 giả định của mô hình** · **0 hệ quả bị khai thành GIVEN** · mọi
`source_fact_id` truy được · mọi nhãn điểm hợp lệ.

Đáng chú ý: mô hình **vẫn không** liệt kê `SA ⟂ AB/AC/BC`. Luật mới mở đúng một
ngăn mà không làm sập luật cấm liệt kê hệ quả — đó là điều dễ hỏng nhất khi nới
một prompt, và nó không hỏng.

## 2. Phép so request — chỗ làm kết quả này có nghĩa

Một lượt *"sửa prompt rồi chạy lại thấy tốt hơn"* chỉ đáng tin nếu chứng minh
được **không có gì khác** thay đổi. Cách làm:

1. **Dựng lại** thân request của lượt trước bằng chính prompt tại `eeacd67`,
   rồi đòi nó băm đúng `e30f0ddd…` **đã commit từ trước**. → khớp ⇒ phép dựng
   lại trung thực.
2. Dựng thân mới bằng prompt hiện tại, so **từng con trỏ JSON**.
   → khác **đúng một**: `/systemInstruction/parts/0/text`.
3. Sau lượt live, thân THẬT gửi đi băm `26ed44c0…` — **trùng byte** bản dự đoán
   offline ở bước 2.

```text
endpoint                giống    · user text            giống từng byte
temperature 0.1         giống    · generationConfig keys giống
thinkingConfig          KHÔNG có · maxOutputTokens       KHÔNG có
REQUEST_EQUALS_PRIOR_EXCEPT_PROMPT = true
```

Nói cách khác: **biến duy nhất đổi giữa hai lượt là prompt.**

## 3. Tầng dựng tất định — 0 lượt gọi model

```text
adapter/2 VALID → fact-graph/2: 8 nút · GIVEN 6 · DERIVED 6
  ba quan hệ ⟂ suy ra: 3/3 khớp ground truth · mỗi cái nêu được cha
compiler SUPPORTED → COMPILED · 11 bước · 9 primitive · model tokens 0
Pydantic PASS · type PASS · IR static PASS · grounding PASS · route served
cổng trực quan COVERED · 4 đỉnh/4 mặt · |AB|²=9 |AC|²=16 |SA|²=25
AB⟂AC · SA⟂AB · SA⟂AC · A,B,C không thẳng hàng · final_memory 10 · answer 10
```

`SYNTHESIS_REQUEST_AVOIDED_ON_SUPPORTED_CASE = 1` — và đó là **một ca**, không
phải một tỉ lệ.

## 4. Trình duyệt và contact sheet

Phát lại envelope do compiler dựng, trên Chrome thật + `dist/`, hai khung, mọi
`/api/*` chặn ở biên mạng. **11/11 ô ĐẠT ở cả hai khung**: canvas có diện tích ·
nhãn đủ `S A B C` · đáp số **10** hiện ở bước cuối · không tràn ngang · nút
*Bước trước/sau* thấy được và **không bị vật khác che** · bước chuyển qua lại rồi
về đúng chỗ · chỉ ba đường `/api` đã chặn · `/api/analyze` đúng **một** lần · 0
lỗi console. `BROWSER_REPLAY_MODEL_REQUESTS = 0`.

**Contact sheet**: `…/structured-relation-revalidation/CONTACT_SHEET.png`
(8 khối: đề · hai quan hệ · FactGraph · bước dựng · cảnh desktop · cảnh mobile ·
topology và kiểm hình học · đáp số/token/độ trễ). Không chứa khoá, nguyên văn
phản hồi, nguyên văn prompt hay toàn bộ semantic program.

## 5. Token — đọc kèm cảnh báo, đừng đọc như tiết kiệm

```text
input 1532 · output 463 · thought 590 · TỔNG 2585
lượt trước 2019 → nay 2585   (Δ +566)
```

Đây là **hai lượt ở hai thời điểm**, mỗi lượt `n = 1`. Nó **không** là bằng
chứng về token, theo chiều nào cả. Phần tăng lớn nhất là `thoughtsTokenCount`
(174 → 590) — đại lượng do provider quyết và dao động giữa các lượt. Prompt dài
thêm 361 byte, nhưng **token không suy được từ byte**.
`TOKEN_OPTIMIZATION = NOT_PRODUCTION_ESTABLISHED`.

## 6. Bộ đo tự sai ba lần — tất cả ở tầng trình duyệt

Cả ba đều làm cổng báo **KHÔNG ĐẠT cho một sản phẩm đang đúng** — hướng sai
nguy hiểm không kém hướng lạc quan, vì nó vu cho sản phẩm một lỗi không có:

1. **`sess.eval` trả GIÁ TRỊ JS, không phải chuỗi.** Tôi so `=== "true"`, nên
   mọi phép chờ hết giờ và cổng báo *"không có canvas"* trong khi cảnh đã dựng
   xong từ lâu. Ảnh chụp lúc ấy cho thấy hình vẽ đầy đủ.
2. **Nút gửi là nút mũi tên, không mang chữ.** Tôi tìm
   `textContent === "Dựng mô phỏng"` — chữ ấy thuộc `PhotoProblemPanel` (luồng
   ảnh), không thuộc ô gõ tay.
3. **Đọc đáp số ở bước 1/6.** `.geo3d-readout` chỉ có nội dung ở **bước cuối**;
   đọc sớm rồi kết luận *"không hiện đáp số"* là chấm sai. Và `/api/auth/me` là
   lời gọi hợp lệ của ứng dụng — danh sách cho phép của tôi bỏ sót nó.

Mỗi lỗi đều được sửa ở **bộ đo**, không ở sản phẩm.

## 7. Phép tiêm lỗi

**6 tiêm · 5 bắt được · 1 vô hiệu**, hoàn nguyên trùng byte. Cái vô hiệu đáng
ghi: thay phép so `_sha(thân_cũ) == PRIOR_SHA` bằng `True` **không** làm test đỏ
— vì giá trị thật vốn đã đúng, nên phép tiêm ấy không đổi hành vi nào. Đã thay
bằng **F5′** có nghĩa (lùi về prompt SAI) và thêm cửa sổ chứng: băm đã commit
phải **gắn với prompt cũ**, và thân dựng bằng prompt mới **không được** khớp nó.
F5′ ⇒ 2 test đỏ.

## 8. Giới hạn — đọc kèm mọi lần dẫn kết quả này

1. **`n = 1`, một ca kiểm soát, một lượt.** `PROMPT_FIX_EFFECT =
   SUPPORTED_ON_ONE_CONTROLLED_REVALIDATION`. **Không** `CAUSALLY_ESTABLISHED`,
   **không** `PRODUCTION_ESTABLISHED`.
2. **Không held-out.** `dataset_split = DEVELOPMENT_PILOT_FOLLOWUP` — không vào
   mẫu số độ chính xác của khoá luận.
3. **Cùng ca đã dùng để chẩn đoán.** Sửa theo một ca rồi kiểm lại bằng chính ca
   ấy là bằng chứng YẾU nhất trong các bằng chứng live; nó loại trừ "prompt vô
   tác dụng", nó **không** cho biết luật mới có tổng quát không. Đó là việc của
   benchmark nhiều ca.
4. **Compiler vẫn ngoài đường mặc định.** `DEFAULT_MODE = LLM_ONLY`. Lượt này
   chạy compiler bằng runner, không bằng sản phẩm.
5. **Trình duyệt phát lại FIXTURE.** Nó chứng minh cảnh vẽ được và điều khiển
   dùng được; nó **không** chứng minh một người học thật đi hết luồng.
6. `EVALUATOR_INDEPENDENCE = OPERATOR_WAIVED` · `USER_VISUAL_APPROVAL = PENDING`.

## 9. Không tuyên bố

```text
MODEL_ACCURACY                 = NOT_MEASURED   (1 ca, không phải tỉ lệ)
CAUSALLY_ESTABLISHED           = NO
PRODUCTION_ESTABLISHED         = NO
TOKEN_OPTIMIZATION             = NOT_PRODUCTION_ESTABLISHED
DEFAULT_ARCHITECTURE_CHANGED   = NO
MERGE_ALLOWED                  = NO
```

Kết quả lượt live **trước** giữ nguyên `ANALYZE_RELATION_INCOMPLETE`; không
artifact lịch sử nào bị sửa.

## 10. Nợ ghi ngược

`STATUS_LEDGER.md` và mục `### 1a-*` cho các wave từ 2026-09-15 tới nay vẫn
chưa có — đặc tả bốn wave liên tiếp đều giới hạn phạm vi thay đổi. Khoảng trống:
bảy wave 2026-09-15, ba wave 2026-09-20, bốn wave 2026-09-21.

```text
NEXT_ACTION = USER_REVIEWS_CONTACT_SHEET_THEN_MULTICASE_STRUCTURED_ANALYZE_COMPILER_BENCHMARK
```
