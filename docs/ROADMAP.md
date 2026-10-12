# ROADMAP.md — Lộ trình nghiên cứu và phát triển AlgoSim

> **Tài liệu Canonical cho Roadmap của đề tài Khóa luận.**
> Mọi bước tiếp theo phải bám sát thứ tự ưu tiên P0 → P6.
> Bước hành động tiếp theo duy nhất (Single Canonical Next Action) được khai báo tại Mục 0.

---

## 0. Canonical Next Action

```text
CANONICAL_NEXT_ACTION = HYBRID_QUESTION_LOCAL_GIVENS_INTEGRATION_DECISION
TARGET_NEXT_ACTION_AFTER_WAVE = OCR_AFTER_FAMILY_EXPANSION
```

- **Question-local givens (LOCAL research, 2026-10-12):** product `e1f288ec`, candidate `d4bc2b04…`; cổng chung A/B fail-closed, dữ kiện cùng câu đã khớp vẫn phục vụ. Review 3 Critical + 1 Important đã đóng RED→GREEN; benchmark 30 ca không đổi. Chưa merge/push; LLM_ONLY/cache125/Gemini0. Run [`question-local-givens`](evaluation/geometry/runs/question-local-givens/report.md). Sau quyết định tích hợp, đề xuất lát nhiều bước dựng mặt phẳng qua điểm song song/vuông góc mặt phẳng đã có rồi dựng thiết diện; chưa triển khai, cần chốt tiền điều kiện bảo đảm mặt phẳng duy nhất. B27/B28/DSL/orbit P1 giữ nguyên.

- **Main integration (LOCAL, 2026-10-12):** fast-forward `a6e27a78` → `22edf7ff`; candidate `d1410731…` verify; T3 PASS (backend 8675, frontend 1053); benchmark 30 ca byte-identical 19/9/0/2. Không push. Run [`hybrid-main-integration`](evaluation/geometry/runs/hybrid-main-integration/report.md). Người dùng đã giao bước kế tiếp: fail-closed question-local givens trên research branch mới, không mở scoped state/schema/provider mới; B27/B28/DSL/orbit P1 vẫn ngoài phạm vi.

- **S1 + S2 hardening (LOCAL, 2026-10-12, nhánh `research/hybrid-semantic-hardening` — con của tip đã review `9cfd0fca`; chưa merge/push; run [`hybrid-semantic-hardening`](evaluation/geometry/runs/hybrid-semantic-hardening/report.md)):**
  - S1: mỗi `ask_*` phải có cụm đối tượng (văn phạm đóng theo hàm) gọi đúng toán hạng, được hỏi nguyên vẹn; giá trị neo phải là phép bằng; bộ phân tích vai trò mệnh đề nhận thêm mục tiêu / giả định / không khẳng định. Probe phần dư: 1/79 còn phục vụ (cách đọc đúng). Review độc lập: sửa 18 từ chối sai mới và 1 phục vụ sai mới.
  - S2: giao tuyến "vô hình" là lỗi tầng trình bày — đoạn cố định ±6 đâm ra sau camera trong cảnh cỡ 1; nay `doanDuongThang` theo cỡ cảnh. Harness áp `veKhongGian` như sản phẩm.
  - Còn mở: `ISSUE-ARCH-HYBRID-QUESTION-LOCAL-GIVENS` (dữ kiện cục bộ trong câu hỏi) — slice riêng, cần duyệt. M4 chỉ kiểm, không đổi hợp đồng.
  - Việc kế tiếp: người dùng quyết tích hợp A (baseline) / B (hardening) theo [`handoff.md`](evaluation/geometry/runs/hybrid-semantic-hardening/handoff.md). DSL vẫn HOLD.

- **Kiểm toán độc lập S0 + lát thiết diện, kiểm Scene3D (LOCAL, 2026-10-12, cùng nhánh nghiên cứu, chưa merge/push; run [`hybrid-slice-review`](evaluation/geometry/runs/hybrid-slice-review/report.md)):**
  - Review: Critical 2, Important 3, Minor 4 cùng các phát hiện tái kiểm. Đã đóng hết bằng RED → GREEN (`5136127a` → `b3e946e9`), trừ M4. Thiết diện khớp oracle độc lập chính xác.
  - Scene3D: harness dùng scene Hybrid thật, không phải UI sản phẩm. Thiết diện hiện đúng; orbit/zoom/reset ổn định. Giao tuyến không hiện pixel nào (`ISSUE-ARCH-SCENE3D-INTERSECTION-LINE-INVISIBLE`).
  - Rủi ro còn lại đã khai: cổng nguồn còn phục vụ sai ở nhóm A–D (`ISSUE-ARCH-HYBRID-GATE-RESIDUAL-FALSE-SERVES`). A–C có sẵn trên `main`; D là bề mặt mới.
  - GO/NO-GO: GO cho fast-forward `main` khi đã khai rủi ro còn lại; NO-GO cho việc bật Hybrid trong sản phẩm hoặc chạy pilot live.
  - Việc kế tiếp: người dùng quyết tích hợp theo [`handoff.md`](evaluation/geometry/runs/hybrid-slice-review/handoff.md). Wave đề xuất sau đó: buộc toán hạng câu hỏi vào quote (đóng nhóm C, D).
  - Spike DSL gọn (nhánh `research/compact-geometry-dsl`, run `compact-geometry-dsl-spike`, không thuộc nhánh này): kết luận nằm ở báo cáo của nhánh đó; không đổi lược đồ hay bề mặt provider.

- **S0 + lát thiết diện (LOCAL, 2026-10-11, nhánh nghiên cứu, chưa merge/push):**
  - **S0** ([`hybrid-gate-clause-role-fix`](evaluation/geometry/runs/hybrid-gate-clause-role-fix/report.md)) sửa lỗi CRITICAL của cổng chung A/B:
    - vai trò mệnh đề đọc tại vị từ trong quote;
    - `ask_*` phải là câu hỏi;
    - T3 PASS.
  - **Lát 1** ([`hybrid-section-slice`](evaluation/geometry/runs/hybrid-section-slice/report.md)):
    - Hybrid dựng được thiết diện, giao tuyến và diện tích thiết diện qua IR chung có sẵn;
    - Registry tăng từ 27 lên 30 hàm, bề mặt provider A/B đổi có chủ đích;
    - benchmark không đổi.
  - Việc kế tiếp: người dùng review và quyết định tích hợp. Lát 2 (dựng song song) và lát 3 (cách diễn đạt) chưa duyệt.

- **Kiểm toán năng lực mô phỏng Hybrid (LOCAL, 2026-10-11, nhánh `research/hybrid-simulation-capability-audit`, run [`hybrid-simulation-capability-audit`](evaluation/geometry/runs/hybrid-simulation-capability-audit/report.md)):**
  - Kết luận chính: thiết diện, giao tuyến, mặt ⊥ đường, chia đoạn và khối cong đã được engine/IR/Scene3D chung dựng (probe thực thi được). Hybrid chỉ thiếu cửa vào (Registry + Typed Facts + planner + ngữ pháp nguồn).
  - Primitive thật sự thiếu: dựng đỉnh từ góc cho trước; trọng tâm đa giác > 3 đỉnh.
  - Lỗi CRITICAL `ISSUE-ARCH-GATE-CLAUSE-ROLE-INSIDE-QUOTE` (cổng chung A/B) phải sửa trước (S0).
  - Đề xuất: S0 → lát "thiết diện + giao tuyến" → song song → độ rộng cách diễn đạt.
  - B27/B28/tìm kiếm tổng quát vẫn hoãn. Việc kế tiếp: người dùng quyết S0 và lát đề xuất.

- **Hybrid B slice 1 ĐÃ TÍCH HỢP `main` (2026-10-11, fast-forward `548066a8` → `a246dd19`, run [`hybrid-slice1-main-integration`](evaluation/geometry/runs/hybrid-slice1-main-integration/report.md)):**
  - B26 (khoảng cách điểm–đường qua chân vuông góc phụ) cùng hai bản sửa Important của kiểm toán độc lập; T3 PASS trên `main`.
  - Trạng thái remote: tra `git log -1 origin/main`, tài liệu này không ghi.
  - **B27 (lát 2, đổi lược đồ Typed Facts) và B28 (từ khoá "tâm") CHƯA được phê duyệt triển khai**; tìm kiếm theo mục tiêu tổng quát cũng chưa.
  - `LLM_ONLY` vẫn mặc định. Chưa có bằng chứng Hybrid B chính xác với Gemini thật.
  - Việc kế tiếp: người dùng chọn ưu tiên. Ứng viên:
    - `ISSUE-ARCH-ASK-GATE-NO-QUESTION-CHECK`;
    - `ISSUE-ARCH-ORBIT-P1-SECTION-SCENE-DOES-NOT-SETTLE` (P1);
    - phê duyệt lát 2 (B27);
    - `ISSUE-ARCH-LINE-SEGMENT-SEMANTIC-DISTINCTION`;
    - giới hạn điểm phụ.

- **Kiểm toán độc lập lát 1 (LOCAL, 2026-10-11):**
  - Không có lỗi Critical; sửa 2 lỗi Important (câu không hỏi thì không trả lời; nhãn phụ tránh H₁/ΔSHD). Benchmark 19/9/0/2 không đổi.
  - Việc kế tiếp: người dùng duyệt fast-forward `main` theo [`hybrid-slice1-review/handoff.md`](evaluation/geometry/runs/hybrid-slice1-review/handoff.md).
  - Lỗ hổng tương tự ở các `ask_*` khác ghi thành `ISSUE-ARCH-ASK-GATE-NO-QUESTION-CHECK` (wave riêng).

- **Goal decomposition slice 1 (LOCAL, 2026-10-11, cùng nhánh nghiên cứu, chưa merge/push):**
  - Người dùng duyệt phương án B, chỉ lát 1. Compiler hiện có dựng điểm phụ (chân vuông góc, DERIVED/AUXILIARY) cho khoảng cách điểm–đường.
  - Benchmark 30 ca: 19/9/0/2 (trước 18/9/0/3); B26 đã phục vụ, 29 ca còn lại không đổi.
  - Không đổi Typed Facts hay bề mặt provider; `LLM_ONLY` vẫn mặc định.
  - Việc kế tiếp: người dùng review [`hybrid-goal-decomposition/report.md`](evaluation/geometry/runs/hybrid-goal-decomposition/report.md). Lát 2 (B27) cần phê duyệt riêng.

- **Hybrid compiler audit (LOCAL, 2026-10-11, nhánh `research/hybrid-compiler-capability-audit`, chưa merge/push):**
  - ADR [`architecture/HYBRID_B_TARGET_ARCHITECTURE_DECISION.md`](architecture/HYBRID_B_TARGET_ARCHITECTURE_DECISION.md): Hybrid B là hướng ưu tiên; A là baseline. Quyết định dựa trên offline, `LLM_ONLY` vẫn mặc định.
  - Benchmark 30 ca: 18 phục vụ đúng, 9 từ chối đúng, 0 phục vụ sai, 3 từ chối sai.
  - Việc kế tiếp: người dùng duyệt phương án B trong
    [`design.md`](evaluation/geometry/runs/hybrid-compiler-capability-audit/design.md), gồm điểm phụ do compiler dựng cho khoảng cách điểm–đường và toán hạng không tên.
  - Tích hợp `main` của expansion đã xong (2026-10-11, `9e3c9789`), nên quyết định `GEOMETRY_LIBRARY_INTEGRATION_APPROVAL_DECISION` đã đóng.

- **Important fixes (LOCAL, 2026-10-11):** review I1–I3 đã sửa trên cùng nhánh
  ([`geometry-library-important-fixes/report.md`](evaluation/geometry/runs/geometry-library-important-fixes/report.md)).
  Việc kế tiếp là quyết định của người dùng về nhánh integration từ main (fast-forward, kế hoạch ở §10 của report);
  trước đó: nghiệm thu hình ảnh, cổng orbit trên môi trường đo được, nguyên nhân test chập chờn.

- **Geometry expansion (LOCAL, 2026-10-11):** hai nhóm đã được người dùng phê duyệt;
  giao điểm đường–đường/đường–mặt và hình chiếu điểm–đường/điểm–mặt trên Registry/Engine chung.
  Nhánh riêng `feat/geometry-library-expansion`, chưa tích hợp; báo cáo/cổng kiểm chứng ở
  [`geometry-library-expansion/report.md`](evaluation/geometry/runs/geometry-library-expansion/report.md).
  Candidate mới không thay candidate A/B đã khóa. Không chạy pilot, merge, push hay đổi default.
  Sau kiểm chứng, review phạm vi đã dựng và giới hạn trước khi chọn lát kế tiếp; OCR vẫn sau mở rộng họ hình.

- **Readiness correction (2026-10-10):** [`hybrid-ab-pilot-readiness/report.md`](evaluation/geometry/runs/hybrid-ab-pilot-readiness/report.md)
  tách object-binding / quan sát cấu hình khỏi chứng minh, khóa SMOKE 24 và FULL 288 riêng, certification fake/network=0.
  Live vẫn NO-GO; người dùng review exact identities và giới hạn prompt estimator trước mọi quyết định chạy. Kết quả hybrid
  cũ giữ nguyên nhưng phải đọc cùng correction layer này; không tuyên bố tỷ lệ lỗi thực bằng 0 hay B tốt hơn A.

- **Quyết định kiến trúc (2026-10-10, người dùng theo ý GVHD):** **Text-to-Geometry Functions là kiến trúc đích**
  ([`architecture/TEXT_TO_GEOMETRY_FUNCTIONS_DECISION.md`](architecture/TEXT_TO_GEOMETRY_FUNCTIONS_DECISION.md), contract
  [`architecture/TEXT_TO_GEOMETRY_FUNCTIONS_CONTRACT.md`](architecture/TEXT_TO_GEOMETRY_FUNCTIONS_CONTRACT.md)). `LLM_ONLY` là legacy: vẫn
  là mặc định sản phẩm, không thêm năng lực mô phỏng mới trên nó. Mọi mở rộng họ hình (§0.2) từ nay làm trên kiến trúc
  mới. Chưa xoá legacy, chưa đổi mặc định (cổng: `MIGRATION_CHECKLIST.md` + nghiệm thu đường AI thật).

- **Việc `hybrid-compiler-selection` (2026-10-10, run [`hybrid-compiler-selection`](evaluation/geometry/runs/hybrid-compiler-selection/),
  LOCAL, cùng nhánh, CHƯA tích hợp, 0 lượt gọi model):** nhánh B thực nghiệm (AI trích dữ kiện có kiểu → planner tất định
  chọn hàm → cùng back end với nhánh A) so offline với nhánh A: parity 58/58, holdout 14/14 khớp tiền đăng ký ở cả hai nhánh;
  không tuyên bố Hybrid tốt hơn, ADR không đổi. Pilot A/B thật P-AB1 đề xuất, chưa chạy (`REAL_MODEL_AB_PROTOCOL.md` của run);
  việc kế tiếp không đổi: người dùng chọn P-FC1, P-AB1 hoặc không chạy.

- **Việc `ai-function-route` (2026-10-10, run [`ai-function-route`](evaluation/geometry/runs/ai-function-route/), LOCAL, nhánh
  `feat/text-to-geometry-functions`, CHƯA tích hợp, 0 lượt gọi model):** adapter Gemini function calling (provider giả),
  cổng nguồn 5 tầng, chuẩn hoá quan hệ có tiền điều kiện, độ dài ký hiệu a, mặt bên ⊥ đáy, trọng tâm, góc hai mặt,
  khoảng cách hai đường; 31/31 ca diễn đạt + mở rộng đăng ký trước, 58/58 qua adapter giả; candidate `168a086e…`.
  Việc kế tiếp: người dùng quyết pilot Gemini có ngân sách (`EXPERIMENT_PROTOCOL_V2.md` của run).

- **Việc `text-to-geometry-functions` (2026-10-10, run [`text-to-geometry-functions`](evaluation/geometry/runs/text-to-geometry-functions/),
  LOCAL, cùng nhánh):** vertical slice đầu tiên — registry 16 hàm, engine bố cục khung affine + Gram, 27/27 fixture.

- **Việc `regular-prisms` (2026-10-09, run [`regular-prisms`](evaluation/geometry/runs/regular-prisms/),
  Cloud + LOCAL, ĐÃ TÍCH HỢP `main` = `9b783cb4`):** lát cắt G05 kế tiếp — lăng trụ tam giác đều và lăng trụ lục giác đều qua
  khuôn T12 + metric khung lăng trụ (amendment §27): 13 đề trước bị từ chối nay phục vụ đúng (C1, Scene3D 12/8/18 và
  6/5/9 có `chart_metric`); 12 biên từ chối; `CACHE_VERSION` 125 (C0 mâu thuẫn served → refused); `foundation_only`;
  candidate `93077b51…` đóng băng LOCAL, kiểm hình trên trình duyệt (`handoff.md` của run); phê duyệt: `APPROVAL.md`
  của run. Việc kế tiếp: người dùng chọn. Còn trong G05: chóp/lăng trụ đều không tên, lăng trụ xiên đáy đều, ngũ giác đều, đáy theo góc, đáy lõm.

- **Việc `regular-hexagonal-pyramid` (2026-10-09, run [`regular-hexagonal-pyramid`](evaluation/geometry/runs/regular-hexagonal-pyramid/),
  Cloud + LOCAL, ĐÃ TÍCH HỢP `main` = `55f51395`):** lát cắt G05 đầu tiên sau Policy A — chóp lục
  giác đều qua khuôn T11 + metric khung (amendment §26): 8 đề trước bị từ chối/phục vụ sai nay phục vụ đúng (C1, Scene3D
  có `chart_metric`); `CACHE_VERSION` 124; `foundation_only`; candidate `cf47dd61…` đóng băng LOCAL, T3 PASS, kiểm hình
  trên trình duyệt (`handoff.md` của run); phê duyệt: `APPROVAL.md` của run. Ứng viên G05 kế tiếp (chưa bắt đầu, người dùng chọn): lăng trụ lục giác đều /
  lăng trụ tam giác đều (ký hiệu lăng trụ + metric lăng trụ, cùng cơ chế).

- **Việc `unnamed-pyramid-vertex-binding` (2026-10-09, run [`unnamed-pyramid-vertex-binding`](evaluation/geometry/runs/unnamed-pyramid-vertex-binding/),
  Cloud + LOCAL, ĐÃ TÍCH HỢP `main` = `32705882`):** nghiên cứu (b) ⇒ người dùng chọn **A**: chặn 21 đề chóp đều không tên
  có tên điểm thiếu toạ độ (12 served → refused, 9 giữ từ chối; amendment §25); `CACHE_VERSION` 123; candidate
  `b13a3ef1…`, T3 PASS; phê duyệt: `APPROVAL.md` của run. 5 đề do chính đề xác định chưa được hỗ trợ (giới hạn năng lực); phương án B hoãn — nâng cấp tuỳ chọn.
  Việc kế tiếp sau tích hợp: quay lại G05.

- **Việc `unnamed-regular-pyramid-grounding` (2026-10-09, run [`unnamed-regular-pyramid-grounding`](evaluation/geometry/runs/unnamed-regular-pyramid-grounding/),
  Cloud + LOCAL, ĐÃ TÍCH HỢP `main` = `2d3c510c`):** chóp đều không tên gắn + kiểm khi đề không gọi tên điểm nào thiếu
  toạ độ (26/47 hàng corpus = nhãn; 4 giá trị sai sửa đúng); `CACHE_VERSION` 122; candidate `d07a92de…`, T3 PASS; phê
  duyệt: `APPROVAL.md` của run. Việc kế tiếp: lượt Cloud RIÊNG phương án (b). Còn mở: đề gọi tên điểm mà không
  toạ độ, không ký hiệu khối — 21 hàng, 3 phục vụ trái nhãn; người dùng đã chọn phương án (b) (kiểm mọi phép gán hữu hạn
  có căn cứ) cho một lượt Cloud RIÊNG sau khi bản này được tích hợp.

- **Việc `c0-whole-solid-reader` (2026-10-09, run [`c0-whole-solid-reader`](evaluation/geometry/runs/c0-whole-solid-reader/),
  Cloud + LOCAL, ĐÃ TÍCH HỢP `main` = `81ff8899`):** bộ đọc nhận "có đỉnh S và đáy ABCD" và "chóp đều S.ABCD" như ký hiệu
  chuẩn; phủ định không là tiền đề; `CACHE_VERSION` 121; candidate `c3f83399…`, T3 PASS; phê duyệt: `APPROVAL.md` của run.
  Việc kế tiếp: người dùng chọn (hai issue chóp đều không tên còn mở; họ hình tiếp theo theo §0.2, G06 chưa bắt đầu).
  `ISSUE-ARCH-C0-WHOLE-SOLID-CLAIMS-NOT-READ` thu hẹp (còn chóp đều không tên); mở
  `ISSUE-ARCH-UNNAMED-REGULAR-PYRAMID-OUTSIDE-REFUSAL-ZONE`.

- **Việc `c0-whole-solid-grounding` (2026-10-09, run [`c0-whole-solid-grounding`](evaluation/geometry/runs/c0-whole-solid-grounding/),
  Cloud + LOCAL, ĐÃ TÍCH HỢP `main` = `11be6092`):** đóng `ISSUE-ARCH-C0-WHOLE-SOLID-RELATIONS-NOT-CHECKED` (amendment
  §22; 15 hàng nhãn served → refused); `CACHE_VERSION` 120; candidate `8c4c0128…`, T3 PASS; phê duyệt: `APPROVAL.md` của
  run. Còn mở: `ISSUE-ARCH-C0-WHOLE-SOLID-CLAIMS-NOT-READ` (ba cách viết chóp đều bộ đọc chưa nhận ⇒ an toàn C0 chưa trọn).
  Việc kế tiếp: người dùng chọn họ hình tiếp theo theo §0.2 (G06 chưa bắt đầu), rồi OCR.

- **Việc `geometry-grounding-safety` (2026-10-09, run [`geometry-grounding-safety`](evaluation/geometry/runs/geometry-grounding-safety/),
  Cloud + LOCAL, ĐÃ TÍCH HỢP `main` = `47d05f22`):** đóng `ISSUE-ARCH-C0-SHAPE-TEXT-NOT-CHECKED-AGAINST-COORDINATES` và
  `ISSUE-ARCH-COMPILER-UNTAGGED-RECTANGLE-ASSUMPTION`; `CACHE_VERSION` 119; candidate `bbfa5b0d…`, T3 PASS; phê duyệt:
  `APPROVAL.md` của run. Còn mở: `ISSUE-ARCH-C0-WHOLE-SOLID-RELATIONS-NOT-CHECKED`. Việc kế tiếp: người dùng chọn họ hình
  tiếp theo theo §0.2 (G06 chưa bắt đầu), rồi OCR.

- **Việc `general-polygon-base` (2026-10-09, run [`general-polygon-base`](evaluation/geometry/runs/general-polygon-base/), Cloud +
  LOCAL, ĐÃ TÍCH HỢP `main` = `9666b861`):** G05 miền hẹp — đáy lồi xác định bởi chuỗi góc vuông (hình thang vuông, tam giác
  vuông với chân bất kỳ, n cạnh) cho chóp và lăng trụ đứng, qua bộ đọc + khuôn T10 (hai tuyến) và hai họ compiler
  `polygon_base_*`; `CACHE_VERSION` 118, candidate `72d6070a…`, T3 PASS; `foundation_only`. Phê duyệt: `APPROVAL.md` của
  run. G05 CHƯA khép toàn họ (`ISSUE-ARCH-G05-REMAINING-BASES`). Việc kế tiếp: người dùng chọn họ tiếp theo theo §0.2 (G06
  chưa bắt đầu), rồi OCR.

- **Việc `oblique-prism` (2026-10-09, run [`oblique-prism`](evaluation/geometry/runs/oblique-prism/), Cloud + LOCAL,
  ĐÃ TÍCH HỢP `main` = `a0fdbba4`):** G04 lăng trụ xiên trên kiến trúc sẵn có — khuôn T9 của cổng giả định (dùng chung
  hai tuyến) + họ compiler `oblique_prism_volume`; miền: chân đường cao tại một đỉnh đáy, chiều cao hữu tỉ; `CACHE_VERSION`
  118, candidate `02ce5e1e…`, T3 PASS; G04 = `foundation_only` (chưa đo mô hình thật; compiler opt-in). Phê duyệt:
  `APPROVAL.md` của run. Việc kế tiếp (Cloud): **G05 — lăng trụ/chóp đáy đa giác tổng quát** theo §0.2, trên kiến trúc
  theo hàm hiện có, nhánh mới rẽ từ `main` đã tích hợp. Lát G04 kế tiếp (chân ở trung điểm/trọng tâm) cần đổi hợp đồng +
  ngân sách đo live.

- **Quyết định `frontend-freeze` (2026-10-09, run [`frontend-freeze`](evaluation/geometry/runs/frontend-freeze/), máy local):**
  người dùng hoãn phát triển frontend (chưa phê duyệt chất lượng UI; chỉ sửa lỗi nghiêm trọng ảnh hưởng chức năng cốt lõi) và
  cho tích hợp baseline có ngoại lệ (`APPROVAL.md`). Việc duy nhất kế tiếp: mở rộng các họ hình còn thiếu theo §0.2 trên kiến
  trúc, hàm và cơ chế SẴN CÓ — không kiến trúc mới, không hardcode theo đề, giữ `LLM_ONLY`; sau đó OCR (§0.4). Handoff:
  `runs/frontend-freeze/handoff.md`.

- **Việc `classroom-band-fit` (2026-10-09, run [`classroom-band-fit`](evaluation/geometry/runs/classroom-band-fit/), máy local):**
  CLASSROOM_BAND_FIT — dải lớp học trên điện thoại gọn thành chip trạng thái trên màn chật (24/24, trước 9/24), tên bài không
  mất, công cụ một hàng; product `45f5a7f0`, candidate `7f3f0423…`, Tier-A 8/8 một lượt, `CACHE_VERSION` 118. Việc duy nhất:
  người dùng thao tác tay + quyết theo `review.md` của run này và của `final-acceptance`; duyệt thì merge, push, xoá nhánh ở
  lượt LOCAL riêng có lệnh.

- **Việc `final-acceptance` (2026-10-09, run [`final-acceptance`](evaluation/geometry/runs/final-acceptance/), máy local):**
  FINAL_ACCEPTANCE — không sửa sản phẩm; danh tính kiểm lại; dải lớp học trên điện thoại là lỗi có từ `main` (không chặn theo
  đánh giá của run). Việc duy nhất: người dùng thao tác tay + quyết theo `review.md` của run này; duyệt thì merge, push, xoá nhánh
  ở lượt LOCAL riêng có lệnh.

- **Việc `phone-landscape-layout` (2026-10-08/09, run [`phone-landscape-layout`](evaluation/geometry/runs/phone-landscape-layout/), máy local):**
  PHONE_LANDSCAPE_LAYOUT — điện thoại ngang: thanh điều khiển thành cột cạnh canvas (hình giữ cỡ, sàn 320 px giữ); 360 px: ba nút
  phát một hàng; nghiệm thu cuối trên candidate `7f3f0423…` (product `95a56a17`), Tier-A 8/8 một lượt, `CACHE_VERSION` 118. Việc duy
  nhất: người dùng duyệt `review.md` của run này cùng các gói dưới; duyệt thì merge, push, xoá nhánh ở lượt riêng có lệnh.

- **Việc `mobile-canvas-fit` (2026-10-08, run [`mobile-canvas-fit`](evaluation/geometry/runs/mobile-canvas-fit/), máy local):**
  MOBILE_CANVAS_FIT — D5 khép theo phương án (b) thu hẹp: khổ hẹp ≤ 48rem canvas cao vừa hình (≤ phần khả dụng, ≥ 320 px,
  hình ràng theo chiều cao giữ nguyên; desktop không đổi); bảng bước giữ bước đang xem; tám họ đo lại trên candidate cuối
  `7f3f0423…` (product `c9bcdcdb`), `CACHE_VERSION` 118. Việc duy nhất: người dùng duyệt `review.md` của run này cùng các gói
  dưới; duyệt thì merge, push, xoá nhánh ở lượt riêng có lệnh.

- **Việc `docs-cleanup` (2026-10-08, run [`docs-cleanup`](evaluation/geometry/runs/docs-cleanup/), máy local):**
  DOCUMENTATION_AND_NAMING_CLEANUP — tên test theo hành vi, `docs/legacy/` + kế hoạch Superpowers đọc và xử lý (42 → 15 file),
  12 lớp CSS chết; danh tính cuối của run: candidate `7f3f0423…` (product `f967ba24`, sau lát cắt lý do từ chối T8),
  `CACHE_VERSION` 118 (ghi `b4a33205…`/117 ở đây trước đó là trạng thái giữa run — đính chính ở run `mobile-canvas-fit`).
- **Việc `repo-cleanup` (2026-10-08, run [`repo-cleanup`](evaluation/geometry/runs/repo-cleanup/), máy local):** REPO_CLEANUP —
  gỡ 132 file Tin học hết vai trò (bộ đánh giá, `/api/explain`, fixture thuật toán, engine/view, runner trình duyệt), 325
  selector CSS chết, đổi tên 29 file theo chức năng; prompt và từ vựng IR Tin học giữ có lý do (bề mặt mô hình có băm);
  candidate `b4a33205…`, `CACHE_VERSION` 117. Việc duy nhất không đổi: người dùng duyệt hình và chọn D5.

- **Việc `exact-dimensions` (2026-10-07/08, run
  [`exact-dimensions`](evaluation/geometry/runs/exact-dimensions/), máy local, cùng nhánh):**
  EXACT_DIMENSIONS_AND_CAPTURE_POLICY — chóp tam giác đều/tứ diện đều với kích thước hữu tỉ (phân số, thập phân, cạnh
  bên) phục vụ trên route bằng khung affine + metric Gram suy từ đề (`ISSUE-ARCH-REGULAR-TRIANGULAR-RATIONAL-EDGES` khép);
  ảnh trình duyệt quyết tại nguồn (cùng ca 109 → 15); 11 tệp đổi tên theo một luật; `CACHE_VERSION` 117, candidate
  `e1927f84…`; D5 vẫn mở. Việc duy nhất không đổi: người dùng duyệt hình — `review.md` của run này (R1–R10) cùng gói
  `regular-triangular-pyramid-w01` và W5/W4 — và chọn phương án D5; duyệt thì merge, push, xoá nhánh ở lượt riêng có lệnh.

- **Việc `regular-triangular-pyramid` W1 (2026-10-07, run
  [`regular-triangular-pyramid-w01`](evaluation/geometry/runs/regular-triangular-pyramid-w01/), máy local, cùng nhánh
  theo lệnh người dùng):** REGULAR_TRIANGULAR_PYRAMID_AND_TETRAHEDRON_SLICE — chóp tam giác đều + tứ diện đều trên route
  sản phẩm trong miền hẹp ℚ³ người dùng chọn (cạnh đáy `k√2`/`k√6`, chiều cao bội √3; cạnh hữu tỉ từ chối trung thực,
  `foundation_only`); D1–D4 sửa, D6 giữ, D5 chờ chọn phương án; khung nhìn ban đầu ở giữa mọi họ; `CACHE_VERSION` 116,
  candidate `92c9e198…`. Việc duy nhất: người dùng duyệt hình theo `REVIEW.md` của run này (R1–R12) cùng gói W5/W4 và chọn
  phương án D5 (chặn merge); duyệt thì merge, push, xoá nhánh ở một lượt riêng có lệnh. Gạch đầu dòng W5 trở xuống là bối cảnh.

- **W5 của việc `regular-square-pyramid` (2026-10-06/07, run
  [`regular-square-pyramid-w05`](evaluation/geometry/runs/regular-square-pyramid-w05/), máy local):**
  IMMERSIVE_SIMULATION_AND_ARCHITECTURE_SLICE — cảnh 3D lấp trang không thanh trên toàn cục, nút quay lại, công cụ nhóm
  trong menu, toàn màn hình tuỳ chọn, thẻ lời giải lặp đã gỡ; bộ đọc độ dài nguồn đọc chuỗi bằng nhau (`R2_L1` phục vụ
  `16/3`); `CACHE_VERSION` 115 (không bump), candidate `5e1c0639…`. Việc duy nhất: người dùng duyệt hình theo
  `REVIEW.md` của run W5 cùng gói W4 (chặn merge); duyệt thì merge, push, xoá nhánh ở một lượt riêng có lệnh. Việc mở rộng
  họ đề xuất sau duyệt: chóp tam giác đều + tứ diện đều trên bộ đọc mới (`REPORT.md` §7 của run W5).

- **W4 của việc `regular-square-pyramid` (2026-10-06, run
  [`regular-square-pyramid-w04`](evaluation/geometry/runs/regular-square-pyramid-w04/), máy local):**
  SHARED_SIMULATION_UI_CLOSURE — một cơ chế bảng nổi cho mọi bảng thông tin (ô soi thôi là cột; H-W2-3 khép theo yêu
  cầu người dùng), canvas theo chiều cao khả dụng với «Bước n/N» trong thanh, cây «Thành phần» theo bước, lời kể theo
  ký hiệu đề, SM trên SA nhường nét; `CACHE_VERSION` 115, candidate `8a27a58b…`. Gói duyệt hình W4 (R1–R10, gộp W1–W3)
  duyệt cùng gói W5; câu R4 (trần chiều cao canvas mobile) được brief W5 trả lời: không trần. Gạch đầu dòng W3, W2, W1
  dưới là bối cảnh.

- **W3 của việc `regular-square-pyramid` (2026-10-06, run
  [`regular-square-pyramid-w03`](evaluation/geometry/runs/regular-square-pyramid-w03/), máy local):** tiếp nhận W2
  (`fe68b4ca`, fast-forward) — T3 `FULL_PRODUCT_GATE_PASS` và 14/14 lượt dương xanh ở local (hai cổng đỏ trên cloud là
  môi trường); sửa H-W2-4 (mặt phẳng phụ chỉ để đo không mở bước dựng; gỡ miễn trừ W2) và H-W2-2 (đoạn đề hỏi độ dài
  được dựng; kỳ vọng W18 khôi phục); `CACHE_VERSION` 114, candidate `5dec4572…`. Duyệt hình của W3 gộp vào gói W4.

- **W2 của việc `regular-square-pyramid` (2026-10-05, run
  [`regular-square-pyramid-w02`](evaluation/geometry/runs/regular-square-pyramid-w02/), cùng nhánh, triển khai trên
  cloud):** khép phần còn lại của hình và giao diện W1 trên bảy họ — nhãn số đo chờ đoạn mang nó được dựng; bảng nổi
  «Các bước dựng» thay cột (không đổi cỡ canvas); đoạn đường cao SO của chóp đều qua bước bổ sung dùng chung; chiều cao
  của công thức theo quan hệ ⊥ (gỡ luật giá trị W1); hình phụ ẩn sau khi xong việc / mặt phẳng chỉ để đo ẩn mặc định;
  lưới tuỳ chọn; độ dài ≤ 0 do đề ghi ⇒ SOURCE. `CACHE_VERSION` 113, candidate `d3de9c44…`. Kết luận
  **`CLOUD_IMPLEMENTATION_COMPLETE_LOCAL_VERIFICATION_REQUIRED`**. Việc kế tiếp: máy local tiếp nhận và chạy các kiểm còn lại (`HANDOFF.md` §2, §4 của run), rồi
  người dùng duyệt H-W2-1 (gộp H-W1-1) và trả lời H-W2-2…H-W2-5; duyệt thì merge thẳng vào `main`, push, xoá nhánh.
  Gạch đầu dòng W1 dưới là bối cảnh.

- **W1 của việc `regular-square-pyramid` (2026-10-05, run
  [`regular-square-pyramid-w01`](evaluation/geometry/runs/regular-square-pyramid-w01/), nhánh
  `feat/regular-square-pyramid`):** chóp tứ giác đều (bộ đọc, khuôn C1 T7, tâm O theo danh tính, chiều cao đo được)
  và chín chỉnh sửa §0.1 trên bảy họ; corpus 17/17, trình duyệt 7/7 họ, occlusion 0 lỗi, playback 14/14;
  `CACHE_VERSION` 112, candidate `5234c37e…` (sau bản sửa của tự rà soát: T7 đọc cạnh bên `SA = 3`). Kết luận **`READY_FOR_HUMAN_VISUAL_REVIEW`**. Việc duy nhất: người
  dùng duyệt hình H-W1-1 (`HANDOFF.md` §1 của run), cùng H-W1-2…H-W1-5; duyệt thì merge thẳng vào `main`, push,
  xoá nhánh. Sau đó trở lại `NEXT_FAMILY_SLICE_WITH_DECIDED_UI_CHANGES` (họ kế tiếp từ §0.2). Gạch đầu dòng dưới là
  bối cảnh trước W1.

- **Vì sao:** W19 (run [`w19-docs-organization`](evaluation/geometry/runs/w19-docs-organization/)) khép việc tổ
  chức tài liệu; W20 (run [`w20-cleanup-premerge`](evaluation/geometry/runs/w20-cleanup-premerge/)) đóng hai issue
  tính đúng còn chặn merge và dọn kho. Theo brief W19, việc kế tiếp là **một lát cắt hình học mới cùng các chỉnh sửa
  giao diện đã chốt** (§0.1), không phải thêm wave tài liệu nhỏ lẻ. Đề xuất của W20 (người dùng chưa chọn): chóp tứ
  giác đều (G03) — lý do và giới hạn ở `HANDOFF.md` §2 của run w20. Lượt chốt của việc này, run
  [`cuboid-final-review`](evaluation/geometry/runs/cuboid-final-review/) (2026-10-05, không đánh số wave), rà soát
  trọn tài liệu, đặt luật đánh số wave theo từng việc (`evaluation/RUN_NAMING.md`) và sửa thẻ từ chối của §17; nó
  không đổi việc kế tiếp. Run [`cuboid-acceptance`](evaluation/geometry/runs/cuboid-acceptance/) (2026-10-05, chỉ
  tài liệu) đối chiếu 24 bất biến có con trỏ chết (0 vi phạm, 0 lỗi chặn) và gom hồ sơ nghiệm thu của nhánh. Việc kế
  tiếp chạy trên nhánh mới rẽ từ `main` đã tích hợp, bắt đầu ở W1; đề xuất (chưa chọn): slug `regular-square-pyramid`,
  run đầu `regular-square-pyramid-w01`, cùng chín mục §0.1 — `HANDOFF.md` §4 của run `cuboid-acceptance`.
- **Điều kiện bắt đầu:** người dùng chọn họ hình từ bảng ứng viên §0.2 (W19 không chọn theo tên). Wave mở bằng tiền
  đăng ký: họ, các tầng phải đóng, corpus gắn nhãn trước, cổng trình duyệt desktop/mobile, hồi quy §0.3.
- **Nhánh `fix/cuboid-visual-semantic-closure` đã tích hợp** (2026-10-05, run `cuboid-merge`): người dùng ACCEPTED A–F
  của [`REVIEW.md`](evaluation/geometry/runs/cuboid-merge/REVIEW.md) — W18-H1 cùng bốn cảnh W14, thẻ từ chối hiện hành;
  F1–F5 hoãn và **vẫn mở** ([`APPROVAL.md`](evaluation/geometry/runs/cuboid-merge/APPROVAL.md)). `main` fast-forward
  tới `c282a5f3`, push thường, nhánh local đã xoá. Việc kế tiếp: `NEXT_ACTION = SELECT_AND_START_NEXT_FAMILY_W01`.
- **Đã quyết (người dùng, brief `cuboid-acceptance`, 2026-10-05):** H-CFR-2 giữ chữ thường và "toạ độ" theo quy ước
  kho; H-CFR-1 là backlog giao diện (dưới §0.1), không sửa sản phẩm lúc này; H-CFR-3 `THESIS_DRAFT` §1.8 là bản chính
  đề xuất, chưa xoá `RELATED_WORK_DRAFT` khi chưa đối chiếu nội dung riêng; H-W20-3: 204 mục `D:/tmp` + 108 mục
  `.superpowers` giữ nguyên, không đòi dọn trước merge.
- **Quyết định còn chờ người dùng:** W18-H2 (ô soi lặp dòng giá trị của đáp số không công thức — trùng mục 2 của
  §0.1); W17-H2 (`ISSUE-ARCH-CUT-PLANE-BY-POINT-AND-PARALLEL`); W15-H2 (vùng chặn ngoài đa diện); W15-H3 (từ vựng —
  `ISSUE-ARCH-CONSTRUCTION-BINDING-VOCABULARY`, PARTIAL ở W1); W18-H3 đã giải quyết ở W1
  (`ISSUE-ARCH-SCOPE-GATE-LENGTH-CLUE` RESOLVED); H-W20-4 (tàn dư Tin học trong mã — `HANDOFF.md` của run w20; run
  `cuboid-acceptance` liệt kê thêm phần còn ngủ ở shell). H-W20-1 (câu chữ) và H-W20-2 (nhãn) đã sửa ở run
  `cuboid-final-review`, còn chờ người xem ảnh.
- **Ràng buộc:** giữ `DEFAULT_MODE = LLM_ONLY`; 0 lượt gọi live khi chưa có quyết định ngân sách; `CACHE_VERSION`
  quyết bằng bằng chứng; automation không tự ghi `APPROVED_BY_USER`, không sửa registry kỳ vọng người; không
  push/merge.

### 0.1 Chỉnh sửa giao diện đã chốt (đăng ký sau W18; **đã làm ở regular-square-pyramid-w01**, chờ người duyệt — bảng §3 của `REPORT.md` run ấy)

1. Ẩn mặc định card **Kết quả** dưới mô phỏng.
2. Truy cập mọi kết quả qua nút chọn đại lượng và **một** ô chi tiết.
3. Nút **"Các bước dựng"** mở danh sách cạnh của hình trên desktop.
4. Mobile: panel thu gọn được, giữ hình và điều khiển truy cập được.
5. Chọn một bước thì đồng bộ trạng thái hình học, dòng thời gian và phát lại.
6. Tách bước dựng khỏi bước tính.
7. Chọn độ dài thì tô sáng đoạn; chọn diện tích thì tô sáng vùng.
8. Giảm các dòng mô tả/phụ thuộc lặp lại.
9. Phân biệt cuộn của bộ đo (runner) với cuộn của người học.

Nguồn: brief W19 (2026-10-04), phản hồi của người dùng sau W18. Mỗi mục cần test đơn vị và cổng trình duyệt
desktop + mobile khi làm; sửa `frontend/src` thì đóng băng lại candidate.

Backlog giao diện thêm, ngoài chín mục (H-CFR-1, người dùng 2026-10-05): các lời CONSTRUCTION khác (dựng lệch điểm
hay mặt phẳng, số liệu hệ dùng lệch đề) vẫn kết bằng câu mời gửi lại — xét bỏ cùng việc giao diện kế tiếp (lời ở
`backend/app/learner_messages.py`, đụng mã đo nên đóng băng lại candidate). Chưa sửa, không tuyên bố đã xong.

### 0.2 Ứng viên họ hình kế tiếp — khoảng trống theo tầng

Nguồn: [`architecture/geometry_capability_matrix_v2.json`](architecture/geometry_capability_matrix_v2.json) —
**snapshot W13 tại `bf5a7907`**; w14–w18 có thể đã đóng một phần ô L03 (grounding nguồn) và L09 (dựng hình theo lớp)
cho sáu họ hiện có. Năng lực sản phẩm: `backend/app/simulation/product_capability.py`. Tầng: L01 analyze · L02
contract · L03 grounding nguồn · L04 topology · L05 fact graph · L06 kernel chính xác · L07 IR · L08 luật compiler ·
L09 dựng hình · L10 đo + xuất xứ · L11 renderer · L12 occlusion · L13 tương tác · L14 nhân quả · L15 fail-closed ·
L16 bằng chứng trình duyệt · L17 đánh giá giáo dục.

| nhóm | ô SUPPORTED / PARTIAL / MISSING | tầng MISSING | chặn chính (ô PARTIAL) |
|---|---|---|---|
| G03 chóp tứ giác đều | 4 / 10 / 3 | L08, L16, L17 | "đều" và chân đường cao ở tâm chưa có trường (L01–L05); cạnh đáy + cạnh bên cho chiều cao thường vô tỉ, toạ độ phải ở ℚ³ (L06); cần bước dựng tâm (L09) |
| G04 lăng trụ xiên | 5 / 10 / 2 | L08, L17 | độ xiên cho bằng góc không được grounding (L03) và thường cho chiều cao vô tỉ (L06); tuyến LLM dựng khối nguyên tử (L09) |
| G05 lăng trụ/chóp đáy đa giác tổng quát | 10 / 6 / 1 | L17 | đa giác đều ngoài hình vuông cần toạ độ vô tỉ (L06); compiler chỉ đáy tam giác vuông/chữ nhật (L08); "lục giác đều" chưa grounding (L03) |
| G16 dựng khoảng cách/góc | 8 / 6 / 2 | L08, L17 | compiler chỉ tính thể tích (L08); góc theo độ không grounding (L03); chưa có cung đánh dấu góc (L11) |
| G06 khối đa diện lõm | 8 / 6 / 3 | L05, L08, L17 | sản phẩm `foundation_only`; tự cắt mặt–mặt (toàn cục) không kiểm (L04) |
| G17 góc nhị diện | 3 / 8 / 5 | L05, L08, L11, L16, L17 | chưa có primitive nhị diện; tổng hợp 0/4 trên probe (L07) |

Hình cong (G07 trụ, G08 nón, G10 cầu): sản phẩm `foundation_only`; lượt live V3 `FAIL` (nút thắt grounding phép
dựng) — hàng E3 của [`research/CLAIM_EVIDENCE_MAP.md`](research/CLAIM_EVIDENCE_MAP.md). Nhiều khối (G13), nội/ngoại
tiếp (G14), tiếp xúc (G15): phần lớn MISSING — để sau (§0.4).

### 0.3 Hồi quy bắt buộc cho mọi lát cắt mới

Sáu họ compiler hiện có (bộ trình duyệt desktop/mobile), corpus gold (AC2 18/18 trong vùng chứng chỉ), năm ca demo
(`replay_demo_cases.py`), bề mặt sập (`audit_demo_crash_surface.py`), T3 `full-gate.mjs`. Không hàng đang phục vụ nào
bị từ chối mới mà không có quyết định ghi trước.

### 0.4 Để sau, không tuyên bố đã hỗ trợ

OCR/đề từ ảnh (P4; bằng chứng hiện là FIXTURE), nhiều khối trong một đề (G13/G14), khối tròn xoay tổng quát và khối
ghép/bù (ngoài phạm vi vì kiến trúc). Mỗi việc mở bằng quyết định của người dùng và một wave riêng. Ý tưởng ngoài
khoá luận: [`POST_THESIS_BACKLOG.md`](POST_THESIS_BACKLOG.md) — phụ lục của ROADMAP này.

---

## 1. Các Tầng Ưu Tiên (P0 – P6)

### P0 — Documentation & Handoff Hardening
- Chuẩn hóa toàn bộ hệ thống tài liệu theo 11 information domain.
- Loại bỏ xung đột sở hữu và các liên kết hỏng.
- Đối soát toàn diện bằng chứng kiểm thử máy và số lượng test.
- Đóng gói tài liệu bàn giao phiên (`AI_CONTEXT_BUNDLE.md`) và cổng điều hướng (`README.md`).
- W19 (2026-10-04): `docs/` chia bốn vùng và có catalog đóng. Lần report organization đã hợp nhất vào `docs-cleanup` sau đó chuyển 156/167 báo cáo
  khỏi gốc theo vai trò, giữ 11 ngoại lệ path-bound được ghi từng file; `ISSUE-DOCS-HISTORICAL-REPORTS-AT-DOCS-ROOT` đã đóng.

### P1 — Primitive Compiler Expansion (Mở Rộng Compiler Cơ Sở)
- **Họ bài thứ hai:** Đã chọn và tiền đăng ký họ Lăng trụ đứng có đáy là tam giác vuông (`right_triangle_base_right_prism_volume`) tại `docs/evaluation/geometry/photo-problem-to-scene/primitive-compiler-second-family-selection/report.md`.
- **Evidence Repair:** Đã hoàn tất đính chính bằng chứng lựa chọn, phân loại `CURRICULUM_EVIDENCE = NOT_ESTABLISHED_OFFLINE`, tái thẩm định ma trận thực chứng (Candidate B đạt 94.375% chuẩn hóa, vượt qua 4 kịch bản robustness), vạch rõ 12 tầng kỹ thuật cho vertical slice tại `docs/evaluation/geometry/photo-problem-to-scene/second-family-preregistration-evidence-repair/report.md`.
- **Source Scope Reconciliation:** Đã hoàn tất đối soát danh tính mã nguồn tại `docs/evaluation/geometry/photo-problem-to-scene/second-family-source-scope-reconciliation/report.md`. Xác định `primitives.py:REGISTRY` có đúng 6 hàm, `SourceInvariant` có 5 kind, `RELATION_KINDS` hiện có đủ biểu diễn, IR (`construct_solid`), kernel và frontend được tái sử dụng nguyên trạng.
- **Generic Solid Topology Contract Design & Preregistration:** Đã hoàn thành thiết kế và tiền đăng ký hợp đồng topology khối đa diện tổng quát tại `docs/evaluation/geometry/photo-problem-to-scene/generic-solid-topology-contract-design/report.md`. Phân tách 2 lớp Internal Contract (Pydantic discriminated union) vs Model Transport (flattened sanitize-safe), giải quyết Single Source of Truth (SSOT), xác lập supported topology class là closed polygonal 2-manifold genus-0 (Euler $V-E+F=2$), quy tắc bảo toàn chu kỳ $D_n$, 18 bất biến và 16 fixtures. Đạt `FINAL_DECISION = PASS`, gỡ bỏ bế tắc kỹ thuật về dữ liệu topology.
- **Vertical Slice:** Mở rộng `FactGraph` và `primitive_compiler` để dẫn xuất `SemanticProgramSpec` tất định cho họ bài mới dựa trên hợp đồng topology đã tiền đăng ký (đã hoàn tất trong wave `PRIMITIVE_COMPILER_SECOND_FAMILY_VERTICAL_SLICE_OFFLINE`).
- **Benchmark Đối Chứng:** Chạy benchmark đo token, độ trễ và tính đúng đắn so với đường LLM synthesis hiện tại.
- **Bảo toàn ranh giới:** Không thay đổi kiến trúc mặc định của sản phẩm.

### P2 — Geometry Generalization (Khái Quát Hóa Năng Lực Hình Học)
- Hình chóp với đáy đa giác tùy ý (tam giác thường, tứ giác, hình thang, hình bình hành, hình thoi, hình chữ nhật, hình vuông).
- Khối lăng trụ, khối hộp chữ nhật, hình lập phương.
- Các phép đo nâng cao: khoảng cách giữa hai đường thẳng chéo nhau, góc giữa đường thẳng và mặt phẳng, góc nhị diện.
- Thiết diện phức tạp cắt bởi mặt phẳng đi qua các điểm xác định.
- Khối tròn xoay (hình nón, hình trụ, mặt cầu) khi nền tảng đa diện đã hoàn thiện và ổn định.
- Trạng thái theo từng tầng của mười bảy nhóm hình (gồm chóp đều, lăng trụ xiên, nón cụt, nhiều khối, tiếp xúc, góc nhị diện) và thứ tự sửa đề xuất: [`docs/architecture/geometry_capability_matrix_v2.json`](architecture/geometry_capability_matrix_v2.json), [`GENERIC_GEOMETRY_FOUNDATION_PREREGISTRATION.md`](architecture/GENERIC_GEOMETRY_FOUNDATION_PREREGISTRATION.md) §7 (W13).

### P3 — Visualization & Readability (Trực Quan Hóa và Khả Năng Đọc Cảnh 3D)
- Bộ giải bố cục không gian 3D tự động (spatial layout solver) đảm bảo tỉ lệ thẩm mỹ và hạn chế méo hình.
- Tối ưu hóa góc nhìn camera mặc định (auto-framing, fit-to-view).
- Giải thuật chống đè nhãn điểm và nhãn đoạn thẳng (label anti-collision / positioning solver).
- Nhận diện và diễn họa nét khuất động học (dynamic hidden-line detection & rendering) khi người dùng xoay quỹ đạo 3D.

### P4 — Image Acquisition & Problem Digitization (Đầu Vào Ảnh Chụp Đề Bài)
- Nhận diện vùng đề bài và tách hình vẽ khỏi văn bản từ ảnh chụp điện thoại.
- OCR bóc tách văn bản đề bài tiếng Việt kèm ký hiệu toán học.
- Benchmark đánh giá độ bền vững trước nhiễu ảnh thực tế (ánh sáng, độ nghiêng, độ mờ).

### P5 — Migration Architecture (Chuyển Giao Sang Compiler-First)
- Xây dựng cổng định tuyến `compiler-first`: ưu tiên chạy compiler nếu bài toán đủ điều kiện (`is_compiler_eligible`).
- Cơ chế chuyển tiếp an toàn sang LLM fallback khi bài toán chưa thuộc tập primitive hỗ trợ.
- Cơ chế triển khai canary (phân luồng tỉ lệ thực nghiệm) và rollback tự động khi phát hiện dị thường.
- Đánh giá toàn diện 20 cổng di chuyển tại [`docs/MIGRATION_CHECKLIST.md`](MIGRATION_CHECKLIST.md) trước khi chốt quyết định đổi default mode.

### P6 — Thesis Evaluation & Empirical Experiments (Đánh Giá Khóa Luận)
- Benchmark kỹ thuật toàn diện trên bộ dữ liệu kiểm thử độc lập (held-out test set).
- Đo lường định lượng: token tiêu thụ, thời gian phản hồi (latency), tỷ lệ từ chối an toàn, độ chính xác tọa độ và tính hợp lệ sư phạm.
- Khảo sát tính khả dụng (usability) và trải nghiệm người dùng trên học sinh/giáo viên.
- Phân tích các mối đe dọa đến tính hợp lệ (threats to validity) và đóng góp nghiên cứu của đề tài.
- Hợp nhất bản thảo khoá luận với bằng chứng w09–w18 (hàng chưa có mục ở `research/CLAIM_EVIDENCE_MAP.md` §4) và hai thân Chương 4 rời nhau.
