# AXO HYBRID /12 — Báo Cáo Tổng Kết Chiến Dịch

- **Run ID:** `axo-hybrid-compositional-geometry-language-grounded-simulation`
- **Branch:** `feat/compositional-geometry-grounding` (không merge `main`, không push, bảo toàn cây sạch)
- **Frozen Product Candidate:** `4f4162d87f8f77388d21c8065f4b0bfd67cb648c` (`measured_system.tree_hash = f3c185a08bf0f227fafc6621195017f3517d7227b20b93c7fdf86278103df40d`, `124` file, `CACHE_VERSION = "147"`, `ROUTE_D_CACHE_POLICY = "147:route-d"`, `HYBRID_ROUTE_MODE = "live"` mặc định giữ nguyên).
- **Trạng thái A4:** `planner.py`, `engine.py`, `typed_fact_next.py`, `adapter4_route.py`, `scene3d.py`, `backend/experimental/construction_planner/`, `tokens.css`, `transition-semantics.test.ts` đều **`0` diff** từ gốc nhánh tới `HEAD`; `registry.py` giữ `geometry-functions/33` và **`0` import từ `app.ai`**.

---

## 1. Tóm tắt Kết quả Chính (`Single-Shot Blind Live Acceptance`)

Chạy một lượt duy nhất trên tập preregistered `V12_ACCEPTANCE_MANIFEST.json` (`sha256 = f2fabd0b43fbe1d2cab1c1eeecdd2e143bf162cdd825b75b44bf209e38f13a86`: `105` in-scope + `6` bất định `VD01..VD06` + `28` phủ định `VN01..VN28`) bằng trình duyệt thật Playwright Chromium + `vite preview` + `uvicorn` (`HYBRID_ROUTE_MODE=local-only-scoped`, `ALLOW_LIVE_AI=0`, `GEMINI_API_KEY` rỗng) + `Qwen3-0.6B-AxoV9-Q4_K_M`:

1. **`SIMULATION_COMPLETION_RATE_in_scope = 88 / 105 = 0.8381` (`83.81%`):** Tăng **`+17.91 pp`** so với `/11` (`56/85 = 0.659`) và **`+21.31 pp`** so với `/10` (`40/64 = 0.625`), sát dưới ngưỡng preregistered `0.85` đúng `2` ca (`-1.19 pp`). Tuyệt đối không chỉnh mã hay chạy lại để ép đạt `0.85`.
2. **`SLM_VERIFIED_SCENE_RATE = 17 / 32 = 0.5312` (`53.12%`):** Trên tầng `SLM_REQUIRED` của ứng viên (`32` ca mà parser tất định `local-geometry-parser/3` kể cả qua normalizer `v3` vẫn chưa tự đọc hết), mô hình cục bộ `AxoV9` chạy sống không cache đã giải và kiểm chứng đầu-cuối thành công **`17` ca** (`>= 5` và `>= 0.30`, tăng mạnh từ `0/20` ở `/10` và `4/30 = 0.133` ở `/11`), kèm `15/26` `preregistered_slm_targets` trong tầng SLM; đồng thời tầng tất định đóng góp riêng **`39` ca** nâng cấp từ P2 baseline (`34 -> 73 PARSER_COMPLETE`).
3. **An toàn Toán học & Không bịa (`0` vi phạm):**
   - Oracle độc lập (`tools/scene_oracle.py`, `Fraction` + Gram `chart_metric`): **`88/88 MATHEMATICALLY_VALID`**, `0 MATHEMATICALLY_INVALID`, `0 VALIDATION_ERROR`.
   - **`wrong_served = 0`**, **`grounding_violations_served = 0`**, **`unverified_relations_served = 0`**, **`fabricated_numeric_goals = 0`**, **`served_numeric_mismatch = 0`**.
   - **Safe refusal:** **`28/28 = 1.0`** (`22 REFUSED` + `6 gate_out_of_scope`).
4. **Hiển thị Ban đầu `Scene3D` (`V11-VIS-1`) & Tương tác:**
   - Trước khi người dùng xoay/reset: **`88/88 = 1.0`** cảnh sống thỏa mãn `ink >= 1%` (`min = 0.80349`), **`0`** nhãn tràn biên canvas, **`0`** đỉnh ngoài NDC, **`0`** lỗi console, **`0`** cảnh cũ đọng khi đổi đề.
   - Tương tác từng cảnh (orbit drag, zoom wheel, bước dựng trước/sau, đặt lại góc nhìn): **`88/88 = 1.0`** (`0` request `/api/analyze` phát sinh).
   - Kịch bản UI (`v12_ui_scenarios.mjs`): **`9/10` PASS** (`I01, I02, I03, I04, I07` và `I08` trên 4 viewport `1920x1080`, `1366x768`, `768x1024`, `390x844` PASS; `I05` lấy `VD01` nên hiển thị thông báo `§17 capability_gap` thay cho câu hỏi làm rõ).
5. **Cô lập Mạng & Hiệu năng (trên Windows dev host `15.78 GiB`):**
   - `external_ai_calls = 0`, `gemini_invocations = 0`, `silent_cloud_fallbacks = 0`, `browser_external_requests = 0`, proxy `18999` (`selfcheck = 2`, `stack = 0`), `netstat` (`763` heartbeats, `0` non-loopback).
   - Uncached live: `deterministic` (`n=71`) `p50/p95 = 152.0 / 413.0 ms`; `live SLM` (`n=17`) `p50/p95 = 4,511.0 / 6,703.0 ms`; peak WS: `llama 914.4 MiB`, `chromium 626.2 MiB`, `backend 126.6 MiB`.

---

## 2. Kết luận Nghiệm thu Chiến dịch (`/12`)

- **`GROUNDED_SLM_RECOVERY_VERIFIED = TRUE`** (`17/32 = 0.5312 >= 0.30` và `>= 5` cảnh `LOCAL_SLM_GROUNDED` sống hợp lệ)
- **`VISUAL_INITIAL_FRAMING_VERIFIED = TRUE`** (`88/88 = 1.0` trước orbit/reset, `V11-VIS-1` đóng hoàn toàn)
- **`SAFETY_AND_NETWORK_ISOLATION_VERIFIED = TRUE`** (`0` wrong-served, `28/28` refusals, `0` external calls)
- **`LIVE_SIMULATION_ACCEPTED = FALSE`** (`0.8381 < 0.85` — gần ngưỡng, thiếu `2` ca trong `17` ca dừng bảo thủ đã phân loại ở [`RESIDUAL_GAPS_AND_HANDOFF_ROADMAP.md`](RESIDUAL_GAPS_AND_HANDOFF_ROADMAP.md))
- **`SCOPED_CUTOVER_COMPLETED = FALSE`** (`HYBRID_ROUTE_MODE = "live"` mặc định giữ nguyên)
- **`NOT_MEASURED`:** `EXTERNAL_INDEPENDENCE`, `INDEPENDENT_H1_VALIDATION`, `PHYSICAL_TARGET_HARDWARE_4_8_GIB`, `GEMINI_PARITY`, `REAL_STUDENT_USABILITY`.
- **Full T3 Gate:** `PENDING_STEP7_T3_EXECUTION` (sẽ cập nhật ngay sau khi chạy `npm run test:full` tại Step 7.4).

---

## 3. Liên kết Hiện vật Chính

- Preregistration & Freeze: [`V12_ACCEPTANCE_MANIFEST.json`](V12_ACCEPTANCE_MANIFEST.json) · [`V12_ACCEPTANCE_CRITERIA.json`](V12_ACCEPTANCE_CRITERIA.json) · [`V12_EVALUATION_FREEZE.json`](V12_EVALUATION_FREEZE.json) · [`V12_CANDIDATE_FREEZE.json`](V12_CANDIDATE_FREEZE.json)
- Kỹ thuật & Cache: [`COMPOSITIONAL_GEOMETRY_LANGUAGE_DESIGN.md`](COMPOSITIONAL_GEOMETRY_LANGUAGE_DESIGN.md) · [`DIACRITIC_FREE_DOMAIN_EVALUATION.json`](DIACRITIC_FREE_DOMAIN_EVALUATION.json) · [`GROUNDED_SOURCE_GATE_REVALIDATION.md`](GROUNDED_SOURCE_GATE_REVALIDATION.md) · [`CACHE_IDENTITY_DECISION.md`](CACHE_IDENTITY_DECISION.md)
- Nghiệm thu Live & Báo cáo: [`LIVE_ACCEPTANCE_RESULTS.json`](LIVE_ACCEPTANCE_RESULTS.json) · [`SCENE_ORACLE_VERIFICATION.json`](SCENE_ORACLE_VERIFICATION.json) · [`SLM_LIVE_CONTRIBUTION_AUDIT.json`](SLM_LIVE_CONTRIBUTION_AUDIT.json) · [`VISUAL_AND_INTERACTION_ACCEPTANCE.json`](VISUAL_AND_INTERACTION_ACCEPTANCE.json) · [`PERFORMANCE_AND_RESOURCE_REPORT.json`](PERFORMANCE_AND_RESOURCE_REPORT.json) · [`NETWORK_ISOLATION_PROOF.json`](NETWORK_ISOLATION_PROOF.json) · [`ABLATION_AND_GENERALIZATION_REPORT.md`](ABLATION_AND_GENERALIZATION_REPORT.md) · [`RESIDUAL_GAPS_AND_HANDOFF_ROADMAP.md`](RESIDUAL_GAPS_AND_HANDOFF_ROADMAP.md) · [`THESIS_EVIDENCE_SUMMARY.md`](THESIS_EVIDENCE_SUMMARY.md)
- Handoff Khóa (`A4`): [`SIMULATION_GOAL_SEMANTICS_REPORT.md`](SIMULATION_GOAL_SEMANTICS_REPORT.md) · [`DERIVED_OBJECT_PROVENANCE_HANDOFF.md`](DERIVED_OBJECT_PROVENANCE_HANDOFF.md) · [`handoff/derived_point_o_provenance.patch`](handoff/derived_point_o_provenance.patch)
