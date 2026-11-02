# Run `pedagogical-simulation-integration`

Pedagogical simulation integration of `ALGOSIM_MASTER_HYBRID_BACKEND_REPLACEMENT`: the student-mode display
contract (`docs/DESIGN_BRIEF.md` §79–80) verified and enforced on the real `/api/analyze` → Hybrid `/4` →
`Scene3DExplorer` path. Report: [`ALGOSIM_PEDAGOGICAL_SIMULATION_INTEGRATION_REPORT.md`](ALGOSIM_PEDAGOGICAL_SIMULATION_INTEGRATION_REPORT.md).

- `candidate_divergence.json` — corrects `../hybrid-master-product-integration/candidate_divergence.json`;
  candidate product `adf4a113`, 118 files, `39e9f54b…` (`frozen-evaluation-candidate.json`). The `123e57da` candidate
  and every earlier receipt stay byte-for-byte.
- `fixtures-adapter-2-stated-perpendicular/` — the 41 Adapter /2 preview fixtures re-exported at engine /23; the
  search-telemetry bundle they supersede is unchanged.
- `pedagogical-e2e-browser-receipt.json` + `flow1-student-mode-final-step.png` — real Chromium + `uvicorn`
  (`staging-replay`, `REPLAY_STAGING_SIMULATED`, 0 live provider calls) at the pre-review candidate `444b8c95`;
  `full-t3-e8fc37fb.json` — its Full T3.
- `e2e-review-round-1/` + `full-t3-dbc0316c.json` — the same gates after review round 1 (candidate `fba8b7a7`; adds the
  detector positive control). These are the authoritative receipts.
- `prefix-ui-audit.json` (+ `prefix-ui-audit-probe.mjs`, `prefix-ui-audit-analyze.mjs`) — the pre-fix UI audit.
