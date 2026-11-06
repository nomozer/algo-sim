# AI_CONTEXT_BUNDLE.md — AlgoSim Session Handoff & Quick Context
**CURRENT 2026-11-04 — FINAL HYBRID ARCHITECTURE CUTOVER (`HYBRID_DEFAULT_CUTOVER_COMPLETE = YES`, `LEGACY_EXECUTION_RETIRED = YES`, `LEGACY_FULLY_RETIRED = NO`, `PRODUCTION_DEPLOYMENT_VERIFIED = NO`, `INDEPENDENT_H1_VALIDATION = NOT_MEASURED`):** Owner-directed cutover makes Hybrid `/4` (`TypedFactNext /2 -> Source Gate -> FactGraph -> Planner /26 -> Registry /33 -> Engine /24 -> Adapter /4`) the official default `POST /api/analyze` pipeline (`HYBRID_ROUTE_MODE = live`, `staging-replay` for dev/test, `ALLOW_LIVE_AI=0` kill-switch, `503 INVALID_HYBRID_ROUTE_MODE` on `off`/unknown, zero fallback to `LLM_ONLY`); retires `pipeline.py`, `adapter3_simulation.py`, `geometry_compiler/*`, and 10 legacy `.md` skills (`transcribe.md` and `semantic_program/route.py` preserved); bumps `CACHE_VERSION = 132` (`102` measured files `765487a4b48e7d52…`, product `52205f45`, frozen candidate `f5f2c147`, Full T3 `FULL_PRODUCT_GATE_PASS` `13,762` pytest / `1,502` vitest `full-t3-f5f2c147.json`, `main` `--no-ff` merge `dacd7f5e`); pre-cutover rollback tag `pre-hybrid-cutover-f986e897` (`f986e897`). Report: `evaluation/geometry/runs/hybrid-master-backend-replacement/ALGOSIM_HYBRID_CUTOVER_FINAL_REPORT.md`.
**INTEGRATION 2026-10-30 — W3-F2 REMOTE_VERIFIED at first push `4d304992` (baseline `996f114b`).** Narrow Owner supersession: `evaluation/geometry/runs/publication-safety-remediation/REMOTE_PUBLICATION_SECURITY_DECISION.md` §4; range PASS, head BLOCKED with identical 105 baseline findings (104 pending), all five Google-key vectors synthetic. Closure and final documentation-tip read-back location: `evaluation/geometry/runs/hybrid-v2-w3-f2-ratio-projection-language-grounding/integration/report.md`. One original worktree removed; seven retained; verifier unregistered but residual retained. Candidate `4e7fe91d`, product `dd17fbfb`, `LLM_ONLY`, cache130, live0; earlier snapshots retain their timing.
**2026-10-27 — Root consolidation (latest repository handoff):** root is clean on `main`; product baseline `b7b8358e`, cache130, LLM_ONLY and opt-in Hybrid unchanged. The 79-file audit, local receipt recovery paths, retained research refs and quarantined worktrees are in `evaluation/geometry/runs/root-consolidation/ROOT_CONSOLIDATION_REPORT.md`. Next backend campaign starts with certificate-bound D-10 point–line presentation, then independent holdout/NL extraction; no implementation or live provider call in cleanup.
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

AlgoSim chuyển đề hình học không gian tiếng Việt thành `Scene3D` tương tác, các bước dựng liên tục và đáp số chính xác qua kiến trúc chính thức **Hybrid `/4`**:
`Vietnamese Problem → Gemini → TypedFactNext /2 → Source Gate → FactGraph → Planner /26 → Registry /33 → Exact Kernel /24 → Adapter /4 → Scene3D + Construction Steps + Results`
Gemini chỉ trích xuất dữ kiện, quan hệ và mục tiêu (`TypedFactNext /2`); không sinh chương trình giải riêng cho từng đề. Engine tất định sở hữu hoàn toàn tọa độ, thực thi, đo lường, correctness và scene state. (`RequestContract` chỉ còn giữ vai trò tương thích nội bộ `COMPATIBILITY_REQUIRED` trong `semantic_program/route.py` và truyền `solid_topology` tất định.)

- `POST /api/analyze` chạy **Hybrid `/4`** mặc định (`HYBRID_ROUTE_MODE = live`; `staging-replay` cho replay offline dev/test; `HYBRID_ROUTE_MODE=off` trả HTTP `503 INVALID_HYBRID_ROUTE_MODE`; thiếu `GEMINI_API_KEY` ở `live` trả HTTP `503 MISSING_API_KEY`; `ALLOW_LIVE_AI=0` trả HTTP `503 LIVE_AI_DISABLED`; **0 fallback** về `LLM_ONLY`).
- `CACHE_VERSION = 132` (`ROUTE_D_CACHE_POLICY = 132:route-d`; lịch sử các đợt bump trước ở `CURRENT_STATE.md`).
- Đã gỡ bỏ: thực thi `LLM_ONLY` (`pipeline.py`), `Adapter /3` (`adapter3_simulation.py`), `Compiler C` (`geometry_compiler/*`) và các cờ cũ `HYBRID_V2_LOCAL`, `GEOMETRY_COMPILER_MODE`. Rollback kiến trúc là rollback Git/deployment về tag `pre-hybrid-cutover-f986e897`.
- Không hardcode case/label/tọa độ/answer vào mã sản phẩm; thiếu dữ kiện, mâu thuẫn, ngoài phạm vi, cần làm rõ (`route-d-clarification/1`) hoặc lỗi hạ tầng phải fail-closed trung thực.

## 2. Repository state hiện tại

Cập nhật 2026-11-04 (sau `FINAL_HYBRID_ARCHITECTURE_CUTOVER` trên `main`; các mục cũ ở §4–§6 bên dưới là bối cảnh lịch sử trước cutover; việc mở: `OPEN_ISSUES.md`; lộ trình: `ROADMAP.md` §0).
```text
MAIN = origin/main includes Final Hybrid Architecture Cutover (merge dacd7f5e; product 52205f45; frozen candidate f5f2c147, 102 measured files 765487a4b48e7d52…; clean detached Full T3 FULL_PRODUCT_GATE_PASS: 13762 pytest / 1502 vitest, full-t3-f5f2c147.json)
AXO = main 64847c1e is the squash of the Axo Hybrid /4 reliability branch (2026-11-07); its candidate seal is red on main (product_commit_sha off main) until branch chore/axo-postmerge-branding-consolidation (Axo favicon + tab titles + re-freeze, NOT merged) lands — run axo-postmerge-consolidation
PRODUCT_STATE = DEFAULT_MODE HYBRID (/4) · HYBRID_ROUTE_MODE live (staging-replay dev/test) · CACHE_VERSION 132 (132:route-d) · typed-fact-next/2 · geometry-fact-planner/26 · geometry-functions/33 · geometry-function-engine/24 · hybrid-simulation-adapter/4
CUTOVER_STATUS = HYBRID_DEFAULT_CUTOVER_COMPLETE=YES · LEGACY_EXECUTION_RETIRED=YES · LEGACY_FULLY_RETIRED=NO (semantic_program/route.py COMPATIBILITY_REQUIRED) · PRODUCTION_DEPLOYMENT_VERIFIED=NO · INDEPENDENT_H1_VALIDATION=NOT_MEASURED · NEW_LIVE_SMOKE_NOT_MEASURED
ROLLBACK = Git/deployment version rollback to tag pre-hybrid-cutover-f986e897 (f986e897; optional ALLOW_LIVE_AI=0 emergency stop); HYBRID_ROUTE_MODE=off returns 503 INVALID_HYBRID_ROUTE_MODE (no LLM_ONLY fallback)
OPEN = INDEPENDENT_H1_VALIDATION (60-case external H-1 corpus not yet authored/measured; C26/Full T3 are not H-1) · ISSUE-ARCH-PARTIAL-STATED-CUT-NAMING · ISSUE-ARCH-HISTORY-REOPEN-DROPS-SCENE3D · ISSUE-ARCH-ROUTE-D-DIACRITIC-FREE-INPUT (OPEN_ISSUES.md)
```

Thay đổi chưa commit của người dùng: không restore, sửa, stage hoặc commit khi chưa được cho phép rõ ràng (xoá favicon AlgoSim
cũ đã được cho phép và commit ở f89a1a8b; favicon HIỆN HÀNH là logo Axo `frontend/public/favicon.svg`, khôi phục ở run
`axo-postmerge-consolidation` — đừng gỡ lại theo bản ghi cũ). Không amend/rebase/squash chuỗi commit đã được evidence tham chiếu.

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

Trạng thái hiện hành (2026-11-04): **Hybrid `/4`** đã tích hợp làm kiến trúc mặc định trên `main` (`ALGOSIM_HYBRID_CUTOVER_FINAL_REPORT.md`); kiểm định độc lập trên tập 60 đề mới `H-1` (`INDEPENDENT_H1_VALIDATION = NOT_MEASURED`), live smoke sau cutover (`NEW_LIVE_SMOKE_NOT_MEASURED`) và xác minh triển khai production (`PRODUCTION_DEPLOYMENT_VERIFIED = NO`) vẫn chờ thực hiện theo quyết định và ngân sách của Owner. Các đoạn dưới khối `CANONICAL_NEXT_ACTION` là nhật ký bàn giao lịch sử trước cutover (giữ nguyên để truy vết).

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
*(Lưu ý lịch sử: dòng ràng buộc `LLM_ONLY` của đợt `cuboid-acceptance` đã hết hiệu lực từ cutover Hybrid `/4` ngày 2026-11-04; giữ luật 0 lượt gọi live khi chưa đăng ký ngân sách, `CACHE_VERSION` quyết bằng bằng chứng, không tự ý push/merge.)*

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
