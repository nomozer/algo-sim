# Provider facts for the live GO, from official sources (read 2026-10-31)

Read with WebFetch from Google's Gemini API documentation. 0 API calls. These facts can change; re-check them on the day of the run.

| fact | value | source |
|---|---|---|
| Model available | `gemini-2.5-flash` is "not deprecated and will continue to be served until further notice". **However, access to the 2.5 models is limited to users who have actively used them in the past.** Availability depends on the Owner's account history. New projects are pointed to newer models. | https://ai.google.dev/gemini-api/docs/models |
| Price (paid tier, standard) | Input **USD 0.30 / 1M** tokens (text). Output **USD 2.50 / 1M**, including thinking. Page "Last updated 2026-10-28 UTC". These match the repository constants. | https://ai.google.dev/gemini-api/docs/pricing |
| Token limits | Input 1 048 576. **Output 65 536.** | https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash |
| Thinking | On by default for 2.5 Flash. Billed as output. **Counts toward `max_output_tokens`**, "including thought tokens". | https://ai.google.dev/gemini-api/docs/thinking |
| Rate limits | RPM/TPM/RPD are shown only in AI Studio, per project. Tier 1 also has a **USD 10 per rolling 10-minute window** spend-based limit, so a fast run can hit 429s. | https://ai.google.dev/gemini-api/docs/rate-limits |
| Provider-side caps | Prepay balance stops keys (HTTP 402) but is "subject to overages during the approximately 10 minute billing pipeline latency". Tier caps are monthly (USD 250 for Tier 1). Project spend caps are "Experimental", with overages possible. **There is no instant hard stop on the provider side.** | https://ai.google.dev/gemini-api/docs/billing |
| Data use | **Unpaid** quota: content is used to improve products, and human reviewers may read it; do not submit sensitive data. **Paid** (Cloud project with active billing): prompts and responses are not used to improve products; they are logged for a limited time for abuse/legal purposes only. | https://ai.google.dev/gemini-api/terms |

## Consequences for the measurement design

1. **The hard cap is enforced client-side, before every HTTP request.** It is computed as accounted spend + a per-request ceiling, compared with `max_usd`.
   - **Per-request output** is bounded by the model's 65 536-token output limit, because thinking is included. This is the limit LLM_ONLY runs under, since it sets no `maxOutputTokens`.
   - **Per-request input** is bounded by the measured payload plus the problem text.
   - **Resulting ceiling:** about USD 0.169 per request (`worst_case_request_usd`).
   - A provider-side prepay balance or project spend cap is recommended as a **second** line only, because it can overshoot.
2. **Run on a paid (billed) project, not free quota.** The free tier permits human review and product use of the content.
3. **Pace requests** below Tier 1's USD 10 / 10-minute window. Count 429 retries as requests, which `gemini.ApiBudget` already does.
4. **If the Owner's account cannot access `gemini-2.5-flash`,** the production default model itself is unavailable. That is an Owner/product decision, and the evaluation must not silently switch models.
