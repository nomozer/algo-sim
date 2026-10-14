# Source-bound result planning — implementation plan

Contract: locked `../goal-directed-planner-generalization-audit/next-slice-preregistration.md`
and its `next-slice-corpus.json`. User explicitly approved implementation on 2026-10-14.
Branch starts at audit commit 19140e2f, a descendant of main 2a3c0787.

1. RED: run the six positive / twelve negative locked fixtures on the real fact route.
   Expected: unsupported line_ref schema prevents serving the positive cases.
2. Extend existing TypedFact/result arguments, Registry planning effects/source certificates and
   existing Planner bounded resolver. Test catalog order, effect selection, supplied producers,
   foot reuse, labels, provenance, role/type/source adversaries and budgets before implementing.
3. Extend the existing Engine line table/dependency/IR emission; reuse Kernel and exact metric.
   GREEN: correct lines/feet/answers/DAG/Scene3D, six positive and twelve negative.
4. Audit fake-provider extraction, intentional A/B surface changes, default/cache isolation;
   run existing regressions and historical benchmark without relabeling evidence.
5. Independent LOCAL read-only review after final product fix; RED/GREEN for blockers.
6. Product commit, new candidate freeze/correction layer; clean detached T3 and related browser
   gates. Publish receipts, living docs and handoff on this branch only.
7. Remove only owned temporary worktrees/junctions/DB/browser/server/scratch with no consumer.

Shared interfaces: line_ref is a fact ID in TypedFact and a validated producer call ID in Registry;
Engine consumes that same binding. PlanningContract is internal metadata, excluded from provider
declarations. Planned effects grant no source/geometry authority. Scene3D consumes existing verified IR.

No Group B, new Geometry Function/Kernel/DSL/FactGraph/Planner/UI implementation, live Gemini,
main merge or push. Cache change or architectural expansion is a stop condition.

Review focus: source-reference spoofing; proof/negation/conditions; lost givens; infinite line versus
segment; duplicate/cyclic producers; cost selection from effects; exact Gram; trace order/identity;
partial serving at a budget; default-route import/cache isolation.
