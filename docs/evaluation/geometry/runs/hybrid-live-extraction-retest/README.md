# Run `hybrid-live-extraction-retest`

C26 of `ALGOSIM_MASTER_HYBRID_BACKEND_REPLACEMENT` (backend only; `frontend/**` untouched): extraction reliability
repairs found in the 64 captured live Run 3 payloads, then a new Owner-authorized live campaign (C26, `<= 80` requests /
`<= USD 1.00`) on K-1/S-2/R-1.

- `preregistration.md` — identity, caps, canary, metrics and label rules, committed before any C26 request.
- `candidate_divergence.json` + `frozen-evaluation-candidate.json` — candidate product `d331e75b`, 118 files,
  `276fc548…`; corrects `../hybrid-live-gemini-execution/candidate_divergence.json`.
- `captured-wire-replay-d331e75b.jsonl` — offline replay of the Run 3 extractions (0 provider calls; not live).
- **Report:** [`HYBRID_LIVE_EXTRACTION_RETEST_REPORT.md`](HYBRID_LIVE_EXTRACTION_RETEST_REPORT.md) — `LIVE_REGRESSION_MEASURED`
  (70/70 on one candidate), `LIVE_GEMINI_QUALITY_VALIDATED = NO`, `HYBRID_CUTOVER_BLOCKED`; false refusal 20/39 → 2/39 on
  the shared positives, 0 wrong-served; corrects the C25 live-timeout statement (route live = 60 s / 180 s, not 15 s).
- `canary/` (10 HTTP) + `full/` (59 HTTP, canary rows reused, ledger carried) — C26 live receipts: 69/80 requests,
  USD 0.3499129 / 1.00, 69 × HTTP 200.
- `c26-vs-run3-analysis.json` — scoring by the pre-registered rules; `full-t3-180db769.json` — Full T3 PASS.
