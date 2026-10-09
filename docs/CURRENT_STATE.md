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
> | Active development branch | **`feat/regular-square-pyramid`** — việc `regular-square-pyramid`: W1 (run `regular-square-pyramid-w01`) + W2 (run `regular-square-pyramid-w02`, 2026-10-05, cloud) + W3 (`regular-square-pyramid-w03`, nghiệm thu local) + W4 (`regular-square-pyramid-w04`, 2026-10-06, giao diện chung) + W5 (`regular-square-pyramid-w05`, 2026-10-06/07, chế độ tập trung + bộ đọc chuỗi bằng nhau) + việc `regular-triangular-pyramid` W1 (`regular-triangular-pyramid-w01`, 2026-10-07, chóp tam giác đều + tứ diện đều, giữ trên cùng nhánh theo lệnh người dùng) + việc `exact-dimensions` (run `exact-dimensions`, 2026-10-07/08, kích thước hữu tỉ + chụp ảnh tại nguồn + chuẩn hoá tên) + việc `mobile-canvas-fit` (run `mobile-canvas-fit`, 2026-10-08, D5: canvas vừa hình trên điện thoại) + việc `phone-landscape-layout` (run `phone-landscape-layout`, 2026-10-08/09, điện thoại ngang + 360 px + nghiệm thu cuối; W3–W5 và các việc sau chỉ ở local), rẽ từ `main` = `38d41588`; **đã fast-forward vào `main` = `caed3809` và push (2026-10-09, run `frontend-freeze`, baseline frontend tạm thời có ngoại lệ theo `APPROVAL.md`); nhánh giữ lại — xoá chưa được phép**. Trước đó: nhánh `fix/cuboid-visual-semantic-closure` đã fast-forward vào `main`, push và xoá (run `cuboid-merge`) |
> | Remote baseline | **`origin/main` = `caed38096f0693702dc0b69668ad8ba58d5fb1fd`** sau push của run `frontend-freeze` (2026-10-09, fast-forward từ `38d41588`, không force, `ls-remote` khớp; commit ghi kết quả tích hợp đi sau, tra `git log -1 origin/main`). Trước đó: `origin/main` = `c282a5f398ea5ed19e311dec10a8c5c2bc4d02ec` sau push của run `cuboid-merge` (2026-10-05, fast-forward từ `a9492ee9`). Lịch sử trước đó: `origin/main` = `a9492ee98ff9dc3302d1ff64465f1c06e9001bce` tại repository gate 2026-09-28; w11 (2026-09-29) và w12 (2026-10-01): ref cục bộ không đổi, là tổ tiên của HEAD; w13 (2026-10-01), w14 (2026-10-01), w15 (2026-10-02), w16 (2026-10-03), w17 (2026-10-03), w18 (2026-10-04) và w19 (2026-10-04): `git fetch --prune origin` + `ls-remote` — không đổi; w20 và run `cuboid-final-review` (2026-10-05): `ls-remote` — không đổi; run `cuboid-acceptance` và run `cuboid-merge` (2026-10-05): `git fetch --prune origin` + `ls-remote` — không đổi; regular-square-pyramid-w01 (2026-10-05): `ls-remote` = `38d41588…` — không đổi (commit ghi kết quả tích hợp của cuboid-merge) |
> | `CACHE_VERSION` | **120** (c0-whole-solid-grounding, 2026-10-09: C0 kiểm khẳng định toàn khối của đề trên toạ độ đề cho, served → refused; trước: 119 ở geometry-grounding-safety, 2026-10-09: C0 kiểm quan hệ hình dạng đề nói trên toạ độ đề cho, served → refused; trước: 118 ở docs-cleanup, 2026-10-08: envelope từ chối T8 thiếu kích thước đổi nguyên nhân `UNKNOWN` → `SOURCE`, phán quyết vẫn `unsupported`; trước: 117 ở exact-dimensions) — kiểm: `grep -n 'CACHE_VERSION = ' backend/app/main.py` |
> | `HISTORY_SCHEMA_VERSION` | **2** — kiểm: `grep -n 'HISTORY_SCHEMA_VERSION' frontend/src/state/history.ts` |
> | Năng lực hình học | **11 phép dựng · 9 câu lệnh · 7 phép đo** — kiểm: `backend/.venv/Scripts/python.exe backend/scripts/audit_named_operand_ergonomics.py` |
> | `simulation_id` sản phẩm | **`generic.semantic_program`** — duy nhất. Danh mục 24 target Tin học đã gỡ (`LEGACY_INFORMATICS_REMOVAL`, 2026-09-02); xem `docs/evaluation/reports/SCOPE_ALIGNMENT_AUDIT.md` |
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
> PRODUCT_AND_EVIDENCE_BASE_HEAD = 45f5a7f0 (dải lớp học gọn thành chip trên màn chật; trên nền điện thoại ngang 95a56a17 + D5 c9bcdcdb); bằng chứng trình duyệt 3095e4f0 (đo 6a1801e7 lần 3, run classroom-band-fit: dải lớp 24/24, không dải lớp 55/56, Tier-A 8/8 một lượt); cổng T3 ở commit tài liệu cuối của run (runs/classroom-band-fit/handoff.md §2)
> DOCUMENTATION_COMMIT_ROLE = SELF
> DEFAULT_MODE = LLM_ONLY
> CACHE_VERSION = 120 trên nhánh `fix/c0-whole-solid-grounding` (C0 mâu thuẫn khẳng định toàn khối ↔ toạ độ served → refused; runs/c0-whole-solid-grounding/cache/decision.json) · `main`: 119 (geometry-grounding-safety; runs/geometry-grounding-safety/cache/decision.json)
> CANDIDATE = bbfa5b0da3a5353a… trên `main` (product commit 765291ab; cache 119); nhánh `fix/c0-whole-solid-grounding`: 8c4c01284232121b… (102 file; product commit c11e8c9d; cache 120; đóng băng LOCAL d838cc5b, T3 PASS — runs/c0-whole-solid-grounding/handoff.md)
> USER_DIRTY_STATE = không — xoá frontend/public/favicon.svg và dòng .playwright-cli/ của .gitignore đã commit theo lệnh người dùng (f89a1a8b; index.html không còn trỏ tệp đã xoá); phần dọn Tin học đã kiểm đã commit ở 0d4c4f8b
> CURRENT_WAVE = GEOMETRY_GROUNDING_SAFETY (run `geometry-grounding-safety` — Cloud sửa C0 + compiler, LOCAL bổ sung 765291ab + kiểm + đóng băng, đã tích hợp `main`; nhánh đã xoá sau tích hợp; frontend vẫn đóng băng theo `runs/frontend-freeze/`)
> FINAL_DECISION = MERGED_AND_PUSHED (geometry-grounding-safety: `main` = `origin/main` = `47d05f22`, fast-forward từ e6c3cf68, 2026-10-09; runs/geometry-grounding-safety/APPROVAL.md · G05: 9666b861, runs/general-polygon-base/APPROVAL.md · G04: a0fdbba4, runs/oblique-prism/APPROVAL.md) · baseline frontend: MERGED_AND_PUSHED_WITH_EXCEPTIONS (runs/frontend-freeze/APPROVAL.md) · HUMAN_VISUAL_REVIEW = NOT_APPROVED (C1–C6 đã xem, chưa phê duyệt chất lượng; P1–P6 PENDING; UX debt OPEN/DEFERRED) · NEXT_ACTION = người dùng chọn việc kế tiếp: họ hình tiếp theo (ROADMAP §0.2; G06 chưa bắt đầu) rồi OCR; frontend đóng băng; giữ LLM_ONLY, không chuyển compiler-first
> CANONICAL_NEXT_ACTION = MISSING_FAMILY_EXPANSION_ON_EXISTING_ARCHITECTURE
> TARGET_NEXT_ACTION_AFTER_WAVE = OCR_AFTER_FAMILY_EXPANSION (sau giai đoạn mở rộng họ hình; ROADMAP §0.4 P4)
> ```

> **C0 kiểm khẳng định toàn khối — run c0-whole-solid-grounding (2026-10-09, Cloud, nhánh `fix/c0-whole-solid-grounding`; 0 model call; LOCAL đã kiểm — chờ người dùng quyết merge):**
>
> | Mục | Kết quả |
> |---|---|
> | Trước (`9762f441`) | 16 đề tự mâu thuẫn được phục vụ C0: lăng trụ đứng/xiên, hộp chữ nhật, lập phương (+ cạnh), chóp tứ giác/tam giác đều (+ cạnh bên, trung đoạn, tâm đáy chỉ có toạ độ trong đề), tứ diện đều (+ cạnh), chiều cao chóp/lăng trụ |
> | Sửa | `_KIEM_C0` thêm định nghĩa chính xác các khẳng định toàn khối trên khối CÓ TÊN (amendment §22); cùng mã/đường từ chối §21 |
> | Nhãn | 29 hàng ghi trước + oracle độc lập, 29/29 khớp; thiếu dữ kiện (không toạ độ, khối không tên) không bị coi là mâu thuẫn |
> | `CACHE_VERSION` · candidate | **120** (served → refused, probe trước/sau; bề mặt mô hình không đổi) · candidate **`8c4c0128…`** (product `c11e8c9d`; đóng băng LOCAL `d838cc5b`, `--verify` khớp) |
> | Kiểm LOCAL | T3 `FULL_PRODUCT_GATE_PASS` tại `d838cc5b`: pytest 7401 passed / 1 skipped, vitest 1040/1040, build, demo, bề mặt sập (`diagnostics/t3_d838cc5b.log`); chạy lại nhãn trên `main` và nhánh: **15** (không phải 16) hàng served → refused, 0 hồi quy; ca biên LOCAL (căn, chiều cao ≠ cạnh bên, ký hiệu `a`, mệnh đề mục tiêu, phủ định) đúng |
> | Còn mở | `ISSUE-ARCH-C0-WHOLE-SOLID-CLAIMS-NOT-READ` (bộ đọc không phát khẳng định cho vài cách viết) |
> | Run | [`c0-whole-solid-grounding`](evaluation/geometry/runs/c0-whole-solid-grounding/) (`plan.md`, `report.md`, `handoff.md`) |

> **Sửa an toàn grounding — run geometry-grounding-safety (2026-10-09, Cloud, nhánh `fix/geometry-grounding-safety`; 0 model call; LOCAL đã kiểm; đã tích hợp `main` = `47d05f22` theo `APPROVAL.md`):**
>
> | Mục | Kết quả |
> |---|---|
> | C0 | quan hệ hình dạng đề nói được kiểm chính xác trên toạ độ đề cho; mâu thuẫn ⇒ `SOURCE_SHAPE_CONTRADICTS_COORDINATES` (amendment §21) |
> | Compiler | tứ giác chưa khai dạng là hình chữ nhật chỉ khi ≥ 3 góc vuông kề; một góc ⇒ `BASE_RECTANGLE_NOT_PROVEN` |
> | Nhãn | 18 hàng ghi trước + oracle độc lập, 21/21; red-before 10 đỏ |
> | LOCAL bổ sung | điểm chương trình không khai lấy toạ độ chính đề trong phép kiểm C0 (`765291ab`; trước: `E(5;5;0)` + "AE ⊥ AB" vẫn phục vụ) — 3 test, tiêm lỗi đỏ |
> | Candidate · `CACHE_VERSION` | **`bbfa5b0d…`** (product `765291ab`; đóng băng LOCAL `e1dfc851`, `--verify` khớp) · **119** (served → refused, kiểm độc lập; khoá danh tính khớp) |
> | Kiểm LOCAL | T3 `FULL_PRODUCT_GATE_PASS` tại `e1dfc851`: pytest 7367 passed / 1 skipped, vitest 1040/1040, build, demo, bề mặt sập (`diagnostics/t3_e1dfc851.log`); còn mở: `ISSUE-ARCH-C0-WHOLE-SOLID-RELATIONS-NOT-CHECKED` |
> | Run | [`geometry-grounding-safety`](evaluation/geometry/runs/geometry-grounding-safety/) |

> **G05 đáy đa giác theo chuỗi góc vuông — run general-polygon-base (2026-10-09, Cloud, nhánh `feat/general-polygon-base`; 0 model call; LOCAL đã kiểm; đã tích hợp `main` = `9666b861` theo `APPROVAL.md`):**
>
> | Mục | Kết quả |
> |---|---|
> | Trước | hình thang vuông bị từ chối (LLM_ONLY: không đọc cụm; compiler: coi là hình chữ nhật); chóp đáy tam giác vuông với chân ≠ đỉnh vuông bị từ chối |
> | Thêm | kernel `polygon_from_right_angle_chain` (một thẩm quyền) · bộ đọc "hình thang vuông tại P và Q" · khuôn **T10** (amendment §20) · hai họ compiler `polygon_base_*` (mọi số cạnh, một chuỗi câu lệnh) |
> | Nhãn | 15 hàng ghi trước, oracle độc lập: 7/7 dương + 8/8 âm trên HAI tuyến; red-before 39 đỏ tại `d5287ff7` |
> | Candidate · `CACHE_VERSION` | **`72d6070a…`** (product `4e30a211`; đóng băng LOCAL `f250f5ef`, `--verify` khớp) · **118** (không bump; cache lock verify; ca toạ độ C0 có cụm hình thang vuông trùng byte trước/sau) |
> | Kiểm LOCAL | T3 `FULL_PRODUCT_GATE_PASS` tại `f250f5ef` (worktree tách rời sạch): pytest 7343 passed / 1 skipped, vitest 1040/1040, build, demo, bề mặt sập (`diagnostics/t3_f250f5ef.log`); compiler tự giả định hình chữ nhật: cổng giả định từ chối, khoá bằng test (`handoff.md` §LOCAL) |
> | Năng lực sản phẩm | `right_angle_chain_base` = `foundation_only` (mô hình chưa đo); đa giác đều/góc/lõm/toạ độ-trên-compiler: `ISSUE-ARCH-G05-REMAINING-BASES` |
> | Run | [`general-polygon-base`](evaluation/geometry/runs/general-polygon-base/) (`plan.md`, `report.md`, `handoff.md`) |

> **G04 lăng trụ xiên — run oblique-prism (2026-10-09, Cloud, nhánh `feat/oblique-prism`; 0 model call; LOCAL đã kiểm; đã tích hợp `main` = `a0fdbba4` theo `APPROVAL.md`):**
>
> | Mục | Kết quả |
> |---|---|
> | Trước | 0 dạng G04 có đáp số: cổng giả định chỉ có khuôn lăng trụ ĐỨNG; compiler lăng trụ tam giác bỏ qua `lateral_structure` |
> | Thêm | khuôn **T9** (amendment §19, dùng chung LLM_ONLY + compiler) · họ compiler thứ bảy `oblique_prism_volume` (đáy trên = `translate` do kernel tính, chiều cao = khoảng cách tới mặt đáy) |
> | Miền | đáy tam giác vuông / chữ nhật / vuông, `T F ⊥ (đáy)` với F một đỉnh đáy, chiều cao hữu tỉ (trực tiếp hoặc từ cạnh bên); góc nghiêng, chân ở trung điểm/trọng tâm ⇒ từ chối (`ISSUE-ARCH-OBLIQUE-PRISM-FOOT-VOCABULARY`) |
> | Nhãn | 16 hàng ghi trước, oracle độc lập: 6/6 dương + 10/10 âm khớp trên HAI tuyến; red-before 39 đỏ tại `ba995887` |
> | Candidate · `CACHE_VERSION` | **`02ce5e1e…`** (product `0fe4edc5`; đóng băng LOCAL `75c24394`, `--verify` khớp) · **118** (không bump; 49/49 fixture trùng byte; cache lock verify) |
> | Kiểm LOCAL | T3 `FULL_PRODUCT_GATE_PASS` tại `75c24394` (worktree tách rời sạch): pytest 7290 passed / 1 skipped, vitest 1040/1040, build, demo, bề mặt sập (`diagnostics/t3_75c24394.log`) |
> | Năng lực sản phẩm | `oblique_prism` = `foundation_only` (mô hình chưa đo) |
> | Run | [`oblique-prism`](evaluation/geometry/runs/oblique-prism/) (`plan.md`, `report.md`, `handoff.md`) |

> **Dải lớp học trên điện thoại — run classroom-band-fit (2026-10-09, máy local; đo `6a1801e7` lần 3, worktree tách rời sạch; chờ review người):**
>
> | Mục | Kết quả |
> |---|---|
> | Nguyên nhân | ngang thấp: hàng trên một dòng ép tên bài về 0 px, nhóm công cụ còn `flex-wrap` nên bốn nút xếp dọc; dọc 360 px: mỗi mục dải lớp một dòng; ngân sách chiều cao (sàn canvas 320 px, chạm 44 px) không chứa nổi một dòng dải lớp riêng ở 640×360 · 844×340 · 360×640 |
> | Sửa | tên bài `min-width: 4rem`; công cụ và nút quay lại không co/không xuống dòng; màn chật: dải lớp gọn thành chip trạng thái (`NhomLop` + `LiveClassStrip tomTat`), chạm mở dải đầy đủ — lựa chọn của người dùng; màn rộng và mô phỏng không lớp giữ nguyên |
> | Trình duyệt | dải lớp 3 vai × 8 khổ 24/24 (trước 9/24); không dải lớp 55/56 như trước; Tier-A 8/8 một lượt; W02 16/16, W04 24/24, W05 23/24 (một trang không tải) |
> | Còn lại | ở 640–667 px ngang chip chỉ hiện chấm màu + «…» (quyết H-3); giơ tay hai chạm trên màn chật |
> | Candidate · `CACHE_VERSION` | **`7f3f0423…`** (cây đo không đổi; product `45f5a7f0`) · **118** (không bump) |
> | Run | [`classroom-band-fit`](evaluation/geometry/runs/classroom-band-fit/) (`review.md`, `report.md`, `handoff.md`) |

> **Nghiệm thu cuối — run final-acceptance (2026-10-09, máy local; không sửa sản phẩm, 0 model call):**
>
> | Mục | Kết quả |
> |---|---|
> | Danh tính | candidate `7f3f0423…` `--verify` khớp; `CACHE_VERSION` 118; `LLM_ONLY`; ngoài `docs/` từ `95a56a17` chỉ dời `product_commit_sha` của manifest Tier-A ⇒ Tier-A 8/8 + T3 của phone-landscape-layout còn hiệu lực |
> | Dải lớp học trên điện thoại | lỗi thật, **có từ `main`**: nhánh 11/24, `main` 5/24, không hồi quy — `ISSUE-ARCH-CLASSROOM-BAND-CROWDS-PHONE-TOP-ROW` (OPEN) |
> | E-R6 / F-R7 | chạm giả lập 8/8 (hỗ trợ); thao tác tay vẫn chờ người dùng |
> | UX debt chấp nhận tạm | bảng nổi che canvas khi ngang; nhãn rời canvas sau cú xoay ở màn thấp; header/thanh công cụ mobile — vẫn OPEN |
> | Run | [`final-acceptance`](evaluation/geometry/runs/final-acceptance/) (`review.md`, `report.md`, `handoff.md`) |

> **Điện thoại ngang + 360 px + nghiệm thu cuối — run phone-landscape-layout (2026-10-08/09, máy local; đo `221ec0a0` lần 3, worktree tách rời sạch; chờ review người):**
>
> | Mục | Kết quả |
> |---|---|
> | Nguyên nhân | 844×390: canvas ở sàn 320 px + thanh phát dưới canvas tràn khung 37 px; 667×375 dùng bố cục khổ hẹp khi nằm ngang; 360×640: ba nút phát xuống ba hàng |
> | Sửa | ngang thấp: thanh điều khiển thành cột 10rem cạnh canvas (canvas giữ chiều cao ⇒ hình giữ cỡ; sàn 320 px giữ), ≤ 48rem dùng bố cục rộng; 360 px: ba nút một hàng |
> | Trình duyệt (8 họ × 7 khổ) | điện thoại/ngang 55/56 (trước 15/40 + 0/8; còn ca xoay màn thấp có từ trước); Tier-A 8/8 một lượt; W02 16/16, W04 24/24, W05 24/24, occlusion pass, phát lại pass |
> | Candidate · `CACHE_VERSION` | **`7f3f0423…`** (cây đo không đổi; product `95a56a17`) · **118** (không bump) |
> | Run | [`phone-landscape-layout`](evaluation/geometry/runs/phone-landscape-layout/) (`review.md`, `report.md`, `handoff.md`) |

> **D5 — canvas vừa hình trên điện thoại — run mobile-canvas-fit (2026-10-08, máy local; đo `90921f53`, worktree tách rời sạch; chờ review người):**
>
> | Mục | Kết quả |
> |---|---|
> | Nguyên nhân | canvas lấy trọn chiều cao khả dụng, camera vừa hình theo bề ngang trên điện thoại dọc ⇒ dải trắng trên/dưới; bảng chảy dưới thanh sát đáy ⇒ mở bảng là cuộn, hình rời khung |
> | Sửa | khổ hẹp ≤ 48rem: canvas = rộng × tỉ lệ hình (`caoKhungVuaHinh`, `tiLeKhungHinh`), ≤ phần khả dụng, ≥ 320 px; hình ràng theo chiều cao giữ nguyên; desktop không đổi; bảng bước giữ bước đang xem trong thân bảng |
> | Trình duyệt (8 họ) | D5 39/40 (trước 18/40; còn một ca xoay có từ trước); 390×844 canvas 519 → 320–485 px; W02 16/16, W04 24/24, W05 24/24, occlusion pass, phát lại 16/16; suite 7/8 + chạy lại bước đỏ (kỳ vọng cũ của bộ đo) PASS |
> | Candidate · `CACHE_VERSION` | **`7f3f0423…`** (cây đo không đổi; product `c9bcdcdb`) · **118** (không bump) |
> | Run | [`mobile-canvas-fit`](evaluation/geometry/runs/mobile-canvas-fit/) (`review.md`, `report.md`, `handoff.md`) |

> **Dọn tài liệu + tên — run docs-cleanup (2026-10-08, máy local; chỉ test/CSS chết/tài liệu, không đổi hành vi):**
>
> | Mục | Kết quả |
> |---|---|
> | Tên test | 123 hàm pytest bỏ mã lượt (`test_w17_…` → `test_…`), 74 tiêu đề vitest + 44 node:test bỏ thẻ; bộ chọn `-k wNN` trong tài liệu sống → đường dẫn file; commit riêng `a993aa8f`; bảng ở `evaluation/RUN_NAMING.md` |
> | `docs/legacy/` | 42 → 15 file: xoá 26 (plan/spec Superpowers M9–M17, W13; tài liệu chuyển đề; REPOSITORY_MAP; RULES_v0.3), thiết kế + kế hoạch route Semantic Program → `legacy/architecture/`, `CUBOID_CUBE_CONTRACT_DECISION.md` về `architecture/` (mã còn cài đúng nó) |
> | Hướng dẫn | kế hoạch/spec của skill: thiết kế ⇒ `docs/architecture/`, kế hoạch ⇒ `plan.md` của run (AGENTS §4, `docs/README.md` §8) |
> | Tàn dư Tin học | 12 lớp `geo3d-*` chết gỡ; còn `SamplePreview`/`threeD`/`specDrift` và prompt + IR (sáu prompt không loader) — hai issue `ISSUE-ARCH-*-INFORMATICS-*` |
> | Candidate · `CACHE_VERSION` | **`7f3f042309dd1c54…`** (product `f967ba24`, 102 file) · **118** (bump do refusal envelope đổi) |
> | Run | [`docs-cleanup`](evaluation/geometry/runs/docs-cleanup/) (`plan.md`, `report.md`, `handoff.md`, `inventory.md`, hai manifest độc lập) |

> **Tổ chức tài liệu cuối — lần report organization đã hợp nhất vào docs-cleanup (2026-10-08, không đổi nội dung bằng chứng):** 167/167 report
> có mapping từng file; 33 report về package artifact, 123 report vào `evaluation/reports/`, 11 ngoại lệ path-bound
> ở gốc; 167/167 blob giữ nguyên, catalog/link/consumer được cập nhật. Duyệt hình vẫn NOT_APPROVED.

> **Dọn kho: gỡ phần Tin học hết vai trò + chuẩn hoá tên — run repo-cleanup (2026-10-08, máy local; chỉ tài liệu/mã chết, không đổi hành vi):**
>
> | Mục | Kết quả |
> |---|---|
> | Gỡ | 132 file: bộ đánh giá `app/evaluation/`, `POST /api/explain`, 42 fixture + oracle thuật toán, 9 script một lần, 26 file engine/view Tin học ở `frontend/src`, 42 runner trình duyệt của danh mục Tin học; 325 selector CSS chết; 8 script `test:domain:*` chết — bằng chứng từng file: `runs/repo-cleanup/inventory.json` |
> | Chuyển sang ca hình học | "runner ghi model" → runner DEV hình học; bộ chọn T0 → `domains/geometry`/`semantic`; SEALED còn consumer giữ, pin M17 thuần Tin học đã gỡ ở cleanup tiếp nối; `/api/explain` khoá 404 |
> | Đổi tên | 29 file + gộp hai test pin + một lớp, commit riêng `67e11671` — bảng ở `evaluation/RUN_NAMING.md` |
> | Còn lại có lý do | prompt Tin học + từ vựng container của IR (băm bề mặt mô hình, IR cấm đổi) · vỏ `SamplePreview`/`threeD`/`specDrift`, 9 lớp `geo3d-*` chết — `ISSUE-ARCH-INFORMATICS-MODEL-SURFACE-AND-IR-VOCABULARY`, `ISSUE-ARCH-SHELL-INFORMATICS-RESIDUE` |
> | Candidate · `CACHE_VERSION` | `e1927f84…` → **`b4a33205…`** (product `be4b8287`, 102 file) · **117** (không bump: khoá danh tính cache khớp nguyên) |
> | Run | [`repo-cleanup`](evaluation/geometry/runs/repo-cleanup/) (`report.md`, `handoff.md`, `inventory.json`) |

> **Kích thước chính xác + chụp ảnh tại nguồn + chuẩn hoá tên — run exact-dimensions (2026-10-07/08, máy local; chờ review người):**
>
> | Mục | Kết quả |
> |---|---|
> | Miền mới | chóp tam giác đều với cạnh đáy + chiều cao hữu tỉ/phân số/thập phân, cạnh đáy + cạnh bên, tứ diện đều cạnh hữu tỉ — phục vụ trên route (b=6, h=4 → 12√3; tứ diện a=6 → 18√2); ca căn cũ trùng byte; vẫn từ chối: thiếu/mâu thuẫn/suy biến, kích thước chữ, tổng căn |
> | Biểu diễn | toạ độ chương trình = khung affine ℚ³; độ dài từ ma trận Gram hữu tỉ G suy từ sáu cạnh của đề (`geometry/metric.py`, `assumption_gate.do_luong_cua`); G = I ⇒ biểu thức cũ nguyên byte; renderer ánh xạ khung → không gian một lần (`scene3d-chart.ts`) |
> | Lỗi tìm ra | bộ đọc độ dài lấy vế đầu của biểu thức ("4 + 1" từng phục vụ V = 16) — sửa, `CACHE_VERSION` 117 |
> | Trình duyệt | họ chóp tam giác đều: suite 7/7, điều khiển cảnh 2/2, bảng 3/3, tập trung 3/3, occlusion pass, phát lại 2/2; 3 lần đo — lần 1–2 đỏ vì lỗi BỘ ĐO (khung không trực giao), chỉ chạy lại bước đỏ |
> | Ảnh (cùng họ, cùng bước) | tạo 109 → **15** (runner 103 → 11; xoá sau chụp 52 → 0), quyết trước khi chụp (`capture-policy.mjs`) — `runs/exact-dimensions/capture_counts.json` |
> | Tên | 11 tệp/thư mục đổi tên ở commit riêng `0ed6332f`; một tài liệu sống `evaluation/RUN_NAMING.md` |
> | Candidate · `CACHE_VERSION` | `92c9e198…` → **`e1927f84…`** (product `ed3ae208`) · 116 → **117** |
> | Run | [`exact-dimensions`](evaluation/geometry/runs/exact-dimensions/) (`review.md`, `report.md`, `handoff.md`) |

> **Chóp tam giác đều + tứ diện đều (miền ℚ³) — regular-triangular-pyramid-w01 (đo `1bb11018`, worktree tách rời sạch; chờ review người):**
>
> | Mục | Kết quả |
> |---|---|
> | Họ mới | chóp tam giác đều + tứ diện đều trên route sản phẩm, miền khai: cạnh đáy² ∈ {2k², 6k²}, chiều cao² = 3t²; ngoài miền từ chối `TEMPLATE_NOT_REPRESENTABLE T8`; năng lực `foundation_only` |
> | Backend | độ dài nguồn đọc căn (`segment_relation`), khuôn T8 (`assumption_gate`, thẩm quyền `shape_constraint.la_chop_tam_giac_deu`), trọng tâm suy ra (`formation`, `construction_binding`), so khớp chính xác cho căn |
> | Giao diện | D1–D4 sửa; D5 chờ quyết định (`ISSUE-ARCH-MOBILE-CANVAS-WHITESPACE-AND-PANEL-SCROLL`); D6 giữ; xoay hiển thị đáy nghiêng; khung nhìn ban đầu nay ở giữa mọi họ (`diemVuaKhung`, sau lượt đo 1) |
> | Trình duyệt `1bb11018` | suite 8/8, 16/16 + 31/31 âm; W02 16/16 (chạy lại riêng); W04 24/24 (cross_section chạy lại riêng); W05 24/24; occlusion pass; phát lại 16/16; 3 lần đo, chỉ lần 3 dùng |
> | Ảnh | 492 giữ / 358 tỉa (W5: 767 cho bảy họ) — `TEST_TIERS.md` luật "chụp để kiểm, lưu có chọn" |
> | Candidate · `CACHE_VERSION` | `5e1c0639…` → **`92c9e198…`** (product `1e90ca0e`, hai lần đóng băng) · **116** (bump: hai envelope thiết diện đổi nhãn bước) |
> | Run | [`regular-triangular-pyramid-w01`](evaluation/geometry/runs/regular-triangular-pyramid-w01/) (`REVIEW.md`, `REPORT.md`, `HANDOFF.md`) |

> **Chế độ tập trung + bộ đọc chuỗi bằng nhau — regular-square-pyramid-w05 (đo `f01df0e5`, worktree tách rời sạch; chờ review người):**
>
> | Mục | Kết quả |
> |---|---|
> | Không gian mô phỏng | cảnh 3D lấp trang, không thanh trên toàn cục; «← trang trước» · tên bài · «Đề bài» · menu «Khám phá»/«Hiển thị»/«Thêm»; toàn màn hình tuỳ chọn; trang vừa một màn ở desktop/màn thấp, mobile cuộn |
> | Bỏ lặp | thẻ lời giải dưới thanh phát gỡ — đại lượng ở «Đại lượng», công thức + nguồn ở ô soi, chú giải màu trong «Hiển thị» |
> | Backend | `segment_relation` đọc `SA = SB = SC = SD = 3` cho mọi đoạn; `R2_L1` phục vụ `V = 16/3` (`ISSUE-ARCH-SOURCE-LENGTH-CHAINED-EQUALITY` khép) |
> | Trình duyệt `f01df0e5` | suite 7/7, 14/14; W2 14/14; W4 21/21; **W05 21/21**; occlusion pass (4 cảnh chờ duyệt, U2); phát lại 14/14; 4 lần đo, chỉ lần 4 dùng |
> | Candidate · `CACHE_VERSION` | `8a27a58b…` → **`5e1c0639…`** (product `82225a7b`, hai lần đóng băng) · **115** (không bump) |
> | Run | [`regular-square-pyramid-w05`](evaluation/geometry/runs/regular-square-pyramid-w05/) (`REVIEW.md`, `REPORT.md`, `HANDOFF.md`) |

> **Giao diện mô phỏng dùng chung — regular-square-pyramid-w04 (đo `103494c4`, worktree tách rời sạch; chờ review người):**
>
> | Mục | Kết quả |
> |---|---|
> | Bảng thông tin | ô soi, Xem đề, Thành phần, Đại lượng, Các bước dựng: một cơ chế `BangNoi` — nổi, kéo tiêu đề, phím, Escape, về mặc định, thu gọn; không cột, không đổi canvas/camera/bước; nhiều bảng cùng mở; mobile là tấm trong dòng chảy (H-W2-3 khép) |
> | Bố cục | canvas theo chiều cao khả dụng, thanh phát sát đáy; «Bước n/N» trong thanh; mô tả bước trong «Các bước dựng»; canvas WebGL theo khung |
> | Chọn thành phần | bấm thẳng lên hình; cây «Thành phần» theo bước, nhóm thu gọn mặc định, không lộ vật tương lai |
> | Câu chữ · SM | lời kể theo ký hiệu đề (`ten_trong_loi_ke`); SM trên SA nhường nét, chọn SM chỉ sáng khúc S–M |
> | Trình duyệt `103494c4` | suite 7/7, 14/14 lượt dương; đầu dò W2 14/14; đầu dò W4 21/21 (7 họ × desktop/màn thấp/mobile); occlusion 0 lỗi (4 cảnh chờ duyệt, U2); phát lại pass; 4 lần đo, chỉ lần 4 dùng |
> | Candidate · `CACHE_VERSION` | `5dec4572…` → **`8a27a58b…`** (product `53e4bec5`, ba lần đóng băng) · 114 → **115** (36 row v114 vẫn HIT) |
> | Run | [`regular-square-pyramid-w04`](evaluation/geometry/runs/regular-square-pyramid-w04/) (`REVIEW.md`, `REPORT.md`, `HANDOFF.md`) |

> **Nghiệm thu local W2 + hai bản sửa — regular-square-pyramid-w03 (đo `a5d233ce`, worktree tách rời sạch; chờ review người):**
>
> | Mục | Kết quả |
> |---|---|
> | W2 nguyên trạng `fe68b4ca` | T3 `FULL_PRODUCT_GATE_PASS`; cổng danh tính xanh; test node đường dẫn có dấu cách qua; 14/14 lượt dương xanh trọn — `camera_settled_rotated_neutral` và `causal_restore` thiết diện đỏ trên cloud là lỗi môi trường |
> | H-W2-4 (lỗi) | mặt phẳng phụ chỉ để đo không mở bước dựng (`measurementOnlyPlanes`); miễn trừ W2 ở ba cổng đã gỡ; chóp đều 8 bước |
> | H-W2-2 (lỗi) | đoạn đề hỏi độ dài được dựng trước đáp số (`formation._doan_duoc_hoi`); kỳ vọng W18 `d_kq` khôi phục (đính chính PC1-W2) |
> | H-W2-3, H-W2-5 | lựa chọn trình bày, chưa đổi; đề nghị giữ — chưa được người dùng chấp nhận |
> | Trình duyệt `a5d233ce` | suite 7/7, 14/14 lượt dương xanh; đầu dò W2 14/14; occlusion 0 lỗi (4 cảnh chờ duyệt, U2); phát lại PASS không miễn trừ; 68 crop, 0 bất đồng |
> | Candidate · `CACHE_VERSION` | `d3de9c44…` → **`5dec4572…`** (product `45beaed3`) · 113 → **114** (13 row v113 vẫn HIT) |
> | Run | [`regular-square-pyramid-w03`](evaluation/geometry/runs/regular-square-pyramid-w03/) (`REVIEW.md`, `REPORT.md`, `HANDOFF.md`) |

> **Khép phần sư phạm của chóp đều — regular-square-pyramid-w02 (triển khai trên cloud, đo `94200b50`; nghiệm thu local ở W3):**
>
> | Mục | Kết quả |
> |---|---|
> | Kết luận | **`CLOUD_IMPLEMENTATION_COMPLETE_LOCAL_VERIFICATION_REQUIRED`** — HANDOFF.md §2 (kiểm còn phải chạy ở máy local), §3 (H-W2-1 chặn merge) |
> | Nhãn theo formation state | nhãn đoạn chỉ khi đoạn mang nó đã dựng (đoạn, cạnh đa giác, cạnh khối), ở mọi chế độ; nhãn hợp lệ thiếu chỗ phân biệt được |
> | Bảng nổi «Các bước dựng» | nổi trên khung, kéo bằng tiêu đề, phím, về mặc định, kẹp khi kéo/đổi cỡ; không đổi cỡ canvas/camera; mobile trong dòng chảy, thu gọn |
> | SO + chiều cao | bước bổ sung dựng SO khi đề nói "đều" và tâm dựng từ hai đường chéo; chiều cao của công thức chọn theo quan hệ ⊥ kiểm chính xác (gỡ luật giá trị W1) |
> | Hình phụ · lưới | AC, BD ẩn sau khi có O; mặt phẳng chỉ để đo ẩn; chip «Hình phụ», «Lưới» (mặc định tắt) |
> | Trình duyệt | đầu dò W2 **14/14** (7 họ × desktop + mobile: kéo, phím, đổi cỡ, về mặc định, Escape; canvas/camera không đổi; nhãn theo bước khớp oracle); từ chối 54/54, phục vụ 6/6, chọn 68/68, ngăn 14/14; occlusion 0 lỗi; phát 14/14; 68 crop, 0 bất đồng oracle. Đỏ chỉ ở hai cổng nghi môi trường, cũng đỏ ở W1 head trên cloud: `camera_settled_rotated_neutral` (6 desktop), `causal_restore` thiết diện (desktop + mobile) — chạy lại ở máy local |
> | Candidate · `CACHE_VERSION` | `5234c37e…` → **`d3de9c44…`** (bốn lần đóng băng cùng tree hash; product commit `70665542`) · 112 → **113** (13 row v112 vẫn HIT; sáu họ cũ trùng byte) |
> | Run | [`regular-square-pyramid-w02`](evaluation/geometry/runs/regular-square-pyramid-w02/) (`REPORT.md`, `HANDOFF.md`) |

> **Chóp tứ giác đều + chín chỉnh sửa giao diện §0.1 — regular-square-pyramid-w01 (đo `ed37f9fa`, worktree tách rời sạch; chưa có review người):**
>
> | Mục | Kết quả |
> |---|---|
> | Kết luận | **`READY_FOR_HUMAN_VISUAL_REVIEW`** — mọi cổng tự động đạt; điều kiện merge: người duyệt H-W1-1 (`HANDOFF.md` §1) |
> | Chóp tứ giác đều | bộ đọc "đều"/cạnh đáy/cạnh bên/trung đoạn/tâm đáy; khuôn C1 T7 (cạnh bên cả từ `SA = 3`); tâm O theo danh tính; chiều cao đo được của thể tích; corpus đăng ký trước **24/24** (hai lớp: 17 + 7) |
> | Giao diện §0.1 | card Kết quả ẩn khi thu gọn · ngăn «Đại lượng» · panel «Các bước dựng» (desktop cạnh khung, mobile dưới điều khiển) · gỡ dải «Đang dựng» · ghi vị trí cuộn mỗi ảnh |
> | Trình duyệt · occlusion · playback | **7/7 họ**: 14/14 dương, 54/54 âm, 6/6 phục vụ, chọn đại lượng 68/68, ngăn + panel 14/14 · occlusion 0 lỗi (bốn cảnh W14 chờ người) · playback 14/14 · 68 crop, 0 bất đồng |
> | T3 từ đường dẫn CÓ dấu cách (`7b99ccaa`) | **PASS** — pytest 7131/0 (1 skipped, 2 deselected) · vitest 1071/1071 · build · demo 5/5 · bề mặt sập 6/6; cổng danh tính, audit tài liệu, harness node đạt |
> | Lỗi tìm ra | công thức thể tích mất khi có hai ứng viên chiều cao (`98e2b8f7`) · cổng phạm vi từ chối "độ dài" (`9d66c603`, đóng `ISSUE-ARCH-SCOPE-GATE-LENGTH-CLUE`) · tự rà soát cuối: T7 bỏ qua cạnh bên `SA = 3` (`ad7172ab`; lớp nhãn R2 7/7) |
> | Candidate · `CACHE_VERSION` | `b2d4187a…` → `4629c3e8…` (trung gian, `de5b2331`) → **`5234c37e…`** (`ad7172ab`, sau tự rà soát) · 111 → **112** (`de5b2331`, chứng minh theo hàng; bản sửa giữ 112); vân tay bề mặt mô hình không đổi |
> | Run | [`regular-square-pyramid-w01`](evaluation/geometry/runs/regular-square-pyramid-w01/) (`REPORT.md`, `HANDOFF.md`) |

> **Gói duyệt hình + tích hợp — run `cuboid-merge` (2026-10-05; chỉ tài liệu; đã duyệt, đã merge và push):**
>
> | Mục | Kết quả |
> |---|---|
> | Kết luận | **`MERGED_AND_PUSHED`** — người dùng ACCEPTED A–E, F (F1–F5 hoãn, vẫn mở) cho [`REVIEW.md`](evaluation/geometry/runs/cuboid-merge/REVIEW.md) ([`APPROVAL.md`](evaluation/geometry/runs/cuboid-merge/APPROVAL.md)); `main` fast-forward `a9492ee9` → `c282a5f3`, push thường, nhánh local đã xoá (không có trên remote) |
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
