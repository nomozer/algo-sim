# M17-Lite Wave 2A — Live Smoke + Gate Re-verification Report

> Hai lần chạy live, cùng runner `scripts/live_smoke_m17_wave2a.py`, cùng 6
> prompt user duyệt, `gemini-2.5-flash`, production `run_pipeline`.
> **Run 1** (trước gate): 5/6 · 18/20 HTTP. **Run 2** (sau deterministic
> structure gate): 4/6 · 16/20 HTTP · 0 retry · 0 transient · 0 reclassify.
> Không sửa frozen M16/Wave 1, không chỉnh expectation.

## Run 2 — kết quả theo case

| # | Case | Route | Gate | Kết quả |
|---|---|---|---|---|
| 1 | preorder (VI) | `tree.traversal` | **PASS** | ✅ ok, variant=preorder, sim tạo |
| 2 | inorder (cây khuyết) | *(classify → generic)* | NOT_RUN | ❌ **unsupported — CHẶN OAN** |
| 3 | postorder (EN) | `tree.traversal` | **PASS** | ✅ ok, variant=postorder |
| 4 | level_order (VI) | `tree.traversal` | **PASS** | ✅ ok, variant=level_order |
| 5 | cross-family graph DFS | `network.graph_traversal` | NOT_RUN | ✅ ok, variant=dfs, gate không can thiệp |
| 6 | insufficient | *(classify → unsupported)* | NOT_RUN | ⚠️ unsupported ĐÚNG **nhưng không phải nhờ gate** |

## Phát hiện 1 — Structure gate KHÔNG chặn oan (thiết kế an toàn ✔)

3/3 case cây có cấu trúc thật mà **tới được gate** đều **PASS** (evidence:
rel=5/4/7, obj=5/4/7). Gate không can thiệp nhánh graph (NOT_RUN). Vậy **giả
định "gate quá chặt" là SAI** — gate an toàn.

## Phát hiện 2 — Gate CHƯA bao giờ bắn, và bằng chứng cho thấy nó SẼ KHÔNG chặn được

Case 6 (`"Mô phỏng duyệt cây preorder."`) bị từ chối bởi **computation gate
M13** (`result_ownership=algorithmic`), **không phải** structure gate
(NOT_RUN — classify trả unsupported nên chưa tới route tree).

**Nghiêm trọng:** analyze cho case 6 trả:
- objects: `['cây', 'nút (đỉnh) của cây', 'cạnh (liên kết) của cây']`
- relations: `['quan hệ cha-con giữa các nút trong cây']`
- evidence đếm được: **rel=1, obj=2 → `tree_structure_present` = True**

Nghĩa là **nếu classify có route sang `tree.traversal`, gate sẽ PASS** và LLM
lại bịa cây như run 1. Gate đếm **mô tả TRỪU TƯỢNG** ("nút của cây", "quan hệ
cha-con giữa các nút") như thể là **cấu trúc CỤ THỂ**. Đây đúng là lỗ hổng
analyze-integrity đã dự báo — **deterministic guard hiện tại KHÔNG giải quyết
được bài toán bịa cây**.

Đối chiếu case 2 (cây thật): objects `['cây','nút A','nút B','nút C','nút D']`,
relations `['A là gốc của cây','B là con trái của A','C là con phải của A','D
là con trái của B']` — có **ĐỊNH DANH nút cụ thể (A/B/C/D)**. Đây là khác biệt
phân biệt được: cụ-thể-có-định-danh vs trừu-tượng-không-định-danh.

## Phát hiện 3 — classify KHÔNG ổn định (nguyên nhân chặn oan case 2)

Case 2 **run 1: `tree.traversal` ok** → **run 2: `generic.rule_scene`** rồi bị
computation gate chặn (`arbitrary_algorithm`) → unsupported. **Cùng prompt,
cùng classify.md, khác kết quả** (temperature 0.2). Đây là **classify
instability**, KHÔNG phải lỗi gate (gate NOT_RUN).

Điểm tích cực: khi classify đi lạc sang generic, **computation gate M13 vẫn
chặn đúng** → không có generic leak, không false-positive simulation. Phòng
thủ nhiều tầng hoạt động.

## Đối chiếu acceptance

| Tiêu chí | Kết quả |
|---|---|
| A. 4/4 tree supported route+variant, không chặn oan | ❌ **3/4** (case 2 chặn oan tại classify) |
| B. Cross-family graph DFS không ảnh hưởng | ✅ đạt |
| C. Insufficient bị **structure gate** chặn đúng mã | ❌ gate NOT_RUN; từ chối bởi computation gate |
| generic leak = 0 | ✅ 0 |
| false-positive simulation = 0 | ✅ 0 (cả 2 run 2) |
| executor không chạy khi insufficient | ✅ đạt |
| learner message thân thiện | ✅ đạt |

**Wave 2A KHÔNG CLOSE.** Hai vấn đề còn mở: (1) structure gate đếm mô tả trừu
tượng là cấu trúc → không chặn được bịa cây; (2) classify không ổn định cho
prompt cây.

## Budget accounting (run 2)

Tổng **16/20 HTTP** · per-case: 3/2/3/3/3/2 · retry **0** · reclassify **0** ·
transient **0**. Còn lại 4 HTTP trong budget đã duyệt.

## Backlog analyze-integrity (user yêu cầu ghi)

> Structure gate hiện deterministic trên analyze output nhưng **chưa chứng minh
> provenance** của từng object/relation. Analyze hallucination (mô tả trừu
> tượng khái niệm cây) tạo **false evidence** — đã QUAN SÁT ĐƯỢC ở case 6 run 2
> (rel=1/obj=2 từ mô tả chung, không có định danh nút nào). Cần **grounded
> evidence / source-span validation** cho required user input: chỉ tính là cấu
> trúc khi object/relation mang **định danh nút có nguồn gốc từ đề**.
