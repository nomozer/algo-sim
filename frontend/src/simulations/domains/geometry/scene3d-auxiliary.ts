/**
 * HÌNH PHỤ — regular-square-pyramid-w02 · D. Hàm thuần, phía trình bày; không đổi dữ liệu, timeline hay xuất xứ.
 *
 * Hình phụ = đường thẳng / mặt phẳng mà backend gắn ĐÚNG MỘT vai `CONSTRUCT_AUXILIARY_GEOMETRY` (formation W14), không
 * phải dữ kiện hay mục tiêu của đề (`display_group` không có `given`/`target`). Hai loại theo việc của nó, đọc từ
 * `depends` của các vật khác — không đọc tên:
 *   - DỰNG — có vật hình học dựng TỪ nó (AC, BD → giao điểm O): hiện từ lúc dựng tới bước mọi vật ấy đã có (xong
 *     nhiệm vụ), sau đó ẩn khỏi cảnh trung tính;
 *   - ĐO — mặt phẳng chỉ làm toán hạng cho đại lượng (mặt phẳng qua A, B, C để đo chiều cao): ẩn mặc định; phân loại
 *     ở `measurementOnlyPlanes` (scene3d-model) — cùng thẩm quyền khiến sự kiện chỉ dựng nó không mở bước dựng (W3).
 * Đường chỉ để đo (vd đường BD của "khoảng cách từ S tới BD") KHÔNG ẩn: đó là vật đề gọi tên.
 * Công tắc «Hình phụ» hiện tất cả; chọn hình phụ — hoặc một vật mà chuỗi phụ thuộc chứa nó — cũng hiện nó.
 */
import type { Scene3D } from "./scene3d-model";
import { clampStep, geometryStepOf, geometryTimeline, measurementOnlyPlanes, objectsAt, stepCount } from "./scene3d-model";
import { dependencyClosure } from "./interaction-state";

export const VAI_PHU = "CONSTRUCT_AUXILIARY_GEOMETRY";

export interface HinhPhu {
  loai: "dung" | "do";
  /** DỰNG: bước cuối còn hiện (vật dựng từ nó đều đã có). ĐO: −1 (ẩn mặc định ở mọi bước). */
  xongTai: number;
}

const _cache = new WeakMap<Scene3D, Map<string, HinhPhu>>();
const _measLinesCache = new WeakMap<Scene3D, Set<string>>();

function edgePairKey(a: string, b: string): string {
  return a < b ? `${a}::${b}` : `${b}::${a}`;
}

function collectSolidAndPolygonEdgeKeys(scene: Scene3D): Set<string> {
  const keys = new Set<string>();
  for (const o of scene.objects) {
    if (o.type === "solid" && o.vertex_ids && o.faces) {
      for (const f of o.faces) {
        for (let i = 0; i < f.length; i += 1) {
          const u = o.vertex_ids[f[i]];
          const v = o.vertex_ids[f[(i + 1) % f.length]];
          if (u && v && u !== v) keys.add(edgePairKey(u, v));
        }
      }
    } else if (o.type === "polygon3") {
      const vs = o.vertex_ids && o.vertex_ids.length >= 3 ? o.vertex_ids : (o.depends ?? []);
      if (vs.length >= 3) {
        for (let i = 0; i < vs.length; i += 1) {
          const u = vs[i];
          const v = vs[(i + 1) % vs.length];
          if (u && v && u !== v) keys.add(edgePairKey(u, v));
        }
      }
    }
  }
  return keys;
}

function collectFiniteSegmentKeys(scene: Scene3D): Set<string> {
  const keys = collectSolidAndPolygonEdgeKeys(scene);
  for (const o of scene.objects) {
    if (o.type !== "segment3") continue;
    const eps = o.endpoint_ids && o.endpoint_ids.length === 2 ? o.endpoint_ids : (o.depends ?? []);
    if (eps.length === 2 && eps[0] !== eps[1]) {
      keys.add(edgePairKey(eps[0], eps[1]));
    }
  }
  return keys;
}

/**
 * ĐƯỜNG THẲNG PHỤ CHỈ ĐỂ ĐO (`line3` dẫn xuất có `CONSTRUCT_AUXILIARY_GEOMETRY`, không phải `given`/`target`,
 * đi qua 2 điểm đã nối sẵn bằng cạnh khối/đoạn hữu hạn, và không có vật hình học nào khác dựng từ nó ngoài `quantity`):
 * ẩn mặc định giống `measurementOnlyPlanes` và không mở bước «Xác định đường thẳng chứa cạnh ...».
 */
export function measurementOnlyLines(scene: Scene3D): Set<string> {
  const cached = _measLinesCache.get(scene);
  if (cached) return cached;
  const loai = new Map(scene.objects.map((o) => [o.id, o.type]));
  const finiteKeys = new Set([
    ...collectFiniteSegmentKeys(scene),
    ...collectSolidAndPolygonEdgeKeys(scene),
  ]);
  const ra = new Set<string>();
  for (const o of scene.objects) {
    if (o.type !== "line3" || o.origin !== "derived") continue;
    const vai = o.formation_roles ?? [];
    const nhom = o.display_group ?? [];
    if (vai.length !== 1 || vai[0] !== VAI_PHU || nhom.includes("given") || nhom.includes("target")) continue;
    const deps = o.depends ?? [];
    if (deps.length !== 2 || !deps.every((id) => loai.get(id) === "point3")) continue;
    if (!finiteKeys.has(edgePairKey(deps[0], deps[1]))) continue;
    const nonQtyCon = scene.objects.filter((x) => !x.parent && x.type !== "quantity" && x.depends?.includes(o.id));
    if (nonQtyCon.length === 0) {
      ra.add(o.id);
    }
  }
  _measLinesCache.set(scene, ra);
  return ra;
}

export function auxiliaryObjects(scene: Scene3D): Map<string, HinhPhu> {
  const co = _cache.get(scene);
  if (co) return co;
  const ra = new Map<string, HinhPhu>();
  const n = stepCount(scene);
  const loai = new Map(scene.objects.map((o) => [o.id, o.type]));
  const duongChieu = new Set(scene.objects.flatMap((o) => [
    ...(o.perpendicular_witness?.on ? [o.perpendicular_witness.on] : []),
    ...(o.type === "point3"
      && (o.depends ?? []).filter((id) => loai.get(id) === "line3").length === 1
      && (o.depends ?? []).some((id) => loai.get(id) === "point3")
      ? (o.depends ?? []).filter((id) => loai.get(id) === "line3")
      : []),
  ]));
  const dinhKhoi = new Set(scene.objects.flatMap((o) =>
    (o.type === "solid" || o.type === "curved_solid") ? [...(o.depends ?? []), ...(o.vertex_ids ?? [])] : []));
  // Tập đỉnh của từng MẶT khối (id thực thể) — mặt phẳng qua các đỉnh của một mặt đã nằm trên hình (G7: thay cho
  // phép so `o.id === "day"` cũ; luật hiển thị không đọc tên vật).
  const matKhoi = scene.objects.flatMap((o) => o.type === "solid" && o.vertex_ids && o.faces
    ? o.faces.map((f) => new Set(f.map((i) => o.vertex_ids![i]))) : []);
  const laMatCuaKhoi = (o: { depends?: string[] }) =>
    matKhoi.some((m) => (o.depends ?? []).every((id) => m.has(id)));
  const solidEdgeKeys = collectSolidAndPolygonEdgeKeys(scene);
  const finiteSegKeys = collectFiniteSegmentKeys(scene);
  const measOnlyLines = measurementOnlyLines(scene);
  const coKhoiChinh = scene.objects.some((x) => x.type === "solid" || x.type === "curved_solid");
  const laDuongCatMatPhangDocLap = (
    o: Scene3D["objects"][number],
    conList: Scene3D["objects"],
  ): boolean =>
    !coKhoiChinh
    && o.type === "line3"
    && conList.some(
      (x) =>
        x.type === "point3"
        && !x.perpendicular_witness
        && (x.depends ?? []).some((depId) => loai.get(depId) === "plane3"),
    );
  const laDuongMangCanhDaCo = (o: Scene3D["objects"][number]): boolean => {
    if (o.type !== "line3") return false;
    const deps = o.depends ?? [];
    return deps.length === 2 && deps.every((id) => loai.get(id) === "point3") && finiteSegKeys.has(edgePairKey(deps[0], deps[1]));
  };
  const laDuongMangCanhKhoi = (o: Scene3D["objects"][number]): boolean => {
    if (o.type !== "line3") return false;
    const deps = o.depends ?? [];
    return deps.length === 2 && deps.every((id) => loai.get(id) === "point3") && solidEdgeKeys.has(edgePairKey(deps[0], deps[1]));
  };
  const nonQtyChildrenOf = (id: string) =>
    scene.objects.filter((x) => !x.parent && x.type !== "quantity" && x.depends?.includes(id));
  // Mặt phẳng / đường thẳng phụ trợ trung gian chỉ phục vụ xác định tâm của khối cầu (`curved_solid` `ball`,
  // ví dụ các mặt phẳng trung trực và trục ngoại tiếp): hiện trong các bước xác định tâm, tự ẩn khi khối cầu đã dựng.
  const timKhungDungTamMatCau = (startId: string): string[] | null => {
    const first = nonQtyChildrenOf(startId);
    if (first.length === 0) return null;
    const visited = new Set<string>([startId]);
    const stack = [...first];
    const sphereLeaves: string[] = [];
    let sawCenterPoint = false;
    while (stack.length > 0) {
      const cur = stack.pop()!;
      if (visited.has(cur.id)) continue;
      visited.add(cur.id);
      if (cur.type === "curved_solid" && cur.curved_kind === "ball") {
        sphereLeaves.push(cur.id);
        continue;
      }
      if (cur.type === "point3") {
        sawCenterPoint = true;
        // Điểm tâm I có thể có thêm các đoạn bán kính ngoại tiếp (IS, IA, OI, MI) dựng từ I ngoài mặt cầu
        const ptNext = nonQtyChildrenOf(cur.id).filter(
          (nx) => !(nx.type === "segment3" && (nx.formation_roles ?? []).every((r) => r === VAI_PHU)),
        );
        if (ptNext.length === 0) return null;
        stack.push(...ptNext);
        continue;
      }
      if (cur.type !== "plane3" && cur.type !== "line3") {
        return null;
      }
      const next = nonQtyChildrenOf(cur.id);
      if (next.length === 0) return null;
      stack.push(...next);
    }
    return sphereLeaves.length > 0 && sawCenterPoint ? sphereLeaves : null;
  };
  for (const o of scene.objects) {
    const vai = o.formation_roles ?? [];
    const nhom = o.display_group ?? [];
    const con = scene.objects.filter((x) => !x.parent && x.depends?.includes(o.id));
    if (o.formation_roles === undefined) {
      if (o.type === "plane3" && o.origin === "derived" && (o.depends ?? []).length >= 3
          && (o.depends ?? []).every((id) => dinhKhoi.has(id))
          && con.every((x) => x.type === "quantity")
          && (con.length === 0 || laMatCuaKhoi(o))) {
        ra.set(o.id, { loai: "do", xongTai: -1 });
        continue;
      }
      if (o.type === "point3" && !dinhKhoi.has(o.id) && con.length === 1 && con[0].type === "plane3") {
        const mp = con[0];
        const mpCon = scene.objects.filter((x) => !x.parent && x.depends?.includes(mp.id));
        const vanhCong = mpCon.find((x) => x.type === "circle3" || x.type === "ellipse3");
        if (vanhCong && (mp.depends ?? []).indexOf(o.id) > 0
            && o.xyz?.join("|") !== vanhCong.center?.join("|")) {
          ra.set(o.id, { loai: "do", xongTai: -1 });
          continue;
        }
      }
    }
    if (
      o.origin === "derived"
      && (o.type === "plane3" || o.type === "line3")
      && (o.formation_roles === undefined || (vai.length === 1 && vai[0] === VAI_PHU))
      && !nhom.includes("given")
      && !nhom.includes("target")
      && !duongChieu.has(o.id)
    ) {
      const sphereLeaves = timKhungDungTamMatCau(o.id);
      if (sphereLeaves) {
        const k = [...Array(n).keys()].find((s) => {
          const hien = new Set(objectsAt(scene, s).map((x) => x.id));
          return sphereLeaves.every((id) => hien.has(id));
        });
        if (k !== undefined) {
          // Tự ẩn ngay khi khối cầu hoàn tất (trước bước dựng khối cầu k => xongTai = Math.max(0, k - 1))
          ra.set(o.id, { loai: "dung", xongTai: Math.max(0, k - 1) });
          continue;
        }
      }
    }
    if (measOnlyLines.has(o.id)) {
      ra.set(o.id, { loai: "do", xongTai: -1 });
      continue;
    }
    const choPhepDuongMangCanhMucTieu = nhom.includes("target") && laDuongMangCanhKhoi(o);
    if (o.origin !== "derived" || vai.length !== 1 || vai[0] !== VAI_PHU
        || nhom.includes("given") || (nhom.includes("target") && !choPhepDuongMangCanhMucTieu)) continue;
    const extendAcrossTrailingMeasures = (baseStep: number): number => {
      let endFrame = baseStep;
      while (endFrame + 1 < n) {
        const nextEv = scene.events.find((e) => e.step_index === endFrame + 1) ?? scene.events[endFrame + 1];
        if (nextEv?.action !== "MEASURE") break;
        endFrame += 1;
      }
      return endFrame;
    };
    if (o.authoritative === false && o.semantic_role === "AUXILIARY_CONSTRUCTION") {
      const finalPresentIds = new Set(objectsAt(scene, n - 1).map((x) => x.id));
      const isSpherePlaneAux = (o.display_group ?? []).includes("sphere_plane_aux");
      const curvedSectionsOnWitnessPlane =
        isSpherePlaneAux
          ? scene.objects
              .filter(
                (sec) =>
                  sec.type === "circle3"
                  && sec.surface_role !== "BASE_REGION"
                  && ((o.depends ?? []).length === 0
                    || (o.depends ?? []).some((depId) => (sec.depends ?? []).includes(depId) || sec.id === depId)),
              )
              .map((sec) => sec.id)
          : o.perpendicular_witness?.on
            ? scene.objects
                .filter(
                  (sec) =>
                    (sec.type === "circle3" || sec.type === "ellipse3")
                    && sec.surface_role !== "BASE_REGION"
                    && (sec.depends ?? []).includes(o.perpendicular_witness!.on),
                )
                .map((sec) => sec.id)
            : [];
      const targetCheckIds = [
        o.id,
        ...con.filter((x) => x.type !== "quantity").map((x) => x.id),
        ...curvedSectionsOnWitnessPlane,
      ].filter((id) => finalPresentIds.has(id));
      const k = [...Array(n).keys()].find((s) => {
        const hien = new Set(objectsAt(scene, s).map((x) => x.id));
        return targetCheckIds.length > 0
          ? targetCheckIds.every((id) => hien.has(id))
          : hien.has(o.id);
      });
      if (k !== undefined) {
        const gStep = geometryTimeline(scene)[geometryStepOf(scene, k)];
        ra.set(o.id, { loai: "dung", xongTai: extendAcrossTrailingMeasures(gStep ? gStep.anchor : k) });
      }
      continue;
    }
    if (o.type === "point3") {
      const diemPhuMp = !o.perpendicular_witness
        && (o.depends ?? []).some((id) => loai.get(id) === "vector3")
        && con.length > 0 && con.every((x) => x.type === "plane3");
      const authCon = con.filter((x) => x.authoritative !== false && x.type !== "quantity");
      const diemPhuKhongKyHieu =
        !o.notation
        && !o.perpendicular_witness
        && (o.depends ?? []).length === 2
        && (o.depends ?? []).every((id) => loai.get(id) === "point3")
        && authCon.length > 0
        && authCon.every((x) => (x.type === "point3" && Boolean(x.notation)) || x.type === "plane3");
      if (diemPhuKhongKyHieu) {
        const k = [...Array(n).keys()].find((s) => {
          const hien = new Set(objectsAt(scene, s).map((x) => x.id));
          return authCon.every((c) => hien.has(c.id));
        });
        if (k !== undefined) {
          const gStep = geometryTimeline(scene)[geometryStepOf(scene, k)];
          ra.set(o.id, { loai: "dung", xongTai: extendAcrossTrailingMeasures(gStep ? gStep.anchor : k) });
        }
        continue;
      }
      if (!diemPhuMp) continue;
    } else if (o.type === "line3") {
      if (laDuongCatMatPhangDocLap(o, con)) continue;
      if (duongChieu.has(o.id) && !laDuongMangCanhDaCo(o)) continue;
    } else if (o.type === "plane3") {
      if (!coKhoiChinh && Boolean(o.notation)) continue;
      if (duongChieu.has(o.id) && !laMatCuaKhoi(o)) continue;
    } else {
      continue;
    }
    const dung = con.filter((x) => x.type !== "quantity").map((x) => x.id);
    if (dung.length > 0) {
      const k = [...Array(n).keys()].find((s) => {
        const hien = new Set(objectsAt(scene, s).map((x) => x.id));
        return dung.every((id) => hien.has(id));
      });
      if (k !== undefined) ra.set(o.id, { loai: "dung", xongTai: k });
    } else if (measurementOnlyPlanes(scene).has(o.id)) {
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
  const phu = auxiliaryObjects(scene);
  const tieuDiem = selectedId ? new Set([selectedId, ...dependencyClosure(scene, selectedId)]) : new Set<string>();
  if (selectedId) {
    const selectedObj = scene.objects.find((x) => x.id === selectedId);
    const isSelectedAuxLike = Boolean(
      selectedObj
      && (phu.has(selectedId)
        || (selectedObj.display_group ?? []).includes("sphere_foundation_ref")
        || selectedObj.authoritative === false
        || selectedObj.semantic_role === "AUXILIARY_CONSTRUCTION"),
    );
    if (isSelectedAuxLike) {
      for (const o of scene.objects) {
        if (!phu.has(o.id)) continue;
        const refs = [...(o.depends ?? []), ...(o.endpoint_ids ?? [])];
        if (refs.includes(selectedId)) {
          tieuDiem.add(o.id);
          for (const depId of dependencyClosure(scene, o.id)) {
            tieuDiem.add(depId);
          }
        }
      }
    }
  }
  const ra = new Set<string>();
  for (const [id, h] of phu) {
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
