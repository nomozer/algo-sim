# Held-out gold encoding record

Label: **INDEPENDENT_AI_AUTHORED_NOT_HUMAN_VALIDATED**.

The encoder was a separately dispatched AI agent. This is an independent gold
annotation relative to provider output, not a human gold standard. No web,
provider, live model/API call or provider output was used. No v3 extraction
prompt, provider response schema, scorer implementation, or live artifact was
read. The preserved corpus and its mathematical oracle were authored by a
different isolated AI agent; this encoder did read those files and therefore does
not claim independence from their mathematical choices or dispositions.

## Inputs and scope

The semantic sources were only the preserved `corpus.json`, `oracle.py`, and
`authoring.md` in this directory. The encoder read `AGENTS.md` and
`docs/RULES.md` for safety, the existing local planner contract (`TypedFact`,
`_CAN`, `doc_du_kien`, `_doc_toan_hang_mo_ta`, `_doc_khoi_tho`) and registry
`Label`/`ExactNumber` definitions. Historical format reference was restricted to
`dev*` entries of `hybrid-semantic-extraction-v2/inputs/gold_facts.json`; the
historical `prelock_corrections.json` supplied representation lessons. Other old
gold entries were not displayed or consulted. A read of the using-superpowers
skill found its explicit subagent exemption; no implementation workflow or
provider discovery followed from it.

A bounded scope deviation occurred: the first planner read requested its first
420 lines rather than extracting only the permitted symbols. That displayed
planner metadata, helper definitions and part of the local planning
implementation in addition to the permitted contract. It exposed no v3 prompt,
provider schema or provider output. Subsequent registry reads used AST extraction
for the requested definitions. The encoder imported the local contract for
validation; imports were offline and bytecode writing was disabled.

A second independence limitation concerns communications. Before the parent
requested aggregate-only updates to preserve its blindness, this encoder sent
small structural descriptions identifying several corpus cases, operand/centre
representation decisions, a response-form limitation, missing-dimension groups,
and sub-solid ownership groups. No complete source problem, oracle answer,
gold file, or provider result was sent. Subsequent updates were aggregate and
provenance-only. This exposure must remain visible to the eventual audit; full
parent blindness is not claimed.

The parent supplied only abstract scorer annotation rules: `required` defaults
to true and controls premise recall; `rid` aligns obligations; `alternatives`
is a list of partial field overrides merged with the main fact. The encoder did
not inspect or run the scorer and did not tune gold against provider output.

Only `gold_facts.json` and this record were created. The three preserved input
files were never rewritten. No commit was made.

## Encoding choices

- All 24 cases retain their 49 requests, in original `rid` order. There are 148
  facts: 99 explicit premise facts and 49 obligation facts. Of the obligations,
  43 use `kind=question` (40 numeric requests and three with missing source
  dimensions); six use `kind=unsupported` (five unsupported requests and one
  ambiguous request). Missing dimensions are not invented or encoded as zero.
- Every fact has a verbatim source substring in `quotes`; semantic point labels
  and solid symbols normalise Unicode primes to ASCII apostrophes while quotes
  preserve original bytes. No extra point name or numerical result is added.
- Every one of the 50 given-length facts identifies its owning solid, as well
  as a named segment or an explicitly stated edge/height role. Solid notation
  carries the explicitly given ordered vertex correspondence. Explicitly
  requested sub-solids have their own sourced solid declarations and volume
  targets; ownership never transfers to the containing solid.
- Regularity and rightness are retained only when explicitly stated. A regular
  square pyramid or regular quadrilateral prism retains that declaration as a
  whole. Its implicit defining square/rightness conditions are not duplicated
  as extra premises. A square mentioned again as the base or top of such a
  solid is already represented by that declaration.
- A right angle uses `at` for the vertex and exactly the other two ray points
  in `points`. Pairwise perpendicularity is expanded to the three stated
  pairs. Equal numeric legs retain both explicit length values, which also
  retain the explicitly stated isosceles condition; no redundant derived
  equality is added.
- The two explicitly named square centres are encoded by the intersection of
  their existing named diagonals. This is a definitional encoding, with no
  auxiliary point or computed position. Each has two equivalent midpoint-of-
  diagonal alternatives. Four right-angle facts also accept the identical
  perpendicular-lines encoding. These eight alternatives cover six facts and
  were validated mathematically; they never introduce an additional premise.
  No general polygon centroid is substituted for a square centre.
- Finite-segment distance, squared segment length, optimisation over a variable
  line, an explanatory request, and curved-solid volume retain exact requests
  as unsupported facts. The ambiguous unnamed face is unsupported with
  `ambiguous=true`; no plane is guessed. Unsupported facts carry a reason and
  no invented quantity, operand domain or point-definition type.
- The explicitly requested squared cosine uses the existing `quantity=angle`
  and exact operand lists, with the response form preserved in the quote,
  reason and aligned corpus request. The existing TypedFact contract has no
  response-form field. This is a documented interface limitation, not a change
  to the source request, corpus disposition or production schema. The parent
  confirmed that response form is read from the aligned source annotation.
- `required=true` marks the explicit facts. Alternative fields are only
  equivalent existing-contract representations. The gold-only fields
  `required`, `alternatives` and `rid` are removed for contract validation.

## Offline validation observed

Interpreter: `D:/Documents/projects/algo-sim/backend/.venv/Scripts/python.exe`.
Commands were run in the designated worktree at HEAD
`cf6a2d234f6483d68c5163658196b4508637d831`.

The local `TypedFact.model_validate` accepted all 148 facts and all eight merged
alternative candidates. `doc_du_kien` accepted each of the 24 complete fact
sets. `_doc_khoi_tho` parsed all 27 solid declarations. Checks confirmed unique
fact IDs, exact source quotes, declared-only point labels, the two-ray
right-angle convention, length ownership, and all 49 request IDs in source
order. There were no provider calls.

A one-off offline stdin script reused the oracle's exact rational coordinate
helpers, recreated one coordinate model per case, and checked all 99 encoded
premises plus all eight alternative encodings against those models. It then
computed all 40 answerable gold question quantities from their gold operands
and gold solid ownership, comparing the exact squared value/cosine to the
independent corpus oracle. All checks passed. The freely chosen heights for
under-specified figures were used only for checking stated premises and the
single height-independent answer, never inserted into gold.

The original oracle was also executed offline and returned PASS: 24 cases,
eight families, 49 requests, 40 numeric oracles, nine nonnumeric requests,
23 cases with multiple requests and 14 data checks. Its dispositions remain
40 answer, five unsupported, three missing_source and one ambiguous.
Re-run the preserved oracle with:

```powershell
D:/Documents/projects/algo-sim/backend/.venv/Scripts/python.exe docs/evaluation/geometry/runs/semantic-extraction-schema-contract/inputs/heldout/oracle.py
```

The one-off gold-validation script/output was not persisted as another file
because the authorised output allowlist contains only these two files. These
are observed offline checks, not human adjudication or a claim of independent
human verification. No `APPROVED_BY_USER` or `PROVED` status is asserted.

## Hashes

SHA-256 values bind the input and annotation versions checked:

| File | SHA-256 |
|---|---|
| `corpus.json` | `23f9ea9c4ec2f41b2418f41afb4dbca9d7c8c9637a4e21726344683f6d37b9ae` |
| `oracle.py` | `0f4a281ec2911a0c30fd89bd14c4d3388a6e19efb60c48edd5a589dda0ef3875` |
| `authoring.md` | `d5b329a16216535897cb60be615d89f07e722d8c71c89a34100b0910f1f89f98` |
| `gold_facts.json` | `ea33013a5ddfb0b79734621274d9f09a966c31807b2c04ad81a1c88a0408ab96` |

Local contract source hashes (full file bytes; only the reading scopes above were consulted):

| File | SHA-256 |
|---|---|
| `backend\app\simulation\geometry_functions\planner.py` | `64b37313d5d93ad3503dce130af85057e4735d43eddd3d5aa9e3b0076def3b6e` |
| `backend\app\simulation\geometry_functions\registry.py` | `11c136421ff6f41097c9cb46ea95d9e15adbc3298c2d2b4f9644a35749c5374c` |

This record's hash is reported separately to avoid a self-referential hash.
