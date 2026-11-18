# AXO HYBRID /8 — SOURCE GATE OWNER STATUS & SECURITY REGRESSION REPORT (Phase P5 / Gate D5)

- **Ownership Status:** **`BLOCKED_OWNERSHIP`**
- **Scope Verified Read-Only:** `backend/app/simulation/geometry_functions/registry.py` (`Registry /33`, `kiem_nguon`, `_lien_ket_cau`, `_C_VAI`, `_C_MAT`, `_C_CHIEU`, `construction_source_bound`), `planner.py`, `engine.py`, `adapter4_route.py` were inspected read-only and **NEVER modified** (`0` edits to `backend/app/**`).
- **Security & Boundary Test Suite:** [`test_source_gate_handoff_boundaries.py`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/tests/geometry/test_source_gate_handoff_boundaries.py) (`8 passed in 5.39s`).
- **Gate D5 Status:** `BLOCKED_OWNERSHIP` (handoff verified, reproducible tests green, zero unauthorized edits, zero security regressions).

---

## 1. Review of All 10 `/8 §12` Source Gate Audit Regions

| Region (`registry.py`) | Current Native Behavior (`local-slm` OFF / Raw Text) | Upstream `/7` Bridge (`local-slm` ONLY) | Safety & Compatibility Assessment | Ownership Status |
|---|---|---|---|---|
| 1. `_C_VAI` (`L1778`) & Universal Quantifiers | Matches `(các\|mọi\|mỗi)` + `(= \| bằng \| là)`. Rejects `"tất cả các cạnh bên"` and verb `"dài"` (`"mọi cạnh bên dài 2a√2"`) with `UNGROUNDED_VALUE`. | `VN05_MOI_CANH_BEN` (`slm-verified-normalizer/2`) rewrites universal plural quantifiers into canonical `"bằng"`; plural quantifier preserved, singular rejected. | **No loss of ambiguity safety:** singular `"cạnh bên dài 2a"` and `"một cạnh bên bằng 2a"` still refused (`AMBIGUOUS_FACT`). | `BLOCKED_OWNERSHIP` (documented in [`SOURCE_GATE_OWNER_HANDOFF.md`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/deterministic-geometry-language-closure-slm-finetuning/SOURCE_GATE_OWNER_HANDOFF.md)) |
| 2. `_C_MAT` (`L1929`) & Face-Plane Perpendicular Wording | Requires `(nằm trong mặt phẳng )?vuông góc với`; rejects elliptical `"nằm vuông góc với"`. | `VN05_NAM_VUONG_GOC_FACE` normalizes only for 3+-vertex faces (`Mặt bên MAB ... nằm vuông góc với`). | Must NEVER relax for 2-vertex segments or unlabelled faces; verified positive/negative. | `BLOCKED_OWNERSHIP` |
| 3. `_C_CHIEU` (`L1804`) & Combined Projection/Midpoint | Requires atomic separation between `"gọi I là trung điểm KL"` and `"hình chiếu của H lên (KLM) là I"`; rejects swapped `point`/`image` (`SOURCE_OBJECT_MISMATCH`). | `VN05_PROJ_MIDPOINT` atomizes merged projection-onto-midpoint wording; **cannot** rescue model argument swaps. | Proven faithfully active on `v7h_p5_09`: caught swapped `(R -> G)` projection with `SOURCE_OBJECT_MISMATCH`. | `BLOCKED_OWNERSHIP` (Gate working as designed) |
| 4. `_lien_ket_cau` & Reordered Sentences | Enforces strict subject continuity & base-type declaration (`doc_rang_buoc` checks every sentence's shape/role). | No special rule; **not** the bug behind `v7h_p8_01..05`. | Verified via [`test_source_gate_handoff_boundaries.py`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/tests/geometry/test_source_gate_handoff_boundaries.py): Gold `TypedFactNext /2` on `"Biết UVWX là hình chữ nhật ..."` **SERVES** through Source Gate without modifying `_lien_ket_cau`. | `NO_CHANGE_NEEDED` (Model omission bug, not Source Gate) |
| 5. `construction_source_bound` (`L8637`) | Verifies projection target plane (`_cung_mat` / `_cung_da_giac`), apex owner ambiguity check, and `"lần lượt"` ordered projections. | Audited read-only. | Correctly prevents out-of-order or ambiguous projection bindings. | `BLOCKED_OWNERSHIP` |
| 6. Conversational Prefixes (`"Thưa thầy..."`, `"Đề thi thử:"`) | Un-normalized prefixes can leave extraneous tokens unless sentence splitter separates cleanly; Gold `TypedFactNext` quotes skip greeting prefix. | `local-slm-extractor/3` strips conversational greetings (`VN` regex) — minor quirk spotted on `v7h_p8_01` (`"Thưa thầy,"` -> `"Cho"`). | `v7h_p8_06..10` with same 5 prefixes + Gold `v7h_p8_01..05` all SERVE through Source Gate. | `UPSTREAM_EXTRACTOR` (Live route optional greeting hygiene) |
| 7. Contrastive `"còn ... thì"` | Surface conditional detector flags literal `"thì"` unless normalized or whitelisted for non-conditional `"còn DD' thì có độ dài bằng"`. | `VN05_CON_THI` (`v2`) rewrites non-conditional contrastive `"còn ... thì"` while preserving genuine `"Nếu ... thì ..."`. | Verified safe: `"Nếu SA vuông góc (ABCD) thì SA=2a"` and `"Nếu cạnh bên AA'=3a thì ..."` still REFUSED (`CONDITIONAL_CLAUSE`). | `BLOCKED_OWNERSHIP` |

---

## 2. Live-Gemini Compatibility Impact & Security Verification (`VERIFIED`)

1. **Zero live-route side effects in `/8`:** Because `registry.py` was untouched and `slm-verified-normalizer/2` runs exclusively inside `HYBRID_ROUTE_MODE=local-slm`, the official production route (`HYBRID_ROUTE_MODE=live`) maintains bit-identical Source Gate behavior (`CACHE_VERSION = 145`).
2. **Adversarial Security Invariants Verified (`test_source_gate_handoff_boundaries.py`, `8 passed`):**
   - `test_native_source_gate_blocks_unnormalized_handoff_forms_read_only`: Confirms `_C_VAI`, `_C_MAT`, and `_C_CHIEU` still enforce strict native grammar when `slm-verified-normalizer/2` is absent, while `v2` normalization preserves exact meaning without bypassing Source Gate.
   - `test_reordered_rect_base_and_conversational_prefix_pass_gold_source_gate`: Proves `v7h_p8_01`'s `"Biết UVWX là hình chữ nhật"` + conversational prefix **SERVES** natively once extracted completely.
   - `test_source_gate_catches_swapped_projection_args_as_in_v7h_p5_09`: Proves `SOURCE_OBJECT_MISMATCH` blocks inverted projection arguments.
   - Five parameterized adversarial tests verify strict refusal (never short-circuiting on `EMPTY_SIMULATION_GOALS`):
     - **Zero conditional-to-premise conversion** (`Nếu SA vuông góc ... thì SA=2a` -> `CONDITIONAL_CLAUSE`),
     - **Zero negation loss** (`SA không vuông góc với (ABC)` -> `NEGATED_CLAUSE`),
     - **Zero invented dimensions** (`SA=3a` ungrounded quote -> `QUOTE_NOT_IN_SOURCE`),
     - **Zero ambiguous reference promotion** (`một cạnh bên bằng 2a` -> refused),
     - **Zero contrastive conditional bypass** (`Nếu cạnh bên AA'=3a thì ...` -> `CONDITIONAL_CLAUSE`).

## 3. Prerequisites Before Any Future Source Gate PR (`Owner Handoff`)

1. Explicit owner sign-off from the `Simulation / Registry /33` maintainer (never self-approved).
2. Applying only scoped plural/face/atomic-projection regex updates from `source-gate-handoff/1` after gating behind quantifier & vertex-arity checks.
3. Re-running full Source Gate security regressions (`C1–C3`), `S2_36`, `COMP112`, `AUTONOMOUS_NEGATIVES`, and a fresh Gemini live parity check (since native grammar changes affect `HYBRID_ROUTE_MODE=live`).
