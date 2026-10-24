# Final owner handoff: visual–Hybrid final corrections

Authorization `GO_LOCAL_VISUAL_HYBRID_FINAL_CORRECTIONS_ONLY`.
- **Branch:** `integration/hybrid-visual-candidate`, local only.
- **Not done:** local `main` stays `9978e512`; no push, no history rewrite, no live provider, no production Hybrid, no publication-exception change, no ACL change.
- 0 model calls.
- **Untouched:** the root checkout (owner's work) and Codex's `visual-hybrid-integration` worktree.

**Status: corrections complete. Local main is NOT ready for an owner GO yet.** Three things are open:
1. two product findings from the official suite;
2. the owner-run independent review;
3. human visual approval.

## 1. Official suite verdict and all remaining failures

**FAIL**, 8/8 scenarios, but every remaining failure is one of two **product findings**. There are 0 harness and 0 environment failures; all refusal, negative and served runs pass. Details are in OFFICIAL_SUITE_RESULTS.md.

The suite now validates the current learner policy:
- **Mode A (default):** no final answer anywhere.
- **Mode B («Phân tích toán học», opened by the learner):** the answer appears exactly once, and the causal-closure oracle is measured there.

The independent oracles and all thresholds are unchanged. Before/after receipts: Codex's earlier run, run 1, run 2.

**F1. Mode B explains a final answer in two places**, the inspector and the analysis panel, against the W18 one-region rule. It affects 7 families on both viewports.
- Option: show the formula in one of the two.
- Option: amend the rule for Mode B.

**F2. The SGK terracotta section (hue ≈ 16°) is inside the oracle's orange "data" role band**, and a selected section shows no target hue (`cross_section`).
- Option: change the section or target colouring.
- Option: amend the role-hue registration.

## 2. Backend naming correctness

Fixed in the backend (`af670aa6`). The frontend still prints notation verbatim. Details are in DISPLAY_IDENTITY_FIX.md.

- **Section vertex cycle:** built only from the notation each vertex shows, never from an id. Otherwise the section is named by its construction sentence.
- **Declared plane names:** `(P)` / `(Q′)` / `(α)` win over the composed name only when the problem text writes the name and exactly one plane declares it. Your rule, with negative controls.
- **Adapter /4:** export byte-identical, 0 leaks over 9 scenes with unnamed points.
- **Only names change:** coordinates, DAG, provenance, order, answers and certificates are equal.
- **Offline samples:** regenerated. The builder now passes each sample's problem text and asked obligations, per your decision, which closed an inherited hidden-answer gap in `the-tich-chop`.
- **Residual, reported:** Adapter /3 still spells `MI1I2I3`. It has no product consumer, and a test locks that.

## 3. Cache version decision

**127 → 128 (BUMP).** A genuine v127 row written by the clean v127 tree serves `(AB′D′)` where v128 serves `(P)`. A hit returns the stored envelope as is, so the old row must miss.

Evidence is in `cache/decision.json`, and the migration test is `backend/tests/test_cache_display_identity_invalidation.py`:
- the v127 row misses;
- the fresh envelope equals the v127 bytes with only the name replaced;
- the control is byte-identical;
- the row is rewritten as v128, and the next request hits.

The model surface is unchanged: in `cache_identity.lock.json` only the version moved. All sync places are updated.

## 4. Diagnostics UI outcome

`0645de46` removes the "Chi tiết chẩn đoán" drawer, which showed `reason_code` / `error_code` and the raw reason. The strict learner assertions are restored over the whole notice. Codes remain in the envelope, the API, the logs and the receipts.
- Refusal surface: 21/21.
- Owner refusal screens: no code and no drawer on desktop and mobile.

Details are in DIAGNOSTICS_UI.md.

## 5. Candidate SHA and Full T3

- **Product:** `af670aa6ba02b7c04da4fe7f863e015d0f4e6e60`.
- **Freeze:** `a636a0e5`, 118 files, `8be632679307a94ce4525ad576a05a9eccffc8ba2bdbf02d4c7dc93c208b7c41`, cache 128.
- **Full T3 at `a084c180`: `FULL_PRODUCT_GATE_PASS`.** pytest 11856 passed, Vitest 1343, build, demo, crash surface; post-T3 `--verify` MATCH.
- The earlier T3 (`b99afd32`, product `a9d05dda`) is not reused.

Details are in REGRESSION_RESULTS.md.

## 6. Browser and independent review results

**Browser:** details are in BROWSER_ACCEPTANCE.md.
- Adapter /4 consumer: 94 rows PASS.
- Refusal surface: 21/21.
- Orbit gate: ĐẠT, 0 allocations.
- Official suite: rendering assertions pass in all 8 families.
- Owner screens: 12 product screens plus 6 refusal screens.

**Independent review: PENDING.** You chose to run it yourself (2026-10-24). The packet is REVIEW_PACKET.md. No subagent of this session was used as a substitute, and `INDEPENDENT_REVIEW.md` does not exist yet.

## 7. Human visual approval status

**NOT_GRANTED.** The screens are ready in `verification/browser/owner-visual/` and `verification/browser/owner-refusal/`. Points worth your eye are in BROWSER_ACCEPTANCE.md:
- `(P)` is small on the sphere sample;
- the construction points U and W are labelled there;
- the "hệ trục do đề chọn" wording in Mode B.

## 8. Is local main ready for an explicit owner GO?

**No.** Before a GO:
1. **Decide F1 and F2:** fix the product, or amend the registered rule. Then re-run the official suite.
2. **Run the independent review** from REVIEW_PACKET.md and record it.
3. **Give or withhold human visual approval.**

Already done for a later merge:
- Full T3 on the candidate;
- the post-T3 freeze match;
- the cache migration test;
- the correction-chain layer (`candidate_divergence.json`).

## Commits (this task)

| Commit | Content |
|---|---|
| `0645de46` | P3 diagnostics UI |
| `af670aa6` | P2 display identity, samples, cache 128 |
| `e3e77a0f`, `4ec36db9` | official suite learner-mode split |
| `a636a0e5` | candidate freeze |
| `7c296be1` | correction-chain layer |
| `63948c05` | suite inputs bound to the candidate |
| `a084c180` | suite reruns, browser, owner screens, review packet (T3 target) |
| (this commit) | T3 receipt, reports, index write-back |

No commit carries a `Co-Authored-By` trailer.

## Worktrees

None was created or removed.
- `t3-b1b2` was moved, detached, between commits for the measurements and is clean.
- Codex's server on 3117 is still running.
- The root checkout is untouched.
