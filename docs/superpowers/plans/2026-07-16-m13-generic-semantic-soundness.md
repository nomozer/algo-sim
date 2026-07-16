# M13 — Generic Semantic Soundness & Algorithmic Right-or-Refuse — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generic specs chỉ được chấp nhận theo hợp đồng ngữ nghĩa dẫn xuất từ manifest; cơ chế tính toán không được hỗ trợ bị từ chối trung thực (`capability_gap`) — không còn cảnh pseudo-algorithm kiểu Dijkstra, không còn toán hạng thiếu lặng lẽ thành 0.

**Architecture:** Ba workstream theo spec `docs/superpowers/specs/2026-07-16-m13-generic-semantic-soundness-design.md`: (A) mô hình ba trạng thái numeric source ở validator hai tầng + runtime fail-closed hai runtime; (B) cổng computation-obligation hai lớp trên đường generic (mở rộng taxonomy `arbitrary_algorithm` sẵn có — KHÔNG keyword-patch); (C) display-label policy cho id sinh lúc runtime. Kèm: CACHE_VERSION bump, pattern revalidation lock, history graceful-fail lock, fixture Dijkstra offline, eval case opt-in.

**Tech Stack:** Python 3 + pytest (backend, offline-guard tự động) · TypeScript + Vitest (frontend) · prompt markdown (`backend/app/ai/skills/*.md`).

## Global Constraints

- **KHÔNG viết production code trước khi plan này được user duyệt.**
- Spec nguồn: `docs/superpowers/specs/2026-07-16-m13-generic-semantic-soundness-design.md` — mọi mâu thuẫn: spec thắng plan, code/test thắng docs.
- KHÔNG thêm module Dijkstra · KHÔNG universal graph DSL · KHÔNG accessor trọng-số-cạnh · KHÔNG primitive DSL mới · KHÔNG redesign UI · KHÔNG sửa README trong M13.
- KHÔNG keyword-patch: gate dựa trên capability/role, prompt chỉ dạy taxonomy bằng ví dụ (thực hành sẵn có của analyze.md/classify.md).
- **SERVER ra phán quyết accept/gap cuối cùng** — tất định trên tín hiệu CÓ CẤU TRÚC (role tags + `result_ownership`), không phải prompt. Prompt chỉ là kênh trích xuất (R0).
- **MỘT artifact hợp đồng ngữ nghĩa canonical**: backend manifest là nguồn chân lý → sinh `dsl-contract.json` cho frontend tiêu thụ; contract-lock test chống drift. KHÔNG allowlist TS viết tay.
- **Coercion role mặc định DENY hai chiều** (`numeric→logical`, `logical→numeric`) — chỉ khai tường minh trong contract khi matrix audit tìm được fixture thật chứng minh.
- M13 KHÔNG claim hoàn tất LLM spec generation cho mọi mô phỏng — đó là đề xuất **M14 — Catalog-Wide Capability Spec Architecture** (sau M13, cần approval riêng).
- Mọi chuỗi user-facing + lỗi validator: **tiếng Việt**.
- Test mặc định offline (guard chặn network tự động); live AI = Task 14, cần user bật `ALLOW_LIVE_AI=1` tường minh.
- Allowlist numeric-provider **dẫn xuất từ manifest** cả hai tầng (anti-pattern #1) — không viết tay hai bản.
- Commit thường xuyên, message tiếng Việt kiểu repo (`M13: ...`), **không** Co-Authored-By trailer.
- `dataset.py` 30 case FROZEN — case mới chỉ vào `datasets/` pools.
- Claim cuối: “Generic specs are accepted according to manifest-derived semantic contracts; unsupported computational mechanisms are rejected.” — KHÔNG phải “Dijkstra is blocked”.

## Stop Conditions (dừng và báo user, không tự xử)

1. Artifact Dijkstra không khôi phục được từ `simulation_cache`/localStorage → dùng reconstructed fixture (Task 7 đã dựng sẵn) và **ghi rõ là tái dựng** — không giả vờ là artifact gốc.
2. Fixture/hợp đồng hiện hành mâu thuẫn với giả định provider (vd `lamp` có `value` trong sample thật, hoặc sample hợp lệ nào đó fail validator mới) → DỪNG, báo cáo, không nới allowlist tùy tiện.
3. Bất kỳ control FP-budget nào (Task 8) đỏ sau siết → DỪNG phân tích nguyên nhân, không "sửa test cho xanh".
4. Task 14 (live): quá 3 case logic hoặc LLM không học được taxonomy sau 1 lần vá prompt → DỪNG, báo kết quả, không đuổi salience (bài học M8-PRE S3).
5. `git status` bẩn ngoài file của task hiện tại → DỪNG.

---

### Task 1: Semantic Matrix Audit (docs-only)

**Files:**
- Create: `docs/superpowers/specs/2026-07-16-m13-semantic-matrix.md`

**Interfaces:**
- Produces: bảng hợp đồng ngữ nghĩa cho MỌI primitive hiện hành — Task 2–6 cài đúng theo bảng này; mọi sai lệch phát hiện khi cài → cập nhật matrix TRƯỚC, code sau.

- [ ] **Step 1: Đối chiếu nguồn** — đọc `backend/app/simulation/dsl/manifest.py` (`PRIMITIVE_ROLES`, `MANIFEST`), `frontend/src/simulations/domains/generic/model.ts` (`RULE_TYPES`, `evalRule`, `initialBase`, `buildTimeline`), `backend/app/simulation/generic_engine.py`, `validate.ts`, `validator.py`. Mỗi hàng matrix phải trỏ symbol thật.

- [ ] **Step 2: Viết matrix** với đúng các cột spec §9b (input/provider roles · output role · trường bắt buộc · input thiếu = invalid/unresolved/optional · dependency · bound · fail behavior · bản chất biểu diễn) **+ cột ENFORCEMENT DISPOSITION bắt buộc cho TỪNG hàng**, giá trị đúng một trong bốn:
  - `EXISTING` — enforcement + test đã tồn tại (trỏ file:test cụ thể);
  - `TASK-N` — được task N của plan này xử lý (trỏ đúng task + RED test);
  - `STOP-UNRESOLVED` — lỗ ngữ nghĩa CHƯA có task nào xử lý;
  - `OUT-OF-SCOPE` — kèm rationale vì sao chấp nhận được trong M13.

  **Luật dừng:** tồn tại ≥ 1 hàng `STOP-UNRESOLVED` → DỪNG sau Task 1, amend plan (thêm task hoặc chuyển thành OUT-OF-SCOPE có rationale được duyệt) — KHÔNG ghi tài liệu rồi đi tiếp.

  Phủ:
  - object: `switch` `lamp` `value_box` `node` `edge` `moving_entity` `label` `container` `group` `heading` `paragraph` `text`
  - rule: `boolean` · `weighted_sum` (comparison rule: **ghi VẮNG MẶT** — `RULE_TYPES` chỉ có 2)
  - interaction: `toggle` (chỉ base value 0/1, xem `index.ts:44-49`) · `drag`
  - process: `reveal_sequence` (object ids trong steps) · `move_along_path` (entity + path node ids)
  Ghi rõ từng lớp bug spec §9b áp vào primitive nào (vd: `move_along_path` path id thiếu → hành vi hiện tại? kiểm thật, ghi thật).

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/2026-07-16-m13-semantic-matrix.md
git commit -m "M13: semantic matrix audit — hợp đồng ngữ nghĩa mọi primitive generic (docs-only)"
```

---

### Task 2: Backend — manifest value-provider derivation + GENERATED contract artifact

**Files:**
- Modify: `backend/app/simulation/dsl/manifest.py` (thêm 2 hàm cuối file)
- Create: `backend/scripts/generate_dsl_contract.py` (generator, chạy tay khi manifest đổi)
- Create: `frontend/src/simulations/domains/generic/dsl-contract.json` (SINH RA, committed)
- Test: `backend/tests/test_manifest_providers.py` (mới — gồm cả sync-lock chống drift)

**Interfaces:**
- Produces: `value_provider_types(role: str) -> set[str]` và `dsl_semantic_contract() -> dict` (backend); `dsl-contract.json` shape:
  ```json
  {
    "value_providers": { "numeric": ["lamp", "switch", "value_box"], "logical": ["lamp", "switch"] },
    "rule_io": { "weighted_sum": { "input_role": "numeric", "output_role": "numeric" },
                  "boolean": { "input_role": "logical", "output_role": "logical" } },
    "object_roles": { "switch": ["interactive", "logical", "numeric"], "lamp": ["logical", "numeric"],
                       "value_box": ["numeric"], "node": ["relational"], "edge": ["relational"] },
    "role_coercions": []
  }
  ```
  (`object_roles` = `PRIMITIVE_ROLES` của các object type, sinh tự động — ràng buộc 2: kiểm cả rule-output → target-object-role, không chỉ provider → input.)
  Task 3 dùng hàm backend; Task 5 import JSON — **không tầng nào viết tay allowlist**. `role_coercions` rỗng = DENY mặc định; matrix audit chứng minh được mới thêm (vd `{"from": "logical", "to": "numeric"}`).

- [ ] **Step 1: Viết test fail**

```python
# backend/tests/test_manifest_providers.py
"""M13: contract-lock — nguồn giá trị dẫn xuất từ PRIMITIVE_ROLES, không viết tay."""
from app.simulation.dsl.manifest import value_provider_types


def test_numeric_providers_dan_xuat_tu_manifest():
    # Snapshot CÓ Ý THỨC: đổi manifest thì test này phải được cập nhật kèm lý do.
    assert value_provider_types("numeric") == {"switch", "lamp", "value_box"}


def test_logical_providers_dan_xuat_tu_manifest():
    assert value_provider_types("logical") == {"switch", "lamp"}


def test_relational_khong_phai_value_provider():
    assert "node" not in value_provider_types("numeric")
    assert "edge" not in value_provider_types("numeric")
```

- [ ] **Step 2: RED** — `cd backend && .venv/Scripts/python -m pytest tests/test_manifest_providers.py -v` → FAIL `ImportError: cannot import name 'value_provider_types'`.

- [ ] **Step 3: Cài tối thiểu** (cuối `manifest.py`):

```python
def value_provider_types(role: str) -> set[str]:
    """M13: các OBJECT type có vai trò cung cấp giá trị `role` (vd "numeric").

    DẪN XUẤT từ PRIMITIVE_ROLES ∩ object_types — không viết tay allowlist
    (anti-pattern #1). node/edge chỉ relational → không bao giờ là provider.
    """
    object_types = set(MANIFEST["object_types"])
    return {t for t in object_types if role in PRIMITIVE_ROLES.get(t, set())}
```

- [ ] **Step 4: GREEN** — chạy lại Step 2 → 3 PASS.

- [ ] **Step 5: Thêm `dsl_semantic_contract()` + generator + sync-lock test**

`manifest.py`:

```python
RULE_IO_ROLES = {
    "weighted_sum": {"input_role": "numeric", "output_role": "numeric"},
    "boolean": {"input_role": "logical", "output_role": "logical"},
}

def dsl_semantic_contract() -> dict:
    """M13: hợp đồng ngữ nghĩa CANONICAL — nguồn duy nhất cho cả hai tầng.
    Frontend tiêu thụ bản sinh (dsl-contract.json); test sync-lock chống drift."""
    object_types = set(MANIFEST["object_types"])
    return {
        "value_providers": {
            role: sorted(value_provider_types(role)) for role in ("numeric", "logical")
        },
        "rule_io": RULE_IO_ROLES,
        "object_roles": {
            t: sorted(PRIMITIVE_ROLES[t]) for t in sorted(object_types)
        },
        "role_coercions": [],  # DENY mặc định — chỉ thêm khi matrix audit chứng minh
    }
```

`backend/scripts/generate_dsl_contract.py`:

```python
"""Sinh dsl-contract.json cho frontend từ manifest (chạy tay khi manifest đổi).
Cách chạy:  cd backend && .venv/Scripts/python scripts/generate_dsl_contract.py"""
import json
from pathlib import Path
from app.simulation.dsl.manifest import dsl_semantic_contract

OUT = Path(__file__).resolve().parents[2] / "frontend/src/simulations/domains/generic/dsl-contract.json"
OUT.write_text(json.dumps(dsl_semantic_contract(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"Đã sinh {OUT}")
```

Chạy generator một lần → file JSON ra đời. Sync-lock test (thêm vào `test_manifest_providers.py`):

```python
import json
from pathlib import Path
from app.simulation.dsl.manifest import dsl_semantic_contract

def test_dsl_contract_json_khong_troi_khoi_manifest():
    """Đổi manifest mà quên chạy generate_dsl_contract.py → test ĐỎ (anti-pattern #1)."""
    committed = json.loads(
        (Path(__file__).resolve().parents[2] / "frontend/src/simulations/domains/generic/dsl-contract.json")
        .read_text(encoding="utf-8")
    )
    assert committed == dsl_semantic_contract()
```

- [ ] **Step 6: GREEN toàn cục** — `python -m pytest` → không vỡ gì.

- [ ] **Step 7: Commit** — `git add … && git commit -m "M13: dsl_semantic_contract canonical + generator dsl-contract.json + sync-lock chống drift"`

---

### Task 3: Backend — validator operand coherence (INVALID_SOURCE)

**Files:**
- Modify: `backend/app/simulation/dsl/validator.py` (khối rule validation, hiện ~dòng 320–355)
- Test: `backend/tests/test_dsl_validator.py` (file test validator sẵn có — thêm test; nếu tên file khác, grep `weighted_sum cần` trong `backend/tests/` để tìm đúng file)

**Interfaces:**
- Consumes: `value_provider_types` (Task 2).
- Produces: validator từ chối operand `INVALID_SOURCE` với lỗi tiếng Việt chứa cụm `không có nguồn giá trị` — Task 7/8/10 khớp trên cụm này.

- [ ] **Step 1: Viết test fail** (thêm vào file test validator; helper `_spec(...)` dựng spec tối thiểu theo mẫu test sẵn có trong file):

```python
def test_weighted_sum_input_edge_bi_tu_choi():
    """M13 E6: tồn tại id là KHÔNG đủ — edge không có hợp đồng giá trị số."""
    spec = _spec(
        objects=[
            {"id": "a", "type": "node", "label": "A"},
            {"id": "b", "type": "node", "label": "B"},
            {"id": "e1", "type": "edge", "label": "AB", "from": "a", "to": "b"},
            {"id": "kq", "type": "value_box", "label": "Tổng"},
        ],
        rules=[{"type": "weighted_sum", "target": "kq", "inputs": ["e1"], "weights": [1]}],
    )
    config, err = validate_generic_config(spec)
    assert config is None
    assert "không có nguồn giá trị" in err


def test_chuoi_dan_xuat_khai_bao_dao_van_hop_le():
    """M13 §3.2: UNRESOLVED_DERIVED_SOURCE — rule khai trước provider vẫn hợp lệ."""
    spec = _spec(
        objects=[
            {"id": "x", "type": "switch", "label": "X", "value": 1},
            {"id": "mid", "type": "value_box", "label": "Trung gian"},
            {"id": "kq", "type": "value_box", "label": "Kết quả"},
        ],
        rules=[
            # kq phụ thuộc mid — mid được rule SAU định nghĩa: phải hợp lệ.
            {"type": "weighted_sum", "target": "kq", "inputs": ["mid"], "weights": [2]},
            {"type": "weighted_sum", "target": "mid", "inputs": ["x"], "weights": [3]},
        ],
    )
    config, err = validate_generic_config(spec)
    assert err is None and config is not None


def test_boolean_input_value_box_bi_tu_choi():
    """value_box chỉ numeric, không logical → không được nuôi boolean rule."""
    spec = _spec(
        objects=[
            {"id": "v", "type": "value_box", "label": "V", "value": 5},
            {"id": "den", "type": "lamp", "label": "Đèn"},
        ],
        rules=[{"type": "boolean", "op": "not", "target": "den", "inputs": ["v"]}],
    )
    config, err = validate_generic_config(spec)
    assert config is None
    assert "không có nguồn giá trị" in err


def test_provider_thieu_value_bi_tu_choi():
    """switch (provider hợp lệ) nhưng KHÔNG khai value và không là rule target."""
    spec = _spec(
        objects=[
            {"id": "s", "type": "switch", "label": "S"},  # không value
            {"id": "kq", "type": "value_box", "label": "KQ"},
        ],
        rules=[{"type": "weighted_sum", "target": "kq", "inputs": ["s"], "weights": [1]}],
    )
    config, err = validate_generic_config(spec)
    assert config is None
    assert "không có nguồn giá trị" in err


def test_derived_target_sai_role_bi_tu_choi_weighted_sum_nuoi_boolean():
    """M13 blocker 3: numeric output (weighted_sum target) KHÔNG được nuôi boolean
    input — chính là lớp coercion im lặng v>=1. DENY mặc định."""
    spec = _spec(
        objects=[
            {"id": "v", "type": "value_box", "label": "V", "value": 5},
            {"id": "tong", "type": "value_box", "label": "Tổng"},
            {"id": "den", "type": "lamp", "label": "Đèn"},
        ],
        rules=[
            {"type": "weighted_sum", "target": "tong", "inputs": ["v"], "weights": [1]},
            {"type": "boolean", "op": "not", "target": "den", "inputs": ["tong"]},
        ],
    )
    config, err = validate_generic_config(spec)
    assert config is None
    assert "vai trò" in err  # lỗi nêu rõ mismatch output_role ↔ input_role


def test_derived_target_dung_role_van_hop_le_chain_numeric():
    """weighted_sum target (numeric) nuôi weighted_sum input (numeric) — hợp lệ."""
    spec = _spec(
        objects=[
            {"id": "x", "type": "switch", "label": "X", "value": 1},
            {"id": "mid", "type": "value_box", "label": "TG"},
            {"id": "kq", "type": "value_box", "label": "KQ"},
        ],
        rules=[
            {"type": "weighted_sum", "target": "mid", "inputs": ["x"], "weights": [3]},
            {"type": "weighted_sum", "target": "kq", "inputs": ["mid"], "weights": [2]},
        ],
    )
    config, err = validate_generic_config(spec)
    assert err is None and config is not None


def test_rule_output_ghi_vao_target_sai_role_bi_tu_choi():
    """Ràng buộc 2 (duyệt lần 3): weighted_sum (output numeric) KHÔNG được ghi
    vào node (chỉ relational) — target phải CHẤP NHẬN output role của rule."""
    spec = _spec(
        objects=[
            {"id": "v", "type": "value_box", "label": "V", "value": 3},
            {"id": "n1", "type": "node", "label": "N1"},
        ],
        rules=[{"type": "weighted_sum", "target": "n1", "inputs": ["v"], "weights": [1]}],
    )
    config, err = validate_generic_config(spec)
    assert config is None
    assert "không nhận được" in err


def test_rule_output_ghi_vao_target_dung_role_hop_le():
    """boolean (output logical) ghi vào lamp ({logical, numeric}) — hợp lệ."""
    spec = _spec(
        objects=[
            {"id": "s", "type": "switch", "label": "S", "value": 0},
            {"id": "den", "type": "lamp", "label": "Đèn"},
        ],
        rules=[{"type": "boolean", "op": "not", "target": "den", "inputs": ["s"]}],
    )
    config, err = validate_generic_config(spec)
    assert err is None and config is not None
```

- [ ] **Step 2: RED** — `python -m pytest tests/test_dsl_validator.py -v -k "m13 or edge_bi or dao or provider_thieu or boolean_input"` (chỉnh -k theo tên thật) → 3 test đầu FAIL (validator hiện chấp nhận), test đảo PASS sẵn (không được làm nó đỏ về sau).

- [ ] **Step 3: Cài** — trong `validator.py`, SAU vòng dựng `rules` + check trùng target + check chu trình (giữ nguyên thứ tự sẵn có), thêm:

```python
    # ── M13 §3.2 + blocker 3: operand coherence VỚI role-typing ──
    # INVALID_SOURCE: type không phải provider của role rule cần, hoặc provider
    #   nhưng không khai value; HOẶC derived target có output_role KHÔNG khớp
    #   input_role của rule tiêu thụ (coercion DENY mặc định — role_coercions rỗng).
    # UNRESOLVED_DERIVED_SOURCE (hợp lệ ở tầng validate): input là target của rule
    #   khác VÀ output_role khớp — thứ tự khai báo tự do, runtime defer theo bound.
    from app.simulation.dsl.manifest import PRIMITIVE_ROLES, RULE_IO_ROLES, dsl_semantic_contract, value_provider_types  # (đầu file)
    obj_by_id = {o["id"]: o for o in objects}
    target_output_role = {r["target"]: RULE_IO_ROLES[r["type"]]["output_role"] for r in rules}
    coercions = {(c["from"], c["to"]) for c in dsl_semantic_contract()["role_coercions"]}
    for r in rules:
        # Ràng buộc 2: target object phải CHẤP NHẬN output role của rule —
        # weighted_sum (numeric) không được ghi vào node/edge (relational).
        out_role = RULE_IO_ROLES[r["type"]]["output_role"]
        target_obj = obj_by_id[r["target"]]
        if out_role not in PRIMITIVE_ROLES.get(target_obj["type"], set()):
            return None, (
                f'Rule {r["type"]} sinh giá trị vai trò "{out_role}" nhưng target '
                f'"{r["target"]}" ({target_obj["type"]}) không nhận được vai trò đó — '
                f'dùng object type có vai trò {out_role} làm target (vd value_box/lamp).'
            )
        need = RULE_IO_ROLES[r["type"]]["input_role"]
        providers = value_provider_types(need)
        for inp in r.get("inputs", []):
            if inp in target_output_role:
                out = target_output_role[inp]
                if out != need and (out, need) not in coercions:
                    return None, (
                        f'Rule "{r["target"]}" dùng input "{inp}" là kết quả rule khác có '
                        f'vai trò "{out}", nhưng rule {r["type"]} cần vai trò "{need}" — '
                        f'không có coercion được khai. Dùng nguồn đúng vai trò.'
                    )
                continue  # derived + đúng role → defer lúc chạy
            o = obj_by_id[inp]
            if o["type"] not in providers or "value" not in o:
                return None, (
                    f'Rule "{r["target"]}" dùng input "{inp}" ({o["type"]}) '
                    f'không có nguồn giá trị {need} theo hợp đồng DSL — '
                    f'chỉ chấp nhận: {", ".join(sorted(providers))} có "value", '
                    f'hoặc target của một rule cùng vai trò. Đừng dùng node/edge làm toán hạng.'
                )
```

Lưu ý cài đặt: biến `objects` là danh sách object đã chuẩn hoá của validator (tên biến thật xem trong file); import đặt đầu file cùng các import manifest sẵn có. `RULE_IO_ROLES` đến từ Task 2.

- [ ] **Step 4: GREEN** — chạy lại Step 2 → 4 PASS. Toàn suite backend: `python -m pytest` → nếu case sẵn có nào đỏ, đó là FP-budget stop-condition #3 — DỪNG và phân tích (trừ khi case đó chính là shape bug, vd fixture test cũ dùng edge làm input: khi đó sửa fixture là ĐÚNG và ghi vào báo cáo).

- [ ] **Step 5: Commit** — `M13: validator backend — operand coherence ba trạng thái (INVALID_SOURCE reject, derived defer)`

---

### Task 4: Backend — runtime three-state + `GenericEvaluationError`

**Files:**
- Modify: `backend/app/simulation/generic_engine.py`
- Test: `backend/tests/test_generic_engine_m13.py` (mới)

**Interfaces:**
- Produces: `GenericEvaluationError(code, detail)` với `code ∈ {invalid_numeric_source, missing_weight, unresolved_dependency_after_bound, non_finite_numeric_value}`; `values_of` giữ nguyên chữ ký `(spec, base) -> dict`. `run_gates` (patterns.py:184) đã bọc `values_of` trong try/except — TỰ ĐỘNG chuyển lỗi thành reject, không sửa `run_gates`.

- [ ] **Step 1: Viết test fail**

```python
# backend/tests/test_generic_engine_m13.py
"""M13 §3.4: runtime fail-closed — không còn undefined-thành-0 im lặng."""
import pytest
from app.simulation.generic_engine import (
    GenericEvaluationError, initial_base, values_of,
)


def _spec(objects, rules):
    return {"objects": objects, "rules": rules, "processes": [], "interactions": []}


def test_chuoi_dao_thu_tu_hoi_tu_dung_gia_tri():
    spec = _spec(
        [{"id": "x", "type": "switch", "value": 1},
         {"id": "mid", "type": "value_box"}, {"id": "kq", "type": "value_box"}],
        [{"type": "weighted_sum", "target": "kq", "inputs": ["mid"], "weights": [2]},
         {"type": "weighted_sum", "target": "mid", "inputs": ["x"], "weights": [3]}],
    )
    values = values_of(spec, initial_base(spec))
    assert values["mid"] == 3 and values["kq"] == 6  # trước đây cũng đúng nhờ fixed-point — GIỮ NGUYÊN


def test_toan_hang_khong_ton_tai_trong_values_nem_typed_error():
    # Validator chặn từ trước; đây là LƯỚI SAU CÙNG (defense in depth):
    spec = _spec(
        [{"id": "e1", "type": "edge"}, {"id": "kq", "type": "value_box"}],
        [{"type": "weighted_sum", "target": "kq", "inputs": ["e1"], "weights": [1]}],
    )
    with pytest.raises(GenericEvaluationError) as ei:
        values_of(spec, initial_base(spec))
    assert ei.value.code == "unresolved_dependency_after_bound"


def test_ket_qua_non_finite_nem_typed_error():
    spec = _spec(
        [{"id": "v", "type": "value_box", "value": 1e308}, {"id": "kq", "type": "value_box"}],
        [{"type": "weighted_sum", "target": "kq", "inputs": ["v"], "weights": [1e308]}],
    )
    with pytest.raises(GenericEvaluationError) as ei:
        values_of(spec, initial_base(spec))
    assert ei.value.code == "non_finite_numeric_value"
```

- [ ] **Step 2: RED** — `python -m pytest tests/test_generic_engine_m13.py -v` → FAIL (`GenericEvaluationError` chưa tồn tại).

- [ ] **Step 3: Cài** — rework `generic_engine.py`:

```python
import math


class GenericEvaluationError(Exception):
    """M13 §3.4 — typed failure tại ranh giới executor; KHÔNG bao giờ thành 0."""

    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def _eval_rule(rule: dict, values: dict[str, float]) -> float:
    inputs = []
    for i in rule.get("inputs", []):
        if i not in values:
            raise GenericEvaluationError("invalid_numeric_source", f'input "{i}" chưa có giá trị')
        inputs.append(values[i])
    if rule["type"] == "boolean":
        bits = [1 if v >= 1 else 0 for v in inputs]
        op = rule.get("op")
        if op == "and":
            return 1 if all(b == 1 for b in bits) else 0
        if op == "or":
            return 1 if any(b == 1 for b in bits) else 0
        if op == "xor":
            return sum(bits) % 2
        if op == "not":
            return 0 if bits and bits[0] == 1 else 1
        return 0
    weights = rule.get("weights", [])
    if len(weights) != len(inputs):
        raise GenericEvaluationError("missing_weight", f'rule "{rule["target"]}" thiếu weight')
    result = sum(v * w for v, w in zip(inputs, weights))
    if not math.isfinite(result):
        raise GenericEvaluationError("non_finite_numeric_value", f'rule "{rule["target"]}" ra {result}')
    return result


def values_of(spec: dict, base: dict[str, float]) -> dict[str, float]:
    """M13 ba trạng thái: KHÔNG seed target = 0 nữa — target chưa resolve là
    UNRESOLVED (vắng mặt trong values), rule chỉ chạy khi MỌI input resolved.
    DAG hợp lệ hội tụ trong ≤ len(rules) lượt; còn sót sau bound → typed error."""
    values = dict(base)
    rules = list(spec.get("rules", []))
    pending = list(rules)
    for _ in range(len(rules) + 1):
        still = []
        for rule in pending:
            if all(i in values for i in rule.get("inputs", [])):
                values[rule["target"]] = _eval_rule(rule, values)
            else:
                still.append(rule)
        if not still:
            break
        if len(still) == len(pending):  # không tiến triển → không bao giờ resolve
            missing = sorted({i for r in still for i in r.get("inputs", []) if i not in values})
            raise GenericEvaluationError(
                "unresolved_dependency_after_bound",
                f'không resolve được: {", ".join(missing)}',
            )
        pending = still
    if pending:
        raise GenericEvaluationError("unresolved_dependency_after_bound", "vượt bound evaluation")
    return values
```

**Chú ý ngữ nghĩa giữ nguyên cho spec hợp lệ:** trước đây toggle làm rule re-evaluate qua fixed-point trên values đã seed; bản mới thuần forward-resolve trên DAG — với spec đã qua validator (không chu trình, không trùng target, operand hợp lệ) kết quả **giống hệt**. Test M11 boolean sẵn có là bằng chứng (Step 4).

- [ ] **Step 4: GREEN** — file mới PASS; toàn suite backend PASS (đặc biệt test semantic/nested_boolean M11 — nếu đỏ: stop-condition #3).

- [ ] **Step 5: Commit** — `M13: generic_engine ba trạng thái + GenericEvaluationError (fail-closed, không seed 0)`

---

### Task 5: Frontend — validator mirror TIÊU THỤ contract sinh ra (parity với Task 3)

**Files:**
- Consume: `frontend/src/simulations/domains/generic/dsl-contract.json` (SINH từ Task 2 — KHÔNG sửa tay; sửa = sửa manifest backend rồi chạy lại generator)
- Modify: `frontend/src/simulations/domains/generic/validate.ts` (import JSON; thêm khối coherence sau check trùng target + chu trình, hiện ~dòng 310–325)
- Test: `frontend/src/simulations/domains/generic/generic.test.ts` (thêm block `describe("M13 operand coherence")`)

**Interfaces:**
- Consumes: `dsl-contract.json` (`value_providers` · `rule_io` · `role_coercions`) — backend là nguồn chân lý duy nhất, sync-lock test Task 2 chống drift. **KHÔNG có `VALUE_PROVIDER_TYPES` viết tay ở TS.**
- Produces: validate.ts từ chối với thông điệp chứa `không có nguồn giá trị` (INVALID_SOURCE) hoặc `vai trò` (role mismatch) — đồng bộ backend Task 3.

- [ ] **Step 1: Viết test fail** — 4 case đúng như Task 3 Step 1 (edge input reject · chuỗi đảo hợp lệ · value_box nuôi boolean reject · provider thiếu value reject), viết bằng vitest trên `validateGenericConfig`. Ví dụ case đầu:

```ts
it("M13: weighted_sum input là edge bị từ chối", () => {
  const res = validateGenericConfig({
    version: "1.0", title: "t",
    objects: [
      { id: "a", type: "node", label: "A" }, { id: "b", type: "node", label: "B" },
      { id: "e1", type: "edge", label: "AB", from: "a", to: "b" },
      { id: "kq", type: "value_box", label: "Tổng" },
    ],
    rules: [{ type: "weighted_sum", target: "kq", inputs: ["e1"], weights: [1] }],
    interactions: [], processes: [],
  });
  expect(res.ok).toBe(false);
  if (!res.ok) expect(res.error).toContain("không có nguồn giá trị");
});
```

(3 case còn lại cùng khuôn — spec đầy đủ từng case, không "tương tự": chuỗi đảo dùng objects `x` switch value 1 / `mid`,`kq` value_box + 2 rule đảo thứ tự, expect `ok === true`; boolean-từ-value_box dùng `v` value_box value 5 + `den` lamp + rule boolean not, expect từ chối; provider-thiếu-value dùng `s` switch KHÔNG value + `kq` + rule weighted_sum, expect từ chối.)

- [ ] **Step 2: RED** — `cd frontend && npx vitest run src/simulations/domains/generic/generic.test.ts -t "M13"` → case reject FAIL.

- [ ] **Step 3: Cài** — `validate.ts` import contract SINH RA (không hằng viết tay):

```ts
import dslContract from "./dsl-contract.json";
```

sau khối chu trình:

```ts
  // M13 §3.2 + blocker 3: operand coherence với role-typing — contract SINH từ
  // manifest backend (dsl-contract.json), sync-lock test backend chống drift.
  const objById = new Map(objects.map((o) => [o.id, o]));
  const ruleIo = dslContract.rule_io as Record<string, { input_role: string; output_role: string }>;
  const targetOutputRole = new Map(rules.map((r) => [r.target, ruleIo[r.type].output_role]));
  const coercions = new Set(
    (dslContract.role_coercions as { from: string; to: string }[]).map((c) => `${c.from}->${c.to}`),
  );
  const objectRoles = dslContract.object_roles as Record<string, string[]>;
  for (const r of rules) {
    // Ràng buộc 2: target phải chấp nhận output role của rule (parity backend).
    const outRole = ruleIo[r.type].output_role;
    const targetObj = objById.get(r.target)!;
    if (!objectRoles[targetObj.type]?.includes(outRole)) {
      return {
        ok: false,
        error:
          `Rule ${r.type} sinh giá trị vai trò "${outRole}" nhưng target "${r.target}" ` +
          `(${targetObj.type}) không nhận được vai trò đó.`,
      };
    }
    const need = ruleIo[r.type].input_role;
    const providers: string[] = (dslContract.value_providers as Record<string, string[]>)[need];
    for (const inp of r.inputs) {
      const out = targetOutputRole.get(inp);
      if (out !== undefined) {
        if (out !== need && !coercions.has(`${out}->${need}`)) {
          return {
            ok: false,
            error:
              `Rule "${r.target}" dùng input "${inp}" là kết quả rule khác có vai trò "${out}", ` +
              `nhưng rule ${r.type} cần vai trò "${need}" — không có coercion được khai.`,
          };
        }
        continue; // derived + đúng role → defer theo bound lúc chạy
      }
      const o = objById.get(inp)!;
      if (!providers.includes(o.type) || o.value === undefined) {
        return {
          ok: false,
          error:
            `Rule "${r.target}" dùng input "${inp}" (${o.type}) không có nguồn giá trị ` +
            `${need} theo hợp đồng DSL — chỉ chấp nhận ${providers.join(", ")} có "value" ` +
            `hoặc target của một rule cùng vai trò.`,
        };
      }
    }
  }
```

(`objects`/`rules` là biến sẵn có trong `validate.ts` — dùng đúng tên hiện hành trong file. Vite hỗ trợ import JSON sẵn, không cần config.) Thêm 4 test mirror của 4 test role-typing Task 3: weighted_sum-target nuôi boolean → reject · chain numeric→numeric → ok · weighted_sum ghi vào node → reject (`không nhận được`) · boolean ghi vào lamp → ok.

- [ ] **Step 4: GREEN + parity backend↔frontend** — vitest block M13 PASS; toàn `npm test` PASS. Đối chiếu tay: 8 case Task 3 và Task 5 cùng phán quyết từng case (ghi vào commit message).

- [ ] **Step 5: Commit** — `M13: validator frontend tiêu thụ dsl-contract.json — operand coherence + role-typing parity backend`

---

### Task 6: Frontend — runtime three-state + `GenericExecutionError` + fail-closed ở store

**Files:**
- Modify: `frontend/src/simulations/domains/generic/model.ts` (`evalRule`, `valuesOf`)
- Modify: `frontend/src/simulations/domains/generic/index.ts` (init fail-fast: gọi `valuesOf` một lần)
- Modify: `frontend/src/state/store.ts` (bọc `mod.init` — hiện dòng ~214 — bằng try/catch, domain-blind)
- Test: `frontend/src/simulations/domains/generic/generic.test.ts` (+ block M13 runtime), `frontend/src/state/` test store sẵn có (thêm 1 case)

**Interfaces:**
- Produces: `class GenericExecutionError extends Error { code: "invalid_numeric_source" | "missing_weight" | "unresolved_dependency_after_bound" | "non_finite_numeric_value" }` export từ `model.ts`. Store: `mod.init` ném bất kỳ Error nào → `analysisError` tiếng Việt thân thiện, `active` giữ null. Task 7 dùng cả hai.

- [ ] **Step 1: Viết test fail** — mirror 3 test Task 4 bằng vitest trên `valuesOf` (chuỗi đảo đúng giá trị · operand vắng → throw code `unresolved_dependency_after_bound` · non-finite → throw code tương ứng), cộng test store:

```ts
it("M13: init ném lỗi → analysisError thân thiện, không crash, không active", () => {
  // envelope generic có spec qua ĐƯỢC validate cũ nhưng nổ khi evaluate —
  // dùng monkeypatch: module giả với init ném GenericExecutionError.
  // (đường thật: fixture Dijkstra ở Task 7 — test này khoá HÀNH VI STORE.)
});
```

Cách cài test store: `registerSimulation` một module giả id `generic.rule_scene`-shaped (hoặc spy `getSimulation`) có `validateConfig` ok + `init` throw; gọi `loadEnvelope`; expect `analysisError` chứa "Mô phỏng này không còn mở được" và `active === null`.

- [ ] **Step 2: RED** — vitest → FAIL.

- [ ] **Step 3: Cài** — `model.ts`: port đúng thuật toán Task 4 Step 3 sang TS (class `GenericExecutionError`; `evalRule` ném khi input vắng/weight lệch/`!Number.isFinite(result)`; `valuesOf` bỏ seed-0, vòng pending/still, ném `unresolved_dependency_after_bound` khi không tiến triển). `index.ts` init:

```ts
    init: (spec) => {
      const base = initialBase(spec);
      valuesOf(spec, base); // M13 fail-fast: spec không evaluate được thì FAIL Ở ĐÂY, không tới render
      return { spec, base, pos: layoutPositions(spec), timeline: buildTimeline(spec), cursor: 0 };
    },
```

`store.ts` (loadEnvelope, quanh dòng 209-215): bọc `mod.init(result.config)`:

```ts
      let initialState: unknown;
      try {
        initialState = mod.init(result.config);
      } catch {
        set({
          analysisError:
            "Mô phỏng này không còn mở được: cấu hình không vượt qua kiểm tra an toàn hiện hành. " +
            "Hãy phân tích lại đề để tạo mô phỏng mới.",
          activeSampleId: null,
        });
        return;
      }
```

rồi dùng `state: initialState` trong `set({ active: … })`. Lưu ý: ghi lịch sử (`historyStore.record`) phải nằm SAU init thành công — di chuyển dòng record xuống nếu cần, để envelope hỏng không được record lại.

- [ ] **Step 4: GREEN** — vitest M13 + toàn `npm test` PASS (test M11 mode-switch/nested boolean là canary ngữ nghĩa giữ nguyên).

- [ ] **Step 5: Commit** — `M13: runtime frontend ba trạng thái + GenericExecutionError + store fail-closed khi init nổ`

---

### Task 7: Fixture Dijkstra — khôi phục/tái dựng + khoá hai phía

**Files:**
- Create: `backend/tests/fixtures/m13_dijkstra_pseudo_algorithm.json`
- Test: `backend/tests/test_m13_dijkstra_fixture.py` (mới)
- Test: thêm 1 case vào test store frontend (Task 6 file) dùng bản TS của fixture

**Interfaces:**
- Consumes: validator Task 3/5, store fail-closed Task 6.
- Produces: fixture JSON `{"source": "...", "config": {…spec generic…}}` — Task 8/10 tái dùng `config`.

- [ ] **Step 1: Thử khôi phục artifact THẬT (best-effort, ghi kết quả vào trường `source`)**

```bash
# SQLite (backend chạy standalone):
cd backend && .venv/Scripts/python -c "
import json, sqlite3, glob
for db in glob.glob('*.db'):
    con = sqlite3.connect(db)
    try:
        rows = con.execute(\"select key, envelope_json from simulation_cache\").fetchall()
        for k, e in rows:
            if 'Dijkstra' in e or 'dijkstra' in e: print(db, k); print(e[:2000])
    except Exception as ex: print(db, 'skip:', ex)
"
# Postgres (nếu volume còn): docker compose up -d db rồi
docker compose exec db psql -U postgres -c "select key from simulation_cache" 2>/dev/null || true
```

Tìm thấy → dùng envelope thật làm fixture, `"source": "recovered_from_simulation_cache"`. Không thấy → **stop-condition #1 áp dụng dạng nhẹ**: dùng bản tái dựng dưới đây, `"source": "reconstructed_from_screenshot_2026-07-16"`, KHÔNG trình bày như artifact gốc.

- [ ] **Step 2: Fixture tái dựng** (khớp ảnh chụp: 3 nút, 3 cạnh, 2 vật di chuyển, 2 ô calc, 2 `weighted_sum` trên id CẠNH — đúng shape bug):

```json
{
  "source": "reconstructed_from_screenshot_2026-07-16",
  "config": {
    "version": "1.0",
    "title": "Mô phỏng so sánh đường đi trong thuật toán Dijkstra",
    "objects": [
      { "id": "node_A", "type": "node", "label": "node_A" },
      { "id": "node_B", "type": "node", "label": "node_B" },
      { "id": "node_C", "type": "node", "label": "node_C" },
      { "id": "edge_AB", "type": "edge", "label": "edge_AB", "from": "node_A", "to": "node_B" },
      { "id": "edge_BC", "type": "edge", "label": "edge_BC", "from": "node_B", "to": "node_C" },
      { "id": "edge_AC", "type": "edge", "label": "edge_AC", "from": "node_A", "to": "node_C" },
      { "id": "runner_ABC", "type": "moving_entity", "label": "Đường A-B-C" },
      { "id": "runner_AC", "type": "moving_entity", "label": "Đường A-C" },
      { "id": "calc_path_ABC", "type": "value_box", "label": "calc_path_ABC" },
      { "id": "calc_path_AC", "type": "value_box", "label": "calc_path_AC" }
    ],
    "rules": [
      { "type": "weighted_sum", "target": "calc_path_ABC", "inputs": ["edge_AB", "edge_BC"], "weights": [1, 1] },
      { "type": "weighted_sum", "target": "calc_path_AC", "inputs": ["edge_AC"], "weights": [1] }
    ],
    "interactions": [],
    "processes": [
      { "type": "move_along_path", "entity": "runner_ABC", "path": ["node_A", "node_B", "node_C"] },
      { "type": "move_along_path", "entity": "runner_AC", "path": ["node_A", "node_C"] }
    ]
  }
}
```

(Nếu Step 1 khôi phục được bản thật: thay `config` bằng bản thật, giữ nguyên test.)

- [ ] **Step 3: Test backend (GREEN ngay nhờ Task 3 — đây là REGRESSION LOCK, không RED)**

```python
# backend/tests/test_m13_dijkstra_fixture.py
"""M13 §6.1: artifact pseudo-Dijkstra KHÔNG BAO GIỜ qua được validator nữa."""
import json
from pathlib import Path
from app.simulation.dsl.validator import validate_generic_config

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "m13_dijkstra_pseudo_algorithm.json").read_text(encoding="utf-8"))


def test_artifact_dijkstra_cu_bi_validator_tu_choi():
    config, err = validate_generic_config(FIXTURE["config"])
    assert config is None
    assert "không có nguồn giá trị" in err
```

Chạy: PASS. **Kiểm chứng nó là lock thật**: tạm comment khối coherence Task 3 → test này phải ĐỎ → bỏ comment (fault-injection, anti-pattern #14).

- [ ] **Step 4: Test frontend history-reopen graceful-fail** — trong test store: dựng envelope `{simulation_id: "generic.rule_scene", config: <fixture config>}`, gọi `loadEnvelope` → expect `analysisError` chứa "không còn mở được" HOẶC lỗi validate tiếng Việt, `active === null`, không throw. (Đường `validateConfig` chặn trước init — cả hai nhánh đều fail-closed; assert không crash là điểm chính. 0 AI hiển nhiên: guard fetch của `test-setup.ts`.)

- [ ] **Step 5: Commit** — `M13: fixture pseudo-Dijkstra (reconstructed) + regression lock hai phía`

---

### Task 8: FP-budget offline — mọi cảnh hợp lệ sẵn có vẫn xanh

**Files:**
- Test: `backend/tests/test_m13_fp_budget.py` (mới)
- Test: frontend — thêm block vào `generic.test.ts`

**Interfaces:**
- Consumes: validator + engine mới (Task 3–6); sample thật `frontend/src/data/sim-samples.ts:130` (đổi nhị phân: switch bit0..bit3 + weighted_sum → out).

- [ ] **Step 1: Frontend** — test: sample đổi-nhị-phân trong `sim-samples.ts` (import trực tiếp, tìm entry chứa rule weighted_sum) qua `validateGenericConfig` → ok, và `valuesOf` chạy không ném, giá trị `out` đúng tổng bit×weight. Cảnh đồ thị CẤU TRÚC hợp lệ (node/edge + reveal, KHÔNG rule) → vẫn ok.
- [ ] **Step 2: Backend** — mirror: spec đổi-nhị-phân tối giản (4 switch value 0/1, weights 8/4/2/1) qua `validate_generic_config` + `values_of` → ok; spec đồ thị cấu trúc (node/edge/reveal, không rule) → ok. Nested-boolean M11 shape (switch → boolean AND → lamp trung gian → boolean OR → lamp cuối) → ok + evaluate đúng bảng chân trị 2 dòng đại diện.
- [ ] **Step 3: Chạy TOÀN BỘ hai suite** — `python -m pytest` + `npm test`: mọi test sẵn có xanh = FP budget offline đạt. Bất kỳ đỏ nào → stop-condition #3.
- [ ] **Step 4: Commit** — `M13: FP-budget offline — sample nhị phân/đồ thị cấu trúc/nested boolean vẫn xanh sau siết`

---

### Task 9: Gate B — SERVER-SIDE computation-ownership check + taxonomy prompt + CACHE_VERSION

**Files:**
- Modify: `backend/app/ai/pipeline.py` (schema analyze ~dòng 60-70: thêm field `result_ownership`; đường generic trong `run_pipeline`: gọi check mới)
- Create: `backend/app/simulation/computation_gate.py` (check tất định, ~30 dòng)
- Modify: `backend/app/ai/skills/analyze.md` (mục `arbitrary_algorithm` + dạy field `result_ownership`)
- Modify: `backend/app/ai/skills/classify.md` (thêm quy tắc 4c cạnh 4b)
- Modify: `backend/app/main.py:73` (`CACHE_VERSION = "10"`)
- Test: `backend/tests/test_m13_routing.py` (mới); test cache sẵn có (thêm 1 case nếu chưa có case version-mismatch)

**Interfaces:**
- Consumes: cơ chế gap sẵn có (`known_gap_roles()`, `build_representation_plan`, E7/E15) + field analyze MỚI.
- Produces: `check_computation_ownership(analysis: dict, plan: dict) -> str | None` — trả reason tiếng Việt khi phải gap, `None` khi đi tiếp. **SERVER ra phán quyết cuối** trên hai tín hiệu CÓ CẤU TRÚC **BỔ SUNG** nhau (không claim "độc lập" — cả hai cùng ra từ MỘT lần gọi analyze, có thể fail tương quan): (i) known-gap roles trong role tags, (ii) enum `result_ownership` **bắt buộc, fail-closed**. LLM bỏ sót MỘT tín hiệu vẫn còn tín hiệu kia; bỏ sót CẢ HAI thì lớp validator (Task 3/5) vẫn chặn shape numeric-fakery. `result_ownership` thiếu/ngoài enum → **reject/retry, KHÔNG default** sang bất kỳ giá trị nào. Giới hạn trung thực ghi vào docs (Task 13): server không đọc đề tiếng Việt trực tiếp — làm vậy là keyword-patch trá hình.

- [ ] **Step 0a: Schema + gate tất định.** Schema analyze (pipeline.py ~dòng 60-70) thêm:

```python
        "result_ownership": {
            "type": "STRING",
            "enum": ["provided", "rule_derivable", "algorithmic"],
        },
```

**BẮT BUỘC**: thêm `"result_ownership"` vào danh sách `required` của schema analyze (kiểm tên danh sách trong file). Fail-closed hai lớp: (1) structured output + required ép Gemini phải phát giá trị trong enum; (2) gate phòng thủ — giá trị thiếu/ngoài enum vẫn lọt tới server → **reject với reason trung thực, KHÔNG default** (test bên dưới). `backend/app/simulation/computation_gate.py`:

```python
"""M13 gate B lớp (a): computation-ownership — SERVER quyết, tất định, sau classify,
CHỈ trên đường generic (giữ carve-out chuyên biệt E7). Không đọc text đề."""
from app.simulation.dsl.manifest import known_gap_roles


def check_computation_ownership(analysis: dict, plan: dict) -> str | None:
    """Trả reason (tiếng Việt) khi yêu cầu đòi CƠ CHẾ TÍNH KẾT QUẢ mà không engine
    nào sở hữu → capability_gap; None khi generic được phép tiếp tục."""
    gaps = sorted(set(plan.get("unsupported_capabilities", [])) & known_gap_roles())
    if gaps:
        return (
            f"Bài cần cơ chế chưa có engine tất định sở hữu ({', '.join(gaps)}) — "
            "hệ từ chối trung thực thay vì dựng cảnh xấp xỉ."
        )
    ownership = analysis.get("result_ownership")
    if ownership not in ("provided", "rule_derivable"):
        # Fail-closed (ràng buộc duyệt lần 3): "algorithmic" → gap có chủ đích;
        # thiếu/ngoài enum → CŨNG từ chối, không default sang giá trị nào.
        if ownership == "algorithmic":
            return (
                "Kết quả của bài phải được TÍNH qua cơ chế thuật toán riêng mà không "
                "engine tất định nào của hệ sở hữu — hệ từ chối trung thực thay vì để "
                "AI tự giải rồi dựng cảnh minh hoạ đáp án."
            )
        return (
            "Phân tích không xác định được nguồn kết quả của bài (result_ownership "
            f"= {ownership!r}) — hệ từ chối an toàn thay vì đoán."
        )
    return None
```

`run_pipeline`: trên nhánh generic (nơi đã có phán quyết gap E7), thay/bổ khối hiện hành bằng gọi `check_computation_ownership(analysis, plan)` — reason không None → trả `{"status": "unsupported", "reason": reason, "failure_category": "capability_gap", ...}` đúng shape hiện hành (giữ nguyên các trường envelope unsupported sẵn có trong file).

- [ ] **Step 0b: Dạy field mới trong `analyze.md`** — thêm vào CÁC TRƯỜNG TRÍCH XUẤT:

```markdown
- result_ownership: kết quả cuối của bài đến từ đâu — "provided" (đề cho sẵn kết quả/diễn biến, chỉ cần dựng/hiển thị); "rule_derivable" (tính được bằng phép logic/tổng có trọng số TỪ các giá trị đề cho sẵn — vd đèn theo công tắc, đổi nhị phân); "algorithmic" (kết quả phải được TÍNH qua cơ chế thuật toán nhiều bước — chọn/loại/cập nhật lặp lại — mà đề KHÔNG cho sẵn: đường đi ngắn nhất, thứ tự duyệt, cây khung...). Trung thực: không biết chắc → "algorithmic" nếu đề yêu cầu "mô phỏng thuật toán X" với X không phải duyệt-dãy/sắp xếp cơ bản.
```

- [ ] **Step 1: Sửa `analyze.md`** — mục `arbitrary_algorithm` hiện kết thúc ở "…không gắn tag này)." Thay bằng:

```markdown
- arbitrary_algorithm: yêu cầu mô phỏng một thuật toán do người dùng tự nghĩ/không mô tả cụ thể, HOẶC thực thi TỪNG BƯỚC một vòng lặp trên biến tự do (biến được cập nhật qua mỗi vòng lặp, kể cả khi mô tả cụ thể như "x tăng thêm 3 mỗi vòng"), HOẶC yêu cầu THỰC THI một thuật toán CÓ TÊN mà kết quả phải được TÍNH RA qua cơ chế của chính thuật toán đó (chọn đỉnh gần nhất, cập nhật khoảng cách, quay lui, quy hoạch động... — ví dụ: Dijkstra, DFS/BFS trên đồ thị tổng quát, tô màu đồ thị) — khác với DUYỆT một dãy số cho sẵn để tìm/đếm/tính tổng/sắp xếp (những bài đó có mô phỏng chuyên biệt, không gắn tag này). DẤU HIỆU: kết quả cuối (đường đi ngắn nhất, cây khung, thứ tự duyệt) KHÔNG được đề cho sẵn mà phải do thuật toán tính ra.
```

- [ ] **Step 2: Sửa `classify.md`** — thêm sau quy tắc 4b:

```markdown
4c. THUẬT TOÁN CÓ TÊN TÍNH KẾT QUẢ, KHÔNG ENGINE NÀO SỞ HỮU → unsupported: đề yêu cầu mô phỏng một thuật toán mà kết quả (đường đi ngắn nhất có trọng số, cây khung nhỏ nhất, thứ tự duyệt đồ thị...) phải được TÍNH qua cơ chế riêng của thuật toán đó (khoảng cách tạm, chọn đỉnh gần nhất, nới cạnh, quay lui...). network.packet_routing chỉ minh hoạ đường đi BFS trên mạng — KHÔNG phải Dijkstra có trọng số; ĐỪNG gán "gần giống". ĐỪNG ép về generic.rule_scene bằng cách khai sẵn các đường đi ứng viên + ô tổng trọng số: khi đó chính bạn đã TỰ GIẢI bài toán thay vì engine tất định — đúng điều quy tắc 4b cấm. Thà unsupported trung thực. (Vẫn CHO PHÉP generic khi đề chỉ cần VẼ/DỰNG đồ thị làm cấu trúc — không đòi tính kết quả thuật toán.)
```

- [ ] **Step 3: `CACHE_VERSION` `"9"` → `"10"`** kèm comment `# M13: operand coherence + taxonomy arbitrary_algorithm mở rộng`.

- [ ] **Step 4: Test offline routing + cache**

```python
# backend/tests/test_m13_routing.py
"""M13 §4: SERVER quyết accept/gap — tất định, KHÔNG mock LLM thật, hai tín hiệu bổ sung."""
from app.simulation.computation_gate import check_computation_ownership
from app.simulation.representation import build_representation_plan


def _analysis(**over):
    base = {
        "entity_roles": ["relational"], "relation_roles": ["relational"],
        "process_roles": ["movement"], "interaction_needs": [],
        "visual_needs": ["relational"], "temporal_needs": ["temporal"],
        "result_ownership": "provided",
    }
    base.update(over)
    return base


def test_kenh_1_arbitrary_algorithm_role_lam_gap_fired():
    analysis = _analysis(process_roles=["arbitrary_algorithm", "movement"])
    plan = build_representation_plan(analysis)
    assert check_computation_ownership(analysis, plan) is not None


def test_kenh_2_result_ownership_algorithmic_gap_KE_CA_khi_role_bi_bo_sot():
    """Blocker 1: analyze quên arbitrary_algorithm nhưng khai algorithmic →
    server VẪN gap. Phán quyết không phụ thuộc một kênh prompt duy nhất."""
    analysis = _analysis(result_ownership="algorithmic")  # KHÔNG có role gap
    plan = build_representation_plan(analysis)
    assert plan["unsupported_capabilities"] == []  # kênh 1 im
    reason = check_computation_ownership(analysis, plan)
    assert reason is not None and "thuật toán" in reason


def test_canh_cau_truc_hop_le_khong_bi_gap():
    analysis = _analysis()  # provided, không role gap
    plan = build_representation_plan(analysis)
    assert check_computation_ownership(analysis, plan) is None


def test_rule_derivable_khong_bi_gap():
    """Đổi nhị phân / đèn-công tắc: tính bằng rule từ giá trị cho sẵn — đi tiếp."""
    analysis = _analysis(result_ownership="rule_derivable", entity_roles=["numeric", "interactive"])
    plan = build_representation_plan(analysis)
    assert check_computation_ownership(analysis, plan) is None


def test_result_ownership_thieu_hoac_la_bi_tu_choi_an_toan():
    """Ràng buộc duyệt lần 3: fail-closed — thiếu/ngoài enum KHÔNG default."""
    for bad in (None, "", "unknown", "maybe_algorithmic"):
        analysis = _analysis()
        if bad is None:
            analysis.pop("result_ownership")
        else:
            analysis["result_ownership"] = bad
        plan = build_representation_plan(analysis)
        reason = check_computation_ownership(analysis, plan)
        assert reason is not None and "từ chối an toàn" in reason
```

Cache: nếu chưa có test version-mismatch, thêm vào file test cache sẵn có: row `policy_version="9"` → `_cache_lookup` trả None (envelope luật cũ không bao giờ được trả lại).

- [ ] **Step 5: Restart-note + cập nhật fixture CHỦ ĐÍCH + toàn suite** — (a) `load_skill` cache per process → backend phải restart sau khi sửa .md (ghi vào commit message). (b) **Hệ quả fail-closed đã lường trước**: mọi fixture analysis trong test sẵn có (test_pipeline, test_evaluation... — mock analyze output) CHƯA có `result_ownership` → gate sẽ từ chối trên đường generic. Cập nhật các fixture đó với giá trị ĐÚNG NGỮ NGHĨA từng case (`provided` cho cảnh dựng/hiển thị, `rule_derivable` cho logic/nhị phân) — đây là cập nhật hợp đồng có chủ đích, KHÔNG phải nới gate cho test xanh; fixture nào KHÓ gán trung thực → dấu hiệu case đó cần xem lại, dừng hỏi thay vì đoán. (c) `python -m pytest` xanh.

- [ ] **Step 6: Commit** — `M13: computation_gate server-side (2 kênh tín hiệu) + result_ownership + taxonomy arbitrary_algorithm mở rộng + classify 4c + CACHE_VERSION 10`

---

### Task 10: Pattern reuse — revalidation lock

**Files:**
- Test: `backend/tests/test_m13_pattern_revalidate.py` (mới)

- [ ] **Step 1: Test** — gọi thẳng `run_gates` (patterns.py:184) với candidate = `config` của fixture Task 7 (shape weighted_sum-trên-edge), scene_mode/roles khớp: expect trả `(None, err)` và `"structural:"` trong err → chứng minh pattern cũ mang shape cấm bị `validate_generic_config` (đã siết) chặn ngay cổng 1, fallback compose, không poison. Thêm case dương: config đổi-nhị-phân hợp lệ → `run_gates` trả config, không err.
- [ ] **Step 2: PASS ngay (regression lock)** — fault-injection như Task 7 Step 3 để chứng minh lock thật.
- [ ] **Step 3: Commit** — `M13: lock — pattern reuse revalidate qua run_gates, shape cấm fallback compose`

---

### Task 11: Workstream C — runtime display label

**Files:**
- Modify: `frontend/src/simulations/domains/generic/model.ts` (`objLabel` → dùng `displayLabel`; export `displayLabel`)
- Modify: `frontend/src/simulations/domains/generic/ui.tsx` (chips/inspector: mọi chỗ render `o.label ?? o.id` hoặc `o.id` trực tiếp → `displayLabel(spec, o.id)`; grep `\.id` trong ui.tsx để tìm hết)
- Test: `generic.test.ts` (+ unit `displayLabel`), 1 render-test cho Inspector

- [ ] **Step 1: Viết test fail** — blocker 4: artifact thật có `label` BẰNG id (`label: "node_A"`), không chỉ thiếu label. Ba điều kiện sanitize: thiếu ∨ `label === id` ∨ dạng định danh kỹ thuật (form-based, không keyword):

```ts
it("M13: label thiếu → tên tiếng Việt theo type", () => {
  const spec = mk({ objects: [
    { id: "n1", type: "node" }, { id: "n2", type: "node" },
    { id: "v1", type: "value_box", value: 0 },
  ]});
  expect(displayLabel(spec, "n1")).toBe("Điểm 1");
  expect(displayLabel(spec, "n2")).toBe("Điểm 2");
  expect(displayLabel(spec, "v1")).toBe("Ô giá trị");
});

it("M13: label BẰNG id (ca Dijkstra thật) → sanitize, không rò", () => {
  const spec = mk({ objects: [
    { id: "node_A", type: "node", label: "node_A" },
    { id: "calc_path_ABC", type: "value_box", label: "calc_path_ABC", value: 0 },
  ]});
  expect(displayLabel(spec, "node_A")).toBe("Điểm");      // 1 node duy nhất → không đánh số
  expect(displayLabel(spec, "calc_path_ABC")).toBe("Ô giá trị");
});

it("M13: label dạng snake_case kỹ thuật (khác id) vẫn bị sanitize", () => {
  const spec = mk({ objects: [{ id: "e9", type: "edge", label: "edge_AB", from: "n1", to: "n2" }] });
  expect(displayLabel(spec, "e9")).toBe("Đoạn nối");
});

it("M13: label tiếng Việt thân thiện GIỮ NGUYÊN (không sanitize oan)", () => {
  const spec = mk({ objects: [
    { id: "runner_ABC", type: "moving_entity", label: "Đường A-B-C" },
    { id: "e1", type: "edge", label: "AB", from: "n1", to: "n2" },
  ]});
  expect(displayLabel(spec, "runner_ABC")).toBe("Đường A-B-C");
  expect(displayLabel(spec, "e1")).toBe("AB");
});
```

- [ ] **Step 2: RED** — vitest → FAIL (`displayLabel` chưa export).

- [ ] **Step 3: Cài** — `model.ts`:

```ts
/** M13 workstream C: tên hiển thị learner-facing — id nội bộ KHÔNG BAO GIỜ là nhãn chính. */
const TYPE_DISPLAY_VI: Record<string, string> = {
  switch: "Công tắc", lamp: "Đèn", value_box: "Ô giá trị", node: "Điểm",
  edge: "Đoạn nối", moving_entity: "Vật di chuyển", label: "Nhãn", container: "Khung",
  group: "Nhóm", heading: "Tiêu đề", paragraph: "Đoạn văn", text: "Chữ",
};

/** Dạng định danh kỹ thuật theo HÌNH THỨC (không keyword): snake/kebab-case
 * chuỗi ASCII — bắt node_A, edge_AB, calc_path_ABC; cho qua "Đường A-B-C"
 * (có dấu cách/ký tự tiếng Việt), "AB" (không có _/-). */
const TECHNICAL_ID_FORM = /^[A-Za-z0-9]+([_-][A-Za-z0-9]+)+$/;

function isTechnicalLabel(label: string | undefined, id: string): boolean {
  if (!label) return true;                 // thiếu
  if (label === id) return true;           // LLM điền label = id (ca Dijkstra thật)
  return TECHNICAL_ID_FORM.test(label) && !label.includes(" ");
}

export function displayLabel(spec: SimulationSpec, id: string): string {
  const o = spec.objects.find((x) => x.id === id);
  if (!o) return id; // sau validate không xảy ra; giữ để total
  if (!isTechnicalLabel(o.label, id)) return o.label!;
  const sameType = spec.objects.filter((x) => x.type === o.type);
  const base = TYPE_DISPLAY_VI[o.type] ?? o.type;
  return sameType.length > 1 ? `${base} ${sameType.findIndex((x) => x.id === id) + 1}` : base;
}
```

Lưu ý ngoại lệ có chủ đích: "Đường A-B-C" chứa `-` nhưng có dấu cách → không match (regex đòi TOÀN chuỗi là snake/kebab ASCII). Debug inspector giữ id thô ở DÒNG PHỤ.

`objLabel` nội bộ đổi thành `return displayLabel(spec, id)`. `ui.tsx`: thay mọi nhãn chính render từ id thô (chips ĐỐI TƯỢNG, QUY TẮC, narration đã ăn theo objLabel) sang `displayLabel`; **inspector debug được giữ id ở dòng phụ** (không phải nhãn chính).

- [ ] **Step 4: GREEN + render-test** — Inspector render với spec-không-label: DOM text KHÔNG match `/node_[A-Za-z]+|calc_path/` ở phần tử nhãn chính. Toàn `npm test` + `npm run build` sạch.

- [ ] **Step 5: Commit** — `M13: displayLabel learner-facing — id runtime không còn là nhãn chính`

---

### Task 12: Eval case Dijkstra + curriculum determination (docs + dataset)

**Files:**
- Modify: `backend/app/evaluation/datasets/capability.py` (thêm 1 EvalItem)
- Modify: `docs/COVERAGE.md` (mục mới: phán quyết Dijkstra)
- Test: `backend/tests/test_datasets.py` (admission tự chạy — không sửa)

- [ ] **Step 1: Kiểm curriculum** — grep `COVERAGE.md` + danh mục SGK trong đó cho "đồ thị/Dijkstra/đường đi ngắn nhất". Kết quả đã biết trước (chỉ BFS làm oracle routing): **kết luận A — ngoài phạm vi công khai**, trừ khi tìm được anchor (khi đó dừng, hỏi user — đổi kết luận là đổi roadmap).

- [ ] **Step 2: Thêm EvalItem** (nhóm `unsupported` — khớp hợp đồng harness sẵn có cho refusal; admission dùng chuỗi trung thực, KHÔNG anchor giả):

```python
EvalItem(
    "cap-dijkstra-gap",
    "Mô phỏng thuật toán Dijkstra tìm đường ngắn nhất từ A đến C trên đồ thị có trọng số.",
    "unsupported", None,
    tags=("boundary", "m13_soundness"),
    curriculum_area="ngoài phạm vi công khai Tin học THPT — không anchor SGK (COVERAGE §Dijkstra-M13)",
    curriculum_topic="Đồ thị có trọng số (ngoài phạm vi)",
    capability_family="algorithmic_computation_gap",
    complexity="L4",
    result_mode="unsupported",
    learning_objective="Hệ từ chối trung thực yêu cầu thuật toán không có engine, thay vì render cảnh giả.",
    pedagogical_rationale=(
        "Cơ chế ẩn của Dijkstra — khoảng cách tạm, extract-min, nới cạnh, tập finalized — "
        "KHÔNG có engine tất định nào sở hữu; cảnh generic với đường đi khai sẵn và tổng trọng số "
        "trên id cạnh dạy SAI cơ chế (LLM tự giải bài thay engine). capability_gap trung thực "
        "tốt hơn một pseudo-simulation trông-hợp-lý."
    ),
),
```

- [ ] **Step 3: `docs/COVERAGE.md`** — mục "Dijkstra / đường đi ngắn nhất có trọng số (M13)": phán quyết A + căn cứ (không title SGK nào; BFS packet_routing là minh hoạ mạng, không phải shortest-path tổng quát) + hệ quả: `graph.shortest_path` KHÔNG vào roadmap đề tài; đổi phán quyết cần approval mới.

- [ ] **Step 4: Chạy** — `python -m pytest tests/test_datasets.py -v` → PASS (admission). Toàn suite xanh.

- [ ] **Step 5: Commit** — `M13: eval case cap-dijkstra-gap (admission trung thực, ngoài phạm vi) + COVERAGE phán quyết Dijkstra`

---

### Task 13: Verify offline toàn cục + docs milestone

**Files:**
- Modify: `docs/CURRENT_STATE.md` (mục M13 + nhật ký live để trống chờ Task 14), `docs/CODE_INDEX.md` (symbol mới: `value_provider_types`, `GenericEvaluationError`, `GenericExecutionError`, `displayLabel`), `docs/ARCHITECTURE_MAP.md` (bất biến #20: operand của numeric rule phải có nguồn giá trị theo manifest; enforcing files + tests)

- [ ] **Step 1:** `cd backend && python -m pytest` → toàn xanh, ghi số pass.
- [ ] **Step 2:** `cd frontend && npm test` → toàn xanh; `npm run build` → sạch.
- [ ] **Step 3:** `npm run audit:layout` (dev server chạy) — 4/4 route (UI chỉ đổi nhãn — vẫn kiểm vì đó là lớp lỗi vitest mù).
- [ ] **Step 4:** Cập nhật 3 docs; commit `M13: docs — CURRENT_STATE/CODE_INDEX/ARCHITECTURE_MAP (bất biến #20)`.

---

### Task 14: STOP GATE — live smoke có mục tiêu (cần user duyệt tường minh)

**KHÔNG tự chạy.** Prompt đã đổi (Task 9) ⇒ theo spec cần live smoke, nhưng chỉ khi user bật.

- [ ] **Step 1: Hỏi user** — xin phép chạy với ngân sách: `ALLOW_LIVE_AI=1 python -m app.evaluation.live --dataset capability --suite m13_soundness --max-api-calls 15` (case `cap-dijkstra-gap`) + nếu user đồng ý rộng hơn: rerun `m11_compose` + `m12_scan` (đối chứng FP, ~9 case logic).
- [ ] **Step 2: Chạy đúng ngân sách được duyệt**; kỳ vọng: Dijkstra → `unsupported` (gap fired, không false positive mới trên suite đối chứng).
- [ ] **Step 3: Ghi nhật ký live CHÍNH XÁC** vào `docs/CURRENT_STATE.md` (case logic · HTTP · retry · 429) + báo cáo cuối theo spec §14 (root cause hai lỗi, before/after routing, gate, fixtures, files, tests/build, limitations, phán quyết curriculum, không tự bắt đầu graph.shortest_path).
- [ ] **Step 4: Stop-condition #4** — LLM không học taxonomy sau 1 lần vá → DỪNG báo user, không đuổi.

---

## Sau M13 (đề xuất, KHÔNG bắt đầu tự động)

**M14 — Catalog-Wide Capability Spec Architecture**: áp khuôn M11/M12 (LLM sinh
bounded spec → validator → adapter → executor tất định SẴN CÓ) cho mọi họ mô
phỏng công khai. M13 KHÔNG claim đã hoàn tất điều này — M13 chỉ đảm bảo generic
path là sound. M14 cần spec + approval riêng.

## Self-review (đã chạy khi viết + amend plan)

- **Spec coverage:** A (T2–T6, T8) · B (T9 — server gate 2 kênh + prompt, T12) · C (T11 — sanitize 3 điều kiện) · cache/pattern (T9, T10) · history (T6-store, T7) · two-layer regression (T7 offline, T12+T14 live) · matrix audit (T1) · curriculum (T12); README ngoài phạm vi (đúng spec §13).
- **4 blocker duyệt có điều kiện:** (1) `computation_gate.py` — server quyết trên 2 kênh cấu trúc, test chứng minh gap fired kể cả khi role bị bỏ sót; (2) `dsl-contract.json` sinh từ manifest + sync-lock, không allowlist TS tay; (3) role-typing derived targets, coercion DENY mặc định (`role_coercions: []`), test 2 chiều; (4) sanitize label thiếu ∨ ==id ∨ dạng kỹ thuật form-based, test giữ nguyên label thân thiện.
- **Placeholder:** không còn "tương tự Task N" cho code load-bearing.
- **Type consistency:** hợp đồng duy nhất `dsl_semantic_contract()` → JSON → cả hai validator; 4 mã lỗi runtime trùng khớp py↔ts; chuỗi lỗi `không có nguồn giá trị`/`vai trò` dùng chung 2 tầng để test khớp.
