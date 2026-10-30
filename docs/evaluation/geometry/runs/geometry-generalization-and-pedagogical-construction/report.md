# W4 — End-to-end geometry generalization and pedagogical 3D construction

Owner Master GO `ALGOSIM_W4_END_TO_END_GEOMETRY_AND_PEDAGOGICAL_SIMULATION` (2026-10-30). The work is one epic on
research branch `research/w4-geometry-pedagogy`, based on `main` `e5dc3d28`. 0 provider calls.

## Architecture: before and after

Evidence: `architecture-audit.md`, read-only and built from the real code.

**Before:**
- Every route ends in one scene builder (`simulation_state` → `scene3d`), one renderer and one exact kernel. Construction
  is truly incremental (`formation.steps`, `visible_ids`).
- Gaps:
  - The 22 Wave 3 false refusals all stopped in the Source Gate's closed SG-3 clause grammar or in the kernel.
  - Student text was not tied to any certificate.
  - Steps had no keyboard navigation.

**After:** the same single pipeline is kept. Rejected alternatives: a second planner, renderer or timeline; giving
Adapter /3 a product path. Changes:

| component | change | responsibility |
|---|---|---|
| `registry.py` SG-3 grammar (`_C_NOI`, `_C_DAU`, `_C_DAY`, `_C_DOAN`, `_HINH`, `m_tai`) | Number-free textbook connectors and lexical variants: "Trong không gian,", "thỏa mãn", "biết", "với (mặt\|tứ giác\|tam giác) đáy", "vuông ở", "số đo XY =" | Source grounding stays closed: every clause maps 1-to-1 to a validated call |
| `registry.py::_vai_doan_ok` | A role-prefixed length ("chiều cao XY", "cạnh bên XY") is read only when proved: XY ⊥ base, or a lateral edge of a right prism, or apex–base / base–top | Fixes pre-freeze review B1 and the pre-existing N1 |
| `simulation_state.py::_canh_song_song_thiet_dien` | Exact rational check that an edge XY of the cut face is parallel to the section edge and X lies off (α); records `steps[k].parallel_face_edge` | Geometry layer; certified fact |
| `scene3d.py::_ly_do_canh_thiet_dien` | Carries that fact as `justification_text` + `details.justification` (the parallel-line–plane intersection theorem). No fact means no text | Presentation layer stays geometry-free (`test_scene3d`) |
| frontend `scene3d-model.ts`, `scene3d-playback.tsx`, `global.css` | "Vì sao" line under the current step; ←/→/Home/End navigation | Shows backend facts only; never infers |
| `CACHE_VERSION` 130 → 131 | The LLM_ONLY served envelope gains the justification | Stale cached envelopes MISS |

## Evidence

| item | receipt | result |
|---|---|---|
| Phase B capability matrix (22 false refusals) | `capability-matrix.md` | All 22 blocked in the Source Gate (20) or the kernel/conditional reader (2) |
| RED → GREEN | `preregistration.md`, `red-baseline.json`, `green1.json` | Independent 70-case corpus: variants 6/42 → 42/42, canonical 18/18, negatives 10/10 |
| Wave 3 post-feedback (`POST_FEEDBACK_DEVELOPMENT_REGRESSION`) | `regression-green3.json`, `wave3-green3.json` | **50 → 67/72** served-correct (target 58), 72/72 negatives, 62/72 reasons, **0 wrong-served**, 0 leaks, 17 transitions, all FALSE_REFUSAL → SERVED_CORRECT |
| Locked development and 203 reviewer probes | same | 96/96, 0 wrong-served; probes 0 served negatives, 0 internal, 0 transitions |
| Role-claim amendment | `dev-corpus/role-claims.json` | 3 negatives agree with the wrong reading, all refused; the proved-height control equals canonical |
| Mutation | `test_premise_sentence_generalization.py`, `test_section_edge_justification.py` | 8 grammar mutants + role-check mutant + 2 justification mutants, all killed behaviourally |
| Pedagogy | `pedagogy-rubric.md`, `pedagogy-metrics.json`, `ui-evidence/` | 100/108 section-edge steps carry a certified "why"; the other 8 have no parallel face edge, so no claim is made. Real-browser forward/back/Home/End shows no stale state. Proxy only, no learner study |
| Pre-freeze adversarial review | `pre-freeze-review.md` | NOT_READY on B1, fixed, re-verified READY (34 new attacks refused) |
| T0/T1/T2 | `tiers.json` | T0 `IMPACT_GATE_PASS` 15892/0; T1 879 + 24; T2 1424 + tsc + build |
| Candidate | `frozen-evaluation-candidate.json`, `candidate_divergence.json` | Freeze `182a7785` (from `be686523`), product `61ade29e`, 118 files `54b5b565…`, cache 131 |
| Full T3 | `full-t3.json` | **FULL_PRODUCT_GATE_PASS** on fresh detached `25028584` (attempt 2; attempt 1 invalid, environment, disclosed) |
| Publication | `publication-assessment.md` | Range: 1 pending synthetic-key exception, so **BLOCKED** pending the Owner. Head: 0 unexcepted (better than pre-W4 main) |

## Remaining limitations (not repaired; fail-closed)

- **Five Wave 3 false refusals remain:**
  - W3-B01: "Thiết lập mặt phẳng" is read as a conditional.
  - W3-B34/35/36: oblique-prism projection phrasing on the two-line slice.
  - W3-A06: radical bound, a genuine limit.
- **Earlier limitations carried over:** R3, RV-2/L-AREA, RV-8, and 4 source-grammar diagnostics.
- **"đường chéo XY" is not role-checked.** This is pre-existing.
- **"chiều cao XY" accepts any validated XY ⊥ base.** The bound length is still correct.
- **Not done (audit items 2, 3, 6):** per-step certificate badges; a claim-word guard on Route B labels (pre-existing gap);
  disclosure of a skipped teaching expansion.
- **Not measured:** live provider quality and actual learning gains.
