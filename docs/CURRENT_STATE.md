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

> ## ⛳ DANH TÍNH KHO MÃ — ĐỌC TRƯỚC MỌI THAY ĐỔI (cập nhật 2026-10-04)
>
> Ba hàng số sống dưới đây **có sync-lock**: `backend/tests/test_current_state_identity.py`
> dẫn xuất chúng từ nguồn (`app.main.CACHE_VERSION`, `build_matrix()` đọc registry)
> và ĐỎ khi bảng này trôi. Test không viết số nào — sửa **tài liệu**, đừng sửa mã.
>
> | | |
> |---|---|
> | Active development branch | **`fix/cuboid-visual-semantic-closure`** |
> | Remote baseline | **`origin/main` = `a9492ee98ff9dc3302d1ff64465f1c06e9001bce`** tại repository gate 2026-09-28; w11 (2026-09-29) và w12 (2026-10-01): ref cục bộ không đổi, là tổ tiên của HEAD; w13 (2026-10-01), w14 (2026-10-01), w15 (2026-10-02), w16 (2026-10-03), w17 (2026-10-03), w18 (2026-10-04) và w19 (2026-10-04): `git fetch --prune origin` + `ls-remote` — không đổi |
> | `CACHE_VERSION` | **111** (W20, 2026-10-04: served → rejected — điểm đề định nghĩa bằng quan hệ mà chương trình đặt bằng toạ độ hay bí danh — `PROOF_CACHE_ROW_W20.json`) — kiểm: `grep -n 'CACHE_VERSION = ' backend/app/main.py` |
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
> PRODUCT_AND_EVIDENCE_BASE_HEAD = 4a9db1ff (measurement commit 0ca3accf) — W19 không đổi sản phẩm
> DOCUMENTATION_COMMIT_ROLE = SELF
> DEFAULT_MODE = LLM_ONLY
> CACHE_VERSION = 111
> CANDIDATE = d3b4cab9… (was d63d6fd4…; one freeze), product commit 7a06ee47 — W19 không đóng băng lại
> USER_DIRTY_STATE = D frontend/public/favicon.svg (bảo tồn tuyệt đối)
> CURRENT_WAVE = W19_DOCS_REORGANIZATION_AND_RESEARCH_EVIDENCE_CURATION (w19, chỉ tài liệu; commit a5c2e6f2 · a44631a9 · commit tài liệu này)
> FINAL_DECISION = DOCS_REORGANIZED_AND_VERIFIED (w19) · sản phẩm: READY_FOR_HUMAN_VISUAL_REVIEW (w18), HUMAN_VISUAL_REVIEW = NOT_APPROVED
> CANONICAL_NEXT_ACTION = NEXT_FAMILY_SLICE_WITH_DECIDED_UI_CHANGES
> TARGET_NEXT_ACTION_AFTER_WAVE = NEXT_FAMILY_SLICE_WITH_DECIDED_UI_CHANGES (người dùng chọn họ từ `ROADMAP.md` §0.2; chỉnh sửa giao diện §0.1; chặn merge: review người W18 + `ISSUE-ARCH-CONSTRUCTION-BINDING-LITERAL-TARGET`)
> ```

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
