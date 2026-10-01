# Kiểm kê năng lực hình học và giả định tuyệt đối (W13)

**Ngày:** 2026-10-01 · **Task:** `W13_GEOMETRY_CAPABILITY_AND_NON_ABSOLUTE_ARCHITECTURE_PREREGISTRATION`
· **Đọc mã tại:** `bf5a7907` (nhánh `fix/cuboid-visual-semantic-closure`)

Đây là **ảnh chụp kiểm kê**, không đổi một dòng mã sản phẩm. Thiết kế và tiền
đăng ký cho wave kế tiếp nằm ở
[`GENERIC_GEOMETRY_FOUNDATION_PREREGISTRATION.md`](GENERIC_GEOMETRY_FOUNDATION_PREREGISTRATION.md).

## 0. Thẩm quyền — file nào trả lời câu nào

| Câu hỏi | Thẩm quyền | Tài liệu này |
|---|---|---|
| Sản phẩm được hiện năng lực nào là "đã hỗ trợ" | [`product_capability.py`](../../backend/app/simulation/product_capability.py) | chỉ trích dẫn |
| Mười hai họ hình trong phạm vi đã đóng, trạng thái đo được | [`CAPABILITY_MATRIX.json`](../evaluation/geometry/missing-family-roadmap-refresh/CAPABILITY_MATRIX.json) | chỉ trích dẫn |
| **Tầng kiến trúc nào** xử lý được nhóm hình nào | [`geometry_capability_matrix_v2.json`](geometry_capability_matrix_v2.json) | tóm tắt §3 |
| Từng giả định tuyệt đối, nguồn `file:dòng`, phân loại | [`ABSOLUTE_ASSUMPTION_INVENTORY.json`](../evaluation/geometry/runs/w13-geometry-preregistration/results/ABSOLUTE_ASSUMPTION_INVENTORY.json) | tóm tắt §2 |
| Bản kiểm kê kiến trúc trước (2026-09-25) | [`architecture_capability_matrix.json`](architecture_capability_matrix.json) (v1, bất biến) | §3.4 ghi chỗ v2 đọc khác |

Ma trận v2 **không** ghi đè hai thẩm quyền đầu: nó trả lời câu hỏi khác
("tầng nào còn thiếu"), mịn hơn, và không nâng trạng thái sản phẩm của nhóm nào.

## 1. Review người của W12

W12 dừng ở `READY_FOR_HUMAN_VISUAL_REVIEW`. Review người: **`NEEDS_CHANGES`**,
merge approval **`NO`** — ghi bổ sung, run w12 giữ nguyên từng byte:
[`inputs/W12_HUMAN_VISUAL_REVIEW.json`](../evaluation/geometry/runs/w13-geometry-preregistration/inputs/W12_HUMAN_VISUAL_REVIEW.json).

| Mã | Phát hiện | Nguyên nhân gốc đọc từ mã |
|---|---|---|
| W12-H1 | Chóp tam giác chỉ có *dữ kiện/điểm → đáy → toàn khối* | `compiler.py::bien_dich` không phát `construct_segment` (đường cao) hay nhóm cạnh bên; lời kể có câu "Dựng đường cao…" nhưng cảnh không có vật nào là đường cao ấy |
| W12-H2 | Lăng trụ tam giác chỉ có *dữ kiện/điểm → đáy → toàn khối* | `compiler.py::_bien_dich_prism` không có đa giác đáy trên, không có nhóm cạnh bên; đường hộp chữ nhật (`_bien_dich_cuboid`) đã có cả hai |
| W12-H3 | Không vá hai họ bằng mã riêng trước khi đánh giá các hình còn thiếu | luật phạm vi — tài liệu này là phần đánh giá |
| W12-H4 | `ISSUE-ARCH-ASSUMPTION-CHANNEL-UNSTATED-DIMENSION` còn mở | toạ độ bố cục / `model_assumption` vẫn cố định được một kích thước đề không cho |

Bốn họ còn lại (chóp chữ nhật, hộp chữ nhật, lập phương, thiết diện) là
`PROVISIONAL_PASS` — không bị bác trong lượt này, **không** phải nghiệm thu.
Thiết diện tô hổ phách ở chế độ trung tính là **câu hỏi thiết kế** (W12-D1),
không phải lỗi tự động.

Điểm chung của H1 và H2: **độ mịn của quá trình dựng do từng họ tự viết tay**.
Hai họ tam giác được viết trước và không bao giờ nhận các bước mà họ chữ nhật
có. Sửa riêng hai họ sẽ lặp đúng lỗi ấy cho chóp đều, lăng trụ xiên, trụ, nón,
cầu — nên W13 không sửa gì, mà tiền đăng ký một mô hình dựng hình theo **lớp
hình** (§2 của tài liệu tiền đăng ký).

## 2. Giả định tuyệt đối

### 2.1 Cách quét

Mỗi hạng mục đích (GPU, trình duyệt, OS, đường dẫn cá nhân, viewport, vectơ
camera, số bước, tên đỉnh, tên họ, mã ca, `CACHE_VERSION`, băm candidate, số
test, số commit, mã màu hex, kích thước bố cục, timeout, dung sai số, một khối,
chỉ đa diện, chỉ toạ độ hữu tỉ, nét khuất chỉ cho cạnh, kề cận trong câu đề,
"đóng băng lại đúng một lần") được quét bằng `grep` trên: `backend/app`,
`frontend/src`, test backend và frontend, `backend/scripts`, `frontend/scripts`
(harness bằng chứng), prompt `backend/app/ai/skills`, và tài liệu sống (AGENTS,
README, RULES, ARCHITECTURE_MAP, AI_CONTEXT_BUNDLE, ROADMAP, OPEN_ISSUES,
THESIS_ARCHITECTURE, THESIS_READINESS, CORRECTNESS, TEST_TIERS, DEMO_RUNBOOK,
RUN_NAMING, `docs/architecture/`, 130 dòng đầu CURRENT_STATE), rồi đọc từng kết
quả trong ngữ cảnh. Artifact lịch sử dưới `docs/evaluation/` mặc định là **G**.

Mười lớp phân loại:

| Lớp | Nghĩa |
|---|---|
| **A** `SAFETY_INVARIANT` | luật an toàn phải đúng ở mọi nơi |
| **B** `MATHEMATICAL_INVARIANT` | đúng vì toán học |
| **C** `CONTRACT_INVARIANT` | hợp đồng có chủ đích của một giao diện |
| **D** `CONFIGURABLE_DEFAULT` | mặc định, đổi được mà không đổi hợp đồng |
| **E** `CAPABILITY_REQUIREMENT` | năng lực môi trường phải có |
| **F** `BASELINE_TEST_ENVIRONMENT` | máy/trình duyệt mà một phép đo đã chạy trên |
| **G** `HISTORICAL_MEASUREMENT` | giá trị quan sát trong một lượt chạy |
| **H** `FAMILY_SPECIFIC_RULE` | luật gọi tên một họ hình |
| **I** `TEMPORARY_IMPLEMENTATION_LIMIT` | giới hạn đã khai của bản cài hiện tại |
| **J** `UNSUPPORTED_ABSOLUTE_REQUIRES_REPAIR` | tuyệt đối không có căn cứ, cần sửa |

### 2.2 Kết quả

**67 mục**: A 4 · B 1 · C 9 · D 13 · E 3 · F 6 · G 8 · H 4 · I 9 · **J 10**.
Năm mục mức HIGH: NA-05, NA-18, NA-37, NA-54, NA-57.

Năm ví dụ bắt buộc của brief:

| Ví dụ | Phân loại |
|---|---|
| GPU "Tesla T4" | Kho **không ghi** tên GPU nào. GPU là **F** — mốc của một số đo hiệu năng, không bao giờ là hợp đồng; số hiệu năng trên GPU thật: `BASELINE_NOT_ESTABLISHED` (NA-01) |
| Chrome 154 | Môi trường đã ghi của run w12 — **G**. Trình duyệt khác: `NOT_MEASURED`, không phải "không hỗ trợ" (NA-02) |
| `3·3·5·5·5·10` | Số đếm của một candidate — **G**. Nghiệm thu đến từ độ phủ ngữ nghĩa + thay đổi quan sát được ở mỗi bước; thêm bước để đủ số là bước giả (NA-13). Harness đã **dẫn xuất** số bước từ trace (NA-14, **C**) |
| cache / candidate | Đọc từ kho (`app.main`, `EVALUATION_CANDIDATE.json`); giá trị trong prompt task chỉ là lời khai — W13 đã đọc lại ở Phase 0 và khớp (NA-22…NA-25) |
| màu | **Vai trò** là hợp đồng (xanh = đang xét, cam đậm = dữ kiện số…); mã hex là giá trị token (NA-30) |

Mười mục **J** — cần sửa, chưa sửa trong W13:

| Mục | Nguồn | Vì sao là J | Hướng sửa |
|---|---|---|---|
| NA-05 · HIGH | `backend/tests/geometry/test_evidence_identity_reconciliation.py:99` | test mặc định đòi file ở `D:/tmp/live_retry_evidence/…`, không có skip; T3 chỉ xanh trên máy có thư mục ấy | marker opt-in báo `NOT_PORTABLE_EXTERNAL_EVIDENCE` (không được commit raw model output — AGENTS §4) |
| NA-11 | `scene3d-view.tsx:593` | bản sao thứ hai của `HUONG = [8,3,6]` | dẫn từ `HUONG` |
| NA-23 | năm test ghim `CACHE_VERSION == "105"` ngoài test nghi lễ | bản sao giá trị sống; mỗi lần bump phải đi tìm | đọc từ `app.main` / lock |
| NA-31 | `scene3d-view.tsx:107-113` | bảng màu KIỂU nằm ngoài thẩm quyền token | dời vào module token có test đồng bộ |
| NA-37 · HIGH | `OPEN_ISSUES` + `ASSUMPTION_CHANNEL_PROBE_79eb1e59.log` | coi "bố cục là tự do" trong khi nó chở một kích thước đáp số phụ thuộc | chính sách §3 tài liệu tiền đăng ký |
| NA-40 | `browser-runner.mjs` | chờ vô hạn một phản hồi DevTools bị mất | timeout từng lượt gọi, có tên lỗi, có đếm |
| NA-42 | `geometry/exact.py:71-80` | docstring nói float đổi "đúng giá trị nhị phân", mã dùng `limit_denominator(10**9)`; số thập phân xấp xỉ thành số hữu tỉ trông như chính xác | đo trước (0 lượt gọi), rồi chọn: từ chối hoặc khai thành hợp đồng |
| NA-52 | `ai/skills/geometry_program_generator.md:85-86` | prompt sinh chương trình **đang chạy** bảo mô hình thiết diện xiên trụ/nón "không diễn đạt được" — trái với IR (`intersect_plane_curved_ellipse`) và với chính thẻ văn phạm gửi kèm | sửa trong wave được phép đổi bề mặt mô hình (băm prompt, quyết định cache, đo lại) |
| NA-53 | `CURRENT_STATE §3/§4`, README §9–10, THESIS_ARCHITECTURE §A/§J, v1 matrix | "8 · 6 · 5", `CURVED_GEOMETRY_SUPPORT = NONE`, mặt cong/khối lõm là gap cố ý — trái với mã (11 · 9 · 7) | W13 thêm banner đính chính ở CURRENT_STATE; các file còn lại vào backlog tài liệu |
| NA-57 · HIGH | phép dò `SOURCE_GROUNDING_PHRASING_PROBE.json` | *"AB dài 5 cm"* không gắn đoạn nào ⇒ số 5 thành giá trị đứng một mình ⇒ khai `AC = 5` **được chấp nhận** | chuẩn hoá an toàn `XY dài v` (cụm đóng, không so khớp mờ) |

Hai mục HIGH không phải J: **NA-18** (H — mỗi họ compiler tự viết chuỗi câu
lệnh, gốc của W12-H1/H2) và **NA-54** (I — toạ độ chỉ ở ℚ³, chặn lời giải chính
xác cho nhiều hình đều).

Những bất biến **giữ nguyên, có bằng chứng**: không mã sản phẩm nào rẽ nhánh
theo tên đỉnh hay mã ca (NA-16, NA-21); harness dẫn xuất số bước (NA-14); kernel
quyết định chính xác, không epsilon (NA-41); thực thi và số lượt sinh có trần
(NA-45, NA-47); test không gọi provider thật (NA-66); `DEFAULT_MODE = LLM_ONLY`
(NA-67).

## 3. Kiểm kê năng lực theo tầng

### 3.1 Mười bảy tầng

Brief ghi "16 tầng" nhưng liệt kê **17 tên**; giữ đủ 17: input/analyze schema ·
RequestContract · source grounding · topology · FactGraph · exact/algebraic
kernel · primitive IR · compiler rule · formation semantics ·
measurement/provenance · renderer · occlusion · interaction · causal closure ·
fail-closed · browser evidence · educational evaluation. Thẩm quyền mã của từng
tầng ghi trong `layers` của ma trận v2.

Luật trạng thái: `SUPPORTED` chỉ khi tầng xử lý **chung** cho nhóm (không phải
một fixture), có mã + test; tầng bằng chứng trình duyệt và đánh giá giáo dục chỉ
`SUPPORTED` khi có artifact đo trên **candidate hiện tại**. Renderer vẽ được
một fixture **không bao giờ** làm nhóm thành `SUPPORTED`: ô renderer chỉ nói
đường vẽ là chung, còn ô bằng chứng nói riêng nó đã từng được đo hay chưa.

### 3.2 Mười bảy nhóm

289 ô: `SUPPORTED` 82 · `PARTIAL` 111 · `MISSING` 87 · `NOT_APPLICABLE` 9.
Ô "nút thắt" là ô chặn nhóm sớm nhất trên đường đi.

| Nhóm | Lớp | Nút thắt |
|---|---|---|
| tứ diện đều | POLYHEDRAL_SOLID | không có ngữ nghĩa "đều"; đặt chính xác trong ℚ³ chỉ được với cạnh đặc biệt (giả thuyết số học, cần phép kiểm khả thi tất định) |
| chóp tam giác đều | POLYHEDRAL_SOLID | tam giác đều trong `z = 0` cần √3; không có họ compiler; dựng hình chưa có kế hoạch kiểu chóp |
| chóp tứ giác đều | POLYHEDRAL_SOLID | biểu diễn được trên tuyến LLM; cho cạnh đáy + cạnh bên ⇒ chiều cao thường vô tỉ; compiler chỉ có chân đường cao tại đỉnh đáy |
| lăng trụ xiên | POLYHEDRAL_SOLID | tuyến LLM dựng được bằng vectơ (demo n2); compiler chỉ nhận lăng trụ đứng; góc nghiêng cho chiều cao vô tỉ |
| lăng trụ/chóp đa giác tổng quát | POLYHEDRAL_SOLID | hợp đồng tô-pô tổng quát có sẵn; compiler chỉ đáy tam giác vuông / chữ nhật / vuông |
| khối đa diện lõm | POLYHEDRAL_SOLID | kernel + renderer đủ (vỏ kín, mặt phẳng và đơn); dựng hình nguyên khối một bước; sản phẩm `foundation_only` |
| hình trụ | CURVED_SOLID | hệ chính xác; **dựng hình nguyên tử** (một câu lệnh → một khung); ngoài bộ phân loại nét khuất |
| hình nón | CURVED_SOLID | như trụ; chế độ vô hướng với `h` vô tỉ bị từ chối |
| nón cụt / trụ cụt | CURVED_SOLID | **thiếu hẳn**; nằm ngoài 12 họ — `OUT_OF_SCOPE_PENDING_DECISION` |
| mặt cầu | CURVED_SOLID | hệ chính xác; dựng hình nguyên tử; neo tâm cần điểm có tên |
| thiết diện mặt cong | DERIVED_SECTION | tròn + elip chính xác; parabol/hyperbol fail-closed; prompt còn nói "không diễn đạt được" (NA-52) |
| giao mặt phẳng – mặt cầu | DERIVED_SECTION | đủ ở hệ; sản phẩm `foundation_only`; bằng chứng trình duyệt chỉ có bản lịch sử |
| nhiều khối | COMPOSITE_SCENE | hợp đồng và compiler **một khối**; nét khuất chỉ xét mặt của chính khối |
| nội tiếp / ngoại tiếp | COMPOSITE_SCENE | không có quan hệ; tâm ngoại tiếp dựng được bằng tổ hợp nhưng chưa đo; tâm nội tiếp thường vô tỉ |
| tiếp xúc | AUXILIARY_GEOMETRY | không có quan hệ, phép dựng hay checker; chỉ có mã từ chối mặt phẳng tiếp xúc |
| khoảng cách, góc | AUXILIARY_GEOMETRY | chính xác bằng tổ hợp; không có ký hiệu cung góc; góc theo độ cho toạ độ vô tỉ |
| góc nhị diện | AUXILIARY_GEOMETRY | chính xác bằng tổ hợp; không có phép dựng riêng (mô hình 0/4 trên probe); không có ký hiệu |

Theo lớp (chi tiết từng ô trong `summary.capability_by_taxonomy` của ma trận v2):
**POLYHEDRAL `PARTIAL`** · **CURVED_SOLID `PARTIAL`** · **AUXILIARY `PARTIAL`**
· **SECTION `PARTIAL`** · **COMPOSITE_SCENE `MISSING`**. Tầng *đánh giá giáo
dục* là `MISSING` cho cả 17 nhóm: chưa có đánh giá với người học
(MIGRATION_CHECKLIST GATE-20), và chương trình học chưa có bằng chứng neo
(`CURRICULUM_EVIDENCE = NOT_ESTABLISHED_OFFLINE`).

### 3.3 Sáu họ đã đo ở W12

| Họ | Dựng hình quan sát được | Còn thiếu (theo mô hình lớp hình) | Review |
|---|---|---|---|
| chóp tam giác | điểm · đáy · khối | đường cao (trùng cạnh bên tại đỉnh vuông) · cạnh bên · khép khối | NEEDS_CHANGES |
| lăng trụ tam giác | điểm · đáy · khối | mặt đáy trên · cạnh bên · khép khối | NEEDS_CHANGES |
| chóp chữ nhật | điểm · đáy · đường cao · cạnh bên · khối | — | PROVISIONAL_PASS |
| hộp chữ nhật, lập phương | điểm · đáy · đáy trên · cạnh bên · khối | — | PROVISIONAL_PASS |
| thiết diện | điểm · đáy · khối · mặt cắt · từng cạnh · khép | — | PROVISIONAL_PASS |

### 3.4 Chỗ v2 đọc khác v1 (v1 giữ nguyên)

1. v1 gọi `Polyhedron` của kernel là "khối lồi"; từ 2026-09-07 thể tích là tổng
   có dấu trên mặt biên, đúng cho vỏ kín không lồi.
2. v1 ghi Scene3D "YES" cho tứ diện đều, chóp đều, lăng trụ xiên vì renderer vẽ
   được khối ấy; v2 tách tính chung của renderer khỏi bằng chứng (chưa đo) và
   khỏi việc đặt toạ độ chính xác (`PARTIAL`).
3. v1 đề xuất primitive `construct_regular_pyramid`; v2 chọn phép dựng chung
   (tâm đa giác, điểm theo pháp tuyến) cộng một phép kiểm khả thi đặt toạ độ —
   không cần primitive riêng cho một họ.

## 4. Phân loại hình (taxonomy)

| Lớp | Định nghĩa | Không được |
|---|---|---|
| `POLYHEDRAL_SOLID` | mặt biên đa diện kín, mặt phẳng; chính xác trong ℚ³; sở hữu cạnh chuẩn và mặt `SOLID_FACE` che khuất | — |
| `CURVED_SOLID` | khối biên mặt bậc hai cho bằng tham số (`KHOI_CONG`: neo, trục, bán kính) | ép thành `Polyhedron`; lưới tam giác chỉ tồn tại trong renderer |
| `AUXILIARY_GEOMETRY` | điểm, đường, đoạn, mặt, vectơ, chân, ký hiệu dựng để giải thích hoặc đo | thuộc biên khối; che khuất |
| `DERIVED_SECTION` | giao của vật cắt với khối: đa giác (đa diện), đường tròn, elip (mặt cong) | là dữ kiện đề cho; đường tròn thành đa giác |
| `COMPOSITE_SCENE` | từ hai khối trở lên, hoặc quan hệ khối–khối | phép hợp/hiệu (giữ `OUT_OF_SCOPE`, lý do kiến trúc) |

## 5. Phát hiện cắt ngang nhiều nhóm

1. **ℚ³ là ranh giới năng lực thật, không chỉ là chi tiết cài đặt.** Đo đạc vô
   tỉ đã có (`Radical`), toạ độ thì không. Một hình không có cách đặt hữu tỉ
   (tam giác đều trong một mặt phẳng toạ độ, chóp đều cho bởi cạnh đáy và cạnh
   bên) không dựng chính xác được — và hiện **không có mã từ chối riêng** cho
   tình huống ấy; số thập phân xấp xỉ còn có cửa vào qua `hf()` (NA-42).
2. **"Đều" không tồn tại ở bất kỳ tầng nào** — lược đồ analyze, quan hệ có cấu
   trúc, FactGraph, checker, cổng phạm vi.
3. **Dựng khối cong là nguyên tử.** Kế hoạch dựng kiểu nón/cầu (tâm, trục, bán
   kính, đường tròn đáy, đường sinh, mặt) cần đổi IR/sự kiện; sản phẩm cong vẫn
   `foundation_only`.
4. **Một khối.** Hợp đồng, compiler và bộ phân loại nét khuất đều giả định một
   khối; renderer vẽ được nhiều vật nhưng thứ tự/độ trong suốt lồng nhau chưa đo.
5. **Bề mặt mô hình và tài liệu sống còn tuyệt đối đã cũ** (NA-52, NA-53).

## 6. Giới hạn của kiểm kê này

- Mỗi ô ma trận đọc từ mã tại `bf5a7907`; **không** ô nào do chạy thử hình đó
  trong W13 (trừ phép dò nguồn ở §4 tài liệu tiền đăng ký). Ô nào là giả
  thuyết thì ghi `HYPOTHESIS`.
- Khẳng định số học về cách đặt hữu tỉ (tứ diện đều, tam giác đều) là giả
  thuyết có cơ sở, cần một phép kiểm khả thi tất định trước khi dùng làm luật.
- Phần Tin học cũ của `STATUS_LEDGER` (dòng 191–456, 600–902) và nhật ký phát
  triển dài của `CURRENT_STATE` chỉ được quét theo từ khoá, không đọc từng dòng.
- 0 lượt gọi model; không chạy trình duyệt; không chạy full suite (chỉ đổi tài
  liệu).
