# Plan — `hybrid-preview-contract-hardening`

Owner approval `GO_HYBRID_PREVIEW_CONTRACT_HARDENING` (2026-10-18). Branch `research/hybrid-preview-contract-hardening` from
`main = origin/main = 65d6ee97`. Offline only. No merge, no push, no live call, no Hybrid enablement, no `frontend/src` edit.

## P1 — refusal classification (existing vocabularies only)

`failure_category` values come from the closed set already emitted and labelled by the frontend
(`error_codes.SEMANTIC_FAILURE_CATEGORY`, `pipeline._that_bai_hinh_hoc`, `SimulationWorkspace.NHAN_LOAI_VAN_DE`).
`refusal_cause` comes from `semantic_program/refusal_cause.py` (`SOURCE | CONSTRUCTION | UNKNOWN`; only a structured
fact may say `SOURCE`). No new code or category. `reason_code` is unchanged.

| group (server-side table, not emitted) | `failure_category` | `refusal_cause` | why this category |
|---|---|---|---|
| capability gap | `capability_gap` (`OUT_OF_SCOPE` → `out_of_scope`) | `UNKNOWN` | "can the machine execute it? — no" |
| missing / ambiguous data | `insufficient_specification` | `UNKNOWN` | the same meaning as `INPUT_NOT_GROUNDED` in the semantic route |
| contradictory / degenerate data | `geometry_generation_failed` | `SOURCE` only for `NON_POSITIVE_LENGTH` (unchanged), else `UNKNOWN` | the category LLM_ONLY uses for every geometry refusal; the cause axis carries "the data" |
| source not verified | `verification_gap` | `UNKNOWN` | provenance not established ⇒ not enough evidence to present |
| result / certificate not verified | `verification_gap` | `UNKNOWN` | `POSTCONDITION_VIOLATED` precedent |
| cannot conclude | `verification_gap` | `UNKNOWN` | `SEMANTIC_VERIFICATION_UNAVAILABLE` precedent: it ran, nothing certifies the claim |
| extraction / provider failure | `geometry_generation_failed` | `UNKNOWN` | generation failed before a verifiable program existed |
| integrity / identity | `geometry_generation_failed` | `UNKNOWN` | the system's own output can't be attributed or trusted; never a capability verdict |
| unknown code (fail-safe) | `geometry_generation_failed` | `UNKNOWN` | never `capability_gap` |

`NEGATED_CLAUSE` is split structurally, not by text. With an observed negated check it means "cannot conclude"; from the
planner (no observation) it means "capability gap". A lock scans the Route D source so that every literal refusal code
is in the table.

## P2 — proof-text backstop

Detection-only normalisation: NFKC, drop `Cf`, fold every `Pd` dash plus the minus signs (U+2212, U+2796, U+02D7,
U+2043) to `-`, casefold. The text served is never modified. The structural invariant stays primary:
`proof_status = UNVERIFIABLE` and `can_present_as_proven = false` for every observation. A test removes the regex and
shows that a promoted status is still refused.

## P3 — fixtures

`backend/scripts/export_hybrid_preview_fixtures.py` runs the real endpoint in-process with:
- an ephemeral operator token that is never written;
- the network blocked;
- inputs from committed corpora only (contract-driven-goal-composition corpus, hybrid holdout cases, the existing
  zero-length and proof-only derivations), plus declared fault injections on a real served result.

It writes a new run folder, refuses to overwrite, and `--verify` regenerates the bundle and compares it. Each fixture
records its source input and hash, its producer (commit, product commit, measured-system hash, adapter/envelope
versions), the expected outcome, and the response with its hash.

## P4 — `docs/architecture/HYBRID_PREVIEW_FRONTEND_CONTRACT.md` (contract for the Scene3D agent)

## P5 — regression, then commit (product), freeze (separate commit), independent review, T3 on a clean detached checkout
