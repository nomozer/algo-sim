# Independent Pre-Merge Evidence Reconciliation Review — `HYBRID_V2_W2_M4_PREMERGE_EVIDENCE_RECONCILIATION`

- **Reviewer:** Independent Math, Kernel & Verification Reviewer (`research` subagent `1cedffc6-e203-4b8a-bbf9-6b8323a99199`)
- **Reviewed Branch:** `research/hybrid-v2-w2-m4-exact-radical-normalization`
- **Base Commit Audited Against:** `e78ecfe7a28cbe9de2754b08283b56d3829d1c1a`
- **Product Commit:** `051224ee2740cbf5d55dd94633503db1f0050ada`
- **Frozen Full T3 Candidate:** `1e0c8db668bbe110f343a8a67cdeca465008c188` (`8b94a5aa4a986e312ef423492b332bf25378868f6c9578767ba2ee7003c18369`, `118` files)
- **Final Review Verdict:** `APPROVED_NO_FINDINGS` (`0 BLOCKER`, `0 MAJOR`, `0 MINOR`, `0 NIT`)

---

## 1. Review Rounds & Finding Disposition

| Pass | Severity | ID | Finding | Resolution | Status |
|---|---|---|---|---|---|
| Pass 1 | `MINOR` | `RECON-1` | `tools/reconcile_premerge_evidence.py:223` scanned `RUN.rglob("*")` for `"150062500"`, `"819529"`, `"8750*sqrt(1006)"`, `"8750√1006"` without excluding `handoff.md` (which cites the debunked conversational summary numbers in `handoff.md:32`), making a second run of `reconcile_premerge_evidence.py` fail. | Added `"handoff.md"` to `reconciliation_meta_files` in `tools/reconcile_premerge_evidence.py` and added an explicit `git grep -F <tok> e78ecfe7a28cbe9de2754b08283b56d3829d1c1a` loop across the entire Git tree at `e78ecfe7`. Re-ran `reconcile_premerge_evidence.py` twice in succession (`exit_code = 0`). | **CLOSED (`RECON_1_VERIFIED_OK`)** |
| Pass 2 | — | — | Re-verification of all 4 checklist areas and `RECON-1` fix. | All checks pass (`0 BLOCKER`, `0 MAJOR`, `0 MINOR`, `0 NIT`). | **`APPROVED_NO_FINDINGS`** |

---

## 2. Detailed Checklist Verification

### 2.1 Product & Historical Evidence Immutability (`PASS`)

- **Zero Product Diff:** Independently verified via `git diff --name-only 1e0c8db668bbe110f343a8a67cdeca465008c188 -- backend/app frontend/src` that `0` product files differ from frozen Full T3 candidate `1e0c8db668bbe110f343a8a67cdeca465008c188` (`8b94a5aa4a986e312ef423492b332bf25378868f6c9578767ba2ee7003c18369`, `118` files).
- **100% Byte-Identical Locked Historical Artifacts:** Independently verified via `git diff --name-only e78ecfe7a28cbe9de2754b08283b56d3829d1c1a` that all 12 locked historical files (`report.md`, `architecture-decision.md`, `baseline-audit.md`, `plan.md`, `review.md`, `inputs/development.json`, `results/red-before.json`, `results/green-after.json`, `results/source-gate-regression.json`, `results/wave2-post-feedback-regression.json`, `verification/full-t3/receipt.json`, `verification/full-t3/full-t3.log`) are **100% byte-identical** to `e78ecfe7a28cbe9de2754b08283b56d3829d1c1a`.

### 2.2 Finding A (`W2-A04` Mathematical Consistency) (`PASS`)

- **Independent First-Principles & Oracle Verification:**
  - Inspected `ecdc26b012c8ce80d53524a98dc75cdcb020079d` (`inputs/holdout-wave2.json`, `oracle/expected.json`, `oracle/geometry.json`), product execution on `051224ee2740cbf5d55dd94633503db1f0050ada`, and independent exact `Fraction` coordinate geometry recomputation:
    - Rectangular pyramid $S.ABCD$ with $A(0,0,0), B(6,0,0), C(6,8,0), D(0,8,0), S(0,0,10)$, plane $(Q)$ through $A$ perpendicular to $SC$ ($3x + 4y - 5z = 0$).
    - Edge intersections from $S$: $t_{SB} = \frac{25}{34}$ ($M = (75/17, 0, 45/17)$), $t_{SC} = \frac{1}{2}$ ($N = (3, 4, 5)$), $t_{SD} = \frac{25}{41}$ ($P = (0, 200/41, 160/41)$).
    - Exact squared area:
      $$\text{area}^2 = \frac{253,125,000}{485,809}, \qquad p = 2^3 \cdot 3^4 \cdot 5^8 = 11,250^2 \cdot 2, \qquad q = 17^2 \cdot 41^2 = 697^2$$
    - Unreduced intermediate radicand:
      $$p \cdot q = 122,970,403,125,000 = 7,841,250^2 \cdot 2$$
    - Canonical exact area:
      $$\text{area} = \frac{11,250\sqrt{2}}{697} = \text{Radical}(\text{Fraction}(11250, 697), 2, 0), \qquad \text{square}(\text{area}) = \frac{253,125,000}{485,809}$$
- **Zero Repository Occurrences at `e78ecfe7`:** Independently verified via `git grep -F <tok> e78ecfe7a28cbe9de2754b08283b56d3829d1c1a` across the entire Git tree that `"150062500"`, `"819529"`, `"8750*sqrt(1006)"`, and `"8750√1006"` have **0 occurrences** in any committed repository file at `e78ecfe7`.
- **`W2-M4-DOC-5` (`baseline-audit.md:53`):** Confirmed that `correction-addendum.md` §2.2.4 accurately documents the intermediate prime-exponent typo in `baseline-audit.md:53` (`2^3 * 3^4 * 5^7 = (2 * 3^2 * 5^3)^2 * 10 = 11250^2 * 2` instead of `2^3 * 3^4 * 5^8 = (2 * 3^2 * 5^4)^2 * 2 = 11250^2 * 2`, where both endpoints `253,125,000` and `11250^2 * 2` are exact).

### 2.3 Finding B (Holdout Wave 2 Historical & Post-Feedback Counts) (`PASS`)

Independently verified from the 4 per-case machine JSON artifacts (`scored-run-1/track-a.json`, `scored-run-2-harness-corrected/track-a.json` at `ecdc26b0`, `hybrid-v2-wave2-source-gate-language-generalization/results/wave2-post-feedback-regression.json` at `d99f6149`, and `hybrid-v2-w2-m4-exact-radical-normalization/results/wave2-post-feedback-regression.json` at `051224ee`):

1. **Historical Raw (`scored-run-1` at `d7a94d3c` / `ecdc26b0`):** `3/48` positive `SERVED_CORRECT` (`3/36` Category B: `W2-B08`, `W2-B12`, `W2-B14`; `0/12` Category A; `2/48` harness-induced false `WRONG_SERVED` on `W2-A01`, `W2-A03`; `43/48` `FALSE_REFUSAL`; `48/48` negatives refused; `33/48` reason agreement).
2. **Historical Adjudicated (`scored-run-2-harness-corrected` at `d7a94d3c` / `ecdc26b0`):** `5/48` positive `SERVED_CORRECT` (`3/36` Category B: `W2-B08`, `W2-B12`, `W2-B14`; `2/12` Category A: `W2-A01`, `W2-A03`; `0/96` `WRONG_SERVED`; `43/48` `FALSE_REFUSAL`; `48/48` negatives refused; `33/48` reason agreement).
3. **Source Gate `/19` Replay (`d99f6149`):** `45/48` positive `SERVED_CORRECT` (`36/36` Category B, `9/12` Category A, `3/48` `FALSE_REFUSAL` [`W2-A04`, `W2-A07`, `W2-A10`], `48/48` negatives refused, `36/48` reason agreement, `0/96` `WRONG_SERVED`).
4. **W2-M4 Replay (`051224ee`):** `46/48` positive `SERVED_CORRECT` (`36/36` Category B unchanged from `d99f6149`, `10/12` Category A up from `9/12` via `W2-A04`, `2/48` `FALSE_REFUSAL` [`W2-A07`, `W2-A10`], `48/48` negatives refused, `36/48` reason agreement, `0/96` `WRONG_SERVED`).
5. Confirmed that `W2-M4-DOC-1` (`report.md:77` `37/48` $\to$ `3/48` raw / `5/48` adjudicated at `d7a94d3c`, `45/48` at `d99f6149`) and `W2-M4-DOC-2` (`report.md:79–80` Category B already `36/36` at `d99f6149`, Category A `9/12` $\to$ `10/12` via `W2-A04`) are accurately documented in `correction-addendum.md` §3.

### 2.4 Additional Integrity Checks (`W2-M4-DOC-3`, `W2-M4-DOC-4`), SHA-256 Table & Archival Plan (`PASS`)

- **`W2-M4-DOC-3`:** Accurately reconciles the `<= 5,000` odd steps uniform bound in `051224ee` (`d * d * d <= MAX_RADICAND`) vs. the leftover `<= 500,000` phrase in `architecture-decision.md:30` and pre-`051224ee` `baseline-audit.md` / `plan.md`.
- **`W2-M4-DOC-4`:** Accurately documents why `results/green-after.json`, `results/source-gate-regression.json`, and `results/wave2-post-feedback-regression.json` record `"head": "14bc010e4b4af2bb324c63e309d41c5c5847a904"` and `"product_diff_sha256": "c730cb94bbd50e557b8d8283c8f73c741d90f32b84576fb954538de07696e147"` (generated on the working tree immediately before committing `051224ee` on top of parent `14bc010e`).
- **SHA-256 Table:** All 12 raw and LF-normalized SHA-256 digests in `correction-addendum.md` §4.3 and `results/premerge-evidence-reconciliation.json` were independently recomputed and match 100%.
- **3-Step `main` Integration Sequence:** Confirmed that `d7a94d3c..ecdc26b0` (`34` files under `docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-section-holdout-wave2/`) and `d7a94d3c..e78ecfe7` have **0 overlapping files**, so fast-forwarding `main` to `research/hybrid-v2-w2-m4-exact-radical-normalization` first (`--ff-only`) followed by a path-disjoint `--no-ff` documentation merge of `ecdc26b012c8ce80d53524a98dc75cdcb020079d` preserves `051224ee`/`1e0c8db6` on `main`'s first-parent spine and makes `ecdc26b0` reachable in single-branch clones of `main` with `0` product diff.
