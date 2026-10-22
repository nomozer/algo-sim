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
    "selectedSection" | "face" | "selectedFace" | "plane" | "selectedPlane" | "planeCore" |
    "selectedPlaneCore" | "hiddenEdge" | "hiddenRim" | "planeEdge" | "selectedPlaneEdge" |
    "hiddenPlaneEdge" | "selectedHiddenPlaneEdge" | "fade" | "auxiliary" | "witness" | "foot" |
    "sphereEquator" | "sphereMeridian" | "gridInner" | "gridMiddle" | "gridOuter", number>;
  width: Record<"edge" | "selected" | "border" | "plane" | "perpendicular" | "pick", number>;
  dash: { relative: number; fallback: number; gapRatio: number; witnessGapRatio: number };
  light: { ambient: number; directional: number; roughness: number; metalness: number };
}

/** Scene3D extension of DESIGN.md, survey B. All colors are sRGB hex, never unresolved CSS variables.
 * Flat semantic regions are unlit; shells retain lighting and the existing depth/occlusion passes. */
export const PHONG_CACH_SCENE3D = {
  colors: {
    free: MAU_VAI_TRO.diem_de_cho, derived: 0x391c57, line: 0x197773, surface: 0xd6b6f6, planeOutline: 0x391c57,
    mesh: 0x62aef0, secondaryMesh: 0x2a9d99, canh: 0x31302e, hiddenEdge: 0x716d69,
    polygon: 0xffc857, sectionOutline: 0xdd5b00, grid: 0xa39e98, gridOuter: 0xe6e6e6, light: 0xffffff,
  },
  opacity: {
    solid: 0.18, secondarySolid: 0.16, selectedSolid: 0.30, base: 0.10, selectedBase: 0.20,
    section: 0.38, selectedSection: 0.48, face: 0.12, selectedFace: 0.24,
    plane: 0.055, selectedPlane: 0.16, planeCore: 0.11, selectedPlaneCore: 0.22,
    hiddenEdge: 0.58, hiddenRim: 0.50, planeEdge: 0.32, selectedPlaneEdge: 0.48,
    hiddenPlaneEdge: 0.20, selectedHiddenPlaneEdge: 0.30, fade: 0.30, auxiliary: 0.45,
    witness: 0.92, foot: 0.96, sphereEquator: 0.18, sphereMeridian: 0.13,
    gridInner: 0.24, gridMiddle: 0.14, gridOuter: 0.06,
  },
  width: { edge: 1, selected: 3, border: 2, plane: 1, perpendicular: 1.5, pick: 6 },
  dash: { relative: 0.022, fallback: 0.16, gapRatio: 0.75, witnessGapRatio: 0.65 },
  light: { ambient: 0.75, directional: 0.6, roughness: 0.9, metalness: 0 },
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
