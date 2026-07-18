# M15 — Public Capability Contract Formalization & Migration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Hình thức hoá contract cho 12 concrete entry non-sorting còn lại (ownership máy-đọc mức membership + config_contract_version + taxonomy cơ chế canonical namespaced + gate consistency hai mã lỗi + locks), theo đúng design rev2 `cd1b8e5`, không viết lại executor/renderer nào.

**Architecture:** Một module taxonomy mới (`mechanisms.py`) là nguồn canonical duy nhất; alias một chiều legacy→canonical tại đúng MỘT boundary (`canonical_mechanism`); gate/descriptor/cross-lock chỉ so canonical; bề mặt analyze giữ legacy sorting values. Pipeline thêm một check consistency cho direct route (3 nhánh, 2 mã lỗi) + một lượt bounded reclassification. Mọi wave sau W1 là descriptor/lock/proof thuần offline.

**Tech Stack:** Python (FastAPI backend, pytest), TypeScript (vitest — chỉ test/artifact, FE production diff = 0), Gemini structured output (chỉ Task 11 live, opt-in).

**Design nguồn:** `docs/superpowers/specs/2026-07-18-m15-public-capability-contract-formalization-design.md` (rev2, commit `cd1b8e5`). Plan này KHÔNG được lệch design; nếu một bước buộc lệch → DỪNG, báo user (stop-condition).

## Global Constraints (áp cho MỌI task — copy từ 13 khóa user + design rev2)

1. `canonical_mechanism` là compatibility boundary DUY NHẤT: legacy sorting → canonical namespaced; canonical giữ nguyên; KHÔNG normalize rải rác (mọi consumer gọi đúng hàm này); gate/descriptor/cross-lock CHỈ dùng canonical; `analysis` trong envelope KHÔNG bị mutate; alias một chiều — không phải taxonomy thứ hai.
2. Mọi analyze-exposed value (≠ "none") sau normalize phải thoả ĐÚNG MỘT trong hai: được ≥1 membership/selector sở hữu, HOẶC ∈ `INTENTIONAL_GAP_MECHANISMS` khai tường minh. Không unowned value nào không được khai.
3. Cross-family mismatch: `ROUTE_MECHANISM_FAMILY_MISMATCH`; KHÔNG gọi simulate trên target mâu thuẫn; bounded reclassification đúng TỐI ĐA 1 lượt; analyze KHÔNG chạy lại; vẫn mismatch → fail-closed `capability_gap`; prescribed=null → 0 classify call thêm; không recursion/loop.
4. Same-family unowned: `GATE_MECHANISM_OWNERSHIP`; không simulate; structured observer event; honest gap.
5. Observer events có cấu trúc cho: raw prescribed, canonical, family mismatch, reclassify attempt/result, ownership gate. KHÔNG categorise chủ yếu bằng string message (bài học 7f).
6. `config_contract_version` = JSON shape + VALIDATION POLICY; per-entry locks bắt buộc (required fields / bounds / normalization / learner-facing annotation / semantic preconditions).
7. Binary-search unsorted policy test chứng minh: normalize tất định, labels↔value giữ liên kết, annotation tồn tại, trace chạy trên input đã normalize, KHÔNG refuse.
8. Hex/octal: offline CẢ HAI → capability_gap, không generic fallback; wrong-family direct route → `ROUTE_MECHANISM_FAMILY_MISMATCH`; binary direct route + `non_binary_base` → ownership gap; live tối thiểu MỘT non-binary case, ưu tiên hex.
9. `CACHE_VERSION` 11→12 bump ĐÚNG MỘT LẦN, CHỈ khi toàn bộ contract/prompt/gate W1 đã đồng bộ (Task 10) — không bump giữa chừng.
10. W2 scan: không selector, không spec mới, giữ specialized surfaces + `algorithm.scan`, không thêm predict/what-if.
11. W3 Boolean: giữ dual surface, không nested truth-table production gate.
12. W4 Network: BFS unweighted ownership; weighted shortest path = gap; không Dijkstra; giữ 2D/3D hiện tại.
13. W5: generic representation authority proof; sorting PILOT→SUPPORTED (kèm claim boundary n=4); docs close; KHÔNG mở M16.

Chuẩn chung: R0 + bất biến #20/#21/#22 nguyên vẹn; offline-first (pytest/vitest 0 network); test tiếng Việt đặt tên theo hành vi; commit KHÔNG có Co-Authored-By trailer; FE production diff = 0 (chỉ `capability-descriptors.json` + test); baseline vào M15: pytest 450 · vitest 403 · build sạch — task nào thấy baseline đỏ không liên quan → DỪNG báo user.

## File Structure (quyết định phân rã — khoá tại đây)

| File | Trách nhiệm |
|---|---|
| `backend/app/simulation/mechanisms.py` (MỚI) | Taxonomy canonical `FAMILY_MECHANISMS` + `INTENTIONAL_GAP_MECHANISMS` + `LEGACY_ALIASES` + `canonical_mechanism` + `mechanism_family` + `analyze_exposed_values` + `FORMALIZED_FAMILIES` (registry tiến độ wave). KHÔNG import catalog (chống vòng). |
| `backend/app/simulation/descriptor.py` | +`owned_mechanisms` trên `FamilyMembership`. |
| `backend/app/simulation/catalog.py` | +kwarg `config_contract_version` trên `SimSpec`; khai version 14 entry; khai owned theo wave; mở rộng `capability_descriptors()`. |
| `backend/app/simulation/families/sorting.py` | `MECH_*` → canonical (import từ mechanisms.py); `PROC_*`/`PRESCRIBED_PROCEDURES` legacy GIỮ NGUYÊN GIÁ TRỊ. |
| `backend/app/simulation/mechanism_gate.py` | Normalize qua `canonical_mechanism`; +`check_mechanism_consistency_for_target` (3 nhánh, 2 mã). |
| `backend/app/simulation/error_codes.py` | +`ROUTE_MECHANISM_FAMILY_MISMATCH`. |
| `backend/app/ai/pipeline.py` | ANALYZE_SCHEMA enum ← `analyze_exposed_values()`; wiring direct-gate + reclassify 1 lượt; events mới; `stage_classify(..., extra_note=None)`. |
| `backend/app/ai/skills/analyze.md` | CHỈ THÊM khối `positional_representation.*` (khối sorting nguyên văn). |
| `backend/scripts/generate_capability_descriptors.py` + `frontend/src/simulations/capability-descriptors.json` | Artifact thêm owned_mechanisms + config_contract_version (regenerate). |
| `backend/app/evaluation/datasets/capability.py`, `live.py` | Case hex/octal/binary-positive/unsorted + suite `m15_wave1`. |
| `backend/app/simulation/coverage.py` | W5: sorting SUPPORTED + note. |
| Test mới: `tests/test_mechanisms.py`, `tests/test_pipeline_mechanism_consistency.py`, `tests/test_algo_entry_policy_locks.py`, `tests/test_scan_conformance.py`, `tests/test_boolean_dual_surface.py`, `tests/test_network_ownership.py`, `tests/test_generic_representation_authority.py`; mở rộng: `test_descriptor.py`, `test_family_registry.py`, `test_capability_descriptors.py`, `test_mechanism_gate.py`, `test_analyze_prescribed_procedure.py`, `test_datasets.py`, `test_coverage_matrix.py`. |

---

# WAVE 1 — Hạ tầng + binary + binary_search (Task 1–11)

### Task 1: Mechanism taxonomy + intentional-gap registry + alias boundary

**Mục tiêu:** Nguồn canonical duy nhất cho mọi mechanism id; alias legacy→canonical một chiều; registry gap-cố-ý; enum analyze dẫn xuất.

**Files:**
- Create: `backend/app/simulation/mechanisms.py`
- Test: `backend/tests/test_mechanisms.py`

**Interfaces — Produces (task sau dựa vào, đúng chính tả):**
```python
FAMILY_MECHANISMS: dict[FamilyId, tuple[str, ...]]
INTENTIONAL_GAP_MECHANISMS: frozenset[str]
LEGACY_ALIASES: dict[str, str]
NO_PRESCRIPTION = "none"
FORMALIZED_FAMILIES: frozenset[FamilyId]        # W1 khởi tạo; wave sau MỞ RỘNG
def canonical_mechanism(raw: str | None) -> str | None
def mechanism_family(canonical: str) -> str      # "comparison_sort.x" -> "comparison_sort"
def analyze_exposed_values() -> tuple[str, ...]  # nguồn enum ANALYZE_SCHEMA
```

**Dependency:** không (task nền). **Invariant bảo vệ:** khóa 1, 2; anti-pattern #1 (enum dẫn xuất, không viết tay ở schema).

- [ ] **Step 1 — test trước** (`tests/test_mechanisms.py`):

```python
from app.simulation.descriptor import FamilyId
from app.simulation import mechanisms as M

def test_canonical_id_dung_dang_namespace_va_thuoc_taxonomy():
    for fam, mechs in M.FAMILY_MECHANISMS.items():
        for m in mechs:
            ns, _, name = m.partition(".")
            assert ns == fam.value and name  # đúng "<family_id>.<mechanism>"

def test_alias_mot_chieu_chi_sorting_va_dich_thuoc_taxonomy():
    all_canonical = {m for ms in M.FAMILY_MECHANISMS.values() for m in ms}
    for legacy, canon in M.LEGACY_ALIASES.items():
        assert "." not in legacy                     # nguồn là bare value
        assert canon in all_canonical                # đích ∈ taxonomy
        assert M.mechanism_family(canon) == "comparison_sort"  # không alias ngoài sorting
    assert set(M.LEGACY_ALIASES) == {
        "adjacent_compare_swap", "shift_into_sorted_prefix",
        "select_extreme_repeated", "partition_recursive", "other_unspecified",
    }

def test_canonical_mechanism_normalize_va_passthrough():
    assert M.canonical_mechanism(None) is None
    assert M.canonical_mechanism("none") is None
    assert M.canonical_mechanism("adjacent_compare_swap") == "comparison_sort.adjacent_compare_swap"
    assert M.canonical_mechanism("comparison_sort.adjacent_compare_swap") == "comparison_sort.adjacent_compare_swap"
    assert M.canonical_mechanism("positional_representation.non_binary_base") == "positional_representation.non_binary_base"

def test_intentional_gap_thuoc_taxonomy_va_khong_giao_alias_owned_w1():
    all_canonical = {m for ms in M.FAMILY_MECHANISMS.values() for m in ms}
    assert M.INTENTIONAL_GAP_MECHANISMS <= all_canonical

def test_analyze_exposed_gom_legacy_sorting_none_va_positional():
    vals = M.analyze_exposed_values()
    assert "none" in vals
    assert "adjacent_compare_swap" in vals           # legacy GIỮ NGUYÊN (rev2 điểm 2)
    assert "comparison_sort.adjacent_compare_swap" not in vals  # canonical KHÔNG lộ ra analyze trong M15
    assert "positional_representation.binary_positional_weights" in vals
    assert "positional_representation.non_binary_base" in vals
```

- [ ] **Step 2 — chạy, xác nhận FAIL** (`ModuleNotFoundError`): `.venv/Scripts/python -m pytest tests/test_mechanisms.py -v`
- [ ] **Step 3 — implement** `backend/app/simulation/mechanisms.py`:

```python
"""M15 — taxonomy cơ chế canonical namespaced (nguồn DUY NHẤT) + alias boundary.

Khóa 1: canonical_mechanism là compatibility boundary duy nhất — legacy sorting
(live-verified M14) → canonical; canonical passthrough; alias MỘT CHIỀU, không
phải taxonomy thứ hai. Gate/descriptor/cross-lock CHỈ so canonical.
Khóa 2: giá trị analyze-exposed unowned phải nằm trong INTENTIONAL_GAP_MECHANISMS.
KHÔNG import catalog (chống vòng import — cross-lock với catalog ở test).
"""
from __future__ import annotations

from app.simulation.descriptor import FamilyId

NO_PRESCRIPTION = "none"

FAMILY_MECHANISMS: dict[FamilyId, tuple[str, ...]] = {
    FamilyId.COMPARISON_SORT: (
        "comparison_sort.adjacent_compare_swap",
        "comparison_sort.shift_into_sorted_prefix",
        "comparison_sort.select_extreme_repeated",
        "comparison_sort.partition_recursive",
        "comparison_sort.other_unspecified",
    ),
    FamilyId.POSITIONAL_REPRESENTATION: (
        "positional_representation.binary_positional_weights",
        "positional_representation.non_binary_base",
    ),
    FamilyId.INTERVAL_ELIMINATION: ("interval_elimination.halve_sorted_interval",),
    FamilyId.SINGLE_PASS_SCAN: (
        "single_pass_scan.track_extreme",
        "single_pass_scan.accumulate_conditional",
        "single_pass_scan.count_conditional",
        "single_pass_scan.find_equal_early_stop",
        "single_pass_scan.configured_single_pass",
    ),
    FamilyId.BOOLEAN_COMPOSITION: (
        "boolean_composition.single_gate_truth_table",
        "boolean_composition.composed_rule_dag",
    ),
    FamilyId.GRAPH_TRAVERSAL: ("graph_traversal.unweighted_hop_bfs",),
    FamilyId.LAYERED_PDU_TRANSFORM: (
        "layered_pdu_transform.encapsulate_decapsulate_4layer",
    ),
    FamilyId.STRUCTURAL_PROGRESSIVE_REPRESENTATION: (
        "structural_progressive_representation.reveal_sequence",
        "structural_progressive_representation.move_along_path",
    ),
}

# Khóa 2 — giá trị CỐ Ý không target nào sở hữu (gap-trigger, khai tường minh)
INTENTIONAL_GAP_MECHANISMS: frozenset[str] = frozenset({
    "comparison_sort.select_extreme_repeated",
    "comparison_sort.partition_recursive",
    "comparison_sort.other_unspecified",
    "positional_representation.non_binary_base",
})

# Khóa 1 — alias MỘT CHIỀU legacy→canonical, CHỈ namespace comparison_sort (M14 compat)
LEGACY_ALIASES: dict[str, str] = {
    "adjacent_compare_swap": "comparison_sort.adjacent_compare_swap",
    "shift_into_sorted_prefix": "comparison_sort.shift_into_sorted_prefix",
    "select_extreme_repeated": "comparison_sort.select_extreme_repeated",
    "partition_recursive": "comparison_sort.partition_recursive",
    "other_unspecified": "comparison_sort.other_unspecified",
}

# Registry tiến độ formalization — wave sau MỞ RỘNG; W5 lock == toàn bộ FamilyId
FORMALIZED_FAMILIES: frozenset[FamilyId] = frozenset({
    FamilyId.COMPARISON_SORT,           # M14 (reference)
    FamilyId.POSITIONAL_REPRESENTATION, # W1
    FamilyId.INTERVAL_ELIMINATION,      # W1
})


def canonical_mechanism(raw: str | None) -> str | None:
    """Boundary DUY NHẤT legacy→canonical. None/"none" → None (không ép cơ chế)."""
    if raw is None or raw == NO_PRESCRIPTION:
        return None
    return LEGACY_ALIASES.get(raw, raw)


def mechanism_family(canonical: str) -> str:
    return canonical.split(".", 1)[0]


def analyze_exposed_values() -> tuple[str, ...]:
    """Nguồn enum `prescribed_procedure` của ANALYZE_SCHEMA (dẫn xuất — anti-pattern #1).
    M15: legacy sorting GIỮ NGUYÊN (rev2 điểm 2) + none + positional namespaced."""
    return (
        NO_PRESCRIPTION,
        *LEGACY_ALIASES.keys(),
        "positional_representation.binary_positional_weights",
        "positional_representation.non_binary_base",
    )
```

- [ ] **Step 4 — chạy PASS** rồi full suite: `.venv/Scripts/python -m pytest` (kỳ vọng 450+5 pass, 0 đỏ).
- [ ] **Step 5 — Commit checkpoint:** `M15 Task 1: mechanisms.py — taxonomy canonical namespaced 8 family + INTENTIONAL_GAP registry + alias một chiều legacy sorting + analyze_exposed_values dẫn xuất; pytest +5`

**Acceptance:** 5 test mới xanh; chưa consumer nào đổi hành vi. **Rollback boundary:** revert commit (file mới + test, không chạm gì khác).

---

### Task 2: `owned_mechanisms` (membership) + `config_contract_version` (SimSpec) + sorting canonical rewire

**Mục tiêu:** Mở rộng descriptor; sorting nội bộ chuyển canonical mà `m14_sorting`/`test_mechanism_gate` hiện có XANH NGUYÊN TRẠNG (proof alias boundary).

**Files:**
- Modify: `backend/app/simulation/descriptor.py` (FamilyMembership), `backend/app/simulation/families/sorting.py`, `backend/app/simulation/mechanism_gate.py` (normalize), `backend/app/simulation/catalog.py`
- Test: mở rộng `backend/tests/test_descriptor.py`, `backend/tests/test_family_registry.py`

**Interfaces — Produces:** `FamilyMembership.owned_mechanisms: tuple[str, ...] = ()`; `SimSpec(..., config_contract_version: str = "")`; sorting `MECH_ADJACENT_SWAP = "comparison_sort.adjacent_compare_swap"` (import mechanisms), `PROC_*`/`PRESCRIBED_PROCEDURES` GIỮ giá trị legacy.

**Dependency:** Task 1. **Invariant:** khóa 1 (chỉ canonical trong descriptor/gate); Control 3 rev2 (m14 offline nguyên trạng); bất biến #4.

- [ ] **Step 1 — test trước** (thêm vào `test_descriptor.py` + `test_family_registry.py`):

```python
def test_membership_owned_mechanisms_canonical_va_mechanism_id_thuoc_owned():
    from app.simulation.catalog import CATALOG
    from app.simulation import mechanisms as M
    all_canonical = {m for ms in M.FAMILY_MECHANISMS.values() for m in ms}
    for spec in CATALOG.values():
        for mem in spec.family_memberships:
            for om in mem.owned_mechanisms:
                assert om in all_canonical
                assert M.mechanism_family(om) == mem.family_id.value
            if mem.mechanism_id is not None and mem.owned_mechanisms:
                assert mem.mechanism_id in mem.owned_mechanisms

def test_config_contract_version_khai_du_14_entry():
    from app.simulation.catalog import CATALOG
    assert len(CATALOG) == 14
    for spec in CATALOG.values():
        assert spec.config_contract_version  # ≠ "" (K1 — shape + VALIDATION POLICY, §C2 rev2)

def test_selector_owned_bang_hop_owned_cua_variant_membership():
    from app.simulation.catalog import CATALOG
    from app.simulation.families import FAMILY_SELECTORS
    sel = FAMILY_SELECTORS["comparison_sort"]
    union = set()
    for var in sel.variants:
        spec = CATALOG[var.concrete_simulation_id]
        for mem in spec.family_memberships:
            if mem.family_id.value == "comparison_sort":
                union |= set(mem.owned_mechanisms)
    assert set(sel.owned_mechanisms) == union  # cross-lock C1
```

- [ ] **Step 2 — FAIL** (thiếu field/kwarg).
- [ ] **Step 3 — implement:**
  - `descriptor.py`: thêm `owned_mechanisms: tuple[str, ...] = ()` vào `FamilyMembership` (docstring: "tập cơ chế membership SỞ HỮU — CHỈ canonical id").
  - `sorting.py`: `from app.simulation.mechanisms import FAMILY_MECHANISMS`… thay bằng import hằng trực tiếp:
    ```python
    from app.simulation import mechanisms as _M
    MECH_ADJACENT_SWAP = "comparison_sort.adjacent_compare_swap"
    MECH_SHIFT_INSERT = "comparison_sort.shift_into_sorted_prefix"
    # PROC_* GIỮ NGUYÊN GIÁ TRỊ LEGACY (live-verified M14 — rev2 điểm 2):
    PROC_ADJACENT_SWAP = "adjacent_compare_swap"
    PROC_SHIFT_INSERT = "shift_into_sorted_prefix"
    # PRESCRIBED_PROCEDURES giữ nguyên tuple legacy hiện có.
    ```
    (assert nhẹ trong module: `_M.LEGACY_ALIASES[PROC_ADJACENT_SWAP] == MECH_ADJACENT_SWAP` — chống hai nguồn trôi nhau.)
  - `mechanism_gate.py`: cả hai hàm hiện có normalize đầu vào — `prescribed = canonical_mechanism(analysis.get("prescribed_procedure"))`; `if prescribed is None: return None` (thay `_NO_PRESCRIPTION` tuple); so sánh với owned/variant.mechanism_id nay đều canonical.
  - `catalog.py`: `SimSpec.__init__` +kwarg `config_contract_version: str = ""`; khai cho 14 entry: 9 entry algorithm (8 + scan) — 8 dùng `"algo-cfg-1"`, scan `"scan-1.0"`; `"logic-cfg-1"`, `"binary-cfg-1"`, `"net-cfg-1"`, `"encap-cfg-1"`, generic `"dsl-1.0"`. Khai `owned_mechanisms` W1-scope: bubble `(MECH_ADJACENT_SWAP,)`, insertion `(MECH_SHIFT_INSERT,)` (trong `_ALGO_META`), binary_search `("interval_elimination.halve_sorted_interval",)`, binary.decimal_to_binary `("positional_representation.binary_positional_weights",)`.
- [ ] **Step 4 — PASS + toàn suite:** đặc biệt `test_pipeline_sorting.py`, `test_mechanism_gate.py`, `test_sorting_family_spec.py`, `test_analyze_prescribed_procedure.py` phải xanh **KHÔNG SỬA MỘT DÒNG** (acceptance cốt lõi — alias boundary gánh trọn). Nếu bất kỳ test m14 nào phải sửa → vi phạm Control 3, DỪNG xem lại.
- [ ] **Step 5 — Commit:** `M15 Task 2: owned_mechanisms membership-level + config_contract_version 14 entry + sorting canonical nội bộ qua alias boundary (m14 tests xanh NGUYÊN TRẠNG — proof rev2 điểm 2); gate normalize canonical_mechanism`

**Acceptance:** 3 test mới xanh; 0 test m14 bị sửa. **Rollback:** revert commit (descriptor/catalog/sorting/gate là một khối nguyên tử — không tách được vì gate phải normalize cùng lúc owned chuyển canonical).

---

### Task 3: Artifact + cross-locks (D2/C1/K2 + khóa 2 machine-check)

**Mục tiêu:** `capability-descriptors.json` mang owned + version; lock "mọi analyze-exposed value owned-XOR-intentional-gap" chạy bằng máy.

**Files:**
- Modify: `backend/app/simulation/catalog.py` (`capability_descriptors()`), `backend/scripts/generate_capability_descriptors.py` (nếu cần field mới), `frontend/src/simulations/capability-descriptors.json` (REGENERATE — artifact, không viết tay)
- Test: mở rộng `backend/tests/test_capability_descriptors.py`; FE cross-lock hiện có tự ăn JSON mới (vitest)

**Dependency:** Task 2. **Invariant:** khóa 2; C4 M14 (artifact sinh-từ-nguồn, production FE không import); sync-lock chống drift.

- [ ] **Step 1 — test trước:**

```python
def test_artifact_mang_owned_va_version_moi_entry():
    from app.simulation.catalog import capability_descriptors
    d = capability_descriptors()
    for sim_id, t in d["runtime_targets"].items():
        assert "config_contract_version" in t and t["config_contract_version"]
        for mem in t["family_memberships"]:
            assert "owned_mechanisms" in mem  # có thể () trước W2–W4, nhưng field phải tồn tại

def test_analyze_exposed_owned_xor_intentional_gap():
    """Khóa 2 — đúng MỘT trong hai, không giá trị mồ côi."""
    from app.simulation.catalog import CATALOG
    from app.simulation.families import FAMILY_SELECTORS
    from app.simulation import mechanisms as M
    owned_everywhere = set()
    for spec in CATALOG.values():
        for mem in spec.family_memberships:
            owned_everywhere |= set(mem.owned_mechanisms)
    for sel in FAMILY_SELECTORS.values():
        owned_everywhere |= set(sel.owned_mechanisms)
    for raw in M.analyze_exposed_values():
        canon = M.canonical_mechanism(raw)
        if canon is None:
            continue  # "none"
        is_owned = canon in owned_everywhere
        is_gap = canon in M.INTENTIONAL_GAP_MECHANISMS
        assert is_owned != is_gap, f"{raw}→{canon}: owned={is_owned} gap={is_gap} (phải đúng MỘT)"

def test_formalized_families_owned_khong_rong():
    """K1 theo pha — family đã formalize thì membership tương ứng owned ≠ ()."""
    from app.simulation.catalog import CATALOG
    from app.simulation.mechanisms import FORMALIZED_FAMILIES
    for spec in CATALOG.values():
        for mem in spec.family_memberships:
            if mem.family_id in FORMALIZED_FAMILIES:
                assert mem.owned_mechanisms, f"{spec.simulation_id}/{mem.family_id.value}"
```

- [ ] **Step 2 — FAIL** (artifact thiếu field). **Step 3 —** mở rộng `_member()`/targets trong `capability_descriptors()` (+`owned_mechanisms`, +`config_contract_version`), chạy `.venv/Scripts/python scripts/generate_capability_descriptors.py`, commit JSON regenerate. **Step 4 — PASS + vitest** (`npm test` — FE cross-lock ăn JSON mới; nếu FE lock cần biết field mới thì SỬA TEST FE, không sửa production). **Step 5 — Commit:** `M15 Task 3: artifact descriptors + owned/version + lock khóa-2 owned-XOR-intentional-gap + K1 lock theo pha FORMALIZED_FAMILIES; JSON regenerate, production FE không đổi`

**Acceptance:** sync-lock BE + cross-lock FE xanh; `git diff --stat frontend/src` chỉ có `.json` + test. **Rollback:** revert commit + regenerate lại JSON cũ.

---

### Task 4: Structured error code + analyze-event canonical

**Mục tiêu:** Mã `ROUTE_MECHANISM_FAMILY_MISMATCH`; event `analyze_done` mang cả raw lẫn canonical (khóa 5 — không categorise bằng string).

**Files:**
- Modify: `backend/app/simulation/error_codes.py`, `backend/app/ai/pipeline.py` (chỉ `_emit` analyze_done)
- Test: mở rộng `backend/tests/test_mechanism_gate.py` (enum), `backend/tests/test_eval_convergence.py` (event)

**Dependency:** Task 1. **Invariant:** khóa 5; bất biến #22 (observer thụ động — thêm FIELD data, không đổi hành vi).

- [ ] **Step 1 — test trước:**

```python
def test_error_code_route_mismatch_ton_tai():
    from app.simulation.error_codes import ErrorCode
    assert ErrorCode.ROUTE_MECHANISM_FAMILY_MISMATCH.value == "route_mechanism_family_mismatch"

def test_analyze_done_event_mang_raw_va_canonical(monkeypatch):
    # mock call_gemini trả analysis có prescribed_procedure="adjacent_compare_swap"
    # (khuôn mock sẵn có của test_eval_convergence) → observer.events chứa
    # analyze_done với prescribed_procedure="adjacent_compare_swap"
    # VÀ canonical_prescribed="comparison_sort.adjacent_compare_swap"
```

- [ ] **Step 2 — FAIL. Step 3 —** thêm enum member (đặt cạnh `MECHANISM_VARIANT_MISMATCH`, comment "# E2 nhánh 3 — analyze family ↔ classify target family mâu thuẫn"); `_emit(observer, "analyze_done", ..., canonical_prescribed=canonical_mechanism(analysis.get("prescribed_procedure")) ...)`. **Step 4 — PASS + suite. Step 5 — Commit:** `M15 Task 4: ROUTE_MECHANISM_FAMILY_MISMATCH + analyze_done mang canonical_prescribed (observer structured, không string-categorise)`

**Acceptance/Rollback:** 2 test xanh / revert commit.

---

### Task 5: `check_mechanism_consistency_for_target` (pure — 3 nhánh, 2 mã)

**Mục tiêu:** Hàm gate thuần cho direct route; T1/T3 mức unit + permissive-null.

**Files:**
- Modify: `backend/app/simulation/mechanism_gate.py`
- Test: mở rộng `backend/tests/test_mechanism_gate.py`

**Interfaces — Produces:**
```python
def check_mechanism_consistency_for_target(analysis: dict, spec) -> tuple[ErrorCode, str] | None
# None = đi tiếp; (GATE_MECHANISM_OWNERSHIP, msg) = cùng family không sở hữu;
# (ROUTE_MECHANISM_FAMILY_MISMATCH, msg) = khác family — caller KHÔNG được simulate.
```

**Dependency:** Task 2, 4. **Invariant:** khóa 3, 4; không keyword-patch (chỉ so tín hiệu cấu trúc đã canonical).

- [ ] **Step 1 — test trước:**

```python
from app.simulation.catalog import CATALOG
from app.simulation.error_codes import ErrorCode
from app.simulation.mechanism_gate import check_mechanism_consistency_for_target as check

def test_T1_non_binary_base_tren_binary_target_la_ownership_gap():
    r = check({"prescribed_procedure": "positional_representation.non_binary_base"},
              CATALOG["binary.decimal_to_binary"])
    assert r is not None and r[0] == ErrorCode.GATE_MECHANISM_OWNERSHIP

def test_T3_sorting_prescribed_tren_binary_target_la_family_mismatch():
    r = check({"prescribed_procedure": "adjacent_compare_swap"},  # legacy → alias
              CATALOG["binary.decimal_to_binary"])
    assert r is not None and r[0] == ErrorCode.ROUTE_MECHANISM_FAMILY_MISMATCH

def test_positional_tren_binary_search_la_family_mismatch():  # T2 phần pure
    r = check({"prescribed_procedure": "positional_representation.non_binary_base"},
              CATALOG["algorithm.binary_search"])
    assert r is not None and r[0] == ErrorCode.ROUTE_MECHANISM_FAMILY_MISMATCH

def test_T4_null_va_none_khong_chan_moi_direct_entry():
    for sim_id, spec in CATALOG.items():
        assert check({"prescribed_procedure": None}, spec) is None
        assert check({"prescribed_procedure": "none"}, spec) is None

def test_owned_hop_le_di_tiep():
    r = check({"prescribed_procedure": "positional_representation.binary_positional_weights"},
              CATALOG["binary.decimal_to_binary"])
    assert r is None
```

- [ ] **Step 2 — FAIL. Step 3 — implement** (trong `mechanism_gate.py`, cùng file với gate M14 — một nguồn message):

```python
def check_mechanism_consistency_for_target(analysis, spec):
    prescribed = canonical_mechanism(analysis.get("prescribed_procedure"))
    if prescribed is None:
        return None
    fam = mechanism_family(prescribed)
    fams = {m.family_id.value for m in spec.family_memberships}
    if fam not in fams:
        return (
            ErrorCode.ROUTE_MECHANISM_FAMILY_MISMATCH,
            "Cơ chế đề yêu cầu thuộc một họ năng lực khác với mô phỏng đã chọn — "
            "cần chọn lại mô phỏng đúng họ hoặc từ chối trung thực.",
        )
    owned: set[str] = set()
    for m in spec.family_memberships:
        if m.family_id.value == fam:
            owned |= set(m.owned_mechanisms)
    if prescribed not in owned:
        return (
            ErrorCode.GATE_MECHANISM_OWNERSHIP,
            "Đề yêu cầu một cơ chế mà engine tất định của mô phỏng này không sở hữu "
            "— hệ từ chối trung thực thay vì minh hoạ bằng cơ chế khác.",
        )
    return None
```

- [ ] **Step 4 — PASS + suite. Step 5 — Commit:** `M15 Task 5: check_mechanism_consistency_for_target 3 nhánh 2 mã (pure) — T1/T3/T4 + positional×binary_search mismatch; chỉ so canonical, không keyword`

**Acceptance:** 5 test xanh, hàm chưa được pipeline gọi (chưa đổi hành vi). **Rollback:** revert commit.

---

### Task 6: Pipeline wiring — direct gate + bounded reclassification (1 lượt)

**Mục tiêu:** Mismatch/ownership sống trong `run_pipeline`; reclassify đúng 1 lượt; analyze không chạy lại; events đầy đủ.

**Files:**
- Modify: `backend/app/ai/pipeline.py`
- Test: Create `backend/tests/test_pipeline_mechanism_consistency.py`

**Interfaces — Produces:** `stage_classify(text, analysis, api_key, extra_note: str | None = None)` (None → prompt y nguyên — hành vi cũ bit-một-bit); events mới: `gate_checked {gate: "route_mechanism", fired, reason_code}`, `reclassify_attempted {from_simulation_id, canonical_prescribed}`, `reclassify_result {status, simulation_id}`.

**Dependency:** Task 4, 5. **Invariant:** khóa 3, 4, 5; bất biến #22 (eval tự thấy gate mới qua observer — KHÔNG sửa harness); #5 (specialized không bị vạ lây: check chỉ nổ khi CÓ prescribed non-null).

- [ ] **Step 1 — test trước** (mock `pipeline.call_gemini` theo khuôn `test_eval_convergence.py`; mock đếm call theo skill name):

```python
async def test_T2_mismatch_khong_goi_simulate_va_reclassify_dung_1_luot():
    # analyze → prescribed="positional_representation.non_binary_base"
    # classify lần 1 → algorithm.binary_search; classify lần 2 (có extra_note) → VẪN binary_search
    # KỲ VỌNG: envelope unsupported, failure_category capability_gap,
    #   error_code "route_mechanism_family_mismatch";
    #   số call skill "simulate" == 0; số call skill "classify" == 2 (1 + đúng 1 reclassify);
    #   số call skill "analyze" == 1 (khóa 3: analyze KHÔNG chạy lại);
    #   observer có gate_checked route_mechanism fired + reclassify_attempted + reclassify_result.

async def test_reclassify_phuc_hoi_ve_dung_route():
    # analyze → prescribed="adjacent_compare_swap" (legacy sorting)
    # classify lần 1 → generic.rule_scene (misroute); lần 2 → "algorithm.comparison_sort"
    # KỲ VỌNG: đi tiếp nhánh selector, envelope ok concrete bubble/insertion
    #   (mock simulate family trả spec hợp lệ); reclassify_result status="ok".

async def test_reclassify_ra_unsupported_la_tu_choi_trung_thuc():
    # lần 2 classify trả status="unsupported" → envelope unsupported thường (reason của classify).

async def test_T4_prescribed_null_khong_them_call_classify():
    # đề thường mọi domain: prescribed=None → số call "classify" == 1, simulate chạy bình thường.

async def test_ownership_gap_khong_reclassify():
    # prescribed="positional_representation.non_binary_base" + classify → binary.decimal_to_binary
    # → capability_gap error_code "gate_mechanism_ownership"; classify == 1 (KHÔNG reclassify
    #   — cùng family, không phải mâu thuẫn route); simulate == 0.

async def test_khong_recursion():
    # sau reclassify, route mới lại mismatch → KHÔNG lượt 3: classify == 2, gap fail-closed.
```

- [ ] **Step 2 — FAIL. Step 3 — implement** trong `run_pipeline` (sau khối computation-gate, quanh `selector = selector_for_token(...)` hiện có):

```python
def _consistency_verdict(analysis, sim_id):
    sel = selector_for_token(sim_id)
    if sel is not None:
        pres = canonical_mechanism(analysis.get("prescribed_procedure"))
        if pres is not None and mechanism_family(pres) != sel.family_id.value:
            return (ErrorCode.ROUTE_MECHANISM_FAMILY_MISMATCH, _MISMATCH_MSG)
        return None  # ownership trong-family: tier-1 sẵn có của nhánh selector lo
    return check_mechanism_consistency_for_target(analysis, CATALOG[sim_id])

# trong run_pipeline, sau khi có simulation_id:
verdict = _consistency_verdict(analysis, simulation_id)
if verdict and verdict[0] == ErrorCode.ROUTE_MECHANISM_FAMILY_MISMATCH:
    _emit(observer, "gate_checked", gate="route_mechanism", fired=True,
          reason_code=verdict[0].value)
    _emit(observer, "reclassify_attempted", from_simulation_id=simulation_id,
          canonical_prescribed=canonical_mechanism(analysis.get("prescribed_procedure")))
    classification = await stage_classify(
        text, analysis, api_key,
        extra_note=("Phân tích xác định cơ chế đề yêu cầu thuộc họ năng lực khác với "
                    "simulation_id đã chọn. Chọn lại đúng mô phỏng biểu diễn cơ chế đó, "
                    "hoặc trả unsupported."))
    _emit(observer, "reclassify_result", status=classification.get("status"),
          simulation_id=classification.get("simulation_id"))
    if classification.get("status") != "ok":
        ...  # envelope unsupported thường (nhánh sẵn có)
    simulation_id = classification["simulation_id"]
    verdict = _consistency_verdict(analysis, simulation_id)
    if verdict is not None:   # vẫn lệch (mismatch HOẶC ownership) → fail-closed, KHÔNG lượt 3
        return {..."status": "unsupported", "failure_category": "capability_gap",
                "error_code": verdict[0].value, ...}
elif verdict:  # GATE_MECHANISM_OWNERSHIP — không reclassify
    _emit(observer, "gate_checked", gate="mechanism", fired=True, reason_code=verdict[0].value)
    return {..."status": "unsupported", "failure_category": "capability_gap",
            "error_code": verdict[0].value, ...}
```

  `stage_classify` thêm `extra_note` ghép cuối user message khi không None. `analysis` KHÔNG mutate, KHÔNG re-run (khóa 3).
- [ ] **Step 4 — PASS + TOÀN suite** (đặc biệt `test_pipeline_sorting.py` — nhánh selector với mismatch check mới KHÔNG được đổi kết quả case sorting hiện có vì prescribed sorting × selector sorting → cùng family → None). **Step 5 — Commit:** `M15 Task 6: direct-route mechanism consistency trong run_pipeline — mismatch→reclassify đúng 1 lượt→fail-closed, ownership→gap thẳng; events structured; prescribed=null 0 call thêm; T2 + no-recursion locks`

**Acceptance:** 6 test mới xanh; call-count asserts đúng; 0 test cũ sửa. **Rollback:** revert commit (wiring tách khỏi hàm pure Task 5).

---

### Task 7: ANALYZE_SCHEMA dẫn xuất + analyze.md khối positional

**Mục tiêu:** Enum analyze ← `analyze_exposed_values()`; prompt CHỈ THÊM khối positional (sorting nguyên văn).

**Files:**
- Modify: `backend/app/ai/pipeline.py` (ANALYZE_SCHEMA), `backend/app/ai/skills/analyze.md`
- Test: mở rộng `backend/tests/test_analyze_prescribed_procedure.py`

**Dependency:** Task 1, 6. **Invariant:** anti-pattern #1 (enum sinh, không viết tay); rev2 §F (khối sorting nguyên văn — diff analyze.md chỉ được THÊM).

- [ ] **Step 1 — test trước:**

```python
def test_analyze_schema_enum_dan_xuat_tu_mechanisms():
    from app.ai.pipeline import ANALYZE_SCHEMA
    from app.simulation.mechanisms import analyze_exposed_values
    assert ANALYZE_SCHEMA["properties"]["prescribed_procedure"]["enum"] == list(analyze_exposed_values())

def test_enum_giu_legacy_sorting_va_co_positional():
    from app.ai.pipeline import ANALYZE_SCHEMA
    e = ANALYZE_SCHEMA["properties"]["prescribed_procedure"]["enum"]
    assert "adjacent_compare_swap" in e and "positional_representation.non_binary_base" in e
```

- [ ] **Step 2 — FAIL. Step 3 —** pipeline: `"enum": list(analyze_exposed_values())` (bỏ import `PRESCRIBED_PROCEDURES` nếu không còn ai dùng — kiểm bằng grep); analyze.md thêm khối (đặt NGAY SAU khối sorting hiện có, dòng 15–21):

```markdown
- prescribed_procedure (bổ sung M15 — bài ĐỔI CƠ SỐ/biểu diễn vị trí): CHỈ đặt khi
  đề là bài đổi một số sang hệ đếm khác / biểu diễn theo trọng số vị trí.
  - "positional_representation.binary_positional_weights": đổi/biểu diễn sang HỆ NHỊ PHÂN
    (cơ số 2) — các bit trọng số 8/4/2/1.
  - "positional_representation.non_binary_base": đề yêu cầu cơ số KHÁC 2 (thập lục phân/16,
    bát phân/8, hay cơ số bất kỳ khác 2).
  - Bài không phải đổi cơ số → giữ nguyên quy tắc cũ (null / giá trị sắp xếp ở trên).
```

- [ ] **Step 4 — PASS + suite. Step 5 — Commit:** `M15 Task 7: ANALYZE_SCHEMA prescribed enum dẫn xuất analyze_exposed_values + analyze.md CHỈ THÊM khối positional (sorting nguyên văn); restart-backend note`

**Acceptance:** 2 test xanh; `git diff` analyze.md chỉ có dòng THÊM. **Rollback:** revert commit.

---

### Task 8: Per-entry policy locks (`algo-cfg-1`) + binary-search normalization proof + CORRECTNESS.md

**Mục tiêu:** Khóa 6 + 7 — policy từng `algorithm_id` dưới version chung; proof chuẩn-hoá-không-refuse đầy đủ (labels giữ liên kết, trace chạy trên normalized).

**Files:**
- Test: Create `backend/tests/test_algo_entry_policy_locks.py`; Create `frontend/src/simulations/domains/algorithm/binary-normalized.test.ts` (vitest, test-only)
- Modify: `docs/CORRECTNESS.md` (một mục policy)

**Dependency:** Task 2. **Invariant:** khóa 6, 7; R0 (validator server là chốt chặn); FE production diff = 0.

- [ ] **Step 1 — test trước (BE, parametrize đủ 8 id):**

```python
import pytest
from app.validation.simulation import validate_algorithm_config

@pytest.mark.parametrize("aid,missing_field,bad", [
    ("linear_search", "target", {"problem": {}, "data": {"array": [1, 2, 3]}}),
    ("binary_search", "target", {"problem": {}, "data": {"array": [1, 2, 3]}}),
    ("sum_if", "condition", {"problem": {}, "data": {"array": [1, 2, 3]}}),
    ("count_if", "condition", {"problem": {}, "data": {"array": [1, 2, 3]}}),
    ("bubble_sort", "order", {"problem": {}, "data": {"array": [3, 1, 2]}}),
    ("insertion_sort", "order", {"problem": {}, "data": {"array": [3, 1, 2]}}),
])
def test_required_field_theo_tung_entry_bi_ep(aid, missing_field, bad):
    config, err = validate_algorithm_config(aid, bad)
    assert config is None and missing_field in (err or "").replace('"', "")

@pytest.mark.parametrize("aid", ["find_max", "find_min", "sum_if", "count_if",
                                 "linear_search", "binary_search", "bubble_sort", "insertion_sort"])
def test_bounds_2_15_ap_moi_entry(aid):
    base = {"problem": {}, "data": {"array": [1], "target": 1,
            "condition": {"op": ">", "value": 0}, "order": "asc"}}
    config, err = validate_algorithm_config(aid, base)
    assert config is None  # 1 phần tử < 2

def test_binary_search_chuan_hoa_tat_dinh_labels_giu_lien_ket_va_annotation():
    """Khóa 7 — normalize + labels theo value + note sư phạm + KHÔNG refuse."""
    raw = {"problem": {}, "data": {"array": [9, 3, 7], "labels": ["chin", "ba", "bay"], "target": 7}}
    config, err = validate_algorithm_config("binary_search", raw)
    assert err is None and config is not None            # KHÔNG refuse
    assert config["data"]["array"] == [3, 7, 9]          # normalize tất định
    assert config["data"]["labels"] == ["ba", "bay", "chin"]  # label đi theo GIÁ TRỊ
    assert "sắp xếp trước" in (config["notes"] or "")    # annotation học sinh thấy
    # idempotent: chạy lại trên output → không đổi nữa, không note đúp
    config2, _ = validate_algorithm_config("binary_search", config)
    assert config2["data"]["array"] == [3, 7, 9]
```

  **FE vitest** (`binary-normalized.test.ts`, test-only): init module `algorithm.binary_search` với config đã normalize (array [3,7,9], target 7) → trace tồn tại, mọi step snapshot.array là dãy ĐÃ SẮP (trace chạy trên normalized input — khóa 7).
- [ ] **Step 2 — chạy: kỳ vọng PHẦN LỚN PASS NGAY** (đây là LOCK hành vi có sẵn [simulation.py:92-129] — pass-ngay là bằng chứng policy tồn tại; test nào FAIL nghĩa là phát hiện policy chưa có thật → DỪNG báo user, không lặng lẽ sửa validator). **Step 3 —** CORRECTNESS.md thêm mục "Chính sách normalize-not-refuse của binary_search" (2–3 dòng, dẫn test làm chốt). **Step 4 — suite đủ xanh cả BE+FE. Step 5 — Commit:** `M15 Task 8: per-entry policy locks algo-cfg-1 (required/bounds/normalize/annotation) + binary_search normalization proof BE+FE (labels giữ liên kết, trace trên normalized, không refuse) + CORRECTNESS.md`

**Acceptance:** locks xanh; FE diff chỉ file test. **Rollback:** revert (test+docs-only — không production code thay đổi).

---

### Task 9: Eval cases + suite `m15_wave1` + offline gap proofs

**Mục tiêu:** Khóa 8 offline: hex VÀ octal → capability_gap qua `run_pipeline` thật (mock LLM); suite live đăng ký sẵn.

**Files:**
- Modify: `backend/app/evaluation/datasets/capability.py` (4 case mới + tag), `backend/app/evaluation/live.py` (`SUITES += "m15_wave1"`), tag 2 case m14_sorting hiện có thêm `m15_wave1` (optional-live)
- Test: mở rộng `backend/tests/test_datasets.py` (admission), Create phần offline trong `backend/tests/test_pipeline_mechanism_consistency.py`

**Case mới (đủ admission rule — learning_objective/pedagogical_rationale/capability_family/complexity/result_mode/curriculum_area):**
- `m15-hex-gap` (group `unsupported`, tags `("m15_wave1",)`): "Đổi số 200 sang hệ thập lục phân và giải thích từng bước." → kỳ vọng refuse.
- `m15-octal-gap` (group `unsupported`, tags `("m15_wave1",)`): đề bát phân tương tự.
- `m15-binary-positive` (group `specialized`, expect `binary.decimal_to_binary`, tags `("m15_wave1",)`).
- `m15-binsearch-unsorted` (group `specialized`, expect `algorithm.binary_search`, tags `("m15_wave1",)`): đề dãy CHƯA sắp + tìm nhanh.

**Dependency:** Task 6, 7. **Invariant:** khóa 8; frozen DATASET không đụng; luật kết nạp.

- [ ] **Step 1 — test trước:** admission cho 4 case; offline proof (mock):

```python
async def test_hex_va_octal_offline_deu_capability_gap_khong_generic():
    # với TỪNG đề hex/octal: mock analyze trả prescribed="positional_representation.non_binary_base";
    # nhánh A: classify → "binary.decimal_to_binary" → ownership gap;
    # nhánh B (fault-injection): classify → "generic.rule_scene", result_ownership="algorithmic"
    #   → computation gate M13 chặn (defense-in-depth);
    # cả hai nhánh: envelope unsupported, KHÔNG có config generic nào được sinh.
```

- [ ] **Step 2 — FAIL (case chưa tồn tại) → Step 3 — thêm case/tag/suite → Step 4 — PASS + suite.**
- [ ] **Step 5 — Commit:** `M15 Task 9: 4 eval case m15_wave1 (hex/octal gap + binary positive + binsearch unsorted) + suite đăng ký + offline proof hai nhánh gap (ownership + defense-in-depth computation gate)`

**Acceptance:** admission xanh; hai đường gap offline chứng minh qua `run_pipeline` thật. **Rollback:** revert commit.

---

### Task 10: CACHE_VERSION 11→12 + full offline regression (khóa 9)

**Mục tiêu:** Bump ĐÚNG MỘT LẦN sau khi contract/prompt/gate đồng bộ; chốt số liệu W1.

**Files:** Modify `backend/app/main.py` (CACHE_VERSION + comment "12": M15 W1); Test: test hiện có nào assert "11" thì cập nhật (grep trước).

**Dependency:** Task 1–9 XANH TOÀN BỘ. **Invariant:** khóa 9; cache invalidation đúng một đợt.

- [ ] **Step 1 —** grep `CACHE_VERSION`/`"11"` trong tests → cập nhật assert. **Step 2 —** bump `"11"` → `"12"` + comment một dòng lý do (enum analyze + analyze.md + gate mới). **Step 3 — FULL regression:** `.venv/Scripts/python -m pytest` · `cd frontend && npm test && npm run build` — ghi số pass thực. **Step 4 —** xác nhận `git diff --stat` FE production = 0 (chỉ json + test). **Step 5 — Commit:** `M15 Task 10: CACHE_VERSION 11→12 (một bump duy nhất W1 — enum analyze + analyze.md + consistency gate); full regression pytest/vitest/build xanh`

**Acceptance:** toàn suite xanh, số liệu ghi vào commit message. **Rollback:** revert (nếu đã deploy phục vụ v12 → forward-fix, không quay lui version).

---

### Task 11: Targeted live checkpoint `m15_wave1` — **STOP GATE, chờ user duyệt ngân sách**

**Mục tiêu:** Khóa 8 live. **KHÔNG TỰ CHẠY** — dừng, trình acceptance + ngân sách, chờ `ALLOW_LIVE_AI=1` và trần call user duyệt.

**Acceptance (viết trước — rev2 §M):**
- BẮT BUỘC: (1) hex → unsupported (classify-refuse HOẶC gate-fired đều đạt), 0 generic config; (2) binary positive → `binary.decimal_to_binary` valid spec, không bị chặn oan; (3) binsearch unsorted → ok + note chuẩn hoá.
- OPTIONAL theo ngân sách: (4) octal; (5) sorting positive paraphrase (control salience — analyze.md dài thêm); (6) selection near-miss.
- Trần đề xuất: ≤6 case logic / ≤20 HTTP. Ghi nhật ký CURRENT_STATE §1 (logical case, HTTP thực, retry, transient). Không prompt-fix trước khi có exact trace; tối đa MỘT prompt-only fix/root-cause đã chứng minh; không sửa validator/gate đúng để LLM pass.

**Dependency:** Task 10. **Rollback:** live fail có chữ ký rõ → xử theo bảng failure-mode design §Q (hex-control hỏng → gỡ `non_binary_base` khỏi analyze-exposed, giữ phần còn lại W1). **Commit checkpoint:** cập nhật CURRENT_STATE §1 sau run (docs).

---

# WAVE 2 — Scan formalization, KHÔNG selector (Task 12)

### Task 12: Scan ownership + conformance proof

**Mục tiêu:** Khóa 10 — 6 entry scan có owned canonical; proof "ScanSpec ĐÃ là bounded family-spec"; không selector, không spec mới, không predict.

**Files:**
- Modify: `backend/app/simulation/catalog.py` (`_ALGO_META` 5 entry + `algorithm.scan` owned; `mechanisms.py` FORMALIZED_FAMILIES += SINGLE_PASS_SCAN), regenerate `capability-descriptors.json`
- Test: Create `backend/tests/test_scan_conformance.py`

**Owned khai:** find_max/find_min `("single_pass_scan.track_extreme",)`; sum_if `("single_pass_scan.accumulate_conditional",)`; count_if `("single_pass_scan.count_conditional",)`; linear_search `("single_pass_scan.find_equal_early_stop",)`; algorithm.scan = CẢ 5 giá trị (catch-all trong-family: `("single_pass_scan.track_extreme", "single_pass_scan.accumulate_conditional", "single_pass_scan.count_conditional", "single_pass_scan.find_equal_early_stop", "single_pass_scan.configured_single_pass")`).

**Dependency:** Task 3 (lock theo pha tự siết khi FORMALIZED_FAMILIES mở rộng). **Invariant:** khóa 10; M12 (interpreter sở hữu loop); classify menu KHÔNG đổi.

- [ ] **Step 1 — test trước** (`test_scan_conformance.py`) — checklist conformance §B design bằng assert:

```python
def test_scan_spec_da_bounded_versioned_khong_can_spec_moi():
    from app.simulation.catalog import CATALOG
    from app.simulation.scan_engine import SCAN_VERSION
    spec = CATALOG["algorithm.scan"]
    assert spec.config_contract_version == "scan-1.0"
    assert spec.config_schema["properties"]["scan_version"]["enum"] == [SCAN_VERSION]

def test_khong_selector_cho_single_pass_scan():
    from app.simulation.families import FAMILY_SELECTORS
    assert "single_pass_scan" not in FAMILY_SELECTORS  # khóa 10

def test_6_entry_scan_owned_canonical_va_menu_khong_doi():
    from app.simulation.catalog import CATALOG, llm_choices
    ids = ["algorithm.find_max", "algorithm.find_min", "algorithm.sum_if",
           "algorithm.count_if", "algorithm.linear_search", "algorithm.scan"]
    for sim_id in ids:
        mems = [m for m in CATALOG[sim_id].family_memberships
                if m.family_id.value == "single_pass_scan"]
        assert mems and mems[0].owned_mechanisms
        assert sim_id in llm_choices()          # direct surface GIỮ NGUYÊN

def test_scan_module_khong_them_predict():
    # vitest-side đã có scan-module tests; BE chỉ khoá mặt catalog — predict
    # là capability FE; lock FE: scan-module.test.ts hiện có assert không predict? nếu chưa,
    # THÊM 1 assert `mod.predict === undefined` vào scan-module.test.ts (test-only).
```

- [ ] **Step 2 — FAIL → Step 3 — khai owned + FORMALIZED += + regenerate JSON → Step 4 — PASS + full suite (m12 locks nguyên trạng) → Step 5 — Commit:** `M15 Task 12 (W2): scan family formalize KHÔNG selector — owned canonical 6 entry (scan = catch-all trong-family), conformance proof ScanSpec bounded/versioned, menu + m12 locks nguyên trạng, không predict`

**Acceptance:** proof xanh; `llm_choices()` y hệt trước; 0 spec mới. **Rollback:** revert commit.

---

# WAVE 3 — Boolean dual-surface (Task 13)

### Task 13: Boolean ownership + boundary locks

**Mục tiêu:** Khóa 11 — dual surface giữ nguyên; ownership 2 phía; ranh giới khoá bằng eval expectations (không production gate mới).

**Files:**
- Modify: `backend/app/simulation/catalog.py` (and_gate + generic comp-membership owned; FORMALIZED += BOOLEAN_COMPOSITION), regenerate JSON
- Test: Create `backend/tests/test_boolean_dual_surface.py`

- [ ] **Step 1 — test trước:**

```python
def test_hai_be_mat_boolean_khong_hop_nhat_va_owned_khac_nhau():
    from app.simulation.catalog import CATALOG
    and_mems = [m for m in CATALOG["logic.and_gate"].family_memberships
                if m.family_id.value == "boolean_composition"]
    gen_mems = [m for m in CATALOG["generic.rule_scene"].family_memberships
                if m.family_id.value == "boolean_composition"]
    assert and_mems[0].owned_mechanisms == ("boolean_composition.single_gate_truth_table",)
    assert gen_mems[0].owned_mechanisms == ("boolean_composition.composed_rule_dag",)

def test_boundary_lock_m11_expectations_giu_nguyen():
    # pin ranh giới đã live-verify M11: case NOT → generic; case a-and đối chứng → logic.and_gate
    # (đọc từ datasets, assert expect_simulation_id — lock chống sửa nhầm dataset)

def test_khong_them_production_truth_table_gate():
    # khóa 11: không symbol mới kiểu check_truth_table trong semantic/validator
    # (lock dạng: pipeline không import gì mới từ semantic ngoài danh sách hiện có)
```

- [ ] **Steps 2–4:** FAIL → khai owned + FORMALIZED += → PASS + full suite. **Step 5 — Commit:** `M15 Task 13 (W3): boolean dual-surface — owned tách bạch single_gate_truth_table ↔ composed_rule_dag, boundary lock pin m11 expectations, không production truth-table gate`

**Rollback:** revert commit. **Dependency:** Task 3.

---

# WAVE 4 — Network ownership/gaps (Task 14)

### Task 14: Routing + encapsulation ownership + known_gaps

**Mục tiêu:** Khóa 12 — BFS unweighted owned; weighted = gap máy-đọc; encap owned; 2D/3D nguyên trạng.

**Files:**
- Modify: `backend/app/simulation/catalog.py` (2 entry owned; packet_routing +`known_gaps=("đường đi ngắn nhất có trọng số (Dijkstra)", "dựng topo từng bước")`; FORMALIZED += GRAPH_TRAVERSAL + LAYERED_PDU_TRANSFORM), regenerate JSON
- Test: Create `backend/tests/test_network_ownership.py`

- [ ] **Step 1 — test trước:**

```python
def test_routing_owned_bfs_va_khai_gap_dijkstra():
    from app.simulation.catalog import CATALOG
    spec = CATALOG["network.packet_routing"]
    mems = [m for m in spec.family_memberships if m.family_id.value == "graph_traversal"]
    assert mems[0].owned_mechanisms == ("graph_traversal.unweighted_hop_bfs",)
    assert any("Dijkstra" in g for g in spec.known_gaps)

def test_encap_owned_va_known_gaps_giu_nguyen():
    from app.simulation.catalog import CATALOG
    spec = CATALOG["network.protocol_encapsulation"]
    mems = [m for m in spec.family_memberships if m.family_id.value == "layered_pdu_transform"]
    assert mems[0].owned_mechanisms == ("layered_pdu_transform.encapsulate_decapsulate_4layer",)
    assert "phân mảnh" in spec.known_gaps  # M10 giữ nguyên

def test_dijkstra_gap_lock_van_nguyen():
    # pin case cap-dijkstra-gap trong datasets/capability.py: group="unsupported"
    # (chống sửa nhầm — Dijkstra vẫn CAPABILITY_GAP, khóa 12: không thêm Dijkstra)
```

- [ ] **Steps 2–4:** FAIL → khai → PASS + full suite (encap/routing/3D tests nguyên trạng — `render3d`/`encap-render3d` vitest không đổi). **Step 5 — Commit:** `M15 Task 14 (W4): network ownership — routing owned unweighted_hop_bfs + known_gaps Dijkstra máy-đọc, encap owned encap_decap_4layer, 2D/3D nguyên trạng, dijkstra-gap lock pin`

**Rollback:** revert commit. **Dependency:** Task 3.

---

# WAVE 5 — Representation proof + coverage + close (Task 15–16)

### Task 15: Generic representation authority proof

**Mục tiêu:** Khóa 13 phần proof — repr membership owned DẪN XUẤT từ manifest; authority tách bạch; representation không thành fallback tính toán.

**Files:**
- Modify: `backend/app/simulation/catalog.py` (generic repr-membership owned dẫn xuất `process_types()` → prefix namespace; FORMALIZED += STRUCTURAL_PROGRESSIVE_REPRESENTATION → **đủ 8 family**), regenerate JSON
- Test: Create `backend/tests/test_generic_representation_authority.py`

- [ ] **Step 1 — test trước:**

```python
def test_repr_owned_dan_xuat_tu_manifest_process_types():
    from app.simulation.catalog import CATALOG
    from app.simulation.dsl.manifest import process_types
    mems = [m for m in CATALOG["generic.rule_scene"].family_memberships
            if m.family_id.value == "structural_progressive_representation"]
    assert set(mems[0].owned_mechanisms) == {
        f"structural_progressive_representation.{p}" for p in process_types()
    }  # một nguồn — manifest, không viết tay

def test_hai_membership_generic_authority_khac_nhau():
    from app.simulation.catalog import CATALOG
    from app.simulation.descriptor import ResultAuthority
    auths = {m.family_id.value: m.result_authority
             for m in CATALOG["generic.rule_scene"].family_memberships}
    assert auths["boolean_composition"] == ResultAuthority.COMPUTATION
    assert auths["structural_progressive_representation"] == ResultAuthority.REPRESENTATION

def test_formalized_families_du_8():
    from app.simulation.descriptor import FamilyId
    from app.simulation.mechanisms import FORMALIZED_FAMILIES
    assert FORMALIZED_FAMILIES == frozenset(FamilyId)  # K1 đầy đủ — kích hoạt lock 14/14

def test_representation_khong_tra_loi_bai_computation():
    # pin bất biến #21: mock analysis result_ownership="algorithmic" + classify→generic
    # → computation gate unsupported (tham chiếu test_m13_routing — thêm assert
    # error/reason không đổi, làm LOCK của family F8)
```

- [ ] **Steps 2–4:** FAIL → khai + FORMALIZED đủ 8 (lock 14/14 owned tự siết — mọi entry giờ phải owned ≠ ∅, đã thoả từ W1–W4) → PASS + full suite. **Step 5 — Commit:** `M15 Task 15 (W5): generic representation authority proof — repr owned dẫn xuất manifest process_types, hai membership authority tách bạch, FORMALIZED đủ 8 family → K1 lock 14/14 kích hoạt, bất biến #21 pin làm lock F8`

**Rollback:** revert commit. **Dependency:** Task 12–14 (FORMALIZED đủ 8 chỉ đúng khi W2–W4 đã khai owned).

### Task 16: Coverage + docs close + final regression

**Mục tiêu:** Khóa 13 — sorting PILOT→SUPPORTED (claim boundary n=4); docs close; KHÔNG mở M16.

**Files:**
- Modify: `backend/app/simulation/coverage.py` (sorting row → `CoverageStatus.SUPPORTED`, note: "M14 pilot + M15 formalize; live n=4 là targeted acceptance, KHÔNG phải bằng chứng thống kê"; binary_system note += "cơ số ≠ 2 → capability_gap có control (M15 W1)")
- Modify docs: `docs/CURRENT_STATE.md` (header + §1 nhật ký live W1 + §2 hàng M15 + §5 nếu có known-issue mới), `docs/CODE_INDEX.md` (mechanisms.py + gate mới + suite m15_wave1), `docs/ARCHITECTURE_MAP.md` (quyết §S6: đăng bất biến #23 "mechanism ownership membership-level, taxonomy canonical đóng, gate so tín hiệu cấu trúc — không keyword" HAY chỉ ghi §6 — trình user chọn ở close report), `docs/COVERAGE.md` nếu chạm phát ngôn
- Test: mở rộng `backend/tests/test_coverage_matrix.py` (sorting SUPPORTED + note chứa claim boundary)

- [ ] **Step 1 — test trước:** matrix lock assert sorting == SUPPORTED và note chứa "không phải bằng chứng thống kê". **Step 2 — FAIL → sửa coverage.py → PASS.**
- [ ] **Step 3 — FULL final regression:** pytest + vitest + `npm run build`; `npm run audit:layout` CHỈ nếu W1–W5 có đụng CSS/UI (theo plan này: KHÔNG → skip, ghi rõ lý do). Ghi số pass THẬT (không bịa — khóa "không phát minh test number").
- [ ] **Step 4 —** viết close report (`.superpowers/sdd/` theo lệ M13) + cập nhật docs trên. **Step 5 — Commit:** `M15 Task 16 (W5): coverage sorting PILOT→SUPPORTED (claim boundary n=4) + binary_system note + docs close CURRENT_STATE/CODE_INDEX/ARCHITECTURE_MAP; final regression <số thật>; M16 chưa bắt đầu`

**Acceptance:** M15 COMPLETE criteria §R design (13 mục) đối chiếu từng dòng trong close report. **Rollback:** docs revert. **Dependency:** Task 11 (nhật ký live), 15.

---

## Thứ tự & phụ thuộc tổng (tóm tắt)

```
T1 ──→ T2 ──→ T3 ──→ (T12 W2, T13 W3, T14 W4 — độc lập nhau, sau T3)
 │      │
 │      └──→ T5 ──→ T6 ──→ T7 ──→ T9 ──→ T10 ──→ T11 (STOP GATE live)
 └──→ T4 ──↗                T8 (sau T2, song song nhánh T5–T7)
T12+T13+T14 ──→ T15 ──→ T16 (cần cả T11 cho nhật ký live)
```

Mỗi task một commit checkpoint, full suite xanh tại MỌI commit. Task nào phát hiện buộc lệch design rev2 → DỪNG báo user trước khi viết tiếp.
