# W4 handoff: READY_FOR_OWNER_REVIEW

**Branch and verdict:**
- Branch `research/w4-geometry-pedagogy`, from `main` = `origin/main` = `e5dc3d28`.
- Product commit `61ade29e`; candidate `182a7785` (118 files, `54b5b565…`); `CACHE_VERSION` 131; `LLM_ONLY`; 0 provider calls.
- Verdict: **READY_FOR_OWNER_REVIEW.** Every technical gate passed. The only open item is a publication decision that only the Owner can make.

## Gates

| gate | result | receipt |
|---|---|---|
| Wave 3 target ≥58/72 positives, 72/72 negatives, 0 wrong-served | **67/72**, 72/72, 0 wrong-served, 62/72 reasons | `regression-green3.json`; re-run at HEAD in `final-review/` |
| Locked regression, reviewer probes | 96/96; 203 probes unchanged | same |
| Mutation / adversarial | all mutants killed; pre-freeze BLOCKER fixed; final review READY | test files, `pre-freeze-review.md`, `final-review.md` |
| T0 / T1 / T2 | PASS | `tiers.json` |
| Candidate freeze, separate commit | `182a7785`, `--verify` 0 | `frozen-evaluation-candidate.json` |
| Full T3, clean detached worktree | `FULL_PRODUCT_GATE_PASS` (`25028584`, attempt 2) | `full-t3.json`, `final-review.md` F3 |
| Publication range `e5dc3d28..HEAD` | **BLOCKED**: 1 `PENDING_OWNER_DECISION` (synthetic key, blob `24d45cd6`) | `publication-assessment.md` |
| Publication head | 0 unexcepted (pre-W4 main: 1) | same |

## Owner decisions

1. **Required for integration:** approve or decline blob `24d45cd6` with the command in `publication-assessment.md`. The agent never writes `APPROVED_BY_USER`.
2. **Optional:** accept the local-path disclosure in `pre-freeze-review-files.sha256` and `pre-freeze-review/probes.py` (`final-review.md` F1). It contains no credential, and main already carries such paths. The scanner does not flag it.

## After approval (scoped W4 rule, not inherited from W3-F2)

1. Check that the registry semantic diff is exactly one value.
2. Run the range scan; it must give 0 violations.
3. Verify the live remote `main` is still `e5dc3d28`.
4. Fast-forward `main` to the W4 tip.
5. Post-integration checks: freeze `--verify`, the targeted suites, preview fixtures, the docs gate and a head scan.
6. Push without force.
7. Run a three-way SHA check (local `main`, `origin/main`, ls-remote).
8. Clean up only what is provably preserved:
   - the `w4-final-t3-25028584` worktree (unlink its node_modules junction first);
   - the W4 worktree;
   - the merged branch.

## Known limitations

- **Five Wave 3 false refusals remain:** W3-B01, B34–36, A06.
- **Role checks:** "đường chéo" is not role-checked. "chiều cao XY" accepts any validated XY ⊥ base.
- **UX:** ←/→ still step the scene while the tool menu is open (F6).
- **Unread phrasings:** some textbook phrasings are still refused (F7).
- **Not measured:** live provider quality and learning gains. The pedagogy evidence is proxy only.
- **Environment:** a Vite dev server left from UI evidence capture is still listening on port 3017, PIDs 3440 and 9616. Stopping it was not permitted to the agent.
