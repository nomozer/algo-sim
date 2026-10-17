# Live approval request — paired extraction pilot (baseline vs v2)

Status: **LIVE_NOT_AUTHORIZED**. Nothing has been sent. This page asks the owner for one decision: **GO PILOT** (24
requests). LOCKED (48 requests on the heldout split) needs a second, later GO after the pilot gate.

| item | value |
|---|---|
| provider / model | Google Gemini API `gemini-2.5-flash` via the existing `live_transport` (key in header); a different `modelVersion` stops the run |
| arms | `baseline` = saved original prompt (surface `485d3834…`) · `v2` = candidate prompt (`c4e4392c…`); same product `b5406c91…`, same schema |
| PILOT | 12 dev cases × 2 arms × 1 sample = **24 requests**, **0 retries**, one process per arm |
| LOCKED (later GO) | 24 heldout cases × 2 arms = **48 requests**, 0 retries |
| caps per arm | PILOT 12 calls · 400k accounted tokens · **USD 0.50**; LOCKED 24 calls · 800k · USD 1.00 |
| worst-case reservation | PILOT baseline 235k tok / USD 0.29, v2 260k / USD 0.29; LOCKED 472k / 0.57 and 521k / 0.59 (payload + 8,192 output cap per call) |
| expected cost | ≈ USD 0.09 pilot, ≈ 0.18 locked (baseline locked averaged ≈ USD 0.0037/call); list price, billing may be 0 on the free tier, whose terms allow Google to use prompts |
| data sent | the product system prompt + response schema + each case's synthetic problem text only |
| raw output | only under git-ignored `.superpowers/sev2-live/` (refused elsewhere before any request); published: derived `score.json` with identity, usage and the manifest row hash |
| stop rules | cap would be exceeded (before sending) · HTTP 400/401/403/429 · 3 consecutive infrastructure failures · secret detected · model drift · unknown usage · persistence failure · uncertain in-flight request on resume |
| pilot gate → ask LOCKED GO | both arms complete, no stop, usage on every answered row, **no unsafe or unscorable served row** |
| decision (LOCKED) | P1: 0 WRONG/PARTIAL/OVER/FORM_MISMATCH and no UNSCORABLE. P2: goal/entity on expressible ≥ 0.85, operands ≥ 0.85, solid ≥ 0.85, no invented entities. Paired per-case/per-family changes; descriptive only |
| what it does NOT mean | Hybrid enablement, general Vietnamese understanding, human-validated labels, population accuracy |

Known ceiling (GOLD, 0 calls): perfect extraction serves 2/12 dev and 2/24 heldout cases; the pilot mainly measures
extraction agreement, unsupported detection and invented labels per arm.

## How the owner approves (an agent never writes these files)

Each arm needs its own approval file: the gate compares `identities[mode]` with that arm's exact identity
(`approval-identities.json`, produced at `c640cd14`). Run from the research checkout's `backend/` at a commit whose
measured product, prompt, protocol and scripts equal `c640cd14` (the identity check refuses anything else). The key comes
from that checkout's `backend/.env` (git-ignored, not present in a fresh worktree) or from `$env:GEMINI_API_KEY`. PowerShell:

```powershell
$id = (Get-Content ..\docs\evaluation\geometry\runs\hybrid-semantic-extraction-v2\approval-identities.json -Raw | ConvertFrom-Json).identities
foreach ($arm in "baseline","v2") {
  @{ decision = "HUMAN_APPROVED_LIVE_EXECUTION"; identities = @{ PILOT = $id."$arm-PILOT" } } |
    ConvertTo-Json -Depth 8 | Set-Content "$env:USERPROFILE\sev2-approval-$arm.json" -Encoding utf8
}
```

Runs (or ask the agent to run them with these files):

```powershell
$env:ALLOW_LIVE_AI = "1"; $env:PYTHONIOENCODING = "utf-8"
foreach ($arm in "baseline","v2") {
  .venv\Scripts\python.exe scripts\run_semantic_extraction_evaluation.py live --arm $arm --mode PILOT `
    --approval "$env:USERPROFILE\sev2-approval-$arm.json" --out ..\.superpowers\sev2-live\pilot-$arm
}
```

Any change to corpus, gold, oracle, protocol, preregistration, scorer, frozen runner, helpers, product or prompt changes
the identity and voids the approval automatically. The earlier `nlu-approval.json` belongs to another protocol and does
not match.
