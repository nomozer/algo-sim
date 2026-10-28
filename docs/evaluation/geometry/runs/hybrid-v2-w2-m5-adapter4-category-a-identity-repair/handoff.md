# Session Handoff — Hybrid V2 W2-M5 Adapter `/4` Category A Identity Repair (`hybrid-v2-w2-m5-adapter4-category-a-identity-repair`)

## 1. Wave Status & Authoritative Identities

- **Task:** `HYBRID_V2_W2_M5_ADAPTER4_CATEGORY_A_IDENTITY_REPAIR`
- **Status:** `READY_FOR_OWNER_REVIEW`
- **Branch:** `research/hybrid-v2-w2-m5-adapter4-category-a-identity-repair`
- **Worktree:** `.superpowers/worktrees/w2-m5-adapter4-category-a-identity-repair`
- **Authoritative `main = origin/main`:** `eb661971847c034500862299c5091f1f3d2a2998`
- **Historical Holdout Wave 2 Commit (preserved untouched):** `ecdc26b012c8ce80d53524a98dc75cdcb020079d`
- **Product Repair Commit:** `73ca8d92e74059680ce53b99692af396df37a2f8`
- **Test & Evaluation Artifacts Commit:** `7aa538aecf2d31c40887b7c6ee52f7e8219ea0eb`
- **Frozen Full T3 Candidate:** `b61f16995dfbe0110a639a2127d0fb5a9c3afde0`
- **Measured Product System:** `118` files, tree SHA-256 `1170ca163529dd40b57f4058826db92a6433359546aa2ad718712f38a538c10d` (`MATCH`)
- **Product Files Modified (`eb661971..HEAD`):** `backend/app/ai/adapter4_route.py` (`1` file only; `0` product diff between `b61f1699` and `HEAD`)
- **Versions & Mode:** `Registry /19`, `Planner /17`, `Engine /14`, `Adapter /4`, `plane-section-certificate/1`, `CACHE_VERSION = 130` (`NO_BUMP`), `DEFAULT_MODE = LLM_ONLY`, `live_provider_calls = 0`.
- **Merge / Push / Cleanup:** `NONE` (awaiting Owner merge GO).

---

## 2. Key Outcomes

1. **`W2-A07` & `W2-A10` Resolved (`W2-M5` Closed):**
   - `W2-A07` (right triangular prism `ABC.A'B'C'`, section `(A'MN)`, `section_area`): `SERVED_CORRECT` with Category A (`DINH_CAT_CANH`), vertices `["A'", "M", "N"]`, exact `area_squared = 1875/8`, and formatted answer `"25√6/4"`.
   - `W2-A10` (cube `ABCD.A'B'C'D'`, section `(A'MN)` cutting `BB'`, `CC'`, `DD'` at `I`, `I1`, `I2`, `section_only`): `SERVED_CORRECT` with Category A (`DINH_CAT_CANH`), 4-vertex boundary cycle `[I, A', I2, I1]`, and exact polygon `area_squared = 504`.
2. **Locked Development & Tamper Corpus (`inputs/development.json`, `results/red-before.json`, `results/green-after.json`, `results/tamper-results.json`):**
   - Positive Category A primed-vertex cases: RED `0/14` (`14/14` `FALSE_REFUSAL`) $\to$ GREEN **`14/14` `SERVED_CORRECT`** (`14/14` exact `Fraction` oracle agreement).
   - Mandatory tamper modes (`TAMPER-01..12`): RED `12/12` $\to$ GREEN **`12/12` refused** (`PREVIEW_VALIDATION_FAILED`, plus 3 machine-ID `_prime` leak guards in `test_w2_m5_adapter4_category_a_identity.py`, `17/17` pytest passed).
3. **Full 96-Case Holdout Wave 2 Post-Feedback Regression (`results/wave2-post-feedback-regression.json`, `results/w2-a10-scorer-adjudication-receipt.json`):**
   - Raw unmodified historical scorer (`evaluate_holdout_wave2.py` at `ecdc26b0`): `47/48` positive `SERVED_CORRECT`, `0/48` `FALSE_REFUSAL`, `1/48` scorer lookup artifact on `W2-A10` (`evaluate_holdout_wave2.py:184` checked `v["label"] in objects_by_id` directly instead of calling its own `_find_point_xyz(objects_by_id, v["label"])` helper defined at line `146`).
   - Scorer-adjudicated result: **`48/48` (`100.00%`) positive `SERVED_CORRECT`** (`36/36` Category B `ENGINE_DERIVED_SECTION`, `12/12` Category A `DINH_CAT_CANH`, `48/48` exact oracle agreement), **`48/48` negative safe refusals** (`36/48` exact refusal-category agreement), **`0/96` genuine wrong-served**, and **`96/96` learner-facing source-identity clean** (`0` `_prime` leaks).
4. **Full T3 Gate (`verification/full-t3/receipt.json`) & Independent Review (`review.md`):**
   - `FULL_PRODUCT_GATE_PASS` on clean detached candidate `b61f16995dfbe0110a639a2127d0fb5a9c3afde0`: `12569 passed, 0 failed` backend pytest, `83 passed / 1417 passed` frontend vitest, production build `PASS`, demo replay `5/5 PASS`, crash surface `6/6 PASS`, post-freeze `MATCH` (`1170ca163529dd40…`).
   - Independent review (`155dd101-7d6a-4edb-9606-b9b56b1bba45`) passed with `APPROVED_NO_FINDINGS` (`0 BLOCKER, 0 MAJOR, 0 MINOR, 0 NIT`).

---

## 3. Recommended Integration Sequence for `main` (Upon Owner Merge GO)

1. **Fast-Forward `main` (`eb661971847c034500862299c5091f1f3d2a2998`) to `research/hybrid-v2-w2-m5-adapter4-category-a-identity-repair` (`git merge --ff-only`):** Preserves the exact commit SHAs of the verified product (`73ca8d92e74059680ce53b99692af396df37a2f8`), frozen Full T3 candidate (`b61f16995dfbe0110a639a2127d0fb5a9c3afde0`), and final documentation commit on `main`.
2. **Post-Merge Verification & Push:** Re-verify `freeze_evaluation_candidate.py --verify` (`MATCH`), `audit_docs_information_architecture.py` (`PASS`), and `check_publication_safety.py --range eb661971..HEAD` (`PASS`) before pushing `main` to `origin`.
