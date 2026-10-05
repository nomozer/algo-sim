/**
 * HÌNH PHỤ — regular-square-pyramid-w02 · D. Hàm thuần, phía trình bày; không đổi dữ liệu, timeline hay xuất xứ.
 *
 * Hình phụ = đường thẳng / mặt phẳng mà backend gắn ĐÚNG MỘT vai `CONSTRUCT_AUXILIARY_GEOMETRY` (formation W14), không
 * phải dữ kiện hay mục tiêu của đề (`display_group` không có `given`/`target`). Hai loại theo việc của nó, đọc từ
 * `depends` của các vật khác — không đọc tên:
 *   - DỰNG — có vật hình học dựng TỪ nó (AC, BD → giao điểm O): hiện từ lúc dựng tới bước mọi vật ấy đã có (xong
 *     nhiệm vụ), sau đó ẩn khỏi cảnh trung tính;
 *   - ĐO — mặt phẳng chỉ làm toán hạng cho đại lượng (mặt phẳng qua A, B, C để đo chiều cao): ẩn mặc định.
 * Đường chỉ để đo (vd đường BD của "khoảng cách từ S tới BD") KHÔNG ẩn: đó là vật đề gọi tên.
 * Công tắc «Hình phụ» hiện tất cả; chọn hình phụ — hoặc một vật mà chuỗi phụ thuộc chứa nó — cũng hiện nó.
 */
import type { Scene3D } from "./scene3d-model";
import { clampStep, geometryStepOf, geometryTimeline, objectsAt, stepCount } from "./scene3d-model";
import { dependencyClosure } from "./interaction-state";

export const VAI_PHU = "CONSTRUCT_AUXILIARY_GEOMETRY";

export interface HinhPhu {
  loai: "dung" | "do";
  /** DỰNG: bước cuối còn hiện (vật dựng từ nó đều đã có). ĐO: −1 (ẩn mặc định ở mọi bước). */
  xongTai: number;
}

const _cache = new WeakMap<Scene3D, Map<string, HinhPhu>>();

export function auxiliaryObjects(scene: Scene3D): Map<string, HinhPhu> {
  const co = _cache.get(scene);
  if (co) return co;
  const ra = new Map<string, HinhPhu>();
  const n = stepCount(scene);
  for (const o of scene.objects) {
    const vai = o.formation_roles ?? [];
    const nhom = o.display_group ?? [];
    if (!(o.type === "line3" || o.type === "plane3") || o.origin !== "derived"
        || vai.length !== 1 || vai[0] !== VAI_PHU || nhom.includes("given") || nhom.includes("target")) continue;
    const con = scene.objects.filter((x) => x.depends?.includes(o.id));
    const dung = con.filter((x) => x.type !== "quantity").map((x) => x.id);
    if (dung.length > 0) {
      const k = [...Array(n).keys()].find((s) => {
        const hien = new Set(objectsAt(scene, s).map((x) => x.id));
        return dung.every((id) => hien.has(id));
      });
      if (k !== undefined) ra.set(o.id, { loai: "dung", xongTai: k });
    } else if (o.type === "plane3" && con.length > 0) {
      ra.set(o.id, { loai: "do", xongTai: -1 });
    }
  }
  _cache.set(scene, ra);
  return ra;
}

/** Hình phụ ẩn ở bước `step` (khung của renderer). `shown` = công tắc «Hình phụ». */
export function auxiliaryHiddenAt(scene: Scene3D, step: number, shown: boolean, selectedId: string | null): Set<string> {
  if (shown) return new Set();
  const k = clampStep(scene, step);
  const tieuDiem = selectedId ? new Set([selectedId, ...dependencyClosure(scene, selectedId)]) : new Set<string>();
  const ra = new Set<string>();
  for (const [id, h] of auxiliaryObjects(scene)) {
    if (!tieuDiem.has(id) && k > h.xongTai) ra.add(id);
  }
  return ra;
}

export type MucBuoc = { loai: "buoc"; index: number } | { loai: "nhom"; chinh: number; con: number[] };

/**
 * Danh sách «Các bước dựng» có NHÓM: một dãy bước liền nhau chỉ dựng hình phụ loại DỰNG, nối ngay bằng bước dựng
 * vật cần chúng (AC, BD rồi giao điểm O) ⇒ một mục chính (bước của vật ấy) với các bước con theo đúng thứ tự —
 * mỗi bước con vẫn là một bước của thanh bước, giữ nguyên delta hình học. Không bước nào bị gộp mất.
 */
export function geometryStepGroups(scene: Scene3D): MucBuoc[] {
  const phu = auxiliaryObjects(scene);
  const neo = geometryTimeline(scene).map((g) => g.anchor);
  const moi = (g: number) => {
    const truoc = g > 0 ? new Set(objectsAt(scene, neo[g - 1]).map((o) => o.id)) : new Set<string>();
    return objectsAt(scene, neo[g]).filter((o) => o.render !== "readout" && o.render !== "non_visual"
      && !truoc.has(o.id)).map((o) => o.id);
  };
  const laPhu = (g: number) => {
    const m = moi(g);
    return g > 0 && m.length > 0 && m.every((id) => phu.get(id)?.loai === "dung");
  };
  const ra: MucBuoc[] = [];
  for (let g = 0; g < neo.length; g += 1) {
    if (!laPhu(g)) { ra.push({ loai: "buoc", index: g }); continue; }
    let h = g;
    while (h + 1 < neo.length && laPhu(h + 1)) h += 1;
    const xong = Math.max(...Array.from({ length: h - g + 1 }, (_, i) => g + i)
      .flatMap((x) => moi(x).map((id) => phu.get(id)!.xongTai)));
    if (h + 1 < neo.length && geometryStepOf(scene, xong) === h + 1) {
      ra.push({ loai: "nhom", chinh: h + 1, con: Array.from({ length: h - g + 2 }, (_, i) => g + i) });
      g = h + 1;
    } else {
      for (let x = g; x <= h; x += 1) ra.push({ loai: "buoc", index: x });
      g = h;
    }
  }
  return ra;
}
