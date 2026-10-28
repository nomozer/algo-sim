# Session Handoff — Hybrid V2 W2-M4 Exact Radical Normalization (`hybrid-v2-w2-m4-exact-radical-normalization`)

## 1. Wave Status & Authoritative Identities

- **Task:** `HYBRID_V2_W2_M4_EXACT_RADICAL_NORMALIZATION`
- **Status:** `READY_FOR_OWNER_REVIEW`
- **Branch:** `research/hybrid-v2-w2-m4-exact-radical-normalization`
- **Worktree:** `.superpowers/worktrees/w2-m4-exact-radical-normalization`
- **Detached T3 Worktree:** `.superpowers/worktrees/w2-m4-t3-detached`
- **Authoritative `main = origin/main`:** `d7a94d3cd4bbdea3df99e383bec78425fcc8bf1c`
- **Parent Baseline (`research/hybrid-v2-wave2-source-gate-language-generalization`):**
  - Final HEAD: `d99f6149ff1997258970bf888db5484665b106b8`
  - Product commit: `c6f6b64bda6473c175a32a7875a9dd9831ae7c6d`
  - Frozen T3 candidate: `b9e3d0966e14acb1d44f2f9c7cd7a3bf49ac54a9` (`8baf3205006d097efdd21087b9d52e85625fa1263e9125b418cf658ccac18d25`)
  - Historical verdict (preserved unchanged): `NOT_READY_ACCEPTANCE_GATE_FAILED`
- **Preregistered RED Commit:** `574ad40ca446232bf54e8e26cda196eee943fcb3`
- **Product Repair Commit:** `051224ee2740cbf5d55dd94633503db1f0050ada`
- **Frozen Full T3 Candidate:** `1e0c8db668bbe110f343a8a67cdeca465008c188`
- **Measured Product System:** `118` files, tree SHA-256 `8b94a5aa4a986e312ef423492b332bf25378868f6c9578767ba2ee7003c18369`
- **Product Files Modified:** `backend/app/simulation/geometry/radical.py` (`1` file)
- **Versions & Mode:** `Registry /19`, `Planner /17`, `Engine /14`, `Adapter /4`, `plane-section-certificate/1`, `CACHE_VERSION = 130` (`NO_BUMP`), `DEFAULT_MODE = LLM_ONLY`, `live_provider_calls = 0`.
- **Merge / Push / Cleanup:** `NONE` (per Owner GO §0 and §10).

---

## 2. Key Outcomes

1. **`DEV-1-3` & `W2-A04` Resolved Exactly:**
   - `DEV-1-3` (`area_squared = 38130625/58564`, unreduced $p \cdot q = 2,233,081,922,500 > 10^{12}$): now `SERVED_CORRECT` with exact rational area `Fraction(6175, 242)` (`6175/242`), closing open MAJOR finding `ACCEPTANCE-1` from Source Gate `/19`.
   - `W2-A04` (`area_squared = 253125000/485809`, unreduced $p \cdot q = 122,970,403,125,000 > 10^{12}$): now `SERVED_CORRECT` with exact radical area `Radical(Fraction(11250, 697), 2, 0)` (`11250√2/697`).
2. **Locked Regressions:**
   - W2-M4 verification corpus (`results/green-after.json`): `2/2` end-to-end, `16/16` kernel, `6/6` metamorphic, `11/11` negative (`all_passed = true`).
   - Source Gate `/19` regression (`results/source-gate-regression.json`): `24/24` original positives `SERVED_CORRECT`, `36/36` genuine negatives refused (`36/36` reason agreement), `1/1` adjudicated valid mislabeled negative `SERVED_CORRECT`, `0` genuine wrong-served, `25/25` exact oracle agreement, `7/7` supplemental controls passed.
   - Holdout Wave 2 post-feedback regression (`results/wave2-post-feedback-regression.json`, `POST_FEEDBACK_DEVELOPMENT_REGRESSION`): `46/48` positive `SERVED_CORRECT` (`46/46` exact oracle agreement; Category B `36/36`, Category A `10/12`), `2/48` remaining false refusals (`W2-A07`, `W2-A10` on out-of-scope `W2-M5` at `Adapter /4`), `48/48` negatives refused (`36/48` reason agreement), `0/96` wrong-served.
3. **Full T3 Gate (`verification/full-t3/receipt.json`):**
   - `FULL_PRODUCT_GATE_PASS` on clean detached candidate `1e0c8db668bbe110f343a8a67cdeca465008c188`: `12552 passed, 0 failed` backend pytest, `83 passed / 1417 passed` frontend vitest, production build `PASS`, demo replay `5/5 PASS`, crash surface `6/6 PASS`, post-freeze `MATCH` (`8b94a5aa4a986e31…`).

---

## 3. Next Steps for Owner

1. Review the evidence package in `docs/evaluation/geometry/runs/hybrid-v2-w2-m4-exact-radical-normalization/`.
2. Decide whether to:
   - Authorize a bounded follow-up wave for the remaining 2 Category A false refusals (`W2-M5: PREVIEW_VALIDATION_FAILED / CANNOT_BUILD_SOLIDS` on `W2-A07` and `W2-A10` in `Adapter /4`), or
   - Proceed with pre-merge adjudication / integration of the verified `Registry /19` + `W2-M4` exact radical normalization lineage (`1e0c8db6`).
