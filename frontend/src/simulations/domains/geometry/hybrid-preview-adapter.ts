/**
 * Biên vận chuyển DUY NHẤT của phản hồi Hybrid Route D Preview → envelope Scene3D
 * (HYBRID_PREVIEW_FRONTEND_CONTRACT §2–§4; ISSUE-ARCH-HYBRID-FRONTEND-OFFLINE-INTEGRATION F3/F4).
 *
 * Phản hồi preview là `{schema_version, envelope, route_d}` — `route_d` cố ý nằm NGOÀI envelope. Trước biên này
 * `SimulationWorkspace` đọc `envelope.route_d` (không bao giờ có), nên trên đường sản phẩm không quan sát/đáp số ký hiệu
 * nào tới được cảnh. Ở đây KHÔNG chép mù `route_d` vào envelope: chỉ những gì kiểm được với chính cảnh mới thành một
 * `HybridPreviewView` (khoá `hybrid_preview`), và module `generic.semantic_program` kiểm lại view ấy ở `validateEnvelope`
 * trước khi store nhận (store vẫn không biết miền — M2 #7). Phản hồi lệch hợp đồng ⇒ từ chối cả phản hồi.
 *
 * Không có lời gọi mạng nào ở đây: frontend KHÔNG gọi `/api/preview/hybrid` (operator-only); biên này chỉ dùng cho
 * fixture/harness offline và cho tuyến `/api/analyze` khi máy chủ bật chế độ Hybrid đã khai báo.
 */
import type { ClarificationPrompt } from "../../../core/types";
import type { Scene3D, SceneObject } from "./scene3d-model";

export const HYBRID_PREVIEW_SCHEMA = "hybrid-route-d-preview/1";
export const HYBRID_PREVIEW_ADAPTER = "hybrid-preview-adapter/2";
export const HYBRID_SIMULATION_SCHEMA = "hybrid-route-d-simulation/4";
export const HYBRID_SIMULATION_ADAPTER = "hybrid-simulation-adapter/4";
const HYBRID_SIMULATION_CONTRACT = "typed-fact-next/2";
const PLANE_SECTION_CERTIFICATE_VERSION = "plane-section-certificate/1";
const PLANE_SECTION_CERTIFICATE_RULE = "engine_derived_plane_section";
const PLANE_SECTION_CERTIFICATE_PRODUCER = "engine.kiem_chung_chi_thiet_dien";
const ENGINE_DERIVED_SECTION_CATEGORY = "ENGINE_DERIVED_SECTION";
const HYBRID_CLARIFICATION_SCHEMA = "route-d-clarification/1";
const RATIONAL_STR_RE = /^-?\d+(?:\/\d+)?$/;
const INTERNAL_LEAK_RE = /::|@[a-zA-Z0-9_]+|\b(?:kq|td|mp_td)_[a-zA-Z0-9_]+|_prime\b|Traceback/i;
/** Khoá của view đã kiểm trong envelope (do frontend tạo, không phải trường của backend). */
export const KHOA_HYBRID_VIEW = "hybrid_preview";

/** Đáp số tổng quát của một đại lượng kết quả: `answers[id]` ↔ đại lượng cảnh `kq_<id>` (engine.py `kq_{c.id}`). */
export interface HybridAnswerView {
  quantity_id: string;
  /** Exact coefficient checked against the scene at transport; retained for history revalidation. */
  coefficient?: string;
  /** Đáp số dạng chữ của backend, vd `a³√3/3`. */
  symbolic: string;
  /** Bậc theo đơn vị ký hiệu (0 ⇒ không thứ nguyên / đề dùng số). */
  dim: number;
  unit: string | null;
}

export type HybridEvidenceState = "TRUE_ON_CONFIGURATION" | "FALSE_ON_CONFIGURATION" | "UNVERIFIABLE";

/** Một quan sát trên hình dựng (KHÔNG phải chứng minh): loại quan hệ + trạng thái + bước neo. */
export interface HybridObservationView {
  check_id: string;
  group: "goal" | "negated";
  /** Tên LOẠI quan hệ (tiếng Việt) từ `planner.trace[].fn`. Vật cụ thể (vd BC, (SAB)) KHÔNG có trong adapter `/2`. */
  relation: string;
  evidence_state: HybridEvidenceState;
  /** Bước timeline mà từ đó quan sát được hiện: bước cuối — mệnh đề được kiểm trên hình đã dựng XONG. */
  anchor_step: number;
}

/** `route_d.source_provenance` của Adapter /4 (`adapter4_route.py`): dữ kiện đã đối chiếu nguyên văn đề. */
export interface HybridSourceProvenanceEntry {
  /** Định danh lời gọi của Adapter /4 (`result.calls[].id`) hoặc định danh dữ kiện mở rộng (`fact_id`). */
  id?: string;
  fact_id?: string | null;
  /** Tên hàm Registry của Adapter /4 (`regular_polygon`, `rectangle`, `right_angle`, `segment_length`...). */
  fn?: string;
  kind?: string;
  args?: Record<string, unknown>;
  quotes?: string[];
  verified?: boolean;
  polygon?: string[];
  edge?: string[];
  points?: string[];
  vertex?: string;
  rays?: string[][];
  line?: string;
  plane?: string[];
  value_display?: string | null;
}

export interface HybridRelationProofLayer {
  verified: true;
  [key: string]: unknown;
}

/** `route_d.relation_certificates` (`geometric-relation-certificate/1`, bốn tầng chứng cứ, hoặc dạng rút gọn đã kiểm). */
export interface HybridRelationCertificateEntry {
  schema_version?: string;
  relation_id?: string | null;
  relation_kind?: string;
  subject_id?: string;
  target_id?: string;
  SOURCE_GROUNDING_PROOF?: HybridRelationProofLayer;
  GEOMETRIC_RELATION_PROOF?: HybridRelationProofLayer;
  KERNEL_EXECUTION_PROOF?: HybridRelationProofLayer;
  RESULT_CERTIFICATE?: HybridRelationProofLayer;
  kind?: string;
  verified?: boolean;
  rule?: string | null;
  details?: Record<string, unknown> | null;
}

export interface HybridPreviewView {
  adapter_version: typeof HYBRID_PREVIEW_ADAPTER | typeof HYBRID_SIMULATION_ADAPTER;
  answers: HybridAnswerView[];
  observations: HybridObservationView[];
  /** Adapter /4 certificates and provenance, never promoted to source givens. */
  sections?: HybridSectionView[];
  /** Mang tiếp `route_d.source_provenance`/`relation_certificates` đã kiểm để Scene3D gắn dữ kiện đề cho với nguồn
   *  (`scene3d-model.ts`, `scene3d-semantic-policy.ts`); chỉ phần tử `verified: true` hoặc có trích dẫn mới qua. */
  source_provenance?: HybridSourceProvenanceEntry[];
  relation_certificates?: HybridRelationCertificateEntry[];
}

export interface HybridSectionView {
  section_id: string;
  certificate_version?: string;
  certificate_category?: string;
  boundary: string[] | null;
  vertices: {
    label: string | null;
    entity_id?: string;
    ordinal?: number;
    xyz?: string[];
    source_kind?: "SOLID_VERTEX" | "SOLID_EDGE_INTERSECTION";
    solid_vertex_index?: number | null;
    solid_edge_vertex_indices?: number[];
    choice?: string;
    edge: string[];
    provenance: string;
    stated: boolean;
  }[];
  closure_certificate: {
    boundary: string[];
    verified: boolean;
    rule: string;
    version?: string;
    polygon?: string[][];
  } | null;
}

export type HybridClarificationView = ClarificationPrompt;

/** Hàm loại `fact` của Registry (`geometry_functions/registry.py` — mệnh đề kiểm được trên hình) → tên cho học sinh.
 *  Ngoài bảng ⇒ tên chung (an toàn: không bịa quan hệ). */
const TEN_QUAN_HE: Record<string, string> = {
  perpendicular_line_plane: "quan hệ vuông góc giữa đường thẳng và mặt phẳng",
  perpendicular_lines: "quan hệ vuông góc giữa hai đường thẳng",
  face_perpendicular_base: "quan hệ vuông góc giữa mặt bên và mặt đáy",
  right_angle: "góc vuông",
  equal_length: "hai đoạn bằng nhau",
  segment_length: "độ dài đoạn thẳng",
  altitude: "đường cao",
  height: "chiều cao",
  orthogonal_projection: "hình chiếu vuông góc",
  rectangle: "hình chữ nhật",
  regular_polygon: "đa giác đều",
};
const TEN_QUAN_HE_CHUNG = "mệnh đề của đề";
const TEN_HOP_LE = new Set<string>([...Object.values(TEN_QUAN_HE), TEN_QUAN_HE_CHUNG]);

const TRANG_THAI = new Set<string>(["TRUE_ON_CONFIGURATION", "FALSE_ON_CONFIGURATION", "UNVERIFIABLE"]);

const CLARIFICATION_KIND_TO_NLU: Record<HybridClarificationView["kind"], HybridClarificationView["nlu_class"]> = {
  ambiguous: "AMBIGUOUS",
  missing_operand: "MISSING_DATA",
  unrecognized_term: "UNRECOGNIZED_WORDING",
  unsupported: "VALID_BUT_UNSUPPORTED",
};

const DERIVED_PLANE_RULES = new Set<string>([
  "section(plane defined by stated constraints)",
  "section(plane through point ∥ plane)",
  "section(plane through point strictly parallel to two lines)",
  "section(plane through point perpendicular to a line)",
]);

export type KetQuaPhanHoiHybrid =
  | { ok: true; envelope: Record<string, unknown> }
  | { ok: false; reason: string };

const laDoiTuong = (x: unknown): x is Record<string, unknown> => !!x && typeof x === "object" && !Array.isArray(x);
const gon = (s: unknown) => String(s ?? "").replace(/\s+/g, "");

/** Compare backend identities/coordinates only; no intersection, area or volume calculation in the consumer. */
function cungChuTrinh(a: unknown[], b: unknown[]): boolean {
  return a.length === b.length && [b, [...b].reverse()].some((cycle) =>
    cycle.some((_, offset) => a.every((x, i) => JSON.stringify(x) === JSON.stringify(cycle[(i + offset) % cycle.length]))));
}

/** Role the backend writes on engine-introduced section points (`backend/app/ai/function_route.py`). */
const VAI_DIEM_PHU = "Điểm dựng phụ";
/** What the planner (`_dinh_cat_canh`) fixes per provenance: is the point an unnamed auxiliary, and is its edge stated?
 *  `undefined` = not fixed by the contract. The scene cannot tell STATED_UNNAMED from DERIVED_FRESH (both unnamed
 *  auxiliaries); that distinction is backend authority only. */
const LUAT_NGUON: Record<string, { phu?: boolean; stated?: boolean; qua?: boolean }> = {
  SOURCE_NAMED: { phu: false, stated: true },
  STATED_UNNAMED: { phu: true, stated: true },
  DERIVED_FRESH: { phu: true, stated: false },
  // `qua`: the label is the plane's own through-point (a named source/premise point the plane depends on).
  THROUGH_POINT_REUSE: { phu: false, qua: true },
  REUSED_INTERSECTION: {},
};
const chuanTen = (s: string) => s.replace(/″/g, "''").replace(/[′’]/g, "'");

/** Structural verification of a Category B (`ENGINE_DERIVED_SECTION`, `plane-section-certificate/1`) section against `scene`. */
function kiemEngineDerivedSection(
  s: Record<string, unknown>,
  obj: SceneObject,
  solid: SceneObject,
  scene: Scene3D,
  diem: (name: string) => SceneObject[],
): string | null {
  if (
    s.certificate_version !== PLANE_SECTION_CERTIFICATE_VERSION
    || s.certificate_category !== ENGINE_DERIVED_SECTION_CATEGORY
    || s.section_object_id !== obj.id
    || s.declared_boundary !== null
    || obj.closed !== true
    || (Array.isArray(obj.identity_diagnostics) && obj.identity_diagnostics.length > 0)
  ) {
    return "chứng chỉ thiết diện dẫn xuất sai dạng";
  }
  const vIds = solid.vertex_ids ?? [];
  const solidVerts = solid.vertices ?? [];
  const faces = solid.faces ?? [];
  if (
    s.solid_object_id !== solid.id
    || typeof s.solid !== "string"
    || typeof solid.notation !== "string"
    || chuanTen(s.solid) !== chuanTen(solid.notation)
    || vIds.length < 4
    || solidVerts.length !== vIds.length
    || faces.length === 0
    || scene.objects.some((o) => o.type === "solid" && o.id !== solid.id && (o.depends ?? []).includes(obj.id))
  ) {
    return "khối của thiết diện dẫn xuất lệch cảnh";
  }
  for (let i = 0; i < vIds.length; i++) {
    const po = scene.objects.find((o) => o.id === vIds[i] && o.type === "point3");
    if (!po || JSON.stringify(po.xyz) !== JSON.stringify(solidVerts[i])) {
      return "đỉnh khối của thiết diện dẫn xuất lệch cảnh";
    }
  }
  const solidEdges = new Set<string>();
  for (const f of faces) {
    if (!Array.isArray(f) || f.length < 3) return "mặt khối sai dạng";
    for (let i = 0; i < f.length; i++) {
      const a = f[i];
      const b = f[(i + 1) % f.length];
      solidEdges.add(`${Math.min(a, b)}-${Math.max(a, b)}`);
    }
  }

  const expectedPlaneId = `mp_td_${s.section_id}`;
  const planeObj = scene.objects.find((o) => o.id === expectedPlaneId && o.type === "plane3");
  if (
    s.plane_object_id !== expectedPlaneId
    || !planeObj
    || !obj.depends.includes(expectedPlaneId)
    || !Array.isArray(s.plane_points)
    || s.plane_points.length !== 3
    || !s.plane_points.every((p) => typeof p === "string" && diem(p).length === 1)
  ) {
    return "mặt cắt của thiết diện dẫn xuất lệch cảnh";
  }
  const planePointIds = new Set(s.plane_points.map((p: string) => diem(p)[0].id));
  const planeDepends = new Set(planeObj.depends ?? []);
  if (
    planePointIds.size !== 3
    || planePointIds.size !== planeDepends.size
    || ![...planePointIds].every((id) => planeDepends.has(id))
  ) {
    return "điểm dựng mặt cắt lệch phụ thuộc cảnh";
  }

  const planeEq = s.plane_equation;
  if (
    !laDoiTuong(planeEq)
    || !Array.isArray(planeEq.normal)
    || planeEq.normal.length !== 3
    || !planeEq.normal.every((c) => typeof c === "string" && RATIONAL_STR_RE.test(c))
    || planeEq.normal.every((c) => c === "0")
    || typeof planeEq.offset !== "string"
    || !RATIONAL_STR_RE.test(planeEq.offset)
  ) {
    return "phương trình mặt cắt dẫn xuất sai dạng";
  }

  const planeRule = s.plane_rule;
  const planeRel = s.plane_relation;
  if (!laDoiTuong(planeRel)) return "quan hệ mặt cắt dẫn xuất sai dạng";
  let tpObj: SceneObject | null = null;
  if (planeRule === "explicit_plane") {
    if (s.through_point !== null || planeRel.kind !== "explicit_points") {
      return "mặt phẳng tường minh không có through_point";
    }
  } else if (typeof planeRule === "string" && DERIVED_PLANE_RULES.has(planeRule)) {
    if (
      typeof s.through_point !== "string"
      || planeRel.through_point !== s.through_point
      || diem(s.through_point).length !== 1
    ) {
      return "điểm đi qua của mặt cắt dẫn xuất sai";
    }
    tpObj = diem(s.through_point)[0];
    if (!planeDepends.has(tpObj.id)) return "điểm đi qua không thuộc mặt cắt";
  } else {
    return "quy tắc mặt cắt dẫn xuất lạ";
  }

  const vertices = s.vertices as unknown[];
  const polygon = obj.polygon ?? [];
  const vSources = obj.vertex_sources ?? [];
  const epEntities = obj.endpoint_entities ?? [];
  if (
    vertices.length < 3
    || vertices.length !== polygon.length
    || vSources.length !== polygon.length
    || epEntities.length !== polygon.length
  ) {
    return "số đỉnh thiết diện dẫn xuất lệch cảnh";
  }

  const seenXyz = new Set<string>();
  const seenEntityIds = new Set<string>();
  const expectedBoundary: string[] = [];

  for (let idx = 0; idx < vertices.length; idx++) {
    const v = vertices[idx];
    const vSrc = vSources[idx] as unknown as Record<string, unknown>;
    const ep = epEntities[idx] as unknown as Record<string, unknown>;
    const polyXyz = polygon[idx];
    if (!laDoiTuong(v) || !laDoiTuong(vSrc) || !laDoiTuong(ep)) return "đỉnh thiết diện dẫn xuất sai dạng";
    const xyzKey = JSON.stringify(polyXyz);
    if (
      v.ordinal !== idx
      || JSON.stringify(v.xyz) !== xyzKey
      || v.stated !== false
      || seenXyz.has(xyzKey)
    ) {
      return "toạ độ hoặc cờ stated của đỉnh thiết diện dẫn xuất sai";
    }
    seenXyz.add(xyzKey);

    const entityId = v.entity_id;
    if (
      typeof entityId !== "string"
      || !entityId
      || seenEntityIds.has(entityId)
      || ep.entity_id !== entityId
      || ep.section_vertex_ordinal !== idx
      || ep.anonymous_coordinate_fallback !== false
    ) {
      return "danh tính endpoint của thiết diện dẫn xuất lệch cảnh";
    }
    seenEntityIds.add(entityId);
    expectedBoundary.push(entityId);

    if (
      !Array.isArray(v.edge)
      || v.edge.length !== 2
      || !v.edge.every((lbl) => typeof lbl === "string" && diem(lbl).length === 1)
      || !Array.isArray(v.solid_edge_vertex_indices)
      || v.solid_edge_vertex_indices.length !== 2
    ) {
      return "cạnh đỡ của đỉnh thiết diện dẫn xuất sai";
    }
    const [ia, ib] = v.solid_edge_vertex_indices;
    if (
      typeof ia !== "number" || typeof ib !== "number"
      || !Number.isInteger(ia) || !Number.isInteger(ib)
      || ia < 0 || ia >= ib || ib >= vIds.length
      || !solidEdges.has(`${ia}-${ib}`)
      || diem(v.edge[0])[0].id !== vIds[ia]
      || diem(v.edge[1])[0].id !== vIds[ib]
    ) {
      return "chỉ số cạnh đỡ của đỉnh thiết diện dẫn xuất lệch khối";
    }

    const srcKind = v.source_kind;
    if (srcKind !== vSrc.kind || ep.provenance_kind !== srcKind) {
      return "source_kind của đỉnh thiết diện dẫn xuất lệch cảnh";
    }
    const isTp = tpObj !== null && JSON.stringify(tpObj.xyz) === xyzKey;
    if (srcKind === "SOLID_VERTEX") {
      const iv = v.solid_vertex_index;
      if (
        typeof iv !== "number"
        || iv !== vSrc.solid_vertex_index
        || (iv !== ia && iv !== ib)
        || JSON.stringify(solidVerts[iv]) !== xyzKey
        || entityId !== vIds[iv]
        || v.label !== vIds[iv]
        || scene.objects.find((o) => o.id === vIds[iv] && o.type === "point3")?.notation == null
        || (isTp
          ? v.choice !== "reuse_through_point" || v.provenance !== "THROUGH_POINT_REUSE"
          : v.choice !== "solid_vertex" || v.provenance !== "SOLID_VERTEX_INTERSECTION")
      ) {
        return "provenance đỉnh khối của thiết diện dẫn xuất sai";
      }
    } else if (srcKind === "SOLID_EDGE_INTERSECTION") {
      const srcPair = vSrc.solid_edge_vertex_indices;
      const expectedEid = `section:${obj.id}:point:on:${solid.id}::edge:${vIds[ia]}-${vIds[ib]}`;
      if (
        v.solid_vertex_index !== null
        || vSrc.solid_vertex_index != null
        || !Array.isArray(srcPair)
        || srcPair.length !== 2
        || Math.min(Number(srcPair[0]), Number(srcPair[1])) !== ia
        || Math.max(Number(srcPair[0]), Number(srcPair[1])) !== ib
        || solidVerts.some((sv) => JSON.stringify(sv) === xyzKey)
        || entityId !== expectedEid
        || (isTp
          ? v.choice !== "reuse_through_point"
            || v.provenance !== "THROUGH_POINT_REUSE"
            || v.label !== tpObj!.id
            || tpObj!.notation == null
          : v.choice !== "engine_derived_edge_cut"
            || v.provenance !== "ENGINE_DERIVED_EDGE_CUT"
            || v.label !== null)
      ) {
        return "provenance giao điểm cạnh của thiết diện dẫn xuất sai";
      }
    } else {
      return "source_kind của thiết diện dẫn xuất không hợp lệ";
    }
  }

  // Cyclic face adjacency across consecutive vertices.
  for (let i = 0; i < vertices.length; i++) {
    const vc = vertices[i] as Record<string, unknown>;
    const vn = vertices[(i + 1) % vertices.length] as Record<string, unknown>;
    const facesContaining = (vx: Record<string, unknown>) =>
      faces.reduce<number[]>((acc, f, fi) => {
        const hit = vx.source_kind === "SOLID_VERTEX"
          ? f.includes(vx.solid_vertex_index as number)
          : (vx.solid_edge_vertex_indices as number[]).every((k) => f.includes(k));
        if (hit) acc.push(fi);
        return acc;
      }, []);
    const fc = facesContaining(vc);
    const fn = new Set(facesContaining(vn));
    if (!fc.some((fi) => fn.has(fi))) return "chu trình đỉnh thiết diện dẫn xuất không kề mặt";
  }

  const cert = s.closure_certificate;
  if (
    JSON.stringify(s.boundary) !== JSON.stringify(expectedBoundary)
    || !laDoiTuong(cert)
    || cert.verified !== true
    || cert.version !== PLANE_SECTION_CERTIFICATE_VERSION
    || cert.rule !== PLANE_SECTION_CERTIFICATE_RULE
    || cert.producer !== PLANE_SECTION_CERTIFICATE_PRODUCER
    || typeof cert.area_squared !== "string"
    || !RATIONAL_STR_RE.test(cert.area_squared)
    || JSON.stringify(cert.boundary) !== JSON.stringify(expectedBoundary)
    || JSON.stringify(cert.polygon) !== JSON.stringify(polygon)
  ) {
    return "chứng chỉ khép kín của thiết diện dẫn xuất lệch";
  }
  return null;
}

/** Malformed scene shapes refuse instead of throwing (the boundary never raises). */
function laMangChuoiKhongRong(x: unknown): x is string[] {
  return Array.isArray(x) && x.every((item) => typeof item === "string" && item.trim().length > 0);
}

/** Phần tử provenance chỉ qua khi đã xác minh (`verified: true`) hoặc mang trích dẫn nguyên văn; `verified: false` ⇒ từ chối. */
function kiemSourceProvenance(raw: unknown): string | null {
  if (!Array.isArray(raw)) return "source_provenance phải là mảng";
  for (const item of raw) {
    if (!laDoiTuong(item)) return "source_provenance có phần tử sai dạng";
    const hasFn = typeof item.fn === "string" && item.fn.trim().length > 0;
    const hasKind = typeof item.kind === "string" && item.kind.trim().length > 0;
    if (!hasFn && !hasKind) return "source_provenance có phần tử thiếu fn/kind hợp lệ";
    if (item.fn !== undefined && !hasFn) return "source_provenance.fn sai dạng";
    if (item.kind !== undefined && !hasKind) return "source_provenance.kind sai dạng";
    if (item.id !== undefined && (typeof item.id !== "string" || !item.id.trim())) return "source_provenance.id sai dạng";
    if (item.args !== undefined && !laDoiTuong(item.args)) return "source_provenance.args sai dạng";
    if (item.quotes !== undefined && (!laMangChuoiKhongRong(item.quotes) || item.quotes.length === 0)) return "source_provenance.quotes sai dạng";
    if (item.fact_id != null && typeof item.fact_id !== "string") return "source_provenance.fact_id sai dạng";
    if (item.verified !== undefined && typeof item.verified !== "boolean") return "source_provenance.verified sai dạng";
    if (item.verified === false) return "source_provenance chưa được xác minh";
    if (item.verified !== true && !(laMangChuoiKhongRong(item.quotes) && item.quotes.length > 0)) {
      return "source_provenance thiếu bằng chứng quotes hoặc cờ verified";
    }
    if (item.polygon != null && (!laMangChuoiKhongRong(item.polygon) || item.polygon.length < 3)) return "source_provenance.polygon sai dạng";
    if (item.edge != null && (!laMangChuoiKhongRong(item.edge) || item.edge.length !== 2)) return "source_provenance.edge sai dạng";
    if (item.points != null && !laMangChuoiKhongRong(item.points)) return "source_provenance.points sai dạng";
    if (item.plane != null && !laMangChuoiKhongRong(item.plane)) return "source_provenance.plane sai dạng";
    if (item.vertex != null && (typeof item.vertex !== "string" || !item.vertex.trim())) return "source_provenance.vertex sai dạng";
    if (item.rays != null && (!Array.isArray(item.rays) || item.rays.some((r) => !laMangChuoiKhongRong(r) || r.length < 2))) {
      return "source_provenance.rays sai dạng";
    }
    if (item.value_display != null && typeof item.value_display !== "string") return "source_provenance.value_display sai dạng";
  }
  return null;
}

const CAC_TANG_CHUNG_CHI_QUAN_HE = ["SOURCE_GROUNDING_PROOF", "GEOMETRIC_RELATION_PROOF", "KERNEL_EXECUTION_PROOF", "RESULT_CERTIFICATE"] as const;

/** Chứng chỉ quan hệ: bản bốn tầng phải đủ cả bốn tầng `verified: true`; bản rút gọn phải `verified: true`. */
function kiemRelationCertificates(raw: unknown): string | null {
  if (!Array.isArray(raw)) return "relation_certificates phải là mảng";
  for (const item of raw) {
    if (!laDoiTuong(item)) return "relation_certificates có phần tử sai dạng";
    const laBonTang = item.schema_version === "geometric-relation-certificate/1"
      || typeof item.relation_kind === "string" || CAC_TANG_CHUNG_CHI_QUAN_HE.some((k) => k in item);
    if (laBonTang) {
      if ((item.schema_version !== undefined && item.schema_version !== "geometric-relation-certificate/1")
        || typeof item.relation_id !== "string" || !item.relation_id.trim()
        || typeof item.relation_kind !== "string" || !item.relation_kind.trim()
        || typeof item.subject_id !== "string" || !item.subject_id.trim()
        || typeof item.target_id !== "string" || !item.target_id.trim()) return "relation_certificates 4 tầng sai dạng";
      for (const layerKey of CAC_TANG_CHUNG_CHI_QUAN_HE) {
        const lp = item[layerKey];
        if (!laDoiTuong(lp) || lp.verified !== true) return `relation_certificates thiếu hoặc chưa kiểm chứng tầng ${layerKey}`;
      }
      continue;
    }
    if (typeof item.kind !== "string" || !item.kind.trim() || item.verified !== true
      || (item.relation_id != null && typeof item.relation_id !== "string")
      || (item.rule != null && typeof item.rule !== "string")
      || (item.details != null && !laDoiTuong(item.details))) return "relation_certificates có phần tử sai dạng hoặc chưa kiểm chứng";
  }
  return null;
}

/** Kiểm cả hai khối provenance tuỳ chọn của Adapter /4 (dùng chung cho biên vận chuyển và biên module). */
function kiemProvenanceAdapter4(src: Record<string, unknown>): string | null {
  if (src.source_provenance !== undefined) {
    const e = kiemSourceProvenance(src.source_provenance);
    if (e) return e;
  }
  if (src.relation_certificates !== undefined) {
    const e = kiemRelationCertificates(src.relation_certificates);
    if (e) return e;
  }
  return null;
}

function kiemSections(sections: unknown, scene: Scene3D): string | null {
  try {
    return kiemSectionsCore(sections, scene);
  } catch {
    return "thiết diện sai dạng";
  }
}

function kiemSectionsCore(sections: unknown, scene: Scene3D): string | null {
  if (!Array.isArray(sections)) return "thiếu provenance thiết diện";
  const ids = new Set<string>();
  const coId = new Set(scene.objects.map((o) => o.id));
  if (scene.objects.some((o) => (o.depends ?? []).some((d) => !coId.has(d)))
    || (scene.formation?.steps ?? []).some((st) => (st.visible_ids ?? []).some((d) => !coId.has(d)))) return "cảnh có phụ thuộc treo";
  const diem = (name: string) => scene.objects.filter((o) => o.type === "point3"
    && (o.id === name || (typeof o.notation === "string" && chuanTen(o.notation) === chuanTen(name))));
  for (const s of sections) {
    if (!laDoiTuong(s) || typeof s.section_id !== "string" || ids.has(s.section_id) || !Array.isArray(s.vertices)) return "thiết diện sai dạng";
    ids.add(s.section_id);
    const obj = scene.objects.find((o) => o.id === `td_${s.section_id}` && o.type === "section");
    if (!obj || !obj.polygon) return "thiết diện không thuộc cảnh";
    const polygon = obj.polygon;
    const solid = scene.objects.find((o) => obj.depends.includes(o.id) && o.type === "solid");
    if (!solid?.vertex_ids || s.vertices.length !== polygon.length) return "đỉnh thiết diện lệch cảnh";
    if (s.certificate_category === ENGINE_DERIVED_SECTION_CATEGORY || "certificate_version" in s || "certificate_category" in s) {
      const catBErr = kiemEngineDerivedSection(s, obj, solid, scene, diem);
      if (catBErr) return catBErr;
      continue;
    }
    const labels = new Set<string>();
    for (const v of s.vertices) {
      const luat = laDoiTuong(v) ? LUAT_NGUON[String(v.provenance)] : undefined;
      // A vertex label is the source name (`A'`); the scene keys points by entity ID (`A_prime`) — resolve, never compare.
      const named = laDoiTuong(v) && typeof v.label === "string" ? diem(v.label) : [];
      if (!laDoiTuong(v) || !luat || typeof v.label !== "string" || labels.has(v.label)
        || typeof v.stated !== "boolean" || (luat.stated !== undefined && v.stated !== luat.stated)
        || !Array.isArray(v.edge) || v.edge.length !== 2 || !v.edge.every((id) => typeof id === "string" && diem(id).length === 1)
        || named.length !== 1 || (v.provenance === "DERIVED_FRESH" && named[0].origin !== "derived")) return "provenance đỉnh thiết diện sai";
      labels.add(v.label);
      const point = named[0];
      const laDiemPhu = point.notation == null && point.role === VAI_DIEM_PHU && !point.display_group?.includes("given");
      if (luat.phu === true && !laDiemPhu) return "điểm suy diễn không được giả làm dữ kiện";
      if (luat.phu === false && point.notation == null) return "điểm suy diễn không được giả làm dữ kiện";
      if (luat.qua && !scene.objects.some((o) => obj.depends.includes(o.id) && o.type !== "solid"
        && (o.depends ?? []).includes(point.id))) return "điểm qua không thuộc mặt cắt";
      const ordinal = polygon.findIndex((p) => JSON.stringify(p) === JSON.stringify(point?.xyz));
      const source = obj.vertex_sources?.[ordinal];
      const edge = v.edge.map((name: string) => diem(name)[0].id);
      const indices = source?.solid_edge_vertex_indices;
      if (ordinal < 0 || !source || (indices
        ? !cungChuTrinh(edge, indices.map((i) => solid.vertex_ids![i]))
        : source.solid_vertex_index == null || !edge.includes(solid.vertex_ids[source.solid_vertex_index]))) return "cạnh nguồn thiết diện lệch cảnh";
    }
    // /4 emits a closure certificate whenever the section closes a derived solid. Without one, the section may be
    // plane-only, so the scene must hold no solid besides the cut one (fail closed; a certificate-less section beside a
    // second solid is refused even if legitimate).
    if (s.boundary === null && s.closure_certificate === null) {
      if (scene.objects.some((o) => o.type === "solid" && o.id !== solid.id)) return "khối dẫn xuất thiếu chứng chỉ khép kín";
      continue;
    }
    if (!Array.isArray(s.boundary) || s.boundary.length < 3 || new Set(s.boundary).size !== s.boundary.length
      || s.boundary.length !== labels.size || !s.boundary.every((id) => labels.has(id))
      || !laDoiTuong(s.closure_certificate) || s.closure_certificate.verified !== true
      || typeof s.closure_certificate.rule !== "string" || !s.closure_certificate.rule || !Array.isArray(s.closure_certificate.boundary)
      || !cungChuTrinh(s.boundary, s.closure_certificate.boundary)) return "chứng chỉ chu trình thiết diện lệch";
    const points = s.boundary.map((label) => { const p = diem(label); return p.length === 1 ? p[0].xyz : undefined; });
    if (points.some((p) => !p) || !cungChuTrinh(points, obj.polygon)) return "chu trình thiết diện lệch cảnh";
  }
  if (scene.objects.filter((o) => o.type === "section").length !== ids.size) return "thiếu thiết diện";
  return null;
}

function kiemClarification(
  rawClar: unknown,
  refusalCode: string,
): { ok: true; view: HybridClarificationView } | { ok: false; reason: string } {
  if (!laDoiTuong(rawClar) || rawClar.schema_version !== HYBRID_CLARIFICATION_SCHEMA) {
    return { ok: false, reason: "clarification sai schema_version" };
  }
  if (typeof rawClar.unresolved_id !== "string" || !rawClar.unresolved_id.trim()) {
    return { ok: false, reason: "clarification thiếu unresolved_id" };
  }
  const kind = rawClar.kind;
  if (typeof kind !== "string" || !(kind in CLARIFICATION_KIND_TO_NLU)) {
    return { ok: false, reason: "clarification có kind lạ" };
  }
  const typedKind = kind as HybridClarificationView["kind"];
  const expectedNlu = CLARIFICATION_KIND_TO_NLU[typedKind];
  if (rawClar.nlu_class !== expectedNlu) {
    return { ok: false, reason: "clarification lệch nlu_class" };
  }
  const expectedCode = typedKind === "unsupported" ? "OUT_OF_SCOPE" : "AMBIGUOUS_FACT";
  if (refusalCode !== expectedCode) {
    return { ok: false, reason: "clarification lệch mã từ chối" };
  }
  if (typeof rawClar.quote !== "string" || !rawClar.quote.trim()) {
    return { ok: false, reason: "clarification thiếu trích dẫn nguyên văn" };
  }
  if (
    !Array.isArray(rawClar.spans)
    || rawClar.spans.length < 1
    || !rawClar.spans.every(
      (sp) =>
        Array.isArray(sp)
        && sp.length === 2
        && typeof sp[0] === "number"
        && typeof sp[1] === "number"
        && Number.isInteger(sp[0])
        && Number.isInteger(sp[1])
        && sp[0] >= 0
        && sp[0] < sp[1],
    )
  ) {
    return { ok: false, reason: "clarification có spans sai dạng" };
  }
  if (typedKind === "unsupported") {
    if (rawClar.question !== null) return { ok: false, reason: "clarification unsupported không được mang câu hỏi" };
  } else if (
    typeof rawClar.question !== "string"
    || !rawClar.question.trim()
    || INTERNAL_LEAK_RE.test(rawClar.question)
  ) {
    return { ok: false, reason: "clarification thiếu câu hỏi làm rõ hoặc chứa mã nội bộ" };
  }
  return {
    ok: true,
    view: {
      kind: typedKind,
      nlu_class: expectedNlu,
      quote: rawClar.quote,
      spans: rawClar.spans.map((sp: number[]) => [sp[0], sp[1]] as [number, number]),
      question: typedKind === "unsupported" ? null : (rawClar.question as string),
    },
  };
}

function nhomKiem(group: unknown): [string, Record<string, unknown>][] | null {
  if (group == null) return [];
  if (!laDoiTuong(group)) return null;
  const ra: [string, Record<string, unknown>][] = [];
  for (const [id, v] of Object.entries(group)) {
    if (!laDoiTuong(v)) return null;
    ra.push([id, v]);
  }
  return ra;
}

/** Giá trị số của đại lượng cảnh, dạng chữ backend phát (`value`) — để đối chiếu với hệ số `answer_exact.coef`. */
function giaTriCanh(scene: Scene3D, id: string): string | null {
  const o = scene.objects.find((x) => x.id === id);
  return o && o.type === "quantity" && o.value != null ? gon(o.value) : null;
}

/**
 * Dựng view từ `route_d` của một envelope PHỤC VỤ; `null` + lý do khi lệch hợp đồng. Mọi đáp số phải nối được với đúng
 * một đại lượng cảnh và khớp giá trị dựng (hệ số tại a = 1); mọi quan sát phải là quan sát (không chứng minh).
 */
export function dungHybridView(routeD: unknown, scene: Scene3D): { view: HybridPreviewView } | { reason: string } {
  if (!laDoiTuong(routeD)) return { reason: "route_d không phải đối tượng" };
  const v4 = routeD.schema_version === HYBRID_SIMULATION_SCHEMA;
  const id = routeD.runtime_identity;
  if (v4) {
    if (routeD.adapter_version !== HYBRID_SIMULATION_ADAPTER || routeD.contract_version !== HYBRID_SIMULATION_CONTRACT
      || routeD.status !== "SERVED" || routeD.refusal !== null || !laDoiTuong(routeD.source_verification)
      || routeD.source_verification.authority !== "registry.kiem_nguon") return { reason: "authority Adapter /4 không hợp lệ" };
    const error = kiemSections(routeD.sections, scene);
    if (error) return { reason: error };
    const provError = kiemProvenanceAdapter4(routeD);
    if (provError) return { reason: provError };
  } else if (!laDoiTuong(id) || id.adapter_version !== HYBRID_PREVIEW_ADAPTER) return { reason: "adapter_version không được hỗ trợ" };

  // §4 — length_unit của route_d phải đúng là length_unit của cảnh (một nguồn).
  if (JSON.stringify(routeD.length_unit ?? null) !== JSON.stringify((v4 ? scene.length_unit?.symbol : scene.length_unit) ?? null)) {
    return { reason: "length_unit của route_d lệch cảnh" };
  }
  const donVi = scene.length_unit?.symbol ?? null;

  const answers: HybridAnswerView[] = [];
  const ans = routeD.answers ?? {};
  const exact = routeD.answer_exact ?? {};
  if (!laDoiTuong(ans) || !laDoiTuong(exact)) return { reason: "answers/answer_exact sai dạng" };
  if (v4 && JSON.stringify(Object.keys(ans).sort()) !== JSON.stringify(Object.keys(exact).sort())) return { reason: "answers/answer_exact lệch" };
  for (const [k, sym] of Object.entries(ans)) {
    const ex = exact[k];
    if (typeof sym !== "string" || !sym.trim() || !laDoiTuong(ex)) return { reason: `đáp số ${k} thiếu dạng chính xác` };
    const dim = ex.dim;
    if (ex.unit != null && typeof ex.unit !== "string") return { reason: `đáp số ${k}: đơn vị sai dạng` };
    const unit: string | null = ex.unit ?? null;
    if (typeof dim !== "number" || !Number.isInteger(dim) || dim < 0) return { reason: `đáp số ${k}: bậc không hợp lệ` };
    if (dim > 0 ? unit !== donVi || donVi == null : unit !== null && unit !== donVi) {
      return { reason: `đáp số ${k}: đơn vị lệch length_unit` };
    }
    const qid = `kq_${k}`;
    const giaTri = giaTriCanh(scene, qid);
    // Hình dựng ở a = 1 ⇒ giá trị trên cảnh = hệ số. Lệch ⇒ đáp số không thuộc cảnh này.
    if (giaTri == null || giaTri !== gon(ex.coef)) return { reason: `đáp số ${k} không khớp đại lượng ${qid} của cảnh` };
    answers.push({ quantity_id: qid, coefficient: giaTri, symbolic: sym, dim, unit });
  }

  const planner = routeD.planner;
  if (!laDoiTuong(planner)) return { reason: "planner thiếu" };
  const trace = Array.isArray(planner.trace) ? planner.trace : [];
  const fnCua = (k: string): string | null => {
    const t = trace.find((x) => laDoiTuong(x) && x.call === k);
    return t && laDoiTuong(t) && typeof t.fn === "string" ? t.fn : null;
  };
  const buocCuoi = Math.max(0, ...scene.events.map((e) => e.step_index));
  const observations: HybridObservationView[] = [];
  for (const [group, khoa] of [["goal", "goal_checks"], ["negated", "negated_checks"]] as const) {
    const nhom = nhomKiem(planner[khoa]);
    if (nhom == null) return { reason: `${khoa} sai dạng` };
    for (const [k, c] of nhom) {
      // §3: phiên bản này không có chứng minh — mọi giá trị khác là lệch hợp đồng, không phải "đã chứng minh".
      if (c.can_present_as_proven !== false || c.proof_status !== "UNVERIFIABLE") {
        return { reason: `quan sát ${k} tự xưng chứng minh` };
      }
      if (typeof c.evidence_state !== "string" || !TRANG_THAI.has(c.evidence_state)) {
        return { reason: `quan sát ${k}: evidence_state lạ` };
      }
      const fn = fnCua(k);
      observations.push({
        check_id: k, group,
        relation: (fn && TEN_QUAN_HE[fn]) ?? TEN_QUAN_HE_CHUNG,
        evidence_state: c.evidence_state as HybridEvidenceState,
        anchor_step: buocCuoi,
      });
    }
  }
  return { view: { adapter_version: v4 ? HYBRID_SIMULATION_ADAPTER : HYBRID_PREVIEW_ADAPTER, answers, observations,
    ...(v4 ? { sections: structuredClone(routeD.sections) as HybridSectionView[] } : {}),
    ...(v4 && routeD.source_provenance !== undefined
      ? { source_provenance: structuredClone(routeD.source_provenance) as HybridSourceProvenanceEntry[] } : {}),
    ...(v4 && routeD.relation_certificates !== undefined
      ? { relation_certificates: structuredClone(routeD.relation_certificates) as HybridRelationCertificateEntry[] } : {}) } };
}

/**
 * Phản hồi preview → envelope cho `store.loadEnvelope`. Envelope phục vụ mang thêm `hybrid_preview` (view đã kiểm);
 * envelope từ chối giữ nguyên (và gắn `clarification` đã kiểm khi có bản ghi `route-d-clarification/1`). Phản hồi cổng HTTP (không envelope) ⇒ lỗi.
 */
export function docPhanHoiHybrid(raw: unknown): KetQuaPhanHoiHybrid {
  if (!laDoiTuong(raw) || (raw.schema_version !== HYBRID_PREVIEW_SCHEMA && raw.schema_version !== HYBRID_SIMULATION_SCHEMA)) return { ok: false, reason: "schema_version lạ" };
  const v4 = raw.schema_version === HYBRID_SIMULATION_SCHEMA;
  if (!v4 && laDoiTuong(raw.route_d) && raw.route_d.schema_version === HYBRID_SIMULATION_SCHEMA) return { ok: false, reason: "wrapper/route_d khác phiên bản" };
  if (v4 && (!laDoiTuong(raw.route_d) || raw.route_d.schema_version !== HYBRID_SIMULATION_SCHEMA
    || raw.route_d.adapter_version !== HYBRID_SIMULATION_ADAPTER || raw.route_d.contract_version !== HYBRID_SIMULATION_CONTRACT)) return { ok: false, reason: "identity Adapter /4 lệch" };
  const envelope = raw.envelope;
  if (!laDoiTuong(envelope)) return { ok: false, reason: "phản hồi không có envelope (phản hồi cổng operator)" };
  if (KHOA_HYBRID_VIEW in envelope) return { ok: false, reason: "envelope backend không được tự mang hybrid_preview" };
  if ("clarification" in envelope) return { ok: false, reason: "envelope backend không được tự mang clarification" };
  if (envelope.status !== "ok") {
    if (v4) {
      if (!laDoiTuong(raw.route_d) || raw.route_d.status !== "REFUSED" || !laDoiTuong(raw.route_d.refusal)
        || typeof raw.route_d.refusal.code !== "string" || raw.route_d.refusal.code !== envelope.reason_code
        || envelope.scene3d != null || envelope.simulation_id != null) {
        return { ok: false, reason: "từ chối Adapter /4 lệch" };
      }
      if ("clarification" in raw.route_d.refusal && raw.route_d.refusal.clarification !== undefined) {
        const clar = kiemClarification(raw.route_d.refusal.clarification, raw.route_d.refusal.code);
        if (!clar.ok) return clar;
        return { ok: true, envelope: { ...envelope, clarification: clar.view } };
      }
    }
    return { ok: true, envelope: { ...envelope } };
  }
  const scene = envelope.scene3d as Scene3D | undefined;
  if (!laDoiTuong(scene) || !Array.isArray(scene.objects) || !Array.isArray(scene.events)) {
    return { ok: false, reason: "envelope phục vụ thiếu scene3d" };
  }
  if (scene.objects.some((o) => !laDoiTuong(o)) || scene.events.some((e) => !laDoiTuong(e))) {
    return { ok: false, reason: "scene3d có đối tượng hoặc sự kiện sai dạng" };
  }
  const r = dungHybridView(raw.route_d, scene);
  if ("reason" in r) return { ok: false, reason: r.reason };
  return { ok: true, envelope: { ...envelope, [KHOA_HYBRID_VIEW]: r.view } };
}

/**
 * Kiểm lại view ở biên module (`validateEnvelope`): view chỉ được trỏ vào vật/bước CÓ trong chính cảnh. `null` = hợp lệ.
 * Không dựng lại từ `route_d` (đã bỏ ở biên vận chuyển) — chỉ kiểm tính nhất quán với cảnh.
 */
export function kiemHybridView(view: unknown, scene: Scene3D | undefined): string | null {
  if (!laDoiTuong(view) || (view.adapter_version !== HYBRID_PREVIEW_ADAPTER && view.adapter_version !== HYBRID_SIMULATION_ADAPTER)) return "hybrid_preview lạ";
  if (!scene) return "hybrid_preview cần scene3d";
  if (view.adapter_version === HYBRID_SIMULATION_ADAPTER) {
    const error = kiemSections(view.sections, scene);
    if (error) return error;
    const provError = kiemProvenanceAdapter4(view);
    if (provError) return provError;
  }
  if (!Array.isArray(view.answers) || !Array.isArray(view.observations)) return "hybrid_preview sai dạng";
  const daCo = new Set<string>();
  for (const a of view.answers) {
    // Cùng ràng buộc như lúc dựng (`dungHybridView`): không tin một view tự đến (review của run, M3).
    if (!laDoiTuong(a) || typeof a.symbolic !== "string" || !a.symbolic.trim()
      || typeof a.dim !== "number" || !Number.isInteger(a.dim) || a.dim < 0
      || (a.dim > 0 ? a.unit !== (scene.length_unit?.symbol ?? null) || a.unit == null : a.unit !== null && a.unit !== scene.length_unit?.symbol)
      || daCo.has(String(a.quantity_id)) || giaTriCanh(scene, String(a.quantity_id)) == null) {
      return "đáp số trỏ vào đại lượng không có trong cảnh hoặc sai dạng";
    }
    daCo.add(String(a.quantity_id));
    if (a.coefficient !== undefined && (typeof a.coefficient !== "string"
      || gon(a.coefficient) !== giaTriCanh(scene, String(a.quantity_id)))) {
      return "hệ số đáp số không khớp đại lượng của cảnh";
    }
  }
  const buocCuoi = Math.max(0, ...scene.events.map((e) => e.step_index));
  for (const o of view.observations) {
    if (!laDoiTuong(o) || !TRANG_THAI.has(String(o.evidence_state)) || o.anchor_step !== buocCuoi
      || (o.group !== "goal" && o.group !== "negated") || !TEN_HOP_LE.has(String(o.relation))) {
      return "quan sát neo vào bước không có trong cảnh hoặc sai dạng";
    }
  }
  return null;
}

/** View đã kiểm của envelope đang hoạt động, hoặc `null` (envelope LLM_ONLY không bao giờ có). */
export function hybridViewCua(envelope: unknown): HybridPreviewView | null {
  const v = laDoiTuong(envelope) ? envelope[KHOA_HYBRID_VIEW] : null;
  return laDoiTuong(v) && (v.adapter_version === HYBRID_PREVIEW_ADAPTER || v.adapter_version === HYBRID_SIMULATION_ADAPTER) ? (v as unknown as HybridPreviewView) : null;
}

/**
 * Thứ được hiện ở bước `buoc` — MỘT luật cho timeline: đáp số từ bước đo đại lượng của nó, quan sát từ bước neo.
 * Không kết luận nào đứng trước bước chống đỡ nó.
 */
export function hybridTaiBuoc(
  view: HybridPreviewView | null | undefined, scene: Pick<Scene3D, "events">, buoc: number,
): { answers: HybridAnswerView[]; observations: HybridObservationView[] } {
  if (!view) return { answers: [], observations: [] };
  return {
    answers: view.answers.filter((a) => scene.events.some((e) => e.object === a.quantity_id && e.step_index <= buoc)),
    observations: view.observations.filter((o) => buoc >= o.anchor_step),
  };
}

/** Giá trị của đáp số dạng chữ — `answers` của góc đã mang ký hiệu ("cos²=1/4"): bỏ vế trái để không lặp ký hiệu
 *  của đại lượng ("cos²(SA, (ABC)) = 1/4", không phải "… = cos²=1/4"; review của run, M1). */
export function giaTriDapSo(a: HybridAnswerView): string {
  return a.symbolic.includes("=") ? a.symbolic.slice(a.symbolic.lastIndexOf("=") + 1).trim() : a.symbolic;
}

/** Câu trình bày MỘT quan sát (§3): luôn nói đây là quan sát trên một hình, không phải chứng minh tổng quát. */
export function cauQuanSat(o: HybridObservationView): string {
  const tt = o.evidence_state === "TRUE_ON_CONFIGURATION" ? "trên hình đã dựng, điều này đúng"
    : o.evidence_state === "FALSE_ON_CONFIGURATION" ? "trên hình đã dựng, điều này không đúng"
    : "chưa kiểm được trên hình đã dựng";
  const dau = o.relation.charAt(0).toUpperCase() + o.relation.slice(1);
  return `${dau} (${o.group === "goal" ? "điều đề yêu cầu" : "mệnh đề phủ định của đề"}): ${tt} — đây là quan sát trên một hình, không phải chứng minh tổng quát.`;
}
