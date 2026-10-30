# Pedagogical rubric and evidence (W4)

**Scope.** Representative supported families: triangular and rectangular-base pyramids, right prisms, cuboid and cube,
with plane sections parallel to two lines or perpendicular to a line. 0 provider calls.

**Limitation.** Every measure below is an automated proxy or a single-reviewer UI observation. It shows what the
learner is shown and that it is mathematically certified. It is not evidence that students learn better; no learner
study was run.

| # | criterion (Owner GO §9) | evidence | result |
|---|---|---|---|
| 1 | The student can identify what each step constructs | `pedagogy-metrics.json`: every event of 30 served dev cases has learner text; each step label names its object ("Giao tuyến của (MNP) với mặt ABS") | PASS (30/30 cases) |
| 2 | Each explanation has a clear mathematical purpose that traces to verified facts | Section-edge steps carry "Vì sao", the theorem *(α) ∥ XY, XY ⊂ face ⇒ (α) ∩ face ∥ XY*, emitted **only** when XY ∥ the edge is exact and X is off the plane (`test_section_edge_justification.py`: independent re-check plus 2 behavioural mutants) | 100/108 edge steps justified. The 8 unjustified edges are TP3's perpendicular cut, where no face edge is parallel; there the system makes no claim instead of an invented one |
| 3 | Auxiliary constructions are distinguishable | Pre-existing auxiliary styling, auxiliary toggle and dashed hidden edges (`architecture-audit.md` §4); unchanged by W4 | PASS (inherited, not re-measured) |
| 4 | The sequence follows a meaningful teaching logic | given points → solid → construction points → cutting plane → one intersection per face → closed section → measurement (`teaching_order_ok`) | PASS (30/30) |
| 5 | The final result follows from the constructed facts | FINAL_RESULT is the last event and depends on the section built in the previous steps; the answer is the exact kernel value (metamorphic oracle, `green1.json`) | PASS |
| 6 | Forward/backward navigation does not corrupt state | Real browser (dev server on `w4-geometry-pedagogy`, offline sample "Thiết diện … qua ba trung điểm"): → moves 7→8 and "Vì sao" follows; End → 11 with no stale "Vì sao"; ← → 10 with BC's reason; Home → 1 with none. The scene shows only edges whose steps have executed (`ui-evidence/step7-why-panel.png`) | PASS (single reviewer, one sample) |
| 7 | Keyboard accessibility | ←/→/Home/End inside the player; range and select controls keep their own keys; auto-play stops on a key press (`scene3d-step-justification.test.tsx`) | PASS |

**Not done (recorded):**
- Per-step certificate badges (audit item 2).
- A claim-word guard on Route B labels (audit item 3; a pre-existing gap the audit found, not introduced here).
- Disclosure of a skipped teaching expansion (audit item 6).

These are candidates for a follow-up, not regressions.
