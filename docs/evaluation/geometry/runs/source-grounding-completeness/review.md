# Independent LOCAL reviews — source grounding completeness

Fresh-context LOCAL Claude subagents, read-only, each in its own detached worktree (removed without `--force`),
0 provider calls. Probes ran on routes A and B against the reviewed commit and the baseline `7767c7e1`.

## Review 1 — `ea18d62f`: interrupted (rate limit)

The reviewer stopped before its report. Its partial probes were kept and acted on (`996f9bc8`):

| Finding (partial) | Ruling |
|---|---|
| Changes with no label, number or listed geometry word passed as notes ("Nhân đôi mọi kích thước.", "Bỏ giả thiết thứ ba.") | Fixed `996f9bc8`: a note is exempt only in a closed note form |
| Hypotheses after a goal clause ("Chứng minh SC ⊥ BD lúc SA = 5.", ", đáy ABCD là hình chữ nhật") or inside a route-B prove quote counted as read | Fixed `996f9bc8`: a goal is read only up to its first given / condition marker or clause boundary |

## Review 2 — `996f9bc8`: BLOCKING

| Finding | Ruling |
|---|---|
| I1 a note prefix let a change through ("Lưu ý: bỏ giả thiết thứ ba.") | Fixed `c56ccc67`: a note is a segment made only of closed note words |
| I2 the goal clause had its own marker list (missing "với", "với điều kiện", "coi như", "đồng thời") | Fixed `c56ccc67`: it ends at the gate's own `_DUNG_GAN` / `_DIEU_KIEN` markers; a length it asserts may not contradict a validated value |
| I3 a route-B "prove" label on a plain premise made it read | Fixed `c56ccc67`: read quotes count only where the gate itself reads a goal or a negation |
| I4 false refusals: "cạnh bên SA", "độ dài SA", "chiều cao SA", units | Fixed `c56ccc67`: object names recognised on the source before quotes are blanked |
| I5 a length hidden in another call's long quote | Fixed `c56ccc67`: a number must sit inside the quote of a call carrying that value |

RED 34 → GREEN.

## Review 3 — verification of `c56ccc67`: BLOCKING

| Finding | Ruling |
|---|---|
| Goal continuations "rồi / sau đó / nhưng" carried a change | Fixed `90ce6497`: the goal ends at `_VIEC_KE_TIEP` and contrast markers too |
| Route-B goal quote read text before the goal opener ("SA = 5 và chứng minh …") | Fixed `90ce6497`: read from the opener on |
| One call value backed two numbers ("SA = 3, đổi AB thành 3") | Fixed `90ce6497`: each value backs one occurrence |
| Role nouns asserted roles ("Đường cao SB.", "Cạnh đáy SA.") | Fixed `90ce6497`: role nouns verified against validated calls |
| False refusals: exam sub-parts, noun sequences, "(đơn vị: cm)" | Fixed `90ce6497` |
| "Lưu ý: độ dài là 5." served | Fixed `90ce6497` |

RED 34 → GREEN.

## Review 4 — final short verification of `90ce6497`: NON-BLOCKING

About 155 probes against `90ce6497`, `c56ccc67` and `7767c7e1`. Every claimed fix held. No new false serve.

| Finding | Ruling |
|---|---|
| Important: "rồi" ended every goal, so chained proofs ("Chứng minh BD ⊥ (SAC) rồi suy ra BD ⊥ SC.") were refused | Fixed `f8ac9f4b`: a goal after a connector continues the goal (`_ket_muc_tieu`); a change after the connector still ends it |
| Important: heights of a right prism ("Chiều cao AA' = 3.") and a regular pyramid ("Đường cao SO.") were refused | Fixed `f8ac9f4b`: roles also come from `prism.right`, the base centre of `regular_pyramid` (`_tam_day`), and the apex projection; an oblique prism's edge is still refused |
| Minor: goal lead-ins "Hãy / Em hãy / Từ đó" | Fixed `f8ac9f4b` |
| Minor: "Ghi kết quả đến 2 chữ số …" refused; "Làm tròn kết quả, độ dài là 5." served | Fixed `f8ac9f4b`: a number in a note only as "N chữ số"; "thập phân" is a note word |
| Minor: "bằng cách …" ends a goal | Declared conservative refusal |
| Minor: "đỉnh A" accepts any vertex | Declared: the solid name already fixes the apex; no figure change |
| Open, pre-existing near-variants (same at `7767c7e1`): "Chứng minh SC ⊥ BD do / vì / bởi vì SB ⊥ (ABCD).", "… còn / song / ngoài ra đáy là hình chữ nhật." served | Fixed `b264828f` (RED 13 → GREEN): do / vì / bởi vì / nhờ / còn / ngoài ra end the goal; "vì sao" still opens a chained goal. "song" is not a marker because of "song song", so "… song đáy là hình chữ nhật." stays a declared limit |
| Earlier conservative refusals: "Cạnh bên SA là đường cao.", "Câu 2 (1 điểm).", "(a) …" / "a. …" layouts | Declared conservative refusals |

RED 25 → GREEN at `f8ac9f4b`, RED 13 → GREEN at `b264828f` (`test_premise_source_coverage.py` 209 passed, 1 xfailed).
Benchmark byte-identical. No further review round: the remaining findings are declared conservative refusals or limits.
