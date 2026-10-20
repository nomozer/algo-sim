# Handoff — source gate hardening (SG-1..SG-6)

Status: **`SOURCE_GATE_GO_MAIN_AND_CLEANUP_VERIFIED`** — integrated onto `main` under **`GO_MAIN_SOURCE_GATE_HARDENING_CONDITIONAL`** (offline research integration ONLY).

## 1. Identity & Governance

- **Branch integrated:** `research/hybrid-source-gate-hardening` fast-forwarded onto `main` from baseline `6973c4b6e0051afea2d63fe4ae89e318464b54b1`
- **Authorization:** `GO_HYBRID_SOURCE_GATE_HARDENING_LOCAL` → `GO_MAIN_SOURCE_GATE_HARDENING_CONDITIONAL` (`DEFAULT_MODE = LLM_ONLY`, `RESPONSE_CONTRACT = flat`, `HYBRID_PRODUCT_ENABLEMENT = NO-GO`, `ALLOW_LIVE_AI = 0`, `CACHE_VERSION = 127`)
- **Final product commit:** `602316ed909ad75b10c46283624e1d753187e371` (`602316ed`)
- **Final frozen candidate commit:** `c5a83b745d14f7321cb8593d9190a53e459a34bb` (`c5a83b74`, 112 files, tree hash `0512dbc53e09696dfecee4cec8ed360af4ad66d8816c782c2993c3617a0d2583`; `freeze_evaluation_candidate.py --verify` MATCH)
- **Final measurement commit:** `2d0641f43b1e977fbe1eec554603da494313a12b` (`2d0641f4`)
- **Independent review:** `INDEPENDENT_REVIEW_PASS` ([`verification/independent-review.md`](verification/independent-review.md) — 6 initial rounds + delta on `1beeec0b`, plus 11 Full-T3 follow-up rounds T3-1..T3-11 ending in PASS on `c5a83b74`)
- **Authoritative Full T3 receipt** (clean detached worktree `.superpowers/worktrees/tmp-sgh-t3` at `2d0641f4`, `ALLOW_LIVE_AI=0`, `node frontend/scripts/full-gate.mjs`):
  - Verdict: **`FULL_PRODUCT_GATE_PASS`** (`EXIT=0`, total `531.7s`)
  - Backend `pytest`: **11,338 passed**, 1 skipped, 2 deselected, 9 xfailed (`514.8s`), including `test_source_gate_hardening.py` (**226 passed**)
  - Frontend `vitest`: **1,146 passed** across 119 test files (`9.6s`)
  - Frontend `typecheck + build production`: **PASS** (`6.2s`)
  - Thesis demo replay (`tập demo khoá luận`): **5/5 PASS**, reduced chain **1/1 PASS** (`0.8s`)
  - Demo crash surface (`bề mặt sập của demo`): **6/6 PASS**, `0` unhandled 500s (`0.5s`)
  - Temporary worktrees (`.superpowers/worktrees/tmp-sgh-base`, `tmp-sgh-w2a`, `tmp-sgh-t3`, `tmp-sgh-freeze`): all removed after verification.
- **Findings & evidence:** [`report.md`](report.md) · [`results/`](results/) · [`bh2a/`](bh2a/) · [`run.json`](run.json)

## 2. SGH-01..18 Scientific Evidence Receipt (P1)

- **SGH original blind evaluation:** `6/10` positive, `10/16` mathematically correct goals.
- **Strict tuple scoring:** `8/16` do khác biệt ngữ nghĩa trường `dim`.
- **Negative exact refusal:** `5/5`.
- **Ambiguous locked expectation:** `1/2`.
- **SGH-17:** sai lệch thiết kế oracle đã được phân xử riêng, không sửa manifest gốc.
- **Four false refusals:** `SGH-02`, `SGH-04`, `SGH-09`, `SGH-10`.
- **Timing:** original blind test was conducted before feedback-based fixes.
- **Remaining defect classes:** two remaining source-gate defect classes are **NOT FIXED** (see §3 below).
- **Preregistered threshold:** strict preregistered SGH threshold **NOT MET**.
- **Authorization scope:** Conditional GO MAIN (`GO_MAIN_SOURCE_GATE_HARDENING_CONDITIONAL`) is authorized for **offline research integration ONLY**.

## 3. Next Task Handoff — Follow-Up Task (P4)

Hai nhóm lỗi còn lại thuộc một **FOLLOW-UP TASK riêng** (không sửa trong GO MAIN):

- **A.** `_kiem_don_vi_hoi` không nhận diện ranh giới mục tiêu kế tiếp có điểm mô tả chưa đặt tên.
- **B.** `_kiem_nguon_dong` từ chối tiền đề ghép trong lát `line_ref` dù đã có các typed facts có nguồn và có thể kiểm tra độc lập.
