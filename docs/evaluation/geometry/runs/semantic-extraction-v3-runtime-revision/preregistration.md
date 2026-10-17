# Runtime revision preregistration — before offline measurements

Parent: `semantic-extraction-schema-contract`, lock 5c58774d; takeover 7168d269. Owner authorization:
`GO_RUNTIME_RECOVERY_AND_OFFLINE_REVISION` (2026-10-18), explicitly excluding live/integration.

Only two evaluation changes: a semantics-preserving possessive separator in the shared question-tail grammar,
and split selection before GOLD/replay route processing and reference GOLD. Full artifact hashes and each split's
source order remain. The parent prompt, flat/v3 schemas, model gemini-2.5-flash, scorer grounded-source-obligations/3,
mathematical oracle, source/gold, thresholds and live caps are unchanged. Corpus/gold are byte copies; the new oracle
entry point delegates to the unchanged parent oracle. All originals remain in the parent run and original worktree.

The two arms remain flat/v3; PILOT is 12 exposed dev cases and LOCKED is 24 previously authored held-out cases.
The held-out source prefix/span of h07 was inspected to diagnose the parent runtime stall. These are now **reused
diagnostic data, not fresh blind evaluation**. No locked outcome is a candidate tuning signal. Any future claim of
fresh independent held-out extraction accuracy requires a separately authored, preregistered corpus and owner GO;
this revision makes no such claim. Gold remains AI-authored, not human-validated; parent review limitations carry forward.

Eight offline invocations run sequentially after a matching candidate, independent revision review and one-time lock:
PILOT then LOCKED, flat then v3, GOLD then synthetic REPLAY. One sample per case; zero real provider calls/retries.
Each child has a **120-second watchdog**; exceeding it yields INCOMPLETE_TIMEOUT, never a geometric REFUSED result.
Capture actual Python exit, wall duration, full input identity, manifest row hash and score-file hash per invocation.
Persist the invocation ledger before/after each child; stop on the first nonzero exit, timeout, identity drift,
missing/invalid receipt, incomplete schedule, infrastructure row, or nonzero live counter. No overwritten destination,
automatic rerun, skipped failure, or shell pipeline hiding a child's exit. Original task absence is checked before launch.

Report GOLD deterministic ceiling, synthetic replay wiring, safety/refusals and schema limitations separately.
GOLD/REPLAY are not model extraction accuracy; their usage/latency are synthetic/local, not live cost evidence.
Wrong/unscorable serves remain measured outcomes under the unchanged scorer, not reasons to tune source/gold/thresholds.
The batch's execution PASS means complete valid receipts, not automatically safe mathematical results or product readiness.

Live envelope remains unchanged for later preparation only: per arm PILOT 12 calls/12 attempts/800000 accounted tokens/
USD0.50, LOCKED 24/24/1600000/USD1.00; one sample, zero retries, provider timeout90s. Parent live stop rules and
thresholds are copied unchanged into the revision identity. No approval is created here. Stop at GO_LIVE_PILOT_REQUIRED;
separate future decisions for LOCKED live and GO INTEGRATION. LLM_ONLY, default flat, cache125, Hybrid NO-GO.
