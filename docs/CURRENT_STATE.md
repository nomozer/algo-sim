# CURRENT_STATE.md — Trạng thái hiện tại

File này chỉ giữ **trạng thái và con trỏ**: danh tính kho mã (có sync-lock), cơ sở
mã + bằng chứng, việc kế tiếp, và bảng của wave gần nhất. Chỉ ghi việc **đã thật sự
xong** (có commit + test). Lịch sử thuộc `STATUS_LEDGER.md`; báo cáo và artifact
thuộc thư mục run trong `docs/evaluation/`.

> **Nhật ký phát triển cũ** — bảng w17 trở về trước, các khối W4B, các mục §1–§7 cũ
> (phần lớn mô tả hệ **Tin học** đã gỡ ở `LEGACY_INFORMATICS_REMOVAL`, 2026-09-02) —
> đã chuyển **nguyên văn** sang
> [`legacy/CURRENT_STATE_HISTORY.md`](legacy/CURRENT_STATE_HISTORY.md) ở W19. Trích
> dẫn kiểu *"CURRENT_STATE §3/§4/§5"* trong tài liệu cũ trỏ vào mục cùng số ở đó.
>
> Kiến trúc hiện tại: [`ARCHITECTURE_MAP.md`](ARCHITECTURE_MAP.md) + contract ở
> [`architecture/`](architecture/). Năng lực sản phẩm:
> `backend/app/simulation/product_capability.py`; năng lực theo tầng:
> [`architecture/geometry_capability_matrix_v2.json`](architecture/geometry_capability_matrix_v2.json).
> Tuyên bố ↔ bằng chứng ↔ giới hạn: [`research/CLAIM_EVIDENCE_MAP.md`](research/CLAIM_EVIDENCE_MAP.md).

> ## ⛳ DANH TÍNH KHO MÃ — ĐỌC TRƯỚC MỌI THAY ĐỔI (cập nhật 2026-10-05)
>
> Ba hàng số sống dưới đây **có sync-lock**: `backend/tests/test_current_state_identity.py`
> dẫn xuất chúng từ nguồn (`app.main.CACHE_VERSION`, `build_matrix()` đọc registry)
> và ĐỎ khi bảng này trôi. Test không viết số nào — sửa **tài liệu**, đừng sửa mã.
>
> | | |
> |---|---|
> | Active development branch | **`fix/cuboid-visual-semantic-closure`** |
> | Remote baseline | **`origin/main` = `a9492ee98ff9dc3302d1ff64465f1c06e9001bce`** tại repository gate 2026-09-28; w11 (2026-09-29) và w12 (2026-10-01): ref cục bộ không đổi, là tổ tiên của HEAD; w13 (2026-10-01), w14 (2026-10-01), w15 (2026-10-02), w16 (2026-10-03), w17 (2026-10-03), w18 (2026-10-04) và w19 (2026-10-04): `git fetch --prune origin` + `ls-remote` — không đổi; w20 và run `cuboid-final-review` (2026-10-05): `ls-remote` — không đổi; run `cuboid-acceptance` và run `cuboid-merge` (2026-10-05): `git fetch --prune origin` + `ls-remote` — không đổi |
> | `CACHE_VERSION` | **111** (W20, 2026-10-04: served → rejected — điểm đề định nghĩa bằng quan hệ mà chương trình đặt bằng toạ độ hay bí danh — `PROOF_CACHE_ROW_W20.json`; giữ ở run `cuboid-final-review`, 2026-10-05: lời từ chối không được cache, envelope được phục vụ trùng byte — `CACHE_DECISION_CFR.json`) — kiểm: `grep -n 'CACHE_VERSION = ' backend/app/main.py` |
> | `HISTORY_SCHEMA_VERSION` | **2** — kiểm: `grep -n 'HISTORY_SCHEMA_VERSION' frontend/src/state/history.ts` |
> | Năng lực hình học | **11 phép dựng · 9 câu lệnh · 7 phép đo** — kiểm: `backend/.venv/Scripts/python.exe backend/scripts/audit_named_operand_ergonomics.py` |
> | `simulation_id` sản phẩm | **`generic.semantic_program`** — duy nhất. Danh mục 24 target Tin học đã gỡ (`LEGACY_INFORMATICS_REMOVAL`, 2026-09-02); xem `docs/SCOPE_ALIGNMENT_AUDIT.md` |
> | Archive (read-only) | tag **`m17-w2b-deep-hardening-archive`** → `feb12d8` — kiểm: `git rev-parse m17-w2b-deep-hardening-archive` (nhánh cùng tên đã xoá 2026-08-24) |
>
> ### Mười một tài liệu CANONICAL theo 11 Information Domain
>
> | Domain | File canonical | Ghi chú |
> |---|---|---|
> | Agent rules | **`docs/RULES.md`** | Quy tắc cứng, scope guard; entry point tại `AGENTS.md` |
> | Architecture map | **`docs/ARCHITECTURE_MAP.md`** | Kiến trúc, luồng xử lý, pipeline tất định |
> | Current state | **`docs/CURRENT_STATE.md`** (file này) | Trạng thái + con trỏ; nhật ký cũ ở `docs/legacy/CURRENT_STATE_HISTORY.md` |
> | Status ledger | **`docs/STATUS_LEDGER.md`** | Lịch sử theo thời gian các wave |
> | Code index | **`docs/CODE_INDEX.md`** | Vị trí code, tooling, test |
> | Roadmap | **`docs/ROADMAP.md`** | Lộ trình ưu tiên khóa luận P0–P6 |
> | Open issues | **`docs/OPEN_ISSUES.md`** | Vấn đề đang mở với stable IDs |
> | Migration checklist | **`docs/MIGRATION_CHECKLIST.md`** | 20 cổng di chuyển compiler-first |
> | AI / session handoff | **`docs/AI_CONTEXT_BUNDLE.md`** | Tóm tắt handoff (<= 300 dòng) |
> | Evidence index | **`docs/EVIDENCE_INDEX.md`** | Chỉ mục báo cáo, artifact và chuỗi đính chính |
> | Docs navigation | **`docs/README.md`** | Cổng điều hướng tài liệu |
>
> ### 🎯 CƠ SỞ KHO MÃ & BẰNG CHỨNG (Base State & Canonical Next Action)
>
> ```text
> PRODUCT_AND_EVIDENCE_BASE_HEAD = a1c53cdb (kiểm chứng có thẩm quyền, worktree tách rời sạch; candidate đóng băng tại 284a9bfa)
> DOCUMENTATION_COMMIT_ROLE = SELF
> DEFAULT_MODE = LLM_ONLY
> CACHE_VERSION = 111
> CANDIDATE = b2d4187a… (was 27c31de6…; một lần đóng băng), product commit 284a9bfa
> USER_DIRTY_STATE = D frontend/public/favicon.svg (bảo tồn tuyệt đối)
> CURRENT_WAVE = CUBOID_ACCEPTANCE_AND_DIRECT_MAIN_INTEGRATION (run cuboid-merge — gói duyệt + tích hợp của việc cuboid-visual-semantic-closure, không đánh số wave; không đổi mã sản phẩm)
> FINAL_DECISION = APPROVED_INTEGRATION_IN_PROGRESS (cuboid-merge) · HUMAN_VISUAL_REVIEW = APPROVED_BY_USER (A–F, 2026-10-05; nguyên văn: runs/cuboid-merge/APPROVAL.md)
> CANONICAL_NEXT_ACTION = NEXT_FAMILY_SLICE_WITH_DECIDED_UI_CHANGES
> TARGET_NEXT_ACTION_AFTER_WAVE = NEXT_FAMILY_SLICE_WITH_DECIDED_UI_CHANGES (người dùng chọn họ từ `ROADMAP.md` §0.2 — đề xuất `regular-square-pyramid-w01`, chưa chọn; chỉnh sửa giao diện §0.1; chặn merge: chỉ còn phê duyệt hình theo `runs/cuboid-merge/REVIEW.md`; việc kế tiếp chạy trên nhánh mới rẽ từ `main` đã cập nhật, bắt đầu ở W1)
> ```

> **Gói duyệt hình + tích hợp — run `cuboid-merge` (2026-10-05; chỉ tài liệu; chưa có phê duyệt, chưa merge):**
>
> | Mục | Kết quả |
> |---|---|
> | Kết luận | **`AWAITING_USER_VISUAL_APPROVAL`** — chờ ACCEPTED/NEEDS_CHANGES cho nhóm A–F của [`REVIEW.md`](evaluation/geometry/runs/cuboid-merge/REVIEW.md) |
> | Ảnh W18 → candidate `b2d4187a` | **chuyển tiếp được, 0 ảnh chụp mới**: fixture tái sinh offline trùng byte bản đã đo; 32/32 fixture hiện hành chỉ khác hai trường danh tính; frontend chỉ đổi ở thẻ từ chối (`results/logs/TRANSFER.log`) |
> | Run | [`cuboid-merge`](evaluation/geometry/runs/cuboid-merge/) (`REVIEW.md`, `HANDOFF.md`, `results/FIXTURE_TRANSFER.json`) |

> **Đối chiếu bất biến + hồ sơ nghiệm thu — run `cuboid-acceptance` (2026-10-05; chỉ tài liệu, byte sản phẩm không đổi so với candidate `b2d4187a`; chưa có review người):**
>
> | Mục | Kết quả |
> |---|---|
> | Kết luận | **`READY_FOR_HUMAN_VISUAL_REVIEW`** — 0 bất biến vi phạm, 0 lỗi chặn nghiệm thu; điều kiện merge còn lại: duyệt hình theo `HANDOFF.md` §1 của run |
> | Bất biến §5 | **24** hàng có con trỏ chết (sửa số 22: #9/#12 thừa hưởng qua "như trên") — 9 đang khoá · 1 chưa đủ bằng chứng (#14, `ISSUE-OPS-LIVE-OPT-IN-NOT-UNIFORM`, không chặn merge) · 14 lịch sử · 0 vi phạm; con trỏ chỉ còn file sống (39/39 hàng, 0 thiếu) — `ISSUE-DOCS-INVARIANT-ENFORCEMENT-POINTERS-STALE` RESOLVED |
> | Quyết định người dùng | H-CFR-2 giữ chữ thường và "toạ độ"; H-CFR-1 = backlog giao diện (`ROADMAP.md` §0.1); H-CFR-3 `THESIS_DRAFT` §1.8 là bản chính đề xuất, `RELATED_WORK_DRAFT` giữ tới khi đối chiếu nội dung riêng |
> | Kiểm chứng | worktree tách rời sạch tại commit tài liệu: `results/logs/INVARIANT_CHECKS_FINAL.log`, `results/logs/DOCS_GATES_FINAL.log` (candidate/cache verify, `LLM_ONLY`, audit tài liệu, test tài liệu, `git diff --check`, báo cáo lịch sử không đổi) |
> | Run | [`cuboid-acceptance`](evaluation/geometry/runs/cuboid-acceptance/) (`REPORT.md`, `HANDOFF.md`, `results/INVARIANT_RECONCILIATION.json`) |

> **Rà soát trọn tài liệu + thẻ từ chối §17 — run `cuboid-final-review` (lượt chốt của việc cuboid; kiểm chứng `a1c53cdb`, worktree tách rời sạch; chưa có review người):**
>
> | Mục | Kết quả |
> |---|---|
> | Kết luận | **`READY_FOR_HUMAN_VISUAL_REVIEW`** — điều kiện merge: review người W18-H1 + thẻ từ chối §17 mới (`HANDOFF.md` §1, đường dẫn ảnh) |
> | Rà soát tài liệu | 8812 file phân lớp (`inventory/DOCS_INVENTORY*.json`); phần thời Tin học của 7 tài liệu sống tách **nguyên văn** sang `legacy/` (119 khối, 2960 dòng, `split_history_cfr.py --verify`); tài liệu sống: 0 link chết, link theo máy 4 → 0; 0 file đã theo dõi bị xoá; 180 báo cáo ở gốc = giới hạn có chủ đích |
> | Đánh số wave | theo từng việc — việc mới, nhánh mới bắt đầu ở W1; định danh `<task-slug>-wNN` (`evaluation/RUN_NAMING.md`; AGENTS §2, RULES §2) |
> | Thẻ từ chối §17 | "Hệ chưa kiểm chứng được ‹quan hệ›, vì điểm này ‹cách đặt› thay vì dựng từ quan hệ trong đề. Hệ tạm dừng…" + nhãn "chưa kiểm chứng được phép dựng"; lệch/chưa đối chiếu giữ nhãn; trình duyệt **12/12** desktop + mobile |
> | T3 từ đường dẫn CÓ dấu cách (`a1c53cdb`) | **PASS** — pytest 7079/0 (1 skipped, 2 deselected) · vitest 1061/1061 · build · demo 5/5 · bề mặt sập 6/6; cổng danh tính, audit tài liệu, harness node đạt |
> | Candidate · `CACHE_VERSION` | `27c31de6…` → **`b2d4187a…`** (một lần đóng băng, `284a9bfa`) · **111** giữ nguyên (chứng minh theo hàng, `6ec40806`); vân tay bề mặt mô hình không đổi |
> | Bất biến | 0/181 báo cáo lịch sử đổi; ngoài run, `docs/evaluation` chỉ đổi `RUN_NAMING.md` + hai registry sống; `LLM_ONLY`; 0 lượt gọi live; không push/merge/xoá nhánh |
> | Run | [`cuboid-final-review`](evaluation/geometry/runs/cuboid-final-review/) (`REPORT.md`, `HANDOFF.md`) |

> **Đóng tính đúng trước merge + dọn kho — w20 (kiểm chứng `5fbb397b`, worktree tách rời sạch; chưa có review người):**
>
> | Mục | Kết quả |
> |---|---|
> | Kết luận | **`READY_FOR_HUMAN_VISUAL_REVIEW`** — hai issue chặn đã đóng bằng bằng chứng; điều kiện merge còn lại: review người W18-H1 (`NOT_APPROVED`) |
> | Đích quan hệ đặt bằng toạ độ (amendment §17) | Trước sửa: hình chiếu đặt bằng toạ độ ngoài vùng đa diện được phục vụ (một ca đáp số sai 2√14 thay vì 3√6), toạ độ rồi mới dựng và bí danh của một đỉnh cũng được phục vụ. Nay: `DEFINED_BY_COORDINATES` → `CONSTRUCTION_REPLACED_BY_COORDINATES` ở mọi vùng. Probe 20/27 → **26/27** (hàng còn lại do cổng miền, ghi trước bản sửa); census 179 hàng không đổi; tiêm lỗi 10/10 bắt |
> | Test không ghi bằng chứng đông cứng | `run_reconciliation(out_dir)` bắt buộc thư mục ra, từ chối thư mục đông cứng và thư mục con; lượt backend đầy đủ ở cây chính để `git status` y nguyên |
> | T3 từ đường dẫn CÓ dấu cách (`5fbb397b`) | **PASS** — pytest 7077/0 (1 skipped, 2 deselected) · vitest 1058/1058 · build · demo · bề mặt sập 6/6; cổng danh tính, audit tài liệu, harness node đạt |
> | Candidate · `CACHE_VERSION` | `d3b4cab9…` → **`27c31de6…`** (hai lần đóng băng, khai ở run) · 110 → **111** (`bedb1040`; khoá `ac241a8d`; vân tay bề mặt mô hình không đổi) |
> | Luật và dọn kho | AGENTS.md §2/§4 + RULES.md §1 (`a36f3e97`); 64 mục xoá có bằng chứng cơ giới, `docs/legacy/superpowers/` giữ 18/18, 314 mục chờ quyết định |
> | Bất biến | ngoài run W20, `docs/evaluation` chỉ đổi hai registry sống; 0/181 báo cáo lịch sử đổi; `LLM_ONLY`; 0 lượt gọi live; không push/merge/xoá nhánh |
> | Run | [`w20-cleanup-premerge`](evaluation/geometry/runs/w20-cleanup-premerge/) (`REPORT.md`, `HANDOFF.md`) |

> **Tổ chức lại tài liệu và bằng chứng nghiên cứu — w19 (chỉ tài liệu; 0 thay đổi sản phẩm; 0 lượt gọi model):**
>
> | Mục | Kết quả |
> |---|---|
> | Kết luận | **`DOCS_REORGANIZED_AND_VERIFIED`** — trạng thái sản phẩm vẫn là của w18 (bảng dưới; người duyệt `NOT_APPROVED`) |
> | Cấu trúc | gốc `docs/` = 11 tài liệu chuẩn tắc + 7 tài liệu dự án + báo cáo wave cũ (catalog đóng, 180); `research/` (bản đồ tuyên bố, khoá luận, bài báo); `evaluation/` (run); `legacy/` (hết hiệu lực) — [`README.md`](README.md) |
> | Di chuyển | 65 file bằng `git mv` (33 sang `research/`, 32 sang `legacy/`); nhật ký phát triển của file này sang [`legacy/CURRENT_STATE_HISTORY.md`](legacy/CURRENT_STATE_HISTORY.md) nguyên văn; cũ → mới: `inventory/MIGRATION_MAP.json` của run |
> | Một nơi có thẩm quyền | tuyên bố ↔ bằng chứng ↔ giới hạn: [`research/CLAIM_EVIDENCE_MAP.md`](research/CLAIM_EVIDENCE_MAP.md) thay ba bảng cũ; báo cáo wave mới chỉ trong thư mục run (`audit_docs_layout`) |
> | Bất biến | báo cáo wave cũ và `docs/evaluation/**` cũ trùng blob với `6d0e6321`; candidate và cache 110 verify; `LLM_ONLY`; 0 lượt gọi live; không push/merge |
> | Run | [`w19-docs-organization`](evaluation/geometry/runs/w19-docs-organization/) |

> **Phép dựng điểm gắn với quan hệ của đề + nhãn tập trung — w18 (measurement `0ca3accf`, detached clean worktree; chưa có review người):**
>
> | Mục | Kết quả |
> |---|---|
> | Kết luận | **`READY_FOR_HUMAN_VISUAL_REVIEW`** — mọi cổng bắt buộc đạt trên candidate cuối; review người `NOT_APPROVED` |
> | Phép dựng điểm cùng thực thể với đề (§16.1–16.4) | Trước sửa: chiếu lên sai đường (6√2 thay vì 3√6), sai mặt phẳng, tráo danh sách "lần lượt" (3√6 thay vì 9), đổi tên đích và một điểm trùng toạ độ khác danh tính đều được PHỤC VỤ. Nay chặng `construction_binding` đối chiếu theo danh tính: lệch ⇒ `CONSTRUCTION_NOT_TEXT_BOUND` ở mọi vùng, nêu cả hai quan hệ; chưa đối chiếu được ⇒ `CONSTRUCTION_BINDING_UNVERIFIED` trong vùng đa diện, không bao giờ nói đề sai |
> | Census (`00654627`) | **SHIP** · AC2 **18/18** · không hàng phục vụ nào của W14–W17C bị từ chối · thay đổi tuyến duy nhất: W15 `oov:chia_doan_canh` (vốn bị từ chối) nay bị từ chối sớm hơn · corpus W18 23/23 đúng kỳ vọng |
> | Nhãn tập trung + một nơi giải thích (§16.5–16.6) | Mặc định: tên điểm + dữ kiện; chọn đại lượng ⇒ nhãn + chuỗi số; một công tắc "Hiện tất cả" (thay "Số đo"/"Kết quả"); ô soi là nơi giải thích duy nhất; lời giải thu gọn mặc định; bản đo trùng gộp theo chủ thể (`same_as`), không theo giá trị |
> | Nhân chứng khoảng cách (§16.7) | Điểm → đường/mặt: đoạn nét đứt tới chân CHÍNH XÁC do kernel tính + ký hiệu vuông góc, chỉ khi nhãn khoảng cách hiện; frontend không tính chân |
> | Bộ đo | Lượt đo nghiệm thu đầu (`8caa8307`) đạt hết; tiêm lỗi frontend vòng 1 tìm ra ba điểm mù của bộ đo trình duyệt (nét đứt khi tô sáng, mốc của công tắc, hai bản công thức khi lời giải mở). Sửa bộ đo đỏ-trước (`1d8dfc6f`), giữ riêng lần thử 1, đo lại toàn bộ ở `0ca3accf` |
> | Tiêm lỗi | backend **12/12** (vòng 3) · frontend vòng 2 tại `0ca3accf` **12/12** (8 đơn vị + 4 trình duyệt; vòng 1 tại `8caa8307`: đơn vị 8/8, trình duyệt 1/4 — ba điểm mù của bộ đo, đã sửa) |
> | T3 từ đường dẫn CÓ dấu cách (`0ca3accf`) | **PASS** — pytest 7001/0 fail (1 skipped, 2 deselected) · vitest 1058/1058 · build · demo 5/5 · bề mặt sập 6/6 |
> | Ảnh · oracle · playback | Trình duyệt 12/12 dương, 46/46 âm (8 loại, có 3 loại W18), 6/6 phục vụ; chọn từng đại lượng 58/58; một vùng công thức 10/10 (thu gọn) + 10/10 (mở); "Hiện tất cả" so với trạng thái trước lần bấm 12/12; nét đứt theo bước 72/72 · occlusion `HUMAN_REVIEW_PENDING` (bốn cảnh như w15–w17) · playback 12/12 · 64 crop, 0 bất đồng |
> | Candidate · `CACHE_VERSION` | `d63d6fd4…` → **`d3b4cab9…`** (đóng băng MỘT lần tại `7a06ee47`) · 109 → **110** (`1e8c5658`; khoá danh tính `5cfb53a1`; fingerprint provider không đổi) |
> | Giới hạn khai | Từ vựng đóng (trung điểm, hình chiếu): tâm, trọng tâm, giao điểm chưa đối chiếu; cách nói ngoài từ vựng bị từ chối dù đúng (`ISSUE-ARCH-CONSTRUCTION-BINDING-VOCABULARY`) · cổng phạm vi chưa có manh mối "độ dài" (`ISSUE-ARCH-SCOPE-GATE-LENGTH-CLUE`) · tô sáng cạnh khuất chỉ xảy ra ở họ thiết diện nên ở năm họ kia luật nét đứt do test đơn vị giữ |
> | Run | [`w18-binding-focus`](evaluation/geometry/runs/w18-binding-focus/) |
>
> Nguồn: `docs/evaluation/geometry/runs/w18-binding-focus/` (`REPORT.md`, `HANDOFF.md`).
> Bảng w17 trở về trước: [`legacy/CURRENT_STATE_HISTORY.md`](legacy/CURRENT_STATE_HISTORY.md).
