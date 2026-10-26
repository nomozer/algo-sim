/**
 * Owner P0 (2026-10-26): "ký hiệu góc vuông có cảm giác nằm trên mặt phẳng hoặc không neo rõ ràng tại chân vuông góc"
 * — cảnh `mp-vuong-goc-duong` (mặt phẳng qua B ⊥ SC, khoảng cách S → mặt phẳng ấy).
 *
 * Chuỗi Backend → envelope → cổng nhân chứng → renderer, kiểm trên bài mẫu THẬT (sinh bởi
 * `build_geometry_samples.py`), cộng sáu lỗi tiêm mà mỗi lỗi phải bị bắt.
 */
import * as THREE from "three";
import { describe, expect, it } from "vitest";

import { geometrySampleById } from "../../../data/geometry-samples";
import { type WitnessShown, projectionWitnessesAt } from "./scene3d-annotations";
import { type Scene3D, type Vec3, toVec3 } from "./scene3d-model";
import { datCoGocVuong, doanDaVe, vatNhanChung } from "./scene3d-view";
import { nhanChungVuongGocHopLe } from "./scene3d-witness-gate";

const canh = (id: string): Scene3D =>
  structuredClone((geometrySampleById(id)!.envelope as unknown as { scene3d: Scene3D }).scene3d);
/** Toạ độ đi qua bộ đệm GPU Float32 (~1e-7 tương đối): so tới 5 chữ số — lệch neo tiêm ở ④ lớn hơn 1e-3. */
const SO = 5;
const tatCa = (s: Scene3D) => new Set(s.objects.map((o) => o.id));
const buocCuoi = (s: Scene3D) => s.events.length - 1;
const nhanChungKetQua = (s: Scene3D) => projectionWitnessesAt(s, tatCa(s), buocCuoi(s));

const tru = (a: Vec3, b: Vec3): Vec3 => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const vh = (a: Vec3, b: Vec3) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const dai = (a: Vec3) => Math.hypot(...a);
const cungPhuong = (a: Vec3, b: Vec3) => Math.abs(vh(a, b)) / (dai(a) * dai(b));

/** Ô vuông của dấu (đỉnh `foot+s·u`, `foot+s(u+v)`, `foot+s·v`) ở toạ độ THẾ GIỚI sau `datCoGocVuong`. */
function dinhDau(nhom: THREE.Group): Vec3[] {
  const goc = nhom.children.find((x) => x.userData?.gocVuongDonVi) as THREE.Line;
  goc.updateMatrixWorld(true);
  const p = goc.geometry.getAttribute("position");
  return [0, 1, 2].map((i) => new THREE.Vector3().fromBufferAttribute(p, i).applyMatrix4(goc.matrixWorld).toArray() as Vec3);
}
/** Chân mà ô vuông THỰC SỰ neo vào: p(1,0) + p(0,1) − p(1,1). Không phụ thuộc cỡ dấu. */
const chanNgamDinh = ([p0, p1, p2]: Vec3[]): Vec3 => [p0[0] + p2[0] - p1[0], p0[1] + p2[1] - p1[1], p0[2] + p2[2] - p1[2]];

function camera(pos: Vec3): THREE.PerspectiveCamera {
  const c = new THREE.PerspectiveCamera(50, 16 / 9, 0.1, 200);
  c.position.set(...pos);
  c.lookAt(1, 1, 1);
  c.updateMatrixWorld(true);
  return c;
}

describe("P0 ký hiệu vuông góc — mp-vuong-goc-duong (thật)", () => {
  const s = canh("mp-vuong-goc-duong");
  const theoId = new Map(s.objects.map((o) => [o.id, o]));

  it("mặt phẳng dựng ra có TÊN, mặt đáy giữ tên khai (ABCD), bước dựng không lộ repr nội bộ", () => {
    expect(theoId.get("mpb")?.notation).toBe("(α)");
    expect(theoId.get("day")?.notation).toBe("(ABCD)");
    expect(JSON.stringify(s.events)).not.toMatch(/Plane3\(|Fraction\(|Vec3\(/);
    const buoc = s.events.find((e) => e.object === "mpb")!;
    expect(buoc.semantic_kind).toBe("GEOMETRY_CONSTRUCTION");
    expect(buoc.learner_text).toBe("Gọi (α) là mặt phẳng qua B và vuông góc với SC.");
  });

  it("đúng MỘT nhân chứng; chân H chính xác, thuộc (α) và SC; cạnh trong mặt phẳng chĩa tới B", () => {
    const ws = nhanChungKetQua(s);
    expect(ws).toHaveLength(1);
    const [w] = ws;
    expect(w.foot).toEqual([5 / 3, 5 / 3, 2 / 3]);
    const mp = theoId.get("mpb")!;
    expect(Math.abs(vh(toVec3(mp.normal!), tru(w.foot, toVec3(mp.point!))))).toBeLessThan(1e-12);
    expect(w.uTo).toEqual(toVec3(theoId.get("B")!.xyz!));
    expect(cungPhuong(tru(w.from, w.foot), toVec3(mp.normal!))).toBeCloseTo(1, 12);
  });

  it("dấu neo ĐÚNG chân H (không lệch), cạnh dọc HS và HB, và đoạn chứng minh HB được vẽ", () => {
    const [w] = nhanChungKetQua(s);
    const nhom = vatNhanChung(w, [], undefined, false, doanDaVe(s.objects));
    datCoGocVuong([nhom], camera([8, -6, 5]), 720);
    const d = dinhDau(nhom);
    chanNgamDinh(d).forEach((x, i) => expect(x).toBeCloseTo(w.foot[i], SO));
    expect(cungPhuong(tru(d[0], w.foot), tru(w.uTo!, w.foot))).toBeCloseTo(1, SO);
    expect(cungPhuong(tru(d[2], w.foot), tru(w.from, w.foot))).toBeCloseTo(1, SO);
    const leg = nhom.children.find((x) => x.name === `witness_leg:${w.id}`) as THREE.Line;
    expect(leg).toBeDefined();
    const p = leg.geometry.getAttribute("position");
    expect([p.getX(1), p.getY(1), p.getZ(1)]).toEqual(w.uTo);
  });
});

describe("P0 lỗi tiêm — mỗi lỗi phải bị bắt", () => {
  const s = canh("mp-vuong-goc-duong");
  const [goc] = nhanChungKetQua(s);
  const hopLe = (w: WitnessShown) => nhanChungVuongGocHopLe(s, w, "mpb");

  it("đối chứng: nhân chứng thật qua cổng", () => expect(hopLe(goc)).toBe(true));

  it("① chân SAI (trượt trong mặt phẳng): bị từ chối", () => {
    const lech = tru(goc.uTo!, goc.foot).map((x) => x * 0.1) as Vec3;
    expect(hopLe({ ...goc, foot: [goc.foot[0] + lech[0], goc.foot[1] + lech[1], goc.foot[2] + lech[2]] })).toBe(false);
  });

  it("② chân KHÔNG thuộc mặt phẳng (dù v vẫn chĩa về S): bị từ chối", () => {
    const foot: Vec3 = [goc.foot[0], goc.foot[1], goc.foot[2] + 0.05];
    expect(hopLe({ ...goc, foot, v: tru(goc.from, foot), uTo: undefined })).toBe(false);
  });

  it("③ quan hệ KHÔNG vuông góc (u lệch khỏi mặt phẳng / khỏi ⊥ v): bị từ chối", () => {
    expect(hopLe({ ...goc, u: [goc.u[0], goc.u[1], goc.u[2] + 0.02], uTo: undefined })).toBe(false);
    expect(hopLe({ ...goc, uTo: [goc.uTo![0] + 0.02, goc.uTo![1], goc.uTo![2]] })).toBe(false);
    // Envelope tiêm thẳng: cảnh bị sửa chân ⇒ projectionWitnessesAt không trả nhân chứng nào để vẽ.
    const hong = canh("mp-vuong-goc-duong");
    const kc = hong.objects.find((o) => o.id === "kc")!;
    kc.annotation!.witness!.foot = ["2", "5/3", "2/3"];
    expect(nhanChungKetQua(hong)).toEqual([]);
  });

  it("④ renderer dịch neo: phép đo chân ngầm định bắt được độ lệch", () => {
    const nhom = vatNhanChung(goc, [], undefined, false, doanDaVe(s.objects));
    datCoGocVuong([nhom], camera([8, -6, 5]), 720);
    const dauVe = nhom.children.find((x) => x.userData?.gocVuongDonVi)!;
    dauVe.position.x += 0.01;                     // lỗi tiêm: lệch neo một chút trong toạ độ thế giới
    const chan = chanNgamDinh(dinhDau(nhom));
    expect(dai(tru(chan, goc.foot))).toBeGreaterThan(5e-3);
  });

  it("⑤ cùng một quan hệ vẽ hai lần ⇒ chỉ MỘT dấu hiện", () => {
    const root = new THREE.Group();
    root.add(vatNhanChung(goc, [], undefined, false), vatNhanChung({ ...goc, id: `${goc.id}:b` }, [], undefined, false));
    expect(datCoGocVuong([root], camera([8, -6, 5]), 720)).toBe(1);
  });

  it("⑥ xoay camera quanh hình: dấu giữ nguyên chân và hai phương THẾ GIỚI (không trôi, không lật)", () => {
    const nhom = vatNhanChung(goc, [], undefined, false, doanDaVe(s.objects));
    const tam = new THREE.Vector3(1, 1, 1);
    let ban: Vec3[] | null = null;
    for (const t of [0, 0.7, 1.6, 2.5, 3.3, 4.4, 5.6]) {
      const c = camera([1 + 9 * Math.cos(t), 1 + 9 * Math.sin(t), 4]);
      datCoGocVuong([nhom], c, 720, tam);
      const d = dinhDau(nhom);
      chanNgamDinh(d).forEach((x, i) => expect(x).toBeCloseTo(goc.foot[i], SO));
      const huong = [tru(d[0], goc.foot), tru(d[2], goc.foot)];
      expect(vh(huong[0], tru(goc.uTo!, goc.foot))).toBeGreaterThan(0);
      expect(vh(huong[1], tru(goc.from, goc.foot))).toBeGreaterThan(0);
      if (ban) d.forEach((p, i) => p.forEach((x, k) => expect(x).toBeCloseTo(ban![i][k], SO)));
      ban = d;
    }
  });
});

describe("G1 — BC ⊥ (SAB) (vuong-goc-chop thật): dấu từ phép đo cos² = 0, không từ suy luận frontend", () => {
  const s = canh("vuong-goc-chop");
  const goc = s.objects.find((o) => o.id === "goc")!;
  const pt = (id: string) => toVec3(s.objects.find((o) => o.id === id)!.xyz!);

  it("backend gắn nhân chứng góc vuông cho đáp số; không còn ANNOTATION_UNBOUND", () => {
    expect(goc.value).toBe("0");
    expect(goc.annotation?.kind).toBe("angle");
    expect(goc.annotation?.witness?.relation).toBe("line_perpendicular_plane");
    expect(s.diagnostics ?? []).toEqual([]);
  });

  it("đúng một dấu tại B, ở bước kết luận; hai cạnh nằm trên BC và trên (SAB); không vẽ thêm nét chồng cạnh", () => {
    expect(projectionWitnessesAt(s, tatCa(s), buocCuoi(s) - 1)).toEqual([]);
    const ws = nhanChungKetQua(s);
    expect(ws).toHaveLength(1);
    const [w] = ws;
    expect(w.foot).toEqual(pt("B"));
    expect(w.from).toEqual(pt("C"));
    expect(nhanChungVuongGocHopLe(s, w, "sab")).toBe(true);
    const nhom = vatNhanChung(w, [], undefined, false, doanDaVe(s.objects));
    // BC và cạnh tới uTo đều là cạnh của khối ⇒ chỉ còn ô vuông và chấm chân, không nét đứt nào chồng lên chúng.
    expect(nhom.children.filter((x) => (x as THREE.Line).isLine && !x.userData?.gocVuongDonVi)).toHaveLength(0);
  });
});

describe("đoạn chứng minh không vẽ chồng lên cạnh đã có", () => {
  it("the-tich-chop: chân A, cạnh dấu chĩa B — AB là cạnh đáy ⇒ không vẽ đoạn chứng minh thứ hai", () => {
    const s = canh("the-tich-chop");
    const ws = nhanChungKetQua(s);
    expect(ws.length).toBeGreaterThan(0);
    const w = ws.find((x) => x.uTo)!;
    expect(w.foot).toEqual(toVec3(s.objects.find((o) => o.id === "A")!.xyz!));
    const nhom = vatNhanChung(w, [], undefined, false, doanDaVe(s.objects));
    expect(nhom.children.some((x) => x.name.startsWith("witness_leg:"))).toBe(false);
  });
});
