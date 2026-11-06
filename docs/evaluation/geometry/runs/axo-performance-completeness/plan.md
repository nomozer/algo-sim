# Axo performance and completeness implementation plan

**Goal:** Diagnose and improve orbit/step latency, restore requested verified conclusions at the final step, and audit cross-family interactions without changing the Axo design.

**Architecture:** Keep the authoritative Scene3D/kernel boundary. Reuse renderer pooling, edge visibility, semantic lifecycle, pedagogical plans and existing browser tooling. Optimize only costs identified in production profiles; retain camera-dependent hidden lines.

**Spec:** User attachment “AXO — FINAL PERFORMANCE, PEDAGOGICAL COMPLETENESS & CROSS-FAMILY ACCEPTANCE”, received 2026-11-04. Sequential execution in the existing integration worktree is explicitly authorized.

**Constraints:** Preserve frontend/index.html SHA256 3B8A5566454E42BA624C4611C82B792EC8ED1CAFC062C0041ADC11DEEB44A69F. No backend changes, provider calls, merge, push or automatic human approval. Preserve earlier evidence. Missing measurements remain UNKNOWN/NOT TESTED.

**Review focus:** Shared GPU resource lifetime; future objects and backward scrubbing; camera/damping snapshots; requested results versus intermediate spoilers; mobile object cards and history restoration.

- [x] A: Create clean detached baseline at 4ed8cb3e. Build production. Measure six families with 15-second continuous orbit, reversal/zoom, selected/hidden/isolated/panel/step/navigation variants. Save raw samples, CPU/React/GL counters and Chrome traces. Identify actual CPU/render/control causes.
- [x] B: Add regression demonstrating measured geometry/resource churn; minimize root-cause changes while preserving hidden-edge correctness. Remeasure identical step and orbit scripts; check resource bounds.
- [x] C: Audit exact requested outputs, sphere d=0/<R/=R/>R and all other families. Test verified final conclusions before implementation; reuse goal completion and exact formulas, with no frontend coordinate/answer invention.
- [x] D: Verify cards, X/IX, hide/isolate, Undo/text editing, camera/panels, Play/Pause, canonical/legacy URL, Back/Forward/F5 and seven widths plus 110% browser zoom. Preserve visual style.
- [x] E: Only after A–C, assess loading/navigation costs; change loading strategy only if evidence supports it.
- [x] F: Run existing frontend and appropriate offline backend suites, mathematical assertions, production browser acceptance and visual review (three angles for hidden-line/section scenes). Record failures and limitations individually.
- [x] Report: One report.md with repository, root-cause table, symmetric statistics, mathematics/pedagogy table, visual evidence, regression and PASS/PARTIAL/FAIL/NOT TESTED conclusions; register in EVIDENCE_INDEX and update CODE_INDEX for changed responsibilities.

**Preflight:** integration/axo-pedagogical-construction-hardening, HEAD 4ed8cb3e262280fe3bf6caab0045185a9bc0e52d; only frontend/index.html dirty. Root main bb61a804 is a different, newer backend lineage; do not copy backend changes between them. No existing graphify-out/graph.json; use CODE_INDEX and direct callers, no graph rebuild needed for this task.
