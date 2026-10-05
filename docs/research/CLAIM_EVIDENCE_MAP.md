# CLAIM_EVIDENCE_MAP — tuyên bố ↔ bằng chứng ↔ giới hạn

> **Thẩm quyền duy nhất** (từ W19, 2026-10-04) cho câu hỏi: *khoá luận hoặc bài báo được nói gì, dựa trên bằng
> chứng nào, đo trên bản hệ nào, giới hạn ở đâu.* Thay ba bảng cũ — bản gốc giữ nguyên byte ở
> [`../legacy/research/`](../legacy/research/):
> [`THESIS_READINESS.md`](../legacy/research/THESIS_READINESS.md) (nhật ký tuyên bố và đính chính tới W18),
> [`CLAIM_EVIDENCE_MATRIX.md`](../legacy/research/CLAIM_EVIDENCE_MATRIX.md) (29 tuyên bố, 2026-09-09),
> [`CLAIM_TO_EVIDENCE_MAP.md`](../legacy/research/CLAIM_TO_EVIDENCE_MAP.md) (lớp bằng chứng, 2026-09-10).
>
> **Không có số mới ở đây.** Mỗi giá trị chép từ nguồn ghi ở cột *Bằng chứng*; chỗ nguồn không ghi là `UNKNOWN`.
> Chuỗi đính chính giữa các wave thuộc [`../EVIDENCE_INDEX.md`](../EVIDENCE_INDEX.md) (`CORRECTED_BY`); một wave đổi
> bằng chứng của hàng nào thì sửa hàng ấy và ghi wave ở cột *Kết quả và giới hạn*, không xoá giới hạn cũ.

## 0. Đọc trước — năm ranh giới không được vượt

1. **Test kỹ thuật không thay thực nghiệm sư phạm.** Chưa có nghiên cứu người dùng nào; tác động lên người học
   **chưa đo** (hàng G1). Hàng loạt cổng trình duyệt đo *cấu trúc* cảnh và nhãn, không đo người học hiểu gì.
2. **Replay offline không phải đánh giá provider live.** Bằng chứng live có thẩm quyền: lượt nghiệm thu cuối
   2026-09-08 (19 lượt gọi, candidate `d72db7c3…`, `CACHE_VERSION 94`) và lượt V3 hình cong 2026-09-05. Mọi wave
   w09–w19 chạy **0 lượt gọi**; chúng không nói gì về hành vi của mô hình trên bản hệ hiện tại (`d3b4cab9…`, 110).
3. **Tự động PASS không phải người duyệt chấp nhận.** Review người đã có kết luận: w09 `FAIL`, w10
   `FAIL_REQUIRES_TARGETED_PEDAGOGICAL_REPAIR`, w11 và w12 `NEEDS_CHANGES`; w14–w18 `NOT_APPROVED` (chờ duyệt). Vì
   thế **không hàng nào ở mức `HUMAN_REVIEWED`**.
4. **18 bài gold không chứng minh đúng cho mọi bài hình học.** `AC2 18/18` là kết quả trên corpus đã gắn nhãn,
   trong vùng chứng chỉ đã đăng ký. Tự rà soát còn tìm ra lỗ ngoài corpus ở w15 (`41a26f11`), w16 (`6b120036`),
   w17 (`d3817d5f`).
5. **Renderer vẽ được không có nghĩa pipeline hỗ trợ.** Scene3D vẽ được cầu, trụ, nón, thiết diện; nhưng năng lực
   **sản phẩm** do `backend/app/simulation/product_capability.py` quyết (khối cong, khối lõm, thiết diện xiên:
   `foundation_only`). Một họ chỉ "được hỗ trợ" khi đi trọn đề → analyze → chương trình → các cổng → kernel → cảnh.

## 1. Bốn mức

| mức | nghĩa |
|---|---|
| `PLANNED` | đã nêu thành việc cần làm hoặc đã đăng ký thiết kế; chưa có mã chạy |
| `IMPLEMENTED` | có mã và test đơn vị; chưa có phép đo đăng ký trước hoặc chưa đo trên đường chạy thật |
| `MEASURED` | có phép đo tự động trên đường chạy thật (live hoặc offline — ghi rõ ở cột phạm vi), artifact có băm |
| `HUMAN_REVIEWED` | một người đã duyệt bằng chứng **và chấp nhận**. Hiện **0** hàng |

## 2. Bảng

Cột *Commit/candidate đo* ghi `measurement commit / candidate / CACHE_VERSION` khi nguồn có. Cột *Dùng ở* trỏ mục
của bản thảo [`thesis/THESIS_DRAFT.md`](thesis/THESIS_DRAFT.md) (Ch. = chương), hai chương rời
[`thesis/CHAPTER_4_RESULTS_AND_DISCUSSION.md`](thesis/CHAPTER_4_RESULTS_AND_DISCUSSION.md),
[`thesis/CHAPTER_5_CONCLUSION_AND_LIMITATIONS.md`](thesis/CHAPTER_5_CONCLUSION_AND_LIMITATIONS.md), và loại bài báo ở
[`paper/PUBLICATION_READINESS_ASSESSMENT.md`](paper/PUBLICATION_READINESS_ASSESSMENT.md) §2. *"Chưa có mục"* = bằng
chứng có nhưng bản thảo (cập nhật lần cuối 2026-09-09) chưa viết tới.

### A. Kiến trúc và ranh giới R0

| ID | Tuyên bố | Phạm vi | Bằng chứng / run | Commit / candidate đo | Kết quả và giới hạn | Mức | Dùng ở |
|---|---|---|---|---|---|---|---|
| A1 | Mô hình không phán toạ độ: mọi toán hạng hình học trong IR là **tên** của vật đã dựng, cưỡng chế ở lược đồ | tuyến `LLM_ONLY`; lược đồ `semantic_program/contract.py` | lượt cuối `docs/evaluation/geometry/thesis-final-acceptance/` (`RAW_GEOMETRY_LITERAL_ATTEMPTS`); `tests/semantic_program/test_schema_sync.py` | live: `d72db7c3…` / v94 | `RAW_GEOMETRY_LITERAL_ATTEMPTS = 0`; ca `n1` thử bịa ba điểm và bị chặn (`UNANCHORED_DERIVED_ASSUMPTION`). Bảo đảm là **cấu trúc lược đồ**, không phải phép đo hành vi trên nhiều đề (9 ca) | MEASURED | Ch.3 §3.2; CHAPTER_4; bài hệ thống |
| A2 | Bài mới không cần mã mới: thêm dạng bài bằng ghép phép có sẵn | trong IR hiện có; ngoài IR ⇒ từ chối | `FINAL_SUMMARY.json` (thesis-final-acceptance); quét AST `PROBLEM_FAMILY_SPECIAL_CASES`; `tests/.../test_missing_family_roadmap.py` | live: `d72db7c3…` / v94 | `NEW_IR_OPERATIONS = 0`, `NEW_MEMORY_TYPES = 0`, `NEW_PER_PROBLEM_MODULES = 0` trên 7 dạng. n = 1 mỗi họ | MEASURED | Ch.3 §3.4; CHAPTER_4 |
| A3 | Compiler tất định phục vụ các họ đã hỗ trợ qua **cùng** bộ cổng, 0 lượt gọi model | sáu họ compiler; **không** phải mặc định (`DEFAULT_MODE = LLM_ONLY`, 20 cổng ở `../MIGRATION_CHECKLIST.md`) | run [`w18-binding-focus`](../evaluation/geometry/runs/w18-binding-focus/) (bộ trình duyệt 6 họ × 2 viewport) | offline: `0ca3accf` / `d3b4cab9…` / 110 | 12/12 ca dương phục vụ; 46/46 ca âm từ chối (W18). Chuyển mặc định sang compiler chưa được phép | MEASURED (offline) | chưa có mục (Ch.3/Ch.5 hướng phát triển) |

### B. Tính đúng tất định

| ID | Tuyên bố | Phạm vi | Bằng chứng / run | Commit / candidate đo | Kết quả và giới hạn | Mức | Dùng ở |
|---|---|---|---|---|---|---|---|
| B1 | Kernel tính **chính xác** (hữu tỉ + căn + π), không làm tròn | bao đóng số `ℚ(√, π)`; ngoài bao đóng ⇒ từ chối | `SCORING_CORRECTION.json` + `scripts/doi_chieu_ket_qua_cuoi.py` (thesis-final-acceptance) | live: `d72db7c3…` / v94 | 12/12 đại lượng khớp từng ký tự và khớp oracle cài độc lập. Văn bản đăng ký trước ghi 11 — đính chính D-1, không sửa hồi tố | MEASURED | Ch.3 §3.5; CHAPTER_4; bài hệ thống |
| B2 | Oracle độc lập xác nhận sản phẩm: nét khuất/hiện của sản phẩm khớp oracle phối cảnh cài khác thuật toán | sáu họ đa diện; camera đã đăng ký | runs w09 → [`w18-binding-focus`](../evaluation/geometry/runs/w18-binding-focus/); `docs/evaluation/geometry/custodian/geometry_oracle.py` | offline; mới nhất `ed37f9fa` / `4629c3e8…` / 112 | product = oracle mọi trạng thái; 64 crop, 0 bất đồng (W18); bảy họ (thêm chóp tứ giác đều), 68 crop, 0 bất đồng (run [`regular-square-pyramid-w01`](../evaluation/geometry/runs/regular-square-pyramid-w01/)). **"Oracle khớp" không chứng minh "người học nhìn thấy"**: w09 đúng phân loại nhưng không có điểm ảnh nét khuất (sửa w10) | MEASURED | Ch.3 §3.7; chưa có mục ở Ch.4 |
| B3 | Năm ca demo chạy lại tất định từ chương trình đã lưu | `n1`, `n2`, `t3`, `t4` phục vụ; `n4` từ chối | `backend/scripts/replay_demo_cases.py` (một phần của T3) | offline; T3 mới nhất `0ca3accf` | 5/5 (W18 T3 PASS). Phát lại chương trình đã lưu, 0 lượt gọi — không nói gì về mô hình | MEASURED (offline) | Ch.4 (demo); `thesis/THESIS_DEMO.md` |

### C. Thẩm định fail-closed, grounding và chứng chỉ giả định

| ID | Tuyên bố | Phạm vi | Bằng chứng / run | Commit / candidate đo | Kết quả và giới hạn | Mức | Dùng ở |
|---|---|---|---|---|---|---|---|
| C1 | Hệ từ chối **có địa chỉ** (giai đoạn, loại, mã lỗi) thay vì chết câm | sáu biên đã biết + hai ca âm của lượt cuối | `backend/scripts/audit_demo_crash_surface.py` (T3); [`../PRODUCT_RESPONSE_CONTRACT_ALIGNMENT.md`](../PRODUCT_RESPONSE_CONTRACT_ALIGNMENT.md) | live 2 ca âm: `d72db7c3…`; căn chỉnh hợp đồng: `e40de3b1…`; T3 mới nhất `0ca3accf` | 6/6 biên, 0 đường ném; 2/2 ca âm fail-closed, `SILENT_WRONG_ANSWER = 0`; lên màn hình 73/73. **Không** phải fuzzing; `n1` không được khai là "ngoài bao đóng" | MEASURED | Ch.3 §3.9; CHAPTER_4 |
| C2 | Độ dài `GIVEN` phải có con số của **đề** ngay sau nhãn đoạn | mọi vùng; chỉ các cách viết bộ đọc nhận ra | run [`w12-pedagogical-grounding-closure`](../evaluation/geometry/runs/w12-pedagogical-grounding-closure/); probe w13/w14 `SOURCE_GROUNDING_PHRASING_PROBE*.json` | offline: `c243968b` / `548f5b3b…` / 105 | giá trị chỉ có trong lời khai `analyze` ⇒ `GIVEN_VALUE_NOT_IN_SOURCE`. W13 tìm ra *"AB dài 5 cm"* lọt (sửa W14); *"AB = AC = 5"* vẫn từ chối oan `AB = 5` | MEASURED (offline) | Ch.3 §3.6 (cần cập nhật) |
| C3 | Trong vùng đa diện theo từ vựng đóng, chỉ phục vụ giá trị số **có chứng chỉ** (C0 / C1) | thể tích, diện tích, khoảng cách; vùng đa diện; góc và cos² ngoài C1 | run [`w15-assumption-closure`](../evaluation/geometry/runs/w15-assumption-closure/) (`ASSUMPTION_MECHANISM_DECISION_W15_R3.json`); [`../architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md`](../architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md) | offline: `c57ebd1b` / `b3b7eb79…` / 107 | AC2 18/18 `PROVEN_SAFE`; AC1 3/3 và đối kháng 7/7 bị từ chối; 111 hàng corpus. Ngoài vùng đa diện cổng chỉ ghi, không từ chối. Lối viết ngoài từ vựng bị từ chối dù đề xác định đáp số | MEASURED (offline) | chưa có mục (Ch.3 §3.6 / Ch.4) |
| C4 | Hệ số mặt phẳng là dữ kiện đề chỉ khi gắn đúng mặt phẳng; yêu cầu chứng minh không làm tiền đề | như C3 | run [`w16-premerge-closure`](../evaluation/geometry/runs/w16-premerge-closure/) (`..._W16_R2.json`, 147 hàng) | offline: `7f3658b0` / `9bb0aaa7…` / 108 | đính chính w15: 7/7 chương trình gán nhầm mặt phẳng bị từ chối, 9/9 gắn đúng vẫn C0; 7/7 lấy mục tiêu làm tiền đề bị từ chối, 4/4 giả thiết hợp lệ vẫn C1 | MEASURED (offline) | chưa có mục |
| C5 | Phép cắt dùng đúng mặt phẳng và đúng khối của câu cắt; giá trị chỉ trong yêu cầu chứng minh không là dữ kiện; lời từ chối nói nguyên nhân | vùng chứng chỉ; từ vựng câu cắt đóng | run [`w17-operation-annotations`](../evaluation/geometry/runs/w17-operation-annotations/) (`..._W17_R2.json`, 167 hàng) | offline: `99925723` / `d63d6fd4…` / 109 | AC2 18/18; tiêm lỗi 23/23 + 18/18. *"(Q) qua M và song song với (X)"* bị từ chối dù đúng (`ISSUE-ARCH-CUT-PLANE-BY-POINT-AND-PARALLEL`) | MEASURED (offline) | chưa có mục |
| C6 | Điểm đề gọi là trung điểm hay hình chiếu được dựng trên **đúng** thực thể đề nêu, xét theo danh tính | từ vựng §16 (trung điểm, hình chiếu); mọi vùng | run [`w18-binding-focus`](../evaluation/geometry/runs/w18-binding-focus/) (`CONSTRUCTION_BINDING_DECISION_W18.json`); run [`w20-cleanup-premerge`](../evaluation/geometry/runs/w20-cleanup-premerge/) (`results/LITERAL_TARGET_PROBE_after_65c90bde.json`, `diagnostics/CONSTRUCTION_BINDING_DECISION_W20.json`) | offline: `0ca3accf` / `d3b4cab9…` / 110; W20: `65c90bde` (probe, census) / `27c31de6…` / 111 | census SHIP, AC2 18/18, 0 hàng W14–W17 bị từ chối mới; tiêm lỗi backend 12/12. W20: đích khai bằng toạ độ, trực tiếp hay qua bí danh, bị từ chối ở mọi vùng — probe 26/27 khớp nhãn ghi trước bản sửa (hàng còn lại do cổng miền), census 179 hàng không đổi, tiêm lỗi FL1–FL7 bắt. Tâm, trọng tâm, giao điểm chưa đối chiếu; đích nhận theo tên điểm | MEASURED (offline) | chưa có mục |
| C7 | Chóp tứ giác ĐỀU được phục vụ chỉ khi đề nói "đều" và cho đủ cạnh đáy cùng một nguồn chiều cao; tâm O đề gọi tên được gắn bằng danh tính | khuôn C1 T7: cạnh đáy + chiều cao / SO / trung đoạn / cạnh bên, chiều cao hữu tỉ; tâm = giao hai đường chéo; thể tích và độ dài | run [`regular-square-pyramid-w01`](../evaluation/geometry/runs/regular-square-pyramid-w01/) (`diagnostics/corpus/LABELS.json`, oracle độc lập `oracle_rsp_w01.py`) | offline: `ed37f9fa` / `4629c3e8…` / 112, chuyển tiếp sang `5234c37e…` (`ad7172ab`) | 24/24 hàng corpus khớp nhãn đăng ký trước (lớp R2 của tự rà soát cuối: cạnh bên `SA = 3` phục vụ sau bản sửa T7, chuỗi `SA = SB = … = 3` còn bị bộ đọc độ dài từ chối); lớp 1 17/17 (7 phục vụ, 10 từ chối có cấu trúc: thiếu chiều cao, không đều, mâu thuẫn, sai danh tính tâm, đỉnh lệch tâm, "chứng minh … đều", chiều cao chỉ ở đầu ra mô hình, chiều cao vô tỉ, dữ kiện góc, chóp tam giác đều); trình duyệt 2 viewport, 4 loại từ chối. Chiều cao vô tỉ (ngoài miền toạ độ hữu tỉ), góc và chóp tam giác/lục giác đều **chưa** phục vụ | MEASURED (offline) | chưa có mục |

### D. Mô phỏng và trình bày

| ID | Tuyên bố | Phạm vi | Bằng chứng / run | Commit / candidate đo | Kết quả và giới hạn | Mức | Dùng ở |
|---|---|---|---|---|---|---|---|
| D1 | Cảnh 3D và dòng thời gian **dẫn xuất** từ vết; khung *k* ⇔ bước *k* (bất biến #31) | mọi envelope có `scene3d` | `FINAL_SUMMARY.json` (TRACE/SCENE3D); `product-envelope-rendering.test.tsx`; `../ARCHITECTURE_MAP.md` §5 | live: `d72db7c3…`; test chạy ở mọi T3, mới nhất `0ca3accf` | 7/7 TRACE, 7/7 SCENE3D. Đo **cấu trúc**, không đo chất lượng sư phạm; kéo liên tục kiểu GeoGebra nằm ngoài vì phá song ánh | MEASURED | Ch.3 §3.7; CHAPTER_4 |
| D2 | Người học truy ngược quan hệ nhân quả bằng thao tác chọn | artifact thật `probe-contract-waves-2` | `test_dependency_visibility.py` (14) + `scene3d-causal-selection.test.ts` (11); báo cáo [`../GEOMETRIC_DEPENDENCY_VISIBILITY_BRIDGE.md`](../GEOMETRIC_DEPENDENCY_VISIBILITY_BRIDGE.md) | `UNKNOWN` trong báo cáo cầu nối (2026-09-04); test chạy ở mọi T3, mới nhất `0ca3accf` | chọn `R` → bao đóng 10 vật, khớp bao đóng dựng độc lập. Trước 2026-09-04 *chọn* trả về rỗng (chỉ *tua* đúng) | MEASURED | Ch.3 §3.8 |
| D3 | Dựng hình theo lớp: đáy, đường cao, đáy trên, cạnh bên thành bước riêng trước khi khép khối, một đường mã cho cả compiler và LLM | sáu họ compiler + gold `p1`, `p2` | run [`w14-generic-formation-assumption`](../evaluation/geometry/runs/w14-generic-formation-assumption/) | offline: `380db58c` / `40263983…` / 106 | trình duyệt 6 họ × 2 viewport, phủ vai trò 12/12. Kết cục w14 `FORMATION_FOUNDATION_INCOMPLETE` (ca âm `n2` `AMBIGUOUS_TOPOLOGY`); **không** phải "mọi đa diện" | MEASURED (offline) | chưa có mục |
| D4 | Phần tô thiết diện phân biệt được với mặt phẳng cắt và khối, nằm dưới cạnh | thiết diện khép kín; desktop + mobile | runs [`w15-assumption-closure`](../evaluation/geometry/runs/w15-assumption-closure/), [`w16-premerge-closure`](../evaluation/geometry/runs/w16-premerge-closure/) | offline: `c57ebd1b`; `7f3658b0` | ΔE nhỏ nhất ≥ 25 (ngưỡng đăng ký trước 12); cạnh che một phần phần tô ρ ≤ 0,485. Chưa ai duyệt bằng mắt | MEASURED (offline) | chưa có mục |
| D5 | Hình mặc định gọn; chọn một đại lượng thì hiện chuỗi số; ô soi là nơi giải thích duy nhất; nhân chứng khoảng cách tới chân chính xác | sáu họ; desktop 1440×900 + mobile 390×844 | run [`w18-binding-focus`](../evaluation/geometry/runs/w18-binding-focus/) (`BROWSER_EVIDENCE.json`) | offline: `0ca3accf` / `d3b4cab9…` / 110 | chọn từng đại lượng 58/58; một vùng công thức 10/10 + 10/10; nét đứt theo bước 72/72; tiêm lỗi frontend 12/12 (vòng 2). Review người `NOT_APPROVED`; yêu cầu sửa giao diện sau W18 ở `../ROADMAP.md`  · **regular-square-pyramid-w01** (`ed37f9fa` / `4629c3e8…` / 112): chín chỉnh sửa ROADMAP §0.1 — card Kết quả ẩn khi lời giải thu gọn, đáp số qua ngăn «Đại lượng» (cổng `quantity_picker` 14/14), panel «Các bước dựng» đồng bộ tiến/lùi, nhảy bước dừng phát, đóng không reset (`steps_panel` 14/14), vị trí cuộn ghi ở mỗi ảnh; review người `NOT_APPROVED` | MEASURED (offline) | chưa có mục |

### E. Tổng hợp bằng mô hình (live)

| ID | Tuyên bố | Phạm vi | Bằng chứng / run | Commit / candidate đo | Kết quả và giới hạn | Mức | Dùng ở |
|---|---|---|---|---|---|---|---|
| E1 | Mô hình tự tổng hợp được chương trình đúng cho đề chưa thấy trong bộ ca | 7 ca dương + 2 âm, phủ 10/10 họ trong phạm vi lúc ấy, n = 1 mỗi họ, **một lượt** | [`../THESIS_FINAL_ACCEPTANCE_EXECUTION.md`](../THESIS_FINAL_ACCEPTANCE_EXECUTION.md); artifact `docs/evaluation/geometry/thesis-final-acceptance/` (run `thesis-final-20260908T160224Z`) | live: `d72db7c3…` / v94; alias `gemini-2.5-flash` | `FINAL_SERVABLE 7/7` · `FIRST_ATTEMPT 6/7` · `RECOVERY 1/1` · `NEGATIVE_FAIL_CLOSED 2/2` · `SILENT_WRONG_ANSWER 0`. **Không** held-out; `STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED`; bộ đo đã sai một lần trong chính lượt này (6 → 0); tái lập model `LIMITED_ACCEPTED`. Cấm gọi 6/7 là "độ chính xác của hệ". `backend/app` đã đổi nhiều lần sau lượt này | MEASURED (live, một lượt) | CHAPTER_4; Ch.4 §4.2 |
| E2 | Chi phí tổng hợp | như E1 | `TELEMETRY_BUDGET_LEDGER.json` (thesis-final-acceptance) | live: `d72db7c3…` / v94 | 19 lượt gọi · 97 869 token · 13 981 token / ca đạt · 2,71 lượt / ca. Không ngưỡng (`no_threshold_by_design`); vượt dự báo +31 % | MEASURED (live, một lượt) | CHAPTER_4 |
| E3 | Mô hình tổng hợp hình cong (cầu, trụ, nón) đủ để bật sản phẩm | pool V3 26 bài / 13 ô, rút 9 ca dương + 4 âm | [`../CURVED_V3_LIVE_ACCEPTANCE.md`](../CURVED_V3_LIVE_ACCEPTANCE.md); [`../V3_PRODUCT_PATH_PARITY_CORRECTION.md`](../V3_PRODUCT_PATH_PARITY_CORRECTION.md); `docs/evaluation/geometry/curved-acceptance-v3/` | live 2026-09-05: `a696200e…` | **FAIL**: 0/9 ca dương phục vụ được; đáp số đúng 1/9 (sau đính chính 0/9 → 1/9); ca âm 4/4 fail-closed. Nút thắt: grounding phép dựng. `EVALUATOR_INDEPENDENCE = OPERATOR_WAIVED`. Khối cong ở sản phẩm giữ `foundation_only` | MEASURED (live, kết quả âm) | Ch.5 (giới hạn) |
| E4 | Độ ổn định qua nhiều lượt | k ≥ 3 lượt trên cùng bộ ca | chưa có; điều kiện A1 ở [`../legacy/research/CLAIM_TO_EVIDENCE_MAP.md`](../legacy/research/CLAIM_TO_EVIDENCE_MAP.md) §3 | — | **chưa đo**; mọi tỉ lệ hiện có là một lượt | PLANNED | Ch.5; điều kiện cho bài hội nghị chính |

### F. Phạm vi và năng lực

| ID | Tuyên bố | Phạm vi | Bằng chứng / run | Commit / candidate đo | Kết quả và giới hạn | Mức | Dùng ở |
|---|---|---|---|---|---|---|---|
| F1 | Hệ phủ **một phần** chương trình hình học không gian THPT | các ô của bảng phủ | [`GEOMETRY_CURRICULUM_COVERAGE.md`](GEOMETRY_CURRICULUM_COVERAGE.md) (mỗi ô đo bằng cách chạy thật); `../COVERAGE.md` cấm tuyên bố phủ toàn bộ | `UNKNOWN` từng ô; tài liệu cập nhật lần cuối 2026-09-04 | phủ một phần, có chủ đích. Bảng chưa cập nhật theo w09–w18 | MEASURED (snapshot 2026-09-04) | Ch.1 §1.7; MỞ ĐẦU §4 |
| F2 | Năng lực **hệ** khác năng lực **sản phẩm** | toàn hệ | `backend/app/simulation/product_capability.py` (ba mức); theo tầng: [`../architecture/geometry_capability_matrix_v2.json`](../architecture/geometry_capability_matrix_v2.json) (snapshot W13) | snapshot `bf5a7907` (W13) | khối cong, khối lõm, thiết diện xiên: hệ có nền, sản phẩm `foundation_only` (không hiện cho người học). Ma trận v2 là kiểm kê kiến trúc, **không** phải năng lực sản phẩm | IMPLEMENTED | Ch.3 §3.6; bài hệ thống |
| F3 | Hai họ ngoài phạm vi vì **lý do kiến trúc** đo được: khối tròn xoay tổng quát, khối ghép/bù cần boolean | toàn hệ | [`../MISSING_FAMILY_ROADMAP_REFRESH.md`](../MISSING_FAMILY_ROADMAP_REFRESH.md); `docs/evaluation/geometry/missing-family-roadmap-refresh/CAPABILITY_MATRIX.json` | 2026-09-08; `UNKNOWN` candidate | chứng minh bằng **vắng mặt** (không thẩm quyền tích phân; không thẩm quyền boolean), không bằng một mã lỗi | MEASURED (chứng minh vắng mặt) | Ch.1 §1.7; Ch.5 |
| F4 | Đọc đề từ **ảnh** (OCR) và bài **nhiều khối** | — | luồng ảnh có mã và cổng trình duyệt dùng FIXTURE (`frontend/scripts/photo-problem-browser-check.mjs`); các wave `PHOTO_PROBLEM_*` ở `../EVIDENCE_INDEX.md` | — | **Không tuyên bố đã hỗ trợ.** Bằng chứng FIXTURE không chứng minh provider thật; nhiều khối chưa làm. Cả hai để sau (`../ROADMAP.md`) | IMPLEMENTED (ảnh) · PLANNED (nhiều khối) | Ch.5 (hướng phát triển) |

### G. Người học

| ID | Tuyên bố | Phạm vi | Bằng chứng / run | Commit / candidate đo | Kết quả và giới hạn | Mức | Dùng ở |
|---|---|---|---|---|---|---|---|
| G1 | Hệ giúp người học hiểu hình học không gian tốt hơn | — | chưa có nghiên cứu người dùng (điều kiện A6 ở bản lưu trữ `CLAIM_TO_EVIDENCE_MAP.md` §3) | — | **chưa đánh giá**. Không trộn kết quả người dùng tương lai vào bảng số kỹ thuật | PLANNED | Ch.5 (hướng phát triển) |

## 3. Câu không được viết (gộp từ ba bảng cũ)

- "IR diễn đạt được mọi bài hình học không gian" · "kernel đúng với mọi bài toán" · "hệ luôn cho đáp số đúng".
- "hệ từ chối đúng mọi bài ngoài năng lực" · "mọi phép dựng đều được đối chiếu với đề" · "mọi đáp số đều có chứng chỉ".
- "mô hình tổng hợp ổn định" · "85,7 % là độ chính xác của hệ" · mọi câu có chữ *ổn định* về hành vi mô hình.
- "phủ chương trình hình học THPT" (không có *một phần*) · "đã hỗ trợ đầy đủ" khối cong.
- "cảnh 3D dễ hiểu với người học" · "đã được người dùng/giáo viên chấp nhận".
- So sánh token liên lượt khi mẫu số khác nhau.

## 4. Khoảng trống của bản thảo (để viết, không phải để đo thêm)

Hàng C3–C6, D3–D5, A3 có bằng chứng đo nhưng bản thảo khoá luận (2026-09-09) chưa có mục. Bản thảo cũng còn **hai
thân Chương 4 rời nhau** (đính chính D-4 trong [`../legacy/research/CLAIM_EVIDENCE_MATRIX.md`](../legacy/research/CLAIM_EVIDENCE_MATRIX.md)).
Hợp nhất là việc của một wave viết bản thảo, ghi ở [`../ROADMAP.md`](../ROADMAP.md).
