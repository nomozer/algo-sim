/**
 * Semantic-to-Scene3D — phép dựng của góc đề hỏi, trên envelope THẬT của backend (fixture sinh bằng route local-first).
 * Kiểm: hiện đúng từ bước kết luận; toạ độ đi qua T·p khi khung không Euclid; mọi bất biến được kiểm lại ở toạ độ thế
 * giới; tiêm lỗi thì không vẽ (fail-closed); không vật nào mang số đo; nhóm vẽ không bắt cú bấm.
 */
import * as THREE from "three";
import { describe, expect, it } from "vitest";

import fixtures from "./scene3d-angle-construction-fixtures.json";
import { angleArcPoints, angleConstructionShape, angleConstructionsAt } from "./scene3d-angle-construction";
import { veKhongGian } from "./scene3d-chart";
import { type Scene3D, type Vec3, toVec3 } from "./scene3d-model";
import { vatDungGoc } from "./scene3d-view";

type Ca = keyof typeof fixtures.cases;
const canh = (k: Ca): Scene3D => veKhongGian(structuredClone(fixtures.cases[k].scene3d) as unknown as Scene3D);
const tatCa = (s: Scene3D) => new Set(s.objects.map((o) => o.id));
const buocKetLuan = (s: Scene3D) => s.events.find((e) => e.semantic_kind === "FINAL_RESULT")!.step_index;
const tru = (a: Vec3, b: Vec3): Vec3 => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const vh = (a: Vec3, b: Vec3) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const dai = (a: Vec3) => Math.hypot(...a);
const diem = (s: Scene3D, id: string) => toVec3(s.objects.find((o) => o.id === id)!.xyz!);
const cos2 = (a: Vec3, b: Vec3) => vh(a, b) ** 2 / (vh(a, a) * vh(b, b));
const dapSo = (s: Scene3D) => {
  const [t, m = "1"] = String(s.objects.find((o) => o.type === "quantity" && o.angle_construction)!.value).split("/");
  return Number(t) / Number(m);
};

describe("phép dựng góc — hiện theo timeline", () => {
  it.each(["line_plane", "dihedral", "skew", "tetra"] as Ca[])("%s: ẩn trước bước kết luận, hiện từ bước đó", (k) => {
    const s = canh(k);
    const t = buocKetLuan(s);
    expect(angleConstructionsAt(s, t - 1, tatCa(s))).toEqual([]);
    expect(angleConstructionsAt(s, t, tatCa(s))).toHaveLength(1);
  });

  it("điểm có tên của phép dựng chưa có mặt ⇒ không vẽ", () => {
    const s = canh("line_plane");
    const coMat = tatCa(s);
    coMat.delete("A");
    expect(angleConstructionsAt(s, buocKetLuan(s), coMat)).toEqual([]);
  });
});

describe("phép dựng góc — bất biến ở toạ độ thế giới", () => {
  it("đường–mặt: chân A của S trên (ABCD), SA ⟂ đáy, góc tại C giữa CS và hình chiếu CA bằng đáp số", () => {
    const s = canh("line_plane");
    const g = angleConstructionsAt(s, buocKetLuan(s), tatCa(s))[0];
    expect(g.relation).toBe("line_plane");
    const [S, A, B, C, D] = ["S", "A", "B", "C", "D"].map((id) => diem(s, id));
    expect(dai(tru(g.vertex, C))).toBeLessThan(1e-9);
    expect(dai(tru(g.perpendicular![1], A))).toBeLessThan(1e-9);
    for (const q of [B, D]) expect(Math.abs(vh(tru(S, A), tru(q, A)))).toBeLessThan(1e-9);
    expect(cos2(tru(g.arms[0], g.vertex), tru(g.arms[1], g.vertex))).toBeCloseTo(dapSo(s), 12);
  });

  it("tứ diện đều (khung không Euclid): sau T·p chân là trọng tâm đáy và đoạn tới chân vuông góc mặt đáy", () => {
    const s = canh("tetra");
    const g = angleConstructionsAt(s, buocKetLuan(s), tatCa(s))[0];
    const [A, B, C, D] = ["A", "B", "C", "D"].map((id) => diem(s, id));
    const tam: Vec3 = [(B[0] + C[0] + D[0]) / 3, (B[1] + C[1] + D[1]) / 3, (B[2] + C[2] + D[2]) / 3];
    expect(dai(tru(g.perpendicular![1], tam))).toBeLessThan(1e-9);
    for (const q of [C, D]) expect(Math.abs(vh(tru(A, tam), tru(q, B)))).toBeLessThan(1e-9);
    // T·p đi qua chuỗi thập phân 1e-9 (biên hiển thị): sai số chuyển đổi, không phải sai số của kernel.
    expect(cos2(tru(A, B), tru(tam, B))).toBeCloseTo(dapSo(s), 8);
  });

  it("nhị diện: hai tia tại đỉnh vuông góc giao tuyến BC, góc giữa hai tia bằng đáp số; hai dấu vuông góc", () => {
    const s = canh("dihedral");
    const g = angleConstructionsAt(s, buocKetLuan(s), tatCa(s))[0];
    const e = tru(diem(s, "C"), diem(s, "B"));
    for (const a of g.arms) expect(Math.abs(vh(tru(a, g.vertex), e))).toBeLessThan(1e-9);
    expect(g.rightAngles).toHaveLength(2);
    expect(cos2(tru(g.arms[0], g.vertex), tru(g.arms[1], g.vertex))).toBeCloseTo(dapSo(s), 12);
  });

  it("chéo nhau: cạnh thứ hai song song A′D và là đoạn phụ", () => {
    const s = canh("skew");
    const g = angleConstructionsAt(s, buocKetLuan(s), tatCa(s))[0];
    const d2 = tru(diem(s, "D"), diem(s, "A_prime"));
    const a2 = tru(g.arms[1], g.vertex);
    expect(Math.abs(Math.abs(vh(a2, d2)) - dai(a2) * dai(d2))).toBeLessThan(1e-9);
    expect(g.parallelHelper).toBe(true);
  });
});

describe("phép dựng góc — fail-closed", () => {
  const goc = () => structuredClone(canh("line_plane").objects.find((o) => o.angle_construction)!.angle_construction!);

  it("đoạn tới chân không vuông góc với mặt ⇒ không vẽ", () => {
    const g = goc();
    g.perpendicular!.v = ["1", "0", "1"];
    expect(angleConstructionShape("q", g)).toBeNull();
  });

  it("chân không phải đầu của cạnh thứ hai ⇒ không vẽ", () => {
    const g = goc();
    g.perpendicular!.foot = ["1/2", "0", "0"];
    expect(angleConstructionShape("q", g)).toBeNull();
  });

  it("tia nhị diện không vuông góc giao tuyến ⇒ không vẽ; quan hệ lạ ⇒ không vẽ", () => {
    const g = structuredClone(canh("dihedral").objects.find((o) => o.angle_construction)!.angle_construction!);
    g.edge!.direction = ["1", "1", "0"];
    expect(angleConstructionShape("q", g)).toBeNull();
    expect(angleConstructionShape("q", { ...goc(), relation: "point_point" as never })).toBeNull();
  });
});

describe("phép dựng góc — trình bày", () => {
  it("cung góc nằm trên đường tròn bán kính r quanh đỉnh, đi từ cạnh này sang cạnh kia", () => {
    const s = canh("line_plane");
    const g = angleConstructionsAt(s, buocKetLuan(s), tatCa(s))[0];
    const cung = angleArcPoints(g, 0.2);
    for (const p of cung) expect(dai(tru(p, g.vertex))).toBeCloseTo(0.2, 9);
    const dau = tru(cung[0], g.vertex), cuoi = tru(cung.at(-1)!, g.vertex);
    expect(cos2(dau, tru(g.arms[0], g.vertex))).toBeCloseTo(1, 9);
    expect(cos2(cuoi, tru(g.arms[1], g.vertex))).toBeCloseTo(1, 9);
  });

  it("nhóm vẽ: có cung, không bắt cú bấm, không chữ / con số nào", () => {
    const s = canh("dihedral");
    const g = angleConstructionsAt(s, buocKetLuan(s), tatCa(s))[0];
    const nhom = vatDungGoc(g, s.objects.flatMap((o) => (o.xyz ? [toVec3(o.xyz)] : [])), []);
    expect(nhom.name).toBe(`angle_construction:${g.id}`);
    expect(nhom.children.some((c) => c.name.startsWith("angle_arc:"))).toBe(true);
    const ray = new THREE.Raycaster();
    const hits: THREE.Intersection[] = [];
    nhom.traverse((c) => c.raycast(ray, hits));
    expect(hits).toEqual([]);
    nhom.traverse((c) => expect(c.type).not.toBe("Sprite"));
  });

  it("phép dựng không mang giá trị số của đáp số", () => {
    const s = canh("line_plane");
    const g = s.objects.find((o) => o.angle_construction)!.angle_construction!;
    expect(Object.keys(g).sort()).toEqual(["arms", "checks", "perpendicular", "relation", "schema", "vertex", "vertex_id"]);
    expect(JSON.stringify(g)).not.toContain(String(s.objects.find((o) => o.angle_construction)!.value));
  });
});
