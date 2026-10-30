# Independent technical review (F7, R1/R2): READY for this gate (0 BLOCKER, 0 MAJOR, 4 MINOR, 4 NOTE)

**Who and what:** a fresh-context subagent of this session reviewed research HEAD `48721da3` (product `dd17fbfb`). It
compared against `1b1a9ed2` (fix reverted in memory) and main `996f114b`.

**Conditions:**
- Read-only on the repositories; 0 provider calls, sockets blocked.
- The harness blocked the reviewer from writing a report file, so its findings are transcribed here.
- Its scripts and raw outputs are copied verbatim into `independent-review/`; the SHA-256 list is in
  `independent-review-files.sha256`.

**Process disclosure:**
- The reviewer briefly wrote 3 untracked probe outputs into the `backend/` folders of two clean worktrees, then moved
  them out.
- I verified `git status --untracked-files=all` = 0 on the research worktree, the clean compat worktree and the main
  baseline.

**READY covers only this review gate.** Publication stays `BLOCKED_PENDING_OWNER_DECISION`, and nothing was frozen and
no T3 was run.

| id | sev | finding | disposition |
|---|---|---|---|
| RV-1 | MINOR | The R2 oracle did not kill a "derived resolves to the first root solid" mutant, because the parent was `solids[0]`. | **Closed, test-only (D2).** The oracle now also runs with the parent solid last, and the first-root mutant is added. Product code is unchanged and handled this correctly: 242 passed. |
| RV-2 | MINOR, pre-existing on main | Other registered alternatives without an a3 branch are refused on a3 as `INVALID_MATH_GOAL`, while pl returns `BRIDGE_UNSUPPORTED_MEASUREMENT` and a4 serves some of them. They are `distance {point,line}`, `{line,plane}`, `{plane1,plane2}`, `angle {plane1,plane2}` and `area {solid}`. Fails closed: no wrong answer is served and there is no internal error. | **Disclosed, not repaired.** It is outside the D1 narrow scope (no internal error). Contract §5 and the handoff now list it as a known limitation. |
| RV-3 | MINOR | `registration.json` kept the pre-amendment builder hash, and `415da751` amended inputs in place. | **Corrected** by the new layer `registration-layer2.json` (builder `20081b24…`). Original bytes are in `ae81b65e`. |
| RV-4 | MINOR | The new contract sentence claimed more than the routes do: an earlier route refusal can apply first. | **Corrected:** §5 now says "when no earlier refusal applies". |
| RV-5 | NOTE | Ordering effect measured: contradictory data plus an unsupported radius on a3 now returns the capability code instead of `INCONSISTENT_FACTS`, the same as pl/a4. A `length_unit` mismatch moved from internal error to the capability code. Everything is still refused. | Disclosed in `root-cause.md` and here. Not pinned by a test. |
| RV-6 | NOTE | `gate-c.json` and `probes203.json` name head `415da751` although they ran on the uncommitted fix. | The reviewer re-ran the locked 96 on clean `dd17fbfb`: 96/96, 0 wrong-served (`independent-review/gatec-dd17.json`). |
| RV-7 | NOTE | The planted-fault test alone cannot see a mask inside the method. The source-anchored mutant test closes that case jointly. | Accepted as is. |
| RV-8 | NOTE, pre-existing | A mixed cylinder+prism payload is refused as `MISSING_CURVED_DIMENSION` for every goal. Fails closed; main is the same. | Recorded limitation. |
| R3 | MINOR | The reviewer agrees with D3: not MAJOR. | Stays DEFERRED, not closed. |

**What held:**
- **Probe sweep:** 3210 route cells (1070 payloads × a3/pl/a4), drawn from all parent cases, all F7 cases, and a
  generated matrix over solid types × goal types × registered alternatives × scope × single/multi-goal.
  - Internal errors or exceptions: main 132, `1b1a9ed2` 45, HEAD 0.
  - HEAD vs `1b1a9ed2`: exactly 45 a3 cells changed, all from `ADAPTER_INTERNAL_ERROR` to
    `BRIDGE_UNSUPPORTED_MEASUREMENT`.
  - 0 served inputs became refused, 0 exact answers changed, 0 wrong-served, and no answer or scene leaked.
- **Fix ownership:**
  - The dispatch `else` is the root-cause owner.
  - No `except` was added.
  - pl/a4 and the curved route have no comparable gap.
- **Mutants:** the R1 identity-before-namespace mutant, both registered R2 mutants and the F7 mutants are all killed by
  behaviour.
- **Amendment and re-pin:**
  - The `415da751` amendment matches the existing oracle.
  - The 8-cell re-pin requires one exact typed code, so it cannot accept an unrelated internal error.
- **Scope:**
  - `CACHE_VERSION` 130, `LLM_ONLY` and Hybrid opt-in are untouched.
  - No historical evidence was modified outside this run's own disclosed amendment.
