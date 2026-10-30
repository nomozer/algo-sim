# Pre-freeze adversarial review: NOT_READY (1 BLOCKER), then resolved in the fix commit

**Who and what:** a fresh-context subagent of this session reviewed `e5dc3d28..0e555bad`.

**Conditions:**
- Read-only, 0 provider calls.
- The base comparison used `git archive e5dc3d28 backend/app`. The older `996f114b` worktree is not the base product.
- The harness blocked a report file, so the findings are transcribed here.
- Probes and outputs are copied to `pre-freeze-review/`. Hashes, including 2 files kept local because they contain a local path, are in `pre-freeze-review-files.sha256`.

| id | sev | finding | disposition |
|---|---|---|---|
| B1 | **BLOCKER** | Adding `chiều cao` to the `_C_DOAN` prefix bound "chiều cao XY = n" as a plain length of XY, so the claim that XY *is* the height was never checked. Three contradictory problems were SERVED with wrong answers that base refuses: a regular pyramid with "chiều cao SA = 3"; SP ⊥ base with "chiều cao SQ"; SD ⊥ base with "chiều cao SE". My 10 negatives did not catch it, because none had a payload that agrees with the wrong reading. | **Fixed.** `_vai_doan_ok` reads a role prefix only when it is proved. A height must be XY ⊥ base, using the same predicate as the `dcao` clause, or a lateral edge of a *right* prism. A lateral edge must join the apex to a base vertex, or a base vertex to its top vertex. It applies in both consumers (`_lien_ket_cau` binding, `_cau_tien_de_dong_hop_le`). An amendment corpus `dev-corpus/role-claims.json` adds 3 negatives whose payload agrees with the wrong reading, plus 1 proved-height positive. A mutant test shows that without the check, B1 returns. All reviewer attacks are now REFUSED, and genuine heights are still served. |
| M1 | MINOR | `_ly_do_canh_thiet_dien` trusted `face_index`. | **Fixed.** The section edge must lie in the face's plane, the face must be planar, and the face must not be parallel to the cutting plane. Synthetic tests cover an inconsistent face and a parallel face. |
| M2 | MINOR | The floating panel's drag handle uses arrow keys and calls `preventDefault`, but the player still stepped. | **Fixed.** The player ignores `defaultPrevented` keys. |
| N1 | NOTE | "cạnh bên DG" with DG a base side was SERVED on base as well. | **Closed** by the same role check (pre-existing on base). "đường chéo DG" with DG a side is still served; it is pre-existing and recorded as a limitation. |
| N2 | NOTE | On a parallel-to-base cut, the metamorphic oracle cannot detect height errors. | Accepted. The role-claim negatives cover it directly. |
| N3 | NOTE | The premise "(α) ∥ XY" is verified on coordinates; the learner does not see it derived from the givens. | Recorded as a limitation in `pedagogy-rubric.md`. |
| N4 | NOTE | The checkpoint cited `capability-matrix.md` one commit before the file existed. | Noted. |

**What held, per the reviewer:**
- **Grammar probes:** all other adversarial grammar probes were refused on both trees. They covered hidden conditionals and disjunctions behind the new connectors, a wrong vertex in "vuông ở", qualifier mismatches, and "Trong không gian," variants.
- **Targeted locked tests:** 494 passed and 1 xfailed.
- **Justifications:** all 427 justifications on 142 real scenes re-checked independently, with 0 failures. The affine/covector validity of the exact test was confirmed.
- **Frontend:** geometry domain vitest, 879 passed.
- **Cache bump:** justified and complete.
- **Evidence:** the preregistration preceded the product change, and historical evidence holds additions only.

**After the fix (`regression-green3.json`):**
- Wave 3: still **67/72** served-correct, 72/72 negatives, 62/72 reasons, 0 wrong-served, 0 leaks.
- Locked 96/96; 203 probes unchanged.
- Dev corpus 42/42 · 18/18 · 10/10; new grammar tests 74 passed; justification tests 35 passed.

## Re-verification of the fix commit `e4e97758`: READY

The same reviewer re-ran its earlier probes against the clean committed tree and added 34 new attacks aimed at
`_vai_doan_ok`. None was served wrongly, and all 34 are also refused on base. The new attacks covered:
- circular ⊥ quotes;
- an oblique prism declared with a right-prism payload;
- "cạnh bên" or "chiều cao" on a cube top edge or a face diagonal;
- chained or combined prefixes;
- height claims outside the prefix;
- a height foot H that is not a base vertex;
- right-prism base edges;
- multi-solid payloads, which fail closed.

Genuine heights are still served with the canonical answers ("chiều cao SH", "D'D", "EE'"). M1 is closed: 427/427 real
justifications are unchanged and the synthetic inconsistent face returns no claim. M2 is closed by code review.

**N-a:** `regression-green3.json` was measured with the product uncommitted. The reviewer re-ran the same gates at clean
`e4e97758` and got the same results case for case: 67/72, 72/72, 62/72, 0 wrong-served, locked 96/96, 203 probes unchanged.

**Remaining NOTEs, not fixed:**
- "đường chéo XY" is not role-checked; this is pre-existing on base.
- "chiều cao XY" accepts any validated XY ⊥ base, even when X is not the apex. The bound length is still correct.

**N-d:** the B1 fix needs no further cache bump. The registry is not reached from `/api/analyze`, and M1 leaves all real
justifications unchanged.
