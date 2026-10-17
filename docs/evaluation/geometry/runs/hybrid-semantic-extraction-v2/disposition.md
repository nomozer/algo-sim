# Disposition — Semantic Extraction v2 (closed)

Owner decisions, 2026-10-17, after the paired dev pilot ([`results/live-pilot-analysis.md`](results/live-pilot-analysis.md)):

1. **NO-GO** for the 48 held-out requests of protocol v2.
2. **NO-GO** for integrating prompt v2 into `main`.
3. **GO** to prepare a selective integration of the reviewed safety fixes, scorer /2 and their regression tests.
4. **GO** for an offline Semantic Extraction v3 study (provider response schema, typed goal completeness).

## What the evidence says (unchanged, not re-scored)

- Prompt v2 improved the intent proxy (10 → 13/16), removed truncation and invented labels on this split (1 → 0 rows),
  parsed 12/12, and cost less (est. USD 0.074 → 0.049, max latency 32 → 13 s).
- Goal/entity on expressible requests (5/11), operand correctness (2/8), solid association (3/6) and unsupported
  detection (0/1) did **not** improve; end to end both arms served **0/12** (GOLD ceiling 2/12), 0 unsafe.
- 12 dev items, one sample per arm: descriptive only, no population claim.
- There is **no evidence that v2 should replace the current extractor**; the current product prompt stays.

## Sealed held-out

The 24 heldout cases were never sent to a provider and stay sealed under their published limits: AI-authored, not
human-validated, *structurally implementer-exposed* (aggregate GOLD outcomes and one row's structure were seen while
fixing the scorer; no text). They are not reused as fresh held-out for a later protocol.

## Preserved evidence

- Research branch `research/hybrid-semantic-extraction-v2` at `0303c3eb`, local annotated tag `evidence/extraction-v2-pilot`.
- Derived receipts in this directory; raw live manifests (redacted, model output) outside Git under the main checkout's
  ignored `.superpowers/evidence/sev2-live/`: baseline `manifest.json` sha256 `df477cd9…5e3`, v2 `338b6eb3…20d`
  (row hashes are also in each published `score.json`).
- Approval identities and the owner's PILOT-only approvals are spent; no identity covers LOCKED.
