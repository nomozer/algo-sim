# -*- coding: utf-8 -*-
"""Validated Simulation Pattern Reuse (M7.13B) — tầng 2/3 của reuse.

Nguyên tắc:
- KHÔNG embeddings/pgvector/RAG — matching TẤT ĐỊNH theo chữ ký cấu trúc,
  exact-match (ngưỡng 1.0, cố tình bảo thủ ở v1).
- Reuse KHÔNG bypass validation: mọi spec adapt xong đều qua ĐỦ 4 cổng
  (structural → scene-mode consistency → semantic compatibility → engine build).
- Template extraction chỉ tham số hóa SAFE ALLOWLIST (title/text/label/
  giá trị switch/weights/narration); cấu trúc, bool op, processes,
  interactions + constraints ĐÓNG BĂNG — không auto-generalize operator.
- Pattern KHÔNG bao giờ bị sửa tại chỗ khi adapt (instantiate ra bản mới).

Module này THUẦN (không LLM, không HTTP) — call Gemini cho slot chưa
resolve nằm ở pipeline (stage_adapt).
"""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timezone

from app.persistence.db import SessionLocal, SimulationPattern
from app.simulation.dsl.manifest import DSL_VERSION, SUPPORTED_VERSIONS, roles_of_primitive
from app.simulation.dsl.validator import validate_generic_config
from app.simulation.generic_engine import build_timeline, initial_base, values_of
from app.simulation.representation import check_scene_consistency
from app.simulation.semantic import check_semantic_compatibility

# Đánh dấu slot trong template: {"$slot": "<tên>"} — không thể nhầm với giá trị
# thật vì validator cấm dict lồng ở các vị trí này.
SLOT_KEY = "$slot"

AUTO_REUSE_STATUSES = ("verified", "validated")  # candidate KHÔNG auto-reuse


def _slot(name: str) -> dict:
    return {SLOT_KEY: name}


# ── Chữ ký cấu trúc (identity) ────────────────────────────────

def spec_signature(scene_mode: str, semantic_roles: set[str], spec: dict) -> dict:
    """Chữ ký pattern (đã duyệt): scene_mode + semantic_roles + object types +
    rule types + OPERATORS cụ thể + process types + interaction types KÈM
    target type — static triangle ≠ draggable triangle."""
    by_id = {o["id"]: o for o in spec.get("objects", [])}
    return {
        "scene_mode": scene_mode,
        "semantic_roles": sorted(semantic_roles),
        "object_types": sorted({o["type"] for o in spec.get("objects", [])}),
        "rule_types": sorted({r["type"] for r in spec.get("rules", [])}),
        "rule_ops": sorted({r["op"] for r in spec.get("rules", []) if r.get("op")}),
        "process_types": sorted({p["type"] for p in spec.get("processes", [])}),
        "interaction_types": sorted({
            f'{i["type"]}:{by_id.get(i["target"], {}).get("type", "?")}'
            for i in spec.get("interactions", [])
        }),
    }


def pattern_key_of(signature: dict) -> str:
    return hashlib.sha256(
        json.dumps(signature, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


# ── Template extraction (safe deterministic allowlist) ────────

def extract_template(spec: dict) -> tuple[dict, dict, dict]:
    """Tách spec đã validate → (template có slot, parameter_schema, params gốc).

    Chỉ tham số hóa allowlist an toàn; mọi thứ khác giữ nguyên. params gốc
    dùng cho SELF-CHECK round-trip khi persist.
    parameter_schema: {tên_slot: {"kind": "string"|"bit"|"number_array",
                                  ("length": n), "example": giá_trị_gốc}}.
    """
    template = copy.deepcopy(spec)
    schema: dict = {}
    params: dict = {}

    def take(name: str, kind: str, value, **extra) -> dict:
        schema[name] = {"kind": kind, "example": value, **extra}
        params[name] = value
        return _slot(name)

    template["title"] = take("title", "string", spec["title"])
    for o in template.get("objects", []):
        if isinstance(o.get("text"), str):
            o["text"] = take(f"text_{o['id']}", "string", o["text"])
        if isinstance(o.get("label"), str):
            o["label"] = take(f"label_{o['id']}", "string", o["label"])
        if o.get("type") == "switch" and "value" in o:
            o["value"] = take(f"value_{o['id']}", "bit", o["value"])
    for ri, r in enumerate(template.get("rules", [])):
        if r.get("type") == "weighted_sum" and r.get("weights"):
            r["weights"] = take(f"weights_{ri}", "number_array", list(r["weights"]), length=len(r["weights"]))
    for pi, p in enumerate(template.get("processes", [])):
        for si, st in enumerate(p.get("steps", []) or []):
            if isinstance(st.get("narration"), str):
                st["narration"] = take(f"narr_{pi}_{si}", "string", st["narration"])
    template["notes"] = None  # notes là instance-specific, không vào template
    return template, schema, params


def instantiate(template: dict, params: dict):
    """Dựng spec mới từ template + params (pure — template gốc không bị sửa)."""

    def walk(node):
        if isinstance(node, dict):
            if set(node.keys()) == {SLOT_KEY}:
                return params[node[SLOT_KEY]]
            return {k: walk(v) for k, v in node.items()}
        if isinstance(node, list):
            return [walk(x) for x in node]
        return node

    return walk(template)


def validate_params(schema: dict, params: dict) -> str | None:
    """Kiểm kiểu tham số TRƯỚC khi instantiate — sai → fallback compose,
    không đưa giá trị rác vào template."""
    for name, meta in schema.items():
        if name not in params:
            return f'Thiếu tham số "{name}".'
        v = params[name]
        if meta["kind"] == "string":
            if not isinstance(v, str) or not v.strip():
                return f'Tham số "{name}" phải là chuỗi không rỗng.'
        elif meta["kind"] == "bit":
            if v not in (0, 1):
                return f'Tham số "{name}" phải là 0 hoặc 1.'
        else:  # number_array
            if (
                not isinstance(v, list)
                or len(v) != meta["length"]
                or not all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in v)
            ):
                return f'Tham số "{name}" phải là mảng {meta["length"]} số.'
    return None


def deterministic_fill(schema: dict, analysis: dict) -> tuple[dict, dict]:
    """Điền tham số KHÔNG cần LLM khi suy trực tiếp được từ analysis:
    number_array khớp độ dài với analysis.data[].values. Trả (đã điền,
    chưa resolve — để stage_adapt gọi 1 lượt LLM nhỏ)."""
    filled: dict = {}
    unresolved: dict = {}
    value_arrays = [
        list(d["values"])
        for d in analysis.get("data", [])
        if isinstance(d, dict) and isinstance(d.get("values"), list) and d["values"]
    ]
    for name, meta in schema.items():
        if meta["kind"] == "number_array":
            match = next((arr for arr in value_arrays if len(arr) == meta["length"]), None)
            if match is not None:
                filled[name] = match
                value_arrays.remove(match)
                continue
        unresolved[name] = meta
    return filled, unresolved


def covered_roles_of_template(template: dict) -> set[str]:
    """Vai trò ngữ nghĩa mà CẤU TRÚC template biểu diễn được — suy từ type
    của primitive (literal trong template, không phải slot) nên ỔN ĐỊNH,
    không phụ thuộc nhiễu gắn role của LLM analyze (bug live: analyze gắn
    thêm 'relational' cho trang web → exact-match theo plan roles vỡ)."""
    covered: set[str] = set()
    for section in ("objects", "rules", "interactions", "processes"):
        for item in template.get(section, []):
            t = item.get("type")
            if isinstance(t, str):
                covered |= roles_of_primitive(t)
    return covered


# ── 4 cổng — reuse không bypass validation ────────────────────

def run_gates(scene_mode: str, required_roles: set[str], candidate: dict) -> tuple[dict | None, str | None]:
    """structural → scene-mode consistency (M7.13A) → semantic compat →
    engine build. Trả (config chuẩn hóa, None) hoặc (None, lỗi)."""
    config, err = validate_generic_config(candidate)
    if config is None:
        return None, f"structural: {err}"
    mode_err = check_scene_consistency(scene_mode, config)
    if mode_err:
        return None, f"scene_mode: {mode_err}"
    compat = check_semantic_compatibility(required_roles, config)
    if not compat["ok"]:
        return None, f"semantic: thiếu vai trò {', '.join(compat['missing'])}"
    try:
        frames = build_timeline(config)
        values_of(config, initial_base(config))
        if not frames:
            return None, "engine: timeline rỗng"
    except Exception as exc:  # engine build phải THÀNH CÔNG mới được reuse/persist
        return None, f"engine: {exc}"
    return config, None


# ── Store (DB) ────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


# Các trường CẤU TRÚC/HÀNH VI của chữ ký — không gồm semantic_roles (đã xét
# riêng bằng subset chống nhiễu) và scene_mode (đã filter exact).
_STRUCTURAL_SIG_FIELDS = (
    "object_types",
    "rule_types",
    "rule_ops",
    "process_types",
    "interaction_types",
)


def _structural_key(row: SimulationPattern) -> str:
    """Chữ ký cấu trúc của một pattern row — dùng kiểm tính ĐỒNG NHẤT của pool
    ứng viên: hai pattern khác bất kỳ trường nào dưới đây là hai cấu trúc/hành
    vi khác nhau, không được thay thế cho nhau."""
    sig = json.loads(row.signature_json)
    return json.dumps({k: sig.get(k, []) for k in _STRUCTURAL_SIG_FIELDS}, sort_keys=True)


class DbPatternStore:
    """Cầu nối pipeline ↔ bảng simulation_patterns. Pipeline nhận store qua
    tham số (inject) — không có store thì hành vi compose cũ giữ nguyên.
    policy_version do NGƯỜI TẠO store cung cấp (main.py giữ CACHE_VERSION)."""

    def __init__(self, policy_version: str = "0"):
        self.policy_version = policy_version

    def find(self, scene_mode: str, required_roles: set[str]) -> SimulationPattern | None:
        """Match tất định (không embedding, không keyword). Eligibility v1 BẢO THỦ:
        - scene_mode: EXACT;
        - required_roles ⊆ vai trò CẤU TRÚC template biểu diễn được (suy từ
          primitive types — subset CHỈ để chống nhiễu gắn role của analyze);
        - process/interaction+target/rule+op/object types: EXACT ở hai tầng —
          (a) trong nội bộ pattern: template đóng băng, adapt chỉ điền content
          slot nên không đổi được cấu trúc (safe-adaptable by construction);
          (b) giữa các ứng viên: mọi pattern đủ điều kiện phải CÙNG MỘT chữ ký
          cấu trúc — hai cấu trúc khác nhau cùng khớp = MƠ HỒ → từ chối reuse
          (compose mới), không để role subset thành cửa reuse chéo cấu trúc;
        - verified > validated > (candidate KHÔNG bao giờ);
        - ưu tiên: ứng viên khớp EXACT plan-roles trước, rồi status, usage_count.
        dsl_version lệch → đánh dấu deprecated (lazy), không reuse mù."""
        roles_str = ",".join(sorted(required_roles))
        with SessionLocal() as session:
            rows = session.query(SimulationPattern).filter_by(scene_mode=scene_mode).all()
            stale = [r for r in rows if r.dsl_version not in SUPPORTED_VERSIONS and r.status != "deprecated"]
            for r in stale:
                r.status = "deprecated"
            if stale:
                session.commit()
            usable = [
                r for r in rows
                if r.status in AUTO_REUSE_STATUSES
                and r.dsl_version in SUPPORTED_VERSIONS
                and required_roles <= covered_roles_of_template(json.loads(r.template_json))
            ]
            if not usable:
                return None
            # Tầng exact plan-roles trước; chỉ khi không có mới xét subset (chống nhiễu)
            exact = [r for r in usable if r.semantic_roles == roles_str]
            pool = exact if exact else usable
            # Điều kiện cấu trúc: pool phải đồng nhất MỘT chữ ký — khác nhau là mơ hồ
            if len({_structural_key(r) for r in pool}) > 1:
                return None
            pool.sort(key=lambda r: (AUTO_REUSE_STATUSES.index(r.status), -r.usage_count))
            session.expunge(pool[0])  # dùng ngoài session an toàn
            return pool[0]

    def bump_usage(self, pattern_key: str) -> None:
        with SessionLocal() as session:
            row = session.query(SimulationPattern).filter_by(pattern_key=pattern_key).first()
            if row is not None:
                row.usage_count += 1
                row.updated_at = _now()
                session.commit()

    def persist_from_spec(
        self, scene_mode: str, required_roles: set[str], spec: dict
    ) -> str | None:
        """Sau compose-new THÀNH CÔNG: extract template + SELF-CHECK round-trip
        qua đủ 4 cổng → lưu status="validated". Self-check chỉ chứng minh
        template round-trip được — KHÔNG auto lên "verified" (cần live
        benchmark/người duyệt). Trùng pattern_key → tăng usage, không nhân bản.
        Trả pattern_key nếu lưu/đụng, None nếu không đủ điều kiện."""
        template, schema, params = extract_template(spec)
        if len(schema) <= 1:
            # chỉ có slot "title" (luôn tồn tại) → không có nội dung tham số hóa
            # thật sự, không đủ tính tổng quát — chỉ cache exact, không lưu pattern
            return None
        rebuilt = instantiate(template, params)
        # notes là bình luận instance-specific (template đặt None) — không được
        # làm fail round-trip (bug live: spec có notes → pattern không bao giờ lưu)
        if rebuilt != {**spec, "notes": None}:
            return None  # round-trip lệch → không lưu template hỏng
        config, err = run_gates(scene_mode, required_roles, rebuilt)
        if config is None or err:
            return None
        signature = spec_signature(scene_mode, required_roles, spec)
        key = pattern_key_of(signature)
        # Pattern chứa bool op (op ĐÓNG BĂNG, không kiểm chứng bảng chân trị
        # được lúc live) → "candidate": KHÔNG auto-reuse — tránh mẫu AND bị
        # dùng cho đề OR; chờ verified qua benchmark/người duyệt.
        status = "candidate" if signature["rule_ops"] else "validated"
        with SessionLocal() as session:
            existing = session.query(SimulationPattern).filter_by(pattern_key=key).first()
            if existing is not None:
                existing.usage_count += 1
                existing.updated_at = _now()
                session.commit()
                return key
            session.add(
                SimulationPattern(
                    pattern_key=key,
                    name=f"{scene_mode}: {'+'.join(signature['object_types'])}",
                    signature_json=json.dumps(signature, ensure_ascii=False),
                    scene_mode=scene_mode,
                    semantic_roles=",".join(sorted(required_roles)),
                    template_json=json.dumps(template, ensure_ascii=False),
                    parameter_schema_json=json.dumps(schema, ensure_ascii=False),
                    dsl_version=DSL_VERSION,
                    policy_version=self.policy_version,
                    status=status,
                    usage_count=0,
                )
            )
            session.commit()
            return key
