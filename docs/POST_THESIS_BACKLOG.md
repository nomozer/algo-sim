# POST_THESIS_BACKLOG.md — ý tưởng đáng làm, **sau** khoá luận

> Danh sách này tồn tại để ý tưởng không bị mất mà sản phẩm vẫn có biên. Mỗi mục
> phải nói **vì sao nó không cần cho khoá luận** — nếu không nói được, nó thuộc
> phạm vi lõi chứ không thuộc đây.
>
> Khoá phạm vi ở `STATUS_LEDGER.md §0` là nguồn phán quyết.

*Hai mục ý tưởng của giai đoạn Tin học (cam kết cơ chế ở điểm quyết định thuật toán; đợt nâng trải nghiệm toàn danh mục, 2026-08-16) — phạm vi đã bỏ từ 2026-08-24: nguyên văn ở [`legacy/POST_THESIS_BACKLOG_INFORMATICS_ERA.md`](legacy/POST_THESIS_BACKLOG_INFORMATICS_ERA.md).*

## Các mục khác (ghi để không mất, không có kế hoạch)

- Mở rộng LMS: sổ điểm, điểm danh, thời khoá biểu, học phí — **NON-GOAL** theo
  khoá phạm vi; tầng lớp học cố ý dừng ở đăng nhập + lớp + giao bài + luyện tập
  + quan sát.
- Trình soạn thảo tự do (HTML/CSS/JS, thuật toán, cây, topology) — phá ranh giới
  "hiện vật có ràng buộc" vốn là điều khiến engine tất định phán được đúng/sai.
- Chủ đề ngoài hình học không gian Toán 11–12 — `detect_domain` từ chối (fail closed).
- Phân tích học tập nâng cao, cộng tác thời gian thực, hiệu ứng 3D mở rộng.
- Nghiên cứu đối chứng trên người học — đây là **giới hạn nghiên cứu**, không
  phải khiếm khuyết hiện thực; `LEARNER_IMPACT_NOT_EVALUATED` giữ nguyên.

## Nợ tìm được khi soát tích hợp (2026-09-02) — có kế hoạch, chờ mở đóng băng

Hai mục dưới đây **không phải ý tưởng**, chúng là khiếm khuyết đã đo được. Ghi ở
đây vì cả hai đòi chạm vùng đang đóng băng; bằng chứng và phân tích đầy đủ ở
`docs/evaluation/reports/PRODUCT_INTEGRATION_HARDENING.md`.

- ~~**Tên biến IR lọt lên bề mặt học sinh** (§4.1)~~ — ✅ **ĐÓNG 2026-09-02**
  (`SEMANTIC_PRESENTATION_METADATA_AUTHORITY`, G1+G2). Giữ mô tả gốc bên dưới
  vì nó ghi đúng chẩn đoán lúc phát hiện; phần *"sửa cùng lúc với việc mở rộng
  `ui-hygiene.test.ts`"* thì **không** làm theo cách ấy — guard mới nằm ở
  `tests/geometry/test_display_names.py` và `certify-display-metadata.mjs`, tức
  ở đúng tầng sinh ra cái tên, không ở tầng quét component. Envelope phát
  `label == id` cho vật `render: "readout"`, nên dải kết quả in
  `khoang_cach_hs √22` thay vì một câu tiếng Việt; dải tiêu điểm in
  `Đang dựng the_tich_sabcd`. Số thì đúng, chỉ cái tên là định danh kỹ thuật.
  Bản sửa đúng nằm ở nơi dựng cảnh trong `backend/app/` — **trong
  `MEASURED_SYSTEM_PATHS`**, nên sửa là candidate hết hiệu lực. Sửa cùng lúc
  với việc mở rộng `components/ui-hygiene.test.ts`: guard hiện chỉ quét
  `components/` và chỉ tìm ba tên `algorithm_id`/`simulationId`/`simId`, nên
  **về cấu tạo** nó không thấy được hạng rò rỉ này.
- ~~**`SECTION_COPLANAR_EDGE_RUNTIME_FIX`**~~ — ✅ **ĐÓNG 2026-09-02.**
  Nguyên nhân không phải hình học mà là **đếm trùng**: một cạnh nằm trong mặt
  phẳng cắt thuộc HAI mặt kề, nên cả hai mặt cùng báo đúng một đoạn giao; vòng
  nối tiêu thụ hết các đoạn thật rồi vấp bản sao. Sửa bằng khử trùng theo cặp
  đầu mút chính xác (`frozenset` trên `Point3`), không đổi thuật toán đi-theo-mặt.
- ~~**`MISLEADING_MALFORMED_SOLID_MESSAGE`**~~ — ✅ **ĐÓNG 2026-09-02.**
  `MALFORMED_SOLID` nay chỉ dành cho khối thật sự hỏng; thêm
  `SECTION_INTERSECTION_DEGENERATE` và `SECTION_CONSTRUCTION_INTERNAL_FAILURE`.
  ⚠️ **Sửa một khẳng định sai của mục cũ:** nó viết rằng thông điệp sai làm
  *"vòng sửa ≤3 lượt tiêu quota vào chỗ không có lỗi"*. Không đúng — vòng sửa
  của `stage_semantic_program` đóng ở tầng TĨNH (`ir_static_check`,
  `grounding_gate`) và **interpreter chạy sau nó**, nên `GeometryError` không
  bao giờ tới prompt sửa. Cái giá thật là **chẩn đoán sai gửi tới người đọc và
  vào artifact đánh giá**, không phải token.
- ~~**Không có React error boundary nào trong kho**~~ — ✅ **ĐÓNG 2026-09-03**
  (`REACT_ERROR_BOUNDARY_HARDENING`). Hai mức, 0 dependency mới, 0 dòng
  backend. Còn hở hai lớp và chúng được khai riêng chứ không gộp:
  `ASYNC_EXCEPTION_CONTAINMENT` và `WEBGL_CONTEXT_LOSS_RECOVERY` —
  React boundary về cấu tạo không bắt được chúng.

## Hướng phát triển (sau khi ĐÓNG phát triển tính năng, 2026-09-09)

`FINAL_SYSTEM_REPRODUCIBILITY_AND_RELEASE_FREEZE` đóng phát triển tính năng cho
bản dùng khoá luận (`FEATURE_DEVELOPMENT_STATUS = CLOSED`). Mọi mục dưới đây
**không** được nhập tiếp vào bản ấy.

- **`BROWSER_GATES_ON_PRODUCTION_BUILD`** — chuyển
  `certify-product-ui-rendering.mjs`, `certify-scene3d-hidden-lines.mjs` và
  `certify-scene3d-visual-fidelity.mjs` sang chạy trên **bản dựng sản phẩm**,
  như `certify-refusal-surface.mjs` đã làm.
  *Vì sao đáng làm*: đo được **13–25 % phiên headless Chrome không tải nổi
  module từ Vite dev**, trong khi bản dựng **0/15 lỗi**
  (`final-system-release/PAGE_BOOT_MEASUREMENT.json`). Nay ba cổng ấy chỉ được
  che bằng *mở lại trình duyệt có trần*, và mở lại chỉ gỡ **6/10**.
  *Vì sao CHƯA làm*: chúng dùng `s.mods.store` — import theo đường dẫn NGUỒN,
  chỉ tồn tại ở dev. Thay nó cần đổi `BrowserSession` (tệp DÙNG CHUNG cho ~10
  script) sang điều khiển qua DOM + tải lại trang. Sửa ba bộ đo vào phút cuối
  kỳ đóng băng đổi lấy rủi ro lớn hơn thứ nó gỡ.
- ~~**`DISPLAY_NAME_AUTHORITY_ELLIPSE_AND_CURVED_KIND`**~~ — ✅ **ĐÓNG một
  nửa 2026-09-10** (`DISPLAY_NAME_FINAL_POLISH_AND_RELEASE_REFRESH`): `ellipse3`
  nay có tên ở cả ba bảng ⇒ **12/12, 0 placeholder**. Nửa còn lại tách ra thành
  mục dưới đây.
- **`CURVED_KIND_IN_SHORT_REFERENCE`** — `curved_solid` vẫn được **NHẮC** bằng
  danh từ chung *«khối cong»* trong câu của vật khác (`p4`, `p5`, `p6`, `p7`),
  dù `curved_kind` biết rõ đó là hình trụ hay hình nón — nhãn của chính khối ấy
  đã ghi `Hình trụ`.
  *Vì sao chưa làm*: `_DANH_TU_NGAN` tra theo **KIỂU**, mà ba hình cong dùng
  chung một kiểu; danh từ riêng thuộc `curved.KHOI_CONG` và `thong_tin` hiện
  **không chở `curved_kind`**. Sửa được, nhưng nó đổi **bốn** nhãn — trong đó
  hai thuộc mười nhãn mà `§5.3` của wave yêu cầu giữ nguyên.
  *Đáng làm vì*: *«Elip giao của hình trụ và mặt phẳng»* đọc rõ hơn hẳn
  *«Elip giao của khối cong và mặt phẳng»* với người học.
- **`PRODUCT_CAPABILITY_REASON_STRING`** — `product_capability.py` còn ghi lý do
  *"MÔ HÌNH: chưa đo"* cho khối cong dù mô hình ĐÃ đo 5/5. Trạng thái
  `foundation_only` vẫn đúng (`n = 1`); chỉ chuỗi lý do cũ.
- **`REFUSAL_SURFACE_CERTIFIER_WARMUP_FLAKE`** — ✅ **ĐÓNG 2026-09-09** bởi
  chính wave này (`FLAKE_RATE 0.9 → 0`).
