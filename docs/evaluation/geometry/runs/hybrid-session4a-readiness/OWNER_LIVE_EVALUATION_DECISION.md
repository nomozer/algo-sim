# Owner live evaluation decision required

Status: **BLOCKED — OWNER_GO_REQUIRED; no live calls made**.

Reason: available provider outputs are flat, while the target contract is `typed-fact-next/2`. Authored fixtures and offline replays cannot measure new NL extraction quality, paired provider latency/tokens/cost, or full live E2E behavior. The offline work is complete enough to review without granting live permission.

Proposed next action, **not authorized here**: a separate research-only pilot on the curator's disjoint 12-source pilot set, one baseline `LLM_ONLY` arm and one provider-independent V2 extraction arm per source. Freeze actual provider/model/version, prompt/schema, candidates, input permissions and price schedule first. Do not add a production endpoint or change the default route merely to measure it.

Proposed hard caps: **24 requests total**, no retries, one worker; 120,000 input tokens + 60,000 output/other billed tokens aggregate, **USD 3 maximum**, 90 seconds/request and 30 minutes wall time. Reserve the conservative request token/cost upper bound before each send; stop before a reservation would exceed any cap. Provider-specific thinking tokens and pricing must fit the same total billed budget. If the owner-selected model cannot fit these caps, revise the proposal and obtain GO before execution.

Stop immediately on HTTP 400/401/403/429, any unsafe acceptance, identity/hash/model drift, secret detection, persistence failure, or exceeded request/token/cost/time cap; also stop after two consecutive timeout/infrastructure failures. Record every attempt and partial run. No automatic continuation to the 60-case locked paired benchmark: that needs a separate owner decision after pilot results and fresh identity verification.

Requested owner disposition for the next session: authorize this exact bounded pilot after curator/model/lock completion, revise the bounds, or defer. **There is no approval in this file.** `ALLOW_LIVE_AI=0` and `HYBRID_PRODUCT_ENABLEMENT=NO-GO` remain in force. Session 4A stops only the dependent live measurement, while completing offline reports, replay, protocol and handoff.
