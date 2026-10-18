# Decision request — frozen v3 runtime blocker

Status: **WAITING_OWNER_PROTOCOL_DECISION**. This is not a GO LIVE request or an approval.

The locked candidate cannot complete its offline job: the shared question-tail regex has catastrophic backtracking
at held-out h07. See [`takeover-20261018.md`](takeover-20261018.md). The original job `bufr6nkj1` is still running,
with no completed receipt. Nothing has been overwritten or terminated.

Recommended decision: authorize stopping only this identified task tree and preparing a **separate protocol revision**
for the shared grammar runtime correction. Preserve the current lock and the unsuccessful attempt as-is. The proposed
scope is one bounded regex correction, a synthetic runtime regression plus existing safety/grounding regressions,
fresh candidate/review/identity, and new output provenance. Do not change prompt, schema, source/gold, oracle,
thresholds or scorer semantics. Do not use h07's outcome as a tuning target. Do not reuse old receipts as revision evidence.
Disclose access to h07's source/span during diagnosis; reusing this corpus for revision regressions does not restore
implementer blindness or make it a fresh held-out set. Decide the later live-evaluation claim before choosing its corpus.
Any new offline runner must capture individual exits and bound execution without recording a timeout as a geometry refusal.
Do not start a replacement while the original tree is active.

An alternative owner decision is to archive this locked attempt as incomplete and defer the correction. Neither option
authorizes Gemini or integration. After a revision is approved and its offline/final gates pass, prepare a new exact-identity
live request; the current [`approval-identities.json`](approval-identities.json) is for inventory only and will be superseded.

## Locked live envelope, for preparation only

| Item | Locked value |
|---|---|
| Model / arms | `gemini-2.5-flash`; `flat`, `v3`; same product prompt |
| Protocol canonical SHA-256 | `f97af99e54aeb27bc18d244577ec01e92f137e164ff362339ba02a23247f9c68` |
| Product SHA-256 | `1ff71da76d999370897edd3a2dfaf161113e4d24f39dd41cda640ce2aa53dbc7` |
| PILOT cap per arm | 12 logical calls, 12 HTTP attempts, 800,000 accounted tokens, USD 0.50, one sample |
| PILOT paired total | 24 calls, USD 1.00; LOCKED needs a separate later GO |
| LOCKED cap per arm | 24 calls, 24 HTTP attempts, 1,600,000 accounted tokens, USD 1.00, one sample |
| LOCKED paired total | 48 calls, USD 2.00 |
| Retries / timeout | 0 / 90 seconds |
| Stop rules | HTTP 400/401/403/429; logical/HTTP/token/USD/context caps; persistence/secret failure; model drift; disabled live AI; post-response failure; unknown/inconsistent usage; three consecutive infrastructure errors |
| Publication | Raw live output only in ignored `.superpowers/`; publish derived metrics/hashes |
| Current authorization | NONE; v2 approval does not authorize v3; no approval file generated |

Gemini acceptance of the approximately 41 KB / 34-branch schema remains NOT_MEASURED. Hybrid product enablement
remains NO-GO; `DEFAULT_MODE = LLM_ONLY`, default extraction `flat`, cache125. GO INTEGRATION remains separate.
