# REPAIR_FRAGMENT_COMPLETENESS — nói cho mô hình biết dạng ĐÚNG nằm ở đâu

> Thực hiện **2026-09-04**, trên HEAD `b135aee`, cây sạch.
> **APPLICATION_LLM_CALLS = 0.** Không đổi prompt tổng hợp, thẻ văn phạm, lược
> đồ, IR, kernel, checker. Không chạy probe, không chạy V3, pool giữ niêm phong.

## 0. Kết luận trước

```
REPAIR_FRAGMENT_COMPLETENESS      = CLOSED
CYLINDER_2_REPAIR_CONTEXT         = COMPLETE
CIRCUMSPHERE_REPAIR_CONTEXT       = COMPLETE
SIGNATURE_AUTHORITIES             = 1
REPAIR_FRAGMENT_TARGETED          = YES
REPAIR_ELIGIBILITY_POLICY_CHANGED = NO   ·  R0_POLICY_CHANGED = NO
RAW_SCHEMA_FAILURE_CANDIDATE_PERSISTED = YES
RAW_PARSE_FAILURE_CANDIDATE_PERSISTED  = YES
CACHE_VERSION 72 → 72 (KHÔNG bump — §5)
```

## 1. Nguyên nhân gốc — và nó KHÔNG phải "thiếu mục biểu thức"

Chẩn đoán ban đầu nói mảnh hợp đồng *"bỏ mục biểu thức"*. Đo lại chính xác hơn:
dòng ấy **có khớp**, nhưng bị **cắt**.

`cylinder_2` viết `intersect_plane_curved` như một câu lệnh. Lời từ chối của
Pydantic liệt kê **mọi tag câu lệnh hợp lệ**. Bộ chọn cũ rút định danh từ lời
từ chối rồi giữ mọi dòng thẻ chứa chúng — nên **chín dòng câu lệnh ấy khớp
trước**, và dòng định nghĩa `intersect_plane_curved`, đứng thứ **14/15**, rơi
ngoài trần `toi_da=12`.

```
  ✓ statements[] — mỗi phần tử có `kind` …        ← khớp
  ✓ assign / construct_curved_solid / …           ← chín dòng, chiếm hết trần
  ✂ intersect_plane_curved: solid:… plane:…        ← thứ 14, BỊ CẮT
```

Nói cách khác: **chính danh sách "tag hợp lệ" trong lỗi đã đẩy câu trả lời ra
khỏi ngữ cảnh.** Mô hình nhận *"sai ở đâu"* mà không nhận *"dạng đúng ở đâu"* —
chín lượt sửa cứu 0 ca.

## 2. Bản vá — hai tầng, tầng đầu miễn trừ khỏi trần

| | |
|---|---|
| `REPAIR_FRAGMENT_OWNER` | `grammar_card.manh_hop_dong` |
| `REPAIR_CONTEXT_OWNER` | `pipeline._prompt_sua` (không đổi) |
| `SIGNATURE_AUTHORITY` | model Pydantic ở `contract.py` → thẻ; phân nhóm từ `_tap_hinh_hoc()` (`_KIEU_DUNG` / `_CHU_KY`) |
| `SIGNATURE_AUTHORITIES` | **1** |

**Tầng ①, dẫn từ CẤU TRÚC lỗi** — không khớp chuỗi tiếng Việt:

```
Input tag 'X' found using 'kind'                    → X
statements.1.assign.expr.vector_from_points.…       → assign, vector_from_points
```

Với mỗi phép nêu tên, kèm **đúng mục của nó**: tiêu đề nhóm + dòng chữ ký; và
nếu là BIỂU THỨC thì kèm `assign` — cửa duy nhất tiêu thụ biểu thức. Ba mảnh ấy
trả lời trọn vẹn *"sai gì · thuộc nhóm nào · dùng thế nào"* mà không cần một câu
văn xuôi nào (§10).

**Tầng ②** giữ nguyên phép khớp định danh cũ, lấp phần trần còn lại.

Tiêu đề hai nhóm hoá thành hằng số `_TIEU_DE_LENH` / `_TIEU_DE_BIEU_THUC`, dùng
chung cho bên **dựng** thẻ và bên **chọn** mảnh — để hai nơi tự gõ lại chuỗi thì
đổi tiêu đề một bên là mảnh lặng lẽ mất phần chỉ nhóm.

### Trước → sau

| ca | mảnh TRƯỚC | mảnh SAU | có `<phép>:` | có tiêu đề nhóm | có `assign:` |
|---|---|---|---|---|---|
| `cylinder_2` | thiếu dòng phép | **1085 byte** | ✓ | ✓ | ✓ |
| `circumsphere` | 816 byte | **863 byte** | ✓ | ✓ | ✓ |
| `ball_2` | 777 byte | **777 byte** | ✓ | ✓ | — (lỗi câu lệnh) |

Cả thẻ hình học là **4035 byte**; lược đồ JSON là **111 KB**. `REPAIR_FRAGMENT_
TARGETED = YES` — mảnh dưới 60% cả thẻ, và không bao giờ là bản đổ lược đồ (§4,
khoá bằng test).

## 3. Chấm lại 9 lượt sửa lịch sử (§22) — 0 lượt gọi

Chỉ sinh lại **ngữ cảnh**, không gọi model, không tuyên bố mô hình sẽ thành công.

| ca | lượt | TRƯỚC | SAU | phép mà lỗi nêu tên |
|---|---|---|---|---|
| `ball_2` | one-shot | ĐỦ | ĐỦ | `construct_plane` |
| `cylinder_2` | one-shot | ĐỦ | ĐỦ | `construct_plane` |
| **`cylinder_2`** | **sửa** | **THIẾU** | **ĐỦ** | `intersect_plane_curved` |
| `circumsphere` | one-shot | ĐỦ | ĐỦ | `construct_plane`, `construct_line` |
| `circumsphere` | sửa | ĐỦ | ĐỦ | `assign`, `vector_from_points` |

```
REPAIR_CONTEXT_INCOMPLETE_BEFORE  1
REPAIR_CONTEXT_COMPLETE_AFTER     5
```

⚠️ **Chỉ 5 trong 9 lượt để lại một lỗi ghi được**: artifact lưu lỗi CUỐI của mỗi
chặng, không lưu từng lượt bên trong vòng sửa của pipeline. Con số "9 lượt" đến
từ telemetry (`calls`), không từ 9 bản ghi lỗi. Nói *"1/9 thiếu"* là sai; nói
*"1 trong 5 lỗi ghi được là thiếu, và nó đúng là ca chặn"* mới đúng.

Và điều này cũng cho thấy vì sao phần B của wave cần thiết.

## 4. Phần B — văn bản THÔ sống sót

| | |
|---|---|
| `RAW_MODEL_OUTPUT_OWNER` | biến cục bộ `raw` trong `pipeline._sinh_chuong_trinh` |
| `RAW_OBSERVER_CHANNEL` | sự kiện mới `semantic_program_candidate` qua `_emit` |
| nơi lưu | `run_curved_ergonomics_v2` → `raw_candidates` trong artifact từng ca |

Phát **ngay sau khi có `raw`, TRƯỚC `json.loads`** — một đầu ra không parse được
là đúng loại đáng xem nhất, và sau parse thì không còn gì.

**Quan trắc ≠ ngữ nghĩa sản phẩm** (§13). Sự kiện thụ động (bất biến #22):
đường sản phẩm truyền `observer=None` nên `_emit` là no-op; không nhánh nào đọc
lại nó. Nó không vào thực thi, không đổi phán quyết thẩm định, không vào khoá
cache, không chạm checker. Khoá bởi `test_observer_None_thi_khong_doi_gi`.

**Biên ghi log (§15):** sink duy nhất là `DiagnosticObserver` → vòng đệm
`route_trace._kho` (`deque` có `maxlen`), bật bằng `SEMANTIC_TELEMETRY`, đọc qua
endpoint chẩn đoán. **Không** vào log hay UI của học sinh. Bộ đo lấy văn bản thô
qua observer riêng của nó, không qua sink ấy.

Ba ca khoá: không parse được JSON · JSON đúng mà lược đồ hỏng · văn bản y
nguyên từng byte và là sự kiện ĐẦU TIÊN của lượt.

## 5. Cache (§24) — **KHÔNG bump**, và đây là lý do

Câu hỏi của cổng: *envelope đã cache có còn đúng dưới bản mới không?*

Đọc `main.py`: **chỉ envelope THÀNH CÔNG mới được cache** —
`if envelope.get("status") == "ok"`, kèm chú thích *"Không cache unsupported để
tránh kẹt kết quả cũ khi năng lực được cải thiện (chống stale)"*.

Hệ quả:

- Đề mà tổng hợp **thất bại** chưa bao giờ vào cache, nên ngữ cảnh sửa tốt hơn
  được dùng ngay ở mọi lượt sau — **không có gì để vô hiệu hoá**.
- Envelope đã cache là những lượt **thành công**, đúng toán học và phục vụ được;
  ngữ cảnh sửa mới không thể làm chúng sai đi.

⇒ Không bump. Đối chiếu wave trước (`SCALAR_FACT_VISIBILITY`, 71→72): ở đó **có**
envelope sai để vô hiệu hoá (`servable=False` cho ca hệ nay phục vụ được). Cùng
một tiêu chí, hai kết luận khác nhau.

## 6. Danh tính (§23, §25)

| | |
|---|---|
| `SYNTHESIS_PROMPT_CHANGED` | **NO** — `prompts` `55ac1ca6…` không đổi |
| `SYNTHESIS_SCHEMA_CHANGED` | **NO** — `421e7aff…` không đổi |
| `GRAMMAR_CARD_CHANGED` | **NO** — `2463652c…` không đổi (hằng số tiêu đề hoá, byte thẻ y nguyên) |
| `ANALYZE_SCHEMA_CHANGED` | **NO** — `a4d5ed7c…` không đổi |
| `REPAIR_CONTEXT_CHANGED` | **YES** |
| `STABLE_CAPABILITY_HASH_CHANGED` | **NO** — `5b61b9ea…` |
| `SEMANTIC_ENV_HASH_CHANGED` | **NO** — `36be94cf…` |
| `CACHE_VERSION` | `72` → `72` |
| candidate | đóng băng lại (`app/` có đổi) |

§25 không phải lo: thêm payload observer **không** làm `semantic_environment_hash`
nhúc nhích, vì vân tay ấy băm prompt/thẻ/hai lược đồ/năng lực — không băm mã.
Chỉ candidate (băm cây `app/`) đổi, và đó đúng thứ nó sinh ra để bắt.

## 7. Hồi quy — 0 API call

| cổng | kết quả |
|---|---|
| pytest | **3214 pass**, 1 skip, 1 deselect |
| vitest | **687 pass / 50 file** |
| `tsc -b && vite build` | PASS |
| `replay_demo_cases.py` | **5/5** · `REDUCED_CHAIN 1/1` |
| `certify_acceptance_runner.py` | **RUNNER_CERTIFICATION PASS** |
| `lock_cache_identity.py --verify` | PASS |
| `freeze_evaluation_candidate.py --verify` | PASS sau khi đóng băng lại |

## 8. Giới hạn — khai thẳng

- **Wave này chứng minh CHẤT LƯỢNG PHẢN HỒI, không chứng minh mô hình sẽ sửa
  được.** Không lượt gọi nào được thực hiện; mọi kết luận là về nội dung ngữ
  cảnh. Có sửa được hay không chỉ một lượt sống mới trả lời.
- **`circumsphere` đã có đủ ngữ cảnh từ trước** mà vẫn hỏng ba lượt liên tiếp
  với cùng lỗi tên toán hạng. Ngữ cảnh đầy đủ là điều kiện cần, rõ ràng chưa đủ
  — đó là dữ liệu cho `AUDIT_MODEL_FACING_SCHEMA_SURFACE`.
- Artifact lịch sử (V1/V2, probe §18, run2) **không sửa một byte**.

## 9. Việc kế tiếp

```
NEXT_ACTION = AUDIT_MODEL_FACING_SCHEMA_SURFACE
```

Chọn nó thay vì `BALL_CENTER_RADIUS_EXPRESSIVENESS` vì bằng chứng chỉ về phía
bề mặt hợp đồng: 92% vật liệu gửi mô hình là lược đồ 111 KB với 39/56 `$defs`
không liên quan hình học, và `circumsphere` hỏng lặp lại ở **tên toán hạng**
ngay cả khi ngữ cảnh đã đủ. `BALL_CENTER_RADIUS_EXPRESSIVENESS` (§8 của audit —
`construct_curved_solid` đòi hai điểm CÓ TÊN trong khi đề chỉ cho tâm + số) vẫn
mở và vẫn đáng làm, nhưng nó **mở năng lực**, nên phải là một quyết định riêng.

⚠️ **KHÔNG chạy V3.** Pool giữ niêm phong, seed chưa rút.
`CURVED_SYNTHESIS_ERGONOMICS = NO_MEASURABLE_GAIN` không đổi.
