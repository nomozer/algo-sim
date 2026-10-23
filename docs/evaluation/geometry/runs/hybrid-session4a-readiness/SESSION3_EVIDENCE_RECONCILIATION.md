# Session 3 evidence reconciliation

Status: **PARTIAL — reproducible research evidence; aggregate and scope claims corrected**. This is a correction layer for the Session 3 reports at `0f7b3a69…`, not a rewrite of those files. Source receipt hashes are in `results/receipt-audit-attempt2.json`; the closing manifest hashes the new results. Source run: `docs/evaluation/geometry/runs/hybrid-contract-v2/` on the S3 branch.

## 562 cannot be reconstructed

The final report says 562 evaluations; the migration report gives an incomplete sum. The raw summary and evaluator define these units:

| Family | Count | Actual unit / scope |
|---|---:|---|
| A | 47 | Authored `/2` grammar payloads, one route per case |
| B | 60 | Replayed S1 problem/payload identities; several routes and an extra S1 replay are invoked |
| C | 316 | Cut-edge permutation payloads; `/1` bridge, `/1` adapter and two labelled `/2` conversions are compared |
| D | 33 | Metamorphic variants, three route results per variant |
| E | 20 | Ten negative controls × two input conventions; multiple route results per convention |
| F budget | 8 | Budget probes, six served and two refused |
| G | 16 | Adapter development payloads, dual route |
| H | 60 | Thirty Route-B problems × two arms, **not sixty distinct problems** |
| F composition | 38 | Additional plan inspections drawn from existing families, not independent problems |

The displayed A–H column totals **560 mixed units** including F budget, or **552** without F. Adding the 38 composition inspections yields **598 mixed units**. None is a defensible count of unique independent problems or total route calls. **562 = NOT_RECONCILED**; no missing ten cases are invented and 560 is not promoted to a corrected unique-case denominator. A complete executed-call count is UNKNOWN because the frozen evaluator does not persist a call ledger for every nested replay. F composition overlaps prior cases. Fuzz is separate.

The persisted summary records no wrong serves in its checked arms, but this is not a global safety proof. E explicitly records one old `/1` Adapter `/3` acceptance (`N-anonymous-ratio-operand-triangle/convention`) while canonical `/2` refuses all twenty. Exact-answer coverage is narrower than scene self-consistency (e.g. B's `/1` answers are checked on 43 served cases; construction-only cases have no numeric oracle). Do not pool these into “0/562 false serves”.

## Fuzz receipts versus resume ledger

| Receipt | Mutants / route calls | Escaped exceptions | Internal errors |
|---|---:|---:|---:|
| baseline-adapter3.json | 13,661 | 1,015 | 0 |
| baseline-bridge.json | 13,661 | 0 | 0 |
| p1-adapter3.json | 13,661 | 0 | 0 |
| p1-bridge.json | 13,661 | 0 | 0 |
| p3-v2.json | 19,114 | 0 | 0 |

The P1 post-fix and P3 runs total **46,436 mutation executions**, not independent source problems. `fuzz_boundary.py` enumerates mutations over corpus/test seeds and field sites, replacing/deleting values; it is not a 500-case random sampler. The resume ledger matches these larger receipts. The final/migration reports' `500` / `3 × 500` descriptions are unsupported. `p1-planner.json` cited there does not exist: the actual second P1 file is `p1-bridge.json`. All five receipts remain unchanged. No new fuzz run was needed to recount them.

## Route-B's four false refusals

The S3 summary stores aggregate H outcomes but drops its row list. Targeted re-execution at clean `84c729e0…` recovers identities in `results/planner-diagnostics.json`, separately labelled as a new reproduction: **38 correct served, 18 correct refusals, 4 false refusals, zero wrong served**.

- **B27, facts and pipeline:** `OUT_OF_SCOPE`. The frozen facts literally encode the described-midpoint question as `kind="unsupported"`. Both arms feed those same facts; the pipeline arm is a fake provider, not an independent language extraction. The current resolver has described-point support. The original “missing composition” diagnosis describes the historical fixture encoding and does not isolate a current planner defect. A re-encoded diagnostic would be a new measurement, never a silent benchmark repair.
- **B28, facts and pipeline:** `PREDICATE_NOT_IN_QUOTE`. A source sentence calls O the square's “tâm” while the point fact requests `centroid` over four vertices; source predicate vocabulary blocks it before execution. Triangle-centroid composition does not establish support for a quadrilateral centre. This is a source/representation limitation with a possible downstream centroid restriction, not evidence of a missing primitive alone.

Thus there are **two problem identities repeated in two arms**. No source, fixture, oracle or product code was changed to improve these results.

## What the locked 47-case set proves

`grammar-set.lock.json` explicitly says **DEVELOPMENT_EVALUATION_NOT_BLIND**, preregistered by the implementing agent. Lock commit `4268f4e214125fe20c858930bc92b0c5798dfc67` precedes `/2`, D6 and G1–G7 implementation. LF-normalized SHA-256: `10c57be7b485d7b3f1a97183ff41b28988e70641e297e01cccf68d1434cc4abe`.

It contains 22 expected serve, 19 source refusal, four geometry refusal and two kernel/capability refusal cases. It checks authored TypedFacts-to-route behavior and exact squared oracle answers, chiefly section phrasing, contract boundaries, selected derived pyramids and source rejection. It does not evaluate provider extraction, all geometry families, independent blindness, browser rendering or production traffic. Some `/2` cases are re-authored equivalents of development examples, not raw provider outputs.

Results: 22/22 positive served; 25/25 negatives refused; exact category 46/47. `NEG-per-edge-same-name` is rejected earlier by schema (`INVALID_DERIVED_SECTION`) rather than in the expected source category. Fresh seam replay reproduces 22 verified scenes / 25 refusals, retaining this boundary distinction.

## Product, measured tree, candidate and final docs are different identities

| Role | Identity / result |
|---|---|
| Product commit | `69bd2fe48be1fd3afa6ce4112ccddda92a07d850` |
| Git backend subtree | `357afcfae2289cfed286cb47f709c708a6c661cc` |
| LF-normalized measured-system SHA-256 | `413ee525d20874aa346b13df7e51019266f7d4701af56719c2a2ee736266b5df` |
| Successful T3 target | `84c729e0b0df7868dfcc0a6e48cac457d7959e92` |
| Final S3 documentation HEAD | `0f7b3a69d0f920a6cc115a7d9e1a89f693137208` |
| First T3 target | `b555ca48f2f40c1b7e6d043ecf8339d10d85f781`, exit 1; not the accepted receipt |

The “116 files in backend/app” wording is inaccurate. The freeze helper hashes **116 path entries: 110 backend + six frontend entries, 115 unique files**. The semantic-program schema appears twice because the configured directory and explicit file overlap; the semantic frontend test is also included. This is the historical algorithm, retained unchanged. Its SHA-256 is not a Git tree SHA and does not cover the entire renderer. The separate `product_commit_sha` rule covers product paths including renderer changes.

Successful T3 receipt: `verification/full-t3/execution.json`, exit 0, clean before/after, 484.53 s, UTC 2026-10-22 19:00:05–19:08:09 (local 2026-10-23 02:00–02:08). Reported counts: backend 11,572 passed / 1 skipped / 2 deselected / 15 xfailed; frontend 72 files / 1,156 passed; build, demo and crash audits PASS. Post-T3 freeze receipt matches. Raw stdout/stderr hashes and byte counts exist, but those streams are not present in the tracked run: their contents cannot be independently recovered from hashes. Treat detailed counts as reported by the final manifest, while exit/status and source identity are directly in the receipt. No new full T3 was run in 4A.

Session 3 review audited `94893d72…` and documents remediation at product `69bd2fe4…`. It is a code-review receipt; it is not an independent problem-authoring/holdout evaluation. Its review identity and final documentation HEAD are not interchangeable with the measured candidate.
