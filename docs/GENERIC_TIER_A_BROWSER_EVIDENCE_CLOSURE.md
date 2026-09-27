# Generic Tier-A browser evidence closure

**Wave:** `CLOSE_GENERIC_TIER_A_BROWSER_EVIDENCE_BEFORE_CUBOID_MERGE`

**Date:** 2026-09-27

**Final decision:** `MERGE_READY`

## Frozen identities

- `measurement_commit_sha = 2747f4b926511bd526e2eab541099f01e4b8acb5`
- `product_commit_sha = 2822beb389f8bdb253f26b8c6d6db1860d184cc6`
- `product_tree_sha = 72516eb576a173a0b987beff684e4e2c6a9669e5ea370828bbd9245447eb369b`
- `evidence_commit_sha = 7cee042c9a539f89970722ac56eb9f490d5e753b`
- `application_llm_calls = 0`

The measurement ran from a detached clean worktree at the measurement commit. The candidate verifier confirms that the measured product still consists of 103 frozen product files with the product tree above. `EVIDENCE_MANIFEST.json` intentionally contains no `evidence_commit_sha`; the post-commit identity is recorded here instead.

## Browser results

| Family | Topology | Desktop formation | Trusted-pointer orbit | Three-way causal closure | Desktop/mobile CSS + overflow | Negative production path |
|---|---:|---:|---:|---:|---:|---:|
| Triangular pyramid | 4/6/4, Euler 2 | 6/6 distinct frames | PASS, 4/4 key vertices moved | 9 = 9 = 9 | PASS / PASS | `NON_POSITIVE_LENGTH`, structured refusal |
| Triangular prism | 6/9/5, Euler 2 | 6/6 distinct frames | PASS, 6/6 key vertices moved | 11 = 11 = 11 | PASS / PASS | `NON_POSITIVE_LENGTH`, structured refusal |
| Rectangular pyramid | 5/8/5, Euler 2 | 8/8 distinct frames | PASS, 5/5 key vertices moved | 13 = 13 = 13 | PASS / PASS | `NON_POSITIVE_LENGTH`, structured refusal |
| Cross-section | 5/8/5, Euler 2; section has 4 vertices | 13 steps, 10 distinct frames | PASS, 5/5 key vertices moved | 9 = 9 = 9 | PASS / PASS | kernel `PLANE_DOES_NOT_CUT`; envelope `semantic_program_invalid` at `execution` |

Each causal result compares three independently named sets:

1. `oracle_expected_closure`, frozen from a canonical RequestContract/FactGraph or gold program source;
2. `event_declared_closure`, derived only from `scene3d.events[].depends`;
3. `browser_observed_closure`, read after trusted browser interaction.

For all eight positive viewport runs, `oracle_vs_event`, `oracle_vs_browser`, and `event_vs_browser` have empty `missing` and `unexpected` lists. The evidence therefore does not reuse the transport declaration as its oracle.

CSS readiness is decided from computed sentinel styles: Scene3D layout and positive size, canvas containment and dimensions, styled controls/readout, and document width not exceeding the viewport. Stylesheet enumeration is diagnostic only. All six computed-style checks pass on both 1440×900 and 390×844 for every family.

The section negative verdict follows the repository contract rather than a generic “outside plane is always an error” rule. The frozen kernel and capability sources require a requested non-empty section outside the solid to fail closed with `PLANE_DOES_NOT_CUT`; the production envelope exposes the structured safe refusal and a useful learner message.

## Evidence integrity

- Directory: `docs/evaluation/geometry/generic-tier-a-browser-closure-20260927/`
- Browser report: four scenarios PASS; 641 recorded `pass` fields are true.
- Artifact manifest: 69 pre-manifest artifacts with byte counts and SHA-256 hashes; all 69 hashes match the committed Git blobs.
- Contact sheet: 24 screenshots pass dimension, dynamic-range and variance checks; visual inspection found no blank or pre-readiness capture.
- Scenario and oracle source hashes use canonical Git blobs, so `core.autocrlf` cannot change their identity.
- The cross-section fixture preserves a hash-verified chain to the canonical thesis measurement artifact; the anti-corpus-leak guard and its generator regression test both pass.

An initial in-wave evidence snapshot (`cb7fadc9a68217852b861472f033b3b3e93d5134`) lacked that last provenance declaration. It was not used for the verdict. The final recapture at the measurement SHA was committed by `a13ea9a0016007db4eccb2f7aec9bef236e51009`; wave-local attributes then disabled JSON newline normalization so its byte hashes remain verifiable in the final evidence commit `7cee042c9a539f89970722ac56eb9f490d5e753b`.

## Regression gates

- Node harness tests: 7/7 PASS.
- Focused section kernel/capability tests: 49/49 PASS.
- Full backend: 6278 passed, 1 skipped, 1 deselected in 273.47s.
- Frontend TypeScript: `npx tsc --noEmit`, PASS.
- Frontend Vitest: 61 files, 890/890 tests PASS.
- Production build: PASS in the detached clean measurement worktree; Vite emitted only the existing >500 kB chunk warning.
- Candidate verify: PASS, 103 product files, tree `72516eb576a173a0…`.
- Cache verify: PASS, `CACHE_VERSION 102`, environment `b1714b566e25c912…`.
- Schema export: two consecutive exports are byte-identical; SHA-256 `D852B47C08B7AC0E2A41155366AC1FF88E7D08875CB1CFE718326C543B2951E7`.
- `DEFAULT_MODE = LLM_ONLY`; no candidate refreeze, cache relock, product edit, merge or push occurred.

The earlier cuboid audit's explicit Generic Tier-A `NOT_MEASURED` cells are now closed. No product defect was found. The final classification is `MERGE_READY` for the requested Cuboid merge decision.
