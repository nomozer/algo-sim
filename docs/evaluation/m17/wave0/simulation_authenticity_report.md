# Báo cáo Authenticity Audit — M17-Lite Wave 0 (offline)

Sinh tự động từ `app/evaluation/authenticity_*` — chạy TOÀN BỘ case
matrix qua production `run_pipeline` (bất biến #22) với provider
scripted per-case. KHÔNG sửa tay file này — chạy
`python scripts/generate_m17_wave0_artifacts.py`.

## Tổng quan

- Tổng case: **55**
- Near-miss gap recall: **4/4**
- Chặn oan trên ok-archetype: **0**
- Envelope integrity (id concrete, không token): **48/48**
- Production parity (#22): **55/55**
- Generic leak vô điều kiện: **0**
- Generic leak CÓ ĐIỀU KIỆN (probe adversarial): **1**

## Phân loại per-target

| Target | Phân loại |
|---|---|
| `algorithm.binary_search` | REAL |
| `algorithm.bubble_sort` | REAL |
| `algorithm.count_if` | REAL |
| `algorithm.find_max` | REAL |
| `algorithm.find_min` | REAL |
| `algorithm.insertion_sort` | REAL |
| `algorithm.linear_search` | REAL |
| `algorithm.scan` | REAL |
| `algorithm.sum_if` | REAL |
| `binary.decimal_to_binary` | REAL |
| `generic.rule_scene` | PARTIAL |
| `logic.and_gate` | REAL |
| `network.packet_routing` | REAL |
| `network.protocol_encapsulation` | REAL |

## Theo archetype

| Archetype | Đạt/Tổng |
|---|---|
| boundary | 4/4 |
| changed_input | 14/14 |
| direct | 14/14 |
| leak_control | 2/2 |
| leak_probe | 0/1 (probe) |
| near_miss | 4/4 |
| paraphrase | 14/14 |
| refusal_control | 2/2 |

## Phát hiện chính (W0)

1. **Regression duyệt cây (honest):** analyze trung thực (`result_ownership=algorithmic`) → computation gate chặn fail-closed, KHÔNG dựng Điểm/Đoạn nối/Vật di chuyển. ✔
2. **Probe adversarial duyệt cây:** khi analyze khai man (`ownership=provided` + scene staging roles), generic dựng cảnh và trả ok → **CONDITIONAL_LEAK_CONFIRMED** (pin bằng test `test_pin_adversarial_tree_probe_conditional_leak`). Gate hiện tại fail-closed THEO TÍN HIỆU CẤU TRÚC — bảo chứng phụ thuộc analyze trung thực (bằng chứng live M16: 24/24 analyze trung thực). Fix dài hạn = family `tree_traversal` (Wave 2); mọi siết gate thêm là production change cần user duyệt.
3. **4/4 intentional gap** (selection/quick/unspecified sort, cơ số ≠ 2) bị chặn đúng mã `gate_mechanism_ownership`.
4. **Đối chứng representation** (vẽ sơ đồ khai báo) KHÔNG bị chặn oan.
