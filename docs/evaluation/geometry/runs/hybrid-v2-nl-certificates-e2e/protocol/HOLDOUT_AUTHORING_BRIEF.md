# Brief — authoring an independent Vietnamese geometry holdout

For an author with **no access to this repository, its tests, fixtures or prompts** (a person, or an agent given only this
page). Nothing here has been run; the Owner decides who authors it and when it is registered.

## Task

Write `N ≥ 60` Vietnamese solid-geometry problems (grade 11–12) in the way textbooks and exams word them, plus gold data for
each. Do not look at any existing fixture. Vary wording deliberately: the same assumption said two ways in different items,
different label names, plane names with several labels (`(BCC'B')`), notation `′` and `'`, "tính / tìm / hỏi … bằng bao nhiêu",
premises given before and after the question.

## Mix (target, not a quota to game)

* ≈ 50 % answerable: a single numeric target (distance, angle, volume, section area) with an exact answer.
* ≈ 15 % insufficient data; ≈ 10 % contradictory data; ≈ 10 % a relation that is only to be *proved* (not given);
  ≈ 10 % conditional ("nếu … thì …") or negated premises; ≈ 5 % outside the supported figures.
* Include a *pair* for ≥ 10 problems: same mathematics, different wording.

## Gold per item (JSON, schema `nl-eval-dataset/1`, see `NL_EVAL_PROTOCOL.md` §2)

`problem_text`; `gold.payload` (canonical `typed-fact-next/2` of a faithful reader: solids, premises with `kind/args/quote`,
math goals; quotes verbatim); `gold.expectation` (`SERVE` with exact value computed **by hand or an independent script**, or
`REFUSE` with a category); `provenance` (`author_kind: HUMAN | BLIND_AGENT`, `origin`, `created`);
`exposure: {label: FRESH, in_tests: false, in_prompt: false}`.

## Hand-over

Deliver one file. The Owner registers `{dataset_sha256, registered_before_tuning: true, git_head, registered_at}` **before any
code is tuned against it**, and a second person re-checks a random 20 % of the gold values. An author who also implemented
the pipeline cannot author the holdout.
