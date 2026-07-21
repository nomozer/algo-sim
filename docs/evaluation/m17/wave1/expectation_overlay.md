# Expectation Overlay — M17-Lite Wave 1 (changelog)

> **Mục đích:** ghi nhận TRUNG THỰC những case của bộ đánh giá M16 / legacy
> mà **kỳ vọng thực-production đã thay đổi** sau khi Wave 1 flip hai
> intentional-gap thành owned (Selection Sort, đổi cơ số hex/octal) và thêm
> duyệt đồ thị BFS/DFS. Đây là **overlay** — một lớp phủ có changelog, KHÔNG
> sửa một byte nào của:
> - `backend/app/evaluation/datasets/m16_catalog.py` (frozen dataset),
> - `docs/evaluation/m16/**` (frozen artifacts),
> - frozen 30-case regression `DATASET` (fingerprint pin vẫn xanh).
>
> Bằng chứng bất khả xâm phạm: `tests/test_m16_offline_eval.py` vẫn chạy 50/50
> case qua production `run_pipeline` với provider scripted **pin route CŨ** và
> pass — vì kịch bản offline pin `classify → binary.decimal_to_binary` (target
> KHÔNG sở hữu `non_binary_base`), gate vẫn fail-closed cho ĐÚNG đường đó.
> Overlay này chỉ mô tả điều xảy ra khi chạy **real-production (unscripted)**.

## Bối cảnh: hai flip của Wave 1

| Cơ chế | Wave 0 | Wave 1 | Target sở hữu mới |
|---|---|---|---|
| `comparison_sort.select_extreme_repeated` | INTENTIONAL_GAP | OWNED | `algorithm.selection_sort` |
| `positional_representation.non_binary_base` | INTENTIONAL_GAP | OWNED | `binary.base_conversion` (chỉ cơ số **2/8/10/16**) |

## Case ĐỔI kỳ vọng: gap → supported (real-production)

| Case | Kỳ vọng cũ | Kỳ vọng mới (W1) | Lý do |
|---|---|---|---|
| `m16-nm-hex-gap` | `unsupported` / `capability_gap` | `ok` → `binary.base_conversion` | Đổi 2026 sang hex nay có executor (chia lấy dư cơ số 16). |
| `m15-hex-gap` | `unsupported` | `ok` → `binary.base_conversion` | Hex ∈ {2,8,10,16}. |
| `m15-octal-gap` | `unsupported` | `ok` → `binary.base_conversion` | Octal ∈ {2,8,10,16}. |
| `cap-selection-sort-gap` | `unsupported` / `gate_mechanism_ownership` | `ok` → `algorithm.selection_sort` (qua token `comparison_sort`) | Selection Sort nay có executor + variant. |

## Case GIỮ NGUYÊN gap (KHÔNG flip — ranh giới quan trọng)

| Case | Kỳ vọng | Vì sao KHÔNG flip |
|---|---|---|
| `m16-cr-positional-fail` | `unsupported` (giữ) | Cơ số **5** — KHÔNG thuộc {2,8,10,16}. `binary.base_conversion` chỉ hỗ trợ 2/8/10/16, nên base-5 vẫn là gap trung thực. |
| `m16-nm-sort-partition` | `unsupported` (giữ) | Quick Sort (`partition_recursive`) vẫn là intentional-gap — contract chưa biểu diễn partition. |
| `m16-nm-weighted-shortest` | `unsupported` (giữ) | Dijkstra CÓ TRỌNG SỐ — `network.graph_traversal` chỉ BFS/DFS **không** trọng số; `dijkstra_weighted_shortest_path` vẫn CAPABILITY_GAP. |

## Áp dụng

- Bộ đánh giá M17 (`datasets/m17_catalog` — Wave 3) sẽ mang các kỳ vọng MỚI
  trực tiếp (dataset riêng, không đụng M16).
- Nếu tương lai chạy lại **live** trên các case M16 ở bảng "gap → supported",
  kết quả `unsupported` KHÔNG còn là "đúng kỳ vọng" — dùng overlay này để
  chấm lại, KHÔNG sửa artifact M16 gốc.
- Audit W0 (`docs/evaluation/m17/wave0/`) là **bản ghi lịch sử** đã FROZEN
  (SHA-256 pin) — vẫn phản ánh trạng thái 4 intentional-gap tại thời điểm W0.
  Audit W1 (nếu sinh) sẽ phản ánh trạng thái mới (2 intentional-gap còn lại).
