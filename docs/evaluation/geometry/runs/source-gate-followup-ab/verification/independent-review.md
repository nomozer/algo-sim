# Independent Mathematical & Source-Gate Security Review (`P5.3–P5.4`) — `source-gate-followup-ab`

- **Reviewer**: Independent Source Gate Reviewer subagent (`8d8f5e12-aea9-4b4e-88e6-c401296989b4`)
- **Branch**: `research/hybrid-source-gate-followup-ab` (base `main` = `97cfff9c3085ec00a236f87587c2e4144b38836c`)
- **Measured System Tree SHA-256**: `de66bd5ca6ee798dab043a1a1a7e79fc635aff5b2c5259de8878fe8f66bcae50` (`112` files)
- **Final Verdict**: **`INDEPENDENT_REVIEW_PASS`** (`0 BLOCKER`, `0 IMPORTANT`, `0 MINOR`)

---

## 1. Round 1 Audit (`FAIL` -> Fixed)

Round 1 identified `1 BLOCKER`, `4 IMPORTANT`, and `1 MINOR` findings, all resolved before candidate freeze:

1. **`[BLOCKER B-1]` Cross-sentence `"diem"` / `"chieu"` bypass in `_cau_tien_de_dong_hop_le` (`registry.py:3753–3758`) — RESOLVED**:
   - **Finding**: `_cau_tien_de_dong_hop_le` accepted `kind == "chieu"` and checked `construction_source_bound(d, de)` against `d.quotes` across the problem text rather than `m.group()`, allowing a point `M` defined in another sentence (`"Gọi M là trung điểm của SA."`) to validate an unencoded or contradictory `"diem"`/`"chieu"` clause in a compound premise sentence.
   - **Fix**: Restricted branch to `elif kind == "diem":` (`"chieu"` returns `False`) and bound validation directly to `m.group()` via `construction_source_bound(replace(d, quotes=(m.group(),)), de)`. Locked in `test_followup_b_negative_controls_stay_refused` (#6 covering `"và M là điểm di động trên cạnh SC"`, `"và M là trung điểm của SB"`, `"và M là hình chiếu vuông góc của S lên BD"` -> `SOURCE_PREMISE_UNREAD`).
2. **`[IMPORTANT I-1]` Missing `khoi is None` and `m["ds"] is None` guards in `kind == "day"` (`registry.py:3665–3686`) — RESOLVED**:
   - **Fix**: Enforced `khoi is None` rejection at line 3665 and `m["ds"] is not None` rejection on `"hình chữ nhật"` (line 3669) and right-triangle `"vuông"` (line 3686) branches.
3. **`[IMPORTANT I-2]` Single-`"khoi"` guard and `"dagiac"` documentation (`registry.py:3640`) — RESOLVED**:
   - **Fix**: Added `not any(k != "khoi" for k, _m in cau)` at line 3640 and documented `"dagiac"` alongside `"day"`, `"vuong"`, `"doan"`, `"vai"`, `"diem"`, `"dcao"` in `report.md` and `handoff.md`.
4. **`[IMPORTANT I-3]` Full 64-hex SHA-256 surface fingerprints in `report.md`, `handoff.md`, `run.json` — RESOLVED**:
   - **Fix**: Recorded exact 64-char SHA-256 digests (`aa9d93eeac9f…`, `485d3834db8b…`, `4bff35bbf690…`, `5ceb0f999d4d…`, `7ea511a6e382…`) and updated tree hash `de66bd5ca6ee798dab043a1a1a7e79fc635aff5b2c5259de8878fe8f66bcae50`.
5. **`[IMPORTANT I-4]` Alignment of `report.md` with code symbols, test names, and JSON artifacts — RESOLVED**:
   - **Fix**: Synchronized all symbol names, test function names, mathematical answers, and refusal codes in `report.md` and `handoff.md` with `registry.py`, `test_source_gate_hardening.py`, `sgh-post-feedback-regression.json`, and `bh2a-post-feedback-regression.json`.
6. **`[MINOR M-1]` Leading `"với "` prefix scope in `_C_VUONG` (`registry.py:904`) — RESOLVED**:
   - **Fix**: Updated `_C_VUONG` to `rf"(?:(?:có|với)\s+)?(?:(?:cạnh\s+bên|đường\s+thẳng)\s+)?{_L1}{_L1}..."`.

---

## 2. Round 2 Verification (`INDEPENDENT_REVIEW_PASS`)

- Verified `B-1`, `I-1..I-4`, and `M-1` resolved across `registry.py`, `test_source_gate_hardening.py` (`235 passed`), and run artifacts (`0 BLOCKER`, `0 IMPORTANT`).
- Cleaned cosmetic duplicate comment `R2-M1` in `test_source_gate_hardening.py`.
