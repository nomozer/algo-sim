# Run `hybrid-live-extraction-retest`

C26 of `ALGOSIM_MASTER_HYBRID_BACKEND_REPLACEMENT` (backend only; `frontend/**` untouched): extraction reliability
repairs found in the 64 captured live Run 3 payloads, then a new Owner-authorized live campaign (C26, `<= 80` requests /
`<= USD 1.00`) on K-1/S-2/R-1.

- `preregistration.md` — identity, caps, canary, metrics and label rules, committed before any C26 request.
- `candidate_divergence.json` + `frozen-evaluation-candidate.json` — candidate product `d331e75b`, 118 files,
  `276fc548…`; corrects `../hybrid-live-gemini-execution/candidate_divergence.json`.
- `captured-wire-replay-d331e75b.jsonl` — offline replay of the Run 3 extractions (0 provider calls; not live).
