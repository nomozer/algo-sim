# Independent LOCAL reviews — goal-directed section planning

Three fresh-context LOCAL Claude subagents, read-only, each in its own detached worktree (removed without `--force`),
0 provider calls. Probes ran on routes A and B against the reviewed commit and the baseline `132e9b23`.

## Review 1 — Phase A at `87118b61`

Verdict non-blocking as a commit, but the claim was too strong: the first follow-up rule was an open token denylist
(digits, √, π, premise words).

| Finding | Ruling |
|---|---|
| Critical (pre-existing): a change written after "tính lại …" was never read ("Tính SC, sau đó tính lại SC với SA = 5.") | Fixed `062b204f`: every length after the first request must match a validated call; a modified re-request is refused |
| Important: changes without digits passed ("tăng SA gấp đôi", "thay SA bằng SB", "bỏ giả thiết …") | Fixed `062b204f`: closed follow-up vocabulary; token readers removed |
| Important: new false refusals ("gọi M là trung điểm SC", "so sánh SC với 4", "kết luận …") | Accepted as the declared bounded limit (closed vocabulary); documented test `test_open_follow_up_wording_is_a_documented_conservative_refusal` |

## Review 2 — Phases A + B at `926c0bf9`: BLOCKING

| Finding | Ruling |
|---|---|
| I1: an area question naming another section was answered with the (P) area | Fixed `16ac524a` (asked phrase must be the bound section) |
| I2: the definition grammar ignored the rest of the clause ("… (ABCD) và song song với (SBC)") | Fixed `16ac524a`, completed `68fbc844` |
| I3: modified re-request refused multi-part questions ("Tính SC. Tính góc giữa SC và (ABCD).") | Fixed `4571b08b` (direct object of the request verb only) |
| Minor 4 goal clause covering ";" · 5 (P) defined twice · 7 tautology · 8 gate→engine side channel · 9 test hygiene | Fixed `4571b08b` / `16ac524a` |
| Minor 6: Q whose first three labels are collinear | Kept: conservative `COLLINEAR_POINTS` refusal |

All RED before the fixes: 19 failing tests → GREEN.

## Verification — `4571b08b`, `16ac524a`: non-blocking

I1, I3, Minors 7/8 closed. Open: ";" inside the definition sentence and a request-verb lookahead licensing a new
condition ("…; (P) song song với (SBC).", "… và dựng (P) song song với (SBC)."); three new false refusals
("(P) cắt … theo thiết diện. Tính diện tích thiết diện đó.", "; sau đó tính SB" after a goal clause, "… tại M").
Fixed `2bdfc43c` / `68fbc844` (9 RED → GREEN); "… tại M" stays a conservative refusal.

Residuals recorded open (not introduced by this branch unless stated): a change after "," or "và" inside a goal
clause (pre-existing at `132e9b23`); a conflicting second definition of (P) in another grammar ("(P) là mặt phẳng
(SBD)"); a premise sentence outside every quote ("Đổi đáy thành hình vuông cạnh 4. Tính SC." — pre-existing general
coverage gap). No further independent review after `68fbc844`: closure is RED → GREEN, clean-worktree checks and T3.
