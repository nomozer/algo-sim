/**
 * BẢNG MÀU VAI TRÒ — mỗi màu MỘT nghĩa, trên canvas và ở bảng lời giải (W12).
 *
 * ─── VÌ SAO TÁCH THÀNH MỘT MODULE ────────────────────────────────────────
 *
 * Review người (W12, NEEDS_CHANGES): cam đậm mang HAI nghĩa — "dữ kiện số"
 * trong hàng số đo và "vật đang chọn" trên canvas; còn xanh vừa là điểm đề
 * cho, vừa là đích của causal ở hàng số. Hai bảng màu viết tay ở hai chỗ là
 * cách chắc chắn để chúng trôi khỏi nhau, nên cả renderer lẫn CSS đọc về đây
 * (CSS giữ bản sao `--geo3d-vai-tro-*`, khoá bằng test đồng bộ).
 *
 *   xanh        thứ ĐANG XÉT — vật được chọn, hoặc vật vừa dựng khi phát
 *   cam đậm     dữ kiện SỐ đề cho
 *   cam nhạt    đại lượng TRUNG GIAN suy ra
 *   xám         ngữ cảnh cấu trúc/tô-pô của chuỗi nhân quả
 *   mờ          ngoài chuỗi (độ trong, không phải một màu)
 *
 * Điểm đề cho không còn xanh (quyết định W12): xanh chỉ còn nghĩa "đang xét".
 */
import type { Scene3D, SceneObject } from "./scene3d-model";

export const MAU_VAI_TRO = {
  /** Đích causal — vật người học chọn (canvas lẫn bảng). */
  dich: 0x0075de,
  /** Vật vừa dựng ở bước đang phát: cũng là thứ đang xét. */
  moi_dung: 0x0075de,
  /** Dữ kiện số đề cho trong chuỗi nhân quả. */
  du_kien_so: 0xc2410c,
  /** Đại lượng trung gian suy ra trong chuỗi nhân quả. */
  trung_gian: 0xfb923c,
  /** Nét của ngữ cảnh cấu trúc/tô-pô — trung tính. */
  boi_canh: 0x6b7280,
  /** Nền (mặt, khối) của ngữ cảnh cấu trúc — trung tính lạnh nhạt (xanh xám sách giáo khoa). */
  nen_boi_canh: 0xcfd6df,
  /** Chấm điểm đề cho khi không có vai trò nào — trung tính đậm. */
  diem_de_cho: 0x31302e,
} as const;

/** Tên biến CSS mang cùng giá trị — bảng lời giải và chú giải đọc chúng. */
export const BIEN_CSS_VAI_TRO = {
  dich: "--geo3d-vai-tro-dich",
  du_kien_so: "--geo3d-vai-tro-du-kien-so",
  trung_gian: "--geo3d-vai-tro-trung-gian",
  boi_canh: "--geo3d-vai-tro-boi-canh",
} as const satisfies Partial<Record<keyof typeof MAU_VAI_TRO, string>>;

/** Số sRGB hex → CSS, để khoá bảng lời giải cùng màu với canvas. */
export function hexCss(mau: number): string {
  return `#${mau.toString(16).padStart(6, "0")}`;
}

export interface PhongCachScene3D {
  colors: Record<"free" | "derived" | "line" | "surface" | "planeOutline" | "mesh" | "secondaryMesh" |
    "canh" | "hiddenEdge" | "polygon" | "sectionOutline" | "grid" | "gridOuter" | "light", number>;
  opacity: Record<"solid" | "secondarySolid" | "selectedSolid" | "base" | "selectedBase" | "section" |
    "selectedSection" | "face" | "selectedFace" | "plane" | "standalonePlane" | "selectedPlane" | "planeCore" |
    "selectedPlaneCore" | "hiddenEdge" | "hiddenRim" | "planeEdge" | "standalonePlaneEdge" | "selectedPlaneEdge" |
    "hiddenPlaneEdge" | "selectedHiddenPlaneEdge" | "fade" | "auxiliary" | "witness" | "foot" |
    "sphereEquator" | "sphereMeridian" | "gridInner" | "gridMiddle" | "gridOuter" | "shellBackRatio", number>;
  width: Record<"edge" | "selected" | "border" | "plane" | "perpendicular" | "pick", number>;
  /** Screen-space (Line2) stroke widths in CSS px at `referenceCanvasHeight`; scaled by canvas height within
   *  [minScale, maxScale] so stroke/figure ratio stays close to the world-space strokes of the reference HTML. */
  fatPx: Record<"edge" | "hiddenEdge" | "selectedEdge" | "section" | "hiddenSection" | "selectedSection" |
    "plane" | "selectedPlane" | "perpendicular" | "hiddenPerpendicular" | "referenceCanvasHeight" | "minScale" |
    "maxScale", number>;
  /** Right-angle marker leg in CSS px (per canvas height, clamped), and its cap as a fraction of the shorter leg. */
  rightAngle: { perCanvasHeight: number; minPx: number; maxPx: number; maxLegRatio: number };
  dash: { relative: number; fallback: number; gapRatio: number; witnessGapRatio: number };
  light: { ambient: number; directional: number; roughness: number; metalness: number };
}

/** SGK_REFERENCE — Scene3D port of the owner's reference `matphanghinhchot.html` (PALETTE, addPolyhedronShell,
 * addPolygonSection, addCuttingPlanePatch, addRightAngleMarker). Every region is unlit (MeshBasicMaterial, as in the
 * reference); shells draw a back pass at `shellBackRatio` × opacity then a front pass. Depth/occlusion passes and the
 * edge-visibility classifier are AlgoSim's own, not the reference's face-normal heuristic. */
export const PHONG_CACH_SCENE3D = {
  colors: {
    free: MAU_VAI_TRO.diem_de_cho, derived: 0xc85a32, line: 0x0f766e, surface: 0x6d28d9, planeOutline: 0x6d28d9,
    mesh: 0x7c8b9e, secondaryMesh: 0x3d7a8a, canh: 0x1e293b, hiddenEdge: 0x64748b,
    polygon: 0xc85a32, sectionOutline: 0xc85a32, grid: 0xa39e98, gridOuter: 0xe6e6e6, light: 0xffffff,
  },
  opacity: {
    solid: 0.12, secondarySolid: 0.10, selectedSolid: 0.20, base: 0.09, selectedBase: 0.16,
    // Section fill: reference 0.27 measures ΔE76 ≈ 17 < 20 on SECTION_FILL_DISTINGUISHABLE (the reference HTML itself
    // too — same shell + plane layering). Owner decision 2026-10-24: smallest passing value 0.32 (ΔE ≈ 20.5).
    section: 0.32, selectedSection: 0.38, face: 0.10, selectedFace: 0.18,
    plane: 0.065, standalonePlane: 0.085, selectedPlane: 0.16, planeCore: 0.065, selectedPlaneCore: 0.16,
    hiddenEdge: 0.78, hiddenRim: 0.65, planeEdge: 0.55, standalonePlaneEdge: 0.55, selectedPlaneEdge: 0.75,
    hiddenPlaneEdge: 0, selectedHiddenPlaneEdge: 0.28, fade: 0.72, auxiliary: 0.42,
    witness: 0.95, foot: 0.95, sphereEquator: 0.09, sphereMeridian: 0.035,
    gridInner: 0.16, gridMiddle: 0.10, gridOuter: 0.04, shellBackRatio: 0.75,
  },
  width: { edge: 1.75, selected: 2.8, border: 2.4, plane: 1.15, perpendicular: 1.4, pick: 6 },
  // Reference cylinder radii 0.028 / 0.028·0.84 / 0.035 / 0.021 / 0.017 ⇒ ratios 1 : 0.84 : 1.25 : 0.75 : 0.61.
  // Edge 3.6 px @720 ⇒ ≈0.008 × figure height, the stroke/figure ratio measured on the reference screenshots.
  fatPx: {
    edge: 3.6, hiddenEdge: 3, selectedEdge: 4.6, section: 4.5, hiddenSection: 3.7, selectedSection: 5.2,
    plane: 2.2, selectedPlane: 3, perpendicular: 2.7, hiddenPerpendicular: 2.4,
    referenceCanvasHeight: 720, minScale: 0.62, maxScale: 1.25,
  },
  // Owner 2026-10-26: 8–12 px was too small to read (≈ 5–8 px once foreshortened); 12–18 px, still screen-sized.
  // Claude resume: at 390 px a 12 px mark at a named vertex was mostly under the vertex dot ⇒ 16–22 px.
  rightAngle: { perCanvasHeight: 0.026, minPx: 16, maxPx: 22, maxLegRatio: 0.3 },
  // Reference dash 0.17 / gap 0.12 on a ~4.5-unit figure ⇒ dash ≈ 2 × the previous relative cycle; gap ratio 0.71.
  dash: { relative: 0.044, fallback: 0.16, gapRatio: 0.72, witnessGapRatio: 0.65 },
  light: { ambient: 1.45, directional: 0.28, roughness: 0.90, metalness: 0 },
} satisfies PhongCachScene3D;

export type VaiTroKhoi = "primary" | "secondary";

/** Assign once from the COMPLETE scene. Visibility, isolation and array order cannot change a solid's role.
 * First constructed solid is primary; all others secondary. Labels/tree/topology also identify each solid. */
export function vaiTroKhoi(scene: Pick<Scene3D, "objects" | "events">): Map<string, VaiTroKhoi> {
  const thuTu = new Map<string, number>();
  for (const event of scene.events) {
    if (event.action !== "CREATE" && event.action !== "INIT") continue;
    for (const id of [event.object, ...(event.objects ?? [])]) {
      if (id && !thuTu.has(id)) thuTu.set(id, event.step_index);
    }
  }
  const solids = scene.objects.filter(o => o.type === "solid" || o.type === "curved_solid")
    .sort((a, b) => (thuTu.get(a.id) ?? Infinity) - (thuTu.get(b.id) ?? Infinity) || a.id.localeCompare(b.id));
  return new Map(solids.map((o, i) => [o.id, i === 0 ? "primary" : "secondary"]));
}

/** Existing surface/formation metadata, not scene ids, determines the visual role across every mesh technique.
 * Base metadata wins; otherwise every region type falls back to section alike — the backend tags each non-base
 * polygon3 AUXILIARY_SURFACE, and pre-metadata envelopes must not change color by mesh technique. */
export function vaiTroMien(o: SceneObject): "base" | "section" | "auxiliary" {
  if (o.surface_role === "BASE_REGION" || (o.formation_roles ?? []).includes("CONSTRUCT_BASE")) return "base";
  if (o.type === "section" || o.type === "polygon3" || o.type === "circle3" || o.type === "ellipse3" || o.surface_role === "SECTION_REGION" || o.surface_role === "AUXILIARY_SURFACE") return "section";
  return "auxiliary";
}
