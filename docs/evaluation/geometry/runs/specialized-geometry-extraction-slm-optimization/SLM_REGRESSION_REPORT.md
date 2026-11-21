# AXO HYBRID /6 — Baseline Regression & Fault Reliability Report

- **Generated (UTC):** `2026-11-17T17:13:59.774582+00:00`
- **External AI Calls:** `0` (`ALLOW_LIVE_AI=0`, `GEMINI_API_KEY=""`)
- **Scene3D Continuity Errors:** Config A `0` · Config C `0`
- **New Mode-A Leaks Above Deterministic v145:** `0`
- **Baseline Regressions vs Deterministic v145:** `0`
- **14 Fault / Adversarial Checks Passed:** `14/14` (`all_passed=True`)

## 1. Baseline Suites (`Config A v145` vs `Config C /6 compact_clause`)

| Suite | Config A (Det v145) | Config C (`/6 compact_clause`) | SLM Invoked | Notes |
| --- | --- | --- | ---: | --- |
| `REAL27_TEXT` (`27`) | `21/27` served (`0` wrong) | `21/27` served (`0` wrong) | `4` | Full end-to-end |
| `REAL27_IMAGES` (`27`, post-OCR) | `21/27` served | `21/27` served | `4` | Confirmed OCR text |
| `NC_GOLD` (`21`) | `21/21` | `21/21` | `0` | Same Kernel route |
| `NC_NL` (`21`) | `21/21` | `21/21` | `0` | Delta `+0` |
| `AUTONOMOUS_NEGATIVES` (`11`) | `11/11` refused | `11/11` refused | `0` | `false_served=0` |
| `RM72` (`62+` / `10-`) | `61/62+`, `10/10-` | `61/62+`, `10/10-` | `0` | `false_served=0` |
| `DEV37` (`37`) | `30/30` pos, `7/7` neg | `30/30` pos, `7/7` neg | `3` | Delta `+0` |
| `PROBES39` (`26+` / `13-`) | `23/26+`, `13/13-` | `23/26+`, `13/13-` | `10` | Delta `+0` |
| `S2_36` (`18+` / `18-`) | `16/18+`, `18/18-` | `16/18+`, `18/18-` | `0` | Delta `+0` |
| `COMP112` (`66+` / `46-`) | `66/66+`, `44/46-` | `66/66+`, `44/46-` | `19` | Dual reporting on `dp_reflection` & `dp_projection_unnamed_image` (`0` new leaks) |
| `frozen_unseen_vmmu20` (`20`) | Separate | `0/20` served (unverified) | `0` | **`GROUND_TRUTH_UNVERIFIED`** (excluded from accuracy denominators) |

### COMP112 Dual Reporting Note

Per `RULES.md`, frozen baseline labels on `COMP112` are never altered. On strict frozen labels both `Config A` and `Config C` score `66/66 pos + 44/46 neg`, where the two served historical negative-labeled items `dp_reflection` and `dp_projection_unnamed_image` both have `slm_invoked=false` (identical Deterministic Parser `v145` behavior) and `new_mode_a_leaks_above_config_a=0`.

## 2. 14 Fault-Tolerance & Adversarial Checks

| Check | Passed |
| --- | --- |
| `1_missing_model_fail_closed` | `True` |
| `2_crash_auto_recovery` | `True` |
| `3_timeout_kill_and_recovery` | `True` |
| `4_bounded_queue_busy` | `True` |
| `5_prompt_injection_en` | `True` |
| `6_prompt_injection_vi` | `True` |
| `7_typo_vuog_no_slm` | `True` |
| `8_typo_chop_no_slm` | `True` |
| `9_conditional_preserved` | `True` |
| `10_validator_invented_vertex` | `True` |
| `11_validator_goal_as_premise` | `True` |
| `12_live_negated_perp_refused` | `True` |
| `13_live_ambig_lateral_refused` | `True` |
| `14_live_curved_refused` | `True` |
