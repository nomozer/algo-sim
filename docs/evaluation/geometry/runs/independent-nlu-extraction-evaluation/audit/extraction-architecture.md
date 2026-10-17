# Phase A — extraction architecture audit (route D, branch B)

Auditor: separate read-only Claude subagent (Agent 2), fresh context, 2026-10-17, at `76dca142`. 0 network calls, no
file changes (`git status` identical before/after). Recorded verbatim in substance; file:line refer to `76dca142`.

## 1. Provider, model, endpoint, key
- `run_ai_fact_route(problem_text, transport)` (`backend/app/ai/fact_extraction.py:112-128`) takes an injected
  transport; no default live transport is wired.
- Live transport `function_calling.live_transport` (`backend/app/ai/function_calling.py:206-232`): raw REST, sync
  `httpx.post` to `https://generativelanguage.googleapis.com/v1beta/models/{model or gemini.MODEL}:generateContent`;
  key in the `x-goog-api-key` header, not the URL; `ALLOW_LIVE_AI == "1"` checked on every send.
- Model id: `gemini.MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")` (`gemini.py:30`). Runners hard-code it and
  pass `model=` explicitly, bypassing the env var. The LLM_ONLY `gemini.call_gemini` still builds `?key=` in its URL
  (`gemini.py:186-189`) — a different path, not route D.

## 2. Generation config (`fact_extraction.build_request`, `:62-68`)
- temperature 0.0, `maxOutputTokens` 8192 (`function_calling.py:40-41`, comment: includes thinking, "Cần đo lại"),
  `responseMimeType: application/json`, `responseSchema = facts_response_schema()`, no `tools`.
- No `thinkingConfig` anywhere in route D: gemini-2.5-flash's default thinking applies and shares the 8192 cap.
- Sizes: SYSTEM_PROMPT 2,518 chars; schema JSON 3,706 chars; full payload with an empty problem 7,176 canonical bytes.
- Whether `responseSchema` is billed as input tokens: not documented in the repo (UNKNOWN); no `countTokens` call exists.

## 3. Prompt, TypedFact, fingerprint
- Prompt `fact_extraction.py:22-47`, ten rules (extract only; roles premise/prove/condition/question; negated/ambiguous,
  do not guess; verbatim quotes; measures; no coordinates/code; section, intersection line, relation planes, line_ref).
- TypedFact `planner.py:55-86`, `extra="forbid"`; kinds: solid, polygon_shape, right_angle, length, equal_lengths,
  perpendicular, altitude, projection, point_def, section, intersection_line, question, unsupported; quantities: volume,
  area, length, distance, angle; required slots per kind `_CAN` (`planner.py:156-160`); planner `geometry-fact-planner/7`.
- `surface_fingerprint()` = sha256 of `build_request("")` minus contents (prompt, config, schema; not the model id).
  Current B = `485d3834db8b18cfdb24143bfbb14deb8f5b7a9d74cb612d48db8c08252e507a`, locked by prefix in
  `test_function_discovery_planning.py:421-422`.

## 4. Validation and refusal codes for bad output
- `parse_response` (`:77-109`): envelope only — PROVIDER_RESPONSE_INVALID, MALFORMED_RESPONSE_PART, PROVIDER_BLOCKED,
  NO_CANDIDATE, RESPONSE_TRUNCATED (MAX_TOKENS), PROVIDER_REFUSED, JSON_INVALID.
- Pydantic in `planner.doc_du_kien` (`:164-218`): SCHEMA_INVALID (also empty facts, duplicate ids), FACT_INCOMPLETE,
  DEGENERATE_LINE, UNKNOWN_DERIVED_REFERENCE, DERIVED_REFERENCE_TYPE_MISMATCH; planner: AMBIGUOUS_FACT,
  CONDITIONAL_CLAUSE, UNKNOWN_SOLID, AMBIGUOUS_REFERENCE, UNSUPPORTED_CAPABILITY, PLANE_NOT_UNIQUE, PLAN_TOO_LARGE,
  DEPENDENCY_CYCLE; registry `doc_ke_hoach` re-validates generated calls.

## 5. Source grounding and goals
- Quotes are copied into every emitted call (`planner.py:261-265`) and checked by `registry.kiem_nguon`
  (`registry.py:1295-1391`, five tiers): QUOTE_NOT_IN_SOURCE, UNKNOWN_LABEL, GOAL_CLAUSE_NOT_PREMISE, CONDITIONAL_CLAUSE,
  NEGATED_CLAUSE, PREDICATE/PLANE/ROLE_NOT_IN_QUOTE, AMBIGUOUS_VALUE_QUOTE, UNGROUNDED_VALUE, SOURCE_OBJECT_MISMATCH,
  SOURCE_PREMISE_UNREAD, QUESTION_CONTEXT_UNSUPPORTED.
- Clause role is decided from the source text (`_vai_tro_tai`, `registry.py:1159`), not from the model's `role`.
- `run_fact_route` observes goals/negations on one configuration only (`function_route.py:116-159`,
  `can_present_as_proven=False`); any negated fact → NEGATED_CLAUSE; goals without a numeric answer → PROOF_UNVERIFIABLE.

## 6. Multi-request and missing information
- `_kiem_du_kien_cau_hoi` (`registry.py:1395`): every asked object phrase must be bound by a validated ask call or an
  effect-chain certificate, else REQUEST_NOT_ANSWERED. Missing data surfaces as MISSING_DIMENSION /
  UNDERDETERMINED_POINT / FACT_INCOMPLETE; `unsupported` → OUT_OF_SCOPE. No fallback to LLM_ONLY.

## 7. Timeout, provider error, MAX_TOKENS, blocked, malformed
- `live_transport`: one attempt, no retry, 60 s default timeout; non-200 → `ProviderHTTPError(status, json body|None)`.
- `run_ai_fact_route`: LiveAIDisabled → LIVE_AI_DISABLED; any other exception → PROVIDER_ERROR (class name only, HTTP
  status lost unless a runner captures it).

## 8. Has branch B ever run live? No
- Every `run.json` under `docs/evaluation` records 0 live calls for route D (`hybrid-compiler-selection`,
  `ai-function-route`, `hybrid-ab-pilot-readiness` SMOKE/FULL NO_GO).
- Nearest real-model run: unmerged `feat/real-model-pilot-tooling` @ `471a2c79` (`g05-real-model-pilot`): LLM_ONLY via
  `run_pipeline`, gemini-2.5-flash, 16 problems; 33 logical / 47 HTTP attempts (14 retries after 120 s timeouts);
  31 responses: input 89,173, output 27,680, thinking 107,170 tokens; cost upper bound USD 0.3639 (74 % thinking).
  Per analyze call ≈ 1.7k input, 340–560 output, 570–1,490 thinking tokens.

## 9. Reusable tooling
- `backend/scripts/run_hybrid_ab_pilot.py`: generic `canonical_json/_sha`, `reserve_payload`, `PilotBudget.reserve`,
  `redact`, `_persist` (atomic write, read-back, secret byte-scan), `_usage`, approval-file pattern; bound to its run:
  inputs, hashes, SMOKE ids, A/B schedule, scorers, 3072 cap. Reuse by import, single-arm loop of its own.
- `certify_hybrid_ab_pilot.py` (fixture provider, network-patch certification), `live_retry_apparatus.py` (photo route,
  single case), `certify_acceptance_runner.py` (LLM_ONLY only) — not applicable as-is.
- Test network guard `backend/conftest.py:114-152` (autouse; removes the key, patches httpx transports) — disabled if
  `ALLOW_LIVE_AI=1` is set in the shell.

## 10. Prices
- `run_hybrid_ab_pilot.py:27-28` 0.30 / 2.50 USD per 1M; `api_usage_log.py:41-46` same for flash. Re-checked by the main
  agent on ai.google.dev/gemini-api/docs/pricing on 2026-10-17: gemini-2.5-flash paid Standard input 0.30, output 2.50
  (thinking included); free tier "free of charge". Deprecations page: gemini-2.5-flash not deprecated, no shutdown date.

## 11. IDE model name vs API model id
- No repo document maps an IDE (Antigravity) model selection to an API model id; `RUN2_PROTOCOL.md:252-254` notes newer
  models listed by ListModels. The evaluation locks the API id `gemini-2.5-flash` and checks `modelVersion` per response.

## 12. Risks
1. Key leakage via `?key=` exists only on the LLM_ONLY path; route D uses a header; `redact` + byte scan cover artifacts.
2. Thinking tokens with no `thinkingConfig` may hit the 8192 cap → RESPONSE_TRUNCATED (pilot criterion).
3. Schema subset: `_openapi` keeps a limited OpenAPI subset; Label/ExactNumber validators are not in the schema, so a
   response can pass the provider and fail later as SCHEMA_INVALID.
4. Temperature 0 is not determinism: persist raw responses; do not re-call to reproduce.
5. Byte-based token reservation is not tokenization.
6. Cost of failed/timeout calls is UNKNOWN.
7. `ISSUE-OPS-HYBRID-PERSISTENCE-FAILURE-UNRECOVERED` is OPEN (atomic write failed twice, cause unknown).
8. The exact `modelVersion` string returned live is UNVERIFIED (only fakes tested).
9. Thought summaries as text parts would break JSON parsing (not requested; UNVERIFIED).
10. HTTP status is lost in `PROVIDER_ERROR` unless the runner captures it.
