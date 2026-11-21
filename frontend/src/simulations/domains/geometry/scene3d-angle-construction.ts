/**
 * Semantic-to-Scene3D — PHÉP DỰNG của góc mà đề hỏi (góc đường–mặt, hai đường, hai đường chéo nhau, nhị diện).
 *
 * Backend (`gan_dung_goc`, tầng số đo ngữ nghĩa) dựng bằng số học chính xác và chỉ phát khi cos² của góc dựng bằng đúng
 * giá trị đã đo. Phía này KHÔNG dựng gì: chỉ (1) kiểm lại bằng số thực ở toạ độ thế giới — fail-closed, sai một điều
 * kiện là không vẽ — và (2) đổi thành nét để vẽ: hai cạnh của góc, cung góc tại đỉnh (không nhãn, không con số: đáp số
 * vẫn ẩn), dấu vuông góc tại chân hình chiếu / tại đỉnh của góc nhị diện. Hiện từ bước kết luận của đại lượng.
 */
import type { AngleConstruction, Scene3D, SceneObject, Vec3 } from "./scene3d-model";
import { clampStep, toVec3 } from "./scene3d-model";

/** Sai số tương đối của phép kiểm trực giao / song song ở toạ độ thế giới (float sau T·p). */
export const SAI_SO_DUNG_GOC = 1e-6;

export interface RightAngleMark { at: Vec3; u: Vec3; v: Vec3 }

export interface AngleConstructionShown {
  /** Id của đại lượng góc. */
  id: string;
  relation: AngleConstruction["relation"];
  vertex: Vec3;
  arms: [Vec3, Vec3];
  /** `line_plane`: đoạn điểm → chân hình chiếu (nét đứt). */
  perpendicular?: [Vec3, Vec3];
  /** `line_line_skew`: cạnh thứ hai là đoạn phụ song song (vẽ nét đứt phụ). */
  parallelHelper?: boolean;
  rightAngles: RightAngleMark[];
}

const tru = (a: Vec3, b: Vec3): Vec3 => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const tich = (a: Vec3, b: Vec3) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const doDai = (a: Vec3) => Math.sqrt(tich(a, a));
const huuHan = (a: Vec3) => a.every(Number.isFinite);

/** Hai phương vuông góc (tương đối) — cùng chuẩn sai số cho mọi phép kiểm. */
function vuong(a: Vec3, b: Vec3): boolean {
  const la = doDai(a), lb = doDai(b);
  return la > 0 && lb > 0 && Math.abs(tich(a, b)) <= SAI_SO_DUNG_GOC * la * lb;
}

function songSong(a: Vec3, b: Vec3): boolean {
  const la = doDai(a), lb = doDai(b);
  return la > 0 && lb > 0 && Math.abs(Math.abs(tich(a, b)) - la * lb) <= SAI_SO_DUNG_GOC * la * lb;
}

/** Một phép dựng (toạ độ THẾ GIỚI, đã qua `veKhongGian`) → nét để vẽ; không hợp lệ ⇒ `null`. */
export function angleConstructionShape(id: string, g: AngleConstruction): AngleConstructionShown | null {
  if (g.schema !== "angle-construction/1" || g.arms?.length !== 2) return null;
  const o = toVec3(g.vertex);
  const a = toVec3(g.arms[0].to), b = toVec3(g.arms[1].to);
  if (![o, a, b].every(huuHan) || doDai(tru(a, o)) === 0 || doDai(tru(b, o)) === 0) return null;
  // Góc đề hỏi là góc không tù: hai tia mở góc tù là góc BÙ (cùng cos²) — không vẽ. Thiếu khai báo miền ⇒ không vẽ.
  if (g.angle_domain !== "[0°, 90°]" || tich(tru(a, o), tru(b, o)) < -SAI_SO_DUNG_GOC * doDai(tru(a, o)) * doDai(tru(b, o))) return null;
  const ra: AngleConstructionShown = { id, relation: g.relation, vertex: o, arms: [a, b], rightAngles: [] };
  if (g.relation === "line_plane") {
    const p = g.perpendicular;
    if (!p) return null;
    const from = toVec3(p.from), foot = toVec3(p.foot), u = toVec3(p.u), v = toVec3(p.v);
    // Chân là đầu của cạnh thứ hai, cạnh thứ nhất đi qua `from`; `u` ⟂ `v` (đoạn tới chân vuông góc với mặt).
    if (![from, foot, u, v].every(huuHan) || doDai(tru(foot, b)) > SAI_SO_DUNG_GOC * (1 + doDai(b))
        || !songSong(tru(from, o), tru(a, o)) || !vuong(u, v) || !songSong(u, tru(o, foot))) return null;
    ra.perpendicular = [from, foot];
    ra.rightAngles.push({ at: foot, u: tru(o, foot), v: tru(from, foot) });
  } else if (g.relation === "line_line_skew") {
    const q = g.parallel;
    if (!q || doDai(tru(toVec3(q.through), o)) > SAI_SO_DUNG_GOC * (1 + doDai(o))
        || doDai(tru(toVec3(q.to), b)) > SAI_SO_DUNG_GOC * (1 + doDai(b))) return null;
    ra.parallelHelper = true;
  } else if (g.relation === "plane_plane") {
    const e = g.edge ? toVec3(g.edge.direction) : null;
    if (!e || !huuHan(e) || !vuong(e, tru(a, o)) || !vuong(e, tru(b, o))) return null;
    ra.rightAngles.push({ at: o, u: e, v: tru(a, o) }, { at: o, u: e, v: tru(b, o) });
  } else if (g.relation !== "line_line") {
    return null;
  }
  return ra;
}

/** Bước kết luận của từng đại lượng (sự kiện FINAL_RESULT / MEASURE) — phép dựng hiện từ bước đó, như nhân chứng. */
function buocKetLuan(scene: Scene3D): Map<string, number> {
  const ra = new Map<string, number>();
  for (const e of scene.events ?? []) {
    if (e.object && (e.semantic_kind === "FINAL_RESULT" || e.action === "MEASURE") && !ra.has(e.object)) {
      ra.set(e.object, e.step_index);
    }
  }
  return ra;
}

/** Phép dựng góc hiện ở bước `step`: đại lượng đã tới bước kết luận và mọi điểm có tên nó dùng đều đã có mặt. */
export function angleConstructionsAt(scene: Scene3D, step: number, present: ReadonlySet<string>): AngleConstructionShown[] {
  const k = clampStep(scene, step);
  const ketLuan = buocKetLuan(scene);
  return scene.objects.flatMap((o: SceneObject) => {
    const g = o.type === "quantity" ? o.angle_construction : undefined;
    const tai = ketLuan.get(o.id);
    if (!g || tai === undefined || tai > k) return [];
    const ids = [g.vertex_id, g.arms[0]?.to_id, g.arms[1]?.to_id].filter((x): x is string => Boolean(x));
    if (!ids.every((x) => present.has(x))) return [];
    const s = angleConstructionShape(o.id, g);
    return s ? [s] : [];
  });
}

/** Đường cao (`altitude-construction/1`) hiện ở bước kết luận của thể tích, khi đỉnh và điểm `u_to` đã có mặt. Kiểm lại
 *  fail-closed ở toạ độ thế giới: đoạn đỉnh → chân vuông góc với phương dấu `u`, `u` hướng tới đúng điểm có tên, đỉnh và
 *  chân khác nhau. Trả về cùng dạng nét như đoạn vuông góc của nhân chứng (`from`, `foot`, `u`, `v`, `uTo`). */
export interface AltitudeShown { id: string; from: Vec3; foot: Vec3; u: Vec3; v: Vec3; uTo: Vec3 }

export function altitudeConstructionsAt(scene: Scene3D, step: number, present: ReadonlySet<string>): AltitudeShown[] {
  const k = clampStep(scene, step);
  const ketLuan = buocKetLuan(scene);
  const theoId = new Map(scene.objects.map((o) => [o.id, o]));
  return scene.objects.flatMap((o: SceneObject): AltitudeShown[] => {
    const h = o.type === "quantity" ? o.altitude_construction : undefined;
    const tai = ketLuan.get(o.id);
    if (!h || h.schema !== "altitude-construction/1" || tai === undefined || tai > k) return [];
    if (!present.has(h.apex_id) || !present.has(h.marker.u_to)) return [];
    const toi = theoId.get(h.marker.u_to)?.xyz;
    const dinh = theoId.get(h.apex_id)?.xyz;
    if (!toi || !dinh) return [];
    const from = toVec3(h.from), foot = toVec3(h.foot), u = toVec3(h.marker.u), v = toVec3(h.marker.v), uTo = toVec3(toi);
    if (![from, foot, u, v, uTo].every(huuHan) || doDai(tru(from, toVec3(dinh))) > SAI_SO_DUNG_GOC * (1 + doDai(from))) return [];
    if (!vuong(tru(from, foot), u) || !songSong(u, tru(uTo, foot)) || !songSong(v, tru(from, foot))) return [];
    return [{ id: o.id, from, foot, u, v, uTo }];
  });
}

/** Điểm của cung góc tại đỉnh, bán kính `r`, từ cạnh thứ nhất sang cạnh thứ hai (nội suy cầu — trình bày thuần). */
export function angleArcPoints(s: Pick<AngleConstructionShown, "vertex" | "arms">, r: number, n = 24): Vec3[] {
  const o = s.vertex;
  const ua = tru(s.arms[0], o), ub = tru(s.arms[1], o);
  const la = doDai(ua), lb = doDai(ub);
  const a: Vec3 = [ua[0] / la, ua[1] / la, ua[2] / la], b: Vec3 = [ub[0] / lb, ub[1] / lb, ub[2] / lb];
  const goc = Math.acos(Math.max(-1, Math.min(1, tich(a, b))));
  if (!(goc > 1e-9)) return [];
  const sg = Math.sin(goc);
  return Array.from({ length: n + 1 }, (_, i) => {
    const t = (i / n) * goc;
    const ka = Math.sin(goc - t) / sg, kb = Math.sin(t) / sg;
    return [o[0] + r * (ka * a[0] + kb * b[0]), o[1] + r * (ka * a[1] + kb * b[1]), o[2] + r * (ka * a[2] + kb * b[2])] as Vec3;
  });
}
