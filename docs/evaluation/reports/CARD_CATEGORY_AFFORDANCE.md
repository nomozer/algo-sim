# CARD_CATEGORY_AFFORDANCE — mỗi dòng thẻ tự khai loại của nó

> Thực hiện **2026-09-04**, trên HEAD `743336a`, cây sạch.
> **APPLICATION_LLM_CALLS = 0.** Không đổi IR, runtime, checker, grounding,
> lược đồ Pydantic, sanitizer. Không chạy probe, không chạy V3, pool niêm phong.

## 0. Kết luận trước

```
CARD_CATEGORY_AFFORDANCE            = CLOSED
PER_LINE_CATEGORY_VISIBLE           = YES
EXPRESSION_CONSUMER_AFFORDANCE      = GENERATED
CYLINDER_2_CATEGORY_DISCOVERABILITY = PASS
CATEGORY_AUTHORITIES = 1 · SIGNATURE_AUTHORITIES = 1
SKILL_PROMPT_CHANGED = NO · SYNTHESIS_SCHEMA_CHANGED = NO
IR_LANGUAGE_CHANGED = NO · GEOMETRY_RUNTIME_CHANGED = NO
STABLE_CAPABILITY_HASH_CHANGED = NO
CACHE_VERSION 72 → 73
```

⚠️ Wave này còn phải sửa **một lỗ danh tính** phát hiện giữa đường — xem §5.
Không sửa nó thì chính thay đổi này **vô hình** với cổng khoá cache.

## 1. Prompt đã dạy gì chưa? (§2)

Đọc `geometry_program_generator.md` **trước** khi đụng thẻ. Nó mở đầu bằng:

> *"Thẻ văn phạm gửi kèm đã ràng buộc cấu trúc và mọi giá trị hợp lệ; đừng nhắc
> lại chúng. Dưới đây chỉ là những điều thẻ KHÔNG nói được."*

Đếm bằng máy trong prompt: `assign` **0** lần · `biểu thức` **0** lần ·
`statements[]` **0** lần.

```
PROMPT_CATEGORY_GUIDANCE = NONE
```

Prompt **cố ý** giao cấu trúc cho thẻ. Nên đặt nhãn loại vào thẻ đúng là phân
công đã ghi sẵn — không trùng lặp, không mâu thuẫn, và `SKILL_PROMPT_CHANGED
= NO` không phải một sự kiềm chế mà là hệ quả của chính nguyên tắc ấy.

## 2. Sở hữu (§3)

| | |
|---|---|
| `CARD_GENERATOR_OWNER` | `grammar_card._the_hinh_hoc` / `_khoi_loc` |
| `CATEGORY_AUTHORITY` | `_tap_hinh_hoc()` → `_KIEU_DUNG` (lệnh) · `_CHU_KY` (biểu thức) |
| `SIGNATURE_AUTHORITY` | model Pydantic ở `contract.py`, qua `_truong` |
| **cửa tiêu thụ** | **`_cua_tieu_thu()`** — mới, DẪN từ model |
| `CATEGORY_AUTHORITIES` | **1** · `SIGNATURE_AUTHORITIES` **1** |

`_cua_tieu_thu` đọc trường nào của một câu lệnh là **union phân biệt** (tức một
ô nhận biểu thức) rồi lật ánh xạ. Nhờ vậy `construct_point` — vốn nhận
`PointExpr` — **tự** xuất hiện làm cửa của `midpoint`, `project_onto`,
`divide_segment`… mà không ai viết tay, và thêm một câu lệnh nhận biểu thức thì
nhãn tự đúng.

## 3. Trước → sau

```
TRƯỚC
  construct_section: target_var:tên solid:tên<solid> plane:tên<plane3> label?:nhãn
  intersect_plane_curved: solid:tên<curved_solid> plane:tên<plane3>

SAU
  [LỆNH] construct_section: target_var:tên solid:tên<solid> plane:tên<plane3> …
  [BIỂU THỨC→assign] intersect_plane_curved: solid:tên<curved_solid> plane:…
  [BIỂU THỨC→assign|construct_point] midpoint: a:tên<point3> b:tên<point3>
```

`CYLINDER_2_CATEGORY_DISCOVERABILITY = PASS`: từ **một dòng** trả lời được cả
hai câu mà `cylinder_2` trả lời sai — *phép này loại gì* · *dùng ở đâu*.

Cặp bẫy nay phân biệt được **tại chỗ**: `construct_section` và
`intersect_plane_curved` vẫn cùng toán hạng `solid`+`plane`, vẫn cách nhau 9
dòng, nhưng nhãn đầu dòng khác nhau.

`_nhan_loai` **NÉM** khi một biểu thức không có cửa nào nhận (§7) — im lặng bỏ
nhãn là quay về đúng trạng thái wave này đi sửa, mà không gì đỏ.

## 4. Kích thước (§13, §14)

| | |
|---|---|
| `GRAMMAR_CARD_BYTES_BEFORE` | 4 035 |
| `GRAMMAR_CARD_BYTES_AFTER` | **4 587** |
| `GRAMMAR_CARD_DELTA` | **+552 (+13.7%)** |
| `MODEL_CONTRACT_BYTES_BEFORE` | 10 535 |
| `MODEL_CONTRACT_BYTES_AFTER` | **11 087 (+5.2%)** |
| `responseSchema` | **0 — vẫn bị sanitizer bỏ vì có `$ref`** |

Trần chống nhồi prompt của thẻ hình học nâng **4200 → 4650**, ghi vào chính
changelog của `test_the_du_gon_de_khong_thanh_nhoi_prompt` theo lệ file ấy: đây
là **nhãn**, không phải văn xuôi và không phải từ vựng mới — cùng loại với hai
lần nâng trước (`tên` → `tên<point3>`, nhãn `[x,y,z]`), và mỗi lần đều vì một
nhãn thiếu/sai đã đo được bằng lượt sống.

⚠️ **Không** nhắc lại: 111 KB lược đồ **không phải** đầu vào của mô hình.

## 5. Lỗ danh tính phát hiện giữa wave — và phải sửa để wave này có nghĩa

`runtime_identity.skill_fingerprint` băm `grammar_card()` — bản **MẶC ĐỊNH**,
tức thẻ **Tin học**. Nhưng thứ ghép vào user message của sản phẩm là
`grammar_card("hinh_hoc")`.

```
grammar_card()           2463652cd8d328ad   ← ĐƯỢC BĂM, không ai gửi
grammar_card('hinh_hoc') 2166641c093a844c   ← ĐƯỢC GỬI, không ai băm
```

Hệ quả: sửa đúng cái thẻ mô hình đọc thì vân tay **không nhúc nhích**; sửa một
thẻ không ai gửi thì nó đỏ. Đúng lớp lỗi *"nghĩa đổi mà danh tính không đổi"*
mà chính vân tay ấy sinh ra để chặn — và nó nằm **ngay trong** vân tay ấy.

§24 bảo *"nếu guard báo nhiều hơn `['grammar_card']` thì audit trước khi tiếp"*.
Ở đây rủi ro ngược lại: nó sẽ báo **không có gì**. Đã sửa: băm **cả hai** bản.

Sau khi sửa, cổng báo đúng một thành phần:

```
thành phần đổi: ['grammar_card']
```

## 6. Danh tính (§21–§25)

| | trước | sau |
|---|---|---|
| `prompts` | `55ac1ca6a6df92ce…` | **không đổi** |
| `synthesis_schema` | `421e7aff8557dc17…` | **không đổi** |
| `analyze_schema` | `a4d5ed7c65a68007…` | **không đổi** |
| `stable_capability_hash` | `5b61b9ea76d0c764…` | **không đổi** |
| `grammar_card` | `2463652cd8d328ad…` | **`02415cb3b6d54b31…`** |
| `semantic_environment_hash` | `36be94cf2258e116…` | **`b428609fbdb9d48a…`** |
| `CACHE_VERSION` | `72` | **`73`** |
| candidate | | đóng băng lại |

Cô lập hoàn hảo: **chỉ** `grammar_card` động.

### Vì sao BUMP (§25)

Cổng hỏi: *envelope đã cache có còn đúng dưới bản mới không?*

Bề mặt mô hình đổi. Tiền lệ của chính kho này cho đúng lớp thay đổi ấy:

- **bump 65** — họ hình cong vào văn phạm model-facing (đổi **thẻ**);
- **bump 70** — prompt sinh chương trình đổi. Lý do ghi nguyên văn: *"cache khoá
  theo text đã chuẩn hoá + CACHE_VERSION, nên đề cũ sẽ trả về chương trình sinh
  bởi PROMPT CŨ… Không bump là đo prompt mới bằng kết quả prompt cũ, và tự kết
  luận rằng sửa prompt chẳng thay đổi gì."*

Lập luận ấy áp ở đây không sửa một chữ. Đối chiếu wave
`REPAIR_FRAGMENT_COMPLETENESS` (**không** bump): ở đó thứ đổi là **ngữ cảnh lượt
SỬA**, mà lượt sửa chỉ xảy ra khi tổng hợp đã thất bại — và envelope thất bại
**chưa bao giờ vào cache**. Ở đây thứ đổi là hợp đồng của **lượt tổng hợp đầu
tiên**, tức đúng thứ sinh ra envelope được cache.

## 7. Bằng chứng — `test_card_category_affordance.py` (61 ca)

| | |
|---|---|
| C1 · C1b | mọi phép của miền có dòng riêng; mọi dòng CÂU LỆNH tự khai `[LỆNH]` |
| C2 | mọi dòng BIỂU THỨC tự khai `[BIỂU THỨC→…]` |
| C3 | cửa tiêu thụ nằm **ngay trên dòng**, cho từng biểu thức |
| C3b | `construct_point` **tự** hiện ra ở phép sinh điểm; `measure` chỉ `assign` |
| C4 · C5 | không phép nào ở hai nhóm (`CATEGORY_AUTHORITIES = 1`) |
| C6 | tiêm một cửa tiêu thụ mới ⇒ dòng thẻ **tự đổi** (không bảng chép tay) |
| C7 | biểu thức không có cửa ⇒ sinh thẻ **NÉM** |
| §16 | `cylinder_2` — một dòng trả lời được cả hai câu |
| §17 | mảnh sửa **giữ nguyên** nhãn loại; không lời riêng cho lượt sửa |
| §10 | tên toán hạng y nguyên (`from_point`/`to_point`, `a`/`b`, `anchor`…) |
| §11 | `PROBLEM_FAMILY_CARD_TEMPLATES = 0` |
| — | từ vựng y nguyên: 9 câu lệnh · 15 biểu thức |

`REPAIR_CARD_SEMANTICS_ALIGNED = YES` — mảnh sửa cắt ra từ thẻ nên nó mang luôn
nhãn. Bộ chọn mảnh phải đổi cách đọc dòng: `_ten_phep()` nay là chỗ **duy nhất**
biết bỏ qua nhãn để lấy tên phép, dùng chung cho bên sinh và bên chọn — hai bản
tự tách chuỗi sẽ lệch đúng vào ngày nhãn đổi hình dạng.

## 8. Đối chứng vẫn MỞ

```
OPERAND_NAME_CONVERGENCE          OPEN   (4 quy ước / 5 phép — §10 cấm đụng)
BALL_CENTER_RADIUS_EXPRESSIVENESS OPEN   (§19 — không thẻ nào sinh được điểm
                                          từ tâm + một số)
DOMAIN_ROOT_TIGHTENING            OPEN_P2 (§20 — `push` vẫn đi tới `served`)
CIRCUMSPHERE_OPERAND_GAP          OPEN   (§18)
```

⚠️ Wave này **không** tuyên bố `circumsphere` đã sửa: lỗi của nó là **tên toán
hạng**, không phải loại. Và nó đã có đủ ngữ cảnh sửa từ wave trước mà vẫn hỏng
ba lượt cùng một lỗi.

## 9. Hồi quy — 0 API call

| cổng | kết quả |
|---|---|
| pytest | **3277 pass**, 1 skip, 1 deselect |
| vitest | **687 pass / 50 file** |
| `tsc -b && vite build` | PASS |
| `replay_demo_cases.py` | **5/5** · `REDUCED_CHAIN 1/1` |
| `certify_acceptance_runner.py` | **RUNNER_CERTIFICATION PASS** |
| mảnh sửa (`test_repair_fragment_completeness`) | PASS sau khi đổi sang `_ten_phep` |
| `lock_cache_identity.py --verify` | PASS |
| `freeze_evaluation_candidate.py --verify` | PASS sau khi đóng băng lại |

## 10. Giới hạn

- Wave này chứng minh **cấu trúc hợp đồng**, không chứng minh mô hình sẽ dùng
  đúng. Chỉ một lượt sống mới trả lời được, và wave này cố ý không chạy lượt nào.
- Nhãn `[BIỂU THỨC→assign|construct_point]` dài hơn `[LỆNH]`; +552 byte là cái
  giá. Nếu một wave sau muốn rút, phải rút **ký hiệu**, không rút thông tin.
- `SKILL_PROMPT_CHANGED = NO`, nhưng prompt **chưa được soi** xem có chỗ nào
  nay thừa vì thẻ đã nói tốt hơn. Ghi lại, không sửa (§12).

## 11. Việc kế tiếp

```
NEXT_ACTION = OPERAND_NAME_CONVERGENCE_AUDIT
```

Bốn quy ước trên năm phép cùng nhận hai `point3` là chỗ trượt còn lại đã đo
được, và `circumsphere` hỏng ở đúng đó ba lượt liên tiếp. Audit trước, **không**
đổi tên ngay: đổi tên phá tương thích lược đồ, chương trình đã cache, artifact
lịch sử và ca thử — ba lối (alias · đổi tên chính tắc · chỉ dẫn chữ ký sinh
kèm) phải được cân trước khi chọn.

⚠️ **KHÔNG chạy V3.** Pool giữ niêm phong, seed chưa rút.
`CURVED_SYNTHESIS_ERGONOMICS = NO_MEASURABLE_GAIN` không đổi — wave này sửa
hợp đồng, không nói gì về kết quả tổng hợp.
