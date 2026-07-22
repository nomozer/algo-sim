# M17-RC1 §L1 — Analyze Sufficiency Reality Check (LIVE)

Chỉ gọi **production analyze**. Không classify, không simulate, không
executor ⇒ không case nào tạo được simulation.

- Môi trường: `local python 3.12.10 on Windows (KHÔNG qua container — Docker Desktop không chạy)`
- git SHA: `a274992b1f033fdbde2c4bb3d9e0274349284c1e` · model: `gemini-2.5-flash`
- HTTP: **14/16** · retry: **0/1** · lượt logic: **14/14**
- Kết luận: **PASS**

## Case hợp lệ (6 case × 2 lần)

- sufficiency PASS: **12/12**
- operation đúng: **12/12**
- dữ liệu cụ thể còn nguyên: **12/12**
- dùng generated_default: **0** (phải 0)
- case cho hai quyết định khác nhau: **không**

## Đối chứng thiếu dữ kiện (2 case × 1 lần)

- sufficiency FAIL: **2/2**
- có bằng chứng BỊA: **không**

## Từng lượt

| Case | Lần | Quyết định | reason_code | operation đúng | dữ liệu nguyên | thiếu |
|---|---|---|---|---|---|---|
| `L1-V1-finite-sequence` | 1 | **PASS** | `—` | ✓ | ✓ | — |
| `L1-V1-finite-sequence` | 2 | **PASS** | `—` | ✓ | ✓ | — |
| `L1-V2-comparison-sort` | 1 | **PASS** | `—` | ✓ | ✓ | — |
| `L1-V2-comparison-sort` | 2 | **PASS** | `—` | ✓ | ✓ | — |
| `L1-V3-base-conversion` | 1 | **PASS** | `—` | ✓ | ✓ | — |
| `L1-V3-base-conversion` | 2 | **PASS** | `—` | ✓ | ✓ | — |
| `L1-V4-boolean-expression` | 1 | **PASS** | `—` | ✓ | ✓ | — |
| `L1-V4-boolean-expression` | 2 | **PASS** | `—` | ✓ | ✓ | — |
| `L1-V5-graph-traversal` | 1 | **PASS** | `—` | ✓ | ✓ | — |
| `L1-V5-graph-traversal` | 2 | **PASS** | `—` | ✓ | ✓ | — |
| `L1-V6-tree-traversal` | 1 | **PASS** | `—` | ✓ | ✓ | — |
| `L1-V6-tree-traversal` | 2 | **PASS** | `—` | ✓ | ✓ | — |
| `L1-I1-sequence-missing` | 1 | **FAIL** | `input_insufficient` | ✓ | ✓ | finite_sequence |
| `L1-I2-tree-missing` | 1 | **FAIL** | `structure_insufficient` | ✓ | ✓ | tree_structure |
