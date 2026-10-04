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
import type { QuantityAnnotation, Scene3D, SceneObject, Vec3 } from "./scene3d-model";
import { clampStep, numericalBasis, objectsAt, toVec3 } from "./scene3d-model";
import { tangNhanManh } from "./interaction-state";

export interface AnnotationView {
  /** "Hiện tất cả": mọi nhãn khả dụng ở bước đang xem, không chỉ dữ kiện và vật đang chọn. */
  showAll: boolean;
}

/** §16.5 (thay U-W17-1): mặc định gọn — tên điểm và dữ kiện đề cho. */
export const DEFAULT_ANNOTATION_VIEW: AnnotationView = Object.freeze({ showAll: false });

export interface AnnotationEntry {
  id: string;
  kind: QuantityAnnotation["kind"];
  category: QuantityAnnotation["category"];
  role: NonNullable<QuantityAnnotation["role"]>;
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

/** Vai trò của nhãn; envelope v109 chưa có `role` ⇒ suy từ `category` và `origin` (vật tự do = đề cho). */
function vaiTro(o: SceneObject, a: QuantityAnnotation): AnnotationEntry["role"] {
  return a.role ?? (a.category === "result" ? "result" : o.origin === "free" ? "given" : "intermediate");
}

/** Có nhãn nào mặc định đang ẩn không — công tắc "Hiện tất cả" vắng khi không có gì để hiện thêm (§3.2). */
export function hasHiddenByDefault(scene: Scene3D): boolean {
  return scene.objects.some((o) => o.type === "quantity" && o.annotation && !o.annotation.same_as
    && vaiTro(o, o.annotation) !== "given");
}

/**
 * Nhãn số đo của bước `step`.
 *
 * Khả dụng = cùng luật lớp lời giải: đáp số (`result`) chỉ từ sự kiện KẾT LUẬN của nó; số đo từ
 * sự kiện tính của nó; dữ kiện đề cho khi nó đã có mặt. Ở các bước dựng người học tới được (neo
 * của bước) luật này trùng `solutionAt`; giữa hai neo nó chặt hơn — không bao giờ lộ trước, ở MỌI
 * chế độ. Chủ thể phải đang có mặt trên hình. Đại lượng `same_as` không có nhãn riêng: chọn nó là
 * chọn nhãn nó trỏ tới.
 */
export function annotationsAt(
  scene: Scene3D,
  step: number,
  view: AnnotationView,
  selectedId: string | null,
): AnnotationEntry[] {
  const k = clampStep(scene, step);
  const coMat = new Set(objectsAt(scene, k).map((o) => o.id));
  const daTinh = new Set<string>();
  const ketLuan = new Set<string>();
  for (const e of scene.events) {
    if (e.step_index > k || !e.object) continue;
    if (e.semantic_kind === "FINAL_RESULT") ketLuan.add(e.object);
    if (e.semantic_kind === "MEASUREMENT" || e.semantic_kind === "FINAL_RESULT") daTinh.add(e.object);
  }
  const theoId = new Map(scene.objects.map((o) => [o.id, o]));
  const chon = selectedId ? theoId.get(selectedId)?.annotation?.same_as ?? selectedId : null;
  const chuoi = chon && theoId.get(chon)?.type === "quantity" ? tangNhanManh(scene, chon) : null;
  const tieuDiem = (o: SceneObject, a: QuantityAnnotation) => chon !== null && (chuoi
    ? o.id === chon || ["du_kien_so", "trung_gian"].includes(chuoi.get(o.id) ?? "")
    : a.subject_ids.includes(chon));
  const ra: AnnotationEntry[] = [];
  for (const o of scene.objects) {
    const a = o.annotation;
    if (!a || a.same_as || o.type !== "quantity" || o.value == null) continue;
    const vai = vaiTro(o, a);
    const khaDung = vai === "result" ? ketLuan.has(o.id) : daTinh.has(o.id) || (o.origin === "free" && coMat.has(o.id));
    if (!khaDung || !a.subject_ids.every((s) => coMat.has(s))) continue;
    const lienQuan = tieuDiem(o, a);
    if (!(view.showAll || vai === "given" || lienQuan)) continue;
    ra.push({
      id: o.id, kind: a.kind, category: a.category, role: vai, subject_ids: [...a.subject_ids], anchor: a.anchor,
      witness: a.witness,
      text: `${o.notation ?? o.label} = ${o.value}${a.unit ? ` ${a.unit}` : ""}`,
      priority: (vai === "result" ? 2 : 1) + (lienQuan ? 10 : 0),
      related: lienQuan,
    });
  }
  return ra;
}

export interface WitnessShown { id: string; from: Vec3; foot: Vec3; u: Vec3; v: Vec3 }

/** §16.7 — nhân chứng của các nhãn khoảng cách ĐANG HIỆN; toạ độ đều do backend phát (chân chính xác). */
export function witnessesShown(scene: Scene3D, entries: AnnotationEntry[]): WitnessShown[] {
  const theoId = new Map(scene.objects.map((o) => [o.id, o]));
  return entries.flatMap((e) => {
    const w = e.anchor === "witness" ? e.witness : undefined;
    const tu = w ? theoId.get(w.from)?.xyz : undefined;
    return w && tu ? [{ id: e.id, from: toVec3(tu), foot: toVec3(w.foot), u: toVec3(w.marker.u), v: toVec3(w.marker.v) }] : [];
  });
}

/** Ô soi (§16.6): dữ kiện số trong chuỗi của đại lượng (`tangNhanManh`) và đầu vào trực tiếp
 *  (`numericalBasis`) — đọc từ cảnh backend phát, không tính gì. */
export function quantitySources(scene: Scene3D, id: string): { givens: string[]; inputs: string[] } {
  const o = scene.objects.find((x) => x.id === id);
  if (!o || o.type !== "quantity") return { givens: [], inputs: [] };
  const chuoi = tangNhanManh(scene, id);
  return {
    givens: scene.objects.filter((x) => x.type === "quantity" && chuoi.get(x.id) === "du_kien_so").map((x) => x.id),
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
    const tu = a.witness ? scene.objects.find((o) => o.id === a.witness!.from)?.xyz : undefined;
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
    const p = vat.map((o) => (o.xyz ? toVec3(o.xyz) : null));
    return p.length === 2 && p[0] && p[1] ? trungBinh([p[0], p[1]]) : null;
  }
  if (a.anchor === "region" || a.anchor === "solid") return trungBinh(dinh(vat[0]));
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
    const r = ung.find((c) => cachNeo(c, n.ax, n.ay) <= NEO_TOI_DA && !daChiem.some((b) => giao(c, b)));
    if (!r) continue;
    giu.set(n.id, r);
    daChiem.push(r);
  }
  return giu;
}
