# Slice 1: sections and intersection lines on the Hybrid route

- Approved by the user on 2026-10-11 ("S0 now, then slice 1").
- Recommended by [`hybrid-simulation-capability-audit`](../hybrid-simulation-capability-audit/report.md) §8.
- Branch `research/hybrid-simulation-capability-audit`, LOCAL, not merged. LIVE GEMINI CALLS = 0. Default `LLM_ONLY`.
- Prerequisite S0 is done: [`hybrid-gate-clause-role-fix`](../hybrid-gate-clause-role-fix/report.md).

## Problem and root cause

- **Problem:** requests such as "Xác định thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (MAB)", "Tìm giao tuyến của (SAB) và (SCD)" and "Tính diện tích thiết diện …" were refused (`OUT_OF_SCOPE`).
- **Not a missing primitive:** the shared engine already builds and renders them (the audit probe proved this).
- **Root cause:** the Hybrid route had no way in — no Registry function, Typed Fact kind or planner rule.

## Change

| Layer | Change |
|---|---|
| Registry (route A surface) | `section(solid, plane)`, `intersection_line(plane1, plane2)` (construct); `ask_section_area(solid, plane)` (ask). Cues "thiết diện" / "giao tuyến" / "diện tích"; every plane must be named in the quote. 27 → 30 functions |
| Typed Facts (route B surface) | kinds `section`, `intersection_line`; a question of `area` with `solid` + three plane points maps to `ask_section_area`; one extraction-prompt rule |
| Planner | one-to-one mapping; no search |
| Engine | emits **existing** IR: `construct_plane` + `construct_section`; `assign` + `intersect_plane_plane`; `measure area`. One section object per (solid, plane) even when it is both constructed and measured. Pre-check `PARALLEL_PLANES`, kernel codes for degenerate planes, `SECTION_EMPTY` after execution |
| Not changed | IR, kernel, interpreter, Scene3D, frontend |

**Provider surfaces, changed by design and pinned in `test_provider_surfaces_are_pinned`:**

| Surface | Before | After |
|---|---|---|
| A | `1e3f71ea…` | `912b22ef…` |
| B | `a4f368cb…` | `396f1c9c…` |
| function declarations | `41e090cd…` | `f2ec9698…` |

The frozen A/B pilot surface is unaffected: pilot readiness stays NO-GO, as its test asserts.

## Evidence

Evidence classes: offline typed facts and route-A calls. There is no fake-provider run for the new kinds, no real model, no browser rendering and no human review.

**RED at `f261e9e7`** (the code without the slice, in a clean worktree): 14 failed, 2 passed ([log](red-at-f261e9e7.txt)). The 2 that already passed are refusals that hold either way.

**GREEN.** `test_hybrid_section_slice.py`: 19 passed. Results against the oracle:

| Case | Oracle (Euclidean, hand-derived) | Result |
|---|---|---|
| (MAB), M = mid SC | trapezoid A, B, mid SC, mid SD; S² = 117/16 | equal |
| (SAC) | triangle S, A, C; S² = 18 | equal |
| (MNP), midpoints of SA, SB, SC | square through the four lateral midpoints; S² = 1 | equal |
| cube (A'BD) | equilateral triangle; S² = 12 | equal |
| section only, no question | served as a simulation (scene `section` → `polygon`, 4 vertices) | equal |
| renamed T.MNPQ + reversed order | S² = 117/16 | equal |
| giao tuyến (SAB) ∩ (SCD) | line through S parallel to AB | equal |
| giao tuyến (SAC) ∩ (SBD) | line through S and the centre | equal |
| (MNP) ∩ (ABC) | parallel ⇒ refused | `PARALLEL_PLANES` |
| collinear plane points | refused | refused (kernel code) |
| "Chứng minh rằng thiết diện …" | refused | `GOAL_CLAUSE_NOT_PREMISE` |
| "Nếu thiết diện … thì …" | refused | `CONDITIONAL_CLAUSE` |
| plane not named in the quote | refused | `PLANE_NOT_IN_QUOTE` |
| no "thiết diện" cue | refused | `PREDICATE_NOT_IN_QUOTE` |
| "Diện tích thiết diện … bằng 3" | refused | `NOT_ASKED_IN_SOURCE` |
| route A `ask_section_area` | S² = 117/16 | equal |

**Mutants:** 3 source mutants killed — the parallel-plane pre-check dropped, the section built twice, the section area routed to polygon area.

**Regression:**
- Hybrid/route-A cluster (14 files): 720 passed, 5 xfailed.
- 30-case benchmark: rows byte-identical. B23 stays refused because its pre-registered facts are typed `unsupported`.

**Gates:** candidate `5a8e0ff6…` (product `eeceefbc`, refreeze `3e0eebc8`), declared in [`candidate_divergence.json`](candidate_divergence.json). T3: see `run.json`.

## Limits

- **Plane definition:** only by three named points. A plane through a point parallel to another plane is not available; that is slice 2.
- **Sections:** only of the declared polyhedra (pyramid, prism family). There are no curved sections on Hybrid.
- **No polygon labels:** section vertices are not named, and `ask_area` of a named polygon is unchanged.
- **Untested wordings:** the section cue is only "thiết diện", so "(MAB) cắt hình chóp theo một đa giác" is refused.
- **Not measured:** how a real model extracts these kinds; the Hybrid section scene has not been rendered in the product UI or reviewed by a human.
