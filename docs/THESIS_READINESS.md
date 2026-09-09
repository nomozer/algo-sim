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

## 3. Đính chính đã ghi (không hồi tố điểm)

| đính chính | nội dung |
|---|---|
| `translate` | **`CANONICAL_ERGONOMIC_PRIMITIVE`**, không phải năng lực tổng quát mới. `PRE_EXTENSION_SEMANTIC_EXPRESSIBLE = YES` — `divide_segment(R, midpoint(P,S), 2)` = `P + S − R`. Nó làm phép affine **dễ biểu diễn và dễ tổng hợp hơn**, không mở thêm thứ biểu diễn được |
| oracle `n3` | **không phân biệt được hai cách dựng**: `F = (0,4,2)` và `F = (0,12,−6)` cùng cho số 4. ⇒ **`n3` KHÔNG được dùng làm bằng chứng đúng đắn ngữ nghĩa.** Đây là lỗi của **artifact đánh giá**, không phải của sản phẩm — không sửa mã |
| `angle_cos_sq` | từng trả `sin²` cho cặp (đường, mặt); đã sửa, `ANGLE_SEMANTICS_ERRATUM.md` |

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
