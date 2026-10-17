# Correction layer — reported beside the locked score, never instead of it

`rescore_ignoring_unused_slots.py` → `scorer-unused-slots.json`. 0 model calls; runner, labels, gold, oracle and recorded
rows untouched. Reviewed by an independent agent (`../review.md`): sound, minimal in effect (`question.measure` alone
removes the unsafe row), hides no unsafe case.

Artifacts of the frozen scorer recorded but NOT corrected (no class changes):
- L35: the camera request was emitted as `unsupported` with the right quote but role `premise`; gold has role `question`,
  so `unsupported` flagging scores 0/12 instead of 1/12 in substance.
- Seven name-only `polygon_shape {shape: triangle}` facts (L21, L22, L24 ×3, L28, L41) count as unmatched premises
  although the planner ignores them (`planner.py`, "chỉ đặt tên"); precision would be ≈ 142/175.
- L14 counts as complete although the user sees cos², because only L07 was labelled as asking degrees.
- The pilot analysis (`../results/live-pilot/analysis.md`, committed) reports upper medians: true medians are latency
  7.0 s, input 784.5, output 532, thinking 822 tokens.

Structural weakness for the next protocol: a served row is judged through fact pairing, so a harmless slot difference
on a served question makes a correct answer "unasked" without comparing its value. The next scorer must compare every
served value with the oracle through the route's own call operands, independently of extraction pairing.
