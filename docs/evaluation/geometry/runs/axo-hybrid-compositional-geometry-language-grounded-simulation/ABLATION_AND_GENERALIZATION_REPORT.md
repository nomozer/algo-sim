# AXO HYBRID /12 — Ablation & Generalization Report

## 1. Cross-Campaign Progress (`/10` → `/11` → `/12`, Single-Shot Offline Browser Acceptance)

| Metric | AXO HYBRID /10 | AXO HYBRID /11 | AXO HYBRID /12 | Target (`/12`) | Status (`/12`) |
| --- | --- | --- | --- | --- | --- |
| In-scope completion rate | `40/64 = 0.625` | `56/85 = 0.659` | **`88/105 = 0.8381`** (`+17.91 pp` vs `/11`) | `>= 0.85` | `NEAR_THRESHOLD` (`-2` cases / `-1.19 pp`) |
| `SLM_VERIFIED_SCENE_RATE` (candidate `SLM_REQUIRED`) | `0/20 = 0.000` | `4/30 = 0.133` | **`17/32 = 0.5312`** (`17 >= 5`) | `>= 0.30` & `>= 5` | **PASS** |
| Exact Oracle (`scene_oracle.py`) | `40/40 (1.0)` | `58/58 (1.0)` | **`88/88 (1.0)`** (`0` invalid/error) | `0` invalid | **PASS** |
| Safety (`wrong_served`, `grounding_violations`, `unverified_relations`, `fabricated_numeric_goals`, `served_numeric_mismatch`) | `0` | `0` | **`0` / `0` / `0` / `0` / `0`** | `0` | **PASS** |
| Safe refusal rate (negative cases) | `18/18 (1.0)` | `24/24 (1.0)` | **`28/28 (1.0)`** | `1.0` | **PASS** |
| Initial render framing & visual check (`V11-VIS-1`) | N/A | Initial clip on `S07`, `Q01` | **`88/88 (1.0)`** (`min_ink = 0.80349`, `0` clipped) | `1.0` | **PASS** |
| Per-scene interactive checks (orbit/zoom/step/reset) | `159/160` | `232/232` | **`88/88 (1.0)`** (`0` extra `/api/analyze`) | `1.0` | **PASS** |
| Registered UI scenarios (`v12_ui_scenarios.mjs`) | — | `7/8` | `9/10` (`I05` hit `VD01` §17 card) | `1.0` | `PARTIAL` (`9/10`) |
| External AI calls / Gemini / browser leaks | `0` | `0` | **`0`** (`tcp non_loopback = 0`) | `0` | **PASS** |

---

## 2. Deterministic vs. Live Model (`AxoV9`) Provenance Separation

Theo quy tắc preregistration tại `V12_ACCEPTANCE_CRITERIA.json`, đóng góp của thành phần tất định được tách bạch hoàn toàn khỏi đóng góp sống của `Qwen3-0.6B-AxoV9-Q4_K_M` (`V12_EVALUATION_FREEZE.json` vs `V12_CANDIDATE_FREEZE.json`, cùng trên `105` ca in-scope của `V12_ACCEPTANCE_MANIFEST.json`, `sha256 = f2fabd0b43fbe1d2cab1c1eeecdd2e143bf162cdd825b75b44bf209e38f13a86`):

1. **Tác động của tầng tất định (`DETERMINISTIC_ONLY` — Parser `/3`, `compositional-clause-analyzer/1`, Source Gate `/33`, `domain_profile.py`):**
   - P2 baseline (`V12_EVALUATION_FREEZE.json`, trước mọi code `/12`): `PARSER_COMPLETE = 34`, `SLM_REQUIRED = 71`.
   - Candidate `/12` (`V12_CANDIDATE_FREEZE.json`): `PARSER_COMPLETE = 73`, `SLM_REQUIRED = 32`.
   - Tổng số ca chuyển từ P2 `SLM_REQUIRED` sang `PARSER_COMPLETE` và hoàn tất đầu-cuối dưới route tất định là **`39` ca `DETERMINISTIC_ONLY`** (`V001, V005, V007, V009, V011, V012, V014..V017, V020, V022, V023, V028, V037..V039, V042..V044, V046, V048..V055, V061, V069, V073, V074, V092, V099, V100, V102, V103, V105`).
   - Trên tập `PARSER_COMPLETE` (`73` ca), `71/73` (`97.26%`) hoàn tất thành công (`1` `CONDITIONAL_CLAUSE` `V008`, `1` `BRIDGE_UNSUPPORTED_MEASUREMENT` `V072`).

2. **Tác động sống của Local SLM (`LOCAL_SLM_GROUNDED` — `local-slm-extractor/6`, `slm-grounding-validator/6`):**
   - Trong **`32` ca `SLM_REQUIRED`** của candidate (tức các đề mà `local-geometry-parser/3` cả thô lẫn sau `slm-verified-normalizer/3` vẫn không đạt `LOCAL_PARSE_COMPLETE`), mô hình cục bộ `Qwen3-0.6B-AxoV9-Q4_K_M` chạy sống hoàn toàn không cache/không replay đã giải và kiểm chứng đầu-cuối thành công **`17/32 = 53.12%`**:
     `V002, V019, V024, V025, V026, V034, V035, V057, V058, V059, V060, V063, V064, V065, V066, V086, V087`.
   - `normalizer_or_det_rescued_within_candidate_slm_required = []` (`0` ca trong 32 ca `SLM_REQUIRED` chạy qua đường fallback tất định).
   - Trên **`33` `preregistered_slm_targets`**: `22/33` hoàn tất cuối cùng (`7` nhờ mở rộng parser + `15` trong `26` ca còn nằm trong `SLM_REQUIRED` được `LOCAL_SLM_GROUNDED` giải sống).

---

## 3. Component Evidence Across `/12` Phases (`P3`–`P7`)

1. **`compositional-clause-analyzer/1` (`CLAUSE_SEGMENTATION_EVALUATION.json`, `SOURCE_SPAN_PROVENANCE_AUDIT.json`):** `114` ca dev `/11`, `0` lỗi lệch offset nguyên văn qua `242` mệnh đề, nhận diện `39/39` `SIMULATE_ONLY`, `15/16` `SIMULATE_AND_QUERY`.
2. **Diacritic-free Domain Gate (`DIACRITIC_FREE_DOMAIN_EVALUATION.json`):** Word-boundary ASCII geometry detector + decoy veto đạt `8/8` TP in-domain và `0/12` FP out-of-domain trên tập phát triển, bảo toàn `test_s1_diacritic_free_offline` (`0` rò rỉ), giúp các đề không dấu hợp lệ trong `V12` đi tiếp thay vì bị `GATE_OUT_OF_SCOPE` trong khi `6` ca ngoại miền trong `VN*` vẫn bị `gate_out_of_scope` chặn sạch.
3. **Dev Failure Recovery & Synthetic Phrasing Ablation (`NESTED_DECLARATION_PARSER_RESULTS.json`, `V12_SLM_CONTRIBUTION_ABLATION.json`):** `28/29` ca non-D dev của `/11` phục hồi qua `DETERMINISTIC_ONLY` + `1/1` (`S17`) qua `SLM_CONTRIBUTED` (`29/29 = 100%`, `D01..D05` bất biến); trên 8 ca probe diễn đạt gián tiếp nhân tạo (`SLM_DIRECT_INDIRECT_PHRASING_PROBE`), SLM giải grounded `5/8` (`SYN_SLM_01, 05, 06, 07, 08`).
4. **Initial Camera Framing `V11-VIS-1` (`SCENE3D_CAMERA_FRAMING_REPORT.md`):** Sửa bù dịch ống kính `setViewOffset` (`dichTamNgang`, `dichTamDoc`) trong `tinhVungAnToanKhungNhin` và kẹp nhãn theo biên canvas trong `tinhViTriNhanDiem` đưa tỷ lệ khớp khung ban đầu trên toàn bộ `88` cảnh sống của `V12` lên **`1.0` (`88/88`)** và `12/12` ma trận `4` viewport (`S07, Q01, S09_ELONGATED`).

---

## 4. Boundaries & Non-Claims

- **`EXTERNAL_INDEPENDENCE = NOT_MEASURED`** (tập `V12` do tác giả thiết kế; kho `H-1` độc lập bên ngoài chưa mở/chưa đo).
- **`PHYSICAL_TARGET_HARDWARE = NOT_MEASURED`**, **`GEMINI_PARITY = NOT_MEASURED`**, **`REAL_STUDENT_USABILITY = NOT_MEASURED`**.
- Kết quả hiệu năng (`PERFORMANCE_AND_RESOURCE_REPORT.json`) chỉ áp dụng cho máy dev Windows 11 (`det p50/p95 = 152.0 / 413.0 ms`; `live SLM p50/p95 = 4,511.0 / 6,703.0 ms`; peak WS `llama 914.4 MiB`, `chromium 626.2 MiB`, `backend 126.6 MiB`), không ngoại suy sang máy yếu `4–8 GiB`.
