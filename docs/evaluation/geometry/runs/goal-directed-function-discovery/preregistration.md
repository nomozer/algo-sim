# Preregistration — goal-directed function discovery (unnamed derived operands)

Written and committed **before** any product change. Branch `research/goal-directed-function-discovery`, rẽ từ
`8c24cb52` (= `main` `2a3c0787` + result-binding `f83b4ed1` + Scene3D W1–W3; cả hai chưa được tích hợp/duyệt).
`DEFAULT_MODE = LLM_ONLY`, Hybrid tắt trên sản phẩm, 0 lượt gọi Gemini, `CACHE_VERSION` không đổi.

## 1. Research question and hypothesis

RQ (từ brief): trong một thư viện hàm hình học xác định, Planner tìm kiếm có điều kiện trên hợp đồng hiệu ứng có tự
tổng hợp được chuỗi dựng mới từ dữ kiện đã kiểm chứng, mở rộng năng lực mô phỏng mà không viết quy tắc phối hợp riêng
cho từng dạng đề không?

**H1 (capability).** Sau thay đổi, Planner phục vụ đúng khoảng cách từ một **điểm dẫn xuất không tên** (vd *"trung điểm
của SC"*) tới mặt phẳng có tên, đường thẳng có tên và giao tuyến đã có nguồn — 9/9 ca dương của `corpus.json`, đúng
từng giá trị bình phương của oracle độc lập, 0 phục vụ sai.

**H2 (discovery, phân biệt search với fixed rule).** Thêm **một** `PlanningContract` cho hàm `centroid` đã có trong một
Registry thử nghiệm (không sửa `planner.py`, cổng nguồn hay engine) làm 3/3 ca `discovery` (trọng tâm → mặt / đường /
giao tuyến) chuyển từ `UNSUPPORTED_CAPABILITY` sang phục vụ đúng. Fixed-rule Planner cần ít nhất một nhánh mới cho mỗi
cặp (mô tả điểm × loại đích).

**H3 (no regression).** Trên benchmark 30 ca (đông cứng), corpus result-binding 18 ca và corpus hai-đường 45 + 32 ca,
Planner mới cho `(status, code, answers)` **trùng từng ca** với Bounded Effect Planner hiện tại.

H1–H3 là giả thuyết; không phải tuyên bố novelty.

## 2. What changes (planned), what does not

Planned (tối thiểu, mở rộng mã có sẵn — không Planner/FactGraph/DSL mới):

1. `planner._EffectResolver`: chuyển nhu cầu theo **vị trí toán hạng** của hiệu ứng (thay vì gộp env theo tên slot);
   nhu cầu `Point` có thể là **mô tả** (`("desc", kind, operands)`) được giải bằng producer có hiệu ứng `Point` cùng
   `descriptor`; lọc kiểu toán hạng (Point/Line/Plane) **trước** khi đếm candidate; phát lời gọi bằng **khuôn đối số
   khai trong contract** (`call`, `fresh`), không bằng `switch` theo `source_policy`; tái dùng lời gọi sẵn có cùng hiệu ứng.
2. Goal entry: câu hỏi `distance` có `point_kind` + `points` (không `points_a`) ⇒ nhu cầu `AnswerDistance(desc, đích)`
   với đích = mặt (`points_b` ≥ 3), đường (`points_b` = 2) hay `line_ref`.
3. `registry`: contract cho `midpoint` (Point, descriptor `midpoint`, cụm nguồn) và `ask_distance_point_plane`
   (AnswerDistance tới Plane); khuôn đối số cho ba contract cũ. Chứng chỉ mới `effect-chain` được kiểm **tổng quát**:
   mỗi lời gọi tái dựng đúng từ khuôn + env, mỗi đầu vào không phải lá phải có một phần tử chuỗi sinh ra đúng hiệu ứng
   ấy, nhãn tươi không trùng đề, cụm nguồn *"khoảng cách từ ‹mô tả› đến ‹đích›"* đúng toán hạng, được hỏi, không điều
   kiện/chứng minh/phủ định/gán giá trị.
4. `engine`: kiểm độc lập ngữ nghĩa mô tả (vị từ theo `descriptor`, không theo hàm đã chọn) và đối chiếu đáp số với
   khoảng cách tính trực tiếp từ đích (Gram), sau khi kernel thực thi.
5. `function_route`: gắn vai/binding `AUXILIARY` cho nhãn tươi của chuỗi.

Not changed: lược đồ `TypedFact` (byte), prompt và khai báo hàm của provider (vân tay A `7ea511a6…`, B `485d3834…`,
khai báo `5ceb0f99…`, lược đồ dữ kiện `282f5f76…` phải giữ nguyên), Kernel, IR, frontend, `CACHE_VERSION`,
`DEFAULT_MODE`. Ngoài phạm vi: chân vuông góc lên mặt phẳng như bước dựng, giao điểm không tên của hai đường, góc,
nhiều khối, CEGIS/chứng minh, bật Hybrid, gọi Gemini.

## 3. Corpora (status declared, never renamed later)

| corpus | file | n | status |
|---|---|---:|---|
| development (new slice) | `corpus.json` (`positive` 9, `negative` 16) | 25 | DEVELOPMENT, NOT_HELD_OUT |
| discovery (experimental Registry) | `corpus.json` (`discovery` 3) | 3 | DEVELOPMENT, NOT_HELD_OUT |
| regression A | `backend/tests/geometry/hybrid_compiler_benchmark.py` (đông cứng, B27 vẫn khai `unsupported`) | 30 | historical, frozen labels |
| regression B | `runs/goal-directed-planner-generalization-audit/next-slice-corpus.json` | 18 | NOT_HELD_OUT |
| regression C | `runs/two-line-plane-section/inputs/{math-corpus,heldout}.json` | 45 + 32 | dev + historical held-out |

`corpus.json` sinh bởi `oracle.py` (không nhập `app`; Fraction + Gram, cách tính khác engine: covector affine, định thức
Gram, cực tiểu bậc hai). Không có tập held-out cho lát này: mọi ca do cùng tác giả thiết kế cùng lúc với lát.

Transport: câu hỏi `kind=question, quantity=distance, point_kind ∈ {midpoint, centroid}, points = toán hạng của mô tả`,
không `points_a`, không `point`; đích = `points_b` hoặc `line_ref`. Đây là tổ hợp trường **đã có** trong lược đồ, hôm nay
bị Planner từ chối; lược đồ và prompt không đổi ⇒ trích xuất live của dạng này `NOT_MEASURED`.

## 4. Arms (same Typed Facts input bundle)

| arm | code | Planner |
|---|---|---|
| FIXED | `main` `2a3c0787` (detached worktree) | `geometry-fact-planner/4`: luật ánh xạ + công thức cố định độ sâu 1 (`_phan_ra`, `_mat_qua_diem`) |
| BOUNDED | `8c24cb52` (detached worktree; backend trùng `f83b4ed1`) | `/5`: `_EffectResolver` có trần trên 3 contract |
| NEW | product commit của run này | `/6`: như mục 2 |

Registry khác nhau giữa các arm (FIXED không có contract). Ảnh hưởng của Registry được tách riêng bằng thí nghiệm
**ablation trên arm NEW** (cùng mã Planner): (a) Registry sản phẩm; (b) bỏ contract `midpoint`; (c) bỏ contract
`ask_distance_point_plane`; (d) + contract `centroid` (thử nghiệm); (e) Registry đảo thứ tự; (f) contract nói dối
(mô tả `centroid` gắn vào hàm `midpoint`).

## 5. Metrics

Theo arm × corpus: correct served · wrong served · correct refusal (mã thuộc `expected_codes`) · false refusal ·
wrong-code refusal. Cho ca phục vụ: bình phương đáp số = oracle (chính xác). Planner: số lời gọi, số nhãn tươi, số
needs / candidates của resolver, độ sâu phân giải lớn nhất, thời gian `lap_ke_hoach` và `run_fact_route`, đỉnh bộ nhớ
(`tracemalloc`) của `lap_ke_hoach`. Tái dùng: số hàm Registry khác nhau dùng trong kế hoạch, số hàm hình học **mới**
(kỳ vọng 0). Số quy tắc phối hợp theo dạng bài phải thêm (đếm nhánh goal-specific trong diff `planner.py`).
Scene3D: thứ tự bước (khối → điểm dẫn xuất → [chân/giao tuyến] → đáp số), nhân chứng vuông góc chính xác, chọn/tua
trong trình duyệt, 0 lỗi console.

## 6. Success criteria (all must hold)

- S1: NEW 9/9 dương đúng oracle; 0 wrong served trên mọi corpus và mọi arm của NEW.
- S2: NEW 16/16 âm từ chối với mã thuộc `expected_codes`.
- S3 (RED baseline): FIXED và BOUNDED phục vụ 0/9 dương (ghi mã thực tế; không sửa nhãn sau khi thấy).
- S4: NEW ≡ BOUNDED từng ca trên regression A, B, C.
- S5: ablation (d) phục vụ 3/3 discovery đúng oracle với 0 dòng thay đổi ở `planner.py`/cổng/engine giữa (a) và (d);
  (a) từ chối 3/3 `UNSUPPORTED_CAPABILITY`; (b) từ chối ca mô tả trung điểm; (e) kế hoạch trùng (a); (f) bị engine từ chối.
- S6: metamorphic (đổi tên, đổi thứ tự dữ kiện, toán hạng `CS`/`SC`, co giãn kích thước ×2 ⇒ bình phương ×4, va chạm
  nhãn tươi ⇒ nhãn kế tiếp) giữ đáp số; mỗi trần ngân sách hạ xuống ⇒ `PLAN_TOO_LARGE`, không phục vụ một phần.

## 7. Budgets and stop rules

Trần tìm kiếm giữ nguyên giá trị hiện có (`MAX_EFFECT_DEPTH 3`, `MAX_EFFECT_NEEDS 32`, `MAX_EFFECT_CANDIDATES 8`,
`MAX_RESULT_LINES 4`, `MAX_RESULT_FEET 8` — nay đếm mọi điểm tươi, `MAX_CALLS 64`); báo cáo giá trị lớn nhất quan sát
được so với trần. Dừng: (i) S4 hỏng ⇒ sửa nguyên nhân hoặc hủy lát, không nới nhãn; (ii) tối đa hai vòng sửa trên corpus
phát triển sau GREEN đầu tiên — không vòng lặp tăng điểm; (iii) không sửa `corpus.json`/`oracle.py` sau commit này —
sai lệch ghi thành `deviation` trong báo cáo; (iv) 0 lượt gọi model.
