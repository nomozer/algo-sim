# VISUAL_BEFORE_AFTER_EVIDENCE — `cc449d5` → `267aca5`

Ghép ảnh của audit gốc với ảnh chụp lại tại HEAD. Mỗi cặp kèm một sidecar JSON
đọc **từ state của engine**, để bằng chứng trình bày (ảnh) và bằng chứng ngữ
nghĩa (state) tách bạch và đối chiếu được.

- BEFORE: `docs/evaluation/simulation-mechanism-audit/screenshots/` (baseline `cc449d5`)
- AFTER: `screenshots/<case>__after__267aca5.png`
- Sidecar: `sidecars/<case>__after__267aca5.json`
- Dữ liệu thô: `delta-verify.json`

Ảnh BEFORE dùng biến thể `-2-mechanism-active` — checkpoint "cơ chế đang diễn ra"
của bộ gốc, tương ứng với vị trí giữa timeline của ảnh AFTER.

## Cặp ảnh

| # | Case | BEFORE (`cc449d5`) | AFTER (`267aca5`) | Trạng thái |
|---|---|---|---|---|
| 1 | `insertion-held-key` | `algorithm-insertion_sort-2-mechanism-active.png` | `insertion-held-key__after__267aca5.png` | RESOLVED |
| 2 | `bounded-loop-visible` | `algorithm-bounded_control_flow-2-mechanism-active.png` | `bounded-loop-visible__after__267aca5.png` | RESOLVED |
| 3 | `tree-stack-drawn` | `tree-traversal-2-mechanism-active.png` | `tree-stack-drawn__after__267aca5.png` | RESOLVED |
| 4 | `graph-queue-drawn` | `network-graph_traversal-2-mechanism-active.png` | `graph-queue-drawn__after__267aca5.png` | IMPROVED_PARTIAL |
| 5 | `dag-legend` | `logic-boolean_dag-2-mechanism-active.png` | `dag-legend__after__267aca5.png` | RESOLVED |
| 6 | `and-gate-legend` | `logic-and_gate-2-mechanism-active.png` | `and-gate-legend__after__267aca5.png` | STILL_PRESENT |
| 7 | `base-conversion-current-row` | `binary-base_conversion-2-mechanism-active.png` | `base-conversion-current-row__after__267aca5.png` | STILL_PRESENT |
| 8 | `table-active-stage` | `database-relational_table_query-2-mechanism-active.png` | `table-active-stage__after__267aca5.png` | STILL_PRESENT |
| 9 | `packet-routing-progress` | `network-packet_routing-2-mechanism-active.png` | `packet-routing-progress__after__267aca5.png` | STILL_PRESENT |

## Phép đo đứng sau từng verdict

Verdict **không** đến từ việc nhìn ảnh. Mỗi ca có một phép đo trong DOM/CSSOM
chạy trong Chrome; ảnh chỉ để người đọc kiểm chứng lại bằng mắt.

| Case | Phép đo | Kết quả |
|---|---|---|
| `insertion-held-key` | có `.hold-tray`? · đếm `<text>` = "trống" trong SVG | `heldTray=true` · `gapCells=1` |
| `bounded-loop-visible` | đếm `<svg>` trong thẻ · dò từ khoá vòng lặp trong `innerText` | `svg=1` · `["lượt","vòng","lặp"]` |
| `tree-stack-drawn` | có `[class*=frontier]`? · đếm ô con | `frontier-stack` · `2 ô` |
| `graph-queue-drawn` | như trên **và** đếm cạnh có `stroke-width ≥ 2.5` | `frontier-queue` · `4 ô` · **cạnh nhấn 0/5** |
| `dag-legend` | có `.stage-legend`? · liệt kê mục | `true` · 4 mục |
| `and-gate-legend` | như trên | `false` · 0 mục |
| `base-conversion-current-row` | đếm `<tr>` mang lớp `is-current`/`is-active` | `0/3 hàng` |
| `table-active-stage` | đếm chip tầng mang lớp active | `0/4 chip` |
| `packet-routing-progress` | lớp phân biệt trên cạnh · `<marker>`/`<polygon>` · chú giải | `0 lớp` · `0 mũi tên` · `0 mục` |

## Nội dung sidecar

Mỗi sidecar AFTER ghi, đọc trực tiếp từ store:

`moduleId · cursor · timelineLength · events · snapshot.array · vars · marks ·
ids · narration · prediction · branch · domText (400 ký tự đầu) · rects (card ·
stage · controls) · viewport`

Nhờ vậy mỗi khẳng định trong ma trận delta truy ngược được về đúng một trạng
thái engine, không phải về ấn tượng thị giác.

## Điều các cặp ảnh này KHÔNG chứng minh

- **Không** chứng minh học sinh hiểu bài hơn. Trạng thái chung giữ nguyên
  `LEARNER_IMPACT_NOT_EVALUATED`.
- **Không** chứng minh cơ chế được *dạy* đúng — chỉ chứng minh dấu hiệu của cơ
  chế **có mặt trên màn hình** và khớp state canonical.
- **Không** phủ mọi viewport: chỉ 1440×1000. Bằng chứng viewport hẹp nằm ở
  các lượt nghiệm thu trước (`ui-baseline/`, và nghiệm thu W3B).
