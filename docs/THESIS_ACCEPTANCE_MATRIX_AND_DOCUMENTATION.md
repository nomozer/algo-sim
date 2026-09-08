# THESIS_ACCEPTANCE_MATRIX_AND_DOCUMENTATION

> **Wave đóng 2026-09-08.** Chuyển từ **xây tính năng** sang **đánh giá khoá
> luận**. Khoá phạm vi · ma trận tuyên bố · bộ ca · tiêu chí · ngân sách ·
> danh tính. **Lượt đo bằng model chưa chạy và không chạy trong wave này.**

```
THESIS_ACCEPTANCE_MATRIX = PASS
FEATURE_SCOPE_COMPLETE   = YES
FEATURE_DEVELOPMENT      = CLOSED
APPLICATION_LLM_CALLS    = 0
PRODUCT_CODE_CHANGED     = NO
```

Sinh bằng `backend/scripts/thesis_final_acceptance_plan.py`; artifact ở
`docs/evaluation/geometry/thesis-final-acceptance/`. Mọi con số trong tài liệu
này **dẫn từ artifact ấy**, không gõ tay.

---

## 0. Danh tính đã khoá

| | |
|---|---|
| `HEAD` | `097f4e6` |
| `CACHE_VERSION` | **94** |
| `CANDIDATE_HASH` | `ddeb0518153facf5…` (92 file) |
| `CORPUS_HASH` | `7c850740b32485ac…` |
| `EXPECTED_RESULTS_HASH` | `1099924b73bf8e54…` |
| `POLICY_HASH` | `26f31dd454e17c92…` |
| `GOLD_PREFLIGHT_HASH` | `985c8922f11d9f5e…` |
| `SCORER_HASH` | `4f7cae906500e0b6…` (`acceptance_verdict.py`) |
| `ATTRIBUTION_RUBRIC` | `CURVED_V3_ATTRIBUTION` — **dùng lại**, xem §10 |
| `RUNNER_HASH` | **`null`** — runner lượt cuối chưa tồn tại, xem §11 |
| `LOCK_STATE` | `LOCKED_PENDING_RUNNER_ALIGNMENT` |

⚠️ `RUNNER_HASH = null` là **cố ý và bắt buộc**. Điền tạm băm của một runner
khác sẽ khoá danh tính vào một thứ không chạy lượt đo — đúng lớp lỗi mà
`V3_LIVE_ENTRYPOINT_INTEGRATION_BLOCKER` đã trả giá một lần.

---

## 1. Bảng 1 — phạm vi năng lực (12 họ)

Nền dẫn từ `MISSING_FAMILY_ROADMAP_REFRESH` (đã có 26 test soát hai chiều);
wave này thêm hai cột: ca nào phủ, và lượt cuối đo được gì.

| họ | trạng thái | EXPR | ĐÚNG | MÔ HÌNH | ỔN ĐỊNH | ca phủ |
|---|---|---|---|---|---|---|
| `point_line_vector_plane` | SUPPORTED | YES | YES | YES | NOT_MEASURED | `p1` |
| `polygon_and_planar_section` | SUPPORTED | YES | YES | YES | NOT_MEASURED | `p1` |
| `convex_polyhedron` | SUPPORTED | YES | YES | YES | NOT_MEASURED | `p1` |
| `nonconvex_polyhedron` | DEVELOPMENT_CONFIRMED | YES | YES | YES | NOT_MEASURED | `p2` |
| `ball` | FOUNDATION_ONLY | YES | YES | NOT_MEASURED | NOT_MEASURED | `p3` |
| `cylinder` | FOUNDATION_ONLY | YES | YES | NOT_MEASURED | NOT_MEASURED | `p4` |
| `cone` | FOUNDATION_ONLY | YES | YES | NOT_MEASURED | NOT_MEASURED | `p5` |
| `curved_circular_section` | FOUNDATION_ONLY | YES | YES | NOT_MEASURED | NOT_MEASURED | `p3` |
| `oblique_cylinder_ellipse` | DEVELOPMENT_CONFIRMED | YES | YES | YES | NOT_MEASURED | `p6` |
| `oblique_cone_section` | FOUNDATION_ONLY | YES | YES | NOT_MEASURED | NOT_MEASURED | `p7` |
| `solid_of_revolution_general` | **OUT_OF_SCOPE** | NO | NO | — | — | `n1` (âm) |
| `composite_boolean` | **OUT_OF_SCOPE** | NO | NO | — | — | `n2` (âm) |

`HO_KHONG_DUOC_PHU = []`. Thẩm quyền: `CAPABILITY_MATRIX.json`.

⚠️ **Cột ỔN ĐỊNH sẽ VẪN là `NOT_MEASURED` sau lượt cuối**, cho mọi họ. Bộ ca có
đúng một ca mỗi họ và chạy đúng một lần — nó không đo được độ ổn định, và điều
đó được khoá **trước** khi có kết quả (`STABILITY_AFTER_FINAL_RUN`, test `G9`).

---

## 2. Bảng 2 — câu hỏi nghiên cứu ↔ metric

| RQ | câu hỏi | tuyên bố | metric | mẫu số | luật đọc |
|---|---|---|---|---|---|
| **RQ1** | độ phủ | C1 · C9 | `NEW_PER_PROBLEM_MODULES` · `ABSENCE_PROOF_PASS` | 7 ca dương · 2 ca âm | = 0 · 2/2 |
| **RQ2** | tính đúng | C2 · C3 · C4 · C5 | `EXACT_ANSWER_MATCH` · `ORACLE_NUMERIC_AGREEMENT` · `SOURCE_INVARIANTS_PASS` · `SCENE3D_PASS` | 11 đại lượng / 7 ca | mọi `*_MISMATCH_COUNT` = 0 |
| **RQ3** | tự sinh | C6 | `FIRST_ATTEMPT_SERVABLE_RATE` · `RECOVERY_WITHIN_ONE_REPAIR_RATE` | 7 ca dương | **KHÔNG NGƯỠNG** — mô tả |
| **RQ4** | an toàn | C7 · C9 | `NEGATIVE_FAIL_CLOSED_RATE` · `SILENT_WRONG_ANSWER_COUNT` | 2 ca âm · 9 ca | 2/2 · = 0 |
| **RQ5** | hiệu quả | C8 | `TOKENS_PER_CORRECT_SERVABLE` · `CALLS_PER_CORRECT_SERVABLE` | số ca ĐẠT (in kèm) | **KHÔNG NGƯỠNG** — mô tả |

Chín tuyên bố `C1`–`C9`, mỗi cái có mười ba cột (gồm `LIMITATION` bắt buộc
không rỗng) ở `CLAIMS_MATRIX.json`. `CLAIMS_REQUIRING_FINAL_RUN = 9`.

⚠️ **Hai RQ không có ngưỡng, và đó là một quyết định chứ không phải một chỗ
trống.** Khoá luận chưa quy định ngưỡng học thuật cho hành vi mô hình. Đặt một
vạch sau khi thấy kết quả là mô tả lại kết quả; đặt trước mà không có nguồn là
bịa ra một tiêu chuẩn. Nên `RQ3` và `RQ5` được **báo cáo kèm mẫu số**, và
policy khoá điều đó bằng `no_threshold_by_design` (test `C4`).

---

## 3. Bảng 3 — bộ ca và độ phủ

Bảy ca dương là một lời giải **set-cover**: mỗi họ trong phạm vi được phủ, và
**bỏ bất kỳ ca nào cũng làm mất ít nhất một họ** (test `A3` kiểm chiều ấy).

| ca | họ phủ | nghĩa vụ | đáp số | oracle |
|---|---|---|---|---|
| `p1` chóp + thiết diện + khoảng cách | linear · section · lồi | `volume` `area` `distance` | `72` · `9` · `3√6` | CLOSED_FORM |
| `p2` chóp đáy ngũ giác **lõm** | lõm | `volume` | `96` | CLOSED_FORM |
| `p3` mặt cầu + thiết diện tròn | cầu · tiết diện tròn | `volume` `area` | `4500π` · `144π` | CLOSED_FORM |
| `p4` hình trụ | trụ | `volume` `lateral_area` | `360π` · `120π` | CLOSED_FORM |
| `p5` hình nón | nón | `volume` `lateral_area` | `100π` · `65π` | CLOSED_FORM |
| `p6` thiết diện **elip** của trụ | elip xiên trụ | `area` | `25π√5` | **LẤY MẪU** |
| `p7` thiết diện **elip** của nón | elip xiên nón | `area` | `2π√6` | **LẤY MẪU** |
| `n1` khối tròn xoay tổng quát | — | — | **từ chối** | absence proof |
| `n2` khối ghép/bù (khoan lỗ) | — | — | **từ chối** | absence proof |

`p2` mang thêm **hai bẫy đã đo**: lấy `abs` từng tam giác quạt cho `120`, bỏ hẳn
đỉnh lõm cho `144` — cả hai khác `96` đủ xa để bộ chấm nói được mô hình hỏng
**kiểu nào**, không chỉ *"sai"*.

### Gold preflight — 0 lượt gọi model

```
GOLD_POSITIVE_SERVABLE   7/7      GOLD_POSTCONDITIONS  7/7
GOLD_EXACT_MATCH         7/7      GOLD_SCENE3D         7/7
GOLD_ORACLE_AGREEMENT    7/7      GOLD_WEAK_KINDS      0
ORACLE_SELF_CHECK        12/12
```

Provider **giả** (gold contract + gold program đóng sẵn), từ
`verify_and_compile` trở đi **thật**: cổng phủ thật, checker thật,
`final_memory` thật, `pipeline._dung_scene3d` thật.

### Oracle độc lập

`thesis_acceptance_oracle.py` **không import bất cứ thứ gì dưới `app.`** — khoá
bằng quét AST (`test_B1`), vì một oracle gọi lại kernel chỉ chứng minh kernel
nhất quán với chính mình.

Với `p6`/`p7` phép độc lập đi xa nhất: **lấy 200 000 điểm trên giao tuyến rồi
tính diện tích đa giác 3D**, không dùng công thức bán trục nào. `p7` đi theo
**tia từ đỉnh** chứ không theo phương trình mặt nón — nên nó không thể "biết
trước" conic thuộc loại gì.

⚠️ **Một đính chính trong chính wave này.** Bản nháp đầu ghi
`oracle_method: SAMPLED` nhưng để `oracle_value` là số dẫn từ **công thức**. Hậu
quả đo được: hạ dung sai từ `1e-8` xuống `1e-12` vẫn XANH — tức cột "oracle"
đang so đáp số với chính công thức kernel dùng, và tính độc lập chỉ có trên
nhãn. Đã sửa: `oracle_value` của `p6`/`p7` nay là số **lấy mẫu**, và `test_H4`
ghim rằng siết dung sai phải làm nó ĐỎ.

---

## 4. Bảng 4 — tiêu chí tính đúng và an toàn

Hai nhóm, **cố ý không gộp**.

### Nhóm BẮT BUỘC — PASS/FAIL

| tiêu chí | ngưỡng | vì sao là PASS/FAIL |
|---|---|---|
| `SILENT_WRONG_ANSWER_COUNT` | **0** | một đáp số sai được phục vụ phá chính luận điểm của đề tài |
| `SERVED_EXACT_MISMATCH_COUNT` | **0** | |
| `SERVED_SOURCE_INVARIANT_VIOLATION_COUNT` | **0** | R0 |
| `SERVED_SCENE3D_MISMATCH_COUNT` | **0** | số đúng mà hình sai vẫn là mô phỏng sai |
| `UNHANDLED_EXCEPTION_COUNT` | **0** | từ chối phải có địa chỉ, không được chết câm |
| `GOLD_PREFLIGHT_PASS_RATE` | **1.0** | ✅ đã đạt, 0 lượt gọi |
| `NEGATIVE_FAIL_CLOSED_RATE` | **1.0** | |

### Nhóm MÔ TẢ — không ngưỡng

`FIRST_ATTEMPT_SERVABLE_RATE` · `RECOVERY_WITHIN_ONE_REPAIR_RATE` ·
`ANALYZE_CORRECT_RATE` · `PROGRAM_VALID_RATE` · `PER_FAMILY_SERVABLE_RATE` ·
`TOKENS_PER_CORRECT_SERVABLE` · `CALLS_PER_CORRECT_SERVABLE`

Policy **cấm** gọi một tỉ lệ trên 7 ca là *"độ chính xác của hệ thống"*, và cấm
so nó với một lượt đo có mẫu số khác.

### Ba cột độc lập

`EXACT_ANSWER_MATCH` · `SCENE3D_PASS` · `SERVABLE` là **ba trường riêng** trong
artifact (test `D2`). Gộp bất kỳ cặp nào là xoá đúng thông tin đã cứu `c7a` của
V3 khỏi bị quy sai trách nhiệm.

---

## 5. Bảng 5 — giới hạn đề tài

| giới hạn | phân loại | bằng chứng |
|---|---|---|
| khối tròn xoay **tổng quát** ngoài phạm vi | kiến trúc | không thẩm quyền tích phân trong `app/simulation` (quét, 0 kết quả) · `MemoryType` không có kiểu biểu thức hàm · `curved_kind` đóng ở `{ball, cylinder, cone}` |
| khối **ghép/bù** ngoài phạm vi | kiến trúc | không thẩm quyền boolean trong `geometry/` (quét, 0 kết quả) · điều kiện TOÀN CỤC *"hai mặt khác nhau xuyên qua nhau"* đã được khai là **không kiểm được** |
| bộ đánh giá **không phải held-out** | phương pháp | corpus xây trong kho; `HELD_OUT_CLAIM = NO` khoá trong policy |
| tái lập model ở mức **LIMITED** | phương pháp | alias `gemini-2.5-flash`, `call_gemini` không phơi `modelVersion`; sửa được nhưng phải chạm `MEASURED_SYSTEM_PATHS` |
| **một ca / một họ, một lượt** | thiết kế | `STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED` sau lượt cuối, cho mọi họ |
| `PRODUCT_PROMOTION_ELIGIBLE = NO` **biết trước** | thiết kế | `requires_stability_measured` không thoả được ⇒ kết luận đã biết bất kể kết quả |
| ranh giới ca âm là **BY_ABSENCE_PROOF** | đo lường | hệ **không có mã lỗi nào mang tên** hai họ ấy — xem §6 |
| `SCORER_CONTAINER_NAME_ONLY_HEURISTIC` | đo lường | xem §10 |

⚠️ `foundation_only` chứng minh **đường hệ thống**, chưa chứng minh mô hình. Hai
câu khác nhau, `product_capability.py` là thẩm quyền của câu thứ hai.

---

## 6. Ca âm — ranh giới chứng minh bằng VẮNG MẶT

`BOUNDARY_EVIDENCE_CLASS = BOUNDARY_BY_ABSENCE_PROOF`, **không phải**
`BOUNDARY_BY_NAMED_ERROR_CODE`.

Lý do nói thẳng: hệ **không có** mã lỗi nào phát biểu *"đây là khối tròn xoay
tổng quát, tôi không làm được"*. Nó từ chối vì **không có đường**, chứ không vì
nó nhận ra tên họ hình. Nên:

- `NEGATIVE_FAIL_CLOSED` là **ngưỡng bắt buộc 2/2** — hệ tuyệt đối không được
  phát đáp số;
- `TARGET_BOUNDARY_DEMONSTRATED` được **đo và báo cáo**, nhưng **không** đặt
  thành ngưỡng — đòi nó là đòi một tín hiệu chưa tồn tại.

Đây chính là bài học sự cố ⑥ của V3, áp theo chiều đúng: ở đó một ca âm chết
sớm ở R0 rồi được ghi công cho một phép thử **chưa diễn ra**.

### Dò tất định, 0 lượt gọi

Bốn chương trình mà mô hình dễ viết nhất, chạy qua route thật:

| dò | mã lỗi | stage |
|---|---|---|
| `n1` bịa hình nón cho khối tròn xoay | `input_not_grounded` | grounding |
| `n1` gán thẳng đáp số tích phân | `requested_operation_uncovered` | structural_coverage |
| `n2` dựng hộp rồi TRỪ thể tích trụ bằng số học | `requested_operation_uncovered` | structural_coverage |
| `n2` bỏ hẳn cái lỗ, trả thể tích khối hộp | `requested_operation_uncovered` | structural_coverage |

Cả bốn **fail-closed**. `n1` nhận **cả hai** mã là on-target (đề không nêu một
điểm 3D nào grounded được, nên bịa điểm CHÍNH LÀ triệu chứng của họ không có
đường); `n2` chỉ nhận một (mọi toạ độ đều grounded được, nên chết ở grounding sẽ
là lạc đề). Lý do từng ca ghi trong `CORPUS.json`.

---

## 7. Bảng 6 — ngân sách dự kiến

Dẫn từ **call graph** qua `measurement_policy.derive_application_call_budget`,
không từ số đã dùng ở lượt trước (test `C3` kiểm lại phép dẫn).

| | |
|---|---|
| `EXPECTED_LOGICAL_CALLS` | **18** = 9 ca × (1 analyze + 1 synthesis) |
| `MAX_LOGICAL_CALLS` | **39** = 18 (chặng A) + 21 (chặng B: 7 ca × (1 + 2)) |
| `EXPECTED_PHYSICAL_ATTEMPTS` | 18 |
| `MAX_PHYSICAL_ATTEMPTS` | **156** = 39 × `MAX_ATTEMPTS` (4) — retry TRANSPORT, đếm RIÊNG |
| `EXPECTED_TOTAL_TOKENS` | **74 763** = 9 × (2382 + 5925) |
| `HARD_TOKEN_BUDGET` | **294 000** = 16×4000 + 23×10000 |

Trung vị token dẫn từ **6 lượt telemetry lịch sử thật** (cache 78–94): analyze
**2382**/lượt, synthesis **5925**/lượt. Trần dùng **cận trên quan sát được**
(analyze 3289, synthesis 8982) làm mức đặt chỗ, không dùng trung vị.

### Hai chặng

**A — FIRST_ATTEMPT**: 9 ca, `MAX_SEMANTIC_PROGRAM_ATTEMPTS` ghim xuống **1**,
0 lượt sửa. Ghi xuống đĩa **trước** khi chặng B bắt đầu — con số one-shot không
bao giờ được đẹp lên nhờ một lượt sửa về sau.

**B — TARGETED_RECOVERY**: chỉ ca **dương** chưa đạt và repair-eligible theo
`acceptance_verdict.sua_duoc`, ghim xuống **2** (≤ 1 lượt sửa). Kết quả gọi là
`RECOVERY_WITHIN_ONE_REPAIR`, **không** được gọi là *full-product eventual* —
sản phẩm mặc định cho 3 lượt.

⚠️ **Ca âm không được sửa.** Sửa một ca âm là ép hệ phục vụ một bài ngoài bao
đóng, tức đo ngược lại chính thứ ca âm tồn tại để đo.

---

## 8. Bằng chứng lịch sử — phân loại

| lớp | số artifact |
|---|---|
| `DEVELOPMENT_LIVE` | 73 |
| `DETERMINISTIC_FOUNDATION` | 28 |
| `HISTORICAL_ACCEPTANCE` | 9 |
| `DEVELOPMENT_REPLAY` | 3 |
| **tổng có danh tính** | **113** |

> ### ⚠️ `KHOP_CANDIDATE_HIEN_TAI = 0`
>
> **Không artifact live nào trong kho được sinh trên candidate `ddeb0518`.**
> Mọi con số live hiện có thuộc về một bản hệ CŨ. Đó không phải khiếm khuyết —
> candidate vừa đổi sáng nay ở `OBLIQUE_CONE_SECTION_FOUNDATION` — nhưng nó là
> lý do lượt đo cuối **phải** chạy, và là câu phải viết vào khoá luận cạnh mọi
> con số dẫn lại từ artifact cũ.

Không hàng nào mang `REQUIRES_RERUN = YES`: lượt cuối **không** chạy lại bằng
chứng cũ, nó chạy một bộ ca MỚI. Artifact cũ vẫn là bằng chứng cho tuyên bố của
**chính chúng**, trên candidate của chúng — và giữ **nguyên byte**.

⚠️ 90/113 artifact **không ghi candidate nào** (chúng có trước cơ chế đóng băng
candidate). Chúng không truy được về một bản mã cụ thể; dẫn số từ chúng thì phải
nói kèm điều đó.

---

## 9. Bộ chấm — 15/15 lớp có fixture

Taxonomy là `acceptance_verdict.LOP_PHAN_QUYET` (**dùng lại**, không viết bản
thứ hai). Hai mức bằng chứng, **cố ý không đếm gộp**:

| mức | nghĩa | lớp |
|---|---|---|
| `REAL_PATH` | một `(contract, spec)` thật đi qua `verify_and_compile` | `CORRECT_SERVABLE_RESULT` · `SYSTEM_COVERAGE_FAILURE` · `SYSTEM_EXPRESSIVENESS_GAP`* · `ATTRIBUTION_UNRESOLVED` · `MODEL_STATIC_FAILURE` · `MODEL_GROUNDING_FAILURE` |
| `SYNTHETIC_OUTCOME` | outcome dựng tay — chứng minh NHÁNH phân loại, **không** chứng minh hệ có phát ra tình huống ấy | 9 lớp còn lại |

Ba fixture giữa dùng **chung một chương trình**, khác nhau chỉ ở bằng chứng năng
lực kèm theo. Đó không phải tiết kiệm — đó là chính luận điểm của bộ chấm: cùng
một cái chết ở `ir_static` phải cho **ba phán quyết khác nhau** tuỳ hệ có đường
hay không, và tuỳ ta có biết điều đó hay không.

### Hai lớp §10 yêu cầu mà scorer canonical KHÔNG sinh ra được

| lớp | vì sao | ai chịu trách nhiệm |
|---|---|---|
| `MODEL_ANALYZE_FAILURE` | analyze hỏng ⇒ không có `RequestContract` ⇒ `verify_and_compile` không chạy ⇒ `phan_loai` **chưa từng được gọi** | **runner** phải ghi riêng |
| `SYSTEM_SCENE3D_FAILURE` | `phan_loai` trả `CORRECT_SERVABLE_RESULT` ngay khi `servable`; nhãn **không hạ** khi cảnh hỏng | **runner** phải hạ nhãn khi `servable ∧ ¬scene3d_pass`; `SERVED_SCENE3D_MISMATCH_COUNT = 0` là chỗ nó thành PASS/FAIL |

Ghi ra vì im lặng về điều này là để runner tự phát minh cách đếm.

### ⚠️ `SCORER_CONTAINER_NAME_ONLY_HEURISTIC` — giới hạn đã đo

`nghia_vu_du_noi_dung_hut_ten` kết luận *"nội dung đúng, chỉ hụt TÊN"* khi
chương trình đo **đúng lượng** trên **đúng kiểu chủ thể**. Nó không phân biệt
được *đúng vật* với *một vật khác cùng kiểu*.

Đo được ở dò `n2-b`: chương trình trả thể tích **khối hộp** cho câu hỏi *"phần
còn lại sau khi khoan"*, và bị xếp `SYSTEM_COVERAGE_FAILURE` — tức đổ lỗi cho
HỆ một ca mà mô hình đã trả lời một bài khác.

**Không sai số đo của lượt cuối**: ở ca âm nhánh ấy không chạy
(`la_ca_am=True` trả sớm). Nhưng nó **có thể** sai ở một ca DƯƠNG nếu mô hình đo
đúng lượng trên một vật cùng kiểu nhưng sai vật. Ghi vào giới hạn thay vì sửa
scorer trong wave khoá phạm vi.

---

## 10. Dùng lại, không viết bản thứ hai

| thành phần | quyết định | lý do |
|---|---|---|
| `acceptance_verdict.py` | **REUSE** | taxonomy canonical, 15 lớp, đã có nền test |
| `acceptance_integrity.py` | **REUSE** | manifest · seal · artifact · telemetry |
| `measurement_policy.py` | **REUSE, không sửa** | `doc_chinh_sach(path)` vốn đã nhận đường dẫn ⇒ policy mới nạp được mà không đụng module chung |
| `curved_v3_attribution_rubric.json` | **REUSE** | rubric phát biểu hoàn toàn theo NĂNG LỰC/KIỂU, `case_id_decides_verdict: false`; không một dòng nào nói về hình cong |
| `CAPABILITY_MATRIX.json` (roadmap) | **REUSE làm nền** | đã có 26 test soát hai chiều |
| `freeze_evaluation_candidate` · `runtime_identity` | **REUSE** | thẩm quyền danh tính |

**Tạo mới** (4 file, đều ở `scripts/` + `tests/` — **ngoài** `MEASURED_SYSTEM_PATHS`):
`thesis_acceptance_corpus.py` · `thesis_acceptance_oracle.py` ·
`thesis_final_acceptance_plan.py` · `policies/thesis_final_acceptance_policy.json`
· `tests/geometry/test_thesis_acceptance_matrix.py`.

**Duplicate check**: không module nào trùng trách nhiệm. Oracle *phải* là file
riêng — trách nhiệm của nó là **không** biết gì về kernel, và trộn nó vào corpus
sẽ làm guard AST mất nghĩa.

---

## 11. Runner — `FINAL_ACCEPTANCE_RUNNER_READY = NO`

Đo trên **mã nguồn** `run_curved_acceptance.py`, không tự khai. Mười lăm yêu
cầu, **mười đạt, năm không**:

| khoảng trống | bằng chứng trong mã |
|---|---|
| `doc_fixed_corpus` | `main_async` lấy bộ ca **duy nhất** từ `nap_ca_v3()`; hàm ấy hiện vẫn trả về 13 ca V3 đã rút (`case_set_hash eb1c402a…`) |
| `giu_moi_raw_candidate` | chỉ ghi candidate **cuối** mỗi chặng; attempt bên trong `stage_semantic_program` không được giữ |
| `scorer_canonical` | ca âm chấm bằng `_cham_am`/`cham_ranh_gioi` **của riêng runner**, với `_MA_RANH_GIOI_CONG` ghim cứng cho hình cong — không phải `acceptance_verdict.cham_ca_am` |
| `hai_chang_A_B` | chặng 8B khôi phục `MAX_SEMANTIC_PROGRAM_ATTEMPTS` về **3**, không phải 2 |
| `nap_chinh_sach_khoa_luan` | `mo_luot_do_v3` gọi `MP.nap_nguong()` — hằng số trỏ `curved_v3_threshold_policy.json`; `acceptance_integrity.mo_run` cũng ghim `MP.CHINH_SACH_NGUONG` vào manifest |

> ### ⚠️ Một khẳng định của tôi bị chính phép đo BÁC
>
> Viết test lần đầu tôi khẳng định *"guard của V3 phải bác bộ ca khoá luận"*.
> Đo ra: **KHÔNG**. `kiem_bo_ca_la_pool_v3` là một **DANH SÁCH CẤM** — nó chỉ
> ném khi id trùng corpus phát triển V1/V2; `p1…p7` đi qua im lặng.
>
> Và lý do thật còn khác nữa: runner V3 **không "từ chối"** bộ ca khoá luận —
> nó **không có đường nào để nhận**. Chạy nó lên sẽ lặng lẽ đo lại pool V3 **đã
> tiêu**, tức tiêu quota thật cho một câu hỏi đã trả lời.
>
> Ghi nguyên trạng thay vì sửa test cho êm. `test_G2` nay ghim đúng điều đo được.

Vì vậy `IDENTITY_LOCK.LOCK_STATE = LOCKED_PENDING_RUNNER_ALIGNMENT` và
`RUNNER_HASH = null`.

---

## 12. Cache · candidate · cổng

```
PRODUCT_CODE_CHANGED           NO
MODEL_FACING_CONTRACT_CHANGED  NO
CACHE_VERSION                  94 → 94  (KHÔNG bump)
CANDIDATE_HASH                 ddeb0518… → ddeb0518…  (KHÔNG đổi)
PRODUCT_CAPABILITY_CHANGED     NO
APPLICATION_LLM_CALLS          0
```

**Vì sao KHÔNG bump**: wave chỉ thêm file ở `backend/scripts/`,
`backend/tests/` và `docs/` — không đường nào trong số đó thuộc
`MEASURED_SYSTEM_PATHS`, và không byte nào của prompt/thẻ/lược đồ đổi. Kiểm
bằng máy: `freeze_evaluation_candidate.py --verify` exit 0 (92 file,
`ddeb0518…`) · `lock_cache_identity.py --verify` exit 0 (v94, môi trường
`12542444…`).

### Cổng

| cổng | kết quả |
|---|---|
| `tests/geometry/test_thesis_acceptance_matrix.py` | **48 pass** |
| `pytest -q` (toàn bộ backend) | xem §13 |
| `freeze_evaluation_candidate --verify` | exit 0 |
| `lock_cache_identity --verify` | exit 0 |
| frontend + build | **INHERITED** — `FRONTEND_TRACKED_BYTES_CHANGED = NO` |

**Nền đỏ**: 48/48 test của wave này ĐỎ ở `097f4e6` (bốn module chưa tồn tại).
**Chín phép tiêm** ở nhóm `H`, mỗi phép chứng minh một guard cụ thể có răng —
và ba trong số đó bắt được lỗi **thật** trong lúc dựng: quy ước hiển thị
(`25√5π` ≠ `25π√5`), oracle lấy mẫu bị gán giá trị công thức, và giả định sai về
guard denylist của V3.

---

## 13. Việc kế tiếp

```
NEXT_ACTION = THESIS_FINAL_ACCEPTANCE_RUNNER_ALIGNMENT
```

Đóng **năm** khoảng trống ở §11, rồi mới tới
`THESIS_FINAL_ACCEPTANCE_EXECUTION` trên **đúng** `IDENTITY_LOCK.json` này.
Lượt cuối được phép chạy khi và chỉ khi `FINAL_ACCEPTANCE_RUNNER_READY = YES`.

⚠️ **Không sửa corpus, policy hay identity lock để runner dễ viết hơn.** Chúng
đã khoá **trước** kết quả, và đó là toàn bộ giá trị của chúng.
