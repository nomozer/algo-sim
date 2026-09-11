# `bien-the/` — lượt đo BIẾN THỂ D, không phải lượt đo candidate

`CANDIDATE_INTERACTION.json` trong thư mục này mang `"nhan": "candidate"` vì bộ
đo dùng chung một nhãn cho mọi lượt chạy trên cây có commit `7f34286`. **Nó
KHÔNG phải bản candidate đang chạy trên `main`.**

Phân biệt bằng ba dấu, theo đúng thứ tự:

| | `truc/CANDIDATE_INTERACTION.json` | `bien-the/CANDIDATE_INTERACTION.json` |
|---|---|---|
| commit ghi trong file | `56350f7` (đỉnh `main`) | `7f34286` |
| sửa chưa commit trong worktree | không | **có** — dời `cam.up.set(...)` lên TRƯỚC `new OrbitControls(...)` |
| trục quay đo được | `[0.35…0.40, −0.05…−0.14, 0.47…0.57]`, ‖trục‖ 0,608–0,680 | `[0, 0, 1]`, ‖trục‖ 1,000 |

Biến thể D dựng trong worktree tạm (`/d/tmp/asim-var`), đo xong thì gỡ; thay đổi
một dòng **không** được commit và **không** có trên `main`. Nếu cần dựng lại: xem
`docs/SCENE3D_INTERACTION_SMOOTHNESS_REGRESSION_DIAGNOSIS.md §5`.

Không sửa file JSON trong thư mục này — nó là baseline để so lượt sau.
