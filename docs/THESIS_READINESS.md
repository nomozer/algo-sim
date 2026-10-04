# THESIS_READINESS — tuyên bố ↔ bằng chứng ↔ giới hạn

> Chốt phạm vi 2026-09-01 (`THESIS_SCOPE_FREEZE_AND_DEMO_READINESS`).
> **Benchmark ĐÓNG.** Không đo thêm, không mở năng lực mới, 0 lượt gọi model.
> Đây là **bảng đối chiếu duy nhất** cho khoá luận — mọi số sống trỏ về
> artifact nêu tên; không chép số vào đây lần thứ hai.

## 0. Trạng thái đóng băng

| tuyến | trạng thái |
|---|---|
| `SYNTHESIS_BENCHMARKING` | **CLOSED** |
| `TRANSLATION_EVIDENCE` | **CLOSED** |
| `NAME_ONLY_EVIDENCE` | **CLOSED** |
| `ANALYZE_STABILITY` | **NOT_MEASURED_BY_SCOPE_DECISION** |
| `THESIS_FINAL_ACCEPTANCE` | ✅ **ĐÃ CHẠY — `RUN_VALIDITY = VALID`** (2026-09-08, `thesis-final-20260908T160224Z`). 7/7 ca dương servable với đáp số chính xác tuyệt đối · 2/2 ca âm fail-closed · 0 đáp số sai phát ra · 19 lượt gọi. Xem **§7** |

✅ **Bốn tuyến nay đều ĐÓNG.** Bộ đánh giá cuối đã chạy đúng một lượt trên
candidate `d72db7c3…`, bằng runner đã chứng nhận, với kế hoạch · bộ ca · ngưỡng ·
ngân sách khoá **trước** kết quả. `FEATURE_DEVELOPMENT = CLOSED`.

⚠️ **Ba điều phải đi kèm MỌI con số của lượt ấy** (§7):
① không phải held-out; ② `n = 1` mỗi họ, chạy một lần ⇒ không nói được gì về độ
ổn định, và `PRODUCT_PROMOTION_ELIGIBLE = NO` là kết luận đã biết TRƯỚC lượt đo;
③ **bộ đo đã sai một lần trong chính lượt này** và chỉ lộ vì con số phi lý đủ lớn
để buộc soi lại — chi tiết ở `THESIS_FINAL_ACCEPTANCE_EXECUTION.md` §5.

`ANALYZE_STABILITY` không đo **vì quyết định phạm vi**, không phải vì thiếu
điều kiện: đề tài không nghiên cứu độ ổn định thống kê của trích xuất thông
tin. Điều kiện kỹ thuật cũng chưa có (artifact không lưu đầu vào analyze — xem
`docs/evaluation/geometry/analyze-fact-stability/PREFLIGHT_STOP.md`), nhưng **lý do dừng là phạm vi**.

## 1. Bảng chính

| tuyên bố | bằng chứng | giới hạn | trạng thái |
|---|---|---|---|
| LLM tổng hợp Semantic Program cho bài **chưa từng thấy** | `clean-baseline-v2` 6/6 · `translation-probe` 4/4 trong ngân sách · `name-contract-probe` 2/4 một lượt | mẫu nhỏ (n = 4–6 mỗi lượt), không phải ước lượng tổng thể | **SUPPORTED** |
| Engine tất định thực thi, **chính xác tuyệt đối** (hữu tỉ + căn) | `replay_demo_cases.py` 5/5 · suite hình học · `geometry_oracle.py` cài ĐỘC LẬP với kernel | chỉ trong phạm vi IR đã thi hành; khối **lồi**. Mặt cong (cầu · trụ · nón) nay CÓ nền tất định (`geometry/curved.py`, 2026-09-03) — nhưng **sản phẩm** vẫn `foundation_only` | **SUPPORTED** |
| **Bài mới ≠ mã mới** — không nhánh theo dạng bài | runtime đóng băng qua 4 wave đề mới · `PROBLEM_FAMILY_SPECIAL_CASES = 0` (quét AST mã sản phẩm) | chỉ đúng **trong IR hiện có**; bài ngoài IR bị từ chối chứ không tự mở rộng | **SUPPORTED** |
| Cảnh 3D + dòng thời gian **dẫn xuất** từ trạng thái tất định | `replay_demo_cases.py`: `producer`/`depends` có mặt trên mọi vật dựng · bất biến #31 `frame k ⇔ trace[k]` | renderer chỉ ĐỌC state; không có đường ngược | **SUPPORTED** |
| Học sinh **truy ngược được** quan hệ nhân quả bằng thao tác chọn | `test_dependency_visibility.py` (14) + `scene3d-causal-selection.test.ts` (11) trên artifact THẬT `probe-contract-waves-2`: chọn `R` → bao đóng 10 vật, khớp bao đóng dựng ĐỘC LẬP từ `events` | ⚠️ đúng từ 2026-09-04 (`GEOMETRIC_DEPENDENCY_VISIBILITY_BRIDGE`). TRƯỚC đó `dependency_graph` lọc cạnh qua `memory_declarations` nên mọi cạnh trỏ tới vật DẪN XUẤT bị mất — chọn `R` trả về **rỗng**. Chỉ *chọn* hỏng; *tua* vẫn đúng | **SUPPORTED** |
| Ranh giới **R0** giữ được dưới áp lực tổng hợp thật | `NAME_ONLY_CONTRACT_LIVE_PROBE`: 42/42 ô toán hạng là TÊN ở bản THÔ · `RAW_GEOMETRY_LITERAL_ATTEMPTS = 0` | n = 4, k = 1 | **SUPPORTED** |
| Hệ **từ chối có địa chỉ** thay vì chết câm | `audit_demo_crash_surface.py` 6/6 biên, **0 đường ném** · ca demo `n4` bị chặn đúng ở grounding | sáu biên đã biết, không phải fuzzing toàn diện | **SUPPORTED** |
| `analyze` trích **đủ** dữ kiện đề cho | `n1` 3 fact toạ độ, `n2` 4 · **`n3`/`n4` không fact toạ độ nào** | quan sát trên 4 đề, **chưa đo lặp lại** | **PARTIAL** |
| Phủ chương trình hình học THPT | `GEOMETRY_CURRICULUM_COVERAGE.md` | phủ **một phần**, có chủ đích | **PARTIAL** |
| Tác động lên người học | — | **chưa đánh giá** | **OPEN / NGOÀI PHẠM VI** |

## 2. `ANALYZE_SOURCE_FACT_COMPLETENESS = PARTIAL`

Bằng chứng hiện có, nguyên văn: `n1`/`n2` có dữ kiện toạ độ trong
`RequestContract`; `n3`/`n4` **không có**, trên bốn đề nêu toạ độ cùng một kiểu
(`Oxyz`, dạng `A(0; 0; 0)`).

**Không tuyên bố** đây là ngẫu nhiên, hệ thống, ổn định hay bất ổn — bốn chữ ấy
đều đòi một phép đo lặp lại chưa được thực hiện. Ghi đúng thứ quan sát được và
dừng ở đó.

Hệ quả đã biết: `n4` không có fact để trích dẫn nên viết chính chữ trong đề vào
`source_fact_id`, và `grounding_gate` từ chối — **đúng**. Cổng làm việc của nó.

⚠️ Không sửa `analyze` trong wave này: **không ca demo nào hỏng vì lỗ này**
(`DEMO_REPLAY 5/5`).

⚠️ **Thêm 2026-09-29 (w11) — chiều ngược lại cũng mở:** một độ dài CHỈ có trong
fact do analyze viết (đề không nói, nên không có bất biến độ dài do server trích)
vẫn làm căn cứ được cho một đại lượng GIVEN — grounding kiểm chương trình ↔ hợp
đồng, không kiểm hợp đồng ↔ đề. Probe offline, 0 lượt gọi: lăng trụ bỏ `AD = 5`
khỏi đề nhưng giữ fact ⇒ tuyến LLM phục vụ `ok`, tuyến compiler từ chối
(`REQUIRED_LENGTH_MISSING`). Chưa sửa: `ISSUE-ARCH-LLM-ROUTE-LENGTH-NOT-TEXT-GROUNDED`,
log ở `docs/evaluation/geometry/runs/w11-pedagogical-polish/diagnostics/logs/`.

✅ **Cập nhật 2026-10-01 (w12) — chiều ấy đã đóng cho GIVEN:** cổng grounding đọc
bằng chứng từ CÂU ĐỀ — độ dài GIVEN cần con số của đề (nguyên, thập phân `.`/`,`,
phân số, căn) ngay sau nhãn đoạn; giá trị chỉ có trong lời khai `analyze` ⇒
`GIVEN_VALUE_NOT_IN_SOURCE`, không gửi đi sửa; điểm ghim vào lời khai toạ độ mà đề
không ghi cũng bị từ chối. Probe lăng trụ nay trả `unsupported` (chủ thể `AD`); sáu
fixture "đề thiếu một dữ kiện" từ chối đúng trong trình duyệt. Còn mở, KHÔNG phải
GIVEN: toạ độ bố cục/giả thiết có thể cố định một kích thước đề không cho
(`ISSUE-ARCH-ASSUMPTION-CHANNEL-UNSTATED-DIMENSION`). Nguồn:
`docs/evaluation/geometry/runs/w12-pedagogical-grounding-closure/`.

⚠️ **Giới hạn đo thêm 2026-10-01 (w13, offline, 0 lượt gọi):** "đóng cho GIVEN" chỉ
đúng với các cách viết bộ đọc nhận ra. Một độ dài có nhãn mà bộ đọc không nhận
(*"AB dài 5 cm"*) bị coi là số đứng một mình, nên chương trình khai `AC = 5` vẫn
qua (`ISSUE-ARCH-SOURCE-LENGTH-UNLABELLED-PHRASE`); *"AB = AC = 5"* thì từ chối
oan `AB = 5`. Phạm vi tuyên bố: đúng các hàng của
`docs/evaluation/geometry/runs/w13-geometry-preregistration/diagnostics/SOURCE_GROUNDING_PHRASING_PROBE.json`.
Năng lực theo tầng của 17 nhóm hình (chóp đều, lăng trụ xiên, khối cong, nhiều
khối, tiếp xúc, góc nhị diện…) ở `docs/architecture/geometry_capability_matrix_v2.json`
— đó là kiểm kê kiến trúc, **không** phải năng lực sản phẩm; khoá luận chỉ trích
năng lực sản phẩm từ `product_capability.py` và bằng chứng đo.

✅/⚠️ **Cập nhật 2026-10-02 (w14, offline, 0 lượt gọi; chưa có duyệt người):**

- **Dựng hình theo lớp hình — tuyên bố được phép:** sáu họ compiler và các chương
  trình gold được phục vụ (p1, p2) dựng đáy, đường cao (chỉ khi có chân định kiểu),
  đáy trên, cạnh bên thành bước riêng TRƯỚC khi khép khối, từ MỘT đường mã cho cả
  tuyến compiler lẫn LLM (đo trong trình duyệt: 6 họ × desktop/mobile, phủ vai trò
  12/12). **Không** được nói "mọi bài đa diện": ca âm gold n2 (hộp không có đáy định
  kiểu) không phân loại được (`AMBIGUOUS_TOPOLOGY`), và chưa ai duyệt bằng mắt.
- **Kênh giả định — KHÔNG có cổng:** khoá luận **không** được nói sản phẩm từ chối đáp
  số phụ thuộc giả định. Được nói: một cơ chế ba trị đo trên corpus gắn nhãn TRƯỚC cho
  0 `PROVEN_SAFE` trên hàng DEPENDS nhưng chứng nhận 0/18 hàng gold, nên không giao
  (`ISSUE-ARCH-ASSUMPTION-CHANNEL-UNSTATED-DIMENSION` vẫn mở). Kết quả corpus trong
  phạm vi chứng chỉ, không phải chứng minh đúng đắn tổng quát.
- **Nguồn độ dài:** *"AB dài 5 cm"* và *"cạnh AB có độ dài 5"* nay gắn đúng AB — khai
  `AC = 5` bị từ chối (`SOURCE_EVIDENCE_CONFLICT`); dò lại khác đúng hai hàng đã đăng
  ký. *"AB = AC = 5"* vẫn từ chối oan `AB = 5` (ngoài W14). Phạm vi tuyên bố: các hàng
  của `docs/evaluation/geometry/runs/w14-generic-formation-assumption/diagnostics/SOURCE_GROUNDING_PHRASING_PROBE_W14.json`.
- **Hợp đồng thiếu đề** nay bị từ chối (`SOURCE_TEXT_MISSING`), không còn mặc định là
  "không kiểm".

Nguồn: `docs/evaluation/geometry/runs/w14-generic-formation-assumption/` (`REPORT.md`).

✅/⚠️ **Cập nhật 2026-10-03 (w15, offline, 0 lượt gọi; chưa có duyệt người):**

- **Kênh giả định — tuyên bố được phép.** Thay mục "KHÔNG có cổng" của w14, nhưng CHỈ
  trong vùng sau: với đề nêu khối đa diện theo từ vựng đóng, sản phẩm chỉ phục vụ giá trị
  số CÓ CHỨNG CHỈ. C0: mọi literal là dữ kiện đề của cùng thực thể. C1: khuôn T1–T6 cho
  thể tích, diện tích, khoảng cách. Đáp số phụ thuộc một kích thước đề không cho bị từ
  chối. Số đo: hai phép dò W12 bị từ chối, AC1 3/3 và đối kháng 7/7 bị từ chối, AC2 18/18
  vẫn được phục vụ, 11 phản ví dụ sai của w14 còn 0. Phạm vi tuyên bố: 111 hàng corpus
  (W14 48 + W15 49 + W15B 14) của census vòng 3 —
  `docs/evaluation/geometry/runs/w15-assumption-closure/diagnostics/ASSUMPTION_MECHANISM_DECISION_W15_R3.json`.
  Đây **không** phải chứng minh đúng đắn tổng quát: đánh giá cuối toàn nhánh còn tìm
  ra một lỗ ngoài corpus (đã sửa ở `41a26f11`).
- **KHÔNG được nói "mọi đáp số đều có chứng chỉ".** Ngoài vùng đa diện (đoạn thẳng,
  hình phẳng, khối cong không theo từ vựng), cổng chỉ ghi, không từ chối (quyết định
  U3). Lối viết ngoài từ vựng (góc, `SA = AB`, `vuông cân`, độ dài có căn, tỉ số viết
  `thuộc cạnh`) bị từ chối dù đề xác định đáp số. Góc và cos² nằm ngoài C1.
- **Phần tô thiết diện.** Vùng thiết diện khép kín nay phân biệt được với mặt phẳng cắt
  và khối: ΔE nhỏ nhất ≥ 25 trên mọi mẫu, ngưỡng đăng ký trước là 12. Chưa ai duyệt
  bằng mắt.
- **Dựng hình.** Tuyên bố w14 giữ nguyên. Ca âm gold n2 là chương trình bị từ chối
  đúng, ngoài tập dựng hình bắt buộc (quyết định W15-D1 của brief).

Nguồn: `docs/evaluation/geometry/runs/w15-assumption-closure/` (`REPORT.md`).

✅/⚠️ **Cập nhật 2026-10-03 (w16, offline, 0 lượt gọi; chưa có duyệt người):**

- **Đính chính tuyên bố w15 về "cùng thực thể".** Ở w15, hệ số mặt phẳng được nhận nếu tỉ
  lệ với BẤT KỲ phương trình nào của đề. Phép dò w16 tại commit đỏ cho thấy năm chương
  trình gán phương trình của (α) cho (β) được phục vụ; một ca hiện 9 trong khi đề cho 16.
  Mệnh đề "mỗi literal là dữ kiện đề của cùng thực thể" của w15 vì thế **không** đúng với
  mặt phẳng cho bằng phương trình trước `24161657`. Nay đúng trong phạm vi đo: 7/7 chương
  trình gán nhầm bị từ chối, 9/9 gắn đúng vẫn C0.
- **Đính chính: yêu cầu chứng minh từng là tiền đề.** Ở w15, `Chứng minh rằng SA ⊥ (ABC)`
  được đọc như một giả thiết; bảy chương trình C1 dựa trên mục tiêu được phục vụ. Nay mệnh
  đề mục tiêu bị che trước mọi bộ đọc tiền đề (7/7 bị từ chối, 4/4 giả thiết hợp lệ vẫn C1).
- **Được nói:** trong vùng chứng chỉ của w15 (không đổi), hai lỗ trên đã đóng. AC2 vẫn
  18/18; 0 ca hợp lệ mới bị từ chối; tiêm lỗi 13/13 (backend) và 4/4 (frontend). Phạm vi
  tuyên bố: 147 hàng của census vòng 2 —
  `docs/evaluation/geometry/runs/w16-premerge-closure/diagnostics/ASSUMPTION_MECHANISM_DECISION_W16_R2.json`.
- **KHÔNG được nói** "chứng chỉ kiểm mọi lỗi đọc đề". Giới hạn A′: C0 không kiểm một phép
  dựng có dùng đúng thực thể mà đề nói hay không — (T) cắt bởi (α) đã ghim đúng, trong khi
  đề nói (β), vẫn được phục vụ (strict xfail,
  `ISSUE-ARCH-ASSUMPTION-CONSTRUCTION-RELATION-NOT-SOURCE-BOUND`). Ngoài vùng đa diện,
  grounding vẫn đọc độ dài viết trong `Chứng minh …` như dữ kiện
  (`ISSUE-ARCH-GROUNDING-GOAL-CLAUSE-AS-DATUM`). Tự rà soát trước bằng chứng còn tìm ra
  một lỗ ngoài corpus (bí danh (P′) ↔ (P), sửa ở `6b120036`): census là kết quả corpus,
  không phải chứng minh tổng quát.
- **Phần tô thiết diện.** Nay nằm DƯỚI các cạnh khối. Cổng ảnh mới: cạnh che một phần
  phần tô (ρ ≤ 0,485 < 1) và vẫn tương phản (≥ 35,5 so với ngưỡng 12). Độ phân biệt giữ
  ngưỡng w15 (nhỏ nhất ≥ 33,7). Chưa ai duyệt bằng mắt.
- **Sheet nghiệm thu.** Đủ sáu ô từ chối mỗi họ. Ô trắng của sheet w15 là lỗi bước ghép;
  ảnh nguồn đúng.

Nguồn: `docs/evaluation/geometry/runs/w16-premerge-closure/` (`REPORT.md`).

✅/⚠️ **Cập nhật 2026-10-04 (w17, offline, 0 lượt gọi; chưa có duyệt người):**

- **Đính chính giới hạn A′ của w16.** Ở w16, phép cắt dùng một mặt phẳng đã ghim đúng nhưng
  KHÁC mặt phẳng đề nói vẫn được chứng nhận: đề (β), chương trình (α), hiện 9 trong khi đề
  cho 16. Nay mỗi phép cắt trên lát cắt của giá trị hiển thị phải dùng đúng mặt phẳng và
  đúng khối của câu cắt. Lệch thì bị từ chối với `CONSTRUCTION_NOT_TEXT_BOUND`; không chứng
  minh được thì bị từ chối với `ASSUMPTION_INVARIANCE_UNPROVEN`.
- **Đính chính: yêu cầu chứng minh ngoài vùng đa diện.** Ở w16, grounding vẫn đọc giá trị
  trong `Chứng minh …` như dữ kiện ngoài vùng đa diện (hình trụ G4). Nay grounding đọc trên
  văn bản đã che mục tiêu ở mọi vùng.
- **Được nói:** trong vùng chứng chỉ đã đăng ký,
  - thiết diện được phục vụ là thiết diện của đúng mặt phẳng và đúng khối đề nêu;
  - không giá trị nào chỉ có trong yêu cầu chứng minh trở thành dữ kiện;
  - mỗi lời từ chối nói nguyên nhân (đề / hệ dựng / chưa rõ), và chỉ bảo sửa đề khi lỗi ở
    đề.

  AC2 vẫn 18/18; tiêm lỗi 23/23 (backend) và 18/18 (frontend). Phạm vi tuyên bố: 167 hàng
  của census vòng 2 —
  `docs/evaluation/geometry/runs/w17-operation-annotations/diagnostics/ASSUMPTION_MECHANISM_DECISION_W17_R2.json`.
- **KHÔNG được nói** "mọi phép dựng đều được đối chiếu với đề".
  - Chỉ phép cắt (`construct_section`) được đối chiếu; trung điểm và chân đường vuông góc
    thì chưa (`ISSUE-ARCH-CONSTRUCTION-RELATION-BEYOND-SECTION-CUT`).
  - Từ vựng câu cắt ĐÓNG: "(Q) qua M và song song với (X)" bị từ chối dù chương trình đúng
    (`ISSUE-ARCH-CUT-PLANE-BY-POINT-AND-PARALLEL`).
  - Tự rà soát cuối tìm ra ba lỗi nằm ngoài corpus ban đầu. Census vì thế là kết quả trên
    corpus, không phải chứng minh tổng quát.
- **Số đo trên hình.** Backend gắn nghĩa, frontend chỉ đặt chỗ. Nhãn cách neo ≤ 24 px, không
  lộ trước bước (72/72), và bật/tắt không đổi gì khác. Đại lượng chưa có neo (góc, khối
  cong, số trần) không có nhãn. Chưa ai duyệt bằng mắt.

Nguồn: `docs/evaluation/geometry/runs/w17-operation-annotations/` (`REPORT.md`).

✅/⚠️ **Cập nhật 2026-10-04 (w18, offline, 0 lượt gọi; chưa có duyệt người):**

- **Đính chính giới hạn phép dựng của w17.** Ở w17 chỉ phép cắt được đối chiếu với đề. Phép tái
  hiện trước sửa của w18 cho thấy năm loại chương trình sai vẫn được phục vụ: chiếu lên sai
  đường (6√2 thay vì 3√6), chiếu lên sai mặt phẳng, danh sách "lần lượt" bị tráo (3√6 thay vì 9),
  đích đổi tên, và một điểm trùng toạ độ nhưng khác danh tính. Nay mỗi phép dựng điểm mà đề gọi
  tên bằng quan hệ trung điểm hay hình chiếu phải dùng đúng thực thể đề nêu, xét theo danh tính.
- **Được nói:** trong từ vựng đã đăng ký (§16), một điểm đề gọi là trung điểm hay hình chiếu được
  dựng trên đúng thực thể đề nêu, kể cả khi đáp số tình cờ bằng nhau. Lệch thì bị từ chối ở mọi
  vùng và lời từ chối nêu cả hai quan hệ. AC2 vẫn 18/18; census trên W14–W18 không làm hàng phục
  vụ nào bị từ chối; tiêm lỗi backend 12/12. Phạm vi tuyên bố là các corpus đã đo
  (`docs/evaluation/geometry/runs/w18-binding-focus/diagnostics/CONSTRUCTION_BINDING_DECISION_W18.json`),
  không phải một chứng minh tổng quát.
- **KHÔNG được nói** "mọi phép dựng đều được đối chiếu với đề".
  - Tâm, trọng tâm, giao điểm, điểm đối xứng chưa được đối chiếu.
  - Cách nói ngoài từ vựng bị từ chối dù chương trình đúng
    (`ISSUE-ARCH-CONSTRUCTION-BINDING-VOCABULARY`).
  - Đích nhận được nhận theo tên điểm: cùng một đường hay mặt gọi qua điểm khác bị coi là lệch.
- **Trình bày.** Hình mặc định gọn; chọn một đại lượng thì hiện chuỗi số của nó; ô soi là nơi
  giải thích duy nhất; khoảng cách điểm → đường/mặt có nhân chứng chân chính xác. Lượt tiêm lỗi
  frontend đầu tiên tìm ra ba điểm mù của bộ đo trình duyệt (sản phẩm đúng, test đơn vị bắt
  được). Bộ đo đã sửa trước khi đo lại, nên số liệu trình duyệt của w18 đến từ bộ đo sau sửa.
  Chưa ai duyệt bằng mắt.

Nguồn: `docs/evaluation/geometry/runs/w18-binding-focus/` (`REPORT.md`).

## 3. Đính chính đã ghi (không hồi tố điểm)

| đính chính | nội dung |
|---|---|
| `translate` | **`CANONICAL_ERGONOMIC_PRIMITIVE`**, không phải năng lực tổng quát mới. `PRE_EXTENSION_SEMANTIC_EXPRESSIBLE = YES` — `divide_segment(R, midpoint(P,S), 2)` = `P + S − R`. Nó làm phép affine **dễ biểu diễn và dễ tổng hợp hơn**, không mở thêm thứ biểu diễn được |
| oracle `n3` | **không phân biệt được hai cách dựng**: `F = (0,4,2)` và `F = (0,12,−6)` cùng cho số 4. ⇒ **`n3` KHÔNG được dùng làm bằng chứng đúng đắn ngữ nghĩa.** Đây là lỗi của **artifact đánh giá**, không phải của sản phẩm — không sửa mã |
| `angle_cos_sq` | từng trả `sin²` cho cặp (đường, mặt); đã sửa, `ANGLE_SEMANTICS_ERRATUM.md` |
| hidden-line / visual correctness (2026-09-28) | Hàng *"phần thấy/khuất"* ở §7 (2026-09-09, oracle *khối lồi* 3/3) giữ nguyên làm lịch sử. **Cơ chế hiện tại**: backend sở hữu edge ID máy (tách `display_label`), một owner mỗi cạnh, chỉ `SOLID_FACE` che; product classifier world-space thích nghi phát span `VISIBLE`/`HIDDEN`/`MIXED`. **Bằng chứng**: product ↔ oracle perspective độc lập khớp tuyệt đối ID + span trên sáu family (0 mismatch), reference ray/triangle 0 bất đồng. **Kiểm chứng**: wave occlusion dừng ở `VERIFICATION_NOT_CLEAN`; wave w09 (`VERIFICATION_CLEANUP_AFTER_OCCLUSION_REPAIR`) khép hết cổng tự động — T3 detached PASS, camera đóng băng 3 EXACT + 3 tương đương phép chiếu, 12/12 cửa sổ bất biến, và phát hiện một lỗi sản phẩm thật (HTTP 500 với giá trị elip/mặt phẳng trong `scene3d.events`) đã sửa ⇒ `READY_FOR_HUMAN_VISUAL_REVIEW`. **`HUMAN_VISUAL_REVIEW = NOT_APPROVED`** — không được trích như chấp nhận trực quan. Nguồn: `docs/architecture/OCCLUSION_AND_SCENE_IDENTITY_AMENDMENT.md`, `EVIDENCE_INDEX.md` wave `CROSS_FAMILY_HIDDEN_LINE_OCCLUSION_ORACLE_AND_FORMATION_REPAIR` → `VERIFICATION_CLEANUP_AFTER_OCCLUSION_REPAIR`. **Cập nhật w10 (2026-09-29):** review người của w09 là `FAIL_REQUIRES_PEDAGOGICAL_VISUAL_REPAIR` — trong đó có một lỗi mà mọi cổng tự động đã bỏ sót: cạnh khuất được PHÂN LOẠI đúng nhưng không có điểm ảnh nào (GPU kiểm chiều sâu lần hai). Wave `HUMAN_VISUAL_REVIEW_AND_PEDAGOGICAL_PLAYBACK_CLOSURE` sửa (phân loại CPU là thẩm quyền cho cả hai lớp nét; camera mặc định chọn theo số đo cảnh; playback/causal/bề mặt học sinh) và thêm bằng chứng cấp điểm ảnh: crop chứa trọn cạnh khuất (60, 0 bất đồng oracle). Tự động xanh ⇒ vẫn chỉ `READY_FOR_HUMAN_VISUAL_REVIEW`; **bài học cho luận văn: "oracle khớp" không chứng minh "người học nhìn thấy"**. **Cập nhật w11 (2026-09-29):** review người của w10 là `FAIL_REQUIRES_TARGETED_PEDAGOGICAL_REPAIR` (W10-H1…H9) — trong đó một lỗi SẢN PHẨM ở tầng chương trình mà mọi cổng tự động đã bỏ sót: thể tích chóp/lăng trụ đáy tam giác vuông đúng số nhưng không công thức, vì compiler không khai độ dài đề cho nên chiều cao không nối được vào thể tích; và cổng ảnh xoay đo trên phép chiếu trực giao đã nhận ảnh gần suy biến. Wave `W11_PEDAGOGICAL_FORMULA_VISUAL_POLISH_AND_HUMAN_REREVIEW` sửa (compiler khai GIVEN chép từ FactGraph, grounding theo bất biến độ dài, tham chiếu công thức nhất quán; cổng ảnh xoay trên ảnh phối cảnh; chấm đỉnh theo px CSS; causal bốn tầng; sheet theo họ) ⇒ vẫn chỉ `READY_FOR_HUMAN_VISUAL_REVIEW`; **bài học thêm: "đáp số đúng" không chứng minh "lời giải hiện đủ căn cứ"**. Nguồn: `docs/evaluation/geometry/runs/w11-pedagogical-polish/`. **Cập nhật w12 (2026-10-01):** review người của w11 là `NEEDS_CHANGES` (W11-H1…H5): thanh bước đi qua cả bước chỉ tính số (hình đứng yên), cam đậm hai nghĩa, và tuyến LLM nhận một độ dài đề không ghi rồi gắn GIVEN. Wave `W12_PEDAGOGICAL_TIMELINE_AND_SOURCE_GROUNDING_CLOSURE` tách dòng thời gian HÌNH HỌC khỏi lớp lời giải (bảng Kết quả · Dữ kiện · Các bước tính đồng bộ), dùng một bảng màu vai trò, và đóng grounding nguồn cho GIVEN ⇒ vẫn chỉ `READY_FOR_HUMAN_VISUAL_REVIEW`. Chính wave này cũng cho một bài học đo lường: mọi cổng tự động xanh trong khi viền thiết diện NGỮ CẢNH vẫn mang màu "trung gian" — lỗi chỉ lộ ra khi người làm đọc sheet; bộ đo nay đếm sắc độ trên khung causal và được thử trên một đáp án đã biết trước khi tin. Nguồn: `docs/evaluation/geometry/runs/w12-pedagogical-grounding-closure/` |

Mọi điểm số lịch sử (`GENERALIZATION_MATRIX`, `CLEAN_BASELINE_V1/V2`,
`SYNTHESIS_STABILITY_K3`, translation probe, `NAME_ONLY` probe) **giữ nguyên**.

## 4. Giới hạn — phân loại

### A. PHẢI SỬA TRƯỚC DEMO
**Không có.** `P0 = 0`, `P1 = 0`. `DEMO_REPLAY = 5/5`, 0 đường ném.

### B. GIỚI HẠN CHẤP NHẬN CỦA KHOÁ LUẬN
| giới hạn | vì sao chấp nhận |
|---|---|
| `CONTROL_FLOW_DEFINITE_ASSIGNMENT = PARTIAL` | chương trình hình học gần như không rẽ nhánh; ca ấy bị **từ chối tĩnh** chứ không chạy sai. Kernel vẫn fail-closed |
| `ANALYZE_SOURCE_FACT_COMPLETENESS = PARTIAL` | không chặn demo; đo nó là nghiên cứu trích xuất thông tin, ngoài đề tài |
| ~~chỉ khối **lồi**~~ → khối **lõm** cũng có nền | ⚠️ **ĐÍNH CHÍNH 2026-09-07/08.** Câu gốc — *"ranh giới phạm vi có chủ đích (`GEOMETRY_ROADMAP`)"* — giữ nguyên ở đây làm bằng chứng lịch sử, nhưng nó **hết đúng**: `NONCONVEX_POLYHEDRON_VOLUME_FOUNDATION` đóng nền tất định cho khối lõm (thể tích bằng **tổng có dấu trên mặt biên**, `abs` đúng một lần ở cuối; 5 mã fail-closed), và `NONCONVEX_POLYHEDRON_MODEL_DISCOVERABILITY` đo được mô hình **tự viết đúng bảng mặt ngay attempt đầu**. ⚠️ Câu cũ còn che một sự thật **tệ hơn** một giới hạn: trước bản vá hệ **không** từ chối khối lõm — nó **phục vụ** khối lõm với một con số **SAI** (`28` thay vì `20`). Phạm vi đã chứng minh vẫn hẹp và phải nói đúng: *"biên KÍN, một vỏ, mọi MẶT phẳng và đơn"*, **không** phải *"mọi đa diện không lồi"*; hai MẶT khác nhau xuyên qua nhau là điều kiện **toàn cục** và vẫn ngoài bao đóng v1. Năng lực **sản phẩm** vẫn `foundation_only`. Thẩm quyền: `product_capability.py` |
| phạm vi TÍNH NĂNG **ĐÃ ĐÓNG** (2026-09-08) | ⚠️ Thêm 2026-09-08 (`MISSING_FAMILY_ROADMAP_REFRESH`). Bản đồ mười hai họ lập lại **từ mã nguồn**, kiểm được bằng máy (`CAPABILITY_MATRIX.json` + 26 test). Kết quả: `UNSUPPORTED` **rỗng**; còn đúng **một** họ đáng làm — **thiết diện xiên của hình nón**, khoảng trống là **một nhánh kernel** + **một chuỗi gợi ý** trong thẻ (`NEW_MEMORY_TYPES = 0`, `NEW_IR_OPERATIONS = 0`, checker/trace/Scene3D đều đã sẵn). ⚠️ Kèm một **đính chính**: ghi chú registry *"nón cắt xiên … ba nhánh chưa phân xử"* mô tả **việc chưa làm**, KHÔNG phải khoảng trống miền số — đo được `a²`, `b²` đều **hữu tỉ**, phân xử ba nhánh conic là một **phép so hữu tỉ**, và bốn ca khớp một oracle số độc lập tới `~1e-9`. Hai họ còn lại (`khối tròn xoay tổng quát`, `khối ghép/bù`) `OUT_OF_SCOPE` vì **lý do kiến trúc đo được**: không thẩm quyền tích phân nào và không kiểu biểu thức hàm trong `MemoryType`; boolean cần đúng điều kiện toàn cục mà hệ **đã khai là không kiểm được**. ⚠️ **CẬP NHẬT cùng ngày**: `OBLIQUE_CONE_SECTION_FOUNDATION` đã làm xong họ ấy — `oblique_cone_section` từ `EXPRESSIBLE_ONLY` sang `FOUNDATION_ONLY`, ca chuẩn `12π√6/5` với ba oracle độc lập, phân xử conic bằng phép so hữu tỉ, `NEW_IR_OPERATIONS = 0` và `NEW_AUTHORITIES = 0`. Nên `FEATURE_SCOPE_COMPLETE = YES`: **mọi họ trong phạm vi đã có foundation**, và việc còn lại của khoá luận là **đánh giá** (độ phủ · độ đúng · tỉ lệ tự sinh thành công · token · giới hạn), **không phải thêm hình**. ⚠️ Vẫn phải phân biệt hai câu: năng lực **hệ** có nền ≠ năng lực **sản phẩm** — mọi họ cong vẫn `foundation_only`, `PRODUCT_PROMOTION_ELIGIBLE = NO` |
| mặt cong: HỆ đóng, SẢN PHẨM `foundation_only` | ⚠️ ĐÍNH CHÍNH 2026-09-04. Bảng này từng ghi *"không mặt cong"* và câu ấy hết đúng từ `169b8ef` (2026-09-03). Phân biệt hai câu: năng lực **hệ** (IR + kernel + vẽ) = `CLOSED`; năng lực **sản phẩm** `ball`/`cylinder`/`cone` = `foundation_only` — chưa lượt tổng hợp cong nào của mô hình đạt `servable` trên bất kỳ artifact nào. Thẩm quyền: `product_capability.py` |
| hình thành khối bằng quay/quét liên tục | `OUTSIDE_CURRENT_MODEL` — `construct_curved_solid` là bước NGUYÊN TỬ (1 lệnh → 1 trace → 1 khung) |
| phủ chương trình **một phần** | có chủ đích; `COVERAGE.md` cấm tuyên bố phủ toàn bộ |
| `SECTION_COPLANAR_EDGE_GAP` | ca demo thiết diện (`v2_04`) **không chạm** lỗ này. Đã sửa 2026-09-02 ở bản sản phẩm hiện tại, **sau** `SEALED_RESEARCH_BASELINE` — số liệu không đổi theo |
| `literal` bọc quanh vô hướng ở `divide_segment.ratio` | quan sát 1 lần; cùng lớp đã vá cho `for_range.step` |
| **tái lập model ở mức `LIMITED`** | ⚠️ **GIỚI HẠN PHƯƠNG PHÁP — phải khai trong khoá luận.** Model gọi bằng **alias** `gemini-2.5-flash`, không phải snapshot bất biến; `call_gemini` không phơi `modelVersion` từ response ra cho caller (sửa được, nhưng `app/ai/gemini.py` nằm trong `MEASURED_SYSTEM_PATHS` ⇒ phá đóng băng candidate). Người hướng dẫn **chấp nhận `LIMITED`** 2026-09-05, khoá **trước** mọi kết quả V3 (policy `1.1.0`, băm `460e0ce5…`). Đổi lại: alias · UTC start/end · SDK + version · endpoint class · tham số **thực sự gửi** · tham số **không gửi** ở trạng thái typed `NOT_SENT` · raw response metadata · raw candidate mọi attempt — tất cả **bắt buộc** có trong manifest. **Không** tuyên bố tái lập bit-for-bit; **không** hiển thị alias thành `PINNED`. Thẩm quyền: `curved_v3_threshold_policy.json` → `model_identity_policy`; chi tiết `V3_RUNNER_MANIFEST_INTEGRATION_AND_LIMITED_REPRODUCIBILITY_DECISION.md` §1, §8 |

| **nghiệm thu V3 hình cong: ĐÃ ĐO — `FAIL`** | ⚠️ **2026-09-05, lượt đã chạy.** `EVALUATOR_INDEPENDENCE = OPERATOR_WAIVED` · `MEASUREMENT_CLASS = INTERNAL_ONE_SHOT_ACCEPTANCE` — phiên đo **cũng là** phiên sửa bộ đo (`c41e1ab`), miễn trừ do người vận hành cấp; con số mất một bậc giá trị và phải khai vậy. Seed ngoài `5324284654432805119`, `DRAW_COUNT=1`, `CASE_SET_HASH eb1c402a…`, 26/78 lượt gọi, `RUN_VALIDITY=VALID`. ⚠️ **ĐÍNH CHÍNH 2026-09-05** (`V3_PRODUCT_PATH_PARITY_CORRECTION`): đáp số đúng **0/9 → 1/9**, Scene3D **0/9 → 1/9**, `c7a` chuyển từ lỗi MÔ HÌNH sang **lỗi HỆ** (`SYSTEM_VERIFICATION_FAILURE`) — runner đọc đáp số từ một phép chiếu luôn rỗng. Servable và verdict tổng **không đổi**. **Kết quả: 0/9 ca dương servable · ~~0/9~~ 1/9 đáp số đúng · ball 0/3 · cylinder 0/3 · cone 0/3 · ca âm 4/4 fail-closed nhưng chỉ 1/4 chạm ranh giới cong.** `GENERAL_CURVED_SYNTHESIS_ACCEPTANCE = FAIL`; ba `PRODUCT_PROMOTION_ELIGIBLE_* = NO`; sản phẩm giữ `foundation_only`. Nút thắt **không** phải derived-scalar (không ca nào rút trúng ⇒ vẫn `NOT_MEASURED`) mà là **CONSTRUCTION-GROUNDING**: `construct_curved_solid` bắt buộc một `point3` neo được, còn grounding gate cấm khai `point3` cho đề không đặt tên điểm — chứng minh tất định ở `CURVED_V3_LIVE_ACCEPTANCE.md` §8. Thẩm quyền: `docs/CURVED_V3_LIVE_ACCEPTANCE.md`; artifact `docs/evaluation/geometry/curved-acceptance-v3/` | |
| ~~nghiệm thu V3: `NOT_MEASURED`~~ (bản trước lượt chạy) | ⚠️ 2026-09-05. Pool V3 đã niêm phong (`36c2153e…`, 26 bài/13 ô) nhưng **chưa rút**, `seed = null`, `APPLICATION_LLM_CALLS = 0`. Ba phiên đã nhận uỷ quyền và cả ba dừng trước khi rút. Phiên thứ ba **đạt** độc lập evaluator, rồi phát hiện hai khiếm khuyết ở **đường chạy live** của bộ đo: `main_async` chạy corpus phát triển V1/V2 chứ không phải pool đã rút và không ghi `manifest.json` (`LIVE_ENTRYPOINT_NOT_WIRED_TO_SEALED_POOL`); `mong` của pool là `list` còn runner đòi `set` (`POOL_MONG_TYPE_INCOMPATIBLE`). Cả hai ở `backend/scripts/` ⇒ **không** đụng candidate, **không** cần reseal, và **cả hai ĐÃ ĐÓNG** cùng ngày (`V3_LIVE_ENTRYPOINT_WIRING_REPAIR` — 37 test chạy chính `main_async`, nhãn certifier mạnh `V3_LIVE_ENTRYPOINT_INTEGRATION PASS`). **Nhưng lượt đo vẫn chưa chạy**: pool chưa rút, `seed = null`, 0 lượt gọi. Nên: `BALL`/`CYLINDER`/`CONE_ACCEPTANCE` = `NOT_MEASURED`, `PRODUCT_PROMOTION_ELIGIBLE_*` = `NOT_MEASURED`, sản phẩm giữ `foundation_only`. Thẩm quyền: `V3_LIVE_ENTRYPOINT_INTEGRATION_BLOCKER.md` (blocker) + `V3_LIVE_ENTRYPOINT_WIRING_REPAIR.md` (bản sửa); bằng chứng máy `docs/evaluation/geometry/curved-v3/PREDRAW_GUARD_2026-09-05_INDEPENDENT.json` |

### C. HƯỚNG PHÁT TRIỂN
Kéo–thả liên tục kiểu GeoGebra (phá song ánh `frame k ⇔ trace[k]`) · **bật
sản phẩm** cho mặt cong (nền hệ đã có; thiếu bằng chứng mô hình tổng hợp) ·
đánh giá tác động người học · đo độ ổn định trích xuất · viết lại thân README
cho đề mới · `REPLAYABLE_ANALYZE_SEED` (chụp đầu vào analyze, đối xứng với tầng
tổng hợp đã có).

## 5. Tập demo

`backend/scripts/replay_demo_cases.py` — **0 lượt gọi model**, chạy từ chương
trình đã lưu trong artifact có xuất xứ rõ.

| ca | vai trò | nguồn |
|---|---|---|
| `n1_thoi_dinh_thu_tu` | dựng đỉnh thứ tư từ vectơ → đo tới đường, đáp số `√3` | `name-contract-probe` |
| `n2_lang_tru_xien_hai_vecto` | lăng trụ **xiên**, hai vectơ dẫn xuất + trung điểm, `3√3` | `name-contract-probe` |
| `t3_hop_tinh_tien_day_chuyen` | dây chuyền tịnh tiến 4 đỉnh, chuỗi sâu, `3√89/5` | `translation-probe` |
| `t4_mat_xich_trong_chuoi_sau` | hình chiếu trong chuỗi phụ thuộc, `2√2` | `translation-probe` |
| `n4_giao_duong_mat_roi_do` | **CỔNG TỪ CHỐI** — trích dẫn dữ kiện không có trong hợp đồng | `name-contract-probe` |

Ca thứ năm là **cố ý**: một demo chỉ toàn ca xanh giấu mất nửa luận điểm. Hệ
phải nói KHÔNG có địa chỉ, và đây là chỗ trình bày điều đó.

**Thiết diện** chạy riêng ở chế độ rút gọn (`v2_04_thiet_dien_goc_va_the_tich`,
cảnh có `section` + `solid`): artifact `clean-baseline-v2` **không lưu
`RequestContract`** nên không chạy được cổng grounding. Đếm riêng, không gộp
vào `DEMO_REPLAY` — gộp là báo cáo một chuỗi đủ mà thực ra thiếu một cổng.

## 6. Smoke trình duyệt cho tập demo

`frontend/scripts/spot-check-demo.mjs` — Chrome thật, WebGL:
**`DEMO_BROWSER_SMOKE = 12/12`, 0 lỗi console** (`DEMO_SPOT_CHECK.json`).

Số bước đọc từ màn hình khớp **chính xác** bộ replay Python — `n1` 6, `n2` 7,
`t3` 10, `t4` 9 — tức hai bộ đo độc lập nói cùng một điều về cùng một trace.
Đã tiêm lỗi giả để chứng minh nó đỏ được (8/12).

## 7. BỘ ĐÁNH GIÁ CUỐI — ĐÃ CHẠY, SỐ ĐÃ ĐỐI CHIẾU, CHƯƠNG ĐÃ VIẾT (2026-09-08)

> ⚠️ Tiêu đề mục này từng ghi *"lượt đo CHƯA CHẠY"* và đã lệch với §0 một wave.
> Thẩm quyền theo thứ tự: kế hoạch ở
> `docs/THESIS_ACCEPTANCE_MATRIX_AND_DOCUMENTATION.md` · runner ở
> `docs/THESIS_FINAL_ACCEPTANCE_RUNNER_ALIGNMENT.md` · **kết quả** ở
> `docs/THESIS_FINAL_ACCEPTANCE_EXECUTION.md` · **đối chiếu + chương** ở
> `docs/THESIS_RESULTS_ANALYSIS_AND_CHAPTER_DRAFTING.md`; artifact ở
> `docs/evaluation/geometry/thesis-final-acceptance/`.

`FEATURE_DEVELOPMENT = CLOSED`. Việc còn lại của khoá luận là **đánh giá**.

| | |
|---|---|
| `EVALUATION_CLASS` | **`FROZEN_FINAL_DEVELOPMENT_BENCHMARK`** |
| `HELD_OUT_CLAIM` | **NO** |
| `OPERATOR_INDEPENDENCE_REQUIRED` | **NO** |
| `MODEL_REPRODUCIBILITY` | `LIMITED_ACCEPTED` (quyết định 2026-09-05 vẫn đứng) |
| bộ ca | **7 dương + 2 âm**, CỐ ĐỊNH, phủ **10/10** họ trong phạm vi |
| gold preflight | **7/7** servable · exact · oracle · postconditions · scene3d |
| ngân sách | `18` lượt dự kiến · trần `39` · `294 000` token |
| `FINAL_ACCEPTANCE_RUNNER_READY` | ✅ **YES** — **16/16** nhãn chứng nhận PASS |
| **KẾT QUẢ LƯỢT CUỐI** | `RUN_VALIDITY = VALID` · `FIRST_ATTEMPT 6/7` · `RECOVERY_WITHIN_ONE_REPAIR 1/1` · **`FINAL_SERVABLE 7/7`** · `EXACT_ANSWER 7/7` · `ORACLE 7/7` · `NEGATIVE_FAIL_CLOSED 2/2` · `SILENT_WRONG_ANSWER 0` |
| chi phí thực | 19 lượt gọi · 0 retry transport · **97 869 token** (trần 196 000) · 13 981 token/ca đạt |
| `TARGET_BOUNDARY_PASS` | **1/2** — số ĐO, không phải ngưỡng. `n1` bị chặn ở R0 (`UNANCHORED_DERIVED_ASSUMPTION`) trước khi tới cổng phủ, nên không có `error_code` để so: giới hạn của phép pre-registration, không phải của hệ |
| trần lượt gọi | **25** logic · **100** vật lý · **196 000** token (amendment 1.1.0, chặng B tiếp tục thay vì chạy lại) |
| **số đã đối chiếu chưa** | ✅ `DOCUMENTATION_INPUT_CONSISTENCY = **PASS**` — `SO_TRUONG_LECH 0/31` · `DAP_SO_KHOP 12/12` (từng ký tự) · băm lại 26 file, 19 file thô nguyên byte · liên kết đính chính trỏ đúng 3 artifact. Lệnh: `scripts/doi_chieu_ket_qua_cuoi.py <thư_mục_lượt_chạy>`, **0 lượt gọi** |
| **chương đã viết chưa** | ✅ `docs/thesis/CHAPTER_4_RESULTS_AND_DISCUSSION.md` (11 mục, 10 bảng) · `docs/thesis/CHAPTER_5_CONCLUSION_AND_LIMITATIONS.md` (4 mục) |
| **JSON có lên được màn hình chưa** | ✅ `UI_RESULT_RENDERING = PASS` (2026-09-09) — 9/9 envelope dựng trong Chrome thật qua **biên mạng**, 66/66 phép kiểm, 12/12 đáp số đọc TRÊN MÀN HÌNH, 0 ngoại lệ, 6/6 phép tiêm đỏ đúng chỗ. `DEMO_READY_ON_FROZEN_CASES = YES` · `PRODUCT_DEPLOYMENT_READY = NOT_CLAIMED`. Xem `PRODUCT_UI_RESULT_RENDERING_AND_DEMO_ACCEPTANCE.md` |
| ⚠️ **đính chính số** | **12** đại lượng, không phải 11 (2026-09-09). `SCORING_CORRECTION.json` có 12 mục `quantities_SUA` đều khớp; cảnh 3D phát đúng 12 số đo. Con số 11 đến từ văn bản ĐĂNG KÝ TRƯỚC (§7 bảng trên vẫn giữ nguyên — không hồi tố) rồi được chép lại mà chưa từng được máy đối chiếu |
| **hình có ĐÚNG và ĐỌC ĐƯỢC không** | ⚠️ `VISUAL_DEMO_FIDELITY_ON_FROZEN_CASES = **PARTIAL**` (2026-09-09). `WORLD_SPACE_GEOMETRY = 7/7` với **tolerance bằng 0** (số hữu tỉ chính xác, 16 điểm mẫu/đường cong) ⇒ dữ liệu Scene3D đúng tuyệt đối, mọi khiếm khuyết đều ở tầng TRÌNH BÀY. Đã sửa: miếng mặt phẳng đặt theo vùng hình học (3/3 phủ hết thiết diện, nền 0/3) · khung nhìn ôm toàn cảnh và bỏ vật vô hạn (7/7, nền 6/7) · nét thiết diện dày theo tỉ lệ cảnh · thẻ từ chối một giọng (2/2, nền 0/2). **KHÔNG** thiết lập được: `SECTION_VISIBILITY` — cả hai chỉ số thử đều không cô lập được khác biệt, bằng chứng còn lại là ảnh. **KHÔNG** sửa: `DISPLAY_NAME` 10/12 — bản vá `ellipse3` đã hoàn tác vì nó buộc phải viết lại `candidate_hash` trong hợp đồng đo ĐĂNG KÝ TRƯỚC. Xem `SCENE3D_VISUAL_SEMANTIC_FIDELITY_REVIEW.md` |
| **phần thấy/khuất có phân biệt được không** | ✅ `DYNAMIC_HIDDEN_LINES = **PASS**` (2026-09-09). Trước đó **không có hidden-line nào**: mọi khối khai `depthWrite: false`. Nay có lớp chiều sâu vô hình + vẽ hai lượt; `OCCLUSION_CLASSIFICATION` 3/3 bằng oracle ĐỘC LẬP (*thấy ⟺ n̂·(mắt−Q) > 0* trên khối lồi), `RASTER_LINE_STYLE` PASS với ngưỡng hiệu chỉnh từ phép tiêm, 6/6 phép tiêm bị bắt. Không hồi quy: đáp số 12/12, ca âm 2/2, world-space 7/7. Xem `SCENE3D_DYNAMIC_HIDDEN_LINES_AND_READABILITY.md` |
| **bản dùng cho khoá luận có TÁI LẬP được không** | ✅ **RỒI** (2026-09-09) — `FINAL_SYSTEM_RELEASE = PASS`. Cổng chập chờn cuối cùng đã có nguyên nhân tất định: **transport headless Chrome ↔ Vite dev server** (Vite dev kẹt **2/15** phiên, bản dựng sản phẩm **0/15**; tải lại cứu 0/2, phiên mới cứu 6/10). `FLAKE_RATE 0.9 → 0`. Lặp: targeted **10/10** · browser **3/3** · visual oracle **3/3** · tiêm lỗi **4/4**. ⚠️ Bộ đo còn một lỗi THẬT đã sửa: nó báo *"nhãn rỗng"* (nội dung) cho một sự cố **hạ tầng**, nên `17/21` đẩy người đọc đi sửa đúng thứ đang chạy tốt; nay quá hạn thì ném `PAGE_NOT_LOADED` và **không** ghi artifact nghiệm thu. Bàn giao: `RELEASE_MANIFEST.json` (hai candidate ghi hai trường), 12 ảnh demo có xuất xứ, `docs/DEMO_RUNBOOK.md`. ⚠️ Giới hạn: hai cổng trình duyệt còn chạy trên dev server và chỉ được che bằng *mở lại có trần* — nợ `BROWSER_GATES_ON_PRODUCTION_BUILD`; runbook vì thế chỉ dẫn demo chạy từ **bản dựng**. `FEATURE_DEVELOPMENT_STATUS = CLOSED`. Xem `FINAL_SYSTEM_REPRODUCIBILITY_AND_RELEASE_FREEZE.md` |
| **lời từ chối có đủ cấu trúc như §1.6/§3.9 đã hứa chưa** | ✅ **RỒI** (2026-09-09) — `PRODUCT_RESPONSE_CONTRACT_ALIGNMENT = PASS`. Cam kết nguyên văn là *"nêu **giai đoạn dừng, loại thất bại, mã lỗi**"*; lượt đo cuối giao `n1` với `stage_reached = null` và `error_code = null` (**2/4** trường). Phát lại **nguyên byte** qua **bảy biên** định vị chỗ mất: biên 4 ĐÃ phát cả hai cho observer rồi `return None` ⇒ lỗi ở **biên chuyển kết quả**, không ở tầng phát hiện. Nay `n1` = `semantic_program` / `semantic_program_invalid`, `n2` = `structural_coverage` / `requested_operation_uncovered`, và cả hai lên MÀN HÌNH bằng nhãn tiếng Việt (**73/73** phép kiểm Chrome thật, **7/7** phép tiêm bị bắt). ⚠️ Giới hạn nói thẳng: **`n1` KHÔNG được khai là "ngoài bao đóng"** dù ma trận năng lực xếp khối tròn xoay tổng quát là `OUT_OF_SCOPE` — lượt chạy **dừng trước** cổng phủ, nên hệ chỉ biết *chương trình không hợp lệ*; câu gợi ý giữ dạng **có điều kiện**. ⚠️ Đây là lần **ĐẦU** `backend/app` đổi sau lượt nghiệm thu cuối: candidate `d72db7c3…` → `e40de3b1…`, đã KHAI ở `CANDIDATE_DIVERGENCE.json`; **số liệu lượt đo cuối KHÔNG chấm lại** — chúng mô tả `d72db7c3…`. Xem `PRODUCT_RESPONSE_CONTRACT_ALIGNMENT.md` |
| **mục tiêu ↔ bằng chứng đã đối chiếu chưa** | ✅ **RỒI** (2026-09-09) — 29 tuyên bố (5 mục tiêu · 7 đóng góp · 5 RQ · 9 claim đăng ký · 3 phát biểu phạm vi): `PROVED_ON_FROZEN_BENCHMARK 13` · `PARTIAL 8` · `NOT_MEASURED 2` · `OUT_OF_SCOPE 2` · **`CONTRADICTED 4`**. `OBJECTIVE_SOURCE = THESIS_DRAFT §3·§4·§6·§1.6·§1.7`. ⚠️ Bốn tuyên bố TRÔI, đã đính chính mà giữ nguyên bản gốc — nặng nhất: bảng *ngoài phạm vi* của bản thảo khai mặt cong/khối lõm/phương trình mặt phẳng là NGOÀI, trong khi lượt đo cuối **phục vụ đúng cả ba**; và bản thảo có **hai thân Chương 4 rời nhau**. Ma trận: `docs/thesis/CLAIM_EVIDENCE_MATRIX.md` |
| `NEXT_ACTION` | `THESIS_OBJECTIVE_AND_CLAIM_ALIGNMENT_REVIEW` |

### ⚠️ Một lỗi SẢN PHẨM lộ ra trước lượt live — và đó là lý do có bước này

`THESIS_FINAL_ACCEPTANCE_RUNNER_ALIGNMENT` chạy trọn bộ ca qua **đường thật**
với provider stub, và phát hiện `plane_equation.doc_phuong_trinh` chỉ đọc được
dấu trừ **ASCII**. Dấu trừ toán học `−` (U+2212) — thứ SGK và một mô hình chép
lại đề đã soạn đẹp sẽ phát ra — làm phép nở span **dừng giữa phương trình**,
biến `2x − z + 12 = 0` thành `z + 12 = 0`, rồi báo bất biến nguồn **vi phạm trên
một chương trình đúng**.

Đã sửa (`chuan_hoa_dau_tru`, ánh xạ 1:1). Hệ quả đo được:
`CANDIDATE_HASH ddeb0518… → d72db7c3…` (đóng băng lại), `CACHE_VERSION 94 → 94`
**không bump** vì bản vá chỉ đi chiều `rejected → served` và `main.py` chỉ cache
`status == "ok"` (`CACHE_IMPACT.json`). **0 hồi quy hình học.**

Điều này củng cố tuyên bố **C3** chứ không làm yếu nó: bất biến nguồn nay đọc
được kiểu chữ toán học bình thường. Nhưng nó cũng là một giới hạn phương pháp
phải khai: **gold preflight của wave trước KHÔNG đi qua `build_request_contract`**,
nên nó chứng minh một điều hẹp hơn thứ nó có vẻ chứng minh. Nhãn
`GOLD_CONTRACT_REACHABLE` nay bịt chỗ ấy.

### ⚠️ Ba điều PHẢI khai kèm mọi con số của lượt cuối

1. **Bộ này KHÔNG phải held-out.** Corpus xây trong kho, người triển khai đọc
   được. Mô hình không nhận gold program hay đáp số (`payload_gui_model()` trả
   đúng một trường `problem_text`, khoá bằng test) — nhưng *"mô hình chưa thấy"*
   khác *"người viết bộ đo chưa thấy"*.
2. **`PRODUCT_PROMOTION_ELIGIBLE = NO` là kết luận đã biết TRƯỚC**, cho mọi họ,
   bất kể kết quả: bộ ca có đúng một ca mỗi họ và chạy đúng một lần, nên
   `requires_stability_measured` không thoả được và
   `STABILITY_UNDER_ACCEPTANCE` giữ `NOT_MEASURED`.
3. **Hai RQ không có ngưỡng** (`RQ3` tự sinh, `RQ5` hiệu quả). Khoá luận chưa
   quy định ngưỡng học thuật cho hành vi mô hình; bộ đo **không tự đặt hộ**.
   Chúng được báo cáo **kèm mẫu số**, và policy cấm gọi một tỉ lệ trên 7 ca là
   *"độ chính xác của hệ thống"*.

### ⚠️ `KHOP_CANDIDATE_HIEN_TAI = 0`

Quét **113** artifact có danh tính trong `docs/evaluation/`: **không cái nào**
được sinh trên candidate `ddeb0518…`. Mọi con số live trong kho — kể cả những
con số bảng chính ở §1 dẫn lại — thuộc về một bản hệ **CŨ**; 90/113 thậm chí
không ghi candidate nào. Đó không phải khiếm khuyết (candidate vừa đổi cùng ngày
ở `OBLIQUE_CONE_SECTION_FOUNDATION`), nhưng nó là **lý do lượt cuối phải chạy**,
và là câu phải đi kèm mọi số dẫn lại từ artifact cũ.

### Giới hạn đo lường mới ghi nhận

| giới hạn | nội dung |
|---|---|
| `BOUNDARY_BY_ABSENCE_PROOF` | Hệ **không có** mã lỗi nào mang tên hai họ ngoài phạm vi. Ranh giới ca âm chứng minh bằng **vắng mặt** (quét mã, kiểm được bằng máy), không bằng một mã lỗi. `NEGATIVE_FAIL_CLOSED` là ngưỡng 2/2; `TARGET_BOUNDARY_DEMONSTRATED` được đo mà **không** đặt ngưỡng |
| `SCORER_CONTAINER_NAME_ONLY_HEURISTIC` | `nghia_vu_du_noi_dung_hut_ten` không phân biệt *đúng vật* với *một vật khác cùng kiểu*, nên một chương trình trả lời **bài khác** có thể bị xếp là lỗi HỆ. Không sai số đo ở ca âm; có thể sai ở ca dương |
| hai lớp ngoài scorer canonical | `MODEL_ANALYZE_FAILURE` và `SYSTEM_SCENE3D_FAILURE` **không** sinh ra được từ `phan_loai`; runner phải đếm riêng |

## 8. Lệnh kiểm lại (0 lượt gọi model)

```bash
cd backend && .venv/Scripts/python.exe scripts/replay_demo_cases.py
cd backend && .venv/Scripts/python.exe scripts/audit_demo_crash_surface.py
cd backend && .venv/Scripts/python.exe scripts/thesis_final_acceptance_plan.py
cd backend && .venv/Scripts/python.exe -m pytest -q
cd frontend && npx vitest run && npm run build
cd frontend && npm run dev          # cửa sổ khác, rồi:
cd frontend && node scripts/spot-check-demo.mjs
```
