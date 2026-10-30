# Consolidated Owner GO request — live paired measurement for Hybrid production cutover

**Requested:** one scoped GO to run `live-evaluation-protocol.md` on a new held-out set. This is the last blocker of D-04, D-11, D-13 and GATE-16. No live call has been made. Approving does not switch production.

| # | item | proposal |
|---|---|---|
| 1 | Provider | Google Gemini API (`generativelanguage.googleapis.com/v1beta`, `generateContent`), the Owner's own API key in `backend/.env` |
| 2 | Exact model | `gemini-2.5-flash`, the production default `GEMINI_MODEL`, for both arms |
| 3 | Maximum live requests | **400 HTTP requests**, enforced before each request by `gemini.ApiBudget`. Expected: 60 problems × (Hybrid 1 + LLM_ONLY 2–4) = 180–300 logical calls, plus transient retries. |
| 4 | Maximum cost | **USD 70 hard cap.** The harness refuses to start unless 400 × the per-request ceiling ≤ the cap. **Expected spend is about USD 2–5.** |
| 5 | Data sent | Only the authored problem text plus each arm's system prompt and schema. No images, learner/account data or repository content. |
| 6 | Privacy | Responses are stored locally in the run directory as decoded structured output plus hashes. Keys and headers are never written. Provider-side retention follows the Owner's Gemini API terms, which the Owner confirms. |
| 7 | Early stop | Any served expected-refusal case; 80% of the USD cap; the request cap; 3 consecutive infrastructure failures; any corpus, oracle or code identity change (protocol §5) |
| 8 | Paired method | Same text to both arms in a seeded order; one name-free scorer on the learner-visible exact targets; Wilson 95% and exact McNemar on complete pairs |
| 9 | Held-out independence | A **new** 60-problem set (45 expected-serve, 15 expected-refuse), hand-authored with oracles **before** any run by a **named author other than the implementer** (the Owner or a nominated teacher). It must be absent from `docs/evaluation/**` and `backend/tests/**`. Without a named author the run is only `IMPLEMENTER_AUTHORED_DIAGNOSTIC` and **cannot** satisfy D-13. |
| 10 | GO/NO-GO for Hybrid production | Protocol §7: Hybrid wrong-served 0 (upper bound ≤ LLM_ONLY); served-correct not worse (McNemar, ≥ −5 pp); 100% expected-refusals refused; median latency ≤ and p90 ≤ 1.5× LLM_ONLY; USD per served-correct ≤ LLM_ONLY; infrastructure ≤ 5%; independence established |
| 11 | What Claude does after the GO | Freeze the corpus and oracle hashes into the protocol; run `--live`; write rows, summary and the stop reason; independent review; then, **only if §7 passes**, prepare the D-13 cutover, which is a separate Owner decision. If §7 fails, report NO-GO with the failing criterion and keep LLM_ONLY. |

**Basis for item 4:**
- Payload sizes were measured offline: Hybrid 8 297 chars; LLM_ONLY analyze 11 782; program 13 169 per attempt.
- The ceiling is conservative: 1 char ≥ 1 token, plus framing.
- Prices are the repository's recorded `gemini-2.5-flash` figures, **USD 0.30 / 2.50 per million input/output tokens** (`run_hybrid_ab_pilot.py`). **The Owner must verify them against current provider pricing** before approving.
- **LLM_ONLY production sends no `maxOutputTokens`**, so its output is reserved at the model maximum. The proposal uses 65 536 tokens, which **the Owner must confirm** from the provider documentation. With that reservation the ceiling is about USD 0.17 per request.

**What the Owner must provide:**
1. An approval JSON written by the Owner, containing `owner_decision`, `corpus_sha256`, `max_requests`, `max_usd`, `model`, the two prices and `llm_only_output_reservation_tokens`.
2. The name of the independent author.
3. `ALLOW_LIVE_AI=1` with the key for the run.

The agent never writes the approval value.

**What it does not authorize:**
- changing `DEFAULT_MODE`;
- deleting LLM_ONLY;
- spending beyond the cap;
- reusing any opened corpus as held-out.
