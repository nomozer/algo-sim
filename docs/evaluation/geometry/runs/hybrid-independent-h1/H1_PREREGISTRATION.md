# Tiền Đăng Ký Đánh Giá Độc Lập H-1 & So Sánh Bắt Cặp Live (`H1_PREREGISTRATION`)

**Chiến dịch:** `H1_PAIRED_LIVE_EVALUATION` · **Master Epic:** `ALGOSIM_MASTER_HYBRID_BACKEND_REPLACEMENT` · **Nhiệm vụ:** `C28` · **Phạm vi:** `BACKEND_ONLY` (`frontend/**`: 0 thay đổi) · **Ngày đăng ký:** `2026-11-03`.

> [!IMPORTANT]
> **Trạng thái niêm phong trước thực thi (`0` live provider calls):**
> - `CANDIDATE_FROZEN` = **`180db769`** (`product_commit_sha = d331e75b5bbf15722eca77c54e398173eefec98d`, `measured_system = 276fc548196e13ea…`, `118` files — `MATCH`).
> - `SEMANTIC_EQUIVALENCE_POLICY` = **`h1-section-determination-equivalence/1`** (`P1_PREREGISTERED_TECHNICAL_POLICY`, `owner_formal_signoff = NOT_SIGNED_OFF`).
> - `PROPOSED_CAMPAIGN_BUDGET` = **`campaign_max_requests = 300`, `campaign_max_usd = 5.00`** (`PENDING_OWNER_DECISION`; hạch toán nguyên tử `SafeCampaignBudget` bằng `decimal.Decimal`).
> - `H1_AUTHORING_INDEPENDENCE` = **`NOT_ESTABLISHED`** (chưa có tác giả độc lập được chỉ định / chưa có file corpus 60 đề).
> - `H1_MEASUREMENT` = **`NOT_MEASURED`**.
> - Tài liệu này khóa toàn bộ danh tính hệ thống, chính sách chấm P1 ba tầng độc lập, cơ chế ngân sách an toàn theo từng request, giao thức bắt cặp `LLM_ONLY` vs `HYBRID`, kế hoạch thống kê và quy tắc quy kết lỗi **trước khi** mở bất kỳ đề `H-1` hay gửi bất kỳ HTTP request nào tới Gemini.

---

## 1. Danh Tính Hệ Thống Đóng Băng Trước Phép Đo (§I, §II, §VI)

Không có bất kỳ thay đổi mã sản phẩm nào trong `backend/app/**` kể từ `180db769`. Toàn bộ cấu hình hệ thống và bộ công cụ đánh giá được khóa cứng như sau (xác minh máy tại [`H1_CORPUS_INTEGRITY.json`](H1_CORPUS_INTEGRITY.json)):

| Thành phần | Giá trị đã khóa | Nguồn xác minh |
|---|---|---|
| Nhánh làm việc | `research/hybrid-master-backend-replacement` | Git worktree sạch |
| Checkpoint cơ sở | `7a2a7592b3eef03afb74b64778e42b2a2311a933` | `git rev-parse` |
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
| Paired harness | `8af7ca1f27e7ca3fb4e58ba7e0e067bc17973d8254a086e6c39d896078cd2e1f` | [`run_paired_route_evaluation.py`](../../../../../backend/scripts/run_paired_route_evaluation.py) |
| Equivalence & sealing scorer | `7ada8a0616e9482b4984e92e86804bfc60deab540a505a10da65d8436ceba391` | [`score_independent_holdout_equivalence.py`](../../../../../backend/scripts/score_independent_holdout_equivalence.py) |
| Chính sách chi phí & ngân sách | `SafeCampaignBudget` (`decimal.Decimal`, đơn giá chuẩn `\$0.30 / 1M` in · `\$2.50 / 1M` out+think; đề xuất `300` req / `\$5.00` chờ duyệt) | [`PAIRED_LIVE_BUDGET_PROPOSAL.md`](PAIRED_LIVE_BUDGET_PROPOSAL.md) |

**Cam kết đóng băng (§II & §VI):**
- Giữ nguyên tuyệt đối prompt, `TypedFactNextPayloadV2` wire schema, Source Gate, FactGraph, Planner, Registry, Kernel, Adapter `/4` và hành vi sản phẩm `LLM_ONLY` trong suốt phép đo `H-1`.
- Nếu phát hiện lỗi bắt buộc của mã sản phẩm **trước** khi mở `H-1` cho phép đo, phải lập candidate mới, chạy Full T3 và đóng băng lại trước khi chạm vào `H-1`. Hiện tại qua toàn bộ kiểm tra pre-run: **0 lỗi sản phẩm cần sửa**; candidate `180db769` giữ nguyên.

---

## 2. Chốt Chính Sách Mục Tiêu Ngữ Nghĩa P1 & Ba Tầng Đánh Giá Độc Lập (§III)

### 2.1. Đối chiếu tài liệu sản phẩm cho câu hỏi thiết diện

Trong chiến dịch phát triển C26 ([`HYBRID_LIVE_EXTRACTION_RETEST_REPORT.md`](../hybrid-live-extraction-retest/HYBRID_LIVE_EXTRACTION_RETEST_REPORT.md) §10), có **7 ca phục vụ đúng 100% đáp số toán học** (`K-A01..A04`, `R1-B01`, `R1-B02`, `R1-C02`) nhưng bị bộ chấm lịch sử gắn `SERVED_WRONG` (cùng `2` ca âm tính `K-B01`, `K-B02` từ chối đúng mã nhưng bị gắn `WRONG_REASON_REFUSAL`) do đề bài chứa mệnh lệnh hai vế *"Xác định thiết diện … và tính diện tích thiết diện đó"* trong khi gold lịch sử rút gọn chỉ ghi `area`.

Đối chiếu trực tiếp với hợp đồng kiến trúc và mã nguồn sản phẩm hiện hành:
1. **[`GROUNDED_GOAL_COMPLETENESS_CONTRACT.md`](../../../../architecture/GROUNDED_GOAL_COMPLETENESS_CONTRACT.md):** Quy định *"Đề có thể yêu cầu nhiều mục tiêu. Không gộp chúng thành một lựa chọn"* và tách bạch `simulation_goal` với `math_goal`.
2. **[`TYPEDFACT_NEXT_ADAPTER3_CONTRACT.md`](../../../../architecture/TYPEDFACT_NEXT_ADAPTER3_CONTRACT.md) (§3.1 & §3.4):** Định nghĩa `construct_plane_section` là mục tiêu mô phỏng tường minh khi người học yêu cầu xác định/dựng thiết diện, tách rời với mục tiêu đo lường `area`.
3. **[`typed_fact_next.py`](../../../../../backend/app/simulation/geometry_functions/typed_fact_next.py) (`KIND_ALLOWED_FIELDS["simulation_goal"]["construct_plane_section"]`):** Cho phép chính thức các khóa `{"kind", "plane_ref", "target_solid_id", "source_quote"}`.
4. **[`geometry_analyze.md`](../../../../../backend/app/ai/skills/geometry_analyze.md) & [`visual_obligations.py`](../../../../../backend/app/simulation/semantic_program/visual_obligations.py):** Trên cả đường `LLM_ONLY`, mệnh lệnh xác định thiết diện sinh nghĩa vụ trực quan riêng cho đa giác giao tuyến bên cạnh đại lượng diện tích.
5. **[`typed_fact_next_extraction.py`](../../../../../backend/app/ai/typed_fact_next_extraction.py) (`TYPED_FACT_NEXT_SYSTEM_INSTRUCTION`):** Chỉ dẫn hệ thống yêu cầu Gemini phát biểu `construct_plane_section` khi đề có mệnh lệnh xác định/dựng thiết diện.

### 2.2. Quy ước kỹ thuật P1 đã chốt cho nghiên cứu H-1 (`h1-section-determination-equivalence/1`)

Chính sách **P1** (`h1-section-determination-equivalence/1`) được chốt làm chính sách kỹ thuật tiền đăng ký cho nghiên cứu `H-1` (`owner_formal_signoff = NOT_SIGNED_OFF` — không giả mạo chữ ký Owner; chỉ ghi nhận phê duyệt chính thức của Owner khi thực sự có):

- **Trường hợp A — *"Xác định thiết diện của hình chóp cắt bởi mặt phẳng (P) và tính diện tích thiết diện đó."*:**
  Có **hai mục tiêu người học tường minh** bắt buộc ở tầng Semantic Goal: `construct_plane_section` **và** `area` (thiếu 1 trong 2 hoặc thừa mục tiêu khác đều bị chấm sai ở `p1_expected_set`).
- **Trường hợp B — *"Tính diện tích thiết diện của hình chóp cắt bởi mặt phẳng (P)."*:**
  Chỉ có **một mục tiêu người học tường minh**: `area`. Phép dựng thiết diện là bước trung gian nội bộ của thuật toán Planner; nếu Gemini tự thêm `construct_plane_section` trong Trường hợp B thì bị phân loại là **sai mục tiêu**.
- **Trường hợp C — Tự thêm đại lượng không được hỏi:**
  Nếu đề chỉ hỏi diện tích mà Gemini tự thêm `volume`, `distance` hoặc bất kỳ mục tiêu nào không nêu trong đề, phải phân loại là **sai mục tiêu** ở cả Semantic Goal và Strict Contract.

### 2.3. Giữ nguyên và tách biệt tuyệt đối ba tầng đánh giá

Không sửa bất kỳ nhãn gold lịch sử nào trong `K-1`, `S-2`, `R-1` hay biên nhận C21/C26, và **tuyệt đối không gộp ba chỉ số thành một nhãn PASS chung**. Bộ chấm [`score_independent_holdout_equivalence.py`](../../../../../backend/scripts/score_independent_holdout_equivalence.py) báo cáo độc lập ba tầng:

| Tầng | Định nghĩa chính xác | Cái gì bị bác bỏ (Fail) | Kết quả kiểm chứng chỉ-đọc trên C26 (`70` ca, `41` dương tính) |
|---|---|---|---|
| **1. Mathematical Correctness** | Ca dương tính được `SERVED` với mọi đại lượng mục tiêu khớp chính xác `oracle` (`radical.from_json`), có chứng chỉ exact kernel hợp lệ; `0` ca âm tính/mâu thuẫn/thiếu dữ kiện/ngoài miền bị phục vụ. | Bất kỳ sai lệch đáp số nào, thiếu đáp số được hỏi, thiếu chứng chỉ, hoặc phục vụ nhầm ca âm tính. | `served_correct`: **37 / 41 (90.24%)** · `wrong_served`: **0 / 70 (0.0%)** |
| **2. Semantic Goal Correctness** (`h1-section-determination-equivalence/1`) | Khớp đầy đủ `facts_signature` và tập mục tiêu ngữ nghĩa theo đúng quy tắc hai chiều **P1** (Trường hợp A bắt buộc đủ `construct_plane_section + area`; Trường hợp B chỉ `area`; Trường hợp C bác bỏ mọi mục tiêu không hỏi). | Bỏ sót `construct_plane_section` ở Trường hợp A; tự thêm `construct_plane_section` ở Trường hợp B; tự thêm `volume`/`distance` không hỏi (Trường hợp C); hoặc bỏ sót bất kỳ mục tiêu nào trong đề. | `goal_completeness`: **52 / 53 (98.11%)** · `served_correct`: **37 / 41 (90.24%)** · `wrong_served`: **0 / 70 (0.0%)** |
| **3. Strict Contract Correctness** | `TypedFactNextPayloadV2` hợp lệ schema, khớp 1-1 chữ ký tập mục tiêu nghiêm ngặt với nhãn gold ghi sẵn, đúng `target` references, operands, canonical identity và `source_quote` nguyên văn, không có khóa ngoài hợp đồng. | Mọi chênh lệch tập mục tiêu so với gold ghi sẵn (kể cả `construct_plane_section` so với gold rút gọn lịch sử), sai quote, sai scope hoặc thừa khóa. | `goal_completeness`: **43 / 53 (81.13%)** · `served_correct`: **30 / 41 (73.17%)** · `wrong_served`: **7 / 70 (10.0%)** |

*(Biên nhận kiểm chứng máy chỉ-đọc trên 70 dòng C26: [`c26-three-tier-verification.json`](c26-three-tier-verification.json)).*

**Đối với phép đo bắt cặp `LLM_ONLY` vs `HYBRID` trên `H-1`:**
- Bộ chấm bắt cặp của giao thức §7 ([`run_paired_route_evaluation.py`](../../../../../backend/scripts/run_paired_route_evaluation.py) `score()`) đọc trực tiếp các đối tượng `quantity` thuộc `display_group = ["target"]` trong `scene3d` của cả hai arm và so khớp chính xác với `oracle`, đồng thời ghi kèm trạng thái chứng chỉ (`certificate_verified`), nguồn gốc tổ hợp Planner (`planner_status`, `composition_provenance`) và giai đoạn/loại lỗi (`failure_stage`, `failure_kind`).
- Song song đó, nhánh `HYBRID` bắt buộc xuất riêng cả 3 chỉ số **Mathematical / Semantic Goal (P1) / Strict Contract**.

---

## 3. Giao Thức Xác Minh Tính Độc Lập & Niêm Phong Corpus H-1 Trước Khi Gọi Provider (§V – §VI)

Ngay khi nhận file `h1-independent-corpus.json` từ tác giả độc lập do Owner chỉ định, thực thi tuần tự 8 bước niêm phong bắt buộc qua `score_independent_holdout_equivalence.py integrity --corpus ...` và `run_paired_route_evaluation.py --manifest`:

1. **Kiểm tra định dạng & duy nhất ID (`1_format_validated`):** Xác thực schema `hybrid-master-paired-heldout/2`, không có `dry_run`, đúng 60 `case_id` duy nhất và `problem_text` không rỗng.
2. **Kiểm tra trùng lặp, nhiễm phát triển & sao chép khung đề (`2_duplication_and_contamination_checked`):**
   - Quét toàn bộ kho mã nguồn (kể cả các ví dụ minh họa trong `H1_AUTHORING_HANDOFF.md` và `corpus-template.json`): trùng khớp chính xác (`exact_overlap_cases`) hoặc trùng khớp khung cấu trúc khi chỉ đổi tên đỉnh và thay số đo (`structural_template_clone_cases` qua `_scan_structural_template_clones`) **chặn cứng niêm phong**; trùng khớp shingle 8 từ $\ge 50\%$ (`near_overlap_cases`) buộc dừng rà soát.
3. **Xác minh số lượng, phân tầng & độ phủ họ hình (`3_count_and_stratification_45_5_5_5_verified`):** Đúng `60` ca = `45 SERVE` + `5 OUT_OF_DOMAIN` + `5 CONTRADICTORY_DATA` + `5 MISSING_DATA`, đồng thời `_verify_stratum_coverage` xác minh đủ cả `7` họ hình (`pyramid`, `prism`, `cuboid`, `cube`, `sphere`, `cylinder`, `cone`) và `5` nhóm câu hỏi (`section_measure`, `distance`, `angle`, `volume`, `area`) với mỗi nhóm $\ge 3$ bài `SERVE`.
4. **Xác minh oracle chính xác, chú giải ngữ nghĩa P1 & bằng chứng tác giả độc lập (`4_independent_oracle_parsed_exact`):**
   - Mọi giá trị trong `oracle` parse thành công qua `radical.parse_exact` (cấm xấp xỉ thập phân); `_assess_oracle_verification` kiểm tra dẫn xuất ký hiệu và gắn nhãn rõ `PENDING_HUMAN_EXPERT_VERIFICATION` cho tới khi có đối soát toán học của chuyên gia con người.
   - Hàm `_verify_semantic_annotations` kiểm tra `semantic_annotations.explicit_goals` phủ đủ khóa `oracle` và nhất quán hai chiều với quy ước **P1**.
   - Hàm `_verify_authoring_independence` **từ chối** đóng dấu `ESTABLISHED` nếu JSON chỉ điền chữ `"ESTABLISHED"` suông: bắt buộc có định danh tác giả con người cụ thể (không phải agent/AI/placeholder), hồ sơ cam kết nguồn gốc độc lập (`author_affiliation` + `independence_evidence`), và lời giải dẫn xuất độc lập cho các bài `SERVE`.
5. **Ghi mã băm bất biến (`5_corpus_and_oracle_sha256_recorded`):** Tính và lưu `corpus_sha256` (trên byte nguyên văn của file) và `oracle_sha256` (`compute_oracle_sha256` trên biểu diễn chuẩn hóa của 60 mục tiêu/oracle).
6. **Niêm phong manifest đánh giá (`6_evaluation_manifest_sealed`):** Cập nhật `H1_CORPUS_INTEGRITY.json` sang `CORPUS_SEALED_AWAITING_BUDGET` và commit trước request đầu tiên.
7. **Khóa đăng ký trước (`7_candidate_scorer_model_budget_acceptance_preregistered`):** Đã hoàn tất tại tài liệu này (`180db769`, `gemini-2.5-flash`, `SafeCampaignBudget`, acceptance §7).
8. **Xác minh phê duyệt ngân sách & quyền trả phí của Owner (`8_owner_live_budget_approved`):** Kiểm tra `paired-live-owner-approval.json` do Owner cấp (trường `owner_decision` do chính Owner ký duyệt, `paid_project_confirmed is True`, khớp `corpus_sha256`, `oracle_sha256`, `measured_system`, `harness_sha256`, `authoring_independence == "ESTABLISHED"`, `evaluator_independence == "ESTABLISHED"`, và hạn mức `campaign_max_requests` / `campaign_max_usd` hợp lệ). Chỉ khi cả 8 cổng đều `true` mới gửi request đầu tiên.

---

## 4. Giao Thức So Sánh Bắt Cặp Live `LLM_ONLY` vs `HYBRID` (§VI – §VIII)

### 4.1. Cấu hình hai nhánh thực thi và sự khác biệt kỹ thuật minh bạch

Cùng 60 đề `H-1` chạy qua cả hai nhánh theo thứ tự ngẫu nhiên hóa tất định theo từng `case_id` (`seed = "hybrid-master-paired/2026-10-31"` trong `arm_order()`), **tuyệt đối không fallback chéo giữa hai arm** và **tắt hoàn toàn bộ nhớ đệm (`cache = none`)**:

| Thuộc tính | Arm A: `LLM_ONLY` (Production hiện tại) | Arm B: `HYBRID` (Ứng viên thay thế `/4`) | Ghi chú công bằng phép đo |
|---|---|---|---|
| Đường thực thi | `ai/pipeline.py::run_pipeline` với `RoutePolicy` mặc định | `main._ngoai_pham_vi` (Domain Gate) $\rightarrow$ `run_hybrid_offline` + `TransportExtractor` | Đúng hành vi thực tế của từng kiến trúc |
| Model | `gemini-2.5-flash` | `gemini-2.5-flash` | Cùng model ID |
| Số provider calls / đề | `0` (nếu Domain Gate chặn) hoặc **`1 – 4` lời gọi tuần tự** (`1` `semantic_analyze` + tối đa `3` `semantic_program` gồm vòng tự sửa `_prompt_sua`) | `0` (nếu Domain Gate chặn) hoặc **đúng `1` lời gọi trích xuất** (`TypedFactNextPayloadV2`) | Bắt buộc so tổng chi phí & tổng độ trễ cấp bài toán, không chỉ so 1 HTTP request |
| `temperature` | `0.1` (giữ nguyên production) | `0.0` (giữ nguyên trích xuất tất định) | Không can thiệp cấu hình gốc |
| `maxOutputTokens` | **Không đặt trần** (giới hạn model `65,536` gồm cả thinking; đặt chỗ đơn lẻ `~\$0.1693/request`) | `8,192` (đặt chỗ đơn lẻ `~\$0.0215/request`) | Đặt chỗ từng request qua `SafeCampaignBudget` thay vì nhân cứng $300 \times \$0.1693$ |
| `responseSchema` | Gửi ở bước `analyze`; **không gửi** ở bước `semantic_program` (do schema đệ quy `\$ref`) | Gửi flat OpenAPI `responseSchema` (`TypedFactNextPayloadV2`) | Đều nằm trong `runtime_identity()` |
| Retry & HTTP timeout | Tối đa `4` lần thử cho lỗi tạm thời `429`/`5xx`, `120 s` mỗi lần thử (mỗi retry tốn 1 slot request + đặt chỗ USD riêng) | Giống hệt (`live_transport`: tối đa `4` lần thử, `120 s` mỗi lần thử, `is_retry = attempt > 0`) | Đối xứng tầng transport & hạch toán retry |
| End-to-end deadline | Không đặt tổng deadline | `480 s` (`HYBRID_LIVE_DEADLINE_S` trong harness; route live `main.py` hiện mặc định `60 s / 180 s`) | Trước khi cutover phải đồng bộ cấu hình deadline production nếu cần |

### 4.2. Hợp đồng nghiệm thu đã khóa (Acceptance Contract §7 — không chỉnh ngưỡng sau chạy)

Phán quyết máy `acceptance()` trong [`run_paired_route_evaluation.py`](../../../../../backend/scripts/run_paired_route_evaluation.py) trả về `HYBRID_CUTOVER_GO` **khi và chỉ khi toàn bộ 8 điều kiện `0..7` cùng đạt `True`** (mọi tiêu chí `False` hoặc `None` / không khả tính, hoặc lượt chạy dừng sớm `INCOMPLETE_PAIRED_EVALUATION`, đều dẫn tới `HYBRID_CUTOVER_NO_GO`):

- **Tiêu chí `0_preconditions`:** Corpus đúng cấu trúc `45 SERVE + 5/5/5 REFUSE`; lượt chạy hoàn tất (`completed = true`, `run_status = "COMPLETE"`, `paired_live_evaluation_complete = "YES"`, `stop_reason = null`, đủ `60` cặp hoàn chỉnh khớp chính xác tập ID của corpus).
- **Tiêu chí `1_no_wrong_served` (An toàn tối thượng):** `HYBRID` có **`0` ca `wrong_served` quan sát được** trên toàn bộ 60 đề (cả 45 đề khả giải lẫn 15 đề âm tính) và `wrong_served_only_HYBRID == 0`.
- **Tiêu chí `2_served_correct_non_inferior`:** Trên 45 đề `SERVE`, kiểm định exact McNemar hai phía không nghiêng có ý nghĩa thống kê về phía `LLM_ONLY` ở mức $\alpha = 0.05$, **và** hiệu tỉ lệ $\text{rate}_{\text{HYBRID}} - \text{rate}_{\text{LLM\_ONLY}} \ge -5\text{ pp}$ (trên 45 bài, `HYBRID` không được kém `LLM_ONLY` quá `2` bài).
- **Tiêu chí `3_refusal`:** `HYBRID` từ chối **100%** các bài `expect = REFUSE` (trừ lỗi hạ tầng được tách riêng) và có tỉ lệ đúng lớp lý do từ chối (`refusal_reason_accuracy`) $\ge$ `LLM_ONLY`.
- **Tiêu chí `4_latency`:** Độ trễ trung vị (median) cấp bài toán của `HYBRID` $\le$ `LLM_ONLY`, **và** phân vị `p90` của `HYBRID` $\le 1.5 \times \text{p90}_{\text{LLM\_ONLY}}$.
- **Tiêu chí `5_cost` (Bảo thủ nghiêng về NO-GO):** Chi phí USD trên mỗi bài phục vụ đúng của `HYBRID` tính theo **cận trên (`usd_charged_total`)** phải $\le$ chi phí tương ứng của `LLM_ONLY` tính theo **cận dưới (`usd_reported_total`)**.
- **Tiêu chí `6_reliability`:** Lỗi kỹ thuật/hạ tầng (`technical_failures`) $\le 5\%$ mỗi arm (tối đa `3 / 60` đề) và `scorer_errors == 0`.
- **Tiêu chí `7_independence`:** File phê duyệt của Owner xác nhận `corpus_author` khác rỗng và cả `authoring_independence` lẫn `evaluator_independence` đều bằng `"ESTABLISHED"`.

### 4.3. Kế hoạch phân tích thống kê bắt cặp & Phân định 4 mức diễn giải (§VI.2 & §VIII)

1. **Ma trận kết quả bắt cặp trên cùng `case_id` (`N = 45` cho `served_correct`, `N = 60` cho `wrong_served`):**
   - Xuất đầy đủ: cả hai cùng đúng ($n_{11}$), chỉ `HYBRID` đúng ($n_{10}$), chỉ `LLM_ONLY` đúng ($n_{01}$), cả hai cùng sai ($n_{00}$), các trường hợp từ chối của từng bên, lỗi an toàn từng arm, khoảng tin cậy **Wilson 95%** đơn nhánh, hiệu bắt cặp $\Delta = (n_{10} - n_{01}) / N$ kèm khoảng tin cậy 95% và trị số $p$ **exact McNemar hai phía**.
2. **Phân biệt rạch ròi 4 khái niệm diễn giải (bắt buộc tuân thủ trong báo cáo cuối):**
   - **Operational acceptance (Nghiệm thu vận hành):** Có vượt qua đồng thời cả 8 cổng đã khóa của Hợp đồng §7 trên mẫu `H-1` hay không (`HYBRID_CUTOVER_GO` vs `HYBRID_CUTOVER_NO_GO`).
   - **Statistical significance (Ý nghĩa thống kê):** Trị số $p < 0.05$ của kiểm định McNemar chỉ kiểm định giả thuyết bác bỏ bằng nhau trên cặp bất đồng $(n_{10}, n_{01})$. **Tuyệt đối không gọi một kết quả McNemar không có ý nghĩa thống kê ($p \ge 0.05$) là bằng chứng chứng minh hai hệ thống tương đương.**
   - **Evidence of non-inferiority (Bằng chứng không kém hơn):** Đánh giá dựa trên biên độ hiệu tỉ lệ bắt cặp $\Delta$ và cận dưới khoảng tin cậy so với ngưỡng biên $-5\text{ pp}$ đã đăng ký trước.
   - **Generalization claims (Phạm vi tổng quát hóa):** Với $N = 60$ bài và `0` lỗi `wrong_served`, khoảng tin cậy Wilson 95% là $[0.0\%, 6.02\%]$ — **tuyệt đối không kết luận hệ thống có `0%` lỗi thực tế chỉ vì quan sát `0/60` lỗi trên mẫu**, và không ngoại suy sang các lớp hình học nằm ngoài phân bố lấy mẫu của `H-1`.

### 4.4. Ranh Giới Hợp Đồng `Scene3D` & Chất Lượng Sư Phạm (C28 §IX)

- Trên mọi dòng `SERVED` của cả hai nhánh `LLM_ONLY` và `HYBRID`, hàm `audit_scene_contract()` trong [`run_paired_route_evaluation.py`](../../../../../backend/scripts/run_paired_route_evaluation.py) kiểm tra tự động 6 bất biến hợp đồng backend mà không sửa `frontend/**`: `envelope_valid`, `object_identity_unique`, `dependency_order_valid`, `section_object_valid`, `explanation_certificate_linked`, và `target_quantity_mapped`.
- **Ranh giới sư phạm bắt buộc khai báo rõ:** `H-1` chỉ gồm các bài có đại lượng định lượng (loại trừ bài chỉ dựng hình và bài chứng minh). Do đó, việc vượt qua kiểm tra `scene_contract` và đúng đáp số toán học **không chứng minh chất lượng sư phạm đã được kiểm chứng** (`pedagogical_human_validation = "NOT_EVALUATED_BY_H1_AUTOMATED_HARNESS"` — không thay thế đánh giá của giáo viên/học sinh về tính mạch lạc của lời dẫn dựng hình).

---

## 5. Quy Tắc Quy Kết Lỗi Sau Đánh Giá & Chống Nhiễm Tập Độc Lập

Sau khi niêm phong kết quả chạy `H-1`, mọi ca không đạt của `HYBRID` bắt buộc được phân loại vào đúng **1 trong 11 nhãn quy kết đã khóa**:

1. `EXTRACTION_FAILURE` — Gemini trích xuất sai cấu trúc/dữ kiện/mục tiêu/quote hoặc vi phạm schema `TypedFactNextPayloadV2`.
2. `SOURCE_GATE_FAILURE` — Trích xuất hợp lý nhưng văn phạm đóng của Source Gate từ chối quá chặt (`UNGROUNDED_VALUE`, `SOURCE_OBJECT_MISMATCH`, …) được kiểm chứng bằng gold replay của chính ca đó.
3. `FACT_GRAPH_FAILURE` — Lỗi gộp quan hệ, canonical identity hoặc suy diễn tương thích trong FactGraph/Bridge.
4. `PLANNER_FAILURE` — Đã qua Source Gate và đủ primitives trong Registry nhưng Planner (`/26`) không lập được kế hoạch. *(Lưu ý: tuyệt đối không tuyên bố `GENUINE_DISCOVERY` chỉ từ `REGISTERED_DECOMPOSITION`).*
5. `REGISTRY_COVERAGE_GAP` — Bài toán thuộc phạm vi công bố nhưng thiếu hàm dựng/đo trong `geometry-functions/32`.
6. `KERNEL_FAILURE` — Lỗi tính toán đại số chính xác, miền căn thức (`EXACT_DOMAIN_EXCEEDED`), hoặc lỗi kiểm chứng chứng chỉ trong Engine (`/24`).
7. `ADAPTER_FAILURE` — Lỗi ánh xạ kết quả/chứng chỉ sang `scene3d` hoặc envelope của Adapter `/4`.
8. `PROVIDER_FAILURE` — Lỗi HTTP `429`/`5xx`, timeout, hoặc response rỗng từ phía nhà cung cấp Gemini sau khi đã retry.
9. `EXPECTED_REFUSAL` — Từ chối/hỏi làm rõ đúng kỳ vọng trên 15 bài âm tính.
10. `EVALUATION_ORACLE_ISSUE` — Sai sót chứng minh được bằng toán học trong đáp án chuẩn ban đầu (chỉ được ghi vào phụ lục đính chính độc lập, **tuyệt đối không sửa file corpus/gold gốc để làm đẹp điểm Hybrid**).
11. `UNKNOWN` — Không đủ thông tin phân định nhân quả.

**Quy tắc đốt cháy tập kiểm định mù (One-Time Blindness Rule):**
- Nếu kết quả `H-1` dẫn tới bất kỳ chỉnh sửa nào trên mã sản phẩm (`backend/app/**`), `H-1` lập tức chuyển trạng thái sang **tập hồi quy phát triển đã mở (`POST_EVALUATION_DEVELOPMENT_REGRESSION`)** và **không được dùng lại `H-1` để tuyên bố tổng quát hóa mù cho candidate mới**. Khi đó bắt buộc phải có vòng đề độc lập kế tiếp (`H-2`) theo đúng giao thức này.
