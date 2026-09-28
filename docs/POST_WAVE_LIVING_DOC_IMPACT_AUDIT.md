# Post-wave living-document impact audit

**Task:** `POST_WAVE_LIVING_DOC_SYNC_AND_RUN_NAMING_POLICY`

**Audit baseline:** `075d484f761eb40474efc9f25e49ece3563003c7`

**Truth synchronized:** `FINAL_DECISION = VERIFICATION_NOT_CLEAN`

This inventory records why each required document was or was not changed. It is
an impact audit, not a new product-evidence run. Started in a Codex session that
hit its usage limit after 11 files; `CODE_INDEX`, `STATUS_LEDGER`,
`EVIDENCE_INDEX`, `THESIS_READINESS` and the audit allowlist were completed in
the resumed session.

| Path / scope | Classification | Reason |
|---|---|---|
| `README.md` | `UPDATE_REQUIRED` | Add direct navigation to the documentation hub, current state, roadmap and code index; no commit telemetry is copied into the root README. |
| `docs/README.md` | `UPDATE_REQUIRED` | Register this audit, the architecture amendment and the run-naming policy. |
| `AGENTS.md` | `NO_CHANGE_REQUIRED` | Existing durable safety rules already cover explicit staging, immutable evidence, detached verification, no push/merge and default-mode safety; task state and SHAs do not belong there. |
| `docs/RULES.md` | `NO_CHANGE_REQUIRED` | Durable rules only; contains no branch, SHA or next-action state affected by this wave. |
| `docs/COVERAGE.md` | `NO_CHANGE_REQUIRED` | Curriculum coverage and forbidden claims are unchanged; the wave adds no family and no coverage number. |
| `docs/AI_CONTEXT_BUNDLE.md` | `UPDATE_REQUIRED` | It named an obsolete branch, cache 100 and push/PR next action. |
| `docs/CURRENT_STATE.md` | `UPDATE_REQUIRED` | Canonical current state did not describe the occlusion wave or its remaining red gates. |
| `docs/CODE_INDEX.md` | `UPDATE_REQUIRED` | New ownership, classifier, oracle, formation, section, browser/performance and recovery modules were not fully indexed. |
| `docs/ARCHITECTURE_MAP.md` | `UPDATE_REQUIRED` | It still listed dynamic hidden-line detection as unimplemented and lacked the new identity/ownership boundaries. |
| `docs/CORRECTNESS.md` | `UPDATE_REQUIRED` | Add the canonical visibility/identity correctness contract. |
| `docs/ROADMAP.md` | `UPDATE_REQUIRED` | The push/PR action is invalid while mandatory verification remains red. |
| `docs/OPEN_ISSUES.md` | `UPDATE_REQUIRED` | Register five independent verification-cleanup issues and correct the old hidden-line status without closing it. |
| `docs/STATUS_LEDGER.md` | `UPDATE_REQUIRED` | Register the exact eight commits and the measured pass/fail result. |
| `docs/EVIDENCE_INDEX.md` | `UPDATE_REQUIRED` | Make the four-step correction chain and all authoritative artifact links explicit. |
| `docs/THESIS_READINESS.md` | `UPDATE_REQUIRED` | Prevent historical readiness statements from being read as current acceptance. |
| `docs/architecture/OCCLUSION_AND_SCENE_IDENTITY_AMENDMENT.md` | `UPDATE_REQUIRED` | New durable decision record for machine identity, visual ownership, surface policy, spans, formation, section identity and oracle independence. |
| `docs/architecture/ARCHITECTURE_CAPABILITY_MATRIX.md` | `SUPERSEDED_BY_CORRECTION_LINK` | Historical audit snapshot dated 2026-09-25; stale hidden-line/browser fields are superseded by the amendment and evidence correction chain, so the snapshot remains byte-identical. |
| `docs/architecture/architecture_capability_matrix.json` | `SUPERSEDED_BY_CORRECTION_LINK` | Machine-readable companion to the historical 2026-09-25 snapshot; not rewritten. |
| Other `docs/architecture/**` decisions | `NO_CHANGE_REQUIRED` | Their compiler-family/composite decisions are outside the occlusion verification delta; the new amendment owns this delta. |
| Candidate-divergence and telemetry artifacts under `docs/evaluation/**` | `IMMUTABLE_HISTORICAL_ARTIFACT` | They describe their recorded candidates/runs and must remain byte-identical; current truth is linked through the correction layer. |
| `docs/evaluation/geometry/runs/20260928-cross-family-hidden-line-occlusion-oracle-and-formation-repair/**` | `IMMUTABLE_HISTORICAL_ARTIFACT` | Authoritative prior-wave run; no file is renamed, moved or edited. |
| `docs/evaluation/RUN_NAMING.md` | `UPDATE_REQUIRED` | New durable naming policy required for future runs; existing long IDs are legacy. |
| `backend/scripts/audit_docs_information_architecture.py` | `UPDATE_REQUIRED` | The docs audit must accept the new canonical next-action value. This is documentation tooling, not product code. |
| `backend/tests/geometry/test_docs_information_architecture.py` | `NO_CHANGE_REQUIRED` | Existing invariants exercise action allowlisting, links, indexes and evidence chains once the audit authority is updated. |
| `frontend/src/code-index-sync.test.ts` | `NO_CHANGE_REQUIRED` | Existing ratchet already checks that new frontend source/scripts are present in `CODE_INDEX.md`. |
| Other docs/index/link/sync tests | `NO_CHANGE_REQUIRED` | Existing suites cover current-state identity, candidate/cache verification, index paths and correction-chain acyclicity; no new test contract is needed. |

`NOT_APPLICABLE`: no Markdown/JSON paired artifact is produced by this docs-only
task. `RUN_NAMING.md` is a policy document, not an evaluation run.
