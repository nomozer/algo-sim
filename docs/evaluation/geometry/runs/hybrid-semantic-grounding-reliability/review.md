# Independent read-only review — 2026-10-17

Reviewer: separate Codex agent `grounding_review`, fresh context, repository access, offline probes; no product edits or provider calls. Reviewed the interrupted diff and connected Registry/Engine/route/planner code, then every product delta. Full suite and live extraction were not independently rerun by this reviewer.

## Findings and disposition

1. **Important, wrong source plane:** source `ABMS` and extraction `ACBM` shared collinear A/B/M; both groups were coplanar but named different planes. Original interrupted code served `cos²=8/17` instead of source `13/17`. Closed: `_cung_mat` requires complete-set containment; engine validates nondegenerate, coplanar groups on both sides. Supplemental regression.
2. **Important, spelling bypass:** bare `SABC`, `mặt bên SABC`, `mặt đáy SABC` bypassed the new explicit-plane collector and served as SAB. Closed: source plane captures come from the shared ask/section/intersection grammars, including 3-label degeneracy. Direct A and fact B probes refuse; valid SAB serves.
3. **False refusal, symbolic cube:** `cạnh 2a` lost its symbolic flag in the reused shape reader; M4's comparison refused. Closed for this spelling by comparing exact squared magnitudes after exact source-value binding. Reviewer confirmed mismatched `2/2a`, `2a/2` still refuse; Engine rejects mixed unit scales. Existing reader limitation `2a√2` remains declared, not claimed supported.
4. **Important delta, extra call-plane labels:** source ABC, extraction SABC passed symmetric containment; angle IR used the first three call labels. Closed: validate every complete `plane`/`plane1`/`plane2` operand before IR. Both angle families, direct A and fact B tested RED/GREEN.
5. **Historical M1 regression:** derived-plane section area was validated but did not publish its answered span. Existing two-line test RED; minimal optional span plumbing to existing binders GREEN. Reviewer probes: valid section serves; unextracted extra volume refuses; a construction without its area-answer call cannot forge area coverage.

Final reviewer verdict: **no remaining critical or important finding in the reviewed delta**. No universal safety or natural-language coverage claim follows.

## Final reviewed product hashes (working bytes at review, before Git CRLF conversion)

- Registry SHA-256: `4fce67c52896b07b8c0feca8f3f17eac04655603c7924c5f17641a2af0dc2eae`.
- Engine SHA-256: `095f954e3513379ac0c54dc90ad70b806b1e29d7abac3b9f3ecaab5357e0be7c`.
- Product checkpoint: `94b3437b`; final candidate normalized tree hash: `57c7f5dbedaa7b21c66345fa4d6f0e1ea461a425293d44035b5678e12d76f96e` (110 files).

Six old wording controls used incomplete extractions for multi-request sentences. Their tests now explicitly reject the incomplete extraction before supplying the missing asks; original numeric assertions remain. For `từ đó suy ra thể tích`, even complete extraction is refused by existing goal-clause policy; the explicit `từ đó tính thể tích` positive control verifies both answers. Frozen corpus/oracle labels and inherited xfail markers were not edited.

The first unseen measurement preceded a later fix driven exclusively by historical section regressions. Subsequent unseen runs are **remeasurements**, not a fresh final holdout; no human held-out claim is made.
