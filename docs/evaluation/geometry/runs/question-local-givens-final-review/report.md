# Question-local givens — final independent review, LOCAL Windows, 2026-10-12

Correction layer for [`question-local-givens`](../question-local-givens/report.md); that report and its receipts keep
their bytes. Branch `research/question-local-givens`, base main `232c1225`.

## Review

One fresh-context LOCAL reviewer (Claude subagent, read-only, 0 provider calls) reviewed `232c1225..98852c8f` with
focus on the fixes `227e1bcf`/`e1f288ec`, which had not been independently reviewed. Existing focused suites:
252 passed. About 70 ask, 14 construction and 3 full-problem probes on both arms, at the branch and at `232c1225`.
No new false serve; arms A and B identical; no second fact store (local claims only compared against validated calls).

| Finding | Effect | Ruling |
|---|---|---|
| I2 "biết rằng" | `Tính SC, biết rằng SA = 3.` served at `232c1225`, refused `QUESTION_CONTEXT_UNSUPPORTED` on the branch (ask and construction, both arms) | **RED for integration** (new false refusal). Fixed `f56d8cb7`: `rằng` added to the closed connector vocabulary |
| I1 same-sentence change | `Tính SC, sau đó thay SA bằng 5 và tính lại SC.`, `Tính SC rồi đổi SA thành 5 …`, `Tính SC, rồi SA = 5.`, `Vẽ thiết diện … (MAB), sau đó SA = 5.` still served from the old figure | Pre-existing at `232c1225`, not a regression; integration remains a strict safety improvement. Recorded open in `ISSUE-ARCH-HYBRID-QUESTION-LOCAL-GIVENS` |
| Minor | New conservative refusals: shape restated without side, `S.ABCD là hình chóp`, `SA = 3 cm` on a unitless source; `_nguon_do_dai_cuc_bo` ignores `equal_length` classes | Safe direction; recorded as limits |

**Correction of the prior claim.** "An earlier clean ask cannot hide a later changed context" in the prior report holds
for later sentences and marked givens (`cho`, `khi`, `nếu`, `sau khi`, `biết`), not for an unmarked change after
"sau đó"/"rồi" in the same sentence.

## RED → GREEN and gates

- New regression `test_bare_connector_biet_rang_is_a_given_lead_in` (ask + construction, arms A/B, matching and
  conflicting given): before the fix 2 failed / 2 passed (the conflict control already refused); after, focused
  suites 256 passed; connected Hybrid cluster 971 passed / 5 xfailed, the only red being the expected candidate drift.
- Candidate refrozen in a clean detached worktree at `f56d8cb7`, committed separately as `8fa3ae4c`:
  `25c85eed5e7433b0f44efdbc2b623cfc416eaf614a411defd547156194bcd438`, 110 files; `--verify` PASS.
  Divergence chain extended in `inputs/candidate_divergence.json`; candidate/divergence/provider-pin suites 146 passed.
  Provider A `912b22ef…`, B `396f1c9c…`, declarations `f2ec9698…` unchanged.
- Clean detached T3 at `8fa3ae4c`: **FULL_PRODUCT_GATE_PASS**, exit 0; backend 8764 passed / 0 failed / 1 skipped /
  2 deselected / 5 xfailed; frontend 1053 passed (68 files); typecheck/build PASS; demo 5/5; crash surface PASS.
  `verification/t3.log` SHA256 `89d1d99e4b9c6ef2c36a3298bd2d5ea668811ea9b1e409e3df7644c069a1fe41`.
- Benchmark 30 cases, both arms 19/9/0/2; metrics SHA256 `febb5b60…` byte-identical to the prior run.

Schema, M4, `CACHE_VERSION` 125, default `LLM_ONLY`, Gemini prompt and renderer unchanged. LIVE requests = 0.

## Recommendation

**GO for a local fast-forward** of `research/question-local-givens` onto `main` after the user's integration decision;
`main` is an ancestor. No merge or push executed. No live-model or default-mode GO; I1 stays open.
