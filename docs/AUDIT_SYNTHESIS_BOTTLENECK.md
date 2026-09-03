# AUDIT_SYNTHESIS_BOTTLENECK — vì sao từ vựng ĐÚNG vẫn bị dùng SAI

> Thực hiện **2026-09-04**, HEAD `42c2f0a`, cây sạch.
> **SOURCE_CHANGES = 0 · APPLICATION_LLM_CALLS = 0.** Không sửa prompt, lược đồ,
> IR, kernel, checker. V3 không chạy, pool niêm phong, seed chưa rút.
> Mọi kết luận dưới đây dẫn từ artifact `curved-ergonomics-v2-run2` và từ mã
> đang chạy — không từ trí nhớ.

## 0. Kết luận trước

```
PRIMARY_BOTTLENECK_OWNER          = MIXED  (CONTRACT + SYSTEM_FOUNDATION)
SYSTEM_FOUNDATION_GAP             = YES  ← phát hiện chính, xem §2
MODEL_REASONING_REMAINS_A_BOTTLENECK = NO (chưa có bằng chứng nào cho nó)
VISUAL_BINDINGS_MODEL_OWNED       = NO   (và mô hình KHÔNG THỂ khai — xem §3)
VISUAL_BINDINGS_DERIVABLE         = YES
STATEMENT_EXPR_BOUNDARY_ERGONOMICS = MIXED
OPERAND_NAME_ERGONOMICS           = WEAK
REPAIR_LOOP_ACTIONABILITY         = WEAK
R0_POLICY_CHANGED                 = NO
```

⚠️ **Đính chính báo cáo trước.** `CURVED_ERGONOMICS_PROBE_V2 §6` viết *"ba lỗi
lược đồ KHÔNG do thiếu từ vựng: `visual_bindings` CÓ trong `grammar_card()`"*.
**Sai.** Tôi gọi `grammar_card()` **không tham số** — bản Tin học. Bản thật sự
gửi cho đề hình học là `grammar_card("hinh_hoc")`, và nó **không có
`visual_bindings`** (4035 byte so với 4703). Kết luận đảo chiều: mô hình chưa
bao giờ được cho biết trường ấy tồn tại.

## 1. FAILURE_OWNER_MATRIX

| ca | quyết định sai ĐẦU TIÊN | cổng thấy đầu tiên | CHỦ SỞ HỮU | vòng sửa thấy? | backend dẫn được? | cần suy luận ngữ nghĩa? |
|---|---|---|---|---|---|---|
| `ball_1` | **không có** — chương trình đúng | `learner_surface` | **HỆ** | **KHÔNG** | **CÓ** | KHÔNG |
| `ball_2` | khai điểm `A` không có trong đề | synthesis → grounding | **HỆ (biểu đạt)** | một phần | KHÔNG | — không đường nào hợp lệ |
| `cylinder_2` | `intersect_plane_curved` viết như CÂU LỆNH | schema | **HỢP ĐỒNG** | **KHÔNG** | KHÔNG | KHÔNG |
| `circumsphere` | `vector_from_points` sai tên toán hạng | schema | **HỢP ĐỒNG** | CÓ | KHÔNG | KHÔNG |

**Không ca nào hỏng vì suy luận hình học.** Cả bốn hỏng ở *giao diện* hoặc ở
*nền hệ*.

## 2. `ball_1` — vòng khép kín KHÔNG CÓ LỐI RA (phát hiện chính)

Chương trình đúng tuyệt đối: `postconditions_pass = True`, `R = 6`,
`V = 288π` **đã được kiểm**. Nó chết ở `learner_surface`:

```
'IA_dist_val' mang dữ liệu đề (mục 'ia_distance') nhưng không có binding
```

Luật (2) của cổng: **mọi khai báo có `source_fact_id` phải NHÌN THẤY ĐƯỢC**.
Nhìn thấy được = có `visual_bindings` **hoặc** có mặt trên cảnh 3D
(`la_doi_tuong_hinh_hoc` hoặc `la_dai_luong_do`).

Ba lối ra, và cả ba đều bị bịt:

**① Thẻ CẤM mô hình khai binding.** Dòng 5 của thẻ hình học:
> *"Cảnh 3D dựng TỰ ĐỘNG từ các phép dựng của bạn — không khai gì thêm để hiển thị."*

**② Thẻ hình học KHÔNG CÓ `visual_bindings`.** Kể cả muốn khai, mô hình không
biết tên trường. (Đo: `"visual_bindings" in grammar_card("hinh_hoc")` → `False`.)

**③ Đường "đại lượng đo" HỎNG.** Replay tất định `ball_1`:

```
IA_dist_val   str "6"      hình học=False   đại lượng=False
R             Fraction 6   hình học=False   đại lượng=True
V             Radical 288π hình học=False   đại lượng=True
```

`interpreter` lưu `initial_value` **nguyên văn** cho mọi kiểu không-hình-học
(`self.memory[name] = deepcopy(decl.initial_value)`), còn `la_dai_luong_do` chỉ
nhận `Fraction | Radical`. Kiểm cả bốn dạng:

| giá trị lưu | `la_dai_luong_do(·, "float")` |
|---|---|
| `str "6"` (thực tế) | **False** |
| `int 6` | **False** |
| `float 6.0` | **False** |
| `Fraction(6)` | True |

⇒ **Không một khai báo vô hướng mang dữ kiện đề nào có thể qua cổng này** — bất
kể mô hình viết gì. Không phải "mô hình quên binding"; là một cổng **không thoả
mãn được** trong miền hình học.

Và nó nằm **ngoài vòng sửa**, nên mô hình cũng không bao giờ được biết.

> `SYSTEM_FOUNDATION_GAP = YES`. Đây là lỗi HỆ, và bộ phân loại của tôi ở lượt 1
> gọi đúng tên nó vì lý do sai; lượt 2 gọi sai tên nó (`MODEL_FIRST_BINDING_
> FAILURE`) vì đọc cổng mà không đọc *khả năng thoả mãn* của cổng.

## 3. `visual_bindings` — kiểm toán hạng nhất

| câu hỏi | trả lời |
|---|---|
| AI TIÊU THỤ | `validator` (phân giải tên) · `pipeline_adapter` · `visual_adapter` · `learner_surface._bound_names` |
| MANG THÔNG TIN GÌ | *biến nào gắn vào primitive 2D nào* — ngăn xếp, mảng, ô kết quả của miền **Tin học** |
| CÓ ĐỔI HÌNH HỌC KHÔNG | **KHÔNG** |
| CÓ ĐỔI SỰ THẬT CỦA CHECKER KHÔNG | **KHÔNG** |
| MIỀN HÌNH HỌC DÙNG KHÔNG | **KHÔNG** — thẻ không phơi, `scene3d` dựng tất định từ `final_memory` |
| DẪN XUẤT ĐƯỢC KHÔNG | **CÓ** — `_tren_canh_3d` đã dẫn xuất sẵn cho mọi đối tượng hình học và mọi đại lượng `Fraction/Radical`; chỗ hụt duy nhất là **vô hướng chưa ép kiểu** |

`VISUAL_BINDINGS_MODEL_OWNED = NO`, và đó **đã là thiết kế hiện tại** cho hình
học — thẻ nói thẳng "không khai gì thêm". Vấn đề không phải quyền sở hữu mà là
`learner_surface` vẫn đòi một điều kiện mà đường dẫn xuất chưa phủ hết.

Nguyên tắc kiến trúc *"đừng bắt mô hình sinh metadata backend dẫn được"* **đang
được tôn trọng**. Không cần chuyển quyền sở hữu; cần **vá đường dẫn xuất**.

## 4. Vòng sửa — topology và vì sao 9 lượt vô hiệu

```
synthesis ──► parse JSON ──► validate schema ──┐
                                               ├─► ir_static ──┐
              ◄── _prompt_sua ──────────────────┘               │
                                                grounding ◄─────┘
                     (KHONG_DUOC_SUA ⇒ DỪNG HẲN)  │
   ═══════ HẾT VÙNG VÒNG SỬA THẤY ĐƯỢC ═══════════╪═══════════
   coverage → execution → postconditions → binding → compile → learner_surface
```

`REPAIR_ENTRY` = lỗi parse/schema/ir_static/grounding-sửa-được.
`REPAIR_EXIT` = mọi cổng sau `grounding`.

**Ngoài vùng sửa, và phân loại:**

| lớp lỗi | phân loại |
|---|---|
| `LEARNER_SURFACE_INCOMPLETE` | **DETERMINISTICALLY_FIXABLE** — backend dẫn được, đừng bắt mô hình sửa (§3) |
| `POSTCONDITION_VIOLATED` (giá trị lệch) | SHOULD_BE_REPAIRABLE (nhưng ngoài phạm vi wave này) |
| `REQUESTED_OPERATION_UNCOVERED` | MUST_REMAIN_NON_REPAIRABLE — nó là *"đề ngoài IR"* |
| `UNANCHORED_DERIVED_ASSUMPTION` | **MUST_REMAIN_NON_REPAIRABLE** (§18, R0) |

### Vì sao 9 lượt sửa cứu 0 ca — đo được

`_prompt_sua` gửi **mảnh** hợp đồng do `manh_hop_dong(loi, domain)` chọn. Kiểm
trên đúng ba lỗi thật:

| ca | mảnh có chứa thứ cần? | lỗi có dịch sau sửa? |
|---|---|---|
| `cylinder_2` | `intersect_plane_curved` **KHÔNG** · mục *"biểu thức giá trị"* **KHÔNG** | **KHÔNG — y nguyên** |
| `circumsphere` | `vector_from_points` CÓ · `from_point` CÓ | có dịch (5 lỗi → 4) nhưng **cùng loại** |
| `ball_2` | `source_fact_id` CÓ · `declare_point` CÓ | có dịch: schema → **R0** (rồi dừng đúng luật) |

`cylinder_2` là ca nặng nhất: mô hình bị báo *"`intersect_plane_curved` không
khớp tag câu lệnh nào"* rồi được đưa **danh sách câu lệnh** — mảnh ấy **giấu
mất** chỗ operation đó thật sự sống (mục biểu thức). Vòng sửa **cấu trúc không
thể** giải lỗi này.

⇒ `REPAIR_LOOP_ACTIONABILITY = WEAK`, và nguyên nhân là **bộ chọn mảnh**, không
phải mô hình.

## 5. Ranh giới CÂU LỆNH ↔ BIỂU THỨC

Thẻ **CÓ** phân nhóm rõ: dòng 10 `statements[] — mỗi phần tử có kind` (9 phép),
dòng 21 `biểu thức giá trị — cũng có kind` (15 phép). `intersect_plane_curved`
nằm đúng nhóm biểu thức (dòng 26).

`IS_STATEMENT_EXPR_BOUNDARY_EXPLICIT = YES`. Vậy vì sao vẫn dễ dùng nhầm:

1. **Hai nhóm trông y hệt nhau.** Mỗi mục là `tên: trường:kiểu trường:kiểu`.
   Không gì **trong bản thân dòng** nói nó thuộc nhóm nào; chỉ tiêu đề cách đó
   5–15 dòng phân biệt.
2. **Cặp bẫy trực tiếp:**
   ```
   dòng 17  construct_section:        target_var solid:tên<solid>  plane:tên<plane3>   ← CÂU LỆNH
   dòng 26  intersect_plane_curved:              solid:tên<curved_solid> plane:tên<plane3> ← BIỂU THỨC
   ```
   Cùng tên toán hạng `solid`/`plane`, hình dạng gần trùng, **khác nhóm**. Suy
   loại suy từ dòng 17 sang dòng 26 là con đường ngắn nhất tới đúng lỗi đã xảy ra.
3. **`assign` không có ví dụ.** Dòng 11 nói `assign: target_var:tên expr:biểu
   thức` — `biểu thức` là một từ trừu tượng, không có một ca mẫu nào cho thấy
   `assign` bọc một phép tên gì.

⇒ `MIXED`: nhóm đúng, nhưng **affordance ở mức từng dòng bằng không**.

## 6. Tên toán hạng — `WEAK`, đo được

Năm phép nhận **hai toán hạng `point3`**, bốn quy ước khác nhau:

| phép | tên toán hạng |
|---|---|
| `divide_segment` | `a`, `b` |
| `midpoint` | `a`, `b` |
| `construct_line` | `through_a`, `through_b` |
| `construct_curved_solid` | `anchor`, `rim_point` |
| **`vector_from_points`** | **`from_point`, `to_point`** |

(Trong khi cặp `line3` và cặp `plane3` lại nhất quán: `line_a/line_b`,
`plane_a/plane_b`.)

Quy ước phổ biến nhất cho cặp điểm là `a`/`b` (2/5). `vector_from_points` là
phép duy nhất dùng `from_/to_`.

**Bằng chứng độc lập rằng đây là bẫy thật, không phải lỗi mô hình:** khi viết
`certify_acceptance_runner.py` tôi gõ `{"a": "O", "b": "A"}` cho
`vector_from_points` và bị Pydantic bác — **đúng lỗi mà mô hình mắc**, cùng ngày,
với cả thẻ mở trước mặt.

⚠️ §13 — bản sửa tương lai phải đến từ **thẩm quyền chữ ký** (`contract.py` →
`grammar_card` sinh ra), không phải chép tay vào prompt. `ONE_SIGNATURE_AUTHORITY`
còn nguyên và phải giữ nguyên.

## 7. Thẻ văn phạm — `GRAMMAR_STRUCTURAL_GROUPING = MIXED`

| | |
|---|---|
| phép CÂU LỆNH | 9 |
| phép BIỂU THỨC | 15 |
| có phân nhóm câu lệnh / biểu thức | **CÓ** |
| có phân nhóm dựng / đo / giao / biến đổi | **KHÔNG** — 15 biểu thức xếp một dãy phẳng theo abc |
| ⚠️ **dòng 8 khai kiểu SAI** | `type nhận đúng một trong: bool float point3 vector3 line3 plane3 polygon3 solid section` — **thiếu `curved_solid` và `circle3`**, trong khi chính thẻ dùng cả hai làm kiểu toán hạng ở dòng 12/26/46/48 |

Dòng 8 là một lỗi thẻ thật: `ball_1` **phải** khai `S: curved_solid` để chạy
được, tức phải dùng một kiểu mà thẻ nói là không hợp lệ.

## 8. `ball_2` — KHÔNG có đường hợp thành (§19)

Đề: *"mặt cầu tâm O bán kính bằng 13"* — cho **một điểm có tên** và **một số**.

`construct_curved_solid` đòi `anchor:tên<point3>` + `rim_point:tên<point3>` —
**hai điểm CÓ TÊN**. Đề không nêu điểm nào trên mặt cầu.

Có dựng được một điểm cách `O` đúng 13 không? Duyệt hết 15 biểu thức:

- `translate(point, vector)` → cần `vector3` có tên;
- `vector_from_points(from, to)` → cần **hai điểm đã có tên**;
- `divide_segment(a, b, ratio)`, `midpoint(a, b)` → cần hai điểm đã có tên;
- `project_onto`, `intersect_*` → cần đường/mặt đã dựng từ điểm đã có tên.

⇒ **Vòng tròn.** Không phép nào sinh được một điểm từ *một điểm + một khoảng
cách vô hướng*. Lối duy nhất là khai toạ độ cho một điểm đề không nêu — và R0
bác đúng: *"`model_assumption` chỉ nói về CÁCH ĐẶT một đối tượng đề đã nêu"*.

Phân loại theo §19: **C — không tồn tại đường dựng hợp lệ.** Đây **không** phải
ecgônômi và **không** phải lỗi mô hình; là **khoảng trống biểu đạt của IR** cho
một dạng SGK rất phổ biến ("mặt cầu tâm O bán kính R").

`R0_POLICY_CHANGED = NO` — không nới R0 để tăng tỉ lệ. Nếu muốn đóng, phải mở
đường **dựng** (một phép sinh điểm từ điểm + độ dài có nguồn), không phải nới cổng.

## 9. `circumsphere` (§20)

Hệ **đã** chứng minh dựng được mặt cầu ngoại tiếp bằng hợp thành
(`test_radius_verification::test_T7`: ba mặt trung trực → giao → tâm `(1,1,1)`,
`R = √3`). Nên khó khăn **không** nằm ở suy luận.

Lỗi thật: `vector_from_points.from_point = null` ở `statements[1]` và `[3]`,
lặp lại y nguyên sau lượt sửa. Toàn bộ thứ cần đều có trong thẻ.

⇒ **OPERAND-NAME ERROR**, không phải deep reasoning. Tách bạch được vì mô hình
đã dựng đúng khung 4 câu lệnh và chỉ sai tên trường.

## 10. Độ sâu hợp thành (§21) — mô tả, không quy nhân quả

| ca | khai | lệnh | sâu biểu thức | kết cục |
|---|---|---|---|---|
| §18 `ball_1` | 5 | 3 | 2 | tới `postconditions` |
| §18 `circumsphere` | 7 | 4 | 2 | tới `grounding` |
| run2 `ball_1` | 6 | 3 | 2 | tới `learner_surface` |
| run2 `ball_2` / `cylinder_2` / `circumsphere` | — | — | — | chết ở **schema**, chương trình không tồn tại |

Ba trong bốn ca run2 hỏng **trước khi có chương trình để đo độ sâu**. Với bốn ca,
**không có bằng chứng nào cho tương quan giữa độ sâu và thất bại**; mọi thất bại
quan sát được là **cú pháp giao diện**, không phải chiều sâu hợp thành.

## 11. Chi phí bề mặt mô hình (§22)

| | byte | tỉ lệ |
|---|---|---|
| skill prompt (`geometry_program_generator.md`) | 5 674 | 4.7% |
| thẻ văn phạm hình học | 4 035 | 3.3% |
| **JSON schema (`responseSchema`)** | **111 152** | **92.0%** |
| tổng | 120 861 | |

Schema có **56 `$defs`**, trong đó **39 KHÔNG liên quan hình học**: `PushStmt`,
`PopStmt`, `EnqueueStmt`, `MapSetStmt`, `ForRangeStmt`, `SwapStmt`,
`WriteIndexStmt`, `NeighborsExpr`… — toàn bộ IR Tin học, gửi kèm mọi đề hình học.

Mô hình đang đi trong **một hợp đồng lớn và phẳng**, nơi 92% bề mặt là schema và
2/3 số định nghĩa vô can. Phần *dạy cách viết IR hình học* chiếm 3.3%.

## 12. Ba ứng viên (§23–§24)

### CANDIDATE_1 — `SCALAR_FACT_VISIBILITY` (backend, tất định)

Đóng vòng khép kín §2: để một khai báo vô hướng mang `source_fact_id` **có thể**
nhìn thấy được. Hai thiết kế con, wave sau chọn:
(a) ép `initial_value` vô hướng về miền số chính xác lúc nạp bộ nhớ; hoặc
(b) `learner_surface` luật (2) đọc `source_fact_id` trên **giá trị đã nạp** với
cùng vị từ mà cảnh dùng.

| | |
|---|---|
| ROOT_CAUSE_COVERAGE | `ball_1` + **mọi** đề hình học có dữ kiện vô hướng (IA = 6, R = 13, h = 8…) — dạng phổ biến nhất của SGK |
| SYSTEM_COMPLEXITY | thấp, một tầng |
| MODEL_TOKEN_DELTA | 0 |
| MODEL_FACING_SCHEMA_CHANGE | **KHÔNG** |
| CAPABILITY_CHANGE | KHÔNG (không phép mới) |
| CACHE_IMPACT | **CÓ bump** — envelope cũ mang `servable=False` cho ca hệ nay phục vụ được (đúng tiền lệ 69/71) |
| R0_RISK | **không** — không đụng grounding |
| LIKELY_CASES_AFFECTED | 1/4 ngay, và mọi đề tương lai cùng dạng |

### CANDIDATE_2 — `REPAIR_FRAGMENT_COMPLETENESS` (backend, tất định)

`manh_hop_dong` phải luôn kèm **mục chứa phép được nêu tên trong lỗi**. Lỗi
*"`intersect_plane_curved` không phải tag câu lệnh"* mà không kèm mục biểu thức
là gửi mô hình đi sửa với đáp án bị che.

| | |
|---|---|
| ROOT_CAUSE_COVERAGE | `cylinder_2` + mọi lỗi nhầm nhóm sau này; cứu được phần lớn 9 lượt sửa vô hiệu |
| SYSTEM_COMPLEXITY | thấp |
| MODEL_TOKEN_DELTA | +vài trăm byte mỗi lượt sửa |
| MODEL_FACING_SCHEMA_CHANGE | KHÔNG (schema không đổi; **nội dung prompt sửa** đổi) |
| CAPABILITY_CHANGE | KHÔNG |
| CACHE_IMPACT | vân tay `grammar_card` **có thể** đổi ⇒ phải đo, có thể bump |
| R0_RISK | không |
| LIKELY_CASES_AFFECTED | 1/4 ngay, mọi lượt sửa về sau |

### CANDIDATE_3 — `SIGNATURE_SURFACE_ERGONOMICS` (thẩm quyền chữ ký)

Sinh thẻ **theo nhóm** (dựng / giao / biến đổi / đo) + đánh dấu nhóm **ngay
trên từng dòng**, và soát lại quy ước tên toán hạng cặp điểm; đồng thời sửa dòng
8 (thiếu `curved_solid`, `circle3`). Tất cả **sinh từ `contract.py`**, không chép
tay vào prompt.

| | |
|---|---|
| ROOT_CAUSE_COVERAGE | `circumsphere` + `cylinder_2` (một phần) |
| SYSTEM_COMPLEXITY | trung bình |
| MODEL_TOKEN_DELTA | ~0 (tổ chức lại, không thêm) |
| MODEL_FACING_SCHEMA_CHANGE | **CÓ** nếu đổi tên toán hạng ⇒ phá tương thích |
| CAPABILITY_CHANGE | KHÔNG |
| CACHE_IMPACT | **CÓ bump chắc chắn** |
| R0_RISK | không |
| LIKELY_CASES_AFFECTED | 2/4, nhưng rủi ro cao nhất |

### Xếp hạng

```
P0  CANDIDATE_1  SCALAR_FACT_VISIBILITY
P1  CANDIDATE_2  REPAIR_FRAGMENT_COMPLETENESS
P2  CANDIDATE_3  SIGNATURE_SURFACE_ERGONOMICS
```

P0 vì: phủ rộng nhất, **không đổi một byte bề mặt mô hình**, không rủi ro R0,
và nó đóng một cổng **chứng minh được là không thoả mãn** — thứ đắt nhất trong
ba, vì nó biến một chương trình đã đúng toàn phần thành một kết quả phục vụ được.

## 13. Bác bỏ (§25)

| đề xuất | phán quyết | vì sao — từ bằng chứng |
|---|---|---|
| `ADD_NEW_GEOMETRY_PRIMITIVE` | **REJECTED** | không ca nào hỏng vì thiếu phép. `circumsphere` đã dựng được bằng hợp thành (`test_T7`). ⚠️ **Ngoại lệ cần cân nhắc riêng**: `ball_2` (§8) hỏng vì *đúng* thiếu đường dựng — nhưng đó là kết luận của một audit riêng, không phải của wave này |
| `ADD_CURVED_TEMPLATE` | **REJECTED** | mẫu theo dạng bài phá *"bài mới ≠ mã mới"*; và không lỗi nào thuộc dạng bài |
| `KEEP_GROWING_PROMPT` | **REJECTED** | prompt chỉ chiếm 4.7% bề mặt; ba lỗi thuộc **chữ ký** và **mảnh hợp đồng lúc sửa**, cả hai đều có chủ khác (§15) |
| `WEAKEN_GROUNDING` | **REJECTED** | R0 chạy đúng ở cả `ball_2` lẫn `circumsphere`. `CURVED_GEOMETRY_LAUNDERING = 0` |
| `RUN_V3_NOW` | **REJECTED** | 0/4 ca phát triển phục vụ được; V3 sẽ đo một hệ có một cổng không thoả mãn được |

## 14. Giới hạn của chính audit này

- **Bốn ca.** Mọi phát biểu về tần suất đều là mô tả, không phải ước lượng.
- **Chương trình hỏng lược đồ KHÔNG được lưu.** `run_curved_ergonomics_v2` chỉ
  ghi `chuong_trinh` khi nó parse được, nên với ba ca `MODEL_SCHEMA_FAILURE` tôi
  chỉ có thông điệp lỗi, không có văn bản mô hình thật sự viết. Đây là lỗ của
  **runner của tôi** so với chính §4 của `ACCEPTANCE_RUNNER_INTEGRITY` (*"persist
  Semantic Program candidate(s)"*) — phân tích nguyên nhân bị hạn chế đúng ở lớp
  lỗi phổ biến nhất. Sửa nó thuộc bộ đo, rẻ, và nên đi kèm wave sau.
- **`MISSED_EXISTING_COMPOSITION` vẫn không đo được bằng máy** — cần oracle mức
  chương trình, kho chưa có.

## 15. Quyết định

```
PRIMARY_BOTTLENECK_OWNER             MIXED (CONTRACT + SYSTEM_FOUNDATION)
VISUAL_BINDINGS_MODEL_OWNED          NO
VISUAL_BINDINGS_DERIVABLE            YES
STATEMENT_EXPR_BOUNDARY_ERGONOMICS   MIXED
OPERAND_NAME_ERGONOMICS              WEAK
REPAIR_LOOP_ACTIONABILITY            WEAK
MODEL_REASONING_REMAINS_A_BOTTLENECK NO
SYSTEM_FOUNDATION_GAP                YES
R0_POLICY_CHANGED                    NO
RUN_V3_NOW                           NO

NEXT_ACTION = SCALAR_FACT_VISIBILITY
              (backend tất định · 0 lượt gọi model · không đổi bề mặt mô hình
               · kèm bump CACHE_VERSION theo tiền lệ 69/71)
```
