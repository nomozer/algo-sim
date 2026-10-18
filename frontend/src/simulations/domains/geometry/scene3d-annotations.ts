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
    if (o.type === "polygon3" && o.vertex_ids && o.vertex_ids.length >= 3) {
      o.vertex_ids.forEach((v, i, d) => ra.add(capDiem(v, d[(i + 1) % d.length])));
    }
    for (const e of o.edge_ownership ?? []) {
      if (e.endpoint_ids?.length === 2) ra.add(capDiem(e.endpoint_ids[0], e.endpoint_ids[1]));
    }
    if (o.perpendicular_witness?.from && ids.has(o.perpendicular_witness.from)) {
      ra.add(capDiem(o.id, o.perpendicular_witness.from));
    }
  }
  return ra;
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
    // W2 · A: nhãn của một ĐOẠN chờ đoạn ấy được dựng — ở MỌI chế độ, kể cả "Hiện tất cả" và khi đang chọn nó.
    if (a.anchor === "segment" && !(a.subject_ids.length === 2 && doan.has(capDiem(a.subject_ids[0], a.subject_ids[1])))) {
      continue;
    }
    const lienQuan = tieuDiem(o, a);
    if (!(view.showAll || vai === "given" || lienQuan)) continue;
    ra.push({
      id: o.id, kind: a.kind, role: vai, subject_ids: [...a.subject_ids], anchor: a.anchor,
      witness: a.witness,
      text: `${o.notation ?? o.label} = ${o.value}${a.unit ? ` ${a.unit}` : ""}`,
      priority: (vai === "result" ? 2 : 1) + (lienQuan ? 10 : 0),
      related: lienQuan,
    });
  }
  return ra;
}

/** `vai`: nhân chứng của nhãn khoảng cách đang xét (`khoang_cach`) hay đoạn vuông góc phụ của điểm hình chiếu
 *  (`hinh_chieu`) — renderer chọn màu theo vai (`scene3d-view.tsx::mauNhanChung`), không theo tiền tố id. */
export interface WitnessShown { id: string; vai: "khoang_cach" | "hinh_chieu"; from: Vec3; foot: Vec3; u: Vec3; v: Vec3 }

/** §16.7 — nhân chứng của các nhãn khoảng cách ĐANG HIỆN; toạ độ đều do backend phát (chân chính xác). */
export function witnessesShown(scene: Scene3D, entries: AnnotationEntry[]): WitnessShown[] {
  const theoId = new Map(scene.objects.map((o) => [o.id, o]));
  return entries.flatMap((e) => {
    const w = e.anchor === "witness" ? e.witness : undefined;
    const tu = w ? theoId.get(w.from)?.xyz : undefined;
    return w && tu
      ? [{ id: e.id, vai: "khoang_cach" as const, from: toVec3(tu), foot: toVec3(w.foot), u: toVec3(w.marker.u),
        v: toVec3(w.marker.v) }]
      : [];
  });
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
    const w = present.has(o.id) ? o.perpendicular_witness : undefined;
    const tu = w ? theoId.get(w.from)?.xyz : undefined;
    return w && tu && present.has(w.from)
      ? [{ id: `perpendicular:${o.id}`, vai: "hinh_chieu" as const, from: toVec3(tu), foot: toVec3(w.foot),
        u: toVec3(w.marker.u), v: toVec3(w.marker.v) }]
      : [];
  });
  const daCo = new Set(tuDiem.map((w) => `${w.from.join(",")}|${w.foot.join(",")}`));
  const k = step !== undefined && scene.events?.length ? clampStep(scene, step) : undefined;
  const daTinh = new Set<string>();
  const ketLuan = new Set<string>();
  if (k !== undefined) {
    for (const e of scene.events) {
      if (e.step_index > k || !e.object) continue;
      const koLoai = !e.semantic_kind && e.action === "MEASURE";
      if (e.semantic_kind === "FINAL_RESULT" || koLoai) ketLuan.add(e.object);
      if (e.semantic_kind === "MEASUREMENT" || e.semantic_kind === "FINAL_RESULT" || koLoai) daTinh.add(e.object);
    }
  }
  const chungNhanDuongMp = (d: SceneObject, mp: SceneObject): boolean =>
    scene.objects.some((q) => {
      if (!present.has(q.id)) return false;
      if (k !== undefined && !daTinh.has(q.id) && !ketLuan.has(q.id)) return false;
      const dep = q.depends ?? [];
      if (!dep.includes(d.id) || !dep.includes(mp.id)) return false;
      const chu = `${q.notation ?? ""} ${q.label ?? ""}`;
      if (chu.includes("⊥") || q.value === "90°" || q.value === "90") return true;
      const bangKhong = q.value === "0" || (q.exact?.kind === "rational" && q.exact.value === "0");
      if (chu.includes("cos") && bangKhong) return true;
      return false;
    });
  const duongHien = scene.objects.filter(
    (o) => present.has(o.id)
      && ((o.type === "line3" && Boolean(o.direction)) || (o.type === "segment3" && o.endpoints?.length === 2))
      && (o.depends?.length ?? 0) >= 2,
  );
  const mpHien = scene.objects.filter(
    (o) => present.has(o.id) && o.type === "plane3" && o.normal && (o.depends?.length ?? 0) >= 3,
  );
  const tuDuongMp: WitnessShown[] = [];
  for (const d of duongHien) {
    const vd: Vec3 = d.direction
      ? toVec3(d.direction)
      : (() => {
          const a = toVec3(d.endpoints![0]);
          const b = toVec3(d.endpoints![1]);
          return [b[0] - a[0], b[1] - a[1], b[2] - a[2]];
        })();
    const nd = Math.hypot(...vd);
    if (!Number.isFinite(nd) || nd < 1e-6) continue;
    for (const mp of mpHien) {
      if (!chungNhanDuongMp(d, mp)) continue;
      const np = toVec3(mp.normal!);
      const nnp = Math.hypot(...np);
      if (!Number.isFinite(nnp) || nnp < 1e-6) continue;
      const cx = vd[1] * np[2] - vd[2] * np[1];
      const cy = vd[2] * np[0] - vd[0] * np[2];
      const cz = vd[0] * np[1] - vd[1] * np[0];
      if (Math.hypot(cx, cy, cz) > 1e-4 * nd * nnp) continue;
      const chungId = (d.depends ?? []).find(
        (id) => (mp.depends ?? []).includes(id) && present.has(id) && Boolean(theoId.get(id)?.xyz),
      );
      if (!chungId) continue;
      const chan = toVec3(theoId.get(chungId)!.xyz!);
      const diemKhacD = (d.depends ?? [])
        .filter((id) => id !== chungId && present.has(id) && Boolean(theoId.get(id)?.xyz))
        .map((id) => toVec3(theoId.get(id)!.xyz!))[0];
      const v: Vec3 = diemKhacD
        ? [diemKhacD[0] - chan[0], diemKhacD[1] - chan[1], diemKhacD[2] - chan[2]]
        : vd;
      const nv = Math.hypot(...v);
      if (!Number.isFinite(nv) || nv < 1e-6) continue;
      const vcx = v[1] * np[2] - v[2] * np[1];
      const vcy = v[2] * np[0] - v[0] * np[2];
      const vcz = v[0] * np[1] - v[1] * np[0];
      if (Math.hypot(vcx, vcy, vcz) > 1e-4 * nv * nnp) continue;
      const diemKhacMp = (mp.depends ?? [])
        .filter((id) => id !== chungId && present.has(id) && Boolean(theoId.get(id)?.xyz))
        .map((id) => toVec3(theoId.get(id)!.xyz!))
        .sort((a, b) => Math.abs(a[2] - chan[2]) - Math.abs(b[2] - chan[2]));
      const daHuong: { raw: Vec3; donVi: Vec3 }[] = [];
      for (const pMp of diemKhacMp) {
        const uRaw: Vec3 = [pMp[0] - chan[0], pMp[1] - chan[1], pMp[2] - chan[2]];
        const nu = Math.hypot(...uRaw);
        if (!Number.isFinite(nu) || nu < 1e-6) continue;
        // Kiểm tra trực tiếp trên hướng gốc uRaw (không dùng phép chiếu đại số để giả tạo hướng vuông góc):
        // 1) uRaw phải thực sự nằm trong mặt phẳng mp (dot(uRaw, np) = 0)
        // 2) uRaw phải thực sự vuông góc với v và vd (dot(uRaw, v) = 0)
        const dotUN = uRaw[0] * np[0] + uRaw[1] * np[1] + uRaw[2] * np[2];
        const dotUV = uRaw[0] * v[0] + uRaw[1] * v[1] + uRaw[2] * v[2];
        const dotUVd = uRaw[0] * vd[0] + uRaw[1] * vd[1] + uRaw[2] * vd[2];
        if (Math.abs(dotUN) > 1e-4 * nu * nnp) continue;
        if (Math.abs(dotUV) > 1e-4 * nu * nv) continue;
        if (Math.abs(dotUVd) > 1e-4 * nu * nd) continue;
        const uDonVi: Vec3 = [uRaw[0] / nu, uRaw[1] / nu, uRaw[2] / nu];
        if (daHuong.some((h) => Math.abs(h.donVi[0] * uDonVi[0] + h.donVi[1] * uDonVi[1] + h.donVi[2] * uDonVi[2]) > 0.98)) continue;
        daHuong.push({ raw: uRaw, donVi: uDonVi });
      }
      // Phải có ít nhất 2 hướng gốc không cùng phương trong mặt phẳng cùng thực sự vuông góc với đường thẳng,
      // và chỉ phát 1 ký hiệu góc vuông rõ ràng tại điểm giao để tránh chồng chéo 2 ký hiệu trên hình chiếu.
      if (daHuong.length < 2) continue;
      const khoa = `${chan.join(",")}|${chan.join(",")}`;
      if (daCo.has(khoa)) continue;
      daCo.add(khoa);
      tuDuongMp.push({
        id: `perpendicular:${d.id}`,
        vai: "hinh_chieu",
        from: chan,
        foot: chan,
        u: daHuong[0].raw,
        v,
      });
    }
  }
  if (k === undefined) return [...tuDiem, ...tuDuongMp];
  if (ketLuan.size === 0) return [...tuDiem, ...tuDuongMp];
  const tuKetQua = scene.objects.flatMap((o) => {
    const ann = o.type === "quantity" && ketLuan.has(o.id) ? o.annotation : undefined;
    if (!ann) return [];
    const w = vaiTro(o, ann) === "result" && ann.anchor === "witness" ? ann.witness : undefined;
    const tu = w ? theoId.get(w.from)?.xyz : undefined;
    if (!w || !tu || !present.has(w.from) || !ann.subject_ids.every((s) => present.has(s))) return [];
    const from = toVec3(tu);
    const foot = toVec3(w.foot);
    if (daCo.has(`${from.join(",")}|${foot.join(",")}`)) return [];
    return [{ id: `perpendicular:${o.id}`, vai: "hinh_chieu" as const, from, foot,
      u: toVec3(w.marker.u), v: toVec3(w.marker.v) }];
  });
  return [...tuDiem, ...tuDuongMp, ...tuKetQua];
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
