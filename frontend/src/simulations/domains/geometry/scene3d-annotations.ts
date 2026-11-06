/**
 * W17 · §15.4 — SỐ ĐO TRÊN HÌNH, phía trình bày. W18 · §16.5–16.7 — nhãn TẬP TRUNG.
 *
 * Backend sở hữu NGHĨA: đại lượng nào gắn với chủ thể nào, vai trò (`role`), gộp (`same_as`) và nhân
 * chứng khoảng cách (`witness`, chân chính xác) — `quantity_annotations.py`. Ở đây chỉ còn việc
 * trình bày, mọi hàm đều thuần:
 *   - `annotationsAt` — nhãn nào được hiện ở bước này: luật khả dụng của lớp lời giải (không lộ
 *     trước), rồi luật TẬP TRUNG — mặc định dữ kiện đề cho; chọn một đại lượng thì nó và chuỗi số
 *     của nó; chọn một vật thì các đại lượng về vật ấy; "Hiện tất cả" thì mọi nhãn khả dụng;
 *   - `annotationAnchor` — điểm neo THẾ GIỚI lấy từ chủ thể backend chỉ (không đọc tên biến);
 *   - `witnessesShown` — nhân chứng của nhãn khoảng cách đang hiện, toạ độ backend phát;
 *   - `quantitySources` — dữ kiện số và đầu vào trực tiếp của một đại lượng, cho ô soi;
 *   - `placeAnnotationLabels` — đặt hộp nhãn theo luật §15.5: trong khung, không đè nhãn điểm /
 *     nút điều khiển, điểm gần nhất của hộp cách điểm neo chiếu ≤ `NEO_TOI_DA` px; không có chỗ
 *     thì ẩn — một nhãn trôi xa vật nó gọi tên còn tệ hơn không có nhãn (giá trị vẫn ở ô soi và
 *     lời giải).
 * Không hàm nào tính GIÁ TRỊ hay dựng hình: chữ của nhãn là ký hiệu + giá trị payload.
 */
import type { CanonicalMathProvenance, QuantityAnnotation, QuantityProvenance, Scene3D, SceneObject, Vec3 } from "./scene3d-model";
import {
  certifiedCuttingPlaneDistanceGivens,
  certifiedHybridGivenDimensions,
  clampStep,
  classifyQuantityProvenance,
  exactSceneOriginOf,
  ghiChuGiaTriDung,
  hienBieuThucDaiLuong,
  isDerivedQuantityMetricallyUnderdetermined,
  numericalBasis,
  objectsAt,
  toNumber,
  toVec3,
} from "./scene3d-model";
import { tangNhanManh } from "./interaction-state";
import { nhanChungVuongGocHopLe } from "./scene3d-witness-gate";

export { classifyQuantityProvenance, type QuantityProvenance };

interface ExactRational {
  num: bigint;
  den: bigint;
}

function gcdBig(a: bigint, b: bigint): bigint {
  let x = a < 0n ? -a : a;
  let y = b < 0n ? -b : b;
  while (y !== 0n) {
    const t = x % y;
    x = y;
    y = t;
  }
  return x === 0n ? 1n : x;
}

function reduceRational(num: bigint, den: bigint): ExactRational | null {
  if (den === 0n) return null;
  const sign = den < 0n ? -1n : 1n;
  const n = num * sign;
  const d = den * sign;
  const g = gcdBig(n, d);
  return { num: n / g, den: d / g };
}

function parseExactRational(s: string | undefined | null): ExactRational | null {
  if (typeof s !== "string") return null;
  const m = /^\s*(-?\d+)(?:\/(\d+))?\s*$/.exec(s);
  if (!m) return null;
  const num = BigInt(m[1]);
  const den = m[2] !== undefined ? BigInt(m[2]) : 1n;
  return reduceRational(num, den);
}

function exactQuantitySquare(o: SceneObject): ExactRational | null {
  if (o.exact) {
    if (o.exact.kind === "rational") {
      const r = parseExactRational(o.exact.value);
      return r ? reduceRational(r.num * r.num, r.den * r.den) : null;
    }
    if (o.exact.kind === "radical") {
      if ((o.exact.pi ?? 0) !== 0) return null;
      if (!Number.isInteger(o.exact.radicand) || o.exact.radicand < 0) return null;
      const c = parseExactRational(o.exact.coefficient);
      if (!c) return null;
      return reduceRational(c.num * c.num * BigInt(o.exact.radicand), c.den * c.den);
    }
    return null;
  }
  const r = parseExactRational(o.value);
  return r ? reduceRational(r.num * r.num, r.den * r.den) : null;
}

function sameExactRational(a: ExactRational | null, b: ExactRational | null): boolean {
  return Boolean(a && b && a.num * b.den === b.num * a.den);
}

export interface AnnotationView {
  /** "Hiện tất cả": mọi nhãn khả dụng ở bước đang xem, không chỉ dữ kiện và vật đang chọn. */
  showAll: boolean;
  /** Ẩn các nhãn kích thước đề cho (`role === "given"`) khi học sinh tắt tùy chọn `Thông số hình học`. */
  hideGiven?: boolean;
  /** Hide label text in the renderer; certified witness geometry remains available. */
  hiddenIds?: ReadonlySet<string>;
}

/** §16.5 (thay U-W17-1): mặc định gọn — tên điểm và dữ kiện đề cho. */
export const DEFAULT_ANNOTATION_VIEW: AnnotationView = Object.freeze({ showAll: false });

export interface AnnotationEntry {
  id: string;
  kind: QuantityAnnotation["kind"];
  role: NonNullable<QuantityAnnotation["role"]>;
  provenance: CanonicalMathProvenance;
  subject_ids: string[];
  anchor: QuantityAnnotation["anchor"];
  witness?: QuantityAnnotation["witness"];
  /** Ký hiệu = giá trị (+ đơn vị nếu payload có) — chữ của payload, không tính lại. */
  text: string;
  /** Càng lớn càng được đặt trước khi chật chỗ. */
  priority: number;
  /** Thuộc tiêu điểm của lựa chọn hiện tại (đại lượng đang chọn, chuỗi số của nó, hay vật nó đo). */
  related: boolean;
}

export interface GivenQuantitySummaryEntry {
  id: string;
  text: string;
  role: "given";
  provenance: CanonicalMathProvenance;
  subject_ids: string[];
  status: "on_canvas" | "pending_step" | "unattached_scalar";
}

/** Vai trò của nhãn; chỉ gán `"given"` khi nguồn gốc nhận thức đã chứng thực là `GIVEN`. */
function vaiTro(
  o: SceneObject,
  a: QuantityAnnotation,
  scene?: Partial<Pick<Scene3D, "free_objects" | "objects">> | null,
): AnnotationEntry["role"] {
  if (a.role === "result" || a.category === "result") return "result";
  if (classifyQuantityProvenance(o, scene) === "GIVEN") return "given";
  return a.role === "given" ? "intermediate" : (a.role ?? "intermediate");
}

/** Có nhãn nào mặc định đang ẩn không — công tắc "Hiện tất cả" vắng khi không có gì để hiện thêm (§3.2). */
export function hasHiddenByDefault(scene: Scene3D): boolean {
  return scene.objects.some((o) => o.type === "quantity" && o.annotation && !o.annotation.same_as
    && vaiTro(o, o.annotation, scene) !== "given");
}

/** Cặp điểm không hướng — khoá của một đoạn theo danh tính hai đầu mút. */
const capDiem = (a: string, b: string) => (a < b ? `${a}\u0000${b}` : `${b}\u0000${a}`);

/**
 * regular-square-pyramid-w02 · A — những ĐOẠN đang có mặt trên hình ở bước này, theo danh tính: đoạn dựng
 * (`endpoint_ids`), cạnh của đa giác (`vertex_ids` theo vòng), cạnh của khối (`edge_ownership`). Một nhãn độ dài
 * chỉ có chỗ bám khi đoạn nó đo đã được dựng; hai điểm đầu mút có mặt chưa đủ.
 */
function doanCoMat(coMat: SceneObject[]): Set<string> {
  const ra = new Set<string>();
  const ids = new Set(coMat.map((o) => o.id));
  for (const o of coMat) {
    if (o.endpoint_ids?.length === 2) ra.add(capDiem(o.endpoint_ids[0], o.endpoint_ids[1]));
    else if (o.type === "segment3" && o.depends?.length === 2 && ids.has(o.depends[0]) && ids.has(o.depends[1])) {
      ra.add(capDiem(o.depends[0], o.depends[1]));
    }
    if (o.type === "polygon3" && o.vertex_ids && o.vertex_ids.length >= 3) {
      o.vertex_ids.forEach((v, i, d) => ra.add(capDiem(v, d[(i + 1) % d.length])));
    } else if (o.type === "polygon3" && o.depends?.length === 3) {
      o.depends.forEach((v, i, d) => ra.add(capDiem(v, d[(i + 1) % d.length])));
    }
    if (o.type === "section" && o.endpoint_entities && o.endpoint_entities.length >= 2) {
      const ents = o.endpoint_entities;
      const limit = o.closed === false ? ents.length - 1 : ents.length;
      for (let i = 0; i < limit; i += 1) {
        const u = ents[i]?.entity_id;
        const v = ents[(i + 1) % ents.length]?.entity_id;
        if (u && v && ids.has(u) && ids.has(v)) ra.add(capDiem(u, v));
      }
    }
    for (const e of o.edge_ownership ?? []) {
      if (e.endpoint_ids?.length === 2) ra.add(capDiem(e.endpoint_ids[0], e.endpoint_ids[1]));
    }
    if (o.type === "point3" && o.perpendicular_witness?.from && ids.has(o.perpendicular_witness.from)) {
      ra.add(capDiem(o.id, o.perpendicular_witness.from));
    }
  }
  return ra;
}

interface ResolvedEffectiveAnnotation {
  ann: QuantityAnnotation;
  fallbackNotation: string | null;
  ownerSolidId: string | null;
}

const REGION_SUBJECT_TYPES = new Set(["polygon3", "section", "circle3", "ellipse3", "plane3"]);
const SOLID_SUBJECT_TYPES = new Set(["solid", "curved_solid"]);

/**
 * Kiểm tra ràng buộc cấu trúc của `QuantityAnnotation`: chặn các annotation gắn nhầm đối tượng
 * (trùng đỉnh `[A, A]`, trỏ tới ID không tồn tại, `anchor === "segment"` nhưng chủ thể không phải `point3`, v.v.).
 */
function hopLeChuTheAnnotation(
  a: QuantityAnnotation,
  theoId: ReadonlyMap<string, SceneObject>,
): boolean {
  if (!Array.isArray(a.subject_ids) || a.subject_ids.length === 0) return false;
  if (new Set(a.subject_ids).size !== a.subject_ids.length) return false;
  const subjects = a.subject_ids.map((id) => theoId.get(id));
  if (subjects.some((s) => !s)) return false;
  const vat = subjects as SceneObject[];

  if (a.anchor === "segment") {
    return vat.length === 2 && vat.every((s) => s.type === "point3" && Boolean(s.xyz));
  }
  if (a.anchor === "region") {
    return vat.length === 1 && REGION_SUBJECT_TYPES.has(vat[0].type);
  }
  if (a.anchor === "solid") {
    return vat.length === 1 && SOLID_SUBJECT_TYPES.has(vat[0].type);
  }
  if (a.anchor === "witness") {
    if (!a.witness) return false;
    const hasFrom = Boolean(a.witness.from_point) || theoId.has(a.witness.from);
    return hasFrom && theoId.has(a.witness.on);
  }
  if (a.anchor === "pair") {
    if (vat.length === 3) {
      return a.kind === "angle" && vat.every((s) => s.type === "point3" && Boolean(s.xyz));
    }
    return vat.length === 2 && vat.some((s) => Boolean(s.xyz));
  }
  return false;
}

/**
 * Liên kết cấu trúc chính xác cho dữ kiện `GIVEN` của khối tròn xoay dựa trên `dependency_edges` / `depends`
 * và đẳng thức bình phương hữu tỉ `q² === radius_sq | height_sq` (TUYỆT ĐỐI không đoán từ tên biến hay đề bài).
 */
type ExactVec3Rat = [ExactRational, ExactRational, ExactRational];

function parseExactVec3(v: readonly string[] | undefined): ExactVec3Rat | null {
  if (!v || v.length !== 3) return null;
  const r0 = parseExactRational(v[0]);
  const r1 = parseExactRational(v[1]);
  const r2 = parseExactRational(v[2]);
  if (!r0 || !r1 || !r2) return null;
  return [r0, r1, r2];
}

function addExactRat(a: ExactRational, b: ExactRational): ExactRational | null {
  return reduceRational(a.num * b.den + b.num * a.den, a.den * b.den);
}

function subExactRat(a: ExactRational, b: ExactRational): ExactRational | null {
  return reduceRational(a.num * b.den - b.num * a.den, a.den * b.den);
}

function mulExactRat(a: ExactRational, b: ExactRational): ExactRational | null {
  return reduceRational(a.num * b.num, a.den * b.den);
}

function exactVec3Equal(a: readonly string[] | undefined, b: readonly string[] | undefined): boolean {
  if (!a || !b || a.length !== 3 || b.length !== 3) return false;
  return (
    sameExactRational(parseExactRational(a[0]), parseExactRational(b[0]))
    && sameExactRational(parseExactRational(a[1]), parseExactRational(b[1]))
    && sameExactRational(parseExactRational(a[2]), parseExactRational(b[2]))
  );
}

function exactCovectorPairing(
  diff: ExactVec3Rat,
  covector: readonly string[] | undefined,
): ExactRational | null {
  const n = parseExactVec3(covector);
  if (!n) return null;
  let sum: ExactRational = { num: 0n, den: 1n };
  for (let i = 0; i < 3; i += 1) {
    const prod = mulExactRat(diff[i], n[i]);
    if (!prod) return null;
    const next = addExactRat(sum, prod);
    if (!next) return null;
    sum = next;
  }
  return sum;
}

function exactMetricDistSq(
  a: readonly string[] | undefined,
  b: readonly string[] | undefined,
  chartMetric: Scene3D["chart_metric"],
): ExactRational | null {
  const pa = parseExactVec3(a);
  const pb = parseExactVec3(b);
  if (!pa || !pb) return null;
  const d0 = subExactRat(pa[0], pb[0]);
  const d1 = subExactRat(pa[1], pb[1]);
  const d2 = subExactRat(pa[2], pb[2]);
  if (!d0 || !d1 || !d2) return null;
  const diff: ExactVec3Rat = [d0, d1, d2];
  if (!chartMetric) {
    let sum: ExactRational = { num: 0n, den: 1n };
    for (let i = 0; i < 3; i += 1) {
      const sq = mulExactRat(diff[i], diff[i]);
      if (!sq) return null;
      const next = addExactRat(sum, sq);
      if (!next) return null;
      sum = next;
    }
    return sum;
  }
  let total: ExactRational = { num: 0n, den: 1n };
  for (let i = 0; i < 3; i += 1) {
    for (let j = 0; j < 3; j += 1) {
      const gij = parseExactRational(chartMetric[i]?.[j]);
      if (!gij) return null;
      const diDj = mulExactRat(diff[i], diff[j]);
      const term = diDj ? mulExactRat(diDj, gij) : null;
      if (!term) return null;
      const next = addExactRat(total, term);
      if (!next) return null;
      total = next;
    }
  }
  return total;
}

function findCurvedBaseCircleId(
  cs: SceneObject,
  rSq: ExactRational | null,
  coMat: ReadonlySet<string>,
  theoId: ReadonlyMap<string, SceneObject>,
  exactById: ReadonlyMap<string, SceneObject>,
): string | null {
  if (cs.curved_kind === "ball" || !rSq) return null;
  const exCs = exactById.get(cs.id) ?? cs;
  if (!exCs.anchor) return null;
  let topFallback: string | null = null;
  for (const cand of theoId.values()) {
    if (cand.type !== "circle3" || !coMat.has(cand.id)) continue;
    const exCand = exactById.get(cand.id) ?? cand;
    if (exCand.surface_role === "SECTION_REGION") continue;
    if (!sameExactRational(parseExactRational(exCand.radius_sq), rSq)) continue;
    if (exactVec3Equal(exCand.center, exCs.anchor)) {
      return cand.id;
    }
    if (cs.curved_kind === "cylinder" && exCs.apex_or_top && exactVec3Equal(exCand.center, exCs.apex_or_top) && !topFallback) {
      topFallback = cand.id;
    }
  }
  return topFallback;
}

function findCurvedRadiusSegmentEndpoints(
  cs: SceneObject,
  rSq: ExactRational | null,
  coMat: ReadonlySet<string>,
  doan: ReadonlySet<string>,
  theoId: ReadonlyMap<string, SceneObject>,
  exactById: ReadonlyMap<string, SceneObject>,
  chartMetric: Scene3D["chart_metric"],
): [string, string] | null {
  const exCs = exactById.get(cs.id) ?? cs;
  if (!exCs.anchor || !rSq) return null;
  const centers: { vec: readonly string[]; isBottom: boolean; capNormals: (readonly string[])[] }[] = [];
  const collectCapNormals = (centerVec: readonly string[]): (readonly string[])[] => {
    const normals: (readonly string[])[] = [];
    for (const cObj of theoId.values()) {
      if (cObj.type !== "circle3") continue;
      const exCir = exactById.get(cObj.id) ?? cObj;
      if (exCir.surface_role === "SECTION_REGION" || !exCir.normal) continue;
      if (exactVec3Equal(exCir.center, centerVec) && sameExactRational(parseExactRational(exCir.radius_sq), rSq)) {
        normals.push(exCir.normal);
      }
    }
    return normals;
  };
  centers.push({
    vec: exCs.anchor,
    isBottom: true,
    capNormals: exCs.curved_kind === "ball" ? [] : collectCapNormals(exCs.anchor),
  });
  if (exCs.curved_kind === "cylinder" && exCs.apex_or_top) {
    centers.push({
      vec: exCs.apex_or_top,
      isBottom: false,
      capNormals: collectCapNormals(exCs.apex_or_top),
    });
  }

  let bestEps: [string, string] | null = null;
  let bestScore = -1;

  for (const cand of theoId.values()) {
    if (cand.type !== "segment3") continue;
    const exCand = exactById.get(cand.id) ?? cand;
    const epIds = exCand.endpoint_ids ?? cand.endpoint_ids;
    if (!epIds || epIds.length !== 2) continue;
    const [id0, id1] = epIds;
    const o0 = theoId.get(id0);
    const o1 = theoId.get(id1);
    if (o0?.type !== "point3" || o1?.type !== "point3") continue;
    const p0 = exactById.get(id0)?.xyz ?? o0.xyz;
    const p1 = exactById.get(id1)?.xyz ?? o1.xyz;
    if (!p0 || !p1) continue;

    if (
      exCs.curved_kind !== "ball"
      && exCs.apex_or_top
      && ((exactVec3Equal(p0, exCs.anchor) && exactVec3Equal(p1, exCs.apex_or_top))
        || (exactVec3Equal(p1, exCs.anchor) && exactVec3Equal(p0, exCs.apex_or_top)))
    ) {
      continue;
    }

    const matchedCenter = centers.find((c) => exactVec3Equal(p0, c.vec) || exactVec3Equal(p1, c.vec));
    if (!matchedCenter) continue;
    if (!sameExactRational(exactMetricDistSq(p0, p1, chartMetric), rSq)) continue;

    if (exCs.curved_kind !== "ball" && matchedCenter.capNormals.length > 0) {
      const vp0 = parseExactVec3(p0);
      const vp1 = parseExactVec3(p1);
      if (!vp0 || !vp1) continue;
      const dv0 = subExactRat(vp1[0], vp0[0]);
      const dv1 = subExactRat(vp1[1], vp0[1]);
      const dv2 = subExactRat(vp1[2], vp0[2]);
      if (!dv0 || !dv1 || !dv2) continue;
      const diffVec: ExactVec3Rat = [dv0, dv1, dv2];
      const inCapPlane = matchedCenter.capNormals.some((nCov) =>
        sameExactRational(exactCovectorPairing(diffVec, nCov), { num: 0n, den: 1n }),
      );
      if (!inCapPlane) continue;
    }

    const isVisibleNow = coMat.has(id0) && coMat.has(id1) && doan.has(capDiem(id0, id1));
    const hasPerpWitness = Boolean(exCand.perpendicular_witness ?? cand.perpendicular_witness);
    const dependsOnSolid = (exCand.depends ?? cand.depends ?? []).includes(cs.id);
    const isActiveSphereTriangleHypotenuse =
      isVisibleNow && (cand.display_group ?? []).includes("sphere_plane_aux");
    const score =
      (isVisibleNow ? 16 : 0)
      + (isActiveSphereTriangleHypotenuse ? 3 : 0)
      + (!hasPerpWitness ? 4 : 0)
      + (dependsOnSolid ? 2 : 0)
      + (matchedCenter.isBottom ? 1 : 0);
    if (score > bestScore) {
      bestScore = score;
      bestEps = [id0, id1];
    }
  }
  return bestEps;
}

function findCurvedAxisSegmentEndpoints(
  cs: SceneObject,
  hSq: ExactRational | null,
  coMat: ReadonlySet<string>,
  doan: ReadonlySet<string>,
  theoId: ReadonlyMap<string, SceneObject>,
  exactById: ReadonlyMap<string, SceneObject>,
  chartMetric: Scene3D["chart_metric"],
): [string, string] | null {
  if (cs.curved_kind === "ball" || !hSq) return null;
  const exCs = exactById.get(cs.id) ?? cs;
  if (!exCs.anchor || !exCs.apex_or_top) return null;
  let bestEps: [string, string] | null = null;
  let bestScore = -1;
  for (const cand of theoId.values()) {
    if (cand.type !== "segment3") continue;
    const exCand = exactById.get(cand.id) ?? cand;
    const epIds = exCand.endpoint_ids ?? cand.endpoint_ids;
    if (!epIds || epIds.length !== 2) continue;
    const [id0, id1] = epIds;
    const p0 = exactById.get(id0)?.xyz ?? theoId.get(id0)?.xyz;
    const p1 = exactById.get(id1)?.xyz ?? theoId.get(id1)?.xyz;
    if (!p0 || !p1) continue;
    if (!sameExactRational(exactMetricDistSq(p0, p1, chartMetric), hSq)) continue;
    const connectsCenters =
      (exactVec3Equal(p0, exCs.anchor) && exactVec3Equal(p1, exCs.apex_or_top))
      || (exactVec3Equal(p1, exCs.anchor) && exactVec3Equal(p0, exCs.apex_or_top));
    const isAltitudeFromTop =
      Boolean(exCand.perpendicular_witness ?? cand.perpendicular_witness)
      && (exactVec3Equal(p0, exCs.apex_or_top) || exactVec3Equal(p1, exCs.apex_or_top));
    if (!connectsCenters && !isAltitudeFromTop) continue;
    const isVisibleNow = coMat.has(id0) && coMat.has(id1) && doan.has(capDiem(id0, id1));
    const score = (isVisibleNow ? 8 : 0) + (connectsCenters ? 4 : 0);
    if (score > bestScore) {
      bestScore = score;
      bestEps = [id0, id1];
    }
  }
  return bestEps;
}

function resolveCurvedGivenFallback(
  scene: Scene3D,
  o: SceneObject,
  theoId: ReadonlyMap<string, SceneObject>,
  exactById: ReadonlyMap<string, SceneObject>,
): { ownerSolidId: string; fallbackNotation: "R" | "h" } | null {
  if (classifyQuantityProvenance(o, scene) !== "GIVEN") return null;
  const qSq = exactQuantitySquare(o);
  if (!qSq) return null;
  let cs: SceneObject | undefined;
  if (o.annotation) {
    if (!hopLeChuTheAnnotation(o.annotation, theoId)) return null;
    if (
      (o.annotation.kind === "length" || (o.annotation.kind as string) === "radius")
      && o.annotation.anchor === "solid"
      && o.annotation.subject_ids.length === 1
    ) {
      const target = theoId.get(o.annotation.subject_ids[0]);
      if (target?.type === "curved_solid") cs = target;
    }
  } else {
    cs = scene.objects.find(
      (cand) =>
        cand.type === "curved_solid"
        && (
          (cand.dependency_edges ?? []).some((e) => e.source_id === o.id && e.relation === "numerical")
          || (cand.depends ?? []).includes(o.id)
        ),
    );
  }
  if (!cs) return null;
  const exCs = exactById.get(cs.id) ?? cs;
  const rSq = parseExactRational(exCs.radius_sq ?? cs.radius_sq);
  const hSq = exCs.curved_kind !== "ball" ? parseExactRational(exCs.height_sq ?? cs.height_sq) : null;
  const matchesRadius = sameExactRational(qSq, rSq);
  const matchesHeight = sameExactRational(qSq, hSq);
  if ((o.annotation?.kind as string | undefined) === "radius" && matchesRadius) {
    return { ownerSolidId: cs.id, fallbackNotation: "R" };
  }
  if (matchesRadius && !matchesHeight) {
    return { ownerSolidId: cs.id, fallbackNotation: "R" };
  }
  if (matchesHeight && !matchesRadius) {
    return { ownerSolidId: cs.id, fallbackNotation: "h" };
  }
  return null;
}

function resolveEffectiveAnnotation(
  scene: Scene3D,
  o: SceneObject,
  coMat: ReadonlySet<string>,
  doan: ReadonlySet<string>,
  theoId: ReadonlyMap<string, SceneObject>,
): ResolvedEffectiveAnnotation | null {
  const exactOrigin = exactSceneOriginOf(scene);
  const exactById = new Map(exactOrigin.objects.map((obj) => [obj.id, obj]));
  const chartMetric = exactOrigin.chart_metric;
  const prov = classifyQuantityProvenance(o, scene);
  if (o.annotation) {
    if (!hopLeChuTheAnnotation(o.annotation, theoId)) {
      return null;
    }
    const isLinearSolidAnn =
      (o.annotation.kind === "length" || (o.annotation.kind as string) === "radius")
      && o.annotation.anchor === "solid"
      && o.annotation.subject_ids.length === 1;
    if (prov === "GIVEN" && isLinearSolidAnn) {
      const cs = theoId.get(o.annotation.subject_ids[0]);
      if (cs?.type === "curved_solid") {
        const exCs = exactById.get(cs.id) ?? cs;
        const qSq = exactQuantitySquare(o);
        const rSq = parseExactRational(exCs.radius_sq ?? cs.radius_sq);
        const hSq = exCs.curved_kind !== "ball" ? parseExactRational(exCs.height_sq ?? cs.height_sq) : null;
        const matchesRadius = sameExactRational(qSq, rSq);
        const matchesHeight = sameExactRational(qSq, hSq);
        if (matchesRadius && (!matchesHeight || (o.annotation.kind as string) === "radius")) {
          const eps = findCurvedRadiusSegmentEndpoints(cs, rSq, coMat, doan, theoId, exactById, chartMetric);
          if (eps && (cs.curved_kind === "ball" || (coMat.has(eps[0]) && coMat.has(eps[1]) && doan.has(capDiem(eps[0], eps[1]))))) {
            return {
              ann: { ...o.annotation, kind: "length", subject_ids: [eps[0], eps[1]], anchor: "segment" },
              fallbackNotation: "R",
              ownerSolidId: cs.id,
            };
          }
          const baseBotId = findCurvedBaseCircleId(cs, rSq, coMat, theoId, exactById);
          if (baseBotId) {
            return {
              ann: { ...o.annotation, kind: "length", subject_ids: [baseBotId], anchor: "region" },
              fallbackNotation: "R",
              ownerSolidId: cs.id,
            };
          }
          if (cs.curved_kind === "ball") {
            return null;
          }
        } else if (matchesHeight && !matchesRadius) {
          const eps = findCurvedAxisSegmentEndpoints(cs, hSq, coMat, doan, theoId, exactById, chartMetric);
          if (eps && coMat.has(eps[0]) && coMat.has(eps[1]) && doan.has(capDiem(eps[0], eps[1]))) {
            return {
              ann: { ...o.annotation, kind: "length", subject_ids: [eps[0], eps[1]], anchor: "segment" },
              fallbackNotation: "h",
              ownerSolidId: cs.id,
            };
          }
        }
      }
    }
    if (
      isLinearSolidAnn
      && (exactById.get(o.annotation.subject_ids[0]) ?? theoId.get(o.annotation.subject_ids[0]))?.curved_kind === "ball"
    ) {
      return null;
    }
    if (
      o.annotation.kind === "distance"
      && o.annotation.anchor === "pair"
      && o.annotation.subject_ids.length === 2
    ) {
      const s0 = theoId.get(o.annotation.subject_ids[0]);
      const s1 = theoId.get(o.annotation.subject_ids[1]);
      const ptSubj = s0?.type === "point3" ? s0 : s1?.type === "point3" ? s1 : undefined;
      const plSubj = s0?.type === "plane3" ? s0 : s1?.type === "plane3" ? s1 : undefined;
      if (ptSubj && plSubj) {
        let footId: string | null = null;
        for (const cand of theoId.values()) {
          if (
            cand.type === "point3"
            && cand.id !== ptSubj.id
            && cand.xyz
            && cand.perpendicular_witness?.from === ptSubj.id
            && cand.perpendicular_witness?.on === plSubj.id
          ) {
            footId = cand.id;
            break;
          }
          if (cand.type === "segment3" && cand.endpoint_ids?.length === 2 && cand.perpendicular_witness?.on === plSubj.id) {
            const [u, v] = cand.endpoint_ids;
            if (u === ptSubj.id && theoId.get(v)?.type === "point3") {
              footId = v;
              break;
            }
            if (v === ptSubj.id && theoId.get(u)?.type === "point3") {
              footId = u;
              break;
            }
          }
        }
        if (footId) {
          return {
            ann: { ...o.annotation, subject_ids: [ptSubj.id, footId], anchor: "segment" },
            fallbackNotation: null,
            ownerSolidId: null,
          };
        }
      }
    }
    const explicitCurvedOwner =
      prov === "GIVEN" && isLinearSolidAnn && theoId.get(o.annotation.subject_ids[0])?.type === "curved_solid"
        ? o.annotation.subject_ids[0]
        : null;
    return { ann: o.annotation, fallbackNotation: null, ownerSolidId: explicitCurvedOwner };
  }

  if (prov !== "GIVEN") return null;
  const qSq = exactQuantitySquare(o);
  if (!qSq) return null;

  const refIds = [...new Set([...(o.depends ?? []), ...(o.dependency_edges ?? []).map((e) => e.source_id)])];
  const refPts = refIds.map((id) => theoId.get(id)).filter((x): x is SceneObject => x?.type === "point3" && Boolean(x.xyz));
  const refPlanes = refIds.map((id) => theoId.get(id)).filter((x): x is SceneObject => x?.type === "plane3" || x?.type === "polygon3");
  if (refPts.length === 1 && refPlanes.length === 1) {
    const ptSubj = refPts[0];
    const plSubj = refPlanes[0];
    const ptExXyz = exactById.get(ptSubj.id)?.xyz ?? ptSubj.xyz;
    let footId: string | null = null;
    for (const cand of theoId.values()) {
      let candidateFoot: SceneObject | undefined;
      if (
        cand.type === "point3"
        && cand.id !== ptSubj.id
        && cand.xyz
        && cand.perpendicular_witness?.from === ptSubj.id
        && cand.perpendicular_witness?.on === plSubj.id
      ) {
        candidateFoot = cand;
      } else if (cand.type === "segment3" && cand.endpoint_ids?.length === 2 && cand.perpendicular_witness?.on === plSubj.id) {
        const [u, v] = cand.endpoint_ids;
        if (u === ptSubj.id && theoId.get(v)?.type === "point3") candidateFoot = theoId.get(v);
        else if (v === ptSubj.id && theoId.get(u)?.type === "point3") candidateFoot = theoId.get(u);
      }
      if (candidateFoot?.xyz) {
        const footExXyz = exactById.get(candidateFoot.id)?.xyz ?? candidateFoot.xyz;
        if (sameExactRational(exactMetricDistSq(ptExXyz, footExXyz, chartMetric), qSq)) {
          footId = candidateFoot.id;
          break;
        }
      }
    }
    if (footId) {
      const cSym = ptSubj.notation?.trim() || ptSubj.id;
      const rawPlSym = plSubj.notation?.trim() || plSubj.label?.replace(/^Mặt\s+phẳng\s+/iu, "").trim() || plSubj.id;
      const pSym = rawPlSym.startsWith("(") && rawPlSym.endsWith(")") ? rawPlSym : `(${rawPlSym})`;
      return {
        ann: {
          kind: "distance",
          category: "measurement",
          role: "given",
          subject_ids: [ptSubj.id, footId],
          anchor: "segment",
        },
        fallbackNotation: `d(${cSym}, ${pSym})`,
        ownerSolidId: null,
      };
    }
  }

  const linkedCurved = scene.objects.find(
    (cand) =>
      cand.type === "curved_solid"
      && (
        (cand.dependency_edges ?? []).some((e) => e.source_id === o.id && e.relation === "numerical")
        || (cand.depends ?? []).includes(o.id)
      ),
  );
  if (!linkedCurved) return null;

  const exLinked = exactById.get(linkedCurved.id) ?? linkedCurved;
  const rSq = parseExactRational(exLinked.radius_sq ?? linkedCurved.radius_sq);
  const hSq = exLinked.curved_kind !== "ball" ? parseExactRational(exLinked.height_sq ?? linkedCurved.height_sq) : null;
  const matchesRadius = sameExactRational(qSq, rSq);
  const matchesHeight = sameExactRational(qSq, hSq);
  if (matchesRadius && matchesHeight) {
    return null;
  }

  if (matchesRadius) {
    const eps = findCurvedRadiusSegmentEndpoints(linkedCurved, rSq, coMat, doan, theoId, exactById, chartMetric);
    if (eps && (linkedCurved.curved_kind === "ball" || (coMat.has(eps[0]) && coMat.has(eps[1]) && doan.has(capDiem(eps[0], eps[1]))))) {
      return {
        ann: {
          kind: "length",
          category: "measurement",
          role: "given",
          subject_ids: [eps[0], eps[1]],
          anchor: "segment",
        },
        fallbackNotation: "R",
        ownerSolidId: linkedCurved.id,
      };
    }
    if (linkedCurved.curved_kind === "ball") {
      return null;
    }
    const baseBotId = findCurvedBaseCircleId(linkedCurved, rSq, coMat, theoId, exactById);
    if (baseBotId) {
      return {
        ann: {
          kind: "length",
          category: "measurement",
          role: "given",
          subject_ids: [baseBotId],
          anchor: "region",
        },
        fallbackNotation: "R",
        ownerSolidId: linkedCurved.id,
      };
    }
    return {
      ann: {
        kind: "length",
        category: "measurement",
        role: "given",
        subject_ids: [linkedCurved.id],
        anchor: "solid",
      },
      fallbackNotation: "R",
      ownerSolidId: linkedCurved.id,
    };
  }

  if (matchesHeight) {
    const eps = findCurvedAxisSegmentEndpoints(linkedCurved, hSq, coMat, doan, theoId, exactById, chartMetric);
    if (eps && coMat.has(eps[0]) && coMat.has(eps[1]) && doan.has(capDiem(eps[0], eps[1]))) {
      const symA = theoId.get(eps[0])?.notation?.trim();
      const symB = theoId.get(eps[1])?.notation?.trim();
      return {
        ann: {
          kind: "length",
          category: "measurement",
          role: "given",
          subject_ids: [eps[0], eps[1]],
          anchor: "segment",
        },
        fallbackNotation: symA && symB ? `${symA}${symB}` : "h",
        ownerSolidId: linkedCurved.id,
      };
    }
    return {
      ann: {
        kind: "length",
        category: "measurement",
        role: "given",
        subject_ids: [linkedCurved.id],
        anchor: "solid",
      },
      fallbackNotation: "h",
      ownerSolidId: linkedCurved.id,
    };
  }

  return null;
}

function canonicalAnnotationSubjectKey(a: Pick<AnnotationEntry, "kind" | "anchor" | "subject_ids" | "witness">): string {
  if (a.anchor === "segment" && a.subject_ids.length === 2) {
    return `${a.kind}|segment|${capDiem(a.subject_ids[0], a.subject_ids[1])}`;
  }
  if (a.anchor === "witness" && a.witness) {
    return `${a.kind}|witness|${a.witness.from}|${a.witness.foot.join(",")}|${a.witness.on}`;
  }
  return `${a.kind}|${a.anchor}|${[...a.subject_ids].sort().join("\u0000")}`;
}

function canvasSpatialAnnotationKey(a: Pick<AnnotationEntry, "kind" | "anchor" | "subject_ids" | "witness">): string {
  if (a.anchor === "segment" && a.subject_ids.length === 2) {
    return `segment|${capDiem(a.subject_ids[0], a.subject_ids[1])}`;
  }
  return canonicalAnnotationSubjectKey(a);
}

function activeCompletedPolyhedralSectionEdgeKeys(
  scene: Scene3D,
  k: number,
  vatCoMat: readonly SceneObject[],
): Set<string> | null {
  if (!scene.objects.some((x) => x.type === "solid")) return null;
  const progressById = new Map(
    (scene.formation?.steps[k]?.geometry_progress ?? []).map((gp) => [gp.object_id, gp]),
  );
  const completedSections = vatCoMat.filter((c) => {
    const isPolySection =
      c.type === "section"
      || (
        c.type === "polygon3"
        && (c.surface_role === "SECTION_REGION" || (c.formation_roles ?? []).includes("PRODUCE_SECTION_RESULT"))
      );
    if (!isPolySection) return false;
    const prog = progressById.get(c.id);
    const closedNow = prog ? prog.closed : c.closed !== false;
    const filledNow = prog ? prog.fill_visible : c.fill_visible !== false;
    return closedNow && filledNow;
  });
  if (completedSections.length === 0) return null;
  const theoId = new Map(scene.objects.map((o) => [o.id, o]));
  const namedPoints = scene.objects
    .filter((o) => o.type === "point3" && !o.parent && Boolean(o.xyz))
    .map((o) => ({ id: o.id, v: toVec3(o.xyz!) }));
  const matchPointIdAt = (raw: readonly string[]): string | null => {
    const p = toVec3(raw as [string, string, string]);
    const hits = namedPoints.filter(
      (cand) => Math.hypot(cand.v[0] - p[0], cand.v[1] - p[1], cand.v[2] - p[2]) <= 1e-4,
    );
    return hits.length === 1 ? hits[0]!.id : null;
  };
  const edgeKeys = new Set<string>();
  for (const sec of completedSections) {
    if (sec.endpoint_entities && sec.endpoint_entities.length >= 2) {
      const ents = sec.endpoint_entities;
      for (let i = 0; i < ents.length; i += 1) {
        const u = ents[i]?.entity_id;
        const v = ents[(i + 1) % ents.length]?.entity_id;
        if (u && v && u !== v && theoId.get(u)?.type === "point3" && theoId.get(v)?.type === "point3") {
          edgeKeys.add(capDiem(u, v));
        }
      }
    }
    if (sec.steps && sec.steps.length > 0) {
      for (const st of sec.steps) {
        const u = matchPointIdAt(st.a);
        const v = matchPointIdAt(st.b);
        if (u && v && u !== v) edgeKeys.add(capDiem(u, v));
      }
    }
    let cyclicIds: (string | null)[] = [];
    if (sec.vertex_ids && sec.vertex_ids.length >= 3) {
      cyclicIds = sec.vertex_ids.map((id) => (theoId.get(id)?.type === "point3" ? id : null));
    } else {
      const polyCoords = sec.polygon ?? sec.vertices ?? [];
      if (polyCoords.length >= 3) {
        cyclicIds = polyCoords.map((pt) => matchPointIdAt(pt));
      }
    }
    for (let i = 0; i < cyclicIds.length; i += 1) {
      const u = cyclicIds[i];
      const v = cyclicIds[(i + 1) % cyclicIds.length];
      if (u && v && u !== v) edgeKeys.add(capDiem(u, v));
    }
  }
  return edgeKeys;
}

function rankAnnotationDuplicate(entry: AnnotationEntry): number {
  const roleRank = entry.role === "given" ? 300 : entry.role === "intermediate" ? 200 : 100;
  const kindBonus = entry.kind === "distance" ? 4 : 0;
  return (entry.related ? 1000 : 0) + roleRank + entry.priority + kindBonus;
}

/**
 * Nhãn số đo của bước `step`.
 *
 * Khả dụng = cùng luật lớp lời giải: đáp số (`result`) chỉ từ sự kiện KẾT LUẬN của nó; số đo từ
 * sự kiện tính của nó; dữ kiện đề cho khi chủ thể hình học của nó đã có mặt. Ở các bước dựng người
 * học tới được (neo của bước) luật này trùng `solutionAt`; giữa hai neo nó chặt hơn — không bao giờ
 * lộ trước, ở MỌI chế độ. Chủ thể phải đang có mặt trên hình. Đại lượng `same_as` không có nhãn riêng:
 * chọn nó là chọn nhãn nó trỏ tới.
 */
export function annotationsAt(
  scene: Scene3D,
  step: number,
  view: AnnotationView,
  selectedId: string | null,
): AnnotationEntry[] {
  const k = clampStep(scene, step);
  const vatCoMat = objectsAt(scene, k);
  const coMat = new Set(vatCoMat.map((o) => o.id));
  const doan = doanCoMat(vatCoMat);
  const daTinh = new Set<string>();
  const ketLuan = new Set<string>();
  for (const e of scene.events) {
    if (e.step_index > k || !e.object) continue;
    const koLoai = !e.semantic_kind && e.action === "MEASURE";
    if (e.semantic_kind === "FINAL_RESULT" || koLoai) ketLuan.add(e.object);
    if (e.semantic_kind === "MEASUREMENT" || e.semantic_kind === "FINAL_RESULT" || koLoai) daTinh.add(e.object);
  }
  const theoId = new Map(scene.objects.map((o) => [o.id, o]));
  const chon = selectedId ? theoId.get(selectedId)?.annotation?.same_as ?? selectedId : null;
  const chuoi = chon && theoId.get(chon)?.type === "quantity" ? tangNhanManh(scene, chon) : null;
  const tieuDiem = (o: SceneObject, a: QuantityAnnotation, ownerSolidId: string | null) =>
    chon !== null
    && (chuoi
      ? o.id === chon || ["du_kien_so", "trung_gian"].includes(chuoi.get(o.id) ?? "")
      : a.subject_ids.includes(chon) || (ownerSolidId !== null && chon === ownerSolidId));
  const isHiddenId = (id: string): boolean => Boolean(view.hiddenIds?.has(id));
  const preservedHiddenWitnessById = new Map<string, AnnotationEntry>();
  const recordEvictedHiddenWitness = (evicted: AnnotationEntry | undefined): void => {
    if (evicted && isHiddenId(evicted.id) && evicted.anchor === "witness" && evicted.witness) {
      preservedHiddenWitnessById.set(evicted.id, evicted);
    }
  };
  const shouldReplaceSubjectEntry = (candidate: AnnotationEntry, prev: AnnotationEntry | undefined): boolean => {
    if (!prev) return true;
    const candHidden = isHiddenId(candidate.id);
    const prevHidden = isHiddenId(prev.id);
    if (!candHidden && prevHidden) return true;
    if (candHidden && !prevHidden) return false;
    return rankAnnotationDuplicate(candidate) > rankAnnotationDuplicate(prev);
  };
  const completedPolySectionEdges =
    !view.showAll && chon === null ? activeCompletedPolyhedralSectionEdgeKeys(scene, k, vatCoMat) : null;
  const bySubjectKey = new Map<string, AnnotationEntry>();
  for (const o of scene.objects) {
    if (o.type !== "quantity" || o.annotation?.same_as) continue;
    const exprText = hienBieuThucDaiLuong(o);
    if (!exprText) continue;
    const prov = classifyQuantityProvenance(o, scene);
    if (prov === "UNVERIFIED" || prov === "DISPLAY_ONLY") continue;
    const resolved = resolveEffectiveAnnotation(scene, o, coMat, doan, theoId);
    if (!resolved) continue;
    const { ann: a, fallbackNotation, ownerSolidId } = resolved;
    const vai = vaiTro(o, a, scene);
    if (vai !== "given" && isDerivedQuantityMetricallyUnderdetermined(scene, o)) continue;
    const khaDung =
      vai === "result"
        ? ketLuan.has(o.id)
        : daTinh.has(o.id) || prov === "GIVEN";
    if (!khaDung || !a.subject_ids.every((s) => coMat.has(s))) continue;
    // W2 · A: nhãn của một ĐOẠN chờ đoạn ấy được dựng — ở MỌI chế độ, kể cả "Hiện tất cả" và khi đang chọn nó.
    if (a.anchor === "segment" && !(a.subject_ids.length === 2 && doan.has(capDiem(a.subject_ids[0], a.subject_ids[1])))) {
      continue;
    }
    if (
      a.anchor === "pair"
      && a.kind === "angle"
      && a.subject_ids.length === 3
      && !(doan.has(capDiem(a.subject_ids[1], a.subject_ids[0])) && doan.has(capDiem(a.subject_ids[1], a.subject_ids[2])))
    ) {
      continue;
    }
    const lienQuan = tieuDiem(o, a, ownerSolidId);
    if (vai === "given" && view.hideGiven) continue;
    if (!(view.showAll || vai === "given" || lienQuan)) continue;
    if (
      vai === "given"
      && !view.showAll
      && !lienQuan
      && ownerSolidId !== null
      && coMat.has(ownerSolidId)
      && a.anchor !== "segment"
    ) {
      continue;
    }
    if (
      vai === "given"
      && !view.showAll
      && !lienQuan
      && completedPolySectionEdges !== null
      && a.anchor === "segment"
      && a.subject_ids.length === 2
      && !completedPolySectionEdges.has(capDiem(a.subject_ids[0], a.subject_ids[1]))
    ) {
      continue;
    }
    const effSym = o.notation?.trim() || fallbackNotation || o.label;
    const entry: AnnotationEntry = {
      id: o.id,
      kind: a.kind,
      role: vai,
      provenance: vai === "given" ? "GIVEN" : "DERIVED_VERIFIED",
      subject_ids: [...a.subject_ids],
      anchor: a.anchor,
      witness: a.witness,
      // F3: trên cảnh dựng theo ký hiệu, chỉ chú thích tỉ lệ dựng khi giá trị là số chuẩn hóa tại a = 1 (chưa mang tham số).
      text: `${effSym} = ${exprText}${a.unit ? ` ${a.unit}` : ""}${ghiChuGiaTriDung(scene, exprText, a.kind)}`,
      priority: (vai === "result" ? 2 : 1) + (lienQuan ? 10 : 0),
      related: lienQuan,
    };
    const key = canvasSpatialAnnotationKey(entry);
    const prev = bySubjectKey.get(key);
    if (shouldReplaceSubjectEntry(entry, prev)) {
      recordEvictedHiddenWitness(prev);
      bySubjectKey.set(key, entry);
    } else {
      recordEvictedHiddenWitness(entry);
    }
  }
  if (!view.hideGiven) {
    for (const hd of certifiedHybridGivenDimensions(scene)) {
      const [u, v] = hd.subjectIds;
      if (!coMat.has(u) || !coMat.has(v) || !doan.has(capDiem(u, v))) continue;
      const lienQuan = chon !== null && (chon === u || chon === v);
      if (
        !view.showAll
        && !lienQuan
        && completedPolySectionEdges !== null
        && !completedPolySectionEdges.has(capDiem(u, v))
      ) {
        continue;
      }
      const entry: AnnotationEntry = {
        id: hd.id,
        kind: "length",
        role: "given",
        provenance: "GIVEN",
        subject_ids: [u, v],
        anchor: "segment",
        text: `${hd.notation} = ${hd.valueDisplay}${ghiChuGiaTriDung(scene, hd.valueDisplay, "length")}`,
        priority: 1 + (lienQuan ? 10 : 0),
        related: lienQuan,
      };
      const key = canvasSpatialAnnotationKey(entry);
      const prev = bySubjectKey.get(key);
      if (shouldReplaceSubjectEntry(entry, prev)) {
        recordEvictedHiddenWitness(prev);
        bySubjectKey.set(key, entry);
      }
    }
    for (const cd of certifiedCuttingPlaneDistanceGivens(scene)) {
      const seg = cd.segmentSubjectIds;
      if (seg && coMat.has(seg[0]) && coMat.has(seg[1]) && doan.has(capDiem(seg[0], seg[1]))) {
        const lienQuan = chon !== null && (chon === seg[0] || chon === seg[1] || chon === cd.planeId);
        const entry: AnnotationEntry = {
          id: cd.id,
          kind: "distance",
          role: "given",
          provenance: "GIVEN",
          subject_ids: [seg[0], seg[1]],
          anchor: "segment",
          text: `${cd.notation} = ${cd.valueDisplay}${ghiChuGiaTriDung(scene, cd.valueDisplay, "distance")}`,
          priority: 1 + (lienQuan ? 10 : 0),
          related: lienQuan,
        };
        const key = canvasSpatialAnnotationKey(entry);
        const prev = bySubjectKey.get(key);
        if (shouldReplaceSubjectEntry(entry, prev)) {
          recordEvictedHiddenWitness(prev);
          bySubjectKey.set(key, entry);
        }
      }
    }
  }
  const activeIds = new Set([...bySubjectKey.values()].map((e) => e.id));
  const extraWitnesses = [...preservedHiddenWitnessById.values()].filter((e) => !activeIds.has(e.id));
  return [...bySubjectKey.values(), ...extraWitnesses];
}

/**
 * Tóm tắt đầy đủ mọi dữ kiện số đo `GIVEN` đã chứng thực trong cảnh tại bước `step` (phục vụ Study Dock
 * `#dock-given-params`, bảo đảm học sinh luôn đọc được dữ kiện đề cho kể cả khi viewport hẹp ẩn hộp nhãn 3D).
 */
export function givenQuantitiesSummary(scene: Scene3D, step: number): GivenQuantitySummaryEntry[] {
  const k = clampStep(scene, step);
  const vatCoMat = objectsAt(scene, k);
  const coMat = new Set(vatCoMat.map((o) => o.id));
  const doan = doanCoMat(vatCoMat);
  const exactOrigin = exactSceneOriginOf(scene);
  const exactById = new Map(exactOrigin.objects.map((obj) => [obj.id, obj]));
  const theoId = new Map(scene.objects.map((o) => [o.id, o]));
  const onCanvasIds = new Set(
    annotationsAt(scene, k, DEFAULT_ANNOTATION_VIEW, null)
      .filter((a) => a.role === "given")
      .map((a) => a.id),
  );
  const outByKey = new Map<string, GivenQuantitySummaryEntry>();
  for (const o of scene.objects) {
    if (o.type !== "quantity" || o.annotation?.same_as) continue;
    const valStr = hienBieuThucDaiLuong(o);
    if (!valStr) continue;
    if (classifyQuantityProvenance(o, scene) !== "GIVEN") continue;
    const resolved = resolveEffectiveAnnotation(scene, o, coMat, doan, theoId);
    const curvedFallback = !resolved ? resolveCurvedGivenFallback(scene, o, theoId, exactById) : null;
    // Nếu quantity có khai báo `annotation` nhưng gắn sai chủ thể (`resolved === null` và không phải tham số khối tròn xoay hợp lệ đang chờ đoạn bán kính/trục), từ chối.
    if (o.annotation && !resolved && !curvedFallback) continue;
    const effAnn = resolved?.ann;
    const effSym = o.notation?.trim() || resolved?.fallbackNotation || curvedFallback?.fallbackNotation || o.label;
    const effUnit = effAnn?.unit ?? o.annotation?.unit;
    const effKind = effAnn?.kind ?? o.annotation?.kind ?? (curvedFallback ? "length" : undefined);
    const text = `${effSym} = ${valStr}${effUnit ? ` ${effUnit}` : ""}${ghiChuGiaTriDung(scene, valStr, effKind)}`;
    const dedupKey = effAnn
      ? canonicalAnnotationSubjectKey({
          kind: effAnn.kind,
          anchor: effAnn.anchor,
          subject_ids: effAnn.subject_ids,
          witness: effAnn.witness,
        })
      : curvedFallback
        ? `curved_given|${curvedFallback.ownerSolidId}|${curvedFallback.fallbackNotation}`
        : `scalar|${o.id}|${text}`;
    const subjectReadyAtStep = effAnn
      ? (
          effAnn.subject_ids.every((s) => coMat.has(s))
          && (
            effAnn.anchor !== "segment"
            || (effAnn.subject_ids.length === 2 && doan.has(capDiem(effAnn.subject_ids[0], effAnn.subject_ids[1])))
          )
        )
      : curvedFallback
        ? coMat.has(curvedFallback.ownerSolidId) && theoId.get(curvedFallback.ownerSolidId)?.curved_kind !== "ball"
        : true;
    const entry: GivenQuantitySummaryEntry = {
      id: o.id,
      text,
      role: "given",
      provenance: "GIVEN",
      subject_ids: effAnn ? [...effAnn.subject_ids] : (curvedFallback ? [curvedFallback.ownerSolidId] : []),
      status: onCanvasIds.has(o.id)
        ? "on_canvas"
        : (effAnn || curvedFallback)
          ? (subjectReadyAtStep ? "unattached_scalar" : "pending_step")
          : "unattached_scalar",
    };
    const prev = outByKey.get(dedupKey);
    const rank = (s: GivenQuantitySummaryEntry["status"]) =>
      s === "on_canvas" ? 3 : s === "unattached_scalar" ? 2 : 1;
    if (!prev || rank(entry.status) > rank(prev.status)) {
      outByKey.set(dedupKey, entry);
    }
  }
  for (const hd of certifiedHybridGivenDimensions(scene)) {
    const dedupKey = canonicalAnnotationSubjectKey({
      kind: "length",
      anchor: "segment",
      subject_ids: hd.subjectIds,
    });
    if (outByKey.has(dedupKey)) continue;
    const hdReady =
      coMat.has(hd.subjectIds[0])
      && coMat.has(hd.subjectIds[1])
      && doan.has(capDiem(hd.subjectIds[0], hd.subjectIds[1]));
    const text = `${hd.notation} = ${hd.valueDisplay}${ghiChuGiaTriDung(scene, hd.valueDisplay, "length")}`;
    outByKey.set(dedupKey, {
      id: hd.id,
      text,
      role: "given",
      provenance: "GIVEN",
      subject_ids: [...hd.subjectIds],
      status: onCanvasIds.has(hd.id) ? "on_canvas" : hdReady ? "unattached_scalar" : "pending_step",
    });
  }
  for (const cd of certifiedCuttingPlaneDistanceGivens(scene)) {
    const subj = cd.segmentSubjectIds ?? [cd.centerId, cd.planeId];
    const dedupKey = canonicalAnnotationSubjectKey({
      kind: "distance",
      anchor: cd.segmentSubjectIds ? "segment" : "pair",
      subject_ids: subj,
    });
    if (outByKey.has(dedupKey)) continue;
    const cdReady = cd.segmentSubjectIds
      ? (
          coMat.has(cd.segmentSubjectIds[0])
          && coMat.has(cd.segmentSubjectIds[1])
          && doan.has(capDiem(cd.segmentSubjectIds[0], cd.segmentSubjectIds[1]))
        )
      : (coMat.has(cd.centerId) && coMat.has(cd.planeId));
    const text = `${cd.notation} = ${cd.valueDisplay}${ghiChuGiaTriDung(scene, cd.valueDisplay, "distance")}`;
    outByKey.set(dedupKey, {
      id: cd.id,
      text,
      role: "given",
      provenance: "GIVEN",
      subject_ids: [...subj],
      status: onCanvasIds.has(cd.id) ? "on_canvas" : cdReady ? "unattached_scalar" : "pending_step",
    });
  }
  const outByText = new Map<string, GivenQuantitySummaryEntry>();
  const rankStatus = (s: GivenQuantitySummaryEntry["status"]) =>
    s === "on_canvas" ? 3 : s === "unattached_scalar" ? 2 : 1;
  for (const entry of outByKey.values()) {
    const textKey = entry.text.trim();
    const prev = outByText.get(textKey);
    if (!prev || rankStatus(entry.status) > rankStatus(prev.status)) {
      outByText.set(textKey, entry);
    }
  }
  return [...outByText.values()];
}

/** `vai`: nhân chứng của nhãn khoảng cách đang xét (`khoang_cach`) hay đoạn vuông góc phụ của điểm hình chiếu
 *  (`hinh_chieu`) — renderer chọn màu theo vai (`scene3d-view.tsx::mauNhanChung`), không theo tiền tố id. */
export interface WitnessShown {
  id: string; vai: "khoang_cach" | "hinh_chieu"; from: Vec3; foot: Vec3; u: Vec3; v: Vec3;
  /** Toạ độ điểm CÓ TÊN `marker.u_to` (backend) — đầu kia của đoạn chứng minh trong vật nhận; vắng ⇒ không vẽ đoạn. */
  uTo?: Vec3;
  /** Dấu thứ hai của đoạn vuông góc chung: đoạn chân → `from` đã do dấu thứ nhất vẽ. */
  khongVeDoan?: true;
}

type NhanChungBackend = NonNullable<QuantityAnnotation["witness"]>;

/** Nhân chứng backend → `WitnessShown` đã qua cổng `scene3d-witness-gate` (fail-closed); không hợp lệ ⇒ `[]`. */
function nhanChungDaKiem(
  scene: Scene3D, theoId: ReadonlyMap<string, SceneObject>, id: string, vai: WitnessShown["vai"], w: NhanChungBackend,
): WitnessShown[] {
  const tu = w.from_point ?? theoId.get(w.from)?.xyz;
  if (!tu) return [];
  const dau = (from: Vec3, foot: Vec3, m: NhanChungBackend["marker"], on: string, khongVeDoan?: true): WitnessShown[] => {
    const dich = m.u_to ? theoId.get(m.u_to)?.xyz : undefined;
    if (m.u_to && !dich) return [];
    const ws: WitnessShown = { id, vai, from, foot, u: toVec3(m.u), v: toVec3(m.v), ...(dich ? { uTo: toVec3(dich) } : {}),
      ...(khongVeDoan ? { khongVeDoan } : {}) };
    return nhanChungVuongGocHopLe(scene, ws, on) ? [ws] : [];
  };
  const mot = dau(toVec3(tu), toVec3(w.foot), w.marker, w.on);
  if (!w.second) return mot;
  // Đoạn vuông góc chung: dấu ở chân kia (chính là `from_point`); một trong hai sai ⇒ không vẽ cả cặp.
  const hai = w.from_point ? dau(toVec3(w.foot), toVec3(w.second.foot), w.second.marker, w.second.on, true) : [];
  return mot.length === 1 && hai.length === 1 && w.second.foot.every((x, i) => x === w.from_point![i]) ? [...mot, ...hai] : [];
}

/** §16.7 — nhân chứng của các nhãn khoảng cách ĐANG HIỆN; toạ độ đều do backend phát (chân chính xác). */
export function witnessesShown(scene: Scene3D, entries: AnnotationEntry[]): WitnessShown[] {
  const theoId = new Map(scene.objects.map((o) => [o.id, o]));
  return entries.flatMap((e) =>
    e.anchor === "witness" && e.witness ? nhanChungDaKiem(scene, theoId, e.id, "khoang_cach", e.witness) : []);
}

/** Review I1 — đoạn vuông góc PHỤ của điểm dựng bằng hình chiếu (`perpendicular_witness`, chân do kernel tính) khi
 *  điểm ấy CÓ MẶT ở bước đang xem (`present` = id của `objectsAt`). Không thuộc khối, không phải chiều cao. */
export function projectionWitnessesAt(
  scene: Scene3D,
  present: ReadonlySet<string>,
  step?: number,
): WitnessShown[] {
  const theoId = new Map(scene.objects.map((o) => [o.id, o]));
  const tuDiem = scene.objects.flatMap((o) => {
    const w = o.type === "point3" && present.has(o.id) ? o.perpendicular_witness : undefined;
    return w && present.has(w.from) ? nhanChungDaKiem(scene, theoId, `perpendicular:${o.id}`, "hinh_chieu", w) : [];
  });
  const daCo = new Set(tuDiem.map((w) => `${w.from.join(",")}|${w.foot.join(",")}`));
  const k = step !== undefined && scene.events?.length ? clampStep(scene, step) : undefined;
  const ketLuan = new Set<string>();
  if (k !== undefined) {
    for (const e of scene.events) {
      if (e.step_index > k || !e.object) continue;
      if (e.semantic_kind === "FINAL_RESULT" || (!e.semantic_kind && e.action === "MEASURE")) ketLuan.add(e.object);
    }
  }
  // Owner 2026-10-26: KHÔNG còn nhánh tự suy "đường ⊥ mặt" từ chữ "⊥"/"90°"/cos = 0 của một đại lượng và toạ độ
  // float. Góc vuông của một phép đo có nhân chứng BACKEND (`quantity_annotations._goc_vuong`) và đi qua `tuKetQua`.
  if (k === undefined || ketLuan.size === 0) return tuDiem;
  const tuKetQua = scene.objects.flatMap((o) => {
    const ann = o.type === "quantity" && ketLuan.has(o.id) ? o.annotation : undefined;
    if (!ann) return [];
    const w = vaiTro(o, ann, scene) === "result" && ann.anchor === "witness" ? ann.witness : undefined;
    if (!w || !present.has(w.from) || !ann.subject_ids.every((s) => present.has(s))) return [];
    const ws = nhanChungDaKiem(scene, theoId, `perpendicular:${o.id}`, "hinh_chieu", w);
    return ws.filter((x) => !daCo.has(`${x.from.join(",")}|${x.foot.join(",")}`));
  });
  return [...tuDiem, ...tuKetQua];
}

/** Ô soi (§16.6): dữ kiện số trong chuỗi của đại lượng (`tangNhanManh`) và đầu vào trực tiếp
 *  (`numericalBasis`) — đọc từ cảnh backend phát, không tính gì. */
export function quantitySources(scene: Scene3D, id: string): { givens: string[]; inputs: string[] } {
  const o = scene.objects.find((x) => x.id === id);
  if (!o || o.type !== "quantity") return { givens: [], inputs: [] };
  const chuoi = tangNhanManh(scene, id);
  return {
    givens: scene.objects
      .filter(
        (x) =>
          x.type === "quantity"
          && chuoi.get(x.id) === "du_kien_so"
          && classifyQuantityProvenance(x, scene) === "GIVEN",
      )
      .map((x) => x.id),
    inputs: numericalBasis(scene, o),
  };
}

/** Trung bình toạ độ — phép đặt chỗ, không phải suy luận hình học. */
function trungBinh(ps: Vec3[]): Vec3 | null {
  if (ps.length === 0) return null;
  const s = ps.reduce<Vec3>((a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]], [0, 0, 0]);
  return [s[0] / ps.length, s[1] / ps.length, s[2] / ps.length];
}

/**
 * Điểm neo THẾ GIỚI của một nhãn, từ đúng chủ thể backend chỉ: đoạn → trung điểm hai điểm ·
 * miền/khối → trung bình các đỉnh · cặp → ĐIỂM của cặp ("d(S, BD)" đứng cạnh S) · nhân chứng →
 * trung điểm điểm–chân, chân do BACKEND phát (§16.7). Chỉ trung bình toạ độ backend đã phát: chân
 * đường vuông góc, giao tuyến, góc là suy luận hình học, CẤM ở phía trình bày (`scene3d.test.tsx` 5D)
 * — kể cả để đặt nhãn. Không neo được ⇒ `null` (không hiện).
 */
export function annotationAnchor(
  scene: Scene3D,
  a: Pick<AnnotationEntry, "anchor" | "subject_ids"> & { witness?: AnnotationEntry["witness"] },
): Vec3 | null {
  if (a.anchor === "witness") {
    const tu = a.witness?.from_point ?? (a.witness ? scene.objects.find((o) => o.id === a.witness!.from)?.xyz : undefined);
    return tu ? trungBinh([toVec3(tu), toVec3(a.witness!.foot)]) : null;
  }
  const byId = new Map(scene.objects.map((o) => [o.id, o]));
  const diem = (id: string): Vec3 | null => {
    const o = byId.get(id);
    return o?.xyz ? toVec3(o.xyz) : null;
  };
  const dinh = (o: SceneObject): Vec3[] => (o.vertex_ids?.length
    ? o.vertex_ids.map(diem).filter((p): p is Vec3 => p !== null)
    : (o.polygon ?? o.vertices ?? []).map(toVec3));
  const chu = a.subject_ids.map((id) => byId.get(id));
  if (chu.length === 0 || chu.some((o) => !o)) return null;
  const vat = chu as SceneObject[];
  if (a.anchor === "segment") {
    if (vat.length !== 2 || a.subject_ids[0] === a.subject_ids[1]) return null;
    if (!vat.every((o) => o.type === "point3" && Boolean(o.xyz))) return null;
    const p = vat.map((o) => toVec3(o.xyz!));
    return trungBinh([p[0], p[1]]);
  }
  if (a.anchor === "pair" && vat.length === 3 && vat.every((o) => o.type === "point3" && Boolean(o.xyz))) {
    return toVec3(vat[1].xyz!);
  }
  if (a.anchor === "region" || a.anchor === "solid") {
    const ds = dinh(vat[0]);
    if (ds.length > 0) return trungBinh(ds);
    const tamRaw = vat[0].anchor ?? vat[0].center;
    if (tamRaw) {
      const tam = toVec3(tamRaw);
      const bk = vat[0].radius_sq != null ? Math.sqrt(Math.max(0, toNumber(vat[0].radius_sq))) : 0;
      if (vat[0].type === "curved_solid" && vat[0].curved_kind === "ball" && bk > 1e-6) {
        for (const depId of vat[0].depends ?? []) {
          const pt = diem(depId);
          if (!pt) continue;
          const dist = Math.hypot(pt[0] - tam[0], pt[1] - tam[1], pt[2] - tam[2]);
          if (Math.abs(dist - bk) <= 1e-3 * Math.max(1, bk)) {
            return [
              tam[0] + (pt[0] - tam[0]) * 0.55,
              tam[1] + (pt[1] - tam[1]) * 0.55,
              tam[2] + (pt[2] - tam[2]) * 0.55,
            ];
          }
        }
        return [
          tam[0] + (12 / 25) * bk * 0.55,
          tam[1] - (9 / 25) * bk * 0.55,
          tam[2] - (20 / 25) * bk * 0.55,
        ];
      }
      const nVec = vat[0].normal
        ? toVec3(vat[0].normal)
        : vat[0].apex_or_top
          ? ([
              toNumber(vat[0].apex_or_top[0]) - tam[0],
              toNumber(vat[0].apex_or_top[1]) - tam[1],
              toNumber(vat[0].apex_or_top[2]) - tam[2],
            ] as Vec3)
          : ([0, 0, 1] as Vec3);
      const hxy = Math.hypot(nVec[0], nVec[1]);
      if (hxy > 1e-6) {
        return [
          tam[0] + (-nVec[1] / hxy) * bk * 0.55,
          tam[1] + (nVec[0] / hxy) * bk * 0.55,
          tam[2],
        ];
      }
      return [tam[0] + bk * 0.55, tam[1], tam[2]];
    }
    return null;
  }
  const diemCuaCap = vat.find((o) => o.xyz);
  return diemCuaCap?.xyz ? toVec3(diemCuaCap.xyz) : null;
}

export interface LabelRect { x: number; y: number; w: number; h: number }
export interface LabelToPlace { id: string; ax: number; ay: number; w: number; h: number; priority: number }

/** §15.5: khoảng tối đa (px CSS) từ điểm neo chiếu tới điểm gần nhất của hộp nhãn. */
export const NEO_TOI_DA = 24;
/** Khe giữa điểm neo và cạnh hộp nhãn — vòng gần trước, xa dần; góc ở khe k cách neo k√2, nên
 *  vòng 18 chỉ còn bốn phía (`NEO_TOI_DA` loại góc). */
const KHE = [6, 12, 18];

const giao = (a: LabelRect, b: LabelRect) =>
  a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h;
const cachNeo = (r: LabelRect, ax: number, ay: number) =>
  Math.hypot(Math.max(r.x - ax, 0, ax - r.x - r.w), Math.max(r.y - ay, 0, ay - r.y - r.h));

/**
 * Đặt hộp nhãn số đo (toạ độ px CSS trong khung `view`). Ưu tiên cao đặt trước; mỗi nhãn thử,
 * theo từng vòng khe `KHE`, trên · dưới · phải · trái điểm neo rồi bốn góc (lượt trình duyệt T7:
 * nhãn đáy kẹp giữa hai nhãn cạnh hết cả bốn phía, rồi chạm một nhãn nửa px ở vòng sát nhất), kẹp
 * vào khung, bỏ chỗ nào xa neo quá `NEO_TOI_DA` hoặc giao một hộp đã có (`chan`: nhãn điểm, nút
 * điều khiển, nhãn số đo đã đặt). Hết chỗ ⇒ không đặt. Tất định: cùng đầu vào, cùng kết quả —
 * không xê dịch dần, không ngẫu nhiên.
 */
export function placeAnnotationLabels(
  items: LabelToPlace[],
  chan: LabelRect[],
  view: { w: number; h: number },
  tranhUuTien: LabelRect[] = [],
): Map<string, LabelRect> {
  const giu = new Map<string, LabelRect>();
  const daChiem = [...chan];
  for (const n of [...items].sort((a, b) => b.priority - a.priority || a.id.localeCompare(b.id))) {
    if (n.ax < 0 || n.ay < 0 || n.ax > view.w || n.ay > view.h || n.w > view.w || n.h > view.h) continue;
    const ung: LabelRect[] = KHE.flatMap((k) => {
      const [tren, duoi, phai, trai] = [n.ay - k - n.h, n.ay + k, n.ax + k, n.ax - k - n.w];
      return [
        { x: n.ax - n.w / 2, y: tren }, { x: n.ax - n.w / 2, y: duoi },
        { x: phai, y: n.ay - n.h / 2 }, { x: trai, y: n.ay - n.h / 2 },
        { x: phai, y: tren }, { x: trai, y: tren }, { x: phai, y: duoi }, { x: trai, y: duoi },
      ];
    }).map((r) => ({ ...r, w: n.w, h: n.h })).map((r) => ({ ...r, x: Math.min(Math.max(r.x, 0), view.w - r.w), y: Math.min(Math.max(r.y, 0), view.h - r.h) }));
    const r =
      (tranhUuTien.length > 0
        ? ung.find(
            (c) =>
              cachNeo(c, n.ax, n.ay) <= NEO_TOI_DA
              && !daChiem.some((b) => giao(c, b))
              && !tranhUuTien.some((b) => giao(c, b)),
          )
        : undefined)
      ?? ung.find((c) => cachNeo(c, n.ax, n.ay) <= NEO_TOI_DA && !daChiem.some((b) => giao(c, b)));
    if (!r) continue;
    giu.set(n.id, r);
    daChiem.push(r);
  }
  return giu;
}
