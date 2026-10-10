# Geometry library expansion — capability audit and proposed bounded design

Stage: CAPABILITY_AUDIT_DESIGN_PENDING_APPROVAL. Implementation has not started.
This is not the requested final handoff GEOMETRY_LIBRARY_EXPANSION_AWAITING_REVIEW.

## Pre-flight and isolation

Base2990d87de861f03b31dd9e7310c50de59bcaf868; product/safety sourcecfe2ada5; verified evaluation source2f1b457c.
New LOCAL branch feat/geometry-library-expansion at .superpowers/worktrees/geometry-library-expansion.
The explicit user base choice overrides the usual main-only branching rule; no branch is merged or rebased.
Original worktree remains feat/text-to-geometry-functions and retains the user's untracked favicon.

Frozen A/B candidate12da4768495572d7b4d04af733edf0c787337a6ab486ce2cae42f7c94bbbce52 matches actual product hash.
Preflight verifies48 LF-normalized artifact hashes, preserved full XML8068 PASS/1 skip/2 deselected and fake24+288/network0/live0.
These are verification of old evidence, not new full-suite or fake measurements.
Fresh clean-base regression:344 PASS/0 fail/skip/deselected,47.26s; kernel/section/annotation baseline107 PASS,2.51s.
Journals: diagnostics/baseline.xml and diagnostics/kernel-scene-baseline.xml.

CORE: reusable geometry construction, not evaluation infrastructure expansion.
Sources of truth: code/tests, TEXT_TO_GEOMETRY_FUNCTIONS_DECISION.md and its contract.
Reuse Registry/Engine, existing planner, kernel, metric, interpreter/IR and Scene3D; no second authority.
Potential production touchpoints after approval: geometry_functions/{registry,engine,planner}.py,
existing neutral IR builders when a helper is actually needed, related source-binding/route tests.
No adapter transport, runner, default route, kernel mathematics, legacy compiler or renderer rewrite is proposed.
Provider-facing A/B surfaces will diverge on this NEW branch if functions/schema are extended. That does not authorize
refreezing the old candidate, reusing locked runner identities or rerunning old measurements.
Record the new measured hash and declaration additively in this run; keep old candidate bytes unchanged.

## Capability matrix BEFORE (AFTER currently identical: no implementation)

Evidence categories distinguish capability layers; a tested kernel does not establish a served function-route problem.

| THPT capability | Kernel / IR / Scene3D | Shared library / A / Hybrid B | Gap classification |
|---|---|---|---|
| Triangle from3 sides or right angle +2 dimensions | Exact affine Gram and common IR | Supported by current engine;344 regression includes it | Existing verified narrow capability |
| Regular triangle/square/hexagon | Exact rational Gram charts, displayed through chart_metric | regular_polygon;3/4/6 only | Existing verified narrow capability |
| Other regular polygons | Rational-Gram restriction; no approximation | UNSUPPORTED_REGULAR_POLYGON | Missing exact representational capability, not missing question data |
| Rectangle / cube / cuboid | Polygon/prism IR, faces/edges/labels | rectangle / regular_polygon / right prism; exact binding safety tested | Existing verified narrow capability |
| Rhombus or general trapezoid | Generic polygon exists; right-angle-chain kernel exists for a narrow trapezoid subset | No shape fact/schema or engine base chart for these | Missing expression + layout integration; do not claim kernel missing |
| Pyramid with a determined foot/height | Same exact Gram, pyramid IR | pyramid / regular_pyramid / altitude and normalizing relations | Existing; missing foot/dimension safely refuses |
| Right prism, including supported regular bases | Translate/prism IR and metric | prism right=true supported | Existing verified narrow capability |
| Oblique prism | Existing translate/vector IR and legacy oblique-prism work | right=false encodable, but _mot_buoc only constructs right prisms | Primitive exists below, missing determined-shift composition at function boundary |
| Midpoint / triangle centroid | Existing point IR | midpoint / centroid, dependency loop | Existing; centroid of arbitrary polygon not supported |
| General division ratio | divide_segment kernel and IR | No registered function or point-kind | Missing exposure/composition |
| Point projection onto a plane | Metric-aware project kernel + project_onto IR | orthogonal_projection mostly normalizes a known foot/normal; cannot construct arbitrary new image | Missing construction composition, not missing mathematics |
| Point projection onto a line | Metric-aware kernel + same project_onto IR | No registered function; B currently maps projection to plane API | Missing exposure / typed operand dispatch |
| Unique line-line / line-plane intersection | Exact kernel; existing intersect_* IR, point scenes | No registry functions or B point definitions | Missing exposure/composition |
| Plane-plane intersection line | Exact kernel + line-result IR and line scenes | No registry/planner line-object construction | Missing line-object composition; defer this bounded slice |
| Plane section of a polyhedron | Existing section kernel, ConstructSectionStmt, ordered section edges/region;107 baseline includes checks | No function/planner section subject; ask_area currently needs point-label polygon | Missing shared-library expression and orchestration, not absent section algorithm |
| Length / volume / area / point-plane distance / skew-line distance / line-plane and plane-plane angles | Existing metric-aware measures / quantities | Seven ask functions supported in current bounded layouts | Existing verified narrow capability; rendering anchors are a separate layer |
| Curved solids / curved sections | Existing legacy IR/kernel capabilities outside this audit's107 tests | Not in24-function registry or current finite layout | Not audited here; missing library exposure, not a claim of absent legacy mathematics |
| Insufficient or contradictory source | Fail-closed geometry and source gates | MISSING_DIMENSION / UNDERDETERMINED_POINT / INCONSISTENT_FACTS, proof-only UNVERIFIABLE | Genuine data insufficiency/contradiction must not be disguised as a library gap |

Registry contains24 entries, not the original16-entry historical slice. CODE_INDEX's detailed B checker summary still
mentions old PROOF_GOAL_FALSE / negation-as-inconsistency semantics; actual function_route now separates configuration
observation and proof UNVERIFIABLE. This stale description does not alter current code or the frozen correction report.

## Reproduced capability counterexample

Probe: diagnostics/probe_capabilities.py; result diagnostics/capability-probe.json.
Square-base pyramid with affine S=(0,0,1), A=(0,0,0), B=(1,0,0), C=(1,1,0), D=(0,1,0),
G=diag(1,1,2). These are independent diagnostic oracle coordinates, not coordinates accepted from an AI.
The foot of D on (SBC), whose covector is(1,0,1), is uniquely H=(2/3,1,1/3):
H=D-(-1)/(3/2)*(1,0,1/2). Independent literal equals the existing kernel.
Projection of D onto AC is(1/2,1/2,0).
A's existing orthogonal_projection nevertheless refuses UNDERDETERMINED_POINT for the new image H.
B does the same: diagnostics/projection-b-probe.json. Its base facts are mechanically converted A facts;
this diagnostic is not independent extraction-quality evidence.

## ANNOTATION_UNBOUND reconciliation

Inspect only frozen FULL sample1:46 served case/arm scenes;10 diagnostics across5 problems x2 arms.
Six: angle_cos_sq has no registered anchor (X02,H03,H11).
Four: distance between two non-point objects has no registered anchor (X04,H12).
The quantity remains in the details panel. quantity_annotations._DO does not register angle_cos_sq and explicitly
declines distance pairs with no point operand. Classification: display-anchor gap, NOT a mathematical error.
No diagnostic is deleted or rewritten. These existing anchor gaps are deferred; new derived-point scenes must still
verify point IDs/labels, witness binding, faces/edges and metric independently.
No browser or human visual acceptance has been performed in this audit.

## Proposed selection: two reusable primitive groups

1. Unique POINT intersections: intersect_line_line and intersect_line_plane.
   Typed point labels and line/plane operands; no injected result coordinates. Defer plane-plane line output and full section
   API because they require an additional object/subject integration slice. The two point primitives support diagonal
   intersections, side/plane constructions and chains of section-point constructions, without claiming general section support.
2. Constructive orthogonal projections: extend the existing plane projection when its input point and plane are already
   determined; expose point-to-line projection. Preserve the old inverse-normalization path when the image is a known foot
   used to determine an apex. B extends its current operand-type dispatch and point-definition mapping, not a new planner.

These two beat adding solid templates: both reuse exact kernel authorities and benefit pyramid/prism/cuboid constructions
and distance tasks. Alternative1: full section/line-object API is valuable but broader. Alternative2: rhombus/trapezoid/oblique
charts first would improve base coverage but need new source-dimension and determinacy contracts. Defer both alternatives.

Dependencies: only execute a new construction once all operands are determined. Preserve topological trace/provenance,
reject duplicate conflicting point definitions, preserve metric context, and emit actual derived IR (not coordinate aliases).
Source gate must bind every operand/output role to the cited premise and retain goal/conditional/negation fail-closed rules.
Expected schema extensions are confined to the existing Registry and TypedFact models and existing mapping rules.

## Verification contract to preregister AFTER design approval, BEFORE production edits

Register literal independent Euclidean/Gram oracles and negative labels in NEW fixtures/run inputs, then commit RED tests.
Positive oracles cover foot on tilted plane, foot on a diagonal, diagonal intersection and line crossing a tilted plane;
also chained midpoint -> intersection -> projection -> quantity, renamed/prime labels, scaled dimensions and permuted calls.
Negative cases: parallel/no intersection, coincident/infinite intersection, skew lines, collinear plane, zero line,
unknown operands, inconsistent alternate definitions, insufficient base/height, wrong source object, conditional/negated/proof
premise. No expected coordinate/value may be generated by importing the product kernel into the independent oracle.
Mutation removes the operand/source guard, changes a projection parameter, or drops metric context; each must be detected.
Metamorphic checks: rename invariance, square/cubic quantity scaling, idempotent projection, unordered intersection operands,
dependency permutation, Euclidean coordinate oracle versus affine Gram scene metric.
Check both real A/B adapters with handwritten NEW fake fixtures, Registry/Engine parity and full backend clean regression.
Reused legacy A/B fixtures may be read for regression only; they must not be rewritten, rescored as a new pilot, or pooled.

Scene verification must cover point/edge/face identity, labels, annotation anchors/witnesses, formation order and real renderer
metric. Browser screenshots/visual inspection are a separate gate; NOT_PERFORMED remains explicit until performed.
Do not expand angle or two-line distance anchors merely to remove their old diagnostic.
Before final handoff: new branch product hash/declaration, frozen A/B byte preservation, main/default unchanged, user files
preserved; report BEFORE/AFTER and remaining gaps. Intended final status is GEOMETRY_LIBRARY_EXPANSION_AWAITING_REVIEW.

Skills: brainstorming enforces the pending short-design approval gate. using-git-worktrees isolated this branch;
Karpathy/ponytail focus the proposal on existing authorities. graphify inspected, but no prebuilt graph exists:
direct code/test/index evidence used, no graph rebuild/provider extraction. Local Claude skills installed include
diagnose, graphify, review, tdd; project .claude/skills includes impeccable and playwright-cli.
No UI redesign is requested, so impeccable is not applied; browser skill belongs to later approved visual verification.
LIVE GEMINI CALLS=0; paid API calls=0; MAIN/default unchanged. No implementation approval is fabricated.
