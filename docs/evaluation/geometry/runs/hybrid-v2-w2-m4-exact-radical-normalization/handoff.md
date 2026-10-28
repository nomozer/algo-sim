# Session Handoff — Hybrid V2 W2-M4 Exact Radical Normalization & Pre-Merge Reconciliation (`hybrid-v2-w2-m4-exact-radical-normalization`)

## 1. Wave Status & Authoritative Identities

- **Task:** `HYBRID_V2_W2_M4_EXACT_RADICAL_NORMALIZATION` + `HYBRID_V2_W2_M4_PREMERGE_EVIDENCE_RECONCILIATION`
- **Status:** `PREMERGE_EVIDENCE_RECONCILED_READY_FOR_OWNER_GO`
- **Branch:** `research/hybrid-v2-w2-m4-exact-radical-normalization`
- **Worktree:** `.superpowers/worktrees/w2-m4-exact-radical-normalization`
- **Detached T3 Worktree:** `.superpowers/worktrees/w2-m4-t3-detached`
- **Authoritative `main = origin/main`:** `d7a94d3cd4bbdea3df99e383bec78425fcc8bf1c`
- **Historical Holdout Wave 2 Commit (`research/hybrid-v2-independent-vietnamese-section-holdout-wave2`):** `ecdc26b012c8ce80d53524a98dc75cdcb020079d`
- **Parent Baseline (`research/hybrid-v2-wave2-source-gate-language-generalization`):**
  - Final HEAD: `d99f6149ff1997258970bf888db5484665b106b8`
  - Product commit: `c6f6b64bda6473c175a32a7875a9dd9831ae7c6d`
  - Frozen T3 candidate: `b9e3d0966e14acb1d44f2f9c7cd7a3bf49ac54a9` (`8baf3205006d097efdd21087b9d52e85625fa1263e9125b418cf658ccac18d25`)
  - Historical verdict (preserved unchanged): `NOT_READY_ACCEPTANCE_GATE_FAILED`
- **Preregistered RED Commit:** `574ad40ca446232bf54e8e26cda196eee943fcb3`
- **Product Repair Commit:** `051224ee2740cbf5d55dd94633503db1f0050ada`
- **Frozen Full T3 Candidate:** `1e0c8db668bbe110f343a8a67cdeca465008c188`
- **Pre-Reconciliation Documentation HEAD:** `e78ecfe7a28cbe9de2754b08283b56d3829d1c1a` (`0` product diff from `1e0c8db6` to `e78ecfe7` and `HEAD`)
- **Measured Product System:** `118` files, tree SHA-256 `8b94a5aa4a986e312ef423492b332bf25378868f6c9578767ba2ee7003c18369` (`MATCH`)
- **Product Files Modified (`d99f6149..HEAD`):** `backend/app/simulation/geometry/radical.py` (`1` file)
- **Versions & Mode:** `Registry /19`, `Planner /17`, `Engine /14`, `Adapter /4`, `plane-section-certificate/1`, `CACHE_VERSION = 130` (`NO_BUMP`), `DEFAULT_MODE = LLM_ONLY`, `live_provider_calls = 0`.
- **Merge / Push / Cleanup:** `NONE` (awaiting Owner merge GO).

---

## 2. Key Outcomes & Pre-Merge Evidence Reconciliation

1. **`DEV-1-3` & `W2-A04` Resolved & Independently Reconciled ([`correction-addendum.md`](correction-addendum.md), [`results/premerge-evidence-reconciliation.json`](results/premerge-evidence-reconciliation.json)):**
   - `DEV-1-3` (`area_squared = 38130625/58564`, unreduced $p \cdot q = 2,233,081,922,500 > 10^{12}$): `SERVED_CORRECT` with exact rational area `Fraction(6175, 242)` (`6175/242`), closing open MAJOR finding `ACCEPTANCE-1` from Source Gate `/19`.
   - `W2-A04` (`area_squared = 253125000/485809`, unreduced $p \cdot q = 122,970,403,125,000 = 7,841,250^2 \cdot 2 > 10^{12}$): `SERVED_CORRECT` with exact radical area `Radical(Fraction(11250, 697), 2, 0)` (`11250√2/697`). Frozen Wave 2 oracle, product output, independent `Fraction` recomputation, and all committed JSON/Markdown files agree 100% (the values `150062500/819529` and `8750√1006/901` appeared only in the previous conversational chat summary and never entered any committed file).
2. **Locked Regressions & Reconciled Historical Trajectory:**
   - W2-M4 verification corpus (`results/green-after.json`): `2/2` end-to-end, `16/16` kernel, `6/6` metamorphic, `11/11` negative (`all_passed = true`).
   - Source Gate `/19` regression (`results/source-gate-regression.json`): `24/24` original positives `SERVED_CORRECT`, `36/36` genuine negatives refused (`36/36` reason agreement), `1/1` adjudicated valid mislabeled negative `SERVED_CORRECT`, `0` genuine wrong-served, `25/25` exact oracle agreement, `7/7` supplemental controls passed.
   - Holdout Wave 2 trajectory (verified from per-case machine JSON records in [`results/premerge-evidence-reconciliation.json`](results/premerge-evidence-reconciliation.json)):
     - Historical raw (`scored-run-1` at `d7a94d3c` / `ecdc26b0`): `3/48` positive `SERVED_CORRECT` (`3/36` Category B, `0/12` Category A, `2/48` harness-induced false `WRONG_SERVED`, `43/48` `FALSE_REFUSAL`, `48/48` negatives refused, `33/48` reason agreement).
     - Historical adjudicated (`scored-run-2-harness-corrected` at `d7a94d3c` / `ecdc26b0`): `5/48` positive `SERVED_CORRECT` (`3/36` Category B, `2/12` Category A, `0/96` `WRONG_SERVED`, `43/48` `FALSE_REFUSAL`, `48/48` negatives refused, `33/48` reason agreement).
     - Source Gate `/19` replay (`d99f6149`): `45/48` positive `SERVED_CORRECT` (`36/36` Category B, `9/12` Category A, `3/48` `FALSE_REFUSAL` [`W2-A04`, `W2-A07`, `W2-A10`], `48/48` negatives refused, `36/48` reason agreement, `0/96` `WRONG_SERVED`).
     - W2-M4 replay (`051224ee`, `results/wave2-post-feedback-regression.json`, `POST_FEEDBACK_DEVELOPMENT_REGRESSION`): `46/48` positive `SERVED_CORRECT` (`36/36` Category B unchanged from `d99f6149`, `10/12` Category A up from `9/12` at `d99f6149` via `W2-A04`), `2/48` remaining false refusals (`W2-A07`, `W2-A10` on out-of-scope `W2-M5` at `Adapter /4`), `48/48` negatives refused (`36/48` reason agreement), `0/96` `WRONG_SERVED`, `46/46` exact oracle agreement.
   - Narrative corrections `W2-M4-DOC-1..5` (covering `report.md:77,79`, `architecture-decision.md:30`, `baseline-audit.md:53,80-103`, `plan.md:46-48`, and `"head": "14bc010e..."` provenance in `results/*.json`) are recorded in [`correction-addendum.md`](correction-addendum.md) without altering any locked historical artifact.
3. **Full T3 Gate (`verification/full-t3/receipt.json`) & Independent Reviews (`review.md`, `review-reconciliation.md`):**
   - `FULL_PRODUCT_GATE_PASS` on clean detached candidate `1e0c8db668bbe110f343a8a67cdeca465008c188`: `12552 passed, 0 failed` backend pytest, `83 passed / 1417 passed` frontend vitest, production build `PASS`, demo replay `5/5 PASS`, crash surface `6/6 PASS`, post-freeze `MATCH` (`8b94a5aa4a986e31…`).
   - Both product repair review ([`review.md`](review.md)) and pre-merge reconciliation review ([`review-reconciliation.md`](review-reconciliation.md)) passed with `APPROVED_NO_FINDINGS` (`0 BLOCKER, 0 MAJOR, 0 MINOR, 0 NIT`).

---

## 3. Recommended Integration Sequence for `main` (Upon Owner Merge GO)

1. **Fast-Forward `main` (`d7a94d3c`) to `research/hybrid-v2-w2-m4-exact-radical-normalization` (`git merge --ff-only`):** Preserves the exact commit SHAs of the verified product (`051224ee`) and frozen Full T3 candidate (`1e0c8db6`) on `main`'s first-parent history without rewriting any commit.
2. **Integrate Frozen Holdout Wave 2 (`ecdc26b012c8ce80d53524a98dc75cdcb020079d`) via Path-Disjoint `--no-ff` Documentation Merge:** Because `d7a94d3c..ecdc26b0` adds only the 34 files under `docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-section-holdout-wave2/` (`0` overlapping files with `d7a94d3c..HEAD`), merging `ecdc26b0` onto `main` after the fast-forward preserves `1e0c8db6` on the first-parent spine, makes `ecdc26b0` reachable in every single-branch clone of `main`, and checks out all 34 Holdout Wave 2 artifacts on `main` with `0` product diff.
3. **Post-Merge Verification & Push:** Re-verify `freeze_evaluation_candidate.py --verify` (`MATCH`), `audit_docs_information_architecture.py` (`PASS`), and `check_publication_safety.py` (`PASS`) before pushing `main` to `origin`.
