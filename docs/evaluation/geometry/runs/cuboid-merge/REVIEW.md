# REVIEW — gói duyệt hình trước khi merge nhánh cuboid

Cho người dùng, người duyệt hình. Nhánh `fix/cuboid-visual-semantic-closure`, candidate hiện hành **`b2d4187a`**
(`b2d4187a78ed8bf6df15118edc7e4e251c5f22df536e50b73ac043f108f3b7af`, commit sản phẩm
`284a9bfad7e815f7a2228eca89736f714b53c26c`). Run này không chụp ảnh và không chép ảnh: mọi ảnh dưới đây là ảnh nguồn
của run đã đo. Đường dẫn tính từ `docs/evaluation/geometry/runs/`.

**Cách trả lời:** với mỗi nhóm A–F, ghi **ACCEPTED** hoặc **NEEDS_CHANGES** kèm lý do cụ thể (ảnh nào, chỗ nào, muốn
gì). `AGENTS.md` §2 và `HANDOFF.md` của nhánh yêu cầu phê duyệt hình **tường minh** trước khi merge vào `main`; việc
gửi báo cáo, gửi prompt hay yêu cầu tiếp tục task không được tính là phê duyệt.

## Ảnh W18 có còn đúng với candidate hiện hành không

Ảnh cảnh phục vụ của W18 đo ở `0ca3accf` trên candidate `d3b4cab9`. Kết luận chuyển tiếp **không** dựa vào việc
renderer giữ nguyên byte, mà dựa vào hai bằng chứng (chi tiết: [`results/logs/TRANSFER.log`](results/logs/TRANSFER.log),
[`results/FIXTURE_TRANSFER.json`](results/FIXTURE_TRANSFER.json)):

1. **Dữ liệu cảnh.** Bộ đo trình duyệt W18 nạp 32 fixture do
   `backend/scripts/generate_generic_tier_a_fixtures.py` sinh qua ranh giới sản phẩm, offline (Analyze thay bằng
   RequestContract chuẩn, tổng hợp bằng compiler hoặc chương trình đã đóng băng; gọi model là ném lỗi). Chạy lại
   generator trong worktree sạch ở `0ca3accf` cho đúng từng byte manifest fixture W18 đã ghi (`10dbe2de…`), tức đúng
   các fixture đã chụp. Chạy cùng generator ở `37b23f04` rồi so từng trường JSON của cả 32 fixture, không bỏ hay che
   trường nào: **khác nhau duy nhất `product_commit_sha` và `product_tree_sha`** (dấu danh tính). Hình học và topology
   của `scene3d`, sự kiện, formation, nhãn hiển thị, đại lượng, tham chiếu công thức, lời và nhãn từ chối: giữ nguyên.
2. **Mã vẽ và cấu hình trình bày.** Từ `0ca3accf`, `frontend/src` chỉ đổi trong `UnsupportedNotice` (nhãn "Loại vấn
   đề" của thẻ từ chối, nhánh mới chỉ cho mã `CONSTRUCTION_REPLACED_BY_COORDINATES` mà không fixture W18 nào mang) và
   một trường kiểu tuỳ chọn; nhánh vẽ Scene3D không đổi. Manifest kịch bản chỉ đổi ba trường danh tính (viewport,
   camera, kỳ vọng giữ nguyên); harness chỉ thêm `export` và một assertion tuỳ chọn cho ca âm. Dependency và cấu hình
   build không đổi.

⇒ **Ảnh W18 được chuyển tiếp sang candidate `b2d4187a`** cho sáu cảnh dương (hai khổ, mọi trạng thái đã chụp), hai
cảnh phục vụ khoảng cách và các thẻ từ chối của W18. **Không chụp bổ sung.** Ảnh thẻ từ chối của
`cuboid-final-review` đã chụp trên chính candidate `b2d4187a` (`a1c53cdb`), danh tính vẫn khớp (candidate `--verify`
của run này).

## Mở nhanh

Tổng quan: `w18-binding-focus/images/overview/INDEX.png`; mỗi họ một trang: `w18-binding-focus/images/<họ>/SHEET.png`
(`triangular-pyramid`, `rectangular-pyramid`, `triangular-prism`, `cuboid`, `cube`, `cross-section`). Ảnh lẻ trong
`w18-binding-focus/images/<họ>/<khổ>/` với `<khổ>` = `desktop` (1440×900) hoặc `mobile` (390×844).

## Phần 1 — chất lượng hình cần bạn duyệt

| nhóm | xem gì | ảnh | ACCEPTED / NEEDS_CHANGES + lý do |
|---|---|---|---|
| **A. Mặc định gọn, chọn đại lượng, vùng giải thích** | mặc định chỉ tên điểm + dữ kiện; một chip "Hiện tất cả"; chọn độ dài/diện tích/thể tích thì hiện nhãn và chuỗi số; ô soi là nơi giải thích duy nhất; lời giải thu gọn mặc định | `<khổ>/neutral_final.png`, `show_all.png`, `selected_<loại>.png` + `detail_<loại>.png`, `solution_neutral_final.png`, `solution_expanded.png` | |
| **B. Nhân chứng khoảng cách, các bước dựng** | đoạn nét đứt tới chân chính xác + dấu góc vuông, chỉ khi nhãn khoảng cách hiện; hai ca phục vụ của W18 (M trên SA tới đáy = 3; S tới H trên BD = 3√6) nằm ở hàng phục vụ của `cross-section/SHEET.png`; hình dựng theo bước | `cross-section/<khổ>/selected_distance.png`, `detail_distance.png`; `cross-section/SHEET.png`; `cuboid-final-review/images/w18_projection_line/<khổ>/served.png` (3√6, chụp trên `b2d4187a`); `<họ>/FILMSTRIP.png`, `<họ>/desktop/formation/`, `<họ>/mobile/formation/` | |
| **C. Nét liền/đứt, tô sáng, bốn cảnh W14** | cạnh khuất nét đứt, cạnh hiện nét liền; tô sáng nhân quả rồi trả lại; bốn cảnh W14 đổi — chóp tam giác, lăng trụ tam giác, chóp đáy chữ nhật, thiết diện — sản phẩm khớp oracle độc lập ở mọi trạng thái (`w18-binding-focus/results/OCCLUSION_MEASUREMENT.json`: 0 lỗi, verdict `HUMAN_REVIEW_PENDING` đúng bốn cảnh này), chỉ còn chờ mắt người | `<họ>/hidden-edges/desktop/`, `<khổ>/rotated_neutral.png`, `causal_selected.png` → `causal_restored.png`, `solution_causal_selected.png` | |
| **D. Desktop / mobile** | ô soi bên phải (desktop) hoặc dưới hình (mobile), không tràn, không che số đo và nút; nhãn khi đổi cỡ | cặp `desktop/` · `mobile/` của mọi ảnh trên; `desktop/annotations_resized.png` | |
| **E. Thẻ từ chối hiện hành** | lời "Hệ chưa kiểm chứng được ‹quan hệ›, vì điểm này ‹cách đặt› thay vì dựng từ quan hệ trong đề. Hệ tạm dừng…", dòng "Loại vấn đề: chưa kiểm chứng được phép dựng", không hình, không đáp số, không câu mời gửi lại; đối chứng lệch/chưa đối chiếu không đổi | `cuboid-final-review/images/cfr_projection_by_coordinates/<khổ>/refusal.png`, `cfr_projection_alias_vertex/<khổ>/refusal.png`, `cfr_midpoint_by_coordinates/<khổ>/refusal.png`; đối chứng `w18_projection_mismatch/<khổ>/refusal.png`, `w18_unverified/<khổ>/refusal.png` (cùng thư mục `images/`); kết quả tự động `cuboid-final-review/results/BROWSER_REFUSAL_CFR.json` (12/12) | |

## Phần 2 — giới hạn chức năng đề nghị hoãn (F)

Chấp nhận nhóm F nghĩa là chấp nhận merge với các giới hạn này còn mở; chúng không bị coi là đã xong.

| # | giới hạn | nơi ghi |
|---|---|---|
| F1 | Phép dựng điểm chỉ đối chiếu trung điểm và hình chiếu với đề; tâm, giao điểm, cách nói ngoài từ vựng ⇒ từ chối "chưa đối chiếu được" trong vùng đa diện | `ISSUE-ARCH-CONSTRUCTION-BINDING-VOCABULARY` |
| F2 | Chứng chỉ giả định chỉ thi hành trong vùng đa diện (từ vựng đóng); ngoài vùng chỉ ghi | `ARCHITECTURE_MAP.md` §5 #37, W15-H2 |
| F3 | Chỉ phép cắt (thiết diện) được đối chiếu với câu đề; quan hệ dựng khác chưa | `ISSUE-ARCH-CONSTRUCTION-RELATION-BEYOND-SECTION-CUT` |
| F4 | Hình cong `foundation_only`; đề từ ảnh mới có bằng chứng FIXTURE; nhiều khối trong một đề ngoài phạm vi | `ROADMAP.md` §0.4 |
| F5 | Hai script dev gọi Gemini mà không cần opt-in (`run_live_gemini_semantic_smoke.py`, `run_rectangular_pyramid_live_analyze.py`). Không nằm trên đường sản phẩm hay của học sinh; rủi ro là tiêu quota khi có người chạy tay — chưa sửa, chưa tái hiện bằng lượt chạy | `ISSUE-OPS-LIVE-OPT-IN-NOT-UNIFORM` |

## Phần 3 — chỉnh sửa giao diện đã đăng ký, chưa triển khai (để biết, không cần duyệt)

Chín mục `ROADMAP.md` §0.1 (ẩn card Kết quả, một ô chi tiết, nút "Các bước dựng", panel mobile thu gọn, đồng bộ bước,
tách bước dựng/bước tính, tô sáng đoạn/vùng, giảm dòng lặp, tách cuộn runner/người học) và backlog H-CFR-1 (câu mời
gửi lại ở các lời CONSTRUCTION khác). Chúng thuộc việc kế tiếp trên nhánh mới; ảnh trên đây là giao diện **trước** các
chỉnh sửa ấy.
