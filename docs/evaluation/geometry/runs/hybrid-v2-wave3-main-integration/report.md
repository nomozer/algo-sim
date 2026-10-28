# Wave 3 evidence + W3-F1 main integration verification

Task: `HYBRID_V2_WAVE3_EVIDENCE_W3_F1_MAIN_INTEGRATION` · 2026-10-28 · Owner GO supplied in session.
Pre-push status: `MERGED_VERIFIED_READY_TO_PUSH`. Push and cleanup are recorded separately in `closure.md` after execution.

## Git identity and integration

| Item | SHA / result |
|---|---|
| Pre-merge local main / origin/main / GitHub main | `e137623c4f674135a8d7884b78614c132eb78085` (all three equal) |
| Wave 3 evidence final / Stage A | `0943f0ee6bd2a2b297827e39fa7c07054d716ea9`, fast-forward |
| Wave 3 pre-execution freeze | `2332f7ad3d1a73733bbc720bcf36705c67bc2d6b` |
| W3-F1 product | `a609c4871a75426db52eb8b7a7be8ba3460fcf8c` |
| W3-F1 frozen Full T3 candidate | `b02b2c422e4049dc6ff0a94996f335424e7b02b9` |
| W3-F1 original documented HEAD | `5e056179b39013cc7e3625dd862e66699071a52f` |
| W3-F1 correction / pointer followup | `95b30f7c` / `85f819f02971f31b193dac9be7a56dbe79362e2a` |
| Stage B normal non-fast-forward merge | `1ee44b89dc593ebc544a4fd6af96f698ff2bf4d7` |
| Merge parent 1 | `0943f0ee6bd2a2b297827e39fa7c07054d716ea9` |
| Merge parent 2 | `85f819f02971f31b193dac9be7a56dbe79362e2a` |

Both branches descend from the exact baseline. Conflicts occurred only in the top insertions of `CODE_INDEX.md`, `CURRENT_STATE.md` and `EVIDENCE_INDEX.md`. Both additions were retained and living integration status reconciled. No product or historical artifact was edited to resolve conflicts. `EVALUATION_CANDIDATE.json` is the W3-F1 candidate manifest unchanged from the research branch.

## Evidence and correction

[Preflight audit](verification/preflight-audit.json) checks **73 SHA-256 references** and inventories **31 historical Wave 3 blobs**. All 18 pre-execution manifest entries reproduce their recorded raw hash/byte count and LF hash; original Windows CRLF and Git LF are distinguished explicitly. Scorer qualification at `53cba0c8` precedes corpus creation, corpus/oracle freeze at `2332f7ad` precedes execution/publication, and original `scored-run-1` files occur only in the publication commit `0943f0ee`. The evidence branch has no backend/frontend changes.

All 31 historical Git blobs remain byte-for-byte identical on merged main; checkout content matches their LF hashes. Historical Wave 3 remains **20/72 served-correct, 52/72 false refusals, 72/72 negatives refused, 60/72 correct reasons, 0/144 wrong-served**, classification `INDEPENDENT_HOLDOUT_WAVE3_EXECUTED`, independence class `AI_CURATED_PROCEDURAL_INDEPENDENCE`.

[W3-F1 correction](../hybrid-v2-w3-f1-cross-sentence-plane-grounding/handoff-correction.md) supersedes the incorrect cluster names in original handoff §3 without changing it or any locked receipt. Machine-verified historical F1..F5 counts **24/14/10/3/1** become **0/21/16/5/1**. Of the original 24 F1 cases, 9 are served correctly, 7 expose F2, 6 expose F3 and 2 expose F4. Negative reason disagreements **12 → 10** are separate from these positive false-refusal clusters. A stale living-index tamper pointer now points to actual outcomes in `green-after.json`.

The original T3 log used mixed line endings. Its exact raw 167582 bytes, SHA-256 `885333241d4d723d73edad5b8f2e98ccf3da0700361fbe4eb974893037ddb2f7`, are preserved in append-only `verification/full-t3/original-log.gz` of the W3-F1 run. Its LF-normalized bytes equal the existing Git log blob. The original log and receipt are untouched; the compressed archive makes the receipt reproducible after worktree cleanup.

## Product and verification

[Product/evidence receipt](verification/product-and-evidence.json): all **118 measured files** match candidate `b02b2c42` individually and combined freeze **`918d3404ac60e81d62c75f6bfb7067ea25a4e27c197e3584075edef42e441f72`**. Full `backend/app` and `frontend/src` Git diffs are empty. Clean detached verification checkout was created at the exact candidate and independently returned freeze MATCH.

The existing Full T3 receipt is therefore applicable: **12592 backend, 1417 frontend passed, build PASS, demo 5/5, crash 6/6**. Full T3 was not rerun. All changes after the frozen candidate are docs/evidence only. The 70-step candidate-divergence chain resolves to the W3-F1 declaration and current freeze.

[Post-merge smoke](verification/smoke.json): **890 passed, 5 xfailed, zero failed**, 23 files, run directly on merged main `1ee44b89`. Coverage includes W3-F1 cross-sentence grounding and all mandatory 20 negative/tamper tests; Registry /20, Planner /18, TypedFactNext bridge, section/area goals, Category A/B, Adapter /4, Certificate /1, W2-M4 radicals, W2-M5 primed identity, cache, candidate/thesis acceptance, docs IA and scorer qualification. The five expected failures are retained baseline xfails.

[Post-feedback replay](verification/wave3-post-feedback-replay.json): **29/72 positives served-correct, 43 false refusals, 72/72 negatives refused, 62/72 correct reasons, 0/144 wrong-served**, `section_and_area` 9/24. All 144 case outcomes/codes and historical transitions exactly match the locked W3-F1 regression. Classification is `POST_FEEDBACK_DEVELOPMENT_REGRESSION`; no claim of a new independent blind holdout. Original scored-run output was not overwritten. Replay explicitly blocks outbound sockets.

[Other gates](verification/gates.json): freeze MATCH; cache130 lock MATCH; **41/41 preview fixtures**, zero problems; docs IA PASS; publication safety over baseline→merge **86 blobs / 15 messages, zero violations or pending exceptions**. A final publication scan including this evidence commit must pass before push. [Independent bounded review](review.md): `APPROVED_NO_FINDINGS` before merge.

Runtime remains Registry /20, Planner /18, Engine /14, Adapter /4, Certificate /1, cache130, **DEFAULT_MODE=LLM_ONLY**, Hybrid opt-in, **ALLOW_LIVE_AI=0**, live provider calls **0**.

## Limits and remaining gates

The blind Wave 3 result measures a deterministic route with curated structured inputs, not a new live extraction study. Procedural AI independence is not human/institutional independence. No corpus-wide mathematical guarantee follows from zero wrong-served on 144 cases. F2–F5 and ten negative reason disagreements remain open. No provider evaluation, production migration, UI redesign or new repair wave is included.

Normal push, three-way remote SHA verification, scoped cleanup, ACL residuals, root dependency checks and final status are appended in `closure.md`. Unrelated historical worktrees are protected.
