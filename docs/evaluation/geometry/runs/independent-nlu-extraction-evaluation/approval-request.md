# Live approval request — Gemini extraction pilot + locked evaluation

Status: **LIVE_NOT_AUTHORIZED**. Nothing below has been sent. This page asks the owner for one decision.

| item | value |
|---|---|
| provider / endpoint | Google Gemini API, REST `v1beta/models/gemini-2.5-flash:generateContent` (existing `live_transport`, key in header) |
| model | `gemini-2.5-flash` — not deprecated, no shutdown date (ai.google.dev deprecations page, read 2026-10-17); a different `modelVersion` stops the run |
| cases | PILOT: 16 dev cases × 2 samples · LOCKED: 44 locked cases × 1 (only if the pilot gate says CONTINUE) |
| max API requests | 32 + 44 = **76**, hard caps; **0 retries** |
| accounted-token caps | 629,000 + 864,000 (conservative reservation: payload bytes + 4,096 + the 8,192 output/thinking cap per call) |
| cost cap | **USD 0.77 + 1.06 = 1.83** at paid list price (input 0.30, output incl. thinking 2.50 per 1M; ai.google.dev pricing, 2026-10-17). On the free tier the price is 0, but Google's free-tier terms allow use of prompts to improve its products |
| expected cost | about USD 0.35–0.50 (pilot) + 0.50–0.70 (locked): an estimate from ≈ 2.5–3.5k input, 0.4–1k output and 1–5k thinking tokens per call (thinking unmeasured on this prompt; the last live LLM_ONLY run averaged 3.5k thinking per call) |
| data sent | the product system prompt + response schema + each case's synthetic problem text; no context, labels, gold facts, oracle values, personal data, or repository content |
| receipts | `results/live-pilot/` and `results/live-locked/`: `manifest.json` (redacted raw response, usage, model version, response id, latency per row) + `score.json`; key byte-scan after every write; nothing overwritten |
| expected time | ≈ 5–40 s per call ⇒ pilot ≈ 3–20 min, locked ≈ 4–30 min, sequential |
| stop rules | cap would be exceeded (before sending) · HTTP 400/401/403/429 · 3 consecutive infrastructure failures · secret detected · unknown `modelVersion` · persistence failure · uncertain in-flight request on resume |
| continue pilot → locked | all 32 rows recorded, no stop; ≥ 28/32 parse as facts; ≤ 2 truncated; usage on every answered row |
| decision on locked | P1 safety: 0 unsafe rows (`WRONG_SERVED`/`PARTIAL_SERVED`/`OVER_SERVED`). P2: goal/entity agreement on expressible requests YES if ≥ 0.85 with exact 95 % lower bound ≥ 0.70, NO if upper bound < 0.85, else INCONCLUSIVE |
| what a pass does NOT mean | Hybrid enablement, general Vietnamese understanding, human-validated labels, or learning impact |

Already measured without the provider (deterministic ceiling, `results/gold/`): the gold extraction is served on 8 of the 44 locked cases (7 complete + 1 proof flagged), refused for capability/grounding gaps on 23, and safely refused on 13. So live end-to-end success can be at most 8/44 rows; the measurement mainly answers how well the model extracts, and whether any wrong extraction slips through.

## How the owner approves (an agent never writes this file)

1. Ensure `backend/.env` has `GEMINI_API_KEY` (no other change).
2. From `backend/`, create the approval from the published identities (PowerShell):

```powershell
$id = Get-Content ..\docs\evaluation\geometry\runs\independent-nlu-extraction-evaluation\approval-identities.json -Raw | ConvertFrom-Json
@{ decision = "HUMAN_APPROVED_LIVE_EXECUTION"; identities = $id.identities } | ConvertTo-Json -Depth 8 | Set-Content $env:USERPROFILE\nlu-approval.json -Encoding utf8
```

3. Then the runs (or ask the agent to run them with this file):

```powershell
$env:ALLOW_LIVE_AI = "1"; $env:PYTHONIOENCODING = "utf-8"
.venv\Scripts\python.exe scripts\run_nlu_extraction_evaluation.py --mode LIVE_PILOT --approval-file $env:USERPROFILE\nlu-approval.json --out-dir ..\docs\evaluation\geometry\runs\independent-nlu-extraction-evaluation\results\live-pilot
```

Any change to the corpus, gold, protocol, preregistration, runner, helpers, product or prompt changes the identity and
voids the approval automatically.
