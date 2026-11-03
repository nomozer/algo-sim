# Tiền Đăng Ký Đánh Giá Độc Lập H-1 & So Sánh Bắt Cặp Live (`H1_PREREGISTRATION`)

**Chiến dịch:** `H1_PAIRED_LIVE_EVALUATION` · **Master Epic:** `ALGOSIM_MASTER_HYBRID_BACKEND_REPLACEMENT` · **Phạm vi:** `BACKEND_ONLY` (`frontend/**`: 0 thay đổi) · **Ngày đăng ký:** `2026-11-03`.

> [!IMPORTANT]
> **Trạng thái niêm phong trước thực thi (`0` live provider calls):**
> - `CANDIDATE_FROZEN` = **`180db769`** (`product_commit_sha = d331e75b5bbf15722eca77c54e398173eefec98d`, `measured_system = 276fc548196e13ea…`, `118` files — `MATCH`).
> - `H1_AUTHORING_INDEPENDENCE` = **`NOT_ESTABLISHED`** (chưa có tác giả độc lập được chỉ định / chưa có file corpus 60 đề).
> - `H1_MEASUREMENT` = **`NOT_MEASURED`**.
> - Tài liệu này khóa toàn bộ danh tính hệ thống, quy tắc chấm ba tầng, giao thức bắt cặp `LLM_ONLY` vs `HYBRID`, kế hoạch thống kê và quy tắc quy kết lỗi **trước khi** mở bất kỳ đề `H-1` hay gửi bất kỳ HTTP request nào tới Gemini.

---

## 1. Danh Tính Hệ Thống Đóng Băng Trước Phép Đo (§I – §II)

Không có bất kỳ thay đổi mã sản phẩm nào trong `backend/app/**` kể từ `180db769`. Toàn bộ cấu hình hệ thống được khóa cứng như sau (xác minh máy tại [`H1_CORPUS_INTEGRITY.json`](H1_CORPUS_INTEGRITY.json)):

| Thành phần | Giá trị đã khóa | Nguồn xác minh |
|---|---|---|
| Nhánh làm việc | `research/hybrid-master-backend-replacement` | Git worktree sạch |
| Checkpoint cơ sở | `8daf3b64c21badc7426e1893e6eeb4d10f7230e1` | `git rev-parse` |
| Commit mã sản phẩm | `d331e75b5bbf15722eca77c54e398173eefec98d` | [`EVALUATION_CANDIDATE.json`](../../../semantic-benchmark/EVALUATION_CANDIDATE.json) |
| Frozen candidate commit | `180db769` (`manifest sha256 = 218404c8794861b1…`) | `freeze_evaluation_candidate.py --verify` (`MATCH`) |
| `measured_system` | `276fc548196e13eaa0ca7635428248dcaee7be79b79dff58c24a0478cddd4c63` (`118` files) | `runtime_identity()` |
| Geometry Registry | `geometry-functions/32` | `backend/app/simulation/geometry_functions/registry.py` |
| Geometry Planner | `geometry-fact-planner/26` | `backend/app/simulation/geometry_functions/planner.py` |
| Exact Kernel / Engine | `geometry-function-engine/24` | `backend/app/simulation/geometry_functions/engine.py` |
| Hợp đồng trích xuất | `typed-fact-next/2` (`TypedFactNextPayloadV2`) | `backend/app/simulation/geometry_functions/typed_fact_next.py` |
| Simulation Adapter | `hybrid-simulation-adapter/4` | `backend/app/ai/adapter4_route.py` |
| Chế độ sản phẩm mặc định | `DEFAULT_MODE = "LLM_ONLY"`, `HYBRID_ROUTE_MODE = "off"`, `CACHE_VERSION = "131"` | `backend/app/main.py`, `backend/app/ai/pipeline.py` |
| Model live | `gemini-2.5-flash` (`skills_sha256 = 1dd37ccce05a9c15…`) | `backend/app/ai/gemini.py` |
| Paired harness | `4af1dc76355ec4f59d1f9045b7cee03d40b1bab3528290963776be85daa408d6` | [`run_paired_route_evaluation.py`](../../../../../backend/scripts/run_paired_route_evaluation.py) |
| Equivalence & sealing scorer | `4c4213eba90e411a302202c002f6a7bc536bac9c22924297bb2c0286d19a156b` | [`score_independent_holdout_equivalence.py`](../../../../../backend/scripts/score_independent_holdout_equivalence.py) |

**Cam kết đóng băng (§II):**
- Giữ nguyên tuyệt đối prompt, `TypedFactNextPayloadV2` wire schema, Source Gate, FactGraph, Planner, Registry, Kernel và Adapter `/4` trong suốt phép đo `H-1`.
- Nếu phát hiện lỗi bắt buộc của mã sản phẩm **trước** khi mở `H-1` cho phép đo, phải lập candidate mới, chạy regression đầy đủ và đóng băng lại trước khi chạm vào `H-1`. Hiện tại qua toàn bộ kiểm tra pre-run: **0 lỗi sản phẩm cần sửa**; candidate `180db769` giữ nguyên.

---

## 2. Giải Quyết Ranh Giới Strict Contract vs Semantic Correctness Trước H-1 (§III)

### 2.1. Đối chiếu tài liệu sản phẩm cho câu hỏi gộp thiết diện + diện tích

Trong chiến dịch phát triển C26 ([`HYBRID_LIVE_EXTRACTION_RETEST_REPORT.md`](../hybrid-live-extraction-retest/HYBRID_LIVE_EXTRACTION_RETEST_REPORT.md) §10), có **7 ca phục vụ đúng 100% đáp số toán học** (`K-A01..A04`, `R1-B01`, `R1-B02`, `R1-C02`) nhưng bị bộ chấm lịch sử gắn `SERVED_WRONG` (cùng `2` ca âm tính `K-B01`, `K-B02` từ chối đúng mã nhưng bị gắn `WRONG_REASON_REFUSAL`). Cả 9 đề này đều chứa câu mệnh lệnh hai vế:

> *"Xác định thiết diện của `<khối>` cắt bởi `(P)` và tính diện tích thiết diện đó."*

Đối chiếu trực tiếp với các hợp đồng kiến trúc và mã nguồn sản phẩm hiện hành:

1. **[`GROUNDED_GOAL_COMPLETENESS_CONTRACT.md`](../../../../architecture/GROUNDED_GOAL_COMPLETENESS_CONTRACT.md) (mục nguyên tắc cốt lõi):** Quy định rõ *"Đề có thể yêu cầu nhiều mục tiêu. Không gộp chúng thành một lựa chọn"* và tách bạch hai họ đầu ra hợp lệ duy nhất: **mục tiêu mô phỏng** (`simulation_goal`) và **mục tiêu tính toán** (`math_goal`).
2. **[`TYPEDFACT_NEXT_ADAPTER3_CONTRACT.md`](../../../../architecture/TYPEDFACT_NEXT_ADAPTER3_CONTRACT.md) (§3.1 & §3.4):** Định nghĩa `construct_plane_section` là mục tiêu mô phỏng tường minh khi người học yêu cầu xác định/dựng thiết diện, tách rời với mục tiêu đo lường `area`.
3. **[`typed_fact_next.py`](../../../../../backend/app/simulation/geometry_functions/typed_fact_next.py) (`KIND_ALLOWED_FIELDS["simulation_goal"]["construct_plane_section"]`):** Cho phép chính thức các khóa `{"kind", "plane_ref", "target_solid_id", "source_quote"}` (trong đó `target_solid_id` là tùy chọn hợp lệ như ở `K-B02`).
4. **[`geometry_analyze.md`](../../../../../backend/app/ai/skills/geometry_analyze.md) & [`visual_obligations.py`](../../../../../backend/app/simulation/semantic_program/visual_obligations.py):** Trên cả đường `LLM_ONLY`, mệnh lệnh xác định thiết diện sinh nghĩa vụ trực quan riêng cho đa giác giao tuyến bên cạnh đại lượng diện tích.
5. **[`typed_fact_next_extraction.py`](../../../../../backend/app/ai/typed_fact_next_extraction.py) (`TYPED_FACT_NEXT_SYSTEM_INSTRUCTION`):** Chỉ dẫn hệ thống yêu cầu Gemini phát biểu `construct_plane_section` khi đề có mệnh lệnh xác định/dựng thiết diện.

**Kết luận kỹ thuật từ hợp đồng sản phẩm:**
- Câu **"Xác định thiết diện … và tính diện tích thiết diện đó"** có **hai mục tiêu ngữ nghĩa tường minh** do người học yêu cầu (`construct_plane_section` + `measurement: area`). Việc gold lịch sử của `K-1` / `R-1` chỉ ghi `area` là một quy ước rút gọn của người viết fixture trước đây, không phải lỗi hiểu sai đề của Gemini.
- Ngược lại, câu **"Tính diện tích thiết diện của hình chóp cắt bởi mặt phẳng (P)"** (không có mệnh lệnh *"xác định / tìm / dựng / vẽ thiết diện"*) chỉ có **một mục tiêu ngữ nghĩa tường minh** (`measurement: area`), còn phép dựng thiết diện là bước phân rã nội bộ của Planner.

### 2.2. Ba tầng chấm độc lập & Chính sách tương đương ngữ nghĩa đã khóa (`h1-section-determination-equivalence/1`)

Không sửa bất kỳ nhãn lịch sử nào trong `K-1`, `S-2`, `R-1` hay biên nhận C26. Thay vào đó, bộ chấm [`score_independent_holdout_equivalence.py`](../../../../../backend/scripts/score_independent_holdout_equivalence.py) tách minh bạch ba tiêu chí cho mọi lượt đánh giá trích xuất/đơn nhánh:

| Tầng | Định nghĩa chính xác | Cái gì bị bác bỏ (Fail) | Kết quả kiểm chứng chỉ-đọc trên C26 (`70` ca, `41` dương tính) |
|---|---|---|---|
| **A. Mathematical correctness** | Ca dương tính được `SERVED` với mọi đại lượng mục tiêu khớp chính xác `oracle` (`radical.from_json`), có chứng chỉ exact kernel hợp lệ; `0` ca âm tính/mâu thuẫn/thiếu dữ kiện/ngoài miền bị phục vụ. | Bất kỳ sai lệch đáp số nào, thiếu đáp số được hỏi, thiếu chứng chỉ, hoặc phục vụ nhầm ca âm tính. | `served_correct`: **37 / 41 (90.24%)** · `wrong_served`: **0 / 70 (0.0%)** |
| **B. Semantic goal correctness** (`h1-section-determination-equivalence/1`) | Khớp đầy đủ `facts_signature` và tập mục tiêu ngữ nghĩa; **chỉ** chấp nhận mục tiêu bổ sung `("simulation", "construct_plane_section", S)` (hoặc có thêm `target_solid_id`) **khi và chỉ khi**: (i) nguyên văn `problem_text` chứa mệnh lệnh xác định/tìm/dựng/vẽ thiết diện tường minh, **và** (ii) `S` đúng là đối tượng thiết diện của mục tiêu `area`/`radius` kỳ vọng. | Tự thêm `construct_plane_section` khi đề chỉ hỏi *"Tính diện tích thiết diện…"* (không yêu cầu xác định thiết diện); tự thêm bất kỳ mục tiêu không được hỏi nào khác (như `volume`, `distance`); hoặc bỏ sót bất kỳ mục tiêu nào trong đề. | `goal_completeness`: **52 / 53 (98.11%)** · `served_correct`: **37 / 41 (90.24%)** · `wrong_served`: **0 / 70 (0.0%)** |
| **C. Strict contract correctness** | `TypedFactNextPayloadV2` hợp lệ schema, khớp 1-1 chữ ký tập mục tiêu nghiêm ngặt với nhãn gold ghi sẵn, đúng operands, canonical identity và `source_quote` nguyên văn, không có khóa ngoài hợp đồng. | Mọi chênh lệch tập mục tiêu so với gold ghi sẵn (kể cả `construct_plane_section` dư so với gold rút gọn), sai quote, sai scope hoặc thừa khóa. | `goal_completeness`: **43 / 53 (81.13%)** · `served_correct`: **30 / 41 (73.17%)** · `wrong_served`: **7 / 70 (10.0%)** |

*(Biên nhận kiểm chứng máy chỉ-đọc trên 70 dòng C26: [`c26-three-tier-verification.json`](c26-three-tier-verification.json)).*

**Đối với phép đo bắt cặp `LLM_ONLY` vs `HYBRID` trên `H-1`:**
- Bộ chấm chính thức của giao thức §7 ([`run_paired_route_evaluation.py`](../../../../../backend/scripts/run_paired_route_evaluation.py) `score()`) đọc trực tiếp các đối tượng `quantity` thuộc `display_group = ["target"]` trong `scene3d` của cả hai arm và so khớp chính xác với `oracle`. Vì `construct_plane_section` sinh đối tượng hình học mặt cắt (`polygon3`/`section`) chứ không sinh thêm `quantity` giả, cả hai arm đều được chấm công bằng tuyệt đối trên cùng một thước đo đầu ra người học.
- Đồng thời, trên nhánh `HYBRID`, báo cáo `H-1` bắt buộc xuất **song song cả ba tầng A / B / C** để không che khuất bất kỳ sai khác hợp đồng nào.

### 2.3. Quyết định ngắn cần Owner xác nhận về định nghĩa sản phẩm (nếu muốn khóa quy ước chuẩn duy nhất)

> **Quyết định định nghĩa sản phẩm (Tùy chọn xác nhận từ Owner — không chặn việc soạn đề H-1):**
> Với câu đề bài tiếng Việt *"Xác định thiết diện của hình chóp cắt bởi mặt phẳng (P) và tính diện tích thiết diện đó"*:
> - **Phương án P1 (Khuyến nghị — khớp hợp đồng hiện hành & hướng dẫn H-1 Mục 3):** Xem đây là **2 mục tiêu người học tường minh** (`construct_plane_section` + `area`), trong khi câu *"Tính diện tích thiết diện…"* là **1 mục tiêu** (`area`). Mọi mục tiêu không nêu trong đề (ví dụ tự tính thêm `volume`) vẫn bị chấm **SAI** ở cả strict và semantic.
> - **Phương án P2 (Strict một mục tiêu số):** Quy ước mọi bài có hỏi diện tích thiết diện chỉ mang duy nhất `math_goal = area` (xem mệnh lệnh *"Xác định thiết diện"* chỉ là lời dẫn cho phép tính diện tích). Nếu chọn P2, hệ thống vẫn không sửa ở vòng này mà giữ nguyên báo cáo chênh lệch ở cột Strict Contract.

---

## 3. Giao Thức Niêm Phong Corpus H-1 Trước Khi Gọi Provider (§IV.3)

Ngay khi nhận file `h1-independent-corpus.json` từ tác giả độc lập do Owner chỉ định, thực thi tuần tự 8 bước niêm phong bắt buộc (tự động hóa qua `run_paired_route_evaluation.py --manifest` và `score_independent_holdout_equivalence.py integrity --corpus ...`):

1. **Kiểm tra định dạng (`1_format_validated`):** Xác thực schema `hybrid-master-paired-heldout/2`, không có `dry_run`, mọi `id` và `problem_text` không rỗng.
2. **Kiểm tra trùng lặp & nhiễm phát triển (`2_duplication_and_contamination_checked`):** Chuẩn hóa NFC + chữ thường + khoảng trắng + giải mã `\uXXXX`; quét toàn bộ kho mã nguồn. Trùng khớp chính xác (`exact_overlap_cases`) **chặn cứng phép đo**; trùng khớp shingle 8 từ $\ge 50\%$ (`near_overlap_cases`) dừng để rà soát thủ công trước khi mở khóa.
3. **Xác minh số lượng & phân tầng (`3_count_and_stratification_45_5_5_5_verified`):** Đúng `60` ca = `45 SERVE` + `5 OUT_OF_DOMAIN` + `5 CONTRADICTORY_DATA` + `5 MISSING_DATA`; kiểm tra tối thiểu $\ge 3$ ca cho từng họ hình / loại câu hỏi.
4. **Xác minh oracle chính xác (`4_independent_oracle_parsed_exact`):** Mọi giá trị trong `oracle` parse thành công qua `radical.parse_exact` (cấm số thập phân, giữ nguyên $\pi$ và căn thức chính xác).
5. **Ghi mã băm bất biến (`5_corpus_and_oracle_sha256_recorded`):** Tính và lưu `corpus_sha256` (trên byte nguyên văn của file) và `oracle_sha256` (trên biểu diễn chuẩn hóa của 60 mục tiêu/oracle).
6. **Niêm phong manifest đánh giá (`6_evaluation_manifest_sealed`):** Cập nhật `H1_CORPUS_INTEGRITY.json` sang `CORPUS_SEALED_AWAITING_BUDGET` (hoặc sẵn sàng chạy) và commit vào Git trước request đầu tiên.
7. **Khóa đăng ký trước (`7_candidate_scorer_model_budget_acceptance_preregistered`):** Đã hoàn tất tại tài liệu này (`180db769`, `gemini-2.5-flash`, acceptance §7).
8. **Xác minh phê duyệt ngân sách & quyền trả phí của Owner (`8_owner_live_budget_approved`):** Kiểm tra `paired-live-owner-approval.json` do Owner cấp (`owner_decision == "APPROVED_BY_USER"`, khớp `corpus_sha256`, `measured_system`, `harness_sha256`, `authoring_independence == "ESTABLISHED"`, `evaluator_independence == "ESTABLISHED"`). Chỉ khi cả 8 cổng đều `true` mới gửi request đầu tiên.

---

## 4. Giao Thức So Sánh Bắt Cặp Live `LLM_ONLY` vs `HYBRID` (§V)

### 4.1. Cấu hình hai nhánh thực thi và sự khác biệt kỹ thuật minh bạch

Cùng 60 đề `H-1` chạy qua cả hai nhánh theo thứ tự ngẫu nhiên hóa tất định theo từng `case_id` (`seed = "hybrid-master-paired/2026-10-31"` trong `arm_order()`), **tuyệt đối không fallback chéo giữa hai arm** và **tắt hoàn toàn bộ nhớ đệm (`cache = none`)**:

| Thuộc tính | Arm A: `LLM_ONLY` (Production hiện tại) | Arm B: `HYBRID` (Ứng viên thay thế `/4`) | Ghi chú công bằng phép đo |
|---|---|---|---|
| Đường thực thi | `ai/pipeline.py::run_pipeline` với `RoutePolicy` mặc định | `main._ngoai_pham_vi` (Domain Gate) $\rightarrow$ `run_hybrid_offline` + `TransportExtractor` | Đúng hành vi thực tế của từng kiến trúc |
| Model | `gemini-2.5-flash` | `gemini-2.5-flash` | Cùng model ID |
| Số provider calls / đề | `0` (nếu Domain Gate chặn) hoặc **`1 – 4` lời gọi tuần tự** (`1` `semantic_analyze` + tối đa `3` `semantic_program` gồm vòng tự sửa `_prompt_sua`) | `0` (nếu Domain Gate chặn) hoặc **đúng `1` lời gọi trích xuất** (`TypedFactNextPayloadV2`) | Bắt buộc so tổng chi phí & tổng độ trễ cấp bài toán, không chỉ so 1 HTTP request |
| `temperature` | `0.1` (giữ nguyên production) | `0.0` (giữ nguyên trích xuất tất định) | Không can thiệp cấu hình gốc |
| `maxOutputTokens` | **Không đặt trần** (giới hạn model `65,536` gồm cả thinking) | `8,192` | Ảnh hưởng trực tiếp đến trần đặt chỗ ngân sách (§VI) |
| `responseSchema` | Gửi ở bước `analyze`; **không gửi** ở bước `semantic_program` (do schema đệ quy `$ref`) | Gửi flat OpenAPI `responseSchema` (`TypedFactNextPayloadV2`) | Đều nằm trong `runtime_identity()` |
| Retry & HTTP timeout | Tối đa `4` lần thử cho lỗi tạm thời `429`/`5xx`, `120 s` mỗi lần thử | Giống hệt (`live_transport`: tối đa `4` lần thử, `120 s` mỗi lần thử) | Đối xứng tầng transport |
| End-to-end deadline | Không đặt tổng deadline | `480 s` (`HYBRID_LIVE_DEADLINE_S` trong harness; route live `main.py` hiện mặc định `60 s / 180 s`) | Trước khi cutover phải đồng bộ cấu hình deadline production nếu cần (§X) |

### 4.2. Hợp đồng nghiệm thu đã khóa (Acceptance Contract §7 — không chỉnh ngưỡng sau chạy)

Phán quyết máy `acceptance()` trong [`run_paired_route_evaluation.py`](../../../../../backend/scripts/run_paired_route_evaluation.py) trả về `HYBRID_CUTOVER_GO` **khi và chỉ khi toàn bộ 8 điều kiện `0..7` cùng đạt `True`** (mọi tiêu chí `False` hoặc `None` / không khả tính đều dẫn tới `HYBRID_CUTOVER_NO_GO`):

- **Tiêu chí `0_preconditions`:** Corpus đúng cấu trúc `45 SERVE + 5/5/5 REFUSE`; lượt chạy hoàn tất (`completed = true`, `stop_reason = null`, không arm nào bị dừng sớm, đủ `60` cặp khớp chính xác tập ID của corpus).
- **Tiêu chí `1_no_wrong_served` (An toàn tối thượng):** `HYBRID` có **`0` ca `wrong_served` quan sát được** trên toàn bộ 60 đề (cả 45 đề khả giải lẫn 15 đề âm tính) và `wrong_served_only_HYBRID == 0`. Khoảng tin cậy Wilson 95% trên số dòng thực thi (`exercised`) được báo cáo minh bạch như biên độ bất định thống kê.
- **Tiêu chí `2_served_correct_non_inferior`:** Trên 45 đề `SERVE`, kiểm định McNemar hai phía không nghiêng có ý nghĩa thống kê về phía `LLM_ONLY` ở mức $\alpha = 0.05$, **và** hiệu tỉ lệ $\text{rate}_{\text{HYBRID}} - \text{rate}_{\text{LLM\_ONLY}} \ge -5\text{ pp}$ (tức trên 45 bài, `HYBRID` không được kém `LLM_ONLY` quá `2` bài).
- **Tiêu chí `3_refusal`:** `HYBRID` từ chối **100%** các bài `expect = REFUSE` (trừ lỗi hạ tầng được tách riêng) và có tỉ lệ đúng lớp lý do từ chối (`refusal_reason_accuracy`) $\ge$ `LLM_ONLY`.
- **Tiêu chí `4_latency`:** Độ trễ trung vị (median) cấp bài toán của `HYBRID` $\le$ `LLM_ONLY`, **và** phân vị `p90` của `HYBRID` $\le 1.5 \times \text{p90}_{\text{LLM\_ONLY}}$.
- **Tiêu chí `5_cost` (Bảo thủ nghiêng về NO-GO):** Chi phí USD trên mỗi bài phục vụ đúng của `HYBRID` tính theo **cận trên (`usd_charged_total`, tính đủ giá cho cả cached tokens và trần cho request thiếu usage)** phải $\le$ chi phí tương ứng của `LLM_ONLY` tính theo **cận dưới (`usd_reported_total`, tính cached prompt tokens bằng `0`)**.
- **Tiêu chí `6_reliability`:** Lỗi kỹ thuật/hạ tầng (`technical_failures`) $\le 5\%$ mỗi arm (tối đa `3 / 60` đề) và `scorer_errors == 0`.
- **Tiêu chí `7_independence`:** File phê duyệt của Owner xác nhận `corpus_author` khác rỗng và cả `authoring_independence` lẫn `evaluator_independence` đều bằng `"ESTABLISHED"`.

*(Cờ cảnh báo bổ sung: nếu `LLM_ONLY` đạt `0` bài đúng, hệ thống gắn cờ `CONTROL_ARM_DEGENERATE` để Owner xem xét chứ không tự coi là thắng lợi thực chất).*

### 4.3. Kế hoạch phân tích thống kê bắt cặp & Giới hạn cỡ mẫu (§V.2 & §VIII)

1. **Bảng phân rã bắt cặp $2 \times 2$ trên cùng `case_id` (`N = 45` cho `served_correct`, `N = 60` cho `wrong_served`):**
   - $n_{11}$: cả `HYBRID` và `LLM_ONLY` cùng đúng (`both`).
   - $n_{10}$: chỉ `HYBRID` đúng, `LLM_ONLY` sai/từ chối (`only_HYBRID`).
   - $n_{01}$: chỉ `LLM_ONLY` đúng, `HYBRID` sai/từ chối (`only_LLM_ONLY`).
   - $n_{00}$: cả hai cùng sai hoặc từ chối (`neither`).
2. **Ước lượng điểm & khoảng tin cậy:**
   - Báo cáo khoảng tin cậy **Wilson 95%** cho từng tỉ lệ đơn nhánh (`served_correct`, `wrong_served`, `false_refusal`, `refusal_reason_accuracy`).
   - Báo cáo hiệu bắt cặp $\Delta = (n_{10} - n_{01}) / N$ kèm khoảng tin cậy 95% cho hiệu hai tỉ lệ bắt cặp (Newcombe/Wald paired score CI) và trị số $p$ **exact McNemar hai phía** trên cặp bất đồng $(n_{10}, n_{01})$.
3. **Giới hạn thống kê khai báo trước (không diễn giải quá mức):**
   - Với $N = 60$ bài thực thi và `0` lỗi `wrong_served`, cận trên Wilson 95% vẫn xấp xỉ **$6.0\%$** ($0/60 \Rightarrow [0.0\%, 6.02\%]$): kết quả `0/60` chứng minh tuân thủ cổng nghiệm thu trên mẫu, **không** chứng minh xác suất lỗi ngoài thực tế bằng `0`.
   - Với $N = 45$ bài `SERVE`, ngưỡng chênh lệch $-5\text{ pp}$ (tối đa kém 2 bài) chặt hơn kiểm định McNemar ở các cặp bất đồng nhỏ; cả hai chỉ số đều được báo cáo đầy đủ.
   - Mọi kết luận tổng quát hóa chỉ có hiệu lực trong phạm vi phân bố các họ hình và cách diễn đạt mà `H-1` lấy mẫu.

---

## 5. Quy Tắc Quy Kết Lỗi Sau Đánh Giá & Chống Nhiễm Tập Độc Lập (§IX)

Sau khi niêm phong kết quả chạy `H-1`, mọi ca không đạt của `HYBRID` bắt buộc được phân loại vào đúng **1 trong 11 nhãn quy kết đã khóa**:

1. `EXTRACTION_FAILURE` — Gemini trích xuất sai cấu trúc/dữ kiện/mục tiêu/quote hoặc vi phạm schema `TypedFactNextPayloadV2`.
2. `SOURCE_GATE_FAILURE` — Trích xuất hợp lý nhưng văn phạm đóng của Source Gate từ chối quá chặt (`UNGROUNDED_VALUE`, `SOURCE_OBJECT_MISMATCH`, …) được kiểm chứng bằng gold replay của chính ca đó.
3. `FACT_GRAPH_FAILURE` — Lỗi gộp quan hệ, canonical identity hoặc suy diễn tương thích trong FactGraph/Bridge.
4. `PLANNER_FAILURE` — Đã qua Source Gate và đủ primitives trong Registry nhưng Planner (`/26`) không lập được kế hoạch. *(Lưu ý: tuyệt đối không gọi `REGISTERED_DECOMPOSITION` là `GENUINE_DISCOVERY`).*
5. `REGISTRY_COVERAGE_GAP` — Bài toán thuộc phạm vi công bố nhưng thiếu hàm dựng/đo trong `geometry-functions/32`.
6. `KERNEL_FAILURE` — Lỗi tính toán đại số chính xác, miền căn thức (`EXACT_DOMAIN_EXCEEDED`), hoặc lỗi kiểm chứng chứng chỉ trong Engine (`/24`).
7. `ADAPTER_FAILURE` — Lỗi ánh xạ kết quả/chứng chỉ sang `scene3d` hoặc envelope của Adapter `/4`.
8. `PROVIDER_FAILURE` — Lỗi HTTP `429`/`5xx`, timeout, hoặc response rỗng từ phía nhà cung cấp Gemini sau khi đã retry.
9. `EXPECTED_REFUSAL` — Từ chối/hỏi làm rõ đúng kỳ vọng trên 15 bài âm tính.
10. `EVALUATION_ORACLE_ISSUE` — Sai sót chứng minh được bằng toán học trong đáp án chuẩn ban đầu (nếu xảy ra: chỉ được ghi vào phụ lục đính chính độc lập, **tuyệt đối không sửa file corpus/gold gốc để làm đẹp điểm Hybrid**).
11. `UNKNOWN` — Không đủ thông tin phân định nhân quả.

**Quy tắc đốt cháy tập kiểm định mù (One-Time Blindness Rule):**
- Nếu kết quả `H-1` dẫn tới bất kỳ chỉnh sửa nào trên mã sản phẩm (`backend/app/**`), `H-1` lập tức chuyển trạng thái sang **tập hồi quy phát triển đã mở (`POST_EVALUATION_DEVELOPMENT_REGRESSION`)** và **không được dùng lại `H-1` để tuyên bố tổng quát hóa mù cho candidate mới**. Khi đó bắt buộc phải có vòng đề độc lập kế tiếp (`H-2`) theo đúng giao thức này.
