# Handoff — Hybrid V2 W3-F1 Cross-Sentence Plane Grounding (`HYBRID_V2_W3_F1_CROSS_SENTENCE_PLANE_GROUNDING`)

## 1. Status & Stop Point

- **Decision:** **`READY_FOR_OWNER_REVIEW`**
- **Task:** `HYBRID_V2_W3_F1_CROSS_SENTENCE_PLANE_GROUNDING`
- **Branch:** `research/hybrid-v2-w3-f1-cross-sentence-plane-grounding` (in `.superpowers/worktrees/w3-f1-cross-sentence-plane-grounding`)
- **Authoritative Baseline (`main = origin/main = remote`):** `e137623c4f674135a8d7884b78614c132eb78085`
- **Product Repair Commit:** `a609c4871a75426db52eb8b7a7be8ba3460fcf8c`
- **Frozen Full T3 Candidate:** `b02b2c422e4049dc6ff0a94996f335424e7b02b9`
- **Measured Product System:** `118` files, tree SHA-256 `918d3404ac60e81d62c75f6bfb7067ea25a4e27c197e3584075edef42e441f72` (`MATCH`)
- **Preserved Historical Holdout Wave 3 Worktree:** `.superpowers/worktrees/independent-section-holdout-wave3` (`0943f0ee6bd2a2b297827e39fa7c07054d716ea9`, clean and untouched)
- **Merge / Push / Cleanup Performed:** **NONE** (`main` not merged, nothing pushed, preserved worktrees kept).

---

## 2. Summary of Deliverables & Verification Gates

1. **Product Repair (`3` files in `backend/app/simulation/geometry_functions/`):**
   - `registry.py` (`REGISTRY_VERSION = "geometry-functions/20"`): Grounded Cross-Sentence Plane Reference Resolution in `mat_song_song_dung_nguon`, compound `section_and_area` request tails in `_het_dinh_nghia`, plane-first section phrase `_td_mat_truoc_khoi`, `đồng thời` / `cả hai` / `_DIEM_TRUOC_HAI_DUONG` bounded grammar, and global plane-name conflict rejection.
   - `planner.py` (`PLANNER_VERSION = "geometry-fact-planner/18"`): `plane_name` propagation into `k.derived_planes` for `MAT_SONG_SONG` and `MAT_VUONG_DUONG`, and `NOT_ASKED_IN_SOURCE` refusal when `"diện tích"` is absent from an `area` goal quote.
   - `typed_fact_next_bridge.py`: `plane_name` propagation + regex validation in `_mat_fact` and unique cross-sentence plane definition quote attachment in `_v2_plane_def_quotes`.
2. **Development & Adversarial Evaluation (`inputs/development.json`, `results/red-before.json`, `results/green-after.json`):**
   - `historical_w3_f1_pure_9`: `0/9` $\rightarrow$ **`9/9` (`100%`) `SERVED_CORRECT`** (`0` `SOURCE_OBJECT_MISMATCH`).
   - `w3_f1_isolated_24`: `0/24` $\rightarrow$ **`24/24` (`100%`) `SERVED_CORRECT`** (`18/18` `P-B`, `6/6` `P-A`, `0` `WRONG_SERVED`).
   - `authored_cross_sentence_positive_24`: `0/24` $\rightarrow$ **`24/24` (`100%`) `SERVED_CORRECT`** (`19/19` `P-B`, `5/5` `P-A`, `0` `WRONG_SERVED`).
   - `mandatory_negative_tamper_20`: **`20/20` (`100%`) refused**, **`20/20` exact expected code & category**, `0` `WRONG_SERVED`.
3. **Post-Feedback Development Regression on Locked Wave 3 (`results/wave3-post-feedback-regression.json`):**
   - Strictly classified as `POST_FEEDBACK_DEVELOPMENT_REGRESSION` (`not_an_independent_blind_holdout = true`).
   - Positive `SERVED_CORRECT`: `20/72` (`27.78%`) $\rightarrow$ **`29/72` (`40.28%`, `+9`)**; `section_and_area`: `0/24` $\rightarrow$ **`9/24` (`37.50%`)**.
   - Remaining `W3-F1` `SOURCE_OBJECT_MISMATCH`: `24/24` $\rightarrow$ **`0/24`**.
   - Negative refusals: **`72/72` (`100%`)**, correct refusal reason category: `60/72` $\rightarrow$ **`62/72` (`+2`)**.
   - Overall `WRONG_SERVED`: **`0/144`**.
4. **Full T3 & Independent Review:**
   - `FULL_PRODUCT_GATE_PASS` on detached candidate `b02b2c422e4049dc6ff0a94996f335424e7b02b9`: `12592 passed, 0 failed` backend pytest, `83 passed / 1417 passed` frontend vitest, production build `PASS`, demo replay `5/5 PASS`, crash surface `6/6 PASS`, post-freeze `MATCH` (`918d3404ac60e81d…`).
   - Independent review (`review.md`) completed by `Independent W3-F1 Cross-Sentence Plane Grounding Reviewer` (`fca2b9f1-95b8-4d68-b5a0-f702b1b75e48`).

---

## 3. Remaining Open Wave 3 Failure Clusters (For Next Repair Waves)

1. **`W3-F2: BASE_SHAPE_AND_RIGHT_TRIANGLE_PHRASING_GAP`** (`PREDICATE_NOT_IN_QUOTE`)
2. **`W3-F3: PRISM_LATERAL_EDGE_AND_ALTITUDE_PREMISE_COVERAGE_GAP`** (`SOURCE_PREMISE_UNREAD`)
3. **`W3-F4: FRACTIONAL_RATIO_AND_IMPLICIT_UNIT_VALUE_GROUNDING_GAP`** (`UNGROUNDED_VALUE`)
4. **`W3-F5: NEGATIVE_REFUSAL_PRECEDENCE_DISAGREEMENT`** (`10/72` negative cases refused with a different precedence category)
