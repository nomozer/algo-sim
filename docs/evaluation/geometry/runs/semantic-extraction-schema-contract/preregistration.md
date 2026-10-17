# Schema-Contract v3 preregistration

This package is **NOT_LOCKED** until `inputs/prepare_protocol.py --lock` succeeds.
The draft is not live-authorizable. No provider request, human approval, integration
decision, or human validation is implied by offline preparation or a passing review.
The protocol records its actual lock state; this document's initial draft label is
retained after locking as provenance of its premeasurement origin.

The intervention compares `flat` and `v3` response contracts with the same frozen
product prompt and model `gemini-2.5-flash`. The scorer remains
`grounded-source-obligations/2`; the historical executor and earlier evidence are
unchanged. The runner identity binds arm, mode, prompt/schema surface, measured
product, runner/helpers/scorer, combined corpus/gold, oracle, protocol,
preregistration, schedule, and caps. File hashes normalize CRLF to LF.

The 12 development cases are reused from `hybrid-semantic-extraction-v2` and are
**EXPOSED DEVELOPMENT, NOT FRESH EVALUATION**. All prior source requests and gold
objects are copied exactly. The fresh heldout set contains 24 cases in eight
correlated structure families, independently AI-authored, not human validated.
Related structures stay within one split. The corpus/gold assembly preserves every
source request, target, disposition, quotation, oracle value, annotation, and angle
response form (angle versus cos squared). No heldout result is a tuning signal.
The preserved authoring and gold-encoding records disclose isolation limitations,
including encoder access to oracle/planner contracts and structural communications.
Neither full implementer blindness nor independent human ground truth is claimed.

Per arm, PILOT uses all 12 exposed development cases once: at most 12 logical
calls, 12 HTTP attempts, 400,000 accounted tokens and USD 0.50. Paired PILOT total
is 24 calls / USD 1.00. LOCKED uses all 24 fresh heldout cases once per arm:
24 logical calls, 24 HTTP attempts, 800,000 accounted tokens and USD 1.00 per arm;
paired total 48 calls / USD 2.00. There are zero retries and a 90-second timeout.
Costs use the inherited reservation/accounting helper; missing usage is UNKNOWN,
never zero. A stopped or incomplete schedule cannot be interpreted as a pass.

Inherited stop rules apply: HTTP 400/401/403/429, logical/HTTP/token/USD/context cap,
persistence failure, detected secret, model-version mismatch, disabled live AI,
post-response failure, unknown/inconsistent usage, and three consecutive infrastructure
errors. A single other infrastructure failure is recorded without retry. Raw live
manifests belong only in ignored `.superpowers/`; publish derived scores and hashes.

Safety requires **zero unsafe serves and zero unscorable serves**. Extraction targets
are at least 0.85 goal/entity recall, 0.85 operand correctness and 0.85 solid ownership,
with zero hallucinated-entity rows. Goal/entity means `goal_match / requests_gold`
(the scorer's complete goal match binds semantic entities); operands mean
`operand_correct / operand_required`; ownership means `solid_correct / solid_required`.
An empty denominator is UNKNOWN, never an automatic pass. Parse failures remain in
the source-based denominators. Multi-goal completeness and unsupported/schema-gap
coverage are descriptive diagnostics. Correlated-family differences are descriptive
only: no independence-based confidence interval, statistical power, population
accuracy, or causal generalization claim. The paired arms isolate the response
contract under the frozen prompt on these requests; no broader causal claim follows.
GOLD and synthetic REPLAY are route/harness checks, not model extraction accuracy.

Before locking, independent gold/oracle, scorer/candidate reviews must all be PASS
with reviewer identity and exact reviewed LF hashes. The candidate review must name
the current measured product hash, and the frozen candidate must match that product.
The one-time lock binds prerequisite receipts, sources, all input files, runner files,
and all measured product files. Preparation refuses mutation of preserved originals
or an already assembled corpus/gold; any semantic correction requires a separate
declared run/correction layer. A locked protocol cannot be regenerated in place.

Live execution later requires an explicit human GO for each exact arm/mode identity,
using the existing human approval contract; this script never creates an approval.
Fresh pilot and heldout identities remain separate. Integration requires a separate
human GO after final review, verification and refreeze. Default flat extraction,
LLM_ONLY, cache policy and Hybrid NO-GO remain governed by the product decision.
