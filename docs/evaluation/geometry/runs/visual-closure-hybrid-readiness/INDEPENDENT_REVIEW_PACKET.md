# Independent review packet — PENDING OWNER-APPOINTED REVIEWER

No independent review has been performed for this change. The author did not appoint a subagent or treat a self-review as an independent verdict. Human visual approval is also pending.

## Identity and review material

- Base: `1a4a0b93747143b2574d0196703aad9f454c4164` on the existing integration candidate.
- Product commits: `956b77f8` and `53fe3d25243fe1e99410dfc52546e16225f19e75`.
- Final freeze: `c84392c15dbd08e4a59a6083ace17b577b8b2cb7`; measured hash `8be632679307a94ce4525ad576a05a9eccffc8ba2bdbf02d4c7dc93c208b7c41` (118 files; scope excludes geometry frontend).
- `verification/full-product.diff`: complete backend/frontend change from base; the Git bundle in the handoff preserves all commits, docs and artifacts. Reproduce with `git diff 1a4a0b93..53fe3d25 -- backend frontend`.
- RED/GREEN: the three JSON receipts at run root and `verification/hover/`, `verification/section-role/`.
- Full tests: `verification/full-t3/receipt.json`, original sanitized browser receipts, `OFFICIAL_SUITE_F1_F2_REPORT.md`.
- Screens: `verification/owner-camera/`, official scenario screen paths and before/after comparisons in the Owner report. The pre-change package remains in `../visual-hybrid-final-corrections/`.
- Capability audit: `catalog-audit.json`, `capability-probe.json`, `capability_probe.py`, and the 18-family matrix. These are offline authored probes, not model/holdout evidence.

## Questions for the reviewer

1. Does formula suppression require the same entity/alias and actually visible coherent formula? Are non-final Mode A formulas and final-answer disclosure retained? Does separating the analysis CSS class retain every explanation and avoid an inspector-selector collision rather than weaken an oracle?
2. Do section defaults stay terracotta and target borders cobalt, including polygon/circle/ellipse paths? Does hover remain transient, clear on leave/drag, and leave selected state and source geometry untouched? Check picking specificity, edge proxies and listener cleanup.
3. Do geometry, provenance, causal closure, refusal, camera-dependent dash signatures and backend cache behavior remain unchanged? No backend/app files changed; the 49 rebound fixture envelopes and all scenario expectations are equal to their prior versions.
4. Does the F2 evidence really isolate orange semantic fill from numeric-data roles? Is the projected-edge supplemental detector independent enough? Its broad boundary-pixel census failed fault discrimination; the per-edge proposal detects a magenta GPU fault at both viewports. Neither proposal changes the locked official rule.
5. Do the sphere captures justify the explicit residual findings? There is no claim of P3 closure or source-grounded sphere support, despite removing decorative loops.
6. Are suite transport adaptations limited to Chrome/CDP lifecycle and artifact location? The native port driver had startup failures; Playwright transport executes unchanged suite assertions. Check that all eight scenarios/viewports and refusals are represented without silently counting incomplete attempts.
7. Are the 18-family labels scoped to full HTML configurations and not inflated by kernel primitives, renderer support or authored facts? New prism cases are not blind holdout or extraction evidence.
8. Are all UNKNOWN/NOT_RUN states honest, with no independent/human approval or Hybrid-default readiness inferred from machine tests?

## Reproduction and governance

Use a clean detached checkout at the final freeze. Existing Python 3.12 environment and frontend dependencies may be reused; do not call a live provider. Set `ALLOW_LIVE_AI=0`. Browser transport source, fixture rebinding checks and test harness sources are included. Raw test tracebacks remain ignored scratch; tracked receipts contain exit codes, summaries and SHA-256 values.

The own clone exists because root `.git` ref creation was denied. Its object store references the original repository read-only. Root checkout and the original candidate were not edited. Main remains `9978e512`. Do not merge/push/enable Hybrid from this packet. Reviewer should author a separate verdict; no verdict file or approval is pre-filled here.
