# Run `w13-geometry-preregistration`

Task `W13_GEOMETRY_CAPABILITY_AND_NON_ABSOLUTE_ARCHITECTURE_PREREGISTRATION` — an
architecture audit and preregistration. It records the human review of run
`w12-pedagogical-grounding-closure` (`NEEDS_CHANGES`, W12-H1…H4), audits absolute
assumptions and remaining capabilities, and preregisters the next wave. It changes no
product code, measures nothing in a browser and makes no model call. Identity and
environment are in `RUN.json`.

Start with `HANDOFF.md`, then `REPORT.md`. The design documents live outside the run:
[`GEOMETRY_CAPABILITY_AND_NON_ABSOLUTE_AUDIT.md`](../../../../architecture/GEOMETRY_CAPABILITY_AND_NON_ABSOLUTE_AUDIT.md),
[`GENERIC_GEOMETRY_FOUNDATION_PREREGISTRATION.md`](../../../../architecture/GENERIC_GEOMETRY_FOUNDATION_PREREGISTRATION.md)
and the layered matrix
[`geometry_capability_matrix_v2.json`](../../../../architecture/geometry_capability_matrix_v2.json).

| Path | What it is |
|---|---|
| `RUN.json` | identity: commits, unchanged candidate/cache/schema, environment, policy flags |
| `MANIFEST.json` | every file of this run with its sha256 |
| `REPORT.md` | findings, decisions, verification, limitations |
| `HANDOFF.md` | required handoff fields and what to decide next |
| `inputs/W12_HUMAN_VISUAL_REVIEW.json` | additive record of the w12 human verdict (w12 stays byte-identical) |
| `results/ABSOLUTE_ASSUMPTION_INVENTORY.json` | 67 absolute assumptions, classified A–J, each with `file:line` sources |
| `results/REMAINING_GEOMETRY_CAPABILITY_MATRIX.json` | derived view: every non-supported cell of the v2 matrix, with the matrix sha256 |
| `diagnostics/source_grounding_probe.py` · `diagnostics/SOURCE_GROUNDING_PHRASING_PROBE.json` | offline probe of the product's own length readers on 25 phrasings (0 model calls; refuses to overwrite a result) |
| `diagnostics/logs/PHASE0_REPOSITORY_GATE.log` | branch, HEAD, fetch, ancestry, candidate/cache/schema at the start |
| `diagnostics/logs/CLEAN_WORKTREE_DOCS_TESTS_7202befe.log` | docs-touching tests + docs audit in a clean detached worktree |
| `diagnostics/logs/VERIFICATION_MAIN_TREE.log` | identity, schema, diff and docs checks in the main tree |
| `diagnostics/WORKTREE_CLEANUP.json` | the temporary worktree and what was left on disk |
