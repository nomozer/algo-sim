/**
 * regular-square-pyramid-w02 · D — hình phụ trên fixture THẬT của bộ đo (không dựng tay): đường AC, BD và mặt phẳng
 * qua A, B, C của chóp đều; đối chứng: đường BD của thiết diện (đề gọi tên, chỉ để đo) và mặt cắt (α) không ẩn.
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import type { Scene3D } from "./scene3d-model";
import { anchorOfGeometryStep, geometryStepCount, objectsAt } from "./scene3d-model";
import { withSubEntities } from "./scene3d-subentities";
import { auxiliaryHiddenAt, auxiliaryObjects, geometryStepGroups } from "./scene3d-auxiliary";

const W1 = join(__dirname, "../../../../../docs/evaluation/geometry/runs/regular-square-pyramid-w01/inputs/fixtures");
const canh = (ten: string): Scene3D =>
  JSON.parse(readFileSync(join(W1, `${ten}.json`), "utf8")).envelope.scene3d as Scene3D;
const buocCuaVat = (s: Scene3D, id: string) =>
  s.formation!.steps.findIndex((st) => st.visible_ids.includes(id));

describe("hình phụ", () => {
  const s = canh("regular_square_pyramid_positive");

  it("AC, BD là hình phụ DỰNG (xong khi có O); mặt phẳng qua A, B, C là hình phụ ĐO", () => {
    const p = auxiliaryObjects(s);
    expect(p.get("AC")).toEqual({ loai: "dung", xongTai: buocCuaVat(s, "O") });
    expect(p.get("BD")?.loai).toBe("dung");
    expect(p.get("mp_day")).toEqual({ loai: "do", xongTai: -1 });
    expect(p.has("O")).toBe(false);          // điểm không bao giờ là hình phụ bị ẩn
  });

  it("đường phụ hiện tới khi O có, rồi ẩn khỏi cảnh trung tính; mặt phẳng đo ẩn ở mọi bước", () => {
    const o = buocCuaVat(s, "O");
    expect(auxiliaryHiddenAt(s, o, false, null)).toEqual(new Set(["mp_day"]));
    expect(auxiliaryHiddenAt(s, o + 1, false, null)).toEqual(new Set(["AC", "BD", "mp_day"]));
    const cuoi = anchorOfGeometryStep(s, geometryStepCount(s) - 1);
    expect(auxiliaryHiddenAt(s, cuoi, false, null)).toEqual(new Set(["AC", "BD", "mp_day"]));
  });

  it("công tắc «Hình phụ» hiện tất cả; chọn hình phụ hay vật dựa trên nó cũng hiện nó", () => {
    const cuoi = anchorOfGeometryStep(s, geometryStepCount(s) - 1);
    expect(auxiliaryHiddenAt(s, cuoi, true, null).size).toBe(0);
    expect(auxiliaryHiddenAt(s, cuoi, false, "mp_day").has("mp_day")).toBe(false);
    expect(auxiliaryHiddenAt(s, cuoi, false, "chieu_cao_SO").has("mp_day")).toBe(false);
    expect(auxiliaryHiddenAt(s, cuoi, false, "O")).toEqual(new Set(["mp_day"]));
  });

  it("đối chứng: đường đề gọi tên chỉ để đo và mặt cắt không ẩn", () => {
    const t = canh("cross_section_positive");
    expect(auxiliaryObjects(t).has("BD")).toBe(false);
    expect(auxiliaryObjects(t).has("alpha_plane")).toBe(false);
    for (const ho of ["triangular_pyramid_positive", "triangular_prism_positive", "cuboid_positive"]) {
      expect(auxiliaryObjects(canh(ho)).size).toBe(0);
    }
  });

  it("«Các bước dựng»: AC, BD, O thành một nhóm, giữ thứ tự và mỗi bước con vẫn là một bước", () => {
    const g = geometryStepGroups(s);
    const nhom = g.filter((m) => m.loai === "nhom");
    expect(nhom).toHaveLength(1);
    const n = nhom[0] as { chinh: number; con: number[] };
    expect(n.con).toEqual([n.con[0], n.con[0] + 1, n.con[0] + 2]);
    expect(n.chinh).toBe(n.con[2]);
    const phang = g.flatMap((m) => (m.loai === "nhom" ? m.con : [m.index]));
    expect(phang).toEqual([...Array(geometryStepCount(s)).keys()]);
    expect(geometryStepGroups(canh("rectangular_pyramid_positive")).every((m) => m.loai === "buoc")).toBe(true);
  });

  it("FINDING-B2: đường thẳng mang chân đường vuông góc (`gt_g`, `derived_H_line`) KHÔNG tự ẩn ở bước cuối khi `aux=0`, còn hai mặt phẳng dựng giao tuyến (`mp1_gt_g`, `mp2_gt_g`) ẩn sau khi có `gt_g`", () => {
    const rb = JSON.parse(readFileSync(
      join(__dirname, "../../../../../docs/evaluation/geometry/runs/source-bound-result-planning/visual/scenes.json"),
      "utf8",
    )) as { id: string; scene: Scene3D }[];
    const dlp = rb.find((x) => x.id === "derived-line-pyramid")!.scene;
    const cuoiDlp = anchorOfGeometryStep(dlp, geometryStepCount(dlp) - 1);
    const anDlp = auxiliaryHiddenAt(dlp, cuoiDlp, false, null);
    expect(anDlp.has("gt_g")).toBe(false);
    expect(anDlp.has("mp1_gt_g")).toBe(true);
    expect(anDlp.has("mp2_gt_g")).toBe(true);

    const gd = JSON.parse(readFileSync(
      join(__dirname, "../../../../../docs/evaluation/geometry/runs/goal-directed-section-planning/visual/scenes.json"),
      "utf8",
    )) as { id: string; scene: Scene3D }[];
    const foot = gd.find((x) => x.id === "aux-foot-S-to-BD")!.scene;
    const cuoiFoot = anchorOfGeometryStep(foot, geometryStepCount(foot) - 1);
    expect(auxiliaryHiddenAt(foot, cuoiFoot, false, null).has("derived_H_line")).toBe(false);
  });

  it("W2: điểm tịnh tiến phụ ngoài khối (`H`, `H1` trong `two-line-prism`) hiện tới khi dựng xong mặt cắt `(P)` rồi ẩn ở bước cuối khi `aux=0`", () => {
    const seq = JSON.parse(readFileSync(
      join(__dirname, "../../../../../docs/evaluation/geometry/runs/pedagogical-construction-sequencing/visual/scenes.json"),
      "utf8",
    )) as { id: string; scene: Scene3D }[];
    const tlp = seq.find((x) => x.id === "two-line-prism")!.scene;
    const buocMp = buocCuaVat(tlp, "mp_td_q");
    const phu = auxiliaryObjects(tlp);
    expect(phu.get("H")).toEqual({ loai: "dung", xongTai: buocMp });
    expect(phu.get("H1")).toEqual({ loai: "dung", xongTai: buocMp });
    expect(phu.has("M")).toBe(false);
    expect(auxiliaryHiddenAt(tlp, buocMp, false, null).has("H")).toBe(false);
    expect(auxiliaryHiddenAt(tlp, buocMp, false, null).has("H1")).toBe(false);
    const cuoi = anchorOfGeometryStep(tlp, geometryStepCount(tlp) - 1);
    expect(auxiliaryHiddenAt(tlp, cuoi, false, null).has("H")).toBe(true);
    expect(auxiliaryHiddenAt(tlp, cuoi, false, null).has("H1")).toBe(true);
    expect(auxiliaryHiddenAt(tlp, cuoi, true, null).has("H")).toBe(false);
    expect(auxiliaryHiddenAt(tlp, cuoi, false, "mp_td_q").has("H")).toBe(false);
    const tlpSub = withSubEntities(tlp, objectsAt);
    expect(auxiliaryHiddenAt(tlpSub, cuoi, false, null).has("H")).toBe(true);
    expect(auxiliaryHiddenAt(tlpSub, cuoi, false, null).has("H1")).toBe(true);
  });
});

