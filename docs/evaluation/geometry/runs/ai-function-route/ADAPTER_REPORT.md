# Adapter Gemini function calling — báo cáo (PROVIDER GIẢ, 0 lượt gọi thật)

Mã: `backend/app/ai/function_calling.py`. Test: `backend/tests/geometry/test_ai_function_route.py` (phần D). Bằng chứng:
`offline/*/results.json` (cột `ai`), `diagnostics/fake_gemini_*.log`.

## 1. Cấu hình provider — tra tài liệu trước khi chọn (2026-10-10)

| điểm | tài liệu nói | lựa chọn |
|---|---|---|
| `functionCallingConfig.mode` | AUTO: "model decides to predict either a function call or a natural language response"; ANY: "constrained to always predicting a function call only"; NONE; VALIDATED: "validate function calls with constrained decoding"; `allowedFunctionNames` "limits the functions the model will call" | **ANY** + `allowedFunctionNames` = 24 tên của REGISTRY. VALIDATED nhận làm nhánh ablation (A2/A5 của văn liệu v2). AUTO/NONE bị `build_request` từ chối (AUTO cho phép trả lời văn bản ngoài registry) |
| gọi song song | nhiều `functionCall` trong một lượt | **một lượt gọi API mỗi đề**; không gửi `functionResponse` ngược lại |
| `FunctionCall` | `id` tuỳ chọn, `name` bắt buộc, `args` tuỳ chọn | `call_id` là tham số BẮT BUỘC trong khai báo |
| lược đồ tham số | `parameters` = tập con OpenAPI (Type, `nullable`, `enum`, `pattern`, `minItems`, `anyOf`…); có `parametersJsonSchema` thay thế | dẫn xuất từ `function_declarations()`: giải `$ref`, `anyOf[X,null]` → `nullable`, Type viết hoa, bỏ `title`/`default`/`additionalProperties` |
| `finishReason` | STOP, MAX_TOKENS, MALFORMED_FUNCTION_CALL, SAFETY, RECITATION, UNEXPECTED_TOOL_CALL, TOO_MANY_TOOL_CALLS, MISSING_THOUGHT_SIGNATURE, … | xem §2 |
| `maxOutputTokens` | trần output gồm cả thinking | **8192**, trần cứng mỗi lượt (bài học R1 của pilot G05: không đặt trần ⇒ trần token không cứng) |

Nguồn: `ai.google.dev/api/caching` (FunctionCallingConfig, Mode); `ai.google.dev/api/generate-content` (FinishReason,
UsageMetadata); proto `generativelanguage v1beta` (FunctionDeclaration, FunctionCall, Schema; bản Dart trên pub.dev). Trang
hướng dẫn function-calling hiện mô tả Interactions API mới (`tool_choice`), khác `generateContent` — adapter theo
`generateContent` như phần còn lại của kho. Cần kiểm lại trên tài khoản thật trước pilot (thought signature với model
thinking không áp dụng vì không có lượt thứ hai).

## 2. Hợp đồng phản hồi — không thực thi trước khi qua kiểm

| tình huống | mã | thực thi? |
|---|---|---|
| không ứng viên, có `promptFeedback.blockReason` / không | `PROVIDER_BLOCKED` / `NO_CANDIDATE` | không |
| `finishReason = MAX_TOKENS` (kế hoạch có thể cụt) | `RESPONSE_TRUNCATED` | không |
| `MALFORMED_FUNCTION_CALL` · lý do khác STOP | `MALFORMED_FUNCTION_CALL` · `PROVIDER_REFUSED` | không |
| chỉ có văn bản | `NO_FUNCTION_CALL` | không |
| thiếu `call_id` · trùng id khác nội dung | `CALL_ID_MISSING` · `DUPLICATE_CALL_ID` | không |
| lời gọi y hệt lặp lại | bỏ bản lặp, `dropped_identical_duplicates` | có |
| `depends_on` treo / vòng | `DANGLING_DEPENDENCY` / `DEPENDENCY_CYCLE` | không |
| hàm lạ, ô lạ (toạ độ), thiếu `quotes` | `SCHEMA_INVALID` | không |
| lỗi transport / mạng | `PROVIDER_ERROR` (chỉ tên lớp lỗi, không nguyên văn) | không |
| qua hết ⇒ cổng nguồn + engine | mã của registry/engine (`docs/architecture/TEXT_TO_GEOMETRY_FUNCTIONS_CONTRACT.md`) | chỉ khi qua |

Không có nhánh nào gọi `LLM_ONLY`: test thay `call_gemini`, `run_pipeline`, `stage_semantic_program` bằng hàm ném lỗi rồi
chạy toàn bộ 31 ca + phản hồi rỗng — không lần nào chạm. Module không nhập `pipeline`/`gemini`/`httpx` ở đầu tệp.

## 3. Kết quả (provider giả)

- 27 + 23 + 8 = **58/58** fixture qua đường đầy đủ text → phản hồi `generateContent` giả (phần `functionCall` song song)
  → registry → engine → Scene3D, khớp kết cục đăng ký trước; **đúng 1 lượt gọi transport mỗi đề**.
- 13 tình huống hỏng của §2 có test riêng; đột biến "thực thi phản hồi MAX_TOKENS" và "cho AUTO" bị bắt.
- `live_transport`: khoá trong header `x-goog-api-key` (không trong URL), kiểm `ALLOW_LIVE_AI` mỗi lần gửi, ghi `ApiBudget`
  + `usageMetadata`; test chỉ kiểm nó từ chối khi chưa bật. **Chưa gửi request thật nào.**

## 4. Bề mặt mô hình của đường mới

`surface_fingerprint()` = `09ec4a9df17bd3b900be44d7e11034b4e9f643d744f5e59219b87e457414faa8` (prompt hệ thống 626 ký tự +
24 khai báo hàm ≈ 19,8 nghìn ký tự + cấu hình). Token đầu vào mỗi lượt: **UNKNOWN** (chưa gọi `countTokens`); ước lượng
thô 6–9 nghìn. Bề mặt `LLM_ONLY` (prompt `skills/*.md`, thẻ văn phạm, lược đồ IR) không đổi; `CACHE_VERSION` 125.

## 5. Chưa kiểm (phải nói rõ)

Mô hình thật có gọi đủ lời gọi trong một lượt không; có chép quote nguyên văn không; tỉ lệ `RESPONSE_TRUNCATED` khi
thinking chiếm trần 8192; khác biệt ANY vs VALIDATED; độ dài khai báo hàm có làm giảm chất lượng không.
