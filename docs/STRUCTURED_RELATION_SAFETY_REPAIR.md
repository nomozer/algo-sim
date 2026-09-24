# STRUCTURED_RELATION_SAFETY_REPAIR

**2026-09-21** · nhánh `feat/photo-problem-to-scene` · START_HEAD `35d84da` ·
commit sản phẩm `8dd5f8b` · `main` giữ `085cae6` · **0 request Gemini · 0 request mạng**

```text
STRUCTURED_RELATION_SAFETY_REPAIR = PASS
REJECTION_CODE = STRUCTURED_RELATION_CONTRADICTION     (trạng thái adapter INVALID_CONFLICT)
RULE_ID        = MULTIPLE_RIGHT_ANGLE_VERTICES_IN_TRIANGLE
N04            UNSAFE (đáp số 70/3, cảnh served) → SAFE_REJECTION trước compiler
CANDIDATE      e7bae036… → 077dbc6b…                  CACHE_VERSION 99 → 99
DEFAULT_MODE   LLM_ONLY — compiler vẫn chưa nằm trên đường mặc định
```

## 1. Lỗi, và vì sao nó lọt

Hợp đồng đọc **đúng** đề N04 — đáy GHL vuông tại G *và* vuông tại H (hai dữ kiện
đề nói, loại trừ nhau), cộng `DG ⊥ (GHL)` — đi hết đường dựng:

1. `fact_graph.kiem_mau_thuan` chỉ có hai lớp: xung đột độ dài, và **cùng**
   `(kind, args)` vừa khẳng định vừa phủ định. `GH⟂GL` mang args `(G,H,G,L)`,
   `HG⟂HL` mang `(G,H,H,L)` — khác args, không lớp nào đem chúng ra so.
2. `compiler.danh_gia_eligibility` lấy chân đường cao G, duyệt các góc vuông đề
   cho, gặp `GH⟂GL` (đỉnh G) thì `break`. `HG⟂HL` (đỉnh H) chỉ bị `continue` kèm
   chú thích *"góc vuông ở một đỉnh khác — không phải đáy của khối này"* — dù nó
   là **cùng** tam giác đáy.
3. Compiler dựng chương trình, cảnh, final_memory và trả **70/3**.

Adapter không bao giờ dựng nút `triangle` (bảng loại nút có, nhưng không đường
nào tạo), nên "tam giác" chỉ tồn tại ngầm qua quan hệ.

Audit còn lộ **lỗ thứ hai**: định tuyến so `bd.reason_code == "INVALID_CONFLICT"`,
nên một mã mâu thuẫn **mới** từ compiler sẽ rơi xuống nhánh **lùi về LLM** — đúng
việc mời mô hình chọn một nửa mâu thuẫn.

## 2. Luật

Với ba điểm **phân biệt** A, B, C: `AB⟂AC` (vuông tại A) và `BA⟂BC` (vuông tại B)
không thể cùng đúng. Tổng hai góc của tam giác ABC đã bằng 180°; còn nếu A, B, C
thẳng hàng thì không đường nào trong số đó vuông góc được. Hai quan hệ ấy nhắc
**đủ** ba cạnh AB, AC, BC, nên chính chúng xác định tam giác — không cần nút
`triangle`.

Nhận diện một góc vuông: `perpendicular_lines` có hai đường, mỗi đường hai điểm
phân biệt, chung **đúng một** điểm. Đọc bằng **tập** điểm, không bằng vị trí
trong `args`. Chỉ tính fact `GIVEN`, hoặc `DERIVED` có nêu cha.

**Một thẩm quyền:**

- luật nằm trong `fact_graph.kiem_mau_thuan` (hàm `_kiem_nhieu_dinh_vuong`), chạy
  trong `dung_graph` — đường **duy nhất** dựng graph, và là cổng sớm nhất đủ
  thông tin;
- `compiler.danh_gia_eligibility` gọi **chính** `kiem_mau_thuan` để fail closed
  khi nhận một graph mâu thuẫn dựng trực tiếp (không chép luật);
- định tuyến đọc tập mã mâu thuẫn từ `fact_graph.MA_MAU_THUAN`.

Chẩn đoán là từ vựng đóng — số đỉnh vuông, pha, mã luật — **không** nhãn điểm,
không câu chữ đề. Bằng chứng thêm có băm tam giác và con trỏ `source_fact_id`.

## 3. Kết quả

**N04, cùng fixture dựng từ registry đã đăng ký, trước/sau:**

| | trước (`35d84da`) | sau (`8dd5f8b`) |
|---|---|---|
| FactGraph | `VALID` | **`INVALID_CONFLICT` · `STRUCTURED_RELATION_CONTRADICTION`** |
| rule / số đỉnh vuông | — | `MULTIPLE_RIGHT_ANGLE_VERTICES_IN_TRIANGLE` · 2 |
| compiler | `SUPPORTED`, chọn đỉnh G, bỏ `HG⟂HL` | **không được gọi** |
| chương trình / cảnh / final_memory / đáp số | có / có / có / 70/3 | **không / không / không / không** |
| định tuyến (compiler bật) | `USE_COMPILER` | **`REFUSE`** |
| runner | `UNSAFE_ACCEPTANCE` | **`SAFE_REJECTION`** |

**Ma trận tổng quát** — 29 test của wave, 15 đỏ trên sản phẩm chưa sửa, 29/29 xanh sau:

- **A · mâu thuẫn (8, đều đỏ trước):** GHL · ABC · PQR · đảo đầu mút mọi cạnh ·
  đảo thứ tự quan hệ (cùng bằng chứng) · một nguồn "vuông tại B" lẫn nguồn ký hiệu ·
  một GIVEN + một DERIVED có cha · cả ba đỉnh vuông (đếm đủ 3).
- **B · hợp lệ, không bị bác nhầm (9):** chỉ vuông tại A · khai lặp + đảo cạnh ·
  hai tam giác khác nhau mỗi cái một góc vuông · đường chéo nhau · hệ quả
  line⟂plane · GIVEN + DERIVED cùng một góc · R01/S.ABC · đổi nhãn · độ dài phân số.
- **C · thiếu bằng chứng, theo chính sách hiện hành (4):** góc thứ hai là giả định
  · không nguồn · điểm lạ · không có đỉnh chung.
- **Tích hợp:** adapter thật · định tuyến thật (compiler **không** được gọi) ·
  đường runner (không chương trình, cảnh, memory, đáp số) · compiler gọi trực
  tiếp với graph mâu thuẫn ⇒ fail closed · định tuyến **từ chối** chứ không lùi
  về LLM khi compiler báo mâu thuẫn.

**Parity ca hợp lệ — trùng byte** giữa `35d84da` và `8dd5f8b` cho P01, P02, P04,
R01/S.ABC, đổi nhãn, phân số, một bộ độ dài line⟂plane khác. Trùng trên mọi
trường so: graph canonical · eligibility + binding · chương trình · các bước dựng
· final_memory · đáp số · envelope/cảnh · route · cổng trực quan — và cả 6 thân
request Analyze.

**Tiêm lỗi — 9/9 bị bắt**, hoàn nguyên trùng byte, không dấu tiêm. Chín phép:
bỏ luật · chỉ kiểm G,H,L · đọc đỉnh theo vị trí args · coi góc lặp là mâu thuẫn ·
bỏ góc vuông thứ hai · bỏ chốt fail-closed của compiler · cho giả định thành
GIVEN · đổi rule id · định tuyến so một chuỗi. Ba phép chỉ bị ít test bắt:

- coi góc lặp là mâu thuẫn — 1 test;
- định tuyến so một chuỗi — 1 test;
- bỏ chốt fail-closed — 2 test.

**Full backend:** 5744 passed ở START; 5771 passed · **0 failed** ở trạng thái
END (worktree sạch).

## 4. Hai test cũ đã đổi — có lý do

- **`test_W2`** dùng `SA ⟂ (ABS)`: đường **nằm trong** mặt nó được khai vuông
  góc, tức một quan hệ suy biến. Hệ quả suy ra (`SA⟂AB`, `SA⟂SB`) làm tam giác
  SAB vuông ở hai đỉnh, nên FactGraph nay bác sớm hơn. Ý định của test (mặt
  **khác** đáy bị eligibility từ chối) được giữ bằng mặt không suy biến
  `SA ⟂ (ABD)`: ở START test vẫn xanh, hành vi eligibility không đổi. Fixture suy
  biến cũ chuyển sang `test_W2b` và được ghim là bị bác có tên.
- **`test_G8_E_N04`** (wave trước) ghim hành vi lỗi và tự dặn *"phải đổi khi sản
  phẩm được sửa"*. Nay nó kỳ vọng từ chối an toàn.

## 5. Cache và candidate

**`CACHE_VERSION` giữ 99**, có bằng chứng:

- `geometry_compiler` không được `backend/app` tham chiếu ngoài chính gói nó;
- đường mặc định là `LLM_ONLY`, và envelope được cache trên đường ấy không import
  compiler;
- khoá `cache_identity.lock.json` trùng byte với START.

Không envelope `ok` nào trên đường mặc định có thể đổi, nên bump chỉ vô hiệu hoá
cache mà không sửa được gì.

**Candidate** `e7bae036… → 077dbc6b…` (103 tệp), đóng băng trong worktree sạch
tại `8dd5f8b`, `--verify` PASS. `CANDIDATE_DIVERGENCE.json` cập nhật: `e7bae036…`
vào lịch sử, wave được nối vào chuỗi. ⚠️ Đặc tả xếp candidate vào commit 1, nhưng
nó nằm ở **commit 2**. Lý do: bộ đóng băng ghi `commit = HEAD`; amend nó vào
commit 1 sẽ làm trường ấy trỏ tới một commit mồ côi. Quy ước của kho là đóng băng
sau commit sản phẩm. Hệ quả: riêng commit 1 có một test candidate đỏ, như mọi
wave trước.

## 6. Vai trò dataset của N04

`N04_ROLE_BEFORE_DISCOVERY = DEVELOPMENT_HOLDOUT_PILOT` →
`N04_ROLE_AFTER_SAFETY_REPAIR = DEVELOPMENT_REGRESSION_CASE`. N04 đã được dùng để
phát hiện lỗi và thiết kế bản sửa, nên kết quả sau sửa chỉ chứng minh **hồi quy**.
Case ID, ground truth và mọi artifact lịch sử **không đổi**. Muốn quyết định
canary vẫn cần một ca âm **mới**.

⚠️ **Hệ quả cho chỉ số phụ ở lượt retry.** Registry targeted của wave trước (bất
biến) ghim N04 `allowed_exact_codes = ["INVALID_CONFLICT"]` — mã mâu thuẫn duy
nhất tồn tại lúc đăng ký. Sản phẩm nay trả `REJECTION_CODE =
STRUCTURED_RELATION_CONTRADICTION`, còn trạng thái adapter vẫn là
`INVALID_CONFLICT`. Nên ở lượt retry, N04 đọc đúng sẽ ra `SAFE_REJECTION = YES`
nhưng `TARGETED_REJECTION_MATCH = NO`. Phân loại benchmark không dùng TARGETED,
nên kết luận không đổi. Tôi **không** sửa registry, và không đổi cách bộ đo đọc
nó sau khi đã thấy mã mới. Nếu muốn TARGETED có nghĩa cho N04, cần đăng ký một
registry v2 **trước** lượt retry.

**P03/P05 không đổi**: ngưỡng cụm lỗi lặp giữ ≥ 2 ca cùng mã quy kết. P03 và P05
vẫn là cụm `MODEL_MALFORMED_RELATION`, nên trần của lượt retry vẫn là `NOT_READY`
(xem `COMPLETION_RUNNER_REPAIR_OFFLINE.md §1`). Bản sửa này chỉ gỡ khả năng ra
`UNSAFE` do N04.

## 7. Artifact

`docs/evaluation/geometry/photo-problem-to-scene/structured-relation-safety-repair/`:
`PRECHECK` · `SAFETY_GAP_AUDIT` · `CONTRADICTION_RULE_CONTRACT` · `N04_BEFORE_AFTER` ·
`GENERIC_CONTRADICTION_MATRIX` · `VALID_CASE_BEHAVIOR_PARITY` · `DATASET_ROLE_DECISION` ·
`CACHE_AND_CANDIDATE_DECISION` · `RED_BEFORE_GREEN_AFTER` · `FAULT_INJECTIONS` ·
`OFFLINE_GATES` · `SECRET_SCAN`.
