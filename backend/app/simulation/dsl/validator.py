"""Validator SimulationSpec DSL v1 (M6) — chốt chặn server-side trước khi
generic engine chạy. Song song với validator TS ở frontend.

Không eval, không arbitrary code — mọi primitive có allowlist. LLM chỉ khai
báo semantics; engine tất định tạo state/timeline/render (§4, §5).
"""

from __future__ import annotations

from app.simulation.dsl import manifest as M
from app.validation.simulation import check_forbidden_keys

# Allowlist/limits DẪN XUẤT từ manifest (M7 §2) — không viết tay lại, chống drift
OBJECT_TYPES = M.object_types()
RULE_TYPES = M.rule_types()
BOOL_OPS = M.bool_ops()
INTERACTION_TYPES = M.interaction_types()
PROCESS_TYPES = M.process_types()
TOP_KEYS = M.top_keys()

MAX_OBJECTS = M.limit("max_objects")
MAX_RULES = M.limit("max_rules")
MAX_INTERACTIONS = M.limit("max_interactions")
MAX_PROCESSES = M.limit("max_processes")
MAX_PATH = M.limit("max_path")
MAX_REVEAL_STEPS = M.limit("max_reveal_steps")
MAX_TEXT_LEN = M.limit("max_text_len")
MAX_NESTING_DEPTH = M.limit("max_nesting_depth")

# M7.12: cấu trúc/nội dung — container/group chứa con qua "parent";
# heading/paragraph/text mang nội dung qua "text".
CONTAINER_TYPES = {"container", "group"}
TEXT_CONTENT_TYPES = {"heading", "paragraph", "text"}

# M7.13A: drag — allowlist target + constraints, dẫn xuất từ manifest
DRAG_TARGET_TYPES = M.drag_target_types()
DRAG_CONSTRAINT_KEYS = {"bounds", "axis", "snap"}
DRAG_BOUND_KEYS = {"min_x", "max_x", "min_y", "max_y"}
DRAG_AXES = {"x", "y"}


def _is_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _detect_cycle(rules: list[dict]) -> bool:
    targets = {r["target"] for r in rules}
    deps = {r["target"]: [i for i in r.get("inputs", []) if i in targets] for r in rules}
    state: dict[str, int] = {}

    def visit(n: str) -> bool:
        if state.get(n) == 1:
            return True
        if state.get(n) == 2:
            return False
        state[n] = 1
        for d in deps.get(n, []):
            if visit(d):
                return True
        state[n] = 2
        return False

    return any(visit(t) for t in targets)


def _validate_drag_constraints(raw) -> tuple[dict | None, str | None]:
    """Kiểm "constraints" của drag: bounds/axis/snap (M7.13A). Trả (chuẩn hóa, lỗi)."""
    if raw is None:
        return None, None
    if not isinstance(raw, dict):
        return None, 'drag "constraints" phải là đối tượng JSON.'
    for k in raw:
        if k not in DRAG_CONSTRAINT_KEYS:
            return None, f'Trường lạ trong drag constraints: "{k}" (chỉ nhận bounds/axis/snap).'
    out: dict = {}
    bounds = raw.get("bounds")
    if bounds is not None:
        if not isinstance(bounds, dict) or any(k not in DRAG_BOUND_KEYS for k in bounds):
            return None, f'drag "bounds" chỉ nhận các khóa {"/".join(sorted(DRAG_BOUND_KEYS))}.'
        norm: dict = {}
        for k in DRAG_BOUND_KEYS:
            v = bounds.get(k)
            if v is None:
                continue
            if not _is_num(v) or not (0 <= v <= 100):
                return None, f'drag bounds "{k}" phải là số trong 0–100.'
            norm[k] = v
        if norm.get("min_x", 0) > norm.get("max_x", 100) or norm.get("min_y", 0) > norm.get("max_y", 100):
            return None, "drag bounds có min lớn hơn max."
        if norm:
            out["bounds"] = norm
    axis = raw.get("axis")
    if axis is not None:
        if axis not in DRAG_AXES:
            return None, f'drag "axis" phải là {"/".join(sorted(DRAG_AXES))}.'
        out["axis"] = axis
    snap = raw.get("snap")
    if snap is not None:
        if not _is_num(snap) or snap <= 0:
            return None, 'drag "snap" phải là số dương.'
        out["snap"] = snap
    return (out or None), None


# Thuộc tính mỗi loại interaction/process ĐIỀU KHIỂN — dùng cho ownership rule
# (M7.13A): một thuộc tính biến đổi không được có HAI chủ (interaction + process)
# khi chưa có arbitration policy.
_INTERACTION_CONTROLS = {"drag": "position", "toggle": "value"}
_PROCESS_CONTROLS = {"move_along_path": ("position", "entity")}  # type → (property, trường target)


def ownership_conflict(interactions: list[dict], processes: list[dict]) -> str | None:
    """Trả thông báo lỗi nếu cùng (thuộc tính, object) bị cả interaction lẫn
    process điều khiển; None nếu sạch."""
    owned_by_process: set[tuple[str, str]] = set()
    for p in processes:
        control = _PROCESS_CONTROLS.get(p.get("type", ""))
        if control:
            prop, field = control
            target = p.get(field)
            if isinstance(target, str):
                owned_by_process.add((prop, target))
    for it in interactions:
        prop = _INTERACTION_CONTROLS.get(it.get("type", ""))
        if prop and (prop, it.get("target")) in owned_by_process:
            return (
                f'"{it["target"]}" đã được một process điều khiển ({prop}) — '
                f"không thể vừa {it['type']} vừa chạy process trên cùng thuộc tính."
            )
    return None


def _norm_text(s) -> str:
    return " ".join(s.split()).casefold() if isinstance(s, str) else ""


def compact_redundant_labels(raw_objects: list, raw: dict) -> list:
    """Gỡ object `label` RỜI mà nội dung TRÙNG HỆT nhãn của một node/edge đã có.

    Vì sao tồn tại (M8-PRE plan C): Gemini thỉnh thoảng vừa đặt `label` inline cho
    node/edge, VỪA tạo thêm một object `label` rời lặp lại đúng chuỗi đó (đo live:
    11 label rời cho 5 node + 6 edge) → cảnh vượt `max_objects` dù NGỮ NGHĨA chỉ có
    ~12 object. Đây là DƯ THỪA CHỨNG MINH ĐƯỢC, không phải nội dung.

    Luật (tất định, KHÔNG đoán):
    - Chỉ gỡ object type "label".
    - Chỉ khi chuỗi của nó TRÙNG HỆT (chuẩn hoá khoảng trắng + hoa/thường) với
      `label`/`text` của một node hoặc edge CÓ THẬT trong spec → renderer đã vẽ chữ
      đó rồi, gỡ đi không mất thông tin nào.
    - TUYỆT ĐỐI không gỡ nếu label đang được THAM CHIẾU về mặt cấu trúc/ngữ nghĩa
      (rule input/target, interaction target, process entity/path, parent của object
      khác) — gỡ sẽ làm hỏng tham chiếu.
    - KHÔNG đoán liên kết theo KHOẢNG CÁCH. KHÔNG dùng LLM. KHÔNG gỡ chữ có nghĩa.

    Tham chiếu trong `reveal_sequence.steps` KHÔNG phải tham chiếu cấu trúc: nó chỉ
    nói "bước này hé lộ thêm id X". Label bị gỡ sẽ được rút khỏi các step (và step
    rỗng bị bỏ) — nội dung vẫn hiện vì node/edge mang chính chuỗi đó cũng được hé lộ.
    """
    objs = [o for o in raw_objects if isinstance(o, dict)]
    if len(objs) != len(raw_objects):
        return raw_objects  # có phần tử lạ → để validator chính báo lỗi, không đụng

    inline: set[str] = set()
    for o in objs:
        if o.get("type") in ("node", "edge"):
            for key in ("label", "text"):
                t = _norm_text(o.get(key))
                if t:
                    inline.add(t)
    if not inline:
        return raw_objects

    hard_refs: set[str] = set()
    for r in raw.get("rules", []) or []:
        if isinstance(r, dict):
            hard_refs.update(i for i in (r.get("inputs") or []) if isinstance(i, str))
            if isinstance(r.get("target"), str):
                hard_refs.add(r["target"])
    for it in raw.get("interactions", []) or []:
        if isinstance(it, dict) and isinstance(it.get("target"), str):
            hard_refs.add(it["target"])
    for p in raw.get("processes", []) or []:
        if isinstance(p, dict):
            if isinstance(p.get("entity"), str):
                hard_refs.add(p["entity"])
            hard_refs.update(n for n in (p.get("path") or []) if isinstance(n, str))
    for o in objs:
        if isinstance(o.get("parent"), str):
            hard_refs.add(o["parent"])

    drop = {
        o["id"]
        for o in objs
        if o.get("type") == "label"
        and isinstance(o.get("id"), str)
        and o["id"] not in hard_refs
        and _norm_text(o.get("label")) in inline
    }
    if not drop:
        return raw_objects

    # Gỡ id đã bỏ khỏi các step reveal; step rỗng thì bỏ hẳn (giữ spec nhất quán).
    for p in raw.get("processes", []) or []:
        if not isinstance(p, dict) or p.get("type") != "reveal_sequence":
            continue
        steps = []
        for st in p.get("steps") or []:
            if not isinstance(st, dict):
                steps.append(st)
                continue
            kept = [i for i in (st.get("objects") or []) if i not in drop]
            if kept:
                steps.append({**st, "objects": kept})
        p["steps"] = steps
    raw["processes"] = [
        p
        for p in (raw.get("processes") or [])
        if not (isinstance(p, dict) and p.get("type") == "reveal_sequence" and not p.get("steps"))
    ]
    return [o for o in objs if o.get("id") not in drop]


def validate_generic_config(raw) -> tuple[dict | None, str | None]:
    """Trả (spec chuẩn hóa, None) hoặc (None, lỗi tiếng Việt cho LLM retry)."""
    if not isinstance(raw, dict):
        return None, "Spec không phải đối tượng JSON."

    forbidden = check_forbidden_keys(raw)
    if forbidden:
        return None, forbidden
    for k in raw:
        if k not in TOP_KEYS:
            return None, f'Trường lạ ở cấp cao nhất: "{k}".'
    # §9: version hóa — reject phiên bản DSL không hỗ trợ (không âm thầm default)
    ver = raw.get("dsl_version")
    if ver is not None and ver not in M.SUPPORTED_VERSIONS:
        return None, f'dsl_version "{ver}" không được hỗ trợ (chỉ nhận {", ".join(sorted(M.SUPPORTED_VERSIONS))}).'
    if not isinstance(raw.get("title"), str) or not raw["title"]:
        return None, '"title" phải là chuỗi.'

    raw_objects = raw.get("objects")
    if not isinstance(raw_objects, list) or len(raw_objects) < 1:
        return None, f'"objects" phải có 1–{MAX_OBJECTS} phần tử.'
    # M8-PRE (plan C): CHỈ khi vượt hạn mức mới thử nén phần dư thừa CHỨNG MINH ĐƯỢC.
    # Cảnh đang trong hạn mức KHÔNG bị đụng tới → 0 bề mặt regression.
    # Thứ tự: candidate → nén dư thừa an toàn → kiểm hạn mức → validator còn lại.
    if len(raw_objects) > MAX_OBJECTS:
        raw_objects = compact_redundant_labels(raw_objects, raw)
    if len(raw_objects) > MAX_OBJECTS:
        return None, f'"objects" phải có 1–{MAX_OBJECTS} phần tử.'
    ids: set[str] = set()
    objects: list[dict] = []
    by_id: dict[str, dict] = {}
    for o in raw_objects:
        if not isinstance(o, dict) or not isinstance(o.get("id"), str) or not o["id"]:
            return None, 'Mỗi object cần "id" chuỗi.'
        if o["id"] in ids:
            return None, f'Trùng object id "{o["id"]}".'
        if o.get("type") not in OBJECT_TYPES:
            return None, f'Object type không hợp lệ: "{o.get("type")}".'
        ids.add(o["id"])
        # M13 Task 2b: "weight" cấp OBJECT là silent semantic no-op — không engine
        # nào đọc nó (trọng số THẬT của weighted_sum luôn là "weights" TRÊN RULE).
        # Reject tường minh, KHÔNG strip im lặng — LLM phải biết mô hình của nó sai.
        if "weight" in o:
            return None, (
                f'Object "{o.get("id")}" khai "weight" — trường này không còn được hỗ trợ '
                f'(không engine nào đọc nó). Trọng số của weighted_sum khai bằng mảng '
                f'"weights" TRÊN RULE, vd {{"type": "weighted_sum", "inputs": [...], "weights": [8,4,2,1]}}.'
            )
        obj = {"id": o["id"], "type": o["type"]}
        for key in ("x", "y", "value"):
            if _is_num(o.get(key)):
                obj[key] = o[key]
        for key in ("label", "node_type", "from", "to", "text", "parent"):
            if isinstance(o.get(key), str):
                obj[key] = o[key]
        # M8-PRE (S2): edge có CHIỀU — chỉ giữ khi là bool THẬT (không nhận 0/1,
        # không nhận chuỗi) và chỉ trên edge; renderer vẽ mũi tên from → to.
        if o["type"] == "edge" and isinstance(o.get("directed"), bool):
            obj["directed"] = o["directed"]
        objects.append(obj)
        by_id[o["id"]] = obj
    for o in objects:
        if o["type"] == "edge":
            if o.get("from") not in ids or o.get("to") not in ids:
                return None, f'edge "{o["id"]}" phải nối hai object có thật (from/to).'

    # M8-PRE (S2): CHIỀU luồng dữ liệu là thứ DẪN XUẤT ĐƯỢC, không phải thứ phải
    # đi xin LLM. Đo live: model dựng đúng actor→process→data_store trong from/to
    # nhưng BỎ QUA `directed` kể cả khi prompt yêu cầu tường minh và kể cả sau khi
    # bị từ chối kèm lý do. Hướng đã nằm sẵn trong from/to → server TỰ SUY.
    # Chỉ áp cho cạnh nối HAI node vai trò HỆ THỐNG → không đụng hình học
    # (node không node_type) và không đụng liên kết mạng (client/router… vốn 2 chiều).
    _sys_types = set(M.node_type_vocabulary()["system"])
    _sys_nodes = {o["id"] for o in objects if o["type"] == "node" and o.get("node_type") in _sys_types}
    for o in objects:
        if (
            o["type"] == "edge"
            and "directed" not in o  # LLM khai tường minh thì TÔN TRỌNG, không ghi đè
            and o.get("from") in _sys_nodes
            and o.get("to") in _sys_nodes
        ):
            o["directed"] = True

    # M7.12: nội dung chữ + lồng nhau (structural/textual)
    for o in objects:
        if o["type"] in TEXT_CONTENT_TYPES:
            txt = o.get("text")
            if not isinstance(txt, str) or not txt.strip():
                return None, f'{o["type"]} "{o["id"]}" cần "text" (nội dung) không rỗng.'
            if len(txt) > MAX_TEXT_LEN:
                return None, f'"text" của "{o["id"]}" quá dài (tối đa {MAX_TEXT_LEN} ký tự).'
        parent = o.get("parent")
        if parent is not None:
            if parent not in by_id or by_id[parent]["type"] not in CONTAINER_TYPES:
                return None, f'"{o["id"]}" có "parent" phải là id của container/group hợp lệ.'
    # chu trình chứa + độ sâu lồng nhau
    for o in objects:
        depth, cur, seen = 0, o["id"], {o["id"]}
        while by_id[cur].get("parent") is not None:
            cur = by_id[cur]["parent"]
            depth += 1
            if cur in seen:
                return None, f'Chuỗi "parent" của "{o["id"]}" tạo chu trình chứa.'
            seen.add(cur)
            if depth > MAX_NESTING_DEPTH:
                return None, f'Lồng nhau vượt độ sâu tối đa {MAX_NESTING_DEPTH}.'

    raw_rules = raw.get("rules") if isinstance(raw.get("rules"), list) else []
    if len(raw_rules) > MAX_RULES:
        return None, f"Tối đa {MAX_RULES} rule."
    rules: list[dict] = []
    for r in raw_rules:
        if not isinstance(r, dict) or r.get("type") not in RULE_TYPES:
            return None, "Rule type không hợp lệ."
        if r.get("target") not in ids:
            return None, "Rule tham chiếu target không tồn tại."
        inputs = r.get("inputs") if isinstance(r.get("inputs"), list) else []
        for inp in inputs:
            if inp not in ids:
                return None, f'Rule tham chiếu input không tồn tại: "{inp}".'
        rule = {"type": r["type"], "target": r["target"], "inputs": list(inputs)}
        if r["type"] == "boolean":
            if r.get("op") not in BOOL_OPS:
                return None, f'boolean rule cần "op" thuộc {"/".join(sorted(BOOL_OPS))}.'
            rule["op"] = r["op"]
        else:
            weights = r.get("weights") if isinstance(r.get("weights"), list) else []
            if len(weights) != len(inputs) or not all(_is_num(w) for w in weights):
                return None, 'weighted_sum cần "weights" cùng độ dài với "inputs".'
            rule["weights"] = list(weights)
        rules.append(rule)
    # M11: mỗi giá trị dẫn xuất đúng MỘT rule sở hữu — hai rule cùng target thì
    # rule sau thắng mỗi vòng quét điểm bất động → kết quả phụ thuộc thứ tự khai
    # báo trong mảng (ngữ nghĩa nhập nhằng), phải chặn trước khi engine chạy.
    seen_targets: set[str] = set()
    for r in rules:
        if r["target"] in seen_targets:
            return None, (
                f'Hai rule cùng ghi vào target "{r["target"]}" — mỗi giá trị dẫn xuất '
                "chỉ được đúng MỘT rule sở hữu. Hãy gộp điều kiện vào một rule hoặc "
                "dùng thêm một object trung gian làm target riêng."
            )
        seen_targets.add(r["target"])
    if _detect_cycle(rules):
        return None, "Rule có phụ thuộc vòng (circular dependency)."

    # ── M13 §3.2 + blocker 3: operand coherence VỚI role-typing ──
    # INVALID_SOURCE: type không phải provider của role rule cần, hoặc provider
    #   nhưng không khai value; HOẶC derived target có output_role KHÔNG khớp
    #   input_role của rule tiêu thụ (coercion DENY mặc định — role_coercions rỗng).
    # UNRESOLVED_DERIVED_SOURCE (hợp lệ ở tầng validate): input là target của rule
    #   khác VÀ output_role khớp — thứ tự khai báo tự do, runtime defer theo bound.
    target_output_role = {r["target"]: M.RULE_IO_ROLES[r["type"]]["output_role"] for r in rules}
    coercions = {(c["from"], c["to"]) for c in M.dsl_semantic_contract()["role_coercions"]}
    for r in rules:
        # Ràng buộc 2: target object phải CHẤP NHẬN output role của rule —
        # weighted_sum (numeric) không được ghi vào node/edge (relational).
        out_role = M.RULE_IO_ROLES[r["type"]]["output_role"]
        target_obj = by_id[r["target"]]
        if out_role not in M.PRIMITIVE_ROLES.get(target_obj["type"], set()):
            return None, (
                f'Rule {r["type"]} sinh giá trị vai trò "{out_role}" nhưng target '
                f'"{r["target"]}" ({target_obj["type"]}) không nhận được vai trò đó — '
                f'dùng object type có vai trò {out_role} làm target (vd value_box/lamp).'
            )
        need = M.RULE_IO_ROLES[r["type"]]["input_role"]
        providers = M.value_provider_types(need)
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
            o = by_id[inp]
            if o["type"] not in providers or "value" not in o:
                return None, (
                    f'Rule "{r["target"]}" dùng input "{inp}" ({o["type"]}) '
                    f'không có nguồn giá trị {need} theo hợp đồng DSL — '
                    f'chỉ chấp nhận: {", ".join(sorted(providers))} có "value", '
                    f'hoặc target của một rule cùng vai trò. Đừng dùng node/edge làm toán hạng.'
                )

    rule_targets = {r["target"] for r in rules}
    raw_inter = raw.get("interactions") if isinstance(raw.get("interactions"), list) else []
    if len(raw_inter) > MAX_INTERACTIONS:
        return None, f"Tối đa {MAX_INTERACTIONS} interaction."
    interactions: list[dict] = []
    for it in raw_inter:
        if not isinstance(it, dict) or it.get("type") not in INTERACTION_TYPES:
            return None, "Interaction type không hợp lệ."
        if it.get("target") not in ids:
            return None, "Interaction tham chiếu target không tồn tại."
        inter = {"type": it["type"], "target": it["target"]}
        if isinstance(it.get("label"), str):
            inter["label"] = it["label"]

        if it["type"] == "toggle":
            if it["target"] in rule_targets:
                return None, f'Không thể toggle "{it["target"]}" vì nó là giá trị dẫn xuất từ rule.'
            # M7.13A: toggle chỉ có nghĩa trên object CÓ value (0/1) — toggle một
            # node/điểm là interaction chết; muốn di chuyển điểm phải dùng drag.
            if "value" not in by_id[it["target"]]:
                return None, (
                    f'toggle "{it["target"]}" vô nghĩa vì object không có "value" khởi tạo — '
                    "muốn học sinh DI CHUYỂN/KÉO điểm thì dùng interaction drag."
                )
        else:  # drag (M7.13A)
            target_type = by_id[it["target"]]["type"]
            if target_type not in DRAG_TARGET_TYPES:
                return None, (
                    f'drag chỉ áp cho object type {"/".join(sorted(DRAG_TARGET_TYPES))} — '
                    f'"{it["target"]}" là {target_type}.'
                )
            constraints, c_err = _validate_drag_constraints(it.get("constraints"))
            if c_err:
                return None, c_err
            if constraints is not None:
                inter["constraints"] = constraints
        interactions.append(inter)

    raw_proc = raw.get("processes") if isinstance(raw.get("processes"), list) else []
    if len(raw_proc) > MAX_PROCESSES:
        return None, f"Tối đa {MAX_PROCESSES} process."
    processes: list[dict] = []
    for p in raw_proc:
        if not isinstance(p, dict) or p.get("type") not in PROCESS_TYPES:
            return None, "Process type không hợp lệ."

        if p["type"] == "reveal_sequence":
            steps = p.get("steps")
            if not isinstance(steps, list) or not (1 <= len(steps) <= MAX_REVEAL_STEPS):
                return None, f'reveal_sequence "steps" phải có 1–{MAX_REVEAL_STEPS} bước.'
            norm_steps: list[dict] = []
            for st in steps:
                objs = st.get("objects") if isinstance(st, dict) else None
                if not isinstance(objs, list) or len(objs) < 1:
                    return None, 'Mỗi reveal step cần "objects" không rỗng.'
                for oid in objs:
                    if oid not in ids:
                        return None, f'reveal step tham chiếu object không tồn tại: "{oid}".'
                for k in st:
                    if k not in ("objects", "narration"):
                        return None, f'Trường lạ trong reveal step: "{k}".'
                step = {"objects": list(objs)}
                if isinstance(st.get("narration"), str):
                    step["narration"] = st["narration"]
                norm_steps.append(step)
            processes.append({"type": "reveal_sequence", "steps": norm_steps})
            continue

        # move_along_path
        if by_id.get(p.get("entity", ""), {}).get("type") != "moving_entity":
            return None, 'Process cần "entity" là một moving_entity có thật.'
        path = p.get("path")
        if not isinstance(path, list) or not (2 <= len(path) <= MAX_PATH):
            return None, f'Process "path" phải có 2–{MAX_PATH} nút.'
        for nid in path:
            if by_id.get(nid, {}).get("type") != "node":
                return None, 'Process "path" phải toàn id của object type node.'
        processes.append({"type": "move_along_path", "entity": p["entity"], "path": list(path)})

    # M7.13A: ownership rule — một thuộc tính không có hai chủ điều khiển
    own_err = ownership_conflict(interactions, processes)
    if own_err:
        return None, own_err

    return {
        "dsl_version": raw["dsl_version"] if isinstance(raw.get("dsl_version"), str) and raw.get("dsl_version") else "1.0",
        "title": raw["title"],
        "objects": objects,
        "rules": rules,
        "interactions": interactions,
        "processes": processes,
        "notes": raw["notes"] if isinstance(raw.get("notes"), str) and raw.get("notes") else None,
    }, None
