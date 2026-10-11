# Geometry library expansion — LOCAL verification report

Status: IMPLEMENTED_VERIFYING_FULL_REGRESSION. Final decision follows the fresh
clean regression journal; this draft does not yet claim the full gate passed.

## Identity and scope

Isolated branch `feat/geometry-library-expansion`, base2990d87d, implementation
a0eb1450; verification tooling3b6104e3. Registry24→27 entries (geometry-functions/3),
Engine geometry-function-engine/2, existing Planner geometry-fact-planner/2.
Four production files changed: registry.py, engine.py, planner.py and fact_extraction.py.
No new authority; existing exact Kernel, metric, IR interpreter and Scene3D reused.
Main remains28ac1d61; original branch stays feat/text-to-geometry-functions at2990d87d.
Default LLM_ONLY and cache125 unchanged. LIVE Gemini/paid API calls=0.

Locked A/B candidate: `12da4768495572d7b4d04af733edf0c787337a6ab486ce2cae42f7c94bbbce52`.
NEW branch candidate: `8ff994c6e20ab982abd208dd8127cd6471bcc56509fd1809433e7a8f5f3601dd`,110 files;
see BRANCH_CANDIDATE.json and candidate_divergence.json. They do not authorize a pilot
or change historical experimental results. The old protocol, runner, corpus and run stay intact.

## Capability matrix: before → after

The full pre-change audit remains in [audit.md](audit.md). A Kernel capability
alone did not establish a served A/B construction; this table records that boundary.

| Capability | Before, shared A/B library | After, actually tested | Layer / remaining gap |
|---|---|---|---|
| Unique line-line point | Kernel/IR existed; no registry/B point kind | intersect_line_line through A calls and B point_def | Exposed/composable; skew/parallel/coincident safely refuse |
| Unique line-plane point | Kernel/IR existed; no registry/B point kind | intersect_line_plane through both adapters | Exposed/composable; contained/parallel/degenerate planes refuse |
| Point-line projection | Kernel/project_onto existed; no library entry | orthogonal_projection_line; B dispatch by two-point target | Exact Gram-aware construction; zero line refuses |
| Point-plane projection | Existing orthogonal_projection normalized a known foot; arbitrary new image unresolved | Existing API constructs derived image once source/plane ready | Preserves inverse known-foot behavior; degenerate/noncoplanar targets refuse |
| Midpoint → intersection → projection → measure | Missing two constructive links | Complete dependency chain in both arms | Order permutation tested; unresolved/cyclic dependencies refuse |
| Output coincides with existing point | No general projection construction | Distinct derived label may have equal coordinates | Provenance remains DERIVED; same-name plane API remains precondition refusal |
| Existing solids/base charts/measures | Narrow capabilities in audit | Regression only; no new family claim | Rhombus/trapezoid and oblique charts not added |
| Plane-plane output / full sections | Lower-level primitives exist | Not exposed by this task | Line-object expression/orchestration still missing |
| Angle / two-nonpoint distance annotations |10 ANNOTATION_UNBOUND across5 frozen sample problems×2arms | Unchanged, separately classified | Display-anchor gap, not automatic math failure |

## New cases correctly constructed

Independent square pyramid oracle: physical A=(0,0,0),B=(2,0,0),C=(2,2,0),D=(0,2,0),
S=(0,0,3); chart metric diag(4,4,9). Output coordinates below are oracle/engine
comparisons, never coordinates passed as facts for the output point.

- AC∩BD gives O=(1/2,1/2,0), physical OA²=2.
- SC∩(ABD) gives H=(1,1,0), coincident with C but independently derived.
- D projected onto AC gives H=(1/2,1/2,0).
- D projected onto (SBC) gives H=(9/13,1,4/13), physical DH=6√13/13,
  physical HA²=88/13. Quantity/witness annotation is separately tested.
- Projection already on target yields a distinct derived image with zero distance.
- Midpoint M of SA → P=SD∩(MBC) → H=P projected onto BD → derived measure.
- Non-diagonal Gram triangle projection, and prism projections with pending top
  vertices/source points, resolve via existing dependency progress rather than a new solver.

Every constructed point has DERIVED provenance, producer, source/dependencies and
relation_verified trace. Actual intersect/project IR is emitted and executed; no
coordinate declaration impersonates a source premise. Conflicting definitions refuse.

## Tests and review evidence

- Preregistration:58 RED before production (4e2b3fb1, diagnostics/red.json).
- Current feature suite:91 PASS (diagnostics/expansion.xml). Both real route
  adapters use independently handwritten fake A calls/B facts, not B converted from A.
- Negative: no intersection, infinitely many, skew, zero line, collinear/noncoplanar
  plane, missing/cyclic operands, inconsistent outputs and source-role mismatch.
- Source: goals, negation and conditional antecedent/consequent cannot become premises.
  Known-foot inverse wording is preserved. Exact object-binding and observation≠proof remain.
- Metamorphic: prime/indexed renaming, scale3, call/fact permutation, swapped
  intersection operands, idempotent projection and non-diagonal metric.
- Five in-memory behavioral mutants killed: source binding removal, wrong projection
  parameter, lost Gram context, relation verification bypass and lost trace provenance.
- Fake certification:74 calls (37A+37B),14 oracle positive outcomes; network/live0,
  offline-certification/certification.json. This is not smoke/full pilot or model quality.
- Independent review: three initial findings plus pending-F prism variant reproduced
  and fixed; follow-up found no blocking issue,91 feature tests and5 candidate tests PASS.
- Candidate tooling:5 new tests for read-only selector, drift/missing rejection,
  write rejection and exact product-path provenance;30 candidate/diagnosis tests PASS.
  Default verification still uses the locked candidate and correctly detects divergence.
- Full backend clean regression: PENDING; unsuccessful attempts are not readiness.

## Renderer and visual verification

34 frontend tests PASS:8 new scenes through veKhongGian/buildObject3D,3 existing
chart tests and23 annotation tests; TypeScript build PASS. Checks cover Euclidean
positions, line/plane operands,5 pyramid faces, edges, point labels and provenance,
plane equation and HA²=88/13. Renderer product source is unchanged.

Browser: actual Scene3DWorkspace on localhost, external requests blocked,8 scenes
(A/B×4 primitives) at1280×900, point selected; derived label inside canvas,1 WebGL
canvas,0 fallback each. Plane-projection mobile390×844 also displays H,1 canvas,
0 fallback. Console0 errors/0 warnings;0 page errors in the measured loop.
Screenshots diagnostics/scene-{0,1,2,3,7}-desktop.png and plane-projection-mobile.png
were inspected by the agent: intersection/foot present, solid edges/faces and labels
visible; A/B plane images agree. Extended target lines and translucent planes can
fill/clamp the viewport; that is the existing representation, not hidden math repair.
The harness asks volume for these captures; derived-length annotation coverage comes
from the backend/frontend tests, not a claimed browser witness screenshot.
Human visual acceptance NOT_PERFORMED. No full production UI or model journey claim.

## Limits, refusals and next expansion

Source matching is a bounded Vietnamese grammar, not a generic language parser.
Unrecognized role wording refuses; alternate reordered plane-name wording is not
claimed. Plane operands require first3 labels noncollinear and all additional points
coplanar. Same-name plane projection is rejected by the legacy precondition even if
geometrically valid; a separate output label is supported. No general proof engine.
Data missing/contradictory is distinguished from capability and display gaps.

Old ANNOTATION_UNBOUND angle/two-nonpoint anchors remain; do not convert them into
mathematical errors. General sections, plane-plane line objects, rhombus/trapezoid and
oblique-prism constructive layouts remain outside this task. Next slice should audit
typed line-object composition/section needs or base determinacy with new oracles,
not add per-problem templates. No generality or population-safety conclusion is supported.

Expanded provider payloads also diverge. Under the existing local byte estimator and
output3072, proposed current surfaces reserve SMOKE536172 tokens/USD0.3230532,
FULL6431706 tokens/USD3.875931; these exceed the old500k/6M accounted-token caps.
Even output2048 exceeds token caps. Do not change the locked runner/protocol to hide
this, pool smoke/full, or run either mode. Provider-bound prompt estimator is still
unverified, historical persistence failure cause UNKNOWN; separate approval and a
new budget/identity review would be required for any real API request.
