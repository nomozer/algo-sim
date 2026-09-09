# PRODUCT_UI_RESULT_RENDERING_AND_DEMO_ACCEPTANCE

**Ngày:** 2026-09-09 · **0 lượt gọi model, 0 lượt gọi provider**

Wave này trả lời câu mà JSON không tự trả lời được: **chín envelope của lượt đo
cuối có thành mô phỏng trên màn hình học sinh không.**

```
UI_RESULT_RENDERING            PASS   (66/66 phép kiểm trong Chrome thật)
PRODUCT_RESPONSE_ADAPTER       PASS   (9/9 rẽ đúng nhánh tại biên nhận)
POSITIVE_CASES_RENDERED        7/7
NEGATIVE_CASES_PRESENTED       2/2
EXACT_DISPLAY_PASS             12/12  đại lượng, đọc TRÊN MÀN HÌNH
SCENE3D_OBJECT_PASS            7/7
TRACE_PLAYBACK_PASS            7/7
STATE_ISOLATION_PASS           9/9
USER_ERROR_PRESENTATION_PASS   2/2
UNCAUGHT_FRONTEND_EXCEPTIONS   0
SCREENSHOTS_CAPTURED           9

APPLICATION_LLM_CALLS          0
REAL_PROVIDER_CALLS            0
PRODUCT_UI_CODE_CHANGED        YES   — một bản vá, xem §4
BACKEND_CODE_CHANGED           NO    (0 byte dưới `backend/app`)
API_CONTRACT_CHANGED           NO
LIVE_ARTIFACTS_CHANGED         NO    (26 file lượt đo nguyên byte)
CACHE_VERSION_BEFORE/AFTER     94 / 94
CANDIDATE_HASH_BEFORE/AFTER    d72db7c3… / d72db7c3…   (không đóng băng lại)

FRONTEND_TEST_RESULT           788 pass / 53 file, 0 đỏ
BROWSER_E2E_RESULT             9/9 ca · 66/66 phép kiểm · 6/6 phép tiêm ĐỎ ĐÚNG CHỖ
BUILD_RESULT                   `tsc -b && vite build` PASS
ARTIFACT_HASH_RESULT           PASS (26 file · 19 raw nguyên byte)
FREEZE_RESULT                  exit 0 — 92 file, `d72db7c3…`
```

---

## 1. Đường chạy đã chứng minh

```
envelope đóng băng của lượt đo cuối
  → /api/analyze (bị chặn ở biên mạng, trả fixture)
  → analyzeViaServer → res.json()
  → rẽ theo `status`: loadEnvelope | loadUnsupported
  → store.active / store.unsupported
  → SimulationWorkspace → hopLeScene3D → Scene3DExplorer
  → canvas WebGL · thanh tua · dải số đo
  → đáp số trên màn hình
```

**Vì sao chặn ở biên mạng chứ không nạp thẳng vào store.** `loadEnvelope` là
đúng cửa Thư viện đi qua, và các lượt spot-check trước đều dùng nó — nhưng nó
**bỏ qua** đoạn `onAnalyze → analyzeViaServer → rẽ theo status`. Đúng đoạn ấy là
"response adapter", và đúng đoạn ấy quyết định một envelope thật có dựng được
không. Nên ở đây: gõ đề vào ô nhập thật, bấm nút thật, `/api/analyze` trả fixture
đã đóng băng. Không một lượt gọi model nào.

### 1.1. Fixture dẫn xuất, và phép đối chứng làm nên giá trị của nó

Artifact lượt đo giữ `chuong_trinh` (đầu ra mô hình) và `cham` (điểm) — **không**
giữ envelope. Envelope là thứ tầng tất định dựng ra *sau* mô hình, nên dựng lại
được với 0 lượt gọi, bằng **đúng đường sản phẩm**: `verify_and_compile` →
`pipeline._dung_scene3d` → `_envelope_tu_route_sinh` / `_that_bai_hinh_hoc` →
`attach_learner_reason`.

Một bản dựng lại chỉ đáng tin khi nó **khớp với điểm đã chấm**. Mỗi ca được so
lại với `cham` đóng băng ở `SERVABLE`, tập kiểu ngữ nghĩa, và từng
`expected_display`; lệch một chỗ là **ném**, không phải cảnh báo.

⚠️ Hai cái bẫy đã mắc khi viết bộ trích, ghi lại vì cả hai đều im lặng:

- **Hai bảng tên cho hai tầng.** `cham["scene3d_kinds"]` là kiểu **ngữ nghĩa**
  (`point3`, `solid`, `ellipse3`), còn `render` là **loại vẽ** (`point_marker`,
  `mesh`, `readout`). So nhầm bảng thì **mọi** ca đều "lệch".
- **Không được so với `actual_display`.** Đó chính là trường mà lỗi bộ chấm của
  wave trước làm rỗng ở 6/7 ca. So với một trường đã biết là hỏng thì phép đối
  chứng sẽ **đỏ trên một hệ hoàn toàn đúng**.

---

## 2. Bảng ánh xạ JSON → nơi tiêu thụ

| trường trong phản hồi | ai đọc | trình bày thành |
|---|---|---|
| `status` | `ProblemInput.onAnalyze` | rẽ nhánh `loadEnvelope` / `loadUnsupported` |
| `simulation_id` | `store.loadEnvelope` → `registry.getSimulation` | phân giải module (`generic.semantic_program`) |
| `config` | `mod.validateConfig` → `mod.init` | trạng thái engine; hỏng ⇒ `analysisError`, KHÔNG dựng cảnh |
| `scene3d` | `SimulationWorkspace` → `hopLeScene3D` | rẽ sang `Scene3DExplorer`; hình dạng lạ ⇒ rơi về đường 2D |
| `scene3d.objects[].render` | `scene3d-view` | loại hình vẽ trên canvas |
| `scene3d.objects[].label` · `notation` | `scene3d-view`, cây thành phần | tên đọc được · ký hiệu in cạnh vật |
| `scene3d.objects[].exact` · `value` | `hienSo` → `.geo3d-readout-gt` | **đáp số**, giữ nguyên căn và π |
| `scene3d.events` | `objectsAt`, `scene3d-playback` | thanh tua; vật hiện đúng bước dựng nó |
| `scene3d.free_objects` | `objectsAt` | vật có mặt từ bước `INIT` |
| `description` · `title` | `Scene3DExplorer` | nội dung sau nút «Xem đề» |
| `failure_category` | `UnsupportedNotice` | nhãn thẻ từ chối |
| `learner_reason` | `UnsupportedNotice` | câu giải thích cho học sinh |
| `error_code` | `UnsupportedNotice` (**mới**, xem §4) | chọn câu gợi ý; **không** in ra |
| `analysis` · `representation_plan` · `source` | — | không consumer nào; không lên bề mặt |

---

## 3. Kết quả từng ca

| ca | nhánh | canvas | bước tua | đáp số ĐỌC TRÊN MÀN HÌNH | console |
|---|---|---|---|---|---|
| `p1` | active | ✓ | 13 | `72` · `9` · `3√6` | 0 |
| `p2` *(đa diện lõm)* | active | ✓ | 4 | `96` | 0 |
| `p3` *(khối cầu)* | active | ✓ | 6 | `4500π` · `144π` | 0 |
| `p4` *(hình trụ)* | active | ✓ | 5 | `360π` · `120π` | 0 |
| `p5` *(hình nón)* | active | ✓ | 5 | `100π` · `65π` | 0 |
| `p6` *(elip xiên trụ)* | active | ✓ | 5 | `25π√5` | 0 |
| `p7` *(elip xiên nón)* | active | ✓ | 5 | `2π√6` | 0 |
| `n1` | unsupported | — | — | *(không có, đúng)* | 0 |
| `n2` | unsupported | — | — | *(không có, đúng)* | 0 |

Ba khẳng định đáng nói riêng:

- **Bước đầu KHÔNG lộ đáp số** ở cả 7 ca. Số đo chỉ hiện sau bước đo nó — đó là
  mục tiêu sư phạm ("một hình được hình thành như thế nào"), không phải thiếu
  sót. Test khoá cả hai chiều.
- **Đáp số đọc từ DOM sau khi tua bằng nút thật**, không đọc từ JSON. `25π√5` và
  `2π√6` lên màn hình đúng từng ký tự — dạng chính xác đi trọn đường tới mắt
  người học.
- **Ca âm dọn sạch cảnh của ca trước**: không canvas, không dải số đo, không mã
  lỗi kỹ thuật.

---

## 4. Nhánh B — một bản vá tầng trình bày

**Lỗi đo được từ ảnh `n1`/`n2`:** thẻ từ chối in câu *"Dạng bài này hệ có mô
phỏng — thử diễn đạt lại đề gọn hơn rồi gửi lại."* cho hai bài **ngoài bao đóng
biểu đạt**. Khối tròn xoay tổng quát và khối ghép/bù là `OUT_OF_SCOPE` **vì lý do
kiến trúc** (không tích phân ký hiệu, không thẩm quyền boolean) — hệ sẽ không bao
giờ mô phỏng chúng. Câu ấy là một lời hứa sai, và nó làm học sinh ngồi chờ một
thứ không tới.

`geometry_generation_failed` gộp hai tình huống ngược nhau:

| | tình huống | lời khuyên đúng |
|---|---|---|
| ① | bài **thuộc** bao đóng, mô hình viết chương trình hỏng | "thử diễn đạt lại đề" |
| ② | bài **ngoài** bao đóng | "hệ chưa có phép dựng cho yêu cầu này" |

Cổng phủ **đã** phân biệt sẵn bằng `requested_operation_uncovered`; chỗ thiếu là
bề mặt học sinh chưa đọc mã ấy. Đây đúng lớp lỗi kho đã sửa hai lần cho
`out_of_scope` vs `not_simulation_suitable`, và cách sửa cũng đúng lối cũ: đọc
`error_code` (chi tiết hơn) **trước** khi rơi về câu chung của `failure_category`.

**Nền đỏ trước bản vá** — ghi lại nguyên văn:

```
× bài NGOÀI bao đóng KHÔNG được hứa «dạng bài này hệ có mô phỏng»
  AssertionError: expected '<section class="card">…' not to contain
  'Dạng bài này hệ có mô phỏng'
```

**Bản vá:** một nhánh trong `UnsupportedNotice` (`components/SimulationWorkspace.tsx`),
đổi **duy nhất câu gợi ý**. `failure_category`, `error_code`, `learner_reason` và
hành vi fail-closed là ngữ nghĩa do backend sở hữu — không đụng một byte.

**Vì sao candidate KHÔNG đổi.** `MEASURED_SYSTEM_PATHS` gồm `backend/app`,
`frontend/src/simulations/domains/semantic` và bản chiếu schema của nó.
`components/` và `domains/geometry/` **không** nằm trong đó, nên
`freeze --verify` vẫn exit 0 với `d72db7c3…`. `CACHE_VERSION` giữ 94: bản vá
không chạm prompt, thẻ văn phạm, lược đồ hay policy định tuyến — **bề mặt mô hình
KHÔNG đổi**.

### 4.1. Phần CHƯA sửa được, và vì sao — bằng chứng cho Nhánh C

⚠️ **`n1` vẫn đọc câu cũ.** Nó bị chặn ở `stage_semantic_program`, nên
`_that_bai_hinh_hoc` nhận `outcome = None` và envelope mang
`error_code: null`, `stage_reached: null`. **Phản hồi không chở tín hiệu nào để
phân biệt**, nên tầng trình bày không có gì để đọc. Đây là khoảng trống hợp
đồng, không phải khoảng trống giao diện.

```
BLOCKER_SCOPE   = n1 (và mọi ca bị chặn TRƯỚC verify_and_compile)
TRƯỜNG THIẾU    = error_code / failure_category phân biệt "ngoài bao đóng"
CONSUMER CẦN NÓ = UnsupportedNotice (components/SimulationWorkspace.tsx)
NEXT_ACTION      = PRODUCT_RESPONSE_CONTRACT_ALIGNMENT
```

⚠️ **Thẻ từ chối của `n2` nay nói hai giọng.** Câu gợi ý đã đúng, nhưng thân
thông điệp (`learner_reason`, do `backend/app/learner_messages.py` sở hữu) vẫn
khuyên *"thử diễn đạt lại đề gọn hơn… rồi gửi lại nhé"*. Sửa nó là sửa
`backend/app` ⇒ đóng băng lại candidate, mà đặc tả wave này cấm
(*"Giữ API contract, backend, kernel, prompt và artifact cuối nguyên vẹn"*). Bản
vá hiện tại vẫn là cải thiện chặt: nó **gỡ một khẳng định SAI SỰ THẬT**, còn câu
còn lại chỉ là lời khuyên kém hữu ích. Phần backend đi cùng `NEXT_ACTION` trên.

---

## 5. Phép tiêm lỗi — 6/6 đỏ đúng chỗ

Một lượt soát "sạch" không chứng minh gì tới khi nó đỏ được, và phải đỏ ở **đúng
khẳng định nhắm tới** — đỏ vì lý do khác là guard vẫn chưa được chứng minh.

| phép tiêm | nhắm tới | đỏ ở |
|---|---|---|
| gỡ `scene3d` | canvas 3D dựng thật | canvas · đáp số · nhãn hình |
| đổi một đáp số `72 → 73` | đáp số trên màn hình | đáp số trên màn hình |
| cắt bớt `events` | số bước tua | số bước tua · đáp số |
| lật `status` sang `unsupported` | adapter rẽ đúng nhánh | adapter rẽ đúng nhánh |
| rò định danh vào nhãn số đo | không rò định danh kỹ thuật | không rò định danh |
| đổi lớp từ chối của ca âm | thẻ từ chối hiện ra | thẻ từ chối hiện ra |

⚠️ **Một phép tiêm ĐÃ HỎNG, giữ lại vì nó dạy được.** Bản đầu tiêm định danh vào
`description` và **không đỏ** — vì đề bài nằm sau nút «Xem đề» nên không có mặt
trong `innerText`. Guard soi thứ **người học thấy**, nên phép tiêm cũng phải đặt
vào chỗ người học thấy. Một phép tiêm đặt sai chỗ sẽ kết luận sai theo hướng
"guard hỏng", trong khi guard đúng.

Phía vitest: **70 test** trên chín fixture thật, gồm khối lỗi có kiểm soát
(`simulation_id` lạ · `config` hỏng · bốn hình dạng `scene3d` hỏng).

---

## 6. ĐÍNH CHÍNH — 11 → 12 đại lượng

Wave này phát hiện một con số sai đã lan vào luận văn.

`THESIS_FINAL_ACCEPTANCE_EXECUTION.md`, `CURRENT_STATE`, `STATUS_LEDGER` và hai
chương đều ghi **"11/11 đại lượng"**. Artifact nói **12**:

| ca | số đại lượng |
|---|---|
| `p1` | 3 (`72` · `9` · `3√6`) |
| `p2` · `p6` · `p7` | 1 mỗi ca |
| `p3` · `p4` · `p5` | 2 mỗi ca |
| **tổng** | **12** |

Hai nguồn độc lập xác nhận 12: `SCORING_CORRECTION.json` có **12** mục
`quantities_SUA`, tất cả `exact_answer_match = true`; và cảnh 3D phát đúng **12**
readout, đọc được trên màn hình ở lượt nghiệm thu này.

Con số 11 xuất hiện lần đầu ở `THESIS_ACCEPTANCE_MATRIX_AND_DOCUMENTATION.md §76`
(*"11 đại lượng / 7 ca"*) rồi được chép lại. Nó **chưa từng được máy đối chiếu**:
`doi_chieu_ket_qua_cuoi.py` vốn đã chấm `DAP_SO_KHOP 12/12` và **đạt**, vì
`BANG_CHUAN` liệt kê 12 biểu thức — không ai đối chiếu con số kể ra **bằng chữ**.

**Đã sửa** ở: `docs/thesis/CHAPTER_4_RESULTS_AND_DISCUSSION.md` ·
`CHAPTER_5_CONCLUSION_AND_LIMITATIONS.md` · `CURRENT_STATE` · `STATUS_LEDGER` ·
`THESIS_FINAL_ACCEPTANCE_EXECUTION.md` (đính chính ghi **bên trên** bảng gốc,
bảng gốc giữ nguyên).

**KHÔNG sửa** `THESIS_ACCEPTANCE_MATRIX_AND_DOCUMENTATION.md` — đó là văn bản
**đăng ký trước**, và sửa nó sau khi thấy kết quả là xoá đúng thứ nó tồn tại để
giữ. Sai lệch được ghi lại, không được che.

**Neo bằng máy để không trôi lần nữa:** một test đọc `SCORING_CORRECTION.json`,
đếm 12 và đối chiếu từng biểu thức với đáp số dựng ra từ cảnh.

---

## 7. Quan sát khác — ghi, không sửa

**Nhãn hiển thị rơi về danh từ chung ở ca elip.** Ảnh `p6` cho thấy dải đáp số
đọc *"Diện tích «đối tượng» 25π√5"*, và vật elip mang nhãn *"Đối tượng"*. Con số
đúng, hình đúng, nhưng tên gọi không nói được nó là **thiết diện**. Thẩm quyền
đặt tên là `backend/app/simulation/semantic_program/display_names.py` — sửa nó
chạm `MEASURED_SYSTEM_PATHS`, ngoài phạm vi wave này. Không ảnh hưởng tính đúng.

**Guard `A5` của bộ đánh giá đã phải nới, và nới theo lối kiểm được.**
`test_A5_de_bai_MOI__khong_trung_corpus_phat_trien` quét mọi JSON dưới
`docs/evaluation/geometry/` tìm `problem_text`, loại trừ **theo đường dẫn** thư
mục lượt đo. Fixture hiển thị chở lại `problem_text` (để gõ vào ô nhập thật)
nhưng nằm thư mục khác ⇒ guard kết luận lượt đo cuối đã chấm trên bài cũ — sai,
và sai theo hướng nghiêm trọng nhất có thể.

Nới bằng **lời khai kiểm được**, không bằng danh sách đường dẫn: một file được
miễn trừ khi nó tự khai `source_artifact_path` trỏ tới một artifact **có thật**
dưới thư mục lượt đo. Kèm hai test giữ chiều ngược lại — `A5b` chứng minh quyền
miễn trừ **không mua được bằng một chuỗi đặt bừa** (5 lời khai bịa đều bị từ
chối), `A5c` chứng minh nó **trúng đúng** thứ nó sinh ra để miễn trừ.

---

## 8. Cổng đã chạy

| cổng | kết quả |
|---|---|
| `npx vitest run` | **788 pass / 53 file** — 0 đỏ |
| `npm run build` (`tsc -b && vite build`) | **PASS** |
| `pytest -q` | **4777 pass, 1 skip, 1 deselect** — 0 đỏ (cây sạch) |
| `certify-product-ui-rendering.mjs --faultcheck` | **66/66** · 9 ảnh · **6/6** phép tiêm đỏ đúng chỗ · ngoại lệ **0** |
| xuất xứ artifact | **FRESH**, `dirtyRelevantSources: []` |
| `build_product_ui_fixtures.py` | 9/9 fixture khớp `cham` đóng băng |
| `doi_chieu_ket_qua_cuoi.py` | PASS — 26 file, 19 raw nguyên byte, 12/12 đáp số |
| `freeze_evaluation_candidate.py --verify` | exit 0 — 92 file, `d72db7c3…` |
| `lock_cache_identity.py --verify` | exit 0 @ `CACHE_VERSION = 94` |
| `git diff --check` | sạch |

---

## 9. Reused / created

**Reused** — không viết lại thứ đã có: `BrowserSession` (vòng đời Chrome, một
`serverStarts` cho cả lượt) · `evidence.provenance` · `doi_chieu_ket_qua_cuoi.kiem_bam`
· `verify_and_compile` · `pipeline._dung_scene3d` · `_envelope_tu_route_sinh` ·
`_that_bai_hinh_hoc` · `attach_learner_reason` · `objectsAt` · `hienSo` ·
`hopLeScene3D` · `entitiesPresentAt`.

**Created** — bốn file:

- `backend/scripts/build_product_ui_fixtures.py`
- `frontend/scripts/certify-product-ui-rendering.mjs`
- `frontend/src/simulations/domains/geometry/product-envelope-rendering.test.tsx`
- `docs/PRODUCT_UI_RESULT_RENDERING_AND_DEMO_ACCEPTANCE.md`

**Modified** — ba file: `frontend/scripts/browser-runner.mjs` (thêm
`interceptJson`, additive) · `frontend/src/components/SimulationWorkspace.tsx`
(bản vá §4) · `backend/tests/geometry/test_thesis_acceptance_matrix.py` (§7).

**Duplicate check**: `grep` `certify-.*ui|product-ui|interceptJson|Fetch.enable`
trong `frontend/scripts/` — không script nào đang chặn mạng ở biên API;
`spot-check-baseline-v2.mjs` và `certify-curved-product.mjs` nạp thẳng vào store
nên **không** phủ được response adapter, và cả hai chạy trên corpus khác.

---

```
DEMO_READY_ON_FROZEN_CASES = YES
PRODUCT_DEPLOYMENT_READY   = NOT_CLAIMED
NEXT_ACTION = THESIS_OBJECTIVE_AND_CLAIM_ALIGNMENT_REVIEW
```

`DEMO_READY_ON_FROZEN_CASES` nói đúng chín ca đã đóng băng, ở một bề rộng
(1440 × 900), trên một trình duyệt, với WebGL phần mềm. Nó **không** nói sản phẩm
sẵn sàng triển khai: chưa đo nhiều bề rộng, chưa đo trên máy học sinh thật, chưa
đo với người học, và `PRODUCT_PROMOTION_ELIGIBLE` vẫn `NO` từ lượt đánh giá cuối.
