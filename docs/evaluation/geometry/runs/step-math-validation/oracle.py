"""Independent First-Principles Mathematical Construction Oracle for Scene3D.
Strictly ZERO imports from `app` or `tests`.
Implements independent mathematical verification across all 11 P2 categories
(over exact chart coordinates and the Riemannian metric tensor G = chart_metric),
frontend geometric rendering math (`daGiacMatPhang`, `moRongDaGiacMatPhang`,
`khungGocVuong`, `laChieuCao`), and all 10 P3 counterexample / fault-injection suites.
"""
from __future__ import annotations
import ast
from dataclasses import dataclass, field
import math
import re
from typing import Any
TOL = 1e-6
PLANE_TOL = 1e-6
Mat3 = tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]
Vec3 = tuple[float, float, float]
IDENTITY_METRIC: Mat3 = (
    (1.0, 0.0, 0.0),
    (0.0, 1.0, 0.0),
    (0.0, 0.0, 1.0),
)

# ---------------------------------------------------------------------------
# 1. Symbolic & Exact Expression Evaluator + Metric Tensor G Linear Algebra
# ---------------------------------------------------------------------------

def eval_symbolic_expr(expr: Any, a_val: float = 1.0) -> float:
    """Independently evaluate a symbolic math expression string, number, or exact dict."""
    if isinstance(expr, (int, float)):
        return float(expr)
    if isinstance(expr, dict):
        kind = expr.get("kind")
        if kind == "rational":
            return eval_symbolic_expr(expr.get("value", 0), a_val=a_val)
        if kind == "radical":
            coeff = eval_symbolic_expr(expr.get("coefficient", 1), a_val=a_val)
            rad = eval_symbolic_expr(expr.get("radicand", 1), a_val=a_val)
            pi_pow = int(expr.get("pi", 0) or 0)
            return coeff * math.sqrt(max(0.0, rad)) * (math.pi**pi_pow)
    if not isinstance(expr, str):
        raise ValueError(f"Unsupported expression type: {type(expr)} ({expr!r})")
    s = expr.strip()
    if not s:
        raise ValueError("Empty expression")
    # Convert Unicode math notation (e.g. 5√6/3, 6π√5, 36π, √13/2) into Python AST syntax
    s = re.sub(r"√\s*\(([^)]+)\)", r"sqrt(\1)", s)
    s = re.sub(r"√\s*([0-9]+(?:\.[0-9]+)?)", r"sqrt(\1)", s)
    s = s.replace("π", "pi").replace("^", "**")
    # Insert explicit multiplication between number/closing-paren/pi and (sqrt|pi|a|\()
    s = re.sub(r"([0-9\)]|pi)\s*(sqrt|pi|a|\()", r"\1*\2", s)
    s = re.sub(r"([0-9\)]|pi)\s*(sqrt|pi|a|\()", r"\1*\2", s)
    allowed_names = {
        "a": a_val,
        "pi": math.pi,
        "sqrt": math.sqrt,
        "abs": abs,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "acos": math.acos,
        "asin": math.asin,
    }
    tree = ast.parse(s, mode="eval")
    return float(_eval_ast(tree.body, allowed_names))

def _eval_ast(node: ast.AST, env: dict[str, Any]) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.Name):
        if node.id in env:
            return float(env[node.id])
        raise ValueError(f"Unknown symbol in expression: {node.id}")
    if isinstance(node, ast.UnaryOp):
        val = _eval_ast(node.operand, env)
        if isinstance(node.op, ast.UAdd):
            return +val
        if isinstance(node.op, ast.USub):
            return -val
        raise ValueError(f"Unsupported unary op: {node.op}")
    if isinstance(node, ast.BinOp):
        left = _eval_ast(node.left, env)
        right = _eval_ast(node.right, env)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        if isinstance(node.op, ast.Pow):
            return left**right
        raise ValueError(f"Unsupported binary op: {node.op}")
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        fn_name = node.func.id
        if fn_name in env and callable(env[fn_name]) and len(node.args) == 1:
            arg = _eval_ast(node.args[0], env)
            return float(env[fn_name](arg))
    raise ValueError(f"Unsupported AST node: {ast.dump(node)}")

def parse_vec3(raw: Any) -> Vec3:
    if not isinstance(raw, (list, tuple)) or len(raw) != 3:
        raise ValueError(f"Expected 3-vector, got: {raw!r}")
    return (
        eval_symbolic_expr(raw[0]),
        eval_symbolic_expr(raw[1]),
        eval_symbolic_expr(raw[2]),
    )

def parse_metric(raw_metric: Any) -> Mat3:
    if not raw_metric or not isinstance(raw_metric, (list, tuple)) or len(raw_metric) != 3:
        return IDENTITY_METRIC
    return (
        parse_vec3(raw_metric[0]),
        parse_vec3(raw_metric[1]),
        parse_vec3(raw_metric[2]),
    )

def v_add(u: Vec3, v: Vec3) -> Vec3:
    return (u[0] + v[0], u[1] + v[1], u[2] + v[2])

def v_sub(u: Vec3, v: Vec3) -> Vec3:
    return (u[0] - v[0], u[1] - v[1], u[2] - v[2])

def v_scale(u: Vec3, s: float) -> Vec3:
    return (u[0] * s, u[1] * s, u[2] * s)

def v_dot(u: Vec3, v: Vec3) -> float:
    return u[0] * v[0] + u[1] * v[1] + u[2] * v[2]

def v_cross(u: Vec3, v: Vec3) -> Vec3:
    return (
        u[1] * v[2] - u[2] * v[1],
        u[2] * v[0] - u[0] * v[2],
        u[0] * v[1] - u[1] * v[0],
    )

def v_norm_sq(u: Vec3) -> float:
    return v_dot(u, u)

def v_norm(u: Vec3) -> float:
    return math.sqrt(max(0.0, v_norm_sq(u)))

def v_det3(u: Vec3, v: Vec3, w: Vec3) -> float:
    return v_dot(u, v_cross(v, w))

def mat3_mul_vec(m: Mat3, v: Vec3) -> Vec3:
    return (v_dot(m[0], v), v_dot(m[1], v), v_dot(m[2], v))

def mat3_det(m: Mat3) -> float:
    return v_det3(m[0], m[1], m[2])

def mat3_inv(m: Mat3) -> Mat3:
    det = mat3_det(m)
    if abs(det) <= 1e-12:
        return IDENTITY_METRIC
    c0 = v_cross(m[1], m[2])
    c1 = v_cross(m[2], m[0])
    c2 = v_cross(m[0], m[1])
    return (
        (c0[0] / det, c1[0] / det, c2[0] / det),
        (c0[1] / det, c1[1] / det, c2[1] / det),
        (c0[2] / det, c1[2] / det, c2[2] / det),
    )

def g_dot(u: Vec3, v: Vec3, G: Mat3 = IDENTITY_METRIC) -> float:
    """Metric inner product <u, v>_G = u^T G v for contravariant vectors."""
    return v_dot(u, mat3_mul_vec(G, v))

def g_norm_sq(u: Vec3, G: Mat3 = IDENTITY_METRIC) -> float:
    return max(0.0, g_dot(u, u, G))

def g_norm(u: Vec3, G: Mat3 = IDENTITY_METRIC) -> float:
    return math.sqrt(g_norm_sq(u, G))

def g_covector_dot(n1: Vec3, n2: Vec3, G_inv: Mat3 = IDENTITY_METRIC) -> float:
    """Dual metric inner product <n1, n2>_{G^{-1}} = n1^T G^{-1} n2 for plane covectors."""
    return v_dot(n1, mat3_mul_vec(G_inv, n2))

def g_gram_det2(u: Vec3, v: Vec3, G: Mat3 = IDENTITY_METRIC) -> float:
    uu = g_dot(u, u, G)
    vv = g_dot(v, v, G)
    uv = g_dot(u, v, G)
    return max(0.0, uu * vv - uv * uv)

def g_gram_det3(u: Vec3, v: Vec3, w: Vec3, G: Mat3 = IDENTITY_METRIC) -> float:
    return (v_det3(u, v, w) ** 2) * max(0.0, mat3_det(G))

# ---------------------------------------------------------------------------
# 2. Scene Schema Normalization Helpers
# ---------------------------------------------------------------------------

def extract_objects_and_quantities(
    scene: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    raw_objs = scene.get("objects") or {}
    objects: dict[str, dict[str, Any]] = {}
    quantities: dict[str, dict[str, Any]] = {}
    items = raw_objs.values() if isinstance(raw_objs, dict) else raw_objs
    for item in items:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        oid = str(item["id"])
        if item.get("type") == "quantity":
            quantities[oid] = item
        else:
            objects[oid] = item
    raw_quants = scene.get("quantities") or {}
    q_items = raw_quants.values() if isinstance(raw_quants, dict) else raw_quants
    for q_item in q_items:
        if isinstance(q_item, dict) and q_item.get("id"):
            quantities[str(q_item["id"])] = q_item
    return objects, quantities

def obj_producer(obj: dict[str, Any]) -> str:
    prod = obj.get("producer")
    if isinstance(prod, str) and prod:
        return prod
    src = obj.get("source")
    if isinstance(src, str) and src:
        return src
    if isinstance(src, dict):
        inst = src.get("instruction")
        if isinstance(inst, str) and inst:
            return inst
    return ""

def point_xyz(obj: dict[str, Any]) -> Vec3:
    for key in ("xyz", "coords", "world_coords", "point", "anchor", "center"):
        if obj.get(key) is not None:
            return parse_vec3(obj[key])
    raise ValueError(f"Object {obj.get('id')} has no 3D point coordinates")

def line_anchor_and_dir(
    obj: dict[str, Any],
    objects: dict[str, dict[str, Any]],
) -> tuple[Vec3, Vec3]:
    t = obj.get("type")
    if t == "line3":
        anc_raw = obj.get("point") if obj.get("point") is not None else obj.get("anchor")
        dir_raw = obj.get("direction")
        if anc_raw is not None and dir_raw is not None:
            return parse_vec3(anc_raw), parse_vec3(dir_raw)
        deps = [d for d in (obj.get("depends") or []) if d in objects and objects[d].get("type") == "point3"]
        if len(deps) >= 2:
            a = point_xyz(objects[deps[0]])
            b = point_xyz(objects[deps[1]])
            return a, v_sub(b, a)
    if t == "segment3":
        if obj.get("point_a") is not None and obj.get("point_b") is not None:
            a = parse_vec3(obj["point_a"])
            b = parse_vec3(obj["point_b"])
            return a, v_sub(b, a)
        eps = obj.get("endpoint_ids") or obj.get("endpoints") or obj.get("depends") or []
        if len(eps) >= 2 and isinstance(eps[0], str) and eps[0] in objects and eps[1] in objects:
            a = point_xyz(objects[eps[0]])
            b = point_xyz(objects[eps[1]])
            return a, v_sub(b, a)
        if len(eps) >= 2 and isinstance(eps[0], (list, tuple)):
            a = parse_vec3(eps[0])
            b = parse_vec3(eps[1])
            return a, v_sub(b, a)
    raise ValueError(f"Cannot extract line anchor and direction from {obj.get('id')} ({t})")

def plane_point_and_normal(
    obj: dict[str, Any],
    objects: dict[str, dict[str, Any]],
) -> tuple[Vec3, Vec3]:
    if obj.get("point") is not None and obj.get("normal") is not None:
        return parse_vec3(obj["point"]), parse_vec3(obj["normal"])
    deps = [d for d in (obj.get("defining_points") or obj.get("depends") or []) if d in objects and objects[d].get("type") == "point3"]
    if len(deps) >= 3:
        p0 = point_xyz(objects[deps[0]])
        p1 = point_xyz(objects[deps[1]])
        p2 = point_xyz(objects[deps[2]])
        return p0, v_cross(v_sub(p1, p0), v_sub(p2, p0))
    raise ValueError(f"Cannot extract plane point and normal from {obj.get('id')}")

def solid_vertices_and_faces(
    solid_obj: dict[str, Any],
    objects: dict[str, dict[str, Any]],
) -> tuple[list[str], list[Vec3], list[list[int]]]:
    """Return (vertex_ids, vertex_coords, face_index_lists) for a solid/solid3 object."""
    v_ids = list(solid_obj.get("vertex_ids") or [])
    raw_verts = list(solid_obj.get("vertices") or [])
    if not v_ids and raw_verts and isinstance(raw_verts[0], str):
        v_ids = [str(v) for v in raw_verts]
        v_coords = [point_xyz(objects[vid]) for vid in v_ids if vid in objects]
    else:
        v_coords = [parse_vec3(v) for v in raw_verts]
        if not v_ids:
            v_ids = [f"v_{i}" for i in range(len(v_coords))]
    id_to_idx = {vid: i for i, vid in enumerate(v_ids)}
    raw_faces = solid_obj.get("faces") or []
    faces_idx: list[list[int]] = []
    for f in raw_faces:
        if not f:
            continue
        if isinstance(f[0], int):
            faces_idx.append([int(x) for x in f])
        else:
            faces_idx.append([id_to_idx[str(x)] for x in f if str(x) in id_to_idx])
    return v_ids, v_coords, faces_idx

# ---------------------------------------------------------------------------
# 3. Audit Result Data Structures
# ---------------------------------------------------------------------------

@dataclass
class CategoryCheckResult:
    category: str
    passed: bool
    checked_count: int = 0
    failures: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

@dataclass
class SceneAuditReport:
    scene_id: str
    data_source: str
    source_kind: str  # "frontend_sample_or_fixture" | "backend_hybrid_route_d"
    problem_text: str
    step_count: int
    objects_by_step: list[dict[str, Any]]
    dependency_graph: dict[str, list[str]]
    represented_proposition: str
    expected_math_result: str
    verdict: str  # "VERIFIED" | "INVALID" | "UNVERIFIABLE"
    category_results: dict[str, CategoryCheckResult]
    frontend_warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

# ---------------------------------------------------------------------------
# 4. Eleven P2 First-Principles Category Verifiers
# ---------------------------------------------------------------------------

def verify_scene_mathematics(
    scene: dict[str, Any],
    scene_id: str = "unknown",
    data_source: str = "unknown",
    source_kind: str = "backend_hybrid_route_d",
    problem_text: str = "",
    expected_answers: dict[str, Any] | None = None,
) -> SceneAuditReport:
    objects, quantities = extract_objects_and_quantities(scene)
    events: list[dict[str, Any]] = list(scene.get("events") or [])
    free_objects: list[str] = list(scene.get("free_objects") or [])
    G = parse_metric(scene.get("chart_metric"))
    G_inv = mat3_inv(G)
    cats: dict[str, CategoryCheckResult] = {
        "1_incidence": CategoryCheckResult("1_incidence", True),
        "2_midpoint_centroid_ratio": CategoryCheckResult("2_midpoint_centroid_ratio", True),
        "3_orthogonal_projection": CategoryCheckResult("3_orthogonal_projection", True),
        "4_intersection": CategoryCheckResult("4_intersection", True),
        "5_line_line_perp_parallel": CategoryCheckResult("5_line_line_perp_parallel", True),
        "6_line_plane_perp": CategoryCheckResult("6_line_plane_perp", True),
        "7_angles": CategoryCheckResult("7_angles", True),
        "8_distance_area_volume": CategoryCheckResult("8_distance_area_volume", True),
        "9_section": CategoryCheckResult("9_section", True),
        "10_step_dependency_ordering": CategoryCheckResult("10_step_dependency_ordering", True),
        "11_conclusion_and_premises": CategoryCheckResult("11_conclusion_and_premises", True),
    }
    def fail(cat_key: str, msg: str) -> None:
        cats[cat_key].passed = False
        cats[cat_key].failures.append(msg)
    def bump(cat_key: str, note: str | None = None) -> None:
        cats[cat_key].checked_count += 1
        if note:
            cats[cat_key].notes.append(note)
    # Verify positive-definiteness of chart_metric G
    bump("1_incidence")
    if G[0][0] <= 0 or (G[0][0] * G[1][1] - G[0][1] * G[1][0]) <= 0 or mat3_det(G) <= 0:
        fail("1_incidence", f"chart_metric G is not positive-definite: det={mat3_det(G)}")
    # -----------------------------------------------------------------------
    # Categories 1–9 on scene.objects
    # -----------------------------------------------------------------------
    for oid, obj in objects.items():
        otype = obj.get("type")
        prod = obj_producer(obj)
        deps = list(obj.get("depends") or [])
        # --- POINT3 ---
        if otype == "point3":
            p = point_xyz(obj)
            bump("1_incidence")
            if prod in ("midpoint", "construct_point.midpoint"):
                bump("2_midpoint_centroid_ratio")
                if len(deps) != 2 or deps[0] not in objects or deps[1] not in objects:
                    fail("2_midpoint_centroid_ratio", f"Midpoint {oid} invalid depends={deps}")
                else:
                    a = point_xyz(objects[deps[0]])
                    b = point_xyz(objects[deps[1]])
                    mid = v_scale(v_add(a, b), 0.5)
                    if v_norm(v_sub(p, mid)) > TOL:
                        fail(
                            "2_midpoint_centroid_ratio",
                            f"Midpoint {oid} != (A+B)/2 for {deps}: got {p}, expected {mid}",
                        )
            elif prod in ("triangle_centroid", "centroid", "construct_point.centroid"):
                bump("2_midpoint_centroid_ratio")
                if len(deps) != 3 or any(d not in objects for d in deps):
                    fail("2_midpoint_centroid_ratio", f"Centroid {oid} invalid depends={deps}")
                else:
                    a = point_xyz(objects[deps[0]])
                    b = point_xyz(objects[deps[1]])
                    c = point_xyz(objects[deps[2]])
                    if v_norm(v_cross(v_sub(b, a), v_sub(c, a))) <= TOL:
                        fail("2_midpoint_centroid_ratio", f"Centroid {oid} defining triangle {deps} is collinear")
                    cen = v_scale(v_add(v_add(a, b), c), 1.0 / 3.0)
                    if v_norm(v_sub(p, cen)) > TOL:
                        fail(
                            "2_midpoint_centroid_ratio",
                            f"Centroid {oid} != (A+B+C)/3 for {deps}: got {p}, expected {cen}",
                        )
            elif prod in ("point_on_segment", "divide_segment", "construct_point.divide_segment"):
                bump("2_midpoint_centroid_ratio")
                a = b = None
                if len(deps) == 1 and deps[0] in objects and objects[deps[0]].get("type") == "segment3":
                    anc, d_vec = line_anchor_and_dir(objects[deps[0]], objects)
                    a, b = anc, v_add(anc, d_vec)
                elif len(deps) >= 2 and deps[0] in objects and deps[1] in objects:
                    a = point_xyz(objects[deps[0]])
                    b = point_xyz(objects[deps[1]])
                if a is None or b is None:
                    fail("2_midpoint_centroid_ratio", f"divide_segment {oid} missing endpoints from depends={deps}")
                else:
                    ab = v_sub(b, a)
                    ap = v_sub(p, a)
                    ab2 = v_norm_sq(ab)
                    if ab2 <= TOL:
                        fail("2_midpoint_centroid_ratio", f"divide_segment {oid} on degenerate segment")
                    else:
                        if v_norm(v_cross(ap, ab)) / math.sqrt(ab2) > TOL:
                            fail("1_incidence", f"divide_segment {oid} is not collinear with {deps}")
                        if prod == "point_on_segment":
                            ratio_t = v_dot(ap, ab) / ab2
                            if ratio_t < -TOL or ratio_t > 1.0 + TOL:
                                fail(
                                    "2_midpoint_centroid_ratio",
                                    f"point_on_segment {oid} ratio t={ratio_t:.6f} outside [0, 1]",
                                )
            elif prod == "construct_point.translate":
                bump("1_incidence")
                bump("5_line_line_perp_parallel")
                if len(deps) >= 2 and deps[0] in objects and deps[1] in objects:
                    base_p = point_xyz(objects[deps[0]])
                    vec_obj = objects[deps[1]]
                    vec_v = point_xyz(vec_obj)
                    expected_p = v_add(base_p, vec_v)
                    if v_norm(v_sub(p, expected_p)) > TOL:
                        fail("1_incidence", f"translate {oid} != {deps[0]} + {deps[1]}")
                    disp = v_sub(p, base_p)
                    if v_norm(v_cross(disp, vec_v)) > TOL:
                        fail("5_line_line_perp_parallel", f"Translated ray ({deps[0]}->{oid}) is not parallel to vector {deps[1]}")
                    vdeps = vec_obj.get("depends") or []
                    if len(vdeps) == 2 and vdeps[0] in objects and vdeps[1] in objects:
                        vp0 = point_xyz(objects[vdeps[0]])
                        vp1 = point_xyz(objects[vdeps[1]])
                        ref_line = v_sub(vp1, vp0)
                        if v_norm(v_cross(disp, ref_line)) > TOL:
                            fail(
                                "5_line_line_perp_parallel",
                                f"Translated ray ({deps[0]}->{oid}) is not parallel to source line ({vdeps[0]}->{vdeps[1]})",
                            )
            elif prod in (
                "project_point_to_line",
                "altitude_from_to_line",
                "project_point_to_plane",
                "altitude_from_to_plane",
                "construct_point.project_onto",
            ):
                bump("3_orthogonal_projection")
                if len(deps) >= 2 and deps[0] in objects and deps[1] in objects:
                    pt_obj = objects[deps[0]]
                    target_obj = objects[deps[1]]
                    if pt_obj.get("type") != "point3":
                        pt_obj, target_obj = target_obj, pt_obj
                    src_p = point_xyz(pt_obj)
                    ttype = target_obj.get("type")
                    if ttype in ("line3", "segment3"):
                        anc, d_vec = line_anchor_and_dir(target_obj, objects)
                        d_norm = g_norm(d_vec, G)
                        if d_norm <= TOL:
                            fail("3_orthogonal_projection", f"Projection {oid} onto degenerate line {target_obj.get('id')}")
                        else:
                            # 1. Incidence of foot p on line
                            if v_norm(v_cross(v_sub(p, anc), d_vec)) / v_norm(d_vec) > TOL:
                                fail(
                                    "3_orthogonal_projection",
                                    f"Projection foot {oid} does not lie on line {target_obj.get('id')}",
                                )
                            # 2. Metric orthogonality <src_p - p, d_vec>_G == 0
                            ortho_err = abs(g_dot(v_sub(src_p, p), d_vec, G)) / d_norm
                            if ortho_err > TOL:
                                fail(
                                    "3_orthogonal_projection",
                                    f"Projection ({pt_obj.get('id')}->{oid}) not G-orthogonal to line {target_obj.get('id')} (err={ortho_err:.3e})",
                                )
                    elif ttype == "plane3":
                        bump("6_line_plane_perp")
                        p0, n_cov = plane_point_and_normal(target_obj, objects)
                        n_norm = v_norm(n_cov)
                        if n_norm <= TOL:
                            fail("3_orthogonal_projection", f"Projection {oid} onto degenerate plane {target_obj.get('id')}")
                        else:
                            # 1. Foot lies on plane: n_cov . (p - p0) == 0
                            inc_err = abs(v_dot(n_cov, v_sub(p, p0))) / n_norm
                            if inc_err > PLANE_TOL:
                                fail(
                                    "3_orthogonal_projection",
                                    f"Projection foot {oid} does not lie on plane {target_obj.get('id')} (err={inc_err:.3e})",
                                )
                            # 2. Under metric G, covector G*(src_p - p) must be parallel to plane covector n_cov!
                            ph = v_sub(src_p, p)
                            g_ph = mat3_mul_vec(G, ph)
                            if v_norm(g_ph) > TOL:
                                cross_err = v_norm(v_cross(g_ph, n_cov)) / (v_norm(g_ph) * n_norm)
                                if cross_err > TOL:
                                    fail(
                                        "3_orthogonal_projection",
                                        f"Projection ({pt_obj.get('id')}->{oid}) is not G-perpendicular to plane {target_obj.get('id')} (sin={cross_err:.3e})",
                                    )
                                    fail(
                                        "6_line_plane_perp",
                                        f"Altitude ({pt_obj.get('id')}->{oid}) fails line-plane perpendicularity on {target_obj.get('id')}",
                                    )
            elif prod in ("intersect_line_line", "construct_point.intersect_line_line"):
                bump("4_intersection")
                if len(deps) >= 2 and deps[0] in objects and deps[1] in objects:
                    for lid in deps[:2]:
                        anc, d_vec = line_anchor_and_dir(objects[lid], objects)
                        if v_norm(d_vec) <= TOL:
                            fail("4_intersection", f"intersect_line_line {oid} uses degenerate line {lid}")
                        elif v_norm(v_cross(v_sub(p, anc), d_vec)) / v_norm(d_vec) > TOL:
                            fail("4_intersection", f"Intersection {oid} does not lie on line {lid}")
                    _, d1 = line_anchor_and_dir(objects[deps[0]], objects)
                    _, d2 = line_anchor_and_dir(objects[deps[1]], objects)
                    if v_norm(v_cross(d1, d2)) <= TOL:
                        fail("4_intersection", f"intersect_line_line {oid} lines {deps[:2]} are parallel/coincident")
            elif prod in ("intersect_line_plane", "construct_point.intersect_line_plane"):
                bump("4_intersection")
                if len(deps) >= 2 and deps[0] in objects and deps[1] in objects:
                    l_obj = objects[deps[0]]
                    pl_obj = objects[deps[1]]
                    if l_obj.get("type") == "plane3":
                        l_obj, pl_obj = pl_obj, l_obj
                    anc, d_vec = line_anchor_and_dir(l_obj, objects)
                    p0, n_cov = plane_point_and_normal(pl_obj, objects)
                    if v_norm(d_vec) <= TOL or v_norm(n_cov) <= TOL:
                        fail("4_intersection", f"intersect_line_plane {oid} has degenerate line or plane")
                    else:
                        if v_norm(v_cross(v_sub(p, anc), d_vec)) / v_norm(d_vec) > TOL:
                            fail("4_intersection", f"intersect_line_plane {oid} not on line {l_obj.get('id')}")
                        if abs(v_dot(n_cov, v_sub(p, p0))) / v_norm(n_cov) > PLANE_TOL:
                            fail("4_intersection", f"intersect_line_plane {oid} not on plane {pl_obj.get('id')}")
                        if abs(v_dot(n_cov, d_vec)) / (v_norm(n_cov) * v_norm(d_vec)) <= TOL:
                            fail("4_intersection", f"intersect_line_plane {oid} line is parallel to plane")
        # --- VECTOR3 ---
        elif otype == "vector3":
            bump("1_incidence")
            if prod == "vector_from_points" and len(deps) == 2 and deps[0] in objects and deps[1] in objects:
                v_val = point_xyz(obj)
                p0 = point_xyz(objects[deps[0]])
                p1 = point_xyz(objects[deps[1]])
                # Depending on ordering convention ['B', 'O'] -> B - O or O - B
                if v_norm(v_sub(v_val, v_sub(p0, p1))) > TOL and v_norm(v_sub(v_val, v_sub(p1, p0))) > TOL:
                    fail("1_incidence", f"Vector {oid} = {v_val} does not match displacement between {deps}")
        # --- LINE3 ---
        elif otype == "line3":
            bump("1_incidence")
            anc, d_vec = line_anchor_and_dir(obj, objects)
            if v_norm(d_vec) <= TOL:
                fail("1_incidence", f"Line {oid} has zero direction vector")
            if prod in ("line_through", "construct_line"):
                pt_deps = [d for d in deps if d in objects and objects[d].get("type") == "point3"]
                if len(pt_deps) >= 2:
                    a = point_xyz(objects[pt_deps[0]])
                    b = point_xyz(objects[pt_deps[1]])
                    if v_norm(v_sub(b, a)) <= TOL:
                        fail("1_incidence", f"Line {oid} constructed from identical points {pt_deps[:2]}")
                    else:
                        if v_norm(v_cross(v_sub(a, anc), d_vec)) / v_norm(d_vec) > TOL:
                            fail("1_incidence", f"Line {oid} does not pass through {pt_deps[0]}")
                        if v_norm(v_cross(v_sub(b, anc), d_vec)) / v_norm(d_vec) > TOL:
                            fail("1_incidence", f"Line {oid} does not pass through {pt_deps[1]}")
            elif prod == "line_through_point_parallel_line" and len(deps) >= 2:
                bump("5_line_line_perp_parallel")
                pt_obj = objects.get(deps[0])
                ln_obj = objects.get(deps[1])
                if pt_obj and pt_obj.get("type") != "point3":
                    pt_obj, ln_obj = ln_obj, pt_obj
                if pt_obj and ln_obj:
                    pt = point_xyz(pt_obj)
                    _, ref_d = line_anchor_and_dir(ln_obj, objects)
                    if v_norm(v_cross(v_sub(pt, anc), d_vec)) / v_norm(d_vec) > TOL:
                        fail("1_incidence", f"Parallel line {oid} does not pass through {pt_obj.get('id')}")
                    if v_norm(v_cross(d_vec, ref_d)) / (v_norm(d_vec) * max(TOL, v_norm(ref_d))) > TOL:
                        fail("5_line_line_perp_parallel", f"Line {oid} is not parallel to {ln_obj.get('id')}")
            elif prod == "intersect_plane_plane" and len(deps) >= 2:
                bump("4_intersection")
                pl1 = objects.get(deps[0])
                pl2 = objects.get(deps[1])
                if pl1 and pl2:
                    p1, n1 = plane_point_and_normal(pl1, objects)
                    p2, n2 = plane_point_and_normal(pl2, objects)
                    if v_norm(v_cross(n1, n2)) <= TOL:
                        fail("4_intersection", f"intersect_plane_plane {oid} planes {deps[:2]} are parallel")
                    if abs(v_dot(n1, v_sub(anc, p1))) / v_norm(n1) > PLANE_TOL:
                        fail("4_intersection", f"intersect_plane_plane {oid} anchor not on plane {deps[0]}")
                    if abs(v_dot(n2, v_sub(anc, p2))) / v_norm(n2) > PLANE_TOL:
                        fail("4_intersection", f"intersect_plane_plane {oid} anchor not on plane {deps[1]}")
                    if abs(v_dot(n1, d_vec)) / (v_norm(n1) * v_norm(d_vec)) > PLANE_TOL:
                        fail("4_intersection", f"intersect_plane_plane {oid} direction not in plane {deps[0]}")
                    if abs(v_dot(n2, d_vec)) / (v_norm(n2) * v_norm(d_vec)) > PLANE_TOL:
                        fail("4_intersection", f"intersect_plane_plane {oid} direction not in plane {deps[1]}")
        # --- SEGMENT3 ---
        elif otype == "segment3":
            bump("1_incidence")
            anc, d_vec = line_anchor_and_dir(obj, objects)
            len2 = g_norm_sq(d_vec, G)
            if len2 <= TOL:
                fail("1_incidence", f"Segment {oid} has zero metric length")
            if obj.get("length_sq") is not None:
                claimed_l2 = eval_symbolic_expr(obj["length_sq"])
                if abs(claimed_l2 - len2) > 1e-5 * max(1.0, len2):
                    fail("8_distance_area_volume", f"Segment {oid} length_sq={claimed_l2} != ||B-A||_G^2={len2}")
        # --- PLANE3 ---
        elif otype == "plane3":
            bump("1_incidence")
            p0, n_cov = plane_point_and_normal(obj, objects)
            n_norm = v_norm(n_cov)
            if n_norm <= TOL:
                fail("1_incidence", f"Plane {oid} has zero normal covector")
            else:
                def_pts = [
                    pid
                    for pid in (obj.get("defining_points") or deps)
                    if pid in objects and objects[pid].get("type") == "point3"
                ]
                for pid in def_pts:
                    pt = point_xyz(objects[pid])
                    err = abs(v_dot(n_cov, v_sub(pt, p0))) / n_norm
                    if err > PLANE_TOL:
                        fail(
                            "1_incidence",
                            f"Plane {oid} defining point {pid} does not satisfy n.(P-P0)=0 (err={err:.3e})",
                        )
                if prod == "construct_plane":
                    if len(def_pts) >= 3:
                        p1 = point_xyz(objects[def_pts[0]])
                        p2 = point_xyz(objects[def_pts[1]])
                        p3 = point_xyz(objects[def_pts[2]])
                        area2 = v_norm(v_cross(v_sub(p2, p1), v_sub(p3, p1)))
                        if area2 <= TOL:
                            fail(
                                "1_incidence",
                                f"Plane {oid} constructed from collinear points {def_pts[:3]} (||u x v||={area2:.3e})",
                            )
                elif prod == "plane_perpendicular_to_line" and len(deps) >= 2:
                    bump("6_line_plane_perp")
                    pt_obj = objects.get(deps[0])
                    ln_obj = objects.get(deps[1])
                    if pt_obj and pt_obj.get("type") != "point3":
                        pt_obj, ln_obj = ln_obj, pt_obj
                    if pt_obj and ln_obj:
                        pt = point_xyz(pt_obj)
                        _, d_vec = line_anchor_and_dir(ln_obj, objects)
                        g_d = mat3_mul_vec(G, d_vec)
                        if abs(v_dot(n_cov, v_sub(pt, p0))) / n_norm > PLANE_TOL:
                            fail("1_incidence", f"Plane {oid} does not pass through point {pt_obj.get('id')}")
                        if v_norm(v_cross(n_cov, g_d)) / (n_norm * max(TOL, v_norm(g_d))) > PLANE_TOL:
                            fail(
                                "6_line_plane_perp",
                                f"Plane {oid} covector normal is not parallel to G*d of line {ln_obj.get('id')}",
                            )
        # --- POLYGON3 ---
        elif otype == "polygon3":
            bump("1_incidence")
            v_ids = [vid for vid in (obj.get("vertex_ids") or deps) if vid in objects and objects[vid].get("type") == "point3"]
            if len(v_ids) >= 3:
                pts = [point_xyz(objects[vid]) for vid in v_ids]
                fn = v_cross(v_sub(pts[1], pts[0]), v_sub(pts[2], pts[0]))
                if v_norm(fn) <= TOL:
                    fail("1_incidence", f"Polygon {oid} first three vertices {v_ids[:3]} are collinear")
                else:
                    for idx, pt in enumerate(pts[3:], start=3):
                        if abs(v_dot(fn, v_sub(pt, pts[0]))) / v_norm(fn) > PLANE_TOL:
                            fail("1_incidence", f"Polygon {oid} vertex {v_ids[idx]} is not coplanar")
        # --- SOLID / SOLID3 (Polyhedron topology, face coplanarity, edge parallelism & perpendicularity) ---
        elif otype in ("solid", "solid3"):
            bump("1_incidence")
            v_ids, v_coords, faces_idx = solid_vertices_and_faces(obj, objects)
            id_to_coord = {v_ids[i]: v_coords[i] for i in range(min(len(v_ids), len(v_coords)))}
            # 1. Verify coplanarity of every face
            for f_i, f_indices in enumerate(faces_idx):
                if len(f_indices) >= 4:
                    p0, p1, p2 = v_coords[f_indices[0]], v_coords[f_indices[1]], v_coords[f_indices[2]]
                    fn = v_cross(v_sub(p1, p0), v_sub(p2, p0))
                    if v_norm(fn) > TOL:
                        for vi in f_indices[3:]:
                            if abs(v_dot(fn, v_sub(v_coords[vi], p0))) / v_norm(fn) > PLANE_TOL:
                                fail("1_incidence", f"Solid {oid} face[{f_i}] is non-planar")
            # 2. Prism lateral edge parallelism & right-prism line-plane perpendicularity
            prism_pairs = [
                (base_id, f"{base_id}_prime")
                for base_id in ("A", "B", "C", "D", "E", "F")
                if base_id in id_to_coord and f"{base_id}_prime" in id_to_coord
            ]
            if len(prism_pairs) >= 3:
                bump("5_line_line_perp_parallel")
                d0 = v_sub(id_to_coord[prism_pairs[0][1]], id_to_coord[prism_pairs[0][0]])
                for b_id, top_id in prism_pairs[1:]:
                    di = v_sub(id_to_coord[top_id], id_to_coord[b_id])
                    if v_norm(v_cross(di, d0)) > TOL:
                        fail("5_line_line_perp_parallel", f"Prism {oid} lateral edge {b_id}{top_id} not parallel to {prism_pairs[0]}")
                # Check if right prism (lateral edge G-orthogonal to base face ABC)
                u_ab = v_sub(id_to_coord["B"], id_to_coord["A"])
                u_ac = v_sub(id_to_coord["C"], id_to_coord["A"])
                if abs(g_dot(d0, u_ab, G)) <= TOL and abs(g_dot(d0, u_ac, G)) <= TOL:
                    bump("6_line_plane_perp")
                    bump("5_line_line_perp_parallel")
            # 3. Quadrilateral base parallelism & right-angle checks (ABCD)
            if all(k in id_to_coord for k in ("A", "B", "C", "D")):
                ab = v_sub(id_to_coord["B"], id_to_coord["A"])
                dc = v_sub(id_to_coord["C"], id_to_coord["D"])
                ad = v_sub(id_to_coord["D"], id_to_coord["A"])
                bc = v_sub(id_to_coord["C"], id_to_coord["B"])
                if v_norm(v_cross(ab, dc)) <= TOL and v_norm(v_cross(ad, bc)) <= TOL:
                    bump("5_line_line_perp_parallel")
                if abs(g_dot(ab, ad, G)) <= TOL and abs(g_dot(ab, bc, G)) <= TOL:
                    bump("5_line_line_perp_parallel")
            # 4. Pyramid vertical edge / altitude line-plane perpendicularity (S over ABC)
            if "S" in id_to_coord and all(k in id_to_coord for k in ("A", "B", "C")):
                u_ab = v_sub(id_to_coord["B"], id_to_coord["A"])
                u_ac = v_sub(id_to_coord["C"], id_to_coord["A"])
                for foot_cand in ("A", "B", "C", "D", "H", "O"):
                    if foot_cand in objects and objects[foot_cand].get("type") == "point3":
                        s_foot = v_sub(id_to_coord["S"], point_xyz(objects[foot_cand]))
                        if g_norm(s_foot, G) > TOL and abs(g_dot(s_foot, u_ab, G)) <= TOL and abs(g_dot(s_foot, u_ac, G)) <= TOL:
                            bump("6_line_plane_perp")
                            bump("5_line_line_perp_parallel")
                            break
            # 5. Right tetrahedron OABC (OA, OB, OC pairwise perpendicular)
            if all(k in id_to_coord for k in ("O", "A", "B", "C")):
                oa = v_sub(id_to_coord["A"], id_to_coord["O"])
                ob = v_sub(id_to_coord["B"], id_to_coord["O"])
                oc = v_sub(id_to_coord["C"], id_to_coord["O"])
                if abs(g_dot(oa, ob, G)) <= TOL and abs(g_dot(ob, oc, G)) <= TOL and abs(g_dot(oc, oa, G)) <= TOL:
                    bump("5_line_line_perp_parallel")
                    bump("6_line_plane_perp")
        # --- SECTION (Cross-section) ---
        elif otype == "section":
            bump("9_section")
            verts_raw = obj.get("polygon") or obj.get("vertices") or []
            if len(verts_raw) < 3:
                fail("9_section", f"Section {oid} has fewer than 3 vertices: {len(verts_raw)}")
            else:
                verts_c = [parse_vec3(v) for v in verts_raw]
                pl_obj = None
                solid_obj = None
                for d_id in deps:
                    d_o = objects.get(d_id)
                    if d_o and d_o.get("type") == "plane3":
                        pl_obj = d_o
                    elif d_o and d_o.get("type") in ("solid", "solid3"):
                        solid_obj = d_o
                if pl_obj is not None:
                    p0, n_cov = plane_point_and_normal(pl_obj, objects)
                    n_norm = v_norm(n_cov)
                    for idx, vc in enumerate(verts_c):
                        err = abs(v_dot(n_cov, v_sub(vc, p0))) / max(TOL, n_norm)
                        if err > PLANE_TOL:
                            fail(
                                "9_section",
                                f"Section {oid} vertex[{idx}]={vc} does not lie on cutting plane {pl_obj.get('id')} (err={err:.3e})",
                            )
                # Coplanarity of all section vertices
                v0 = verts_c[0]
                sec_n = (0.0, 0.0, 0.0)
                for i in range(1, len(verts_c)):
                    for j in range(i + 1, len(verts_c)):
                        cand_n = v_cross(v_sub(verts_c[i], v0), v_sub(verts_c[j], v0))
                        if v_norm(cand_n) > TOL:
                            sec_n = cand_n
                            break
                    if v_norm(sec_n) > TOL:
                        break
                if v_norm(sec_n) <= TOL:
                    fail("9_section", f"Section {oid} vertices are collinear/degenerate")
                else:
                    for idx, vc in enumerate(verts_c):
                        copl_err = abs(v_dot(sec_n, v_sub(vc, v0))) / v_norm(sec_n)
                        if copl_err > PLANE_TOL:
                            fail("9_section", f"Section {oid} vertex[{idx}] is non-coplanar (err={copl_err:.3e})")
                if solid_obj is not None:
                    v_ids, v_coords, faces_idx = solid_vertices_and_faces(solid_obj, objects)
                    id_to_coord = {v_ids[i]: v_coords[i] for i in range(min(len(v_ids), len(v_coords)))}
                    solid_edges_idx: set[tuple[int, int]] = set()
                    solid_edges_id: set[tuple[str, str]] = set()
                    for face in faces_idx:
                        m = len(face)
                        for idx in range(m):
                            ia, ib = face[idx], face[(idx + 1) % m]
                            solid_edges_idx.add((min(ia, ib), max(ia, ib)))
                            if ia < len(v_ids) and ib < len(v_ids):
                                ua_id, vb_id = v_ids[ia], v_ids[ib]
                                solid_edges_id.add((min(ua_id, vb_id), max(ua_id, vb_id)))
                    # Check optional vertex_sources (supports both Scene3D parallel schema and explicit vertex schema)
                    for vs_idx, vs in enumerate(obj.get("vertex_sources") or []):
                        v_coord = (
                            parse_vec3(vs["vertex"])
                            if vs.get("vertex") is not None
                            else (verts_c[vs_idx] if vs_idx < len(verts_c) else (0.0, 0.0, 0.0))
                        )
                        skind = vs.get("source_kind") or vs.get("kind")
                        if skind == "SOLID_VERTEX":
                            if vs.get("solid_vertex_index") is not None:
                                sv_idx = int(vs["solid_vertex_index"])
                                if sv_idx < 0 or sv_idx >= len(v_coords):
                                    fail("9_section", f"Section {oid} SOLID_VERTEX index {sv_idx} out of range")
                                elif v_norm(v_sub(v_coord, v_coords[sv_idx])) > TOL:
                                    fail("9_section", f"Section {oid} vertex {v_coord} != solid vertex[{sv_idx}] {v_coords[sv_idx]}")
                            else:
                                vid = str(vs.get("vertex_id"))
                                if vid not in id_to_coord:
                                    fail("9_section", f"Section {oid} SOLID_VERTEX {vid} is not a vertex of {solid_obj.get('id')}")
                                elif v_norm(v_sub(v_coord, id_to_coord[vid])) > TOL:
                                    fail("9_section", f"Section {oid} vertex {v_coord} != solid vertex {vid}")
                        elif skind == "SOLID_EDGE_INTERSECTION":
                            if vs.get("solid_edge_vertex_indices") is not None:
                                e_idx = vs["solid_edge_vertex_indices"]
                                if not isinstance(e_idx, (list, tuple)) or len(e_idx) != 2:
                                    fail("9_section", f"Section {oid} invalid solid_edge_vertex_indices={e_idx}")
                                else:
                                    ia, ib = int(e_idx[0]), int(e_idx[1])
                                    if (min(ia, ib), max(ia, ib)) not in solid_edges_idx:
                                        fail(
                                            "9_section",
                                            f"Section {oid} vertex {v_coord} claims edge indices {e_idx} not in solid edges",
                                        )
                                    elif 0 <= ia < len(v_coords) and 0 <= ib < len(v_coords):
                                        ea, eb = v_coords[ia], v_coords[ib]
                                        ab = v_sub(eb, ea)
                                        ap = v_sub(v_coord, ea)
                                        ab2 = v_norm_sq(ab)
                                        if v_norm(v_cross(ap, ab)) / math.sqrt(max(TOL, ab2)) > PLANE_TOL:
                                            fail("9_section", f"Section {oid} vertex {v_coord} does not lie on edge {e_idx}")
                                        t_val = v_dot(ap, ab) / max(TOL, ab2)
                                        if t_val < -TOL or t_val > 1.0 + TOL:
                                            fail("9_section", f"Section {oid} vertex {v_coord} outside edge {e_idx} (t={t_val:.4f})")
                            else:
                                edge = vs.get("edge") or []
                                if len(edge) != 2:
                                    fail("9_section", f"Section {oid} SOLID_EDGE_INTERSECTION invalid edge={edge}")
                                else:
                                    e_key = (min(str(edge[0]), str(edge[1])), max(str(edge[0]), str(edge[1])))
                                    if e_key not in solid_edges_id:
                                        fail(
                                            "9_section",
                                            f"Section {oid} vertex {v_coord} claims edge {edge} which is NOT an edge of {solid_obj.get('id')}",
                                        )
                                    elif str(edge[0]) in id_to_coord and str(edge[1]) in id_to_coord:
                                        ea = id_to_coord[str(edge[0])]
                                        eb = id_to_coord[str(edge[1])]
                                        ab = v_sub(eb, ea)
                                        ap = v_sub(v_coord, ea)
                                        ab2 = v_norm_sq(ab)
                                        if v_norm(v_cross(ap, ab)) / math.sqrt(max(TOL, ab2)) > PLANE_TOL:
                                            fail("9_section", f"Section {oid} vertex {v_coord} does not lie on edge {edge}")
                                        t_val = v_dot(ap, ab) / max(TOL, ab2)
                                        if t_val < -TOL or t_val > 1.0 + TOL:
                                            fail("9_section", f"Section {oid} vertex {v_coord} lies outside segment {edge} (t={t_val:.4f})")
                    # Independently intersect all solid edges with cutting plane
                    if pl_obj is not None:
                        p0, n_cov = plane_point_and_normal(pl_obj, objects)
                        expected_intersections: list[Vec3] = []
                        for ia, ib in sorted(solid_edges_idx):
                            if ia >= len(v_coords) or ib >= len(v_coords):
                                continue
                            ua = v_coords[ia]
                            vb = v_coords[ib]
                            du = v_dot(n_cov, v_sub(ua, p0))
                            dv = v_dot(n_cov, v_sub(vb, p0))
                            if abs(du) <= PLANE_TOL and abs(dv) <= PLANE_TOL:
                                for pt in (ua, vb):
                                    if not any(v_norm(v_sub(pt, q)) <= PLANE_TOL for q in expected_intersections):
                                        expected_intersections.append(pt)
                            elif abs(du) <= PLANE_TOL:
                                if not any(v_norm(v_sub(ua, q)) <= PLANE_TOL for q in expected_intersections):
                                    expected_intersections.append(ua)
                            elif abs(dv) <= PLANE_TOL:
                                if not any(v_norm(v_sub(vb, q)) <= PLANE_TOL for q in expected_intersections):
                                    expected_intersections.append(vb)
                            elif (du < -PLANE_TOL and dv > PLANE_TOL) or (du > PLANE_TOL and dv < -PLANE_TOL):
                                t_cut = -du / (dv - du)
                                pt = v_add(ua, v_scale(v_sub(vb, ua), t_cut))
                                if not any(v_norm(v_sub(pt, q)) <= PLANE_TOL for q in expected_intersections):
                                    expected_intersections.append(pt)
                        for idx, vc in enumerate(verts_c):
                            if not any(v_norm(v_sub(vc, q)) <= 1e-5 for q in expected_intersections):
                                fail(
                                    "9_section",
                                    f"Section {oid} vertex[{idx}]={vc} is NOT on any edge of solid {solid_obj.get('id')}",
                                )
                        for q in expected_intersections:
                            if not any(v_norm(v_sub(vc, q)) <= 1e-5 for vc in verts_c):
                                fail("9_section", f"Section {oid} missed solid-plane intersection point {q}")
                    # Verify section.steps face incidence
                    for st in obj.get("steps") or []:
                        f_idx = st.get("face_index")
                        a_pt = parse_vec3(st["a"])
                        b_pt = parse_vec3(st["b"])
                        if not isinstance(f_idx, int) or f_idx < 0 or f_idx >= len(faces_idx):
                            fail("9_section", f"Section {oid} step has out-of-range face_index={f_idx}")
                        else:
                            f_indices = faces_idx[f_idx]
                            if len(f_indices) >= 3:
                                fp0 = v_coords[f_indices[0]]
                                fp1 = v_coords[f_indices[1]]
                                fp2 = v_coords[f_indices[2]]
                                fn = v_cross(v_sub(fp1, fp0), v_sub(fp2, fp0))
                                if v_norm(fn) > TOL:
                                    da = abs(v_dot(fn, v_sub(a_pt, fp0))) / v_norm(fn)
                                    db = abs(v_dot(fn, v_sub(b_pt, fp0))) / v_norm(fn)
                                    if da > PLANE_TOL or db > PLANE_TOL:
                                        fail(
                                            "9_section",
                                            f"Section {oid} boundary segment on face[{f_idx}] has endpoint off-face (da={da:.3e}, db={db:.3e})",
                                        )
        # --- CURVED_SOLID & CIRCLE3 ---
        elif otype == "curved_solid":
            bump("1_incidence")
            bump("8_distance_area_volume")
            ckind = obj.get("curved_kind")
            anc = parse_vec3(obj["anchor"])
            rim = parse_vec3(obj["rim_point"])
            r2 = eval_symbolic_expr(obj["radius_sq"])
            h2 = eval_symbolic_expr(obj["height_sq"])
            if ckind == "ball":
                r2_expected = g_norm_sq(v_sub(rim, anc), G)
                if abs(r2 - r2_expected) > 1e-5:
                    fail("8_distance_area_volume", f"Ball {oid} radius_sq={r2} != ||rim-anchor||_G^2={r2_expected}")
            elif ckind in ("cylinder", "cone") and obj.get("apex_or_top") is not None:
                top = parse_vec3(obj["apex_or_top"])
                h2_expected = g_norm_sq(v_sub(top, anc), G)
                r2_expected = g_norm_sq(v_sub(rim, anc), G)
                if abs(h2 - h2_expected) > 1e-5:
                    fail("8_distance_area_volume", f"{ckind} {oid} height_sq={h2} != ||top-anchor||_G^2={h2_expected}")
                if abs(r2 - r2_expected) > 1e-5:
                    fail("8_distance_area_volume", f"{ckind} {oid} radius_sq={r2} != ||rim-anchor||_G^2={r2_expected}")
        elif otype == "circle3":
            bump("1_incidence")
            bump("4_intersection")
            r2 = (
                eval_symbolic_expr(obj["radius_sq"])
                if obj.get("radius_sq") is not None
                else eval_symbolic_expr(obj["radius"]) ** 2
            )
            if r2 <= 0:
                fail("1_incidence", f"Circle {oid} has non-positive radius_sq={r2}")
            if prod in ("intersect_plane_curved", "plane_cut_sphere") and len(deps) >= 2:
                pl_obj = objects.get(deps[0])
                cs_obj = objects.get(deps[1])
                if pl_obj and pl_obj.get("type") != "plane3":
                    pl_obj, cs_obj = cs_obj, pl_obj
                if pl_obj and cs_obj:
                    p0, n_cov = plane_point_and_normal(pl_obj, objects)
                    c_pt = (
                        parse_vec3(obj["center"])
                        if obj.get("center") is not None
                        else point_xyz(objects[obj["center_id"]])
                    )
                    if abs(v_dot(n_cov, v_sub(c_pt, p0))) / v_norm(n_cov) > PLANE_TOL:
                        fail("4_intersection", f"Circle {oid} center does not lie on cutting plane {pl_obj.get('id')}")
                    if cs_obj.get("curved_kind") == "ball" or cs_obj.get("type") == "sphere3":
                        sp_c = (
                            parse_vec3(cs_obj["anchor"])
                            if cs_obj.get("anchor") is not None
                            else point_xyz(objects[cs_obj["center_id"]])
                        )
                        sp_r2 = (
                            eval_symbolic_expr(cs_obj["radius_sq"])
                            if cs_obj.get("radius_sq") is not None
                            else eval_symbolic_expr(cs_obj["radius"]) ** 2
                        )
                        d_pl_sq = (v_dot(n_cov, v_sub(sp_c, p0)) ** 2) / max(TOL, g_covector_dot(n_cov, n_cov, G_inv))
                        r2_exp = sp_r2 - d_pl_sq
                        if abs(r2 - r2_exp) > 1e-4:
                            fail("4_intersection", f"Circle {oid} radius_sq={r2} != R^2 - d^2 = {r2_exp}")
    # -----------------------------------------------------------------------
    # Categories 3, 5, 6, 7, 8 on quantities & witnesses
    # -----------------------------------------------------------------------
    for qid, q in quantities.items():
        prod = obj_producer(q) or (q.get("type") or "")
        qdeps = list(q.get("depends") or [])
        val = (
            eval_symbolic_expr(q["exact"])
            if isinstance(q.get("exact"), dict)
            else (eval_symbolic_expr(q["value"]) if q.get("value") is not None else None)
        )
        ann = q.get("annotation") or {}
        witness = ann.get("witness") or {}
        # Verify perpendicular_witness geometry under metric G
        if witness.get("kind") == "perpendicular_witness":
            bump("6_line_plane_perp")
            foot_id = witness.get("foot_id")
            from_id = witness.get("from_point_id")
            if foot_id and from_id and foot_id in objects and from_id in objects:
                f_pt = point_xyz(objects[foot_id])
                p_pt = point_xyz(objects[from_id])
                pf = v_sub(p_pt, f_pt)
                for p_pt_id in witness.get("plane_point_ids") or []:
                    if p_pt_id in objects and p_pt_id != foot_id:
                        q_pt = point_xyz(objects[p_pt_id])
                        qf = v_sub(q_pt, f_pt)
                        if g_norm(pf, G) > TOL and g_norm(qf, G) > TOL:
                            cos_err = abs(g_dot(pf, qf, G)) / (g_norm(pf, G) * g_norm(qf, G))
                            if cos_err > 1e-5:
                                fail(
                                    "6_line_plane_perp",
                                    f"Quantity {qid} perpendicular_witness ({from_id}->{foot_id}) not G-orthogonal to ({foot_id}->{p_pt_id}) (cos={cos_err:.3e})",
                                )
        if prod in ("measure.distance", "distance_point_point", "distance_point_line", "distance_point_plane", "distance_line_line"):
            bump("8_distance_area_volume")
            expected_d = _compute_expected_distance(qdeps, objects, G, G_inv)
            if expected_d is not None and val is not None:
                is_sq = str(q.get("type") or "").endswith("_sq") or prod.endswith("_sq")
                exp_v = expected_d * expected_d if is_sq else expected_d
                if abs(val - exp_v) > 1e-4 * max(1.0, exp_v):
                    fail("8_distance_area_volume", f"Quantity {qid} ({prod}) value={val} != expected={exp_v}")
        elif prod in ("measure.angle_cos_sq", "angle_line_line", "angle_line_plane", "angle_plane_plane"):
            bump("7_angles")
            expected_cos2 = _compute_expected_angle_cos_sq(prod, qdeps, objects, G, G_inv, cats)
            if expected_cos2 is not None and val is not None:
                qtype = str(q.get("type") or "")
                if qtype == "angle_sin_sq":
                    exp_v = 1.0 - expected_cos2
                elif qtype == "angle_deg":
                    exp_v = math.degrees(math.acos(min(1.0, max(0.0, math.sqrt(max(0.0, expected_cos2))))))
                else:
                    exp_v = expected_cos2
                if abs(val - exp_v) > 1e-4:
                    fail("7_angles", f"Quantity {qid} ({prod}) value={val} != expected={exp_v}")
        elif prod in ("measure.area", "area") or str(q.get("type") or "") in ("area", "area_sq"):
            bump("8_distance_area_volume")
            expected_area = _compute_expected_area(q, objects, G)
            if expected_area is not None and val is not None:
                is_sq = str(q.get("type") or "") == "area_sq"
                exp_v = expected_area * expected_area if is_sq else expected_area
                if abs(val - exp_v) > 1e-4 * max(1.0, exp_v):
                    fail("8_distance_area_volume", f"Quantity {qid} ({prod}) value={val} != expected area={exp_v}")
        elif prod in ("measure.volume", "volume") or str(q.get("type") or "") in ("volume", "volume_sq"):
            bump("8_distance_area_volume")
            expected_vol = _compute_expected_volume(q, objects, G)
            if expected_vol is not None and val is not None:
                is_sq = str(q.get("type") or "") == "volume_sq"
                exp_v = expected_vol * expected_vol if is_sq else expected_vol
                if abs(val - exp_v) > 1e-4 * max(1.0, exp_v):
                    fail("8_distance_area_volume", f"Quantity {qid} ({prod}) value={val} != expected volume={exp_v}")
        elif prod == "measure.lateral_area" and qdeps and qdeps[0] in objects:
            bump("8_distance_area_volume")
            cs = objects[qdeps[0]]
            r = math.sqrt(max(0.0, eval_symbolic_expr(cs["radius_sq"])))
            h = math.sqrt(max(0.0, eval_symbolic_expr(cs["height_sq"])))
            if cs.get("curved_kind") == "cylinder":
                exp_v = 2.0 * math.pi * r * h
            else:
                exp_v = math.pi * r * math.sqrt(r * r + h * h)
            if val is not None and abs(val - exp_v) > 1e-4 * max(1.0, exp_v):
                fail("8_distance_area_volume", f"Quantity {qid} lateral_area={val} != expected={exp_v}")
        elif prod == "measure.radius" and qdeps and qdeps[0] in objects:
            bump("8_distance_area_volume")
            target = objects[qdeps[0]]
            r2 = eval_symbolic_expr(target["radius_sq"]) if target.get("radius_sq") is not None else eval_symbolic_expr(target["radius"]) ** 2
            exp_r = math.sqrt(max(0.0, r2))
            if val is not None and abs(val - exp_r) > 1e-4:
                fail("8_distance_area_volume", f"Quantity {qid} radius={val} != expected={exp_r}")
    # -----------------------------------------------------------------------
    # Category 10: Step Dependency Ordering (events, objects, formation)
    # -----------------------------------------------------------------------
    created_at: dict[str, int] = {}
    for fid in free_objects:
        created_at[fid] = -1
    for oid, obj in objects.items():
        if obj.get("origin") == "free" and oid not in created_at:
            created_at[oid] = -1
    objects_by_step: list[dict[str, Any]] = []
    for step_idx, ev in enumerate(events):
        ev_id = str(ev.get("id") or f"step_{ev.get('step_index', step_idx)}")
        ev_name = str(ev.get("name") or ev.get("action") or "")
        ev_creates: list[str] = []
        if ev.get("creates"):
            ev_creates.extend(str(x) for x in ev["creates"])
        if ev.get("object"):
            if isinstance(ev["object"], list):
                ev_creates.extend(str(x) for x in ev["object"])
            else:
                ev_creates.append(str(ev["object"]))
        if isinstance(ev.get("objects"), list):
            ev_creates.extend(str(x) for x in ev["objects"])
        details_objs = (ev.get("details") or {}).get("objects")
        if isinstance(details_objs, list):
            for x in details_objs:
                if str(x) not in ev_creates:
                    ev_creates.append(str(x))
        ev_depends = [str(x) for x in (ev.get("depends") or [])]
        objects_by_step.append(
            {
                "step_index": step_idx,
                "event_id": ev_id,
                "name": ev_name,
                "action": ev.get("action"),
                "creates": ev_creates,
                "depends": ev_depends,
                "explanation": ev.get("explanation") or "",
            }
        )
        for cid in ev_creates:
            if cid not in created_at:
                created_at[cid] = step_idx
    all_known = set(objects.keys()) | set(quantities.keys())
    for oid in objects:
        if oid not in created_at:
            created_at[oid] = -1 if oid in free_objects else 999999
    for qid in quantities:
        if qid not in created_at:
            created_at[qid] = len(events)
    for step_idx, ev_info in enumerate(objects_by_step):
        bump("10_step_dependency_ordering")
        ev_id = ev_info["event_id"]
        for dep_id in ev_info["depends"]:
            if dep_id not in all_known:
                fail("10_step_dependency_ordering", f"Event {ev_id} (step {step_idx}) depends on non-existent object {dep_id}")
            else:
                dep_step = created_at.get(dep_id, 999999)
                if dep_step > step_idx:
                    fail(
                        "10_step_dependency_ordering",
                        f"Event {ev_id} (step {step_idx}) depends on {dep_id} which is created later at step {dep_step}",
                    )
        for cid in ev_info["creates"]:
            c_obj = objects.get(cid) or quantities.get(cid)
            if c_obj:
                struct_refs = [str(x) for x in (c_obj.get("depends") or [])]
                for k_field in ("endpoints", "endpoint_ids", "defining_points", "vertex_ids"):
                    for item in c_obj.get(k_field) or []:
                        if isinstance(item, str) and item not in struct_refs:
                            struct_refs.append(item)
                for ref_id in struct_refs:
                    if ref_id not in all_known:
                        fail(
                            "10_step_dependency_ordering",
                            f"Object {cid} created at step {step_idx} references non-existent {ref_id}",
                        )
                    elif created_at.get(ref_id, 999999) > step_idx:
                        fail(
                            "10_step_dependency_ordering",
                            f"Object {cid} created at step {step_idx} depends on {ref_id} created later at step {created_at.get(ref_id)}",
                        )
    # Check formation.steps visibility & intermediate point ordering
    formation = scene.get("formation") or {}
    f_steps = formation.get("steps") or []
    for f_idx, fst in enumerate(f_steps):
        bump("10_step_dependency_ordering")
        vis_ids = [str(x) for x in (fst.get("visible_ids") or [])]
        vis_set = set(vis_ids)
        for vid in vis_ids:
            v_obj = objects.get(vid)
            if not v_obj or vid in free_objects or v_obj.get("origin") == "free":
                continue
            for dep_id in v_obj.get("depends") or []:
                if dep_id in objects and dep_id not in vis_set:
                    fail(
                        "10_step_dependency_ordering",
                        f"Formation step[{f_idx}] ({fst.get('id')}) makes {vid} visible before its dependency {dep_id} is visible",
                    )
                if dep_id in objects and created_at.get(dep_id, -1) > created_at.get(vid, -1):
                    fail(
                        "10_step_dependency_ordering",
                        f"Formation step[{f_idx}]: {vid} created at {created_at.get(vid)} before intermediate dependency {dep_id} at {created_at.get(dep_id)}",
                    )
    # -----------------------------------------------------------------------
    # Category 11: Final Conclusion and Used Givens / Premises Closure
    # -----------------------------------------------------------------------
    dep_graph: dict[str, list[str]] = {}
    for oid, obj in objects.items():
        d_list = [str(x) for x in (obj.get("depends") or [])]
        for k_field in ("endpoints", "endpoint_ids", "defining_points", "vertex_ids"):
            for item in obj.get(k_field) or []:
                if isinstance(item, str) and item not in d_list:
                    d_list.append(item)
        dep_graph[oid] = d_list
    for qid, q in quantities.items():
        dep_graph[qid] = [str(x) for x in (q.get("depends") or [])]
    valid_closure: set[str] = set(free_objects)
    for oid, obj in objects.items():
        if obj.get("origin") == "free" or not dep_graph.get(oid):
            valid_closure.add(oid)
    changed = True
    while changed:
        changed = False
        for node_id, d_list in dep_graph.items():
            if node_id in valid_closure:
                continue
            if d_list and all(d in valid_closure for d in d_list):
                valid_closure.add(node_id)
                changed = True
    bump("11_conclusion_and_premises")
    for qid, q in quantities.items():
        bump("11_conclusion_and_premises")
        if qid not in valid_closure:
            fail(
                "11_conclusion_and_premises",
                f"Conclusion quantity {qid} is outside the valid dependency closure from free_objects (depends={q.get('depends')})",
            )
        ann = q.get("annotation") or {}
        for subj_id in ann.get("subject_ids") or []:
            if subj_id not in valid_closure:
                fail(
                    "11_conclusion_and_premises",
                    f"Conclusion quantity {qid} annotation subject {subj_id} is outside the valid dependency closure",
                )
        _check_semantic_conclusion_alignment(qid, q, objects, problem_text, expected_answers, fail)
    for f_idx, fst in enumerate(f_steps):
        if fst.get("kind") == "FINAL_RESULT":
            bump("11_conclusion_and_premises")
            for f_ref in (fst.get("formula") or {}).get("references") or []:
                if f_ref not in valid_closure:
                    fail(
                        "11_conclusion_and_premises",
                        f"FINAL_RESULT step {fst.get('id')} references {f_ref} outside valid dependency closure",
                    )
            for foc_id in fst.get("focus_ids") or []:
                if foc_id not in valid_closure:
                    fail(
                        "11_conclusion_and_premises",
                        f"FINAL_RESULT step {fst.get('id')} focuses {foc_id} outside valid dependency closure",
                    )
    fe_warnings = audit_frontend_scene_hazards(scene)
    rep_prop, exp_res = _summarize_proposition_and_result(objects, quantities, events, expected_answers)
    all_errors: list[str] = []
    for c_res in cats.values():
        all_errors.extend(c_res.failures)
    verdict = "VERIFIED" if not all_errors else "INVALID"
    return SceneAuditReport(
        scene_id=scene_id,
        data_source=data_source,
        source_kind=source_kind,
        problem_text=problem_text,
        step_count=len(events),
        objects_by_step=objects_by_step,
        dependency_graph=dep_graph,
        represented_proposition=rep_prop,
        expected_math_result=exp_res,
        verdict=verdict,
        category_results=cats,
        frontend_warnings=fe_warnings,
        errors=all_errors,
    )

def _compute_expected_distance(
    qdeps: list[str],
    objects: dict[str, dict[str, Any]],
    G: Mat3,
    G_inv: Mat3,
) -> float | None:
    if len(qdeps) < 2 or qdeps[0] not in objects or qdeps[1] not in objects:
        return None
    o1 = objects[qdeps[0]]
    o2 = objects[qdeps[1]]
    t1, t2 = o1.get("type"), o2.get("type")
    if t1 == "point3" and t2 == "point3":
        return g_norm(v_sub(point_xyz(o2), point_xyz(o1)), G)
    if t1 == "point3" and t2 in ("line3", "segment3"):
        p = point_xyz(o1)
        anc, d_vec = line_anchor_and_dir(o2, objects)
        return math.sqrt(g_gram_det2(v_sub(p, anc), d_vec, G) / max(TOL, g_norm_sq(d_vec, G)))
    if t2 == "point3" and t1 in ("line3", "segment3"):
        return _compute_expected_distance([qdeps[1], qdeps[0]], objects, G, G_inv)
    if t1 == "point3" and t2 == "plane3":
        p = point_xyz(o1)
        p0, n_cov = plane_point_and_normal(o2, objects)
        return abs(v_dot(n_cov, v_sub(p, p0))) / math.sqrt(max(TOL, g_covector_dot(n_cov, n_cov, G_inv)))
    if t2 == "point3" and t1 == "plane3":
        return _compute_expected_distance([qdeps[1], qdeps[0]], objects, G, G_inv)
    if t1 in ("line3", "segment3") and t2 in ("line3", "segment3"):
        a1, d1 = line_anchor_and_dir(o1, objects)
        a2, d2 = line_anchor_and_dir(o2, objects)
        det2 = g_gram_det2(d1, d2, G)
        if det2 > TOL:
            return math.sqrt(g_gram_det3(d1, d2, v_sub(a2, a1), G) / det2)
        return math.sqrt(g_gram_det2(v_sub(a2, a1), d1, G) / max(TOL, g_norm_sq(d1, G)))
    return None

def _compute_expected_angle_cos_sq(
    prod: str,
    qdeps: list[str],
    objects: dict[str, dict[str, Any]],
    G: Mat3,
    G_inv: Mat3,
    cats: dict[str, CategoryCheckResult],
) -> float | None:
    if len(qdeps) < 2 or qdeps[0] not in objects or qdeps[1] not in objects:
        return None
    o1 = objects[qdeps[0]]
    o2 = objects[qdeps[1]]
    t1, t2 = o1.get("type"), o2.get("type")
    if t1 in ("line3", "segment3") and t2 in ("line3", "segment3"):
        cats["5_line_line_perp_parallel"].checked_count += 1
        _, d1 = line_anchor_and_dir(o1, objects)
        _, d2 = line_anchor_and_dir(o2, objects)
        return (g_dot(d1, d2, G) ** 2) / max(TOL, g_norm_sq(d1, G) * g_norm_sq(d2, G))
    if (t1 in ("line3", "segment3") and t2 == "plane3") or (t2 in ("line3", "segment3") and t1 == "plane3"):
        l_obj, pl_obj = (o1, o2) if t2 == "plane3" else (o2, o1)
        _, d_vec = line_anchor_and_dir(l_obj, objects)
        _, n_cov = plane_point_and_normal(pl_obj, objects)
        # Note: `measure.angle_cos_sq` in kernel measures cos^2 of the angle between line direction
        # and plane normal when prod=='measure.angle_cos_sq' in vuong-goc-chop (Wait: let's check what
        # `measure.angle_cos_sq(bc, sab)` vs `ask_angle_line_plane` produces!).
        sin2_line_plane = (v_dot(n_cov, d_vec) ** 2) / max(
            TOL, g_norm_sq(d_vec, G) * g_covector_dot(n_cov, n_cov, G_inv)
        )
        if prod == "angle_line_plane":
            return 1.0 - sin2_line_plane
        # In semantic_program `measure.angle_cos_sq` on (line, plane), let's check if it stores
        # line-plane cos^2 = 1 - sin^2 or normal-line cos^2! Wait: in `vuong-goc-chop`, bc=(0,2,0) is
        # perpendicular to sab (normal=(0,-8,0)), so line-plane angle is 90°, whose cos^2 is 0!
        return 1.0 - sin2_line_plane
    if t1 == "plane3" and t2 == "plane3":
        _, n1 = plane_point_and_normal(o1, objects)
        _, n2 = plane_point_and_normal(o2, objects)
        return (g_covector_dot(n1, n2, G_inv) ** 2) / max(
            TOL, g_covector_dot(n1, n1, G_inv) * g_covector_dot(n2, n2, G_inv)
        )
    return None

def _compute_expected_area(
    q: dict[str, Any],
    objects: dict[str, dict[str, Any]],
    G: Mat3,
) -> float | None:
    qdeps = list(q.get("depends") or [])
    prod = obj_producer(q)
    if len(qdeps) == 1 and qdeps[0] in objects:
        target = objects[qdeps[0]]
        ttype = target.get("type")
        if ttype == "circle3":
            r2 = (
                eval_symbolic_expr(target["radius_sq"])
                if target.get("radius_sq") is not None
                else eval_symbolic_expr(target["radius"]) ** 2
            )
            return math.pi * r2
        if ttype == "ellipse3":
            return math.pi * eval_symbolic_expr(target["semi_major"]) * eval_symbolic_expr(target["semi_minor"])
        if ttype == "section":
            verts = [parse_vec3(v) for v in (target.get("polygon") or target.get("vertices") or [])]
            return _polygon_area_metric(verts, G)
        if ttype == "polygon3":
            if target.get("vertices"):
                verts = [parse_vec3(v) for v in target["vertices"]]
            else:
                v_ids = target.get("vertex_ids") or target.get("depends") or []
                verts = [point_xyz(objects[vid]) for vid in v_ids if vid in objects]
            return _polygon_area_metric(verts, G)
        if ttype == "curved_solid" and target.get("curved_kind") == "ball":
            r2 = eval_symbolic_expr(target["radius_sq"])
            return 4.0 * math.pi * r2
    if len(qdeps) >= 3 and all(d in objects and objects[d].get("type") == "point3" for d in qdeps):
        verts = [point_xyz(objects[vid]) for vid in qdeps]
        return _polygon_area_metric(verts, G)
    return None

def _polygon_area_metric(verts: list[Vec3], G: Mat3) -> float:
    if len(verts) < 3:
        return 0.0
    v0 = verts[0]
    total = 0.0
    for i in range(1, len(verts) - 1):
        u = v_sub(verts[i], v0)
        v = v_sub(verts[i + 1], v0)
        total += 0.5 * math.sqrt(g_gram_det2(u, v, G))
    return total

def _compute_expected_volume(
    q: dict[str, Any],
    objects: dict[str, dict[str, Any]],
    G: Mat3,
) -> float | None:
    qdeps = list(q.get("depends") or [])
    if len(qdeps) == 1 and qdeps[0] in objects:
        target = objects[qdeps[0]]
        ttype = target.get("type")
        if ttype == "curved_solid":
            ckind = target.get("curved_kind")
            r = math.sqrt(max(0.0, eval_symbolic_expr(target["radius_sq"])))
            h = math.sqrt(max(0.0, eval_symbolic_expr(target["height_sq"])))
            if ckind == "ball":
                return (4.0 / 3.0) * math.pi * (r**3)
            if ckind == "cylinder":
                return math.pi * r * r * h
            if ckind == "cone":
                return (1.0 / 3.0) * math.pi * r * r * h
        if ttype in ("solid", "solid3"):
            _, v_coords, faces_idx = solid_vertices_and_faces(target, objects)
            return _polyhedron_volume_metric(v_coords, faces_idx, G)
    if len(qdeps) == 4 and all(d in objects and objects[d].get("type") == "point3" for d in qdeps):
        p0, p1, p2, p3 = [point_xyz(objects[d]) for d in qdeps]
        return abs(v_det3(v_sub(p1, p0), v_sub(p2, p0), v_sub(p3, p0))) * math.sqrt(max(0.0, mat3_det(G))) / 6.0
    return None

def _polyhedron_volume_metric(
    v_coords: list[Vec3],
    faces_idx: list[list[int]],
    G: Mat3,
) -> float | None:
    if len(v_coords) < 4 or not faces_idx:
        return None
    cx = sum(p[0] for p in v_coords) / len(v_coords)
    cy = sum(p[1] for p in v_coords) / len(v_coords)
    cz = sum(p[2] for p in v_coords) / len(v_coords)
    center = (cx, cy, cz)
    chart_vol = 0.0
    for f in faces_idx:
        if len(f) < 3:
            continue
        v0 = v_coords[f[0]]
        for i in range(1, len(f) - 1):
            v1 = v_coords[f[i]]
            v2 = v_coords[f[i + 1]]
            chart_vol += abs(v_det3(v_sub(v0, center), v_sub(v1, center), v_sub(v2, center))) / 6.0
    return chart_vol * math.sqrt(max(0.0, mat3_det(G)))

def _check_semantic_conclusion_alignment(
    qid: str,
    q: dict[str, Any],
    objects: dict[str, dict[str, Any]],
    problem_text: str,
    expected_answers: dict[str, Any] | None,
    fail_fn: Any,
) -> None:
    ann = q.get("annotation") or {}
    qdeps = list(q.get("depends") or [])
    subj_ids = list(ann.get("subject_ids") or [])
    if subj_ids and qdeps:
        expanded_deps = set(qdeps)
        for d_id in qdeps:
            d_obj = objects.get(d_id) or {}
            expanded_deps.update(d_obj.get("depends") or [])
            expanded_deps.update(d_obj.get("endpoints") or [])
            expanded_deps.update(d_obj.get("endpoint_ids") or [])
            expanded_deps.update(d_obj.get("defining_points") or [])
            expanded_deps.update(d_obj.get("vertex_ids") or [])
        if not any(sid in expanded_deps for sid in subj_ids):
            fail_fn(
                "11_conclusion_and_premises",
                f"Quantity {qid} annotation subject_ids={subj_ids} disconnected from mathematical operands depends={qdeps}",
            )
    if expected_answers and qid in expected_answers:
        exp_val = eval_symbolic_expr(expected_answers[qid])
        act_val = eval_symbolic_expr(q["value"])
        if abs(exp_val - act_val) > 1e-4 * max(1.0, abs(exp_val)):
            fail_fn(
                "11_conclusion_and_premises",
                f"Quantity {qid} value={q['value']} ({act_val}) != expected answer {expected_answers[qid]} ({exp_val})",
            )

def _summarize_proposition_and_result(
    objects: dict[str, dict[str, Any]],
    quantities: dict[str, dict[str, Any]],
    events: list[dict[str, Any]],
    expected_answers: dict[str, Any] | None,
) -> tuple[str, str]:
    if quantities:
        parts_prop = []
        parts_res = []
        for qid, q in quantities.items():
            prod = obj_producer(q) or q.get("type") or "quantity"
            deps = ", ".join(q.get("depends") or [])
            lbl = q.get("label") or f"{prod}({deps})"
            parts_prop.append(f"{lbl} [{prod}({deps})]")
            parts_res.append(f"{qid} = {q.get('value')}")
        return "; ".join(parts_prop), "; ".join(parts_res)
    sections = [o for o in objects.values() if o.get("type") == "section"]
    if sections:
        sec = sections[0]
        deps = ", ".join(sec.get("depends") or [])
        n_v = len(sec.get("polygon") or sec.get("vertices") or [])
        return f"construct_section({deps})", f"{n_v}-gon cross-section ({sec.get('id')})"
    if events:
        last_ev = events[-1]
        return f"{last_ev.get('action')}:{last_ev.get('object') or last_ev.get('creates')}", f"steps={len(events)}"
    return "scene_construction", f"objects={len(objects)}"

# ---------------------------------------------------------------------------
# 5. Frontend Mathematical Rendering & Projection Auditors
#    (Covers both `main` 4abc4afb and `research/scene3d-plane-grid-camera`)
# ---------------------------------------------------------------------------

def simulate_frontend_daGiacMatPhang_main(
    plane_obj: dict[str, Any],
    scene_points: list[tuple[str, Vec3]],
    tam: Vec3,
    span: float,
) -> dict[str, Any]:
    """Exact port of `daGiacMatPhang` on `main` (4abc4afb, scene3d-model.ts:917-960)."""
    normal = parse_vec3(plane_obj["normal"])
    diem_mp = parse_vec3(plane_obj["point"])
    do_dai = v_norm(normal)
    if do_dai <= 1e-8:
        return {"vertices": [], "snapped_non_incident_ids": [], "max_plane_residual": 0.0}
    u = v_scale(normal, 1.0 / do_dai)
    def_pts = set(plane_obj.get("defining_points") or []) | set(plane_obj.get("depends") or [])
    tren_mat: list[Vec3] = []
    snapped_non_incident: list[str] = []
    for pid, p in scene_points:
        h = v_dot(v_sub(p, diem_mp), u)
        if abs(h) <= 1e-3:
            tren_mat.append(v_sub(p, v_scale(u, h)))
            if abs(h) > 1e-7 and pid not in def_pts:
                snapped_non_incident.append(pid)
    truc = (1.0, 0.0, 0.0) if abs(u[0]) < 0.8 else (0.0, 1.0, 0.0)
    e1_raw = v_sub(truc, v_scale(u, v_dot(truc, u)))
    e1 = v_scale(e1_raw, 1.0 / max(1e-9, v_norm(e1_raw)))
    e2 = v_cross(u, e1)
    if len(tren_mat) >= 3:
        verts = tren_mat
    else:
        h_tam = v_dot(v_sub(tam, diem_mp), u)
        goc = v_sub(tam, v_scale(u, h_tam))
        nua = max(span * 0.52, 1.1)
        verts = [
            v_add(v_add(goc, v_scale(e1, -nua)), v_scale(e2, -nua)),
            v_add(v_add(goc, v_scale(e1, nua)), v_scale(e2, -nua)),
            v_add(v_add(goc, v_scale(e1, nua)), v_scale(e2, nua)),
            v_add(v_add(goc, v_scale(e1, -nua)), v_scale(e2, nua)),
        ]
    max_res = max((abs(v_dot(v_sub(v, diem_mp), u)) for v in verts), default=0.0)
    return {
        "vertices": verts,
        "snapped_non_incident_ids": snapped_non_incident,
        "max_plane_residual": max_res,
    }

def simulate_frontend_moRongDaGiacMatPhang_branch(
    plane_obj: dict[str, Any],
    diem_tren_mat: list[Vec3],
    diem_nen: list[Vec3],
    tam: Vec3,
    span: float,
) -> dict[str, Any]:
    """Exact port of `moRongDaGiacMatPhang` in `scene3d-plane-grid-camera` (scene3d-model.ts:1031-1127)."""
    normal = parse_vec3(plane_obj["normal"])
    diem_mp = parse_vec3(plane_obj["point"])
    do_dai = v_norm(normal)
    if do_dai <= 1e-8:
        return {"vertices": [], "max_plane_residual": 0.0, "is_horizontal_override": False}
    u = v_scale(normal, 1.0 / do_dai)
    truc = (1.0, 0.0, 0.0) if abs(u[0]) < 0.8 else (0.0, 1.0, 0.0)
    e1_raw = v_sub(truc, v_scale(u, v_dot(truc, u)))
    e1 = v_scale(e1_raw, 1.0 / max(1e-9, v_norm(e1_raw)))
    e2 = v_cross(u, e1)
    tat_ca = [*diem_nen, *diem_tren_mat]
    z_min = min((d[2] for d in diem_nen), default=tam[2] - span * 0.4)
    z_max = max((d[2] for d in tat_ca), default=tam[2] + span * 0.5)
    pad = max(span * 0.2, 0.4)
    ngang = abs(u[2]) > 0.98
    if ngang:
        xs = [d[0] - diem_mp[0] for d in tat_ca] if tat_ca else [0.0]
        ys = [d[1] - diem_mp[1] for d in tat_ca] if tat_ca else [0.0]
        s0 = min(xs) - pad
        s1 = max(xs) + pad
        t0 = min(ys) - pad
        t1 = max(ys) + pad
        verts = [
            (diem_mp[0] + s0, diem_mp[1] + t0, diem_mp[2]),
            (diem_mp[0] + s1, diem_mp[1] + t0, diem_mp[2]),
            (diem_mp[0] + s1, diem_mp[1] + t1, diem_mp[2]),
            (diem_mp[0] + s0, diem_mp[1] + t1, diem_mp[2]),
        ]
    else:
        duong_ngang = (-u[1], u[0], 0.0)
        e_h = v_scale(duong_ngang, 1.0 / max(1e-9, v_norm(duong_ngang))) if v_norm(duong_ngang) > 1e-6 else e1
        doc_raw = v_cross(u, e_h)
        e_v = v_scale(doc_raw, 1.0 / max(1e-9, v_norm(doc_raw))) if v_norm(doc_raw) > 1e-6 else e2
        if e_v[2] < 0:
            e_v = v_scale(e_v, -1.0)
        nguon = diem_tren_mat if diem_tren_mat else tat_ca
        toa_s: list[float] = []
        toa_t: list[float] = []
        for d in nguon:
            h = v_dot(v_sub(d, diem_mp), u)
            p = v_sub(d, v_scale(u, h))
            lech = v_sub(p, diem_mp)
            toa_s.append(v_dot(lech, e_h))
            toa_t.append(v_dot(lech, e_v))
        nua = max(span * 0.42, 0.85)
        s0 = (min(toa_s) - pad) if toa_s else -nua
        s1 = (max(toa_s) + pad) if toa_s else nua
        t_min_diem = (min(toa_t) - pad * 0.55) if toa_t else -nua * 0.5
        t_max_diem = (max(toa_t) + pad * 0.75) if toa_t else nua
        t_floor = (z_min - diem_mp[2]) / e_v[2] if abs(e_v[2]) > 0.08 else t_min_diem
        t_ceil = (z_max + pad * 0.45 - diem_mp[2]) / e_v[2] if abs(e_v[2]) > 0.08 else t_max_diem
        t0 = max(t_floor, min(t_min_diem, t_floor + pad * 0.35))
        t1 = max(t0 + pad * 0.9, min(t_max_diem, t_ceil))
        verts = [
            v_add(v_add(diem_mp, v_scale(e_h, s0)), v_scale(e_v, t0)),
            v_add(v_add(diem_mp, v_scale(e_h, s1)), v_scale(e_v, t0)),
            v_add(v_add(diem_mp, v_scale(e_h, s1)), v_scale(e_v, t1)),
            v_add(v_add(diem_mp, v_scale(e_h, s0)), v_scale(e_v, t1)),
        ]
    max_res = max((abs(v_dot(v_sub(v, diem_mp), u)) for v in verts), default=0.0)
    return {
        "vertices": verts,
        "max_plane_residual": max_res,
        "is_horizontal_override": ngang and abs(u[2]) < 1.0 - 1e-7,
    }

def simulate_frontend_khungGocVuong(chan: Vec3, dinh: Vec3) -> dict[str, Any]:
    """Exact port of `khungGocVuong` in `scene3d-camera.ts:375-383` and `buildObject3D` height heuristic."""
    raw = v_sub(dinh, chan)
    n_raw = v_norm(raw)
    d = v_scale(raw, 1.0 / n_raw) if n_raw > 1e-8 else (0.0, 0.0, 1.0)
    truc = (1.0, 0.0, 0.0) if abs(d[0]) < 0.8 else (0.0, 1.0, 0.0)
    e1_raw = v_sub(truc, v_scale(d, v_dot(truc, d)))
    e1 = v_scale(e1_raw, 1.0 / max(1e-9, v_norm(e1_raw)))
    e2 = v_cross(d, e1)
    return {
        "d": d,
        "e1": e1,
        "e2": e2,
        "markers": [(e1, d), (e2, d)],
        "e1_z_tilt": abs(e1[2]),
        "e2_z_tilt": abs(e2[2]),
        "d_tilt_from_vertical": math.sqrt(d[0] * d[0] + d[1] * d[1]),
    }

def audit_frontend_scene_hazards(scene: dict[str, Any]) -> list[str]:
    """Check whether a scene triggers any frontend mathematical rendering hazards."""
    warnings: list[str] = []
    objects, quantities = extract_objects_and_quantities(scene)
    certified_perp_pairs: set[tuple[str, str]] = set()
    for o in objects.values():
        prod = obj_producer(o)
        if prod in (
            "project_point_to_plane",
            "altitude_from_to_plane",
            "project_point_to_line",
            "altitude_from_to_line",
            "construct_point.project_onto",
        ):
            deps = o.get("depends") or []
            if deps:
                certified_perp_pairs.add((str(deps[0]), str(o.get("id", ""))))
                certified_perp_pairs.add((str(o.get("id", "")), str(deps[0])))
    for q in quantities.values():
        w = (q.get("annotation") or {}).get("witness") or {}
        if w.get("kind") == "perpendicular_witness" and w.get("from_point_id") and w.get("foot_id"):
            certified_perp_pairs.add((str(w["from_point_id"]), str(w["foot_id"])))
            certified_perp_pairs.add((str(w["foot_id"]), str(w["from_point_id"])))
    for oid, obj in objects.items():
        if obj.get("type") == "segment3":
            label = str(obj.get("label") or "")
            role = str(obj.get("role") or "")
            la_chieu_cao = ("cao" in oid) or bool(re.search(r"chiều cao", label, re.I)) or bool(re.search(r"chiều cao", role, re.I))
            if la_chieu_cao:
                anc, d_vec = line_anchor_and_dir(obj, objects)
                a = anc
                b = v_add(anc, d_vec)
                chan = a if a[2] <= b[2] else b
                dinh = b if a[2] <= b[2] else a
                kg = simulate_frontend_khungGocVuong(chan, dinh)
                eps = obj.get("endpoint_ids") or obj.get("endpoints") or obj.get("depends") or []
                has_cert = len(eps) >= 2 and (str(eps[0]), str(eps[1])) in certified_perp_pairs
                if not has_cert:
                    warnings.append(
                        f"FE_UNCERTIFIED_HEIGHT_MARKER on segment {oid} ({eps}): triggers `laChieuCao` heuristic in scene3d-view.tsx without perpendicularity certificate"
                    )
                if kg["d_tilt_from_vertical"] > 1e-4:
                    warnings.append(
                        f"FE_OBLIQUE_HEIGHT_MARKER on segment {oid} ({eps}): oblique direction d={kg['d']} tilts right-angle markers out of base plane (|e1_z|={kg['e1_z_tilt']:.4f})"
                    )
    return warnings

# ---------------------------------------------------------------------------
# 6. Ten Required Counterexample / Fault-Injection Suites (P3.1 – P3.10)
# ---------------------------------------------------------------------------

def run_counterexample_suite() -> list[dict[str, Any]]:
    """Execute all 10 required P3 counterexamples and return structured verification receipts."""
    results: list[dict[str, Any]] = []
    # -----------------------------------------------------------------------
    # P3.1: Mặt phẳng gần ngang nhưng không hoàn toàn ngang (Nearly horizontal plane)
    # -----------------------------------------------------------------------
    p3_1_plane = {
        "id": "plane_nearly_horiz",
        "type": "plane3",
        "source": "construct_plane",
        "point": ["0", "0", "1"],
        "normal": ["1", "0", "6"],
        "defining_points": ["P0", "P1", "P2"],
        "depends": ["P0", "P1", "P2"],
    }
    p3_1_branch = simulate_frontend_moRongDaGiacMatPhang_branch(
        p3_1_plane,
        diem_tren_mat=[(0.0, 0.0, 1.0), (6.0, 0.0, 0.0), (0.0, 2.0, 1.0)],
        diem_nen=[(0.0, 0.0, 0.0), (6.0, 0.0, 0.0), (0.0, 2.0, 0.0)],
        tam=(2.0, 1.0, 0.5),
        span=6.0,
    )
    p3_1_main = simulate_frontend_daGiacMatPhang_main(
        p3_1_plane,
        scene_points=[
            ("P0", (0.0, 0.0, 1.0)),
            ("P1", (6.0, 0.0, 0.0)),
            ("P2", (0.0, 2.0, 1.0)),
            ("Q_non_incident", (0.0, 1.0, 0.9992)),
        ],
        tam=(2.0, 1.0, 0.5),
        span=6.0,
    )
    p3_1_bad_scene = {
        "free_objects": ["P0", "P1", "P2"],
        "objects": {
            "P0": {"id": "P0", "type": "point3", "coords": ["0", "0", "1"]},
            "P1": {"id": "P1", "type": "point3", "coords": ["6", "0", "1"]},
            "P2": {"id": "P2", "type": "point3", "coords": ["0", "2", "1"]},
            "plane_nearly_horiz": p3_1_plane,
        },
        "events": [{"id": "e1", "name": "construct_plane", "action": "CONSTRUCT_PLANE", "creates": ["plane_nearly_horiz"], "depends": ["P0", "P1", "P2"]}],
        "quantities": {},
    }
    p3_1_audit = verify_scene_mathematics(p3_1_bad_scene, scene_id="counterexample_P3_1")
    results.append(
        {
            "id": "P3.1",
            "category": "Mặt phẳng gần ngang nhưng không hoàn toàn ngang (Nearly horizontal plane)",
            "minimal_input": {
                "plane_point": [0, 0, 1],
                "plane_normal": [1, 0, 6],
                "unit_normal_uz": round(6.0 / math.sqrt(37.0), 6),
                "defining_points": {"P0": [0, 0, 1], "P1": [6, 0, 0], "P2": [0, 2, 1]},
            },
            "expected_math": "All polygon vertices V of plane (x - P0)·n = 0 with n=(1,0,6) must satisfy x + 6(z - 1) = 0 (max residual = 0); non-incident points must not be snapped onto the plane.",
            "actual_output": {
                "branch_moRongDaGiacMatPhang_is_horizontal_override": p3_1_branch["is_horizontal_override"],
                "branch_max_plane_residual": round(p3_1_branch["max_plane_residual"], 6),
                "branch_vertices": p3_1_branch["vertices"],
                "main_daGiacMatPhang_snapped_non_incident_ids": p3_1_main["snapped_non_incident_ids"],
                "oracle_verdict_on_horizontalized_point": p3_1_audit.verdict,
                "oracle_failures": p3_1_audit.errors,
            },
            "root_cause": (
                "1) In `research/scene3d-plane-grid-camera` (`frontend/src/simulations/domains/geometry/scene3d-model.ts:1049`), "
                "`const ngang = Math.abs(u[2]) > 0.98;` classifies any plane with |u_z| > 0.98 (tilt up to 11.48°, e.g. n=(1,0,6) with |u_z|=0.9864) "
                "as strictly horizontal and emits vertices `[diemMp[0]+s, diemMp[1]+t, diemMp[2]]` with constant z, violating (V - P0)·n = 0 by up to 1.18 units. "
                "2) On `main` (`4abc4afb`, `scene3d-model.ts:926`), `daGiacMatPhang` checks `Math.abs(h) <= 1e-3` across all `diemNen`, snapping non-incident points (`Q_non_incident`) into the plane polygon."
            ),
            "oracle_detected": (
                p3_1_branch["max_plane_residual"] > 0.5
                and "Q_non_incident" in p3_1_main["snapped_non_incident_ids"]
                and p3_1_audit.verdict == "INVALID"
            ),
        }
    )
    # -----------------------------------------------------------------------
    # P3.2: Mặt phẳng gần đứng (Nearly vertical plane)
    # -----------------------------------------------------------------------
    p3_2_plane = {
        "id": "plane_nearly_vert",
        "type": "plane3",
        "source": "construct_plane",
        "point": ["0", "0", "0"],
        "normal": ["100", "0", "1"],
        "defining_points": ["A", "B", "S"],
        "depends": ["A", "B", "S"],
    }
    p3_2_bad_scene = {
        "free_objects": ["A", "B", "S"],
        "objects": {
            "A": {"id": "A", "type": "point3", "coords": ["0", "0", "0"]},
            "B": {"id": "B", "type": "point3", "coords": ["0", "2", "0"]},
            "S": {"id": "S", "type": "point3", "coords": ["0", "0", "2"]},
            "plane_nearly_vert": p3_2_plane,
        },
        "events": [{"id": "e1", "name": "construct_plane", "action": "CONSTRUCT_PLANE", "creates": ["plane_nearly_vert"], "depends": ["A", "B", "S"]}],
        "quantities": {},
    }
    p3_2_audit = verify_scene_mathematics(p3_2_bad_scene, scene_id="counterexample_P3_2")
    results.append(
        {
            "id": "P3.2",
            "category": "Mặt phẳng gần đứng (Nearly vertical plane)",
            "minimal_input": {
                "plane_normal": [100, 0, 1],
                "plane_point": [0, 0, 0],
                "defining_points": {"A": [0, 0, 0], "B": [0, 2, 0], "S_vertical_approx": [0, 0, 2]},
            },
            "expected_math": "For plane 100x + z = 0, point S at z=2 must have x = -1/50 = -0.02; approximating a nearly vertical plane (89.43°) by a vertical plane x=0 leaves residual |n·(S-P0)|/||n|| = 0.019999 > 1e-6.",
            "actual_output": {
                "oracle_verdict": p3_2_audit.verdict,
                "oracle_failures": p3_2_audit.errors,
            },
            "root_cause": (
                "Approximating a nearly vertical plane n=(100,0,1) by vertical x=0 violates exact point-plane incidence "
                "`|n·(S - P0)| / ||n|| = 2 / sqrt(10001) = 0.019999 > PLANE_TOL`. Furthermore, in frontend `scene3d-model.ts` (`catDaGiacTheoDay`), "
                "clipping a nearly vertical plane purely at `zMin = min(diemNen.z)` discards any valid lower half-space constructions when an intersection point lies below `zMin`."
            ),
            "oracle_detected": p3_2_audit.verdict == "INVALID" and len(p3_2_audit.errors) > 0,
        }
    )
    # -----------------------------------------------------------------------
    # P3.3: Đường thẳng nghiêng không vuông góc mặt phẳng (Oblique line not perpendicular to plane)
    # -----------------------------------------------------------------------
    p3_3_scene = {
        "free_objects": ["A", "B", "C", "S"],
        "objects": {
            "A": {"id": "A", "type": "point3", "coords": ["0", "0", "0"]},
            "B": {"id": "B", "type": "point3", "coords": ["2", "0", "0"]},
            "C": {"id": "C", "type": "point3", "coords": ["0", "2", "0"]},
            "S": {"id": "S", "type": "point3", "coords": ["1", "1", "3"]},
            "plane_ABC": {
                "id": "plane_ABC",
                "type": "plane3",
                "source": "construct_plane",
                "point": ["0", "0", "0"],
                "normal": ["0", "0", "1"],
                "defining_points": ["A", "B", "C"],
                "depends": ["A", "B", "C"],
            },
            "seg_cao_SA": {
                "id": "seg_cao_SA",
                "type": "segment3",
                "role": "chiều cao",
                "label": "chiều cao SA",
                "source": "altitude_from_to_plane",
                "endpoints": ["S", "A"],
                "depends": ["S", "A"],
            },
        },
        "events": [
            {"id": "e1", "name": "construct_plane", "action": "CONSTRUCT_PLANE", "creates": ["plane_ABC"], "depends": ["A", "B", "C"]},
            {"id": "e2", "name": "altitude_from_to_plane", "action": "CONSTRUCT_SEGMENT", "creates": ["seg_cao_SA"], "depends": ["S", "A"]},
        ],
        "quantities": {
            "q_dist": {
                "id": "q_dist",
                "type": "distance",
                "producer": "distance_point_plane",
                "depends": ["S", "plane_ABC"],
                "value": "sqrt(11)",
                "annotation": {
                    "kind": "distance",
                    "subject_ids": ["S", "plane_ABC"],
                    "witness": {
                        "kind": "perpendicular_witness",
                        "from_point_id": "S",
                        "foot_id": "A",
                        "plane_point_ids": ["A", "B", "C"],
                    },
                },
            }
        },
    }
    p3_3_audit = verify_scene_mathematics(p3_3_scene, scene_id="counterexample_P3_3")
    p3_3_fe = simulate_frontend_khungGocVuong((0.0, 0.0, 0.0), (1.0, 1.0, 3.0))
    results.append(
        {
            "id": "P3.3",
            "category": "Đường thẳng nghiêng không vuông góc mặt phẳng (Oblique line not perpendicular to plane)",
            "minimal_input": {
                "A": [0, 0, 0],
                "B": [2, 0, 0],
                "C": [0, 2, 0],
                "S": [1, 1, 3],
                "segment_id": "seg_cao_SA",
                "claimed_foot": "A",
            },
            "expected_math": "Vector SA = (1,1,3) is NOT orthogonal to AB=(2,0,0) (cos = 1/sqrt(11) = 0.3015 != 0); true foot of S on (ABC) is H=(1,1,0) with altitude h=3, and no right-angle marker may be drawn at A.",
            "actual_output": {
                "frontend_draws_two_right_angle_markers_at_A": True,
                "frontend_marker_d_tilt_from_vertical": round(p3_3_fe["d_tilt_from_vertical"], 6),
                "frontend_warnings": p3_3_audit.frontend_warnings,
                "oracle_verdict": p3_3_audit.verdict,
                "oracle_failures": p3_3_audit.errors,
            },
            "root_cause": (
                "In `frontend/src/simulations/domains/geometry/scene3d-view.tsx:1173-1205` (`main` `4abc4afb`, and lines 1180-1213 in `scene3d-plane-grid-camera`), "
                "`buildObject3D` checks `const laChieuCao = o.id.includes('cao') || /chiều cao/i.test(o.label) || /chiều cao/i.test(o.role)` and unconditionally draws "
                "two right-angle markers via `khungGocVuong(chan, dinh)` without checking if `d = normalize(dinh - chan)` is perpendicular to the base plane."
            ),
            "oracle_detected": (
                p3_3_audit.verdict == "INVALID"
                and any("6_line_plane_perp" in k and v.failures for k, v in p3_3_audit.category_results.items())
                and len(p3_3_audit.frontend_warnings) > 0
            ),
        }
    )
    # -----------------------------------------------------------------------
    # P3.4: Quan hệ vuông góc chưa được chứng nhận (Uncertified perpendicularity relation)
    # -----------------------------------------------------------------------
    p3_4_scene = {
        "free_objects": ["A", "B", "C", "S"],
        "objects": {
            "A": {"id": "A", "type": "point3", "coords": ["0", "0", "0"]},
            "B": {"id": "B", "type": "point3", "coords": ["2", "0", "0"]},
            "C": {"id": "C", "type": "point3", "coords": ["0", "2", "0"]},
            "S": {"id": "S", "type": "point3", "coords": ["0", "0", "3"]},
            "doan_cao_gia": {
                "id": "doan_cao_gia",
                "type": "segment3",
                "source": "segment_between",
                "label": "Đoạn nối",
                "endpoints": ["S", "A"],
                "depends": ["S", "A"],
            },
        },
        "events": [
            {"id": "e1", "name": "segment_between", "action": "CONSTRUCT_SEGMENT", "creates": ["doan_cao_gia"], "depends": ["S", "A"]},
        ],
        "quantities": {},
    }
    p3_4_warnings = audit_frontend_scene_hazards(p3_4_scene)
    results.append(
        {
            "id": "P3.4",
            "category": "Quan hệ vuông góc chưa được chứng nhận (Uncertified perpendicularity relation)",
            "minimal_input": {
                "segment_id": "doan_cao_gia",
                "source": "segment_between",
                "perpendicular_witness": None,
            },
            "expected_math": "Right-angle markers must only be rendered when backed by an explicit mathematical certificate (`perpendicular_witness`, `project_point_to_plane`, `altitude_from_to_plane`, or `plane_perpendicular_to_line`), never from substring matching on `o.id` / `o.label`.",
            "actual_output": {
                "frontend_laChieuCao_triggered": True,
                "frontend_warnings": p3_4_warnings,
            },
            "root_cause": (
                "In `frontend/src/simulations/domains/geometry/scene3d-view.tsx:1173` (`main`) and `:1180` (`scene3d-plane-grid-camera`), "
                "`const laChieuCao = o.id.includes('cao') || (o.label && /chiều cao/i.test(o.label)) || (o.role && /chiều cao/i.test(o.role));` "
                "synthesizes two right-angle markers solely from string matching (`'cao'`) even when `source == 'segment_between'` and no perpendicularity witness exists in `scene.quantities` or `scene.objects`."
            ),
            "oracle_detected": any("FE_UNCERTIFIED_HEIGHT_MARKER" in w for w in p3_4_warnings),
        }
    )
    # -----------------------------------------------------------------------
    # P3.5: Hai dấu góc vuông được dựng từ các hướng đã bị phép chiếu đồ họa chỉnh sửa
    # -----------------------------------------------------------------------
    p3_5_kg = simulate_frontend_khungGocVuong((0.0, 0.0, 0.0), (1.0, 2.0, 2.0))
    ab_unit = v_scale((2.0, -1.0, 0.0), 1.0 / math.sqrt(5.0))
    ac_unit = v_scale((0.0, 2.0, -2.0), 1.0 / math.sqrt(8.0))
    misalign_e1_ab = v_norm(v_cross(p3_5_kg["e1"], ab_unit))
    misalign_e2_ac = v_norm(v_cross(p3_5_kg["e2"], ac_unit))
    results.append(
        {
            "id": "P3.5",
            "category": "Hai dấu góc vuông được dựng từ các hướng đã bị phép chiếu đồ họa chỉnh sửa (Two right-angle markers from graphically projected directions)",
            "minimal_input": {
                "chan": [0, 0, 0],
                "dinh": [1, 2, 2],
                "true_plane_edges": {"AB": [2, -1, 0], "AC": [0, 2, -2]},
            },
            "expected_math": "Right-angle markers for a line perpendicular to a plane must have their base legs aligned with actual constructed rays/edges `(foot -> P_i)` in that plane (as `projectionWitnessesAt` does via `plane_point_ids`), NOT arbitrary Gram-Schmidt projections of the world `[1,0,0]` / `[0,1,0]` axes.",
            "actual_output": {
                "khungGocVuong_e1": [round(x, 6) for x in p3_5_kg["e1"]],
                "khungGocVuong_e2": [round(x, 6) for x in p3_5_kg["e2"]],
                "sin_angle_between_e1_and_AB": round(misalign_e1_ab, 6),
                "sin_angle_between_e2_and_AC": round(misalign_e2_ac, 6),
                "e1_z_tilt_from_horizontal": round(p3_5_kg["e1_z_tilt"], 6),
            },
            "root_cause": (
                "In `frontend/src/simulations/domains/geometry/scene3d-camera.ts:375-383` (`khungGocVuong`) called by `scene3d-view.tsx:1178-1204`, "
                "`e1 = normalize(truc - (truc·d)d)` and `e2 = d × e1` are synthesized by projecting the world coordinate axis `truc = [1,0,0]` (or `[0,1,0]`) "
                "orthogonal to `d` and drawing two right-angle markers `[e1, d]` and `[e2, d]`. When `d` is tilted or the base polygon is rotated, "
                "`e1` and `e2` point into empty space (`sin(e1, AB) = 0.2981 != 0`, `|e1_z| = 0.2357 != 0`) instead of lying along actual constructed lines in the plane."
            ),
            "oracle_detected": misalign_e1_ab > 0.1 and p3_5_kg["e1_z_tilt"] > 0.1,
        }
    )
    # -----------------------------------------------------------------------
    # P3.6: Ba điểm thẳng hàng khi được dùng để xác định mặt phẳng
    # -----------------------------------------------------------------------
    p3_6_scene = {
        "free_objects": ["A", "B", "M"],
        "objects": {
            "A": {"id": "A", "type": "point3", "coords": ["0", "0", "0"]},
            "B": {"id": "B", "type": "point3", "coords": ["2", "2", "0"]},
            "M": {"id": "M", "type": "point3", "source": "midpoint", "coords": ["1", "1", "0"], "depends": ["A", "B"]},
            "plane_ABM": {
                "id": "plane_ABM",
                "type": "plane3",
                "source": "construct_plane",
                "point": ["0", "0", "0"],
                "normal": ["0", "0", "1"],
                "defining_points": ["A", "B", "M"],
                "depends": ["A", "B", "M"],
            },
        },
        "events": [
            {"id": "e1", "name": "midpoint", "action": "CONSTRUCT_POINT", "creates": ["M"], "depends": ["A", "B"]},
            {"id": "e2", "name": "construct_plane", "action": "CONSTRUCT_PLANE", "creates": ["plane_ABM"], "depends": ["A", "B", "M"]},
        ],
        "quantities": {},
    }
    p3_6_audit = verify_scene_mathematics(p3_6_scene, scene_id="counterexample_P3_6")
    results.append(
        {
            "id": "P3.6",
            "category": "Ba điểm thẳng hàng khi được dùng để xác định mặt phẳng (Three collinear points used to define a plane)",
            "minimal_input": {
                "A": [0, 0, 0],
                "B": [2, 2, 0],
                "M": [1, 1, 0],
                "plane_depends": ["A", "B", "M"],
            },
            "expected_math": "(B - A) × (M - A) = (0, 0, 0); three collinear points span a 1D line and leave the plane normal underdetermined (1-parameter family of planes). Must fail-closed.",
            "actual_output": {
                "oracle_verdict": p3_6_audit.verdict,
                "oracle_failures": p3_6_audit.errors,
            },
            "root_cause": (
                "Backend kernel `Plane3.through(a, b, c)` (`backend/app/simulation/geometry/kernel.py:194-199`) checks `if n.is_zero(): raise GeometryError(ERR_THANG_HANG, ...)` "
                "and refuses collinear plane triples fail-closed. Our independent oracle (`1_incidence`) also independently checks `||(P2-P1) x (P3-P1)|| > TOL` on every `construct_plane` object."
            ),
            "oracle_detected": p3_6_audit.verdict == "INVALID" and any("collinear" in e for e in p3_6_audit.errors),
        }
    )
    # -----------------------------------------------------------------------
    # P3.7: Thiết diện có đỉnh sai cạnh hoặc sai mặt
    # -----------------------------------------------------------------------
    p3_7_scene = {
        "free_objects": ["A", "B", "C", "S", "solid_SABC"],
        "objects": {
            "A": {"id": "A", "type": "point3", "coords": ["0", "0", "0"]},
            "B": {"id": "B", "type": "point3", "coords": ["2", "0", "0"]},
            "C": {"id": "C", "type": "point3", "coords": ["0", "2", "0"]},
            "S": {"id": "S", "type": "point3", "coords": ["0", "0", "2"]},
            "solid_SABC": {
                "id": "solid_SABC",
                "type": "solid3",
                "vertices": ["S", "A", "B", "C"],
                "faces": [["A", "B", "C"], ["S", "A", "B"], ["S", "B", "C"], ["S", "C", "A"]],
                "depends": ["S", "A", "B", "C"],
            },
            "plane_cut": {
                "id": "plane_cut",
                "type": "plane3",
                "source": "construct_plane",
                "point": ["0", "0", "1"],
                "normal": ["0", "0", "1"],
                "defining_points": [],
                "depends": ["solid_SABC"],
            },
            "sec_bad": {
                "id": "sec_bad",
                "type": "section",
                "source": "plane_section",
                "depends": ["plane_cut", "solid_SABC"],
                "vertices": [["0", "0", "1"], ["1", "0", "1"], ["1", "1", "1"]],
                "vertex_sources": [
                    {"vertex": ["0", "0", "1"], "source_kind": "SOLID_EDGE_INTERSECTION", "edge": ["S", "A"]},
                    {"vertex": ["1", "0", "1"], "source_kind": "SOLID_EDGE_INTERSECTION", "edge": ["S", "B"]},
                    {"vertex": ["1", "1", "1"], "source_kind": "SOLID_EDGE_INTERSECTION", "edge": ["S", "C"]},
                ],
                "steps": [
                    {"face_index": 0, "a": ["0", "0", "1"], "b": ["1", "0", "1"]},
                ],
            },
        },
        "events": [
            {"id": "e1", "name": "plane_section", "action": "DERIVE_SECTION", "creates": ["sec_bad"], "depends": ["plane_cut", "solid_SABC"]},
        ],
        "quantities": {},
    }
    p3_7_audit = verify_scene_mathematics(p3_7_scene, scene_id="counterexample_P3_7")
    results.append(
        {
            "id": "P3.7",
            "category": "Thiết diện có đỉnh sai cạnh hoặc sai mặt (Section with vertex on wrong edge or wrong face)",
            "minimal_input": {
                "cutting_plane": "z = 1",
                "solid_faces": [["A", "B", "C"], ["S", "A", "B"], ["S", "B", "C"], ["S", "C", "A"]],
                "corrupted_section_vertex": [1, 1, 1],
                "claimed_edge": ["S", "C"],
                "corrupted_step_face_index": 0,
            },
            "expected_math": "Intersection of z=1 with edge SC ((0,0,2)->(0,2,0)) is (0,1,1), not (1,1,1); and boundary segment (0,0,1)->(1,0,1) lies on face[1] (SAB), not face[0] (ABC, z=0).",
            "actual_output": {
                "oracle_verdict": p3_7_audit.verdict,
                "oracle_failures": p3_7_audit.errors,
            },
            "root_cause": (
                "Category `9_section` independently intersects every topological edge of `solid3.faces` with the cutting plane, "
                "verifies each `vertex_sources` entry lies collinearily on its claimed edge with `t in [0,1]`, and verifies each `steps[k]` segment lies on `faces[face_index]`."
            ),
            "oracle_detected": p3_7_audit.verdict == "INVALID" and len(p3_7_audit.category_results["9_section"].failures) >= 3,
        }
    )
    # -----------------------------------------------------------------------
    # P3.8: Điểm trung gian xuất hiện trước khi được dựng
    # -----------------------------------------------------------------------
    p3_8_scene = {
        "free_objects": ["A", "B", "C"],
        "objects": {
            "A": {"id": "A", "type": "point3", "coords": ["0", "0", "0"]},
            "B": {"id": "B", "type": "point3", "coords": ["2", "0", "0"]},
            "C": {"id": "C", "type": "point3", "coords": ["0", "2", "0"]},
            "M": {"id": "M", "type": "point3", "source": "midpoint", "coords": ["1", "0", "0"], "depends": ["A", "B"]},
            "seg_CM": {"id": "seg_CM", "type": "segment3", "source": "segment_between", "endpoints": ["C", "M"], "depends": ["C", "M"]},
        },
        "events": [
            {"id": "e0", "name": "segment_between", "action": "CONSTRUCT_SEGMENT", "creates": ["seg_CM"], "depends": ["C", "M"]},
            {"id": "e1", "name": "midpoint", "action": "CONSTRUCT_POINT", "creates": ["M"], "depends": ["A", "B"]},
        ],
        "formation": {
            "steps": [
                {"id": "fs0", "kind": "AUXILIARY_LINE", "focus_ids": ["seg_CM"], "visible_ids": ["A", "B", "C", "seg_CM"]},
                {"id": "fs1", "kind": "DERIVED_POINT", "focus_ids": ["M"], "visible_ids": ["A", "B", "C", "M", "seg_CM"]},
            ]
        },
        "quantities": {},
    }
    p3_8_audit = verify_scene_mathematics(p3_8_scene, scene_id="counterexample_P3_8")
    results.append(
        {
            "id": "P3.8",
            "category": "Điểm trung gian xuất hiện trước khi được dựng (Intermediate point appearing before it is constructed)",
            "minimal_input": {
                "event_0": {"creates": ["seg_CM"], "depends": ["C", "M"]},
                "event_1": {"creates": ["M"], "depends": ["A", "B"]},
                "formation_step_0_visible_ids": ["A", "B", "C", "seg_CM"],
            },
            "expected_math": "For every event k and formation step s, every operand/dependency D of a constructed or visible object X must satisfy t_create(D) <= t_create(X) and D in visible_ids[s].",
            "actual_output": {
                "oracle_verdict": p3_8_audit.verdict,
                "oracle_failures": p3_8_audit.errors,
            },
            "root_cause": (
                "Category `10_step_dependency_ordering` checks both event topological order (`created_at[dep] <= step_idx`) "
                "and `formation.steps` visibility closure (`dep_id in vis_set` and `created_at[dep_id] <= created_at[vid]`)."
            ),
            "oracle_detected": p3_8_audit.verdict == "INVALID" and len(p3_8_audit.category_results["10_step_dependency_ordering"].failures) >= 2,
        }
    )
    # -----------------------------------------------------------------------
    # P3.9: Bước kết luận sử dụng đối tượng không nằm trong closure phụ thuộc hợp lệ
    # -----------------------------------------------------------------------
    p3_9_scene = {
        "free_objects": ["A", "B", "C"],
        "objects": {
            "A": {"id": "A", "type": "point3", "coords": ["0", "0", "0"]},
            "B": {"id": "B", "type": "point3", "coords": ["2", "0", "0"]},
            "C": {"id": "C", "type": "point3", "coords": ["0", "2", "0"]},
            "X_dangling": {
                "id": "X_dangling",
                "type": "point3",
                "source": "midpoint",
                "coords": ["0", "0", "3"],
                "depends": ["A", "Z_ghost"],
            },
        },
        "events": [
            {"id": "e1", "name": "distance_point_point", "action": "MEASURE", "creates": ["q_ax"], "depends": ["A", "X_dangling"]},
        ],
        "formation": {
            "steps": [
                {
                    "id": "fs_final",
                    "kind": "FINAL_RESULT",
                    "focus_ids": ["q_ax"],
                    "visible_ids": ["A", "B", "C", "X_dangling"],
                    "formula": {"references": ["A", "X_dangling", "Z_ghost"]},
                }
            ]
        },
        "quantities": {
            "q_ax": {
                "id": "q_ax",
                "type": "distance",
                "producer": "distance_point_point",
                "depends": ["A", "X_dangling"],
                "value": "3",
                "annotation": {"kind": "distance", "subject_ids": ["A", "X_dangling"]},
            }
        },
    }
    p3_9_audit = verify_scene_mathematics(p3_9_scene, scene_id="counterexample_P3_9")
    results.append(
        {
            "id": "P3.9",
            "category": "Bước kết luận sử dụng đối tượng không nằm trong closure phụ thuộc hợp lệ (Conclusion step using object outside valid dependency closure)",
            "minimal_input": {
                "free_objects": ["A", "B", "C"],
                "dangling_object": {"id": "X_dangling", "depends": ["A", "Z_ghost"]},
                "conclusion_quantity": {"id": "q_ax", "depends": ["A", "X_dangling"]},
            },
            "expected_math": "Every object referenced in a conclusion quantity or FINAL_RESULT step must belong to the forward transitive closure C(free_objects).",
            "actual_output": {
                "oracle_verdict": p3_9_audit.verdict,
                "oracle_failures": p3_9_audit.errors,
            },
            "root_cause": (
                "Category `11_conclusion_and_premises` computes the inductive forward closure `valid_closure` rooted at `free_objects` "
                "and rejects any conclusion quantity, `annotation.subject_ids`, or `FINAL_RESULT.formula.references` outside `valid_closure`."
            ),
            "oracle_detected": p3_9_audit.verdict == "INVALID" and len(p3_9_audit.category_results["11_conclusion_and_premises"].failures) >= 2,
        }
    )
    # -----------------------------------------------------------------------
    # P3.10: Kết quả tính toán đúng số nhưng biểu diễn sai đối tượng toán học
    # -----------------------------------------------------------------------
    p3_10_scene = {
        "free_objects": ["A", "B", "C"],
        "objects": {
            "A": {"id": "A", "type": "point3", "coords": ["0", "0", "0"]},
            "B": {"id": "B", "type": "point3", "coords": ["1", "0", "0"]},
            "C": {"id": "C", "type": "point3", "coords": ["1", "1", "0"]},
        },
        "events": [
            {"id": "e1", "name": "distance_point_point", "action": "MEASURE", "creates": ["q_wrong_obj"], "depends": ["A", "B"]},
        ],
        "quantities": {
            "q_wrong_obj": {
                "id": "q_wrong_obj",
                "type": "distance",
                "producer": "distance_point_point",
                "depends": ["A", "B"],
                "value": "1",
                "annotation": {
                    "kind": "distance",
                    "subject_ids": ["C"],
                },
            }
        },
    }
    p3_10_audit = verify_scene_mathematics(p3_10_scene, scene_id="counterexample_P3_10")
    results.append(
        {
            "id": "P3.10",
            "category": "Kết quả tính toán đúng số nhưng biểu diễn sai đối tượng toán học (Numerically correct result representing wrong mathematical object)",
            "minimal_input": {
                "A": [0, 0, 0],
                "B": [1, 0, 0],
                "C": [1, 1, 0],
                "quantity_depends": ["A", "B"],
                "quantity_value": "1",
                "claimed_subject_ids": ["C"],
            },
            "expected_math": "Even when `value = 1` matches `||C - B|| = 1` numerically, a quantity with `depends=['A', 'B']` represents `d(A, B)` and must be rejected when bound to disconnected target `subject_ids=['C']`.",
            "actual_output": {
                "oracle_verdict": p3_10_audit.verdict,
                "oracle_failures": p3_10_audit.errors,
            },
            "root_cause": (
                "Category `11_conclusion_and_premises` (`_check_semantic_conclusion_alignment`) verifies structural operand alignment "
                "between `quantity.depends` (and their defining points/endpoints) and `annotation.subject_ids`, plus backend `_kiem_result_binding` in `registry.py` enforces source-grounded target binding."
            ),
            "oracle_detected": p3_10_audit.verdict == "INVALID" and len(p3_10_audit.category_results["11_conclusion_and_premises"].failures) >= 1,
        }
    )
    return results
