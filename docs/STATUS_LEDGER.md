# STATUS_LEDGER.md — SỔ TRẠNG THÁI SẢN PHẨM

> **Luật của file này:** mỗi dòng phải trỏ tới **bằng chứng chạy được**. Không
> có bằng chứng ⇒ không được ghi DONE. Bằng chứng sinh từ commit khác HEAD ⇒
> `STALE_EVIDENCE`, cũng không được ghi DONE (`evidence.mjs::assertFresh`).
>
> Cập nhật ở CUỐI mỗi wave. Số sống vẫn ở `CURRENT_STATE.md`.

**HEAD lúc lập sổ:** `a3dac3b` (Wave 0–1 làm trên đó, commit ngay sau).

## 1. Kiến trúc & năng lực

| Owner / Feature | Trạng thái | Bằng chứng | Wave kế |
|---|---|---|---|
| Kiến trúc mô phỏng tất định (R0: LLM đọc đề, engine diễn hoạt) | **DONE** | bất biến #1–#3 + `algorithms.test.ts`, `generic.test.ts`; pytest 1212 | — |
| Danh mục 23 target / 12 family | **DONE** | `catalog_runtime_matrix.py` → 23 target, conformance/ownership/parity 0 | — |
| Đường AI sinh spec (analyze→classify→simulate→validate) | **DONE** | `test_pipeline`, `test_capability_boundary`; bất biến #22 | W2 (oracle mới) |
| Đường demo công khai (thư viện offline) | **DONE** | `sample-coverage-w4b3d.test.ts` | W3 (lọc phạm vi) |
| **Parity demo ↔ AI** | **DONE (W1)** | `generation-parity.test.ts` — 22 target × 4 nguồn pipeline; `docs/evaluation/m20/generation-parity.json` | — |
| Bố cục sân khấu dùng chung (khung theo cơ chế, một rail) | **DONE (M19)** | `audit-composition.mjs` 92/92 ở 4 bề rộng; bất biến #30 | W7 (tách transport) |
| Khay điều khiển (transport) | **PARTIAL** | cùng cột với thẻ nên co theo cơ chế; W7 muốn nó có bề rộng workspace ỔN ĐỊNH | **W7A** |

## 2. Tương tác học sinh theo miền

| Owner / Feature | Trạng thái | Bằng chứng | Wave kế |
|---|---|---|---|
| Thao tác trực tiếp HTML/CSS (chọn khối, đổi thứ tự) | **DONE** | `direct-manipulation-w4b4d.test.tsx`; mồi hai chiều | W9 (bàn phím/WCAG) |
| Truy vấn CSDL có ràng buộc | **DONE** | `query-first-w4b4b.test.ts` | — |
| Logic (bật/tắt đầu vào, lan truyền) | **DONE** | `dag.test.tsx`, `logic` domain tests | — |
| Điều kiện `count_if`/`sum_if` | **DONE** | `condition-param.test.ts`, `explore-ownership-w4b3a` | — |
| Trải nghiệm toàn danh mục | **PARTIAL — 20/23 thao tác được** | `w4b4a-experience/probe.json`, `VERDICT.md` | **W5F** |
| 3 target giữ trace có lý do cơ chế | **DONE (quyết định)** | `KEEP_TRACE` + guard hai chiều | W5F (rà lại) |
| RGB/CSS color (Tin 12) | **OPEN — chưa có target** | — | **W5A** |
| Nhãn giá trị vị trí theo cơ số | **OPEN** | — | **W5B** |
| Ký tự & mã hoá theo tham số | **PARTIAL** | đổi được `text`/`encoding` | **W5C** |

## 3. Sản phẩm & lớp học

| Owner / Feature | Trạng thái | Bằng chứng | Wave kế |
|---|---|---|---|
| Trang khách (không thanh bên, một ô nhập, dùng thử 1 lượt) | **DONE** | `accept-classroom-m18.mjs` 4 bề rộng | **W7C** (đổi bản sắc sang LAB) |
| Xác thực + vai trò do máy chủ sở hữu | **DONE** | `test_auth_api.py`, 6 ca từ chối của `§36` | — |
| Lớp · mã vào lớp · giao bài · thực hành | **DONE** | `test_classroom_api.py` | — |
| Giáo viên quan sát (trạng thái có cấu trúc, 5s) | **DONE** | bất biến #27; `accept-classroom-m18.mjs` | — |
| Giáo viên CẤP tài khoản học sinh | **MISSING** | — (khai ở `CLASSROOM_AUTH_CONTRACT §3`) | ngoài chương trình |
| Phiên dạy trực tiếp (bám theo · tự do · gọi cả lớp về) | **DONE** | `test_live_session_api.py`; `classroom-sync.test.ts`; `live-classroom-acceptance.json` 56/56, provenance FRESH | — |
| Giơ tay xin hỗ trợ + bảng theo dõi | **DONE** | cùng artifact, lát `4-help`; sắp xếp help-first **không** theo số click | — |
| Giao bài HÌNH HỌC (tuyến ngữ nghĩa) | **DONE** | `test_envelope_config_gate.py` 18 ca; lát `0-setup` của artifact | — |
| Giáo viên MỞ được bài mình giao | **DONE** | `assignment-open.test.ts`; lát `5-ui` (dock dựng trong xưởng) | — |
| Quản trị (token, cấp tài khoản hàng loạt) | **OPEN** | — (cố ý: chỉ thị wave cấm thêm admin) | chưa xếp |
| Bề mặt công khai = hình học (bỏ danh tính Tin học) | **DONE** | `PRODUCT_DOMAINS`; `catalog.test.tsx`; `product-scope-acceptance.json` 32/32 | — |
| 10 miền Tin học sau khi de-expose | **DE-EXPOSED, KHÔNG XOÁ** | vẫn đăng ký + mở lại được từ Lịch sử/bài đã giao; khoá bởi test «mẫu Tin học VẪN sống» | quyết định xoá: chưa xếp |
| Bảng điều khiển «lớp nào · bài nào» | **DONE** | `HomeWorkStrip` + `home-work-strip.test.tsx` | — |
| Tên đề tài trong README/RULES/COVERAGE | **THESIS_SCOPE_MISMATCH** | còn tuyên bố Tin học THPT — **không tự sửa**, cần quyết định ngoài code | chờ GVHD |
| Miền số chính xác `a·√b` | **DONE** | `geometry/radical.py`; `test_radical_domain.py` 66 ca | — |
| 5 ô khoảng cách (điểm–đường · điểm–mặt · đường–đường · đường–mặt · mặt–mặt) | **PARTIAL → SUPPORTED** | `test_radical_distance.py` 42 ca (đo · chấm đúng · chấm SAI được); `CAPABILITY_GAP_AUDIT §4b` | — |
| Tổng hai căn khác căn thức (`√2 + √3`) | **NGOÀI MIỀN, cố ý** | `add` fail-closed; khoá bởi `test_TONG_HAI_CAN_KHAC_NHAU_bi_tu_choi` | không mở |
| Toạ độ căn thức (ℚ(√d) thay cho ℚ³) | **UNSUPPORTED** | — kernel dựng trên ℚ³; đổi trường số là wave riêng | chưa xếp |
| Góc nhị diện có miền | **SUPPORTED (tổ hợp)** | `angle_cos` + `vector_from_points`; `test_signed_angle.py` 29 ca — KHÔNG primitive nhị diện | — |
| Tổng hợp nhị diện bằng LLM trong 2 lượt | **OPEN — 0/4** | `dihedral-probe-ergonomics`: token 83.337 → 68.004 qua ba lượt, nhưng chưa ca nào đạt | chưa xếp |
| Ma sát bề mặt IR (`declare_point` · `description` · `/` · prompt sửa) | **DONE** | `test_ir_ergonomics.py` 21 ca · `test_offline_replay.py` 12 ca | — |
| Thẩm quyền kiểu gom một nguồn | **DERIVED** | `validator._BIEU_THUC_HINH_HOC` sinh từ `_CHU_KY`; `test_type_authority.py` đọc AST | — |
| Gộp khai báo trùng khi nâng `declare_point` | **DONE — XÁC MINH LIVE** | `dihedral-probe-merge-verify`: khai trùng 4 ca → **0 ca**; `duplicate_equivalent_count` 5–6/ca, `conflict_count` 0 | — |
| Mâu thuẫn toạ độ khi gộp | **FAIL-CLOSED** | từ chối kèm cả hai toạ độ; `test_toa_do_MAU_THUAN_thi_FAIL_CLOSED` | — |
| Mô hình chọn `angle_cos` cho đề chỉ hỏi ĐỘ LỚN góc | **ĐÃ SỬA — 0/1 bẫy cắn** | `measure_contract` đưa KIỂU TOÁN HẠNG + ngữ nghĩa vào thẻ; prompt chọn bằng câu hỏi "kết luận có đổi khi đảo chiều không". `fresh-probe fp_2` có chữ "côsin" trong đề vẫn chọn `angle_cos_sq`, ra đúng. `PROMPT_BIAS_FAILURES = 0/6`. ⚠️ n=6, phương sai 2 ca giữa hai lượt — xem `FRESH_PROBE_REPORT §3` | — |
| Thẩm quyền kiểu của `measure` rải ba chỗ | **DONE** | `measure_contract.BANG_PHEP_DO` — `_KIEU_DO` dẫn xuất, validator đọc bảng, thẻ render bảng; `test_measure_contract.py` 15 ca | — |
| Bộ đo truyền chuỗi miền lạ ⇒ đo hình học bằng prompt TIN HỌC | **ĐÃ SỬA** | `program_skill_for("geometry")` → `semantic_program`. Matrix + 6 probe nhị diện dính; `dev-results` thì không. Artifact KHÔNG hồi tố, 3/9 giữ nguyên. Guard: `test_domain_string.py` quét mọi `scripts/*.py` | — |
| `angle_cos_sq` trả **sin²** cho cặp (đường, mặt) | **ĐÃ SỬA** | `measure.cos_sq_giua` — một thẩm quyền, cos² ở cả bốn cặp; bộ chấm thôi mang bản sao. Replay `fp_5` cùng JSON: 1/3 → **2/3**, khớp oracle. `test_angle_semantics.py` 27 ca, mọi ca dùng góc 0°/90° vì 45° không phân biệt được cos² với sin². Migration: 1 ca duy nhất, nằm trong artifact lịch sử; pool holdout KHÔNG sửa (hai ô A10 ở 45°, điểm bất động). Xem `ANGLE_SEMANTICS_ERRATUM.md` | — |
| Bảng nghĩa vụ trong prompt quảng cáo từ vựng KHÔNG viết được | **ĐÃ SỬA** | Bề mặt tổng hợp thôi nhắc `perpendicular`/`parallel`/`coplanar`/`witness`/`obligations`; đề "chứng minh" nay được dạy: dựng vật rồi dừng, engine kiểm. `test_contract_self_check.py` 14 ca — mọi định danh trong backtick của prompt+thẻ phải có trong schema | — |
| Hạt giống chạy lại được cho phép đo độ ổn định | **DONE — INPUT_EQUIVALENCE PASS 6/6** | `stability-seed/seed.json` trên `f774a332`, 12/12 lượt provider (6 analyze + 6 tổng hợp, **0 sửa**). Kiểm HAI chiều từ đĩa, 0 provider: payload tự chứa **và** dựng lại từ mảnh đều khớp hash. `test_probe_artifact_replayable.py` chạy lại phép kiểm ấy trong suite — không đọc cờ artifact tự ghi. repeat_1 = 4/6, **KHÔNG so với V2 6/6** (khác điều kiện: không có lượt sửa) | — |
| `construct_point.expr` nhận `arith` — lần thứ BA | **QUAN SÁT, chưa hành động** | 2/6 ca của hạt giống hỏng schema vì mô hình đặt biểu thức số học vào `construct_point`. Đã ghi ở `CACHE_VERSION 46` (hai vòng đo độc lập) và ở `cb_04` của V1 (bắt bởi `AMBIGUOUS_FIRST_BINDING`). Chỉ thị cấm sửa prompt trong wave chụp hạt giống | chưa xếp |
| Độ ổn định tổng hợp trên bộ V2 (k=3) | **MIXED — 9/18, 0 lỗi hệ** | `stability-k3/stability.json` trên `550bb00c`. 12 lượt provider, 0 analyze, 0 sửa; `INPUT_HASH_PRE_SEND` PASS 12/12 (băm và đối chiếu TRƯỚC khi gửi). `CASE_AT_LEAST_2_OF_3 = 3/6`, `SYSTEM_FAILURE = 0/18`, `FIRST_BINDING_RUNTIME_FAILURES = 0/18`. Ngưỡng chốt trước lượt đo | — |
| ⛔ **CHỐT PHẠM VI 2026-09-01 — BENCHMARK ĐÓNG** | `SYNTHESIS_BENCHMARKING = CLOSED` · `TRANSLATION_EVIDENCE = CLOSED` · `NAME_ONLY_EVIDENCE = CLOSED` · `ANALYZE_STABILITY = NOT_MEASURED_BY_SCOPE_DECISION` | `docs/THESIS_READINESS.md` — bảng đối chiếu tuyên bố ↔ bằng chứng ↔ giới hạn DUY NHẤT của khoá luận. **Không** k=3/k=5/fresh probe/stability seed nữa. Đề tài không nghiên cứu độ ổn định thống kê của trích xuất thông tin; `ANALYZE_STABILITY` dừng vì **phạm vi**, không vì thiếu điều kiện (điều kiện cũng thiếu — xem dòng artifact analyze) | — |
| Tập DEMO của khoá luận | **DONE — 5/5, 0 lượt gọi model** | `scripts/replay_demo_cases.py`: `n1` (√3) · `n2` (lăng trụ xiên, 3√3) · `t3` (dây chuyền tịnh tiến, 3√89/5) · `t4` (2√2) đi trọn chuỗi schema→tĩnh→grounding+trung thực→chạy→checker→transport→Scene3D; `n4` là **ca TỪ CHỐI cố ý** (bị chặn đúng ở grounding). Thiết diện `v2_04` chạy RÚT GỌN riêng (artifact V2 không lưu hợp đồng), **không gộp** vào 5/5 | — |
| Đường 500/crash trên luồng demo | **KHÔNG CÓ — 6/6 biên, 0 đường ném** | `scripts/audit_demo_crash_surface.py`: toạ độ ký hiệu · sai kiểu toán hạng · ràng buộc lần đầu (chạy được sau chuẩn hoá) · ràng buộc trong nhánh · toạ độ thô ở ô TÊN · rửa năng lực qua biểu thức lồng. Sáu biên ĐÃ từng hỏng thật, không phải fuzzing | — |
| ⛔ Gỡ mã Tin học khỏi tuyến đang chạy | **CHẶN — đã thử, đã đo, đã hoàn nguyên** | `docs/SCOPE_ALIGNMENT_AUDIT.md`. Audit đồ thị chứng minh 9 domain frontend gỡ được (geometry/semantic không nhập một dòng nào từ chúng). Nhưng **hai chặn cứng**: ① `run_pipeline` gọi `stage_analyze` Tin học TRƯỚC, tuyến hình học là nhánh **shadow** bên trong — bỏ `CATALOG` = viết lại bộ điều phối, tức refactor (§17 cấm) và đổi hành vi hệ ĐANG ĐƯỢC ĐO (§12 cấm xác nhận bằng lượt gọi thật); ② bài mẫu offline **100% Tin học, 0 bài hình học** — xoá là thư viện sản phẩm RỖNG, mà tạo mẫu mới là việc §17 cấm. Đo thật khi thử: **30 test frontend hỏng**, **73/249 test backend** chạm `catalog`/`dsl`, và `capability-descriptors.test.ts` khoá target backend ↔ module frontend SONG ÁNH 1:1 ⇒ hai phía phải đi cùng một wave. Kế hoạch 7 bước có thứ tự ở audit | chưa xếp |
| README mô tả ĐỀ TÀI CŨ | **ĐÃ VIẾT LẠI TOÀN BỘ** — thay dòng dưới | 281 dòng, **0 lần nhắc hình học**, tiêu đề vẫn "hỗ trợ dạy học môn Tin học THPT" trong khi đề đổi từ 2026-08-24. Thêm khối PHẠM VI ở đầu: đề hiện tại, thứ được/không được tuyên bố, trỏ `THESIS_READINESS.md`. Viết lại 13 mục thân bài = việc tài liệu, xếp FUTURE_WORK | chưa xếp |
| `tên<T>` có đổi được cách mô hình VIẾT không | **STRONG — 42/42 ô đúng ngay bản THÔ** | `name-contract-probe/probe.json` trên `bc8b06c`, 4 đề mới, 8/8 lượt, **0 lượt sửa**. `RAW_NAME_COMPLIANCE_RATE = 1.0`: 0 bọc `var`, 0 lồng, 0 toạ độ thô, 0 sai kiểu — bộ chuẩn hoá KHÔNG phải làm gì (0 gỡ bọc, 0 nâng, 0 temp, 0 ca được cứu). `ONE_SHOT_CORRECT = 2/4` nhưng **không lỗi nào là lỗi ô TÊN** ⇒ `SYSTEM_ERGONOMICS = MIXED`. Artifact chạy lại được 4/4 (tầng tổng hợp) | — |
| ⚠️ Oracle của `n3` KHÔNG phân biệt được lời giải sai | **NỢ CỦA BỘ ĐỀ, đã khai** | Chẩn đoán offline 0 lượt: mô hình đọc *"SF = 2FD"* thành tỉ lệ `2` ⇒ `F = (0,12,−6)` thay vì `(0,4,2)`, **vẫn ra đúng số 4**. Đã thay oracle `n3` MỘT LẦN trước khi seal vì đúng lý do ấy và bản thay vẫn chưa đủ. Không làm sai con số nào đã báo (n3 hỏng ở schema trước đó), nhưng nếu mô hình viết `"2"` thành chuỗi thì n3 đã được ghi ONE_SHOT_CORRECT với hình dựng sai | chưa xếp |
| `literal` bọc quanh VÔ HƯỚNG ở `divide_segment.ratio` | **OPEN — quan sát, chưa hành động** | `n3` hỏng schema vì `{"kind":"literal","value":2}` ở `ratio`. Đó là ô VÔ HƯỚNG, không phải ô TÊN, nên `GeometryName` không phủ. Cùng lớp `canonical_const_int` đã vá cho `for_range.step` (2026-08-24), chưa vá cho miền hình học | chưa xếp |
| `analyze` bỏ sót dữ kiện TOẠ ĐỘ | **OPEN — chưa đo được, chặn bởi artifact** | `n1` 4 fact (3 toạ độ), `n2` 7 fact (4 toạ độ), **`n3`/`n4` 3 fact và KHÔNG toạ độ nào**, trên bốn đề nêu toạ độ cùng kiểu. Nguyên nhân gần của thất bại grounding duy nhất: `n4` không có fact để trích nên viết chính chữ trong đề (`source_fact_id: "A(0; 0; 0)"`). Wave đo độ ổn định phải **DỪNG ở cổng §1, 0 lượt provider** — xem dòng dưới | chưa xếp |
| ⚠️ Artifact KHÔNG ghi đầu vào của `analyze` | **CHẶN — dừng trước API, 0 lượt tiêu** | `analyze-fact-stability/PREFLIGHT_STOP.md`. `probe.json` lưu `raw_request_contract` + `request_contract_hash` — đều là ĐẦU RA; không `payload`, không `model_input_hash`. Dựng lại được payload (tất định từ `problem_text` + commit đóng băng, 4 hash phân biệt) nhưng **không có vế thứ hai để so** ⇒ cổng exact-input thành phép tự-khẳng-định. **BẤT ĐỐI XỨNG**: tầng tổng hợp CÓ đủ và kiểm được (`tự chứa 4/4, dựng lại 4/4`) — hàm bao chụp payload ở nhánh `SYNTHESIS` và chỉ chuyển tiếp ở nhánh `ANALYZE`. Là **lần thứ hai** của cùng lớp lỗi đã chặn `CLEAN_BASELINE_V2_SYNTHESIS_STABILITY`; bản vá khi ấy làm cho tầng tổng hợp và không kéo xuống analyze | chưa xếp |
| Mô hình có TỰ TÌM RA `translate` không | **MIXED — 4/4 đúng, 3/4 chọn ngay lượt đầu** | `translation-probe/probe.json` trên `397f24f6`, 4 đề mới, 10 lượt provider. **`ARITH_POINT_VECTOR_REAPPEARED = 0`** — khuôn giết 9/9 lượt hỏng của k=3 nay biến mất hoàn toàn. `SYSTEM_FAILURE 0/4`, artifact chạy lại được 4/4, spot check 8/8. `ONE_SHOT 2/4` nên chưa STRONG | — |
| ~~Mô hình LỒNG biểu thức vào toán hạng vectơ~~ | **ĐÃ SỬA — nâng tất định, R0 nguyên vẹn** | `named-operand-ergonomics/REPORT.md`. Thẻ nay in `tên<T>` ở 30 ô (dẫn từ `hoisting.O_TEN`), prompt nói luật bằng MỘT câu khẳng định, và hai biên chuẩn hoá nhận thứ mô hình thật sự viết: `hoisting` nâng biểu thức dựng lồng thành ràng buộc có tên, `canonical_geometry_name` gỡ bọc `{"kind":"var"}`. Chạy lại lịch sử: **23/23 chuẩn hoá được, 0 từ chối**; hai chương trình hỏng của probe chạy trọn chuỗi cổng VÀ khớp oracle. `NEW_GEOMETRY_CAPABILITY = NO`, `LLM_CALLS = 0`, điểm lịch sử KHÔNG đổi | — |
| ⚠️ Ma sát ĐÔNG NHẤT không phải biểu thức lồng | **ĐÃ SỬA — 16/23 là `var` bọc quanh một TÊN** | Audit `audit_named_operand_ergonomics.py` đếm trên artifact đã commit: 7 lần lồng biểu thức thật, **16 lần** `{"kind":"var","name":"Q"}` ở `through_a`/`of`/`wrt`/`through[]`. Đúng lớp lỗi `canonical_container_name` vá cho miền Tin học từ 2026-08-23; ô hình học là `str` trần nên chưa ai vá. Hai cơ chế tách rời: nâng (sinh temp) vs gỡ bọc (1:1, không temp) — gộp chúng vào một con số là báo cáo sai chuyện đang xảy ra | — |
| Toạ độ KÝ HIỆU đi thẳng tới kernel | **ĐÃ SỬA — bắt ở thẩm định TĨNH** | `at: list[Any]`/`initial_value: Any` nhận `[{"kind":"var","name":"a"}, 0, 0]` — mô hình nói *"cạnh đáy là a"*, kernel ném `ZERO_VECTOR` ở RUNTIME nơi vòng sửa không với tới. Lỗ VỐN ĐÃ CÓ, bị một lỗi schema khác che ở `dihedral-probe-ergonomics`; lượt chạy lại lịch sử làm nó lộ ra. Nay câu ③ (*số hữu tỉ chính xác*) áp cho toạ độ chứ không chỉ `ratio` — `_kiem_toa_do`, dùng lại `_la_huu_ti` + `IR_NOT_EXACT_RATIONAL`. Không thêm năng lực. **Mô hình vẫn chưa có cách nói *"cạnh a"*** — câu hỏi thiết kế, không phải lỗ | chưa xếp |
| `construct_plane.through` bọc CẢ DANH SÁCH | **OPEN — quan sát, chưa hành động** | `{"kind":"literal","value":["A","B","C"]}` thay vì ba tên. `list[GeometryName]` gỡ bọc từng PHẦN TỬ, không gỡ được lớp bọc ngoài. Đã quan sát trong artifact lịch sử | chưa xếp |
| ⚠️ **ĐÍNH CHÍNH: `translate` KHÔNG phải khoảng trống năng lực** | **SỬA LỜI KHAI, KHÔNG SỬA MÃ** — phân loại chốt: `PRE_EXTENSION_SEMANTIC_EXPRESSIBLE = YES`, `translate` = **`CANONICAL_ERGONOMIC_PRIMITIVE`**, KHÔNG phải `NEW_GENERAL_CAPABILITY` | Wave trước báo `PRE_EXTENSION_EXPRESSIBLE = NO`. **Sai.** Audit hỏi câu KIỂU (*"phép sinh điểm nào nhận `vector3`?"* — đúng là KHÔNG) rồi dùng nó trả lời câu NGỮ NGHĨA. Tổ hợp có thật trong IR cũ: `M = midpoint(P,S)` rồi `Q = divide_segment(R, M, 2)` = `P + S − R`, đúng bằng `translate(P, vector_from_points(R,S))`. Đã kiểm chạy. ⇒ `translate` là phép **dễ tìm và đúng nghĩa**, không phải năng lực mới. Đánh đổi vẫn thật: đường vòng dùng tỉ lệ `2` để đi RA NGOÀI đoạn, trong khi hợp đồng `divide_segment` khai `t=0 → A, t=1 → B` — chạy được nhưng nói dối về việc nó làm gì | — |
| **IR thiếu phép TỊNH TIẾN ĐIỂM** | **ĐÃ SỬA — `translate(point3, vector3) → point3`** | ⚠️ đọc dòng ĐÍNH CHÍNH ngay trên trước. Ở mức KIỂU: 0 phép sinh điểm nhận vectơ, 0 câu lệnh dựng đường/mặt từ điểm + phương. `vector3` từng là kiểu **chỉ-ghi**. Nay `_CHU_KY` + cả hai union + kernel + thẻ, tất cả dẫn từ một thẩm quyền. `test_translate.py` 26 ca gồm lồng hai lần, đảo chiều, phân số, và làm đầu vào cho đường/mặt/chiếu/đo. §17 replay: **6/6 chương trình · 12 câu lệnh** từ schema-hỏng sang chạy được — KHÔNG tính là thành công hồi tố | — |
| ~~IR thiếu phép tịnh tiến — OPEN~~ | **ĐÃ GỠ** | 9/9 lượt hỏng của k=3 đều là SCHEMA, và **10 lần cùng một hình dạng**: `construct_point X = arith(+, var(P), vector_from_points(A,B))` — *"tịnh tiến P theo vectơ AB"*. Đó là cách duy nhất tự nhiên để dựng `C` hình bình hành và `B'`,`C'`,`D'` của lăng trụ/hộp; `PointExpr` có 5 phép, không phép nào là tịnh tiến. Mô hình đang cố **DỰNG** thay vì **KHAI** — tôn trọng R0 chặt hơn thứ IR cho phép. `grounding_gate` Wave 5 đã ghi khoảng trống này rồi bỏ quên. Hai đề không cần tịnh tiến (`v2_01`, `v2_06`) đều 3/3 STABLE | chưa xếp |
| Bằng chứng AI TỔ HỢP, không chép khuôn | **XÁC NHẬN** | k=3: `v2_01` và `v2_06` mỗi ca 3/3 đúng với **3 chương trình khác nhau** trên cùng byte đầu vào. `ALTERNATIVE_VALID_COMPOSITIONS = 3/6`, 9 chương trình chuẩn hoá khác nhau trên 18 quan sát. Khác hash KHÔNG phải bất ổn — thứ cần ổn định là tính đúng ngữ nghĩa | — |
| ~~Độ ổn định tổng hợp trên bộ V2 — sẵn sàng chạy~~ | **ĐÃ CHẠY** | Hạt giống đã đủ; lượt sau cần 0 analyze + 6 R2 + 6 R3 + 0 sửa, và phải khẳng định `MODEL_INPUT_HASH` khớp R1 trước khi gửi. ~~chặn bởi artifact~~ | chưa xếp |
| ~~Độ ổn định tổng hợp trên bộ V2 — chặn bởi artifact~~ | **ĐÃ GỠ CHẶN** | `probe.json` ghi hợp đồng dạng TÓM TẮT (`{hash, số fact, tập nghĩa vụ}`), không dựng lại được đầu vào tổng hợp: prompt nhúng `id`/`nhãn`/`giá trị` từng dữ kiện. Gom `source_fact_id` từ chương trình cũng thiếu — `v2_02` có 6 dữ kiện, mô hình chỉ trích dẫn 4. §3 của chỉ thị đòi DỪNG trước API trong ca này, và cấm gọi analyze để vá. **0 call đã tiêu.** Đã sửa bản ghi (`ghi_hop_dong` lưu `raw`) + guard `test_probe_artifact_replayable.py`; cần chạy lại V2 để sinh artifact đủ | chưa xếp |
| Baseline tổng hợp sau bản sửa ràng buộc lần đầu | **CLEAN_BASELINE_V2 — 6/6, STRONG** | Seal `adbb0ca9` trên `c1e0f672`, 6 đề mới, đường sản phẩm đầy đủ. one-shot 5/6 · SYSTEM_FAILURE **0/6** · FIRST_BINDING_RUNTIME_FAILURES **0/6** · `NEW_CODE_REQUIRED = 0` · spot check 8/8. **Con số quan trọng nhất không phải 6/6**: `construct_point` được chọn **12/12 lần**, chuẩn hoá không phải ra tay lần nào — V1 là 0/12. Điều đổi là THẺ, không phải mô hình. ⚠️ n=6, bộ đề cố ý tránh hai giới hạn đã khai, không đo k>1 | — |
| Baseline tổng hợp hình học đo ĐÚNG hệ | **CLEAN_BASELINE_V1 — 2/6 (lịch sử)** | 6 đề mới, seal `fa00ac08` trên `6ffb0753`, đường sản phẩm đầy đủ (có analyze), tiền kiểm miền PASS. 0 ca hỏng vì schema/grounding/trung thực/tổng hợp; 4/6 hỏng ở runtime cùng MỘT nguyên nhân. Spot check trình duyệt 8/8. `NEW_CODE_REQUIRED = 0`. KHÔNG so trực tiếp với matrix 3/9 hay fresh probe 4/6 — hai lượt ấy đo hệ khác | — |
| `assign` hình học không khai bị chặn ở SAI TẦNG | **ĐÃ SỬA** | `contract._rang_buoc_lan_dau` chuẩn hoá trước runtime: sinh ĐIỂM → viết lại thành `construct_point` (dạng chuẩn tắc, có sẵn memory + provenance); sinh vectơ/đường → giữ `assign` + bổ sung khai báo, kiểu dẫn từ `_CHU_KY`. Thẩm định tĩnh nay từ chối hai ca không nâng được: `CONDITIONAL_UNINITIALIZED_TARGET` (ràng buộc trong nhánh) và `AMBIGUOUS_FIRST_BINDING` (`assign C = arith(...)` làm điểm). Replay 6 chương trình thô: **0/6 còn chết ở runtime**, 5/6 chạy đúng oracle offline. `test_first_binding.py` 16 ca gồm phép tiêm lỗi | — |
| **Thẻ hình học GIẤU MẤT `construct_point`** | **ĐÃ SỬA — nguyên nhân gốc thật sự** | Thẻ dẫn từ `_TOAN_HANG_LENH`, bảng **cố ý** không chứa `construct_point` (toán hạng của nó nằm trong `expr`). Nên mô hình không chọn nhầm giữa hai lối — nó dùng lối DUY NHẤT được bày ra, và lối ấy chết ở runtime. 4/6 ca `CLEAN_BASELINE_V1` mất vì một cái tên vắng mặt trong một danh sách. Nay dẫn từ `_KIEU_DUNG` (bảng *"câu lệnh nào SINH RA vật gì"*) | — |
| `assign` hình học mất producer | **ĐÃ SỬA** | `_provenance` chỉ xử `assign` khi biểu thức là `measure`; `vector_from_points`/`intersect_plane_plane` mang `producer: null`. Nay phủ mọi biểu thức hình học — mất producer là cảnh 3D thôi kể *nó được tạo ra thế nào* | — |
| `construct_section` khi mặt phẳng cắt **chứa trọn một CẠNH** của khối | **DONE — `SECTION_COPLANAR_EDGE_GAP` CLOSED 2026-09-02** | Nguyên nhân: cạnh đồng phẳng thuộc HAI mặt kề nên cả hai cùng báo một đoạn giao; vòng nối vấp bản sao rồi đổ lỗi cho bảng mặt. Sửa bằng khử trùng theo cặp đầu mút chính xác. Bằng chứng: `tests/geometry/test_section_coplanar_edge.py` (19 ca, khẳng định theo TÔ-PÔ) · `frontend/scripts/certify-section-coplanar-edge.mjs` 7/7 trong Chrome thật · bài mẫu offline `mat-cheo-sac`. Kèm theo: thông điệp lỗi thôi đổ tội bảng mặt, và mặt phẳng trùng một mặt nay cho ra chính mặt ấy | — |
| Hoà giải tên khi ĐỈNH của một mặt bị đổi tên | **OPEN — giới hạn đã biết** | Hợp đồng gọi mặt là `(PMN)`, tức định danh bằng chữ cái các đỉnh. Đổi tên `P`,`M`,`N` thì phép hoà giải mất đường. Fixture `test_validator_name_normalization` nay giữ nguyên tên mà hợp đồng nhắc tới — đúng nguyên tắc docstring của nó, không phải nới bất biến | chưa xếp |
| Bộ đo dựng envelope hình học thiếu `scene3d` | **ĐÃ SỬA (bộ đo)** | `compile_semantic_program_to_envelope` một mình cho ra envelope 2D; cảnh 3D do `pipeline._dung_scene3d` đổ. Spot check đỏ 6/8 với 0 lỗi console — chỉ câu hỏi trình duyệt mới lộ ra | — |
| Thẩm quyền phép phân phối góc bị chép hai bản | **DONE** | `geometry_exec._do` và `geometry_obligations.check_angle` cùng gọi `cos_sq_giua`; guard đọc AST (`than_ma`) nên không khớp chính chú thích của nó | — |
| Envelope hình học có `value_box` KHÔNG serialize được | **ĐÃ SỬA** | `semantic_program/transport.py` — một thẩm quyền + cổng `check_envelope_transport` chạy trước cổng bề mặt; `test_transport_boundary.py` 24 ca, đã tiêm lại bug thấy 4 ca đỏ; spot check 12/12 trên envelope thật | — |
| Đề NGOÀI năng lực (mặt cầu) không bị chặn theo đúng lý do | **ĐÃ SỬA** | `UNANCHORED_DERIVED_ASSUMPTION` + `DERIVED_ENTITY_WITHOUT_PRODUCER` ở tầng grounding (TRƯỚC thực thi, khoá bởi `test_chan_TRUOC_khi_thuc_thi_khong_phai_sau`); `test_capability_honesty.py` 43 ca gồm replay `gm_10` thật, 8 tên thay thế, 5 khuôn giấu đáp án, 7 chứng cứ dương. Soát lại matrix: `gm_03` mang cùng bệnh (`P_parallel`) — **điểm 3/9 KHÔNG đổi**, cả hai vốn đã fail, nhưng fail vì thiếu `source_fact_id` tức chết tình cờ | — |
| Điểm phụ đề CÓ NÊU nhưng khai bằng toạ độ | **ĐÃ SỬA (một phần)** | `nhan_suy_ra` bắt *"Gọi H là…"*, *"M là trung điểm"*; `test_de_TANG_TEN_cho_diem_phu_thi_van_phai_DUNG` + đối chứng dựng-thì-qua. **Giới hạn khai thẳng:** khớp mẫu chữ, không phân tích cú pháp — lối viết ngoài mẫu vẫn lọt | chưa xếp |
| Sinh mô phỏng từ đề chưa từng thấy (10 đề, 7 topology) | **3/9 live · 7/9 chương trình đúng** | `generalization-matrix/matrix.json` + `matrix-offline-reanalysis.json`; spot check trình duyệt 12/12 | — |
| Tiếp tục ở nhà | **PARTIAL** | khôi phục BẢN GHI tiến độ, KHÔNG khôi phục state engine | W5F |
| Vỏ ứng dụng theo vai trò | **DONE** | `ux-shell.test.tsx`, `accept-classroom-m18.mjs` | W7D |

## 4. Đo lường & chất lượng

| Owner / Feature | Trạng thái | Bằng chứng | Wave kế |
|---|---|---|---|
| **Xuất xứ bằng chứng (dấu HEAD)** | **DONE (W0)** | `scripts/evidence.mjs`; đã gắn 3 script | — |
| Bằng chứng cũ trước W0 | **STALE_EVIDENCE** | không mang `head` ⇒ phải sinh lại trước phán quyết cuối | W14 |
| Dataset đánh giá AI 30 case | **DONE, đã đổi vai (W2)** | `LEGACY_AI_COMPOSITION_REGRESSION` — còn nguyên 30 case, hết làm thước đo phủ | — |
| Benchmark theo chương trình học | **DONE (W2/W2A/W2B/W2C)** | `curriculum_schema.py` + `metamorphic.py` + `product_scope.py`; `test_curriculum_benchmark.py` 23 test; `docs/evaluation/m20/curriculum-benchmark.json` | W3 dùng làm oracle |
| Phép đếm phủ từng nói dối | **ĐÃ SỬA (W2A)** | đếm chuỗi thô ⇒ 14 đơn vị (6 là câu ghi chú); rút regex ⇒ `T10.CD1` 12 case. Thật: **8 đơn vị**, `T10.CD1` 9–24 tùy pool | — |
| Cổng phạm vi + khả-mô-phỏng | **DONE (W3)** | `simulation/scope_gate.py` — cổng thứ NĂM, trước đường generic; `test_scope_gate.py` 15 test + 4 phép tiêm lỗi | — |
| Phán quyết phạm vi do LLM sở hữu (lỗ R0) | **ĐÃ BỊT (W3)** | trước W3, đề ngoài môn chỉ bị chặn khi `classify` tự từ chối; nay LLM KHAI, server PHÁN | — |
| Lời từ chối cho học sinh | **DONE (W3)** | 3 hạng mục riêng: `out_of_scope` · `not_simulation_suitable` · ngoài danh mục — không hứa sai “sẽ mở rộng dần” | W12 (soát ảnh) |
| Chứng nhận từng target | **PARTIAL (W4)** | manifest `target-certification.test.ts` — 4 cổng ĐỀU ĐÃ có chủ; ghi rõ cổng nào CHƯ A có bằng chứng tươi | W12 (sinh lại bằng chứng trình duyệt) |
| Join target ↔ đơn vị chương trình | **DONE (W4)** | 22/23 có bằng chứng, dẫn xuất từ case; ngoại lệ `binary.base_conversion` (cơ số 8/16 ngoài neo SGK) | — |
| Hai hệ ký hiệu neo trong cùng kho | **ĐÃ BẮC CẦU (W4)** | catalog ghi số BÀI, benchmark ghi mã CHỦ ĐỀ — join qua case thay vì chép tay SGK | W13 (hợp nhất?) |
| Kim tự tháp test (T0–T3) | **OPEN** | hiện chỉ có "chạy hết" | **W8** |
| Nghiệm thu trình duyệt 4 bề rộng | **DONE** | composition + classroom + experience | W12 (mở rộng) |
| Hook chất lượng phân biệt SVG vs HTML | **OPEN** | false positive đã xác định ở `ArrayView` | **W10** |
| Mặt phẳng đề cho bằng PHƯƠNG TRÌNH có biểu đạt được TRUNG THỰC không | **XONG — `PLANE_FROM_EQUATION_FOUNDATION = CLOSED`** (2026-09-07, `PLANE_FROM_EQUATION_REPRESENTATION`) | **`APPLICATION_LLM_CALLS = 0`.** `ROOT_CAUSE`: IR không có phép dựng mặt phẳng từ phương trình ⇒ ba lối biểu đạt, **một lối chạy được**, và lối ấy đòi gắn `source_fact_id` vào **toạ độ đề KHÔNG HỀ NÊU** — hệ buộc mô hình khai xuất xứ không trung thực để đi được. Chữa nguyên nhân (thêm phép) thay vì nới grounding: nới là làm yếu một cổng đang gác đúng, và vẫn để mô hình phải tự chọn ba điểm. `NEW_MEMORY_TYPES = 0 · NEW_IR_OPERATIONS = 1 · NEW_PER_PROBLEM_MODULES = 0`. **Kernel giữ biểu diễn**: `Plane3.from_equation` đặt CẠNH `Plane3.through` — đây là phép dựng mặt phẳng THỨ HAI và nó phải sinh CÙNG một `(point, normal)`; để tầng IR tự chọn điểm neo là dựng thẩm quyền thứ hai về *'mặt phẳng là gì'*. Điểm neo canonical dồn `−d` vào trục đầu tiên có hệ số khác 0 (`a≠0 → (−d/a,0,0)` · `a=0,b≠0 → (0,−d/b,0)` · `a=b=0 → (0,0,−d/c)`) ⇒ **toạ độ ở lại ℚ³**, không phép chia nào cho một căn. KHÔNG chuẩn hoá độ dài (rời ℚ) và KHÔNG chuẩn hoá dấu (quy ước không tầng nào cần) — phương trình tỉ lệ cho hai `Plane3` khác DỮ LIỆU nhưng bằng nhau về HÌNH, và mọi tầng sau chỉ hỏi `signed_eval == 0`. Suy biến `(a,b,c)=(0,0,0)` → `PLANE_EQUATION_DEGENERATE` ở **HAI tầng**: lược đồ (lỗi đi ngược về mô hình qua vòng sửa) và kernel (tiền điều kiện của một hàm CÔNG KHAI phải do chính nó giữ); phép tiêm ② chứng minh là hai tầng chứ không nhân đôi thẩm quyền. **Hệ số là SỐ, không phải TÊN** — khác `construct_curved_solid.radius` có chủ đích: bán kính là một ĐỘ LỚN nên grounding đòi nó truy về đề, còn bốn hệ số là **nguyên văn con số trong câu đề** và cùng nhau xác định một VỊ TRÍ. Miền `int | chuỗi phân số`, cùng miền `divide_segment.ratio`; `int` có mặt vì **đó là thứ mô hình thật sự viết** (đo ở attempt 1). ⚠️ **Grounding KHÔNG hỏi bốn hệ số câu nào** — nó chỉ soi `memory_declarations`, còn hệ số nằm trong CÂU LỆNH. Nên phép gác là **`SourceInvariant kind="plane_equation"`**: SERVER tự đọc phương trình từ câu văn của đề rồi so **TỈ LỆ CHÍNH XÁC** (định thức con 2×2, nhân chéo, không phép chia, không dung sai) với mặt phẳng có thật trong **trạng thái cuối**. Nguyên văn lập luận `check_source_invariants` đã dựng cho `segment_length`: *'cổng chạy trên dữ liệu server tự phát, nên không có đường nào để một chương trình tránh bị kiểm bằng cách im lặng'*. Nó hỏi **trên HÌNH, không trên câu lệnh**, nên **phủ luôn đường dựng ba điểm cũ** — gold ba điểm `checked=1 passed=1`, ba điểm dựng SAI mặt phẳng thì `violated=1`. Không cửa sau. ⚠️ **CA ĐẮT NHẤT của wave, và là lý do tầng bất biến không bỏ được**: `2x − z + 11 = 0` **SONG SONG** với mặt phẳng đề cho nên thiết diện elip **BẰNG HỆT** — cùng `16π√5`, đúng đáp số. Mọi cổng hỏi *đáp số* đều xanh; hình thì sai chỗ. Phép tiêm ③ đo thẳng cái giá: gỡ bất biến ⇒ ca ấy **`served`** kèm đáp số ĐÚNG và **không cổng nào kêu**. ⚠️ **Bộ đọc phương trình có HAI lỗi THẬT, bắt được bằng test TRƯỚC khi nhập** — ghi ra vì cả hai là lớp lỗi 'nở theo tập ký tự mà không hỏi biên': *'Diện tích mặt phẳng **đáy** = 12'* đọc thành mặt phẳng `y − 12 = 0` (chữ `y` của *'đáy'*); và nặng hơn hẳn, *'(α): 2x + **m**y − z + 10 = 0'* đọc thành `y − z + 10 = 0` — một phương trình **KHÁC HẲN** đề, tức **một mặt phẳng SAI được đem đi đối chiếu**, không phải một cảnh báo thừa. Bản sửa: biên bẩn (chữ cái dính liền) ⇒ **nuốt trọn cụm chữ cái** để chuỗi mang theo thứ làm nó không đọc nổi, rồi phân xử bằng **BIẾN ĐỘC LẬP** (`x`/`y`/`z` không dính chữ cái hai bên): có biến mà không đọc được ⇒ **CHẶN** (`plane_equation_unresolved`, cùng khuôn `segment_division_unresolved`); không có biến ⇒ **IM LẶNG**. Chặn oan một LỚP đề còn tệ hơn bỏ sót một phép kiểm, nên *'diện tích mặt phẳng đáy'* phải im lặng chứ không chặn. Ngưỡng còn hẹp ở hai chỗ nữa: chỉ tuyến tính Cartesian `x,y,z` hệ số hữu tỉ, và phải có **cụm chỉ mặt phẳng** trong 48 ký tự trước dấu `=`. **REPLAY §11 NGUYÊN BYTE, 0 lượt gọi** (`scripts/replay_plane_from_equation.py`, artifact `docs/evaluation/geometry/plane-from-equation/REPLAY.json`). Hợp đồng dựng lại từ **raw `analyze` của lượt chạy thật** qua `build_request_contract`, KHÔNG dùng gold — `fact_id` của gold khác (`tam_day_duoi` vs `tam_day_duoi_O`) nên mọi `source_fact_id` của mô hình sẽ trượt oan. Kết quả: `RAW_ATTEMPT_1_SCHEMA_VALID = YES` (trước: schema TỪ CHỐI) · **`RAW_ATTEMPT_1_STATIC_VALID = PASS`** ← khẳng định trung tâm · `SERVABLE = NO`. ⚠️ `ir_static` phải hỏi **RIÊNG**, không đọc qua `verify_and_compile` (hàm ấy chạy grounding TRƯỚC, nên ô `STATIC_VALID` sẽ là `NOT_REACHED` — mà đó đúng ô người đọc tới để xem, vì tầng phép mới gỡ tắc CHÍNH LÀ `ir_static`; báo `NOT_REACHED` cho thứ đo được là giấu kết quả sau một thứ tự gọi). ⚠️ **Chỗ còn tắc là một lỗ KHÁC, CÓ SẴN, không liên quan wave**: grounding bác `P_rim` — điểm vành mô hình bịa cho hình trụ, khai bằng `model_assumption`, đúng lớp `ball_2` mà `ConstructCurvedSolidStmt` đã ghi — trong khi mô hình **ĐÃ KHAI SẴN** `R` với `source_fact_id: ban_kinh_day` rồi vẫn bịa thêm. `MINIMAL_DELTA_SIZE = 2 trường · 2125 → 1964 byte`, và **`cau_lenh_mat_phang_KHONG_DOI = True`** — không một byte nào của phép mới bị sửa ⇒ `served` · `16π√5` · `checked=1 passed=1 violated=0` · TRACE PASS · SCENE3D PASS. attempt 0 và attempt 2 **giữ nguyên phán quyết**. **MODEL_GENERATED_OPERATION_EVIDENCE**: attempt 1 (raw `da8e60af…`) **tự đặt ĐÚNG tên và ĐÚNG chữ ký** `construct_plane_from_equation(a,b,c,d)`, không ai gợi ý. **§10**: đúng MỘT producer · MỘT bước `CREATE` · `depends: []` · lời kể *'Dựng mặt phẳng … từ phương trình 2x - z + 10 = 0'*; ⚠️ **điểm neo canonical KHÔNG lọt vào lời kể** (`test_29`) — nó là chi tiết thực thi, gọi tên nó cho học sinh là dạy một điểm hình học đề không có. Cảnh: `plane3` · `render: surface` · `point`/`normal` là **chuỗi phân số**, không `float` nào xuống renderer. `action` DÙNG LẠI `construct_plane` (cùng loại vật ⇒ một nhánh hiển thị, không hai). **Thẻ 6042 → 6302 B (+260)**, toàn bộ trên dòng lệnh mới: `+182` từ vựng, `+78` vai trò bốn ô số. ⚠️ **Luật in vai trò hẹp dần HAI lần trước khi chốt, và hai con số nói vì sao**: in cho MỌI ô = **+1791 B** (`target_var` và mọi ô `str` cũng mang mô tả); in cho cả ô *'giá trị thô'* = `+132 B`, nhưng 27 trong đó là `initial_value?:…[Giá trị khởi tạo ban đầu]` — **nói lại đúng thứ tên ô đã nói**, trên dòng `memory_declarations` mà MỌI chương trình đều đọc. Bản chốt chỉ in cho ô SỐ TRẦN: `+78 B`, dòng ấy giữ nguyên từng byte. Nhãn kiểu rút `giá trị thô, KHÔNG phải biểu thức` (34 B) → `số hữu tỉ THÔ` (14 B), khớp theo **KIỂU** (`int | str`) chứ không theo tên trường. Card C nguyên vẹn: hai affordance đã đo còn nguyên văn. **`CACHE_VERSION` 88 → 89.** BA băm model-facing đổi: `grammar_card` 4b435fbb→285292fe · `synthesis_schema` d69661ce→6ccef323 · `capability` e0214b77→4b1e2f80. `prompts` và `analyze_schema` **KHÔNG đổi một byte** — hợp đồng `SourceInvariant` do SERVER sở hữu, không bao giờ gửi cho mô hình, nên `ANALYZE_SCHEMA_CHANGED = NO`. ⚠️ Lần bump này **MẠNH HƠN 86/87/88**: wave đổi cả **PHÁN QUYẾT** chứ không riêng đầu vào — một envelope `ok` cache dưới v88 có thể là chương trình hệ HÔM NAY từ chối, nên row cũ **PHẢI** miss chứ không phải chỉ nên miss. Candidate `f48e768b…` → **`422a9e7b…`** (90 → 91 file, commit riêng). **5 phép tiêm**: ① `tuong_duong` chỉ so `(a,b,c)` ⇒ ca `d=11` LỌT (chứng minh `test_11` có răng) · ② gỡ kiểm suy biến ở lược đồ ⇒ kernel VẪN ném (hàng phòng thủ thứ hai có thật) · ③ gỡ bất biến ⇒ hình SAI được `served` kèm đáp số ĐÚNG · ④ điểm neo sai trục ⇒ `signed_eval ≠ 0` · ⑤ gỡ khỏi `_KIEU_DUNG` ⇒ `_producers` mất vật. `PRODUCT_CAPABILITY_CHANGED = NO` (`curved_oblique_section` giữ `foundation_only`, `PRODUCT_PROMOTION_ELIGIBLE = NO`). Cổng: wave **67 pass** · `pytest` **4329 pass, 0 đỏ** · `vitest` **698/51** · build PASS · replay **5/5** · crash **6/6 ném 0** · `certify_acceptance_runner` PASS 0 lượt gọi · cache identity exit 0 @ v89 · freeze `--verify` exit 0 (91 file) · `git diff --check` sạch. ⚠️ **Giới hạn**: wave này **KHÔNG đo hành vi mô hình** (`APPLICATION_LLM_CALLS = 0`) — nó chứng minh HỆ biểu đạt và kiểm được; câu *'mô hình có tự viết lại được không'* chưa ai hỏi. **`ELLIPSE_SERVABLE_REPLAY = PASS` là của MINIMAL DELTA, không phải raw** — trích số này mà bỏ chữ *'minimal delta'* là nói quá; raw attempt 1 vẫn `NO`. Delta hai trường ấy sửa một lỗ KHÁC có sẵn. `n = 1` đề, `n = 3` ứng viên, `DEVELOPMENT_SIGNAL`. Đề nêu mặt phẳng bằng cách bộ đọc không hiểu thì **không bất biến nào kiểm** — giới hạn của tầng đọc đề, không phải cửa mở trong cổng. Báo cáo `docs/PLANE_FROM_EQUATION_REPRESENTATION.md` | `OBLIQUE_ELLIPSE_FRESH_E2E_RERUN` (kèm quan sát thứ hai cho `CURVED_RIM_POINT_AFFORDANCE`, `HYPOTHESIS`, `n=1`) |
| Cổng phạm vi có định tuyến ĐỦ nghĩa vụ đại lượng không; và mô hình có tự tìm ra phép elip xiên không | **PHA A XONG — `ALL_4_OBLIGATIONS_ROUTABLE = YES`; PHA B CHƯA `served` — `EVENTUAL_SERVABLE = NO`** (2026-09-07, `SCOPE_GATE_QUANTITY_OBLIGATION_CLUE_REPAIR_AND_ELLIPSE_CONFIRMATION`) | **PHA A, 0 lượt gọi.** `ROOT_CAUSE = _MANH_MOI_NGHIA_VU thiếu 4 nghĩa vụ vừa analyze-emittable vừa checker-backed` ⇒ `co_duong_thuc_thi` fail-closed cả một LỚP bài. Sửa **đúng MỘT bảng, MỘT thẩm quyền**: `area` (danh từ trần) · `lateral_area` (3 biến thể có định ngữ) · `radius` (danh từ trần) · `section_matches`. ⚠️ **`area`/`radius` dùng danh từ TRẦN có chủ đích** — cổng này định tuyến THÔ, hợp đồng của nó chỉ là *'hệ có đường nào cho thứ đề này hỏi không'*; đúng/sai hình học vẫn thuộc grounding · phủ · kernel · checker. Bỏ sót một cách viết = **fail-closed một bài giải được**; nhận dư một ứng viên chỉ tốn một phép giao tập. KHÔNG thêm *'diện tích toàn phần'* (miền số CỐ Ý từ chối tổng hai căn thức khác nhau của `S_tp` nón). `section_matches` dùng CHUNG cụm *'thiết diện'* với `coplanar` — không thừa, vì trước bản này nó định tuyến được là nhờ **MƯỢN** manh mối của `coplanar`. **Bất biến khoá bằng test DẪN XUẤT từ registry**, không phải danh sách chép tay: `(analyze enum ∩ GEOMETRY_CHECKERS) − khoá(_MANH_MOI_NGHIA_VU) = ∅`, và chiều ngược lại cũng sạch (không manh mối nào trỏ nghĩa vụ chết). Đo sau sửa: *'Tính diện tích elip (E).'* → `['area']` · *'…diện tích xung quanh hình trụ.'* → `['area','lateral_area']` · *'Tính bán kính mặt cầu.'* → `['radius']` · đề nón **BỎ** cụm *'vuông góc'* → `['radius']` (trước đây chết ở `scope`). 8 manh mối cũ định tuyến y như trước; ngoài miền · chuỗi rỗng · đề không hỏi gì vẫn fail-closed. ⚠️ **Phép tiêm phải chấm ở mức TẬP, không mức `bool`** — bỏ `lateral_area` thì *'diện tích xung quanh…'* VẪN mở cổng nhờ `area`, nên một khẳng định boolean sẽ xanh và **không chứng minh gì**; khẳng định đúng là *'nghĩa vụ ấy có trong tập ứng viên'*. **43 test** (chính diện · dấu tiếng Việt · viết hoa · bài cong đầy đủ · bảo toàn · parity · **4 phép tiêm**). ⚠️ **Một mục `NGOAI_NANG_LUC` là SAI PHÂN LOẠI, sửa kèm**: đề nón *'bán kính đáy 3, đường sinh 5, tính diện tích xung quanh'* **chưa bao giờ** ngoài năng lực — hệ tính đúng `S_xq = πrl = 15π`, kiểm bằng kernel. Nó nằm đó vì **cổng từ chối nó**, và cổng từ chối vì bảng thiếu `lateral_area`: **một danh sách 'ngoài năng lực' dẫn từ hành vi của cổng là một VÒNG LẶP — cổng sai thì danh sách sai theo, và cả hai cùng xanh.** Hai mục còn lại đứng vững vì lý do thật (hỏi *phương trình*; hỏi *hình chiếu để vẽ*). `test_scope_gate_quantity_obligation_gap.py` (12 test khoá lỗ, tự dự báo sẽ đỏ khi lỗ đóng) đã **XOÁ**; chống tái phát nay là test parity, mạnh hơn vì dẫn xuất. **`CACHE_VERSION` 87 → 88, BUMP theo LUẬT** (đổi policy định tuyến), đúng tiền lệ **bump 80** — lượt ấy cũng đổi policy định tuyến, cũng không có row stale, cũng bump theo luật chứ không để dọn rác. Kiểm cache bằng **row thật**: `main.py:746`/`:781` chỉ ghi khi `envelope['status'] == 'ok'`, một refusal mang `'unsupported'` ⇒ lời từ chối ở `scope` **CHƯA BAO GIỜ được cache**, không có row stale nào để dọn. Lý do luật tồn tại: một đề từng bị từ chối nay được phục vụ, và `CACHE_VERSION` là thứ duy nhất nói được *'kết quả này sinh dưới luật định tuyến nào'*. **Sáu băm model-facing KHÔNG đổi một byte** — Pha A chỉ sửa **ĐƯỜNG VÀO**, không sửa bề mặt mô hình. Bốn cổng cùng commit + làm mới `cache_identity.lock.json`; candidate `e8c6150f…` → **`f48e768b…`** (commit riêng). **PHA B — lượt live `oblique-ellipse-after-scope-repair-20260907T050244Z`.** Đề · oracle · gold · tiêu chí chấm · trần token **giữ nguyên từng byte** từ wave bị chặn; artifact lượt bị chặn giữ nguyên làm bằng chứng lịch sử. `MEASUREMENT_CLASS = DEVELOPMENT_CURVED_END_TO_END_CONFIRMATION` · `HELD_OUT_CLAIM = NO` · `ANALYZE = 1` · `INITIAL_SYNTHESIS = 1` · `REPAIR = 2` · `LOGICAL_APPLICATION_CALLS = 4/5` · `PHYSICAL_API_ATTEMPTS = 4` · `TRANSPORT_RETRIES = 0` · `CANDIDATE_PROGRAM_ATTEMPTS = 3` · **20 725/40 000** token · `cached_content = 0`. ✅ **Cổng phạm vi đã mở đúng** — đề đi qua `scope` → `analyze` → ba lượt sinh; Pha A làm đúng thứ nó nhắm, và điều đó được xác nhận **trên đường sản phẩm** chứ không chỉ ở mức hàm. `ANALYZE_CONTRACT_CORRECT` = **PASS** toàn bộ 7 chiều (5 fact · obligation `area` · container `E` · witness `dien_tich_E` · hai tâm · bán kính 4 · phương trình mp). ⚠️ **`servable = False`, dừng ở `semantic_program`. Cả ba ứng viên đúng MỌI THỨ trừ mặt phẳng**: chọn `intersect_plane_curved_ellipse` **ngay attempt 0**, khai `E` là `ellipse3`, dựng đúng hình trụ (`anchor`/`apex`/`rim_point`), đo đúng `area` của `E`, xuất xứ O/O′/R dùng `source_fact_id` — cả ba lượt. Hỏng: attempt 0 `IR_USE_BEFORE_CONSTRUCTION: 'alpha_plane'` (khai từ fact mà không câu lệnh nào dựng) → attempt 1 **tự đặt tên phép còn thiếu** `construct_plane_from_equation(a,b,c,d)` (schema bác: tag không khớp) → attempt 2 ba điểm `(0,0,10)`, `(1,0,12)`, `(0,1,10)` khai `model_assumption` → `grounding UNANCHORED_DERIVED_ASSUMPTION`. **Ba điểm ấy THOẢ đúng `2x − z + 10 = 0`** (kiểm số học): thứ bị bác là **XUẤT XỨ**, không phải toạ độ. ⚠️ **`BLOCKER = PLANE_FROM_EQUATION_REPRESENTATION`, loại `SYSTEM_GAP` + `OPERATOR_AFFORDANCE`** — đo TẤT ĐỊNH, 0 lượt gọi thêm: mặt phẳng cho bằng **phương trình** có đúng ba lối biểu đạt và **chỉ MỘT lối chạy được**. (A) `plane3` + `initial_value` + `source_fact_id` → grounding bác *'giá trị […] không có trong mục mat_phang_alpha'*; (B) ba `point3` chỉ có `model_assumption` → `UNANCHORED_DERIVED_ASSUMPTION`; (C) ba `point3` mang `source_fact_id` trỏ fact phương trình → **chạy** (đường gold). `_KIEU_DUNG`/`_CHU_KY` **không có phép nào** chứa chữ `equation`. **Điểm đắt nhất: lối C đòi gắn `source_fact_id` vào toạ độ mà đề KHÔNG HỀ NÊU** — đề cho một *phương trình*, không cho ba điểm. Mô hình chọn `model_assumption` là **ngữ nghĩa ĐÚNG** (nó thật sự tự chọn ba điểm ấy, và lời khai nói đúng vậy), grounding bác nó và grounding **không sai** theo luật hiện có ⇒ **hệ đang buộc mô hình khai xuất xứ không trung thực để đi được**. Đó là khoảng trống biểu đạt của HỆ, không phải lỗi mô hình. **Phân loại từng phát hiện**: ba lối biểu đạt + `_KIEU_DUNG` thiếu phép = **`SYSTEM_GAP`** (tái hiện tất định, không phụ thuộc lượt sinh nào) · lối chạy được đòi xuất xứ không trung thực = **`SYSTEM_GAP`** · mô hình tự đặt tên `construct_plane_from_equation` = **`OBSERVATION`** (`n=1`) · mô hình chọn `model_assumption` cho điểm tự chọn = **`HYPOTHESIS`** (`n=1`, và lựa chọn ấy hợp lý về ngữ nghĩa). **`PRODUCT_CAPABILITY_CHANGED = NO`** — `curved_oblique_section` giữ `foundation_only`, `PRODUCT_PROMOTION_ELIGIBLE = NO`. ⚠️ **`ELLIPSE_FOUNDATION_SEQUENCE` KHÔNG đóng** — `CARD_C_CURVED_ELLIPSE_PATH_CONFIRMED` giữ `NOT_MEASURED` vì điều kiện là *eventual served* và nó chưa đạt. `STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED`. Cổng: scope-gate **43** (4 phép tiêm) · tiền kiểm gold **20** · runner stub **18** · `pytest` **4259 pass** (cây SẠCH @ `2beb693`), 1 skip, 1 deselect, **0 đỏ** · replay **5/5** · crash **6/6 ném 0** · `certify_acceptance_runner` **PASS, 0 lượt gọi** · cache identity exit 0 @ v88 · freeze `--verify` exit 0 (90 file, `f48e768b…`) · `git diff --check` sạch · frontend **KẾ THỪA** (Scene3D không đụng). ⚠️ **Giới hạn**: `n = 1` lượt chạy, 3 attempt ⇒ `DEVELOPMENT_SIGNAL`, không phải ước lượng tổng thể. **KHÔNG được đọc thành *'mô hình không làm được bài elip'*** — nó chọn đúng toán tử ngay attempt 0, khai đúng kiểu, dựng đúng hình trụ, đo đúng đại lượng, ba điểm nó chọn thoả đúng phương trình; thứ chặn nó là một khoảng trống biểu đạt của HỆ. Báo cáo `docs/SCOPE_GATE_QUANTITY_OBLIGATION_CLUE_REPAIR_AND_ELLIPSE_CONFIRMATION.md` | `PLANE_FROM_EQUATION_REPRESENTATION` |
| Mo hinh co TU tim ra phep elip xien tren de moi khong | **DUNG TRUOC PROVIDER** — `BLOCKED_BEFORE_PROVIDER`, `MODEL_DISCOVERABILITY = NOT_MEASURED` (2026-09-07, `OBLIQUE_ELLIPSE_FRESH_END_TO_END_CONFIRMATION`) | **`APPLICATION_LLM_CALLS = 0`** — khong tieu mot luot quota nao, va do la ket qua DUNG chu khong phai mot luot hong. `GOLD_PREFLIGHT = PASS` (20 test): de MOI `r=4 · h=20 · (α): 2x−z+10=0` di TRON duong toi `served` voi **`16π√5` CHINH XAC**, **HAI oracle doc lap** — cong thuc ban truc (`b²=16`, `a²=16·5·400/400=80`), va **the thang** bon dau mut truc vao `x²+y²=16` + `2x−z+10=0` (chung ra `(4,0,18)`, `(−4,0,2)`, `(0,±4,10)`, toan huu ti; bien doc `z ∈ [2,18]` khop oracle). Bon vat dung producer/dependency; bao dong tu `dien_tich_E` ve du 9 vat. **BAY phan vi du**: `construct_section` cho khoi cong → `ir_static` · mp ∥ truc → `CURVED_ELLIPSE_OUTSIDE_V1_CLOSURE` · elip vuot day → `CURVED_ELLIPSE_CROSSES_CAP` · do `radius` thay `area` → `ir_static` · thieu producer → `IR_USE_BEFORE_CONSTRUCTION`. HAI ca KHONG bi chan va **ca hai la dung**: khai sai kieu (kieu DUNG RA thang kieu KHAI — hanh vi co san, dap so van `16π√5`), va sai he so goc (mat phang hop le, chi khong phai mp de cho — tuyen phong thu duy nhat la PHEP SO DAP SO: `16π√2 ≠ 16π√5`). ⚠️ **BLOCKER = `SCOPE_GATE_MISSING_QUANTITY_OBLIGATION_CLUES`, loai `SYSTEM_GAP`**, tim bang provider stub TRUOC khi tieu quota. `co_duong_thuc_thi` la cong TAT DINH dung truoc `analyze`; hop dong cua no la *'he co duong bieu dien nao cho thu de nay hoi khong'*. Bang manh moi `_MANH_MOI_NGHIA_VU` **thieu BON nghia vu CO CHECKER**: `area` · `lateral_area` · `radius` · `section_matches`. Nen de chi hoi *'tinh dien tich …'* bi bac o tang `scope` voi `GATE_NOT_SIMULATION_SUITABLE`, **0 luot goi model** — trong khi he CO du duong (`BANG_PHEP_DO['area']`, `check_area`, `OBLIGATION_KINDS`, va ca kieu `ellipse3` vua dung xong). Ca LOP cau hoi ay truot, khong phai mot cach viet xui. Bang chung cong dang doc CHU chu khong doc thu de hoi: them cum *'Mat phang vuong goc voi truc.'* vao truoc cung cau hoi ay thi cong MO (khop `perpendicular`). ⚠️ **DINH CHINH CACH DOC WAVE TRUOC**: de bai NON cua `CURVED_END_TO_END_FRESH_CONFIRMATION` hoi **`radius`** nhung qua cong nho manh moi **`perpendicular`** tu cum *'vuong goc voi SO'* nam o phan MO TA, khong phai phan hoi — `nghia_vu_ung_vien(de non) = {perpendicular}`, KHONG co `radius`. Bo hai chu ay di thi luot do ay cung da chet o `scope`. Cong cho DUNG cau tra loi **vi mot ly do SAI**. Moi con so cua wave ay **giu nguyen**; thu sua la CACH DOC. **Vi sao lo song sot qua ba wave**: `RATIO_*`/`PROVENANCE_*`/`MINIMAL_CARD_*` dung runner A/B voi hop dong CO DINH — khong cham cong; `CURVED_MISSING_FAMILY_…` dung `verify_and_compile` voi hop dong dung tay — cung khong cham; `CURVED_END_TO_END_…` co cham nhung lot nho mot tu trong phan mo ta; wave nay la de dau tien khong tinh co mang chu nao trong bang. **Duong sua ghi san**: them cum manh moi cho bon nghia vu vao `_MANH_MOI_NGHIA_VU` — MOT bang, MOT tham quyen. KHONG noi `co_duong_thuc_thi` thanh 'cu hinh hoc thi cho qua' (cong ay ton tai de tu choi de hoi thu he khong dung duoc), KHONG dung bang manh moi thu hai. Khoa bang `test_D1_sua_la_MOT_bang_MOT_tham_quyen`. Wave nay **khong sua** — dung ma san pham keo theo nhip bump/dong bang lai, va §11 cua brief noi ro ma san pham giu nguyen. **Bo do**: runner nay **chon duoc gold module va scorer module theo dang ky** (`gold_module`, `scorer_module`) thay vi viet runner thu hai — cung khuon `corpus_module` da ap cho runner A/B; module cu giu nguyen vi bam cua no da nam trong artifact BAT BIEN. Bo cham cua wave la module rieng, khong noi hai bo cham mac dinh (chung hoi nhung chieu cua bai NON). `test_runner_curved_end_to_end.py` van **21 pass**, khong hoi quy. **Khong dung ma san pham**: `CACHE_VERSION` 87→87, candidate `e8c6150f…` khong dong bang lai, 6 bam model-facing khong doi, `curved_oblique_section` giu `foundation_only`, `PRODUCT_PROMOTION_ELIGIBLE = NO`. ⚠️ **`ELLIPSE_FOUNDATION_SEQUENCE` KHONG dong** — dieu kien la *eventual served*, va no CHUA dat; khong phai vi mo hinh sai ma vi phep do chua chay duoc. `CARD_C_CURVED_ELLIPSE_PATH_CONFIRMED` giu `NOT_MEASURED`. Cong: tien kiem gold **20** · tai hien blocker **12** · runner stub **14** · runner wave truoc **21** · `pytest` **4223 pass, 0 do** · replay **5/5** · crash **6/6 nem 0** · `certify_acceptance_runner` **PASS, 0 luot goi** · cache identity exit 0 · freeze `--verify` exit 0 · `git diff --check` sach · frontend KE THUA (hop dong Scene3D khong dung). ⚠️ **Gioi han**: wave nay KHONG noi gi ve hanh vi mo hinh — 0 luot goi nghia la KHONG co du lieu nao theo huong ay; noi *'mo hinh khong lam duoc bai elip'* la noi SAI, chua ai hoi no. Blocker la `SYSTEM_GAP` chu khong phai `HYPOTHESIS`: tai hien tat dinh, 12 test, hai bang tham quyen doi chieu duoc. Bao cao `docs/OBLIQUE_ELLIPSE_FRESH_END_TO_END_CONFIRMATION.md` | `SCOPE_GATE_QUANTITY_OBLIGATION_CLUE_REPAIR` |
| Mo ho hinh con thieu dau tien — thiet dien elip cua hinh tru cat xien | **NEN TAT DINH XONG** — `SYSTEM_EXPRESSIBLE = YES` · `DETERMINISTICALLY_CORRECT = YES` (2026-09-07, `CURVED_MISSING_FAMILY_ROADMAP_AND_OBLIQUE_CYLINDER_ELLIPSE_FOUNDATION`) | **`APPLICATION_LLM_CALLS = 0`**. `tests/geometry/test_oblique_cylinder_ellipse.py` **29 pass**, BA phep tiem chiu luc. **Ban do 4 ho con thieu, doc THANG ma nguon** — moi o tro chu ky hoac `grep` tren cay hien tai, khong tin dong chu trong bang capability: thiet dien cong xien thang **5/7** tieu chi va khong thua o dau (mien so `Radical` = `he·√can·π^mu` DA cho duoc `9√2π` · checker + trace DAN XUAT nen tu nhan kieu moi · khoang trong thu ve **1 kieu + 1 phep**); tron xoay tong quat vuong **MIEN SO** (can tich phan); ghep–bu khong co MOT phep boolean nao trong `geometry/` (grep 0 hit) — blast radius lon nhat; **da dien khong loi** la ung vien gan thu hai va mang mot khiem khuyet CO SAN CHUA AI GHI: `volume_pyramid_fan` kiem day PHANG nhung **khong kiem LOI** ⇒ day lom cho so sai IM LANG (ghi de viec ke tiep co dia chi; wave nay KHONG sua — cham tham quyen dung chung voi `check_volume`). **Tai hien TRUOC khi sua**: chuong trinh cat xien qua schema · `ir_static` · grounding · phu · CA HAI bat bien nguon roi chet o **`execution`** voi `CURVED_SECTION_OUTSIDE_V1_CLOSURE` ⇒ khoang trong o **kernel + he kieu**, KHONG o checker/measure/renderer. ⚠️ Ban tai hien dau bi `grounding` chan truoc (de tong hop khong dat ten ba diem mat phang) — **khong phai** khoang trong can do; ghi ra de lan sau khong ai doc loi tu choi ay nhu mot phat hien. **Them DUNG MOT kieu (`ellipse3`) va DUNG MOT phep (`intersect_plane_curved_ellipse`)**: moi truong o ℚ (ban truc dang BINH PHUONG; hai phuong truc la tich co huong cua vecto huu ti, CHUA chuan hoa — chuan hoa da chung khoi ℚ³ nen renderer lam o bien hien thi). Phep RIENG chu khong phai kieu tra ve 'tuy luc chay' cua `intersect_plane_curved`: kieu dong lay di dung thu `ir_static_check` sinh ra de lam. **Cong thuc dan tu `u` va `n`**: `b² = r²`, `a² = r²|n|²|u|²/(n·u)²` — ca hai huu ti, khong phep chia nao cho mot can. Ca chuan `r=3 · h=20 · z=10+x` cho **`9√2π` CHINH XAC**, **HAI oracle doc lap**: giai tich, va **the thang** bon dau mut truc vao `x²+y²=9` + `n·(P−C)=0` (chung ra `(±3,0,13/7)` va `(0,±3,10)`, toan huu ti). Bao dong V1 hep co chu dich: chi HINH TRU, mat phang xien, elip nam TRON giua hai day — **nam bien, nam ma rieng**; ⊥ truc **neu ten phep dung** (`intersect_plane_curved`). Duong `circle3` cu, cau va non KHONG suy suyen. ⚠️ **Sua mot lo DA TROI HAI LAN**: dong `type nhan dung mot trong` cua the la danh sach CHEP TAY liet ke kieu DUOC PHEP, thieu `circle3`+`curved_solid` tu 2026-09-03 va thieu `ellipse3`. Hau qua DO DUOC o `CURVED_END_TO_END_FRESH_CONFIRMATION` attempt 1: mo hinh khai thiet dien la `section` — kieu the CO liet ke — roi hong o `ir_static`, mat mot luot sua (wave ay ghi `HYPOTHESIS`, `n=1`). Nay dan xuat bang cach **LOAI TRU** tap Tin hoc da dong bang (`_KIEU_TIN_HOC`): tap ay chi co lai, tap hinh hoc dang lon, nen chieu troi DAO lai. Khoa bang `test_the_liet_ke_DU_moi_kieu_hinh_hoc_khai_duoc`. **BA tang TU NHAN, khong sua mot dong logic nao** — bang chung cho thiet ke mot-tham-quyen: `OBLIGATION_KINDS['area']` (dan tu `BANG_PHEP_DO`) · `check_area` (dan kieu tu `BANG_PHEP_DO`, goi `area_of` DUNG CHUNG voi duong chay) · `_BIEU_THUC_HINH_HOC` (dan tu `_CHU_KY`, nen trace/`depends` tu co). Trace: 1 buoc sinh elip · `depends ⊇ {tru, mp}` · bao dong tu `dt_E` ve du 9 vat. Scene3D: loai ve `ellipse` RIENG (khong muon `circle` — mot duong tron ve duoc tu MOT ban kinh, elip can hai ban truc VA biet no xoay the nao), 6 truong exact, khong float nao xuong day; renderer dung vanh bang `BufferGeometry` tu hai phuong, KHONG `RingGeometry` + scale khong deu. **BA phep tiem chiu luc**: he so ban truc lon (`a² := b²` ⇒ `9π` thay vi `9√2π`, moi test cau truc VAN XANH) · kiem nam tron giua hai day (`z0=1` di lot, tra mot elip DOI) · lien ket producer/dependency (elip **bien mat khoi canh** — manh hon du doan ban dau). ⚠️ **HAI gia dinh cua chinh bo test da SAI va duoc sua bang phep do**, ghi vi chung noi ve he: (a) `test_17` khang dinh `ir_static` chan khi khai `E` la `circle3` roi gan bang phep elip — chay thu: **khong chan**, kieu DUNG RA thang kieu KHAI o moi tang (`bang_ky_hieu` noi thang dieu ay), dap so van dung, canh van nhan `ellipse3`; hanh vi CO SAN TU TRUOC, siet lai la mot luot rieng cham moi chuong trinh dang khai long; (b) `test_21` tiem `_NGUON_CUA_PHEP_DUNG` va **van xanh** — tuc khong gac gi; bang dung la `validator._BIEU_THUC_HINH_HOC` (vat sinh boi `assign` di nhanh bieu thuc) va no duoc nhap BEN TRONG ham nen phai va o module so huu. **`CACHE_VERSION` 86 → 87, BUMP** — bon cong cung commit. Dung tien le bump 70/73 (cache giu CA envelope ⇒ de da phan tich tra lai chuong trinh sinh boi THE CU, the khong co phep elip) + ly do doc lap cung hang bump 68/78 (**luoc do gui cho mo hinh doi**). Kiem cache da lam: KHONG envelope cu nao hoa SAI (chi cache `status == ok`, wave nay chi bien tu-choi → phuc-vu). Model-facing: **BA** doi (`grammar_card` 9685b06a→4b435fbb · `synthesis_schema` 8c57c9de→d69661ce · `capability` 85bd3167→e0214b77); `prompts` va `analyze_schema` **KHONG doi mot byte** (nghia vu `area` da co tu bump 78, wave nay chi noi tap KIEU CHU THE). The hinh hoc 5855 → 6042 byte (`+157` tu vung moi, `+30` sua nhan sai), tran 5900 → 6100. Candidate `138db7b1…` → **`e8c6150f…`** (commit rieng). **Card C giu nguyen nghia**: hai affordance da do con NGUYEN VAN; guard byte-match cu doi sang kiem hai dong ay thay vi so byte — so byte tu nay chi noi *'the da doi'*, cau vo ich vi the SE doi moi lan mo nang luc. **Capability `curved_oblique_section`: `unsupported` → `foundation_only`** (ly do cu *'khong co kieu conic trong IR'* nay SAI). KHONG len `supported`: chua ai do mo hinh co tu tim ra phep ay khong. ball/cylinder/cone GIU NGUYEN. Cong: elip **29** · pytest **4172 pass, 0 do** · vitest **698/51** · build PASS · replay **5/5** · crash **6/6 nem 0** · `certify_acceptance_runner` **PASS, 0 luot goi** · cache identity exit 0 · freeze `--verify` exit 0 · `git diff --check` sach. ⚠️ **Gioi han**: wave nay KHONG do hanh vi mo hinh — noi *'he lam duoc elip'* la dung, noi *'AI sinh duoc bai elip'* la noi qua. Bao dong V1 hep: chi tru, chi elip DAY DU; **non xien chua phan xu**. Mot ca chuan + bon ca bien, khong phai mot khao sat. Bao cao `docs/CURVED_MISSING_FAMILY_ROADMAP_AND_OBLIQUE_CYLINDER_ELLIPSE_FOUNDATION.md` | `OBLIQUE_ELLIPSE_FRESH_END_TO_END_CONFIRMATION` |
| Card C co dung vung NGOAI ho doan thang, tren TRON duong san pham khong | **DA DO — `CURVED_END_TO_END_FRESH_CONFIRMATION = PASS`, giu C** (2026-09-07) | `MEASUREMENT_CLASS = DEVELOPMENT_CURVED_END_TO_END_CONFIRMATION` · `HELD_OUT_CLAIM = NO` · **1 de hinh CONG moi** · `LOGICAL_APPLICATION_CALLS = 4` (analyze **1** + chuong trinh **3**) · `PHYSICAL_API_ATTEMPTS = 4` · `TRANSPORT_RETRIES = 0` · **19 263/37 500** token · `cached_content = 0` (khong nhieu cache) · `RUN_STATUS = COMPLETE`. **Khac moi wave A/B truoc o HAI dieu, ca hai co y**: `analyze` la mot luot LLM THAT (hop dong do mo hinh trich), va vong sua cua san pham KHONG bi tat — nen no tra loi duoc cau ma bon luot truoc co y khong hoi, doi lai **khong tach duoc dong gop tung tang**. Runner goi thang `pipeline.run_pipeline`, KHONG qua HTTP, va **tu choi chay** neu the san pham da troi khoi Card C. De: non dinh S, tam day O, ban kinh day 12, chieu cao SO 18; T tren SO voi ST:TO = 1:2; mp qua T vuong goc SO cat non theo (c). Oracle `r(c) = 4`, **kiem cheo BA loi doc lap** (ti le truc · chieu cao tu day · KERNEL). `SYSTEM_EXPRESSIBLE = YES` — 7/7 cau, moi cau tro chu ky runtime hoac test. `GOLD_PREFLIGHT = PASS` — 19 test, **7 phan vi du moi cai chan DUNG TANG cua no**: ratio sai trong doan -> `source_invariant` · T khai thang toa do -> `grounding`/`DERIVED_ENTITY_WITHOUT_PRODUCER` · toa do trai chieu cao -> `source_invariant` · giao sai kieu -> `ir_static`/`IR_OPERAND_TYPE` · diem ngoai truc bia ra -> `grounding`/`UNANCHORED_DERIVED_ASSUMPTION` · do ban kinh SAI CHU THE -> `structural_coverage` · mat cat xien -> KERNEL `CURVED_SECTION_OUTSIDE_V1_CLOSURE`. ⚠️ Phan vi du cuoi phai hoi THANG kernel: o tang IR mot mat cat xien khong dung noi ma khong bia them diem, va grounding bat diem bia TRUOC — hoi qua IR thi cau tra loi den tu mot cong KHAC. **Ket qua live: `served`, `EXACT_ANSWER = 4`, envelope `ok`, Scene3D 9 vat, trace PASS.** `FIRST_ATTEMPT_SERVABLE = NO` — dat duoc **nho 2 luot sua**, va ca hai loi deu la LOP DA BIET: attempt 0 dat `at` sai o (lop `POINT_INITIALIZATION`; tai hien tren mot bai KHAC HAN va **van tu dong**, tuc bang chung THU HAI cho `PERMANENT_SLOT_INSTRUCTION_NEEDED = NOT_PROVED` — quyet dinh khong them dong huong dan ve o `at` vao Card C duoc giu vung them mot ca); attempt 1 voi tay tim `construct_section` cho khoi CONG roi do `radius` tren mot `section` — dung lop `c5b`/`c9b` ma `CURVED_SECTION_RADIUS_PATH_ADJUDICATION` da phan xu la **lua chon cua mo hinh**, nay cho thay no VAN tai hien va VAN sua duoc trong mot luot. **Hai delta cua Card C hien ro tren bai hinh cong**: `ratio 1/3` quy dung tu `m:n` (chieu `S->O`), va CA BA diem dau vao di kenh `model_assumption`; khong attempt nao hong o hai truc ay. Synthesis cuoi: `construct_curved_solid.cone` · `intersect_plane_curved -> circle3` · diem chia DO LENH TAO · `measure(radius, of=c)` dung chu the. ⚠️ **DINH CHINH BO CHAM, khai truoc khi dung so:** ban inline ghi `ANALYZE_CONTRACT_CORRECT = FAIL` trong khi runner **chua he giu** raw cua tang analyze — tuc cham TRUOT mot tang no khong quan sat duoc, cung ho voi loi `GROUNDING = PASS` cho tang chua chay ma `PROVENANCE_AFFORDANCE_AB_4_LUOT §6` da dinh chinh. Bo cham nay phan biet BA gia tri: `PASS/FAIL` · **`NOT_CAPTURED`** · `NOT_REACHED`. Gia tri dung: nghia vu **PASS** (kind `radius`, container `(c)`), noi dung fact **`NOT_CAPTURED`** (8 fact quan sat duoc tu su kien). Runner da sua de giu raw analyze (`test_C5`), va bo cham VAN FAIL duoc khi co du lieu va du lieu sai (`test_C7` — dinh chinh khong duoc lam bo cham mat rang). Artifact luot chay giu nguyen tung byte; ket qua dung o `SCORING.json`. ⚠️ **Dinh chinh thu hai:** `CANDIDATE_ATTEMPTS = 4` gom **1 luot analyze**; doc mot minh se bi hieu thanh 4 ung vien CHUONG TRINH (that ra la 3). `wave_counters` nay phat **phan ra theo tang** cung voi tong, khoa bang `test_C4`. **Khong dung ma san pham**: `CACHE_VERSION` 86→86, candidate `138db7b1…` khong dong bang lai, 6 bam model-facing khong doi mot byte, `PRODUCT_VARIANT` = **C**, `PRODUCT_CAPABILITY_CHANGED = NO`. Cong: tien kiem **19** · runner stub **21** · bo dem **12** · chon loc **192** · `pytest` **4141 pass, 0 do** · `vitest` **698/51** · build PASS · replay **5/5** · crash **6/6 nem 0** · cache identity exit 0 · freeze `--verify` exit 0 · `git diff --check` sach. ⚠️ **Gioi han:** `n = 1` · khong tach duoc dong gop tung tang · **KHONG phai luot sinh dung ngay** (noi *'mo hinh tu sinh dung bai hinh cong'* la noi qua; cau dung la *'duong san pham — gom ca vong sua — phuc vu duoc bai nay'*) · mot ca **CHUA du** de chuyen ball/cylinder/cone sang `supported` · `STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED`. Hai `HYPOTHESIS` chua phan biet duoc: the KHONG liet ke `circle3`/`curved_solid` trong dong `type nhan dung mot trong` (bo loc tay trong `_the_hinh_hoc`) va attempt 1 hong dung o cho khai `c` la `section` — hai dieu khop nhau nhung `n=1` khong tach duoc khoi *'mo hinh quen tay voi construct_section'*; va mo hinh chon `rim_point` thay vi o `radius` du de cho ban kinh bang SO. Bao cao `docs/CURVED_END_TO_END_FRESH_CONFIRMATION.md` | `CURVED_MISSING_FAMILY_ROADMAP_AND_FIRST_IMPLEMENTATION` |
| Hợp nhất hai hướng dẫn đã có bằng chứng vào thẻ, xác nhận trên đề MỚI | **ÁP DỤNG — `CARD_C_ADOPTED = YES`, thẻ A → C** (2026-09-07, `MINIMAL_CARD_CONSOLIDATION_AND_FRESH_CONFIRMATION`) | `MEASUREMENT_CLASS = DEVELOPMENT_SYNTHESIS_AB` · `HELD_OUT_CLAIM = NO` · **2 đề MỚI × 2 arm = 4 lượt** · `ANALYZE = 0` · `REPAIR = 0` · `LOGICAL_APPLICATION_CALLS = 4` · `PHYSICAL_API_ATTEMPTS = 4` · `CANDIDATE_ATTEMPTS = 4` · **23 801/30 000** token · `RUN_STATUS = COMPLETE`. **Wave ĐẦU TIÊN của chuỗi đổi MÃ SẢN PHẨM** — ba wave trước đo từng mảnh rời rồi giữ nguyên thẻ. Thẻ **C** = thẻ sản phẩm + **hai** hướng dẫn đã đo riêng (`ratio` định nghĩa `t`; dòng `Xuất xứ:`), **+383 B**, 1 dòng thêm + 1 dòng sửa; nó **TRÙNG BYTE** với `card_P1` của wave provenance — dùng nguyên byte để giữ liền chuỗi bằng chứng thay vì tạo biến thể thứ ba chưa đo. **Kết quả trên 2 đề chưa từng đo** (`f1` tỉ số trực tiếp `AM:MB=5:4`; `f2` bội số đảo hướng `KH=2·GK`, đáp số **28/3 hữu tỉ không nguyên**): `t` đúng **A0 0/2 · C 2/2**; xuất xứ **1/2 · 2/2**; điểm dẫn xuất được dựng **2/2 cả hai**; mô phỏng `served` đúng **0/2 · 2/2**; ghép cặp **C thắng 2 · thua 0**; `A0_CORRECT_AND_C_INCORRECT = 0`. **A0 mắc đúng hai lỗi mà hai dòng nhắm tới**, mỗi lỗi một ca: `f2/A0` ghi nhãn *'GK:KH = 1:2'* (đọc đề ĐÚNG) rồi viết `ratio 1/2` — lần tái hiện **thứ TƯ** của nhầm `m:n` ↔ `t`, bị `source_invariant` bắt; `f1/A0` khai gốc toạ độ với **cả hai** ô xuất xứ trống **và** đi vòng qua biến `ratio_for_M` — đúng thứ nhãn `ratio:tên` mời gọi — nên grounding từ chối hai lần. Chi tiết sau là bằng chứng TRỰC TIẾP rằng nhãn cũ không chỉ thiếu mà **đánh lạc hướng**: mô hình tính đúng `5/9` rồi vẫn hỏng. **Token** A0 13 310 (0 ca đúng ⇒ `UNDEFINED`) · C 10 491 với **5 246/mô phỏng đúng**; ⚠️ **có nhiễu cache** (`cached_content` C 997 · A0 0) nên chênh tổng không quy hết cho delta; phần chênh lớn nhất ở **thoughts** (A0 5 342 vs C 2 352 — A0 nghĩ nhiều gấp đôi và vẫn hỏng cả hai ca). **Sáu điều kiện áp dụng khoá TRƯỚC lượt gọi đầu, đủ cả sáu** ⇒ áp dụng: hai dòng vào `grammar_card.py` (thẻ sinh ra **trùng byte** thẻ đã đo `ac07f716…`, tức bản áp dụng đúng bằng bản đo) · trần thẻ 5510→**5900** với phân loại thẳng thắn (`+60` sửa nhãn sai, `+323` **VĂN XUÔI VIẾT TAY** — phá lệ mọi lần nâng trần trước, nhận vì quan hệ GIỮA ba ô xuất xứ không thuộc `Field.description` của trường đơn lẻ nào; khoá bằng `test_dong_xuat_xu_la_quy_tac_CHUNG` cấm mọi tên điểm/fact/đáp số) · **`CACHE_VERSION` 85 → 86, BUMP** đúng lý do bump 70/73 (cache giữ CẢ envelope ⇒ đề đã phân tích trả lại chương trình sinh bởi THẺ CŨ), bốn cổng cùng commit + làm mới `cache_identity.lock.json` · **đúng MỘT băm model-facing đổi**: `grammar_card e0fbbc84→9685b06a`, còn `prompts` · `synthesis_schema` · `analyze_schema` · `capability` **không đổi một byte** · candidate `36e81713…`→**`138db7b1…`** (commit riêng). ⚠️ **HAI ĐÍNH CHÍNH BỘ ĐO, xong TRƯỚC lượt gọi đầu, cả hai tìm bằng stub:** (a) `REPAIR_PROBE_COUNTER_DECOMPOSITION` — `PHYSICAL_ATTEMPTS = 2` của wave trước đếm **ỨNG VIÊN** chứ không đếm request (bộ đếm tăng cả ở nhánh trả raw lịch sử đọc từ artifact); telemetry `calls = 1` là bằng chứng độc lập; ba trường tách riêng, hai trong số đó **DẪN XUẤT** từ `ApiBudget` nên không còn đường nào để ứng viên đọc từ file làm tăng `physical_api_attempts`; artifact nguồn giữ nguyên từng byte, đính chính liên kết bằng hash; **lỗi ĐẶT TÊN, không phải lỗi số liệu** — mọi kết luận wave nguồn không đổi. (b) `RUNNER_SOURCE_INVARIANT_UNDERBINDING` — runner A/B chỉ gắn `bat_bien_chia_doan`, **thiếu** `bat_bien_do_dai` (đường sản phẩm gắn cả hai), nên cổng `segment_length` **chưa từng chạy** trong hai wave A/B trước dù đăng ký khai là có; chấm lại **toàn bộ** artifact cũ 0 lượt gọi: mọi lượt đều khai toạ độ **đúng** độ dài đề cho ⇒ **không kết luận cũ nào đổi**; phép tiêm chứng minh bản sửa chạy cả hai chiều (trước: `served`; sau: chặn ở `source_invariant`). ⚠️ **Bốn guard ghim `PRODUCT_VARIANT = A` đỏ đúng chức năng** và được cập nhật giữ nguyên ý định; `test_E8` lộ ra nó kết bằng `grammar_card == a`, **khẳng định ngược chính docstring của nó**. Cổng: tiền kiểm **21** · bộ đếm **11** · runner stub **23** (gồm `test_F3` gọi CHÍNH `call_gemini` với transport giả để chứng minh bộ đếm nằm trên đường thật — live xác nhận: stub đọc 0/0/4, chạy thật đọc **4/4/4**) · thẻ **12** · `pytest` **4094 pass, 0 đỏ** · `vitest` **698/51** · build PASS · replay **5/5** · crash **6/6 ném 0** · freeze `--verify` exit 0 · `git diff --check` sạch. ⚠️ **Giới hạn:** delta **GỘP** hai dòng (không tách được đóng góp từng dòng — hai wave trước đã đo riêng, đây là ba phép đo nhỏ chứ không phải một phép đo lớn) · `n = 2` cặp · **cả hai đề cùng một họ** (điểm chia đoạn thẳng) · `PRODUCT_CAPABILITY_CHANGED = NO` (IR không mở thêm phép nào; chỉ đổi thứ mô hình ĐỌC THẤY) · `STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED`. Báo cáo `docs/MINIMAL_CARD_CONSOLIDATION_AND_FRESH_CONFIRMATION.md` | `CURVED_END_TO_END_FRESH_CONFIRMATION` |
| Vòng sửa sẵn có có tự đóng được lỗi đặt `at` sai ô không | **ĐÃ ĐO — `ONE_REPAIR_RECOVERS_CORRECT_SIMULATION = YES`, giữ A** (2026-09-07, `POINT_INITIALIZATION_REPAIR_EFFICACY`) | `MEASUREMENT_CLASS = DEVELOPMENT_REPAIR_PROBE` · `HELD_OUT_CLAIM = NO` · **LOGICAL 1/1** (đúng trần đăng ký) · `PHYSICAL = 2` (lượt 0 là raw candidate lịch sử, **không** ra mạng) · `INITIAL_SYNTHESIS_CALLS_THIS_WAVE = 0` · **3123** token · `RUN_STATUS = COMPLETE`. Đo **vòng sửa CỦA SẢN PHẨM** (`pipeline.stage_semantic_program` + `_prompt_sua`), không phải một bộ sửa dựng riêng. **Kết quả: một lượt sửa, trọn đường tới `served`** — `SLOT_REPAIRED` · `PROVENANCE_PRESERVED` · `RATIO_PRESERVED` (`2/5`, `C->D`) · `GROUNDING` · `SOURCE_INVARIANTS` · `RUNTIME` · `POSTCONDITIONS` · `EXACT_ANSWER` (**`ND = 6`**) · `TRACE_CONSTRUCTION` (producer `construct_point.divide_segment`, `depends = [C,D]`) · `SCENE3D` · `SERVABLE` — **PASS toàn bộ**. Mô hình chọn `at` → **`initial_value`** (tương đương chính tắc, đã ghi trong tiêu chí **trước** lượt gọi), không dựng thêm `declare_point`; `N` vẫn không có toạ độ, `C` giữ `model_assumption`, `D` giữ `source_fact_id`, `model_assumption` **không** lan sang `N`. Chẩn đoán validator từ `4ab25e9` lần đầu được **đo hiệu lực** thay vì chỉ kiểm bằng test. **Kết luận chính là kết luận PHỦ ĐỊNH: `PERMANENT_SLOT_INSTRUCTION_NEEDED = NOT_PROVED`** — đề xuất *"thêm một dòng hướng dẫn về ô chứa toạ độ"* mà wave trước bàn giao **chưa chứng minh được là cần**; vòng sửa sẵn có đã đóng lỗ. (Chưa chứng minh cần ≠ chứng minh không cần; `n = 1`.) Token ba số không trộn: `CURRENT_WAVE_REPAIR = 3123` · `HISTORICAL_INITIAL_SYNTHESIS = 5023` · `COMBINED_OBSERVED_RECOVERY = 8146`. ⚠️ **Hai lỗ BỘ ĐO, khai trước khi dùng số** — cả hai đều làm **chốt chặn mạng offline mất tác dụng trong im lặng**, tức đe doạ chính câu *"pytest = 0 API call thật"*: (a) fixture của test probe chỉ vá `G.call_gemini`, nên `goc_call` mà probe khôi phục **chính là stub** và `PL.call_gemini` ở lại = stub **vĩnh viễn** ⇒ `test_offline_guard::test_pipeline_quen_mock_cung_bi_chan` hết raise cho mọi test chạy **sau**; (b) `block_real_network` gỡ `GEMINI_API_KEY` nhưng `db.py` gọi `load_dotenv` **lúc import** và điền lại — ẩn vì phụ thuộc **thứ tự thu thập**, xác nhận **có sẵn từ trước** bằng `git stash`. **Runner giữ nguyên TỪNG BYTE** (`runner_sha256 dad902f0…` đã nằm trong artifact bất biến; cách khôi phục của nó đúng cho lượt chạy thật vì `pipeline.py` dùng `from … import call_gemini`) — thay vào đó **khoá tiền đề bằng test**: `test_A2b` (`PL.call_gemini is G.call_gemini`) + `test_A2c` (không rò rỉ sau lượt chạy), fixture chuyển sang `MonkeyPatch.context()` vì `monkeypatch` chỉ hoàn nguyên lúc teardown. Tiêm lỗi tái hiện **đúng triệu chứng gốc** (3 failed), trả về: 17 pass. Tiền kiểm `test_repair_probe_integrity.py` **12 pass, 0 lượt gọi**. **Không đụng mã sản phẩm**: `CACHE_VERSION` 85→85 (không có đường served→refusal), candidate `36e81713…` không đóng băng lại, **6 băm model-facing byte-identical**, `PRODUCT_VARIANT` = **A**. `CAUSAL_ATTRIBUTION = LIMITED` (n=1) · `STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED`. Báo cáo `docs/POINT_INITIALIZATION_REPAIR_EFFICACY.md` | `MINIMAL_CARD_CONSOLIDATION_AND_FRESH_CONFIRMATION` |
| Hướng dẫn ngắn về xuất xứ gốc toạ độ có giúp AI tự sinh đúng không | **ĐÃ ĐO — `P1_PROVENANCE_SIGNAL = POSITIVE`, giữ A** (2026-09-07, `PROVENANCE_AFFORDANCE_AB_4_LUOT`) | `MEASUREMENT_CLASS = DEVELOPMENT_SYNTHESIS_AB` · **2 đề × 2 arm = 4 lượt** · `ANALYZE = 0` · `REPAIR = 0` · LOGICAL 4/4 · **22 982/30 000** token · `RUN_STATUS = COMPLETE`. Hai arm chỉ khác **ĐÚNG MỘT DÒNG** (+323 byte): P0 = `card_B` lượt ratio **nguyên byte**, P1 = P0 + hướng dẫn provenance (quy tắc CHUNG, không tên điểm/fact/đáp số). **Kết quả:** provenance **P0 1/2 · P1 2/2** (không ca nào P0 đúng mà P1 sai) ⇒ tín hiệu **POSITIVE**. ratio **2/2 cả hai**; điểm dẫn xuất **được dựng 2/2 cả hai**; `served` đúng **1/2 mỗi arm**, ghép cặp **1 thắng 1 thua** ⇒ `P1_SERVABLE_SIGNAL = NEUTRAL`. **Hai lượt hỏng ở HAI TRỤC KHÁC NHAU** — đây là điểm đọc chính: P0/MULTIPLE hỏng đúng trục wave đo (`E` khai toạ độ mà **thiếu cả hai** kênh xuất xứ ⇒ `input_not_grounded`); P1/RATIO hỏng ở trục **không liên quan** — đặt `at` vào `memory_declarations`, tức lớp lỗi `POINT_INITIALIZATION` đã đóng, và chẩn đoán của wave ấy phát đúng. Về provenance ứng viên ấy **làm đúng**. Token: P0 11 089 · P1 11 893; token/provenance đúng **11 089 vs 5 946**; token/served đúng 11 089 vs 11 893. `cached_content` **0 cho cả hai** ⇒ lần này **không nhiễu cache** (khác lượt trước). Kết luận token ở **mức quan sát**; chưa có đơn giá provider. ⚠️ **Đính chính bộ chấm** khai trước khi dùng số: lượt dừng ở `semantic_program` từng bị chấm `GROUNDING = PASS` — chấm PASS cho tầng **chưa bao giờ chạy**. Đã sửa và chấm lại 0 lượt gọi; đổi `P1 grounding` 2/2 → **1/2**, **không** đổi kết luận provenance (chấm từ raw candidate). Nhánh §9 áp dụng: *P1 giúp đúng trục nhưng hỏng ở TẦNG MỚI* ⇒ ghi rõ tầng, giữ kết luận provenance độc lập. **KHÔNG** đóng băng P1 (điều kiện là 2/2 provenance **và** 2/2 mô phỏng đúng). Bộ đo sửa: nhãn arm đọc từ file (tránh nhầm với PRODUCT VARIANT A) · lịch đọc từ **đăng ký** (không từ `lich_chay` vốn đánh số theo corpus đầy đủ). **Không đụng mã sản phẩm**: `CACHE_VERSION` 85→85, candidate `36e81713…` không đóng băng lại, 6 băm model-facing không đổi, `PRODUCT_VARIANT` = **A**. `CAUSAL_ATTRIBUTION = LIMITED` (n=2). Báo cáo `docs/PROVENANCE_AFFORDANCE_AB_4_LUOT.md` | `PROVENANCE_INSTRUCTION_SLOT_DISAMBIGUATION` |
| Điểm do quan hệ chia đoạn xác định phải được DỰNG, không khai thẳng toạ độ | **DONE** (2026-09-07, `DERIVED_POINT_CONSTRUCTION_ENFORCEMENT`) | `tests/geometry/test_derived_point_construction.py` **23 pass**, 1 phép tiêm · **`APPLICATION_LLM_CALLS = 0`**. Lỗ đã đo ở wave trước: khai thẳng toạ độ `P`, **bỏ câu lệnh dựng**, còn **1** câu lệnh, trace **0 khung**, `P` không có trong scene — mà vẫn **`served`** với đáp số **ĐÚNG** (`8`). `ROOT_CAUSE` theo đường chạy thật: chốt ⑥ hỏi đúng câu này rồi nhưng đọc `nhan_suy_ra`, bộ ấy chỉ khớp *'gọi/lấy X là'* và *'X là trung điểm|hình chiếu|…'* — lối nói *'nằm trên … **sao cho**'* trượt; **và** chốt ⑥ chỉ chạy trong nhánh `model_assumption` trong khi lỗ đi được **CẢ HAI** kênh xuất xứ. Sửa: **chốt ⑦** `_diem_phai_dung` đặt sau `computed` và **trước** khi rẽ kênh (nên phủ cả hai), đọc lại `SourceInvariant(segment_division)` — **không** dựng bộ nhận diện thứ hai, **không** nới `nhan_suy_ra` (hàm dùng chung nhiều wave). Mã lỗi dùng lại `DERIVED_ENTITY_WITHOUT_PRODUCER`. Ranh giới hẹp: **chỉ** bất biến **đã giải được** (`unresolved` chưa đủ để kết luận) · **chỉ** vế thứ ba `M` (hai đầu mút là điểm đầu vào, giữ nguyên quyền khai toạ độ và đặt hệ trục). **Ba đường producer giả đều đã có chủ** nên KHÔNG nới: literal→`ir_static`, bí danh sang điểm có thật→`source_invariant`, bí danh qua điểm bịa→`grounding` ⑤. Bảo toàn: ratioB **6**/**8** · `r3` sai ratio vẫn bác · `e4` **15** · `e4` sai tỉ lệ trong khối vẫn bác · phản ví dụ `396/5` vẫn bác (bổ sung bản *sau* mà artifact trước còn thiếu). Ca đúng: `P` `origin=derived`, `producer=construct_point.divide_segment`, `depends ⊇ {E,F}`. **`CACHE_VERSION` 84 → 85, BUMP** — ⚠️ khác ba bump trước: envelope cũ có **đáp số ĐÚNG**, thứ sai là **MÔ PHỎNG**. Đo bằng row thật. Bề mặt mô hình **6 băm byte-identical**. Candidate `a9289410…`→**`36e81713…`**. `test_C1` của wave trước **đã lật** từ *ghi nhận lỗ* sang *khẳng định hành vi đúng*, giữ nguyên chú thích lịch sử. Báo cáo `docs/DERIVED_POINT_CONSTRUCTION_ENFORCEMENT.md` | `PROVENANCE_AFFORDANCE_AB_4_LUOT` |
| Xuất xứ khi chọn gốc toạ độ — và độ dài đề cho có được kiểm không | **DONE (một nửa), LỖ CÒN LẠI đã khai** (2026-09-07, `FRAME_ORIGIN_PROVENANCE_AFFORDANCE`) | **`APPLICATION_LLM_CALLS = 0`** — phần A/B live **dừng theo luật §2** vì replay tìm ra lỗ nặng hơn. `tests/geometry/test_frame_origin_provenance.py` **15 pass**, 1 phép tiêm. **Replay chứng minh ①:** kênh xuất xứ **ĐÃ ĐỦ** — chỉ cần **MỘT** trong hai trường (`model_assumption` **hoặc** `source_fact_id`) trên khai báo gốc toạ độ là qua grounding; ratioB → **served** với **6** và **8** scene 4, ratioA(MULTIPLE) → qua grounding rồi bị `source_invariant` chặn vì ratio sai. **Không cần trường mới.** ⚠️ Đính chính bàn giao: `r2/ratioA` thiếu xuất xứ ở **HAI** khai báo (`C` và `D`) + một `float` `ratio_CN` mà kênh giả thiết không nhận (đúng như phải thế) ⇒ ca ấy vẫn dừng ở grounding. **Replay chứng minh ②, và đây là lý do dừng live:** đề `EF = 10`, chương trình khai **`F = [99,0,0]`** kèm `model_assumption` HỢP LỆ rồi chia đúng tỉ lệ ⇒ hệ **`served`** với **`396/5`** thay vì `8` — **đáp số SAI, im lặng**. `segment_division` kiểm TỈ LỆ, không kiểm THANG. Sửa tối thiểu, **không thẩm quyền thứ hai**: checker `segment_length` vốn hỏi đúng câu ấy và **chạy đúng**, chỉ chưa bao giờ được phát cho đề cho SỐ (bộ phát duy nhất nằm trên đường chuẩn hoá thang). Thêm `segment_relation.bat_bien_do_dai` dùng lại chính `_do_dai_doan`, phát ở cùng biên `build_request_contract`; **khử trùng** với đường thang (nhãn+giá trị viết lại thành `AB = 1` sẽ nhân đôi bất biến và nhân đôi mẫu số telemetry); hai độ dài mâu thuẫn ⇒ **không phát**. **`CACHE_VERSION` 83 → 84, BUMP** cùng loại 81→82/82→83, đo bằng **row thật**: envelope `396/5` ở v83 vẫn HIT, không qua cổng mới. Bề mặt mô hình **6 băm byte-identical**. Candidate `179793db…`→**`a9289410…`**. `PRODUCT_VARIANT` A→A. ⚠️ **LỖ CÒN LẠI, ghi bằng test ĐANG XANH** (`test_C1`): điểm đề giới thiệu như **phải dựng ra** vẫn khai thẳng toạ độ được và **bỏ câu lệnh dựng** — `nhan_suy_ra` chỉ nhận *'gọi/lấy X là'* và *'X là trung điểm|hình chiếu|…'*, không nhận *'nằm trên … sao cho'*. Đáp số vẫn đúng; thứ mất là **BƯỚC DỰNG**. `test_C2` ghi sẵn đường sửa: bộ neo `segment_relation` đã có tín hiệu ấy. Báo cáo `docs/FRAME_ORIGIN_PROVENANCE_AFFORDANCE.md` | `DERIVED_POINT_CONSTRUCTION_ENFORCEMENT` |
| Thẻ nói rõ `divide_segment.ratio` có giúp AI dựng đúng điểm chia đoạn không | **ĐÃ ĐO — `B_RATIO_SIGNAL = POSITIVE`, giữ A** (2026-09-06, `RATIO_AFFORDANCE_STAGED_RECHECK`) | `MEASUREMENT_CLASS = DEVELOPMENT_SYNTHESIS_AB` · `HELD_OUT_CLAIM = NO` · **2 đề × 2 arm = 4 lượt synthesis** · `ANALYZE_CALLS = 0` · `REPAIR_CALLS = 0` · LOGICAL 4/4 · TOKENS 20 198/30 000. **Trục `ratio`: A 0/2 · B 2/2, ghép cặp thắng 2 thua 0 hoà 0.** A viết `2/3` cho `CN:ND = 2:3` và `1/4` cho `FP = 4·PE` — đúng quy ước chia đoạn `m:n`, tức lần **tái hiện thứ BA** của cùng hiểu nhầm (`c9b` · `r3/A` · đây). ⚠️ **Cả bốn lượt, CẢ HAI arm, chết ở `grounding`** vì cùng một điều — raw candidate giống hệt nhau: gốc toạ độ (`E`/`C`) khai `[0,0,0]` mà **thiếu cả `source_fact_id` lẫn `model_assumption`**, trong khi đầu mút kia ghim đúng `do_dai_doan`. Đặt gốc toạ độ là **lựa chọn hệ trục**, và hợp đồng CÓ SẴN ô `model_assumption` cho đúng việc ấy — mô hình không dùng. Grounding **không sai**; đây là lỗ **affordance**, cùng hình dạng với `ratio`. `B_SERVABLE_SIGNAL = NEUTRAL` (cả hai arm 0/2, `SOURCE_INVARIANT`/`POSTCONDITIONS`/`SCENE3D` đều `NOT_REACHED`). **Token:** A 10 263 (0 ca đúng ⇒ `UNDEFINED`) · B 9 935 với **4 968/kết quả đúng**. ⚠️ So tổng **bị nhiễu**: `cached_content` A **2 989** · B **0**, prompt caching không kiểm soát được ⇒ chênh tổng KHÔNG quy cho delta thẻ. Tiền kiểm tất định **11 pass** trước lượt live, gồm phán quyết thẩm quyền khi hai nguồn mâu thuẫn: **không nguồn nào thắng** — mâu thuẫn ĐỌC ĐƯỢC ⇒ `unresolved` ⇒ chặn cả chương trình theo dữ kiện lẫn theo đề. Ngân sách nay **theo lượt chạy** và **dự trữ đủ cả cặp** trước khi bắt đầu — sửa đúng giới hạn guard mà lượt trước ghi (vượt trần 47 303/40 000). Runner nay gắn `source_invariants` như `build_request_contract`, thêm chiều chấm `SOURCE_INVARIANT_RESULT`. **Không đụng mã sản phẩm**: `CACHE_VERSION` 83→83, candidate `179793db…` không đóng băng lại, 6 băm model-facing không đổi, `PRODUCT_VARIANT` = **A**. `CAUSAL_ATTRIBUTION = LIMITED` (n=2 cặp). Báo cáo `docs/RATIO_AFFORDANCE_STAGED_RECHECK.md` | `FRAME_ORIGIN_PROVENANCE_AFFORDANCE` |
| Phủ quan hệ chia đoạn cho LỚP CÂU tổng quát + trạng thái chưa-kiểm-được | **DONE** (2026-09-06, `SEGMENT_RELATION_COVERAGE_HARDENING`) | `tests/geometry/test_segment_relation_coverage.py` **27 pass**, 4 phép tiêm · **0 lượt gọi model**. `ROOT_CAUSE`: bộ đọc wave trước gộp neo và quan hệ vào MỘT mẫu nên **không đọc được `e4`** — neo dạng **cắt** (*'cắt PQ tại điểm T'*), từ nối **'bằng'**, và độ dài cả đoạn ở **câu khác** (*'chiều cao PQ bằng 28'*). Hệ quả đo được: `divide_segment(P,Q,1/2)` — sai dữ kiện nhưng VẪN dựng được thiết diện — **`served`** với bán kính **21/2** thay vì 15. Sửa bằng **tách hai pha** (neo → bộ ba; quan hệ + độ dài → tìm trên TOÀN BỘ đề + mọi `InputFact`), luật ghép là *'cùng xác định một bộ ba'* chứ không phải *'cùng một câu'*; ghép nhãn+giá trị của `InputFact` (chỉ giá trị SỐ) là đọc đúng hợp đồng. Phủ **3 neo × 4 quan hệ**. Thêm trạng thái **CHẶN** `SOURCE_INVARIANT_NOT_CHECKABLE` (trường `unresolved`, tách hẳn khỏi `not_checkable` vốn KHÔNG chặn): thấy bộ ba + mảnh quan hệ + nguồn mà không tính được `t` ⇒ bác; VIOLATED thắng khi có cả hai. `e4` nay: `t=5/7` **served** bán kính 15 scene 12 · `t=1/2` **bác** ở `source_invariant` · đảo hướng `(Q,P,2/7)` dựng đúng cùng điểm ⇒ **served**. Không test nào đọc tên `P/Q/T` để quyết định (đổi tên và đổi số đều giữ kết quả). **`CACHE_VERSION` 82 → 83, BUMP** cùng loại 81→82 — chiều đổi `served → từ chối`, đo bằng **row `e4` thật**: envelope `21/2` ở v82 vẫn HIT, không qua cổng mới. Bề mặt mô hình **6 băm byte-identical**. Candidate `1151bc6f…`→**`179793db…`**. ⚠️ Đính chính từ vựng: lối nói ngoài mẫu là **`NOT_EXTRACTED`** — giới hạn PHỦ, **không phải** fail-closed (wave trước gọi sai). `PRODUCT_CAPABILITY_CHANGED = NO`. Báo cáo `docs/SEGMENT_RELATION_COVERAGE_HARDENING.md` | `RATIO_AFFORDANCE_STAGED_RECHECK` |
| Hình dựng phải thoả QUAN HỆ CHIA ĐOẠN của đề trước khi được phục vụ | **DONE** (2026-09-06, `SEGMENT_RELATION_CONSISTENCY_VERIFICATION`) | `tests/geometry/test_segment_relation_consistency.py` **36 pass**, 3 phép tiêm · **0 lượt gọi model**. `ROOT_CAUSE`: `source_fact_id` chứng minh **nguồn tồn tại**, KHÔNG chứng minh **hình dựng thoả nội dung** của nguồn — nên `r3/A` của lượt A/B (`FP = 4·PE`, mô hình viết `divide_segment(E,F,1/4)`) được **`served`** với `PF = 15/2` thay vì `8`. Ba tầng đều làm đúng: kernel thi hành đúng chương trình đã nhận, `check_distance` đo đúng khoảng cách tới điểm ĐÃ DỰNG, grounding thấy có `source_fact_id` nên cho qua. Hỏng **IM LẶNG**. **Khả năng biểu đạt = PARTIAL** (đo, không đoán): hợp đồng ĐÃ có `SourceInvariant` có cấu trúc + dispatch theo `kind` + cổng P0 so `Fraction` — nhưng chỉ có `segment_length`, và bộ phát duy nhất chỉ chạy trên đường chuẩn hoá thang ⇒ **nhánh A**, dùng lại thẩm quyền, không dựng cổng thứ hai. Biểu diễn: `kind="segment_division"`, `points=(A,B,M)` hướng A→B **của ĐỀ**, `expected = t` hữu tỉ — **0 trường mới**. Đọc từ **câu văn đề** (4 mẫu: tỉ số · bội số · độ dài một nhánh · trung điểm), không khớp ⇒ KHÔNG phát. Kiểm trên HÌNH: giải `t` rồi đối chiếu cả ba thành phần (chính là phép kiểm thẳng hàng), so `Fraction`; `(E,F,1/5)` và `(F,E,4/5)` đều được phục vụ, `2/10 ≡ 1/5`. `r3/A` nay bác ở stage **`source_invariant`** (`NORMALIZED_SOURCE_VIOLATED`), thông điệp nêu đủ 5 thứ; bản đúng vẫn `served` `PF=8` scene 5. Gold `r1`–`r4` **4/4 served**. **`CACHE_VERSION` 81 → 82 — BUMP, ngược chiều hai wave trước**: chiều đổi là `served → từ chối`, mà `served` LÀ thứ được cache. Chứng minh bằng **row thật**: envelope `PF=15/2` ghi ở v81 vẫn HIT và trả về không qua cổng mới. Bề mặt mô hình **6 băm byte-identical**. Candidate `c39f7358…`→**`1151bc6f…`** (89→90 file). Đính chính khoá liên-wave: `test_CA1` thôi ghim hằng `"81"`. `PRODUCT_CAPABILITY_CHANGED = NO`. ⚠️ Giới hạn: đề `e4` ngoài 4 mẫu ⇒ không phát bất biến, giữ hành vi cũ. Báo cáo `docs/SEGMENT_RELATION_CONSISTENCY_VERIFICATION.md` | `RATIO_AB_CONFOUND_REMOVAL_REPEAT` |
| Mô hình hiểu `divide_segment.ratio` là tham số `t` chưa | **ĐÃ ĐO — tín hiệu ĐĂNG KÝ KHÔNG ĐẠT, giữ A** (2026-09-06, `DIVIDE_SEGMENT_RATIO_AFFORDANCE_AB`) | `MEASUREMENT_CLASS = DEVELOPMENT_SYNTHESIS_AB` · `HELD_OUT_CLAIM = NO` · **`ANALYZE_LIVE_CALLS = 0`** (hợp đồng CỐ ĐỊNH đã kiểm) · 8/8 lượt tổng hợp · 8/32 vật lý. `ROOT_CAUSE` affordance đo được: thẻ in **`ratio:tên`** — nhãn KIỂU SAI (`_la_ten` trả True cho mọi `str` trần) **và bỏ chú thích**, vì `_vai_tro` (in `Field.description`) chỉ chạy ở nhánh ô-TÊN; nên mô tả `"phân số, vd 2/3"` có sẵn ở `contract.py:625` **chưa bao giờ tới thẻ**. Delta đăng ký: **+60 byte, ĐÚNG 1 dòng** qua `_VAN_XUOI['ratio']`; `responseSchema` KHÔNG đổi (hai arm dùng lược đồ y hệt); `card_A` byte-đối-byte với thẻ sản phẩm. Thiết kế thay thế (`Field.description` + `_vai_tro` mọi nơi) đã đo và LOẠI: +1857 byte/17 dòng, sẽ làm mất khả năng quy kết. **Kết quả:** trục `ratio` A 2/3 → B **3/3** ca mục tiêu, thắng 1 thua 0; nhưng tiêu chí ĐÃ ĐĂNG KÝ là `POSITION_CORRECT` và ở đó **A 3/4 · B 1/4** — **3/4 lượt B chết ở `grounding` vì thiếu `source_fact_id`, KHÔNG liên quan `ratio`**; n=4 one-shot không tách được delta khỏi nhiễu ⇒ **giữ baseline A**, không nới luật. **Chi phí: B ĐẮT hơn ~2,6×** — token/ca-served-đúng A **8 435** · B **21 998** (cả hai mẫu số dương). Prompt B chỉ +100 token; chỗ chênh nằm ở `thoughts` (A 9 545 · B 6 262). ⚠️ `TOKEN_CEILING_EXCEEDED` 47 303/40 000 — guard kiểm theo CẶP, không cắt được giữa cặp. ⚠️ **Đính chính bộ chấm** (khai trước khi dùng số): `T_CORRECT` so CHUỖI thay vì HỮU TỈ nên `9/12` bị chấm FAIL dù `9/12 = 3/4`; đã chấm lại **0 lượt gọi**, bảng gốc giữ nguyên, **không đổi quyết định**. ⚠️ Phát hiện an toàn: `r3/A` **served một đáp số SAI** (`15/2` thay vì `8`) — hiểu nhầm `ratio` hỏng **IM LẶNG**, không fail-closed. Toàn vẹn runner chứng minh TRƯỚC lượt live bằng stub chạy chính `main_async`: `tests/geometry/test_runner_ratio_ab.py` **23 pass**. Wave **KHÔNG chạm `MEASURED_SYSTEM_PATHS`**: `CACHE_VERSION` 81→81, candidate `c39f7358…` không đóng băng lại, `PRODUCT_VARIANT` = **A**. `CHI_PHI_TOAN_PIPELINE = NOT_MEASURED`. Báo cáo `docs/DIVIDE_SEGMENT_RATIO_AFFORDANCE_AB.md` | `RATIO_AB_CONFOUND_REMOVAL_REPEAT` |
| Nghĩa vụ nối với vật khi đề đặt NHÃN còn chương trình đặt TÊN khác | **DONE** (2026-09-06, `OBLIGATION_CONTAINER_NAME_BINDING`) | `tests/geometry/test_obligation_container_binding.py` **27 pass** (nền đỏ **11/27**), 11 phép tiêm/phản ví dụ · 0 lượt gọi model. **GIẢ THUYẾT BÀN GIAO BỊ BÁC**: *"container không phải định danh"* sai — `e5` container `(j)` cũng có dấu ngoặc và **served**. `ROOT_CAUSE` thật: khi container là **nhãn đề đặt cho vật DẪN XUẤT** và vắng mặt khỏi chương trình, việc nối rơi **hoàn toàn** vào ba lưới CHÍNH TẢ — `e1` qua là may rủi (`ten_loi('(u)')==ten_loi('u')`), `e4` trượt vì `ten_loi('duong_tron_t')=='tront'` (phụ tố `duong_` dán `tron` vào `t`); net ⓪ không chạy được vì nó đòi container CÓ MẶT. Lỗ thứ hai tìm được khi đi tìm bằng chứng: mô hình **đã tự khai** `source_fact_id` ở `assign` (dữ kiện *"…cắt hình nón theo đường tròn (t)"*) nhưng `AssignStmt` không có ô ấy ⇒ Pydantic `extra="ignore"` **vứt im lặng** — đúng lớp lỗi `at` của wave trước. Sửa: `_nang_xuat_xu_cau_lenh` chở lời khai về khai báo (chỉ điền chỗ trống, không đẻ khai báo mới) + net ⓪b `_theo_xuat_xu_du_kien` chạy khi container VẮNG MẶT, đứng **SAU** ba lưới nên `e1`/`e5` không đổi một chút nào; bộ lọc witness **rút ra dùng chung** với net ⓪. ⚠️ **KHÔNG thêm ô vào `AssignStmt`**: `generate_json_schema()` là `responseSchema` thật và thẻ dẫn từ `model_fields`, nên đó là đổi **affordance** — phải đo bằng A/B, mà wave này 0 quota (bản thử đầu làm đỏ 9 test, gồm `test_AB1` và `test_E8`). `MODEL_FACING_DELTA = NONE`: schema `9b186828…` · thẻ == `card_A.txt` · prompt · capability **nguyên**. Gỡ tấm che thì `e4` lộ khiếm khuyết **thứ hai của MÔ HÌNH**, độc lập: `ratio 5/2` (quy ước chia đoạn) thay vì tham số `t = 5/7` ⇒ `CURVED_PLANE_DOES_NOT_CUT`; sửa **một token** trên hợp đồng nguyên văn ⇒ **`served`, bán kính 15**, và delta ấy MỘT MÌNH không cứu được ca (`test_B2b`). Cùng lớp `c9b`. `CACHE_VERSION` **81→81 KHÔNG bump** (3 căn cứ đo: bề mặt nguyên · chỉ *từ chối→phục vụ* mà `main.py` chỉ cache `ok` · phép nâng KHÔNG làm grounding chặt thêm — bịa `source_fact_id` ở mọi `assign` của `e1`/`e5` vẫn `served`). Candidate `4f813a38…`→`c39f7358…`. Báo cáo `docs/OBLIGATION_CONTAINER_NAME_BINDING.md` | `DIVIDE_SEGMENT_RATIO_AFFORDANCE_AB` |
| Khai báo điểm: `at` vs `initial_value` | **DONE** (2026-09-06, `POINT_INITIALIZATION_CONTRACT_ALIGNMENT`) | `tests/semantic_program/test_point_initialization_contract.py` **30 pass**, 4 phép tiêm · 0 lượt gọi model. `ROOT_CAUSE`: `MemoryDeclaration` không khai `model_config` ⇒ Pydantic `extra="ignore"` **bỏ IM LẶNG** khoá `at` mà mô hình đặt nhầm vào khai báo; còn lại `initial_value: null`, và lời từ chối *"có khai báo nhưng chưa có giá trị"* **đúng sự thật, sai chỗ**. Vá tại `validate_semantic_program` — biên CUỐI còn giữ đầu vào thô — trả chẩn đoán nêu đường dẫn JSON · trường đã gửi · chủ sở hữu (`declare_point`) · ô chính tắc (`initial_value`), tất cả **dẫn xuất** từ model. TỪ CHỐI chứ không quy đổi, theo đúng doctrine `DeclarePointStmt` (*"ánh xạ ấy không bảo toàn xuất xứ"*). Replay: **`e6` một delta là đủ** (`served`, `400π`, scene 8); **`e2`** mở tới `grounding` rồi cần xuất xứ cho `X` (`served`, `121π`, scene 12). ⚠️ Luật thu hẹp SAU khi replay corpus lịch sử bác oan **3/5** chương trình AI sinh đặt `label` trong khai báo: chỉ báo khi ô bị bỏ là **ô giá trị thô** (`Any`/`list[Any]`), không báo khoá trang trí. Chẩn đoán tới được vòng sửa và vòng sửa **khép được** (test_D1/D2). Xuất xứ **không nới** (4 phản ví dụ; ranh giới thật đo lại: mục mang TÊN không ràng buộc toạ độ, `[0,0,0]` miễn đối chiếu). **ĐÍNH CHÍNH A/B**: điều kiện ca âm của `MODEL_FACING_OPERATION_AFFORDANCE_ALIGNMENT` KHÔNG đạt ⇒ nhánh đăng ký "chưa đạt" được thực hiện — thẻ sản phẩm **về A** (`e0fbbc84…`), B đóng băng thành `card_B.txt` làm ứng viên thử nghiệm, `SELECTOR_GAIN_OBSERVED = YES` giữ nguyên. `CACHE_VERSION` **81→81 KHÔNG bump**, kiểm bằng row cache thật. Candidate `67ad7f4f…`→`4f813a38…`. Báo cáo `docs/POINT_INITIALIZATION_CONTRACT_ALIGNMENT.md` | `OBLIGATION_CONTAINER_NAME_BINDING` |
| Thẻ văn phạm nói ra KIỂU KẾT QUẢ của từng phép | **DONE** (2026-09-05, `MODEL_FACING_OPERATION_AFFORDANCE_ALIGNMENT`) | A/B ghép cặp, 24 lượt gọi logic/trần 24, `MEASUREMENT_CLASS = DEVELOPMENT_AB` · `HELD_OUT_CLAIM = NO`. **Chọn đúng toán tử ngay lượt đầu: A 1/6 → B 6/6; thắng 5 · thua 0. `served` lượt đầu A 0/6 → B 3/6, cả 3 khớp đáp số.** Ca đối chứng đa diện: cả hai arm chọn `construct_section` (B không khái quát quá tay). `ROOT_CAUSE` đã sửa: thẻ in TOÁN HẠNG của mọi phép mà **không in kiểu KẾT QUẢ của phép nào**, dù `_CHU_KY` (vế phải) và `_KIEU_DUNG` đã mang sẵn — nhãn `[BIỂU THỨC→assign]` nói cửa tiêu thụ, không nói kiểu ra. Phụ: danh sách kiểu khai được là bản CHÉP TAY đã trôi (thiếu `circle3`, `curved_solid` từ wave cong 2026-09-03), nay dẫn xuất. Delta **+203 byte**, phân loại NHÃN THIẾU, trần thẻ hình học 5510→5720; thẻ đầy đủ KHÔNG đổi. Gold preflight 7/7 · exact 7/7 · Scene3D 7/7 · biên PASS; runner chứng minh bằng provider stub trước lượt live (18 test). `CACHE_VERSION` **81→81 KHÔNG bump** (thẻ đổi thứ mô hình VIẾT RA, không đổi nghĩa chương trình; `main.py` chỉ cache `ok`), identity khoá lại `9a230794…`; candidate `a5b63aa3…`→`67ad7f4f…`. Chặn còn lại đo được: xuất xứ điểm có tên 4/8 ca, liên kết tên analyze/synthesis 1/8. Báo cáo `docs/MODEL_FACING_OPERATION_AFFORDANCE_ALIGNMENT.md` | `NAMED_POINT_PROVENANCE_AFFORDANCE_ALIGNMENT` |
| Khối cong khai bằng `radius + height` cắt được bằng mặt phẳng | **DONE** (2026-09-05, `CURVED_SCALAR_AXIS_INTERSECTION_FIX`) | `tests/geometry/test_curved_scalar_axis_intersection.py` **41 pass** (nền đỏ **34/41**), 5 phép tiêm · `ROOT_CAUSE`: `_giao_tron_xoay` đọc `truc` (= vectơ KHÔNG khi khai bằng `height`) thay vì `huong_truc` — thuộc tính `CURVED_CONSTRUCTION_GROUNDING_FOUNDATION` thêm đúng cho ca này mà consumer không bao giờ chuyển sang. Hai hỏng: chốt ⊥ trục **im lặng nhận mọi mặt phẳng** (cross với vectơ không luôn bằng không) và `d·d = 0` ném `ZeroDivisionError` trần, phân loại sai thành `capability_gap`, rò tên ngoại lệ Python lên `details`. Vá: đọc `huong_truc`; tâm = giao điểm trục×mặt phẳng (bỏ `anchor + truc·t`); kiểm biên bằng bình phương nên không cần `√h`; đổi thang `L→t` CHỈ ở nhánh vô hướng (`_ti_le_doc_truc`) — nhánh khai bằng điểm **tương đương đại số** với luật cũ. Oracle 7/7 khớp giá trị tính trực tiếp; parity điểm↔vô hướng 7/7 (tâm · mặt phẳng · `radius_sq` · bán kính · diện tích). Đường sản phẩm `served` 2/2 (trụ `9`/`81π` · nón `6`) với Scene3D đúng producer/depends. Biên giữ nguyên mã: xiên · ngoài chiều cao · qua đỉnh · nón `h` vô tỉ (`OUTSIDE_V1_CLOSURE`, nêu lối đi thay thế). Sáu băm model-facing **byte-identical** ⇒ `CACHE_VERSION` **81→81, KHÔNG bump** (`main.py` chỉ cache `status == "ok"`, mà bản vá chỉ biến *từ chối→phục vụ*); candidate `d105f83e…`→`a5b63aa3…`. 0 lượt gọi model. Báo cáo `docs/CURVED_SCALAR_AXIS_INTERSECTION_FIX.md` | `MODEL_FACING_OPERATION_AFFORDANCE_ALIGNMENT` |
| Mô hình có TỰ tìm ra `intersect_plane_curved` không | **ĐÃ ĐO — `WEAK`** (2026-09-05, `CURVED_SECTION_MODEL_DISCOVERABILITY_PROBE`) | `MEASUREMENT_CLASS = DEVELOPMENT_DIAGNOSTIC` · `HELD_OUT_CLAIM = NO` · 26 lượt gọi logic / trần 32 · 150 854 token. **Lượt đầu chọn đúng toán tử 0/6; chọn `construct_section` 8/8 — kể cả ca đa diện (ở đó nó ĐÚNG) và ca âm.** Sau MỘT lượt sửa, 6/6 chuyển sang `intersect_plane_curved` + `circle3`: câu `IR_OPERAND_TYPE: cần solid, có curved_solid` là bộ dạy 100%. `EVENTUAL_SERVABLE` 0/6 cong · **1/1 đối chứng đa diện `served` với `8√3` chính xác**. Hai `ROOT_CAUSE` đủ bằng chứng §7: ① `construct_section` là mặc định phổ quát (6/6); ② `analyze` phát container không phải định danh — `(σ)`,`(δ)`,`(λ)` — trái chính chỉ dẫn `geometry_analyze.md:38` *"tên biến snake_case, không dấu"*, và `analyze` **không có vòng sửa** nên không cứu được. Gold preflight 7/7 · exact 7/7 · Scene3D 7/7 · biên PASS · `RUNNER_INTEGRITY` 31 test. ⚠️ **Lỗi hệ tìm được trong preflight, đăng ký trước, CHƯA sửa**: `CURVED_SCALAR_DECLARED_SOLID_CANNOT_BE_CUT` — trụ/nón khai bằng `height` ném `ZeroDivisionError` trần vì `_giao_tron_xoay` đọc `s.truc` thay vì `s.huong_truc`; không kích hoạt lần nào trong lượt đo (mô hình khai bằng `apex_or_top` 8/8). Mã sản phẩm · lược đồ · thẻ · prompt · `CACHE_VERSION` 81 · candidate `d105f83e…` **không đổi**; V3 không chạy lại. Báo cáo `docs/CURVED_SECTION_MODEL_DISCOVERABILITY_PROBE.md` | `MODEL_FACING_OPERATION_AFFORDANCE_ALIGNMENT` |
| Thiết diện tròn `intersect_plane_curved → circle3 → measure(radius\|area)` | **ĐÃ PHÁN QUYẾT — KHÔNG CÓ KHOẢNG TRỐNG** (2026-09-05, `CURVED_SECTION_RADIUS_PATH_ADJUDICATION`) | `tests/geometry/test_curved_section_radius_path.py` **32 pass**, **11 phép tiêm** · replay tất định chứng minh đường đã thông đủ 10 tầng (IR → `_CHU_KY` → `BANG_PHEP_DO`/`_KIEU_DO` → cổng phủ → kernel → bất biến `radius_sq>0` → hậu điều kiện → `scene3d` → `scene3d-view.tsx:171`): `W_R=9` · `W_A=81π` (trụ), `W_R=6` (nón, tỉ lệ `(1−t)²`). Ablation vét cạn trên **chính chương trình mô hình đã sinh**: `C5B_MINIMAL_DELTA = 2` (`khai[C:circle3]` + `producer`) — `hinh_tru: solid→curved_solid` **KHÔNG** load-bearing; `C9B_MINIMAL_DELTA = 3`, và `c9b` có **hai** khiếm khuyết mô hình độc lập (`ratio 9/6` là `t`, đúng phải `3/5`) mà cổng phủ che cái thứ hai. **Mã sản phẩm · lược đồ · prompt · `CACHE_VERSION` (81) · candidate (`d105f83e…`) đều KHÔNG đổi**; 0 lượt gọi model. Đính chính dự đoán `CURVED_SECTION_RADIUS_COVERAGE` của wave trước (nó dự đoán một khoảng trống không tồn tại). Phát hiện phụ **chưa sửa, đã khoá**: cổng phủ tin `memory_declarations` còn thẩm định tĩnh suy kiểu từ câu lệnh dựng. Báo cáo `docs/CURVED_SECTION_RADIUS_PATH_ADJUDICATION.md` | `CURVED_SECTION_MODEL_DISCOVERABILITY_PROBE` |
| Witness của nghĩa vụ đại lượng kiểm qua câu lệnh sinh nó | **DONE** (2026-09-05, `CURVED_DISTANCE_WITNESS_VERIFICATION`) | `tests/geometry/test_curved_distance_witness.py` **18 pass** (nền đỏ 7/18), 10 phép tiêm · `c7a` nay SERVABLE: coverage PASS · `l=13 · V=100π · Sxq=65π` · postconditions PASS · resolver `phan_giai_witness` dùng chung cho cổng phủ và hậu điều kiện (khoá bằng quét AST); attachment chứng minh bằng `_phu_thuoc`, phản ví dụ `test_F8` · `_theo_witness_do` thu hẹp về phép đo một toán hạng · lược đồ/thẻ/prompt/capability **không đổi**; `CACHE_VERSION` 80→81 vì chiều THU HẸP tạo stale thật. Báo cáo `docs/CURVED_DISTANCE_WITNESS_VERIFICATION.md` | `CURVED_SECTION_RADIUS_COVERAGE` |
| Nghĩa vụ `area` của mặt cầu ≡ `lateral_area` | **DONE** (2026-09-05, `CURVED_OBLIGATION_SURFACE_ALIGNMENT`) | `tests/geometry/test_curved_obligation_surface.py` **30 pass** (nền đỏ 21/30), 10 phép tiêm · `c1a` nay đi TRỌN: coverage PASS · `volume 972π` · `area 324π` · postconditions PASS · servable · trụ/nón GIỮ phân biệt `area`/`lateral_area` · thẩm quyền là MỘT cột `KHOI_CONG.nghia_vu_area_la` + helper `nghia_vu_chinh_tac`, cả cổng phủ lẫn hậu điều kiện gọi chung (khoá bằng quét AST) · lược đồ/thẻ/prompt/capability **không đổi**; `CACHE_VERSION` 79→80 theo LUẬT (đổi policy định tuyến) — kiểm cache cho thấy KHÔNG envelope nào hoá sai vì bản từ chối chưa bao giờ được cache. Báo cáo `docs/CURVED_OBLIGATION_SURFACE_ALIGNMENT.md` | `CURVED_DISTANCE_WITNESS_VERIFICATION` |
| Runner acceptance chấm ở đúng tầng sản phẩm | **DONE** (2026-09-05, `ACCEPTANCE_POST_MODEL_PATH_ALIGNMENT`) | `tests/test_acceptance_post_model_path.py` **24 pass**, 9 phép tiêm · certifier nhãn **`ACCEPTANCE_POST_MODEL_PATH_INTEGRATION PASS`** + `READY_FOR_FUTURE_CURVED_ACCEPTANCE YES` · đáp số nay đọc từ `outcome.final_memory` (không từ `scene3d`), cảnh từ `pipeline._dung_scene3d`, phán quyết từ `acceptance_verdict.phan_loai`; bốn cột tách rời với `c7a` làm fixture chuẩn · runner `6570b57b…`→`3cabd207…`, certifier `ce0d44d9…`→`bbbed77b…`; scorer/threshold/rubric/loader/candidate/CACHE_VERSION **không đổi**; V3 gốc byte-identical, 0 lượt gọi. Báo cáo `docs/ACCEPTANCE_POST_MODEL_PATH_ALIGNMENT.md` | `CURVED_OBLIGATION_SURFACE_ALIGNMENT` |
| Đường chạy live V3 dùng pool đã niêm phong | **DONE** (2026-09-05, `V3_LIVE_ENTRYPOINT_WIRING_REPAIR`) | `tests/test_v3_live_entrypoint_wiring.py` **37 pass** — chạy chính `main_async`, 10 phép tiêm · `certify_acceptance_runner.py` exit 0 với nhãn mạnh **`V3_LIVE_ENTRYPOINT_INTEGRATION PASS`** · runner `55be22b6…`→`6570b57b…`, certifier `81799613…`→`070189b5…`; candidate `a696200e…` · pool `36c2153e…` · seal · `CACHE_VERSION 78` **không đổi**; `seed`/`da_rut` vẫn `null`, 0 lượt gọi model. Báo cáo `docs/V3_LIVE_ENTRYPOINT_WIRING_REPAIR.md` | `INDEPENDENT_CURVED_V3_LIVE_ACCEPTANCE` |
| **Nghiệm thu V3 hình cong (held-out)** | **ĐÃ ĐO — `FAIL`** (2026-09-05) | `EVALUATOR_INDEPENDENCE = OPERATOR_WAIVED` · `MEASUREMENT_CLASS = INTERNAL_ONE_SHOT_ACCEPTANCE` — phiên đo cũng là phiên sửa bộ đo, miễn trừ do người vận hành cấp. `DRAW_COUNT=1` · seed `5324284654432805119` · `CASE_SET_HASH eb1c402a…` · 26/78 lượt gọi · `RUN_VALIDITY=VALID` · danh tính 8/8 băm không trôi. **0/9 servable · ball 0/3 · cylinder 0/3 · cone 0/3 · âm 4/4 fail-closed nhưng 1/4 chạm ranh giới.** ⚠️ ĐÍNH CHÍNH 2026-09-05 (`V3_PRODUCT_PATH_PARITY_CORRECTION`, artifact `d01578c8…`): đáp số đúng 0/9 → **1/9**, Scene3D 0/9 → **1/9**, `c7a` MODEL → **SYSTEM**; servable và verdict tổng không đổi. Gốc: CONSTRUCTION-GROUNDING (§8 báo cáo), không phải derived-scalar (`NOT_MEASURED` — không ca nào rút trúng). Artifact `docs/evaluation/geometry/curved-acceptance-v3/` (`curved_acceptance.json 70d47a95…` · `attribution.json 280a3fe1…`); báo cáo `docs/CURVED_V3_LIVE_ACCEPTANCE.md` | **`CURVED_CONSTRUCTION_GROUNDING_FOUNDATION`** |
| ~~Nghiệm thu V3 (trước lượt chạy)~~ | ~~BLOCKED — `NOT_MEASURED`~~ (2026-09-05) | `PRE_DRAW_GUARD = BLOCKED` · `CASES_DRAWN = NO` · `seed = null` · `APPLICATION_LLM_CALLS = 0`. Tiền kiểm đo lại ĐẠT toàn bộ (candidate `a696200e…` 89 file verify exit 0 · pool `36c2153e…` 26/13 ô · runner `55be22b6…` · scorer `4f7cae90…` · threshold `460e0ce5…` v1.1.0 · rubric `d44f2b7c…` · loader `b51e936f…` · pytest **3518 pass** · certifier **PASS**), nhưng **đường chạy live** hỏng hai chỗ: `main_async` chạy corpus V1/V2 thay vì pool đã rút và không ghi `manifest.json`; `mong` pool là `list` còn runner đòi `set`. Artifact: `docs/evaluation/geometry/curved-v3/PREDRAW_GUARD_2026-09-05_INDEPENDENT.json` (`3ade2a9e…`); báo cáo `docs/V3_LIVE_ENTRYPOINT_INTEGRATION_BLOCKER.md`. ✅ **Hai blocker ĐÃ ĐÓNG** cùng ngày (dòng trên) — nhưng lượt đo vẫn `NOT_MEASURED`: pool chưa rút, seed chưa dùng | **`INDEPENDENT_CURVED_V3_LIVE_ACCEPTANCE`** |

## 4b. Wave 5 — hoạt hình → công cụ học tập

| Owner / Feature | Trạng thái | Bằng chứng | Wave kế |
|---|---|---|---|
| `binary.base_conversion` trả lời không cần Play | **DONE (W5)** | BEFORE 0 tin@cursor0, đáp án `7EA` vắng mặt → AFTER 17 tin, đọc được; 4 bề rộng | — |
| `binary.character_encoding` bảng đủ hàng | **DONE (W5)** | BEFORE dãy bit của T/i/n vắng ở cursor 0 → AFTER đọc được; 4 bề rộng | — |
| `web.style_model` công cụ màu RGB | **DONE (W5)** | 4 → 7 ô điều khiển; ba kênh 0–255 qua `set_param` → `module.apply` | — |
| `web.style_model` — THAO TÁC TRỰC TIẾP | **DONE ở tầng module (5443c51)** | `direct-manipulation-w4b4d.test.tsx`: chọn nút trên sân khấu + dời khối (`move`, miền HOÁN VỊ) đi qua `module.apply`. Bằng chứng TRÌNH DUYỆT: **NO_EVIDENCE** | **W12** |
| Miền màu nới bảy ô → 24 bit | **DONE (W5)** | validator hai tầng + `CACHE_VERSION` 28→29 (ba chỗ) | — |
| Oracle độc lập ba target | **DONE (W5)** | `parseInt`/`toString(base)` · `codePointAt`/`toString(2)` · số học chuỗi hex | — |
| Tiêm lỗi W5 | **13/13 BỊ BẮT** | hai phép tìm ra LỖ GUARD THẬT (cột thập phân renderer; chiến lược diễn giải sau khi đổi cơ số) — đã vá. #12/#13 chạy ở preflight W6: đổi bảng mã chỉ-đổi-nhãn · mã sản phẩm rẽ nhánh theo nguồn envelope | — |
| Quyết định W3 bị W5 đảo | **ĐÃ KHAI** | ba guard "không lộ đáp án sớm" viết lại về bảng chia + băng kết luận, không xoá | — |
| Yêu cầu transport (đầu vào W7) | **ĐÃ GHI** | base_conversion + character_encoding: TRACE TUỲ CHỌN · web.style_model: RESET ONLY | **W7** |

## 4c. Wave 6 — công cụ là chính, thử thách là phụ

| Owner / Feature | Trạng thái | Bằng chứng | Wave kế |
|---|---|---|---|
| Thử thách đóng mặc định | **ĐÃ CÓ TỪ W4B-2Z** | `loadEnvelope` đặt `challengeOpen/exploreOpen: false`; nay khoá bằng guard | — |
| Tính đúng sai do engine sở hữu | **DONE** | `PredictionBar` chỉ đọc `prediction.verdict`; guard quét mã sản phẩm | — |
| Băng phán quyết không lấn cơ chế | **DONE** | `.result-banner` giữ `width: fit-content`; guard đọc CSS | — |
| Lối vào/ra thử thách tiếp cận được | **DONE (W6)** | **khiếm khuyết W6 tìm ra**: trước đây chỉ có `setOpened(true)` — cửa MỘT CHIỀU. Nay có nút Đóng + phím Esc + trả tiêu điểm về nút mở | — |
| Manifest trải nghiệm 23 target | **DONE (W6)** | `experience-manifest.test.ts` → `docs/evaluation/m20/experience-manifest.json` | — |
| Phân loại transport (đầu vào W7) | **DONE (W6)** | **13 FULL_TRACE · 7 OPTIONAL_TRACE · 3 RESET_ONLY**, mỗi target một lý do cơ chế | **W7** |
| Con số transport từng giả | **ĐÃ SỬA (W6)** | mặc định "có timeline ⇒ FULL_TRACE" cho ra 18; bỏ mặc định, khai đủ ⇒ 13/7/3 | — |
| Tiêm lỗi W6 | **8/8 BỊ BẮT** | thử thách tự mở · kết quả bị giấu · băng phán quyết to · khám phá chấm điểm · UI tự chấm · cửa một chiều · không trả tiêu điểm · trace-first bị hạ | — |
| Chứng nhận tương tác toàn danh mục | **NO_EVIDENCE** | manifest MÔ TẢ hiện thực, không cấp chứng nhận | **W12** |

## 4d. Wave 7 — khay điều khiển thuộc workspace

| Owner / Feature | Trạng thái | Bằng chứng | Wave kế |
|---|---|---|---|
| Khay tách khỏi bề rộng cơ chế | **DONE (W7)** | BEFORE cơ chế lệch 849px / khay lệch 849px → AFTER khay lệch **0px**; 4 bề rộng | — |
| Chế độ transport từ CHÍNH SÁCH | **DONE (W7)** | `transport-policy.ts` — 23 target khai đủ, `transportModeOf` không có mặc định | — |
| Suy diễn `stepCount` bị bỏ | **DONE (W7)** | trước W7 dải phân loại bằng `stepCount > 1`; nay đọc chính sách, guard khoá phép gán | — |
| Dòng thời gian tuỳ chọn gập mặc định | **DONE (W7)** | "Xem cách thực hiện" / "Ẩn các bước"; trạng thái TRÌNH BÀY, không vào store | — |
| Soát transport toàn danh mục | **DONE (W7)** | 23/23 khay đúng 1120px, 1 hàng, 0 tràn, 0 hở >24px | — |
| Tiêm lỗi W7 | **8/8 BỊ BẮT** | hai phép tìm ra LỖ GUARD THẬT: phép gán chế độ; sàn cột chỉ khoá một biến thể | — |
| Quyết định M19 bị W7 đảo | **ĐÃ KHAI** | M19 cố ý buộc khay bằng cột nội dung; W7 đổi sang thẳng TÂM thay vì thẳng MÉP | — |
| Tiêm lỗi W7 | **11/11 CÓ BẰNG CHỨNG** | 5 phép tĩnh (W7) + 6 phép bổ sung ở closure: mở trace reset state · mở trace gọi fetch · trace cũ sống sót · hở 16→**169px** · mobile tràn · Đặt lại gọi mạng | — |
| ZERO-AI runtime | **DONE (W7 closure)** | `runtime-zero-ai-w7.mjs` 23/23: mở/đóng trace, trace theo tham số, Đặt lại — fetch delta 0, init delta 0, state trùng khớp | — |
| Dòng thời gian gập lại khi đổi bài | **DONE (W7 closure)** | khiếm khuyết do harness runtime tìm ra: `SimulationControls` không remount nên trace mở ở bài A còn mở ở bài B | — |
| Nghiệm thu trải nghiệm trình duyệt (W6) | **PARTIAL — không đổi** | W7 chỉ chứng minh transport, không chứng minh thứ tự tầng thị giác | **W12** |

## 4e. Wave 8 — kim tự tháp test

| Owner / Feature | Trạng thái | Bằng chứng | Wave kế |
|---|---|---|---|
| Hợp đồng 4 tầng | **DONE (W8)** | `docs/TEST_TIERS.md` + `test-tiers.test.ts` khoá ngữ nghĩa nhãn | — |
| Bộ chọn T0 | **DONE (W8)** | `impact.mjs` — ba nguồn, in lý do, leo thang khi không tra ra chủ | — |
| Luật không-chọn-rỗng | **DONE (W8)** | mã sản phẩm luôn chọn ≥1 đơn vị; `IMPACT_MAPPING_MISSING` leo thang | — |
| **pytest 57s → 15,6s** | **DONE (W8)** | nguyên nhân đo được: 365ms/lần băm × mỗi lượt đăng ký; hạ vòng KDF TRONG TEST, mức production khoá bởi `test_kdf_cost.py` (marker `real_kdf_cost`) | — |
| T0 thực đo | **DONE (W8)** | renderer 3,2s · engine 3,4s · chủ sở hữu chung 4,9s · tài liệu 3,0s · hợp đồng backend 26s (leo thang đúng) | — |
| Tiêm lỗi W8 | **8/8 BỊ BẮT** | 3 guard từng KHỚP RỖNG rồi báo đạt — đúng lỗi wave này tồn tại để chống, xuất hiện trong chính guard chống nó | — |
| Live AI tách tầng | **DONE (W8)** | guard cấm `ALLOW_LIVE_AI` xuất hiện trong bộ chọn tất định | — |
| Xuất xứ bằng chứng v2 | **DONE (W8 closure)** | mô hình W0 TỰ MÂU THUẪN: artifact ghi `head=A`, commit xong HEAD thành B ⇒ STALE vĩnh viễn. Nay buộc vào `sourceFingerprint` (loại trừ `docs/`) — commit bằng chứng không đổi dấu vân tay | — |
| Năm trạng thái xuất xứ | **DONE (W8 closure)** | FRESH · STALE_SOURCE · DIRTY_SOURCE · INCOMPATIBLE_TOOL · UNKNOWN_PROVENANCE; thiếu trường KHÔNG mặc định thành FRESH | — |
| `binary.base_conversion` | **SUPPORTING_CAPABILITY** | catalog neo `T10 B4` (nhị phân, đã được `decimal_to_binary` phủ); case duy nhất tự khai NOT_ANCHORED cho cơ số 16. KHÔNG bịa mã SGK để đạt 23/23 | — |
| Gộp server trình duyệt (§21) | **OPEN** | chưa làm — W12 mới biết cần kịch bản nào | **W12** |
| Phân tầng benchmark (§24) | **OPEN** | chưa làm | **W12** |
| Gộp test trùng / property (§25–26) | **OPEN** | chưa làm | — |

## 0. KHOÁ PHẠM VI ĐỀ TÀI — ràng buộc cho mọi wave còn lại

### TÊN ĐỀ TÀI CANONICAL (chốt 2026-08-18)

> **Hệ thống mô phỏng tương tác kết hợp LLM phân tích bài toán bằng ngôn ngữ
> tự nhiên, hỗ trợ dạy học môn Tin học THPT**

Tên này **thay** mọi bản trước: bản hẹp 2026-08-16 (*"Hệ mô phỏng thuật toán …
bài toán có lời văn"*), bản có cụm *"2D/3D"*, và bản dùng động từ *"cấu hình
theo"* — cả ba đều dùng trong ngày 2026-08-18. Đều là quyết định của chủ đề tài,
không phải một lượt dọn tài liệu — đừng "khôi phục" bản cũ khi thấy chúng ở file
đông cứng.

**Hai điểm trong tên là ràng buộc, không phải văn phong.**

- *"LLM phân tích"* — **TÊN ĐỀ TÀI vẫn KHÔNG đổi thành "sinh"/"tự sinh"**
  (chốt lại 2026-08-20, xem §0-2026-08-20 bên dưới). Nhưng **lý do phải sửa**:
  lập luận cũ dựa vào tiền đề *"miền mô phỏng dựng tay"*, và tiền đề đó nay chỉ
  còn đúng **một phần** — route `generic.semantic_program` sinh chương trình
  ngữ nghĩa từ đề. Lý do còn hiệu lực, hẹp hơn: README §6 cấm tuyên bố *"sinh
  mô phỏng phổ quát"*, mà phạm vi mới **cố ý không phổ quát** (bounded IR, 2D,
  miền thuật toán rời rạc — spec 2026-08-20 §1.1). "Phân tích" giữ trong tên vì
  nó là tên bước thật trong pipeline (`analyze`) và không hứa quá.
  ⚠️ **"Sinh" KHÔNG tự phản chứng R0** dưới kiến trúc mới: LLM tổng hợp IR,
  còn thực thi · kiểm chứng · dẫn xuất trực quan thuộc thành phần tất định —
  LLM vẫn **không bao giờ** là authority của kết quả. Dùng chữ "sinh" trong
  **tên module/tài liệu kỹ thuật** là hợp lệ; chỉ **tên đề tài** giữ nguyên.
- *bỏ "2D/3D"* — có chủ đích, vì số thật là **23 target chỉ 2D · 1 có 2D+3D**
  (`network.protocol_encapsulation`) và W4B-2R đã phán 3D thua 10/10 tiêu chí ở
  hầu hết cơ chế. 3D vẫn là năng lực có thật và vẫn được kể trong thân luận văn;
  chỉ không đứng ngang hàng 2D ở tên nữa.

⚠️ **PHẠM VI KHÔNG CÒN SUY RA TỪ TÊN.** Lập luận cũ ở mục này (*"tên hẹp đúng
hơn vì bề rộng chỉ đo LƯỢNG CODE, chiều sâu mới đo kiến trúc"*) **đã bị gỡ cùng
lượt đổi tên**: nó từng được dùng để chặn wave mới, và nay không còn hiệu lực.
Việc xếp loại task quay về đúng `docs/RULES.md §3b–3d` (CORE · SUPPORTING ·
DEEP_HARDENING · OUT_OF_SCOPE), tức là xét *task đó phục vụ gì*, không xét nó có
nằm trong chữ "thuật toán"/"bài toán lời văn" hay không.

Hai thứ **vẫn còn hiệu lực** vì chúng chưa bao giờ dựa vào tên, đừng nhân lượt
mở này mà bỏ luôn:

- danh sách **KHÔNG phải mục tiêu** + tầng lớp học đóng băng ở cuối §0 (LMS ·
  IDE tuỳ ý · mô phỏng cho mọi môn · chứng minh cải thiện kết quả học tập…) —
  ý tưởng rơi vào đó vẫn thuộc `POST_THESIS_BACKLOG.md`;
- **kỷ luật tuyên bố**: mở phạm vi không sinh thêm bằng chứng. Wave mới vẫn phải
  mang bằng chứng chạy được mới được ghi DONE.

**TIÊU ĐIỂM = BA ĐIỂM NGHẼN NHẬN THỨC (chốt 2026-08-16)**

⚠️ Sau lượt đổi tên 2026-08-18, mục này là **khung KỂ CHUYỆN của quyển luận
văn**, không còn là trần phạm vi: nó quyết định chương nào được viết sâu, không
quyết định wave nào được phép mở.

Khung tổ chức của luận văn KHÔNG phải "độ phủ chương trình" mà là **điểm nghẽn
nhận thức**: chỗ trực giác học sinh hỏng, nên mới đáng bỏ công trực quan hoá.
Khung này trả lời được câu "vì sao cái này đáng mô phỏng?" — điều mà khung độ
phủ không trả lời nổi — và nó khớp gốc hình học động: KÉO để thấy bất biến,
đúng ở chỗ nghĩ thầm không ra.

⚠️ **CÁCH PHÁT BIỂU BẮT BUỘC.** Nói *"ba điểm nghẽn LỚN NHẤT"* là tuyên bố THỰC
NGHIỆM, mà kho này giữ nhãn `LEARNER_IMPACT_NOT_EVALUATED` — không có khảo sát
trên người học. Phát biểu đúng: *"ba điểm nghẽn được CHỌN theo yêu cầu cần đạt
của chương trình GDPT 2018 và các khó khăn đã ghi nhận trong tài liệu về người
mới học lập trình"*. Chọn có căn cứ, không tự phong.

| # | Điểm nghẽn | Vì sao trực giác hỏng | Target (13) |
|---|---|---|---|
| 1 | **Trạng thái tích luỹ qua vòng lặp** | không giữ nổi "max đến giờ" / "tổng đến giờ" trong đầu khi duyệt, và không thấy nó đổi lúc nào | `find_max` `find_min` `sum_if` `count_if` `linear_search` `scan` `bounded_control_flow` |
| 2 | **Bất biến & tiền điều kiện** | không hiểu vì sao tìm nhị phân ĐÒI dãy đã sắp; không thấy thuật toán KHÔNG nhìn lại vùng đã duyệt | `binary_search` `bubble_sort` `insertion_sort` `selection_sort` |
| 3 | **Thứ tự duyệt quyết định kết quả** | cùng một cây/đồ thị, đổi kiểu duyệt ra dãy khác — thứ tự LÀ định nghĩa | `tree.traversal` `network.graph_traversal` |

Bộ ba này KHÔNG được gán cho vừa: mỗi nghẽn ứng đúng một tương tác ĐÃ CÓ trong
`interaction-policy.ts` — đổi ngưỡng/điều kiện (1) · kéo cột vào vùng đã duyệt,
phá thứ tự đã sắp (2) · đổi kiểu duyệt (3). Nó mô tả thứ hệ ĐÃ LÀM ĐƯỢC, không
phải thứ hứa sẽ làm.

**TẦNG HAI — 11 target, GIỮ TRONG HỆ, CẮT KHỎI TIÊU ĐIỂM**

`decimal_to_binary` `base_conversion` `character_encoding` `color.rgb_model` ·
`and_gate` `boolean_dag` `generic.rule_scene` · `protocol_encapsulation` ·
`relational_table_query` · `web.style_model` · `network.packet_routing`

⚠️ **CẮT KHỎI TIÊU ĐIỂM ≠ XOÁ KHỎI HỆ.** Không demo, không chương, không đo —
một bảng phụ lục nửa trang là đủ. Nhưng KHÔNG xoá code, vì xoá là mất đúng ba
thứ đang đứng vững: (a) bằng chứng mở rộng — luận cứ kiến trúc mạnh nhất, số đo
W5A: thêm miền tốn một `SimSpec` + một dòng đăng ký, 0 dòng pipeline; (b) ranh
giới TỪ CHỐI — `generic.rule_scene` chính là chỗ chứng minh đúng-hoặc-
`capability_gap`, xoá nó thì Phase M không còn đối tượng; (c) 24 target đang bị
khoá bởi test đếm, migration và artifact chứng nhận, nên xoá là một wave gỡ rối
mà KHÔNG thêm một chữ nào cho quyển luận văn.
Loãng đề tài là do KỂ CHUYỆN dàn trải, không phải do code tồn tại.

`network.packet_routing` xuống tầng hai vì định tuyến không nằm gọn trong ba
nghẽn trên; nhét vào nghẽn 3 là làm hỏng sự sạch của bộ ba để lấy một con số.

**TIÊU ĐỀ XUỐNG 2 DÒNG — ĐO XONG, GIẢ THUYẾT HIỂN NHIÊN ĐÃ BỊ LOẠI**

Đo trên app thật, 24 target × 4 bề rộng (probe CDP qua `audit-composition.mjs`):
**7 target xuống 2 dòng ở CẢ ba bề rộng desktop** — `bubble_sort`,
`insertion_sort`, `scan`, `character_encoding`, `boolean_dag`,
`graph_traversal`, `protocol_encapsulation`. KHÔNG phải bệnh riêng của một bài.

Số liệu quyết định:

    title 706/706   max-width 938.7px   header 706

⚠️ **`max-width: 68ch` KHÔNG PHẢI thủ phạm** — 938px luôn RỘNG HƠN header (≤722),
nên nó chưa bao giờ bó tiêu đề. Sửa nó là sửa vào chỗ không có bệnh.

Ràng buộc thật là **BỀ RỘNG THẺ**: tiêu đề đã dùng trọn header (706/706) mà vẫn
cần ~740px. Thiếu chưa tới 40px.

**Ngã ba phải quyết trước khi sửa** (không tự chọn được vì hai luật chọi nhau):

- Cho thẻ rộng ra đủ chứa tiêu đề ⇒ đụng Phase A ("chữ KHÔNG được quyết bề rộng
  khung"). Nhưng lưu ý: brief mới chỉ cấm chữ đổi **HÌNH HỌC SÂN KHẤU**, mà nới
  thẻ thì sân khấu giữ nguyên kích thước — nên hai luật CÓ THỂ cùng đúng nếu
  tách "bề rộng thẻ" khỏi "bề rộng sân khấu".
- Hoặc giảm cỡ chữ tiêu đề (24px) ⇒ đổi thang chữ toàn sản phẩm.
- Hoặc chấp nhận 2 dòng cho tiêu đề dài thật (brief cho phép).

⚠️ KHÔNG dùng `white-space: nowrap` — brief cấm, và nó đẻ tràn ở 768px.

Bản vá phải đo lại CẢ 7 target × 4 bề rộng + chụp ảnh đối chứng bằng
`capture-phase-evidence.mjs`.

**BỐ CỤC — GUARD M19 ĐANG ĐO SAI ĐẠI LƯỢNG (đo được 2026-08-16)**

`audit-composition.mjs` chạy trên app thật, 24 target × 4 bề rộng: **96/96 OK**.
Nhưng đọc cột số thì thấy nó xanh vì đo nhầm thứ:

| ở 1920px | |
|---|---|
| chỗ khả dụng (`stage`) | 1672px |
| bề rộng thẻ (`khung`) | 512–719px |
| mực lấp trong thẻ | 99,6% |

Guard đo **mực / khung** (M19 sinh ra để sửa "thẻ 1624px cứng mà mực 276px"), nên
nó không hề đo **khung / chỗ khả dụng**. Thẻ dùng ~31% bề ngang mà vẫn OK.
Triệu chứng người dùng — cột bé tí, thừa mênh mông hai bên — nằm NGOÀI tầm đo.

⚠️ Đây là lý do bốn commit bố cục đã phải lùi ở `df55c0c`: tôi sửa theo mắt vì
guard không nói gì, rồi `.workspace-card: width 100%` làm SVG mạch logic co về 0
(`.dag-stage` là `width: fit-content`, còn `dag-module.tsx:429` đã cảnh báo sẵn
lớp lỗi này).

**Việc phải làm, theo thứ tự:**
1. Thêm cột **khung/stage** vào `audit-composition.mjs` + ngưỡng khai tường minh
   (target nào được phép hẹp, vì sao). Không có phép đo thì mọi bản vá sau đều
   là mò.
2. Chỉ khi có cột đó mới sửa bề rộng thẻ — và phải xem cả `logic.boolean_dag`
   trong cùng lượt đo, vì nó là target vỡ trước tiên.

Artifact: `docs/evaluation/m19/composition.json` (lượt đo này).

**VIỆC CÒN LẠI ĐỂ TIÊU ĐIỂM THÀNH THẬT (W5P — chưa làm)**

Quyết định ba tầng hiện MỚI NẰM Ở TÀI LIỆU. Thư viện vẫn bày đủ 11 target tầng
hai cho học sinh, nên sản phẩm vẫn loãng đúng như trước khi chốt. Cách làm đã
thử và ĐÃ BIẾT chính xác cần gì:

Khai MỘT danh sách `FOCUS_SIM_IDS` (13 target) ở `data/offline-catalog.ts`, rồi
`publicCatalog()` lọc theo `visibility === "public" && FOCUS_SIM_IDS.includes(...)`.
KHÔNG rải 13 cờ `visibility` khắp `sim-samples.ts`: tiering là quyết định SẢN
PHẨM đổi theo phạm vi đề tài, rải thành cờ thì mỗi lần đổi phải sửa mười mấy chỗ
và không ai đọc ra ý định.

Bốn guard sẽ đỏ, và cả bốn đều mã hoá GIẢ ĐỊNH CŨ (mọi target đăng ký đều bày ở
Thư viện) — phải migrate chứ không vá:

1. `catalog.test.tsx::starterEntries` — `STARTER_SIM_IDS` đang chứa ba target
   tầng hai (`binary.decimal_to_binary`, `network.packet_routing`,
   `logic.and_gate`); thay bằng target tiêu điểm.
2. `capability-descriptors.test.ts::library_discoverable ⟹ có mẫu công khai` —
   BACKEND còn khai `ReachabilityLevel.LIBRARY_DISCOVERABLE` cho 11 target tầng
   hai. Phải bỏ mức đó trong `catalog.py` rồi chạy
   `scripts/generate_capability_descriptors.py`. GIỮ `AI_REACHABLE_PUBLIC`:
   học sinh gõ đề màu RGB thì hệ vẫn phải dựng được — từ chối lúc ấy mới là sai.
3. `ux-shell.test.tsx` ×3 — đếm thẻ Trang chủ/Thư viện.
4. `interaction-semantics.test.ts` — quét qua danh mục công khai.

⚠️ Đây là một cuộc DI TRÚ, không phải một dòng sửa: nó chạm backend catalog +
artifact sinh lại + 4 file test. Làm trọn một lượt, đừng bỏ dở.

**NGOÀI PHẠM VI:** LMS · IDE tự do · sinh hình không ràng buộc · chứng minh cải
thiện kết quả học tập → `POST_THESIS_BACKLOG.md`.


**Lõi đề tài**: yêu cầu học bằng ngôn ngữ tự nhiên → LLM đề xuất *spec ứng viên
có ràng buộc* → validate năng lực/phạm vi tất định → engine tất định → biểu diễn
2D/3D tương tác khi có vai trò sư phạm → học sinh thao tác/quan sát cơ chế →
trace/giải thích/thử thách tuỳ chọn → bối cảnh lớp học nhẹ.

**KHÔNG phải mục tiêu** (nếu một ý tưởng rơi vào đây, nó thuộc
`POST_THESIS_BACKLOG`, không phải wave mới): LMS đầy đủ · quản lý trường học ·
điểm danh · học phí · sổ điểm · thời khoá biểu · diễn đàn · nền tảng soạn khoá
học · IDE HTML/CSS/JS tuỳ ý · IDE lập trình tuỳ ý · hệ mô phỏng cho mọi môn ·
sinh hình tuỳ ý không ràng buộc · thay thế giáo viên · chứng minh cải thiện kết
quả học tập khi chưa có nghiên cứu trên người học.

**Tầng lớp học ĐÓNG BĂNG ở mức**: đăng nhập · lớp · giao mô phỏng đã hỗ trợ ·
học sinh luyện tập · giáo viên quan sát trạng thái có cấu trúc.

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
`docs/superpowers/specs/2026-08-20-semantic-program-generative-route-design.md`
(APPROVED DESIGN, `0c53882`). Kế hoạch thực thi: `docs/superpowers/plans/2026-08-20-semantic-program-generative-route.md`.

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

## 4f. Wave 10 — guard ngữ nghĩa chuyển động

| Owner / Feature | Trạng thái | Bằng chứng | Wave kế |
|---|---|---|---|
| Phân biệt hình học SVG ↔ bố cục HTML | **DONE (W10)** | `transition-semantics.test.ts` — đọc NGỮ CẢNH PHẦN TỬ, không cấm theo tên thuộc tính | — |
| `ArrayView` giữ chuyển động dạy học | **DONE (W10)** | cột `<rect>` chạy `y`/`height` vì chúng encode giá trị mảng | — |
| Hạng mục THỨ BA do guard tìm ra | **ĐÃ KHAI (W10)** | `.web-page` chạy `padding` — thuộc tính bố cục HTML nhưng CHÍNH LÀ state mô phỏng đang dạy; cấm nó là cấm bài học | — |
| Tiêm lỗi W10 | **5/5 BỊ BẮT** | HTML chạy height · HTML chạy margin · inline `<div>` chạy width · ngoại lệ wildcard · gỡ hình học SVG | — |

## 4g. Wave 12 — chứng nhận trình duyệt (ĐANG DỞ)

| Owner / Feature | Trạng thái | Bằng chứng | Wave kế |
|---|---|---|---|
| Runner dùng chung một server | **DONE (W12)** | `browser-runner.mjs` — 23 kịch bản, `serverStarts: 1`; cách ly bằng `store.reset()` + xoá lưu trữ, không khởi động lại tiến trình | — |
| Chứng nhận tương tác 23 target | **14/23 CERTIFIED** | `certify-w12.mjs` → `w12-interaction.json`, mang `sourceFingerprint`. Luật: hành động → SimAction → apply → state tất định đổi → hệ quả DOM | **W12 tiếp** |
| 9 target còn lại | **PROBE_UNVERIFIED** | **KHÔNG phải khiếm khuyết sản phẩm.** Probe chưa dùng đúng từ vựng action của miền (`logic` chỉ nhận `toggle`, `network` nhận `net_*`, `tree`/`database` chưa đọc hợp đồng). Phải đọc hợp đồng rồi chạy lại trước khi kết luận bất cứ điều gì | **W12 tiếp** |
| Mùi quiz — `packet_routing` | **ĐÃ SỬA (W12-A)** | đo được 111px/180px = **0,62** (thử thách gần bằng ⅔ cơ chế). Sửa ở CHỦ SỞ HỮU CHUNG `.predict-bar` (dải ngang biết xuống dòng), không vá riêng network → **0,34**, 2 hàng → 1 hàng | — |
| Guard W6 đo sai tầng | **ĐÃ SỬA (W12-A)** | W6 chỉ soi `.result-banner` có `fit-content`; băng gọn thật nhưng HỘP CHỨA nó thì không. Guard mới đo cả khối | — |
| Ma trận 23×4 bề rộng | **39/92** | 0 tràn · 0 cắt · thử thách đóng sẵn ở mọi dòng. 52 dòng hỏng là họ `algorithm` + `graph_traversal`/`packet_routing`: affordance kéo bị HOÃN theo luật cam kết (`interaction-policy.ts` §15) ở bước mặc định · 1 dòng `web.style_model` @768 sân khấu chồng khay | **W12 tiếp** |
| Nguyên nhân "quiz-first" đã truy được | **XÁC ĐỊNH (W12-C)** | `whatIfDragAllowed` cố ý hoãn kéo khi còn cam kết chờ. Hành vi được thiết kế, nhưng hệ quả: ở bước mặc định thứ duy nhất nhìn thấy được là ô dự đoán — đúng điều quan sát từ màn hình thật | **cần quyết định sản phẩm** |
| `commit_decision` | **POST_THESIS_BACKLOG** | `docs/POST_THESIS_BACKLOG.md` — mở rộng đáng làm, không cần cho chứng nhận trung thực kiến trúc hiện có | — |
| Chứng nhận tương tác trình duyệt | **23/23** | 20 CERTIFIED qua thao tác THẬT (action đọc từ config + hợp đồng miền) + 3 TRACE_MODEL đã xác nhận (`apply` đồng nhất). `PROBE_LIMITED` = **0** | W12-C tiếp |
| Ngữ nghĩa tương tác 23 target | **11 / 9 / 3** | `INTERACTIVE_MODEL` 11 (đụng ĐỐI TƯỢNG HỌC) · `BOUNDED_PARAMETER_TOOL` 9 (họ algorithm — chỉ đổi ĐẦU VÀO) · `TRACE_MODEL` 3 | — |
| Năm lần probe sai từ vựng | **ĐÃ GIẢI** | logic dùng `N/G/K` không phải `A`; mạng dùng trường `a`/`b` không phải `from`/`to`, id `client`/`router`; tree dùng `variant` không phải `order`; generic dùng `a`/`b` không phải `0`; database dùng `filter.column` không phải `threshold`. Mọi giá trị nay ĐỌC từ config mẫu + hợp đồng miền | — |
| Bảng "6/9/3/5" cũ | **ĐÃ THAY** | 5 `PROBE_LIMITED` đã giải bằng id thật, 4 trong đó hoá ra là INTERACTIVE_MODEL | — | `INTERACTIVE_MODEL` 6 (đụng ĐỐI TƯỢNG HỌC) · `BOUNDED_PARAMETER_TOOL` 9 (chỉ đổi ĐẦU VÀO) · `TRACE_MODEL` 3 · `PROBE_LIMITED` 5. Con số giảm so với lượt trước và đó là kết quả TRUNG THỰC HƠN | **W12 tiếp** |
| Cả họ `algorithm` chưa có đường cam kết cơ chế | **KHIẾM KHUYẾT ĐÃ XÁC ĐỊNH** | quyết định "promote/keep max" chỉ sống trong `predict` (thử thách); `module.apply` KHÔNG có action nào cho nó. Nên 9 target thuật toán là công cụ tham số + trace, chưa phải mô phỏng tương tác theo nghĩa cơ chế | **W12-B0.5 tiếp** |
| Ngữ nghĩa tương tác (bảng 15/3/5 cũ) | **ĐÃ HUỶ** | nó tính `whatif_swap` là thao tác mô hình, trong khi sắp xếp lại dãy là đổi ĐỀ BÀI chứ không phải tham gia phép quét | — | `INTERACTIVE_MODEL` 15 · `TRACE_MODEL` 3 (xác nhận `apply` đồng nhất) · `PROBE_LIMITED` 5 (chưa kết luận). Câu hỏi cổng: "đóng thử thách rồi, học sinh thao tác lên cái gì?" | **W12 tiếp** |
| `find_max` — ca tham chiếu | **ĐÃ LÀM RÕ (W12-B0)** | hai nút "Đặt 9 làm max mới"/"Giữ max = 7.5" là THỬ THÁCH (nuôi `predict.check`). Thao tác mô hình thật là kéo cột `ArrayView` → `whatif_swap` → nhánh what-if, còn nguyên khi đóng thử thách | — |
| Con số "14 CERTIFIED" cũ | **ĐÃ HUỶ** | nó chưa phân biệt thao tác mô hình với trả lời dự đoán | — |
| Quét mùi quiz 23 target | **PARTIAL** | 2/23 chạm được bề mặt thử thách sau khi tiến bước; 21 target còn lại CHƯA kết luận được — không đọc thành "không có thử thách" | **W12 tiếp** |
## W12 — BỐN CHIỀU CÒN LẠI ĐÃ ĐÓNG (2026-08-16)

| chiều | trạng thái | bằng chứng |
|---|---|---|
| Khả năng tiếp cận trình duyệt | **DONE** | `w12-a11y.json` — 6/6 bề mặt, phím THẬT qua CDP; Escape đóng thử thách + trả tiêu điểm về nút mở; 4/4 tiêm lỗi đỏ đúng chỗ |
| Tiếp nối lớp học | **DONE** | `w12-classroom-continuation.json` — đăng nhập → luyện → ĐĂNG XUẤT + xoá sạch lưu trữ → quay lại → tiến độ về từ MÁY CHỦ; 2/2 tiêm lỗi |
| Kịch bản dạy học | **DONE** | `w12-teaching-walkthrough.json` — 11/11 dùng được KHI thử thách đóng |
| Biểu diễn công khai + parity 2D↔3D | **DONE** | `w12-representation.json` — 23 target, **0** bày công tắc cho học sinh, 0 vi phạm; `protocol_encapsulation` parity 2D↔3D đạt trên trình duyệt |

**Lỗi sản phẩm THẬT tìm ra và đã sửa** (không phải lỗi phép đo):

1. **Affordance cơ chế nằm ngoài bàn phím.** `logic.and_gate` có 13 phần tử
   focus được trên màn, KHÔNG cái nào là công tắc A/B. Cùng họ ở
   `binary.decimal_to_binary` và `generic.rule_scene`. Idiom "một `<g>` có
   `cursor:pointer` + `onClick`" được dựng ở năm chỗ, làm ĐÚNG ở hai. Gom về
   `simulations/svg-affordance.ts`.
2. **Không có vòng tiêu điểm** cho chính những affordance vừa nối bàn phím —
   vào được cơ chế mà không thấy mình đang ở đâu. Thêm `.sim-affordance:focus-visible`.
3. **Công tắc 2D/3D bày cho học sinh mà không có luật.**
   `protocol_encapsulation` khai `primary: "2d"` nhưng `alternate:
   ALTERNATE_FOR_EXPLANATION`, trong khi chính lời khai lý do lại mô tả 2D là
   "biểu diễn nội bộ" — một cấu hình không mô tả sản phẩm nào. Nay 3D là bản
   NỘI BỘ, học sinh không bị hỏi chọn cách xem.

**PACKET_ROUTING_3D_DEFERRED.** Lý do kỹ thuật, không phải thẩm mỹ: renderer 3D
DUY NHẤT trong kho là `encap-ui3d.tsx`, dựng cho trục Z = tầng giao thức. Định
tuyến cần Z = TUYẾN THAY THẾ — một ngữ nghĩa khác, tức renderer mới chứ không
phải một lời khai. Và 2D hiện tại đã chứng nhận đủ chuỗi tương tác có thẩm
quyền (`net_disconnect` → `module.apply` → tính lại tuyến → hệ quả nhìn thấy),
có đường bàn phím, dùng được ở cả bốn bề rộng. Bày 3D trang trí mà không có
tương tác có thẩm quyền là đúng thứ `PUBLIC_3D_INTERACTION_FAIL` cấm.

**PRIMARY_CAPABILITY_PARITY_CERTIFICATION = NOT_CURRENTLY_EVIDENCED.** Hai con
số `10/23` và `13/23` từng được mang theo qua nhiều báo cáo. Grep toàn kho:
không mã, không test, không artifact nào sinh ra chúng — chúng sống sót vì lượt
trước đã nói ra chúng. Cổng parity CÓ THẬT là `generation-parity.test.ts`, và nó
chứng minh một trục KHÁC: **nguồn spec (mẫu vs AI) không chọn đường đi**, 22
target × 4 nguồn pipeline. Artifact nay có provenance + danh tính target. Không
dựng lại 23 fixture chỉ để cứu một thống kê — mục tiêu là toàn vẹn bằng chứng.
Khoá bởi `certification-sweep.test.ts`.

## W12 — ĐÃ GIẢI: MỘT LƯỢT, MỘT DẤU VÂN TAY (2026-08-16, `80c7c05`)

> Mục ngay dưới (`9609cc6`) là **chẩn đoán**, giữ lại để đọc *vì sao*. Trạng
> thái hiện hành là mục này.

**`FINAL_SOURCE_HEAD = 80c7c05` · `FINAL_SOURCE_FINGERPRINT = de3007604b68ca47`**

| | |
|---|---|
| artifact W12 FRESH | **9/9** (8 cổng con + chính bản ghi lượt) |
| `UNIQUE_CERTIFICATION_SOURCE_FINGERPRINT_COUNT` | **1** |
| STALE_SOURCE · DIRTY_SOURCE · UNKNOWN_PROVENANCE | **0 · 0 · 0** |
| phán quyết lượt | `CERTIFICATION_SWEEP_VALID` — HEAD và vân tay y nguyên hai đầu, `DIRTY_AFTER` rỗng |

Bằng chứng: `docs/evaluation/m20/w12-sweep.json`. Công cụ:
`frontend/scripts/certify-sweep-w12.mjs`, khoá bởi `src/certification-sweep.test.ts`.

**Cái đã đổi về CHẤT.** Hệ quả vận hành ở mục dưới trước đây là *lời nhắc* — và
nó bị bỏ qua đúng như mọi lời nhắc khác trong kho này. Nay nó là **cổng**: một
lượt chứng nhận chụp `HEAD` + vân tay + cây bẩn ở hai đầu, và mọi vi phạm có mã
lý do riêng (`SOURCE_DIRTY_AT_SWEEP_START` · `SOURCE_DIRTY_AT_SWEEP_END` ·
`HEAD_MOVED_DURING_SWEEP` · `SOURCE_FINGERPRINT_CHANGED_DURING_SWEEP`). Nhắc thì
trôi, đỏ thì không.

**Hai lỗi đường ống bắt được trong lúc làm, cả hai đều là cổng tự miễn trừ:**

1. `w12-interaction-semantics.json` là **đầu vào** của `certify-viewports-w12.mjs`
   nhưng chỉ có `generatedAt` ⇒ `UNKNOWN_PROVENANCE` vĩnh viễn. Một mắt xích của
   bộ bằng chứng nằm ngoài mọi cổng.
2. `w12-sweep.json` — artifact *chứng minh* kỷ luật xuất xứ — cũng
   `UNKNOWN_PROVENANCE` ở lượt cuối đầu tiên. Guard mới đã **đỏ thật** trên chính
   bản ghi hỏng ấy trước khi nó bị bỏ đi.

**Kết quả sản phẩm không đổi khi đo lại trên nguồn sạch** — 20 TOOL_PASS ·
3 TRACE_PASS · 23/23 sức nặng thị giác · 92/92 viewport · 20/20 cuộn ·
23/23 tương tác · 0 FAIL mùi quiz · 3/3 tiêm lỗi. Tức các con số lịch sử vốn
đúng; thứ thiếu đúng là **chứng minh chúng thuộc về nguồn hiện tại**, và nay có.

## W12 — XUẤT XỨ BẰNG CHỨNG: KHÔNG ARTIFACT NÀO FRESH (2026-08-15, `9609cc6`)

Đo bằng chính hợp đồng provenance (`sourceFingerprint` hiện tại `551c75b4…`):

| artifact | trạng thái |
|---|---|
| `w12-experience-audit.json` · `w12-visual-weight-faults.json` | **STALE_SOURCE** |
| `w12-interaction.json` · `w12-quiz-dominance.json` · `w12-scroll-shell.json` · `w12-viewport-matrix.json` · `w12-visual-weight.json` | **DIRTY_SOURCE** — đo trên mã chưa commit |
| `w12-interaction-semantics.json` | **UNKNOWN_PROVENANCE** — sinh trước hợp đồng v2 |

**Luật `chỉ FRESH mới đỡ được COMPLETE` ⇒ hiện KHÔNG chiều trình duyệt nào
được phép khai COMPLETE**, kể cả những chiều có con số đẹp (23/23 sức nặng thị
giác, 92/92 viewport, 20/20 cuộn). Con số vẫn đúng với lúc đo; cái thiếu là
**chứng minh chúng đúng với nguồn HIỆN TẠI**.

### Nguyên nhân, và nó mang tính cấu trúc

`sourceFingerprint` phủ `frontend/scripts` — nên **commit chính script vừa sinh
artifact sẽ làm artifact ấy STALE ngay lập tức**. Cùng họ với lỗi tự-tham-chiếu
đã sửa một lần ở W8 (`assertFresh` đòi `head === gitHead()`, khiến artifact vừa
commit vĩnh viễn cũ). Lần ấy sửa bằng cách loại `docs/` khỏi vân tay; lần này
lộ ra vế còn lại.

### Hệ quả vận hành — thứ tự BẮT BUỘC

1. Đóng băng nguồn (`src/` + `scripts/`), commit hết.
2. **Rồi mới** chạy lại toàn bộ script chứng nhận trong MỘT lượt.
3. Commit **chỉ artifact** — `docs/` không nằm trong vân tay nên bước này
   không tự huỷ kết quả.

Chạy chứng nhận trước khi source đóng băng là **lãng phí**: mọi artifact sinh ra
đều DIRTY, và một bản chứng nhận DIRTY không đỡ được bất kỳ tuyên bố nào.

## W12 — trạng thái theo TỪNG CHIỀU (2026-08-15, `28a0c20`)

**`ALGOSIM_WAVE12_BROWSER_CERTIFICATION_PARTIAL`.**

### COMPLETE / ĐÓNG BĂNG — không soát lại trừ khi có hồi quy

| chiều | bằng chứng |
|---|---|
| hợp đồng sinh đặc tả | `test_web_contract_sync.py` · `CACHE_VERSION` 30 ba chủ sở hữu |
| hành vi sinh, **6/6 họ** | `test_web_generated_behavior.py` · `..._families.py` · `..._db_network.py` |
| soát hợp đồng cả catalog | `test_catalog_contract_audit.py` (23/23 dẫn từ `CATALOG`) |
| preflight PDF + soát OCR | 5/5 IMAGE_ONLY · 804 trang · 15/15 mẫu → 0 ký tự · không công cụ OCR nào |

### BLOCKED_EXTERNAL_EVIDENCE — **nhánh đóng băng, KHÔNG chặn phần còn lại**

```
CURRICULUM_SOURCE_PRESENT  = YES (5/5)
CURRICULUM_SOURCE_FORMAT   = IMAGE_ONLY
CURRICULUM_TARGETED_OCR    = UNAVAILABLE
CURRICULUM_BLOCKER         = CURRICULUM_EXTRACTION_REQUIRES_EXTERNAL_EVIDENCE
```

Thiếu cụ thể: mục lục 5 quyển + các trang bài để neo 24 mục công khai.
**Không** chạm engine tất định, hành vi trình duyệt, hay hợp đồng sinh.

### PARTIAL — việc độc lập còn lại, theo thứ tự thi hành

1. parity mẫu↔AI ở mức trường lõi (23 target)
2. phân loại trải nghiệm cuối + teaching-tool audit cả catalog
3. chứng nhận tương tác trình duyệt thật (INTERACTIVE_MODEL) + discoverability
4. chứng nhận BOUNDED_PARAMETER_TOOL + TRACE_MODEL
5. soát animation-only + quiz-first
6. chính sách biểu diễn công khai · `packet_routing` · `protocol_encapsulation`
7. parity 2D↔3D nội bộ
8. thao tác trực tiếp HTML/CSS · tiếp cận · tiếp nối lớp học
9. ma trận viewport tươi · hồi quy cuộn · walkthrough dạy học
10. ma trận lỗi cuối · provenance · T3 kỹ thuật

Hạ tầng đã đủ: `browser-runner.mjs` · `certify-{viewports,experience,visual-weight,scroll}-w12.mjs`
· `canonical_config.py` · mẫu FAULT/CONTROL ở `test_web_contract_sync.py`.

### Giữ nguyên

`CURRICULUM_SUPPORT_PARTIAL` · `LEARNER_IMPACT_NOT_EVALUATED` ·
`WAVE4_INTERACTION_CERTIFICATION = NO_EVIDENCE` · `WAVE6_BROWSER_EXPERIENCE = PARTIAL`

### Rủi ro kỹ thuật đã ghi nhận (không phải khiếm khuyết tất định)

`GENERATION_CONTRACT_RESIDUAL_ENGINEERING_RISK` — schema thuật toán dùng chung
không diễn đạt được `required` theo từng target. Validator vẫn fail-closed nên
runtime an toàn; giá phải trả là một lượt sinh hỏng, không phải mô phỏng sai.

## W12 — trạng thái đóng (2026-08-14, `1647af3`)

**Verdict: `ALGOSIM_WAVE12_BROWSER_CERTIFICATION_PARTIAL`.**

Blocker **đúng hai mục**, chi tiết thi hành ở `docs/W12_REMAINING.md`:

1. `network.packet_routing` chưa có renderer 3D — cần dựng cảnh + đường chọn
   liên kết phát `net_disconnect` + đường bàn phím tương đương.
2. Benchmark theo đơn vị chương trình — chặn bởi **thiếu danh sách mã SGK có
   thẩm quyền**, không phải bởi code. KHÔNG tự chế mã (`COVERAGE.md §15`).

Đã đóng: cuộn 20/20 · viewport 92/92 · ngữ nghĩa 11/9/3 · trải nghiệm 19 TOOL /
4 TRACE / 0 FAIL · **sức nặng thị giác 23/23** · bề mặt công cụ CSS dẫn từ đặc
tả · `protocol_encapsulation` 3D công khai · rò rỉ liên môn 0.

Giữ nguyên: `CURRICULUM_SUPPORT_PARTIAL` · `LEARNER_IMPACT_NOT_EVALUATED` ·
`WAVE4_INTERACTION_CERTIFICATION = NO_EVIDENCE` ·
`WAVE6_BROWSER_EXPERIENCE = PARTIAL`.

## W12 §A — quyền sở hữu cuộn của vỏ ứng dụng (2026-08-14)

**Triệu chứng người dùng chụp được.** Thanh cuộn gần như tàng hình · một khe dọc
xấu cạnh header · mép trang và mép header không đọc thành một vỏ liền.

**Không đảo quyết định cũ.** Mẫu "vỏ cố định + main tự cuộn" mà brief §3 nêu
nghe đúng, nhưng **W4B-1A đã đo và cố ý đi hướng ngược**: vùng cuộn nội bộ giấu
170px nội dung học ở 1920×768 mà `page_scrollable_y` vẫn `false` — học sinh
không có tín hiệu nào ở mức trang. Chủ sở hữu cuộn đúng vẫn là TÀI LIỆU, và §3
cho phép giữ nếu đã có chủ sở hữu đúng.

**Nguyên nhân thật, đo bằng chuỗi bố cục.**

```
innerW 1902 · html clientWidth 1902 · body 1892 ← hụt đúng 10px
```

`html { scrollbar-gutter: stable }` giữ 10px ở content box của html, nên body —
và header bên trong nó — hẹp hơn 10px. Dải ấy lộ nền `--canvas-soft` cạnh header
`--canvas`, chạy suốt chiều cao tài liệu.

Nó đọc ra là KHE HỞ chứ không phải máng cuộn vì `scrollbar-color: transparent
transparent` + thumb webkit `background: transparent`: **mặc định không thấy
gì**. "Mảnh, chìm" đã trượt thành "vô hình" — đúng thứ W12 §4 cấm.

**Sửa.** Ba mức đậm dần qua token (`--scroll-thumb` · `-strong` · `-hover`),
có mặt sẵn ở mức mờ. Giữ nguyên `scrollbar-gutter: stable` — bỏ nó đi để "hết
khe hở" là đổi một lỗi thị giác lấy lỗi nhảy ngang mà §5 cấm.

**Một lỗi TIÊU CHÍ của chính phép đo.** Bản đầu so header với
`de.clientWidth` (padding-box, không phản ánh việc giữ chỗ) nên báo HỎNG 20/20 —
tức đòi header phủ luôn cả máng cuộn, điều không trang cuộn-tài-liệu nào làm
được. Đo lại bằng body: header **trải hết vỏ** ở mọi dòng.

**Kết quả:** `certify-scroll-w12.mjs` — **20/20** (5 màn × 4 bề rộng), máng
đúng 10px và **giống nhau giữa trang ngắn (985px, không cuộn) và trang dài
(2045px, cuộn)** ⇒ không nhảy ngang; 0 tràn ngang.

⚠️ Thumb có thấy được không thì trình duyệt không trả lời được (CDP không đọc
computed style của pseudo-element). Khoá ở `styles/scrollbar-ownership.test.ts`,
kèm đối chứng dương dựng lại đúng bản CSS cũ.

## W12 §6 — Policy B: công cụ hiện ra khi thử thách ĐÓNG (2026-08-14)

**Quan sát khởi nguồn (của người dùng).** `algorithm.find_max` đọc ra: nhìn hình
→ đọc câu hỏi → bấm một trong hai nút. Tức một bài kiểm tra, không phải công cụ.

**Đo trước khi sửa.** `certify-viewports-w12.mjs` (23 target × 4 bề rộng, HEAD
`99548af`): **39/92** dòng ĐẠT.

**Nguyên nhân — một luật bị chép tay ba lần.** Ba nơi cùng đòi `exploreOpen`
trước khi dựng công cụ, mà trang vừa mở thì cờ đó `false`:

| nơi | công cụ bị giấu |
|---|---|
| `domains/algorithm/ui.tsx` | kéo cột (`whatif_swap`) |
| `domains/network/ui.tsx` | vùng bấm ngắt/nối liên kết |
| `domains/algorithm/ui.tsx` — `ConditionBar` | ngưỡng + phép so sánh (`set_param`) |

Lý do gốc của cổng là "đừng cho né cam kết", nhưng cam kết chỉ tồn tại KHI THỬ
THÁCH ĐANG MỞ. Nay cả ba đi qua **`simulations/tool-affordance.ts`**.

**Một bug thứ hai, chỉ trình duyệt mới thấy.** Trong `traverse-module.tsx`, dòng
JSX gọi `TraverseParamBar` nằm SAU câu `return` của một `useEffect`: cú pháp hợp
lệ, tên không "unused", TypeScript im — nên control BFS↔DFS **không bao giờ được
render**. `network.graph_traversal` là công cụ tham số mà học sinh không có cách
nào đổi tham số. Không unit test nào bắt được vì không test nào hỏi "control có
trên màn hình không".

**Ba lỗi TIÊU CHÍ của chính phép đo, sửa luôn** — mỗi cái đều xác minh bằng dò
tận nơi, không suy đoán:

1. `getBoundingClientRect` trên `<line>` ngang trả `150×0` (Chrome không cộng
   stroke) ⇒ ba vùng bấm liên kết bấm được của `packet_routing` bị vứt đi.
2. Đòi affordance ở target **TRACE_MODEL** (`apply` đồng nhất) — 0 affordance ở
   đó là ĐÚNG. Danh sách nay ĐỌC TỪ bảng phân loại, vì bản viết tay của tôi sai
   ngay lần đầu (ghi nhầm `tree.traversal`).
3. Khay điều khiển `position: sticky` nổi trên nội dung dài bị đọc là "chồng
   lấn" — đó chính là việc của neo (quyết định W7).

**Sau khi sửa: 92/92.** Diễn tiến đo được: 39 → 67 (Policy B ở miền thuật toán)
→ 75 (miền mạng + thanh điều kiện) → 87 → 91 → 92 (ba lỗi tiêu chí).

**KHÔNG nâng hạng target nào** (W12 §8): `whatif_swap` vẫn là INPUT_MANIPULATION.
Bảng ngữ nghĩa giữ nguyên **11 INTERACTIVE_MODEL · 9 BOUNDED_PARAMETER_TOOL ·
3 TRACE_MODEL · PROBE_LIMITED = 0**.

| `WAVE4_INTERACTION_CERTIFICATION` | **NO_EVIDENCE — không đổi** | chỉ nâng khi đủ 23/23 có bằng chứng tươi | **W12** |
| `WAVE6_BROWSER_EXPERIENCE` | **PARTIAL — không đổi** | chín màn trải nghiệm chưa chạy | **W12** |

## 4h. vNext — route sinh ngữ nghĩa NỐI VÀO SẢN PHẨM (2026-08-23)

Bằng chứng: `docs/evaluation/semantic-vnext/` (`SERVE_PROBE_CHAIN.md` ·
`STACK_VISUAL_ACCEPTANCE.md` · `e2e-serve-daoday/`).

| Owner / Feature | Trạng thái | Bằng chứng | Wave kế |
|---|---|---|---|
| Route sinh được NỐI vào `run_pipeline` sản phẩm | **DONE** | `test_semantic_route_wired_to_production.py`; `main.py::semantic_route_mode` | — |
| `generic` diễn hoạt trạng thái theo bước (`Frame.values`) | **DONE** | `STACK_VISUAL_ACCEPTANCE.md` 6/6 khung, `--faultcheck` tụt 2/6 | — |
| Nhánh PHÁT không bị classifier legacy phủ quyết | **DONE** | `_envelope_tu_route_sinh`; đo: `served` → envelope `ok` | — |
| Vòng sửa có trần cho `stage_semantic_program` | **DONE** | `MAX_SEMANTIC_PROGRAM_ATTEMPTS=3`; lỗi cú pháp 4→2→1→0 | — |
| Bốn biên ký pháp (`spec_version`·`container`·`condition`·nesting) | **DONE** | `test_*_canonicalization.py`, `MAX_NESTING_DEPTH` 4→6 | — |
| **C₂ không cho nghĩa vụ VÔ HIỆU phát đi** | **DONE** | `test_derived_sequence_vacuous.py` 7 test, hai chiều | — |
| **Route sinh ra mô phỏng ĐÚNG** | **OPEN — chưa có lượt nào** | `SERVE_PROBE_CHAIN §4b`: lượt "phát được" là DƯƠNG TÍNH GIẢ | **cần wave riêng** |
| Trần độ dài `narration` của `generic.rule_scene` | **DONE** | `test_dsl.py` 5 test + `narration-boundary.characterization.test.tsx` 18 test, hai tầng | — |
| Kiểm **nội dung** narration (mâu thuẫn với state) | **OPEN — có chủ đích** | audit §9 cấm dựng hệ kiểm duyệt / LLM judge; tuyên bố đã thu hẹp thay vì hứa suông | — |
| `SEMANTIC_ROUTE_MODE` trong sản phẩm | **`off` có chủ đích** | chưa có bằng chứng route sinh mô phỏng đúng ⇒ bật là sớm | — |
| Đo lại `A` sau bốn biên ký pháp | **OPEN** | phải niêm phong **SEALED MỚI**; cấm chạy lại trên tập cũ | — |
| Bằng chứng thị giác cho envelope do route PHÁT | **PARTIAL** | ảnh có, nhưng chụp đúng lượt dương tính giả | wave sau |

⚠️ **Bài học lặp lại HAI lần trong cùng wave: `status=ok` không phải bằng
chứng.** Lần một: `capture-stack-vnext.mjs` tiêm envelope thẳng vào store nên
chứng minh renderer chứ không chứng minh đường sinh. Lần hai: envelope `ok` với
5 khung mà mọi khung đều rỗng. Cả hai lần chỉ lộ ra khi **mở ảnh ra xem**.

## 5. Phủ chương trình

| Owner / Feature | Trạng thái | Bằng chứng | Wave kế |
|---|---|---|---|
| Ma trận phủ chương trình | **PARTIAL** | `COVERAGE.md` + `catalog_runtime_matrix` + báo cáo W2A (8 đơn vị, mọi đơn vị ≥3 case) | **W13** |
| Đơn vị chương trình mỏng (<3 case) | **DONE (W2A)** | T10.CD2 2→3, T12CS.CD7 1→3 (3 case cross-domain mới); khoá bởi guard ngưỡng | — |
| Tuyên bố bị cấm (không claim phủ toàn chương trình) | **DONE** | `COVERAGE.md §O` | giữ nguyên |
| `CURRICULUM_SUPPORT_PARTIAL` | **GIỮ** | — | W13 |
| `LEARNER_IMPACT_NOT_EVALUATED` | **GIỮ** | chưa có nghiên cứu trên người học | — |
