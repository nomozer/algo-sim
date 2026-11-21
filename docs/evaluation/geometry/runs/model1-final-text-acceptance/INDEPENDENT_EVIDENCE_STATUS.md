# Independent evidence status — candidate 158

Run `model1-final-text-acceptance` (AXO HYBRID /19), 2026-11-21. Audience: the owner.

## 1. The three evidence classes

| class | what it is | candidate 158 |
|---|---|---|
| A — exposed regression | Holdout-2…6, SLM-Independent-1…3, /12–/14 manifests (used to fix, select or route the product) | measured in /17 (706 cases parser-only, 138 full route): 0 served negatives, 0 invalid scenes |
| B — prospective internal | a new set never used to change 158, frozen before the run, provenance + checked oracle, organised by the team | **Holdout-7** (this run): 58 positive + 22 negative, hand-written by the /19 agent, frozen at `98163cce5` before any case ran; results in `PROSPECTIVE_TEXT_ACCEPTANCE.json` |
| C — external independent | source, sampling and oracle review controlled by people outside the Model 1 team | **NOT_MEASURED** |

Holdout-7 is class B and **only** class B. It must not be cited as external or independent validation.

## 2. Why Holdout-7 is not independent

- Author, sampler and oracle writer are the same agent that audited the parser, the normalizer and the earlier failure
  taxonomies (`PROVENANCE.json → author_bias_disclosure`). Knowledge of the parser may shape wording either way.
- The oracle was checked by machine only (closed form vs. independent coordinates; 376/376 relations), not by a second
  person.
- It is not learner or teacher data; the "learner colloquial" stratum is written by the agent.

What it does guarantee: no case was run, inspected against the product or edited after a run; 0 string and 0 template
containment matches against 29,643 prior strings; thresholds fixed before the run (`/16` values, unchanged).

## 3. Search for an external source (this run)

| attempt | result |
|---|---|
| web search for official MOET exam texts (Toán, hình học không gian) | official reference/exam papers are distributed as PDF/image via aggregators (thuvienphapluat.vn, hocmai.vn, hoatieu.vn, vietjack.com); reuse rights unclear; formulas typeset as images ⇒ would need OCR (owner: no OCR work) |
| moet.gov.vn direct | no text source found in search results |
| teacher / evaluator | none available to this session |

No source was invented and no person was simulated.

## 4. What closes class C

The protocol and template already exist (`../model1-integration-readiness/INDEPENDENT_VALIDATION_READINESS.md`,
`../model1-final-acceptance-premerge/EVALUATOR_MANIFEST_TEMPLATE.json`). An evaluator outside the team supplies the
problems and the oracle (or reviews ours), freezes them with `freeze_acceptance.py`, and the shared harness runs once on
the frozen candidate in a clean detached worktree. Until then: **`EXTERNAL_INDEPENDENCE = NOT_MEASURED`**.
