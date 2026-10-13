# Source grounding integration and research closure — LOCAL, 2026-10-13

User-authorized final independent review, ff-only main integration and push, physical cleanup and read-only research audit.
No new feature, live provider request, Hybrid enablement, cache change or history rewrite.

Final review found one previously undeclared Important safety gap, present at main `7767c7e1`, prior review `90ce6497`
and product `b264828f`: overlapping quotes of one length call could spend that value twice. Source `SA = 3 và SB = 3.`
or `SA = 3, đổi AB thành 3.` served SC = √17 when its SA call listed a short quote before the whole sentence.
This corrects the numeric one-use claim of `source-grounding-completeness` §2; that historical report remains untouched.
Product fix `c30049fd` gives each validated call field one numeric budget across all its quotes, in the same authority.
RED 4 failed / 14 passed; GREEN 227 passed / 1 xfailed. Independent follow-up NON-BLOCKING: 415 passed / 1 xfailed,
12 extra route probes, including equal values on distinct validated fields. See [review.md](review.md).

Declared residuals remain open: goal joined to hypothesis by bare và/song; numberless relation inside another call's
long quote; a goal value without a validated value. All reproduce at the baseline; no full Vietnamese coverage claim.
Integration gates, cleanup outcomes and research preservation are recorded below after execution.
