# GEO-BE-001: tên mặt phẳng rò ID vào vai trò điểm giao

| Mục | Giá trị |
|---|---|
| Worktree | `D:\Documents\projects\axo-geometry-library` — một **git worktree của kho `algo-sim`** (chung `.git`), nhánh `feat/axo-geometry-library-verification` |
| Mốc | `c7a6077fd` |
| Commit sửa | `5a229507b` (`display_names.py`, test mới, catalog nâng cao) |
| Lượt gọi AI | 0 |

Nhãn: **VF** VERIFIED FACT · **INF** INFERENCE · **NM** NOT_MEASURED · **BL** BLOCKED.

## Kết quả

- **VF. Tái hiện đúng 4 nhãn lỗi tại `c7a6077fd`**, qua đường thật của generator (`build_all_advanced_samples`).
- **VF. Nguyên nhân đúng như giả thuyết của ticket.** Chuỗi gọi:
  1. `giai(E)` gọi sang mặt phẳng `mp_MNP`.
  2. Nhánh `points_on_plane` của mặt phẳng gọi `giai(F)`.
  3. `sources` của F lại gồm `mp_MNP`, nên lời gọi ngược `giai(mp_MNP)` thoát sớm vì mặt phẳng còn trong `dang_giai`.
  4. Câu của F được dựng bằng `goi_ngan.get(s, s)`, rơi về raw ID, rồi được ghi nhớ.
  - Lỗi **phụ thuộc thứ tự duyệt**: điểm giao giải đầu tiên (E) đúng, các điểm khác trên cùng mặt phẳng sai.
- **VF. Đã sửa ở `_mot_luot`, theo hai bước.**
  - **Incidence ≠ định nghĩa:** điểm mà định nghĩa của nó đi qua mặt phẳng không được giải từ phía mặt phẳng.
  - **Ký hiệu trước, mô tả sau:** câu nào được dựng khi một toán hạng còn dang dở thì được dựng lại sau lượt một, cùng mọi tên phụ thuộc vào nó.
  - Raw ID không còn được dùng làm fallback trong câu. Chu trình định nghĩa thật được báo qua tham số tuỳ chọn `unresolved`.
  - Chỉ đổi trường hiển thị; `id`, `sources`, `depends`, `producer` giữ nguyên.
- **VF.** F/F/Q/E nay là "Giao điểm của SD và (MNP)", "… A′B′ và (MNP)", "… AA′ và (MNP)", "… A′B′ và (NPQ)". 15/15 test đạt:
  - đúng nguyên văn 4 nhãn;
  - 0 raw ID trong 11 mẫu;
  - 6 thứ tự xáo trộn và thứ tự đảo cho cùng kết quả;
  - đổi tên MNP → XYZ;
  - mặt phẳng tên (α);
  - chu trình thật.
- **VF. Catalog nâng cao:** đúng 4 thay đổi, đều ở `role`; sinh lại lần hai trùng byte.
- **VF. Catalog cơ bản:** bản sửa không đổi gì ở đây. Có một **trôi có từ trước** (`steps` của thiết diện trong `thiet-dien-chop`), vẫn xuất hiện khi sinh từ HEAD sạch không có bản sửa; nó ngoài phạm vi ticket nên tôi **không commit**, file được hoàn lại.
- **VF. Frontend:**
  - `v9413-geometry-rendering-integrity` 8/8 đạt.
  - Miền geometry 1370/1371 đạt. Ca đỏ là phép quét tĩnh `family-icons.tsx` (commit `65ffb998a` của phiên frontend), không liên quan catalog; tôi không sửa vì thuộc quyền phiên đó.
  - `geometry-samples.test.ts` không tồn tại với tên đó.
  - `replaceRawSceneIdTokens` giữ nguyên.
- **NM.** Trình duyệt thật trong repo A chưa chạy.
- **BL.** Đóng băng candidate ở A bị chặn: cây có 82 file chưa commit của phiên khác. Pytest đầy đủ trên cây bẩn: 13 880 đạt / 16 đỏ, phân loại trong `backend_regression.json`; không ca nào do bản sửa này.
- **INF.** `display_names.py` của worktree `local-first-geometry-understanding` trùng byte với bản trước khi sửa, nên rất có thể mang cùng lỗi tiềm ẩn. Tôi không chép bản sửa sang đó (quy định của task); việc đó cần Owner quyết.
