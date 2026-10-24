# Bàn giao — Unified Geometry Visual Language

**Kết luận kỹ thuật:** `SCENE3D_UNIFIED_VISUAL_LANGUAGE_READY_FOR_HUMAN_REVIEW`
**Phê duyệt thị giác:** `HUMAN_VISUAL_APPROVAL_NOT_GRANTED` — dành cho Owner. **GO MAIN:** chưa cấp; chưa merge, chưa push.

## Danh tính (đầy đủ)

- Nhánh `research/scene3d-unified-visual-language`, worktree `.superpowers/worktrees/scene3d-unified-visual-language`.
- `main` = `origin/main` = `43247c9e9375a3dbf2b5223324a58e6f932ca596` (không đổi). Nguồn chiến dịch `f95596716912e5550ed079287221274b2d70f24c`.
- Sản phẩm: `36dfccef9bb3f5bff3e802aece7083a0e747df72` → `24e1a9dbe24a5abf965ae268ce89097b67060a53` → **`34a57d3540f82a78701b0f0caa8dbae746f266d1`**.
- Bằng chứng `672e8fc60465becd666e8450af55d2ea852d277c`; candidate đóng băng **`dd3bddd48dad7ff865d7c0442c50b6523d87d3c7`**; mã đo 114 file `9bf35a1d6f4c3b3e90228964a3b5ee96288de29efcb3f580f22c6f126489bd9a`.
- Full T3 `FULL_PRODUCT_GATE_PASS` (t3-attempt2, 570.3 s); freeze sau T3 `MATCH`; [`validation.json`](validation.json) 15/15.
- `CACHE_VERSION = 127`, `LLM_ONLY`, `flat`, Hybrid NO-GO, `ALLOW_LIVE_AI=0`, 0 lượt gọi provider.

## Owner cần quyết định

1. **Mặc định B (Academic)** hay đổi sang A/C. So sánh cùng cảnh, cùng camera, cùng viewport: [`comparison/`](comparison/) (mỗi ảnh: before | A | B | C | final). Đề nghị xem trước: `family07_multi_solid_composition` (hai khối, vai trò chính/phụ), `family09_cylinder_and_sections` và `family12_cylinder_ellipse_section` (thiết diện tròn/elip), `public-thiet-dien-chop` và `public-non-thiet-dien-truc` (thiết diện đa giác, mẫu công khai), màn hình từ chối `final-r2/family13_invalid_geometry_refusal-refusal.png` (không có ảnh đối chiếu vì không có cảnh 3D).
2. Trạng thái tương tác của final (chọn, orbit, X-ray, 1024 / 820 với bảng phân tích): `final-r2/*-selected.png`, `*-orbit.png`, `*-xray.png`, `*-1024-analysis.png`, `*-820-analysis.png`, `*-isolated.png`, `*-hidden.png`.
3. Nếu chấp thuận: cấp GO MAIN riêng cho bước merge (không tự suy từ bàn giao này).

## Đã làm trong phiên tiếp nối

- **A.** Lỗi override token được xác minh ở runtime: probe hằng sống trong trình duyệt + kiểm vật liệu WebGL thật; nhánh before chứng minh thay CSS trong bản build.
- **B.** Chạy lại A/B/C với cùng dữ liệu, hình, camera, viewport; các lượt cũ bị ảnh hưởng được đánh dấu INVALIDATED/SUPERSEDED ([`survey-validity.json`](survey-validity.json)), byte giữ nguyên, kiểm được qua [`superseded-evidence-manifest.json`](superseded-evidence-manifest.json).
- **C.** Token ngữ nghĩa thống nhất cho mọi họ hình: thêm fallback thiết diện cho polygon3 thiếu metadata (`24e1a9db`) và thứ tự depth/X-ray theo cùng vai trò (`34a57d35`); 0 ngoại lệ theo id cảnh/họ.
- **D–E.** Kiểm hồi quy: vỏ khối, cạnh hiện/khuất, tô/viền thiết diện, nhiều khối, chọn, Normal/X-ray, khung camera, chồng lấn bảng, ba viewport — 1542/1542 check tự động; focused vitest 60 file / 1064.
- **F.** Review độc lập vòng 3, 4, 5 sau mọi thay đổi; không còn Critical/Important.
- **G.** Candidate, sản phẩm, băm mã đo, log thô, freeze `MATCH` — đối chiếu máy ở `validation.json`; không dùng receipt của candidate khác.

Chi tiết số liệu, các điều chỉnh tiêu chí sau quan sát (reset camera, orbit `[3,0]` chưa tái hiện) và giới hạn: [`report.md`](report.md).

## Giới hạn và việc treo

- **M-b** (backlog): mặt khối thiếu metadata có `parent` trong envelope cũ hiển thị như thiết diện; cần luật tô-pô cạnh của backend ở frontend.
- `[3,0]` cấp phát orbit một lần ở `final-v2`, không tái hiện ở hai lượt có đo pool — nguyên nhân chưa xác minh.
- Ảnh cảnh cong không lặp lại bit-chính-xác giữa hai lần chụp (có từ trước).
- Tương phản nhãn trên mọi nền, FPS thiết bị thật, E2E NLU sống: UNKNOWN.
- File chưa track ở gốc worktree `.gitattributes` (tắt chuẩn hoá xuống dòng cho mọi `*.log`/`*.png` toàn kho) và `debug.log` (log Chrome) — không commit, không xoá; bản `.gitattributes` có phạm vi run đã được commit trong thư mục run.
