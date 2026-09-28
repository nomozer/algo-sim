# -*- coding: utf-8 -*-
"""Independent Scene3D hidden-line oracle (standard library only).

The product implementation is intentionally not imported.  Faces are
triangulated here, projected intervals are clipped analytically, and camera
depth is reconstructed with clip-space ``w``.  A second implementation uses
camera-ray/triangle intersection for synthetic and evidence cross-checks.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import sqrt, tan, pi
from typing import Any, Iterable


class OracleFailure(RuntimeError):
    def __init__(self, code: str, detail: str):
        self.code = code
        super().__init__(f"{code}: {detail}")


Vec3 = tuple[float, float, float]
Vec4 = tuple[float, float, float, float]
Mat4 = tuple[tuple[float, float, float, float], ...]


@dataclass(frozen=True)
class CameraSnapshot:
    view: Mat4
    projection: Mat4
    viewport_width: int
    viewport_height: int
    device_pixel_ratio: float = 1.0


@dataclass(frozen=True)
class Projected:
    screen: tuple[float, float]
    camera: Vec3
    clip_w: float
    camera_depth: float


@dataclass(frozen=True)
class Triangle:
    surface_id: str
    world: tuple[Vec3, Vec3, Vec3]
    projected: tuple[Projected, Projected, Projected]


def _v(value: Iterable[Any]) -> Vec3:
    values = tuple(float(Fraction(str(item))) for item in value)
    if len(values) != 3:
        raise ValueError("expected vec3")
    return values  # type: ignore[return-value]


def _sub(a: Vec3, b: Vec3) -> Vec3:
    return a[0] - b[0], a[1] - b[1], a[2] - b[2]


def _add(a: Vec3, b: Vec3) -> Vec3:
    return a[0] + b[0], a[1] + b[1], a[2] + b[2]


def _mul(a: Vec3, value: float) -> Vec3:
    return a[0] * value, a[1] * value, a[2] * value


def _dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a: Vec3, b: Vec3) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _norm(a: Vec3) -> float:
    return sqrt(_dot(a, a))


def _mat_vec(matrix: Mat4, vector: Vec4) -> Vec4:
    return tuple(sum(matrix[row][column] * vector[column] for column in range(4))
                 for row in range(4))  # type: ignore[return-value]


def perspective(fov_degrees: float, aspect: float, near: float, far: float) -> Mat4:
    scale = 1.0 / tan(fov_degrees * pi / 360.0)
    return (
        (scale / aspect, 0.0, 0.0, 0.0),
        (0.0, scale, 0.0, 0.0),
        (0.0, 0.0, (far + near) / (near - far), 2 * far * near / (near - far)),
        (0.0, 0.0, -1.0, 0.0),
    )


IDENTITY: Mat4 = (
    (1.0, 0.0, 0.0, 0.0),
    (0.0, 1.0, 0.0, 0.0),
    (0.0, 0.0, 1.0, 0.0),
    (0.0, 0.0, 0.0, 1.0),
)


def _project(point: Vec3, camera: CameraSnapshot) -> Projected:
    camera4 = _mat_vec(camera.view, (*point, 1.0))
    clip = _mat_vec(camera.projection, camera4)
    if abs(clip[3]) < 1e-12:
        raise OracleFailure("PERSPECTIVE_DEPTH_INTERPOLATION_INVALID", "clip.w is zero")
    ndc = clip[0] / clip[3], clip[1] / clip[3]
    screen = (
        (ndc[0] + 1.0) * camera.viewport_width * camera.device_pixel_ratio / 2.0,
        (1.0 - ndc[1]) * camera.viewport_height * camera.device_pixel_ratio / 2.0,
    )
    return Projected(screen, camera4[:3], clip[3], -camera4[2])


def _triangulate(indices: list[int]) -> list[tuple[int, int, int]]:
    """Independent deterministic fan for the convex solid-face contract."""
    if len(indices) < 3:
        return []
    return [(indices[0], indices[index], indices[index + 1])
            for index in range(1, len(indices) - 1)]


def _edge_records(solid: dict[str, Any]) -> list[dict[str, Any]]:
    if solid.get("edge_ownership"):
        return list(solid["edge_ownership"])
    vertex_ids = solid["vertex_ids"]
    records: dict[tuple[int, int], dict[str, Any]] = {}
    for face_index, face in enumerate(solid["faces"]):
        for index, ia in enumerate(face):
            ib = face[(index + 1) % len(face)]
            key = (ia, ib) if ia <= ib else (ib, ia)
            record = records.setdefault(key, {
                "edge_id": f"{solid['id']}::edge:{vertex_ids[key[0]]}-{vertex_ids[key[1]]}",
                "endpoint_ids": [vertex_ids[key[0]], vertex_ids[key[1]]],
                "adjacent_surface_ids": [],
            })
            record["adjacent_surface_ids"].append(f"{solid['id']}::face:{face_index}")
    return list(records.values())


def _triangles(scene: dict[str, Any], camera: CameraSnapshot) -> list[Triangle]:
    result: list[Triangle] = []
    for solid in (item for item in scene.get("objects", []) if item.get("type") == "solid"):
        vertices = [_v(point) for point in solid["vertices"]]
        policies = {item["surface_id"]: item for item in solid.get("surfaces", [])}
        for face_index, face in enumerate(solid["faces"]):
            surface_id = f"{solid['id']}::face:{face_index}"
            policy = policies.get(surface_id, {
                "surface_role": "SOLID_FACE", "occludes_edges": True,
            })
            if policy.get("surface_role") != "SOLID_FACE" or not policy.get("occludes_edges"):
                continue
            for ia, ib, ic in _triangulate(face):
                world = vertices[ia], vertices[ib], vertices[ic]
                result.append(Triangle(surface_id, world,
                                       tuple(_project(point, camera) for point in world)))
    return result


def _cross2(a: tuple[float, float], b: tuple[float, float]) -> float:
    return a[0] * b[1] - a[1] * b[0]


def _clip_segment_triangle(
    start: tuple[float, float], end: tuple[float, float],
    triangle: tuple[Projected, Projected, Projected],
) -> tuple[float, float] | None:
    points = [item.screen for item in triangle]
    area = _cross2((points[1][0] - points[0][0], points[1][1] - points[0][1]),
                   (points[2][0] - points[0][0], points[2][1] - points[0][1]))
    if abs(area) < 1e-10:
        return None
    orientation = 1.0 if area > 0 else -1.0
    direction = end[0] - start[0], end[1] - start[1]
    low, high = 0.0, 1.0
    for index, a in enumerate(points):
        b = points[(index + 1) % 3]
        side = b[0] - a[0], b[1] - a[1]
        c0 = orientation * _cross2(side, (start[0] - a[0], start[1] - a[1]))
        c1 = orientation * _cross2(side, direction)
        if abs(c1) < 1e-12:
            if c0 < -1e-9:
                return None
            continue
        boundary = -c0 / c1
        if c1 > 0:
            low = max(low, boundary)
        else:
            high = min(high, boundary)
        if low >= high - 1e-12:
            return None
    return max(0.0, low), min(1.0, high)


def _perspective_attribute(values: list[float], weights: list[float], ws: list[float]) -> float:
    denominator = sum(weight / w for weight, w in zip(weights, ws))
    if abs(denominator) < 1e-12:
        raise OracleFailure("PERSPECTIVE_DEPTH_INTERPOLATION_INVALID", "perspective denominator is zero")
    return sum(weight * value / w for weight, value, w in zip(weights, values, ws)) / denominator


def _barycentric(point: tuple[float, float], triangle: tuple[Projected, Projected, Projected]) -> list[float]:
    a, b, c = (item.screen for item in triangle)
    denominator = _cross2((b[0] - a[0], b[1] - a[1]), (c[0] - a[0], c[1] - a[1]))
    if abs(denominator) < 1e-12:
        return [float("nan")] * 3
    wb = _cross2((point[0] - a[0], point[1] - a[1]),
                 (c[0] - a[0], c[1] - a[1])) / denominator
    wc = _cross2((b[0] - a[0], b[1] - a[1]),
                 (point[0] - a[0], point[1] - a[1])) / denominator
    return [1.0 - wb - wc, wb, wc]


def _depth_delta(edge: tuple[Projected, Projected], triangle: Triangle, u: float) -> tuple[float, float, float]:
    point = (
        edge[0].screen[0] + (edge[1].screen[0] - edge[0].screen[0]) * u,
        edge[0].screen[1] + (edge[1].screen[1] - edge[0].screen[1]) * u,
    )
    edge_depth = _perspective_attribute(
        [edge[0].camera_depth, edge[1].camera_depth], [1.0 - u, u],
        [edge[0].clip_w, edge[1].clip_w],
    )
    bary = _barycentric(point, triangle.projected)
    surface_depth = _perspective_attribute(
        [item.camera_depth for item in triangle.projected], bary,
        [item.clip_w for item in triangle.projected],
    )
    return edge_depth, surface_depth, edge_depth - surface_depth


def _merge(intervals: list[tuple[float, float]]) -> list[tuple[float, float]]:
    result: list[list[float]] = []
    for start, end in sorted(intervals):
        if end <= start:
            continue
        if result and start <= result[-1][1] + 1e-7:
            result[-1][1] = max(result[-1][1], end)
        else:
            result.append([start, end])
    return [(start, end) for start, end in result]


def _visible_spans(hidden: list[tuple[float, float]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    cursor = 0.0
    for start, end in hidden:
        if start > cursor + 1e-7:
            result.append({"t0": cursor, "t1": start, "visibility": "VISIBLE"})
        result.append({"t0": start, "t1": end, "visibility": "HIDDEN"})
        cursor = end
    if cursor < 1.0 - 1e-7:
        result.append({"t0": cursor, "t1": 1.0, "visibility": "VISIBLE"})
    return result or [{"t0": 0.0, "t1": 1.0, "visibility": "VISIBLE"}]


def classify(scene: dict[str, Any], camera: CameraSnapshot) -> dict[str, Any]:
    triangles = _triangles(scene, camera)
    visible: list[str] = []
    hidden: list[str] = []
    mixed: list[str] = []
    spans: dict[str, list[dict[str, Any]]] = {}
    projected_lengths: dict[str, float] = {}
    witnesses: list[dict[str, Any]] = []
    for solid in (item for item in scene.get("objects", []) if item.get("type") == "solid"):
        vertex_ids = solid["vertex_ids"]
        index_by_id = {value: index for index, value in enumerate(vertex_ids)}
        vertices = [_v(point) for point in solid["vertices"]]
        for record in _edge_records(solid):
            edge_id = record["edge_id"]
            ia, ib = (index_by_id[value] for value in record["endpoint_ids"])
            projected = _project(vertices[ia], camera), _project(vertices[ib], camera)
            projected_lengths[edge_id] = sqrt(
                (projected[1].screen[0] - projected[0].screen[0]) ** 2
                + (projected[1].screen[1] - projected[0].screen[1]) ** 2
            )
            excluded = set(record.get("adjacent_surface_ids", []))
            intervals: list[tuple[float, float]] = []
            for triangle in triangles:
                if triangle.surface_id in excluded:
                    continue
                interval = _clip_segment_triangle(projected[0].screen, projected[1].screen,
                                                  triangle.projected)
                if not interval:
                    continue
                start, end = interval
                triangle_intervals: list[tuple[float, float]] = []
                # Depth is perspective-correct. Subdivide only to locate a
                # depth-order transition, never as a containment sampler.
                cuts = [start + (end - start) * index / 8 for index in range(9)]
                values = [_depth_delta(projected, triangle, value)[2] for value in cuts]
                for index in range(8):
                    left, right = cuts[index], cuts[index + 1]
                    if values[index] > 1e-7 and values[index + 1] > 1e-7:
                        triangle_intervals.append((left, right))
                    elif (values[index] > 1e-7) != (values[index + 1] > 1e-7):
                        lo, hi = left, right
                        left_hidden = values[index] > 1e-7
                        for _ in range(40):
                            mid = (lo + hi) / 2
                            if (_depth_delta(projected, triangle, mid)[2] > 1e-7) == left_hidden:
                                lo = mid
                            else:
                                hi = mid
                        transition = (lo + hi) / 2
                        triangle_intervals.append(
                            (left, transition) if left_hidden else (transition, right)
                        )
                    elif _depth_delta(projected, triangle, (left + right) / 2)[2] > 1e-7:
                        triangle_intervals.append((left, right))
                intervals.extend(triangle_intervals)
                if triangle_intervals:
                    middle = (start + end) / 2
                    edge_depth, surface_depth, delta = _depth_delta(projected, triangle, middle)
                    camera_point = _perspective_point(projected, middle)
                    ray_length = _norm(camera_point)
                    witnesses.append({
                        "edge_id": edge_id,
                        "screen_coordinate": [
                            projected[0].screen[0] + (projected[1].screen[0] - projected[0].screen[0]) * middle,
                            projected[0].screen[1] + (projected[1].screen[1] - projected[0].screen[1]) * middle,
                        ],
                        "camera_ray": {"origin": [0.0, 0.0, 0.0],
                                       "direction": [value / ray_length for value in camera_point]},
                        "candidate_surface_id": triangle.surface_id,
                        "edge_camera_depth": edge_depth,
                        "surface_camera_depth": surface_depth,
                        "depth_delta": delta,
                        "perspective_correction_method": "CLIP_W_RECIPROCAL_INTERPOLATION",
                    })
            edge_hidden = _merge(intervals)
            edge_spans = _visible_spans(edge_hidden)
            spans[edge_id] = edge_spans
            classes = {item["visibility"] for item in edge_spans}
            if classes == {"VISIBLE"}:
                visible.append(edge_id)
            elif classes == {"HIDDEN"}:
                hidden.append(edge_id)
            else:
                mixed.append(edge_id)
    return {
        "visible_edge_ids": sorted(visible),
        "hidden_edge_ids": sorted(hidden),
        "mixed_edge_ids": sorted(mixed),
        "edge_spans": spans,
        "edge_projected_lengths_px": projected_lengths,
        "witnesses": witnesses,
        "perspective_correction_method": "CLIP_W_RECIPROCAL_INTERPOLATION",
    }


def _perspective_point(edge: tuple[Projected, Projected], u: float) -> Vec3:
    weights = [1.0 - u, u]
    denominator = sum(weight / item.clip_w for weight, item in zip(weights, edge))
    return tuple(
        sum(weight * item.camera[axis] / item.clip_w for weight, item in zip(weights, edge))
        / denominator for axis in range(3)
    )  # type: ignore[return-value]


def _ray_triangle(target: Vec3, triangle: Triangle) -> bool:
    distance = _norm(target)
    direction = _mul(target, 1.0 / distance)
    a, b, c = (item.camera for item in triangle.projected)
    edge1, edge2 = _sub(b, a), _sub(c, a)
    h = _cross(direction, edge2)
    determinant = _dot(edge1, h)
    if abs(determinant) < 1e-10:
        return False
    inverse = 1.0 / determinant
    s = _mul(a, -1.0)
    u = inverse * _dot(s, h)
    if u < 0.0 or u > 1.0:
        return False
    q = _cross(s, edge1)
    v = inverse * _dot(direction, q)
    if v < 0.0 or u + v > 1.0:
        return False
    hit = inverse * _dot(edge2, q)
    return 1e-7 < hit < distance - max(1e-7, distance * 1e-7)


def reference_classify(scene: dict[str, Any], camera: CameraSnapshot) -> dict[str, Any]:
    """Independent physical-pixel ray reference (no projected clipping)."""
    triangles = _triangles(scene, camera)
    result = {"visible_edge_ids": [], "hidden_edge_ids": [], "mixed_edge_ids": [],
              "transitions": {}}
    for solid in (item for item in scene.get("objects", []) if item.get("type") == "solid"):
        index_by_id = {value: index for index, value in enumerate(solid["vertex_ids"])}
        vertices = [_v(point) for point in solid["vertices"]]
        for record in _edge_records(solid):
            ia, ib = (index_by_id[value] for value in record["endpoint_ids"])
            edge = _project(vertices[ia], camera), _project(vertices[ib], camera)
            length = sqrt(sum((edge[1].screen[i] - edge[0].screen[i]) ** 2 for i in (0, 1)))
            cells = max(16, int(length / 0.25) + 1)
            excluded = set(record.get("adjacent_surface_ids", []))
            states = []
            for index in range(cells):
                target = _perspective_point(edge, (index + 0.5) / cells)
                states.append(any(_ray_triangle(target, triangle) for triangle in triangles
                                  if triangle.surface_id not in excluded))
            transitions = [index / cells for index in range(1, cells)
                           if states[index] != states[index - 1]]
            edge_id = record["edge_id"]
            result["transitions"][edge_id] = transitions
            key = ("hidden_edge_ids" if all(states) else "visible_edge_ids"
                   if not any(states) else "mixed_edge_ids")
            result[key].append(edge_id)
    for key in ("visible_edge_ids", "hidden_edge_ids", "mixed_edge_ids"):
        result[key].sort()
    return result


def cross_check(scene: dict[str, Any], camera: CameraSnapshot) -> dict[str, Any]:
    analytic = classify(scene, camera)
    reference = reference_classify(scene, camera)
    for key in ("visible_edge_ids", "hidden_edge_ids", "mixed_edge_ids"):
        if analytic[key] != reference[key]:
            raise OracleFailure("PERSPECTIVE_ORACLE_REFERENCE_DISAGREEMENT",
                                f"{key}: analytic={analytic[key]} reference={reference[key]}")
    for edge_id, spans in analytic["edge_spans"].items():
        analytic_transitions = [item["t1"] for item in spans[:-1]]
        reference_transitions = reference["transitions"].get(edge_id, [])
        edge_record = next((item for solid in scene.get("objects", [])
                            if solid.get("type") == "solid"
                            for item in _edge_records(solid) if item["edge_id"] == edge_id), None)
        if not edge_record:
            continue
        solid = next(item for item in scene["objects"]
                     if item.get("type") == "solid" and edge_id.startswith(item["id"] + "::"))
        by_id = {value: index for index, value in enumerate(solid["vertex_ids"])}
        pa, pb = (_project(_v(solid["vertices"][by_id[value]]), camera).screen
                  for value in edge_record["endpoint_ids"])
        pixels = sqrt((pb[0] - pa[0]) ** 2 + (pb[1] - pa[1]) ** 2)
        if len(analytic_transitions) != len(reference_transitions) or any(
            abs(a - b) * pixels > 0.5
            for a, b in zip(analytic_transitions, reference_transitions)
        ):
            raise OracleFailure("PERSPECTIVE_ORACLE_REFERENCE_DISAGREEMENT",
                                f"transition mismatch for {edge_id}")
    return {"analytic": analytic, "reference": reference, "tolerance_physical_px": 0.5}


def reject_linear_ndc_depth(method: str) -> None:
    if method == "LINEAR_NDC_Z":
        raise OracleFailure("PERSPECTIVE_DEPTH_INTERPOLATION_INVALID",
                            "linear NDC-z interpolation is not perspective-correct")


def detect_coarse_sampling_blind_spot(coarse: str, authoritative: str) -> None:
    if coarse != authoritative:
        raise OracleFailure("SHARED_SAMPLING_BLIND_SPOT",
                            f"coarse={coarse}, authoritative={authoritative}")
