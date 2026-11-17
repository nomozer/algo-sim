# Frontend Handoff Patches — `student-ready-geometry-simulation-input-reliability`

- **Status:** `FRONTEND_INTEGRATION = BLOCKED_OWNERSHIP` · `Gate C = BLOCKED_OWNERSHIP`
- **Ownership Boundary:** Zero edits were made to `frontend/` in this repository or to the external `D:\Documents\projects\axo-geometry-library` worktree (`git status --short frontend/` is empty).
- **Apply Check Command (from repo/worktree root):** `git apply --check <patch>`

---

## Standalone Verified Patches

| Patch ID | File | Target Files | Size (bytes) | Dry Apply (`git apply --check`) | Purpose |
|---|---|---|---:|---|---|
| **`FE-2`** | [`FE-2-multi-layer-aux-pyramid-readout.patch`](FE-2-multi-layer-aux-pyramid-readout.patch) | `frontend/src/simulations/domains/geometry/scene3d-regression-archetypes-fixtures.json` | 2,534 | `rc = 0` | Adds `"readout_ids": []` to all 9 formation steps (`step_index` `0..8`) of `multi_layer_aux_pyramid`. |
| **`FE-3`** | [`FE-3-ocr-confirmation-source-provenance.patch`](FE-3-ocr-confirmation-source-provenance.patch) | `frontend/src/llm/input.ts`, `frontend/src/components/photo-problem-flow.ts`, `frontend/src/components/ProblemInput.tsx` | 8,805 | `rc = 0` | Adds `InputSourceProvenance` (`ocr-confirmation-provenance/1` -> `verified-input-provenance/1`), captures `selectedCandidateId` and `prepareProvenance`, and forwards `input.source_provenance` on `analyzeFn` (`/api/analyze`) for both auto-verified and student-confirmed OCR flows. |
| **`FE-4`** | [`FE-4-scene3d-auxiliary-role-styling.patch`](FE-4-scene3d-auxiliary-role-styling.patch) | `frontend/src/simulations/domains/geometry/scene3d-view.tsx` | 4,609 | `rc = 0` | Distinguishes `CONSTRUCT_AUXILIARY_GEOMETRY` auxiliary `point3` markers (`semanticPointRole = "auxiliary_point"`, `0.72x` radius in `datCoDauDinh`, slate `0x64748b` color) from primary solid vertices, and renders trace-method `details.justification.auxiliary_points` dots (`trace_auxiliary_points`). |
| **`FE-6`** | [`FE-6-workspace-grid-toggle.patch`](FE-6-workspace-grid-toggle.patch) | `frontend/src/components/SimulationWorkspace.tsx` | 628 | `rc = 0` | Wires `#chk-grid` state (`luoi`) into `<Scene3DWorkspace gridShown={luoi} />` instead of hardcoded `gridShown={false}` at line 1546. |

---

## Merge Notes (`FE-6` Static Fixtures)

- Consistent with [`simulation-first-mvp-stabilization/FRONTEND_HANDOFF_STATUS.md`](../../simulation-first-mvp-stabilization/FRONTEND_HANDOFF_STATUS.md), when integrating `D:\Documents\projects\axo-geometry-library` with `feat/local-first-geometry-understanding`, take the library worktree versions of `scene3d-circumsphere-fixture.json` and `scene3d-regression-archetypes-fixtures.json` and apply `FE-2-multi-layer-aux-pyramid-readout.patch` along with `FE-3`, `FE-4`, and `FE-6`.
