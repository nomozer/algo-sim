/**
 * Run `scene3d-section-inspector-c0`: a section vertex shared by two semantic points (prism: translate H ≡ cut I on
 * BB′) is named by the point whose dependencies say it IS the cut of that solid edge with the section plane
 * (`vertex_sources` edge indices + a `line3` on exactly that edge + the section's plane), never by coordinate alone,
 * object order or names. No such unique point ⇒ the neutral "Đỉnh k" stays.
 */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import type { Scene3D, SceneObject } from "./scene3d-model";
import { deriveSectionSubEntities, sectionCycleLabel, sectionDetails } from "./scene3d-subentities";

const EXPORT = resolve(__dirname,
  "../../../../../docs/evaluation/geometry/runs/scene3d-plane-section-display-identity/results/adapter4-export-final/adapter4-fixtures.json");
const SERVED: { id: string; envelope: { scene3d: Scene3D } }[] = JSON.parse(readFileSync(EXPORT, "utf-8")).fixtures;
const scene = (id: string): Scene3D => structuredClone(SERVED.find((f) => f.id === id)!.envelope.scene3d);
const PRISM = "CORPUS-DEV10-prism-area";
const obj = (sc: Scene3D, id: string) => sc.objects.find((o) => o.id === id)!;

describe("section vertex identity on coincident points", () => {
  it("names the prism's unnamed cuts by their edge-intersection role", () => {
    expect(sectionDetails(scene(PRISM), "td_sp")?.vertexNames).toEqual([
      "Giao điểm của BB' và (α)", "M", "Giao điểm của CC' và (α)"]);
  });

  it("gives the section vertex sub-entities the same point, edges unchanged", () => {
    const sub = deriveSectionSubEntities(scene(PRISM)).filter((s) => s.parent === "td_sp");
    const dinh = sub.filter((s) => s.type === "point3");
    expect(dinh.map((s) => [s.label, s.depends])).toEqual([
      ["Giao điểm của BB' và (α)", ["I"]], ["M", ["M"]], ["Giao điểm của CC' và (α)", ["I1"]]]);
    expect(sub.filter((s) => s.type === "edge").map((s) => s.label)).toEqual(["Cạnh 1", "Cạnh 2", "Cạnh 3"]);
  });

  it("does not depend on object order or on the coincident point's name", () => {
    const sc = scene(PRISM);
    sc.objects.reverse();
    for (const o of sc.objects) if (o.id === "H" || o.id === "H1") o.notation = `Z${o.id}`;
    expect(sectionDetails(sc, "td_sp")?.vertexNames[0]).toBe("Giao điểm của BB' và (α)");
  });

  it("stays neutral when no coincident point is the cut of that edge", () => {
    const sc = scene(PRISM);
    const line = obj(sc, obj(sc, "I").depends.find((d) => obj(sc, d).type === "line3")!);
    line.depends = ["A", "A_prime"];
    expect(sectionDetails(sc, "td_sp")?.vertexNames[0]).toBe("Đỉnh 1");
  });

  it("stays neutral when two coincident points both qualify", () => {
    const sc = scene(PRISM);
    sc.objects.push({ ...(structuredClone(obj(sc, "I")) as SceneObject), id: "I_twin", label: "Bản sao" });
    expect(sectionDetails(sc, "td_sp")?.vertexNames[0]).toBe("Đỉnh 1");
  });

  it("never promotes the stated-unnamed cut to a named source point", () => {
    const sc = scene(PRISM);
    expect(obj(sc, "I").notation ?? null).toBeNull();
    expect(sectionCycleLabel(sc, "td_sp")).toBeNull();
  });

  it("leaves every non-ambiguous section vertex of the 22 served scenes as the coordinate rule names it", () => {
    let changed = 0;
    for (const f of SERVED) {
      const sc = f.envelope.scene3d;
      for (const sec of sc.objects.filter((o) => o.type === "section" && o.polygon)) {
        const names = sectionDetails(sc, sec.id)!.vertexNames;
        sec.polygon!.forEach((v, k) => {
          const at = sc.objects.filter((p) => p.type === "point3" && !p.id.includes("::") && p.xyz?.join("|") === v.join("|"));
          if (at.length === 1) expect(names[k]).toBe(at[0].notation ?? at[0].label);
          else changed += 1;
        });
      }
    }
    expect(changed).toBe(2);                    // the prism's two coincident vertices, nothing else
  });
});
