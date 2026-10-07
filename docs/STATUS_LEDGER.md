# STATUS_LEDGER.md — SỔ TRẠNG THÁI SẢN PHẨM

> **Luật của file này:** mỗi dòng phải trỏ tới **bằng chứng chạy được**. Không
> có bằng chứng ⇒ không được ghi DONE. Bằng chứng sinh từ commit khác HEAD ⇒
> `STALE_EVIDENCE`, cũng không được ghi DONE (`evidence.mjs::assertFresh`).
>
> Cập nhật ở CUỐI mỗi wave. Số sống vẫn ở `CURRENT_STATE.md`.

**HEAD lúc lập sổ:** `a3dac3b` (Wave 0–1 làm trên đó, commit ngay sau).

> **Điều hướng (2026-10-05, `cuboid-final-review`).** Khoá phạm vi hiện hành: **§0-2026-08-24** (dưới). Lịch sử
> các wave hình học: **§6**. Các bảng trạng thái của giai đoạn Tin học — §1 Kiến trúc & năng lực · §2 Tương tác
> theo miền · §3 Sản phẩm & lớp học · §4 Đo lường & chất lượng · §4b–§4e Wave 5–8 · §4f Wave 10 · §4g và các
> mục W12 · §4h vNext · §5 Phủ chương trình — cùng tên đề tài 2026-08-18 đã hết hiệu lực, được chuyển
> **nguyên văn** sang [`legacy/STATUS_LEDGER_INFORMATICS_ERA.md`](legacy/STATUS_LEDGER_INFORMATICS_ERA.md). Không thêm dòng mới vào các mục ấy.

## 0. KHOÁ PHẠM VI ĐỀ TÀI — ràng buộc cho mọi wave còn lại

### TÊN ĐỀ TÀI CANONICAL (chốt 2026-08-18) — HẾT HIỆU LỰC

> Thay bởi §0-2026-08-24 ngay dưới. Nguyên văn khoá phạm vi cũ: [`legacy/STATUS_LEDGER_INFORMATICS_ERA.md`](legacy/STATUS_LEDGER_INFORMATICS_ERA.md).

### §0-2026-08-24 — ĐỔI ĐỀ TÀI (nguồn: giáo viên hướng dẫn). §0 cũ HẾT HIỆU LỰC

**Đề mới:** *"Nghiên cứu và xây dựng hệ thống mô phỏng 3D hình học không gian."*

Thay thế đề chốt 18/08 (*"…kết hợp LLM phân tích bài toán bằng ngôn ngữ tự
nhiên, hỗ trợ dạy học môn **Tin học** THPT"*). Mọi khoá phạm vi bên dưới —
gồm §0-2026-08-20 và bản cắt phạm vi 2026-08 — **không còn ràng buộc**.

⚠️ **Đây KHÔNG phải một wave mới trên hệ cũ.** Đề mới lệch hệ hiện có ở **ba
trục cùng lúc**, và phải nhìn cả ba, vì chỉ nhìn một trục sẽ dẫn tới ước lượng
sai công việc còn lại:

| Trục | Đề mới | Hệ hiện có |
|---|---|---|
| Môn | **hình học không gian** → Toán 11/12 | Tin học THPT |
| Chiều | **3D** | 2D — 23/24 target `('2d',)`; **đúng một** cái có 3D |
| Đối tượng | hình khối **liên tục** | thuật toán **rời rạc** |

**Ghi lại một sự thật dễ quên:** ý tưởng GỐC của dự án là *hình học động — kéo
để thấy bất biến (GeoGebra)*, rồi mới chuyển sang mô phỏng thuật toán. Nên đổi
đề lần này gần với **quay về gốc** hơn là rẽ sang hướng lạ.

#### Giữ được — tài sản lớn nhất, KHÔNG được vứt theo

1. **Ranh giới R0** (LLM đọc đề, engine tất định diễn hoạt) — đúng nguyên với
   hình học, và vẫn là luận điểm mạnh nhất.
2. **Toàn bộ phương pháp đánh giá**: SEALED + custodian độc lập + seed do GVHD
   cấp + oracle không import mã sản phẩm + fail-closed + A/B đồng-primary +
   replay đa đầu vào + taxonomy thất bại 8 tầng + luật báo cáo mẫu nhỏ. Đây là
   phần **khó nhất và mất nhiều tuần nhất**; một hệ hình học cần y hệt.
3. Vỏ frontend, store, timeline/transport, tầng lớp học, hạ tầng test 4 tầng.
4. **Three.js đã là dependency**, và `protocol_encapsulation` là tiền lệ 3D có
   `meaning_of_z` mang nghĩa.

#### KHÔNG giữ được — phải làm lại phần lõi miền

- 24 module (đều là nội dung Tin học) · 12 family · neo chương trình.
- **9 primitive thị giác** (`array_strip`, `stack_view`, `graph_view`, …) và
  **14 `MemoryType`** — **không có một thứ nào là hình học**. Hình học cần
  điểm · đường · mặt phẳng · khối · thiết diện · giao tuyến.
- **11 nghĩa vụ** — toàn rời rạc. Hình học cần *thuộc · song song · vuông góc ·
  đồng phẳng · khoảng cách · thể tích*.
- Kho **189 bài SGK Tin học** và toàn bộ nội dung SEALED #1/#2.

#### Câu hỏi CHẶN, phải trả lời trước khi mở wave nào

**Nhánh LLM còn trong đề không?** Tên đề mới **không nhắc** LLM hay ngôn ngữ tự
nhiên. Hai ngả dẫn tới hai luận văn khác hẳn:

- **CÒN** ⇒ kiến trúc chuyển gần trọn; chỉ đổi *miền* (IR primitive, nghĩa vụ,
  renderer). Toàn bộ máy đánh giá dùng lại. Novelty giữ nguyên.
- **KHÔNG** ⇒ thành công cụ trực quan 3D thuần; phần lớn hạ tầng LLM + đánh giá
  thành **gánh nặng chết**, và novelty phải tìm chỗ khác.

Chưa trả lời được câu này thì **cấm đẻ wave**, cấm viết primitive hình học.

#### Kỷ luật giữ nguyên

`CURRICULUM_SUPPORT_PARTIAL` và `LEARNER_IMPACT_NOT_EVALUATED` **vẫn giữ** —
đổi đề không sinh thêm bằng chứng. Số của SEALED #1 (`A 3/40 · B 1/40`) vẫn là
kết quả thật của hệ Tin học, và **vẫn trích được** nếu luận văn còn kể phần đó.

---

### §0-2026-08-20 — MỞ LẠI phạm vi "sinh mô phỏng" (nguồn: giáo viên hướng dẫn)

> ⚠️ **HẾT HIỆU LỰC 2026-08-24** — xem §0-2026-08-24 bên trên. Giữ lại để tra
> lịch sử quyết định, **không** đọc như ràng buộc hiện hành.

Khoá phạm vi 2026-08 (24 target, không sinh tự động) **được thay thế ở ĐÚNG
phần sinh mô phỏng** bởi
`docs/legacy/superpowers/specs/2026-08-20-semantic-program-generative-route-design.md`
(APPROVED DESIGN, `0c53882`). Kế hoạch thực thi: `docs/legacy/superpowers/plans/2026-08-20-semantic-program-generative-route.md`.

**Lõi đề tài được bổ sung một nhánh**, không thay nhánh cũ: yêu cầu học bằng
ngôn ngữ tự nhiên → **LLM tổng hợp bounded Semantic IR** → validate tất định →
**interpreter tất định thực thi** → kiểm chứng nghĩa vụ → dẫn xuất trực quan 2D.

**Phạm vi mới HẸP và có hàng rào** (spec §1.1 — đọc trước khi mở bất kỳ wave nào):
2D only · bounded IR · miền thuật toán rời rạc/hữu hạn/có biên · 6 ranh giới ·
hard scope lock sau khi SEALED niêm phong.

**VẪN ngoài mục tiêu** (danh sách trên còn nguyên hiệu lực, không nhân lượt mở
này mà nới): HTML/CSS · CSDL · đóng gói giao thức theo hướng generative · 3D cho
route mới · tắt 24 module cũ · pattern reuse cho route mới · explicit context
caching · mức yếu phục vụ học sinh. Ý tưởng rơi vào đây → `POST_THESIS_BACKLOG.md`.

**Kỷ luật tuyên bố không đổi**: mở phạm vi **không** sinh thêm bằng chứng. Hai
chỉ số phải báo **riêng, đồng-primary** — `A: Generative executability rate`
(kiến trúc có thoát module-per-problem không) và `B: internal servable rate`
(bao nhiêu qua hết cổng nội bộ). Không được gộp làm một để số đẹp hơn.

**Ba chỗ dễ viết sai, chốt 2026-08-22** (chi tiết: `semantic-benchmark/README.md`):

- **B không phải "đúng".** Tên cũ `Safe serve rate` hứa nhiều hơn thứ đo được —
  cổng nội bộ không phải oracle độc lập. Đúng tên là **STRONG-assurance nội
  bộ**; correctness theo oracle độc lập báo **riêng**, và case `servable=true`
  mà oracle nói sai phải được **nêu đích danh**.
- **A − B phải phân rã.** Chỉ một nhánh trong đó là `verification_gap`; các
  nhánh còn lại là chương trình tự mâu thuẫn (C₁b/C₂) hoặc không dựng nổi bề
  mặt thị giác. Gọi cả khối bằng một tên là báo cáo sai.
- **D1 là claim CẤU TRÚC**, không phải giá đo được: sau khi IR sinh xong,
  interpreter chạy bao nhiêu bước cũng không tốn thêm lượt LLM nào. Token/case
  là telemetry hỗ trợ; claim thực nghiệm về token là **D2**.

**Kỷ luật tuyên bố**: chỉ nói điều có bằng chứng. Giữ
`CURRICULUM_SUPPORT_PARTIAL` khi phủ chương trình còn dở, và
`LEARNER_IMPACT_NOT_EVALUATED` vì kho này không chứa nghiên cứu đối chứng trên
người học.

### §0-2026-08-23 — TASK 12 ĐÃ CHẠY. Ba tầng bằng chứng, chỉ tầng 3 được trích

Bằng chứng: **`docs/evaluation/semantic-benchmark/results/OFFICIAL_RESULT.md`**
(+ `sealed_summary.json`, `sealed_cases.json`). Candidate `4e13e2b`, harness
`9d8e1a1`, SEALED `7e5df014…`, N=40, `evaluation_complete = true`, chạy **một
lần** `2026-08-23T05:10:39Z`.

| Owner / Feature | Trạng thái | Bằng chứng | Wave kế |
|---|---|---|---|
| Route sinh ngữ nghĩa — đo held-out chính thức | **DONE (Task 12)** | `results/OFFICIAL_RESULT.md`; A 3/40 · B 1/40 · oracle PASS 2/FAIL 0 | — (cần SEALED mới để đo lại) |
| Biên assurance nội bộ | **DONE — bảo thủ, không lỏng** | 0 sai-chấp-nhận · 1 false rejection (`T11CS-C6-041`) | phân tích C₂ |
| D1 claim cấu trúc | **DONE** | bước 2→22 (×11) vs lượt LLM `[2,4,5,6,7,8]` | — |
| D2 claim thực nghiệm token | **NOT_ESTIMABLE** | `matched_N = 0`; giao ngữ nghĩa×legacy rỗng | SEALED mới |
| Năng lực ngữ nghĩa thật của `4e13e2b` | **CHƯA ĐO TỚI** | 17/40 chết ở `spec_version` float vs `Literal["1.0"]` | **SEALED mới bắt buộc** |

**Ba tầng bằng chứng — không được trộn:**

| tầng | là gì | dùng được cho |
|---|---|---|
| 1. OFFLINE / UNIT / INVARIANT | pytest · vitest · tsc · build · guard | kỹ thuật; **không** là số năng lực |
| 2. INTERNAL LIVE PILOT | `pilot/sealed-pilot-34a10a9c/` + `pilot-results/`→`pilot-results-4/` | **engineering evidence** — dò lỗi, chỉnh hệ trước khi niêm phong |
| 3. **OFFICIAL INDEPENDENT SEALED** | **`results/`** trên `7e5df014…` | **held-out metrics chính thức của luận văn** |

Chỉ **tầng 3** được viết vào kết luận. Số của pilot (tầng 2) **không bao giờ** là
A/B/D — nó chỉ chứng minh quá trình kỹ thuật, và bốn lượt pilot đều xảy ra
**trước** khi SEALED được niêm phong nên luật con dấu không bị đụng.

**Hard scope lock nay có hiệu lực.** SEALED đã mở. Mọi sửa vào prompt · schema ·
taxonomy · primitive · route · checker · interpreter · renderer · ngưỡng
assurance · ngân sách kể từ đây **làm mất hiệu lực con dấu** và bắt buộc niêm
phong tập SEALED MỚI trước khi công bố bất kỳ số nào. Điều này áp cả cho lỗi
`spec_version` đã biết — biết chỗ hỏng **không** cấp quyền vá rồi chạy lại.

## 6. Lịch sử các Wave Đánh Giá & Hoàn Thiện Tuyến Hình Học (2026-09-17 đến 2026-09-22)

### WAVE_ID = COMPLETION_RUNNER_REPAIR_OFFLINE
- **DATE:** 2026-09-17
- **START_BASE:** bd370157
- **CODE_COMMIT_OR_NONE:** 25c3f5b8
- **EVIDENCE_COMMIT_ROLE:** 35d84da0
- **CLASSIFICATION:** RUNNER_REPAIR_OFFLINE
- **PRODUCT_CHANGED:** NO
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/COMPLETION_RUNNER_REPAIR_OFFLINE.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/photo-problem-to-scene/completion-runner-repair-offline/
- **CORRECTED_BY:** NONE
- **NEXT_ACTION_AT_TIME:** STRUCTURED_RELATION_SAFETY_REPAIR

### WAVE_ID = STRUCTURED_RELATION_SAFETY_REPAIR
- **DATE:** 2026-09-17
- **START_BASE:** 35d84da0
- **CODE_COMMIT_OR_NONE:** 8dd5f8b6
- **EVIDENCE_COMMIT_ROLE:** cac49a09
- **CLASSIFICATION:** COMPILER_SAFETY_REPAIR
- **PRODUCT_CHANGED:** YES
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/STRUCTURED_RELATION_SAFETY_REPAIR.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/photo-problem-to-scene/structured-relation-safety-repair/
- **CORRECTED_BY:** NONE
- **NEXT_ACTION_AT_TIME:** N04_TARGETED_REJECTION_REGISTRY_V2_PREREGISTRATION

### WAVE_ID = N04_TARGETED_REJECTION_REGISTRY_V2_PREREGISTRATION
- **DATE:** 2026-09-17
- **START_BASE:** cac49a09
- **CODE_COMMIT_OR_NONE:** 330334a0
- **EVIDENCE_COMMIT_ROLE:** d01254c2
- **CLASSIFICATION:** EVALUATION_PREREGISTRATION
- **PRODUCT_CHANGED:** NO
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/N04_TARGETED_REJECTION_REGISTRY_V2_PREREGISTRATION.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/photo-problem-to-scene/n04-targeted-rejection-registry-v2-preregistration/
- **CORRECTED_BY:** NONE
- **NEXT_ACTION_AT_TIME:** COMPLETION_MEASUREMENT_REPAIR_OFFLINE_POST_SAFETY

### WAVE_ID = COMPLETION_MEASUREMENT_REPAIR_OFFLINE_POST_SAFETY
- **DATE:** 2026-09-18
- **START_BASE:** d01254c2
- **CODE_COMMIT_OR_NONE:** e0fbbb22
- **EVIDENCE_COMMIT_ROLE:** e76419f4
- **CLASSIFICATION:** RUNNER_MEASUREMENT_REPAIR
- **PRODUCT_CHANGED:** NO
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/COMPLETION_MEASUREMENT_REPAIR_OFFLINE_POST_SAFETY.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/photo-problem-to-scene/completion-measurement-repair-offline-post-safety/
- **CORRECTED_BY:** NONE
- **NEXT_ACTION_AT_TIME:** RETRY_REMAINING_PREREGISTERED_CASES_POST_MEASUREMENT_REPAIR

### WAVE_ID = RETRY_REMAINING_PREREGISTERED_CASES_POST_MEASUREMENT_REPAIR
- **DATE:** 2026-09-18
- **START_BASE:** e76419f4
- **CODE_COMMIT_OR_NONE:** NONE
- **EVIDENCE_COMMIT_ROLE:** 12df583a
- **CLASSIFICATION:** LIVE_EVALUATION
- **PRODUCT_CHANGED:** NO
- **MODEL_REQUESTS:** 12
- **REPORT_PATH:** docs/RETRY_REMAINING_PREREGISTERED_CASES_POST_MEASUREMENT_REPAIR.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/photo-problem-to-scene/completion-measurement-repair-offline-post-safety/
- **CORRECTED_BY:** NONE
- **NEXT_ACTION_AT_TIME:** ANALYZE_FAILURE_CLUSTER_DIAGNOSIS

### WAVE_ID = ANALYZE_FAILURE_CLUSTER_DIAGNOSIS
- **DATE:** 2026-09-19
- **START_BASE:** 12df583a
- **CODE_COMMIT_OR_NONE:** 5806fec9
- **EVIDENCE_COMMIT_ROLE:** 0ff69cbb
- **CLASSIFICATION:** DIAGNOSIS_OFFLINE
- **PRODUCT_CHANGED:** NO
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/ANALYZE_FAILURE_CLUSTER_DIAGNOSIS.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/photo-problem-to-scene/analyze-failure-cluster-diagnosis/
- **CORRECTED_BY:** NONE
- **NEXT_ACTION_AT_TIME:** FRESH_PREREGISTERED_FAILURE_REPRODUCTION

### WAVE_ID = FRESH_PREREGISTERED_FAILURE_REPRODUCTION
- **DATE:** 2026-09-19
- **START_BASE:** 0ff69cbb
- **CODE_COMMIT_OR_NONE:** 2dbf23c7
- **EVIDENCE_COMMIT_ROLE:** 45702b36
- **CLASSIFICATION:** REPRODUCTION_PREREGISTRATION
- **PRODUCT_CHANGED:** NO
- **MODEL_REQUESTS:** 1
- **REPORT_PATH:** docs/FRESH_PREREGISTERED_FAILURE_REPRODUCTION.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/photo-problem-to-scene/fresh-preregistered-failure-reproduction/
- **CORRECTED_BY:** NONE
- **NEXT_ACTION_AT_TIME:** SAFE_STRUCTURE_TRACE_REPAIR_OFFLINE

### WAVE_ID = SAFE_STRUCTURE_TRACE_REPAIR_OFFLINE
- **DATE:** 2026-09-20
- **START_BASE:** 45702b36
- **CODE_COMMIT_OR_NONE:** 866a1257
- **EVIDENCE_COMMIT_ROLE:** efee245c
- **CLASSIFICATION:** RUNNER_PERSISTENCE_REPAIR
- **PRODUCT_CHANGED:** NO
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/SAFE_STRUCTURE_TRACE_REPAIR_OFFLINE.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/photo-problem-to-scene/safe-structure-trace-repair-offline/
- **CORRECTED_BY:** SAFE_STRUCTURE_TRACE_REPAIR_EVIDENCE_RECONCILIATION
- **NEXT_ACTION_AT_TIME:** FRESH_PREREGISTERED_FAILURE_REPRODUCTION_RETRY

### WAVE_ID = SAFE_STRUCTURE_TRACE_REPAIR_EVIDENCE_RECONCILIATION
- **DATE:** 2026-09-20
- **START_BASE:** efee245c
- **CODE_COMMIT_OR_NONE:** NONE
- **EVIDENCE_COMMIT_ROLE:** c6c6448e
- **CLASSIFICATION:** RECONCILIATION_OFFLINE
- **PRODUCT_CHANGED:** NO
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/SAFE_STRUCTURE_TRACE_REPAIR_EVIDENCE_RECONCILIATION.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/photo-problem-to-scene/safe-structure-trace-repair-evidence-reconciliation/
- **CORRECTED_BY:** NONE
- **NEXT_ACTION_AT_TIME:** FRESH_PREREGISTERED_FAILURE_REPRODUCTION_RETRY

### WAVE_ID = FRESH_PREREGISTERED_FAILURE_REPRODUCTION_RETRY
- **DATE:** 2026-09-21
- **START_BASE:** c6c6448e
- **CODE_COMMIT_OR_NONE:** 934b4aeb
- **EVIDENCE_COMMIT_ROLE:** d09331ea
- **CLASSIFICATION:** LIVE_RETRY_EVALUATION
- **PRODUCT_CHANGED:** NO
- **MODEL_REQUESTS:** 2
- **REPORT_PATH:** docs/FRESH_PREREGISTERED_FAILURE_REPRODUCTION_RETRY.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/photo-problem-to-scene/fresh-preregistered-failure-reproduction-retry/
- **CORRECTED_BY:** MODEL_VARIANCE_EVIDENCE_REVIEW
- **NEXT_ACTION_AT_TIME:** MODEL_VARIANCE_EVIDENCE_REVIEW

### WAVE_ID = MODEL_VARIANCE_EVIDENCE_REVIEW
- **DATE:** 2026-09-21
- **START_BASE:** d09331ea
- **CODE_COMMIT_OR_NONE:** 3ba5afbb
- **EVIDENCE_COMMIT_ROLE:** 63eb0640
- **CLASSIFICATION:** EVIDENCE_REVIEW_OFFLINE
- **PRODUCT_CHANGED:** NO
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/MODEL_VARIANCE_EVIDENCE_REVIEW.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/photo-problem-to-scene/model-variance-evidence-review/
- **CORRECTED_BY:** MODEL_VARIANCE_EVIDENCE_PROVENANCE_REPAIR_OFFLINE
- **NEXT_ACTION_AT_TIME:** MODEL_VARIANCE_EVIDENCE_PROVENANCE_REPAIR_OFFLINE

### WAVE_ID = MODEL_VARIANCE_EVIDENCE_PROVENANCE_REPAIR_OFFLINE
- **DATE:** 2026-09-22
- **START_BASE:** 63eb0640
- **CODE_COMMIT_OR_NONE:** 18704f14
- **EVIDENCE_COMMIT_ROLE:** 2678cc65
- **CLASSIFICATION:** PROVENANCE_REPAIR_OFFLINE
- **PRODUCT_CHANGED:** NO
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/MODEL_VARIANCE_EVIDENCE_PROVENANCE_REPAIR_OFFLINE.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/photo-problem-to-scene/model-variance-evidence-provenance-repair/
- **CORRECTED_BY:** NONE
- **NEXT_ACTION_AT_TIME:** DOCS_INFORMATION_ARCHITECTURE_AND_HANDOFF_HARDENING

### WAVE_ID = DOCS_INFORMATION_ARCHITECTURE_AND_HANDOFF_HARDENING
- **DATE:** 2026-09-22
- **START_BASE:** 2678cc65
- **CODE_COMMIT_OR_NONE:** 34c36872
- **EVIDENCE_COMMIT_ROLE:** c36f2042
- **CLASSIFICATION:** DOCS_HARDENING_OFFLINE
- **PRODUCT_CHANGED:** NO
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/DOCS_INFORMATION_ARCHITECTURE_AND_HANDOFF_HARDENING.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/photo-problem-to-scene/docs-information-architecture-handoff-hardening/
- **CORRECTED_BY:** DOCS_INFORMATION_ARCHITECTURE_EVIDENCE_PROVENANCE_REPAIR_OFFLINE
- **NEXT_ACTION_AT_TIME:** DOCS_INFORMATION_ARCHITECTURE_EVIDENCE_PROVENANCE_REPAIR_OFFLINE

### WAVE_ID = DOCS_INFORMATION_ARCHITECTURE_EVIDENCE_PROVENANCE_REPAIR_OFFLINE
- **DATE:** 2026-09-22
- **START_BASE:** c36f2042
- **CODE_COMMIT_OR_NONE:** 27ed66aa
- **EVIDENCE_COMMIT_ROLE:** 02a7a860
- **CLASSIFICATION:** PROVENANCE_REPAIR_OFFLINE
- **PRODUCT_CHANGED:** NO
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/DOCS_INFORMATION_ARCHITECTURE_EVIDENCE_PROVENANCE_REPAIR_OFFLINE.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/photo-problem-to-scene/docs-information-architecture-evidence-provenance-repair/
- **CORRECTED_BY:** DOCS_TEST_TELEMETRY_RECONCILIATION_FINAL
- **NEXT_ACTION_AT_TIME:** PRIMITIVE_COMPILER_SECOND_FAMILY_SELECTION_AND_PREREGISTRATION

### WAVE_ID = DOCS_TEST_TELEMETRY_RECONCILIATION_FINAL
- **DATE:** 2026-09-22
- **START_BASE:** 02a7a860
- **CODE_COMMIT_OR_NONE:** dbb1ef1c
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** TELEMETRY_RECONCILIATION_OFFLINE
- **PRODUCT_CHANGED:** NO
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/DOCS_TEST_TELEMETRY_RECONCILIATION_FINAL.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/photo-problem-to-scene/docs-test-telemetry-reconciliation-final/
- **CORRECTED_BY:** NONE
- **NEXT_ACTION_AT_TIME:** PRIMITIVE_COMPILER_SECOND_FAMILY_SELECTION_AND_PREREGISTRATION

### WAVE_ID = PRIMITIVE_COMPILER_SECOND_FAMILY_SELECTION_AND_PREREGISTRATION
- **DATE:** 2026-09-22
- **START_BASE:** 6ec2e0d3
- **CODE_COMMIT_OR_NONE:** abb377b8
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** PREREGISTRATION_OFFLINE
- **PRODUCT_CHANGED:** NO
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/PRIMITIVE_COMPILER_SECOND_FAMILY_SELECTION_AND_PREREGISTRATION.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/photo-problem-to-scene/primitive-compiler-second-family-selection/
- **CORRECTED_BY:** SECOND_FAMILY_PREREGISTRATION_EVIDENCE_REPAIR_OFFLINE
- **NEXT_ACTION_AT_TIME:** PRIMITIVE_COMPILER_SECOND_FAMILY_VERTICAL_SLICE

### WAVE_ID = SECOND_FAMILY_PREREGISTRATION_EVIDENCE_REPAIR_OFFLINE
- **DATE:** 2026-09-22
- **START_BASE:** 2a5b28eb
- **CODE_COMMIT_OR_NONE:** 4a218d2d
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** EVIDENCE_REPAIR_OFFLINE
- **PRODUCT_CHANGED:** NO
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/SECOND_FAMILY_PREREGISTRATION_EVIDENCE_REPAIR_OFFLINE.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/photo-problem-to-scene/second-family-preregistration-evidence-repair/
- **CORRECTED_BY:** SECOND_FAMILY_SOURCE_SCOPE_RECONCILIATION_OFFLINE
- **CORRECTS:** PRIMITIVE_COMPILER_SECOND_FAMILY_SELECTION_AND_PREREGISTRATION
- **NEXT_ACTION_AT_TIME:** PRIMITIVE_COMPILER_SECOND_FAMILY_VERTICAL_SLICE

### WAVE_ID = SECOND_FAMILY_SOURCE_SCOPE_RECONCILIATION_OFFLINE
- **DATE:** 2026-09-22
- **START_BASE:** dc444acd
- **CODE_COMMIT_OR_NONE:** 4630f24d
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** SOURCE_SCOPE_RECONCILIATION_OFFLINE
- **PRODUCT_CHANGED:** NO
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/SECOND_FAMILY_SOURCE_SCOPE_RECONCILIATION_OFFLINE.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/photo-problem-to-scene/second-family-source-scope-reconciliation/
- **CORRECTED_BY:** NONE
- **CORRECTS:** SECOND_FAMILY_PREREGISTRATION_EVIDENCE_REPAIR_OFFLINE
- **NEXT_ACTION_AT_TIME:** SECOND_FAMILY_SOURCE_SCOPE_REAUDIT
- **FINAL_DECISION:** INCOMPLETE (VERTICAL_SLICE_ALLOWED = NO)

### WAVE_ID = GENERIC_SOLID_TOPOLOGY_CONTRACT_DESIGN_AND_PREREGISTRATION_OFFLINE
- **DATE:** 2026-09-22
- **START_BASE:** 65d09a89
- **CODE_COMMIT_OR_NONE:** d0ba8bb7
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** CONTRACT_DESIGN_AND_PREREGISTRATION_OFFLINE
- **PRODUCT_CHANGED:** NO
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/GENERIC_SOLID_TOPOLOGY_CONTRACT_DESIGN_AND_PREREGISTRATION_OFFLINE.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/photo-problem-to-scene/generic-solid-topology-contract-design/
- **CORRECTED_BY:** NONE
- **CORRECTS:** NONE
- **NEXT_ACTION_AT_TIME:** PRIMITIVE_COMPILER_SECOND_FAMILY_VERTICAL_SLICE
- **FINAL_DECISION:** PASS (SOLID_TOPOLOGY_REPRESENTATION = RESOLVED)

### WAVE_ID = PRIMITIVE_COMPILER_SECOND_FAMILY_VERTICAL_SLICE_OFFLINE
- **DATE:** 2026-09-22
- **START_BASE:** f4a547ab
- **CODE_COMMIT_OR_NONE:** 5a5534fe
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** VERTICAL_SLICE_IMPLEMENTATION_AND_VERIFICATION_OFFLINE
- **PRODUCT_CHANGED:** YES
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/PRIMITIVE_COMPILER_SECOND_FAMILY_VERTICAL_SLICE_OFFLINE.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/photo-problem-to-scene/primitive-compiler-second-family-vertical-slice/
- **CORRECTED_BY:** SECOND_FAMILY_FROZEN_BENCHMARK_ALIGNMENT_REPAIR_OFFLINE
- **CORRECTS:** NONE
- **NEXT_ACTION_AT_TIME:** SECOND_FAMILY_LIVE_SCHEMA_REVALIDATION_PREREGISTRATION
- **FINAL_DECISION:** PASS (PRISM_VERTICAL_SLICE = VERIFIED)

### WAVE_ID = SECOND_FAMILY_FROZEN_BENCHMARK_ALIGNMENT_REPAIR_OFFLINE
- **DATE:** 2026-09-22
- **START_BASE:** b4521d28
- **CODE_COMMIT_OR_NONE:** 0714e929
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** REPORTING_AND_TEST_ASSERTION_EVIDENCE_MISMATCH
- **PRODUCT_CHANGED:** NO
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/SECOND_FAMILY_FROZEN_BENCHMARK_ALIGNMENT_REPAIR_OFFLINE.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/photo-problem-to-scene/second-family-frozen-benchmark-alignment-repair/
- **CORRECTED_BY:** NONE
- **CORRECTS:** PRIMITIVE_COMPILER_SECOND_FAMILY_VERTICAL_SLICE_OFFLINE
- **NEXT_ACTION_AT_TIME:** SECOND_FAMILY_LIVE_SCHEMA_REVALIDATION_PREREGISTRATION
- **FINAL_DECISION:** PASS_WITH_REPORTING_AND_ASSERTION_CORRECTION

### WAVE_ID = SECOND_FAMILY_POST_VERTICAL_SLICE_FULL_REGRESSION_REPAIR_OFFLINE_GATE_2
- **DATE:** 2026-09-23
- **START_BASE:** 8703fb50
- **CODE_COMMIT_OR_NONE:** SELF
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** REGRESSION_REPAIR_OFFLINE
- **PRODUCT_CHANGED:** NO
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/SECOND_FAMILY_POST_VERTICAL_SLICE_FULL_REGRESSION_REPAIR_OFFLINE_GATE_2.md
- **ARTIFACT_PATH:** NONE
- **CORRECTED_BY:** SCHEMA_SYNC_AND_CANDIDATE_REFREEZE_REPAIR_OFFLINE
- **CORRECTS:** NONE
- **NEXT_ACTION_AT_TIME:** SECOND_FAMILY_LIVE_SCHEMA_REVALIDATION_PREREGISTRATION
- **FINAL_DECISION:** PASS (GATE_2_REGRESSION_REPAIR = COMPLETE)

### WAVE_ID = SCHEMA_SYNC_AND_CANDIDATE_REFREEZE_REPAIR_OFFLINE
- **DATE:** 2026-09-23
- **START_BASE:** c69eef96
- **CODE_COMMIT_OR_NONE:** 6eb23e8d
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** SCHEMA_SYNC_AND_CANDIDATE_REFREEZE_OFFLINE
- **PRODUCT_CHANGED:** NO
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/SCHEMA_SYNC_AND_CANDIDATE_REFREEZE_REPAIR_OFFLINE.md
- **ARTIFACT_PATH:** docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json
- **CORRECTED_BY:** NONE
- **CORRECTS:** SECOND_FAMILY_POST_VERTICAL_SLICE_FULL_REGRESSION_REPAIR_OFFLINE_GATE_2
- **NEXT_ACTION_AT_TIME:** SECOND_FAMILY_LIVE_SCHEMA_REVALIDATION_PREREGISTRATION
- **FINAL_DECISION:** PASS (STRICT_SCHEMA_SYNC = PASS, CANDIDATE_REFREEZE = PASS)

### WAVE_ID = SECOND_FAMILY_LIVE_SCHEMA_REVALIDATION_PREREGISTRATION
- **DATE:** 2026-09-24
- **START_BASE:** 002b8da5
- **CODE_COMMIT_OR_NONE:** NONE
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** PREREGISTRATION_OFFLINE
- **PRODUCT_CHANGED:** NO
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/SECOND_FAMILY_LIVE_SCHEMA_REVALIDATION_PREREGISTRATION.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/photo-problem-to-scene/second-family-live-schema-revalidation-preregistration/
- **CORRECTED_BY:** NONE
- **CORRECTS:** NONE
- **NEXT_ACTION_AT_TIME:** SECOND_FAMILY_LIVE_SCHEMA_REVALIDATION
- **FINAL_DECISION:** PASS (GATE_0 = PASS, PREREGISTRATION = VERIFIED)

### WAVE_ID = SECOND_FAMILY_LIVE_SCHEMA_REVALIDATION
- **DATE:** 2026-09-24
- **START_BASE:** ef8af771
- **CODE_COMMIT_OR_NONE:** NONE
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** SCHEMA_ACCEPTED_MODEL_SEMANTIC_FAILURE
- **PRODUCT_CHANGED:** NO
- **MODEL_REQUESTS:** 1
- **REPORT_PATH:** docs/SECOND_FAMILY_LIVE_SCHEMA_REVALIDATION.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/photo-problem-to-scene/second-family-live-schema-revalidation/
- **CORRECTED_BY:** SECOND_FAMILY_LIVE_MEASUREMENT_RECONCILIATION_OFFLINE
- **CORRECTS:** NONE
- **NEXT_ACTION_AT_TIME:** SECOND_FAMILY_SEMANTIC_FAILURE_DIAGNOSIS_OFFLINE
- **FINAL_DECISION:** PASS (SCHEMA_ACCEPTED = YES, SEMANTIC_EXTRACTION = FALSE, NEXT_ACTION = SECOND_FAMILY_SEMANTIC_FAILURE_DIAGNOSIS_OFFLINE)

### WAVE_ID = SECOND_FAMILY_LIVE_MEASUREMENT_RECONCILIATION_OFFLINE
- **DATE:** 2026-09-24
- **START_BASE:** 532f447e
- **CODE_COMMIT_OR_NONE:** NONE
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** HISTORICAL_EVIDENCE_INSUFFICIENT
- **PRODUCT_CHANGED:** NO
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/SECOND_FAMILY_LIVE_MEASUREMENT_RECONCILIATION_OFFLINE.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/photo-problem-to-scene/second-family-live-measurement-reconciliation/
- **CORRECTED_BY:** NONE
- **CORRECTS:** SECOND_FAMILY_LIVE_SCHEMA_REVALIDATION
- **NEXT_ACTION_AT_TIME:** SECOND_FAMILY_LIVE_RETRY_PREREGISTRATION
- **FINAL_DECISION:** HISTORICAL_EVIDENCE_INSUFFICIENT (APPARATUS_REPAIRED = YES, RAW_EVIDENCE_TRUNCATED = YES, NEXT_ACTION = SECOND_FAMILY_LIVE_RETRY_PREREGISTRATION)

### WAVE_ID = SECOND_FAMILY_LIVE_RETRY_PREREGISTRATION
- **DATE:** 2026-09-24
- **START_BASE:** 462645ec
- **CODE_COMMIT_OR_NONE:** ab7d94eb
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** PREREGISTRATION_PASS
- **PRODUCT_CHANGED:** NO
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/SECOND_FAMILY_LIVE_RETRY_PREREGISTRATION.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/photo-problem-to-scene/second-family-live-retry-preregistration/
- **CORRECTED_BY:** NONE
- **CORRECTS:** NONE
- **NEXT_ACTION_AT_TIME:** SECOND_FAMILY_LIVE_RETRY
- **FINAL_DECISION:** PASS (REQUEST_PARITY = PASS, APPARATUS_TESTS = 12_OF_12_PASSED, PERSISTENCE_CONTRACT = VERIFIED, NEXT_ACTION = SECOND_FAMILY_LIVE_RETRY)

### WAVE_ID = SECOND_FAMILY_LIVE_RETRY
- **DATE:** 2026-09-24
- **START_BASE:** 5d92afa2
- **CODE_COMMIT_OR_NONE:** NONE
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** SCHEMA_ACCEPTED_PIPELINE_PASS
- **PRODUCT_CHANGED:** NO
- **MODEL_REQUESTS:** 1
- **REPORT_PATH:** docs/SECOND_FAMILY_LIVE_RETRY.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/photo-problem-to-scene/second-family-live-retry/
- **CORRECTED_BY:** NONE
- **CORRECTS:** SECOND_FAMILY_LIVE_SCHEMA_REVALIDATION
- **NEXT_ACTION_AT_TIME:** PRISM_VERTICAL_SLICE_MERGE_READINESS_REVIEW
- **FINAL_DECISION:** PASS (SCHEMA_ACCEPTED = YES, RAW_PERSISTED = YES, SEMANTICS_VALID = YES, PIPELINE_ANSWER = 30, NEXT_ACTION = PRISM_VERTICAL_SLICE_MERGE_READINESS_REVIEW)

> Các wave 2026-09-25…27 (prism merge review, cuboid/Tier-A, cross-family
> semantic repair) chưa có khối `WAVE_ID` ở đây; nguồn tra cứu của chúng là
> `docs/EVIDENCE_INDEX.md`.

### WAVE_ID = CROSS_FAMILY_HIDDEN_LINE_OCCLUSION_ORACLE_AND_FORMATION_REPAIR
- **DATE:** 2026-09-28
- **START_BASE:** 532d4366
- **CODE_COMMIT_OR_NONE:** b8880d77 (topology/ownership/adaptive occlusion) · 50a31e0b (formation + section identity)
- **COMMITS:** bc19021e red regressions · b8880d77 · 50a31e0b · 1dab0f7d independent oracle + browser gates · 80766b90 frozen human expectations · e115c31d candidate refreeze · 09934eb7 evidence + worktree recovery · 075d484f handoff
- **CANDIDATE:** measurement commit e115c31d · product tree hash 31725284… · product-path commit 1dab0f7d
- **EVIDENCE_COMMIT_ROLE:** 09934eb7
- **CLASSIFICATION:** VERIFICATION_NOT_CLEAN
- **PRODUCT_CHANGED:** YES
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/evaluation/geometry/runs/20260928-cross-family-hidden-line-occlusion-oracle-and-formation-repair/REPORT.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/runs/20260928-cross-family-hidden-line-occlusion-oracle-and-formation-repair/
- **PASS:** product↔oracle exact edge IDs + spans (0 mismatch) · perspective oracle ↔ ray/triangle reference (0 disagreement) · oracle independence · typed formation · stable section identity · worktree recovery 5/5 (required/unknown/unique-commit risk = 0) · candidate/cache 28/28 · build
- **FAIL:** frozen camera identity 2 (`triangular_prism`, `cube`) · mobile `immutable_120_frames` 5/6 families · frontend full 904 pass / 1 fail · backend full 6268 pass / 35 fail / 1 skip / 1 deselect · detached full-gate Python env chưa resolve
- **PUSH / MERGE:** NO / NO
- **CORRECTED_BY:** NONE
- **CORRECTS:** CROSS_FAMILY_SCENE3D_PRODUCT_SEMANTIC_REPAIR (READY_FOR_HUMAN_VISUAL_REVIEW)
- **NEXT_ACTION_AT_TIME:** VERIFICATION_CLEANUP_AFTER_OCCLUSION_REPAIR
- **FINAL_DECISION:** VERIFICATION_NOT_CLEAN (HUMAN_VISUAL_REVIEW = NOT_APPROVED, MERGE_READY = NO)

### WAVE_ID = VERIFICATION_CLEANUP_AFTER_OCCLUSION_REPAIR
- **DATE:** 2026-09-28
- **START_BASE:** 42c736ea
- **CODE_COMMIT_OR_NONE:** f337323f (transport boundary) · 7b8528a9 (camera key + harness settle) · 91d3e9c3 · fe3eccee · 1d1397fa · defb77ed (tooling)
- **COMMITS:** 418db2fb reproduce · 7b8528a9 · 1f151f8d · f337323f · 9c233f10 golden review · 1d1397fa · 5bd8b52c refreeze · 6f8f675e declaration · 91d3e9c3 · fe3eccee · defb77ed · 774377dd evidence
- **CANDIDATE:** 31725284… → 3bc9415b… (clean worktree at 1d1397fa, commit 5bd8b52c) · CACHE_VERSION 102, fingerprint unchanged
- **EVIDENCE_COMMIT_ROLE:** 774377dd (measurement commit defb77ed, detached clean worktree)
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **PRODUCT_CHANGED:** YES
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/evaluation/geometry/runs/w09-verify-cleanup/REPORT.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/runs/w09-verify-cleanup/
- **PASS:** inventory 40 records / 0 unresolved · T3 detached FULL_PRODUCT_GATE_PASS (pytest 6314/0 fail, vitest 906/0 fail, build, demo) · browser 12/12 positive + 12/12 negative · immutable windows 12/12, 0 recompute · frozen camera 3 EXACT + 3 CANONICAL_EQUIVALENT · product/oracle 0 mismatch · backend reconciliation 34/0 unaccounted
- **OPEN (non-blocking):** ISSUE-OPS-FRONTEND-TESTS-SPACE-PATH · ISSUE-EVAL-ORBIT-EVIDENCE-INTERMITTENT
- **PUSH / MERGE:** NO / NO
- **CORRECTED_BY:** NONE
- **CORRECTS:** CROSS_FAMILY_HIDDEN_LINE_OCCLUSION_ORACLE_AND_FORMATION_REPAIR (VERIFICATION_NOT_CLEAN)
- **NEXT_ACTION_AT_TIME:** HUMAN_VISUAL_REVIEW_OF_OCCLUSION_EVIDENCE
- **FINAL_DECISION:** READY_FOR_HUMAN_VISUAL_REVIEW (HUMAN_VISUAL_REVIEW = NOT_APPROVED, MERGE_READY = NO)
- **HUMAN_REVIEW_AFTERWARDS:** FAIL_REQUIRES_PEDAGOGICAL_VISUAL_REPAIR (recorded additively in the w10 run, `inputs/W09_HUMAN_VISUAL_REVIEW.json`)

### WAVE_ID = HUMAN_VISUAL_REVIEW_AND_PEDAGOGICAL_PLAYBACK_CLOSURE
- **DATE:** 2026-09-29
- **START_BASE:** be23e88d
- **CODE_COMMIT_OR_NONE:** 9dc56ae1 (playback, camera, hidden lines, learner surface, causal, narrow panel) · f5a3adf2 (alias conclusion dependencies) · 7a03e50d + f0deaa0d (tree aliases, narrow floating buttons)
- **COMMITS:** 22f162f5 red tests · 9dc56ae1 · 1eca93d7 tooling · 48226ef6 / c13d2712 / bd7b4c27 / 7f5205ca refreezes · 14de613a / 28a5dece declarations · 554df6d8 · c7fee8f8 · dce4aa87 fixtures · f5a3adf2 · c1947f57 · 7a03e50d · 3f24b943 · ea18ee79 · f0deaa0d · 26dfba43 · 5e6e1583 · 40ce889f (measurement) · 52de6f22 (post-processing) · 8a09a5d8 evidence
- **CANDIDATE:** 3bc9415b… → 875bc19c… → 8539acbc… (clean worktrees; last refreeze 7f5205ca, product commit f0deaa0d) · CACHE_VERSION 102 → 103 (user decision; fingerprint b1714b56… unchanged)
- **EVIDENCE_COMMIT_ROLE:** 8a09a5d8 (measurement commit 40ce889f, detached clean worktrees)
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **PRODUCT_CHANGED:** YES
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/evaluation/geometry/runs/w10-pedagogical-playback/REPORT.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/runs/w10-pedagogical-playback/
- **PASS:** T3 from a path with a space FULL_PRODUCT_GATE_PASS (pytest 6368/0 fail, vitest 946/0 fail, build, demo) · browser 12/12 positive + 12/12 negative · occlusion 24/24, frozen expectations DECLARED_CAMERA_CHANGE 6/6 · learner playback 12/12 × 17 checks, orbit laps 60/60 · 60 hidden-edge crops, 0 oracle disagreements, 0 duplicate owners · candidate/cache/schema verify
- **CLOSED:** ISSUE-OPS-FRONTEND-TESTS-SPACE-PATH · ISSUE-EVAL-ORBIT-EVIDENCE-INTERMITTENT
- **OPEN (non-blocking):** ISSUE-OPS-BROWSER-SCRIPTS-SPACE-PATH · 1 px lines (WebGL `linewidth`) · per-solid visibility (multi-solid scenes need `occluders`)
- **PUSH / MERGE:** NO / NO
- **CORRECTED_BY:** NONE
- **CORRECTS:** VERIFICATION_CLEANUP_AFTER_OCCLUSION_REPAIR (human review FAIL_REQUIRES_PEDAGOGICAL_VISUAL_REPAIR)
- **NEXT_ACTION_AT_TIME:** HUMAN_VISUAL_REVIEW_OF_PEDAGOGICAL_PLAYBACK_EVIDENCE
- **FINAL_DECISION:** READY_FOR_HUMAN_VISUAL_REVIEW (HUMAN_VISUAL_REVIEW = NOT_APPROVED, MERGE_READY = NO)
- **HUMAN_REVIEW_AFTERWARDS:** FAIL_REQUIRES_TARGETED_PEDAGOGICAL_REPAIR, W10-H1…H9 (recorded additively in the w11 run, `inputs/W10_HUMAN_VISUAL_REVIEW.json`)

### WAVE_ID = W11_PEDAGOGICAL_FORMULA_VISUAL_POLISH_AND_HUMAN_REREVIEW
- **DATE:** 2026-09-29
- **START_BASE:** b9193766
- **CODE_COMMIT_OR_NONE:** f147dde6 (given lengths, grounding by length invariant, formula references; CACHE_VERSION 103 → 104) · e186b4cf (causal tiers, px vertex markers, light auxiliary lines, numerical "Dựa trên") · e633ad0c (camera target for the harness) · 60292ecf ("Xem lại toàn hình" ignores infinite lines and markers)
- **COMMITS:** e90363a4 run renames · ca77665d w10 verdict + BEFORE trace · f147dde6 · e186b4cf · 5f44eb85 / e633ad0c / 7efdae4a tooling · 60292ecf · a39028de refreeze + cache locks · df52e745 scenarios · 48c676d5 fixtures · 39e54046 (oracle signature; measurement) · ac19e03d (trace; post-processing) · 5e3dbab4 evidence
- **CANDIDATE:** 8539acbc… → df04a613… (refrozen ONCE in a clean worktree at 7efdae4a, product commit 60292ecf) · CACHE_VERSION 103 → 104 (fingerprint b1714b56… unchanged)
- **EVIDENCE_COMMIT_ROLE:** 5e3dbab4 (measurement commit 39e54046, detached clean worktree)
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **PRODUCT_CHANGED:** YES
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/evaluation/geometry/runs/w11-pedagogical-polish/REPORT.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/runs/w11-pedagogical-polish/
- **PASS:** T3 from a path with a space FULL_PRODUCT_GATE_PASS at 5e3dbab4 (pytest 6411/0 fail, vitest 958/0 fail, build, demo, crash surface; 6368 → 6370 → 6411 reconciled) · browser 12/12 positive + 12/12 negative, planned rotation first time 12/12 · occlusion 24/24, frozen expectations DECLARED_CAMERA_CHANGE 6/6 · learner playback 12/12 × 18 checks, orbit laps 60/60 · 64 hidden-edge crops, 0 oracle disagreements, 0 duplicate owners · formula provenance 5/5 volume families · candidate/cache/schema verify
- **OPENED:** ISSUE-ARCH-LLM-ROUTE-LENGTH-NOT-TEXT-GROUNDED · ISSUE-OPS-OFFLINE-SAMPLES-STALE · ISSUE-OPS-DIST-ACL-OWNERSHIP
- **OPEN (non-blocking):** ISSUE-OPS-BROWSER-SCRIPTS-SPACE-PATH · 1 px lines · per-solid visibility
- **PUSH / MERGE:** NO / NO
- **CORRECTED_BY:** NONE
- **CORRECTS:** HUMAN_VISUAL_REVIEW_AND_PEDAGOGICAL_PLAYBACK_CLOSURE (human review FAIL_REQUIRES_TARGETED_PEDAGOGICAL_REPAIR)
- **NEXT_ACTION_AT_TIME:** HUMAN_VISUAL_REREVIEW_OF_PEDAGOGICAL_POLISH_EVIDENCE
- **FINAL_DECISION:** READY_FOR_HUMAN_VISUAL_REVIEW (HUMAN_VISUAL_REVIEW = NOT_APPROVED, MERGE_READY = NO)
- **HUMAN_REVIEW_AFTERWARDS:** NEEDS_CHANGES, W11-H1…H5 — timeline mixes construction with calculation steps, static steps, the solution layer, dark orange with two meanings, a GIVEN length not in the problem (recorded additively in the w12 run, `inputs/W11_HUMAN_VISUAL_REVIEW.json`)

### WAVE_ID = W12_PEDAGOGICAL_TIMELINE_AND_SOURCE_GROUNDING_CLOSURE
- **DATE:** 2026-09-30 … 2026-10-01
- **START_BASE:** a4fd5fec
- **CODE_COMMIT_OR_NONE:** 79eb1e59 (GIVEN needs evidence from the problem text; three stable codes, never sent to repair) · 98b505ef (geometry timeline separate from solution events; solution panel) · 233f8720 (one role-colour table, blue = being looked at) · d17550c3 (CACHE_VERSION 104 → 105) · 8aaeae80 (points pinned to unstated coordinate claims refused; P1 under NFKC) · 4014f311 (causal context strokes neutral)
- **COMMITS:** 1fd55d99 / fb4ea271 red tests · 79eb1e59 · 98b505ef · 233f8720 · d17550c3 · b9c60010 freeze 1 · 8aaeae80 · 054bc08d freeze 2 · e115eede tooling (BROWSER-1, superseded) · 4014f311 · 7b039621 hue gate (BROWSER-2, superseded for provenance) · 6569ed41 sheet legend · 399fc423 evidence of BROWSER-2 · c243968b freeze 3 + scenarios (measurement) · 442584cf evidence · docs
- **CANDIDATE:** df04a613… → 548f5b3b… (frozen THREE times in a clean worktree; intermediates 8ffd6d46 and 548f5b3b@8aaeae80 declared) · CACHE_VERSION 104 → 105 (fingerprint b1714b56… unchanged)
- **EVIDENCE_COMMIT_ROLE:** 442584cf (measurement commit c243968b, detached clean worktree)
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **PRODUCT_CHANGED:** YES
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/evaluation/geometry/runs/w12-pedagogical-grounding-closure/REPORT.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/runs/w12-pedagogical-grounding-closure/
- **PASS:** T3 from a path with a space FULL_PRODUCT_GATE_PASS at 442584cf (pytest 6443/0 fail, vitest 1010/0 fail, build, demo, crash surface; 6411 → 6443 reconciled) · browser 12/12 positive + 12/12 ungrounded negative (GIVEN_VALUE_NOT_IN_SOURCE, no canvas, no answer) · geometry steps = expected 12/12, 0 static frames, 0 result steps · solution panel in sync, answer once · causal canvas role hues clean 12/12 (gate validated on a known answer) · occlusion 24/24, frozen expectations DECLARED_CAMERA_CHANGE 6/6 · learner playback 12/12 × 19 checks, orbit laps 60/60 · 64 hidden-edge crops, 0 oracle disagreements, 0 duplicate owners · candidate/cache/schema verify · 8/8 temporary worktrees removed
- **CLOSED:** ISSUE-ARCH-LLM-ROUTE-LENGTH-NOT-TEXT-GROUNDED
- **OPENED:** ISSUE-ARCH-ASSUMPTION-CHANNEL-UNSTATED-DIMENSION · ISSUE-EVAL-CDP-SEND-NO-TIMEOUT
- **OPEN (non-blocking):** ISSUE-OPS-DIST-ACL-OWNERSHIP · ISSUE-OPS-OFFLINE-SAMPLES-STALE · ISSUE-OPS-BROWSER-SCRIPTS-SPACE-PATH · 1 px lines · per-solid visibility
- **PUSH / MERGE:** NO / NO
- **CORRECTED_BY:** NONE
- **CORRECTS:** W11_PEDAGOGICAL_FORMULA_VISUAL_POLISH_AND_HUMAN_REREVIEW (human review NEEDS_CHANGES)
- **NEXT_ACTION_AT_TIME:** HUMAN_VISUAL_REREVIEW_OF_GEOMETRY_TIMELINE_EVIDENCE
- **FINAL_DECISION:** READY_FOR_HUMAN_VISUAL_REVIEW (HUMAN_VISUAL_REVIEW = NOT_APPROVED, MERGE_READY = NO)

### WAVE_ID = W13_GEOMETRY_CAPABILITY_AND_NON_ABSOLUTE_ARCHITECTURE_PREREGISTRATION
- **DATE:** 2026-10-01
- **START_BASE:** bf5a7907
- **CODE_COMMIT_OR_NONE:** NONE (documentation, evidence and the docs-audit allow-list only; backend/app and frontend/src untouched)
- **COMMITS:** docs(architecture) audit + matrix v2 + inventory + grounding probe · docs(eval) preregistration + W12 review record + run docs + living docs
- **CANDIDATE:** 548f5b3b… unchanged (verify PASS at start and end) · CACHE_VERSION 105 unchanged · schema mirrors byte-identical
- **EVIDENCE_COMMIT_ROLE:** SELF (docs-only run)
- **CLASSIFICATION:** ARCHITECTURE_PREREGISTRATION_READY
- **PRODUCT_CHANGED:** NO
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/evaluation/geometry/runs/w13-geometry-preregistration/REPORT.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/runs/w13-geometry-preregistration/
- **PASS:** W12 human review recorded additively (NEEDS_CHANGES, merge NO, W12-H1…H4; four families PROVISIONAL_PASS; amber section = design question) · root cause of H1/H2 read from code (per-family compiler sequences) · 67 absolute assumptions classified A–J with file:line sources (10 J, 5 HIGH) · 17 groups × 17 layers capability matrix v2 (does not override product_capability.py or CAPABILITY_MATRIX.json) · generic formation model, assumption/default policy, source-grounding table (offline probe, 25 rows, 0 calls), capability-based environment policy · W14 preregistered · docs audit + docs tests · candidate/cache/schema verify
- **CLOSED:** ISSUE-ARCH-PRISM-COMPILER-GAP · ISSUE-ARCH-REQUEST-CONTRACT-PRISM-GAP (stale; resolved by code since 5a5534fe, verified in the audit)
- **OPENED:** ISSUE-ARCH-FORMATION-PER-FAMILY-SEQUENCE · ISSUE-ARCH-SOURCE-LENGTH-UNLABELLED-PHRASE · ISSUE-OPS-TEST-EXTERNAL-EVIDENCE-PATH · ISSUE-ARCH-PROMPT-OBLIQUE-SECTION-STALE · ISSUE-ARCH-EXACT-PLACEMENT-FEASIBILITY · ISSUE-DOCS-STALE-CAPABILITY-CLAIMS
- **OPEN (blocking merge of the branch):** ISSUE-ARCH-ASSUMPTION-CHANNEL-UNSTATED-DIMENSION (W12-H4) · W12-H1/H2 formation
- **FULL_PRODUCT_SUITE:** NOT_RUN_NOT_REQUIRED_FOR_DOCS_ONLY_AUDIT
- **PUSH / MERGE:** NO / NO
- **CORRECTED_BY:** NONE
- **CORRECTS:** W12_PEDAGOGICAL_TIMELINE_AND_SOURCE_GROUNDING_CLOSURE (human review NEEDS_CHANGES)
- **NEXT_ACTION_AT_TIME:** W14_GENERIC_FORMATION_AND_ASSUMPTION_FOUNDATION (after user decisions D2, D3)
- **FINAL_DECISION:** ARCHITECTURE_PREREGISTRATION_READY

### WAVE_ID = W14_GENERIC_FORMATION_AND_ASSUMPTION_FOUNDATION
- **DATE:** 2026-10-01 → 2026-10-02
- **START_BASE:** ce9c672d
- **CODE_COMMIT_OR_NONE:** 44f2dd32 (formation pass) · d537cf74 (trust policy) · 2f2c97b2 (length connector vocabulary) · 69d3c985 (sample text, frontend/src) · 733435ac (CACHE_VERSION 106) · a2af56e4 (ponytail cleanup; last product commit)
- **COMMITS:** red tests 0daa6354 + characterization 1a8ea7b8 · product (above) · assumption corpus 9ddecb35 + census/decision 70453330 + source declaration 152de650 · harness 3709d7c8 · divergence declaration caf76ed8 · single refreeze 380db58c (measurement commit) · evidence 54af39a4 · docs SELF
- **CANDIDATE:** 548f5b3b… → 40263983… (105 files), frozen once at a2af56e4 · CACHE_VERSION 105 → 106 (served → rejected + formation of served envelopes; fingerprint b1714b566e25c912 unchanged) · schema mirrors byte-identical
- **EVIDENCE_COMMIT_ROLE:** 54af39a4 (browser, occlusion, playback, crops, T3, gates at 380db58c)
- **CLASSIFICATION:** FORMATION_FOUNDATION_INCOMPLETE
- **PRODUCT_CHANGED:** YES
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/evaluation/geometry/runs/w14-generic-formation-assumption/REPORT.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/runs/w14-generic-formation-assumption/
- **PASS:** one shape-class completion pass for compiler and LLM programs (six families + served gold p1, p2 COMPLETED; browser role coverage 12/12; playback 12/12 × 19; triangular pyramid and prism filmstrips show height/top face/lateral edges as separate steps) · AST guard: no family branch · trust policy (SOURCE_TEXT_MISSING unless an explicit trusted fixture) · source-length vocabulary (probe diff as registered) · NA-05 portability · T3 FULL_PRODUCT_GATE_PASS from a spaced path (pytest 6564/0, vitest 1010/1010) · product = oracle 24/24
- **CLOSED:** ISSUE-ARCH-SOURCE-LENGTH-UNLABELLED-PHRASE · ISSUE-OPS-TEST-EXTERNAL-EVIDENCE-PATH · ISSUE-ARCH-TEXTLESS-CONTRACT-UNCHECKED (opened and closed in w14)
- **OPENED:** ISSUE-EVAL-HUMAN-VISIBILITY-REGISTRY-PREDATES-S4
- **PARTIAL:** ISSUE-ARCH-FORMATION-PER-FAMILY-SEQUENCE (refused gold negative n2 stays AMBIGUOUS_TOPOLOGY; decision W14-D1)
- **OPEN (blocking merge of the branch):** ISSUE-ARCH-ASSUMPTION-CHANNEL-UNSTATED-DIMENSION (Track B STOP: ASSUMPTION_POLICY_INCOMPLETE, AC2 0/18) · human visual re-review of the w14 formation and of the four scenes S4 changed
- **FULL_PRODUCT_SUITE:** FULL_PRODUCT_GATE_PASS (T3 at 380db58c, path with a space)
- **PUSH / MERGE:** NO / NO
- **CORRECTED_BY:** NONE
- **CORRECTS:** W12_PEDAGOGICAL_TIMELINE_AND_SOURCE_GROUNDING_CLOSURE (answers its human review W12-H1…H4)
- **NEXT_ACTION_AT_TIME:** COMPLETE_SHAPE_CLASS_FORMATION (starts with user decision W14-D1)
- **FINAL_DECISION:** FORMATION_FOUNDATION_INCOMPLETE







### WAVE_ID = W15_SOURCE_CONSTRAINT_AND_ASSUMPTION_CLOSURE
- **DATE:** 2026-10-02 → 2026-10-03
- **START_BASE:** 4f6a0ab6
- **CODE_COMMIT_OR_NONE:** 5dd8e7f5 (solid_faces bijection) · cf57332b (constraint reader + assumption certificate) · 6fa6e582 (fully-read counterexample rule) · 2305f072 (right-angle phrasings, polyhedral scope) · a1b17fef (symbol-key binding) · 45d014b0 (route wiring, U3) · 33b11a79 (U5) · 8239a2a4 (section fill) · 0579d559 (CACHE_VERSION 107) · d41176f2 (review simplifications) · 909a3a2d (section fill without depth test) · 41a26f11 (final-review soundness fix; last product commit)
- **COMMITS:** Track B investigation 7b9e250b · red tests ac6687ae · scope registration and corpus labels 5f750bd6 (+ gold-row source f6cbf355) · census rounds ae64946b, d68c4f79, bb0740f7 · W15B labels 14d5e786 · fault injections 51e4177e, fbabbc2e, 5a54bfc6, bb0740f7 · harness 092df243, e59712a1 · freezes c1638891, e5b88647, c57ebd1b (measurement commit) · evidence 751169dd (superseded), 23cc880a · docs SELF
- **CANDIDATE:** 40263983… → b3b7eb79… (107 files), frozen three times (d41176f2 and 909a3a2d → intermediate aaa5b5bd…; 41a26f11 → b3b7eb79…) · CACHE_VERSION 106 → 107 (served → rejected; fingerprint b1714b566e25c912 unchanged) · schema mirrors byte-identical
- **EVIDENCE_COMMIT_ROLE:** 23cc880a (browser, occlusion, playback, crops, T3, gates at c57ebd1b)
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **PRODUCT_CHANGED:** YES
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/evaluation/geometry/runs/w15-assumption-closure/REPORT.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/runs/w15-assumption-closure/
- **PASS:** assumption certificate wired (stage `assumption`): AC2 18/18 PROVEN_SAFE (8 C0, 10 C1) and served, both W12 probes refused, AC1 3/3 and adversarial 7/7 refused, W14's 11 false counterexamples → 0, census round 3 SHIP (§9 a–f), fault injections FI2–FI14 caught (FI1 masked as registered), 0 strict xfail left · SECTION_FILL_DISTINGUISHABLE 33.9/25.3 desktop, 33.8/25.9 mobile (thresholds 20/12, 3) · occlusion HUMAN_REVIEW_PENDING (U2; product = oracle 24/24) · playback 12/12 × 19 · browser 12/12 positive + 36/36 negative (three kinds, own codes) · T3 FULL_PRODUCT_GATE_PASS from a spaced path (pytest 6757/0, vitest 1017/1017, demo 5/5, crash surface 6/6)
- **CLOSED:** ISSUE-ARCH-FORMATION-PER-FAMILY-SEQUENCE (decision W15-D1: n2 is a correctly refused program, outside the enforced formation set)
- **OPENED:** ISSUE-ARCH-SHAPE-CONSTRAINT-VOCABULARY-COVERAGE · ISSUE-ARCH-ASSUMPTION-C0-PLANE-EQUATION-ENTITY · ISSUE-EVAL-ASSUMPTION-GATE-UNTESTED-GUARDS
- **PARTIAL:** ISSUE-ARCH-ASSUMPTION-CHANNEL-UNSTATED-DIMENSION (closed inside the polyhedral vocabulary; recorded, not refused, outside it — U3)
- **OPEN (blocking merge of the branch):** human visual review of the four W14-changed scenes (`ISSUE-EVAL-HUMAN-VISIBILITY-REGISTRY-PREDATES-S4`, HUMAN_REVIEW_PENDING) and of the section fill
- **FULL_PRODUCT_SUITE:** FULL_PRODUCT_GATE_PASS (T3 at c57ebd1b, path with a space)
- **PUSH / MERGE:** NO / NO
- **CORRECTED_BY:** NONE
- **CORRECTS:** W14_GENERIC_FORMATION_AND_ASSUMPTION_FOUNDATION (Track B root causes and gate; W14-D1 settled by W15-D1)
- **NEXT_ACTION_AT_TIME:** HUMAN_VISUAL_REVIEW_OF_ASSUMPTION_CLOSURE_EVIDENCE
- **FINAL_DECISION:** READY_FOR_HUMAN_VISUAL_REVIEW

### WAVE_ID = W16_PREMERGE_SOUNDNESS_AND_VISUAL_EVIDENCE_CLOSURE
- **DATE:** 2026-10-03
- **START_BASE:** 8a339d17
- **CODE_COMMIT_OR_NONE:** 24161657 (plane-equation literals bound to their own text plane) · 93d4ec69 (goal clauses never premises) · 29da8e5a (section fill under the solid edges, frontend/src) · 2ec02b3a (CACHE_VERSION 108) · 6b120036 (primed plane names; last product commit)
- **COMMITS:** registration 6ed110f6 · red tests 6d015112 · phase-1 probe and corpus dea0ad91 · harness 1d782bd8, 85e73394 · drivers 00f0981d · census round 1 + fault injections cd3a0efa · cache proof e42bdd8f · freeze 1 55cde06e · W16B red 2dc55f1b + corpus 681c34cf · FA3/FA4 + census round 2 7695b967, f3f9836a · freeze 2 7f3658b0 (measurement commit) · evidence 705970dd
- **CANDIDATE:** b3b7eb79… → 9bb0aaa7… (107 files), frozen twice (2ec02b3a → intermediate 8d14469b…; 6b120036 → 9bb0aaa7 after the primed-name fix found by the pre-evidence self-review) · CACHE_VERSION 107 → 108 (served → rejected; fingerprint b1714b566e25c912 unchanged) · schema mirrors byte-identical · model surface unchanged
- **EVIDENCE_COMMIT_ROLE:** 705970dd (browser, occlusion, playback, sheets, T3, gates at 7f3658b0)
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **PRODUCT_CHANGED:** YES
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/evaluation/geometry/runs/w16-premerge-closure/REPORT.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/runs/w16-premerge-closure/
- **PASS:** plane binding: 7/7 wrong-entity programs refused (5 were served from C0 before W16), 9/9 valid bindings C0 · goal clauses: 7/7 goal-as-premise programs refused (all served before W16), 4/4 hypothesis rows C1 · four guards tested from valid specs, FG1–FG4 caught · census round 2 SHIP, AC2 18/18 PROVEN_SAFE, 0 status changes on W14/W15/W15B, 0 valid cases newly refused · fault injections backend 13/13, frontend 4/4 · SECTION_FILL_UNDER_EDGES (rho ≤ 0.485 < 1, edge contrast ≥ 35.5) and SECTION_FILL_DISTINGUISHABLE 34.20/34.11 desktop, 34.19/33.74 mobile (W15 thresholds unchanged) · 6 sheets × 6 refusal panels, a missing or blank panel fails the builder · browser 12/12 + 36/36, occlusion HUMAN_REVIEW_PENDING (four scenes as w15), playback 12/12 × 19/19
- **CLOSED:** ISSUE-ARCH-ASSUMPTION-C0-PLANE-EQUATION-ENTITY · ISSUE-EVAL-ASSUMPTION-GATE-UNTESTED-GUARDS
- **OPENED:** ISSUE-ARCH-ASSUMPTION-CONSTRUCTION-RELATION-NOT-SOURCE-BOUND (declared limit A′, strict xfail) · ISSUE-ARCH-GROUNDING-GOAL-CLAUSE-AS-DATUM · ISSUE-ARCH-SECTION-FILL-OPAQUE-AUXILIARY-LINES
- **OPEN (blocking merge of the branch):** human visual review (W16-H1): the four W14-changed scenes (`ISSUE-EVAL-HUMAN-VISIBILITY-REGISTRY-PREDATES-S4`, HUMAN_REVIEW_PENDING), the section fill under the edges, the refusal panels
- **FULL_PRODUCT_SUITE:** FULL_PRODUCT_GATE_PASS (T3 at 7f3658b0, path with a space; pytest 6854 passed / 0 failed / 1 xfailed = limit A′)
- **PUSH / MERGE:** NO / NO
- **CORRECTED_BY:** NONE
- **CORRECTS:** W15_SOURCE_CONSTRAINT_AND_ASSUMPTION_CLOSURE (two certificate soundness gaps, the fill drawn over the edges, the blank refusal cells of the w15 sheets)
- **NEXT_ACTION_AT_TIME:** HUMAN_VISUAL_REVIEW_OF_PREMERGE_CLOSURE_EVIDENCE
- **FINAL_DECISION:** READY_FOR_HUMAN_VISUAL_REVIEW

### WAVE_ID = W17_OPERATION_BINDING_AND_ON_SCENE_ANNOTATIONS
- **DATE:** 2026-10-03 / 2026-10-04
- **START_BASE:** dd6e86b0
- **CODE_COMMIT_OR_NONE:** 2678b363 (operation binding) · 0b71502b (goal-only givens, refusal causes) · ce9a4c1f (group-step label) · 8e002028 (annotation binding) · fa5f8382 (labels and chips, frontend/src) · 2c7d4134, 240ecba5, dbb38b95 (label placement and refusal card, frontend/src) · fadfd10e (CACHE_VERSION 109) · add4afb0 (ponytail simplifications) · d3817d5f (final-review fix; last product commit)
- **COMMITS:** registration bce0b7bb · red tests 288f3616 · reconciliation d7c26405 · harness 4d9eacfb, ca6c4107 · fault injections 239efc05, d4ca6ea9 · census round 1 + cache proof 37043376 · freeze 1 4706eb0b · intermediate measurement c5592c1a + evidence f07b0d24 · final-review red 01b0c27c · census round 2 3cbe3a1f · fault-injection table 6d52ab2f · freeze 2 921015b6 · intermediate evidence kept apart 83f101e4 · fix-pass logs a20b76f1 · failed attempt 1 kept apart c14edd07 · harness fix 4e07548e · frontend fault-injection table 99925723 (measurement commit) · evidence 781c14e5
- **CANDIDATE:** 9bb0aaa7… → d63d6fd4… (109 files), frozen twice (add4afb0 → intermediate d4a24eba…; d3817d5f → d63d6fd4 after the final-review fix) · CACHE_VERSION 108 → 109 (served → rejected; fingerprint b1714b566e25c912 unchanged) · schema mirrors byte-identical · model surface unchanged
- **EVIDENCE_COMMIT_ROLE:** 781c14e5 (browser, occlusion, playback, sheets, T3, gates, frontend fault injections at 99925723)
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **PRODUCT_CHANGED:** YES
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/evaluation/geometry/runs/w17-operation-annotations/REPORT.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/runs/w17-operation-annotations/
- **PASS:** operation binding: A′ refused CONSTRUCTION_NOT_TEXT_BOUND (served with area 9 before W17; the text gives 16), O1–O10 as registered, the W16 strict xfail passes · goal-only givens: G1, G3, G4 refused at grounding; G2, G5–G7 served · refusal causes: 20/20 negative fixtures reconciled, only SOURCE asks to fix the text · on-figure labels: ≤ 24 px from the anchor (max 16.97 px), 72/72 steps equal the oracle, toggles change only labels 12/12, causal restore byte-identical 12/12 · census round 2 SHIP, AC2 18/18, A2b the only gate change since W16 round 2 · fault injections backend 23/23, frontend 18/18 · browser 12/12 + 40/40 + 2/2, occlusion HUMAN_REVIEW_PENDING (four scenes as w15/w16), playback 12/12
- **CLOSED:** ISSUE-ARCH-ASSUMPTION-CONSTRUCTION-RELATION-NOT-SOURCE-BOUND (for section cuts) · ISSUE-ARCH-GROUNDING-GOAL-CLAUSE-AS-DATUM
- **OPENED:** ISSUE-ARCH-CONSTRUCTION-RELATION-BEYOND-SECTION-CUT · ISSUE-ARCH-CUT-PLANE-BY-POINT-AND-PARALLEL · ISSUE-ARCH-ANNOTATION-UNANCHORED-QUANTITIES
- **OPEN (blocking merge of the branch):** human visual review (W17-H1, carrying W16-H1): on-figure labels and chips, W17 refusal panels, group-step names, the four W14-changed scenes (`ISSUE-EVAL-HUMAN-VISIBILITY-REGISTRY-PREDATES-S4`, HUMAN_REVIEW_PENDING), the section fill under the edges, the refusal panels
- **FULL_PRODUCT_SUITE:** FULL_PRODUCT_GATE_PASS (T3 at 99925723, path with a space; pytest 6936 passed / 0 failed / 0 xfailed)
- **PUSH / MERGE:** NO / NO
- **CORRECTED_BY:** NONE
- **CORRECTS:** W16_PREMERGE_SOUNDNESS_AND_VISUAL_EVIDENCE_CLOSURE (declared limit A′ closed for section cuts; goal clauses no longer read as data by grounding outside the polyhedral scope; the w16 cube "cạnh 4" refusal image traced to a fixture-generator defect)
- **NEXT_ACTION_AT_TIME:** HUMAN_VISUAL_REVIEW_OF_OPERATION_ANNOTATION_EVIDENCE
- **FINAL_DECISION:** READY_FOR_HUMAN_VISUAL_REVIEW

### WAVE_ID = W18_CONSTRUCTION_BINDING_AND_FOCUSED_ANNOTATIONS
- **DATE:** 2026-10-04
- **START_BASE:** 0ec2bbbb
- **CODE_COMMIT_OR_NONE:** 84ce7b70 (construction binding, route stage, learner messages, refusal-card label) · f2a040f9 (label roles, same-subject merge, exact distance witness, S(T)) · b6868e19 (focused labels, one explanation place, witness layer; frontend/src) · 1e8c5658 (CACHE_VERSION 110) · 7a06ee47 (ponytail cuts; last product commit)
- **COMMITS:** registration + corpus labels c479f377 · red reproductions f3edd903, bb9f7004 · Phase 1 reproduction d5b0a555 · census + reproduction after 00654627 · red annotations 9844f83e · P1 lock 3b0d6989 · red frontend 21981005 · harness 91f750e6 · fault-injection drivers 256fdc8e, 83a0e0c1 · oracle same_as 32f10f69 · fault injections run 2 1a20b74c · cache lock 5cfb53a1 · fixture pin 72be45ce · freeze 8caa8307 · harness blind spots 1d8dfc6f · attempt 1 kept apart 0ca3accf (measurement commit) · FW1 retarget b5ab4656 · evidence 4a9db1ff
- **CANDIDATE:** d63d6fd4… → d3b4cab9… (110 files), frozen once (7a06ee47) · CACHE_VERSION 109 → 110 (served → rejected; lock 5cfb53a1; fingerprint b1714b566e25c912 unchanged) · schema mirrors byte-identical · model surface unchanged
- **EVIDENCE_COMMIT_ROLE:** 4a9db1ff (browser, occlusion, playback, sheets, T3, gates, frontend fault injections run 2 at 0ca3accf)
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **PRODUCT_CHANGED:** YES
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/evaluation/geometry/runs/w18-binding-focus/REPORT.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/runs/w18-binding-focus/
- **PASS:** construction binding: B5, B7, B9, B11, B13 served before W18 (3√6 for 9, 6√2 for 3√6, 3√2 for 2√3) and B2, B4 refused only by the coordinate invariant; after: the seven reachable MUST_REFUSE rows refused at construction_binding with cause CONSTRUCTION and both relations named · census SHIP, AC2 18/18, no served row of W14–W17C refused, W18 23/23 as registered · focused labels: compact default 12/12, per-step 72/72, selection 58/58, one formula region 10/10 collapsed + 10/10 open, show-all isolation 12/12, ≤ 24 px (max 16.97) · witness 2/2 + 2/2 · dash under highlight 72/72 steps · fault injections backend 12/12 (run 3), frontend 12/12 (run 2: 8 unit + 4 browser; run 1 found three browser-harness blind spots, fixed in 1d8dfc6f)
- **CLOSED:** ISSUE-ARCH-CONSTRUCTION-RELATION-BEYOND-SECTION-CUT (partially: midpoints and projections)
- **OPENED:** ISSUE-ARCH-CONSTRUCTION-BINDING-VOCABULARY · ISSUE-ARCH-SCOPE-GATE-LENGTH-CLUE
- **OPEN (blocking merge of the branch):** human visual review (W18-H1, carrying W17-H1 and W16-H1): compact default, "Hiện tất cả", selection with its chain, the inspector, the collapsed solution, distance witnesses, W18 refusal panels, the four W14-changed scenes (`ISSUE-EVAL-HUMAN-VISIBILITY-REGISTRY-PREDATES-S4`, HUMAN_REVIEW_PENDING)
- **FULL_PRODUCT_SUITE:** FULL_PRODUCT_GATE_PASS (T3 at 0ca3accf, path with a space; pytest 7001 passed / 0 failed / 0 xfailed)
- **PUSH / MERGE:** NO / NO
- **CORRECTED_BY:** NONE
- **CORRECTS:** W17_OPERATION_BINDING_AND_ON_SCENE_ANNOTATIONS (constructions other than section cuts were not checked against the text: midpoints and projections now are)
- **NEXT_ACTION_AT_TIME:** HUMAN_VISUAL_REVIEW_OF_CONSTRUCTION_BINDING_AND_FOCUS_EVIDENCE
- **FINAL_DECISION:** READY_FOR_HUMAN_VISUAL_REVIEW

### WAVE_ID = W19_DOCS_REORGANIZATION_AND_RESEARCH_EVIDENCE_CURATION
- **DATE:** 2026-10-04
- **START_BASE:** 6d0e6321
- **CODE_COMMIT_OR_NONE:** NONE (product). Docs tooling: `audit_docs_layout` + `NAVIGATION_DOCS` in `backend/scripts/audit_docs_information_architecture.py`; tests inv_23, inv_24, fi_17, fi_18; one doc path in `test_curriculum_coverage.py`
- **COMMITS:** a5c2e6f2 (structure + migration) · a44631a9 (claim map, hubs, closed docs root) · documentation commit (state, report, handoff)
- **CANDIDATE:** d3b4cab96c69a09f… unchanged (`--verify` exit 0) · CACHE_VERSION 110 unchanged (lock `--verify` exit 0) · model surface unchanged
- **EVIDENCE_COMMIT_ROLE:** a5c2e6f2 · a44631a9 · documentation commit
- **CLASSIFICATION:** DOCS_REORGANIZED_AND_VERIFIED
- **PRODUCT_CHANGED:** NO
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/evaluation/geometry/runs/w19-docs-organization/REPORT.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/runs/w19-docs-organization/
- **PASS:** 65 files moved by `git mv` (33 to `docs/research/`, 32 to `docs/legacy/`; 55 byte-identical, 10 with recorded link/pointer changes) and the CURRENT_STATE development log (5 388 lines) moved verbatim; one claim-evidence map (26 rows); docs root closed (198 = 11 canonical + 7 project + 180 catalogued); frozen evidence identical to 6d0e6321 (8 439 `docs/evaluation` files + 192 frozen docs, digest 03447263…); living-doc links: 0 broken introduced, 1 pre-existing (annotated); old-path consumers 0 in living docs, code, tests, tools
- **CLOSED:** —
- **OPENED:** ISSUE-ARCH-CONSTRUCTION-BINDING-LITERAL-TARGET (blocks merge) · ISSUE-DOCS-HISTORICAL-REPORTS-AT-DOCS-ROOT · ISSUE-OPS-TMP-LEFTOVERS-UNVERIFIED · ISSUE-OPS-TEST-SUITE-WRITES-FROZEN-EVIDENCE
- **OPEN (blocking merge of the branch):** W18 human visual review (NOT_APPROVED); ISSUE-ARCH-CONSTRUCTION-BINDING-LITERAL-TARGET
- **FULL_PRODUCT_SUITE:** T3 not run (docs-only wave; product code unchanged, candidate verify). Backend pytest full in a detached clean worktree of the final tree: 7005 passed / 0 failed (1 skipped, 2 deselected) on tree 6b926494 (temporary commit object 3de7bda0, not on any branch; verification records added afterwards); main tree with uncommitted W19 docs: 7003 passed / 2 failed (both read `git status` and require that only the user's favicon is dirty); vitest full 1058/1058
- **PUSH / MERGE:** NO / NO
- **CORRECTED_BY:** NONE
- **CORRECTS:** NONE
- **NEXT_ACTION_AT_TIME:** NEXT_FAMILY_SLICE_WITH_DECIDED_UI_CHANGES
- **FINAL_DECISION:** DOCS_REORGANIZED_AND_VERIFIED

### WAVE_ID = W20_REPOSITORY_CLEANUP_AND_PREMERGE_CORRECTNESS_CLOSURE
- **DATE:** 2026-10-04 → 2026-10-05
- **START_BASE:** 2cb4ed8c
- **CODE_COMMIT_OR_NONE:** 65c90bde (construction binding §17: `DEFINED_BY_COORDINATES`, `CONSTRUCTION_REPLACED_BY_COORDINATES`) · bedb1040 (CACHE_VERSION 110 → 111) · a4f771b3 (comments only, self-review F1). Tooling/tests: 4e647861 + 654beda3 (`run_reconciliation(out_dir)`), 72 new tests
- **COMMITS:** f0edcd11 · 65c90bde · bedb1040 · ac241a8d · 4e647861 · 8b6a1a3a · c43862da · a36f3e97 · 31716373 · 654beda3 · a4f771b3 · 908a1f2c · 5fbb397b · aa036c42 · documentation commit (state, report, handoff)
- **CANDIDATE:** d3b4cab96c69a09f… → 2a15102b… (intermediate, bedb1040) → 27c31de6dcd7708e… (a4f771b3), two freezes in clean detached worktrees, `--verify` exit 0 · CACHE_VERSION 111 (lock `--verify` exit 0) · model surface unchanged (fingerprint b1714b566e25c912…)
- **EVIDENCE_COMMIT_ROLE:** f0edcd11 (labels + before probe, before any fix) · 8b6a1a3a (after probe, census, fault injections) · 31716373 (cleanup inventory + deletion log) · documentation commit (verification logs, report, handoff)
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **PRODUCT_CHANGED:** YES — served → rejected for a W18 §16.1 relation target defined by coordinates (directly or through an alias chain)
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/evaluation/geometry/runs/w20-cleanup-premerge/REPORT.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/runs/w20-cleanup-premerge/
- **PASS:** probe through `run_pipeline` with labels registered before the fix 20/27 → 26/27 (the remaining row is refused by the domain gate, recorded before the fix); census 179 rows of W14–W18, no route change, SHIP (AC2 18/18); 527 stored programs scanned for the literal-then-construct pattern: one (the W20 row itself); fault injections 10/10 caught, 2 defense-in-depth injections not caught by design; frozen reconciliation folder never written (main-tree full run, git status identical); 64 cleanup deletions with mechanical proof, 0 living references
- **CLOSED:** ISSUE-ARCH-CONSTRUCTION-BINDING-LITERAL-TARGET · ISSUE-OPS-TEST-SUITE-WRITES-FROZEN-EVIDENCE
- **OPENED:** ISSUE-OPS-DOCS-FAULT-INJECTION-TESTS-WRITE-LIVING-DOCS (ISSUE-OPS-TMP-LEFTOVERS-UNVERIFIED partial: 8 of 212 entries deleted)
- **OPEN (blocking merge of the branch):** W18 human visual review (NOT_APPROVED) only
- **FULL_PRODUCT_SUITE:** T3 `frontend/scripts/full-gate.mjs` from 'D:/tmp/w20 space/algo-sim' (clean detached worktree) at 5fbb397b: FULL_PRODUCT_GATE_PASS — pytest 7077 passed / 0 failed / 1 skipped / 2 deselected; vitest 1058/1058; typecheck + build; demo; crash surface 6/6 · gates PASS (candidate + cache verify, schema ×2 identical, LLM_ONLY, model surface 0 files, 0/181 historical reports changed, docs audit PASS, node harness 70 + 2 skipped, 0 fail)
- **PUSH / MERGE / BRANCH_DELETION:** NO / NO / NO (no visual approval)
- **CORRECTED_BY:** COMPLETE_DOCS_CLEANUP_AND_CUBOID_BRANCH_ACCEPTANCE (scope note only: W20 was a correctness closure plus a bounded cleanup — mechanical duplicates, rules, temp files; the full docs review is the run cuboid-final-review; W20 results unchanged)
- **CORRECTS:** NONE (amendment §17 carries an erratum for the "§16.5" citations of earlier W20 commits, logs and outputs, which stay as they are)
- **NEXT_ACTION_AT_TIME:** NEXT_FAMILY_SLICE_WITH_DECIDED_UI_CHANGES (merge waits for W18-H1)
- **FINAL_DECISION:** READY_FOR_HUMAN_VISUAL_REVIEW

### WAVE_ID = COMPLETE_DOCS_CLEANUP_AND_CUBOID_BRANCH_ACCEPTANCE
- **RUN_ID:** cuboid-final-review (closing run of the work cuboid-visual-semantic-closure; no wave number, `docs/evaluation/RUN_NAMING.md`)
- **DATE:** 2026-10-05
- **START_BASE:** 4048ff83
- **CODE_COMMIT_OR_NONE:** 284a9bfa (refusal card of §17: message built from `reason_subjects`, no resend promise; card label "chưa kiểm chứng được phép dựng" from `reason_code`). Tooling: fac2769e (focused browser check of the refusal card)
- **COMMITS:** 42dd1af5 · 3f8127fd · 284a9bfa · fac2769e · 6ec40806 · a1c53cdb · documentation commit · final docs-gate log commit
- **CANDIDATE:** 27c31de6dcd7708e… → b2d4187a78ed8bf6… (284a9bfa), one freeze in a clean detached worktree, `--verify` exit 0 · CACHE_VERSION 111 kept (row proof, 6ec40806) · model surface unchanged (fingerprint b1714b566e25c912)
- **EVIDENCE_COMMIT_ROLE:** 42dd1af5 (docs inventory, verbatim history split, cleanup log) · 284a9bfa (red and green logs) · 6ec40806 (cache proof) · a1c53cdb (refreeze, pre-freeze log) · documentation commit (T3, gates, browser check, inventories before/after, report, handoff)
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **PRODUCT_CHANGED:** YES — learner-facing only: the §17 refusal says the construction is unverified (not mismatched); routes unchanged
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/evaluation/geometry/runs/cuboid-final-review/REPORT.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/runs/cuboid-final-review/
- **PASS:** docs: 8812 files classified, 119 blocks (2960 lines) of 7 living docs moved verbatim to `docs/legacy/` (split `--verify` OK), living docs 0 dead links and 0 machine-local links, 0 tracked files deleted, 0/181 catalogued reports changed; wave numbering per work in RUN_NAMING; refusal card TDD (backend 5 red → green, frontend 1 red → green) and browser 12/12 (desktop + mobile, three new-code cases and three controls)
- **CLOSED:** NONE (ISSUE-DOCS-HISTORICAL-REPORTS-AT-DOCS-ROOT → INTENDED_LIMITATION)
- **OPENED:** ISSUE-OPS-T1-DOMAIN-SCRIPTS-STALE · ISSUE-DOCS-INVARIANT-ENFORCEMENT-POINTERS-STALE
- **OPEN (blocking merge of the branch):** W18 human visual review (NOT_APPROVED) and the new §17 refusal cards
- **FULL_PRODUCT_SUITE:** T3 `frontend/scripts/full-gate.mjs` from 'D:/tmp/cfr space/algo-sim' (clean detached worktree) at a1c53cdb: FULL_PRODUCT_GATE_PASS — pytest 7079 passed / 0 failed / 1 skipped / 2 deselected; vitest 1061/1061; typecheck + build; demo 5/5; crash surface 6/6
- **PUSH / MERGE / BRANCH_DELETION:** NO / NO / NO (no visual approval)
- **CORRECTED_BY:** CUBOID_INVARIANT_RECONCILIATION_AND_MERGE_HANDOFF (count only: 24 rows of ARCHITECTURE_MAP §5 had dead pointers, not 22; results unchanged)
- **CORRECTS:** W20_REPOSITORY_CLEANUP_AND_PREMERGE_CORRECTNESS_CLOSURE (scope note only: W20's cleanup was bounded; the full docs review is this run)
- **NEXT_ACTION_AT_TIME:** NEXT_FAMILY_SLICE_WITH_DECIDED_UI_CHANGES on a new branch from the updated main, starting at W1 (merge waits for the visual review)
- **FINAL_DECISION:** READY_FOR_HUMAN_VISUAL_REVIEW

### WAVE_ID = CUBOID_INVARIANT_RECONCILIATION_AND_MERGE_HANDOFF
- **RUN_ID:** cuboid-acceptance (acceptance package of the work cuboid-visual-semantic-closure; no wave number, `docs/evaluation/RUN_NAMING.md`)
- **DATE:** 2026-10-05
- **START_BASE:** 903e874c
- **CODE_COMMIT_OR_NONE:** NONE — documentation only
- **COMMITS:** documentation commit · final log commit
- **CANDIDATE:** b2d4187a78ed8bf6… unchanged (no product byte changed since 284a9bfa) · CACHE_VERSION 111 unchanged · LLM_ONLY
- **EVIDENCE_COMMIT_ROLE:** documentation commit (reconciliation JSON, check scripts, living docs) · final log commit (invariant checks and docs gates in a clean detached worktree)
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **PRODUCT_CHANGED:** NO
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/evaluation/geometry/runs/cuboid-acceptance/REPORT.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/runs/cuboid-acceptance/
- **PASS:** 24 rows of ARCHITECTURE_MAP §5 reconciled to the assertion (9 CURRENT_ENFORCED, 1 CURRENT_UNVERIFIED, 14 HISTORICAL_NOT_APPLICABLE, 0 VIOLATED); pointer cells name only live files (39/39 rows, 0 missing); user decisions H-CFR-1/2/3 recorded
- **CLOSED:** ISSUE-DOCS-INVARIANT-ENFORCEMENT-POINTERS-STALE
- **OPENED:** ISSUE-OPS-LIVE-OPT-IN-NOT-UNIFORM
- **OPEN (blocking merge of the branch):** the human visual review only (checklist: HANDOFF.md §1 of the run)
- **FULL_PRODUCT_SUITE:** not re-run (no product byte changed); last T3 at a1c53cdb (cuboid-final-review): FULL_PRODUCT_GATE_PASS
- **PUSH / MERGE / BRANCH_DELETION:** NO / NO / NO (no explicit visual approval)
- **CORRECTED_BY:** NONE
- **CORRECTS:** COMPLETE_DOCS_CLEANUP_AND_CUBOID_BRANCH_ACCEPTANCE (count only: 24 invariant rows, not 22)
- **NEXT_ACTION_AT_TIME:** human visual review; after approval merge into main without a PR, push, delete the branch; then a new work on a new branch from the updated main starting at W1 (proposal, not chosen: regular-square-pyramid-w01)
- **FINAL_DECISION:** READY_FOR_HUMAN_VISUAL_REVIEW

### WAVE_ID = CUBOID_ACCEPTANCE_AND_DIRECT_MAIN_INTEGRATION
- **RUN_ID:** cuboid-merge (review package and integration of the work cuboid-visual-semantic-closure; no wave number)
- **DATE:** 2026-10-05
- **START_BASE:** 37b23f04
- **CODE_COMMIT_OR_NONE:** NONE — documentation only
- **COMMITS:** documentation commit · final log commit
- **CANDIDATE:** b2d4187a78ed8bf6… unchanged · CACHE_VERSION 111 · LLM_ONLY
- **EVIDENCE_COMMIT_ROLE:** documentation commit (review package, fixture transfer) · final log commit (gates in a clean detached worktree)
- **CLASSIFICATION:** MERGED_AND_PUSHED
- **PRODUCT_CHANGED:** NO
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/evaluation/geometry/runs/cuboid-merge/REVIEW.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/runs/cuboid-merge/
- **PASS:** w18 visual evidence transferred to candidate b2d4187a (fixtures regenerated offline: old run byte-exact to the measured manifest; 32/32 current fixtures differ only in two identity fields; frontend diff confined to the refusal card); 0 new captures; review package A–F
- **CLOSED:** NONE
- **OPENED:** NONE
- **OPEN (not blocking):** F1–F5 deferred by the user and still open; reviewed hidden-line registry layer (ISSUE-EVAL-HUMAN-VISIBILITY-REGISTRY-PREDATES-S4)
- **FULL_PRODUCT_SUITE:** not re-run (no product byte changed); last T3 at a1c53cdb: FULL_PRODUCT_GATE_PASS
- **PUSH / MERGE / BRANCH_DELETION:** YES (a9492ee9..c282a5f3, no force) / FAST_FORWARD (no PR) / LOCAL DELETED (no remote branch) — approval: runs/cuboid-merge/APPROVAL.md
- **CORRECTED_BY:** NONE
- **CORRECTS:** NONE
- **NEXT_ACTION_AT_TIME:** user answers ACCEPTED or NEEDS_CHANGES for A–F; on approval fast-forward main, push, delete the branch; then SELECT_AND_START_NEXT_FAMILY_W01
- **FINAL_DECISION:** MERGED_AND_PUSHED

### WAVE_ID = REGULAR_SQUARE_PYRAMID_AND_PEDAGOGICAL_UI
- **RUN_ID:** regular-square-pyramid-w01 (task regular-square-pyramid, wave W1)
- **DATE:** 2026-10-05
- **START_BASE:** 38d41588
- **CODE_COMMIT_OR_NONE:** 3bdada32 (regular square pyramid: reader, C1 template T7, centre binding, measured height, given labels) · ae9c72a5 + b2d224f6 (ROADMAP §0.1 UI) · 98e2b8f7 (volume formula height selection) · 9d66c603 (scope clue "độ dài") · de5b2331 (CACHE_VERSION 111 → 112) · ad7172ab (T7 reads lateral edges named by a segment — final self-review)
- **COMMITS:** ab98a2df (README) · e537dbd9 (registration) · product commits above · c37b2cc4, 3ad9442f, 1310658b, ed37f9fa (harness) · 5aaf11ee (refreeze) · 025bbff4 (evidence) · living docs and state commits
- **CANDIDATE:** b2d4187a… → 4629c3e8… (intermediate, de5b2331) → 5234c37e… (ad7172ab, after the final self-review fix); two freezes, clean detached worktrees · CACHE_VERSION 112 · LLM_ONLY
- **EVIDENCE_COMMIT_ROLE:** 025bbff4 (browser, occlusion, playback, images at ed37f9fa) · transfer to 5234c37e (results/FIXTURE_TRANSFER_b5cf4503_r2.json) · state commit (T3 and identity gates at the final documentation commit)
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **PRODUCT_CHANGED:** YES
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/evaluation/geometry/runs/regular-square-pyramid-w01/REPORT.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/runs/regular-square-pyramid-w01/
- **PASS:** corpus 24/24 rows match labels registered before the corresponding change (layer 1 17/17, layer R2 7/7); browser 7/7 families (14/14 positives, 54/54 refusals, 6/6 served, 68/68 selections, quantity drawer 14/14, steps panel 14/14); occlusion pass 0 failures; playback 14/14; 68 crops, 0 oracle disagreements
- **CLOSED:** ISSUE-ARCH-SCOPE-GATE-LENGTH-CLUE
- **OPENED:** ISSUE-ARCH-DEFAULT-ROUTE-NON-POSITIVE-LENGTH-CAUSE · ISSUE-ARCH-SOURCE-LENGTH-CHAINED-EQUALITY · ISSUE-ARCH-CONSTRUCTION-BINDING-VOCABULARY PARTIAL (centre, intersection of two lines)
- **OPEN (not blocking):** four W14 scenes HUMAN_REVIEW_PENDING; F1–F5 of cuboid-merge
- **FULL_PRODUCT_SUITE:** T3 at the documentation commit from a path with a space — see the run's `diagnostics/logs/T3_FULL_GATE_*.log`
- **PUSH / MERGE / BRANCH_DELETION:** NO / NO / NOT_ATTEMPTED
- **CORRECTED_BY:** NONE
- **CORRECTS:** NONE (preregistration correction PC1 inside the run, before any browser run)
- **NEXT_ACTION_AT_TIME:** human visual review H-W1-1 (HANDOFF.md §1); on approval merge into main, push, delete the branch
- **FINAL_DECISION:** READY_FOR_HUMAN_VISUAL_REVIEW

### WAVE_ID = REGULAR_SQUARE_PYRAMID_PEDAGOGICAL_CLOSURE
- **RUN_ID:** regular-square-pyramid-w02 (task regular-square-pyramid, wave W2; cloud implementation, local acceptance)
- **DATE:** 2026-10-05
- **START_BASE:** e821b9b5 (W1 head, pushed)
- **CODE_COMMIT_OR_NONE:** 2a63da7d (labels wait for their segment) · 9f454d6b (SO via the shared formation step; volume height by an exact perpendicularity relation) · 71cf0e80 (floating steps panel) · 6ca3b35e (helper geometry, step groups, grid) · c86cf53c (text-stated length ≤ 0 ⇒ SOURCE; no machine-token fact labels) · e68fa199 (CACHE_VERSION 112 → 113) · 7a88a789, c5142f07 (self-review) · 527d642e (panel close button name) · 75a0af9a (drawers above the panel) · 70665542 (CRLF-safe CSS test; divergence declaration at CACHE_VERSION 113 — both found by T3)
- **CANDIDATE:** 5234c37e… → d3de9c44… (four freezes, same tree hash; product commit 70665542; browser evidence of 94200b50 transferred) · CACHE_VERSION 113 · LLM_ONLY
- **EVIDENCE_COMMIT_ROLE:** measurement 94200b50 (cloud) · evidence c5b39092
- **CLASSIFICATION:** CLOUD_IMPLEMENTATION_COMPLETE_LOCAL_VERIFICATION_REQUIRED
- **PRODUCT_CHANGED:** YES
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/evaluation/geometry/runs/regular-square-pyramid-w02/REPORT.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/runs/regular-square-pyramid-w02/
- **PASS:** W2 probe 14/14 (7 families × desktop + mobile); refusals 54/54; served 6/6; selections 68/68; quantity drawer 14/14; occlusion pass (0 failures); playback 14/14; 68 crops, 0 oracle disagreements, 0 duplicate owners; positives green on every gate except camera_settled_rotated_neutral (6 desktop) and cross-section causal_restore (desktop + mobile), both red at the W1 head in the cloud environment too (diagnostics/ENV_CAMERA_SETTLE_BASELINE.json) ⇒ LOCAL_VERIFICATION_REQUIRED
- **CLOSED:** —
- **PARTIAL:** ISSUE-ARCH-DEFAULT-ROUTE-NON-POSITIVE-LENGTH-CAUSE
- **OPENED:** ISSUE-ARCH-INSPECTOR-COLUMN-RESIZES-CANVAS
- **LOCAL_VERIFICATION_REQUIRED:** T3 full gate; browser gates camera_settled_rotated_neutral and cross-section causal_restore (both red at the W1 head in the cloud environment too); Windows-path node test
- **PUSH / MERGE / BRANCH_DELETION:** working branch pushed / NO / NOT_ATTEMPTED
- **CORRECTED_BY:** NONE
- **CORRECTS:** NONE (preregistration corrections PC1-W2, PC2-W2 inside the run)
- **NEXT_ACTION_AT_TIME:** local acceptance (HANDOFF.md §2, §4), human visual review H-W2-1; on approval merge into main, push, delete the branch
- **FINAL_DECISION:** CLOUD_IMPLEMENTATION_COMPLETE_LOCAL_VERIFICATION_REQUIRED

### WAVE_ID = REGULAR_SQUARE_PYRAMID_LOCAL_ACCEPTANCE
- **RUN_ID:** regular-square-pyramid-w03 (task regular-square-pyramid, wave W3; local acceptance of W2 + fixes)
- **DATE:** 2026-10-06
- **START_BASE:** fe68b4ca (cloud W2 head, fast-forwarded; 0 local commits)
- **CODE_COMMIT_OR_NONE:** 824924d7 (a measurement-only helper plane opens no geometry step; W2 gate exemptions removed — H-W2-4) · 45beaed3 (the segment whose length the problem asks for is built before the answer; CACHE_VERSION 113 → 114 — H-W2-2) · a5d233ce (scenario file pins the refrozen tree hash)
- **CANDIDATE:** d3de9c44… → 5dec4572… (one freeze at 45beaed3, de3f9ec2) · CACHE_VERSION 114 · LLM_ONLY
- **EVIDENCE_COMMIT_ROLE:** baseline at fe68b4ca 47941832 · measurement a5d233ce · evidence 0d0d1de3
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **FULL_PRODUCT_SUITE:** T3 FULL_PRODUCT_GATE_PASS at 4c0f9219 from a path with a space (pytest 7156 passed / 1 skipped, vitest 1091/1091, build, demo 5/5, crash surface 6/6); identity gates green (`diagnostics/logs/GATES_4c0f9219.log`)
- **PRODUCT_CHANGED:** YES
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/evaluation/geometry/runs/regular-square-pyramid-w03/REPORT.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/runs/regular-square-pyramid-w03/
- **PASS:** W2 as received at fe68b4ca — T3 FULL_PRODUCT_GATE_PASS, identity gates, spaced-path node test, browser 14/14 positives fully green (camera_settled_rotated_neutral and cross-section causal_restore green locally: the cloud reds were environment). At a5d233ce — suite 7/7, 14/14 positives fully green, w18_projection_line label restored, W2 probe 14/14, occlusion 0 failures (4 scenes HUMAN_REVIEW_PENDING, U2), playback with every step changing the figure and no exemption, 68 crops 0 disagreements
- **CLOSED:** —
- **OPENED:** ISSUE-ARCH-ASKED-SEGMENT-OVER-EXISTING-EDGE
- **PUSH / MERGE / BRANCH_DELETION:** NO / NO / NOT_ATTEMPTED
- **CORRECTED_BY:** NONE
- **CORRECTS:** regular-square-pyramid-w02 — PC1-W2 (lowered W18 expectation restored), the hidden-helper exemption of three gates, the cloud classification of two browser gates (environment)
- **NEXT_ACTION_AT_TIME:** human visual review (REVIEW.md, H-W2-1); user decision on H-W2-3, H-W2-5; on approval merge into main, push, delete the branch
- **FINAL_DECISION:** READY_FOR_HUMAN_VISUAL_REVIEW

### WAVE_ID = SHARED_SIMULATION_UI_CLOSURE
- **RUN_ID:** regular-square-pyramid-w04 (task regular-square-pyramid, wave W4; local)
- **DATE:** 2026-10-06
- **START_BASE:** f3db0f6f (W3 head)
- **CODE_COMMIT_OR_NONE:** ce44eb38 (segment on a solid edge yields its stroke) · 98b1ce8d (one floating-panel mechanism) · 270cae4e (narration names) · a1c17714 (canvas height, step counter in the bar) · e41b0ab1 (tree by step) · aa754cb9 (CACHE_VERSION 114 → 115) · c8c49f3c (panels never lost, tree hoist, height settles; W4 probe) · ecbe55c0 (renderer follows its container) · 53e4bec5 (lit sub-segment span not faded)
- **CANDIDATE:** 5dec4572… → 8a27a58b… (three freezes, same tree hash: d47488f6, 643b7d7a, 103494c4) · CACHE_VERSION 115 · LLM_ONLY
- **EVIDENCE_COMMIT_ROLE:** measurement 103494c4 (attempt 4) · evidence b4f924c1; attempts 1–3 kept (`MEASUREMENT_ATTEMPTS.json`)
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **FULL_PRODUCT_SUITE:** T3 FULL_PRODUCT_GATE_PASS at d6e41d80 from a path with a space (pytest 7174 passed / 1 skipped, vitest 1113/1113, build, demo, crash surface); identity gates green (`diagnostics/logs/GATES_d6e41d80.log`); T3 at 82e61f8b failed one test whose secret-witness window relied on raw-label narration (fixed in the test at d6e41d80)
- **PRODUCT_CHANGED:** YES
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/evaluation/geometry/runs/regular-square-pyramid-w04/REPORT.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/runs/regular-square-pyramid-w04/
- **PASS:** at 103494c4 — suite 7/7, 14/14 positives; W2 probe 14/14; W4 panels probe 21/21 (7 families × desktop, 1366×650, mobile); SM control (selected, only S–M lit, 0 duplicate owners); occlusion 0 failures (4 scenes HUMAN_REVIEW_PENDING, U2); playback pass; 68 crops 0 disagreements
- **CLOSED:** ISSUE-ARCH-INSPECTOR-COLUMN-RESIZES-CANVAS · ISSUE-ARCH-ASKED-SEGMENT-OVER-EXISTING-EDGE (RESOLVED, visual review pending)
- **OPENED:** —
- **PUSH / MERGE / BRANCH_DELETION:** NO / NO / NOT_ATTEMPTED
- **CORRECTED_BY:** NONE
- **CORRECTS:** NONE (W1–W3 artifacts unchanged)
- **NEXT_ACTION_AT_TIME:** human visual review (REVIEW.md R1–R10, incl. R4 mobile canvas height); on approval merge into main, push, delete the branch
- **FINAL_DECISION:** READY_FOR_HUMAN_VISUAL_REVIEW

### WAVE_ID = IMMERSIVE_SIMULATION_AND_ARCHITECTURE_SLICE
- **RUN_ID:** regular-square-pyramid-w05 (task regular-square-pyramid, wave W5; local)
- **DATE:** 2026-10-06/07
- **START_BASE:** 73bc404e (W4 head)
- **CODE_COMMIT_OR_NONE:** c15e6fab (source length reader reads chained equal segments) · 470adc3a (focused simulation mode, grouped tools, solution card removed) · 82225a7b (focused page exactly one screen tall); harness c1070389, f01df0e5
- **CANDIDATE:** 8a27a58b… → 5e1c0639… (two freezes, same tree hash: a588f8db at 470adc3a, 74c91060 at 82225a7b) · CACHE_VERSION 115 (no bump, row proof) · LLM_ONLY
- **EVIDENCE_COMMIT_ROLE:** measurement f01df0e5 (attempt 4) · evidence 3b31aa18; attempts 1–3 kept (`MEASUREMENT_ATTEMPTS.json`)
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **FULL_PRODUCT_SUITE:** T3 FULL_PRODUCT_GATE_PASS at 4123fb4f from a path with a space (pytest 7191 passed / 1 skipped, vitest 1136/1136, build, demo, crash surface); identity gates green (`diagnostics/logs/GATES_4123fb4f.log`)
- **PRODUCT_CHANGED:** YES
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/evaluation/geometry/runs/regular-square-pyramid-w05/REPORT.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/runs/regular-square-pyramid-w05/
- **PASS:** at f01df0e5 — suite 7/7, 14/14 positives; W2 probe 14/14; W4 panels probe 21/21; W05 focus probe 21/21 (7 families × desktop, 1366×650, mobile); occlusion 0 failures (4 scenes HUMAN_REVIEW_PENDING, U2); playback 14/14; 68 crops 0 disagreements
- **CLOSED:** ISSUE-ARCH-SOURCE-LENGTH-CHAINED-EQUALITY (RESOLVED)
- **OPENED:** —
- **PUSH / MERGE / BRANCH_DELETION:** NO / NO / NOT_ATTEMPTED
- **CORRECTED_BY:** NONE
- **CORRECTS:** regular-square-pyramid-w01 LABELS_R2 row R2_L1 (product_limit → served 16/3, new label layer `diagnostics/corpus/LABELS_W05.json`; W1 files unchanged)
- **NEXT_ACTION_AT_TIME:** human visual review (W5 REVIEW.md R1–R10 with the W4 package); on approval merge into main, push, delete the branch
- **FINAL_DECISION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **SUPERSEDES:** NONE
- **THESIS_USE:** IMMERSIVE_SIMULATION_AND_ARCHITECTURE_SLICE — focused simulation workspace + one source-grounding reader slice; human review NOT_APPROVED
- **AUTHORITATIVE_FILES:** `REVIEW.md` · `REPORT.md` · `HANDOFF.md` · `RUN.json` · `MEASUREMENT_ATTEMPTS.json` · `PLAN.md` · `diagnostics/TOOL_INVENTORY.md` · `diagnostics/corpus/LABELS_W05.json` · `diagnostics/cache_proof/CACHE_DECISION_W05.json` · `results/` · `images/` · `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json`
- **RUN_ID_POLICY:** TASK_WAVE (`<task-slug>-wNN`)


### WAVE_ID = REGULAR_TRIANGULAR_PYRAMID_AND_TETRAHEDRON_SLICE
- **RUN_ID:** regular-triangular-pyramid-w01 (task regular-triangular-pyramid, wave W1; local; kept on feat/regular-square-pyramid by user instruction)
- **DATE:** 2026-10-07
- **START_BASE:** e9435d67 (W5 head)
- **CODE_COMMIT_OR_NONE:** 0d4c4f8b (informatics cleanup) · 983cfc16 (T8 in the declared Q3 domain) · 82beaf62 (cross-section edge steps named by face; CACHE_VERSION 116) · df614b30 (display rotation, D1–D4) · 3487c0a7 (height marker, D2 segment, oracle world frame) · e7b92e49 (ponytail cleanup) · 1e90ca0e (camera fit fallback after the whole scene); harness 4e285690
- **CANDIDATE:** 5e1c0639… → 92c9e198… (two freezes, same tree hash: aa583ad9 at c6fd9996, 1bb11018 at 1e90ca0e) · CACHE_VERSION 116 (bump, CACHE_DECISION.json) · LLM_ONLY
- **EVIDENCE_COMMIT_ROLE:** measurement 1bb11018 (attempt 3) · evidence c08a1eed; attempts 1–2 kept (`MEASUREMENT_ATTEMPTS.json`)
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **FULL_PRODUCT_SUITE:** T3 FULL_PRODUCT_GATE_PASS at aa845902 from a path with a space (pytest 7251 passed / 1 skipped, vitest 1145/1145, build, demo 5/5, crash surface 6/6); identity gates green (`diagnostics/logs/GATES_aa845902.log`); a first T3 at d2e8a778 failed on a stale fixture-count lock (fixed in aa845902, log kept)
- **PRODUCT_CHANGED:** YES
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/evaluation/geometry/runs/regular-triangular-pyramid-w01/REPORT.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/runs/regular-triangular-pyramid-w01/
- **PASS:** at 1bb11018 — suite 8/8, 16/16 positives, 31/31 negatives; W02 16/16 (rerun alone after a harness hang); W04 24/24 (cross_section rerun alone after a page timeout at 100 % CPU); W05 24/24; occlusion pass; playback 16/16; 72 crops, 0 oracle disagreements, 0 duplicate owners; 492 images kept / 358 pruned
- **CLOSED:** —
- **OPENED:** ISSUE-ARCH-REGULAR-TRIANGULAR-RATIONAL-EDGES · ISSUE-ARCH-REGULAR-TRIANGULAR-MODEL-LAYOUT-UNMEASURED · ISSUE-ARCH-TETRAHEDRON-OUTSIDE-POLYHEDRAL-REGION · ISSUE-ARCH-MOBILE-CANVAS-WHITESPACE-AND-PANEL-SCROLL
- **PUSH / MERGE / BRANCH_DELETION:** NO / NO / NOT_ATTEMPTED
- **CORRECTED_BY:** NONE
- **CORRECTS:** regular-square-pyramid-w05 record (attempt 4 missing from MEASUREMENT_ATTEMPTS.json; node harness 91 pass + 2 skip, not 93/93) — `corrections/W05_RECORD_CORRECTION.json`; W5 files unchanged
- **NEXT_ACTION_AT_TIME:** human visual review (REVIEW.md R1–R12 with the W5/W4 packages) and a D5 option; on approval merge into main, push, delete the branch
- **FINAL_DECISION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **SUPERSEDES:** NONE
- **THESIS_USE:** regular triangular pyramid / regular tetrahedron in a declared exact domain; honest refusal outside it; human review NOT_APPROVED
- **AUTHORITATIVE_FILES:** `REVIEW.md` · `REPORT.md` · `HANDOFF.md` · `RUN.json` · `MEASUREMENT_ATTEMPTS.json` · `PLAN.md` · `diagnostics/corpus/LABELS.json` · `diagnostics/cache_proof/CACHE_DECISION.json` · `inputs/REVIEW_SET.json` · `results/IMAGE_POLICY.json`
- **RUN_ID_POLICY:** TASK_WAVE (`<task-slug>-wNN`)


### WAVE_ID = EXACT_DIMENSIONS_AND_CAPTURE_POLICY
- **RUN_ID:** exact-dimensions (task exact-dimensions; local; same branch feat/regular-square-pyramid)
- **DATE:** 2026-10-07/08
- **START_BASE:** 4ceadd55
- **CODE_COMMIT_OR_NONE:** 1c8f3cb4 (source-length reader: a number followed by an operator is not a length) · de6d3e35 (affine chart + Gram metric; T8 rational sizes) · 14892061 (capture policy, bounded browser waits, failure classes) · 0ed6332f (rename active files) · 6c89abcd (fixtures at rational sizes) · ed3ae208 (CACHE_VERSION 117); harness d4834d92, 2d62f69c (world-space measurement of chart scenes)
- **CANDIDATE:** 92c9e198… → e1927f84… (one freeze at ed3ae208, 43d354f0) · CACHE_VERSION 117 (bump, `cache/decision.json`) · LLM_ONLY
- **EVIDENCE_COMMIT_ROLE:** measurement 3bbb8052 (probes) / fe83c46e (suite, occlusion) / d51db4e2 (playback, builder) · evidence c5cae8af; attempts 1–2 failed on harness defects, kept (`diagnostics/attempt1–3/`)
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **FULL_PRODUCT_SUITE:** T3 + identity gates on a clean detached checkout of the final docs commit — `handoff.md` §2
- **PRODUCT_CHANGED:** YES
- **MODEL_REQUESTS:** 0
- **REPORT_PATH:** docs/evaluation/geometry/runs/exact-dimensions/report.md
- **ARTIFACT_PATH:** docs/evaluation/geometry/runs/exact-dimensions/
- **PASS:** regular triangular pyramid family — suite 7/7 (2 positives, 4 refusals, tetrahedron 18√2 served), scene controls 2/2, panels 3/3, focus 3/3, occlusion pass, playback 2/2, 4 crops all endpoints inside; corpus 31 rows, oracle 18/18; images created 109 → 15 for the same case, 0 deleted after capture
- **CLOSED:** ISSUE-ARCH-REGULAR-TRIANGULAR-RATIONAL-EDGES
- **OPENED:** ISSUE-ARCH-MISSING-SIZE-REASON-ON-AFFINE-CHART
- **PUSH / MERGE / BRANCH_DELETION:** NO / NO / NOT_ATTEMPTED
- **CORRECTED_BY:** NONE
- **CORRECTS:** regular-triangular-pyramid-w01 labels N5, N5b, U1–U4 and regular-square-pyramid-w01 row U3_regular_triangular (refused → served in the rational domain) — `label_corrections.json`; earlier files unchanged
- **NEXT_ACTION_AT_TIME:** human visual review (`review.md` R1–R10 with the rtp-w01 and W5/W4 packages) and a D5 option; on approval merge into main, push, delete the branch
- **FINAL_DECISION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **SUPERSEDES:** NONE
- **THESIS_USE:** exact metric from the text on an affine chart (rational sizes for the regular triangular pyramid / tetrahedron) without changing the IR or the model surface; source-side screenshot policy; human review NOT_APPROVED
- **AUTHORITATIVE_FILES:** `review.md` · `report.md` · `handoff.md` · `run.json` · `plan.md` · `labels.json` · `label_corrections.json` · `oracle.py` · `capture_counts.json` · `cache/decision.json` · `inputs/REVIEW_SET.json` · `inputs/candidate_divergence.json` · `results/`
- **RUN_ID_POLICY:** TASK_NAME (`docs/evaluation/RUN_NAMING.md`, naming policy 2026-10-07)
