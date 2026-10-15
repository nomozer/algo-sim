# Independent review — shared ask grammar `9ce1298f` (2026-10-15)

**Reviewer:** fresh-context, read-only Claude Code subagent (LOCAL), given only the repository and a written brief.
It made 0 model/network calls and did not modify the repository. It created 7 temporary worktrees (head, `8da9ae31`,
mutants a–e) and removed all of them.

**Reviewed:** `2427289a → 8da9ae31 → 5f1b576c → 9ce1298f`. This includes the previously unreviewed delta
`2427289a..8da9ae31`. `9ce1298f` changes only `backend/scripts/report_holdout_readiness.py`.

**VERDICT: BLOCK.** CRITICAL 4 · IMPORTANT 3 · NONBLOCKING 4.

The integration session independently reproduced C1, C2 (length ask), C3 (MAT_SONG_SONG) and C4 (unit), with the
outputs listed below. The scripts are in `probes/`, with outputs `*-5fc1645c.txt` measured at `5fc1645c`, whose
product tree is the same as `5f1b576c`.

## Preregistered probe (unedited) at 9ce1298f

Route B: 0 WRONG_SERVED · 84 CORRECT_REFUSAL · 36 CORRECT_SERVED · 3 FALSE_REFUSAL (P11, pre-existing).
Route A: 0 WRONG_SERVED · 52 CORRECT_REFUSAL · 20 CORRECT_SERVED.
The reviewer found the probe set too narrow: its own probes still produce wrong serves.

## CRITICAL

- **C1 — a goal clause swallows the words before the first question stop.**
  - Where: `_kiem_du_kien_cau_hoi`, `if muc: doc(start + min(muc), first)`. The follow-up goal branch reads to the
    next stop and splits only on ";".
  - Served on all 8 ask kinds and both routes:
    - "Chứng minh BD ⊥ SC; kết quả lấy bình phương; tính {O}."
    - "Chứng minh BD ⊥ SC, nhân đôi kết quả và tính {O}."
    - "Tính {O} rồi suy ra đáp số là bình phương của nó."
    - "Chỉ ra đáp số gấp đôi: tính {O}."
    - …
  - **Regression:** G1-line and G7-line were refused at `8da9ae31` by the sentence-wide denylist that `5f1b576c` removed.
  - Reproduced: `probes/residual_goal_and_followup-5fc1645c.txt` (lines 1–3).
- **C2 — a sentence after the question is not read** if it holds a request verb or a given marker but no asked phrase.
  - Pre-existing; served at `8da9ae31` too.
  - Served: "Tính {O}. Hãy tính kết quả dưới dạng bình phương.", "Tính {O}. Đáp số nhân đôi, biết SA = 3.",
    "Tính {O}. Hỏi kết quả nhân đôi bằng bao nhiêu?", "Tính hai lần {O}. Tính {O}." …
  - Also served on the `line_ref` answer.
  - Reproduced: lines 4–5 of the same file.
- **C3 — derived-plane `ask_section_area` (MAT_SONG_SONG / MAT_HAI_DUONG) bypasses the closed grammar and the sentence
  reading.**
  - Where: `mat_song_song_dung_nguon`, `_mat_hai_duong_dung_nguon` use `_duoc_hoi` only, and `_CUM_HOI` does not match
    "(P)", so `phrases` is empty.
  - Served 1 for "Nhân đôi kết quả, tính diện tích thiết diện … với (P).", "Tính nửa / bình phương / hai lần …",
    "… (kết quả nhân đôi)". Pre-existing.
  - Reproduced: `probes/residual_derived_section-5fc1645c.txt`.
- **C4 — the closed unit grammar admits a unit change.**
  - Givens are in cm. "Tính độ dài SC (đơn vị: mm)." / "theo đơn vị mm" / "(mm)" / "(đơn vị m)" are served `√17`
    without conversion. `cover()` already refuses a unit mismatch for local givens. Pre-existing.
  - Reproduced: `probes/residual_unit-5fc1645c.txt`.

## IMPORTANT

- **I1:** the candidate was not refrozen after `5f1b576c`. Done since, at `5fc1645c` (`4b95dcc6…`).
- **I2 — new false refusal of a standard wording:** "Xác định thiết diện của hình chóp S.ABCD cắt bởi (MAB) và tính
  diện tích thiết diện đó." (also "rồi tính", and derived (P)). The construction object before "và/rồi tính" is residue.
  Served at `8da9ae31`.
- **I3 — other new false refusals:** "Dựng hình chiếu của S lên (ABCD) và tính SC.", "(đơn vị diện tích)",
  "(làm tròn đến chữ số thập phân thứ hai)", "(làm tròn đến 0,01)".

## Prior findings

- CRITICAL-1 is closed only for the prefix shapes (W1–W8, NFD/NBSP/tab/newline, missing space); open through C1/C2/C3.
- CRITICAL-2 is closed apart from C4.
- IMPORTANT-1 is closed: the reused-foot branch reads `de` within the quote span; Q1 refused, Q2/Q3 served.

## NONBLOCKING

1. The test edits are legitimate. The tail-check mutant changes only SERVED→REFUSED over 855 rows; the asserted-value
   mutant changes nothing. Each equivalence test asserts one sentence only.
2. The harness fix is correct. `endswith("favicon.svg")` would ignore any path ending so; an exact
   `?? frontend/public/favicon.svg` match would be safer.
3. No hardcoded examples. The squared/half denylist is gone. `_GAN_GIA_TRI`'s verb list predates this wave.
4. Small pre-existing false refusals: quotes with an extra space or padding on aux/reused feet, and NFD text on the aux
   line, give AUXILIARY_RULE_MISMATCH.

## Tests and mutations

- 11 files in a clean worktree at `9ce1298f` with the favicon copied: 1352 passed, 1 xfailed.
- `tests/geometry`: 9 failed (all I1), 7270 passed.
- Mutation (a), residue check off: 48 killed. (b), old open bracket: 42 killed. (c), spliced reused foot: 2 killed.
