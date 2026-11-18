# AXO HYBRID /7 — Full Regression, SLM Pytest & 14 Adversarial/Fault Report

- **Generated (UTC):** `2026-11-18T16:55:53.852844+00:00`
- **External AI Calls:** `0` (`ALLOW_LIVE_AI=0`, `GEMINI_API_KEY=""`)
- **Runtime / Cache Namespace:** `local-slm-runtime/3` / `HYBRID_V7_LOCAL_SLM`
- **Scene3D Continuity Errors:** Config A `0` · Config C `0` · Config D `0`
- **New Mode-A Leaks Above Deterministic v145:** Config C `0` · Config D `0`
- **Baseline Regressions vs Deterministic v145:** `0`
- **4 SLM Pytest Modules:** `23 passed, 1 warning in 48.12s` (`exit_code=0`, `49.11s`)
- **14 Adversarial & Fault Checks (Original + Fine-Tuned GGUF):** `14/14` (`all_passed=True`)

## 1. Baseline Suites (`Config A v145` vs `Config C v7+Orig` vs `Config D v7+AxoV7`)

| Suite | Config A (`det_v145`) | Config C (`v7 + Orig Q4_K_M`) | Config D (`v7 + AxoV7 Q4_K_M`) | Notes |
| --- | --- | --- | --- | --- |
| `REAL27_TEXT` (`27`) | `21/27` (`0` wrong) | `21/27` (`0` wrong, `slm=4`) | `21/27` (`0` wrong, `slm=4`) | Full end-to-end |
| `REAL27_IMAGES` (`27`) | `21/27` | `21/27` (`slm=4`) | `21/27` (`slm=4`) | Post-OCR confirmed texts |
| `NC_GOLD` (`21`) | `21/21` | `21/21` | `21/21` | Same Kernel route |
| `NC_NL` (`21`) | `21/21` | `21/21` (`+0`) | `21/21` (`+0`) | `0` regressions |
| `AUTONOMOUS_NEGATIVES` (`11`) | `11/11` refused | `11/11` refused | `11/11` refused | `false_served=0` |
| `RM72` (`62+` / `10-`) | `61/62+`, `10/10-` | `61/62+`, `10/10-` | `61/62+`, `10/10-` | `false_served=0` |
| `DEV37` (`37`) | `30/30+`, `7/7-` | `30/30+`, `7/7-` (`slm=4`) | `30/30+`, `7/7-` (`slm=4`) | Delta C `+0` · D `+0` |
| `PROBES39` (`26+` / `13-`) | `23/26+`, `13/13-` | `23/26+`, `13/13-` (`slm=10`) | `23/26+`, `13/13-` (`slm=10`) | Delta C `+0` · D `+0` |
| `S2_36` (`18+` / `18-`) | `16/18+`, `18/18-` | `16/18+`, `18/18-` (`slm=0`) | `16/18+`, `18/18-` (`slm=0`) | Delta C `+0` · D `+0` |
| `COMP112` (`66+` / `46-`) | `66/66+`, `44/46-` | `66/66+`, `44/46-` (`slm=19`) | `66/66+`, `44/46-` (`slm=19`) | Dual reporting (`0` new leaks) |
| `frozen_unseen_vmmu20` (`20`) | Separate | `0/20` unverified (`slm=0`) | `0/20` unverified (`slm=0`) | **`GROUND_TRUTH_UNVERIFIED`** (excluded) |

### COMP112 Dual Reporting Note

- Strict frozen labels (`dp_reflection` & `dp_projection_unnamed_image` kept negative): Config C `66/66 pos + 44/46 neg` · Config D `66/66 pos + 44/46 neg`.
- New Mode-A leaks above `Config A` (`slm_invoked=false` on both historical items for Configs A/C/D): Config C `0` · Config D `0`.

## 2. 4-Module SLM Pytest Suite

- Command: `pytest -c backend/pytest.ini backend/tests/geometry/test_local_slm_understanding.py backend/tests/geometry/test_slm_compact_extraction.py backend/tests/geometry/test_slm_language_closure.py backend/tests/geometry/test_slm_finetuned_runtime.py -q`
- Result: `23 passed, 1 warning in 48.12s` (`passed=True`, `duration=49.11s`)

## 3. 14 Section-16 Adversarial & Runtime Fault Checks (Both Original & Fine-Tuned GGUF)

| Check | Passed |
| --- | --- |
| `1_universal_quantifier_ambiguity` | `True` |
| `2_wrong_lateral_edge_scope` | `True` |
| `3_conditional_to_fact_injection` | `True` |
| `4_negated_perpendicular_relation` | `True` |
| `5_missing_dimensions` | `True` |
| `6_conflicting_geometric_constraints` | `True` |
| `7_wrong_quantity_mapping` | `True` |
| `8_wrong_edge_plane_binding` | `True` |
| `9_invented_vertices` | `True` |
| `10_prompt_injection_en_and_vi` | `True` |
| `11_invalid_json_typo_and_curved` | `True` |
| `12_model_timeout_and_bounded_queue` | `True` |
| `13_model_crash_and_missing_model` | `True` |
| `14_model_checksum_mismatch_and_no_cloud_fallback` | `True` |
