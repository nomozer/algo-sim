# plan.md — `hybrid-v2-independent-vietnamese-section-holdout-wave2`

## 1. Mission & Scope

- **Task:** `HYBRID_V2_INDEPENDENT_VIETNAMESE_SECTION_HOLDOUT_WAVE2`
- **Wave Type:** Evaluation-only preregistered independent holdout evaluation after M1–M5 repairs.
- **Authoritative Baseline (`main = origin/main = GitHub remote`):** `d7a94d3cd4bbdea3df99e383bec78425fcc8bf1c`
- **Product Commit:** `e3678608f1f7110d7046c9c43c312c69d7614f55` (Frozen Full T3 candidate `e7bcff316ee6d443e753105a887e0689ea04848b`)
- **Measured System:** `118` product files, `measured_system.tree_hash = 84ccf653441d1bd54f352756b9a5e917ee02a9ea11a83ac60585dfc585f3f99f`
- **Architecture Versions:**
  - `REGISTRY_VERSION = "geometry-functions/18"`
  - `PLANNER_VERSION = "geometry-fact-planner/17"`
  - `ENGINE_VERSION = "geometry-function-engine/14"`
  - `ADAPTER_V4_VERSION = "hybrid-simulation-adapter/4"`
  - `PLANE_SECTION_CERTIFICATE_VERSION = "plane-section-certificate/1"`
  - `CACHE_VERSION = "130"`
  - `DEFAULT_MODE = "LLM_ONLY"` (Hybrid opt-in only)
- **Hard Authorization Boundaries:**
  - Zero product code modifications (`backend/app/**`, `frontend/src/**`).
  - Zero live AI/provider calls (`ALLOW_LIVE_AI = 0`).
  - No merge to `main`, no push to `origin`, no worktree deletion.
  - Historical holdout (`hybrid-v2-independent-vietnamese-section-holdout`, now classified as `POST_FEEDBACK_DEVELOPMENT_REGRESSION`) and M1–M5 development corpus (`hybrid-v2-holdout-failure-repair`) remain byte-untouched and excluded from Wave 2 case construction.

## 2. Execution Phases

1. **Phase 1 — Preflight & Product Freeze Verification:**
   - Verify 3-way `main` alignment (`local main == origin/main == GitHub remote == d7a94d3cd4bbdea3df99e383bec78425fcc8bf1c`).
   - Create isolated evaluation worktree `.superpowers/worktrees/independent-section-holdout-wave2` on branch `research/hybrid-v2-independent-vietnamese-section-holdout-wave2`.
   - Verify `freeze_evaluation_candidate.py --verify` (`118` files, tree hash `84ccf653441d1bd54f352756b9a5e917ee02a9ea11a83ac60585dfc585f3f99f`).
2. **Phase 2 — Preregistration & Scorer Self-Tests (Before Corpus Generation):**
   - Author and commit `plan.md`, `preregistration.md`, `supported-family-matrix.md`, `scoring-contract.md`, `curator-brief.md`, `tools/refusal_taxonomy.json`, `tools/evaluate_holdout_wave2.py`, and `tools/test_evaluate_holdout_wave2.py`.
   - Verify all 17 mandatory synthetic positive and negative scorer controls pass via `pytest` before spawning the curator.
   - Commit and SHA-256 hash all preregistration and scorer artifacts prior to corpus creation.
3. **Phase 3 — Independent Curator Corpus & Exact-Oracle Authoring:**
   - Spawn an isolated curator subagent (`Independent Holdout Wave 2 Curator`) restricted strictly to the allowed reading list (`AGENTS.md`, `docs/RULES.md`, `preregistration.md`, `supported-family-matrix.md`, `scoring-contract.md`, `curator-brief.md`, `tools/refusal_taxonomy.json`, and `backend/app/simulation/geometry_functions/typed_fact_next.py`).
   - Author 96 new Vietnamese spatial-geometry section problems (`inputs/holdout-wave2.json`: 36 Category B `W2-B01..W2-B36`, 12 Category A `W2-A01..W2-A12`, 48 Negative/Adversarial `W2-N01..W2-N48`), Euclidean coordinate specifications (`oracle/geometry.json`), pure-Python exact-`Fraction` oracle (`oracle/oracle_holdout_wave2.py`), expected outcomes (`oracle/expected.json`), `curator-attestation.md`, and `corpus-provenance.md`.
4. **Phase 4 — Independence Audit, Semantic Deduplication, Independent Oracle Re-Verification & Pre-Execution Freeze:**
   - Audit the curator subagent's tool transcript (`tools/audit_curator_log.py` → `results/independence-audit.json`).
   - Run 9-dimensional semantic deduplication (`tools/dedup_check_wave2.py` → `results/deduplication-audit.json`) comparing all 96 Wave 2 cases against Wave 1 (`H001..H084`), M1–M5 development (`D001..D016`, `N001..N016`), and all historical geometry corpora and test fixtures.
   - Spawn a separate read-only reviewer subagent to independently recompute all 48 positive oracle cases (`W2-B01..W2-B36`, `W2-A01..W2-A12`) from the Vietnamese problem texts before product execution.
   - Record SHA-256 hashes of all frozen preregistration, corpus, oracle, and scorer files in `holdout-manifest.json` and commit the pre-run freeze.
5. **Phase 5 — Single Frozen Scored Run, Post-Hoc Diagnostics, Independent Review & Handoff:**
   - Execute `tools/evaluate_holdout_wave2.py` once on the frozen 96-case corpus into `results/scored-run-1/`.
   - Run non-mutating post-run diagnostics (`results/diagnostics.json`) and independent review (`review.md`).
   - Author `report.md`, `handoff.md`, and `run.json`, verify `freeze_evaluation_candidate.py --verify` (`MATCH`), and stop for Owner review.
