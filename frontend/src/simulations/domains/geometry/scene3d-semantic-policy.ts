/**
 * scene3d-semantic-policy.ts — CHÍNH SÁCH BIỂU DIỄN NGỮ NGHĨA THỐNG NHẤT CHO SCENE3D.
 *
 * ─── MỤC TIÊU NGHIÊN CỨU & SƯ PHẠM ───────────────────────────────────────
 *
 * Tầng trình bày Scene3D xác định vai trò toán học, trạng thái nhận thức
 * (`given` / `constructed_result` / `auxiliary` / `explained_focus`), màu sắc,
 * độ đục, độ dày nét, kiểu nét, quy tắc hiện/ẩn mặc định theo ngữ nghĩa và thứ
 * bậc thị giác 5 tầng hoàn toàn từ hợp đồng hình học (`Scene3D` contract) đã được
 * backend xác minh, đối chiếu chuẩn với HTML tham chiếu hình học.
 *
 * Bất biến kiến trúc:
 * - Không hardcode theo ID bài mẫu, tên đề, nhãn đỉnh hay họ hình riêng lẻ.
 * - Không biến đổi dữ liệu `Scene3D`, không tạo thực thể hình học có thẩm quyền
 *   mới (`GIVEN`), không tự suy diễn ký hiệu góc vuông / song song chưa được chứng nhận.
 * - Tương tác hover / click / chọn đối tượng giữ nguyên màu ngữ nghĩa toán học.
 */

import * as THREE from "three";
import {
  cauTrucGocNhin,
  certifiedCuttingPlaneDistanceGivens,
  clampStep,
  classifyQuantityProvenance,
  classifySceneEntityProvenance,
  dayVaDinhChop,
  derivedSceneParentOf,
  diemChoDuong,
  diemHuuHan,
  doanDuongThang,
  duongKinhCanh,
  exactSceneOriginOf,
  geometryActionLabelAt,
  geometryJustificationsAt,
  geometryNarrationAt,
  geometryStepOf,
  geometryTimeline,
  ghiChuGiaTriDung,
  hienBieuThucDaiLuong,
  hybridViewOfScene,
  isSceneWorldTransformed,
  learnerTextIsSafe,
  measurementOnlyPlanes,
  objectsAt,
  propagateSceneLineage,
  registerExactSceneOrigin,
  toNumber,
  toVec3,
  type CanonicalMathProvenance,
  type Exact,
  type ExactVec3,
  type FormationStep,
  type GeometryProgress,
  type Scene3D,
  type SceneEvent,
  type SceneObject,
  type Vec3,
} from "./scene3d-model";
import { annotationsAt, DEFAULT_ANNOTATION_VIEW } from "./scene3d-annotations";
import { auxiliaryHiddenAt, auxiliaryObjects } from "./scene3d-auxiliary";
import { diemTaiDinhThietDien, isSubEntity, laDiemPhuDungMatPhang, parentSolidOf, sectionDetails, withSubEntities } from "./scene3d-subentities";
import { maTranKhung } from "./scene3d-chart";
import { chonHuongNhin, huongLenHienThi, type Diem3, type TuyChonHuongNhin } from "./scene3d-camera";
import { PHONG_CACH_SCENE3D, hexCss, vaiTroMien } from "./scene3d-roles";
import { nhanChungDoanHopLe } from "./scene3d-witness-gate";

export type SemanticRoleId =
  | "SOLID_SHELL"
  | "GEOMETRIC_PLANE"
  | "RESULT_SECTION"
  | "INSCRIBED_CIRCLE"
  | "CIRCUMSCRIBED_CIRCLE"
  | "INSCRIBED_SPHERE"
  | "CIRCUMSCRIBED_SPHERE"
  | "REFERENCE_EQUATOR"
  | "REFERENCE_GREAT_CIRCLE"
  | "BOUNDARY_AND_INTERSECTION"
  | "AUXILIARY_CONSTRUCTION"
  | "HIDDEN_EDGE"
  | "CERTIFIED_RELATION_MARKER";

export type SphereSemanticRole =
  | "STANDALONE_SPHERE"
  | "INSCRIBED_SPHERE"
  | "CIRCUMSCRIBED_SPHERE";

export type CircleSemanticRole =
  | "REFERENCE_EQUATOR"
  | "REFERENCE_GREAT_CIRCLE"
  | "BOUNDARY_AND_INTERSECTION"
  | "INSCRIBED_CIRCLE"
  | "CIRCUMSCRIBED_CIRCLE"
  | "RESULT_SECTION";

export type InteractionVisualState = "neutral" | "hover" | "selected" | "context";

export type EpistemicStatus =
  | "given"
  | "constructed_result"
  | "auxiliary"
  | "explained_focus";

export type PlaneSemanticSubRole =
  | "MANDATORY_STUDIED_PLANE"
  | "SPATIAL_RELATION_PLANE"
  | "CONSTRUCTION_TOOL_PLANE"
  | "SOLID_FACE_DUPLICATE_PLANE";

export interface SemanticRoleSpec {
  role: SemanticRoleId;
  labelVi: string;
  colorHex: string;
  accentHex?: string;
  opacity: number;
  selectedOpacity: number;
  strokeWidthPx: number;
  hiddenStrokeWidthPx?: number;
  lineStyle: "solid" | "dashed" | "solid_visible_dashed_hidden" | "thin_frame" | "certified_square_and_drop";
  /** Thứ bậc nổi bật thị giác 1..5 (1 = Kết quả chính cao nhất, 5 = Lưới & nền thấp nhất). */
  prominenceTier: 1 | 2 | 3 | 4 | 5;
  /** Dấu hiệu phân biệt phi màu sắc (bề dày, nét đứt, ký hiệu, nhãn). */
  nonColorCue: string;
}

const S = PHONG_CACH_SCENE3D;

export const SEMANTIC_ROLE_SPECS: Readonly<Record<SemanticRoleId, SemanticRoleSpec>> = {
  RESULT_SECTION: {
    role: "RESULT_SECTION",
    labelVi: "Thiết diện hoặc miền giao kết quả",
    colorHex: hexCss(S.colors.polygon),
    accentHex: hexCss(S.colors.line),
    opacity: S.opacity.section,
    selectedOpacity: S.opacity.selectedSection,
    strokeWidthPx: S.fatPx.section,
    hiddenStrokeWidthPx: S.fatPx.hiddenSection,
    lineStyle: "solid_visible_dashed_hidden",
    prominenceTier: 1,
    nonColorCue: "Viền dày nhất khung (4.5px), vùng tô cam đất rõ (0.32) và huy hiệu đỉnh thiết diện vai-thiet-dien",
  },
  INSCRIBED_CIRCLE: {
    role: "INSCRIBED_CIRCLE",
    labelVi: "Đường tròn nội tiếp",
    colorHex: hexCss(S.colors.inscribed),
    opacity: S.opacity.inscribedCircleFill,
    selectedOpacity: 0.14,
    strokeWidthPx: 3.4,
    hiddenStrokeWidthPx: 2.35,
    lineStyle: "solid_visible_dashed_hidden",
    prominenceTier: 2,
    nonColorCue: "Vành cam hổ phách tiếp xúc các cạnh đa giác chủ kèm tô nhẹ 0.08 và phân đoạn thấy/khuất theo mặt chứa",
  },
  CIRCUMSCRIBED_CIRCLE: {
    role: "CIRCUMSCRIBED_CIRCLE",
    labelVi: "Đường tròn ngoại tiếp",
    colorHex: hexCss(S.colors.circumscribedCircle),
    opacity: 0,
    selectedOpacity: 0,
    strokeWidthPx: 3.4,
    hiddenStrokeWidthPx: 2.35,
    lineStyle: "solid_visible_dashed_hidden",
    prominenceTier: 2,
    nonColorCue: "Vành xanh lam không tô nền đi qua các đỉnh đa giác, liền ngoài khối và đứt đoạn bị khối che",
  },
  INSCRIBED_SPHERE: {
    role: "INSCRIBED_SPHERE",
    labelVi: "Mặt cầu nội tiếp",
    colorHex: hexCss(S.colors.inscribed),
    opacity: S.opacity.inscribedSphereShell,
    selectedOpacity: 0.22,
    strokeWidthPx: 2.0,
    hiddenStrokeWidthPx: 1.8,
    lineStyle: "dashed",
    prominenceTier: 2,
    nonColorCue: "Vỏ cầu cam hổ phách trong suốt (0.16) không đường bao đen, đường tròn lớn tham chiếu nét đứt nằm trong khối",
  },
  CIRCUMSCRIBED_SPHERE: {
    role: "CIRCUMSCRIBED_SPHERE",
    labelVi: "Mặt cầu ngoại tiếp",
    colorHex: hexCss(S.colors.circumscribedSphere),
    opacity: S.opacity.circumscribedSphereShell,
    selectedOpacity: 0.14,
    strokeWidthPx: 2.0,
    hiddenStrokeWidthPx: 1.75,
    lineStyle: "solid_visible_dashed_hidden",
    prominenceTier: 2,
    nonColorCue: "Vỏ cầu xanh ngọc rất mảnh (0.085) không đường bao đen, không che cạnh khối nội tiếp, đường tròn lớn tham chiếu nửa trước liền nửa sau đứt",
  },
  CERTIFIED_RELATION_MARKER: {
    role: "CERTIFIED_RELATION_MARKER",
    labelVi: "Đường cao, chân vuông góc và quan hệ đã xác minh",
    colorHex: hexCss(S.colors.line),
    opacity: S.opacity.witness,
    selectedOpacity: 1,
    strokeWidthPx: S.fatPx.perpendicular,
    hiddenStrokeWidthPx: S.fatPx.hiddenPerpendicular,
    lineStyle: "certified_square_and_drop",
    prominenceTier: 2,
    nonColorCue: "Ô vuông hai đoạn 16–22px tại chân vuông góc kèm đoạn hạ vuông góc chỉ dựng khi có witness từ kernel",
  },
  SOLID_SHELL: {
    role: "SOLID_SHELL",
    labelVi: "Vỏ khối hình học trung tính",
    colorHex: hexCss(S.colors.mesh),
    accentHex: hexCss(S.colors.secondaryMesh),
    opacity: S.opacity.solid,
    selectedOpacity: S.opacity.selectedSolid,
    strokeWidthPx: S.fatPx.edge,
    hiddenStrokeWidthPx: S.fatPx.hiddenEdge,
    lineStyle: "solid_visible_dashed_hidden",
    prominenceTier: 3,
    nonColorCue: "Hai lượt vỏ bán trong suốt không đèn (0.12) kèm cạnh biên 3.6px nhường độ nổi bật cho thiết diện",
  },
  BOUNDARY_AND_INTERSECTION: {
    role: "BOUNDARY_AND_INTERSECTION",
    labelVi: "Đường biên khối và giao tuyến chính",
    colorHex: hexCss(S.colors.canh),
    accentHex: hexCss(S.colors.sectionOutline),
    opacity: 1,
    selectedOpacity: 1,
    strokeWidthPx: S.fatPx.edge,
    hiddenStrokeWidthPx: S.fatPx.hiddenEdge,
    lineStyle: "solid_visible_dashed_hidden",
    prominenceTier: 3,
    nonColorCue: "Độ dày chuẩn 3.6px với chủ quyền nét duy nhất (không vẽ chồng hai lớp cạnh)",
  },
  HIDDEN_EDGE: {
    role: "HIDDEN_EDGE",
    labelVi: "Cạnh khuất sau vỏ khối hoặc mặt cong",
    colorHex: hexCss(S.colors.hiddenEdge),
    opacity: S.opacity.hiddenEdge,
    selectedOpacity: 0.9,
    strokeWidthPx: S.fatPx.hiddenEdge,
    lineStyle: "dashed",
    prominenceTier: 3,
    nonColorCue: "Chu kỳ nét đứt tỷ lệ cảnh (gapRatio 0.72) phân biệt tức thì phần khuất mà không phụ thuộc màu",
  },
  GEOMETRIC_PLANE: {
    role: "GEOMETRIC_PLANE",
    labelVi: "Mặt phẳng hình học",
    colorHex: hexCss(S.colors.surface),
    opacity: S.opacity.plane,
    selectedOpacity: S.opacity.selectedPlane,
    strokeWidthPx: S.fatPx.plane,
    lineStyle: "thin_frame",
    prominenceTier: 4,
    nonColorCue: "Tấm phẳng cắt theo đáy z >= z_min với nền tím trong suốt (0.085), khung viền 2.7px và nhãn ký hiệu góc (α), (P)",
  },
  AUXILIARY_CONSTRUCTION: {
    role: "AUXILIARY_CONSTRUCTION",
    labelVi: "Đường và miền dựng phụ trợ",
    colorHex: hexCss(S.colors.line),
    opacity: S.opacity.auxiliary,
    selectedOpacity: 0.92,
    strokeWidthPx: S.fatPx.auxiliary,
    hiddenStrokeWidthPx: S.fatPx.hiddenAuxiliary,
    lineStyle: "solid_visible_dashed_hidden",
    prominenceTier: 4,
    nonColorCue: "Nét mảnh 2.1px (nhỏ hơn cạnh khối 3.6px), đoạn kéo dài gọn (14%) và thu gọn khi hoàn tất dựng",
  },
  REFERENCE_EQUATOR: {
    role: "REFERENCE_EQUATOR",
    labelVi: "Đường tròn lớn tham chiếu của mặt cầu",
    colorHex: hexCss(S.colors.hiddenEdge),
    opacity: S.opacity.hiddenRim,
    selectedOpacity: 0.8,
    strokeWidthPx: 2.0,
    hiddenStrokeWidthPx: 1.75,
    lineStyle: "solid_visible_dashed_hidden",
    prominenceTier: 4,
    nonColorCue: "Vòng tham chiếu phi thẩm quyền (authoritative: false), mảnh hơn biên khối và không bao giờ thành thực thể GIVEN",
  },
  REFERENCE_GREAT_CIRCLE: {
    role: "REFERENCE_GREAT_CIRCLE",
    labelVi: "Đường tròn lớn tham chiếu",
    colorHex: hexCss(S.colors.hiddenEdge),
    opacity: 0.24,
    selectedOpacity: 0.65,
    strokeWidthPx: 1.85,
    hiddenStrokeWidthPx: 1.6,
    lineStyle: "solid_visible_dashed_hidden",
    prominenceTier: 4,
    nonColorCue: "Đường tròn lớn tham chiếu 3D qua tâm mặt cầu (authoritative: false), nửa trước liền mảnh nửa sau đứt, tự giảm độ nổi bật khi có mặt phẳng cắt và đường tròn giao tuyến",
  },
};

function hueDiffDeg(aHex: number, bHex: number): number {
  const a = { h: 0, s: 0, l: 0 };
  const b = { h: 0, s: 0, l: 0 };
  new THREE.Color(aHex).getHSL(a, THREE.SRGBColorSpace);
  new THREE.Color(bHex).getHSL(b, THREE.SRGBColorSpace);
  if (a.s < 0.05 && b.s < 0.05) return 0;
  const d = Math.abs(a.h - b.h) * 360;
  return d > 180 ? 360 - d : d;
}

/**
 * Điều biến độ đậm/độ sáng của màu ngữ nghĩa theo trạng thái tương tác mà KHÔNG BAO GIỜ
 * đổi sang họ màu khác (`|Δhue| < 1.5°`).
 */
export function modulateSemanticColor(
  baseHex: number,
  state: InteractionVisualState,
): number {
  if (state === "neutral" || state === "context") return baseHex;
  const c = new THREE.Color(baseHex);
  const hsl = { h: 0, s: 0, l: 0 };
  c.getHSL(hsl, THREE.SRGBColorSpace);
  if (hsl.s < 0.05) {
    const deltaL = state === "selected" ? -0.05 : -0.025;
    c.setHSL(hsl.h, hsl.s, Math.max(0.06, Math.min(0.92, hsl.l + deltaL)), THREE.SRGBColorSpace);
    return c.getHex();
  }
  const nextS = Math.min(0.96, hsl.s + (state === "selected" ? 0.045 : 0.02));
  const deltaL = hsl.l < 0.25
    ? (state === "selected" ? 0.055 : 0.03)
    : (state === "selected" ? -0.055 : -0.03);
  const nextL = Math.max(0.08, Math.min(0.88, hsl.l + deltaL));
  c.setHSL(hsl.h, nextS, nextL, THREE.SRGBColorSpace);
  const hex = c.getHex();
  return hueDiffDeg(hex, baseHex) < 1.5 ? hex : baseHex;
}

function normalFromPoints(pts: readonly Diem3[]): Diem3 | null {
  if (pts.length < 3) return null;
  const a = pts[0];
  for (let i = 1; i < pts.length - 1; i += 1) {
    const b = pts[i];
    for (let j = i + 1; j < pts.length; j += 1) {
      const c = pts[j];
      const ux = b[0] - a[0], uy = b[1] - a[1], uz = b[2] - a[2];
      const vx = c[0] - a[0], vy = c[1] - a[1], vz = c[2] - a[2];
      const nx = uy * vz - uz * vy;
      const ny = uz * vx - ux * vz;
      const nz = ux * vy - uy * vx;
      const len = Math.hypot(nx, ny, nz);
      if (len > 1e-6) return [nx / len, ny / len, nz / len];
    }
  }
  return null;
}

/**
 * Phân biệt 3 vai trò mặt cầu từ hợp đồng `Scene3D`:
 * - `STANDALONE_SPHERE`: mặt cầu độc lập (ví dụ bài thể tích mặt cầu, mặt phẳng cắt mặt cầu).
 * - `INSCRIBED_SPHERE`: mặt cầu nội tiếp khối đa diện / hình nón / hình trụ trong cảnh.
 * - `CIRCUMSCRIBED_SPHERE`: mặt cầu ngoại tiếp khối đa diện / hình nón / hình trụ trong cảnh.
 */
export function classifySphereSemanticRole(
  scene: Pick<Scene3D, "objects">,
  o: SceneObject,
): SphereSemanticRole {
  if (o.semantic_role === "INSCRIBED_SPHERE") return "INSCRIBED_SPHERE";
  if (o.semantic_role === "CIRCUMSCRIBED_SPHERE") return "CIRCUMSCRIBED_SPHERE";
  if (o.semantic_role === "STANDALONE_SPHERE") return "STANDALONE_SPHERE";
  if (o.type !== "curved_solid" || o.curved_kind !== "ball" || !o.anchor) {
    return "STANDALONE_SPHERE";
  }
  const hasTangentOrCircumLineage =
    o.origin === "derived"
    || (o.depends?.length ?? 0) > 0
    || /\b(ngoại|nội)\s+tiếp\b/iu.test(`${o.label ?? ""} ${o.role ?? ""}`);
  if (!hasTangentOrCircumLineage) {
    return "STANDALONE_SPHERE";
  }

  const center = toVec3(o.anchor);
  const rSq = o.radius_sq ? toNumber(o.radius_sq) : 0;
  const r = rSq > 0
    ? Math.sqrt(rSq)
    : o.rim_point
      ? Math.hypot(...toVec3(o.rim_point).map((v, k) => v - center[k]))
      : 0;
  if (!(r > 1e-6)) return "STANDALONE_SPHERE";
  const tol = 1e-3 * Math.max(1, r);

  for (const s of scene.objects) {
    if (s.id === o.id) continue;
    if (s.type === "solid" && s.vertices && s.vertices.length >= 4 && s.faces && s.faces.length >= 4) {
      const verts = s.vertices.map(toVec3);
      const allVertsOnSphere = verts.every(
        (v) => Math.abs(Math.hypot(v[0] - center[0], v[1] - center[1], v[2] - center[2]) - r) <= tol,
      );
      if (allVertsOnSphere) return "CIRCUMSCRIBED_SPHERE";

      const centroid: Vec3 = [
        verts.reduce((acc, v) => acc + v[0], 0) / verts.length,
        verts.reduce((acc, v) => acc + v[1], 0) / verts.length,
        verts.reduce((acc, v) => acc + v[2], 0) / verts.length,
      ];
      let allInside = true;
      let tangentFaces = 0;
      let validFaces = 0;
      for (const f of s.faces) {
        const fPts = f.map((idx) => verts[idx]).filter(Boolean);
        const nRaw = normalFromPoints(fPts);
        if (!nRaw) continue;
        validFaces += 1;
        const a = fPts[0];
        const outDot = nRaw[0] * (a[0] - centroid[0]) + nRaw[1] * (a[1] - centroid[1]) + nRaw[2] * (a[2] - centroid[2]);
        const n: Vec3 = outDot < 0 ? [-nRaw[0], -nRaw[1], -nRaw[2]] : [nRaw[0], nRaw[1], nRaw[2]];
        const signedDist = n[0] * (a[0] - center[0]) + n[1] * (a[1] - center[1]) + n[2] * (a[2] - center[2]);
        if (signedDist < r - tol) {
          allInside = false;
          break;
        }
        if (Math.abs(signedDist - r) <= tol) tangentFaces += 1;
      }
      if (allInside && validFaces >= 4 && tangentFaces >= 4) {
        return "INSCRIBED_SPHERE";
      }
    }

    if (
      s.type === "curved_solid"
      && (s.curved_kind === "cone" || s.curved_kind === "cylinder")
      && s.anchor
    ) {
      const A = toVec3(s.anchor);
      const rsSq = s.radius_sq ? toNumber(s.radius_sq) : 0;
      const rs = rsSq > 0 ? Math.sqrt(rsSq) : 0;
      const hs = s.height_sq ? Math.sqrt(Math.max(0, toNumber(s.height_sq))) : 0;
      const T: Vec3 | null = s.apex_or_top
        ? toVec3(s.apex_or_top)
        : hs > 0
          ? [A[0], A[1], A[2] + hs]
          : null;
      if (!T || !(rs > 1e-6)) continue;
      const ax = T[0] - A[0], ay = T[1] - A[1], az = T[2] - A[2];
      const hAxis = Math.hypot(ax, ay, az);
      if (!(hAxis > 1e-6)) continue;
      const ux = ax / hAxis, uy = ay / hAxis, uz = az / hAxis;
      const relX = center[0] - A[0], relY = center[1] - A[1], relZ = center[2] - A[2];
      const zProj = relX * ux + relY * uy + relZ * uz;
      const radialOff = Math.hypot(relX - zProj * ux, relY - zProj * uy, relZ - zProj * uz);
      if (radialOff > tol) continue;

      if (s.curved_kind === "cylinder") {
        if (Math.abs(zProj - hAxis * 0.5) <= tol) {
          if (Math.abs(r - Math.hypot(rs, hAxis * 0.5)) <= tol) return "CIRCUMSCRIBED_SPHERE";
          if (Math.abs(r - rs) <= tol && Math.abs(hAxis - 2 * r) <= tol) return "INSCRIBED_SPHERE";
        }
      } else if (s.curved_kind === "cone") {
        const dApex = Math.abs(hAxis - zProj);
        const dRim = Math.hypot(rs, zProj);
        if (Math.abs(dApex - r) <= tol && Math.abs(dRim - r) <= tol) return "CIRCUMSCRIBED_SPHERE";
        const slant = Math.hypot(rs, hAxis);
        const dSlant = ((hAxis - zProj) * rs) / slant;
        if (zProj > 0 && zProj < hAxis && Math.abs(zProj - r) <= tol && Math.abs(dSlant - r) <= tol) {
          return "INSCRIBED_SPHERE";
        }
      }
    }
  }

  return "STANDALONE_SPHERE";
}

/**
 * Quyết định có vẽ vòng xích đạo tham chiếu 3D (`sphere_reference:*`, `authoritative: false`) của mặt cầu theo `matphang.html`:
 * - Mọi mặt cầu trong `matphang.html` KHÔNG vẽ đường bao đen giả tiếp tuyến theo camera (`sphere_silhouette:*`), mà thể hiện độ cong 3D
 *   bằng vỏ cầu bán trong suốt kết hợp vòng tròn lớn xích đạo 3D (trước liền, sau đứt với mặt cầu độc lập / ngoại tiếp; toàn đứt với mặt cầu nội tiếp).
 * - Chỉ ẩn `sphere_reference:*` trên `STANDALONE_SPHERE` khi tập đối tượng đang hiện đã có sẵn một `circle3` tường minh trùng đúng
 *   đường tròn lớn nằm ngang đi qua tâm cầu (để không vẽ chồng hai đường tròn trùng khít lên nhau).
 */
export interface SphereReferenceGreatCirclePolicy {
  visible: boolean;
  role: "REFERENCE_GREAT_CIRCLE";
  semanticRole: "REFERENCE_GREAT_CIRCLE";
  canonicalRole: "REFERENCE_GEOMETRY";
  authoritative: false;
  labelVi: "Đường tròn lớn tham chiếu";
  center: ExactVec3;
  normal: ExactVec3;
  radiusSq: string;
  frontOpacity: number;
  hiddenOpacity: number;
  strokeScale: number;
  reason: string;
  roleTransitionedToObjectId?: string;
  suppressibleByProjection?: boolean;
}

/**
 * Chính sách hiển thị thống nhất cho mặt cầu (§2):
 * 1. Đường tròn lớn tham chiếu (`REFERENCE_GREAT_CIRCLE`, `authoritative: false`) có duy nhất một hướng chuẩn ngang
 *    đi qua tâm `ballObj.anchor` với pháp tuyến `["0", "0", "1"]` — TUYỆT ĐỐI không tự sinh hoặc xoay sang đường tròn
 *    tham chiếu thứ hai (`[0, 1, 0]`, `[1, 0, 0]`) chỉ để tránh chồng nét.
 * 2. Khi đường tròn giao tuyến (`RESULT_SECTION`) trùng hình học 3D với đường tròn lớn tham chiếu (ví dụ mặt phẳng ngang
 *    đi qua tâm `d = 0`), hệ thống dùng một quỹ tích hiển thị duy nhất có chuyển đổi vai trò: hiển thị làm đường tham chiếu
 *    trước khi có giao tuyến, rồi chuyển vai trò sang đối tượng đường tròn giao tuyến (`roleTransitionedToObjectId`).
 * 3. Khi mặt phẳng cắt song song gần tâm (`0 < d < 0.28 R`, `|cos θ| >= 0.94`), ẩn đường tham chiếu ngay khi đường tròn
 *    giao tuyến xuất hiện để tránh nhiễu nét mà không làm thay đổi hình học 3D.
 * 4. Khi chỉ hình chiếu elip 2D trên màn hình gần trùng nhau do góc nhìn camera, `computeProjectedCircleOverlapFactor`
 *    giảm độ đậm / ẩn tạm thời theo khung hình mà không chạm vào tọa độ 3D.
 */
export function resolveSphereReferenceGreatCirclePolicy(
  scene: Pick<Scene3D, "objects">,
  ballObj: SceneObject,
  optionsOrVisible?:
    | {
        auxiliaryShown?: boolean;
        visibleObjects?: readonly SceneObject[];
      }
    | readonly SceneObject[],
  legacyAuxShown?: boolean,
): SphereReferenceGreatCirclePolicy {
  const options = Array.isArray(optionsOrVisible)
    ? { visibleObjects: optionsOrVisible, auxiliaryShown: legacyAuxShown }
    : (optionsOrVisible as { auxiliaryShown?: boolean; visibleObjects?: readonly SceneObject[] } | undefined);
  const center: ExactVec3 = ballObj.anchor ?? ["0", "0", "0"];
  const canonicalNormal: ExactVec3 = ["0", "0", "1"];
  const radiusSq = ballObj.radius_sq ?? "1";
  if (ballObj.type !== "curved_solid" || ballObj.curved_kind !== "ball") {
    return {
      visible: false,
      role: "REFERENCE_GREAT_CIRCLE",
      semanticRole: "REFERENCE_GREAT_CIRCLE",
      canonicalRole: "REFERENCE_GEOMETRY",
      authoritative: false,
      labelVi: "Đường tròn lớn tham chiếu",
      center,
      normal: canonicalNormal,
      radiusSq,
      frontOpacity: 0,
      hiddenOpacity: 0,
      strokeScale: 0.22,
      reason: "not_a_sphere",
    };
  }

  const sphereRole = classifySphereSemanticRole(scene, ballObj);
  if (sphereRole === "INSCRIBED_SPHERE") {
    return {
      visible: true,
      role: "REFERENCE_GREAT_CIRCLE",
      semanticRole: "REFERENCE_GREAT_CIRCLE",
      canonicalRole: "REFERENCE_GEOMETRY",
      authoritative: false,
      labelVi: "Đường tròn lớn tham chiếu",
      center,
      normal: canonicalNormal,
      radiusSq,
      frontOpacity: 0.78,
      hiddenOpacity: 0.78,
      strokeScale: 0.27,
      reason: "inscribed_sphere_reference",
    };
  }
  if (sphereRole === "CIRCUMSCRIBED_SPHERE") {
    return {
      visible: true,
      role: "REFERENCE_GREAT_CIRCLE",
      semanticRole: "REFERENCE_GREAT_CIRCLE",
      canonicalRole: "REFERENCE_GEOMETRY",
      authoritative: false,
      labelVi: "Đường tròn lớn tham chiếu",
      center,
      normal: canonicalNormal,
      radiusSq,
      frontOpacity: 0.85,
      hiddenOpacity: 0.52,
      strokeScale: 0.27,
      reason: "circumscribed_sphere_reference",
    };
  }

  const anchor = toVec3(center);
  const rNum = toNumber(radiusSq);
  const R = rNum > 0 ? Math.sqrt(rNum) : 1;
  const tolPos = Math.max(1e-3 * R, 1e-6);
  const measOnly = "events" in scene ? measurementOnlyPlanes(scene as Scene3D) : new Set<string>();
  const chosenUnit: Vec3 = [0, 0, 1];
  const pool = options?.visibleObjects ?? scene.objects;
  const auxBoost = options?.auxiliaryShown ?? false;

  const hasOtherBalls = scene.objects.some(
    (b) => b.id !== ballObj.id && b.type === "curved_solid" && b.curved_kind === "ball",
  );
  const relatedPlaneIds = new Set(
    scene.objects
      .filter((x) => (x.depends ?? []).includes(ballObj.id))
      .flatMap((x) => (x.depends ?? []).filter((id) => id !== ballObj.id)),
  );

  const activeSectionCircles = pool.filter(
    (x) =>
      x.id !== ballObj.id
      && x.type === "circle3"
      && x.surface_role !== "BASE_REGION"
      && x.display_role !== "presentation_reference"
      && x.semantic_role !== "REFERENCE_EQUATOR"
      && x.semantic_role !== "REFERENCE_GREAT_CIRCLE"
      && (!hasOtherBalls || (x.depends ?? []).includes(ballObj.id)),
  );

  const coincidentSectionCircle = activeSectionCircles.find((x) => {
    if (!x.center || !x.normal) return false;
    const c = toVec3(x.center);
    if (Math.hypot(c[0] - anchor[0], c[1] - anchor[1], c[2] - anchor[2]) > tolPos) return false;
    const n = toVec3(x.normal);
    const nLen = Math.hypot(n[0], n[1], n[2]);
    if (!(nLen > 1e-9)) return false;
    const cosAng = Math.abs(chosenUnit[0] * n[0] + chosenUnit[1] * n[1] + chosenUnit[2] * n[2]) / nLen;
    return cosAng >= 1 - 1e-3;
  });

  if (coincidentSectionCircle) {
    return {
      visible: false,
      role: "REFERENCE_GREAT_CIRCLE",
      semanticRole: "REFERENCE_GREAT_CIRCLE",
      canonicalRole: "REFERENCE_GEOMETRY",
      authoritative: false,
      labelVi: "Đường tròn lớn tham chiếu",
      center,
      normal: canonicalNormal,
      radiusSq,
      frontOpacity: 0,
      hiddenOpacity: 0,
      strokeScale: 0.2,
      reason: "coincident_role_transition_to_intersection_circle",
      roleTransitionedToObjectId: coincidentSectionCircle.id,
    };
  }

  const nearCoincidentSectionCircle = activeSectionCircles.find((x) => {
    if (!x.center || !x.normal) return false;
    const c = toVec3(x.center);
    const distC = Math.hypot(c[0] - anchor[0], c[1] - anchor[1], c[2] - anchor[2]);
    if (distC >= 0.28 * R) return false;
    const n = toVec3(x.normal);
    const nLen = Math.hypot(n[0], n[1], n[2]);
    if (!(nLen > 1e-9)) return false;
    const cosAng = Math.abs(chosenUnit[0] * n[0] + chosenUnit[1] * n[1] + chosenUnit[2] * n[2]) / nLen;
    return cosAng >= 0.94;
  });

  if (nearCoincidentSectionCircle) {
    if (!auxBoost) {
      return {
        visible: false,
        role: "REFERENCE_GREAT_CIRCLE",
        semanticRole: "REFERENCE_GREAT_CIRCLE",
        canonicalRole: "REFERENCE_GEOMETRY",
        authoritative: false,
        labelVi: "Đường tròn lớn tham chiếu",
        center,
        normal: canonicalNormal,
        radiusSq,
        frontOpacity: 0,
        hiddenOpacity: 0,
        strokeScale: 0.2,
        reason: "hidden_near_coincident_with_intersection_circle",
      };
    }
    return {
      visible: true,
      role: "REFERENCE_GREAT_CIRCLE",
      semanticRole: "REFERENCE_GREAT_CIRCLE",
      canonicalRole: "REFERENCE_GEOMETRY",
      authoritative: false,
      labelVi: "Đường tròn lớn tham chiếu",
      center,
      normal: canonicalNormal,
      radiusSq,
      frontOpacity: 0.08,
      hiddenOpacity: 0.045,
      strokeScale: 0.18,
      reason: "attenuated_near_coincident_with_intersection_circle",
    };
  }

  const hasActiveSectionCircle = activeSectionCircles.length > 0;
  const hasActiveCuttingPlane = pool.some(
    (x) =>
      !isSubEntity(x.id)
      && x.type === "plane3"
      && !measOnly.has(x.id)
      && (!hasOtherBalls || relatedPlaneIds.has(x.id)),
  );

  if (hasActiveSectionCircle) {
    return {
      visible: true,
      role: "REFERENCE_GREAT_CIRCLE",
      semanticRole: "REFERENCE_GREAT_CIRCLE",
      canonicalRole: "REFERENCE_GEOMETRY",
      authoritative: false,
      labelVi: "Đường tròn lớn tham chiếu",
      center,
      normal: canonicalNormal,
      radiusSq,
      frontOpacity: auxBoost ? 0.19 : 0.13,
      hiddenOpacity: auxBoost ? 0.11 : 0.075,
      strokeScale: 0.2,
      reason: "attenuated_under_intersection_circle",
      suppressibleByProjection: !auxBoost,
    };
  }
  if (hasActiveCuttingPlane) {
    return {
      visible: true,
      role: "REFERENCE_GREAT_CIRCLE",
      semanticRole: "REFERENCE_GREAT_CIRCLE",
      canonicalRole: "REFERENCE_GEOMETRY",
      authoritative: false,
      labelVi: "Đường tròn lớn tham chiếu",
      center,
      normal: canonicalNormal,
      radiusSq,
      frontOpacity: auxBoost ? 0.22 : 0.16,
      hiddenOpacity: auxBoost ? 0.13 : 0.095,
      strokeScale: 0.23,
      reason: "attenuated_under_cutting_plane",
    };
  }
  return {
    visible: true,
    role: "REFERENCE_GREAT_CIRCLE",
    semanticRole: "REFERENCE_GREAT_CIRCLE",
    canonicalRole: "REFERENCE_GEOMETRY",
    authoritative: false,
    labelVi: "Đường tròn lớn tham chiếu",
    center,
    normal: canonicalNormal,
    radiusSq,
    frontOpacity: auxBoost ? 0.28 : 0.24,
    hiddenOpacity: auxBoost ? 0.16 : 0.14,
    strokeScale: 0.27,
    reason: "standalone_depth_cue",
  };
}

/**
 * Hệ số ưu tiên hiển thị theo hình chiếu elip 2D trên màn hình (`∈ [0, 1]`):
 * Khi góc nhìn camera làm elip chiếu 2D của đường tròn lớn tham chiếu chồng sát lên elip chiếu 2D của đường tròn giao tuyến,
 * giảm độ đậm / ẩn tạm thời đường tham chiếu mà không thay đổi bất kỳ tọa độ hay pháp tuyến 3D nào.
 */
export function computeProjectedCircleOverlapFactor(
  refCenter: Vec3,
  refNormal: Vec3,
  refRadius: number,
  sectionCircles: readonly { center: Vec3; normal: Vec3; radius: number }[],
  camera: {
    matrixWorldInverse: { elements: ArrayLike<number> };
    projectionMatrix: { elements: ArrayLike<number> };
  },
  viewportWidthPx: number,
  viewportHeightPx: number,
): number {
  if (!(refRadius > 1e-6) || sectionCircles.length === 0 || !(viewportWidthPx > 1) || !(viewportHeightPx > 1)) {
    return 1;
  }
  const V = camera.matrixWorldInverse.elements;
  const P = camera.projectionMatrix.elements;
  const projectPt = (x: number, y: number, z: number): [number, number] | null => {
    const vx = V[0]! * x + V[4]! * y + V[8]! * z + V[12]!;
    const vy = V[1]! * x + V[5]! * y + V[9]! * z + V[13]!;
    const vz = V[2]! * x + V[6]! * y + V[10]! * z + V[14]!;
    const vw = V[3]! * x + V[7]! * y + V[11]! * z + V[15]!;
    const cx = P[0]! * vx + P[4]! * vy + P[8]! * vz + P[12]! * vw;
    const cy = P[1]! * vx + P[5]! * vy + P[9]! * vz + P[13]! * vw;
    const cw = P[3]! * vx + P[7]! * vy + P[11]! * vz + P[15]! * vw;
    if (!(Math.abs(cw) > 1e-6)) return null;
    const ndcX = cx / cw;
    const ndcY = cy / cw;
    return [(ndcX * 0.5 + 0.5) * viewportWidthPx, (0.5 - ndcY * 0.5) * viewportHeightPx];
  };
  const sampleCircle2D = (c: Vec3, n: Vec3, r: number, count = 36): [number, number][] => {
    const nLen = Math.hypot(n[0], n[1], n[2]);
    if (!(nLen > 1e-9)) return [];
    const nx = n[0] / nLen, ny = n[1] / nLen, nz = n[2] / nLen;
    const refAx: Vec3 = Math.abs(nx) < 0.85 ? [1, 0, 0] : [0, 1, 0];
    let ux = ny * refAx[2] - nz * refAx[1];
    let uy = nz * refAx[0] - nx * refAx[2];
    let uz = nx * refAx[1] - ny * refAx[0];
    const uLen = Math.hypot(ux, uy, uz);
    if (!(uLen > 1e-9)) return [];
    ux /= uLen; uy /= uLen; uz /= uLen;
    const vx = ny * uz - nz * uy;
    const vy = nz * ux - nx * uz;
    const vz = nx * uy - ny * ux;
    const out: [number, number][] = [];
    for (let i = 0; i < count; i += 1) {
      const ang = (2 * Math.PI * i) / count;
      const ca = Math.cos(ang), sa = Math.sin(ang);
      const p2 = projectPt(
        c[0] + r * (ca * ux + sa * vx),
        c[1] + r * (ca * uy + sa * vy),
        c[2] + r * (ca * uz + sa * vz),
      );
      if (p2) out.push(p2);
    }
    return out;
  };
  const distPtToLoop = (pt: [number, number], loop: [number, number][]): number => {
    let bestSq = Infinity;
    for (let i = 0; i < loop.length; i += 1) {
      const a = loop[i]!;
      const b = loop[(i + 1) % loop.length]!;
      const dx = b[0] - a[0], dy = b[1] - a[1];
      const lSq = dx * dx + dy * dy;
      const t = lSq > 1e-9 ? Math.max(0, Math.min(1, ((pt[0] - a[0]) * dx + (pt[1] - a[1]) * dy) / lSq)) : 0;
      const qx = a[0] + t * dx - pt[0];
      const qy = a[1] + t * dy - pt[1];
      const dSq = qx * qx + qy * qy;
      if (dSq < bestSq) bestSq = dSq;
    }
    return Math.sqrt(bestSq);
  };

  const refLoop = sampleCircle2D(refCenter, refNormal, refRadius);
  if (refLoop.length < 8) return 1;
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  for (const [px, py] of refLoop) {
    if (px < minX) minX = px;
    if (px > maxX) maxX = px;
    if (py < minY) minY = py;
    if (py > maxY) maxY = py;
  }
  const majorRadiusPx = Math.max(24, 0.5 * Math.hypot(maxX - minX, maxY - minY));
  const hideDistPx = Math.max(5, 0.036 * majorRadiusPx);
  const clearDistPx = Math.max(26, 0.19 * majorRadiusPx);

  let minFactor = 1;
  for (const sec of sectionCircles) {
    if (!(sec.radius > 1e-6)) continue;
    const secLoop = sampleCircle2D(sec.center, sec.normal, sec.radius);
    if (secLoop.length < 8) continue;
    let sumSecToRef = 0;
    for (const q of secLoop) sumSecToRef += distPtToLoop(q, refLoop);
    let sumRefToSec = 0;
    for (const p of refLoop) sumRefToSec += distPtToLoop(p, secLoop);
    const dSym = 0.5 * (sumSecToRef / secLoop.length + sumRefToSec / refLoop.length);
    if (dSym <= hideDistPx) return 0;
    if (dSym < clearDistPx) {
      const t = (dSym - hideDistPx) / (clearDistPx - hideDistPx);
      const smooth = t * t * (3 - 2 * t);
      const f = smooth;
      if (f < minFactor) minFactor = f;
    }
  }
  return minFactor;
}

export function shouldShowSphereReferenceEquator(
  scene: Pick<Scene3D, "objects">,
  o: SceneObject,
  auxiliaryShown = false,
  visibleObjects?: readonly SceneObject[],
): boolean {
  if (o.type !== "curved_solid" || o.curved_kind !== "ball") return false;
  return resolveSphereReferenceGreatCirclePolicy(scene, o, {
    auxiliaryShown,
    visibleObjects,
  }).visible;
}

/**
 * Xác định tập đối tượng mới xuất hiện/cập nhật (`newIds`) và tập tiền đề trực tiếp (`depIds`)
 * khi chuyển sang một bước dựng hình học (`Step Highlight`, độc lập hoàn toàn với `Selection Highlight`).
 */
export function computeStepHighlightTargets(
  scene: Scene3D,
  step: number,
  startStep?: number,
): { newIds: Set<string>; depIds: Set<string> } {
  const newIds = new Set<string>();
  const depIds = new Set<string>();
  const tl = geometryTimeline(scene);
  if (tl.length === 0) return { newIds, depIds };
  const k = clampStep(scene, step);
  const gIdx = geometryStepOf(scene, k);
  const gStartIdx = startStep !== undefined ? geometryStepOf(scene, clampStep(scene, startStep)) : gIdx;
  if (gIdx <= 0 || !tl[gIdx]) return { newIds, depIds };

  const byId = new Map(scene.objects.map((o) => [o.id, o]));
  const isVisualTarget = (o: SceneObject | undefined) =>
    Boolean(o && o.render !== "readout" && o.render !== "non_visual");

  // Bước kết luận đại lượng (vd góc nhị diện / góc đường–mặt) tách ở cuối: nhấn mạnh các đối tượng mang góc
  if (startStep !== undefined) {
    const startClamped = clampStep(scene, startStep);
    const rangeEvs = scene.events.slice(startClamped, k + 1);
    if (rangeEvs.length > 0 && rangeEvs.every((ev) => ev.action === "MEASURE")) {
      for (const ev of rangeEvs) {
        const qObj = ev.object ? byId.get(ev.object) : undefined;
        for (const d of [...(ev.depends ?? []), ...(qObj?.depends ?? [])]) {
          const depObj = byId.get(d);
          if (!depObj || depObj.type === "solid" || depObj.type === "curved_solid") continue;
          if (isVisualTarget(depObj)) depIds.add(d);
        }
      }
      return { newIds, depIds };
    }
  }

  const prevIdx = Math.max(0, gStartIdx - 1);
  const prevPresent = gStartIdx > 0
    ? new Set(objectsAt(scene, tl[prevIdx].anchor).map((o) => o.id))
    : new Set<string>();
  for (const o of objectsAt(scene, tl[gIdx].anchor)) {
    if (!prevPresent.has(o.id) && isVisualTarget(o)) {
      newIds.add(o.id);
    }
  }
  for (let idx = Math.min(gStartIdx, gIdx); idx <= gIdx; idx += 1) {
    for (const evIdx of tl[idx]?.construction ?? []) {
      const ev = scene.events[evIdx];
      if (!ev) continue;
      for (const oid of [ev.object, ...(ev.objects ?? [])]) {
        if (!oid) continue;
        const targetObj = byId.get(oid);
        if (isVisualTarget(targetObj)) {
          newIds.add(oid);
        }
      }
      for (const d of ev.depends ?? []) {
        const depObj = byId.get(d);
        if (!depObj || depObj.type === "solid" || depObj.type === "curved_solid") continue;
        if (!newIds.has(d) && isVisualTarget(depObj)) depIds.add(d);
      }
    }
  }
  const presentSet = new Set(objectsAt(scene, tl[gIdx].anchor).map((o) => o.id));
  for (const id of newIds) {
    const src = byId.get(id);
    if (!src) continue;
    for (const d of src.depends ?? []) {
      const depObj = byId.get(d);
      if (!depObj || depObj.type === "solid" || depObj.type === "curved_solid") continue;
      if (!newIds.has(d) && isVisualTarget(depObj)) depIds.add(d);
    }
    if (src.type === "point3") {
      const ptDeps = (src.depends ?? []).filter((d) => byId.get(d)?.type === "point3");
      if (ptDeps.length === 2) {
        const [uId, vId] = ptDeps;
        for (const cand of scene.objects) {
          if (newIds.has(cand.id)) continue;
          if (!cand.id.includes("::edge:") && !presentSet.has(cand.id)) continue;
          if (cand.id.includes("::edge:") && cand.parent && !presentSet.has(cand.parent)) continue;
          if (cand.type !== "edge" && cand.type !== "segment3" && cand.type !== "line3") continue;
          const endIds = (cand.endpoint_ids ?? cand.depends ?? []).filter(
            (d) => byId.get(d)?.type === "point3",
          );
          if (endIds.length === 2 && endIds.includes(uId) && endIds.includes(vId)) {
            depIds.add(cand.id);
          }
        }
      }
    }
  }
  return { newIds, depIds };
}

function orthonormalBasisOnPlane(normal: Vec3): [Vec3, Vec3] {
  const dn = Math.hypot(...normal) || 1;
  const u: Vec3 = [normal[0] / dn, normal[1] / dn, normal[2] / dn];
  const nXY = Math.hypot(u[0], u[1]);
  if (nXY > 1e-6) {
    const e1: Vec3 = [-u[1] / nXY, u[0] / nXY, 0];
    let e2: Vec3 = [
      u[1] * e1[2] - u[2] * e1[1],
      u[2] * e1[0] - u[0] * e1[2],
      u[0] * e1[1] - u[1] * e1[0],
    ];
    if (e2[2] < 0) e2 = [-e2[0], -e2[1], -e2[2]];
    return [e1, e2];
  }
  return [[1, 0, 0], [0, 1, 0]];
}

/**
 * Phân biệt 5 vai trò đường tròn (`circle3`) từ hợp đồng `Scene3D`:
 * - `REFERENCE_EQUATOR`: vòng xích đạo tham chiếu (`presentation_reference`, `authoritative: false`).
 * - `BOUNDARY_AND_INTERSECTION`: vành đáy vật lý của hình nón / hình trụ (`BASE_REGION`).
 * - `INSCRIBED_CIRCLE`: đường tròn nội tiếp đa giác đồng phẳng (mặt khối hoặc đa giác trong cảnh).
 * - `CIRCUMSCRIBED_CIRCLE`: đường tròn ngoại tiếp đi qua các đỉnh đa giác đồng phẳng.
 * - `RESULT_SECTION`: đường tròn thiết diện do mặt phẳng cắt mặt cầu / hình trụ / hình nón.
 */
export function classifyCircleSemanticRole(
  scene: Pick<Scene3D, "objects">,
  o: SceneObject,
): CircleSemanticRole {
  if (o.semantic_role === "REFERENCE_GREAT_CIRCLE") {
    return "REFERENCE_GREAT_CIRCLE";
  }
  if (o.semantic_role === "REFERENCE_EQUATOR" || o.display_role === "presentation_reference") {
    return "REFERENCE_EQUATOR";
  }
  if (o.semantic_role === "INSCRIBED_CIRCLE") return "INSCRIBED_CIRCLE";
  if (o.semantic_role === "CIRCUMSCRIBED_CIRCLE") return "CIRCUMSCRIBED_CIRCLE";
  if (o.semantic_role === "BOUNDARY_AND_INTERSECTION") return "BOUNDARY_AND_INTERSECTION";
  if (o.semantic_role === "RESULT_SECTION") return "RESULT_SECTION";

  if (o.surface_role === "BASE_REGION") return "BOUNDARY_AND_INTERSECTION";
  if (o.surface_role === "SECTION_REGION" || (o.formation_roles ?? []).includes("PRODUCE_SECTION_RESULT")) {
    return "RESULT_SECTION";
  }
  if (!o.center || !o.normal || !o.radius_sq) {
    return vaiTroMien(o) === "base" ? "BOUNDARY_AND_INTERSECTION" : "RESULT_SECTION";
  }

  const center = toVec3(o.center);
  const nRaw = toVec3(o.normal);
  const nLen = Math.hypot(...nRaw);
  const r = Math.sqrt(Math.max(0, toNumber(o.radius_sq)));
  if (!(r > 1e-6) || !(nLen > 1e-9)) {
    return vaiTroMien(o) === "base" ? "BOUNDARY_AND_INTERSECTION" : "RESULT_SECTION";
  }
  const u: Vec3 = [nRaw[0] / nLen, nRaw[1] / nLen, nRaw[2] / nLen];
  const tol = 1e-3 * Math.max(1, r);

  const candidatePolygons: Vec3[][] = [];
  const hasCircleLineage =
    o.origin === "derived"
    || (o.depends?.length ?? 0) > 0
    || /\b(ngoại|nội)\s+tiếp\b/iu.test(`${o.label ?? ""} ${o.role ?? ""}`);
  for (const s of hasCircleLineage ? scene.objects : []) {
    if (s.id === o.id) continue;
    if (s.type === "solid" && s.vertices && s.faces) {
      const verts = s.vertices.map(toVec3);
      for (const f of s.faces) {
        const loop = f.map((idx) => verts[idx]).filter(Boolean);
        if (loop.length >= 3) candidatePolygons.push(loop);
      }
    } else if ((s.type === "polygon3" || s.type === "face") && (s.polygon ?? s.vertices)) {
      const loop = (s.polygon ?? s.vertices ?? []).map(toVec3);
      if (loop.length >= 3) candidatePolygons.push(loop);
    }
  }

  const [e1, e2] = orthonormalBasisOnPlane(u);
  for (const poly of candidatePolygons) {
    const nPoly = normalFromPoints(poly);
    if (!nPoly) continue;
    const parallel = Math.abs(nPoly[0] * u[0] + nPoly[1] * u[1] + nPoly[2] * u[2]);
    if (parallel < 1 - 1e-3) continue;
    const planeDist = Math.abs(
      (center[0] - poly[0][0]) * nPoly[0]
      + (center[1] - poly[0][1]) * nPoly[1]
      + (center[2] - poly[0][2]) * nPoly[2],
    );
    if (planeDist > tol) continue;

    // 1. Đường tròn ngoại tiếp: đi qua toàn bộ đỉnh của đa giác đồng phẳng
    const passesAllVertices = poly.every(
      (v) => Math.abs(Math.hypot(v[0] - center[0], v[1] - center[1], v[2] - center[2]) - r) <= tol,
    );
    if (passesAllVertices) return "CIRCUMSCRIBED_CIRCLE";

    // 2. Đường tròn nội tiếp: tâm nằm trong đa giác lồi và tiếp xúc tất cả các cạnh ở phần trong đoạn cạnh
    const pts2d = poly.map((v): [number, number] => {
      const dx = v[0] - center[0], dy = v[1] - center[1], dz = v[2] - center[2];
      return [
        dx * e1[0] + dy * e1[1] + dz * e1[2],
        dx * e2[0] + dy * e2[1] + dz * e2[2],
      ];
    });
    let sign = 0;
    let allEdgesTangent = true;
    for (let i = 0; i < pts2d.length; i += 1) {
      const [ax, ay] = pts2d[i];
      const [bx, by] = pts2d[(i + 1) % pts2d.length];
      const ex = bx - ax, ey = by - ay;
      const eLen = Math.hypot(ex, ey);
      if (!(eLen > 1e-6)) {
        allEdgesTangent = false;
        break;
      }
      // Vector từ A tới tâm O(0,0) là (-ax, -ay); tích có hướng 2D = ex*(-ay) - ey*(-ax)
      const cross = ex * (-ay) - ey * (-ax);
      const curSign = cross > 1e-6 ? 1 : cross < -1e-6 ? -1 : 0;
      if (curSign === 0 || (sign !== 0 && curSign !== sign)) {
        allEdgesTangent = false;
        break;
      }
      sign = curSign;
      const perpDist = Math.abs(cross) / eLen;
      const tFoot = ((-ax) * ex + (-ay) * ey) / (eLen * eLen);
      if (Math.abs(perpDist - r) > tol || tFoot < -1e-2 || tFoot > 1 + 1e-2) {
        allEdgesTangent = false;
        break;
      }
    }
    if (allEdgesTangent && pts2d.length >= 3) return "INSCRIBED_CIRCLE";
  }

  // Kiểm tra trùng nắp hình nón / hình trụ khi `surface_role` bị lược bỏ
  for (const s of scene.objects) {
    if (s.type !== "curved_solid" || (s.curved_kind !== "cone" && s.curved_kind !== "cylinder") || !s.anchor) {
      continue;
    }
    const anchor = toVec3(s.anchor);
    const rs = s.radius_sq ? Math.sqrt(Math.max(0, toNumber(s.radius_sq))) : 0;
    const hs = s.height_sq ? Math.sqrt(Math.max(0, toNumber(s.height_sq))) : 0;
    const top: Vec3 | null = s.apex_or_top
      ? toVec3(s.apex_or_top)
      : hs > 0
        ? [anchor[0], anchor[1], anchor[2] + hs]
        : null;
    if (Math.abs(rs - r) > tol) continue;
    const atAnchor = Math.hypot(anchor[0] - center[0], anchor[1] - center[1], anchor[2] - center[2]) <= tol;
    const atTop = s.curved_kind === "cylinder"
      && top !== null
      && Math.hypot(top[0] - center[0], top[1] - center[1], top[2] - center[2]) <= tol;
    if (atAnchor || atTop) return "BOUNDARY_AND_INTERSECTION";
  }

  return vaiTroMien(o) === "base" ? "BOUNDARY_AND_INTERSECTION" : "RESULT_SECTION";
}

export interface ObjectSemanticClassification {
  role: SemanticRoleId;
  epistemicStatus: EpistemicStatus;
  fillColor: number;
  strokeColor: number;
  fillOpacity: number;
  prominenceTier: 1 | 2 | 3 | 4 | 5;
  /** True khi một `polygon3` mang vai `AUXILIARY_SURFACE` cùng tồn tại với thiết diện cắt tường minh. */
  isAuxiliaryExplanatorySurface: boolean;
}

/** Kiểm tra xem cảnh có một miền thiết diện cắt tường minh khác với `candidateId` hay không. */
export function hasExplicitCutSectionElsewhere(
  scene: Pick<Scene3D, "objects">,
  candidateId: string,
): boolean {
  return scene.objects.some((other) => {
    if (other.id === candidateId) return false;
    if (other.type === "section" || other.surface_role === "SECTION_REGION") return true;
    if ((other.formation_roles ?? []).includes("PRODUCE_SECTION_RESULT")) return true;
    if (other.type === "ellipse3" && vaiTroMien(other) === "section") return true;
    if (other.type === "circle3" && classifyCircleSemanticRole(scene, other) === "RESULT_SECTION") return true;
    return false;
  });
}

function isExplanatoryPerpSegment(o: SceneObject | undefined): boolean {
  if (!o || o.type !== "segment3") return false;
  const src = o.source as Record<string, unknown> | undefined;
  const groups = o.display_group ?? [];
  return (
    groups.includes("perp_witness")
    || (src?.instruction === "EXPLANATORY_DERIVED_WITNESS" && Boolean(o.perpendicular_witness) && !groups.includes("goal_segment"))
  );
}

function isExplanatoryTargetSegment(o: SceneObject | undefined): boolean {
  if (!o || o.type !== "segment3") return false;
  const src = o.source as Record<string, unknown> | undefined;
  const groups = o.display_group ?? [];
  return (
    groups.includes("goal_segment")
    || (src?.instruction === "EXPLANATORY_DERIVED_WITNESS" && groups.includes("target") && !o.perpendicular_witness)
  );
}

export function isTwoBasePolyhedronSolid(
  scene: Pick<Scene3D, "objects">,
  sol: SceneObject,
): boolean {
  if (sol.type !== "solid") return false;
  if (
    sol.shape_class === "PRISM_LIKE"
    || sol.shape_class === "BOX_LIKE"
    || sol.shape_class === "FRUSTUM_LIKE"
  ) {
    return true;
  }
  if (sol.shape_class === "PYRAMID_LIKE") return false;
  const exactScene = exactSceneOriginOf(scene);
  const exSol = exactScene.objects.find((x) => x.id === sol.id) ?? sol;
  const faces = exSol.faces ?? [];
  if (faces.length < 5 || (faces[0]?.length ?? 0) < 3) return false;
  const byId = new Map(exactScene.objects.map((x) => [x.id, x]));
  const faceNormal = (faceIdxList: number[]): FracVec3 | null => {
    const pts: FracVec3[] = [];
    for (const vi of faceIdxList) {
      const vId = exSol.vertex_ids?.[vi];
      const ptXyz = (vId ? byId.get(vId)?.xyz : undefined) ?? exSol.vertices?.[vi];
      if (ptXyz) pts.push(parseFracVec3(ptXyz));
    }
    if (pts.length < 3) return null;
    for (let i = 1; i + 1 < pts.length; i += 1) {
      const n = vCross(vSub(pts[i], pts[0]), vSub(pts[i + 1], pts[0]));
      if (!vIsZero(n)) return n;
    }
    return null;
  };
  const n0 = faceNormal(faces[0]);
  if (!n0) return false;
  for (let k = 1; k < faces.length; k += 1) {
    if (faces[k].length !== faces[0].length) continue;
    const disjointVerts = faces[k].every((vi) => !faces[0].includes(vi));
    if (!disjointVerts) continue;
    const nk = faceNormal(faces[k]);
    if (nk && vIsZero(vCross(n0, nk))) return true;
  }
  return false;
}

export function isPolyhedronOppositeTopBasePolygon(
  scene: Pick<Scene3D, "objects">,
  o: SceneObject,
): boolean {
  if (o.type !== "polygon3") return false;
  if ((o.formation_roles ?? []).includes("CONSTRUCT_TRANSLATED_FACE")) return true;
  if (
    o.surface_role === "SECTION_REGION"
    || (o.formation_roles ?? []).includes("PRODUCE_SECTION_RESULT")
  ) {
    return false;
  }
  const exactScene = exactSceneOriginOf(scene);
  const exO = exactScene.objects.find((x) => x.id === o.id) ?? o;
  const byId = new Map(exactScene.objects.map((x) => [x.id, x]));
  const rawPtIds = (exO.vertex_ids && exO.vertex_ids.length >= 3 ? exO.vertex_ids : exO.depends ?? []).filter(
    (id) => byId.get(id)?.type === "point3",
  );
  const rawCoordKeys = (exO.polygon ?? exO.vertices ?? []).map((v) => v.join("|"));
  for (const sol of exactScene.objects) {
    if (sol.type !== "solid" || !Array.isArray(sol.faces) || sol.faces.length < 5) continue;
    if (!isTwoBasePolyhedronSolid(exactScene, sol)) continue;
    const faces = sol.faces;
    const faceNormal = (faceIdxList: number[]): FracVec3 | null => {
      const pts: FracVec3[] = [];
      for (const vi of faceIdxList) {
        const vId = sol.vertex_ids?.[vi];
        const ptXyz = (vId ? byId.get(vId)?.xyz : undefined) ?? sol.vertices?.[vi];
        if (ptXyz) pts.push(parseFracVec3(ptXyz));
      }
      if (pts.length < 3) return null;
      for (let i = 1; i + 1 < pts.length; i += 1) {
        const n = vCross(vSub(pts[i], pts[0]), vSub(pts[i + 1], pts[0]));
        if (!vIsZero(n)) return n;
      }
      return null;
    };
    const n0 = faceNormal(faces[0]);
    if (!n0) continue;
    let oppIdx = -1;
    for (let k = 1; k < faces.length; k += 1) {
      const sameDegree = sol.shape_class === "FRUSTUM_LIKE" || faces[k].length === faces[0].length;
      if (!sameDegree) continue;
      const disjointVerts = faces[k].every((vi) => !faces[0].includes(vi));
      const nk = faceNormal(faces[k]);
      if (nk && disjointVerts && vIsZero(vCross(n0, nk))) {
        oppIdx = k;
        break;
      }
    }
    if (oppIdx <= 0) continue;
    if (rawPtIds.length >= 3 && sol.vertex_ids && sol.vertex_ids.length > 0) {
      const faceIdSet = new Set(faces[oppIdx].map((vi) => sol.vertex_ids![vi]).filter(Boolean));
      if (faceIdSet.size === rawPtIds.length && rawPtIds.every((id) => faceIdSet.has(id))) return true;
    }
    if (rawCoordKeys.length >= 3 && sol.vertices && sol.vertices.length > 0) {
      const faceCoordSet = new Set(faces[oppIdx].map((vi) => sol.vertices![vi]?.join("|")).filter(Boolean));
      if (faceCoordSet.size === rawCoordKeys.length && rawCoordKeys.every((k) => faceCoordSet.has(k))) return true;
    }
  }
  return false;
}

export function isSecondaryCutCurvedSolid(
  scene: Pick<Scene3D, "objects"> & Partial<Pick<Scene3D, "events">>,
  cs: SceneObject,
): boolean {
  if (cs.type !== "curved_solid") return false;
  const byId = new Map(scene.objects.map((o) => [o.id, o]));
  const hasCutDependency = (cs.depends ?? []).some((d) => {
    const dep = byId.get(d);
    if (!dep) return false;
    if (dep.type === "plane3" || dep.type === "section" || vaiTroMien(dep) === "section") {
      return true;
    }
    if (dep.type === "point3" && dep.origin === "derived") {
      return true;
    }
    if (dep.type === "circle3" || dep.type === "ellipse3") {
      return dep.surface_role !== "BASE_REGION";
    }
    return false;
  });
  if (hasCutDependency) return true;
  const hasCuttingSurfaceInScene = scene.objects.some(
    (o) =>
      !isSubEntity(o.id)
      && (o.type === "plane3" || o.type === "section" || vaiTroMien(o) === "section"),
  );
  if (!hasCuttingSurfaceInScene || !scene.events) return false;
  const evOrder = new Map<string, number>();
  scene.events.forEach((ev, idx) => {
    if (ev.object && !evOrder.has(ev.object)) evOrder.set(ev.object, idx);
  });
  const myPos = evOrder.get(cs.id) ?? Number.MAX_SAFE_INTEGER;
  return scene.objects.some((other) => {
    if (other.id === cs.id || other.type !== "curved_solid" || other.curved_kind !== cs.curved_kind) return false;
    const otherPos = evOrder.get(other.id) ?? Number.MAX_SAFE_INTEGER;
    return otherPos < myPos;
  });
}

/**
 * Kiểm tra `polygon3` có phải mặt bên hoặc miền phẳng phụ trùng với một mặt biên của khối đa diện `solid`
 * (hoặc mang `CONSTRUCT_AUXILIARY_GEOMETRY`), thay vì mặt đáy chính hay thiết diện cắt xuyên khối.
 */
export function isPolyhedronLateralOrAuxFacePolygon(
  scene: Pick<Scene3D, "objects">,
  o: SceneObject,
): boolean {
  if (o.type !== "polygon3") return false;
  const roles = o.formation_roles ?? [];
  if (
    roles.includes("CONSTRUCT_BASE")
    || roles.includes("CONSTRUCT_TRANSLATED_FACE")
  ) {
    return false;
  }
  if (
    o.surface_role === "SECTION_REGION"
    || roles.includes("PRODUCE_SECTION_RESULT")
  ) {
    return false;
  }
  const exactScene = exactSceneOriginOf(scene);
  const exO = exactScene.objects.find((x) => x.id === o.id) ?? o;
  const solids = exactScene.objects.filter((s) => s.type === "solid" && Array.isArray(s.faces) && s.faces.length > 0);
  if (solids.length === 0) return false;

  const byId = new Map(exactScene.objects.map((x) => [x.id, x]));
  const rawPtIds = (exO.vertex_ids && exO.vertex_ids.length >= 3 ? exO.vertex_ids : exO.depends ?? []).filter(
    (id) => byId.get(id)?.type === "point3",
  );
  const rawCoordKeys = (exO.polygon ?? exO.vertices ?? []).map((v) => v.join("|"));

  const matchesFace = (sol: SceneObject, faceIdxList: number[]): boolean => {
    if (rawPtIds.length >= 3 && sol.vertex_ids && sol.vertex_ids.length > 0) {
      const faceIdSet = new Set(faceIdxList.map((vi) => sol.vertex_ids![vi]).filter(Boolean));
      if (faceIdSet.size === rawPtIds.length && rawPtIds.every((id) => faceIdSet.has(id))) return true;
    }
    if (rawCoordKeys.length >= 3 && sol.vertices && sol.vertices.length > 0) {
      const faceCoordSet = new Set(faceIdxList.map((vi) => sol.vertices![vi]?.join("|")).filter(Boolean));
      if (faceCoordSet.size === rawCoordKeys.length && rawCoordKeys.every((k) => faceCoordSet.has(k))) return true;
    }
    return false;
  };

  const faceNormal = (sol: SceneObject, faceIdxList: number[]): FracVec3 | null => {
    const pts: FracVec3[] = [];
    for (const vi of faceIdxList) {
      const vId = sol.vertex_ids?.[vi];
      const ptXyz = (vId ? byId.get(vId)?.xyz : undefined) ?? sol.vertices?.[vi];
      if (ptXyz) pts.push(parseFracVec3(ptXyz));
    }
    if (pts.length < 3) return null;
    for (let i = 1; i + 1 < pts.length; i += 1) {
      const n = vCross(vSub(pts[i], pts[0]), vSub(pts[i + 1], pts[0]));
      if (!vIsZero(n)) return n;
    }
    return null;
  };

  for (const sol of solids) {
    const faces = sol.faces!;
    const hasPrimaryBaseOnFace0Elsewhere = exactScene.objects.some((b) => {
      if (b.id === o.id || b.type !== "polygon3") return false;
      const bRoles = b.formation_roles ?? [];
      if (bRoles.includes("CONSTRUCT_BASE")) return true;
      if (b.surface_role === "BASE_REGION") {
        const bPtIds = (b.vertex_ids && b.vertex_ids.length >= 3 ? b.vertex_ids : b.depends ?? []).filter(
          (id) => byId.get(id)?.type === "point3",
        );
        const face0Set = new Set((faces[0] ?? []).map((vi) => sol.vertex_ids?.[vi]).filter(Boolean));
        if (bPtIds.length >= 3 && face0Set.size === bPtIds.length && bPtIds.every((id) => face0Set.has(id))) {
          return true;
        }
      }
      return false;
    });

    const baseFaceIndices = new Set<number>([0]);
    const isTwoBaseFamily = isTwoBasePolyhedronSolid(exactScene, sol);
    if (isTwoBaseFamily && faces.length >= 5) {
      const n0 = faceNormal(sol, faces[0]);
      if (n0) {
        for (let k = 1; k < faces.length; k += 1) {
          const sameDegree = sol.shape_class === "FRUSTUM_LIKE" || faces[k].length === faces[0].length;
          if (!sameDegree) continue;
          const nk = faceNormal(sol, faces[k]);
          const disjointVerts = faces[k].every((vi) => !faces[0].includes(vi));
          if (nk && disjointVerts && vIsZero(vCross(n0, nk))) {
            baseFaceIndices.add(k);
            break;
          }
        }
      }
    }

    for (let fi = 0; fi < faces.length; fi += 1) {
      if (!matchesFace(sol, faces[fi])) continue;
      if (baseFaceIndices.has(fi)) {
        if (fi === 0 && o.surface_role === "BASE_REGION") return false;
        if (fi > 0 && isTwoBaseFamily) return false;
        if (fi === 0 && !hasPrimaryBaseOnFace0Elsewhere) return false;
      }
      return true;
    }
  }
  return false;
}

/** Kiểm tra `polygon3` có phải miền phụ trợ giải thích (như mặt bên phụ hoặc tam giác trục phụ khi cảnh có thiết diện cắt khác). */
export function isAuxiliaryExplanatoryPolygon(
  scene: Pick<Scene3D, "objects">,
  o: SceneObject,
): boolean {
  if (o.type !== "polygon3") return false;
  if (o.parent && (o.display_group ?? []).includes("face")) return false;
  if (isPolyhedronLateralOrAuxFacePolygon(scene, o)) return true;
  if (vaiTroMien(o) === "base") return false;
  if (o.surface_role !== "AUXILIARY_SURFACE") return false;
  if ((o.formation_roles ?? []).includes("PRODUCE_SECTION_RESULT")) return false;
  if ((o.display_group ?? []).includes("target")) return false;
  return hasExplicitCutSectionElsewhere(scene, o.id);
}

/**
 * Phân loại vai trò ngữ nghĩa của một đối tượng `SceneObject` tại bước `step`
 * chỉ từ siêu dữ liệu hợp đồng `Scene3D`. Khi hover hoặc chọn đối tượng, vai trò
 * toán học và họ màu ngữ nghĩa được giữ nguyên tuyệt đối.
 */
export function classifySceneObjectSemantics(
  scene: Pick<Scene3D, "objects"> & Partial<Pick<Scene3D, "events" | "formation" | "free_objects">>,
  o: SceneObject,
  _step: number,
  selectedId: string | null = null,
  hoveredObjectId: string | null = null,
): ObjectSemanticClassification {
  const isSelected = selectedId !== null && selectedId === o.id;
  const isHovered = !isSelected && hoveredObjectId !== null && hoveredObjectId === o.id;
  const interactionState: InteractionVisualState = isSelected ? "selected" : isHovered ? "hover" : "neutral";
  const groups = o.display_group ?? [];
  const roles = o.formation_roles ?? [];
  const isCertGivenObj = isCertifiedGivenSceneObject(scene, o);
  const byIdForSem = new Map(scene.objects.map((x) => [x.id, x]));
  const allDepsCertGiven =
    (o.depends ?? []).length > 0
    && (o.depends ?? []).every((depId) => {
      const dep = byIdForSem.get(depId);
      return dep ? isCertifiedGivenSceneObject(scene, dep) : false;
    });
  const isCertGivenOrGroup =
    isCertGivenObj
    || (
      groups.includes("given")
      && o.authoritative !== false
      && !hasUncertifiedObjectSource(o)
      && !hasContradictoryObjectProvenance(o, false)
      && allDepsCertGiven
    );

  if (o.type === "curved_solid" && o.curved_kind === "ball") {
    const sphereRole = classifySphereSemanticRole(scene, o);
    if (sphereRole === "INSCRIBED_SPHERE") {
      return {
        role: "INSCRIBED_SPHERE",
        epistemicStatus: isSelected || isHovered ? "explained_focus" : isCertGivenObj ? "given" : "constructed_result",
        fillColor: S.colors.inscribed,
        strokeColor: modulateSemanticColor(S.colors.inscribed, interactionState),
        fillOpacity: isSelected ? 0.22 : isHovered ? 0.19 : S.opacity.inscribedSphereShell,
        prominenceTier: 2,
        isAuxiliaryExplanatorySurface: false,
      };
    }
    if (sphereRole === "CIRCUMSCRIBED_SPHERE") {
      return {
        role: "CIRCUMSCRIBED_SPHERE",
        epistemicStatus: isSelected || isHovered ? "explained_focus" : isCertGivenObj ? "given" : "constructed_result",
        fillColor: S.colors.circumscribedSphere,
        strokeColor: modulateSemanticColor(S.colors.circumscribedSphere, interactionState),
        fillOpacity: isSelected ? 0.14 : isHovered ? 0.11 : S.opacity.circumscribedSphereShell,
        prominenceTier: 2,
        isAuxiliaryExplanatorySurface: false,
      };
    }
  }

  if (o.type === "circle3") {
    const circleRole = classifyCircleSemanticRole(scene, o);
    if (circleRole === "REFERENCE_EQUATOR" || circleRole === "REFERENCE_GREAT_CIRCLE") {
      return {
        role: circleRole,
        epistemicStatus: "auxiliary",
        fillColor: S.colors.hiddenEdge,
        strokeColor: modulateSemanticColor(S.colors.hiddenEdge, interactionState),
        fillOpacity: 0,
        prominenceTier: 4,
        isAuxiliaryExplanatorySurface: false,
      };
    }
    if (circleRole === "INSCRIBED_CIRCLE") {
      return {
        role: "INSCRIBED_CIRCLE",
        epistemicStatus: isSelected || isHovered ? "explained_focus" : isCertGivenObj ? "given" : "constructed_result",
        fillColor: S.colors.inscribed,
        strokeColor: modulateSemanticColor(S.colors.inscribed, interactionState),
        fillOpacity: isSelected ? 0.14 : isHovered ? 0.11 : S.opacity.inscribedCircleFill,
        prominenceTier: 2,
        isAuxiliaryExplanatorySurface: false,
      };
    }
    if (circleRole === "CIRCUMSCRIBED_CIRCLE") {
      return {
        role: "CIRCUMSCRIBED_CIRCLE",
        epistemicStatus: isSelected || isHovered ? "explained_focus" : isCertGivenObj ? "given" : "constructed_result",
        fillColor: S.colors.circumscribedCircle,
        strokeColor: modulateSemanticColor(S.colors.circumscribedCircle, interactionState),
        fillOpacity: 0,
        prominenceTier: 2,
        isAuxiliaryExplanatorySurface: false,
      };
    }
    if (circleRole === "BOUNDARY_AND_INTERSECTION") {
      return {
        role: "BOUNDARY_AND_INTERSECTION",
        epistemicStatus: isSelected || isHovered ? "explained_focus" : isCertGivenObj ? "given" : "constructed_result",
        fillColor: S.colors.mesh,
        strokeColor: modulateSemanticColor(S.colors.canh, interactionState),
        fillOpacity: isSelected ? S.opacity.selectedBase : S.opacity.base,
        prominenceTier: 3,
        isAuxiliaryExplanatorySurface: false,
      };
    }
    return {
      role: "RESULT_SECTION",
      epistemicStatus: isSelected || isHovered ? "explained_focus" : "constructed_result",
      fillColor: S.colors.polygon,
      strokeColor: modulateSemanticColor(S.colors.sectionOutline, interactionState),
      fillOpacity: isSelected ? S.opacity.selectedSection : S.opacity.section,
      prominenceTier: 1,
      isAuxiliaryExplanatorySurface: false,
    };
  }

  const isSolidFace =
    o.type === "face"
    || Boolean(o.type === "polygon3" && o.parent && groups.includes("face"))
    || vaiTroMien(o) === "base";

  if (o.type === "solid" || o.type === "curved_solid" || isSolidFace) {
    return {
      role: "SOLID_SHELL",
      epistemicStatus: isSelected || isHovered ? "explained_focus" : isCertGivenObj ? "given" : "constructed_result",
      fillColor: S.colors.mesh,
      strokeColor: modulateSemanticColor(S.colors.canh, interactionState),
      fillOpacity: isSelected ? S.opacity.selectedSolid : isHovered ? 0.15 : S.opacity.solid,
      prominenceTier: 3,
      isAuxiliaryExplanatorySurface: false,
    };
  }

  if (vaiTroMien(o) === "section") {
    const auxSurface = isAuxiliaryExplanatoryPolygon(scene, o);
    if (auxSurface) {
      return {
        role: "AUXILIARY_CONSTRUCTION",
        epistemicStatus: isSelected || isHovered ? "explained_focus" : "auxiliary",
        fillColor: S.colors.line,
        strokeColor: modulateSemanticColor(S.colors.line, interactionState),
        fillOpacity: isSelected ? 0.26 : isHovered ? 0.22 : 0.18,
        prominenceTier: 4,
        isAuxiliaryExplanatorySurface: true,
      };
    }
    return {
      role: "RESULT_SECTION",
      epistemicStatus: isSelected || isHovered ? "explained_focus" : "constructed_result",
      fillColor: S.colors.polygon,
      strokeColor: modulateSemanticColor(S.colors.sectionOutline, interactionState),
      fillOpacity: isSelected ? S.opacity.selectedSection : S.opacity.section,
      prominenceTier: 1,
      isAuxiliaryExplanatorySurface: false,
    };
  }

  if (o.type === "plane3") {
    const isAux = roles.includes("CONSTRUCT_AUXILIARY_GEOMETRY") && !groups.includes("target");
    return {
      role: "GEOMETRIC_PLANE",
      epistemicStatus: isSelected || isHovered
        ? "explained_focus"
        : isCertGivenOrGroup
          ? "given"
          : isAux
            ? "auxiliary"
            : "constructed_result",
      fillColor: S.colors.surface,
      strokeColor: modulateSemanticColor(S.colors.planeOutline, interactionState),
      fillOpacity: isSelected ? S.opacity.selectedPlane : isHovered ? 0.10 : S.opacity.plane,
      prominenceTier: 4,
      isAuxiliaryExplanatorySurface: false,
    };
  }

  const curvedSegRole = (o.type === "segment3" || o.type === "line3")
    ? classifyCurvedSegmentRole(scene, o)
    : null;

  if (
    o.perpendicular_witness
    || o.annotation?.witness
    || ((o.type === "line3" || o.type === "segment3") && roles.includes("CONSTRUCT_HEIGHT"))
    || curvedSegRole?.kind === "axis"
    || curvedSegRole?.kind === "altitude"
  ) {
    return {
      role: "CERTIFIED_RELATION_MARKER",
      epistemicStatus: isSelected || isHovered ? "explained_focus" : "constructed_result",
      fillColor: S.colors.line,
      strokeColor: modulateSemanticColor(S.colors.line, interactionState),
      fillOpacity: S.opacity.witness,
      prominenceTier: 2,
      isAuxiliaryExplanatorySurface: false,
    };
  }

  if (isIntersectionLineOrSegment(o, scene)) {
    return {
      role: "RESULT_SECTION",
      epistemicStatus: isSelected || isHovered ? "explained_focus" : "constructed_result",
      fillColor: S.colors.sectionOutline,
      strokeColor: modulateSemanticColor(S.colors.sectionOutline, interactionState),
      fillOpacity: 0.96,
      prominenceTier: 1,
      isAuxiliaryExplanatorySurface: false,
    };
  }

  if (isPrimarySpatialLine(o, scene)) {
    return {
      role: "BOUNDARY_AND_INTERSECTION",
      epistemicStatus: isSelected || isHovered
        ? "explained_focus"
        : isCertGivenOrGroup
          ? "given"
          : "constructed_result",
      fillColor: S.colors.circumscribedCircle,
      strokeColor: modulateSemanticColor(S.colors.circumscribedCircle, interactionState),
      fillOpacity: 0.92,
      prominenceTier: 2,
      isAuxiliaryExplanatorySurface: false,
    };
  }

  if (
    o.type === "segment3"
    && (roles.includes("CONSTRUCT_LATERAL_BOUNDARY") || Boolean(o.boundary_edge_ids?.length))
  ) {
    const endpointIds = o.endpoint_ids?.length ? o.endpoint_ids : (o.depends ?? []);
    const endpointsCertifiedGiven =
      endpointIds.length > 0
      && endpointIds.every((id) => {
        const pt = byIdForSem.get(id);
        if (!pt) return false;
        return pt.type === "point3"
          ? isCertifiedGivenSceneObject(scene, pt)
          : pt.authoritative !== false && !hasUncertifiedObjectSource(pt);
      });
    const parentObj = o.parent ? byIdForSem.get(o.parent) : undefined;
    const isLateralCertGiven =
      o.authoritative !== false
      && !hasUncertifiedObjectSource(o)
      && (!parentObj || (parentObj.authoritative !== false && !hasUncertifiedObjectSource(parentObj)))
      && endpointsCertifiedGiven;
    return {
      role: "BOUNDARY_AND_INTERSECTION",
      epistemicStatus: isSelected || isHovered ? "explained_focus" : isLateralCertGiven ? "given" : "constructed_result",
      fillColor: S.colors.canh,
      strokeColor: modulateSemanticColor(S.colors.canh, interactionState),
      fillOpacity: 1,
      prominenceTier: 3,
      isAuxiliaryExplanatorySurface: false,
    };
  }

  if (o.type === "line3" || o.type === "segment3") {
    const isTarget = groups.includes("target");
    return {
      role: isTarget ? "BOUNDARY_AND_INTERSECTION" : "AUXILIARY_CONSTRUCTION",
      epistemicStatus: isSelected || isHovered
        ? "explained_focus"
        : isCertGivenOrGroup
          ? "given"
          : isTarget
            ? "constructed_result"
            : "auxiliary",
      fillColor: S.colors.line,
      strokeColor: modulateSemanticColor(S.colors.line, interactionState),
      fillOpacity: isTarget ? 0.92 : S.opacity.auxiliary,
      prominenceTier: isTarget ? 2 : 4,
      isAuxiliaryExplanatorySurface: false,
    };
  }

  const basePointOrEdge = o.type === "point3"
    ? (isCertGivenObj ? S.colors.free : S.colors.derived)
    : S.colors.canh;
  return {
    role: "BOUNDARY_AND_INTERSECTION",
    epistemicStatus: isSelected || isHovered ? "explained_focus" : isCertGivenObj ? "given" : "constructed_result",
    fillColor: basePointOrEdge,
    strokeColor: modulateSemanticColor(basePointOrEdge, interactionState),
    fillOpacity: 1,
    prominenceTier: 3,
    isAuxiliaryExplanatorySurface: false,
  };
}

export function isIntersectionLineOrSegment(
  o: SceneObject,
  scene?: Pick<Scene3D, "objects">,
): boolean {
  if (o.type !== "line3" && o.type !== "segment3") return false;
  const roles = o.formation_roles ?? [];
  const srcInst = String((o.source as Record<string, unknown> | undefined)?.instruction ?? "");
  if (
    o.semantic_role === "RESULT_SECTION"
    || roles.includes("PRODUCE_SECTION_RESULT")
    || roles.includes("CONSTRUCT_INTERSECTION")
    || roles.includes("DERIVE_INTERSECTION")
    || srcInst.includes("intersect")
  ) {
    return true;
  }
  if (scene && o.origin === "derived" && (o.depends?.length ?? 0) >= 2) {
    const planeDeps = (o.depends ?? []).filter((id) => {
      const dep = scene.objects.find((x) => x.id === id);
      return dep?.type === "plane3" || dep?.type === "polygon3";
    });
    if (planeDeps.length >= 2) return true;
  }
  if (!scene && o.origin === "derived") {
    return String(o.producer ?? "").includes("intersect");
  }
  return false;
}

export function isPrimarySpatialLine(o: SceneObject, scene?: Pick<Scene3D, "objects">): boolean {
  if (o.type !== "line3" || isIntersectionLineOrSegment(o, scene)) return false;
  const roles = o.formation_roles ?? [];
  if (o.perpendicular_witness || o.annotation?.witness || roles.includes("CONSTRUCT_HEIGHT")) {
    return false;
  }
  const groups = o.display_group ?? [];
  return o.origin === "free" || groups.includes("given") || groups.includes("target");
}

export type PlaneSectionLifecycleStage =
  | "primary_focus"
  | "active_carrier"
  | "attenuated_support"
  | "consolidated_section_support"
  | "retired_scaffold";

export interface PlaneSectionVisibilityDecision {
  visible: boolean;
  subRole: PlaneSemanticSubRole;
  opacityScale: number;
  lifecycleStage: PlaneSectionLifecycleStage;
  showPlaneLabel: boolean;
}

export interface AxialCurvedOrthogonality {
  isRightCertified: boolean;
  isOblique: boolean;
  isTiltedAxisInSpace: boolean;
  baseNormal: FracVec3 | null;
  isIllustrativeBasePlane?: boolean;
}

/**
 * Kiểm chứng chính xác trên ℚ³ xem khối có trục (`cylinder` / `cone`) là khối tròn xoay trục vuông góc mặt đáy
 * hay khối trụ xiên (`OO′` không vuông góc mặt đáy):
 * - Không mặc định tính chất hình trụ đứng (`OO′ ⊥ đáy`, thiết diện qua trục là hình chữ nhật) nếu pháp tuyến đường tròn đáy
 *   không song song `OO′` hoặc điểm vành đáy khai báo `A` không thỏa `(A - O) · (O′ - O) = 0`.
 * - Phân biệt rõ `OO′ ⊥ OA` (chỉ vuông góc một bán kính đơn lẻ) với `OO′ ⊥ mặt phẳng đáy`: nếu `label`/`role`/`source`
 *   khai báo trụ xiên, không vuông góc hoặc cấu hình minh họa thì không bao giờ nâng lên trụ đứng từ một bán kính đơn lẻ.
 * - Phân biệt rõ hình trụ tròn xoay có trục đặt xiên trong không gian (`tru-truc-xien`: `OO′` nghiêng so với `Oz` nhưng vẫn `⊥` hai đáy tròn)
 *   với hình trụ xiên thực sự (`OO′` nghiêng với mặt phẳng đáy).
 */
export function inspectAxialCurvedOrthogonality(
  scene: Pick<Scene3D, "objects" | "chart_metric">,
  cs: SceneObject,
): AxialCurvedOrthogonality {
  const exactScene = exactSceneOriginOf(scene);
  const exactById = new Map(exactScene.objects.map((o) => [o.id, o]));
  const s = exactById.get(cs.id) ?? cs;
  const sApexOrTop = s.apex_or_top ?? (s as SceneObject & { apex?: ExactVec3 | null }).apex ?? undefined;
  if (
    s.type !== "curved_solid"
    || (s.curved_kind !== "cylinder" && s.curved_kind !== "cone")
    || !s.anchor
    || !sApexOrTop
  ) {
    return { isRightCertified: false, isOblique: false, isTiltedAxisInSpace: false, baseNormal: null };
  }
  const A = parseFracVec3(s.anchor);
  const T = parseFracVec3(sApexOrTop);
  const ax = vSub(T, A);
  if (vIsZero(ax)) {
    return { isRightCertified: false, isOblique: false, isTiltedAxisInSpace: false, baseNormal: null };
  }
  const zAxis: FracVec3 = [
    [0n, 1n],
    [0n, 1n],
    [1n, 1n],
  ];
  const isTiltedAxisInSpace = !vParallel(ax, zAxis);

  let isOblique = false;
  let hasCapCircleNormal = false;
  let hasAuthoritativeCapCircleNormal = false;
  let baseNormal: FracVec3 = ax;
  let sampleRimVec: FracVec3 | null = null;

  for (const c of exactScene.objects) {
    if (c.type !== "circle3" || !c.center || !c.normal) continue;
    const isBaseCap =
      c.surface_role === "BASE_REGION"
      || ((c.depends ?? []).includes(s.id) && (vIsZero(vSub(parseFracVec3(c.center), A)) || vIsZero(vSub(parseFracVec3(c.center), T))));
    if (!isBaseCap) continue;
    const cCenter = parseFracVec3(c.center);
    if (!vIsZero(vSub(cCenter, A)) && !vIsZero(vSub(cCenter, T))) continue;
    const nCap = parseFracVec3(c.normal);
    if (!vIsZero(nCap)) {
      hasCapCircleNormal = true;
      if (c.authoritative !== false && !hasUncertifiedObjectSource(c)) {
        hasAuthoritativeCapCircleNormal = true;
      }
      baseNormal = nCap;
      if (!vParallel(nCap, ax)) {
        isOblique = true;
      }
    }
  }

  const gMetric = isSceneWorldTransformed(exactScene) ? undefined : exactScene.chart_metric;
  if (s.rim_point) {
    const P = parseFracVec3(s.rim_point);
    if (!vIsZero(vSub(P, A)) && !vIsZero(vSub(P, T))) {
      const rBase = vSub(P, A);
      const rTop = vSub(P, T);
      const orthoBase = fIsZero(metricDot(rBase, ax, gMetric));
      const orthoTop = s.curved_kind === "cylinder" && fIsZero(metricDot(rTop, ax, gMetric));
      if (!sampleRimVec && !vIsZero(vCross(rBase, ax))) sampleRimVec = rBase;
      if (!orthoBase && !orthoTop) {
        isOblique = true;
      }
    }
  }

  for (const depId of s.depends ?? []) {
    const pt = exactById.get(depId);
    if (!pt || pt.type !== "point3" || !pt.xyz) continue;
    const P = parseFracVec3(pt.xyz);
    if (vIsZero(vSub(P, A)) || vIsZero(vSub(P, T))) continue;
    const rBase = vSub(P, A);
    const rTop = vSub(P, T);
    const orthoBase = fIsZero(metricDot(rBase, ax, gMetric));
    const orthoTop = s.curved_kind === "cylinder" && fIsZero(metricDot(rTop, ax, gMetric));
    if (!sampleRimVec && !vIsZero(vCross(rBase, ax))) sampleRimVec = rBase;
    if (!orthoBase && !orthoTop) {
      isOblique = true;
    }
  }

  const textTag = `${s.label ?? ""} ${s.role ?? ""}`;
  const declaredObliqueText =
    (/\b(trụ|nón)\s+xiên\b/iu.test(textTag) && !/\btrục\s+xiên\b/iu.test(textTag))
    || /\bkhông\s+vuông\s+góc\b/iu.test(textTag)
    || /không\s*⊥/u.test(textTag);
  const sSrc = s.source as Record<string, unknown> | undefined;
  const declaredIllustrative =
    sSrc?.is_given === false
    || sSrc?.assumption === "ILLUSTRATIVE_CONFIGURATION"
    || sSrc?.assumption === "LAYOUT_DERIVED"
    || sSrc?.provenance === "LAYOUT_DERIVED";

  if (declaredObliqueText || declaredIllustrative) {
    isOblique = true;
  }

  let isIllustrativeBasePlane = false;
  if (isOblique && !hasAuthoritativeCapCircleNormal) {
    isIllustrativeBasePlane = true;
    if (!hasCapCircleNormal && sampleRimVec && !vIsZero(vCross(sampleRimVec, ax))) {
      // Chọn mặt phẳng đáy minh họa chứa bán kính OA (`baseNormal ⊥ sampleRimVec`):
      // - Khi `OA · OO′ ≠ 0`, `(OA × OO′) × OA` vuông góc `OA` và nghiêng với `OO′` một cách tất định.
      // - Khi `OA · OO′ = 0` nhưng đề khai trụ xiên / chưa vuông góc đáy (mặt đáy quay tự do quanh OA),
      //   xoay pháp tuyến quanh `OA` sang `ax + (OA × ax)` để không ngầm biến thành trụ đứng.
      const perpInPlane = vCross(vCross(sampleRimVec, ax), sampleRimVec);
      if (!vIsZero(perpInPlane) && !vParallel(perpInPlane, ax)) {
        baseNormal = perpInPlane;
      } else {
        const tiltedAroundRim = vAdd(ax, vCross(sampleRimVec, ax));
        if (!vIsZero(tiltedAroundRim) && !vParallel(tiltedAroundRim, ax)) {
          baseNormal = tiltedAroundRim;
        }
      }
    }
  }

  return {
    isRightCertified: !isOblique,
    isOblique,
    isTiltedAxisInSpace,
    baseNormal,
    ...(isIllustrativeBasePlane ? { isIllustrativeBasePlane: true } : {}),
  };
}

export function classifyCurvedSegmentRole(
  scene: Pick<Scene3D, "objects" | "chart_metric">,
  seg: SceneObject,
): {
  host: SceneObject;
  kind: "axis" | "center_line" | "radius" | "generator" | "altitude";
  isOblique: boolean;
  isTiltedAxisInSpace: boolean;
} | null {
  if (seg.type !== "segment3" && seg.type !== "line3") return null;
  const exactScene = exactSceneOriginOf(scene);
  const byId = new Map(exactScene.objects.map((o) => [o.id, o]));
  const exactSeg = byId.get(seg.id) ?? seg;
  let rawA: ExactVec3 | undefined = exactSeg.point_a ?? exactSeg.endpoints?.[0];
  let rawB: ExactVec3 | undefined = exactSeg.point_b ?? exactSeg.endpoints?.[1];
  if (!rawA || !rawB) {
    const depPts = (exactSeg.depends ?? [])
      .map((id) => byId.get(id))
      .filter((p): p is SceneObject => Boolean(p && p.type === "point3" && p.xyz));
    if (depPts.length === 2) {
      rawA = depPts[0].xyz;
      rawB = depPts[1].xyz;
    }
  }
  if (!rawA || !rawB) return null;
  const pA = parseFracVec3(rawA);
  const pB = parseFracVec3(rawB);
  const segVec = vSub(pB, pA);
  if (vIsZero(segVec)) return null;

  for (const s of exactScene.objects) {
    if (s.type !== "curved_solid" || !s.anchor) continue;
    const A = parseFracVec3(s.anchor);
    const rSq = s.radius_sq ? parseExactFrac(s.radius_sq) : null;

    if (s.curved_kind === "ball") {
      const aAtCenter = vIsZero(vSub(pA, A));
      const bAtCenter = vIsZero(vSub(pB, A));
      if (aAtCenter || bAtCenter) {
        const other = aAtCenter ? pB : pA;
        const radial = vSub(other, A);
        if (!vIsZero(radial) && (!rSq || fEq(metricDot(radial, radial, exactScene.chart_metric), rSq))) {
          return { host: s, kind: "radius", isOblique: false, isTiltedAxisInSpace: false };
        }
      }
      continue;
    }

    const sApexOrTop = s.apex_or_top ?? (s as SceneObject & { apex?: ExactVec3 | null }).apex ?? undefined;
    if ((s.curved_kind !== "cone" && s.curved_kind !== "cylinder") || !sApexOrTop) {
      continue;
    }
    const T = parseFracVec3(sApexOrTop);
    const ax = vSub(T, A);
    if (vIsZero(ax)) continue;
    const ortho = inspectAxialCurvedOrthogonality(exactScene, s);
    const capNorm = ortho.baseNormal ?? ax;

    const aAtBase = vIsZero(vSub(pA, A));
    const bAtBase = vIsZero(vSub(pB, A));
    const aAtTop = vIsZero(vSub(pA, T));
    const bAtTop = vIsZero(vSub(pB, T));

    if ((aAtBase && bAtTop) || (aAtTop && bAtBase)) {
      return {
        host: s,
        kind: ortho.isOblique ? "center_line" : "axis",
        isOblique: ortho.isOblique,
        isTiltedAxisInSpace: ortho.isTiltedAxisInSpace,
      };
    }

    if (
      ortho.isOblique
      && vParallel(segVec, capNorm)
      && ((aAtTop && fIsZero(plainDotFrac(vSub(pB, A), capNorm)))
        || (bAtTop && fIsZero(plainDotFrac(vSub(pA, A), capNorm))))
    ) {
      return {
        host: s,
        kind: "altitude",
        isOblique: true,
        isTiltedAxisInSpace: ortho.isTiltedAxisInSpace,
      };
    }

    const onCapRim = (pt: FracVec3, center: FracVec3): boolean => {
      const radial = vSub(pt, center);
      if (vIsZero(radial)) return false;
      if (!fIsZero(plainDotFrac(radial, capNorm))) return false;
      return rSq ? fEq(metricDot(radial, radial, exactScene.chart_metric), rSq) : true;
    };

    if (
      (aAtBase && onCapRim(pB, A))
      || (bAtBase && onCapRim(pA, A))
      || (s.curved_kind === "cylinder" && ((aAtTop && onCapRim(pB, T)) || (bAtTop && onCapRim(pA, T))))
    ) {
      return {
        host: s,
        kind: "radius",
        isOblique: ortho.isOblique,
        isTiltedAxisInSpace: ortho.isTiltedAxisInSpace,
      };
    }

    if (s.curved_kind === "cone" && ((aAtTop && onCapRim(pB, A)) || (bAtTop && onCapRim(pA, A)))) {
      return {
        host: s,
        kind: "generator",
        isOblique: ortho.isOblique,
        isTiltedAxisInSpace: ortho.isTiltedAxisInSpace,
      };
    }

    if (
      s.curved_kind === "cylinder"
      && vIsZero(vCross(segVec, ax))
      && ((onCapRim(pA, A) && onCapRim(pB, T)) || (onCapRim(pA, T) && onCapRim(pB, A)))
    ) {
      return {
        host: s,
        kind: "generator",
        isOblique: ortho.isOblique,
        isTiltedAxisInSpace: ortho.isTiltedAxisInSpace,
      };
    }
  }
  return null;
}

function isDuplicateOfSolidFace(scene: Scene3D, planeObj: SceneObject): boolean {
  if (measurementOnlyPlanes(scene).has(planeObj.id)) return true;
  const groups = planeObj.display_group ?? [];
  const dependents = scene.objects.filter((x) => !x.parent && (x.depends ?? []).includes(planeObj.id));
  const faceVertexSets = scene.objects.flatMap((o) =>
    o.type === "solid" && o.vertex_ids && o.faces
      ? o.faces.map((f) => new Set(f.map((i) => o.vertex_ids![i])))
      : [],
  );
  const deps = planeObj.depends ?? [];
  if (
    planeObj.origin === "derived"
    && !groups.includes("given")
    && !groups.includes("target")
    && !(planeObj.formation_roles ?? []).includes("CONSTRUCT_CUTTING_OBJECT")
    && dependents.length > 0
    && dependents.every(
      (x) => x.type === "quantity" || x.type === "point3" || x.type === "segment3" || x.type === "line3",
    )
    && deps.length >= 3
    && faceVertexSets.some((fSet) => deps.every((id) => fSet.has(id)))
  ) {
    return true;
  }
  if (planeObj.origin !== "derived" || groups.includes("given") || groups.includes("target")) return false;

  // Kiểm tra mặt phẳng mang đáy/nắp nội tại của hình nón hoặc hình trụ (`mp_day_*`, `mp_day_tren_*`):
  // trùng mặt phẳng đáy tròn vuông góc trục của `curved_solid` và chỉ sinh ra vành đáy `BASE_REGION`.
  if (
    planeObj.point
    && planeObj.normal
    && dependents.every(
      (x) =>
        x.type === "quantity"
        || (x.type === "circle3"
          && (x.surface_role === "BASE_REGION" || classifyCircleSemanticRole(scene, x) === "BOUNDARY_AND_INTERSECTION")),
    )
  ) {
    const pPl = parseFracVec3(planeObj.point);
    const nPl = parseFracVec3(planeObj.normal);
    if (!vIsZero(nPl)) {
      const matchesCurvedCap = scene.objects.some((s) => {
        if (
          s.type !== "curved_solid"
          || (s.curved_kind !== "cone" && s.curved_kind !== "cylinder")
          || !s.anchor
          || !s.apex_or_top
        ) {
          return false;
        }
        const A = parseFracVec3(s.anchor);
        const T = parseFracVec3(s.apex_or_top);
        const ax = vSub(T, A);
        if (vIsZero(ax) || !vIsZero(vCross(nPl, ax))) return false;
        const atBase = fIsZero(plainDotFrac(vSub(A, pPl), nPl));
        const atTop = s.curved_kind === "cylinder" && fIsZero(plainDotFrac(vSub(T, pPl), nPl));
        return atBase || atTop;
      });
      if (matchesCurvedCap) return true;
    }
  }

  if (!dependents.every((x) => x.type === "quantity")) return false;
  if (deps.length >= 3 && faceVertexSets.some((fSet) => deps.every((id) => fSet.has(id)))) {
    return true;
  }
  if (
    dependents.length > 0
    && (planeObj.formation_roles ?? []).includes("CONSTRUCT_AUXILIARY_GEOMETRY")
    && planeObj.point
    && planeObj.normal
  ) {
    const pPl = parseFracVec3(planeObj.point);
    const nPl = parseFracVec3(planeObj.normal);
    if (!vIsZero(nPl)) {
      const duplicatesExistingPlane = scene.objects.some((other) => {
        if (other.id === planeObj.id || other.type !== "plane3" || !other.point || !other.normal) return false;
        if ((other.formation_roles ?? []).includes("CONSTRUCT_AUXILIARY_GEOMETRY")) return false;
        const pO = parseFracVec3(other.point);
        const nO = parseFracVec3(other.normal);
        return !vIsZero(nO) && vIsZero(vCross(nPl, nO)) && fIsZero(plainDotFrac(vSub(pPl, pO), nO));
      });
      if (duplicatesExistingPlane) return true;
    }
  }
  return false;
}

export interface SolidFaceCarrierOverlay {
  planeId: string;
  vertices: ExactVec3[];
  rank: number;
  isSelected: boolean;
}

/**
 * Khi một `plane3` trùng mặt bên của khối đa diện (`SOLID_FACE_DUPLICATE_PLANE`) nhưng đóng vai trò
 * mặt phẳng mang giao tuyến hai mặt phẳng (như `(SAB) ∩ (SCD)`) hoặc mặt phẳng đối chiếu góc/khoảng cách
 * (như góc giữa `BC` và `(SAB)`), trả về đúng đa giác mặt bên giới hạn trên khối để tô nền dịu trực quan
 * mà không vẽ mảng chữ nhật vô hạn đâm xuyên khối.
 */
export function resolveSolidFaceDuplicateCarrierPolygons(
  scene: Scene3D,
  step: number,
  selectedId: string | null = null,
): SolidFaceCarrierOverlay[] {
  const k = clampStep(scene, step);
  const presentIds = new Set(objectsAt(scene, k).map((o) => o.id));
  const exactScene = exactSceneOriginOf(scene);
  const exactById = new Map(exactScene.objects.map((o) => [o.id, o]));

  const baseFaceKeys = new Set<string>();
  for (const p of scene.objects) {
    if (
      p.type === "polygon3"
      && p.vertex_ids?.length
      && (vaiTroMien(p) === "base" || isPolyhedronOppositeTopBasePolygon(scene, p))
    ) {
      baseFaceKeys.add([...p.vertex_ids].sort().join("|"));
    }
  }
  for (const sol of scene.objects) {
    if (sol.type !== "solid" || !sol.vertex_ids?.length || !sol.faces?.length) continue;
    if (baseFaceKeys.size === 0 && sol.faces.some((f) => f.length > 3) && sol.faces.some((f) => f.length === 3)) {
      for (const f of sol.faces) {
        if (f.length > 3) {
          const vids = f.map((i) => sol.vertex_ids![i]).filter(Boolean);
          if (vids.length === f.length) baseFaceKeys.add([...vids].sort().join("|"));
        }
      }
    }
  }

  const overlays: SolidFaceCarrierOverlay[] = [];
  for (const mp of scene.objects) {
    if (mp.type !== "plane3" || !presentIds.has(mp.id) || !isDuplicateOfSolidFace(scene, mp)) continue;
    const isSelected = selectedId === mp.id;
    const isInterCarrier = scene.objects.some(
      (x) => !isSubEntity(x.id) && isIntersectionLineOrSegment(x, scene) && (x.depends ?? []).includes(mp.id),
    );
    const isRelQtyCarrier = scene.objects.some(
      (x) =>
        x.type === "quantity"
        && (x.depends ?? []).includes(mp.id)
        && (x.depends ?? []).some((d) => d !== mp.id),
    );
    if (!isSelected && !isInterCarrier && !isRelQtyCarrier) continue;

    // Nếu đã có sẵn `polygon3` tường minh trùng mặt này thì không vẽ chồng thêm lớp phủ
    const mpDeps = mp.depends ?? [];
    const exMp = exactById.get(mp.id) ?? mp;
    let matchedVerts: ExactVec3[] | null = null;

    for (const sol of scene.objects) {
      if (sol.type !== "solid" || !presentIds.has(sol.id) || !sol.faces?.length || !sol.vertices?.length) continue;
      const exSol = exactById.get(sol.id) ?? sol;
      for (const f of sol.faces) {
        if (f.length < 3) continue;
        const fVids = sol.vertex_ids ? f.map((i) => sol.vertex_ids![i]).filter(Boolean) : [];
        const faceKey = fVids.length === f.length ? [...fVids].sort().join("|") : "";
        if (faceKey && baseFaceKeys.has(faceKey)) continue;
        if (
          faceKey
          && scene.objects.some(
            (po) =>
              po.type === "polygon3"
              && !isSubEntity(po.id)
              && !(po.parent && (po.display_group ?? []).includes("face"))
              && presentIds.has(po.id)
              && po.vertex_ids?.length === f.length
              && [...po.vertex_ids].sort().join("|") === faceKey,
          )
        ) {
          continue;
        }
        const matchByDeps =
          mpDeps.length >= 3 && fVids.length === f.length && mpDeps.every((id) => fVids.includes(id));
        const matchByPlaneEq =
          !matchByDeps
          && Boolean(exMp.point && exMp.normal && exSol.vertices?.length)
          && (() => {
            const pPl = parseFracVec3(exMp.point!);
            const nPl = parseFracVec3(exMp.normal!);
            if (vIsZero(nPl)) return false;
            return f.every(
              (idx) =>
                Boolean(exSol.vertices![idx])
                && fIsZero(plainDotFrac(vSub(parseFracVec3(exSol.vertices![idx]), pPl), nPl)),
            );
          })();
        if (matchByDeps || matchByPlaneEq) {
          const verts = f.map((idx) => sol.vertices![idx]).filter((v): v is ExactVec3 => Boolean(v));
          if (verts.length === f.length) {
            matchedVerts = verts;
            break;
          }
        }
      }
      if (matchedVerts) break;
    }

    if (matchedVerts) {
      overlays.push({
        planeId: mp.id,
        vertices: matchedVerts,
        rank: overlays.length,
        isSelected,
      });
    }
  }
  return overlays;
}

export interface PlanePerpendicularLineWitnessRender {
  foot: [number, number, number];
  uUnit: [number, number, number];
  vUnit: [number, number, number];
  spanLen: number;
  circleRadius: number | null;
}

export function resolvePlanePerpendicularLineWitness(
  scene: Pick<Scene3D, "objects">,
  mp: SceneObject,
  visibleObjects?: readonly SceneObject[],
): PlanePerpendicularLineWitnessRender | null {
  if (mp.type !== "plane3" || !mp.point || !mp.normal) return null;
  if (!("events" in scene) || !Array.isArray((scene as Scene3D).events)) return null;
  const fullScene = scene as Scene3D;
  const semMp = resolveSemanticObjectContract(fullScene, mp.id);
  const perpRel = semMp?.verifiedRelations.find((r) => r.kind === "line_perp_plane" && r.canDisplaySymbol);
  if (!perpRel || perpRel.targetIds.length === 0) return null;

  const visList = visibleObjects ?? scene.objects;
  const hasSegWitnessOnPlane = visList.some(
    (s) =>
      s.type === "segment3"
      && (s.perpendicular_witness?.on === mp.id || s.annotation?.witness?.on === mp.id),
  );
  if (hasSegWitnessOnPlane) return null;

  const exactOrigin = exactSceneOriginOf(scene);
  const exById = new Map(exactOrigin.objects.map((o) => [o.id, o]));
  const curById = new Map(scene.objects.map((o) => [o.id, o]));
  const visIdSet = new Set(visList.map((o) => o.id));
  const exMp = exById.get(mp.id) ?? mp;
  if (!exMp.point || !exMp.normal) return null;
  const exMpPt = parseFracVec3(exMp.point);
  const exMpNorm = parseFracVec3(exMp.normal);
  if (vIsZero(exMpNorm)) return null;

  const lnId = perpRel.targetIds[0];
  const exLn = exById.get(lnId) ?? curById.get(lnId);
  const curLn = curById.get(lnId);
  if (!exLn || !curLn) return null;

  let exLnPt: FracVec3 | null = null;
  let exLnDir: FracVec3 | null = null;
  if (exLn.point && exLn.direction) {
    exLnPt = parseFracVec3(exLn.point);
    exLnDir = parseFracVec3(exLn.direction);
  } else if (exLn.point_a && exLn.point_b) {
    exLnPt = parseFracVec3(exLn.point_a);
    exLnDir = vSub(parseFracVec3(exLn.point_b), exLnPt);
  } else if ((exLn.endpoints?.length ?? 0) >= 2) {
    exLnPt = parseFracVec3(exLn.endpoints![0]);
    exLnDir = vSub(parseFracVec3(exLn.endpoints![1]), exLnPt);
  } else {
    const depPts = (exLn.endpoint_ids?.length ? exLn.endpoint_ids : (exLn.depends ?? []))
      .map((id) => exById.get(id))
      .filter((p): p is SceneObject => Boolean(p && p.type === "point3" && p.xyz));
    if (depPts.length >= 2) {
      exLnPt = parseFracVec3(depPts[0].xyz!);
      exLnDir = vSub(parseFracVec3(depPts[1].xyz!), exLnPt);
    }
  }
  if (!exLnPt || !exLnDir || vIsZero(exLnDir)) return null;

  const candidatePts = [
    ...(mp.depends ?? []).map((id) => curById.get(id)).filter((p): p is SceneObject => Boolean(p)),
    ...visList.filter((p) => p.type === "point3"),
  ];
  let footCur: SceneObject | null = null;
  for (const cand of candidatePts) {
    if (cand.type !== "point3" || !cand.xyz || !visIdSet.has(cand.id)) continue;
    const exCand = exById.get(cand.id) ?? cand;
    if (!exCand.xyz) continue;
    const exXyz = parseFracVec3(exCand.xyz);
    const onPlane = fIsZero(plainDotFrac(vSub(exXyz, exMpPt), exMpNorm));
    const onLine = vIsZero(vCross(vSub(exXyz, exLnPt), exLnDir));
    if (onPlane && onLine) {
      footCur = cand;
      break;
    }
  }
  if (!footCur?.xyz) return null;

  const foot = toVec3(footCur.xyz);
  const mpNormScene = toVec3(mp.normal);
  const nLen = Math.hypot(mpNormScene[0], mpNormScene[1], mpNormScene[2]);
  if (nLen <= 1e-8) return null;

  let vx = mpNormScene[0] / nLen;
  let vy = mpNormScene[1] / nLen;
  let vz = mpNormScene[2] / nLen;
  if (curLn.direction) {
    const ld = toVec3(curLn.direction);
    const lLen = Math.hypot(ld[0], ld[1], ld[2]);
    if (lLen > 1e-8) {
      vx = ld[0] / lLen; vy = ld[1] / lLen; vz = ld[2] / lLen;
    }
  } else {
    const pa = curLn.point_a ?? curLn.endpoints?.[0];
    const pb = curLn.point_b ?? curLn.endpoints?.[1];
    if (pa && pb) {
      const va = toVec3(pa), vb = toVec3(pb);
      const dx = vb[0] - va[0], dy = vb[1] - va[1], dz = vb[2] - va[2];
      const lLen = Math.hypot(dx, dy, dz);
      if (lLen > 1e-8) {
        vx = dx / lLen; vy = dy / lLen; vz = dz / lLen;
      }
    }
  }

  let spanLen = 2.0;
  const lineNamedPts = [
    ...(curLn.depends ?? []).map((id) => curById.get(id)),
    ...visList.filter((p) => p.type === "point3"),
  ].filter((p): p is SceneObject => Boolean(p && p.type === "point3" && p.xyz && p.id !== footCur!.id));
  let bestUpperDist = 0;
  let bestAnyDist = 0;
  let bestDirSign = 1;
  for (const lp of lineNamedPts) {
    const pv = toVec3(lp.xyz!);
    const dx = pv[0] - foot[0], dy = pv[1] - foot[1], dz = pv[2] - foot[2];
    const d = Math.hypot(dx, dy, dz);
    if (d <= 1e-5) continue;
    const align = Math.abs(dx * vx + dy * vy + dz * vz) / d;
    if (align < 0.999) continue;
    const sign = dx * vx + dy * vy + dz * vz >= 0 ? 1 : -1;
    if (pv[2] > foot[2] + 1e-4 && d > bestUpperDist) {
      bestUpperDist = d;
      bestDirSign = sign;
    }
    if (d > bestAnyDist) {
      bestAnyDist = d;
      if (bestUpperDist === 0) bestDirSign = sign;
    }
  }
  if (bestUpperDist > 0) spanLen = bestUpperDist;
  else if (bestAnyDist > 0) spanLen = bestAnyDist;
  vx *= bestDirSign;
  vy *= bestDirSign;
  vz *= bestDirSign;

  const nnx = mpNormScene[0] / nLen, nny = mpNormScene[1] / nLen, nnz = mpNormScene[2] / nLen;
  const [ux, uy, uz] = computeOptimalInPlaneWitnessBasis([nnx, nny, nnz], resolveSceneLocalViewRay(scene));

  let circleRadius: number | null = null;
  const circleSearchPools: readonly (readonly SceneObject[])[] =
    visList === scene.objects ? [visList] : [visList, scene.objects];
  for (const pool of circleSearchPools) {
    if (circleRadius !== null) break;
    for (const c of pool) {
      if (c.type !== "circle3" || !c.center || !c.normal || !c.radius_sq) continue;
      const cc = toVec3(c.center);
      if (Math.hypot(cc[0] - foot[0], cc[1] - foot[1], cc[2] - foot[2]) > 1e-4) continue;
      const cn = toVec3(c.normal);
      const cnLen = Math.hypot(cn[0], cn[1], cn[2]);
      if (cnLen <= 1e-8) continue;
      if (Math.abs(cn[0] * nnx + cn[1] * nny + cn[2] * nnz) / cnLen < 0.999) continue;
      const r = Math.sqrt(Math.max(0, toNumber(c.radius_sq)));
      if (r > 1e-5) {
        circleRadius = r;
        break;
      }
    }
  }
  if (circleRadius === null) {
    for (const cs of visList) {
      if (cs.type !== "curved_solid" || cs.curved_kind !== "cylinder" || !cs.radius_sq) continue;
      const r = Math.sqrt(Math.max(0, toNumber(cs.radius_sq)));
      if (r <= 1e-5) continue;
      const b0 = cs.anchor ? toVec3(cs.anchor) : null;
      const b1 = cs.apex_or_top ? toVec3(cs.apex_or_top) : null;
      if (b0 && b1) {
        const ax = b1[0] - b0[0], ay = b1[1] - b0[1], az = b1[2] - b0[2];
        const aLen = Math.hypot(ax, ay, az);
        if (aLen > 1e-6 && Math.abs(ax * nnx + ay * nny + az * nnz) / aLen > 0.999) {
          const fx = foot[0] - b0[0], fy = foot[1] - b0[1], fz = foot[2] - b0[2];
          const crossAxis = Math.hypot(fy * az - fz * ay, fz * ax - fx * az, fx * ay - fy * ax) / aLen;
          if (crossAxis <= 1e-4) {
            circleRadius = r;
            break;
          }
        }
      }
    }
  }

  return {
    foot,
    uUnit: [ux, uy, uz],
    vUnit: [vx, vy, vz],
    spanLen,
    circleRadius,
  };
}

/**
 * Chọn vector đơn vị `uUnit` nằm trong mặt phẳng có pháp tuyến `planeNormal` sao cho ô ký hiệu vuông góc
 * `span(uUnit, nHat)` đạt độ mở 3D cực đại theo tia nhìn chuẩn `canonicalViewRay` (`uUnit = ±(rHat × nHat)/|rHat × nHat|`),
 * có hướng bất biến khi đảo dấu pháp tuyến `n -> -n` và suy biến êm về phương ngang màn hình khi mặt phẳng trực diện tia nhìn.
 */
const _sceneLocalViewRayCache = new WeakMap<Pick<Scene3D, "objects">, Vec3>();

export function resolveSceneLocalViewRay(scene: Pick<Scene3D, "objects"> | undefined | null): Vec3 {
  if (!scene) return [8, 3, 6];
  const cached = _sceneLocalViewRayCache.get(scene);
  if (cached) return cached;
  const dc = dayVaDinhChop(scene.objects);
  const len = dc ? huongLenHienThi(dc.day, dc.dinh) : null;
  const q = len
    ? new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(...len), new THREE.Vector3(0, 0, 1))
    : new THREE.Quaternion();
  const ct = cauTrucSuPham(scene.objects, q);
  const worldRay: Vec3 = ct.canh.length > 0
    ? chonHuongNhin(ct.diem, ct.canh, ct.mat, ct.tuyChon)
    : [8, 3, 6];
  const localVec = new THREE.Vector3(worldRay[0], worldRay[1], worldRay[2]).applyQuaternion(q.clone().invert());
  const out: Vec3 = [localVec.x, localVec.y, localVec.z];
  _sceneLocalViewRayCache.set(scene, out);
  return out;
}

export function clampInPlaneRayToPolygon(
  foot: Vec3,
  uUnit: Vec3,
  vUnit: Vec3,
  polyVerts: readonly ExactVec3[],
  defaultLen: number,
  minLen: number,
): number {
  if (polyVerts.length < 3) return defaultLen;
  const wx = vUnit[1] * uUnit[2] - vUnit[2] * uUnit[1];
  const wy = vUnit[2] * uUnit[0] - vUnit[0] * uUnit[2];
  const wz = vUnit[0] * uUnit[1] - vUnit[1] * uUnit[0];
  let minHit = Infinity;
  const pts2d = polyVerts.map((vp) => {
    const pv = toVec3(vp);
    const rx = pv[0] - foot[0], ry = pv[1] - foot[1], rz = pv[2] - foot[2];
    return [
      rx * uUnit[0] + ry * uUnit[1] + rz * uUnit[2],
      rx * wx + ry * wy + rz * wz,
    ] as [number, number];
  });
  for (let pi = 0; pi < pts2d.length; pi += 1) {
    const [ax2, ay2] = pts2d[pi]!;
    const [bx2, by2] = pts2d[(pi + 1) % pts2d.length]!;
    if ((ay2 <= 0 && by2 > 0) || (by2 <= 0 && ay2 > 0)) {
      const sEdge = -ay2 / (by2 - ay2);
      const hitT = ax2 + sEdge * (bx2 - ax2);
      if (hitT > 1e-4 && hitT < minHit) minHit = hitT;
    }
  }
  if (!Number.isFinite(minHit)) return defaultLen;
  return Math.min(defaultLen, Math.max(minLen, minHit * 0.78));
}

export function computeOptimalInPlaneWitnessBasis(
  planeNormal: Vec3,
  canonicalViewRay: Vec3 = [8, 3, 6],
): Vec3 {
  const nLen = Math.hypot(planeNormal[0], planeNormal[1], planeNormal[2]);
  if (nLen <= 1e-8) return [1, 0, 0];
  const nx = planeNormal[0] / nLen;
  const ny = planeNormal[1] / nLen;
  const nz = planeNormal[2] / nLen;

  const rLen = Math.hypot(canonicalViewRay[0], canonicalViewRay[1], canonicalViewRay[2]);
  const rx = rLen > 1e-8 ? canonicalViewRay[0] / rLen : 8 / Math.hypot(8, 3, 6);
  const ry = rLen > 1e-8 ? canonicalViewRay[1] / rLen : 3 / Math.hypot(8, 3, 6);
  const rz = rLen > 1e-8 ? canonicalViewRay[2] / rLen : 6 / Math.hypot(8, 3, 6);

  let wx = ry * nz - rz * ny;
  let wy = rz * nx - rx * nz;
  let wz = rx * ny - ry * nx;
  let wLen = Math.hypot(wx, wy, wz);

  if (wLen <= 1e-5) {
    for (const fb of [[3, -8, 0], [1, 0, 0], [0, 1, 0]] as Vec3[]) {
      const dotFN = fb[0] * nx + fb[1] * ny + fb[2] * nz;
      const px = fb[0] - dotFN * nx;
      const py = fb[1] - dotFN * ny;
      const pz = fb[2] - dotFN * nz;
      const pLen = Math.hypot(px, py, pz);
      if (pLen > 1e-6) {
        wx = px;
        wy = py;
        wz = pz;
        wLen = pLen;
        break;
      }
    }
  }
  if (wLen <= 1e-8) return [1, 0, 0];

  let ux = wx / wLen;
  let uy = wy / wLen;
  let uz = wz / wLen;

  const canonDot = ux * 3 - uy * 8 - uz * 2;
  const flipSign =
    canonDot < -1e-9
    || (Math.abs(canonDot) <= 1e-9
      && (Math.abs(ux) > 1e-9 ? ux < 0 : Math.abs(uy) > 1e-9 ? uy < 0 : uz < 0));
  if (flipSign) {
    ux = -ux;
    uy = -uy;
    uz = -uz;
  }
  return [ux, uy, uz];
}

export type StepVisualRole = "PRIMARY" | "CONTEXT" | "SUPPORT" | "INACTIVE";

export type StepTargetRelation =
  | "active_target"
  | "direct_prerequisite"
  | "spatial_carrier"
  | "explanatory_witness"
  | "completed_scaffold"
  | "inactive";

export type StepPresentationTier =
  | "ACTIVE_PRIMARY"
  | "ACTIVE_EVIDENCE"
  | "ORIENTATION_CONTEXT"
  | "COMPLETED_AUXILIARY";

export interface StepVisualRoleEntry {
  objectId: string;
  role: StepVisualRole;
  presentationTier: StepPresentationTier;
  visible: boolean;
  opacityScale: number;
  reason: string;
  semanticLayer?: SemanticConstructionLayer;
  semanticRole?: UnifiedSemanticObjectRole;
  birthStep?: number;
  prerequisites?: string[];
  relationToActiveTarget?: StepTargetRelation;
  visualPriority?: 1 | 2 | 3 | 4 | 5;
  keepCondition?: string;
  attenuateCondition?: string;
  hideCondition?: string;
  restorableOnBackwardScrub?: boolean;
  showPerpWitnessSymbol?: boolean;
  perpWitnessOpacityScale?: number;
  showParallelWitnessSymbol?: boolean;
  planeLifecycleStage?: PlaneSectionLifecycleStage;
  showObjectLabel?: boolean;
}

export interface StepVisualRoleOptions {
  auxiliaryShown?: boolean;
  selectedId?: string | null;
}

/**
 * Chính sách hiển thị theo mục tiêu từng bước cho `plane3` dựa trên vai trò ngữ nghĩa:
 * - `MANDATORY_STUDIED_PLANE`: mặt phẳng là đối tượng khảo sát chính (giao tuyến hai mặt phẳng, góc nhị diện, khoảng cách điểm–mặt) → luôn giữ hiển thị (`PRIMARY` khi vừa dựng, `CONTEXT` ở các bước suy ra sau đó).
 * - `SPATIAL_RELATION_PLANE`: mặt phẳng cắt mặt cầu → `PRIMARY` khi dựng mặt phẳng, sau đó lùi thành `SUPPORT` dịu khi đường tròn giao tuyến xuất hiện để đường tròn nổi bật rõ.
 * - `CONSTRUCTION_TOOL_PLANE`: mặt phẳng phụ cắt khối đa diện/trụ/nón → `PRIMARY` ở bước dựng mặt phẳng, chuyển sang `CONTEXT` khi tìm giao điểm trên cạnh, `SUPPORT` khi dựng các đoạn giao tuyến mặt, và tự ẩn mặc định khi đa giác thiết diện đã khép kín tô miền (khôi phục ngay khi bật `Hình phụ` hoặc chọn trực tiếp).
 * - `SOLID_FACE_DUPLICATE_PLANE`: mặt phẳng trùng mặt khối đã vẽ chỉ phục vụ đo đạc → ẩn mặc định trừ khi chọn trực tiếp hoặc bật `Hình phụ`.
 */
export function resolvePlaneSectionVisibility(
  scene: Scene3D,
  planeObj: SceneObject,
  step: number,
  auxiliaryShown = false,
  selectedId: string | null = null,
  startAnchor?: number,
): PlaneSectionVisibilityDecision {
  const directlySelected = selectedId !== null && selectedId === planeObj.id;
  const k = clampStep(scene, step);
  const effStart = startAnchor !== undefined ? Math.max(0, Math.min(k, Math.trunc(startAnchor))) : k;

  if (isDuplicateOfSolidFace(scene, planeObj)) {
    const visDup = directlySelected || auxiliaryShown;
    return {
      visible: visDup,
      subRole: "SOLID_FACE_DUPLICATE_PLANE",
      opacityScale: directlySelected ? 1 : 0.85,
      lifecycleStage: directlySelected ? "primary_focus" : "retired_scaffold",
      showPlaneLabel: visDup,
    };
  }

  const visAtStep = objectsAt(scene, k);
  const visStepIds = new Set(visAtStep.map((o) => o.id));

  // Mặt phẳng khung dựng trung gian (vd mặt phẳng trung trực phục vụ dựng tâm mặt cầu ngoại tiếp)
  // tự thu gọn sau khi hoàn tất bước dựng đối tượng đích, khôi phục khi bật `Hình phụ` hoặc chọn trực tiếp.
  if (!directlySelected) {
    const auxEntry = auxiliaryObjects(scene).get(planeObj.id);
    if (auxEntry?.loai === "dung" && k > auxEntry.xongTai) {
      return {
        visible: auxiliaryShown,
        subRole: "CONSTRUCTION_TOOL_PLANE",
        opacityScale: auxiliaryShown ? 0.48 : 0,
        lifecycleStage: "retired_scaffold",
        showPlaneLabel: auxiliaryShown,
      };
    }
  }

  // Nếu mặt phẳng phụ `CONSTRUCT_AUXILIARY_GEOMETRY` (vd `derived_Q_plane`) trùng khít với một mặt phẳng cắt tường minh
  // `CONSTRUCT_CUTTING_OBJECT` đang hiện tại bước `step`, nhường hiển thị cho mặt phẳng cắt chính để không vẽ chồng hai lần.
  if (
    (planeObj.formation_roles ?? []).includes("CONSTRUCT_AUXILIARY_GEOMETRY")
    && !(planeObj.formation_roles ?? []).includes("CONSTRUCT_CUTTING_OBJECT")
    && planeObj.normal
    && planeObj.point
  ) {
    const exactScene = exactSceneOriginOf(scene);
    const exactById = new Map(exactScene.objects.map((o) => [o.id, o]));
    const pSelf = exactById.get(planeObj.id) ?? planeObj;
    if (pSelf.normal && pSelf.point) {
      const nSelf = parseFracVec3(pSelf.normal);
      const ptSelf = parseFracVec3(pSelf.point);
      const hasCoplanarCuttingPlane = scene.objects.some((other) => {
        if (
          other.id === planeObj.id
          || other.type !== "plane3"
          || !visStepIds.has(other.id)
          || !(other.formation_roles ?? []).includes("CONSTRUCT_CUTTING_OBJECT")
        ) {
          return false;
        }
        const pOther = exactById.get(other.id) ?? other;
        if (!pOther.normal || !pOther.point) return false;
        const nOther = parseFracVec3(pOther.normal);
        const ptOther = parseFracVec3(pOther.point);
        return vIsZero(vCross(nSelf, nOther)) && fIsZero(plainDotFrac(vSub(ptSelf, ptOther), nOther));
      });
      if (hasCoplanarCuttingPlane) {
        return {
          visible: directlySelected,
          subRole: "SOLID_FACE_DUPLICATE_PLANE",
          opacityScale: 1,
          lifecycleStage: directlySelected ? "primary_focus" : "retired_scaffold",
          showPlaneLabel: directlySelected,
        };
      }
    }
  }

  const hl = computeStepHighlightTargets(scene, k, effStart);
  const isNewlyCreatedPlane = hl.newIds.has(planeObj.id);
  const progressById = new Map(
    (scene.formation?.steps[k]?.geometry_progress ?? []).map((gp) => [gp.object_id, gp]),
  );

  const cutResults = scene.objects.filter(
    (x) =>
      (x.type === "section"
        || x.type === "circle3"
        || x.type === "ellipse3"
        || (x.type === "polygon3" && vaiTroMien(x) === "section"))
      && (x.depends ?? []).includes(planeObj.id),
  );

  if (cutResults.length > 0) {
    const cutsSphere = cutResults.some((cut) =>
      (cut.depends ?? []).some((depId) => {
        const solid = scene.objects.find((s) => s.id === depId);
        return solid?.type === "curved_solid" && solid.curved_kind === "ball";
      }),
    );

    const presentCuts = cutResults.filter((c) => visStepIds.has(c.id));

    if (cutsSphere) {
      if (directlySelected || isNewlyCreatedPlane) {
        return {
          visible: true,
          subRole: "SPATIAL_RELATION_PLANE",
          opacityScale: 1,
          lifecycleStage: "primary_focus",
          showPlaneLabel: true,
        };
      }
      if (presentCuts.length === 0) {
        return {
          visible: true,
          subRole: "SPATIAL_RELATION_PLANE",
          opacityScale: 0.68,
          lifecycleStage: "active_carrier",
          showPlaneLabel: true,
        };
      }
      return {
        visible: true,
        subRole: "SPATIAL_RELATION_PLANE",
        opacityScale: 0.38,
        lifecycleStage: "attenuated_support",
        showPlaneLabel: true,
      };
    }

    if (directlySelected) {
      return {
        visible: true,
        subRole: "CONSTRUCTION_TOOL_PLANE",
        opacityScale: 1,
        lifecycleStage: "primary_focus",
        showPlaneLabel: true,
      };
    }

    // Khi đa giác thiết diện của khối đa diện đã khép kín và tô miền hoàn chỉnh:
    // - Nếu bước hiện tại là bước hợp nhất vừa dựng các đoạn giao tuyến mặt (`EXTEND`) vừa khép miền (`STEP`),
    //   giữ mặt phẳng cắt ở chế độ `SUPPORT` dịu (`0.28`) để học sinh nhìn rõ giao tuyến sinh ra từ đâu.
    // - Ở các bước sau khi thiết diện đã dựng xong (hoặc sự kiện `STEP` đơn lẻ), mặt phẳng cắt tự ẩn mặc định
    //   (`visible: auxiliaryShown`) để thiết diện nổi bật sạch sẽ, vẫn bật lại được qua `Hình phụ`.
    const hasCompletedPolySection = presentCuts.some((c) => {
      if (c.type !== "section" && c.type !== "polygon3") return false;
      const prog = progressById.get(c.id);
      const closedNow = prog ? prog.closed : c.closed !== false;
      const filledNow = prog ? prog.fill_visible : c.fill_visible !== false;
      return closedNow && filledNow;
    });

    const hasConsolidatedTraceInCurrentStep =
      effStart < k
      && presentCuts.some((c) => {
        if (c.type !== "section" && c.type !== "polygon3") return false;
        for (let idx = effStart; idx <= k; idx += 1) {
          const ev = scene.events[idx];
          if (ev && ev.action === "EXTEND" && ev.object === c.id) {
            return true;
          }
        }
        return false;
      });

    if (hasCompletedPolySection && !isNewlyCreatedPlane) {
      if (hasConsolidatedTraceInCurrentStep) {
        return {
          visible: true,
          subRole: "CONSTRUCTION_TOOL_PLANE",
          opacityScale: auxiliaryShown ? 0.42 : 0.28,
          lifecycleStage: "consolidated_section_support",
          showPlaneLabel: auxiliaryShown,
        };
      }
      return {
        visible: auxiliaryShown,
        subRole: "CONSTRUCTION_TOOL_PLANE",
        opacityScale: auxiliaryShown ? 0.42 : 0,
        lifecycleStage: "retired_scaffold",
        showPlaneLabel: auxiliaryShown,
      };
    }

    if (presentCuts.length > 0 && !isNewlyCreatedPlane) {
      const hasCurvedCutOnly = presentCuts.every((c) => c.type === "circle3" || c.type === "ellipse3");
      return {
        visible: true,
        subRole: "CONSTRUCTION_TOOL_PLANE",
        opacityScale: hasCurvedCutOnly ? 0.42 : 0.35,
        lifecycleStage: "attenuated_support",
        showPlaneLabel: true,
      };
    }

    const hasDerivedObjectFromPlane = visAtStep.some(
      (x) => x.id !== planeObj.id && !isSubEntity(x.id) && (x.depends ?? []).includes(planeObj.id),
    );
    if (hasDerivedObjectFromPlane && !isNewlyCreatedPlane) {
      return {
        visible: true,
        subRole: "CONSTRUCTION_TOOL_PLANE",
        opacityScale: 0.62,
        lifecycleStage: "active_carrier",
        showPlaneLabel: true,
      };
    }

    return {
      visible: true,
      subRole: "CONSTRUCTION_TOOL_PLANE",
      opacityScale: 1,
      lifecycleStage: "primary_focus",
      showPlaneLabel: true,
    };
  }

  const coexistingStudiedPlanes = scene.objects.filter(
    (other) =>
      other.type === "plane3"
      && visStepIds.has(other.id)
      && !isDuplicateOfSolidFace(scene, other),
  );
  const studiedScale = directlySelected
    ? 1
    : isNewlyCreatedPlane
      ? (coexistingStudiedPlanes.length >= 2 ? 0.76 : 1)
      : (coexistingStudiedPlanes.length >= 2 ? 0.58 : 0.68);

  return {
    visible: true,
    subRole: "MANDATORY_STUDIED_PLANE",
    opacityScale: studiedScale,
    lifecycleStage: directlySelected || isNewlyCreatedPlane ? "primary_focus" : "active_carrier",
    showPlaneLabel: true,
  };
}

export type AuxiliaryPlanePedagogicalState =
  | "unborn"
  | "active_primary"
  | "used_for_intersection"
  | "context_only"
  | "retired_hidden";

export interface AuxiliaryPlaneStateDecision {
  state: AuxiliaryPlanePedagogicalState;
  visible: boolean;
  opacityScale: number;
  showPlaneLabel: boolean;
  geometryInvariant: true;
  reason: string;
}

/**
 * Chuẩn hóa vòng đời 5 trạng thái sư phạm của mặt phẳng phụ / mặt phẳng cắt (§6):
 * `unborn` -> `active_primary` -> `used_for_intersection` -> `context_only` -> `retired_hidden`.
 * Thay đổi trạng thái chỉ điều biến hiển thị (`visible`, `opacityScale`), tuyệt đối không đổi vị trí hay kích thước tấm phẳng.
 */
export function classifyAuxiliaryPlanePedagogicalState(
  scene: Scene3D,
  planeObj: SceneObject,
  step: number,
  auxiliaryShown = false,
  selectedId: string | null = null,
  startStep?: number,
): AuxiliaryPlaneStateDecision {
  const k = clampStep(scene, step);
  const presentIds = new Set(objectsAt(scene, k).map((o) => o.id));
  if (!presentIds.has(planeObj.id)) {
    return {
      state: "unborn",
      visible: false,
      opacityScale: 0,
      showPlaneLabel: false,
      geometryInvariant: true,
      reason: "not_yet_constructed",
    };
  }
  const dec = resolvePlaneSectionVisibility(scene, planeObj, k, auxiliaryShown, selectedId, startStep);
  if (!dec.visible) {
    return {
      state: "retired_hidden",
      visible: false,
      opacityScale: 0,
      showPlaneLabel: false,
      geometryInvariant: true,
      reason: dec.lifecycleStage,
    };
  }
  if (dec.lifecycleStage === "primary_focus") {
    return {
      state: "active_primary",
      visible: true,
      opacityScale: dec.opacityScale,
      showPlaneLabel: dec.showPlaneLabel,
      geometryInvariant: true,
      reason: dec.lifecycleStage,
    };
  }
  if (dec.lifecycleStage === "active_carrier" || dec.lifecycleStage === "consolidated_section_support") {
    return {
      state: "used_for_intersection",
      visible: true,
      opacityScale: dec.opacityScale,
      showPlaneLabel: dec.showPlaneLabel,
      geometryInvariant: true,
      reason: dec.lifecycleStage,
    };
  }
  return {
    state: "context_only",
    visible: true,
    opacityScale: dec.opacityScale,
    showPlaneLabel: dec.showPlaneLabel,
    geometryInvariant: true,
    reason: dec.lifecycleStage,
  };
}

/**
 * Xác định vai trò trực quan theo bước (`PRIMARY` | `CONTEXT` | `SUPPORT` | `INACTIVE`) cho toàn bộ đối tượng
 * trong `scene` tại mốc `step`, sử dụng thuần metadata hợp đồng đã có (`formation`, `events`, `depends`,
 * `surface_role`, `formation_roles`, `perpendicular_witness`).
 */
export function resolveStepVisualRoles(
  scene: Scene3D,
  step: number,
  options?: StepVisualRoleOptions,
): Map<string, StepVisualRoleEntry> {
  const k = clampStep(scene, step);
  const auxiliaryShown = options?.auxiliaryShown ?? false;
  const selectedId = options?.selectedId ?? null;
  const presentObjs = objectsAt(scene, k);
  const presentIds = new Set(presentObjs.map((o) => o.id));
  const ungrounded = ungroundedFreePointIdsAt(scene, k);
  const hiddenAux = auxiliaryHiddenAt(scene, k, auxiliaryShown, selectedId);

  const pedSteps = pedagogicalStepList(scene);
  let matchedPedStep: PedagogicalStepItem | undefined;
  for (const ps of pedSteps) {
    if (ps.anchor === k) {
      matchedPedStep = ps;
      break;
    }
    if (ps.anchor < k) matchedPedStep = ps;
  }
  const hl = computeStepHighlightTargets(
    scene,
    k,
    matchedPedStep && matchedPedStep.anchor === k ? matchedPedStep.startAnchor : undefined,
  );

  const hasSectionOrCircleNew = [...hl.newIds].some((id) => {
    const obj = scene.objects.find((x) => x.id === id);
    return Boolean(
      obj
      && (obj.type === "section"
        || obj.type === "circle3"
        || obj.type === "ellipse3"
        || (obj.type === "polygon3" && vaiTroMien(obj) === "section")),
    );
  });

  const isSphereTriangleSupportId = (id: string): boolean => {
    const cand = scene.objects.find((x) => x.id === id);
    if (!cand) return false;
    const groups = cand.display_group ?? [];
    if (groups.includes("sphere_plane_aux") || groups.includes("sphere_plane_dist")) return true;
    return (
      cand.source?.instruction === "EXPLANATORY_DERIVED_WITNESS"
      && cand.semantic_role === "AUXILIARY_CONSTRUCTION"
      && (cand.type === "segment3" || cand.type === "point3")
    );
  };

  const hasAuthoritativeNewTarget = [...hl.newIds].some((id) => {
    const obj = scene.objects.find((x) => x.id === id);
    return Boolean(
      obj
      && !(obj.authoritative === false && obj.semantic_role === "AUXILIARY_CONSTRUCTION")
      && !(obj.display_group ?? []).includes("sphere_foundation_ref"),
    );
  });

  const primaryFocalIds = new Set<string>();
  for (const id of hl.newIds) {
    if (hasSectionOrCircleNew && isSphereTriangleSupportId(id)) continue;
    const cand = scene.objects.find((x) => x.id === id);
    if (
      hasAuthoritativeNewTarget
      && cand?.authoritative === false
      && cand.semantic_role === "AUXILIARY_CONSTRUCTION"
      && !(cand.display_group ?? []).includes("sphere_foundation_ref")
    ) {
      continue;
    }
    primaryFocalIds.add(id);
  }

  const hasSectionPrimary = [...primaryFocalIds].some((id) => {
    const obj = scene.objects.find((x) => x.id === id);
    return Boolean(
      obj
      && (obj.type === "section" || (obj.type === "polygon3" && vaiTroMien(obj) === "section")),
    );
  });
  const hasCommonPerpPrimary = [...primaryFocalIds].some((id) => {
    const obj = scene.objects.find((x) => x.id === id);
    const w = obj?.perpendicular_witness ?? obj?.annotation?.witness;
    return w?.relation === "common_perpendicular";
  });

  const exactOrigin = exactSceneOriginOf(scene);
  const contract = getSemanticConstructionContract(scene);
  const byId = new Map(scene.objects.map((x) => [x.id, x]));
  const exactById = new Map(exactOrigin.objects.map((x) => [x.id, x]));

  const birthStepById = new Map<string, number>();
  for (const fid of scene.free_objects) {
    if (byId.has(fid)) birthStepById.set(fid, 0);
  }
  for (const ev of scene.events) {
    const evIds = [
      ...(ev.object ? [ev.object] : []),
      ...(Array.isArray(ev.objects) ? ev.objects : []),
    ];
    for (const eid of evIds) {
      if (!birthStepById.has(eid) && byId.has(eid)) {
        birthStepById.set(eid, ev.step_index);
      }
    }
  }

  const visibleGeomObjs = presentObjs.filter(
    (x) =>
      !ungrounded.has(x.id)
      && !hiddenAux.has(x.id)
      && x.type !== "quantity"
      && x.render !== "readout"
      && x.render !== "non_visual",
  );

  // Collect real visible 3D segment spans (excluding synthetic witness rays) for anchor-edge verification
  const realVisibleEdges: { ownerId: string; a: Vec3; b: Vec3 }[] = [];
  for (const x of visibleGeomObjs) {
    if (isSubEntity(x.id)) continue;
    if (x.type === "segment3" || x.type === "line3") {
      const pa = x.point_a ?? x.endpoints?.[0] ?? (x.endpoint_ids?.[0] ? byId.get(x.endpoint_ids[0])?.xyz : undefined);
      const pb = x.point_b ?? x.endpoints?.[1] ?? (x.endpoint_ids?.[1] ? byId.get(x.endpoint_ids[1])?.xyz : undefined);
      if (pa && pb) {
        realVisibleEdges.push({ ownerId: x.id, a: toVec3(pa), b: toVec3(pb) });
      }
    } else if (x.type === "polygon3" || x.type === "section") {
      const polyPts = x.polygon ?? x.vertices ?? [];
      for (let i = 0; i < polyPts.length; i += 1) {
        realVisibleEdges.push({
          ownerId: x.id,
          a: toVec3(polyPts[i]!),
          b: toVec3(polyPts[(i + 1) % polyPts.length]!),
        });
      }
    } else if (x.type === "solid" && x.vertices?.length && x.faces?.length) {
      for (const face of x.faces) {
        for (let i = 0; i < face.length; i += 1) {
          const va = x.vertices[face[i]!];
          const vb = x.vertices[face[(i + 1) % face.length]!];
          if (va && vb) {
            realVisibleEdges.push({ ownerId: x.id, a: toVec3(va), b: toVec3(vb) });
          }
        }
      }
    }
  }

  const hasHostSolidInScene = scene.objects.some(
    (x) => x.type === "solid" || (x.type === "curved_solid" && x.curved_kind !== "ball"),
  );
  const foundationPointIds = new Set<string>();
  if (hasHostSolidInScene) {
    for (const x of exactOrigin.objects) {
      if (x.type === "solid") {
        for (const vid of x.vertex_ids ?? x.depends ?? []) foundationPointIds.add(vid);
      } else if (x.type === "curved_solid" && x.curved_kind !== "ball") {
        for (const vid of x.depends ?? []) {
          if (exactById.get(vid)?.type === "point3") foundationPointIds.add(vid);
        }
        const candidates = [
          x.anchor,
          x.apex_or_top ?? (x as SceneObject & { apex?: ExactVec3 | null }).apex ?? undefined,
          x.rim_point,
        ].filter((v): v is ExactVec3 => Boolean(v));
        for (const ptObj of exactOrigin.objects) {
          if (ptObj.type !== "point3" || !ptObj.xyz) continue;
          const pv = parseFracVec3(ptObj.xyz);
          if (candidates.some((cv) => vIsZero(vSub(pv, parseFracVec3(cv))))) {
            foundationPointIds.add(ptObj.id);
          }
        }
      } else if (
        (x.type === "segment3" || x.type === "line3")
        && ((x.formation_roles ?? []).includes("CONSTRUCT_HEIGHT") || classifyCurvedSegmentRole(exactOrigin, x)?.kind === "axis")
      ) {
        for (const eid of x.endpoint_ids ?? x.depends ?? []) {
          if (exactById.get(eid)?.type === "point3") foundationPointIds.add(eid);
        }
        if (x.perpendicular_witness?.foot_id) foundationPointIds.add(x.perpendicular_witness.foot_id);
        if (x.perpendicular_witness?.from) foundationPointIds.add(x.perpendicular_witness.from);
      }
    }
  }

  const auxSet = auxiliaryObjects(scene);
  const isHostFoundationObj = (x: SceneObject): boolean => {
    const ex = exactById.get(x.id) ?? x;
    if (x.type === "solid" || (x.type === "curved_solid" && x.curved_kind !== "ball")) return true;
    if (x.type === "point3") return foundationPointIds.has(x.id);
    if (x.type === "polygon3") {
      return (
        x.surface_role === "BASE_REGION"
        || (x.formation_roles ?? []).includes("CONSTRUCT_BASE")
        || (x.formation_roles ?? []).includes("CONSTRUCT_TRANSLATED_FACE")
        || (x.display_group ?? []).includes("face")
      );
    }
    if (x.type === "circle3") return x.surface_role === "BASE_REGION";
    if (x.type === "segment3" || x.type === "line3") {
      const roles = x.formation_roles ?? [];
      if (
        roles.includes("CONSTRUCT_HEIGHT")
        || roles.includes("CONSTRUCT_LATERAL_BOUNDARY")
        || Boolean(classifyCurvedSegmentRole(exactOrigin, ex))
      ) {
        return true;
      }
      if (auxSet.get(x.id)?.loai === "dung") {
        const epIds = x.endpoint_ids ?? x.depends ?? [];
        if (epIds.length > 0 && epIds.every((id) => foundationPointIds.has(id))) {
          return true;
        }
      }
      return false;
    }
    return false;
  };

  const hasPostFoundationTargetAtStep =
    hasHostSolidInScene
    && visibleGeomObjs.some((x) => !isSubEntity(x.id) && !isHostFoundationObj(x));

  const ballsInScene = scene.objects.filter(
    (x) => x.type === "curved_solid" && x.curved_kind === "ball",
  );
  const secantBallIdsAtStep = new Set<string>();
  const witnessedBallIdsAtStep = new Set<string>();
  for (const ball of ballsInScene) {
    const exBall = exactById.get(ball.id) ?? ball;
    const ballAnchor = exBall.anchor ? parseFracVec3(exBall.anchor) : null;
    for (const x of presentObjs) {
      if (isSubEntity(x.id)) continue;
      const groups = x.display_group ?? [];
      if (
        x.type === "circle3"
        && x.surface_role !== "BASE_REGION"
        && ((x.depends ?? []).includes(ball.id) || ballsInScene.length === 1)
      ) {
        secantBallIdsAtStep.add(ball.id);
      } else if (
        groups.includes("sphere_plane_aux")
        && !groups.includes("sphere_plane_dist")
        && ((x.depends ?? []).includes(ball.id) || ballsInScene.length === 1)
      ) {
        secantBallIdsAtStep.add(ball.id);
      }
      const pw = x.perpendicular_witness ?? x.annotation?.witness;
      if (
        (x.type === "segment3" || x.type === "line3")
        && pw?.on
        && (
          groups.includes("sphere_plane_dist")
          || (pw.from && ballAnchor && (() => {
            const fromPt = exactById.get(pw.from) ?? byId.get(pw.from);
            return Boolean(fromPt?.xyz && vIsZero(vSub(parseFracVec3(fromPt.xyz), ballAnchor)));
          })())
        )
      ) {
        witnessedBallIdsAtStep.add(ball.id);
      }
    }
  }

  const enrichEntry = (
    o: SceneObject,
    base: Pick<StepVisualRoleEntry, "objectId" | "role" | "visible" | "opacityScale" | "reason">
      & Partial<Pick<StepVisualRoleEntry, "presentationTier" | "planeLifecycleStage" | "showObjectLabel">>,
  ): StepVisualRoleEntry => {
    const spec = contract.objectsById.get(o.id);
    const semanticLayer = spec?.objectLayer ?? (o.type === "quantity" ? "INTERNAL_MATH_RESULT" : "CONSTRUCTION_GEOMETRY");
    const semanticRole = spec?.semanticRole;
    const birthStep = birthStepById.get(o.id) ?? (o.origin === "free" ? 0 : k);
    const prerequisites = spec?.prerequisiteIds ?? [...(o.depends ?? [])];
    const exO = exactById.get(o.id) ?? o;
    const cRole = (o.type === "segment3" || o.type === "line3")
      ? classifyCurvedSegmentRole(exactOrigin, exO)
      : null;
    const isFoundationAltitudeOrAxis =
      hasHostSolidInScene
      && (o.type === "segment3" || o.type === "line3")
      && ((o.formation_roles ?? []).includes("CONSTRUCT_HEIGHT") || cRole?.kind === "axis");

    let relationToActiveTarget: StepTargetRelation = "inactive";
    if (!base.visible || base.role === "INACTIVE") {
      relationToActiveTarget = base.reason === "retired_auxiliary" ? "completed_scaffold" : "inactive";
    } else if (base.role === "PRIMARY") {
      relationToActiveTarget = "active_target";
    } else if (hl.depIds.has(o.id)) {
      relationToActiveTarget = "direct_prerequisite";
    } else if (base.role === "SUPPORT") {
      relationToActiveTarget =
        semanticLayer === "RELATION_WITNESS" || base.reason === "sphere_section_explanatory_support"
          ? "explanatory_witness"
          : "completed_scaffold";
    } else {
      relationToActiveTarget = "spatial_carrier";
    }

    const visualPriority: 1 | 2 | 3 | 4 | 5 =
      !base.visible || base.role === "INACTIVE"
        ? 5
        : base.role === "PRIMARY"
          ? (semanticLayer === "RESULT_SECTION" ? 1 : 2)
          : base.role === "CONTEXT"
            ? 3
            : 4;

    const segEndA = o.point_a ?? o.endpoints?.[0];
    const segEndB = o.point_b ?? o.endpoints?.[1];
    const hasValidSegmentPerpMarker = Boolean(
      o.type === "segment3"
        && segEndA
        && segEndB
        && o.perpendicular_witness?.foot
        && o.perpendicular_witness?.marker
        && nhanChungDoanHopLe(
          o.perpendicular_witness as { foot: ExactVec3; marker: { u: ExactVec3; v: ExactVec3 }; plane_directions?: ExactVec3[] },
          toVec3(segEndA),
          toVec3(segEndB),
        ),
    );
    const hasOwnPerpWitness =
      o.type === "point3"
        ? false
        : o.type === "plane3"
          ? Boolean(
              spec?.verifiedRelations.some((r) => r.kind === "line_perp_plane" && r.canDisplaySymbol)
                && resolvePlanePerpendicularLineWitness(scene, o, presentObjs) !== null,
            )
          : Boolean(
              hasValidSegmentPerpMarker
                && (spec === undefined
                  || spec.verifiedRelations.some(
                    (r) =>
                      (r.kind === "line_perp_plane" || r.kind === "line_perp_line" || r.kind === "common_perpendicular")
                      && r.canDisplaySymbol,
                  )),
            );
    let showPerpWitnessSymbol = base.visible && hasOwnPerpWitness;
    let perpWitnessOpacityScale = showPerpWitnessSymbol ? 1 : 0;
    const isFoundationPerpRelevantToPrimary = (altObj: SceneObject): boolean => {
      if (hl.depIds.has(altObj.id)) return true;
      const pw = altObj.perpendicular_witness ?? altObj.annotation?.witness;
      const cR = (altObj.type === "segment3" || altObj.type === "line3")
        ? classifyCurvedSegmentRole(exactOrigin, exactById.get(altObj.id) ?? altObj)
        : null;
      const hostScObj = cR?.host ? byId.get(cR.host.id) : undefined;
      const paRaw =
        altObj.point_a
        ?? altObj.endpoints?.[0]
        ?? (altObj.endpoint_ids?.[0] ? byId.get(altObj.endpoint_ids[0])?.xyz : undefined)
        ?? hostScObj?.anchor;
      const pbRaw =
        altObj.point_b
        ?? altObj.endpoints?.[1]
        ?? (altObj.endpoint_ids?.[1] ? byId.get(altObj.endpoint_ids[1])?.xyz : undefined)
        ?? (hostScObj?.apex_or_top ?? (hostScObj as (SceneObject & { apex?: ExactVec3 | null }) | undefined)?.apex ?? undefined);
      const aV = paRaw ? toVec3(paRaw) : null;
      const bV = pbRaw ? toVec3(pbRaw) : null;
      const altEndpointIds = new Set<string>([
        ...(altObj.endpoint_ids ?? []),
        ...(altObj.depends ?? []).filter((d) => byId.get(d)?.type === "point3"),
        ...(pw?.from ? [pw.from] : []),
        ...(pw?.foot_id ? [pw.foot_id] : []),
      ]);
      for (const pid of primaryFocalIds) {
        const pObj = byId.get(pid);
        if (!pObj) continue;
        if (pObj.type === "plane3" && pObj.point && pObj.normal && aV && bV) {
          const p0 = toVec3(pObj.point);
          const nRaw = toVec3(pObj.normal);
          const nLen = Math.hypot(nRaw[0], nRaw[1], nRaw[2]);
          if (nLen > 1e-9) {
            const da = Math.abs((aV[0] - p0[0]) * nRaw[0] + (aV[1] - p0[1]) * nRaw[1] + (aV[2] - p0[2]) * nRaw[2]) / nLen;
            const db = Math.abs((bV[0] - p0[0]) * nRaw[0] + (bV[1] - p0[1]) * nRaw[1] + (bV[2] - p0[2]) * nRaw[2]) / nLen;
            if (da <= 1e-3 && db <= 1e-3) return true;
          }
        }
        if ((pObj.type === "polygon3" || pObj.type === "section") && aV && bV) {
          const polyPts = (pObj.polygon ?? pObj.vertices ?? []).map(toVec3);
          const nPoly = polyPts.length >= 3 ? normalFromPoints(polyPts) : null;
          if (nPoly) {
            const p0 = polyPts[0];
            const da = Math.abs((aV[0] - p0[0]) * nPoly[0] + (aV[1] - p0[1]) * nPoly[1] + (aV[2] - p0[2]) * nPoly[2]);
            const db = Math.abs((bV[0] - p0[0]) * nPoly[0] + (bV[1] - p0[1]) * nPoly[1] + (bV[2] - p0[2]) * nPoly[2]);
            if (da <= 1e-3 && db <= 1e-3) return true;
          }
        }
        const prodHint = String(pObj.producer ?? "");
        const isPerpOrProjTarget =
          Boolean(pObj.perpendicular_witness)
          || /perpendicular|project|foot/iu.test(prodHint)
          || (pObj.display_group ?? []).includes("perp_witness");
        if (isPerpOrProjTarget) {
          const pRefs = [
            pObj.id,
            ...(pObj.endpoint_ids ?? []),
            ...(pObj.depends ?? []),
            ...(pObj.perpendicular_witness?.from ? [pObj.perpendicular_witness.from] : []),
            ...(pObj.perpendicular_witness?.foot_id ? [pObj.perpendicular_witness.foot_id] : []),
          ];
          if (pRefs.some((rId) => altEndpointIds.has(rId))) return true;
        }
      }
      return false;
    };
    if (showPerpWitnessSymbol && !auxiliaryShown && selectedId !== o.id && base.role !== "PRIMARY") {
      if (isFoundationAltitudeOrAxis && hasPostFoundationTargetAtStep) {
        showPerpWitnessSymbol = true;
        perpWitnessOpacityScale = isFoundationPerpRelevantToPrimary(o) ? 0.5 : 0.44;
      } else if (base.role === "SUPPORT") {
        perpWitnessOpacityScale = o.type === "plane3" ? 0.55 : 0.82;
      } else if (base.role === "CONTEXT") {
        perpWitnessOpacityScale = 0.9;
      }
    }

    const hasOwnParallelWitness = Boolean(
      isIntersectionLineOrSegment(o, scene)
        && spec?.verifiedRelations.some((r) => r.kind === "parallel" && r.canDisplaySymbol),
    );
    const showParallelWitnessSymbol =
      base.visible
      && hasOwnParallelWitness
      && (auxiliaryShown
        || selectedId === o.id
        || base.role === "PRIMARY"
        || relationToActiveTarget === "direct_prerequisite");

    const showObjectLabel =
      !base.visible
        ? false
        : o.type === "plane3"
          ? (base.showObjectLabel ?? true)
          : o.type === "point3"
            ? true
            : false;

    const keepCondition =
      base.role === "PRIMARY"
        ? "step_active_focus"
        : relationToActiveTarget === "direct_prerequisite"
          ? "active_target_prerequisite"
          : o.type === "plane3"
            ? base.reason
            : "persistent_spatial_structure";
    const attenuateCondition =
      base.opacityScale > 0 && base.opacityScale < 1
        ? base.reason
        : (hasOwnPerpWitness && base.visible && !showPerpWitnessSymbol
          ? "retire_unanchored_foundation_witness"
          : "none");
    const hideCondition =
      !base.visible
        ? base.reason
        : o.type === "plane3"
          ? "when_polyhedral_section_closed_after_trace"
          : auxSet.has(o.id)
            ? "after_dependent_target_constructed"
            : "manual_hide_only";

    const presentationTier: StepPresentationTier =
      base.presentationTier
      ?? (
        !base.visible || base.role === "INACTIVE"
          ? "COMPLETED_AUXILIARY"
          : base.role === "PRIMARY"
            ? "ACTIVE_PRIMARY"
            : hl.depIds.has(o.id) || base.role === "SUPPORT"
              ? "ACTIVE_EVIDENCE"
              : "ORIENTATION_CONTEXT"
      );

    return {
      ...base,
      presentationTier,
      semanticLayer,
      semanticRole,
      birthStep,
      prerequisites,
      relationToActiveTarget,
      visualPriority,
      keepCondition,
      attenuateCondition,
      hideCondition,
      restorableOnBackwardScrub: true,
      showPerpWitnessSymbol,
      perpWitnessOpacityScale,
      showParallelWitnessSymbol,
      showObjectLabel,
    };
  };

  const selectedConnectedAuxIds = new Set<string>();
  if (selectedId) {
    const addTransitiveRefs = (startId: string) => {
      const stack = [startId];
      while (stack.length > 0) {
        const cur = stack.pop()!;
        if (selectedConnectedAuxIds.has(cur)) continue;
        selectedConnectedAuxIds.add(cur);
        const curObj = byId.get(cur);
        if (!curObj) continue;
        for (const depId of [...(curObj.depends ?? []), ...(curObj.endpoint_ids ?? [])]) {
          if (!selectedConnectedAuxIds.has(depId)) stack.push(depId);
        }
      }
    };
    addTransitiveRefs(selectedId);
    const selObj = byId.get(selectedId);
    const isSelectedAuxOrRef = Boolean(
      selObj
      && (auxSet.has(selectedId)
        || (selObj.display_group ?? []).includes("sphere_foundation_ref")
        || selObj.authoritative === false
        || selObj.semantic_role === "AUXILIARY_CONSTRUCTION"),
    );
    if (isSelectedAuxOrRef) {
      for (const cand of scene.objects) {
        const isCandAuxOrRef =
          auxSet.has(cand.id)
          || (cand.display_group ?? []).includes("sphere_foundation_ref")
          || cand.authoritative === false
          || cand.semantic_role === "AUXILIARY_CONSTRUCTION";
        if (!isCandAuxOrRef) continue;
        const refs = [...(cand.depends ?? []), ...(cand.endpoint_ids ?? [])];
        if (refs.includes(selectedId)) {
          addTransitiveRefs(cand.id);
        }
      }
    }
  }

  const result = new Map<string, StepVisualRoleEntry>();

  for (const o of scene.objects) {
    if (
      !presentIds.has(o.id)
      || ungrounded.has(o.id)
      || o.type === "quantity"
      || o.render === "readout"
      || o.render === "non_visual"
    ) {
      result.set(
        o.id,
        enrichEntry(o, {
          objectId: o.id,
          role: "INACTIVE",
          presentationTier: "COMPLETED_AUXILIARY",
          visible: false,
          opacityScale: 0,
          reason: "future_or_non_visual",
        }),
      );
      continue;
    }

    if (o.type === "plane3") {
      const pVis = resolvePlaneSectionVisibility(
        scene,
        o,
        k,
        auxiliaryShown,
        selectedId,
        matchedPedStep?.startAnchor,
      );
      if (pVis.subRole === "SOLID_FACE_DUPLICATE_PLANE") {
        result.set(
          o.id,
          enrichEntry(o, {
            objectId: o.id,
            role: pVis.visible ? "SUPPORT" : "INACTIVE",
            visible: pVis.visible,
            opacityScale: pVis.visible ? pVis.opacityScale : 0,
            reason: "duplicate_solid_face_plane",
            planeLifecycleStage: pVis.lifecycleStage,
            showObjectLabel: pVis.showPlaneLabel,
          }),
        );
        continue;
      }
      if (primaryFocalIds.has(o.id)) {
        result.set(
          o.id,
          enrichEntry(o, {
            objectId: o.id,
            role: "PRIMARY",
            visible: pVis.visible,
            opacityScale: pVis.opacityScale,
            reason: "active_plane_target",
            planeLifecycleStage: pVis.lifecycleStage,
            showObjectLabel: pVis.showPlaneLabel,
          }),
        );
        continue;
      }
      if (pVis.subRole === "MANDATORY_STUDIED_PLANE") {
        result.set(
          o.id,
          enrichEntry(o, {
            objectId: o.id,
            role: "CONTEXT",
            visible: pVis.visible,
            opacityScale: pVis.opacityScale,
            reason: "studied_plane_context",
            planeLifecycleStage: pVis.lifecycleStage,
            showObjectLabel: pVis.showPlaneLabel,
          }),
        );
        continue;
      }
      const isContextCutPlane =
        pVis.visible
        && (pVis.lifecycleStage === "primary_focus" || pVis.lifecycleStage === "active_carrier");
      result.set(
        o.id,
        enrichEntry(o, {
          objectId: o.id,
          role: isContextCutPlane ? "CONTEXT" : "SUPPORT",
          visible: pVis.visible,
          opacityScale: pVis.visible ? pVis.opacityScale : 0,
          reason: isContextCutPlane ? "cutting_plane_context" : "cutting_plane_support",
          planeLifecycleStage: pVis.lifecycleStage,
          showObjectLabel: pVis.showPlaneLabel,
        }),
      );
      continue;
    }

    if ((o.display_group ?? []).includes("sphere_foundation_ref")) {
      const ownerBall =
        ballsInScene.find((b) => o.id.startsWith(`${b.id}__`))
        ?? ballsInScene[0];
      const isFirstSphereStep =
        primaryFocalIds.has(o.id)
        || (ownerBall !== undefined && primaryFocalIds.has(ownerBall.id))
        || (matchedPedStep !== undefined && pedSteps[0] === matchedPedStep);
      if (isFirstSphereStep) {
        result.set(
          o.id,
          enrichEntry(o, {
            objectId: o.id,
            role: o.type === "point3" ? "SUPPORT" : "PRIMARY",
            presentationTier: "ACTIVE_PRIMARY",
            visible: true,
            opacityScale: o.type === "point3" ? 0.86 : 0.94,
            reason: "sphere_foundation_reference_active",
          }),
        );
        continue;
      }
      if (ownerBall && secantBallIdsAtStep.has(ownerBall.id)) {
        const revealCompletedRef = auxiliaryShown || selectedConnectedAuxIds.has(o.id);
        result.set(
          o.id,
          enrichEntry(o, {
            objectId: o.id,
            role: "SUPPORT",
            presentationTier: "COMPLETED_AUXILIARY",
            visible: revealCompletedRef,
            opacityScale: revealCompletedRef ? 0.42 : 0,
            reason: "completed_sphere_foundation_reference",
          }),
        );
        continue;
      }
      if (ownerBall && witnessedBallIdsAtStep.has(ownerBall.id)) {
        result.set(
          o.id,
          enrichEntry(o, {
            objectId: o.id,
            role: "SUPPORT",
            presentationTier: "ACTIVE_EVIDENCE",
            visible: true,
            opacityScale: auxiliaryShown ? 0.64 : 0.52,
            reason: "sphere_foundation_reference_evidence",
          }),
        );
        continue;
      }
      result.set(
        o.id,
        enrichEntry(o, {
          objectId: o.id,
          role: "CONTEXT",
          presentationTier: "ORIENTATION_CONTEXT",
          visible: true,
          opacityScale: auxiliaryShown ? 0.58 : 0.38,
          reason: "sphere_foundation_reference_context",
        }),
      );
      continue;
    }

    const auxMeta = auxSet.get(o.id);
    if (
      auxMeta?.loai === "dung"
      && auxMeta.xongTai >= 0
      && (k > auxMeta.xongTai || (!primaryFocalIds.has(o.id) && o.authoritative === false))
    ) {
      const hasHiddenPlaneHelperEndpoint =
        (o.type === "segment3" || o.type === "line3")
        && (o.endpoint_ids ?? o.depends ?? []).some((epId) => {
          const epObj = byId.get(epId);
          return Boolean(epObj?.type === "point3" && laDiemPhuDungMatPhang(scene, epObj, byId));
        });
      if ((o.type === "segment3" || o.type === "line3") && !hasHiddenPlaneHelperEndpoint) {
        const keepAsFoundationEvidence =
          k <= auxMeta.xongTai || !hasPostFoundationTargetAtStep || hl.depIds.has(o.id);
        if (keepAsFoundationEvidence) {
          result.set(
            o.id,
            enrichEntry(o, {
              objectId: o.id,
              role: "SUPPORT",
              presentationTier: "ACTIVE_EVIDENCE",
              visible: true,
              opacityScale: 0.42,
              reason: "foundation_auxiliary_evidence",
            }),
          );
          continue;
        }
        // Các đường thẳng kéo dài đồng phẳng (`line3`, ví dụ MN cắt BC tại điểm E nằm ngoài đáy khối chóp)
        // là giá mang định hướng bắt buộc của giao điểm ngoài khối nên giữ ở tầng ORIENTATION_CONTEXT độ mờ thấp;
        // còn các đoạn dựng phụ nội bộ (`segment3`, ví dụ đường chéo EG, FH xác định tâm O) chuyển sang COMPLETED_AUXILIARY.
        if (o.type === "line3") {
          result.set(
            o.id,
            enrichEntry(o, {
              objectId: o.id,
              role: "SUPPORT",
              presentationTier: "ORIENTATION_CONTEXT",
              visible: true,
              opacityScale: 0.4,
              reason: "coplanar_extension_orientation_context",
            }),
          );
          continue;
        }
        const revealCompletedAux = auxiliaryShown || selectedConnectedAuxIds.has(o.id);
        result.set(
          o.id,
          enrichEntry(o, {
            objectId: o.id,
            role: "SUPPORT",
            presentationTier: "COMPLETED_AUXILIARY",
            visible: revealCompletedAux,
            opacityScale: revealCompletedAux ? 0.38 : 0,
            reason: "completed_auxiliary_scaffold",
          }),
        );
        continue;
      }
      if (hiddenAux.has(o.id)) {
        result.set(
          o.id,
          enrichEntry(o, {
            objectId: o.id,
            role: "SUPPORT",
            presentationTier: "COMPLETED_AUXILIARY",
            visible: false,
            opacityScale: 0,
            reason: "retired_auxiliary",
          }),
        );
        continue;
      }
    }

    if (hiddenAux.has(o.id)) {
      result.set(
        o.id,
        enrichEntry(o, {
          objectId: o.id,
          role: "SUPPORT",
          presentationTier: "COMPLETED_AUXILIARY",
          visible: false,
          opacityScale: 0,
          reason: "retired_auxiliary",
        }),
      );
      continue;
    }

    if (primaryFocalIds.has(o.id)) {
      result.set(
        o.id,
        enrichEntry(o, {
          objectId: o.id,
          role: "PRIMARY",
          visible: true,
          opacityScale: 1,
          reason: "step_primary_target",
        }),
      );
      continue;
    }

    if (isSphereTriangleSupportId(o.id)) {
      result.set(
        o.id,
        enrichEntry(o, {
          objectId: o.id,
          role: "SUPPORT",
          visible: true,
          opacityScale: 0.76,
          reason: "sphere_section_explanatory_support",
        }),
      );
      continue;
    }

    const curvedRole = (o.type === "segment3" || o.type === "line3")
      ? classifyCurvedSegmentRole(scene, o)
      : null;
    const isAuxiliarySupport =
      !curvedRole
      && (
        isAuxiliaryExplanatoryPolygon(scene, o)
        || auxSet.has(o.id)
        || (o.authoritative === false && o.semantic_role === "AUXILIARY_CONSTRUCTION")
      );
    if (isAuxiliarySupport) {
      result.set(
        o.id,
        enrichEntry(o, {
          objectId: o.id,
          role: "SUPPORT",
          visible: true,
          opacityScale: 0.56,
          reason: "auxiliary_scaffolding_support",
        }),
      );
      continue;
    }

    if (o.type === "solid" && hasSectionPrimary) {
      result.set(
        o.id,
        enrichEntry(o, {
          objectId: o.id,
          role: "CONTEXT",
          visible: true,
          opacityScale: 0.85,
          reason: "host_solid_section_context",
        }),
      );
      continue;
    }

    if (hasCommonPerpPrimary && (o.type === "line3" || o.type === "segment3") && isPrimarySpatialLine(o)) {
      result.set(
        o.id,
        enrichEntry(o, {
          objectId: o.id,
          role: "CONTEXT",
          visible: true,
          opacityScale: 0.82,
          reason: "skew_line_context",
        }),
      );
      continue;
    }

    result.set(
      o.id,
      enrichEntry(o, {
        objectId: o.id,
        role: "CONTEXT",
        visible: true,
        opacityScale: 1,
        reason: "spatial_context",
      }),
    );
  }

  return result;
}

function clipConvexPolygonAboveZ(poly: Vec3[], zMin: number): Vec3[] {
  if (poly.length < 3 || !Number.isFinite(zMin)) return poly;
  const eps = 1e-5;
  if (poly.every((p) => p[2] >= zMin - eps)) return poly;
  const out: Vec3[] = [];
  for (let i = 0; i < poly.length; i += 1) {
    const a = poly[i];
    const b = poly[(i + 1) % poly.length];
    const da = a[2] - zMin;
    const db = b[2] - zMin;
    const aIn = da >= -eps;
    const bIn = db >= -eps;
    if (aIn && bIn) {
      out.push(b);
    } else if (aIn && !bIn) {
      const t = da / (da - db);
      out.push([a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]), zMin]);
    } else if (!aIn && bIn) {
      const t = da / (da - db);
      out.push([a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]), zMin]);
      out.push(b);
    }
  }
  return out.length >= 3 ? out : poly;
}

function intersectSegmentWithPlane(a: Vec3, b: Vec3, p0: Vec3, u: Vec3, eps = 1e-6): Vec3[] {
  const ha = (a[0] - p0[0]) * u[0] + (a[1] - p0[1]) * u[1] + (a[2] - p0[2]) * u[2];
  const hb = (b[0] - p0[0]) * u[0] + (b[1] - p0[1]) * u[1] + (b[2] - p0[2]) * u[2];
  if (Math.abs(ha) <= eps && Math.abs(hb) <= eps) {
    return [
      [a[0] - ha * u[0], a[1] - ha * u[1], a[2] - ha * u[2]],
      [b[0] - hb * u[0], b[1] - hb * u[1], b[2] - hb * u[2]],
    ];
  }
  if (Math.abs(ha) <= eps) {
    return [[a[0] - ha * u[0], a[1] - ha * u[1], a[2] - ha * u[2]]];
  }
  if (Math.abs(hb) <= eps) {
    return [[b[0] - hb * u[0], b[1] - hb * u[1], b[2] - hb * u[2]]];
  }
  if ((ha > 0 && hb < 0) || (ha < 0 && hb > 0)) {
    const t = ha / (ha - hb);
    return [[
      a[0] + t * (b[0] - a[0]),
      a[1] + t * (b[1] - a[1]),
      a[2] + t * (b[2] - a[2]),
    ]];
  }
  return [];
}

/**
 * Tìm các điểm xuyên thực tế của mặt phẳng `(point, normal)` qua các cạnh của khối đa diện đang hiện.
 * Chỉ dùng cho kích thước tấm mặt phẳng minh họa hữu hạn (`plane3` presentation patch) để mặt phẳng luôn xuyên hết khối
 * ở cả bước trung gian lẫn bước cuối; tuyệt đối KHÔNG dùng để tính hay sửa thiết diện.
 */
export function planeSolidEdgeIntersections(
  planeObj: SceneObject,
  visibleObjects: readonly SceneObject[],
): Vec3[] {
  if (planeObj.type !== "plane3" || !planeObj.point || !planeObj.normal) return [];
  const p0 = toVec3(planeObj.point);
  const nRaw = toVec3(planeObj.normal);
  const dn = Math.hypot(...nRaw);
  if (!(dn > 1e-9)) return [];
  const u: Vec3 = [nRaw[0] / dn, nRaw[1] / dn, nRaw[2] / dn];

  const out: Vec3[] = [];
  const pushUnique = (pt: Vec3) => {
    if (!out.some((q) => Math.hypot(q[0] - pt[0], q[1] - pt[1], q[2] - pt[2]) <= 1e-5)) {
      out.push(pt);
    }
  };

  for (const obj of visibleObjects) {
    if (obj.type !== "solid" || !obj.vertices || !obj.faces) continue;
    const verts = obj.vertices.map(toVec3);
    const seenEdges = new Set<string>();
    for (const f of obj.faces) {
      for (let i = 0; i < f.length; i += 1) {
        const ia = f[i];
        const ib = f[(i + 1) % f.length];
        if (!verts[ia] || !verts[ib]) continue;
        const key = ia < ib ? `${ia}-${ib}` : `${ib}-${ia}`;
        if (seenEdges.has(key)) continue;
        seenEdges.add(key);
        for (const p of intersectSegmentWithPlane(verts[ia], verts[ib], p0, u)) {
          pushUnique(p);
        }
      }
    }
  }
  return out;
}

/**
 * Tạo tập điểm neo đồng phẳng gọn cho các trường hợp mà tấm mặt phẳng minh họa cần ôm vừa vặn và xuyên qua toàn bộ khối:
 * 1. Mặt phẳng cắt khối cong (`ball` / `cylinder` / `cone`, kể cả bước trung gian trước khi dựng xong `circle3` / `ellipse3`):
 *    tính từ bounds hình học của khối cong + giao tuyến thực tế để tấm phẳng luôn vượt ra ngoài biên khối ở mọi phía.
 * 2. Mặt phẳng nghiên cứu xác định qua < 3 đỉnh khối tường minh (vd qua B vuông góc SC):
 *    kết hợp các điểm xuyên cạnh khối thực tế + chân vuông góc được chứng nhận để mặt phẳng luôn phủ qua vùng giao cắt.
 * Trả mảng rỗng `[]` khi mặt phẳng đã đi qua >= 3 đỉnh không thẳng hàng của khối đa diện (giữ `daGiacMatPhang` + `moRongDaGiacMatPhang`).
 */
export function compactPlaneAnchorPoints(
  scene: Pick<Scene3D, "objects">,
  planeObj: SceneObject,
  visibleObjects: readonly SceneObject[],
): Vec3[] {
  if (planeObj.type !== "plane3" || !planeObj.point || !planeObj.normal) return [];
  const p0 = toVec3(planeObj.point);
  const nRaw = toVec3(planeObj.normal);
  const dn = Math.hypot(...nRaw);
  if (!(dn > 1e-9)) return [];
  const u: Vec3 = [nRaw[0] / dn, nRaw[1] / dn, nRaw[2] / dn];
  const allFinite = diemHuuHan([...visibleObjects]);
  const zMin = allFinite.length > 0 ? Math.min(...allFinite.map((p) => p[2])) : -Infinity;

  // 1. Mặt phẳng cắt khối cong (mặt cầu, hình trụ, hình nón) ở cả bước trung gian lẫn bước hoàn tất
  const conicCut = visibleObjects.find(
    (x) => (x.type === "circle3" || x.type === "ellipse3") && (x.depends ?? []).includes(planeObj.id),
  );
  const curvedSolids = visibleObjects.filter((x) => x.type === "curved_solid" && x.anchor);
  if (conicCut) {
    for (const depId of conicCut.depends ?? []) {
      const s = scene.objects.find((obj) => obj.id === depId && obj.type === "curved_solid" && obj.anchor);
      if (s && !curvedSolids.some((c) => c.id === s.id)) curvedSolids.push(s);
    }
  }

  for (const s of curvedSolids) {
    if (s.curved_kind !== "ball" || !s.anchor) continue;
    const centerSphere = toVec3(s.anchor);
    const rSq = s.radius_sq ? toNumber(s.radius_sq) : 0;
    const R = rSq > 0
      ? Math.sqrt(rSq)
      : s.rim_point
        ? Math.hypot(...toVec3(s.rim_point).map((v, k) => v - centerSphere[k]))
        : 0;
    if (!(R > 1e-6)) continue;
    const dPlane =
      (centerSphere[0] - p0[0]) * u[0]
      + (centerSphere[1] - p0[1]) * u[1]
      + (centerSphere[2] - p0[2]) * u[2];
    if (Math.abs(dPlane) > R + 1e-4) continue;
    const center: Vec3 = conicCut?.center
      ? toVec3(conicCut.center)
      : [
          centerSphere[0] - dPlane * u[0],
          centerSphere[1] - dPlane * u[1],
          centerSphere[2] - dPlane * u[2],
        ];
    const rCut = conicCut?.type === "circle3" && conicCut.radius_sq
      ? Math.sqrt(Math.max(0, toNumber(conicCut.radius_sq)))
      : Math.sqrt(Math.max(0, R * R - dPlane * dPlane));
    const [e1, e2] = orthonormalBasisOnPlane(u);
    const hs = Math.max(rCut * 1.30, R * 1.18);
    const ht = Math.max(rCut * 1.24, R * 1.12);
    return [
      [-hs, -ht],
      [hs, -ht],
      [hs, ht],
      [-hs, ht],
    ].map(([sc, tc]): Vec3 => [
      center[0] + sc * e1[0] + tc * e2[0],
      center[1] + sc * e1[1] + tc * e2[1],
      center[2] + sc * e1[2] + tc * e2[2],
    ]);
  }

  const cylConeSolids = curvedSolids.filter(
    (s) => (s.curved_kind === "cylinder" || s.curved_kind === "cone") && s.anchor,
  );
  if (cylConeSolids.length > 0) {
    const piercePts: Vec3[] = [];
    let maxParentR = 0;
    let primaryAxis: Vec3 | null = null;
    for (const s of cylConeSolids) {
      const A = toVec3(s.anchor!);
      const rSq = s.radius_sq ? toNumber(s.radius_sq) : 0;
      const R = rSq > 0
        ? Math.sqrt(rSq)
        : s.rim_point
          ? Math.hypot(...toVec3(s.rim_point).map((v, k) => v - A[k]))
          : 0;
      const h = s.height_sq ? Math.sqrt(Math.max(0, toNumber(s.height_sq))) : 0;
      const T: Vec3 | null = s.apex_or_top
        ? toVec3(s.apex_or_top)
        : h > 0
          ? [A[0], A[1], A[2] + h]
          : null;
      if (!T || !(R > 1e-6)) continue;
      const ax: Vec3 = [T[0] - A[0], T[1] - A[1], T[2] - A[2]];
      const hLen = Math.hypot(...ax);
      if (!(hLen > 1e-6)) continue;
      maxParentR = Math.max(maxParentR, R);
      const uAxis: Vec3 = [ax[0] / hLen, ax[1] / hLen, ax[2] / hLen];
      if (!primaryAxis) primaryAxis = uAxis;
      const [b1, b2] = orthonormalBasisOnPlane(uAxis);
      const M = 64;
      const baseRing: Vec3[] = [];
      const topRing: Vec3[] = [];
      for (let k = 0; k < M; k += 1) {
        const theta = (k / M) * Math.PI * 2;
        const cs = Math.cos(theta);
        const sn = Math.sin(theta);
        const rx = R * (cs * b1[0] + sn * b2[0]);
        const ry = R * (cs * b1[1] + sn * b2[1]);
        const rz = R * (cs * b1[2] + sn * b2[2]);
        baseRing.push([A[0] + rx, A[1] + ry, A[2] + rz]);
        topRing.push(s.curved_kind === "cylinder" ? [T[0] + rx, T[1] + ry, T[2] + rz] : T);
      }
      for (let k = 0; k < M; k += 1) {
        const next = (k + 1) % M;
        for (const p of intersectSegmentWithPlane(baseRing[k], topRing[k], p0, u)) piercePts.push(p);
        for (const p of intersectSegmentWithPlane(baseRing[k], baseRing[next], p0, u)) piercePts.push(p);
        if (s.curved_kind === "cylinder") {
          for (const p of intersectSegmentWithPlane(topRing[k], topRing[next], p0, u)) piercePts.push(p);
        }
      }
    }

    if (conicCut?.center) {
      const cCenter = toVec3(conicCut.center);
      if (conicCut.type === "circle3" && conicCut.radius_sq) {
        const r = Math.sqrt(Math.max(0, toNumber(conicCut.radius_sq)));
        const [ce1, ce2] = orthonormalBasisOnPlane(u);
        for (let k = 0; k < 32; k += 1) {
          const theta = (k / 32) * Math.PI * 2;
          const cs = Math.cos(theta), sn = Math.sin(theta);
          piercePts.push([
            cCenter[0] + r * (cs * ce1[0] + sn * ce2[0]),
            cCenter[1] + r * (cs * ce1[1] + sn * ce2[1]),
            cCenter[2] + r * (cs * ce1[2] + sn * ce2[2]),
          ]);
        }
      } else if (
        conicCut.type === "ellipse3"
        && conicCut.major_dir
        && conicCut.minor_dir
        && conicCut.semi_major_sq
        && conicCut.semi_minor_sq
      ) {
        const a = Math.sqrt(Math.max(0, toNumber(conicCut.semi_major_sq)));
        const b = Math.sqrt(Math.max(0, toNumber(conicCut.semi_minor_sq)));
        const Mv = toVec3(conicCut.major_dir);
        const mv = toVec3(conicCut.minor_dir);
        const dM = Math.hypot(...Mv) || 1;
        const dm = Math.hypot(...mv) || 1;
        for (let k = 0; k < 32; k += 1) {
          const theta = (k / 32) * Math.PI * 2;
          const cs = Math.cos(theta), sn = Math.sin(theta);
          piercePts.push([
            cCenter[0] + a * cs * (Mv[0] / dM) + b * sn * (mv[0] / dm),
            cCenter[1] + a * cs * (Mv[1] / dM) + b * sn * (mv[1] / dm),
            cCenter[2] + a * cs * (Mv[2] / dM) + b * sn * (mv[2] / dm),
          ]);
        }
      }
    }

    if (piercePts.length >= 2) {
      let [e1, e2] = orthonormalBasisOnPlane(u);
      if (
        conicCut?.type === "ellipse3"
        && conicCut.major_dir
        && conicCut.minor_dir
      ) {
        const Mv = toVec3(conicCut.major_dir);
        const mv = toVec3(conicCut.minor_dir);
        const dM = Math.hypot(...Mv) || 1;
        const dm = Math.hypot(...mv) || 1;
        e1 = [Mv[0] / dM, Mv[1] / dM, Mv[2] / dM];
        e2 = [mv[0] / dm, mv[1] / dm, mv[2] / dm];
      } else if (primaryAxis) {
        const dotAU = primaryAxis[0] * u[0] + primaryAxis[1] * u[1] + primaryAxis[2] * u[2];
        const tx = primaryAxis[0] - dotAU * u[0];
        const ty = primaryAxis[1] - dotAU * u[1];
        const tz = primaryAxis[2] - dotAU * u[2];
        const tLen = Math.hypot(tx, ty, tz);
        if (tLen > 1e-5) {
          e1 = [tx / tLen, ty / tLen, tz / tLen];
          e2 = [
            u[1] * e1[2] - u[2] * e1[1],
            u[2] * e1[0] - u[0] * e1[2],
            u[0] * e1[1] - u[1] * e1[0],
          ];
        }
      }
      const pCoords = piercePts.map((pt) => ({
        s: (pt[0] - p0[0]) * e1[0] + (pt[1] - p0[1]) * e1[1] + (pt[2] - p0[2]) * e1[2],
        t: (pt[0] - p0[0]) * e2[0] + (pt[1] - p0[1]) * e2[1] + (pt[2] - p0[2]) * e2[2],
      }));
      const sMinC = Math.min(...pCoords.map((c) => c.s));
      const sMaxC = Math.max(...pCoords.map((c) => c.s));
      const tMinC = Math.min(...pCoords.map((c) => c.t));
      const tMaxC = Math.max(...pCoords.map((c) => c.t));
      const midSC = (sMinC + sMaxC) * 0.5;
      const midTC = (tMinC + tMaxC) * 0.5;
      const hs = Math.max((sMaxC - sMinC) * 0.5 * 1.28, maxParentR * 1.24);
      const ht = Math.max((tMaxC - tMinC) * 0.5 * 1.24, maxParentR * 1.18);
      const curvedBox: Vec3[] = [
        [midSC - hs, midTC - ht],
        [midSC + hs, midTC - ht],
        [midSC + hs, midTC + ht],
        [midSC - hs, midTC + ht],
      ].map(([sc, tc]): Vec3 => [
        p0[0] + sc * e1[0] + tc * e2[0],
        p0[1] + sc * e1[1] + tc * e2[1],
        p0[2] + sc * e1[2] + tc * e2[2],
      ]);
      return clipConvexPolygonAboveZ(curvedBox, zMin);
    }
  }

  if (conicCut && conicCut.center) {
    const center = toVec3(conicCut.center);
    if (conicCut.type === "circle3" && conicCut.radius_sq) {
      const r = Math.sqrt(Math.max(0, toNumber(conicCut.radius_sq)));
      const [e1, e2] = orthonormalBasisOnPlane(u);
      const hs = r * 1.28;
      const ht = r * 1.24;
      return [
        [-hs, -ht],
        [hs, -ht],
        [hs, ht],
        [-hs, ht],
      ].map(([s, t]): Vec3 => [
        center[0] + s * e1[0] + t * e2[0],
        center[1] + s * e1[1] + t * e2[1],
        center[2] + s * e1[2] + t * e2[2],
      ]);
    }
    if (
      conicCut.type === "ellipse3"
      && conicCut.major_dir
      && conicCut.minor_dir
      && conicCut.semi_major_sq
      && conicCut.semi_minor_sq
    ) {
      const a = Math.sqrt(Math.max(0, toNumber(conicCut.semi_major_sq)));
      const b = Math.sqrt(Math.max(0, toNumber(conicCut.semi_minor_sq)));
      const M = toVec3(conicCut.major_dir);
      const m = toVec3(conicCut.minor_dir);
      const dM = Math.hypot(...M) || 1;
      const dm = Math.hypot(...m) || 1;
      const e1: Vec3 = [M[0] / dM, M[1] / dM, M[2] / dM];
      const e2: Vec3 = [m[0] / dm, m[1] / dm, m[2] / dm];
      const hs = a * 1.28;
      const ht = b * 1.24;
      return [
        [-hs, -ht],
        [hs, -ht],
        [hs, ht],
        [-hs, ht],
      ].map(([s, t]): Vec3 => [
        center[0] + s * e1[0] + t * e2[0],
        center[1] + s * e1[1] + t * e2[1],
        center[2] + s * e1[2] + t * e2[2],
      ]);
    }
  }

  // 2. Kiểm tra số đỉnh hình học tường minh (không tính witness.foot) thực sự nằm trên mặt phẳng
  const explicitPts: Vec3[] = [];
  for (const obj of visibleObjects) {
    if (obj.type === "point3" && obj.xyz) explicitPts.push(toVec3(obj.xyz));
    else if (obj.type === "solid" && obj.vertices) for (const v of obj.vertices) explicitPts.push(toVec3(v));
    else if ((obj.type === "section" || obj.type === "polygon3") && (obj.polygon ?? obj.vertices)) {
      for (const v of obj.polygon ?? obj.vertices ?? []) explicitPts.push(toVec3(v));
    }
  }
  const dk = Math.max(duongKinhCanh(allFinite), 1);
  const epsPlane = Math.max(dk * 1e-4, 1e-7);
  const [e1, e2] = orthonormalBasisOnPlane(u);

  const coplanarScenePts: { p: Vec3; s: number; t: number }[] = [];
  for (const p of explicitPts) {
    const vx = p[0] - p0[0], vy = p[1] - p0[1], vz = p[2] - p0[2];
    const dist = vx * u[0] + vy * u[1] + vz * u[2];
    if (Math.abs(dist) > epsPlane) continue;
    const s = vx * e1[0] + vy * e1[1] + vz * e1[2];
    const t = vx * e2[0] + vy * e2[1] + vz * e2[2];
    if (!coplanarScenePts.some((q) => Math.hypot(q.s - s, q.t - t) <= 1e-5)) {
      coplanarScenePts.push({ p: [p[0] - dist * u[0], p[1] - dist * u[1], p[2] - dist * u[2]], s, t });
    }
  }
  if (coplanarScenePts.length >= 3) {
    const a = coplanarScenePts[0];
    const b = coplanarScenePts[1];
    const nonCollinear = coplanarScenePts.slice(2).some(
      (c) => Math.abs((b.s - a.s) * (c.t - a.t) - (b.t - a.t) * (c.s - a.s)) > 1e-4,
    );
    if (nonCollinear) return [];
  }

  // Mặt phẳng đi qua < 3 đỉnh tường minh không thẳng hàng (vd qua B vuông góc SC): kết hợp điểm xuyên cạnh khối thực tế + chân vuông góc
  const anchors: Vec3[] = [p0];
  for (const item of coplanarScenePts) anchors.push(item.p);
  for (const pierce of planeSolidEdgeIntersections(planeObj, visibleObjects)) {
    anchors.push(pierce);
  }
  for (const obj of scene.objects) {
    for (const w of [obj.perpendicular_witness, obj.annotation?.witness]) {
      if (w?.on === planeObj.id && w.foot) {
        const f = toVec3(w.foot);
        const dist = (f[0] - p0[0]) * u[0] + (f[1] - p0[1]) * u[1] + (f[2] - p0[2]) * u[2];
        if (Math.abs(dist) <= epsPlane * 5) {
          anchors.push([f[0] - dist * u[0], f[1] - dist * u[1], f[2] - dist * u[2]]);
        }
      }
    }
  }

  const coords = anchors.map((p) => ({
    s: (p[0] - p0[0]) * e1[0] + (p[1] - p0[1]) * e1[1] + (p[2] - p0[2]) * e1[2],
    t: (p[0] - p0[0]) * e2[0] + (p[1] - p0[1]) * e2[1] + (p[2] - p0[2]) * e2[2],
  }));
  const sMin = Math.min(...coords.map((c) => c.s));
  const sMax = Math.max(...coords.map((c) => c.s));
  const tMin = Math.min(...coords.map((c) => c.t));
  const tMax = Math.max(...coords.map((c) => c.t));
  const midS = (sMin + sMax) / 2;
  const midT = (tMin + tMax) / 2;
  const sSpan = sMax - sMin;
  const tSpan = tMax - tMin;
  const localSpan = Math.hypot(sSpan, tSpan);
  const padS = Math.min(dk * 0.10, Math.max(localSpan * 0.11, dk * 0.06));
  const padT = Math.max(tSpan * 0.48, dk * 0.24);
  const hs = Math.max(sSpan * 0.5 + padS, dk * 0.22);
  const ht = Math.max(tSpan * 0.5 + padT, dk * 0.26);

  const box: Vec3[] = [
    [midS - hs, midT - ht],
    [midS + hs, midT - ht],
    [midS + hs, midT + ht],
    [midS - hs, midT - ht + 2 * ht],
  ].map(([s, t]): Vec3 => [
    p0[0] + s * e1[0] + t * e2[0],
    p0[1] + s * e1[1] + t * e2[1],
    p0[2] + s * e1[2] + t * e2[2],
  ]);

  return clipConvexPolygonAboveZ(box, zMin);
}

function convexHull2D(pts: { s: number; t: number }[]): { s: number; t: number }[] {
  if (pts.length <= 2) return pts.slice();
  const sorted = [...pts].sort((a, b) => (a.s !== b.s ? a.s - b.s : a.t - b.t));
  const cross = (o: { s: number; t: number }, a: { s: number; t: number }, b: { s: number; t: number }) =>
    (a.s - o.s) * (b.t - o.t) - (a.t - o.t) * (b.s - o.s);
  const lower: { s: number; t: number }[] = [];
  for (const p of sorted) {
    while (lower.length >= 2 && cross(lower[lower.length - 2], lower[lower.length - 1], p) <= 1e-8) {
      lower.pop();
    }
    lower.push(p);
  }
  const upper: { s: number; t: number }[] = [];
  for (let i = sorted.length - 1; i >= 0; i -= 1) {
    const p = sorted[i];
    while (upper.length >= 2 && cross(upper[upper.length - 2], upper[upper.length - 1], p) <= 1e-8) {
      upper.pop();
    }
    upper.push(p);
  }
  lower.pop();
  upper.pop();
  return [...lower, ...upper];
}

/**
 * Tạo miền đa giác minh họa hữu hạn gọn cho các mặt phẳng nghiên cứu đi qua >= 3 đỉnh không thẳng hàng của khối đa diện
 * (như `(SAC)`, `(SBD)` trong bài giao tuyến hai mặt phẳng, góc nhị diện, góc đường–mặt) mà KHÔNG có thiết diện cắt khối.
 * Giữ nguyên phương trình mặt phẳng `(point, normal)`, bao trọn mọi điểm/giao tuyến liên quan nhưng không phình thành tấm chữ nhật khổng lồ.
 */
export interface StudiedPlaneVisualStyle {
  rank: number;
  coexistingCount: number;
  fillColor: number;
  strokeColor: number;
  borderColor: number;
  opacityScale: number;
  continuousPlaneBorder: boolean;
  cornerArcIndex: number;
}

/**
 * Xác định phong cách trực quan phân biệt khi nhiều mặt phẳng nghiên cứu cùng xuất hiện (vd `(SAC)` và `(SBD)`, `(SAM)` và `(SBD)`):
 * - Giữ nguyên hệ màu tím ngữ nghĩa của Axo (`#6D28D9` cho mặt phẳng thứ nhất, `#8B3DFF` cùng họ tím cho mặt phẳng thứ hai).
 * - Khi có >= 2 mặt phẳng nghiên cứu cùng hiện: dùng viền liên tục (`continuousPlaneBorder: true`, không đứt đoạn để tránh nhầm với cạnh khuất khối),
 *   kèm lệch nhẹ bậc biên (`rank`) và cung ký hiệu góc mặt phẳng (`cornerArcIndex`) không phụ thuộc màu sắc.
 */
export function resolveStudiedPlaneVisualStyle(
  scene: Pick<Scene3D, "objects"> & Partial<Pick<Scene3D, "events">>,
  planeObj: SceneObject,
  visibleObjects: readonly SceneObject[],
  isSelected = false,
): StudiedPlaneVisualStyle {
  const sceneWrap: Scene3D = {
    free_objects: [],
    objects: scene.objects,
    events: scene.events ?? [],
  };
  const orderMap = new Map(scene.objects.map((o, idx) => [o.id, idx]));
  const hasClosedSection = (plId: string) =>
    scene.objects.some(
      (x) =>
        (x.type === "section" || x.type === "circle3" || x.type === "ellipse3")
        && (x.depends ?? []).includes(plId),
    );
  const coexisting = visibleObjects
    .filter(
      (o) =>
        o.type === "plane3"
        && !isDuplicateOfSolidFace(sceneWrap, o)
        && !hasClosedSection(o.id),
    )
    .sort((a, b) => (orderMap.get(a.id) ?? 0) - (orderMap.get(b.id) ?? 0));

  const idx = coexisting.findIndex((o) => o.id === planeObj.id);
  const rank = idx >= 0 ? idx : 0;
  const coexistingCount = idx >= 0 ? coexisting.length : Math.max(1, coexisting.length);
  const isSecondaryTone = coexistingCount >= 2 && rank % 2 === 1;
  const strokeColor = isSecondaryTone ? S.colors.secondaryPlaneOutline : S.colors.planeOutline;
  const opacityScale = !isSelected && coexistingCount >= 2 ? (rank === 0 ? 0.78 : 0.74) : 1;
  return {
    rank,
    coexistingCount,
    fillColor: isSecondaryTone ? S.colors.secondarySurface : S.colors.surface,
    strokeColor,
    borderColor: strokeColor,
    opacityScale,
    continuousPlaneBorder: coexistingCount >= 2,
    cornerArcIndex: rank % 2 === 0 ? 2 : 3,
  };
}

/**
 * Phương án 3 (Adaptive Bounded 4-Gon Finite Plane Patch):
 * Tạo miền tứ giác phẳng hữu hạn (`4-gon`) cho các mặt phẳng nghiên cứu đi qua >= 3 đỉnh không thẳng hàng của khối đa diện
 * (như `(SAC)`, `(SBD)`, `(SAM)` trong bài giao tuyến hai mặt phẳng, góc nhị diện, góc đường–mặt) mà KHÔNG có thiết diện cắt khối.
 * - Giữ nguyên tuyệt đối phương trình mặt phẳng `(point, normal)` và mọi giao điểm/giao tuyến.
 * - Vượt ra ngoài tam giác xác định một khoảng thích ứng vừa đủ ở hai bên và vai trên đỉnh để học sinh nhận biết rõ đây là
 *   mặt phẳng mở rộng chứ không phải mặt tam giác `△SAC`/`△SBD`, đồng thời không phình thành tấm chữ nhật lớn che khuất hình chóp.
 * - Bất biến theo góc quay camera (không giật/nhấp nháy khi Orbit), có lệch nhẹ theo `rank` khi nhiều mặt phẳng cùng xuất hiện để hai biên không trùng khít.
 */
export function computeBoundedStudiedPlanePolygon(
  scene: Pick<Scene3D, "objects"> & Partial<Pick<Scene3D, "events">>,
  planeObj: SceneObject,
  visibleObjects: readonly SceneObject[],
): Vec3[] {
  if (planeObj.type !== "plane3" || !planeObj.point || !planeObj.normal) return [];
  if (visibleObjects.some((x) => x.type === "curved_solid")) return [];
  const hasCutResult = scene.objects.some(
    (x) =>
      (x.type === "section"
        || x.type === "circle3"
        || x.type === "ellipse3"
        || (x.type === "polygon3" && vaiTroMien(x) === "section"))
      && (x.depends ?? []).includes(planeObj.id),
  );
  if (!visibleObjects.some((x) => x.type === "solid")) return [];

  const p0 = toVec3(planeObj.point);
  const nRaw = toVec3(planeObj.normal);
  const dn = Math.hypot(...nRaw);
  if (!(dn > 1e-9)) return [];
  const u: Vec3 = [nRaw[0] / dn, nRaw[1] / dn, nRaw[2] / dn];
  const allFinite = diemHuuHan([...visibleObjects]);
  if (allFinite.length === 0) return [];
  const zMin = Math.min(...allFinite.map((p) => p[2]));
  const zMax = Math.max(...allFinite.map((p) => p[2]));
  const dk = Math.max(duongKinhCanh(allFinite), 1);
  const epsPlane = Math.max(dk * 1e-4, 1e-7);

  const candidates: Vec3[] = [];
  for (const obj of visibleObjects) {
    if (obj.type === "point3" && obj.xyz) candidates.push(toVec3(obj.xyz));
    else if (obj.type === "solid" && obj.vertices) {
      for (const v of obj.vertices) candidates.push(toVec3(v));
    }
  }
  for (const pierce of planeSolidEdgeIntersections(planeObj, visibleObjects)) {
    candidates.push(pierce);
  }
  for (const obj of scene.objects) {
    for (const w of [obj.perpendicular_witness, obj.annotation?.witness]) {
      if (w?.on === planeObj.id && w.foot) candidates.push(toVec3(w.foot));
    }
  }

  const coplanarPts: Vec3[] = [];
  for (const p of candidates) {
    const vx = p[0] - p0[0], vy = p[1] - p0[1], vz = p[2] - p0[2];
    const dist = vx * u[0] + vy * u[1] + vz * u[2];
    if (Math.abs(dist) > epsPlane * 3) continue;
    const proj: Vec3 = [p[0] - dist * u[0], p[1] - dist * u[1], p[2] - dist * u[2]];
    if (!coplanarPts.some((q) => Math.hypot(q[0] - proj[0], q[1] - proj[1], q[2] - proj[2]) <= 1e-5)) {
      coplanarPts.push(proj);
    }
  }
  if (coplanarPts.length < 3) return [];

  const [b1, b2] = orthonormalBasisOnPlane(u);
  const hullCheck = convexHull2D(
    coplanarPts.map((p) => ({
      s: (p[0] - p0[0]) * b1[0] + (p[1] - p0[1]) * b1[1] + (p[2] - p0[2]) * b1[2],
      t: (p[0] - p0[0]) * b2[0] + (p[1] - p0[1]) * b2[1] + (p[2] - p0[2]) * b2[2],
    })),
  );
  if (hullCheck.length < 3) return [];

  const style = resolveStudiedPlaneVisualStyle(scene, planeObj, visibleObjects);
  const cutCollarScale = hasCutResult ? 0.68 : 1.0;
  const multiScale = (style.coexistingCount >= 2 ? 0.92 : 1.0) * cutCollarScale;
  const rankDelta = style.coexistingCount >= 2 ? (style.rank % 3) * 0.022 * dk : 0;

  const nXY = Math.hypot(u[0], u[1]);
  // Trường hợp 1: Mặt phẳng nghiêng hoặc thẳng đứng (có giao tuyến ngang eHoriz xác định) → dựng tấm tứ giác hình thang phối cảnh SGK
  if (nXY > 0.14) {
    const eHoriz: Vec3 = [-u[1] / nXY, u[0] / nXY, 0];
    const eSlope: Vec3 = [(-u[2] * u[0]) / nXY, (-u[2] * u[1]) / nXY, nXY];
    const stPts = coplanarPts.map((p) => ({
      p,
      s: (p[0] - p0[0]) * eHoriz[0] + (p[1] - p0[1]) * eHoriz[1],
      t: (p[0] - p0[0]) * eSlope[0] + (p[1] - p0[1]) * eSlope[1] + (p[2] - p0[2]) * eSlope[2],
    }));

    const sAllMin = Math.min(...stPts.map((c) => c.s));
    const sAllMax = Math.max(...stPts.map((c) => c.s));
    const tAllMin = Math.min(...stPts.map((c) => c.t));
    const tAllMax = Math.max(...stPts.map((c) => c.t));
    const sWidth = Math.max(sAllMax - sAllMin, dk * 0.24);
    const tHeight = Math.max(tAllMax - tAllMin, dk * 0.24);

    const minPlaneZ = Math.min(...coplanarPts.map((p) => p[2]));
    const restsOnBase = Math.abs(minPlaneZ - zMin) <= epsPlane * 5;
    const tAtZMin = (zMin - p0[2]) / eSlope[2];
    const botPad = restsOnBase ? 0 : Math.min(dk * 0.075, tHeight * 0.11) * multiScale;
    const tBot = restsOnBase ? tAtZMin : Math.max(tAtZMin, tAllMin - botPad);

    const zSpan = Math.max(zMax - zMin, 1e-3);
    const zTopPad = Math.min(dk * 0.082, Math.max(zSpan * 0.105, dk * 0.055)) * multiScale + rankDelta;
    const zTopTarget = Math.min(zMax + zSpan * 0.18, Math.max(...coplanarPts.map((p) => p[2])) + zTopPad);
    const tTop = Math.max(tAllMax + 0.04 * dk, (zTopTarget - p0[2]) / eSlope[2]);

    const lowerPts = stPts.filter((c) => c.t <= tAllMin + 0.36 * tHeight);
    const upperPts = stPts.filter((c) => c.t >= tAllMax - 0.36 * tHeight);
    const sLowMin = lowerPts.length > 0 ? Math.min(...lowerPts.map((c) => c.s)) : sAllMin;
    const sLowMax = lowerPts.length > 0 ? Math.max(...lowerPts.map((c) => c.s)) : sAllMax;
    const sUpMin = upperPts.length > 0 ? Math.min(...upperPts.map((c) => c.s)) : sAllMin;
    const sUpMax = upperPts.length > 0 ? Math.max(...upperPts.map((c) => c.s)) : sAllMax;

    const latPad = (Math.min(dk * 0.115, Math.max(sWidth * 0.155, dk * 0.075)) * multiScale) + rankDelta * 0.45;
    const sBotLo = Math.min(sLowMin, sAllMin) - latPad;
    const sBotHi = Math.max(sLowMax, sAllMax) + latPad;

    const sLowMid = 0.5 * (sLowMin + sLowMax);
    const shoulderPad = Math.min(dk * 0.105, Math.max(latPad * 0.86, sWidth * 0.14));
    let sTopLo: number;
    let sTopHi: number;
    if (hasCutResult) {
      sTopLo = sUpMin - shoulderPad;
      sTopHi = sUpMax + shoulderPad;
      const minCutTopSpan = Math.min(0.24 * sWidth, shoulderPad * 2.1);
      if (sTopHi - sTopLo < minCutTopSpan) {
        const midTop = 0.5 * (sTopLo + sTopHi);
        sTopLo = midTop - 0.5 * minCutTopSpan;
        sTopHi = midTop + 0.5 * minCutTopSpan;
      }
    } else {
      sTopLo = Math.min(sUpMin - shoulderPad, sLowMid - 0.22 * sWidth);
      sTopHi = Math.max(sUpMax + shoulderPad, sLowMid + 0.22 * sWidth);
      if (sTopHi - sTopLo < 0.38 * sWidth) {
        const midTop = 0.5 * (sTopLo + sTopHi);
        sTopLo = midTop - 0.19 * sWidth;
        sTopHi = midTop + 0.19 * sWidth;
      }
    }
    sTopLo = Math.max(sTopLo, sBotLo + 0.06 * latPad);
    sTopHi = Math.min(sTopHi, sBotHi - 0.06 * latPad);
    if (sTopHi <= sTopLo + 1e-4) {
      sTopLo = sBotLo;
      sTopHi = sBotHi;
    }

    const to3D = (s: number, t: number): Vec3 => [
      p0[0] + s * eHoriz[0] + t * eSlope[0],
      p0[1] + s * eHoriz[1] + t * eSlope[1],
      p0[2] + t * eSlope[2],
    ];

    return [
      to3D(sBotLo, tBot),
      to3D(sBotHi, tBot),
      to3D(sTopHi, tTop),
      to3D(sTopLo, tTop),
    ];
  }

  // Trường hợp 2: Mặt phẳng nằm ngang / gần ngang → dựng hình chữ nhật 4 đỉnh theo hệ trục trực chuẩn trên mặt phẳng
  const sVals = coplanarPts.map((p) => (p[0] - p0[0]) * b1[0] + (p[1] - p0[1]) * b1[1] + (p[2] - p0[2]) * b1[2]);
  const tVals = coplanarPts.map((p) => (p[0] - p0[0]) * b2[0] + (p[1] - p0[1]) * b2[1] + (p[2] - p0[2]) * b2[2]);
  const sMin = Math.min(...sVals), sMax = Math.max(...sVals);
  const tMin = Math.min(...tVals), tMax = Math.max(...tVals);
  const padS = Math.min(dk * 0.11, Math.max((sMax - sMin) * 0.16, dk * 0.07)) * multiScale + rankDelta * 0.4;
  const padT = Math.min(dk * 0.11, Math.max((tMax - tMin) * 0.16, dk * 0.07)) * multiScale + rankDelta * 0.4;
  const toFlat3D = (s: number, t: number): Vec3 => [
    p0[0] + s * b1[0] + t * b2[0],
    p0[1] + s * b1[1] + t * b2[1],
    p0[2] + s * b1[2] + t * b2[2],
  ];
  return [
    toFlat3D(sMin - padS, tMin - padT),
    toFlat3D(sMax + padS, tMin - padT),
    toFlat3D(sMax + padS, tMax + padT),
    toFlat3D(sMin - padS, tMax + padT),
  ];
}

function rotateVec(v: Vec3, q?: THREE.Quaternion): Diem3 {
  if (!q) return [v[0], v[1], v[2]];
  const tv = new THREE.Vector3(v[0], v[1], v[2]).applyQuaternion(q);
  return [tv.x, tv.y, tv.z];
}

/**
 * Cấu trúc hình học + trọng tâm sư phạm cho `chonHuongNhin`:
 * - Mở rộng diện tích hình chiếu của thiết diện (`section`, `polygon3` thiết diện, `ellipse3`/`circle3` nghiêng).
 * - Mở rõ tam giác trục – bán kính – đường sinh của hình nón/trụ khi có điểm vành đáy khai báo.
 * - Mở rõ tam giác nhân chứng vuông góc (điểm – chân vuông góc – điểm tựa trên mặt/đường).
 * - Tách hai đáy hình trụ không chồng lấn.
 */
export function cauTrucSuPham(
  objects: SceneObject[],
  qHienThi?: THREE.Quaternion,
): { diem: Diem3[]; canh: [number, number][]; mat: number[][]; tuyChon: TuyChonHuongNhin } {
  const ct = cauTrucGocNhin(objects);
  const diem = qHienThi ? ct.diem.map((p) => rotateVec(p, qHienThi)) : ct.diem;
  const pointById = new Map<string, Diem3>();
  for (const o of objects) {
    if (o.type === "point3" && o.xyz) {
      pointById.set(o.id, rotateVec(toVec3(o.xyz), qHienThi));
    }
  }

  const matTrongTam: Diem3[] = [];
  const capDayTru: [Diem3, Diem3, number][] = [];
  const matCap: [Diem3, Diem3][] = [];
  let coKhoiCong = false;
  const sceneWrap: Scene3D = { free_objects: [], objects, events: [] };

  for (const o of objects) {
    if (o.type === "solid" && o.vertices && o.faces && o.faces.length >= 4) {
      const verts = o.vertices.map((v) => rotateVec(toVec3(v), qHienThi));
      const horizFaces: [Diem3, Diem3][] = [];
      for (const f of o.faces) {
        if (f.length < 3) continue;
        const pts = f.map((idx) => verts[idx]).filter(Boolean);
        const n = normalFromPoints(pts);
        if (n && Math.abs(n[2]) > 0.85) {
          const cx = pts.reduce((s, p) => s + p[0], 0) / pts.length;
          const cy = pts.reduce((s, p) => s + p[1], 0) / pts.length;
          const cz = pts.reduce((s, p) => s + p[2], 0) / pts.length;
          horizFaces.push([[cx, cy, cz], n]);
        }
      }
      if (horizFaces.length >= 2) {
        matCap.push(...horizFaces);
      }
    }
    if (
      o.type === "circle3"
      && o.center
      && o.normal
      && classifyCircleSemanticRole(sceneWrap, o) === "BOUNDARY_AND_INTERSECTION"
    ) {
      const c = rotateVec(toVec3(o.center), qHienThi);
      const nRaw = rotateVec(toVec3(o.normal), qHienThi);
      const nLen = Math.hypot(...nRaw);
      if (nLen > 1e-6) {
        matCap.push([c, [nRaw[0] / nLen, nRaw[1] / nLen, nRaw[2] / nLen]]);
      }
    }
    const isSolidFace = Boolean(o.type === "polygon3" && o.parent && (o.display_group ?? []).includes("face"));
    const polyPts = o.polygon ?? o.vertices;
    if (
      !isSolidFace
      && (o.type === "section" || (o.type === "polygon3" && vaiTroMien(o) === "section"))
      && polyPts
      && polyPts.length >= 3
    ) {
      const n = normalFromPoints(polyPts.map((p) => rotateVec(toVec3(p), qHienThi)));
      if (n) matTrongTam.push(n);
    } else if (
      (o.type === "ellipse3" && vaiTroMien(o) === "section" && o.normal)
      || (o.type === "circle3" && classifyCircleSemanticRole(sceneWrap, o) === "RESULT_SECTION" && o.normal)
    ) {
      const n = rotateVec(toVec3(o.normal), qHienThi);
      const len = Math.hypot(...n);
      if (len > 1e-6 && Math.abs(n[2] / len) < 0.96) {
        matTrongTam.push([n[0] / len, n[1] / len, n[2] / len]);
      }
    } else if (o.type === "plane3" && o.normal && !isDuplicateOfSolidFace(sceneWrap, o)) {
      const hasPolySection = objects.some(
        (x) => (x.type === "section" || x.type === "ellipse3") && (x.depends ?? []).includes(o.id),
      );
      if (!hasPolySection) {
        const n = rotateVec(toVec3(o.normal), qHienThi);
        const len = Math.hypot(...n);
        if (len > 1e-6 && Math.abs(n[2] / len) < 0.96) {
          matTrongTam.push([n[0] / len, n[1] / len, n[2] / len]);
        }
      }
    } else if (o.type === "curved_solid" && o.anchor) {
      if (o.curved_kind === "cone" || o.curved_kind === "cylinder") {
        coKhoiCong = true;
      }
      const anchor = rotateVec(toVec3(o.anchor), qHienThi);
      const rSq = o.radius_sq ? toNumber(o.radius_sq) : 0;
      const r = rSq > 0
        ? Math.sqrt(rSq)
        : o.rim_point
          ? Math.hypot(...rotateVec(toVec3(o.rim_point), qHienThi).map((v, k) => v - anchor[k]))
          : 0;
      const h = o.height_sq ? Math.sqrt(Math.max(0, toNumber(o.height_sq))) : 0;
      const top: Diem3 | null = o.apex_or_top
        ? rotateVec(toVec3(o.apex_or_top), qHienThi)
        : o.curved_kind !== "ball" && h > 0
          ? rotateVec([toVec3(o.anchor)[0], toVec3(o.anchor)[1], toVec3(o.anchor)[2] + h], qHienThi)
          : null;
      if (o.curved_kind === "cylinder" && top && r > 1e-6) {
        capDayTru.push([anchor, top, r]);
        const ax = top[0] - anchor[0], ay = top[1] - anchor[1], az = top[2] - anchor[2];
        const aLen = Math.hypot(ax, ay, az);
        if (aLen > 1e-6) {
          const uCap: Diem3 = [ax / aLen, ay / aLen, az / aLen];
          matCap.push([anchor, uCap], [top, uCap]);
        }
      }
      if (o.curved_kind !== "ball" && top) {
        for (const depId of o.depends ?? []) {
          const pt = pointById.get(depId);
          if (!pt) continue;
          const n = normalFromPoints([anchor, top, pt]);
          if (n) matTrongTam.push(n);
        }
      }
    }
    for (const w of [o.perpendicular_witness, o.annotation?.witness]) {
      if (w?.foot && w.from) {
        const fromPt = pointById.get(w.from);
        const footPt = rotateVec(toVec3(w.foot), qHienThi);
        if (fromPt) {
          const anchorOnTarget = w.on ? objects.find((x) => x.id === w.on) : undefined;
          const thirdId = anchorOnTarget?.depends?.find((id) => pointById.has(id));
          const thirdPt = thirdId ? pointById.get(thirdId) : undefined;
          const n = thirdPt ? normalFromPoints([fromPt, footPt, thirdPt]) : null;
          if (n) matTrongTam.push(n);
        }
      }
    }
  }

  return {
    diem,
    canh: ct.canh,
    mat: ct.mat,
    tuyChon: {
      matTrongTam,
      capDayTru,
      matCap,
      coKhoiCong,
    },
  };
}

function createReferencePoolGeometry(): THREE.BufferGeometry {
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(new Float32Array(6), 3));
  geo.setAttribute("lineDistance", new THREE.Float32BufferAttribute(new Float32Array(2), 1));
  return geo;
}

function segmentContainsBoth(
  segA: Vec3,
  segB: Vec3,
  p: Vec3,
  q: Vec3,
  tol = 1e-4,
): boolean {
  const onSeg = (pt: Vec3) => {
    const abx = segB[0] - segA[0], aby = segB[1] - segA[1], abz = segB[2] - segA[2];
    const lenSq = abx * abx + aby * aby + abz * abz;
    if (lenSq < 1e-12) return false;
    const apx = pt[0] - segA[0], apy = pt[1] - segA[1], apz = pt[2] - segA[2];
    const t = (apx * abx + apy * aby + apz * abz) / lenSq;
    if (t < -1e-3 || t > 1 + 1e-3) return false;
    return Math.hypot(segA[0] + abx * t - pt[0], segA[1] + aby * t - pt[1], segA[2] + abz * t - pt[2]) <= tol;
  };
  return onSeg(p) && onSeg(q);
}

function buildReferenceSegmentNode(
  name: string,
  sourceObjectId: string,
  role: "CURVED_AXIS_REFERENCE" | "CURVED_RADIUS_REFERENCE" | "QUANTITY_SPAN_REFERENCE",
  aVec: Vec3,
  bVec: Vec3,
  dashSize: number,
  alwaysDashed: boolean,
  color: number = S.colors.line,
): THREE.Group {
  const a = new THREE.Vector3(...aVec);
  const b = new THREE.Vector3(...bVec);
  const group = new THREE.Group();
  group.name = name;
  group.userData.voHan = true;
  group.userData.semanticLineRole = "auxiliary_line";
  group.userData.lamDiu = 0.92;
  group.userData.presentationReference = {
    role,
    source_object_id: sourceObjectId,
    authoritative: false,
  };
  group.raycast = () => {};

  const g = new THREE.BufferGeometry().setFromPoints([a, b]);

  if (alwaysDashed) {
    const dashed = new THREE.Line(
      g,
      new THREE.LineDashedMaterial({
        color,
        dashSize,
        gapSize: dashSize * S.dash.gapRatio,
        transparent: true,
        opacity: 0.78,
        depthTest: false,
        depthWrite: false,
      }),
    );
    dashed.computeLineDistances();
    dashed.name = `${name}:khuat`;
    dashed.userData.hidden = true;
    dashed.userData.semanticLineRole = "auxiliary_line";
    dashed.renderOrder = 4;
    dashed.raycast = () => {};
    group.add(dashed);
    return group;
  }

  const lineThay = new THREE.Line(
    g,
    new THREE.LineBasicMaterial({
      color,
      transparent: true,
      opacity: 0.86,
      depthFunc: THREE.LessEqualDepth,
      depthWrite: false,
    }),
  );
  lineThay.name = `${name}:thay`;
  lineThay.userData.semanticLineRole = "auxiliary_line";
  lineThay.renderOrder = 4;
  lineThay.raycast = () => {};

  const lineKhuat = new THREE.Line(
    g.clone(),
    new THREE.LineDashedMaterial({
      color,
      dashSize,
      gapSize: dashSize * S.dash.gapRatio,
      transparent: true,
      opacity: S.opacity.hiddenEdge * 0.86,
      depthFunc: THREE.GreaterDepth,
      depthWrite: false,
    }),
  );
  lineKhuat.computeLineDistances();
  lineKhuat.name = `${name}:khuat`;
  lineKhuat.userData.hidden = true;
  lineKhuat.userData.semanticLineRole = "auxiliary_line";
  lineKhuat.renderOrder = 4;
  lineKhuat.raycast = () => {};

  group.add(lineThay, lineKhuat);
  group.userData.spanGeoPool = Array.from({ length: 6 }, () => createReferencePoolGeometry());
  group.userData.nonCanonicalSegment = {
    prefix: name,
    objectId: name,
    a,
    b,
    color,
    dashSize,
    highlighted: false,
    yieldColinear: true,
    renderOrder: 4,
    noRaycast: true,
  };
  return group;
}

/**
 * Dựng nhóm đường tham chiếu trình bày phi thẩm quyền (`authoritative: false`) từ dữ liệu hợp đồng có sẵn:
 * - Trục hữu hạn của hình nón / hình trụ (`anchor ↔ apex_or_top`) khi chưa có đường/cạnh nào phủ lên.
 * - Bán kính đáy / mặt cầu / đường tròn nội-ngoại tiếp tới điểm vành đã khai báo trong `depends` (`anchor/center ↔ P`) khi chưa có cạnh phủ lên.
 * - Đoạn nối hai điểm mút của một đại lượng độ dài (`quantity` `annotation.kind === "length"` với 2 `point3` đang hiện,
 *   như đường sinh `l = SA` của hình nón) khi chưa có cạnh vật lý nào nối hai điểm ấy.
 * Tuyệt đối KHÔNG sửa `scene.objects` và KHÔNG sinh ký hiệu góc vuông chưa được chứng nhận.
 */
export function buildContractReferenceGroup(
  scene: Pick<Scene3D, "objects"> & Partial<Pick<Scene3D, "events">>,
  visibleObjects: readonly SceneObject[],
  _step: number,
): THREE.Group | null {
  const finitePts = diemHuuHan([...visibleObjects]);
  const dk = Math.max(duongKinhCanh(finitePts), 2);
  const dashSize = Math.max(0.11, dk * 0.032);

  const existingSpans: [Vec3, Vec3][] = [];
  for (const o of visibleObjects) {
    if (o.display_role === "hit_proxy") continue;
    if (o.type === "solid" && o.vertices && o.faces) {
      const verts = o.vertices.map(toVec3);
      for (const f of o.faces) {
        for (let i = 0; i < f.length; i += 1) {
          existingSpans.push([verts[f[i]], verts[f[(i + 1) % f.length]]]);
        }
      }
    } else if ((o.type === "section" || o.type === "polygon3") && (o.polygon || o.vertices)) {
      const pts = (o.polygon ?? o.vertices ?? []).map(toVec3);
      const count = o.closed === false ? Math.max(0, pts.length - 1) : pts.length;
      for (let i = 0; i < count; i += 1) {
        existingSpans.push([pts[i], pts[(i + 1) % pts.length]]);
      }
    } else if (o.type === "segment3" && ((o.point_a && o.point_b) || (o.endpoints && o.endpoints.length >= 2))) {
      const a = toVec3(o.point_a ?? o.endpoints![0]);
      const b = toVec3(o.point_b ?? o.endpoints![1]);
      existingSpans.push([a, b]);
    } else if (o.type === "line3" && o.point && o.direction) {
      const p = toVec3(o.point);
      const d = toVec3(o.direction);
      const len = Math.hypot(...d) || 1;
      const u: Vec3 = [d[0] / len, d[1] / len, d[2] / len];
      existingSpans.push([
        [p[0] - u[0] * dk * 2, p[1] - u[1] * dk * 2, p[2] - u[2] * dk * 2],
        [p[0] + u[0] * dk * 2, p[1] + u[1] * dk * 2, p[2] + u[2] * dk * 2],
      ]);
    }
  }

  const isCovered = (a: Vec3, b: Vec3) =>
    Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]) <= 1e-5
    || existingSpans.some(([sa, sb]) => segmentContainsBoth(sa, sb, a, b));

  const visiblePointById = new Map<string, Vec3>();
  for (const o of visibleObjects) {
    if (o.type === "point3" && o.xyz && !o.id.includes("::")) {
      visiblePointById.set(o.id, toVec3(o.xyz));
    }
  }

  const refRoot = new THREE.Group();
  refRoot.name = "contract_reference_group";
  refRoot.userData.voHan = true;
  refRoot.userData.presentationReference = {
    role: "CONTRACT_REFERENCE_GROUP",
    source_object_id: "scene",
    authoritative: false,
  };

  for (const o of visibleObjects) {
    if (o.type === "curved_solid" && o.anchor && o.curved_kind) {
      const anchor = toVec3(o.anchor);
      const rSq = o.radius_sq ? toNumber(o.radius_sq) : 0;
      const r = rSq > 0
        ? Math.sqrt(rSq)
        : o.rim_point
          ? Math.hypot(...toVec3(o.rim_point).map((v, k) => v - anchor[k]))
          : 0;
      const h = o.height_sq ? Math.sqrt(Math.max(0, toNumber(o.height_sq))) : 0;
      const top: Vec3 | null = o.apex_or_top
        ? toVec3(o.apex_or_top)
        : o.curved_kind !== "ball" && h > 0
          ? [anchor[0], anchor[1], anchor[2] + h]
          : null;

      if (o.curved_kind !== "ball" && top && !isCovered(anchor, top)) {
        refRoot.add(
          buildReferenceSegmentNode(`curved_axis:${o.id}`, o.id, "CURVED_AXIS_REFERENCE", anchor, top, dashSize, true),
        );
        existingSpans.push([anchor, top]);
      }

      if (r > 1e-6) {
        const sphereRole = o.curved_kind === "ball" ? classifySphereSemanticRole(scene, o) : "STANDALONE_SPHERE";
        const radColor = sphereRole === "INSCRIBED_SPHERE"
          ? S.colors.inscribed
          : sphereRole === "CIRCUMSCRIBED_SPHERE"
            ? S.colors.circumscribedSphere
            : S.colors.line;
        for (const depId of o.depends ?? []) {
          const pt = visiblePointById.get(depId);
          if (!pt) continue;
          const dist = Math.hypot(pt[0] - anchor[0], pt[1] - anchor[1], pt[2] - anchor[2]);
          if (Math.abs(dist - r) <= 1e-3 * Math.max(1, r) && !isCovered(anchor, pt)) {
            refRoot.add(
              buildReferenceSegmentNode(
                `curved_radius:${o.id}:${depId}`,
                o.id,
                "CURVED_RADIUS_REFERENCE",
                anchor,
                pt,
                dashSize,
                true,
                radColor,
              ),
            );
            existingSpans.push([anchor, pt]);
          }
        }
      }
      continue;
    }

    if (o.type === "circle3" && o.center && o.radius_sq) {
      const circleRole = classifyCircleSemanticRole(scene, o);
      if (circleRole === "REFERENCE_EQUATOR" || circleRole === "REFERENCE_GREAT_CIRCLE") continue;
      const center = toVec3(o.center);
      const r = Math.sqrt(Math.max(0, toNumber(o.radius_sq)));
      if (!(r > 1e-6)) continue;
      const radColor = circleRole === "INSCRIBED_CIRCLE"
        ? S.colors.inscribed
        : circleRole === "CIRCUMSCRIBED_CIRCLE"
          ? S.colors.circumscribedCircle
          : S.colors.line;
      for (const depId of o.depends ?? []) {
        const pt = visiblePointById.get(depId);
        if (!pt) continue;
        const dist = Math.hypot(pt[0] - center[0], pt[1] - center[1], pt[2] - center[2]);
        if (Math.abs(dist - r) <= 1e-3 * Math.max(1, r) && !isCovered(center, pt)) {
          refRoot.add(
            buildReferenceSegmentNode(
              `circle_radius:${o.id}:${depId}`,
              o.id,
              "CURVED_RADIUS_REFERENCE",
              center,
              pt,
              dashSize,
              true,
              radColor,
            ),
          );
          existingSpans.push([center, pt]);
        }
      }
    }
  }

  const curvedPointIds = new Set(
    visibleObjects
      .filter((o) => o.type === "curved_solid")
      .flatMap((o) => o.depends ?? []),
  );
  const measuredQtyIds = scene.events?.length
    ? new Set(
        scene.events
          .filter((ev) => ev && ev.step_index <= _step && ev.action === "MEASURE" && Boolean(ev.object))
          .map((ev) => ev.object!),
      )
    : null;
  for (const qty of scene.objects) {
    if (qty.type !== "quantity" || qty.annotation?.kind !== "length") continue;
    if (qty.annotation.witness || qty.perpendicular_witness) continue;
    if (measuredQtyIds && qty.origin !== "free" && !measuredQtyIds.has(qty.id)) continue;
    const subs = qty.annotation.subject_ids ?? [];
    if (subs.length !== 2) continue;
    if (!subs.every((id) => curvedPointIds.has(id))) continue;
    const hasExplicitSpanInScene = scene.objects.some(
      (cand) =>
        (cand.type === "segment3" || cand.type === "line3")
        && (cand.depends ?? []).length === 2
        && cand.depends!.includes(subs[0])
        && cand.depends!.includes(subs[1]),
    );
    if (hasExplicitSpanInScene) continue;
    const p1 = visiblePointById.get(subs[0]);
    const p2 = visiblePointById.get(subs[1]);
    if (!p1 || !p2 || isCovered(p1, p2)) continue;
    refRoot.add(
      buildReferenceSegmentNode(
        `quantity_span:${qty.id}`,
        qty.id,
        "QUANTITY_SPAN_REFERENCE",
        p1,
        p2,
        dashSize,
        false,
      ),
    );
    existingSpans.push([p1, p2]);
  }

  return refRoot.children.length > 0 ? refRoot : null;
}

// ── CHU TRÌNH ĐỈNH CHUẨN HÓA, ĐẠI SỐ HỮU TỈ CHÍNH XÁC, TRÌNH TỰ SƯ PHẠM & TOOLTIP ─────────────

export type Frac = readonly [bigint, bigint];
export type FracVec3 = readonly [Frac, Frac, Frac];

function gcdBig(a: bigint, b: bigint): bigint {
  let x = a < 0n ? -a : a;
  let y = b < 0n ? -b : b;
  while (y !== 0n) {
    const r = x % y;
    x = y;
    y = r;
  }
  return x === 0n ? 1n : x;
}

export function normFrac(num: bigint, den: bigint): Frac {
  if (den === 0n) return [0n, 1n];
  const sign = den < 0n ? -1n : 1n;
  const n = num * sign;
  const d = den * sign;
  if (n === 0n) return [0n, 1n];
  const g = gcdBig(n, d);
  return [n / g, d / g];
}

export function parseExactFrac(s: Exact): Frac {
  const m = /^(-?\d+)(?:\/(\d+))?$/.exec(String(s).trim());
  if (!m) return [0n, 1n];
  return normFrac(BigInt(m[1]), m[2] === undefined ? 1n : BigInt(m[2]));
}

export function fAdd(a: Frac, b: Frac): Frac {
  return normFrac(a[0] * b[1] + b[0] * a[1], a[1] * b[1]);
}
export function fSub(a: Frac, b: Frac): Frac {
  return normFrac(a[0] * b[1] - b[0] * a[1], a[1] * b[1]);
}
export function fMul(a: Frac, b: Frac): Frac {
  return normFrac(a[0] * b[0], a[1] * b[1]);
}
export function fEq(a: Frac, b: Frac): boolean {
  return a[0] === b[0] && a[1] === b[1];
}
export function fIsZero(a: Frac): boolean {
  return a[0] === 0n;
}

export function parseFracVec3(v: ExactVec3): FracVec3 {
  return [parseExactFrac(v[0]), parseExactFrac(v[1]), parseExactFrac(v[2])];
}

export function vSub(a: FracVec3, b: FracVec3): FracVec3 {
  return [fSub(a[0], b[0]), fSub(a[1], b[1]), fSub(a[2], b[2])];
}
export function vAdd(a: FracVec3, b: FracVec3): FracVec3 {
  return [fAdd(a[0], b[0]), fAdd(a[1], b[1]), fAdd(a[2], b[2])];
}
export function vIsZero(v: FracVec3): boolean {
  return fIsZero(v[0]) && fIsZero(v[1]) && fIsZero(v[2]);
}
export function vCross(a: FracVec3, b: FracVec3): FracVec3 {
  return [
    fSub(fMul(a[1], b[2]), fMul(a[2], b[1])),
    fSub(fMul(a[2], b[0]), fMul(a[0], b[2])),
    fSub(fMul(a[0], b[1]), fMul(a[1], b[0])),
  ];
}
export function vParallel(a: FracVec3, b: FracVec3): boolean {
  return !vIsZero(a) && !vIsZero(b) && vIsZero(vCross(a, b));
}

export function metricDot(u: FracVec3, v: FracVec3, chartMetric?: Exact[][]): Frac {
  if (!chartMetric || chartMetric.length !== 3) {
    return fAdd(fAdd(fMul(u[0], v[0]), fMul(u[1], v[1])), fMul(u[2], v[2]));
  }
  let acc: Frac = [0n, 1n];
  for (let i = 0; i < 3; i += 1) {
    for (let j = 0; j < 3; j += 1) {
      const gij = parseExactFrac(chartMetric[i]?.[j] ?? "0");
      acc = fAdd(acc, fMul(fMul(u[i], gij), v[j]));
    }
  }
  return acc;
}

export function fDiv(a: Frac, b: Frac): Frac {
  return normFrac(a[0] * b[1], a[1] * b[0]);
}

export function vScaleFrac(s: Frac, v: FracVec3): FracVec3 {
  return [fMul(s, v[0]), fMul(s, v[1]), fMul(s, v[2])];
}

function findRationalPlaneBasis(nVec: FracVec3): [FracVec3, FracVec3] | null {
  if (vIsZero(nVec)) return null;
  const axes: FracVec3[] = [
    [[1n, 1n], [0n, 1n], [0n, 1n]],
    [[0n, 1n], [1n, 1n], [0n, 1n]],
    [[0n, 1n], [0n, 1n], [1n, 1n]],
  ];
  for (const ax of axes) {
    const t1 = vCross(ax, nVec);
    if (!vIsZero(t1)) {
      const t2 = vCross(nVec, t1);
      if (!vIsZero(t2)) return [t1, t2];
    }
  }
  return null;
}

function projectPointOntoPlaneExact(
  pt: FracVec3,
  p0: FracVec3,
  nVec: FracVec3,
  chartMetric?: Exact[][],
): { foot: FracVec3; basis: [FracVec3, FracVec3] } | null {
  const basis = findRationalPlaneBasis(nVec);
  if (!basis) return null;
  const [u1, u2] = basis;
  const g11 = metricDot(u1, u1, chartMetric);
  const g12 = metricDot(u1, u2, chartMetric);
  const g22 = metricDot(u2, u2, chartMetric);
  const det = fSub(fMul(g11, g22), fMul(g12, g12));
  if (det[0] <= 0n) return null;
  const w = vSub(pt, p0);
  const b1 = metricDot(w, u1, chartMetric);
  const b2 = metricDot(w, u2, chartMetric);
  const alpha = fDiv(fSub(fMul(b1, g22), fMul(b2, g12)), det);
  const beta = fDiv(fSub(fMul(g11, b2), fMul(g12, b1)), det);
  const foot = vAdd(p0, vAdd(vScaleFrac(alpha, u1), vScaleFrac(beta, u2)));
  return { foot, basis };
}

function isExactMidpointVec(mid: ExactVec3, a: ExactVec3, b: ExactVec3): boolean {
  const m = parseFracVec3(mid);
  const sum = vAdd(parseFracVec3(a), parseFracVec3(b));
  const twoM: FracVec3 = [fMul([2n, 1n], m[0]), fMul([2n, 1n], m[1]), fMul([2n, 1n], m[2])];
  return fEq(twoM[0], sum[0]) && fEq(twoM[1], sum[1]) && fEq(twoM[2], sum[2]);
}

export { exactSceneOriginOf, registerExactSceneOrigin };

/**
 * Chuẩn hóa đại diện chu trình nhị diện D_n của một đa giác / thiết diện (`["N","M","Q","P"]` → `["M","N","P","Q"]`):
 * chỉ quay vòng và đổi chiều duyệt chu trình của Kernel, TUYỆT ĐỐI không đảo hai đỉnh không kề nhau.
 */
export function canonicalizeCycleNames(
  names: readonly string[],
  preferredOrder?: readonly string[],
): string[] {
  const n = names.length;
  if (n <= 2) return [...names];
  if (names.some((nm) => !nm || /^Đỉnh\s+\d+$/u.test(nm))) {
    return [...names];
  }
  const rankMap = new Map<string, number>();
  (preferredOrder ?? []).forEach((nm, idx) => {
    if (!rankMap.has(nm)) rankMap.set(nm, idx);
  });

  const compareToken = (a: string, b: string): number => {
    const ra = rankMap.get(a);
    const rb = rankMap.get(b);
    if (ra !== undefined && rb !== undefined && ra !== rb) return ra - rb;
    if (ra !== undefined && rb === undefined) return -1;
    if (ra === undefined && rb !== undefined) return 1;
    return a.localeCompare(b, "en");
  };

  const candidates: string[][] = [];
  const reversed = [...names].reverse();
  for (let shift = 0; shift < n; shift += 1) {
    candidates.push(Array.from({ length: n }, (_, k) => names[(shift + k) % n]));
    candidates.push(Array.from({ length: n }, (_, k) => reversed[(shift + k) % n]));
  }
  candidates.sort((ca, cb) => {
    for (let k = 0; k < n; k += 1) {
      const c = compareToken(ca[k], cb[k]);
      if (c !== 0) return c;
    }
    return 0;
  });
  return candidates[0];
}

export function formatCycleNotation(
  names: readonly string[],
  preferredOrder?: readonly string[],
): string | null {
  if (names.length < 3) return null;
  if (names.some((nm) => !nm || !isCompactPointSym(nm.trim()) || /^Đỉnh\s+\d+$/u.test(nm))) return null;
  const canon = canonicalizeCycleNames(names, preferredOrder);
  const compact = canon.every((t) => t.length <= 3) ? canon.join("") : canon.join("–");
  return `(${compact})`;
}

export function preferredPointOrderForPolygon(
  scene: Pick<Scene3D, "objects">,
  polyObj?: SceneObject | null,
): string[] {
  const order: string[] = [];
  const byId = new Map(scene.objects.map((o) => [o.id, o]));
  const planeDep = (polyObj?.depends ?? []).map((id) => byId.get(id)).find((o) => o?.type === "plane3");
  if (planeDep) {
    if (planeDep.notation) {
      const stripped = planeDep.notation.replace(/^[(\s]+|[)\s]+$/g, "");
      if (/^[A-Z][A-Z0-9′']*$/u.test(stripped)) {
        const tokens = stripped.match(/[A-Z][0-9′']*/gu) ?? [];
        for (const t of tokens) if (!order.includes(t)) order.push(t);
      }
    }
    for (const d of planeDep.depends ?? []) {
      const pt = byId.get(d);
      const tok = pt?.notation ?? pt?.reference;
      if (pt?.type === "point3" && tok && !order.includes(tok)) order.push(tok);
    }
  }
  for (const o of scene.objects) {
    if (o.type === "point3" && !isSubEntity(o.id)) {
      const tok = o.notation ?? o.reference;
      if (tok && !order.includes(tok)) order.push(tok);
    }
  }
  return order;
}

/**
 * Phân loại hình dạng chính xác của đa giác đồng phẳng trên Q^3 (tôn trọng `chart_metric` affine nếu có).
 * Không dùng số thực dấu phẩy động hay suy đoán từ hình chiếu.
 */
export function classifyExactPolygonShape(
  pts: readonly ExactVec3[],
  chartMetric?: Exact[][],
): string | null {
  const n = pts.length;
  if (n < 3) return null;
  const v = pts.map(parseFracVec3);
  const edges = v.map((cur, i) => vSub(v[(i + 1) % n], cur));
  const sqLens = edges.map((e) => metricDot(e, e, chartMetric));
  if (sqLens.some((l) => l[0] <= 0n)) return null;

  if (n === 3) {
    const [l0, l1, l2] = sqLens;
    const allEqual = fEq(l0, l1) && fEq(l1, l2);
    if (allEqual) return "tam giác đều";
    const right0 = fIsZero(metricDot(edges[2], edges[0], chartMetric));
    const right1 = fIsZero(metricDot(edges[0], edges[1], chartMetric));
    const right2 = fIsZero(metricDot(edges[1], edges[2], chartMetric));
    const hasRight = right0 || right1 || right2;
    const hasIso = fEq(l0, l1) || fEq(l1, l2) || fEq(l2, l0);
    if (hasRight && hasIso) return "tam giác vuông cân";
    if (hasRight) return "tam giác vuông";
    if (hasIso) return "tam giác cân";
    return "tam giác";
  }

  if (n === 4) {
    const opp02 = vIsZero(vAdd(edges[0], edges[2]));
    const opp13 = vIsZero(vAdd(edges[1], edges[3]));
    const right01 = fIsZero(metricDot(edges[0], edges[1], chartMetric));
    const eqAdj = fEq(sqLens[0], sqLens[1]);
    if (opp02 && opp13) {
      if (right01 && eqAdj) return "hình vuông";
      if (right01) return "hình chữ nhật";
      if (eqAdj) return "hình thoi";
      return "hình bình hành";
    }
    const par02 = vParallel(edges[0], edges[2]);
    const par13 = vParallel(edges[1], edges[3]);
    if (par02 !== par13) {
      const legEqual = par02 ? fEq(sqLens[1], sqLens[3]) : fEq(sqLens[0], sqLens[2]);
      const hasRight = par02
        ? (fIsZero(metricDot(edges[0], edges[1], chartMetric)) || fIsZero(metricDot(edges[0], edges[3], chartMetric)))
        : (fIsZero(metricDot(edges[1], edges[0], chartMetric)) || fIsZero(metricDot(edges[1], edges[2], chartMetric)));
      if (hasRight) return "hình thang vuông";
      if (legEqual) return "hình thang cân";
      return "hình thang";
    }
    return "tứ giác";
  }

  const allSidesEqual = sqLens.every((l) => fEq(l, sqLens[0]));
  const adjDots = edges.map((e, i) => metricDot(e, edges[(i + 1) % n], chartMetric));
  const allAnglesEqual = adjDots.every((d) => fEq(d, adjDots[0]));
  const turnVecs = edges.map((e, i) => vCross(e, edges[(i + 1) % n]));
  const strictlyConvexSameTurn =
    !vIsZero(turnVecs[0]) && turnVecs.every((tv) => !vIsZero(tv) && plainDotFrac(tv, turnVecs[0])[0] > 0n);
  const isRegularN = allSidesEqual && allAnglesEqual && strictlyConvexSameTurn;

  if (n === 5) return isRegularN ? "ngũ giác đều" : "ngũ giác";
  if (n === 6) return isRegularN ? "lục giác đều" : "lục giác";
  return isRegularN ? `đa giác đều ${n} cạnh` : `đa giác ${n} cạnh`;
}

export type SceneClaimProvenance =
  | "GIVEN"
  | "DERIVED_VERIFIED"
  | "CONSTRUCTED"
  | "ILLUSTRATIVE_CHOICE"
  | "UNVERIFIED"
  | "CONTRADICTORY_OR_UNSUPPORTED";

export interface PolygonShapeProvenanceResult {
  provenance: SceneClaimProvenance;
  certifiedShape: string | null;
  coordinateShape: string | null;
  weakerDeclared: string | null;
}

export function isLinePerpPlaneRelation(rel: string | undefined | null): boolean {
  return rel === "line_perp_plane" || rel === "line_perpendicular_plane";
}

const UNCERTIFIED_SOURCE_TOKENS = new Set([
  "LAYOUT_DERIVED",
  "ILLUSTRATIVE_CONFIGURATION",
  "ILLUSTRATIVE_CHOICE",
  "MODEL_ASSUMPTION",
  "UNVERIFIED",
]);

function isNonAuthoritativeNonFoundation(obj: SceneObject | undefined): boolean {
  if (!obj || obj.authoritative !== false) return false;
  const src = obj.source as Record<string, unknown> | undefined;
  return src?.instruction !== "PRESENTATION_CURVED_FOUNDATION";
}

function hasUncertifiedObjectSource(obj: SceneObject | undefined): boolean {
  const src = obj?.source as Record<string, unknown> | undefined;
  if (!src) return false;
  if (src.is_given === false) return true;
  if (src.binding === "AUXILIARY" || src.provenance === "DISPLAY_ONLY") return true;
  if (typeof src.provenance === "string" && UNCERTIFIED_SOURCE_TOKENS.has(src.provenance.trim())) return true;
  if (typeof src.assumption === "string" && UNCERTIFIED_SOURCE_TOKENS.has(src.assumption.trim())) return true;
  if (
    typeof src.assumption === "string"
    && src.assumption.trim().length > 0
    && src.assumption.trim() !== "hệ trục do đề chọn"
  ) {
    return true;
  }
  return false;
}

export function isCertifiedGivenSceneObject(
  scene: Pick<Scene3D, "objects"> & { free_objects?: string[] },
  obj: SceneObject | undefined,
): boolean {
  if (!obj) return false;
  if (obj.authoritative === false) return false;
  if (hasUncertifiedObjectSource(obj)) return false;
  if (hasContradictoryObjectProvenance(obj, true)) return false;
  const src = obj.source as Record<string, unknown> | undefined;
  if (obj.origin !== "free") return false;
  if (!isSubEntity(obj.id) && Array.isArray(scene.free_objects)) {
    const explicitGiven = src?.is_given === true || src?.provenance === "GIVEN" || Boolean(src?.fact_id);
    if (!explicitGiven && !scene.free_objects.includes(obj.id)) {
      return false;
    }
  }
  return true;
}

function hasContradictoryObjectProvenance(obj: SceneObject | undefined, disallowDerivedGiven = false): boolean {
  const src = obj?.source as Record<string, unknown> | undefined;
  if (!src) return false;
  const claimsGiven = src.is_given === true || src.provenance === "GIVEN";
  if (!claimsGiven) return false;
  if (disallowDerivedGiven && obj?.origin === "derived") return true;
  if (src.is_given === false) return true;
  if (typeof src.provenance === "string" && UNCERTIFIED_SOURCE_TOKENS.has(src.provenance.trim())) return true;
  if (typeof src.assumption === "string" && UNCERTIFIED_SOURCE_TOKENS.has(src.assumption.trim())) return true;
  return false;
}

function isUncertifiedPolygonSource(polyObj: SceneObject, hostSolid?: SceneObject): boolean {
  return hasUncertifiedObjectSource(polyObj) || hasUncertifiedObjectSource(hostSolid);
}

function declaredExactPolygonShape(polyObj: SceneObject, hostSolid?: SceneObject): string | null {
  const txt = `${polyObj.label ?? ""} ${polyObj.role ?? ""} ${hostSolid?.label ?? ""} ${hostSolid?.role ?? ""}`;
  if (/\bhình\s+vuông\b|\bchóp\s+tứ\s+giác\s+đều\b|\blăng\s+trụ\s+tứ\s+giác\s+đều\b/iu.test(txt)) return "hình vuông";
  if (/\btam\s+giác(?:\s+[A-Z0-9′']+)?\s+đều\b|\bchóp\s+tam\s+giác\s+đều\b|\blăng\s+trụ\s+tam\s+giác\s+đều\b/iu.test(txt)) {
    return "tam giác đều";
  }
  if (/\btam\s+giác(?:\s+[A-Z0-9′']+)?\s+vuông\s+cân\b/iu.test(txt)) return "tam giác vuông cân";
  if (/\bngũ\s+giác(?:\s+[A-Z0-9′']+)?\s+đều\b|\bchóp\s+ngũ\s+giác\s+đều\b|\blăng\s+trụ\s+ngũ\s+giác\s+đều\b/iu.test(txt)) {
    return "ngũ giác đều";
  }
  if (/\blục\s+giác(?:\s+[A-Z0-9′']+)?\s+đều\b|\bchóp\s+lục\s+giác\s+đều\b|\blăng\s+trụ\s+lục\s+giác\s+đều\b/iu.test(txt)) {
    return "lục giác đều";
  }
  return null;
}

function declaredWeakerPolygonShape(polyObj: SceneObject, hostSolid?: SceneObject): string | null {
  const txt = `${polyObj.label ?? ""} ${polyObj.role ?? ""} ${hostSolid?.label ?? ""} ${hostSolid?.role ?? ""}`;
  if (/\bhình\s+bình\s+hành\b/iu.test(txt)) return "hình bình hành";
  if (/\bhình\s+chữ\s+nhật\b/iu.test(txt)) return "hình chữ nhật";
  if (/\bhình\s+thoi\b/iu.test(txt)) return "hình thoi";
  if (/\bhình\s+thang(?:\s+[A-Z0-9′']+)?\s+vuông\b/iu.test(txt)) return "hình thang vuông";
  if (/\bhình\s+thang(?:\s+[A-Z0-9′']+)?\s+cân\b/iu.test(txt)) return "hình thang cân";
  if (/\bhình\s+thang\b/iu.test(txt)) return "hình thang";
  if (/\bđáy\b[^.;]*\blà\s+tứ\s+giác\b/iu.test(txt) && !/\btứ\s+giác\s+đều\b/iu.test(txt)) return "tứ giác";
  if (/^\s*tứ\s+giác\b/iu.test(polyObj.label ?? "") && !/\btứ\s+giác\s+đều\b/iu.test(polyObj.label ?? "")) return "tứ giác";
  if (/\btam\s+giác(?:\s+[A-Z0-9′']+)?\s+thường\b/iu.test(txt)) return "tam giác";
  if (/\btam\s+giác(?:\s+[A-Z0-9′']+)?\s+vuông\b/iu.test(txt) && !/\bvuông\s+cân\b/iu.test(txt)) return "tam giác vuông";
  if (/\btam\s+giác(?:\s+[A-Z0-9′']+)?\s+cân\b/iu.test(txt) && !/\bvuông\s+cân\b/iu.test(txt)) return "tam giác cân";
  return null;
}

function isCoordinateShapeConsistentWithWeakerDeclared(weaker: string, coordShape: string | null): boolean {
  if (!coordShape) return false;
  switch (weaker) {
    case "hình chữ nhật":
      return coordShape === "hình chữ nhật" || coordShape === "hình vuông";
    case "hình thoi":
      return coordShape === "hình thoi" || coordShape === "hình vuông";
    case "hình bình hành":
      return (
        coordShape === "hình bình hành"
        || coordShape === "hình chữ nhật"
        || coordShape === "hình thoi"
        || coordShape === "hình vuông"
      );
    case "hình thang vuông":
      return coordShape === "hình thang vuông" || coordShape === "hình chữ nhật" || coordShape === "hình vuông";
    case "hình thang cân":
      return coordShape === "hình thang cân" || coordShape === "hình chữ nhật" || coordShape === "hình vuông";
    case "hình thang":
      return (
        coordShape.startsWith("hình thang")
        || coordShape === "hình bình hành"
        || coordShape === "hình chữ nhật"
        || coordShape === "hình thoi"
        || coordShape === "hình vuông"
      );
    case "tứ giác":
      return !coordShape.startsWith("tam giác");
    case "tam giác vuông":
      return coordShape === "tam giác vuông" || coordShape === "tam giác vuông cân";
    case "tam giác cân":
      return coordShape === "tam giác cân" || coordShape === "tam giác đều" || coordShape === "tam giác vuông cân";
    case "tam giác":
      return coordShape.startsWith("tam giác");
    default:
      return true;
  }
}

function topologicalPolygonNoun(sideCount: number): string {
  if (sideCount === 3) return "tam giác";
  if (sideCount === 4) return "tứ giác";
  if (sideCount === 5) return "ngũ giác";
  if (sideCount === 6) return "lục giác";
  return `đa giác ${sideCount} cạnh`;
}

/**
 * Phân loại hình dạng đa giác kèm nguồn gốc ngữ nghĩa nội bộ (`SceneClaimProvenance`, §4.1–§4.3):
 * - Không bao giờ suy ra khẳng định toán học (`tam giác vuông cân`, `hình vuông`, `chóp đều`...) chỉ từ tọa độ
 *   minh họa (`LAYOUT_DERIVED` / thiếu bậc tự do metric khi không có `chart_metric` hoặc khai báo tường minh).
 * - Không sửa public schema `Scene3D`; chỉ phục vụ tầng phân tích ngữ nghĩa và hiển thị frontend.
 */
export function classifyPolygonShapeWithProvenance(
  rawScene: Pick<Scene3D, "objects" | "chart_metric">,
  rawPolyObj: SceneObject,
): PolygonShapeProvenanceResult {
  const exactScene = exactSceneOriginOf(rawScene);
  const polyObj =
    exactScene === rawScene
      ? rawPolyObj
      : (exactScene.objects.find((o) => o.id === rawPolyObj.id) ?? rawPolyObj);
  const pts = polyObj.polygon ?? polyObj.vertices ?? [];
  if (pts.length < 3) {
    return { provenance: "UNVERIFIED", certifiedShape: null, coordinateShape: null, weakerDeclared: null };
  }
  const byId = new Map(exactScene.objects.map((o) => [o.id, o]));
  const isBaseLike =
    polyObj.surface_role === "BASE_REGION" || (polyObj.formation_roles ?? []).includes("CONSTRUCT_BASE");
  const hostSolid = polyObj.id.endsWith("__base")
    ? exactScene.objects.find((o) => o.id === polyObj.id.slice(0, -"__base".length))
    : isBaseLike
      ? exactScene.objects.find((o) => o.type === "solid")
      : undefined;

  const gMetric = isSceneWorldTransformed(exactScene) ? undefined : exactScene.chart_metric;
  const coordinateShape = classifyExactPolygonShape(pts, gMetric);
  const declaredExact = declaredExactPolygonShape(polyObj, hostSolid);
  const weakerDeclared = declaredWeakerPolygonShape(polyObj, hostSolid);

  const vertIds = [...new Set([...(polyObj.vertex_ids ?? []), ...(polyObj.depends ?? [])])].filter(
    (id) => byId.get(id)?.type === "point3",
  );
  const vertIdSet = new Set(vertIds);

  // 1. Chặn ngay dữ liệu provenance mâu thuẫn nội tại (vd vừa đánh dấu GIVEN vừa gắn ILLUSTRATIVE_CONFIGURATION / derived)
  if (
    hasContradictoryObjectProvenance(polyObj, true)
    || hasContradictoryObjectProvenance(hostSolid, false)
    || vertIds.some((id) => hasContradictoryObjectProvenance(byId.get(id), true))
  ) {
    return {
      provenance: "CONTRADICTORY_OR_UNSUPPORTED",
      certifiedShape: null,
      coordinateShape,
      weakerDeclared,
    };
  }

  // 2. Đối chiếu `source_provenance` từ hợp đồng Hybrid (nếu có đính kèm trên scene)
  const hybridMeta = hybridViewOfScene(rawScene) ?? hybridViewOfScene(exactScene);
  if (hybridMeta?.source_provenance && hybridMeta.source_provenance.length > 0) {
    const polySyms = new Set(
      vertIds.map((id) => shortSym(byId.get(id))).filter((s): s is string => Boolean(s)),
    );
    const matchesPolyTarget = (tokens: readonly string[]): boolean => {
      if (tokens.includes(polyObj.id)) return true;
      const cleaned = tokens.map((t) => t.replace(/^[(\s]+|[)\s]+$/gu, "").trim()).filter(Boolean);
      if (polyObj.notation && cleaned.includes(polyObj.notation.replace(/^[(\s]+|[)\s]+$/gu, "").trim())) {
        return true;
      }
      if (cleaned.length === pts.length && cleaned.every((t) => vertIdSet.has(t) || polySyms.has(t))) {
        return new Set(cleaned).size === pts.length;
      }
      if (cleaned.length === 1 && polySyms.size === pts.length && pts.length >= 3) {
        const parts = cleaned[0].match(/[A-Z][0-9′']*/gu) ?? [];
        if (parts.length === pts.length && new Set(parts).size === pts.length && parts.every((p) => polySyms.has(p))) {
          return true;
        }
      }
      return false;
    };

    let spRightAngle = false;
    let spEqualSides = false;
    let spRightOrigin: string | undefined;
    let spEqualOrigin: string | undefined;

    for (const sp of hybridMeta.source_provenance) {
      if (sp.verified === false) continue;
      const spRec = sp as unknown as Record<string, unknown>;
      const hasSpQuotes = Array.isArray(spRec.quotes) && spRec.quotes.length > 0;
      if (sp.verified !== true && !hasSpQuotes) continue;
      const argsRec =
        spRec.args && typeof spRec.args === "object" && !Array.isArray(spRec.args)
          ? (spRec.args as Record<string, unknown>)
          : {};
      const strArr = (v: unknown): string[] =>
        Array.isArray(v) ? v.filter((x): x is string => typeof x === "string") : [];
      const optStr = (v: unknown): string[] => (typeof v === "string" && v.trim() ? [v.trim()] : []);
      const polyTokens = [
        ...strArr(spRec.polygon),
        ...strArr(spRec.points),
        ...strArr(spRec.plane),
        ...strArr(spRec.object_ids),
        ...strArr(spRec.subjects),
        ...strArr(argsRec.vertices),
        ...strArr(argsRec.polygon),
        ...strArr(argsRec.base),
      ];
      const angleTokens = [
        ...polyTokens,
        ...strArr(spRec.edge),
        ...optStr(spRec.line),
        ...strArr(argsRec.rays),
        ...optStr(argsRec.ray1),
        ...optStr(argsRec.ray2),
        ...strArr(argsRec.line1),
        ...strArr(argsRec.line2),
        ...optStr(argsRec.line1_ref),
        ...optStr(argsRec.line2_ref),
        ...optStr(spRec.vertex),
        ...optStr(argsRec.vertex),
        ...(Array.isArray(spRec.rays) ? spRec.rays.flatMap((r) => strArr(r)) : []),
      ];
      const eqSegTokens = [...strArr(argsRec.segment_a), ...strArr(argsRec.segment_b)];
      const spOrigin = typeof spRec.origin === "string" ? spRec.origin : undefined;
      const rawKind = typeof sp.fn === "string" && sp.fn.trim() ? sp.fn : (sp.kind ?? "");
      const kindNorm = rawKind.trim().toLowerCase();
      if (!kindNorm) continue;

      if ((kindNorm === "regular_polygon" || kindNorm === "square" || kindNorm === "equilateral_triangle") && matchesPolyTarget(polyTokens)) {
        const expected =
          kindNorm === "square"
            ? "hình vuông"
            : kindNorm === "equilateral_triangle"
              ? "tam giác đều"
              : pts.length === 3
                ? "tam giác đều"
                : pts.length === 4
                  ? "hình vuông"
                  : pts.length === 5
                    ? "ngũ giác đều"
                    : pts.length === 6
                      ? "lục giác đều"
                      : `đa giác đều ${pts.length} cạnh`;
        if (coordinateShape !== expected) {
          return { provenance: "CONTRADICTORY_OR_UNSUPPORTED", certifiedShape: null, coordinateShape, weakerDeclared };
        }
        return { provenance: spOrigin === "derived" ? "DERIVED_VERIFIED" : "GIVEN", certifiedShape: expected, coordinateShape, weakerDeclared };
      }
      const mappedWeaker =
        kindNorm === "rectangle"
          ? "hình chữ nhật"
          : kindNorm === "rhombus"
            ? "hình thoi"
            : kindNorm === "parallelogram"
              ? "hình bình hành"
              : kindNorm === "isosceles_triangle"
                ? "tam giác cân"
                : null;
      if (mappedWeaker && matchesPolyTarget(polyTokens)) {
        if (!isCoordinateShapeConsistentWithWeakerDeclared(mappedWeaker, coordinateShape)) {
          return { provenance: "CONTRADICTORY_OR_UNSUPPORTED", certifiedShape: null, coordinateShape, weakerDeclared };
        }
        return { provenance: spOrigin === "derived" ? "DERIVED_VERIFIED" : "GIVEN", certifiedShape: mappedWeaker, coordinateShape, weakerDeclared };
      }
      if (
        pts.length === 3
        && (kindNorm === "right_angle" || kindNorm === "right_triangle" || kindNorm === "line_perp_line" || kindNorm === "perpendicular_lines")
        && angleTokens.length > 0
      ) {
        const coveredVertSyms = new Set<string>();
        const allOperandsInPoly = angleTokens.every((t) => {
          const clean = t.replace(/^[(\s]+|[)\s]+$/gu, "").trim();
          if (!clean) return false;
          if (clean === polyObj.id) {
            for (const ps of polySyms) coveredVertSyms.add(ps);
            return true;
          }
          if (vertIdSet.has(clean)) {
            const vs = shortSym(byId.get(clean));
            if (vs && polySyms.has(vs)) coveredVertSyms.add(vs);
            return true;
          }
          if (polySyms.has(clean)) {
            coveredVertSyms.add(clean);
            return true;
          }
          const refObj = byId.get(clean);
          if (refObj && (refObj.type === "segment3" || refObj.type === "line3")) {
            const refDeps = (refObj.endpoint_ids ?? refObj.depends ?? []).filter((d) => byId.get(d)?.type === "point3");
            if (refDeps.length >= 2 && refDeps.every((d) => vertIdSet.has(d))) {
              for (const d of refDeps) {
                const vs = shortSym(byId.get(d));
                if (vs && polySyms.has(vs)) coveredVertSyms.add(vs);
              }
              return true;
            }
            return false;
          }
          const parts = clean.match(/[A-Z][0-9′']*/gu) ?? [];
          if (parts.length >= 2 && parts.join("") === clean && parts.every((p) => polySyms.has(p))) {
            for (const p of parts) coveredVertSyms.add(p);
            return true;
          }
          return false;
        });
        const spansAllThreeVertices =
          kindNorm === "right_triangle" ? matchesPolyTarget(polyTokens) : coveredVertSyms.size === 3;
        if (allOperandsInPoly && spansAllThreeVertices) {
          spRightAngle = true;
          spRightOrigin = spOrigin;
        }
      }
      if (
        pts.length === 3
        && kindNorm === "equal_length"
        && eqSegTokens.length === 4
        && eqSegTokens.every((t) => vertIdSet.has(t.trim()) || polySyms.has(t.trim()))
      ) {
        spEqualSides = true;
        spEqualOrigin = spOrigin;
      }
    }

    if (spRightAngle) {
      if (coordinateShape !== "tam giác vuông" && coordinateShape !== "tam giác vuông cân") {
        return { provenance: "CONTRADICTORY_OR_UNSUPPORTED", certifiedShape: null, coordinateShape, weakerDeclared };
      }
      const isRightIso =
        (spEqualSides || declaredExact === "tam giác vuông cân") && coordinateShape === "tam giác vuông cân";
      const triShape = isRightIso ? "tam giác vuông cân" : "tam giác vuông";
      const prov = spRightOrigin === "derived" || (isRightIso && spEqualOrigin === "derived") ? "DERIVED_VERIFIED" : "GIVEN";
      return { provenance: prov, certifiedShape: triShape, coordinateShape, weakerDeclared };
    }
    if (spEqualSides) {
      if (!isCoordinateShapeConsistentWithWeakerDeclared("tam giác cân", coordinateShape)) {
        return { provenance: "CONTRADICTORY_OR_UNSUPPORTED", certifiedShape: null, coordinateShape, weakerDeclared };
      }
      return {
        provenance: spEqualOrigin === "derived" ? "DERIVED_VERIFIED" : "GIVEN",
        certifiedShape: "tam giác cân",
        coordinateShape,
        weakerDeclared,
      };
    }
  }

  // 3. Khai báo hình dạng tường minh từ nhãn/vai trò hợp đồng
  if (declaredExact) {
    if (coordinateShape !== declaredExact) {
      return {
        provenance: "CONTRADICTORY_OR_UNSUPPORTED",
        certifiedShape: null,
        coordinateShape,
        weakerDeclared,
      };
    }
    if (!isUncertifiedPolygonSource(polyObj, hostSolid)) {
      return {
        provenance: "GIVEN",
        certifiedShape: declaredExact,
        coordinateShape,
        weakerDeclared,
      };
    }
  }

  if (weakerDeclared && !isCoordinateShapeConsistentWithWeakerDeclared(weakerDeclared, coordinateShape)) {
    return {
      provenance: "CONTRADICTORY_OR_UNSUPPORTED",
      certifiedShape: null,
      coordinateShape,
      weakerDeclared,
    };
  }

  if (isUncertifiedPolygonSource(polyObj, hostSolid)) {
    return {
      provenance: "ILLUSTRATIVE_CHOICE",
      certifiedShape: null,
      coordinateShape,
      weakerDeclared,
    };
  }

  if (weakerDeclared) {
    return {
      provenance: isBaseLike ? "GIVEN" : polyObj.origin === "derived" ? "DERIVED_VERIFIED" : "GIVEN",
      certifiedShape: weakerDeclared,
      coordinateShape,
      weakerDeclared,
    };
  }

  // 4. Nhân chứng vuông góc phẳng (`perpendicular_witness`) do Backend chứng nhận tại đúng một ĐỈNH của tam giác giữa hai cạnh kề
  if (pts.length === 3 && vertIds.length === 3) {
    const inPlaneRightWitness = exactScene.objects.find((o) => {
      if (hasUncertifiedObjectSource(o) || hasContradictoryObjectProvenance(o, true)) return false;
      const w = o.perpendicular_witness ?? o.annotation?.witness;
      if (!w || isLinePerpPlaneRelation(w.relation)) return false;
      const wRec = w as unknown as Record<string, unknown>;
      if (wRec.status === "UNVERIFIED" || wRec.can_present_as_proven === false) return false;
      const footXyz = w.foot ?? (w.foot_id ? byId.get(w.foot_id)?.xyz : undefined);
      if (!footXyz) return false;
      const footVec = parseFracVec3(footXyz);
      const vFootId = vertIds.find((vid) => {
        if (w.foot_id && w.foot_id === vid) return true;
        const vp = byId.get(vid);
        return Boolean(vp?.xyz && vIsZero(vSub(parseFracVec3(vp.xyz), footVec)));
      });
      // Chân đường cao hạ xuống điểm trong/ngoài cạnh đối diện (vd H = proj(A, BC) ≠ B, C) KHÔNG phải góc vuông của tam giác!
      if (!vFootId) return false;
      const otherPolyVertexOf = (refId: string | undefined): string | null => {
        if (!refId) return null;
        if (vertIdSet.has(refId)) return refId !== vFootId ? refId : null;
        const refObj = byId.get(refId);
        if (!refObj || (refObj.type !== "segment3" && refObj.type !== "line3")) return null;
        const epPts = [...new Set([...(refObj.endpoint_ids ?? []), ...(refObj.depends ?? [])])].filter(
          (id) => byId.get(id)?.type === "point3",
        );
        if (epPts.length !== 2 || !epPts.includes(vFootId) || !epPts.every((id) => vertIdSet.has(id))) {
          return null;
        }
        return epPts.find((id) => id !== vFootId) ?? null;
      };
      const vFromOther = otherPolyVertexOf(w.from);
      const vOnOther = otherPolyVertexOf(w.on);
      return Boolean(vFromOther && vOnOther && vFromOther !== vOnOther);
    });
    if (inPlaneRightWitness) {
      if (coordinateShape !== "tam giác vuông" && coordinateShape !== "tam giác vuông cân") {
        return {
          provenance: "CONTRADICTORY_OR_UNSUPPORTED",
          certifiedShape: null,
          coordinateShape,
          weakerDeclared,
        };
      }
      const wObj = (inPlaneRightWitness.perpendicular_witness ?? inPlaneRightWitness.annotation?.witness) as unknown as
        | Record<string, unknown>
        | undefined;
      const isGivenW =
        wObj?.status === "GIVEN"
        || (inPlaneRightWitness.source as Record<string, unknown> | undefined)?.provenance === "GIVEN"
        || isCertifiedGivenSceneObject(exactScene, inPlaneRightWitness);
      return {
        provenance: isGivenW ? "GIVEN" : "DERIVED_VERIFIED",
        certifiedShape: "tam giác vuông",
        coordinateShape,
        weakerDeclared,
      };
    }
  }

  // 5. Đa giác thiết diện suy dẫn (`section` / `polygon3` vai trò `section`): chỉ nhận kết luận khi đủ tiền đề đã chứng nhận
  if (
    !isBaseLike
    && polyObj.origin === "derived"
    && (polyObj.type === "section" || vaiTroMien(polyObj) === "section")
  ) {
    const basis = deriveExactPolygonMathBasis(exactScene as Scene3D, polyObj);
    if (basis?.shape && basis.epistemicLevel === "DERIVED" && basis.shape !== topologicalPolygonNoun(pts.length)) {
      return {
        provenance: "DERIVED_VERIFIED",
        certifiedShape: basis.shape,
        coordinateShape,
        weakerDeclared,
      };
    }
  }

  // 6. Tuyệt đối KHÔNG suy ra hình dạng đặc biệt từ tọa độ bố cục hoặc `chart_metric` đơn lẻ,
  // và KHÔNG tự đo lại ba cạnh để nâng cấp lên `DERIVED_VERIFIED` khi thiếu chứng chỉ từ Backend (§3.2).
  const anyExplicitUnverified = [polyObj, hostSolid, ...vertIds.map((id) => byId.get(id))].some((obj) => {
    const src = obj?.source as Record<string, unknown> | undefined;
    return src?.provenance === "UNVERIFIED" || src?.assumption === "UNVERIFIED";
  });
  if (anyExplicitUnverified) {
    return { provenance: "UNVERIFIED", certifiedShape: null, coordinateShape, weakerDeclared };
  }
  const anyVertexUncertified = vertIds.some((id) => hasUncertifiedObjectSource(byId.get(id)));
  if (anyVertexUncertified) {
    return { provenance: "ILLUSTRATIVE_CHOICE", certifiedShape: null, coordinateShape, weakerDeclared };
  }
  if (!isBaseLike && polyObj.origin === "derived") {
    return { provenance: "CONSTRUCTED", certifiedShape: null, coordinateShape, weakerDeclared };
  }
  return {
    provenance: "UNVERIFIED",
    certifiedShape: null,
    coordinateShape,
    weakerDeclared,
  };
}

export function classifyScenePolygonShape(
  rawScene: Pick<Scene3D, "objects" | "chart_metric">,
  rawPolyObj: SceneObject,
): string | null {
  const exactScene = exactSceneOriginOf(rawScene);
  const polyObj =
    exactScene === rawScene
      ? rawPolyObj
      : (exactScene.objects.find((o) => o.id === rawPolyObj.id) ?? rawPolyObj);
  const pts = polyObj.polygon ?? polyObj.vertices ?? [];
  if (pts.length < 3) return null;
  const res = classifyPolygonShapeWithProvenance(rawScene, rawPolyObj);
  if (res.certifiedShape) return res.certifiedShape;
  return topologicalPolygonNoun(pts.length);
}

function structuralApexSymsOfScene(scene: Pick<Scene3D, "objects">): Set<string> {
  const exactScene = exactSceneOriginOf(scene);
  const byId = new Map(exactScene.objects.map((o) => [o.id, o]));
  const baseVertIds = new Set<string>();
  for (const o of exactScene.objects) {
    if (isSubEntity(o.id)) continue;
    if (
      (o.surface_role === "BASE_REGION" || (o.formation_roles ?? []).includes("CONSTRUCT_BASE"))
      && !(o.formation_roles ?? []).includes("CONSTRUCT_TRANSLATED_FACE")
      && !isPolyhedronLateralOrAuxFacePolygon(exactScene, o)
    ) {
      for (const vid of [...(o.vertex_ids ?? []), ...(o.depends ?? [])]) baseVertIds.add(vid);
    }
  }
  const apexSyms = new Set<string>();
  for (const o of exactScene.objects) {
    if (o.type === "solid" && o.shape_class !== "PRISM_LIKE") {
      if (baseVertIds.size > 0) {
        const candIds = (o.vertex_ids ?? o.depends ?? []).filter((vid) => !baseVertIds.has(vid));
        if (candIds.length === 1) {
          const ap = byId.get(candIds[0]);
          if (ap?.type === "point3" && isCompactPointSym(shortSym(ap))) apexSyms.add(shortSym(ap));
        }
      } else if (o.vertex_ids && o.faces) {
        const nonTriFaces = o.faces.filter((f) => f.length >= 4);
        const triFaces = o.faces.filter((f) => f.length === 3);
        if (nonTriFaces.length === 1 && triFaces.length === o.faces.length - 1) {
          const baseFaceIds = new Set(nonTriFaces[0].map((idx) => o.vertex_ids![idx]));
          const candIds = o.vertex_ids.filter((vid) => !baseFaceIds.has(vid));
          if (candIds.length === 1) {
            const ap = byId.get(candIds[0]);
            if (ap?.type === "point3" && isCompactPointSym(shortSym(ap))) apexSyms.add(shortSym(ap));
          }
        }
      }
    } else if (o.type === "curved_solid" && o.curved_kind === "cone" && o.apex_or_top) {
      const topVec = parseFracVec3(o.apex_or_top);
      const ap = exactScene.objects.find(
        (p) => !isSubEntity(p.id) && p.type === "point3" && p.xyz && vIsZero(vSub(parseFracVec3(p.xyz), topVec)),
      );
      if (ap && isCompactPointSym(shortSym(ap))) apexSyms.add(shortSym(ap));
    }
  }
  if (apexSyms.size === 0) {
    const perpFromSyms = new Set<string>();
    for (const o of exactScene.objects) {
      if (isSubEntity(o.id)) continue;
      const w = o.perpendicular_witness ?? o.annotation?.witness;
      if (!w || !isLinePerpPlaneRelation(w.relation) || !w.from) continue;
      const fromPt = byId.get(w.from);
      if (fromPt?.type === "point3" && isCompactPointSym(shortSym(fromPt))) {
        perpFromSyms.add(shortSym(fromPt));
      }
    }
    if (perpFromSyms.size === 1) {
      for (const s of perpFromSyms) apexSyms.add(s);
    }
  }
  return apexSyms;
}

/**
 * Tập các `point3` tự do (`origin === "free"`) CHƯA tham gia vào bất kỳ đối tượng hình học nào đang hiện ở bước `step`
 * (ví dụ đỉnh `S` ở bước 1 khi mới dựng đáy `ABCD`, chưa dựng đường cao `SA`).
 * Không áp dụng ở bước `INIT` rỗng hoặc cảnh chỉ có các điểm rời.
 */
export function ungroundedFreePointIdsAt(scene: Scene3D, step: number): Set<string> {
  const k = clampStep(scene, step);
  const present = objectsAt(scene, k);
  const nonPointVisualPresent = present.filter(
    (o) => o.type !== "point3" && o.render !== "readout" && o.render !== "non_visual" && !isSubEntity(o.id),
  );
  if (nonPointVisualPresent.length === 0) return new Set();

  const referencedAnywhere = new Set<string>();
  for (const o of scene.objects) {
    if (o.type === "point3" || o.render === "readout" || o.render === "non_visual" || isSubEntity(o.id)) continue;
    for (const id of [...(o.depends ?? []), ...(o.vertex_ids ?? []), ...(o.endpoint_ids ?? [])]) {
      referencedAnywhere.add(id);
    }
  }

  const groundedNow = new Set<string>();
  for (const o of nonPointVisualPresent) {
    for (const id of [...(o.depends ?? []), ...(o.vertex_ids ?? []), ...(o.endpoint_ids ?? [])]) {
      groundedNow.add(id);
    }
  }
  const snap = scene.formation?.steps[k];
  for (const id of snap?.focus_ids ?? []) groundedNow.add(id);
  for (const ev of scene.events) {
    if (ev.step_index > k || ev.action === "INIT") continue;
    if (ev.object) groundedNow.add(ev.object);
    for (const id of ev.objects ?? []) groundedNow.add(id);
  }

  const out = new Set<string>();
  for (const o of present) {
    if (o.type === "point3" && o.origin === "free" && referencedAnywhere.has(o.id) && !groundedNow.has(o.id)) {
      out.add(o.id);
    }
  }
  return out;
}

export type EpistemicConclusionLevel =
  | "GIVEN"
  | "DERIVED"
  | "COORDINATE_CONFIGURATION_ONLY"
  | "INSUFFICIENT_PREMISES";

export type PedagogicalEpistemicCategory =
  | "given"
  | "derived"
  | "constructed"
  | "auxiliary"
  | "conclusion";

export type PedagogicalStepRole =
  | "identify_given"
  | "construct_geometry"
  | "identify_auxiliary"
  | "deduce_relation"
  | "construct_intersection_or_section"
  | "emphasize_result"
  | "conclude_and_calculate";

export interface PedagogicalStepItem {
  index: number;
  startAnchor: number;
  anchor: number;
  label: string;
  title: string;
  subtitle: string;
  /** Các đối tượng được tạo hoặc được nhấn mạnh tại bước này. */
  targetIds: string[];
  /** Các đối tượng tiên quyết bắt buộc phải tồn tại trước bước này. */
  prerequisiteIds: string[];
  /** Tên thao tác dựng hình sư phạm. */
  operation: string;
  /** Tiền đề / quan hệ toán học cho phép thực hiện bước dựng. */
  premise: string;
  /** Tập đối tượng hữu hình hiện diện tại thời điểm kết thúc bước này. */
  visibleIds: string[];
  /** Phân loại nhận thức của bước: đề cho / được suy ra / được dựng / hình phụ. */
  epistemicCategory: PedagogicalEpistemicCategory;
  /** Nhãn tiếng Việt tương ứng với phân loại nhận thức. */
  categoryLabel: string;
  /** Vai trò bước dựng chi tiết theo đặc tả sư phạm. */
  stepRole: PedagogicalStepRole;
  /** Nhãn tiếng Việt của vai trò bước dựng. */
  stepRoleLabel: string;
  /** Nguồn gốc nhận thức toán học chuẩn hóa của bước dựng. */
  provenance: CanonicalMathProvenance;
  /** Thuyết minh sư phạm 3 phần (Hành động dựng · Giải thích ngắn · Chứng cứ đầy đủ). */
  narration?: PedagogicalStepNarration;
}

export interface PedagogicalStepNarration {
  actionTitle: string;
  conciseRationale: string;
  detailedEvidence: string[];
}

export function shortSym(o: SceneObject | undefined): string {
  if (!o) return "";
  const explicit = o.notation?.trim() || o.reference?.trim() || o.display_label?.trim();
  if (explicit) return explicit;
  const lbl = (o.label ?? "").trim();
  if (o.type === "point3") {
    const m = lbl.match(/^(?:Điểm|Giao\s+điểm|Trung\s+điểm|Trọng\s+tâm|Tâm|Đỉnh)\s+([A-Z][0-9′']*)\.?$/u);
    if (m) return m[1].replace(/'+/gu, "′");
    const isUnnamedAuxiliaryOrIntersection =
      o.role === "Điểm dựng phụ"
      || lbl === "Điểm dựng phụ"
      || /^Giao\s+điểm\s+của\b/iu.test(lbl)
      || o.authoritative === false;
    if (!isUnnamedAuxiliaryOrIntersection && /\s/u.test(lbl) && !isSubEntity(o.id) && /^[A-Z](?:_prime|'+)?$/u.test(o.id)) {
      return o.id.replace(/_prime$/u, "′").replace(/'+/gu, "′");
    }
  }
  return lbl;
}

function findPolygonDiagonalIntersectionRelation(
  scene: Pick<Scene3D, "objects">,
  ptObj: SceneObject,
  options?: { allowHeightFoot?: boolean },
): {
  aId: string;
  bId: string;
  cId: string;
  dId: string;
  aSym: string;
  bSym: string;
  cSym: string;
  dSym: string;
  d1Sym: string;
  d2Sym: string;
  polySym: string | null;
} | null {
  if (ptObj.type !== "point3") return null;
  if (ptObj.origin !== "derived") {
    const isHeightFoot =
      options?.allowHeightFoot === true
      && scene.objects.some(
        (s) =>
          s.perpendicular_witness?.foot_id === ptObj.id
          || ((s.formation_roles ?? []).includes("CONSTRUCT_HEIGHT")
            && (s.endpoint_ids ?? s.depends ?? []).includes(ptObj.id)),
      );
    if (!isHeightFoot) return null;
  }
  const exactScene = exactSceneOriginOf(scene);
  const exactById = new Map(exactScene.objects.map((o) => [o.id, o]));
  const byId = new Map(scene.objects.map((o) => [o.id, o]));
  const exPt = exactById.get(ptObj.id) ?? ptObj;
  if (!exPt.xyz) return null;
  const xO = parseFracVec3(exPt.xyz);

  const quadCycles: { ids: [string, string, string, string]; polySym: string | null }[] = [];
  for (const o of scene.objects) {
    if (isSubEntity(o.id)) continue;
    if (o.type === "polygon3") {
      const vIds = (o.vertex_ids && o.vertex_ids.length === 4 ? o.vertex_ids : o.depends?.length === 4 ? o.depends : null);
      if (vIds && vIds.every((id) => byId.get(id)?.type === "point3")) {
        const syms = vIds.map((id) => shortSym(byId.get(id)));
        quadCycles.push({
          ids: [vIds[0], vIds[1], vIds[2], vIds[3]],
          polySym: syms.every(isCompactPointSym) ? syms.join("") : null,
        });
      }
    } else if (o.type === "solid" && o.vertex_ids && o.faces) {
      for (const f of o.faces) {
        if (f.length !== 4) continue;
        const vIds = f.map((idx) => o.vertex_ids![idx]);
        if (vIds.every((id) => Boolean(id && byId.get(id)?.type === "point3"))) {
          const syms = vIds.map((id) => shortSym(byId.get(id)));
          quadCycles.push({
            ids: [vIds[0], vIds[1], vIds[2], vIds[3]],
            polySym: syms.every(isCompactPointSym) ? syms.join("") : null,
          });
        }
      }
    }
  }

  for (const cand of quadCycles) {
    if (cand.ids.includes(ptObj.id)) continue;
    const pts = cand.ids.map((id) => {
      const disp = byId.get(id);
      const ex = exactById.get(id) ?? disp;
      return disp && ex?.xyz ? { id, sym: shortSym(disp), xyz: parseFracVec3(ex.xyz) } : null;
    });
    if (pts.some((p) => !p || !isCompactPointSym(p.sym))) continue;
    const [p0, p1, p2, p3] = pts as NonNullable<(typeof pts)[number]>[];
    const diag1 = vSub(p2.xyz, p0.xyz);
    const diag2 = vSub(p3.xyz, p1.xyz);
    if (vIsZero(vCross(diag1, diag2))) continue;
    const onD1 =
      vIsZero(vCross(vSub(xO, p0.xyz), diag1))
      && plainDotFrac(vSub(xO, p0.xyz), vSub(xO, p2.xyz))[0] < 0n;
    const onD2 =
      vIsZero(vCross(vSub(xO, p1.xyz), diag2))
      && plainDotFrac(vSub(xO, p1.xyz), vSub(xO, p3.xyz))[0] < 0n;
    if (onD1 && onD2) {
      return {
        aId: p0.id,
        bId: p1.id,
        cId: p2.id,
        dId: p3.id,
        aSym: p0.sym,
        bSym: p1.sym,
        cSym: p2.sym,
        dSym: p3.sym,
        d1Sym: `${p0.sym}${p2.sym}`,
        d2Sym: `${p1.sym}${p3.sym}`,
        polySym: cand.polySym,
      };
    }
  }
  return null;
}

export function plainDotFrac(a: FracVec3, b: FracVec3): Frac {
  return fAdd(fAdd(fMul(a[0], b[0]), fMul(a[1], b[1])), fMul(a[2], b[2]));
}

export function fmtFrac(f: Frac): string {
  return f[1] === 1n ? f[0].toString() : `${f[0].toString()}/${f[1].toString()}`;
}

export function isCompactPointSym(s: string): boolean {
  return Boolean(s) && s.length <= 5 && !/\s/u.test(s);
}

export function findPointMidpointRelation(
  scene: Pick<Scene3D, "objects">,
  ptObj: SceneObject,
): { kind: "midpoint" | "symmetric" | "ratio"; aSym: string; bSym: string; centerSym?: string; ratioFrac?: Frac } | null {
  if (ptObj.type !== "point3" || !ptObj.xyz) return null;
  const exactScene = exactSceneOriginOf(scene);
  const byId = new Map(scene.objects.map((o) => [o.id, o]));
  const exactById = new Map(exactScene.objects.map((o) => [o.id, o]));
  const exactPt = exactById.get(ptObj.id) ?? ptObj;
  if (!exactPt.xyz) return null;
  const ptDeps = (exactPt.depends ?? ptObj.depends ?? [])
    .map((id) => exactById.get(id) ?? byId.get(id))
    .filter((o): o is SceneObject => Boolean(o && o.type === "point3" && o.xyz));
  if (ptDeps.length === 2) {
    const [pA, pB] = ptDeps;
    const dispA = byId.get(pA.id) ?? pA;
    const dispB = byId.get(pB.id) ?? pB;
    const dispPt = byId.get(ptObj.id) ?? ptObj;
    const aSym = shortSym(dispA);
    const bSym = shortSym(dispB);
    if (!isCompactPointSym(aSym) || !isCompactPointSym(bSym)) return null;
    const apexSyms = structuralApexSymsOfScene(exactScene);
    const preferA = apexSyms.has(aSym) && !apexSyms.has(bSym);
    const preferB = apexSyms.has(bSym) && !apexSyms.has(aSym);
    if (isExactMidpointVec(exactPt.xyz, pA.xyz!, pB.xyz!)) {
      const first = preferA ? aSym : preferB ? bSym : aSym;
      const second = first === aSym ? bSym : aSym;
      return { kind: "midpoint", aSym: first, bSym: second };
    }
    if (isExactMidpointVec(pA.xyz!, exactPt.xyz, pB.xyz!)) {
      return { kind: "symmetric", aSym: bSym, bSym: shortSym(dispPt), centerSym: aSym };
    }
    if (isExactMidpointVec(pB.xyz!, exactPt.xyz, pA.xyz!)) {
      return { kind: "symmetric", aSym, bSym: shortSym(dispPt), centerSym: bSym };
    }
    const firstObj = preferA ? pA : preferB ? pB : pA;
    const secondObj = firstObj === pA ? pB : pA;
    const firstSym = firstObj === pA ? aSym : bSym;
    const secondSym = firstObj === pA ? bSym : aSym;
    const tFrac = exactCollinearParam(exactPt.xyz, firstObj.xyz!, secondObj.xyz!);
    if (tFrac && !fIsZero(tFrac) && !fEq(tFrac, [1n, 1n])) {
      return {
        kind: "ratio",
        aSym: firstSym,
        bSym: secondSym,
        ratioFrac: tFrac,
      };
    }
  }
  return null;
}

export function findPointCentroidRelation(
  scene: Pick<Scene3D, "objects">,
  ptObj: SceneObject,
): {
  vertexSyms: [string, string, string];
  constructionMode: "three_vertices" | "median_ratio";
  medianVertexId?: string;
  medianVertexSym?: string;
  oppositeEdgeSyms?: [string, string];
  helperMidpointId?: string;
} | null {
  if (ptObj.type !== "point3" || !ptObj.xyz) return null;
  const exactScene = exactSceneOriginOf(scene);
  const apexSyms = structuralApexSymsOfScene(exactScene);
  const byId = new Map(exactScene.objects.map((o) => [o.id, o]));
  const exactPt = byId.get(ptObj.id) ?? ptObj;
  if (!exactPt.xyz) return null;
  const ptDeps = (exactPt.depends ?? [])
    .map((id) => byId.get(id))
    .filter((o): o is SceneObject => Boolean(o && o.type === "point3" && o.xyz));
  if (ptDeps.length === 3) {
    const syms = ptDeps.map((p) => shortSym(p));
    if (syms.every(isCompactPointSym)) {
      const g = parseFracVec3(exactPt.xyz);
      const sum3 = vAdd(vAdd(parseFracVec3(ptDeps[0].xyz!), parseFracVec3(ptDeps[1].xyz!)), parseFracVec3(ptDeps[2].xyz!));
      const threeG: FracVec3 = [fMul([3n, 1n], g[0]), fMul([3n, 1n], g[1]), fMul([3n, 1n], g[2])];
      if (fEq(threeG[0], sum3[0]) && fEq(threeG[1], sum3[1]) && fEq(threeG[2], sum3[2])) {
        const sorted = [...syms].sort((x, y) => {
          if (apexSyms.has(x) && !apexSyms.has(y)) return -1;
          if (apexSyms.has(y) && !apexSyms.has(x)) return 1;
          return x.localeCompare(y, "en");
        }) as [string, string, string];
        return { vertexSyms: sorted, constructionMode: "three_vertices" };
      }
    }
  }
  if (ptDeps.length < 2) return null;

  const candidatePairs: [SceneObject, SceneObject][] = [];
  for (let i = 0; i < ptDeps.length; i += 1) {
    for (let j = 0; j < ptDeps.length; j += 1) {
      if (i !== j) candidatePairs.push([ptDeps[i], ptDeps[j]]);
    }
  }

  for (const [pVert, pMid] of candidatePairs) {
    const vSym = shortSym(pVert);
    if (!isCompactPointSym(vSym)) continue;
    const midDeps = (pMid.depends ?? [])
      .map((id) => byId.get(id))
      .filter((o): o is SceneObject => Boolean(o && o.type === "point3" && o.xyz));
    if (midDeps.length !== 2) continue;
    const [pB, pC] = midDeps;
    const bSym = shortSym(pB);
    const cSym = shortSym(pC);
    if (!isCompactPointSym(bSym) || !isCompactPointSym(cSym)) continue;
    if (!isExactMidpointVec(pMid.xyz!, pB.xyz!, pC.xyz!)) continue;
    const g = parseFracVec3(exactPt.xyz);
    const sum3 = vAdd(vAdd(parseFracVec3(pVert.xyz!), parseFracVec3(pB.xyz!)), parseFracVec3(pC.xyz!));
    const threeG: FracVec3 = [fMul([3n, 1n], g[0]), fMul([3n, 1n], g[1]), fMul([3n, 1n], g[2])];
    if (fEq(threeG[0], sum3[0]) && fEq(threeG[1], sum3[1]) && fEq(threeG[2], sum3[2])) {
      const sorted = [vSym, bSym, cSym].sort((x, y) => {
        if (apexSyms.has(x) && !apexSyms.has(y)) return -1;
        if (apexSyms.has(y) && !apexSyms.has(x)) return 1;
        return x.localeCompare(y, "en");
      }) as [string, string, string];
      const oppSorted = [bSym, cSym].sort((x, y) => x.localeCompare(y, "en")) as [string, string];
      return {
        vertexSyms: sorted,
        constructionMode: "median_ratio",
        medianVertexId: pVert.id,
        medianVertexSym: vSym,
        oppositeEdgeSyms: oppSorted,
        ...(!pMid.notation ? { helperMidpointId: pMid.id } : {}),
      };
    }
  }
  return null;
}

export interface ResolvedLineDisplaySpan {
  endpoints: [Vec3, Vec3] | null;
  mode: "clamped_segment" | "endpoint_coincident" | "extended_ray" | "no_intersection" | "infinite_line";
  coreSegment?: [Vec3, Vec3] | null;
  basePointIds?: [string, string];
  tRange?: [number, number];
  coincidentEndpointId?: string;
  extensionDirection?: "before_start" | "after_end" | "both";
}

/**
 * Quyết định phần hiển thị của một `line3` dựa trên vai trò ngữ nghĩa và vị trí các điểm trên đường:
 * - Đường giao tuyến hoặc đường thẳng không gian chính (`target`) giữ phần kéo dài vô hạn để phân biệt với đoạn thẳng.
 * - Đường phụ mang 2 điểm (`origin === "derived"`, `CONSTRUCT_AUXILIARY_GEOMETRY`, phụ thuộc đúng 2 `point3`):
 *   + Nếu mọi điểm/chân vuông góc đang hiện trên đường đều nằm trong đoạn `[A, B]` (`0 < t < 1`) ⇒ kẹp đúng `[A, B]`
 *     (`clamped_segment`), không sinh đầu thừa giả ngoài `A` hoặc `B` (vd `Q ∈ SD` ở bước dựng thiết diện).
 *   + Nếu giao điểm trùng đúng đầu mút `A` hoặc `B` (`t = 0` hoặc `t = 1`) ⇒ không kéo dài (`clamped_segment` kèm
 *     `coincidentEndpointId` để truy vết rõ ràng).
 *   + Nếu có giao điểm/chân vuông góc hợp lệ nằm ngoài `[A, B]` (`t < 0` hoặc `t > 1`) ⇒ chỉ kéo dài đúng đầu cần thiết
 *     theo phương và phía của giao điểm (`extended_ray`), đầu còn lại giữ đúng mút của đoạn.
 *   + Nếu đường phụ dùng để tìm giao điểm với một mặt phẳng song song nó (không có giao điểm hợp lệ) ⇒ trả `no_intersection`.
 */
export function resolveLineDisplaySpan(
  scene: Pick<Scene3D, "objects">,
  lineObj: SceneObject,
  visibleObjects?: readonly SceneObject[],
  overridePointsForLine?: readonly Vec3[],
): ResolvedLineDisplaySpan {
  const visObjs = (visibleObjects ? [...visibleObjects] : [...scene.objects]) as SceneObject[];
  const ptsForLine = overridePointsForLine ? [...overridePointsForLine] : diemChoDuong(visObjs, lineObj.id);
  if (
    (lineObj.type !== "line3" && lineObj.render !== "line")
    || !lineObj.point
    || !lineObj.direction
  ) {
    return { endpoints: null, mode: "infinite_line" };
  }

  const roles = lineObj.formation_roles ?? [];
  const isAuxTwoPointCarrier =
    lineObj.origin === "derived"
    && roles.includes("CONSTRUCT_AUXILIARY_GEOMETRY")
    && !isIntersectionLineOrSegment(lineObj, scene)
    && !isPrimarySpatialLine(lineObj, scene)
    && (lineObj.depends ?? []).length === 2;

  if (isAuxTwoPointCarrier) {
    const exactScene = exactSceneOriginOf(scene);
    const exactById = new Map(exactScene.objects.map((o) => [o.id, o]));
    const exactLineObj = exactById.get(lineObj.id) ?? lineObj;
    const byId = new Map(scene.objects.map((o) => [o.id, o]));
    // Kiểm tra xem có mặt phẳng cắt nào trong cảnh song song hoàn toàn với đường mang này mà không có điểm giao không
    const lineDirFrac = parseFracVec3((exactLineObj.direction ?? lineObj.direction)!);
    const linePtFrac = parseFracVec3((exactLineObj.point ?? lineObj.point)!);
    const hasConsumerPoint = visObjs.some(
      (o) => !isSubEntity(o.id) && o.type === "point3" && (o.depends ?? []).includes(lineObj.id),
    );
    if (!hasConsumerPoint) {
      const parallelCutPlane = visObjs.find((visO) => {
        const o = exactById.get(visO.id) ?? visO;
        return (
          o.type === "plane3"
          && o.normal
          && o.point
          && fIsZero(plainDotFrac(lineDirFrac, parseFracVec3(o.normal)))
          && !fIsZero(plainDotFrac(vSub(linePtFrac, parseFracVec3(o.point)), parseFracVec3(o.normal)))
        );
      });
      const hasOtherConsumer = exactScene.objects.some(
        (o) => !isSubEntity(o.id) && o.id !== lineObj.id && (o.depends ?? []).includes(lineObj.id),
      );
      if (parallelCutPlane && !hasOtherConsumer) {
        return { endpoints: null, mode: "no_intersection" };
      }
    }

    const depPts = (lineObj.depends ?? [])
      .map((id) => byId.get(id))
      .filter((o): o is SceneObject => Boolean(o && o.type === "point3" && o.xyz));
    if (depPts.length === 2) {
      const [uObj, vObj] = depPts;
      const uExact = exactById.get(uObj.id) ?? uObj;
      const vExact = exactById.get(vObj.id) ?? vObj;
      const a = toVec3(uObj.xyz!);
      const b = toVec3(vObj.xyz!);
      const dx = b[0] - a[0];
      const dy = b[1] - a[1];
      const dz = b[2] - a[2];
      const lenSq = dx * dx + dy * dy + dz * dz;
      const len = Math.sqrt(lenSq);
      if (len > 1e-9) {
        const tol = 1e-4 * Math.max(1, len);
        let tMin = 0;
        let tMax = 1;
        let coincidentEndpointId: string | undefined;
        for (const consumerPt of visObjs) {
          if (
            isSubEntity(consumerPt.id)
            || consumerPt.type !== "point3"
            || !consumerPt.xyz
            || !(consumerPt.depends ?? []).includes(lineObj.id)
          ) {
            continue;
          }
          const cExact = exactById.get(consumerPt.id) ?? consumerPt;
          const tExact = exactCollinearParam(cExact.xyz!, uExact.xyz!, vExact.xyz!);
          if (tExact && fIsZero(tExact)) coincidentEndpointId = uObj.id;
          else if (tExact && fEq(tExact, [1n, 1n])) coincidentEndpointId = vObj.id;
        }
        for (const p of ptsForLine) {
          const apx = p[0] - a[0];
          const apy = p[1] - a[1];
          const apz = p[2] - a[2];
          const t = (apx * dx + apy * dy + apz * dz) / lenSq;
          const perp = Math.hypot(apx - t * dx, apy - t * dy, apz - t * dz);
          if (perp <= tol) {
            if (t < tMin) tMin = t;
            if (t > tMax) tMax = t;
          }
        }
        const at = (s: number): Vec3 => [a[0] + s * dx, a[1] + s * dy, a[2] + s * dz];
        if (tMin < -1e-4 || tMax > 1 + 1e-4) {
          const span = tMax - tMin;
          const sLo = tMin < -1e-4 ? tMin - 0.08 * span : 0;
          const sHi = tMax > 1 + 1e-4 ? tMax + 0.08 * span : 1;
          const extensionDirection =
            tMin < -1e-4 && tMax > 1 + 1e-4
              ? "both"
              : tMin < -1e-4
                ? "before_start"
                : "after_end";
          return {
            endpoints: [at(sLo), at(sHi)],
            mode: "extended_ray",
            basePointIds: [uObj.id, vObj.id],
            tRange: [tMin, tMax],
            extensionDirection,
          };
        }
        return {
          endpoints: [a, b],
          mode: "clamped_segment",
          basePointIds: [uObj.id, vObj.id],
          tRange: [0, 1],
          ...(coincidentEndpointId ? { coincidentEndpointId } : {}),
        };
      }
    }
  }

  if (isIntersectionLineOrSegment(lineObj, scene)) {
    const exactScene = exactSceneOriginOf(scene);
    const exactById = new Map(exactScene.objects.map((o) => [o.id, o]));
    const exactLn = exactById.get(lineObj.id) ?? lineObj;
    const planeDeps = (exactLn.depends ?? lineObj.depends ?? [])
      .map((id) => exactById.get(id))
      .filter((p): p is SceneObject => Boolean(p && p.type === "plane3" && p.point && p.normal));
    if (planeDeps.length >= 2) {
      const p1 = parseFracVec3(planeDeps[0].point!);
      const n1 = parseFracVec3(planeDeps[0].normal!);
      const p2 = parseFracVec3(planeDeps[1].point!);
      const n2 = parseFracVec3(planeDeps[1].normal!);
      if (vIsZero(n1) || vIsZero(n2) || vIsZero(vCross(n1, n2))) {
        return { endpoints: null, mode: "no_intersection", coreSegment: null };
      }
      if (exactLn.point && exactLn.direction) {
        const lp0 = parseFracVec3(exactLn.point);
        const ldir = parseFracVec3(exactLn.direction);
        if (
          vIsZero(ldir)
          || !fIsZero(plainDotFrac(ldir, n1))
          || !fIsZero(plainDotFrac(ldir, n2))
          || !fIsZero(plainDotFrac(vSub(lp0, p1), n1))
          || !fIsZero(plainDotFrac(vSub(lp0, p2), n2))
        ) {
          return { endpoints: null, mode: "no_intersection", coreSegment: null };
        }
      }
    }
    const p0 = toVec3(lineObj.point);
    const dirRaw = toVec3(lineObj.direction);
    const dn = Math.hypot(...dirRaw);
    if (dn > 1e-9 && ptsForLine.length > 0) {
      const u: Vec3 = [dirRaw[0] / dn, dirRaw[1] / dn, dirRaw[2] / dn];
      const cheo = Math.max(duongKinhCanh(ptsForLine), 1);
      const tol = 1e-4 * Math.max(1, cheo);
      const zMin = Math.min(...ptsForLine.map((p) => p[2]));
      const lineAnchors: Vec3[] = [];
      for (const p of ptsForLine) {
        const ti = (p[0] - p0[0]) * u[0] + (p[1] - p0[1]) * u[1] + (p[2] - p0[2]) * u[2];
        const perp = Math.hypot(p[0] - p0[0] - ti * u[0], p[1] - p0[1] - ti * u[1], p[2] - p0[2] - ti * u[2]);
        if (perp <= tol) lineAnchors.push(p);
      }
      // Intersect line (p0, u) with visible solid faces & polygons so the displayed intersection line spans the solid cleanly
      const tryPiercePolygon = (polyPts: Vec3[]) => {
        if (polyPts.length < 3) return;
        const e1: Vec3 = [polyPts[1][0] - polyPts[0][0], polyPts[1][1] - polyPts[0][1], polyPts[1][2] - polyPts[0][2]];
        const e2: Vec3 = [polyPts[2][0] - polyPts[0][0], polyPts[2][1] - polyPts[0][1], polyPts[2][2] - polyPts[0][2]];
        const nx = e1[1] * e2[2] - e1[2] * e2[1];
        const ny = e1[2] * e2[0] - e1[0] * e2[2];
        const nz = e1[0] * e2[1] - e1[1] * e2[0];
        const nLen = Math.hypot(nx, ny, nz);
        if (!(nLen > 1e-8)) return;
        const fn: Vec3 = [nx / nLen, ny / nLen, nz / nLen];
        const denom = u[0] * fn[0] + u[1] * fn[1] + u[2] * fn[2];
        if (Math.abs(denom) <= 1e-7) return;
        const numer = (polyPts[0][0] - p0[0]) * fn[0] + (polyPts[0][1] - p0[1]) * fn[1] + (polyPts[0][2] - p0[2]) * fn[2];
        const tHit = numer / denom;
        const q: Vec3 = [p0[0] + tHit * u[0], p0[1] + tHit * u[1], p0[2] + tHit * u[2]];
        let posSign = 0;
        let negSign = 0;
        for (let i = 0; i < polyPts.length; i += 1) {
          const a = polyPts[i];
          const b = polyPts[(i + 1) % polyPts.length];
          const ex = b[0] - a[0], ey = b[1] - a[1], ez = b[2] - a[2];
          const qx = q[0] - a[0], qy = q[1] - a[1], qz = q[2] - a[2];
          const cx = ey * qz - ez * qy;
          const cy = ez * qx - ex * qz;
          const cz = ex * qy - ey * qx;
          const s = cx * fn[0] + cy * fn[1] + cz * fn[2];
          if (s > 1e-5) posSign += 1;
          else if (s < -1e-5) negSign += 1;
        }
        if (posSign === 0 || negSign === 0) lineAnchors.push(q);
      };
      for (const obj of visObjs) {
        if (obj.type === "solid" && obj.vertices && obj.faces) {
          const verts = obj.vertices.map(toVec3);
          for (const f of obj.faces) {
            const fPts = f.map((idx) => verts[idx]).filter(Boolean);
            tryPiercePolygon(fPts);
          }
        } else if ((obj.type === "polygon3" || obj.type === "section") && (obj.polygon ?? obj.vertices)) {
          tryPiercePolygon((obj.polygon ?? obj.vertices ?? []).map(toVec3));
        }
      }
      if (lineAnchors.length >= 2) {
        const ts = lineAnchors.map((p) => (p[0] - p0[0]) * u[0] + (p[1] - p0[1]) * u[1] + (p[2] - p0[2]) * u[2]);
        const tLo = Math.min(...ts);
        const tHi = Math.max(...ts);
        const span = tHi - tLo;
        if (span > 1e-5) {
          const pad = Math.min(Math.max(span * 0.12, cheo * 0.04), cheo * 0.09);
          let sLo = tLo - pad;
          let sHi = tHi + pad;
          const zFloorLimit = zMin - Math.min(span * 0.08, 0.24);
          if (Math.abs(u[2]) > 1e-5) {
            const zAtLo = p0[2] + sLo * u[2];
            const zAtHi = p0[2] + sHi * u[2];
            if (zAtLo < zFloorLimit && p0[2] + tLo * u[2] >= zMin - 1e-4) {
              sLo = (zFloorLimit - p0[2]) / u[2];
            }
            if (zAtHi < zFloorLimit && p0[2] + tHi * u[2] >= zMin - 1e-4) {
              sHi = (zFloorLimit - p0[2]) / u[2];
            }
          }
          const at = (s: number): Vec3 => [p0[0] + s * u[0], p0[1] + s * u[1], p0[2] + s * u[2]];
          return {
            endpoints: [at(Math.min(sLo, sHi)), at(Math.max(sLo, sHi))],
            mode: "infinite_line",
            coreSegment: [at(tLo), at(tHi)],
          };
        }
      }
    }
  }

  return {
    endpoints: (() => {
      const raw = doanDuongThang(toVec3(lineObj.point), toVec3(lineObj.direction), ptsForLine);
      return raw;
    })(),
    ...(() => {
      const raw = doanDuongThang(toVec3(lineObj.point), toVec3(lineObj.direction), ptsForLine);
      if (!raw) return {};
      const dx = raw[1][0] - raw[0][0];
      const dy = raw[1][1] - raw[0][1];
      const dz = raw[1][2] - raw[0][2];
      const len = Math.hypot(dx, dy, dz);
      if (len <= 1e-5) return {};
      const lerp = (t: number): Vec3 => [raw[0][0] + t * dx, raw[0][1] + t * dy, raw[0][2] + t * dz];
      return { coreSegment: [lerp(0.16), lerp(0.84)] as [Vec3, Vec3] };
    })(),
    mode: "infinite_line",
  };
}

function exactCollinearParam(pRaw: ExactVec3, aRaw: ExactVec3, bRaw: ExactVec3): Frac | null {
  const p = parseFracVec3(pRaw);
  const a = parseFracVec3(aRaw);
  const b = parseFracVec3(bRaw);
  const ab = vSub(b, a);
  const ap = vSub(p, a);
  if (vIsZero(ab) || !vIsZero(vCross(ap, ab))) return null;
  for (let c = 0; c < 3; c += 1) {
    if (!fIsZero(ab[c])) {
      return normFrac(ap[c][0] * ab[c][1], ap[c][1] * ab[c][0]);
    }
  }
  return null;
}

export interface SceneMathContradiction {
  objectId: string;
  title: string;
  explanation: string;
}

export interface SceneMathVerificationResult {
  valid: boolean;
  contradictions: SceneMathContradiction[];
}

/**
 * Kiểm chứng tính nhất quán toán học chính xác trên Q^3 của toàn bộ cảnh `Scene3D` trước khi kết luận / hiển thị:
 * 1. Điểm trung điểm / chia đoạn phải thỏa phương trình affine chính xác với hai đầu mút phụ thuộc.
 * 2. Mặt phẳng `plane3` có `normal != 0` và chứa toàn bộ các điểm `point3` trong `depends`.
 * 3. Giao điểm đường–mặt `Q = d ∩ (α)` phải đồng thời thuộc đường thẳng `d` VÀ thuộc mặt phẳng `(α)`.
 *    - Nếu `d ∥ (α)` (`dot(dir, normal) == 0`) mà vẫn khai báo giao điểm duy nhất ⇒ báo lỗi không có giao điểm hợp lệ.
 *    - Nếu dữ kiện mặt phẳng bắt buộc giao tại tỉ số `t_expected` (vd `t = 1/2` khi `M, N, P` là ba trung điểm của `SA, SB, SC`)
 *      nhưng tọa độ `Q` đặt lệch sang vị trí khác (vd `t = 3/2` ngoài đoạn `SD`) ⇒ từ chối an toàn kèm giải thích tiếng Việt rõ ràng.
 * 4. Đa giác thiết diện `section` phải đồng phẳng, không suy biến (diện tích > 0), thuộc mặt phẳng cắt và từng cạnh giao tuyến
 *    `steps` phải nằm đúng trên mặt tương ứng của khối.
 * 5. Nhân chứng vuông góc `perpendicular_witness` phải thỏa tích vô hướng Gram bằng 0 chính xác.
 */
const _mathVerifyCache = new WeakMap<object, { sig: string; result: SceneMathVerificationResult }>();

function mathVerifySignature(scene: Pick<Scene3D, "objects" | "chart_metric" | "length_unit">): string {
  const m = scene.chart_metric ? scene.chart_metric.map((r) => r.join(",")).join(";") : "";
  const parts: string[] = [m, String(scene.objects.length)];
  for (const o of scene.objects) {
    if (isSubEntity(o.id)) continue;
    parts.push(
      `${o.id}:${o.type}:${o.authoritative === false ? 0 : 1}:${o.xyz?.join(",") ?? o.point?.join(",") ?? o.center?.join(",") ?? o.anchor?.join(",") ?? ""}:${o.normal?.join(",") ?? o.direction?.join(",") ?? o.apex_or_top?.join(",") ?? ""}:${o.radius_sq ?? ""}:${o.height_sq ?? ""}:${o.value ?? ""}:${o.polygon?.length ?? o.vertices?.length ?? 0}:${Boolean(o.perpendicular_witness)}`,
    );
  }
  return parts.join("|");
}

export function verifySceneMathematicalConsistency(
  rawScene: Pick<Scene3D, "objects" | "chart_metric" | "length_unit">,
): SceneMathVerificationResult {
  const scene = exactSceneOriginOf(rawScene);
  const sig = mathVerifySignature(scene);
  const cached = _mathVerifyCache.get(scene as object);
  if (cached && cached.sig === sig) return cached.result;
  const contradictions: SceneMathContradiction[] = [];
  const byId = new Map(scene.objects.map((o) => [o.id, o]));

  for (const obj of scene.objects) {
    if (isSubEntity(obj.id)) continue;

    // 0. Kiểm tra ranh giới thẩm quyền: đối tượng chính thống không được phụ thuộc ngược vào đối tượng phụ giải thích (`authoritative: false`)
    if (obj.authoritative !== false) {
      for (const depId of obj.depends ?? []) {
        const depObj = byId.get(depId);
        if (depObj && depObj.authoritative === false) {
          contradictions.push({
            objectId: obj.id,
            title: "Vi phạm ranh giới đối tượng phụ không thẩm quyền",
            explanation: `Đối tượng chính thống ${shortSym(obj) || obj.label} không được phụ thuộc ngược vào đối tượng phụ giải thích ${shortSym(depObj) || depObj.label} (authoritative: false).`,
          });
          break;
        }
      }
    }

    // 1. Kiểm tra điểm trung điểm & giao điểm đường–mặt
    if (obj.type === "point3" && obj.xyz && obj.origin === "derived") {
      const sym = shortSym(obj) || obj.label;
      const depObjs = (obj.depends ?? []).map((id) => byId.get(id)).filter((x): x is SceneObject => Boolean(x));
      const ptDeps = depObjs.filter((d) => d.type === "point3" && Boolean(d.xyz));

      const srcInst = obj.source?.instruction ?? "";
      const trimmedRole = (obj.role ?? "").trim();
      const isMidpointClaim = trimmedRole
        ? /^Trung điểm\b/iu.test(trimmedRole)
        : (
            /^Trung điểm\b/iu.test(obj.label ?? "")
            || srcInst.endsWith(".midpoint")
            || (obj.producer ?? "").endsWith(".midpoint")
          );
      if (ptDeps.length === 2 && isMidpointClaim) {
        const [pA, pB] = ptDeps;
        if (!isExactMidpointVec(obj.xyz, pA.xyz!, pB.xyz!)) {
          contradictions.push({
            objectId: obj.id,
            title: "Mâu thuẫn dữ kiện trung điểm",
            explanation: `Điểm ${sym} được khai báo là trung điểm của ${shortSym(pA)}${shortSym(pB)} nhưng tọa độ không thỏa mãn 2·${sym} = ${shortSym(pA)} + ${shortSym(pB)}.`,
          });
        }
      }

      if (depObjs.length === 2) {
        const ln = depObjs.find((d) => d.type === "line3" || d.type === "segment3");
        const pl = depObjs.find((d) => d.type === "plane3");
        if (ln && pl && pl.point && pl.normal) {
          const p0 = parseFracVec3(pl.point);
          const nVec = parseFracVec3(pl.normal);
          const endPts = (ln.depends ?? [])
            .map((id) => byId.get(id))
            .filter((d): d is SceneObject => Boolean(d && d.type === "point3" && d.xyz));
          const apexSyms = structuralApexSymsOfScene(scene);
          let pLine: FracVec3 | null = null;
          let dirLine: FracVec3 | null = null;
          let firstEnd: SceneObject | undefined;
          let secondEnd: SceneObject | undefined;
          if (endPts.length === 2) {
            const [u, v] = endPts;
            firstEnd = apexSyms.has(shortSym(u)) ? u : apexSyms.has(shortSym(v)) ? v : u;
            secondEnd = firstEnd === u ? v : u;
            pLine = parseFracVec3(firstEnd.xyz!);
            dirLine = vSub(parseFracVec3(secondEnd.xyz!), pLine);
          } else if (ln.point && ln.direction) {
            pLine = parseFracVec3(ln.point);
            dirLine = parseFracVec3(ln.direction);
          } else if (ln.point_a && ln.point_b) {
            pLine = parseFracVec3(ln.point_a);
            dirLine = vSub(parseFracVec3(ln.point_b), pLine);
          }

          if (pLine && dirLine && !vIsZero(dirLine) && !vIsZero(nVec)) {
            const lineLabel = firstEnd && secondEnd
              ? `${shortSym(firstEnd)}${shortSym(secondEnd)}`
              : shortSym(ln);
            const rawPl = pl.notation?.trim() || shortSym(pl);
            const planeLabel = rawPl.startsWith("(") ? rawPl : `(${rawPl})`;
            const dn = plainDotFrac(dirLine, nVec);
            const num = plainDotFrac(vSub(p0, pLine), nVec);

            if (fIsZero(dn)) {
              if (!fIsZero(num)) {
                contradictions.push({
                  objectId: obj.id,
                  title: "Không tồn tại giao điểm đường thẳng và mặt phẳng",
                  explanation: `Đường thẳng ${lineLabel} song song với mặt phẳng ${planeLabel} nên không tồn tại giao điểm ${sym} = ${lineLabel} ∩ ${planeLabel}.`,
                });
              } else {
                contradictions.push({
                  objectId: obj.id,
                  title: "Giao điểm không xác định duy nhất",
                  explanation: `Đường thẳng ${lineLabel} nằm trọn trong mặt phẳng ${planeLabel} nên không xác định giao điểm duy nhất ${sym}.`,
                });
              }
            } else {
              const qVec = parseFracVec3(obj.xyz);
              const onLine = vIsZero(vCross(vSub(qVec, pLine), dirLine));
              const onPlane = fIsZero(plainDotFrac(vSub(qVec, p0), nVec));
              if (!onLine || !onPlane) {
                const tExpected = normFrac(num[0] * dn[1], num[1] * dn[0]);
                const tActual = firstEnd && secondEnd
                  ? exactCollinearParam(obj.xyz, firstEnd.xyz!, secondEnd.xyz!)
                  : null;
                const expectedWhere =
                  tExpected[0] === 1n && tExpected[1] === 2n
                    ? `trung điểm đoạn ${lineLabel} (tỉ số 1/2 nằm trong đoạn)`
                    : tExpected[0] >= 0n && tExpected[0] <= tExpected[1]
                      ? `điểm nằm trong đoạn ${lineLabel} (tỉ số ${fmtFrac(tExpected)})`
                      : `điểm nằm ngoài đoạn ${lineLabel} (tỉ số ${fmtFrac(tExpected)})`;
                const actualWhere = tActual
                  ? (tActual[0] < 0n || tActual[0] > tActual[1]
                      ? `ngoài đoạn ${lineLabel} ở tỉ số ${fmtFrac(tActual)}`
                      : `tỉ số ${fmtFrac(tActual)}`)
                  : "tọa độ không thuộc đồng thời đường thẳng và mặt phẳng";
                contradictions.push({
                  objectId: obj.id,
                  title: "Mâu thuẫn dữ kiện vị trí giao điểm",
                  explanation: `Theo giả thiết xác định mặt phẳng ${planeLabel}, giao điểm ${lineLabel} ∩ ${planeLabel} bắt buộc là ${expectedWhere}, mâu thuẫn với vị trí ${sym} đặt tại ${actualWhere}.`,
                });
              } else if (ln.type === "segment3" && firstEnd && secondEnd) {
                const finiteSegOnly = srcInst.endsWith("intersect_segment_plane");
                if (finiteSegOnly) {
                  const tSeg = exactCollinearParam(obj.xyz, firstEnd.xyz!, secondEnd.xyz!);
                  if (!tSeg || tSeg[0] < 0n || tSeg[0] > tSeg[1]) {
                    contradictions.push({
                      objectId: obj.id,
                      title: "Giao điểm nằm ngoài đoạn thẳng",
                      explanation: `Điểm ${sym} được khai báo thuộc đoạn thẳng hữu hạn ${lineLabel} nhưng giao điểm với ${planeLabel} nằm ngoài đoạn ${lineLabel}${tSeg ? ` (tỉ số ${fmtFrac(tSeg)})` : ""}.`,
                    });
                  }
                }
              }
            }
          }
        }
      }
    }

    // 2. Kiểm tra mặt phẳng `plane3` chứa đủ các điểm định nghĩa và có hạng affine = 2 (không suy biến / không mơ hồ)
    if (obj.type === "plane3" && obj.point && obj.normal) {
      const p0 = parseFracVec3(obj.point);
      const nVec = parseFracVec3(obj.normal);
      const rawPl = obj.notation?.trim() || shortSym(obj);
      const planeLabel = rawPl.startsWith("(") ? rawPl : `(${rawPl})`;
      if (vIsZero(nVec)) {
        contradictions.push({
          objectId: obj.id,
          title: "Mặt phẳng suy biến",
          explanation: `Mặt phẳng ${planeLabel} có pháp tuyến bằng 0 (các điểm xác định thẳng hàng hoặc trùng nhau).`,
        });
      } else {
        const depObjs = (obj.depends ?? []).map((depId) => byId.get(depId));
        const allPointDeps =
          obj.origin !== "free"
          && depObjs.length > 0
          && depObjs.every((d): d is SceneObject => Boolean(d && d.type === "point3" && d.xyz));
        if (allPointDeps) {
          const pts = depObjs.map((d) => parseFracVec3(d.xyz!));
          let spans2D = false;
          for (let i = 1; i < pts.length && !spans2D; i += 1) {
            for (let j = i + 1; j < pts.length; j += 1) {
              if (!vIsZero(vCross(vSub(pts[i], pts[0]), vSub(pts[j], pts[0])))) {
                spans2D = true;
                break;
              }
            }
          }
          if (!spans2D) {
            contradictions.push({
              objectId: obj.id,
              title: "Mặt phẳng không xác định duy nhất",
              explanation: `Các điểm xác định mặt phẳng ${planeLabel} thẳng hàng hoặc không đủ 3 điểm không thẳng hàng nên mặt phẳng suy biến / không duy nhất.`,
            });
          }
        }
        for (const depId of obj.depends ?? []) {
          const pt = byId.get(depId);
          if (pt?.type === "point3" && pt.xyz) {
            const pv = parseFracVec3(pt.xyz);
            if (!fIsZero(plainDotFrac(vSub(pv, p0), nVec))) {
              contradictions.push({
                objectId: obj.id,
                title: "Mâu thuẫn điểm thuộc mặt phẳng",
                explanation: `Điểm ${shortSym(pt)} được khai báo xác định mặt phẳng ${planeLabel} nhưng không nằm trên mặt phẳng này.`,
              });
            }
          }
        }
      }
    }

    // 2b. Kiểm tra đoạn thẳng / đường thẳng suy biến (hai đầu mút trùng nhau hoặc vectơ chỉ phương bằng 0)
    if ((obj.type === "line3" || obj.type === "segment3") && obj.authoritative !== false) {
      if (obj.point_a && obj.point_b && vIsZero(vSub(parseFracVec3(obj.point_b), parseFracVec3(obj.point_a)))) {
        contradictions.push({
          objectId: obj.id,
          title: "Đoạn thẳng suy biến",
          explanation: `Hai đầu mút của ${shortSym(obj) || obj.label} trùng nhau nên phép dựng suy biến.`,
        });
      } else if (obj.direction && vIsZero(parseFracVec3(obj.direction))) {
        contradictions.push({
          objectId: obj.id,
          title: "Đường thẳng không xác định duy nhất",
          explanation: `Đường thẳng ${shortSym(obj) || obj.label} có vectơ chỉ phương bằng 0 nên không xác định duy nhất.`,
        });
      }
    }

    // 3. Kiểm tra đa giác thiết diện `section`
    if (obj.type === "section") {
      const poly = obj.polygon ?? [];
      if (poly.length < 3) {
        contradictions.push({
          objectId: obj.id,
          title: "Thiết diện suy biến",
          explanation: `Thiết diện có ít hơn 3 đỉnh nên không tạo thành miền đa giác hợp lệ.`,
        });
      } else {
        const v = poly.map(parseFracVec3);
        let hasZeroEdge = false;
        for (let i = 0; i < v.length; i += 1) {
          if (vIsZero(vSub(v[(i + 1) % v.length], v[i]))) {
            hasZeroEdge = true;
            break;
          }
        }
        let areaVec: FracVec3 = [
          [0n, 1n],
          [0n, 1n],
          [0n, 1n],
        ];
        for (let i = 1; i + 1 < v.length; i += 1) {
          areaVec = vAdd(areaVec, vCross(vSub(v[i], v[0]), vSub(v[i + 1], v[0])));
        }
        if (hasZeroEdge || vIsZero(areaVec)) {
          contradictions.push({
            objectId: obj.id,
            title: "Thiết diện suy biến",
            explanation: `Các đỉnh của thiết diện thẳng hàng hoặc trùng nhau nên miền đa giác suy biến.`,
          });
        } else {
          for (let i = 2; i < v.length; i += 1) {
            if (!fIsZero(plainDotFrac(vSub(v[i], v[0]), areaVec))) {
              contradictions.push({
                objectId: obj.id,
                title: "Mâu thuẫn đồng phẳng của thiết diện",
                explanation: `Các đỉnh của thiết diện không đồng phẳng trên cùng một mặt phẳng cắt.`,
              });
              break;
            }
          }
          const planeDep = (obj.depends ?? []).map((id) => byId.get(id)).find((d) => d?.type === "plane3");
          if (planeDep?.point && planeDep.normal) {
            const p0 = parseFracVec3(planeDep.point);
            const nVec = parseFracVec3(planeDep.normal);
            const rawPl = planeDep.notation?.trim() || shortSym(planeDep);
            const planeLabel = rawPl.startsWith("(") ? rawPl : `(${rawPl})`;
            for (const vx of v) {
              if (!fIsZero(plainDotFrac(vSub(vx, p0), nVec))) {
                contradictions.push({
                  objectId: obj.id,
                  title: "Đỉnh thiết diện lệch khỏi mặt phẳng cắt",
                  explanation: `Tồn tại đỉnh của thiết diện không thuộc mặt phẳng cắt ${planeLabel}.`,
                });
                break;
              }
            }
          }
          // Kiểm tra miền giới hạn của khối chủ (`solid`): mọi đỉnh của `section.polygon` phải nằm trong hoặc trên biên
          // của khối đa diện lồi (giao điểm phụ trên đường kéo dài ngoài khối KHÔNG được đưa vào đa giác thiết diện).
          const allSolids = scene.objects.filter(
            (s) => s.type === "solid" && (s.vertices?.length ?? 0) >= 4 && (s.faces?.length ?? 0) >= 4,
          );
          const hostSolid =
            (obj.depends ?? [])
              .map((id) => byId.get(id))
              .find((d) => d?.type === "solid" && (d.vertices?.length ?? 0) >= 4 && (d.faces?.length ?? 0) >= 4)
            ?? (allSolids.length === 1 ? allSolids[0] : undefined);
          if (hostSolid?.vertices && hostSolid.faces) {
            const sVerts = hostSolid.vertices.map(parseFracVec3);
            let outsideSolid = false;
            for (const face of hostSolid.faces) {
              if (face.length < 3 || !sVerts[face[0]]) continue;
              const f0 = sVerts[face[0]];
              let nFace: FracVec3 | null = null;
              for (let k = 1; k + 1 < face.length; k += 1) {
                if (!sVerts[face[k]] || !sVerts[face[k + 1]]) continue;
                const cand = vCross(vSub(sVerts[face[k]], f0), vSub(sVerts[face[k + 1]], f0));
                if (!vIsZero(cand)) {
                  nFace = cand;
                  break;
                }
              }
              if (!nFace) continue;
              let hasPos = false;
              let hasNeg = false;
              for (const sv of sVerts) {
                const sgn = plainDotFrac(vSub(sv, f0), nFace)[0];
                if (sgn > 0n) hasPos = true;
                else if (sgn < 0n) hasNeg = true;
              }
              if ((hasPos && hasNeg) || (!hasPos && !hasNeg)) continue;
              const inward: FracVec3 = hasPos
                ? nFace
                : [[-nFace[0][0], nFace[0][1]], [-nFace[1][0], nFace[1][1]], [-nFace[2][0], nFace[2][1]]];
              if (v.some((vx) => plainDotFrac(vSub(vx, f0), inward)[0] < 0n)) {
                outsideSolid = true;
                break;
              }
            }
            if (outsideSolid) {
              contradictions.push({
                objectId: obj.id,
                title: "Đỉnh thiết diện nằm ngoài miền khối",
                explanation:
                  "Tồn tại đỉnh được đưa vào đa giác thiết diện nhưng nằm ngoài miền giới hạn của khối đa diện (điểm giao trên cạnh kéo dài ngoài khối chỉ là điểm phụ dựng giao tuyến, không phải đỉnh của thiết diện).",
              });
            }
          }
        }
      }
    }

    // 3b. Kiểm tra giao tuyến của hai mặt phẳng (`intersect_plane_plane`)
    if ((obj.type === "line3" || obj.type === "segment3") && isIntersectionLineOrSegment(obj, scene)) {
      const planeDeps = (obj.depends ?? [])
        .map((id) => byId.get(id))
        .filter((d): d is SceneObject => Boolean(d && d.type === "plane3" && d.point && d.normal));
      if (planeDeps.length >= 2) {
        const p1 = parseFracVec3(planeDeps[0].point!);
        const n1 = parseFracVec3(planeDeps[0].normal!);
        const p2 = parseFracVec3(planeDeps[1].point!);
        const n2 = parseFracVec3(planeDeps[1].normal!);
        const pl1 = formatPlaneDisplayNotation(planeDeps[0]);
        const pl2 = formatPlaneDisplayNotation(planeDeps[1]);
        if (!vIsZero(n1) && !vIsZero(n2)) {
          if (vIsZero(vCross(n1, n2))) {
            const coincident = fIsZero(plainDotFrac(vSub(p2, p1), n1));
            contradictions.push({
              objectId: obj.id,
              title: coincident
                ? "Hai mặt phẳng trùng nhau không xác định giao tuyến duy nhất"
                : "Hai mặt phẳng song song không có giao tuyến",
              explanation: coincident
                ? `Hai mặt phẳng ${pl1} và ${pl2} trùng nhau nên không xác định một đường giao tuyến duy nhất.`
                : `Hai mặt phẳng ${pl1} và ${pl2} song song phân biệt nên không tồn tại giao tuyến ${shortSym(obj) || obj.label}.`,
            });
          } else if (obj.point && obj.direction) {
            const lp0 = parseFracVec3(obj.point);
            const ldir = parseFracVec3(obj.direction);
            if (
              vIsZero(ldir)
              || !fIsZero(plainDotFrac(ldir, n1))
              || !fIsZero(plainDotFrac(ldir, n2))
              || !fIsZero(plainDotFrac(vSub(lp0, p1), n1))
              || !fIsZero(plainDotFrac(vSub(lp0, p2), n2))
            ) {
              contradictions.push({
                objectId: obj.id,
                title: "Mâu thuẫn phương trình giao tuyến hai mặt phẳng",
                explanation: `Đường thẳng ${shortSym(obj) || obj.label} không thuộc đồng thời cả hai mặt phẳng ${pl1} và ${pl2}.`,
              });
            }
          }
        }
      }
    }

    // 4. Kiểm tra nhân chứng vuông góc `perpendicular_witness` / `annotation.witness` (gồm cả đường vuông góc chung `second`, tính thuộc trên đối tượng mang & độ dài chuẩn Gram)
    const w = obj.perpendicular_witness ?? obj.annotation?.witness;
    if (w?.foot && w.marker?.v) {
      const pointLiesOnWitnessCarrier = (pt: FracVec3, carrier: SceneObject | undefined): boolean => {
        if (!carrier) return true;
        if (carrier.type === "plane3" && carrier.point && carrier.normal) {
          const p0 = parseFracVec3(carrier.point);
          const nVec = parseFracVec3(carrier.normal);
          return !vIsZero(nVec) && fIsZero(plainDotFrac(vSub(pt, p0), nVec));
        }
        if (carrier.point && carrier.direction) {
          const lp = parseFracVec3(carrier.point);
          const ld = parseFracVec3(carrier.direction);
          return !vIsZero(ld) && vIsZero(vCross(vSub(pt, lp), ld));
        }
        if (carrier.point_a && carrier.point_b) {
          const pa = parseFracVec3(carrier.point_a);
          const pb = parseFracVec3(carrier.point_b);
          const dir = vSub(pb, pa);
          return !vIsZero(dir) && vIsZero(vCross(vSub(pt, pa), dir));
        }
        if (carrier.type === "polygon3" && (carrier.vertices?.length ?? 0) >= 3) {
          const pv = carrier.vertices!.map(parseFracVec3);
          const fn = vCross(vSub(pv[1], pv[0]), vSub(pv[2], pv[0]));
          return !vIsZero(fn) && fIsZero(plainDotFrac(vSub(pt, pv[0]), fn));
        }
        const depPts = (carrier.depends ?? [])
          .map((id) => byId.get(id))
          .filter((p): p is SceneObject => Boolean(p && p.type === "point3" && p.xyz));
        if (depPts.length >= 2 && (carrier.type === "line3" || carrier.type === "segment3")) {
          const pa = parseFracVec3(depPts[0].xyz!);
          const pb = parseFracVec3(depPts[1].xyz!);
          const dir = vSub(pb, pa);
          return !vIsZero(dir) && vIsZero(vCross(vSub(pt, pa), dir));
        }
        return true;
      };
      const exactNumberSq = (ex: SceneObject["exact"] | string): Frac | null => {
        if (!ex) return null;
        if (typeof ex === "string") {
          try {
            const c = parseExactFrac(ex);
            return fMul(c, c);
          } catch {
            return null;
          }
        }
        if (ex.kind === "rational") {
          const c = parseExactFrac(ex.value);
          return fMul(c, c);
        }
        if (ex.kind === "radical" && !ex.pi) {
          const c = parseExactFrac(ex.coefficient);
          return fMul(fMul(c, c), [BigInt(ex.radicand), 1n]);
        }
        return null;
      };

      const vPerp = parseFracVec3(w.marker.v);
      const foot1 = parseFracVec3(w.foot);
      if (vIsZero(vPerp)) {
        contradictions.push({
          objectId: obj.id,
          title: "Nhân chứng vuông góc suy biến",
          explanation: `Vector vuông góc của ${shortSym(obj)} suy biến bằng 0.`,
        });
      } else {
        let orthoFailed = false;
        let incidenceOrNormTitle = "";
        let incidenceOrNormDetail = "";
        if (w.plane_directions?.length) {
          for (const pDir of w.plane_directions) {
            if (!fIsZero(metricDot(vPerp, parseFracVec3(pDir), scene.chart_metric))) {
              orthoFailed = true;
              break;
            }
          }
        }
        if (!orthoFailed && w.marker?.u) {
          const uVec = parseFracVec3(w.marker.u);
          if (vIsZero(uVec) || !fIsZero(metricDot(uVec, vPerp, scene.chart_metric))) {
            orthoFailed = true;
          }
        }
        if (!orthoFailed && w.second?.marker?.u && w.second?.marker?.v) {
          const u2 = parseFracVec3(w.second.marker.u);
          const v2 = parseFracVec3(w.second.marker.v);
          if (vIsZero(u2) || vIsZero(v2) || !fIsZero(metricDot(u2, v2, scene.chart_metric))) {
            orthoFailed = true;
          }
        }
        if (!orthoFailed && w.on && !pointLiesOnWitnessCarrier(foot1, byId.get(w.on))) {
          incidenceOrNormTitle = "Chân vuông góc không nằm trên đối tượng mang";
          incidenceOrNormDetail = `Chân vuông góc của ${shortSym(obj) || obj.label} không thỏa phương trình thuộc đối tượng ${shortSym(byId.get(w.on)) || w.on}.`;
        }
        if (!orthoFailed && !incidenceOrNormTitle && (w.relation === "common_perpendicular" || w.second?.foot)) {
          if (w.second?.foot) {
            const foot2 = parseFracVec3(w.second.foot);
            const secondCarrier = w.second.on ? byId.get(w.second.on) : undefined;
            const segVec = vSub(foot2, foot1);
            if (secondCarrier && !pointLiesOnWitnessCarrier(foot2, secondCarrier)) {
              incidenceOrNormTitle = "Chân vuông góc chung không thuộc đường thẳng thứ hai";
              incidenceOrNormDetail = `Chân vuông góc thứ hai của ${shortSym(obj) || obj.label} không nằm trên đường thẳng ${shortSym(secondCarrier) || w.second.on}.`;
            } else if (w.from_point && !vIsZero(vSub(parseFracVec3(w.from_point), foot2))) {
              incidenceOrNormTitle = "Mâu thuẫn đầu mút đoạn vuông góc chung";
              incidenceOrNormDetail = `Tọa độ đầu mút from_point và second.foot của nhân chứng vuông góc chung không khớp nhau.`;
            } else if (!vIsZero(segVec)) {
              if (!vParallel(segVec, vPerp)) {
                orthoFailed = true;
              } else if (w.marker?.u && !fIsZero(metricDot(segVec, parseFracVec3(w.marker.u), scene.chart_metric))) {
                orthoFailed = true;
              } else if (w.second.marker?.u && !fIsZero(metricDot(segVec, parseFracVec3(w.second.marker.u), scene.chart_metric))) {
                orthoFailed = true;
              } else if (obj.type === "quantity" && obj.annotation?.kind === "distance" && !scene.length_unit) {
                const expSq = exactNumberSq(obj.exact);
                if (expSq && !fEq(metricDot(segVec, segVec, scene.chart_metric), expSq)) {
                  incidenceOrNormTitle = "Mâu thuẫn giữa tọa độ chân vuông góc chung và khoảng cách";
                  incidenceOrNormDetail = `Độ dài đoạn nối hai chân vuông góc chung theo metric của cảnh không khớp giá trị khoảng cách ${obj.value ?? ""}.`;
                }
              }
            }
          }
        } else if (!orthoFailed && !incidenceOrNormTitle && obj.type === "quantity" && w.from) {
          const fromObj = byId.get(w.from);
          if (fromObj?.type === "point3" && fromObj.xyz) {
            const dropVec = vSub(parseFracVec3(fromObj.xyz), foot1);
            if (!vIsZero(dropVec) && !vParallel(dropVec, vPerp)) {
              orthoFailed = true;
            } else if (obj.annotation?.kind === "distance" && !scene.length_unit) {
              const expSq = exactNumberSq(obj.exact);
              if (expSq && !fEq(metricDot(dropVec, dropVec, scene.chart_metric), expSq)) {
                incidenceOrNormTitle = "Mâu thuẫn giữa chân vuông góc và giá trị khoảng cách";
                incidenceOrNormDetail = `Độ dài đoạn vuông góc hạ từ ${shortSym(fromObj)} đến chân vuông góc không khớp giá trị khoảng cách ${obj.value ?? ""}.`;
              }
            }
          }
        }
        if (orthoFailed) {
          contradictions.push({
            objectId: obj.id,
            title: "Mâu thuẫn quan hệ vuông góc",
            explanation: `Đối tượng ${shortSym(obj) || obj.label} mang ký hiệu vuông góc nhưng không thỏa tích vô hướng bằng 0 theo metric của cảnh.`,
          });
        } else if (incidenceOrNormTitle) {
          contradictions.push({
            objectId: obj.id,
            title: incidenceOrNormTitle,
            explanation: incidenceOrNormDetail,
          });
        }
      }
    }

    // 4b. Kiểm tra mặt phẳng có ý định cắt mặt cầu nhưng khoảng cách d > R (không cắt mặt cầu — fail-closed).
    // Lưu ý: backend mặc định gắn `surface_role: "CUTTING_PLANE"` lên mọi `plane3` (kể cả mặt phẳng tham chiếu/khoảng cách
    // rời mặt cầu hợp lệ), nên chỉ báo lỗi khi có ý định cắt/giao thực sự.
    if (
      obj.type === "plane3"
      && obj.point
      && obj.normal
      && (obj.surface_role === "CUTTING_PLANE" || (obj.formation_roles ?? []).includes("CONSTRUCT_CUTTING_OBJECT"))
    ) {
      const hasDownstreamSectionOrCircle = scene.objects.some(
        (cand) =>
          (cand.type === "section" || cand.type === "circle3" || cand.type === "ellipse3")
          && (cand.depends ?? []).includes(obj.id),
      );
      const isDistanceTargetReferencePlane = scene.objects.some((cand) => {
        if (cand.type === "quantity" && (cand.depends ?? []).includes(obj.id)) {
          return cand.annotation?.kind === "distance" || Boolean(cand.annotation?.witness);
        }
        return Boolean(
          (cand.type === "point3" || cand.type === "segment3")
            && cand.perpendicular_witness?.on === obj.id
            && !(obj.formation_roles ?? []).includes("CONSTRUCT_CUTTING_OBJECT"),
        );
      });
      const hasExplicitCuttingIntent =
        hasDownstreamSectionOrCircle
        || (obj.formation_roles ?? []).includes("CONSTRUCT_CUTTING_OBJECT")
        || (obj.formation_roles ?? []).includes("PRODUCE_SECTION_RESULT")
        || (obj.depends ?? []).some((d) => byId.get(d)?.type === "curved_solid" && byId.get(d)?.curved_kind === "ball")
        || (obj.surface_role === "CUTTING_PLANE" && !obj.producer && !isDistanceTargetReferencePlane);
      const cutsOtherSolid = scene.objects.some(
        (cand) =>
          (cand.type === "section" || cand.type === "circle3" || cand.type === "ellipse3")
          && (cand.depends ?? []).includes(obj.id)
          && (cand.depends ?? []).some((d) => {
            const dep = byId.get(d);
            return Boolean(dep && (dep.type === "solid" || (dep.type === "curved_solid" && dep.curved_kind !== "ball")));
          }),
      );
      if (hasExplicitCuttingIntent && !cutsOtherSolid) {
        const directBall = (obj.depends ?? [])
          .map((id) => byId.get(id))
          .find((d): d is SceneObject => Boolean(d && d.type === "curved_solid" && d.curved_kind === "ball" && d.anchor && d.radius_sq));
        const allBalls = scene.objects.filter(
          (cand) => cand.type === "curved_solid" && cand.curved_kind === "ball" && cand.anchor && cand.radius_sq,
        );
        const hasNonBallSolid = scene.objects.some(
          (cand) => cand.type === "solid" || (cand.type === "curved_solid" && cand.curved_kind !== "ball"),
        );
        const targetBall = directBall ?? (!hasNonBallSolid && allBalls.length === 1 ? allBalls[0] : undefined);
        if (targetBall?.anchor && targetBall.radius_sq) {
          const I = parseFracVec3(targetBall.anchor);
          const p0 = parseFracVec3(obj.point);
          const nVec = parseFracVec3(obj.normal);
          const proj = projectPointOntoPlaneExact(I, p0, nVec, scene.chart_metric);
          if (proj) {
            const diff = vSub(proj.foot, I);
            const d2 = metricDot(diff, diff, scene.chart_metric);
            const R2 = parseExactFrac(targetBall.radius_sq);
            if (d2[0] * R2[1] > R2[0] * d2[1]) {
              const pName = formatPlaneDisplayNotation(obj);
              contradictions.push({
                objectId: obj.id,
                title: "Mặt phẳng không cắt mặt cầu",
                explanation: `Khoảng cách từ tâm mặt cầu đến mặt phẳng ${pName} lớn hơn bán kính mặt cầu nên mặt phẳng không cắt mặt cầu.`,
              });
            }
          }
        }
      }
    }

    // 5. Kiểm tra thiết diện tròn / elip trên khối tròn xoay (Case 4: mặt cầu, hình trụ, hình nón)
    if (obj.type === "circle3" && obj.surface_role !== "BASE_REGION" && obj.center && obj.normal && obj.radius_sq) {
      const depObjs = (obj.depends ?? []).map((id) => byId.get(id)).filter((x): x is SceneObject => Boolean(x));
      const curvedDep = depObjs.find((d) => d.type === "curved_solid");
      const planeDep = depObjs.find((d) => d.type === "plane3" && Boolean(d.point && d.normal));
      const r2 = parseExactFrac(obj.radius_sq);
      if (r2[0] <= 0n) {
        contradictions.push({
          objectId: obj.id,
          title: "Đường tròn thiết diện suy biến",
          explanation: "Bán kính đường tròn thiết diện không dương nên không tạo thành đường tròn thực.",
        });
      } else if (curvedDep && planeDep?.point && planeDep.normal) {
        const H = parseFracVec3(obj.center);
        const p0 = parseFracVec3(planeDep.point);
        const nVec = parseFracVec3(planeDep.normal);
        const pName = formatPlaneDisplayNotation(planeDep);
        if (!vIsZero(nVec) && !fIsZero(plainDotFrac(vSub(H, p0), nVec))) {
          contradictions.push({
            objectId: obj.id,
            title: "Tâm thiết diện tròn lệch khỏi mặt phẳng cắt",
            explanation: `Tâm của đường tròn thiết diện không nằm trên mặt phẳng cắt ${pName}.`,
          });
        } else if (curvedDep.curved_kind === "ball" && curvedDep.anchor && curvedDep.radius_sq && !vIsZero(nVec)) {
          const I = parseFracVec3(curvedDep.anchor);
          const R2 = parseExactFrac(curvedDep.radius_sq);
          const IH = vSub(H, I);
          const d2 = metricDot(IH, IH, scene.chart_metric);
          const piv = !fIsZero(nVec[0]) ? 0 : !fIsZero(nVec[1]) ? 1 : 2;
          const i1 = (piv + 1) % 3;
          const i2 = (piv + 2) % 3;
          const t1: [Frac, Frac, Frac] = [[0n, 1n], [0n, 1n], [0n, 1n]];
          t1[i1] = nVec[piv];
          t1[piv] = [-nVec[i1][0], nVec[i1][1]];
          const t2: [Frac, Frac, Frac] = [[0n, 1n], [0n, 1n], [0n, 1n]];
          t2[i2] = nVec[piv];
          t2[piv] = [-nVec[i2][0], nVec[i2][1]];
          const ihPerpPlane =
            vIsZero(IH)
            || (fIsZero(metricDot(IH, t1, scene.chart_metric)) && fIsZero(metricDot(IH, t2, scene.chart_metric)));
          if (!ihPerpPlane) {
            contradictions.push({
              objectId: obj.id,
              title: "Mâu thuẫn chân đường vuông góc từ tâm mặt cầu",
              explanation: `Đoạn nối tâm mặt cầu tới tâm đường tròn thiết diện không vuông góc với mặt phẳng cắt ${pName}.`,
            });
          } else if (!fEq(fAdd(d2, r2), R2)) {
            contradictions.push({
              objectId: obj.id,
              title: "Mâu thuẫn hệ thức mặt cầu cắt mặt phẳng",
              explanation: `Bán kính thiết diện tròn không thỏa hệ thức Pythagoras d² + r² = R² (${fmtFrac(d2)} + ${fmtFrac(r2)} ≠ ${fmtFrac(R2)}).`,
            });
          }
        } else if (
          (curvedDep.curved_kind === "cylinder" || curvedDep.curved_kind === "cone")
          && curvedDep.anchor
          && curvedDep.apex_or_top
          && curvedDep.radius_sq
        ) {
          const A = parseFracVec3(curvedDep.anchor);
          const T = parseFracVec3(curvedDep.apex_or_top);
          const ax = vSub(T, A);
          const R2 = parseExactFrac(curvedDep.radius_sq);
          const ortho = inspectAxialCurvedOrthogonality(scene, curvedDep);
          if (!vIsZero(ax) && !vIsZero(vCross(vSub(H, A), ax))) {
            contradictions.push({
              objectId: obj.id,
              title: "Tâm đường tròn thiết diện lệch khỏi trục",
              explanation: "Tâm của đường tròn thiết diện không nằm trên trục của khối tròn xoay.",
            });
          } else if (
            curvedDep.curved_kind === "cylinder"
            && ortho.isRightCertified
            && vParallel(parseFracVec3(obj.normal), ax)
            && !fEq(r2, R2)
          ) {
            contradictions.push({
              objectId: obj.id,
              title: "Mâu thuẫn bán kính thiết diện tròn của hình trụ đứng",
              explanation: `Mặt phẳng vuông góc trục cắt hình trụ đứng bắt buộc theo đường tròn bán kính r = R (r² = ${fmtFrac(r2)} ≠ R² = ${fmtFrac(R2)}).`,
            });
          } else if (
            curvedDep.curved_kind === "cone"
            && ortho.isRightCertified
            && vParallel(parseFracVec3(obj.normal), ax)
          ) {
            const SH = vSub(H, T);
            const SO = vSub(A, T);
            const sh2 = metricDot(SH, SH, scene.chart_metric);
            const so2 = metricDot(SO, SO, scene.chart_metric);
            if (!fEq(fMul(r2, so2), fMul(R2, sh2))) {
              contradictions.push({
                objectId: obj.id,
                title: "Mâu thuẫn tỉ số đồng dạng khi cắt hình nón song song đáy",
                explanation: `Bán kính thiết diện tròn song song mặt đáy hình nón không thỏa r²/R² = SH²/SO².`,
              });
            }
          }
        }
      }
    }

    if (
      obj.type === "ellipse3"
      && obj.center
      && obj.major_dir
      && obj.minor_dir
      && obj.semi_major_sq
      && obj.semi_minor_sq
    ) {
      const a2 = parseExactFrac(obj.semi_major_sq);
      const b2 = parseExactFrac(obj.semi_minor_sq);
      const uMaj = parseFracVec3(obj.major_dir);
      const uMin = parseFracVec3(obj.minor_dir);
      const depObjs = (obj.depends ?? []).map((id) => byId.get(id)).filter((x): x is SceneObject => Boolean(x));
      const curvedDep = depObjs.find((d) => d.type === "curved_solid");
      const planeDep = depObjs.find((d) => d.type === "plane3" && Boolean(d.point && d.normal));
      if (a2[0] <= 0n || b2[0] <= 0n || a2[0] * b2[1] < b2[0] * a2[1]) {
        contradictions.push({
          objectId: obj.id,
          title: "Mâu thuẫn bán trục elip thiết diện",
          explanation: `Elip thiết diện vi phạm điều kiện bán trục lớn a ≥ b > 0 (a² = ${fmtFrac(a2)}, b² = ${fmtFrac(b2)}).`,
        });
      } else if (!fIsZero(metricDot(uMaj, uMin, scene.chart_metric))) {
        contradictions.push({
          objectId: obj.id,
          title: "Hai trục chính của elip không vuông góc",
          explanation: "Phương trục lớn và phương trục nhỏ của elip thiết diện không vuông góc nhau.",
        });
      } else if (planeDep?.point && planeDep.normal) {
        const H = parseFracVec3(obj.center);
        const p0 = parseFracVec3(planeDep.point);
        const nVec = parseFracVec3(planeDep.normal);
        const pName = formatPlaneDisplayNotation(planeDep);
        if (
          !vIsZero(nVec)
          && (
            !fIsZero(plainDotFrac(vSub(H, p0), nVec))
            || !fIsZero(plainDotFrac(uMaj, nVec))
            || !fIsZero(plainDotFrac(uMin, nVec))
          )
        ) {
          contradictions.push({
            objectId: obj.id,
            title: "Elip thiết diện không thuộc mặt phẳng cắt",
            explanation: `Tâm hoặc trục của elip thiết diện lệch khỏi mặt phẳng cắt ${pName}.`,
          });
        } else if (
          curvedDep?.curved_kind === "cylinder"
          && curvedDep.anchor
          && curvedDep.apex_or_top
          && curvedDep.radius_sq
          && inspectAxialCurvedOrthogonality(scene, curvedDep).isRightCertified
        ) {
          const ax = vSub(parseFracVec3(curvedDep.apex_or_top), parseFracVec3(curvedDep.anchor));
          const R2 = parseExactFrac(curvedDep.radius_sq);
          if (fIsZero(plainDotFrac(ax, nVec))) {
            contradictions.push({
              objectId: obj.id,
              title: "Mặt phẳng song song trục không tạo thiết diện elip kín",
              explanation: `Mặt phẳng ${pName} song song với trục hình trụ nên giao tuyến là các đường sinh, không thể là elip kín.`,
            });
          } else if (!fEq(b2, R2)) {
            contradictions.push({
              objectId: obj.id,
              title: "Mâu thuẫn bán trục nhỏ elip khi cắt xiên hình trụ đứng",
              explanation: `Khi cắt xiên hình trụ tròn xoay bán kính R, bán trục nhỏ của elip bắt buộc bằng R (b² = ${fmtFrac(b2)} ≠ R² = ${fmtFrac(R2)}).`,
            });
          }
        }
      }
    }

    // 6. Kiểm tra ranh giới hình trụ xiên vs hình trụ đứng (Case 5 & §5.2: không gán tính chất vuông góc đáy hay công thức V = πR²·OO′ cho hình trụ xiên / trục chưa vuông góc đáy)
    if (obj.type === "curved_solid" && obj.curved_kind === "cylinder") {
      const ortho = inspectAxialCurvedOrthogonality(scene, obj);
      if (ortho.isOblique) {
        for (const seg of scene.objects) {
          if (isSubEntity(seg.id) || (seg.type !== "segment3" && seg.type !== "line3")) continue;
          const cRole = classifyCurvedSegmentRole(scene, seg);
          if (cRole?.host.id !== obj.id) continue;
          if (
            (cRole.kind === "center_line" || cRole.kind === "generator")
            && ((seg.formation_roles ?? []).includes("CONSTRUCT_HEIGHT") || Boolean(seg.perpendicular_witness))
          ) {
            contradictions.push({
              objectId: seg.id,
              title: "Mâu thuẫn tính chất hình trụ xiên",
              explanation: `Trong hình trụ xiên, ${cRole.kind === "center_line" ? "đường nối tâm hai đáy" : "đường sinh"} ${shortSym(seg)} nghiêng với mặt phẳng đáy nên không vuông góc với đáy và không bằng chiều cao h.`,
            });
          }
        }
        const hasCertifiedAltitudeSeg = scene.objects.some(
          (seg) =>
            !isSubEntity(seg.id)
            && (seg.type === "segment3" || seg.type === "line3")
            && classifyCurvedSegmentRole(scene, seg)?.host.id === obj.id
            && classifyCurvedSegmentRole(scene, seg)?.kind === "altitude",
        );
        const axSq =
          obj.anchor && obj.apex_or_top
            ? metricDot(
                vSub(parseFracVec3(obj.apex_or_top), parseFracVec3(obj.anchor)),
                vSub(parseFracVec3(obj.apex_or_top), parseFracVec3(obj.anchor)),
                scene.chart_metric,
              )
            : null;
        const rSq = obj.radius_sq ? parseExactFrac(obj.radius_sq) : null;
        const rightVolSqPi =
          axSq && rSq ? fMul(fMul(rSq, rSq), axSq) : null;
        for (const q of scene.objects) {
          if (q.type !== "quantity") continue;
          const qDeps = [...new Set([...(q.depends ?? []), ...(q.annotation?.subject_ids ?? [])])];
          if (!qDeps.includes(obj.id)) continue;
          const prod = `${q.producer ?? ""} ${q.source?.instruction ?? ""}`;
          const isVolOrLateral =
            /\b(volume|lateral_area)\b/iu.test(prod)
            || q.annotation?.kind === "volume"
            || /\bthể\s+tích\b/iu.test(q.label ?? "")
            || /\bdiện\s+tích\s+xung\s+quanh\b/iu.test(q.label ?? "");
          if (!isVolOrLateral) continue;
          let matchesWrongRightFormula = !hasCertifiedAltitudeSeg;
          if (!matchesWrongRightFormula && rightVolSqPi && q.exact && typeof q.exact === "object") {
            const ex = q.exact as { kind?: string; pi?: boolean; value?: string; coefficient?: string; radicand?: number };
            if (ex.kind === "rational" && ex.pi && ex.value) {
              const c = parseExactFrac(ex.value);
              if (fEq(fMul(c, c), rightVolSqPi)) matchesWrongRightFormula = true;
            } else if (ex.kind === "radical" && ex.pi && ex.coefficient && typeof ex.radicand === "number") {
              const c = parseExactFrac(ex.coefficient);
              if (fEq(fMul(fMul(c, c), [BigInt(ex.radicand), 1n]), rightVolSqPi)) {
                matchesWrongRightFormula = true;
              }
            }
          }
          if (matchesWrongRightFormula) {
            contradictions.push({
              objectId: q.id,
              title: "Áp dụng sai công thức trụ đứng cho hình trụ trục không vuông góc đáy",
              explanation: `Đoạn nối tâm hai đáy không vuông góc với mặt phẳng đáy (hoặc chưa đủ giả thiết chứng minh vuông góc đáy) nên độ dài nối tâm không phải chiều cao h; không được áp dụng công thức trụ đứng V = πR²·OO′ hay Sxq = 2πR·OO′.`,
            });
          }
        }
      }
    }
  }

  const result: SceneMathVerificationResult = {
    valid: contradictions.length === 0,
    contradictions,
  };
  _mathVerifyCache.set(scene as object, { sig, result });
  return result;
}

export function findLinePlaneIntersectionMidpoint(
  scene: Pick<Scene3D, "objects">,
  ptObj: SceneObject,
): {
  lineSym: string;
  planeSym: string;
  segA?: string;
  segB?: string;
  isMidpoint: boolean;
  isCoincidentEndpoint: boolean;
  coincidentSym?: string;
  isInterior: boolean;
  isExterior: boolean;
  ratioFrac?: Frac;
} | null {
  if (ptObj.type !== "point3" || !ptObj.xyz || (ptObj.depends ?? []).length !== 2) return null;
  const exactScene = exactSceneOriginOf(scene);
  const byId = new Map(scene.objects.map((o) => [o.id, o]));
  const exactById = new Map(exactScene.objects.map((o) => [o.id, o]));
  const exactPt = exactById.get(ptObj.id) ?? ptObj;
  if (!exactPt.xyz) return null;
  const depObjs = (ptObj.depends ?? []).map((id) => byId.get(id) ?? exactById.get(id));
  const ln = depObjs.find((o) => o?.type === "line3" || o?.type === "segment3");
  const pl = depObjs.find((o) => o?.type === "plane3");
  if (!ln || !pl) return null;
  const exactLn = exactById.get(ln.id) ?? ln;
  const endPts = (exactLn.depends ?? ln.depends ?? [])
    .map((id) => exactById.get(id) ?? byId.get(id))
    .filter((o): o is SceneObject => Boolean(o && o.type === "point3" && o.xyz));
  let segA: string | undefined;
  let segB: string | undefined;
  let isMidpoint = false;
  let isCoincidentEndpoint = false;
  let coincidentSym: string | undefined;
  let isInterior = false;
  let isExterior = false;
  let ratioFrac: Frac | undefined;
  if (endPts.length === 2) {
    const [u, v] = endPts;
    const uSym = shortSym(byId.get(u.id) ?? u);
    const vSym = shortSym(byId.get(v.id) ?? v);
    const apexSyms = structuralApexSymsOfScene(exactScene);
    const firstObj = apexSyms.has(uSym) && !apexSyms.has(vSym)
      ? u
      : apexSyms.has(vSym) && !apexSyms.has(uSym)
        ? v
        : u;
    const secondObj = firstObj === u ? v : u;
    segA = firstObj === u ? uSym : vSym;
    segB = firstObj === u ? vSym : uSym;
    const t = exactCollinearParam(exactPt.xyz, firstObj.xyz!, secondObj.xyz!);
    if (t !== null) {
      isMidpoint = t[0] === 1n && t[1] === 2n;
      if (fIsZero(t)) {
        isCoincidentEndpoint = true;
        coincidentSym = segA;
      } else if (fEq(t, [1n, 1n])) {
        isCoincidentEndpoint = true;
        coincidentSym = segB;
      }
      isInterior = t[0] >= 0n && t[0] <= t[1];
      isExterior = t[0] < 0n || t[0] > t[1];
      ratioFrac = t;
    } else {
      isMidpoint = isExactMidpointVec(exactPt.xyz, u.xyz!, v.xyz!);
      isInterior = isMidpoint;
    }
  }
  const planeNotation = pl.notation?.trim() || shortSym(pl);
  return {
    lineSym: segA && segB && segA.length <= 2 && segB.length <= 2 ? `${segA}${segB}` : shortSym(ln),
    planeSym: planeNotation.startsWith("(") ? planeNotation : `(${planeNotation})`,
    segA,
    segB,
    isMidpoint,
    isCoincidentEndpoint,
    coincidentSym,
    isInterior,
    isExterior,
    ratioFrac,
  };
}

export interface PolygonDiagnostics {
  edgeCount: number;
  boundaryConnected: boolean;
  coplanar: boolean;
  nonDegenerate: boolean;
  faceIncidences: string[];
}

export interface ExactPolygonMathBasis {
  /** Kết luận hình dạng ĐƯỢC CHỨNG MINH từ dữ kiện & quan hệ đã xác nhận (không nâng quan hệ chỉ đúng trên một cấu hình tọa độ thành định lý). */
  shape: string | null;
  /** Hình dạng quan sát trên cấu hình tọa độ cụ thể hiện tại (có thể hẹp hơn `shape` khi thiếu giả thiết vuông góc / độ dài). */
  coordinateShape: string | null;
  /** Cấp độ nhận thức của kết luận chính (`GIVEN` | `DERIVED` | `COORDINATE_CONFIGURATION_ONLY` | `INSUFFICIENT_PREMISES`). */
  epistemicLevel: EpistemicConclusionLevel;
  cycleNotation: string | null;
  parallelPairs: string[];
  metricFacts: string[];
  /** Các quan hệ chỉ thỏa trên cấu hình tọa độ hiện hành nhưng CHƯA đủ dữ kiện đề bài để kết luận tổng quát. */
  coordinateOnlyFacts: string[];
  /** Giải thích rõ thuộc tính nào chưa xác định do thiếu giả thiết (vd thiếu đường cao / cạnh bên vuông góc mặt đáy). */
  undeterminedAspects: string[];
  /** Chuỗi tiền đề hỗ trợ kết luận. */
  supportingPremises: string[];
  /** Kiểm tra cấu trúc đa giác theo §5 (số cạnh, liên thông, đồng phẳng, không suy biến, quan hệ với mặt khối). */
  diagnostics: PolygonDiagnostics;
  summary: string;
}

/**
 * Xác định xem các quan hệ metric ngoài mặt đáy (góc vuông & độ dài cạnh xiên trên thiết diện cắt xiên qua khối)
 * có được chứng nhận bởi tiền đề hình học tường minh trong `scene.objects` hay không:
 * - Mặt đáy (`BASE_REGION`) có metric được cho trực tiếp từ giả thiết đáy (`GIVEN`).
 * - Thiết diện nằm trên mặt phẳng song song với `BASE_REGION` thừa hưởng trực tiếp góc và tỉ số độ dài từ `BASE_REGION` (`DERIVED` qua phép vị tự / tịnh tiến song song đáy).
 * - Thiết diện cắt xiên qua mặt bên chỉ được khẳng định góc vuông hoặc bằng nhau giữa các phương không song song khi có
 *   nhân chứng vuông góc tường minh (`perpendicular_witness` đường ⊥ đáy đã kiểm chứng) hoặc đối xứng trục của khối tròn xoay (`cone` / `cylinder`).
 * - Nếu không có các tiền đề này (ví dụ chỉ cho đáy ABCD là hình vuông và M là trung điểm SC, dù tọa độ mẫu đặt S=(0,0,1)),
 *   tuyệt đối KHÔNG tự động kết luận "hình thang vuông".
 */
function inspectPolygonMetricCertification(
  scene: Scene3D,
  polyObj: SceneObject,
  polyNormal: FracVec3,
): {
  isBaseRegion: boolean;
  isBaseMetricCertified: boolean;
  hasAnyMetricCertifiedBase: boolean;
  parallelToCertifiedBase: boolean;
  parallelBaseProvenShape: string | null;
  parallelBaseSideCount: number | null;
  hasCertifiedVerticalWitness: boolean;
  certifiedVerticalDirs: FracVec3[];
  hasCertifiedConeSymmetry: boolean;
  supportingPremises: string[];
} {
  const byId = new Map(scene.objects.map((o) => [o.id, o]));
  const roles = polyObj.formation_roles ?? [];
  const isBaseRegion = polyObj.surface_role === "BASE_REGION" || roles.includes("CONSTRUCT_BASE");
  const supportingPremises: string[] = [];
  const gMetric = isSceneWorldTransformed(scene) ? undefined : scene.chart_metric;

  let isBaseMetricCertified = false;
  if (isBaseRegion) {
    const selfPts = polyObj.polygon ?? polyObj.vertices ?? [];
    const selfProv = classifyPolygonShapeWithProvenance(scene, polyObj);
    const selfCoord = classifyExactPolygonShape(selfPts, gMetric);
    isBaseMetricCertified =
      (selfProv.provenance === "GIVEN" || selfProv.provenance === "DERIVED_VERIFIED")
      && selfProv.certifiedShape !== null
      && selfProv.certifiedShape === selfCoord;
  }

  const baseVertexIds = new Set<string>();
  const pSample = (polyObj.polygon ?? polyObj.vertices)?.[0];
  let parallelToCertifiedBase = false;
  let hasAnyMetricCertifiedBase = false;
  let parallelBaseProvenShape: string | null = null;
  let parallelBaseSideCount: number | null = null;
  for (const base of scene.objects) {
    if (isSubEntity(base.id) || base.surface_role !== "BASE_REGION") continue;
    for (const vid of [...(base.depends ?? []), ...(base.vertex_ids ?? [])]) baseVertexIds.add(vid);
    const bPts = base.polygon ?? base.vertices;
    if (!bPts || bPts.length < 3) continue;
    const baseProv = classifyPolygonShapeWithProvenance(scene, base);
    const bShape = classifyScenePolygonShape(scene, base);
    const bCoordShape = classifyExactPolygonShape(bPts, gMetric);
    const baseIsCertified =
      (baseProv.provenance === "GIVEN" || baseProv.provenance === "DERIVED_VERIFIED")
      && baseProv.certifiedShape !== null
      && baseProv.certifiedShape === bCoordShape;
    if (baseIsCertified) hasAnyMetricCertifiedBase = true;
    const depNames = (base.depends ?? []).map((id) => shortSym(byId.get(id))).filter(Boolean);
    const cyc = depNames.length >= 3
      ? canonicalizeCycleNames(depNames, preferredPointOrderForPolygon(scene, base)).join("")
      : shortSym(base);
    if (baseProv.certifiedShape && (baseProv.provenance === "GIVEN" || baseProv.provenance === "DERIVED_VERIFIED")) {
      supportingPremises.push(`Đáy ${cyc} là ${baseProv.certifiedShape} (đề cho)`);
    }
    const b0 = parseFracVec3(bPts[0]);
    const bNormal = vCross(vSub(parseFracVec3(bPts[1]), b0), vSub(parseFracVec3(bPts[2]), b0));
    const strictlyParallel =
      isBaseRegion
      || !pSample
      || !fIsZero(plainDotFrac(vSub(parseFracVec3(pSample), b0), bNormal));
    if (!vIsZero(polyNormal) && !vIsZero(bNormal) && vParallel(polyNormal, bNormal) && strictlyParallel) {
      parallelBaseProvenShape = bShape;
      parallelBaseSideCount = bPts.length;
      if (baseIsCertified) {
        parallelToCertifiedBase = true;
      }
      if (!isBaseRegion) {
        supportingPremises.push(`Mặt phẳng đa giác song song với mặt đáy (${cyc})`);
      }
    }
  }

  let hasCertifiedVerticalWitness = false;
  const certifiedVerticalDirs: FracVec3[] = [];
  for (const o of scene.objects) {
    if (isSubEntity(o.id) || !o.perpendicular_witness) continue;
    const w = o.perpendicular_witness;
    const onObj = w.on ? byId.get(w.on) : undefined;
    const isLinePlaneWitness =
      isLinePerpPlaneRelation(w.relation)
      || Boolean(w.plane_directions && w.plane_directions.length >= 2)
      || onObj?.surface_role === "BASE_REGION"
      || (o.formation_roles ?? []).includes("CONSTRUCT_HEIGHT");
    if (!isLinePlaneWitness || !w.marker?.v) continue;
    const vPerp = parseFracVec3(w.marker.v);
    if (vIsZero(vPerp)) continue;
    const dirsOk = (w.plane_directions ?? []).every((pd) =>
      fIsZero(metricDot(vPerp, parseFracVec3(pd), scene.chart_metric)),
    );
    if (!dirsOk) continue;
    const footPt = w.foot_id
      ? byId.get(w.foot_id)
      : w.foot
        ? scene.objects.find((cand) => !isSubEntity(cand.id) && cand.type === "point3" && cand.xyz?.join("|") === w.foot!.join("|"))
        : undefined;
    const footGrounded =
      !footPt
      || footPt.origin === "derived"
      || baseVertexIds.has(footPt.id)
      || baseVertexIds.size === 0;
    if (!footGrounded) continue;
    hasCertifiedVerticalWitness = true;
    certifiedVerticalDirs.push(vPerp);
    const onSym = onObj?.notation
      ? (onObj.notation.startsWith("(") ? onObj.notation : `(${onObj.notation})`)
      : shortSym(onObj) || "mặt đáy";
    supportingPremises.push(`${shortSym(o)} ⊥ ${onSym} (giả thiết vuông góc đã xác nhận)`);
  }

  const hasCertifiedConeSymmetry = scene.objects.some(
    (s) => s.type === "curved_solid" && s.curved_kind === "cone" && Boolean(s.anchor && s.apex_or_top && s.radius_sq),
  );
  if (hasCertifiedConeSymmetry && !isBaseRegion) {
    supportingPremises.push("Các đường sinh của hình nón tròn xoay có độ dài bằng nhau");
  }

  if (!isBaseRegion && !vIsZero(polyNormal)) {
    for (const s of scene.objects) {
      if (
        s.type !== "curved_solid"
        || (s.curved_kind !== "cylinder" && s.curved_kind !== "cone")
        || !s.anchor
        || !s.apex_or_top
        || !s.radius_sq
      ) {
        continue;
      }
      const ax = vSub(parseFracVec3(s.apex_or_top), parseFracVec3(s.anchor));
      if (vIsZero(ax)) continue;
      if (
        s.curved_kind === "cylinder"
        && inspectAxialCurvedOrthogonality(scene, s).isRightCertified
        && fIsZero(metricDot(polyNormal, ax, scene.chart_metric))
      ) {
        hasCertifiedVerticalWitness = true;
        certifiedVerticalDirs.push(ax);
        supportingPremises.push("Các đường sinh của hình trụ tròn xoay vuông góc với hai mặt đáy tròn");
      }
    }
  }

  return {
    isBaseRegion,
    isBaseMetricCertified,
    hasAnyMetricCertifiedBase,
    parallelToCertifiedBase,
    parallelBaseProvenShape,
    parallelBaseSideCount,
    hasCertifiedVerticalWitness,
    certifiedVerticalDirs,
    hasCertifiedConeSymmetry,
    supportingPremises,
  };
}

/**
 * Suy dẫn cơ sở toán học chính xác trên Q^3 (tôn trọng `chart_metric`) cho một đa giác / thiết diện:
 * - Kiểm tra đầy đủ số cạnh, tính liên thông đường bao, đồng phẳng, không suy biến, cạnh song song,
 *   cạnh vuông góc, độ dài bằng nhau, thứ tự chu trình đỉnh và giao tuyến với từng mặt khối (§5).
 * - Phân biệt nghiêm ngặt 4 tầng nhận thức (`GIVEN`, `DERIVED`, `COORDINATE_CONFIGURATION_ONLY`, `INSUFFICIENT_PREMISES`):
 *   tuyệt đối không nâng một quan hệ chỉ thỏa số trên một cấu hình tọa độ thành kết luận tổng quát khi thiếu giả thiết.
 */
export function deriveExactPolygonMathBasis(
  rawScene: Scene3D,
  rawPolyObj: SceneObject,
): ExactPolygonMathBasis | null {
  const scene = exactSceneOriginOf(rawScene);
  const polyObj = scene === rawScene ? rawPolyObj : (scene.objects.find((o) => o.id === rawPolyObj.id) ?? rawPolyObj);
  const rawPts = polyObj.polygon ?? polyObj.vertices ?? [];
  const n = rawPts.length;
  if (n < 3) return null;

  const byId = new Map(scene.objects.map((o) => [o.id, o]));
  const coordMap = new Map<string, SceneObject | null>();
  for (const o of scene.objects) {
    if (isSubEntity(o.id) || o.type !== "point3" || !o.xyz || laDiemPhuDungMatPhang(scene, o, byId)) continue;
    const key = o.xyz.join("|");
    coordMap.set(key, coordMap.has(key) ? null : o);
  }

  let rawNames: string[] = [];
  if (polyObj.type === "section") {
    const sd = sectionDetails(scene, polyObj.id);
    rawNames = sd ? [...sd.vertexNames] : rawPts.map((pt, idx) => shortSym(coordMap.get(pt.join("|")) ?? undefined) || `Đỉnh ${idx + 1}`);
  } else {
    rawNames = rawPts.map((pt, idx) => {
      const matched = coordMap.get(pt.join("|"));
      if (matched && isCompactPointSym(shortSym(matched))) return shortSym(matched);
      const depObj = polyObj.depends?.[idx] ? byId.get(polyObj.depends[idx]) : undefined;
      return depObj?.type === "point3" && !laDiemPhuDungMatPhang(scene, depObj, byId) && isCompactPointSym(shortSym(depObj))
        ? shortSym(depObj)
        : `Đỉnh ${idx + 1}`;
    });
  }

  const prefOrder = preferredPointOrderForPolygon(scene, polyObj);
  const allNamed = rawNames.length === n && rawNames.every((nm) => Boolean(nm) && nm.length <= 3 && !/^Đỉnh\s+\d+$/u.test(nm));

  let pts: ExactVec3[] = [...rawPts];
  let names: string[] = [...rawNames];
  let cycleNotation: string | null = null;

  if (allNamed) {
    const targetCanon = canonicalizeCycleNames(rawNames, prefOrder);
    const revNames = [...rawNames].reverse();
    const revPts = [...rawPts].reverse();
    for (let shift = 0; shift < n; shift += 1) {
      const candFwd = Array.from({ length: n }, (_, k) => rawNames[(shift + k) % n]);
      if (candFwd.every((v, idx) => v === targetCanon[idx])) {
        names = candFwd;
        pts = Array.from({ length: n }, (_, k) => rawPts[(shift + k) % n]);
        break;
      }
      const candRev = Array.from({ length: n }, (_, k) => revNames[(shift + k) % n]);
      if (candRev.every((v, idx) => v === targetCanon[idx])) {
        names = candRev;
        pts = Array.from({ length: n }, (_, k) => revPts[(shift + k) % n]);
        break;
      }
    }
    cycleNotation = `(${names.join("")})`;
  }

  const v = pts.map(parseFracVec3);
  const edges = v.map((cur, i) => vSub(v[(i + 1) % n], cur));
  const sqLens = edges.map((e) => metricDot(e, e, scene.chart_metric));
  const boundaryConnected = polyObj.closed !== false && sqLens.every((l) => l[0] > 0n);

  let areaVec: FracVec3 = [
    [0n, 1n],
    [0n, 1n],
    [0n, 1n],
  ];
  for (let i = 1; i + 1 < n; i += 1) {
    areaVec = vAdd(areaVec, vCross(vSub(v[i], v[0]), vSub(v[i + 1], v[0])));
  }
  const nonDegenerate = boundaryConnected && !vIsZero(areaVec);
  const coplanar = nonDegenerate && v.every((vx) => fIsZero(plainDotFrac(vSub(vx, v[0]), areaVec)));
  if (!nonDegenerate || !coplanar) return null;

  const coordinateShape = classifyExactPolygonShape(pts, scene.chart_metric);
  const cert = inspectPolygonMetricCertification(scene, polyObj, areaVec);
  const hasAnyPolyBase = scene.objects.some(
    (b) => !isSubEntity(b.id) && b.surface_role === "BASE_REGION" && b.type === "polygon3",
  );
  const isParallelToPolyBase = !cert.isBaseRegion && cert.parallelBaseProvenShape !== null;
  const metricCertified = cert.isBaseRegion
    ? cert.isBaseMetricCertified
    : isParallelToPolyBase
      ? cert.parallelToCertifiedBase
      : (cert.hasCertifiedVerticalWitness && (!hasAnyPolyBase || cert.hasAnyMetricCertifiedBase))
        || (n === 3 && cert.hasCertifiedConeSymmetry);

  const edgeNames = allNamed ? names.map((nm, i) => `${nm}${names[(i + 1) % n]}`) : [];

  // Tập các cạnh có tên của khối đa diện chủ để kiểm tra quan hệ song song & giao tuyến mặt khối
  const solids = scene.objects.filter((o) => o.type === "solid" && o.faces && o.vertex_ids && o.vertices);
  const hostSolidId = (polyObj.depends ?? []).find((id) => byId.get(id)?.type === "solid");
  solids.sort((sa, sb) => (sa.id === hostSolidId ? -1 : sb.id === hostSolidId ? 1 : 0));

  interface FacePlane {
    p0: FracVec3;
    cov: FracVec3;
  }
  interface NamedSolidEdge {
    uSym: string;
    vSym: string;
    a: FracVec3;
    b: FracVec3;
    dir: FracVec3;
    facePlanes: FacePlane[];
  }

  const solidEdges: NamedSolidEdge[] = [];
  const edgeByKey = new Map<string, NamedSolidEdge>();
  for (const s of solids) {
    const vIds = s.vertex_ids!;
    const vCoords = s.vertices!;
    const orderedFaces = [...s.faces!].sort((fa, fb) => fb.length - fa.length);
    for (const face of orderedFaces) {
      let facePlane: FacePlane | null = null;
      if (face.length >= 3 && vCoords[face[0]]) {
        const p0 = parseFracVec3(vCoords[face[0]]);
        for (let k = 1; k + 1 < face.length; k += 1) {
          if (!vCoords[face[k]] || !vCoords[face[k + 1]]) continue;
          const cov = vCross(
            vSub(parseFracVec3(vCoords[face[k]]), p0),
            vSub(parseFracVec3(vCoords[face[k + 1]]), p0),
          );
          if (!vIsZero(cov)) {
            facePlane = { p0, cov };
            break;
          }
        }
      }
      for (let i = 0; i < face.length; i += 1) {
        const ia = face[i];
        const ib = face[(i + 1) % face.length];
        const idA = vIds[ia];
        const idB = vIds[ib];
        if (!idA || !idB || !vCoords[ia] || !vCoords[ib]) continue;
        const pairKey = idA < idB ? `${idA}|${idB}` : `${idB}|${idA}`;
        let entry = edgeByKey.get(pairKey);
        if (!entry) {
          const uSym = shortSym(byId.get(idA));
          const vSym = shortSym(byId.get(idB));
          if (!uSym || !vSym || uSym.length > 3 || vSym.length > 3) continue;
          const aPos = parseFracVec3(vCoords[ia]);
          const bPos = parseFracVec3(vCoords[ib]);
          entry = {
            uSym,
            vSym,
            a: aPos,
            b: bPos,
            dir: vSub(bPos, aPos),
            facePlanes: [],
          };
          edgeByKey.set(pairKey, entry);
          solidEdges.push(entry);
        }
        if (facePlane) entry.facePlanes.push(facePlane);
      }
    }
  }

  const hostSolid = solids[0];
  const faceIncidences: string[] = [];
  const partialEdgeLabels: (string | null)[] = pts.map((ptA, idx) => {
    const nA = names[idx];
    const nB = names[(idx + 1) % n];
    const okA = Boolean(nA) && nA.length <= 3 && !/^Đỉnh\s+\d+$/u.test(nA);
    const okB = Boolean(nB) && nB.length <= 3 && !/^Đỉnh\s+\d+$/u.test(nB);
    const ptB = pts[(idx + 1) % n];
    const keyAB = `${ptA.join("|")}->${ptB.join("|")}`;
    const keyBA = `${ptB.join("|")}->${ptA.join("|")}`;
    const stepMatch = (polyObj.steps ?? []).find((st) => {
      const sk = `${st.a.join("|")}->${st.b.join("|")}`;
      return sk === keyAB || sk === keyBA;
    });
    let faceNot: string | null = null;
    if (stepMatch && stepMatch.face_index !== null && hostSolid?.faces?.[stepMatch.face_index] && hostSolid.vertex_ids) {
      const fSyms = hostSolid.faces[stepMatch.face_index]
        .map((vi) => shortSym(byId.get(hostSolid.vertex_ids![vi])))
        .filter(Boolean);
      faceNot = formatCycleNotation(fSyms, [...structuralApexSymsOfScene(scene), ...preferredPointOrderForPolygon(scene, hostSolid)]);
    }
    if (okA && okB) {
      const seg = `${nA}${nB}`;
      if (faceNot) faceIncidences.push(`${seg} ⊂ ${faceNot}`);
      return seg;
    }
    if (faceNot) {
      faceIncidences.push(`giao tuyến trên ${faceNot}`);
      return `giao tuyến trên ${faceNot}`;
    }
    return null;
  });

  const parallelPairs: string[] = [];
  for (let i = 0; i < n; i += 1) {
    const eLabel = allNamed ? edgeNames[i] : partialEdgeLabels[i];
    if (!eLabel) continue;
    const e = edges[i];
    const pStart = v[i];
    const pEnd = v[(i + 1) % n];
    let bestCoplanar: NamedSolidEdge | null = null;
    let firstParallel: NamedSolidEdge | null = null;
    for (const se of solidEdges) {
      if (!vParallel(e, se.dir)) continue;
      const diffStart = vSub(pStart, se.a);
      if (vIsZero(vCross(diffStart, se.dir))) continue;
      if (!firstParallel) firstParallel = se;
      const sharesSolidFace = se.facePlanes.some(
        (fp) =>
          fIsZero(plainDotFrac(vSub(pStart, fp.p0), fp.cov)) &&
          fIsZero(plainDotFrac(vSub(pEnd, fp.p0), fp.cov)),
      );
      if (sharesSolidFace) {
        bestCoplanar = se;
        break;
      }
    }
    const chosen = bestCoplanar ?? firstParallel;
    if (chosen) {
      const sameDir = metricDot(e, chosen.dir, scene.chart_metric)[0] >= 0n;
      const solidSegSym = sameDir ? `${chosen.uSym}${chosen.vSym}` : `${chosen.vSym}${chosen.uSym}`;
      parallelPairs.push(`${eLabel} ∥ ${solidSegSym}`);
    }
  }
  if (parallelPairs.length === 0 && n >= 4) {
    for (let i = 0; i < n; i += 1) {
      const lblI = allNamed ? edgeNames[i] : partialEdgeLabels[i];
      if (!lblI) continue;
      for (let j = i + 2; j < n; j += 1) {
        if (i === 0 && j === n - 1) continue;
        const lblJ = allNamed ? edgeNames[j] : partialEdgeLabels[j];
        if (!lblJ) continue;
        if (!vParallel(edges[i], edges[j])) continue;
        if (vIsZero(vCross(vSub(v[j], v[i]), edges[i]))) continue;
        const pairStr = `${lblI} ∥ ${lblJ}`;
        if (!parallelPairs.includes(pairStr)) {
          parallelPairs.push(pairStr);
        }
      }
    }
  }

  const isCertifiedRightPair = (eA: FracVec3, eB: FracVec3): boolean => {
    if (!fIsZero(metricDot(eA, eB, scene.chart_metric))) return false;
    if (metricCertified) return true;
    return cert.certifiedVerticalDirs.some(
      (vp) =>
        (vParallel(eA, vp) && fIsZero(metricDot(eB, vp, scene.chart_metric)))
        || (vParallel(eB, vp) && fIsZero(metricDot(eA, vp, scene.chart_metric))),
    );
  };

  // Xác định hình dạng ĐƯỢC CHỨNG MINH (`provenShape`) và các tính chất metric
  let provenShape: string | null = coordinateShape;
  const metricFacts: string[] = [];
  const coordinateOnlyFacts: string[] = [];
  const undeterminedAspects: string[] = [];

  if (!metricCertified) {
    if (cert.isBaseRegion) {
      provenShape = classifyScenePolygonShape(scene, polyObj);
    } else if (cert.parallelBaseProvenShape && cert.parallelBaseSideCount === n) {
      provenShape = cert.parallelBaseProvenShape;
    } else if (n === 4) {
      const opp02 = vIsZero(vAdd(edges[0], edges[2]));
      const opp13 = vIsZero(vAdd(edges[1], edges[3]));
      const par02 = vParallel(edges[0], edges[2]);
      const par13 = vParallel(edges[1], edges[3]);
      const hasRightAdj =
        isCertifiedRightPair(edges[0], edges[1])
        || isCertifiedRightPair(edges[1], edges[2])
        || isCertifiedRightPair(edges[2], edges[3])
        || isCertifiedRightPair(edges[3], edges[0]);
      if (opp02 && opp13) {
        provenShape = hasRightAdj ? "hình chữ nhật" : "hình bình hành";
      } else if (par02 !== par13) {
        provenShape = hasRightAdj ? "hình thang vuông" : "hình thang";
      } else {
        provenShape = "tứ giác";
      }
    } else if (n === 3) {
      const hasCertRightAngle =
        isCertifiedRightPair(edges[2], edges[0])
        || isCertifiedRightPair(edges[0], edges[1])
        || isCertifiedRightPair(edges[1], edges[2]);
      provenShape = hasCertRightAngle ? "tam giác vuông" : "tam giác";
    }
    if (coordinateShape && coordinateShape !== provenShape) {
      const provenAlreadyRight = Boolean(provenShape && provenShape.includes("vuông"));
      coordinateOnlyFacts.push(
        `Cấu hình tọa độ hiện tại có dạng ${coordinateShape}, nhưng đề chưa cho giả thiết ${provenAlreadyRight ? "độ dài" : "vuông góc hoặc độ dài"} tương ứng`,
      );
      if (isParallelToPolyBase && cert.parallelBaseProvenShape) {
        undeterminedAspects.push(
          `mặt đáy chỉ được chứng nhận là ${cert.parallelBaseProvenShape} nên chưa đủ cơ sở kết luận tính đặc biệt hơn của thiết diện`,
        );
      } else if (coordinateShape.includes("vuông") && !provenAlreadyRight) {
        undeterminedAspects.push(
          "chưa đủ giả thiết cạnh bên hoặc đường cao vuông góc với mặt đáy để kết luận góc vuông",
        );
      } else {
        undeterminedAspects.push(
          "chưa đủ giả thiết độ dài hoặc đối xứng của các cạnh bên để kết luận tính cân/đều",
        );
      }
    }
  }

  if (allNamed) {
    if (n === 4) {
      const [s0, s1, s2, s3] = edgeNames;
      const opp02 = vIsZero(vAdd(edges[0], edges[2]));
      const opp13 = vIsZero(vAdd(edges[1], edges[3]));
      const right01 = isCertifiedRightPair(edges[0], edges[1]);
      const eqAdj = metricCertified && fEq(sqLens[0], sqLens[1]);
      if (opp02 && opp13) {
        if (parallelPairs.length === 0) {
          parallelPairs.push(`${s0} ∥ ${s2}`, `${s1} ∥ ${s3}`);
        }
        if (right01 && eqAdj) {
          metricFacts.push(`${s0} = ${s1} = ${s2} = ${s3}`, `${s0} ⊥ ${s1}`);
        } else if (right01) {
          metricFacts.push(`${s0} = ${s2}, ${s1} = ${s3} (${s0} ≠ ${s1})`, `${s0} ⊥ ${s1}`);
        } else if (eqAdj) {
          metricFacts.push(`${s0} = ${s1} = ${s2} = ${s3}`);
        } else {
          metricFacts.push(`${s0} = ${s2}, ${s1} = ${s3}`);
        }
      } else {
        const par02 = vParallel(edges[0], edges[2]);
        const par13 = vParallel(edges[1], edges[3]);
        if (par02 !== par13) {
          const basePair = par02 ? `${s0} ∥ ${s2}` : `${s1} ∥ ${s3}`;
          if (!parallelPairs.includes(basePair)) parallelPairs.unshift(basePair);
          if (metricCertified) {
            if (par02 && fEq(sqLens[1], sqLens[3])) metricFacts.push(`${s1} = ${s3}`);
            if (par13 && fEq(sqLens[0], sqLens[2])) metricFacts.push(`${s0} = ${s2}`);
          }
          if (isCertifiedRightPair(edges[0], edges[1])) metricFacts.push(`${s0} ⊥ ${s1}`);
          else if (isCertifiedRightPair(edges[1], edges[2])) metricFacts.push(`${s1} ⊥ ${s2}`);
          else if (isCertifiedRightPair(edges[2], edges[3])) metricFacts.push(`${s2} ⊥ ${s3}`);
          else if (isCertifiedRightPair(edges[3], edges[0])) metricFacts.push(`${s3} ⊥ ${s0}`);
        }
      }
    } else if (n === 3) {
      const [A0, A1, A2] = names;
      if (metricCertified && provenShape === "tam giác đều") {
        metricFacts.push(`${A0}${A1} = ${A1}${A2} = ${A2}${A0}`);
      } else {
        if (metricCertified) {
          if (fEq(sqLens[0], sqLens[2])) metricFacts.push(`${A0}${A1} = ${A0}${A2}`);
          else if (fEq(sqLens[0], sqLens[1])) metricFacts.push(`${A1}${A0} = ${A1}${A2}`);
          else if (fEq(sqLens[1], sqLens[2])) metricFacts.push(`${A2}${A1} = ${A2}${A0}`);
        }
        if (isCertifiedRightPair(edges[2], edges[0])) {
          metricFacts.push(`${A0}${A1} ⊥ ${A0}${A2} tại ${A0}`);
        } else if (isCertifiedRightPair(edges[0], edges[1])) {
          metricFacts.push(`${A1}${A0} ⊥ ${A1}${A2} tại ${A1}`);
        } else if (isCertifiedRightPair(edges[1], edges[2])) {
          metricFacts.push(`${A2}${A0} ⊥ ${A2}${A1} tại ${A2}`);
        }
      }
    }
  } else if (provenShape) {
    if (provenShape === "hình vuông") metricFacts.push("hai cặp cạnh đối song song, 4 cạnh bằng nhau và có góc vuông");
    else if (provenShape === "hình chữ nhật") metricFacts.push("hai cặp cạnh đối song song và có góc vuông");
    else if (provenShape === "hình thang vuông") {
      const perpWitness = cert.supportingPremises.find((p) => p.includes("⊥"));
      metricFacts.push(
        perpWitness
          ? `có một cặp cạnh đối song song và cạnh bên vuông góc đáy (${perpWitness})`
          : "có một cặp cạnh đối song song và một góc vuông đã chứng minh",
      );
    } else if (provenShape.startsWith("hình thang")) {
      metricFacts.push("có một cặp cạnh đối song song");
    }
  }

  const epistemicLevel: EpistemicConclusionLevel = cert.isBaseRegion
    ? "GIVEN"
    : provenShape
      ? "DERIVED"
      : undeterminedAspects.length > 0
        ? "INSUFFICIENT_PREMISES"
        : "COORDINATE_CONFIGURATION_ONLY";

  const secNoun = cycleNotation ? `thiết diện ${cycleNotation}` : "thiết diện";
  const parts: string[] = [];
  if (parallelPairs.length > 0) parts.push(parallelPairs.join(", "));
  if (metricFacts.length > 0) {
    parts.push(
      metricFacts.length === 2
        ? `${metricFacts[0]} và ${metricFacts[1]}`
        : metricFacts.join(", "),
    );
  }
  const undeterminedSuffix = undeterminedAspects.length > 0
    ? ` (${undeterminedAspects[0]})`
    : "";
  const summary = provenShape && parts.length > 0
    ? `${parts.join("; ")} ⇒ ${secNoun} là ${provenShape}${undeterminedSuffix}`
    : provenShape
      ? `Khép kín miền giao phẳng, thu được ${secNoun} là ${provenShape}${undeterminedSuffix}`
      : `Khép kín đa giác giao tạo thành ${secNoun}${undeterminedSuffix}`;

  return {
    shape: provenShape,
    coordinateShape,
    epistemicLevel,
    cycleNotation,
    parallelPairs,
    metricFacts,
    coordinateOnlyFacts,
    undeterminedAspects,
    supportingPremises: cert.supportingPremises,
    diagnostics: {
      edgeCount: n,
      boundaryConnected,
      coplanar,
      nonDegenerate,
      faceIncidences,
    },
    summary,
  };
}

const GREEK_PLANE_ALIAS: Record<string, string> = {
  alpha: "α",
  beta: "β",
  gamma: "γ",
  delta: "δ",
};

export function formatPlaneDisplayNotation(pl: SceneObject, scene?: Pick<Scene3D, "objects">): string {
  const raw = (pl.notation?.trim() || shortSym(pl))
    .replace(/^Mặt phẳng(?:\s+cắt)?\s+/iu, "")
    .trim();
  const bare = raw.replace(/^\((.+)\)$/u, "$1").trim();
  const quaMatch = /^qua\s+([A-Z][0-9′']*)\s*,\s*([A-Z][0-9′']*)\s*,\s*([A-Z][0-9′']*)$/u.exec(bare);
  if (quaMatch) {
    const trio = [quaMatch[1], quaMatch[2], quaMatch[3]];
    if (scene) {
      const apexSyms = structuralApexSymsOfScene(scene);
      const ordered = [...trio.filter((s) => apexSyms.has(s)), ...trio.filter((s) => !apexSyms.has(s))];
      return `(${ordered.join("")})`;
    }
    return `(${trio.join("")})`;
  }
  const greek = GREEK_PLANE_ALIAS[bare.toLowerCase()];
  if (greek) return `(${greek})`;
  if (raw.startsWith("(")) return raw;
  return raw.length <= 6 ? `(${raw})` : pl.label.replace(/^Mặt phẳng(?:\s+cắt)?\s+/iu, "").trim() || raw;
}

export function findParallelBaseForPlane(
  scene: Pick<Scene3D, "objects">,
  planeObj: SceneObject,
): string | null {
  const exactScene = exactSceneOriginOf(scene);
  const exactPl = exactScene.objects.find((o) => o.id === planeObj.id) ?? planeObj;
  if (exactPl.type !== "plane3" || !exactPl.normal) return null;
  const nPlane = parseFracVec3(exactPl.normal);
  for (const base of exactScene.objects) {
    if (base.surface_role !== "BASE_REGION") continue;
    const pts = base.polygon ?? base.vertices;
    if (!pts || pts.length < 3) continue;
    const v0 = parseFracVec3(pts[0]);
    const v1 = parseFracVec3(pts[1]);
    const v2 = parseFracVec3(pts[2]);
    const nBase = vCross(vSub(v1, v0), vSub(v2, v0));
    if (
      !vIsZero(nBase)
      && vParallel(nPlane, nBase)
      && exactPl.point
      && fIsZero(plainDotFrac(vSub(parseFracVec3(exactPl.point), v0), nBase))
    ) {
      return null;
    }
  }
  for (const base of exactScene.objects) {
    if (base.surface_role !== "BASE_REGION") continue;
    const pts = base.polygon ?? base.vertices;
    if (!pts || pts.length < 3) continue;
    const v0 = parseFracVec3(pts[0]);
    const v1 = parseFracVec3(pts[1]);
    const v2 = parseFracVec3(pts[2]);
    const nBase = vCross(vSub(v1, v0), vSub(v2, v0));
    const nonCoplanar =
      !exactPl.point
      || !fIsZero(plainDotFrac(vSub(parseFracVec3(exactPl.point), v0), nBase));
    if (!vIsZero(nBase) && vParallel(nPlane, nBase) && nonCoplanar) {
      const byId = new Map(exactScene.objects.map((o) => [o.id, o]));
      const names = (base.depends ?? []).map((id) => shortSym(byId.get(id))).filter(Boolean);
      const cyc = formatCycleNotation(names, preferredPointOrderForPolygon(exactScene, base));
      return cyc ?? (base.notation ? `(${base.notation.replace(/^[()]+|[()]+$/g, "")})` : base.label);
    }
  }
  return null;
}

function exactIntSqrt(n: bigint): bigint | null {
  if (n < 0n) return null;
  if (n < 2n) return n;
  let x = n;
  let y = (x + 1n) >> 1n;
  while (y < x) {
    x = y;
    y = (x + n / x) >> 1n;
  }
  return x * x === n ? x : null;
}

function hostCurvedSolidForBaseCircle(
  scene: Pick<Scene3D, "objects">,
  circleObj: SceneObject,
): SceneObject | null {
  if (circleObj.type !== "circle3") return null;
  if (
    circleObj.surface_role !== "BASE_REGION"
    && (circleObj.surface_role as string) !== "TOP_BASE_REGION"
    && classifyCircleSemanticRole(scene, circleObj) !== "BOUNDARY_AND_INTERSECTION"
  ) {
    return null;
  }
  const exactScene = exactSceneOriginOf(scene);
  const byId = new Map(exactScene.objects.map((o) => [o.id, o]));
  const exactC = byId.get(circleObj.id) ?? circleObj;
  for (const d of exactC.depends ?? []) {
    const cand = byId.get(d);
    if (cand?.type === "curved_solid") return cand;
  }
  if (!exactC.center) return null;
  const cCenter = parseFracVec3(exactC.center);
  for (const s of exactScene.objects) {
    if (s.type !== "curved_solid" || (s.curved_kind !== "cylinder" && s.curved_kind !== "cone")) continue;
    if (s.anchor && vIsZero(vSub(parseFracVec3(s.anchor), cCenter))) return s;
    if (s.curved_kind === "cylinder" && s.apex_or_top && vIsZero(vSub(parseFracVec3(s.apex_or_top), cCenter))) return s;
  }
  return null;
}

export function describeExactCurvedSectionMath(
  rawScene: Pick<Scene3D, "objects" | "chart_metric">,
  rawSecObj: SceneObject,
): string | null {
  const scene = exactSceneOriginOf(rawScene);
  const byId = new Map(scene.objects.map((o) => [o.id, o]));
  const secObj = byId.get(rawSecObj.id) ?? rawSecObj;
  const depObjs = (secObj.depends ?? []).map((id) => byId.get(id)).filter((x): x is SceneObject => Boolean(x));
  const curvedDep = depObjs.find((d) => d.type === "curved_solid");
  const planeDep = depObjs.find((d) => d.type === "plane3");
  if (!curvedDep) return null;

  if (secObj.type === "circle3" && secObj.center && secObj.radius_sq) {
    const r2 = parseExactFrac(secObj.radius_sq);
    if (curvedDep.curved_kind === "ball" && curvedDep.anchor && curvedDep.radius_sq) {
      const I = parseFracVec3(curvedDep.anchor);
      const H = parseFracVec3(secObj.center);
      const d2 = metricDot(vSub(H, I), vSub(H, I), scene.chart_metric);
      return fIsZero(d2)
        ? `Mặt phẳng đi qua tâm mặt cầu tạo giao tuyến là đường tròn lớn cùng tâm với mặt cầu`
        : `Mặt phẳng cắt mặt cầu tạo đường tròn giao tuyến nhận hình chiếu vuông góc của tâm mặt cầu làm tâm`;
    }
    if (curvedDep.curved_kind === "cylinder" && curvedDep.radius_sq) {
      const ortho = inspectAxialCurvedOrthogonality(scene, curvedDep);
      if (ortho.isRightCertified && fEq(r2, parseExactFrac(curvedDep.radius_sq))) {
        return `Mặt phẳng${planeDep ? ` ${formatPlaneDisplayNotation(planeDep)}` : ""} vuông góc với trục cắt hình trụ theo giao tuyến là đường tròn bằng đường tròn đáy`;
      }
      return `Xác định đường tròn giao tuyến phẳng của mặt phẳng cắt với mặt trụ`;
    }
    if (curvedDep.curved_kind === "cone" && curvedDep.anchor && curvedDep.apex_or_top && curvedDep.radius_sq) {
      return `Mặt phẳng song song với mặt đáy cắt hình nón theo đường tròn đồng dạng với đường tròn đáy`;
    }
  }

  if (secObj.type === "ellipse3" && secObj.semi_major_sq && secObj.semi_minor_sq) {
    if (curvedDep.curved_kind === "cylinder" && inspectAxialCurvedOrthogonality(scene, curvedDep).isRightCertified) {
      return `Mặt phẳng cắt xiên trục hình trụ tròn xoay tạo thiết diện là đường elip khép kín`;
    }
    return `Mặt phẳng cắt xiên mặt xung quanh tạo giao tuyến là đường elip khép kín`;
  }
  return null;
}

function formatCosSquaredConclusion(valRaw: string | undefined): { exactDegree: string | null; cosSqText: string } {
  const v = (valRaw ?? "").trim();
  if (!v) return { exactDegree: null, cosSqText: "" };
  try {
    const f = parseExactFrac(v);
    const key = `${f[0].toString()}/${f[1].toString()}`;
    const degMap: Record<string, string> = {
      "0/1": "90°",
      "1/4": "60°",
      "1/2": "45°",
      "3/4": "30°",
      "1/1": "0°",
    };
    return { exactDegree: degMap[key] ?? null, cosSqText: fmtFrac(f) };
  } catch {
    return { exactDegree: null, cosSqText: v };
  }
}

function lowerLeadingVietnameseNoun(lbl: string): string {
  return lbl
    .trim()
    .replace(/«([^»]+)»/gu, "$1")
    .replace(
      /^(Hình|Khối|Lăng\s+trụ|Tứ\s+diện|Mặt\s+cầu|Đường\s+tròn|Mặt\s+đáy|Đáy|Thiết\s+diện|Mặt\s+cắt|Giao\s+điểm|Đoạn\s+thẳng|Cạnh\s+bên)(?=\s|$)/u,
      (m) => m.toLowerCase(),
    );
}

export function isExplicitOxyzCoordinateScene(scene: Scene3D, obj?: SceneObject): boolean {
  const frame = (scene as { coordinate_frame?: string }).coordinate_frame;
  if (typeof frame === "string" && /oxyz/iu.test(frame)) return true;
  if (
    scene.objects.some(
      (o) =>
        o.type === "axes"
        || /^truc[:_]/iu.test(o.id)
        || /\bOxyz\b/u.test(`${o.label ?? ""} ${o.notation ?? ""}`),
    )
  ) {
    return true;
  }
  const exactScene = exactSceneOriginOf(scene);
  const hybridMeta = hybridViewOfScene(scene) ?? hybridViewOfScene(exactScene);
  if (hybridMeta?.source_provenance && obj) {
    for (const sp of hybridMeta.source_provenance) {
      const spRec = sp as unknown as Record<string, unknown>;
      if (spRec.id !== obj.id && spRec.object_id !== obj.id) continue;
      if (
        Array.isArray(spRec.quotes)
        && spRec.quotes.some(
          (q) => typeof q === "string" && (/\bOxyz\b/u.test(q) || /[xyz]\s*[+-]|[=]\s*0\b/iu.test(q)),
        )
      ) {
        return true;
      }
    }
  }
  return false;
}

function buildPedagogicalNarrationForRange(
  scene: Scene3D,
  startAnchor: number,
  anchor: number,
): { title: string; subtitle: string; label: string } {
  const byId = new Map(scene.objects.map((o) => [o.id, o]));
  const finalAnchor = Math.max(0, scene.events.length - 1);

  const directEvs = scene.events.slice(Math.max(0, startAnchor), Math.max(0, anchor) + 1).filter(Boolean);
  // §4.3 & §6: Bước dựng hình trên timeline chính KHÔNG kèm con số đáp án cuối cùng vào phụ đề.
  const appendMeasuredResultSuffix = (baseSubtitle: string): string => baseSubtitle;

  if (directEvs.length > 0 && directEvs.every((ev) => ev.action === "MEASURE")) {
    return {
      title: "Quan sát cấu hình đề bài",
      subtitle: "Quan sát các yếu tố hình học đã xác định trong không gian từ dữ kiện đề bài",
      label: "Quan sát cấu hình đề bài",
    };
  }

  const isAbsorbedSubordinateObject = (id: string | null | undefined): boolean => {
    if (!id) return false;
    const o = byId.get(id);
    if (!o) return false;
    if (o.type === "quantity" || o.render === "readout" || o.render === "non_visual") return true;
    if (
      o.type === "plane3"
      && resolvePlaneSectionVisibility(scene, o, finalAnchor, false, null).subRole === "SOLID_FACE_DUPLICATE_PLANE"
      && !scene.objects.some((x) => !isSubEntity(x.id) && isIntersectionLineOrSegment(x, scene) && (x.depends ?? []).includes(o.id))
    ) {
      return true;
    }
    return false;
  };
  const tl = geometryTimeline(scene);
  const gStart = geometryStepOf(scene, startAnchor);
  const gEnd = geometryStepOf(scene, anchor);
  const evIndices: number[] = [];
  for (let gi = Math.min(gStart, gEnd); gi <= Math.max(gStart, gEnd); gi += 1) {
    for (const k of tl[gi]?.construction ?? []) evIndices.push(k);
  }
  const events = evIndices.map((k) => scene.events[k]).filter(Boolean);
  const nonDuplicateEvents = events.filter((ev) => !isAbsorbedSubordinateObject(ev.object ?? ev.objects?.[0]));
  const effectiveEvents = nonDuplicateEvents.length > 0 ? nonDuplicateEvents : events;
  const effectiveObjs = [
    ...new Map(
      effectiveEvents
        .flatMap((ev) => [...(ev.object ? [ev.object] : []), ...(ev.objects ?? [])])
        .map((id) => byId.get(id))
        .filter((o): o is SceneObject => Boolean(o && !isAbsorbedSubordinateObject(o.id)))
        .map((o) => [o.id, o]),
    ).values(),
  ];
  const lastEv = effectiveEvents[effectiveEvents.length - 1] ?? scene.events[anchor];
  const primaryId = lastEv?.object ?? lastEv?.objects?.[0] ?? null;
  const primaryObj = primaryId ? byId.get(primaryId) : undefined;

  // 0s. Các bước trung gian dựng hình cầu cắt mặt phẳng (§3.3: `H, IH` và `M, IM, HM`)
  if (
    effectiveObjs.length > 0
    && effectiveObjs.every((o) => (o.display_group ?? []).includes("sphere_plane_aux"))
  ) {
    const distSeg = effectiveObjs.find((o) => o.type === "segment3" && (o.display_group ?? []).includes("sphere_plane_dist"));
    if (distSeg) {
      const footObj =
        effectiveObjs.find((o) => o.type === "point3")
        ?? (distSeg.perpendicular_witness?.foot_id ? byId.get(distSeg.perpendicular_witness.foot_id) : undefined);
      const fromObj = distSeg.perpendicular_witness?.from ? byId.get(distSeg.perpendicular_witness.from) : undefined;
      const onPlane = distSeg.perpendicular_witness?.on ? byId.get(distSeg.perpendicular_witness.on) : undefined;
      const symI = fromObj && fromObj.type === "point3" ? shortSym(fromObj) : "I";
      const symH = footObj ? shortSym(footObj) : "H";
      const pName = onPlane ? formatPlaneDisplayNotation(onPlane, scene) : "mặt phẳng cắt";
      if ((distSeg.display_group ?? []).includes("sphere_plane_tangent")) {
        // d = R: không có đường tròn giao tuyến; chân vuông góc (đã dựng ở bước trước) là điểm chung duy nhất.
        const title = `Nối bán kính ${symI}${symH} tới tiếp điểm ${symH}`;
        const subtitle = `Hạ ${symI}${symH} ⊥ ${pName} tại ${symH}; ${symI}${symH} bằng bán kính nên ${symH} là điểm chung duy nhất (tiếp điểm) của mặt cầu và ${pName}`;
        return { title, subtitle, label: title };
      }
      const title = `Xác định hình chiếu vuông góc ${symH} của tâm ${symI} và đoạn ${symI}${symH}`;
      const subtitle = `Hạ ${symI}${symH} ⊥ ${pName} tại ${symH}; điểm ${symH} là tâm của đường tròn giao tuyến trên ${pName}`;
      return { title, subtitle, label: title };
    }
    const sphRadSeg = effectiveObjs.find(
      (o) =>
        o.type === "segment3"
        && !(o.display_group ?? []).includes("sphere_plane_dist")
        && (o.depends ?? []).some((id) => {
          const d = byId.get(id);
          return d?.type === "curved_solid" && d.curved_kind === "ball";
        }),
    );
    const secRadSeg = effectiveObjs.find(
      (o) =>
        o.type === "segment3"
        && o.id !== sphRadSeg?.id
        && !(o.display_group ?? []).includes("sphere_plane_dist")
        && (o.depends ?? []).some((id) => byId.get(id)?.type === "plane3"),
    );
    if (secRadSeg && sphRadSeg) {
      const rimObj =
        effectiveObjs.find((o) => o.type === "point3")
        ?? (secRadSeg.endpoint_ids?.[1] ? byId.get(secRadSeg.endpoint_ids[1]) : undefined);
      const footObj = secRadSeg.endpoint_ids?.[0] ? byId.get(secRadSeg.endpoint_ids[0]) : undefined;
      const fromObj = sphRadSeg.endpoint_ids?.[0] ? byId.get(sphRadSeg.endpoint_ids[0]) : undefined;
      const planeDep = (secRadSeg.depends ?? []).map((id) => byId.get(id)).find((x) => x?.type === "plane3");
      const symM = rimObj ? shortSym(rimObj) : "M";
      const symH = footObj ? shortSym(footObj) : "H";
      const symI = fromObj && fromObj.type === "point3" ? shortSym(fromObj) : "I";
      const pName = planeDep ? formatPlaneDisplayNotation(planeDep, scene) : "mặt phẳng cắt";
      const title = `Xác định điểm ${symM} thuộc giao tuyến và tam giác vuông ${symI}${symH}${symM}`;
      const subtitle = `Lấy điểm ${symM} chung của mặt cầu và ${pName}, nối bán kính mặt cầu ${symI}${symM} và bán kính giao tuyến ${symH}${symM} (${symI}${symH} ⊥ ${symH}${symM})`;
      return { title, subtitle, label: title };
    }
    if (sphRadSeg) {
      const rimObj =
        effectiveObjs.find((o) => o.type === "point3")
        ?? (sphRadSeg.endpoint_ids?.[1] ? byId.get(sphRadSeg.endpoint_ids[1]) : undefined);
      const fromObj = sphRadSeg.endpoint_ids?.[0] ? byId.get(sphRadSeg.endpoint_ids[0]) : undefined;
      const planeDep = (rimObj?.depends ?? []).map((id) => byId.get(id)).find((x) => x?.type === "plane3");
      const symM = rimObj ? shortSym(rimObj) : "M";
      const symI = fromObj && fromObj.type === "point3" ? shortSym(fromObj) : "I";
      const pName = planeDep ? formatPlaneDisplayNotation(planeDep, scene) : "mặt phẳng cắt";
      const title = `Xác định điểm ${symM} thuộc đường tròn lớn giao tuyến và bán kính ${symI}${symM}`;
      const subtitle = `Mặt phẳng ${pName} đi qua tâm ${symI}; lấy điểm ${symM} thuộc đường tròn lớn giao tuyến với bán kính ${symI}${symM} bằng bán kính mặt cầu`;
      return { title, subtitle, label: title };
    }
  }

  // 0a. Nền tảng khối tròn xoay được nhóm ngữ cảnh (ví dụ `(O) + OA` của nón/trụ, hoặc `OO′ + (O′)` của trụ)
  if (effectiveObjs.length > 0) {
    const curvedBaseCircles = effectiveObjs.filter(
      (o) => o.type === "circle3" && Boolean(hostCurvedSolidForBaseCircle(scene, o)),
    );
    const curvedSegRoles = effectiveObjs
      .filter((o) => o.type === "segment3")
      .map((o) => ({ seg: o, role: classifyCurvedSegmentRole(scene, o) }));
    const allCurvedFoundationWithCircle =
      curvedBaseCircles.length > 0
      && curvedBaseCircles.length + curvedSegRoles.length === effectiveObjs.length
      && curvedSegRoles.every(
        (x) => x.role && (x.role.kind === "radius" || x.role.kind === "axis" || x.role.kind === "center_line"),
      );
    if (allCurvedFoundationWithCircle) {
      const host = hostCurvedSolidForBaseCircle(scene, curvedBaseCircles[0]);
      if (host) {
        const exactScene = exactSceneOriginOf(scene);
        const findCenterSym = (cRaw: ExactVec3 | undefined): string => {
          if (!cRaw) return "";
          const cv = parseFracVec3(cRaw);
          const pt = exactScene.objects.find(
            (p) => !isSubEntity(p.id) && p.type === "point3" && p.xyz && vIsZero(vSub(parseFracVec3(p.xyz), cv)),
          );
          return pt ? shortSym(pt) : "";
        };
        const ortho = host.curved_kind === "cylinder" ? inspectAxialCurvedOrthogonality(scene, host) : null;
        const hostNoun =
          host.curved_kind === "cone"
            ? "hình nón"
            : ortho?.isOblique
              ? "hình trụ xiên"
              : "hình trụ";
        const axEntry = curvedSegRoles.find((x) => x.role?.kind === "axis" || x.role?.kind === "center_line");
        const radEntry = curvedSegRoles.find((x) => x.role?.kind === "radius");
        if (axEntry && curvedBaseCircles.length === 1 && host.curved_kind === "cylinder") {
          const topSym = findCenterSym(curvedBaseCircles[0].center);
          const axSym = shortSym(axEntry.seg)
            .replace(/^(Đường\s+nối\s+tâm|Trục|Đoạn\s+thẳng|Đoạn)\s+/iu, "")
            .trim();
          const radSym = radEntry
            ? shortSym(radEntry.seg).replace(/^(Bán\s+kính(?:\s+đáy)?|Đoạn\s+thẳng|Đoạn)\s+/iu, "").trim()
            : "";
          if (ortho?.isOblique) {
            const title = topSym && axSym
              ? `Xác định tâm ${topSym}, dựng đường nối tâm ${axSym} và đường tròn đáy tâm ${topSym} của hình trụ xiên`
              : `Dựng đường nối tâm hai đáy và đường tròn đáy đối diện của hình trụ xiên`;
            const illusNote = ortho.isIllustrativeBasePlane
              ? " (mặt phẳng đáy biểu diễn theo cấu hình minh họa thỏa mãn giả thiết; đề bài chưa cố định duy nhất hướng mặt đáy)"
              : "";
            return {
              title,
              subtitle: `Đoạn ${axSym || "nối tâm"} nối hai tâm đáy (không được giả định là chiều cao vuông góc) và xác định đường tròn đáy song song bằng nhau${topSym ? ` (${topSym})` : ""}${illusNote}`,
              label: title,
            };
          }
          const title = topSym && axSym
            ? `Xác định tâm ${topSym}, dựng trục ${axSym} và đường tròn đáy tâm ${topSym}${radSym ? ` (bán kính ${radSym})` : ""} của hình trụ`
            : `Dựng trục và đường tròn đáy thứ hai của hình trụ`;
          const subtitle = ortho?.isTiltedAxisInSpace
            ? `Từ tâm đáy thứ nhất dựng trục ${axSym} vuông góc mặt đáy (đặt nghiêng trong không gian) tới ${topSym} và dựng đường tròn đáy (${topSym})`
            : `Từ tâm đáy thứ nhất dựng trục ${axSym} vuông góc mặt đáy tới ${topSym} và dựng đường tròn đáy song song (${topSym})`;
          return { title, subtitle, label: title };
        }
        if (!axEntry && curvedBaseCircles.length === 1) {
          const cSym = findCenterSym(curvedBaseCircles[0].center);
          const rSym = radEntry ? shortSym(radEntry.seg) : "";
          const title = cSym && rSym
            ? `Dựng đường tròn đáy tâm ${cSym}, bán kính ${rSym} của ${hostNoun}`
            : cSym
              ? `Dựng đường tròn đáy tâm ${cSym} của ${hostNoun}`
              : rSym
                ? `Dựng đường tròn đáy bán kính ${rSym} của ${hostNoun}`
                : `Dựng đường tròn đáy của ${hostNoun}`;
          const illusBaseNote = ortho?.isIllustrativeBasePlane
            ? " (mặt phẳng đáy chọn theo cấu hình minh họa đi qua bán kính đề cho; đề bài chưa cố định duy nhất hướng mặt đáy)"
            : "";
          const subtitle = cSym && rSym
            ? `Xác định tâm ${cSym}, bán kính R = ${rSym} và đường tròn mặt đáy (${cSym}) làm mặt phẳng cơ sở của ${hostNoun}${illusBaseNote}`
            : host.curved_kind === "cone"
              ? `Xác định đường tròn mặt đáy nằm trong mặt phẳng vuông góc với trục của hình nón`
              : `Xác định đường tròn mặt đáy cơ sở của ${hostNoun}${illusBaseNote}`;
          return { title, subtitle, label: title };
        }
      }
    }

    // 0b. Bộ khung các cạnh bên của hình chóp / hình lăng trụ (`CONSTRUCT_LATERAL_BOUNDARY`)
    const allLateralBoundary = effectiveObjs.every((o) => {
      const r = o.formation_roles ?? [];
      return o.type === "segment3" && r.includes("CONSTRUCT_LATERAL_BOUNDARY") && !r.includes("CONSTRUCT_HEIGHT");
    });
    if (allLateralBoundary) {
      const edgeSyms = effectiveObjs.map((o) => shortSym(o)).filter(Boolean);
      const allCompactEdgeSyms =
        edgeSyms.length === effectiveObjs.length
        && edgeSyms.every((s) => /^[A-Z0-9′']{2,8}$/u.test(s));
      const hostSolidForLat = !allCompactEdgeSyms
        ? scene.objects.find((s) => {
            if (s.type !== "solid") return false;
            const sVerts = new Set([...(s.vertex_ids ?? []), ...(s.depends ?? [])]);
            return effectiveObjs.every((eo) => (eo.depends ?? []).length > 0 && (eo.depends ?? []).every((d) => sVerts.has(d)));
          })
        : undefined;
      const hostSolidDesc = hostSolidForLat
        ? (hostSolidForLat.notation && /^[A-Z0-9′'.]+$/u.test(hostSolidForLat.notation)
            ? hostSolidForLat.notation
            : lowerLeadingVietnameseNoun(hostSolidForLat.label || "khối đa diện"))
        : "khối đa diện";
      const isPrism = scene.objects.some(
        (o) =>
          (o.type === "solid" && isTwoBasePolyhedronSolid(scene, o))
          || (o.formation_roles ?? []).includes("CONSTRUCT_TRANSLATED_FACE"),
      );
      const title = allCompactEdgeSyms
        ? edgeSyms.length === 1
          ? `Dựng cạnh bên ${edgeSyms[0]}`
          : edgeSyms.length > 1 && edgeSyms.length <= 6
            ? `Dựng các cạnh bên ${edgeSyms.join(", ")}`
            : `Dựng các cạnh bên của ${hostSolidDesc}`
        : effectiveObjs.length === 1
          ? `Dựng cạnh bên của ${hostSolidDesc}`
          : `Dựng các cạnh bên của ${hostSolidDesc}`;
      if (isPrism) {
        return {
          title,
          subtitle: "Nối các cặp đỉnh tương ứng giữa hai mặt đáy tạo bộ khung các cạnh bên song song bằng nhau của hình lăng trụ",
          label: title,
        };
      }
      const lowerBaseVerts = new Set(
        scene.objects
          .filter(
            (o) =>
              (o.surface_role === "BASE_REGION" || (o.formation_roles ?? []).includes("CONSTRUCT_BASE"))
              && !(o.formation_roles ?? []).includes("CONSTRUCT_TRANSLATED_FACE")
              && !isPolyhedronLateralOrAuxFacePolygon(scene, o),
          )
          .flatMap((o) => [...(o.depends ?? []), ...(o.vertex_ids ?? [])]),
      );
      const apexCandidates = [
        ...new Set(
          effectiveObjs
            .flatMap((o) => o.depends ?? [])
            .filter((dId) => byId.get(dId)?.type === "point3" && !lowerBaseVerts.has(dId)),
        ),
      ];
      const rawApexSym = apexCandidates.length === 1 ? shortSym(byId.get(apexCandidates[0])) : "";
      const apexSym = isCompactPointSym(rawApexSym) ? rawApexSym : "";
      return {
        title,
        subtitle: apexSym
          ? `Nối đỉnh ${apexSym} với các đỉnh mặt đáy tạo bộ khung cạnh bên của hình chóp`
          : "Nối đỉnh chóp với các đỉnh mặt đáy tạo bộ khung cạnh bên của hình chóp",
        label: title,
      };
    }
  }

  if (primaryObj) {
    const roles = primaryObj.formation_roles ?? [];
    // 1a. Mặt đáy đối diện tịnh tiến của lăng trụ (kiểm tra trước `BASE_REGION` vì đáy trên mang cả hai vai trò)
    if (primaryObj.type === "polygon3" && roles.includes("CONSTRUCT_TRANSLATED_FACE")) {
      const depNames = (primaryObj.depends ?? []).map((id) => shortSym(byId.get(id))).filter(Boolean);
      const allCompactDeps = depNames.length >= 3 && depNames.every(isCompactPointSym);
      const cyc = allCompactDeps
        ? canonicalizeCycleNames(depNames, preferredPointOrderForPolygon(scene, primaryObj)).join("")
        : primaryObj.notation && /^[A-Z0-9′']+$/u.test(primaryObj.notation)
          ? primaryObj.notation
          : "";
      const title = cyc ? `Dựng mặt đáy đối diện ${cyc} của lăng trụ` : "Dựng mặt đáy đối diện của lăng trụ";
      return {
        title,
        subtitle: cyc
          ? `Tịnh tiến các đỉnh mặt đáy theo phương cạnh bên để xác định mặt đáy song song bằng nhau ${cyc}`
          : "Tịnh tiến các đỉnh mặt đáy theo phương cạnh bên để xác định mặt đáy đối diện song song bằng nhau",
        label: title,
      };
    }

    if (
      primaryObj.type === "polygon3"
      && (primaryObj.surface_role === "BASE_REGION" || roles.includes("CONSTRUCT_BASE"))
      && !isPolyhedronLateralOrAuxFacePolygon(scene, primaryObj)
    ) {
      const prov = classifyPolygonShapeWithProvenance(scene, primaryObj);
      const depNames = (primaryObj.depends ?? []).map((id) => shortSym(byId.get(id))).filter(Boolean);
      const allCompactDeps = depNames.length >= 3 && depNames.every(isCompactPointSym);
      const cyc = allCompactDeps
        ? canonicalizeCycleNames(depNames, preferredPointOrderForPolygon(scene, primaryObj)).join("")
        : primaryObj.notation && /^[A-Z0-9′']+$/u.test(primaryObj.notation)
          ? primaryObj.notation
          : "";
      const fallbackBaseDesc = lowerLeadingVietnameseNoun(primaryObj.label || "mặt đáy");
      const fallbackHasBasePrefix = /^(?:mặt\s+đáy|đáy|thiết\s+diện|mặt\s+cắt)\b/iu.test(fallbackBaseDesc);
      if (prov.certifiedShape) {
        const title = cyc
          ? `Dựng đáy ${cyc} là ${prov.certifiedShape}`
          : `Dựng ${fallbackHasBasePrefix ? fallbackBaseDesc : `đáy ${fallbackBaseDesc}`} là ${prov.certifiedShape}`;
        return {
          title,
          subtitle: cyc
            ? `Xác định đa giác đáy ${cyc} làm mặt phẳng chuẩn từ dữ kiện đề bài`
            : `Xác định ${fallbackHasBasePrefix ? fallbackBaseDesc : `đa giác đáy ${fallbackBaseDesc}`} từ các quan hệ hình học đã dựng`,
          label: title,
        };
      }
      const title = cyc
        ? `Dựng mặt đáy ${cyc}`
        : `Dựng ${fallbackHasBasePrefix ? fallbackBaseDesc : `mặt đáy ${fallbackBaseDesc}`}`;
      const polySideCount = (primaryObj.polygon ?? primaryObj.vertices ?? []).length;
      const hasSpecialIllustrativeLayout =
        prov.provenance === "ILLUSTRATIVE_CHOICE"
        || (
          prov.provenance === "UNVERIFIED"
          && prov.coordinateShape !== null
          && polySideCount >= 3
          && prov.coordinateShape !== topologicalPolygonNoun(polySideCount)
        );
      const subtitle =
        hasSpecialIllustrativeLayout
          ? `Xác định ${cyc ? `mặt phẳng đáy ${cyc}` : fallbackBaseDesc} từ các đỉnh đề bài (hình dạng cụ thể trên khung là cấu hình minh họa)`
          : cyc
            ? `Xác định mặt phẳng đáy ${cyc} từ các đỉnh đã nêu trong đề bài`
            : `Xác định ${fallbackBaseDesc} làm mặt đáy của khối`;
      return {
        title,
        subtitle,
        label: title,
      };
    }

    // 1b. Đường tròn đáy của hình trụ / hình nón (`BASE_REGION`)
    if (primaryObj.type === "circle3" && primaryObj.surface_role === "BASE_REGION") {
      const baseCirclesInUnit = effectiveEvents
        .map((ev) => (ev.object ? byId.get(ev.object) : undefined))
        .filter((o): o is SceneObject => Boolean(o && o.type === "circle3" && o.surface_role === "BASE_REGION"));
      const host = hostCurvedSolidForBaseCircle(scene, primaryObj);
      const exactScene = exactSceneOriginOf(scene);
      const findCenterSym = (cRaw: ExactVec3 | undefined): string => {
        if (!cRaw) return "";
        const cv = parseFracVec3(cRaw);
        const pt = exactScene.objects.find(
          (p) => !isSubEntity(p.id) && p.type === "point3" && p.xyz && vIsZero(vSub(parseFracVec3(p.xyz), cv)),
        );
        return pt ? shortSym(pt) : "";
      };
      if (baseCirclesInUnit.length >= 2) {
        const cNames = [...new Set(baseCirclesInUnit.map((c) => findCenterSym(c.center)).filter(isCompactPointSym))];
        const ortho = host ? inspectAxialCurvedOrthogonality(scene, host) : null;
        const noun = ortho?.isOblique ? "hình trụ xiên" : "hình trụ";
        const title = cNames.length >= 2
          ? `Dựng hai đường tròn đáy tâm ${cNames.join(", ")} của ${noun}`
          : `Dựng hai đường tròn đáy của ${noun}`;
        return {
          title,
          subtitle: `Xác định hai đường tròn đáy song song và bằng nhau của ${noun}`,
          label: title,
        };
      }
      const cSym = findCenterSym(primaryObj.center);
      const ortho = host?.curved_kind === "cylinder" ? inspectAxialCurvedOrthogonality(scene, host) : null;
      const hostNoun =
        host?.curved_kind === "cylinder"
          ? (ortho?.isOblique ? "hình trụ xiên" : "hình trụ")
          : "hình nón";
      const title = cSym ? `Dựng đường tròn đáy tâm ${cSym} của ${hostNoun}` : `Dựng đường tròn đáy của ${hostNoun}`;
      return {
        title,
        subtitle: `Xác định đường tròn mặt đáy cơ sở của ${hostNoun}`,
        label: title,
      };
    }

    // 2. Đường cao được chứng nhận vuông góc
    if (
      (primaryObj.type === "segment3" || primaryObj.type === "line3")
      && roles.includes("CONSTRUCT_HEIGHT")
      && !classifyCurvedSegmentRole(scene, primaryObj)
    ) {
      const sym = shortSym(primaryObj);
      const w = primaryObj.perpendicular_witness;
      const onObj = w?.on ? byId.get(w.on) : undefined;
      const footObj = w?.foot_id
        ? byId.get(w.foot_id)
        : (primaryObj.depends ?? [])
            .map((id) => byId.get(id))
            .find((o) => o?.type === "point3" && o.xyz && w?.foot && o.xyz.join("|") === w.foot.join("|"));
      const apexObj = w?.from ? byId.get(w.from) : undefined;
      const onNotation = onObj?.notation
        ? (onObj.notation.startsWith("(") ? onObj.notation : `(${onObj.notation})`)
        : shortSym(onObj);
      const footSym = shortSym(footObj);
      const apexSym = shortSym(apexObj);
      if (w?.rule === "regular_pyramid_center_altitude" && onNotation && footSym) {
        const basePlain = onNotation.replace(/^\(|\)$/gu, "");
        const title = `Xác định tâm đáy ${footSym} và dựng đường cao ${sym} ⊥ ${onNotation}`;
        const subtitle = apexSym
          ? `Hình chóp đều có chân đường cao trùng tâm ${footSym} của đáy ${basePlain}; dựng ${sym} ⊥ ${onNotation} để xác định đỉnh ${apexSym}`
          : `Hình chóp đều có chân đường cao trùng tâm ${footSym} của đáy ${basePlain}; dựng ${sym} ⊥ ${onNotation}`;
        return { title, subtitle, label: title };
      }
      const title = onNotation && footSym
        ? `Dựng đường cao ${sym} ⊥ ${onNotation} tại ${footSym}`
        : `Dựng đường cao ${sym}`;
      const subtitle = footSym && apexSym && onNotation
        ? `Xác định phương vuông góc với mặt đáy ${onNotation} tại ${footSym} để dựng đỉnh ${apexSym}`
        : `Dựng đoạn đường cao ${sym} vuông góc với mặt đáy`;
      return { title, subtitle, label: title };
    }

    // 3. Khép kín khối đa diện (chóp, lăng trụ, tứ diện không khai báo mặt đáy ưu tiên)
    if (primaryObj.type === "solid") {
      const sym = shortSym(primaryObj);
      const priorObjsForSolid = startAnchor > 0 ? objectsAt(scene, startAnchor - 1) : [];
      const hadPriorLateralFrame = priorObjsForSolid.some(
        (po) => po.type === "segment3" && (po.formation_roles ?? []).includes("CONSTRUCT_LATERAL_BOUNDARY"),
      );
      const isPrism =
        isTwoBasePolyhedronSolid(scene, primaryObj)
        || scene.objects.some((o) => (o.formation_roles ?? []).includes("CONSTRUCT_TRANSLATED_FACE"));
      if (isPrism) {
        const cleanPrismLbl = lowerLeadingVietnameseNoun(primaryObj.label ?? `lăng trụ ${sym}`);
        const title = /^Hoàn thiện/iu.test(cleanPrismLbl) ? cleanPrismLbl : `Hoàn thiện ${cleanPrismLbl}`;
        return {
          title,
          subtitle: hadPriorLateralFrame
            ? `Khép kín các mặt bên giữa hai mặt đáy và bộ khung cạnh bên để hoàn thiện khối ${sym}`
            : `Nối các cặp đỉnh tương ứng giữa hai mặt đáy để khép kín các mặt bên của ${sym}`,
          label: title,
        };
      }
      const hasExplicitBase = scene.objects.some(
        (o) =>
          !isSubEntity(o.id)
          && (o.authoritative !== false || /\./u.test(primaryObj.notation ?? ""))
          && (o.surface_role === "BASE_REGION" || (o.formation_roles ?? []).includes("CONSTRUCT_BASE")),
      );
      if (!hasExplicitBase && (primaryObj.vertices?.length ?? 0) === 4) {
        const declIndex = new Map(scene.objects.map((o, idx) => [o.id, idx]));
        const exactSol = exactSceneOriginOf(scene).objects.find((o) => o.id === primaryObj.id) ?? primaryObj;
        const rawIds = [...new Set(primaryObj.vertex_ids ?? primaryObj.depends ?? [])].sort(
          (a, b) => (declIndex.get(a) ?? 999) - (declIndex.get(b) ?? 999),
        );
        const vSyms = rawIds.map((id) => shortSym(byId.get(id))).filter(isCompactPointSym);
        const tetVerts = exactSol.vertices ?? primaryObj.vertices ?? [];
        const exactTetOrigin = exactSceneOriginOf(scene);
        const tetHasUncertifiedVerts =
          hasUncertifiedObjectSource(exactSol)
          || rawIds.some((vid) => {
            const vp = exactTetOrigin.objects.find((o) => o.id === vid) ?? byId.get(vid);
            return hasUncertifiedObjectSource(vp);
          });
        const gMetricForTet = exactTetOrigin.chart_metric ?? scene.chart_metric;
        const hasNonIdentityMetric = Boolean(
          gMetricForTet
            && gMetricForTet.some((row, rIdx) =>
              row.some((cell, cIdx) => !fEq(parseFracVec3([cell, "0", "0"])[0], rIdx === cIdx ? [1n, 1n] : [0n, 1n])),
            ),
        );
        const allVertsCertifiedGiven =
          rawIds.length === 4
          && rawIds.every((vid) =>
            isCertifiedGivenSceneObject(
              exactTetOrigin as Pick<Scene3D, "objects"> & { free_objects?: string[] },
              exactTetOrigin.objects.find((o) => o.id === vid) ?? byId.get(vid),
            ),
          );
        const hasCertifiedEdgeFact =
          (exactSol.source as Record<string, unknown> | undefined)?.is_given === true
          || (hasNonIdentityMetric && allVertsCertifiedGiven)
          || exactTetOrigin.objects.some(
            (q) =>
              q.type === "quantity"
              && classifyQuantityProvenance(q, exactTetOrigin) === "GIVEN"
              && q.annotation?.kind === "length",
          );
        let isRegTet = false;
        if (tetVerts.length === 4 && hasCertifiedEdgeFact && !tetHasUncertifiedVerts) {
          const tv = tetVerts.map(parseFracVec3);
          const pairSq: Frac[] = [];
          const gMetric = exactTetOrigin.chart_metric ?? scene.chart_metric;
          for (let i = 0; i < 4; i += 1) {
            for (let j = i + 1; j < 4; j += 1) {
              pairSq.push(metricDot(vSub(tv[j], tv[i]), vSub(tv[j], tv[i]), gMetric));
            }
          }
          isRegTet = pairSq[0][0] > 0n && pairSq.every((sq) => fEq(sq, pairSq[0]));
        }
        const tetSym = vSyms.length === 4 ? vSyms.join("") : sym.replace(/\./gu, "");
        const tetKind = isRegTet ? "tứ diện đều" : "tứ diện";
        const title = hadPriorLateralFrame ? `Hoàn thiện khối ${tetKind} ${tetSym}` : `Dựng ${tetKind} ${tetSym}`;
        return {
          title,
          subtitle: hadPriorLateralFrame
            ? `Khép kín các mặt tam giác từ mặt đáy và bộ khung cạnh bên để hoàn thiện khối ${tetKind} ${tetSym}`
            : `Xác định 4 đỉnh không đồng phẳng và nối 6 cạnh tạo thành khối ${tetKind} ${tetSym}`,
          label: title,
        };
      }
      const cleanSolidLbl = lowerLeadingVietnameseNoun(primaryObj.label ?? `hình chóp ${sym}`);
      const isCompactSolidSym = /^[A-Z0-9′'.]+$/u.test(sym);
      const exactSolidOrigin = exactSceneOriginOf(scene);
      const exactSolidById = new Map(exactSolidOrigin.objects.map((o) => [o.id, o]));
      const solidBasePoly = scene.objects.find(
        (p) =>
          p.type === "polygon3"
          && (p.surface_role === "BASE_REGION" || (p.formation_roles ?? []).includes("CONSTRUCT_BASE"))
          && !(p.formation_roles ?? []).includes("CONSTRUCT_TRANSLATED_FACE")
          && !isPolyhedronLateralOrAuxFacePolygon(scene, p),
      );
      const solidBaseProv = solidBasePoly ? classifyPolygonShapeWithProvenance(scene, solidBasePoly) : null;
      const solidVertIds = [...new Set([...(primaryObj.vertex_ids ?? []), ...(primaryObj.depends ?? [])])].filter(
        (id) => exactSolidById.get(id)?.type === "point3",
      );
      const givenQtyMentionedIds = new Set(
        exactSolidOrigin.objects
          .filter((q) => q.type === "quantity" && classifyQuantityProvenance(q, exactSolidOrigin) === "GIVEN")
          .flatMap((q) => [...(q.depends ?? []), ...(q.annotation?.subject_ids ?? [])]),
      );
      const baseVertIdsForIllus = solidBasePoly
        ? [...new Set([...(solidBasePoly.vertex_ids ?? []), ...(solidBasePoly.depends ?? [])])].filter(
            (id) => exactSolidById.get(id)?.type === "point3",
          )
        : [];
      const hasUnconstrainedFreeBaseVertex =
        givenQtyMentionedIds.size > 0
        && baseVertIdsForIllus.some(
          (id) => exactSolidById.get(id)?.origin === "free" && !givenQtyMentionedIds.has(id),
        );
      const hasIllustrativeBaseOrVerts =
        (solidBaseProv !== null
          && !solidBaseProv.certifiedShape
          && solidBaseProv.coordinateShape !== null
          && (solidBaseProv.provenance === "ILLUSTRATIVE_CHOICE"
            || (solidBaseProv.provenance === "UNVERIFIED"
              && (hasUnconstrainedFreeBaseVertex
                || solidVertIds.some((id) => hasUncertifiedObjectSource(exactSolidById.get(id)))))))
        || hasUncertifiedObjectSource(exactSolidById.get(primaryObj.id) ?? primaryObj);
      const illusSolidNote = hasIllustrativeBaseOrVerts
        ? " (cấu hình tọa độ cụ thể trên khung chỉ để minh họa cho giả thiết đề bài)"
        : "";
      const title = `Hoàn thiện ${cleanSolidLbl}`;
      const baseSubtitle = hadPriorLateralFrame
        ? isCompactSolidSym
          ? `Khép kín các mặt bên tam giác từ mặt đáy và bộ khung cạnh bên để hoàn thiện khối ${sym}`
          : `Khép kín các mặt bên từ mặt đáy và bộ khung cạnh bên để hoàn thiện ${cleanSolidLbl}`
        : events.length > 1
          ? `Nối đỉnh với các đỉnh mặt đáy để khép kín các mặt bên của ${isCompactSolidSym ? sym : cleanSolidLbl}`
          : (primaryObj.role || `Khép kín các mặt của ${isCompactSolidSym ? `khối ${sym}` : cleanSolidLbl}`);
      const subtitle = `${baseSubtitle}${illusSolidNote}`;
      return { title, subtitle, label: title };
    }

    // 4. Khối tròn xoay
    if (primaryObj.type === "curved_solid") {
      const sym = shortSym(primaryObj);
      const priorObjs = startAnchor > 0 ? objectsAt(scene, startAnchor - 1) : [];
      const hasPriorFoundation = priorObjs.some(
        (po) =>
          (po.type === "circle3"
            && po.surface_role === "BASE_REGION"
            && hostCurvedSolidForBaseCircle(scene, po)?.id === primaryObj.id)
          || ((po.type === "segment3" || po.type === "line3")
            && classifyCurvedSegmentRole(scene, po)?.host.id === primaryObj.id),
      );
      if (primaryObj.curved_kind === "ball") {
        const deps = (primaryObj.depends ?? []).map((id) => byId.get(id)).filter((o): o is SceneObject => o?.type === "point3");
        const anchorKey = primaryObj.anchor?.join("|");
        const centerPt = deps.find((p) => p.xyz?.join("|") === anchorKey) ?? deps[0];
        const rimPt = deps.find((p) => p.id !== centerPt?.id);
        const rawCenterSym = centerPt ? shortSym(centerPt) : "";
        // Chỉ gọi tên tâm khi điểm tâm thực sự có ký hiệu hiển thị trên khung (`notation` hợp lệ), không tự bịa `"tâm I"` từ role nội bộ
        const hasRenderedCenterSym = Boolean(centerPt?.notation?.trim()) && isCompactPointSym(rawCenterSym);
        const centerSym = hasRenderedCenterSym ? rawCenterSym : "";
        const rawRimSym = rimPt ? shortSym(rimPt) : "";
        const rimSym = Boolean(rimPt?.notation?.trim() || isCompactPointSym(rawRimSym)) && isCompactPointSym(rawRimSym) ? rawRimSym : "";
        // Chỉ lấy ký hiệu `(S)` khi `notation` được đề bài khai báo tường minh (tránh lấy nhãn mặc định `"(S)"` của sample cũ khi `notation === null`)
        const parenSym = primaryObj.notation?.trim() || "";
        const sphereRole = classifySphereSemanticRole(scene, primaryObj);
        if (!centerSym && sphereRole === "CIRCUMSCRIBED_SPHERE") {
          const title = "Xác định tâm cách đều các đỉnh và dựng mặt cầu ngoại tiếp";
          return {
            title,
            subtitle: `Xác định tâm mặt cầu ngoại tiếp từ giao các mặt phẳng trung trực${rimSym ? `, bán kính đi qua ${rimSym}` : ""}`,
            label: title,
          };
        }
        const foundRefPt = byId.get(`${primaryObj.id}__ref_pt`);
        const rawRefSym = foundRefPt ? shortSym(foundRefPt) : "";
        const refSym = Boolean(foundRefPt?.notation?.trim() || isCompactPointSym(rawRefSym)) && isCompactPointSym(rawRefSym) ? rawRefSym : "";
        const verb = hasPriorFoundation ? "Hoàn thiện" : "Dựng";
        const rawBallLabel = primaryObj.label && !/^\([A-Za-z0-9_′']+\)$/u.test(primaryObj.label.trim()) ? primaryObj.label : "";
        const cleanBallNoun = lowerLeadingVietnameseNoun(rawBallLabel || "mặt cầu");
        const title = centerSym
          ? rimSym
            ? `${verb} mặt cầu${parenSym ? ` ${parenSym}` : ""} tâm ${centerSym} đi qua ${rimSym}`
            : refSym
              ? `${verb} mặt cầu${parenSym ? ` ${parenSym}` : ""} tâm ${centerSym}, bán kính R = ${centerSym}${refSym}`
              : `${verb} mặt cầu${parenSym ? ` ${parenSym}` : ""} tâm ${centerSym}`
          : `${verb} ${parenSym ? `mặt cầu ${parenSym}` : cleanBallNoun}${rimSym && !cleanBallNoun.includes(rimSym) ? ` đi qua ${rimSym}` : ""}`;
        return {
          title,
          subtitle: rimSym && centerSym
            ? `Đặt tâm ${centerSym}, nối bán kính R = ${centerSym}${rimSym} tới điểm ${rimSym} thuộc mặt cầu rồi dựng mặt cầu hoàn chỉnh`
            : refSym && centerSym
              ? `Đặt tâm ${centerSym}, lấy điểm tham chiếu ${refSym} trên mặt cầu để mở bán kính R = ${centerSym}${refSym} rồi dựng mặt cầu hoàn chỉnh`
              : rimSym
                ? `Xác định mặt cầu đi qua ${rimSym} từ tâm vừa dựng (bán kính bằng khoảng cách từ tâm tới ${rimSym})`
                : `Xác định mặt cầu${parenSym ? ` ${parenSym}` : centerSym ? ` tâm ${centerSym}` : ""} từ tâm và bán kính đề cho`,
          label: title,
        };
      }
      if (primaryObj.curved_kind === "cylinder") {
        const ortho = inspectAxialCurvedOrthogonality(scene, primaryObj);
        const baseKey = primaryObj.anchor?.join("|");
        const topKey = primaryObj.apex_or_top?.join("|");
        const pts = (primaryObj.depends ?? []).map((id) => byId.get(id)).filter((o): o is SceneObject => o?.type === "point3");
        const pBase = pts.find((p) => p.xyz?.join("|") === baseKey);
        const pTop = pts.find((p) => p.xyz?.join("|") === topKey);
        const segSym = pBase && pTop ? `${shortSym(pBase)}${shortSym(pTop)}` : pts.length >= 2 ? `${shortSym(pts[0])}${shortSym(pts[1])}` : "";
        if (ortho.isOblique) {
          const title = hasPriorFoundation
            ? `Hoàn thiện mặt xung quanh hình trụ xiên${segSym ? ` nối tâm ${segSym}` : ""}`
            : `Dựng hình trụ xiên${segSym ? ` nối tâm ${segSym}` : ""}`;
          const illusNote = ortho.isIllustrativeBasePlane
            ? " (hướng nghiêng mặt đáy là cấu hình minh họa cho giả thiết chưa xác định duy nhất)"
            : "";
          return {
            title,
            subtitle: `Quét các đường sinh song song với đường nối tâm hai đáy${segSym ? ` ${segSym}` : ""} (nghiêng với mặt đáy, không phải chiều cao vuông góc h)${illusNote}`,
            label: title,
          };
        }
        const tiltedRightNote =
          ortho.isRightCertified && ortho.isTiltedAxisInSpace
            ? ` (trục${segSym ? ` ${segSym}` : ""} vuông góc hai đáy — hình trụ tròn xoay đặt nghiêng trong không gian, không phải hình trụ xiên)`
            : "";
        const title = hasPriorFoundation
          ? (segSym ? `Hoàn thiện mặt xung quanh hình trụ trục ${segSym}` : `Hoàn thiện mặt xung quanh ${primaryObj.label}`)
          : (segSym ? `Dựng hình trụ trục ${segSym}` : `Dựng ${primaryObj.label}`);
        return {
          title,
          subtitle: hasPriorFoundation
            ? `Quét các đường sinh song song với trục${segSym ? ` ${segSym}` : ""} nối hai đường tròn đáy của hình trụ${tiltedRightNote}`
            : `Xác định hai đáy tròn song song và mặt xung quanh của hình trụ${tiltedRightNote}`,
          label: title,
        };
      }
      if (primaryObj.curved_kind === "cone") {
        const isSecondaryCut = isSecondaryCutCurvedSolid(scene, primaryObj);
        if (isSecondaryCut) {
          const cleanLabel = (primaryObj.label ?? `hình nón ${sym}`).replace(/«([^»]+)»/gu, "$1");
          const title = /^Xác định|^Dựng/iu.test(cleanLabel) ? cleanLabel : `Xác định ${cleanLabel.charAt(0).toLowerCase()}${cleanLabel.slice(1)}`;
          return {
            title,
            subtitle: appendMeasuredResultSuffix(`Tách phần hình nón nhỏ phía trên mặt phẳng cắt và phần hình nón cụt còn lại`),
            label: title,
          };
        }
        const topKey = primaryObj.apex_or_top?.join("|");
        const baseKey = primaryObj.anchor?.join("|");
        const pts = (primaryObj.depends ?? []).map((id) => byId.get(id)).filter((o): o is SceneObject => o?.type === "point3");
        const apex = pts.find((p) => p.xyz?.join("|") === topKey);
        const center = pts.find((p) => p.xyz?.join("|") === baseKey);
        const title = hasPriorFoundation
          ? (apex && center
              ? `Hoàn thiện mặt xung quanh hình nón đỉnh ${shortSym(apex)}, tâm đáy ${shortSym(center)}`
              : `Hoàn thiện mặt xung quanh ${primaryObj.label}`)
          : (apex && center
              ? `Dựng hình nón đỉnh ${shortSym(apex)}, tâm đáy ${shortSym(center)}`
              : `Dựng ${primaryObj.label}`);
        return {
          title,
          subtitle: hasPriorFoundation
            ? `Quét các đường sinh nối đỉnh${apex ? ` ${shortSym(apex)}` : ""} với đường tròn đáy${center ? ` tâm ${shortSym(center)}` : ""}`
            : `Xác định đáy đường tròn và mặt xung quanh của hình nón`,
          label: title,
        };
      }
    }

    // 5. Điểm trọng tâm / trung điểm / đối xứng / tỉ số / hình chiếu / giao điểm đường–mặt
    if (primaryObj.type === "point3") {
      const sym = shortSym(primaryObj);
      const centroidRel = findPointCentroidRelation(scene, primaryObj);
      if (centroidRel) {
        const tri = centroidRel.vertexSyms.join("");
        const title = `Xác định trọng tâm ${sym} của tam giác ${tri}`;
        const projFrom = primaryObj.perpendicular_witness?.from ? byId.get(primaryObj.perpendicular_witness.from) : undefined;
        const projOn = primaryObj.perpendicular_witness?.on ? byId.get(primaryObj.perpendicular_witness.on) : undefined;
        const projSuffix = projFrom
          ? `; hình chiếu vuông góc của ${shortSym(projFrom)} lên ${projOn ? (projOn.type === "plane3" ? formatPlaneDisplayNotation(projOn, scene) : `(${shortSym(projOn)})`) : `(${tri})`} trùng với ${sym}`
          : "";
        const subtitle =
          centroidRel.constructionMode === "median_ratio" && centroidRel.medianVertexSym && centroidRel.oppositeEdgeSyms
            ? `Dựng đường trung tuyến từ ${centroidRel.medianVertexSym} tới trung điểm cạnh ${centroidRel.oppositeEdgeSyms.join("")}, lấy trọng tâm ${sym} chia trung tuyến theo tỉ số 2/3${projSuffix}`
            : `Lấy giao điểm các đường trung tuyến của tam giác ${tri}${projSuffix}`;
        return {
          title,
          subtitle,
          label: title,
        };
      }
      const midRel = findPointMidpointRelation(scene, primaryObj);
      if (midRel?.kind === "midpoint") {
        const seg = `${midRel.aSym}${midRel.bSym}`;
        const compact = isCompactPointSym(sym);
        const title = compact ? `Xác định trung điểm ${sym} của ${seg}` : `Xác định trung điểm của ${seg}`;
        return {
          title,
          subtitle: compact
            ? `Lấy điểm ${sym} trên đoạn ${seg} sao cho ${midRel.aSym}${sym} = ${sym}${midRel.bSym}`
            : `Lấy trung điểm chia đôi đoạn thẳng ${seg}`,
          label: title,
        };
      }
      if (midRel?.kind === "symmetric" && midRel.centerSym) {
        const compact = isCompactPointSym(sym);
        const title = compact
          ? `Xác định điểm ${sym} đối xứng với ${midRel.aSym} qua ${midRel.centerSym}`
          : `Xác định điểm đối xứng với ${midRel.aSym} qua ${midRel.centerSym}`;
        return {
          title,
          subtitle: compact
            ? `Kéo dài bán kính ${midRel.aSym}${midRel.centerSym} cắt đường tròn đáy tại ${sym} (${midRel.centerSym}${midRel.aSym} = ${midRel.centerSym}${sym})`
            : `Kéo dài bán kính ${midRel.aSym}${midRel.centerSym} cắt đường tròn đáy tại điểm đối xứng qua tâm ${midRel.centerSym}`,
          label: title,
        };
      }
      if (midRel?.kind === "ratio" && midRel.ratioFrac) {
        const seg = `${midRel.aSym}${midRel.bSym}`;
        const rText = fmtFrac(midRel.ratioFrac);
        const inside = midRel.ratioFrac[0] > 0n && midRel.ratioFrac[0] < midRel.ratioFrac[1];
        const compact = isCompactPointSym(sym);
        const title = compact
          ? inside
            ? `Xác định điểm ${sym} trên đoạn ${seg}`
            : `Xác định điểm ${sym} trên đường thẳng ${seg}`
          : inside
            ? `Xác định điểm chia trên đoạn ${seg}`
            : `Xác định điểm chia trên đường thẳng ${seg}`;
        return {
          title,
          subtitle: compact
            ? inside
              ? `Lấy điểm ${sym} thuộc đoạn ${seg} theo tỉ số ${midRel.aSym}${sym}/${seg} = ${rText}`
              : `Lấy điểm ${sym} trên đường thẳng ${seg} theo tỉ số đại số ${midRel.aSym}${sym}/${seg} = ${rText}`
            : inside
              ? `Lấy điểm thuộc đoạn ${seg} theo tỉ số ${rText} tính từ ${midRel.aSym}`
              : `Lấy điểm trên đường thẳng ${seg} theo tỉ số đại số ${rText} tính từ ${midRel.aSym}`,
          label: title,
        };
      }
      const inferredFootSegWitness =
        !primaryObj.perpendicular_witness
          ? scene.objects.find(
              (s) =>
                s.type === "segment3"
                && s.perpendicular_witness?.foot_id === primaryObj.id
                && !(s.formation_roles ?? []).includes("CONSTRUCT_HEIGHT"),
            )?.perpendicular_witness
          : undefined;
      const effectivePtWitness = primaryObj.perpendicular_witness ?? inferredFootSegWitness;
      if (effectivePtWitness?.on && effectivePtWitness?.from) {
        const fromObj = byId.get(effectivePtWitness.from);
        const onObj = byId.get(effectivePtWitness.on);
        if (fromObj && onObj) {
          const onName =
            onObj.type === "plane3"
              ? formatPlaneDisplayNotation(onObj, scene)
              : onObj.type === "polygon3"
                ? (onObj.notation?.startsWith("(") ? onObj.notation : `(${shortSym(onObj)})`)
                : shortSym(onObj);
          const exactScene = exactSceneOriginOf(scene);
          const exactById = new Map(exactScene.objects.map((o) => [o.id, o]));
          const exPrim = exactById.get(primaryObj.id) ?? primaryObj;
          const coincPt = exPrim.xyz
            ? scene.objects.find((cand) => {
                if (isSubEntity(cand.id) || cand.type !== "point3" || cand.id === primaryObj.id) return false;
                const ec = exactById.get(cand.id) ?? cand;
                return Boolean(
                  ec.xyz
                    && vIsZero(vSub(parseFracVec3(ec.xyz), parseFracVec3(exPrim.xyz!)))
                    && isCompactPointSym(shortSym(cand))
                    && shortSym(cand) !== sym,
                );
              })
            : undefined;
          const visNow = objectsAt(scene, anchor);
          const dedicatedPerpSeg = scene.objects.find(
            (so) =>
              so.type === "segment3"
              && so.endpoint_ids?.length === 2
              && ((so.endpoint_ids[0] === fromObj.id && so.endpoint_ids[1] === primaryObj.id)
                || (so.endpoint_ids[1] === fromObj.id && so.endpoint_ids[0] === primaryObj.id)),
          );
          const hasPerpSegVisibleNow = dedicatedPerpSeg
            ? visNow.some((so) => so.id === dedicatedPerpSeg.id)
            : Boolean(primaryObj.perpendicular_witness);
          // Chân không có tên ngắn (nhãn là mô tả "Hình chiếu của I lên (ABC)") thì không chèn vào câu — câu đã nói đủ.
          const title = `Hạ hình chiếu vuông góc${isCompactPointSym(sym) ? ` ${sym}` : ""} của ${shortSym(fromObj)} lên ${onName}`;
          const subtitle = coincPt
            ? `Chân vuông góc ${sym} trùng ${shortSym(coincPt)} (${shortSym(fromObj)}${shortSym(coincPt)} ⊥ ${onName}); khoảng cách từ ${shortSym(fromObj)} đến ${onName} được biểu diễn bởi đoạn ${shortSym(fromObj)}${shortSym(coincPt)}`
            : hasPerpSegVisibleNow
              ? `Kẻ ${shortSym(fromObj)}${sym} ⊥ ${onName} tại chân vuông góc ${sym}; đoạn vuông góc ${shortSym(fromObj)}${sym} biểu diễn khoảng cách từ ${shortSym(fromObj)} đến ${onName}`
              : `Điểm ${sym} thuộc ${onName} sao cho đường thẳng qua ${shortSym(fromObj)} và ${sym} vuông góc với ${onName}`;
          return {
            title,
            subtitle,
            label: title,
          };
        }
      }
      const interRel = findLinePlaneIntersectionMidpoint(scene, primaryObj);
      if (interRel) {
        const excludedFromSection =
          interRel.isExterior
          && Boolean(primaryObj.xyz)
          && scene.objects.some(
            (s) =>
              s.type === "section"
              && (s.polygon?.length ?? 0) >= 3
              && !s.polygon!.some((vx) => vx.join("|") === primaryObj.xyz!.join("|")),
          );
        const compactInterSym = isCompactPointSym(sym);
        const title = interRel.isExterior && interRel.segA && interRel.segB
          ? compactInterSym
            ? `Kéo dài ${interRel.lineSym} cắt ${interRel.planeSym} tại ${sym}`
            : `Kéo dài ${interRel.lineSym} cắt ${interRel.planeSym}`
          : !compactInterSym || /^giao\s+điểm\b/iu.test(sym)
            ? `Xác định giao điểm của ${interRel.lineSym} và ${interRel.planeSym}`
            : `Xác định giao điểm ${sym} = ${interRel.lineSym} ∩ ${interRel.planeSym}`;
        let subtitle = `Tìm giao điểm của đường thẳng ${interRel.lineSym} với mặt phẳng ${interRel.planeSym}`;
        if (interRel.isCoincidentEndpoint && interRel.coincidentSym) {
          subtitle = compactInterSym
            ? `Mặt phẳng ${interRel.planeSym} đi qua đầu mút ${interRel.coincidentSym} nên giao điểm ${sym} trùng ${interRel.coincidentSym} (không cần kéo dài ${interRel.lineSym})`
            : `Mặt phẳng ${interRel.planeSym} đi qua đầu mút ${interRel.coincidentSym} nên giao điểm trùng ${interRel.coincidentSym} (không cần kéo dài ${interRel.lineSym})`;
        } else if (interRel.isMidpoint && interRel.segA && interRel.segB) {
          subtitle = compactInterSym
            ? `Mặt phẳng ${interRel.planeSym} cắt cạnh ${interRel.lineSym} tại trung điểm ${sym} (${interRel.segA}${sym} = ${sym}${interRel.segB})`
            : `Mặt phẳng ${interRel.planeSym} cắt cạnh ${interRel.lineSym} tại trung điểm của đoạn ${interRel.lineSym}`;
        } else if (interRel.isExterior && interRel.segA && interRel.segB) {
          subtitle = excludedFromSection
            ? compactInterSym
              ? `Đường phụ kéo dài cạnh ${interRel.lineSym} (ngoài đoạn ${interRel.lineSym}) cắt ${interRel.planeSym} tại điểm phụ ${sym} nằm ngoài miền khối (${sym} không phải đỉnh của thiết diện)`
              : `Đường phụ kéo dài cạnh ${interRel.lineSym} (ngoài đoạn ${interRel.lineSym}) cắt ${interRel.planeSym} tại giao điểm phụ nằm ngoài miền khối (không phải đỉnh của thiết diện)`
            : compactInterSym
              ? `Đường phụ kéo dài cạnh ${interRel.lineSym} (ngoài đoạn ${interRel.lineSym}, đi qua ${interRel.segA} và ${interRel.segB}) để tìm giao điểm ${sym} = ${interRel.lineSym} ∩ ${interRel.planeSym}`
              : `Đường phụ kéo dài cạnh ${interRel.lineSym} (ngoài đoạn ${interRel.lineSym}, đi qua ${interRel.segA} và ${interRel.segB}) cắt mặt phẳng ${interRel.planeSym}`;
        } else if (
          interRel.isInterior
          && interRel.segA
          && interRel.segB
          && interRel.ratioFrac
          && interRel.ratioFrac[0] > 0n
          && interRel.ratioFrac[0] < interRel.ratioFrac[1]
        ) {
          subtitle = compactInterSym
            ? `Trên đoạn ${interRel.lineSym}, mặt phẳng ${interRel.planeSym} cắt cạnh ${interRel.lineSym} tại ${sym} (${interRel.segA}${sym}/${interRel.lineSym} = ${interRel.ratioFrac[0].toString()}/${interRel.ratioFrac[1].toString()})`
            : `Trên đoạn ${interRel.lineSym}, mặt phẳng ${interRel.planeSym} cắt cạnh ${interRel.lineSym} theo tỉ số ${interRel.ratioFrac[0].toString()}/${interRel.ratioFrac[1].toString()} tính từ ${interRel.segA}`;
        }
        return { title, subtitle, label: title };
      }
      const diagRel = findPolygonDiagonalIntersectionRelation(scene, primaryObj);
      if (diagRel) {
        const compactDiagSym = isCompactPointSym(sym);
        const title = compactDiagSym
          ? `Xác định giao điểm ${sym} = ${diagRel.d1Sym} ∩ ${diagRel.d2Sym}`
          : `Xác định giao điểm của ${diagRel.d1Sym} và ${diagRel.d2Sym}`;
        const subtitle = compactDiagSym
          ? `Nối hai đường chéo ${diagRel.d1Sym} và ${diagRel.d2Sym}${diagRel.polySym ? ` của mặt ${diagRel.polySym}` : ""} cắt nhau tại ${sym}`
          : `Nối hai đường chéo ${diagRel.d1Sym} và ${diagRel.d2Sym}${diagRel.polySym ? ` của mặt ${diagRel.polySym}` : ""}`;
        return { title, subtitle, label: title };
      }
      if (primaryObj.role) {
        const title = isCompactPointSym(sym) ? `Xác định điểm ${sym}` : `Xác định ${lowerLeadingVietnameseNoun(sym)}`;
        return { title, subtitle: primaryObj.role.replace(/«([^»]+)»/gu, "$1"), label: title };
      }
      if (isCompactPointSym(sym)) {
        const lineDeps = (primaryObj.depends ?? [])
          .map((id) => byId.get(id))
          .filter((d): d is SceneObject => Boolean(d && (d.type === "line3" || d.type === "segment3")));
        if (lineDeps.length === 2) {
          const l1 = shortSym(lineDeps[0]);
          const l2 = shortSym(lineDeps[1]);
          const title = `Xác định giao điểm ${sym} = ${l1} ∩ ${l2}`;
          return {
            title,
            subtitle: `Hai đường thẳng đồng phẳng ${l1} và ${l2} cắt nhau tại ${sym}`,
            label: title,
          };
        }
        const title = `Xác định điểm ${sym}`;
        return {
          title,
          subtitle: cleanLearnerText(primaryObj.label) !== sym ? cleanLearnerText(primaryObj.label) : "",
          label: title,
        };
      }
    }

    // 6. Mặt phẳng cắt / mặt phẳng nghiên cứu (hoặc cặp mặt phẳng chuẩn bị tìm giao tuyến)
    if (effectiveObjs.length >= 2 && effectiveObjs.every((o) => o.type === "plane3")) {
      const planeNames = effectiveObjs.map((p) => formatPlaneDisplayNotation(p, scene));
      const joinedNames =
        planeNames.length === 2 ? `hai mặt phẳng ${planeNames[0]} và ${planeNames[1]}` : `các mặt phẳng ${planeNames.join(", ")}`;
      const firstDeps = new Set(effectiveObjs[0].depends ?? []);
      const sharedPtSyms = [...firstDeps]
        .filter((id) => effectiveObjs.every((p) => (p.depends ?? []).includes(id)))
        .map((id) => byId.get(id))
        .filter((p): p is SceneObject => Boolean(p && p.type === "point3" && isCompactPointSym(shortSym(p))))
        .map((p) => shortSym(p));
      const title = `Xác định ${joinedNames}`;
      const subtitle =
        sharedPtSyms.length > 0
          ? `Xác định ${joinedNames} cùng đi qua điểm chung ${sharedPtSyms.join(", ")}`
          : `Xác định ${joinedNames} trong không gian trước khi tìm giao tuyến`;
      return { title, subtitle, label: title };
    }
    if (primaryObj.type === "plane3") {
      const pName = formatPlaneDisplayNotation(primaryObj, scene);
      const parallelBase = findParallelBaseForPlane(scene, primaryObj);
      const rawDepPts = (primaryObj.depends ?? [])
        .map((id) => byId.get(id))
        .filter((o): o is SceneObject => Boolean(o && o.type === "point3"));
      const depPts = rawDepPts.filter((o) => !laDiemPhuDungMatPhang(scene, o, byId) && isCompactPointSym(shortSym(o)));
      const depLine = (primaryObj.depends ?? [])
        .map((id) => byId.get(id))
        .find((o): o is SceneObject => Boolean(o && (o.type === "line3" || o.type === "segment3")));
      const planeVis = resolvePlaneSectionVisibility(scene, primaryObj, finalAnchor, false, null);
      const isCut = planeVis.subRole === "CONSTRUCTION_TOOL_PLANE" || planeVis.subRole === "SPATIAL_RELATION_PLANE";
      const attachedSphereDistSeg = effectiveObjs.find(
        (o) =>
          o.type === "segment3"
          && o.perpendicular_witness?.on === primaryObj.id
          && (
            (o.display_group ?? []).includes("sphere_plane_dist")
            || classifyCurvedSegmentRole(scene, o)?.host.curved_kind === "ball"
            || (o.depends ?? []).some((d) => byId.get(d)?.curved_kind === "ball")
          ),
      );
      const hasSphereSectionCircle = scene.objects.some(
        (c) =>
          c.type === "circle3"
          && (c.depends ?? []).includes(primaryObj.id)
          && (c.depends ?? []).some((d) => byId.get(d)?.curved_kind === "ball"),
      );
      const isTangentSpherePlane = Boolean(attachedSphereDistSeg && !hasSphereSectionCircle);
      const title = isTangentSpherePlane
        ? `Dựng mặt phẳng tiếp diện ${pName}`
        : isCut
          ? `Dựng mặt phẳng cắt ${pName}`
          : `Dựng mặt phẳng ${pName}`;
      let subtitle = (primaryObj.role || `Xác định mặt phẳng ${pName} trong không gian`).replace(/«([^»]+)»/gu, "$1");
      if (!isExplicitOxyzCoordinateScene(scene, primaryObj) && /phương\s+trình/iu.test(subtitle)) {
        const cutsSphere = hasSphereSectionCircle || Boolean(attachedSphereDistSeg);
        subtitle = cutsSphere
          ? `Xác định mặt phẳng cắt ${pName} theo khoảng cách từ tâm mặt cầu đề cho`
          : `Xác định mặt phẳng ${pName} theo vị trí hình học đề cho`;
      }
      if (depPts.length >= 3) {
        const pList = depPts.map((p) => shortSym(p)).join(", ");
        subtitle = parallelBase
          ? `Mặt phẳng đi qua ${pList}; song song với mặt đáy ${parallelBase}`
          : `Mặt phẳng xác định bởi ba điểm không thẳng hàng ${pList}`;
      } else if (depPts.length === 1 && depLine) {
        const exactPl = exactSceneOriginOf(scene).objects.find((o) => o.id === primaryObj.id) ?? primaryObj;
        const exactLn = exactSceneOriginOf(scene).objects.find((o) => o.id === depLine.id) ?? depLine;
        const isPerp =
          Boolean(exactPl.normal && exactLn.direction)
          && vParallel(parseFracVec3(exactPl.normal!), parseFracVec3(exactLn.direction!));
        if (isPerp) {
          subtitle = `Mặt phẳng đi qua điểm ${shortSym(depPts[0])} và vuông góc với đường thẳng ${shortSym(depLine)}`;
        }
      } else if (depPts.length === 1 && rawDepPts.length >= 3 && parallelBase && !primaryObj.role) {
        subtitle = `Mặt phẳng đi qua điểm ${shortSym(depPts[0])} và song song với mặt đáy ${parallelBase}`;
      } else if (parallelBase && !/song\s+song/iu.test(subtitle)) {
        subtitle = `${subtitle}; song song với mặt đáy ${parallelBase}`;
      }
      if (attachedSphereDistSeg) {
        const footId = attachedSphereDistSeg.perpendicular_witness?.foot_id;
        const footSym = footId ? shortSym(byId.get(footId)) : "";
        const segSym = shortSym(attachedSphereDistSeg);
        if (isTangentSpherePlane && segSym && footSym) {
          subtitle = `Xác định mặt phẳng tiếp diện ${pName} vuông góc với bán kính ${segSym} tại tiếp điểm ${footSym}`;
        } else if (segSym && footSym && !subtitle.includes(segSym)) {
          subtitle = `${subtitle}; hạ đoạn vuông góc ${segSym} ⊥ ${pName} tại ${footSym}`;
        }
      }
      return { title, subtitle, label: title };
    }

    // 7. Thiết diện đa diện (từng đoạn giao tuyến vs bước khép kín hoàn chỉnh)
    if (primaryObj.type === "section") {
      const sd = sectionDetails(scene, primaryObj.id);
      const prefOrder = preferredPointOrderForPolygon(scene, primaryObj);
      const cycNotation = sd ? formatCycleNotation(sd.vertexNames, prefOrder) : null;
      const planeObj = sd?.planeId ? byId.get(sd.planeId) : undefined;
      const solidObj = sd?.solidId ? byId.get(sd.solidId) : undefined;
      const pRaw = planeObj ? shortSym(planeObj) : "mặt phẳng cắt";
      const pSym = pRaw !== "mặt phẳng cắt" && !pRaw.startsWith("(") && pRaw.length <= 5 ? `(${pRaw})` : pRaw;
      const sSym = solidObj ? shortSym(solidObj) : "khối";

      const hasCombinedExtendTraces = effectiveEvents.some(
        (ev) => ev.action === "EXTEND" && ev.object === primaryObj.id,
      );
      if (lastEv?.action === "EXTEND" || hasCombinedExtendTraces) {
        const canonNames = sd ? canonicalizeCycleNames(sd.vertexNames, prefOrder) : [];
        const canonEdges = canonNames.length >= 3 && canonNames.every((x) => x.length <= 3 && !/^Đỉnh\s+\d+$/u.test(x))
          ? canonNames.map((a, idx) => `${a}${canonNames[(idx + 1) % canonNames.length]}`)
          : [];
        const coordSym = new Map<string, string | null>();
        for (const o of scene.objects) {
          if (isSubEntity(o.id) || o.type !== "point3" || !o.xyz || laDiemPhuDungMatPhang(scene, o, byId)) continue;
          const s = shortSym(o);
          if (!isCompactPointSym(s)) continue;
          const key = o.xyz.join("|");
          coordSym.set(key, coordSym.has(key) ? null : s);
        }
        const faceTraces: { order: number; text: string }[] = [];
        for (const st of primaryObj.steps ?? []) {
          if (st.face_index === null || !solidObj?.faces?.[st.face_index] || !solidObj.vertex_ids) continue;
          const fSyms = solidObj.faces[st.face_index]
            .map((vi) => shortSym(byId.get(solidObj.vertex_ids![vi])))
            .filter(Boolean);
          const faceNotation = formatCycleNotation(fSyms, [...structuralApexSymsOfScene(scene), ...preferredPointOrderForPolygon(scene, solidObj)]);
          if (!faceNotation) continue;
          const aSym = coordSym.get(st.a.join("|"));
          const bSym = coordSym.get(st.b.join("|"));
          if (aSym && bSym) {
            const fwd = `${aSym}${bSym}`;
            const rev = `${bSym}${aSym}`;
            const idxFwd = canonEdges.indexOf(fwd);
            const idxRev = canonEdges.indexOf(rev);
            const segSym = idxFwd >= 0 ? fwd : idxRev >= 0 ? rev : fwd;
            const order = idxFwd >= 0 ? idxFwd : idxRev >= 0 ? idxRev : faceTraces.length + 100;
            faceTraces.push({ order, text: `${pSym} ∩ ${faceNotation} = ${segSym}` });
          } else {
            faceTraces.push({ order: faceTraces.length + 100, text: `${pSym} ∩ ${faceNotation}` });
          }
        }
        faceTraces.sort((ta, tb) => ta.order - tb.order);
        const segTokens = canonEdges.length > 0 ? canonEdges.join(", ") : null;
        if (lastEv?.action === "EXTEND") {
          const title = `Dựng các giao tuyến của ${pSym} với các mặt của ${sSym}`;
          const subtitle = faceTraces.length > 0
            ? `Giao tuyến trên từng mặt: ${faceTraces.map((ft) => ft.text).join(", ")}`
            : segTokens
              ? `Xác định các đoạn giao tuyến ${segTokens} trên các mặt của khối ${sSym}`
              : `Tìm giao tuyến của ${pSym} với từng mặt của khối ${sSym}`;
          return { title, subtitle, label: title };
        }
        const basis = deriveExactPolygonMathBasis(scene, primaryObj);
        const secName = cycNotation
          ? `thiết diện ${cycNotation}`
          : pSym !== "mặt phẳng cắt"
            ? `thiết diện tạo bởi ${pSym}`
            : "thiết diện";
        const title = `Dựng các giao tuyến và hoàn thiện ${secName}`;
        const parallelHint = basis && basis.parallelPairs.length > 0
          ? ` (${basis.parallelPairs.join(", ")})`
          : "";
        const traceSummary = faceTraces.length > 0
          ? `Giao tuyến trên từng mặt: ${faceTraces.map((ft) => ft.text).join(", ")}`
          : segTokens
            ? `Xác định các đoạn giao tuyến ${segTokens} trên các mặt của khối ${sSym}`
            : "";
        const subtitle = appendMeasuredResultSuffix(
          traceSummary
            ? `${traceSummary} ⇒ khép kín miền ${secName}${parallelHint}`
            : `Khép kín các đoạn giao tuyến của ${pSym} với các mặt của ${sSym} để xác định miền ${secName}${parallelHint}`,
        );
        return { title, subtitle, label: title };
      }

      const basis = deriveExactPolygonMathBasis(scene, primaryObj);
      const secName = cycNotation
        ? `thiết diện ${cycNotation}`
        : primaryObj.label.replace(/^Thiết diện\b/u, "thiết diện");
      const title = `Hoàn thiện và làm nổi bật ${secName}`;
      const parallelHint = basis && basis.parallelPairs.length > 0
        ? ` (${basis.parallelPairs.join(", ")})`
        : "";
      const subtitle = appendMeasuredResultSuffix(
        `Khép kín các đoạn giao tuyến của ${pSym} với các mặt của ${sSym} để xác định miền ${secName}${parallelHint}`,
      );
      return { title, subtitle, label: title };
    }

    // 8. Thiết diện tròn / elip hoặc đa giác thiết diện qua trục
    if (
      (primaryObj.type === "circle3" || primaryObj.type === "ellipse3")
      && (vaiTroMien(primaryObj) === "section"
        || (primaryObj.type === "ellipse3" && (primaryObj.depends ?? []).some((id) => byId.get(id)?.type === "curved_solid")))
    ) {
      const planeDep = (primaryObj.depends ?? []).map((id) => byId.get(id)).find((o) => o?.type === "plane3");
      const solidDep = (primaryObj.depends ?? []).map((id) => byId.get(id)).find((o) => o?.type === "curved_solid");
      const kindLabel = primaryObj.type === "ellipse3" ? "elip thiết diện" : "đường tròn thiết diện";
      const solidName = solidDep
        ? (solidDep.notation?.trim()
            || (solidDep.curved_kind === "cylinder"
                ? "hình trụ"
                : solidDep.curved_kind === "cone"
                  ? "hình nón"
                  : solidDep.curved_kind === "ball"
                    ? "mặt cầu"
                    : shortSym(solidDep)))
        : null;
      const title = (
        planeDep && solidName
          ? `Dựng ${kindLabel} giao của ${solidName} và ${formatPlaneDisplayNotation(planeDep, scene)}`
          : `Dựng ${kindLabel}`
      ).replace(/«([^»]+)»/gu, "$1");
      const exactMathDesc = describeExactCurvedSectionMath(scene, primaryObj);
      return {
        title,
        subtitle: appendMeasuredResultSuffix(
          exactMathDesc ?? `Xác định miền giao phẳng khi cắt khối tròn xoay bởi mặt phẳng`,
        ),
        label: title,
      };
    }

    if (
      primaryObj.type === "polygon3"
      && (vaiTroMien(primaryObj) === "section" || isPolyhedronLateralOrAuxFacePolygon(scene, primaryObj))
    ) {
      const basis = deriveExactPolygonMathBasis(scene, primaryObj);
      const shape = basis ? basis.shape : classifyScenePolygonShape(scene, primaryObj);
      const depNames = (primaryObj.vertex_ids && primaryObj.vertex_ids.length >= 3 ? primaryObj.vertex_ids : primaryObj.depends ?? [])
        .map((id) => shortSym(byId.get(id)))
        .filter(Boolean);
      const prefOrder = [...structuralApexSymsOfScene(scene), ...preferredPointOrderForPolygon(scene, primaryObj)];
      const cyc = basis?.cycleNotation ?? (depNames.length >= 3
        ? formatCycleNotation(depNames, prefOrder)
        : (primaryObj.notation ? (primaryObj.notation.startsWith("(") ? primaryObj.notation : `(${primaryObj.notation})`) : primaryObj.label));
      const hasCurvedSolid = scene.objects.some((o) => o.type === "curved_solid");
      const isLateralSolidFace = isPolyhedronLateralOrAuxFacePolygon(scene, primaryObj);
      if (isLateralSolidFace) {
        const lateralCyc = depNames.length >= 3
          ? formatCycleNotation(depNames, prefOrder)
          : (primaryObj.notation ? (primaryObj.notation.startsWith("(") ? primaryObj.notation : `(${primaryObj.notation})`) : primaryObj.label);
        const faceParen = lateralCyc ? (lateralCyc.startsWith("(") ? lateralCyc : `(${lateralCyc})`) : (primaryObj.notation ?? primaryObj.label);
        const vList = depNames.length >= 3 ? canonicalizeCycleNames(depNames, prefOrder).join(", ") : "";
        const title = `Xác định mặt bên ${faceParen}`;
        return {
          title,
          subtitle: vList
            ? `Xác định mặt phẳng bên ${faceParen} của khối qua các đỉnh ${vList}`
            : `Xác định mặt phẳng bên ${faceParen} của khối đa diện`,
          label: title,
        };
      }
      const isAuxiliaryPolygonNotSection =
        !hasCurvedSolid
        && primaryObj.surface_role === "AUXILIARY_SURFACE"
        && !(primaryObj.formation_roles ?? []).includes("PRODUCE_SECTION_RESULT")
        && !/section|intersect/iu.test(String(primaryObj.producer ?? ""))
        && !(primaryObj.depends ?? []).some((d) => byId.get(d)?.type === "plane3")
        && !isPolyhedronLateralOrAuxFacePolygon(scene, primaryObj);
      if (isAuxiliaryPolygonNotSection) {
        const bareCyc = (cyc ?? primaryObj.label).replace(/^\((.+)\)$/u, "$1");
        const title = `Dựng ${shape ?? "đa giác"} ${bareCyc}`;
        return {
          title,
          subtitle: `Nối các đỉnh xác định miền phẳng của ${shape ?? "đa giác"} ${bareCyc}`,
          label: title,
        };
      }
      const title = `Dựng thiết diện ${cyc ?? primaryObj.label}`;
      return {
        title,
        subtitle: appendMeasuredResultSuffix(
          `Nối các đỉnh đã xác định tạo thành miền đa giác thiết diện ${cyc ?? primaryObj.label}`,
        ),
        label: title,
      };
    }

    // 9. Đoạn thẳng / đường thẳng khác (đoạn vuông góc chung, khoảng cách, đoạn mục tiêu, giao tuyến, trục, bán kính, đường sinh)
    if (primaryObj.type === "segment3" || primaryObj.type === "line3") {
      const sym = shortSym(primaryObj);
      const segW = primaryObj.perpendicular_witness ?? primaryObj.annotation?.witness;

      if (segW?.relation === "common_perpendicular") {
        const l1 = segW.on ? byId.get(segW.on) : undefined;
        const l2 = segW.second?.on ? byId.get(segW.second.on) : (segW.from ? byId.get(segW.from) : undefined);
        const l1Sym = l1 ? shortSym(l1) : "";
        const l2Sym = l2 ? shortSym(l2) : "";
        const title = l1Sym && l2Sym
          ? `Dựng đoạn vuông góc chung ${sym} của ${l1Sym} và ${l2Sym}`
          : `Dựng đoạn vuông góc chung ${sym}`;
        const subtitle = l1Sym && l2Sym
          ? `Xác định ${sym} ⊥ ${l1Sym} và ${sym} ⊥ ${l2Sym}; độ dài đoạn vuông góc chung ${sym} biểu diễn khoảng cách giữa ${l1Sym} và ${l2Sym}`
          : (primaryObj.role || `Đoạn vuông góc chung biểu diễn khoảng cách giữa hai đường thẳng chéo nhau`);
        return { title, subtitle, label: title };
      }

      const curvedRoleForPerp = classifyCurvedSegmentRole(scene, primaryObj);
      const isTangentSpherePerpRadius =
        curvedRoleForPerp?.kind === "radius"
        && curvedRoleForPerp.host.curved_kind === "ball"
        && Boolean(segW?.on && byId.get(segW.on)?.type === "plane3");
      const srcInstruction = (primaryObj.source as Record<string, unknown> | undefined)?.instruction;
      if (
        segW?.on
        && !isExplanatoryTargetSegment(primaryObj)
        && (
          isExplanatoryPerpSegment(primaryObj)
          || srcInstruction === "EXPLANATORY_DERIVED_WITNESS"
          || (
            !(primaryObj.formation_roles ?? []).includes("CONSTRUCT_HEIGHT")
            && (!curvedRoleForPerp || isTangentSpherePerpRadius)
            && !isIntersectionLineOrSegment(primaryObj, scene)
            && (segW.relation === "line_perp_plane" || segW.relation === "line_perp_line")
          )
        )
      ) {
        const onObj = byId.get(segW.on);
        const onName = onObj
          ? onObj.type === "plane3"
            ? formatPlaneDisplayNotation(onObj, scene)
            : onObj.type === "polygon3"
              ? (onObj.notation?.startsWith("(") ? onObj.notation : `(${shortSym(onObj)})`)
              : shortSym(onObj)
          : "";
        const footObj = segW.foot_id ? byId.get(segW.foot_id) : undefined;
        const fromObj = segW.from ? byId.get(segW.from) : undefined;
        const footPart = footObj && isCompactPointSym(shortSym(footObj)) ? ` tại ${shortSym(footObj)}` : "";
        const title = onName
          ? `Hạ đoạn vuông góc ${sym} ⊥ ${onName}${footPart}`
          : `Hạ đoạn vuông góc ${sym}`;
        const subtitle = isTangentSpherePerpRadius && onName
          ? `Khoảng cách ${sym} bằng bán kính mặt cầu nên ${onName} tiếp xúc với mặt cầu${footPart}`
          : fromObj && onName
            ? `Đoạn vuông góc ${sym} biểu diễn khoảng cách từ ${shortSym(fromObj)} đến ${onName}`
            : (primaryObj.role || `Đoạn vuông góc biểu diễn khoảng cách cần khảo sát`);
        return { title, subtitle, label: title };
      }

      if (isExplanatoryTargetSegment(primaryObj)) {
        const depPts = (primaryObj.depends ?? [])
          .map((id) => byId.get(id))
          .filter((p): p is SceneObject => Boolean(p && p.type === "point3" && isCompactPointSym(shortSym(p))));
        if (segW?.on && segW?.from) {
          const onObj = byId.get(segW.on);
          const fromObj = byId.get(segW.from);
          const onName = onObj ? (onObj.type === "plane3" ? formatPlaneDisplayNotation(onObj, scene) : shortSym(onObj)) : "";
          const title = onName && fromObj
            ? `Nối đoạn vuông góc ${sym} ⊥ ${onName}`
            : `Nối đoạn thẳng ${sym}`;
          const subtitle = fromObj && onName
            ? `Đoạn vuông góc ${sym} biểu diễn khoảng cách từ ${shortSym(fromObj)} đến ${onName}`
            : `Nối đoạn thẳng ${sym} giữa hai điểm đã xác định`;
          return { title, subtitle, label: title };
        }
        const title = `Nối đoạn thẳng ${sym}`;
        const subtitle = depPts.length === 2
          ? `Nối hai điểm đã xác định ${shortSym(depPts[0])} và ${shortSym(depPts[1])} tạo đoạn thẳng ${sym}`
          : (primaryObj.role || `Xác định đoạn thẳng ${sym}`);
        return { title, subtitle, label: title };
      }

      if (isIntersectionLineOrSegment(primaryObj, scene)) {
        const planeDeps = (primaryObj.depends ?? [])
          .map((id) => byId.get(id))
          .filter((o): o is SceneObject => Boolean(o && (o.type === "plane3" || o.type === "polygon3")));
        const exactScene = exactSceneOriginOf(scene);
        const exactById = new Map(exactScene.objects.map((o) => [o.id, o]));
        const exactLine = exactById.get(primaryObj.id) ?? primaryObj;
        const presentUpToStep = new Set(objectsAt(scene, anchor).map((o) => o.id));
        const rawLineOrigin =
          exactLine.point
          ?? exactLine.point_a
          ?? exactLine.endpoints?.[0]
          ?? (exactLine.endpoint_ids?.[0] ? exactById.get(exactLine.endpoint_ids[0])?.xyz : undefined);
        const lineOriginFrac = rawLineOrigin ? parseFracVec3(rawLineOrigin) : null;
        const lineDirFrac = (() => {
          if (exactLine.direction) return parseFracVec3(exactLine.direction);
          const pa =
            exactLine.point_a
            ?? exactLine.endpoints?.[0]
            ?? (exactLine.endpoint_ids?.[0] ? exactById.get(exactLine.endpoint_ids[0])?.xyz : undefined);
          const pb =
            exactLine.point_b
            ?? exactLine.endpoints?.[1]
            ?? (exactLine.endpoint_ids?.[1] ? exactById.get(exactLine.endpoint_ids[1])?.xyz : undefined);
          return pa && pb ? vSub(parseFracVec3(pb), parseFracVec3(pa)) : null;
        })();
        const commonPoints: SceneObject[] = [];
        if (lineOriginFrac && lineDirFrac && !vIsZero(lineDirFrac)) {
          for (const cand of scene.objects) {
            if (isSubEntity(cand.id) || cand.type !== "point3" || !presentUpToStep.has(cand.id)) continue;
            const ec = exactById.get(cand.id) ?? cand;
            if (!ec.xyz) continue;
            if (vIsZero(vCross(vSub(parseFracVec3(ec.xyz), lineOriginFrac), lineDirFrac)) && isCompactPointSym(shortSym(cand))) {
              commonPoints.push(cand);
            }
          }
        }
        const parallelEdgeInPlane = (plObj: SceneObject): string | null => {
          if (!lineDirFrac || vIsZero(lineDirFrac)) return null;
          const ldir = lineDirFrac;
          const ptIds = [...new Set([...(plObj.vertex_ids ?? []), ...(plObj.depends ?? [])])].filter((id) => {
            const o = byId.get(id);
            return Boolean(o && o.type === "point3" && presentUpToStep.has(id) && isCompactPointSym(shortSym(o)));
          });
          for (let i = 0; i < ptIds.length; i += 1) {
            for (let j = i + 1; j < ptIds.length; j += 1) {
              const pa = exactById.get(ptIds[i]) ?? byId.get(ptIds[i]);
              const pb = exactById.get(ptIds[j]) ?? byId.get(ptIds[j]);
              if (!pa?.xyz || !pb?.xyz) continue;
              const edgeVec = vSub(parseFracVec3(pb.xyz), parseFracVec3(pa.xyz));
              if (!vIsZero(edgeVec) && vParallel(edgeVec, ldir)) {
                return `${shortSym(byId.get(ptIds[i]))}${shortSym(byId.get(ptIds[j]))}`;
              }
            }
          }
          return null;
        };
        const derivedLineName =
          commonPoints.length === 2
            ? `${shortSym(commonPoints[0])}${shortSym(commonPoints[1])}`
            : "";
        const compactNot = primaryObj.notation?.trim() || derivedLineName;
        const hasCompactNot = Boolean(compactNot) && compactNot.length <= 8 && !/^Giao\s+tuyến/iu.test(compactNot);
        const p0Name = planeDeps[0] ? formatPlaneDisplayNotation(planeDeps[0], scene) : "";
        const p1Name = planeDeps[1] ? formatPlaneDisplayNotation(planeDeps[1], scene) : "";
        const title = planeDeps.length >= 2
          ? (hasCompactNot
            ? `Xác định giao tuyến ${compactNot} = ${p0Name} ∩ ${p1Name}`
            : `Xác định giao tuyến của ${p0Name} và ${p1Name}`)
          : (/^Giao\s+tuyến/iu.test(sym) ? `Xác định g${sym.slice(1)}` : `Xác định giao tuyến ${sym}`);
        const commonNames = commonPoints.map((p) => {
          if (p.role && /giao\s+điểm/iu.test(p.role) && p.role.length <= 36) {
            return `${shortSym(p)} (${p.role.replace(/\.$/, "").replace(/^Giao\b/u, "giao")})`;
          }
          return shortSym(p);
        });
        const par0 = planeDeps.length >= 2 ? parallelEdgeInPlane(planeDeps[0]) : null;
        const par1 = planeDeps.length >= 2 ? parallelEdgeInPlane(planeDeps[1]) : null;
        const subtitle = planeDeps.length >= 2
          ? (commonNames.length >= 2
            ? `Hai mặt phẳng ${p0Name} và ${p1Name} có hai điểm chung phân biệt ${commonNames.slice(0, 2).join(" và ")} nên giao tuyến là đường thẳng ${compactNot || "chung"}`
            : commonNames.length === 1 && par0 && par1 && par0 !== par1
              ? `Hai mặt phẳng ${p0Name} và ${p1Name} có điểm chung ${commonNames[0]} và lần lượt chứa hai đường thẳng song song ${par0}, ${par1} nên giao tuyến${hasCompactNot ? ` ${compactNot}` : ""} đi qua ${commonNames[0]} và song song với ${par0}, ${par1}`
              : commonNames.length === 1
                ? `Hai mặt phẳng ${p0Name} và ${p1Name} cắt nhau theo giao tuyến${hasCompactNot ? ` ${compactNot}` : ""} đi qua điểm chung ${commonNames[0]}`
                : `Tìm đường thẳng chung đi qua các điểm chung của hai mặt phẳng ${p0Name} và ${p1Name}`)
          : (primaryObj.role && primaryObj.role !== "Đường thẳng" && primaryObj.role !== "Đoạn thẳng"
            ? primaryObj.role
            : `Xác định đường thẳng chung của hai mặt phẳng cắt nhau`).replace(/«([^»]+)»/gu, "$1");
        return { title, subtitle, label: title };
      }
      const curvedSeg = classifyCurvedSegmentRole(scene, primaryObj);
      const curvedSym = sym
        .replace(/^(Đường\s+(?:cao|sinh|nối\s+tâm)|Chiều\s+cao|Bán\s+kính(?:\s+đáy)?|Trục|Đoạn\s+thẳng|Đoạn)\s+/iu, "")
        .trim() || sym;
      if (curvedSeg?.kind === "axis") {
        const isCone = curvedSeg.host.curved_kind === "cone";
        const depPts = (primaryObj.depends ?? [])
          .map((id) => byId.get(id))
          .filter((p): p is SceneObject => Boolean(p && p.type === "point3" && isCompactPointSym(shortSym(p))));
        if (isCone) {
          const apexKey = curvedSeg.host.apex_or_top?.join("|");
          const apexPt = depPts.find((p) => p.xyz?.join("|") === apexKey);
          const title = apexPt
            ? `Xác định đỉnh ${shortSym(apexPt)} và dựng đường cao (trục) ${curvedSym} của hình nón`
            : `Dựng đường cao (trục) ${curvedSym} của hình nón`;
          return {
            title,
            subtitle: `Nối đỉnh với tâm đáy xác định trục vuông góc mặt đáy của hình nón`,
            label: title,
          };
        }
        const title = depPts.length === 2
          ? `Xác định hai tâm ${shortSym(depPts[0])}, ${shortSym(depPts[1])} và dựng trục ${curvedSym} của hình trụ`
          : `Dựng trục ${curvedSym} của hình trụ`;
        return {
          title,
          subtitle: curvedSeg.isTiltedAxisInSpace
            ? `Nối hai tâm đáy xác định trục (đặt xiên trong không gian, vuông góc hai mặt đáy) của hình trụ tròn xoay`
            : `Nối hai tâm đáy tròn xác định trục vuông góc mặt đáy của hình trụ`,
          label: title,
        };
      }
      if (curvedSeg?.kind === "center_line") {
        const title = `Dựng đường nối tâm hai đáy ${curvedSym} của hình trụ xiên`;
        return {
          title,
          subtitle: `Đoạn ${curvedSym} nối tâm hai đáy tròn nhưng nghiêng với mặt phẳng đáy (không phải chiều cao vuông góc của hình trụ xiên)`,
          label: title,
        };
      }
      if (curvedSeg?.kind === "altitude") {
        const title = `Hạ đường vuông góc ${curvedSym} giữa hai mặt đáy của hình trụ xiên`;
        return {
          title,
          subtitle: `Khoảng cách vuông góc giữa hai mặt phẳng đáy song song của hình trụ xiên`,
          label: title,
        };
      }
      if (curvedSeg?.kind === "radius") {
        const depPts = (primaryObj.depends ?? [])
          .map((id) => byId.get(id))
          .filter((p): p is SceneObject => Boolean(p && p.type === "point3" && isCompactPointSym(shortSym(p))));
        if (curvedSeg.host.curved_kind === "ball") {
          const anchorKey = curvedSeg.host.anchor?.join("|");
          const centerPt = depPts.find((p) => p.xyz?.join("|") === anchorKey) ?? depPts[0];
          const rimPt = depPts.find((p) => p.id !== centerPt?.id);
          const title = centerPt && rimPt
            ? `Xác định tâm ${shortSym(centerPt)}, điểm ${shortSym(rimPt)} và dựng bán kính ${curvedSym} của mặt cầu`
            : `Dựng bán kính ${curvedSym} của mặt cầu`;
          return {
            title,
            subtitle: `Xác định khoảng cách từ tâm đến điểm thuộc mặt cầu làm bán kính R = ${curvedSym}`,
            label: title,
          };
        }
        const hostNoun = curvedSeg.host.curved_kind === "cone"
          ? "hình nón"
          : curvedSeg.isOblique
            ? "hình trụ xiên"
            : "hình trụ";
        const title = `Dựng bán kính đáy ${curvedSym} của ${hostNoun}`;
        return {
          title,
          subtitle: `Nối tâm đáy với điểm trên đường tròn đáy xác định bán kính R = ${curvedSym}`,
          label: title,
        };
      }
      if (curvedSeg?.kind === "generator") {
        const hostNoun = curvedSeg.host.curved_kind === "cylinder"
          ? (curvedSeg.isOblique ? " của hình trụ xiên" : " của hình trụ")
          : " của hình nón";
        const title = `Dựng đường sinh ${curvedSym}${hostNoun}`;
        return {
          title,
          subtitle:
            curvedSeg.host.curved_kind === "cylinder"
              ? `Nối hai điểm tương ứng trên hai đường tròn đáy tạo đường sinh ${curvedSym}`
              : `Nối đỉnh hình nón với điểm thuộc đường tròn đáy tạo đường sinh ${curvedSym}`,
          label: title,
        };
      }
      const noun = primaryObj.type === "segment3" ? "đoạn thẳng" : "đường thẳng";
      const depPts = (primaryObj.depends ?? [])
        .map((id) => byId.get(id))
        .filter((p): p is SceneObject => Boolean(p && p.type === "point3" && isCompactPointSym(shortSym(p))));
      const pRoles = primaryObj.formation_roles ?? [];
      const isFoundationSeg =
        pRoles.includes("CONSTRUCT_HEIGHT")
        || pRoles.includes("CONSTRUCT_LATERAL_BOUNDARY")
        || pRoles.includes("CONSTRUCT_BASE");
      if (
        (primaryObj.type === "line3" || (primaryObj.type === "segment3" && !isFoundationSeg && !isExplanatoryPerpSegment(primaryObj) && !isExplanatoryTargetSegment(primaryObj)))
        && depPts.length === 2
      ) {
        const [pa, pb] = [depPts[0].id, depPts[1].id];
        const priorObjsAtStart = startAnchor > 0 ? objectsAt(scene, startAnchor - 1) : [];
        const alreadyExistingEdge = priorObjsAtStart.some((po) => {
          if (!po || isSubEntity(po.id)) return false;
          if (po.type === "segment3") {
            const eps = po.endpoint_ids ?? po.depends ?? [];
            return eps.length === 2 && ((eps[0] === pa && eps[1] === pb) || (eps[0] === pb && eps[1] === pa));
          }
          if (po.type === "polygon3") {
            const vs = po.vertex_ids ?? po.depends ?? [];
            return vs.some((v, i) => {
              const nxt = vs[(i + 1) % vs.length];
              return (v === pa && nxt === pb) || (v === pb && nxt === pa);
            });
          }
          if (po.type === "solid" && po.vertex_ids && po.faces) {
            return po.faces.some((f) =>
              f.some((vi, k) => {
                const u = po.vertex_ids![vi];
                const v = po.vertex_ids![f[(k + 1) % f.length]];
                return (u === pa && v === pb) || (u === pb && v === pa);
              }),
            );
          }
          return false;
        });
        if (alreadyExistingEdge) {
          const title = primaryObj.type === "line3"
            ? `Xác định đường thẳng chứa cạnh ${sym}`
            : `Xác định cạnh ${sym} trên khối đã dựng`;
          const subtitle = primaryObj.type === "line3"
            ? `Xét đường thẳng đi qua cạnh ${sym} (${shortSym(depPts[0])}, ${shortSym(depPts[1])} đã thuộc hình) để phục vụ quan hệ không gian`
            : `Nhấn mạnh cạnh ${sym} (${shortSym(depPts[0])}, ${shortSym(depPts[1])} đã thuộc hình) để phục vụ quan hệ không gian`;
          return { title, subtitle, label: title };
        }
      }
      const title = `Dựng ${noun} ${sym}`;
      const genericRole = !primaryObj.role || primaryObj.role === "Đường thẳng" || primaryObj.role === "Đoạn thẳng";
      const fallbackSub = depPts.length === 2
        ? (primaryObj.type === "segment3"
          ? `Nối hai điểm ${shortSym(depPts[0])} và ${shortSym(depPts[1])} tạo đoạn thẳng ${sym}`
          : `Đường thẳng xác định đi qua hai điểm ${shortSym(depPts[0])} và ${shortSym(depPts[1])}`)
        : `Xác định ${noun} ${sym} từ hai điểm đã dựng`;
      return {
        title,
        subtitle: (genericRole ? fallbackSub : primaryObj.role!).replace(/«([^»]+)»/gu, "$1"),
        label: title,
      };
    }
  }

  const rawTitle = (
    geometryActionLabelAt(scene, anchor)
    || (lastEv?.display_label && learnerTextIsSafe(scene, lastEv.display_label) ? lastEv.display_label : null)
    || geometryNarrationAt(scene, anchor)
    || "Bước dựng hình"
  ).replace(/«([^»]+)»/gu, "$1");
  const rawSub = geometryNarrationAt(scene, anchor)?.replace(/«([^»]+)»/gu, "$1") ?? null;
  return {
    title: rawTitle,
    subtitle: rawSub && rawSub !== rawTitle ? rawSub : "",
    label: rawTitle,
  };
}

export interface PedagogicalDagEdge {
  from: number;
  to: number;
  reason: string;
}

export type GoalCompletionKind =
  | "intersection_line"
  | "intersection_point"
  | "section"
  | "distance"
  | "angle"
  | "length"
  | "area"
  | "volume"
  | "radius"
  | "construction";

export type GoalCompletionStatus = "reached" | "unverified_or_contradictory" | "missing_goal_output";

export interface GoalCompletionItem {
  id: string;
  kind: GoalCompletionKind;
  label: string;
  valueText: string | null;
  witnessSummary: string | null;
  reachedAtStepIndex: number | null;
  reachedStepTitle: string | null;
  carrierIds: string[];
  provenance: CanonicalMathProvenance;
}

export interface GoalCompletionSummary {
  status: GoalCompletionStatus;
  primaryKind: GoalCompletionKind;
  headline: string;
  detail: string;
  items: GoalCompletionItem[];
  reachedAtStepIndex: number | null;
}

export interface PedagogicalConstructionPlan {
  scene: Scene3D;
  steps: PedagogicalStepItem[];
  dagEdges: PedagogicalDagEdge[];
  reordered: boolean;
  goalCompletion: GoalCompletionSummary;
}

const PEDAGOGICAL_CATEGORY_LABELS: Record<PedagogicalEpistemicCategory, string> = {
  given: "Đề cho",
  derived: "Được suy ra",
  constructed: "Được dựng",
  auxiliary: "Hình phụ",
  conclusion: "Kết luận mục tiêu",
};

const PEDAGOGICAL_STEP_ROLE_LABELS: Record<PedagogicalStepRole, string> = {
  identify_given: "Xác định dữ kiện",
  construct_geometry: "Dựng hình học",
  identify_auxiliary: "Xác định đối tượng phụ",
  deduce_relation: "Suy luận quan hệ",
  construct_intersection_or_section: "Dựng giao tuyến hoặc thiết diện",
  emphasize_result: "Nhấn mạnh kết quả",
  conclude_and_calculate: "Kết luận và tính toán",
};

function buildGoalCompletionSummary(scene: Scene3D, steps: PedagogicalStepItem[]): GoalCompletionSummary {
  const mathCheck = verifySceneMathematicalConsistency(scene);
  if (!mathCheck.valid) {
    const first = mathCheck.contradictions[0];
    return {
      status: "unverified_or_contradictory",
      primaryKind: "construction",
      headline: first?.title || "Dữ kiện hoặc kết quả chưa nhất quán toán học",
      detail: first?.explanation || "Hệ thống từ chối kết luận mục tiêu do phát hiện mâu thuẫn hình học.",
      items: [],
      reachedAtStepIndex: null,
    };
  }
  if (steps.length === 0) {
    return {
      status: "missing_goal_output",
      primaryKind: "construction",
      headline: "Chưa có bước dựng hoàn thành mục tiêu",
      detail: "Cảnh hiện tại chưa có trình tự dựng hình hoặc đại lượng mục tiêu hợp lệ.",
      items: [],
      reachedAtStepIndex: null,
    };
  }

  const byId = new Map(scene.objects.map((o) => [o.id, o]));
  const cuttingDistGivens = certifiedCuttingPlaneDistanceGivens(scene);
  const derivedQuantities = scene.objects.filter(
    (o) =>
      o.type === "quantity"
      && o.origin !== "free"
      && o.annotation?.role !== "given"
      && (o.source as Record<string, unknown> | undefined)?.is_given !== true
      && o.annotation?.role !== "intermediate"
      && o.annotation?.category !== "measurement",
  );

  if (derivedQuantities.length > 0) {
    const items: GoalCompletionItem[] = derivedQuantities.map((q) => {
      const rawLabel = q.label ?? q.notation ?? q.id;
      const hadGuillemets = rawLabel.includes("«");
      const cleanLabel = rawLabel.replace(/«([^»]+)»/gu, "$1").trim();
      const annKind = q.annotation?.kind;
      let kind: GoalCompletionKind = "length";
      if (annKind === "distance") kind = "distance";
      else if (annKind === "angle" || /\bgóc\s+giữa\b/iu.test(cleanLabel)) kind = "angle";
      else if (annKind === "area" || /^Diện\s+tích\b/iu.test(cleanLabel)) kind = "area";
      else if (annKind === "volume" || /^Thể\s+tích\b/iu.test(cleanLabel)) kind = "volume";
      else if (/^Bán\s+kính\b/iu.test(cleanLabel)) kind = "radius";
      else if (
        /^Khoảng\s+cách\b/iu.test(cleanLabel)
        && (
          q.annotation?.witness
          || (q.depends ?? []).some((id) => {
            const t = byId.get(id)?.type;
            return t === "plane3" || t === "polygon3" || t === "line3";
          })
        )
      ) {
        kind = "distance";
      }

      const qSubjects = new Set([...(q.annotation?.subject_ids ?? []), ...(q.depends ?? [])]);
      const synthSeg = scene.objects.find((cand) => {
        if (!isExplanatoryPerpSegment(cand) && !isExplanatoryTargetSegment(cand)) return false;
        const candDeps = cand.depends ?? [];
        return candDeps.length > 0 && candDeps.some((d) => qSubjects.has(d));
      });
      const measEvIdx = scene.events.findIndex((ev) => ev.action === "MEASURE" && ev.object === q.id);
      const revSteps = [...steps].reverse();
      const reachedStep =
        (synthSeg ? revSteps.find((st) => st.targetIds.includes(synthSeg.id)) : undefined)
        ?? (measEvIdx >= 0 ? revSteps.find((st) => measEvIdx >= st.startAnchor && measEvIdx <= st.anchor) : undefined)
        ?? steps[steps.length - 1];

      const rawProv = classifySceneEntityProvenance(scene, q);
      const provenance: CanonicalMathProvenance = rawProv === "GIVEN" ? "DERIVED_VERIFIED" : rawProv;
      const isVerifiedResult = provenance === "DERIVED_VERIFIED";
      let valueText: string | null = isVerifiedResult
        ? (hienBieuThucDaiLuong(q)?.trim() || q.value?.trim() || null)
        : null;
      if (valueText && q.annotation?.unit && !valueText.includes(q.annotation.unit)) {
        valueText = `${valueText} ${q.annotation.unit}`;
      }
      if (valueText) {
        const scaleNote = ghiChuGiaTriDung(scene, valueText, q.annotation?.kind);
        // Chỉ đính kèm ghi chú chuẩn hóa khi length_unit thiếu display_scale (tránh đổi chuỗi kỳ vọng trên các cảnh đã khai báo display_scale)
        if (scaleNote && !scene.length_unit?.display_scale) {
          valueText = `${valueText}${scaleNote}`;
        }
      }

      let displayLabel = kind === "angle" && /côsin\s+bình\s+phương\s+của\s+/iu.test(cleanLabel)
        ? cleanLabel.replace(/^Côsin\s+bình\s+phương\s+của\s+/iu, "").replace(/^góc/u, "Góc")
        : cleanLabel;

      const singleDep = (q.depends ?? []).length === 1 ? byId.get(q.depends![0]) : undefined;
      if (singleDep?.type === "circle3" && vaiTroMien(singleDep) === "section" && /Đường\s+tròn\s+giao\s+của\s+khối\s+cong/iu.test(cleanLabel)) {
        if (kind === "radius") displayLabel = "Bán kính đường tròn thiết diện";
        else if (kind === "area") displayLabel = "Diện tích hình tròn thiết diện";
      } else if (singleDep?.type === "curved_solid") {
        if (singleDep.curved_kind === "ball" && !singleDep.notation?.includes("(S)") && /\(S\)/u.test(cleanLabel)) {
          if (kind === "radius") displayLabel = "Bán kính mặt cầu";
          else if (kind === "volume") displayLabel = "Thể tích khối cầu";
          else if (kind === "area") displayLabel = "Diện tích mặt cầu";
        } else if (hadGuillemets && singleDep.curved_kind === "cylinder") {
          if (kind === "volume") displayLabel = "Thể tích khối trụ";
          else if (kind === "area" && /^Diện\s+tích\s+mặt\s+cong/iu.test(cleanLabel)) displayLabel = "Diện tích xung quanh hình trụ";
        } else if (hadGuillemets && singleDep.curved_kind === "cone") {
          if (kind === "volume") displayLabel = "Thể tích khối nón";
          else if (kind === "area" && /^Diện\s+tích\s+mặt\s+cong/iu.test(cleanLabel)) displayLabel = "Diện tích xung quanh hình nón";
        }
      }

      let witnessSummary: string | null = null;
      if (provenance === "UNDERDETERMINED") {
        witnessSummary = "Bản ghi chưa có chứng nhận xác định duy nhất giá trị đại lượng này.";
      } else if (!isVerifiedResult) {
        witnessSummary = "Đại lượng chưa có chứng chỉ suy dẫn hợp lệ từ dữ kiện đề bài.";
      } else if (kind === "angle" && /côsin\s+bình\s+phương/iu.test(cleanLabel) && valueText) {
        const { exactDegree, cosSqText } = formatCosSquaredConclusion(valueText);
        valueText = exactDegree ? `${exactDegree} (cos² φ = ${cosSqText})` : `cos² φ = ${cosSqText}`;
        if (exactDegree === "90°") {
          witnessSummary = "cos² φ = 0 ⇒ quan hệ vuông góc 90°";
        }
      }
      const w = isVerifiedResult ? (synthSeg?.perpendicular_witness ?? q.annotation?.witness) : undefined;
      if (isVerifiedResult && w?.relation === "common_perpendicular") {
        const l1 = w.on ? byId.get(w.on) : undefined;
        const l2 = w.second?.on ? byId.get(w.second.on) : (w.from ? byId.get(w.from) : undefined);
        const segSym = synthSeg ? shortSym(synthSeg) : "đoạn vuông góc chung";
        witnessSummary = l1 && l2
          ? `Đoạn vuông góc chung ${segSym} ⊥ ${shortSym(l1)} và ${segSym} ⊥ ${shortSym(l2)}`
          : `Đoạn vuông góc chung ${segSym}`;
      } else if (isVerifiedResult && w?.on && synthSeg) {
        const onObj = byId.get(w.on);
        const onName = onObj ? (onObj.type === "plane3" ? formatPlaneDisplayNotation(onObj) : shortSym(onObj)) : "";
        witnessSummary = onName ? `Đoạn vuông góc ${shortSym(synthSeg)} ⊥ ${onName}` : `Đoạn vuông góc ${shortSym(synthSeg)}`;
      } else if (isVerifiedResult && w?.on && w.from && w.foot) {
        const fromObj = byId.get(w.from);
        const onObj = byId.get(w.on);
        const onName = onObj ? (onObj.type === "plane3" ? formatPlaneDisplayNotation(onObj) : shortSym(onObj)) : "";
        const exactScene = exactSceneOriginOf(scene);
        const exactById = new Map(exactScene.objects.map((o) => [o.id, o]));
        const wExFoot = (exactById.get(q.id)?.annotation?.witness ?? w).foot;
        const footPt = wExFoot
          ? scene.objects.find((cand) => {
              if (isSubEntity(cand.id) || cand.type !== "point3") return false;
              const ec = exactById.get(cand.id) ?? cand;
              return Boolean(
                ec.xyz
                  && vIsZero(vSub(parseFracVec3(ec.xyz), parseFracVec3(wExFoot)))
                  && isCompactPointSym(shortSym(cand)),
              );
            })
          : undefined;
        if (fromObj && footPt && onName) {
          witnessSummary = `Đoạn vuông góc ${shortSym(fromObj)}${shortSym(footPt)} ⊥ ${onName}`;
        }
      } else if (isVerifiedResult && synthSeg) {
        witnessSummary = `Đoạn thẳng mục tiêu ${shortSym(synthSeg)}`;
      } else if (isVerifiedResult && singleDep?.type === "circle3" && vaiTroMien(singleDep) === "section" && valueText) {
        const hostBall = (singleDep.depends ?? []).map((id) => byId.get(id)).find((o) => o?.type === "curved_solid" && o.curved_kind === "ball");
        const cutDist = cuttingDistGivens.find((cd) => cd.circleId === singleDep.id);
        if (kind === "radius" && hostBall && cutDist) {
          const radGiven = (hostBall.depends ?? [])
            .map((id) => byId.get(id))
            .find((o) => o?.type === "quantity" && classifyQuantityProvenance(o, scene) === "GIVEN");
          const radSym = radGiven?.notation?.trim() || "R";
          const radVal = radGiven ? (hienBieuThucDaiLuong(radGiven)?.trim() || radGiven.value?.trim()) : null;
          if (radVal) {
            witnessSummary = `${radSym} = ${radVal}, ${cutDist.notation} = ${cutDist.valueDisplay} ⇒ r = √(${radSym}² − d²) = ${valueText}`;
          }
        } else if (kind === "area") {
          witnessSummary = `S = πr² = ${valueText}`;
        }
      }

      const carrierIds = [
        ...(synthSeg ? [synthSeg.id] : []),
        ...(q.depends ?? []),
      ].filter((id) => byId.has(id));

      return {
        id: q.id,
        kind,
        label: displayLabel,
        valueText,
        witnessSummary,
        reachedAtStepIndex: reachedStep ? reachedStep.index : null,
        reachedStepTitle: reachedStep ? reachedStep.title : null,
        carrierIds,
        provenance,
      };
    });

    if (items.some((it) => it.provenance === "INVALID")) {
      const invalidItem = items.find((it) => it.provenance === "INVALID") ?? items[items.length - 1];
      return {
        status: "unverified_or_contradictory",
        primaryKind: invalidItem.kind,
        headline: `Chưa kiểm chứng được: ${invalidItem.label}`,
        detail: "Đại lượng kết quả thiếu nguồn suy dẫn hợp lệ hoặc mâu thuẫn dữ kiện nên không công bố đáp số.",
        items,
        reachedAtStepIndex: null,
      };
    }

    if (items.some((it) => it.provenance !== "DERIVED_VERIFIED")) {
      const missingLabels = items
        .filter((it) => it.provenance !== "DERIVED_VERIFIED")
        .map((it) => it.label)
        .join(", ");
      const primary = items.find((it) => it.provenance !== "DERIVED_VERIFIED") ?? items[items.length - 1];
      return {
        status: "missing_goal_output",
        primaryKind: primary.kind,
        headline: `Chưa kiểm chứng được mục tiêu: ${missingLabels}`,
        detail: "Bản ghi chưa có chứng nhận kết quả mục tiêu. Trạng thái này chưa xác định đề bài có đủ dữ kiện hay không.",
        items,
        reachedAtStepIndex: null,
      };
    }

    const primary = items[items.length - 1];
    const headline = items
      .map((it) => (it.valueText ? `${it.label}: ${it.valueText}` : it.label))
      .join(" · ");
    const detail = primary.witnessSummary
      ? `${primary.witnessSummary} (Bước ${(primary.reachedAtStepIndex ?? steps.length - 1) + 1}/${steps.length})`
      : `Xác định tại Bước ${(primary.reachedAtStepIndex ?? steps.length - 1) + 1}/${steps.length}: ${primary.reachedStepTitle ?? ""}`;
    return {
      status: "reached",
      primaryKind: primary.kind,
      headline,
      detail,
      items,
      reachedAtStepIndex: primary.reachedAtStepIndex ?? steps.length - 1,
    };
  }

  const lastStep = steps[steps.length - 1];
  const lastTargetObjs = lastStep.targetIds.map((id) => byId.get(id)).filter((o): o is SceneObject => Boolean(o));
  const secObj =
    lastTargetObjs.find((o) => o.type === "section" || ((o.type === "circle3" || o.type === "ellipse3" || o.type === "polygon3") && vaiTroMien(o) === "section"))
    ?? scene.objects.find((o) => !isSubEntity(o.id) && (o.type === "section" || ((o.type === "circle3" || o.type === "ellipse3") && vaiTroMien(o) === "section")));
  if (secObj) {
    const secStep = [...steps].reverse().find((st) => st.targetIds.includes(secObj.id)) ?? lastStep;
    const secProv = classifySceneEntityProvenance(scene, secObj);
    return {
      status: secProv === "INVALID" ? "unverified_or_contradictory" : "reached",
      primaryKind: "section",
      headline: secStep.title,
      detail: secStep.subtitle || `Hoàn thành tại Bước ${secStep.index + 1}/${steps.length}`,
      items: [
        {
          id: secObj.id,
          kind: "section",
          label: secStep.title,
          valueText: null,
          witnessSummary: secStep.subtitle || null,
          reachedAtStepIndex: secProv === "INVALID" ? null : secStep.index,
          reachedStepTitle: secStep.title,
          carrierIds: [secObj.id],
          provenance: secProv === "GIVEN" ? "DERIVED_VERIFIED" : secProv,
        },
      ],
      reachedAtStepIndex: secProv === "INVALID" ? null : secStep.index,
    };
  }

  const interLine = lastTargetObjs.find((o) => isIntersectionLineOrSegment(o, scene));
  if (interLine) {
    const lineProv = classifySceneEntityProvenance(scene, interLine);
    return {
      status: lineProv === "INVALID" ? "unverified_or_contradictory" : "reached",
      primaryKind: "intersection_line",
      headline: lastStep.title,
      detail: lastStep.subtitle || `Hoàn thành tại Bước ${lastStep.index + 1}/${steps.length}`,
      items: [
        {
          id: interLine.id,
          kind: "intersection_line",
          label: lastStep.title,
          valueText: null,
          witnessSummary: lastStep.subtitle || null,
          reachedAtStepIndex: lineProv === "INVALID" ? null : lastStep.index,
          reachedStepTitle: lastStep.title,
          carrierIds: [interLine.id, ...(interLine.depends ?? [])],
          provenance: lineProv === "GIVEN" ? "DERIVED_VERIFIED" : lineProv,
        },
      ],
      reachedAtStepIndex: lineProv === "INVALID" ? null : lastStep.index,
    };
  }

  const interPt = lastTargetObjs.find((o) => o.type === "point3" && o.origin === "derived");
  if (interPt) {
    const ptProv = classifySceneEntityProvenance(scene, interPt);
    return {
      status: ptProv === "INVALID" ? "unverified_or_contradictory" : "reached",
      primaryKind: "intersection_point",
      headline: lastStep.title,
      detail: lastStep.subtitle || `Hoàn thành tại Bước ${lastStep.index + 1}/${steps.length}`,
      items: [
        {
          id: interPt.id,
          kind: "intersection_point",
          label: lastStep.title,
          valueText: null,
          witnessSummary: lastStep.subtitle || null,
          reachedAtStepIndex: ptProv === "INVALID" ? null : lastStep.index,
          reachedStepTitle: lastStep.title,
          carrierIds: [interPt.id, ...(interPt.depends ?? [])],
          provenance: ptProv === "GIVEN" ? "DERIVED_VERIFIED" : ptProv,
        },
      ],
      reachedAtStepIndex: ptProv === "INVALID" ? null : lastStep.index,
    };
  }

  return {
    status: "reached",
    primaryKind: "construction",
    headline: lastStep.title,
    detail: lastStep.subtitle || `Hoàn thành dựng hình tại Bước ${lastStep.index + 1}/${steps.length}`,
    items: [
      {
        id: lastStep.targetIds[0] ?? "goal",
        kind: "construction",
        label: lastStep.title,
        valueText: null,
        witnessSummary: null,
        reachedAtStepIndex: lastStep.index,
        reachedStepTitle: lastStep.title,
        carrierIds: [...lastStep.targetIds],
        provenance: lastStep.provenance,
      },
    ],
    reachedAtStepIndex: lastStep.index,
  };
}

interface CachedPedPlanEntry {
  plan: PedagogicalConstructionPlan;
  hybrid: unknown;
  sig: string;
}

function sceneCacheSignature(scene: Scene3D): string {
  const objSig = scene.objects
    .map((o) => {
      const coord = o.xyz ?? o.center ?? o.anchor ?? o.point ?? o.point_a ?? o.endpoints?.[0];
      const aux = o.normal ?? o.direction ?? o.apex_or_top ?? o.point_b ?? o.endpoints?.[1];
      return `${o.id}:${o.type}:${coord ? coord.join(",") : ""}:${aux ? aux.join(",") : ""}:${o.radius_sq ?? ""}:${o.value ?? ""}`;
    })
    .join(";");
  const evSig = scene.events
    .map((ev) => `${ev.step_index}:${ev.action}:${ev.object ?? ""}:${(ev.objects ?? []).join(",")}`)
    .join(";");
  return `${scene.objects.length}|${scene.events.length}|${objSig}#${evSig}`;
}

const _pedPlanCache = new WeakMap<Scene3D, CachedPedPlanEntry>();
const _pedPlanNoSplitCache = new WeakMap<Scene3D, CachedPedPlanEntry>();

/**
 * Tách cạnh cao được chứng nhận vuông góc (`perpendicular_witness` đường ⊥ mặt đáy) khỏi sự kiện bó chung
 * `CONSTRUCT_LATERAL_BOUNDARY` (khi backend gộp `SA` vào cùng sự kiện `canh_ben` với `SB, SC, SD`).
 * Tuyệt đối KHÔNG tự sinh bước `SA ⊥ (ABCD)` khi dữ kiện không có nhân chứng vuông góc hợp lệ.
 */
function splitBundledCertifiedHeight(baseScene: Scene3D): { scene: Scene3D; didSplit: boolean } {
  const byId = new Map(baseScene.objects.map((o) => [o.id, o]));
  let targetEventIdx = -1;
  let heightId = "";
  let restIds: string[] = [];

  for (let k = 0; k < baseScene.events.length; k += 1) {
    const ev = baseScene.events[k];
    if (ev.action !== "CREATE") continue;
    const rawIds = ev.objects && ev.objects.length > 0
      ? ev.objects
      : ev.object
        ? [ev.object]
        : [];
    const semIds = rawIds.filter((id) => byId.has(id));
    if (semIds.length < 2) continue;
    const allPureLateral = semIds.every((id) => {
      const o = byId.get(id);
      const roles = o?.formation_roles ?? [];
      return o?.type === "segment3" && roles.includes("CONSTRUCT_LATERAL_BOUNDARY") && !roles.includes("CONSTRUCT_HEIGHT");
    });
    if (!allPureLateral) continue;

    const certIds = semIds.filter((id) => {
      const o = byId.get(id)!;
      const w = o.perpendicular_witness;
      if (!w?.marker?.v) return false;
      const vPerp = parseFracVec3(w.marker.v);
      if (vIsZero(vPerp)) return false;
      const onObj = w.on ? byId.get(w.on) : undefined;
      const isLinePlane =
        isLinePerpPlaneRelation(w.relation)
        || Boolean(w.plane_directions && w.plane_directions.length >= 2)
        || onObj?.surface_role === "BASE_REGION";
      if (!isLinePlane) return false;
      return (w.plane_directions ?? []).every((pd) =>
        fIsZero(metricDot(vPerp, parseFracVec3(pd), baseScene.chart_metric)),
      );
    });

    if (certIds.length === 1) {
      targetEventIdx = k;
      heightId = certIds[0];
      restIds = semIds.filter((id) => id !== heightId);
      break;
    }
  }

  if (targetEventIdx < 0 || !heightId || restIds.length === 0) {
    return { scene: baseScene, didSplit: false };
  }

  const hObj = byId.get(heightId)!;
  const newObjects = baseScene.objects.map((o) =>
    o.id === heightId
      ? {
          ...o,
          formation_roles: [...new Set([...(o.formation_roles ?? []), "CONSTRUCT_HEIGHT"])],
        }
      : o,
  );

  const origEv = baseScene.events[targetEventIdx];
  const evHeight: SceneEvent = {
    step_index: targetEventIdx,
    action: "CREATE",
    object: heightId,
    objects: [heightId],
    depends: [...(hObj.depends ?? [])],
    explanation: `Dựng ${hObj.label}.`,
    semantic_kind: "GEOMETRY_CONSTRUCTION",
  };
  const evRest: SceneEvent = {
    ...origEv,
    object: origEv.object && origEv.object !== heightId ? origEv.object : restIds[0],
    objects: restIds,
    depends: restIds,
  };

  const newEvents: SceneEvent[] = [];
  for (let k = 0; k < baseScene.events.length; k += 1) {
    if (k === targetEventIdx) {
      newEvents.push({ ...evHeight, step_index: newEvents.length });
      newEvents.push({ ...evRest, step_index: newEvents.length });
    } else {
      newEvents.push({ ...baseScene.events[k], step_index: newEvents.length });
    }
  }

  let newFormation = baseScene.formation;
  if (baseScene.formation && baseScene.formation.steps.length === baseScene.events.length) {
    const restSet = new Set(restIds);
    const origStep = baseScene.formation.steps[targetEventIdx];
    const stepHeight: FormationStep = {
      ...origStep,
      step_index: targetEventIdx,
      visible_ids: origStep.visible_ids.filter((id) => !restSet.has(id)),
      focus_ids: [heightId, ...(hObj.depends ?? [])],
      learner_text: `Dựng ${hObj.label}.`,
      semantic_kind: "GEOMETRY_CONSTRUCTION",
    };
    const newSteps: FormationStep[] = [];
    for (let k = 0; k < baseScene.formation.steps.length; k += 1) {
      if (k === targetEventIdx) {
        newSteps.push({ ...stepHeight, step_index: newSteps.length });
        newSteps.push({ ...origStep, step_index: newSteps.length });
      } else {
        newSteps.push({ ...baseScene.formation.steps[k], step_index: newSteps.length });
      }
    }
    newFormation = { steps: newSteps };
  }

  return {
    scene: {
      ...baseScene,
      objects: newObjects,
      events: newEvents,
      ...(newFormation ? { formation: newFormation } : {}),
    },
    didSplit: true,
  };
}

function isPrimaryCurvedSolid(scene: Pick<Scene3D, "objects" | "events">, cs: SceneObject): boolean {
  if (cs.type !== "curved_solid") return false;
  if (cs.curved_kind === "ball") {
    return classifySphereSemanticRole(scene, cs) === "STANDALONE_SPHERE";
  }
  if (cs.curved_kind !== "cylinder" && cs.curved_kind !== "cone") return false;
  if (isSecondaryCutCurvedSolid(scene, cs)) return false;
  return true;
}

/**
 * Triển khai nền tảng dựng hình sư phạm tường minh cho khối tròn xoay sơ cấp (`cylinder`, `cone`, `STANDALONE_SPHERE`)
 * từ chính các tâm, đỉnh, điểm vành và bán kính đã được Kernel chứng nhận trên `curved_solid`:
 * - Hình trụ: trục (hoặc đường nối tâm hai đáy) `OO′` → bán kính đáy (nếu có điểm vành) → hai đường tròn đáy → mặt xung quanh.
 * - Hình nón: bán kính đáy (nếu có điểm vành) → đường tròn đáy → đường cao/trục `SO` → mặt xung quanh.
 * - Mặt cầu độc lập có điểm trên mặt cầu (`I, A`): bán kính `IA` → mặt cầu `(I; IA)`.
 * Tuyệt đối KHÔNG tự bịa thêm điểm mới không có trong đề bài và KHÔNG nhân đôi vành đáy (đã đồng bộ với `boVanhDayTrung`).
 */
function expandPrimaryCurvedFoundation(baseScene: Scene3D): { scene: Scene3D; didExpand: boolean } {
  const exactRefForChart = exactSceneOriginOf(baseScene);
  const chartT = baseScene !== exactRefForChart ? maTranKhung(exactRefForChart) : null;
  const gMetric = isSceneWorldTransformed(exactRefForChart) ? undefined : exactRefForChart.chart_metric;
  const buildCurvedAxisPerpWitness = (
    footPt: SceneObject,
    fromPt: SceneObject,
    footDisp: ExactVec3,
    fromDisp: ExactVec3,
    footEx: FracVec3,
    fromEx: FracVec3,
    rimObj: SceneObject | undefined,
    onCircleId: string,
  ): NonNullable<SceneObject["perpendicular_witness"]> | null => {
    const vEx = vSub(fromEx, footEx);
    const vNormSq = metricDot(vEx, vEx, gMetric);
    if (vIsZero(vEx) || fIsZero(vNormSq)) return null;
    let uEx: FracVec3 | null = null;
    let uToId: string | undefined;
    if (rimObj) {
      const exRim = exactRefForChart.objects.find((o) => o.id === rimObj.id) ?? rimObj;
      if (exRim.xyz) {
        const candU = vSub(parseFracVec3(exRim.xyz), footEx);
        if (!vIsZero(candU) && fIsZero(metricDot(candU, vEx, gMetric))) {
          uEx = candU;
          uToId = rimObj.id;
        }
      }
    }
    if (!uEx) {
      const seeds: FracVec3[] = [
        [[1n, 1n], [0n, 1n], [0n, 1n]],
        [[0n, 1n], [1n, 1n], [0n, 1n]],
        [[0n, 1n], [0n, 1n], [1n, 1n]],
      ];
      for (const e of seeds) {
        const dotEV = metricDot(e, vEx, gMetric);
        const scale = fDiv(dotEV, vNormSq);
        const orthoE = vSub(e, [fMul(scale, vEx[0]), fMul(scale, vEx[1]), fMul(scale, vEx[2])]);
        if (!vIsZero(orthoE) && fIsZero(metricDot(orthoE, vEx, gMetric))) {
          uEx = orthoE;
          break;
        }
      }
    }
    if (!uEx) return null;
    return {
      from: fromPt.id,
      from_point: fromDisp,
      on: onCircleId,
      foot: footDisp,
      foot_id: footPt.id,
      relation: "line_perp_plane",
      can_present_as_proven: true,
      marker: {
        u: mapExactVecToSceneFrame(uEx, chartT),
        v: mapExactVecToSceneFrame(vEx, chartT),
        ...(uToId ? { u_to: uToId } : {}),
      },
    };
  };
  const exactRef = exactSceneOriginOf(baseScene);
  const exactById = new Map(exactRef.objects.map((o) => [o.id, o]));
  let curScene = baseScene;
  let didExpand = false;

  const curvedCandidates = baseScene.objects.filter(
    (o) => o.type === "curved_solid" && isPrimaryCurvedSolid(baseScene, o),
  );

  for (const rawCs of curvedCandidates) {
    const byId = new Map(curScene.objects.map((o) => [o.id, o]));
    const cs = byId.get(rawCs.id);
    if (!cs) continue;
    const evIdx = curScene.events.findIndex(
      (ev) => ev.action === "CREATE" && (ev.object === cs.id || (ev.objects ?? []).includes(cs.id)),
    );
    if (evIdx < 0) continue;

    const presentAtOrBeforeCsIds = new Set<string>(curScene.free_objects ?? []);
    for (const o of curScene.objects) {
      if (o.origin === "free") presentAtOrBeforeCsIds.add(o.id);
    }
    for (let k = 0; k <= evIdx; k += 1) {
      const ev = curScene.events[k];
      if (!ev || (ev.action !== "CREATE" && ev.action !== "INIT")) continue;
      if (ev.object) presentAtOrBeforeCsIds.add(ev.object);
      for (const oid of ev.objects ?? []) presentAtOrBeforeCsIds.add(oid);
    }

    const exactCs = exactById.get(cs.id) ?? cs;
    const hasSegKind = (kind: "axis" | "center_line" | "radius"): boolean =>
      curScene.objects.some((o) => {
        if (isSubEntity(o.id) || o.type !== "segment3") return false;
        const r = classifyCurvedSegmentRole(curScene, o);
        return Boolean(r && r.host.id === cs.id && r.kind === kind);
      });
    const hasExistingBallFoundationRadius = (): boolean =>
      curScene.objects.some((o) => {
        if (isSubEntity(o.id) || o.type !== "segment3") return false;
        if (!presentAtOrBeforeCsIds.has(o.id)) return false;
        if (o.perpendicular_witness) return false;
        const r = classifyCurvedSegmentRole(curScene, o);
        return Boolean(r && r.host.id === cs.id && r.kind === "radius");
      });

    const hasBaseCircleAt = (targetCenterExact: ExactVec3): boolean => {
      const targetV = parseFracVec3(targetCenterExact);
      return curScene.objects.some((o) => {
        if (o.type !== "circle3" || (o.surface_role !== "BASE_REGION" && (o.surface_role as string) !== "TOP_BASE_REGION")) return false;
        const eo = exactById.get(o.id) ?? o;
        return Boolean(eo.center && vIsZero(vSub(parseFracVec3(eo.center), targetV)));
      });
    };

    const depPts = (cs.depends ?? [])
      .map((id) => byId.get(id))
      .filter((p): p is SceneObject => Boolean(p && p.type === "point3" && p.xyz));

    const matchPointAtExact = (targetExact: ExactVec3 | undefined): SceneObject | undefined => {
      if (!targetExact) return undefined;
      const tv = parseFracVec3(targetExact);
      const fromDeps = depPts.find((p) => {
        const ep = exactById.get(p.id) ?? p;
        return Boolean(ep.xyz && vIsZero(vSub(parseFracVec3(ep.xyz), tv)));
      });
      if (fromDeps) return fromDeps;
      return curScene.objects.find((p) => {
        if (isSubEntity(p.id) || p.type !== "point3") return false;
        const ep = exactById.get(p.id) ?? p;
        return Boolean(ep.xyz && vIsZero(vSub(parseFracVec3(ep.xyz), tv)));
      });
    };

    const insertedObjs: SceneObject[] = [];

    if (cs.curved_kind === "ball" && exactCs.anchor && cs.anchor) {
      const centerPt = matchPointAtExact(exactCs.anchor);
      const rSqFrac = exactCs.radius_sq ? parseExactFrac(exactCs.radius_sq) : null;
      const anchorEx = parseFracVec3(exactCs.anchor);
      let rimPt = depPts.find((p) => p.id !== centerPt?.id && presentAtOrBeforeCsIds.has(p.id));
      if (!rimPt && centerPt && rSqFrac && rSqFrac[0] > 0n) {
        rimPt = curScene.objects.find((p) => {
          if (isSubEntity(p.id) || p.type !== "point3" || p.id === centerPt.id || !p.xyz) return false;
          if (!presentAtOrBeforeCsIds.has(p.id) || p.origin !== "free") return false;
          const ep = exactById.get(p.id) ?? p;
          if (!ep.xyz) return false;
          const diff = vSub(parseFracVec3(ep.xyz), anchorEx);
          return fEq(metricDot(diff, diff, gMetric), rSqFrac);
        });
      }
      if (!rimPt && centerPt?.xyz && rSqFrac && rSqFrac[0] > 0n && !byId.has(`${cs.id}__ref_pt`) && !hasExistingBallFoundationRadius()) {
        const seedDirs: FracVec3[] = [
          [[0n, 1n], [1n, 1n], [0n, 1n]],
          [[-1n, 1n], [0n, 1n], [0n, 1n]],
          [[-3n, 1n], [4n, 1n], [0n, 1n]],
          [[3n, 1n], [4n, 1n], [0n, 1n]],
          [[-4n, 1n], [3n, 1n], [0n, 1n]],
          [[1n, 1n], [0n, 1n], [0n, 1n]],
          [[0n, 1n], [-1n, 1n], [0n, 1n]],
          [[3n, 1n], [-4n, 1n], [0n, 1n]],
          [[0n, 1n], [0n, 1n], [-1n, 1n]],
        ];
        for (let dx = -5n; dx <= 5n; dx += 1n) {
          for (let dy = -5n; dy <= 5n; dy += 1n) {
            if (dx === 0n && dy === 0n) continue;
            seedDirs.push([[dx, 1n], [dy, 1n], [0n, 1n]]);
          }
        }
        for (let dx = -3n; dx <= 3n; dx += 1n) {
          for (let dy = -3n; dy <= 3n; dy += 1n) {
            for (let dz = -3n; dz <= 3n; dz += 1n) {
              if (dz === 0n) continue;
              seedDirs.push([[dx, 1n], [dy, 1n], [dz, 1n]]);
            }
          }
        }
        const avoidPts = curScene.objects
          .filter((o) => !isSubEntity(o.id) && o.type === "point3" && o.id !== centerPt.id && Boolean(o.xyz))
          .map((o) => toVec3(o.xyz!));
        for (const pl of curScene.objects) {
          if (pl.type === "plane3" && pl.point) avoidPts.push(toVec3(pl.point));
        }
        const cNum = toVec3(centerPt.xyz);
        let bestRefDisp: ExactVec3 | null = null;
        let bestRefScore = -Infinity;
        for (const dVec of seedDirs) {
          const lenSq = metricDot(dVec, dVec, gMetric);
          if (lenSq[0] <= 0n) continue;
          const ratioSq = normFrac(rSqFrac[0] * lenSq[1], rSqFrac[1] * lenSq[0]);
          const kFrac = exactFracSqrt(ratioSq);
          if (!kFrac) continue;
          const candEx = vAdd(anchorEx, vScaleFrac(kFrac, dVec));
          if (!fEq(metricDot(vSub(candEx, anchorEx), vSub(candEx, anchorEx), gMetric), rSqFrac)) continue;
          const candDisp = mapExactVecToSceneFrame(candEx, chartT);
          const candNum = toVec3(candDisp);
          const vx = candNum[0] - cNum[0], vy = candNum[1] - cNum[1], vz = candNum[2] - cNum[2];
          const vLen = Math.hypot(vx, vy, vz);
          if (!(vLen > 1e-8)) continue;
          const ux = vx / vLen, uy = vy / vLen, uz = vz / vLen;
          // Prefer horizontal canonical great circle (uz == 0) toward upper-left (-3x + 8y) away from M's front-right (+3x - 8y)
          let score = (Math.abs(uz) < 1e-6 ? 1.5 : 0) + 0.35 * ((-3 * ux + 8 * uy) / Math.hypot(-3, 8));
          for (const ap of avoidPts) {
            const ax = ap[0] - cNum[0], ay = ap[1] - cNum[1], az = ap[2] - cNum[2];
            const aLen = Math.hypot(ax, ay, az);
            if (aLen > 1e-6) {
              const cosA = (ux * ax + uy * ay + uz * az) / aLen;
              if (cosA > 0.96) score -= 5;
              else score -= 0.25 * cosA;
            }
          }
          if (score > bestRefScore + 1e-7) {
            bestRefScore = score;
            bestRefDisp = candDisp;
          }
        }
        if (bestRefDisp) {
          const usedSyms = new Set(
            curScene.objects
              .filter((o) => !isSubEntity(o.id))
              .map((o) => o.notation?.trim() ?? o.reference?.trim() ?? "")
              .filter(Boolean),
          );
          const symX = (["X", "K", "E", "F", "U"] as const).find((c) => !usedSyms.has(c)) ?? "X′";
          const createdRefPt: SceneObject = {
            id: `${cs.id}__ref_pt`,
            type: "point3",
            label: `Điểm tham chiếu ${symX}`,
            notation: symX,
            reference: symX,
            role: `Điểm tham chiếu ${symX} thuộc mặt cầu dùng để mở bán kính từ tâm ${shortSym(centerPt)}`,
            origin: "derived",
            authoritative: false,
            semantic_role: "AUXILIARY_CONSTRUCTION",
            producer: null,
            render: "point_marker",
            display_group: ["construction", "sphere_foundation_ref"],
            formation_roles: ["CONSTRUCT_BASE"],
            depends: [centerPt.id],
            source: { instruction: "PRESENTATION_CURVED_FOUNDATION" },
            xyz: bestRefDisp,
          };
          insertedObjs.push(createdRefPt);
          rimPt = createdRefPt;
        }
      }
      if (centerPt?.xyz && rimPt?.xyz && !byId.has(`${cs.id}__radius`) && !hasExistingBallFoundationRadius()) {
        const sym = `${shortSym(centerPt)}${shortSym(rimPt)}`;
        const isRefRadius = rimPt.id === `${cs.id}__ref_pt`;
        insertedObjs.push({
          id: `${cs.id}__radius`,
          type: "segment3",
          label: `Bán kính ${sym}`,
          notation: sym,
          role: isRefRadius
            ? `Đoạn bán kính tham chiếu ${sym} xác định độ mở mặt cầu từ tâm ${shortSym(centerPt)}`
            : `Bán kính nối tâm ${shortSym(centerPt)} với điểm ${shortSym(rimPt)} thuộc mặt cầu`,
          origin: "derived",
          authoritative: false,
          ...(isRefRadius ? { semantic_role: "AUXILIARY_CONSTRUCTION" as const } : {}),
          producer: "construct_segment",
          render: "segment",
          display_group: isRefRadius ? ["construction", "sphere_foundation_ref"] : ["construction"],
          formation_roles: ["CONSTRUCT_BASE"],
          depends: [centerPt.id, rimPt.id],
          endpoint_ids: [centerPt.id, rimPt.id],
          source: { instruction: "PRESENTATION_CURVED_FOUNDATION" },
          point_a: centerPt.xyz,
          point_b: rimPt.xyz,
          endpoints: [centerPt.xyz, rimPt.xyz],
        });
      }
    } else if (
      cs.curved_kind === "cylinder"
      && exactCs.anchor
      && exactCs.apex_or_top
      && cs.anchor
      && cs.apex_or_top
      && cs.radius_sq
    ) {
      const ortho = inspectAxialCurvedOrthogonality(curScene, cs);
      const basePt = matchPointAtExact(exactCs.anchor);
      const topPt = matchPointAtExact(exactCs.apex_or_top);
      const rimPt = depPts.find((p) => p.id !== basePt?.id && p.id !== topPt?.id);
      const dispAx = [
        String(toNumber(cs.apex_or_top[0]) - toNumber(cs.anchor[0])),
        String(toNumber(cs.apex_or_top[1]) - toNumber(cs.anchor[1])),
        String(toNumber(cs.apex_or_top[2]) - toNumber(cs.anchor[2])),
      ] as ExactVec3;
      const capNormal: ExactVec3 =
        !isSceneWorldTransformed(curScene) && ortho.baseNormal
          ? [fmtFrac(ortho.baseNormal[0]), fmtFrac(ortho.baseNormal[1]), fmtFrac(ortho.baseNormal[2])]
          : dispAx;
      const baseCircleSource = ortho.isIllustrativeBasePlane
        ? {
            instruction: "PRESENTATION_CURVED_FOUNDATION",
            is_given: false,
            assumption: "ILLUSTRATIVE_CONFIGURATION",
            provenance: "ILLUSTRATIVE_CONFIGURATION",
          }
        : { instruction: "PRESENTATION_CURVED_FOUNDATION" };

      if (rimPt?.xyz && (basePt || topPt) && !byId.has(`${cs.id}__radius`) && !hasSegKind("radius")) {
        const exactRim = (exactById.get(rimPt.id) ?? rimPt).xyz!;
        const capN = ortho.baseNormal ?? vSub(parseFracVec3(exactCs.apex_or_top), parseFracVec3(exactCs.anchor));
        const onTop =
          Boolean(topPt)
          && fIsZero(plainDotFrac(vSub(parseFracVec3(exactRim), parseFracVec3(exactCs.apex_or_top)), capN));
        const centerForRim = (onTop ? topPt : basePt) ?? basePt ?? topPt!;
        const sym = `${shortSym(centerForRim)}${shortSym(rimPt)}`;
        const radiusPtA = centerForRim.xyz ?? cs.anchor;
        insertedObjs.push({
          id: `${cs.id}__radius`,
          type: "segment3",
          label: `Bán kính đáy ${sym}`,
          notation: sym,
          role: `Bán kính đáy nối tâm ${shortSym(centerForRim)} với ${shortSym(rimPt)}`,
          origin: "derived",
          authoritative: false,
          producer: "construct_segment",
          render: "segment",
          display_group: ["construction"],
          formation_roles: ["CONSTRUCT_BASE"],
          depends: [centerForRim.id, rimPt.id],
          endpoint_ids: [centerForRim.id, rimPt.id],
          source: { instruction: "PRESENTATION_CURVED_FOUNDATION" },
          point_a: radiusPtA,
          point_b: rimPt.xyz,
          endpoints: [radiusPtA, rimPt.xyz],
        });
      }

      const botDeps = basePt ? [basePt.id] : depPts.length > 0 ? [depPts[0].id] : [];
      if (botDeps.length > 0 && !byId.has(`${cs.id}__base_bot`) && !hasBaseCircleAt(exactCs.anchor)) {
        insertedObjs.push({
          id: `${cs.id}__base_bot`,
          type: "circle3",
          label: basePt ? `Đường tròn đáy (${shortSym(basePt)})` : "Đường tròn đáy dưới",
          origin: "derived",
          authoritative: false,
          producer: "construct_circle",
          render: "circle",
          surface_role: "BASE_REGION",
          display_group: ["construction"],
          formation_roles: ["CONSTRUCT_BASE"],
          depends: botDeps,
          source: baseCircleSource,
          center: cs.anchor,
          normal: capNormal,
          radius_sq: cs.radius_sq,
        });
      }

      if (basePt && topPt && !byId.has(`${cs.id}__axis`) && !hasSegKind("axis") && !hasSegKind("center_line")) {
        const sym = `${shortSym(basePt)}${shortSym(topPt)}`;
        insertedObjs.push({
          id: `${cs.id}__axis`,
          type: "segment3",
          label: ortho.isOblique ? `Đường nối tâm ${sym}` : `Trục ${sym}`,
          notation: sym,
          role: ortho.isOblique
            ? `Đoạn thẳng nối hai tâm đáy ${shortSym(basePt)} và ${shortSym(topPt)} của hình trụ xiên`
            : `Trục nối hai tâm đáy ${shortSym(basePt)} và ${shortSym(topPt)} của hình trụ`,
          ...(ortho.isRightCertified && !ortho.isOblique
            ? (() => {
                const botCapId =
                  curScene.objects.find((o) => {
                    if (o.type !== "circle3" || o.surface_role !== "BASE_REGION") return false;
                    const eo = exactById.get(o.id) ?? o;
                    return Boolean(eo.center && vIsZero(vSub(parseFracVec3(eo.center), parseFracVec3(exactCs.anchor!))));
                  })?.id ?? `${cs.id}__base_bot`;
                const w = buildCurvedAxisPerpWitness(
                  basePt,
                  topPt,
                  cs.anchor!,
                  cs.apex_or_top!,
                  parseFracVec3(exactCs.anchor!),
                  parseFracVec3(exactCs.apex_or_top!),
                  rimPt,
                  botCapId,
                );
                return w ? { perpendicular_witness: w } : {};
              })()
            : {}),
          origin: "derived",
          authoritative: false,
          producer: "construct_segment",
          render: "segment",
          display_group: ["construction"],
          formation_roles: ortho.isOblique ? ["CONSTRUCT_BASE"] : ["CONSTRUCT_HEIGHT"],
          depends: [basePt.id, topPt.id],
          endpoint_ids: [basePt.id, topPt.id],
          source: { instruction: "PRESENTATION_CURVED_FOUNDATION" },
          point_a: cs.anchor,
          point_b: cs.apex_or_top,
          endpoints: [cs.anchor, cs.apex_or_top],
        });
      }

      const topDeps = topPt ? [topPt.id] : depPts.length > 0 ? [depPts[0].id] : [];
      if (topDeps.length > 0 && !byId.has(`${cs.id}__base_top`) && !hasBaseCircleAt(exactCs.apex_or_top)) {
        insertedObjs.push({
          id: `${cs.id}__base_top`,
          type: "circle3",
          label: topPt ? `Đường tròn đáy (${shortSym(topPt)})` : "Đường tròn đáy trên",
          origin: "derived",
          authoritative: false,
          producer: "construct_circle",
          render: "circle",
          surface_role: "BASE_REGION",
          display_group: ["construction"],
          formation_roles: ["CONSTRUCT_BASE"],
          depends: topDeps,
          source: baseCircleSource,
          center: cs.apex_or_top,
          normal: capNormal,
          radius_sq: cs.radius_sq,
        });
      }
    } else if (
      cs.curved_kind === "cone"
      && exactCs.anchor
      && exactCs.apex_or_top
      && cs.anchor
      && cs.apex_or_top
      && cs.radius_sq
    ) {
      const ortho = inspectAxialCurvedOrthogonality(curScene, cs);
      const centerPt = matchPointAtExact(exactCs.anchor);
      const apexPt = matchPointAtExact(exactCs.apex_or_top);
      const rimPt = depPts.find((p) => p.id !== centerPt?.id && p.id !== apexPt?.id);
      const dispAx = [
        String(toNumber(cs.apex_or_top[0]) - toNumber(cs.anchor[0])),
        String(toNumber(cs.apex_or_top[1]) - toNumber(cs.anchor[1])),
        String(toNumber(cs.apex_or_top[2]) - toNumber(cs.anchor[2])),
      ] as ExactVec3;
      const capNormal: ExactVec3 =
        !isSceneWorldTransformed(curScene) && ortho.baseNormal
          ? [fmtFrac(ortho.baseNormal[0]), fmtFrac(ortho.baseNormal[1]), fmtFrac(ortho.baseNormal[2])]
          : dispAx;

      if (rimPt?.xyz && centerPt && !byId.has(`${cs.id}__radius`) && !hasSegKind("radius")) {
        const sym = `${shortSym(centerPt)}${shortSym(rimPt)}`;
        insertedObjs.push({
          id: `${cs.id}__radius`,
          type: "segment3",
          label: `Bán kính đáy ${sym}`,
          notation: sym,
          role: `Bán kính đáy nối tâm ${shortSym(centerPt)} với ${shortSym(rimPt)}`,
          origin: "derived",
          authoritative: false,
          producer: "construct_segment",
          render: "segment",
          display_group: ["construction"],
          formation_roles: ["CONSTRUCT_BASE"],
          depends: [centerPt.id, rimPt.id],
          endpoint_ids: [centerPt.id, rimPt.id],
          source: { instruction: "PRESENTATION_CURVED_FOUNDATION" },
          point_a: cs.anchor,
          point_b: rimPt.xyz,
          endpoints: [cs.anchor, rimPt.xyz],
        });
      }

      const coneBaseDeps = centerPt ? [centerPt.id] : depPts.length > 0 ? [depPts[0].id] : [];
      if (coneBaseDeps.length > 0 && !byId.has(`${cs.id}__base_bot`) && !hasBaseCircleAt(exactCs.anchor)) {
        insertedObjs.push({
          id: `${cs.id}__base_bot`,
          type: "circle3",
          label: centerPt ? `Đường tròn đáy (${shortSym(centerPt)})` : "Đường tròn đáy",
          origin: "derived",
          authoritative: false,
          producer: "construct_circle",
          render: "circle",
          surface_role: "BASE_REGION",
          display_group: ["construction"],
          formation_roles: ["CONSTRUCT_BASE"],
          depends: coneBaseDeps,
          source: { instruction: "PRESENTATION_CURVED_FOUNDATION" },
          center: cs.anchor,
          normal: capNormal,
          radius_sq: cs.radius_sq,
        });
      }

      if (apexPt && centerPt && !byId.has(`${cs.id}__axis`) && !hasSegKind("axis") && !hasSegKind("center_line")) {
        const sym = `${shortSym(apexPt)}${shortSym(centerPt)}`;
        insertedObjs.push({
          id: `${cs.id}__axis`,
          type: "segment3",
          label: `Đường cao ${sym}`,
          notation: sym,
          role: `Đường cao (trục) nối đỉnh ${shortSym(apexPt)} với tâm đáy ${shortSym(centerPt)} của hình nón`,
          ...(ortho.isRightCertified && !ortho.isOblique
            ? (() => {
                const botCapId =
                  curScene.objects.find((o) => {
                    if (o.type !== "circle3" || o.surface_role !== "BASE_REGION") return false;
                    const eo = exactById.get(o.id) ?? o;
                    return Boolean(eo.center && vIsZero(vSub(parseFracVec3(eo.center), parseFracVec3(exactCs.anchor!))));
                  })?.id ?? `${cs.id}__base_bot`;
                const w = buildCurvedAxisPerpWitness(
                  centerPt,
                  apexPt,
                  cs.anchor!,
                  cs.apex_or_top!,
                  parseFracVec3(exactCs.anchor!),
                  parseFracVec3(exactCs.apex_or_top!),
                  rimPt,
                  botCapId,
                );
                return w ? { perpendicular_witness: w } : {};
              })()
            : {}),
          origin: "derived",
          authoritative: false,
          producer: "construct_segment",
          render: "segment",
          display_group: ["construction"],
          formation_roles: ortho.isOblique ? ["CONSTRUCT_BASE"] : ["CONSTRUCT_HEIGHT"],
          depends: [apexPt.id, centerPt.id],
          endpoint_ids: [apexPt.id, centerPt.id],
          source: { instruction: "PRESENTATION_CURVED_FOUNDATION" },
          point_a: cs.apex_or_top,
          point_b: cs.anchor,
          endpoints: [cs.apex_or_top, cs.anchor],
        });
      }
    }

    if (insertedObjs.length === 0) continue;
    didExpand = true;

    const csObjIdx = curScene.objects.findIndex((o) => o.id === cs.id);
    const nextObjects = [...curScene.objects];
    nextObjects.splice(csObjIdx >= 0 ? csObjIdx : nextObjects.length, 0, ...insertedObjs);

    const foundationEvents: SceneEvent[] = insertedObjs.map((fo) => ({
      step_index: 0,
      action: "CREATE",
      object: fo.id,
      objects: [fo.id],
      depends: [...(fo.depends ?? [])],
      explanation: `Dựng ${fo.label}.`,
      semantic_kind: "GEOMETRY_CONSTRUCTION",
    }));

    const nextEvents: SceneEvent[] = [];
    for (let k = 0; k < curScene.events.length; k += 1) {
      if (k === evIdx) {
        for (const fev of foundationEvents) {
          nextEvents.push({ ...fev, step_index: nextEvents.length });
        }
      }
      nextEvents.push({ ...curScene.events[k], step_index: nextEvents.length });
    }

    let nextFormation = curScene.formation;
    if (curScene.formation && curScene.formation.steps.length === curScene.events.length) {
      const prevStep = evIdx > 0 ? curScene.formation.steps[evIdx - 1] : undefined;
      const baseVis = prevStep ? [...prevStep.visible_ids] : [...curScene.free_objects];
      const baseRead = prevStep ? [...prevStep.readout_ids] : [];
      const baseProg = prevStep?.geometry_progress ? [...prevStep.geometry_progress] : [];
      const allInsertedIds = insertedObjs.map((fo) => fo.id);

      const newFSteps: FormationStep[] = [];
      for (let k = 0; k < curScene.formation.steps.length; k += 1) {
        if (k === evIdx) {
          const accNew: string[] = [];
          for (const fo of insertedObjs) {
            accNew.push(fo.id);
            newFSteps.push({
              step_index: newFSteps.length,
              visible_ids: [...new Set([...baseVis, ...accNew])],
              focus_ids: [fo.id, ...(fo.depends ?? [])],
              readout_ids: [...baseRead],
              ...(baseProg.length > 0 ? { geometry_progress: [...baseProg] } : { geometry_progress: [] }),
              learner_text: `Dựng ${fo.label}.`,
              semantic_kind: "GEOMETRY_CONSTRUCTION",
            });
          }
        }
        const origSt = curScene.formation.steps[k];
        if (k >= evIdx) {
          const visWithFound = [...origSt.visible_ids];
          const csVisPos = visWithFound.indexOf(cs.id);
          const missingIds = allInsertedIds.filter((id) => !visWithFound.includes(id));
          if (missingIds.length > 0) {
            visWithFound.splice(csVisPos >= 0 ? csVisPos : visWithFound.length, 0, ...missingIds);
          }
          newFSteps.push({
            ...origSt,
            step_index: newFSteps.length,
            visible_ids: visWithFound,
          });
        } else {
          newFSteps.push({ ...origSt, step_index: newFSteps.length });
        }
      }
      nextFormation = { steps: newFSteps };
    } else if (curScene.formation) {
      nextFormation = undefined;
    }

    const { formation: _droppedFormation, ...restCurScene } = curScene;
    curScene = {
      ...restCurScene,
      objects: nextObjects,
      events: nextEvents,
      ...(nextFormation ? { formation: nextFormation } : {}),
    };
  }

  return { scene: curScene, didExpand };
}

/**
 * Triển khai nền tảng mặt đáy và cạnh bên cho khối đa diện nguyên khối (`solid`) khi hợp đồng backend
 * chỉ phát ra một `solid` duy nhất (hoặc thiếu `polygon3` đáy / `segment3` cạnh bên tường minh):
 * - Rút trích hoàn toàn từ topology đã xác nhận (`vertex_ids`, `vertices`, `faces`, `shape_class`).
 * - Tuyệt đối không bịa điểm mới hoặc tọa độ mới; nếu đã có mặt đáy và đủ cạnh bên thì trả nguyên cảnh gốc.
 */
function expandPrimaryPolyhedralFoundation(baseScene: Scene3D): { scene: Scene3D; didExpand: boolean } {
  const exactRef = exactSceneOriginOf(baseScene);
  const exactById = new Map(exactRef.objects.map((o) => [o.id, o]));
  let curScene = baseScene;
  let didExpand = false;

  const solidCandidates = baseScene.objects.filter(
    (o) =>
      o.type === "solid"
      && (o.vertex_ids?.length ?? 0) >= 4
      && o.vertex_ids?.length === (o.vertices?.length ?? 0)
      && (o.faces?.length ?? 0) >= 4,
  );

  for (const rawSol of solidCandidates) {
    const byId = new Map(curScene.objects.map((o) => [o.id, o]));
    const sol = byId.get(rawSol.id);
    if (!sol?.vertex_ids || !sol.vertices || !sol.faces) continue;
    const evIdx = curScene.events.findIndex(
      (ev) => ev.action === "CREATE" && (ev.object === sol.id || (ev.objects ?? []).includes(sol.id)),
    );
    if (evIdx < 0) continue;

    const vIds = sol.vertex_ids;
    const vCoords = sol.vertices;
    const baseFace = sol.faces[0] ?? [];
    if (baseFace.length < 3 || baseFace.some((k) => k < 0 || k >= vIds.length)) continue;
    const baseVertIds = baseFace.map((k) => vIds[k]);
    const baseVertSet = new Set(baseVertIds);

    const sameVertSet = (a: string[], bSet: Set<string>): boolean =>
      a.length === bSet.size && a.every((id) => bSet.has(id));

    const existingBasePoly = curScene.objects.find(
      (o) =>
        !isSubEntity(o.id)
        && o.type === "polygon3"
        && sameVertSet(o.vertex_ids ?? o.depends ?? [], baseVertSet),
    );
    const basePolyId = existingBasePoly?.id ?? `${sol.id}__base`;

    const isPrism =
      (sol.shape_class === "PRISM_LIKE"
        || sol.shape_class === "BOX_LIKE"
        || sol.shape_class === "FRUSTUM_LIKE"
        || isTwoBasePolyhedronSolid(curScene, sol))
      && sol.faces.length >= 5
      && (sol.faces[1]?.length ?? 0) === baseFace.length
      && sol.faces[1].every((k) => k >= 0 && k < vIds.length && !baseVertSet.has(vIds[k]));

    const topFace = isPrism ? sol.faces[1] : [];
    const topVertIds = topFace.map((k) => vIds[k]);
    const topVertSet = new Set(topVertIds);
    const existingTopPoly = isPrism
      ? curScene.objects.find(
          (o) =>
            !isSubEntity(o.id)
            && o.type === "polygon3"
            && sameVertSet(o.vertex_ids ?? o.depends ?? [], topVertSet),
        )
      : undefined;

    const remainingIds = vIds.filter((id) => !baseVertSet.has(id));
    const isPyramid = !isPrism && (sol.shape_class === "PYRAMID_LIKE" || remainingIds.length === 1) && remainingIds.length === 1;
    if (!isPrism && !isPyramid) continue;

    const lateralPairs: [string, string][] = [];
    if (isPyramid) {
      const apexId = remainingIds[0];
      for (const bId of baseVertIds) {
        lateralPairs.push([bId, apexId]);
      }
    } else {
      const seenPairs = new Set<string>();
      for (const f of sol.faces.slice(2)) {
        for (let j = 0; j < f.length; j += 1) {
          const aId = vIds[f[j]];
          const bId = vIds[f[(j + 1) % f.length]];
          if (baseVertSet.has(aId) && topVertSet.has(bId)) {
            const key = `${aId}|${bId}`;
            if (!seenPairs.has(key)) {
              seenPairs.add(key);
              lateralPairs.push([aId, bId]);
            }
          } else if (topVertSet.has(aId) && baseVertSet.has(bId)) {
            const key = `${bId}|${aId}`;
            if (!seenPairs.has(key)) {
              seenPairs.add(key);
              lateralPairs.push([bId, aId]);
            }
          }
        }
      }
    }

    const findExistingSeg = (uId: string, vId: string): SceneObject | undefined => {
      const eu = exactById.get(uId) ?? byId.get(uId);
      const evObj = exactById.get(vId) ?? byId.get(vId);
      const pu = eu?.xyz ? parseFracVec3(eu.xyz) : null;
      const pv = evObj?.xyz ? parseFracVec3(evObj.xyz) : null;
      return curScene.objects.find((o) => {
        if (isSubEntity(o.id) || o.type !== "segment3") return false;
        const deps = o.endpoint_ids ?? o.depends ?? [];
        if (deps.includes(uId) && deps.includes(vId)) return true;
        const eo = exactById.get(o.id) ?? o;
        if (pu && pv && eo.point_a && eo.point_b) {
          const pa = parseFracVec3(eo.point_a);
          const pb = parseFracVec3(eo.point_b);
          return (
            (vIsZero(vSub(pa, pu)) && vIsZero(vSub(pb, pv)))
            || (vIsZero(vSub(pa, pv)) && vIsZero(vSub(pb, pu)))
          );
        }
        return false;
      });
    };

    const baseInsertedObjs: SceneObject[] = [];
    const solDescForFoundation = lowerLeadingVietnameseNoun(sol.label || (isPrism ? "hình lăng trụ" : "khối đa diện"));
    if (!existingBasePoly) {
      const rawBaseSyms = baseVertIds.map((id) => shortSym(byId.get(id)) || id);
      const compactBase = rawBaseSyms.length >= 3 && rawBaseSyms.every(isCompactPointSym);
      const baseSyms = compactBase ? rawBaseSyms.join("") : "";
      baseInsertedObjs.push({
        id: basePolyId,
        type: "polygon3",
        label: compactBase ? `Đáy ${baseSyms}` : `Mặt đáy của ${solDescForFoundation}`,
        ...(compactBase ? { notation: baseSyms } : {}),
        origin: "derived",
        authoritative: false,
        producer: "construct_polygon",
        render: "polygon",
        display_group: ["construction"],
        formation_roles: ["CONSTRUCT_BASE"],
        surface_role: "BASE_REGION",
        depends: [...baseVertIds],
        vertex_ids: [...baseVertIds],
        source: { instruction: "PRESENTATION_POLYHEDRAL_FOUNDATION" },
        polygon: baseFace.map((k) => vCoords[k]),
      });
    }

    if (isPrism && !existingTopPoly) {
      const rawTopSyms = topVertIds.map((id) => shortSym(byId.get(id)) || id);
      const compactTop = rawTopSyms.length >= 3 && rawTopSyms.every(isCompactPointSym);
      const topSyms = compactTop ? rawTopSyms.join("") : "";
      baseInsertedObjs.push({
        id: `${sol.id}__top_base`,
        type: "polygon3",
        label: compactTop ? `Đáy trên ${topSyms}` : `Mặt đáy đối diện của ${solDescForFoundation}`,
        ...(compactTop ? { notation: topSyms } : {}),
        origin: "derived",
        authoritative: false,
        producer: "construct_polygon",
        render: "polygon",
        display_group: ["construction"],
        formation_roles: ["CONSTRUCT_TRANSLATED_FACE"],
        surface_role: "BASE_REGION",
        depends: [...topVertIds],
        vertex_ids: [...topVertIds],
        source: { instruction: "PRESENTATION_POLYHEDRAL_FOUNDATION" },
        polygon: topFace.map((k) => vCoords[k]),
      });
    }

    const latInsertedObjs: SceneObject[] = [];
    const existingLatSegIds = new Set<string>();
    for (const [uId, vId] of lateralPairs) {
      const exSeg = findExistingSeg(uId, vId);
      if (exSeg) {
        existingLatSegIds.add(exSeg.id);
        continue;
      }
      const uPt = byId.get(uId);
      const vPt = byId.get(vId);
      if (!uPt?.xyz || !vPt?.xyz) continue;
      const uSym = shortSym(uPt) || uId;
      const vSym = shortSym(vPt) || vId;
      const compactLat = isCompactPointSym(uSym) && isCompactPointSym(vSym);
      const edgeSym = compactLat ? (isPyramid ? `${vSym}${uSym}` : `${uSym}${vSym}`) : "";
      latInsertedObjs.push({
        id: `${sol.id}__lat_${uId}_${vId}`,
        type: "segment3",
        label: compactLat ? `Cạnh bên ${edgeSym}` : `Cạnh bên của ${solDescForFoundation}`,
        ...(compactLat ? { notation: edgeSym } : {}),
        origin: "derived",
        authoritative: false,
        producer: "construct_segment",
        render: "segment",
        display_group: ["construction"],
        formation_roles: ["CONSTRUCT_LATERAL_BOUNDARY"],
        depends: [uId, vId],
        endpoint_ids: [uId, vId],
        source: { instruction: "PRESENTATION_POLYHEDRAL_FOUNDATION" },
        point_a: uPt.xyz,
        point_b: vPt.xyz,
        endpoints: [uPt.xyz, vPt.xyz],
      });
    }

    const preSolidCreatedIds = new Set<string>();
    for (let k = 0; k < evIdx; k += 1) {
      const ev = curScene.events[k];
      for (const id of ev.objects ?? (ev.object ? [ev.object] : [])) {
        preSolidCreatedIds.add(id);
      }
    }
    const preSolidExistingLatIds = new Set(
      [...existingLatSegIds].filter((id) => {
        if (!preSolidCreatedIds.has(id)) return false;
        const o = byId.get(id);
        const r = o?.formation_roles ?? [];
        return !r.includes("CONSTRUCT_LATERAL_BOUNDARY") && !r.includes("CONSTRUCT_HEIGHT");
      }),
    );
    const reboundWitnessOnSolid = curScene.objects.some(
      (o) => o.perpendicular_witness?.on === sol.id && isLinePerpPlaneRelation(o.perpendicular_witness.relation),
    );
    if (baseInsertedObjs.length === 0 && latInsertedObjs.length === 0 && !reboundWitnessOnSolid && preSolidExistingLatIds.size === 0) continue;
    didExpand = true;

    const updatedExistingObjects = curScene.objects.map((o) => {
      let nextObj = o;
      if (preSolidExistingLatIds.has(o.id)) {
        const cleanRoles = (o.formation_roles ?? []).filter((r) => r !== "CONSTRUCT_AUXILIARY_GEOMETRY");
        const creatorEv = curScene.events.find(
          (ev) => ev.action !== "INIT" && (ev.object === o.id || (ev.objects ?? []).includes(o.id)),
        );
        const hasExplicitHeightClaim =
          Boolean(o.perpendicular_witness && isLinePerpPlaneRelation(o.perpendicular_witness.relation))
          || /đường\s+cao|chiều\s+cao/iu.test(
            [o.label, o.role, creatorEv?.learner_text, creatorEv?.display_label, creatorEv?.explanation]
              .filter(Boolean)
              .join(" "),
          );
        nextObj = {
          ...o,
          formation_roles: [hasExplicitHeightClaim ? "CONSTRUCT_HEIGHT" : "CONSTRUCT_LATERAL_BOUNDARY", ...cleanRoles],
        };
      }
      if (nextObj.perpendicular_witness?.on === sol.id && isLinePerpPlaneRelation(nextObj.perpendicular_witness.relation)) {
        const roles = nextObj.formation_roles ?? [];
        nextObj = {
          ...nextObj,
          formation_roles: roles.includes("CONSTRUCT_HEIGHT") ? roles : ["CONSTRUCT_HEIGHT", ...roles],
          perpendicular_witness: {
            ...nextObj.perpendicular_witness,
            on: basePolyId,
          },
        };
      }
      return nextObj;
    });

    const solObjIdx = updatedExistingObjects.findIndex((o) => o.id === sol.id);
    const nextObjects = [...updatedExistingObjects];
    const allNewObjs = [...baseInsertedObjs, ...latInsertedObjs];
    nextObjects.splice(solObjIdx >= 0 ? solObjIdx : nextObjects.length, 0, ...allNewObjs);

    let earliestRelatedEvIdx = evIdx;
    for (let k = 0; k < evIdx; k += 1) {
      const ev = curScene.events[k];
      const evIds = ev.objects ?? (ev.object ? [ev.object] : []);
      if (
        evIds.some((id) => {
          if (existingLatSegIds.has(id)) return true;
          const obj = byId.get(id);
          if (obj?.perpendicular_witness?.on === sol.id) return true;
          // Mọi điểm/đoạn dựng trực tiếp trên tập đỉnh mặt đáy (như trọng tâm G của ABC, giao điểm hai đường chéo O của ABCD)
          // đòi hỏi mặt đáy nền phải xuất hiện trước trong tiến trình dựng (§5)
          if (
            obj
            && !baseVertSet.has(id)
            && obj.type !== "quantity"
            && (obj.depends ?? []).length >= 2
            && (obj.depends ?? []).every((d) => baseVertSet.has(d))
          ) {
            return true;
          }
          return false;
        })
      ) {
        earliestRelatedEvIdx = Math.min(earliestRelatedEvIdx, k);
      }
    }

    const nextEvents: SceneEvent[] = [];
    for (let k = 0; k < curScene.events.length; k += 1) {
      if (k === earliestRelatedEvIdx && baseInsertedObjs.length > 0) {
        for (const bo of baseInsertedObjs) {
          nextEvents.push({
            step_index: nextEvents.length,
            action: "CREATE",
            object: bo.id,
            objects: [bo.id],
            depends: [...(bo.depends ?? [])],
            explanation: `Dựng ${bo.label}.`,
            semantic_kind: "GEOMETRY_CONSTRUCTION",
          });
        }
      }
      if (k === evIdx && latInsertedObjs.length > 0) {
        const latIds = latInsertedObjs.map((lo) => lo.id);
        nextEvents.push({
          step_index: nextEvents.length,
          action: "CREATE",
          object: `${sol.id}__lat_bundle`,
          objects: latIds,
          depends: latIds,
          explanation: "Dựng các cạnh bên.",
          semantic_kind: "GEOMETRY_CONSTRUCTION",
        });
      }
      nextEvents.push({ ...curScene.events[k], step_index: nextEvents.length });
    }

    let nextFormation = curScene.formation;
    if (curScene.formation && curScene.formation.steps.length === curScene.events.length) {
      const baseInsertedIds = baseInsertedObjs.map((bo) => bo.id);
      const latIds = latInsertedObjs.map((lo) => lo.id);
      const newFSteps: FormationStep[] = [];
      for (let k = 0; k < curScene.formation.steps.length; k += 1) {
        if (k === earliestRelatedEvIdx && baseInsertedObjs.length > 0) {
          const prevSt = k > 0 ? curScene.formation.steps[k - 1] : undefined;
          const baseVis = prevSt ? [...prevSt.visible_ids] : [...curScene.free_objects];
          const baseRead = prevSt ? [...prevSt.readout_ids] : [];
          const baseProg = prevSt?.geometry_progress ? [...prevSt.geometry_progress] : [];
          const accBase: string[] = [];
          for (const bo of baseInsertedObjs) {
            accBase.push(bo.id);
            newFSteps.push({
              step_index: newFSteps.length,
              visible_ids: [...new Set([...baseVis, ...accBase])],
              focus_ids: [bo.id, ...(bo.depends ?? [])],
              readout_ids: [...baseRead],
              ...(baseProg.length > 0 ? { geometry_progress: [...baseProg] } : { geometry_progress: [] }),
              learner_text: `Dựng ${bo.label}.`,
              semantic_kind: "GEOMETRY_CONSTRUCTION",
            });
          }
        }
        if (k === evIdx && latIds.length > 0) {
          const prevSt = newFSteps.length > 0 ? newFSteps[newFSteps.length - 1] : undefined;
          const baseVis = prevSt ? [...prevSt.visible_ids] : [...curScene.free_objects];
          const baseRead = prevSt ? [...prevSt.readout_ids] : [];
          const baseProg = prevSt?.geometry_progress ? [...prevSt.geometry_progress] : [];
          newFSteps.push({
            step_index: newFSteps.length,
            visible_ids: [...new Set([...baseVis, ...latIds])],
            focus_ids: [...latIds],
            readout_ids: [...baseRead],
            ...(baseProg.length > 0 ? { geometry_progress: [...baseProg] } : { geometry_progress: [] }),
            learner_text: "Dựng các cạnh bên.",
            semantic_kind: "GEOMETRY_CONSTRUCTION",
          });
        }
        const origSt = curScene.formation.steps[k];
        const visNext = [...origSt.visible_ids];
        const extraBeforeSol = [
          ...(k >= earliestRelatedEvIdx ? baseInsertedIds : []),
          ...(k >= evIdx ? latIds : []),
        ].filter((id) => !visNext.includes(id));
        if (extraBeforeSol.length > 0) {
          const solPos = visNext.indexOf(sol.id);
          visNext.splice(solPos >= 0 ? solPos : visNext.length, 0, ...extraBeforeSol);
        }
        newFSteps.push({
          ...origSt,
          step_index: newFSteps.length,
          visible_ids: visNext,
        });
      }
      nextFormation = { steps: newFSteps };
    } else if (curScene.formation) {
      nextFormation = undefined;
    }

    const { formation: _droppedFormation, ...restCurScene } = curScene;
    curScene = {
      ...restCurScene,
      objects: nextObjects,
      events: nextEvents,
      ...(nextFormation ? { formation: nextFormation } : {}),
    };
  }

  return { scene: curScene, didExpand };
}

function exactFracSqrt(sq: Frac): Frac | null {
  if (sq[0] < 0n || sq[1] <= 0n) return null;
  if (sq[0] === 0n) return [0n, 1n];
  const rn = exactIntSqrt(sq[0]);
  const rd = exactIntSqrt(sq[1]);
  return rn !== null && rd !== null ? normFrac(rn, rd) : null;
}

function fmtExactVec3(v: FracVec3): ExactVec3 {
  return [fmtFrac(v[0]), fmtFrac(v[1]), fmtFrac(v[2])];
}

function mapExactVecToSceneFrame(
  vExact: FracVec3,
  chartT: [[number, number, number], [number, number, number], [number, number, number]] | null,
): ExactVec3 {
  const raw = fmtExactVec3(vExact);
  if (!chartT) return raw;
  const x = toNumber(raw[0]);
  const y = toNumber(raw[1]);
  const z = toNumber(raw[2]);
  const out = [0, 1, 2].map((i) => {
    const val = chartT[i][0] * x + chartT[i][1] * y + chartT[i][2] * z;
    const scaled = Math.round(val * 1e9);
    return `${scaled}/1000000000`;
  });
  return out as ExactVec3;
}

/**
 * Bổ sung các đối tượng phụ giải thích (`AUXILIARY` / `DERIVED`, `authoritative: false`) KHI VÀ CHỈ KHI
 * được chứng minh chính xác trên `Q^3`:
 * 1. Tương giao mặt cầu và mặt phẳng (cát tuyến `0 < d < R`, đường tròn lớn `d = 0`, tiếp diện `d = R`).
 * 2. Giao tuyến hai mặt phẳng (`(SAC) ∩ (SBD)`): khi hai mặt phẳng mới có `< 2` điểm chung đặt tên nhưng cùng cắt một đa giác mặt/đáy
 *    theo hai dây cung cắt nhau tại đúng điểm hữu tỉ `O ∈ Q³`, bổ sung điểm chung `O` (`AUXILIARY/DERIVED`, `authoritative: false`) để làm rõ cơ sở xác định giao tuyến.
 */
function expandVerifiedExplanatoryRelations(rawScene: Scene3D): { scene: Scene3D; didExpand: boolean } {
  const exactRef = exactSceneOriginOf(rawScene);
  const chartT = rawScene !== exactRef ? maTranKhung(exactRef) : null;
  let curScene = rawScene;
  let didExpand = false;

  const pickUnusedSym = (scene: Scene3D, candidates: readonly string[]): string => {
    const used = new Set(
      scene.objects
        .filter((o) => !isSubEntity(o.id))
        .map((o) => o.notation?.trim() ?? o.reference?.trim() ?? "")
        .filter(Boolean),
    );
    for (const c of candidates) {
      if (!used.has(c)) return c;
    }
    return `${candidates[0]}′`;
  };

  // ── 0a. Đường cao tại tâm đáy của hình chóp đều (chứng minh đại số chính xác trên Q³) ──────────
  const pyramidSolids = curScene.objects.filter(
    (o) => !isSubEntity(o.id) && o.type === "solid" && o.shape_class !== "PRISM_LIKE",
  );
  for (const sol of pyramidSolids) {
    const altId = `${sol.id}__altitude`;
    if (curScene.objects.some((o) => o.id === altId)) continue;
    const exactById = new Map(exactRef.objects.map((o) => [o.id, o]));
    const curById = new Map(curScene.objects.map((o) => [o.id, o]));
    if (
      curScene.objects.some(
        (o) =>
          !isSubEntity(o.id)
          && ((o.formation_roles ?? []).includes("CONSTRUCT_HEIGHT")
            || isLinePerpPlaneRelation(o.perpendicular_witness?.relation)),
      )
    ) {
      continue;
    }
    const basePoly = curScene.objects.find(
      (o) =>
        !isSubEntity(o.id)
        && o.type === "polygon3"
        && (o.surface_role === "BASE_REGION" || (o.formation_roles ?? []).includes("CONSTRUCT_BASE"))
        && !(o.formation_roles ?? []).includes("CONSTRUCT_TRANSLATED_FACE"),
    );
    if (!basePoly) continue;
    const exactBase = exactById.get(basePoly.id) ?? basePoly;
    const baseVidList = exactBase.vertex_ids ?? exactBase.depends ?? basePoly.vertex_ids ?? basePoly.depends ?? [];
    const basePtExacts = baseVidList
      .map((id) => exactById.get(id))
      .filter((p): p is SceneObject => Boolean(p && p.type === "point3" && p.xyz));
    const m = basePtExacts.length;
    if (m < 3) continue;
    const baseVidSet = new Set(basePtExacts.map((p) => p.id));

    const solVidList = (exactById.get(sol.id) ?? sol).vertex_ids ?? sol.vertex_ids ?? sol.depends ?? [];
    const apexIds = [...new Set(solVidList.filter((id) => !baseVidSet.has(id) && exactById.get(id)?.type === "point3"))];
    if (apexIds.length !== 1) continue;
    const exactApex = exactById.get(apexIds[0]);
    const curApex = curById.get(apexIds[0]);
    if (!exactApex?.xyz || !curApex?.xyz) continue;

    const gMetric = isSceneWorldTransformed(exactRef) ? undefined : exactRef.chart_metric;
    const baseProv = classifyPolygonShapeWithProvenance(exactRef, exactBase);
    const baseShape = baseProv.certifiedShape;
    const isRegularBase =
      baseShape === "tam giác đều"
      || baseShape === "hình vuông"
      || baseShape === "ngũ giác đều"
      || baseShape === "lục giác đều"
      || Boolean(baseShape && /^đa giác đều /u.test(baseShape));
    if (!isRegularBase) continue;

    const apexVec = parseFracVec3(exactApex.xyz);
    const baseVecs = basePtExacts.map((p) => parseFracVec3(p.xyz!));
    const latSq = baseVecs.map((bv) => metricDot(vSub(apexVec, bv), vSub(apexVec, bv), gMetric));
    if (latSq[0][0] <= 0n || !latSq.every((sq) => fEq(sq, latSq[0]))) continue;

    let sumV: FracVec3 = [[0n, 1n], [0n, 1n], [0n, 1n]];
    for (const bv of baseVecs) sumV = vAdd(sumV, bv);
    const invM: Frac = [1n, BigInt(m)];
    const centroidVec: FracVec3 = [fMul(invM, sumV[0]), fMul(invM, sumV[1]), fMul(invM, sumV[2])];

    const exactCenterPt = exactRef.objects.find(
      (p) =>
        !isSubEntity(p.id)
        && p.type === "point3"
        && p.id !== exactApex.id
        && !baseVidSet.has(p.id)
        && Boolean(p.xyz && vIsZero(vSub(parseFracVec3(p.xyz), centroidVec)))
        && isCompactPointSym(shortSym(p)),
    );
    if (!exactCenterPt) continue;
    const curCenterPt = curById.get(exactCenterPt.id);
    if (!curCenterPt?.xyz) continue;

    const vSO = vSub(apexVec, centroidVec);
    const hSq = metricDot(vSO, vSO, gMetric);
    if (hSq[0] <= 0n) continue;
    const perpToAllRadii = baseVecs.every((bv) => fIsZero(metricDot(vSO, vSub(bv, centroidVec), gMetric)));
    if (!perpToAllRadii) continue;

    const baseEvIdx = curScene.events.findIndex(
      (ev) => ev.action === "CREATE" && (ev.object === basePoly.id || (ev.objects ?? []).includes(basePoly.id)),
    );
    if (baseEvIdx < 0) continue;

    const symS = shortSym(curApex);
    const symO = shortSym(curCenterPt);
    const baseDepNames = basePtExacts.map((p) => shortSym(p)).filter(isCompactPointSym);
    const baseCyc =
      baseDepNames.length >= 3
        ? canonicalizeCycleNames(baseDepNames, preferredPointOrderForPolygon(curScene, basePoly)).join("")
        : (basePoly.notation?.replace(/^\(|\)$/gu, "").trim() || shortSym(basePoly));
    const uExact = vSub(baseVecs[0], centroidVec);
    const vExact = vSO;
    const pDir1 = vSub(baseVecs[1], baseVecs[0]);
    const pDir2 = vSub(baseVecs[2], baseVecs[0]);
    const dispS = curApex.xyz;
    const dispO = curCenterPt.xyz;
    const altObj: SceneObject = {
      id: altId,
      type: "segment3",
      label: `Đường cao ${symS}${symO}`,
      notation: `${symS}${symO}`,
      reference: `${symS}${symO}`,
      role: `Đường cao hạ từ đỉnh ${symS} vuông góc với mặt đáy (${baseCyc}) tại tâm ${symO}`,
      origin: "derived",
      authoritative: false,
      semantic_role: "CERTIFIED_RELATION_MARKER",
      producer: null,
      render: "segment",
      display_group: ["construction"],
      formation_roles: ["CONSTRUCT_HEIGHT"],
      depends: [curApex.id, curCenterPt.id, basePoly.id],
      endpoint_ids: [curApex.id, curCenterPt.id],
      source: { instruction: "EXPLANATORY_DERIVED_WITNESS" },
      point_a: dispS,
      point_b: dispO,
      endpoints: [dispS, dispO],
      perpendicular_witness: {
        from: curApex.id,
        on: basePoly.id,
        foot: dispO,
        foot_id: curCenterPt.id,
        relation: "line_perp_plane",
        rule: "regular_pyramid_center_altitude",
        can_present_as_proven: true,
        plane_directions: [mapExactVecToSceneFrame(pDir1, chartT), mapExactVecToSceneFrame(pDir2, chartT)],
        marker: {
          u: mapExactVecToSceneFrame(uExact, chartT),
          v: mapExactVecToSceneFrame(vExact, chartT),
        },
      },
    };

    didExpand = true;
    const insertEvIdx = baseEvIdx + 1;
    const baseObjIdx = curScene.objects.findIndex((o) => o.id === basePoly.id);
    const nextObjects = [...curScene.objects];
    nextObjects.splice(baseObjIdx >= 0 ? baseObjIdx + 1 : nextObjects.length, 0, altObj);
    const hasTypedEvents =
      curScene.events.length > 0
      && curScene.events.every((e, k) => Boolean(e.semantic_kind || curScene.formation?.steps[k]?.semantic_kind));
    const altExplanation = `Hình chóp đều có chân đường cao trùng tâm ${symO} của đáy (${baseCyc}); dựng ${symS}${symO} ⊥ (${baseCyc}).`;
    const createAltEv: SceneEvent = {
      step_index: insertEvIdx,
      action: "CREATE",
      object: altId,
      objects: [altId],
      depends: [curApex.id, curCenterPt.id, basePoly.id],
      explanation: altExplanation,
      ...(hasTypedEvents ? { semantic_kind: "GEOMETRY_CONSTRUCTION" as const } : {}),
    };
    const nextEvents: SceneEvent[] = [];
    for (let k = 0; k < curScene.events.length; k += 1) {
      if (k === insertEvIdx) {
        nextEvents.push({ ...createAltEv, step_index: nextEvents.length });
      }
      nextEvents.push({ ...curScene.events[k], step_index: nextEvents.length });
    }
    if (insertEvIdx >= curScene.events.length) {
      nextEvents.push({ ...createAltEv, step_index: nextEvents.length });
    }
    let nextFormation = curScene.formation;
    if (curScene.formation && curScene.formation.steps.length === curScene.events.length) {
      const origSteps = curScene.formation.steps;
      const refStep = origSteps[baseEvIdx];
      const stepAlt: FormationStep = {
        ...refStep,
        step_index: insertEvIdx,
        visible_ids: [...new Set([...refStep.visible_ids, curCenterPt.id, curApex.id, altId])],
        readout_ids: [...refStep.readout_ids],
        focus_ids: [altId, curCenterPt.id, curApex.id],
        learner_text: altExplanation,
        semantic_kind: "GEOMETRY_CONSTRUCTION",
      };
      const rebuiltSteps: FormationStep[] = [];
      for (let k = 0; k < origSteps.length; k += 1) {
        if (k === insertEvIdx) {
          rebuiltSteps.push({ ...stepAlt, step_index: rebuiltSteps.length });
        }
        const st = origSteps[k];
        const vis = k >= insertEvIdx ? [...new Set([...st.visible_ids, curCenterPt.id, curApex.id, altId])] : st.visible_ids;
        rebuiltSteps.push({ ...st, step_index: rebuiltSteps.length, visible_ids: vis });
      }
      if (insertEvIdx >= origSteps.length) {
        rebuiltSteps.push({ ...stepAlt, step_index: rebuiltSteps.length });
      }
      nextFormation = { steps: rebuiltSteps };
    }
    curScene = {
      ...curScene,
      objects: nextObjects,
      events: nextEvents,
      ...(nextFormation ? { formation: nextFormation } : {}),
    };
  }

  // ── 0b. Đoạn trung tuyến phụ tạm thời khi dựng trọng tâm G theo tỉ số 2/3 trên trung tuyến ───────
  const centroidPts = curScene.objects.filter(
    (o) => !isSubEntity(o.id) && o.type === "point3" && Boolean(o.xyz) && Boolean(o.notation),
  );
  for (const gObj of centroidPts) {
    const medId = `${gObj.id}__median`;
    if (curScene.objects.some((o) => o.id === medId)) continue;
    const centRel = findPointCentroidRelation(exactRef, gObj);
    if (
      centRel?.constructionMode !== "median_ratio"
      || !centRel.medianVertexId
      || !centRel.helperMidpointId
      || !centRel.medianVertexSym
    ) {
      continue;
    }
    const curById = new Map(curScene.objects.map((o) => [o.id, o]));
    const curVert = curById.get(centRel.medianVertexId);
    const curMid = curById.get(centRel.helperMidpointId);
    if (!curVert?.xyz || !curMid?.xyz) continue;
    const gEvIdx = curScene.events.findIndex(
      (ev) => ev.action === "CREATE" && (ev.object === gObj.id || (ev.objects ?? []).includes(gObj.id)),
    );
    if (gEvIdx < 0) continue;

    didExpand = true;
    const oppEdge = centRel.oppositeEdgeSyms?.join("") ?? "";
    const medObj: SceneObject = {
      id: medId,
      type: "segment3",
      label: `Trung tuyến qua ${centRel.medianVertexSym}`,
      role: oppEdge
        ? `Đường trung tuyến từ ${centRel.medianVertexSym} tới trung điểm cạnh ${oppEdge}`
        : `Đường trung tuyến đi qua ${centRel.medianVertexSym}`,
      origin: "derived",
      authoritative: false,
      semantic_role: "AUXILIARY_CONSTRUCTION",
      producer: null,
      render: "segment",
      display_group: ["construction"],
      formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"],
      depends: [centRel.medianVertexId, centRel.helperMidpointId],
      endpoint_ids: [centRel.medianVertexId, centRel.helperMidpointId],
      source: { instruction: "EXPLANATORY_DERIVED_WITNESS" },
      point_a: curVert.xyz,
      point_b: curMid.xyz,
      endpoints: [curVert.xyz, curMid.xyz],
    };
    const gObjIdx = curScene.objects.findIndex((o) => o.id === gObj.id);
    const nextObjects = [...curScene.objects];
    nextObjects.splice(gObjIdx >= 0 ? gObjIdx + 1 : nextObjects.length, 0, medObj);
    const nextEvents = curScene.events.map((ev, k) =>
      k === gEvIdx
        ? { ...ev, objects: [...new Set([ev.object ?? gObj.id, ...(ev.objects ?? []), medId])] }
        : ev,
    );
    const nextFormation = curScene.formation
      ? {
          steps: curScene.formation.steps.map((st, k) =>
            k >= gEvIdx ? { ...st, visible_ids: [...new Set([...st.visible_ids, medId])] } : st,
          ),
        }
      : undefined;
    curScene = {
      ...curScene,
      objects: nextObjects,
      events: nextEvents,
      ...(nextFormation ? { formation: nextFormation } : {}),
    };
  }

  // ── 0b. Giao điểm O của hai đường chéo mặt tứ giác: bổ sung đoạn chéo nét đứt AC, BD khi chưa có ──
  const diagCandPts = curScene.objects.filter(
    (o) =>
      !isSubEntity(o.id)
      && o.type === "point3"
      && Boolean(o.xyz)
      && (o.origin === "derived"
        || curScene.objects.some(
          (s) =>
            s.perpendicular_witness?.foot_id === o.id
            || ((s.formation_roles ?? []).includes("CONSTRUCT_HEIGHT")
              && (s.endpoint_ids ?? s.depends ?? []).includes(o.id)),
        )),
  );
  for (const dPt of diagCandPts) {
    if (curScene.objects.some((o) => o.id === `${dPt.id}__diag_1` || o.id === `${dPt.id}__diag_2`)) continue;
    const diagRel = findPolygonDiagonalIntersectionRelation(curScene, dPt, { allowHeightFoot: true });
    if (!diagRel) continue;
    let dEvIdx = curScene.events.findIndex(
      (ev) => ev.action !== "INIT" && (ev.object === dPt.id || (ev.objects ?? []).includes(dPt.id)),
    );
    if (dEvIdx < 0) {
      dEvIdx = curScene.events.findIndex(
        (ev) =>
          ev.action !== "INIT"
          && curScene.objects.some(
            (s) =>
              (ev.object === s.id || (ev.objects ?? []).includes(s.id))
              && (s.perpendicular_witness?.foot_id === dPt.id
                || ((s.formation_roles ?? []).includes("CONSTRUCT_HEIGHT")
                  && (s.endpoint_ids ?? s.depends ?? []).includes(dPt.id))),
          ),
      );
    }
    if (dEvIdx < 0) continue;
    const curById = new Map(curScene.objects.map((o) => [o.id, o]));
    const hasDrawnPair = (u: string, v: string) =>
      curScene.objects.some((o) => {
        if (isSubEntity(o.id) || (o.type !== "segment3" && o.type !== "line3")) return false;
        const eps = o.endpoint_ids ?? o.depends ?? [];
        return eps.length === 2 && ((eps[0] === u && eps[1] === v) || (eps[0] === v && eps[1] === u));
      });
    const insertedDiags: SceneObject[] = [];
    const pairs: [string, string, string, string][] = [
      [`${dPt.id}__diag_1`, diagRel.aId, diagRel.cId, diagRel.d1Sym],
      [`${dPt.id}__diag_2`, diagRel.bId, diagRel.dId, diagRel.d2Sym],
    ];
    for (const [diagId, uId, vId, dSym] of pairs) {
      if (hasDrawnPair(uId, vId)) continue;
      const uObj = curById.get(uId);
      const vObj = curById.get(vId);
      if (!uObj?.xyz || !vObj?.xyz) continue;
      insertedDiags.push({
        id: diagId,
        type: "segment3",
        label: `Đường chéo ${dSym}`,
        notation: dSym,
        reference: dSym,
        role: `Đường chéo ${dSym}${diagRel.polySym ? ` của mặt ${diagRel.polySym}` : ""} xác định giao điểm ${shortSym(dPt)}`,
        origin: "derived",
        authoritative: false,
        semantic_role: "AUXILIARY_CONSTRUCTION",
        producer: null,
        render: "segment",
        display_group: ["construction"],
        formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"],
        depends: [uId, vId],
        endpoint_ids: [uId, vId],
        source: { instruction: "EXPLANATORY_DERIVED_WITNESS" },
        point_a: uObj.xyz,
        point_b: vObj.xyz,
        endpoints: [uObj.xyz, vObj.xyz],
      });
    }
    if (insertedDiags.length === 0) continue;
    didExpand = true;
    const insertedIds = insertedDiags.map((x) => x.id);
    const ptIdx = curScene.objects.findIndex((o) => o.id === dPt.id);
    const nextObjects = [...curScene.objects];
    nextObjects.splice(ptIdx >= 0 ? ptIdx : nextObjects.length, 0, ...insertedDiags);
    const nextEvents = curScene.events.map((ev, k) =>
      k === dEvIdx
        ? { ...ev, objects: [...new Set([...insertedIds, ev.object ?? dPt.id, ...(ev.objects ?? [])])] }
        : ev,
    );
    const nextFormation = curScene.formation
      ? {
          steps: curScene.formation.steps.map((st, k) =>
            k >= dEvIdx ? { ...st, visible_ids: [...new Set([...st.visible_ids, ...insertedIds])] } : st,
          ),
        }
      : undefined;
    curScene = {
      ...curScene,
      objects: nextObjects,
      events: nextEvents,
      ...(nextFormation ? { formation: nextFormation } : {}),
    };
  }

  // ── 1. Tương giao mặt cầu và mặt phẳng (cát tuyến 0 < d < R, đường tròn lớn d = 0, tiếp diện d = R) ─────────
  const sphereSections = curScene.objects.filter(
    (o) => !isSubEntity(o.id) && o.type === "circle3" && o.surface_role !== "BASE_REGION",
  );
  for (const sec of sphereSections) {
    if (
      curScene.objects.some(
        (o) => o.id === `${sec.id}__center` || o.id === `${sec.id}__dist` || o.id === `${sec.id}__sph_rad`,
      )
    ) {
      continue;
    }
    const exactById = new Map(exactRef.objects.map((o) => [o.id, o]));
    const curById = new Map(curScene.objects.map((o) => [o.id, o]));
    const exactSec = exactById.get(sec.id) ?? sec;
    if (!exactSec.center || !exactSec.normal || !exactSec.radius_sq) continue;

    const depIds = exactSec.depends ?? sec.depends ?? [];
    const exactBall = depIds
      .map((id) => exactById.get(id))
      .find((d): d is SceneObject => Boolean(d && d.type === "curved_solid" && d.curved_kind === "ball" && d.anchor && d.radius_sq));
    const exactPlane = depIds
      .map((id) => exactById.get(id))
      .find((d): d is SceneObject => Boolean(d && d.type === "plane3" && d.point && d.normal));
    if (!exactBall?.anchor || !exactBall.radius_sq || !exactPlane?.point || !exactPlane.normal) continue;

    const evIdx = curScene.events.findIndex(
      (ev) => ev.action === "CREATE" && (ev.object === sec.id || (ev.objects ?? []).includes(sec.id)),
    );
    if (evIdx < 0) continue;

    const I = parseFracVec3(exactBall.anchor);
    const H = parseFracVec3(exactSec.center);
    const vIH = vSub(H, I);
    const d2 = metricDot(vIH, vIH, exactRef.chart_metric);
    const r2 = parseExactFrac(exactSec.radius_sq);
    const R2 = parseExactFrac(exactBall.radius_sq);
    if (d2[0] < 0n || r2[0] <= 0n) continue;
    if (!fEq(fAdd(d2, r2), R2)) continue;

    const planeBasis = findRationalPlaneBasis(parseFracVec3(exactPlane.normal));
    if (!planeBasis) continue;
    const [t1, t2] = planeBasis;

    const curBall = curById.get(exactBall.id) ?? exactBall;
    const curPlane = curById.get(exactPlane.id) ?? exactPlane;
    const existingCenterPt = curScene.objects.find((p) => {
      if (isSubEntity(p.id) || p.type !== "point3") return false;
      const ep = exactById.get(p.id) ?? p;
      return Boolean(ep.xyz && vIsZero(vSub(parseFracVec3(ep.xyz), I)));
    });
    const symI = existingCenterPt ? shortSym(existingCenterPt) : "I";
    const dispI = curBall.anchor ?? mapExactVecToSceneFrame(I, chartT);
    const fromAnchorId = existingCenterPt?.id ?? curBall.id;

    // Kiểm tra điểm vành hữu tỉ chính xác M ∈ Q³ trên đường tròn thiết diện
    let rimExact: FracVec3 | null = null;
    let existingRimPt: SceneObject | undefined;
    for (const p of curScene.objects) {
      if (isSubEntity(p.id) || p.type !== "point3") continue;
      if ((p.display_group ?? []).includes("sphere_foundation_ref")) continue;
      const ep = exactById.get(p.id) ?? p;
      if (!ep.xyz) continue;
      const pv = parseFracVec3(ep.xyz);
      const diffH = vSub(pv, H);
      if (
        fIsZero(plainDotFrac(diffH, parseFracVec3(exactPlane.normal)))
        && fEq(metricDot(diffH, diffH, exactRef.chart_metric), r2)
      ) {
        existingRimPt = p;
        rimExact = pv;
        break;
      }
    }
    if (!rimExact) {
      const rawN = parseFracVec3(exactPlane.normal);
      const candidateDirs: FracVec3[] = [
        t1,
        vScaleFrac([-1n, 1n], t1),
        t2,
        vScaleFrac([-1n, 1n], t2),
      ];
      // Phép phản xạ Householder hữu tỉ chính xác trên Q³: với mọi mặt phẳng nghiêng có pháp tuyến độ dài hữu tỉ,
      // ánh xạ e1 -> ±uN biến {e2, e3} thành cơ sở tiếp tuyến trực chuẩn hữu tỉ đóng O(1) không xấp xỉ.
      const nSqPlain = plainDotFrac(rawN, rawN);
      const nLenFrac = nSqPlain[0] > 0n ? exactFracSqrt(nSqPlain) : null;
      if (nLenFrac) {
        const uN = vScaleFrac(fDiv([1n, 1n], nLenFrac), rawN);
        const e1: FracVec3 = [[1n, 1n], [0n, 1n], [0n, 1n]];
        const e2: FracVec3 = [[0n, 1n], [1n, 1n], [0n, 1n]];
        const e3: FracVec3 = [[0n, 1n], [0n, 1n], [1n, 1n]];
        const pivot = !vIsZero(vAdd(uN, e1)) ? vAdd(uN, e1) : vSub(uN, e1);
        const pSq = plainDotFrac(pivot, pivot);
        if (pSq[0] > 0n) {
          const reflect = (x: FracVec3): FracVec3 => {
            const scale = fDiv(fMul([2n, 1n], plainDotFrac(pivot, x)), pSq);
            return vSub(x, vScaleFrac(scale, pivot));
          };
          const re2 = reflect(e2);
          const re3 = reflect(e3);
          candidateDirs.push(re2, vScaleFrac([-1n, 1n], re2), re3, vScaleFrac([-1n, 1n], re3));
        }
      }
      // Trực giao hóa Gram–Schmidt theo chart_metric hữu tỉ tổng quát
      const g11 = metricDot(t1, t1, exactRef.chart_metric);
      if (g11[0] > 0n) {
        const g12 = metricDot(t1, t2, exactRef.chart_metric);
        const v2Ortho = vSub(t2, vScaleFrac(fDiv(g12, g11), t1));
        if (!vIsZero(v2Ortho)) {
          candidateDirs.push(v2Ortho, vScaleFrac([-1n, 1n], v2Ortho));
          for (const signP of [1n, -1n]) {
            for (let p = 1n; p <= 6n; p += 1n) {
              for (let q = -6n; q <= 6n; q += 1n) {
                if (q === 0n) continue;
                candidateDirs.push(vAdd(vScaleFrac([signP * p, 1n], t1), vScaleFrac([q, 1n], v2Ortho)));
              }
            }
          }
        }
      }
      const dispHPreview = mapExactVecToSceneFrame(H, chartT);
      const dispIPreview = dispI;
      const viewLenCanon = Math.hypot(8, 3, 6);
      const rxC = 8 / viewLenCanon, ryC = 3 / viewLenCanon, rzC = 6 / viewLenCanon;
      const vDispX = toNumber(dispIPreview[0]) - toNumber(dispHPreview[0]);
      const vDispY = toNumber(dispIPreview[1]) - toNumber(dispHPreview[1]);
      const vDispZ = toNumber(dispIPreview[2]) - toNumber(dispHPreview[2]);
      const vDispLen = Math.hypot(vDispX, vDispY, vDispZ);
      let bestRimScore = -Infinity;
      for (const candDir of candidateDirs) {
        if (vIsZero(candDir) || !fIsZero(plainDotFrac(candDir, rawN))) continue;
        const lenSq = metricDot(candDir, candDir, exactRef.chart_metric);
        if (lenSq[0] <= 0n) continue;
        const ratioSq = normFrac(r2[0] * lenSq[1], r2[1] * lenSq[0]);
        const kFrac = exactFracSqrt(ratioSq);
        if (kFrac) {
          const candRim = vAdd(H, vScaleFrac(kFrac, candDir));
          if (
            fEq(metricDot(vSub(candRim, H), vSub(candRim, H), exactRef.chart_metric), r2)
            && fEq(metricDot(vSub(candRim, I), vSub(candRim, I), exactRef.chart_metric), R2)
          ) {
            const dispCand = mapExactVecToSceneFrame(candRim, chartT);
            const uxD = toNumber(dispCand[0]) - toNumber(dispHPreview[0]);
            const uyD = toNumber(dispCand[1]) - toNumber(dispHPreview[1]);
            const uzD = toNumber(dispCand[2]) - toNumber(dispHPreview[2]);
            const uDispLen = Math.hypot(uxD, uyD, uzD);
            if (uDispLen <= 1e-8) continue;
            const udx = uxD / uDispLen, udy = uyD / uDispLen, udz = uzD / uDispLen;
            let opennessScore = 0;
            if (vDispLen > 1e-6) {
              const vdx = vDispX / vDispLen, vdy = vDispY / vDispLen, vdz = vDispZ / vDispLen;
              const cx = udy * vdz - udz * vdy;
              const cy = udz * vdx - udx * vdz;
              const cz = udx * vdy - udy * vdx;
              opennessScore = Math.abs(cx * rxC + cy * ryC + cz * rzC);
            } else {
              opennessScore = Math.hypot(
                udy * rzC - udz * ryC,
                udz * rxC - udx * rzC,
                udx * ryC - udy * rxC,
              );
            }
            const frontRightBias = 0.015 * ((3 * udx - 8 * udy) / Math.hypot(3, -8));
            let refSepPenalty = 0;
            const sphereRefObj = curById.get(`${exactBall.id}__ref_pt`);
            if (sphereRefObj?.xyz) {
              const rxVec = toNumber(sphereRefObj.xyz[0]) - toNumber(dispIPreview[0]);
              const ryVec = toNumber(sphereRefObj.xyz[1]) - toNumber(dispIPreview[1]);
              const rzVec = toNumber(sphereRefObj.xyz[2]) - toNumber(dispIPreview[2]);
              const rVecLen = Math.hypot(rxVec, ryVec, rzVec);
              const mxVec = toNumber(dispCand[0]) - toNumber(dispIPreview[0]);
              const myVec = toNumber(dispCand[1]) - toNumber(dispIPreview[1]);
              const mzVec = toNumber(dispCand[2]) - toNumber(dispIPreview[2]);
              const mVecLen = Math.hypot(mxVec, myVec, mzVec);
              if (rVecLen > 1e-6 && mVecLen > 1e-6) {
                const cosRef = (rxVec * mxVec + ryVec * myVec + rzVec * mzVec) / (rVecLen * mVecLen);
                if (cosRef > 0.92) refSepPenalty = 2.0;
                else if (cosRef > 0.5) refSepPenalty = 0.15 * cosRef;
              }
            }
            const totalScore = opennessScore + frontRightBias - refSepPenalty;
            if (totalScore > bestRimScore + 1e-7) {
              bestRimScore = totalScore;
              rimExact = candRim;
            }
          }
        }
      }
    }

    // Trường hợp 1B: Mặt phẳng đi qua tâm mặt cầu (d = 0, đường tròn lớn) — không sinh đoạn IH độ dài 0
    if (fIsZero(d2)) {
      if (!rimExact) continue;
      const dispRim = existingRimPt?.xyz ?? mapExactVecToSceneFrame(rimExact, chartT);
      const symM = existingRimPt ? shortSym(existingRimPt) : pickUnusedSym(curScene, ["M", "A", "E"]);
      const mId = existingRimPt?.id ?? `${sec.id}__rim_pt`;
      const greatInserted: SceneObject[] = [];
      if (!existingRimPt) {
        greatInserted.push({
          id: mId,
          type: "point3",
          label: `Điểm ${symM}`,
          notation: symM,
          reference: symM,
          role: `Điểm thuộc đường tròn lớn giao tuyến của mặt cầu và ${formatPlaneDisplayNotation(curPlane)}`,
          origin: "derived",
          authoritative: false,
          semantic_role: "AUXILIARY_CONSTRUCTION",
          producer: null,
          render: "point_marker",
          display_group: ["construction", "sphere_plane_aux"],
          formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"],
          depends: [fromAnchorId, curPlane.id, curBall.id],
          source: { instruction: "EXPLANATORY_DERIVED_WITNESS" },
          xyz: dispRim,
        });
      }
      greatInserted.push({
        id: `${sec.id}__sph_rad`,
        type: "segment3",
        label: `Bán kính ${symI}${symM}`,
        notation: `${symI}${symM}`,
        reference: `${symI}${symM}`,
        role: `Bán kính nối tâm ${symI} với điểm ${symM} trên đường tròn lớn`,
        origin: "derived",
        authoritative: false,
        semantic_role: "AUXILIARY_CONSTRUCTION",
        producer: null,
        render: "segment",
        display_group: ["construction", "sphere_plane_aux"],
        formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"],
        depends: [fromAnchorId, mId, curBall.id],
        endpoint_ids: [fromAnchorId, mId],
        source: { instruction: "EXPLANATORY_DERIVED_WITNESS" },
        point_a: dispI,
        point_b: dispRim,
        endpoints: [dispI, dispRim],
      });
      didExpand = true;
      const insIds = greatInserted.map((x) => x.id);
      const secObjIdx = curScene.objects.findIndex((o) => o.id === sec.id);
      const nextObjects = [...curScene.objects];
      nextObjects.splice(secObjIdx >= 0 ? secObjIdx + 1 : nextObjects.length, 0, ...greatInserted);
      const ballEvIdx0 = curScene.events.findIndex(
        (ev) => ev.action === "CREATE" && (ev.object === curBall.id || (ev.objects ?? []).includes(curBall.id)),
      );
      const planeEvIdx0 = curScene.events.findIndex(
        (ev) => ev.action === "CREATE" && (ev.object === curPlane.id || (ev.objects ?? []).includes(curPlane.id)),
      );
      const readyEvIdx0 = Math.max(ballEvIdx0, planeEvIdx0);
      const canSplitGreatStep = planeEvIdx0 >= 0 && readyEvIdx0 >= 0 && readyEvIdx0 < evIdx;
      let nextEvents: typeof curScene.events;
      let nextFormation: Scene3D["formation"] = curScene.formation;
      if (canSplitGreatStep) {
        const rawEvents = [...curScene.events];
        rawEvents[evIdx] = {
          ...rawEvents[evIdx],
          depends: [...new Set([...(rawEvents[evIdx].depends ?? []), mId])],
        };
        rawEvents.splice(evIdx, 0, {
          step_index: evIdx,
          action: "CREATE",
          object: insIds[0] ?? null,
          objects: insIds,
          depends: [fromAnchorId, curPlane.id, curBall.id],
          explanation: "",
          semantic_kind: "GEOMETRY_CONSTRUCTION",
        });
        nextEvents = rawEvents.map((ev, idx) => ({ ...ev, step_index: idx }));
        if (curScene.formation && curScene.formation.steps.length === curScene.events.length) {
          const rawSteps = [...curScene.formation.steps];
          const prevFormStep = rawSteps[Math.max(0, evIdx - 1)];
          const insertedFormStep = {
            ...prevFormStep,
            semantic_kind: "GEOMETRY_CONSTRUCTION" as const,
            formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"],
            visible_ids: [...new Set([...prevFormStep.visible_ids, ...insIds])],
            focus_ids: [...insIds],
          };
          rawSteps.splice(evIdx, 0, insertedFormStep);
          nextFormation = {
            steps: rawSteps.map((st, idx) => ({
              ...st,
              ...(typeof (st as { step_index?: number }).step_index === "number" ? { step_index: idx } : {}),
              visible_ids: idx >= evIdx ? [...new Set([...st.visible_ids, ...insIds])] : st.visible_ids,
            })),
          };
        }
      } else {
        nextEvents = curScene.events.map((ev, k) =>
          k === evIdx
            ? { ...ev, objects: [...new Set([ev.object ?? sec.id, ...(ev.objects ?? []), ...insIds])] }
            : ev,
        );
        nextFormation = curScene.formation
          ? {
              steps: curScene.formation.steps.map((st, k) =>
                k >= evIdx
                  ? {
                      ...st,
                      visible_ids: [...new Set([...st.visible_ids, ...insIds])],
                      ...(k === evIdx ? { focus_ids: [...new Set([...st.focus_ids, ...insIds])] } : {}),
                    }
                  : st,
              ),
            }
          : undefined;
      }
      curScene = {
        ...curScene,
        objects: nextObjects,
        events: nextEvents,
        ...(nextFormation ? { formation: nextFormation } : {}),
      };
      continue;
    }

    // Trường hợp 1A: Mặt phẳng cắt mặt cầu (0 < d < R) — tách tiến trình sư phạm (§3.3): (S) -> (P) -> (H, IH) -> (M, HM, IM nếu M ∈ Q³) -> (C)
    const vHI = vSub(I, H);
    if (
      !fIsZero(metricDot(vHI, t1, exactRef.chart_metric))
      || !fIsZero(metricDot(vHI, t2, exactRef.chart_metric))
    ) {
      continue;
    }

    const existingFootPt = curScene.objects.find((p) => {
      if (isSubEntity(p.id) || p.type !== "point3") return false;
      const ep = exactById.get(p.id) ?? p;
      return Boolean(ep.xyz && vIsZero(vSub(parseFracVec3(ep.xyz), H)));
    });
    const symH = existingFootPt ? shortSym(existingFootPt) : pickUnusedSym(curScene, ["H", "O", "K"]);
    const dispH = sec.center ?? mapExactVecToSceneFrame(H, chartT);
    const distInserted: SceneObject[] = [];
    const secInserted: SceneObject[] = [];

    const markerUExact = rimExact ? vSub(rimExact, H) : t1;
    const dispMarkerU = mapExactVecToSceneFrame(markerUExact, chartT);
    const dispMarkerV = mapExactVecToSceneFrame(vHI, chartT);
    const dispPlaneDirs: ExactVec3[] = [
      mapExactVecToSceneFrame(t1, chartT),
      mapExactVecToSceneFrame(t2, chartT),
    ];

    const hId = existingFootPt?.id ?? `${sec.id}__center`;
    const perpWitness: NonNullable<SceneObject["perpendicular_witness"]> = {
      from: fromAnchorId,
      from_point: dispI,
      on: curPlane.id,
      foot: dispH,
      foot_id: hId,
      relation: "line_perp_plane",
      can_present_as_proven: true,
      plane_directions: dispPlaneDirs,
      marker: {
        u: dispMarkerU,
        v: dispMarkerV,
      },
    };

    if (!existingFootPt) {
      distInserted.push({
        id: hId,
        type: "point3",
        label: `Hình chiếu ${symH}`,
        notation: symH,
        reference: symH,
        role: `Hình chiếu vuông góc của tâm ${symI} trên ${formatPlaneDisplayNotation(curPlane)}`,
        origin: "derived",
        authoritative: false,
        semantic_role: "AUXILIARY_CONSTRUCTION",
        producer: null,
        render: "point_marker",
        display_group: ["construction", "sphere_plane_aux"],
        formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"],
        depends: [fromAnchorId, curPlane.id],
        source: { instruction: "EXPLANATORY_DERIVED_WITNESS" },
        xyz: dispH,
        perpendicular_witness: perpWitness,
      });
    }

    distInserted.push({
      id: `${sec.id}__dist`,
      type: "segment3",
      label: `Đoạn vuông góc ${symI}${symH}`,
      notation: `${symI}${symH}`,
      reference: `${symI}${symH}`,
      role: `Đoạn vuông góc hạ từ tâm ${symI} đến ${formatPlaneDisplayNotation(curPlane)} tại ${symH}`,
      origin: "derived",
      authoritative: false,
      semantic_role: "AUXILIARY_CONSTRUCTION",
      producer: null,
      render: "segment",
      display_group: ["construction", "sphere_plane_aux", "sphere_plane_dist"],
      formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"],
      depends: [fromAnchorId, hId, curPlane.id],
      endpoint_ids: [fromAnchorId, hId],
      source: { instruction: "EXPLANATORY_DERIVED_WITNESS" },
      point_a: dispI,
      point_b: dispH,
      endpoints: [dispI, dispH],
      perpendicular_witness: perpWitness,
    });

    const mId = existingRimPt?.id ?? `${sec.id}__rim_pt`;
    if (rimExact) {
      const dispRim = existingRimPt?.xyz ?? mapExactVecToSceneFrame(rimExact, chartT);
      const symM = existingRimPt ? shortSym(existingRimPt) : pickUnusedSym(curScene, ["M", "A", "E"]);
      if (!existingRimPt) {
        secInserted.push({
          id: mId,
          type: "point3",
          label: `Điểm ${symM}`,
          notation: symM,
          reference: symM,
          role: `Điểm thuộc đường tròn giao tuyến của mặt cầu và ${formatPlaneDisplayNotation(curPlane)}`,
          origin: "derived",
          authoritative: false,
          semantic_role: "AUXILIARY_CONSTRUCTION",
          producer: null,
          render: "point_marker",
          display_group: ["construction", "sphere_plane_aux"],
          formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"],
          depends: [fromAnchorId, hId, curPlane.id, curBall.id],
          source: { instruction: "EXPLANATORY_DERIVED_WITNESS" },
          xyz: dispRim,
        });
      }
      secInserted.push({
        id: `${sec.id}__sec_rad`,
        type: "segment3",
        label: `Bán kính thiết diện ${symH}${symM}`,
        notation: `${symH}${symM}`,
        reference: `${symH}${symM}`,
        role: `Bán kính đường tròn giao tuyến nối tâm ${symH} với điểm ${symM}`,
        origin: "derived",
        authoritative: false,
        semantic_role: "AUXILIARY_CONSTRUCTION",
        producer: null,
        render: "segment",
        display_group: ["construction", "sphere_plane_aux"],
        formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"],
        depends: [hId, mId, curPlane.id],
        endpoint_ids: [hId, mId],
        source: { instruction: "EXPLANATORY_DERIVED_WITNESS" },
        point_a: dispH,
        point_b: dispRim,
        endpoints: [dispH, dispRim],
      });
      secInserted.push({
        id: `${sec.id}__sph_rad`,
        type: "segment3",
        label: `Bán kính mặt cầu ${symI}${symM}`,
        notation: `${symI}${symM}`,
        reference: `${symI}${symM}`,
        role: `Bán kính mặt cầu nối tâm ${symI} với điểm ${symM} trên giao tuyến`,
        origin: "derived",
        authoritative: false,
        semantic_role: "AUXILIARY_CONSTRUCTION",
        producer: null,
        render: "segment",
        display_group: ["construction", "sphere_plane_aux"],
        formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"],
        depends: [fromAnchorId, mId, curBall.id],
        endpoint_ids: [fromAnchorId, mId],
        source: { instruction: "EXPLANATORY_DERIVED_WITNESS" },
        point_a: dispI,
        point_b: dispRim,
        endpoints: [dispI, dispRim],
      });
    }

    if (distInserted.length > 0 || secInserted.length > 0) {
      didExpand = true;
      const ballEvIdx = curScene.events.findIndex(
        (ev) => ev.action === "CREATE" && (ev.object === curBall.id || (ev.objects ?? []).includes(curBall.id)),
      );
      const planeEvIdx = curScene.events.findIndex(
        (ev) => ev.action === "CREATE" && (ev.object === curPlane.id || (ev.objects ?? []).includes(curPlane.id)),
      );
      const readyEvIdx = Math.max(ballEvIdx, planeEvIdx);
      const canSplitSteps = planeEvIdx >= 0 && readyEvIdx >= 0 && readyEvIdx < evIdx;
      const distIds = distInserted.map((x) => x.id);
      const secIds = secInserted.map((x) => x.id);

      const nextObjects = [...curScene.objects];
      const planeObjIdx = nextObjects.findIndex((o) => o.id === curPlane.id);
      if (distInserted.length > 0) {
        nextObjects.splice(planeObjIdx >= 0 ? planeObjIdx + 1 : nextObjects.length, 0, ...distInserted);
      }
      const secObjIdx = nextObjects.findIndex((o) => o.id === sec.id);
      if (secInserted.length > 0) {
        nextObjects.splice(secObjIdx >= 0 ? secObjIdx : nextObjects.length, 0, ...secInserted);
      }

      let nextEvents: typeof curScene.events;
      let nextFormation: Scene3D["formation"] = curScene.formation;

      if (canSplitSteps) {
        const rawEvents = [...curScene.events];
        const hasSyncedFormation = Boolean(curScene.formation && curScene.formation.steps.length === rawEvents.length);
        const rawFormSteps = hasSyncedFormation ? [...curScene.formation!.steps] : [];

        let curSecEvIdx = evIdx;
        if (distIds.length > 0) {
          const distInsertAt = readyEvIdx + 1;
          rawEvents.splice(distInsertAt, 0, {
            step_index: distInsertAt,
            action: "CREATE",
            object: distIds[0] ?? null,
            objects: distIds,
            depends: [fromAnchorId, curPlane.id],
            explanation: "",
            semantic_kind: "GEOMETRY_CONSTRUCTION",
          });
          if (hasSyncedFormation) {
            const baseForm = rawFormSteps[Math.max(0, distInsertAt - 1)];
            rawFormSteps.splice(distInsertAt, 0, {
              ...baseForm,
              semantic_kind: "GEOMETRY_CONSTRUCTION",
              visible_ids: [...new Set([...baseForm.visible_ids, ...distIds])],
              focus_ids: [...distIds],
            });
            for (let fi = distInsertAt + 1; fi < rawFormSteps.length; fi += 1) {
              rawFormSteps[fi] = {
                ...rawFormSteps[fi],
                visible_ids: [...new Set([...rawFormSteps[fi].visible_ids, ...distIds])],
              };
            }
          }
          curSecEvIdx += 1;
        }

        if (secIds.length > 0) {
          rawEvents.splice(curSecEvIdx, 0, {
            step_index: curSecEvIdx,
            action: "CREATE",
            object: secIds[0] ?? null,
            objects: secIds,
            depends: [fromAnchorId, hId, curPlane.id, curBall.id],
            explanation: "",
            semantic_kind: "GEOMETRY_CONSTRUCTION",
          });
          if (hasSyncedFormation) {
            const baseForm = rawFormSteps[Math.max(0, curSecEvIdx - 1)];
            rawFormSteps.splice(curSecEvIdx, 0, {
              ...baseForm,
              semantic_kind: "GEOMETRY_CONSTRUCTION",
              visible_ids: [...new Set([...baseForm.visible_ids, ...secIds])],
              focus_ids: [...secIds],
            });
            for (let fi = curSecEvIdx + 1; fi < rawFormSteps.length; fi += 1) {
              rawFormSteps[fi] = {
                ...rawFormSteps[fi],
                visible_ids: [...new Set([...rawFormSteps[fi].visible_ids, ...secIds])],
              };
            }
          }
          curSecEvIdx += 1;
        }

        rawEvents[curSecEvIdx] = {
          ...rawEvents[curSecEvIdx],
          depends: [
            ...new Set([
              ...(rawEvents[curSecEvIdx].depends ?? []),
              hId,
              ...(rimExact ? [mId] : []),
            ]),
          ],
        };
        nextEvents = rawEvents.map((ev, idx) => ({ ...ev, step_index: idx }));
        if (hasSyncedFormation) {
          nextFormation = {
            steps: rawFormSteps.map((st, idx) => ({
              ...st,
              ...(typeof (st as { step_index?: number }).step_index === "number" ? { step_index: idx } : {}),
            })),
          };
        }
      } else {
        nextEvents = curScene.events.map((ev, k) =>
          k === evIdx
            ? {
                ...ev,
                objects: [...new Set([ev.object ?? sec.id, ...(ev.objects ?? []), ...distIds, ...secIds])],
              }
            : ev,
        );
        nextFormation = curScene.formation
          ? {
              steps: curScene.formation.steps.map((st, k) => {
                let vis = st.visible_ids;
                let foc = st.focus_ids;
                if (k >= evIdx) {
                  vis = [...new Set([...vis, ...distIds, ...secIds])];
                }
                if (k === evIdx) {
                  foc = [...new Set([...foc, ...distIds, ...secIds])];
                }
                return vis !== st.visible_ids || foc !== st.focus_ids
                  ? { ...st, visible_ids: vis, focus_ids: foc }
                  : st;
              }),
            }
          : undefined;
      }

      curScene = {
        ...curScene,
        objects: nextObjects,
        events: nextEvents,
        ...(nextFormation ? { formation: nextFormation } : {}),
      };
    }
  }

  // Trường hợp 1C: Mặt phẳng tiếp diện với mặt cầu độc lập (d = R > 0, không có circle3 giao tuyến, không phải mặt cầu nội tiếp khối đa diện/tròn xoay)
  const hasHostNonBallSolid = curScene.objects.some(
    (o) => !isSubEntity(o.id) && (o.type === "solid" || (o.type === "curved_solid" && o.curved_kind !== "ball")),
  );
  const measOnlyPlanesForTangent = measurementOnlyPlanes(curScene);
  const sphereBallsForTangent = hasHostNonBallSolid
    ? []
    : curScene.objects.filter(
        (o) =>
          !isSubEntity(o.id)
          && o.type === "curved_solid"
          && o.curved_kind === "ball"
          && classifySphereSemanticRole(curScene, o) === "STANDALONE_SPHERE",
      );
  const candidateTangentPlanes = curScene.objects.filter(
    (o) => !isSubEntity(o.id) && o.type === "plane3" && !measOnlyPlanesForTangent.has(o.id),
  );
  for (const ballObj of sphereBallsForTangent) {
    for (const plObj of candidateTangentPlanes) {
      const tanDistId = `${ballObj.id}__${plObj.id}__dist`;
      if (curScene.objects.some((o) => o.id === tanDistId)) continue;
      if (
        curScene.objects.some(
          (c) =>
            c.type === "circle3"
            && (c.depends ?? []).includes(ballObj.id)
            && (c.depends ?? []).includes(plObj.id),
        )
      ) {
        continue;
      }
      const exactById = new Map(exactRef.objects.map((o) => [o.id, o]));
      const curById = new Map(curScene.objects.map((o) => [o.id, o]));
      const exBall = exactById.get(ballObj.id) ?? ballObj;
      const exPlane = exactById.get(plObj.id) ?? plObj;
      if (!exBall.anchor || !exBall.radius_sq || !exPlane.point || !exPlane.normal) continue;

      const I = parseFracVec3(exBall.anchor);
      const R2 = parseExactFrac(exBall.radius_sq);
      if (R2[0] <= 0n) continue;
      const proj = projectPointOntoPlaneExact(
        I,
        parseFracVec3(exPlane.point),
        parseFracVec3(exPlane.normal),
        exactRef.chart_metric,
      );
      if (!proj) continue;
      const H = proj.foot;
      const vIH = vSub(H, I);
      const d2 = metricDot(vIH, vIH, exactRef.chart_metric);
      if (fIsZero(d2) || d2[0] <= 0n || !fEq(d2, R2)) continue;

      const ballEvIdx = curScene.events.findIndex(
        (ev) => ev.action === "CREATE" && (ev.object === ballObj.id || (ev.objects ?? []).includes(ballObj.id)),
      );
      const planeEvIdx = curScene.events.findIndex(
        (ev) => ev.action === "CREATE" && (ev.object === plObj.id || (ev.objects ?? []).includes(plObj.id)),
      );

      const curBall = curById.get(ballObj.id) ?? ballObj;
      const curPlane = curById.get(plObj.id) ?? plObj;
      const existingCenterPt = curScene.objects.find((p) => {
        if (isSubEntity(p.id) || p.type !== "point3") return false;
        const ep = exactById.get(p.id) ?? p;
        return Boolean(ep.xyz && vIsZero(vSub(parseFracVec3(ep.xyz), I)));
      });
      const existingFootPt = curScene.objects.find((p) => {
        if (isSubEntity(p.id) || p.type !== "point3") return false;
        const ep = exactById.get(p.id) ?? p;
        return Boolean(ep.xyz && vIsZero(vSub(parseFracVec3(ep.xyz), H)));
      });
      const existingFootEvIdx = existingFootPt
        ? curScene.events.findIndex(
            (ev) => ev.action === "CREATE" && (ev.object === existingFootPt.id || (ev.objects ?? []).includes(existingFootPt.id)),
          )
        : -1;
      const tanEvIdx = Math.max(ballEvIdx, planeEvIdx, existingFootEvIdx);
      if (tanEvIdx < 0) continue;

      const symI = existingCenterPt ? shortSym(existingCenterPt) : "I";
      const symH = existingFootPt ? shortSym(existingFootPt) : pickUnusedSym(curScene, ["H", "T", "M"]);
      const fromAnchorId = existingCenterPt?.id ?? curBall.id;
      const hId = existingFootPt?.id ?? `${ballObj.id}__${plObj.id}__center`;
      const dispI = curBall.anchor ?? mapExactVecToSceneFrame(I, chartT);
      const dispH = existingFootPt?.xyz ?? mapExactVecToSceneFrame(H, chartT);
      const [t1, t2] = proj.basis;
      const vHI = vSub(I, H);
      const canonRayExact: FracVec3 = [[8n, 1n], [3n, 1n], [6n, 1n]];
      const rawCrossTangent = vCross(canonRayExact, vHI);
      const g11Tan = metricDot(t1, t1, exactRef.chart_metric);
      let uTangentExact: FracVec3 = t1;
      if (g11Tan[0] > 0n) {
        const g12Tan = metricDot(t1, t2, exactRef.chart_metric);
        const e2Ortho = vSub(t2, vScaleFrac(fDiv(g12Tan, g11Tan), t1));
        const g22Tan = metricDot(e2Ortho, e2Ortho, exactRef.chart_metric);
        for (const seedEx of [
          rawCrossTangent,
          [[3n, 1n], [-8n, 1n], [0n, 1n]] as FracVec3,
          [[1n, 1n], [0n, 1n], [0n, 1n]] as FracVec3,
          [[0n, 1n], [1n, 1n], [0n, 1n]] as FracVec3,
        ]) {
          if (vIsZero(seedEx)) continue;
          const c1 = fDiv(metricDot(seedEx, t1, exactRef.chart_metric), g11Tan);
          let projTan = vScaleFrac(c1, t1);
          if (g22Tan[0] > 0n) {
            const c2 = fDiv(metricDot(seedEx, e2Ortho, exactRef.chart_metric), g22Tan);
            projTan = vAdd(projTan, vScaleFrac(c2, e2Ortho));
          }
          if (!vIsZero(projTan)) {
            const orientBias = plainDotFrac(projTan, [[3n, 1n], [-8n, 1n], [-2n, 1n]]);
            uTangentExact = orientBias[0] < 0n ? vScaleFrac([-1n, 1n], projTan) : projTan;
            break;
          }
        }
      }
      const perpWitness: NonNullable<SceneObject["perpendicular_witness"]> = {
        from: fromAnchorId,
        from_point: dispI,
        on: curPlane.id,
        foot: dispH,
        foot_id: hId,
        relation: "line_perp_plane",
        can_present_as_proven: true,
        plane_directions: [mapExactVecToSceneFrame(t1, chartT), mapExactVecToSceneFrame(t2, chartT)],
        marker: {
          u: mapExactVecToSceneFrame(uTangentExact, chartT),
          v: mapExactVecToSceneFrame(vHI, chartT),
        },
      };

      const existingIHSeg = curScene.objects.find((s) => {
        if (isSubEntity(s.id) || s.type !== "segment3") return false;
        const es = exactById.get(s.id) ?? s;
        const pA = es.point_a ?? es.endpoints?.[0] ?? (es.endpoint_ids?.[0] ? exactById.get(es.endpoint_ids[0])?.xyz : undefined);
        const pB = es.point_b ?? es.endpoints?.[1] ?? (es.endpoint_ids?.[1] ? exactById.get(es.endpoint_ids[1])?.xyz : undefined);
        if (!pA || !pB) return false;
        const va = parseFracVec3(pA);
        const vb = parseFracVec3(pB);
        return (
          (vIsZero(vSub(va, I)) && vIsZero(vSub(vb, H)))
          || (vIsZero(vSub(va, H)) && vIsZero(vSub(vb, I)))
        );
      });

      if (existingIHSeg) {
        const curSegMarkerKey = `${existingIHSeg.perpendicular_witness?.marker?.u?.join("|") ?? ""}::${existingIHSeg.perpendicular_witness?.marker?.v?.join("|") ?? ""}`;
        const curFootMarkerKey = `${existingFootPt?.perpendicular_witness?.marker?.u?.join("|") ?? ""}::${existingFootPt?.perpendicular_witness?.marker?.v?.join("|") ?? ""}`;
        const nextMarkerKey = `${perpWitness.marker?.u?.join("|") ?? ""}::${perpWitness.marker?.v?.join("|") ?? ""}`;
        if (
          !existingIHSeg.perpendicular_witness
          || curSegMarkerKey !== nextMarkerKey
          || (existingFootPt && existingFootPt.perpendicular_witness && curFootMarkerKey !== nextMarkerKey)
        ) {
          didExpand = true;
          curScene = {
            ...curScene,
            objects: curScene.objects.map((o) => {
              if (o.id === existingIHSeg.id) {
                return {
                  ...o,
                  perpendicular_witness: o.perpendicular_witness
                    ? { ...o.perpendicular_witness, marker: perpWitness.marker }
                    : perpWitness,
                };
              }
              if (existingFootPt && o.id === existingFootPt.id && o.perpendicular_witness) {
                return {
                  ...o,
                  perpendicular_witness: {
                    ...o.perpendicular_witness,
                    marker: perpWitness.marker,
                  },
                };
              }
              return o;
            }),
          };
        }
        continue;
      }

      const tanInserted: SceneObject[] = [];
      if (!existingFootPt) {
        tanInserted.push({
          id: hId,
          type: "point3",
          label: `Tiếp điểm ${symH}`,
          notation: symH,
          reference: symH,
          role: `Tiếp điểm của mặt cầu và mặt phẳng tiếp diện ${formatPlaneDisplayNotation(curPlane, curScene)}`,
          origin: "derived",
          authoritative: false,
          semantic_role: "AUXILIARY_CONSTRUCTION",
          producer: null,
          render: "point_marker",
          display_group: ["construction", "target", "sphere_plane_aux", "sphere_plane_tangent"],
          formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"],
          depends: [fromAnchorId, curPlane.id],
          source: { instruction: "EXPLANATORY_DERIVED_WITNESS" },
          xyz: dispH,
          perpendicular_witness: perpWitness,
        });
      }
      tanInserted.push({
        id: tanDistId,
        type: "segment3",
        label: `Bán kính tiếp điểm ${symI}${symH}`,
        notation: `${symI}${symH}`,
        reference: `${symI}${symH}`,
        role: `Bán kính nối tâm ${symI} tới tiếp điểm ${symH} vuông góc với ${formatPlaneDisplayNotation(curPlane, curScene)}`,
        origin: "derived",
        authoritative: false,
        semantic_role: "AUXILIARY_CONSTRUCTION",
        producer: null,
        render: "segment",
        display_group: ["construction", "target", "sphere_plane_aux", "sphere_plane_dist", "sphere_plane_tangent"],
        formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"],
        depends: [fromAnchorId, hId, curPlane.id],
        endpoint_ids: [fromAnchorId, hId],
        source: { instruction: "EXPLANATORY_DERIVED_WITNESS" },
        point_a: dispI,
        point_b: dispH,
        endpoints: [dispI, dispH],
        perpendicular_witness: perpWitness,
      });

      didExpand = true;
      const nextObjects = [...curScene.objects];
      const anchorIndices = [
        nextObjects.findIndex((o) => o.id === curBall.id),
        nextObjects.findIndex((o) => o.id === curPlane.id),
        existingFootPt ? nextObjects.findIndex((o) => o.id === existingFootPt.id) : -1,
      ];
      const insertAfterIdx = Math.max(...anchorIndices);
      nextObjects.splice(insertAfterIdx >= 0 ? insertAfterIdx + 1 : nextObjects.length, 0, ...tanInserted);

      const hasTypedEvents =
        curScene.events.length > 0
        && curScene.events.every((e, k) => Boolean(e.semantic_kind || curScene.formation?.steps[k]?.semantic_kind));
      const insertEvAt = tanEvIdx + 1;
      const splicedTanEvents: SceneEvent[] = tanInserted.map((insObj) => ({
        step_index: 0,
        action: "CREATE" as const,
        object: insObj.id,
        objects: [insObj.id],
        depends: insObj.depends ?? [],
        explanation: "",
        ...(hasTypedEvents ? { semantic_kind: "GEOMETRY_CONSTRUCTION" as const } : {}),
      }));
      const nextEvents: SceneEvent[] = [];
      for (let k = 0; k < curScene.events.length; k += 1) {
        if (k === insertEvAt) {
          for (const sev of splicedTanEvents) {
            nextEvents.push({ ...sev, step_index: nextEvents.length });
          }
        }
        nextEvents.push({ ...curScene.events[k], step_index: nextEvents.length });
      }
      if (insertEvAt >= curScene.events.length) {
        for (const sev of splicedTanEvents) {
          nextEvents.push({ ...sev, step_index: nextEvents.length });
        }
      }

      let nextFormation = curScene.formation;
      if (curScene.formation && curScene.formation.steps.length === curScene.events.length) {
        const origSteps = curScene.formation.steps;
        const refStep = origSteps[tanEvIdx];
        const allInsertedIds = tanInserted.map((x) => x.id);
        const rebuiltSteps: FormationStep[] = [];
        const appendSplicedSteps = () => {
          const accIds: string[] = [];
          for (const insObj of tanInserted) {
            accIds.push(insObj.id);
            rebuiltSteps.push({
              ...refStep,
              step_index: rebuiltSteps.length,
              visible_ids: [...new Set([...refStep.visible_ids, ...accIds])],
              readout_ids: [...refStep.readout_ids],
              focus_ids: [insObj.id],
              learner_text: insObj.label,
              semantic_kind: "GEOMETRY_CONSTRUCTION",
            });
          }
        };
        for (let k = 0; k < origSteps.length; k += 1) {
          if (k === insertEvAt) appendSplicedSteps();
          const st = origSteps[k];
          const vis = k >= insertEvAt ? [...new Set([...st.visible_ids, ...allInsertedIds])] : st.visible_ids;
          rebuiltSteps.push({ ...st, step_index: rebuiltSteps.length, visible_ids: vis });
        }
        if (insertEvAt >= origSteps.length) appendSplicedSteps();
        nextFormation = { steps: rebuiltSteps };
      }

      curScene = {
        ...curScene,
        objects: nextObjects,
        events: nextEvents,
        ...(nextFormation ? { formation: nextFormation } : {}),
      };
    }
  }

  // ── 2. Giao tuyến hai mặt phẳng: điểm chung thứ hai O = d₁ ∩ d₂ trên mặt đa giác chung ─────
  const interLines = curScene.objects.filter(
    (o) => !isSubEntity(o.id) && o.type === "line3" && isIntersectionLineOrSegment(o, curScene),
  );
  for (const ln of interLines) {
    if (curScene.objects.some((o) => o.id === `${ln.id}__pt2`)) continue;
    const exactById = new Map(exactRef.objects.map((o) => [o.id, o]));
    const curById = new Map(curScene.objects.map((o) => [o.id, o]));
    const exactLn = exactById.get(ln.id) ?? ln;
    if (!exactLn.point || !exactLn.direction) continue;
    const planeDeps = (exactLn.depends ?? ln.depends ?? [])
      .map((id) => exactById.get(id))
      .filter((p): p is SceneObject => Boolean(p && p.type === "plane3" && p.point && p.normal));
    if (planeDeps.length < 2) continue;

    const evIdx = curScene.events.findIndex(
      (ev) => ev.action === "CREATE" && (ev.object === ln.id || (ev.objects ?? []).includes(ln.id)),
    );
    if (evIdx < 0) continue;

    const lp0 = parseFracVec3(exactLn.point);
    const ldir = parseFracVec3(exactLn.direction);
    if (vIsZero(ldir)) continue;

    const existingOnLine = curScene.objects.filter((p) => {
      if (isSubEntity(p.id) || p.type !== "point3") return false;
      const ep = exactById.get(p.id) ?? p;
      return Boolean(ep.xyz && vIsZero(vCross(vSub(parseFracVec3(ep.xyz), lp0), ldir)));
    });
    if (existingOnLine.length >= 2) continue;

    // Kiểm tra xem đường giao tuyến có cắt một đa giác mặt/đáy đã dựng tại đúng một điểm hữu tỉ O ∈ Q³ không
    let pierceExact: FracVec3 | null = null;
    let chordRoleDesc = "Điểm chung thứ hai của hai mặt phẳng";
    let chordPointDeps: string[] = [];

    const facePolys = exactRef.objects.filter(
      (o) => !isSubEntity(o.id) && o.type === "polygon3" && (o.vertices?.length ?? 0) >= 3,
    );
    for (const poly of facePolys) {
      const fVerts = (poly.vertices ?? []).map(parseFracVec3);
      if (fVerts.length < 3) continue;
      const fn = vCross(vSub(fVerts[1], fVerts[0]), vSub(fVerts[2], fVerts[0]));
      if (vIsZero(fn)) continue;
      const denom = plainDotFrac(ldir, fn);
      if (fIsZero(denom)) continue;
      const numer = plainDotFrac(vSub(fVerts[0], lp0), fn);
      const tHit = normFrac(numer[0] * denom[1], numer[1] * denom[0]);
      const qExact: FracVec3 = [
        fAdd(lp0[0], fMul(tHit, ldir[0])),
        fAdd(lp0[1], fMul(tHit, ldir[1])),
        fAdd(lp0[2], fMul(tHit, ldir[2])),
      ];
      if (existingOnLine.some((epObj) => {
        const ep = exactById.get(epObj.id) ?? epObj;
        return Boolean(ep.xyz && vIsZero(vSub(parseFracVec3(ep.xyz), qExact)));
      })) {
        continue;
      }
      // Kiểm tra qExact nằm trong miền lồi của đa giác mặt
      let posSign = 0;
      let negSign = 0;
      for (let i = 0; i < fVerts.length; i += 1) {
        const e = vSub(fVerts[(i + 1) % fVerts.length], fVerts[i]);
        const c = vCross(e, vSub(qExact, fVerts[i]));
        const s = plainDotFrac(c, fn)[0];
        if (s > 0n) posSign += 1;
        else if (s < 0n) negSign += 1;
      }
      if (posSign > 0 && negSign > 0) continue;

      const vIds = poly.vertex_ids ?? poly.depends ?? [];
      const chordNames: string[] = [];
      const collectedPts: string[] = [];
      for (const mp of planeDeps.slice(0, 2)) {
        const mpN = parseFracVec3(mp.normal!);
        const mpP = parseFracVec3(mp.point!);
        const onChord = vIds
          .map((id) => ({ id, cur: curById.get(id), ex: exactById.get(id) }))
          .filter((item) => item.cur && item.ex?.xyz && fIsZero(plainDotFrac(vSub(parseFracVec3(item.ex.xyz), mpP), mpN)));
        if (onChord.length === 2) {
          chordNames.push(`${shortSym(onChord[0].cur!)}${shortSym(onChord[1].cur!)}`);
          collectedPts.push(onChord[0].id, onChord[1].id);
        }
      }
      pierceExact = qExact;
      if (chordNames.length === 2) {
        chordRoleDesc = `Giao điểm hai đường chéo ${chordNames[0]} và ${chordNames[1]}`;
        chordPointDeps = collectedPts;
      }
      break;
    }

    if (pierceExact) {
      didExpand = true;
      const symO = pickUnusedSym(curScene, ["O", "I", "E", "F"]);
      const dispO = mapExactVecToSceneFrame(pierceExact, chartT);
      const oId = `${ln.id}__pt2`;
      const oObj: SceneObject = {
        id: oId,
        type: "point3",
        label: `Điểm ${symO}`,
        notation: symO,
        reference: symO,
        role: chordRoleDesc,
        origin: "derived",
        authoritative: false,
        semantic_role: "AUXILIARY_CONSTRUCTION",
        producer: null,
        render: "point_marker",
        display_group: ["construction"],
        formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"],
        depends: [...new Set([planeDeps[0].id, planeDeps[1].id, ...chordPointDeps])],
        source: { instruction: "EXPLANATORY_DERIVED_WITNESS" },
        xyz: dispO,
      };
      const lnObjIdx = curScene.objects.findIndex((o) => o.id === ln.id);
      const nextObjects = [...curScene.objects];
      nextObjects.splice(lnObjIdx >= 0 ? lnObjIdx + 1 : nextObjects.length, 0, oObj);
      const nextEvents = curScene.events.map((ev, k) =>
        k === evIdx
          ? {
              ...ev,
              objects: [...new Set([ev.object ?? ln.id, ...(ev.objects ?? []), oId])],
            }
          : ev,
      );
      const nextFormation = curScene.formation
        ? {
            steps: curScene.formation.steps.map((st, k) =>
              k >= evIdx ? { ...st, visible_ids: [...new Set([...st.visible_ids, oId])] } : st,
            ),
          }
        : undefined;
      curScene = {
        ...curScene,
        objects: nextObjects,
        events: nextEvents,
        ...(nextFormation ? { formation: nextFormation } : {}),
      };
    }
  }

  // ── Helper chung cho chứng cứ khoảng cách / đoạn thẳng mục tiêu (Sections 3–5) ──────
  const pointLiesOnExactCarrier = (
    ptEx: FracVec3,
    carrierEx: SceneObject | undefined,
    exactMap: Map<string, SceneObject>,
  ): boolean => {
    if (!carrierEx) return false;
    if (carrierEx.type === "plane3" && carrierEx.point && carrierEx.normal) {
      const p0 = parseFracVec3(carrierEx.point);
      const nVec = parseFracVec3(carrierEx.normal);
      return !vIsZero(nVec) && fIsZero(plainDotFrac(vSub(ptEx, p0), nVec));
    }
    if (carrierEx.point && carrierEx.direction) {
      const lp = parseFracVec3(carrierEx.point);
      const ld = parseFracVec3(carrierEx.direction);
      return !vIsZero(ld) && vIsZero(vCross(vSub(ptEx, lp), ld));
    }
    if (carrierEx.point_a && carrierEx.point_b) {
      const pa = parseFracVec3(carrierEx.point_a);
      const pb = parseFracVec3(carrierEx.point_b);
      const d = vSub(pb, pa);
      return !vIsZero(d) && vIsZero(vCross(vSub(ptEx, pa), d));
    }
    const endPts = (carrierEx.depends ?? [])
      .map((id) => exactMap.get(id))
      .filter((p): p is SceneObject => Boolean(p && p.type === "point3" && p.xyz));
    if (endPts.length >= 2) {
      const pa = parseFracVec3(endPts[0].xyz!);
      const pb = parseFracVec3(endPts[1].xyz!);
      const d = vSub(pb, pa);
      return !vIsZero(d) && vIsZero(vCross(vSub(ptEx, pa), d));
    }
    return false;
  };

  const findCoincidentPointInScene = (
    sceneToSearch: Scene3D,
    exactCoord: FracVec3,
    exactMap: Map<string, SceneObject>,
  ): SceneObject | undefined =>
    sceneToSearch.objects.find((p) => {
      if (isSubEntity(p.id) || p.type !== "point3") return false;
      const ep = exactMap.get(p.id) ?? p;
      return Boolean(ep.xyz && vIsZero(vSub(parseFracVec3(ep.xyz), exactCoord)));
    });

  const hasExistingSegmentOrSolidEdge = (
    sceneToSearch: Scene3D,
    idA: string | null,
    idB: string | null,
    exactA: FracVec3,
    exactB: FracVec3,
    exactMap: Map<string, SceneObject>,
  ): boolean => {
    for (const o of sceneToSearch.objects) {
      if (isSubEntity(o.id)) continue;
      if (o.type === "segment3" || o.type === "line3") {
        if (idA && idB && (o.depends ?? []).length === 2 && o.depends!.includes(idA) && o.depends!.includes(idB)) {
          return true;
        }
        const eo = exactMap.get(o.id) ?? o;
        if (eo.point_a && eo.point_b) {
          const pa = parseFracVec3(eo.point_a);
          const pb = parseFracVec3(eo.point_b);
          if (
            (vIsZero(vSub(pa, exactA)) && vIsZero(vSub(pb, exactB)))
            || (vIsZero(vSub(pa, exactB)) && vIsZero(vSub(pb, exactA)))
          ) {
            return true;
          }
        }
      }
      if (o.type === "solid") {
        const es = exactMap.get(o.id) ?? o;
        const vIds = es.vertex_ids ?? o.vertex_ids ?? [];
        const verts = (es.vertices ?? []).map(parseFracVec3);
        for (const f of es.faces ?? o.faces ?? []) {
          for (let fi = 0; fi < f.length; fi += 1) {
            const i = f[fi];
            const j = f[(fi + 1) % f.length];
            if (idA && idB && ((vIds[i] === idA && vIds[j] === idB) || (vIds[i] === idB && vIds[j] === idA))) {
              return true;
            }
            if (
              verts[i]
              && verts[j]
              && (
                (vIsZero(vSub(verts[i], exactA)) && vIsZero(vSub(verts[j], exactB)))
                || (vIsZero(vSub(verts[i], exactB)) && vIsZero(vSub(verts[j], exactA)))
              )
            ) {
              return true;
            }
          }
        }
      }
    }
    return false;
  };

  const insertGoalWitnessEventBeforeMeasure = (
    qId: string,
    evIdx: number,
    inserted: SceneObject[],
    primarySegId: string,
    segDeps: string[],
    explanation: string,
  ): void => {
    didExpand = true;
    const insertedIds = inserted.map((x) => x.id);
    const qObjIdx = curScene.objects.findIndex((o) => o.id === qId);
    const nextObjects = [...curScene.objects];
    nextObjects.splice(qObjIdx >= 0 ? qObjIdx : nextObjects.length, 0, ...inserted);

    const hasTypedEvents =
      curScene.events.length > 0
      && curScene.events.every((e, k) => Boolean(e.semantic_kind || curScene.formation?.steps[k]?.semantic_kind));
    const createEv: SceneEvent = {
      step_index: evIdx,
      action: "CREATE",
      object: primarySegId,
      objects: insertedIds,
      depends: [...new Set(segDeps)],
      explanation,
      ...(hasTypedEvents ? { semantic_kind: "GEOMETRY_CONSTRUCTION" as const } : {}),
    };

    const nextEvents: SceneEvent[] = [];
    for (let k = 0; k < curScene.events.length; k += 1) {
      if (k === evIdx) {
        nextEvents.push({ ...createEv, step_index: nextEvents.length });
      }
      nextEvents.push({ ...curScene.events[k], step_index: nextEvents.length });
    }

    let nextFormation = curScene.formation;
    if (curScene.formation && curScene.formation.steps.length === curScene.events.length) {
      const origSteps = curScene.formation.steps;
      const refStep = evIdx > 0 ? origSteps[evIdx - 1] : origSteps[evIdx];
      const stepCreate: FormationStep = {
        ...refStep,
        step_index: evIdx,
        visible_ids: [...new Set([...refStep.visible_ids, ...insertedIds])],
        readout_ids: evIdx > 0 ? [...refStep.readout_ids] : [],
        focus_ids: [primarySegId, ...segDeps],
        learner_text: explanation,
        semantic_kind: "GEOMETRY_CONSTRUCTION",
      };
      const rebuiltSteps: FormationStep[] = [];
      for (let k = 0; k < origSteps.length; k += 1) {
        if (k === evIdx) {
          rebuiltSteps.push({ ...stepCreate, step_index: rebuiltSteps.length });
        }
        const st = origSteps[k];
        rebuiltSteps.push({
          ...st,
          step_index: rebuiltSteps.length,
          visible_ids: k >= evIdx ? [...new Set([...st.visible_ids, ...insertedIds])] : st.visible_ids,
        });
      }
      nextFormation = { steps: rebuiltSteps };
    }

    curScene = {
      ...curScene,
      objects: nextObjects,
      events: nextEvents,
      ...(nextFormation ? { formation: nextFormation } : {}),
    };
  };

  // ── 3. Đoạn vuông góc chung của hai đường thẳng chéo nhau (`common_perpendicular`) ────
  const commonPerpQuantities = curScene.objects.filter((o) => {
    if (isSubEntity(o.id) || o.type !== "quantity") return false;
    const w = o.annotation?.witness;
    return w?.relation === "common_perpendicular";
  });
  for (const q of commonPerpQuantities) {
    if (curScene.objects.some((o) => o.id === `${q.id}__perp_seg`)) continue;
    const exactMap = new Map(exactRef.objects.map((o) => [o.id, o]));
    const curMap = new Map(curScene.objects.map((o) => [o.id, o]));
    const exactQ = exactMap.get(q.id) ?? q;
    const wEx = exactQ.annotation?.witness;
    const wDisp = q.annotation?.witness;
    if (
      !wEx?.foot
      || !wEx.on
      || !wEx.marker?.u
      || !wEx.marker?.v
      || !wEx.second?.foot
      || !wEx.second?.on
      || !wEx.second?.marker?.u
      || !wEx.second?.marker?.v
      || !wDisp?.foot
      || !wDisp.second?.foot
    ) {
      continue;
    }

    const evIdx = curScene.events.findIndex((ev) => ev.action === "MEASURE" && ev.object === q.id);
    if (evIdx < 0) continue;

    const l1Ex = exactMap.get(wEx.on);
    const l2Ex = exactMap.get(wEx.second.on);
    const f1Ex = parseFracVec3(wEx.foot);
    const f2Ex = parseFracVec3(wEx.second.foot);
    const u1Ex = parseFracVec3(wEx.marker.u);
    const v1Ex = parseFracVec3(wEx.marker.v);
    const u2Ex = parseFracVec3(wEx.second.marker.u);
    const v2Ex = parseFracVec3(wEx.second.marker.v);
    const segVecEx = vSub(f2Ex, f1Ex);

    if (
      vIsZero(segVecEx)
      || vIsZero(u1Ex)
      || vIsZero(v1Ex)
      || vIsZero(u2Ex)
      || vIsZero(v2Ex)
      || !pointLiesOnExactCarrier(f1Ex, l1Ex, exactMap)
      || !pointLiesOnExactCarrier(f2Ex, l2Ex, exactMap)
      || !fIsZero(metricDot(u1Ex, v1Ex, exactRef.chart_metric))
      || !fIsZero(metricDot(u2Ex, v2Ex, exactRef.chart_metric))
      || !vParallel(segVecEx, v1Ex)
    ) {
      continue;
    }

    const l1Cur = curMap.get(wEx.on) ?? l1Ex!;
    const l2Cur = curMap.get(wEx.second.on) ?? l2Ex!;
    const existingF1 = findCoincidentPointInScene(curScene, f1Ex, exactMap);
    const existingF2 = findCoincidentPointInScene(curScene, f2Ex, exactMap);
    const sym1 = existingF1 ? shortSym(existingF1) : pickUnusedSym(curScene, ["H", "I", "P", "E"]);
    const usedAfter1 = new Set([
      ...curScene.objects.filter((o) => !isSubEntity(o.id)).map((o) => o.notation?.trim() ?? o.reference?.trim() ?? ""),
      sym1,
    ]);
    const sym2 = existingF2
      ? shortSym(existingF2)
      : (["K", "J", "Q", "F"].find((c) => !usedAfter1.has(c)) ?? "K′");

    const f1Id = existingF1?.id ?? `${q.id}__foot1`;
    const f2Id = existingF2?.id ?? `${q.id}__foot2`;
    const dispF1 = existingF1?.xyz ?? wDisp.foot ?? mapExactVecToSceneFrame(f1Ex, chartT);
    const dispF2 = existingF2?.xyz ?? wDisp.second.foot ?? mapExactVecToSceneFrame(f2Ex, chartT);

    const inserted: SceneObject[] = [];
    if (!existingF1) {
      inserted.push({
        id: f1Id,
        type: "point3",
        label: `Điểm ${sym1}`,
        notation: sym1,
        reference: sym1,
        role: `Chân đường vuông góc chung trên ${shortSym(l1Cur)}`,
        origin: "derived",
        authoritative: false,
        semantic_role: "AUXILIARY_CONSTRUCTION",
        producer: null,
        render: "point_marker",
        display_group: ["construction", "target"],
        formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"],
        depends: [...new Set([l1Cur.id, l2Cur.id, ...(l1Cur.depends ?? [])])],
        source: { instruction: "EXPLANATORY_DERIVED_WITNESS" },
        xyz: dispF1,
      });
    }
    if (!existingF2) {
      inserted.push({
        id: f2Id,
        type: "point3",
        label: `Điểm ${sym2}`,
        notation: sym2,
        reference: sym2,
        role: `Chân đường vuông góc chung trên ${shortSym(l2Cur)}`,
        origin: "derived",
        authoritative: false,
        semantic_role: "AUXILIARY_CONSTRUCTION",
        producer: null,
        render: "point_marker",
        display_group: ["construction", "target"],
        formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"],
        depends: [...new Set([l1Cur.id, l2Cur.id, ...(l2Cur.depends ?? [])])],
        source: { instruction: "EXPLANATORY_DERIVED_WITNESS" },
        xyz: dispF2,
      });
    }

    const segId = `${q.id}__perp_seg`;
    const segDeps = [f1Id, f2Id, l1Cur.id, l2Cur.id];
    const perpWitness: NonNullable<SceneObject["perpendicular_witness"]> = {
      ...wDisp,
      from: l2Cur.id,
      from_point: dispF2,
      on: l1Cur.id,
      foot: dispF1,
      foot_id: f1Id,
      relation: "common_perpendicular",
      can_present_as_proven: true,
      second: {
        ...wDisp.second,
        on: l2Cur.id,
        foot: dispF2,
        foot_id: f2Id,
      },
    };
    inserted.push({
      id: segId,
      type: "segment3",
      label: `Đoạn vuông góc chung ${sym1}${sym2}`,
      notation: `${sym1}${sym2}`,
      reference: `${sym1}${sym2}`,
      role: `Đoạn vuông góc chung của ${shortSym(l1Cur)} và ${shortSym(l2Cur)}`,
      origin: "derived",
      authoritative: false,
      semantic_role: "AUXILIARY_CONSTRUCTION",
      producer: null,
      render: "segment",
      display_group: ["construction", "target", "perp_witness"],
      formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"],
      depends: segDeps,
      endpoint_ids: [f1Id, f2Id],
      source: { instruction: "EXPLANATORY_DERIVED_WITNESS" },
      point_a: dispF1,
      point_b: dispF2,
      endpoints: [dispF1, dispF2],
      perpendicular_witness: perpWitness,
    });

    insertGoalWitnessEventBeforeMeasure(
      q.id,
      evIdx,
      inserted,
      segId,
      segDeps,
      `Dựng đoạn vuông góc chung ${sym1}${sym2} của ${shortSym(l1Cur)} và ${shortSym(l2Cur)}.`,
    );
  }

  // ── 4. Khoảng cách từ điểm đến mặt phẳng / đường thẳng có witness kiểm chứng ─────────
  const pointDistQuantities = curScene.objects.filter((o) => {
    if (isSubEntity(o.id) || o.type !== "quantity") return false;
    const w = o.annotation?.witness;
    return o.annotation?.kind === "distance" && Boolean(w && w.relation !== "common_perpendicular");
  });
  for (const q of pointDistQuantities) {
    if (curScene.objects.some((o) => o.id === `${q.id}__perp_seg`)) continue;
    const exactMap = new Map(exactRef.objects.map((o) => [o.id, o]));
    const curMap = new Map(curScene.objects.map((o) => [o.id, o]));
    const exactQ = exactMap.get(q.id) ?? q;
    const wEx = exactQ.annotation?.witness;
    const wDisp = q.annotation?.witness;
    if (!wEx?.from || !wEx.foot || !wEx.on || !wEx.marker?.u || !wEx.marker?.v || !wDisp?.foot) continue;

    const evIdx = curScene.events.findIndex((ev) => ev.action === "MEASURE" && ev.object === q.id);
    if (evIdx < 0) continue;

    const fromExObj = exactMap.get(wEx.from);
    const onExObj = exactMap.get(wEx.on);
    if (!fromExObj?.xyz || !onExObj) continue;

    const fromEx = parseFracVec3(fromExObj.xyz);
    const footEx = parseFracVec3(wEx.foot);
    const uEx = parseFracVec3(wEx.marker.u);
    const vEx = parseFracVec3(wEx.marker.v);
    const dropVecEx = vSub(fromEx, footEx);
    if (
      vIsZero(dropVecEx)
      || vIsZero(uEx)
      || vIsZero(vEx)
      || !pointLiesOnExactCarrier(footEx, onExObj, exactMap)
      || !fIsZero(metricDot(uEx, vEx, exactRef.chart_metric))
      || !vParallel(dropVecEx, vEx)
    ) {
      continue;
    }
    if (onExObj.type === "plane3" && onExObj.normal) {
      const basis = findRationalPlaneBasis(parseFracVec3(onExObj.normal));
      if (
        !basis
        || !fIsZero(metricDot(dropVecEx, basis[0], exactRef.chart_metric))
        || !fIsZero(metricDot(dropVecEx, basis[1], exactRef.chart_metric))
      ) {
        continue;
      }
    }

    const existingFoot = findCoincidentPointInScene(curScene, footEx, exactMap);
    if (hasExistingSegmentOrSolidEdge(curScene, wEx.from, existingFoot?.id ?? null, fromEx, footEx, exactMap)) {
      continue;
    }

    const fromCur = curMap.get(wEx.from) ?? fromExObj;
    const onCur = curMap.get(wEx.on) ?? onExObj;
    const footSym = existingFoot ? shortSym(existingFoot) : pickUnusedSym(curScene, ["H", "K", "I", "E"]);
    const footId = existingFoot?.id ?? `${q.id}__foot1`;
    const dispFrom = fromCur.xyz ?? mapExactVecToSceneFrame(fromEx, chartT);
    const dispFoot = existingFoot?.xyz ?? wDisp.foot ?? mapExactVecToSceneFrame(footEx, chartT);
    const onName = onCur.type === "plane3" ? formatPlaneDisplayNotation(onCur) : shortSym(onCur);

    const perpWitness: NonNullable<SceneObject["perpendicular_witness"]> = {
      ...wDisp,
      from: fromCur.id,
      from_point: dispFrom,
      on: onCur.id,
      foot: dispFoot,
      foot_id: footId,
      relation: onCur.type === "plane3" ? "line_perp_plane" : (wDisp.relation ?? "line_perp_line"),
      can_present_as_proven: true,
    };

    const inserted: SceneObject[] = [];
    if (!existingFoot) {
      inserted.push({
        id: footId,
        type: "point3",
        label: `Điểm ${footSym}`,
        notation: footSym,
        reference: footSym,
        role: `Hình chiếu vuông góc của ${shortSym(fromCur)} trên ${onName}`,
        origin: "derived",
        authoritative: false,
        semantic_role: "AUXILIARY_CONSTRUCTION",
        producer: null,
        render: "point_marker",
        display_group: ["construction", "target"],
        formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"],
        depends: [...new Set([fromCur.id, onCur.id, ...(onCur.depends ?? [])])],
        source: { instruction: "EXPLANATORY_DERIVED_WITNESS" },
        xyz: dispFoot,
        perpendicular_witness: perpWitness,
      });
    }

    const segId = `${q.id}__perp_seg`;
    const segDeps = [...new Set([fromCur.id, footId, onCur.id, ...(onCur.depends ?? [])])];
    inserted.push({
      id: segId,
      type: "segment3",
      label: `Đoạn vuông góc ${shortSym(fromCur)}${footSym}`,
      notation: `${shortSym(fromCur)}${footSym}`,
      reference: `${shortSym(fromCur)}${footSym}`,
      role: `Đoạn vuông góc hạ từ ${shortSym(fromCur)} đến ${onName} tại ${footSym}`,
      origin: "derived",
      authoritative: false,
      semantic_role: "AUXILIARY_CONSTRUCTION",
      producer: null,
      render: "segment",
      display_group: ["construction", "target", "perp_witness"],
      formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"],
      depends: segDeps,
      endpoint_ids: [fromCur.id, footId],
      source: { instruction: "EXPLANATORY_DERIVED_WITNESS" },
      point_a: dispFrom,
      point_b: dispFoot,
      endpoints: [dispFrom, dispFoot],
      perpendicular_witness: perpWitness,
    });

    insertGoalWitnessEventBeforeMeasure(
      q.id,
      evIdx,
      inserted,
      segId,
      segDeps,
      `Hạ đoạn vuông góc ${shortSym(fromCur)}${footSym} ⊥ ${onName} tại ${footSym}.`,
    );
  }

  // ── 5. Đoạn thẳng mục tiêu chưa được nối cho goal `length` (vd `MG`, `SK`, `SH`) ──────
  const lengthGoalQuantities = curScene.objects.filter(
    (o) =>
      !isSubEntity(o.id)
      && o.type === "quantity"
      && o.origin !== "free"
      && o.annotation?.kind === "length"
      && o.annotation?.role !== "intermediate"
      && o.annotation?.category !== "measurement",
  );
  for (const q of lengthGoalQuantities) {
    if (curScene.objects.some((o) => o.id === `${q.id}__target_seg`)) continue;
    const exactMap = new Map(exactRef.objects.map((o) => [o.id, o]));
    const curMap = new Map(curScene.objects.map((o) => [o.id, o]));
    const exactQ = exactMap.get(q.id) ?? q;
    const rawSubjIds = exactQ.annotation?.subject_ids ?? q.annotation?.subject_ids ?? q.depends ?? [];
    const ptPairs = rawSubjIds
      .map((id) => ({ id, cur: curMap.get(id), ex: exactMap.get(id) ?? curMap.get(id) }))
      .filter((x): x is { id: string; cur: SceneObject; ex: SceneObject } =>
        Boolean(x.cur && x.ex && x.ex.type === "point3" && x.ex.xyz && x.cur.xyz),
      );
    if (ptPairs.length !== 2) continue;

    const evIdx = curScene.events.findIndex((ev) => ev.action === "MEASURE" && ev.object === q.id);
    if (evIdx < 0) continue;

    const [pA, pB] = ptPairs;
    const exA = parseFracVec3(pA.ex.xyz!);
    const exB = parseFracVec3(pB.ex.xyz!);
    if (vIsZero(vSub(exB, exA))) continue;
    if (hasExistingSegmentOrSolidEdge(curScene, pA.id, pB.id, exA, exB, exactMap)) continue;

    // Kế thừa `perpendicular_witness` CHỈ KHI một đầu mút chính là chân hình chiếu vuông góc từ đầu mút kia (`w.from === other.id`, vd `SH ⊥ BC`)
    let inheritedWitness: SceneObject["perpendicular_witness"] | undefined;
    if (pB.cur.perpendicular_witness?.from === pA.id && pB.cur.perpendicular_witness.marker?.v) {
      inheritedWitness = {
        ...pB.cur.perpendicular_witness,
        foot_id: pB.id,
      };
    } else if (pA.cur.perpendicular_witness?.from === pB.id && pA.cur.perpendicular_witness.marker?.v) {
      inheritedWitness = {
        ...pA.cur.perpendicular_witness,
        foot_id: pA.id,
      };
    }

    const segSym = `${shortSym(pA.cur)}${shortSym(pB.cur)}`;
    const segId = `${q.id}__target_seg`;
    const segDeps = [pA.id, pB.id];
    const segObj: SceneObject = {
      id: segId,
      type: "segment3",
      label: `Đoạn thẳng ${segSym}`,
      notation: segSym,
      reference: segSym,
      role: `Đoạn thẳng mục tiêu nối ${shortSym(pA.cur)} và ${shortSym(pB.cur)}`,
      origin: "derived",
      authoritative: false,
      semantic_role: "AUXILIARY_CONSTRUCTION",
      producer: null,
      render: "segment",
      display_group: ["construction", "target", "goal_segment"],
      formation_roles: ["CONSTRUCT_AUXILIARY_GEOMETRY"],
      depends: segDeps,
      endpoint_ids: [pA.id, pB.id],
      source: { instruction: "EXPLANATORY_DERIVED_WITNESS" },
      point_a: pA.cur.xyz!,
      point_b: pB.cur.xyz!,
      endpoints: [pA.cur.xyz!, pB.cur.xyz!],
      ...(inheritedWitness ? { perpendicular_witness: inheritedWitness } : {}),
    };

    insertGoalWitnessEventBeforeMeasure(
      q.id,
      evIdx,
      [segObj],
      segId,
      segDeps,
      `Nối đoạn thẳng mục tiêu ${segSym}.`,
    );
  }

  return { scene: curScene, didExpand };
}

/**
 * Xây dựng kế hoạch dựng hình sư phạm tổng quát dựa trên đồ thị phụ thuộc tôpô (DAG, §3):
 * - Tách biệt thứ tự thực thi của Engine/Planner với thứ tự giảng dạy cho học sinh:
 *   không có đối tượng nào xuất hiện hoặc được sử dụng trước khi các đối tượng tiên quyết (đáy, khối mang cạnh,
 *   đỉnh, mặt phẳng cắt) được dựng.
 * - Nhóm các thao tác kỹ thuật (đường mang phụ dùng một lần, cạnh bên đi liền khép kín khối, mặt phẳng trùng mặt khối,
 *   các đoạn `EXTEND` giao tuyến trên từng mặt) thành các bước có ý nghĩa sư phạm rõ ràng.
 * - Gắn đầy đủ 7 trường siêu dữ liệu sư phạm trên mỗi `PedagogicalStepItem`.
 */
export function buildPedagogicalConstructionPlan(
  rawScene: Scene3D,
  options?: { splitBundledHeight?: boolean },
): PedagogicalConstructionPlan {
  const splitHeight = options?.splitBundledHeight ?? true;
  const targetCache = splitHeight ? _pedPlanCache : _pedPlanNoSplitCache;
  const currentHybrid = hybridViewOfScene(rawScene);
  const rawSig = sceneCacheSignature(rawScene);
  const cached = targetCache.get(rawScene);
  if (cached && cached.hybrid === currentHybrid && cached.sig === rawSig) return cached.plan;

  const rawExactOrigin = exactSceneOriginOf(rawScene);
  const normalizeCurvedApexObjects = (objs: SceneObject[]): { objects: SceneObject[]; changed: boolean } => {
    let changed = false;
    const mapped = objs.map((o) => {
      if (o.type === "curved_solid" && !o.apex_or_top) {
        const legacyApex = (o as SceneObject & { apex?: ExactVec3 | null }).apex;
        if (legacyApex) {
          changed = true;
          return { ...o, apex_or_top: legacyApex };
        }
      }
      return o;
    });
    return { objects: changed ? mapped : objs, changed };
  };
  const hadSubEntities = rawScene.objects.some((o) => isSubEntity(o.id));
  const filteredObjs = hadSubEntities
    ? rawScene.objects.filter((o) => !isSubEntity(o.id))
    : rawScene.objects;
  const { objects: normObjs, changed: didNormalizeCurvedApex } = normalizeCurvedApexObjects(filteredObjs);
  const normIdSet = new Set(normObjs.map((o) => o.id));
  const hasStaleFormation = Boolean(
    rawScene.formation
    && rawScene.events.some(
      (ev, k) =>
        ev.action === "CREATE"
        && typeof ev.object === "string"
        && normIdSet.has(ev.object)
        && !(rawScene.formation!.steps[k]?.visible_ids ?? []).includes(ev.object),
    ),
  );
  const cleanInput: Scene3D = hadSubEntities || didNormalizeCurvedApex || hasStaleFormation
    ? {
        ...rawScene,
        objects: normObjs,
        ...(hasStaleFormation ? { formation: undefined } : {}),
      }
    : rawScene;
  const hasRegisteredOrigin = rawExactOrigin !== rawScene || didNormalizeCurvedApex || hasStaleFormation;
  propagateSceneLineage(cleanInput, rawScene);
  if (hasRegisteredOrigin && cleanInput !== rawScene) {
    const exactFiltered = hadSubEntities
      ? rawExactOrigin.objects.filter((o) => !isSubEntity(o.id))
      : rawExactOrigin.objects;
    const { objects: normExactObjs, changed: exactChanged } = normalizeCurvedApexObjects(exactFiltered);
    registerExactSceneOrigin(
      cleanInput,
      hadSubEntities || exactChanged || hasStaleFormation
        ? {
            ...rawExactOrigin,
            objects: normExactObjs,
            ...(hasStaleFormation ? { formation: undefined } : {}),
          }
        : rawExactOrigin,
    );
  }

  if (cleanInput.events.length === 0) {
    const emptyPlan: PedagogicalConstructionPlan = {
      scene: rawScene,
      steps: [],
      dagEdges: [],
      reordered: false,
      goalCompletion: buildGoalCompletionSummary(rawScene, []),
    };
    targetCache.set(rawScene, { plan: emptyPlan, hybrid: currentHybrid, sig: rawSig });
    return emptyPlan;
  }

  // Bước N1: Triển khai nền tảng khối nguyên khối (đa diện + tròn xoay) và tách đường cao có nhân chứng vuông góc
  const { scene: polyScene, didExpand: didExpandPoly } = splitHeight
    ? expandPrimaryPolyhedralFoundation(cleanInput)
    : { scene: cleanInput, didExpand: false };
  propagateSceneLineage(polyScene, cleanInput);
  if (hasRegisteredOrigin && polyScene !== cleanInput) {
    const prevExact = exactSceneOriginOf(cleanInput);
    const exactPoly = expandPrimaryPolyhedralFoundation(prevExact);
    registerExactSceneOrigin(polyScene, exactPoly.scene);
  }
  const { scene: heightSplitScene, didSplit: didSplitHeight } = splitHeight
    ? splitBundledCertifiedHeight(polyScene)
    : { scene: polyScene, didSplit: false };
  propagateSceneLineage(heightSplitScene, polyScene);
  if (hasRegisteredOrigin && heightSplitScene !== polyScene) {
    const prevExact = exactSceneOriginOf(polyScene);
    const exactSplit = splitBundledCertifiedHeight(prevExact);
    registerExactSceneOrigin(heightSplitScene, exactSplit.scene);
  }
  const { scene: curvedScene, didExpand: didExpandCurved } = splitHeight
    ? expandPrimaryCurvedFoundation(heightSplitScene)
    : { scene: heightSplitScene, didExpand: false };
  propagateSceneLineage(curvedScene, heightSplitScene);
  if (hasRegisteredOrigin && curvedScene !== heightSplitScene) {
    const prevExact = exactSceneOriginOf(heightSplitScene);
    const exactExpanded = expandPrimaryCurvedFoundation(prevExact);
    registerExactSceneOrigin(curvedScene, exactExpanded.scene);
  }
  const { scene: workScene, didExpand: didExpandExplanatory } = splitHeight
    ? expandVerifiedExplanatoryRelations(curvedScene)
    : { scene: curvedScene, didExpand: false };
  const didSplit =
    didNormalizeCurvedApex || didExpandPoly || didSplitHeight || didExpandCurved || didExpandExplanatory;
  propagateSceneLineage(workScene, curvedScene);
  if (hasRegisteredOrigin && workScene !== curvedScene) {
    const prevExact = exactSceneOriginOf(curvedScene);
    const exactRel = expandVerifiedExplanatoryRelations(prevExact);
    registerExactSceneOrigin(workScene, exactRel.scene);
  }
  const rawSteps = geometryTimeline(workScene);
  if (rawSteps.length === 0) {
    const emptyPlan: PedagogicalConstructionPlan = {
      scene: rawScene,
      steps: [],
      dagEdges: [],
      reordered: false,
      goalCompletion: buildGoalCompletionSummary(rawScene, []),
    };
    targetCache.set(rawScene, { plan: emptyPlan, hybrid: currentHybrid, sig: rawSig });
    return emptyPlan;
  }

  const byId = new Map(workScene.objects.map((o) => [o.id, o]));
  const phu = auxiliaryObjects(workScene);
  const workMeasOnlyIds = measurementOnlyPlanes(workScene);

  const hasDerivedVisualStepAfterInit = rawSteps.slice(1).some((rs) =>
    rs.construction.some((ek) => {
      const ev = workScene.events[ek];
      if (!ev || ev.action === "INIT" || ev.action === "MEASURE") return false;
      const t = ev.object ? byId.get(ev.object) : undefined;
      return Boolean(
        !t
        || (t.type !== "quantity"
          && t.render !== "readout"
          && t.render !== "non_visual"
          && !workMeasOnlyIds.has(t.id)),
      );
    }),
  );
  const dropInit = rawSteps.length >= 2
    && hasDerivedVisualStepAfterInit
    && rawSteps[0].construction.length > 0
    && rawSteps[0].construction.every((k) => workScene.events[k]?.action === "INIT");
  const initEventIndices = dropInit
    ? Array.from({ length: rawSteps[0].end - rawSteps[0].start + 1 }, (_, off) => rawSteps[0].start + off)
    : [];
  const baseSteps = dropInit ? rawSteps.slice(1) : rawSteps.slice();

  const createdVisualIdsAtBase = (gIdx: number): string[] => {
    const g = baseSteps[gIdx];
    const prevAnchor = gIdx > 0
      ? baseSteps[gIdx - 1].anchor
      : dropInit
        ? rawSteps[0].anchor
        : -1;
    const prevSet = prevAnchor >= 0
      ? new Set(objectsAt(workScene, prevAnchor).map((o) => o.id))
      : new Set<string>();
    return objectsAt(workScene, g.anchor)
      .filter((o) => o.render !== "readout" && o.render !== "non_visual" && !prevSet.has(o.id))
      .map((o) => o.id);
  };

  interface PedagogicalUnit {
    origOrder: number;
    eventIndices: number[];
    createdVisualIds: string[];
    absorbedAuxIds: string[];
    extendSectionId: string | null;
    closeSectionId: string | null;
    conclusionQuantityIds: string[];
    hasMeasurementOrResult: boolean;
  }

  const rangeIndices = (start: number, end: number): number[] =>
    Array.from({ length: end - start + 1 }, (_, off) => start + off);

  const exactOriginForPlan = exactSceneOriginOf(workScene);
  const exactOriginById = new Map(exactOriginForPlan.objects.map((x) => [x.id, x]));

  const foundationRoleForCurved = (o: SceneObject): { hostId: string; stage: number } | null => {
    if (o.type === "curved_solid" && o.curved_kind === "ball" && isPrimaryCurvedSolid(workScene, o)) {
      return { hostId: o.id, stage: 1 };
    }
    if (o.type === "point3" && (o.display_group ?? []).includes("sphere_foundation_ref")) {
      const host = workScene.objects.find(
        (cand) => cand.type === "curved_solid" && cand.curved_kind === "ball" && o.id === `${cand.id}__ref_pt`,
      );
      if (host && isPrimaryCurvedSolid(workScene, host)) {
        return { hostId: host.id, stage: 1 };
      }
    }
    if (o.type === "circle3") {
      const host = hostCurvedSolidForBaseCircle(workScene, o);
      if (!host || !isPrimaryCurvedSolid(workScene, host)) return null;
      if (host.curved_kind === "cylinder") {
        const exHost = exactOriginById.get(host.id) ?? host;
        const exCircle = exactOriginById.get(o.id) ?? o;
        const isTop =
          Boolean(exHost.apex_or_top && exCircle.center)
          && vIsZero(vSub(parseFracVec3(exCircle.center!), parseFracVec3(exHost.apex_or_top!)));
        return { hostId: host.id, stage: isTop ? 2 : 1 };
      }
      return { hostId: host.id, stage: 1 };
    }
    if (o.type === "segment3") {
      const cRole = classifyCurvedSegmentRole(workScene, o);
      if (!cRole || !isPrimaryCurvedSolid(workScene, cRole.host)) return null;
      const host = cRole.host;
      if (cRole.kind === "radius") {
        const endpointRefs = [...new Set([...(o.endpoint_ids ?? []), ...(o.depends ?? [])])];
        const dependsOnCutOrProjection =
          Boolean(o.perpendicular_witness)
          || endpointRefs.some((dId) => {
            const dep = byId.get(dId);
            if (!dep) return false;
            if (dep.type === "plane3" || dep.type === "section" || vaiTroMien(dep) === "section") {
              return true;
            }
            if (dep.type === "point3" && dep.origin === "derived") {
              const prod = String(dep.producer ?? "");
              if (
                Boolean(dep.perpendicular_witness)
                || prod.includes("project")
                || prod.includes("foot")
                || prod.includes("intersect")
                || (dep.depends ?? []).some((subId) => {
                  const sub = byId.get(subId);
                  return Boolean(sub && (sub.type === "plane3" || sub.type === "section" || vaiTroMien(sub) === "section"));
                })
              ) {
                return true;
              }
            }
            return false;
          });
        if (dependsOnCutOrProjection) return null;
        if (host.curved_kind === "cylinder") {
          const exHost = exactOriginById.get(host.id) ?? host;
          const touchesTop =
            Boolean(exHost.apex_or_top)
            && (o.depends ?? []).some((dId) => {
              const ep = exactOriginById.get(dId) ?? byId.get(dId);
              return Boolean(ep?.xyz && vIsZero(vSub(parseFracVec3(ep.xyz), parseFracVec3(exHost.apex_or_top!))));
            });
          return { hostId: host.id, stage: touchesTop ? 2 : 1 };
        }
        return { hostId: host.id, stage: 1 };
      }
      if (cRole.kind === "axis" || cRole.kind === "center_line") {
        return { hostId: host.id, stage: 2 };
      }
      if (cRole.kind === "generator") {
        const deps = o.depends ?? [];
        const allFreeEndpoints =
          deps.length >= 2 && deps.every((dId) => byId.get(dId)?.origin === "free");
        if (allFreeEndpoints) {
          return { hostId: host.id, stage: 3 };
        }
      }
    }
    return null;
  };

  const isSecondaryCurvedSolidObj = (o: SceneObject): boolean =>
    isSecondaryCutCurvedSolid(workScene, o);

  const unitCreatesGoalWitnessOrSection = (ids: string[]): boolean =>
    ids.some((id) => {
      const o = byId.get(id);
      if (!o) return false;
      const srcInst = (o.source as Record<string, unknown> | undefined)?.instruction;
      if (
        isExplanatoryPerpSegment(o)
        || isExplanatoryTargetSegment(o)
        || (srcInst === "EXPLANATORY_DERIVED_WITNESS" && o.type === "segment3" && Boolean(o.perpendicular_witness))
        || o.type === "section"
        || ((o.type === "circle3" || o.type === "ellipse3" || o.type === "polygon3") && vaiTroMien(o) === "section")
        || (o.type === "point3" && Boolean(o.perpendicular_witness))
      ) {
        return true;
      }
      return isSecondaryCurvedSolidObj(o);
    });

  // Bước N2: Phân hoạch thành các đơn vị dựng hình sư phạm nguyên tử
  const finalWorkAnchor = Math.max(0, workScene.events.length - 1);
  const isInterCarrierDupPlaneId = (id: string): boolean => {
    const o = byId.get(id);
    if (!o || o.type !== "plane3" || !isDuplicateOfSolidFace(workScene, o)) return false;
    return workScene.objects.some(
      (x) => !isSubEntity(x.id) && isIntersectionLineOrSegment(x, workScene) && (x.depends ?? []).includes(id),
    );
  };
  const isDupFacePlaneId = (id: string): boolean => {
    const o = byId.get(id);
    return Boolean(
      o
      && o.type === "plane3"
      && !isInterCarrierDupPlaneId(id)
      && resolvePlaneSectionVisibility(workScene, o, finalWorkAnchor, false, null).subRole === "SOLID_FACE_DUPLICATE_PLANE",
    );
  };
  const preUnits: PedagogicalUnit[] = [];
  let idx = 0;
  while (idx < baseSteps.length) {
    const cur = baseSteps[idx];
    const curNew = createdVisualIdsAtBase(idx);
    const fullEvIndices = rangeIndices(cur.start, cur.end);

    // Tách sự kiện tính đại lượng / kết luận góc mục tiêu (`MEASURE` ở cuối bước) theo provenance phụ thuộc
    let trailingTargetMeasEvs: number[] = [];
    let trailingTargetQIds: string[] = [];
    let headAndInterEvs: number[] | null = null;
    {
      let cursor = fullEvIndices.length;
      const revTargetEvs: number[] = [];
      const revInterEvs: number[] = [];
      const revTargetQs: string[] = [];
      while (cursor > 0) {
        const evK = fullEvIndices[cursor - 1];
        const ev = workScene.events[evK];
        if (!ev || ev.action !== "MEASURE" || !ev.object) break;
        const q = byId.get(ev.object);
        if (!q || q.type !== "quantity") break;
        const isTarget =
          q.origin !== "free"
          && q.annotation?.role !== "intermediate"
          && q.annotation?.category !== "measurement";
        if (isTarget) {
          revTargetEvs.push(evK);
          revTargetQs.push(q.id);
        } else {
          revInterEvs.push(evK);
        }
        cursor -= 1;
      }
      if (revTargetQs.length > 0) {
        const candidateMainEvs = [...fullEvIndices.slice(0, cursor), ...revInterEvs.slice().reverse()];
        const targetEvs = revTargetEvs.slice().reverse();
        const targetQIds = revTargetQs.slice().reverse();
        const targetQObjs = targetQIds.map((id) => byId.get(id)).filter((o): o is SceneObject => Boolean(o));
        const hasAngleGoal = targetQObjs.some(
          (q) => q.annotation?.kind === "angle" || /\bgóc\s+giữa\b/iu.test(q.label ?? ""),
        );
        if (candidateMainEvs.length === 0 && curNew.length === 0) {
          const prevU = preUnits[preUnits.length - 1];
          const prevHasAngle = prevU?.conclusionQuantityIds.some((id) => {
            const pq = byId.get(id);
            return Boolean(pq && (pq.annotation?.kind === "angle" || /\bgóc\s+giữa\b/iu.test(pq.label ?? "")));
          }) ?? false;
          if (!hasAngleGoal && prevU && prevU.conclusionQuantityIds.length > 0 && !prevHasAngle) {
            prevU.eventIndices.push(...fullEvIndices);
            prevU.conclusionQuantityIds.push(...targetQIds);
            idx += 1;
            continue;
          }
          preUnits.push({
            origOrder: preUnits.length,
            eventIndices: fullEvIndices,
            createdVisualIds: [],
            absorbedAuxIds: [],
            extendSectionId: null,
            closeSectionId: null,
            conclusionQuantityIds: targetQIds,
            hasMeasurementOrResult: true,
          });
          idx += 1;
          continue;
        }

        const curNewSet = new Set(curNew);
        const mainCreatesPrimarySolid = curNew.some((id) => {
          const o = byId.get(id);
          if (!o) return false;
          if (o.type === "solid") return true;
          return o.type === "curved_solid" && !isSecondaryCurvedSolidObj(o);
        });
        const nonDupCurNew = curNew.filter((id) => !isDupFacePlaneId(id) && !workMeasOnlyIds.has(id));
        const isNonVisualOrDupOnly = nonDupCurNew.length === 0;
        const mainIsCurvedFoundation =
          nonDupCurNew.length > 0
          && nonDupCurNew.every((id) => {
            const o = byId.get(id);
            return Boolean(o && foundationRoleForCurved(o));
          });
        const hasExternalDerivedDep =
          splitHeight
          && !unitCreatesGoalWitnessOrSection(curNew)
          && targetQObjs.some((q) =>
            [...(q.depends ?? []), ...(q.annotation?.subject_ids ?? [])].some((depId) => {
              if (curNewSet.has(depId)) return false;
              const depObj = byId.get(depId);
              return Boolean(depObj && depObj.origin !== "free");
            }),
          );
        const prevUForSplit = preUnits[preUnits.length - 1];
        const prevCreatesPrimarySolidForSplit = prevUForSplit?.createdVisualIds.some((id) => {
          const po = byId.get(id);
          return Boolean(po && (po.type === "solid" || (po.type === "curved_solid" && !isSecondaryCurvedSolidObj(po))));
        }) ?? false;
        const shouldSplitTrailingMeas = splitHeight
          ? (hasAngleGoal || mainCreatesPrimarySolid || mainIsCurvedFoundation || isNonVisualOrDupOnly || hasExternalDerivedDep)
          : (mainCreatesPrimarySolid || (isNonVisualOrDupOnly && prevCreatesPrimarySolidForSplit));
        if (shouldSplitTrailingMeas) {
          trailingTargetMeasEvs = targetEvs;
          trailingTargetQIds = targetQIds;
          headAndInterEvs = candidateMainEvs;
        }
      }
    }
    const mainEvIndices = headAndInterEvs ?? fullEvIndices;
    const pushTrailingConclusionUnitIfAny = () => {
      if (trailingTargetMeasEvs.length > 0 && trailingTargetQIds.length > 0) {
        preUnits.push({
          origOrder: preUnits.length,
          eventIndices: trailingTargetMeasEvs,
          createdVisualIds: [],
          absorbedAuxIds: [],
          extendSectionId: null,
          closeSectionId: null,
          conclusionQuantityIds: trailingTargetQIds,
          hasMeasurementOrResult: true,
        });
      }
    };

    const isIntrinsicCapOrDupPlane = curNew.length > 0 && curNew.every(isDupFacePlaneId);
    const isMeasOnlyHelper =
      curNew.length === 0
      && preUnits.length > 0
      && mainEvIndices.length > 0
      && mainEvIndices.every((k) => {
        const ev = workScene.events[k];
        if (!ev) return true;
        if (ev.action === "MEASURE") return true;
        const target = ev.object ? byId.get(ev.object) : undefined;
        return Boolean(
          target
          && (target.render === "readout" || target.render === "non_visual" || workMeasOnlyIds.has(target.id) || isDupFacePlaneId(target.id)),
        );
      });
    const isNonVisualReadoutOnly =
      curNew.length === 0
      && preUnits.length > 0
      && cur.construction.every((k) => {
        const ev = workScene.events[k];
        if (!ev) return true;
        const target = ev.object ? byId.get(ev.object) : undefined;
        return Boolean(target && (target.render === "readout" || target.render === "non_visual"));
      });
    if ((isIntrinsicCapOrDupPlane || isNonVisualReadoutOnly || isMeasOnlyHelper) && preUnits.length > 0) {
      const hasQtyMeas = [...cur.solution, ...cur.results].some((k) => {
        const oid = workScene.events[k]?.object;
        return oid ? byId.get(oid)?.type === "quantity" : false;
      });
      const prevU = preUnits[preUnits.length - 1];
      prevU.eventIndices.push(...mainEvIndices);
      prevU.createdVisualIds.push(...curNew);
      prevU.hasMeasurementOrResult = prevU.hasMeasurementOrResult || hasQtyMeas;
      pushTrailingConclusionUnitIfAny();
      idx += 1;
      continue;
    }

    // Gộp các mặt phẳng mang giao tuyến trùng mặt bên liên tiếp (như `(SAB)`, `(SCD)`) thành 1 bước chuẩn bị trước khi dựng giao tuyến
    if (curNew.length > 0 && curNew.every(isInterCarrierDupPlaneId) && preUnits.length > 0) {
      const prevU = preUnits[preUnits.length - 1];
      if (
        prevU.conclusionQuantityIds.length === 0
        && !prevU.extendSectionId
        && !prevU.closeSectionId
        && prevU.createdVisualIds.length > 0
        && prevU.createdVisualIds.every(isInterCarrierDupPlaneId)
      ) {
        prevU.eventIndices.push(...mainEvIndices);
        prevU.createdVisualIds.push(...curNew);
        pushTrailingConclusionUnitIfAny();
        idx += 1;
        continue;
      }
    }

    // Gộp các bước cạnh bên liên tiếp (`CONSTRUCT_LATERAL_BOUNDARY`) thành 1 bước bộ khung cạnh bên, tách riêng với bước khép kín mặt khối (`solid`)
    const isPureLateralEdges = curNew.length > 0 && curNew.every((id) => {
      const o = byId.get(id);
      const roles = o?.formation_roles ?? [];
      return o?.type === "segment3" && roles.includes("CONSTRUCT_LATERAL_BOUNDARY") && !roles.includes("CONSTRUCT_HEIGHT");
    });
    if (isPureLateralEdges && preUnits.length > 0) {
      const prevU = preUnits[preUnits.length - 1];
      const prevIsPureLateral =
        prevU.conclusionQuantityIds.length === 0
        && !prevU.extendSectionId
        && !prevU.closeSectionId
        && prevU.createdVisualIds.length > 0
        && prevU.createdVisualIds.every((id) => {
          const po = byId.get(id);
          const pr = po?.formation_roles ?? [];
          return po?.type === "segment3" && pr.includes("CONSTRUCT_LATERAL_BOUNDARY") && !pr.includes("CONSTRUCT_HEIGHT");
        });
      if (prevIsPureLateral) {
        const hasQtyMeas = [...cur.solution, ...cur.results].some((k) => {
          const oid = workScene.events[k]?.object;
          return oid ? byId.get(oid)?.type === "quantity" : false;
        });
        prevU.eventIndices.push(...mainEvIndices);
        prevU.createdVisualIds.push(...curNew);
        prevU.hasMeasurementOrResult = prevU.hasMeasurementOrResult || (trailingTargetQIds.length === 0 && hasQtyMeas);
        pushTrailingConclusionUnitIfAny();
        idx += 1;
        continue;
      }
    }

    const extendSecId = (() => {
      const evs = cur.construction.map((k) => workScene.events[k]).filter(Boolean);
      if (evs.length === 0 || !evs.every((e) => e.action === "EXTEND" && e.object)) return null;
      const objId = evs[0].object!;
      return evs.every((e) => e.object === objId) && byId.get(objId)?.type === "section" ? objId : null;
    })();
    if (extendSecId && trailingTargetMeasEvs.length === 0) {
      let j = idx;
      const evIdxs: number[] = [];
      const visIds: string[] = [];
      let hasMeas = false;
      while (j < baseSteps.length) {
        const sj = baseSteps[j];
        const sjEvs = sj.construction.map((k) => workScene.events[k]).filter(Boolean);
        if (j === idx || (sjEvs.length > 0 && sjEvs.every((e) => e.action === "EXTEND" && e.object === extendSecId))) {
          evIdxs.push(...rangeIndices(sj.start, sj.end));
          visIds.push(...createdVisualIdsAtBase(j));
          hasMeas =
            hasMeas
            || [...sj.solution, ...sj.results].some((k) => {
              const oid = workScene.events[k]?.object;
              return oid ? byId.get(oid)?.type === "quantity" : false;
            });
          j += 1;
        } else {
          break;
        }
      }
      preUnits.push({
        origOrder: preUnits.length,
        eventIndices: evIdxs,
        createdVisualIds: [...new Set(visIds)],
        absorbedAuxIds: [],
        extendSectionId: extendSecId,
        closeSectionId: null,
        conclusionQuantityIds: [],
        hasMeasurementOrResult: hasMeas,
      });
      idx = j;
      continue;
    }

    const closeSecId = (() => {
      const evs = cur.construction.map((k) => workScene.events[k]).filter(Boolean);
      const secEv = evs.find((e) => (e.action === "STEP" || e.action === "CREATE") && e.object && byId.get(e.object)?.type === "section");
      return secEv?.object ?? null;
    })();

    const hasCurQtyMeas = [...cur.solution, ...cur.results].some((k) => {
      const oid = workScene.events[k]?.object;
      return oid ? byId.get(oid)?.type === "quantity" : false;
    });
    preUnits.push({
      origOrder: preUnits.length,
      eventIndices: mainEvIndices,
      createdVisualIds: curNew,
      absorbedAuxIds: [],
      extendSectionId: null,
      closeSectionId: closeSecId,
      conclusionQuantityIds: [],
      hasMeasurementOrResult: trailingTargetQIds.length === 0 && hasCurQtyMeas,
    });
    pushTrailingConclusionUnitIfAny();
    idx += 1;
  }

  // Hấp thụ đơn vị đường/mặt phụ dùng một lần (`loai === "dung"`) hoặc trung điểm phụ không ký hiệu chỉ phục vụ trọng tâm G
  const preCreatorOf = new Map<string, number>();
  preUnits.forEach((u, uIdx) => {
    for (const id of u.createdVisualIds) {
      if (!preCreatorOf.has(id)) preCreatorOf.set(id, uIdx);
    }
  });

  const absorbedUnitIdx = new Set<number>();
  let pulledNonAdjacentAux = false;
  for (let uIdx = 0; uIdx < preUnits.length; uIdx += 1) {
    const u = preUnits[uIdx];
    const nonDupIds = u.createdVisualIds.filter((id) => !isDupFacePlaneId(id));
    const isUnlabelledCentroidHelper =
      nonDupIds.length === 1
      && (() => {
        const mObj = byId.get(nonDupIds[0]);
        if (!mObj || mObj.type !== "point3" || Boolean(mObj.notation) || mObj.origin !== "derived") return false;
        const consumers = workScene.objects.filter(
          (cand) => cand.authoritative !== false && cand.type !== "quantity" && (cand.depends ?? []).includes(mObj.id),
        );
        return consumers.length === 1 && findPointCentroidRelation(workScene, consumers[0]) !== null;
      })();
    const isUnlabelledSphereCenterHelper =
      nonDupIds.length === 1
      && (() => {
        const mObj = byId.get(nonDupIds[0]);
        if (!mObj || mObj.type !== "point3" || Boolean(mObj.notation?.trim()) || mObj.origin !== "derived") return false;
        const consumers = workScene.objects.filter(
          (cand) => cand.authoritative !== false && cand.type !== "quantity" && (cand.depends ?? []).includes(mObj.id),
        );
        return (
          consumers.length === 1
          && consumers[0].type === "curved_solid"
          && consumers[0].curved_kind === "ball"
          && consumers[0].anchor?.join("|") === mObj.xyz?.join("|")
        );
      })();
    const isExplicitCuttingForIntersectionLine =
      nonDupIds.some((id) => {
        const po = byId.get(id);
        return Boolean(
          po
          && po.type === "plane3"
          && (
            po.surface_role === "CUTTING_PLANE"
            || isInterCarrierDupPlaneId(id)
            || workScene.objects.some(
              (cand) =>
                isIntersectionLineOrSegment(cand, workScene)
                && (cand.depends ?? []).includes(id)
                && phu.get(cand.id)?.loai !== "dung",
            )
          )
          && workScene.objects.some((cand) => isIntersectionLineOrSegment(cand, workScene) && (cand.depends ?? []).includes(id)),
        );
      });
    const isDisposableAux =
      !isExplicitCuttingForIntersectionLine
      && u.createdVisualIds.length > 0
      && u.createdVisualIds.every((id) => {
        const o = byId.get(id);
        if (o && foundationRoleForCurved(o)) return false;
        if (o && (o.display_group ?? []).includes("sphere_plane_aux")) return false;
        if (o && o.type === "point3" && Boolean(o.perpendicular_witness) && Boolean(o.notation?.trim())) return false;
        return phu.get(id)?.loai === "dung";
      });
    if (
      u.createdVisualIds.length === 0
      || u.hasMeasurementOrResult
      || u.extendSectionId
      || u.closeSectionId
      || (!isDisposableAux && !isUnlabelledCentroidHelper && !isUnlabelledSphereCenterHelper)
    ) {
      continue;
    }
    const consumerUnits = new Set<number>();
    for (const auxId of u.createdVisualIds) {
      for (const cand of workScene.objects) {
        if (cand.type === "quantity" || !(cand.depends ?? []).includes(auxId)) continue;
        const cUnit = preCreatorOf.get(cand.id);
        if (cUnit !== undefined && cUnit !== uIdx) consumerUnits.add(cUnit);
      }
    }
    let targetUIdx: number | undefined;
    if (consumerUnits.size === 1) {
      targetUIdx = [...consumerUnits][0];
    } else if (consumerUnits.size > 1 && isDisposableAux) {
      const cUnits = [...consumerUnits];
      const allPlaneConsumers = cUnits.every((cIdx) => {
        const nonDup = preUnits[cIdx].createdVisualIds.filter((cid) => !isDupFacePlaneId(cid));
        return nonDup.length > 0 && nonDup.every((cid) => byId.get(cid)?.type === "plane3");
      });
      if (allPlaneConsumers) {
        const primaryPlaneUnits = cUnits.filter((cIdx) =>
          preUnits[cIdx].createdVisualIds.some((cid) => !isDupFacePlaneId(cid) && phu.get(cid)?.loai !== "dung"),
        );
        if (primaryPlaneUnits.length === 1) {
          targetUIdx = primaryPlaneUnits[0];
        }
      }
    }
    if (targetUIdx !== undefined && targetUIdx > uIdx) {
      const targetU = preUnits[targetUIdx];
      if (targetUIdx !== uIdx + 1) pulledNonAdjacentAux = true;
      // Chèn các sự kiện dựng hình phụ vào ngay trước các sự kiện của đối tượng đích (giữ thứ tự tương đối giữa nhiều đường phụ)
      const insertPos = targetU.absorbedAuxIds.length > 0
        ? targetU.eventIndices.findIndex((evK) => {
            const evObj = workScene.events[evK]?.object;
            return Boolean(evObj && targetU.createdVisualIds.includes(evObj));
          })
        : 0;
      const pos = insertPos >= 0 ? insertPos : 0;
      targetU.eventIndices.splice(pos, 0, ...u.eventIndices);
      targetU.absorbedAuxIds.push(...u.createdVisualIds);
      absorbedUnitIdx.add(uIdx);
    }
  }

  const freeIdSetForFound = new Set(workScene.free_objects);
  const unitCurvedFoundationStage = (u: PedagogicalUnit): { hostId: string; stage: number } | null => {
    const nonDup = u.createdVisualIds.filter((id) => {
      if (isDupFacePlaneId(id)) return false;
      const o = byId.get(id);
      if (o?.type === "point3" && (o.origin === "free" || freeIdSetForFound.has(id))) return false;
      return true;
    });
    if (nonDup.length === 0) return null;
    const roles = nonDup.map((id) => {
      const o = byId.get(id);
      return o ? foundationRoleForCurved(o) : null;
    });
    if (roles.some((r) => !r)) return null;
    const hostId = roles[0]!.hostId;
    if (!roles.every((r) => r!.hostId === hostId)) return null;
    const distinctStages = new Set(roles.map((r) => r!.stage));
    if (distinctStages.size > 1) return null;
    return { hostId, stage: roles[0]!.stage };
  };

  // Gộp ngữ cảnh các thành phần nền tảng khối tròn xoay cùng `(hostId, stage)` ở stage 1 (`(O) + OA`) và stage 2 (`OO′ + (O′)`)
  const postAuxUnits = preUnits.filter((_, uIdx) => !absorbedUnitIdx.has(uIdx));
  const coalescedCurvedSlotRep = new Map<string, PedagogicalUnit>();
  const postCoalesceUnits: PedagogicalUnit[] = [];
  for (const u of postAuxUnits) {
    const rawFStage =
      !u.extendSectionId && !u.closeSectionId
        ? unitCurvedFoundationStage(u)
        : null;
    const rawHostKind = rawFStage ? byId.get(rawFStage.hostId)?.curved_kind : undefined;
    const fStage =
      rawFStage && (u.conclusionQuantityIds.length === 0 || rawHostKind === "ball")
        ? rawFStage
        : null;
    if (fStage && (fStage.stage === 1 || fStage.stage === 2)) {
      const hostKind = byId.get(fStage.hostId)?.curved_kind;
      if (hostKind === "cone" || hostKind === "cylinder" || hostKind === "ball") {
        const key = `${fStage.hostId}::stage:${fStage.stage}`;
        const existing = coalescedCurvedSlotRep.get(key);
        if (existing) {
          existing.eventIndices.push(...u.eventIndices);
          existing.createdVisualIds.push(...u.createdVisualIds);
          existing.absorbedAuxIds.push(...u.absorbedAuxIds);
          existing.conclusionQuantityIds.push(...u.conclusionQuantityIds);
          existing.hasMeasurementOrResult = existing.hasMeasurementOrResult || u.hasMeasurementOrResult;
          continue;
        }
        coalescedCurvedSlotRep.set(key, u);
      }
    }
    postCoalesceUnits.push(u);
  }

  // Gộp bước tô miền thiết diện (`STEP`) liền kề ngay sau bước dựng khép kín đủ các đoạn giao tuyến (`EXTEND`)
  // theo tiêu chí tôpô tổng quát (chu trình giao tuyến đã khép kín, không phát sinh đỉnh/đối tượng mới hay kết luận số đo).
  const consolidatedSectionUnits: PedagogicalUnit[] = [];
  for (const u of postCoalesceUnits) {
    const prevU = consolidatedSectionUnits[consolidatedSectionUnits.length - 1];
    if (
      prevU
      && prevU.extendSectionId
      && !prevU.closeSectionId
      && prevU.conclusionQuantityIds.length === 0
      && u.closeSectionId === prevU.extendSectionId
      && !u.extendSectionId
      && u.conclusionQuantityIds.length === 0
      && u.absorbedAuxIds.length === 0
      && u.createdVisualIds.every((id) => id === u.closeSectionId || isDupFacePlaneId(id))
    ) {
      const secId = prevU.extendSectionId;
      const secObj = byId.get(secId);
      const lastExtEv = prevU.eventIndices[prevU.eventIndices.length - 1];
      const expectedEdges = Math.max(3, secObj?.steps?.length ?? secObj?.polygon?.length ?? 3);
      const progAtExt = workScene.formation?.steps[lastExtEv]?.geometry_progress?.find(
        (gp) => gp.object_id === secId,
      );
      const extCountUpToHere = workScene.events.filter(
        (ev, evIdx) => evIdx <= lastExtEv && ev.action === "EXTEND" && ev.object === secId,
      ).length;
      const boundaryAlreadyClosed = progAtExt
        ? Boolean(progAtExt.closed || progAtExt.visible_edge_ids.length >= expectedEdges)
        : extCountUpToHere >= expectedEdges;
      if (boundaryAlreadyClosed) {
        prevU.eventIndices.push(...u.eventIndices);
        prevU.createdVisualIds = [...new Set([...prevU.createdVisualIds, ...u.createdVisualIds])];
        prevU.closeSectionId = secId;
        prevU.hasMeasurementOrResult = prevU.hasMeasurementOrResult || u.hasMeasurementOrResult;
        continue;
      }
    }
    consolidatedSectionUnits.push(u);
  }

  const units: PedagogicalUnit[] = consolidatedSectionUnits.map((u, newOrder) => ({ ...u, origOrder: newOrder }));

  // Bước N3: Dựng đồ thị phụ thuộc tôpô (DAG) trên các đơn vị sư phạm
  const creatorUnitOf = new Map<string, number>();
  const extendUnitOfSection = new Map<string, number>();
  const closeUnitOfSection = new Map<string, number>();

  units.forEach((u, uIdx) => {
    for (const id of [...u.absorbedAuxIds, ...u.createdVisualIds]) {
      if (!creatorUnitOf.has(id)) creatorUnitOf.set(id, uIdx);
    }
    for (const evK of u.eventIndices) {
      const ev = workScene.events[evK];
      if (!ev) continue;
      for (const id of [...(ev.object ? [ev.object] : []), ...(ev.objects ?? [])]) {
        if (byId.has(id) && !creatorUnitOf.has(id)) creatorUnitOf.set(id, uIdx);
      }
    }
    if (u.extendSectionId) extendUnitOfSection.set(u.extendSectionId, uIdx);
    if (u.closeSectionId) closeUnitOfSection.set(u.closeSectionId, uIdx);
  });

  const adj: Set<number>[] = Array.from({ length: units.length }, () => new Set<number>());
  const dagEdges: PedagogicalDagEdge[] = [];

  const isReachable = (src: number, dst: number): boolean => {
    if (src === dst) return true;
    const visited = new Set<number>([src]);
    const queue = [src];
    while (queue.length > 0) {
      const cur = queue.shift()!;
      for (const nxt of adj[cur]) {
        if (nxt === dst) return true;
        if (!visited.has(nxt)) {
          visited.add(nxt);
          queue.push(nxt);
        }
      }
    }
    return false;
  };

  const ancestorsOf = (target: number): Set<number> => {
    const anc = new Set<number>();
    for (let cand = 0; cand < units.length; cand += 1) {
      if (cand !== target && isReachable(cand, target)) anc.add(cand);
    }
    return anc;
  };

  const addDagEdge = (uFrom: number, uTo: number, reason: string): void => {
    if (uFrom < 0 || uTo < 0 || uFrom === uTo || adj[uFrom].has(uTo)) return;
    if (isReachable(uTo, uFrom)) return;
    adj[uFrom].add(uTo);
    dagEdges.push({ from: uFrom, to: uTo, reason });
  };

  // D1: Phụ thuộc toán học trực tiếp (`depends` + `perpendicular_witness` + thứ tự `EXTEND` -> `STEP` của thiết diện)
  units.forEach((u, uIdx) => {
    const uFound = unitCurvedFoundationStage(u);
    const unitObjIds = new Set<string>([...u.absorbedAuxIds, ...u.createdVisualIds]);
    for (const evK of u.eventIndices) {
      const ev = workScene.events[evK];
      if (!ev) continue;
      for (const id of [...(ev.object ? [ev.object] : []), ...(ev.objects ?? [])]) {
        if (byId.has(id)) unitObjIds.add(id);
      }
      for (const depId of ev.depends ?? []) {
        if (uFound && (depId === uFound.hostId || isDupFacePlaneId(depId))) continue;
        const uDep = creatorUnitOf.get(depId);
        if (uDep !== undefined && uDep !== uIdx) addDagEdge(uDep, uIdx, "event_dependency");
      }
    }
    for (const id of unitObjIds) {
      const o = byId.get(id);
      if (!o) continue;
      const depCandidates = [
        ...(o.depends ?? []),
        ...(o.endpoint_ids ?? []),
        ...(o.perpendicular_witness?.on ? [o.perpendicular_witness.on] : []),
        ...(o.perpendicular_witness?.foot_id ? [o.perpendicular_witness.foot_id] : []),
        ...(o.perpendicular_witness?.from ? [o.perpendicular_witness.from] : []),
      ];
      for (const depId of depCandidates) {
        if (uFound && (depId === uFound.hostId || isDupFacePlaneId(depId))) continue;
        const uDep = creatorUnitOf.get(depId);
        if (uDep !== undefined && uDep !== uIdx) addDagEdge(uDep, uIdx, "object_dependency");
      }
    }
    if (u.conclusionQuantityIds.length > 0) {
      for (const qId of u.conclusionQuantityIds) {
        const q = byId.get(qId);
        const qDeps = [...new Set([...(q?.depends ?? []), ...(q?.annotation?.subject_ids ?? [])])];
        for (const depId of qDeps) {
          const uDep = creatorUnitOf.get(depId);
          if (uDep !== undefined && uDep !== uIdx) addDagEdge(uDep, uIdx, "quantity_subject_dependency");
        }
        if (qDeps.length === 2) {
          const [d0, d1] = qDeps;
          for (const seg of workScene.objects) {
            if (
              seg.type === "segment3"
              && (seg.depends ?? []).length === 2
              && seg.depends.includes(d0)
              && seg.depends.includes(d1)
            ) {
              const uSeg = creatorUnitOf.get(seg.id);
              if (uSeg !== undefined && uSeg !== uIdx) addDagEdge(uSeg, uIdx, "quantity_segment_carrier");
            }
          }
        }
        if (qDeps.length >= 2) {
          for (const host of workScene.objects) {
            if (host.type !== "solid" && !(host.type === "curved_solid" && !isSecondaryCurvedSolidObj(host))) continue;
            const hostVerts = new Set([...(host.vertex_ids ?? []), ...(host.depends ?? [])]);
            if (qDeps.every((d) => hostVerts.has(d))) {
              const uHost = creatorUnitOf.get(host.id);
              if (uHost !== undefined && uHost !== uIdx) addDagEdge(uHost, uIdx, "host_solid_before_conclusion");
            }
          }
        }
      }
    }
    if (u.closeSectionId) {
      const uExt = extendUnitOfSection.get(u.closeSectionId);
      if (uExt !== undefined && uExt !== uIdx) addDagEdge(uExt, uIdx, "section_traces_before_close");
    }
  });

  // D2: Thứ tự nội bộ khi hình thành khối đa diện:
  // Đáy dưới (`BASE_REGION` không phải `CONSTRUCT_TRANSLATED_FACE`) -> Chân chiếu đáy (`D2b`)
  // -> Đáy đối diện (`CONSTRUCT_TRANSLATED_FACE`) / Đường cao (`CONSTRUCT_HEIGHT`)
  // -> Bộ khung cạnh bên (`CONSTRUCT_LATERAL_BOUNDARY`) -> Khép kín khối (`solid`)
  const solidObjects = workScene.objects.filter((o) => o.type === "solid");
  for (const sol of solidObjects) {
    const uSol = creatorUnitOf.get(sol.id);
    if (uSol === undefined) continue;
    const solVerts = new Set<string>([...(sol.vertex_ids ?? []), ...(sol.depends ?? [])]);
    for (const vId of solVerts) {
      const uVert = creatorUnitOf.get(vId);
      if (uVert !== undefined && uVert !== uSol) addDagEdge(uVert, uSol, "solid_vertex_prerequisite");
    }
    const lowerBasePolys = workScene.objects.filter(
      (o) =>
        (o.surface_role === "BASE_REGION" || (o.formation_roles ?? []).includes("CONSTRUCT_BASE"))
        && !(o.formation_roles ?? []).includes("CONSTRUCT_TRANSLATED_FACE")
        && !isPolyhedronLateralOrAuxFacePolygon(workScene, o)
        && [...(o.depends ?? []), ...(o.vertex_ids ?? [])].length > 0
        && [...(o.depends ?? []), ...(o.vertex_ids ?? [])].every((v) => solVerts.has(v)),
    );
    const auxLateralFacePolys = workScene.objects.filter(
      (o) =>
        o.type === "polygon3"
        && isPolyhedronLateralOrAuxFacePolygon(workScene, o)
        && [...(o.depends ?? []), ...(o.vertex_ids ?? [])].length > 0
        && [...(o.depends ?? []), ...(o.vertex_ids ?? [])].every((v) => solVerts.has(v)),
    );
    for (const latPoly of auxLateralFacePolys) {
      const uLatPoly = creatorUnitOf.get(latPoly.id);
      if (uLatPoly !== undefined && uLatPoly !== uSol) {
        addDagEdge(uSol, uLatPoly, "solid_before_lateral_face_polygon");
      }
    }
    const translatedFaces = workScene.objects.filter(
      (o) =>
        o.type === "polygon3"
        && (o.formation_roles ?? []).includes("CONSTRUCT_TRANSLATED_FACE")
        && [...(o.depends ?? []), ...(o.vertex_ids ?? [])].length > 0
        && [...(o.depends ?? []), ...(o.vertex_ids ?? [])].every((v) => solVerts.has(v)),
    );
    const lateralEdgeObjs = workScene.objects.filter((o) => {
      const r = o.formation_roles ?? [];
      return (
        o.type === "segment3"
        && r.includes("CONSTRUCT_LATERAL_BOUNDARY")
        && !r.includes("CONSTRUCT_HEIGHT")
        && (o.depends ?? []).length > 0
        && (o.depends ?? []).every((v) => solVerts.has(v))
      );
    });
    const baseVertSet = new Set<string>();
    const lowerBaseIds = new Set<string>();
    for (const bPoly of lowerBasePolys) {
      lowerBaseIds.add(bPoly.id);
      for (const bv of [...(bPoly.depends ?? []), ...(bPoly.vertex_ids ?? [])]) baseVertSet.add(bv);
    }
    const isPointAnchoredToSolBase = (ptId: string, seen = new Set<string>()): boolean => {
      if (baseVertSet.has(ptId)) return true;
      if (seen.has(ptId)) return false;
      seen.add(ptId);
      const pObj = byId.get(ptId);
      if (!pObj || pObj.origin === "free") return false;
      const nonVecDeps = (pObj.depends ?? []).filter((d) => byId.get(d)?.type !== "vector3");
      return nonVecDeps.length > 0 && nonVecDeps.every((d) => isPointAnchoredToSolBase(d, seen));
    };
    const heightObjs = workScene.objects.filter((o) => {
      if (!(o.formation_roles ?? []).includes("CONSTRUCT_HEIGHT")) return false;
      const wFrom = o.perpendicular_witness?.from;
      const wOn = o.perpendicular_witness?.on;
      const upperInSol = wFrom
        ? solVerts.has(wFrom)
        : (o.depends ?? []).some((d) => solVerts.has(d) && (baseVertSet.size === 0 || !baseVertSet.has(d)));
      if (!upperInSol) return false;
      if (baseVertSet.size === 0) return true;
      if (wOn) {
        if (wOn === sol.id || lowerBaseIds.has(wOn)) return true;
        const onObj = byId.get(wOn);
        if (onObj && (onObj.type === "plane3" || onObj.type === "polygon3")) {
          const onDeps = [...(onObj.depends ?? []), ...(onObj.vertex_ids ?? [])];
          return onDeps.length > 0 && onDeps.every((d) => isPointAnchoredToSolBase(d));
        }
        return false;
      }
      if (wFrom) {
        const ptDeps = (o.depends ?? []).filter((d) => byId.get(d)?.type === "point3" && d !== wFrom);
        return ptDeps.length > 0 && ptDeps.every((d) => isPointAnchoredToSolBase(d));
      }
      const allPtDeps = (o.depends ?? []).filter((d) => byId.get(d)?.type === "point3");
      return (
        allPtDeps.length >= 2
        && allPtDeps.some((d) => isPointAnchoredToSolBase(d))
        && allPtDeps.every((d) => solVerts.has(d) || isPointAnchoredToSolBase(d))
      );
    });

    for (const bPoly of lowerBasePolys) {
      const uBase = creatorUnitOf.get(bPoly.id);
      if (uBase === undefined) continue;
      if (uBase !== uSol) addDagEdge(uBase, uSol, "base_before_solid");
      for (const tf of translatedFaces) {
        const uTf = creatorUnitOf.get(tf.id);
        if (uTf !== undefined && uBase !== uTf) addDagEdge(uBase, uTf, "lower_base_before_translated_face");
      }
      for (const le of lateralEdgeObjs) {
        const uLat = creatorUnitOf.get(le.id);
        if (uLat !== undefined && uBase !== uLat) addDagEdge(uBase, uLat, "base_before_lateral_edges");
      }
    }
    for (const tf of translatedFaces) {
      const uTf = creatorUnitOf.get(tf.id);
      if (uTf === undefined) continue;
      if (uTf !== uSol) addDagEdge(uTf, uSol, "translated_face_before_solid");
      for (const le of lateralEdgeObjs) {
        const uLat = creatorUnitOf.get(le.id);
        if (uLat !== undefined && uTf !== uLat) addDagEdge(uTf, uLat, "translated_face_before_lateral_edges");
      }
    }
    for (const hObj of heightObjs) {
      const uHeight = creatorUnitOf.get(hObj.id);
      if (uHeight === undefined) continue;
      for (const bPoly of lowerBasePolys) {
        const uBase = creatorUnitOf.get(bPoly.id);
        if (uBase !== undefined && uBase !== uHeight) addDagEdge(uBase, uHeight, "base_before_height");
      }
      const hFootId =
        hObj.perpendicular_witness?.foot_id
        ?? (hObj.depends ?? []).find((d) => byId.get(d)?.type === "point3" && byId.get(d)?.origin === "derived");
      if (hFootId && byId.get(hFootId)?.origin === "derived") {
        for (const tf of translatedFaces) {
          const uTf = creatorUnitOf.get(tf.id);
          if (uTf !== undefined && uHeight !== uTf) addDagEdge(uHeight, uTf, "oblique_height_before_translated_face");
        }
      }
      for (const le of lateralEdgeObjs) {
        const uLat = creatorUnitOf.get(le.id);
        if (uLat !== undefined && uHeight !== uLat) addDagEdge(uHeight, uLat, "height_before_lateral_edges");
      }
      if (uHeight !== uSol) addDagEdge(uHeight, uSol, "height_before_solid");
    }
    for (const le of lateralEdgeObjs) {
      const uLat = creatorUnitOf.get(le.id);
      if (uLat !== undefined && uLat !== uSol) addDagEdge(uLat, uSol, "lateral_edges_before_solid");
    }

    // D2b: Chân hình chiếu vuông góc trên mặt đáy dưới (vd trọng tâm `G` là hình chiếu của `A′` lên `(ABC)` trong lăng trụ xiên)
    // phải được xác định sau đáy dưới `lowerBasePolys` và trước `translatedFaces` / `lateralEdgeObjs` / `solid`.
    if (baseVertSet.size > 0) {
      const exBasePts = [...baseVertSet]
        .map((id) => exactOriginById.get(id) ?? byId.get(id))
        .filter((p): p is SceneObject => Boolean(p && p.type === "point3" && p.xyz));
      const exUpperPts = [...solVerts]
        .filter((id) => !baseVertSet.has(id))
        .map((id) => ({ id, obj: exactOriginById.get(id) ?? byId.get(id) }))
        .filter((x): x is { id: string; obj: SceneObject } => Boolean(x.obj && x.obj.type === "point3" && x.obj.xyz));

      const onlyDependsOnBaseVerts = (startId: string, seen = new Set<string>()): boolean => {
        if (seen.has(startId)) return true;
        seen.add(startId);
        const curObj = byId.get(startId);
        if (!curObj) return false;
        if (curObj.origin === "free") return baseVertSet.has(startId);
        const deps = curObj.depends ?? [];
        return deps.length > 0 && deps.every((d) => onlyDependsOnBaseVerts(d, seen));
      };

      for (const pt of workScene.objects) {
        if (pt.type !== "point3" || pt.origin !== "derived" || !pt.notation) continue;
        const wFrom = pt.perpendicular_witness?.from;
        let isBaseProjectionFoot = false;
        if (wFrom && solVerts.has(wFrom) && !baseVertSet.has(wFrom)) {
          isBaseProjectionFoot =
            heightObjs.some((h) => h.perpendicular_witness?.foot_id === pt.id || (h.depends ?? []).includes(pt.id))
            || translatedFaces.some((tf) => (tf.depends ?? []).includes(pt.id))
            || [...solVerts].some((vId) => (byId.get(vId)?.depends ?? []).includes(pt.id))
            || (pt.perpendicular_witness?.on
              ? byId.get(pt.perpendicular_witness.on)?.surface_role === "BASE_REGION"
                || lowerBasePolys.some(
                  (bp) =>
                    bp.id === pt.perpendicular_witness?.on
                    || (byId.get(pt.perpendicular_witness!.on)?.type === "plane3"
                      && (byId.get(pt.perpendicular_witness!.on)?.depends ?? []).every((d) => baseVertSet.has(d))),
                )
              : false);
        } else if (exBasePts.length >= 3 && exUpperPts.length > 0 && onlyDependsOnBaseVerts(pt.id)) {
          if (heightObjs.some((h) => h.perpendicular_witness?.foot_id === pt.id || (h.depends ?? []).includes(pt.id))) {
            isBaseProjectionFoot = true;
          } else {
            const exPtObj = exactOriginById.get(pt.id) ?? pt;
            if (exPtObj.xyz && heightObjs.length === 0) {
              const pFoot = parseFracVec3(exPtObj.xyz);
              const b0 = parseFracVec3(exBasePts[0].xyz!);
              const baseEdges = exBasePts.slice(1).map((bp) => vSub(parseFracVec3(bp.xyz!), b0));
              const gMetric = exactOriginForPlan.chart_metric ?? workScene.chart_metric;
              // Kiểm tra chân vuông góc chính xác trên metric Gram của một đỉnh ngoài đáy (không có đường cao tường minh khác đã dựng)
              isBaseProjectionFoot = exUpperPts.some((up) => {
                const dropVec = vSub(parseFracVec3(up.obj.xyz!), pFoot);
                return (
                  !vIsZero(dropVec)
                  && baseEdges.every((be) => fIsZero(metricDot(dropVec, be, gMetric)))
                );
              });
            }
          }
        }
        if (!isBaseProjectionFoot) continue;
        const uFoot = creatorUnitOf.get(pt.id);
        if (uFoot === undefined || uFoot === uSol) continue;
        for (const bPoly of lowerBasePolys) {
          const uBase = creatorUnitOf.get(bPoly.id);
          if (uBase !== undefined && uBase !== uFoot) addDagEdge(uBase, uFoot, "base_before_projection_foot");
        }
        for (const tf of translatedFaces) {
          const uTf = creatorUnitOf.get(tf.id);
          if (uTf !== undefined && uTf !== uFoot) addDagEdge(uFoot, uTf, "projection_foot_before_translated_face");
        }
        for (const le of lateralEdgeObjs) {
          const uLat = creatorUnitOf.get(le.id);
          if (uLat !== undefined && uLat !== uFoot) addDagEdge(uFoot, uLat, "projection_foot_before_lateral_edges");
        }
        addDagEdge(uFoot, uSol, "projection_foot_before_solid");
      }
    }
  }

  // D3: Khối đa diện chủ (và các cạnh bên/cạnh trên của nó, vd `SC` của `S.ABCD`) phải tồn tại trước mọi điểm/đường/mặt
  // dựng trên cạnh bên hoặc đỉnh ngoài đáy của khối đó (loại bỏ triệt để lỗi dựng `M = trung điểm SC` ở bước 1 trước khối `S.ABCD`).
  for (const sol of solidObjects) {
    const uSol = creatorUnitOf.get(sol.id);
    if (uSol === undefined) continue;
    const solVerts = new Set<string>([...(sol.vertex_ids ?? []), ...(sol.depends ?? [])]);
    const baseVerts = new Set<string>();
    for (const o of workScene.objects) {
      if (
        !(o.surface_role === "BASE_REGION" || (o.formation_roles ?? []).includes("CONSTRUCT_BASE"))
        || (o.formation_roles ?? []).includes("CONSTRUCT_TRANSLATED_FACE")
        || isPolyhedronLateralOrAuxFacePolygon(workScene, o)
      ) {
        continue;
      }
      const bV = [...(o.depends ?? []), ...(o.vertex_ids ?? [])];
      if (bV.length > 0 && bV.every((v) => solVerts.has(v))) {
        for (const v of bV) baseVerts.add(v);
      }
    }
    const planesCuttingSol = new Set<string>(
      workScene.objects
        .filter((o) => o.type === "section" && (o.depends ?? []).includes(sol.id))
        .flatMap((o) => (o.depends ?? []).filter((d) => byId.get(d)?.type === "plane3")),
    );
    const formingSol = ancestorsOf(uSol);
    units.forEach((uOther, uOtherIdx) => {
      if (uOtherIdx === uSol || formingSol.has(uOtherIdx)) return;
      const otherObjs = [...uOther.absorbedAuxIds, ...uOther.createdVisualIds]
        .map((id) => byId.get(id))
        .filter((x): x is SceneObject => Boolean(x));
      const usesSolidOrNonBaseCarrier = otherObjs.some((o) => {
        if (planesCuttingSol.has(o.id)) return true;
        const deps = o.depends ?? [];
        if (deps.includes(sol.id)) return true;
        if (baseVerts.size > 0) {
          return deps.some((d) => solVerts.has(d) && !baseVerts.has(d));
        }
        return deps.filter((d) => solVerts.has(d)).length >= 2;
      });
      if (usesSolidOrNonBaseCarrier) {
        addDagEdge(uSol, uOtherIdx, "carrier_solid_before_edge_construction");
      }
    });
  }

  // D4: Thứ tự hình thành khối tròn xoay sơ cấp (đáy/bán kính -> trục/đáy đối diện -> đường sinh cho trước -> hoàn thiện mặt xung quanh -> thiết diện)
  const curvedSolids = workScene.objects.filter((o) => o.type === "curved_solid");
  for (const cs of curvedSolids) {
    const uCurved = creatorUnitOf.get(cs.id);
    if (uCurved === undefined) continue;
    const foundUnits: { uIdx: number; stage: number }[] = [];
    units.forEach((uCand, uCandIdx) => {
      if (uCandIdx === uCurved) return;
      const fRole = unitCurvedFoundationStage(uCand);
      if (fRole && fRole.hostId === cs.id) {
        foundUnits.push({ uIdx: uCandIdx, stage: fRole.stage });
      }
    });
    foundUnits.sort((a, b) => a.stage - b.stage || a.uIdx - b.uIdx);
    for (let i = 0; i < foundUnits.length; i += 1) {
      for (let j = i + 1; j < foundUnits.length; j += 1) {
        if (foundUnits[i].stage < foundUnits[j].stage) {
          addDagEdge(foundUnits[i].uIdx, foundUnits[j].uIdx, "curved_foundation_stage_order");
        }
      }
      addDagEdge(foundUnits[i].uIdx, uCurved, "curved_foundation_before_solid");
    }

    const csDeps = new Set<string>(cs.depends ?? []);
    const exCs = exactOriginById.get(cs.id) ?? cs;
    const csCenterIds = new Set<string>([cs.id]);
    if (cs.curved_kind === "ball" && exCs.anchor) {
      const cAnchor = parseFracVec3(exCs.anchor);
      for (const p of workScene.objects) {
        if (isSubEntity(p.id) || p.type !== "point3") continue;
        const ep = exactOriginById.get(p.id) ?? p;
        if (ep.xyz && vIsZero(vSub(parseFracVec3(ep.xyz), cAnchor))) {
          csCenterIds.add(p.id);
        }
      }
    }
    const planesCuttingCurved = new Set<string>(
      workScene.objects
        .filter((o) => (o.type === "circle3" || o.type === "ellipse3") && (o.depends ?? []).includes(cs.id))
        .flatMap((o) => (o.depends ?? []).filter((d) => byId.get(d)?.type === "plane3")),
    );
    if (cs.curved_kind === "ball" && classifySphereSemanticRole(workScene, cs) === "STANDALONE_SPHERE") {
      for (const pl of workScene.objects) {
        if (isSubEntity(pl.id) || pl.type !== "plane3" || workMeasOnlyIds.has(pl.id)) continue;
        if (pl.surface_role === "CUTTING_PLANE") {
          planesCuttingCurved.add(pl.id);
          continue;
        }
        const exPl = exactOriginById.get(pl.id) ?? pl;
        if (exCs.anchor && exCs.radius_sq && exPl.point && exPl.normal) {
          const proj = projectPointOntoPlaneExact(
            parseFracVec3(exCs.anchor),
            parseFracVec3(exPl.point),
            parseFracVec3(exPl.normal),
            exactOriginForPlan.chart_metric ?? workScene.chart_metric,
          );
          if (proj) {
            const diff = vSub(proj.foot, parseFracVec3(exCs.anchor));
            const d2 = metricDot(diff, diff, exactOriginForPlan.chart_metric ?? workScene.chart_metric);
            const R2 = parseExactFrac(exCs.radius_sq);
            if (fSub(R2, d2)[0] >= 0n) {
              planesCuttingCurved.add(pl.id);
            }
          }
        }
      }
    }
    const formingCurved = ancestorsOf(uCurved);
    units.forEach((uOther, uOtherIdx) => {
      if (uOtherIdx === uCurved || formingCurved.has(uOtherIdx)) return;
      const otherObjs = [...uOther.absorbedAuxIds, ...uOther.createdVisualIds]
        .map((id) => byId.get(id))
        .filter((x): x is SceneObject => Boolean(x));
      const usesCurvedCarrier = otherObjs.some((o) => {
        if (planesCuttingCurved.has(o.id)) return true;
        const deps = o.depends ?? [];
        if (deps.includes(cs.id) || deps.filter((d) => csDeps.has(d)).length >= 2) return true;
        const pw = o.perpendicular_witness ?? o.annotation?.witness;
        if (
          cs.curved_kind === "ball"
          && pw
          && ((pw.from && csCenterIds.has(pw.from)) || (pw.on && planesCuttingCurved.has(pw.on)))
          && (deps.some((d) => csCenterIds.has(d) || planesCuttingCurved.has(d)) || (pw.on && planesCuttingCurved.has(pw.on)))
        ) {
          return true;
        }
        if ((o.type === "segment3" || o.type === "line3") && classifyCurvedSegmentRole(workScene, o)?.host.id === cs.id) {
          return true;
        }
        return false;
      });
      if (usesCurvedCarrier) {
        addDagEdge(uCurved, uOtherIdx, "curved_solid_before_surface_element");
      }
    });
  }

  // D5: Mọi giao điểm có tên nằm trên đỉnh đa giác thiết diện phải được xác định trước bước dựng các giao tuyến `EXTEND`
  for (const sec of workScene.objects) {
    if (sec.type !== "section" || !sec.polygon) continue;
    const uSecTarget = extendUnitOfSection.get(sec.id) ?? closeUnitOfSection.get(sec.id);
    if (uSecTarget === undefined) continue;
    const formingSec = ancestorsOf(uSecTarget);
    const polyKeys = new Set(sec.polygon.map((v) => v.join("|")));
    for (const pt of workScene.objects) {
      if (pt.type !== "point3" || pt.origin !== "derived" || !pt.xyz || !polyKeys.has(pt.xyz.join("|"))) continue;
      const uPt = creatorUnitOf.get(pt.id);
      if (uPt !== undefined && uPt !== uSecTarget && !formingSec.has(uPt)) {
        addDagEdge(uPt, uSecTarget, "section_vertex_before_traces");
      } else if (uPt !== undefined && uPt !== uSecTarget) {
        addDagEdge(uPt, uSecTarget, "section_vertex_before_traces");
      }
    }
  }

  // D6: Khi một phép dựng giao điểm (vd `Q = SD ∩ (MNP)`) hấp thụ một mặt phẳng phụ `derived_Q_plane` trùng khít về mặt đại số
  // với một mặt phẳng cắt tường minh `CONSTRUCT_CUTTING_OBJECT` (vd `mp_td_fsec` `(MNP)`), mặt phẳng cắt tường minh phải được
  // dựng trước bước tìm giao điểm đó (trừ khi mặt phẳng cắt lại phụ thuộc ngược vào giao điểm đó).
  const explicitCuttingPlanes = workScene.objects.filter(
    (o) =>
      o.type === "plane3"
      && Boolean(o.normal && o.point)
      && (o.formation_roles ?? []).includes("CONSTRUCT_CUTTING_OBJECT"),
  );
  for (let uIdx = 0; uIdx < units.length; uIdx += 1) {
    const auxPlanes = units[uIdx].absorbedAuxIds
      .map((id) => byId.get(id))
      .filter((o): o is SceneObject => Boolean(o && o.type === "plane3" && o.normal && o.point));
    if (auxPlanes.length === 0) continue;
    for (const pAux of auxPlanes) {
      const nAux = parseFracVec3(pAux.normal!);
      const ptAux = parseFracVec3(pAux.point!);
      for (const pCut of explicitCuttingPlanes) {
        const uCut = creatorUnitOf.get(pCut.id);
        if (uCut === undefined || uCut === uIdx) continue;
        const nCut = parseFracVec3(pCut.normal!);
        const ptCut = parseFracVec3(pCut.point!);
        if (
          vIsZero(vCross(nAux, nCut))
          && fIsZero(plainDotFrac(vSub(ptAux, ptCut), nCut))
          && !ancestorsOf(uCut).has(uIdx)
        ) {
          addDagEdge(uCut, uIdx, "cutting_plane_before_intersection_using_same_plane");
        }
      }
    }
  }

  // Sắp xếp tôpô Kahn ổn định (ưu tiên `origOrder` nhỏ nhất khi nhiều bước cùng sẵn sàng)
  const inDegree = new Array<number>(units.length).fill(0);
  for (let u = 0; u < units.length; u += 1) {
    for (const v of adj[u]) inDegree[v] += 1;
  }
  const ready: number[] = [];
  for (let u = 0; u < units.length; u += 1) {
    if (inDegree[u] === 0) ready.push(u);
  }
  const topoOrder: number[] = [];
  while (ready.length > 0) {
    ready.sort((a, b) => a - b);
    const u = ready.shift()!;
    topoOrder.push(u);
    for (const v of adj[u]) {
      inDegree[v] -= 1;
      if (inDegree[v] === 0) ready.push(v);
    }
  }
  if (topoOrder.length < units.length) {
    for (let u = 0; u < units.length; u += 1) {
      if (!topoOrder.includes(u)) topoOrder.push(u);
    }
  }

  const candidateOrderedEventIndices: number[] = [...initEventIndices];
  for (const uIdx of topoOrder) {
    candidateOrderedEventIndices.push(...units[uIdx].eventIndices);
  }
  const eventOrderChanged =
    candidateOrderedEventIndices.length !== workScene.events.length
    || candidateOrderedEventIndices.some((oldK, newK) => oldK !== newK);
  const orderChanged = topoOrder.some((uIdx, pos) => uIdx !== pos);
  const freeIdSetForMeas = new Set(workScene.free_objects);
  const isPureNonVisualUnit = (u: PedagogicalUnit): boolean => {
    const hasInitVisualObjects =
      u.conclusionQuantityIds.length === 0
      && u.eventIndices.some((k) => workScene.events[k]?.action === "INIT")
      && u.createdVisualIds.some((id) => !isDupFacePlaneId(id) && !workMeasOnlyIds.has(id));
    if (hasInitVisualObjects) return false;
    const nonFreeVisualIds = u.createdVisualIds.filter(
      (id) => !freeIdSetForMeas.has(id) && !isDupFacePlaneId(id) && !workMeasOnlyIds.has(id),
    );
    return (
      nonFreeVisualIds.length === 0
      && u.absorbedAuxIds.length === 0
      && !u.extendSectionId
      && !u.closeSectionId
      && u.eventIndices.length > 0
      && (
        u.conclusionQuantityIds.length > 0
        || u.eventIndices.every((k) => {
          const ev = workScene.events[k];
          if (!ev) return true;
          if (ev.action === "MEASURE" || ev.action === "INIT") return true;
          const target = ev.object ? byId.get(ev.object) : undefined;
          return Boolean(
            target
            && (target.type === "quantity"
              || target.render === "readout"
              || target.render === "non_visual"
              || workMeasOnlyIds.has(target.id)
              || isDupFacePlaneId(target.id)),
          );
        })
      )
    );
  };
  const hasVisualConstructionUnit = units.some((u) => !isPureNonVisualUnit(u));
  const isPureMeasurementUnit = (u: PedagogicalUnit): boolean =>
    hasVisualConstructionUnit && isPureNonVisualUnit(u);
  const hasUntypedFoldedMeasurement =
    units.some(isPureMeasurementUnit)
    && workScene.events.some((ev) => !ev.semantic_kind || ev.semantic_kind === "LEGACY_UNTYPED_EVENT");
  const needsRebuild = didSplit || pulledNonAdjacentAux || orderChanged || eventOrderChanged || hasUntypedFoldedMeasurement;

  let orderedSemanticScene: Scene3D = workScene;
  const unitAnchorRanges: { unit: PedagogicalUnit; startAnchor: number; narrateAnchor: number; anchor: number }[] = [];

  if (!needsRebuild) {
    let pendingStart: number | null = null;
    for (const u of units) {
      const startAnchor: number = pendingStart ?? u.eventIndices[0];
      const anchor = u.eventIndices[u.eventIndices.length - 1];
      if (isPureMeasurementUnit(u)) {
        if (unitAnchorRanges.length > 0) {
          unitAnchorRanges[unitAnchorRanges.length - 1].anchor = anchor;
        } else {
          pendingStart = startAnchor;
        }
        continue;
      }
      pendingStart = null;
      unitAnchorRanges.push({ unit: u, startAnchor, narrateAnchor: anchor, anchor });
    }
  } else {
    const orderedEventIndices: number[] = [...initEventIndices];
    let pendingStart: number | null = null;
    for (const uIdx of topoOrder) {
      const u = units[uIdx];
      const startAnchor: number = pendingStart ?? orderedEventIndices.length;
      orderedEventIndices.push(...u.eventIndices);
      const anchor = orderedEventIndices.length - 1;
      if (isPureMeasurementUnit(u)) {
        if (unitAnchorRanges.length > 0) {
          unitAnchorRanges[unitAnchorRanges.length - 1].anchor = anchor;
        } else {
          pendingStart = startAnchor;
        }
        continue;
      }
      pendingStart = null;
      unitAnchorRanges.push({ unit: u, startAnchor, narrateAnchor: anchor, anchor });
    }

    const rebuiltEvents: SceneEvent[] = orderedEventIndices.map((oldK, newK) => {
      const srcEv = workScene.events[oldK];
      const measTarget = srcEv.action === "MEASURE" && srcEv.object ? byId.get(srcEv.object) : undefined;
      const measSrc = measTarget?.source as Record<string, unknown> | undefined;
      const isNonAnswerMeasureTarget = Boolean(
        measTarget
        && (
          isCertifiedGivenSceneObject(workScene, measTarget)
          || (!hasUncertifiedObjectSource(measTarget) && measTarget.annotation?.role === "given")
          || measTarget.annotation?.role === "intermediate"
          || (!hasUncertifiedObjectSource(measTarget) && measSrc?.provenance === "GIVEN")
        )
        && measTarget.annotation?.role !== "result"
        && measTarget.annotation?.category !== "result",
      );
      const normKind =
        srcEv.semantic_kind && srcEv.semantic_kind !== "LEGACY_UNTYPED_EVENT"
          ? srcEv.semantic_kind
          : srcEv.action === "MEASURE"
            ? (isNonAnswerMeasureTarget ? "MEASUREMENT" : "FINAL_RESULT")
            : srcEv.action === "INIT"
              ? "EXPLANATION"
              : "GEOMETRY_CONSTRUCTION";
      return {
        ...srcEv,
        step_index: newK,
        semantic_kind: normKind,
      };
    });

    let rebuiltFormation = workScene.formation;
    if (workScene.formation && workScene.formation.steps.length === workScene.events.length) {
      const oldSteps = workScene.formation.steps;
      const oldAddedAt = oldSteps.map((st, oldK) => {
        if (oldK === 0) return [...st.visible_ids];
        const prev = new Set(oldSteps[oldK - 1].visible_ids);
        return st.visible_ids.filter((id) => !prev.has(id));
      });
      const oldRemovedAt = oldSteps.map((st, oldK) => {
        if (oldK === 0) return [] as string[];
        const curSet = new Set(st.visible_ids);
        return oldSteps[oldK - 1].visible_ids.filter((id) => !curSet.has(id));
      });
      const oldReadoutAddedAt = oldSteps.map((st, oldK) => {
        if (oldK === 0) return [...st.readout_ids];
        const prev = new Set(oldSteps[oldK - 1].readout_ids);
        return st.readout_ids.filter((id) => !prev.has(id));
      });
      const oldProgressChangedAt = oldSteps.map((st, oldK) => {
        const curProg = st.geometry_progress ?? [];
        if (oldK === 0) return curProg;
        const prevMap = new Map(
          (oldSteps[oldK - 1].geometry_progress ?? []).map((gp) => [
            gp.object_id,
            JSON.stringify([gp.visible_edge_ids, gp.closed, gp.fill_visible]),
          ]),
        );
        return curProg.filter(
          (gp) => prevMap.get(gp.object_id) !== JSON.stringify([gp.visible_edge_ids, gp.closed, gp.fill_visible]),
        );
      });

      const runningVisible = new Set<string>(workScene.free_objects.filter((id) => byId.has(id)));
      const runningReadouts = new Set<string>();
      const latestProgress = new Map<string, GeometryProgress>();

      const newFormationSteps: FormationStep[] = orderedEventIndices.map((oldK, newK) => {
        const oldSt = oldSteps[oldK];
        const ev = workScene.events[oldK];
        for (const id of oldAddedAt[oldK]) {
          if (byId.has(id)) runningVisible.add(id);
        }
        if (ev) {
          for (const id of [...(ev.object ? [ev.object] : []), ...(ev.objects ?? [])]) {
            if (byId.has(id)) runningVisible.add(id);
          }
          for (const rId of ev.retires ?? []) runningVisible.delete(rId);
        }
        for (const rId of oldRemovedAt[oldK]) runningVisible.delete(rId);
        for (const rdId of oldReadoutAddedAt[oldK]) runningReadouts.add(rdId);
        for (const gp of oldProgressChangedAt[oldK]) {
          latestProgress.set(gp.object_id, gp);
        }
        const activeProgress = [...latestProgress.values()].filter((gp) => runningVisible.has(gp.object_id));
        return {
          ...oldSt,
          step_index: newK,
          visible_ids: workScene.objects.map((o) => o.id).filter((id) => runningVisible.has(id)),
          readout_ids: [...runningReadouts],
          ...(activeProgress.length > 0 ? { geometry_progress: activeProgress } : { geometry_progress: [] }),
        };
      });
      rebuiltFormation = { steps: newFormationSteps };
    }

    orderedSemanticScene = {
      ...workScene,
      events: rebuiltEvents,
      ...(rebuiltFormation ? { formation: rebuiltFormation } : {}),
    };
  }

  const outScene: Scene3D = !needsRebuild
    ? rawScene
    : hadSubEntities
      ? withSubEntities(orderedSemanticScene)
      : orderedSemanticScene;
  propagateSceneLineage(orderedSemanticScene, workScene);
  propagateSceneLineage(outScene, workScene);
  if (rawExactOrigin !== rawScene && outScene !== rawScene) {
    const exactPlan = buildPedagogicalConstructionPlan(rawExactOrigin, options);
    registerExactSceneOrigin(orderedSemanticScene, exactPlan.scene);
    registerExactSceneOrigin(outScene, exactPlan.scene);
  }

  // Bước N4: Tính toán đầy đủ 7 trường siêu dữ liệu sư phạm trên từng bước đã sắp tôpô
  const outById = new Map(orderedSemanticScene.objects.map((o) => [o.id, o]));
  const outPhu = auxiliaryObjects(orderedSemanticScene);
  const finalOutAnchor = Math.max(0, orderedSemanticScene.events.length - 1);
  const dupPlaneIds = new Set(
    orderedSemanticScene.objects
      .filter(
        (o) =>
          o.type === "plane3"
          && !orderedSemanticScene.objects.some(
            (x) => !isSubEntity(x.id) && isIntersectionLineOrSegment(x, orderedSemanticScene) && (x.depends ?? []).includes(o.id),
          )
          && resolvePlaneSectionVisibility(orderedSemanticScene, o, finalOutAnchor, false, null).subRole ===
            "SOLID_FACE_DUPLICATE_PLANE",
      )
      .map((o) => o.id),
  );
  const measOnlyIds = measurementOnlyPlanes(orderedSemanticScene);

  const accumulatedPriorIds = new Set<string>(
    orderedSemanticScene.free_objects.filter((id) => outById.has(id)),
  );

  const steps: PedagogicalStepItem[] = unitAnchorRanges.map(({ unit, startAnchor, narrateAnchor, anchor }, index) => {
    const nar = buildPedagogicalNarrationForRange(orderedSemanticScene, startAnchor, narrateAnchor);
    const ungrounded = ungroundedFreePointIdsAt(orderedSemanticScene, anchor);
    const auxHidden = auxiliaryHiddenAt(orderedSemanticScene, anchor, false, null);

    const visibleIds = objectsAt(orderedSemanticScene, anchor)
      .filter(
        (o) =>
          !isSubEntity(o.id)
          && o.render !== "readout"
          && o.render !== "non_visual"
          && !ungrounded.has(o.id)
          && !auxHidden.has(o.id)
          && !dupPlaneIds.has(o.id)
          && !measOnlyIds.has(o.id),
      )
      .map((o) => o.id);

    const nonDupCreated = unit.createdVisualIds.filter((id) => !dupPlaneIds.has(id) && !measOnlyIds.has(id));
    let targetIds: string[];
    if (unit.conclusionQuantityIds.length > 0) {
      const visibleSet = new Set(visibleIds);
      const carriers: string[] = [];
      for (const qId of unit.conclusionQuantityIds) {
        const qObj = outById.get(qId);
        const qDeps = [...new Set([...(qObj?.depends ?? []), ...(qObj?.annotation?.subject_ids ?? [])])];
        if (qDeps.length === 2) {
          const [d0, d1] = qDeps;
          const matchingSeg = orderedSemanticScene.objects.find(
            (cand) =>
              cand.type === "segment3"
              && visibleSet.has(cand.id)
              && (cand.depends ?? []).length === 2
              && cand.depends.includes(d0)
              && cand.depends.includes(d1),
          );
          if (matchingSeg) carriers.push(matchingSeg.id);
        }
        for (const depId of qDeps) {
          if (visibleSet.has(depId)) {
            carriers.push(depId);
          } else {
            const depObj = outById.get(depId);
            if (depObj && (dupPlaneIds.has(depId) || measOnlyIds.has(depId))) {
              const depVerts = new Set(depObj.depends ?? []);
              const matchingPoly = orderedSemanticScene.objects.find(
                (cand) =>
                  cand.type === "polygon3"
                  && visibleSet.has(cand.id)
                  && (cand.depends ?? []).length === depVerts.size
                  && (cand.depends ?? []).every((v) => depVerts.has(v)),
              );
              if (matchingPoly) {
                carriers.push(matchingPoly.id);
              } else {
                for (const v of depObj.depends ?? []) {
                  if (visibleSet.has(v)) carriers.push(v);
                }
              }
            }
          }
        }
      }
      targetIds = carriers.length > 0 ? [...new Set(carriers)] : [...unit.conclusionQuantityIds];
    } else if (unit.extendSectionId) {
      targetIds = [unit.extendSectionId];
    } else if (unit.closeSectionId) {
      targetIds = [unit.closeSectionId];
    } else if (
      nonDupCreated.some((id) => {
        const t = outById.get(id)?.type;
        return t === "solid" || t === "curved_solid";
      })
    ) {
      const solidsFirst = nonDupCreated.filter((id) => {
        const t = outById.get(id)?.type;
        return t === "solid" || t === "curved_solid";
      });
      const others = nonDupCreated.filter((id) => {
        const t = outById.get(id)?.type;
        return t !== "solid" && t !== "curved_solid";
      });
      targetIds = [...solidsFirst, ...others];
    } else if (nonDupCreated.length > 0) {
      const authFirst = nonDupCreated.filter((id) => {
        const cand = outById.get(id);
        return !(cand?.authoritative === false && cand.semantic_role === "AUXILIARY_CONSTRUCTION");
      });
      targetIds = authFirst.length > 0 ? [...authFirst] : [...nonDupCreated];
    } else {
      const lastEvObj = orderedSemanticScene.events[anchor]?.object;
      targetIds = lastEvObj && outById.has(lastEvObj) ? [lastEvObj] : [];
    }

    const rawPrereqs = new Set<string>();
    for (const tId of targetIds) {
      const tObj = outById.get(tId);
      if (!tObj) continue;
      const baseHostForPrereq = tObj.type === "circle3" ? hostCurvedSolidForBaseCircle(orderedSemanticScene, tObj) : null;
      for (const depId of tObj.depends ?? []) {
        if (baseHostForPrereq && depId === baseHostForPrereq.id) continue;
        if (unit.absorbedAuxIds.includes(depId) || dupPlaneIds.has(depId) || measOnlyIds.has(depId)) {
          const auxObj = outById.get(depId);
          for (const subDep of auxObj?.depends ?? []) {
            if (accumulatedPriorIds.has(subDep)) rawPrereqs.add(subDep);
          }
          // Nếu đường phụ trùng hai đầu mút với một cạnh bên đã dựng (vd `canh_ben_S_D`), ghi nhận thêm cạnh đó làm tiên quyết
          const auxDeps = auxObj?.depends ?? [];
          if (auxDeps.length === 2) {
            const matchingEdge = orderedSemanticScene.objects.find(
              (cand) =>
                cand.type === "segment3"
                && accumulatedPriorIds.has(cand.id)
                && (cand.depends ?? []).length === 2
                && cand.depends.includes(auxDeps[0])
                && cand.depends.includes(auxDeps[1]),
            );
            if (matchingEdge) rawPrereqs.add(matchingEdge.id);
          }
        } else if (accumulatedPriorIds.has(depId)) {
          rawPrereqs.add(depId);
        }
      }
      if (tObj.perpendicular_witness?.on && accumulatedPriorIds.has(tObj.perpendicular_witness.on)) {
        rawPrereqs.add(tObj.perpendicular_witness.on);
      }
      // Với điểm dựng trên cạnh bên / đỉnh khối (vd `M` trung điểm `SC`), ghi nhận cạnh bên / khối chủ đã tồn tại làm tiên quyết
      if (tObj.type === "point3" && (tObj.depends ?? []).length === 2) {
        const [d0, d1] = tObj.depends;
        const carrierSeg = orderedSemanticScene.objects.find(
          (cand) =>
            cand.type === "segment3"
            && accumulatedPriorIds.has(cand.id)
            && (cand.depends ?? []).length === 2
            && cand.depends.includes(d0)
            && cand.depends.includes(d1),
        );
        if (carrierSeg) rawPrereqs.add(carrierSeg.id);
        const carrierSolid = orderedSemanticScene.objects.find(
          (cand) =>
            cand.type === "solid"
            && accumulatedPriorIds.has(cand.id)
            && [...(cand.vertex_ids ?? []), ...(cand.depends ?? [])].includes(d0)
            && [...(cand.vertex_ids ?? []), ...(cand.depends ?? [])].includes(d1),
        );
        if (carrierSolid) rawPrereqs.add(carrierSolid.id);
      }
      if (
        ((tObj.surface_role === "BASE_REGION" || (tObj.formation_roles ?? []).includes("CONSTRUCT_BASE"))
          && !isPolyhedronLateralOrAuxFacePolygon(orderedSemanticScene, tObj))
        || baseHostForPrereq
      ) {
        // Mặt đáy ở bước đầu lấy các đỉnh/tâm đáy và bán kính/trục đã dựng trong `accumulatedPriorIds`
        for (const depId of tObj.depends ?? []) {
          if (baseHostForPrereq && (depId === baseHostForPrereq.id || dupPlaneIds.has(depId))) continue;
          if (accumulatedPriorIds.has(depId)) rawPrereqs.add(depId);
        }
        if (tObj.type === "circle3") {
          const host = baseHostForPrereq;
          if (host) {
            for (const cand of orderedSemanticScene.objects) {
              if (!accumulatedPriorIds.has(cand.id)) continue;
              if (cand.type === "segment3" && classifyCurvedSegmentRole(orderedSemanticScene, cand)?.host.id === host.id) {
                rawPrereqs.add(cand.id);
              }
            }
          }
        }
      } else if (tObj.type === "solid") {
        for (const cand of orderedSemanticScene.objects) {
          const cr = cand.formation_roles ?? [];
          if (
            accumulatedPriorIds.has(cand.id)
            && !isPolyhedronLateralOrAuxFacePolygon(orderedSemanticScene, cand)
            && (
              cand.surface_role === "BASE_REGION"
              || cr.includes("CONSTRUCT_BASE")
              || cr.includes("CONSTRUCT_HEIGHT")
              || cr.includes("CONSTRUCT_LATERAL_BOUNDARY")
              || cr.includes("CONSTRUCT_TRANSLATED_FACE")
            )
            && (cand.depends ?? []).every((d) => [...(tObj.vertex_ids ?? []), ...(tObj.depends ?? [])].includes(d))
          ) {
            rawPrereqs.add(cand.id);
          }
        }
      } else if (tObj.type === "curved_solid") {
        for (const cand of orderedSemanticScene.objects) {
          if (!accumulatedPriorIds.has(cand.id)) continue;
          if (cand.type === "circle3" && hostCurvedSolidForBaseCircle(orderedSemanticScene, cand)?.id === tObj.id) {
            rawPrereqs.add(cand.id);
          } else if (cand.type === "segment3" && classifyCurvedSegmentRole(orderedSemanticScene, cand)?.host.id === tObj.id) {
            rawPrereqs.add(cand.id);
          }
        }
      } else if (tObj.type === "plane3" && (tObj.depends ?? []).length === 0) {
        for (const cand of orderedSemanticScene.objects) {
          const cDeps = cand.depends ?? [];
          if (!cDeps.includes(tObj.id)) continue;
          for (const otherId of cDeps) {
            if (otherId === tObj.id || !accumulatedPriorIds.has(otherId)) continue;
            rawPrereqs.add(otherId);
            const otherObj = outById.get(otherId);
            for (const subId of otherObj?.depends ?? []) {
              if (accumulatedPriorIds.has(subId) && outById.get(subId)?.type !== "quantity") {
                rawPrereqs.add(subId);
              }
            }
          }
        }
      }
    }
    for (const selfId of targetIds) rawPrereqs.delete(selfId);
    if (unit.conclusionQuantityIds.length > 0) {
      for (const tId of targetIds) {
        if (accumulatedPriorIds.has(tId)) rawPrereqs.add(tId);
      }
    }
    const prerequisiteIds = [...rawPrereqs];

    // Phân loại nhận thức (`given` | `derived` | `constructed` | `auxiliary` | `conclusion`) + tên phép dựng + tiền đề toán học
    const primaryObj = targetIds[0] ? outById.get(targetIds[0]) : undefined;
    let epistemicCategory: PedagogicalEpistemicCategory = "constructed";
    let operation = "Thực hiện bước dựng hình học";
    let premise = nar.subtitle || nar.title;

    if (unit.conclusionQuantityIds.length > 0) {
      epistemicCategory = "given";
      operation = "Quan sát cấu hình hình học từ dữ kiện đề bài";
      premise = nar.subtitle || nar.title;
    } else if (unit.closeSectionId && primaryObj?.type === "section") {
      epistemicCategory = "derived";
      operation = unit.extendSectionId
        ? "Tìm giao tuyến trên các mặt và khép kín miền đa giác thiết diện"
        : "Khép kín các đoạn giao tuyến thành miền đa giác thiết diện";
      const basis = deriveExactPolygonMathBasis(orderedSemanticScene, primaryObj);
      premise = basis?.supportingPremises.length
        ? basis.supportingPremises.join("; ")
        : "Các đoạn giao tuyến liên tiếp trên bề mặt khối tạo thành chu trình phẳng khép kín";
    } else if (unit.extendSectionId && primaryObj?.type === "section") {
      epistemicCategory = "derived";
      operation = "Tìm giao tuyến của mặt phẳng cắt với các mặt của khối";
      premise = "Hai mặt phẳng phân biệt có điểm chung cắt nhau theo một giao tuyến thẳng trên từng mặt bên / mặt đáy";
    } else if (primaryObj) {
      const roles = primaryObj.formation_roles ?? [];
      const isPureLateralFrame =
        targetIds.length > 0
        && targetIds.every((id) => {
          const o = outById.get(id);
          const r = o?.formation_roles ?? [];
          return o?.type === "segment3" && r.includes("CONSTRUCT_LATERAL_BOUNDARY") && !r.includes("CONSTRUCT_HEIGHT");
        });
      const hostSolidForUnit = orderedSemanticScene.objects.find((s) => s.type === "solid" && !isSubEntity(s.id));
      const isHostSolidIllustrative = (solObj: SceneObject | undefined): boolean => {
        if (!solObj) return false;
        const exactScene = exactSceneOriginOf(orderedSemanticScene);
        const exactById = new Map(exactScene.objects.map((o) => [o.id, o]));
        const exSol = exactById.get(solObj.id) ?? solObj;
        const vIds = [...new Set([...(exSol.vertex_ids ?? []), ...(exSol.depends ?? [])])].filter(
          (id) => exactById.get(id)?.type === "point3",
        );
        const hasExplicitIllustrative = [exSol, ...vIds.map((id) => exactById.get(id))].some((o) => {
          const src = o?.source as Record<string, unknown> | undefined;
          return Boolean(
            src
              && (src.is_given === false
                || src.provenance === "UNVERIFIED"
                || src.assumption === "UNVERIFIED"
                || src.provenance === "ILLUSTRATIVE_CHOICE"
                || src.assumption === "ILLUSTRATIVE_CHOICE"
                || src.provenance === "ILLUSTRATIVE_CONFIGURATION"
                || src.assumption === "ILLUSTRATIVE_CONFIGURATION"
                || src.provenance === "MODEL_ASSUMPTION"
                || src.assumption === "MODEL_ASSUMPTION"),
          );
        });
        if (hasExplicitIllustrative) return true;
        const basePoly = orderedSemanticScene.objects.find(
          (p) =>
            p.type === "polygon3"
            && (p.surface_role === "BASE_REGION" || (p.formation_roles ?? []).includes("CONSTRUCT_BASE"))
            && !(p.formation_roles ?? []).includes("CONSTRUCT_TRANSLATED_FACE")
            && !isPolyhedronLateralOrAuxFacePolygon(orderedSemanticScene, p),
        );
        if (basePoly) {
          const bp = classifyPolygonShapeWithProvenance(orderedSemanticScene, basePoly);
          if (bp.certifiedShape && (bp.provenance === "GIVEN" || bp.provenance === "DERIVED_VERIFIED")) {
            return false;
          }
          if (bp.provenance === "ILLUSTRATIVE_CHOICE" || bp.provenance === "UNVERIFIED") {
            return true;
          }
        }
        return vIds.some((id) => hasUncertifiedObjectSource(exactById.get(id)));
      };
      if (isPureLateralFrame) {
        epistemicCategory = isHostSolidIllustrative(hostSolidForUnit) ? "constructed" : "given";
        operation = "Dựng bộ khung các cạnh bên của khối đa diện";
        premise = nar.subtitle || "Nối các đỉnh đã xác định để tạo bộ khung cạnh bên";
      } else if (primaryObj.type === "circle3" && Boolean(hostCurvedSolidForBaseCircle(orderedSemanticScene, primaryObj))) {
        const hostCurved = hostCurvedSolidForBaseCircle(orderedSemanticScene, primaryObj)!;
        const hostOrtho = inspectAxialCurvedOrthogonality(orderedSemanticScene, hostCurved);
        const isIllustrativeBaseCircle =
          isNonAuthoritativeNonFoundation(primaryObj)
          || hasUncertifiedObjectSource(primaryObj)
          || hostCurved.authoritative === false
          || hasUncertifiedObjectSource(hostCurved)
          || Boolean(hostOrtho.isIllustrativeBasePlane);
        epistemicCategory = isIllustrativeBaseCircle ? "constructed" : "given";
        operation = "Dựng đường tròn mặt đáy của khối tròn xoay";
        premise = isIllustrativeBaseCircle
          ? (nar.subtitle || "Mặt phẳng đáy minh họa phù hợp với dữ kiện tâm và điểm thuộc đường tròn đáy")
          : (nar.subtitle || "Tâm và bán kính đáy theo giả thiết đề bài");
      } else if (primaryObj.type === "polygon3" && roles.includes("CONSTRUCT_TRANSLATED_FACE")) {
        epistemicCategory = isHostSolidIllustrative(hostSolidForUnit) ? "constructed" : "given";
        operation = "Tịnh tiến mặt đáy xác định mặt đáy đối diện của lăng trụ";
        premise = nar.subtitle || "Hai mặt đáy của hình lăng trụ nằm trên hai mặt phẳng song song và bằng nhau";
      } else if (
        primaryObj.type === "segment3"
        && classifyCurvedSegmentRole(orderedSemanticScene, primaryObj)
        && isPrimaryCurvedSolid(orderedSemanticScene, classifyCurvedSegmentRole(orderedSemanticScene, primaryObj)!.host)
        && classifyCurvedSegmentRole(orderedSemanticScene, primaryObj)!.kind !== "generator"
        && classifyCurvedSegmentRole(orderedSemanticScene, primaryObj)!.kind !== "altitude"
        && !(primaryObj.perpendicular_witness?.on && outById.get(primaryObj.perpendicular_witness.on)?.type === "plane3")
      ) {
        const cSeg = classifyCurvedSegmentRole(orderedSemanticScene, primaryObj)!;
        const cSegHostOrtho = inspectAxialCurvedOrthogonality(orderedSemanticScene, cSeg.host);
        const hasBundledIllustrativeCircle = targetIds.some((tid) => {
          const t = outById.get(tid);
          return Boolean(
            t
            && t.type === "circle3"
            && (isNonAuthoritativeNonFoundation(t) || hasUncertifiedObjectSource(t)),
          );
        });
        const isIllustrativeCurvedSeg =
          isNonAuthoritativeNonFoundation(primaryObj)
          || hasUncertifiedObjectSource(primaryObj)
          || cSeg.host.authoritative === false
          || hasUncertifiedObjectSource(cSeg.host)
          || Boolean(cSegHostOrtho.isIllustrativeBasePlane)
          || hasBundledIllustrativeCircle;
        epistemicCategory = isIllustrativeCurvedSeg ? "constructed" : "given";
        operation =
          cSeg.kind === "axis"
            ? "Xác định trục của khối tròn xoay"
            : cSeg.kind === "center_line"
              ? "Nối tâm hai mặt đáy của hình trụ xiên"
              : "Dựng bán kính từ tâm tới điểm thuộc đường tròn đáy / mặt cầu";
        premise = nar.subtitle || nar.title;
      } else if (primaryObj.type === "polygon3" && isPolyhedronLateralOrAuxFacePolygon(orderedSemanticScene, primaryObj)) {
        epistemicCategory = isHostSolidIllustrative(hostSolidForUnit) ? "constructed" : "given";
        operation = "Xác định mặt bên của khối đa diện";
        premise = nar.subtitle || "Mặt bên đi qua các đỉnh đã xác định của khối đa diện";
      } else if (primaryObj.surface_role === "BASE_REGION" || roles.includes("CONSTRUCT_BASE")) {
        if (primaryObj.type === "polygon3") {
          const baseProv = classifyPolygonShapeWithProvenance(orderedSemanticScene, primaryObj);
          const isCertBase =
            Boolean(baseProv.certifiedShape)
            && (baseProv.provenance === "GIVEN" || baseProv.provenance === "DERIVED_VERIFIED");
          epistemicCategory = isCertBase ? "given" : "constructed";
          operation = "Dựng đa giác mặt đáy";
          premise = isCertBase
            ? `Giả thiết hình dạng mặt đáy đề bài cho (${nar.title.replace(/^Dựng\s+/iu, "")})`
            : (nar.subtitle || "Xác định mặt phẳng đáy từ các đỉnh của đề bài (hình dạng cụ thể trên khung là cấu hình minh họa)");
        } else {
          const isIllustrativeBase =
            isNonAuthoritativeNonFoundation(primaryObj)
            || hasUncertifiedObjectSource(primaryObj)
            || isHostSolidIllustrative(hostSolidForUnit);
          epistemicCategory = isIllustrativeBase ? "constructed" : "given";
          operation = "Dựng mặt đáy cơ sở";
          premise = isIllustrativeBase
            ? (nar.subtitle || "Mặt đáy cơ sở được dựng theo cấu hình minh họa phù hợp dữ kiện đề bài")
            : `Giả thiết hình dạng mặt đáy đề bài cho (${nar.title.replace(/^Dựng\s+/iu, "")})`;
        }
      } else if (roles.includes("CONSTRUCT_HEIGHT")) {
        const fromPt = primaryObj.perpendicular_witness?.from ? outById.get(primaryObj.perpendicular_witness.from) : undefined;
        const footPt = primaryObj.perpendicular_witness?.foot_id ? outById.get(primaryObj.perpendicular_witness.foot_id) : undefined;
        const primarySrc = primaryObj.source as Record<string, unknown> | undefined;
        const isTheoremDerivedAltitude =
          primaryObj.perpendicular_witness?.rule === "regular_pyramid_center_altitude"
          || primarySrc?.instruction === "EXPLANATORY_DERIVED_WITNESS";
        const isGivenHeight =
          !isTheoremDerivedAltitude
          && primaryObj.authoritative !== false
          && !hasUncertifiedObjectSource(primaryObj)
          && (!fromPt || isCertifiedGivenSceneObject(orderedSemanticScene, fromPt))
          && (!footPt || isCertifiedGivenSceneObject(orderedSemanticScene, footPt));
        epistemicCategory = isTheoremDerivedAltitude ? "derived" : isGivenHeight ? "given" : "constructed";
        operation = "Dựng đường cao vuông góc với mặt phẳng đáy";
        premise = nar.subtitle || `Giả thiết vuông góc ${shortSym(primaryObj)} ⊥ mặt đáy`;
      } else if (primaryObj.type === "solid") {
        const solidIsIllustrative = primaryObj.authoritative === false || isHostSolidIllustrative(primaryObj);
        epistemicCategory = solidIsIllustrative ? "constructed" : "given";
        operation = "Nối các cạnh và mặt để hoàn thiện khối đa diện";
        premise = solidIsIllustrative
          ? `Các đỉnh và mặt cơ sở của ${shortSym(primaryObj)} đã dựng (tọa độ cụ thể trên khung là cấu hình minh họa thỏa mãn giả thiết)`
          : `Các đỉnh và mặt cơ sở của ${shortSym(primaryObj)} đã được xác định`;
      } else if (primaryObj.type === "curved_solid") {
        const hasPriorCurvedHost = [...accumulatedPriorIds].some(
          (id) => id !== primaryObj.id && outById.get(id)?.type === "curved_solid",
        );
        const derivedFromCut =
          hasPriorCurvedHost
          || isSecondaryCutCurvedSolid(orderedSemanticScene, primaryObj)
          || (primaryObj.depends ?? []).some((d) => {
            const dObj = outById.get(d);
            if (!dObj || dObj.origin !== "derived") return false;
            if (dObj.surface_role === "BASE_REGION") return false;
            if (dObj.type === "circle3" && hostCurvedSolidForBaseCircle(orderedSemanticScene, dObj)?.id === primaryObj.id) {
              return false;
            }
            return true;
          });
        const curvedOrtho = inspectAxialCurvedOrthogonality(orderedSemanticScene, primaryObj);
        const isIllustrativeCurved =
          primaryObj.authoritative === false
          || hasUncertifiedObjectSource(primaryObj)
          || Boolean(curvedOrtho.isIllustrativeBasePlane);
        epistemicCategory = derivedFromCut ? "derived" : isIllustrativeCurved ? "constructed" : "given";
        operation = derivedFromCut
          ? "Xác định khối tròn xoay thành phần tạo bởi mặt phẳng cắt"
          : "Hoàn thiện mặt cong của khối tròn xoay";
        premise = derivedFromCut
          ? "Mặt phẳng cắt tách khối tròn xoay thành phần theo thiết diện tương ứng"
          : isIllustrativeCurved
            ? (nar.subtitle || "Hoàn thiện mặt cong theo cấu hình minh họa phù hợp dữ kiện đề bài")
            : `Tâm, trục và bán kính của ${shortSym(primaryObj)} theo giả thiết đề bài`;
      } else if (targetIds.every((id) => outPhu.has(id))) {
        epistemicCategory = "auxiliary";
        operation = "Dựng đối tượng phụ hỗ trợ phép dựng";
        premise = nar.subtitle || "Đối tượng phụ trung gian phục vụ xác định giao điểm hoặc khoảng cách";
      } else if (primaryObj.type === "point3") {
        const centroidRel = findPointCentroidRelation(orderedSemanticScene, primaryObj);
        const midRel = findPointMidpointRelation(orderedSemanticScene, primaryObj);
        const interRel = findLinePlaneIntersectionMidpoint(orderedSemanticScene, primaryObj);
        if (centroidRel) {
          epistemicCategory = isCertifiedGivenSceneObject(orderedSemanticScene, primaryObj) ? "given" : "constructed";
          operation = "Xác định trọng tâm của tam giác";
          premise = `Ba đỉnh ${centroidRel.vertexSyms.join(", ")} tạo thành tam giác đã tồn tại`;
        } else if (interRel) {
          epistemicCategory = "derived";
          operation = interRel.isExterior
            ? "Kéo dài cạnh trên mặt đồng phẳng để tìm giao điểm với mặt phẳng cắt"
            : "Xác định giao điểm của đường thẳng và mặt phẳng";
          premise = `Đường thẳng ${interRel.lineSym} cắt mặt phẳng ${interRel.planeSym} tại điểm duy nhất`;
        } else if (midRel?.kind === "midpoint") {
          epistemicCategory = isCertifiedGivenSceneObject(orderedSemanticScene, primaryObj) ? "given" : "constructed";
          operation = "Xác định trung điểm của đoạn thẳng";
          premise = `Đoạn thẳng ${midRel.aSym}${midRel.bSym} đã tồn tại trên hình dựng`;
        } else if (midRel?.kind === "symmetric") {
          epistemicCategory = "constructed";
          operation = "Xác định điểm đối xứng tâm";
          premise = `Tâm đối xứng ${midRel.centerSym} và điểm ${midRel.aSym} đã xác định`;
        } else if (midRel?.kind === "ratio" && midRel.ratioFrac) {
          epistemicCategory = isCertifiedGivenSceneObject(orderedSemanticScene, primaryObj) ? "given" : "constructed";
          operation = "Chia đoạn thẳng theo tỉ số đã cho";
          premise = `Đoạn thẳng ${midRel.aSym}${midRel.bSym} đã tồn tại; tỉ số ${fmtFrac(midRel.ratioFrac)} đề cho`;
        } else if (primaryObj.perpendicular_witness) {
          epistemicCategory = "constructed";
          operation = "Hạ hình chiếu vuông góc";
          premise = "Qua một điểm ngoài đường thẳng / mặt phẳng xác định duy nhất hình chiếu vuông góc";
        } else {
          const diagRel = findPolygonDiagonalIntersectionRelation(orderedSemanticScene, primaryObj);
          const lineDeps = (primaryObj.depends ?? []).filter((d) => {
            const dt = outById.get(d)?.type;
            return dt === "line3" || dt === "segment3";
          });
          if (diagRel) {
            epistemicCategory = "derived";
            operation = "Xác định giao điểm của hai đường chéo đồng phẳng";
            premise = `Hai đường chéo ${diagRel.d1Sym} và ${diagRel.d2Sym} đồng phẳng cắt nhau tại điểm duy nhất`;
          } else if (lineDeps.length === 2) {
            epistemicCategory = "derived";
            operation = "Xác định giao điểm của hai đường thẳng đồng phẳng";
            premise = "Hai đường thẳng đồng phẳng không song song cắt nhau tại điểm duy nhất";
          } else {
            epistemicCategory = "constructed";
            operation = "Xác định điểm theo quan hệ hình học";
          }
        }
      } else if (primaryObj.type === "plane3") {
        const isAux = outPhu.has(primaryObj.id);
        epistemicCategory = isAux ? "auxiliary" : "constructed";
        operation = "Xác định mặt phẳng";
        premise = nar.subtitle || "Ba điểm không thẳng hàng hoặc đường thẳng và quan hệ vuông góc xác định duy nhất mặt phẳng";
      } else if ((primaryObj.type === "circle3" || primaryObj.type === "ellipse3") && vaiTroMien(primaryObj) === "section") {
        epistemicCategory = "derived";
        operation = "Xác định đường cong giao tuyến phẳng với khối tròn xoay";
        premise = describeExactCurvedSectionMath(orderedSemanticScene, primaryObj)
          ?? "Mặt phẳng cắt khối tròn xoay theo đường cong giao tuyến phẳng";
      } else if (
        primaryObj.type === "polygon3"
        && vaiTroMien(primaryObj) === "section"
        && !isPolyhedronLateralOrAuxFacePolygon(orderedSemanticScene, primaryObj)
      ) {
        epistemicCategory = "derived";
        operation = "Dựng miền đa giác thiết diện";
        const basis = deriveExactPolygonMathBasis(orderedSemanticScene, primaryObj);
        premise = basis?.supportingPremises.length ? basis.supportingPremises.join("; ") : nar.subtitle;
      } else if (primaryObj.type === "polygon3" && isPolyhedronLateralOrAuxFacePolygon(orderedSemanticScene, primaryObj)) {
        epistemicCategory = "constructed";
        operation = "Xác định mặt bên của khối đa diện";
        premise = nar.subtitle || "Mặt phẳng bên xác định từ đỉnh và cạnh đáy tương ứng của khối đa diện";
      } else if (primaryObj.type === "segment3" || primaryObj.type === "line3") {
        const isInter = isIntersectionLineOrSegment(primaryObj, orderedSemanticScene);
        const cRole = classifyCurvedSegmentRole(orderedSemanticScene, primaryObj);
        const segW = primaryObj.perpendicular_witness ?? primaryObj.annotation?.witness;
        const pSrcInst = (primaryObj.source as Record<string, unknown> | undefined)?.instruction;
        if (segW?.relation === "common_perpendicular") {
          epistemicCategory = "derived";
          operation = "Xác định đoạn vuông góc chung của hai đường thẳng chéo nhau";
          premise = nar.subtitle || "Đoạn nối hai chân vuông góc thỏa đồng thời hai điều kiện vuông góc chính xác";
        } else if ((isExplanatoryPerpSegment(primaryObj) || pSrcInst === "EXPLANATORY_DERIVED_WITNESS") && !isExplanatoryTargetSegment(primaryObj) && segW?.on) {
          epistemicCategory = "derived";
          operation = "Hạ đoạn vuông góc từ điểm đến mặt phẳng / đường thẳng";
          premise = nar.subtitle || "Đoạn vuông góc hạ từ điểm đến hình chiếu vuông góc trên mặt phẳng / đường thẳng";
        } else if (
          cRole?.kind === "radius"
          && cRole.host.curved_kind === "ball"
          && segW?.on
          && outById.get(segW.on)?.type === "plane3"
        ) {
          epistemicCategory = "derived";
          operation = "Hạ bán kính vuông góc xác định tiếp điểm mặt cầu và mặt phẳng";
          premise = nar.subtitle || "Khoảng cách từ tâm mặt cầu đến mặt phẳng bằng bán kính mặt cầu";
        } else if (isExplanatoryTargetSegment(primaryObj)) {
          epistemicCategory = "derived";
          operation = "Nối hai điểm đã xác định tạo đoạn thẳng mục tiêu";
          premise = nar.subtitle || "Hai đầu mút của đoạn mục tiêu đã được xác định hợp lệ trên hình";
        } else {
          epistemicCategory = isInter ? "derived" : outPhu.has(primaryObj.id) ? "auxiliary" : "constructed";
          operation = isInter
            ? "Xác định giao tuyến của hai mặt phẳng"
            : cRole?.kind === "generator"
              ? "Nối đường sinh của khối tròn xoay"
              : cRole?.kind === "altitude"
                ? "Hạ chiều cao vuông góc với mặt phẳng đáy của hình trụ xiên"
                : primaryObj.type === "segment3"
                  ? "Nối hai điểm tạo đoạn thẳng"
                  : "Dựng đường thẳng đi qua hai điểm";
        }
      }
    }

    for (const vId of visibleIds) accumulatedPriorIds.add(vId);
    for (const tId of targetIds) accumulatedPriorIds.add(tId);

    const cleanTitle = nar.title.replace(/«([^»]+)»/gu, "$1");
    let stepRole: PedagogicalStepRole = "construct_geometry";
    if (
      unit.closeSectionId
      || unit.extendSectionId
      || (primaryObj
        && (
          primaryObj.type === "section"
          || (
            (primaryObj.type === "circle3" || primaryObj.type === "ellipse3" || primaryObj.type === "polygon3")
            && vaiTroMien(primaryObj) === "section"
            && !(primaryObj.type === "polygon3" && isPolyhedronLateralOrAuxFacePolygon(orderedSemanticScene, primaryObj))
          )
          || isIntersectionLineOrSegment(primaryObj, orderedSemanticScene)
          || (primaryObj.type === "point3" && String(primaryObj.producer ?? "").includes("intersect"))
        ))
    ) {
      stepRole = "construct_intersection_or_section";
    } else if (
      isExplanatoryTargetSegment(primaryObj)
      || /^Xác định (?:đường thẳng chứa cạnh|cạnh .* trên khối đã dựng)/u.test(cleanTitle)
    ) {
      stepRole = "emphasize_result";
    } else if (epistemicCategory === "auxiliary" || (primaryObj && outPhu.has(primaryObj.id))) {
      stepRole = "identify_auxiliary";
    } else if (epistemicCategory === "derived") {
      stepRole = "deduce_relation";
    } else if (epistemicCategory === "given") {
      stepRole = "identify_given";
    }

    const conclusionProvs = unit.conclusionQuantityIds
      .map((qid) => byId.get(qid))
      .filter((qo): qo is SceneObject => Boolean(qo))
      .map((qo) => classifySceneEntityProvenance(orderedSemanticScene, qo));
    const weakestConclusionProv: CanonicalMathProvenance | null =
      conclusionProvs.length === 0
        ? null
        : conclusionProvs.includes("INVALID")
          ? "INVALID"
          : conclusionProvs.includes("UNDERDETERMINED")
            ? "UNDERDETERMINED"
            : conclusionProvs.includes("ILLUSTRATIVE")
              ? "ILLUSTRATIVE"
              : "DERIVED_VERIFIED";
    const objProv =
      weakestConclusionProv
      ?? (primaryObj ? classifySceneEntityProvenance(orderedSemanticScene, primaryObj) : "DERIVED_VERIFIED");
    const stepProvenance: CanonicalMathProvenance =
      epistemicCategory === "given" && objProv !== "ILLUSTRATIVE" && objProv !== "INVALID"
        ? "GIVEN"
        : objProv;

    const baseStepItem: PedagogicalStepItem = {
      index,
      startAnchor,
      anchor,
      label: nar.label.replace(/«([^»]+)»/gu, "$1"),
      title: cleanTitle,
      subtitle: nar.subtitle.replace(/«([^»]+)»/gu, "$1"),
      targetIds,
      prerequisiteIds,
      operation: operation.replace(/«([^»]+)»/gu, "$1"),
      premise: premise.replace(/«([^»]+)»/gu, "$1"),
      visibleIds,
      epistemicCategory,
      categoryLabel: PEDAGOGICAL_CATEGORY_LABELS[epistemicCategory],
      stepRole,
      stepRoleLabel: PEDAGOGICAL_STEP_ROLE_LABELS[stepRole],
      provenance: stepProvenance,
    };
    baseStepItem.narration = buildPedagogicalStepNarration(orderedSemanticScene, baseStepItem);
    return baseStepItem;
  });

  const goalCompletion = buildGoalCompletionSummary(orderedSemanticScene, steps);

  const plan: PedagogicalConstructionPlan = {
    scene: outScene,
    steps,
    dagEdges,
    reordered: needsRebuild,
    goalCompletion,
  };
  const outSig = outScene === rawScene ? rawSig : sceneCacheSignature(outScene);
  targetCache.set(rawScene, { plan, hybrid: currentHybrid, sig: rawSig });
  if (cleanInput !== rawScene) {
    targetCache.set(cleanInput, { plan, hybrid: currentHybrid, sig: sceneCacheSignature(cleanInput) });
  }
  if (rawExactOrigin !== rawScene && !hadSubEntities && rawExactOrigin.events.length === rawScene.events.length) {
    targetCache.set(rawExactOrigin, { plan, hybrid: currentHybrid, sig: sceneCacheSignature(rawExactOrigin) });
  }
  if (outScene !== rawScene) {
    const realizedPlan: PedagogicalConstructionPlan = { ...plan, reordered: false };
    targetCache.set(outScene, { plan: realizedPlan, hybrid: currentHybrid, sig: outSig });
    if (splitHeight) {
      _pedPlanNoSplitCache.set(outScene, { plan: realizedPlan, hybrid: currentHybrid, sig: outSig });
    }
  }
  return plan;
}

/**
 * Danh sách bước dựng sư phạm cho thanh bước & Study Dock (§3):
 * Ủy quyền toàn bộ sang `buildPedagogicalConstructionPlan(scene)` để mọi đường gọi đều nhận đúng trình tự tôpô DAG
 * và đầy đủ 7 trường siêu dữ liệu sư phạm, đồng thời giữ bất biến `anchor <= stepCount(scene) - 1` ngay cả khi caller
 * truyền trực tiếp `scene` gốc chưa tách sự kiện đường cao.
 */
export function pedagogicalStepList(scene: Scene3D): PedagogicalStepItem[] {
  const curHybrid = hybridViewOfScene(scene);
  const curSig = sceneCacheSignature(scene);
  const fromSplitPlan = _pedPlanCache.get(scene);
  if (fromSplitPlan && fromSplitPlan.hybrid === curHybrid && fromSplitPlan.sig === curSig && fromSplitPlan.plan.scene === scene) {
    return fromSplitPlan.plan.steps;
  }
  let ancestor: Scene3D | undefined = derivedSceneParentOf(scene);
  for (let depth = 0; ancestor && depth < 5; depth += 1) {
    if (ancestor.events.length === scene.events.length) {
      const ancSig = sceneCacheSignature(ancestor);
      const fromAnc = _pedPlanCache.get(ancestor) ?? _pedPlanNoSplitCache.get(ancestor);
      if (fromAnc && fromAnc.hybrid === curHybrid && fromAnc.sig === ancSig && fromAnc.plan.scene === ancestor) {
        return fromAnc.plan.steps;
      }
    }
    ancestor = derivedSceneParentOf(ancestor);
  }
  const exactOrigin = exactSceneOriginOf(scene);
  if (exactOrigin !== scene) {
    const exactSig = sceneCacheSignature(exactOrigin);
    const fromExactSplitPlan = _pedPlanCache.get(exactOrigin);
    if (fromExactSplitPlan && fromExactSplitPlan.hybrid === curHybrid && fromExactSplitPlan.sig === exactSig && fromExactSplitPlan.plan.scene === exactOrigin) {
      return fromExactSplitPlan.plan.steps;
    }
  }
  return buildPedagogicalConstructionPlan(scene, { splitBundledHeight: false }).steps;
}

export interface VerifiedObjectTooltip {
  header: string;
  body: string;
  accentHex: string;
}

export interface StudentObjectPresentation {
  title: string;
  role: string;
  description: string;
  evidence: string | null;
  accentHex: string;
  hasCanvasHoverTooltip: boolean;
}

function stripStudentSpoilerSuffix(raw: string | null | undefined): string {
  if (!raw) return "";
  const cleaned = cleanLearnerText(raw).replace(/\bDựng\s+khối\s+cầu\b/giu, (m) =>
    m[0] === "d" ? "dựng mặt cầu" : "Dựng mặt cầu",
  );
  const match = /\s*(?:⇒|->|=)\s*[-+(]*(?:\d|[√π]|\\sqrt|\\frac|(?:[ahb]\b|[aRhb](?=\s*[0-9√π^²³/*+-])))[^∩⊥∥;,]*$/u.exec(
    cleaned,
  );
  if (!match) return cleaned.trim();
  const prefix = cleaned.slice(0, match.index);
  let openParens = 0;
  for (const ch of prefix) {
    if (ch === "(") openParens += 1;
    else if (ch === ")" && openParens > 0) openParens -= 1;
  }
  // Không cắt biểu thức định danh nằm bên trong dấu ngoặc đơn chưa đóng (vd: `Đáy tròn (O; R = 2)`).
  if (openParens > 0) return cleaned.trim();
  return prefix.trim();
}

function formatCurvedSolidProseName(
  scene: Scene3D,
  solidObj: SceneObject,
  presentObjects: readonly SceneObject[],
): string {
  const explicitNot = cleanLearnerText(solidObj.notation);
  const exactScene = exactSceneOriginOf(scene);
  const exactById = new Map(exactScene.objects.map((o) => [o.id, o]));
  const eCs = exactById.get(solidObj.id) ?? solidObj;
  const findCenterPt = (): SceneObject | undefined => {
    if (!eCs.anchor) return undefined;
    const tv = parseFracVec3(eCs.anchor);
    return (
      presentObjects.find((p) => {
        if (isSubEntity(p.id) || p.type !== "point3" || !isCompactPointSym(shortSym(p))) return false;
        const ep = exactById.get(p.id) ?? p;
        return Boolean(ep.xyz && vIsZero(vSub(parseFracVec3(ep.xyz), tv)));
      })
      ?? scene.objects.find((p) => {
        if (isSubEntity(p.id) || p.type !== "point3" || !isCompactPointSym(shortSym(p))) return false;
        const ep = exactById.get(p.id) ?? p;
        return Boolean(ep.xyz && vIsZero(vSub(parseFracVec3(ep.xyz), tv)));
      })
    );
  };
  if (solidObj.curved_kind === "ball") {
    if (explicitNot) return `mặt cầu ${explicitNot}`;
    const cPt = findCenterPt();
    return cPt ? `mặt cầu tâm ${shortSym(cPt)}` : "mặt cầu";
  }
  if (solidObj.curved_kind === "cylinder") {
    const noun = inspectAxialCurvedOrthogonality(scene, solidObj).isOblique ? "hình trụ xiên" : "hình trụ";
    return explicitNot ? `${noun} ${explicitNot}` : noun;
  }
  if (solidObj.curved_kind === "cone") {
    return explicitNot ? `hình nón ${explicitNot}` : "hình nón";
  }
  return explicitNot || "khối tròn xoay";
}

function finalizeStudentObjectPresentation(raw: StudentObjectPresentation): StudentObjectPresentation {
  const title = stripStudentSpoilerSuffix(raw.title) || "Đối tượng hình học";
  const rawRole = stripStudentSpoilerSuffix(raw.role) || "Đối tượng";
  let role = rawRole.length <= 26 ? rawRole : truncateVietnameseWords(rawRole, 26);
  if (role.toLowerCase() === title.toLowerCase()) {
    role = /^Mặt\s+cầu|^Hình\s+(?:trụ|nón)/iu.test(title)
      ? "Khối tròn xoay"
      : /^Đường\s+tròn|^Elip/iu.test(title)
        ? "Đường cong phẳng"
        : /^Đoạn|^Đường|^Bán\s+kính|^Giao\s+tuyến|^Trục/iu.test(title)
          ? "Yếu tố tuyến tính"
          : /^Điểm|^Tâm|^Đỉnh|^Tiếp\s+điểm|^Hình\s+chiếu/iu.test(title)
            ? "Điểm hình học"
            : /^Thiết\s+diện|^Đa\s+giác|^Đáy|^Mặt/iu.test(title)
              ? "Miền phẳng"
              : title === "Đối tượng hình học"
                ? "Phần tử không gian"
                : "Đối tượng hình học";
  }
  let description = stripStudentSpoilerSuffix(raw.description);
  if (!description || description === title || description === role) {
    description = `${title} được xác định từ quan hệ hình học tại bước dựng hiện tại.`;
  }
  let evidence = raw.evidence ? stripStudentSpoilerSuffix(raw.evidence) : null;
  if (evidence && (evidence === description || evidence === title || evidence === role || description.includes(evidence))) {
    evidence = null;
  }
  return {
    title,
    role,
    description,
    evidence,
    accentHex: raw.accentHex,
    hasCanvasHoverTooltip: raw.hasCanvasHoverTooltip,
  };
}

/**
 * Hợp đồng trình bày chuẩn hóa cho mọi thẻ thông tin đối tượng (`.context-object-card`),
 * bảng soi (`BangNoi`), tooltip trên canvas (`.geo3d-math-tooltip`) và chip đối tượng (`§4`):
 * - `title`: tên toán học ngắn gọn, đúng ký hiệu của đề bài (không bịa `(S)` khi `notation === null`).
 * - `role`: vai trò phân loại ngắn gọn (`<= 26` ký tự), tuyệt đối không nhét cả câu giải thích vào badge.
 * - `description`: một đoạn/câu giải thích rõ ràng, không lặp nguyên văn `title` hay `role`, không rò rỉ đối tượng tương lai.
 * - `evidence`: quan hệ / căn cứ hình học bổ sung khi có, đã khử trùng lặp với `description`.
 */
export function resolveStudentObjectPresentation(
  rawScene: Scene3D,
  targetId: string | null | undefined,
  step?: number,
): StudentObjectPresentation | null {
  if (!targetId) return null;
  const k = clampStep(rawScene, step ?? Math.max(0, rawScene.events.length - 1));
  const presentObjs = objectsAt(rawScene, k);
  const presentIds = new Set(presentObjs.map((o) => o.id));
  const byId = new Map(rawScene.objects.map((o) => [o.id, o]));
  const exactScene = exactSceneOriginOf(rawScene);
  const exactById = new Map(exactScene.objects.map((o) => [o.id, o]));
  let obj = byId.get(targetId) ?? exactById.get(targetId);

  if (obj && isSubEntity(obj.id)) {
    const parentId = parentSolidOf(obj.id);
    const parentObj = parentId ? byId.get(parentId) : undefined;
    if (parentObj?.type === "section") {
      obj = parentObj;
    } else if (obj.type === "edge" && (obj.depends ?? []).length === 2) {
      const [u, v] = obj.depends;
      const semMatch = rawScene.objects.find((cand) =>
        !isSubEntity(cand.id)
        && presentIds.has(cand.id)
        && (cand.type === "segment3" || cand.type === "line3")
        && ((cand.endpoint_ids ?? cand.depends ?? []).length === 2)
        && (cand.endpoint_ids ?? cand.depends ?? []).includes(u)
        && (cand.endpoint_ids ?? cand.depends ?? []).includes(v)
        && (
          Boolean(cand.perpendicular_witness || cand.annotation?.witness)
          || (cand.formation_roles ?? []).includes("CONSTRUCT_HEIGHT")
          || isIntersectionLineOrSegment(cand, rawScene)
          || isPrimarySpatialLine(cand, rawScene)
        ),
      );
      if (semMatch) {
        obj = semMatch;
      } else {
        const uSym = shortSym(byId.get(u));
        const vSym = shortSym(byId.get(v));
        const edgeSym = uSym && vSym && isCompactPointSym(uSym) && isCompactPointSym(vSym) ? `${uSym}${vSym}` : cleanLearnerText(obj.label);
        return finalizeStudentObjectPresentation({
          title: edgeSym.startsWith("Cạnh") ? edgeSym : `Cạnh ${edgeSym}`,
          role: "Cạnh khối",
          description: uSym && vSym
            ? `Cạnh của khối đa diện nối hai đỉnh ${uSym} và ${vSym}.`
            : "Cạnh biên của khối đa diện.",
          evidence: null,
          accentHex: hexCss(S.colors.line),
          hasCanvasHoverTooltip: false,
        });
      }
    } else if (obj.type === "face" && parentObj?.type === "solid") {
      const faceSet = new Set(obj.depends ?? []);
      const baseMatch = rawScene.objects.find((cand) =>
        !isSubEntity(cand.id)
        && presentIds.has(cand.id)
        && cand.type === "polygon3"
        && cand.surface_role === "BASE_REGION"
        && (cand.depends ?? []).length === faceSet.size
        && (cand.depends ?? []).every((d) => faceSet.has(d)),
      );
      if (baseMatch) {
        obj = baseMatch;
      } else {
        const vSyms = (obj.depends ?? []).map((id) => shortSym(byId.get(id))).filter(isCompactPointSym);
        const cyc = vSyms.length >= 3 ? formatCycleNotation(vSyms, preferredPointOrderForPolygon(rawScene, obj)) : null;
        return finalizeStudentObjectPresentation({
          title: cyc ? `Mặt ${cyc}` : cleanLearnerText(obj.label || "Mặt khối"),
          role: "Mặt khối",
          description: vSyms.length >= 3
            ? `Mặt biên của khối đa diện đi qua các đỉnh ${vSyms.join(", ")}.`
            : "Mặt biên của khối đa diện.",
          evidence: null,
          accentHex: hexCss(S.colors.surface),
          hasCanvasHoverTooltip: false,
        });
      }
    } else {
      return null;
    }
  }

  if (!obj) return null;
  const sem = classifySceneObjectSemantics(rawScene, obj, k);
  const accentHex = hexCss(sem.strokeColor);
  const groups = obj.display_group ?? [];

  if (obj.type === "point3") {
    const sym = shortSym(obj);
    if (groups.includes("sphere_foundation_ref")) {
      const centerPt = (obj.depends ?? [])
        .map((id) => byId.get(id))
        .find((p): p is SceneObject => Boolean(p && p.type === "point3"));
      const cSym = centerPt && isCompactPointSym(shortSym(centerPt)) ? shortSym(centerPt) : "";
      return finalizeStudentObjectPresentation({
        title: `Điểm tham chiếu ${sym}`,
        role: "Điểm phụ trợ",
        description: cSym
          ? `${sym} thuộc mặt cầu tâm ${cSym}, dùng để biểu diễn bán kính ${cSym}${sym} = R.`
          : `${sym} thuộc mặt cầu, dùng để biểu diễn độ mở bán kính R từ tâm.`,
        evidence: null,
        accentHex,
        hasCanvasHoverTooltip: true,
      });
    }

    if (
      groups.includes("sphere_plane_aux")
      || (obj as SceneObject & { auxiliary?: string }).auxiliary === "sphere_plane_aux"
    ) {
      const planeDep =
        (obj.depends ?? [])
          .map((id) => byId.get(id))
          .find((p): p is SceneObject => Boolean(p && p.type === "plane3" && presentIds.has(p.id)))
        ?? presentObjs.find((p): p is SceneObject => p.type === "plane3" && (p.formation_roles ?? []).includes("CONSTRUCT_CUTTING_OBJECT"));
      const pName = planeDep ? formatPlaneDisplayNotation(planeDep, rawScene) : "mặt phẳng cắt";
      const exAuxPt = exactById.get(obj.id) ?? obj;
      const pvAux = exAuxPt.xyz ? parseFracVec3(exAuxPt.xyz) : null;
      const hostBall =
        (obj.depends ?? [])
          .map((id) => byId.get(id))
          .find((b): b is SceneObject => Boolean(b && b.type === "curved_solid" && b.curved_kind === "ball"))
        ?? presentObjs.find((b): b is SceneObject => b.type === "curved_solid" && b.curved_kind === "ball");
      const exBall = hostBall ? (exactById.get(hostBall.id) ?? hostBall) : undefined;
      const ballCenterPt = exBall?.anchor
        ? presentObjs.find((p) => {
            if (isSubEntity(p.id) || p.type !== "point3" || !isCompactPointSym(shortSym(p))) return false;
            const ep = exactById.get(p.id) ?? p;
            return Boolean(ep.xyz && vIsZero(vSub(parseFracVec3(ep.xyz), parseFracVec3(exBall.anchor!))));
          })
        : undefined;
      const iSym = ballCenterPt ? shortSym(ballCenterPt) : "";
      const centerClause = iSym ? ` của tâm ${iSym}` : " của tâm mặt cầu";

      const isCircleCenter =
        Boolean(pvAux)
        && presentObjs.some((c) => {
          if (c.type !== "circle3") return false;
          const ec = exactById.get(c.id) ?? c;
          return Boolean(ec.center && vIsZero(vSub(pvAux!, parseFracVec3(ec.center))));
        });

      if (pvAux && exBall?.anchor && exBall.radius_sq) {
        const dVec = vSub(pvAux, parseFracVec3(exBall.anchor));
        const dSq = metricDot(dVec, dVec, exactScene.chart_metric);
        const rSq = parseExactFrac(exBall.radius_sq);
        const cmpDR = dSq[0] * rSq[1] - rSq[0] * dSq[1];
        if (fIsZero(dSq)) {
          // Mặt phẳng đi qua tâm I (d = 0): để khối `ballAsCenter` phía dưới trình bày chính xác `Tâm I`.
        } else if (isCircleCenter || cmpDR < 0n) {
          return finalizeStudentObjectPresentation({
            title: `Tâm ${sym}`,
            role: "Tâm giao tuyến",
            description: `Hình chiếu vuông góc${centerClause} lên ${pName}, là tâm của đường tròn giao tuyến.`,
            evidence: null,
            accentHex,
            hasCanvasHoverTooltip: true,
          });
        } else if (cmpDR > 0n) {
          return finalizeStudentObjectPresentation({
            title: `Hình chiếu ${sym}`,
            role: "Hình chiếu vuông góc",
            description: `Hình chiếu vuông góc${centerClause} lên ${pName} (khoảng cách lớn hơn bán kính nên mặt phẳng không cắt mặt cầu).`,
            evidence: null,
            accentHex,
            hasCanvasHoverTooltip: true,
          });
        } else {
          // cmpDR === 0n (d = R): phân biệt tiếp điểm khi không có đường tròn giao tuyến dương trên mặt phẳng này
          const hasPositiveCutCircle = presentObjs.some((c) => {
            if (c.type !== "circle3") return false;
            if (planeDep && !(c.depends ?? []).includes(planeDep.id)) return false;
            const ec = exactById.get(c.id) ?? c;
            return Boolean(ec.radius_sq && parseExactFrac(ec.radius_sq)[0] > 0n);
          });
          if (!hasPositiveCutCircle || Boolean(obj.perpendicular_witness)) {
            return finalizeStudentObjectPresentation({
              title: `Tiếp điểm ${sym}`,
              role: "Tiếp điểm",
              description: `Hình chiếu vuông góc${centerClause} lên ${pName}, nơi mặt cầu tiếp xúc với ${pName}.`,
              evidence: null,
              accentHex,
              hasCanvasHoverTooltip: true,
            });
          }
          return finalizeStudentObjectPresentation({
            title: `Điểm ${sym}`,
            role: "Điểm giao tuyến",
            description: `Điểm thuộc đường tròn giao tuyến của mặt cầu với mặt phẳng ${pName}.`,
            evidence: null,
            accentHex,
            hasCanvasHoverTooltip: true,
          });
        }
      } else if (isCircleCenter) {
        return finalizeStudentObjectPresentation({
          title: `Tâm ${sym}`,
          role: "Tâm giao tuyến",
          description: `Hình chiếu vuông góc${centerClause} lên ${pName}, là tâm của đường tròn giao tuyến.`,
          evidence: null,
          accentHex,
          hasCanvasHoverTooltip: true,
        });
      } else {
        return finalizeStudentObjectPresentation({
          title: `Điểm ${sym}`,
          role: "Điểm giao tuyến",
          description: `Điểm thuộc đường tròn giao tuyến của mặt cầu với mặt phẳng ${pName}.`,
          evidence: null,
          accentHex,
          hasCanvasHoverTooltip: true,
        });
      }
    }

    const midRel = findPointMidpointRelation(rawScene, obj);
    if (midRel?.kind === "midpoint") {
      return finalizeStudentObjectPresentation({
        title: `Điểm ${sym}`,
        role: "Trung điểm",
        description: `Trung điểm của ${midRel.aSym}${midRel.bSym} (${midRel.aSym}${sym} = ${sym}${midRel.bSym})`,
        evidence: null,
        accentHex,
        hasCanvasHoverTooltip: true,
      });
    }
    if (midRel?.kind === "symmetric" && midRel.centerSym) {
      return finalizeStudentObjectPresentation({
        title: `Điểm ${sym}`,
        role: "Điểm đối xứng",
        description: `Đối xứng với ${midRel.aSym} qua ${midRel.centerSym} (${midRel.centerSym}${midRel.aSym} = ${midRel.centerSym}${sym})`,
        evidence: null,
        accentHex,
        hasCanvasHoverTooltip: true,
      });
    }
    if (midRel?.kind === "ratio" && midRel.ratioFrac) {
      const seg = `${midRel.aSym}${midRel.bSym}`;
      return finalizeStudentObjectPresentation({
        title: `Điểm ${sym}`,
        role: "Điểm chia tỉ số",
        description: `Chia đoạn ${seg} theo tỉ số ${midRel.aSym}${sym}/${seg} = ${fmtFrac(midRel.ratioFrac)}`,
        evidence: null,
        accentHex,
        hasCanvasHoverTooltip: true,
      });
    }

    const centRel = findPointCentroidRelation(rawScene, obj);
    if (centRel) {
      const tri = centRel.vertexSyms.join("");
      const projFrom =
        obj.perpendicular_witness?.from && presentIds.has(obj.perpendicular_witness.from)
          ? byId.get(obj.perpendicular_witness.from)
          : undefined;
      const projSuffix = projFrom ? ` · hình chiếu vuông góc của ${shortSym(projFrom)} lên (${tri})` : "";
      const howDesc =
        centRel.constructionMode === "median_ratio" && centRel.medianVertexSym && centRel.oppositeEdgeSyms
          ? `chia đường trung tuyến từ ${centRel.medianVertexSym} tới trung điểm ${centRel.oppositeEdgeSyms.join("")} theo tỉ số 2/3`
          : "giao ba đường trung tuyến";
      return finalizeStudentObjectPresentation({
        title: `Điểm ${sym}`,
        role: "Trọng tâm",
        description: `Trọng tâm của tam giác ${tri} (${howDesc})${projSuffix}`,
        evidence: null,
        accentHex,
        hasCanvasHoverTooltip: true,
      });
    }

    const interRel = findLinePlaneIntersectionMidpoint(rawScene, obj);
    if (interRel) {
      const compactSym = isCompactPointSym(sym);
      const eqToken = compactSym
        ? `${sym} = ${interRel.lineSym} ∩ ${interRel.planeSym}`
        : `${interRel.lineSym} ∩ ${interRel.planeSym}`;
      let body = `Giao điểm của ${interRel.lineSym} và ${interRel.planeSym} (${eqToken})`;
      if (interRel.isCoincidentEndpoint && interRel.coincidentSym) {
        body = `Giao điểm ${interRel.lineSym} ∩ ${interRel.planeSym} · trùng đầu mút ${interRel.coincidentSym}`;
      } else if (interRel.isMidpoint && interRel.segA && interRel.segB) {
        body = compactSym
          ? `Giao điểm ${interRel.lineSym} ∩ ${interRel.planeSym} · trung điểm ${interRel.lineSym} (${interRel.segA}${sym} = ${sym}${interRel.segB})`
          : `Giao điểm ${interRel.lineSym} ∩ ${interRel.planeSym} · trung điểm của đoạn ${interRel.lineSym}`;
      } else if (interRel.isExterior && interRel.segA && interRel.segB) {
        const exPt = exactById.get(obj.id) ?? obj;
        const excludedFromSection =
          Boolean(exPt.xyz)
          && presentObjs.some((s) => {
            if (s.type !== "section") return false;
            const exSec = exactById.get(s.id) ?? s;
            return (
              (exSec.polygon?.length ?? 0) >= 3
              && !exSec.polygon!.some((vx) => vx.join("|") === exPt.xyz!.join("|"))
            );
          });
        body = excludedFromSection
          ? `Giao điểm ${interRel.lineSym} ∩ ${interRel.planeSym} · nằm trên cạnh ${interRel.lineSym} kéo dài ngoài miền khối (điểm phụ dựng giao tuyến, không phải đỉnh của thiết diện)`
          : `Giao điểm ${interRel.lineSym} ∩ ${interRel.planeSym} · kéo dài cạnh ${interRel.lineSym} (ngoài đoạn ${interRel.lineSym})`;
      } else if (
        interRel.isInterior
        && interRel.segA
        && interRel.ratioFrac
        && interRel.ratioFrac[0] > 0n
        && interRel.ratioFrac[0] < interRel.ratioFrac[1]
      ) {
        body = compactSym
          ? `Giao điểm ${interRel.lineSym} ∩ ${interRel.planeSym} (${interRel.segA}${sym}/${interRel.lineSym} = ${interRel.ratioFrac[0].toString()}/${interRel.ratioFrac[1].toString()})`
          : `Giao điểm ${interRel.lineSym} ∩ ${interRel.planeSym} (tỉ số ${interRel.ratioFrac[0].toString()}/${interRel.ratioFrac[1].toString()} tính từ ${interRel.segA})`;
      }
      return finalizeStudentObjectPresentation({
        title: compactSym ? `Giao điểm ${sym}` : "Giao điểm đường – mặt",
        role: interRel.isExterior ? "Giao điểm phụ" : "Giao điểm",
        description: body,
        evidence: null,
        accentHex,
        hasCanvasHoverTooltip: true,
      });
    }

    const exPtObj = exactById.get(obj.id) ?? obj;
    if (exPtObj.xyz) {
      const pv = parseFracVec3(exPtObj.xyz);
      const ballAsCenter = presentObjs.find((b) => {
        if (b.type !== "curved_solid" || b.curved_kind !== "ball") return false;
        const eb = exactById.get(b.id) ?? b;
        return Boolean(eb.anchor && vIsZero(vSub(pv, parseFracVec3(eb.anchor))));
      });
      if (ballAsCenter) {
        return finalizeStudentObjectPresentation({
          title: `Tâm ${sym}`,
          role: "Tâm mặt cầu",
          description: `Tâm cố định xác định vị trí của ${formatCurvedSolidProseName(rawScene, ballAsCenter, presentObjs)} trong không gian.`,
          evidence: null,
          accentHex,
          hasCanvasHoverTooltip: true,
        });
      }
      const ballAsRimGiven = presentObjs.find((b) => {
        if (b.type !== "curved_solid" || b.curved_kind !== "ball") return false;
        return (b.depends ?? []).includes(obj!.id);
      });
      if (ballAsRimGiven) {
        return finalizeStudentObjectPresentation({
          title: `Điểm ${sym}`,
          role: "Điểm thuộc mặt cầu",
          description: `Điểm đề cho nằm trên ${formatCurvedSolidProseName(rawScene, ballAsRimGiven, presentObjs)}, dùng để xác định độ mở bán kính.`,
          evidence: null,
          accentHex,
          hasCanvasHoverTooltip: true,
        });
      }
      const coneAsApex = presentObjs.find((c) => {
        if (c.type !== "curved_solid" || c.curved_kind !== "cone") return false;
        const ec = exactById.get(c.id) ?? c;
        const ap = ec.apex_or_top ?? (ec as SceneObject & { apex?: ExactVec3 | null }).apex;
        return Boolean(ap && vIsZero(vSub(pv, parseFracVec3(ap))));
      });
      if (coneAsApex) {
        return finalizeStudentObjectPresentation({
          title: `Đỉnh ${sym}`,
          role: "Đỉnh hình nón",
          description: "Đỉnh của hình nón nằm trên trục đối xứng của khối.",
          evidence: null,
          accentHex,
          hasCanvasHoverTooltip: true,
        });
      }
      const axialCenterHost = presentObjs.find((c) => {
        if (c.type !== "curved_solid" || (c.curved_kind !== "cylinder" && c.curved_kind !== "cone")) return false;
        const ec = exactById.get(c.id) ?? c;
        const ap = ec.apex_or_top ?? (ec as SceneObject & { apex?: ExactVec3 | null }).apex;
        return Boolean(
          (ec.anchor && vIsZero(vSub(pv, parseFracVec3(ec.anchor))))
          || (c.curved_kind === "cylinder" && ap && vIsZero(vSub(pv, parseFracVec3(ap)))),
        );
      });
      if (axialCenterHost) {
        return finalizeStudentObjectPresentation({
          title: `Tâm ${sym}`,
          role: "Tâm đường tròn đáy",
          description: `Tâm của mặt đáy tròn thuộc ${formatCurvedSolidProseName(rawScene, axialCenterHost, presentObjs)}.`,
          evidence: null,
          accentHex,
          hasCanvasHoverTooltip: true,
        });
      }
    }

    const heightAsFoot = presentObjs.find((h) => {
      if (!(h.formation_roles ?? []).includes("CONSTRUCT_HEIGHT")) return false;
      if (h.perpendicular_witness?.foot_id === obj!.id) return true;
      const exH = exactById.get(h.id) ?? h;
      return Boolean(exH.perpendicular_witness?.foot && exPtObj.xyz && exH.perpendicular_witness.foot.join("|") === exPtObj.xyz.join("|"));
    });
    const diagRel = findPolygonDiagonalIntersectionRelation(rawScene, obj, { allowHeightFoot: true });
    if (heightAsFoot) {
      const onObj = heightAsFoot.perpendicular_witness?.on ? byId.get(heightAsFoot.perpendicular_witness.on) : undefined;
      const onSym = onObj?.notation ? `(${onObj.notation.replace(/^[()]+|[()]+$/g, "")})` : "mặt đáy";
      return finalizeStudentObjectPresentation({
        title: `Điểm ${sym}`,
        role: "Chân đường cao",
        description: diagRel
          ? `Giao điểm hai đường chéo ${diagRel.d1Sym}, ${diagRel.d2Sym} · chân đường cao ${shortSym(heightAsFoot)} vuông góc với ${onSym}`
          : `Chân đường cao ${shortSym(heightAsFoot)} vuông góc với ${onSym}`,
        evidence: null,
        accentHex: hexCss(S.colors.line),
        hasCanvasHoverTooltip: true,
      });
    }
    if (diagRel) {
      return finalizeStudentObjectPresentation({
        title: `Giao điểm ${sym}`,
        role: "Tâm đa giác đáy",
        description: `Giao điểm hai đường chéo ${diagRel.d1Sym} và ${diagRel.d2Sym}${diagRel.polySym ? ` của mặt ${diagRel.polySym}` : ""}.`,
        evidence: null,
        accentHex,
        hasCanvasHoverTooltip: true,
      });
    }

    const perpWitnessSeg = presentObjs.find((s) => {
      if (s.type !== "segment3" && s.type !== "line3") return false;
      if ((s.formation_roles ?? []).includes("CONSTRUCT_HEIGHT")) return false;
      const pw = s.perpendicular_witness ?? s.annotation?.witness;
      if (!pw) return false;
      if (pw.foot_id === obj!.id) return true;
      const exS = exactById.get(s.id) ?? s;
      const exFoot = (exS.perpendicular_witness ?? exS.annotation?.witness)?.foot;
      return Boolean(exFoot && exPtObj.xyz && exFoot.join("|") === exPtObj.xyz.join("|"));
    });
    if (obj.perpendicular_witness || perpWitnessSeg) {
      const pw = obj.perpendicular_witness ?? perpWitnessSeg?.perpendicular_witness ?? perpWitnessSeg?.annotation?.witness;
      const fromObj = pw?.from && presentIds.has(pw.from) ? byId.get(pw.from) : undefined;
      const onObj = pw?.on && presentIds.has(pw.on) ? byId.get(pw.on) : undefined;
      const onSym = onObj ? formatPlaneDisplayNotation(onObj, rawScene) : "mặt phẳng";
      const isTangentSpherePt =
        Boolean(exPtObj.xyz)
        && presentObjs.some((b) => {
          if (b.type !== "curved_solid" || b.curved_kind !== "ball") return false;
          const eb = exactById.get(b.id) ?? b;
          if (!eb.anchor || !eb.radius_sq) return false;
          const diff = vSub(parseFracVec3(exPtObj.xyz!), parseFracVec3(eb.anchor));
          return fEq(metricDot(diff, diff, exactScene.chart_metric), parseExactFrac(eb.radius_sq));
        });
      return finalizeStudentObjectPresentation({
        title: isTangentSpherePt ? `Tiếp điểm ${sym}` : `Hình chiếu ${sym}`,
        role: isTangentSpherePt ? "Tiếp điểm" : "Hình chiếu vuông góc",
        description: isTangentSpherePt
          ? `Hình chiếu vuông góc${fromObj ? ` của tâm ${shortSym(fromObj)}` : ""} lên ${onSym}, nơi mặt cầu tiếp xúc với ${onSym}.`
          : `Hình chiếu vuông góc${fromObj ? ` của ${shortSym(fromObj)}` : ""} lên ${onSym}.`,
        evidence: null,
        accentHex,
        hasCanvasHoverTooltip: true,
      });
    }

    const heightAsApex = presentObjs.find((h) =>
      (h.formation_roles ?? []).includes("CONSTRUCT_HEIGHT")
      && h.perpendicular_witness?.from === obj!.id,
    );
    if (heightAsApex) {
      const onObj = heightAsApex.perpendicular_witness?.on ? byId.get(heightAsApex.perpendicular_witness.on) : undefined;
      const onSym = onObj?.notation ? `(${onObj.notation.replace(/^[()]+|[()]+$/g, "")})` : "mặt đáy";
      return finalizeStudentObjectPresentation({
        title: `Đỉnh ${sym}`,
        role: "Đỉnh khối",
        description: `${shortSym(heightAsApex)} ⊥ ${onSym}`,
        evidence: null,
        accentHex: hexCss(S.colors.line),
        hasCanvasHoverTooltip: true,
      });
    }

    const isSolidVertex = presentObjs.some(
      (s) =>
        (s.type === "solid" || (s.type === "polygon3" && s.surface_role === "BASE_REGION"))
        && ((s.vertex_ids ?? s.depends ?? []).includes(obj!.id)),
    );
    const cleanedRole = stripStudentSpoilerSuffix(obj.role);
    const hasSpecificRole = Boolean(cleanedRole && cleanedRole !== "Điểm" && cleanedRole !== cleanLearnerText(obj.label));
    if (isSolidVertex && !hasSpecificRole) {
      return finalizeStudentObjectPresentation({
        title: `Đỉnh ${sym}`,
        role: "Đỉnh khối",
        description: `Đỉnh ${sym} thuộc khung đa diện cho trong giả thiết bài toán.`,
        evidence: null,
        accentHex,
        hasCanvasHoverTooltip: false,
      });
    }
    return finalizeStudentObjectPresentation({
      title: isCompactPointSym(sym) ? `Điểm ${sym}` : cleanLearnerText(obj.label || sym),
      role: obj.origin === "free" ? "Điểm đề cho" : obj.authoritative === false ? "Điểm phụ trợ" : "Điểm dựng",
      description: hasSpecificRole
        ? cleanedRole
        : obj.origin === "free"
          ? `Điểm ${sym} được cho trước trong giả thiết bài toán.`
          : `Điểm ${sym} được dựng theo quan hệ hình học tại bước hiện tại.`,
      evidence: null,
      accentHex,
      hasCanvasHoverTooltip: hasSpecificRole,
    });
  }

  if (obj.type === "plane3") {
    const pName = formatPlaneDisplayNotation(obj, rawScene);
    const depPts = (obj.depends ?? [])
      .filter((id) => presentIds.has(id))
      .map((id) => byId.get(id))
      .filter((p): p is SceneObject => Boolean(p && p.type === "point3" && !laDiemPhuDungMatPhang(rawScene, p, byId) && isCompactPointSym(shortSym(p))));
    const parallelBase = findParallelBaseForPlane(rawScene, obj);
    let sanitizedPlaneRole = stripStudentSpoilerSuffix(obj.role);
    if (!isExplicitOxyzCoordinateScene(rawScene, obj) && /phương\s+trình/iu.test(sanitizedPlaneRole)) {
      const hasSphereInPresent = presentObjs.some((c) => c.type === "curved_solid" && c.curved_kind === "ball");
      sanitizedPlaneRole = hasSphereInPresent
        ? "Mặt phẳng xác định theo khoảng cách từ tâm mặt cầu đề cho"
        : "Mặt phẳng xác định theo vị trí hình học đề cho";
    }
    if (
      sanitizedPlaneRole === "Mặt phẳng"
      || sanitizedPlaneRole === "Mặt phẳng cắt"
      || sanitizedPlaneRole.toLowerCase() === `mặt phẳng ${pName}`.toLowerCase()
    ) {
      sanitizedPlaneRole = "";
    }
    let perpLineClause = "";
    const exPlane = exactById.get(obj.id) ?? obj;
    const perpLineDep = (obj.depends ?? [])
      .filter((id) => presentIds.has(id))
      .map((id) => byId.get(id))
      .find((d): d is SceneObject => Boolean(d && (d.type === "segment3" || d.type === "line3") && shortSym(d)));
    if (perpLineDep && exPlane.normal) {
      const exLn = exactById.get(perpLineDep.id) ?? perpLineDep;
      const lnDir = exLn.direction
        ? parseFracVec3(exLn.direction)
        : exLn.point_a && exLn.point_b
          ? vSub(parseFracVec3(exLn.point_b), parseFracVec3(exLn.point_a))
          : null;
      if (lnDir && !vIsZero(lnDir)) {
        const covN = parseFracVec3(exPlane.normal);
        // Pháp tuyến covector song song với G * lnDir ⇔ mọi vector v ⊥ lnDir theo metric G đều thỏa covN · v = 0
        const gLn: FracVec3 = exactScene.chart_metric
          ? (([0, 1, 2] as const).map((r) => {
              let acc: Frac = [0n, 1n];
              for (let c = 0; c < 3; c += 1) {
                acc = fAdd(acc, fMul(parseExactFrac(exactScene.chart_metric![r][c]), lnDir[c]));
              }
              return acc;
            }) as unknown as FracVec3)
          : lnDir;
        if (vParallel(covN, gLn)) {
          perpLineClause = `vuông góc với ${shortSym(perpLineDep)}`;
        }
      }
    }
    const body = depPts.length >= 3
      ? `Đi qua ba điểm ${depPts.map((p) => shortSym(p)).join(", ")}${parallelBase ? ` · song song với ${parallelBase}` : ""}`
      : sanitizedPlaneRole
        || (depPts.length === 1 && perpLineClause
          ? `Đi qua ${shortSym(depPts[0])} · ${perpLineClause}${parallelBase ? ` · song song với ${parallelBase}` : ""}`
          : depPts.length === 1 && parallelBase
            ? `Đi qua ${shortSym(depPts[0])} · song song với ${parallelBase}`
            : perpLineClause
              ? `Mặt phẳng ${perpLineClause}`
              : "");
    const isCutting = (obj.formation_roles ?? []).includes("CONSTRUCT_CUTTING_OBJECT");
    return finalizeStudentObjectPresentation({
      title: `Mặt phẳng ${pName}`,
      role: isCutting ? "Mặt phẳng cắt" : "Mặt phẳng",
      description: body || `Mặt phẳng ${pName} xác định từ các yếu tố hình học trong đề bài.`,
      evidence: null,
      accentHex: hexCss(S.colors.surface),
      hasCanvasHoverTooltip: Boolean(body),
    });
  }

  if (obj.type === "section") {
    const sd = sectionDetails(rawScene, obj.id);
    const prefOrder = preferredPointOrderForPolygon(rawScene, obj);
    const cyc = sd ? formatCycleNotation(sd.vertexNames, prefOrder) : null;
    const basis = deriveExactPolygonMathBasis(rawScene, obj);
    const shape = basis ? basis.shape : (obj.polygon ? classifyScenePolygonShape(rawScene, obj) : null);
    const planeObj = sd?.planeId ? byId.get(sd.planeId) : undefined;
    const solidObj = sd?.solidId ? byId.get(sd.solidId) : undefined;
    const header = cyc ? `Thiết diện ${cyc}` : cleanLearnerText(obj.label) || "Thiết diện";
    const cutDesc = planeObj && solidObj
      ? `Hình giao của ${formatPlaneDisplayNotation(planeObj, rawScene)} với ${shortSym(solidObj)}`
      : "Hình giao của mặt phẳng cắt với khối";
    const basisSuffix = basis && (basis.parallelPairs.length > 0 || basis.metricFacts.length > 0 || basis.undeterminedAspects.length > 0)
      ? basis.summary
      : shape;
    return finalizeStudentObjectPresentation({
      title: header,
      role: "Thiết diện",
      description: basisSuffix ? `${cutDesc} · ${basisSuffix}` : cutDesc,
      evidence: null,
      accentHex: hexCss(S.colors.sectionOutline),
      hasCanvasHoverTooltip: true,
    });
  }

  if (obj.type === "polygon3") {
    const shape = classifyScenePolygonShape(rawScene, obj);
    const depNames = (obj.vertex_ids && obj.vertex_ids.length >= 3 ? obj.vertex_ids : obj.depends ?? [])
      .map((id) => shortSym(byId.get(id)))
      .filter(Boolean);
    const prefOrder = [...structuralApexSymsOfScene(rawScene), ...preferredPointOrderForPolygon(rawScene, obj)];
    const cyc =
      depNames.length >= 3 && depNames.every(isCompactPointSym)
        ? formatCycleNotation(depNames, prefOrder)
        : null;
    if (isPolyhedronLateralOrAuxFacePolygon(rawScene, obj)) {
      const faceParen = cyc ? (cyc.startsWith("(") ? cyc : `(${cyc})`) : (obj.notation ?? shortSym(obj));
      return finalizeStudentObjectPresentation({
        title: `Mặt bên ${faceParen}`,
        role: "Mặt bên",
        description: depNames.length >= 3
          ? `Mặt bên của khối đa diện qua các đỉnh ${canonicalizeCycleNames(depNames, prefOrder).join(", ")}`
          : "Mặt bên của khối đa diện",
        evidence: null,
        accentHex,
        hasCanvasHoverTooltip: true,
      });
    }
    if (obj.surface_role === "BASE_REGION") {
      const prov = classifyPolygonShapeWithProvenance(rawScene, obj);
      return finalizeStudentObjectPresentation({
        title: `Đáy ${cyc ?? shortSym(obj)}`,
        role: "Mặt đáy",
        description: prov.certifiedShape ? `Đa giác đáy là ${prov.certifiedShape}` : "Mặt phẳng đáy xác định từ các đỉnh của đề bài",
        evidence: null,
        accentHex,
        hasCanvasHoverTooltip: true,
      });
    }
    if ((obj.formation_roles ?? []).includes("CONSTRUCT_TRANSLATED_FACE")) {
      return finalizeStudentObjectPresentation({
        title: `Đáy ${cyc ?? shortSym(obj)}`,
        role: "Đáy đối diện",
        description: "Mặt đáy song song và bằng mặt đáy tương ứng của khối lăng trụ.",
        evidence: null,
        accentHex,
        hasCanvasHoverTooltip: true,
      });
    }
    if (vaiTroMien(obj) === "section") {
      const basis = deriveExactPolygonMathBasis(rawScene, obj);
      const secShape = basis ? basis.shape : shape;
      return finalizeStudentObjectPresentation({
        title: `Thiết diện ${cyc ?? shortSym(obj)}`,
        role: "Thiết diện",
        description: basis && (basis.parallelPairs.length > 0 || basis.metricFacts.length > 0 || basis.undeterminedAspects.length > 0)
          ? basis.summary
          : secShape
            ? `Miền thiết diện là ${secShape}`
            : (stripStudentSpoilerSuffix(obj.role) || "Miền đa giác thiết diện"),
        evidence: null,
        accentHex: hexCss(S.colors.sectionOutline),
        hasCanvasHoverTooltip: true,
      });
    }
    return finalizeStudentObjectPresentation({
      title: cyc ? `Đa giác ${cyc}` : cleanLearnerText(obj.label || shortSym(obj)),
      role: "Đa giác",
      description: stripStudentSpoilerSuffix(obj.role) || "Miền đa giác phẳng xác định từ các đỉnh trên hình.",
      evidence: null,
      accentHex,
      hasCanvasHoverTooltip: false,
    });
  }

  if (obj.type === "segment3" || obj.type === "line3") {
    const sym = shortSym(obj);
    if (groups.includes("sphere_foundation_ref")) {
      return finalizeStudentObjectPresentation({
        title: `Bán kính tham chiếu ${sym}`,
        role: "Bán kính tham chiếu",
        description: `Đoạn nối tâm với điểm tham chiếu trên mặt cầu để biểu diễn độ mở bán kính ${sym} = R.`,
        evidence: null,
        accentHex,
        hasCanvasHoverTooltip: true,
      });
    }
    if (groups.includes("sphere_plane_dist")) {
      const pw = obj.perpendicular_witness ?? obj.annotation?.witness;
      const fromObj = pw?.from ? byId.get(pw.from) : undefined;
      const footObj = pw?.foot_id ? byId.get(pw.foot_id) : undefined;
      const onObj = pw?.on ? byId.get(pw.on) : undefined;
      const onSym = onObj ? formatPlaneDisplayNotation(onObj, rawScene) : "mặt phẳng cắt";
      return finalizeStudentObjectPresentation({
        title: `Đoạn vuông góc ${sym}`,
        role: "Đoạn vuông góc",
        description: `Đoạn vuông góc hạ${fromObj ? ` từ tâm ${shortSym(fromObj)}` : ""} đến ${onSym}${footObj ? ` tại ${shortSym(footObj)}` : ""} (${sym} ⊥ ${onSym}).`,
        evidence: null,
        accentHex: hexCss(S.colors.line),
        hasCanvasHoverTooltip: true,
      });
    }
    const curvedRole = classifyCurvedSegmentRole(rawScene, obj);
    if (
      groups.includes("sphere_plane_aux")
      || (obj as SceneObject & { auxiliary?: string }).auxiliary === "sphere_plane_aux"
    ) {
      if (curvedRole?.kind === "radius") {
        return finalizeStudentObjectPresentation({
          title: `Bán kính mặt cầu ${sym}`,
          role: "Bán kính mặt cầu",
          description: `Bán kính nối tâm mặt cầu với điểm thuộc đường tròn giao tuyến (${sym} = R).`,
          evidence: null,
          accentHex,
          hasCanvasHoverTooltip: true,
        });
      }
      return finalizeStudentObjectPresentation({
        title: `Bán kính giao tuyến ${sym}`,
        role: "Bán kính giao tuyến",
        description: stripStudentSpoilerSuffix(obj.role) || `Bán kính đường tròn giao tuyến trên mặt phẳng cắt.`,
        evidence: null,
        accentHex,
        hasCanvasHoverTooltip: true,
      });
    }
    if (obj.id.includes("__diag_") || /^Đường\s+chéo\b/iu.test(obj.label ?? "")) {
      return finalizeStudentObjectPresentation({
        title: /^Đường\s+chéo\b/iu.test(obj.label ?? "") ? cleanLearnerText(obj.label) : `Đường chéo ${sym}`,
        role: "Đường dựng phụ",
        description: stripStudentSpoilerSuffix(obj.role) || `Đường chéo phụ trợ ${sym} dùng để xác định giao điểm tâm mặt đáy.`,
        evidence: null,
        accentHex,
        hasCanvasHoverTooltip: true,
      });
    }
    if (curvedRole?.kind === "center_line") {
      return finalizeStudentObjectPresentation({
        title: `Đường nối tâm ${sym}`,
        role: "Đường nối tâm",
        description: "Đoạn nối tâm hai đáy hình trụ xiên (không vuông góc với mặt đáy)",
        evidence: null,
        accentHex,
        hasCanvasHoverTooltip: true,
      });
    }
    if ((obj.formation_roles ?? []).includes("CONSTRUCT_HEIGHT") || curvedRole?.kind === "altitude") {
      const onObj = obj.perpendicular_witness?.on ? byId.get(obj.perpendicular_witness.on) : undefined;
      const onSym = onObj?.notation
        ? (onObj.notation.startsWith("(") ? onObj.notation : `(${onObj.notation})`)
        : shortSym(onObj) || "mặt đáy";
      return finalizeStudentObjectPresentation({
        title: `Đường cao ${sym}`,
        role: "Đường cao",
        description: `Vuông góc với mặt phẳng ${onSym} (${sym} ⊥ ${onSym})`,
        evidence: null,
        accentHex: hexCss(S.colors.line),
        hasCanvasHoverTooltip: true,
      });
    }
    const pw = obj.perpendicular_witness ?? obj.annotation?.witness;
    if (pw) {
      if (pw.relation === "common_perpendicular") {
        return finalizeStudentObjectPresentation({
          title: `Đoạn vuông góc chung ${sym}`,
          role: "Vuông góc chung",
          description: stripStudentSpoilerSuffix(obj.role) || "Đoạn vuông góc chung nối hai chân vuông góc trên hai đường thẳng chéo nhau.",
          evidence: null,
          accentHex: hexCss(S.colors.line),
          hasCanvasHoverTooltip: true,
        });
      }
      const onObj = pw.on ? byId.get(pw.on) : undefined;
      const onSym = onObj
        ? (onObj.type === "plane3"
            ? formatPlaneDisplayNotation(onObj, rawScene)
            : (onObj.notation ? (onObj.notation.startsWith("(") ? onObj.notation : `(${onObj.notation})`) : shortSym(onObj)))
        : "đối tượng đích";
      const targetPhrase =
        onObj?.type === "plane3" || onObj?.type === "polygon3"
          ? `mặt phẳng ${onSym}`
          : onSym;
      return finalizeStudentObjectPresentation({
        title: `Đoạn vuông góc ${sym}`,
        role: "Đoạn vuông góc",
        description: `Vuông góc với ${targetPhrase} (${sym} ⊥ ${onSym})`,
        evidence: null,
        accentHex: hexCss(S.colors.line),
        hasCanvasHoverTooltip: true,
      });
    }
    if (curvedRole?.kind === "axis") {
      return finalizeStudentObjectPresentation({
        title: `Trục ${sym}`,
        role: "Trục khối tròn xoay",
        description: obj.role && obj.role !== obj.label ? stripStudentSpoilerSuffix(obj.role) : "Trục đối xứng vuông góc với mặt đáy khối tròn xoay",
        evidence: null,
        accentHex,
        hasCanvasHoverTooltip: true,
      });
    }
    if (curvedRole?.kind === "radius") {
      return finalizeStudentObjectPresentation({
        title: `Bán kính ${sym}`,
        role: "Bán kính",
        description: obj.role && obj.role !== obj.label ? stripStudentSpoilerSuffix(obj.role) : "Đoạn nối tâm với điểm thuộc biên khối tròn xoay",
        evidence: null,
        accentHex,
        hasCanvasHoverTooltip: true,
      });
    }
    if (curvedRole?.kind === "generator") {
      return finalizeStudentObjectPresentation({
        title: `Đường sinh ${sym}`,
        role: "Đường sinh",
        description: obj.role && obj.role !== obj.label ? stripStudentSpoilerSuffix(obj.role) : "Đường sinh trên mặt xung quanh khối tròn xoay",
        evidence: null,
        accentHex,
        hasCanvasHoverTooltip: true,
      });
    }
    if (isIntersectionLineOrSegment(obj, rawScene)) {
      const planeDeps = (obj.depends ?? [])
        .map((id) => byId.get(id))
        .filter((d): d is SceneObject => Boolean(d) && (d!.type === "plane3" || d!.type === "polygon3"));
      const planeDesc = planeDeps.length >= 2
        ? `Giao tuyến của ${formatPlaneDisplayNotation(planeDeps[0], rawScene)} và ${formatPlaneDisplayNotation(planeDeps[1], rawScene)}`
        : (obj.role && obj.role !== obj.label ? stripStudentSpoilerSuffix(obj.role) : "Giao tuyến của hai mặt phẳng");
      return finalizeStudentObjectPresentation({
        title: obj.type === "line3" ? `Giao tuyến ${sym}` : `Đoạn giao tuyến ${sym}`,
        role: "Giao tuyến",
        description: planeDesc,
        evidence: null,
        accentHex,
        hasCanvasHoverTooltip: true,
      });
    }
    const cleanedSegRole = stripStudentSpoilerSuffix(obj.role);
    const hasSpecificSegRole = Boolean(cleanedSegRole && cleanedSegRole !== cleanLearnerText(obj.label));
    return finalizeStudentObjectPresentation({
      title: isCompactPointSym(sym) || /^[A-Z0-9′']{2,6}$/u.test(sym)
        ? `${obj.type === "line3" ? "Đường thẳng" : "Đoạn thẳng"} ${sym}`
        : cleanLearnerText(obj.label || sym),
      role: (obj.formation_roles ?? []).includes("CONSTRUCT_LATERAL_BOUNDARY")
        ? "Cạnh bên"
        : obj.authoritative === false
          ? "Đường dựng phụ"
          : obj.type === "line3"
            ? "Đường thẳng"
            : "Đoạn thẳng",
      description: hasSpecificSegRole
        ? cleanedSegRole
        : `${obj.type === "line3" ? "Đường thẳng" : "Đoạn thẳng"} xác định qua hai điểm trên hình không gian.`,
      evidence: null,
      accentHex,
      hasCanvasHoverTooltip: hasSpecificSegRole,
    });
  }

  if (obj.type === "circle3" || obj.type === "ellipse3") {
    if (obj.type === "circle3") {
      const cRole = classifyCircleSemanticRole(rawScene, obj);
      if (cRole === "INSCRIBED_CIRCLE") {
        return finalizeStudentObjectPresentation({
          title: "Đường tròn nội tiếp",
          role: "Đường tròn đặc biệt",
          description: stripStudentSpoilerSuffix(obj.role) || "Tiếp xúc với các cạnh của đa giác chứa nó",
          evidence: null,
          accentHex,
          hasCanvasHoverTooltip: true,
        });
      }
      if (cRole === "CIRCUMSCRIBED_CIRCLE") {
        return finalizeStudentObjectPresentation({
          title: "Đường tròn ngoại tiếp",
          role: "Đường tròn đặc biệt",
          description: stripStudentSpoilerSuffix(obj.role) || "Đi qua các đỉnh của đa giác đồng phẳng",
          evidence: null,
          accentHex,
          hasCanvasHoverTooltip: true,
        });
      }
      if (obj.surface_role === "BASE_REGION" || cRole === "BOUNDARY_AND_INTERSECTION") {
        return finalizeStudentObjectPresentation({
          title: formatCanonicalCircleDesignation(rawScene, obj, presentObjs),
          role: "Đường tròn đáy",
          description: "Đường tròn biên của mặt đáy khối tròn xoay.",
          evidence: null,
          accentHex,
          hasCanvasHoverTooltip: false,
        });
      }
    }
    const planeDep = (obj.depends ?? []).map((id) => byId.get(id)).find((o) => o?.type === "plane3");
    const solidDep = (obj.depends ?? []).map((id) => byId.get(id)).find((o) => o?.type === "curved_solid");
    const exactMath = describeExactCurvedSectionMath(rawScene, obj);
    const baseBody = planeDep && solidDep
      ? `Giao của ${formatCurvedSolidProseName(rawScene, solidDep, presentObjs)} với mặt phẳng ${formatPlaneDisplayNotation(planeDep, rawScene)}`
      : (stripStudentSpoilerSuffix(obj.role) || "Giao tuyến phẳng của khối tròn xoay");
    return finalizeStudentObjectPresentation({
      title: obj.type === "circle3"
        ? formatCanonicalCircleDesignation(rawScene, obj, presentObjs)
        : formatCompactEntityChipLabel(rawScene, obj, presentObjs),
      role: obj.type === "ellipse3" ? "Giao tuyến elip" : "Giao tuyến tròn",
      description: exactMath ? `${baseBody} · ${exactMath}` : baseBody,
      evidence: null,
      accentHex: hexCss(S.colors.sectionOutline),
      hasCanvasHoverTooltip: true,
    });
  }

  if (obj.type === "curved_solid") {
    const explicitNot = cleanLearnerText(obj.notation);
    const eCs = exactById.get(obj.id) ?? obj;
    const centerPt = eCs.anchor
      ? (() => {
          const tv = parseFracVec3(eCs.anchor);
          return presentObjs.find((p) => {
            if (isSubEntity(p.id) || p.type !== "point3" || !isCompactPointSym(shortSym(p))) return false;
            const ep = exactById.get(p.id) ?? p;
            return Boolean(ep.xyz && vIsZero(vSub(parseFracVec3(ep.xyz), tv)));
          });
        })()
      : undefined;
    const cSym = centerPt ? shortSym(centerPt) : "";
    if (obj.curved_kind === "ball") {
      const sRole = classifySphereSemanticRole(rawScene, obj);
      if (sRole === "INSCRIBED_SPHERE") {
        return finalizeStudentObjectPresentation({
          title: explicitNot ? `Mặt cầu nội tiếp ${explicitNot}` : "Mặt cầu nội tiếp",
          role: explicitNot ? "Mặt cầu nội tiếp" : "Mặt cầu đặc biệt",
          description: "Tiếp xúc với các mặt của khối bao ngoài.",
          evidence: null,
          accentHex,
          hasCanvasHoverTooltip: true,
        });
      }
      if (sRole === "CIRCUMSCRIBED_SPHERE") {
        return finalizeStudentObjectPresentation({
          title: explicitNot ? `Mặt cầu ngoại tiếp ${explicitNot}` : "Mặt cầu ngoại tiếp",
          role: explicitNot ? "Mặt cầu ngoại tiếp" : "Mặt cầu đặc biệt",
          description: "Đi qua toàn bộ các đỉnh của khối nội tiếp.",
          evidence: null,
          accentHex,
          hasCanvasHoverTooltip: true,
        });
      }
      const ballTitle = explicitNot
        ? (cSym ? `Mặt cầu ${explicitNot} tâm ${cSym}` : `Mặt cầu ${explicitNot}`)
        : (cSym ? `Mặt cầu tâm ${cSym}` : "Mặt cầu không gian");
      return finalizeStudentObjectPresentation({
        title: ballTitle,
        role: "Mặt cầu",
        description: cSym
          ? `Tập hợp các điểm trong không gian cách tâm ${cSym} một khoảng không đổi bằng bán kính R.`
          : "Tập hợp các điểm trong không gian cách đều tâm một khoảng bằng bán kính.",
        evidence: null,
        accentHex,
        hasCanvasHoverTooltip: true,
      });
    }
    if (obj.curved_kind === "cylinder") {
      const ortho = inspectAxialCurvedOrthogonality(rawScene, obj);
      return finalizeStudentObjectPresentation({
        title: formatCompactEntityChipLabel(rawScene, obj, presentObjs),
        role: ortho.isOblique ? "Khối trụ xiên" : "Khối trụ tròn xoay",
        description: ortho.isOblique
          ? "Khối trụ có đường nối tâm hai đáy không vuông góc với mặt đáy."
          : "Khối trụ tròn xoay nhận đoạn nối tâm hai đáy làm trục vuông góc với mặt đáy.",
        evidence: null,
        accentHex,
        hasCanvasHoverTooltip: Boolean(obj.role && obj.role !== obj.label),
      });
    }
    if (obj.curved_kind === "cone") {
      return finalizeStudentObjectPresentation({
        title: formatCompactEntityChipLabel(rawScene, obj, presentObjs),
        role: "Khối nón tròn xoay",
        description: "Khối nón tròn xoay xác định bởi đỉnh, tâm đáy và đường tròn đáy.",
        evidence: null,
        accentHex,
        hasCanvasHoverTooltip: Boolean(obj.role && obj.role !== obj.label),
      });
    }
  }

  if (obj.type === "solid") {
    const cleanLbl = cleanLearnerText(obj.label || shortSym(obj)) || "Khối đa diện";
    const solidRole =
      /lập\s+phương/iu.test(cleanLbl)
        ? "Hình lập phương"
        : /hình\s+hộp/iu.test(cleanLbl)
          ? "Hình hộp"
          : /lăng\s+trụ/iu.test(cleanLbl)
            ? "Hình lăng trụ"
            : /tứ\s+diện/iu.test(cleanLbl)
              ? "Tứ diện"
              : /chóp\s+cụt/iu.test(cleanLbl)
                ? "Hình chóp cụt"
                : /chóp/iu.test(cleanLbl)
                  ? "Hình chóp"
                  : cleanLbl === "Khối đa diện"
                    ? "Khối không gian"
                    : "Khối đa diện";
    const hasSpecificSolidRole = Boolean(obj.role && obj.role !== obj.label);
    return finalizeStudentObjectPresentation({
      title: cleanLbl,
      role: solidRole,
      description: hasSpecificSolidRole
        ? stripStudentSpoilerSuffix(obj.role)
        : "Khối đa diện không gian được dựng từ mặt đáy và các đỉnh của đề bài.",
      evidence: null,
      accentHex,
      hasCanvasHoverTooltip: hasSpecificSolidRole,
    });
  }

  if (obj.type === "quantity") {
    const isGiven = classifyQuantityProvenance(obj, rawScene) === "GIVEN";
    return finalizeStudentObjectPresentation({
      title: cleanLearnerText(obj.label || obj.notation || "Đại lượng"),
      role: isGiven ? "Dữ kiện đề cho" : "Đại lượng hình học",
      description: isGiven
        ? "Đại lượng số đo được cho trực tiếp trong giả thiết bài toán."
        : "Đại lượng hình học gắn với các yếu tố trên mô hình.",
      evidence: null,
      accentHex,
      hasCanvasHoverTooltip: false,
    });
  }

  return finalizeStudentObjectPresentation({
    title: cleanLearnerText(obj.label || shortSym(obj) || "Đối tượng"),
    role: "Đối tượng hình học",
    description: stripStudentSpoilerSuffix(obj.role) || "Đối tượng hình học trong không gian.",
    evidence: null,
    accentHex,
    hasCanvasHoverTooltip: false,
  });
}

/**
 * Xây dựng nội dung tooltip toán học ngắn gọn, có kiểm chứng (§3):
 * - KHÔNG lặp lại tên đối tượng vô nghĩa: nếu không có quan hệ / vai trò toán học thực chất thì trả về `null`.
 * - Hỗ trợ cả đối tượng chính và thực thể con (`chop::edge:*`, `thiet_dien::face:0`, `thiet_dien::edge:*`).
 */
export function buildVerifiedObjectTooltip(
  rawScene: Scene3D,
  targetId: string | null | undefined,
  step: number,
): VerifiedObjectTooltip | null {
  const pres = resolveStudentObjectPresentation(rawScene, targetId, step);
  if (!pres || !pres.hasCanvasHoverTooltip) return null;
  return {
    header: pres.title,
    body: pres.evidence ? `${pres.description} · ${pres.evidence}` : pres.description,
    accentHex: pres.accentHex,
  };
}

export interface DockEntityChipItem {
  id: string;
  tier: "primary" | "context" | "other";
  shortLabel: string;
  fullTooltip: string;
  epistemicBadge: string;
}

export interface StepEntityGroupsResult {
  primary: DockEntityChipItem[];
  context: DockEntityChipItem[];
  other: DockEntityChipItem[];
  all: DockEntityChipItem[];
}

function cleanLearnerText(raw: string | undefined | null): string {
  return (raw ?? "").replace(/«([^»]+)»/gu, "$1").replace(/\s+/gu, " ").trim();
}

function truncateVietnameseWords(text: string, maxChars: number): string {
  const s = text.trim();
  if (s.length <= maxChars) return s;
  const cut = s.slice(0, Math.max(1, maxChars - 1));
  const lastSpace = cut.lastIndexOf(" ");
  const cleanCut = lastSpace >= Math.floor(maxChars * 0.45) ? cut.slice(0, lastSpace) : cut;
  return `${cleanCut.trimEnd()}…`;
}

export function formatCanonicalCircleDesignation(
  scene: Scene3D,
  obj: SceneObject,
  presentObjects?: readonly SceneObject[],
): string {
  const byId = new Map(scene.objects.map((o) => [o.id, o]));
  const pool = presentObjects ?? scene.objects;
  const exactScene = exactSceneOriginOf(scene);
  const exactById = new Map(exactScene.objects.map((o) => [o.id, o]));
  const eC = exactById.get(obj.id) ?? obj;

  let cp: SceneObject | undefined;
  let centerSym = "";
  const cv = eC.center ? parseFracVec3(eC.center) : null;
  if (cv) {
    cp =
      pool.find((p) => {
        if (isSubEntity(p.id) || p.type !== "point3") return false;
        const ep = exactById.get(p.id) ?? p;
        return Boolean(ep.xyz && vIsZero(vSub(parseFracVec3(ep.xyz), cv)));
      })
      ?? scene.objects.find((p) => {
        if (isSubEntity(p.id) || p.type !== "point3") return false;
        const ep = exactById.get(p.id) ?? p;
        return Boolean(ep.xyz && vIsZero(vSub(parseFracVec3(ep.xyz), cv)));
      });
    if (cp && isCompactPointSym(shortSym(cp))) centerSym = shortSym(cp);
  }

  const rSqFrac = eC.radius_sq ? parseExactFrac(eC.radius_sq) : null;
  const nv = eC.normal ? parseFracVec3(eC.normal) : null;

  const isGreatCircle =
    obj.surface_role !== "BASE_REGION"
    && Boolean(cv && rSqFrac)
    && scene.objects.some((b) => {
      if (b.type !== "curved_solid" || b.curved_kind !== "ball") return false;
      const eb = exactById.get(b.id) ?? b;
      if (!eb.anchor || !eb.radius_sq) return false;
      return vIsZero(vSub(parseFracVec3(eb.anchor), cv!)) && fEq(parseExactFrac(eb.radius_sq), rSqFrac!);
    });

  let rimPt: SceneObject | undefined;
  if (cv && nv && rSqFrac && rSqFrac[0] > 0n) {
    const matchesCircleRim = (p: SceneObject): boolean => {
      if (isSubEntity(p.id) || p.type !== "point3" || p.id === cp?.id) return false;
      if ((p.display_group ?? []).includes("sphere_foundation_ref")) return false;
      if (!isCompactPointSym(shortSym(p))) return false;
      const ep = exactById.get(p.id) ?? p;
      if (!ep.xyz) return false;
      const diff = vSub(parseFracVec3(ep.xyz), cv);
      return fIsZero(plainDotFrac(diff, nv)) && fEq(metricDot(diff, diff, exactScene.chart_metric), rSqFrac);
    };
    rimPt = pool.find(matchesCircleRim) ?? scene.objects.find(matchesCircleRim);
  }

  let radiusSpec = "";
  if (rimPt) {
    const rimSym = shortSym(rimPt);
    radiusSpec = centerSym ? `${centerSym}${rimSym}` : rimSym;
  } else if (obj.surface_role === "BASE_REGION" || isGreatCircle) {
    const hostSolid =
      obj.surface_role === "BASE_REGION"
        ? hostCurvedSolidForBaseCircle(scene, obj)
        : scene.objects.find(
            (b) => b.type === "curved_solid" && b.curved_kind === "ball" && (obj.depends ?? []).includes(b.id),
          );
    const givenRQty =
      hostSolid && rSqFrac
        ? exactScene.objects.find((q) => {
            if (q.type !== "quantity" || classifyQuantityProvenance(q, exactScene) !== "GIVEN") return false;
            const hostDeps = (exactById.get(hostSolid.id) ?? hostSolid).depends ?? [];
            const subjIds = q.annotation?.subject_ids ?? [];
            if (!hostDeps.includes(q.id) && !subjIds.includes(hostSolid.id)) return false;
            const vTxt = typeof q.value === "string" ? q.value.trim() : "";
            if (!vTxt || /π/u.test(vTxt)) return false;
            const parsedVal = Number(vTxt);
            return Number.isFinite(parsedVal) && Math.abs(parsedVal * parsedVal - toNumber(eC.radius_sq!)) <= 1e-6;
          })
        : undefined;
    const valStr = givenRQty && typeof givenRQty.value === "string" ? givenRQty.value.trim() : "";
    radiusSpec = valStr ? `R = ${valStr}` : "R";
  } else {
    radiusSpec = "r";
  }

  if (obj.surface_role === "BASE_REGION") {
    const isTopBase = (obj.formation_roles ?? []).includes("CONSTRUCT_TRANSLATED_FACE");
    return centerSym ? `Đáy tròn (${centerSym}; ${radiusSpec})` : isTopBase ? "Đáy tròn trên" : "Đáy tròn";
  }
  if (isGreatCircle) {
    return centerSym ? `Đường tròn lớn (${centerSym}; ${radiusSpec})` : "Đường tròn lớn giao tuyến";
  }
  if (centerSym) return `Đường tròn (${centerSym}; ${radiusSpec})`;
  const planeDep = (obj.depends ?? []).map((id) => byId.get(id)).find((p) => p?.type === "plane3");
  if (planeDep) return `Giao tuyến tròn trên ${formatPlaneDisplayNotation(planeDep)}`;
  return "Đường tròn thiết diện";
}

export function formatCompactEntityChipLabel(
  scene: Scene3D,
  obj: SceneObject,
  presentObjects?: readonly SceneObject[],
): string {
  const byId = new Map(scene.objects.map((o) => [o.id, o]));
  const pool = presentObjects ?? scene.objects;

  if (obj.type === "point3") {
    const explicitSym = cleanLearnerText(obj.notation);
    if (explicitSym && isCompactPointSym(explicitSym)) return explicitSym;
    const exactScene = exactSceneOriginOf(scene);
    const exactById = new Map(exactScene.objects.map((o) => [o.id, o]));
    const ePt = exactById.get(obj.id) ?? obj;
    const isSphereCenter =
      Boolean(ePt.xyz)
      && scene.objects.some((cand) => {
        if (cand.type !== "curved_solid" || cand.curved_kind !== "ball" || !(cand.depends ?? []).includes(obj.id)) {
          return false;
        }
        const eCand = exactById.get(cand.id) ?? cand;
        return Boolean(eCand.anchor && vIsZero(vSub(parseFracVec3(eCand.anchor), parseFracVec3(ePt.xyz!))));
      });
    if (isSphereCenter) return "Tâm mặt cầu";
    const refSym = cleanLearnerText(obj.reference);
    if (refSym && isCompactPointSym(refSym)) return refSym;
    const interRel = findLinePlaneIntersectionMidpoint(scene, obj);
    if (interRel) return `${interRel.lineSym} ∩ ${interRel.planeSym}`;
    return truncateVietnameseWords(cleanLearnerText(obj.label), 20);
  }

  if (obj.type === "plane3") {
    return cleanLearnerText(formatPlaneDisplayNotation(obj, scene));
  }

  if (
    obj.type === "section"
    || (obj.type === "polygon3" && vaiTroMien(obj) === "section" && !isPolyhedronLateralOrAuxFacePolygon(scene, obj))
  ) {
    const det = obj.type === "section" ? sectionDetails(scene, obj.id) : null;
    if (det && det.vertexNames.length >= 3 && det.vertexNames.every(isCompactPointSym)) {
      const cyc = formatCycleNotation(det.vertexNames, preferredPointOrderForPolygon(scene, obj));
      if (cyc) return `Thiết diện ${cyc}`;
    }
    if (obj.type === "polygon3") {
      const exactScene = exactSceneOriginOf(scene);
      const exactById = new Map(exactScene.objects.map((o) => [o.id, o]));
      const ePoly = exactById.get(obj.id) ?? obj;
      const rawIds = obj.vertex_ids ?? obj.depends ?? [];
      let polyNames = rawIds
        .map((id) => byId.get(id))
        .filter((p): p is SceneObject => Boolean(p && p.type === "point3" && isCompactPointSym(shortSym(p))))
        .map((p) => shortSym(p));
      const polyVertices = ePoly.vertices ?? obj.vertices;
      if (polyNames.length < 3 && (polyVertices?.length ?? 0) >= 3) {
        const matchedNames: string[] = [];
        for (const vx of polyVertices!) {
          const vFrac = parseFracVec3(vx);
          const pt = scene.objects.find((p) => {
            if (isSubEntity(p.id) || p.type !== "point3") return false;
            const ep = exactById.get(p.id) ?? p;
            return Boolean(ep.xyz && vIsZero(vSub(parseFracVec3(ep.xyz), vFrac)) && isCompactPointSym(shortSym(p)));
          });
          if (pt) matchedNames.push(shortSym(pt));
        }
        if (matchedNames.length === polyVertices!.length) polyNames = matchedNames;
      }
      if (polyNames.length >= 3 && polyNames.every(isCompactPointSym)) {
        const cyc = formatCycleNotation(polyNames, [
          ...structuralApexSymsOfScene(scene),
          ...preferredPointOrderForPolygon(scene, obj),
        ]);
        if (cyc) return `Thiết diện ${cyc}`;
      }
    }
    const planeForChip = det?.planeId
      ? byId.get(det.planeId)
      : (obj.depends ?? []).map((id) => byId.get(id)).find((p) => p?.type === "plane3");
    if (planeForChip) {
      return `Thiết diện ${cleanLearnerText(formatPlaneDisplayNotation(planeForChip, scene))}`;
    }
    return "Thiết diện";
  }

  if (obj.type === "polygon3") {
    const rawIds = obj.vertex_ids ?? obj.depends ?? [];
    const depNames = rawIds
      .map((id) => shortSym(byId.get(id)))
      .filter((s): s is string => Boolean(s && isCompactPointSym(s)));
    const not = cleanLearnerText(obj.notation);
    if (rawIds.length >= 3 && depNames.length === rawIds.length) {
      const prefOrder = [
        ...(isPolyhedronLateralOrAuxFacePolygon(scene, obj) ? structuralApexSymsOfScene(scene) : []),
        ...preferredPointOrderForPolygon(scene, obj),
      ];
      const canon = canonicalizeCycleNames(depNames, prefOrder).join("");
      if (canon.length <= 12) {
        return not.startsWith("(") && not.endsWith(")") ? `(${canon})` : canon;
      }
    }
    if (not && not.length <= 16) return not;
    const roles = obj.formation_roles ?? [];
    if (roles.includes("CONSTRUCT_TRANSLATED_FACE")) return "Đáy đối diện";
    if (obj.surface_role === "BASE_REGION" || roles.includes("CONSTRUCT_BASE")) return "Mặt đáy";
    return truncateVietnameseWords(cleanLearnerText(obj.label), 18);
  }

  if (obj.type === "segment3") {
    const not = cleanLearnerText(obj.notation);
    if (not && not.length <= 10) return not;
    const rawEpIds = obj.endpoint_ids ?? obj.depends ?? [];
    const ptSyms = rawEpIds
      .map((id) => byId.get(id))
      .filter((p): p is SceneObject => Boolean(p && p.type === "point3" && isCompactPointSym(shortSym(p))))
      .map((p) => shortSym(p));
    if (rawEpIds.length === 2 && ptSyms.length === 2) return `${ptSyms[0]}${ptSyms[1]}`;
    const cRole = classifyCurvedSegmentRole(scene, obj);
    if (cRole?.kind === "radius") return "Bán kính R";
    if (cRole?.kind === "axis") return "Trục";
    if (cRole?.kind === "generator") return "Đường sinh";
    const roles = obj.formation_roles ?? [];
    if (roles.includes("CONSTRUCT_HEIGHT")) return "Đường cao";
    if (roles.includes("CONSTRUCT_LATERAL_BOUNDARY")) return "Cạnh bên";
    return truncateVietnameseWords(cleanLearnerText(obj.label), 18);
  }

  if (obj.type === "line3") {
    if (isIntersectionLineOrSegment(obj, scene)) {
      const exactScene = exactSceneOriginOf(scene);
      const exactById = new Map(exactScene.objects.map((o) => [o.id, o]));
      const eLine = exactById.get(obj.id) ?? obj;
      if (eLine.point && eLine.direction) {
        const lp0 = parseFracVec3(eLine.point);
        const ldir = parseFracVec3(eLine.direction);
        const ptsOn = pool.filter((p) => {
          if (isSubEntity(p.id) || p.type !== "point3") return false;
          const ep = exactById.get(p.id) ?? p;
          return Boolean(ep.xyz && vIsZero(vCross(vSub(parseFracVec3(ep.xyz), lp0), ldir)) && isCompactPointSym(shortSym(p)));
        });
        if (ptsOn.length === 2) return `${shortSym(ptsOn[0])}${shortSym(ptsOn[1])}`;
      }
      const explicitInterNot = cleanLearnerText(obj.notation);
      if (
        explicitInterNot
        && explicitInterNot.length <= 6
        && !explicitInterNot.includes("∩")
        && !/^(?:gt|inter|line)/iu.test(explicitInterNot)
      ) {
        return `Giao tuyến ${explicitInterNot}`;
      }
      const planeDeps = (obj.depends ?? [])
        .map((id) => byId.get(id))
        .filter((p): p is SceneObject => Boolean(p && p.type === "plane3"));
      if (planeDeps.length >= 2) {
        return `${formatPlaneDisplayNotation(planeDeps[0])} ∩ ${formatPlaneDisplayNotation(planeDeps[1])}`;
      }
      return "Giao tuyến";
    }
    const not = cleanLearnerText(obj.notation);
    const ptSyms = (obj.depends ?? [])
      .map((id) => byId.get(id))
      .filter((p): p is SceneObject => Boolean(p && p.type === "point3" && isCompactPointSym(shortSym(p))))
      .map((p) => shortSym(p));
    const baseSym = (not && not.length <= 10 ? not : ptSyms.length === 2 ? `${ptSyms[0]}${ptSyms[1]}` : "") || "d";
    const collidesWithSeg = pool.some(
      (other) =>
        other.id !== obj.id
        && !isSubEntity(other.id)
        && other.type === "segment3"
        && formatCompactEntityChipLabel(scene, other) === baseSym,
    );
    return collidesWithSeg ? `Đường thẳng ${baseSym}` : baseSym;
  }

  if (obj.type === "circle3") {
    return formatCanonicalCircleDesignation(scene, obj, presentObjects);
  }

  if (obj.type === "ellipse3") {
    const planeDep = (obj.depends ?? []).map((id) => byId.get(id)).find((p) => p?.type === "plane3");
    return planeDep ? `Elip giao tuyến trên ${formatPlaneDisplayNotation(planeDep)}` : "Elip thiết diện";
  }

  if (obj.type === "curved_solid") {
    const not = cleanLearnerText(obj.notation);
    if (not && not.length <= 12 && !/^\([A-Z]\)$/u.test(not)) return not;
    const exactScene = exactSceneOriginOf(scene);
    const exactById = new Map(exactScene.objects.map((o) => [o.id, o]));
    const eCs = exactById.get(obj.id) ?? obj;
    const depPts = (obj.depends ?? [])
      .map((id) => byId.get(id))
      .filter((p): p is SceneObject => Boolean(p && p.type === "point3" && isCompactPointSym(shortSym(p))));
    const findPtAt = (target: ExactVec3 | null | undefined): SceneObject | undefined => {
      if (!target) return undefined;
      const tv = parseFracVec3(target);
      return (
        depPts.find((p) => {
          const ep = exactById.get(p.id) ?? p;
          return Boolean(ep.xyz && vIsZero(vSub(parseFracVec3(ep.xyz), tv)));
        })
        ?? pool.find((p) => {
          if (isSubEntity(p.id) || p.type !== "point3" || !isCompactPointSym(shortSym(p))) return false;
          const ep = exactById.get(p.id) ?? p;
          return Boolean(ep.xyz && vIsZero(vSub(parseFracVec3(ep.xyz), tv)));
        })
      );
    };
    if (obj.curved_kind === "ball") {
      const cPt = findPtAt(eCs.anchor);
      if (cPt && Boolean(cPt.notation?.trim())) return `Mặt cầu (${shortSym(cPt)})`;
      const sRole = classifySphereSemanticRole(scene, obj);
      if (sRole === "CIRCUMSCRIBED_SPHERE") return "Mặt cầu ngoại tiếp";
      if (sRole === "INSCRIBED_SPHERE") return "Mặt cầu nội tiếp";
      return "Mặt cầu";
    }
    if (obj.curved_kind === "cylinder") {
      const pBase = findPtAt(eCs.anchor);
      const pTop = findPtAt(eCs.apex_or_top);
      const cylNoun = inspectAxialCurvedOrthogonality(scene, obj).isOblique ? "Hình trụ xiên" : "Hình trụ";
      if (pBase && pTop) return `${cylNoun} ${shortSym(pBase)}${shortSym(pTop)}`;
      return depPts.length >= 2 ? `${cylNoun} ${shortSym(depPts[0])}${shortSym(depPts[1])}` : cylNoun;
    }
    if (obj.curved_kind === "cone") {
      const apex = findPtAt(eCs.apex_or_top);
      const center = findPtAt(eCs.anchor);
      if (apex && center) return `Hình nón ${shortSym(apex)}.${shortSym(center)}`;
      return depPts.length >= 2 ? `Hình nón ${shortSym(depPts[0])}.${shortSym(depPts[1])}` : "Hình nón";
    }
  }

  if (obj.type === "solid") {
    const not = cleanLearnerText(obj.notation);
    if (not && not.length <= 16) return not;
    const m = /([A-Z0-9′'.]{3,14})$/u.exec(cleanLearnerText(obj.label));
    if (m) return m[1];
  }

  const fallback = cleanLearnerText(obj.notation || obj.reference || obj.label);
  return truncateVietnameseWords(fallback, 20);
}

/**
 * Phân nhóm đối tượng tại bước `step` cho Study Dock theo 3 mức ưu tiên sư phạm:
 * - `primary`: Đối tượng chính vừa tạo / đang giải thích tại bước hiện tại.
 * - `context`: Đối tượng nền trực tiếp liên quan (tiên quyết trực tiếp & hình phụ giải thích được chứng minh ngay tại bước này).
 * - `other`: Các đối tượng nền khác và hình phụ còn lại (thu gọn mặc định trên giao diện để tránh quá tải thông tin).
 */
export function buildStepEntityGroups(
  scene: Scene3D,
  step: number,
  options?: {
    hiddenAuxIds?: ReadonlySet<string>;
    hiddenAnswerIds?: ReadonlySet<string>;
    selectedId?: string | null;
    steps?: readonly PedagogicalStepItem[];
    pedagogicalSteps?: readonly PedagogicalStepItem[];
  },
): StepEntityGroupsResult {
  const k = clampStep(scene, step);
  const presentObjs = objectsAt(scene, k);
  const presentIds = new Set(presentObjs.map((o) => o.id));
  const ungrounded = ungroundedFreePointIdsAt(scene, k);
  const hiddenAux = options?.hiddenAuxIds ?? auxiliaryHiddenAt(scene, k, false, options?.selectedId ?? null);
  const hiddenAns = options?.hiddenAnswerIds ?? new Set<string>();
  const selectedId = options?.selectedId ?? null;

  const steps = options?.steps ?? options?.pedagogicalSteps ?? pedagogicalStepList(scene);
  const activeStep =
    steps.find((s) => k >= s.startAnchor && k <= s.anchor)
    ?? [...steps].reverse().find((s) => s.anchor <= k)
    ?? steps[0];
  const stepHl = computeStepHighlightTargets(scene, k, activeStep?.startAnchor);
  const activeFaceCarrierIds = new Set(
    resolveSolidFaceDuplicateCarrierPolygons(scene, k, selectedId).map((x) => x.planeId),
  );

  const byId = new Map(scene.objects.map((o) => [o.id, o]));
  const stepRolesAtK = resolveStepVisualRoles(scene, k, {
    auxiliaryShown: false,
    selectedId,
  });
  const isSphereFoundationVisibleAtStep = (o: SceneObject): boolean =>
    (o.display_group ?? []).includes("sphere_foundation_ref")
    && (stepRolesAtK.get(o.id)?.visible ?? false);
  const isHiddenPlaneHelperPoint = (o: SceneObject): boolean =>
    laDiemPhuDungMatPhang(scene, o, byId)
    && o.source?.instruction !== "EXPLANATORY_DERIVED_WITNESS"
    && !isSphereFoundationVisibleAtStep(o)
    && !o.perpendicular_witness;

  const isRenderableDockEntity = (o: SceneObject | undefined): o is SceneObject => {
    if (!o || !presentIds.has(o.id)) return false;
    if (
      ungrounded.has(o.id)
      || (hiddenAux.has(o.id) && !activeFaceCarrierIds.has(o.id) && !isSphereFoundationVisibleAtStep(o))
      || hiddenAns.has(o.id)
    ) {
      return false;
    }
    if (selectedId !== o.id && isHiddenPlaneHelperPoint(o)) return false;
    if (o.type === "quantity" || o.render === "readout" || o.render === "non_visual") return false;
    if (o.display_role === "hit_proxy" || o.display_role === "measurement" || o.display_role === "non_visual") return false;
    if (isSubEntity(o.id)) return false;
    if (o.type === "plane3") {
      const pDec = resolvePlaneSectionVisibility(scene, o, k, false, selectedId, activeStep?.startAnchor);
      if (pDec.subRole === "SOLID_FACE_DUPLICATE_PLANE" && !pDec.visible && !activeFaceCarrierIds.has(o.id)) return false;
    }
    return true;
  };

  const stepCandidateIds = [...new Set([...(activeStep?.targetIds ?? []), ...stepHl.newIds])];
  const isAbsorbedPointCarrierLine = (cid: string): boolean => {
    const o = byId.get(cid);
    if (!o || o.type !== "line3" || isIntersectionLineOrSegment(o, scene)) return false;
    return stepCandidateIds.some((otherId) => {
      if (otherId === cid) return false;
      const other = byId.get(otherId);
      return Boolean(other && other.type === "point3" && isRenderableDockEntity(other) && (other.depends ?? []).includes(cid));
    });
  };
  const authoritativePrimaryIds = stepCandidateIds.filter((cid) => {
    const o = byId.get(cid);
    return (
      isRenderableDockEntity(o)
      && !(o.authoritative === false && o.semantic_role === "AUXILIARY_CONSTRUCTION")
      && !isAbsorbedPointCarrierLine(cid)
    );
  });

  const primaryIdSet = new Set<string>(
    authoritativePrimaryIds.length > 0
      ? authoritativePrimaryIds
      : stepCandidateIds.filter((cid) => isRenderableDockEntity(byId.get(cid))),
  );

  const contextIdSet = new Set<string>(
    (activeStep?.prerequisiteIds ?? []).filter((pid) => {
      const o = byId.get(pid);
      return !(o && isHiddenPlaneHelperPoint(o));
    }),
  );
  for (const did of stepHl.depIds) {
    const o = byId.get(did);
    if (o && isHiddenPlaneHelperPoint(o)) continue;
    if (!primaryIdSet.has(did)) contextIdSet.add(did);
  }
  for (const nid of stepHl.newIds) {
    const o = byId.get(nid);
    if (o && isHiddenPlaneHelperPoint(o)) continue;
    if (!primaryIdSet.has(nid)) contextIdSet.add(nid);
  }
  for (const tid of activeStep?.targetIds ?? []) {
    const o = byId.get(tid);
    if (!o || isHiddenPlaneHelperPoint(o)) continue;
    if (!primaryIdSet.has(tid)) contextIdSet.add(tid);
  }
  for (const fcId of activeFaceCarrierIds) {
    if (!primaryIdSet.has(fcId)) contextIdSet.add(fcId);
  }
  // Với thiết diện ở bước hoàn thiện, đưa các đỉnh của thiết diện vào nhóm liên quan trực tiếp để học sinh dễ tra cứu
  for (const pid of primaryIdSet) {
    const pObj = byId.get(pid);
    if (!pObj) continue;
    if (
      pObj.type === "section"
      || (
        pObj.type === "polygon3"
        && vaiTroMien(pObj) === "section"
        && !isAuxiliaryExplanatoryPolygon(scene, pObj)
        && !isPolyhedronOppositeTopBasePolygon(scene, pObj)
      )
    ) {
      const secVIds = diemTaiDinhThietDien({
        objects: presentObjs.filter(
          (x) => x.id === pid || (x.type === "point3" && !isHiddenPlaneHelperPoint(x)),
        ),
      });
      for (const vid of secVIds) {
        if (!primaryIdSet.has(vid)) contextIdSet.add(vid);
      }
    }
    for (const d of pObj.depends ?? []) {
      const dObj = byId.get(d);
      if (dObj && isHiddenPlaneHelperPoint(dObj)) continue;
      if (!primaryIdSet.has(d)) contextIdSet.add(d);
    }
  }
  // Khi bán kính tham chiếu mặt cầu (IX) thuộc nhóm chính/liên quan ở Bước 1, đưa đầu mút tham chiếu (X) vào nhóm liên quan trực tiếp
  for (const fgId of [...primaryIdSet, ...contextIdSet]) {
    const fgObj = byId.get(fgId);
    if (!fgObj || !(fgObj.display_group ?? []).includes("sphere_foundation_ref")) continue;
    for (const epId of fgObj.endpoint_ids ?? fgObj.depends ?? []) {
      const epObj = byId.get(epId);
      if (!epObj || isHiddenPlaneHelperPoint(epObj)) continue;
      if (!primaryIdSet.has(epId)) contextIdSet.add(epId);
    }
  }

  const rawCandidates = scene.objects.filter((o) => {
    if (!presentIds.has(o.id)) return false;
    if (
      ungrounded.has(o.id)
      || (hiddenAux.has(o.id) && !activeFaceCarrierIds.has(o.id) && !isSphereFoundationVisibleAtStep(o))
      || hiddenAns.has(o.id)
    ) {
      return false;
    }
    if (selectedId !== o.id && isHiddenPlaneHelperPoint(o)) return false;
    if (o.type === "quantity" || o.render === "readout" || o.render === "non_visual") return false;
    if (o.display_role === "hit_proxy" || o.display_role === "measurement" || o.display_role === "non_visual") return false;
    if (isSubEntity(o.id)) return false;
    if (o.type === "plane3") {
      const pDec = resolvePlaneSectionVisibility(scene, o, k, false, selectedId, activeStep?.startAnchor);
      if (pDec.subRole === "SOLID_FACE_DUPLICATE_PLANE" && !pDec.visible) {
        const isActiveIntersectionCarrier =
          contextIdSet.has(o.id)
          && [...primaryIdSet].some((pid) => {
            const pObj = byId.get(pid);
            return Boolean(pObj && (pObj.depends ?? []).includes(o.id));
          });
        if (!isActiveIntersectionCarrier && !activeFaceCarrierIds.has(o.id)) return false;
      }
    }
    return true;
  });

  const tierRank = (tier: "primary" | "context" | "other") =>
    tier === "primary" ? 0 : tier === "context" ? 1 : 2;

  const builtItems: DockEntityChipItem[] = rawCandidates.map((o) => {
    const retiredAuxPlane =
      o.type === "plane3"
      && !activeFaceCarrierIds.has(o.id)
      && !resolvePlaneSectionVisibility(scene, o, k, false, selectedId, activeStep?.startAnchor).visible;
    const isCompletedAuxAtStep =
      selectedId !== o.id
      && !activeFaceCarrierIds.has(o.id)
      && stepRolesAtK.get(o.id)?.presentationTier === "COMPLETED_AUXILIARY";
    const tier: "primary" | "context" | "other" = primaryIdSet.has(o.id) && !isCompletedAuxAtStep
      ? "primary"
      : retiredAuxPlane || isCompletedAuxAtStep
        ? "other"
        : contextIdSet.has(o.id)
          ? "context"
          : "other";
    const shortLabel = formatCompactEntityChipLabel(scene, o, rawCandidates);
    const pres = resolveStudentObjectPresentation(scene, o.id, k);
    const sem = classifySceneObjectSemantics(scene, o, k, selectedId);
    const epistemicBadge =
      o.authoritative === false && o.semantic_role === "AUXILIARY_CONSTRUCTION"
        ? "Hình phụ"
        : sem.epistemicStatus === "given"
          ? "Đề cho"
          : sem.epistemicStatus === "auxiliary"
            ? "Hình phụ"
            : sem.epistemicStatus === "constructed_result"
              ? "Được suy ra"
              : "Được dựng";
    const cleanFullName = cleanLearnerText(pres?.title || o.label || shortLabel);
    const cleanBody = cleanLearnerText(pres?.description || "");
    const fullTooltip = cleanBody && cleanBody !== cleanFullName
      ? `[${epistemicBadge}] ${cleanFullName} — ${cleanBody}`
      : `[${epistemicBadge}] ${cleanFullName}`;
    return {
      id: o.id,
      tier,
      shortLabel,
      fullTooltip,
      epistemicBadge,
    };
  });

  // Khử trùng lặp theo nhãn hiển thị ngắn gọn (ưu tiên đối tượng đang chọn > primary > context > other)
  const dedupByLabel = new Map<string, DockEntityChipItem>();
  for (const item of builtItems) {
    const existing = dedupByLabel.get(item.shortLabel);
    if (!existing) {
      dedupByLabel.set(item.shortLabel, item);
      continue;
    }
    const itemSelected = item.id === selectedId;
    const existingSelected = existing.id === selectedId;
    if (itemSelected && !existingSelected) {
      dedupByLabel.set(item.shortLabel, item);
    } else if (!existingSelected && tierRank(item.tier) < tierRank(existing.tier)) {
      dedupByLabel.set(item.shortLabel, item);
    }
  }

  const deduped = [...dedupByLabel.values()];
  if (deduped.length > 0 && !deduped.some((x) => x.tier === "primary")) {
    const firstContextIdx = deduped.findIndex((x) => x.tier === "context");
    const promoteIdx = firstContextIdx >= 0 ? firstContextIdx : 0;
    deduped[promoteIdx] = { ...deduped[promoteIdx], tier: "primary" };
  }

  const primaryPrereqOfOtherPrimary = new Set<string>();
  for (const pid of primaryIdSet) {
    const pObj = byId.get(pid);
    for (const dep of pObj?.depends ?? []) {
      if (dep !== pid && primaryIdSet.has(dep)) {
        primaryPrereqOfOtherPrimary.add(dep);
      }
    }
  }
  const primary = deduped
    .filter((x) => x.tier === "primary")
    .sort((a, b) => Number(primaryPrereqOfOtherPrimary.has(a.id)) - Number(primaryPrereqOfOtherPrimary.has(b.id)));
  const context = deduped.filter((x) => x.tier === "context").slice(0, 8);
  const contextKeptIds = new Set(context.map((x) => x.id));
    const other = deduped
      .filter((x) => x.tier === "other" || (x.tier === "context" && !contextKeptIds.has(x.id)))
      .map((x) => (x.tier === "other" ? x : { ...x, tier: "other" as const }));

    return {
      primary,
      context,
      other,
      all: [...primary, ...context, ...other],
    };
  }

// ─── HỢP ĐỒNG DỰNG HÌNH NGỮ NGHĨA THỐNG NHẤT (UNIFIED SEMANTIC CONSTRUCTION CONTRACT) ───

export type SemanticGeometricType =
  | "point"
  | "segment"
  | "line"
  | "plane"
  | "polygon"
  | "section"
  | "circle"
  | "ellipse"
  | "polyhedron_solid"
  | "curved_solid"
  | "quantity"
  | "sub_entity";

export type UnifiedSemanticObjectRole =
  | "PRIMARY_SOLID"
  | "SECONDARY_CUT_SOLID"
  | "BASE_FACE"
  | "TOP_FACE"
  | "LATERAL_FACE"
  | "CUTTING_PLANE"
  | "AUXILIARY_PLANE"
  | "DUPLICATE_FACE_PLANE"
  | "MEASUREMENT_PLANE"
  | "INTERSECTION_SECTION"
  | "INTERSECTION_CIRCLE"
  | "INTERSECTION_ELLIPSE"
  | "INTERSECTION_LINE"
  | "ALTITUDE_OR_AXIS"
  | "TANGENT_OR_DISTANCE_PERP"
  | "COMMON_PERPENDICULAR"
  | "CURVED_RADIUS"
  | "CURVED_GENERATOR"
  | "PROJECTION_FOOT"
  | "INTERSECTION_POINT"
  | "MIDPOINT_OR_RATIO_POINT"
  | "GIVEN_VERTEX"
  | "AUXILIARY_OBJECT"
  | "GIVEN_QUANTITY"
  | "RESULT_OR_INTERMEDIATE_QUANTITY"
  | "SUB_ENTITY";

export type SemanticDeterminacy =
  | "EXACT_DETERMINED"
  | "ILLUSTRATIVE_GAUGE"
  | "UNDERDETERMINED"
  | "CONTRADICTORY";

export type SemanticVisibilityLifecycle =
  | "PERSISTENT_PRIMARY"
  | "PERSISTENT_CONTEXT"
  | "TRANSIENT_CONSTRUCTION_TOOL"
  | "AUXILIARY_ON_DEMAND"
  | "INTERNAL_HIDDEN";

export type UnifiedInformationCategory =
  | "GIVEN_FACT"
  | "CONSTRUCTION_RELATION"
  | "INTERNAL_MATH_RESULT";

export interface CertifiedGeometricRelation {
  kind:
    | "line_perp_plane"
    | "line_perp_line"
    | "common_perpendicular"
    | "parallel"
    | "incidence"
    | "tangent_sphere_plane"
    | "secant_sphere_plane";
  targetIds: string[];
  provenance: CanonicalMathProvenance;
  exactVerified: boolean;
  canDisplaySymbol: boolean;
}

export type CanonicalPedagogicalObjectRole =
  | "GIVEN_FACT"
  | "CONSTRUCTION_GEOMETRY"
  | "AUXILIARY_GEOMETRY"
  | "REFERENCE_GEOMETRY"
  | "RESULT_SECTION"
  | "ILLUSTRATIVE_GEOMETRY"
  | "INTERNAL_MATH_RESULT";

export type SemanticConstructionLayer =
  | "GIVEN_GEOMETRY"
  | "REFERENCE_GEOMETRY"
  | "CONSTRUCTION_GEOMETRY"
  | "RELATION_WITNESS"
  | "RESULT_SECTION"
  | "INTERNAL_MATH_RESULT";

export type ConstructionOperationKind =
  | "GIVEN_SEED"
  | "CONSTRUCT_SOLID_OR_FACE"
  | "CONSTRUCT_PLANE"
  | "PROJECT_PERPENDICULAR"
  | "INTERSECT_CARRIERS"
  | "INTERSECT_SECTION"
  | "INTERPOLATE_RATIO_OR_MIDPOINT"
  | "CONNECT_SEGMENT_OR_LINE"
  | "EXTRACT_CURVED_WITNESS"
  | "AUXILIARY_REFERENCE"
  | "INTERNAL_MEASUREMENT";

export interface ConstructionEventContract {
  object_id: string;
  semantic_role: UnifiedSemanticObjectRole;
  object_layer: SemanticConstructionLayer;
  provenance: CanonicalMathProvenance;
  prerequisites: readonly string[];
  construction_operation: ConstructionOperationKind;
  geometric_witness: CertifiedGeometricRelation | null;
  visibility_policy: SemanticVisibilityLifecycle;
  visual_role: StepVisualRole;
  step_group: number;
  birth_anchor: number;
}

export interface SemanticObjectContract {
  id: string;
  geometricType: SemanticGeometricType;
  semanticRole: UnifiedSemanticObjectRole;
  canonicalRole: CanonicalPedagogicalObjectRole;
  objectLayer: SemanticConstructionLayer;
  provenance: CanonicalMathProvenance;
  determinacy: SemanticDeterminacy;
  informationCategory: UnifiedInformationCategory;
  visibilityLifecycle: SemanticVisibilityLifecycle;
  prerequisiteIds: string[];
  verifiedRelations: CertifiedGeometricRelation[];
  visualPriorityTier: 1 | 2 | 3 | 4 | 5;
}

export interface SemanticConstructionContract {
  scene: Scene3D;
  exactOrigin: Scene3D;
  consistency: ReturnType<typeof verifySceneMathematicalConsistency>;
  objectsById: ReadonlyMap<string, SemanticObjectContract>;
  constructionEvents: readonly ConstructionEventContract[];
}

const _semanticContractCache = new WeakMap<
  Scene3D,
  { hybrid: ReturnType<typeof hybridViewOfScene>; sig: string; contract: SemanticConstructionContract }
>();

function mapSemanticGeometricType(obj: SceneObject): SemanticGeometricType {
  if (isSubEntity(obj.id) || obj.type === "edge" || obj.type === "face") return "sub_entity";
  switch (obj.type) {
    case "point3":
      return "point";
    case "segment3":
      return "segment";
    case "line3":
      return "line";
    case "plane3":
      return "plane";
    case "polygon3":
      return "polygon";
    case "section":
      return "section";
    case "circle3":
      return "circle";
    case "ellipse3":
      return "ellipse";
    case "solid":
      return "polyhedron_solid";
    case "curved_solid":
      return "curved_solid";
    case "quantity":
    default:
      return "quantity";
  }
}

export function getSemanticConstructionContract(scene: Scene3D): SemanticConstructionContract {
  const curHybrid = hybridViewOfScene(scene);
  const curSig = sceneCacheSignature(scene);
  const cached = _semanticContractCache.get(scene);
  if (cached && cached.hybrid === curHybrid && cached.sig === curSig) {
    return cached.contract;
  }

  const exactOrigin = exactSceneOriginOf(scene);
  const exactById = new Map(exactOrigin.objects.map((o) => [o.id, o]));
  const byId = new Map(scene.objects.map((o) => [o.id, o]));
  const consistency = verifySceneMathematicalConsistency(exactOrigin);
  const contradictoryIds = new Set(consistency.contradictions.map((c) => c.objectId));
  const measOnlyPlanes = measurementOnlyPlanes(exactOrigin);
  const auxIds = auxiliaryObjects(scene);
  const finalExactAnchor = Math.max(0, exactOrigin.events.length - 1);

  const exactLineDirectionOf = (lo: SceneObject): FracVec3 | null => {
    if (lo.direction) {
      const dv = parseFracVec3(lo.direction);
      if (!vIsZero(dv)) return dv;
    }
    if (lo.point_a && lo.point_b) {
      const dv = vSub(parseFracVec3(lo.point_b), parseFracVec3(lo.point_a));
      if (!vIsZero(dv)) return dv;
    }
    if (lo.endpoints && lo.endpoints.length >= 2) {
      const dv = vSub(parseFracVec3(lo.endpoints[1]), parseFracVec3(lo.endpoints[0]));
      if (!vIsZero(dv)) return dv;
    }
    const epIds = lo.endpoint_ids?.length ? lo.endpoint_ids : (lo.depends ?? []);
    if (epIds.length >= 2) {
      const p0 = exactById.get(epIds[0])?.xyz;
      const p1 = exactById.get(epIds[1])?.xyz;
      if (p0 && p1) {
        const dv = vSub(parseFracVec3(p1), parseFracVec3(p0));
        if (!vIsZero(dv)) return dv;
      }
    }
    return null;
  };

  const exactPolygonNormalOf = (po: SceneObject): { p0: FracVec3; normal: FracVec3 } | null => {
    const rawPts: FracVec3[] = [];
    const coordSrc = po.polygon ?? po.vertices;
    if (coordSrc && coordSrc.length >= 3) {
      for (const c of coordSrc) rawPts.push(parseFracVec3(c));
    } else {
      const vIds = po.vertex_ids?.length ? po.vertex_ids : (po.depends ?? []);
      for (const vid of vIds) {
        const vx = exactById.get(vid)?.xyz;
        if (vx) rawPts.push(parseFracVec3(vx));
      }
    }
    if (rawPts.length < 3) return null;
    for (let i = 1; i + 1 < rawPts.length; i += 1) {
      const n = vCross(vSub(rawPts[i], rawPts[0]), vSub(rawPts[i + 1], rawPts[0]));
      if (!vIsZero(n)) return { p0: rawPts[0], normal: n };
    }
    return null;
  };

  const objectsById = new Map<string, SemanticObjectContract>();

  for (const obj of scene.objects) {
    const hasExactEntry = exactById.has(obj.id);
    const exObj = exactById.get(obj.id) ?? obj;
    const gMetricForObj = hasExactEntry
      ? exactOrigin.chart_metric
      : (isSceneWorldTransformed(scene) ? undefined : scene.chart_metric);
    const geometricType = mapSemanticGeometricType(obj);
    const provenance = classifySceneEntityProvenance(exactOrigin, exObj);
    const prerequisiteIds = [...new Set((exObj.depends ?? obj.depends ?? []).filter((d) => d !== obj.id && byId.has(d)))];

    let semanticRole: UnifiedSemanticObjectRole = "AUXILIARY_OBJECT";
    let visibilityLifecycle: SemanticVisibilityLifecycle = "PERSISTENT_CONTEXT";
    let visualPriorityTier: 1 | 2 | 3 | 4 | 5 = 3;

    if (geometricType === "sub_entity") {
      semanticRole = "SUB_ENTITY";
      visibilityLifecycle = "PERSISTENT_CONTEXT";
      visualPriorityTier = 4;
    } else if (obj.type === "quantity" || obj.render === "readout" || obj.render === "non_visual") {
      const qProv = classifyQuantityProvenance(exObj, exactOrigin);
      if (qProv === "GIVEN") {
        semanticRole = "GIVEN_QUANTITY";
        visibilityLifecycle = "PERSISTENT_CONTEXT";
        visualPriorityTier = 3;
      } else {
        semanticRole = "RESULT_OR_INTERMEDIATE_QUANTITY";
        visibilityLifecycle = "INTERNAL_HIDDEN";
        visualPriorityTier = 5;
      }
    } else if (obj.type === "solid") {
      semanticRole = "PRIMARY_SOLID";
      visibilityLifecycle = "PERSISTENT_PRIMARY";
      visualPriorityTier = 2;
    } else if (obj.type === "curved_solid") {
      const isSecondary = isSecondaryCutCurvedSolid(exactOrigin, exObj);
      semanticRole = isSecondary ? "SECONDARY_CUT_SOLID" : "PRIMARY_SOLID";
      visibilityLifecycle = "PERSISTENT_PRIMARY";
      visualPriorityTier = isSecondary ? 1 : 2;
    } else if (obj.type === "section") {
      semanticRole = "INTERSECTION_SECTION";
      visibilityLifecycle = "PERSISTENT_PRIMARY";
      visualPriorityTier = 1;
    } else if (obj.type === "circle3") {
      if (vaiTroMien(exObj) === "section" || classifyCircleSemanticRole(exactOrigin, exObj) === "RESULT_SECTION") {
        semanticRole = "INTERSECTION_CIRCLE";
        visibilityLifecycle = "PERSISTENT_PRIMARY";
        visualPriorityTier = 1;
      } else if (exObj.surface_role === "BASE_REGION") {
        semanticRole = (exObj.formation_roles ?? []).includes("CONSTRUCT_TRANSLATED_FACE") ? "TOP_FACE" : "BASE_FACE";
        visibilityLifecycle = "PERSISTENT_PRIMARY";
        visualPriorityTier = 2;
      } else {
        semanticRole = "AUXILIARY_OBJECT";
        visibilityLifecycle = auxIds.has(obj.id) ? "AUXILIARY_ON_DEMAND" : "PERSISTENT_CONTEXT";
        visualPriorityTier = 4;
      }
    } else if (obj.type === "ellipse3") {
      semanticRole = "INTERSECTION_ELLIPSE";
      visibilityLifecycle = "PERSISTENT_PRIMARY";
      visualPriorityTier = 1;
    } else if (obj.type === "polygon3") {
      if (isPolyhedronOppositeTopBasePolygon(exactOrigin, exObj)) {
        semanticRole = "TOP_FACE";
        visibilityLifecycle = "PERSISTENT_PRIMARY";
        visualPriorityTier = 2;
      } else if (isPolyhedronLateralOrAuxFacePolygon(exactOrigin, exObj)) {
        semanticRole = "LATERAL_FACE";
        visibilityLifecycle = "PERSISTENT_CONTEXT";
        visualPriorityTier = 3;
      } else if (exObj.surface_role === "BASE_REGION" || (exObj.formation_roles ?? []).includes("CONSTRUCT_BASE")) {
        semanticRole = "BASE_FACE";
        visibilityLifecycle = "PERSISTENT_PRIMARY";
        visualPriorityTier = 2;
      } else if (vaiTroMien(exObj) === "section") {
        semanticRole = "INTERSECTION_SECTION";
        visibilityLifecycle = "PERSISTENT_PRIMARY";
        visualPriorityTier = 1;
      } else {
        semanticRole = "AUXILIARY_OBJECT";
        visibilityLifecycle = auxIds.has(obj.id) ? "AUXILIARY_ON_DEMAND" : "PERSISTENT_CONTEXT";
        visualPriorityTier = 4;
      }
    } else if (obj.type === "plane3") {
      if (measOnlyPlanes.has(obj.id)) {
        semanticRole = "MEASUREMENT_PLANE";
        visibilityLifecycle = "INTERNAL_HIDDEN";
        visualPriorityTier = 5;
      } else {
        const pDec = resolvePlaneSectionVisibility(exactOrigin, exObj, finalExactAnchor, false, null);
        if (pDec.subRole === "SOLID_FACE_DUPLICATE_PLANE") {
          semanticRole = "DUPLICATE_FACE_PLANE";
          visibilityLifecycle = "AUXILIARY_ON_DEMAND";
          visualPriorityTier = 5;
        } else if (pDec.subRole === "CONSTRUCTION_TOOL_PLANE" || pDec.subRole === "SPATIAL_RELATION_PLANE" || exObj.surface_role === "CUTTING_PLANE") {
          semanticRole = "CUTTING_PLANE";
          visibilityLifecycle = "TRANSIENT_CONSTRUCTION_TOOL";
          visualPriorityTier = 3;
        } else {
          semanticRole = "AUXILIARY_PLANE";
          visibilityLifecycle = auxIds.has(obj.id) ? "AUXILIARY_ON_DEMAND" : "PERSISTENT_CONTEXT";
          visualPriorityTier = 4;
        }
      }
    } else if (obj.type === "segment3" || obj.type === "line3") {
      const segW = exObj.perpendicular_witness ?? exObj.annotation?.witness;
      const cRole = classifyCurvedSegmentRole(exactOrigin, exObj);
      if (isIntersectionLineOrSegment(exObj, exactOrigin)) {
        semanticRole = "INTERSECTION_LINE";
        visibilityLifecycle = "PERSISTENT_PRIMARY";
        visualPriorityTier = 1;
      } else if (segW?.relation === "common_perpendicular") {
        semanticRole = "COMMON_PERPENDICULAR";
        visibilityLifecycle = "PERSISTENT_PRIMARY";
        visualPriorityTier = 1;
      } else if ((exObj.formation_roles ?? []).includes("CONSTRUCT_HEIGHT") || cRole?.kind === "axis" || cRole?.kind === "altitude") {
        semanticRole = "ALTITUDE_OR_AXIS";
        visibilityLifecycle = "PERSISTENT_CONTEXT";
        visualPriorityTier = 2;
      } else if (segW?.on) {
        semanticRole = "TANGENT_OR_DISTANCE_PERP";
        visibilityLifecycle = "PERSISTENT_CONTEXT";
        visualPriorityTier = 2;
      } else if (cRole?.kind === "radius") {
        semanticRole = "CURVED_RADIUS";
        visibilityLifecycle = auxIds.has(obj.id) ? "AUXILIARY_ON_DEMAND" : "PERSISTENT_CONTEXT";
        visualPriorityTier = 3;
      } else if (cRole?.kind === "generator") {
        semanticRole = "CURVED_GENERATOR";
        visibilityLifecycle = "PERSISTENT_CONTEXT";
        visualPriorityTier = 3;
      } else {
        semanticRole = "AUXILIARY_OBJECT";
        visibilityLifecycle = auxIds.has(obj.id) ? "AUXILIARY_ON_DEMAND" : "PERSISTENT_CONTEXT";
        visualPriorityTier = 4;
      }
    } else if (obj.type === "point3") {
      const ptRoles = exObj.formation_roles ?? [];
      const hasPlaneAndLineDeps =
        (exObj.depends ?? []).some((d) => exactById.get(d)?.type === "plane3")
        && (exObj.depends ?? []).some((d) => {
          const dt = exactById.get(d)?.type;
          return dt === "line3" || dt === "segment3" || dt === "point3";
        });
      if (exObj.origin === "free") {
        semanticRole = "GIVEN_VERTEX";
        visibilityLifecycle = "PERSISTENT_PRIMARY";
        visualPriorityTier = 2;
      } else if (Boolean(exObj.perpendicular_witness)) {
        semanticRole = "PROJECTION_FOOT";
        visibilityLifecycle = "PERSISTENT_CONTEXT";
        visualPriorityTier = 2;
      } else if (
        ptRoles.includes("DERIVE_INTERSECTION")
        || ptRoles.includes("CONSTRUCT_INTERSECTION")
        || findLinePlaneIntersectionMidpoint(exactOrigin, exObj) !== null
        || findPolygonDiagonalIntersectionRelation(exactOrigin, exObj) !== null
        || (hasPlaneAndLineDeps && !exObj.perpendicular_witness)
      ) {
        semanticRole = "INTERSECTION_POINT";
        visibilityLifecycle = "PERSISTENT_PRIMARY";
        visualPriorityTier = 2;
      } else if (findPointMidpointRelation(exactOrigin, exObj) !== null || findPointCentroidRelation(exactOrigin, exObj) !== null) {
        semanticRole = "MIDPOINT_OR_RATIO_POINT";
        visibilityLifecycle = "PERSISTENT_CONTEXT";
        visualPriorityTier = 3;
      } else {
        semanticRole = "AUXILIARY_OBJECT";
        visibilityLifecycle = auxIds.has(obj.id) ? "AUXILIARY_ON_DEMAND" : "PERSISTENT_CONTEXT";
        visualPriorityTier = 4;
      }
    }

    // 3-tier Information Classification: GIVEN_FACT | CONSTRUCTION_RELATION | INTERNAL_MATH_RESULT
    let informationCategory: UnifiedInformationCategory = "CONSTRUCTION_RELATION";
    if (semanticRole === "RESULT_OR_INTERMEDIATE_QUANTITY" || semanticRole === "MEASUREMENT_PLANE") {
      informationCategory = "INTERNAL_MATH_RESULT";
    } else if (
      semanticRole === "GIVEN_QUANTITY"
      || semanticRole === "GIVEN_VERTEX"
      || semanticRole === "PRIMARY_SOLID"
      || semanticRole === "BASE_FACE"
      || semanticRole === "TOP_FACE"
      || provenance === "GIVEN"
    ) {
      informationCategory = "GIVEN_FACT";
    }

    // Determinacy & Exact Verified Relations
    let determinacy: SemanticDeterminacy = "EXACT_DETERMINED";
    if (contradictoryIds.has(obj.id) || provenance === "INVALID") {
      determinacy = "CONTRADICTORY";
    } else if (provenance === "UNDERDETERMINED") {
      determinacy = "UNDERDETERMINED";
    } else if (provenance === "ILLUSTRATIVE") {
      determinacy = "ILLUSTRATIVE_GAUGE";
    }

    if (obj.type === "polygon3" || obj.type === "section") {
      const polyProv = classifyPolygonShapeWithProvenance(exactOrigin, exObj);
      if (polyProv.provenance === "CONTRADICTORY_OR_UNSUPPORTED") {
        determinacy = "CONTRADICTORY";
      } else if (
        polyProv.coordinateShape !== null
        && polyProv.certifiedShape === null
        && (polyProv.provenance === "ILLUSTRATIVE_CHOICE" || polyProv.provenance === "UNVERIFIED")
      ) {
        determinacy = "ILLUSTRATIVE_GAUGE";
      }
    }

    const isObjConsistent = !contradictoryIds.has(obj.id) && determinacy !== "CONTRADICTORY";
    const verifiedRelations: CertifiedGeometricRelation[] = [];
    const w = exObj.perpendicular_witness ?? exObj.annotation?.witness;
    if (w) {
      const wRec = w as unknown as Record<string, unknown>;
      const unverifiedFlag = wRec.status === "UNVERIFIED" || wRec.can_present_as_proven === false;
      let exactOk = false;
      if (w.relation === "common_perpendicular") {
        const u1 = w.marker?.u ? parseFracVec3(w.marker.u) : null;
        const v1 = w.marker?.v ? parseFracVec3(w.marker.v) : null;
        const firstMarkerOk = Boolean(
          u1
            && v1
            && !vIsZero(u1)
            && !vIsZero(v1)
            && fIsZero(metricDot(u1, v1, gMetricForObj)),
        );
        const secondMarkerOk = w.second?.marker
          ? (() => {
              const u2 = parseFracVec3(w.second.marker.u);
              const v2 = parseFracVec3(w.second.marker.v);
              return !vIsZero(u2) && !vIsZero(v2) && fIsZero(metricDot(u2, v2, gMetricForObj));
            })()
          : true;
        exactOk = isObjConsistent && firstMarkerOk && secondMarkerOk;
        verifiedRelations.push({
          kind: "common_perpendicular",
          targetIds: [w.on, w.second?.on ?? w.from].filter((x): x is string => Boolean(x)),
          provenance: w.status === "GIVEN" ? "GIVEN" : "DERIVED_VERIFIED",
          exactVerified: exactOk,
          canDisplaySymbol: exactOk && !unverifiedFlag,
        });
      } else if (isLinePerpPlaneRelation(w.relation) || (w.plane_directions && w.plane_directions.length >= 2)) {
        const vVec = w.marker?.v ? parseFracVec3(w.marker.v) : null;
        const segDir = (exObj.type === "segment3" || exObj.type === "line3") ? exactLineDirectionOf(exObj) : null;
        const spanVecs: FracVec3[] = (w.plane_directions ?? [])
          .map(parseFracVec3)
          .filter((pd) => !vIsZero(pd));
        const exOn = w.on ? exactById.get(w.on) : undefined;
        if (exOn?.type === "plane3" && exOn.point && exOn.normal) {
          const proj = projectPointOntoPlaneExact(
            parseFracVec3(exOn.point),
            parseFracVec3(exOn.point),
            parseFracVec3(exOn.normal),
            gMetricForObj,
          );
          if (proj) {
            spanVecs.push(proj.basis[0], proj.basis[1]);
          }
        } else if (exOn && (exOn.type === "polygon3" || exOn.type === "section")) {
          const rawPts: FracVec3[] = [];
          const cSrc = exOn.polygon ?? exOn.vertices;
          if (cSrc && cSrc.length >= 3) {
            for (const c of cSrc) rawPts.push(parseFracVec3(c));
          } else {
            for (const vid of exOn.vertex_ids ?? exOn.depends ?? []) {
              const vx = exactById.get(vid)?.xyz;
              if (vx) rawPts.push(parseFracVec3(vx));
            }
          }
          for (let k = 1; k < rawPts.length; k += 1) {
            const ev = vSub(rawPts[k], rawPts[0]);
            if (!vIsZero(ev)) spanVecs.push(ev);
          }
        } else if (spanVecs.length === 0 && w.marker?.u) {
          const uFallback = parseFracVec3(w.marker.u);
          if (!vIsZero(uFallback)) spanVecs.push(uFallback);
        }
        exactOk = Boolean(
          isObjConsistent
            && vVec
            && !vIsZero(vVec)
            && spanVecs.length >= 1
            && spanVecs.every((pd) => fIsZero(metricDot(vVec, pd, gMetricForObj)))
            && (!segDir || spanVecs.every((pd) => fIsZero(metricDot(segDir, pd, gMetricForObj)))),
        );
        verifiedRelations.push({
          kind: "line_perp_plane",
          targetIds: [w.on, w.foot_id].filter((x): x is string => Boolean(x)),
          provenance: w.status === "GIVEN" ? "GIVEN" : "DERIVED_VERIFIED",
          exactVerified: exactOk,
          canDisplaySymbol: exactOk && !unverifiedFlag,
        });
      } else {
        const uVec = w.marker?.u ? parseFracVec3(w.marker.u) : null;
        const vVec = w.marker?.v ? parseFracVec3(w.marker.v) : null;
        const exOnLine = w.on ? exactById.get(w.on) : undefined;
        const rawLineDir = Array.isArray(wRec.line_direction) && wRec.line_direction.length === 3
          ? (wRec.line_direction as ExactVec3)
          : undefined;
        const carrierDir =
          rawLineDir
            ? parseFracVec3(rawLineDir)
            : (exOnLine && (exOnLine.type === "line3" || exOnLine.type === "segment3") ? exactLineDirectionOf(exOnLine) : null);
        exactOk = Boolean(
          isObjConsistent
            && uVec
            && vVec
            && !vIsZero(uVec)
            && !vIsZero(vVec)
            && fIsZero(metricDot(uVec, vVec, gMetricForObj))
            && (!carrierDir || vIsZero(carrierDir) || fIsZero(metricDot(vVec, carrierDir, gMetricForObj))),
        );
        verifiedRelations.push({
          kind: "line_perp_line",
          targetIds: [w.on, w.foot_id].filter((x): x is string => Boolean(x)),
          provenance: w.status === "GIVEN" ? "GIVEN" : "DERIVED_VERIFIED",
          exactVerified: exactOk,
          canDisplaySymbol: exactOk && !unverifiedFlag,
        });
      }
    }

    if (obj.type === "polygon3" || obj.type === "section") {
      const polyProv = classifyPolygonShapeWithProvenance(exactOrigin, exObj);
      if (
        isObjConsistent
        && polyProv.certifiedShape
        && (polyProv.certifiedShape.includes("vuông") || polyProv.certifiedShape === "hình chữ nhật")
        && (polyProv.provenance === "GIVEN" || polyProv.provenance === "DERIVED_VERIFIED")
      ) {
        verifiedRelations.push({
          kind: "line_perp_line",
          targetIds: prerequisiteIds,
          provenance: polyProv.provenance === "GIVEN" ? "GIVEN" : "DERIVED_VERIFIED",
          exactVerified: true,
          canDisplaySymbol: true,
        });
      } else if (polyProv.coordinateShape && polyProv.coordinateShape.includes("vuông") && !polyProv.certifiedShape) {
        verifiedRelations.push({
          kind: "line_perp_line",
          targetIds: prerequisiteIds,
          provenance: "ILLUSTRATIVE",
          exactVerified: false,
          canDisplaySymbol: false,
        });
      }
    }

    // Parallel relations (`parallel`): intersection lines parallel to edges, cutting planes parallel to bases, opposite parallel bases
    if (semanticRole === "INTERSECTION_LINE" && (exObj.type === "line3" || exObj.type === "segment3")) {
      const lDir = exactLineDirectionOf(exObj);
      if (lDir) {
        const parallelCarriers: string[] = [];
        const rawExLinePt =
          exObj.point
          ?? exObj.point_a
          ?? exObj.endpoints?.[0]
          ?? (exObj.endpoint_ids?.[0] ? exactById.get(exObj.endpoint_ids[0])?.xyz : undefined);
        const exLinePt = rawExLinePt ? parseFracVec3(rawExLinePt) : null;
        for (const sol of exactOrigin.objects) {
          if (sol.type !== "solid" || !sol.faces?.length || !sol.vertices?.length || !sol.vertex_ids?.length) continue;
          const seenPairs = new Set<string>();
          for (const f of sol.faces) {
            for (let i = 0; i < f.length; i += 1) {
              const ia = f[i];
              const ib = f[(i + 1) % f.length];
              if (ia === undefined || ib === undefined) continue;
              const [firstIdx, secondIdx] = ia <= ib ? [ia, ib] : [ib, ia];
              const vaId = sol.vertex_ids[firstIdx];
              const vbId = sol.vertex_ids[secondIdx];
              const vaPt = sol.vertices[firstIdx];
              const vbPt = sol.vertices[secondIdx];
              if (!vaId || !vbId || !vaPt || !vbPt) continue;
              const pairKey = `${firstIdx}|${secondIdx}`;
              if (seenPairs.has(pairKey)) continue;
              seenPairs.add(pairKey);
              const eDir = vSub(parseFracVec3(vbPt), parseFracVec3(vaPt));
              if (vIsZero(eDir) || !vIsZero(vCross(lDir, eDir))) continue;
              if (exLinePt && vIsZero(vCross(vSub(parseFracVec3(vaPt), exLinePt), lDir))) continue;
              parallelCarriers.push(`${sol.id}::edge:${vaId}-${vbId}`);
            }
          }
        }
        for (const cand of exactOrigin.objects) {
          if (cand.id === obj.id || isSubEntity(cand.id) || (cand.type !== "segment3" && cand.type !== "line3")) continue;
          const cDir = exactLineDirectionOf(cand);
          if (!cDir || !vIsZero(vCross(lDir, cDir))) continue;
          const rawCandPt =
            cand.point
            ?? cand.point_a
            ?? cand.endpoints?.[0]
            ?? (cand.endpoint_ids?.[0] ? exactById.get(cand.endpoint_ids[0])?.xyz : undefined);
          if (exLinePt && rawCandPt && vIsZero(vCross(vSub(parseFracVec3(rawCandPt), exLinePt), lDir))) continue;
          parallelCarriers.push(cand.id);
        }
        if (parallelCarriers.length > 0) {
          verifiedRelations.push({
            kind: "parallel",
            targetIds: parallelCarriers,
            provenance: "DERIVED_VERIFIED",
            exactVerified: isObjConsistent,
            canDisplaySymbol: isObjConsistent && determinacy === "EXACT_DETERMINED",
          });
        }
      }
    } else if (exObj.type === "plane3" && exObj.normal) {
      if (exObj.point) {
        const projMp = projectPointOntoPlaneExact(
          parseFracVec3(exObj.point),
          parseFracVec3(exObj.point),
          parseFracVec3(exObj.normal),
          gMetricForObj,
        );
        if (projMp) {
          const perpLineDeps: string[] = [];
          for (const depId of prerequisiteIds) {
            const depEx = exactById.get(depId) ?? byId.get(depId);
            if (!depEx || (depEx.type !== "line3" && depEx.type !== "segment3")) continue;
            const lDir = exactLineDirectionOf(depEx);
            if (
              lDir
              && !vIsZero(lDir)
              && fIsZero(metricDot(lDir, projMp.basis[0], gMetricForObj))
              && fIsZero(metricDot(lDir, projMp.basis[1], gMetricForObj))
            ) {
              perpLineDeps.push(depId);
            }
          }
          if (perpLineDeps.length > 0) {
            verifiedRelations.push({
              kind: "line_perp_plane",
              targetIds: perpLineDeps,
              provenance: provenance === "GIVEN" ? "GIVEN" : "DERIVED_VERIFIED",
              exactVerified: isObjConsistent,
              canDisplaySymbol: isObjConsistent && determinacy === "EXACT_DETERMINED",
            });
          }
        }
      }
      if (semanticRole === "CUTTING_PLANE") {
      const nPlane = parseFracVec3(exObj.normal);
      if (!vIsZero(nPlane)) {
        const parallelBases: string[] = [];
        for (const cand of exactOrigin.objects) {
          if (cand.id === obj.id || isSubEntity(cand.id)) continue;
          if (cand.type === "polygon3" && (cand.surface_role === "BASE_REGION" || (cand.formation_roles ?? []).includes("CONSTRUCT_BASE"))) {
            const pn = exactPolygonNormalOf(cand);
            if (pn && vIsZero(vCross(nPlane, pn.normal))) parallelBases.push(cand.id);
          } else if (cand.type === "circle3" && cand.surface_role === "BASE_REGION" && cand.normal) {
            const cn = parseFracVec3(cand.normal);
            if (!vIsZero(cn) && vIsZero(vCross(nPlane, cn))) parallelBases.push(cand.id);
          }
        }
        if (parallelBases.length > 0) {
          verifiedRelations.push({
            kind: "parallel",
            targetIds: parallelBases,
            provenance: provenance === "GIVEN" ? "GIVEN" : "DERIVED_VERIFIED",
            exactVerified: isObjConsistent,
            canDisplaySymbol: isObjConsistent && determinacy === "EXACT_DETERMINED",
          });
        }
      }
      }
    } else if (semanticRole === "TOP_FACE" && (exObj.type === "polygon3" || exObj.type === "circle3")) {
      const topNorm = exObj.type === "polygon3"
        ? exactPolygonNormalOf(exObj)?.normal ?? null
        : (exObj.normal ? parseFracVec3(exObj.normal) : null);
      if (topNorm && !vIsZero(topNorm)) {
        const lowerBases = exactOrigin.objects
          .filter((cand) => {
            if (cand.id === obj.id || isSubEntity(cand.id)) return false;
            if (cand.type === "polygon3" && (cand.surface_role === "BASE_REGION" || (cand.formation_roles ?? []).includes("CONSTRUCT_BASE")) && !isPolyhedronOppositeTopBasePolygon(exactOrigin, cand) && !isPolyhedronLateralOrAuxFacePolygon(exactOrigin, cand)) {
              const bn = exactPolygonNormalOf(cand);
              return Boolean(bn && vIsZero(vCross(topNorm, bn.normal)));
            }
            if (cand.type === "circle3" && cand.surface_role === "BASE_REGION" && !(cand.formation_roles ?? []).includes("CONSTRUCT_TRANSLATED_FACE") && cand.normal) {
              const cn = parseFracVec3(cand.normal);
              return !vIsZero(cn) && vIsZero(vCross(topNorm, cn));
            }
            return false;
          })
          .map((c) => c.id);
        if (lowerBases.length > 0) {
          verifiedRelations.push({
            kind: "parallel",
            targetIds: lowerBases,
            provenance: provenance === "GIVEN" ? "GIVEN" : "DERIVED_VERIFIED",
            exactVerified: isObjConsistent,
            canDisplaySymbol: isObjConsistent && determinacy === "EXACT_DETERMINED",
          });
        }
      }
    }

    // Incidence relations (`incidence`): derived points certified to lie on their prerequisite carriers over Q³
    if (
      exObj.type === "point3"
      && exObj.xyz
      && (semanticRole === "INTERSECTION_POINT" || semanticRole === "MIDPOINT_OR_RATIO_POINT" || semanticRole === "PROJECTION_FOOT")
    ) {
      const pt = parseFracVec3(exObj.xyz);
      const incidentCarriers: string[] = [];
      const candidateCarrierIds = [...new Set([...prerequisiteIds, ...(w?.on ? [w.on] : [])])];
      for (const cid of candidateCarrierIds) {
        const carrier = exactById.get(cid);
        if (!carrier) continue;
        if (carrier.type === "plane3" && carrier.point && carrier.normal) {
          const p0 = parseFracVec3(carrier.point);
          const nVec = parseFracVec3(carrier.normal);
          if (!vIsZero(nVec) && fIsZero(plainDotFrac(vSub(pt, p0), nVec))) {
            incidentCarriers.push(cid);
          }
        } else if (carrier.type === "polygon3" || carrier.type === "section") {
          const pn = exactPolygonNormalOf(carrier);
          if (pn && fIsZero(plainDotFrac(vSub(pt, pn.p0), pn.normal))) {
            incidentCarriers.push(cid);
          }
        } else if (carrier.type === "line3" || carrier.type === "segment3") {
          const lDir = exactLineDirectionOf(carrier);
          const anchorXyz =
            carrier.point
            ?? carrier.point_a
            ?? carrier.endpoints?.[0]
            ?? (carrier.endpoint_ids?.[0] ? exactById.get(carrier.endpoint_ids[0])?.xyz : undefined)
            ?? (carrier.depends?.[0] ? exactById.get(carrier.depends[0])?.xyz : undefined);
          if (lDir && anchorXyz && vIsZero(vCross(vSub(pt, parseFracVec3(anchorXyz)), lDir))) {
            incidentCarriers.push(cid);
          }
        } else if (carrier.type === "curved_solid" && carrier.curved_kind === "ball" && carrier.anchor && carrier.radius_sq) {
          const diff = vSub(pt, parseFracVec3(carrier.anchor));
          const distSq = metricDot(diff, diff, exactOrigin.chart_metric);
          if (fEq(distSq, parseExactFrac(carrier.radius_sq))) {
            incidentCarriers.push(cid);
          }
        }
      }
      if (incidentCarriers.length > 0) {
        verifiedRelations.push({
          kind: "incidence",
          targetIds: incidentCarriers,
          provenance: provenance === "GIVEN" ? "GIVEN" : "DERIVED_VERIFIED",
          exactVerified: isObjConsistent,
          canDisplaySymbol: isObjConsistent && determinacy === "EXACT_DETERMINED",
        });
      }
    }

    // Sphere–plane regime relations (`tangent_sphere_plane` & `secant_sphere_plane`)
    if (semanticRole === "INTERSECTION_CIRCLE" && exObj.type === "circle3" && exObj.center && exObj.radius_sq) {
      const ballDep = (exObj.depends ?? [])
        .map((id) => exactById.get(id))
        .find((d): d is SceneObject => Boolean(d && d.type === "curved_solid" && d.curved_kind === "ball" && d.anchor && d.radius_sq));
      const planeDep = (exObj.depends ?? [])
        .map((id) => exactById.get(id))
        .find((d): d is SceneObject => Boolean(d && d.type === "plane3"));
      if (ballDep?.anchor && ballDep.radius_sq) {
        const diff = vSub(parseFracVec3(exObj.center), parseFracVec3(ballDep.anchor));
        const d2 = metricDot(diff, diff, exactOrigin.chart_metric);
        const r2 = parseExactFrac(exObj.radius_sq);
        const R2 = parseExactFrac(ballDep.radius_sq);
        const secantOk = isObjConsistent && r2[0] > 0n && fSub(R2, d2)[0] > 0n && fEq(fAdd(d2, r2), R2);
        verifiedRelations.push({
          kind: "secant_sphere_plane",
          targetIds: [ballDep.id, planeDep?.id].filter((x): x is string => Boolean(x)),
          provenance: "DERIVED_VERIFIED",
          exactVerified: secantOk,
          canDisplaySymbol: secantOk && determinacy === "EXACT_DETERMINED",
        });
      }
    } else if (exObj.type === "plane3" && exObj.point && exObj.normal && !measOnlyPlanes.has(obj.id)) {
      const p0 = parseFracVec3(exObj.point);
      const nVec = parseFracVec3(exObj.normal);
      if (!vIsZero(nVec)) {
        for (const ball of exactOrigin.objects) {
          if (isSubEntity(ball.id) || ball.type !== "curved_solid" || ball.curved_kind !== "ball" || !ball.anchor || !ball.radius_sq) {
            continue;
          }
          const proj = projectPointOntoPlaneExact(parseFracVec3(ball.anchor), p0, nVec, exactOrigin.chart_metric);
          if (!proj) continue;
          const diff = vSub(proj.foot, parseFracVec3(ball.anchor));
          const d2 = metricDot(diff, diff, exactOrigin.chart_metric);
          const R2 = parseExactFrac(ball.radius_sq);
          if (R2[0] <= 0n) continue;
          if (d2[0] > 0n && fEq(d2, R2)) {
            verifiedRelations.push({
              kind: "tangent_sphere_plane",
              targetIds: [ball.id],
              provenance: "DERIVED_VERIFIED",
              exactVerified: isObjConsistent,
              canDisplaySymbol: isObjConsistent && determinacy === "EXACT_DETERMINED",
            });
          } else if (d2[0] >= 0n && fSub(R2, d2)[0] > 0n && exObj.surface_role === "CUTTING_PLANE") {
            verifiedRelations.push({
              kind: "secant_sphere_plane",
              targetIds: [ball.id],
              provenance: "DERIVED_VERIFIED",
              exactVerified: isObjConsistent,
              canDisplaySymbol: isObjConsistent && determinacy === "EXACT_DETERMINED",
            });
          }
        }
      }
    } else if (
      (semanticRole === "TANGENT_OR_DISTANCE_PERP" || semanticRole === "PROJECTION_FOOT")
      && w?.on
      && exactById.get(w.on)?.type === "plane3"
    ) {
      const exPlane = exactById.get(w.on)!;
      if (exPlane.point && exPlane.normal) {
        const p0 = parseFracVec3(exPlane.point);
        const nVec = parseFracVec3(exPlane.normal);
        for (const ball of exactOrigin.objects) {
          if (isSubEntity(ball.id) || ball.type !== "curved_solid" || ball.curved_kind !== "ball" || !ball.anchor || !ball.radius_sq) {
            continue;
          }
          const bCenter = parseFracVec3(ball.anchor);
          const wFromObj = w.from ? exactById.get(w.from) : undefined;
          const matchesBallCenter =
            w.from === ball.id
            || Boolean(wFromObj?.xyz && vIsZero(vSub(parseFracVec3(wFromObj.xyz), bCenter)));
          if (!matchesBallCenter) continue;
          const proj = projectPointOntoPlaneExact(bCenter, p0, nVec, exactOrigin.chart_metric);
          if (!proj) continue;
          const diff = vSub(proj.foot, bCenter);
          const d2 = metricDot(diff, diff, exactOrigin.chart_metric);
          const R2 = parseExactFrac(ball.radius_sq);
          if (d2[0] > 0n && fEq(d2, R2)) {
            verifiedRelations.push({
              kind: "tangent_sphere_plane",
              targetIds: [ball.id, exPlane.id],
              provenance: "DERIVED_VERIFIED",
              exactVerified: isObjConsistent,
              canDisplaySymbol: isObjConsistent && determinacy === "EXACT_DETERMINED",
            });
          }
        }
      }
    }

    let canonicalRole: CanonicalPedagogicalObjectRole = "CONSTRUCTION_GEOMETRY";
    if (
      informationCategory === "INTERNAL_MATH_RESULT"
      || obj.display_role === "measurement"
      || obj.display_role === "non_visual"
    ) {
      canonicalRole = "INTERNAL_MATH_RESULT";
    } else if (
      obj.display_role === "presentation_reference"
      || obj.semantic_role === "REFERENCE_EQUATOR"
      || obj.semantic_role === "REFERENCE_GREAT_CIRCLE"
      || semanticRole === "DUPLICATE_FACE_PLANE"
      || (obj.type === "circle3" && (
        classifyCircleSemanticRole(exactOrigin, exObj) === "REFERENCE_EQUATOR"
        || classifyCircleSemanticRole(exactOrigin, exObj) === "REFERENCE_GREAT_CIRCLE"
      ))
    ) {
      canonicalRole = "REFERENCE_GEOMETRY";
    } else if (
      semanticRole === "INTERSECTION_SECTION"
      || semanticRole === "INTERSECTION_CIRCLE"
      || semanticRole === "INTERSECTION_ELLIPSE"
      || semanticRole === "INTERSECTION_LINE"
      || semanticRole === "SECONDARY_CUT_SOLID"
    ) {
      canonicalRole = "RESULT_SECTION";
    } else if (determinacy === "ILLUSTRATIVE_GAUGE" || provenance === "ILLUSTRATIVE") {
      canonicalRole = "ILLUSTRATIVE_GEOMETRY";
    } else if (informationCategory === "GIVEN_FACT") {
      canonicalRole = "GIVEN_FACT";
    } else if (
      visibilityLifecycle === "AUXILIARY_ON_DEMAND"
      || visibilityLifecycle === "TRANSIENT_CONSTRUCTION_TOOL"
      || semanticRole === "AUXILIARY_OBJECT"
      || semanticRole === "AUXILIARY_PLANE"
      || (exObj.authoritative === false && exObj.semantic_role === "AUXILIARY_CONSTRUCTION")
    ) {
      canonicalRole = "AUXILIARY_GEOMETRY";
    }

    let objectLayer: SemanticConstructionLayer = "CONSTRUCTION_GEOMETRY";
    if (informationCategory === "INTERNAL_MATH_RESULT") {
      objectLayer = "INTERNAL_MATH_RESULT";
    } else if (canonicalRole === "REFERENCE_GEOMETRY") {
      objectLayer = "REFERENCE_GEOMETRY";
    } else if (canonicalRole === "RESULT_SECTION") {
      objectLayer = "RESULT_SECTION";
    } else if (
      semanticRole === "ALTITUDE_OR_AXIS"
      || semanticRole === "TANGENT_OR_DISTANCE_PERP"
      || semanticRole === "COMMON_PERPENDICULAR"
      || semanticRole === "PROJECTION_FOOT"
      || (
        canonicalRole !== "GIVEN_FACT"
        && verifiedRelations.some(
          (r) =>
            (r.kind === "line_perp_plane" || r.kind === "line_perp_line" || r.kind === "common_perpendicular")
            && r.canDisplaySymbol,
        )
      )
    ) {
      objectLayer = "RELATION_WITNESS";
    } else if (canonicalRole === "GIVEN_FACT") {
      objectLayer = "GIVEN_GEOMETRY";
    }

    objectsById.set(obj.id, {
      id: obj.id,
      geometricType,
      semanticRole,
      canonicalRole,
      objectLayer,
      provenance,
      determinacy,
      informationCategory,
      visibilityLifecycle,
      prerequisiteIds,
      verifiedRelations,
      visualPriorityTier,
    });
  }

  const constructionEvents: ConstructionEventContract[] = [];
  const provisionalContract: SemanticConstructionContract = {
    scene,
    exactOrigin,
    consistency,
    objectsById,
    constructionEvents,
  };
  _semanticContractCache.set(scene, { hybrid: curHybrid, sig: curSig, contract: provisionalContract });

  const freeSet = new Set(scene.free_objects);
  const birthAnchorById = new Map<string, number>();
  for (const fid of freeSet) {
    if (byId.has(fid)) birthAnchorById.set(fid, 0);
  }
  for (const ev of scene.events) {
    const evIds = [
      ...(ev.object ? [ev.object] : []),
      ...(Array.isArray(ev.objects) ? ev.objects : []),
    ];
    for (const eid of evIds) {
      if (!birthAnchorById.has(eid) && byId.has(eid)) {
        birthAnchorById.set(eid, ev.step_index);
      }
    }
  }
  const maxAnchor = scene.events.length > 0 ? Math.max(...scene.events.map((e) => e.step_index)) : 0;
  for (const obj of scene.objects) {
    if (isSubEntity(obj.id)) continue;
    if (!birthAnchorById.has(obj.id)) {
      birthAnchorById.set(obj.id, obj.origin === "free" ? 0 : maxAnchor);
    }
  }

  const stepsForScene = scene.events.length > 0 ? pedagogicalStepList(scene) : [];
  const stepGroupForAnchor = (anchor: number, hiddenInternal: boolean): number => {
    if (hiddenInternal) return -1;
    if (stepsForScene.length === 0) return 0;
    const hit = stepsForScene.findIndex((s) => anchor >= s.startAnchor && anchor <= s.anchor);
    if (hit >= 0) return hit;
    const after = stepsForScene.findIndex((s) => anchor <= s.anchor);
    return after >= 0 ? after : stepsForScene.length - 1;
  };

  const rolesCache = new Map<number, ReadonlyMap<string, StepVisualRoleEntry>>();
  const visualRoleAtAnchor = (anchor: number, id: string, hiddenInternal: boolean): StepVisualRole => {
    if (hiddenInternal) return "INACTIVE";
    let rMap = rolesCache.get(anchor);
    if (!rMap) {
      rMap = resolveStepVisualRoles(scene, anchor, { auxiliaryShown: false, selectedId: null });
      rolesCache.set(anchor, rMap);
    }
    return rMap.get(id)?.role ?? "CONTEXT";
  };

  const mapConstructionOperation = (spec: SemanticObjectContract, obj: SceneObject): ConstructionOperationKind => {
    if (spec.objectLayer === "INTERNAL_MATH_RESULT") return "INTERNAL_MEASUREMENT";
    if (spec.objectLayer === "REFERENCE_GEOMETRY") return "AUXILIARY_REFERENCE";
    if (obj.origin === "free" || spec.semanticRole === "GIVEN_VERTEX" || spec.semanticRole === "GIVEN_QUANTITY") {
      return "GIVEN_SEED";
    }
    switch (spec.semanticRole) {
      case "PRIMARY_SOLID":
      case "BASE_FACE":
      case "TOP_FACE":
      case "LATERAL_FACE":
        return "CONSTRUCT_SOLID_OR_FACE";
      case "CUTTING_PLANE":
      case "AUXILIARY_PLANE":
      case "DUPLICATE_FACE_PLANE":
        return "CONSTRUCT_PLANE";
      case "PROJECTION_FOOT":
      case "ALTITUDE_OR_AXIS":
      case "TANGENT_OR_DISTANCE_PERP":
      case "COMMON_PERPENDICULAR":
        return "PROJECT_PERPENDICULAR";
      case "INTERSECTION_POINT":
      case "INTERSECTION_LINE":
        return "INTERSECT_CARRIERS";
      case "INTERSECTION_SECTION":
      case "INTERSECTION_CIRCLE":
      case "INTERSECTION_ELLIPSE":
      case "SECONDARY_CUT_SOLID":
        return "INTERSECT_SECTION";
      case "MIDPOINT_OR_RATIO_POINT":
        return "INTERPOLATE_RATIO_OR_MIDPOINT";
      case "CURVED_RADIUS":
      case "CURVED_GENERATOR":
        return "EXTRACT_CURVED_WITNESS";
      default:
        return obj.type === "segment3" || obj.type === "line3"
          ? "CONNECT_SEGMENT_OR_LINE"
          : "CONSTRUCT_SOLID_OR_FACE";
    }
  };

  const normalizeCausalPrerequisites = (spec: SemanticObjectContract, obj: SceneObject): string[] => {
    const exObjDeps = (exactById.get(obj.id) ?? obj).depends ?? obj.depends ?? [];
    const hasDirectSelfDep = exObjDeps.some((d) => !isSubEntity(d) && d === obj.id);
    if (
      !hasDirectSelfDep
      && (obj.origin === "free" || spec.semanticRole === "GIVEN_VERTEX" || spec.semanticRole === "GIVEN_QUANTITY")
    ) {
      return [];
    }
    const out: string[] = [];
    if (hasDirectSelfDep) {
      out.push(obj.id);
    }
    for (const rawDep of spec.prerequisiteIds) {
      const targetId = isSubEntity(rawDep) ? rawDep.split("::")[0]! : rawDep;
      if (!targetId || (isSubEntity(rawDep) && targetId === obj.id) || !objectsById.has(targetId)) continue;
      if (!out.includes(targetId)) out.push(targetId);
    }
    return out;
  };

  for (const obj of scene.objects) {
    if (isSubEntity(obj.id)) continue;
    const spec = objectsById.get(obj.id);
    if (!spec) continue;
    const hiddenInternal = spec.informationCategory === "INTERNAL_MATH_RESULT" || spec.objectLayer === "INTERNAL_MATH_RESULT";
    const birthAnchor = birthAnchorById.get(obj.id) ?? 0;
    const stepGroup = stepGroupForAnchor(birthAnchor, hiddenInternal);
    const primaryWitness = spec.verifiedRelations.find((r) => r.exactVerified) ?? spec.verifiedRelations[0] ?? null;
    constructionEvents.push({
      object_id: obj.id,
      semantic_role: spec.semanticRole,
      object_layer: spec.objectLayer,
      provenance: spec.provenance,
      prerequisites: normalizeCausalPrerequisites(spec, obj),
      construction_operation: mapConstructionOperation(spec, obj),
      geometric_witness: primaryWitness,
      visibility_policy: spec.visibilityLifecycle,
      visual_role: visualRoleAtAnchor(birthAnchor, obj.id, hiddenInternal),
      step_group: stepGroup,
      birth_anchor: birthAnchor,
    });
  }

  return provisionalContract;
}

export function resolveSemanticObjectContract(
  scene: Scene3D,
  id: string,
): SemanticObjectContract | undefined {
  return getSemanticConstructionContract(scene).objectsById.get(id);
}

export type ConstructionContinuityViolationCode =
  | "CONTRADICTORY_GEOMETRY"
  | "UNDERDETERMINED_GEOMETRY"
  | "DUPLICATE_OBJECT_ID"
  | "PREREQUISITE_CYCLE"
  | "CAUSAL_BIRTH_ORDER"
  | "RESULT_BEFORE_OPERANDS"
  | "UNVERIFIED_OR_PREMATURE_WITNESS"
  | "COORDINATE_DRIFT_ACROSS_STEPS"
  | "SPHERE_RADIUS_CONTINUITY"
  | "SCRUB_FORWARD_BACKWARD_MISMATCH";

export interface ConstructionContinuityViolation {
  code: ConstructionContinuityViolationCode;
  objectId: string | null;
  detail: string;
}

export interface ConstructionContinuityReport {
  valid: boolean;
  failureReason: "CONTRADICTORY_GEOMETRY" | "UNDERDETERMINED_GEOMETRY" | "CONTINUITY_VIOLATION" | null;
  stepCount: number;
  violations: ConstructionContinuityViolation[];
}

function objectCoordinateSignature(o: SceneObject): string {
  const vec = (v: ExactVec3 | null | undefined) => (v ? v.join(",") : "");
  const vecList = (vs: readonly ExactVec3[] | undefined) => (vs ? vs.map((x) => x.join(",")).join(";") : "");
  return [
    o.type,
    vec(o.xyz),
    vec(o.point),
    vec(o.point_a),
    vec(o.point_b),
    vec(o.center),
    vec(o.anchor),
    vec(o.apex_or_top),
    vec(o.normal),
    vec(o.direction),
    o.radius_sq ?? "",
    o.height_sq ?? "",
    vecList(o.vertices),
    vecList(o.polygon),
    vecList(o.endpoints),
  ].join("|");
}

export function verifyConstructionContinuity(scene: Scene3D): ConstructionContinuityReport {
  const violations: ConstructionContinuityViolation[] = [];
  const contract = getSemanticConstructionContract(scene);

  if (!contract.consistency.valid) {
    for (const c of contract.consistency.contradictions) {
      violations.push({
        code: "CONTRADICTORY_GEOMETRY",
        objectId: c.objectId,
        detail: `${c.title}: ${c.explanation}`,
      });
    }
  }

  const seenIds = new Set<string>();
  for (const o of scene.objects) {
    if (seenIds.has(o.id)) {
      violations.push({
        code: "DUPLICATE_OBJECT_ID",
        objectId: o.id,
        detail: `Duplicate object id '${o.id}' in scene.objects`,
      });
    }
    seenIds.add(o.id);
  }

  for (const spec of contract.objectsById.values()) {
    if (spec.geometricType === "sub_entity" || spec.geometricType === "quantity") continue;
    if (spec.determinacy === "UNDERDETERMINED") {
      violations.push({
        code: "UNDERDETERMINED_GEOMETRY",
        objectId: spec.id,
        detail: `Geometric object '${spec.id}' is metrically/structurally UNDERDETERMINED`,
      });
    }
  }

  const eventById = new Map<string, ConstructionEventContract>();
  for (const ev of contract.constructionEvents) {
    eventById.set(ev.object_id, ev);
  }

  // 1. Cycle check on causal prerequisite graph
  const visitState = new Map<string, 0 | 1 | 2>();
  const dfsCycle = (id: string, stack: string[]): void => {
    visitState.set(id, 1);
    const ev = eventById.get(id);
    for (const depId of ev?.prerequisites ?? []) {
      const st = visitState.get(depId) ?? 0;
      if (st === 1) {
        violations.push({
          code: "PREREQUISITE_CYCLE",
          objectId: id,
          detail: `Cycle in construction prerequisites: ${[...stack, id, depId].join(" -> ")}`,
        });
      } else if (st === 0 && eventById.has(depId)) {
        dfsCycle(depId, [...stack, id]);
      }
    }
    visitState.set(id, 2);
  };
  for (const id of eventById.keys()) {
    if ((visitState.get(id) ?? 0) === 0) {
      dfsCycle(id, []);
    }
  }

  const exactOrigin = contract.exactOrigin;
  const exactById = new Map(exactOrigin.objects.map((o) => [o.id, o]));
  const sceneById = new Map(scene.objects.map((o) => [o.id, o]));

  // 2. Causal birth order, result-after-operands, and relation-witness grounding
  for (const ev of contract.constructionEvents) {
    if (ev.step_group < 0) continue;
    for (const depId of ev.prerequisites) {
      if (depId === ev.object_id) continue;
      const depEv = eventById.get(depId);
      if (!depEv) continue;
      if (depEv.object_layer === "INTERNAL_MATH_RESULT") {
        violations.push({
          code: "CAUSAL_BIRTH_ORDER",
          objectId: ev.object_id,
          detail: `Visual object '${ev.object_id}' depends on hidden math result '${depId}'`,
        });
      } else if (
        depEv.step_group >= 0
        && (
          depEv.step_group > ev.step_group
          || (depEv.step_group === ev.step_group && depEv.birth_anchor > ev.birth_anchor)
        )
      ) {
        violations.push({
          code: "CAUSAL_BIRTH_ORDER",
          objectId: ev.object_id,
          detail: `Object '${ev.object_id}' (step ${ev.step_group}, anchor ${ev.birth_anchor}) appears before prerequisite '${depId}' (step ${depEv.step_group}, anchor ${depEv.birth_anchor})`,
        });
      }
    }

    if (ev.object_layer === "RESULT_SECTION" && ev.prerequisites.length > 0) {
      for (const depId of ev.prerequisites) {
        const depEv = eventById.get(depId);
        if (
          depEv
          && depEv.step_group >= 0
          && (
            depEv.step_group > ev.step_group
            || (depEv.step_group === ev.step_group && depEv.birth_anchor > ev.birth_anchor)
          )
        ) {
          violations.push({
            code: "RESULT_BEFORE_OPERANDS",
            objectId: ev.object_id,
            detail: `Result section '${ev.object_id}' appears before operand '${depId}'`,
          });
        }
      }
    }

    const spec = contract.objectsById.get(ev.object_id);
    const exObj = exactById.get(ev.object_id) ?? sceneById.get(ev.object_id);
    const explicitWitness = exObj?.perpendicular_witness ?? exObj?.annotation?.witness;
    if (spec && spec.determinacy !== "ILLUSTRATIVE_GAUGE" && spec.determinacy !== "UNDERDETERMINED") {
      if (explicitWitness) {
        const wRec = explicitWitness as unknown as Record<string, unknown>;
        const markedUnverified = wRec.status === "UNVERIFIED" || wRec.can_present_as_proven === false;
        const hasVerifiedPerp = spec.verifiedRelations.some(
          (r) =>
            (r.kind === "line_perp_plane" || r.kind === "line_perp_line" || r.kind === "common_perpendicular")
            && r.exactVerified,
        );
        if (!markedUnverified && !hasVerifiedPerp) {
          violations.push({
            code: "UNVERIFIED_OR_PREMATURE_WITNESS",
            objectId: ev.object_id,
            detail: `Explicit perpendicular witness on '${ev.object_id}' is not exactVerified`,
          });
        }
        if (spec.geometricType !== "quantity" && exObj?.perpendicular_witness) {
          const pw = exObj.perpendicular_witness;
          const witnessRefs = [pw.on, pw.foot_id, pw.from, pw.second?.on, pw.second?.foot_id].filter(
            (x): x is string => Boolean(x),
          );
          for (const rawRef of witnessRefs) {
            const targetId = isSubEntity(rawRef) ? rawRef.split("::")[0]! : rawRef;
            if (!targetId || targetId === ev.object_id) continue;
            const targetEv = eventById.get(targetId);
            if (
              targetEv
              && targetEv.step_group >= 0
              && (
                targetEv.step_group > ev.step_group
                || (targetEv.step_group === ev.step_group && targetEv.birth_anchor > ev.birth_anchor)
              )
            ) {
              violations.push({
                code: "UNVERIFIED_OR_PREMATURE_WITNESS",
                objectId: ev.object_id,
                detail: `Perpendicular witness on '${ev.object_id}' (step ${ev.step_group}, anchor ${ev.birth_anchor}) precedes carrier/foot '${targetId}' (step ${targetEv.step_group}, anchor ${targetEv.birth_anchor})`,
              });
            }
          }
        }
      } else if (
        ev.object_layer === "RELATION_WITNESS"
        && spec.verifiedRelations.length > 0
        && !spec.verifiedRelations.some((r) => r.exactVerified)
      ) {
        violations.push({
          code: "UNVERIFIED_OR_PREMATURE_WITNESS",
          objectId: ev.object_id,
          detail: `Relation witness '${ev.object_id}' is not exactVerified`,
        });
      }
    }
  }

  // 3. Coordinate identity across steps, sphere radius continuity, and forward/backward scrubbing equivalence
  const steps = scene.events.length > 0 ? pedagogicalStepList(scene) : [];
  const firstSeenCoord = new Map<string, string>();

  for (let s = 0; s < steps.length; s += 1) {
    const k = steps[s]!.anchor;
    const vis = objectsAt(scene, k);
    const visIds = new Set(vis.map((v) => v.id));
    for (const o of vis) {
      if (isSubEntity(o.id)) continue;
      const sig = objectCoordinateSignature(o);
      const prevSig = firstSeenCoord.get(o.id);
      if (prevSig === undefined) {
        firstSeenCoord.set(o.id, sig);
      } else if (prevSig !== sig) {
        violations.push({
          code: "COORDINATE_DRIFT_ACROSS_STEPS",
          objectId: o.id,
          detail: `Object '${o.id}' changed coordinates/type at step ${s}`,
        });
      }

      if (o.type === "segment3") {
        const exSeg = exactById.get(o.id) ?? o;
        const spec = contract.objectsById.get(o.id);
        const cRole = classifyCurvedSegmentRole(exactOrigin, exSeg);
        const depBall = (exSeg.depends ?? o.depends ?? [])
          .map((d) => exactById.get(d) ?? sceneById.get(d))
          .find((cand) => cand?.type === "curved_solid" && cand.curved_kind === "ball");
        const targetBall =
          cRole?.kind === "radius" && cRole.host.curved_kind === "ball"
            ? cRole.host
            : (depBall?.anchor && !cRole && !exSeg.perpendicular_witness && spec?.semanticRole !== "TANGENT_OR_DISTANCE_PERP" && spec?.semanticRole !== "ALTITUDE_OR_AXIS" && ((exSeg.endpoint_ids ?? []).some((eid) => { const px = (exactById.get(eid) ?? sceneById.get(eid))?.xyz; return Boolean(px && vIsZero(vSub(parseFracVec3(px), parseFracVec3(depBall.anchor!)))); }) || (exSeg.endpoints ?? []).some((ep) => vIsZero(vSub(parseFracVec3(ep), parseFracVec3(depBall.anchor!))))) ? depBall : null);
        if (targetBall?.anchor && targetBall.radius_sq) {
          const epIds = exSeg.endpoint_ids ?? o.endpoint_ids ?? [];
          const p0 = epIds[0] ? (exactById.get(epIds[0]) ?? sceneById.get(epIds[0])) : undefined;
          const p1 = epIds[1] ? (exactById.get(epIds[1]) ?? sceneById.get(epIds[1])) : undefined;
          if (
            epIds.length !== 2
            || p0?.type !== "point3"
            || p1?.type !== "point3"
            || !p0.xyz
            || !p1.xyz
            || !visIds.has(epIds[0])
            || !visIds.has(epIds[1])
          ) {
            violations.push({
              code: "SPHERE_RADIUS_CONTINUITY",
              objectId: o.id,
              detail: `Sphere radius '${o.id}' does not connect two visible point3 objects at step ${s}`,
            });
          } else {
            const cVec = parseFracVec3(targetBall.anchor);
            const v0 = parseFracVec3(p0.xyz);
            const v1 = parseFracVec3(p1.xyz);
            const touchesCenter = vIsZero(vSub(v0, cVec)) || vIsZero(vSub(v1, cVec));
            const dSq = metricDot(vSub(v1, v0), vSub(v1, v0), exactOrigin.chart_metric);
            if (!touchesCenter || !fEq(dSq, parseExactFrac(targetBall.radius_sq))) {
              violations.push({
                code: "SPHERE_RADIUS_CONTINUITY",
                objectId: o.id,
                detail: `Sphere radius '${o.id}' does not connect ball center to sphere surface (|IX|^2 = R^2)`,
              });
            }
          }
        }
      }
    }
  }

  const forwardSnap = steps.map((st) => {
    const visIds = objectsAt(scene, st.anchor).map((o) => o.id).join(",");
    const roles = [...resolveStepVisualRoles(scene, st.anchor, { auxiliaryShown: false, selectedId: null }).entries()]
      .map(([id, dec]) => `${id}:${dec.role}:${dec.visible}`)
      .join(",");
    const groups = buildStepEntityGroups(scene, st.anchor, { steps });
    return `${visIds}||${roles}||${groups.primary.map((x) => x.id).join(",")}`;
  });
  for (let s = steps.length - 1; s >= 0; s -= 1) {
    const st = steps[s]!;
    const visIds = objectsAt(scene, st.anchor).map((o) => o.id).join(",");
    const roles = [...resolveStepVisualRoles(scene, st.anchor, { auxiliaryShown: false, selectedId: null }).entries()]
      .map(([id, dec]) => `${id}:${dec.role}:${dec.visible}`)
      .join(",");
    const groups = buildStepEntityGroups(scene, st.anchor, { steps });
    const bwdSnap = `${visIds}||${roles}||${groups.primary.map((x) => x.id).join(",")}`;
    if (bwdSnap !== forwardSnap[s]) {
      violations.push({
        code: "SCRUB_FORWARD_BACKWARD_MISMATCH",
        objectId: null,
        detail: `Forward/backward state mismatch at step ${s}`,
      });
    }
  }

  let failureReason: ConstructionContinuityReport["failureReason"] = null;
  if (violations.some((v) => v.code === "CONTRADICTORY_GEOMETRY")) {
    failureReason = "CONTRADICTORY_GEOMETRY";
  } else if (violations.some((v) => v.code === "UNDERDETERMINED_GEOMETRY")) {
    failureReason = "UNDERDETERMINED_GEOMETRY";
  } else if (violations.length > 0) {
    failureReason = "CONTINUITY_VIOLATION";
  }

  return {
    valid: violations.length === 0,
    failureReason,
    stepCount: steps.length,
    violations,
  };
}


function soDemCanhTiengViet(n: number): string {
  switch (n) {
    case 3:
      return "ba";
    case 4:
      return "bốn";
    case 5:
      return "năm";
    case 6:
      return "sáu";
    default:
      return String(n);
  }
}

export function canonicalizeSceneFaceTokensInText(scene: Scene3D, rawText: string): string {
  if (!rawText) return "";
  const exactOrigin = exactSceneOriginOf(scene);
  const byId = new Map(exactOrigin.objects.map((o) => [o.id, o]));
  const apexSyms = structuralApexSymsOfScene(exactOrigin);
  const canonFaceBySortedKey = new Map<string, string>();

  const registerFaceSyms = (syms: string[], prefOrder: string[]) => {
    if (syms.length < 3 || syms.length > 6) return;
    if (!syms.every((s) => /^[A-Z][0-9′']*$/u.test(s))) return;
    const uniq = new Set(syms);
    if (uniq.size !== syms.length) return;
    const sortedKey = [...syms].sort().join("|");
    if (canonFaceBySortedKey.has(sortedKey)) return;
    const cyc = formatCycleNotation(syms, [...apexSyms, ...prefOrder]);
    if (cyc) canonFaceBySortedKey.set(sortedKey, cyc);
  };

  for (const o of exactOrigin.objects) {
    if (o.type === "solid" && o.vertex_ids?.length && o.faces?.length) {
      const pref = preferredPointOrderForPolygon(exactOrigin, o);
      for (const f of o.faces) {
        const fSyms = f
          .map((vi) => shortSym(byId.get(o.vertex_ids![vi]!)))
          .filter(Boolean);
        registerFaceSyms(fSyms, pref);
      }
    } else if (o.type === "polygon3" || o.type === "section") {
      const pref = preferredPointOrderForPolygon(exactOrigin, o);
      if (o.type === "section") {
        const sd = sectionDetails(exactOrigin, o.id);
        if (sd && sd.vertexNames.length >= 3) {
          registerFaceSyms([...sd.vertexNames], pref);
        }
      } else {
        const rawIds = (o.vertex_ids?.length ? o.vertex_ids : o.depends) ?? [];
        const fSyms = rawIds
          .map((id) => byId.get(id))
          .filter((pt): pt is SceneObject => Boolean(pt && pt.type === "point3"))
          .map((pt) => shortSym(pt))
          .filter(Boolean);
        registerFaceSyms(fSyms, pref);
      }
    }
  }

  if (canonFaceBySortedKey.size === 0) return rawText;
  return rawText.replace(/\(([A-Z][0-9′']*(?:[A-Z][0-9′']*){2,5})\)/gu, (full, inner: string) => {
    const tokens = inner.match(/[A-Z][0-9′']*/gu) ?? [];
    if (tokens.length < 3 || tokens.join("") !== inner) return full;
    const key = [...tokens].sort().join("|");
    return canonFaceBySortedKey.get(key) ?? full;
  });
}

function consolidateParallelIntersectionJustifications(items: readonly string[]): string[] {
  const re =
    /^Vì\s+(\([^)]+\))\s+song song với\s+([A-Z0-9′']+)\s+và\s+\2\s+nằm trong mặt\s+(\([^)]+\)),\s*nên giao tuyến của\s+\1\s+với mặt\s+\3\s+song song với\s+\2\.?$/u;
  const groups = new Map<string, { indices: number[]; pairs: { edge: string; face: string }[] }>();
  items.forEach((item, idx) => {
    const m = item.match(re);
    if (!m) return;
    const mp = m[1]!;
    const edge = m[2]!;
    const face = m[3]!;
    let g = groups.get(mp);
    if (!g) {
      g = { indices: [], pairs: [] };
      groups.set(mp, g);
    }
    g.indices.push(idx);
    if (!g.pairs.some((p) => p.edge === edge && p.face === face)) {
      g.pairs.push({ edge, face });
    }
  });

  const skipIndices = new Set<number>();
  const replacementAtFirstIdx = new Map<number, string>();
  for (const [mp, g] of groups.entries()) {
    if (g.indices.length < 2) continue;
    const firstIdx = g.indices[0]!;
    for (const idx of g.indices) skipIndices.add(idx);
    const pairText = g.pairs.map((p) => `${p.edge} ⊂ ${p.face}`).join(", ");
    replacementAtFirstIdx.set(
      firstIdx,
      `Định lý giao tuyến song song: mặt phẳng ${mp} lần lượt song song với ${pairText}, nên giao tuyến trên từng mặt tương ứng song song với cạnh đó.`,
    );
  }

  const out: string[] = [];
  items.forEach((item, idx) => {
    const rep = replacementAtFirstIdx.get(idx);
    if (rep) out.push(rep);
    if (!skipIndices.has(idx)) out.push(item);
  });
  return out;
}

function stripTrailingNumericAssignment(raw: string): string {
  const trimmed = raw.replace(/«([^»]+)»/gu, "$1").replace(/\s+/gu, " ").trim();
  if (!trimmed) return "";
  return trimmed
    .replace(
      /\s*(?:⇒|->|=)\s*[-+(]*(?:\d|[√π]|\\sqrt|\\frac|(?:[ahb]\b|[aRhb](?=\s*[0-9√π^²³/*+-])))[^∩⊥∥;,]*$/u,
      "",
    )
    .trim();
}

/**
 * `PedagogicalNarrationPolicy` (§6):
 * Tách bạch ở tầng sinh & chọn nội dung thành 3 phần:
 * - `actionTitle`: Hành động dựng hình rõ ràng học sinh cần thực hiện/quan sát.
 * - `conciseRationale`: 1–2 quan hệ hình học trực tiếp nhất đã kiểm chứng trên ℚ³ (không dùng CSS line-clamp, không cắt chuỗi theo ký tự).
 * - `detailedEvidence`: Mọi phương trình giao tuyến từng mặt, quan hệ song song/vuông góc, tiền đề & giải thích chi tiết (truy cập qua "Xem giải thích").
 */
function computeExactPolygonNormal(
  polyObj: SceneObject,
  byId?: ReadonlyMap<string, SceneObject>,
): { p0: FracVec3; normal: FracVec3 } | null {
  const rawPts: FracVec3[] = [];
  const coordSrc = polyObj.polygon ?? polyObj.vertices;
  if (coordSrc && coordSrc.length >= 3) {
    for (const c of coordSrc) rawPts.push(parseFracVec3(c));
  } else if (byId) {
    const vIds = polyObj.vertex_ids?.length ? polyObj.vertex_ids : (polyObj.depends ?? []);
    for (const vid of vIds) {
      const vx = byId.get(vid)?.xyz;
      if (vx) rawPts.push(parseFracVec3(vx));
    }
  }
  if (rawPts.length < 3) return null;
  const p0 = rawPts[0]!;
  for (let i = 1; i + 1 < rawPts.length; i += 1) {
    const u = vSub(rawPts[i]!, p0);
    const v = vSub(rawPts[i + 1]!, p0);
    const n = vCross(u, v);
    if (!vIsZero(n)) return { p0, normal: n };
  }
  return null;
}

export function buildPedagogicalStepNarration(
  scene: Scene3D,
  step: Pick<
    PedagogicalStepItem,
    "index" | "startAnchor" | "anchor" | "label" | "title" | "subtitle" | "targetIds" | "prerequisiteIds"
  >,
): PedagogicalStepNarration {
  const exactOrigin = exactSceneOriginOf(scene);
  const byId = new Map(exactOrigin.objects.map((o) => [o.id, o]));
  const rawTitle = (step.title || step.label || "").replace(/«([^»]+)»/gu, "$1").trim();
  const safeTitle = learnerTextIsSafe(scene, rawTitle) ? rawTitle : stripTrailingNumericAssignment(rawTitle);
  const actionTitle = canonicalizeSceneFaceTokensInText(scene, safeTitle);

  const rawSub = (step.subtitle || "").replace(/«([^»]+)»/gu, "$1").trim();
  const safeSub = learnerTextIsSafe(scene, rawSub) ? rawSub : stripTrailingNumericAssignment(rawSub);
  const canonicalSubtitle = canonicalizeSceneFaceTokensInText(scene, safeSub);

  const rawJustSet = new Set<string>();
  for (const ev of scene.events) {
    if (ev.step_index < step.startAnchor || ev.step_index > step.anchor) continue;
    const jt = ev.justification_text?.trim() ?? "";
    if (jt.length > 0 && learnerTextIsSafe(scene, jt)) {
      rawJustSet.add(jt);
    }
  }
  for (const gj of geometryJustificationsAt(scene, step.anchor)) {
    const trimmed = gj.trim();
    if (trimmed.length > 0 && learnerTextIsSafe(scene, trimmed)) {
      rawJustSet.add(trimmed);
    }
  }

  const normalizedJusts = consolidateParallelIntersectionJustifications(
    [...rawJustSet]
      .map((s) => canonicalizeSceneFaceTokensInText(scene, stripTrailingNumericAssignment(s)))
      .filter((s) => s.length > 0 && s !== actionTitle && s !== canonicalSubtitle),
  );

  const presentIdsAtAnchor = new Set(objectsAt(scene, step.anchor).map((o) => o.id));
  const progressAtAnchor = new Map(
    (scene.formation?.steps[step.anchor]?.geometry_progress ?? []).map((gp) => [gp.object_id, gp]),
  );
  const resolveSolidBaseFacesExact = (sObj: SceneObject): number[][] => {
    const faces = sObj.faces ?? [];
    const vIds = sObj.vertex_ids ?? [];
    if (faces.length === 0 || vIds.length === 0) return [];
    const faceNormalOf = (f: number[]): FracVec3 | null => {
      const pts = f
        .map((vi) => (vIds[vi] ? byId.get(vIds[vi]!)?.xyz : undefined) ?? sObj.vertices?.[vi])
        .filter((v): v is ExactVec3 => Boolean(v))
        .map(parseFracVec3);
      if (pts.length < 3) return null;
      for (let i = 1; i + 1 < pts.length; i += 1) {
        const n = vCross(vSub(pts[i]!, pts[0]!), vSub(pts[i + 1]!, pts[0]!));
        if (!vIsZero(n)) return n;
      }
      return null;
    };
    const explicitBaseVertSets = exactOrigin.objects
      .filter(
        (cand) =>
          cand.type === "polygon3"
          && !isSubEntity(cand.id)
          && (cand.surface_role === "BASE_REGION"
            || (cand.formation_roles ?? []).includes("CONSTRUCT_BASE")
            || (cand.formation_roles ?? []).includes("CONSTRUCT_TRANSLATED_FACE"))
          && !isPolyhedronLateralOrAuxFacePolygon(exactOrigin, cand),
      )
      .map((cand) => new Set((cand.vertex_ids?.length ? cand.vertex_ids : cand.depends) ?? []));
    const matchedExplicit = faces.filter((f) => {
      const fIdSet = new Set(f.map((vi) => vIds[vi]).filter(Boolean));
      return explicitBaseVertSets.some(
        (bs) => bs.size === fIdSet.size && [...fIdSet].every((id) => bs.has(id!)),
      );
    });
    if (isTwoBasePolyhedronSolid(exactOrigin, sObj)) {
      if (matchedExplicit.length >= 2) return matchedExplicit;
      if (matchedExplicit.length === 1) {
        const b0 = matchedExplicit[0]!;
        const n0 = faceNormalOf(b0);
        const partner = faces.find((f) => {
          if (f === b0 || f.some((vi) => b0.includes(vi))) return false;
          const nf = faceNormalOf(f);
          return Boolean(n0 && nf && vIsZero(vCross(n0, nf)));
        });
        return partner ? [b0, partner] : [b0];
      }
      for (let i = 0; i < faces.length; i += 1) {
        const fi = faces[i]!;
        const ni = faceNormalOf(fi);
        if (!ni) continue;
        for (let j = i + 1; j < faces.length; j += 1) {
          const fj = faces[j]!;
          if (fj.some((vi) => fi.includes(vi))) continue;
          const nj = faceNormalOf(fj);
          if (nj && vIsZero(vCross(ni, nj))) return [fi, fj];
        }
      }
      return [faces[0]!];
    }
    if (matchedExplicit.length >= 1) return [matchedExplicit[0]!];
    return [faces.reduce((best, f) => (f.length > best.length ? f : best), faces[0]!)];
  };

  const normNarCompare = (s: string): string =>
    s
      .toLowerCase()
      .replace(/[.;:,!?—–-]+/gu, " ")
      .replace(/\s+/gu, " ")
      .trim();

  const stripActionVerbPrefix = (s: string): string =>
    normNarCompare(s)
      .replace(/^(?:hạ đoạn vuông góc|kẻ đoạn vuông góc|dựng đoạn vuông góc|nối đoạn vuông góc|nối đoạn thẳng|hạ|kẻ|dựng|nối|vẽ)\s+/u, "")
      .trim();

  const isSameActionClause = (a: string, b: string): boolean => {
    const na = normNarCompare(a);
    const nb = normNarCompare(b);
    if (!na || !nb) return false;
    if (na === nb) return true;
    const sa = stripActionVerbPrefix(a);
    const sb = stripActionVerbPrefix(b);
    return sa.length >= 4 && sa === sb;
  };

  const isGenericStepBoilerplate = (s: string): boolean =>
    /^(?:(?:tìm|xác định) đường thẳng chung (?:của|đi qua các điểm chung của) hai mặt phẳng.*|nối các đỉnh (?:đã xác định )?(?:để hoàn thiện|tạo thành) miền.*|nối các đoạn giao tuyến trên từng mặt của khối để khép kín miền thiết diện.*)$/iu.test(
      s.trim(),
    );

  const filterDistinctEvidence = (
    titleText: string,
    conciseText: string,
    rawItems: readonly string[],
  ): string[] => {
    const out: string[] = [];
    const seen = new Set<string>();
    const nTitle = normNarCompare(titleText);
    const nConcise = normNarCompare(conciseText);
    const combinedVisible = `${nTitle} ${nConcise}`.trim();
    const conciseIsSpecific = nConcise.length > 0 && !isGenericStepBoilerplate(conciseText);
    for (const raw of rawItems) {
      const trimmed = raw.trim();
      if (!trimmed) continue;
      const nItem = normNarCompare(trimmed);
      if (!nItem || nItem === nTitle || nItem === nConcise || isSameActionClause(trimmed, titleText) || seen.has(nItem)) continue;
      if (combinedVisible.includes(nItem)) continue;
      const rawClauses = trimmed.split(/\s*;\s*/u).map((c) => c.trim()).filter(Boolean);
      if (rawClauses.length >= 2 && isSameActionClause(rawClauses[0]!, titleText)) {
        const restNorm = normNarCompare(rawClauses.slice(1).join(" ").replace(/^(?:vì|do|nên)\s+/iu, ""));
        if (!restNorm || combinedVisible.includes(restNorm) || nConcise.includes(restNorm)) continue;
      }
      if (conciseIsSpecific && isGenericStepBoilerplate(trimmed)) continue;
      seen.add(nItem);
      out.push(trimmed);
    }
    return out;
  };

  const hostSolids = exactOrigin.objects.filter((o) => o.type === "solid");
  const hostCurvedSolids = exactOrigin.objects.filter((o) => o.type === "curved_solid");
  const findClosedSectionTarget = (): SceneObject | undefined =>
    step.targetIds
      .map((id) => {
        const sceneObj = scene.objects.find((x) => x.id === id);
        const exObj = byId.get(id);
        if (!exObj) return undefined;
        const isPolySec =
          exObj.type === "section"
          || (exObj.type === "polygon3"
            && (
              vaiTroMien(exObj) === "section"
              || (sceneObj !== undefined && vaiTroMien(sceneObj) === "section")
              || (hostCurvedSolids.length > 0 && (exObj.display_group ?? []).includes("target"))
            )
            && !isPolyhedronLateralOrAuxFacePolygon(exactOrigin, exObj));
        if (!isPolySec) return undefined;
        const gp = progressAtAnchor.get(id);
        const isClosedNow = gp ? gp.closed : (sceneObj?.closed ?? exObj.closed) !== false;
        if (!isClosedNow) return undefined;
        const secCoords = exObj.polygon ?? exObj.vertices ?? [];
        for (const cPt of secCoords) {
          const cp = parseFracVec3(cPt);
          const namedMatch = exactOrigin.objects.find(
            (p) => !isSubEntity(p.id) && p.type === "point3" && p.xyz && vIsZero(vSub(parseFracVec3(p.xyz), cp)),
          );
          if (namedMatch && !presentIdsAtAnchor.has(namedMatch.id)) return undefined;
        }
        return exObj;
      })
      .find((o): o is SceneObject => Boolean(o));

  const closedSectionTarget = findClosedSectionTarget();
  const polySectionTarget = hostSolids.length > 0 ? closedSectionTarget : undefined;
  const curvedPolySectionTarget =
    !polySectionTarget && hostCurvedSolids.length > 0 ? closedSectionTarget : undefined;

  if (polySectionTarget) {
    const basis = deriveExactPolygonMathBasis(exactOrigin, polySectionTarget);
    const secNormInfo = computeExactPolygonNormal(polySectionTarget, byId);
    const secNotation =
      basis?.cycleNotation
      ?? (() => {
        const m = actionTitle.match(/\([A-Z0-9′']{3,}\)/u);
        return m ? m[0] : polySectionTarget.notation?.trim() || "đa giác";
      })();

    let parallelBaseNotation: string | null = null;
    let hostSolid: SceneObject | undefined;
    if (secNormInfo && !vIsZero(secNormInfo.normal)) {
      for (const cand of exactOrigin.objects) {
        if (cand.id === polySectionTarget.id || isSubEntity(cand.id)) continue;
        if (
          cand.type === "polygon3"
          && (cand.surface_role === "BASE_REGION" || (cand.formation_roles ?? []).includes("CONSTRUCT_BASE"))
          && !isPolyhedronLateralOrAuxFacePolygon(exactOrigin, cand)
        ) {
          const bn = computeExactPolygonNormal(cand, byId);
          if (bn && !vIsZero(bn.normal) && vIsZero(vCross(secNormInfo.normal, bn.normal))) {
            const bBasis = deriveExactPolygonMathBasis(exactOrigin, cand);
            parallelBaseNotation = bBasis?.cycleNotation ?? cand.notation?.trim() ?? null;
            break;
          }
        }
      }
      for (const sObj of hostSolids) {
        if (!sObj.vertex_ids?.length || !sObj.faces?.length) continue;
        if (!hostSolid) hostSolid = sObj;
        if (!parallelBaseNotation) {
          const baseFaces = resolveSolidBaseFacesExact(sObj);
          for (const baseFace of baseFaces) {
            if (baseFace.length < 3) continue;
            const fPts = baseFace.map((vi) => sObj.vertices?.[vi]).filter((v): v is ExactVec3 => Boolean(v));
            if (fPts.length >= 3) {
              const p0 = parseFracVec3(fPts[0]!);
              const nB = vCross(vSub(parseFracVec3(fPts[1]!), p0), vSub(parseFracVec3(fPts[2]!), p0));
              if (!vIsZero(nB) && vIsZero(vCross(secNormInfo.normal, nB))) {
                const fSyms = baseFace.map((vi) => shortSym(byId.get(sObj.vertex_ids![vi]!))).filter(Boolean);
                parallelBaseNotation = formatCycleNotation(
                  fSyms,
                  [...structuralApexSymsOfScene(exactOrigin), ...preferredPointOrderForPolygon(exactOrigin, sObj)],
                );
                break;
              }
            }
          }
        }
      }
    }

    const secPts = polySectionTarget.polygon ?? polySectionTarget.vertices ?? [];
    let allVerticesAreLateralEdgeMidpoints = false;
    if (hostSolid?.vertex_ids?.length && hostSolid.faces?.length && secPts.length >= 3) {
      const baseFaces = resolveSolidBaseFacesExact(hostSolid);
      const baseEdgeKeys = new Set<string>();
      for (const bf of baseFaces) {
        for (let i = 0; i < bf.length; i += 1) {
          const ia = bf[i]!;
          const ib = bf[(i + 1) % bf.length]!;
          baseEdgeKeys.add(ia < ib ? `${ia}-${ib}` : `${ib}-${ia}`);
        }
      }
      const lateralEdges: [ExactVec3, ExactVec3][] = [];
      const seenEdge = new Set<string>();
      for (const f of hostSolid.faces) {
        for (let i = 0; i < f.length; i += 1) {
          const ia = f[i]!;
          const ib = f[(i + 1) % f.length]!;
          const key = ia < ib ? `${ia}-${ib}` : `${ib}-${ia}`;
          if (baseEdgeKeys.has(key) || seenEdge.has(key)) continue;
          seenEdge.add(key);
          const va = hostSolid.vertices?.[ia];
          const vb = hostSolid.vertices?.[ib];
          if (va && vb) lateralEdges.push([va, vb]);
        }
      }
      if (lateralEdges.length >= secPts.length) {
        allVerticesAreLateralEdgeMidpoints = secPts.every((sp) =>
          lateralEdges.some(([ea, eb]) => isExactMidpointVec(sp, ea, eb)),
        );
      }
    }

    const parallelPairs = basis?.parallelPairs ?? [];
    let conciseRationale: string;
    if (allVerticesAreLateralEdgeMidpoints && parallelBaseNotation) {
      conciseRationale = `Thiết diện ${secNotation} đi qua trung điểm của ${soDemCanhTiengViet(secPts.length)} cạnh bên và song song với mặt đáy ${parallelBaseNotation}.`;
    } else if (parallelBaseNotation && parallelPairs.length >= 2) {
      conciseRationale = `Mặt phẳng cắt song song với mặt đáy ${parallelBaseNotation}, tạo các giao tuyến song song với cạnh đáy và khép kín thiết diện ${secNotation}.`;
    } else if (parallelPairs.length > 0 && parallelPairs.length <= 2) {
      conciseRationale = `Nối các đoạn giao tuyến trên các mặt khối (${parallelPairs.join(", ")}) để khép kín thiết diện ${secNotation}.`;
    } else if (parallelPairs.length > 2) {
      conciseRationale = `Nối các đoạn giao tuyến song song (${parallelPairs.slice(0, 4).join(", ")}) trên các mặt khối để khép kín thiết diện ${secNotation}.`;
    } else {
      const coincidentSolidEdges: string[] = [];
      const faceTraceEdges: string[] = [];
      if (hostSolid?.vertex_ids?.length && hostSolid.vertices?.length && hostSolid.faces?.length && secPts.length >= 3) {
        const solidEdgePairs: { a: FracVec3; b: FracVec3; symA: string; symB: string }[] = [];
        const seenSE = new Set<string>();
        for (const f of hostSolid.faces) {
          for (let i = 0; i < f.length; i += 1) {
            const ia = f[i]!;
            const ib = f[(i + 1) % f.length]!;
            const k = ia < ib ? `${ia}-${ib}` : `${ib}-${ia}`;
            if (seenSE.has(k)) continue;
            seenSE.add(k);
            const va = hostSolid.vertices[ia];
            const vb = hostSolid.vertices[ib];
            const idA = hostSolid.vertex_ids[ia];
            const idB = hostSolid.vertex_ids[ib];
            if (!va || !vb || !idA || !idB) continue;
            solidEdgePairs.push({
              a: parseFracVec3(va),
              b: parseFracVec3(vb),
              symA: shortSym(byId.get(idA)),
              symB: shortSym(byId.get(idB)),
            });
          }
        }
        const apexPref = [...structuralApexSymsOfScene(exactOrigin), ...preferredPointOrderForPolygon(exactOrigin, hostSolid)];
        const ptSymAt = (pt: ExactVec3): string => {
          const fv = parseFracVec3(pt);
          const match = exactOrigin.objects.find(
            (p) => !isSubEntity(p.id) && p.type === "point3" && p.xyz && vIsZero(vSub(parseFracVec3(p.xyz), fv)),
          );
          return shortSym(match);
        };
        for (let i = 0; i < secPts.length; i += 1) {
          const pa = secPts[i]!;
          const pb = secPts[(i + 1) % secPts.length]!;
          const fpa = parseFracVec3(pa);
          const fpb = parseFracVec3(pb);
          const sa = ptSymAt(pa);
          const sb = ptSymAt(pb);
          if (!sa || !sb) continue;
          const exactEdge = solidEdgePairs.find(
            (se) =>
              (vIsZero(vSub(fpa, se.a)) && vIsZero(vSub(fpb, se.b)))
              || (vIsZero(vSub(fpa, se.b)) && vIsZero(vSub(fpb, se.a))),
          );
          if (exactEdge) {
            const preferFirst = apexPref.indexOf(sa) !== -1 && (apexPref.indexOf(sb) === -1 || apexPref.indexOf(sa) < apexPref.indexOf(sb));
            coincidentSolidEdges.push(preferFirst ? `${sa}${sb}` : `${sb}${sa}`);
            continue;
          }
          let hostFaceLabel: string | null = null;
          for (const f of hostSolid.faces) {
            if (f.length < 3) continue;
            const fp0 = hostSolid.vertices[f[0]!];
            const fp1 = hostSolid.vertices[f[1]!];
            const fp2 = hostSolid.vertices[f[2]!];
            if (!fp0 || !fp1 || !fp2) continue;
            const p0 = parseFracVec3(fp0);
            const cov = vCross(vSub(parseFracVec3(fp1), p0), vSub(parseFracVec3(fp2), p0));
            if (
              !vIsZero(cov)
              && fIsZero(plainDotFrac(vSub(fpa, p0), cov))
              && fIsZero(plainDotFrac(vSub(fpb, p0), cov))
            ) {
              const fSyms = f.map((vi) => shortSym(byId.get(hostSolid!.vertex_ids![vi]!))).filter(Boolean);
              hostFaceLabel = formatCycleNotation(fSyms, apexPref);
              break;
            }
          }
          faceTraceEdges.push(hostFaceLabel ? `${sa}${sb} ⊂ ${hostFaceLabel}` : `${sa}${sb}`);
        }
      }
      if (coincidentSolidEdges.length > 0 && faceTraceEdges.length > 0) {
        conciseRationale = `Mặt phẳng cắt đi qua ${coincidentSolidEdges.length === 1 ? "cạnh" : "các cạnh"} ${coincidentSolidEdges.join(", ")} và cắt theo ${faceTraceEdges.join(", ")}, khép kín thiết diện ${secNotation}.`;
      } else if (faceTraceEdges.length >= 2) {
        conciseRationale = `Nối các đoạn giao tuyến (${faceTraceEdges.slice(0, 4).join(", ")}) để khép kín thiết diện ${secNotation}.`;
      } else {
        conciseRationale = `Nối các đoạn giao tuyến trên từng mặt của khối để khép kín miền thiết diện ${secNotation}.`;
      }
    }

    // The engine supplies the face walk and vertex-edge provenance; do not re-intersect planes in the presenter.
    const details = sectionDetails(exactOrigin, polySectionTarget.id);
    const certifiedSolid = details?.solidId ? byId.get(details.solidId) : undefined;
    const sources = polySectionTarget.vertex_sources ?? [];
    const vertexNames = details?.vertexNames ?? [];
    const named = (i: number) => /^[A-Z][A-Za-z0-9′']*$/u.test(vertexNames[i] ?? "") ? vertexNames[i]! : null;
    const solidSymbol = (i: number) => shortSym(byId.get(certifiedSolid?.vertex_ids?.[i] ?? ""));
    const cutEdges = sources.flatMap((s, i) => {
      if (named(i) || s.kind !== "SOLID_EDGE_INTERSECTION" || s.solid_edge_vertex_indices?.length !== 2) return [];
      const symbols = s.solid_edge_vertex_indices.map(solidSymbol);
      return symbols.every(Boolean) ? [{ ordinal: i, edge: symbols.join("") }] : [];
    });
    const describeVertex = (xyz: ExactVec3): string | null => {
      const i = secPts.findIndex(p => p.join("|") === xyz.join("|"));
      if (i < 0) return null;
      const sym = named(i);
      if (sym) return sym;
      const edge = cutEdges.find(e => e.ordinal === i)?.edge;
      if (edge) return `giao điểm của ${edge} với mặt phẳng cắt`;
      const source = sources[i];
      if (source?.kind === "SOLID_VERTEX" && source.solid_vertex_index != null) {
        const vertex = solidSymbol(source.solid_vertex_index);
        if (vertex) return `đỉnh ${vertex}`;
      }
      return null;
    };
    const certifiedTraces = sources.length === secPts.length ? (polySectionTarget.steps ?? []).flatMap(trace => {
      const face = trace.face_index != null ? certifiedSolid?.faces?.[trace.face_index] : undefined;
      const faceSymbols = face?.map(solidSymbol) ?? [];
      const a = describeVertex(trace.a), b = describeVertex(trace.b);
      if (faceSymbols.length < 3 || !faceSymbols.every(Boolean) || !a || !b) return [];
      return [canonicalizeSceneFaceTokensInText(scene, `Trên mặt (${faceSymbols.join("")}), nối ${a} với ${b}.`)];
    }) : [];
    if (cutEdges.length > 0 && certifiedTraces.length === polySectionTarget.steps?.length) {
      const givenNames = vertexNames.map((_, i) => named(i)).filter(Boolean);
      conciseRationale = `${givenNames.length ? `Ngoài các điểm ${givenNames.join(", ")}, mặt` : "Mặt"} phẳng cắt còn gặp ${cutEdges.length === 1 ? "cạnh" : "các cạnh"} ${cutEdges.map(e => e.edge).join(", ")}. Các giao điểm này cùng các đỉnh đã có tạo thành thiết diện ${topologicalPolygonNoun(secPts.length)}.`;
    }
    const detailedEvidence = filterDistinctEvidence(actionTitle, conciseRationale, [
      canonicalSubtitle,
      ...normalizedJusts,
      ...certifiedTraces,
    ]);

    return {
      actionTitle,
      conciseRationale,
      detailedEvidence,
    };
  }

  if (curvedPolySectionTarget) {
    const basis = deriveExactPolygonMathBasis(exactOrigin, curvedPolySectionTarget);
    const secNotation =
      basis?.cycleNotation
      ?? (() => {
        const m = actionTitle.match(/\([A-Z0-9′']{3,}\)/u);
        return m ? m[0] : curvedPolySectionTarget.notation?.trim() || "đa giác";
      })();
    const secPts = curvedPolySectionTarget.polygon ?? curvedPolySectionTarget.vertices ?? [];
    const ptSymAt = (pt: ExactVec3): string => {
      const fv = parseFracVec3(pt);
      const match = exactOrigin.objects.find(
        (p) => !isSubEntity(p.id) && p.type === "point3" && p.xyz && vIsZero(vSub(parseFracVec3(p.xyz), fv)),
      );
      return shortSym(match);
    };

    let curvedConcise: string | null = null;
    const coneHost = hostCurvedSolids.find(
      (cs) =>
        cs.curved_kind === "cone"
        && Boolean(cs.apex_or_top ?? (cs as { apex?: ExactVec3 }).apex)
        && Boolean(cs.anchor ?? (cs as { base_center?: ExactVec3 }).base_center)
        && Boolean(cs.radius_sq),
    );
    if (coneHost && secPts.length === 3) {
      const apexF = parseFracVec3((coneHost.apex_or_top ?? (coneHost as { apex?: ExactVec3 }).apex)!);
      const centerF = parseFracVec3((coneHost.anchor ?? (coneHost as { base_center?: ExactVec3 }).base_center)!);
      const R2 = parseExactFrac(coneHost.radius_sq!);
      const fVerts = secPts.map((p) => parseFracVec3(p));
      const vSyms = secPts.map((p) => ptSymAt(p));
      const apexIdx = fVerts.findIndex((fv) => vIsZero(vSub(fv, apexF)));
      if (apexIdx >= 0 && vSyms.every(Boolean)) {
        const i1 = (apexIdx + 1) % 3;
        const i2 = (apexIdx + 2) % 3;
        const pA = fVerts[i1]!;
        const pB = fVerts[i2]!;
        const sS = vSyms[apexIdx]!;
        const sA = vSyms[i1]!;
        const sB = vSyms[i2]!;
        const onRimA = fEq(metricDot(vSub(pA, centerF), vSub(pA, centerF), exactOrigin.chart_metric), R2);
        const onRimB = fEq(metricDot(vSub(pB, centerF), vSub(pB, centerF), exactOrigin.chart_metric), R2);
        if (onRimA && onRimB) {
          const passesCenter = vIsZero(vCross(vSub(centerF, pA), vSub(pB, pA)));
          curvedConcise = passesCenter
            ? `Mặt phẳng qua đỉnh ${sS} và trục cắt đáy theo đường kính ${sA}${sB} và hai đường sinh ${sS}${sA}, ${sS}${sB}, khép kín thiết diện ${secNotation}.`
            : `Mặt phẳng qua đỉnh ${sS} cắt đường tròn đáy theo dây cung ${sA}${sB} và hai đường sinh ${sS}${sA}, ${sS}${sB}, khép kín thiết diện ${secNotation}.`;
        }
      }
    }
    const cylHost = !curvedConcise ? hostCurvedSolids.find((cs) => cs.curved_kind === "cylinder") : undefined;
    if (cylHost && secPts.length === 4) {
      curvedConcise = `Mặt phẳng cắt hai đáy hình trụ theo hai dây cung song song và cắt mặt xung quanh theo hai đường sinh, khép kín thiết diện ${secNotation}.`;
    }

    if (curvedConcise) {
      return {
        actionTitle,
        conciseRationale: curvedConcise,
        detailedEvidence: filterDistinctEvidence(actionTitle, curvedConcise, [
          canonicalSubtitle,
          ...normalizedJusts,
        ]),
      };
    }
  }

  // Non-polyhedral-section steps: preserve complete semantic clauses without dumping multi-paragraph provenance or parroting actionTitle
  let conciseRationale = canonicalSubtitle;
  const extraEvidenceCandidates: string[] = [];

  if (!canonicalSubtitle.includes("∥") && !canonicalSubtitle.includes("song song")) {
    for (const tid of step.targetIds) {
      const exTarget = byId.get(tid);
      const scTarget = scene.objects.find((x) => x.id === tid) ?? exTarget;
      if (!exTarget || !scTarget || !isIntersectionLineOrSegment(scTarget, scene)) continue;
      let lp0: FracVec3 | null = null;
      let ldir: FracVec3 | null = null;
      if (exTarget.type === "line3" && exTarget.point && exTarget.direction) {
        lp0 = parseFracVec3(exTarget.point);
        ldir = parseFracVec3(exTarget.direction);
      } else {
        const pa = exTarget.point_a ?? exTarget.endpoints?.[0];
        const pb = exTarget.point_b ?? exTarget.endpoints?.[1];
        if (pa && pb) {
          lp0 = parseFracVec3(pa);
          ldir = vSub(parseFracVec3(pb), lp0);
        }
      }
      if (!lp0 || !ldir || vIsZero(ldir)) continue;
      const parNames: string[] = [];
      const seenPar = new Set<string>();
      for (const sObj of hostSolids) {
        const vIds = sObj.vertex_ids ?? [];
        const verts = sObj.vertices ?? [];
        for (const f of sObj.faces ?? []) {
          for (let i = 0; i < f.length; i += 1) {
            if (parNames.length >= 2) break;
            const ia = f[i]!;
            const ib = f[(i + 1) % f.length]!;
            const idA = vIds[ia];
            const idB = vIds[ib];
            const va = verts[ia];
            const vb = verts[ib];
            if (!idA || !idB || !va || !vb) continue;
            if (!presentIdsAtAnchor.has(idA) && !presentIdsAtAnchor.has(sObj.id)) continue;
            const fva = parseFracVec3(va);
            const ev = vSub(parseFracVec3(vb), fva);
            if (vIsZero(ev) || !vParallel(ldir, ev)) continue;
            if (vIsZero(vCross(vSub(fva, lp0), ldir))) continue;
            const sa = shortSym(byId.get(idA));
            const sb = shortSym(byId.get(idB));
            if (!sa || !sb) continue;
            const edgeKey = idA < idB ? `${idA}|${idB}` : `${idB}|${idA}`;
            if (seenPar.has(edgeKey)) continue;
            seenPar.add(edgeKey);
            parNames.push(`${sa}${sb}`);
          }
          if (parNames.length >= 2) break;
        }
        if (parNames.length >= 2) break;
      }
      if (parNames.length > 0) {
        const interSym = shortSym(exTarget) || "giao tuyến";
        if (canonicalSubtitle && !isGenericStepBoilerplate(canonicalSubtitle)) {
          extraEvidenceCandidates.push(canonicalSubtitle);
        }
        conciseRationale = `Giao tuyến ${interSym} song song với ${parNames.join(", ")} theo tính chất giao tuyến của các mặt phẳng chứa đường thẳng song song.`;
        break;
      }
    }
  }

  const semicolonClauses = conciseRationale.split(/\s*;\s*/u).map((c) => c.trim()).filter(Boolean);
  if (semicolonClauses.length >= 3) {
    extraEvidenceCandidates.push(conciseRationale);
    if (isSameActionClause(semicolonClauses[0]!, actionTitle)) {
      const rem = `${semicolonClauses[1]}; ${semicolonClauses[2]}`.replace(/^(?:vì|do)\s+/iu, "");
      conciseRationale = rem.charAt(0).toUpperCase() + rem.slice(1);
    } else {
      conciseRationale = `${semicolonClauses[0]}; ${semicolonClauses[1]}`;
    }
  } else if (
    semicolonClauses.length === 2
    && isSameActionClause(semicolonClauses[0]!, actionTitle)
  ) {
    const rem = semicolonClauses[1]!.replace(/^(?:vì|do)\s+/iu, "");
    conciseRationale = rem.charAt(0).toUpperCase() + rem.slice(1);
  } else if (actionTitle.trim().length > 0) {
    const trimmedTitle = actionTitle.trim().replace(/\.+$/u, "");
    const mConnSplit = conciseRationale.match(/^(.+?)\s+(để|nhằm|vì|do)\s+(.+)$/iu);
    if (conciseRationale.toLowerCase().startsWith(trimmedTitle.toLowerCase())) {
      const tail = conciseRationale.slice(trimmedTitle.length).trim();
      const mConn = tail.match(/^(để|nhằm|vì|do)\s+(.+)$/iu);
      if (mConn) {
        const conn = mConn[1]!.toLowerCase();
        const body = mConn[2]!.trim();
        conciseRationale =
          conn === "để" || conn === "nhằm"
            ? `Nhằm ${body}`
            : `${mConn[1]!.charAt(0).toUpperCase()}${mConn[1]!.slice(1)} ${body}`;
      }
    } else if (mConnSplit && isSameActionClause(mConnSplit[1]!, trimmedTitle)) {
      const conn = mConnSplit[2]!.toLowerCase();
      const body = mConnSplit[3]!.trim();
      conciseRationale =
        conn === "để" || conn === "nhằm"
          ? `Nhằm ${body}`
          : `${mConnSplit[2]!.charAt(0).toUpperCase()}${mConnSplit[2]!.slice(1)} ${body}`;
    }
  }

  const detailedEvidence = filterDistinctEvidence(actionTitle, conciseRationale, [
    ...extraEvidenceCandidates,
    ...normalizedJusts,
  ]);

  return {
    actionTitle,
    conciseRationale,
    detailedEvidence,
  };
}

export type VisualContinuityDimension = "geometric" | "semantic" | "visual" | "pedagogical";

export type VisualContinuityViolationCode =
  | "GEOMETRIC_CONTINUITY_FAILURE"
  | "INTERNAL_RESULT_EXPOSED"
  | "REFERENCE_PROMOTED_TO_RESULT"
  | "UNVERIFIED_WITNESS_SYMBOL_SHOWN"
  | "REPRESENTATION_DRIFT_ACROSS_STEPS"
  | "HIDDEN_ACTIVE_PREREQUISITE"
  | "OBSOLETE_AUXILIARY_WITNESS_ACTIVE"
  | "DUPLICATE_CANVAS_DIMENSION"
  | "NON_DETERMINISTIC_STEP_SCRUB"
  | "CONCISE_RATIONALE_OVERFLOW"
  | "SUMMARY_DROPPED_KEY_RELATION"
  | "SPOILER_LEAK_IN_NARRATION"
  | "DISAPPEARING_AUXILIARY_CONSTRUCTION_LINE";

export interface VisualContinuityViolation {
  dimension: VisualContinuityDimension;
  code: VisualContinuityViolationCode;
  stepIndex: number | null;
  objectId: string | null;
  detail: string;
}

export interface VisualContinuityReport {
  valid: boolean;
  stepCount: number;
  dimensions: Record<VisualContinuityDimension, boolean>;
  violations: VisualContinuityViolation[];
}

/**
 * Kiểm chứng tính liên tục 4 chiều (`geometric`, `semantic`, `visual`, `pedagogical`) xuyên suốt chuỗi bước (§7):
 * kết hợp `verifyConstructionContinuity` với bất biến hiển thị theo ngữ cảnh bước, độ ổn định vai trò biểu diễn,
 * thu hồi đường phụ/ký hiệu hết vai trò, chống trùng nhãn số đo, chống tràn thẻ "Được suy ra" và tính tất định khi tiến/lùi/nhảy bước.
 */
export function verifyVisualContinuity(scene: Scene3D): VisualContinuityReport {
  const violations: VisualContinuityViolation[] = [];
  const geoReport = verifyConstructionContinuity(scene);
  for (const gv of geoReport.violations) {
    violations.push({
      dimension: gv.code === "UNVERIFIED_OR_PREMATURE_WITNESS" ? "semantic" : "geometric",
      code:
        gv.code === "UNVERIFIED_OR_PREMATURE_WITNESS"
          ? "UNVERIFIED_WITNESS_SYMBOL_SHOWN"
          : "GEOMETRIC_CONTINUITY_FAILURE",
      stepIndex: null,
      objectId: gv.objectId,
      detail: `[${gv.code}] ${gv.detail}`,
    });
  }

  const contract = getSemanticConstructionContract(scene);
  const steps = scene.events.length > 0 ? pedagogicalStepList(scene) : [];
  const auxMap = auxiliaryObjects(scene);
  const byId = new Map(scene.objects.map((o) => [o.id, o]));
  const seenBaseRoleByObj = new Map<string, SemanticRoleId>();

  const snapshotAtStep = (st: PedagogicalStepItem): string => {
    const roles = resolveStepVisualRoles(scene, st.anchor, { auxiliaryShown: false, selectedId: null });
    const roleSig = [...roles.entries()]
      .map(
        ([id, r]) =>
          `${id}:${r.role}:${r.visible}:${r.opacityScale}:${Boolean(r.showPerpWitnessSymbol)}:${r.perpWitnessOpacityScale ?? 1}:${Boolean(r.showParallelWitnessSymbol)}:${r.planeLifecycleStage ?? ""}:${Boolean(r.showObjectLabel)}`,
      )
      .join(",");
    const anns = annotationsAt(scene, st.anchor, DEFAULT_ANNOTATION_VIEW, null)
      .map((a) => `${a.id}:${a.text}`)
      .join(",");
    const nar = buildPedagogicalStepNarration(scene, st);
    return `${roleSig}||${anns}||${nar.actionTitle}||${nar.conciseRationale}||${nar.detailedEvidence.length}`;
  };

  const forwardSnaps: string[] = [];

  for (let s = 0; s < steps.length; s += 1) {
    const st = steps[s]!;
    const k = st.anchor;
    forwardSnaps.push(snapshotAtStep(st));
    const roles = resolveStepVisualRoles(scene, k, { auxiliaryShown: false, selectedId: null });

    // 1. Semantic & Visual checks per object at step s
    for (const [id, entry] of roles.entries()) {
      const obj = byId.get(id);
      if (!obj || isSubEntity(id)) continue;
      const spec = contract.objectsById.get(id);

      if (spec?.objectLayer === "INTERNAL_MATH_RESULT" && entry.visible) {
        violations.push({
          dimension: "semantic",
          code: "INTERNAL_RESULT_EXPOSED",
          stepIndex: s,
          objectId: id,
          detail: `Internal math result '${id}' is visible at step ${s}`,
        });
      }

      if (spec?.objectLayer === "REFERENCE_GEOMETRY" && entry.visible && entry.role === "PRIMARY") {
        violations.push({
          dimension: "semantic",
          code: "REFERENCE_PROMOTED_TO_RESULT",
          stepIndex: s,
          objectId: id,
          detail: `Reference geometry '${id}' promoted to PRIMARY at step ${s}`,
        });
      }

      if (entry.visible) {
        const sem = classifySceneObjectSemantics(scene, obj, k);
        const prevSemRole = seenBaseRoleByObj.get(id);
        if (prevSemRole === undefined) {
          seenBaseRoleByObj.set(id, sem.role);
        } else if (prevSemRole !== sem.role) {
          violations.push({
            dimension: "visual",
            code: "REPRESENTATION_DRIFT_ACROSS_STEPS",
            stepIndex: s,
            objectId: id,
            detail: `Object '${id}' switched base semantic rendering role from '${prevSemRole}' to '${sem.role}' at step ${s}`,
          });
        }
      }

      const auxEntry = auxMap.get(id);
      if (auxEntry?.loai === "dung" && k > auxEntry.xongTai) {
        const auxObj = byId.get(id);
        const isPersistentAuxLine =
          Boolean(auxObj && (auxObj.type === "segment3" || auxObj.type === "line3"))
          && !(auxObj!.endpoint_ids ?? auxObj!.depends ?? []).some((epId) => {
            const epObj = byId.get(epId);
            return Boolean(epObj?.type === "point3" && laDiemPhuDungMatPhang(scene, epObj, byId));
          });
        if (isPersistentAuxLine) {
          if (!entry.visible && entry.presentationTier !== "COMPLETED_AUXILIARY") {
            violations.push({
              dimension: "visual",
              code: "DISAPPEARING_AUXILIARY_CONSTRUCTION_LINE",
              stepIndex: s,
              objectId: id,
              detail: `Auxiliary construction line '${id}' disappeared without COMPLETED_AUXILIARY retirement after anchor ${auxEntry.xongTai} at anchor ${k}`,
            });
          } else if (entry.visible && (entry.role === "PRIMARY" || entry.opacityScale > 0.45)) {
            violations.push({
              dimension: "visual",
              code: "OBSOLETE_AUXILIARY_WITNESS_ACTIVE",
              stepIndex: s,
              objectId: id,
              detail: `Auxiliary construction line '${id}' remained unattenuated (role=${entry.role}, opacity=${entry.opacityScale}) at anchor ${k}`,
            });
          }
        } else if (entry.visible) {
          violations.push({
            dimension: "visual",
            code: "OBSOLETE_AUXILIARY_WITNESS_ACTIVE",
            stepIndex: s,
            objectId: id,
            detail: `Transient construction auxiliary '${id}' (finished at ${auxEntry.xongTai}) remained visible at anchor ${k}`,
          });
        }
      }
    }

    // 2. Active target direct point prerequisites must remain visible when target is born
    for (const tId of st.targetIds) {
      const tObj = byId.get(tId);
      const tRole = roles.get(tId);
      if (!tObj || !tRole?.visible) continue;
      const directPointPrereqIds =
        tObj.type === "segment3"
          ? (tObj.endpoint_ids ?? [])
          : tObj.type === "line3" || tObj.type === "polygon3" || tObj.type === "circle3"
            ? (tObj.vertex_ids?.length ? tObj.vertex_ids : (tObj.depends ?? []))
            : [];
      for (const epId of directPointPrereqIds) {
        const epObj = byId.get(epId);
        const epRole = roles.get(epId);
        if (
          epObj?.type === "point3"
          && !isSubEntity(epObj.id)
          && !laDiemPhuDungMatPhang(scene, epObj, byId)
          && (!epRole || !epRole.visible)
        ) {
          violations.push({
            dimension: "visual",
            code: "HIDDEN_ACTIVE_PREREQUISITE",
            stepIndex: s,
            objectId: epId,
            detail: `Direct point prerequisite '${epId}' of active target '${tId}' is hidden at step ${s}`,
          });
        }
      }
    }

    // 3. Canvas dimension deduplication & non-spoiler annotation check
    const anns = annotationsAt(scene, k, DEFAULT_ANNOTATION_VIEW, null);
    const seenSegKeys = new Set<string>();
    for (const ann of anns) {
      if (ann.role !== "given") {
        violations.push({
          dimension: "pedagogical",
          code: "SPOILER_LEAK_IN_NARRATION",
          stepIndex: s,
          objectId: ann.id,
          detail: `Non-given annotation '${ann.text}' (${ann.role}) shown by default at step ${s}`,
        });
      }
      if (ann.anchor === "segment" && ann.subject_ids.length === 2) {
        const [u, v] = ann.subject_ids;
        const segKey = u < v ? `${u}|${v}` : `${v}|${u}`;
        if (seenSegKeys.has(segKey)) {
          violations.push({
            dimension: "visual",
            code: "DUPLICATE_CANVAS_DIMENSION",
            stepIndex: s,
            objectId: ann.id,
            detail: `Duplicate canvas segment dimension on '${segKey}' at step ${s}`,
          });
        }
        seenSegKeys.add(segKey);
      }
    }

    // 4. Pedagogical narration conciseness, non-spoiler & lossless relation preservation
    const nar = buildPedagogicalStepNarration(scene, st);
    if (!learnerTextIsSafe(scene, nar.actionTitle) || !learnerTextIsSafe(scene, nar.conciseRationale)) {
      violations.push({
        dimension: "pedagogical",
        code: "SPOILER_LEAK_IN_NARRATION",
        stepIndex: s,
        objectId: null,
        detail: `Step ${s} narration leaked answer text`,
      });
    }
    const presentAtStepSet = new Set(objectsAt(scene, k).map((o) => o.id));
    const presentPointSyms = new Set(
      scene.objects
        .filter((o) => presentAtStepSet.has(o.id) && o.type === "point3" && !isSubEntity(o.id))
        .map((o) => shortSym(o))
        .filter(Boolean),
    );
    const cycleTokensInNarration = [
      ...(nar.actionTitle.match(/\([A-Z0-9′']{3,}\)/gu) ?? []),
      ...(nar.conciseRationale.match(/\([A-Z0-9′']{3,}\)/gu) ?? []),
    ].flatMap((tok) => tok.slice(1, -1).match(/[A-Z][0-9′']*/gu) ?? []);
    for (const futObj of scene.objects) {
      if (presentAtStepSet.has(futObj.id) || futObj.type !== "point3" || isSubEntity(futObj.id)) continue;
      const fSym = shortSym(futObj);
      if (!fSym || presentPointSyms.has(fSym)) continue;
      if (cycleTokensInNarration.includes(fSym)) {
        violations.push({
          dimension: "pedagogical",
          code: "SPOILER_LEAK_IN_NARRATION",
          stepIndex: s,
          objectId: futObj.id,
          detail: `Step ${s} narration referenced future unconstructed vertex '${fSym}' inside polygon token`,
        });
      }
    }
    const semiCount = nar.conciseRationale.split(/\s*;\s*/u).filter(Boolean).length;
    if (semiCount >= 3 || /\bGiao tuyến trên từng mặt:/u.test(nar.conciseRationale)) {
      violations.push({
        dimension: "pedagogical",
        code: "CONCISE_RATIONALE_OVERFLOW",
        stepIndex: s,
        objectId: null,
        detail: `Step ${s} conciseRationale contains uncondensed multi-face derivation: '${nar.conciseRationale}'`,
      });
    }
    if (st.subtitle.includes("∥")) {
      const combined = [nar.conciseRationale, ...nar.detailedEvidence].join(" ");
      if (!combined.includes("∥") && !combined.includes("song song")) {
        violations.push({
          dimension: "pedagogical",
          code: "SUMMARY_DROPPED_KEY_RELATION",
          stepIndex: s,
          objectId: null,
          detail: `Step ${s} narration lost verified parallel relation from subtitle`,
        });
      }
    }
  }

  // 5. Backward & interleaved random-order scrubbing determinism
  for (let s = steps.length - 1; s >= 0; s -= 1) {
    if (snapshotAtStep(steps[s]!) !== forwardSnaps[s]) {
      violations.push({
        dimension: "visual",
        code: "NON_DETERMINISTIC_STEP_SCRUB",
        stepIndex: s,
        objectId: null,
        detail: `Backward scrub mismatch at step ${s}`,
      });
    }
  }
  const randomOrder = [
    ...steps.map((_, i) => i).filter((i) => i % 2 === 0),
    ...steps.map((_, i) => i).filter((i) => i % 2 === 1).reverse(),
  ];
  for (const idx of randomOrder) {
    if (snapshotAtStep(steps[idx]!) !== forwardSnaps[idx]) {
      violations.push({
        dimension: "visual",
        code: "NON_DETERMINISTIC_STEP_SCRUB",
        stepIndex: idx,
        objectId: null,
        detail: `Random-order scrub mismatch at step ${idx}`,
      });
    }
  }

  const dimensions: Record<VisualContinuityDimension, boolean> = {
    geometric: !violations.some((v) => v.dimension === "geometric"),
    semantic: !violations.some((v) => v.dimension === "semantic"),
    visual: !violations.some((v) => v.dimension === "visual"),
    pedagogical: !violations.some((v) => v.dimension === "pedagogical"),
  };

  return {
    valid: violations.length === 0,
    stepCount: steps.length,
    dimensions,
    violations,
  };
}

export function normalizeCylinderEnvelopeTitle(
  rawTitle: string | null | undefined,
  scene?: Scene3D | null,
): string {
  const title = rawTitle ?? "";
  if (scene && /hình\s+trụ\s+(?:có\s+)?trục\s+xiên|hình\s+trụ\s+xiên/iu.test(title)) {
    const cyl = scene.objects?.find((o) => o.type === "curved_solid" && o.curved_kind === "cylinder");
    if (cyl) {
      const ortho = inspectAxialCurvedOrthogonality(scene, cyl);
      if (ortho.isRightCertified && !ortho.isOblique) {
        return "Hình trụ tròn xoay có trục đặt nghiêng";
      }
    }
  }
  return title;
}
