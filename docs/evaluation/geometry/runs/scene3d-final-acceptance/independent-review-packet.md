# Independent review packet

**INDEPENDENT_REVIEW_PENDING. HUMAN_VISUAL_APPROVED=PENDING.** No Owner-appointed independent reviewer has reviewed this candidate.

Product `b8b3311b`, freeze `c84e8620`, branch `research/scene3d-visual-correction`. Main `9978e512` is unchanged. Current continuation changes evaluation/docs only; root research checkout is protected. Exact source hashes, T3 receipt/stream validation and served-module identity are in `provenance-verified.json`; final package hashes are in `artifact-manifest.json`.

## Review inputs

- Product diff: `git diff 9978e512 c84e8620 -- frontend/src frontend/vite.config.ts`; include the earlier renderer changes and Mode B fix, not just the evaluator diff.
- Evaluation delta: `git diff 16b46d38 -- frontend/scripts docs/CODE_INDEX.md docs/EVIDENCE_INDEX.md`; untracked run files must be included if reviewing before the evaluation commit.
- Requirements: Owner attachment, `plan.md`, prior `../scene3d-visual-correction/FINAL_OWNER_HANDOFF.md` and current `report.md`.
- Evidence: `baseline-final.json` (4/1/25), `faults-final.json` (10/10 on certified views), `motion-summary.json`, corrected `label-controls/receipt.json`, `visual-review.md`.
- Fresh tests: Node 40/40 (`oracle-tests.log`); existing product material/presentation/annotation tests 82/82. Prior frozen Full T3: pytest 11923 passed / Vitest1378 / build PASS; hashes revalidated, no new T3 run.

## Required independent checks

1. Source/provenance: authoritative point/plane/section names, certificates, exact geometry, honest refusal, no fixture-name hardcoding.
2. Solid faces versus curved occlusion and presentation-plane boundaries: distinguish physical edges, intersection/section boundary, construction segments, free curves, plane display border and silhouette. Keep the Owner's provisional split convention; flag inconsistent mathematics before any broad rewrite.
3. F2: normal/hover/selected fill and boundary; previous section loses cobalt after selecting another item; polygon/circle/ellipse consistency; small other region cannot hide a stale selection.
4. Locked official 7/8 and V2 independence/observability: do not infer that more tests override the gate. Examine the analytic ellipse interval failure and missing dash-bound certification.
5. Mode A/B under the locked reveal contract, point/plane prime names, no invented labels, square markers only from certified relations with correct foot/operands.
6. Label traces and camera crossing: evaluate the 112 heuristic jump flags, test unobserved frames, isolate hover from camera allocations. CPU observations do not establish a performance guarantee.
7. Hybrid impact: renderer presents backend facts; `/4` view and future H1 must not rederive geometry, change default routing or use live providers.

## Internal AI review disclosure

One fresh-context internal reviewer read the evaluator delta. It found five Important issues: hidden polygon local gaps bypassed; `polygon3` omitted from other-boundary checks; missing parent invented visibility; complete masking misclassified as FAIL; motion PASS ignored failed controls. All received conservative fixes. Review follow-up found malformed faces could still reach V1; bad index and degenerate-face RED regressions now pass with explicit rejection. The reviewer ran 38 tests before the final two malformed-face regressions; the author ran the final 40. No false claim of a final independent PASS.

The original motion wrong-name control also failed because substring matching admitted A/O in its control text. The failed attempt remains; a separate exact-token control run detects wrong names 18/18 and second selections 18/18. Product files were not changed for these fixes.

## Decision requested at the Owner gate

Assign an independent reviewer and review the short image set. Keep NO-GO merge until the official F2 gate has an approved resolution, the transition/continuity gaps have an accepted disposition, and human visual approval exists. This packet is ready to review; it does not request authorization to merge, push or enable Hybrid now.
