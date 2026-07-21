# M17-RC1 §C — Failure ledger

Case chạy: **77** · không khớp kỳ vọng: **1**

| Case | Slot | Family | Kỳ vọng | Thực tế | error_code | Ghi chú |
|---|---|---|---|---|---|---|
| `rc1c-scan-max-and-min` | semantic_completeness | single_pass_scan | unsupported/multiple_operations_not_supported | ok→algorithm.find_max | `—` | kỳ vọng unsupported, thực tế ok→algorithm.find_max |

## Điều kiện dừng (§C stop conditions)

| Điều kiện | Giá trị | Kích hoạt? |
|---|---|---|
| COVERED_FAIL ở supported_canonical | **0** | không |
| generic_leak | **0** | không |
| false_positive_simulation | **1** | **CÓ** |
| semantic_loss | **1** | **CÓ** |
| result_leakage | **0** | không |
| executor ownership sai (engine BROKEN) | **0** | không |
