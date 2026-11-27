import {
  recoverCachedCatalogScene3D,
  resolveGeometrySampleIdMeta as resolveGeometrySampleId,
  resolveSampleMetaByRouteToken as resolveSampleByRouteToken,
  sampleMetaById,
} from "../data/sample-catalog-meta";
import type { Scene3D, SceneObject } from "../simulations/domains/geometry/scene3d-model";
import type { SimulationEnvelope } from "../simulations/types";

export type GeometrySolidFamily =
  | "pyramid"
  | "cube"
  | "prism"
  | "sphere"
  | "cylinder"
  | "cone"
  | "neutral";

export const GEOMETRY_SOLID_FAMILIES: readonly GeometrySolidFamily[] = Object.freeze([
  "pyramid",
  "cube",
  "prism",
  "sphere",
  "cylinder",
  "cone",
  "neutral",
]);

export const GEOMETRY_FAMILY_LABELS: Readonly<Record<GeometrySolidFamily, string>> =
  Object.freeze({
    pyramid: "Hình chóp",
    cube: "Hình lập phương",
    prism: "Hình lăng trụ",
    sphere: "Mặt cầu",
    cylinder: "Hình trụ",
    cone: "Hình nón",
    neutral: "Không gian Oxyz",
  });

export interface ResolveGeometrySolidFamilyInput {
  readonly envelope?: unknown;
  readonly sampleId?: string | null;
  readonly problemStatement?: string | null;
  readonly title?: string | null;
}

function parseExactNumber(raw: unknown): number | null {
  if (typeof raw === "number") {
    return Number.isFinite(raw) ? raw : null;
  }
  if (typeof raw !== "string") return null;
  const trimmed = raw.trim();
  if (!trimmed) return null;
  if (trimmed.includes("/")) {
    const parts = trimmed.split("/");
    if (parts.length !== 2) return null;
    const num = Number(parts[0]?.trim());
    const den = Number(parts[1]?.trim());
    if (!Number.isFinite(num) || !Number.isFinite(den) || Math.abs(den) < 1e-12) {
      return null;
    }
    return num / den;
  }
  const parsed = Number(trimmed);
  return Number.isFinite(parsed) ? parsed : null;
}

function parseVec3(raw: unknown): [number, number, number] | null {
  if (!Array.isArray(raw) || raw.length !== 3) return null;
  const x = parseExactNumber(raw[0]);
  const y = parseExactNumber(raw[1]);
  const z = parseExactNumber(raw[2]);
  if (x === null || y === null || z === null) return null;
  return [x, y, z];
}

function parseMetricMatrix(chartMetric: unknown): number[][] | null {
  if (!Array.isArray(chartMetric) || chartMetric.length !== 3) return null;
  const rows: number[][] = [];
  for (const r of chartMetric) {
    if (!Array.isArray(r) || r.length !== 3) return null;
    const row: number[] = [];
    for (const cell of r) {
      const val = parseExactNumber(cell);
      if (val === null) return null;
      row.push(val);
    }
    rows.push(row);
  }
  return rows;
}

function metricDot(
  u: [number, number, number],
  v: [number, number, number],
  metric: number[][] | null,
): number {
  if (!metric) {
    return u[0] * v[0] + u[1] * v[1] + u[2] * v[2];
  }
  let sum = 0;
  for (let i = 0; i < 3; i += 1) {
    for (let j = 0; j < 3; j += 1) {
      sum += u[i]! * (metric[i]?.[j] ?? (i === j ? 1 : 0)) * v[j]!;
    }
  }
  return sum;
}

/**
 * Kiểm tra tất định một khối đa diện 8 đỉnh, 6 mặt tứ giác có phải là hình lập phương
 * (tất cả các cạnh của 6 mặt có độ dài dương bằng nhau và các cạnh kề vuông góc) hay không.
 */
function isEqualEdgeOrthogonalHexahedron(
  verticesRaw: unknown,
  facesRaw: unknown,
  chartMetric?: unknown,
): boolean {
  if (!Array.isArray(verticesRaw) || verticesRaw.length !== 8) return false;
  if (!Array.isArray(facesRaw) || facesRaw.length !== 6) return false;

  const pts: [number, number, number][] = [];
  for (const v of verticesRaw) {
    const parsed = parseVec3(v);
    if (!parsed) return false;
    pts.push(parsed);
  }

  const metric = parseMetricMatrix(chartMetric);
  let refEdgeSq: number | null = null;

  for (const face of facesRaw) {
    if (!Array.isArray(face) || face.length !== 4) return false;
    const idx0 = face[0];
    const idx1 = face[1];
    const idx2 = face[2];
    const idx3 = face[3];
    if (
      typeof idx0 !== "number" ||
      typeof idx1 !== "number" ||
      typeof idx2 !== "number" ||
      typeof idx3 !== "number"
    ) {
      return false;
    }
    const p0 = pts[idx0];
    const p1 = pts[idx1];
    const p2 = pts[idx2];
    const p3 = pts[idx3];
    if (!p0 || !p1 || !p2 || !p3) return false;

    const facePts = [p0, p1, p2, p3];
    const edgeVecs: [number, number, number][] = [];
    for (let i = 0; i < 4; i += 1) {
      const a = facePts[i]!;
      const b = facePts[(i + 1) % 4]!;
      const vec: [number, number, number] = [b[0] - a[0], b[1] - a[1], b[2] - a[2]];
      const lenSq = metricDot(vec, vec, metric);
      if (!(lenSq > 1e-9)) return false;
      if (refEdgeSq === null) {
        refEdgeSq = lenSq;
      } else if (Math.abs(lenSq - refEdgeSq) > 1e-4 * refEdgeSq) {
        return false;
      }
      edgeVecs.push(vec);
    }

    for (let i = 0; i < 4; i += 1) {
      const e1 = edgeVecs[i]!;
      const e2 = edgeVecs[(i + 1) % 4]!;
      const dot = Math.abs(metricDot(e1, e2, metric));
      if (refEdgeSq !== null && dot > 1e-4 * refEdgeSq) {
        return false;
      }
    }
  }

  return refEdgeSq !== null && refEdgeSq > 0;
}

function classifyExplicitKindTag(tagRaw: unknown): GeometrySolidFamily | null {
  if (typeof tagRaw !== "string") return null;
  const tag = tagRaw.trim().toLowerCase();
  if (!tag) return null;
  if (
    tag === "cube" ||
    tag === "lap_phuong" ||
    tag === "lap-phuong" ||
    tag === "hinh_lap_phuong" ||
    tag === "regular_hexahedron"
  ) {
    return "cube";
  }
  if (
    tag === "prism" ||
    tag === "lang_tru" ||
    tag === "lang-tru" ||
    tag === "box" ||
    tag === "hinh_hop" ||
    tag === "parallelepiped"
  ) {
    return "prism";
  }
  if (
    tag === "pyramid" ||
    tag === "chop" ||
    tag === "hinh_chop" ||
    tag === "tetrahedron" ||
    tag === "tu_dien"
  ) {
    return "pyramid";
  }
  if (tag === "sphere" || tag === "ball" || tag === "mat_cau" || tag === "cau") {
    return "sphere";
  }
  if (tag === "cylinder" || tag === "tru" || tag === "hinh_tru") {
    return "cylinder";
  }
  if (tag === "cone" || tag === "non" || tag === "hinh_non") {
    return "cone";
  }
  if (tag === "neutral" || tag === "oxyz") {
    return "neutral";
  }
  return null;
}

function classifyPolyhedronObject(
  obj: Partial<SceneObject> & Record<string, unknown>,
  chartMetric?: unknown,
): GeometrySolidFamily | null {
  const explicit =
    classifyExplicitKindTag(obj.solid_kind) ??
    classifyExplicitKindTag(obj.family) ??
    classifyExplicitKindTag(obj.id);
  if (explicit && explicit !== "neutral") {
    return explicit;
  }

  const labelAndId = `${obj.id ?? ""} ${obj.label ?? ""} ${obj.notation ?? ""}`.toLowerCase();
  if (
    labelAndId.includes("lap_phuong") ||
    labelAndId.includes("lập phương") ||
    labelAndId.includes("cube")
  ) {
    return "cube";
  }

  const vertices = Array.isArray(obj.vertices) ? obj.vertices : [];
  const faces = Array.isArray(obj.faces) ? obj.faces : [];
  const vCount = vertices.length;
  const fCount = faces.length;

  // Khối 6 mặt tứ giác, 8 đỉnh (hexahedron): kiểm tra tọa độ cạnh bằng nhau + vuông góc để tách "cube" khỏi "prism"
  if (
    vCount === 8 &&
    fCount === 6 &&
    faces.every((f) => Array.isArray(f) && f.length === 4)
  ) {
    if (isEqualEdgeOrthogonalHexahedron(vertices, faces, chartMetric)) {
      return "cube";
    }
    return "prism";
  }

  if (obj.shape_class === "PRISM_LIKE") {
    return "prism";
  }
  if (obj.shape_class === "PYRAMID_LIKE") {
    return "pyramid";
  }

  // Topology hình chóp / tứ diện: N đỉnh (N >= 4), N mặt, trong đó ít nhất N-1 mặt tam giác và 1 mặt đáy (N-1) cạnh
  if (vCount >= 4 && fCount === vCount) {
    const triFaces = faces.filter((f) => Array.isArray(f) && f.length === 3).length;
    const baseFaces = faces.filter(
      (f) => Array.isArray(f) && f.length === vCount - 1,
    ).length;
    if (triFaces >= fCount - 1 && baseFaces >= 1) {
      return "pyramid";
    }
  }

  // Topology hình lăng trụ N-giác (N >= 3): 2N đỉnh, N + 2 mặt (N mặt bên tứ giác, 2 mặt đáy N-giác)
  if (vCount >= 6 && vCount % 2 === 0) {
    const nGon = vCount / 2;
    if (fCount === nGon + 2) {
      const quadFaces = faces.filter((f) => Array.isArray(f) && f.length === 4).length;
      if (quadFaces >= nGon) {
        return "prism";
      }
    }
  }

  if (
    labelAndId.includes("lăng trụ") ||
    labelAndId.includes("lang_tru") ||
    labelAndId.includes("hình hộp")
  ) {
    return "prism";
  }
  if (
    labelAndId.includes("hình chóp") ||
    labelAndId.includes("khối chóp") ||
    labelAndId.includes("tứ diện") ||
    /\bs\.[a-z]{3,6}\b/i.test(labelAndId)
  ) {
    return "pyramid";
  }

  return null;
}

function classifyCurvedObject(
  obj: Partial<SceneObject> & Record<string, unknown>,
): GeometrySolidFamily | null {
  const ck = typeof obj.curved_kind === "string" ? obj.curved_kind.trim().toLowerCase() : "";
  if (ck === "ball" || ck === "sphere") return "sphere";
  if (ck === "cylinder") return "cylinder";
  if (ck === "cone") return "cone";

  const semRole = typeof obj.semantic_role === "string" ? obj.semantic_role : "";
  if (
    semRole === "STANDALONE_SPHERE" ||
    semRole === "CIRCUMSCRIBED_SPHERE" ||
    semRole === "INSCRIBED_SPHERE"
  ) {
    return "sphere";
  }

  if ("apex" in obj && obj.apex != null) return "cone";
  if (("axis" in obj && obj.axis != null) || ("bottom_center" in obj && obj.bottom_center != null)) {
    return "cylinder";
  }
  if ("anchor" in obj && obj.anchor != null && "radius_sq" in obj && obj.radius_sq != null) {
    return "sphere";
  }
  return null;
}

function classifyFromScene3D(sceneRaw: unknown): GeometrySolidFamily | null {
  if (!sceneRaw || typeof sceneRaw !== "object") return null;
  const scene = sceneRaw as Partial<Scene3D> & Record<string, unknown>;
  const explicitSceneFamily =
    classifyExplicitKindTag(scene.solid_kind) ?? classifyExplicitKindTag(scene.family);
  if (explicitSceneFamily) return explicitSceneFamily;

  const objects = Array.isArray(scene.objects) ? scene.objects : [];
  if (objects.length === 0) return null;

  // 1. Ưu tiên khối đa diện chính (polyhedron solid mesh) trước mặt cầu ngoại/nội tiếp đi kèm
  const solidMeshes = objects.filter((o) => {
    if (!o || typeof o !== "object") return false;
    const rec = o as Partial<SceneObject>;
    return (
      rec.type === "solid" ||
      rec.render === "mesh" ||
      rec.semantic_role === "SOLID_SHELL"
    );
  });

  for (const mesh of solidMeshes) {
    const matched = classifyPolyhedronObject(
      mesh as Partial<SceneObject> & Record<string, unknown>,
      scene.chart_metric,
    );
    if (matched) return matched;
  }

  // 2. Khối tròn xoay / mặt cong (ball, cylinder, cone)
  const curvedSolids = objects.filter((o) => {
    if (!o || typeof o !== "object") return false;
    const rec = o as Partial<SceneObject>;
    return (
      rec.type === "curved_solid" ||
      rec.render === "curved_solid" ||
      typeof rec.curved_kind === "string"
    );
  });

  for (const curved of curvedSolids) {
    const matched = classifyCurvedObject(
      curved as Partial<SceneObject> & Record<string, unknown>,
    );
    if (matched) return matched;
  }

  return null;
}

function classifyFromSampleToken(sampleIdRaw: string | null | undefined): GeometrySolidFamily | null {
  if (!sampleIdRaw) return null;
  const trimmed = sampleIdRaw.trim();
  if (!trimmed) return null;
  const lower = trimmed.toLowerCase();

  // Bí danh kiểm thử hoặc định danh mẫu cụ thể
  if (
    lower === "thiet-dien-lap-phuong" ||
    lower === "lap-phuong-thiet-dien-bat-ky" ||
    lower === "cube-hexagonal-plane-section" ||
    lower.includes("lap-phuong") ||
    lower.includes("lap_phuong") ||
    lower.includes("cube")
  ) {
    return "cube";
  }

  const metaEntry = resolveSampleByRouteToken(trimmed) ?? sampleMetaById(trimmed);
  if (metaEntry) {
    return metaEntry.solidFamily;
  }

  if (lower.startsWith("oxyz-") || lower.includes("oxyz")) return "neutral";
  if (
    lower.includes("lang-tru") ||
    lower.includes("lang_tru") ||
    lower.includes("prism") ||
    lower.includes("hinh-hop")
  ) {
    return "prism";
  }
  if (
    (lower.startsWith("cau-") ||
      lower.startsWith("mat-cau") ||
      lower.includes("mat-cau") ||
      lower.includes("sphere")) &&
    !lower.startsWith("chop-") &&
    !lower.startsWith("pyramid-")
  ) {
    return "sphere";
  }
  if (
    (lower.startsWith("tru-") ||
      lower.startsWith("hinh-tru") ||
      lower.includes("cylinder")) &&
    !lower.includes("lang-tru")
  ) {
    return "cylinder";
  }
  if (
    lower.startsWith("non-") ||
    lower.startsWith("hinh-non") ||
    lower.includes("cone")
  ) {
    return "cone";
  }
  if (
    lower.startsWith("chop-") ||
    lower.includes("-chop") ||
    lower.startsWith("pyramid-") ||
    lower.includes("tu-dien") ||
    lower.includes("tetrahedron")
  ) {
    return "pyramid";
  }

  return null;
}

function classifyFromTextWording(rawText: string): GeometrySolidFamily | null {
  const norm = rawText.normalize("NFC").toLowerCase().replace(/\s+/g, " ").trim();
  if (!norm) return null;

  // 1. Hình lập phương phải tách biệt hoàn toàn với lăng trụ thường
  if (
    norm.includes("hình lập phương") ||
    norm.includes("khối lập phương") ||
    norm.includes("lập phương") ||
    norm.includes("lap phuong")
  ) {
    return "cube";
  }

  // 2. Hình lăng trụ / hình hộp (kiểm tra trước "hình trụ" vì có chữ "trụ")
  if (
    norm.includes("lăng trụ") ||
    norm.includes("lang tru") ||
    norm.includes("hình hộp") ||
    norm.includes("khối hộp") ||
    /\b[a-z]{3,6}\.[a-z][′'][a-z][′'][a-z][′']/.test(norm)
  ) {
    return "prism";
  }

  // 3. Hình trụ tròn xoay
  if (
    norm.includes("hình trụ") ||
    norm.includes("khối trụ") ||
    norm.includes("mặt trụ") ||
    norm.includes("hinh tru") ||
    norm.includes("khoi tru")
  ) {
    return "cylinder";
  }

  // 4. Hình nón tròn xoay
  if (
    norm.includes("hình nón") ||
    norm.includes("khối nón") ||
    norm.includes("mặt nón") ||
    norm.includes("hinh non") ||
    norm.includes("khoi non")
  ) {
    return "cone";
  }

  // 5. Hình chóp / tứ diện (ưu tiên trước mặt cầu ngoại/nội tiếp của hình chóp; KHÔNG BAO GIỜ suy từ "thiết diện")
  if (
    norm.includes("hình chóp") ||
    norm.includes("khối chóp") ||
    norm.includes("tứ diện") ||
    norm.includes("hinh chop") ||
    norm.includes("khoi chop") ||
    norm.includes("tu dien") ||
    /\bs\.[a-z]{3,6}\b/i.test(norm)
  ) {
    return "pyramid";
  }

  // 6. Mặt cầu / khối cầu độc lập
  if (
    norm.includes("mặt cầu") ||
    norm.includes("khối cầu") ||
    norm.includes("hình cầu") ||
    norm.includes("mat cau") ||
    norm.includes("khoi cau")
  ) {
    return "sphere";
  }

  return null;
}

function classifyFromEnvelopeObject(envRaw: unknown): GeometrySolidFamily | null {
  if (!envRaw || typeof envRaw !== "object") return null;
  const env = envRaw as Partial<SimulationEnvelope> & Record<string, unknown>;

  const directTag =
    classifyExplicitKindTag(env.solid_kind) ?? classifyExplicitKindTag(env.family);
  if (directTag) return directTag;

  const config =
    env.config && typeof env.config === "object"
      ? (env.config as Record<string, unknown>)
      : null;
  if (config) {
    const configTag =
      classifyExplicitKindTag(config.solid_kind) ??
      classifyExplicitKindTag(config.family) ??
      classifyExplicitKindTag(config.curved_kind);
    if (configTag) return configTag;
  }

  let scene3d = env.scene3d;
  if (
    (!scene3d || typeof scene3d !== "object") &&
    typeof env.simulation_id === "string" &&
    env.config !== undefined
  ) {
    try {
      const recovered = recoverCachedCatalogScene3D(env as SimulationEnvelope) as {
        scene3d?: unknown;
      };
      scene3d = recovered.scene3d;
    } catch {
      /* bỏ qua nếu không khôi phục được từ catalog */
    }
  }

  if (scene3d && typeof scene3d === "object") {
    const fromScene = classifyFromScene3D(scene3d);
    if (fromScene) return fromScene;
    // Nếu scene3d hợp lệ, có objects nhưng không có bất kỳ khối đa diện hay khối tròn xoay nào (vd bài tọa độ Oxyz thuần túy)
    const objs = (scene3d as { objects?: unknown }).objects;
    if (Array.isArray(objs) && objs.length > 0) {
      const textFromEnv = [
        typeof config?.title === "string" ? config.title : "",
        typeof env.title === "string" ? env.title : "",
        typeof env.problem_statement === "string" ? env.problem_statement : "",
        typeof env.description === "string" ? env.description : "",
      ].join(" ");
      return classifyFromTextWording(textFromEnv) ?? "neutral";
    }
  }

  if (typeof env.simulation_id === "string" && env.config !== undefined) {
    const matchedSampleId = resolveGeometrySampleId({
      envelope: env as SimulationEnvelope,
    });
    if (matchedSampleId) {
      const matchedMeta = sampleMetaById(matchedSampleId);
      if (matchedMeta) return matchedMeta.solidFamily;
    }
  }

  if (config && Array.isArray(config.frames)) {
    const frameNarrations = config.frames
      .map((f) =>
        f && typeof f === "object" && typeof (f as { narration?: unknown }).narration === "string"
          ? (f as { narration: string }).narration
          : "",
      )
      .join(" ");
    const fromFrames = classifyFromTextWording(frameNarrations);
    if (fromFrames) return fromFrames;
  }

  const envText = [
    typeof config?.title === "string" ? config.title : "",
    typeof env.title === "string" ? env.title : "",
    typeof env.problem_statement === "string" ? env.problem_statement : "",
    typeof env.description === "string" ? env.description : "",
  ].join(" ");
  return classifyFromTextWording(envText);
}

/**
 * Phân loại tất định họ khối hình học (`GeometrySolidFamily`) từ dữ liệu thật của bài toán:
 * 1. Ưu tiên tuyệt đối `envelope` / `scene3d` / `config` (topology đa diện + tọa độ cạnh bằng nhau cho lập phương, `curved_kind` cho cầu/trụ/nón).
 * 2. Tiếp theo là `sampleId` / `slug` trong danh mục mẫu đã kiểm chứng.
 * 3. Khi chưa có `envelope` (vd bản ghi đang xử lý / cần chú ý), xét từ khóa hình học tường minh trong `problemStatement` và `title`.
 * 4. Tuyệt đối KHÔNG phân loại "thiết diện" thành `"pyramid"` và KHÔNG fallback mặc định về `"pyramid"`; mặc định khi chưa xác định là `"neutral"`.
 */
export function resolveGeometrySolidFamily(
  input: ResolveGeometrySolidFamilyInput | null | undefined,
): GeometrySolidFamily {
  if (!input) return "neutral";

  if (input.envelope !== undefined && input.envelope !== null) {
    const fromEnvelope = classifyFromEnvelopeObject(input.envelope);
    if (fromEnvelope) return fromEnvelope;
  }

  if (input.sampleId) {
    const fromSample = classifyFromSampleToken(input.sampleId);
    if (fromSample) return fromSample;
  }

  if (input.problemStatement) {
    const fromStatement = classifyFromTextWording(input.problemStatement);
    if (fromStatement) return fromStatement;
  }

  if (input.title) {
    const fromTitle = classifyFromTextWording(input.title);
    if (fromTitle) return fromTitle;
  }

  return "neutral";
}

export interface GeometryFamilyIconProps {
  readonly family: GeometrySolidFamily;
  readonly size?: number;
  readonly className?: string;
}

/**
 * Bộ icon SVG đơn sắc nét mảnh (`strokeWidth="1.5"`) rõ ràng ở kích thước 16–18px
 * cho 7 họ khối hình học: `pyramid`, `cube`, `prism`, `sphere`, `cylinder`, `cone`, `neutral`.
 */
export function GeometryFamilyIcon({
  family,
  size = 16,
  className,
}: GeometryFamilyIconProps) {
  const combinedClassName = className
    ? `axo-geo-family-icon is-${family} ${className}`
    : `axo-geo-family-icon is-${family}`;

  switch (family) {
    case "pyramid":
      return (
        <svg
          className={combinedClassName}
          data-geometry-icon="pyramid"
          width={size}
          height={size}
          viewBox="0 0 16 16"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d="M8 2L2.3 11.8 8 14l5.7-2.2L8 2Z" />
          <path d="M8 2v12" />
        </svg>
      );

    case "cube":
      return (
        <svg
          className={combinedClassName}
          data-geometry-icon="cube"
          width={size}
          height={size}
          viewBox="0 0 16 16"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d="M8 2L13.2 5v6L8 14 2.8 11V5L8 2Z" />
          <path d="M2.8 5L8 8l5.2-3" />
          <path d="M8 8v6" />
        </svg>
      );

    case "prism":
      return (
        <svg
          className={combinedClassName}
          data-geometry-icon="prism"
          width={size}
          height={size}
          viewBox="0 0 16 16"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d="M2.6 2.4h10.8L8 5.6 2.6 2.4Z" />
          <path d="M2.6 2.4v8.2L8 13.6l5.4-3V2.4" />
          <path d="M8 5.6v8" />
        </svg>
      );

    case "sphere":
      return (
        <svg
          className={combinedClassName}
          data-geometry-icon="sphere"
          width={size}
          height={size}
          viewBox="0 0 16 16"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <circle cx="8" cy="8" r="5.6" />
          <ellipse cx="8" cy="8" rx="5.6" ry="2.0" strokeOpacity="0.68" />
          <path d="M8 2.4c1.9 1.6 1.9 9.6 0 11.2" strokeOpacity="0.68" />
        </svg>
      );

    case "cylinder":
      return (
        <svg
          className={combinedClassName}
          data-geometry-icon="cylinder"
          width={size}
          height={size}
          viewBox="0 0 16 16"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <ellipse cx="8" cy="4.3" rx="5.2" ry="1.85" />
          <path d="M2.8 4.3v7.4c0 1.02 2.33 1.85 5.2 1.85s5.2-.83 5.2-1.85V4.3" />
        </svg>
      );

    case "cone":
      return (
        <svg
          className={combinedClassName}
          data-geometry-icon="cone"
          width={size}
          height={size}
          viewBox="0 0 16 16"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d="M2.7 11.8L8 2.3l5.3 9.5" />
          <ellipse cx="8" cy="11.8" rx="5.3" ry="1.9" />
        </svg>
      );

    case "neutral":
    default:
      return (
        <svg
          className={combinedClassName}
          data-geometry-icon="neutral"
          width={size}
          height={size}
          viewBox="0 0 16 16"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d="M8 8.8V2.6" />
          <path d="M8 8.8l5.3 4.6" />
          <path d="M8 8.8L2.7 13.4" />
          <path d="M8 5.1l3.1 1.9v3.8" strokeOpacity="0.6" />
        </svg>
      );
  }
}
