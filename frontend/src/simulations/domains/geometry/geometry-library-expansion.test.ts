import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { veKhongGian } from "./scene3d-chart";
import { toVec3, type Scene3D } from "./scene3d-model";
import { buildObject3D } from "./scene3d-view";

// Real backend output from BOTH fake adapters, not a handwritten renderer scene.
const rows = JSON.parse(readFileSync(resolve("../docs/evaluation/geometry/runs/geometry-library-expansion/offline-certification/scenes.json"), "utf8")) as { id: string; scene: Scene3D }[];
const expected = [[1, 1, 0], [2, 2, 0], [1, 1, 0], [18 / 13, 2, 12 / 13]];
describe("expanded primitives cross the actual renderer metric boundary", () => {
  for (const row of rows) {
    it(`${row.id}: Euclidean point, provenance, solid faces/edges and render objects`, () => {
      const index = Number(row.id.split("-")[1]);
      const scene = veKhongGian(row.scene);
      const point = scene.objects.find(o => o.id === (index === 0 ? "O" : "H"))!;
      expect(point.origin).toBe("derived");
      expect(point.producer).toMatch(/construct_point\.(intersect|project)/);
      expect(point.depends.length).toBeGreaterThan(0);
      toVec3(point.xyz!).forEach((x, i) => expect(x).toBeCloseTo(expected[index][i], 8));
      const rendered = buildObject3D(point, false);
      expect(rendered).not.toBeNull();
      const solid = scene.objects.find(o => o.type === "solid")!;
      expect(solid.faces?.length).toBe(5);
      expect(buildObject3D(solid, false)).not.toBeNull();
      expect(scene.objects.some(o => o.type === "segment3")).toBe(true);
      expect(scene.objects.some(o => o.type === "polygon3")).toBe(true);
      // Scene identity must retain label and dependency relationships after transform.
      expect(point.display_label).toBe(index === 0 ? "O" : "H");
      if (index === 3) {
        const p = toVec3(point.xyz!);
        expect(p[0] / 2 + p[2] / 3).toBeCloseTo(1, 8);
        expect((p[0] ** 2 + p[1] ** 2 + p[2] ** 2)).toBeCloseTo(88 / 13, 8);
      }
    });
  }
});
