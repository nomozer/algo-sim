# GENERIC_RULE_SCENE — AUDIT RANH GIỚI LLM ↔ BỀ MẶT HỌC SINH

Baseline đo: `c8a04a3ce69bacbc98c0baf14377657dbad0d829`. **Không sửa production.**
Đây là tài liệu **bằng chứng**, không phải đề xuất thiết kế.

## 1. Câu hỏi

`generic.rule_scene` có cho phép **văn bản tự do do LLM soạn** trở thành nội dung
runtime mà học sinh đọc, tới mức làm yếu hợp đồng *"spec có biên · engine sở hữu
sự thật"* không?

## 2. Chuỗi sở hữu — truy qua đường render thật

| # | Chặng | File · symbol | Tất định? | Có biên? | Học sinh thấy? |
|---|---|---|---|---|---|
| 1 | LLM sinh trường | `catalog.py:1379` — `"narration": {"type": "STRING", "nullable": True}` | không | **không** — chuỗi bất kỳ | — |
| 2 | Validator BE | `dsl/validator.py:482-486` — chặn key lạ; narration chỉ `isinstance(str)` | có | **chỉ về CẤU TRÚC** | — |
| 3 | Validator FE (mirror) | `generic/validate.ts:476-482` — cùng luật | có | **chỉ về CẤU TRÚC** | — |
| 4 | Engine dựng frame | `generic/model.ts:373` — `step.narration ?? "Hé lộ: …"` | có | dùng **nguyên văn** nếu LLM có gửi | — |
| 5 | Khe thuyết minh shell | `generic/index.ts:78` `narrate()` → `NarrationSlot` | — | — | **CÓ — ở Quan sát** |
| 6 | Thẻ TIẾN TRÌNH | `generic/ui.tsx:818`, trong **`GenericInspector`** | — | — | có, **chỉ khi mở Giải thích** |
| 7 | Ngữ cảnh gia sư AI | `index.ts::getExplainContext` → `narration: frame.narration` | — | — | gián tiếp |

> **Đính chính do đo được.** Bản nháp đầu của audit này ghi *"narration hiện hai
> lần trên một màn hình"*, suy từ việc `progressive = timeline.length > 1` trùng
> điều kiện với `narrate()`. **Sai.** Dòng 818 nằm trong `GenericInspector`, tức
> panel Giải thích (đóng mặc định). Đo thật: `GenericWorkspace` render 1241 ký
> tự và **không** chứa narration. Đúng lý do §4 cấm suy từ grep.

## 3. Phân loại nội dung học sinh đọc

| Loại | Ở `generic.rule_scene` |
|---|---|
| **A. STATE-DERIVED** | narration của `move_along_path` (`model.ts:384,392` — dựng từ id đối tượng); nhánh mặc định `"Hé lộ: …"` |
| **B. CATALOG/SCHEMA-BOUNDED** | nhãn đối tượng, kiểu đối tượng, giá trị — đều qua allowlist DSL |
| **C. FREE-FORM_GENERATED** | **`RevealStep.narration`** — đúng một trường, chỉ ở `reveal_sequence` |

Bề mặt tự do vì thế **hẹp và gọi tên được**, không phải "LLM sinh UI".

## 4. Ma trận đối kháng — đo bằng validator thật, không gọi API

Đặc tả ở `generic/narration-boundary.characterization.test.tsx` (18 test, xanh).

| Ca | Kết quả | Học sinh có đọc được? |
|---|---|---|
| mâu thuẫn giá trị đang hiện (`"Ô A đang mang giá trị 999"` khi A = 5) | **ACCEPTED** | có |
| tuyên bố kết quả thuật toán (`"Kết quả cuối cùng là 42"`) | **ACCEPTED** | có |
| tự phán học sinh đúng/sai (`"Em đã chọn đúng rồi"`) | **ACCEPTED** | có |
| lộ trước bước sau / đáp án | **ACCEPTED** | có |
| tự xưng là hệ thống chấm (`"Hệ thống xác nhận: chính xác"`) | **ACCEPTED** | có |
| chuỗi 20 000 ký tự | **ACCEPTED** — không có trần độ dài ở bất kỳ tầng nào | có |
| chèn `<script>` | ACCEPTED ở validator, nhưng **React escape** → `&lt;script&gt;` | text thô, **không** thành markup |
| `narration` không phải chuỗi | **SANITIZED** → rơi về chuỗi dẫn xuất `"Hé lộ: …"` | — |
| thêm key lạ (`html`) vào reveal step | **REJECTED** | — |

Hàng rào **có thật** nhưng chỉ chặn **hình dạng**, không chặn **nội dung**.

## 5. Sở hữu sự thật — câu hỏi quan trọng nhất

| Narration có thể… | Đo được | Bằng chứng |
|---|---|---|
| đổi engine state / timeline | **KHÔNG** | state serialize **giống hệt từng byte** khi có và không có narration |
| đổi kết quả | **KHÔNG** | không logic nào đọc narration để quyết định (khoá bằng test quét `model.ts`) |
| đổi phán quyết `predict.check` | **KHÔNG áp dụng** | `generic.rule_scene` **không khai `predict`** |
| mâu thuẫn với sự thật đang hiển thị | **CÓ** | sân khấu vẽ `5` (engine), khe thuyết minh in *"đang mang giá trị 999"* — cùng lúc, không tầng nào đối chiếu |

Ranh giới then chốt của §5 — *mô tả state* hay *tuyên bố sự thật thuật toán* —
rơi vào vế thứ hai: narration **không tính được** kết quả, nhưng **nói được** một
kết quả.

## 6. Phân loại rủi ro

### **C — THESIS_BOUNDARY_WEAKNESS**

Không phải **B**, vì rủi ro vượt quá "cách hành văn": một câu do LLM soạn có thể
khẳng định kết quả, khẳng định tính đúng đắn, hoặc mâu thuẫn thẳng với con số mà
engine đang vẽ trên cùng màn hình.

Không phải **D**, và đây là chỗ kiến trúc **đứng vững**: narration **không** sở
hữu state, kết quả hay phán quyết. Đo được, không suy đoán.

Yếu tố thu hẹp mức độ: đúng **1/22** target · đúng **một** trường · chỉ ở
`reveal_sequence` · chỉ trên đường LLM soạn (bài mẫu offline do người viết) ·
không có `predict` để bẻ · không chèn được markup.

## 7. Ảnh hưởng tới từng tuyên bố

| | Kết luận |
|---|---|
| **T1** — NL → spec có biên đã validate | **Vẫn bảo vệ được, kèm giới hạn nêu rõ.** Spec có biên về *cấu trúc*: allowlist trường, tham chiếu object phải có thật, key lạ bị từ chối. Đúng một trường văn bản là không có biên về *nội dung*. |
| **T2** — engine tất định sở hữu sự thật | **NGUYÊN VẸN, đã đo.** Đây là kết quả quan trọng nhất của audit. |
| **T3** — biểu diễn có thể gây hiểu sai dù engine đúng | **CÓ — đây chính là chỗ hở.** |

**Một tuyên bố hiện hành cần thu hẹp.** Danh sách được-phép-nói có câu
*"biểu diễn dẫn xuất từ state"*. Với `generic.rule_scene.narration` thì **không
đúng**: nó dẫn xuất từ LLM. Hoặc thu hẹp tuyên bố, hoặc siết trường đó — không
được giữ cả hai như hiện nay.

## 8. Đề xuất bước kế tiếp

Phân loại: **`THESIS_LIMITATION`**.

Vì sao **không** phải `THESIS_BLOCKER_FIX`: T2 nguyên vẹn và đã đo; chỗ hở giới
hạn ở một trường của một target; khoá luận vẫn bảo vệ được nếu nêu giới hạn
trung thực.

Vì sao **không** phải `PRODUCT_BACKLOG`: nó động tới một tuyên bố đang được nêu,
và `CORRECTNESS.md §1` cấm *"dựng xấp xỉ rồi giả vờ đúng"* — một câu thuyết minh
sai về cảnh đang hiện nằm rất gần lằn ranh đó.

Giảm nhẹ **rẻ** cho một task được uỷ quyền riêng sau này (**không làm ở đây**):
đặt trần độ dài, và/hoặc yêu cầu narration **dẫn xuất** từ đối tượng được reveal
thay vì nhận chuỗi tự do — nhánh mặc định `"Hé lộ: …"` đã sẵn là bản dẫn xuất
đúng khuôn, nên đường lui đã tồn tại.

## 9. Điều audit này KHÔNG làm

Không sửa schema · validator · renderer · prompt · engine · `RevealStep`. Không
gọi API ngoài. Không xây hệ kiểm duyệt nội dung, không thêm LLM judge. Không
tuyên bố gì về kết quả học tập: `LEARNER_IMPACT_NOT_EVALUATED`,
`CURRICULUM_SUPPORT_PARTIAL`.
