# AI_CONTEXT_BUNDLE.md — AlgoSim Session Handoff & Quick Context
**2026-10-27 — Root consolidation (latest repository handoff):** root is clean on `main`; product baseline `b7b8358e`, cache130, LLM_ONLY and opt-in Hybrid unchanged. The 79-file audit, local receipt recovery paths, retained research refs and quarantined worktrees are in `evaluation/geometry/runs/root-consolidation/ROOT_CONSOLIDATION_REPORT.md`. Next backend campaign starts with certificate-bound D-10 point–line presentation, then independent holdout/NL extraction; no implementation or live provider call in cleanup.
**LOCAL 2026-10-26 — latest continuation (Claude resume after Codex limit):** branch `research/scene3d-hybrid-v2-claude-resume` in `.superpowers/worktrees/s3d-hybrid-v2-claude`, from Codex `e336e0df` (Codex worktree, Claude worktree `s3d-hybrid-v2` and root untouched; backups in root `.superpowers/backups/`). Codex's Full T3 at `e336e0df` died at 27 % (INCOMPLETE, no receipt; 9 failures diagnosed and fixed, 0 product regressions). Claude: Scene3D Checkpoint C (foot dot, panel dedup, 16–22 px right-angle mark) and Hybrid V2 Checkpoint D (route-D exact common perpendicular for skew distances, NO_BUMP). No full 18-family or independent extraction claim. Then sphere closure (`b101dc79`, candidate `3994f603`): outline at edge pixel width, reference equator auxiliary; official suite re-run 7/8 (F2 unchanged); SPHERE_VISUAL_MERGE_GATE_BLOCKED on Owner image approval + F2 decision. LLM_ONLY/cache130/live0/no merge/push. Continue: `evaluation/geometry/runs/sphere-final-closure/report.md`.
**LOCAL 2026-10-24 — Visual–Hybrid final corrections:** same branch; product af670aa6 (backend display identity, diagnostics UI, samples), candidate a636a0e5, CACHE_VERSION 128, Full T3 PASS at a084c180; official suite FAIL with 2 product findings, independent review PENDING, main NOT ready for GO; evaluation/geometry/runs/visual-hybrid-final-corrections/FINAL_OWNER_HANDOFF.md. **Visual–Hybrid integration:** integration/hybrid-visual-candidate = merge 78e88470 of the B1/B2 branch below (97d59bf9) with the Scene3D SGK visual port (7f90d9b3) + label-authority fix (frontend prints backend notation verbatim); product a9d05dda, candidate aec7b183, Full T3 PASS at b99afd32; owner gate in evaluation/geometry/runs/visual-hybrid-integration/FINAL_OWNER_HANDOFF.md. **Hybrid primary B1/B2 (research only):** branch research/hybrid-primary-b1-b2-offline from verified C0 5ee97340 (main 9978e512 unchanged); product c3c1eb80, internal source-text -> replay V2 -> Source Gate/Planner/exact engine -> product /4 wrapper. 47-case development replay: 22 served/25 refused, zero wrong-served/false-refused; one historical refusal-category mismatch retained. Full T3 FULL_PRODUCT_GATE_PASS at f72ccc82 (candidate d8a22dbe + docs; Claude takeover, attempt 4 in clean worktree t3-b1b2). Scene3D owner visual reference: spec only, no product change. Live quality UNKNOWN; full live NL E2E NOT_MEASURED; production LLM_ONLY/flat/Hybrid NO-GO/live0/cache127/memory32, remote BLOCKED and 27 exceptions pending. Scope, review and current machine receipts: evaluation/geometry/runs/hybrid-primary-b1-b2-offline/. Earlier S1-S2 handoffs remain in backend-hybrid-continuation/ and backend-hybrid-contract-unification/.
**2026-10-19 LOCAL Wave 1 (takes precedence over older snapshots):** branch `research/hybrid-architecture-wave1-exact-certificates-planner` from `main` = `origin/main` = `f0560449` (after Session A `hybrid-offline-readiness-finalization` fast-forwarded to `main` `f0560449`), product `fd310cd9` (Wave 1B `681e0473`, Wave 1A `29a7b8c8`, initial `222cd541`), candidate freeze `77b05def` (112 measured files / `534c726a4379700be0035752f4925d1ee5573e6d2db1718c07053f2e14ab7bfa`). Batch B cleanup (`BATCH_B_CLEANUP_VERIFIED`) safely removed `3/3` eligible worktrees (`B2`, `B3`, `B4`) via `git worktree remove` without `--force` (`5.2670 GiB` reclaimed, `6.9562 GiB` cumulative with A1; `D:` free `23.1552 GiB`). Wave 1A (`ISSUE-ARCH-SCENE3D-ALTITUDE-CERTIFICATE-MISSING` resolved on branch) adds `certificates.py` (exact `Fraction` Gram-metric perpendicularity & deductive line-plane certificates + `verify_perpendicular_witness`), emits Path A `segment3.perpendicular_witness` in `quantity_annotations._gan_chung_chi_vuong_goc_doan` + `scene3d._TRUONG["segment3"]`, and guards `o.type === "point3"` in `scene3d-annotations.ts` (`10/10` backend + `34/34` frontend tests, `41/41` Adapter `/2` fixtures). Wave 1B (`GAP-C1` / `ISSUE-RESEARCH-HYBRID-AUXILIARY-BEFORE-SOLID`) adds `planner.py::_sap_xep_phu_thuoc_loi_goi` enforcing explicit directed dependency edges and tiered topological ordering with fail-closed dangling/cycle rejection (`10/10` tests, `417/417` targeted backend regression). Independent review `INDEPENDENT_REVIEW_PASS`; clean detached T3 at `77b05def` **`FULL_PRODUCT_GATE_PASS`** (backend `10970/0`, frontend `1146/0`, build `PASS`, demo `5/5`, crash `6/6`; `authoritative-t3.json`). Verdict then: **`BATCH_B_AND_ARCH_WAVE1_READY_FOR_REVIEW`** (`evaluation/geometry/runs/hybrid-architecture-wave1-exact-certificates-planner/handoff.md`). **Corrected by run `segment-witness-cache-invalidation`:** its "Cache 126, no bump" was wrong — v126 rows from `main` lack the new segment witness and still hit — so product `2635cbd6` bumps **`CACHE_VERSION = 127`** and fixes the Path A witness labels (`formation_construct_height`, `ENGINE_VERIFIED`), and `008918cb` revives the dead prism branch (`shape_class`; right prism / cuboid / cube lateral edges now get witnesses); measured `8cb9857f…` (112 files); candidate `1117cfd4`, clean detached T3 **`FULL_PRODUCT_GATE_PASS`** (backend `10986/0`, frontend `1146/0`), independent review round 2 PASS; verdict **`WAVE1_CACHE127_READY_FOR_GO_MAIN`** (`evaluation/geometry/runs/segment-witness-cache-invalidation/handoff.md`). Cache127 / LLM_ONLY / flat / Adapter `/2` / Hybrid NO-GO / live0.

## LOCAL override — 2026-10-15 (ưu tiên hơn snapshot §2)
**2026-10-17, independent-nlu-extraction-evaluation (LOCAL branch from `76dca142`, no product change):** blind-authored 60-case corpus + oracle, gold facts, harness, two audits; gold arm 8/44 locked served; live 76 calls (est. USD 0.299); locked: preregistered UNSAFE (scorer artifact L01) → corrected P1 PASS, P2 NO (27/45), 2/44 served; extraction is the dominant loss. **Integrated on `main` `b22c2269` (owner GO, pushed; branch deleted).** Next: research priority decision (`runs/independent-nlu-extraction-evaluation/approval-request.md`). **2026-10-17, hybrid-semantic-grounding-reliability:** resumed Claude's preserved uncommitted M1–M4; product `94b3437b`, clean candidate `57c7f5db…` MATCH. Offline 99 cases: wrong serves13→0, false refusals21→16; historical174 answers/planner unchanged, two refusal-code changes. Independent review delta clear; clean detached T3 `bd2dc080` PASS (backend 10240/0, vitest 1072), candidate MATCH. **Integrated on `main` `bd20ac46` (user GO, pushed; branch deleted).** Next: research priority decision. cache125/LLM_ONLY/Hybrid NO-GO/live0. Single handoff: `evaluation/geometry/runs/hybrid-semantic-grounding-reliability/report.md`.
**2026-10-17, scene3d-annotation-correctness (`e218b5ef` from `8427c879`, refreeze `b2352aae`) & scene3d-educational-finalization (`22df95d6` → `8427c879`):** P1–P2 mathematical audit (`dot(u_world, v_world)=0`, `d_3D(C', (A'BD))=4/√3≈2.309>0` vs 2D perspective foreshortening) + boundary-edge tangent alignment in `huongChanVuongGoc`, 3-point textbook L-bracket & dash origin at foot in `vatNhanChung`, and `±10px` witness-segment obstacles in `chieuNhan`; independent review PASS, 68 Vitest files (1079 tests), 30 full-size (`1280×900`) states, **`HUMAN_VISUAL_REVIEW_PASS`**, clean detached T3 `29127ba2` PASS, **integrated on `main` and pushed (`runs/scene3d-annotation-correctness/integration.md`).** Earlier 2026-10-17: `scene3d-educational-finalization` (`22df95d6`, EDU-1..8, T3 `8aabb4b9` PASS, `HUMAN_VISUAL_REVIEW_PASS`) and `scene3d-visual-correctness` (`ee9689e6`). cache125/LLM_ONLY/Hybrid NO-GO/live0.
**2026-10-16, generalized-goal-entry (branch `research/generalized-goal-entry` from `96569792`, Codex session committed and verified by Claude):** product `193e634a` + Scene3D witness fix `289007a4`; length goals enter Registry effect search (midpoint 8/8 exact, experimental centroid 2/2 without code change, 0 wrong served, 153 earlier rows identical). Schema/provider/cache125/LLM_ONLY unchanged; Hybrid NO-GO; Gemini 0. Candidate `eaddb56c…`, clean T3 `5964f875` PASS. **Integrated on `main` `bd4d3f59` with its stack (user GO, pushed).** Next: research priority decision.
**2026-10-16, goal-directed function discovery (`goal-directed-function-discovery`, branch `research/goal-directed-function-discovery` stacked on result binding `f83b4ed1` + Scene3D W1–W3 `8c24cb52`, both not integrated):** product `cfa27baa` (route D only; review fixes after `9fec9f43`), candidate `093359c2…` (110 files) frozen at `313cc537`, refreeze `81315986`; independent review PASS_WITH_FINDINGS, 0 wrong served. Planner composes distances from an unnamed described point ("trung điểm của SC") to a plane / named line / intersection line from Registry contracts; 9/9 dev positives exact, 15/16 negatives registered code (D-1), 0 wrong served, regression corpora identical to the previous planner; an experimental contract added as data served 3 new forms without planner change. No schema/prompt change, cache 125, LLM_ONLY, 0 Gemini. Clean detached T3 `e6c5b0f1` `FULL_PRODUCT_GATE_PASS` (pytest 10115/0, vitest 1061). Next: research priority decision.
**2026-10-16, result binding FINAL T3 PASS (`result-binding-final-acceptance`):** product `55c657b8` (shared ask-grammar closure, independently code-reviewed; E-1 evidence review PASS at `7a583590`), refreeze checkpoint `7f355a81`, candidate `30808cb0…` (110 files). T3 `FULL_PRODUCT_GATE_PASS` on a clean detached worktree (pytest 10046/0, vitest 1055/1055). Corpus 18/18, Benchmark 30 and grammar probe byte-identical; provider fingerprints unchanged. Integration readiness READY_FOR_REVIEW; `main` is still `2a3c0787`; no merge, nothing pushed. Earlier: `shared-ask-grammar-safety` (5f1b576c → 55c657b8, E-1 addenda 1–3).
**2026-10-15, earlier steps of this chain:** integration readiness (`source-bound-result-planning-integration-readiness`, provider A/B/declarations intentionally changed, corrections C1–C3) → main integration BLOCKED on 2 pre-existing false serves (`source-bound-result-planning-main-integration`) → false-serve fix `8da9ae31` BLOCKED on shared-grammar gaps (`source-bound-result-planning-false-serve-fix`). Details in those runs.
**2026-10-15, `source-bound-result-planning` on `research/source-bound-result-planning` (from `19140e2f`, `main`/`origin/main` `2a3c0787` unchanged, no merge/push):** Product `efb756aa`, candidate `c0a8792f1c491ae4…` (110 files), `CACHE_VERSION = 125`, `DEFAULT_MODE = LLM_ONLY`, Hybrid OFF, `LIVE_GEMINI_REQUESTS = 0`. Implements preregistered `line_ref` transport, `PlanningContract` effects (`intersection_line`, `orthogonal_projection_line`, `ask_length`), bounded `_EffectResolver` (depth 3, needs 32, candidates 8, lines 4, feet 8, available-binding reuse, equivalent-producer alias coalescing, goal memoization), `_kiem_result_binding` enclosing-sentence source certificate validation (3 distinct plane labels before `frozenset`, Route A `RESULT_BINDING_UNVERIFIED`), and Engine/IR line result binding (`_Dung.lines`, `_emit_intersection`). Locked corpus (`NOT_HELD_OUT`): RED `de5ea1a7` 18/18 `SCHEMA_INVALID` → GREEN 6/6 positive `SERVED` ($10/11, 5, 3, 10, 0, 10/11$), 12/12 negative `REFUSED` (`test_result_binding_planning.py` 72 passed; 18/18 `EXACT_MATCH` in `reconciliation.json`). Independent 11-dimension review (`review.md`) PASS (`efb756aa`). Historical two-line (45/32) and benchmark 30 (19/9/0/2) invariant; Playwright SwiftShader + Intel D3D11 `PASS_CORE_CAUSAL_RENDERING` (4 scenes, 0 errors); clean detached T3 `FULL_PRODUCT_GATE_PASS` at `7b14fe04` (`verification/t3-pass.json`, `verification/t3-authoritative.log` `29b09bf5…`: backend 9405 / frontend 1055). Run `docs/evaluation/geometry/runs/source-bound-result-planning/`.
**2026-10-14, Group A integrated on `main` (`5d73f7c2`, audit `2a3c0787`):** Product `a5a0797c`, freeze `f227dd72`, candidate `26698338…`, inherited T3 `f227dd72` PASS (backend 9329 / frontend 1055). Earlier waves (`hybrid-main-integration`, `question-local-givens`, `goal-directed-section-planning`, `source-grounding-integration`, `two-line-plane-section`, `scene3d-construction-audit`, `pedagogical-construction-sequencing`, `goal-directed-planner-generalization-audit`) in `docs/evaluation/geometry/runs/`. Protected `frontend/public/favicon.svg`, DB, DSL archive (`NO-GO_ARCHIVED`), bundles, real-model refs (`471a2c79`) preserved.

> Handoff cô đọng cho session mới. Code/test thắng khi mâu thuẫn với docs.
> Không chứa secret hoặc raw model output; giới hạn 300 dòng. Lịch sử từng wave:
> `docs/STATUS_LEDGER.md`; bằng chứng và chuỗi đính chính: `docs/EVIDENCE_INDEX.md`.

## 1. Product và ranh giới

AlgoSim chuyển đề hình học không gian tiếng Việt thành Semantic Program và
Scene3D tương tác. LLM chỉ trích xuất/tổng hợp cấu trúc; engine tất định sở hữu
tọa độ, thực thi, đo lường, correctness và scene state.

- `DEFAULT_MODE = LLM_ONLY`; compiler-first vẫn opt-in (20 cổng ở `docs/MIGRATION_CHECKLIST.md`).
- `CACHE_VERSION = 125` trên source LOCAL đã kiểm (118 là snapshot run docs-cleanup: envelope từ chối T8 thiếu kích thước đổi nguyên nhân `UNKNOWN` → `SOURCE`;
  117 ở exact-dimensions — bộ đọc độ dài không lấy vế đầu của biểu thức); provider-facing fingerprint `b1714b566e25c912…`
  không đổi. Run mobile-canvas-fit không bump (chỉ frontend).
- Mọi wave từ w09 chạy offline: `LIVE_GEMINI_REQUESTS = 0`.
- Không hardcode case/label/answer vào product; mâu thuẫn phải fail-closed.

## 2. Repository state hiện tại

Cập nhật 2026-10-19 — mới hơn khối "LOCAL override" ở đầu file; tường thuật cũ ở đó và §5–§6 có thể lỗi thời (việc mở: `OPEN_ISSUES.md`; việc kế tiếp: `ROADMAP.md` §0).
```text
MAIN = origin/main (2026-10-27) a3ee14a7 (includes hybrid-v2-planner-generalization + registry /17 I-1 consistency); NEXT branch research/hybrid-v2-adapter4-plane-section-certificate (product f54c3561 closing ADAPTER_INTEGRATION_GAP via Category B plane-section-certificate/1, candidate 0be084d9, NOT merged): runs/hybrid-v2-adapter4-plane-section-certificate/handoff.md
SGH_STATE = product 602316ed · candidate c5a83b74 (112 file 0512dbc5…) · review PASS · T3 2d0641f4 PASS · corpus 18/18, BH2A 11/12 · SGH blind 6/10 pos (10/16 math, 8/16 tuple, 5/5 neg, threshold NOT MET); FOLLOWUP_AB (`research/hybrid-source-gate-followup-ab`, product `68acc140`, candidate `b5e80380` / `de66bd5c…`, review PASS, T3 `b0b2a3c3` PASS): fixes Defect Classes A (`_kiem_don_vi_hoi`/`_kiem_du_kien_cau_hoi` unnamed-point multi-goal boundary) & B (`_kiem_nguon_dong`/`_cau_tien_de_dong_hop_le` compound premises on `line_ref` slice) -> SGH post-feedback regression 10/10 pos (16/16 math), 5/5 neg, 0 false serves; BH2A 11/12 + `BH2A-03-variant-ABCD` served `a√10` (`runs/source-gate-followup-ab/handoff.md`)
PRODUCT_STATE = CACHE_VERSION 130 · DEFAULT_MODE LLM_ONLY · flat · Hybrid opt-in only, product NO-GO · route D registry/17 · planner/16 · engine/14 · adapter/4 · Full T3 PASS 0be084d9 (12421/1417)
SCENE3D = M2 #7, F1, F2 xong; P0–P3 owner duyệt hình trên bộ cảnh mẫu (chỉ phạm vi đó); "chọn kết quả" trên canvas chưa kiểm; KHÔNG Product E2E PASS
HYBRID = product enablement NO-GO · không frontend caller /api/preview/hybrid · không tích hợp provider live · không GO LIVE
OPEN = F3–F6 + thiếu fixture insufficient_specification+SOURCE · SOURCE-LENGTH-READER-VECTOR-ZERO · CACHE-HISTORICAL-MODE-UNKNOWN · SCENE3D-ALTITUDE-CERTIFICATE-MISSING · offline Product E2E chưa đạt (OPEN_ISSUES.md)
EXTRACTION_V2 = prompt v2 NO-GO, không ở main; phần an toàn trên main = e4fff851 + aa0da02b + 0507cb01 (runs/extraction-v2-integration-record, CORRECTED_BY); không có T3 riêng tại các commit đó
LOCAL_ONLY = nhánh research/hybrid-semantic-extraction-v2, research/compact-geometry-dsl, integration/extraction-v2-safety, commit 471a2c79, tag evidence/extraction-v2-pilot — chưa push
PRESERVATION = bundle + bản sao non-Git ngoài repo D:/algo-sim-preservation-20261018 (GO_PRESERVE_PARTIAL: 20 thư mục khoá ACL và secret chưa chép; cùng một SSD) — chưa cleanup
NEXT_ACTION = owner chọn ưu tiên giữa các wave cần duyệt riêng (vector-zero, chứng nhận chiều cao, F3–F6 offline); ROADMAP §0
WAVE2C_3A = Wave 2C on main `1613e0d3` (BH2C blind 11/11 pos, 13/13 neg, 0 wrong serves); TypedFactNext + Adapter /3 on main `f2bc01e3` (`typed-fact-next/1` + `hybrid-simulation-adapter/3`, product `61d6f44b`, candidate `09f97a28` / `42f6ae2c…`, T3 `80f47de9`/`7eadd56b` PASS, dev 10/10 pos, 6/6 neg, 4/4 demos); local Wave 3A `research/hybrid-wave3a-volume-reasoning` (product `4c282ecd`, candidate `0a4b6d70` / `df262376…`, review round 2 PASS, T3 `373116d2` PASS, dev 18/18 pos, 14/14 neg); combined reconciliation `research/integration-wave3a-adapter3` from `f2bc01e3` (product `fb63df66`, candidate `e345e717` / `81778092…` across 114 files, review PASS, T3 `cb09d8f9` PASS 11,427/1,150, `runs/wave3a-adapter3-integration/report.md`)
```

Thay đổi chưa commit của người dùng: không restore, sửa, stage hoặc commit khi chưa được cho phép rõ ràng (xoá favicon đã
được cho phép và commit ở f89a1a8b). Không amend/rebase/squash chuỗi commit đã được evidence tham chiếu.

## 3. Tài liệu nằm ở đâu

- Gốc `docs/`: tài liệu chuẩn tắc/dự án và 11 contract/report ngoại lệ có ràng buộc đường dẫn cụ thể. Catalog
  `docs/evaluation/HISTORICAL_REPORTS.md` trỏ 167 báo cáo: 33 report nằm cạnh package artifact, 123 report ở
  `docs/evaluation/reports/`, 11 ngoại lệ ở gốc. `audit_docs_layout` kiểm cả root đóng và đích catalog.
- `docs/research/`: `CLAIM_EVIDENCE_MAP.md` (thẩm quyền duy nhất tuyên bố ↔ bằng chứng ↔ giới hạn),
  `thesis/` (bản thảo, chương, tài liệu tham khảo, hình), `paper/`, phương pháp và tài liệu tham khảo.
- `docs/evaluation/`: run (`geometry/runs/wNN-slug/`), `README.md`, catalog báo cáo cũ.
- `docs/architecture/`: contract đang hiệu lực + snapshot kiểm kê (`README.md` phân biệt).
- `docs/legacy/`: hết hiệu lực — kế hoạch/spec skill, tài liệu giai đoạn chuyển đề, quyết định đã thực
  thi, `CURRENT_STATE_HISTORY.md` (nhật ký cũ của CURRENT_STATE), ba bảng tuyên bố cũ. Loại khỏi grep
  khi tìm luật/trạng thái hiện hành.
- Đường report cũ → mới: inventory hợp nhất `docs/evaluation/geometry/runs/docs-cleanup/inventory.md`; bản đồ máy W19
  lịch sử vẫn ở `docs/evaluation/geometry/runs/w19-docs-organization/inventory/MIGRATION_MAP.json`.
- Hub: `docs/README.md` (năm câu hỏi: hệ làm gì · kiến trúc và cách chạy · việc mở · khoá luận/bài
  báo · bằng chứng).

## 4. Hệ hiện tại (sau regular-square-pyramid-w01) — mỗi dòng một chỗ đọc thêm

- Occlusion và danh tính cảnh: edge ID máy theo entity ID (`A_prime`), nhãn hiển thị riêng, một visual
  owner mỗi cạnh, span `VISIBLE`/`HIDDEN`/`MIXED`, oracle cài độc lập —
  `docs/architecture/OCCLUSION_AND_SCENE_IDENTITY_AMENDMENT.md`.
- Dựng hình theo lớp (w14): `semantic_program/formation.py` chạy cho cả chương trình compiler và LLM.
- Grounding nguồn (w12–w14): độ dài `GIVEN` cần chữ số của đề ngay sau nhãn đoạn.
- Chứng chỉ giả định (w15–w17): C0/C1 trong vùng đa diện; hệ số mặt phẳng gắn đúng mặt phẳng; mệnh đề
  mục tiêu không làm tiền đề; phép cắt gắn câu cắt —
  `docs/architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md` §2–§15.
- Ràng buộc phép dựng (w18, §16): trung điểm/hình chiếu đối chiếu theo danh tính, chặng route
  `construction_binding` (`CONSTRUCTION_NOT_TEXT_BOUND` / `CONSTRUCTION_BINDING_UNVERIFIED`).
- Đích quan hệ đặt bằng toạ độ (w20, §17): trực tiếp hay qua bí danh ⇒ `DEFINED_BY_COORDINATES` ⇒
  `CONSTRUCTION_REPLACED_BY_COORDINATES`, từ chối mọi vùng. Test không ghi bằng chứng đông cứng
  (`run_reconciliation(out_dir)`). Thẻ từ chối (run `cuboid-final-review`): lời ghép từ `reason_subjects`
  ("Hệ chưa kiểm chứng được ‹quan hệ›, vì điểm này ‹cách đặt›…"), không hứa gửi lại; nhãn "chưa kiểm chứng được
  phép dựng" (frontend đọc `reason_code`, không hiển thị).
- Trình bày (w17–w18): backend gắn nghĩa nhãn, frontend chỉ đặt chỗ; hình mặc định gọn, "Hiện tất cả",
  ô soi là nơi giải thích duy nhất, nhân chứng khoảng cách tới chân chính xác.
- Chóp tứ giác đều (regular-square-pyramid-w01): bộ đọc "đều"/cạnh đáy/cạnh bên/trung đoạn/tâm đáy, khuôn C1 T7,
  tâm O gắn theo danh tính (giao hai đường chéo), chiều cao đo được của thể tích; chiều cao vô tỉ, góc, chóp tam
  giác đều chưa phục vụ; cạnh bên đọc cả từ `SA = 3` (tự rà soát cuối, `ad7172ab`), chuỗi `SA = SB = … = 3` chưa
  (`ISSUE-ARCH-SOURCE-LENGTH-CHAINED-EQUALITY`). Giao diện ROADMAP §0.1: card Kết quả ẩn khi thu gọn, ngăn «Đại lượng», panel «Các bước
  dựng», gỡ dải «Đang dựng»; cổng phạm vi nhận "độ dài".
- Khép sư phạm (regular-square-pyramid-w02): nhãn đoạn chỉ khi đoạn mang nó đã dựng; bảng nổi «Các bước dựng» (kéo,
  phím, kẹp; mobile thu gọn); đoạn SO qua bước bổ sung (`formation._tam_day_deu`); chiều cao của công thức theo quan hệ
  ⊥ (`quantity_annotations.chieu_cao_the_tich`); hình phụ (`scene3d-auxiliary.ts`) và lưới tuỳ chọn; độ dài ≤ 0 do
  đề ghi ⇒ `NON_POSITIVE_LENGTH`/SOURCE trên tuyến mặc định (PARTIAL).
- Nghiệm thu local (regular-square-pyramid-w03): mặt phẳng phụ chỉ để đo không mở bước dựng (`measurementOnlyPlanes`;
  miễn trừ W2 ở ba cổng đã gỡ); đoạn đề hỏi độ dài được dựng trước đáp số (`formation._doan_duoc_hoi`; giới hạn
  `ISSUE-ARCH-ASKED-SEGMENT-OVER-EXISTING-EDGE`). Đo `a5d233ce`: suite 7/7, 14/14 lượt dương xanh, đầu dò W2 14/14,
  occlusion 0 lỗi, phát lại không miễn trừ.
- Giao diện chung (regular-square-pyramid-w04): mọi bảng thông tin là `BangNoi` (`scene3d-floating-panel.tsx`; không
  cột, không đổi canvas/camera/bước; nhiều bảng cùng mở; khổ hẹp là tấm trong dòng chảy); canvas theo chiều cao khả
  dụng (`caoKhungKhaDung`), «Bước n/N» trong thanh; cây «Thành phần» theo bước (`treeAt`, nhóm `<details>` thu gọn);
  lời kể theo ký hiệu đề (`ten_trong_loi_ke`); đoạn con trên cạnh khối nhường nét (`doan_tren_canh`, `edge_span`).
  Đo `103494c4`: suite 7/7, đầu dò W2 14/14, đầu dò W4 21/21 (7 họ × 3 khổ), occlusion 0 lỗi, phát lại pass.
- Chế độ tập trung (regular-square-pyramid-w05): cảnh 3D không dựng `nav-bar` (`App`, gốc `la-tap-trung`, một hàng lưới),
  nút quay lại về trang trước (`returnView`/`roiXuong`), công cụ nhóm qua `MenuCongCu` (`scene3d-tool-menu.tsx`), toàn
  màn hình tuỳ chọn; thẻ lời giải `scene3d-solution.tsx` đã gỡ (đại lượng ở «Đại lượng», công thức ở ô soi, chú giải trong
  «Hiển thị»); bộ đọc độ dài nguồn đọc chuỗi bằng nhau (`segment_relation.cac_doan_truoc`). Đo `f01df0e5`: suite 7/7,
  W2 14/14, W4 21/21, W05 21/21, occlusion 0 lỗi, phát lại 14/14.
- Điện thoại (mobile-canvas-fit, D5): khổ hẹp ≤ 48rem canvas cao vừa hình (`scene3d-playback.caoKhungVuaHinh`, tỉ lệ
  `scene3d-view.tiLeKhungHinh` cùng điểm/phép xoay/hướng với phép vừa khung; ≤ phần khả dụng, ≥ 320 px; hình ràng theo
  chiều cao giữ nguyên); bảng bước giữ bước đang xem trong thân bảng. 390×844: canvas 519 → 320–485 px, bảng mở thấy
  cùng hình. Đầu dò `frontend/scripts/check-mobile-layout.mjs`.
- Điện thoại ngang (phone-landscape-layout): ngang thấp (`(orientation: landscape) and (max-height: 30rem)`) ⇒ thanh điều khiển
  thành cột 10rem cạnh canvas (canvas giữ chiều cao, hình giữ cỡ; hai nút xem ở đầu cột; ≤ 48rem dùng bố cục rộng, bảng nổi);
  360 px: ba nút phát một hàng. 844×390 · 667×375 · 844×340 · 360×640 điều khiển trong khung; xoay máy giữ bước/lựa chọn/camera.
- Bảy họ đo trong trình duyệt: `triangular_pyramid`, `rectangular_pyramid`, `triangular_prism`,
  `cuboid`, `cube`, `cross_section`, `regular_square_pyramid`.
- Đo mới nhất (regular-square-pyramid-w01, `ed37f9fa`): bảy họ 14/14 dương, 54/54 âm, 6/6 phục vụ, chọn đại lượng
  68/68, ngăn đại lượng + panel bước 14/14; occlusion 0 lỗi (bốn cảnh W14 `HUMAN_REVIEW_PENDING`); playback 14/14;
  T3 ở commit tài liệu (log trong run).
- Tự động trước đó (run `cuboid-final-review`, `a1c53cdb`): T3 `FULL_PRODUCT_GATE_PASS` (pytest 7079/0,
  vitest 1061/1061, build, demo 5/5, bề mặt sập 6/6); thẻ từ chối trong trình duyệt 12/12 (desktop +
  mobile). Sáu họ không đo lại: bằng chứng hình gần nhất của chúng là w18 (12/12 dương + 46/46 âm;
  occlusion `HUMAN_REVIEW_PENDING`); census SHIP (AC2 18/18) của w20.
- Tài liệu (run `cuboid-final-review`): phần thời Tin học của CODE_INDEX, STATUS_LEDGER, COVERAGE, CORRECTNESS,
  ARCHITECTURE_MAP, DESIGN_BRIEF, POST_THESIS_BACKLOG nằm nguyên văn ở `docs/legacy/*_INFORMATICS_ERA.md` và
  `legacy/CODE_INDEX_REMOVED_ENTRIES.md`; wave đánh số theo từng việc (`docs/evaluation/RUN_NAMING.md`).
- Bất biến (run `cuboid-acceptance`): 24 hàng §5 của ARCHITECTURE_MAP có con trỏ chết đã đối chiếu tới assertion —
  9 đang khoá, 1 chưa đủ bằng chứng (#14), 14 **LỊCH SỬ**, 0 vi phạm; cột con trỏ chỉ còn file sống
  (`results/INVARIANT_RECONCILIATION.json` của run). Run `repo-cleanup` gỡ `editViaServer`, `AIHelpPanel` + `/api/explain`,
  `AttemptObserver` và mọi mã chết Tin học khác; còn lại có lý do: `specDrift`, chính sách `threeD`, `SamplePreview`, prompt
  và từ vựng IR (`ISSUE-ARCH-SHELL-INFORMATICS-RESIDUE`, `ISSUE-ARCH-INFORMATICS-MODEL-SURFACE-AND-IR-VOCABULARY`).
- Tuyên bố được phép: `docs/research/CLAIM_EVIDENCE_MAP.md` — 0 hàng `HUMAN_REVIEWED`; năm ranh giới ở §0.

## 5. Còn mở — không được che

- **frontend-freeze (2026-10-09):** người dùng hoãn phát triển frontend (chưa hài lòng chất lượng UI) để ưu tiên kiến trúc
  hình học + backend. C1–C6 đã xem, chưa phê duyệt; P1–P6 PENDING; UX debt OPEN/DEFERRED; W05 23/24; W14 registry chưa có.
  Chờ quyết định merge tường minh; handoff Cloud `runs/frontend-freeze/handoff.md`.
- **merge-readiness (chờ người dùng):** danh sách nghiệm thu tối thiểu `runs/merge-readiness/report.md` §4. 671 hồ sơ cũ
  `%TEMP%\w12-*` đã xoá sau xác nhận (C: trống 43,87 → 77,43 GB); `scoped_dir*` không đụng. Favicon + `.gitignore` đã commit.
- **browser-temp-lifecycle (hạ tầng kiểm thử):** `ISSUE-OPS-BROWSER-SESSION-PROFILE-LEAK` RESOLVED — hồ sơ Chrome của bộ đo ở
  `D:/tmp/algosim-browser`, xoá khi phiên đóng/hỏng, orphan dọn theo `owner.json`. Còn: 20 script trình duyệt độc lập.
- **classroom-band-fit chờ người dùng:** `runs/classroom-band-fit/review.md` H-1…H-3 (ảnh, quyết chip chỉ hiện chấm màu ở
  640–667 px ngang) và C-1…C-4 (thao tác tay chế độ lớp). `ISSUE-ARCH-CLASSROOM-BAND-CROWDS-PHONE-TOP-ROW` RESOLVED (chờ duyệt;
  24/24, trước 9/24); giới hạn còn lại ghi trong issue.
- **final-acceptance chờ người dùng:** thao tác tay G-1…G-9 (= E-R6 + F-R7; chạm giả lập 8/8 chỉ là hỗ trợ) và D-2…D-4 của
  `runs/final-acceptance/review.md` (D-1 đã xử lý ở classroom-band-fit). UX debt người dùng chấp nhận tạm, vẫn OPEN: bảng nổi
  che canvas khi ngang, nhãn rời canvas ở màn thấp, `ISSUE-ARCH-MOBILE-HEADER-TOOLBAR-LAYOUT`.
- **phone-landscape-layout chờ người dùng:** duyệt `review.md` F-R1–F-R7 (F-R7 + E-R6 cần thao tác tay). Quyết: bảng nổi phủ
  canvas hẹp khi ngang (`ISSUE-ARCH-LANDSCAPE-FLOATING-PANEL-COVERS-CANVAS`), ca xoay màn thấp (`ISSUE-ARCH-ORBIT-LABELS-LEAVE-CANVAS-LOW-SCREEN`,
  khôi phục bằng «Xem lại toàn hình» 56/56). `ISSUE-ARCH-PHONE-LANDSCAPE-CONTROLS-BELOW-FOLD` RESOLVED (chờ duyệt).
- **mobile-canvas-fit chờ người dùng:** duyệt `review.md` E-R1–E-R6 của run (D5 RESOLVED, chờ duyệt). Mở mới (có từ trước, chờ
  quyết): `ISSUE-ARCH-PHONE-LANDSCAPE-CONTROLS-BELOW-FOLD`, `ISSUE-ARCH-ORBIT-LABELS-LEAVE-CANVAS-LOW-SCREEN`. Sửa ở bộ đo: băm
  oracle_source lệch (node 96/97 tại 38a19c65) và kỳ vọng cũ của suite cho ca T8 thiếu chiều cao.
- **Đã tích hợp:** người dùng ACCEPTED A–F của `REVIEW.md` (run `cuboid-merge`, `APPROVAL.md`); `main` fast-forward
  tới `c282a5f3` và push. Giới hạn F1–F5 được **hoãn, vẫn mở** (`ISSUE-ARCH-CONSTRUCTION-BINDING-VOCABULARY`, vùng đa
  diện của #37, `ISSUE-ARCH-CONSTRUCTION-RELATION-BEYOND-SECTION-CUT`, `ROADMAP.md` §0.4,
  `ISSUE-OPS-LIVE-OPT-IN-NOT-UNIFORM`); registry khuất/hiện mới vẫn chưa có (`ISSUE-EVAL-HUMAN-VISIBILITY-REGISTRY-PREDATES-S4`).
- **Đã quyết (người dùng, brief `cuboid-acceptance`):** H-CFR-2 giữ chữ thường và "toạ độ"; H-CFR-1 = backlog giao
  diện, không sửa sản phẩm lúc này; H-CFR-3 `THESIS_DRAFT` §1.8 là bản chính đề xuất, chưa xoá `RELATED_WORK_DRAFT`
  khi chưa đối chiếu nội dung riêng; 204 mục `D:/tmp` + 108 mục `.superpowers` giữ nguyên, không chặn merge.
- **Câu hỏi còn mở từ w20:** H-W20-4 (tàn dư Tin học trong mã) — xử lý ở run `repo-cleanup`; phần còn lại có lý do ở hai
  issue `ISSUE-ARCH-*-INFORMATICS-*`. H-W20-1/H-W20-2 đã sửa, chờ xem ảnh.
- **docs-cleanup (2026-10-08):** tên test theo hành vi (123 hàm, 118 tiêu đề), `docs/legacy/` 42 → 15 file (Superpowers M9–M17,
  W13 và tài liệu chuyển đề gỡ; thiết kế route → `legacy/architecture/`; contract cuboid về `architecture/`), 12 lớp CSS chết;
  còn `SamplePreview`/`threeD`/`specDrift` và sáu prompt + IR Tin học — kiểm kê: `runs/docs-cleanup/inventory.md`.
- **repo-cleanup (2026-10-08):** gỡ 132 file Tin học hết vai trò, 325 selector CSS chết, đổi tên 29 file theo chức năng;
  `ISSUE-OPS-T1-DOMAIN-SCRIPTS-STALE` khép; inventory + lý do giữ: `runs/repo-cleanup/report.md`.
- **exact-dimensions chờ người dùng:** duyệt `review.md` R1–R10 của run. Khép: `ISSUE-ARCH-REGULAR-TRIANGULAR-RATIONAL-EDGES`
  (khung affine + metric Gram; kích thước chữ, tổng căn vẫn từ chối). Mở mới: `ISSUE-ARCH-MISSING-SIZE-REASON-ON-AFFINE-CHART`.
  `ISSUE-ARCH-REGULAR-TRIANGULAR-MODEL-LAYOUT-UNMEASURED` vẫn mở (mọi khung nay phục vụ; mô hình chưa đo). D5 đã triển khai ở run mobile-canvas-fit (chờ duyệt).
- **regular-triangular-pyramid-w01 chờ người dùng:** duyệt hình `REVIEW.md` R1–R12 của run; D5
  (`ISSUE-ARCH-MOBILE-CANVAS-WHITESPACE-AND-PANEL-SCROLL`) đã triển khai ở run mobile-canvas-fit. Mở mới: `ISSUE-ARCH-REGULAR-TRIANGULAR-RATIONAL-EDGES` (miền ℚ³),
  `ISSUE-ARCH-REGULAR-TRIANGULAR-MODEL-LAYOUT-UNMEASURED`, `ISSUE-ARCH-TETRAHEDRON-OUTSIDE-POLYHEDRAL-REGION`. Khung nhìn ban đầu
  đã sửa cho mọi họ (hình nay ở giữa) — ảnh trung tính khác W5 (dịch ngang).
- **W5 (IMMERSIVE_SIMULATION_AND_ARCHITECTURE_SLICE) chờ người dùng:** duyệt hình theo `REVIEW.md` của run
  regular-square-pyramid-w05 cùng gói W4. R4 của W4 (trần chiều cao canvas mobile) đã được brief W5 trả lời: không trần.
- **W4 (SHARED_SIMULATION_UI_CLOSURE):** gói duyệt R1–R10 của run regular-square-pyramid-w04. Người dùng không chấp nhận hoãn H-W2-3 ⇒ W4 đưa mọi bảng thông tin lên một
  cơ chế bảng nổi (`ISSUE-ARCH-INSPECTOR-COLUMN-RESIZES-CANVAS` RESOLVED); SM trên SA nhường nét
  (`ISSUE-ARCH-ASKED-SEGMENT-OVER-EXISTING-EDGE` RESOLVED); tên nhóm «Giao điểm của AC và BD» giữ theo yêu cầu.
- **W3 (đã đóng):** H-W2-2, H-W2-4 đã sửa (lỗi); hai worktree đo của W3 đã gỡ.
- **W1 chờ người dùng:** H-W1-1 (duyệt hình — chặn merge), H-W1-2 (chiều cao hiện `d(S, (ABC))`, không vẽ SO),
  H-W1-3 (mặt phẳng phụ để đo), H-W1-4 (bước dựng phụ AC, BD, O), H-W1-5
  (`ISSUE-ARCH-DEFAULT-ROUTE-NON-POSITIVE-LENGTH-CAUSE`) — `HANDOFF.md` §1 của run regular-square-pyramid-w01.
- **Quyết định chờ người dùng:** W18-H2 (ô soi lặp dòng giá trị), W18-H3 đã giải quyết ở W1
  (`ISSUE-ARCH-SCOPE-GATE-LENGTH-CLUE` RESOLVED), W17-H2 (`ISSUE-ARCH-CUT-PLANE-BY-POINT-AND-PARALLEL`), W15-H2
  (vùng chặn ngoài đa diện), W15-H3 (`ISSUE-ARCH-CONSTRUCTION-BINDING-VOCABULARY`).
- **Sau lần report organization trong `docs-cleanup`:** `ISSUE-DOCS-HISTORICAL-REPORTS-AT-DOCS-ROOT` = `RESOLVED` (156 report chuyển,
  11 ngoại lệ root); `ISSUE-OPS-TMP-LEFTOVERS-UNVERIFIED` (w20 xoá 8/212; 204 + 108 mục chờ quyết
  định); `ISSUE-OPS-DOCS-FAULT-INJECTION-TESTS-WRITE-LIVING-DOCS` (năm test ghi tạm vào tài liệu sống); mới:
  `ISSUE-OPS-T1-DOMAIN-SCRIPTS-STALE` (8/10 script T1 trỏ miền đã gỡ); run `cuboid-acceptance`:
  `ISSUE-OPS-LIVE-OPT-IN-NOT-UNIFORM` (smoke script Tin học đã retire, còn `run_rectangular_pyramid_live_analyze.py`; không chặn merge).
  Đã đóng: `ISSUE-DOCS-INVARIANT-ENFORCEMENT-POINTERS-STALE` (`cuboid-acceptance`),
  `ISSUE-OPS-TEST-SUITE-WRITES-FROZEN-EVIDENCE` (w20).
- Các issue khác và trạng thái từng cái: `docs/OPEN_ISSUES.md` (thẩm quyền).

## 6. Bước tiếp theo duy nhất

Run hiện tại: `hybrid-goal-decomposition` (LOCAL, nhánh nghiên cứu; lát 1 B26; product f874b4dd, candidate cac3022f, cache125); trước đó `hybrid-compiler-capability-audit` (không đổi sản phẩm), `geometry-library-important-fixes` (product 4ad89909), `geometry-library-expansion` (8ff994c6) và review `geometry-library-integration-review`.
Run A/B trước: `hybrid-ab-pilot-readiness` (product `cfe2ada5`, candidate `12da4768`, giữ nguyên).
344 focused PASS, 9 mutation killed, 24+288 fake/network=0; clean backend8068 PASS/1 skip/2 deselected; report.md của run.
Offline readiness GO có giới hạn; human review chưa phê duyệt; SMOKE/FULL live NO-GO, không merge/push/default change. `frontend/public/favicon.svg` là của user.
Correction của hybrid cũ: object-binding chính xác, configuration ≠ proof; current divergence authority ở run mới, lịch sử giữ nguyên.

```text
CANONICAL_NEXT_ACTION = POST_NLU_BASELINE_RESEARCH_PRIORITY_DECISION
TARGET_NEXT_ACTION_AFTER_WAVE = OCR_AFTER_FAMILY_EXPANSION
```

Kiến trúc ĐÍCH từ 2026-10-10: Text-to-Geometry Functions (`architecture/TEXT_TO_GEOMETRY_FUNCTIONS_DECISION.md`); run `ai-function-route` (nhánh `feat/text-to-geometry-functions`, chưa tích hợp) dựng adapter Gemini offline; run `hybrid-compiler-selection` (cùng nhánh) so offline nhánh B thực nghiệm (AI trích dữ kiện → planner chọn hàm) với A — tương đương khi AI trích đúng, không tuyên bố B tốt hơn — việc kế tiếp: người dùng quyết pilot có ngân sách (`runs/ai-function-route/EXPERIMENT_PROTOCOL_V2.md` hoặc A/B `runs/hybrid-compiler-selection/REAL_MODEL_AB_PROTOCOL.md`).

Việc `phone-landscape-layout` (máy local, cùng nhánh) đưa điều khiển vào khung khi ngang và ở 360 px, chạy nghiệm thu cuối (Tier-A
8/8 một lượt, T3); việc kế tiếp: người dùng duyệt `review.md` của run này cùng các gói dưới. Việc `mobile-canvas-fit` (máy local, cùng nhánh) khép D5 theo phương án (b) thu hẹp ở khổ hẹp và đo lại tám họ trên candidate
cuối; việc kế tiếp: người dùng duyệt `review.md` của run này cùng các gói dưới. Việc `docs-cleanup` (máy local, cùng nhánh) khép đổi tên test, xử lý `docs/legacy/` + kế hoạch Superpowers và CSS chết, không
đổi hành vi; việc kế tiếp không đổi. Việc `repo-cleanup` (máy local, cùng nhánh) gỡ phần Tin học hết vai trò và chuẩn hoá tên, không đổi hành vi; việc kế tiếp
không đổi. Việc `exact-dimensions` (máy local, cùng nhánh) phục vụ chóp tam giác đều/tứ diện đều với kích thước hữu tỉ bằng khung
affine + metric Gram suy từ đề, chụp ảnh quyết tại nguồn (109 → 15 ảnh cùng ca) và chuẩn hoá tên; việc kế tiếp: người dùng
duyệt `review.md` của run `exact-dimensions` cùng các gói dưới. Việc `regular-triangular-pyramid` W1 (máy local, cùng nhánh) đã thêm chóp tam giác đều + tứ diện đều trong miền ℚ³ trên route
sản phẩm, sửa D1–D4, xoay hiển thị đáy nghiêng và khung nhìn ban đầu; việc kế tiếp: người dùng duyệt `REVIEW.md` của run
`regular-triangular-pyramid-w01` (R1–R12) cùng gói W5/W4 và chọn phương án D5. Bối cảnh trước đó: W5 của việc `regular-square-pyramid` (máy local) đã làm chế độ tập trung (không thanh trên toàn cục, quay lại, công cụ
nhóm, toàn màn hình tuỳ chọn, bỏ thẻ lời giải lặp) và lát cắt backend "chuỗi bằng nhau" trên route thật. Việc kế tiếp:
người dùng duyệt hình theo `docs/evaluation/geometry/runs/regular-square-pyramid-w05/REVIEW.md` cùng gói W4
(gộp duyệt W1–W3); khi có phê duyệt
tường minh thì merge thẳng `feat/regular-square-pyramid` vào `main` (không PR), push, xoá nhánh. Sau đó (phần dưới
là bối cảnh trước W1, giữ để tra): người dùng chọn họ hình từ `docs/ROADMAP.md` §0.2 (ứng viên + khoảng trống theo tầng, snapshot W13);
wave làm họ ấy cùng chín chỉnh sửa giao diện đã chốt (§0.1) và giữ hồi quy §0.3. OCR và nhiều khối để
sau, không tuyên bố đã hỗ trợ. Trước đó, để merge: duyệt hình theo `REVIEW.md` của run `cuboid-merge` (A–F); khi có
phê duyệt tường minh thì merge thẳng vào `main` (không PR), chạy cổng trên cây tích hợp,
push, kiểm SHA remote, xoá nhánh đã merge. Việc kế tiếp chạy trên **nhánh mới rẽ từ `main` đã tích hợp và cập
nhật**, bắt đầu ở **W1**. Đề xuất (người dùng chưa chọn): chóp tứ giác đều + chín chỉnh sửa giao diện, slug
`regular-square-pyramid`, run đầu `regular-square-pyramid-w01` — `HANDOFF.md` §4 của run `cuboid-acceptance`.
Ràng buộc: `LLM_ONLY`; 0 lượt gọi live khi chưa có quyết định ngân sách; `CACHE_VERSION` quyết bằng
bằng chứng; sửa `frontend/src` ⇒ đóng băng lại candidate; không push/merge.

## 7. Evidence có thẩm quyền

- Run `phone-landscape-layout` (PHONE_LANDSCAPE_LAYOUT): `docs/evaluation/geometry/runs/phone-landscape-layout/` (`review.md`, `report.md`, `handoff.md`, `run.json`, `plan.md`, `MEASUREMENT_ATTEMPTS.json`, `inputs/REVIEW_SET.json`, `results/`, `images/`, `diagnostics/`).
- Run `mobile-canvas-fit` (MOBILE_CANVAS_FIT): `docs/evaluation/geometry/runs/mobile-canvas-fit/` (`review.md`, `report.md`, `handoff.md`, `run.json`, `plan.md`, `inputs/REVIEW_SET.json`, `results/`, `images/`, `diagnostics/`).
- Run `docs-cleanup` (DOCUMENTATION_AND_NAMING_CLEANUP): `docs/evaluation/geometry/runs/docs-cleanup/` (`report.md`, `handoff.md`, `run.json`, `inventory.md`, `diagnostics/`).
- Run `repo-cleanup` (REPO_CLEANUP): `docs/evaluation/geometry/runs/repo-cleanup/` (`report.md`, `handoff.md`, `run.json`, `inventory.json`, `code_index_removed_entries.md`, `relocated/`, `inputs/candidate_divergence.json`, `diagnostics/`).
- Run `exact-dimensions` (EXACT_DIMENSIONS_AND_CAPTURE_POLICY): `docs/evaluation/geometry/runs/exact-dimensions/` (`review.md`, `report.md`, `handoff.md`, `run.json`, `plan.md`, `labels.json`, `capture_counts.json`, `results/`, `images/`, `diagnostics/attempt1–3/`).
- Run `regular-triangular-pyramid-w01` (REGULAR_TRIANGULAR_PYRAMID_AND_TETRAHEDRON_SLICE):
  `docs/evaluation/geometry/runs/regular-triangular-pyramid-w01/` (`REVIEW.md`, `REPORT.md`, `HANDOFF.md`, `RUN.json`,
  `MEASUREMENT_ATTEMPTS.json`, `results/`, `images/`, `diagnostics/`, `corrections/W05_RECORD_CORRECTION.json`).
- Run `regular-square-pyramid-w05` (IMMERSIVE_SIMULATION_AND_ARCHITECTURE_SLICE):
  `docs/evaluation/geometry/runs/regular-square-pyramid-w05/` (`REVIEW.md`, `REPORT.md`, `HANDOFF.md`, `RUN.json`,
  `MEASUREMENT_ATTEMPTS.json`, `results/`, `images/`, `diagnostics/`).
- Run `regular-square-pyramid-w04` (SHARED_SIMULATION_UI_CLOSURE):
  `docs/evaluation/geometry/runs/regular-square-pyramid-w04/` (`REVIEW.md`, `REPORT.md`, `HANDOFF.md`, `RUN.json`,
  `MEASUREMENT_ATTEMPTS.json`, `results/`, `images/`, `diagnostics/`).
- Run `regular-square-pyramid-w03` (nghiệm thu local W2 + H-W2-2, H-W2-4):
  `docs/evaluation/geometry/runs/regular-square-pyramid-w03/` (`REVIEW.md`, `REPORT.md`, `HANDOFF.md`, `RUN.json`,
  `results/`, `images/`, `diagnostics/baseline_fe68b4ca/`).
- Run `regular-square-pyramid-w01` (chóp tứ giác đều + giao diện §0.1):
  `docs/evaluation/geometry/runs/regular-square-pyramid-w01/` (`REPORT.md`, `HANDOFF.md`, `RUN.json`,
  `results/BROWSER_EVIDENCE.json`, `results/OCCLUSION_MEASUREMENT.json`, `results/PLAYBACK_EVIDENCE.json`, `images/`).

- Run `cuboid-merge` (gói duyệt + chuyển tiếp ảnh W18 sang `b2d4187a`): `docs/evaluation/geometry/runs/cuboid-merge/`
  (`REVIEW.md`, `HANDOFF.md`, `RUN.json`, `results/FIXTURE_TRANSFER.json`, `results/logs/`).
- Run `cuboid-acceptance` (đối chiếu 24 bất biến + hồ sơ nghiệm thu, chỉ tài liệu):
  `docs/evaluation/geometry/runs/cuboid-acceptance/` (`REPORT.md`, `HANDOFF.md`, `RUN.json`,
  `results/INVARIANT_RECONCILIATION.json`, `results/logs/`).
- Run `cuboid-final-review` (rà soát trọn tài liệu + thẻ từ chối §17):
  `docs/evaluation/geometry/runs/cuboid-final-review/` (`REPORT.md`, `HANDOFF.md`, `RUN.json`, `MANIFEST.json`,
  `inventory/DOCS_INVENTORY.json`, `inventory/HISTORY_SPLIT.json`, `results/BROWSER_REFUSAL_CFR.json`, `images/`).
- W20 (đóng tính đúng + dọn kho có giới hạn): `docs/evaluation/geometry/runs/w20-cleanup-premerge/` (`REPORT.md`,
  `HANDOFF.md`, `RUN.json`, `MANIFEST.json`, `inventory/DELETION_LOG.json`); luật:
  `docs/architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md` §17.
- W19 (tài liệu): `docs/evaluation/geometry/runs/w19-docs-organization/` (`REPORT.md`, `HANDOFF.md`,
  `inventory/INVENTORY.json`, `inventory/MIGRATION_MAP.json`, `verification/`).
- Hình ảnh hiện hành, chờ người duyệt (w18): `docs/evaluation/geometry/runs/w18-binding-focus/` (`REPORT.md`,
  `HANDOFF.md`, `RUN.json`, `MANIFEST.json`, `diagnostics/CONSTRUCTION_BINDING_DECISION_W18.json`);
  phạm vi đăng ký: `docs/architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md` §16.
- Run trước (bất biến) và chủ đề: `docs/evaluation/README.md`; chuỗi đính chính: `docs/EVIDENCE_INDEX.md`.
- Frozen human sets (bất biến): `inputs/human_expected_visibility.json` của wave occlusion; preimage
  camera ở `inputs/REGISTERED_CAMERA_PREIMAGES.json` của w09.

Artifact còn làm căn cứ cho claim/repro giữ nguyên byte; artifact hết consumer có thể xoá qua inventory có kiểm theo
AGENTS §4. Run mới theo `docs/evaluation/RUN_NAMING.md` (mục đầu, từ run `exact-dimensions`):
tên theo việc, không mã lượt; lần thứ hai của cùng việc thêm ngày; ngày, nhánh, commit, candidate nằm trong `run.json`.

## 8. Thứ tự đọc

`AGENTS.md` → `docs/RULES.md` → file này → `docs/CURRENT_STATE.md` →
`docs/OPEN_ISSUES.md` → `docs/ROADMAP.md` → `docs/CODE_INDEX.md` →
`docs/EVIDENCE_INDEX.md` → code/test trực tiếp liên quan.

## 9. Git và evidence safety

- Staging theo explicit file allowlist; kiểm `git diff --cached --name-only`.
- Không push/merge/rewrite history khi chưa được chỉ định.
- Authoritative measurement chạy từ detached clean worktree tại candidate.
- Product output và oracle output không tự sửa frozen human expectations.
- Evidence còn dùng không sửa byte; sai lệch đi qua correction layer. Mục hết vai trò được xoá qua inventory + kiểm consumer.
- Báo cáo wave mới nằm trong thư mục run, không ở gốc `docs/`.
