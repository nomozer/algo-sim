# repo-cleanup — report

Run metadata: `run.json`. Every processed path with its function, consumers, action and reason: `inventory.json`
(`2c2dfbbf..372f78c2`). Naming rule and rename tables: `docs/evaluation/RUN_NAMING.md`.

## 1. Areas

| reviewed | how |
|---|---|
| `backend/app` (105 files) | import graph from `app.main` (AST, incl. imports inside functions); removed-module imports |
| `backend/scripts` (178) | docstring of every script, imports incl. `importlib.spec_from_file_location`, consumers in tests, scripts, docs, run `.sh` |
| `backend/tests` + fixtures (356) | consumers of every fixture group incl. dynamic paths (`Path(...) / "fixtures"`, globs) |
| `frontend/src` (166) + CSS | import graph from `main.tsx`; class usage incl. `stem-${…}` for `global.css` |
| `frontend/scripts` (95) | what each opens (catalogue ids, `offline-catalog`, fixtures), gates (`full-gate`, `impact`, `package.json`) |
| root, `.claude`, `package.json`, `alembic`, `public/` | read |
| living docs | 18 root docs, `docs/architecture`, `docs/research`, `AGENTS.md`, `README.md`, `RUN_NAMING.md` — reference sweep |

Not reviewed as code, with reason: `docs/evaluation/**` run directories and the 180 historical reports (frozen evidence,
AGENTS §4 — classified, not rewritten); `docs/legacy/**` (dead by definition); `node_modules`, `.venv`, `dist`,
`__pycache__`, `*.db`, `data/` (dependencies, regenerable or not tracked). No CI configuration is tracked.

## 2. Removed (132 files) — evidence in `inventory.json`

| group | files | evidence it is no longer needed |
|---|---|---|
| `backend/tests/fixtures` certified/faults/recorded/refusals, `d_test_holdout*`, `m13_dijkstra_pseudo_algorithm.json`, `seal_manifest.json` | 42 | only self-references; their readers (`oracles.py`, `ProvenanceLogger`) went with them |
| `backend/tests/oracles.py` | 1 | named only by the removed fixtures |
| `backend/app/evaluation/` | 8 | unreachable from `app.main`; `wave_snapshots` imported the removed `app.simulation.catalog` |
| `backend/app/ai/explain.py` + `POST /api/explain` | 1 | only caller `AIHelpPanel` not mounted; route now 404 next to the old tutor-flow routes |
| one-off Informatics scripts (M17 reproduction, SGK Tin học OCR, M17 visual review, SEALED run/seal/validation, SEALED #1 failure classes, container replay) | 9 | the runs are done and frozen; no gate or live tool calls them |
| tests of those scripts, the merged M17 pin pair | 4 | test the removed tool / merged |
| `frontend/src` engine + views + 2D helpers + their tests | 26 | not reachable from `main.tsx` |
| `frontend/scripts` Informatics runners | 42 | measure the removed catalogue; no gate uses them |

Also removed inside kept files: `editViaServer`/`explainViaServer`/`EditResponse` (client), `getExplainContext`
(module contract), `ExplainBody`/`EditBody` (`main.py`), the sweep functions of `evidence.mjs`, the `action-probe`
preload of `browser-runner.mjs`, 325 dead CSS selectors (218 class names; a selector with a class no file uses never
matches, so the page is unchanged — removal-only checked by parser: 830 → 530 rules, every kept rule identical), the
eight dead `test:domain:*` scripts and the impact rules for removed paths. Moved, not removed:
`capability-descriptors.json` (historical snapshot) to `relocated/`, same git blob `258d8da3…`.

## 3. Generic invariants kept on geometry cases

| invariant | before (Informatics) | now |
|---|---|---|
| a runner's artifact records the configured model | SEALED runner `_tong_ket` | geometry DEV runner: call site passes `gemini.MODEL` (AST) and `tong_ket` records it |
| T0 selects tests by owner (one domain → that domain; shared owners widen; shared CSS → token guard; backend → pytest; never empty) | paths under `domains/web`, `domains/binary`, `logic`, `app/validation`, `simulation/catalog.py` | `domains/geometry`, `domains/semantic`, `semantic_program/route.py`; two assertions on a test file that did not exist (`experience-manifest.test.ts`) removed — they were green on an echoed name |
| frozen SEALED set is not edited after the seal | seal/runner coupling tests + pin | pin kept (`test_benchmark_seal.py`); coupling tests go with the two scripts |
| frozen M17 evidence is not edited | two files named by wave | one file, same pins and assertions |
| removed routes stay removed | tutor-flow 404 | + `/api/explain` 404 |
| IR gates red under fault injection | `test_cross_domain_matrix.py` | kept unchanged with its data script (live IR) |

## 4. Renamed (29 + one merge + one class)

Table: `docs/evaluation/RUN_NAMING.md` — "Đã đổi (run `repo-cleanup`)". Held-out apparatus (`run_holdout_*`,
`score_holdout_official`, `finalize_holdout_intake`, `run_holdout_ingest_chain`, `run_dev_stability`), geometry tests named
by what they lock (`test_dev_failure_regressions`, `test_angle_scope_gate`, `test_curved_acceptance_*`, …), three frontend
files. Separate commit `67e11671`, no logic change; references updated in scripts (`importlib` names included), tests,
the T0 selector and living docs.

## 5. Informatics content and wave codes left, with reasons

| item | why it stays | tracked by |
|---|---|---|
| prompts `skills/{adapt,analyze,classify,edit,explain,simulate,semantic_analyze,semantic_program}.md` | every `skills/*.md` is in the cache-lock hash; deleting one = model-surface change + `CACHE_VERSION` bump | `ISSUE-ARCH-INFORMATICS-MODEL-SURFACE-AND-IR-VOCABULARY` |
| IR container vocabulary, 2D semantic renderer, their tests and `cross_domain_matrix.py`; `domain=None` branch of the pipeline | live IR and schema (hashed, exported); the brief forbids IR change | same |
| `SamplePreview` Informatics glyphs, `threeD`/`specDrift` shell contract, `offline-catalog.ts` comment, nine dead `geo3d-*` classes | changing them changes what the UI shows or is geometry UI work | `ISSUE-ARCH-SHELL-INFORMATICS-RESIDUE` |
| comments citing removed measurement scripts (`tokens.css`, `global.css`, `SimulationControls.tsx`, `transport-policy.test.tsx`, `test-tiers.test.ts`, `evidence.mjs`, `main.py`) and the `AIHelpPanel` needle of `ui-hygiene.test.ts` | provenance of a measured value / absence guard; the evidence named stays in `docs/evaluation/m20` | same |
| pins of retained evidence (`test_informatics_evidence_pins.py`, `test_benchmark_seal.py`, `visual-audit-completeness.test.ts`) | the evidence stays in the repo; the pins keep it unedited | — |
| dataset / pool / metric versions and concept ids in names; `test_w17_*`-style names; Alembic revision file | data identity or concept; `-k w17` selectors; migration history | `RUN_NAMING.md` |
| 18 geometry browser scripts building paths with `URL.pathname` | not Informatics; existing defect | `ISSUE-OPS-BROWSER-SCRIPTS-SPACE-PATH` |
| `docs/evaluation/**`, historical reports, `docs/legacy/**` | frozen evidence / dead by definition | AGENTS §4 |

After the cleanup, `docs/CODE_INDEX.md` has 0 stale paths (59 entries moved verbatim to
`code_index_removed_entries.md`); the reference sweep of living docs and live code leaves only the items above.

## 6. Identity and checks

Product commit `be4b8287`, candidate `b4a33205…` (102 files), `CACHE_VERSION` 117, `LLM_ONLY`, 0 model calls, 0
screenshots. Checks and the full gate: `handoff.md` §2.
