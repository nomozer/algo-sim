# Owner adjudication addendum — four fresh-source controls (W3-F2 closed input contract)

Owner decision `W3-F2 CLOSED INPUT CONTRACT ADJUDICATION`, 2026-10-30: the four supplementary controls
`test_fresh_geometry_positive_scope_aliases[id|notation|nested_id|goal_id]` are **outside the current Source Gate
grammar**. `registry.py` is not changed by this task. This addendum is a new layer: `../report.md`, `../gates.json`,
`../green.json`, `../green-attempt.log`, `../source-control-analysis.json` and every earlier receipt stay byte-for-byte.

Research HEAD of the adjudicated product: `4b361c47` (verbatim checkpoint of the uncommitted state left on `5e44d5da`;
backup + SHA-256 manifest `.superpowers/backups/w3-f2-closed-input-contract-20261030-pre-adjudication/`). The product
files equal the hashes in `../stop-verification.json`. Baseline: detached clean `main` `996f114b`. 0 provider calls.

## Four separate questions

| question | finding | evidence |
|---|---|---|
| Mathematical validity | Valid. Right triangle PQR at P, PQ = 3, PR = 4 ⇒ area 6; KP ⊥ (PQR), KP = 6 is the height ⇒ V = 6·6/3 = **12** (exact Fraction). The expected `SERVED`/12 of the four controls stays unchanged. | `pending-source-grammar-controls.json` |
| Source grammar support | Not supported: `QUESTION_CONTEXT_UNSUPPORTED` on all 12 route cells at HEAD. The unread clause is the **named construction request** inside the request text: alone, `Dựng hình chóp K.PQR.` serves; followed by an ask, or joined to it (`Dựng hình chóp K.PQR và tính …` → unread `'hình chóp K.PQR và'`), it is refused. Supporting it needs the request coverage reader in `registry.py` (Owner: out of scope). | `qualification-pending-source-grammar-head-4b361c47.json` |
| Closed Input Contract correctness | No evidence that the patch caused these refusals. On `main`, `id` and `goal_id` already refuse with the same code on all three routes. `nested_id` refuses on `main` before the Source Gate is reached (`UNKNOWN_SOLID_ID` / `BRIDGE_UNSUPPORTED_MEASUREMENT`). `notation` on `main` is SERVED only by Adapter /3, with `source_verification.authority = adapter3.substring_legacy` (Bridge refused `BRIDGE_UNSUPPORTED_MEASUREMENT` ⇒ no Source Gate verdict, documented decision D2 of `_shared_source_gate`). On `main`, Planner and Adapter /4 refuse the same case. The patch makes the Bridge resolve the notation scope, so the Source Gate now gives its verdict. The outcome change on that one cell comes from the Source Gate being **reached**; nothing broke inside the closed-input checks. | `qualification-pending-source-grammar-main-996f114b.json` |
| Pre-registration status | The four were added after the initial RED (`../red.json`) and were never baseline-qualified. They cannot serve as acceptance controls. | `../source-control-analysis.json` (`classification`) |

## Diagnostic wordings tried (exploratory, HEAD, same geometry; scratch runs, not receipts)

| wording of the request part | outcome on a3/pl/a4 |
|---|---|
| `Dựng hình chóp K.PQR. Tính thể tích hình chóp K.PQR.` (v1) | REFUSED `QUESTION_CONTEXT_UNSUPPORTED` |
| `Dựng hình chóp K.PQR. Tính thể tích khối chóp K.PQR.` | REFUSED `QUESTION_CONTEXT_UNSUPPORTED` |
| `Dựng hình chóp K.PQR và tính thể tích hình chóp K.PQR.` | REFUSED `QUESTION_CONTEXT_UNSUPPORTED` (unread `'hình chóp K.PQR và'`) |
| `Dựng hình chóp K.PQR.` with no math goal | SERVED (no answer) |
| `Tính thể tích …` with no simulation goal | REFUSED `EMPTY_SIMULATION_GOALS` |
| `Tính thể tích hình chóp K.PQR.`, `construct_object` quoting `Cho hình chóp K.PQR` (locked supplementary pattern) | SERVED 12; retained, then qualified in receipts |

## Decision applied (amendment 1)

1. The four controls move to `PENDING_SOURCE_GRAMMAR_SUPPORT` (`pending-source-grammar-controls.json`). Their inputs
   were rebuilt from the v1 test source at `4b361c47` and checked equal to `source-control-analysis.json#payloads`. They keep the
   expected outcome SERVED/12 and still run on their own:
   `backend/tests/geometry/source_grammar_pending_diagnostics.py` (an explicit path, not in the default collection or in T3)
   and `tools/controls.py run`. **They are not reported as PASS and not as product-supported.**
2. New acceptance positives `supported-positive-controls.json`: same solids, premises, goals and the four scope forms
   `id`, `notation`, `nested_id`, `goal_id`. They use the same oracle 12 and change only the wording, to the locked
   control `inputs/recovery-supplementary.json`: `construct_object` quotes the given clause and the volume is asked as
   `Tính thể tích hình chóp …`. They were qualified on `main` and HEAD before registration (`amendment-1.md`).
3. The acceptance suite is superseded transparently (`acceptance-manifest.json`, v1 → v2). Gate A reports two
   separate results: Closed Input Contract acceptance, and source-grammar diagnostics.

No oracle, expected outcome, locked corpus, historical result or earlier receipt changed. No xfail or skip.
No Source Gate bypass. `DEFAULT_MODE=LLM_ONLY`, Hybrid opt-in, `ALLOW_LIVE_AI=0`, `CACHE_VERSION` 130.
