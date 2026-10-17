# Independent review of the live results (Agent 4) and disposition

Reviewer: separate read-only Claude subagent, fresh context, 2026-10-17, after LIVE_LOCKED. 0 provider calls, no
repository writes; offline scripts in its own scratch directory (`integrity.py`, `rows.py`, `diff.py`, `layers.py`,
`nums.py`, `ablate.py`, `cf.py`, `cf2.py`). Verdict: **BASELINE_EVIDENCE_NEEDS_FIXES** — measurement sound, write-ups to fix.

## Confirmed (OK)

- Runner unchanged since the lock (`git diff 6255a743` empty); pilot receipts unchanged since `a9724519`.
- Locked manifest: rows hash OK; identity equals the published LOCKED identity in all 12 keys and the identity
  recomputed today; 44 rows / 44 calls / 44 HTTP attempts (no retry); `gemini-2.5-flash` on every row; 44 distinct
  response ids and payload hashes; no infra or HTTP error; usage on all rows; only non-STOP finish is L12 `MAX_TOKENS`.
- No `AIza`/`key=`/`GEMINI_API_KEY=` string in `results/` or `corrections/`.
- Gold rows reproduce exactly; the frozen score reproduces `score.json` in full (every per-row record), pilot too.
- Clopper–Pearson intervals recomputed with an independent exact rational method: identical to the runner's.
- L01: served the oracle value for the asked object; the neutralised slots are not used by the planner for those kinds
  (`_cau_hoi`, `_doc_khoi`; `solid.points` only feeds the auxiliary-name set, redundantly); the correction is minimal in
  effect and hides no unsafe row. P2 is NO under both scorers.

## Findings → disposition

| sev | finding | disposition |
|---|---|---|
| IMPORTANT | `report.md` / `run.json` stale (LOCKED shown as not run) | rewritten |
| IMPORTANT | L19 live attributed to Planner capability; it is a request without operands | `attribute_layers.py` refines the rule; planner input 30, Planner/Engine 0 |
| IMPORTANT | L40/L44 counted as capability refusals | gold engine stops split: 3 gaps (L17, L19, L29), 2 correct refusals |
| IMPORTANT | wrong-extraction refusals stated as 30 | 34 (30 / 3 / 1) + 1 no-parse |
| IMPORTANT | L23 said to be refused on "suy ra" | live refused on the volume clause; order dependence noted as undiagnosed |
| IMPORTANT | `layer_rows.json` had no generator | `results/live-locked/attribute_layers.py` committed; table regenerated |
| IMPORTANT | structural scorer weakness (served value judged through pairing) | recorded for the next protocol (`corrections/README.md`); frozen score kept |
| MINOR | `_CAN` cited instead of the read sites; `solid.points` is read (redundantly) | analysis cites `_doc_khoi` / `_cau_hoi` |
| MINOR | L02 correct only under the correction; L36 metric change omitted | stated |
| MINOR | L35 used `unsupported` for the request itself (role premise) | stated; not re-scored |
| MINOR | 7 name-only triangle facts lower precision; L14 shows cos² for "Tính góc" | recorded in `corrections/README.md` |
| MINOR | upper medians reported | locked analysis uses true medians; pilot correction noted |
| MINOR | gold L38 `CONDITIONAL_CLAUSE` is the planner role gate, not grounding | attribution distinguishes by reason; gold grounding 18 |
| MINOR | "wordings unseen by the LLM" too strong | "not shown in the prompt" |
| MINOR | safety framing beyond the corpus | analysis states no bound beyond the 44 items |
| MINOR | no LOCKED approval receipt | `approval-receipt.json` (sha256 of the owner's file, identities equal) |
