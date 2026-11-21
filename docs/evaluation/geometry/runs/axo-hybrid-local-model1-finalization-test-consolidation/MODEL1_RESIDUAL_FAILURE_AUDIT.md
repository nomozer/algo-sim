# AXO HYBRID /13 — Model 1 Residual Failure Audit (`/12` Regression Diagnostic)

> **Source corpus (exposed regression only):** `V12_ACCEPTANCE_MANIFEST.json` (`17` incomplete in-scope cases `V006..V104`, never used as blind holdout).
> **Audit command:** `diagnostics/residual_audit.py` with `ALLOW_LIVE_AI=0`, `GEMINI_API_KEY=""`, `LOCAL_SLM_MODEL=qwen3-0.6b-axo-v9-q4_k_m`.
> **Machine artifact:** [MODEL1_RESIDUAL_FAILURE_AUDIT.json](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/simulation-intent-slm-recovery/docs/evaluation/geometry/runs/axo-hybrid-local-model1-finalization-test-consolidation/MODEL1_RESIDUAL_FAILURE_AUDIT.json)

## 1. Summary (`15 / 17 SERVED`, `2 / 17 FAIL-CLOSED AT SOURCE GATE`)

| Group | Cases | Current Status | Notes |
|---|---|---|---|
| **Served & Oracle `MATHEMATICALLY_VALID`** (`13`) | `V006`, `V008`, `V027`, `V030`, `V031`, `V040`, `V047`, `V062`, `V067`, `V070`, `V088`, `V098`, `V104` | `SERVED` (`LOCAL_DETERMINISTIC_PARSER`) | Gold intervention (`CANONICAL`) also `13/13` `SERVED MATHEMATICALLY_VALID`. |
| **Served, Exact Math Differs From Pre-Existing `/12` Manifest Bug** (`2`) | `V029`, `V072` | `SERVED` (`LOCAL_DETERMINISTIC_PARSER`) | Frozen `/12` manifest untouched per evidence immutability rules:<br>• `V029`: `/12` text writes `góc NMP bằng 60°` (side `MN` diagonal `MP`, rhombus -> `∠NMQ = 120°`, `MN·MQ = -2`), whereas `/12` manifest `gold_relations` encodes `dot(MN, MQ) = 2` (`∠NMQ = 60°`, already documented in `residual_audit.py`).<br>• `V072`: `/12` text writes equilateral triangle `MNP` side `2` and lateral edge `MM' = 2√3` -> true area `√3` and volume `6`, whereas `/12` manifest `metric_oracle` encodes `[0.14433756729740643, 6.0]` (`√3/12`, `6.0`). Current engine serves `q2 = √3`, `q1 = 6`. |
| **SLM Routed & Refused Fail-Closed** (`2`) | `V032`, `V033` | `REFUSED` (`SOURCE_PREMISE_UNREAD`, `LOCAL_SLM_GROUNDED`) | `Qwen3-0.6B-AxoV9` omitted 1 clause/sub-op per item (`V032` omitted midpoint `I` of `LL'`; `V033` omitted `right_angle K`), so `Source Gate` refused safely without guessing. Note: `test_model1_residual_phrasings.py` covers `purpose_tail` and `voi_data` phrasings cleanly. |

## 2. General Fixes Landed in Phase 1

1. **`V008` (`registry.py` `_vai_tro_tai`):** Checked `_DIEU_KIEN` against full sentence `de[a:b]` (`m.end() <= p - a`) instead of truncated `de[a:p]`, preventing lookahead blindness on `muốn(?!\s+xem\b)` and `khi(?!\s+(?:đó|cắt|...))`.
2. **`V027` (`local_geometry_parser.py` `m_tet`):** Accepted optional `(?:(?:hình|khối)\s+)?` before `tứ diện`.
3. **`V029` (`engine.py` `_hinh_binh_hanh`):** Added exact rational double-angle solver for rhombus side–diagonal `vertex_angle` (`cos(2α) = 2cos²(α) - 1`, acute check enforced).
4. **`V067` (`local_geometry_parser.py` `_SIM_OBJECT`, `registry.py` `_VAT_MO_PHONG` & `_doc_yeu_cau_mo_phong`):** Supported named built segments/altitudes alongside solids in simulation requests, role-checked via `_vai_tro_doi_tuong_khop`.
5. **`V070` (`local_geometry_parser.py` `m_len_seg`, compound-goal quote handling):** Added `cạnh(?:\s+(?:bên|đáy))?` in length-goal extraction.
6. **`V072` (`typed_fact_next_bridge.py` `bridge_v2`, `local_geometry_parser.py` `m_poly_area` / `m_vol` / compound check):** Mapped polyhedral `measurement/area` (`{"polygon": ...}`) to `ask_area` and handled `"cùng"` conjunction cleanly.
